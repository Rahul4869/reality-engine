"""whatifs/reels.py v8.5 - 9:16 reels from the long video's own shots: cover frame first, new order, re-voiced lines, burned captions. 1080x1920.
REEL_STYLE bridge (default): one payoff given, the bigger question left open, an invite to the full video, then the follow/share ask.
standalone: a complete loopable mini-story (no fade). teaser: v8.4 (cut on the question, end card)."""
from __future__ import annotations
import os, re, subprocess
from whatifs.core import SMALL, S
from whatifs.voice import narrate
from whatifs.render import score, write_mix, fps as _fps

def _vsize(): return (360, 640) if SMALL else (1080, 1920)

def _ass(timeline, path, hook_text, W, H):
    fs = int(H * 0.042); hs = int(H * 0.05)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Anton,{fs},&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,{max(2,fs//9)},2,2,60,60,{int(H * (S("REEL_CAPTION_MARGIN_PCT", float) if S("KINETIC_CAPTIONS_ON", bool) else 0.30))},1
Style: Hook,Anton,{hs},&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,{max(3,hs//8)},3,8,60,60,{int(H*0.12)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def ts(t): h, m = int(t // 3600), int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
    ev = [f"Dialogue: 1,{ts(0)},{ts(2.6)},Hook,,0,0,0,,{hook_text.upper()}"]
    for u in timeline["units"]:
        ws = u.get("words") or []
        if not ws:
            parts = u["text"].split(); d = (u["end"] - u["start"]) / max(1, len(parts))
            ws = [{"w": p, "s": u["start"] + i * d, "e": u["start"] + (i + 1) * d} for i, p in enumerate(parts)]
        for i in range(0, len(ws), 3):
            g = ws[i:i + 3]
            if not S("KINETIC_CAPTIONS_ON", bool):
                ev.append(f"Dialogue: 0,{ts(g[0]['s'])},{ts(g[-1]['e'])},Cap,,0,0,0,,{' '.join(x['w'] for x in g).upper()}"); continue
            for j, cur in enumerate(g):                        # v10 (G2, K135): kinetic captions: the spoken word lights up; numbers and YOU pop
                end = g[j + 1]["s"] if j + 1 < len(g) else cur["e"]
                parts = []
                for k, x in enumerate(g):
                    w = str(x["w"]).upper()
                    if k == j:
                        pop = any(c.isdigit() for c in w) or w.strip(".,!?") in ("YOU", "YOUR", "YOURS")
                        parts.append("{\\c&H0000D7FF&" + ("\\fscx112\\fscy112" if pop else "") + "}" + w + "{\\r}")
                    else: parts.append(w)
                ev.append(f"Dialogue: 0,{ts(cur['s'])},{ts(max(end, cur['s'] + 0.05))},Cap,,0,0,0,," + " ".join(parts))
    open(path, "w").write(head + "\n".join(ev) + "\n"); return path

def _label_lines(lines, speaker_blends):
    """v8.3: in the two-role format every reel line is spoken by the Director or the Curious One (an unlabelled line used to be a third voice)."""
    if not speaker_blends: return list(lines)
    from whatifs.voice import _peel
    out = []
    for l in lines:
        spk, _, _, text = _peel(str(l))
        out.append(l if (spk or not text) else "[DIRECTOR] " + str(l))
    return out

def reel_style():
    from whatifs.core import S
    mode = str(S("REEL_STYLE")).strip().lower()
    return mode if mode in ("bridge", "standalone", "teaser") else "bridge"

def reel_lines(k, plan, seed, speaker_blends=None, mode=None):
    """v8.5: the spoken lines of reel k for the reel style. bridge (default) / teaser: lines, the invite to the full video, then the follow/share ask (v8.3 order).
    standalone: lines, the ask, then a loop line that flows back into line 1 (never a 'full video' line)."""
    from whatifs.core import S
    mode = mode or reel_style(); ask = None
    try:
        if S("CTA_ON", bool):                                    # v8.3: a witty follow (odd reels) or share (even reels) ask
            from whatifs import cta as _CTA
            spk, tag, txt = _CTA.reel_ask(seed, k)
            ask = f"[{spk}] [{tag}] {txt}" if speaker_blends else f"[{tag}] {txt}"
    except Exception: pass
    end = str(plan.get("end_line") or "").strip()
    if mode == "standalone":
        if re.search(r"full video|our channel|link in|part 2", end, re.I): end = ""
        return _label_lines(list(plan["lines"]) + ([ask] if ask else []) + (["[tension] " + end] if end else []), speaker_blends)
    if mode == "bridge" and end and not re.search(r"full|channel|simulation|episode|video", end, re.I): end = end.rstrip(". ") + ". Full video on our channel."
    return _label_lines(list(plan["lines"]) + ["[pause:short]", "[reveal] " + (end or "Full video on our channel.")], speaker_blends) + ([ask] if ask else [])

def build_reel(k, plan, shot_files, cover, blend, style, out_dir, fonts_dir="fonts", speaker_blends=None):
    W, H = _vsize(); os.makedirs(out_dir, exist_ok=True)
    mode = reel_style(); loop = mode == "standalone"             # v8.5: only a standalone reel loops (no fade at the end)
    body_lines = reel_lines(k, plan, os.path.basename(out_dir.rstrip("/")), speaker_blends, mode)
    lines = "\n".join(body_lines)
    vo = narrate(lines, blend, os.path.join(out_dir, f"reel{k}_vo"), style=style, seed=f"{os.path.basename(out_dir.rstrip(chr(47)))}|reel{k}", speaker_blends=speaker_blends)
    import json
    tl = json.load(open(vo.timeline_path)); dur = vo.duration + 0.4
    cov_t = 0.8 if mode == "teaser" else 0.4          # v8.5: the hook picture arrives sooner (Instagram gets the cover separately)
    segs = []; per = max(1.6, (dur - cov_t) / max(1, len(plan["shots"])))
    F = _fps()
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={F},format=yuv420p"
    c0 = os.path.join(out_dir, f"r{k}_c.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", cover, "-t", f"{cov_t}", "-vf",
                    f"scale={W*1.08:.0f}:-2,zoompan=z='1+0.0015*on':d=1:s={W}x{H}:fps={F},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-video_track_timescale", "15360", c0], check=True)
    segs.append(c0)
    for j, i in enumerate(plan["shots"]):
        src = shot_files[i]; o = os.path.join(out_dir, f"r{k}_{j}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", f"{per:.2f}", "-vf", vf + ",tpad=stop_mode=clone:stop_duration=3", "-t", f"{per:.2f}",
                        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-video_track_timescale", "15360", o], check=True)
        segs.append(o)
    lst = os.path.join(out_dir, f"r{k}.txt"); open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    body = os.path.join(out_dir, f"r{k}_body.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", body], check=True)
    ass = _ass(tl, os.path.join(out_dir, f"r{k}.ass"), plan.get("hook_text", ""), W, H)
    mix = score(dur, f"{os.path.basename(out_dir.rstrip(chr(47)))}reel{k}", [("riser", max(0.5, dur - 1.6)), ("boom", 0.05)], vo.wav_path, bed_db=-20)
    aud = write_mix(mix, os.path.join(out_dir, f"r{k}_mix.wav"), lufs=-13)
    out = os.path.join(out_dir, f"reel{k}.mp4")
    fd = os.path.abspath(fonts_dir) if os.path.isdir(fonts_dir) else "/usr/share/fonts"
    end_fade = "null" if loop else f"fade=t=out:st={max(0.1, dur - 0.35):.2f}:d=0.35"      # a loop must not fade to black (it would break the restart)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", body, "-i", aud, "-filter_complex",
                    f"[0:v]tpad=stop_mode=clone:stop_duration=5,trim=duration={dur:.2f},ass={ass}:fontsdir={fd},{end_fade}[v]",
                    "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "256k",
                    "-t", f"{dur:.2f}", "-movflags", "+faststart", out], check=True)
    return out, dur

