"""whatifs/qc.py v8.3 - quality checks before anything goes public. Any FAIL stops upload of that file (fail-safe, logged)."""
from __future__ import annotations
import subprocess, re, json
from whatifs.render import probe_dur

BLACKDETECT = "blackdetect=d=2.5:pix_th=0.05:pic_th=0.9999"      # v8.3: a frame is black only if ~every pixel is dark; a starfield or a dark scene with a few hundred lit pixels is a picture, not a black screen
FREEZEDETECT = "freezedetect=n=0.001:d=9"
def _ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args + ["-f", "null", "-"], capture_output=True, text=True).stderr

def check_video(path, expect_sec, tol=1.5, vertical=False):
    res = {}
    d = probe_dur(path); res["duration"] = (abs(d - expect_sec) <= tol, round(d, 2))
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate", "-of", "json", path], capture_output=True, text=True)
    st = json.loads(p.stdout or "{}").get("streams", [])
    v = next((s for s in st if s["codec_type"] == "video"), {}); a = next((s for s in st if s["codec_type"] == "audio"), {})
    res["has_audio"] = (bool(a), a.get("sample_rate")); res["has_video"] = (bool(v), f'{v.get("width")}x{v.get("height")}')
    res["orientation"] = ((v.get("height", 0) > v.get("width", 0)) == vertical, "")
    e = _ff(["-i", path, "-af", "ebur128=peak=true", "-vn"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); lufs = float(m[-1]) if m else -99
    res["loudness"] = (-17.5 <= lufs <= -11.5, lufs)
    pk = re.findall(r"Peak:\s+(-?[\d.]+)\s+dBFS", e); res["true_peak"] = (float(pk[-1]) <= -0.5 if pk else True, float(pk[-1]) if pk else None)    # v8.2: no clipping
    e = _ff(["-i", path, "-vf", BLACKDETECT, "-an"])
    blacks = re.findall(r"black_duration:([\d.]+)", e); res["no_long_black"] = (not blacks, blacks[:3])
    e = _ff(["-i", path, "-af", "silencedetect=n=-50dB:d=4", "-vn"])
    sil = re.findall(r"silence_duration: ([\d.]+)", e); res["no_long_silence"] = (not sil, sil[:3])
    e = _ff(["-i", path, "-vf", FREEZEDETECT, "-an"])
    fr = re.findall(r"freeze_duration: ([\d.]+)", e); res["no_frozen_picture"] = (not fr, fr[:3])
    ok = all(v[0] for v in res.values())
    return ok, res

def check_thumb(path, phone_score):
    import os
    ok = os.path.exists(path) and os.path.getsize(path) < 2_000_000 and phone_score > 38
    return ok, {"size": os.path.getsize(path) if os.path.exists(path) else 0, "phone_contrast": round(phone_score, 1)}


# =====================================================================================================================================
# v8.2: render QC. Every check is cheap and independent of the code that built the video (it measures the FINISHED file against the narration
# clock). full_check() returns problems with a fix class: 'free' (code can repair it), 'paid' (needs a few rupees of re-made images/clips), 'none'.
# =====================================================================================================================================
import os, base64
import numpy as np

def problem(code, detail, fix="none", t=None, idx=None):
    return {"code": code, "detail": str(detail)[:200], "fix": fix, "t": t, "idx": idx}

def _probe_json(args):
    p = subprocess.run(["ffprobe", "-v", "error", "-of", "json"] + args, capture_output=True, text=True)
    try: return json.loads(p.stdout or "{}")
    except Exception: return {}

def packet_check(path, expect_sec, fps, tol_frames=3):
    """Frame count straight from the container (no decoding) against the narration clock, and constant frame rate."""
    j = _probe_json(["-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets,r_frame_rate,avg_frame_rate", path])
    st = (j.get("streams") or [{}])[0]
    try: n = int(st.get("nb_read_packets"))
    except (TypeError, ValueError): return []
    want = round(expect_sec * fps); out = []
    if abs(n - want) > tol_frames: out.append(problem("frame_count", f"{n} frames in the file, the narration clock needs {want} (+-{tol_frames})", "free"))
    if st.get("r_frame_rate") and st.get("avg_frame_rate") and st["r_frame_rate"] != st["avg_frame_rate"]:
        out.append(problem("frame_count", f"variable frame rate ({st['r_frame_rate']} vs {st['avg_frame_rate']})", "free"))
    return out

def _decode_env(path, sr=4000):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.float32)
    k = max(1, sr // 100)                                    # 100 envelope points per second
    n = len(a) // k; return np.abs(a[: n * k]).reshape(n, k).mean(1)

def audio_offsets(narration_wav, master, windows=3, win_sec=30.0, max_lag=0.8):
    """How far the narration inside the finished file sits from the narration clock, measured at the start, middle and end. Returns [(t, offset_sec, quality)].
    Positive offset = the audio in the file is LATE. Inconclusive windows (quality < 0.25) are returned with quality only; they never fail a video."""
    try: a, b = _decode_env(narration_wav), _decode_env(master)
    except Exception: return []
    n = min(len(a), len(b)); out = []
    if n < 1500: return out
    L = int(win_sec * 100); lag = int(max_lag * 100)
    for t0 in sorted({int(n * f) for f in np.linspace(0.08, 0.80, windows)}):
        x = a[t0: t0 + L]; y = b[max(0, t0 - lag): t0 + L + lag]
        if len(x) < 400 or x.std() < 1e-6 or y.std() < 1e-6: continue
        x = (x - x.mean()) / (x.std() + 1e-9); best, off = -1.0, 0
        for d in range(-lag, lag + 1, 2):
            s = (t0 + d) - max(0, t0 - lag)
            if s < 0 or s + len(x) > len(y): continue
            seg = y[s: s + len(x)]
            if seg.std() < 1e-9: continue
            c = float(np.dot(x, (seg - seg.mean()) / (seg.std() + 1e-9)) / len(x))
            if c > best: best, off = c, d
        out.append((round(t0 / 100.0, 1), round(off / 100.0, 2), round(best, 2)))
    return out

def srt_check(path, timeline, duration):
    """Captions: ordered, inside the video, readable length, and every spoken word is in them."""
    try: txt = open(path, encoding="utf-8").read()
    except OSError: return [problem("captions", "caption file missing", "free")]
    cues = re.findall(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)\n(.*?)(?:\n\n|\Z)", txt, re.S)
    if not cues: return [problem("captions", "no caption cues", "free")]
    t = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    prev_end, prev_start, bad, words = -1.0, -1.0, [], 0
    for c in cues:
        a, b = t(*c[:4]), t(*c[4:8]); words += len(c[8].split())
        if b <= a or a < prev_start - 1e-3 or a < prev_end - 0.06 or b > duration + 0.6 or (b - a) > 9.0: bad.append(f"{a:.1f}s")
        prev_end, prev_start = b, a
    want = sum(len((u.get("text") or "").split()) for u in timeline.get("units", []))
    out = []
    if bad: out.append(problem("captions", f"out-of-order, overlapping or too long cues near {', '.join(bad[:4])}", "free"))
    if want and words < 0.97 * want: out.append(problem("captions", f"captions hold {words} of {want} spoken words", "free"))
    return out

def reuse_runs(shots, own):
    """Longest run of consecutive shots that show the same underlying picture. own = set of shot indexes that have their own fresh image or clip."""
    best = run = 0
    for i, s in enumerate(shots):
        if i in own or s["type"] in ("stock", "graphic", "living", "kling"): run = 0 if (i in own or s["type"] != "still") else run + 1; continue
        run += 1; best = max(best, run)
    return best

def vision_check(master, units, shots, episode="", n=None):
    """Independent Gemini Flash look at ~12 evenly spaced frames. v8.3: a judge that cannot be reached is a PROBLEM ('vision_unavailable') while QC_VISION_REQUIRED is TRUE, so the video is held rather than passed unchecked."""
    from whatifs.core import S
    if not S("QC_VISION_ON", bool): return [], {"vision": "off"}
    from whatifs.models import ask_vision
    n = n or S("QC_VISION_FRAMES", int); dur = probe_dur(master)
    if not units or dur <= 0: return [], {"vision": "no frames"}
    kl = [i for i, s in enumerate(shots) if s.get("type") == "kling" and i < len(units)][:3]       # v8.3: every Kling clip (the expensive, most glitch-prone shots) is always looked at
    n_even = max(6, n - len(kl))
    idx = sorted({min(len(units) - 1, int(len(units) * (k + 0.5) / n_even)) for k in range(n_even)} | set(kl)); imgs, lines = [], []
    tmp = master + ".qc"; os.makedirs(tmp, exist_ok=True)
    for k, i in enumerate(idx):
        t = (units[i]["start"] + units[i]["end"]) / 2
        if i in kl: t = units[i]["start"] + min(2.0, (units[i]["end"] - units[i]["start"]) / 2)
        f = os.path.join(tmp, f"f{k}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", master, "-frames:v", "1", "-vf", "scale=512:-2", "-q:v", "5", f], check=False)
        if os.path.exists(f): imgs.append(("image/jpeg", base64.b64encode(open(f, "rb").read()).decode())); lines.append(f'{len(imgs) - 1}: "{units[i]["text"][:140]}"')
    if not imgs: return [], {"vision": "no frames"}
    sysmsg = ("You are an independent video QC inspector. For each numbered frame you get the narration line spoken at that moment. Rate match 0-10: does the picture "
              "plausibly illustrate or support the line (presenter silhouettes or control-room screens during dialogue are fine when they fit)? Set artifact true ONLY for a clear visual "
              "defect: garbled or misspelled on-screen text, a melted or distorted face or body, an obvious glitch, a stray interface overlay. Judge only what you see. "
              'Return JSON: {"frames":[{"i":0,"match":0,"artifact":false,"note":""}]}')
    r = ask_vision(sysmsg, f"FRAMES: {len(imgs)}\n" + "\n".join(lines), imgs, episode)
    try: shutil_rm(tmp)
    except Exception: pass
    if not r or not isinstance(r.get("frames"), list):
        if S("QC_VISION_REQUIRED", bool):
            return [problem("vision_unavailable", "the independent picture check could not run (judge unreachable); the video is held rather than passed unchecked", "none")], {"vision": "unavailable"}
        return [], {"vision": "unavailable"}
    fr = [x for x in r["frames"] if isinstance(x, dict)]
    miss = [x for x in fr if float(x.get("match", 10) or 0) < 4]; art = [x for x in fr if x.get("artifact")]
    out = []
    if len(miss) >= max(3, int(0.25 * len(imgs))): out.append(problem("vision_mismatch", f"{len(miss)} of {len(imgs)} sampled frames do not fit their line", "paid", idx=[idx[int(x["i"])] for x in miss if str(x.get("i", "")).isdigit() and int(x["i"]) < len(idx)]))
    kart = [x for x in art if str(x.get("i", "")).isdigit() and int(x["i"]) < len(idx) and idx[int(x["i"])] in kl]
    if len(art) >= 2 or kart: out.append(problem("vision_artifact", f"{len(art)} sampled frames show a visible defect", "paid", idx=[idx[int(x["i"])] for x in art if str(x.get("i", "")).isdigit() and int(x["i"]) < len(idx)]))
    return out, {"vision": f"{len(imgs)} frames, {len(miss)} weak match, {len(art)} defects"}

def shutil_rm(path):
    import shutil; shutil.rmtree(path, ignore_errors=True)

def scan_times(path):
    """When the black / frozen stretches are (for the targeted free fix)."""
    e = _ff(["-i", path, "-vf", BLACKDETECT + "," + FREEZEDETECT, "-an"])
    return {"black": [float(x) for x in re.findall(r"black_start:([\d.]+)", e)], "frozen": [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", e)]}

def full_check(c):
    """c: dict with master, duration, fps, wav, srt, timeline, units, shots, own (set of shot indexes with their own picture), delivered {'kling': n},
    kling_min, episode. Returns {'ok', 'problems', 'info'}."""
    from whatifs.core import S
    probs, info = [], {}
    ok0, res = check_video(c["master"], c["duration"], vertical=False, tol=0.4)
    codes = {"duration": "duration_mismatch", "has_audio": "no_audio", "has_video": "no_video", "orientation": "orientation", "loudness": "loudness",
             "true_peak": "true_peak", "no_long_black": "black", "no_long_silence": "silence", "no_frozen_picture": "frozen"}
    fixes = {"duration_mismatch": "free", "loudness": "free", "true_peak": "free", "black": "free", "frozen": "free", "silence": "none", "no_audio": "free"}
    for k, (good, val) in res.items():
        if not good: probs.append(problem(codes.get(k, k), f"{k}: {val}", fixes.get(codes.get(k, k), "none")))
    probs += packet_check(c["master"], c["duration"], c["fps"])
    offs = audio_offsets(c["wav"], c["master"]) if c.get("wav") else []
    tol = S("QC_SYNC_TOL_SEC", float); info["audio_offsets"] = offs
    for t, off, q in offs:
        if q >= 0.25 and abs(off) > tol: probs.append(problem("av_offset", f"narration is {off:+.2f}s from the clock near {t}s (limit {tol}s)", "free", t=t))
    if c.get("srt"): probs += srt_check(c["srt"], c["timeline"], c["duration"])
    kd = (c.get("delivered") or {}).get("kling", 0)
    if kd < c.get("kling_min", 0): probs.append(problem("kling_short", f"{kd} of {c['kling_min']} Kling clips were delivered", "paid"))
    miss = c.get("missing_images") or []
    if miss: probs.append(problem("asset_missing", f"{len(miss)} planned pictures could not be made", "paid", idx=list(miss)))
    run = reuse_runs(c["shots"], c.get("own", set())); info["max_reuse_run"] = run
    if run > S("FREE_SHOT_MAX_RUN", int) + 2: probs.append(problem("reuse_run", f"{run} shots in a row show the same picture", "paid"))
    vp, vi = vision_check(c["master"], c["units"], c["shots"], c.get("episode", "")); probs += vp; info.update(vi)
    return {"ok": not probs, "problems": probs, "info": info}
