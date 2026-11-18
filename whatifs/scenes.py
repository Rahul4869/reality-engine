"""Drawn by code (D6): which explaining moments of a long video carry a drawn scene - the arm, the writer's one call, the check that every word, number, pair and arrow is the script's own, the plan's report. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, re
from whatifs.core import S, log, store
from whatifs import drawn as DRAWN, media as MD
from whatifs.org import audience as AUD, layman as LAY

FORWARD = ("therefore", "which means", "that means", "makes", "causes", "leads to", "forces")      # and "so" only at a clause's start (after , ; or .)
BACK = ("because",)
STOP = ("the", "and", "but", "its", "this", "that", "these", "those", "with", "from", "into", "onto", "your", "you", "are", "was", "were", "has", "have", "had",
        "will", "would", "can", "could", "then", "than", "when", "what", "who")      # C1: never an anchor
_TOK = re.compile(r"\d[\d,]*(?:\.\d+)?|[a-z]+|[.,;:!?]")
_NUM = re.compile(r"\d[\d,]*\.?\d*")


def on(): return S("DRAWN_ON", bool)


def arm(ep):
    """Is this episode in the drawn arm? A hash of its id against DRAWN_SHARE_PCT (a lever): at four videos a month the share is true on average."""
    return int(hashlib.sha256(str(ep).encode()).hexdigest(), 16) % 100 < S("DRAWN_SHARE_PCT", int)


def opts(): return {"text_min": S("DRAWN_TEXT_MIN_PCT", float), "words_max": S("DRAWN_WORDS_MAX", int), "hold_max": S("DRAWN_HOLD_MAX_S", float)}


def _dur(units, i, total):
    a = float(units[i].get("start") or 0)
    b = float(units[i + 1].get("start") or 0) if i + 1 < len(units) else float(total or 0)
    return max(0.0, b - a)


def slots(shots, units, total):
    """The explaining moments: every shot after the first whose type is "graphic", whose graphic media.clean_graphic can draw, and whose line
    (its start to the next line's start) lasts at least DRAWN_MIN_S."""
    lo = S("DRAWN_MIN_S", float); out = []
    for i, s in enumerate(shots or []):
        if i < 1 or i >= len(units) or not isinstance(s, dict) or s.get("type") != "graphic": continue
        if MD.clean_graphic(s.get("graphic")) is None: continue
        if _dur(units, i, total) >= lo: out.append(i)
    return out


def _key(w): return re.sub(r"[^a-z0-9]", "", str(w or "").lower())


def cue_s(unit, phrase, dur=None):
    """The second, from the line's start, at which the phrase's first word is spoken: from the unit's timed words where it carries them (the reader
    living.render is given), else dur * k / n for the k-th (from 0) of the line's n words; None when the phrase is empty or its word is not in the line."""
    first = next((_key(w) for w in str(phrase or "").split() if _key(w)), "")
    if not first: return None
    t0 = float(unit.get("start") or 0); ws = unit.get("words") or []
    if ws:
        for x in ws:
            if isinstance(x, dict) and _key(x.get("w")) == first: return max(0.0, float(x.get("s") or t0) - t0)
        return None
    toks = [k for k in (_key(w) for w in AUD.spoken(unit.get("text") or "").split()) if k]
    if first not in toks: return None
    d_ = float(dur) if dur is not None else max(0.0, float(unit.get("end") or t0) - t0)
    return d_ * toks.index(first) / max(1, len(toks))


# ---------------------------------------------------------------- verify: every word, number, pair and arrow on screen is the script's
def _f(x):
    try: return float(str(x).replace(",", "").rstrip("."))
    except ValueError: return None


def _eq(a, b): return a is not None and b is not None and abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def _toks(text):
    out = []
    for m in _TOK.findall(str(text or "").lower()):
        if m[0].isdigit() and m.endswith(","): out += [m.rstrip(","), ","]
        else: out.append(m)
    return out


def _words(toks): return [t for t in toks if t[0].isalnum()]          # words and numbers, in order (no punctuation): "the fewest words between"


def _anchors(s): return [w for w in re.findall(r"[a-z]+", str(s or "").lower()) if len(w) >= 3 and w not in STOP]


def _nums(s): return [v for v in (_f(x) for x in _NUM.findall(str(s or ""))) if v is not None]


def _walk(x, strs, nums):
    if isinstance(x, str): strs.append(x)
    elif isinstance(x, bool): pass
    elif isinstance(x, (int, float)): nums.append(float(x))
    elif isinstance(x, dict):
        for v in x.values(): _walk(v, strs, nums)
    elif isinstance(x, list):
        for v in x: _walk(v, strs, nums)


def sentences(texts):
    """C3: each of the three lines cut by layman._SENT.split(audience.spoken(text)) - the cut inside.sentences itself uses, without its four-word filter."""
    return [s.strip() for t in texts for s in LAY._SENT.split(AUD.spoken(t or "")) if s.strip()]


def _own(graphic):
    """The graphic's own entries (a name and its value; a time and its event): drawn as the Director gave them, never asked for a sentence."""
    g = graphic or {}; out = set()
    if g.get("kind") == "compare":
        for e in (g.get("a") or {}, g.get("b") or {}): out.add((str(e.get("name", "")).strip().lower(), _f(e.get("value"))))
    if g.get("kind") == "timeline":
        for e in g.get("events") or []: out.add((str(e.get("t", "")).strip().lower(), str(e.get("text", "")).strip().lower()))
    return out


def _pairs(t, s, graphic, sents):
    own = _own(graphic); scene_nums = []
    if t == "ladder":
        ents = [(r["text"], r["t"], _anchors(r["t"]) + _anchors(r["text"]), _nums(r["t"]) + _nums(r["text"]), (_nums(r["t"]) or [None])[0],
                (r["t"].strip().lower(), r["text"].strip().lower()) in own) for r in s["rungs"]]
        for r in s["rungs"]: scene_nums += _nums(r["t"]) + _nums(r["text"])
    else:
        es = (s["a"], s["b"]) if t == "compare" else (s["part"], s["whole"])
        ents = [(e["name"], e["value"], _anchors(e["name"]), [float(e["value"])], float(e["value"]), (e["name"].strip().lower(), _f(e["value"])) in own) for e in es]
        scene_nums = [float(e["value"]) for e in es]
    places = []
    for name, val, A, D, V, is_own in ents:
        if is_own: continue                                     # the Director's own pair: drawn as the card draws it, never asked for a sentence
        for x in ((val, name) if t == "ladder" else (name,)):
            if not _anchors(x): return f"a part the script cannot place: {x}"          # C1: a name, a t or a text with no anchor
        place = None
        for si, sent in enumerate(sents):
            w = _words(_toks(sent)); nums = [(k, _f(x)) for k, x in enumerate(w) if x[0].isdigit()]
            if not all(a in w for a in A) or not all(any(_eq(v, d) for _, v in nums) for d in D): continue
            if V is not None:
                present = sorted({n for n in scene_nums if any(_eq(v, n) for _, v in nums)})
                if len(present) > 1:
                    pa = [k for k, x in enumerate(w) if x in A]
                    dist = {n: min(abs(k - j) for k, v in nums if _eq(v, n) for j in pa) for n in present}
                    best = min(dist.values()); win = [n for n in present if dist[n] == best]
                    if len(win) > 1 or not _eq(win[0], V): continue          # a tie, or another number stands nearer the name: not this sentence's pair
            place = (si, min([k for k, x in enumerate(w) if x in A] + [k for k, v in nums if any(_eq(v, d) for d in D)])); break
        if place is None: return f"a value the script does not give to that name: {name} = {val if isinstance(val, str) else MD._fmt(val, '')}"
        places.append(place)
    if t == "ladder" and any(places[k] >= places[k + 1] for k in range(len(places) - 1)): return "the rungs are not in the script's order"
    return ""


def _causes(links, texts):
    toks = [t for x in texts for t in (_toks(AUD.spoken(x or "")) + ["."])]
    marks = []                                                  # (first index, last index, direction) of every cause word
    for k, x in enumerate(toks):
        for ph in FORWARD + BACK:
            p = ph.split()
            if toks[k:k + len(p)] == p: marks.append((k, k + len(p) - 1, ph in BACK))
        if x == "so" and k and toks[k - 1] in (",", ";", "."): marks.append((k, k, False))
    for k in range(len(links) - 1):
        A, B = _anchors(links[k]), _anchors(links[k + 1])
        for x in (links[k], links[k + 1]):
            if not _anchors(x): return f"a part the script cannot place: {x}"
        ok = False
        for i0, i1, back in marks:
            before, after = set(toks[:i0]), set(toks[i1 + 1:])
            first, second = (B, A) if back else (A, B)
            if all(a in before for a in first) and all(b in after for b in second): ok = True; break
        if not ok: return f"an arrow the script does not state: {links[k]} -> {links[k + 1]}"
    return ""


def verify(scene, graphic, texts):
    """"" when every number, word, name-value pair and arrow of a clean scene is the script's own, else the reason. texts = (the line before, the
    line, the line after). A scene of drawn.from_graphic passes by construction: it shows the Director's own pairs."""
    t, s = scene["template"], scene["slots"]; g = graphic or {}
    three = [AUD.spoken(x or "") for x in texts]; low = " ".join(three).lower()
    gs, gn = [], []; _walk({k: v for k, v in g.items() if k != "kind"}, gs, gn)
    known = gn + _nums(low) + [v for x in gs for v in _nums(x)]
    ss, sn = [], []; _walk(s, ss, sn)
    for x in sn + [v for y in ss for v in _nums(y)]:
        if not any(_eq(x, k) for k in known): return f"a number the voice never says: {MD._fmt(x, '')}"
    vocab = set(re.findall(r"[a-z]+", low)) | {w for x in gs for w in re.findall(r"[a-z]+", x.lower())}
    for y in ss:
        for w in re.findall(r"[a-z]+", y.lower()):
            if len(w) >= 3 and w not in vocab: return f"a word the script does not have: {w}"
    if t in ("compare", "part", "ladder"):
        why = _pairs(t, s, g, sentences(texts))
        if why: return why
    if t == "flow": return _causes(s["links"], texts)
    return ""


# ---------------------------------------------------------------- the writer's one call, the variety across uploads
def ask(ep, wanted):
    """ONE call for the whole video: the writer fills one template card per explaining moment. {unit: its reply} - an exception, a reply that is
    not a dict or a missing unit means no writer's scene for that moment (logged once); never a second call."""
    from whatifs import models as MDL, prompts as PR
    try:
        r = MDL.ask("scene", PR.Packed(PR.fill(PR.SCENE_SYSTEM, cards=json.dumps(DRAWN.TEMPLATES))), "SLOTS: " + json.dumps(wanted), want_json=True, max_tokens=2000,
                    temperature=0.4, episode=ep, fake_key="scene")
    except Exception as e:
        log(f"drawn scenes: the writer's call failed ({type(e).__name__}) - the code draws the moments from the Director's graphics", "WARN", ep); return {}
    out = {}
    for x in (r.get("scenes") if isinstance(r, dict) else None) or []:
        if isinstance(x, dict):
            try: out.setdefault(int(x.get("unit")), x)
            except (TypeError, ValueError): pass
    miss = [w["unit"] for w in wanted if w["unit"] not in out]
    if miss: log(f"drawn scenes: the writer gave no scene for line(s) {miss} - the code's scene is tried there", "WARN", ep)
    return out


def last_used():
    """{template: variant} of the newest drawn video: the newest row of tab Video_Features whose arm holds a non-empty list under "drawn" ({} when none)."""
    best = []
    for r in store().rows("Video_Features"):
        try: a = json.loads(r.get("arm") or "{}")
        except ValueError: continue
        if isinstance(a, dict) and isinstance(a.get("drawn"), list) and a["drawn"]: best = a["drawn"]
    out = {}
    for c in best:
        c = str(c)
        if c[:-1] in DRAWN.TEMPLATES and c[-1:] in ("0", "1"): out.setdefault(c[:-1], int(c[-1]))
    return out


# ---------------------------------------------------------------- the plan step (D6's run "drawn")
def _three(units, i): return tuple((units[j].get("text") or "") if 0 <= j < len(units) else "" for j in (i - 1, i, i + 1))


def _cues(free, unit, dur): return [cue_s(unit, st["cue"], dur) for st in free["steps"]]


def _lays(sc, units, i, total):
    """Lays the scene out at the render's work size (the same size every later layout uses); raises Refused."""
    from whatifs import render as RN
    dur = _dur(units, i, total); free = DRAWN.expand(sc)
    return DRAWN.layout(free, *RN.work_size(), dur, _cues(free, units[i], dur), **opts())


def _variant(t, ep, i, used, last):
    n = used.get(t, [])
    if len(n) >= 2: return None
    if n: return 1 - n[0]
    return (1 - last[t]) if t in last else int(hashlib.sha256(f"{ep}:{i}".encode()).hexdigest(), 16) % 2


def _one(shots, units, ep, i, total, reply, last, used):
    g = MD.clean_graphic(shots[i].get("graphic")); texts = _three(units, i); wwhy = "the writer gave no scene"
    cands = []
    if isinstance(reply, dict):
        sc, wwhy = DRAWN.clean({"v": 1, "template": reply.get("template"), "variant": 0, "slots": reply.get("slots"), "cues": reply.get("cues") if reply.get("cues") is not None else []})
        wwhy = wwhy or verify(sc, g, texts)
        if not wwhy: cands.append((sc, "writer"))
    code, cwhy = DRAWN.from_graphic(g)
    if code: cands.append((code, "code"))
    why = wwhy if not code else ""
    for k, (sc, by) in enumerate(cands):
        var = _variant(sc["template"], ep, i, used, last)
        if var is None: return {"template": sc["template"], "variant": 0, "slots": sc["slots"], "cues": sc.get("cues", []), "by": "", "why": "its composition is used twice already"}
        sc = dict(sc, variant=var)
        try: _lays(sc, units, i, total)
        except DRAWN.Refused as e:
            why = f"{by}'s scene refused: {e}"
            if by == "writer": continue
            return {"template": sc["template"], "variant": var, "slots": sc["slots"], "cues": sc.get("cues", []), "by": "", "why": why}
        return {"template": sc["template"], "variant": var, "slots": sc["slots"], "cues": sc.get("cues", []), "by": by, "why": "" if by == "writer" else wwhy}
    return {"by": "", "why": why or cwhy or wwhy}


def _put_back(shots, units, ep, d, total):
    idx = set(slots(shots, units, total))
    for rec in d["drawn"].get("scenes") or []:
        if not rec.get("by"): continue
        i = rec.get("unit"); ok = False
        try:
            if i in idx:
                sc, why = DRAWN.clean({"v": 1, "template": rec.get("template"), "variant": rec.get("variant"), "slots": rec.get("slots"), "cues": rec.get("cues") or []})
                if not why and not verify(sc, MD.clean_graphic(shots[i].get("graphic")), _three(units, i)):
                    _lays(sc, units, i, total); ok = True
        except Exception as e: log(f"drawn scene {i}: {type(e).__name__} after a resume - its number card stays", "WARN", ep)
        if ok: shots[i]["scene"] = dict(sc, by=rec["by"])
        else: rec.update(by="", why="no longer fits after a resume")
    return shots


def place(shots, units, ep, d, total, fresh):
    """The new shot list (copies): a drawn scene on each explaining moment of a video in the arm. A resume puts the stored scenes back and asks no
    model; a plan saved before this step (fresh False) is not re-drawn. A shot's type and graphic are NEVER changed: with DRAWN_ON FALSE or
    outside the arm the film is what it was. Never stops a video: any error keeps that moment's number card."""
    if not on(): return shots
    shots = [dict(s) for s in shots]
    if d.get("drawn") is not None: return _put_back(shots, units, ep, d, total)
    if not fresh:
        d["drawn"] = {"arm": False, "why": "planned before the drawn arm", "scenes": []}; return shots
    d["drawn"] = {"arm": arm(ep), "scenes": []}
    if not d["drawn"]["arm"]: return shots
    try: last = last_used()
    except Exception as e:
        log(f"drawn scenes: the last drawn video could not be read ({type(e).__name__}) - no variant to avoid", "WARN", ep); last = {}
    d["drawn"]["last"] = last                                   # C8: the variety rule is judged on what the plan saw
    try:
        idx = slots(shots, units, total)
        wanted = [{"unit": i, "before": _three(units, i)[0], "line": _three(units, i)[1], "after": _three(units, i)[2], "seconds": round(_dur(units, i, total), 2),
                   "graphic": MD.clean_graphic(shots[i].get("graphic"))} for i in idx]
    except Exception as e:
        log(f"drawn scenes: the moments could not be read ({type(e).__name__}) - every number card stays", "WARN", ep); return shots
    replies = ask(ep, wanted) if wanted else {}
    used = {}
    for i in idx:
        rec = {"unit": i, "template": "", "variant": 0, "slots": {}, "cues": [], "by": "", "why": ""}
        try: rec.update(_one(shots, units, ep, i, total, replies.get(i), last, used))
        except Exception as e:
            rec.update(by="", why=f"error: {type(e).__name__}"); log(f"drawn scene {i}: {type(e).__name__} - its number card stays", "WARN", ep)
        if rec["by"]:
            shots[i]["scene"] = {"v": 1, "template": rec["template"], "variant": rec["variant"], "slots": rec["slots"], "cues": rec["cues"], "by": rec["by"]}
            used.setdefault(rec["template"], []).append(rec["variant"])
        d["drawn"]["scenes"].append(rec)
    return shots


def feature(d):
    """The arm in the learning core's features: {"drawn": ["count0", ...]} for a video in the arm with the switch on, else {}."""
    dr = (d or {}).get("drawn") or {}
    if not (on() and dr.get("arm")): return {}
    return {"drawn": [f"{x['template']}{x['variant']}" for x in dr.get("scenes") or [] if x.get("by")]}


def m_place(shots):
    """D6's measures of the run (never raises: odd output gives zeros): the graphic moments after the first shot, the scenes by writer and by code, the cards kept."""
    try:
        sh = list(shots or []); sc = [s.get("scene") for s in sh if isinstance(s, dict) and isinstance(s.get("scene"), dict)]
        n = sum(1 for k, s in enumerate(sh) if k >= 1 and isinstance(s, dict) and s.get("type") == "graphic")
        w = sum(1 for x in sc if x.get("by") == "writer"); c = sum(1 for x in sc if x.get("by") == "code")
        return {"slots": n, "drawn_by_writer": w, "drawn_by_code": c, "kept_card": max(0, n - w - c)}
    except Exception: return {"slots": 0, "drawn_by_writer": 0, "drawn_by_code": 0, "kept_card": 0}


def plan_report(shots, units, d, total):
    """(status, words) of check drawn_plan, on the shot list before any picture is paid: it asks clean, verify and layout AGAIN (never trusts the
    mark) and judges the variety on what the plan saw (d["drawn"]["last"])."""
    sc_ = [(i, s["scene"]) for i, s in enumerate(shots or []) if isinstance(s, dict) and isinstance(s.get("scene"), dict)]
    dr = (d or {}).get("drawn") or {}
    if not on(): return ("FAIL", f"shot {sc_[0][0]} carries a scene with the drawn scenes switched off") if sc_ else ("N/A", "not applicable: the drawn scenes are switched off")
    if not dr.get("arm"): return ("FAIL", f"shot {sc_[0][0]} carries a scene outside the drawn arm") if sc_ else ("N/A", "not applicable: this video is not in the drawn arm")
    idx = slots(shots, units, total); last = dr.get("last") or {}; seen, first = set(), {}
    for i, x in sc_:
        if i not in idx: return "FAIL", f"a scene sits on a shot that is not an explaining moment: {i}"
        sc, why = DRAWN.clean({k: x.get(k) for k in ("v", "template", "variant", "slots", "cues")})
        why = why or verify(sc, MD.clean_graphic(shots[i].get("graphic")), _three(units, i))
        if why: return "FAIL", f"scene {i}: {why}"
        try: _lays(sc, units, i, total)
        except DRAWN.Refused as e: return "FAIL", f"scene {i}: {e}"
        comp = (sc["template"], sc["variant"])
        if comp in seen: return "FAIL", f"two scenes share one composition: {comp[0]}{comp[1]}"
        seen.add(comp)
        if comp[0] not in first:
            first[comp[0]] = comp[1]
            if last.get(comp[0]) == comp[1]: return "FAIL", f"the first {comp[0]} repeats the last drawn video's composition {comp[0]}{comp[1]}"
    m, n = len(idx), len(sc_)
    if not m: return "PASS", "the drawn arm held: no explaining moment in this film"
    kept = sorted({str(x.get("why") or "no scene") for x in dr.get("scenes") or [] if not x.get("by")})
    comps = ", ".join(f"{x['template']}{x['variant']}" for _, x in sc_) or "none"
    return "PASS", (f"the drawn arm held: {n} of {m} explaining moments carry a scene ({comps}; none repeats the last drawn video's), {m - n} keep the number card"
                    + (": " + "; ".join(kept) if m - n and kept else ""))[:380]
