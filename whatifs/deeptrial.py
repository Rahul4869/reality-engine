"""The monthly Deep Trial: one long slot a month becomes a ~20-minute episode. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
from whatifs.core import S, log, set_setting, parse_iso, now_utc

NOTE = ("DEEP TRIAL (this is the month's special, about 20 minutes): write THREE ACTS with a short chapter title line before each "
        "('## ACT 1: ...'). Each act ends with a DIFFERENT outcome type (one win, one loss, one absurd turn) and a re-hook line spoken by a different "
        "character than the one before. Between act 2 and act 3 add a 3-5 minute JURY ROOM segment: the cast argue the evidence among themselves "
        "(Vale, Grimm, Nana Rosa, the Archivist), each new exhibit changes someone's mind, at least two jokes per minute, and it ends on the question "
        "the verdict answers. Keep every rule above; the length target already includes all of this.")

def due(slot_iso, now=None):
    """True for the first long slot on or after DEEP_TRIAL_DAY in a month that has no Deep Trial yet."""
    if not S("DEEP_TRIAL_ON", bool): return False
    t = parse_iso(slot_iso) or (now or now_utc())
    return t.day >= S("DEEP_TRIAL_DAY", int) and str(S("DEEP_TRIAL_MONTH") or "") != t.strftime("%Y-%m")

def maybe(d, ep, slot_iso):
    """Turns this episode's draw into the Deep Trial when one is due. Returns True when it did."""
    if not due(slot_iso): return False
    d["deep_trial"] = True
    d["words"] = int(int(d.get("words") or 1500) * S("DEEP_TRIAL_WORDS_MULT", float))
    t = parse_iso(slot_iso) or now_utc()
    set_setting("DEEP_TRIAL_MONTH", t.strftime("%Y-%m"))
    log(f"Deep Trial: this slot is the month's ~20-minute special ({d['words']} words)", episode=ep)
    return True
