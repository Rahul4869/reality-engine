"""whatifs/showfx.py v9 (stage 2) - the trial's signature devices, drawn by code at render time (zero API cost, deterministic per episode):
found-footage reconstruction stack (RECON exhibits + the cold open), the Survival HUD, the Jury Meter, exhibit pins with credits, Nana's teacup and
letterbox bars on hero moments. Plus the show QC (clip-bait, meter vs verdict, jury timing, teacup timing, photosensitivity).

Photosensitivity by construction: no full-frame flash is ever drawn here (exposure flicker <= 4 % luminance at <= 2 Hz, glitch bursts are horizontal slice
shifts of 2 frames at most once every 1.5 s and never within 1 s of an impact, the REC dot is a small area, nothing flashes red). QC still measures the
finished master (max 3 luminance flashes per second, no large-area red flashing)."""
from __future__ import annotations
import json, math, random, re
import numpy as np
import cv2
from PIL import Image, ImageDraw
from whatifs.core import S, log
from whatifs.media import font

def _tags(u): return [str(x).upper() for x in (u.get("show") or [])]

def events(units):
    """Show events in time order from the voiced timeline: (t, kind, value)."""
    out = []
    if isinstance(units, dict): units = units.get("units") or []
    for u in units:
        if not isinstance(u, dict): continue
        t = float(u.get("start", 0))
        for tg in _tags(u):
            m = re.match(r"\[METER\s*([+-]?\d+)\s+(GRIMM|VALE)\]", tg)
            if m: out.append((t, "meter", abs(int(m.group(1))) * (1 if m.group(2) == "VALE" else -1)))
            m = re.match(r"\[EXHIBIT\s+([A-H])\]", tg)
            if m: out.append((t, "exhibit", m.group(1)))
            if tg == "[JURY]": out.append((t, "jury", 1))
            if tg == "[CLIPBAIT]": out.append((t, "clip_open", 1))
            if tg == "[/CLIPBAIT]": out.append((float(u.get("end", t)), "clip_close", 1))
    return sorted(out, key=lambda e: e[0])

def recon_spans(units, plan, total):
    """Time spans shown as found-footage reconstruction: the cold open (until the first exhibit, at most 25 s) and every RECON exhibit until the next exhibit."""
    kinds = {e["id"]: e["kind"] for e in (plan or {}).get("exhibits", [])}
    ev = [(t, v) for t, k, v in events(units) if k == "exhibit"]
    spans = [(0.0, min(25.0, ev[0][0] if ev else 25.0, total))]
    for n, (t, x) in enumerate(ev):
        if kinds.get(x) == "RECON": spans.append((t, ev[n + 1][0] if n + 1 < len(ev) else min(total, t + 30.0)))
    return [(a, b) for a, b in spans if b - a > 0.5]

def teacup_plan(spans, plan, ww, wh, seed, total):
    """2-4 hidden teacups (t, x, y, scale): inside reconstruction spans, never before 30 s, kept to the outer thirds (never over the centre evidence or the
    bottom-left exhibit pin). Deterministic per episode; logged with the episode."""
    rng = random.Random(f"{seed}|teacup"); out = []
    cand = [(max(30.0, a), b) for a, b in spans if b - max(30.0, a) >= 3.0]
    want = max(0, min(4, len((plan or {}).get("teacup_scenes") or []) or 2))
    for a, b in cand[: max(want, 2)]:
        if len(out) >= want: break
        t = round(rng.uniform(a, b - 2.5), 2); right = rng.random() < 0.5
        x = int(ww * (rng.uniform(0.72, 0.9) if right else rng.uniform(0.62, 0.7))); y = int(wh * rng.uniform(0.15, 0.45))
        out.append({"t": t, "x": x, "y": y, "scale": round(rng.uniform(0.035, 0.05), 3)})
    return out[:4] if len(out) >= 2 or not cand else out

def _teacup_sprite(h):
    """A small floral teacup on a saucer, drawn with Pillow (RGBA)."""
    w = int(h * 1.5); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, int(h * 0.78), w - 1, h - 1), fill=(235, 230, 220, 230))
    d.chord((int(w * 0.12), int(h * 0.15), int(w * 0.78), int(h * 0.95)), 0, 180, fill=(245, 240, 232, 240))
    d.rectangle((int(w * 0.12), int(h * 0.15), int(w * 0.78), int(h * 0.55)), fill=(245, 240, 232, 240))
    d.arc((int(w * 0.7), int(h * 0.25), int(w * 0.98), int(h * 0.62)), 270, 90, fill=(245, 240, 232, 240), width=max(2, h // 12))
    for k in range(3): d.ellipse((int(w * (0.22 + 0.17 * k)), int(h * 0.3), int(w * (0.3 + 0.17 * k)), int(h * 0.42)), fill=(190, 80, 110, 230))
    return np.array(im)

class ShowOverlay:
    """One overlay for the whole video (apply(frame, global_frame)). Layers bottom to top: found footage, letterbox, teacup, HUD, exhibit pin, meter."""
    def __init__(self, units, plan, ww, wh, fps, seed="ep", hero_spans=None, impacts=None, portraits=None):
        self.units, self.plan, self.W, self.H, self.fps = units, plan or {}, ww, wh, fps
        self.total = max([float(u.get("end", 0)) for u in units] or [0.0])
        self.ev = events(units); self.seed = seed; self.s = wh / 1080.0
        self.recon = recon_spans(units, plan, self.total) if S("FOUND_FOOTAGE_ON", bool) else []
        self.it = int(self.plan.get("intensity", 1) or 0)
        self.hud = [h for h in (self.plan.get("hud_spec") or []) if isinstance(h, dict)] if S("HUD_ON", bool) else []
        self.impacts = list(impacts or []); self.hero = list(hero_spans or []) if S("LETTERBOX_ON", bool) else []
        self.cups = teacup_plan(self.recon, plan, ww, wh, seed, self.total) if S("TEACUP_ON", bool) else []
        self.kinds = {e["id"]: e for e in self.plan.get("exhibits", [])}
        self.meter_on = S("JURY_METER_ON", bool) and any(k == "meter" for _, k, _ in self.ev)
        y, x = np.ogrid[:wh, :ww]; r = np.sqrt(((x - ww / 2) / (ww / 2)) ** 2 + ((y - wh / 2) / (wh / 2)) ** 2)
        self.vig = np.clip(1 - 0.75 * np.clip(r - 0.4, 0, None) ** 1.4, 0, 1).astype(np.float32)[..., None]
        self.rng = np.random.default_rng(int(__import__("hashlib").sha256(str(seed).encode()).hexdigest()[:8], 16)); self._grain = [self.rng.normal(0, 7, (wh // 2, ww // 2, 1)).astype(np.float32) for _ in range(6)]      # v9.1 fix: a stable seed (hash() is salted per process)
        self.glitch_at = self._glitches(); self._cup = {}; self._font = {}
        self.spans = [(float(u.get("start", 0)), float(u.get("end", 0)), u.get("speaker")) for u in (units if isinstance(units, list) else []) if isinstance(u, dict)]
        ph = int(wh * 0.26)                                              # v9 character theatre (approved, locked portraits only): a framed portrait while that character speaks
        self.court = None
        if (portraits or {}).get("SET") is not None:                         # v9.1: the locked courtroom set (THEATER_STYLE = courtroom)
            s_ = portraits.pop("SET"); self.court = cv2.resize(s_, (int(ph * 16 / 9), ph))
        self.portraits = {k: cv2.resize(v, (int(v.shape[1] * ph / v.shape[0]), ph)) for k, v in (portraits or {}).items() if v is not None}
    def active(self): return bool(self.recon or self.hud or self.cups or self.meter_on or self.hero or self.kinds or self.portraits)
    def _f(self, px):
        px = max(10, int(px * self.s))
        if px not in self._font: self._font[px] = font(px)
        return self._font[px]
    def _glitches(self):
        """Glitch burst start times: only with intensity >= 2, inside reconstruction spans, at most one per 1.5 s, never within 1 s of an impact."""
        if self.it < 2: return []
        rng = random.Random(f"{self.seed}|glitch"); out = []
        for a, b in self.recon:
            t = a + 1.0
            while t < b - 0.5:
                if not any(abs(t - i) < 1.0 for i in self.impacts) and (not out or t - out[-1] >= 1.5): out.append(round(t, 2))
                t += rng.uniform(2.5, 6.0)
        return out
    def in_recon(self, t): return any(a <= t < b for a, b in self.recon)
    def meter_at(self, t):
        return sum(v for tt, k, v in self.ev if k == "meter" and tt <= t)
    def exhibit_at(self, t):
        cur = [(tt, v) for tt, k, v in self.ev if k == "exhibit" and tt <= t]
        return (cur[-1][1], t - cur[-1][0]) if cur else (None, 0)
    # ---- layers
    def _found_footage(self, fr, t, g):
        f = fr.astype(np.float32) * self.vig
        f *= 1.0 + 0.04 * math.sin(2 * math.pi * 1.7 * t) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.31 * t))      # auto-exposure drift: <= 4 %, < 2 Hz
        gr = cv2.resize(self._grain[g % 6], (self.W, self.H), interpolation=cv2.INTER_NEAREST)[..., None] if self._grain else 0
        f = np.clip(f + gr, 0, 255).astype(np.uint8)
        if any(0 <= t - s0 < 2.0 / self.fps for s0 in self.glitch_at):                   # 2-frame slice shift, no brightness change
            k = int((t * 1000) % 7) + 3; h = self.H // k
            for j in range(0, self.H, h * 2): f[j:j + h] = np.roll(f[j:j + h], int(self.W * 0.02), axis=1)
        if self.it >= 3:                                                                   # lens crack in the top-left corner
            cv2.line(f, (int(self.W * 0.02), int(self.H * 0.05)), (int(self.W * 0.14), int(self.H * 0.18)), (225, 225, 225), 1, cv2.LINE_AA)
            cv2.line(f, (int(self.W * 0.09), int(self.H * 0.11)), (int(self.W * 0.06), int(self.H * 0.24)), (205, 205, 205), 1, cv2.LINE_AA)
        if int(t * 2) % 2 == 0: cv2.circle(f, (int(self.W * 0.05), int(self.H * 0.07)), max(4, int(9 * self.s)), (40, 40, 220), -1, cv2.LINE_AA)   # REC dot, 1 Hz
        cv2.putText(f, "REC  " + f"{int(t // 3600):02d}:{int(t // 60) % 60:02d}:{int(t) % 60:02d}:{int((t % 1) * self.fps):02d}", (int(self.W * 0.075), int(self.H * 0.08)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7 * self.s, (235, 235, 235), max(1, int(2 * self.s)), cv2.LINE_AA)
        return f
    def _text(self, fr, xy, txt, px, col=(240, 240, 240), box=(0, 0, 0, 150)):
        im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        f = self._f(px); x0, y0, x1, y1 = d.textbbox(xy, txt, font=f); pad = int(10 * self.s)
        d.rectangle((x0 - pad, y0 - pad, x1 + pad, y1 + pad), fill=box); d.text(xy, txt, font=f, fill=col + (255,))
        return cv2.cvtColor(np.array(Image.alpha_composite(im, ov).convert("RGB")), cv2.COLOR_RGB2BGR)
    def apply(self, fr, g):
        t = g / self.fps
        if self.in_recon(t): fr = self._found_footage(fr, t, g)
        sp = next((s for a, b, s in self.spans if a <= t < b), None)
        if sp in self.portraits and not self.in_recon(t):                 # never over the reconstruction footage
            im = self.portraits[sp]
            from whatifs import v91 as V91
            if self.court is not None and V91.on("COURTROOM_ON"):           # v9.1: THEATER_STYLE = courtroom (locked set, deterministic cut to the speaker)
                from whatifs import herostill as HS
                im = HS.courtroom(self.court, self.portraits, sp, t)
            elif V91.on("CHAR_GRAMMAR_ON"):                                  # v9.1: the speaker's cinematic grammar on the portrait
                from whatifs import herostill as HS
                im = HS.apply_grammar(im, sp, t)
            h, w = im.shape[:2]; x0, y0 = self.W - w - int(self.W * 0.03), self.H - h - int(self.H * 0.12)
            if x0 > 0 and y0 > 0:
                fr[y0:y0 + h, x0:x0 + w] = im; cv2.rectangle(fr, (x0 - 2, y0 - 2), (x0 + w + 1, y0 + h + 1), (200, 200, 200), 2)
        if any(a <= t < b for a, b in self.hero):
            bh = int(self.H * 0.1); fr[:bh] = 0; fr[-bh:] = 0
        for c in self.cups:
            if c["t"] <= t < c["t"] + 2.5:
                h = max(12, int(self.H * c["scale"]))
                if h not in self._cup: self._cup[h] = _teacup_sprite(h)
                sp = self._cup[h]; y0, x0 = c["y"], c["x"]; hh, ww_ = sp.shape[:2]
                if y0 + hh < self.H and x0 + ww_ < self.W:
                    a = sp[..., 3:4].astype(np.float32) / 255 * 0.85; roi = fr[y0:y0 + hh, x0:x0 + ww_].astype(np.float32)
                    fr[y0:y0 + hh, x0:x0 + ww_] = (roi * (1 - a) + sp[..., [2, 1, 0]].astype(np.float32) * a).astype(np.uint8)
        cur = [h for h in self.hud if h["t"] <= t < h["t"] + 6.0]
        if cur:
            h = cur[-1]; v = h["value"]; vs = f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:.2f}"
            fr = self._text(fr, (int(self.W * 0.04), int(self.H * 0.13)), f"{h['label'].upper()}  {vs} {h.get('unit', '')}".strip(), 30, (120, 255, 170))
        x, age = self.exhibit_at(t)
        if x and age < 4.0 and S("EXHIBIT_PINS_ON", bool):
            e = self.kinds.get(x, {}); lab = "RECONSTRUCTION" if e.get("kind") == "RECON" else f"EXHIBIT {x}" + (f"  ·  {e.get('credit')}" if e.get("credit") else "")
            fr = self._text(fr, (int(self.W * 0.04), int(self.H * 0.86)), lab, 28, (250, 235, 200))
        if self.meter_on and t >= 3.0:
            m = max(-6, min(6, self.meter_at(t))); bw, bh = int(self.W * 0.26), max(8, int(14 * self.s)); x0, y0 = int(self.W * 0.70), int(self.H * 0.12)      # below the letterbox bars
            cv2.rectangle(fr, (x0, y0), (x0 + bw, y0 + bh), (40, 40, 40), -1)
            mid = x0 + bw // 2; pos = int(mid + (bw // 2) * m / 6)
            cv2.rectangle(fr, (min(mid, pos), y0), (max(mid, pos), y0 + bh), (190, 210, 80) if m > 0 else (60, 120, 255), -1)
            cv2.line(fr, (mid, y0 - 3), (mid, y0 + bh + 3), (240, 240, 240), 1)
            cv2.putText(fr, "GRIMM", (x0, y0 + bh + int(22 * self.s)), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * self.s, (60, 120, 255), 1, cv2.LINE_AA)
            cv2.putText(fr, "VALE", (x0 + bw - int(48 * self.s), y0 + bh + int(22 * self.s)), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * self.s, (190, 210, 80), 1, cv2.LINE_AA)
        return fr

# ---------------------------------------------------------------- QC (reported as problems; a failing check stops posting like every final-QC problem)
def show_qc(units, plan, cups=None):
    """[(code, detail)] for the show devices measured on the VOICED timeline (not word estimates)."""
    out = []; ev = events(units)
    op = [t for t, k, _ in ev if k == "clip_open"]; cl = [t for t, k, _ in ev if k == "clip_close"]
    if len(op) != 1 or len(cl) != 1: out.append(("clipbait", f"{len(op)} clip-bait segment(s); exactly one is needed"))
    elif not 0 < cl[0] - op[0] <= 8.5: out.append(("clipbait", f"clip-bait segment lasts {cl[0] - op[0]:.1f}s (6-8 s wanted)"))
    win = (plan or {}).get("verdict", {}).get("winner")
    tot = sum(v for _, k, v in ev if k == "meter"); end = "vale" if tot > 0 else "grimm" if tot < 0 else "split"
    if win and any(k == "meter" for _, k, _ in ev) and end != win: out.append(("meter_verdict", f"the meter ends on {end} but the verdict is {win}"))
    jury = [t for t, k, _ in ev if k == "jury"]
    if jury and min(jury) < 30.0: out.append(("jury_early", f"a jury prompt at {min(jury):.0f}s (not before 30 s)"))
    for c in cups or []:
        if c["t"] < 30.0: out.append(("teacup_early", f"teacup at {c['t']}s"))
    return out

def photosensitivity(path, max_flash=3, step=1):
    """Measured on the finished master: luminance flashes per second (a flash = an opposing pair of changes of >= 10 % of full scale in mean luminance)
    and large-area red flashing (a red-dominant frame share above 25 % alternating within a second). Returns [(code, detail, t)]."""
    cap = cv2.VideoCapture(path); fpsv = cap.get(cv2.CAP_PROP_FPS) or 30; lum, red = [], []; k = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if k % step == 0:
            sm = cv2.resize(fr, (64, 36)).astype(np.float32); lum.append(float((0.114 * sm[..., 0] + 0.587 * sm[..., 1] + 0.299 * sm[..., 2]).mean()))
            red.append(float(((sm[..., 2] > 150) & (sm[..., 2] > 2 * sm[..., 1]) & (sm[..., 2] > 2 * sm[..., 0])).mean()))
        k += 1
    cap.release(); out = []; n = int(round(fpsv / step))
    d = np.diff(np.array(lum)) if len(lum) > 1 else np.array([])
    big = [(i, 1 if x > 0 else -1) for i, x in enumerate(d) if abs(x) >= 25.5]
    flashes = [big[j][0] for j in range(1, len(big)) if big[j][1] != big[j - 1][1] and big[j][0] - big[j - 1][0] <= n // 3]
    for i in flashes:
        if sum(1 for x in flashes if i <= x < i + n) > max_flash: out.append(("photosensitive_flash", f"more than {max_flash} flashes in one second near {i / n:.1f}s", round(i / n, 1))); break
    rd = [1 if r > 0.25 else 0 for r in red]
    for i in range(0, max(0, len(rd) - n)):
        if sum(1 for j in range(i + 1, i + n) if rd[j] != rd[j - 1]) >= 4: out.append(("red_flash", f"large-area red flashing near {i / n:.1f}s", round(i / n, 1))); break
    return out

def audio_drop(master, units, out_dir, ep):
    """v9: the clip-bait moment as a 5-8 s audio drop (from the finished mix; zero cost). Returns the file path or None."""
    import os, subprocess
    ev = events(units); op = [t for t, k, _ in ev if k == "clip_open"]; cl = [t for t, k, _ in ev if k == "clip_close"]
    if len(op) != 1 or len(cl) != 1 or not 0 < cl[0] - op[0] <= 8.5: return None
    dur = max(5.0, cl[0] - op[0] + 0.3); p = os.path.join(out_dir, f"{ep}_drop.m4a")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0.0, op[0] - 0.15):.2f}", "-t", f"{dur:.2f}", "-i", master, "-vn", "-c:a", "aac", "-b:a", "160k",
                        "-af", "afade=t=in:d=0.05,afade=t=out:st=" + f"{max(0.0, dur - 0.3):.2f}" + ":d=0.3", p], capture_output=True)
    return p if r.returncode == 0 and os.path.exists(p) else None
