"""Shorts Lab: the weekly list of winning Shorts for the owner to link to the full episode. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import statistics
from whatifs.core import S, log, store, now_utc, parse_iso, FAKE, scrub

def _shorts(days=7, now=None):
    """[(yt_id, posted_at, episode_id)] for reels (Episodes reel1..4) and hero/special Shorts posted in the last `days` days."""
    now = now or now_utc(); out = []
    for e in store().rows("Episodes"):
        t = parse_iso(e.get("slot_et"))
        if not t or (now - t).days > days or t > now: continue
        for k in ("reel1_yt", "reel2_yt", "reel3_yt", "reel4_yt"):
            v = str(e.get(k) or "")
            if v and not v.startswith("FAKE"): out.append((v, t, e.get("episode_id")))
    for r in store().rows("Specials"):
        t = parse_iso(r.get("ts")); v = str(r.get("yt_id") or "")
        if v and t and (now - t).days <= days and not v.startswith("FAKE"): out.append((v, t, r.get("id")))
    return out

def views_many(ids):
    """{id: public views} in one call per 50 ids (1 quota unit each call). {} in fake mode or on error."""
    if FAKE or not ids: return {}
    import requests
    from whatifs.publish import YT, gheaders
    out = {}
    for i in range(0, len(ids), 50):
        try:
            r = requests.get(YT + "videos", params={"part": "statistics", "id": ",".join(ids[i:i + 50])}, headers=gheaders(), timeout=30).json()
            for it in r.get("items", []): out[it["id"]] = int(it.get("statistics", {}).get("viewCount") or 0)
        except Exception as e: log(f"Shorts views not read: {scrub(e)[:80]}", "WARN")
    return out

def link_pack(now=None, views=None):
    """Create the weekly winners card. Returns the list of Short ids listed."""
    now = now or now_utc(); shorts = [s for s in _shorts(7, now) if (now - s[1]).total_seconds() >= 24 * 3600]
    if not shorts: return []
    v = views if views is not None else views_many([s[0] for s in shorts])
    vals = [v[s[0]] for s in shorts if s[0] in v]
    if len(vals) < 2: return []
    med = statistics.median(vals)
    winners = sorted([s for s in shorts if v.get(s[0], 0) > med], key=lambda s: -v.get(s[0], 0))[:S("SHORTS_LINK_MAX", int)]
    if not winners: return []
    from whatifs import notify as NT
    links = "<br>".join(f"<a href='https://studio.youtube.com/video/{s[0]}/edit'>Short of {s[2]}</a> ({v[s[0]]} views) → Related video = the full episode" for s in winners)
    NT.send("linkpack", f"This week's winning Shorts: link each to its full episode (Studio, about 3 taps each):<br>{links}", [("Done", "LINKED")],
            tier="week", default="Shorts keep the description link and the comment", expires_h=24 * 6, dedupe_key=f"linkpack|{now:%G-W%V}")
    return [s[0] for s in winners]

def breakouts(now=None, views=None):
    """'Act now' card for a Short that is taking off (once per Short)."""
    now = now or now_utc(); shorts = [s for s in _shorts(2, now)]
    if len(shorts) < 1: return []
    v = views if views is not None else views_many([s[0] for s in shorts])
    rates = {s[0]: v.get(s[0], 0) / max(1.0, (now - s[1]).total_seconds() / 3600) for s in shorts if s[0] in v}
    if len(rates) < 2: return []
    med = statistics.median(rates.values()); out = []
    from whatifs import notify as NT
    for s in shorts:
        r = rates.get(s[0], 0)
        if med > 0 and r > S("SHORTS_BREAKOUT_X", float) * med:
            NT.send("breakout", f"A Short is taking off ({v[s[0]]} views, {r:.0f}/hour). Link it to its full episode now: "
                    f"<a href='https://studio.youtube.com/video/{s[0]}/edit'>open it in Studio</a> → Related video.", [("Done", "LINKED")],
                    tier="now", default="it keeps the description link", expires_h=48, dedupe_key=f"breakout|{s[0]}")
            out.append(s[0])
    return out

def weekly_count(now=None):
    return len(_shorts(7, now))

def allowed_today(now=None):
    """The 14-a-week ceiling (decision 6): False when the last 7 days already hold SHORTS_WEEKLY_CAP Shorts."""
    return weekly_count(now) < S("SHORTS_WEEKLY_CAP", int)
