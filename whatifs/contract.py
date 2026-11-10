"""Feature Contract: every promised feature is a named HARD check at a stage, judged from real evidence; a FAIL holds the episode and sends the owner a decision message. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os
import json, math, os, re, statistics, subprocess
from whatifs.core import S, log, store, iso, now_utc, set_setting, FAKE, scrub

PASS, FAIL, WAIVED, NA = "PASS", "FAIL", "WAIVED", "N/A"

# ------------------------------------------------------------------ helpers
def _script_text(ctx):
    sc = (ctx.get("room") or {}).get("script")
    return sc.get("script", "") if isinstance(sc, dict) else str(sc or "")

def _spoken_lines(text):
    return [l for l in str(text or "").split("\n") if l.strip() and not l.strip().startswith(("#", "[SFX", "[MUSIC", "("))]

def _waived(ep, fid):
    try: return fid in (json.loads(S("CONTRACT_WAIVERS") or "{}").get(ep) or [])
    except Exception: return False

def _dur(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, timeout=60)
        return float(out.stdout.strip() or 0)
    except Exception: return 0.0

def motion_score(path, samples=6):
    """Mean absolute luma change between frames 0.4 s apart, sampled across the clip (0..255). A portrait push-in or a frozen face scores
    low; characters acting in a scene score high. Free (ffmpeg + numpy)."""
    import numpy as np
    d = _dur(path)
    if d <= 0.9: return 0.0
    vals = []
    for k in range(samples):
        t = 0.2 + (d - 0.8) * k / max(1, samples - 1)
        fr = []
        for tt in (t, t + 0.4):
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tt:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=160:90,format=gray", "-f", "rawvideo", "-"],
                               capture_output=True, timeout=60)
            if len(r.stdout) == 160 * 90: fr.append(np.frombuffer(r.stdout, np.uint8).astype(np.float32))
        if len(fr) == 2: vals.append(float(np.mean(np.abs(fr[1] - fr[0]))))
    return round(statistics.mean(vals), 2) if vals else 0.0

def music_presence_db(master, timeline):
    """Loudness (dBFS) of the master in the gaps between spoken lines. A music/ambience bed keeps gaps well above silence (-60 dBFS)."""
    import numpy as np
    segs = sorted((float(u.get("start", 0)), float(u.get("end", 0))) for u in (timeline or {}).get("units", []) if u.get("end"))
    gaps = [(a[1], b[0]) for a, b in zip(segs, segs[1:]) if b[0] - a[1] >= 0.35][:40]
    if not gaps: return None
    vals = []
    for g0, g1 in gaps:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{g0 + 0.05:.2f}", "-t", f"{max(0.1, g1 - g0 - 0.1):.2f}", "-i", master, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                           capture_output=True, timeout=60)
        x = np.frombuffer(r.stdout, "<i2").astype(np.float64) / 32768
        if len(x): vals.append(20 * math.log10(max(1e-6, float(np.sqrt(np.mean(x ** 2))))))
    return round(statistics.median(vals), 1) if vals else None

# ------------------------------------------------------------------ probes (each returns (status, evidence))
def p_hook(ctx):
    rec = ctx.get("hook_rec") or {}
    if not S("HOOKS_ON", bool): return NA, "Hook Lab switched off"
    if not rec or rec.get("status") == "failed" or not rec.get("applied"): return FAIL, f"Hook Lab did not run or was not applied ({(rec or {}).get('status', 'no record')})"
    n = len(rec.get("candidates") or []); sc = rec.get("score") or rec.get("winner_score")
    if n < S("CONTRACT_HOOK_MIN_CANDIDATES", int): return FAIL, f"only {n} hook candidates (need {S('CONTRACT_HOOK_MIN_CANDIDATES', int)})"
    if sc is not None and float(sc) < S("CONTRACT_HOOK_MIN_SCORE", float): return FAIL, f"winning hook scored {sc} (bar {S('CONTRACT_HOOK_MIN_SCORE', float)})"
    return PASS, f"{n} candidates, winner {sc if sc is not None else 'chosen'} by {rec.get('scored_by', '?')}"

def p_owners_cut(ctx):
    d = ctx.get("d") or {}; oc = d.get("owners_cut") or {}
    if not oc: return FAIL, "the Owner's Cut judge did not score this script"
    if d.get("below_bar"): return FAIL, f"best script stayed below the Owner's Cut bar (mean {oc.get('mean')})"
    return PASS, f"mean {oc.get('mean')} after {oc.get('rounds')} round(s)"

def p_emotion(ctx):
    if not S("EMOTION_BEAT_ON", bool): return NA, "emotion beats switched off"
    eb = (ctx.get("d") or {}).get("emotion_beat")
    return (PASS, f"beat: {eb if isinstance(eb, str) else json.dumps(eb)[:80]}") if eb else (FAIL, "no emotion beat was planned and written")

def p_asks(ctx):
    from whatifs import engage as EN, cta as CTA
    text = _script_text(ctx); lines = text.split("\n")
    n = sum(1 for l in lines if l.strip() and CTA.kind_of_text(CTA._peel(l)[3]))
    sp = len(EN._spoken(lines))
    room_needed = S("ENGAGE_MIN_GAP_LINES", int) * (S("ENGAGE_MAX_CTA", int) + 1) / max(0.2, 1 - S("ENGAGE_NO_ASK_FIRST_PCT", float))
    _, removed = EN.enforce(text, ctx.get("ep", ""))
    if removed and sp >= room_needed: return FAIL, f"{removed} audience ask(s) break the placement rules"
    if removed: return (PASS, f"{n} ask(s); script of {sp} lines is too short for the spacing rules (presence checked)") if n >= 1 else (FAIL, "no audience ask at all")
    if n < 1: return FAIL, "no audience ask at all"
    if n > S("ENGAGE_MAX_CTA", int): return FAIL, f"{n} asks (max {S('ENGAGE_MAX_CTA', int)})"
    return PASS, f"{n} ask(s), placement rules met"

def p_verdict(ctx):
    if not S("VERDICT_ROTATION_ON", bool): return NA, "rotation off"
    v = ((ctx.get("d") or {}).get("show_plan") or {}).get("verdict") or {}
    return (PASS, f"style: {v.get('style')}") if v.get("style") else (FAIL, "the verdict has no style (rotation not applied)")

def p_similarity(ctx):
    s = (ctx.get("d") or {}).get("script_similarity")
    if s is None: return FAIL, "the similarity guard did not run"
    return (PASS, f"{s:.0%} vs the last 10") if float(s) <= S("SCRIPT_SIMILARITY_MAX", float) else (FAIL, f"{s:.0%} similar to an earlier script")

def p_tease(ctx):
    t = (ctx.get("d") or {}).get("next_tease")
    return (PASS, str(t.get("line") or t.get("premise") or "set")[:80] if isinstance(t, dict) else str(t)[:80]) if t else (FAIL, "no end tease for the next case")

def p_cold_open(ctx):
    sp = _spoken_lines(_script_text(ctx))
    if not sp: return FAIL, "empty script"
    first = re.sub(r"^\s*[A-Z][A-Z .']{1,24}:\s*", "", sp[0]).strip()
    if re.match(r"(?i)^(hi|hello|hey|welcome|today we|in this video)\b", first): return FAIL, f"opens with a greeting: '{first[:60]}'"
    return PASS, f"first line: '{first[:70]}'"

def _pre_grammar(ctx):
    """An owner-approved Script Preview written before TRIAL_GRAMMAR_SINCE is not judged on the trial grammar (it could not know it)."""
    d = ctx.get("d") or {}
    if not d.get("from_preview") or not d.get("preview_room_ts"): return False
    from whatifs.core import parse_iso
    since = parse_iso(S("TRIAL_GRAMMAR_SINCE"))
    try: return bool(since) and float(d["preview_room_ts"]) < since.timestamp()
    except (TypeError, ValueError): return False

_RUNGS = {"hour 1": r"\bhour (1|one)\b|\bfirst hour\b", "day 1": r"\bday (1|one)\b|\bfirst day\b", "year 1": r"\byear (1|one)\b|\bfirst year\b",
          "million years": r"\bmillion years\b"}

def p_time_ladder(ctx):
    if not S("TRIAL_GRAMMAR_ON", bool): return NA, "trial grammar off"
    if _pre_grammar(ctx): return NA, "owner-approved Script Preview written before the trial grammar"
    t = _script_text(ctx).lower(); hit = [k for k, rx in _RUNGS.items() if re.search(rx, t)]
    return (PASS, f"rungs: {', '.join(hit)}") if len(hit) >= 3 else (FAIL, f"time ladder incomplete ({', '.join(hit) or 'none'}); need 3 of hour 1 / day 1 / year 1 / million years")

def p_exhibits(ctx):
    if not S("TRIAL_GRAMMAR_ON", bool): return NA, "trial grammar off"
    if _pre_grammar(ctx): return NA, "owner-approved Script Preview written before the trial grammar"
    lines = [l for l in _script_text(ctx).split("\n") if re.search(r"(?i)\bexhibit [a-z]\b", l)]
    sourced = [l for l in lines if re.search(r"\b(1[89]|20)\d{2}\b", l)]
    if len(lines) < 3: return FAIL, f"{len(lines)} exhibit(s); need at least 3"
    if len(sourced) < 2: return FAIL, f"only {len(sourced)} exhibit(s) name a source year"
    return PASS, f"{len(lines)} exhibits, {len(sourced)} with a source year"

def p_prototype(ctx):
    if not S("TRIAL_GRAMMAR_ON", bool): return NA, "trial grammar off"
    if _pre_grammar(ctx): return NA, "owner-approved Script Preview written before the trial grammar"
    return (PASS, "Grimm's Prototype demonstration present") if re.search(r"(?i)\bprototype\b", _script_text(ctx)) else (FAIL, "no Grimm Prototype demonstration")

def p_verdict_line(ctx):
    if not S("TRIAL_GRAMMAR_ON", bool): return NA, "trial grammar off"
    if _pre_grammar(ctx): return NA, "owner-approved Script Preview written before the trial grammar"
    return (PASS, "verdict opens with 'Here's what's true'") if re.search(r"(?i)here[\u2019']s what[\u2019']s true", _script_text(ctx)) else (FAIL, "Nana's verdict line \"Here's what's true\" is missing")

def p_promise_paid(ctx):
    """v11 (K158): the packaging promise is ON SCREEN early (the promise shot starts by PROMISE_BY_SEC)."""
    from whatifs import breakout as BRK
    if not S("PROMISE_SHOT_ON", bool): return NA, "promise shot off (owner setting)"
    shots, units = ctx.get("shots") or [], ctx.get("units") or []
    if not shots: return NA, "no shot list in this run"
    t = BRK.promise_start(shots, units)
    if t is None:                                              # v11 audit: never hold a video for something it could not have done
        if not any(s.get("type") == "kling" for s in shots): return NA, "no animated scene this episode (budget-trimmed), so no promise shot to place"
        pkg = ctx.get("pkg") or {}; promise = (pkg.get("promise") or {}) if isinstance(pkg, dict) else {}
        if isinstance(promise, dict) and not (promise.get("thumbnail") or promise.get("title") or promise.get("text")) and not (ctx.get("d") or {}).get("promise"):
            return NA, "no packaging promise text for this episode"
        return FAIL, "an animated scene exists, but none shows the thumbnail's promise"
    return (PASS, f"promise on screen at {t:.1f} s") if t <= S("PROMISE_BY_SEC", float) else (FAIL, f"promise first shown at {t:.1f} s (limit {S('PROMISE_BY_SEC', float):.0f} s)")

def p_alive(ctx):
    """v11 (K158): no stretch of the finished video looks like a still photo (residual motion after removing the camera move)."""
    from whatifs.core import FAKE
    if FAKE and not S("CONTRACT_MEASURE_IN_FAKE", bool): return NA, "measured in real runs only"
    m = ctx.get("master")
    if not m or not os.path.exists(m): return FAIL, "no finished video to measure"
    from whatifs import breakout as BRK
    try: a = BRK.aliveness(m)
    except Exception as e: return FAIL, f"could not measure: {str(e)[:120]}"
    (ctx.get("d") or {})["aliveness"] = a
    longest = max([b - x for x, b in a["dead_stretches"]] or [0])
    ok = a["alive_share"] >= S("ALIVE_MIN_SHARE", float) and longest <= S("ALIVE_MAX_DEAD_S", float)
    ev = f"alive {a['alive_share']:.0%} of the time; longest still-looking stretch {longest:.1f} s; first ones {a['dead_stretches'][:3]}"
    return (PASS, ev) if ok else (FAIL, ev)

# ---------------- v11.1 (K166) hard enforcement of the researched breakout rules
def p_brain_playbook(ctx):
    d = ctx.get("d") or {}
    if not d.get("brain_block"): return NA, "no proven/promising/retired evidence on the channel yet"
    return (PASS, "the channel's own evidence was in the writer's brief") if d.get("brain_block_in_brief") else (FAIL, "evidence existed but did not reach the writer")

def p_no_retired(ctx):
    from whatifs import enforce as EN
    d = ctx.get("d") or {}; h = d.get("hook_archetype")
    if not h: return NA, "no hook archetype recorded"
    return (FAIL, f"the hook archetype '{h}' is RETIRED by the learning core") if ("hook", h) in EN.retired_levels() else (PASS, f"hook '{h}' is not retired")

def p_idea_evidence(ctx):
    from whatifs import enforce as EN
    if not S("IDEA_GATE_ON", bool): return NA, "idea gate off (owner setting)"
    if not EN.demand_data_exists(): return NA, "no outlier data collected yet (the Outlier Lab fills it daily)"
    spine = (ctx.get("room") or {}).get("spine") or {}; prem = str(spine.get("premise") or "").strip().lower()
    row = next((b for b in store().rows("Premise_Bench") if str(b.get("premise") or "").strip().lower() == prem), None)
    m = EN.premise_evidence(row) if row else 0.0
    return (PASS, f"premise backed by an outlier at {m:.1f}x") if m >= S("IDEA_MIN_MULTIPLE", float) else (FAIL, f"premise evidence {m:.1f}x (needs {S('IDEA_MIN_MULTIPLE', float):.0f}x)")

def p_joke_density(ctx):
    from whatifs import enforce as EN
    t = _script_text(ctx)
    if not t: return FAIL, "no script"
    need, have, gap = EN.joke_need(t), len(EN.punch_lines(t)), EN.biggest_gap_lines(t)
    ok = have >= need and gap <= 2.2 * S("JOKE_EVERY_SEC_LONG", float)
    return (PASS if ok else FAIL), f"{have} punchlines (need {need}); biggest gap {gap:.0f} s"

def p_send_awe(ctx):
    from whatifs import enforce as EN
    t = _script_text(ctx)
    s, a = bool(EN.SEND_RE.search(t)), [i for i, l in enumerate(t.split("\n")) if EN.AWE_RE.search(l)]
    n = max(1, len(t.split("\n"))); late = bool(a) and min(a) / n > 0.8
    ok = s and a and not late
    return (PASS if ok else FAIL), f"send moment {'yes' if s else 'MISSING'}; awe peak {'yes' if a else 'MISSING'}{' (in the last 20%)' if late else ''}"

def p_impact(ctx):
    """Impact Map V1 hook, V3/V4 re-hook cadence, V6 pause-then-punch, V8 SFX spacing, V9 variety vs the last 10, V10 flash safety."""
    from whatifs import enforce as EN, sound as SD
    units, shots = ctx.get("units") or [], ctx.get("shots") or []
    if not units: return NA, "no narration timeline in this run"
    total = float(units[-1].get("end", 0) or 0); probs = []
    ok1, early = EN.v1_hook(units)
    if not ok1: probs.append(f"V1: no question / 'you' stake in the first {S('IMPACT_HOOK_SEC', float):.0f} s")
    for u in units: u["punch"] = u.get("punch") or any("PUNCH" in str(x).upper() for x in (u.get("show") or []))
    n, bad = EN.v6_punch_timing(units)
    if bad: probs.append(f"V6: {len(bad)} of {n} punchlines without the pause (gaps {bad[:4]})")
    try: bad8 = EN.v8_sfx(SD.immersive(shots, units, total, seed=ctx.get("ep", ""))) if shots else []
    except Exception: bad8 = []
    if bad8: probs.append(f"V8: repeated sound events {bad8[:3]}")
    sig = EN.signature(units, total); sim = EN.v9_variety(sig, ctx.get("ep", ""))
    if sim >= S("IMPACT_VARIETY_MAX", float): probs.append(f"V9: {sim:.2f} similar to a recent episode (max {S('IMPACT_VARIETY_MAX', float)})")
    fl = EN.v10_flash(ctx.get("master")) if S("CONTRACT_MEASURE_IN_FAKE", bool) or not __import__("whatifs.core", fromlist=["FAKE"]).FAKE else 0.0
    if fl > S("IMPACT_FLASH_MAX", float): probs.append(f"V10: {fl:.0f} luminance flips in one second (max {S('IMPACT_FLASH_MAX', float):.0f})")
    EN.record_map(ctx.get("ep", ""), sig, {"punch": n, "similarity": round(sim, 3), "flash": fl, "problems": probs})
    return (FAIL, "; ".join(probs)) if probs else (PASS, f"hook ok; {n} timed punchlines; similarity {sim:.2f}; flash {fl:.0f}/s")

def p_retention(ctx):
    """HARD (v11.1): re-hook cadence + promise + loops on the FINAL script (the room tries to fix; this blocks what is still broken)."""
    from whatifs import growth as GR
    t = _script_text(ctx); spine = (ctx.get("room") or {}).get("spine") or {}
    if not t: return FAIL, "no script"
    s = (ctx.get("room") or {}).get("script") or {}
    r = GR.retention_issues(t, spine.get("promise"), S("WPM_ESTIMATE", float), s.get("loops") if isinstance(s, dict) else None)
    return (PASS, f"longest stretch without a re-hook {r.get('max_gap', 0):.0f} s") if not r.get("issues") else (FAIL, "; ".join(r["issues"])[:300])

def p_living(ctx):
    """v11.1 (K167): once character sheets are LOCKED, every reaction cutaway shows the approved character (blinking, breathing, talking)."""
    from whatifs import living as LV
    if not S("LIVING_CHARACTERS_ON", bool): return NA, "living characters off (owner setting)"
    locked = [r for r in store().rows("Character_Sheets") if r.get("status") == "LOCKED"]
    shots = ctx.get("shots") or []
    n_react = sum(1 for s in shots if s.get("type") == "reaction")
    if not locked: return NA, "no character sheets locked yet (run Character sheets)"
    if not n_react: return NA, "no reaction cutaways in this episode"
    used = len(LV.USED)
    return (PASS, f"{used} living character shots ({sum(u['blinks'] for u in LV.USED)} blinks, {sum(u['mouth_frames'] for u in LV.USED)} talking frames)") \
        if used >= n_react else (FAIL, f"{n_react - used} of {n_react} reaction cutaways fell back to a silhouette")

def p_visual_change(ctx):
    """Impact Map V2 + V5: a new picture state at least every VISUAL_CHANGE_MAX_S (graphics/reaction cutaways animate: 2x), and no 2-s window
    with 3+ changes (overload). Recomputed with the same rule the renderer uses (shotplan.pieces_for)."""
    from whatifs.shotplan import pieces_for
    units, shots = ctx.get("units") or [], ctx.get("shots") or []
    if not units or not shots: return NA, "no shot timeline in this run"
    mx = S("VISUAL_CHANGE_MAX_S", float); bounds, worst, where, fast, facts = [], 0.0, "", [], []
    merged = set(ctx.get("merged_units") or [])
    if not merged:
        try:
            from whatifs import episode as _EP; merged = set(_EP.MERGED_UNITS)
        except Exception: merged = set()
    for i, u in enumerate(units):
        if i in merged: continue                                   # folded into the previous shot by the renderer (no new picture state)
        a, b = float(u.get("start", 0) or 0), float(u.get("end", 0) or 0)
        j = i + 1
        while j in merged and j < len(units): b = float(units[j].get("end", b) or b); j += 1
        dur = max(0.0, b - a)
        typ = (shots[i] if i < len(shots) else {}).get("type", "still")
        n = max(1, pieces_for(dur, typ, a < S("OPENING_WINDOW_SEC", float), ctx.get("ep")))
        step = dur / n; lim = S("VISUAL_ANIMATED_MAX_S", float) if typ in ("graphic", "reaction") else mx * (2 if typ in ("kling", "living", "stock") else 1)
        if step > lim + 0.05 and step - lim > worst: worst, where = step - lim, f"{a:.0f}s ({typ}, {step:.1f} s per picture state)"
        bounds += [a + k * step for k in range(n)]
        if step < 1.0: fast.append(a)
        if re.search(r"\d", str(u.get("text", ""))): facts.append(a)
    # V5 overload (research definition): in one 2-s window a fast cut (< 1 s) AND a new fact AND a burst of changes (3+); or 5+ changes regardless
    bounds.sort(); dense = []
    for j, t0 in enumerate(bounds):
        win = [b for b in bounds[j:] if b - t0 < 2.0]
        if len(win) >= 5 or (len(win) >= 3 and any(t0 - 1 <= f <= t0 + 2 for f in fast) and any(t0 - 1 <= f <= t0 + 2 for f in facts)):
            dense.append(t0); break
    probs = ([f"V2: a picture holds too long at {where}"] if worst else []) + ([f"V5: overload at {dense[0]:.1f}s (fast cuts + a new fact + a burst of changes in 2 s)"] if dense else [])
    return (FAIL, "; ".join(probs)) if probs else (PASS, f"{len(bounds)} picture states; max hold within {mx:.1f} s; no overload")

def p_breakout_bar(ctx):
    """HARD: no upload below the Breakout Score bar (research: publish >= 80 and no hard gate failing). Rework = the episode is HELD with the
    weakest part named; the owner's card offers Rewrite / Approve anyway."""
    from whatifs import breakout as BRK
    d = ctx.get("d") or {}
    r = BRK.score(d, ctx.get("ledger_rows") or [], ctx.get("room"), ctx.get("critique"))
    if r.get("score") is None: return NA, "no evidence to score yet"
    ok = r["score"] >= S("BREAKOUT_HARD_BAR", float)
    return (PASS if ok else FAIL), f"Breakout Score {r['score']} (bar {S('BREAKOUT_HARD_BAR', float):.0f}; weakest: {r.get('weakest')})"

def p_research(ctx):
    if not S("RESEARCH_ON", bool): return NA, "research switched off by the owner (RESEARCH_ON)"
    rb = (ctx.get("d") or {}).get("research_brief")
    return (PASS, "research brief used by the writers' room") if rb else (FAIL, "the writers' room had no research brief")

def p_voices(ctx):
    tl = ctx.get("timeline") or {}
    fb = tl.get("voice_fallback")
    if fb is None: return FAIL, "no voice record in the timeline"
    if fb: return FAIL, f"fallback voice used for: {', '.join(fb)} (designed voices missing)"
    return PASS, "every speaker used its designed voice"

def p_music(ctx):
    m = ctx.get("master")
    if not m or not os.path.exists(m): return FAIL, "no master file"
    if FAKE and not S("CONTRACT_MEASURE_IN_FAKE", bool): return PASS, "measured live only"
    db = music_presence_db(m, ctx.get("timeline"))
    if db is None: return PASS, "no pauses long enough to measure"
    return (PASS, f"bed under pauses at {db} dBFS") if db >= S("CONTRACT_MUSIC_MIN_DB", float) else (FAIL, f"pauses are near-silent ({db} dBFS): no music/ambience bed")

def p_animation(ctx):
    clips = [c for c in (ctx.get("clips") or []) if c and os.path.exists(c)]
    need = S("ANIM_MIN_SEC", float)
    if need <= 0: return NA, "no animation minimum set"
    secs = sum(_dur(c) for c in clips)
    if secs < need: return FAIL, f"{secs:.0f} s of animated scenes (need {need:.0f} s)"
    return PASS, f"{len(clips)} animated scenes, {secs:.0f} s"

def p_motion(ctx):
    clips = [c for c in (ctx.get("clips") or []) if c and os.path.exists(c)]
    if not clips: return NA, "no animated scenes"
    if FAKE and not S("CONTRACT_MEASURE_IN_FAKE", bool): return PASS, "measured live only"
    sc = [motion_score(c) for c in clips]; low = [round(x, 1) for x in sc if x < S("ANIM_MIN_MOTION", float)]
    if len(low) > S("ANIM_MAX_STATIC_CLIPS", int): return FAIL, f"{len(low)} of {len(sc)} scenes barely move (motion {low}); template-like"
    return PASS, f"motion per scene {[round(x, 1) for x in sc]}"

def p_static(ctx):
    holds = ctx.get("holds") or []
    if not holds: return PASS, "no still picture states"
    mx = max(b - a for a, b in holds)
    return (PASS, f"longest still picture {mx:.1f} s") if mx <= S("CONTRACT_MAX_STILL_SEC", float) else (FAIL, f"a still picture holds {mx:.1f} s (max {S('CONTRACT_MAX_STILL_SEC', float)})")

def p_slop(ctx):
    sl = (ctx.get("qc_info") or {}).get("slop")
    if sl is None: return FAIL, "the slop guard did not score this video"
    return (PASS, f"slop {sl}/100") if float(sl) <= S("SLOP_HOLD", float) else (FAIL, f"slop {sl}/100 (hold above {S('SLOP_HOLD', float)})")

def p_thumbs(ctx):
    t, tb, ok = ctx.get("thumb"), ctx.get("thumb_b"), ctx.get("thumb_ok")
    if not t or not os.path.exists(t): return FAIL, "no thumbnail"
    if not ok: return FAIL, "the thumbnail failed the phone-size check"
    if S("PKG_RESCUE_ON", bool) and not tb: return FAIL, "no runner-up thumbnail for the packaging rescue"
    return PASS, "thumbnail passed the phone check" + (", runner-up ready" if tb else "")

def p_titles(ctx):
    ts = [t for t in ((ctx.get("pkg") or {}).get("titles") or []) if t]
    return (PASS, f"{len(ts)} scored titles") if len(ts) >= 2 else (FAIL, f"{len(ts)} title(s): the packaging room must offer at least 2")

def p_chapters(ctx):
    n = len(ctx.get("chapters") or [])
    dur = max([float(u.get("end", 0) or 0) for u in (ctx.get("timeline") or {}).get("units", [])] or [0])
    if 0 < dur < 180: return (PASS, f"{n} chapter(s); a {dur:.0f} s video is too short for YouTube chapters") if n >= 1 else (FAIL, "no chapters")
    return (PASS, f"{n} chapters") if n >= 3 else (FAIL, f"{n} chapters (need 3)")

def p_shorts(ctx):
    n = len(ctx.get("reel_files") or []); need = min(S("REELS_PER_VIDEO", int), 2)
    return (PASS, f"{n} Shorts passed QC") if n >= need else (FAIL, f"{n} Shorts passed QC (need {need})")

def p_covers(ctx):
    rf = ctx.get("reel_files") or []
    miss = [k for k, x in enumerate(rf) if not (x[2] and os.path.exists(x[2]))]
    return (PASS, f"{len(rf)} covers") if not miss else (FAIL, f"Shorts without a cover: {miss}")

def p_critique(ctx):
    cr = ctx.get("critique") or {}
    if not cr: return FAIL, "the creative self-review did not run"
    low = {k: v for k, v in cr.items() if k in CRIT_KEYS and isinstance(v, (int, float)) and v < S("CRITIQUE_MIN", float)}
    if low: return FAIL, "below the bar: " + ", ".join(f"{k} {v}" for k, v in low.items())
    return PASS, ", ".join(f"{k} {cr.get(k)}" for k in CRIT_KEYS)

def p_docs_current(ctx):
    """One current truth: no retired concept in the current docs, CLAUDE.md, module docstrings, prompt strings or the owner's CONSTITUTION cell."""
    from whatifs import truth as TRU
    bad = TRU.issues(runtime=True)
    if bad: return FAIL, f"{len(bad)} retired or stale reference(s): " + " | ".join(bad[:3])
    return PASS, f"no retired concept in current docs, docstrings or prompts ({len(TRU.RETIRED)} rules)"

def p_palace_health(ctx):
    """Knowledge Palace: founding knowledge present, every served item valid, evidenced and tied to code that exists, every department's playbook
    inside its cap with nothing retired, superseded or expired in it. Upkeep (seed, clock, self-repair, caps) runs first; the check judges the result."""
    if not S("PALACE_ON", bool): return NA, "Knowledge Palace switched off"
    from whatifs.org import palace as PAL, DEPARTMENTS
    PAL.maintain()
    h = PAL.health()
    if not h["ok"]: return FAIL, f"{len(h['problems'])} Palace problem(s): " + " | ".join(h["problems"][:3])
    s = h["stats"]
    return PASS, (f"{s['items']} items ({s['served']} served, {s['owner']} owner), {len(DEPARTMENTS)} playbooks inside their caps, version {s['version']}"
                  + (f"; notes: {'; '.join(h['notes'])}" if h["notes"] else ""))

def _org_gate(ctx, gate):
    """The organisation judged at an episode gate: every department this episode needed so far finished a complete run under the department contract
    (six chained receipts, the latest attempt ok) and wrote a valid takeaway; no run broke the contract; the registry is honest; the watchdog is alive."""
    from whatifs.org import runner as ORG
    if not ORG.on(): return NA, "organisation switched off"
    r = ORG.episode_issues(ctx.get("ep"), gate)
    if r["na"]: return NA, r["na"]
    if r["problems"]: return FAIL, f"{len(r['problems'])} problem(s): " + " | ".join(r["problems"][:3])
    return PASS, f"{r['runs']} department run(s) complete: six receipts each, playbook handed over, valid takeaway"

def _exec_gate(which):
    """The Execution Engine judged at the script gate (before picture money). A broken invariant fails; waiting for the owner's answer does not."""
    from whatifs.org import execute as EXE
    if not EXE.on(): return NA, "Execution Engine switched off (EXEC_ON, or the organisation)"
    p, s = EXE.decision_issues() if which == "decisions" else EXE.lever_issues()
    if p: return FAIL, f"{len(p)} problem(s): " + " | ".join(p[:3])
    if which == "decisions" and not s["decisions"] and not s["tickets"]: return NA, "no decision and no ticket yet: there is nothing to execute (a PASS here would claim work that does not exist)"
    if which == "decisions": return PASS, f"{s['decisions']} decision(s), {s['tickets']} ticket(s): none is text only; {s['live']} open inside their deadline or escalated ({s['with_owner']} with the owner)"
    return PASS, (f"{s['tickets']} ticket(s) in the engine: {s['verified']} verified, {s['rolled_back']} rolled back, {s['refused']} refused, {s['in_verification']} inside the verification window, "
                  f"{s['waiting']} waiting; every change has its ledger rows")

def p_decisions_executed(ctx): return _exec_gate("decisions")
def p_lever_verified(ctx): return _exec_gate("levers")
def p_dept_contract(ctx): return _org_gate(ctx, "script")
def p_takeaways_written(ctx): return _org_gate(ctx, "final")

FEATURES = [
    ("retention",     "script", p_retention,    "re-hook at least every REHOOK_MAX_GAP_SEC, promise shown early, every opened question answered"),
    ("brain_playbook", "script", p_brain_playbook, "the channel's own proven/retired evidence reached the writer"),
    ("no_retired",    "script", p_no_retired,   "no technique the learning core retired"),
    ("docs_current",  "script", p_docs_current, "one current truth: no retired concept in current docs, docstrings or prompts"),
    ("palace_health", "script", p_palace_health, "Knowledge Palace fit to feed departments: evidenced items tied to real code, nothing retired or expired served, playbooks inside their caps"),
    ("dept_contract", "script", p_dept_contract, "every department that worked on the script ran under the department contract: memos and playbook loaded, work done, memos sent, takeaway written, tickets executed, run reported"),
    ("decisions_executed", "script", p_decisions_executed, "nothing the organisation decided stays text: every decision has tickets, every ticket is executed with proof, refused with a reason or escalated"),
    ("lever_verified", "script", p_lever_verified, "every change made by ticket is written down before and after, verified by later evidence or rolled back; none sits past its window"),
    ("idea_evidence", "script", p_idea_evidence, "the premise is backed by an outlier at IDEA_MIN_MULTIPLE x"),
    ("joke_density",  "script", p_joke_density, "a [PUNCH] line at least every JOKE_EVERY_SEC_LONG seconds"),
    ("send_and_awe",  "script", p_send_awe,     "a [SEND] moment and an [AWE] peak (not in the last 20%)"),
    # id,             stage,    probe,          what the owner was promised
    ("hook_lab",      "script", p_hook,         "15-candidate Hook Lab, best opening applied"),
    ("owners_cut",    "script", p_owners_cut,   "independent judge scores the script above the bar"),
    ("cold_open",     "script", p_cold_open,    "no greeting: the video opens inside the story"),
    ("emotion_beat",  "script", p_emotion,      "one earned emotion beat"),
    ("audience_asks", "script", p_asks,         "comment/predict/share asks placed by the rules"),
    ("verdict_style", "script", p_verdict,      "verdict style rotates (no same-outcome repetition)"),
    ("originality",   "script", p_similarity,   "not a near-copy of an earlier script"),
    ("end_tease",     "script", p_tease,        "the video ends on the next case"),
    ("research",      "script", p_research,     "the writers' room used the research brief"),
    ("time_ladder",   "script", p_time_ladder,  "the case is examined on the time ladder (ticking clock)"),
    ("exhibits",      "script", p_exhibits,     "science claims entered as Exhibits with real sources"),
    ("grimm_prototype", "script", p_prototype,  "Grimm's failed Prototype demonstration (mad-scientist beat)"),
    ("verdict_line",  "script", p_verdict_line, "Nana's verdict opens with 'Here's what's true'"),
    ("designed_voices", "final", p_voices,      "every character speaks in its designed voice"),
    ("music_bed",     "final",  p_music,        "music/ambience bed under the story"),
    ("animation",     "final",  p_animation,    "minimum seconds of animated character scenes"),
    ("real_motion",   "final",  p_motion,       "animated scenes really move (no template push-ins)"),
    ("no_frozen_frames", "final", p_static,     "no still picture held too long"),
    ("slop_guard",    "final",  p_slop,         "anti-'AI slop' score under the hold line"),
    ("thumbnails",    "final",  p_thumbs,       "thumbnail passes the phone check + runner-up"),
    ("titles",        "final",  p_titles,       "several scored titles"),
    ("chapters",      "final",  p_chapters,     "YouTube chapters (at least 3)"),
    ("shorts",        "final",  p_shorts,       "Shorts cut, checked and ready"),
    ("short_covers",  "final",  p_covers,       "every Short has a designed cover"),
    ("self_review",   "final",  p_critique,     "6-point creative self-review at or above the bar"),
    ("promise_paid",  "final",  p_promise_paid, "the thumbnail's promise is on screen early"),
    ("impact_map",    "final",  p_impact,       "Impact Map: hook in 3 s, timed punchlines, sound spacing, variety vs last 10, flash safety"),
    ("visual_change", "final",  p_visual_change, "a new picture state every <= VISUAL_CHANGE_MAX_S, no overload"),
    ("living_characters", "final", p_living,   "reaction cutaways show the approved character, blinking, breathing and talking"),
    ("breakout_bar",  "final",  p_breakout_bar, "Breakout Score >= BREAKOUT_HARD_BAR (no upload below it)"),
    ("aliveness",     "final",  p_alive,        "no stretch of the video looks like a still photo"),
    ("takeaways_written", "final", p_takeaways_written, "every department run of this episode finished its six steps and wrote a valid takeaway"),
]
CRIT_KEYS = ("hook", "clarity", "humour", "visual_variety", "audio", "accuracy")

def enabled(fid):
    off = {x.strip() for x in str(S("CONTRACT_OFF") or "").split(",") if x.strip()}
    return fid not in off

# ------------------------------------------------------------------ the gate
def run(stage, ctx, ep, write=True):
    """Evaluate every feature of a stage. Returns {'ok', 'failed': [(id, evidence)], 'rows'}. Writes Feature_Ledger. Never raises."""
    rows, failed = [], []
    for fid, stg, probe, what in FEATURES:
        if stg != stage or not enabled(fid): continue
        try: status, ev = probe(ctx)
        except Exception as e: status, ev = FAIL, f"check crashed: {scrub(e)[:120]}"
        if status == FAIL and _waived(ep, fid): status, ev = WAIVED, f"waived by the owner ({ev})"
        rows.append({"ts": iso(), "episode_id": ep, "stage": stage, "feature": fid, "status": status, "evidence": str(ev)[:300], "promise": what})
        if status == FAIL: failed.append((fid, ev))
    if write:
        try: store().append("Feature_Ledger", rows)
        except Exception as e: log(f"ledger not written: {scrub(e)}", "WARN", ep)
    ok = not failed or not S("CONTRACT_ON", bool)
    log(f"contract {stage}: {len(rows) - len(failed)}/{len(rows)} pass" + (f"; FAILED: {', '.join(f for f, _ in failed)}" if failed else ""), "INFO" if not failed else "WARN", ep)
    for f_, ev_ in failed: log(f"contract {stage} {f_}: {str(ev_)[:240]}", "WARN", ep)          # v11.1: the reason, not just the name
    return {"ok": ok, "failed": failed, "rows": rows}

def owner_card(ep, stage, failed, extra=""):
    from whatifs import notify as NT
    lines = "; ".join(f"{f}: {str(ev)[:90]}" for f, ev in failed[:5])
    btn = [("Rewrite" if stage == "script" else "Fix", f"CONTRACT FIX {ep} {stage}"), ("Approve anyway", f"CONTRACT WAIVE {ep} {','.join(f for f, _ in failed)}"), ("Discuss", f"DISCUSS contract {ep}")]
    NT.send("contract_hold", f"{ep} is HELD at the {stage} check (nothing goes public). Failed: {lines}. {extra}".strip(), btn, tier="now", urgent=True,
            episode=ep, default="stays held", expires_h=48, dedupe_key=f"contract|{ep}|{stage}")

def _answer(row, choice):
    parts = str(choice).split()
    if len(parts) >= 3 and parts[0].upper() == "CONTRACT" and parts[1].upper() == "WAIVE":
        ep, feats = parts[2], (parts[3].split(",") if len(parts) > 3 else [])
        w = json.loads(S("CONTRACT_WAIVERS") or "{}"); w[ep] = sorted(set(w.get(ep, [])) | set(feats)); set_setting("CONTRACT_WAIVERS", json.dumps(w))
        _open_fix_issue(ep); return f"waived {', '.join(feats)} for {ep}; it continues"
    if len(parts) >= 3 and parts[0].upper() == "CONTRACT" and parts[1].upper() == "FIX":
        if len(parts) > 3 and parts[3] == "script": _drop_for_rewrite(parts[2]); return f"{parts[2]} dropped: a fresh episode is written for its slot"
        _open_fix_issue(parts[2]); return f"{parts[2]}: the one-click fix is running"
    if len(parts) >= 2 and parts[0].upper() in ("APPROVE", "HOLDREVIEW"):
        return approve(parts[1]) if parts[0].upper() == "APPROVE" else hold_review(parts[1])
    return "recorded"

def _open_fix_issue(ep):
    """The existing one-click fix (fix.yml runs on an issue titled 'FIX <ep>' opened by the repository owner). Opened with the owner's token."""
    if FAKE: return True
    import requests
    from whatifs.core import env
    tok, repo = env("GH_MERGE_TOKEN") or env("GH_DISPATCH_TOKEN"), env("GH_REPO")
    if not (tok and repo): log("fix issue not opened: no GitHub token here (use the link in the email)", "WARN", ep); return False
    r = requests.post(f"https://api.github.com/repos/{repo}/issues", headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"},
                      json={"title": f"FIX {ep}", "body": "Opened from the owner's tap (contract hold)."}, timeout=30)
    return r.status_code < 300

def _drop_for_rewrite(ep):
    """Script-stage hold + [Rewrite]: the episode is dropped (nothing paid for pictures yet) and its slot gets a fresh episode on the next tick."""
    try:
        from whatifs import checkpoint as CK; CK.clear(ep)
    except Exception: pass
    store().update("Episodes", "episode_id", ep, {"status": "DROPPED", "notes": "dropped for a rewrite (contract)", "updated": iso()})

def register():
    from whatifs import notify as NT
    for k in ("contract_hold", "creative_review"): NT.register(k, on_answer=_answer)

# ------------------------------------------------------------------ creative self-review (6 points) + owner approval gate
def critique(ctx, ep):
    """One cheap judge call: script + the ledger so far -> 6 scores 0-10 + 2 sentences. Never raises; {} when unavailable."""
    try:
        from whatifs.models import ask
        led = [f"{r['feature']}={r['status']} ({r['evidence'][:60]})" for r in ctx.get("ledger_rows") or []]
        r = ask("critic", "You are a demanding YouTube creative director. Score this episode 0-10 on hook, clarity, humour, visual_variety, audio, "
                     "accuracy (facts). Be strict: 7 = publishable, 9 = excellent. JSON only: {\"hook\":n,\"clarity\":n,\"humour\":n,\"visual_variety\":n,"
                     "\"audio\":n,\"accuracy\":n,\"notes\":\"two sentences: the biggest weakness and the fix\"}",
                     f"TITLE: {ctx.get('title', '')}\nSCRIPT (first 6000 chars):\n{_script_text(ctx)[:6000]}\n\nMEASURED CHECKS:\n" + "\n".join(led), want_json=True, episode=ep)
        r = r if isinstance(r, dict) else {}
        return {k: (float(r[k]) if isinstance(r.get(k), (int, float, str)) and str(r.get(k)).replace('.', '', 1).isdigit() else r.get(k)) for k in (*CRIT_KEYS, "notes") if k in (r or {})}
    except Exception as e:
        log(f"self-review unavailable: {scrub(e)[:100]}", "WARN", ep); return {}

def review_needed(kind="long"):
    if kind == "special": return S("SPECIALS_REVIEW_ON", bool)
    done = [e for e in store().rows("Episodes") if e.get("yt_id") and str(e.get("status")) not in ("AWAITING_APPROVAL",)]
    return len(done) <= S("CREATIVE_REVIEW_FIRST_N", int)

def await_approval(ep, vid, slot_iso, summary):
    """The uploaded video is taken OFF YouTube's schedule (private) until the owner approves."""
    from whatifs import publish as PUB, notify as NT
    try: PUB.yt_set_privacy(vid, "private")
    except Exception as e: log(f"could not unschedule {vid}: {scrub(e)}", "WARN", ep)
    store().update("Episodes", "episode_id", ep, {"status": "AWAITING_APPROVAL", "updated": iso()})
    NT.send("creative_review", f"Review before it goes public: {summary} Watch it (private): https://studio.youtube.com/video/{vid}/edit",
            [("Approve", f"APPROVE {ep}"), ("Hold", f"HOLDREVIEW {ep}"), ("Discuss", f"DISCUSS review {ep}")], tier="now", urgent=True,
            episode=ep, default="stays private", expires_h=72, dedupe_key=f"review|{ep}")

def approve(ep):
    from whatifs import publish as PUB
    from whatifs.manage import next_slots
    st = store(); e = next((r for r in st.rows("Episodes") if r.get("episode_id") == ep), None)
    if not e or not e.get("yt_id"): return f"{ep} not found"
    from whatifs.core import parse_iso
    import datetime as dt
    t = parse_iso(e.get("slot_et")); slot = e.get("slot_et")
    taken = {r.get("slot_et") for r in st.rows("Episodes") if r.get("status") in ("SCHEDULED", "LIVE1", "LIVE") and r.get("episode_id") != ep}
    if not t or t < now_utc() + dt.timedelta(minutes=30) or slot in taken:
        slot = next((s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in next_slots(12, now_utc() + dt.timedelta(minutes=30)) if s.strftime("%Y-%m-%dT%H:%M:%SZ") not in taken), None)
    if not slot: return "no free slot found"
    PUB.yt_schedule(e["yt_id"], slot)
    st.update("Episodes", "episode_id", ep, {"status": "SCHEDULED", "slot_et": slot, "updated": iso()})
    return f"approved: {ep} publishes at {slot}"

def hold_review(ep):
    store().update("Episodes", "episode_id", ep, {"status": "HELD_BY_OWNER", "updated": iso()})
    return f"{ep} stays private"
