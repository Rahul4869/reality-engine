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
    for mod, fn in (("whatifs.builds", "ensure_registered"), ("whatifs.visual_lab", "register"), ("whatifs.wa", "register"), ("whatifs.caretaker", "register"), ("whatifs.bakeoff", "register"), ("whatifs.steward", "register"), ("whatifs.contract", "register"), ("whatifs.specials", "register"), ("whatifs.sheets", "register"), ("whatifs.breakout", "register"), ("whatifs.ladder", "register"), ("whatifs.replan", "register"), ("whatifs.org.memos", "register"), ("whatifs.org.execute", "register")):
        try: getattr(__import__(mod, fromlist=[fn]), fn)()
        except Exception as e: log(f"handlers from {mod} not loaded: {scrub(e)[:80]}", "WARN")

def register(kind, on_answer=None, on_default=None):
    if on_answer: HANDLERS[kind] = on_answer
    if on_default: DEFAULTS[kind] = on_default


def _link(verb, aid):
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


def open_rows(tier=None):
    return [r for r in store().rows("Owner_Actions") if r.get("status") in ("OPEN", "QUEUED") and (tier is None or r.get("tier") == tier)]


def send(kind, text, buttons=(), episode=None, tier="week", default=None, expires_h=None, urgent=False, dedupe_key=None):
    """Create the owner action (and deliver it if its tier says so). Returns the row id, or the id of an identical open row."""
    tier = tier if tier in TIERS else "week"
    st = store(); key = dedupe_key or f"{kind}|{episode or ''}"
    for r in open_rows():
        if r.get("dedupe_key") == key: return r["id"]
    aid = _new_id(); exp = (now_utc() + dt.timedelta(hours=float(expires_h))).strftime("%Y-%m-%dT%H:%M:%SZ") if expires_h else ""
    row = {"id": aid, "created": iso(), "tier": tier, "kind": str(kind)[:40], "episode_id": episode or "", "text": str(text)[:1500],
           "buttons": json.dumps([[str(l)[:30], str(v)[:120]] for l, v in buttons]), "default_action": default or "", "expires_at": exp,
           "status": "OPEN", "answered_at": "", "answer": "", "channel": "", "delivered_at": "", "dedupe_key": key, "urgent": "TRUE" if urgent else ""}
    st.append("Owner_Actions", [row])
    if tier == "now": _deliver_now(row)
    return aid


def _email_body(row):
    btns = json.loads(row.get("buttons") or "[]")
    links = " &nbsp;|&nbsp; ".join(f"<a href='{_link(v, row['id'])}'>{l}</a>" for l, v in btns if _link(v, row["id"]))
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
    opens = open_rows("week") + open_rows("now")
    try:
        from whatifs.costguard import month_spend
        spent = month_spend()
    except Exception: spent = 0.0
    try: cover = G.credit_cover_inr()
    except Exception: cover = 0.0
    lines = [f"<p><b>Mode:</b> {G.budget_mode()} · <b>spend this month:</b> Rs {spent:.0f} of Rs {G.cap_inr():.0f}"
             + (f" (about Rs {cover:.0f} of it covered by free credits)" if cover > 0 else "") + "</p>",
             "<p><b>This week:</b> " + (", ".join(f"{str(e.get('title') or e.get('episode_id'))[:50]} [{e.get('status')}]" for e in recent) or "no videos yet") + "</p>"]
    if opens:
        lines.append("<p><b>Waiting for you (optional):</b></p><ul>" + "".join(f"<li>{r['text'][:160]} " + " ".join(f"<a href='{_link(v, r['id'])}'>{l}</a>" for l, v in json.loads(r.get('buttons') or '[]') if _link(v, r['id'])) + "</li>" for r in opens[:12]) + "</ul>")
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
