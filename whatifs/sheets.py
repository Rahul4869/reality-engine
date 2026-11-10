"""The one-time character sheets workflow: expression sheets and the courtroom set under a hard lifetime image cap. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, os, re
from whatifs.core import S, log, store, iso, WORK, env, set_setting

EXPRESSIONS = ["neutral", "smug", "outraged", "delighted", "sceptical", "shocked", "thinking", "defeated", "triumphant", "whispering", "laughing", "stern"]
LOOK = ("stylized 3D puppet look (Toybox Noir): felt and clay materials, one hard noir key light, same person as the reference image; "
        "no text, no letters or words on any prop, no logo, no chibi, no mascot, no child")      # v10.2 (#8): the owner-approved style; expressions use the LOCKED master as reference

def plan(characters=None):
    from whatifs import show as SHOW
    out = [{"character": "SET", "expression": "courtroom", "prompt": "an empty dramatic old courtroom at night, rain on tall windows, warm lamps, " + LOOK}]
    n = max(1, min(len(EXPRESSIONS), S("SHEET_EXPRESSIONS", int)))
    for c in (characters or SHOW.characters()):
        if c.get("speaker") == "WITNESS": continue                     # the Archivist is never fully seen
        for ex in EXPRESSIONS[:n]:
            out.append({"character": c["id"], "expression": ex, "prompt": f"portrait of {c.get('name')}, {c.get('visual')}, expression: {ex}, same person in every image, " + LOOK})
    for p in out: p["hash"] = hashlib.sha256(p["prompt"].encode()).hexdigest()[:16]
    return out

def masters_plan():
    """v10.2 (#8): the Toybox Noir MASTER portrait per core character, made from the owner's approved (LOCKED) neutral portrait as the reference image,
    so the identity carries over into the new style. Expressions are made only after a master is LOCKED (with the master as the reference)."""
    from whatifs import anim as ANIM, show as SHOW
    out = []
    for c in SHOW.characters():
        if c.get("speaker") == "WITNESS": continue
        lock = ANIM.char_lock(c["id"])                    # the canon (Characters.visual), never invented features
        p = (f"Character master portrait, waist-up, three-quarter view, neutral confident expression, plain dark studio background. "
             f"No text, no letters or words on any prop. Same person as the reference image, restyled. {lock}. {ANIM.style_lock()}")
        out.append({"character": c["id"], "expression": "master", "prompt": p, "hash": hashlib.sha256(p.encode()).hexdigest()[:16]})
    return out

def identity_score(ref, new, who):
    """Vision judge: is the new picture the same character as the reference (0-10)? None when unavailable."""
    try:
        import base64
        from whatifs.models import ask_vision
        imgs = [("image/png", base64.b64encode(open(x, "rb").read()).decode()) for x in (ref, new)]
        r = ask_vision("Compare the two images. Is the second the SAME character as the first (face shape, hair, age, costume), restyled? "
                       "JSON only: {\"score\": 0-10, \"why\": \"short\"}", f"Character: {who}", imgs, "SHEETS")
        return float((r or {}).get("score"))
    except Exception: return None

def masters(limit=None):
    """Make the missing master portraits (reference-based, inside the lifetime cap). Nothing is LOCKED by code: the owner approves."""
    from whatifs import anim as ANIM, publish as PUB, specials as SP
    st = store(); have = {r.get("hash"): r for r in st.rows("Character_Sheets")}; cap = S("CHARACTER_SHEET_IMAGE_CAP", int)
    made = 0; out_dir = os.path.join(WORK, "sheets"); os.makedirs(out_dir, exist_ok=True)
    for p in masters_plan():
        if p["hash"] in have and have[p["hash"]].get("file"): continue
        if used() >= cap or (limit and made >= limit): break
        ref = SP._portrait(p["character"], out_dir, "SHEETS")
        path = os.path.join(out_dir, f"{p['character']}_master_{p['hash']}.png")
        try:
            ANIM.gemini_image(p["prompt"], [ref] if ref else [], path, "SHEETS", aspect="3:4")
            sc = identity_score(ref, path, p["character"]) if ref else None
            fid = PUB.drive_upload(path, os.path.basename(path))[0]
            st.append("Character_Sheets", [{"ts": iso(), "character": p["character"], "expression": "master", "hash": p["hash"], "prompt": p["prompt"][:400],
                                            "file": "drive:" + fid, "status": f"DRAFT (identity {sc:.0f}/10)" if sc is not None else "DRAFT", "approved_at": ""}]); made += 1
        except Exception as e: log(f"master portrait {p['character']} failed: {str(e)[:120]}", "WARN")
    if made:
        try: PUB.email("New Toybox Noir character masters to approve", f"<p>{made} master portrait(s) in Drive (Character_Sheets tab, expression 'master'), made from your approved portraits. "
                       f"Approve to LOCK them; animated scenes then use them as the face reference. Lifetime images used: {used()} of {cap}.</p>")
        except Exception: pass
    return {"made": made, "have": used()}

def used():
    return sum(1 for r in store().rows("Character_Sheets") if r.get("file"))

def run(limit=None):
    """Make the missing sheet images inside the lifetime cap. Returns {made, skipped_cap, have}. Bounded: one attempt per image per run.
    v10.2 (#8): until every core character has a LOCKED master, only masters are made (no reference-less expressions ever again)."""
    from whatifs import show as SHOW
    locked = {r.get("character") for r in store().rows("Character_Sheets") if r.get("expression") == "master" and r.get("status") == "LOCKED"}
    if any(c["id"] not in locked for c in SHOW.characters() if c.get("speaker") != "WITNESS"): return dict(masters(limit), skipped_cap=0)
    from whatifs import media as M, publish as PUB
    st = store(); have = {r.get("hash"): r for r in st.rows("Character_Sheets")}; cap = S("CHARACTER_SHEET_IMAGE_CAP", int)
    made = skipped = 0; base = used(); out_dir = os.path.join(WORK, "sheets"); os.makedirs(out_dir, exist_ok=True)
    for p in plan():
        if p["hash"] in have and have[p["hash"]].get("file"): continue           # idempotent: never bought twice
        if base + made >= cap or (limit and made >= limit): skipped += 1; continue
        path = os.path.join(out_dir, f"{p['character']}_{p['expression']}_{p['hash']}.jpg")
        try:
            from whatifs import anim as ANIM, specials as SP
            ref = SP._portrait(p["character"], out_dir, "SHEETS") if p["character"] != "SET" else None
            ANIM.gemini_image(p["prompt"], [ref] if ref else [], path, "SHEETS", aspect="3:4")      # v10.2 (#8): the master is the face reference
            fid = PUB.drive_upload(path, os.path.basename(path))[0]
            st.append("Character_Sheets", [{"ts": iso(), "character": p["character"], "expression": p["expression"], "hash": p["hash"], "prompt": p["prompt"][:400],
                                            "file": "drive:" + fid, "status": "DRAFT", "approved_at": ""}]); made += 1
        except Exception as e:
            log(f"sheet image {p['character']}/{p['expression']} failed: {str(e)[:120]}", "WARN"); continue
    if made:
        try:
            from urllib.parse import quote
            repo = env("GH_REPO"); chars = sorted({p["character"] for p in plan()})
            links = "".join(f"<li>{c}: <a href='https://github.com/{repo}/issues/new?title={quote('APPROVE SHEET ' + c)}'>APPROVE</a></li>" for c in chars) if repo else ""
            PUB.email("Character sheets ready to review", f"<p>{made} new image(s) in Drive (Character_Sheets tab). Approving locks them; CHARACTER_THEATER_ON stays FALSE "
                      f"until you switch it on.</p><ul>{links}</ul><p>Lifetime images used: {used()} of {cap}.</p>")
        except Exception: pass
    return {"made": made, "skipped_cap": skipped, "have": used()}

def auto_lock(now=None):
    """v9.3.1 (L6, SHEETS_DEFAULT_LOCK_H): sheet images still in DRAFT this many hours after they were made are locked by default (silence = yes),
    so the characters do not stay off screen forever. 'REDO SHEET <ID> <expression>' still works afterwards (lifetime cap K102 unchanged).
    When every character has locked images, CHARACTER_THEATER_ON is switched on once (owner decision 2, 2026-11-07) and the owner is told how to undo it."""
    from whatifs.core import parse_iso, now_utc, set_setting
    h = S("SHEETS_DEFAULT_LOCK_H", float)
    if h <= 0: return 0
    st = store(); now = now or now_utc(); n = 0
    for r in st.rows("Character_Sheets"):
        t0 = parse_iso(r.get("ts"))
        if r.get("status") == "DRAFT" and r.get("file") and t0 and (now - t0).total_seconds() > h * 3600:
            st.update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "LOCKED", "approved_at": iso() + " (default)"}); n += 1
    rows = st.rows("Character_Sheets")
    chars = {r.get("character") for r in rows if r.get("character")}
    all_locked = bool(chars) and all(any(x.get("character") == c and x.get("status") == "LOCKED" for x in rows) for c in chars)
    if n and all_locked and not S("CHARACTER_THEATER_ON", bool) and not str(S("SHEETS_THEATER_AUTO_ON_AT") or "").strip():
        set_setting("CHARACTER_THEATER_ON", "TRUE"); set_setting("SHEETS_THEATER_AUTO_ON_AT", iso())
        try:
            from whatifs import publish as PUB
            PUB.email("Character sheets locked by default", f"<p>{n} sheet image(s) were locked after {int(h)} hours without a reply, and the characters now appear on screen "
                      "(CHARACTER_THEATER_ON = TRUE). To switch them off: Settings -> CHARACTER_THEATER_ON = FALSE (or the toggle in Mission Control once it is live). "
                      "To remake one image: REDO SHEET VALE smug.</p>")
        except Exception: pass
    if n: log(f"character sheets: {n} image(s) locked by default after {int(h)} h")
    return n

def decide(title):
    """'APPROVE SHEET <ID>' locks that character's images; 'REDO SHEET <ID> <expression>' clears ONE image so the next run remakes it (cap still counts)."""
    st = store(); t = str(title or "").strip()
    m = re.match(r"^APPROVE SHEET ([A-Z]+)$", t)
    if m:
        n = 0
        for r in st.rows("Character_Sheets"):
            if r.get("character") == m.group(1) and r.get("status") == "DRAFT":
                st.update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "LOCKED", "approved_at": iso()}); n += 1
        return f"{n} image(s) locked"
    m = re.match(r"^REDO SHEET ([A-Z]+) ([a-z]+)$", t)
    if m:
        for r in st.rows("Character_Sheets"):
            if r.get("character") == m.group(1) and r.get("expression") == m.group(2):
                st.update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "REDO", "hash": r["hash"] + "-redo-" + iso()[:16]})
                return "cleared; the next sheets run remakes it (lifetime cap still applies)"
        return "no such image"
    raise SystemExit("usage: 'APPROVE SHEET VALE' or 'REDO SHEET VALE smug'")

def locked_portraits():
    """{(character, expression): drive file} of LOCKED images (what the theatre layer may show)."""
    return {(r["character"], r["expression"]): r["file"] for r in store().rows("Character_Sheets") if r.get("status") == "LOCKED" and r.get("file")}

# ---------------------------------------------------------------- v10.2: the owner's look decision, shown with HIS characters
SAMPLE_STYLES = ("photoreal", "toybox_noir", "illustrated")
STYLE_LABEL = {"photoreal": "PHOTOREAL", "toybox_noir": "TOYBOX NOIR", "illustrated": "ILLUSTRATED"}

def style_samples():
    """The SAME staged scene per character (Vale in his office, Grimm in his lab, Rosa in her courtroom) in each ART_STYLE, made from the LOCKED
    portrait as the face reference: exactly how episodes would start their animated scenes. One comparison board (rows = characters; columns = the
    locked portrait + the 3 looks) goes to Drive, and a card asks the owner to tap a look. 9 Google images (about Rs 55); the lifetime sheet cap is
    not touched."""
    from whatifs import anim as ANIM, publish as PUB, specials as SP, notify as NT
    from whatifs.core import FAKE
    fx = S("USD_INR", float) or 92.0
    est = len(ANIM.FACE_CAST) * len(SAMPLE_STYLES) * S("PRICE_GEM_IMAGE_USD", float) * fx
    if est > S("STYLE_SAMPLES_CAP_INR", float): return {"ok": False, "why": f"estimated Rs {est:.0f} is above STYLE_SAMPLES_CAP_INR"}
    out_dir = os.path.join(WORK, "style_samples"); os.makedirs(out_dir, exist_ok=True)
    world = {"VALE": "office", "GRIMM": "lab", "ROSA": "court"}; grid = []
    for who in ANIM.FACE_CAST:
        ref = SP._portrait(who, out_dir, "STYLES")
        row = [ref]
        for st in SAMPLE_STYLES:
            p = os.path.join(out_dir, f"{who}_{st}.png")
            prompt = ANIM.frame_prompt({"world": world[who], "line": ""}, "16:9", style=st)
            try: ANIM.gemini_image(prompt, [ref] if ref else [], p, "STYLES", aspect="16:9"); row.append(p)
            except Exception as e: log(f"style sample {who}/{st} failed: {str(e)[:100]}", "WARN"); row.append(None)
        grid.append((who, row))
    board = _board(grid, os.path.join(out_dir, "style_board.jpg"))
    fid = PUB.drive_upload(board, "Reality_Engine_style_board.jpg")[0]
    link = f"https://drive.google.com/file/d/{fid}/view"
    NT.send("style_pick", f"Your cast in 3 looks (left: your locked portrait; then Photoreal, Toybox Noir, Illustrated): {link}  Tap the look for the show. "
            "It applies to every picture, the 4 animated scenes, the masters and the cast intro.",
            [("Photoreal", "STYLE photoreal"), ("Toybox Noir", "STYLE toybox_noir"), ("Illustrated", "STYLE illustrated")],
            tier="now", urgent=True, default="Toybox Noir stays", expires_h=96, dedupe_key="style_pick")
    try: PUB.email("Pick the look of your show (3 styles, your characters)", f"<p>The comparison board: <a href='{link}'>{link}</a></p><p>Reply on WhatsApp or the dashboard with your pick.</p>")
    except Exception: pass
    set_setting("STYLE_SAMPLES_REQUEST", "DONE " + iso())
    return {"ok": True, "board": board, "drive": fid}

def _board(grid, path):
    from PIL import Image, ImageDraw
    from whatifs.media import font
    cw, ch, head, lab = 480, 270, 54, 150
    W = lab + cw * 4; H = head + ch * len(grid)
    im = Image.new("RGB", (W, H), (14, 15, 20)); d = ImageDraw.Draw(im); f = font(26); fs = font(22, bold=False)
    for k, t in enumerate(["YOUR LOCKED PORTRAIT", "PHOTOREAL", "TOYBOX NOIR", "ILLUSTRATED"]):
        d.text((lab + k * cw + 14, 14), t, font=f, fill=(255, 214, 0))
    for r, (who, row) in enumerate(grid):
        y = head + r * ch; d.text((14, y + ch // 2 - 14), who, font=f, fill=(240, 240, 245))
        for k, p in enumerate(row):
            x = lab + k * cw
            if p and os.path.exists(p):
                c = Image.open(p).convert("RGB"); s = max(cw / c.width, ch / c.height)
                c = c.resize((int(c.width * s) + 1, int(c.height * s) + 1)); ox, oy = (c.width - cw) // 2, (c.height - ch) // 2
                im.paste(c.crop((ox, oy, ox + cw, oy + ch)), (x, y))
            else: d.text((x + 20, y + ch // 2), "not made", font=fs, fill=(200, 80, 80))
            d.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(40, 42, 50), width=2)
    im.save(path, "JPEG", quality=88); return path

def _answer(row, choice):
    p = str(choice).split()
    if len(p) == 2 and p[0].upper() == "STYLE" and p[1].lower() in SAMPLE_STYLES:
        set_setting("ART_STYLE", p[1].lower())
        return f"look set to {STYLE_LABEL[p[1].lower()]}: every picture, the animated scenes, the masters and the intro use it from now on"
    return "recorded"

def register():
    from whatifs import notify as NT
    NT.register("style_pick", on_answer=_answer)

