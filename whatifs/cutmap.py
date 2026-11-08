"""whatifs/cutmap.py v8.0 - reviewable cut map (edit decision list proposal) from the ACTUAL rendered narration / video.

NOTHING IS EVER CUT AUTOMATICALLY. The project has no editor that can safely re-time narration, captions, pictures, effects and music together,
so this module only measures and proposes. A person reviews cutmap.md / the Cut_Map tab before the video goes public.

Evidence used (best first):
  1. word-level timeline written by voice.py (exact for the synthesized narration; includes which pauses were planned: [pause], paragraph, tags, breaths)
  2. the rendered narration WAV, measured with a frame-RMS silence detector (works without any transcript; results are ESTIMATES when used alone)
  3. optional ffmpeg scan of the finished video for frozen picture / black frames
Stumbles: a stumble cannot be detected reliably from audio alone. With word timings only these signals are measured: repeated adjacent words and
unusually slow sentences. Without word timings no stumble check is done and the map says so.
Sync: narration is the master clock (render.py cuts every shot at narration unit starts). Cuts are placed only inside silence between words, snapped
inward to video frames, and carry the ripple information (shift of everything after, captions, shot boundary, sound effects) needed to apply
the same cut to picture, captions, sfx and music together. ripple_remap()/apply_to_timeline() show exactly how.
"""
from __future__ import annotations
import json, math, os, re, statistics, subprocess
import numpy as np
from whatifs.core import S, log, iso, scrub, safe_append

SCHEMA = 1
LONG_PLANNED_PAUSE = 1.6      # length of the script's own [pause:long]
INTENT_TAGS = ("reveal", "aside", "callback")

def tc(t):
    t = max(0.0, float(t)); m, s = divmod(t, 60); return f"{int(m):02d}:{s:06.3f}"

# ---------------- audio analysis (numpy only) ----------------
def read_mono(path):
    import soundfile as sf
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    return a.mean(axis=1), int(sr)

def analyse_audio(path, min_gap=0.8, frame_ms=20):
    """Silence map of a narration file. Threshold adapts to the file's own noise floor (room tone) but never leaves [-58, -40] dBFS."""
    x, sr = read_mono(path); n = len(x)
    if n < sr * 0.2: raise ValueError("audio too short to analyse")
    hop = int(sr * frame_ms / 1000); nf = n // hop
    fr = x[: nf * hop].reshape(nf, hop)                      # float32 view: no big copy for a 12-minute file
    db = 20 * np.log10(np.sqrt(np.einsum("ij,ij->i", fr, fr, dtype=np.float64) / hop) + 1e-9)
    floor = float(np.percentile(db, 5)); thr = float(min(-40.0, max(-58.0, floor + 9.0)))
    quiet = db < thr
    quiet = (np.convolve(quiet.astype(float), np.ones(5) / 5, mode="same") > 0.5)    # ignore single-frame clicks
    sil, i = [], 0
    while i < nf:
        if quiet[i]:
            j = i
            while j < nf and quiet[j]: j += 1
            sil.append((round(i * hop / sr, 3), round(j * hop / sr, 3))); i = j
        else: i += 1
    return {"duration": round(n / sr, 3), "sample_rate": sr, "noise_floor_db": round(floor, 1), "threshold_db": round(thr, 1),
            "frame_ms": frame_ms, "silences": [s for s in sil if s[1] - s[0] >= 0.15], "min_gap": min_gap}

def silence_overlap(silences, a, b):
    return sum(max(0.0, min(b, e) - max(a, s)) for s, e in silences)

def silent_core(silences, a, b, margin=0.0):
    """Longest silent run inside [a, b] (so a cut never lands on a breath or noise)."""
    best = None
    for s, e in silences:
        s2, e2 = max(a, s) + margin, min(b, e) - margin
        if e2 - s2 > 0 and (best is None or e2 - s2 > best[1] - best[0]): best = (s2, e2)
    return best

# ---------------- timeline helpers ----------------
def _wordspans(tl):
    out = []
    for u in tl.get("units", []):
        ws = u.get("words") or []
        if ws:
            for w in ws: out.append((float(w["s"]), float(w["e"])))
        else: out.append((float(u["start"]), float(u["end"])))
    return sorted(out)

def has_word_timing(tl): return bool(tl) and any(u.get("words") for u in tl.get("units", []))

def snap_inward(a, b, fps):
    """Frame-align a cut so it sits fully inside the silence: start rounds UP to a frame, end rounds DOWN."""
    s = math.ceil(a * fps - 1e-9) / fps; e = math.floor(b * fps + 1e-9) / fps
    return (round(s, 4), round(e, 4)) if e > s else None

def overlaps_speech(a, b, spans, pad=0.02):
    return any(s < b + pad and e > a - pad for s, e in spans)

def sfx_spans(events):
    """Where render.score() puts sound effects: boom at t..t+2.2, whoosh t..t+0.7, riser (t-3)..t."""
    out = []
    for kind, at in events or []:
        at = float(at)
        if kind == "boom": out.append((kind, at, at + 2.2))
        elif kind == "whoosh": out.append((kind, at, at + 0.7))
        elif kind == "riser": out.append((kind, max(0.0, at - 3.0), at))
        elif kind in ("pop", "gasp", "huh"): out.append((kind, at, at + {"pop": 0.22, "gasp": 0.42, "huh": 0.34}[kind]))      # v8.2 reaction sounds
    return out

def ripple_remap(t, cuts):
    """New time of original time t after the given removable cuts ([{start,end}], non-overlapping) are applied. Inside a cut -> collapses to its start."""
    shift = 0.0
    for c in sorted(cuts, key=lambda c: c["start"]):
        if t >= c["end"]: shift += c["end"] - c["start"]
        elif t > c["start"]: shift += t - c["start"]
    return round(t - shift, 4)

def apply_to_timeline(tl, cuts):
    """Return a copy of the narration timeline with the cuts ripple-applied (captions/shots are regenerated from this). Refuses to clip speech."""
    spans = _wordspans(tl)
    for c in cuts:
        if overlaps_speech(c["start"], c["end"], spans, pad=0.0): raise ValueError(f"cut {c.get('cut_id', '?')} would remove speech")
    new = json.loads(json.dumps(tl)); total = sum(c["end"] - c["start"] for c in cuts)
    for u in new["units"]:
        u["start"], u["end"] = ripple_remap(u["start"], cuts), ripple_remap(u["end"], cuts)
        for w in u.get("words", []): w["s"], w["e"] = ripple_remap(w["s"], cuts), ripple_remap(w["e"], cuts)
    new["duration"] = round(tl.get("duration", 0) - total, 3)
    return new

def keep_segments(duration, cuts):
    """The EDL if every given removable cut were accepted: [(start, end)] of material that stays."""
    out, pos = [], 0.0
    for c in sorted(cuts, key=lambda c: c["start"]):
        if c["start"] > pos: out.append((round(pos, 3), round(c["start"], 3)))
        pos = max(pos, c["end"])
    if duration > pos: out.append((round(pos, 3), round(duration, 3)))
    return out

# ---------------- detection ----------------
def _norm(w): return re.sub(r"[^a-z0-9']", "", str(w).lower())
_OK_REPEAT = {"had", "that", "very", "ha", "no", "so", "bye", "knock", "far", "long", "again", "more", "many", "ever", "little", "one"}

def detect_repeats(tl):
    """Adjacent identical words inside one spoken unit (a classic stumble signal). Needs word timings. Low confidence on purpose."""
    out = []
    for u in tl.get("units", []):
        ws = [w for w in (u.get("words") or []) if _norm(w.get("w"))]
        for a, b in zip(ws, ws[1:]):
            if _norm(a["w"]) == _norm(b["w"]) and float(b["s"]) - float(a["e"]) < 0.5:
                out.append({"start": float(a["s"]), "end": float(b["e"]), "word": _norm(a["w"]), "common_phrase": _norm(a["w"]) in _OK_REPEAT})
    return out

def detect_pacing_lags(tl, min_words=6, ratio=0.6):
    """Spoken units whose words-per-second is far below the episode median (slow, dragging delivery)."""
    rates = []
    for u in tl.get("units", []):
        n = len(str(u.get("text", "")).split()); d = float(u["end"]) - float(u["start"])
        if n >= min_words and d > 0: rates.append((u, n / d))
    if len(rates) < 8: return []
    med = statistics.median(r for _, r in rates); out = []
    for u, r in rates:
        if r < med * ratio: out.append({"start": float(u["start"]), "end": float(u["end"]), "rate": round(r, 2), "median": round(med, 2)})
    return out

def scan_video(path, fps=30):
    """Optional ffmpeg scan for frozen picture (>=4 s) and black frames (>=1.5 s). Returns [{kind,start,end}]. Never raises."""
    out = []
    def run(vf):
        return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", vf, "-f", "null", "-"], capture_output=True, text=True, timeout=1800).stderr
    try:
        e = run("scale=320:-2,freezedetect=n=0.001:d=4")
        starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", e)]; durs = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", e)]
        for s, d in zip(starts, durs): out.append({"kind": "frozen_picture", "start": s, "end": s + d})
        e = run("scale=320:-2,blackdetect=d=1.5:pix_th=0.06")
        for s, en in re.findall(r"black_start:([\d.]+)\s+black_end:([\d.]+)", e): out.append({"kind": "black_frames", "start": float(s), "end": float(en)})
    except Exception as ex: log(f"video scan skipped: {scrub(ex)}", "WARN")
    return out

# ---------------- the map ----------------
def _unit_at(units, t, before=True):
    if before:
        c = [i for i, u in enumerate(units) if float(u["end"]) <= t + 1e-6]; return c[-1] if c else None
    c = [i for i, u in enumerate(units) if float(u["start"]) >= t - 1e-6]; return c[0] if c else None

def _conf(base, sync_ok, audio_ok):
    c = base * (1.0 if sync_ok else 0.6) * (1.0 if audio_ok else 0.85)
    return round(max(0.05, min(0.95, c)), 2)

def build_cutmap(wav_path=None, timeline=None, video_path=None, fps=30, events=(), episode="", master_duration=None, now=None, holds=None):
    """Return the cut-map dict. Missing/odd inputs become 'limitations', not exceptions."""
    min_gap = S("CUTMAP_MIN_GAP_SEC", float); long_p = S("CUTMAP_LONG_PAUSE_SEC", float); keep = S("CUTMAP_KEEP_PAUSE_SEC", float)
    tl = timeline if (timeline and timeline.get("units")) else None
    m = {"schema": SCHEMA, "episode_id": episode, "created": iso(now), "fps": fps, "method": "", "estimate": True, "cuts": [], "preserved": [],
         "limitations": [], "params": {"min_gap_sec": min_gap, "long_pause_sec": long_p, "keep_pause_sec": keep},
         "inputs": {"narration_audio": bool(wav_path), "word_timeline": bool(tl), "word_level": has_word_timing(tl) if tl else False, "video": bool(video_path)},
         "apply_policy": "REVIEW ONLY. No cut is applied automatically. Accepted cuts must be applied identically to picture, narration, captions, sound effects and music.",
         "sync_check": {}, "summary": {}}
    audio = None
    if wav_path and os.path.exists(wav_path):
        try: audio = analyse_audio(wav_path, min_gap)
        except Exception as e: m["limitations"].append("Audio could not be analysed: " + scrub(str(e))[:120])
    elif wav_path: m["limitations"].append("Narration audio file not found; audio checks skipped.")
    if not tl and not audio:
        m["method"] = "none"; m["limitations"].append("Neither a narration timeline nor readable audio was available: no cut map could be produced."); return _finish(m, [], tl, fps)
    durs = {"timeline": tl.get("duration") if tl else None, "audio": audio["duration"] if audio else None, "video": master_duration}
    known = [v for v in durs.values() if v]
    sync_ok = (max(known) - min(known) <= 0.25) if len(known) > 1 else True
    m["sync_check"] = {"durations": durs, "tolerance_sec": 0.25, "ok": sync_ok}
    if not sync_ok: m["limitations"].append(f"Narration/timeline/video lengths differ by {max(known)-min(known):.2f}s: timestamps may not line up with the video; confidence reduced.")
    m["method"] = "timeline+audio" if (tl and audio) else ("timeline" if tl else "audio_only")
    m["estimate"] = tl is None
    if m["estimate"]: m["limitations"].append("ESTIMATE: no word timing or transcript available; results come from audio loudness only, so intentional pauses cannot be told from dead air.")
    if tl and not m["inputs"]["word_level"]: m["limitations"].append("Timeline has sentence timing only: repeated-word and slow-word checks were not run.")
    m["limitations"].append("Vocal stumbles cannot be detected reliably. Only measurable signals are reported: repeated adjacent words and unusually slow delivery (needs word timing).")
    spans = _wordspans(tl) if tl else []
    units = tl["units"] if tl else []
    sil = audio["silences"] if audio else []
    sfx = sfx_spans(events)
    cuts, preserved = [], []

    def add(kind, a, b, reason, base_conf, removable, action, method, extra=None, snap=True):
        if b - a <= 0: return
        rng = snap_inward(a, b, fps) if (removable and snap) else (round(a, 3), round(b, 3))
        if rng is None: return
        a2, b2 = rng
        if removable and tl and overlaps_speech(a2, b2, spans):
            action = "review"; removable = False; reason += " (not removable: overlaps spoken words)"; base_conf = min(base_conf, 0.2)
        hit = [(k, round(s, 2), round(e, 2)) for k, s, e in sfx if s < b2 and e > a2]
        if hit and removable:
            action = "review"; base_conf = min(base_conf, 0.3); reason += " (a sound effect sits inside this range: it must be moved/re-cut together with the pause)"
        ui, uj = _unit_at(units, a2, True), _unit_at(units, b2, False)
        shot_cross = bool(units) and removable and any(a2 < float(u["start"]) < b2 for u in units)
        c = {"kind": kind, "start": round(a2, 3), "end": round(b2, 3), "duration": round(b2 - a2, 3), "start_tc": tc(a2), "end_tc": tc(b2), "action": action,
             "removable": bool(removable), "confidence": _conf(base_conf, sync_ok, audio is not None), "reason": reason, "method": method, "estimate": m["estimate"],
             "review_status": "pending", "context": {"text_before": (units[ui]["text"][-70:] if ui is not None else ""), "text_after": (units[uj]["text"][:70] if uj is not None else "")}}
        if removable:
            c["ripple"] = {"shift_later_content_by_sec": round(b2 - a2, 3), "start_frame": int(round(a2 * fps)), "end_frame": int(round(b2 * fps)),
                           "crosses_shot_boundary": shot_cross, "sfx_inside": hit,
                           "captions_after": sum(1 for s, _ in spans if s >= b2) if spans else None,
                           "note": "Remove the same range from picture, narration, music bed and sfx; shift later captions/shots/effects earlier by the duration."}
        if extra: c.update(extra)
        cuts.append(c)

    if tl:
        # 1. gaps between spoken units, using the planned-pause metadata written by voice.py
        for i in range(1, len(units)):
            e0, s1 = float(units[i - 1]["end"]), float(units[i]["start"]); d = s1 - e0
            if d < min_gap: continue
            reasons = list(units[i - 1].get("pause_after_reasons", [])) + list(units[i].get("pause_before_reasons", []))
            explicit = "explicit_pause" in reasons
            cov = (silence_overlap(sil, e0, s1) / d) if audio else None
            # A pause the writer asked for ([pause:long] = 1.6 s, plus tag padding and natural gaps) gets the benefit of the doubt:
            # it is only called "unusually long" when it exceeds the threshold by one more full long pause.
            limit = long_p + (LONG_PLANNED_PAUSE if explicit else 0.0)
            if reasons and d <= limit:
                preserved.append({"start": round(e0, 3), "end": round(s1, 3), "duration": round(d, 3), "reason": "intentional pause kept: " + ", ".join(sorted(set(reasons)))})
                continue
            if reasons:   # intentional but unusually long
                leave = LONG_PLANNED_PAUSE if explicit else max(keep, 1.0)
                core = silent_core(sil, e0, s1) if audio else (e0, s1)
                a = (core[0] if core else e0) + leave / 2; b = (core[1] if core else s1) - leave / 2
                add("long_pause", a, b, f"Planned pause is unusually long ({d:.2f}s > {limit:.1f}s; reasons: {', '.join(sorted(set(reasons)))}). Review: trim to about {leave:.1f}s if it drags.",
                    0.35 if explicit else 0.5, True, "review", m["method"], {"gap_total_sec": round(d, 3), "planned": True})
                continue
            if audio and cov is not None and cov < 0.5:
                add("dead_air", e0, s1, f"Gap of {d:.2f}s between lines but the audio is not silent there (coverage {cov:.0%}); possible noise or breath. Review only.", 0.3, False, "review", m["method"])
                continue
            core = silent_core(sil, e0, s1, 0.0) if audio else (e0, s1)
            if not core: continue
            a, b = core[0] + keep / 2, core[1] - keep / 2
            add("dead_air", a, b, f"Silence of {d:.2f}s between lines with no planned pause behind it; leaves a {keep:.2f}s natural pause.",
                0.85 if audio else 0.6, True, "trim_suggested", m["method"], {"gap_total_sec": round(d, 3), "planned": False})
        # 2. silence INSIDE a spoken unit (only the audio can see this)
        if audio:
            gaps = [(float(units[i - 1]["end"]) - 0.05, float(units[i]["start"]) + 0.05) for i in range(1, len(units))]
            for s, e in sil:
                if e - s < min_gap: continue
                if any(g0 <= s + 0.2 and g1 >= e - 0.2 for g0, g1 in gaps) or e <= 1.0 or s >= audio["duration"] - 1.0: continue
                inside = [u for u in units if float(u["start"]) < (s + e) / 2 < float(u["end"])]
                if not inside: continue
                add("dead_air", s + keep / 2, e - keep / 2, f"Silence of {e - s:.2f}s inside a spoken line (no planned pause); leaves a {keep:.2f}s natural pause.", 0.7, True, "trim_suggested", m["method"], {"inside_line": True})
        # 3. pacing + stumble signals
        for lag in detect_pacing_lags(tl):
            add("pacing_lag", lag["start"], lag["end"], f"Delivery is slow: {lag['rate']} words/s vs episode median {lag['median']} words/s. Review the line; do not cut.", 0.4, False, "review", m["method"], snap=False)
        if m["inputs"]["word_level"]:
            for r in detect_repeats(tl):
                add("possible_stumble", r["start"], r["end"], f"Word '{r['word']}' repeated back to back" + (" (can be normal phrasing)" if r["common_phrase"] else "") + ". Listen to confirm; this is a weak stumble signal.",
                    0.3 if r["common_phrase"] else 0.55, False, "review", m["method"], snap=False)
    elif audio:
        # audio-only fallback: every long silence is a review item and an ESTIMATE
        d_total = audio["duration"]
        for s, e in audio["silences"]:
            d = e - s
            if d < min_gap: continue
            kind = "head_tail_silence" if (s <= 0.05 or e >= d_total - 0.05) else ("long_pause" if d > long_p else "dead_air")
            base = 0.4 if d < 1.5 else (0.55 if d < long_p else 0.65)
            leave = keep if kind != "long_pause" else LONG_PLANNED_PAUSE
            add(kind, s + leave / 2, e - leave / 2, f"Silence of {d:.2f}s (estimate from loudness only; could be an intentional dramatic pause). Review before cutting.", base, True, "review", "audio_only_estimate", {"gap_total_sec": round(d, 3)})
    # 4. optional video scan
    if video_path and os.path.exists(video_path) and S("CUTMAP_VIDEO_SCAN", bool):
        for v in scan_video(video_path, fps):
            add(v["kind"], v["start"], v["end"], f"{v['kind'].replace('_', ' ').capitalize()} for {v['end'] - v['start']:.1f}s in the rendered video. Review; fix in the picture, not by cutting audio.", 0.7, False, "review", "video_scan", snap=False)
    elif video_path and not S("CUTMAP_VIDEO_SCAN", bool): m["limitations"].append("Video scan switched off (CUTMAP_VIDEO_SCAN = FALSE): frozen/black picture not checked.")
    # 5. v9.3: still picture states held too long (from the real render's segment list; review only, nothing is cut)
    if holds:
        mx = S("CUTMAP_MAX_HOLD_SEC", float); hs = [(float(a), float(b)) for a, b in holds if float(b) > float(a)]
        over = [(a, b) for a, b in hs if mx > 0 and b - a > mx + 1e-6]
        for a, b in over[:60]:
            add("static_hold", a, b, f"One still picture state for {b - a:.1f}s (limit {mx:.1f}s) reads as a slideshow. Review the shot (MICRO_CUTS_ON splits stills by itself).",
                0.5, False, "review", "segment_plan", snap=False)
        if hs:
            ds = sorted(b - a for a, b in hs)
            m["pacing"] = {"picture_states": len(hs), "median_hold_sec": round(statistics.median(ds), 2), "max_hold_sec": round(ds[-1], 2), "over_limit": len(over), "limit_sec": mx}
    m["limitations"].append("Music and sound effects are not analysed. The score is a continuous bed made for the full length and must be trimmed/regenerated after any accepted cut; effects inside a cut are flagged.")
    cuts.sort(key=lambda c: c["start"])
    cuts = cuts[:200]
    keepers = []
    for c in cuts:   # overlapping removable suggestions: keep the more confident one
        if keepers and c["removable"] and keepers[-1]["removable"] and c["start"] < keepers[-1]["end"]:
            if c["confidence"] > keepers[-1]["confidence"]: keepers[-1] = c
            continue
        keepers.append(c)
    return _finish(m, keepers, tl, fps, preserved)

def _finish(m, cuts, tl, fps, preserved=()):
    for i, c in enumerate(cuts, 1): c["cut_id"] = f"C{i:03d}"
    m["cuts"] = cuts; m["preserved"] = list(preserved)[:200]
    rem = [c for c in cuts if c["removable"] and c["action"] == "trim_suggested"]
    dur = (tl or {}).get("duration") or (m.get("sync_check", {}).get("durations", {}) or {}).get("audio") or 0
    m["edl_if_suggested_trims_accepted"] = keep_segments(dur, rem) if dur else []
    m["summary"] = {"cuts": len(cuts), "trim_suggested": len(rem), "review_only": len(cuts) - len(rem),
                    "suggested_trim_total_sec": round(sum(c["duration"] for c in rem), 2), "preserved_pauses": len(m["preserved"]), "by_kind": {}}
    for c in cuts: m["summary"]["by_kind"][c["kind"]] = m["summary"]["by_kind"].get(c["kind"], 0) + 1
    return m

# ---------------- output ----------------
def sheet_rows(m):
    return [{"episode_id": m["episode_id"], "cut_id": c["cut_id"], "start": c["start"], "end": c["end"], "duration": c["duration"], "kind": c["kind"], "action": c["action"],
             "confidence": c["confidence"], "reason": c["reason"][:400], "method": c["method"] + (" (estimate)" if c.get("estimate") else ""), "review_status": c["review_status"]} for c in m["cuts"]]

def to_markdown(m):
    L = [f"# Cut map - {m['episode_id']}", f"Created {m['created']} | method: **{m['method']}**" + (" | **ESTIMATE**" if m["estimate"] else ""), "", f"**{m['apply_policy']}**", ""]
    s = m["summary"]
    L += [f"- {s.get('cuts', 0)} item(s): {s.get('trim_suggested', 0)} suggested trim(s) totalling {s.get('suggested_trim_total_sec', 0)} s, {s.get('review_only', 0)} review-only; {s.get('preserved_pauses', 0)} intentional pause(s) preserved.",
          f"- Sync check: {json.dumps(m['sync_check'].get('durations', {}))} - {'OK' if m['sync_check'].get('ok', True) else 'MISMATCH'}", ""]
    if m.get("pacing"):
        p_ = m["pacing"]; L.insert(len(L) - 1, f"- Pacing (v9.3): {p_['picture_states']} still picture states, median {p_['median_hold_sec']} s, longest {p_['max_hold_sec']} s, {p_['over_limit']} over {p_['limit_sec']} s.")
    if m["limitations"]: L += ["## Limitations"] + [f"- {x}" for x in m["limitations"]] + [""]
    L += ["## Items", "| id | start | end | dur (s) | kind | action | confidence | reason |", "|---|---|---|---|---|---|---|---|"]
    for c in m["cuts"]: L.append(f"| {c['cut_id']} | {c['start_tc']} | {c['end_tc']} | {c['duration']} | {c['kind']} | {c['action']} | {c['confidence']} | {c['reason']} |")
    if not m["cuts"]: L.append("| - | - | - | - | none found | - | - | nothing above the thresholds |")
    L += ["", "## How to apply an accepted cut without breaking sync",
          "1. Remove the range from the narration, the picture, the music bed and any sound effect at the same time stamps (frame numbers are in the JSON `ripple` block).",
          "2. Move every later caption, shot boundary and effect earlier by the cut length (`whatifs.cutmap.apply_to_timeline` does this for the narration timeline).",
          "3. Re-run captions from the shifted timeline. Do not cut anything marked 'overlaps spoken words' or containing a sound effect without moving the effect."]
    return "\n".join(L) + "\n"

def save(m, out_dir):
    """cutmap.json + cutmap.md + Cut_Map tab. Never raises."""
    paths = []
    try:
        os.makedirs(out_dir, exist_ok=True)
        p = os.path.join(out_dir, "cutmap.json"); json.dump(m, open(p, "w", encoding="utf-8"), indent=1); paths.append(p)
        p = os.path.join(out_dir, "cutmap.md"); open(p, "w", encoding="utf-8").write(to_markdown(m)); paths.append(p)
    except Exception as e: log(f"could not write cut map files: {scrub(e)}", "WARN")
    safe_append("Cut_Map", sheet_rows(m)); return paths

def run_cutmap(out_dir, wav_path, timeline, video_path=None, fps=30, events=(), episode="", master_duration=None, holds=None):
    """Stage entry for episode.py. `timeline` is the dict or a path to *_timeline.json. Returns (map|None, paths). NEVER raises."""
    if not S("CUTMAP_ON", bool): return None, []
    try:
        if isinstance(timeline, str) and os.path.exists(timeline): timeline = json.load(open(timeline, encoding="utf-8"))
        elif isinstance(timeline, str): timeline = None
        m = build_cutmap(wav_path, timeline, video_path, fps, events, episode, master_duration, holds=holds)
        paths = save(m, out_dir); s = m["summary"]
        log(f"cut map: {s.get('cuts', 0)} item(s), {s.get('trim_suggested', 0)} suggested trim(s) ({s.get('suggested_trim_total_sec', 0)} s), method {m['method']}"
            + (f", median still hold {m['pacing']['median_hold_sec']} s" if m.get("pacing") else ""), episode=episode)
        return m, paths
    except Exception as e:
        log(f"cut map skipped: {scrub(e)}", "WARN", episode); return None, []

def main(folder):
    """python -m whatifs.cli cutmap <episode folder>  - re-run on saved files (voice.wav, voice_timeline.json, master.mp4)."""
    from whatifs.render import fps as _fps, probe_dur
    wav = os.path.join(folder, "voice.wav"); tlp = os.path.join(folder, "voice_timeline.json"); vid = os.path.join(folder, "master.mp4")
    m, paths = run_cutmap(folder, wav, tlp, vid if os.path.exists(vid) else None, _fps(), (), os.path.basename(os.path.normpath(folder)), probe_dur(vid) if os.path.exists(vid) else None)
    if m: print(to_markdown(m))
    return m

