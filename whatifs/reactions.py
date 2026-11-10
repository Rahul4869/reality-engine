"""Reaction moments: a short voiced reaction plus original code-drawn effects that amplify the feeling. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import math, re, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw
from whatifs.core import S, safe_append
from whatifs import cta as CTA

REACT_TAGS = ("wow", "gasp", "awe", "laugh", "doubt")
_RANK = {"gasp": 0, "wow": 0, "awe": 0, "laugh": 1, "doubt": 2}
SFX_FOR = {"wow": "pop", "gasp": "gasp", "awe": "gasp", "laugh": "pop", "doubt": "huh"}
DEFAULT_WORD = {"wow": "WOW!!", "gasp": "WAIT!", "awe": "WHOA...", "laugh": "HA!", "doubt": "HUH?"}
COLOURS = {"wow": (255, 214, 0), "gasp": (255, 120, 60), "awe": (120, 200, 255), "laugh": (120, 230, 120), "doubt": (200, 200, 210)}
_LEAD = re.compile(r"^\W*([A-Za-z][A-Za-z']{1,11}[.!?…]*)")

def is_reaction(u): return u.get("speaker") == "SKEPTIC" and u.get("tag") in REACT_TAGS

_INTERJ = {"whoa", "woah", "wow", "wait", "no", "oh", "ohh", "ohhh", "ah", "ahh", "huh", "hm", "hmm", "yikes", "uh", "ha", "haha", "okay", "ok", "seriously", "really", "what", "nope",
           "wicked", "whoah", "ooh", "oooh", "jeez", "gosh", "dude", "nah", "yeah", "yes", "sweet", "cool", "damn", "ugh", "eek", "aw", "aww", "phew", "oof"}
def pop_word(text, kind):
    """The pop-up word is the first word of the spoken reaction ('Whoa!' -> WHOA!) when it is a real interjection, so picture and voice always agree.
    A line that opens with an ordinary word gets the default word for its kind instead of a random first word."""
    m = _LEAD.match(text or ""); w = (m.group(1) if m else "").strip()
    base = re.sub(r"[^a-z']", "", w.lower())
    if (text or "").lower().startswith("wait"): return "WAIT.."
    if base in _INTERJ and len(w) <= 12: return w.upper()
    return DEFAULT_WORD.get(kind, "WOW!!")

def find_events(units):
    """Reaction moments from the real narration timeline. At most REACTION_MAX, never closer than REACTION_GAP_SEC, strongest kinds first."""
    cand = [u for u in units if is_reaction(u)]
    cand.sort(key=lambda u: (_RANK.get(u["tag"], 3), u["start"]))
    chosen = []
    for u in cand:
        if len(chosen) >= S("REACTION_MAX", int): break
        if any(abs(u["start"] - c["start"]) < S("REACTION_GAP_SEC", float) for c in chosen): continue
        chosen.append(u)
    chosen.sort(key=lambda u: u["start"])
    return [{"i": u["i"], "t": round(float(u["start"]), 2), "end": round(float(u["end"]), 2), "kind": u["tag"], "word": pop_word(u["text"], u["tag"]), "line": u["text"][:80]} for u in chosen]

def peak_units(units):
    """Unit indexes directly BEFORE a reaction line. The big shots (Kling, living) belong here: the viewer sees the thing, then the Curious One reacts."""
    return [i for i in range(len(units) - 1) if is_reaction(units[i + 1]) and not is_reaction(units[i])]

def ensure_units(units):
    """Pre-voice safety net: if the writer tagged fewer than 3 reaction lines, tag up to 3 [SKEPTIC] lines that follow a reveal/tension line or a number.
    Only the delivery tag changes (pace and pause), never a word of the script. Used as the unit_hook of voice.narrate."""
    have = [i for i, u in enumerate(units) if is_reaction(u.__dict__ if hasattr(u, "__dict__") else u)]
    if len(have) >= 3: return units
    last = -99
    for i, u in enumerate(units):
        if len(have) >= 3: break
        if u.speaker != "SKEPTIC" or u.tag in REACT_TAGS or i - last < 12 or i == 0: continue
        if len(u.text.split()) > 9 or CTA.kind_of_text(u.text): continue      # v8.3: only a short, real interjection becomes a reaction, never a plain question or an audience ask
        prev = units[i - 1]
        if prev.tag in ("reveal", "tension") or re.search(r"\d", prev.text):
            u.tag = "wow" if len(have) % 2 == 0 else "gasp"; have.append(i); last = i
    return units

def sfx_events(events):
    """(sound kind, seconds) for render.score: the sound starts a hair before the spoken reaction so the picture, sound and voice hit together."""
    return [(SFX_FOR.get(e["kind"], "pop"), max(0.0, e["t"] - 0.04)) for e in events]

def map_rows(ep, events, total_sec=""):
    return [{"episode_id": ep, "t": e["t"], "kind": e["kind"], "word": e["word"], "line": e["line"], "style": "", "total_sec": total_sec} for e in events]

def record(ep, events, banter="", total_sec=""):
    if not events: return
    rows = map_rows(ep, events, round(float(total_sec), 1) if total_sec not in ("", None) else "")
    for r in rows: r["style"] = banter
    safe_append("Reaction_Map", rows)

# ---------------------------------------------------------------- the visual effect (drawn by code, blended into the frames)
class ReactionFX:
    """Punch-in zoom + comic burst + pop-up word for each reaction moment. Pure OpenCV / Pillow; no images from anywhere."""
    LEN = 1.0
    def __init__(self, events, ww, wh, fps):
        self.ev = [e for e in events]; self.W, self.H, self.fps = ww, wh, fps; self.s = wh / 1080.0; self._cache = {}
        from whatifs.media import font
        self.font = font(max(10, int(150 * self.s)))

    def active(self): return bool(self.ev)

    def _burst(self, kind, word):
        key = (kind, word)
        if key in self._cache: return self._cache[key]
        s = self.s; c = COLOURS.get(kind, (255, 214, 0)); d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tw = int(d0.textlength(word, font=self.font)); w = max(int(tw + 260 * s), int(560 * s)); h = int(430 * s)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        cx, cy, pts = w / 2, h / 2, []
        hv = int(hashlib.md5(f"{kind}{word}".encode()).hexdigest()[:4], 16); n_pts = (16, 20, 24, 28)[hv % 4]; tilt = (hv % 7) * 0.09     # v8.3: spike count and tilt vary
        for k in range(n_pts):                                # a comic burst (original shape)
            r = (0.50 if k % 2 == 0 else 0.34) * min(w, h * 1.25); a = math.pi * 2 * k / n_pts + tilt
            pts.append((cx + r * math.cos(a) * 1.15, cy + r * math.sin(a) * 0.80))
        d.polygon(pts, fill=c + (235,), outline=(20, 20, 24, 255))
        d.line(pts + [pts[0]], fill=(20, 20, 24, 255), width=max(3, int(8 * s)))
        d.text((cx - tw / 2, cy - self.font.size * 0.58), word, font=self.font, fill=(255, 255, 255, 255), stroke_width=max(3, int(9 * s)), stroke_fill=(20, 20, 24, 255))
        a = np.asarray(im); out = (a[..., :3][..., ::-1].astype(np.float32), a[..., 3:4].astype(np.float32) / 255.0)
        self._cache[key] = out; return out

    def _active(self, t):
        for e in self.ev:
            if e["t"] - 0.02 <= t <= e["t"] + self.LEN: return e, t - e["t"]
        return None, 0.0

    def apply(self, frame, gframe):
        t = gframe / float(self.fps); e, age = self._active(t)
        if e is None: return frame
        H, W = frame.shape[:2]
        k = max(0.0, 1.0 - age / 0.35) if age >= 0 else 0.0                         # punch-in: 1.0 -> 1.07 -> 1.0 over 0.35 s, with a tiny shake
        if k > 0:
            z = 1.0 + 0.07 * math.sin(min(1.0, age / 0.35) * math.pi) ; dx = int(math.sin(gframe * 2.1) * 5 * self.s * k); dy = int(math.cos(gframe * 1.7) * 4 * self.s * k)
            M = np.float32([[z, 0, (1 - z) * W / 2 + dx], [0, z, (1 - z) * H / 2 + dy]])
            frame = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        rgb, al = self._burst(e["kind"], e["word"]); h, w = al.shape[:2]
        if age < 0: return frame
        pop = 0.4 + 0.75 * min(1.0, age / 0.14) if age < 0.14 else (1.15 - 0.15 * min(1.0, (age - 0.14) / 0.12) if age < 0.26 else 1.0)    # scale-in with overshoot
        fade = 1.0 if age < self.LEN - 0.2 else max(0.0, (self.LEN - age) / 0.2)
        nw, nh = max(8, int(w * pop * 0.78)), max(8, int(h * pop * 0.78))
        rgb2 = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA); al2 = cv2.resize(al, (nw, nh), interpolation=cv2.INTER_AREA)
        if al2.ndim == 2: al2 = al2[..., None]
        x = int(W / 2 - nw / 2); y = int(H * 0.30 - nh / 2)
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + nw), min(H, y + nh)
        if x1 <= x0 or y1 <= y0: return frame
        a = al2[y0 - y:y1 - y, x0 - x:x1 - x] * fade; sub = frame[y0:y1, x0:x1].astype(np.float32)
        frame[y0:y1, x0:x1] = (sub * (1 - a) + rgb2[y0 - y:y1 - y, x0 - x:x1 - x] * a).astype(np.uint8)
        return frame

class Stack:
    """Several overlays in order (reaction effects first, so the speaker tag is never zoomed)."""
    def __init__(self, parts): self.parts = [p for p in parts if p is not None]
    def active(self): return bool(self.parts)
    def apply(self, frame, gframe):
        for p in self.parts: frame = p.apply(frame, gframe)
        return frame

# ---------------------------------------------------------------- learning: did viewers stay through the reactions?
def reaction_lessons(curve, events, total_sec, label=""):
    """curve = [(share of video 0..1, share of viewers still watching 0..1)]. For each reaction, viewers 4 s before vs 6 s after. Returns <= 2 lesson strings."""
    pts = sorted((float(a), float(b)) for a, b in curve)
    if len(pts) < 20 or not events or total_sec <= 0: return []
    def at(sec):
        r = min(1.0, max(0.0, sec / total_sec)); return min(pts, key=lambda p: abs(p[0] - r))[1]
    by = {}
    for e in events:
        t = float(e["t"]); b = at(max(0, t - 4)); a = at(min(total_sec, t + 6))
        if b > 0: by.setdefault(e["kind"], []).append(a / b)
    if not by: return []
    avg = {k: sum(v) / len(v) for k, v in by.items()}; best = max(avg, key=avg.get); worst = min(avg, key=avg.get); out = []
    out.append(f"{label}reactions: viewers kept {avg[best] * 100:.0f} percent of the audience through '{best}' reactions (best)" + (f" and {avg[worst] * 100:.0f} percent through '{worst}' (weakest)." if worst != best else "."))
    if avg[worst] < 0.96 and worst != best: out.append(f"{label}reactions: '{worst}' moments coincided with a drop; use them less or move them closer to the payoff.")
    return out[:2]
