"""The one-time character sheets workflow: expression sheets and the courtroom set under a hard lifetime image cap. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, os, re
from whatifs.core import S, log, store, iso, WORK, env, set_setting
from whatifs import notify as NT

def _review_card():
    """v12 B-OWNER (rows 34 and 35 of PART 2's table): what the sheets' review card does at his silence - `auto_lock` locks them after
    SHEETS_DEFAULT_LOCK_H hours; when that cell is 0 they stay drafts (the card still closes after 72 hours)."""
    h = S("SHEETS_DEFAULT_LOCK_H", float)
    return ("they lock by themselves", h) if h > 0 else ("they stay drafts", 72.0)

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
        q = (f"Character master portrait, waist-up, three-quarter view, neutral confident expression, plain dark studio background. "      # v12 F318: the second try of a refused master - no canon text, the face from the reference
             f"No text, no letters or words on any prop. Take the face, hair, age and costume from the reference image exactly; change only the rendering style. {ANIM.style_lock()}")
        out.append({"character": c["id"], "expression": "master", "prompt": p, "retry": q, "hash": hashlib.sha256(p.encode()).hexdigest()[:16]})
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

def master_score(ref, new, who):
    """v12 F318: the master's identity score - the judge looks both ways (his portrait first, then the new picture first) and the LOWER answer counts; one answer when only one came; None when none came (no floor is judged on no evidence)."""
    looks = [s for s in (identity_score(ref, new, who), identity_score(new, ref, who)) if s is not None]
    log(f"master {who}: identity looks {looks}")                              # both answers stay in the run's log: the pilot reads whether the turned look runs lower
    return min(looks) if looks else None

def master_round(h, rows):
    """v12 F318: how often he had this master remade - each REDO leaves one row '<hash>-redo-...'."""
    return sum(1 for r in rows if str(r.get("hash") or "").startswith(h + "-redo-"))

def master_tries(h, rows):
    """v12 F318: this round's refused attempts, oldest first (rows '<hash>-r<round>-try<k>')."""
    pre = f"{h}-r{master_round(h, rows)}-try"
    return [r for r in rows if str(r.get("hash") or "").startswith(pre)]

def status_score(status):
    m = re.search(r"identity (\d+)/10", str(status or ""))
    return float(m.group(1)) if m else None

def sheets_owed():
    """v12 F318: the pictures the plan still needs - every planned master and sheet with no row that has a file."""
    have = {r.get("hash") for r in store().rows("Character_Sheets") if r.get("file")}
    return sum(1 for p in masters_plan() + plan() if p["hash"] not in have)

def masters(limit=None):
    """Make the missing master portraits (reference-based, inside the lifetime cap). Each is a DRAFT for him: his Approve locks it, and one he leaves alone is LOCKED by auto_lock after SHEETS_DEFAULT_LOCK_H hours (silence = yes, the memo's row 34) - so the card says each identity score against his portrait (CA3-5)."""
    from whatifs import anim as ANIM, publish as PUB, specials as SP, governor as GOV
    st = store(); have = {r.get("hash"): r for r in st.rows("Character_Sheets")}; cap = S("CHARACTER_SHEET_IMAGE_CAP", int)
    made = 0; out_dir = os.path.join(WORK, "sheets"); os.makedirs(out_dir, exist_ok=True); done = []; scored = []
    floor_on = S("MASTER_FLOOR_ON", bool); floor = S("MASTER_MIN_IDENTITY", float); low = []      # v12 F318: the floor, the remakes and what the card says of them
    his = {r.get("character") for r in st.rows("Character_Sheets") if r.get("status") == "LOCKED" and r.get("file")}
    for p in masters_plan():
        if p["hash"] in have and have[p["hash"]].get("file"): continue
        if limit and made >= limit: break
        if used() >= cap and not master_tries(p["hash"], st.rows("Character_Sheets")): break      # as at S0 the cap is asked BEFORE the portrait (it can draw a paid picture); a round already begun still ends below
        who = p["character"]; ref = SP._portrait(who, out_dir, "SHEETS")          # ONCE per character, never per attempt (it can draw a paid picture)
        judged = bool(floor_on and ref and who in his)                            # a floor only against a portrait he locked
        more = max(0, S("MASTER_REMAKES_MAX", int)) if judged else 0; kept = False; why = ""
        for _ in range(more + 1):                                                 # a paid loop also ends by its own count, never only by a re-read of the tab
            if kept or why: break
            rows = st.rows("Character_Sheets"); k = len(master_tries(p["hash"], rows))
            if k == 0: pass                                                       # the first picture: the cap was asked above, before the portrait
            elif k > more: why = "no remake left"
            elif cap - used() - sheets_owed() < 0: why = "no spare picture inside the lifetime cap"
            else:
                ok, no = GOV.extras_allowed(S("PRICE_GEM_IMAGE_USD", float) * S("USD_INR", float))
                if not ok: why = "no money room this month"; log(f"master {who}: no remake - {no}", "WARN")
            if why: break
            text = p["retry"] if k == 1 and p.get("retry") else p["prompt"]
            path = os.path.join(out_dir, f"{who}_master_{p['hash']}.png" if k == 0 else f"{who}_master_{p['hash']}-{k}.png")
            try:
                ANIM.gemini_image(text, [ref] if ref else [], path, "SHEETS", aspect="3:4")
                sc = (master_score if judged else identity_score)(ref, path, who) if ref else None
                if judged and sc is not None: sc = float(round(sc))               # what is compared is what is stored and said
                bad = bool(judged and sc is not None and sc < floor)
                fid = PUB.drive_upload(path, os.path.basename(path))[0]
                st.append("Character_Sheets", [{"ts": iso(), "character": who, "expression": "master", "hash": f"{p['hash']}-r{master_round(p['hash'], rows)}-try{k}" if bad else p["hash"],
                                                "prompt": text[:400], "file": "drive:" + fid, "approved_at": "",
                                                "status": f"REJECTED (identity {sc:.0f}/10)" if bad else f"DRAFT (identity {sc:.0f}/10)" if sc is not None else "DRAFT"}])
                if not bad:
                    kept = True; made += 1; done.append(who)
                    if sc is not None: scored.append((who, sc))      # FINISHED BY FABLE (CA3-5; B3 ruled (C) by R1-104): the card says each score
            except Exception as e: log(f"master portrait {who} failed: {str(e)[:120]}", "WARN"); why = "a remake failed"
        tries = master_tries(p["hash"], st.rows("Character_Sheets"))
        if tries and not kept:                                                    # nothing reached the floor: the best attempt stands as his draft
            best = max(tries, key=lambda r: status_score(r.get("status")) or 0.0)  # the first of equals = the earliest
            st.update_where("Character_Sheets", {"hash": best["hash"]}, {"status": str(best.get("status")).replace("REJECTED", "DRAFT", 1), "hash": p["hash"]})
            made += 1; done.append(who); scored.append((who, status_score(best.get("status")) or 0.0)); low.append((who, len(tries), why or "no remake left"))
    if made:
        dflt, hrs = _review_card()
        spare_note = " (no spare picture is left: a remake takes one from the expression sheets)" if low and cap - used() - sheets_owed() < 1 else ""
        try: NT.mail("sheets_review", "New Toybox Noir character masters to approve",
                     buttons=[(f"Remake {c}", f"REDO SHEET {c} master") for c, _, _ in low] + [(f"Approve {c}", f"APPROVE SHEET {c}") for c in sorted(set(done))],      # v12 F318: Remake first; more than three choices reach WhatsApp as a list (wa.send_buttons, RUL-U1h 1)
                     default=dflt, expires_h=hrs, dedupe_key=f"sheets|masters|{','.join(sorted(set(done)))}|{NT._india_day()}", html=f"<p>{made} master portrait(s) in Drive (Character_Sheets tab, expression 'master'), made from your approved portraits. "
                       f"Approve to LOCK them; animated scenes then use them as the face reference. Lifetime images used: {used()} of {cap}.</p>"
                       + (f"<p>Identity against your portrait: {', '.join(f'{c} {s:.0f}/10' for c, s in scored)}. A low score means the face moved - look before it locks.</p>" if scored else "")      # FINISHED BY FABLE (CA3-5): silence locks a scored master - the card says each score first
                       + (f"<p>Still under {floor:.0f}/10 after every allowed try: {'; '.join(f'{c} ({n} picture(s), {w})' for c, n, w in low)}. The best one is shown. Tap Remake to try again{spare_note}; left alone, {dflt}.</p>" if low else ""))
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
            dflt, hrs = _review_card()
            NT.mail("sheets_review", "Character sheets ready to review", buttons=[(f"Approve {c}", f"APPROVE SHEET {c}") for c in chars],
                    default=dflt, expires_h=hrs, dedupe_key=f"sheets|expressions|{NT._india_day()}", html=f"<p>{made} new image(s) in Drive (Character_Sheets tab). Approving locks them; CHARACTER_THEATER_ON stays FALSE "
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
        if str(r.get("status") or "").startswith("DRAFT") and r.get("file") and t0 and (now - t0).total_seconds() > h * 3600:
            st.update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "LOCKED", "approved_at": iso() + " (default)"}); n += 1
    rows = st.rows("Character_Sheets")
    chars = {r.get("character") for r in rows if r.get("character")}
    all_locked = bool(chars) and all(any(x.get("character") == c and x.get("status") == "LOCKED" for x in rows) for c in chars)
    if n and all_locked and not S("CHARACTER_THEATER_ON", bool) and not str(S("SHEETS_THEATER_AUTO_ON_AT") or "").strip():
        set_setting("CHARACTER_THEATER_ON", "TRUE"); set_setting("SHEETS_THEATER_AUTO_ON_AT", iso())
        try:
            from whatifs import publish as PUB
            NT.mail("sheets_locked", "Character sheets locked by default", f"<p>{n} sheet image(s) were locked after {int(h)} hours without a reply, and the characters now appear on screen "
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
            if r.get("character") == m.group(1) and str(r.get("status") or "").startswith("DRAFT"):      # FINISHED BY FABLE (CA2-4): a scored master is "DRAFT (identity N/10)"
                st.update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "LOCKED", "approved_at": iso()}); n += 1
        return f"{n} image(s) locked"
    m = re.match(r"^REDO SHEET ([A-Z]+) ([a-z]+)$", t)
    if m:
        live = [r for r in st.rows("Character_Sheets") if r.get("character") == m.group(1) and r.get("expression") == m.group(2) and not str(r.get("status") or "").startswith(("REDO", "REJECTED"))]      # v12 F318: the LIVE images, never an old cleared or refused row
        for r in ([x for x in live if str(x.get("status") or "").startswith("DRAFT")] or live)[-1:]:      # RUL-U1i 2: the DRAFT he was shown before any LOCKED row; of equals the newest
            was, redo = (r["hash"], r.get("status")), r["hash"] + "-redo-" + iso()[:16]
            st.update_where("Character_Sheets", {"hash": was[0]}, {"status": "REDO", "hash": redo})
            if S("MASTER_FLOOR_ON", bool):      # RUL-U3k U1-2: every Remake starts the run that remakes it (sheets.yml is never scheduled: no "next run" comes by itself); off = S0 as typed
                if start_sheets_run(): return "cleared; the sheets run that remakes it has been started (lifetime cap still applies)"      # code review U1FIX-b (4), widened by RUL-U3k U1-2 to every expression
                st.update_where("Character_Sheets", {"hash": redo}, {"status": was[1], "hash": was[0]})      # CR-U1FIX_2 (4): no run started, so no next run comes - the image is put back, nothing cleared
                return f"NOT remade: the sheets run could not be started, so {m.group(1)}'s {m.group(2)} was kept as it was (nothing cleared)."
            return "cleared; the next sheets run remakes it (lifetime cap still applies)"
        return "no such image"
    raise SystemExit("usage: 'APPROVE SHEET VALE' or 'REDO SHEET VALE smug'")

def start_sheets_run():
    """v12 F318: his Remake tap starts the sheets run itself (the workflow is never scheduled). True when GitHub took it."""
    try:
        from whatifs import builds as BLD
        return bool(BLD.dispatch("sheets.yml", {}))
    except Exception as e: log(f"sheets run not started: {str(e)[:120]}", "WARN"); return False

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
    try: NT.mail("style_pick", "Pick the look of your show (3 styles, your characters)", f"<p>The comparison board: <a href='{link}'>{link}</a></p><p>Reply on WhatsApp or the dashboard with your pick.</p>", screens=False)
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

