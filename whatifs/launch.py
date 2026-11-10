"""Launch checks: the zero-cost upload check, the private-lock detector and the uploads-open rule. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os, subprocess, tempfile
from whatifs.core import S, log, set_setting, iso, now_utc, parse_iso, FAKE

_FAKE_RESULT = ["unlisted"]          # tests set this to "private" to simulate a locked project


def lock_state():
    v = str(S("UPLOAD_LOCK") or "unknown").strip().lower()
    return v if v in ("on", "off", "unknown") else "unknown"


def uploads_open():
    """True when a public upload is known to work: the upload check passed (UPLOAD_LOCK = off) or the old API audit is approved."""
    if lock_state() == "off": return True
    try:
        from whatifs.manage import audit_state
        return audit_state() == "approved" and lock_state() != "on"
    except Exception: return False


def _status(key, ok, msg):
    try:
        from whatifs.manage import status
        status(key, ok, msg)
    except Exception as e: log(f"Setup_Status {key} not written: {e}", "WARN")


def _test_clip(out_dir):
    """A 20-second, 1280x720 clip (dark frame + quiet tone). Pure ffmpeg, no paid call."""
    path = os.path.join(out_dir, "upload_check.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x151A2E:s=1280x720:r=30:d=20",
           "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000:duration=20", "-shortest",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", path]
    subprocess.run(cmd, check=True, timeout=120)
    return path


def upload_check(force=False):
    """The ₹0 upload check (L1). Idempotent: once it has passed it does nothing unless force=True. Never raises."""
    if not force and lock_state() == "off": return "upload check already passed (UPLOAD_LOCK = off)"
    from whatifs import publish as PUB
    got, vid = "", ""
    try:
        if FAKE: got = _FAKE_RESULT[0]; vid = "FAKE_upload_check"
        else:
            with tempfile.TemporaryDirectory() as td:
                clip = _test_clip(td)
                vid = PUB.yt_upload(clip, "Reality Engine - upload check", "Automatic upload check. This test video is deleted within a minute.",
                                    ["test"], privacy="unlisted", ai_label=True, verify=False)
            got = str((PUB.yt_status_full(vid) or {}).get("privacyStatus") or "")
    except Exception as e:
        set_setting("UPLOAD_CHECK_AT", iso())
        _status("upload_check", False, f"could not run yet: {str(e)[:160]} (it retries in 6 h; nothing is spent)")
        log(f"upload check could not run: {e}", "WARN"); return "upload check could not run"
    finally:
        if vid and not FAKE:
            try: PUB.yt_delete(vid)
            except Exception as e: log(f"upload check: test video {vid} not deleted ({e}); delete it in Studio", "WARN")
    set_setting("UPLOAD_CHECK_AT", iso())
    if got == "unlisted":
        set_setting("UPLOAD_LOCK", "off"); set_setting("API_AUDIT_STATUS", "approved")
        _status("upload_check", True, "passed - uploads can go public (YouTube lifted the private lock on 2 Nov 2026)")
        _status("youtube_api_audit", True, "not needed: the upload check passed")
        log("upload check passed: UPLOAD_LOCK = off"); return "passed"
    lock_detected(vid or "upload_check", [f"test upload came back '{got or 'unknown'}' instead of 'unlisted'"])
    return "locked"


def due_check():
    """True when the upload check should run now: the lock state is unknown and the last attempt is older than 6 hours."""
    if lock_state() != "unknown": return False
    last = parse_iso(S("UPLOAD_CHECK_AT"))
    return not last or (now_utc() - last).total_seconds() > 6 * 3600


def lock_detected(vid, issues):
    """Called when YouTube kept an upload private against our request. Holds production through the gate (no money wasted)."""
    set_setting("UPLOAD_LOCK", "on")
    _status("upload_check", False, "LOCKED: YouTube kept an upload private. New videos are paused (nothing is spent). See the email.")
    log(f"UPLOAD LOCK detected on {vid}: {'; '.join(issues)}", "ERROR")
    last = parse_iso(S("UPLOAD_LOCK_ALERT_AT"))
    if last and (now_utc() - last).total_seconds() < 86400: return
    set_setting("UPLOAD_LOCK_ALERT_AT", iso())
    try:
        from whatifs import publish as PUB
        PUB.email("URGENT: YouTube is keeping uploads private again",
                  "<p>An upload came back <b>private</b> even though the pipeline asked for it to be visible. New videos are paused, so no money is spent on videos nobody can see.</p>"
                  f"<p>Video: <a href='https://studio.youtube.com/video/{vid}/edit'>open in Studio</a>.</p>"
                  "<p>What happens next: your build chat files the YouTube API audit form for you (master file Section 4, Answer Bank). Until Google approves it, "
                  "you can still publish a finished video yourself: open it in the YouTube Studio app and set it to Public (about 1 minute).</p>"
                  "<p>When the audit is approved, set Settings -> UPLOAD_LOCK = off (or tell the build chat). Production restarts by itself.</p>")
    except Exception as e: log(f"lock alert email failed: {e}", "WARN")
