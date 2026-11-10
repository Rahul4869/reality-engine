"""Atmosphere pack: code-only, deterministic per-shot overlays applied under the show overlay at zero API cost. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, math, re, time
import numpy as np
import cv2
from whatifs.core import S, log

MAX_GAIN = 0.22                    # total light any layer stack may add (fraction of 255)
PULSE_MAX_RATE = 2.0               # pulses per second (hard cap)
PULSE_MAX_SWING = 0.08             # luminance swing per pulse (hard cap)
LAYERS = ("GODRAYS", "PARTICLES", "FOG", "SHIMMER", "LENS", "BREATH", "PULSE", "AURA")
DEGRADE_ORDER = ("PARTICLES", "FOG", "GODRAYS")
MOODS = {"fire": r"fire|flame|lava|magma|burn|ember|volcan|explo", "space": r"space|orbit|star|galax|planet|moon|astero|meteor|comet",
         "underwater": r"underwater|ocean floor|deep sea|submar|reef|abyss", "cold": r"ice|snow|frozen|freez|arctic|glacier|blizzard|cold",
         "hot": r"desert|heat|scorch|sun|drought|sahara|engine|exhaust", "rain": r"rain|storm|hurricane|monsoon|flood"}

def _seed(*parts): return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)

def moods_of(text):
    t = str(text or "").lower()
    return {m for m, rx in MOODS.items() if re.search(rx, t)}

def level_for(plan_intensity, moods, impact=False):
    v = str(S("ATMOSPHERE_LEVEL") or "auto").strip().lower()
    if v in ("0", "1", "2", "3"): return int(v)
    base = 1 if plan_intensity in (None, "") else int(plan_intensity)
    return max(0, min(3, base + (1 if moods & {"fire", "space"} or impact else 0)))

def _tile_noise(h, w, seed, scale=24):
    """Tileable smooth noise in [0,1] (wraps at the edges, so it can scroll forever)."""
    rng = np.random.default_rng(seed); g = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    g = np.tile(g, (3, 3)); big = cv2.resize(g, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    n = big[h:2 * h, w:2 * w]; n = cv2.GaussianBlur(n, (0, 0), scale / 2.5)
    return (n - n.min()) / max(1e-6, n.max() - n.min())

class Atmosphere:
    def __init__(self, units, shots, plan, ww, wh, fps, seed="ep", recon=None, beats=None, protect=None, hud_spans=None, long_video=True):
        self.W, self.H, self.fps = ww, wh, fps; self.seed = seed; self.plan = plan or {}
        self.units = units or []; self.shots = shots or []
        self.recon = list(recon or []); self.long = long_video
        self.spans = [(float(u.get("start", 0)), float(u.get("end", 0))) for u in self.units]
        self.flags = {k: S(f"ATMOS_{k}_ON", bool) for k in LAYERS}
        if not S("PULSE_ON", bool): self.flags["PULSE"] = False
        self.dropped = []; self.spent = 0.0; self.frames = 0; self._last = None; self._base = 0.0
        self.qs, self.qh = max(16, ww // 8), max(9, wh // 8)                # eighth-resolution working size for every soft layer
        self.noise = [_tile_noise(self.qh, self.qs, _seed(seed, "fog", i), scale=12) for i in range(2)]
        self.protect = self._protect_mask(protect)
        self._pmask = cv2.resize(self.protect[..., 0], (self.qs, self.qh))[..., None].astype(np.float32)
        self._yy = np.linspace(1.0, 0.0, self.qh, dtype=np.float32)[:, None]; self._xx = np.arange(self.qs, dtype=np.float32)[None, :]
        self._yy2 = np.arange(self.qh, dtype=np.float32)[:, None]; self._mx = self._my = None
        self._edge = np.clip(np.sqrt(((self._xx - self.qs / 2) / (self.qs / 2)) ** 2 + ((self._yy2 - self.qh / 2) / (self.qh / 2)) ** 2) / 1.42, 0, 1).astype(np.float32)
        self.hud_spans = list(hud_spans or [])
        self.pulses = self._pulse_times(beats or [])
        self.shot_info = {}
        self.pulse_log = []
    # ------------------------------------------------------------------ planning
    def _protect_mask(self, boxes):
        """1.0 everywhere, 0.3 inside the HUD, meter, exhibit pin, speaker chip and caption band (fractions of the frame)."""
        m = np.ones((self.qh, self.qs), np.float32)
        for x0, y0, x1, y1 in (boxes or [(0.0, 0.08, 0.45, 0.22), (0.66, 0.08, 1.0, 0.2), (0.0, 0.8, 0.55, 0.95), (0.0, 0.82, 1.0, 1.0)]):
            m[int(y0 * self.qh):int(y1 * self.qh), int(x0 * self.qs):int(x1 * self.qs)] = 0.3
        return cv2.resize(cv2.GaussianBlur(m, (0, 0), 3), (self.W, self.H))[..., None]
    def _pulse_times(self, beats):
        """Beat / bass events -> pulse times, enforcing the hard caps: >= 0.5 s apart (<= 2 per second), none in the first 2 s of a long video,
        none during a HUD or exhibit readout, only at designated moments (the caller passes impact / hook beats)."""
        out = []
        for t in sorted(float(b) for b in beats):
            if self.long and t < 2.0: continue
            if any(a <= t <= b for a, b in self.hud_spans): continue
            if out and t - out[-1] < 1.0 / PULSE_MAX_RATE: continue
            out.append(t)
        return out
    def _shot_at(self, t):
        for i, (a, b) in enumerate(self.spans):
            if a <= t < b: return i
        return len(self.spans) - 1 if self.spans else 0
    def _info(self, i, fr):
        if i in self.shot_info: return self.shot_info[i]
        s = self.shots[i] if i < len(self.shots) else {}
        txt = " ".join(str(x) for x in (s.get("prompt", ""), self.units[i].get("text", "") if i < len(self.units) else "", s.get("mood", "")))
        m = moods_of(txt); imp = bool(s.get("impact"))
        lvl = level_for(self.plan.get("intensity", 1), m, imp)
        small = cv2.resize(fr, (self.qs, self.qh)).astype(np.float32); lum = small.mean(axis=2)
        by, bx = np.unravel_index(np.argmax(cv2.GaussianBlur(lum, (0, 0), 6)), lum.shape)
        hue = cv2.cvtColor(cv2.resize(fr, (8, 8)), cv2.COLOR_BGR2HSV)[..., 0].mean()
        tint = np.array({"fire": (60, 120, 230), "hot": (90, 150, 220), "cold": (230, 200, 170), "space": (200, 140, 120), "underwater": (190, 160, 60)}.get(
            next(iter(sorted(m)), ""), (200, 200, 205)), np.float32)
        kind = "embers" if m & {"fire", "hot"} else "snow" if "cold" in m else "rain" if "rain" in m else "space" if "space" in m else "sparks" if imp else "dust"
        rng = np.random.default_rng(_seed(self.seed, "shot", i))
        parts = [{"xy": rng.random((n, 2)).astype(np.float32), "v": np.array(v, np.float32), "r": r, "layer": L}
                 for L, n, v, r in (("far", 26, (0.004, -0.002), 1), ("mid", 16, (0.008, -0.004), 2), ("near", 8, (0.014, -0.006), 3))]
        info = {"lvl": lvl, "moods": m, "anchor": (bx / self.qs, by / self.qh), "tint": tint, "kind": kind, "parts": parts, "impact": imp, "hue": hue}
        self.shot_info[i] = info; return info
    # ------------------------------------------------------------------ the frame
    def apply(self, fr, g):
        t0 = time.perf_counter()
        if self._last is not None: self._base += max(0.0, t0 - self._last)
        try: out = self._apply(fr, g)
        finally:
            el = time.perf_counter() - t0; self.spent += el; self.frames += 1; self._last = time.perf_counter()
            if self.frames % 120 == 0: self._budget()
        return out
    def _budget(self):
        """Above ATMOSPHERE_MAX_OVERHEAD_PCT of the rest of the frame pipeline: drop the next layer in DEGRADE_ORDER (logged)."""
        if self._base <= 0: return
        pct = 100.0 * self.spent / self._base
        if pct > S("ATMOSPHERE_MAX_OVERHEAD_PCT", float):
            nxt = next((k for k in DEGRADE_ORDER if self.flags.get(k)), None)
            if nxt:
                self.flags[nxt] = False; self.dropped.append(nxt)
                log(f"atmosphere over its time budget ({pct:.0f}% > {S('ATMOSPHERE_MAX_OVERHEAD_PCT')}%) - {nxt.lower()} switched off for the rest of the render", "WARN")
            self.spent = 0.0; self._base = 0.0
    def overhead_pct(self): return 100.0 * self.spent / self._base if self._base > 0 else 0.0
    def _apply(self, fr, g):
        """Fast path: every soft layer is computed at QUARTER resolution into one signed light layer, upscaled ONCE and added; full-resolution work is
        limited to cheap OpenCV ops (one add, an optional cached remap for shimmer, a radial channel scale for chromatic aberration, AA dots)."""
        t = g / self.fps; i = self._shot_at(t); inf = self._info(i, fr)
        lvl = inf["lvl"]
        if lvl <= 0: return fr
        k = lvl / 3.0
        small = cv2.resize(fr, (self.qs, self.qh), interpolation=cv2.INTER_LINEAR).astype(np.float32); lum = small.mean(axis=2) / 255.0
        depth = np.clip(0.55 * self._yy + 0.45 * cv2.GaussianBlur(lum, (0, 0), 8), 0, 1)              # far ~ top / brighter haze: a PROXY
        add = np.zeros((self.qh, self.qs, 3), np.float32)
        if self.flags["GODRAYS"]:
            ax, ay = inf["anchor"]; ax += 0.02 * math.sin(t * 0.3); ay += 0.015 * math.cos(t * 0.23)
            hi = np.clip((lum - 0.6) * 2.5, 0, 1)[..., None] * small
            acc = np.zeros_like(small); cx, cy = ax * self.qs, ay * self.qh
            for st in range(1, 7):
                z = 1 + 0.045 * st; M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
                acc += cv2.warpAffine(hi, M, (self.qs, self.qh), flags=cv2.INTER_LINEAR) * (1 - st / 8)
            add += acc / 6.0 * 0.35 * k * (1.0 + 0.03 * math.sin(t * 2 * math.pi * 0.5))
            band = np.clip(1 - np.abs((self._xx / self.qs + self._yy * 0.6) - ((t * 0.05) % 1.6)) * 6, 0, 1)
            add += (band * (1 - depth) * 10 * k)[..., None]
        if self.flags["FOG"] and (lvl >= 2 or inf["moods"]):
            n = np.roll(self.noise[0], int(t * 6) % self.qs, axis=1) * 0.6 + np.roll(self.noise[1], int(-t * 3) % self.qs, axis=1) * 0.4
            dens = (n * depth)[..., None] * 0.12 * k
            add += (inf["tint"][None, None, :] - small) * dens
        if self.flags["AURA"]:
            r = inf.setdefault("_r", np.sqrt(((self._xx - inf["anchor"][0] * self.qs) / self.qs) ** 2 + ((self._yy2 - inf["anchor"][1] * self.qh) / self.qh) ** 2))
            add += (np.exp(-(r / 0.16) ** 2) * 14 * k)[..., None] * np.array([1.0, 0.95, 0.85], np.float32)
            if lvl >= 3:
                ang = inf.setdefault("_ang", np.arctan2(self._yy2 - inf["anchor"][1] * self.qh, self._xx - inf["anchor"][0] * self.qs))
                add += (((np.sin(ang * 5 + r * 40 - t * 2.0) > 0.92) * np.exp(-(r / 0.3) ** 2)) * 18)[..., None].astype(np.float32)
        if self.flags["LENS"]:
            z = 1 + 0.012 * k; M = np.float32([[z, 0, self.qs / 2 * (1 - z)], [0, z, self.qh / 2 * (1 - z)]])          # radial chromatic aberration:
            rs = cv2.warpAffine(small[..., 2], M, (self.qs, self.qh), borderMode=cv2.BORDER_REPLICATE)                  # red fringe grows to the edges
            add[..., 2] += (rs - small[..., 2]) * 0.5 * self._edge
            hi2 = np.clip(small - 200, 0, 55)
            add += cv2.blur(hi2, (max(3, self.qs // 6), 1)) * np.array([1.0, 0.8, 0.6], np.float32) * 0.6 * k        # anamorphic streaks
            add += cv2.GaussianBlur(hi2, (0, 0), 4) * np.array([0.3, 0.4, 0.9], np.float32) * 0.4 * k                 # halation
        if self.flags["BREATH"] and inf["moods"] & {"cold", "hot"}:
            a0 = next((a for a, b in self.recon if a <= t < b), None)
            if a0 is not None:
                e = max(0.0, 1.0 - (t - a0) / 2.5)
                if e > 0:
                    w = (e * 0.35 * k * self._yy[..., None]); add += (cv2.GaussianBlur(small, (0, 0), 3) * 0.7 + 255 * 0.3 - small) * w
        add *= self._pmask
        np.clip(add, -255 * MAX_GAIN, 255 * MAX_GAIN, out=add)
        pos = cv2.resize(np.clip(add, 0, 255).astype(np.uint8), (self.W, self.H), interpolation=cv2.INTER_LINEAR)       # uint8 at full size: SIMD-fast
        neg = cv2.resize(np.clip(-add, 0, 255).astype(np.uint8), (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        out = cv2.subtract(cv2.add(fr, pos), neg)
        if self.flags["SHIMMER"] and inf["moods"] & {"fire", "hot"}:                                   # heat shimmer: bands of rows shifted 0-2 px
            bh = max(2, self.H // 135); amp = 1.0 + 1.0 * k
            for y0 in range(int(self.H * 0.35), self.H, bh):                                               # the lower (near / hot) part only
                d = int(round(amp * math.sin(y0 / 9.0 + t * 7.0)))
                if d: out[y0:y0 + bh] = np.roll(out[y0:y0 + bh], d, axis=1)

        if self.flags["PARTICLES"]:
            self._particles(out, inf, t, depth)
        if self.flags["PULSE"]:
            out = self._pulse(out, t)
        return out
    def _particles(self, img, inf, t, depth):
        """Antialiased dots / streaks drawn straight onto the frame; never inside the protected boxes; far motes only in the far zone (depth proxy)."""
        col = {"embers": (60, 150, 255), "snow": (250, 250, 250), "rain": (210, 200, 190), "space": (255, 240, 220), "sparks": (120, 220, 255), "dust": (200, 215, 225)}[inf["kind"]]
        n_on = max(1, int(round(inf["lvl"])))
        for P in inf["parts"][-n_on:] if n_on < 3 else inf["parts"]:
            v = P["v"] * (2.2 if inf["kind"] == "rain" else 1.0) * (-1 if inf["kind"] in ("snow", "rain") else 1)
            xy = (P["xy"] + v[None, :] * t * self.fps / 3.0) % 1.0
            for x, y in xy:
                if self._pmask[min(int(y * self.qh), self.qh - 1), min(int(x * self.qs), self.qs - 1), 0] < 0.5: continue
                if P["layer"] == "far" and depth[min(int(y * self.qh), self.qh - 1), min(int(x * self.qs), self.qs - 1)] < 0.5: continue
                px, py = int(x * self.W), int(y * self.H); r = max(1, int(P["r"] * self.W / 1280))
                if inf["kind"] == "rain": cv2.line(img, (px, py), (px - 3, py + 14 * r), col, 1, cv2.LINE_AA)
                else: cv2.circle(img, (px, py), r, col, -1, cv2.LINE_AA)
    def _pulse(self, img, t):
        """Hue/saturation/bloom pulse: 0.25 s ease-out after each allowed beat; luminance gain <= PULSE_MAX_SWING; the red channel never rises."""
        for p in self.pulses:
            d = t - p
            if 0 <= d < 0.25:
                a = PULSE_MAX_SWING * (1 - d / 0.25)
                r = img[..., 2].copy(); img = cv2.convertScaleAbs(img, alpha=1 + a); img[..., 2] = np.minimum(img[..., 2], r)
                self.pulse_log.append((round(p, 3), round(a, 4)))
                break
        return img

def pulse_qc(atm):
    """Hard caps re-checked on what was actually drawn: rate <= 2/s, swing <= 8 %, none in the first 2 s, none in a HUD readout."""
    out = []; ps = sorted({p for p, _ in atm.pulse_log})
    if any(b - a < 1.0 / PULSE_MAX_RATE - 1e-6 for a, b in zip(ps, ps[1:])): out.append(("pulse_rate", "pulses closer than 0.5 s"))
    if any(a > PULSE_MAX_SWING + 1e-6 for _, a in atm.pulse_log): out.append(("pulse_swing", "pulse above 8 % luminance"))
    if atm.long and any(p < 2.0 for p in ps): out.append(("pulse_early", "pulse in the first 2 s"))
    if any(x <= p <= y for p in ps for x, y in atm.hud_spans): out.append(("pulse_hud", "pulse during a HUD / exhibit readout"))
    return out

def lighting_directive(vertical=False):
    """g + j: appended to image prompts (the style lock stays in place). Fits inside IMAGE_PROMPT_MAX_CHARS together with the prompt."""
    d = ("Lighting: one motivated key light, crisp rim light, volumetric haze, high dynamic range, 35mm anamorphic lens. "
         "Composition: ONE dominant focal point that glows from within, low-angle or symmetrical hero framing, a clear diagonal or centred axis, "
         "an iconic silhouette, one dominant hue plus one accent hue")
    return d + (", vertical 9:16 framing with the subject in the centre third." if vertical else ".")

def with_directive(prompt, max_chars=None, vertical=False):
    """The prompt + the directive, never longer than max_chars: the DIRECTIVE is shortened first, never the prompt or its style lock."""
    mx = int(max_chars or S("IMAGE_PROMPT_MAX_CHARS", int)); d = lighting_directive(vertical); p = str(prompt or "").rstrip()
    room = mx - len(p) - 2
    if room <= 40: return p[:mx]
    if len(d) > room: d = d[:room].rsplit(" ", 1)[0].rstrip(",") + "."
    return p + ". " + d if not p.endswith(".") else p + " " + d
