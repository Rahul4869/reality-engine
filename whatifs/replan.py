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

def proposals(now=None):
    now = now or now_utc(); free = free_inr(now); d = days_left(now); out = []
    per_short = S("REPLAN_SHORT_INR", float)
    cost2 = 0.5 * d * per_short
    if S("SHORTS_PER_DAY", float) < S("REPLAN_MAX_SHORTS_PER_DAY", float) and free >= cost2:
        out.append({"rung": 2, "key": "SHORTS_PER_DAY", "to": str(min(S("REPLAN_MAX_SHORTS_PER_DAY", float), S("SHORTS_PER_DAY", float) + 0.5)),
                    "cost": round(cost2), "why": "more hook-style tests per week (the learning core gets data faster)"})
        free -= cost2
    every = S("SHORTS_KLING_EVERY", int); kling = S("PRICE_KLING_USD", float) * (S("USD_INR", float) or 92.0)
    if every > 1:
        shorts_left = d * S("SHORTS_PER_DAY", float)
        cost3 = (shorts_left / (every - 1) - shorts_left / every) * kling
        if free >= cost3:
            out.append({"rung": 3, "key": "SHORTS_KLING_EVERY", "to": str(every - 1), "cost": round(cost3), "why": "more Shorts open on a new animated shot"})
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
