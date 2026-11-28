"""Living characters: locked expression art in every reaction cutaway, with blink, breathing and mouth movement. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, re, random, math, hashlib
import numpy as np
from whatifs.core import S, log, store, iso, FAKE, WORK, scrub

USED = []                     # this process's living shots (the final contract check reads it)
_SAID = set()                 # v12 DRAWN-b: (character, variant) already said once to be of another shape than its art
SPEAKER_CHAR = {"DIRECTOR": "VALE", "SKEPTIC": "GRIMM", "JUDGE": "ROSA", "WITNESS": "ARCHIVIST"}
MOOD = (("shocked", r"\b(what|no way|impossible|wait|!)"), ("smug", r"\b(obviously|of course|told you|prototype)\b"),
        ("sceptical", r"\b(really|sure|doubt|prove|objection)\b"), ("laughing", r"\b(ha|joke|funny)\b"), ("stern", r"\b(order|verdict|sentence|guilty)\b"))
SHORT_SAFE = (0.10, 0.62, 0.04, 0.84)   # v12 DRAWN-b (3.1): an upright frame's band for a face - top, bottom, left, right as shares (above the lowest 38% the buttons and title cover, left of the right rail)
HEAD = 0.45                             # the top share of a waist-up portrait that holds the head (sheets.masters_plan: "waist-up")
GROUND = 0.55                           # how bright the blurred copy around the art stays
SHAPES = {"3:4": 0.75, "4:3": 4 / 3, "1:1": 1.0, "16:9": 16 / 9, "9:16": 9 / 16}

def _sheet_rows(char):
    his = S("LIVING_HIS_LOCK_ONLY", bool)      # v12 DRAWN-b (3.3, P20): a lock by default after 72 h never turns the talking cast on - only his own lock does
    return [r for r in store().rows("Character_Sheets") if str(r.get("character", "")).upper() == char and r.get("status") == "LOCKED" and r.get("file")
            and not (his and str(r.get("approved_at") or "").rstrip().endswith("(default)"))]

def _local(file_ref, char, expr):
    """A local path for a sheet file ('drive:<id>' is downloaded once into WORK/sheets)."""
    if not file_ref: return None
    if not str(file_ref).startswith("drive:"): return file_ref if os.path.exists(file_ref) else None
    p = os.path.join(WORK, "sheets", f"{char}_{expr}.png"); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        from whatifs import publish as PUB
        PUB.drive_download(str(file_ref)[6:], p)
    return p if os.path.exists(p) else None

def has_art(speaker):
    """Is there APPROVED art of this speaker's character (a LOCKED sheet with a file)? v12 V2d-b: a character is drawn or absent - without it no
    cutaway of the character is planned and nothing is ever drawn in its place."""
    try: return bool(S("LIVING_CHARACTERS_ON", bool) and _sheet_rows(SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper())))
    except Exception: return False

def expression_for(speaker, line=""):
    """(path, expression) of the LOCKED still that fits the line's mood; neutral when nothing matches; (None, None) when no sheets are locked."""
    char = SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper()); rows = _sheet_rows(char)
    if not rows: return None, None
    by = {str(r.get("expression")): r for r in rows}
    want = next((e for e, rx in MOOD if re.search(rx, str(line), re.I) and e in by), None) or ("neutral" if "neutral" in by else next(iter(by)))
    return _local(by[want].get("file"), char, want), want

def shape_word(w, h):
    """The aspect word of the image model nearest to w / h (the art's own shape)."""
    r = w / max(1, h); return min(SHAPES, key=lambda k: abs(math.log(SHAPES[k] / r)))

def frame_of(art, W, H):
    """The approved art at its OWN shape inside a W x H frame - never stretched, never cut: landscape fills the height, centred; upright fills the
    width with its top at SHORT_SAFE[0] of the height; around it the art's own copy, enlarged to cover, blurred and darkened to GROUND.
    box = (x0, y0, x1, y1) of the art."""
    import cv2
    ah, aw = art.shape[:2]; s = min(W / aw, H / ah); w, h = max(1, round(aw * s)), max(1, round(ah * s))
    x0 = (W - w) // 2; y0 = (H - h) // 2 if W >= H else min(int(SHORT_SAFE[0] * H), H - h)
    k = max(W / aw, H / ah); cw, ch = max(W, math.ceil(aw * k)), max(H, math.ceil(ah * k))
    g = cv2.resize(art, (cw, ch))[(ch - H) // 2:(ch - H) // 2 + H, (cw - W) // 2:(cw - W) // 2 + W]
    out = (cv2.GaussianBlur(g, (0, 0), max(2.0, W / 64.0)).astype(np.float32) * GROUND).astype(np.uint8); out[y0:y0 + h, x0:x0 + w] = cv2.resize(art, (w, h))
    return out, (x0, y0, x0 + w, y0 + h)

def cap_room():
    """v12 DRAWN-b (C11): how many more blink / mouth pictures the variants' lifetime cap (LIVING_VARIANTS_CAP_INR) lets be asked. Every row whose
    expression holds '+' counts at the picture's price - made, REJECTED or TRIED alike; the judge of each is the estimate's line living_identity,
    not in this sum. A free picture divides nothing (999: the film's count and the missing slots still bound it)."""
    price = S("PRICE_GEM_IMAGE_USD", float) * (S("USD_INR", float) or 92.0)
    if price <= 0: return 999
    spent = sum(1 for r in store().rows("Character_Sheets") if "+" in str(r.get("expression", ""))) * price
    cap = S("LIVING_VARIANTS_CAP_INR", float)
    return 0 if spent > cap else int((cap - spent) // price) + 1

def _asked(char, key, prompt, status, ep, n):
    """v12 DRAWN-b (C11): a picture asked and not made is a row of its own with no file - REJECTED by the judge or TRIED (a call raised); its hash is
    its own, so no reader takes it for the made row. A store error only logs: the film's count already holds the attempt."""
    try: store().append("Character_Sheets", [{"ts": iso(), "character": char, "expression": key, "hash": f"{char}{key}-{status.lower()}-{ep}-{n}", "prompt": prompt[:200],
                                              "file": "", "status": status, "approved_at": ""}])
    except Exception as e: log(f"living: the {status} row of {key} for {char} was not written ({scrub(e)[:80]})", "WARN", ep)

def variants(char, expr, base_path, ep):
    """(eyes_closed_path, mouth_open_path) for a locked still; made once, identity-checked, recorded in Character_Sheets as '<expr>+eyes' / '+mouth'.
    v12 DRAWN-b (C11): 2. one film asks at most LIVING_VARIANT_TRIES pictures - its count (variant_tries.txt in the film's work folder) is written
    BEFORE the picture call, so a failed call is counted; a count that is there but cannot be read asks nothing more for this film. 3. every
    picture asked on the paid road ends as a row: made (AUTO, its file), below LIVING_MIN_IDENTITY (REJECTED, no file), the picture, the judge or
    the upload raising, or a face the judge could not score (TRIED, no file; RULINGS_U2k 1); offline no picture is asked and no such row is written, the count is kept on both roads. 4. the lifetime
    cap counts every such row (cap_room). 5. a slot is looked up as a row WITH a file: a REJECTED or TRIED slot may be asked again in a LATER
    film, never past the film's count or the cap."""
    if expr not in [x.strip() for x in str(S("LIVING_VARIANT_EXPRESSIONS")).split(",")]: return None, None
    out = []; tf = os.path.join(WORK, str(ep), "variant_tries.txt")
    for kind, prompt in (("eyes", "Exactly the same image, same character, same pose, same lighting and framing - ONLY the eyes are fully closed (a blink)."),
                         ("mouth", "Exactly the same image, same character, same pose, same lighting and framing - ONLY the mouth is open mid-word.")):
        key = f"{expr}+{kind}"
        row = next((r for r in store().rows("Character_Sheets") if str(r.get("character", "")).upper() == char and r.get("expression") == key and r.get("file")), None)
        if row: out.append(_local(row.get("file"), char, key)); continue
        if cap_room() <= 0: out.append(None); continue
        try: tries = int(open(tf).read().strip())
        except FileNotFoundError: tries = 0
        except Exception: log(f"living: this film's count of blink / mouth pictures cannot be read - nothing more is asked for this film", "WARN", ep); out.append(None); continue
        if tries >= S("LIVING_VARIANT_TRIES", int): out.append(None); continue
        p = os.path.join(WORK, "sheets", f"{char}_{key}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); os.makedirs(os.path.dirname(tf), exist_ok=True)
        try:
            if FAKE:
                import cv2
                with open(tf, "w") as f: f.write(str(tries + 1))
                b = cv2.imread(base_path); h, w = b.shape[:2]; v = b.copy()
                y0, y1 = (int(h * 0.38), int(h * 0.44)) if kind == "eyes" else (int(h * 0.58), int(h * 0.64))
                v[y0:y1, int(w * 0.4):int(w * 0.6)] = (v[y0:y1, int(w * 0.4):int(w * 0.6)] * 0.35).astype(np.uint8); cv2.imwrite(p, v)
            else:
                import cv2
                from whatifs import anim as ANIM, sheets as SH
                with open(tf, "w") as f: f.write(str(tries + 1))
                ANIM.gemini_image(prompt, [base_path], p, ep, aspect=shape_word(*cv2.imread(base_path).shape[1::-1]))      # v12 DRAWN-b (3.1): at the art's own shape
                sc = SH.identity_score(base_path, p, char, episode=ep)
                if sc is None or sc < S("LIVING_MIN_IDENTITY", float):          # RULINGS_U2k 1: a face that could not be judged is never filed (as restyle refuses it)
                    log(f"living: {key} for {char} " + ("not filed: its identity could not be judged" if sc is None else f"rejected (identity {sc})"), "WARN", ep)
                    out.append(None); _asked(char, key, prompt, "TRIED" if sc is None else "REJECTED", ep, tries + 1); continue
            fid = ""
            if not FAKE:
                from whatifs import publish as PUB
                fid = "drive:" + PUB.drive_upload(p, f"sheet_{char}_{key}.png", public=False)[0]
            store().append("Character_Sheets", [{"ts": iso(), "character": char, "expression": key, "hash": f"{char}{key}", "prompt": prompt[:200],
                                                 "file": fid or p, "status": "AUTO", "approved_at": ""}])
            out.append(p)
        except Exception as e:
            log(f"living variant {key} for {char} skipped: {scrub(e)[:120]}", "WARN", ep); out.append(None)
            if not FAKE: _asked(char, key, prompt, "TRIED", ep, tries + 1)
    return tuple(out)

def variant_room():
    """v12 DRAWN-b (C12): the blink / mouth pictures ONE film can still buy - the estimate's lines living_variants and living_identity. 0 unless the
    talking cast is on and LIVING_VARIANT_EXPRESSIONS names an expression; else the missing slots (every character's approved expressions - his own
    lock only, while LIVING_HIS_LOCK_ONLY - that get variants, eyes and mouth, with no row WITH a file), bounded by the film's count and the cap."""
    if not S("LIVING_CHARACTERS_ON", bool): return 0
    want = {x.strip() for x in str(S("LIVING_VARIANT_EXPRESSIONS")).split(",") if x.strip()}
    if not want: return 0
    rows = store().rows("Character_Sheets"); missing_ = 0
    for char in sorted({str(r.get("character", "")).upper() for r in rows if str(r.get("character", "")).strip()}):
        made = {str(r.get("expression")) for r in rows if str(r.get("character", "")).upper() == char and r.get("file")}
        for e in sorted({str(r.get("expression")) for r in _sheet_rows(char)} & want):
            missing_ += sum(1 for kind in ("eyes", "mouth") if f"{e}+{kind}" not in made)
    return max(0, min(S("LIVING_VARIANT_TRIES", int), missing_, cap_room()))

def change_mask(base, var):
    """Soft mask of where the variant really differs from the base (eyes / mouth only); zeros when it differs everywhere (a bad variant)."""
    import cv2
    if var is None: return None
    v = cv2.resize(var, (base.shape[1], base.shape[0]))
    d = cv2.cvtColor(cv2.absdiff(base, v), cv2.COLOR_BGR2GRAY)
    m = (d > 22).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), 6).astype(np.float32) / 255.0
    if m.mean() > S("LIVING_MAX_CHANGE_SHARE", float): return None             # the variant changed the whole picture: never used (would flicker)
    return m[..., None], v

def blink_frames(nframes, fps, seed):
    r = random.Random(str(seed)); out = set(); t = r.uniform(0.6, 2.0)
    while t * fps < nframes:
        f0 = int(t * fps); out.update(range(f0, min(nframes, f0 + 3))); t += r.uniform(2.0, 6.0)
    return out

def envelope(wav, t0, fps, nframes):
    """The narration's loudness in each video frame of a cutaway that starts at film second t0 - the RMS of the WAV's samples in that frame's
    1/fps seconds; [] when the file cannot be read."""
    try:
        import wave
        with wave.open(str(wav), "rb") as f:
            sr, ch, sw = f.getframerate(), f.getnchannels(), f.getsampwidth()
            if sw not in (1, 2, 4): return []
            f.setpos(max(0, min(f.getnframes(), int(round(float(t0) * sr))))); raw = f.readframes(int(math.ceil(nframes * sr / fps)) + 1)
        a = np.frombuffer(raw, dtype={1: np.uint8, 2: np.int16, 4: np.int32}[sw]).astype(np.float64)
        if sw == 1: a = a - 128.0
        if ch > 1: a = a[:len(a) // ch * ch].reshape(-1, ch).mean(axis=1)
        out = []
        for k in range(int(nframes)):
            seg = a[int(k * sr / fps):int((k + 1) * sr / fps)]
            out.append(float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0)
        return out
    except Exception: return []

def voice_median(words, t0, fps, nframes, env):
    """v12 DRAWN-b (CR-DRAWN-b 2): the words' median loudness the voice rule opens on - 0.0 when the rule cannot act (no envelope, a short one, a
    silent stretch or one past the WAV's end, LIVING_MOUTH_OPEN_K 0, no frame inside a word). `speaking` and the record both read it: the record
    says the rule the mouth really followed."""
    inside = sorted({f for w in words or [] for f in range(max(0, int((float(w["s"]) - t0) * fps)), min(nframes, int((float(w["e"]) - t0) * fps)))}); K = S("LIVING_MOUTH_OPEN_K", float)
    m = float(np.median([env[f] for f in inside])) if (env and len(env) >= nframes and K > 0 and inside) else 0.0
    return m

def speaking(words, t0, fps, nframes, env=None):
    """Frames during which the character's mouth is open (word timings from the narration timeline, relative to this shot's start t0). v12 DRAWN-b
    (3.2): with the narration's loudness `env` (one value a frame, `envelope`) it opens on the loud frames inside a word - its syllables - and closes
    in its pauses, with no one-frame flicker; without it, or with LIVING_MOUTH_OPEN_K 0, the older ~7 Hz flap. Never open outside a word."""
    spans = []
    for w in words or []:
        a, b = int((float(w["s"]) - t0) * fps), int((float(w["e"]) - t0) * fps)
        spans.append((a, range(max(0, a), min(nframes, b))))
    inside = sorted({f for _a, r in spans for f in r}); K = S("LIVING_MOUTH_OPEN_K", float)
    m = voice_median(words, t0, fps, nframes, env)                             # CR-DRAWN-b 2: the ONE helper the record reads too
    if m > 0:                                                                  # THE VOICE RULE: open on a frame at least K x the words' median loudness
        st = {f: env[f] >= K * m for f in inside}
        for f in inside:                                                       # a frame whose two neighbours agree and differ from it takes their state
            if f - 1 in st and f + 1 in st and st[f - 1] == st[f + 1] != st[f]: st[f] = st[f - 1]
        return {f for f in st if st[f]}
    out = set()
    for a, r in spans:
        for f in r:
            if (f - a) % 4 < 2: out.add(f)                                     # open-close at ~7 Hz during a word (viseme-lite)
    return out

def render(speaker, line, words, t0, path, nframes, ep, seed="", size=None, wav=None, record=True):
    """Render a living reaction / character shot. Returns a dict (used, blinks, mouth frames) or None when no LOCKED sheet exists (caller falls back).
    v12 DRAWN-b (3.1, 3.2, 3.4): the art is composed at its OWN shape (`frame_of`) in a frame of `size` (W, H) - the work size when None, wide or
    upright; the mouth follows the narration `wav`'s loudness inside the words; `record` False leaves USED untouched."""
    import cv2
    from whatifs import render as RN
    base_path, expr = expression_for(speaker, line)
    if not base_path: return None
    char = SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper())
    W, H = size or RN.work_size(); fps = RN.fps()
    art = cv2.imread(base_path); base, box = frame_of(art, W, H)                 # v12 DRAWN-b (3.1): whole, at its own shape, never stretched
    ev, mv = variants(char, expr, base_path, ep)
    def framed(p, key):                                                         # a variant is composed the same way before its mask is taken
        im = cv2.imread(p) if p else None
        if im is None: return None
        if shape_word(*im.shape[1::-1]) != shape_word(*art.shape[1::-1]) and (char, key) not in _SAID:
            _SAID.add((char, key)); log(f"living: {key} for {char} is not the art's shape - REDO SHEET makes it again", "WARN", ep)
        return frame_of(im, W, H)[0]
    me = change_mask(base, framed(ev, f"{expr}+eyes")) if ev else None; mm = change_mask(base, framed(mv, f"{expr}+mouth")) if mv else None
    env = envelope(wav, t0, fps, nframes) if (wav and S("LIVING_MOUTH_OPEN_K", float) > 0) else None      # v12 DRAWN-b (3.2): the mouth on the voice
    blinks = blink_frames(nframes, fps, f"{seed}{char}") if me else set(); mouth = speaking(words, t0, fps, nframes, env=env) if mm else set()
    cx, cy = (box[0] + box[2]) / 2, box[1] + 0.55 * (box[3] - box[1])          # the breathing push-in turns about the art (full-frame art: today's centre)
    parts = RN.Particles("court" if char == "ROSA" else "lab" if char == "GRIMM" else "office" if char == "VALE" else "case", base, seed, W, H, nframes, fps) if S("PARTICLES_ON", bool) else None
    def frames():
        for k in range(nframes):
            fr = base.astype(np.float32)
            if k in blinks: fr = fr * (1 - me[0]) + me[1].astype(np.float32) * me[0]
            if k in mouth: fr = fr * (1 - mm[0]) + mm[1].astype(np.float32) * mm[0]
            s = 1.0 + 0.006 * np.sin(2 * np.pi * 0.22 * k / fps) + 0.012 * k / max(1, nframes)      # breathing + a slow push-in
            M = cv2.getRotationMatrix2D((cx, cy), 0, s)
            out = cv2.warpAffine(fr.clip(0, 255).astype(np.uint8), M, (W, H), borderMode=cv2.BORDER_REFLECT)
            if parts is not None: out = parts.apply(out, k)
            yield out
    RN._pipe(path, frames(), nframes, W, H)
    shape_err = round(abs(((box[2] - box[0]) / max(1, box[3] - box[1])) / (art.shape[1] / art.shape[0]) - 1), 4)
    rec = {"character": char, "expression": expr, "blinks": len(blinks), "mouth_frames": len(mouth), "shape_err": shape_err, "size": [W, H],
           "mouth_rule": "voice" if voice_median(words, t0, fps, nframes, env) > 0 else "flap", "restyled": False}
    if not mm: rec["mouth_rule"] = "none"                                       # CODEREVIEW_DRAWN-b_2 1: no mouth picture (line 228's condition) - the mouth never moved, the record names no rule
    if record: USED.append(dict(rec))
    return dict(rec, variants=[bool(ev), bool(mv)])


# ------------------------------------------------------------------ v12 DRAWN-b (3.5, F-11, F-12, C6, C7, C9): the restyle trial arm - built and off
RESTYLE_PROMPT = ("The same puppet character, the same face, costume, pose, framing and light; {look}; natural small motion of the face; keep the "
                  "timing of every blink and every mouth movement exactly; no text, no new object, no other character.")

def restyle_arm(ep, i, k):
    """Is this reaction cutaway piece in the restyle arm? False whenever clips.restyle() is None (his switch, the share, a buyable row, the line);
    else the piece's own hash against RESTYLE_SHARE_PCT."""
    from whatifs import clips as CL
    if CL.restyle() is None: return False
    return int(hashlib.sha256(f"{ep}:restyle:{i}:{k}".encode()).hexdigest(), 16) % 100 < S("RESTYLE_SHARE_PCT", int)

def restyle(src, speaker, ep, i, k, seconds):
    """One restyled copy of a code-made cutaway piece, bought at most ONCE a video (its file rst<i>_<k>.mp4 beside the film is used again on a resume
    or a re-render) and used only when the character in its middle frame is still the approved art's (sheets.identity_score at least
    LIVING_MIN_IDENTITY; no score = not used). F-11: the seconds one film restyles never pass RESTYLE_EST_S - rst_booked.txt beside the film, written
    BEFORE the call (a failed buy is booked too); a booked file that cannot be read closes the cap. F-12: the score is kept in the piece's .id file
    and read on a later render - one judgement a piece. True = the restyled copy may be played."""
    import cv2
    from whatifs import media as MD, sheets as SH, anim as ANIM
    char = SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper())
    keep = os.path.join(os.path.dirname(src), f"rst{i:03d}_{k}.mp4")
    if not os.path.exists(keep):
        n = math.ceil(float(seconds) - 1e-6); bk = os.path.join(os.path.dirname(src), "rst_booked.txt")
        try: booked = int(open(bk).read().strip())
        except FileNotFoundError: booked = 0
        except Exception: log(f"restyled cutaway {i}.{k}: the booked seconds cannot be read - nothing more is restyled for this film, the code-made one stays", "WARN", ep); return False
        if booked + n > S("RESTYLE_EST_S", float):
            log(f"restyled cutaway {i}.{k}: {booked} + {n} s would pass RESTYLE_EST_S - the code-made one stays", "WARN", ep); return False
        with open(bk, "w") as f: f.write(str(booked + n))
        MD.restyle(src, RESTYLE_PROMPT.format(look=ANIM.style_lock()), keep, ep, seconds)
    idf = keep + ".id"; sc = None
    if os.path.exists(idf):
        try: sc = float(open(idf).read().strip())
        except Exception: sc = None
    else:
        mid = keep + ".mid.png"; cap = cv2.VideoCapture(keep); cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) // 2)
        ok, fr = cap.read(); cap.release(); ok = bool(ok) and fr is not None and bool(cv2.imwrite(mid, fr))
        base_path, _e = expression_for(speaker, "")
        sc = SH.identity_score(base_path, mid, char, episode=ep) if (base_path and ok) else None
        if sc is not None:
            with open(idf, "w") as f: f.write(str(float(sc)))
    if sc is None or sc < S("LIVING_MIN_IDENTITY", float): log(f"restyled cutaway {i}.{k}: identity {sc} - the code-made one stays", "WARN", ep); return False
    return True
