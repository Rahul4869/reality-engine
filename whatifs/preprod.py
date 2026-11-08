"""v9.4a (WP2, K123): pre-production at half price. The writers' room for the next slot runs PREPROD_LEAD_HOURS early (when nobody is waiting), every
Claude call through the Message Batches API (50% off, stacks with prompt caching), and the result is saved as an APPROVED draft that the normal production
job takes as written (preview.take_approved). Nothing else changes: voice, pictures, render and upload still happen PRODUCE_AHEAD_HOURS before the slot.
Safety: a call that waits longer than ROOM_BATCH_MAX_WAIT_MIN runs directly (never two paid answers); after PREPROD_JOB_MAX_HOURS all remaining calls run
directly; if pre-production fails or is late, production simply writes the episode itself as before (a slot is never skipped, K92)."""
from __future__ import annotations
import time
from whatifs.core import S, log, store, now_utc, parse_iso, JOB, flush_log

def _slot_taken(slot):
    for e in store().rows("Episodes"):
        t = parse_iso(e.get("slot_et"))
        if t and abs((t - slot).total_seconds()) < 3600: return True
    return False

def due(now=None):
    """The slot pre-production should write for now, or None. One waiting draft at a time; never inside the production window."""
    if not S("PREPROD_ON", bool): return None
    if any(r.get("status") == "APPROVED" for r in store().rows("Script_Previews")): return None
    from whatifs.manage import next_slots
    now = now or now_utc(); lead, lo = S("PREPROD_LEAD_HOURS", float), S("PREPROD_MIN_LEAD_HOURS", float)
    for slot in next_slots(3, now):
        h = (slot - now).total_seconds() / 3600
        if lo <= h <= lead and not _slot_taken(slot): return slot
    return None

def run(force=False, check_only=False):
    """python -m whatifs.cli preprod [--check] [--force]. --check prints yes/no and spends nothing."""
    slot = due()
    if check_only: return "yes" if (slot or force) else "no"
    if not slot and not force:
        log("pre-production: nothing due"); return {"ok": True, "due": False}
    from whatifs import models as M, preview as PV
    M.PREPROD["on"] = True
    M.PREPROD["deadline"] = time.time() + max(0.5, S("PREPROD_JOB_MAX_HOURS", float)) * 3600 - 900
    try:
        return PV.run(mode="preprod")
    except Exception as e:
        log(f"pre-production failed ({str(e)[:200]}); production will write this episode itself", "WARN"); flush_log()
        return {"ok": False, "why": str(e)[:300]}
    finally:
        M.PREPROD["on"] = False; M.PREPROD["deadline"] = 0.0
