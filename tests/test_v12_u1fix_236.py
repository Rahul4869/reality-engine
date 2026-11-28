"""U1 fix 236 (B-OWNER audit J19-2, HELD): HIS "Discuss" ON THE REVIEW CARD NO LONGER ENDS THE FILM'S ROAD. A Discuss on a `review|` card is recorded
(notify.answer logs his tap) and the card is left OPEN - as `_ran` re-opens a card - so it stays under "Needs you" and his silence is still asked:
past the hours the clean video is SCHEDULED."""
from whatifs import core, notify as NT, contract as CON
from tests.test_v12_owner import _ep8, _epi, _kind, _later


def test_a_discuss_leaves_the_review_card_open_and_his_silence_still_schedules(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "s")
    card = _kind("creative_review", "EP8")[0]
    NT.answer(card["id"], "DISCUSS review EP8")
    assert card["id"] in [r["id"] for r in NT.needs()], "the Discuss closed the review card: nothing is left under Needs you"
    NT.expire_defaults(now=_later(14 + 1))
    assert _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)]


def test_a_discuss_on_another_card_is_unchanged(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting, ep="EP9")
    row = NT.send("contract_hold", "held", [("Discuss", "DISCUSS contract EP9")], tier="now", urgent=True, episode="EP9", dedupe_key="contract|EP9|script")
    rid = row if isinstance(row, str) else row.get("id")
    NT.answer(rid, "DISCUSS contract EP9")
    assert next(r for r in core.store().rows("Owner_Actions") if r["id"] == rid)["status"] == "ANSWERED"
