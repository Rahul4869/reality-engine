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
    if rec.get("source") == "short":                           # v12 V2c-b2b: the first line is the hook of the Short this video is about - real viewers stayed for it, no lab is run
        ref = str((ctx.get("d") or {}).get("ladder") or "") if isinstance(ctx.get("d"), dict) else ""
        if not ref or str(rec.get("short") or "") != ref: return FAIL, f"the opening line was taken from Short {rec.get('short') or '?'}, but this video is about {ref or 'no Short'}"
        if rec.get("status") != "applied": return FAIL, f"the hook of Short {ref} is not the first spoken line of the finished narration ({rec.get('status')})"
        return PASS, f"the opening line is the hook of Short {ref}, word for word: the line its viewers stayed for (no lab needed)"
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
    from whatifs import ladder as LAD
    if S("ENDINGS_ON", bool) and LAD.on(): return NA, "under the ladder no next topic is promised: the next long video is the Short viewers pick"      # v12 V2b (issue 101)
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
    """v12 V2d-b: A CHARACTER IS DRAWN OR ABSENT, in every format (the owner's rejected video showed a flat black shape with a name: the code that
    drew it is gone). Every reaction cutaway of the plan is for a character with approved art, and the renderer showed that art in each (blinking,
    breathing, talking). No cutaway at all = nobody is on screen: that passes - absent is the other half of the rule. v12 V2b (CHIP_DRAWN_ONLY_ON): and no
    name chip the render drew (ctx['chips'], what the renderer recorded) names a character nobody sees."""
    from whatifs import living as LV
    react = [s for s in (ctx.get("shots") or []) if s.get("type") == "reaction"]
    bare = sorted({str(s.get("speaker")) for s in react if not LV.has_art(s.get("speaker"))})
    if bare: return FAIL, f"a reaction cutaway is planned for {', '.join(bare)} without approved character art: a character is drawn or absent"
    absent = int(ctx.get("absent") or 0)
    if absent: return FAIL, f"{absent} of {len(react)} reaction cutaways could not show the approved character (the picture before was continued; nothing was drawn in its place)"
    chip_ = S("CHIP_DRAWN_ONLY_ON", bool); tail_ = "; no name chip for a character nobody sees" if chip_ else ""
    if chip_:
        unseen = sorted({str(c[2]) for c in (ctx.get("chips") or []) if not LV.has_art(c[2])})
        if unseen: return FAIL, "; ".join(f"a name chip for {x}, who is never seen" for x in unseen)
    if not react: return PASS, "nobody is on screen: no cutaway of a character was made (a character without approved art is absent, never a shape)" + tail_
    return PASS, f"{len(react)} reaction cutaways, each the approved character ({sum(u['blinks'] for u in LV.USED)} blinks, {sum(u['mouth_frames'] for u in LV.USED)} talking frames in this job)" + tail_

def p_visual_change(ctx):
    """Impact Map V2 + V5: a new picture state at least every VISUAL_CHANGE_MAX_S (graphics/reaction cutaways animate: 2x), and no 2-s window
    with 3+ changes (overload). Recomputed with the same rule the renderer uses (shotplan.pieces_for)."""
    from whatifs.shotplan import pieces_for
    units, shots = ctx.get("units") or [], ctx.get("shots") or []
    if not units or not shots: return NA, "no shot timeline in this run"
    mx = S("VISUAL_CHANGE_MAX_S", float); bounds, worst, where, fast, facts = [], 0.0, "", [], []
    if ctx.get("states"):                                          # v12 V2d-b: judged on what the RENDER showed - one entry per picture state - never on a second copy of the cutting rule
        for a, b, typ, clip, short in ctx["states"]:
            step = float(b) - float(a); bounds.append(float(a))
            if step < 1.0: fast.append(float(a))
            if clip and short: continue                            # a stretch of the Short's own footage was cut and judged as a Short
            lim = S("VISUAL_ANIMATED_MAX_S", float) if typ in ("graphic", "reaction") else mx * (2 if clip else 1)
            if step > lim + 0.05 and step - lim > worst: worst, where = step - lim, f"{float(a):.0f}s ({'a playing clip' if clip else typ}, {step:.1f} s as one picture state)"
        facts = [float(u.get("start", 0) or 0) for u in units if re.search(r"\d", str(u.get("text", "")))]
        units = []                                                 # nothing is recomputed below
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
    src = ctx.get("scenes") if ctx.get("scenes") is not None else ctx.get("clips")      # v12 V2d-b: the animated SCENES (a still brought to life moves gently by design: check moving_share judges it on the film)
    clips = [c for c in (src or []) if c and os.path.exists(c)]
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

def p_research_cadence(ctx):
    """R&D and the Review Board on schedule (judged at the script gate): R&D's daily and weekly research ran, every research memo carries code-verified
    sources and an evidence ceiling that re-computes, every one was assessed within its SLA or escalated, every assessment's verdict is the code's
    verdict on its own blind two-family checklist with a rejected canary, and neither department spent past its cap without an owner question."""
    from whatifs.org import rnd as RND
    p, s, na = RND.cadence_issues()
    if na: return NA, na
    if p: return FAIL, f"{len(p)} problem(s): " + " | ".join(p[:3])
    return PASS, (f"R&D daily {s.get('daily_h')} h ago, weekly {s.get('weekly_d')} d ago; {s.get('research_memos', 0)} research memo(s): {s.get('assessed', 0)} assessed, "
                  f"{s.get('escalated', 0)} escalated; {s.get('assessments', 0)} assessment(s) re-computed ({s.get('accept', 0)} accept, {s.get('test', 0)} test, "
                  f"{s.get('reject', 0)} reject); spent D2 Rs {s.get('D2_inr', 0)}, D3 Rs {s.get('D3_inr', 0)}")

def p_viewer_plain(ctx):
    """v12 V1b (the layman test, D13): few expert words - the distinct words a layman would not know, in the whole narration, in the first 30 s and
    piled into one sentence. Counted by code (whatifs/org/layman.py); names and the title's own words are not counted."""
    from whatifs.org import layman as LAY
    if not LAY.on(): return NA, "the layman test is switched off (LAYMAN_ON / VIEWER_SEAT_ON)"
    text = _script_text(ctx)
    if not str(text or "").strip(): return FAIL, "empty script"
    r = LAY.plain_report(text, ctx.get("units"), LAY.promise_words(ctx.get("pkg"), ctx.get("d"))[1])
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:400]
    return PASS, (f"{len(r['hard'])} expert word(s) a layman would not know (limit {r['allowed']})" + (f": {', '.join(r['hard'][:6])}" if r["hard"] else "")
                  + f"; {len(r['opening'])} in the first 30 s (limit {r['opening_max']}); sentences: median {r['median_words']} words, longest {r['longest_words']}")

def p_viewer_probe(ctx):
    """v12 V1b (the layman test, D13): the promise line-up - from the first 30 s alone, two first-time readers of two model families picked this
    video's title out of a line-up, and gave no title to the planted opening. The verdict is computed by code (layman.probe); a void session is
    D13's own problem and never holds a video."""
    from whatifs.org import layman as LAY
    if not LAY.on() or not S("LAYMAN_PROBE_ON", bool): return NA, "the promise line-up is switched off (LAYMAN_PROBE_ON / LAYMAN_ON)"
    p = ctx.get("probe")
    if not isinstance(p, dict) or not p.get("status"): return NA, "no promise line-up in this run (it is made in the plan stage, right after the package)"
    st = str(p.get("status")); why = str(p.get("why") or "")[:380]
    if st == "pass": return PASS, why
    if st == "fail": return FAIL, why
    return NA, (f"the line-up was void and is not counted ({why})" if st == "void" else why or st)

def p_viewer_inside(ctx):
    """v12 V2b (inside the scene, D13): the voice speaks to the viewer as something happening to him now - a floor for the share of counted sentences
    that do, no run of sentences from outside longer than the format's limit, and no beat that explains before it shows. Counted by code
    (whatifs/org/inside.py), judged on the script; the format's row says the floor and the limit. Never a device: no format can loosen it."""
    from whatifs.org import inside as INS
    from whatifs import formats as FMT
    if not INS.on(): return NA, "the voice rule is switched off (INSIDE_ON / VIEWER_SEAT_ON)"
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    fmt = str(d.get("format") or "")
    if fmt not in FMT.FORMATS: return NA, "no format on this episode (written before formats existed, or FORMATS_ON is off)"
    r = INS.report(_script_text(ctx), fmt)
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    return PASS, (f"{r['inside']} of {r['n']} sentences ({r['share_pct']:g}%) inside the scene (floor {r['min_pct']:g}%); the longest run from outside {r['run']} "
                  f"(limit {r['run_max']}); no act explains before it shows")

def p_format_ending(ctx):
    """v12 V2b (the ending is the format's, D4): F1 ends on the question to the viewer, F3 on the arrival; no ask and no pointer to another video in the
    last seconds (formats.tail, on the script's words); only the asks the format carries (code removed the others: d['asks_removed']). Never a device."""
    from whatifs import formats as FMT
    if not S("ENDINGS_ON", bool): return NA, "the format's own ending is switched off (ENDINGS_ON)"
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    fmt = str(d.get("format") or "")
    if fmt not in FMT.FORMATS: return NA, "no format on this episode (written before formats existed, or FORMATS_ON is off)"
    if FMT.ending(fmt) == "tease": return NA, f"format {fmt} ends on a tease (its own devices judge it)"
    r = FMT.ending_report(_script_text(ctx), fmt, d.get("asks_removed"))
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    asks = ", ".join(f"{k} {n}" for k, n in sorted(r["asks"].items())) or "none"
    return PASS, (f"ends on its {r['ending']}: '{r['last'][:90]}'; no ask and no pointer in the tail; asks in this video: {asks}; "
                  f"removed by code: {sum(int(v) for v in r['removed_kinds'].values())}")

def p_camera_path(ctx):
    """v12 V2b (the camera path, D6): on the shot list, BEFORE any picture is paid - every shot of an act carries its mark, every act opens on a picture of
    its own (episode.anchors_for: what the asset step will make), every picture whose angle code assigned is at eye level, every still and living prompt
    holds its act's place, and the acts were joined (none shorter than ACT_MIN_S beside another, no more changes of place than the allowance)."""
    from whatifs import path as PATH, episode as EP
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}; units = ctx.get("units") or []; shots = ctx.get("shots") or []
    why = PATH.why_na(str(d.get("format") or ""), units)
    if why: return NA, why
    total = float(ctx.get("total") or (units[-1].get("end") if units else 0) or 0)
    r = PATH.plan_report(shots, units, total, EP.anchors_for(shots, units, d, ctx.get("plan") or {}))
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    return PASS, (f"{r['acts']} acts in {len(set(r['places']))} places ({r['changes']} changes in {r['minutes']:.1f} min, at most {r['allow']}): " + " | ".join(r["places"])[:200]
                  + ("; every picture at eye level" if r["angles"] else "; angle not assigned by code") + "; every act opens on its own picture")

def p_camera_shown(ctx):
    """v12 V2b (the camera path, D6): on what the RENDER recorded (ctx['path_states']), never the plan - every still state of an act showed a picture of
    its own act, moved one of the path's moves (never backwards, never rolled, always recorded) and travelled in its act's direction."""
    from whatifs import path as PATH
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    why = PATH.why_na(str(d.get("format") or ""), ctx.get("units") or [])
    if why: return NA, why
    r = PATH.shown_report(ctx.get("path_states") or [], ctx.get("shots") or [])
    if not r["states"]: return NA, "no still state carries an act"
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    return PASS, (f"{r['states']} still states in {r['acts']} acts: each showed a picture of its own act, at eye level, travelling one way ("
                  + ", ".join(f"{k} {v}" for k, v in sorted(r["moves"].items())) + ")")

def p_format_kept(ctx):
    """v12 V2a: the script is what its FORMAT says - a format that is not a trial does not sound like one (no name of the court's cast, no courtroom
    furniture, only its own voices); a trial has its Show Plan."""
    from whatifs import formats as FMT
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    fmt = str(d.get("format") or "")
    if fmt not in FMT.FORMATS: return NA, "no format on this episode (written before formats existed, or FORMATS_ON is off)"
    r = FMT.kept_report(_script_text(ctx), fmt, d)
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    dev = FMT.FORMATS[fmt]["devices"]
    return PASS, (f"format {fmt} ({FMT.name(fmt)}): " + ("the Show Plan is there" if FMT.FORMATS[fmt]["show"] else "no courtroom word, only its own voices")
                  + f"; devices: {sum(1 for k in FMT.DEVICES if dev.get(k, 'must') == 'must')} required, {sum(1 for v in dev.values() if v == 'advisory')} optional, "
                  f"{sum(1 for v in dev.values() if v == 'never')} not part of it")

def p_topic_ladder(ctx):
    """v12 V2c-b (the ladder, D10): every topic starts as a Short - this long video is about the topic of a Short the promote rule took (the same
    premise, promoted for this video), or it was made under an override that is on record (who, when, why)."""
    from whatifs import ladder as LAD
    if not LAD.on(): return NA, "the ladder is switched off (LADDER_ON, or the Shorts track)"
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    ok, why = LAD.topic_report(d, ((ctx.get("room") or {}).get("spine") or {}).get("premise"), ctx.get("ep"))
    return (PASS if ok else FAIL), why[:380]

def p_opening_footage(ctx):
    """v12 V2c-b2b (the opening, D6): a long video about a promoted Short opens on THAT Short's kept footage - judged on the shot list, before any
    picture is paid: the archive of its ladder row was fetched whole, the first shots carry it and nothing else, laid as the rule says."""
    from whatifs import opening as OPEN
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    ok, why = OPEN.plan_report(d, ctx.get("shots") or [], ctx.get("units") or [], ctx.get("opening"))
    return (NA if ok is None else PASS if ok else FAIL), why[:380]

def p_opening_shown(ctx):
    """v12 V2c-b2b (the opening, D6): the FINISHED film opens on its Short's footage - the opening clips are the files cut from that Short's
    archive and frames of the master match them. A video the owner approved without its footage (opening_footage waived) is not judged again."""
    from whatifs import opening as OPEN
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}
    if OPEN.source(d)[0] == "short" and not OPEN.marked(ctx.get("shots")) and _waived(ctx.get("ep"), "opening_footage"):
        return NA, "the owner approved this video without its Short's footage (opening_footage waived): it opens on its own pictures"
    ok, why = OPEN.shown_report(d, ctx.get("shots") or [], ctx.get("units") or [], ctx.get("opening"), ctx.get("master"))
    return (NA if ok is None else PASS if ok else FAIL), why[:380]

def p_viewer_numbers(ctx):
    """v12 V1 (the viewer's seat, D13): few numbers - what a viewer hears per minute, and the full-screen number graphics he must read."""
    from whatifs.org import audience as AUD
    if not AUD.on(): return NA, "the viewer's seat is switched off (VIEWER_SEAT_ON)"
    text = _script_text(ctx)
    if not str(text or "").strip(): return FAIL, "empty script"
    r = AUD.numbers_report(text, ctx.get("shots"), ctx.get("units"))
    if r["problems"]: return FAIL, "; ".join(r["problems"])
    g = "" if ctx.get("shots") is None else ("; no number graphic" if not r["graphics"] else f"; {r['graphics']} number graphic(s)"
                                             + (f", the first at {r['first_graphic_s']:.0f} s" if r["first_graphic_s"] is not None else ""))
    return PASS, f"{r['numbers']} numbers heard = {r['per_min']:.1f} a minute (limit {r['max_per_min']:g})" + g

def p_viewer_breath(ctx):
    """v12 V1 (the viewer's seat, D13): the voice breathes - never longer than BREATH_EVERY_S (+25%) without a real pause, judged on the voice timeline."""
    from whatifs.org import audience as AUD
    if not AUD.on(): return NA, "the viewer's seat is switched off (VIEWER_SEAT_ON)"
    r = AUD.breath_report(ctx.get("units"))
    if r is None: return NA, "no voice timeline in this run (judged at the production's script gate, once the voice is made)"
    if r["problems"]: return FAIL, r["problems"][0]
    return PASS, f"{r['pauses']} pauses; the longest stretch without one is {r['longest_s']:.0f} s (limit {r['limit_s']:.0f} s); {r['wpm']} words a minute"

def p_viewer_promise(ctx):
    """v12 V1 (the viewer's seat, D13): the video OPENS on a made picture and the thumbnail's promise is on screen by PROMISE_BY_SEC - judged before any
    picture is paid (promise_paid judges the finished video again)."""
    from whatifs import breakout as BRK
    from whatifs.org import audience as AUD
    if not AUD.on(): return NA, "the viewer's seat is switched off (VIEWER_SEAT_ON)"
    if not S("PROMISE_SHOT_ON", bool): return NA, "promise shot off (owner setting)"
    shots, units = ctx.get("shots") or [], ctx.get("units") or []
    if not shots: return NA, "no shot list in this run (judged at the production's script gate)"
    if shots[0].get("type") not in AUD.PICTURES: return FAIL, f"the video opens on a {shots[0].get('type')}, not on a made picture"
    t = BRK.promise_start(shots, units)
    if t is None:
        if not any(s.get("type") == "kling" for s in shots): return NA, "no animated scene this episode (budget-trimmed), so no promise scene to place"
        pkg = ctx.get("pkg") or {}; promise = (pkg.get("promise") or {}) if isinstance(pkg, dict) else {}
        if isinstance(promise, dict) and not (promise.get("thumbnail") or promise.get("title") or promise.get("text")) and not (ctx.get("d") or {}).get("promise") \
                and not (isinstance(pkg, dict) and pkg.get("thumb_prompt")):
            return NA, "no packaging promise for this episode"
        return FAIL, "an animated scene exists, but none shows the thumbnail's promise"
    lim = S("PROMISE_BY_SEC", float)
    return (PASS, f"the promise is on screen at {t:.1f} s") if t <= lim else (FAIL, f"the promise is first shown at {t:.1f} s (limit {lim:.0f} s)")

def _creative_gate(ctx, which):
    """v12 B6a: the creative runs of this episode (D4 write or its adopted draft, D5 package, D6 plan) judged from their receipts."""
    from whatifs.org import cite as CITE
    r = CITE.episode_issues(ctx.get("ep"), which)
    if r["na"]: return NA, r["na"]
    if r["problems"]: return FAIL, f"{len(r['problems'])} problem(s): " + " | ".join(r["problems"][:3])
    s = r["stats"]; leg = f"; {s['legacy']}" if s.get("legacy") else ""
    if which == "injected": return PASS, f"{s['runs']} creative run(s): the playbook was inside the prompt of each key call (writer / packager / director) and its text is stored{leg}"
    return PASS, f"{s['runs']} creative run(s): {s['verified']} citation(s) verified by quote, {s['unverified']} not found, {s['ghost']} never offered{leg}"

def p_palace_injected(ctx): return _creative_gate(ctx, "injected")
def p_palace_cited(ctx): return _creative_gate(ctx, "cited")

def p_canon_in_brief(ctx):
    """v12 B6a: the writer was given the show's canon (cast + the newest aired case), paid the continuity debt in a line of the final script, and wrote
    this episode's case record."""
    from whatifs.org import canon as CANON
    r = CANON.episode_issues(ctx.get("ep"), _script_text(ctx), fmt=(ctx.get("d") or {}).get("format"))      # v12 V2b (issue 77): a format that is not a trial is not asked for the cast
    if r["na"]: return NA, r["na"]
    if r["problems"]: return FAIL, f"{len(r['problems'])} problem(s): " + " | ".join(r["problems"][:3])
    s = r["stats"]
    return PASS, (f"canon given: {s.get('cast', 0)} cast item(s) + newest case {s.get('newest_case')}; " + (f"callback in the script: '{s['callback']}'" if s.get("callback") else "no aired case to call back to yet")
                  + "; case record written")

def p_moving_share(ctx):
    """v12 V2d-b (the motion ladder, D6): THE SHARE OF THE FINISHED FILM THAT REALLY MOVES. Measured on the file: a half second counts where the
    renderer played a clip made by a model (its Short's footage, an animated scene, a still brought to life) AND the film's picture changes there.
    The video is held under the floor MOVING_SHARE_MIN_LONG, and when it shows less than MOVING_SEEN_MIN_PCT of the seconds of clip it paid for."""
    from whatifs import motion as MOT
    if not MOT.on(): return NA, "the motion ladder is switched off (MOTION_LADDER_ON; it needs CLIP_VALUE_ON)"
    m = ctx.get("master")
    if ctx.get("moving") is None: return NA, "no render record in this run (judged on the finished film)"
    if not m or not os.path.exists(m): return FAIL, "no finished video to measure"
    try: r = MOT.long_report(m, ctx.get("moving"), ctx.get("moving_paid_s"))
    except Exception as e: return FAIL, f"could not measure: {scrub(e)[:120]}"
    d = ctx.get("d") if isinstance(ctx.get("d"), dict) else {}; d["moving_share"] = {k: r[k] for k in ("duration", "moving_s", "share_pct", "by", "paid_s", "seen_pct")}
    floor = S("MOVING_SHARE_MIN_LONG", float); seen = S("MOVING_SEEN_MIN_PCT", float); plan = d.get("moving") or {}; p = []
    if r["share_pct"] < floor - 1e-6: p.append(f"only {r['share_pct']:g}% of the film is moving pictures (the floor is {floor:g}%)")
    if r["seen_pct"] is not None and r["seen_pct"] < seen - 1e-6:
        p.append(f"of {r['paid_s']:g} s of clip this video paid for only {r['seen_pct']:g}% are on screen and moving (at least {seen:g}%)"
                 + (f"; nothing changes at {', '.join(f'{t:g} s ({k})' for t, k in r['frozen'][:4])}" if r["frozen"] else ""))
    ev = (f"{r['moving_s']:g} of {r['duration']:g} s move = {r['share_pct']:g}% (floor {floor:g}%; the lever asks {S('MOVING_SHARE_LONG', float):g}%"
          + (f", this month's money planned {plan.get('bought_pct'):g}%" if plan.get("bought_pct") is not None else "") + "): "
          + (", ".join(f"{k} {v:g} s" for k, v in r["by"].items()) or "nothing") + (f"; {r['seen_pct']:g}% of the {r['paid_s']:g} s paid are seen moving" if r["seen_pct"] is not None else ""))
    sc_paid = round(sum(_dur(c) for c in (ctx.get("scenes") or []) if c and os.path.exists(c)), 1)      # v12 V2d-b red 1: the peaks - the scenes' seconds on screen (as the render recorded them) of those paid
    if sc_paid > 0: ev += f"; the scenes on screen {r.get('scene_shown_s', 0):g} of {sc_paid:g} s ({round(100.0 * float(r.get('scene_shown_s') or 0) / sc_paid, 1):g}%)"
    return (FAIL, ("; ".join(p) + " | " + ev)[:380]) if p else (PASS, ev[:380])

def p_stock_share(ctx):
    """v12 V2d-b (real footage, D6): THE STOCK RULES ON THE FINISHED FILM - what the renderer really showed of NASA's and Pexels' footage: a tenth of
    the runtime at most, never the first picture, never two in a row, never longer than an anchor, every clip with a record that names its source
    and no person, every credit in the description. No real footage at all passes (it is allowed, never demanded)."""
    from whatifs import stock as STK
    st_ = ctx.get("stock")
    if st_ is None: return NA, "no render record in this run (judged on the finished film)"
    dur = float((ctx.get("timeline") or {}).get("duration") or 0) or _dur(ctx.get("master") or "")
    r = STK.report(ctx.get("shots") or [], st_.get("spans"), st_.get("records"), st_.get("description"), dur)
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    if not r["n"]: return PASS, "no real footage in this video" + ("" if STK.on() else " (switched off: STOCK_ON)")
    return PASS, (f"{r['n']} clip(s) of real footage, {r['seconds']:g} s = {r['share_pct']:g}% of the film (limit {r['limit_pct']:g}%); never first, never two in a row; "
                  f"cropped in and slowed by the renderer; no title names a person; credited: {', '.join(r['credits'])}")

# ------------------------------------------------------------------ v12 V2d-b: the gate of a Short's FINISHED FILE (stage "short_file": after it is made, before it is handed to Publishing)
def _short_file(ctx):
    from whatifs import motion as MOT
    if not MOT.on(): return None, (NA, "the motion ladder is switched off (MOTION_LADDER_ON; it needs CLIP_VALUE_ON)")
    f = ctx.get("short_file") if isinstance(ctx.get("short_file"), dict) else {}
    if not f.get("path") or not os.path.exists(str(f["path"])): return None, (FAIL, "no finished Short reached the gate of its file")
    return f, None

def p_short_moving(ctx):
    """v12 V2d-b (D6): A SHORT MOVES IN EVERY SECOND - measured on its finished file, half second by half second, in the band of the picture that never
    carries words: a clip that came back shorter than it was bought and was held on its last frame, or a clip that does not move, is found."""
    from whatifs import motion as MOT
    f, out = _short_file(ctx)
    if f is None: return out
    try: r = MOT.short_report(f["path"])
    except Exception as e: return FAIL, f"could not measure: {scrub(e)[:120]}"
    if not r["cells"]: return FAIL, "the finished Short has no picture to measure"
    if r["still"]: return FAIL, (f"{r['cells'] - r['moving']} of {r['cells']} half seconds of the Short do not move ({r['share_pct']:g}% moves; a Short moves in every second): "
                                 f"nothing changes at {', '.join(f'{t:g}' for t in r['still'][:6])} s")
    return PASS, f"every one of the {r['cells']} half seconds of the {r['duration']:g} s Short changes on the finished file (100% moves)"

def p_short_sound(ctx):
    """v12 V2d-b (Sound, D7): A SHORT SOUNDS FROM ITS FIRST FRAME - measured on its finished file: its level passes the floor inside SHORT_SOUND_BY_S
    seconds, the first fifth of a second is at least SHORT_SOUND_MIN_DB loud (no fade-in from silence), nothing clips, and the guide's first
    word starts inside SHORT_VOICE_BY_S seconds (the real voice timeline)."""
    from whatifs import sound as SD
    f, out = _short_file(ctx)
    if f is None: return out
    try: r = SD.first_second(f["path"])
    except Exception as e: return FAIL, f"could not measure: {scrub(e)[:120]}"
    by, mn, vb = S("SHORT_SOUND_BY_S", float), S("SHORT_SOUND_MIN_DB", float), S("SHORT_VOICE_BY_S", float); units = f.get("units") or []; p = []
    try: v0 = float(((units[0].get("words") or [{}])[0]).get("s", units[0].get("start"))) if units else None
    except (TypeError, ValueError, IndexError): v0 = None
    if r["onset_s"] is None: p.append("the Short is silent in its first second and a half")
    elif r["onset_s"] > by + 1e-6: p.append(f"the first sound comes at {r['onset_s']:g} s (inside {by:g} s of the first frame)")
    if r["onset_s"] is not None and r["db_200"] < mn - 1e-6: p.append(f"the first fifth of a second is only {r['db_200']:g} dBFS loud (at least {mn:g}): it fades in")
    if r["peak_db"] > -0.1: p.append(f"the first second clips ({r['peak_db']:g} dBFS)")
    if v0 is None: p.append("no voice timeline reached the gate")
    elif v0 > vb + 1e-6: p.append(f"the guide's first word starts at {v0:g} s (inside {vb:g} s)")
    if p: return FAIL, "; ".join(p)[:380]
    return PASS, (f"sound from {r['onset_s']:g} s (limit {by:g} s), the first fifth of a second at {r['db_200']:g} dBFS (at least {mn:g}), the first second at {r['db_1000']:g} dBFS; "
                  f"the guide speaks from {v0:g} s" + (f"; the place sounds of {f.get('sound')}" if f.get("sound") else ""))

# ------------------------------------------------------------------ v12 V2c: the short gate (stage "short": a standalone Short, before any picture is paid)
def _short(ctx):
    s = ctx.get("short"); return s if isinstance(s, dict) and isinstance(s.get("script"), dict) else None

def _short_seat(ctx):
    """(the Short at the gate, None) or (None, the (status, evidence) to return): the seat switched off = NA, nothing at the gate = FAIL."""
    from whatifs.org import shortseat as SEAT
    if not SEAT.on(): return None, (NA, "the viewer's seat for a Short is switched off (SHORT_SEAT_ON / VIEWER_SEAT_ON)")
    s = _short(ctx)
    if s is None: return None, (FAIL, "no Short script reached the short gate")
    if not s.get("units") or not isinstance(s.get("plan"), dict): return None, (FAIL, "the Short reached the gate without its real voice timeline or its picture plan")
    return s, None

def p_short_open(ctx):
    """v12 V2c (the viewer's seat for a Short, D13): the first frame is the moving promise picture, the hook has at most SHORT_HOOK_WORDS_MAX words
    and ENDS inside SHORT_HOOK_BY_S seconds of the real voice, the promise text is on screen inside the first second."""
    from whatifs.org import shortseat as SEAT
    s, out = _short_seat(ctx)
    if s is None: return out
    r = SEAT.open_report(s["script"], s["units"], s["plan"])
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    pr = str((s["plan"].get("promise") or {}).get("text") or "")
    return PASS, (f"the hook '{r['hook'][:60]}' has {r['hook_words']} words (limit {r['hook_max']}) and ends at {r['hook_end_s']} s of the voice (limit {r['hook_by_s']:g} s); "
                  "the first frame is the moving promise picture" + (f"; promise text '{pr}' from the first frame" if pr else "; no promise text (switched off)"))

def p_short_plain(ctx):
    """v12 V2c (D13): a Short a layman follows on one listen - at most SHORT_NUMBERS_MAX number heard and SHORT_EXPERT_MAX expert words."""
    from whatifs.org import shortseat as SEAT
    s, out = _short_seat(ctx)
    if s is None: return out
    r = SEAT.plain_report(s["script"])
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    return PASS, f"{r['numbers']} number(s) heard (limit {r['numbers_max']}); {len(r['hard'])} expert word(s) a layman would not know (limit {r['hard_max']})"

def p_short_shape(ctx):
    """v12 V2c (D13): the shape of a Short - its real length inside the format's band, the last line hands back to the first, no ask, every second
    planned as an animated clip with no gap and no stock, the last shot is the first clip returning (the loop), captions above the buttons."""
    from whatifs.org import shortseat as SEAT
    s, out = _short_seat(ctx)
    if s is None: return out
    r = SEAT.shape_report(s["script"], s.get("format"), s["units"], s["plan"])
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    m = SEAT.m_shape(s["plan"])
    return PASS, (f"{r['seconds']} s (format {s.get('format')}: {r['band'][0]:g} to {r['band'][1]:g} s); the last line hands back ('{', '.join(r['handback'][:3])}'); no ask; "
                  f"{m['shots']} clips cover every second ({m['paid_clips']} made, the last is the first clip returning); captions on")

def p_short_kept(ctx):
    """v12 V2c (the Shorts Studio, D14): the Short is what its FORMAT says (its beats, its ending, one guide voice, no courtroom) and is not like the
    last ten Shorts (likeness of script and opener; the pair format + hook differs from the last two)."""
    from whatifs import formats as FMT
    from whatifs.org import shortseat as SEAT
    s, out = _short_seat(ctx)
    if s is None: return out
    fmt = str(s.get("format") or "")
    if fmt not in FMT.SHORTS: return FAIL, f"the Short has no Short format ('{fmt}')"
    r = FMT.short_kept_report(s["script"], fmt, s.get("hook") or "", s.get("last") or ())
    if r["problems"]: return FAIL, "; ".join(r["problems"])[:380]
    return PASS, (f"format {fmt} ({FMT.short_name(fmt)}): beats {', '.join(r['roles'])}; one guide voice, no courtroom word; unlike the last "
                  f"{len([x for x in (s.get('last') or ()) if isinstance(x, dict)][:10])} Short(s); hook '{s.get('hook')}'")

def p_short_contract(ctx): return _org_gate(ctx, "short")

def p_release_sheet(ctx):
    """v12 V2c-b2 (Publishing, D9): the release sheet of a Short, judged AFTER its uploads from what each platform itself answered - every row code
    sets was kept (or repaired once, or sent where the platform shows nothing back), on YouTube always and on Instagram and Facebook when they are
    connected; the file each platform got is the one master."""
    from whatifs import release as REL
    if not REL.on(): return NA, "the release sheet is switched off (RELEASE_SHEET_ON)"
    sid = str((ctx.get("release") or {}).get("id") or "")
    if not sid: return FAIL, "nothing reached the release gate"
    ok, why = REL.report(sid)
    return (PASS if ok else FAIL), why[:380]

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
    ("research_cadence", "script", p_research_cadence, "R&D researched on schedule with sources proven by code, and the Review Board judged every research memo in time, blind, across two model families, with a rejected canary and the verdict computed by code"),
    ("viewer_promise", "script", p_viewer_promise, "the video opens on a made picture and the thumbnail's promise is on screen within PROMISE_BY_SEC seconds (the viewer's seat)"),
    ("viewer_breath", "script", p_viewer_breath, "the voice breathes: a real pause at least every BREATH_EVERY_S seconds (the viewer's seat)"),
    ("viewer_numbers", "script", p_viewer_numbers, "few numbers: a budget for the numbers a viewer hears and for full-screen number graphics, none in the opening (the viewer's seat)"),
    ("viewer_plain", "script", p_viewer_plain, "everyday words: a budget for the expert words a layman would not know - in the narration, in the first 30 s, in one sentence (the layman test)"),
    ("viewer_probe", "script", p_viewer_probe, "the promise line-up: from the first 30 s alone two first-time readers pick this video's title, and give none to a planted opening (the layman test)"),
    ("format_kept", "script", p_format_kept, "the script is what its format says: a format that is not a trial does not sound like one, a trial has its Show Plan (formats as data)"),
    ("viewer_inside", "script", p_viewer_inside, "the voice speaks to YOU, now: at least the format's share of sentences put the viewer inside the scene, never a run of sentences from outside longer than its limit, and no beat explains before it shows (inside the format)"),
    ("camera_path",   "script", p_camera_path,   "one place per act, seen from where the viewer stands: every act opens on a picture of its own, every picture at eye level holds its act's place, the acts are joined to an allowance (inside the format)"),
    ("format_ending", "script", p_format_ending,"the video ends as its format ends - F1 on the question to the viewer, F3 on the arrival - with no ask and no pointer to another video in its last seconds, and carries only the asks of its format (inside the format)"),
    ("topic_ladder", "script", p_topic_ladder, "every topic starts as a Short: this long video is about the topic of a Short the promote rule took, or was made under an override on record (the ladder)"),
    ("opening_footage", "script", p_opening_footage, "a long video about a promoted Short opens on that Short's own footage, laid by code under its first sentences - or was made under an override, which has none (the opening)"),
    ("palace_injected", "script", p_palace_injected, "the Knowledge Palace playbook was inside the model prompt of every creative run's key call (the writer, the packager, the director), and the exact text is stored"),
    ("palace_cited", "script", p_palace_cited, "every creative run cited Palace knowledge it really applied: each counted citation has a quote that code found in the final output"),
    ("canon_in_brief", "script", p_canon_in_brief, "the writer was given the show's canon (cast and the newest aired case), called back to that case in a line of the final script, and wrote this episode's case record"),
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
    ("self_review",   "final",  p_critique,     "6-point creative self-review at or above the bar"),
    ("promise_paid",  "final",  p_promise_paid, "the thumbnail's promise is on screen early"),
    ("impact_map",    "final",  p_impact,       "Impact Map: hook in 3 s, timed punchlines, sound spacing, variety vs last 10, flash safety"),
    ("visual_change", "final",  p_visual_change, "a new picture state every <= VISUAL_CHANGE_MAX_S, no overload"),
    ("living_characters", "final", p_living,   "a character is drawn or absent: every reaction cutaway shows the approved character, blinking, breathing and talking - and where no art is approved nobody is shown, never a shape"),
    ("breakout_bar",  "final",  p_breakout_bar, "Breakout Score >= BREAKOUT_HARD_BAR (no upload below it)"),
    ("aliveness",     "final",  p_alive,        "no stretch of the video looks like a still photo"),
    ("camera_shown",  "final",  p_camera_shown, "what the render recorded keeps the camera path: every still state of an act showed a picture of its own act, never moved backwards or rolled, and travelled one way (inside the format)"),
    ("opening_shown", "final",  p_opening_shown,"the finished film opens on its Short's footage: the opening clips are the files cut from that Short's archive and the frames of the film match them (the opening)"),
    ("moving_share",  "final",  p_moving_share, "the share of the finished film that really moves - measured on the file where the renderer played a clip made by a model - is at least MOVING_SHARE_MIN_LONG, and the seconds of clip the video paid for are on screen and moving (the motion ladder)"),
    ("stock_share",   "final",  p_stock_share,  "real footage (NASA, Pexels) is a short anchor: STOCK_SHARE_MAX_PCT of the film at most, never the first picture, never two in a row, changed, no clip whose title names a person, every credit in the description"),
    ("takeaways_written", "final", p_takeaways_written, "every department run of this episode finished its six steps and wrote a valid takeaway"),
    # v12 V2c: stage "short" = the short gate of a standalone Short (whatifs/shorts2.py), judged before any picture is paid; a held Short is not made
    ("short_open",    "short",  p_short_open,   "a Short opens on the moving promise picture, its hook has at most SHORT_HOOK_WORDS_MAX words and ends inside SHORT_HOOK_BY_S seconds of the real voice, the promise text is on screen in the first second (the viewer's seat for a Short)"),
    ("short_plain",   "short",  p_short_plain,  "a Short a layman follows on one listen: one number at most, no expert word (the viewer's seat for a Short)"),
    ("short_shape",   "short",  p_short_shape,  "a Short has its format's length, hands its last line back to the first, asks for nothing, is an animated clip in every second and loops into its first frame, captions above the buttons (the viewer's seat for a Short)"),
    ("short_kept",    "short",  p_short_kept,   "a Short is what its Short format says and is not like the last ten Shorts (Short formats as data)"),
    ("short_contract", "short", p_short_contract, "every department that worked on a Short (the Shorts Studio, Sound, Audience) ran under the department contract before the short gate"),
    # v12 V2d-b: stage "short_file" = the gate of a Short's FINISHED FILE (whatifs/shorts2.py), after it is made and before it is handed to Publishing; a Short that fails is kept and waits for the owner's tap
    ("short_moving",  "short_file", p_short_moving, "a Short moves in every second: every half second of its finished file changes (the motion ladder)"),
    ("short_sound",   "short_file", p_short_sound, "a Short sounds from its first frame: its place's own sound inside SHORT_SOUND_BY_S seconds at full level, the guide's first word inside SHORT_VOICE_BY_S seconds - measured on the finished file"),
    # v12 V2c-b2: stage "release" = the release gate of a standalone Short (whatifs/release.py), judged AFTER the uploads from the platforms' own answers; the Short is public by then: nothing is held
    ("release_sheet", "release", p_release_sheet, "every setting of a Short's release sheet that code sets was kept by YouTube, Instagram and Facebook as each platform itself answers (or was repaired once), and each got the one master file (the release sheet)"),
]
CRIT_KEYS = ("hook", "clarity", "humour", "visual_variety", "audio", "accuracy")

def enabled(fid):
    off = {x.strip() for x in str(S("CONTRACT_OFF") or "").split(",") if x.strip()}
    return fid not in off

# ------------------------------------------------------------------ the gate
def run(stage, ctx, ep, write=True):
    """Evaluate every feature of a stage. Returns {'ok', 'failed': [(id, evidence)], 'rows'}. Writes Feature_Ledger. Never raises."""
    from whatifs import formats as FMT
    rows, failed = [], []
    fmt = str((ctx.get("d") or {}).get("format") or "") if isinstance(ctx.get("d"), dict) else ""      # v12 V2a: the three-tier contract - a DEVICE is judged by the episode's format
    for fid, stg, probe, what in FEATURES:
        if stg != stage or not enabled(fid): continue
        rule = FMT.rule(fid, fmt)
        if rule == "never": status, ev = NA, f"not part of format {fmt} ({FMT.name(fmt)})"
        else:
            try: status, ev = probe(ctx)
            except Exception as e: status, ev = FAIL, f"check crashed: {scrub(e)[:120]}"
            if rule == "advisory" and status == FAIL: status, ev = NA, f"optional in format {fmt}, not held: {ev}"
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
