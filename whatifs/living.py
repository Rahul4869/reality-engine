"""Living characters: locked expression art in every reaction cutaway, with blink, breathing and mouth movement. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, re, random
import numpy as np
from whatifs.core import S, log, store, iso, FAKE, WORK, scrub

USED = []                     # this process's living shots (the final contract check reads it)
SPEAKER_CHAR = {"DIRECTOR": "VALE", "SKEPTIC": "GRIMM", "JUDGE": "ROSA", "WITNESS": "ARCHIVIST"}
MOOD = (("shocked", r"\b(what|no way|impossible|wait|!)"), ("smug", r"\b(obviously|of course|told you|prototype)\b"),
        ("sceptical", r"\b(really|sure|doubt|prove|objection)\b"), ("laughing", r"\b(ha|joke|funny)\b"), ("stern", r"\b(order|verdict|sentence|guilty)\b"))

def _sheet_rows(char):
    return [r for r in store().rows("Character_Sheets") if str(r.get("character", "")).upper() == char and r.get("status") == "LOCKED" and r.get("file")]

def _local(file_ref, char, expr):
    """A local path for a sheet file ('drive:<id>' is downloaded once into WORK/sheets)."""
    if not file_ref: return None
    if not str(file_ref).startswith("drive:"): return file_ref if os.path.exists(file_ref) else None
    p = os.path.join(WORK, "sheets", f"{char}_{expr}.png"); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        from whatifs import publish as PUB
        PUB.drive_download(str(file_ref)[6:], p)
    return p if os.path.exists(p) else None

def expression_for(speaker, line=""):
    """(path, expression) of the LOCKED still that fits the line's mood; neutral when nothing matches; (None, None) when no sheets are locked."""
    char = SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper()); rows = _sheet_rows(char)
    if not rows: return None, None
    by = {str(r.get("expression")): r for r in rows}
    want = next((e for e, rx in MOOD if re.search(rx, str(line), re.I) and e in by), None) or ("neutral" if "neutral" in by else next(iter(by)))
    return _local(by[want].get("file"), char, want), want

def variants(char, expr, base_path, ep):
    """(eyes_closed_path, mouth_open_path) for a locked still; made once, identity-checked, recorded in Character_Sheets as '<expr>+eyes' / '+mouth'."""
    if expr not in [x.strip() for x in str(S("LIVING_VARIANT_EXPRESSIONS")).split(",")]: return None, None
    out = []
    for kind, prompt in (("eyes", "Exactly the same image, same character, same pose, same lighting and framing - ONLY the eyes are fully closed (a blink)."),
                         ("mouth", "Exactly the same image, same character, same pose, same lighting and framing - ONLY the mouth is open mid-word.")):
        key = f"{expr}+{kind}"
        row = next((r for r in store().rows("Character_Sheets") if str(r.get("character", "")).upper() == char and r.get("expression") == key and r.get("file")), None)
        if row: out.append(_local(row.get("file"), char, key)); continue
        spent = sum(1 for r in store().rows("Character_Sheets") if "+" in str(r.get("expression", ""))) * S("PRICE_GEM_IMAGE_USD", float) * (S("USD_INR", float) or 92.0)
        if spent > S("LIVING_VARIANTS_CAP_INR", float): out.append(None); continue
        p = os.path.join(WORK, "sheets", f"{char}_{key}.png"); os.makedirs(os.path.dirname(p), exist_ok=True)
        try:
            if FAKE:
                import cv2
                b = cv2.imread(base_path); h, w = b.shape[:2]; v = b.copy()
                y0, y1 = (int(h * 0.38), int(h * 0.44)) if kind == "eyes" else (int(h * 0.58), int(h * 0.64))
                v[y0:y1, int(w * 0.4):int(w * 0.6)] = (v[y0:y1, int(w * 0.4):int(w * 0.6)] * 0.35).astype(np.uint8); cv2.imwrite(p, v)
            else:
                from whatifs import anim as ANIM, sheets as SH
                ANIM.gemini_image(prompt, [base_path], p, ep, aspect="16:9")
                sc = SH.identity_score(base_path, p, char)
                if sc is not None and sc < S("LIVING_MIN_IDENTITY", float): log(f"living: {key} for {char} rejected (identity {sc})", "WARN", ep); out.append(None); continue
            fid = ""
            if not FAKE:
                from whatifs import publish as PUB
                fid = "drive:" + PUB.drive_upload(p, f"sheet_{char}_{key}.png", public=False)[0]
            store().append("Character_Sheets", [{"ts": iso(), "character": char, "expression": key, "hash": f"{char}{key}", "prompt": prompt[:200],
                                                 "file": fid or p, "status": "AUTO", "approved_at": ""}])
            out.append(p)
        except Exception as e:
            log(f"living variant {key} for {char} skipped: {scrub(e)[:120]}", "WARN", ep); out.append(None)
    return tuple(out)

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

def speaking(words, t0, fps, nframes):
    """Frames during which the character is mid-word (word timings from the narration timeline, relative to this shot's start t0)."""
    out = set()
    for w in words or []:
        a, b = int((float(w["s"]) - t0) * fps), int((float(w["e"]) - t0) * fps)
        for f in range(max(0, a), min(nframes, b)):
            if (f - a) % 4 < 2: out.add(f)                                     # open-close at ~7 Hz during a word (viseme-lite)
    return out

def render(speaker, line, words, t0, path, nframes, ep, seed=""):
    """Render a living reaction / character shot. Returns a dict (used, blinks, mouth frames) or None when no LOCKED sheet exists (caller falls back)."""
    import cv2
    from whatifs import render as RN
    base_path, expr = expression_for(speaker, line)
    if not base_path: return None
    char = SPEAKER_CHAR.get(str(speaker).upper(), str(speaker).upper())
    W, H = RN.work_size(); fps = RN.fps()
    base = cv2.resize(cv2.imread(base_path), (W, H))
    ev, mv = variants(char, expr, base_path, ep)
    me = change_mask(base, cv2.imread(ev)) if ev else None; mm = change_mask(base, cv2.imread(mv)) if mv else None
    blinks = blink_frames(nframes, fps, f"{seed}{char}") if me else set(); mouth = speaking(words, t0, fps, nframes) if mm else set()
    parts = RN.Particles("court" if char == "ROSA" else "lab" if char == "GRIMM" else "office" if char == "VALE" else "case", base, seed, W, H, nframes, fps) if S("PARTICLES_ON", bool) else None
    def frames():
        for k in range(nframes):
            fr = base.astype(np.float32)
            if k in blinks: fr = fr * (1 - me[0]) + me[1].astype(np.float32) * me[0]
            if k in mouth: fr = fr * (1 - mm[0]) + mm[1].astype(np.float32) * mm[0]
            s = 1.0 + 0.006 * np.sin(2 * np.pi * 0.22 * k / fps) + 0.012 * k / max(1, nframes)      # breathing + a slow push-in
            M = cv2.getRotationMatrix2D((W / 2, H * 0.55), 0, s)
            out = cv2.warpAffine(fr.clip(0, 255).astype(np.uint8), M, (W, H), borderMode=cv2.BORDER_REFLECT)
            if parts is not None: out = parts.apply(out, k)
            yield out
    RN._pipe(path, frames(), nframes, W, H)
    USED.append({"character": char, "expression": expr, "blinks": len(blinks), "mouth_frames": len(mouth)})
    return {"character": char, "expression": expr, "blinks": len(blinks), "mouth_frames": len(mouth), "variants": [bool(ev), bool(mv)]}
