"""The opening (Visual Production, D6): a long video about a promoted Short opens on that Short's kept footage - fetched from its archive, laid by code under the first sentences, shown through one window whose width follows the clip's real sharpness, and proven on the shot list and on the finished film. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, re, shutil, subprocess, zipfile
from whatifs.core import S, log, scrub

DIR = "short_footage"                                      # where a video's working folder keeps the unpacked archive of its Short
NAMES = re.compile(r"^(c\d+\.mp4|f\d+\.png|short\.json)$")   # the only names an archive may bring (ladder.keep writes no others)
MODES = ("auto", "fill", "whole")                          # OPENING_FIT: the widest window the sharpness allows | the frame filled, whatever it costs | the whole upright clip
SAME_MIN = 0.5                                             # how alike (-1 .. 1) a frame of the finished film and the frame of the footage it must show have to be (measured: the same footage under the trial's grade 0.8 and more, other pictures under 0.3)
GRID = (64, 36)                                            # the small grey copy both frames are compared on
FLAT = 1.0                                                 # a footage frame with less detail than this (grey levels) has nothing to recognise: it is not compared
REGION = (0.2, 0.8, 0.15, 0.85)                            # the part of the frame that is compared (x from, x to, y from, y to): its middle - no chip, no bar, no edge of the window
EVERY_S = 0.5                                              # the finished film is compared with the footage this often inside every stretch of a clip
EDGE_S = 0.2                                               # ... and never this close to where two clips meet (or the shot begins or ends): film and clip can be a frame apart there
MIN_PART_S = 0.02

def on():
    """Does a long video open on its Short's footage? Only while the ladder binds long videos (there is no Short without it)."""
    from whatifs import ladder as LAD
    return S("OPENING_SHORT_ON", bool) and LAD.on()

def source(d):
    """(kind, ladder row) for an episode's draw: 'short' = it is about a promoted Short (its footage must open it), 'override' = made under an
    override (no Short, no footage), 'none' = the draw names no ladder row (check topic_ladder judges that), 'off' = switched off."""
    from whatifs import ladder as LAD
    if not on(): return "off", None
    r = LAD.row(str((d or {}).get("ladder") or ""))
    if not r: return "none", None
    return ("override" if str(r.get("state") or "").startswith("OVERRIDE") else "short"), r

def none_words(kind, r=None):
    """Why a video has no footage to open on, in plain words (the evidence of a check that does not apply)."""
    if kind == "override":
        return (f"made under override {r.get('id')} ({r.get('by')}): there is no Short and no footage - it opens on the hook lab's line and its own animated "
                "promise scene, which viewer_promise and promise_paid judge")
    if kind == "none": return "the draw names no ladder row (check topic_ladder judges where the topic comes from)"
    return "the opening from the Short's footage is switched off (OPENING_SHORT_ON, or the ladder)"

# ------------------------------------------------------------------ the footage: fetched, unpacked, measured
def manifest(meta, wd):
    """What an unpacked archive holds, measured on the files themselves: every clip of the Short's plan but the loop (pixels, seconds, SHA-256) and
    the Short's PICTURE TRACK - which clip was on screen from when to when, slowed exactly as the Short played it. Raises when a clip is missing."""
    from whatifs import release as REL, shorts2 as SH
    shots = [s for s in ((meta.get("plan") or {}).get("shots") or []) if isinstance(s, dict) and s.get("src") != "loop"]
    clips, track = {}, []
    for s in sorted(shots, key=lambda x: float(x.get("start") or 0)):
        name = f"c{int(s['i'])}.mp4"; p = os.path.join(wd, name)
        if not os.path.exists(p): raise RuntimeError(f"clip {name} of the Short's plan is not in the archive")
        pr = REL.probe(p)
        if pr["w"] <= 0 or pr["h"] <= 0 or pr["sec"] <= 0: raise RuntimeError(f"clip {name} cannot be read")
        clips[name] = {"sha": REL.sha(p), "w": pr["w"], "h": pr["h"], "sec": pr["sec"]}
        a, b = float(s["start"]), float(s["end"])
        if b - a >= 0.05: track.append({"clip": name, "start": round(a, 3), "end": round(b, 3), "slow": round(SH.slow_of(s), 4)})      # v12 V2d: how the Short really played it - on its own plan since clips are bought by the second
    if not track: raise RuntimeError("the archive holds no clip of the Short's plan")
    return {"hook": hook_of((meta.get("timeline") or {}).get("units") or []), "seconds": track[-1]["end"], "clips": clips, "track": track}

def hook_of(units):
    """v12 V2b (issue 129): a Short's hook - the FIRST unit of its own voice timeline, its brackets removed, its spaces made one. The ONE definition:
    the archive's manifest (the long video's inserted first line) and the Short's ladder row (`shorts2.run` -> `ladder.enter`, field `hook_line`,
    the line the long video's writer is handed) both call it."""
    return " ".join(re.sub(r"\[[^\]]*\]", " ", str((units[0] if units else {}).get("text") or "")).split())

def fetch(d, out):
    """The footage of the Short this long video is about, in the video's working folder: the archive named on the Short's ladder row is downloaded
    (free), only its own file names are unpacked, an archive that names another Short is refused, every clip is measured. Returns the manifest
    {short, footage, hook, seconds, clips, track} - or {none: kind, why} when there is nothing to open on (an override, switched off) or the
    footage is missing or broken (then check opening_footage holds the video before any picture is paid). Never raises."""
    kind, r = source(d)
    if kind != "short": return {"none": kind, "short": "", "why": none_words(kind, r)}
    sid = str(r["id"]); fid = str(r.get("footage") or "")
    if not fid: return {"none": "missing", "short": sid, "why": f"the footage of Short {sid} was not kept when the Short was made (its ladder row names no archive)"}
    wd = os.path.join(out, DIR)
    try:
        from whatifs import publish as PUB
        have = os.path.join(wd, "short.json")
        if not (os.path.exists(have) and str(json.load(open(have, encoding="utf-8")).get("id") or "") == sid):
            shutil.rmtree(wd, ignore_errors=True); os.makedirs(wd, exist_ok=True); z = os.path.join(out, "_footage.zip"); PUB.drive_download(fid, z)
            with zipfile.ZipFile(z) as f:
                for n in f.namelist():
                    if not NAMES.match(n): continue
                    with f.open(n) as src, open(os.path.join(wd, n), "wb") as dst: shutil.copyfileobj(src, dst)
            os.remove(z)
        meta = json.load(open(have, encoding="utf-8"))
        if str(meta.get("id") or "") != sid:
            return {"none": "broken", "short": sid, "why": f"the archive on the ladder row of Short {sid} is the footage of {meta.get('id') or 'no Short'}"}
        man = manifest(meta, wd)
    except Exception as e:
        return {"none": "broken", "short": sid, "why": f"the footage of Short {sid} could not be read ({scrub(e)[:140]})"}
    man.update(short=sid, footage=fid)
    log(f"opening: the footage of Short {sid} is here - {len(man['clips'])} clips, {man['seconds']:.1f} s of picture; its hook: '{man['hook'][:80]}'")
    return man

def proven(man):
    """The Short's own first sentence as the long video's first line ({line, short}), or None (no footage, or OPENING_HOOK_ON is off)."""
    if not man or man.get("none") or not str(man.get("hook") or "").strip() or not S("OPENING_HOOK_ON", bool): return None
    return {"line": str(man["hook"]).strip(), "short": man["short"]}

# ------------------------------------------------------------------ the laying: the Short's picture track under the long video's first sentences (pure)
def bounds(units):
    """Where each unit's picture starts and the last one ends - the renderer's own rule (the first picture starts at 0.0)."""
    if not units: return [0.0]
    return [0.0] + [float(u.get("start") or 0) for u in units[1:]] + [float(units[-1].get("end") or units[-1].get("start") or 0)]

def lay(units, man):
    """{unit index: [[clip, from, to, slow], ...]}: which stretch of which clip each opening sentence shows. The track runs at the Short's own
    speed from second 0; a sentence may cross from one clip into the next; the opening ends with the last sentence that ENDS inside the footage
    (and inside OPENING_SHORT_MAX_S). from / to are seconds of the clip as made. Pure: same units and manifest, same answer."""
    if not units or not man or man.get("none") or not man.get("track"): return {}
    L = min(float(man.get("seconds") or 0), max(0.0, S("OPENING_SHORT_MAX_S", float))); b = bounds(units); out = {}
    for i in range(len(units)):
        a, e = b[i], b[i + 1]
        if e > L + 1e-6: break
        if e - a < 0.05: continue
        parts = []
        for t in man["track"]:
            x0, x1 = max(a, float(t["start"])), min(e, float(t["end"]))
            if x1 - x0 < MIN_PART_S: continue
            parts.append([t["clip"], round((x0 - float(t["start"])) / float(t["slow"]), 3), round((x1 - float(t["start"])) / float(t["slow"]), 3), float(t["slow"])])
        if not parts: break
        out[i] = parts
    return out

def mark(shots, units, man):
    """The shot list with the opening laid on it (a new list; pure). Every covered unit becomes an animated shot that carries its piece of the
    Short's track (`short` = {id, parts}); the first one carries the promise - it is the picture real viewers stayed for. Marks of an earlier
    pass are rebuilt from the rule, so marking twice changes nothing and a video whose footage is gone loses its marks."""
    out = [dict(s) for s in shots or []]; want = lay(units, man)
    for i, s in enumerate(out):
        if i in want:
            s.update(type="kling", hero=True, short={"id": man["short"], "parts": want[i]})
            for k in ("graphic", "search", "anim", "seat", "pov_fx", "impact"): s.pop(k, None)
            if not str(s.get("prompt") or "").strip(): s["prompt"] = str((units[i] if i < len(units) else {}).get("text") or "")
        elif s.get("short"):
            s.pop("short"); s["type"] = "still"; s.pop("promise", None)
    if want:
        for s in out: s.pop("promise", None)
        out[min(want)]["promise"] = True
    return out

def marked(shots): return [i for i, s in enumerate(shots or []) if isinstance(s, dict) and s.get("short")]

# ------------------------------------------------------------------ the window: how an upright clip is shown in a wide frame (pure)
def fit(w, h, W, H, mode=None, emax=None):
    """How a clip of w x h pixels is shown in a frame of W x H: {mode, shape, crop [w, h], show [w, h], enlarge, ground, kept}. A window as wide
    as the clip is cut out and shown at the frame's full height; its shape runs from the clip's own (the whole clip) to the frame's (filled).
    'whole' keeps the whole clip, 'fill' fills the frame whatever it costs, 'auto' takes the widest window that enlarges the paid picture at
    most `emax` times (OPENING_ENLARGE_MAX). ground = the window does not fill the frame: a blurred copy of the same picture lies under it.
    A clip that is already as wide as the frame only loses its sides."""
    mode = str(mode or S("OPENING_FIT") or "auto").strip().lower(); mode = mode if mode in MODES else "auto"
    emax = float(S("OPENING_ENLARGE_MAX", float) if emax is None else emax); F = W / H; a = w / h
    if a >= F:
        cw = min(w, int(round(h * F)) // 2 * 2)
        return {"mode": mode, "shape": round(F, 4), "crop": [cw, h], "show": [W, H], "enlarge": round(H / h, 3), "ground": False, "kept": round(cw / w, 3)}
    A = a if mode == "whole" else F if mode == "fill" else min(F, max(a, emax * w / H))
    ch = max(2, min(h, int(w / A + 1e-6) // 2 * 2))      # rounded DOWN to whole pixel pairs: a window meant to fill the frame never leaves a strip of ground
    dw = min(W, int(round(H * w / ch)) // 2 * 2)
    return {"mode": mode, "shape": round(w / ch, 4), "crop": [w, ch], "show": [dw, H], "enlarge": round(H / ch, 3), "ground": dw < W, "kept": round(ch / h, 3)}

def _show(k, c, f, W, H, fps):
    """The ffmpeg filters that show part k through its window (and lay the blurred ground under it), ending in the stream [v<k>]."""
    cw, ch = f["crop"]; dw = f["show"][0]; x = max(0, (c["w"] - cw) // 2 // 2 * 2)
    y = max(0, min(c["h"] - ch, int(round(c["h"] * min(1.0, max(0.0, S("OPENING_WINDOW_Y", float))) - ch / 2)) // 2 * 2))
    tail = f"setsar=1,fps={fps},format=yuv420p[v{k}]"
    if not f["ground"]: return f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,{tail}"
    return (f"split[g{k}][w{k}];[g{k}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur={max(2, W // 64)}:2,eq=brightness=-0.12:saturation=0.8[b{k}];"
            f"[w{k}]crop={cw}:{ch}:{x}:{y},scale={dw}:{H}:flags=lanczos[f{k}];[b{k}][f{k}]overlay={(W - dw) // 2}:0,{tail}")

def _frame(path, t):
    """The picture of a video file at second t (a BGR array), or None."""
    import cv2
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, float(t)) * 1000.0); ok, fr = cap.read()
    if not ok: cap.set(cv2.CAP_PROP_POS_FRAMES, 0); ok, fr = cap.read()
    cap.release(); return fr if ok else None

# ------------------------------------------------------------------ the files: one clip per opening sentence, cut from the footage (free)
def cut(shots, units, out, man, have=None):
    """Inside D6's assets run, BEFORE anything is paid: every marked shot gets its own clip `clip<i>.mp4` - its stretch of the Short's footage,
    slowed as the Short played it, shown through the window, exactly as long as its sentence, at the frame's size - and `img<i>.jpg`, its first
    frame. Returns {img, clips, opening} (opening = the record check opening_shown reads: the Short, the archive, per shot its parts and the
    hash of its clip). A clip restored from a checkpoint is kept when its hash and its parts are the recorded ones. RAISES when a marked shot
    cannot be cut: the assets stage must never buy another picture for it."""
    idx = marked(shots)
    if not idx: return {}
    if not man or man.get("none"): raise RuntimeError("the opening is laid on the Short's footage, but the footage is not here - nothing is paid; will retry")
    import cv2
    from whatifs import render as RN, release as REL
    W, H = RN.out_size(); fps = RN.fps(); b = bounds(units); wd = os.path.join(out, DIR)
    old = (have or {}).get("opening") or {}; old = (old.get("units") or {}) if old.get("short") == man.get("short") and old.get("footage") == man.get("footage") else {}
    rec = {"short": man["short"], "footage": man["footage"], "units": {}, "fit": None}; imgs, clips = {}, {}
    for i in idx:
        parts = shots[i]["short"].get("parts") or []; dur = b[i + 1] - b[i]; p = os.path.join(out, f"clip{i:03d}.mp4"); ip = os.path.join(out, f"img{i:03d}.jpg")
        o = old.get(str(i))
        if not (o and o.get("parts") == parts and os.path.exists(p) and os.path.exists(ip) and REL.sha(p) == o.get("sha")):
            inputs, filt = [], []
            for k, (name, t0, t1, slow) in enumerate(parts):
                c = (man.get("clips") or {}).get(name); src = os.path.join(wd, name)
                if not c: raise RuntimeError(f"opening shot {i} needs {name}, which is not in the footage of Short {man['short']} - nothing is paid; will retry")
                f = fit(c["w"], c["h"], W, H); rec["fit"] = rec["fit"] or dict(f, w=c["w"], h=c["h"])
                t0 = min(float(t0), max(0.0, float(c["sec"]) - 0.1)); inputs += ["-i", src]
                filt.append(f"[{k}:v]trim=start={t0:.3f}:end={max(float(t1), t0 + 0.05):.3f},setpts=(PTS-STARTPTS)*{float(slow):.4f}," + _show(k, c, f, W, H, fps))
            filt.append("".join(f"[v{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0,tpad=stop_mode=clone:stop_duration=2,trim=0:{dur:.3f},setpts=PTS-STARTPTS[vout]")
            try:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[vout]", "-an", "-r", str(fps), "-c:v", "libx264",
                                "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", p], check=True, timeout=600)
                fr = _frame(p, 0.0)
                if fr is None: raise RuntimeError("the cut clip has no frame")
                cv2.imwrite(ip, fr)
            except Exception as e:
                raise RuntimeError(f"opening shot {i} could not be cut from the footage of Short {man['short']} ({scrub(e)[:120]}) - nothing is paid; will retry")
            o = {"sha": REL.sha(p), "parts": parts, "sec": round(dur, 3)}
        else:
            c0 = (man.get("clips") or {}).get(parts[0][0]) if parts else None
            if c0 and not rec["fit"]: rec["fit"] = dict(fit(c0["w"], c0["h"], W, H), w=c0["w"], h=c0["h"])
        rec["units"][str(i)] = o; imgs[i] = ip; clips[i] = p
    f = rec["fit"] or {}
    log(f"opening: {len(idx)} shots ({b[idx[-1] + 1]:.1f} s) cut from the footage of Short {man['short']} - clips of {f.get('w')} x {f.get('h')}, window {f.get('mode')}: "
        f"{f.get('show', ['?'])[0]} of {W} pixels wide, enlarged {f.get('enlarge')} times, {'on a blurred ground' if f.get('ground') else 'the frame filled'}; nothing paid")
    return {"img": imgs, "clips": clips, "opening": rec}

# ------------------------------------------------------------------ the proof: on the shot list (before picture money) and on the finished film
def plan_report(d, shots, units, man):
    """(ok, why) for check opening_footage; ok None = the check does not apply (an override, switched off). A long video about a promoted Short
    must open on THAT Short's footage: its archive fetched and whole, the first shots carrying it and nothing else, laid as `lay` says."""
    kind, r = source(d)
    if kind != "short": return None, none_words(kind, r)
    sid = str(r["id"])
    if not man or man.get("none") or man.get("short") != sid:
        return False, str((man or {}).get("why") or f"the footage of Short {sid} was not fetched for this video") + ": the video would open with other pictures"
    if str(man.get("footage") or "") != str(r.get("footage") or ""): return False, f"the footage in this video's plan is not the archive on the ladder row of Short {sid}"
    want = lay(units, man); have = {i: shots[i].get("short") or {} for i in marked(shots)}; b = bounds(units)
    if 0 not in want: return False, f"the first sentence ends at {b[1] if len(b) > 1 else 0:.1f} s, after the footage of Short {sid} ({float(man.get('seconds') or 0):.1f} s): nothing can be laid"
    if not shots or not shots[0].get("short"): return False, f"the video opens on a {(shots[0].get('type') if shots else 'missing shot')}, not on the footage of its Short {sid}"
    alien = [i for i, m in have.items() if m.get("id") != sid]
    if alien: return False, f"opening shot {alien[0]} carries the footage of another Short ({have[alien[0]].get('id')})"
    still = [i for i in have if shots[i].get("type") != "kling"]
    if still: return False, f"opening shot {still[0]} carries the footage of Short {sid} but is planned as a {shots[still[0]].get('type')}: it would be made from another picture"
    if {i: m.get("parts") for i, m in have.items()} != want:
        return False, f"the opening is not laid as the rule says: shots {sorted(have)[:12]} carry footage, the rule lays it on {sorted(want)[:12]} (or other stretches of the clips)"
    last = max(want); names = sorted({p[0] for ps in want.values() for p in ps})
    return True, f"opens on {b[last + 1]:.1f} s of the footage of Short {sid}: {len(want)} shots from {len(names)} of its {len(man.get('clips') or {})} clips, laid by code"

def detail(img):
    """The DETAIL of the middle of a picture: a small grey copy minus its own blur. What a grade does to a picture - darker, tinted, a vignette -
    is in the blur and drops out; what the picture SHOWS stays."""
    import cv2, numpy as np
    h, w = img.shape[:2]; x0, x1, y0, y1 = REGION
    g = cv2.resize(cv2.cvtColor(img[int(h * y0):int(h * y1), int(w * x0):int(w * x1)], cv2.COLOR_BGR2GRAY), GRID, interpolation=cv2.INTER_AREA).astype(np.float32)
    return g - cv2.GaussianBlur(g, (0, 0), 6)

def alike(film, clip):
    """-1 .. 1: how alike a frame of the finished film and a frame of the footage are - the correlation of their detail (1 = the same picture,
    about 0 = another picture). None when the footage frame itself has no detail to recognise (fog, a plain wall): nothing can be said."""
    import numpy as np
    a, b = detail(film), detail(clip)
    if float(b.std()) < FLAT: return None
    a = a - a.mean(); b = b - b.mean(); den = float(np.sqrt(float((a * a).sum()) * float((b * b).sum())))
    return round(float((a * b).sum()) / den, 3) if den > 1e-6 else 0.0

def spots(parts, dur):
    """Where inside one opening shot (seconds from its start) the film is compared with its clip: inside every stretch of a clip of the Short,
    every EVERY_S seconds, at least EDGE_S away from the stretch's two ends - a change between two clips is never a place to compare (the film
    and the clip may be a frame apart there, and a frame apart at a cut is another picture). A stretch too short for that gives its middle
    when it is the only one. Pure."""
    out = []; at = 0.0
    for _name, t0, t1, slow in parts or []:
        ln = min((float(t1) - float(t0)) * float(slow), max(0.0, dur - at)); x = at + EDGE_S
        while x <= at + ln - EDGE_S + 1e-9: out.append(round(x, 3)); x += EVERY_S
        at += ln
    return out or [round(dur / 2, 3)]

def shown_report(d, shots, units, rec, master):
    """(ok, why) for check opening_shown, measured on the FINISHED film; ok None = the check does not apply. The clips of the opening shots must
    be the files cut from this Short's footage (their hashes are on record) and the film must SHOW them: all through every opening shot
    the frame of the master is compared with the frame of the clip (the correlation of their detail, `alike`) - at the moments `spots` names:
    every half second inside every stretch of a clip, never where two clips meet."""
    kind, r = source(d)
    if kind != "short": return None, none_words(kind, r)
    sid = str(r["id"]); idx = marked(shots)
    if not idx or idx[0] != 0:
        return False, f"the finished video does not open on the footage of its Short {sid}: its first shot is a {(shots[0].get('type') if shots else 'missing shot')} of its own"
    if not rec or rec.get("short") != sid: return False, f"nothing on record says that the opening was cut from the footage of Short {sid}"
    if not master or not os.path.exists(master): return False, "there is no finished film to compare with the footage"
    from whatifs import release as REL
    b = bounds(units); out = os.path.dirname(master); worst = (2.0, 0.0); n = 0
    for i in idx:
        u = (rec.get("units") or {}).get(str(i)); p = os.path.join(out, f"clip{i:03d}.mp4")
        if not u or not os.path.exists(p) or REL.sha(p) != u.get("sha"): return False, f"the clip of opening shot {i} is not the file that was cut from the footage of Short {sid}"
        if u.get("parts") != (shots[i].get("short") or {}).get("parts"): return False, f"the clip of opening shot {i} was cut from other stretches of the footage than its shot names"
        dur = b[i + 1] - b[i]
        for o in spots(u.get("parts"), dur):
            fm, fc = _frame(master, b[i] + o), _frame(p, o)
            if fm is None or fc is None: return False, f"no frame of the finished film could be read at {b[i] + o:.1f} s"
            same = alike(fm, fc)
            if same is None: continue
            n += 1; worst = min(worst, (same, round(b[i] + o, 1)))
    if n and worst[0] < SAME_MIN:
        return False, f"at {worst[1]:.1f} s the finished film does not show the footage of its Short {sid}: the two pictures are alike by {worst[0]:.2f} (at least {SAME_MIN:g})"
    f = rec.get("fit") or {}
    return True, (f"the first {b[idx[-1] + 1]:.1f} s are the footage of Short {sid}: {len(idx)} shots, {n} frames of the finished film compared with it, the least alike by {worst[0] if n else 1.0:.2f} "
                  f"(at least {SAME_MIN:g}); window {f.get('mode')}: {f.get('show', ['?'])[0]} pixels wide, enlarged {f.get('enlarge')} times"
                  + (", on a blurred ground" if f.get("ground") else ""))

def m_cut(files):
    """Measures of the opening inside D6's assets run (they join that run's takeaway)."""
    o = (files or {}).get("opening") or {}; f = o.get("fit") or {}
    return {"opening_shots": len(o.get("units") or {}), "opening_s": round(sum(float(u.get("sec") or 0) for u in (o.get("units") or {}).values()), 1), "opening_enlarge": f.get("enlarge") or 0}
