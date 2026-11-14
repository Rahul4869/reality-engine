"""Shot-plan rules: where the animated clips go, shot pacing (pieces_for) and related fixes; never adds a paid shot. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import re, hashlib, math
from whatifs.core import S, log

def pieces_for(dur, shot_type, opening=False, episode=None):
    """v9.3 (MICRO_CUTS_ON, code only, zero cost): how many picture states a shot of `dur` seconds gets. v9.2 rule: 1 under 7.5 s, 2 under 13 s, else 3.
    With micro-cuts a still / reused picture changes framing (alternating wide / detail crop, a new camera move) at least every PIECE_MAX_SEC
    (PIECE_MAX_SEC_OPENING inside the opening window), never below PIECE_MIN_SEC per piece, at most 8. Graphics and reaction cutaways stay one piece.
    Any failure = the v9.2 rule for this episode (v91.guard)."""
    base = 1 if dur < 7.5 or shot_type in ("graphic", "reaction") else (2 if dur < 13 else 3)
    from whatifs import v91 as V91
    if shot_type in ("graphic", "reaction"):                       # v11.1: animated, but never one piece longer than VISUAL_ANIMATED_MAX_S
        return max(base, int(math.ceil(float(dur) / max(1.0, S("VISUAL_ANIMATED_MAX_S", float)) - 1e-9)))
    if not V91.on("MICRO_CUTS_ON", episode): return base
    res = base
    with V91.guard("MICRO_CUTS_ON", episode):
        mx = S("PIECE_MAX_SEC_OPENING" if opening else "PIECE_MAX_SEC", float); mn = max(0.5, S("PIECE_MIN_SEC", float))
        if mx > 0: res = max(base, min(int(math.ceil(float(dur) / mx - 1e-9)), max(1, int(float(dur) // mn)), 24))   # v11.1: cap 8 -> 24 (a 40 s line still changes every <= 4 s)
    return res

SCENES = [
    ("bathroom", r"\b(bathroom|mirror|sink|toothbrush|shower|bathtub|towel|tap)\b", ["a toothbrush in your hand", "fogged mirror edge", "your fingers on the cold sink rim", "a towel hook at the frame edge"]),
    ("kitchen", r"\b(kitchen|kettle|stove|fridge|counter|mug|cup|plate|toaster|pan|spoon)\b", ["a steaming mug in your hand", "the edge of the kitchen counter", "your hand on the fridge door", "a spoon caught mid-stir"]),
    ("hallway", r"\b(hallway|corridor|door|doorway|stairs|staircase|landing)\b", ["your hand on the door frame", "the edge of an open door", "a light switch beside your hand", "the stair rail under your palm"]),
    ("window", r"\b(window|curtain|blinds|windowsill|pane)\b", ["your fingertips on the window glass", "a curtain edge in the foreground", "the window frame cutting the view", "your breath on the pane"]),
    ("bedroom", r"\b(bed|pillow|blanket|duvet|bedroom|alarm clock)\b", ["the blanket edge across your knees", "your hand on the pillow", "an alarm clock on the nightstand edge"]),
    ("living", r"\b(sofa|couch|tv|television|lamp|living room|rug|bookshelf)\b", ["the arm of the sofa", "a lamp shade at the frame edge", "your hand on the remote"]),
    ("street", r"\b(street|road|car|traffic|pavement|sidewalk|bus|city)\b", ["a windshield edge and dashboard", "your hand on a lamppost", "the kerb at your feet"]),
    ("space", r"\b(space|orbit|astronaut|spacecraft|spaceship|planet|moon|saturn|galaxy|asteroid|meteor)\b", ["the rim of a helmet visor", "a gloved hand on a handrail", "a cockpit window frame"]),
    ("water", r"\b(ocean|sea|underwater|flood|wave|waves|river|lake|rain|swimming)\b", ["water droplets on the lens", "your hand breaking the water surface", "a rain-streaked visor edge"]),
    ("fire", r"\b(fire|lava|volcano|volcanic|flame|flames|burn|burning|magma)\b", ["your hands shielding your face from the heat", "a scorched glove at the frame edge", "embers drifting past the lens"]),
    ("body", r"\b(hair|skin|bone|bones|blood|heart|eye|eyes)\b", ["your own hand turned palm-up", "your reflection at the frame edge", "a sleeve cuff in the foreground"]),
]
DEFAULT_ANCHORS = ["your own hands in the lower frame", "your shoulder at the frame edge", "the edge of your sleeve", "your fingertips reaching in"]
LENSES = ["14mm ultra-wide", "24mm wide", "35mm", "50mm natural", "85mm close"]
ANGLES = ["eye level", "low angle looking up", "high angle looking down", "over your own shoulder", "tilted, off balance"]
POV_PHRASES = [
    "first-person POV, the camera IS the viewer's eyes, foreground {anchor}, {lens} lens, {angle}, viewer inside the scene",
    "seen through your own eyes, {anchor} in the near foreground, {lens}, {angle}, you are standing right there",
    "your point of view, {angle}, {anchor} close to the lens, {lens}, strong depth",
    "first-person view from inside the moment, {lens}, {angle}, {anchor} framing the scene",
]

def scene_of(text):
    t = str(text or "").lower()
    for name, rx, _ in SCENES:
        if re.search(rx, t): return name
    return ""

def _h(*p): return int(hashlib.sha256("|".join(map(str, p)).encode()).hexdigest()[:8], 16)

def assign_anchors(shots, units, seed="ep"):
    """Sets shot['pov'] = {..., anchor, lens, angle, phrase} for every picture shot: the scene's anchors rotate; lens, angle and phrasing never repeat on
    two consecutive pictures. Deterministic per episode."""
    prev = {"anchor": None, "lens": None, "angle": None, "phrase": None}; scene_last = {}
    from whatifs import path as PATH
    eye = PATH.on(); lenses = LENSES[1:4] if eye else LENSES          # v12 V2b: the camera path - every picture at eye level, a lens among 24mm, 35mm, 50mm
    for i, s in enumerate(shots):
        if s.get("type") not in ("still", "living", "kling"): continue
        line = units[i].get("text", "") if i < len(units) else ""
        sc = scene_of(line + " " + str(s.get("prompt") or "")) or scene_last.get("_", "")
        if sc: scene_last["_"] = sc
        pool = next((a for n, _, a in SCENES if n == sc), DEFAULT_ANCHORS)
        k = _h(seed, i)
        anchor = next((pool[(k + j) % len(pool)] for j in range(len(pool)) if pool[(k + j) % len(pool)] != prev["anchor"]), pool[0])
        lens = next((lenses[(k + j) % len(lenses)] for j in range(len(lenses)) if lenses[(k + j) % len(lenses)] != prev["lens"]), lenses[0])
        angle = ANGLES[0] if eye else next((ANGLES[(k // 7 + j) % len(ANGLES)] for j in range(len(ANGLES)) if ANGLES[(k // 7 + j) % len(ANGLES)] != prev["angle"]), ANGLES[0])
        phrase = next(((k // 13 + j) % len(POV_PHRASES) for j in range(len(POV_PHRASES)) if (k // 13 + j) % len(POV_PHRASES) != prev["phrase"]), 0)
        pv = dict(s.get("pov") or {}); pv.update(anchor=anchor, lens=lens, angle=angle, phrase=phrase, scene=sc); s["pov"] = pv
        prev = {"anchor": anchor, "lens": lens, "angle": angle, "phrase": phrase}
    return shots

def pov_sentence(typ, pv):
    """The first-person sentence for a still (living / kling keep their motion sentences) in one of the phrasings."""
    return POV_PHRASES[int(pv.get("phrase") or 0) % len(POV_PHRASES)].format(anchor=pv.get("anchor") or DEFAULT_ANCHORS[0], lens=pv.get("lens") or LENSES[1],
                                                                             angle=pv.get("angle") or ANGLES[0])

def prompt_variety(shots):
    """{'pictures', 'top_anchor_share', 'top_opening_share'}: how often the most common anchor / the most common first 60 characters repeat."""
    pics = [s for s in shots if s.get("type") in ("still", "living", "kling")]
    if not pics: return {"pictures": 0, "top_anchor_share": 0.0, "top_opening_share": 0.0}
    from collections import Counter
    a = Counter(str((s.get("pov") or {}).get("anchor") or "") for s in pics).most_common(1)[0][1] / len(pics)
    o = Counter(str(s.get("prompt") or "")[:60] for s in pics).most_common(1)[0][1] / len(pics)
    return {"pictures": len(pics), "top_anchor_share": round(a, 3), "top_opening_share": round(o, 3)}

# ---------------------------------------------------------------- Kling on the stakes
def _tags(u): return [str(x).upper() for x in (u.get("show") or [])]

def stakes(units, imp=None):
    """Score of each unit as a Kling moment: CLIPBAIT +3, the final reveal +3, the biggest meter swing +2, the named impact +2, tension / awe +1;
    a plain explanation line (no tag, no show tag) scores 0 and is never chosen."""
    sc = [0.0] * len(units); n = len(units)
    meters = []
    for i, u in enumerate(units):
        tg = _tags(u)
        if "[CLIPBAIT]" in tg: sc[i] += 3
        for t in tg:
            m = re.match(r"\[METER\s*([+-]?\d+)", t)
            if m: meters.append((abs(int(m.group(1))), i))
        if str(u.get("tag")) in ("tension", "awe"): sc[i] += 1
    reveals = [i for i, u in enumerate(units) if str(u.get("tag")) == "reveal" and i >= n * 0.6]
    if reveals: sc[reveals[-1]] += 3
    if meters: sc[max(meters)[1]] += 2
    if imp is not None and 0 <= imp < n: sc[imp] += 2
    return sc

def stakes_top(units, n=2):
    sc = stakes(units); return [i for i in sorted(range(len(units)), key=lambda i: -sc[i])[:n] if sc[i] > 0]

def opening_slot(shots, units, window):
    """The opening clip's unit: the opening line with the highest stakes / a reveal-tension-awe tag; never unit 0, never a tiny line; a plain line only
    when the opening has nothing else. None when the window is empty."""
    sc = stakes(units)
    top = [i for i in sorted(range(len(units)), key=lambda i: -sc[i])[:2] if sc[i] > 0]      # the peak beats are kept for the peak clips (short videos)
    cand = [i for i in window if 0 < i < len(shots) and i not in top and shots[i].get("type") not in ("graphic", "reaction", "stock")
            and words(units[i].get("text")) > S("REACTION_MAX_WORDS", int) and all(abs(i - t) > 1 for t in top)]
    if not cand: return None
    return sorted(cand, key=lambda i: (-sc[i], str(units[i].get("tag")) not in ("reveal", "tension", "awe"), -words(units[i].get("text")), i))[0]

def stake_slots(shots, units, k, imp=None, taken=(), exclude=()):
    """Up to k unit indexes for Kling: highest stakes first, never adjacent to each other or to `taken`, never a graphic / reaction / zero-stakes line."""
    sc = stakes(units, imp); out = []
    def ok(i):
        return 0 < i < len(shots) and i not in exclude and shots[i].get("type") not in ("graphic", "reaction", "stock") and all(abs(i - j) > 1 for j in list(out) + list(taken))
    for i in sorted(range(len(units)), key=lambda i: (-sc[i], i)):              # 1) the scored stakes, best first
        if len(out) >= k or sc[i] <= 0: break
        if ok(i): out.append(i)
    if len(out) < k:                                                             # 2) never fewer clips: the next strongest lines in the back half
        rest = sorted([i for i in range(len(units)) if i >= len(units) // 2 and words(units[i].get("text")) > S("REACTION_MAX_WORDS", int)],
                      key=lambda i: (str(units[i].get("tag")) not in ("reveal", "tension", "awe"), -words(units[i].get("text")), i))
        for i in rest:
            if len(out) >= k: break
            if ok(i): out.append(i)
    return out

# ---------------------------------------------------------------- tiny lines -> reaction cutaways
def words(t): return len(re.findall(r"[A-Za-z0-9']+", str(t or "")))

def reaction_shots(shots, units):
    """Tiny lines become free REACTION cutaways of the speaking character - ONLY where that character has approved art (v12 V2d-b: a character is drawn
    or absent; a line of a character without it keeps its picture). Never a Kling / living / impact / exhibit / clip-bait line. Returns (shots, n_converted)."""
    from whatifs import living as LV
    n = 0; mx = S("REACTION_MAX_WORDS", int); art = {}
    def drawn(spk):
        if spk not in art: art[spk] = LV.has_art(spk)
        return art[spk]
    for i, s in enumerate(shots):
        if i >= len(units) or s.get("type") != "still" or s.get("impact") or s.get("opening_hook") or s.get("promise"): continue
        u = units[i]; tg = _tags(u)
        if any(t.startswith(("[EXHIBIT", "[CLIPBAIT", "[/CLIPBAIT", "[JURY")) for t in tg): continue
        if u.get("speaker") in ("DIRECTOR", "SKEPTIC", "JUDGE", "WITNESS") and words(u.get("text")) <= mx and drawn(u.get("speaker")):
            s["type"] = "reaction"; s["speaker"] = u.get("speaker"); s.pop("prompt", None); n += 1
    return shots, n
