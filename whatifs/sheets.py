"""whatifs/sheets.py v9 (stage 3c) - the one-time CHARACTER SHEETS workflow (K102). Expression sheets (SHEET_EXPRESSIONS per character) + the courtroom
set, made ONCE with a hard LIFETIME image cap (CHARACTER_SHEET_IMAGE_CAP; counted from the Character_Sheets tab, never reset by code), every image keyed
by a content hash (a rerun never re-buys an image), LOCKED after the owner's one-click approval; a locked image is regenerated only by the owner's
'REDO SHEET' click (which still counts toward the cap). Nothing here runs on a schedule: workflow 'sheets' (manual) only.
Face consistency: every expression is made from the same written identity (visual + 'same person as the reference') and, when the image model accepts
it, the approved neutral portrait as a reference image. Which fal model keeps one face across expressions was NOT verified (see the report)."""
from __future__ import annotations
import hashlib, os, re
from whatifs.core import S, log, store, iso, WORK, env

EXPRESSIONS = ["neutral", "smug", "outraged", "delighted", "sceptical", "shocked", "thinking", "defeated", "triumphant", "whispering", "laughing", "stern"]
LOOK = ("cinematic adult realism, natural human proportions, 35mm film still, moody courtroom lighting, no text, no logo, no cartoon, no chibi, "
        "no mascot, no child")

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

def used():
    return sum(1 for r in store().rows("Character_Sheets") if r.get("file"))

def run(limit=None):
    """Make the missing sheet images inside the lifetime cap. Returns {made, skipped_cap, have}. Bounded: one attempt per image per run."""
    from whatifs import media as M, publish as PUB
    st = store(); have = {r.get("hash"): r for r in st.rows("Character_Sheets")}; cap = S("CHARACTER_SHEET_IMAGE_CAP", int)
    made = skipped = 0; base = used(); out_dir = os.path.join(WORK, "sheets"); os.makedirs(out_dir, exist_ok=True)
    for p in plan():
        if p["hash"] in have and have[p["hash"]].get("file"): continue           # idempotent: never bought twice
        if base + made >= cap or (limit and made >= limit): skipped += 1; continue
        path = os.path.join(out_dir, f"{p['character']}_{p['expression']}_{p['hash']}.jpg")
        try:
            M.still(p["prompt"], path, "SHEETS", seed=p["hash"], premium=True)
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
