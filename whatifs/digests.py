"""v10.3 (K153): the daily and weekly WhatsApp briefs (owner change request C3). Built ONLY from the owner view (every number with its source;
interpretations labelled; 'no data yet' when empty) plus one chart image. Inside WhatsApp's 24-hour window: text + chart + buttons; outside it: the
approved template with Menu / Numbers / Pause quick replies (the full brief also goes by email). Rs 0 (rule-based, code-made chart)."""
from __future__ import annotations
import datetime as dt
from whatifs.core import S, log, store, iso, now_utc, set_setting, FAKE, scrub

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
    opn = [r for r in store().rows("Owner_Actions") if str(r.get("status", "")).upper() in ("", "QUEUED", "PENDING", "SENT", "OPEN")]
    if len(opn) > 2: out.append(f"{len(opn)} open decisions on the dashboard [Owner_Actions]")
    return out or ["No risks flagged [rule-based check of spend, holds and open decisions]"]

def compose(kind="daily", demo=False, now=None):
    from whatifs import owner_view as OV, charts as CH
    now = now or now_utc(); v = OV.build(demo=demo)
    head = ("[DEMO] " if demo else "") + ("Morning brief" if kind == "daily" else "Weekly brief") + f", {now.astimezone(IST):%a %d %b}"
    parts = [f"*{head}*", OV.render("today", v), OV.render("numbers", v), OV.render("observations", v), OV.render("strategy", v),
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
    from whatifs import wa as WA, publish as PUB
    now = now or now_utc(); text, chart = compose(kind, demo, now)
    sent = "email"
    if WA.configured() or FAKE:
        if WA.in_window(now) or FAKE:
            WA.send_text(text)
            if chart: WA.send_image(chart, "Numbers" + (" (DEMO)" if demo else ""))
            WA.send_buttons("Open a section:", [("Menu", "MENU|menu"), ("Numbers", "MENU|numbers"), ("What to post", "MENU|recommendations")]); sent = "whatsapp"
        else:
            WA.send_template(f"Your {kind} brief is ready ({text.splitlines()[0].strip('*')}).", ["Menu", "Numbers", "Pause"], ["MENU|menu", "MENU|numbers", "PAUSE"]); sent = "template"
    try: PUB.email(f"Reality Engine {kind} brief", "<pre style='font-family:inherit;white-space:pre-wrap'>" + text.replace("<", "&lt;") + "</pre>")
    except Exception: pass
    if kind == "daily": set_setting("DIGEST_DAILY_SENT", now.astimezone(IST).date().isoformat())
    else: set_setting("DIGEST_WEEKLY_SENT", f"{now.astimezone(IST).isocalendar()[0]}-W{now.astimezone(IST).isocalendar()[1]:02d}")
    log(f"{kind} brief sent ({sent})"); return {"kind": kind, "via": sent, "chars": len(text), "chart": bool(chart)}

def tick(now=None):
    out = []
    for kind in ("weekly", "daily"):
        try:
            if due(kind, now): out.append(send(kind, now=now))
        except Exception as e: log(f"{kind} brief failed: {scrub(e)[:120]}", "WARN")
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

