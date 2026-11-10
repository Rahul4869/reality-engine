"""Hero-still reels, per-character cinematic grammar and the courtroom composition (code only). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, math, os, subprocess
import numpy as np
import cv2
from whatifs.core import S, log, set_setting, FAKE

TEMPLATES = ("push_glow", "rise_fog", "orbit_embers")
GRAMMAR = {"SKEPTIC": {"tilt": 6.0, "handheld": 2.5, "push": 0.10, "crop": 0.80, "grade": (0.92, 0.95, 1.12), "under": 0.18},
           "DIRECTOR": {"tilt": 0.0, "handheld": 0.0, "push": 0.05, "crop": 0.92, "grade": (1.10, 1.04, 0.90), "under": 0.0},
           "JUDGE": {"tilt": 0.0, "handheld": 0.0, "push": 0.0, "drift": 0.03, "crop": 0.95, "grade": (0.86, 1.00, 1.14), "under": 0.0},
           "WITNESS": {"tilt": 0.0, "handheld": 0.5, "push": 0.02, "crop": 0.9, "grade": (1.0, 0.95, 0.9), "under": 0.1}}

def grammar(speaker):
    """Render parameters for a speaker (BGR grade gains). The Characters tab's 'grammar_json' cell overrides the defaults when it is valid JSON."""
    g = dict(GRAMMAR.get(speaker, GRAMMAR["DIRECTOR"]))
    try:
        from whatifs import show as SHOW
        row = next((c for c in SHOW.characters() if c.get("speaker") == speaker), {})
        over = json.loads(row.get("grammar_json") or "{}")
        if isinstance(over, dict): g.update({k: v for k, v in over.items() if k in g})
    except Exception: pass
    return g

def apply_grammar(img, speaker, t):
    """One portrait / cutaway frame through the character's grammar. Deterministic in t. Never changes the image size."""
    g = grammar(speaker); h, w = img.shape[:2]
    jx = g["handheld"] * (math.sin(t * 7.3) + 0.5 * math.sin(t * 13.1)); jy = g["handheld"] * (math.cos(t * 6.1) + 0.5 * math.sin(t * 11.7))
    z = 1.0 / max(0.5, g["crop"]) * (1 + g["push"] * (0.5 - 0.5 * math.cos(min(t, 6.0) / 6.0 * math.pi)))
    dx = w * g.get("drift", 0.0) * math.sin(t * 0.4)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), g["tilt"], z); M[0, 2] += jx + dx; M[1, 2] += jy
    out = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    out *= np.array(g["grade"], np.float32)[None, None, :]
    if g["under"]:                                                                  # underlight: the lower half brighter, the top darker
        ramp = np.linspace(1 - g["under"], 1 + g["under"], h, dtype=np.float32)[:, None, None]; out *= ramp
    return np.clip(out, 0, 255).astype(np.uint8)

def courtroom(set_img, portraits, speaker, t):
    """THEATER_STYLE = courtroom: the locked set with the bench (Rosa, top centre), the lectern (Grimm, left) and the defence table (Vale, right);
    a deterministic cut: the speaking character is shown large (grammar applied), the others small in place."""
    H, W = set_img.shape[:2]; out = set_img.copy()
    spots = {"JUDGE": (0.5, 0.28, 0.30), "SKEPTIC": (0.22, 0.62, 0.34), "DIRECTOR": (0.78, 0.62, 0.34)}
    for sp, (cx, cy, sc) in spots.items():
        im = portraits.get(sp)
        if im is None: continue
        big = sp == speaker; hh = int(H * sc * (1.25 if big else 0.8)); ww = int(im.shape[1] * hh / im.shape[0])
        p = cv2.resize(apply_grammar(im, sp, t) if (big and S("CHAR_GRAMMAR_ON", bool)) else im, (ww, hh))
        x0 = int(W * cx - ww / 2); y0 = int(H * cy - hh / 2)
        x0, y0 = max(0, min(W - ww, x0)), max(0, min(H - hh, y0))
        out[y0:y0 + hh, x0:x0 + ww] = p
    return out

# ---------------------------------------------------------------- hero-still reels
def poster_score(img):
    """Cheap CV poster quality in [0, 1]: saliency concentrated in ONE region (focal point), contrast, and the share of saliency inside the best 9:16
    crop (vertical safety). No AI call."""
    small = cv2.resize(img, (256, 144)); gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    try:
        ok, sal = cv2.saliency.StaticSaliencySpectralResidual_create().computeSaliency(small)
        sal = sal.astype(np.float32) if ok else None
    except Exception: sal = None
    if sal is None: sal = np.abs(cv2.Laplacian(cv2.GaussianBlur(gray, (0, 0), 2), cv2.CV_32F))
    sal = cv2.GaussianBlur(sal, (0, 0), 6); sal = sal / max(1e-6, sal.sum())
    peak = float(np.sort(sal.ravel())[::-1][: sal.size // 12].sum())                  # mass in the top 8 % = one strong focal region
    contrast = float(min(1.0, gray.std() / 64.0))
    cw = int(144 * 9 / 16); cols = sal.sum(axis=0); win = np.convolve(cols, np.ones(cw), "valid")
    crop = float(win.max()) if len(win) else 0.0
    return round(0.45 * peak + 0.25 * contrast + 0.30 * crop, 4), int(np.argmax(win)) * 256 // 256 if len(win) else 0

def pick_best(paths, n=None):
    """The best still of the first N (HERO_STILL_CANDIDATES) by poster_score. Returns (path, score, crop_x0 in the 256-wide grid) or None."""
    best = None
    for p in list(paths)[: (n or S("HERO_STILL_CANDIDATES", int))]:
        im = cv2.imread(p)
        if im is None: continue
        sc, x0 = poster_score(im)
        if best is None or sc > best[1]: best = (p, sc, x0)
    return best

def next_template():
    last = str(S("HERO_REEL_LAST_TEMPLATE") or "")
    i = (TEMPLATES.index(last) + 1) % len(TEMPLATES) if last in TEMPLATES else 0
    return TEMPLATES[i]

def build(still, hook, audio_src, t0, t1, out_path, seed="hero", template=None, size=None):
    """Render one seamless-loop vertical reel. audio_src = the finished episode mix; [t0, t1] = the voiced line to reuse. Returns out_path or None.
    Duration = clamp(line + 1 s, HERO_STILL_MIN_SEC, HERO_STILL_MAX_SEC) (v9.3.1: 6-10 s; was 15-25). Bounded: one ffmpeg encode, one audio cut; no paid call."""
    from whatifs import atmosphere as AT, render as RN
    from whatifs.media import font
    from PIL import Image, ImageDraw
    W, H = size or ((360, 640) if FAKE else (1080, 1920)); fps = 30
    img = cv2.imread(still)
    if img is None: return None
    lo, hi = S("HERO_STILL_MIN_SEC", float), S("HERO_STILL_MAX_SEC", float)
    dur = float(min(hi, max(lo, (t1 - t0) + 1.0))); n = int(dur * fps)
    ih, iw = img.shape[:2]; cw = int(ih * 9 / 16)
    _, x0g = poster_score(img); x0 = int(min(max(0, x0g * iw / 256), max(0, iw - cw)))
    crop = cv2.resize(img[:, x0:x0 + cw] if cw <= iw else img, (W, H), interpolation=cv2.INTER_AREA)
    template = template or next_template()
    units = [{"start": 0.0, "end": dur, "text": "fire" if template == "orbit_embers" else "fog", "show": []}]
    shots = [{"prompt": {"push_glow": "glow", "rise_fog": "fog mist", "orbit_embers": "fire embers"}[template]}]
    beats = [i * 0.6 for i in range(int(dur / 0.6))]                                   # 100 bpm grid; the caps thin it to <= 2 per second
    atm = AT.Atmosphere(units, shots, {"intensity": 2}, W, H, fps, seed=seed, beats=beats, long_video=False)
    fnt = font(int(H * 0.045)); raw = os.path.splitext(out_path)[0] + "_v.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20", raw]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for g in range(n):
        t = g / fps; z = 1.0 + 0.06 * (0.5 - 0.5 * math.cos(2 * math.pi * t / dur))      # cosine push: frame n == frame 0 (seamless loop)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); fr = cv2.warpAffine(crop, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        fr = atm.apply(fr, g)
        if t < 2.5 and hook:                                                             # the hook text inside the first second, gone before the loop point
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im)
            tw = d.textlength(hook, font=fnt); d.rectangle((W / 2 - tw / 2 - 16, H * 0.12 - 12, W / 2 + tw / 2 + 16, H * 0.12 + H * 0.06), fill=(0, 0, 0))
            d.text((W / 2 - tw / 2, H * 0.12), hook, font=fnt, fill=(255, 255, 255)); fr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: return None
    st = max(0.0, t0 - 0.2); fade = 0.6
    a = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ss", f"{st:.2f}", "-t", f"{dur:.2f}", "-i", audio_src, "-map", "0:v", "-map", "1:a?",
                        "-af", f"apad,atrim=0:{dur:.2f},afade=t=in:d={fade},afade=t=out:st={dur - fade:.2f}:d={fade},loudnorm=I=-14:TP=-1.0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out_path], capture_output=True)
    try: os.remove(raw)
    except Exception: pass
    if a.returncode or not os.path.exists(out_path): return None
    atm_qc = AT.pulse_qc(atm)
    if atm_qc: log(f"hero-still reel pulse caps failed: {atm_qc} - not used", "WARN"); return None
    set_setting("HERO_REEL_LAST_TEMPLATE", template)
    return out_path

def hero_short_slot(slot_iso):
    """v9.3: when the hero-still Short goes public: HERO_SHORT_DELAY_MIN after the long video's slot ('' when the slot is unknown: then no upload)."""
    from whatifs.core import parse_iso
    import datetime as _dt
    t = parse_iso(slot_iso or "")
    if not t: return ""
    return (t + _dt.timedelta(minutes=max(0.0, S("HERO_SHORT_DELAY_MIN", float)))).strftime("%Y-%m-%dT%H:%M:%SZ")

def make_for_episode(ep, out_dir, stills, master, units, hook, slot_iso=None, long_id=None, title=None):
    """Episode step (after scheduling). Never raises; never blocks. Returns the reel path or None."""
    from whatifs import v91 as V91
    if not V91.on("HERO_STILL_REELS_ON", ep): return None
    res = None
    with V91.guard("HERO_STILL_REELS_ON", ep):
        best = pick_best(stills)
        if not best: return None
        from whatifs import showfx as SFX
        ev = SFX.events(units); op = [t for t, k, _ in ev if k == "clip_open"]; cl = [t for t, k, _ in ev if k == "clip_close"]
        t0, t1 = (op[0], cl[0]) if op and cl and cl[0] > op[0] else (float(units[0]["start"]) if units else 0.0, float(units[0]["end"]) if units else 4.0)
        out = os.path.join(out_dir, f"{ep}_hero.mp4")
        res = build(best[0], hook, master, t0, t1, out, seed=ep)
        if res:
            from whatifs import publish as PUB
            PUB.drive_upload(res, os.path.basename(res)); log(f"hero-still reel filed ({os.path.basename(best[0])}, poster score {best[1]})", episode=ep)
            if V91.on("HERO_STILL_SHORTS_ON", ep):                            # v9.3 (fix): it was uploaded PUBLIC at once, ~30 h before the long video existed
                sched = hero_short_slot(slot_iso)
                from whatifs import launch as LA
                if not sched: log("hero-still Short not uploaded: no release slot (it never goes out before the long video)", "WARN", ep)
                elif not LA.uploads_open(): log("hero-still Short not uploaded: uploads are not confirmed public yet (upload check pending or lock on)", "WARN", ep)
                else:
                    long_url = f"https://youtu.be/{long_id}" if long_id else ""
                    PUB.yt_upload(res, str(hook or title or "Reality on Trial")[:80],                       # v9.3.1: the hook is the title; no "#shorts"
                                  (str(hook or "") + (f"\nThe full case: {long_url}" if long_url else "")).strip(), ["what if"],
                                  publish_at=sched, ai_label=S("AI_LABEL_DEFAULT", bool), short=True)
                    log(f"hero-still Short scheduled for {sched}", episode=ep)
            if not (S("META_ON", bool) and os.environ.get("META_TOKEN")): log("hero-still reel: Instagram skipped (no Meta keys) - zero cost", episode=ep)
    return res
