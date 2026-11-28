"""U1 fix 236 (B-OWNER audit J19-2, HELD): HIS "Discuss" ON THE REVIEW CARD NO LONGER ENDS THE FILM'S ROAD. A Discuss on a `review|` card is recorded
(notify.answer logs his tap) and the card is left OPEN - as `_ran` re-opens a card - so it stays under "Needs you" and his silence is still asked:
past the hours the clean video is SCHEDULED. U1 J 236 (RUL-U1): the answer he reads says so - with TWO_SCREENS_ON that his silence approves it at the
time on the card, with it off that it stays private; a Discuss on any other card is "recorded" as before. RUL-U1g 2: the answer asks the rule the
expiry asks (`contract._silence_approves`: the switch now AND the card's own default), so the words and the act cannot drift apart."""
from whatifs import core, notify as NT, contract as CON
from tests.test_v12_owner import _ep8, _epi, _kind, _later

SAID_ON = "Noted. The review stays open: Approve or Hold. Without your tap it is approved by your silence at the time on the card."
SAID_OFF = "Noted. The review stays open: Approve or Hold. Without your tap it stays private."


def test_a_discuss_leaves_the_review_card_open_and_his_silence_still_schedules(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "s")
    card = _kind("creative_review", "EP8")[0]
    assert NT.answer(card["id"], "DISCUSS review EP8") == SAID_ON
    assert card["id"] in [r["id"] for r in NT.needs()], "the Discuss closed the review card: nothing is left under Needs you"
    NT.expire_defaults(now=_later(14 + 1))
    assert _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)]


def test_with_the_switch_off_his_discuss_is_told_the_video_stays_private(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting); setting("TWO_SCREENS_ON", "FALSE")
    CON.await_approval("EP8", "ytEP8", slot, "s")
    card = _kind("creative_review", "EP8")[0]; assert card["default_action"] == "stays private"
    assert NT.answer(card["id"], "DISCUSS review EP8") == SAID_OFF
    assert next(r for r in core.store().rows("Owner_Actions") if r["id"] == card["id"])["status"] == "OPEN" and sched == []


def test_a_discuss_on_another_card_is_unchanged(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting, ep="EP9")
    row = NT.send("contract_hold", "held", [("Discuss", "DISCUSS contract EP9")], tier="now", urgent=True, episode="EP9", dedupe_key="contract|EP9|script")
    rid = row if isinstance(row, str) else row.get("id")
    assert NT.answer(rid, "DISCUSS contract EP9") == "recorded"
    assert next(r for r in core.store().rows("Owner_Actions") if r["id"] == rid)["status"] == "ANSWERED"


def test_a_card_that_said_stays_private_is_answered_so_after_the_switch_is_turned_on(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting); setting("TWO_SCREENS_ON", "FALSE")
    CON.await_approval("EP8", "ytEP8", slot, "s")
    card = _kind("creative_review", "EP8")[0]; assert card["default_action"] == "stays private"
    setting("TWO_SCREENS_ON", "TRUE")
    assert NT.answer(card["id"], "DISCUSS review EP8") == SAID_OFF
    NT.expire_defaults(now=_later(72 + 1))
    assert sched == [] and _epi("EP8")["status"] != "SCHEDULED"                                  # the answer and the act agree: it stays private


def test_a_card_that_said_silence_approves_is_answered_stays_private_while_the_switch_is_off(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "s")
    card = _kind("creative_review", "EP8")[0]; assert card["default_action"] == "approved by your silence"
    setting("TWO_SCREENS_ON", "FALSE")
    assert NT.answer(card["id"], "DISCUSS review EP8") == SAID_OFF
    NT.expire_defaults(now=_later(14 + 1))
    assert sched == [] and _epi("EP8")["status"] != "SCHEDULED"
