"""The one owner-messaging layer with no-spam tiers; every owner message goes through notify.send(). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, itertools, json, re
from zoneinfo import ZoneInfo
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, set_setting, scrub

IST = ZoneInfo("Asia/Kolkata")
TIERS = ("now", "week", "fyi")
HANDLERS = {}          # kind -> callable(row, answer) run when the owner answers; registered by features
DEFAULTS = {}          # kind -> callable(row) run when the row expires unanswered; registered by features


def _ensure_handlers():
    """Every feature's answer/default handlers are known before an answer or a default runs (any entry point: email, dashboard, WhatsApp, tick)."""
    for mod, fn in (("whatifs.builds", "ensure_registered"), ("whatifs.visual_lab", "register"), ("whatifs.wa", "register"), ("whatifs.caretaker", "register"), ("whatifs.bakeoff", "register"), ("whatifs.steward", "register"), ("whatifs.contract", "register"), ("whatifs.specials", "register"), ("whatifs.sheets", "register"), ("whatifs.breakout", "register"), ("whatifs.ladder", "register"), ("whatifs.replan", "register"), ("whatifs.org.memos", "register"), ("whatifs.org.execute", "register"), ("whatifs.org.floor", "register"), ("whatifs.org.verdicts", "register"), ("whatifs.maker", "register"), ("whatifs.org.strategy", "register"), ("whatifs.org.risk", "register"), ("whatifs.org.desk", "register")):
        try: getattr(__import__(mod, fromlist=[fn]), fn)()
        except Exception as e: log(f"handlers from {mod} not loaded: {scrub(e)[:80]}", "WARN")

def register(kind, on_answer=None, on_default=None):
    if on_answer: HANDLERS[kind] = on_answer
    if on_default: DEFAULTS[kind] = on_default


INFORM_KINDS = ("strategy", "desk")      # v12 V4: rows that tell him what was done ("Nothing to do"): never counted or listed as waiting for him, never expire
STANDING_KINDS = INFORM_KINDS + ("idea", "decided_post")      # v12 B-OWNER: rows that tell him what was done, with an undo or a next step: never counted as waiting, never given an expiry by the inform rule (the older path reads INFORM_KINDS, word for word)

# ------------------------------------------------------------------ v12 B-OWNER: THE REGISTER - every kind of message to him, what it is and where it shows (data)
ALARM, HOLD, CARD, INFORM = "alarm", "hold", "card", "inform"
GROUPS = ("needs", "posted", "learned", "research", "plan", "inputs", "money", "decided")
def _kinds(klass_, group_, *kinds): return {k: (klass_, group_) for k in kinds}
KINDS = {
    # ALARM, the fixed list (item 180): the channel's safety (five), money stopping, the pipeline stopping
    **_kinds(ALARM, "needs", "kids_flag", "policy", "risk_lock", "risk_gone", "uploads_private", "money_stop", "pipeline_stop", "org_watchdog"),
    # HOLD, the named hold list (item 150): (a) a quality or policy hold; (b) what only he can lawfully do. (c), the launch un-pause, is his own sitting and has no card
    **_kinds(HOLD, "needs", "contract_hold", "floor_hold", "special_review", "hd_blocked", "org_lever", "api_audit", "ypp_tier"),
    # CARD, a decision with a deadline and a default
    **_kinds(CARD, "needs", "bakeoff", "breakout", "expiry", "build_ready", "ladder", "occasion", "replan", "linkpack", "model_dead", "style_pick", "visual_idea",
             "creative_review", "floor_eye", "special_ready", "maker_line", "owner_verdict", "org_stuck", "pin_comment", "title_pick", "script_preview",
             "sheets_review", "voice_pick", "prepublic"),
    **_kinds(CARD, "money", "budget_guard", "split", "clip_price", "scout_price"),
    **_kinds(CARD, "plan", "scout_deprecated", "model_switch", "model_plan", "model_new", "model_upgrade", "platform_change", "advisor"),
    # INFORM, what was done - by group
    **_kinds(INFORM, "decided", "strategy", "decided_post", "pick_ack", "sheets_locked"),
    **_kinds(INFORM, "inputs", "desk", "idea"),
    **_kinds(INFORM, "posted", "scheduled", "live", "audio_drop", "below_bar", "slot_skipped", "api_audit_wait", "floor_kit", "hd_late"),
    **_kinds(INFORM, "research", "comments_digest", "region", "similar_script", "slop"),
    **_kinds(INFORM, "plan", "monthly_brief", "preview_none", "repair_waiting", "org_cap", "org_build_held", "occasion_dates", "card_rule"),
    **_kinds(INFORM, "money", "budget_pct", "cost_overrun", "cost_check", "headroom", "topup", "mode_ack", "wa_cap"),
}
ALARM_KINDS = tuple(k for k, v in KINDS.items() if v[0] == ALARM)
HOLD_KINDS = tuple(k for k, v in KINDS.items() if v[0] == HOLD)
DASH_PRIVATE = ("script_preview", "special_ready", "special_review", "ladder", "occasion")      # kinds whose text holds a script or an unreleased premise: the dashboard shows their plain name only
INFORM_KEEP_H = 336          # an inform row of a kind outside STANDING_KINDS closes by itself after this many hours (its key holds the India date)
CARD_FALLBACK = "nothing changes; it is reported in the morning message"      # the default of a card sent without one (the build refuses such a call: the card scan)
_SEEN_VERBS = ("OK", "NOTED", "SEEN")

def klass(kind):
    """The kind's class: alarm, hold, card or inform. An unknown kind is a card under "Needs you" - never lost, never silent."""
    return KINDS.get(kind, (CARD, "needs"))[0]

def asks(row):
    """Does the row ask him to decide - a button whose verb is not OK, NOTED or SEEN?"""
    try: btns = json.loads(row.get("buttons") or "[]")
    except Exception: btns = []
    return any(str(v).strip().split(" ")[0].upper() not in _SEEN_VERBS for _l, v in btns if str(v).strip())

def needs(rows=None):
    """THE one definition of "Needs you": open HOLD rows, open CARD rows that ask him (`asks`), and open rows of a kind the register does not know."""
    rows = open_rows() if rows is None else [r for r in rows if r.get("status") in ("OPEN", "QUEUED")]
    return [r for r in rows if r.get("kind") not in KINDS or klass(r.get("kind")) == HOLD or (klass(r.get("kind")) == CARD and asks(r))]

def _on():
    return S("TWO_SCREENS_ON", bool)

def _india_day(): return now_utc().astimezone(IST).date().isoformat()

def link(verb, aid):
    """The one-tap link of an owner action (v12 V4: public - the brief's Undo links use it)."""
    from urllib.parse import quote
    repo = env("GH_REPO")
    if not repo: return ""
    return f"https://github.com/{repo}/issues/new?title={quote(f'ACT {aid} {verb}')}&body={quote('Press Submit new issue. The robot records your answer.')}"


_SEQ = itertools.count(1)
def _new_id(): return "A" + now_utc().strftime("%Y%m%d%H%M%S%f") + f"{next(_SEQ) % 100:02d}"      # 22 digits: unique even within one microsecond


def in_quiet_hours(now=None):
    now = (now or now_utc()).astimezone(IST)
    try:
        a, b = str(S("QUIET_HOURS_IST") or "00:30-08:00").split("-")
        h1, m1 = [int(x) for x in a.split(":")]; h2, m2 = [int(x) for x in b.split(":")]
    except Exception: return False
    t = now.hour * 60 + now.minute; lo, hi = h1 * 60 + m1, h2 * 60 + m2
    return (lo <= t < hi) if lo <= hi else (t >= lo or t < hi)


def _sent_today(rows):
    d = now_utc().astimezone(IST).date()
    n = 0
    for r in rows:
        t = parse_iso(r.get("delivered_at")) if r.get("tier") == "now" else None
        if t and t.astimezone(IST).date() == d and not str(r.get("kind", "")).startswith("digest"): n += 1
    return n


def now_room():
    """v12 V1c: how many 'act now' places are left today (NOTIFY_NOW_MAX_PER_DAY minus the ones sent): an ask that can wait never takes the last one."""
    return S("NOTIFY_NOW_MAX_PER_DAY", int) - _sent_today(store().rows("Owner_Actions"))


def open_rows(tier=None):
    return [r for r in store().rows("Owner_Actions") if r.get("status") in ("OPEN", "QUEUED") and (tier is None or r.get("tier") == tier)]


def send(kind, text, buttons=(), episode=None, tier="week", default=None, expires_h=None, urgent=False, dedupe_key=None):
    """Create the owner action (and deliver it if its tier says so). Returns the row id, or the id of an identical open row."""
    tier = tier if tier in TIERS else "week"
    if _on(): buttons, default, expires_h, dedupe_key = _shape(kind, episode, buttons, default, expires_h, dedupe_key)
    st = store(); key = dedupe_key or f"{kind}|{episode or ''}"
    if _on() and kind == "ypp_tier":                              # v12 B-OWNER (R7's round 2): the tier is told ONCE - any row with its key, open or closed, stands
        for r in st.rows("Owner_Actions"):
            if r.get("dedupe_key") == key: return r["id"]
    for r in open_rows():
        if r.get("dedupe_key") == key: return r["id"]
    aid = _new_id(); exp = (now_utc() + dt.timedelta(hours=float(expires_h))).strftime("%Y-%m-%dT%H:%M:%SZ") if expires_h else ""
    row = {"id": aid, "created": iso(), "tier": tier, "kind": str(kind)[:40], "episode_id": episode or "", "text": str(text)[:1500],
           "buttons": json.dumps([[str(l)[:30], str(v)[:120]] for l, v in buttons]), "default_action": default or "", "expires_at": exp,
           "status": "OPEN", "answered_at": "", "answer": "", "channel": "", "delivered_at": "", "dedupe_key": key, "urgent": "TRUE" if urgent else ""}
    st.append("Owner_Actions", [row])
    if tier == "now": _deliver_now(row)
    return aid


def _shape(kind, episode, buttons, default, expires_h, dedupe_key):
    """v12 B-OWNER (switch TWO_SCREENS_ON): what the register says a row of this kind must carry, each only where its caller gave none.
    A HOLD without a button gets ("Done", "OK") - his tap closes it; an inform row outside STANDING_KINDS closes by itself after INFORM_KEEP_H hours
    and its key holds the India date (a second one on another day is a new row, never swallowed); a CARD with buttons and no default or no expiry is
    stored with CARD_FALLBACK and 72 hours, an error is logged and one `card_rule` row a kind a day names it (nothing he is sent may be lost)."""
    buttons = list(buttons or ()); k = klass(kind)
    if k == HOLD and not buttons: buttons = [("Done", "OK")]
    if k == INFORM and kind not in STANDING_KINDS:
        if expires_h is None: expires_h = INFORM_KEEP_H
        if dedupe_key is None: dedupe_key = f"{kind}|{episode or ''}|{_india_day()}"
    if k == CARD and buttons and kind not in STANDING_KINDS and (not default or not expires_h):
        log(f"a card of kind {kind} was sent without a default or an expiry: stored with the fallback default and 72 hours", "ERROR")
        default = default or CARD_FALLBACK; expires_h = expires_h or 72
        try: send("card_rule", f"A message of kind '{kind}' was sent without a default or an expiry. It was given '{CARD_FALLBACK}' and 72 hours.",
                  tier="week", dedupe_key=f"card_rule|{kind}|{_india_day()}")
        except Exception as e: log(f"the card rule's report was not written: {scrub(e)[:120]}", "WARN")
    return buttons, default, expires_h, dedupe_key


def _email_body(row):
    btns = json.loads(row.get("buttons") or "[]")
    links = " &nbsp;|&nbsp; ".join(f"<a href='{link(v, row['id'])}'>{l}</a>" for l, v in btns if link(v, row["id"]))
    dflt = f"<p><i>If you do nothing: {row['default_action']}" + (f" (at {row['expires_at'][:16].replace('T', ' ')} UTC)" if row.get("expires_at") else "") + "</i></p>" if row.get("default_action") else ""
    return f"<p>{row['text']}</p><p>{links}</p>{dflt}"


def _deliver_now(row):
    """Email now (WhatsApp later through wa.send when that module exists). Caps and quiet hours apply unless urgent; a held message is QUEUED and flushed by tick()."""
    st = store(); urgent = str(row.get("urgent")) == "TRUE"
    rows = st.rows("Owner_Actions")
    if not urgent and (in_quiet_hours() or _sent_today(rows) >= S("NOTIFY_NOW_MAX_PER_DAY", int)):
        st.update("Owner_Actions", "id", row["id"], {"status": "QUEUED"}); log(f"owner message queued ({row['kind']}): quiet hours or daily cap"); return False
    sent = False
    try:
        from whatifs import publish as PUB
        sent = bool(PUB.email(("URGENT: " if urgent else "") + str(row["text"])[:70], _email_body(row)))
    except Exception as e: log(f"owner message email failed: {scrub(e)[:120]}", "WARN")
    try:                                                          # v9.4b hook: WhatsApp when configured
        from whatifs import wa as WA
        if hasattr(WA, "send_action"): WA.send_action(row)
    except Exception: pass
    st.update("Owner_Actions", "id", row["id"], {"status": "OPEN", "channel": "email", "delivered_at": iso()})
    return sent


def flush():
    """Deliver QUEUED 'now' messages once quiet hours end / the cap allows."""
    n = 0
    for r in store().rows("Owner_Actions"):
        if r.get("status") == "QUEUED" and r.get("tier") == "now":
            if _deliver_now(r): n += 1
            else: break
    return n


def answer(aid, choice, who="owner"):
    """The owner's tap. Verbs the old flows understand (PICK..., MODE..., APPROVE DRAFT...) are passed to preview.decide; others are recorded + handled."""
    _ensure_handlers()
    st = store(); row = next((r for r in st.rows("Owner_Actions") if r.get("id") == aid), None)
    if not row: raise RuntimeError(f"unknown action {aid}")
    if row.get("status") not in ("OPEN", "QUEUED"): return f"{aid} already {row.get('status')}"
    st.update("Owner_Actions", "id", aid, {"status": "ANSWERED", "answered_at": iso(), "answer": str(choice)[:120], "channel": who})
    out = ""
    try:
        if re.match(r"^(PICK |MODE |APPROVE DRAFT|REJECT DRAFT|APPROVE SHEET|REDO SHEET)", str(choice).upper()):
            from whatifs import preview as PV
            out = str(PV.decide(choice))
        h = HANDLERS.get(row.get("kind"))
        if h: out = str(h(row, choice) or out)
    except Exception as e: log(f"action handler failed for {aid}: {scrub(e)[:160]}", "WARN"); out = f"recorded (handler failed: {str(e)[:80]})"
    log(f"owner action {aid} ({row.get('kind')}): {choice}"); return out or "recorded"


def expire_defaults(now=None):
    """Silence = the default. Runs the registered default once and marks the row DEFAULTED (or EXPIRED when there is no default)."""
    _ensure_handlers()
    now = now or now_utc(); st = store(); n = 0
    for r in st.rows("Owner_Actions"):
        if r.get("status") not in ("OPEN", "QUEUED"): continue
        t = parse_iso(r.get("expires_at"))
        if not t or now < t: continue
        status = "DEFAULTED" if r.get("default_action") else "EXPIRED"
        st.update("Owner_Actions", "id", r["id"], {"status": status, "answered_at": iso(), "answer": r.get("default_action") or ""})
        d = DEFAULTS.get(r.get("kind"))
        if d:
            try: d(r)
            except Exception as e: log(f"default action failed for {r['id']}: {scrub(e)[:160]}", "WARN")
        n += 1
    return n


def _digest_due(now=None):
    now = (now or now_utc()).astimezone(IST)
    days = [d.strip()[:3] for d in str(S("DIGEST_DAYS") or "Tue,Sat,Sun").split(",")]
    if now.strftime("%a") not in days or now.hour < S("DIGEST_HOUR_IST", int): return False
    return str(S("DIGEST_SENT_AT") or "")[:10] != now.date().isoformat()


def digest(now=None, force=False):
    """The Tue/Sat/Sun evening message: this week's videos, money vs cap, open actions (the 'This week' tier lives here). One per day at most."""
    if not force and not _digest_due(now): return False
    from whatifs import governor as G
    st = store(); eps = st.rows("Episodes"); week_ago = (now_utc() - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = [e for e in eps if str(e.get("slot_et", "")) >= week_ago]
    opens = [r for r in open_rows("week") + open_rows("now") if r.get("kind") not in INFORM_KINDS]      # v12 V4: "Nothing to do" is never shown as waiting
    if _on(): opens = needs()                                                          # v12 B-OWNER: "Waiting for you" is "Needs you" - one definition (notify.needs)
    try: spent = G.own_spend_inr()                                                     # v12 V4: his own money (= the list-price spend with STRATEGY_ON FALSE)
    except Exception: spent = 0.0
    try:
        from whatifs.org import finance as FIN
        cover = FIN.cover() if FIN.on() else G.credit_cover_inr()
    except Exception: cover = 0.0
    try:
        from whatifs import scoreboard as SB; sb = SB.line(now)                      # v12 V4: the scoreboard is the digest's first paragraph ("" with STRATEGY_ON FALSE)
    except Exception as e: sb = ""; log(f"digest: the scoreboard line was not built: {scrub(e)[:120]}", "WARN")
    lines = (["<p>" + sb.replace("&", "&amp;").replace("<", "&lt;") + "</p>"] if sb else [])
    if S("STRATEGY_ON", bool):                                                               # v12 V4: what he reads of his money
        lines.append(f"<p><b>Mode:</b> {G.budget_mode()} · Your money this month: Rs {spent:.0f} of Rs {G.cap_inr():.0f}." + (f" Claude credit paid another Rs {cover:.0f}." if cover > 0 else "") + "</p>")
    else: lines.append(f"<p><b>Mode:</b> {G.budget_mode()} · <b>spend this month:</b> Rs {spent:.0f} of Rs {G.cap_inr():.0f}"
                       + (f" (about Rs {cover:.0f} of it covered by free credits)" if cover > 0 else "") + "</p>")
    lines.append("<p><b>This week:</b> " + (", ".join(f"{str(e.get('title') or e.get('episode_id'))[:50]} [{e.get('status')}]" for e in recent) or "no videos yet") + "</p>")
    if opens:
        lines.append("<p><b>Waiting for you (optional):</b></p><ul>" + "".join(f"<li>{r['text'][:160]} " + " ".join(f"<a href='{link(v, r['id'])}'>{l}</a>" for l, v in json.loads(r.get('buttons') or '[]') if link(v, r['id'])) + "</li>" for r in opens[:12]) + "</ul>")
    else: lines.append("<p>Nothing is waiting for you.</p>")
    try:
        from whatifs import publish as PUB
        PUB.email("Reality Engine: " + (now or now_utc()).astimezone(IST).strftime("%a %d %b") + " digest", "".join(lines))
    except Exception as e: log(f"digest email failed: {scrub(e)[:120]}", "WARN")
    set_setting("DIGEST_SENT_AT", (now or now_utc()).astimezone(IST).isoformat()); return True      # v10.2: the digest's own IST date (was wall-clock UTC)


def tick():
    """Called from the half-hourly tick: flush queued messages, run defaults, send the digest when due. Never raises."""
    try:
        from whatifs import builds as BD; BD.ensure_registered()      # v9.4a (WP3): Merge / Reject / auto-merge handlers
        from whatifs import visual_lab as VL; VL.register()            # v9.4a: Visual Lab answers
    except Exception: pass
    out = {}
    for name, fn in (("flushed", flush), ("defaulted", expire_defaults), ("digest", digest)):
        try: out[name] = fn()
        except Exception as e: log(f"notify {name} failed: {scrub(e)[:120]}", "WARN")
    return out
