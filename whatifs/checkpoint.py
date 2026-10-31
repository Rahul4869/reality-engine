"""whatifs/checkpoint.py v8.2 - save and restore the expensive state of an episode in your private Drive.

Why: before v8.2 a failure after the AI writing (about Rs 140) or after the paid images/clips threw all of it away and the retry paid again. Now:
  plan   = script, voice (the narration clock), shot list, bible, packaging inputs      -> saved after planning
  assets = every paid picture and clip                                                    -> saved after the assets are made
  hold   = everything needed to re-render (plus thumbnail, covers, reels)                 -> saved when final QC fails (the one-click fix reads it)
A retry of the same slot, or the one-click fix, restores the newest stage and continues from there. Best effort: if Drive is unavailable the episode simply
runs as before. Segments and the master are never stored (they are cheap to render again).
"""
from __future__ import annotations
import os, re, json, zipfile
from whatifs.core import log, store, S, scrub
from whatifs import publish as PUB

ORDER = ("plan", "assets", "hold")
_PATTERNS = {
    "plan": [r"^plan\.json$", r"^hooks\.json$", r"^voice[^/]*\.(wav|json)$"],
    "assets": [r"^assets\.json$", r"^img\d+\.jpg$", r"^clip\d+\.mp4$"],
    "hold": [r"^thumb[^/]*\.jpg$", r"^cover\d(_raw)?\.jpg$", r"^reel\d\.mp4$", r"^thumb_raw\.jpg$"],
}
def _key(stage): return f"_ckpt_{stage}.zip"

def attempts(row):
    """How many production attempts this episode row has had (kept in its notes as 'attempts=N'; rows from older versions count as 1)."""
    m = re.search(r"attempts=(\d+)", str((row or {}).get("notes") or "")); return int(m.group(1)) if m else 1

def set_attempts(notes, n):
    t = re.sub(r"\s*\|?\s*attempts=\d+", "", str(notes or "")).strip(" |")
    return (t + " | " if t else "") + f"attempts={n}"

def _assets_of(row):
    a = row.get("assets") or {}
    return a if isinstance(a, dict) else json.loads(a or "{}")

def has(row): return any(_key(s) in _assets_of(row) for s in ORDER)

def save(out, ep, stage, state=None):
    """Zip the files of this stage and every earlier one; replace the previous checkpoint of the same stage. Never raises. Returns the Drive id or None."""
    if not S("CHECKPOINT_ON", bool): return None
    try:
        if state:
            for name, obj in state.items(): json.dump(obj, open(os.path.join(out, name), "w", encoding="utf-8"), default=str)
        want = [p for s in ORDER[: ORDER.index(stage) + 1] for p in _PATTERNS[s]]
        zp = os.path.join(out, _key(stage))
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
            for f in sorted(os.listdir(out)):
                if any(re.match(p, f) for p in want): z.write(os.path.join(out, f), f)
        fid, _ = PUB.drive_upload(zp, f"{ep}{_key(stage)}", public=False); os.remove(zp)
        st = store(); row = next((r for r in st.rows("Episodes") if r["episode_id"] == ep), None)
        if row is not None:
            a = _assets_of(row); old = [a.get(_key(stage))] + [a.pop(_key(s), None) for s in ORDER[: ORDER.index(stage)]]    # earlier stages are subsets of this one
            a[_key(stage)] = fid
            st.update("Episodes", "episode_id", ep, {"assets": a})
            for o in old:
                if o and o != fid: PUB.drive_delete(o)
        return fid
    except Exception as e:
        log(f"checkpoint '{stage}' not saved ({scrub(e)[:160]}) - the episode continues without it", "WARN"); return None

def restore(ep, out):
    """Download and unpack the newest checkpoint into out. Returns the stage name or None."""
    st = store(); row = next((r for r in st.rows("Episodes") if r["episode_id"] == ep), None)
    if row is None: return None
    a = _assets_of(row)
    for stage in reversed(ORDER):
        fid = a.get(_key(stage))
        if not fid: continue
        try:
            zp = os.path.join(out, _key(stage)); PUB.drive_download(fid, zp)
            with zipfile.ZipFile(zp) as z: z.extractall(out)
            os.remove(zp)
            return stage                                   # a later stage's zip already contains the earlier files
        except Exception as e: log(f"checkpoint '{stage}' could not be restored ({scrub(e)[:160]})", "WARN")
    return None

def clear(ep):
    """The episode is finished: remove its checkpoints from Drive (older ones are also cleaned by DRIVE_ARCHIVE_KEEP for masters)."""
    try:
        st = store(); row = next((r for r in st.rows("Episodes") if r["episode_id"] == ep), None)
        if row is None: return
        a = _assets_of(row)
        for s in ORDER:
            fid = a.pop(_key(s), None)
            if fid: PUB.drive_delete(fid)
        st.update("Episodes", "episode_id", ep, {"assets": a})
    except Exception as e: log(f"checkpoint clean-up skipped: {scrub(e)[:120]}", "WARN")
