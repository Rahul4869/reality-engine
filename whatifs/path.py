"""The camera path (Visual Production, D6): one place per act seen from where the viewer stands, one direction of travel inside an act, no picture of another act. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import math, re
from whatifs.core import S, log

MOVES = ("push_parallax", "drift", "handheld", "rack_focus", "orbit", "whip_settle")      # never "pull" (backwards), never "kb_roll" (it rolls the horizon)
SENTENCE = "ONE PLACE FOR THIS ACT"
KLING_MOTION = "first-person view at eye level, the camera moving forward with the viewer's own steps while the impossible thing moves in front of him. "
WALK_LIVING = "first-person eye-level view, moving forward at a slow walking pace, particles drifting past the lens. "
DIRECTOR = ("ONE PLACE PER BEAT, SEEN FROM WHERE THE VIEWER STANDS (this format; code enforces it): every still, living and kling picture is seen "
            "through the viewer's own eyes at his own standing height - never from above, from far away, from outside the place or from an "
            "object; \"pov\" is eyes or hands only, with one foreground anchor (his hands, a door frame, a cup). Every shot of a beat stays in "
            "the place that beat's visual_world names: write each prompt as another look at THAT place - what is ahead of him, what is at his "
            "feet, what his hand touches - never a new location, never an aerial or establishing view. A consequence as big as the planet is "
            "shown as what he can see of it from where he stands: the sky, the horizon, the street. Camera moves: push_parallax, drift, handheld, "
            "rack_focus or orbit only - never pull, never kb_roll, never pov_rush away from him.")
PICTURES = ("still", "living", "kling")

def on():
    """The camera path runs for the episode in the making: CAMERA_PATH_ON and its format's camera is 'path' (F1) or 'walk' (F3); a 'cut' format (the trial) never."""
    from whatifs import formats as FMT
    return S("CAMERA_PATH_ON", bool) and FMT.camera() in ("path", "walk")

def on_units(units):
    """... and its units know their beats (a timeline saved before this batch has no key `beat`: nothing here runs, both checks say why)."""
    return on() and bool(units) and all(isinstance(u, dict) and "beat" in u for u in units)

def director_rules(): return DIRECTOR

def allowance(total):
    """How many changes of place a film of `total` seconds may have: max(3, floor(PLACE_CHANGES_PER_MIN_MAX x minutes))."""
    return max(3, int(math.floor(S("PLACE_CHANGES_PER_MIN_MAX", float) * float(total) / 60.0 + 1e-9)))

def acts(shots, units, total):
    """THE ACTS (pure): consecutive units with the same `beat` are one act; the units whose shots are the Short's footage (opening.marked) belong to no
    act. Joined in this order: (1) an act whose lines last less than ACT_MIN_S joins the act BEFORE it (the first act joins the act after it); (2) while
    the changes of place (acts - 1) are more than the allowance, the SHORTEST act joins the act before it (the first joins the act after it; of two equally
    short the later one). A joined act keeps the beat number of its first beat. Returns [{beat, units, from_s, to_s, s}] (s = seconds of its lines)."""
    from whatifs import motion as MOT
    sp = MOT.lines_of(units, total); foot = {i for i, s in enumerate(shots or []) if isinstance(s, dict) and s.get("short")}
    out = []
    for i, u in enumerate(units):
        if i in foot: continue
        b = int(u.get("beat") or 0)
        if out and out[-1]["beat_last"] == b: out[-1]["units"].append(i)
        else: out.append({"beat": b, "beat_last": b, "units": [i]})
    dur = lambda a: sum(sp[i][1] - sp[i][0] for i in a["units"])
    def join(k, into):                                      # act k joins act `into` (its neighbour); the joined act keeps the first beat's number
        a, b = (out[into], out[k]) if into < k else (out[k], out[into])
        a["units"] = sorted(a["units"] + b["units"]); a["beat_last"] = b["beat_last"]; out.remove(b)
    lim = S("ACT_MIN_S", float)
    while len(out) > 1:
        k = next((j for j, a in enumerate(out) if dur(a) < lim - 1e-9), None)
        if k is None: break
        join(k, k - 1 if k > 0 else 1)
    allow = allowance(total)
    while len(out) - 1 > allow:
        k = min(range(len(out)), key=lambda j: (dur(out[j]), -j))
        join(k, k - 1 if k > 0 else 1)
    return [{"beat": a["beat"], "units": list(a["units"]), "from_s": round(sp[a["units"][0]][0], 3), "to_s": round(sp[a["units"][-1]][1], 3), "s": round(dur(a), 3)} for a in out]

def place_of(act, bible, units=None, before=""):
    """THE PLACE OF AN ACT: the `visual_world` of the bible beat whose `n` EQUALS the act's beat, cut to its first 10 words without a final full stop; when
    the bible has no such beat or an empty one, the first name shotplan.scene_of finds in the act's lines joined; when neither, the place of the act
    before (the first act: 'your home')."""
    from whatifs import shotplan as SP
    for b in ((bible or {}).get("beats") or []):
        try: n = int(b.get("n"))
        except (TypeError, ValueError, AttributeError): continue
        if n == int(act["beat"]):
            w = " ".join(str(b.get("visual_world") or "").split()[:10]).rstrip(".")
            if w: return w
            break
    sc = SP.scene_of(" ".join(str((units or [])[i].get("text") or "") for i in act["units"] if i < len(units or [])))
    return sc or before or "your home"

def sign_of(ep, act_beat, cam):
    """One direction of travel: per act in 'path' (+1 or -1 from the id and the act), ONE for the whole video in 'walk'."""
    from whatifs import shotplan as SP
    if cam == "walk": return 1 if SP._h(ep, "walk") % 2 == 0 else -1
    return 1 if SP._h(ep, act_beat) % 2 == 0 else -1

def mark(shots, units, total, bible, ep):
    """THE MARKS COME FIRST (before the Animation Director and motion.place): every shot of an act gets `path` = {act, place, sign, first} - `first` True on
    the act's first shot whose type is still, living or kling now (after this a still may become living or kling, a picture of its own); an act with no
    such shot has no `first`. Returns (shots, the plan's acts [{act, place, from_s, to_s, sign}]). Nothing when off or the units carry no beats."""
    if not on_units(units): return shots, []
    from whatifs import formats as FMT
    cam = FMT.camera(); out = [dict(s) for s in shots]; plan = []; prev = ""
    for a in acts(out, units, total):
        pl = place_of(a, bible, units, prev); prev = pl; sg = sign_of(ep, a["beat"], cam); first = None
        for i in a["units"]:
            if i >= len(out): continue
            if first is None and out[i].get("type") in PICTURES: first = i
            out[i]["path"] = {"act": a["beat"], "place": pl, "sign": sg, "first": i == first}
        plan.append({"act": a["beat"], "place": pl, "from_s": a["from_s"], "to_s": a["to_s"], "sign": sg})
    log(f"camera path: {len(plan)} act(s) in {len({p['place'] for p in plan})} place(s): " + " | ".join(p["place"] for p in plan)[:300])
    return out, plan

def lay(shots):
    """THE WORDS LAST (after motion.place, the last step before the script gate; it changes no type): every still or living shot with a `path` mark and none
    of the marks short / promise / anim gets, once, the act's place sentence in front of its prompt."""
    out = []
    for s in shots:
        s = dict(s); pm = s.get("path")
        if pm and s.get("type") in ("still", "living") and not (s.get("short") or s.get("promise") or s.get("anim")) and SENTENCE not in str(s.get("prompt") or ""):
            s["prompt"] = sentence(pm["place"]) + str(s.get("prompt") or "")
        out.append(s)
    return out

def sentence(place): return f"{SENTENCE}: {place}, the same light and weather as the shot before, seen at eye level. "

# ------------------------------------------------------------------ the two checks (measures; contract.py says PASS / FAIL / N/A)
def why_na(fmt, units):
    """'' when the camera path is judged for this episode, else the reason both checks give."""
    from whatifs import formats as FMT
    if not S("CAMERA_PATH_ON", bool): return "the camera path is switched off (CAMERA_PATH_ON)"
    if fmt not in FMT.FORMATS: return "no format on this episode (written before formats existed, or FORMATS_ON is off)"
    if FMT.camera(fmt) == "cut": return f"format {fmt} cuts between its pictures"
    if not units or not all(isinstance(u, dict) and "beat" in u for u in units): return "made before the camera path"
    return ""

def plan_report(shots, units, total, anchors):
    """camera_path on the shot list, BEFORE any picture is paid: problems for (1) a shot of an act without its mark, (2) an act's first still that gets no
    picture of its own (`anchors` = what the asset step will make), (3) a picture whose angle code assigned and is not eye level, (4) a still or living
    shot without the marks short / promise / anim that does not hold its act's place sentence, (5) an act shorter than ACT_MIN_S beside another, or more
    changes of place than the allowance (the joins did not run). Returns {acts, places, changes, allow, minutes, angles, problems}."""
    p = []; want = acts(shots, units, total); anchors = set(anchors or ())
    for a in want:
        for i in a["units"]:
            if i < len(shots) and not shots[i].get("path"): p.append(f"shot {i} of act {a['beat']} has no camera-path mark"); break
    have = {}
    for i, s in enumerate(shots):
        pm = s.get("path")
        if not pm: continue
        have.setdefault(pm["act"], {"place": pm["place"], "units": []})["units"].append(i)
        if pm.get("first") and s.get("type") == "still" and i not in anchors: p.append(f"act {pm['act']} would open on a picture made for another act")
        if s.get("type") in ("still", "living") and not (s.get("short") or s.get("promise") or s.get("anim")) and sentence(pm["place"]) not in str(s.get("prompt") or ""):
            p.append(f"shot {i} does not hold the place of act {pm['act']}")
    angles = [str((s.get("pov") or {}).get("angle")) for s in shots if s.get("type") in PICTURES and (s.get("pov") or {}).get("angle")]
    bad = [a for a in angles if a != "eye level"]
    if bad: p.append(f"{len(bad)} picture(s) not at eye level: '{bad[0]}'")
    from whatifs import motion as MOT
    sp = MOT.lines_of(units, total); secs = {k: sum(sp[i][1] - sp[i][0] for i in v["units"] if i < len(sp)) for k, v in have.items()}
    allow = allowance(total)
    if len(have) > 1 and any(v < S("ACT_MIN_S", float) - 1e-9 for v in secs.values()) or len(have) - 1 > allow:
        p.append(f"{len(have)} acts, one shorter than {S('ACT_MIN_S', float):g} s or more than {allow} changes of place: the joins did not run")
    places = [have[k]["place"] for k in have]
    return {"acts": len(have), "places": places, "changes": max(0, len(have) - 1), "allow": allow, "minutes": round(float(total) / 60.0, 1),
            "angles": bool(angles), "problems": list(dict.fromkeys(p))}

def shown_report(states, shots):
    """camera_shown on what the RENDER recorded (ctx['path_states'], never the plan): for every state of type still with an act - its picture (`src`) is a
    picture of its own act; unless it is a fall-back its move is in MOVES (recorded); its sign is its act's sign. Returns {states, acts, moves, problems}."""
    p = []; moves = {}; acts_ = set(); n = 0
    act_of = {i: (s.get("path") or {}).get("act") for i, s in enumerate(shots or []) if s.get("path")}
    sign_of_ = {(s.get("path") or {}).get("act"): (s.get("path") or {}).get("sign") for s in shots or [] if s.get("path")}
    for st in states or []:
        if st.get("type") != "still" or st.get("act") is None: continue
        n += 1; a = st["act"]; acts_.add(a); t = float(st.get("t0") or 0)
        src = st.get("src"); b = act_of.get(src)
        if src is None or b != a: p.append(f"at {t:.1f} s act {a} showed a picture made for act {b if src is not None else 'none'}")
        if not st.get("fallback"):
            if st.get("move") not in MOVES: p.append(f"at {t:.1f} s the camera moved backwards, rolled or was not recorded: '{st.get('move') or ''}'")
            else: moves[st["move"]] = moves.get(st["move"], 0) + 1
        if not st.get("fallback") and st.get("sign") != sign_of_.get(a): p.append(f"at {t:.1f} s the camera travelled against act {a}'s direction")
    return {"states": n, "acts": len(acts_), "moves": moves, "problems": list(dict.fromkeys(p))}
