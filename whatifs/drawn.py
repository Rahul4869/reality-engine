"""Drawn by code (D6): the house kit and its closed scene language - a scene is DATA (a template, its slots, its cue words), checked, expanded, laid out and timed here alone. See docs/CURRENT/SYSTEM.md."""
import math, re, time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from whatifs.media import font as _media_font, _fmt

# ---------------------------------------------------------------- the kit: the house look (module constants, not levers)
PALETTE = {"ink": (240, 244, 248), "dim": (170, 182, 194), "panel": (10, 14, 20), "a": (120, 220, 255), "b": (255, 190, 70)}      # a and b ARE the number card's two colours
SCRIM = 0.80                    # the blurred picture behind a scene is covered by `panel` at this opacity: every text colour keeps 4.5:1 on the worst ground
TYPE = {"title": 0.075, "value": 0.12, "label": 0.05}       # of the frame's HEIGHT
SAFE = 0.90                     # the title-safe rectangle, centred
GRID = (12, 6)                  # columns and rows inside it
STROKE = 0.008                  # of the height
DUR = {"draw": 0.6, "grow": 0.8, "count": 0.9, "pop": 0.35, "fade": 0.4}      # seconds
KINDS = ("bar", "ring", "dot", "box", "arrow", "line", "label", "value")
HOWS = ("draw", "grow", "count", "pop", "fade")
IN, GAP, EARLY, PULSE, TINT = 0.25, 0.3, 0.15, 0.5, 0.25   # the first step's start; the least room between two step starts; a step begins this long before its word; a pulse's length and its largest tint
CHARS = re.compile(r"^[A-Za-z0-9 .,%:;'!?()+\-x/&]*$")       # a slot or cue string: nothing else (C5: "://" and ".." are refused after the class)
NUM_MAX, CUES_MAX, CUE_LEN = 1e15, 6, 40
SWAP = {"’": "'", "‘": "'", "—": "-", "–": "-", "×": "x", "“": "'", "”": "'", '"': "'"}


class Refused(Exception):
    """A scene the kit cannot draw; the message is the reason."""


# ---------------------------------------------------------------- the five templates: the kit's visual cards, served to the writer word for word
# A slot's bound: an int N = a text of 1 to N characters (a slot named "unit" may be empty); "number" = a finite number; a dict = an object of
# exactly those keys; {"list": [lo, hi], "each": spec} = a list of lo to hi entries. The bounds: a box's width at 1920 x 1080 / 33.5 px a character.
TEMPLATES = {
    "count": {"use": "one quantity the line says, counted up on screen as the narrator says it",
              "feel": "scale: how big it is, in your own terms",
              "slots": {"label": 48, "from": "number", "to": "number", "unit": 16},
              "gold": {"v": 1, "template": "count", "variant": 0, "slots": {"label": "Pillows that float away tonight", "from": 0, "to": 8000000000, "unit": "pillows"},
                       "cues": ["pillows"]},
              "anti": "never for two quantities side by side (that is compare) or a number the line does not say, or a unit that does not stand right behind that number in the line"},
    "ladder": {"use": "two to five steps in the order the script tells them, each a time or place and what happens there",
               "feel": "escalation: each rung bigger than the last",
               "slots": {"label": 48, "rungs": {"list": [2, 5], "each": {"t": 14, "text": 34}}},
               "gold": {"v": 1, "template": "ladder", "variant": 0, "slots": {"label": "How high the pillows go", "rungs": [
                   {"t": "1 minute", "text": "Over the roofs"}, {"t": "1 hour", "text": "Past the planes"}, {"t": "1 day", "text": "Into space"}]}, "cues": []},
               "anti": "never for steps the script does not tell in this order, or for a single moment"},
    "compare": {"use": "two named quantities of one unit that the line sets side by side",
                "feel": "scale and awe: how much bigger one is than the other",
                "slots": {"label": 48, "unit": 8, "a": {"name": 22, "value": "number"}, "b": {"name": 22, "value": "number"}},
                "gold": {"v": 1, "template": "compare", "variant": 0, "slots": {"label": "How far away they are", "unit": "km",
                         "a": {"name": "The Moon", "value": 384000}, "b": {"name": "The Sun", "value": 150000000}}, "cues": []},
                "anti": "never for two values the line does not give to those two names, or for values of different units, or where no single sentence gives both values and no line says in digits how many times one is the other"},
    "flow": {"use": "two to four things where the line says that one causes the next, listed from cause to effect",
             "feel": "consequence: what happens next, step by step",
             "slots": {"label": 48, "links": {"list": [2, 4], "each": 34}},
             "gold": {"v": 1, "template": "flow", "variant": 0, "slots": {"label": "Why the cup falls", "links": ["The table tilts", "The cup slides", "The cup falls"]},
                      "cues": ["tilts", "slides", "falls"]},
             "anti": "never for things that only happen one after another: an arrow is drawn only where the line says one causes the next"},
    "part": {"use": "a share of a whole that the line names: the part, the whole and how much of it the part is",
             "feel": "you: how much of the whole is yours",
             "slots": {"label": 48, "part": {"name": 22, "value": "number"}, "whole": {"name": 22, "value": "number"}},
             "gold": {"v": 1, "template": "part", "variant": 0, "slots": {"label": "Your share of the air", "part": {"name": "Oxygen", "value": 21},
                      "whole": {"name": "All the air", "value": 100}}, "cues": []},
             "anti": "never for two separate amounts (that is compare) or a part that is not inside its whole, or where no line says the percentage itself in digits"},
}


# ---------------------------------------------------------------- the font: the kit's files, else a scalable default, else refused
_FONTS = {}


def font(px, bold=True):
    """The kit's font at `px` pixels: the files media.font tries, in its order (bold = Anton for title and value; Inter for a label); when none
    exists, the scalable default font; where that cannot be sized (Pillow 10.0): Refused("no scalable font on this machine")."""
    px = max(1, int(round(px)))
    if (px, bold) not in _FONTS:
        f = _media_font(px, bold)
        if getattr(f, "size", None) != px:                      # media.font found no file: it fell back to the unsized default
            try: f = ImageFont.load_default(size=px)
            except TypeError: raise Refused("no scalable font on this machine")
        _FONTS[(px, bold)] = f
    return _FONTS[(px, bold)]


# ---------------------------------------------------------------- the language: clean, from_graphic, expand
def _check(spec, val, key):
    if spec == "number":
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or abs(val) > NUM_MAX: return f"not a number the kit can draw: {key}"
        return ""
    if isinstance(spec, int):
        if not isinstance(val, str): return f"not in the scene language: {key}"
        if len(val) > spec: return f"a text over its bound: {key}"
        if (not val and key != "unit") or not CHARS.match(val) or "://" in val or ".." in val: return f"not in the scene language: {key}"
        return ""
    if "list" in spec:
        lo, hi = spec["list"]
        if not isinstance(val, list) or not lo <= len(val) <= hi: return f"not in the scene language: {key}"
        for x in val:
            r = _check(spec["each"], x, key)
            if r: return r
        return ""
    if not isinstance(val, dict): return f"not in the scene language: {key}"
    for k in val:
        if k not in spec: return f"not in the scene language: {k}"
    for k in spec:
        if k not in val: return f"a missing slot: {k}"
        r = _check(spec[k], val[k], k)
        if r: return r
    return ""


def clean(scene):
    """(scene, "") when the scene is in the kit's closed language, else (None, reason). Nothing outside the kit can be expressed: a colour, a size
    and a time are never slots; any other key anywhere is refused."""
    if not isinstance(scene, dict): return None, "not in the scene language: not an object"
    for k in scene:
        if k not in ("v", "template", "variant", "slots", "cues"): return None, f"not in the scene language: {k}"
    for k in ("v", "template", "variant", "slots"):
        if k not in scene: return None, f"a missing slot: {k}"
    if type(scene["v"]) is not int or scene["v"] != 1: return None, "not in the scene language: v"
    t = scene["template"]
    if not isinstance(t, str) or t not in TEMPLATES: return None, f"an unknown template: {str(t)[:30]}"
    if type(scene["variant"]) is not int or scene["variant"] not in (0, 1): return None, "not in the scene language: variant"
    why = _check(TEMPLATES[t]["slots"], scene["slots"], "slots")
    if why: return None, why
    s = scene["slots"]
    if t == "compare" and not (s["a"]["value"] > 0 and s["b"]["value"] > 0 and s["a"]["value"] != s["b"]["value"]): return None, "a compare needs two different values above 0"
    if t == "part" and not (0 < s["part"]["value"] < s["whole"]["value"]): return None, "a part must be above 0 and under its whole"
    cues = scene.get("cues", [])
    if not isinstance(cues, list) or len(cues) > CUES_MAX: return None, "not in the scene language: cues"
    for c in cues:
        if not isinstance(c, str) or len(c) > CUE_LEN or not CHARS.match(c) or "://" in c or ".." in c: return None, "not in the scene language: cues"
    return scene, ""


class _Over(Exception): pass
class _Char(Exception): pass


def _norm(x, bound, cut=False):
    s = str(x if x is not None else "")
    for a, b in SWAP.items(): s = s.replace(a, b)
    s = " ".join(s.split())
    if len(s) > bound:
        if not cut: raise _Over(s)
        i = s.rfind(" ", 0, bound + 1)                          # only a LABEL is cut, at its last space inside the bound (C4)
        if i <= 0: raise _Over(s)
        s = s[:i].rstrip()
    bad = [c for c in s if not CHARS.match(c)]
    if bad: raise _Char(bad[0])
    return s


def from_graphic(g):
    """The code's own scene of a clean Director graphic: counter -> count, timeline -> ladder, compare -> compare, with the graphic's own fields and
    no cues. (scene, "") or (None, reason) - the number card stays. Quotes and dashes are made plain; only the label is cut, at its last space."""
    if not isinstance(g, dict): return None, "no graphic"
    kind = g.get("kind")
    try:
        if kind == "counter":
            t, s = "count", {"label": _norm(g.get("label"), 48, cut=True), "from": float(g.get("from", 0)), "to": float(g.get("to", 100)), "unit": _norm(g.get("unit"), 16)}
        elif kind == "timeline":
            t, s = "ladder", {"label": _norm(g.get("label"), 48, cut=True), "rungs": [{"t": _norm(e.get("t"), 14), "text": _norm(e.get("text"), 34)} for e in (g.get("events") or [])]}
        elif kind == "compare":
            a, b = g.get("a") or {}, g.get("b") or {}
            t, s = "compare", {"label": _norm(g.get("label"), 48, cut=True), "unit": _norm(g.get("unit"), 8),
                               "a": {"name": _norm(a.get("name"), 22), "value": float(a.get("value"))}, "b": {"name": _norm(b.get("name"), 22), "value": float(b.get("value"))}}
        else: return None, f"a graphic the kit has no template for: {str(kind)[:20]}"
    except _Over as e: return None, f"a text over its bound: {str(e)[:60]}"
    except _Char as e: return None, f"a character the kit cannot draw: {e}"
    except (TypeError, ValueError): return None, "a graphic the kit cannot read"
    return clean({"v": 1, "template": t, "variant": 0, "slots": s, "cues": []})


def _it(id_, kind, col, row, w, h, colour, **kw):
    return dict({"id": id_, "kind": kind, "at": [col, row], "span": [w, h], "colour": colour, "text": "", "value": 1.0, "of": 1.0}, **kw)


def _ratio_text(r): return f"{r:,.0f}x" if r >= 10 else f"{r:.1f}x"


def _pct_text(p): return f"{p:.0f}%" if p >= 10 else f"{p:.1f}%" if p >= 0.1 else f"{p:.2g}%"


def expand(scene):
    """The FREE FORM of a clean scene - the only thing the renderer draws: {"title", "items": [{id, kind, at, span, colour, text, value, of, ...}],
    "steps": [{show, how, cue}]}. Grid cells are (column, row) of GRID inside the safe area; a colour is a key of PALETTE, a size a key of TYPE,
    a time a key of DUR. The ratio badge and the percentage are COMPUTED here, never slots."""
    t, v, s = scene["template"], scene["variant"], scene["slots"]
    cues = list(scene.get("cues") or [])
    def cue(k): return cues[k] if k < len(cues) else ""
    items = [_it("title", "label", 0, 0, 12, 1, "a", text=s["label"], size="title", align="l")]
    steps = [{"show": ["title"], "how": "fade", "cue": ""}]
    if t == "count":
        txt = _fmt(float(s["to"]), s["unit"])
        val = _it("value", "value", *((0, 1.75, 12, 1.5) if v == 0 else (5, 2.5, 7, 1.25)), "ink", text=txt, size="value", value=float(s["to"]), of=float(s["from"]),
                  unit=s["unit"], runs=True, align="c" if v == 0 else "l")
        shape = _it("bar", "bar", 2, 4, 8, 0.3, "a") if v == 0 else _it("ring", "ring", 0, 1.25, 4, 4.5, "a")
        items += [val, shape]; steps.append({"show": ["value", shape["id"]], "how": "count", "cue": cue(0)})
    elif t == "ladder":
        rungs = s["rungs"]; n = len(rungs)
        rows = [2, 4] if n == 2 else [1 + k * 4 / (n - 1) for k in range(n)]
        for k, r in enumerate(rungs):
            y = rows[k]; ids = [f"t{k}", f"dot{k}", f"x{k}"]
            if v == 0:
                items += [_it(f"t{k}", "label", 0, y + 0.1, 3.4, 0.8, "b", text=r["t"], size="label", align="r"), _it(f"dot{k}", "dot", 3.5, y + 0.4, 0.2, 0.2, "a"),
                          _it(f"x{k}", "label", 3.8, y + 0.1, 8.2, 0.8, "ink", text=r["text"], size="label", align="l")]      # the finisher's DQ-1: boxes for DejaVuSans-Bold at the 5% minimum
            else:
                items += [_it(f"x{k}", "label", 0, y + 0.1, 8.2, 0.8, "ink", text=r["text"], size="label", align="r"), _it(f"dot{k}", "dot", 8.3, y + 0.4, 0.2, 0.2, "a"),
                          _it(f"t{k}", "label", 8.6, y + 0.1, 3.4, 0.8, "b", text=r["t"], size="label", align="l"),
                          _it(f"bar{k}", "bar", 0, y + 0.88, 12, 0.1, "a", value=float(k + 1), of=float(n), alpha=0.25)]
                ids.append(f"bar{k}")
            steps.append({"show": ids, "how": "pop" if v == 0 else "grow", "cue": r["t"]})
    elif t == "compare":
        a, b = s["a"], s["b"]; hi, lo = max(a["value"], b["value"]), min(a["value"], b["value"]); ratio = hi / lo
        def frac(x): return (math.log10(x) - math.log10(lo) + 0.35) / (math.log10(hi) - math.log10(lo) + 0.35) if ratio > 20 else x / hi
        for k, (e, col) in enumerate(((a, "a"), (b, "b"))):
            p = "ab"[k]
            if v == 0:
                y = 1 if k == 0 else 3
                items += [_it(f"name_{p}", "label", 0, y, 7, 0.7, "ink", text=e["name"], size="label", align="l"),
                          _it(f"bar_{p}", "bar", 0, y + 0.75, 6.75, 0.6, col, value=frac(e["value"])),
                          _it(f"val_{p}", "value", 7, y + 0.6, 5, 0.8, "ink", text=_fmt(e["value"], s["unit"]), size="value", align="l")]      # DQ-1: 22 characters
            else:
                x0 = 0 if k == 0 else 6
                items += [_it(f"val_{p}", "value", x0, 1.0, 6, 0.8, "ink", text=_fmt(e["value"], s["unit"]), size="value", align="c"),
                          _it(f"bar_{p}", "bar", x0 + 2, 1.9, 2, 3, col, value=frac(e["value"]), dir="up"),
                          _it(f"name_{p}", "label", x0, 5.0, 6, 0.8, "ink", text=e["name"], size="label", align="c")]
            steps.append({"show": [f"name_{p}", f"bar_{p}", f"val_{p}"], "how": "grow", "cue": e["name"]})
        items.append(_it("badge", "value", *((4, 5, 4, 1) if v == 0 else (4.5, 2.2, 3, 0.8)), "ink", text=_ratio_text(ratio), size="value", align="c"))
        steps.append({"show": ["badge"], "how": "pop", "cue": ""})
    elif t == "flow":
        links = s["links"]
        for k, x in enumerate(links):
            y = 1 + k * 1.2; col = 1 if v == 0 else (0 if k % 2 == 0 else 2); ids = [f"box{k}", f"link{k}"]
            items += [_it(f"box{k}", "box", col, y, 10, 0.8, "a"), _it(f"link{k}", "label", col + 0.25, y + 0.1, 9.5, 0.6, "ink", text=x, size="label", align="c")]
            if k:
                items.append(_it(f"arrow{k}", "arrow", 5.8, y - 0.4, 0.4, 0.4, "b")); ids.append(f"arrow{k}")
            steps.append({"show": ids, "how": "draw", "cue": cue(k)})
    elif t == "part":
        p, w = s["part"], s["whole"]; pct = _pct_text(100.0 * p["value"] / w["value"])
        if v == 0:
            items += [_it("whole", "ring", 0, 1.25, 4, 4.5, "dim"), _it("part", "ring", 0, 1.25, 4, 4.5, "a", value=float(p["value"]), of=float(w["value"])),
                      _it("pct", "value", 0.6, 3.0, 2.8, 1.0, "ink", text=pct, size="value", align="c"),
                      _it("name_w", "label", 5, 1.5, 7, 0.7, "dim", text=w["name"], size="label", align="l"), _it("val_w", "value", 5, 2.2, 7, 0.9, "ink", text=_fmt(w["value"], ""), size="value", align="l"),
                      _it("name_p", "label", 5, 3.4, 7, 0.7, "a", text=p["name"], size="label", align="l"), _it("val_p", "value", 5, 4.1, 7, 0.9, "a", text=_fmt(p["value"], ""), size="value", align="l")]
        else:
            items += [_it("whole", "bar", 0, 3.0, 12, 0.5, "dim"), _it("part", "bar", 0, 3.0, 12, 0.5, "a", value=float(p["value"]), of=float(w["value"])),
                      _it("name_p", "label", 0, 1.3, 7.5, 0.7, "a", text=p["name"], size="label", align="l"), _it("val_p", "value", 0, 2.0, 7.5, 0.9, "a", text=_fmt(p["value"], ""), size="value", align="l"),
                      _it("name_w", "label", 0, 3.7, 7.5, 0.7, "dim", text=w["name"], size="label", align="l"), _it("val_w", "value", 0, 4.4, 7.5, 0.9, "ink", text=_fmt(w["value"], ""), size="value", align="l"),
                      _it("pct", "value", 8, 1.4, 4, 1.4, "ink", text=pct, size="value", align="r")]
        steps += [{"show": ["whole", "name_w", "val_w"], "how": "draw", "cue": w["name"]}, {"show": ["part", "name_p", "val_p"], "how": "grow", "cue": p["name"]},
                  {"show": ["pct"], "how": "pop", "cue": ""}]
    return {"title": s["label"], "items": items, "steps": steps}


# ---------------------------------------------------------------- the layout and its timing (pure; measured before a frame exists)
def _cross(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _fit(it, box, H, lo):
    """(px, bold, tbox): the text at its TYPE size, shrunk by 5% a try down to `lo` pixels; a counting value fits its widest number of the run."""
    bw, bh = box[2] - box[0], box[3] - box[1]; key = it.get("size") or ("value" if it["kind"] == "value" else "label"); bold = key in ("title", "value")
    texts = [it["text"]] + ([_fmt(it["of"] + (it["value"] - it["of"]) * k / 10.0, it.get("unit", "")) for k in range(11)] if it.get("runs") else [])
    size = TYPE[key] * H
    while True:
        px = max(lo, size); f = font(px, bold)
        tw = max(f.getlength(x) for x in texts); asc, desc = f.getmetrics(); th = asc + desc
        if tw <= bw and th <= bh: break
        if px <= lo: raise Refused(f"a text does not fit: {it['text']}")
        size = px * 0.95
    al = it.get("align") or "c"
    x = box[0] if al == "l" else box[2] - tw if al == "r" else box[0] + (bw - tw) / 2
    y = box[1] + (bh - th) / 2; pad = 0.15 * px
    tb = [max(box[0], x - pad), max(box[1], y - pad), min(box[2], x + tw + pad), min(box[3], y + th + pad)]
    return int(round(px)), bold, [round(q, 2) for q in tb]


def _timing(steps, dur, cue_s, hold_max):
    n = len(steps); tail = min(1.2, 0.2 * dur); slot = (dur - IN - tail) / max(1, n)
    if n == 0 or slot <= 0: raise Refused("more steps than the line can show")
    t0 = [IN + k * slot for k in range(n)]; on = [min(DUR[s["how"]], 0.9 * slot) for s in steps]
    for k in range(n):
        c = cue_s[k] if cue_s and k < len(cue_s) else None
        if c is None: continue
        if ((t0[k - 1] + GAP) if k else 0.0) <= c - EARLY <= dur - tail - on[k]: t0[k] = c - EARLY
    for k in range(1, n): t0[k] = max(t0[k], t0[k - 1] + GAP)
    if t0[-1] + on[-1] > dur - tail + 1e-9: raise Refused("more steps than the line can show")
    gaps = [(t0[k], t0[k + 1]) for k in range(n - 1)] + [(t0[-1] + on[-1], dur)]
    pulses = []
    for g0, g1 in gaps:                                         # THE HOLD RULE: nothing stands still longer than hold_max + one pulse
        if g1 - g0 <= hold_max: continue
        j = 1
        while g0 + j * hold_max + PULSE / 2 < g1:
            pulses.append({"t": round(g0 + j * hold_max, 4), "peak": round(g0 + j * hold_max + PULSE / 2, 4)}); j += 1
    return [dict(s, t0=round(t0[k], 4), on=round(on[k], 4)) for k, s in enumerate(steps)], pulses


def layout(free, W, H, dur, cue_s, text_min, words_max, hold_max):
    """L: every item placed in pixels inside the safe area (each text fitted to its box at no less than text_min % of the height), the steps
    timed on the line (cue_s = seconds from the line's start per step, None where unknown) and the pulses of the hold rule. Raises Refused:
    a text that does not fit, two texts that overlap, a box outside the safe area, too many words, more steps than the line can show, a
    portrait frame."""
    W, H, dur = int(W), int(H), float(dur)
    if H > W: raise Refused("no portrait layout yet")
    sx, sy = W * (1 - SAFE) / 2, H * (1 - SAFE) / 2; cw, rh = W * SAFE / GRID[0], H * SAFE / GRID[1]; lo = float(text_min) * H / 100.0
    items, texts, words = [], [], 0
    for it in free["items"]:
        (c, r), (w, h) = it["at"], it["span"]
        box = [sx + c * cw, sy + r * rh, sx + (c + w) * cw, sy + (r + h) * rh]
        if box[0] < sx - 0.5 or box[1] < sy - 0.5 or box[2] > W - sx + 0.5 or box[3] > H - sy + 0.5: raise Refused("outside the safe area")
        p = dict(it, box=[round(q, 2) for q in box])
        if it.get("text"):
            px, bold, tb = _fit(it, box, H, lo)
            for q in texts:
                if _cross(q["box"], tb): raise Refused("two texts overlap")
            texts.append({"id": it["id"], "box": tb}); p.update(px=px, bold=bold, tbox=tb)
            if it["id"] != "title": words += len(it["text"].split())
        items.append(p)
    if words > int(words_max): raise Refused("too many words on screen")
    steps, pulses = _timing(free["steps"], dur, cue_s, float(hold_max))
    at = {i_: k for k, st in enumerate(steps) for i_ in st["show"]}
    for p in items: p["step"] = at.get(p["id"], 0)
    return {"W": W, "H": H, "dur": dur, "title": free.get("title", ""), "items": items, "steps": steps, "pulses": pulses, "texts": texts, "hold_max": float(hold_max)}


# ---------------------------------------------------------------- drawing: ONE seam for shapes; text always by PIL into an alpha mask
def ease(x):
    """The kit's one easing: e = 1 - (1 - x) ** 3, x clipped to 0..1."""
    x = min(1.0, max(0.0, float(x)))
    return 1 - (1 - x) ** 3


LANES = 16                      # v12 U1 (J 220): a reduced box's width is a multiple of 16 pixels of the frame - OpenCV's vector lanes (4, 8 or 16) then sum every pixel as the whole layer does

class Own:
    """The default drawing seam: rect, line, arc and poly on a float layer that keeps STRAIGHT colour beside its alpha (never premultiplied),
    drawn at twice the size with OpenCV's anti-aliased calls inside each shape's own box and reduced with INTER_AREA. v12 U1 (J 220): only the boxes its
    shapes touched are reduced (each widened to multiples of k), never the two whole layers; `reduced_px` counts the source pixels reduced a frame."""
    def __init__(self, W, H, k=2):
        self.W, self.H, self.k = int(W), int(H), int(k)
        self.col = np.zeros((self.H * k, self.W * k, 3), np.float32); self.alp = np.zeros((self.H * k, self.W * k), np.float32)
        self.boxes = []; self.reduced_px = 0

    def _roi(self, x0, y0, x1, y1, pad):
        k = self.k; a = max(0, int(math.floor(min(x0, x1) * k - pad))); b = max(0, int(math.floor(min(y0, y1) * k - pad)))
        c = min(self.W * k, int(math.ceil(max(x0, x1) * k + pad)) + 1); d = min(self.H * k, int(math.ceil(max(y0, y1) * k + pad)) + 1)
        return a, b, c, d

    def _put(self, roi, mask, rgb, a):
        x0, y0, x1, y1 = roi
        if x1 <= x0 or y1 <= y0: return
        k = self.k; q = k * LANES; b = (x0 // q * q, y0 // k * k, min(self.W * k, -(-x1 // q) * q), min(self.H * k, -(-y1 // k) * k))      # v12 U1 (J 220): the shape's own box,
        inside = lambda u, v: v[0] <= u[0] and v[1] <= u[1] and u[2] <= v[2] and u[3] <= v[3]                                             # widened to multiples of k (its width to LANES pixels)
        if not any(inside(b, o) for o in self.boxes): self.boxes = [o for o in self.boxes if not inside(o, b)] + [b]                          # a box inside another is reduced once
        m = mask.astype(np.float32) / 255.0 * float(a); al = self.alp[y0:y1, x0:x1]; na = al + m * (1 - al)
        cs = self.col[y0:y1, x0:x1]; nz = na > 1e-6
        mix = (cs * (al * (1 - m))[..., None] + np.asarray(rgb, np.float32)[None, None, :] * m[..., None])
        cs[nz] = mix[nz] / na[nz][:, None]; self.alp[y0:y1, x0:x1] = na

    def _pts(self, pts, roi): return np.int32([[(x * self.k - roi[0]) * 16, (y * self.k - roi[1]) * 16] for x, y in pts])

    def rect(self, x0, y0, x1, y1, rgb, a=1.0, width=0.0):
        w = max(1, int(round(width * self.k))) if width > 0 else -1; roi = self._roi(x0, y0, x1, y1, max(2, w + 2))
        mask = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), np.uint8); p = self._pts(((x0, y0), (x1, y1)), roi)
        cv2.rectangle(mask, tuple(int(v) for v in p[0]), tuple(int(v) for v in p[1]), 255, w, cv2.LINE_AA, 4); self._put(roi, mask, rgb, a)

    def line(self, pts, rgb, a=1.0, width=1.0):
        w = max(1, int(round(width * self.k))); xs, ys = [p[0] for p in pts], [p[1] for p in pts]; roi = self._roi(min(xs), min(ys), max(xs), max(ys), w + 2)
        mask = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), np.uint8); cv2.polylines(mask, [self._pts(pts, roi)], False, 255, w, cv2.LINE_AA, 4); self._put(roi, mask, rgb, a)

    def arc(self, cx, cy, r, a0, a1, rgb, a=1.0, width=1.0):
        w = max(1, int(round(width * self.k))); roi = self._roi(cx - r, cy - r, cx + r, cy + r, w + 2)
        mask = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), np.uint8); c = self._pts(((cx, cy),), roi)[0]
        cv2.ellipse(mask, (int(c[0]), int(c[1])), (int(r * self.k * 16), int(r * self.k * 16)), 0, a0, a1, 255, w, cv2.LINE_AA, 4); self._put(roi, mask, rgb, a)

    def poly(self, pts, rgb, a=1.0):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]; roi = self._roi(min(xs), min(ys), max(xs), max(ys), 2)
        mask = np.zeros((roi[3] - roi[1], roi[2] - roi[0]), np.uint8); cv2.fillPoly(mask, [self._pts(pts, roi)], 255, cv2.LINE_AA, 4); self._put(roi, mask, rgb, a)

    def result(self):
        """(colour RGB float, alpha float) at the layer's own size: premultiplied only for the reduction, straight again after it. v12 U1 (J 220): each
        shape's widened box is reduced alone (INTER_AREA, factor k); outside every box the layer keeps its cleared value - the frame is byte for byte
        the whole-layer reduction (tests/test_v12_u1fix_220.py keeps that reduction as its reference)."""
        k = self.k; pm = np.zeros((self.H, self.W, 3), np.float32); al = np.zeros((self.H, self.W), np.float32); n = 0
        for x0, y0, x1, y1 in self.boxes:
            a_ = self.alp[y0:y1, x0:x1]; sz = ((x1 - x0) // k, (y1 - y0) // k)
            pm[y0 // k:y1 // k, x0 // k:x1 // k] = cv2.resize(self.col[y0:y1, x0:x1] * a_[..., None], sz, interpolation=cv2.INTER_AREA)
            al[y0 // k:y1 // k, x0 // k:x1 // k] = cv2.resize(np.ascontiguousarray(a_), sz, interpolation=cv2.INTER_AREA); n += (x1 - x0) * (y1 - y0)
        self.reduced_px = n
        return pm / np.maximum(al, 1e-6)[..., None], al


def _tint(t, L):
    """The hold rule's pulse at second t: up to TINT, up for a quarter second and down for a quarter second around each peak."""
    return max([TINT * max(0.0, 1 - abs(t - p["peak"]) / (PULSE / 2)) for p in L["pulses"]] or [0.0])


def _mixc(c, to, w): return tuple(c[j] + (to[j] - c[j]) * w for j in range(3))


def _text_mask(it, text, px, bold):
    """(x, y, mask 0..1) of a text drawn alone at L's size inside its item box (placed as the layout placed it)."""
    f = font(px, bold); tw = f.getlength(text); asc, desc = f.getmetrics(); bx = it["box"]; al = it.get("align") or "c"
    x = bx[0] if al == "l" else bx[2] - tw if al == "r" else bx[0] + (bx[2] - bx[0] - tw) / 2; y = bx[1] + (bx[3] - bx[1] - asc - desc) / 2
    x0, y0 = int(math.floor(x)), int(math.floor(y)); im = Image.new("L", (int(math.ceil(tw)) + 4, asc + desc + 4), 0)
    ImageDraw.Draw(im).text((x - x0, y - y0), text, font=f, fill=255)
    return x0, y0, np.asarray(im, np.float32) / 255.0


def layer(L, t, draw=None):
    """The scene's own layer at second t, alone: (colour RGB float, alpha float) at L's size. Every item whose step has begun, drawn to the fraction
    e((t - t0) / on) of its step; the pulse tints every item on screen (C2). Shapes go through the seam `draw` (default Own); text is always PIL's."""
    W, H = L["W"], L["H"]; sd = draw(W, H) if draw is not None else Own(W, H); tau = _tint(t, L); sw = STROKE * H; texts = []
    for it in L["items"]:
        st = L["steps"][it.get("step", 0)]
        if t < st["t0"]: continue
        p = ease((t - st["t0"]) / max(1e-6, st["on"])); how = st["how"]; base = PALETTE[it["colour"]]
        rgb = _mixc(base, PALETTE["a"] if it["colour"] == "ink" else PALETTE["ink"], tau); a = float(it.get("alpha", 1.0))
        if it["kind"] in ("label", "value"):
            txt = _fmt(it["of"] + (it["value"] - it["of"]) * p, it.get("unit", "")) if (it.get("runs") and how == "count") else it["text"]
            texts.append((it, txt, rgb, a * (1.0 if how == "count" else p))); continue
        x0, y0, x1, y1 = it["box"]; fr = max(0.0, min(1.0, float(it["value"]) / float(it["of"] or 1)))
        grow = p if how in ("draw", "grow", "count") else 1.0; fade = p if how in ("fade", "pop") else 1.0
        if it["kind"] == "bar":
            if it.get("dir") == "up": sd.rect(x0, y1 - (y1 - y0) * fr * grow, x1, y1, rgb, a * fade)
            else: sd.rect(x0, y0, x0 + (x1 - x0) * fr * grow, y1, rgb, a * fade)
        elif it["kind"] == "ring":
            r = min(x1 - x0, y1 - y0) / 2 * 0.94; th = max(sw, 0.12 * r)
            sd.arc((x0 + x1) / 2, (y0 + y1) / 2, r - th / 2, -90, -90 + 360 * fr * grow, rgb, a * fade, th)
        elif it["kind"] == "dot":
            s = (0.6 + 0.4 * p) if how == "pop" else 1.0; r = min(x1 - x0, y1 - y0) / 2 * s; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            sd.poly([(cx + r * math.cos(q * math.pi / 16), cy + r * math.sin(q * math.pi / 16)) for q in range(32)], rgb, a * fade)
        elif it["kind"] == "box":
            sd.rect(x0, y0, x1, y1, _mixc(PALETTE["panel"], PALETTE["ink"], tau), a * p)
            per = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]; pts = [_lerp(per, j / 32.0) for j in range(int(round(32 * p)) + 1)]      # the outline draws itself
            if len(pts) >= 2: sd.line(pts, rgb, a, sw)
        elif it["kind"] in ("arrow", "line"):
            cx = (x0 + x1) / 2; tip = y0 + (y1 - y0) * grow; sd.line([(cx, y0), (cx, tip)], rgb, a, sw)
            if it["kind"] == "arrow" and grow > 0.5: hw = (x1 - x0) / 2; sd.poly([(cx - hw, tip - hw), (cx + hw, tip - hw), (cx, tip)], rgb, a)
    col, alp = sd.result() if hasattr(sd, "result") else Own(W, H).result()
    for it, txt, rgb, a in texts:                                # TEXT is composited by the layer itself, whatever the backend
        x, y, m = _text_mask(it, txt, it["px"], it.get("bold", False)); h, w = m.shape
        xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if xb <= xa or yb <= ya: continue
        mm = m[ya - y:yb - y, xa - x:xb - x] * a; al = alp[ya:yb, xa:xb]; na = al + mm * (1 - al); cs = col[ya:yb, xa:xb]; nz = na > 1e-6
        mix = cs * (al * (1 - mm))[..., None] + np.asarray(rgb, np.float32)[None, None, :] * mm[..., None]; cs[nz] = mix[nz] / na[nz][:, None]; alp[ya:yb, xa:xb] = na
    return col, alp


def _lerp(per, f):
    """The point at fraction f (0..1) along a closed rectangle's perimeter of four equal steps (a box's outline drawing itself)."""
    f = max(0.0, min(1.0, f)) * 4; k = min(3, int(f)); r = f - k; a, b = per[k], per[k + 1]
    return (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)


def frame(L, t, bg=None, push=0.0, draw=None):
    """One frame (H, W, 3) BGR uint8 at L's own size: the ground (bg = an RGB array already blurred, enlarged by 1 + 0.04 * push about its centre;
    else flat panel), the scrim, then the scene's layer."""
    W, H = L["W"], L["H"]
    if bg is None: g = np.empty((H, W, 3), np.float32); g[:] = PALETTE["panel"]
    else:
        g = np.asarray(bg, np.float32); z = 1 + 0.04 * max(0.0, float(push))
        if z > 1.0001:
            g = cv2.resize(g, (int(round(W * z)), int(round(H * z))), interpolation=cv2.INTER_LINEAR); ox, oy = (g.shape[1] - W) // 2, (g.shape[0] - H) // 2; g = g[oy:oy + H, ox:ox + W]
    g = g * (1 - SCRIM) + np.asarray(PALETTE["panel"], np.float32) * SCRIM
    col, alp = layer(L, t, draw)
    out = g * (1 - alp[..., None]) + col * alp[..., None]
    return cv2.cvtColor(np.clip(out + 0.5, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)


def proof(L, fps, hold_max, change_px=0.002, kit_min=0.90, budget_s=90.0):
    """On the ONE L the film is drawn from, on the flat panel: (a) IT MOVES - the longest run of samples (every half second, every step's end, every
    pulse's peak; each reduced to a width of 480) without a change of more than change_px of the pixels by more than 8 grey levels must stay within
    hold_max + 0.5 s; (b) IT FITS THE KIT - at the last sample outside every pulse, of the layer's pixels above alpha 0.5 the share within 24 levels
    of a PALETTE colour must be at least kit_min; (c) a time limit. Never raises for a failed measure: ok False and why."""
    t_start = time.monotonic(); dur = float(L["dur"])
    ts = sorted({round(min(dur, k * 0.5), 4) for k in range(int(dur / 0.5) + 1)} | {round(s["t0"] + s["on"], 4) for s in L["steps"] if s["t0"] + s["on"] <= dur}
                | {round(p["peak"], 4) for p in L["pulses"] if p["peak"] <= dur})
    prev = None; run0 = ts[0]; still = 0.0; n = 0
    for k, t in enumerate(ts):
        fr = frame(L, t); w = 480; g = cv2.cvtColor(cv2.resize(fr, (w, max(1, int(round(fr.shape[0] * w / fr.shape[1])))), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.int16)
        if prev is not None and float(np.mean(np.abs(g - prev) > 8)) > change_px: run0 = t
        still = max(still, t - run0); prev = g; n += 1
        if time.monotonic() - t_start > budget_s:
            return {"ok": False, "why": "over the time limit", "still_s": round(still, 2), "kit_pct": 0.0, "ms": round(1000 * (time.monotonic() - t_start) / max(1, n), 1)}
    quiet = [t for t in ts if _tint(t, L) == 0.0] or ts
    col, alp = layer(L, quiet[-1]); sel = alp > 0.5
    if sel.any():
        px_ = col[sel]; d = np.min(np.stack([np.max(np.abs(px_ - np.asarray(c, np.float32)), axis=1) for c in PALETTE.values()]), axis=0); kit = float(np.mean(d <= 24))
    else: kit = 0.0
    ms = round(1000 * (time.monotonic() - t_start) / max(1, n), 1); out = {"ok": True, "why": "", "still_s": round(still, 2), "kit_pct": round(kit, 4), "ms": ms}
    if still > hold_max + 0.5: out.update(ok=False, why=f"it stands still {still:.1f} s")
    elif kit < kit_min: out.update(ok=False, why=f"only {kit:.0%} of it is in the kit's colours")
    return out


def lum(grey):
    """Relative luminance (WCAG 2) of sRGB grey levels 0..255 (a number or an array)."""
    c = np.asarray(grey, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def ratio(l1, l2):
    """WCAG's contrast ratio of two relative luminances: (lighter + 0.05) / (darker + 0.05)."""
    a, b = max(float(l1), float(l2)), min(float(l1), float(l2))
    return (a + 0.05) / (b + 0.05)


def ink(gray, L):
    """The lowest contrast of a text of L on a grey frame of the FINISHED FILE (any size): per text, the mean luminance of its ink (the text drawn
    alone, reduced to the frame's size, above 0.5, eroded by one pixel) against its box's ground (the box minus the ink dilated by two pixels). A
    picture that does not carry our text gives about 1."""
    g = np.asarray(gray, np.float64); h, w = g.shape[:2]; sx, sy = w / float(L["W"]), h / float(L["H"]); low = None; k3 = np.ones((3, 3), np.uint8)
    for it in L["items"]:
        if not it.get("text") or not it.get("tbox"): continue
        x, y, m = _text_mask(it, it["text"], it["px"], it.get("bold", False)); full = np.zeros((L["H"], L["W"]), np.float32)
        ya, xa = max(0, y), max(0, x); yb, xb = min(L["H"], y + m.shape[0]), min(L["W"], x + m.shape[1])
        if xb > xa and yb > ya: full[ya:yb, xa:xb] = m[ya - y:yb - y, xa - x:xb - x]
        small = cv2.resize(full, (w, h), interpolation=cv2.INTER_AREA) > 0.5
        inkm = cv2.erode(small.astype(np.uint8), k3, iterations=1).astype(bool); near = cv2.dilate(small.astype(np.uint8), k3, iterations=2).astype(bool)
        b = it["tbox"]; box = np.zeros((h, w), bool); box[int(b[1] * sy):int(math.ceil(b[3] * sy)), int(b[0] * sx):int(math.ceil(b[2] * sx))] = True
        ground = box & ~near
        if not inkm.any() or not ground.any(): continue
        r = ratio(float(np.mean(lum(g[inkm]))), float(np.mean(lum(g[ground]))))
        low = r if low is None else min(low, r)
    return round(low, 2) if low is not None else 1.0
