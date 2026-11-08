"""v10.1 (K148): the North-Star tracker. Weekly, YouTube Analytics (verified metric names 8 Nov 2026: estimatedMinutesWatched, engagedViews,
subscribersGained/Lost; dimension creatorContentType) gives an UPPER-BOUND proxy of the 500-subscriber YPP tier (500 subs + 3 qualified uploads
in 90 days + 3,000 qualified long-form watch hours in 365 days, or 3M qualified Shorts views in 90 days). Studio's tracker is the only authority,
so the owner gets ONE card 'check Studio > Earn and apply' when the proxy passes. Progress goes to YPP_PROGRESS for the dashboard."""
from __future__ import annotations
import json, datetime as dt
from whatifs.core import S, log, store, iso, now_utc, FAKE, scrub, set_setting

def _query(start, end, metrics, dims="creatorContentType"):
    if FAKE: return {"rows": []}
    import requests
    from whatifs.publish import gheaders
    r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", params={"ids": "channel==MINE", "startDate": start, "endDate": end,
                     "metrics": metrics, "dimensions": dims}, headers=gheaders(), timeout=30)
    return r.json() if r.status_code < 300 else {"rows": []}

def progress(now=None):
    now = now or now_utc(); d = lambda n: (now - dt.timedelta(days=n)).strftime("%Y-%m-%d")
    y = _query(d(365), d(0), "estimatedMinutesWatched,subscribersGained,subscribersLost")
    hours, subs = 0.0, 0
    for row in y.get("rows", []) or []:
        kind, mins, g, l = row[0], float(row[1]), int(row[2]), int(row[3]); subs += g - l
        if kind != "shorts": hours += mins / 60
    q = _query(d(90), d(0), "engagedViews")
    shorts = sum(int(r[1]) for r in (q.get("rows") or []) if r[0] == "shorts")
    uploads = len([e for e in store().rows("Episodes") if e.get("yt_id") and str(e.get("slot_et", "")) >= d(90)])
    return {"subs": subs, "hours": round(hours, 1), "shorts_views_90d": shorts, "uploads_90d": uploads, "at": iso()}

def check(now=None):
    if not S("YPP_WATCH_ON", bool): return None
    try: p = progress(now)
    except Exception as e: log(f"YPP progress not read: {scrub(e)[:100]}", "WARN"); return None
    set_setting("YPP_PROGRESS", json.dumps(p))
    ok = p["subs"] >= 500 and p["uploads_90d"] >= 3 and (p["hours"] >= 3000 or p["shorts_views_90d"] >= 3_000_000)
    if ok:
        from whatifs import notify as NT
        NT.send("ypp_tier", f"You may now qualify for YouTube's 500-subscriber tier ({p['subs']} subs, ~{p['hours']:.0f} long-form hours). Open Studio > Earn: if it says eligible, apply. This unlocks Hype, Shopping affiliate and memberships.",
                tier="now", urgent=True, dedupe_key="ypp_tier_500")
    return p
