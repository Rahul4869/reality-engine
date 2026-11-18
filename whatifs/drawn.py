"""Drawn by code (D6): the house kit and its closed scene language - a scene is DATA (a template, its slots, its cue words), checked, expanded, laid out and timed here alone. See docs/CURRENT/SYSTEM.md."""
import math, re
from PIL import ImageFont
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
              "anti": "never for two quantities side by side (that is compare) or a number the line does not say"},
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
                "anti": "never for two values the line does not give to those two names, or for values of different units"},
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
             "anti": "never for two separate amounts (that is compare) or a part that is not inside its whole"},
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
