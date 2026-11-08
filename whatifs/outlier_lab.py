"""v10 Outlier Lab (K142): every day, up to OUTLIER_LAB_DAILY videos that are doing unusually well in our wider space (YouTube search, last 14 days,
by views; one search call = 100 quota units, inside the separate search bucket) are WATCHED by Gemini Flash (first OUTLIER_LAB_SECONDS only,
public URL, about ₹0.5 each). Each becomes a technique card (hook device, first frame, cut rhythm, sound moment, caption style, why it works,
how to adapt without copying) and goes through the technique intake judge (craft.intake_technique): value, fit and risk decide whether it
becomes active, a trial, parked or rejected. Never copies titles, scenes or lines (K99). Paid from the growth allowance; never near a release."""
from __future__ import annotations
import json
from whatifs.core import S, log, store, iso, now_utc, FAKE, scrub

def _search():
    if FAKE: return [{"id": "FAKEvid1", "title": "What if the Sun vanished for 8 minutes"}]
    import requests, datetime as dt
    from whatifs.publish import YT, gheaders
    after = (now_utc() - dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    q = str(S("OUTLIER_LAB_QUERY") or "what if")
    r = requests.get(YT + "search", params={"part": "snippet", "q": q, "type": "video", "order": "viewCount", "publishedAfter": after, "maxResults": 15,
                                            "relevanceLanguage": "en", "safeSearch": "strict"}, headers=gheaders(), timeout=30).json()
    return [{"id": i["id"]["videoId"], "title": i["snippet"]["title"]} for i in r.get("items", []) if i.get("id", {}).get("videoId")]

def run():
    if not S("OUTLIER_LAB_ON", bool): return []
    from whatifs import governor as G, orchestra as OR
    if not OR.heavy_allowed(what="Outlier Lab"): return []
    seen = {r.get("video_id") for r in store().rows("Outlier_Lab")}
    try: cands = [c for c in _search() if c["id"] not in seen][:S("OUTLIER_LAB_DAILY", int)]
    except Exception as e: log(f"Outlier Lab search failed: {scrub(e)[:100]}", "WARN"); return []
    from whatifs.models import ask_video
    from whatifs import craft as CR
    done = []
    for c in cands:
        ok, why = G.extras_allowed(1.0, "outlier")
        if not ok: log(f"Outlier Lab paused: {why}"); break
        card = ask_video("You are a short-form video craft analyst. Watch only what you are given. Describe the TECHNIQUE, never the content to copy. "
                         "JSON only: {hook_device, first_frame, cut_rhythm, sound_moment, caption_style, why_it_works, how_to_adapt}",
                         "Analyse this video's opening.", f"https://www.youtube.com/watch?v={c['id']}", S("OUTLIER_LAB_SECONDS", int))
        status = "no answer"
        if isinstance(card, dict) and card.get("why_it_works"):
            try:
                res = CR.intake_technique({"video_id": c["id"], "title": c["title"], "source_url": f"https://www.youtube.com/watch?v={c['id']}",
                                           "hook_device": card.get("hook_device", ""), "first_3s_visual": card.get("first_frame", ""), "cut_rhythm": card.get("cut_rhythm", ""),
                                           "sound_moment": card.get("sound_moment", ""), "payoff_structure": card.get("caption_style", ""),
                                           "evidence": card.get("why_it_works", ""), "applies_when": card.get("how_to_adapt", "")}, None)
                status = str((res or {}).get("status") if isinstance(res, dict) else res)[:40]
            except Exception as e: status = f"intake failed: {str(e)[:60]}"
        store().append("Outlier_Lab", [{"ts": iso(), "video_id": c["id"], "title": str(c["title"])[:120], "status": status}])
        done.append(c["id"])
    return done
