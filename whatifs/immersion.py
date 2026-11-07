"""whatifs/immersion.py v8.10 - "the viewer is inside the scene" (IMMERSION_ON, POV_CAMERA_ON).
1. The IMMERSION DIRECTOR (a writers'-room role, one Sonnet call) maps the final script: for each key moment the first-person vantage (the camera IS the object
   or the viewer's eyes), the body sensation, the sensory stack, a free camera event and the sound event locked to it; it names the single impact moment.
2. First-person rules on EVERY picture prompt (owner rule): stills (foreground anchors such as hands, a helmet rim, debris streaks, heat shimmer, extreme wide
   lens, motion blur), living stills (eye-level breathing sway, particles close to the lens) and Kling clips (camera mounted on the moving object,
   accelerating, shaking). Stock footage and code-drawn graphics cannot be re-shot, so they get the same camera EFFECTS in render instead.
3. The Kling clips are spent on the peak and impact sequence (the run-up, the impact, the aftermath); v8.11: KLING_OPENING_CLIPS of them (default 1)
   stay in the opening window as a first-person rush hook.
4. Camera events (render.pov_fx: pov_rush, impact_shake, debris) are applied to every shot type and locked to sound events (sound.immersive)."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, scrub
from whatifs import prompts as P

POV_MOVES = ("pov_rush", "impact_shake", "debris")
SOUNDS = ("rumble", "riser", "silence", "boom", "ringing", "heartbeat", "breath", "creak", "drip", "none")

def on(): return S("IMMERSION_ON", bool)

def writer_rules():
    """Extra rules for the writer: POV + present tense second person in the podcast format, the emotion curve, and film-edit pacing."""
    out = []
    if on():
        out.append("IMMERSION (owner rule): in the simulation scenes the viewer is INSIDE the scene. The Director narrates in the PRESENT TENSE, SECOND PERSON "
                   "('you feel the floor tilt'); the guest reacts PHYSICALLY in character (a breath, a gasp, a nervous laugh), never just 'wow'. Withhold and "
                   "suggest; let silence work; cut to black before the obvious.")
    if S("EMOTION_CURVE_ON", bool):
        out.append("VOICE ACTING: after the tags, give each line its delivery curve in braces, e.g. '[SKEPTIC] [tension] {slow, low, whisper, breath} It's... "
                   "breathing.' Words: slow fast low high soft loud whisper hushed rising falling shaky breathless tense warm awed dry; vocal events: breath gasp "
                   "laugh chuckle sigh exhale pant. Whisper at suspense, a breath before every reveal, a gasp or laugh where a real person would. The braces are "
                   "never spoken. Energy must move up AND down across the video (never one flat level).")
        out.append("PACING LIKE FILM EDITING: cut on the beat, vary sentence length (a long line, then two words), use [pause:short]/[pause:long] on purpose, "
                   "and land the hook inside the first 3-8 seconds.")
    return "\n".join(out)

def director_rules():
    if not on(): return ""
    return ("FIRST-PERSON POV (owner rule, EVERY shot type): every still, living and kling prompt is shot from INSIDE the scene: the camera is the viewer's eyes or "
            "the moving object; give each shot \"pov\": eyes|object|hands|helmet|vehicle|ground and one foreground anchor (your hands, a helmet rim, debris "
            "streaks, heat shimmer), extreme wide lens, motion blur. Kling = camera mounted on the moving object, accelerating, shaking. Camera may also be "
            "pov_rush | impact_shake | debris (free code moves, also allowed on stock and graphic shots) on the run-up and the impact.")

def immersion_map(script_text, spine, episode):
    """One Sonnet call. Returns {'scenes': [...], 'peak_quote': ''}; {} on any failure (never blocks)."""
    if not on(): return {}
    from whatifs.models import ask
    from whatifs import craft as CR
    try:
        m = ask("immersion", P.fill(P.IMMERSION, constitution=CR.constitution(), script=script_text[:24000]), "Map the scenes now.", episode=episode,
                fake_key="immersion", max_tokens=5000, temperature=0.6)
    except Exception as e:
        log(f"Immersion Director unavailable ({scrub(e)[:120]}) - shots planned without the map", "WARN", episode); return {}
    scenes = []
    for x in (m.get("scenes") or [])[:40]:
        if not isinstance(x, dict) or not str(x.get("quote") or "").strip(): continue
        scenes.append({"quote": str(x["quote"])[:120], "vantage": x.get("vantage") if x.get("vantage") in ("eyes", "object", "hands", "helmet", "vehicle", "ground") else "eyes",
                       "body": str(x.get("body") or "")[:120], "senses": [str(s)[:60] for s in (x.get("senses") or [])][:3],
                       "camera": x.get("camera") if x.get("camera") in POV_MOVES else "none", "sound": x.get("sound") if x.get("sound") in SOUNDS else "none",
                       "impact": bool(x.get("impact"))})
    return {"scenes": scenes, "peak_quote": str(m.get("peak_quote") or "")[:160]}

def _match(quote, units):
    qw = set(re.findall(r"[a-z']{3,}", quote.lower()))
    if not qw: return None
    best, bi = 0.0, None
    for i, u in enumerate(units):
        uw = set(re.findall(r"[a-z']{3,}", str(u.get("text", "")).lower()))
        if not uw: continue
        sc = len(qw & uw) / len(qw)
        if sc > best: best, bi = sc, i
    return bi if best >= 0.5 else None

def anchor_for(text):
    from whatifs.data import POV_ANCHORS, POV_ANCHOR_DEFAULT
    t = str(text or "").lower()
    return next((a for rx, a in POV_ANCHORS if re.search(rx, t)), POV_ANCHOR_DEFAULT)

def pov_prompt(shot, line=""):
    """The first-person rules appended to a picture / clip prompt (idempotent). Stock and graphic shots are left alone (they get render effects)."""
    from whatifs.data import POV_STILL, POV_LIVING, POV_KLING
    typ = shot.get("type"); p = str(shot.get("prompt") or line or "")
    if typ not in ("still", "living", "kling") or "first-person POV" in p: return p
    pv = shot.get("pov") or {}
    anchor = pv.get("anchor") or anchor_for(p + " " + line)
    rule = {"still": POV_STILL, "living": POV_LIVING, "kling": POV_KLING}[typ].format(anchor=anchor)
    if typ == "still" and "phrase" in pv:                            # v9.2: one of several first-person phrasings with its own lens / angle
        from whatifs import shotplan as SP
        rule = SP.pov_sentence(typ, pv)
    if pv.get("body"): rule += f", the feeling of {pv['body']}"
    return f"{rule}. {p}"

def apply(shots, units, imap, plan, episode=None):
    """Attach the map to the shots, put the POV rules on every picture/clip prompt, put the Kling clips on the peak + impact sequence, and give the run-up
    and the impact their camera events. Returns a NEW list. Counts never change (same cost)."""
    if not on(): return shots
    out = [dict(s) for s in shots]; scenes = (imap or {}).get("scenes") or []
    for sc in scenes:
        i = _match(sc["quote"], units)
        if i is None or i >= len(out): continue
        out[i]["pov"] = {"vantage": sc["vantage"], "body": sc["body"], "senses": sc["senses"], "sound": sc["sound"], "anchor": anchor_for(units[i].get("text", ""))}
        if sc["camera"] in POV_MOVES and S("POV_CAMERA_ON", bool): out[i]["pov_fx"] = sc["camera"]
        if sc.get("impact"): out[i]["impact"] = True
    imp = next((i for i, s in enumerate(out) if s.get("impact")), None)
    if imp is None and imap and imap.get("peak_quote"): imp = _match(imap["peak_quote"], units)
    if imp is None:                                     # no named impact: the last kling shot (the peak the Director chose) is the impact
        ks = [i for i, s in enumerate(out) if s.get("type") == "kling"]; imp = ks[-1] if ks else None
    n = int((plan or {}).get("kling") or sum(1 for s in out if s.get("type") == "kling"))
    hook = opening_hook(out, units, n, imp)                      # v8.11: KLING_OPENING_CLIPS clips stay in the opening as a POV rush hook
    from whatifs import v91 as V91
    stake = None
    if V91.on("KLING_STAKES_ON", episode):                       # v9.2: the other clips on the highest-stakes beats, never adjacent, never a plain line
        with V91.guard("KLING_STAKES_ON", episode):
            from whatifs import shotplan as SP
            from whatifs.room import opening_units as _ou
            stake = SP.stake_slots(out, units, max(0, n - len(hook)), None, hook, exclude=set(_ou(units)) - set(SP.stakes_top(units)) if hook else ())
            if stake:
                if imp is not None and imp not in stake: out[imp].pop("impact", None)
                imp = stake[0]                                                  # the impact = the highest-stakes clip
    if imp is not None:
        out[imp]["impact"] = True
        want = hook + (stake if stake else [x for x in (imp, imp - 1, imp + 1, imp - 2, imp + 2) if 0 <= x < len(out) and out[x].get("type") not in ("graphic", "reaction") and x not in hook][:max(0, n - len(hook))])
        have = [i for i, s in enumerate(out) if s.get("type") == "kling"]
        for d, r in zip([i for i in have if i not in want], [i for i in want if out[i].get("type") != "kling"]):
            out[d]["type"] = "still"; out[r]["type"] = "kling"; out[r]["hero"] = True
            out[r]["prompt"] = out[r].get("prompt") or units[r].get("text", "")
        if S("POV_CAMERA_ON", bool):
            out[imp]["pov_fx"] = "impact_shake"
            if imp - 1 >= 0 and not out[imp - 1].get("pov_fx"): out[imp - 1]["pov_fx"] = "pov_rush"
            if imp + 1 < len(out) and not out[imp + 1].get("pov_fx"): out[imp + 1]["pov_fx"] = "debris"
    if V91.on("POV_VARIETY_ON", episode):                          # v9.2: scene-aware anchors; lens / angle / phrasing vary between pictures
        with V91.guard("POV_VARIETY_ON", episode):
            from whatifs import shotplan as SP
            SP.assign_anchors(out, units, episode or "ep")
    for i in hook:
        if out[i].get("type") == "kling":
            out[i]["hero"] = True; out[i]["opening_hook"] = True
            if S("POV_CAMERA_ON", bool) and not out[i].get("impact"): out[i]["pov_fx"] = "pov_rush"
    for i, s in enumerate(out):
        if s.get("type") in ("still", "living", "kling"):
            s["prompt"] = pov_prompt(s, units[i].get("text", "") if i < len(units) else "")
            if s.get("type") == "kling" and "camera mounted" not in str(s.get("motion") or ""):
                s["motion"] = "first-person camera mounted on the moving object, accelerating, shaking, debris streaking past the lens. " + str(s.get("motion") or "")
            if s.get("type") == "living" and "breathing sway" not in str(s.get("motion") or ""):
                s["motion"] = "first-person eye-level view, slow breathing sway, particles drifting close to the lens. " + str(s.get("motion") or "")
        cam = str(s.get("camera") or "").lower()
        if cam in POV_MOVES:                            # a Director suggestion of a POV move works on every shot type
            s.pop("camera", None)
            if S("POV_CAMERA_ON", bool): s.setdefault("pov_fx", cam)
    return out

def opening_hook(out, units, n, imp=None):
    """v8.11 (K93): the unit indexes that keep a Kling clip INSIDE the opening window (OPENING_WINDOW_SEC) as the first-person rush hook: at most
    KLING_OPENING_CLIPS and never all of the clips while an impact needs one. A Kling clip already in the window is kept (the Director chose it);
    otherwise the strongest opening line (reveal / tension / awe first, never the very first unit, never a graphic) receives one moved from elsewhere.
    Moved, never added: the clip count and the cost do not change. [] when units carry no timing or the setting is 0 (v8.10)."""
    k = min(max(0, S("KLING_OPENING_CLIPS", int)), max(0, n - (1 if imp is not None else 0)))      # the impact always keeps a clip
    if k <= 0: return []
    from whatifs.room import opening_units
    op = [i for i in opening_units(units) if i < len(out) and i != imp and out[i].get("type") != "graphic"]
    if not op: return []
    from whatifs import v91 as V91
    if k == 1 and V91.on("KLING_STAKES_ON"):                       # v9.2: the strongest opening line, not whichever line already had a clip
        from whatifs import shotplan as SP
        best = SP.opening_slot(out, units, op)
        if best is not None: return [best]
    keep = [i for i in op if out[i].get("type") == "kling"][:k]
    rest = sorted([i for i in op if i not in keep and i > 0], key=lambda i: (str(units[i].get("tag")) not in ("reveal", "tension", "awe"), i))
    return sorted(keep + rest[: k - len(keep)])

def camera_sound_events(shots, units):
    """[(kind, seconds)] for the mixer, locked to the camera events: pov_rush -> a Doppler pass + riser ending on the cut; impact_shake -> the impact recipe;
    debris -> close crackle. Times are the units' starts on the narration clock (the same frame the camera event starts)."""
    ev = []
    for i, s in enumerate(shots):
        if i >= len(units) or not s.get("pov_fx"): continue
        t = float(units[i]["start"]); fx = s["pov_fx"]
        if fx == "impact_shake": ev.append(("impact", t))
        elif fx == "pov_rush":
            nxt = float(units[i + 1]["start"]) if i + 1 < len(units) else t + 3.0
            ev.append(("doppler", t)); ev.append(("rush_end", nxt))
        elif fx == "debris": ev.append(("debris", t))
    return ev
