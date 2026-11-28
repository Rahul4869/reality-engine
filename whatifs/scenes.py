"""Drawn by code (D6): which explaining moments of a long video carry a drawn scene - the arm, the writer's one call, the check that every word, number, pair and arrow is the script's own, the plan's report. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, re
from whatifs.core import S, log, store
from whatifs import drawn as DRAWN, media as MD
from whatifs.org import audience as AUD, layman as LAY

FORWARD = ("therefore", "which means", "that means", "makes", "causes", "leads to", "forces")      # and "so" only at a clause's start (after , ; or .)
BACK = ("because",)
DENY = ("not", "never", "if", "cannot", "no", "nobody", "nothing", "neither", "nor", "may", "might", "whether", "doubt", "myth", "without", "none", "hardly", "rarely", "seldom", "barely", "false", "untrue", "wrong")      # RUL-U3p 1: ONE list - AFD F1 (+U1) denies or doubts, DRAWN-b A0a (R2-F6) adds its nine; "n't" too, see _denied; a premise's "if", see _premise_if
STOP = ("the", "and", "but", "its", "this", "that", "these", "those", "with", "from", "into", "onto", "your", "you", "are", "was", "were", "has", "have", "had",
        "will", "would", "can", "could", "then", "than", "when", "what", "who")      # C1: never an anchor
_TOK = re.compile(r"\d[\d,]*(?:\.\d+)?|[a-z]+|[.,;:!?]")
_NUM = re.compile(r"\d[\d,]*\.?\d*")
_SCALE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion)\b", re.I)
_MUL = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_UNIT = {w: u for u, ws in (("second", "seconds secs sec"), ("minute", "minutes mins min"), ("hour", "hours hrs hr h"), ("day", "days"), ("week", "weeks"),
                            ("month", "months"), ("year", "years"), ("decade", "decades"), ("century", "centuries"), ("millennium", "millennia millenniums"),
                            ("degree", "degrees"), ("calorie", "calories"), ("mm", "millimetre millimetres millimeter millimeters"),
                            ("cm", "centimetre centimetres centimeter centimeters"), ("m", "metre metres meter meters"), ("km", "kilometre kilometres kilometer kilometers"),
                            ("mile", "miles"), ("foot", "feet ft"), ("inch", "inches"), ("g", "gram grams"), ("kg", "kilo kilos kilogram kilograms"),
                            ("tonne", "tonnes ton tons"), ("pound", "pounds lb lbs"), ("ml", "millilitre millilitres milliliter milliliters"), ("litre", "litres liter liters"))
         for w in [u] + ws.split()}                             # AFD F2: the unit a script says after an amount ("10 minutes", "10 more minutes"), by its one name


def _scaled(text):
    """'150 million' -> '150000000': a number with its scale word is ONE number, never the bare 150 (verify reads digits)."""
    return _SCALE.sub(lambda m: f"{float(m.group(1).replace(',', '')) * _MUL[m.group(2).lower()]:.0f}", str(text or ""))


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
    (its start to the next line's start) lasts at least DRAWN_MIN_S - and never less than UNIT_MERGE_SEC, or the renderer's merge takes the line away and
    the scene has no proof and no reason (open issue 250): the larger of the two cells."""
    lo = max(S("DRAWN_MIN_S", float), S("UNIT_MERGE_SEC", float)); out = []
    for i, s in enumerate(shots or []):
        if i < 1 or i >= len(units) or not isinstance(s, dict) or s.get("type") != "graphic": continue
        if MD.clean_graphic(s.get("graphic")) is None: continue
        if _dur(units, i, total) >= lo: out.append(i)
    return out


def _key(w): return re.sub(r"[^a-z0-9]", "", str(w or "").lower())


def _plain(s):
    """A graphic's string as from_graphic draws it: the kit's quotes and dashes made plain, spaces collapsed, lower case (C4)."""
    s = str(s if s is not None else "")
    for a, b in DRAWN.SWAP.items(): s = s.replace(a, b)
    return " ".join(s.split()).strip().lower()


def cue_s(unit, phrase, dur=None):
    """The second, from the line's start, at which the phrase's first word is spoken: from the unit's timed words where it carries them (the reader
    living.render is given), else dur * k / n for the k-th (from 0) of the line's n words; None when the phrase is empty or its word is not in the line."""
    ws_ = [_key(w) for w in str(phrase or "").split() if _key(w)]; an_ = [w for w in ws_ if len(w) >= 3 and w.isalpha() and w not in STOP]
    first = an_[-1] if an_ else (ws_[0] if ws_ else "")          # the phrase's last ANCHOR (C1's), never "the": the word the narrator lands on
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
    return [s.strip() for t in texts for s in LAY._SENT.split(_scaled(AUD.spoken(t or ""))) if s.strip()]


def _own(graphic):
    """The graphic's own entries (a name and its value; a time and its event): drawn as the Director gave them, never asked for a sentence."""
    g = graphic or {}; out = set()
    if g.get("kind") == "compare":
        for e in (g.get("a") or {}, g.get("b") or {}): out.add((_plain(e.get("name", "")), _f(e.get("value"))))
    if g.get("kind") == "timeline":
        for e in g.get("events") or []: out.add((_plain(e.get("t", "")), _plain(e.get("text", ""))))
    if g.get("kind") == "counter": out.add((_plain(g.get("label", "")), _f(g.get("to"))))      # DRAWN-b A0a (253 (a)): the Director's own count
    return out


def _pairs(t, s, graphic, sents):
    own = _own(graphic); scene_nums = []
    if t == "ladder":
        ents = [(r["text"], r["t"], _anchors(r["t"]) + _anchors(r["text"]), _nums(_scaled(r["t"])) + _nums(_scaled(r["text"])), (_nums(_scaled(r["t"])) or [None])[0],
                (_plain(r["t"]), _plain(r["text"])) in own) for r in s["rungs"]]
        for r in s["rungs"]: scene_nums += _nums(_scaled(r["t"])) + _nums(_scaled(r["text"]))
    else:
        es = (s["a"], s["b"]) if t == "compare" else (s["part"], s["whole"]) if t == "part" else ({"name": s["label"], "value": s["to"]},)      # DRAWN-b A0a (253 (a)): a count's number under its own noun
        ents = [(e["name"], e["value"], _anchors(e["name"]), [float(e["value"])], float(e["value"]), (_plain(e["name"]), _f(e["value"])) in own) for e in es]
        scene_nums = [float(e["value"]) for e in es]
    places, units = [], []
    for name, val, A, D, V, is_own in ents:
        if is_own: continue                                     # the Director's own pair: drawn as the card draws it, never asked for a sentence
        for x in ((val, name) if t == "ladder" else (name,)):
            if not _anchors(x): return f"a part the script cannot place: {x}"          # C1: a name, a t or a text with no anchor
        place = None
        for si, sent in enumerate(sents):
            w = _words(_toks(sent)); nums = [(k, _f(x)) for k, x in enumerate(w) if x[0].isdigit()]
            if not all(a in w for a in A) or not all(any(_eq(v, d) for _, v in nums) for d in D): continue
            if V is not None:
                present = sorted({v for _, v in nums if v is not None})
                if len(present) > 1:
                    pa = [k for k, x in enumerate(w) if x in A]
                    dist = {n: min(abs(k - j) for k, v in nums if _eq(v, n) for j in pa) for n in present}
                    best = min(dist.values()); win = [n for n in present if dist[n] == best]
                    if len(win) > 1 or not _eq(win[0], V): continue          # a tie, or another number stands nearer the name: not this sentence's pair
            place = (si, min([k for k, x in enumerate(w) if x in A] + [k for k, v in nums if any(_eq(v, d) for d in D)]))
            if t == "part":                                     # AFD F2: the unit the voice says after this amount (its number nearest the name)
                pa = [k for k, x in enumerate(w) if x in A]; at = min((k for k, v in nums if _eq(v, V)), key=lambda k: min(abs(k - j) for j in pa))
                units.append(_unit_after(w, at))
            break
        if place is None: return f"a value the script does not give to that name: {name} = {val if isinstance(val, str) else MD._fmt(val, '')}"
        places.append(place)
    if t == "part" and len(units) == 2 and all(units) and _UNIT[units[0]] != _UNIT[units[1]]:      # AFD F2: 10 minutes of 24 hours is never "42%" - the share of two units is false
        return f"a part and its whole in different units: {units[0]} and {units[1]}"
    if t == "ladder" and any(places[k] >= places[k + 1] for k in range(len(places) - 1)): return "the rungs are not in the script's order"
    return ""


def _unit_after(w, at):
    """AFD F2 (U1): the unit word the voice says after the amount w[at] - the next word, or the one after a single word between ("10 more minutes",
    "24 whole hours"); "" when neither is a unit of _UNIT."""
    return next((x for x in w[at + 1:at + 3] if x in _UNIT), "")


def _denied(ws):
    """AFD F1: do these words deny or only doubt (a word of DENY - "no longer" by its "no" - and "n't": "doesn't" is cut "doesn" + "t")?"""
    return any(x in DENY or (x == "t" and k and ws[k - 1].endswith("n")) for k, x in enumerate(ws))


def _premise_if(toks, sid, j, i0, reach, first, second):
    """U1d (AFD-if, RUL-U1d 1 as re-ruled by RUL-U1f 1): is toks[j] the "if" of a what-if's premise, whose arrow first -> second the cause mark at
    toks[i0] states? Only an "if" that opens its sentence ("If ...", "What if ..."). P1, the mark in the same sentence: only an "If" that is the
    sentence's FIRST word (a "What if" never - the whole question supposes, its link included: 1a), in a sentence holding EXACTLY ONE "," or ";"
    (none or two: the if-clause's end is not known: 1b), the mark after it (1c); THE PREMISE is the tokens between the "if" and that one stop. P2:
    the mark opens the next sentence ("What if X? So Y."); THE PREMISE is the whole sentence before. On both roads every anchor of `first` (the
    arrow's tail) is in THE PREMISE (G1) and not every anchor of `second` (its head) is (G2): the arrow left out is premise -> consequence, never
    the premise's own supposed link. Every other "if" - "whether", "So if", a mark inside the if-clause - still denies; only this one token is left
    out of what _denied judges, and only for this (mark, link) pair."""
    if toks[j] != "if": return False
    s = [k for k in range(len(toks)) if sid[k] == sid[j]]; w = [k for k in s if toks[k][0].isalnum()]          # its sentence's tokens, and its words, in order
    if not (w[0] == j or (w[1:2] == [j] and toks[w[0]] == "what")): return False
    if sid[j] == sid[i0]:                                       # P1: the if-clause has ended before the mark
        c = [k for k in s if toks[k] in (",", ";")]
        if w[0] != j: return False                              # 1a: a "What if" takes P2 only
        if len(c) != 1 or not j < c[0] < i0: return False      # 1b: exactly one "," or ";" in the sentence; 1c: the mark after it
        prem = {toks[k] for k in range(j + 1, c[0])}
    elif reach and sid[j] == sid[i0] - 1: prem = {toks[k] for k in s}          # P2: the whole sentence before is the premise
    else: return False
    return all(a in prem for a in first) and not all(b in prem for b in second)          # G1, G2: premise -> consequence, never inside the premise


def _causes(links, texts):
    toks = [t for x in texts for t in (_toks(AUD.spoken(x or "")) + ["."])]
    sid, s_, seen = [], 0, False                              # each token's sentence; the appended "." of an empty line opens no sentence
    for t in toks:
        sid.append(s_)
        if t[0].isalnum(): seen = True
        elif t in (".", "!", "?") and seen: s_ += 1; seen = False
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
            S_ = sid[i0]
            before = {toks[j] for j in range(i0) if sid[j] == S_}; after = {toks[j] for j in range(i1 + 1, len(toks)) if sid[j] == S_}
            reach = not back and not any(toks[j][0].isalnum() for j in range(i0) if sid[j] == S_)
            if reach:                                           # a cause word that opens its sentence ("So ...") reaches back one sentence
                before |= {toks[j] for j in range(i0) if sid[j] == S_ - 1}
            words = [j for j in range(len(toks)) if sid[j] == S_ or (reach and sid[j] == S_ - 1) or sid[j] == S_ + 1]      # RUL-U3p 1: ONE scope - its own sentence, the one a "So" reaches back to (AFD F1), the next ("... a cold. It doesn't.": DRAWN-b A0a, T2)
            first, second = (B, A) if back else (A, B)
            if _denied([toks[j] for j in words if not _premise_if(toks, sid, j, i0, reach, first, second)]): continue      # AFD F1 + DRAWN-b A0a (R2-F6), ONE check (RUL-U3p 1): a denial or doubt in that scope draws no arrow; U1d/U1f: only a premise's "if" is left out
            if all(a in before for a in first) and all(b in after for b in second): ok = True; break
        if not ok: return f"an arrow the script does not state: {links[k]} -> {links[k + 1]}"
    return ""


# DRAWN-b A0b (253 (b), (c)): a computed figure is drawn only where the voice says it, digit for digit; a unit only behind a value the script gives it to
_SAY = {"pct": (("percent",), ("per", "cent")), "x": (("times",), ("x",), ("fold",))}
_XWORD = {"twice": 2.0, "double": 2.0, "triple": 3.0, "half": 2.0}


def _wd(sent): return _words(_toks(str(sent or "").replace("%", " percent ")))          # a sentence's words and numbers in order; "%" is read as the word


def _said(w, kind):
    """[(place, figure)] of every percentage ("pct") or ratio ("x") the words SAY: a number in digits followed by "percent", "per cent" or "%" - by "times",
    "x" or "fold" - and, for a ratio, the words of _XWORD. A number spelled in words is not read: the scene is refused, the card stays."""
    out = []
    for k, x in enumerate(w):
        if x[0].isdigit():
            for m in _SAY[kind]:
                if tuple(w[k + 1:k + 1 + len(m)]) == m and not (m == ("x",) and k + 2 < len(w) and w[k + 2][0].isdigit()) and not (m == ("times",) and w[k + 2:k + 3] in (["a"], ["an"], ["per"], ["each"], ["every"])):
                    if _f(x) is not None: out.append((k, _f(x)))
                    break
        elif kind == "x" and x in _XWORD and w[k + 1:k + 2] not in (["a"], ["an"]): out.append((k, _XWORD[x]))      # R16 [R1-18, change 7]: "half a billion", "twice a day" are no ratio
    return out


def _states(sents, kind, want, names):
    """True when ONE sentence says, as a percentage (a ratio), exactly the number the screen will show (`want` = drawn._pct_text / _ratio_text of the computed
    figure), carries every anchor of one of `names`, and - where it says several different figures - the one nearest that name's anchors is this one (a tie refuses)."""
    n = _f(str(want).rstrip("%x"))
    for sent in sents:
        w = _wd(sent); said = _said(w, kind)
        for A in names:
            if not said or not A or not all(a in w for a in A): continue
            pa = [k for k, x in enumerate(w) if x in A]; dist = {}
            for k, q in said: dist[q] = min([dist.get(q, len(w))] + [abs(k - j) for j in pa])
            best = min(dist.values()); win = [q for q, d_ in dist.items() if d_ == best]
            if len(win) == 1 and _eq(win[0], n): return True
    return False


_JOIN = ("a", "an", "per")      # RUL-U3p 2b: the joining words of a unit said aloud ("kilometres an hour", "kilometres per hour")


def _unit_at(U, w, k):
    """253 (c) + CR-AUDITFIX 2 (RUL-U3p 2b): do the unit's words U stand right behind the value w[k] - from the next word or the one after it?
    As written ("km" after "384,000"), or each word by its one name in _UNIT ("km" is the voice's "kilometres", "h" its "hour"), a joining "a",
    "an" or "per" read on neither side ("km/h" = "kilometres an hour"); the unit never starts on a joining word of the line."""
    if U in (w[k + 1:k + 1 + len(U)], w[k + 2:k + 2 + len(U)]): return True
    nm = lambda xs: [_UNIT.get(x, x) for x in xs if x not in _JOIN]
    want = nm(U)
    return bool(want) and any(s0 < len(w) and w[s0] not in _JOIN and nm(w[s0:s0 + 2 * len(U) + 1])[:len(want)] == want for s0 in (k + 1, k + 2))


def _unit(t, s, g, sents):
    """253 (c): a count's or a compare's unit stands within the two words after EACH of its values, in a sentence that carries that value's own name; the
    Director's own pair under the Director's own unit is drawn as the card draws it."""
    U = _wd(s.get("unit") or "")
    if not U: return ""
    own = _own(g); same = _plain(s["unit"]) == _plain((g or {}).get("unit", ""))
    for e in (({"name": s["label"], "value": s["to"]},) if t == "count" else (s["a"], s["b"])):
        if same and (_plain(e["name"]), _f(e["value"])) in own: continue
        A = _anchors(e["name"]); ok = False
        for sent in sents:
            w = _wd(sent)
            if all(a in w for a in A): ok = ok or any(x[0].isdigit() and _eq(_f(x), float(e["value"])) and _unit_at(U, w, k) for k, x in enumerate(w))      # RUL-U3p 2b: right behind the value, as written or by its one name in _UNIT
        if not ok: return f"a unit the script does not give to that value: {MD._fmt(float(e['value']), s['unit'])}"
    return ""


def verify(scene, graphic, texts):
    """"" when every number, word, name-value pair and arrow of a clean scene is the script's own, else the reason. texts = (the line before, the
    line, the line after). A scene of drawn.from_graphic passes by construction: it shows the Director's own pairs."""
    t, s = scene["template"], scene["slots"]; g = graphic or {}
    code_ = DRAWN.from_graphic(g)[0] if g else None
    if code_ and code_["template"] == t and code_["slots"] == s: return ""      # the code's own scene of this graphic: the Director's own content, as the card shows it (memo 3.3) - recomputed, never the mark
    three = [_scaled(AUD.spoken(x or "")) for x in texts]; low = " ".join(three).lower()
    gs, gn = [], []; _walk({k: v for k, v in g.items() if k != "kind"}, gs, gn)
    known = gn + _nums(low) + [v for x in gs for v in _nums(_scaled(x))]
    ss, sn = [], []; _walk(s, ss, sn)
    for x in sn + [v for y in ss for v in _nums(_scaled(y))]:
        if not any(_eq(x, k) for k in known): return f"a number the voice never says: {MD._fmt(x, '')}"
    vocab = set(re.findall(r"[a-z]+", low)) | {w for x in gs for w in re.findall(r"[a-z]+", x.lower())}
    for y in ss:
        for w in re.findall(r"[a-z]+", y.lower()):
            if len(w) >= 3 and w not in vocab: return f"a word the script does not have: {w}"
    for w in re.findall(r"[a-z]+", str(s.get("unit") or "").lower()):      # AFD F3: a unit is asked at ANY length - "kg" is never the script's "km"
        if w not in vocab and not (w in _UNIT and any(_UNIT.get(v) == _UNIT[w] for v in vocab)):      # CR-AUDITFIX 2: "km" is the voice's "kilometres" - one name in _UNIT
            return f"a word the script does not have: {w}"
    if "%" in str(s.get("unit") or "") and not ("%" in low or "percent" in vocab or "per cent" in low or any("%" in x for x in gs)):      # U1 (AFD-%): "%" has no letters to ask - asked as itself
        return "a word the script does not have: %"
    if t in ("compare", "part", "ladder", "count"):
        sents = sentences(texts); why = _pairs(t, s, g, sents)
        if not why and t in ("count", "compare"): why = _unit(t, s, g, sents)
        if not why and t == "part" and not _states(sents, "pct", DRAWN._pct_text(100.0 * float(s["part"]["value"]) / float(s["whole"]["value"])), [_anchors(s["part"]["name"])]):
            why = "a percentage the script does not state"
        if not why and t == "compare":
            a, b = float(s["a"]["value"]), float(s["b"]["value"]); own = _own(g)
            both_own = g.get("kind") == "compare" and all((_plain(e["name"]), _f(e["value"])) in own for e in (s["a"], s["b"]))      # the Director's own two pairs: the card's own comparison
            if not both_own and not any(_pairs("compare", s, None, [x]) == "" for x in sents) \
               and not _states(sents, "x", DRAWN._ratio_text(max(a, b) / min(a, b)), [_anchors(s["a"]["name"]), _anchors(s["b"]["name"])]):
                why = "a comparison the script does not make"
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
    sc_ = r.get("scenes") if isinstance(r, dict) else None
    for x in (sc_ if isinstance(sc_, list) else []):
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
    last = d["drawn"].get("last") or {}; first = set()
    for rec in sorted([r for r in d["drawn"].get("scenes") or [] if r.get("by")], key=lambda r: r.get("unit", 0)):
        t = rec.get("template")
        if t in first: continue
        first.add(t)
        if last.get(t) == rec.get("variant"):
            rec.update(by="", why="its composition would repeat the last drawn video's after a resume"); shots[rec["unit"]].pop("scene", None)
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
        log(f"drawn scenes: the last drawn video could not be read ({type(e).__name__}) - no variant to avoid", "WARN", ep); last = None
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
        try: rec.update(_one(shots, units, ep, i, total, replies.get(i), last or {}, used))
        except Exception as e:
            rec.update(by="", why=f"error: {type(e).__name__}"); log(f"drawn scene {i}: {type(e).__name__} - its number card stays", "WARN", ep)
        if rec["by"]:
            shots[i]["scene"] = {"v": 1, "template": rec["template"], "variant": rec["variant"], "slots": rec["slots"], "cues": rec["cues"], "by": rec["by"]}
            used.setdefault(rec["template"], []).append(rec["variant"])
        d["drawn"]["scenes"].append(rec)
    return shots


def feature(d, shown=None):
    """The arm in the learning core's features: {"drawn": ["count0", ...]} for a video in the arm with the switch on, else {}."""
    dr = (d or {}).get("drawn") or {}
    if not (on() and dr.get("arm")): return {}
    return {"drawn": [f"{x['template']}{x['variant']}" for x in dr.get("scenes") or [] if x.get("by") and (shown is None or x.get("unit") in shown)]}


def m_place(shots):
    """D6's measures of the run (never raises: odd output gives zeros): the graphic moments after the first shot, the scenes by writer and by code, the cards kept."""
    try:
        sh = list(shots or []); sc = [s.get("scene") for s in sh if isinstance(s, dict) and isinstance(s.get("scene"), dict)]
        n = sum(1 for k, s in enumerate(sh) if k >= 1 and isinstance(s, dict) and s.get("type") == "graphic")
        w = sum(1 for x in sc if x.get("by") == "writer"); c = sum(1 for x in sc if x.get("by") == "code")
        return {"slots": n, "drawn_by_writer": w, "drawn_by_code": c, "kept_card": max(0, n - w - c)}
    except Exception: return {"slots": 0, "drawn_by_writer": 0, "drawn_by_code": 0, "kept_card": 0}


# ---------------------------------------------------------------- the render and the finished file (step 2)
def proof(scene, units, i, dur, fps):
    """THE layout of the render (the only one: at the work size, on the line the render cuts) and drawn.proof on it: the report plus "L"."""
    from whatifs import render as RN
    sc, why = DRAWN.clean({k: scene.get(k) for k in ("v", "template", "variant", "slots", "cues")})
    if why: raise DRAWN.Refused(why)
    free = DRAWN.expand(sc); o = opts()
    L = DRAWN.layout(free, *RN.work_size(), float(dur), _cues(free, units[i], float(dur)), **o)
    return dict(DRAWN.proof(L, fps, o["hold_max"], budget_s=S("DRAWN_RENDER_MAX_S", float)), L=L)


def audit(master, job):
    """The finished file, read where each drawn scene has finished drawing (its last drawn state's end - 0.25 s): a scene whose text does not reach
    DRAWN_INK_MIN on the master (or whose frame could not be read) returns every drawn state of its shot as (middle second, (i, k)) - their still."""
    from whatifs import render as RN
    out = []; f_ = float(job.fps)
    for i, r in sorted((getattr(job, "drawn", {}) or {}).items()):
        st_ = [m for m in job.segmeta if m.get("i") == i and m.get("drawn")]
        if not isinstance(r, dict): continue
        if not st_:                                             # proved, yet no state shows it drawn (a repair re-drew it, or the render failed): its still, with the reason on record
            if r.get("ok"): r.update(ok=False, why=r.get("why") or "shown as its still: the render or a repair re-drew it")
            continue
        if r.get("ok") and len(st_) < sum(1 for m in job.segmeta if m.get("i") == i):      # AFD F4 (F-12 on this road): a repair re-drew only SOME of its states -
            out += [((m["f0"] + m["nf"] / 2) / f_, (m["i"], m["k"])) for m in st_]            # never half a diagram: the whole scene goes to its still, with the reason
            r.update(ok=False, why=r.get("why") or "shown as its still: a repair re-drew part of it"); continue
        if not r.get("L"): continue
        if not r.get("ok"): out += [((m["f0"] + m["nf"] / 2) / f_, (m["i"], m["k"])) for m in st_]; continue
        g = RN.frame_at(master, max((m["f0"] + m["nf"]) / f_ for m in st_) - 0.25, w=int(r["L"]["W"]))
        v = DRAWN.ink(g, r["L"]) if g is not None else 0.0; r["ink"] = v
        if g is None or v < S("DRAWN_INK_MIN", float):
            out += [((m["f0"] + m["nf"] / 2) / f_, (m["i"], m["k"])) for m in st_]
            r["ok"] = False; r["why"] = "its frame could not be read on the finished file" if g is None else f"its text reached only {v:.1f} to 1 on the finished file"      # the reason drawn_shown asks for
    return out


def audit_failed(job, e):
    """256 (a): the audit itself raised. Every scene still on record as proved - drawn on the file, or re-drawn by a repair before the audit ran - gets the
    reason drawn_shown asks for, and every state still recorded drawn is returned as audit returns an unreadable one: (middle second, (i, k)) - its still."""
    why = f"the audit could not run ({type(e).__name__}): shown as its still"
    for r in (getattr(job, "drawn", {}) or {}).values():
        if isinstance(r, dict) and (r.get("ok") or not r.get("why")): r.update(ok=False, why=why)
    return [((m["f0"] + m["nf"] / 2) / float(job.fps), (m["i"], m["k"])) for m in job.segmeta if m.get("drawn")]


def shown_report(master, shots, drawn):
    """(status, words) of check drawn_shown, on what the RENDER recorded and the master itself: a state recorded drawn must sit on a shot with a
    scene, a scene without a drawn state must have its reason on record, and a shot still recorded drawn is measured AGAIN on the master with the
    proof's own L. A scene shown as its still is never a failure."""
    from whatifs import render as RN
    dr = drawn or {}; plan = dr.get("plan") or {}; proof_ = dr.get("proof") or {}; Ls = dr.get("L") or {}; states = dr.get("states") or []
    sc_ = {i for i, s in enumerate(shots or []) if isinstance(s, dict) and isinstance(s.get("scene"), dict)}
    if not on(): return ("FAIL", "a state is recorded drawn with the drawn scenes switched off") if states else ("N/A", "not applicable: the drawn scenes are switched off")
    if not plan.get("arm"): return ("FAIL", "a state is recorded drawn outside the drawn arm") if states else ("N/A", "not applicable: this video is not in the drawn arm")
    by_i = {}
    for x in states: by_i.setdefault(x[2], []).append(x)
    for i in by_i:
        if i not in sc_: return "FAIL", f"a state is recorded drawn on shot {i}, which carries no scene"
    stills = []
    for i in sorted(sc_):
        if i not in by_i:
            why = str((proof_.get(i) or proof_.get(str(i)) or {}).get("why") or "")
            if not why: return "FAIL", f"shot {i} has a scene, no drawn state and no reason on record"
            stills.append(f"{i}: {why}")
    lows = []
    for i, xs in sorted(by_i.items()):
        L = Ls.get(i) or Ls.get(str(i))
        g = RN.frame_at(master, max(x[1] for x in xs) - 0.25, w=int(L["W"])) if (L and master) else None
        if g is None: return "FAIL", f"shot {i} is recorded drawn but its frame could not be read on the master"
        v = DRAWN.ink(g, L) if g is not None else 0.0
        if v < S("DRAWN_INK_MIN", float): return "FAIL", f"shot {i} is recorded drawn but its text reaches only {v:.1f} to 1 on the master (limit {S('DRAWN_INK_MIN', float):.1f})"
        lows.append(v)
    if not by_i and not stills: return "PASS", "the drawn arm held: no explaining moment in this film"
    return "PASS", (f"the drawn arm held: {len(by_i)} scene(s) drawn" + (f" (lowest contrast of a text on the film {min(lows):.1f} to 1)" if lows else "")
                    + f", {len(stills)} shown as its still" + (": " + "; ".join(stills) if stills else ""))[:380]


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
    rep = "the last drawn video could not be read" if dr.get("last", {}) is None else "none repeats the last drawn video's"      # F-14: never a variety the plan did not check
    return "PASS", (f"the drawn arm held: {n} of {m} explaining moments carry a scene ({comps}; {rep}), {m - n} keep the number card"
                    + (": " + "; ".join(kept) if m - n and kept else ""))[:380]
