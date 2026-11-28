"""U1 fix 219 (open issue 250): an explaining moment's line must outlast BOTH cells - DRAWN_MIN_S and UNIT_MERGE_SEC - or the renderer's merge
takes the line away and the scene is left with no proof and no reason (check drawn_shown FAILs). scenes.slots takes the larger of the two."""
from whatifs import scenes as SCN

G = {"kind": "counter", "label": "Pillows airborne", "from": 0, "to": 8000000000, "unit": ""}


def _film(dur1):
    starts = [0.0, 4.0, 4.0 + dur1, 12.0]
    units = [{"i": k, "text": "line %d" % k, "start": s, "end": s + 0.5, "words": [], "speaker": "GUIDE"} for k, s in enumerate(starts)]
    shots = [{"type": "still", "prompt": "a picture"}] + [{"type": "graphic", "graphic": dict(G), "prompt": "a picture"} for _ in range(3)]
    return shots, units, 16.0


def test_a_moment_shorter_than_the_merge_is_never_a_slot_when_drawn_min_s_is_below_it(setting):
    setting("DRAWN_MIN_S", "0.5"); setting("UNIT_MERGE_SEC", "1.0")
    shots, units, total = _film(0.8)                         # line 1 lasts 0.8 s: over DRAWN_MIN_S, under the merge
    assert 1 not in SCN.slots(shots, units, total)
    assert SCN.slots(shots, units, total) == [2, 3]


def test_the_larger_cell_wins_both_ways(setting):
    setting("DRAWN_MIN_S", "0.5"); setting("UNIT_MERGE_SEC", "1.0")
    shots, units, total = _film(1.0)                         # exactly the merge: kept (the merge takes only a line SHORTER than its cell)
    assert 1 in SCN.slots(shots, units, total)
    setting("DRAWN_MIN_S", "3.0"); setting("UNIT_MERGE_SEC", "1.0")
    shots, units, total = _film(2.0)                         # over the merge, under DRAWN_MIN_S: not a slot
    assert 1 not in SCN.slots(shots, units, total)
    setting("DRAWN_MIN_S", "2.4"); setting("UNIT_MERGE_SEC", "1.0")
    shots, units, total = _film(2.4)                         # the defaults: unchanged
    assert 1 in SCN.slots(shots, units, total)
