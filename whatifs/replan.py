"""The mid-month re-planner: invests money that is truly free in breakout steps, each one a WhatsApp decision the owner can veto. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json
from whatifs.core import S, log, store, iso, now_utc, set_setting, scrub

def free_inr(now=None):
    from whatifs import governor as G
    now = now or now_utc()
    import calendar
    last_week = now.day > calendar.monthrange(now.year, now.month)[1] - 7
    left = max(0, min(G.episodes_left_this_month(), G.max_long_videos() - G.long_videos_this_month()))
    floor = S("REPLAN_LASTWEEK_FLOOR_INR" if last_week else "REPLAN_FLOOR_INR", float)
    return G.production_room_inr() - left * G.full_episode_inr() - floor

def days_left(now=None):
    import calendar
    now = now or now_utc(); return calendar.monthrange(now.year, now.month)[1] - now.day + 1

def short_inr():
    """What one more Short really costs: the Shorts Studio's own estimate, weighted by the shares of the Short formats (every second is a paid clip)."""
    from whatifs import shorts2 as SH2, formats as FMT
    sh = FMT.short_shares(); tot = sum(sh.values()) or 1
    return sum(SH2.est_inr(f) * w for f, w in sh.items()) / tot

def proposals(now=None):
    """What truly free money could buy: ONE more Short a week for the rest of the month (more topics tested with real viewers), up to
    REPLAN_MAX_SHORTS_PER_WEEK and never past SHORTS_PER_MONTH's own room. Nothing changes before the owner's tap."""
    now = now or now_utc(); free = free_inr(now); d = days_left(now); out = []
    cur = S("SHORTS_PER_WEEK", int); cost2 = d / 7.0 * short_inr()
    if cur < S("REPLAN_MAX_SHORTS_PER_WEEK", int) and d >= 7 and free >= cost2:
        out.append({"rung": 2, "key": "SHORTS_PER_WEEK", "to": str(cur + 1), "cost": round(cost2), "why": "one more Short a week: one more topic a week is tested with real viewers"})
    return out

def weekly(now=None):
    """Monday: one card with the proposals (Approve all / Not now). Returns the proposals sent."""
    now = now or now_utc()
    if not S("REPLAN_ON", bool) or now.weekday() != 0 or str(S("REPLAN_LAST") or "")[:10] == now.strftime("%Y-%m-%d"): return []
    set_setting("REPLAN_LAST", iso(now))
    props = proposals(now)
    if not props: return []
    from whatifs import notify as NT
    txt = "Money check: Rs %.0f is truly free this month (long slots and the safety floor are already set aside). Invest it?\n" % free_inr(now)
    txt += "\n".join(f"- {p['why']}: {p['key']} -> {p['to']} (about Rs {p['cost']})" for p in props)
    set_setting("REPLAN_PENDING", json.dumps(props))
    NT.send("replan", txt, [("Approve all", "REPLAN GO"), ("Not now", "REPLAN NO")], tier="digest", default="not now", expires_h=72,
            dedupe_key=f"replan|{now:%Y-%m-%d}")
    return props

def _answer(row, choice):
    if str(choice).upper().startswith("REPLAN GO"):
        props = json.loads(S("REPLAN_PENDING") or "[]"); orig = json.loads(S("REPLAN_ORIGINALS") or "{}")
        for p in props:
            orig.setdefault(p["key"], str(S(p["key"]))); set_setting(p["key"], p["to"])
        set_setting("REPLAN_ORIGINALS", json.dumps(orig)); set_setting("REPLAN_MONTH", now_utc().strftime("%Y-%m"))
        return f"done: {len(props)} change(s) until the month ends"
    return "kept as is"

def month_restore(now=None):
    """At a new month: the owner's own values come back."""
    now = now or now_utc(); mk = now.strftime("%Y-%m")
    if str(S("REPLAN_MONTH") or "") in ("", mk): return False
    for k, v in json.loads(S("REPLAN_ORIGINALS") or "{}").items(): set_setting(k, v)
    set_setting("REPLAN_ORIGINALS", "{}"); set_setting("REPLAN_MONTH", ""); log("re-planner: last month's temporary changes undone")
    return True

def register():
    from whatifs import notify as NT
    NT.register("replan", on_answer=_answer)
