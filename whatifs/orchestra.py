"""v9.4a (ORCHESTRA, K127): heavy optional jobs never run inside a release window or a production run, so nothing clashes, times out or fights
for quotas. Locks between workflows are GitHub concurrency groups (produce, release, preprod, build, sheet-heavy); this module is the time-window rule."""
from __future__ import annotations
from whatifs.core import S, log, store, now_utc, parse_iso

def heavy_allowed(now=None, what="job"):
    """False within ORCHESTRA_RELEASE_GUARD_H hours before or after a scheduled release (optional heavy jobs wait for the next run)."""
    now = now or now_utc(); g = S("ORCHESTRA_RELEASE_GUARD_H", float)
    if g <= 0: return True
    for e in store().rows("Episodes"):
        t = parse_iso(e.get("slot_et"))
        if t and abs((t - now).total_seconds()) < g * 3600 and str(e.get("status", "")).upper() not in ("KILLED", "FAILED"):
            log(f"{what} waits: a release is within {g:g} h (ORCHESTRA)"); return False
    return True
