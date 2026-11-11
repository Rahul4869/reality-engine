"""Breakout Protocol checks and tools: promise-paid, the aliveness (still-photo) detector, the Breakout Score and the 48-hour breakout monitor. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, statistics, subprocess
import numpy as np
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, scrub

# ------------------------------------------------------------------ 1. the promise is paid early
def promise_start(shots, units):
    for i, s in enumerate(shots or []):
        if s.get("promise") and i < len(units or []):
            return float(units[i].get("start", 0) or 0)
    return None

# ------------------------------------------------------------------ 2. the still detector
def _frames(path, fps=2, width=320):
    """Grey frames at `fps` (H x W uint8 arrays) via ffmpeg."""
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                        capture_output=True, text=True, timeout=60)
    w0, h0 = [int(x) for x in pr.stdout.strip().split(",")[:2]]
    h = int(round(h0 * width / w0 / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={width}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, timeout=1800).stdout
    n = len(raw) // (width * h)
    return np.frombuffer(raw[:n * width * h], np.uint8).reshape(n, h, width)

def aliveness(path, fps=2, width=None):
    """{'alive_share', 'dead_stretches': [(start_s, end_s)], 'windows'} - residual motion after removing each frame pair's camera move."""
    import cv2
    fr = _frames(path, fps, width or S("ALIVE_DETECT_WIDTH", int))
    if len(fr) < 2: return {"alive_share": 1.0, "dead_stretches": [], "windows": 0}
    delta, share_min = S("ALIVE_PIXEL_DELTA", float), S("ALIVE_PIXEL_SHARE", float); alive = []
    for a, b in zip(fr[:-1], fr[1:]):
        pa = cv2.goodFeaturesToTrack(a, 200, 0.01, 6)
        edge = cv2.dilate(cv2.Canny(b, 60, 160), np.ones((5, 5), np.uint8)) > 0       # v11: interpolation noise of a camera move lives on sharp edges
        res = float(((cv2.absdiff(a, b) > delta) & ~edge)[8:-8, 8:-8].mean())
        if pa is not None and len(pa) >= 8:
            pb, st, _ = cv2.calcOpticalFlowPyrLK(a, b, pa, None)
            good = st.reshape(-1) == 1
            if good.sum() >= 8:
                m, _ = cv2.estimateAffinePartial2D(pa[good], pb[good])
                if m is not None:
                    warped = cv2.warpAffine(a, m, (a.shape[1], a.shape[0]), borderMode=cv2.BORDER_REFLECT)
                    res = float(((cv2.absdiff(warped, b) > delta) & ~edge)[8:-8, 8:-8].mean())   # real change, off the edges
        alive.append(res > share_min)
    dead, start = [], None
    for k, ok in enumerate(alive + [True]):
        if not ok and start is None: start = k
        if ok and start is not None: dead.append((start / fps, k / fps)); start = None
    return {"alive_share": round(sum(alive) / len(alive), 3), "dead_stretches": [(round(a, 1), round(b, 1)) for a, b in dead], "windows": len(alive)}

# ------------------------------------------------------------------ 3. the Breakout Score
WEIGHTS = {"idea": 20, "packaging": 25, "hook": 15, "retention": 15, "story": 10, "visual": 8, "share": 4, "sound": 3}

def _clip(x, lo=0.0, hi=1.0):
    try: return max(lo, min(hi, float(x)))
    except (TypeError, ValueError): return None

def components(d, ledger, room=None, critique=None):
    """0..1 per component from evidence already recorded; None = no evidence (the weight is re-spread, and 'missing' is reported)."""
    status = {r.get("feature"): r.get("status") for r in ledger or []}
    def ok(f): return 1.0 if status.get(f) == "PASS" else (0.0 if status.get(f) == "FAIL" else None)
    crit = critique or d.get("critique") or {}                 # the 6-point self-review the final check measured
    spine = (room or {}).get("spine") or {}
    c = {}
    idea = d.get("premise_score") or spine.get("score") or spine.get("bench_score")
    c["idea"] = _clip(float(idea) / 10) if idea else None
    pk = [x for x in (ok("thumbnails"), ok("titles")) if x is not None]
    c["packaging"] = sum(pk) / len(pk) if pk else None
    hk = d.get("hook_score") or (d.get("hook") or {}).get("score")
    c["hook"] = _clip(float(hk) / 10) if hk else (_clip(crit.get("hook", 0) / 10) if crit.get("hook") else None)
    rc = d.get("retention_check") or {}
    c["retention"] = (1.0 if not rc.get("issues") else max(0.0, 1 - 0.2 * len(rc.get("issues") or []))) if rc else None
    oc = (d.get("owners_cut") or {}).get("mean")
    c["story"] = (_clip(crit.get("humour", 0) / 10 * 0.5 + crit.get("clarity", 0) / 10 * 0.5) if crit.get("humour") is not None and crit.get("clarity") is not None
                  else (_clip(float(oc) / 10) if oc else None))
    al = d.get("aliveness") or {}
    c["visual"] = _clip(al.get("alive_share")) if al else ok("real_motion")
    c["share"] = 1.0 if d.get("emotion_beat") else None
    c["sound"] = ok("music_bed")
    return c

def score(d, ledger, room=None, critique=None):
    c = components(d, ledger, room, critique)
    have = {k: v for k, v in c.items() if v is not None}
    if not have: return {"score": None, "components": c, "missing": list(c)}
    wsum = sum(WEIGHTS[k] for k in have)
    s = sum(WEIGHTS[k] * have[k] for k in have) / wsum * 100
    weakest = min(have, key=lambda k: have[k])
    return {"score": round(s, 1), "components": {k: (None if v is None else round(v, 2)) for k, v in c.items()},
            "missing": [k for k, v in c.items() if v is None], "weakest": weakest,
            "grade": "breakout-grade" if s >= S("BREAKOUT_AMPLIFY_AT", float) else ("ok" if s >= S("BREAKOUT_BAR", float) else "below the bar")}

def record(ep, fmt, res):
    try:
        store().append("Breakout_Scores", [{"ts": iso(), "episode_id": ep, "format": fmt, "score": res.get("score"), "grade": res.get("grade", ""),
                                            "weakest": res.get("weakest", ""), "components": json.dumps(res.get("components") or {}), "missing": ",".join(res.get("missing") or [])}])
    except Exception as e: log(f"breakout score not recorded: {scrub(e)}", "WARN", ep)

# ------------------------------------------------------------------ 4. the 48-hour breakout monitor
def _views(yt_ids):
    """Public view counts now (YouTube Data API videos.list, 1 unit per 50 ids)."""
    if FAKE:
        import random
        return {y: random.Random(y).randint(20, 3000) for y in yt_ids}
    import requests
    from whatifs.publish import gheaders
    out = {}
    for k in range(0, len(yt_ids), 50):
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=gheaders(), params={"part": "statistics", "id": ",".join(yt_ids[k:k + 50])}, timeout=30)
        for it in (r.json().get("items") or []): out[it["id"]] = int(it.get("statistics", {}).get("viewCount", 0) or 0)
    return out

def _recent_videos(now):
    """(key, yt_id, published, kind) for long videos and Shorts published in the last BREAKOUT_WINDOW_H + 26 hours."""
    out = []
    from whatifs.brain import _short_ids
    for e in store().rows("Episodes"):
        if e.get("yt_id") and e.get("slot_et"): out.append((e["episode_id"], e["yt_id"], e["slot_et"], "long"))
    for key, y, pub, _, _ in _short_ids(): out.append((key, y, pub, "short"))
    win = (S("BREAKOUT_WINDOW_H", float) + 26) * 3600
    return [x for x in out if parse_iso(x[2]) and 0 <= (now - parse_iso(x[2])).total_seconds() <= win]

def short_winner(v, hist):
    """(is it a winner, the base it was measured against): a Short's public views at one mark against the median of the channel's EARLIER Shorts at
    the SAME mark (SHORTS_BREAKOUT_X times it); with fewer than BREAKOUT_MIN_HISTORY earlier Shorts the line is SHORTS_WINNER_MIN_VIEWS."""
    base = statistics.median(hist) if len(hist) >= S("BREAKOUT_MIN_HISTORY", int) else None
    if base: return v >= S("SHORTS_BREAKOUT_X", float) * base, base
    return v >= S("SHORTS_WINNER_MIN_VIEWS", float), None

def monitor(now=None):
    """Called by the tick. Records the public views at the 24-hour and the 48-hour mark (real-time: YouTube's own numbers are 48 to 72 hours late).
    A LONG video at BREAKOUT_MULT times the usual 48-hour views gets ONE card with follow-ups to approve. A standalone SHORT that is a winner at
    either mark (`short_winner`) gets its follow-up ordered by code, with a clock (`ladder.order_followup`). Returns the breakouts found."""
    if not S("BREAKOUT_MONITOR_ON", bool): return []
    now = now or now_utc(); st = store()
    rows = {r.get("yt_id"): r for r in st.rows("Monitor48")}
    vids = _recent_videos(now)
    if not vids: return []
    views = _views([v[1] for v in vids])
    found = []
    for key, y, pub, kind in vids:
        age_h = (now - parse_iso(pub)).total_seconds() / 3600
        col = "v24" if age_h < S("BREAKOUT_WINDOW_H", float) else "v48"
        row = rows.get(y) or {"yt_id": y, "video_key": key, "kind": kind, "published": pub}
        if row.get(col) not in (None, ""): continue
        if age_h < 24: continue
        row[col] = views.get(y, 0); row["updated"] = iso(now)
        if y in rows: st.update("Monitor48", "yt_id", y, row)
        else: st.append("Monitor48", [row]); rows[y] = row
        if kind == "short":                                       # v12 V2c-b: the fast clock of the ladder - judged at BOTH marks, against the same mark
            from whatifs import ladder as LAD
            if not LAD.row(key): continue                             # only a standalone Short has a topic to follow up (never a cut-down reel)
            own = {x.get("id") for x in LAD.rows()}                    # ... and it is compared with its own kind only: cut-down reels, pilots and cast reels are other products
            hist = [float(r[col]) for r in st.rows("Monitor48") if r.get("kind") == "short" and r.get(col) not in (None, "") and r.get("yt_id") != y and r.get("video_key") in own]
            hit, base = short_winner(float(row[col]), hist)
            if hit:
                found.append({"key": key, "yt_id": y, "views": float(row[col]), "base": base, "kind": kind, "mark": 24 if col == "v24" else 48})
                LAD.order_followup(key, y, float(row[col]), base, 24 if col == "v24" else 48, now)
            continue
        if col != "v48": continue
        hist = [float(r["v48"]) for r in st.rows("Monitor48") if r.get("kind") == kind and r.get("v48") not in (None, "") and r.get("yt_id") != y]
        base = statistics.median(hist) if len(hist) >= S("BREAKOUT_MIN_HISTORY", int) else None
        v = float(row[col])
        hit = (v >= S("BREAKOUT_MULT", float) * base) if base else (v >= S("BREAKOUT_MIN_VIEWS", float))
        if hit:
            found.append({"key": key, "yt_id": y, "views": v, "base": base, "kind": kind})
            _breakout_card(key, y, v, base, kind)
    return found

def _breakout_card(key, y, v, base, kind):
    from whatifs import notify as NT
    rel = f"{v / base:.1f}x the usual {int(base)}" if base else f"{int(v)} views in 48 h (no history yet)"
    from whatifs import ladder as LAD
    sequel = "the best of them can earn the sequel as a long video" if LAD.on() else "a sequel premise for the next long slot"
    NT.send("breakout", f"BREAKOUT: your {kind} {key} is at {rel}. Strike while it's hot: 2 follow-up Shorts on its topic; {sequel} "
            f"(paid from the breakout fund / reserve). https://youtu.be/{y}",
            [("Approve follow-ups", f"BREAKOUT GO {key}"), ("Not this one", f"BREAKOUT NO {key}")],
            tier="now", urgent=True, default="not approved", expires_h=36, dedupe_key=f"breakout|{y}")

def _answer(row, choice):
    p = str(choice).split()
    if len(p) >= 3 and p[0].upper() == "BREAKOUT" and p[1].upper() == "GO":
        st = store(); key = p[2]
        st.append("Breakout_Queue", [{"ts": iso(), "video_key": key, "status": "APPROVED", "plan": "2 follow-up Shorts + sequel premise", "left": 2}])
        src = next((e for e in st.rows("Episodes") if e.get("episode_id") == key), None) or next((s for s in st.rows("Specials") if s.get("id") == key), {}) or {}
        base = src.get("premise") or src.get("title") or key
        from whatifs import ladder as LAD
        if LAD.on(): return "approved: 2 follow-up Shorts are queued (breakout fund first); the best of them can earn the sequel as a long video"      # v12 V2c-b: every topic starts as a Short
        try:                                                   # the sequel premise goes to the top of the bench for the next long slot
            st.append("Premise_Bench", [{"bench_id": f"BRK{key}", "premise": f"Sequel to a breakout: {base} - the follow-up question viewers asked",
                                         "status": "READY", "combined": 99, "source": "breakout"}])
        except Exception as e: log(f"sequel premise not added: {scrub(e)}", "WARN")
        return "approved: 2 follow-up Shorts are queued (breakout fund first) and a sequel premise is first on the bench"
    if len(p) >= 3 and p[1].upper() == "NO":
        st = store()
        if any(q.get("video_key") == p[2] and q.get("status") in ("ORDERED", "OVERDUE") for q in st.rows("Breakout_Queue")):          # v12 V2c-b: "Stop it" on a follow-up ordered by code
            st.update("Breakout_Queue", "video_key", p[2], {"status": "DECLINED"}); return "stopped: no follow-up is made"
        st.append("Breakout_Queue", [{"ts": iso(), "video_key": p[2], "status": "DECLINED", "plan": ""}]); return "noted: no follow-ups"
    return "recorded"

def register():
    from whatifs import notify as NT
    NT.register("breakout", on_answer=_answer)
