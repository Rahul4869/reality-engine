"""whatifs/overlay.py v8.3 - the speaker tag: a small code-drawn chip (DIRECTOR / SKEPTIC) with animated level bars, shown while that role speaks.

Why: the two recurring roles must be recognisable on every video, but an image model cannot keep one face identical across 50 shots (faces drift and the
channel looks cheap). The tag gives the roles a stable identity for free: no image call, no face. Presenters are shown only as silhouettes, hands or
console glow (see format_engine). Pure Pillow + numpy; panels are cached per (role, bar levels), so a frame costs one tiny alpha blend.
"""
from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw
from whatifs.media import font

COLOURS = {"DIRECTOR": (80, 210, 190), "SKEPTIC": (255, 176, 40), "HOST_A": (120, 170, 255), "HOST_B": (255, 120, 160)}
NAMES = {"DIRECTOR": "THE DIRECTOR", "SKEPTIC": "THE CURIOUS ONE", "HOST_A": "HOST A", "HOST_B": "HOST B"}

class SpeakerTag:
    FADE = 0.25
    def __init__(self, units, ww, wh, fps):
        self.spans = [(float(u["start"]), float(u["end"]), u.get("speaker", "NARRATOR")) for u in units if u.get("speaker", "NARRATOR") in COLOURS]
        self.W, self.H, self.fps = ww, wh, fps; self.s = wh / 1080.0; self._cache = {}
        self.f = font(max(8, int(34 * self.s))); self.m = int(ww * 0.035)

    def active(self): return bool(self.spans)

    def _who(self, t):
        for a, b, spk in self.spans:
            if a - 0.05 <= t <= b + self.FADE: return spk, (1.0 if t <= b else max(0.0, 1.0 - (t - b) / self.FADE))
        return None, 0.0

    def _chip(self, spk, levels):
        key = (spk, levels)
        if key in self._cache: return self._cache[key]
        s = self.s; c = COLOURS[spk]; name = NAMES[spk]; d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        w = int(d0.textlength(name, font=self.f) + 150 * s); h = int(70 * s)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(12 * s), fill=(6, 8, 12, 170))
        d.rectangle([0, 0, int(8 * s), h], fill=c + (255,))
        for i, lv in enumerate(levels):
            bh = int((10 + 34 * lv / 5.0) * s); x = int((26 + i * 16) * s)
            d.rounded_rectangle([x, int(h / 2 - bh / 2), x + int(9 * s), int(h / 2 + bh / 2)], radius=int(3 * s), fill=c + (255,))
        d.text((int(100 * s), int(h / 2 - 20 * s)), name, font=self.f, fill=(255, 255, 255, 255))
        a = np.asarray(im); out = (a[..., :3][..., ::-1].astype(np.float32), a[..., 3:4].astype(np.float32) / 255.0)
        self._cache[key] = out; return out

    def apply(self, frame, gframe):
        t = gframe / float(self.fps); spk, k = self._who(t)
        if not spk or k <= 0: return frame
        levels = tuple(int(2.5 + 2.5 * math.sin(t * (7 + 2.3 * i) + i * 1.7)) for i in range(4))
        rgb, al = self._chip(spk, levels); H, W = frame.shape[:2]; h, w = al.shape[:2]
        x, y = self.m, H - h - int(H * 0.06)
        if x + w > W or y < 0: return frame
        sub = frame[y:y + h, x:x + w].astype(np.float32); a = al * k
        frame[y:y + h, x:x + w] = (sub * (1 - a) + rgb * a).astype(np.uint8)
        return frame


class CtaChip:
    """v8.3: a small code-drawn chip (heart + LIKE, bell + SUBSCRIBE, arrow + SHARE) at the bottom right while a like / subscribe / share line is spoken.
    Original icons drawn with shapes (no YouTube logo or UI is imitated). Pops in, pulses gently, fades out. The speaker chip stays at the bottom left."""
    FADE = 0.25
    NAMES = {"like": "LIKE", "subscribe": "SUBSCRIBE", "share": "SHARE"}
    COLOURS = {"like": (255, 96, 128), "subscribe": (255, 214, 0), "share": (80, 210, 190)}

    def __init__(self, units, ww, wh, fps):
        from whatifs.cta import kind_of_text
        self.spans = []
        for u in units:
            k = kind_of_text(u.get("text", ""))
            if k: self.spans.append((float(u["start"]), float(u["end"]) + 0.5, k))
        self.W, self.H, self.fps = ww, wh, fps; self.s = wh / 1080.0; self._cache = {}
        self.f = font(max(8, int(32 * self.s))); self.m = int(ww * 0.035)

    def active(self): return bool(self.spans)

    def _which(self, t):
        for a, b, k in self.spans:
            if a - 0.1 <= t <= b + self.FADE:
                return k, (1.0 if t <= b else max(0.0, 1.0 - (t - b) / self.FADE)), min(1.0, (t - (a - 0.1)) / 0.25), (t - a)
        return None, 0.0, 0.0, 0.0

    def _icon(self, d, kind, cx, cy, r, col, pulse):
        r = r * (1.0 + 0.08 * pulse)
        if kind == "like":                                   # a heart: two circles and a triangle
            d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.1], fill=col); d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.1], fill=col)
            d.polygon([(cx - r * 0.97, cy - r * 0.18), (cx + r * 0.97, cy - r * 0.18), (cx, cy + r * 1.05)], fill=col)
        elif kind == "subscribe":                            # a bell: dome, flared body, clapper
            d.pieslice([cx - r * 0.7, cy - r * 1.0, cx + r * 0.7, cy + r * 0.4], 180, 360, fill=col)
            d.polygon([(cx - r * 0.7, cy - r * 0.3), (cx + r * 0.7, cy - r * 0.3), (cx + r * 1.0, cy + r * 0.55), (cx - r * 1.0, cy + r * 0.55)], fill=col)
            d.ellipse([cx - r * 0.25, cy + r * 0.6, cx + r * 0.25, cy + r * 1.05], fill=col)
        else:                                                # an arrow leaving a box
            d.polygon([(cx - r * 0.1, cy - r * 1.0), (cx + r * 1.0, cy - r * 0.1), (cx - r * 0.1, cy + r * 0.8), (cx - r * 0.1, cy + r * 0.35),
                       (cx - r * 0.9, cy + r * 0.55), (cx - r * 0.55, cy - r * 0.1), (cx - r * 0.1, cy - r * 0.35)], fill=col)

    def _chip(self, kind, pulse_q):
        key = (kind, pulse_q)
        if key in self._cache: return self._cache[key]
        s = self.s; c = self.COLOURS[kind]; name = self.NAMES[kind]; d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        w = int(d0.textlength(name, font=self.f) + 128 * s); h = int(70 * s)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(12 * s), fill=(6, 8, 12, 178))
        d.rectangle([w - int(8 * s), 0, w, h], fill=c + (255,))
        self._icon(d, kind, int(46 * s), int(h / 2), 20 * s, c + (255,), (pulse_q - 2) / 2.0)
        d.text((int(84 * s), int(h / 2 - 19 * s)), name, font=self.f, fill=(255, 255, 255, 255))
        a = np.asarray(im); out = (a[..., :3][..., ::-1].astype(np.float32), a[..., 3:4].astype(np.float32) / 255.0)
        self._cache[key] = out; return out

    def apply(self, frame, gframe):
        t = gframe / float(self.fps); kind, k, pop, age = self._which(t)
        if not kind or k <= 0: return frame
        pq = int(2 + 2 * math.sin(max(0.0, age) * 6.0))                      # 0..4, a slow pulse
        rgb, al = self._chip(kind, pq); H, W = frame.shape[:2]; h, w = al.shape[:2]
        if pop < 1.0:                                                        # slide in from the right edge
            shift = int((1.0 - pop) ** 2 * w * 0.6)
        else: shift = 0
        x = W - w - self.m + shift; y = H - h - int(H * 0.06)
        if y < 0 or x + w <= 0 or x >= W: return frame
        x0, x1 = max(0, x), min(W, x + w); sx = x0 - x; ex = sx + (x1 - x0)
        sub = frame[y:y + h, x0:x1].astype(np.float32); a = al[:, sx:ex] * k
        frame[y:y + h, x0:x1] = (sub * (1 - a) + rgb[:, sx:ex] * a).astype(np.uint8)
        return frame
