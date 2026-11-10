"""Animation director: places the animated (Kling) scenes of a long video at the retention cliffs and writes their motion prompts. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import base64, json, os, re
from whatifs.core import S, log, FAKE, env, cost, scrub

STYLE_LOCKS = {   # STYLE ONLY (materials, light, lens). Never hair, clothes, props or faces: those come from the canon (Characters.visual).
    "toybox_noir": ("Stylized 3D cartoon, premium stop-motion puppet look: felt and wool fabrics with visible fibers, soft clay skin with subtle "
                    "fingerprint texture, painted wood, aged brass. Big readable silhouettes. Cinematic noir lighting with one hard key light, deep "
                    "shadows, shallow depth of field, 35mm lens, subtle film grain. Original characters only, no text, no logos."),
    "photoreal":   ("Cinematic adult realism, natural human proportions, 35mm film still, moody motivated lighting, shallow depth of field, subtle "
                    "film grain. Original characters only, no text, no logos."),
    "illustrated": ("Graphic-novel illustration, bold ink lines and painted textures, dramatic noir lighting, rich colour, cinematic framing. "
                    "Original characters only, no text, no logos."),
}
STYLE_LOCK = STYLE_LOCKS["toybox_noir"]          # kept for older callers; style_lock() follows ART_STYLE

def style_lock(style=None):
    return STYLE_LOCKS.get(str(style or S("ART_STYLE") or "toybox_noir").strip().lower(), STYLE_LOCKS["toybox_noir"])

ART_STYLE_WORDS = {   # the short form added to EVERY ordinary still and thumbnail, so the whole video has ONE look (not just the 4 scenes)
    "toybox_noir": "stylized 3D stop-motion puppet diorama look: felt, clay, painted wood, aged brass",
    "photoreal":   "photographic realism, natural textures",
    "illustrated": "graphic-novel illustration, bold ink lines, painted textures",
}

def style_words(style=None):
    return ART_STYLE_WORDS.get(str(style or S("ART_STYLE") or "toybox_noir").strip().lower(), ART_STYLE_WORDS["toybox_noir"])

FACE_CAST = ("VALE", "GRIMM", "ROSA")            # the Archivist is never fully seen (canon)

def char_lock(who):
    """The character's look in the CANON's own words (Characters.visual + name) - nothing invented (setup-chat review, 9 Nov 2026)."""
    from whatifs import show as SHOW
    c = next((r for r in SHOW.characters() if r.get("id") == who), None)
    if not c: return ""
    return f"{c.get('name', who)}: {c.get('visual', '')}".strip().rstrip(":")

WORLDS = {
    "lab":    {"who": "GRIMM", "set": "a gothic stone laboratory at night: bubbling glass flasks glowing chemical green, candles, a tall arched window, a "
               "Tesla coil, a chalkboard, brass instruments", "light": "green chemical under-light on the face, amber candlelight, a lightning flash "
               "through the arched window", "camera": "slow push-in at a 12-degree Dutch angle", "event": "lightning flashes twice through the window"},
    "office": {"who": "VALE", "set": "a 1940s detective office at night: corkboard of polaroids joined by red string, rain on the window, rotary phone, "
               "desk lamp", "light": "magenta neon slicing through venetian blinds, a sodium-orange desk-lamp pool, rain-streak shadows",
               "camera": "slow lateral dolly", "event": "the neon sign outside flickers off and on"},
    "court":  {"who": "ROSA", "set": "a warm oak courtroom in late afternoon: curved bench, tall arched windows, nameplate HON. ROSA (blurred)",
               "light": "golden sunbeams with floating dust through tall windows", "camera": "locked-off symmetrical wide with a slight push-in",
               "event": "dust bursts and hangs in the sunbeam"},
    "case":   {"who": "", "set": "the scene of the case itself as a miniature diorama", "light": "one hard moonlit or lamplit key light",
               "camera": "slow push-in", "event": "the consequence of the case becomes visible"},
}
SPEAKER_WORLD = {"GRIMM": "lab", "VALE": "office", "ROSA": "court", "NANA": "court"}
ANCHORS = (0.0, 0.29, 0.57, 0.92)
ACTING = {
    "lab":    "{who} straightens his red pocket square, pauses with a wicked grin (anticipation), then throws a lever; his machine coughs a puff "
              "of violet smoke into his face; he blinks, undeterred",
    "office": "{who} pins a final photograph to the evidence board, glances at his worn evidence notebook, steps back and tilts his head; the "
              "red strings pull taut into one line",
    "court":  "{who} sets her floral teacup down without a sound, lifts the gavel slowly (anticipation) and strikes once; she stays perfectly deadpan",
    "case":   "the scene reacts to the case: {line}",
}
AVOID = "no morphing faces, no extra fingers, no text, no lip movement, no camera cuts, no realistic human skin, no glossy plastic look"

# ------------------------------------------------------------------ 1. slots
def pick_slots(shots, units, n=None):
    """Indexes of the shots nearest the retention anchors (unique, each a picture shot with a unit)."""
    n = n if n is not None else S("ANIM_SHOTS", int)
    if not shots or not units or n <= 0: return []
    times = [(i, float(units[i].get("start", units[i].get("t0", 0)) or 0)) for i, s in enumerate(shots) if i < len(units) and s.get("type") in ("still", "living", "kling")]
    if not times: return []
    end = max(t for _, t in times) or 1.0
    chosen = []
    for a in ANCHORS[:n]:
        target = a * end
        cand = sorted((abs(t - target), i) for i, t in times if i not in chosen)
        if cand: chosen.append(cand[0][1])
    return chosen

def world_for(shot, unit, k):
    sp = str((unit or {}).get("speaker") or shot.get("speaker") or "").upper()
    for key, w in SPEAKER_WORLD.items():
        if key in sp: return w
    return ("case", "lab", "office", "court")[k % 4]

def apply(shots, units, plan=None):
    """Turns the chosen shots into animated scenes (type 'kling' + an 'anim' record) and every other paid clip into a living still.
    Returns the chosen indexes."""
    if not S("ANIM_DIRECTOR_ON", bool): return []
    n = min(S("ANIM_SHOTS", int), int(plan.get("kling", S("ANIM_SHOTS", int)))) if plan is not None else None
    idx = pick_slots(shots, units, n)
    for i, s in enumerate(shots):                               # a Kling slot that moved becomes a plain still (no extra paid living clip)
        if s.get("type") == "kling" and i not in idx: s["type"] = "still"
    for k, i in enumerate(idx):
        u = units[i] if i < len(units) else {}
        w = world_for(shots[i], u, k)
        shots[i]["type"] = "kling"; shots[i]["anim"] = {"slot": k, "world": w, "line": str(u.get("text", ""))[:160]}
    if plan is not None: plan["kling"] = len(idx)
    log(f"animation director: {len(idx)} animated scenes at {[round(float(units[i].get('start', 0) or 0)) for i in idx if i < len(units)]} s")
    return idx

# ------------------------------------------------------------------ 2. start frames (Google image model + locked portraits)
def _refs(who_list, workdir, ep):
    from whatifs.specials import _portrait
    out = []
    for who in who_list:
        try: out.append(_portrait(who, workdir, ep))
        except Exception as e: log(f"no portrait for {who}: {scrub(e)[:80]}", "WARN", ep)
    return [p for p in out if p and os.path.exists(p)]

def frame_prompt(anim, aspect="16:9", style=None):
    w = WORLDS.get(anim.get("world"), WORLDS["case"]); who = w["who"]
    cast = char_lock(who)
    staged = (f"{cast}, acting in {w['set']}" if who else w["set"]) + (f". The case: {anim.get('line')}" if anim.get("line") else "")
    return f"{'Wide' if aspect == '16:9' else 'Vertical'} staged scene, {aspect}. {staged}. Lighting: {w['light']}. Keep every character identical to the reference images. {style_lock(style)}"

def gemini_image(prompt, refs, path, ep, aspect="16:9"):
    """One picture from Google's image model with reference images. Returns path or raises."""
    if FAKE:
        from PIL import Image
        Image.new("RGB", (1280, 720) if aspect == "16:9" else (720, 1280), (40, 30, 60)).save(path); return path
    import requests
    from whatifs.models import model
    mid = model("gem_image")
    if not mid: raise RuntimeError("no Google image model discovered")
    parts = [{"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(p, "rb").read()).decode()}} for p in refs[:4]] + [{"text": prompt}]
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{mid}:generateContent", headers={"x-goog-api-key": env("GEMINI_KEY")},
                      json={"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}, timeout=180)
    if r.status_code >= 300: raise RuntimeError(f"Google image {r.status_code}: {r.text[:160]}")
    for c in r.json().get("candidates", []):
        for p in (c.get("content") or {}).get("parts", []):
            d = (p.get("inline_data") or p.get("inlineData") or {}).get("data")
            if d:
                open(path, "wb").write(base64.b64decode(d)); cost("image_ref", "google", 1, S("PRICE_GEM_IMAGE_USD", float), ep); return path
    raise RuntimeError("Google image: no picture in the reply")

def start_frame(shot, path, ep, workdir, aspect="16:9"):
    """The staged, reference-locked start picture of an animated scene. Falls back to the normal still (same style lock)."""
    anim = shot.get("anim") or {}
    who = WORLDS.get(anim.get("world"), {}).get("who")
    prompt = frame_prompt(anim, aspect)
    try:
        refs = _refs([who] if who else [], workdir, ep)
        return gemini_image(prompt, refs, path, ep, aspect), "google+refs" if refs else "google"
    except Exception as e:
        log(f"reference start frame failed ({scrub(e)[:100]}): using the normal still with the style lock", "WARN", ep)
        from whatifs import media as M
        M.still(prompt, path, ep, seed=f"anim|{ep}|{anim.get('slot')}")
        return path, "fallback-still"

# ------------------------------------------------------------------ 3. acting prompt
def acting_prompt(shot):
    anim = shot.get("anim") or {}
    w = WORLDS.get(anim.get("world"), WORLDS["case"]); who = {"GRIMM": "Dr. Grimm", "VALE": "Inspector Vale", "ROSA": "Nana Rosa"}.get(w["who"], "")
    act = ACTING.get(anim.get("world"), ACTING["case"]).format(who=who, line=anim.get("line", "")[:120])
    return (f"Using the start frame: {act}. {w['event']}. Camera: {w['camera']}. Snappy cartoon timing with anticipation, a slight overshoot and "
            f"settle; hold the final pose for one second. Keep faces, costumes and props identical to the start frame. {AVOID}.")
