"""v10.1 (K146): search-demand score for bench premises (compliant: YouTube search.list, own 100-calls/day bucket, 1 unit each, plus
videos.list statistics, verified 8 Nov 2026; no autocomplete scraping). Daily, up to DEMAND_DAILY READY bench premises are scored once:
median views of the top results for the premise's headline in the last DEMAND_LOOKBACK_DAYS, as log10, mapped to 0..1. The score adds
DEMAND_WEIGHT x score to the premise's combined bench score (once; demand_json records it)."""
from __future__ import annotations
import json, math, statistics, datetime as dt
from whatifs.core import S, log, store, iso, now_utc, FAKE, scrub

def _views_for(query):
    if FAKE: return [int(10 ** (3 + (len(query) % 4))) for _ in range(5)]
    import requests
    from whatifs.publish import YT, gheaders
    after = (now_utc() - dt.timedelta(days=S("DEMAND_LOOKBACK_DAYS", int))).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = requests.get(YT + "search", params={"part": "snippet", "q": query, "type": "video", "order": "viewCount", "publishedAfter": after,
                                            "maxResults": 10, "relevanceLanguage": "en", "safeSearch": "strict"}, headers=gheaders(), timeout=30).json()
    ids = [i["id"]["videoId"] for i in r.get("items", []) if i.get("id", {}).get("videoId")]
    if not ids: return []
    v = requests.get(YT + "videos", params={"part": "statistics", "id": ",".join(ids)}, headers=gheaders(), timeout=30).json()
    return [int(x.get("statistics", {}).get("viewCount") or 0) for x in v.get("items", [])]

def score_views(views):
    """0..1: log10(median of the top 5) from 3 (1k views) to 7 (10M views)."""
    if not views: return 0.0
    m = statistics.median(sorted(views, reverse=True)[:5]) or 1
    return max(0.0, min(1.0, (math.log10(m) - 3) / 4))

def run():
    if not S("DEMAND_SCORE_ON", bool): return 0
    st = store(); n = 0
    for r in st.rows("Premise_Bench"):
        if n >= S("DEMAND_DAILY", int): break
        if str(r.get("status")) != "READY": continue
        try: dj = json.loads(r.get("demand_json") or "{}")
        except Exception: dj = {}
        if "search_score" in dj: continue
        q = str(r.get("headline") or r.get("premise") or "")[:90]
        try: views = _views_for(q)
        except Exception as e: log(f"demand check failed: {scrub(e)[:100]}", "WARN"); break
        sc = round(score_views(views), 3); dj.update({"search_score": sc, "search_q": q, "search_at": iso()})
        try: comb = float(r.get("combined") or 0)
        except ValueError: comb = 0.0
        st.update("Premise_Bench", "bench_id", r["bench_id"], {"demand_json": json.dumps(dj)[:1500], "combined": round(comb + S("DEMAND_WEIGHT", float) * sc, 2)})
        n += 1
    if n: log(f"search demand scored for {n} bench premise(s)")
    return n
