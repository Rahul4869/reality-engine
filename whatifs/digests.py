"""The daily and weekly WhatsApp briefs, built only from the owner view. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt
from whatifs.core import S, log, store, iso, now_utc, parse_iso, set_setting, FAKE, scrub

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

def _risks(view):
    out = []
    m = view.get("money") or {}
    if m.get("cap"):
        pct = 100 * float(m.get("month_spend") or 0) / float(m["cap"])
        if pct >= 70: out.append(f"Spend at {pct:.0f}% of the cap: the controller will use cheaper tiers (fewer stills), never fewer animated scenes [Cost_Log]")
    eps = store().rows("Episodes")
    held = [e.get("episode_id") for e in eps if e.get("status") in ("HOLD_QC", "AWAITING_APPROVAL", "HELD_BY_OWNER")]
    if held: out.append(f"Waiting for you: {', '.join(held[-3:])} [Episodes]")
    from whatifs.notify import INFORM_KINDS
    opn = [r for r in store().rows("Owner_Actions") if str(r.get("status", "")).upper() in ("", "QUEUED", "PENDING", "SENT", "OPEN") and r.get("kind") not in INFORM_KINDS]      # v12 V4
    if S("TWO_SCREENS_ON", bool):                                                     # v12 B-OWNER: the count is "Needs you" - one definition (notify.needs)
        from whatifs import notify as NT; opn = NT.needs()
    if len(opn) > 2: out.append(f"{len(opn)} open decisions on the dashboard [Owner_Actions]")
    return out or ["No risks flagged [rule-based check of spend, holds and open decisions]"]

def compose(kind="daily", demo=False, now=None):
    from whatifs import owner_view as OV, charts as CH, scoreboard as SB
    now = now or now_utc(); v = OV.build(demo=demo)
    head = ("[DEMO] " if demo else "") + ("Morning brief" if kind == "daily" else "Weekly brief") + f", {now.astimezone(IST):%a %d %b}"
    from whatifs.org import strategy as STR
    def _part(fn, name):                                                       # V4's finish C16: each part of the CEO in its own try
        try: return fn(now)
        except Exception as e: log(f"{kind} brief: {name} was not built: {scrub(e)[:120]}", "WARN"); return f"{name}: not available right now ({scrub(e)[:80]})"
    parts = [f"*{head}*"] + [p for p in (_part(SB.line, "Scoreboard"), _part(STR.brief, "*Decisions*")) if p]      # v12 V4: the scoreboard, then Strategy's part *Decisions* ("" with STRATEGY_ON FALSE)
    parts += [OV.render("today", v), OV.render("numbers", v), OV.render("observations", v), OV.render("strategy", v),
              OV.render("hot_topics", v), OV.render("recommendations", v)]
    if kind == "weekly": parts += [OV.render("experiments", v), OV.render("money", v), learned(demo)]
    parts.append("*Risks*\n" + "\n".join(f"- {r}" for r in (_risks(v) if not demo else ["DEMO: spend at 62% of the cap [Cost_Log]"])))
    chart = CH.numbers_chart(v) or CH.money_chart(v)
    return "\n\n".join(parts), chart

def due(kind, now=None):
    if not S("DIGEST_WA_ON", bool): return False
    now = (now or now_utc()).astimezone(IST)
    if now.hour < S("DIGEST_DAILY_HOUR_IST", int): return False
    if kind == "daily": return str(S("DIGEST_DAILY_SENT") or "")[:10] != now.date().isoformat()
    wk = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
    return now.strftime("%a") == str(S("DIGEST_WEEKLY_DAY") or "Sun")[:3] and str(S("DIGEST_WEEKLY_SENT") or "") != wk

def send(kind="daily", demo=False, now=None):
    """The brief of the day or the week. v12 B-OWNER: with TWO_SCREENS_ON it is the morning message (`_send_new`); FALSE = the older brief."""
    if S("TWO_SCREENS_ON", bool): return _send_new(kind, now)
    return _send_old(kind, demo, now)

def _send_old(kind="daily", demo=False, now=None):
    """The older brief, word for word (the switch off)."""
    from whatifs import wa as WA, publish as PUB
    now = now or now_utc(); text, chart = compose(kind, demo, now)
    sent = "email"
    if WA.configured() or FAKE:
        if WA.in_window(now) or FAKE:
            took = WA.send_text(text) or FAKE
            if chart: WA.send_image(chart, "Numbers" + (" (DEMO)" if demo else ""))
            WA.send_buttons("Open a section:", [("Menu", "MENU|menu"), ("Numbers", "MENU|numbers"), ("What to post", "MENU|recommendations")]); sent = "whatsapp" if took else "whatsapp_failed"      # V4's finish C15: stamped only when WhatsApp took the text
        else:
            WA.send_template(f"Your {kind} brief is ready ({text.splitlines()[0].strip('*')}).", ["Menu", "Numbers", "Pause"], ["MENU|menu", "MENU|numbers", "PAUSE"]); sent = "template"
    mailed = False
    try: mailed = bool(PUB.email(f"Reality Engine {kind} brief", "<pre style='font-family:inherit;white-space:pre-wrap'>" + text.replace("<", "&lt;") + "</pre>"))
    except Exception as e: log(f"{kind} brief e-mail failed: {scrub(e)[:120]}", "WARN")
    if sent == "whatsapp" or mailed:                                              # v12 V4: what was shown is stamped only when it went
        try:
            from whatifs.org import strategy as STR; STR.briefed(now)
        except Exception as e: log(f"the brief's rows were not stamped: {scrub(e)[:120]}", "WARN")
    if kind == "daily": set_setting("DIGEST_DAILY_SENT", now.astimezone(IST).date().isoformat())
    else: set_setting("DIGEST_WEEKLY_SENT", f"{now.astimezone(IST).isocalendar()[0]}-W{now.astimezone(IST).isocalendar()[1]:02d}")
    log(f"{kind} brief sent ({sent})"); return {"kind": kind, "via": sent, "chars": len(text), "chart": bool(chart)}

# ------------------------------------------------------------------ v12 B-OWNER (PART 4, item 150): the morning message and the "Needs you" list
def head(kind="daily", now=None):
    """The morning message's head: numbers and facts, at most 8 lines and 700 characters, no greeting and no filler - a line appears only when it
    has something to say. Sunday's is the weekly message, with the week's numbers."""
    from whatifs import notify as NT, scoreboard as SB
    now = now or now_utc(); loc = now.astimezone(IST)
    lines = [f"{'Weekly' if kind == 'weekly' else 'Morning'} message, {loc:%a %d %b}"]
    try: sb = SB.line(now)
    except Exception as e: sb = ""; log(f"the morning head's scoreboard line was not built: {scrub(e)[:120]}", "WARN")
    if sb: lines.append(sb)
    if kind == "weekly":
        try:
            from whatifs import owner_view as OV
            wk = next((l[2:] for l in OV.render("numbers", OV.build()).splitlines() if l.startswith("- ")), "")
            if wk: lines.append("This week: " + wk)
        except Exception as e: log(f"the weekly head's numbers were not built: {scrub(e)[:120]}", "WARN")
    for r in [r for r in NT.open_rows() if NT.klass(r.get("kind")) == NT.ALARM]:
        lines.append("ALARM open: " + NT.whole(r.get("text") or "", 120))
    need = sorted(NT.needs(), key=lambda r: str(r.get("expires_at") or "9999"))
    first = next((r for r in need if r.get("expires_at")), None)
    lines.append(f"Needs you: {len(need)}" + (f" (the first closes {parse_iso(first['expires_at']).astimezone(IST):%a %H:%M}: {first.get('default_action') or 'it waits'})" if first else ""))
    lines += [NT.whole(r.get("text") or "", 120) for r in NT.open_rows() if r.get("kind") in ("topup", "expiry")][:2]
    try:
        from whatifs.org import desk as DK; ans = len(DK.lines(now))
    except Exception as e: ans = 0; log(f"the morning head's answers were not counted: {scrub(e)[:120]}", "WARN")
    if ans: lines.append(f"Answers to your inputs: {ans}")
    return NT.whole("\n".join(lines[:8]), 700)

def whole(now=None):
    """The eight groups in full - the mail of the morning message (the copy cannot open on a tap)."""
    from whatifs import wa as WA, owner_view as OV
    view = OV.build(); return "\n\n".join(WA.group_text(g, view, now, cut=None) for g, _t in WA.MENU_GROUPS)

def _send_new(kind="daily", now=None):
    """The morning message: ONE WhatsApp push (`wa.push("morning")`: the head and the eight groups' list, or the one template outside the window) and
    the mail of the WHOLE message. What it showed is stamped only when WhatsApp took the push or the mail went (V4's rule). The weekly message
    replaces the morning message of its day (Sunday): both clocks are stamped."""
    from whatifs import wa as WA, publish as PUB
    now = now or now_utc(); top = head(kind, now); took = ""
    try: took = WA.push("morning", now=now, text=top)
    except Exception as e: log(f"the {kind} message was not pushed: {scrub(e)[:120]}", "WARN")
    mailed = False; text = top + "\n\n" + whole(now)
    try: mailed = bool(PUB.email(f"Reality Engine {kind} brief", "<pre style='font-family:inherit;white-space:pre-wrap'>" + text.replace("<", "&lt;") + "</pre>"))
    except Exception as e: log(f"{kind} message e-mail failed: {scrub(e)[:120]}", "WARN")
    if took or mailed:
        try:
            from whatifs.org import strategy as STR; STR.briefed(now)
        except Exception as e: log(f"the message's rows were not stamped: {scrub(e)[:120]}", "WARN")
    loc = now.astimezone(IST); set_setting("DIGEST_DAILY_SENT", loc.date().isoformat())
    if kind == "weekly": set_setting("DIGEST_WEEKLY_SENT", f"{loc.isocalendar()[0]}-W{loc.isocalendar()[1]:02d}")
    sent = "whatsapp" if took else ("email" if mailed else "none")
    log(f"{kind} message sent ({sent})"); return {"kind": kind, "via": sent, "chars": len(text), "chart": False}

def needs_tick(now=None):
    """The "Needs you" list: at the first tick at or after NEEDS_HOUR_IST (India time), once a day, only when a decision is open - ONE WhatsApp push
    and its mail. No decision open = no message."""
    from whatifs import wa as WA, notify as NT, publish as PUB
    now = now or now_utc(); loc = now.astimezone(IST)
    if loc.hour < S("NEEDS_HOUR_IST", int) or str(S("NEEDS_SENT") or "")[:10] == loc.date().isoformat(): return False
    rows = NT.needs()
    if not rows: return False
    try: WA.push("needs", now=now)
    except Exception as e: log(f"the needs list was not pushed: {scrub(e)[:120]}", "WARN")
    try: PUB.email(f"Reality Engine: {len(rows)} decision{'s' if len(rows) != 1 else ''} need you", "<ul>" + "".join(f"<li>{str(r.get('text') or '')[:200].replace('<', '&lt;')}"
                   + (f" - if you do nothing: {r['default_action']}" if r.get("default_action") else "") + "</li>" for r in rows) + "</ul>")
    except Exception as e: log(f"the needs list e-mail failed: {scrub(e)[:120]}", "WARN")
    set_setting("NEEDS_SENT", loc.date().isoformat()); return True

def tick(now=None):
    out = []
    for kind in ("weekly", "daily"):
        try:
            if due(kind, now): out.append(send(kind, now=now))
        except Exception as e: log(f"{kind} brief failed: {scrub(e)[:120]}", "WARN")
    if S("TWO_SCREENS_ON", bool):                                                  # v12 B-OWNER: the evening list
        try:
            if needs_tick(now): out.append({"kind": "needs"})
        except Exception as e: log(f"the needs list failed: {scrub(e)[:120]}", "WARN")
    return out

def learned(demo=False):
    """v11 (K155 report): the week's learning in plain words - proven / promising / disproven techniques with the evidence, and whether the
    forecasts beat simply guessing the channel median (honest: 'too few measured videos' until there are 8)."""
    if demo:
        return ("*What we learned (DEMO DATA)*\n- Proven: verdict-first cold opens (+3.1 pts stayed-to-watch, 7 Shorts, P=0.93)\n"
                "- Promising: object-on-trial titles (P=0.78)\n- Disproven: countdown hooks (P=0.22, retired for 60 days)\n- Forecasts: learning")
    try:
        from whatifs import brain as BR
        v = BR.verdicts()
    except Exception as e:
        return f"*What we learned*\n- not available this week ({str(e)[:80]})"
    def line(r): return f"{r.get('family')}={r.get('level')} ({r.get('format')}, {r.get('n_videos')} videos, P={float(r.get('p_beats_baseline') or 0):.2f}, {float(r.get('effect_pp') or 0):+.1f} pts)"
    out = ["*What we learned* [Technique_Evidence]"]
    for name, key in (("Proven", "proven"), ("Promising", "promising"), ("Disproven (retired 60 days)", "retired")):
        rows = v.get(key) or []
        out.append(f"- {name}: " + ("; ".join(line(r) for r in rows[:3]) if rows else "none yet"))
    out.append(f"- Forecasts: {v.get('learning')}")
    return "\n".join(out)

