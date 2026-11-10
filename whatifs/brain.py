"""Channel Brain, the learning core: video features, engaged-view outcomes, Technique_Evidence (Beta-binomial), Thompson sampling with a holdout, forecasts and the weekly 'what we learned'. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, json, re
import numpy as np
from whatifs.core import S, log, store, iso, now_utc, parse_iso

HOOK_ARCHETYPES = {
    "verdict_first":  "state the verdict or the absurd consequence in the first second, then show why",
    "impossible_number": "open on one impossible-sounding number, then prove it",
    "object_on_trial": "put an everyday object on trial ('The Moon is charged with...')",
    "countdown":      "a ticking clock: 'In 8 minutes, the sky goes dark'",
    "you_pov":        "drop the viewer into the situation in second person, in the first frame",
}
FAMILIES = ("hook", "title", "topic", "length", "lead", "origin")
TOPICS = {"space": r"moon|sun|planet|star|galax|black hole|mars|jupiter|orbit|asteroid|comet|space",
          "earth": r"ocean|earth|volcano|weather|ice|climate|tide|earthquake|forest",
          "body":  r"body|brain|sleep|blood|heart|eat|human|skin|bone|dna",
          "physics": r"gravity|light|speed|time|atom|energy|magnet|sound|heat|cold",
          "life":  r"animal|insect|bacteria|dinosaur|plant|bird|fish|cat|dog",
          "everyday": r"phone|internet|money|city|car|coffee|chair|pillow|food"}

def _rows(tab):
    try: return store().rows(tab)
    except Exception: return []

def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

# ------------------------------------------------------------------ features
def title_pattern(title):
    t = str(title or "").strip()
    if t.endswith("?"): return "question"
    if re.search(r"\d", t): return "number"
    if re.search(r"(?i)\b(guilty|verdict|trial|court|charged)\b", t): return "verdict"
    return "statement"

def topic_cluster(text):
    low = str(text or "").lower()
    for k, rx in TOPICS.items():
        if re.search(rx, low): return k
    return "other"

def length_band(sec, fmt):
    s = _f(sec)
    if fmt == "short": return "short_20_35" if s <= 35 else ("short_36_50" if s <= 50 else "short_51_60")
    return "long_lt9" if s < 540 else ("long_9_11" if s <= 660 else "long_gt11")

def tag(video_key, fmt, title="", premise="", hook="", sec=0, lead="", origin="ai", arm=None, holdout=False, yt_id=""):
    """Record one video's features (once per video_key). fmt = 'short' | 'long'."""
    st = store()
    if any(r.get("video_key") == video_key for r in st.rows("Video_Features")): return False
    st.append("Video_Features", [{"ts": iso(), "video_key": video_key, "yt_id": yt_id, "format": fmt, "hook": hook or "unknown", "title": title_pattern(title),
                                  "topic": topic_cluster(premise or title), "length": length_band(sec, fmt), "lead": (lead or "ensemble").upper(),
                                  "origin": origin, "arm": json.dumps(arm or {}), "holdout": "TRUE" if holdout else "", "title_text": str(title)[:120]}])
    return True

def link_yt(video_key, yt_id):
    st = store()
    if any(r.get("video_key") == video_key for r in st.rows("Video_Features")): st.update("Video_Features", "video_key", video_key, {"yt_id": yt_id})

# ------------------------------------------------------------------ outcomes (YouTube Analytics only)
def outcomes():
    """{yt_id: {'views', 'engaged', 'avp'}} from the newest Analytics pull per video (rows with engaged views only)."""
    out = {}
    for r in _rows("Analytics"):
        y = r.get("yt_id")
        if not y or r.get("engaged_views") in (None, ""): continue
        out[y] = {"views": _f(r.get("views")), "engaged": _f(r.get("engaged_views")), "avp": _f(r.get("avg_view_pct"), None)}
    return out

def _obs(fmt):
    """Joined rows: features + outcomes, for one format."""
    oc = outcomes(); rows = []
    for f in _rows("Video_Features"):
        if f.get("format") != fmt or f.get("yt_id") not in oc: continue
        o = oc[f["yt_id"]]
        if o["views"] <= 0: continue
        rows.append(dict(f, **o))
    return rows

# ------------------------------------------------------------------ the library (Beta-binomial, pooled, against the channel baseline)
def _p_beats(a1, b1, a0, b0, n=4000, seed=7):
    rng = np.random.default_rng(seed)
    return float(np.mean(rng.beta(a1, b1, n) > rng.beta(a0, b0, n)))

def update_library(now=None, fmt="short"):
    """Recompute every feature level's evidence; promote / demote / retire by the rules. Returns {technique_id: status}."""
    now = now or now_utc(); rows = _obs(fmt); st = store()
    if not rows: return {}
    S_ = sum(min(r["engaged"], r["views"]) for r in rows); N_ = sum(r["views"] for r in rows)
    k = S("BRAIN_PRIOR_STRENGTH", float)
    base_rate = S_ / N_ if N_ else 0.5
    a0, b0 = 1 + S_, 1 + (N_ - S_)
    lib = {r.get("technique_id"): r for r in st.rows("Technique_Evidence")}
    result = {}
    for fam in FAMILIES:
        levels = {}
        for r in rows: levels.setdefault(str(r.get(fam) or "unknown"), []).append(r)
        for lvl, rs in levels.items():
            if lvl in ("unknown", ""): continue
            tid = f"{fmt}:{fam}:{lvl}"
            s = sum(min(r["engaged"], r["views"]) for r in rs); n = sum(r["views"] for r in rs)
            a1, b1 = 1 + k * base_rate + s, 1 + k * (1 - base_rate) + (n - s)       # empirical-Bayes prior centred on the channel rate
            p = _p_beats(a1, b1, a0, b0)
            eff = (a1 / (a1 + b1)) - base_rate
            old = lib.get(tid, {})
            status = old.get("status") or "testing"
            if p >= S("BRAIN_PROVEN_P", float) and len(rs) >= S("BRAIN_MIN_VIDEOS", int) and n >= S("BRAIN_MIN_TRIALS", int): status = "proven"
            elif p >= S("BRAIN_PROMISING_P", float): status = "promising" if status != "proven" else "proven"
            elif p <= S("BRAIN_RETIRE_P", float) and len(rs) >= S("BRAIN_MIN_VIDEOS", int): status = "retired"
            elif status == "proven" and p < S("BRAIN_DEMOTE_P", float): status = "testing"
            last_ok = old.get("last_validated") if status not in ("proven", "promising") else iso(now)
            exp = old.get("expires_at") or ""
            if status in ("proven", "promising"): exp = (now + dt.timedelta(days=S("BRAIN_RULE_DAYS", int))).strftime("%Y-%m-%dT%H:%M:%SZ")
            elif exp and parse_iso(exp) and parse_iso(exp) < now and old.get("status") in ("proven", "promising"): status = "retired"
            row = {"technique_id": tid, "format": fmt, "family": fam, "level": lvl, "alpha": round(a1, 2), "beta": round(b1, 2), "trials": int(n),
                   "successes": int(s), "n_videos": len(rs), "p_beats_baseline": round(p, 3), "effect_pp": round(100 * eff, 2), "baseline_rate": round(base_rate, 4),
                   "status": status, "last_validated": last_ok or "", "expires_at": exp, "updated": iso(now),
                   "mechanism": HOOK_ARCHETYPES.get(lvl, old.get("mechanism", "")) if fam == "hook" else old.get("mechanism", ""),
                   "kill_condition": f"P(beats baseline) <= {S('BRAIN_RETIRE_P', float)} over >= {S('BRAIN_MIN_VIDEOS', int)} videos, or no re-confirmation in {S('BRAIN_RULE_DAYS', int)} days",
                   "source_type": old.get("source_type") or "own_data"}
            if tid in lib: st.update("Technique_Evidence", "technique_id", tid, row)
            else: st.append("Technique_Evidence", [row])
            if old.get("status") and old.get("status") != status:
                st.append("Brain_Log", [{"ts": iso(now), "event": "status", "technique_id": tid, "from": old.get("status"), "to": status, "evidence": f"P={p:.2f}, {len(rs)} videos, {int(n)} views, effect {100 * eff:+.1f} pp"}])
            result[tid] = status
    return result

# ------------------------------------------------------------------ choices: Thompson sampling with a holdout
def choose(family="hook", fmt="short", options=None, seed=None):
    """Pick a level for the next video. Returns {'level', 'holdout', 'p_draws'}. Retired levels are never picked; BRAIN_HOLDOUT keep the default."""
    rng = np.random.default_rng(seed)
    options = list(options or (HOOK_ARCHETYPES if family == "hook" else []))
    if not options: return {"level": None, "holdout": False}
    default = S("BRAIN_DEFAULT_HOOK") if family == "hook" else options[0]
    if rng.random() < S("BRAIN_HOLDOUT", float): return {"level": default, "holdout": True, "p_draws": {}}
    lib = {r.get("technique_id"): r for r in _rows("Technique_Evidence")}
    draws = {}
    for o in options:
        r = lib.get(f"{fmt}:{family}:{o}")
        if r and r.get("status") == "retired": continue
        a, b = (_f(r.get("alpha"), 1), _f(r.get("beta"), 1)) if r else (1.0 + S("BRAIN_PRIOR_STRENGTH", float) * 0.5, 1.0 + S("BRAIN_PRIOR_STRENGTH", float) * 0.5)
        draws[o] = float(rng.beta(a, b))
    if not draws: return {"level": default, "holdout": False, "p_draws": {}}
    best = max(draws, key=draws.get)
    return {"level": best, "holdout": False, "p_draws": {k: round(v, 3) for k, v in draws.items()}}

# ------------------------------------------------------------------ forecasts and their calibration
def forecast(video_key, fmt, hook=None, now=None):
    """80% interval for the engaged rate of the next video (pooled posterior of its hook level, else the channel). Logged in Forecasts."""
    lib = {r.get("technique_id"): r for r in _rows("Technique_Evidence")}
    r = lib.get(f"{fmt}:hook:{hook}") if hook else None
    rows = _obs(fmt)
    if r: a, b = _f(r.get("alpha"), 1), _f(r.get("beta"), 1); basis = f"{fmt}:hook:{hook}"
    elif rows:
        s = sum(min(x["engaged"], x["views"]) for x in rows); n = sum(x["views"] for x in rows)
        a, b = 1 + s / max(1, len(rows)), 1 + (n - s) / max(1, len(rows)); basis = "channel pooled"     # per-video scale: honest width
    else: a, b = 2.0, 2.0; basis = "no data yet (wide prior)"
    q = np.random.default_rng(11).beta(a, b, 6000)
    lo, mid, hi = (float(np.quantile(q, x)) for x in (0.1, 0.5, 0.9))
    naive = None
    if rows:
        rates = sorted(min(x["engaged"], x["views"]) / x["views"] for x in rows); naive = rates[len(rates) // 2]
    store().append("Forecasts", [{"ts": iso(now or now_utc()), "video_key": video_key, "format": fmt, "metric": "engaged_rate", "lo": round(lo, 4),
                                  "mid": round(mid, 4), "hi": round(hi, 4), "naive": "" if naive is None else round(naive, 4), "basis": basis,
                                  "actual": "", "scored": ""}])
    return {"lo": lo, "mid": mid, "hi": hi, "naive": naive, "basis": basis}

def score_forecasts():
    """Fill actuals; return {'n', 'coverage', 'mae', 'mae_naive', 'beats_naive'} over scored forecasts."""
    st = store(); feats = {r.get("video_key"): r.get("yt_id") for r in _rows("Video_Features")}; oc = outcomes()
    for f in st.rows("Forecasts"):
        if f.get("scored"): continue
        y = feats.get(f.get("video_key"))
        if y in oc and oc[y]["views"] >= S("BRAIN_SCORE_MIN_VIEWS", int):
            act = min(oc[y]["engaged"], oc[y]["views"]) / oc[y]["views"]
            st.update("Forecasts", "video_key", f["video_key"], {"actual": round(act, 4), "scored": iso()})
    sc = [f for f in st.rows("Forecasts") if f.get("scored")]
    if not sc: return {"n": 0}
    cov = np.mean([_f(f["lo"]) <= _f(f["actual"]) <= _f(f["hi"]) for f in sc])
    mae = np.mean([abs(_f(f["mid"]) - _f(f["actual"])) for f in sc])
    nv = [abs(_f(f["naive"]) - _f(f["actual"])) for f in sc if f.get("naive") not in ("", None)]
    mae_n = float(np.mean(nv)) if nv else None
    return {"n": len(sc), "coverage": round(float(cov), 3), "mae": round(float(mae), 4), "mae_naive": None if mae_n is None else round(mae_n, 4),
            "beats_naive": (mae_n is not None and mae < mae_n)}

# ------------------------------------------------------------------ the honest verdicts (for the weekly report and the dashboard)
def verdicts():
    lib = _rows("Technique_Evidence")
    def pick(st_): return sorted([r for r in lib if r.get("status") == st_], key=lambda r: -_f(r.get("p_beats_baseline")))
    hold = [r for r in _rows("Video_Features") if r.get("holdout") == "TRUE"]
    return {"proven": pick("proven"), "promising": pick("promising"), "retired": pick("retired"), "testing": pick("testing"),
            "forecasts": score_forecasts(), "holdout_videos": len(hold),
            "learning": ("NOT LEARNING YET: forecasts do not beat the channel median" if (score_forecasts().get("n", 0) >= 8 and not score_forecasts().get("beats_naive"))
                         else "too few measured videos to judge" if score_forecasts().get("n", 0) < 8 else "learning: forecasts beat the median")}

# ------------------------------------------------------------------ Shorts outcomes (every Short, not only long videos)
def _short_ids():
    """(video_key, yt_id, published_iso, title, premise) for every Short the channel posted: reels cut from episodes, specials, pilots."""
    out = []
    for e in _rows("Episodes"):
        for k in range(1, 5):
            y = e.get(f"reel{k}_yt")
            if y: out.append((f"{e.get('episode_id')}#r{k}", y, e.get("slot_et"), e.get("title", ""), e.get("premise", "")))
    for s in _rows("Specials"):
        if s.get("yt_id"): out.append((s.get("id"), s.get("yt_id"), s.get("ts"), s.get("title", ""), s.get("format", "")))
    for p in _rows("Pilots"):
        if p.get("yt_id"): out.append((p.get("id"), p.get("yt_id"), p.get("ts"), p.get("hook", ""), p.get("premise", "")))
    return out

def _short_metrics(yt_id, since):
    from whatifs.core import FAKE
    if FAKE:
        import random
        r = random.Random(yt_id); v = r.randint(40, 4000); return {"views": v, "engaged_views": int(v * r.uniform(0.35, 0.85)), "avg_view_pct": r.uniform(55, 110)}
    import requests
    from whatifs.publish import gheaders
    p = {"ids": "channel==MINE", "startDate": since[:10], "endDate": now_utc().strftime("%Y-%m-%d"), "filters": f"video=={yt_id}",
         "metrics": "views,engagedViews,averageViewPercentage"}
    a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=p, timeout=30).json()
    if a.get("error") or not a.get("rows"): return None
    r = a["rows"][0]; return {"views": r[0], "engaged_views": r[1], "avg_view_pct": r[2]}

def ingest_shorts(now=None):
    """Pull each Short once it is BRAIN_SHORT_AGE_H old (and refresh weekly for 28 days); tag Shorts that have no features yet."""
    now = now or now_utc(); st = store(); n = 0
    have = {r.get("yt_id"): r for r in st.rows("Analytics")}
    tagged = {r.get("video_key") for r in st.rows("Video_Features")}
    for key, y, pub, title, prem in _short_ids():
        t = parse_iso(pub)
        if not t or (now - t).total_seconds() < S("BRAIN_SHORT_AGE_H", float) * 3600: continue
        if key not in tagged: tag(key, "short", title=title, premise=prem, yt_id=y, origin="ai"); tagged.add(key)
        else: link_yt(key, y)
        old = have.get(y)
        if old and old.get("engaged_views") not in (None, "") and (parse_iso(old.get("pulled")) or now) > now - dt.timedelta(days=7): continue
        if old and (now - t).days > 28: continue
        try: m = _short_metrics(y, t.strftime("%Y-%m-%d"))
        except Exception as e: log(f"Short analytics failed for {y}: {str(e)[:100]}", "WARN"); m = None
        if not m: continue
        row = {"episode_id": key, "yt_id": y, "pulled": iso(now), **m, "data_note": "ok (short)"}
        if old: st.update("Analytics", "yt_id", y, row)
        else: st.append("Analytics", [row])
        n += 1
    return n

def daily(now=None):
    """The learning job's brain step: ingest, update both libraries, score forecasts. Never raises."""
    if not S("BRAIN_ON", bool): return {}
    out = {}
    for name, fn in (("shorts_ingested", lambda: ingest_shorts(now)), ("short_lib", lambda: update_library(now, "short")),
                     ("long_lib", lambda: update_library(now, "long")), ("forecasts", score_forecasts)):
        try: out[name] = fn()
        except Exception as e: log(f"brain step {name} failed: {str(e)[:120]}", "WARN"); out[name] = None
    return out
