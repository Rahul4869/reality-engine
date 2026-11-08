"""whatifs/shotplan.py v9.2 (K108) - shot-plan fixes found by reading the first real preview's 80-shot list. Code only; never adds a paid shot.

1. KLING ON THE STAKES (KLING_STAKES_ON): one clip stays in the opening (v8.11 hook); the others go to the highest-stakes beats - the [CLIPBAIT] moment,
   the final reveal, the biggest Jury Meter swing, the named impact - never next to another clip, never on a plain explanation line, never on a graphic.
2. SCENE-AWARE POV ANCHORS (POV_VARIETY_ON): the foreground anchor comes from the SCENE of the line (bathroom, kitchen, hallway, window, bedroom, living
   room, street, space, water, fire...) matched on whole words (the old rule matched 'ring' inside 'bring' and 'wave' inside 'light wave'); anchor, lens
   and angle rotate so consecutive pictures differ, and the first-person sentence has several phrasings. prompt_variety() measures one episode.
3. TINY LINES (REACTION_SHOTS_ON): lines of at most REACTION_MAX_WORDS words ('Fine.', 'A fifth.') become a code-made REACTION cutaway of the speaking
   character (no image bought) instead of yet another near-identical still; the cutaway also appears at every speaker change of a Director / Skeptic
   exchange when that line is short, so the characters are visible before the sheets are approved. Cost never goes up (fewer images are bought)."""
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
    if shot_type in ("graphic", "reaction") or not V91.on("MICRO_CUTS_ON", episode): return base
    res = base
    with V91.guard("MICRO_CUTS_ON", episode):
        mx = S("PIECE_MAX_SEC_OPENING" if opening else "PIECE_MAX_SEC", float); mn = max(0.5, S("PIECE_MIN_SEC", float))
        if mx > 0: res = max(base, min(int(math.ceil(float(dur) / mx - 1e-9)), max(1, int(float(dur) // mn)), 8))
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
    for i, s in enumerate(shots):
        if s.get("type") not in ("still", "living", "kling"): continue
        line = units[i].get("text", "") if i < len(units) else ""
        sc = scene_of(line + " " + str(s.get("prompt") or "")) or scene_last.get("_", "")
        if sc: scene_last["_"] = sc
        pool = next((a for n, _, a in SCENES if n == sc), DEFAULT_ANCHORS)
        k = _h(seed, i)
        anchor = next((pool[(k + j) % len(pool)] for j in range(len(pool)) if pool[(k + j) % len(pool)] != prev["anchor"]), pool[0])
        lens = next((LENSES[(k + j) % len(LENSES)] for j in range(len(LENSES)) if LENSES[(k + j) % len(LENSES)] != prev["lens"]), LENSES[0])
        angle = next((ANGLES[(k // 7 + j) % len(ANGLES)] for j in range(len(ANGLES)) if ANGLES[(k // 7 + j) % len(ANGLES)] != prev["angle"]), ANGLES[0])
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
    """Tiny lines become free REACTION cutaways (speaker card). Never a Kling / living / impact / exhibit / clip-bait line. Returns (shots, n_converted)."""
    n = 0; mx = S("REACTION_MAX_WORDS", int)
    for i, s in enumerate(shots):
        if i >= len(units) or s.get("type") != "still" or s.get("impact") or s.get("opening_hook") or s.get("promise"): continue
        u = units[i]; tg = _tags(u)
        if any(t.startswith(("[EXHIBIT", "[CLIPBAIT", "[/CLIPBAIT", "[JURY")) for t in tg): continue
        if u.get("speaker") in ("DIRECTOR", "SKEPTIC", "JUDGE", "WITNESS") and words(u.get("text")) <= mx:
            s["type"] = "reaction"; s["speaker"] = u.get("speaker"); s.pop("prompt", None); n += 1
    return shots, n

# ---------------------------------------------------------------- the reaction card (render)
def reaction_frame(speaker, bg, W, H, t, line=""):
    """One frame of a reaction cutaway: the previous picture blurred and graded in the character's colour, a procedural silhouette of the character with
    one unmistakable feature (Vale: glasses; Grimm: high collar + red pocket square; Rosa: hair bun + teacup; Archivist: shelves), the name, and the
    character's camera grammar (tilt / handheld / drift). Deterministic in t."""
    import numpy as np, cv2
    from PIL import Image, ImageDraw
    from whatifs.overlay import COLOURS, name_of
    from whatifs.media import font
    base = cv2.GaussianBlur(cv2.resize(bg, (W, H)), (0, 0), 18) if bg is not None else np.full((H, W, 3), 30, np.uint8)
    col = COLOURS.get(speaker, (200, 200, 200))
    base = (base.astype(np.float32) * 0.45 + np.array(col[::-1], np.float32)[None, None, :] * 0.18).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im)
    cx, cy, r = W * 0.5, H * 0.46, H * 0.16; sil = (12, 12, 16)
    d.ellipse((cx - r, cy - r * 1.2, cx + r, cy + r * 0.9), fill=sil)                                    # head
    d.polygon([(cx - r * 2.4, H), (cx - r * 1.1, cy + r * 1.1), (cx + r * 1.1, cy + r * 1.1), (cx + r * 2.4, H)], fill=sil)   # shoulders
    if speaker == "DIRECTOR":
        for dx in (-0.45, 0.45): d.ellipse((cx + dx * r - r * 0.32, cy - r * 0.25, cx + dx * r + r * 0.32, cy + r * 0.1), outline=(200, 210, 220), width=max(2, int(H * 0.006)))
    elif speaker == "SKEPTIC":
        d.polygon([(cx - r * 1.3, cy + r * 1.0), (cx - r * 0.6, cy - r * 0.2), (cx - r * 0.4, cy + r * 1.2)], fill=sil); d.polygon([(cx + r * 1.3, cy + r * 1.0), (cx + r * 0.6, cy - r * 0.2), (cx + r * 0.4, cy + r * 1.2)], fill=sil)
        d.rectangle((cx + r * 0.9, cy + r * 1.6, cx + r * 1.25, cy + r * 1.85), fill=(200, 30, 40))
    elif speaker == "JUDGE":
        d.ellipse((cx - r * 0.45, cy - r * 1.75, cx + r * 0.45, cy - r * 0.95), fill=sil)
        d.chord((cx + r * 1.4, cy + r * 1.7, cx + r * 2.2, cy + r * 2.4), 0, 180, fill=(235, 225, 210))
    elif speaker == "WITNESS":
        for k in range(4): d.line((W * 0.08, H * (0.2 + 0.18 * k), W * 0.92, H * (0.2 + 0.18 * k)), fill=(60, 55, 50), width=max(2, int(H * 0.008)))
    f = font(int(H * 0.05)); nm = name_of(speaker); tw = d.textlength(nm, font=f)
    d.text((cx - tw / 2, H * 0.83), nm, font=f, fill=tuple(col))
    out = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    try:
        from whatifs import v91 as V91, herostill as HS
        if V91.on("CHAR_GRAMMAR_ON"): out = HS.apply_grammar(out, speaker, t)
    except Exception: pass
    return out

def reaction_segment(speaker, bg_path, path, nframes):
    """Render a reaction cutaway through the normal frame pipe (overlay stack, cursor, encoder)."""
    import cv2
    from whatifs import render as RN
    W, H = RN.work_size(); bg = cv2.imread(bg_path) if bg_path else None
    RN._pipe(path, (reaction_frame(speaker, bg, W, H, k / RN.fps()) for k in range(nframes)), nframes, W, H)
