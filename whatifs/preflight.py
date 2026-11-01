"""whatifs/preflight.py v8.3 - free health checks BEFORE any paid step. A red critical check means: do not start (no episode row, no spend, one email per day).

Most wasted retries come from a problem that was knowable in advance: a missing key, a full disk, a voice engine that cannot load, a Google sign-in that
expired, a model list that is empty. Those are checked here, once, for free.
"""
from __future__ import annotations
import os, shutil
from whatifs.core import env, log, FAKE, SMALL, WORK, scrub

def run(need_voice=True):
    """Returns [(name, ok, detail, critical)]."""
    r = []
    def add(name, ok, detail="", critical=True): r.append((name, bool(ok), str(detail)[:160], critical))
    add("ffmpeg", shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe on the machine")
    try: free = shutil.disk_usage(WORK).free / 1e9
    except Exception: free = 99
    need = 1.0 if SMALL else 8.0            # v8.3: segments + joined video + master are about 3 GB at CRF 20; 8 GB leaves room for repairs and checkpoints
    add("disk", free >= need, f"{free:.1f} GB free (need {need:.0f})")
    if FAKE: return r
    for k in ("ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY", "SHEET_ID", "G_REFRESH", "G_CLIENT_ID", "G_CLIENT_KEY"):
        add(f"key {k}", bool(env(k)), "present" if env(k) else "MISSING (GitHub Actions secret)")
    try:
        from whatifs.core import google_access; google_access(); add("google sign-in", True, "token refreshed")
    except Exception as e: add("google sign-in", False, scrub(e)[:120])
    try:
        from whatifs.models import model; add("models", bool(model("sonnet")) and bool(model("gem_flash") or model("gem_pro")), "Claude and Gemini models known")
    except Exception as e: add("models", False, scrub(e)[:120])
    if need_voice:
        try: import kokoro, soundfile; add("voice engine", True, "Kokoro importable")
        except Exception as e: add("voice engine", False, scrub(e)[:120])
    try:                                               # v8.9.2: Drive has its own Google key (G_REFRESH_DRIVE); a warning, never a block
        from whatifs.core import google_access, _gtok; google_access("drive"); dok = "drive.file" in _gtok["drive"]["scope"]
    except Exception: dok = False
    add("drive sign-in", dok, "Drive allowed" if dok else "no Drive permission: run Google Sign-in link 2 and save G_REFRESH_DRIVE", critical=False)
    try:                                               # v8.3: Drive space (the archive and the held-video bundles live there); a warning, never a block
        from whatifs.core import gdrive_headers; import requests
        q = requests.get("https://www.googleapis.com/drive/v3/about?fields=storageQuota", headers=gdrive_headers(), timeout=20).json().get("storageQuota", {})
        if q.get("limit"):
            left = (int(q["limit"]) - int(q.get("usage", 0))) / 1e9
            add("drive space", left >= 3.0, f"{left:.1f} GB free in Drive (need 3)", critical=False)
    except Exception: pass
    add("fonts", os.path.exists("fonts/Anton-Regular.ttf") or os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), "headline font (falls back to a plain font)", critical=False)
    return r

def check(need_voice=True):
    """(ok, text). ok is False only when a CRITICAL check failed."""
    res = run(need_voice); bad = [x for x in res if not x[1]]
    crit = [x for x in bad if x[3]]
    for n, ok, d, c in bad: log(f"pre-flight {'FAILED' if c else 'warning'}: {n}: {d}", "WARN" if not c else "ERROR")
    return not crit, "; ".join(f"{n}: {d}" for n, ok, d, c in crit)
