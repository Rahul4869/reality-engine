"""The renderer: segments (parallax stills, crops, clips, graphics, particles) piped into FFmpeg, frame-accurate against the narration clock, with score and effects. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os, subprocess, random, hashlib, math
import numpy as np, cv2
from PIL import Image, ImageFilter
from whatifs.core import S, log, SMALL
from whatifs.media import depth_map, graphic_frame

FPS = 30   # default; the Settings cell FPS (24/25/30/50/60) is used at render time via fps()
def fps():
    try: v = S("FPS", int)
    except Exception: v = 30
    return v if v in (24, 25, 30, 50, 60) else 30
def out_size():
    if SMALL: return 640, 360
    h = S("OUTPUT_HEIGHT", int); return (2560, 1440) if h >= 1440 else (1920, 1080)
def work_size():
    return (640, 360) if SMALL else (1920, 1080)

def _enc_args(W, H, extra_vf=""):
    try: g = max(0, min(6, S("GRAIN_LEVEL", int))); crf = max(16, min(28, S("VIDEO_CRF", int)))
    except Exception: g, crf = 3, 20
    grade = "eq=contrast=1.06:saturation=1.08:gamma=0.98,vignette=PI/5" + (f",noise=alls={g}:allf=t" if g else "")     # v8.3: light grain + CRF 20 (v8.2: grain 4, CRF 17 made ~4 GB masters)
    vf = f"{extra_vf + ',' if extra_vf else ''}scale={W}:{H}:flags=lanczos,{grade},format=yuv420p"
    return ["-vf", vf, "-r", str(fps()), "-c:v", "libx264", "-preset", "veryfast" if not SMALL else "ultrafast",
            "-crf", str(crf), "-pix_fmt", "yuv420p", "-video_track_timescale", "15360", "-an"]

def _ease(t): return t * t * (3 - 2 * t)

# v8.1: an optional code-drawn overlay (the speaker tag). _render sets it once and tells us where each segment starts in the whole video.
_OVL = {"obj": None, "start": 0}
def set_overlay(o): _OVL["obj"] = o; _OVL["start"] = 0
def set_cursor(frame_index): _OVL["start"] = int(frame_index)

def _pipe(path, frames_iter, nframes, ww, wh):
    W, H = out_size(); ovl, g0 = _OVL["obj"], _OVL["start"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ww}x{wh}", "-r", str(fps()), "-i", "-"] + _enc_args(W, H) + ["-frames:v", str(nframes), path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for fr in frames_iter:
        if ovl is not None:
            try: fr = ovl.apply(fr if fr.flags.writeable else fr.copy(), g0 + n)
            except Exception as e: log(f"overlay frame skipped: {e}", "WARN"); ovl = None
        p.stdin.write(fr.tobytes()); n += 1
        if n >= nframes: break
    while n < nframes:   # safety: never short
        if ovl is not None:
            try: fr = ovl.apply(fr if fr.flags.writeable else fr.copy(), g0 + n)
            except Exception: ovl = None
        p.stdin.write(fr.tobytes()); n += 1
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError(f"ffmpeg pipe failed for {path}")
    return path

def _load(img_path, ww, wh, pad=1.3):
    im = cv2.imread(img_path)
    if im is None: raise RuntimeError(f"cannot read {img_path}")
    tw, th = int(ww * pad), int(wh * pad)
    s = max(tw / im.shape[1], th / im.shape[0]); im = cv2.resize(im, (int(im.shape[1] * s + 1), int(im.shape[0] * s + 1)), interpolation=cv2.INTER_LANCZOS4)
    y0, x0 = (im.shape[0] - th) // 2, (im.shape[1] - tw) // 2
    return im[y0:y0 + th, x0:x0 + tw]

_FOCUS = {"left": (0.32, 0.5), "right": (0.68, 0.5), "top": (0.5, 0.32), "bottom": (0.5, 0.68), "center": (0.5, 0.5)}
LOOKS = ("none", "warm", "cool", "contrast", "dim")
def _look(src, look):
    """v8.2: free variety for a re-used picture (a different crop is not enough on its own): a gentle colour grade, applied once per segment."""
    if look in (None, "none"): return src
    f = src.astype(np.float32)
    if look == "warm": f *= np.array([0.92, 1.0, 1.10], np.float32)          # BGR: a little more red
    elif look == "cool": f *= np.array([1.10, 1.0, 0.92], np.float32)
    elif look == "contrast": f = (f - 128.0) * 1.16 + 124.0
    elif look == "dim": f *= 0.86
    return np.clip(f, 0, 255).astype(np.uint8)

def _parallax_v87(img_path, path, nframes, seed, detail=False, depth=None, focus=None, look=None):
    """Depth parallax camera move (wide) or a punched-in detail drift. Different move per shot, S-curve eased."""
    ww, wh = work_size(); rng = random.Random(seed)
    detail = detail or (focus in _FOCUS)
    src = _look(_load(img_path, ww, wh, 1.3 if not detail else 1.6), look)
    sh, sw = src.shape[:2]
    if depth is None: depth = depth_map(img_path)
    D = cv2.resize(depth, (sw, sh)).astype(np.float32)
    move = rng.choice(["push", "pull", "pan_l", "pan_r", "rise", "drift"])
    z0, z1 = {"push": (1.0, 1.16), "pull": (1.16, 1.0), "pan_l": (1.06, 1.1), "pan_r": (1.06, 1.1), "rise": (1.05, 1.12), "drift": (1.03, 1.09)}[move]
    dx = {"pan_l": 1, "pan_r": -1}.get(move, rng.uniform(-0.4, 0.4)) * sw * 0.05
    dy = {"rise": -1}.get(move, rng.uniform(-0.3, 0.3)) * sh * 0.04
    if detail and focus in _FOCUS: cx0, cy0 = sw * _FOCUS[focus][0], sh * _FOCUS[focus][1]
    elif detail:
        fy, fx = np.unravel_index(np.argmax(cv2.GaussianBlur(D, (0, 0), 25)), D.shape)
        cx0, cy0 = np.clip(fx, sw * 0.3, sw * 0.7), np.clip(fy, sh * 0.3, sh * 0.7)
    else: cx0, cy0 = sw / 2, sh / 2
    par = (0.0 if detail else sw * 0.018) * rng.choice([-1, 1])
    uu, vv = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(wh, dtype=np.float32))
    base_scale = ww / (sw / (1.3 if not detail else 1.6))
    def frames():
        for f in range(nframes):
            t = _ease(f / max(1, nframes - 1)); z = (z0 + (z1 - z0) * t) * base_scale
            cx, cy = cx0 + dx * (t - 0.5), cy0 + dy * (t - 0.5)
            mx = cx + (uu - ww / 2) / z; my = cy + (vv - wh / 2) / z
            if par:
                d = cv2.remap(D, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                mx = mx + par * (t - 0.5) * (d - 0.5) * 2
            yield cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return _pipe(path, frames(), nframes, ww, wh)


# ---------------- v8.9 cinematic camera library (free: pure code on pictures already paid for) ----------------
MOVES_HIGH = ("push_parallax", "whip_settle", "orbit", "rack_focus", "kb_roll")                       # opening window + the shot before each reaction
MOVES_CALM = ("drift", "push_parallax", "pull", "handheld", "kb_roll", "orbit", "rack_focus")         # explanation lines
CAMERA_MOVES = tuple(dict.fromkeys(MOVES_HIGH + MOVES_CALM))                                          # every move the Director may suggest (v8.9)

def pick_move(suggested, rng, energy="calm", avoid=None):
    """v8.9: the Director's suggested move is used when it is in the library, allowed at this energy (whip-and-settle only on strong shots) and not a repeat
    of the previous shot; otherwise code chooses. A suggestion is a hint, never a way around the variety rule."""
    m = str(suggested or "").strip().lower()
    if m in CAMERA_MOVES and m != avoid and m in (MOVES_HIGH if energy == "high" else MOVES_CALM): return m
    return choose_move(rng, energy, avoid)
_LAST = {"move": None}

def choose_move(rng, energy="calm", avoid=None):
    """A move for this shot: from the energy's pool, never the same as the previous shot (no visible repetition)."""
    pool = [m for m in (MOVES_HIGH if energy == "high" else MOVES_CALM) if m != avoid] or list(MOVES_CALM)
    return rng.choice(pool)

def camera_path(move, nframes, sw, sh, ww, wh, base_scale, rng, energy="calm", cx0=None, cy0=None, detail=False):
    """Per-frame (cx, cy, zoom, rotation radians, parallax px, focus depth) for one move. The centre is CLAMPED so the rotated, zoomed viewport plus the
    largest parallax shift always stays inside the picture (no mirrored edges ever show). Variable speed comes from the easing of each move."""
    amp = 1.7 if energy == "high" else 1.15; sgn = rng.choice([-1, 1]); cx0 = sw / 2 if cx0 is None else cx0; cy0 = sh / 2 if cy0 is None else cy0
    ease = _ease; z0, z1, dx, dy, r0, r1, par, hand, rack = 1.0, 1.08, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None
    if move == "push_parallax": z0, z1, par = 1.0, 1.0 + 0.13 * amp, 0.022 * amp
    elif move == "pull": z0, z1, par = 1.0 + 0.13 * amp, 1.0, 0.016 * amp
    elif move == "drift": z0, z1, dx, dy = 1.03, 1.03 + 0.04 * amp, sgn * 0.04 * amp, rng.uniform(-0.02, 0.02); ease = lambda t: t
    elif move == "orbit": z0, z1, dx, par, r0, r1 = 1.06, 1.10, sgn * 0.05 * amp, 0.035 * amp, -sgn * 0.004, sgn * 0.004
    elif move == "handheld": z0, z1, hand = 1.06, 1.09, 0.0035 * amp
    elif move == "rack_focus": z0, z1, dx, rack = 1.04, 1.04 + 0.06 * amp, sgn * 0.015 * amp, rng.choice([(0.85, 0.25), (0.25, 0.85)])
    elif move == "kb_roll":
        z0, z1, dx, dy = 1.02, 1.02 + 0.10 * amp, sgn * 0.035, rng.uniform(-0.025, 0.025); r1 = sgn * rng.uniform(0.017, 0.043)      # 1-2.5 degrees of roll
        p_ = rng.uniform(1.4, 2.2); ease = (lambda t, p_=p_: t ** p_) if rng.random() < 0.5 else (lambda t, p_=p_: 1 - (1 - t) ** p_)
    elif move == "whip_settle": z0, z1, dx, par = 1.0, 1.0 + 0.14 * amp, sgn * 0.06, 0.02 * amp; ease = lambda t: 1 - (1 - t) ** 3
    if detail: par = 0.0
    par_px = sw * par * rng.choice([-1, 1]); ph = [rng.uniform(0, 6.283) for _ in range(6)]; fq = [rng.uniform(0.25, 0.6), rng.uniform(0.7, 1.7), rng.uniform(0.3, 0.9)]
    out = []
    for f in range(nframes):
        u = f / max(1, nframes - 1); t = ease(u); z = (z0 + (z1 - z0) * t) * base_scale; th = r0 + (r1 - r0) * t
        cx = cx0 + dx * sw * (t - 0.5); cy = cy0 + dy * sh * (t - 0.5)
        if hand:
            sec = f / max(1, fps()); cx += hand * sw * (0.6 * math.sin(6.283 * fq[0] * sec + ph[0]) + 0.4 * math.sin(6.283 * fq[1] * sec + ph[1]))
            cy += hand * sh * (0.6 * math.sin(6.283 * fq[2] * sec + ph[2]) + 0.4 * math.sin(6.283 * fq[1] * 1.3 * sec + ph[3])); th += 0.0045 * math.sin(6.283 * fq[0] * sec + ph[4])
        hw, hh = (ww / 2) / z, (wh / 2) / z; c, s_ = abs(math.cos(th)), abs(math.sin(th)); pm = abs(par_px) * 0.5 + 1.0
        ex, ey = hw * c + hh * s_ + pm, hw * s_ + hh * c + pm
        if 2 * ex > sw or 2 * ey > sh:                    # never possible with the 1.3x pad, but a tiny picture must still never show an edge
            k = max(2 * ex / sw, 2 * ey / sh) * 1.01; z *= k; hw, hh = hw / k, hh / k; ex, ey = hw * c + hh * s_ + pm, hw * s_ + hh * c + pm
        cx = min(max(cx, ex), sw - ex); cy = min(max(cy, ey), sh - ey)
        fd = None if rack is None else rack[0] + (rack[1] - rack[0]) * _ease(u)
        out.append((cx, cy, z, th, par_px * (t - 0.5), fd))
    return out

# ---------------- v11 (K161b) WORLD PARTICLE LAYER: independent motion that makes a still read as alive (research 9 Nov 2026) ----------------
# Three depth layers (far/mid/near: size 1:3:8, nearer = faster and softer), light-gated (particles glint where the picture is lit, with a floor so
# dark noir frames still breathe), tinted toward the scene's key light, screen-blended, motion-streaked along velocity, faded in/out over their
# life, pre-rolled (frame 0 is already populated). One look per world: court/case dust, lab embers, office rain, outdoor wind.
PARTICLE_WORLDS = {
    # count per 1920x1080 (scaled by area), size px at 1080p (far, mid, near), speed px/s at 1080p, opacity (far, mid, near), direction, streak, tint BGR
    "dust":  dict(n=(110, 70, 14), size=(2.0, 3.5, 9.0), speed=(6, 14, 26), op=(0.35, 0.55, 0.22), vx=(-0.3, 0.3), vy=(-0.25, 0.15), streak=0.0, tint=(170, 225, 255), wobble=1.0),
    "embers": dict(n=(55, 34, 8), size=(1.6, 3.0, 7.0), speed=(40, 90, 150), op=(0.55, 0.85, 0.35), vx=(-0.25, 0.25), vy=(-1.0, -0.6), streak=0.5, tint=(60, 150, 255), wobble=0.6),
    "rain":  dict(n=(190, 110, 22), size=(1.0, 1.6, 3.0), speed=(900, 1500, 2200), op=(0.22, 0.34, 0.18), vx=(0.10, 0.22), vy=(1.0, 1.0), streak=1.0, tint=(255, 225, 200), wobble=0.0),
    "wind":  dict(n=(120, 70, 12), size=(1.4, 3.0, 8.0), speed=(60, 130, 220), op=(0.30, 0.55, 0.25), vx=(1.0, 1.0), vy=(-0.10, 0.25), streak=0.25, tint=(215, 230, 240), wobble=0.8),
}
WORLD_PARTICLES = {"court": "dust", "case": "dust", "lab": "embers", "office": "rain", "outdoor": "wind"}

class Particles:
    def __init__(self, world, src, seed, ww, wh, nframes, fpsv):
        style = PARTICLE_WORLDS[WORLD_PARTICLES.get(world, world) if WORLD_PARTICLES.get(world, world) in PARTICLE_WORLDS else "dust"]
        self.ww, self.wh, self.fps = ww, wh, fpsv; sc = wh / 1080.0; area = (ww * wh) / (1920 * 1080)
        rng = np.random.default_rng(int(hashlib.md5(f"{seed}|{world}".encode()).hexdigest()[:8], 16))   # stable across processes (built-in hash() of a str is randomised per run)
        g = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0                 # light gate: where the picture is lit (with a floor),
        self.g98 = max(1e-3, float(np.percentile(g, 98))); self.floor = S("PARTICLE_GATE_FLOOR", float)   # measured on each rendered frame (follows the camera)
        top = src.reshape(-1, 3)[np.argsort(src.reshape(-1, 3).sum(1))[-max(10, src.shape[0] * src.shape[1] // 100):]].mean(0)   # key light colour
        key = top / max(1.0, top.max()); tint = np.array(style["tint"], np.float32) / 255.0
        self.col = (0.55 * tint + 0.45 * key).astype(np.float32)
        dens = S("PARTICLE_DENSITY", float); self.layers = []
        for li, (n, size, speed, op) in enumerate(zip(style["n"], style["size"], style["speed"], style["op"])):
            m = max(1, int(round(n * area * dens)))
            vx = rng.uniform(*style["vx"], m); vy = rng.uniform(*style["vy"], m); norm = np.maximum(1e-3, np.hypot(vx, vy))
            sp = speed * sc * rng.uniform(0.7, 1.3, m)
            self.layers.append(dict(x=rng.uniform(0, ww, m), y=rng.uniform(0, wh, m), vx=vx / norm * sp, vy=vy / norm * sp,
                                    r=np.maximum(0.6, size * sc * rng.lognormal(0, 0.35, m)), a=op * rng.uniform(0.5, 1.0, m),
                                    life=rng.uniform(2.0, 6.0, m), age=rng.uniform(0, 6.0, m), ph=rng.uniform(0, 6.28, m),
                                    blur=(1.2, 0.0, 3.5)[li] * sc, streak=style["streak"], wob=style["wobble"] * sc * (4, 7, 12)[li]))
        self.dt = 1.0 / fpsv
        for _ in range(int(S("PARTICLE_PREROLL_S", float) * fpsv)): self._step()
    def _step(self):
        for L in self.layers:
            L["x"] = (L["x"] + L["vx"] * self.dt) % self.ww; L["y"] = (L["y"] + L["vy"] * self.dt) % self.wh
            L["age"] += self.dt; dead = L["age"] > L["life"]; L["age"][dead] = 0.0
    def apply(self, fr, k):
        dv = max(1, S("PARTICLE_RES_DIV", int)); hw, hh = self.ww // dv, self.wh // dv          # v11: drawn at 1/dv resolution, scaled up (soft particles hide it)
        acc = np.zeros((hh, hw), np.float32); t = k * self.dt; sh = 4                           # sub-pixel positions (cv2 shift bits)
        for L in self.layers:
            lay = np.zeros_like(acc)
            fade = np.clip(np.minimum(L["age"], L["life"] - L["age"]) / 0.6, 0, 1)
            wx = (L["x"] + L["wob"] * np.sin(L["ph"] + t * 0.9)) / dv; wy = (L["y"] + L["wob"] * np.cos(L["ph"] * 1.3 + t * 0.7)) / dv
            for x, y, r, a, f, vx, vy in zip(wx, wy, L["r"] / dv, L["a"], fade, L["vx"] / dv, L["vy"] / dv):
                val = float(a * f)
                if val < 0.02: continue
                p0 = (int(x * 16), int(y * 16))
                if L["streak"] > 0:                                     # motion streak along the velocity (180-degree shutter)
                    ex, ey = x - vx * self.dt * 0.5 * (1 + 4 * L["streak"]), y - vy * self.dt * 0.5 * (1 + 4 * L["streak"])
                    cv2.line(lay, p0, (int(ex * 16), int(ey * 16)), val, max(1, int(round(r))), cv2.LINE_AA, sh)
                else: cv2.circle(lay, p0, max(16, int(round(r * 16))), val, -1, cv2.LINE_AA, sh)
            if L["blur"] / dv > 0.3: lay = cv2.GaussianBlur(lay, (0, 0), L["blur"] / dv)
            acc += lay
        self._step()
        q = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (max(8, hw // 2), max(8, hh // 2)), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        q = cv2.GaussianBlur(q, (0, 0), max(1.5, hw * 0.01))
        gate = cv2.resize(np.clip(self.floor + (1 - self.floor) * q / self.g98, 0, 1), (hw, hh), interpolation=cv2.INTER_LINEAR)
        over = (np.clip(acc * gate, 0, 1)[..., None] * (self.col * 255.0)[None, None, :]).astype(np.uint8)
        over = cv2.resize(over, (self.ww, self.wh), interpolation=cv2.INTER_LINEAR)
        inv = cv2.multiply(cv2.bitwise_not(fr), cv2.bitwise_not(over), scale=1.0 / 255.0)     # screen blend in 8-bit: 255 - (255-a)(255-b)/255
        return cv2.bitwise_not(inv)

def parallax_segment(img_path, path, nframes, seed, detail=False, depth=None, focus=None, look=None, energy="calm", move=None, world=None):
    """v8.9: one cinematic camera move per shot (push-in + depth parallax, pull, drift, subtle orbit, controlled handheld, rack-focus, variable-speed Ken Burns
    with a 1-2.5 degree roll, whip-and-settle). energy='high' (opening window, the shot before a reaction) = the strongest moves, ~45 % bigger.
    Never the same move twice in a row. Settings CAMERA_MOTION = gentle restores the v8.7 moves exactly."""
    if str(S("CAMERA_MOTION") or "dynamic").strip().lower() == "gentle":
        return _parallax_v87(img_path, path, nframes, seed, detail=detail, depth=depth, focus=focus, look=look)
    ww, wh = work_size(); rng = random.Random(seed)
    detail = detail or (focus in _FOCUS); pad = 1.3 if not detail else 1.6
    src = _look(_load(img_path, ww, wh, pad), look)
    sh, sw = src.shape[:2]
    if depth is None: depth = depth_map(img_path)
    D = cv2.resize(depth, (sw, sh)).astype(np.float32)
    move = pick_move(move, rng, energy, _LAST["move"]); _LAST["move"] = move      # v8.9: a Director suggestion is validated, never trusted blindly
    if detail and focus in _FOCUS: cx0, cy0 = sw * _FOCUS[focus][0], sh * _FOCUS[focus][1]
    elif detail:
        fy, fx = np.unravel_index(np.argmax(cv2.GaussianBlur(D, (0, 0), 25)), D.shape)
        cx0, cy0 = float(np.clip(fx, sw * 0.3, sw * 0.7)), float(np.clip(fy, sh * 0.3, sh * 0.7))
    else: cx0, cy0 = sw / 2, sh / 2
    base_scale = ww / (sw / pad)
    cam = camera_path(move, nframes, sw, sh, ww, wh, base_scale, rng, energy, cx0, cy0, detail)
    du, dv = np.meshgrid(np.arange(ww, dtype=np.float32) - ww / 2, np.arange(wh, dtype=np.float32) - wh / 2)
    soft = cv2.GaussianBlur(src, (0, 0), max(1.5, ww * 0.0045)) if move == "rack_focus" else None
    life = S("LIFE_LAYER_ON", bool); amp = S("LIFE_AMP", float) * wh; ph = rng.uniform(0, 6.28); f_ = fps()
    flat = float(np.std(D)) < 0.05                       # v11: depth failed / flat -> the subject is assumed in the centre (screen-space breath)
    parts = Particles(world or S("PARTICLE_DEFAULT_WORLD"), src, seed, ww, wh, nframes, fps()) if S("PARTICLES_ON", bool) else None   # v11 (K161b)
    centre = np.clip(1.0 - (du / (ww * 0.33)) ** 2 - (dv / (wh * 0.4)) ** 2, 0.0, 1.0).astype(np.float32) if life else None
    def frames():
        for k, (cx, cy, z, th, pshift, fd) in enumerate(cam):
            c, s_ = math.cos(th), math.sin(th)
            mx = (cx + (du * c - dv * s_) / z).astype(np.float32); my = (cy + (du * s_ + dv * c) / z).astype(np.float32)
            d = cv2.remap(D, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) if (pshift or fd is not None or life) else None
            if pshift: mx = mx + pshift * (d - 0.5) * 2
            if life:                                   # v11 (K161) life layer: the NEAR part of the picture breathes and sways (local, non-camera motion)
                near = centre if flat else np.clip((d - S("LIFE_NEAR_DEPTH", float)) * 3.0, 0.0, 1.0)
                tt = k / f_
                my = my + (amp * math.sin(6.2832 * 0.22 * tt + ph)) * near
                mx = mx + (amp * 0.45 * math.sin(6.2832 * 0.13 * tt + ph * 1.7)) * near
            fr = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if fd is not None:
                b = cv2.remap(soft, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT); w = np.clip(np.abs(d - fd) * 2.6, 0, 1)[..., None]
                fr = (fr.astype(np.float32) * (1 - w) + b.astype(np.float32) * w).astype(np.uint8)
            if parts is not None: fr = parts.apply(fr, k)
            yield fr
    return _pipe(path, frames(), nframes, ww, wh)

# ---------------- v8.10 first-person camera EFFECTS (free; owner rule: every shot type - stills, living stills, Kling, stock, graphics) ----------------
POV_FX = ("pov_rush", "impact_shake", "debris")

import functools
@functools.lru_cache(maxsize=8)
def _vignette(ww, wh, strength):
    y, x = np.ogrid[:wh, :ww]; r = np.sqrt(((x - ww / 2) / (ww / 2)) ** 2 + ((y - wh / 2) / (wh / 2)) ** 2)
    return np.clip(1 - strength * np.clip(r - 0.35, 0, None) ** 1.5, 0, 1).astype(np.float32)[..., None]

def pov_fx(kind, nframes, seed, ww=None, wh=None):
    """A frame filter f(frame, k) for one segment (k = frame index inside it). Deterministic per seed (a re-render looks the same).
    pov_rush: accelerating push-in, radial speed streaks, a slow roll, edges darkening.  impact_shake: a freeze of a few frames, a white flash, a decaying
    shake and a tunnel-vision vignette that slowly opens (the sound's impact recipe starts on frame 0 of the same segment). debris: two parallax layers of
    streaks flying past the lens (near = big, fast, soft; far = small, slow)."""
    if kind not in POV_FX: return None
    ww, wh = ww or work_size()[0], wh or work_size()[1]; rng = random.Random(f"{seed}|{kind}"); fpsv = fps(); sgn = rng.choice([-1, 1])
    def zoom(fr, z, th=0.0, dx=0.0, dy=0.0):
        M = cv2.getRotationMatrix2D((ww / 2, wh / 2), math.degrees(th), z); M[0, 2] += dx; M[1, 2] += dy
        return cv2.warpAffine(fr, M, (ww, wh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if kind == "pov_rush":
        vig = _vignette(ww, wh, 0.9)
        def f(fr, k):
            t = k / max(1, nframes - 1); z = 1.0 + 0.24 * t * t; th = sgn * 0.03 * math.sin(math.pi * t)
            base = zoom(fr, z, th)
            if t > 0.15:
                a = zoom(base, 1.0 + 0.035 * t); b = zoom(base, 1.0 + 0.07 * t); w_ = 0.30 * t
                base = cv2.addWeighted(cv2.addWeighted(base, 1 - w_, a, w_, 0), 1 - w_ * 0.7, b, w_ * 0.7, 0)
            return (base.astype(np.float32) * (1 - (1 - vig) * (0.4 + 0.6 * t))).astype(np.uint8)
        return f
    if kind == "impact_shake":
        hold = max(2, int(0.12 * fpsv)); first = {}; ph = [rng.uniform(0, 6.28) for _ in range(4)]
        def f(fr, k):
            if k == 0: first["fr"] = fr.copy()
            if k < hold and "fr" in first: fr = first["fr"]                              # freeze: the instant of impact holds
            sec = k / fpsv; amp = 0.028 * ww * math.exp(-sec / 0.45)
            dx = amp * math.sin(2 * math.pi * 13 * sec + ph[0]) * 0.8; dy = amp * math.sin(2 * math.pi * 17 * sec + ph[1]) * 0.6
            out = zoom(fr, 1.06 + 0.04 * math.exp(-sec / 0.6), 0.012 * math.exp(-sec / 0.5) * math.sin(2 * math.pi * 9 * sec + ph[2]), dx, dy)
            tun = 0.85 * math.exp(-sec / 1.6)
            if tun > 0.02: out = (out.astype(np.float32) * (1 - (1 - _vignette(ww, wh, 1.6)) * tun)).astype(np.uint8)
            fl = 0.75 if k < 2 else (0.35 if k < 4 else 0.0)
            if fl: out = cv2.addWeighted(out, 1 - fl, np.full_like(out, 255), fl, 0)
            return out
        return f
    if kind == "debris":
        parts = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.choice([0.35, 1.0]), rng.uniform(0.6, 1.4)) for _ in range(46)]
        def f(fr, k):
            sec = k / fpsv; lay = np.zeros_like(fr); near = np.zeros_like(fr)
            for x0, y0, depth, sp in parts:
                d = (sec * sp * depth * 0.9 + abs(x0) * 0.3) % 1.2
                x = ww / 2 + x0 * ww * (0.15 + d); y = wh / 2 + y0 * wh * (0.15 + d)
                ln = (6 + 40 * depth) * (0.4 + d); vx, vy = x0 * ln, y0 * ln
                tgt = near if depth > 0.5 else lay; c = int(70 + 120 * depth)
                cv2.line(tgt, (int(x), int(y)), (int(x - vx), int(y - vy)), (c, c, c), max(1, int(1 + 3 * depth * d)), cv2.LINE_AA)
            near = cv2.GaussianBlur(near, (0, 0), 2.2)
            return cv2.add(cv2.add(zoom(fr, 1.03 + 0.02 * math.sin(sec)), (lay * 0.55).astype(np.uint8)), (near * 0.8).astype(np.uint8))
        return f

class FxOverlay:
    """Runs a POV effect on a segment's frames, then the normal overlay (speaker tag, reactions) on top, so the tag itself never shakes."""
    def __init__(self, base, fx, f0): self.base, self.fx, self.f0 = base, fx, f0
    def apply(self, fr, g):
        fr = self.fx(fr, g - self.f0)
        return self.base.apply(fr, g) if self.base is not None else fr
    def active(self): return True

def with_fx(ovl, kind, nframes, seed, f0):
    """The overlay to set for one segment: the POV effect (if any, and POV_CAMERA_ON) wrapped around the normal overlay."""
    if not kind or not S("POV_CAMERA_ON", bool): return ovl
    fx = pov_fx(kind, nframes, seed)
    return FxOverlay(ovl, fx, f0) if fx else ovl

def clip_segment(clip_path, path, nframes, loop=False, push=0.0):
    """push > 0 (v8.9, living stills only): a slow sub-pixel push-in over the clip (1 -> 1 + push), so atmospheric clips also carry camera motion."""
    W, H = out_size(); ww, wh = work_size()
    dur_in = probe_dur(clip_path); want = nframes / fps()
    slow = 1.0 if loop else min(1.25, max(1.0, want / max(0.1, dur_in)))      # v8.3: was up to 2x (frame doubling = judder); the renderer now hands the rest of a long unit to a camera move on the same picture
    pre = f"scale={ww}:{wh}:force_original_aspect_ratio=increase,crop={ww}:{wh},setpts={slow:.4f}*PTS,fps={fps()},tpad=stop_mode=clone:stop_duration={want + 1:.2f}"
    if not loop and push == 0 and S("MOTION_BOOST_ON", bool) and want > dur_in * slow + 0.3:       # v9: stretch a Kling clip without freezing: play it
        sl = min(1.25, max(1.0, want / max(0.1, 2 * dur_in)))                                        # forward then in reverse (an echo cut), a gentle speed
        pre = (f"split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0,scale={int(ww * 1.06)}:{int(wh * 1.06)}:force_original_aspect_ratio=increase,"     # ramp, a 6 % crop-in
               f"crop={ww}:{wh},setpts={sl:.4f}*PTS,fps={fps()},tpad=stop_mode=clone:stop_duration={want + 1:.2f}")                                    # and last-frame hold
    if _OVL["obj"] is not None or push > 0:      # decode to raw frames so the speaker tag can be blended in, then encode exactly like every other segment
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + (["-stream_loop", "-1"] if loop else []) + ["-i", clip_path, "-vf", pre + ",format=bgr24", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        def frames():
            size = ww * wh * 3; frames.n = 0
            while True:
                buf = proc.stdout.read(size)
                if len(buf) < size: break
                fr = np.frombuffer(buf, np.uint8).reshape(wh, ww, 3).copy()
                if push > 0:
                    k = frames.n / max(1, nframes - 1); zz = 1.0 + push * _ease(min(1.0, k)); frames.n += 1
                    M = np.float32([[zz, 0, (1 - zz) * ww / 2], [0, zz, (1 - zz) * wh / 2]]); fr = cv2.warpAffine(fr, M, (ww, wh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                yield fr
        try: return _pipe(path, frames(), nframes, ww, wh)
        finally:
            try: proc.kill(); proc.wait()
            except Exception: pass
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + (["-stream_loop", "-1"] if loop else []) + ["-i", clip_path] + _enc_args(W, H, pre) + ["-frames:v", str(nframes), path]
    subprocess.run(cmd, check=True); return path

def graphic_segment(g, bg_path, path, nframes):
    ww, wh = work_size()
    bg = None
    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB").resize((ww, wh)).filter(ImageFilter.GaussianBlur(14))
    def frames():
        for f in range(nframes):
            im = graphic_frame(g, f / max(1, nframes - 1), ww, wh, bg)
            yield cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    return _pipe(path, frames(), nframes, ww, wh)

def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except Exception: return 0.0

def concat(segs, path):
    lst = path + ".txt"
    with open(lst, "w") as f:
        for s in segs: f.write(f"file '{os.path.abspath(s)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", path], check=True)
    return path

# ---------------- original score + SFX (no licensing risk) ----------------
SR = 48000
def score(duration, seed, events, voice_wav=None, bed_db=-24, duck_db=9, design=None):
    rng = np.random.default_rng(int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)); n = int(duration * SR)
    t = np.arange(n, dtype=np.float32) / SR
    pal = float(rng.uniform(0.86, 1.22)); riser_rate = float(rng.uniform(450, 800)); pop_shift = float(rng.uniform(0.9, 1.12))      # v8.3: every episode gets its own boom / riser / pop colour
    root = float(rng.choice([41.2, 43.65, 46.25, 49.0, 55.0]))
    chord = [root, root * 1.5, root * 2, root * 2.4 if rng.random() < .5 else root * 2.25, root * 3]
    L = np.zeros(n, np.float32); Rr = np.zeros(n, np.float32)
    for i, f in enumerate(chord):
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.013 + 0.007 * i) * t + rng.uniform(0, 6.28)).astype(np.float32)
        ph = rng.uniform(0, 6.28); amp = 0.22 / (1 + i * 0.6)
        L += (amp * lfo * np.sin(2 * np.pi * f * 0.999 * t + ph)).astype(np.float32)
        Rr += (amp * lfo * np.sin(2 * np.pi * f * 1.001 * t + ph + 0.4)).astype(np.float32)
    for ch in (L, Rr):
        noise = rng.standard_normal(n).astype(np.float32)
        noise = cv2.GaussianBlur(noise.reshape(1, -1), (0, 0), sigmaX=40).ravel() * 6
        ch += noise * 0.05
    bed = np.stack([L, Rr], 1); bed /= (np.abs(bed).max() + 1e-6); bed *= 10 ** (bed_db / 20)
    if design:                      # v8.7: the bed moves (arc, section changes, near-silence before peaks, hush under [close]) and carries code-made textures
        from whatifs import sound as SD
        bed *= SD.bed_gain(t, duration, design, seed)[:, None]
        for kind, a, b in design.get("sensory", []):
            i0 = int(a * SR); i1 = min(n, int(b * SR))
            if i1 - i0 < int(0.4 * SR): continue
            tex = SD.texture(kind, (i1 - i0) / SR, f"{seed}{i0}", SR); bed[i0:i0 + len(tex)] += tex[: n - i0] * SD.LEVEL
        # v8.10 immersive layers (ducked under the voice like the bed): ambient beds per scene, close-mic textures, and the impact's near-silence + hole
        for key, lvl in (("ambience", SD.AMB_LEVEL), ("close", SD.CLOSE_LEVEL)):
            for kind, a, b in design.get(key, []):
                i0 = int(a * SR); i1 = min(n, int(b * SR))
                if i1 - i0 < int(0.4 * SR): continue
                tex = SD.texture(kind, (i1 - i0) / SR, f"{seed}{key}{i0}", SR); bed[i0:i0 + len(tex)] += tex[: n - i0] * lvl
        if design.get("impacts"): bed *= SD.impact_gain(t, design["impacts"])[:, None]
    sfx = np.zeros(n, np.float32); sfx2 = np.zeros((n, 2), np.float32)       # v8.10: stereo effects (Doppler pass, impact, foley)
    def put2(at, a2, lvl):
        i0 = int(at * SR)
        if i0 >= n or i0 + len(a2) <= 0: return
        s0 = max(0, -i0); i0 = max(0, i0); e = min(n, i0 + len(a2) - s0); sfx2[i0:e] += a2[s0:s0 + e - i0] * lvl
    if design:
        from whatifs import sound as SD
        for kind, at in design.get("foley", []): put2(at, SD.foley(kind, f"{seed}{at}", SR), SD.FOLEY_LEVEL * SD.KIND_GAIN.get(kind, 1.0))      # v11: per-kind level (ASMR touches quieter)
    rush_end = sorted(at for kind, at in events if kind == "rush_end")
    for kind, at in events:
        i0 = int(at * SR)
        if i0 >= n: continue
        if kind == "boom":
            m = int(2.2 * SR); tt = np.arange(m) / SR
            s = (np.sin(2 * np.pi * (52 * pal * np.exp(-tt * 1.4) + 28 * pal) * tt) * np.exp(-tt * 2.2)).astype(np.float32) * 0.5
        elif kind == "whoosh":
            m = int(0.7 * SR); x = rng.standard_normal(m).astype(np.float32)
            x = cv2.GaussianBlur(x.reshape(1, -1), (0, 0), sigmaX=3).ravel() * 3
            s = x * np.sin(np.linspace(0, np.pi, m)).astype(np.float32) ** 2 * 0.12
        elif kind == "riser":
            m = int(3.0 * SR); tt = np.arange(m) / SR
            s = (np.sin(2 * np.pi * (200 * pal + riser_rate * tt / 3) * tt) * (tt / 3) ** 2).astype(np.float32) * 0.05
            i0 = max(0, i0 - m)
        elif kind == "pop":         # v8.2 reaction sounds (original, generated): a bright pop
            m = int(0.22 * SR); tt = np.arange(m) / SR
            s = (np.sin(2 * np.pi * (1100 * pop_shift * np.exp(-tt * 14) + 260 * pop_shift) * tt) * np.exp(-tt * 16) * 0.34 + np.sin(2 * np.pi * 2200 * pop_shift * tt) * np.exp(-tt * 90) * 0.08).astype(np.float32)
        elif kind == "gasp":        # a short inhale: filtered noise rising then falling
            m = int(0.42 * SR); x = rng.standard_normal(m).astype(np.float32); x = cv2.GaussianBlur(x.reshape(1, -1), (0, 0), sigmaX=5).ravel() * 5
            s = x * (np.sin(np.linspace(0, np.pi, m)) ** 1.6).astype(np.float32) * 0.16
        elif kind in ("impact", "doppler", "debris"):        # v8.10, locked to the POV camera events
            from whatifs import sound as SD
            if kind == "impact":       # rumble + riser that stops 1 s before (the near-silence), then boom + sub drop, ringing, muffled heartbeat, a breath
                put2(at - 4.0, SD.impact_run_up(3.0, f"{seed}{at}", SR), 0.22); put2(at, SD.impact_layers(f"{seed}{at}", SR, pal), 0.55)
            elif kind == "doppler":
                end = next((x for x in rush_end if x > at), at + 2.0); put2(at, SD.doppler(max(0.6, end - at), f"{seed}{at}", SR), 0.16)
            else: put2(at, SD.texture("crackle", 1.6, f"{seed}deb{at}", SR), 0.05)
            continue
        elif kind == "huh":         # two falling blips
            m = int(0.34 * SR); tt = np.arange(m) / SR
            s = (np.sin(2 * np.pi * (520 - 160 * (tt > 0.15)) * tt) * np.exp(-((tt % 0.17) * 18)) * 0.2).astype(np.float32)
        else: continue
        e = min(n, i0 + len(s)); sfx[i0:e] += s[: e - i0]
    mix = bed.copy()
    if voice_wav is not None:
        import soundfile as sf
        v, vsr = sf.read(voice_wav, dtype="float32")
        if v.ndim > 1: v = v.mean(1)
        if vsr != SR: v = cv2.resize(v.reshape(1, -1), (int(len(v) * SR / vsr), 1)).ravel()
        v = np.pad(v, (0, max(0, n - len(v))))[:n]
        blk = 480                                                    # v8.3: the loudness envelope only needs ~100 points a second; a 34,000-tap blur over 8 million samples took minutes
        m_ = len(v) // blk + 1; lo = np.abs(np.pad(v, (0, m_ * blk - len(v)))).reshape(m_, blk).mean(1)
        lo = cv2.GaussianBlur(lo.reshape(1, -1).astype(np.float32), (0, 0), sigmaX=0.12 * SR / blk).ravel()
        env = np.interp(np.arange(len(v)), (np.arange(m_) + 0.5) * blk, lo).astype(np.float32)
        g = 1 - (1 - 10 ** (-duck_db / 20)) * np.clip(env / (env.max() * 0.15 + 1e-6), 0, 1)
        mix *= g[:, None]
        mix += v[:, None]
    mix += sfx[:, None] + sfx2
    return mix

def write_mix(mix, path, lufs=-14):
    import soundfile as sf
    raw = path + ".raw.wav"; sf.write(raw, np.clip(mix, -1, 1), SR, subtype="PCM_24")
    try:          # v8.9.1: the stereo layout is stated explicitly (some FFmpeg builds lose it between loudnorm and aresample and abort), and the big raw file is always removed
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"loudnorm=I={lufs}:TP=-1.0:LRA=11,aresample={SR},aformat=channel_layouts=stereo",
                        "-ar", str(SR), "-ac", "2", path], check=True)
    finally:
        try: os.remove(raw)
        except OSError: pass
    return path

def mux(video, audio, path):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", path], check=True)
    return path

# ---------------- captions ----------------
def _ts(t, comma=True):
    h, m = int(t // 3600), int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", "," if comma else ".")
def srt(timeline, path, max_words=7):
    out, k = [], 1
    for u in timeline["units"]:
        ws = u.get("words") or []
        if not ws:
            ws = [{"w": x, "s": u["start"] + i * (u["end"] - u["start"]) / max(1, len(u["text"].split())), "e": 0} for i, x in enumerate(u["text"].split())]
            for i in range(len(ws)): ws[i]["e"] = ws[i + 1]["s"] if i + 1 < len(ws) else u["end"]
        for i in range(0, len(ws), max_words):
            g = ws[i:i + max_words]
            out.append(f"{k}\n{_ts(g[0]['s'])} --> {_ts(g[-1]['e'])}\n{' '.join(x['w'] for x in g)}\n"); k += 1
    open(path, "w").write("\n".join(out)); return path

