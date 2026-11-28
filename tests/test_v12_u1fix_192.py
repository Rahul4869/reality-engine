"""U1 fix 192 (open issue 215): FLOOR DROP NEVER SAYS "is dropped" WHILE NOTHING DROPS IT. With the cell KILL_CHECK FALSE manage.kill_check returns at
once: his drop is still marked (KILL, kept for when the check is on) and kept as his verdict, and the answer says plainly that nothing drops it."""
from whatifs import core, manage as MG
from whatifs.org import floor as FL


def _ep(ep):
    MG.setup(); core.store().append("Episodes", [{"episode_id": ep, "status": "HOLD_QC", "title": "Flop", "kill": "", "yt_id": ""}])


def test_a_drop_with_the_kill_check_off_says_nothing_drops_it(setting):
    _ep("EPKCOFF"); setting("KILL_CHECK", "FALSE")
    a = FL._answer({"episode_id": "EPKCOFF"}, "FLOOR DROP EPKCOFF")
    assert "is dropped" not in a and "KILL_CHECK" in a and "nothing drops it" in a, a
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == "EPKCOFF"); assert e["kill"] == "KILL"


def test_a_drop_with_the_kill_check_on_is_dropped(setting):
    _ep("EPKCON"); setting("KILL_CHECK", "TRUE")
    assert FL._answer({"episode_id": "EPKCON"}, "FLOOR DROP EPKCON") == "EPKCON is dropped"
