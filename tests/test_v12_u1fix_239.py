"""U1 J 239 (B-OWNER audit J19-5): A TAP BACK AFTER "Take it down". The usual take-down is of a film stopped BEFORE its slot (items 149, 150); YouTube
takes a time again for it, so sending him to Studio by hand was work only code made necessary. `contract.unpost` reads YouTube's own privacy BEFORE
the take-down; when it said "private" and our record said SCHEDULED, one `decided_post` row offers ("Approve", "APPROVE <ep>") for 7 days - his own
decision, never a hold, never under "Needs you". His Approve reads the channel's two locks (RUL-U1g 4) and runs the review card's `approve` (the
video's own checks are not asked again): its own slot when still 30 minutes ahead and free, otherwise the next free slot (RUL-U1g 1); when it does not
put the video back he is told so and the row stays open. A video that was public, or whose read-back is unknown, keeps today's words and gets no row."""
import datetime as dt
import json
import pytest
from whatifs import core, notify as NT, contract as CON, publish as PUB, launch as LA
from tests.test_v12_owner import _ep8, _epi, _decided, _later

OFFER = ("Title EP8 is private again. Nothing was deleted. Changed your mind? Approve puts it back on the schedule: at its own time if that is still 30 minutes or more ahead and free, otherwise at the next free slot. After 7 days: "
         "YouTube Studio, Visibility.")
SAID_OFFER = "Title EP8 is private again. Nothing was deleted. To put it back: Decided for you, Approve."
SAID_TODAY = "Title EP8 is private again. Nothing was deleted. To publish it later: YouTube Studio, Visibility, Public."


def _yt(monkeypatch, before="private", refuse=False, read=None):
    """YouTube's stand-in: the read-back answers the privacy it holds NOW (so a read-back after the take-down would read the take-down's own
    "private"); every call is written in order."""
    calls, state = [], {"p": before}
    def status_full(vid):
        calls.append("read")
        return read(vid) if read else {"privacyStatus": state["p"], "madeForKids": False}
    def set_privacy(vid, p):
        calls.append("set")
        if refuse: return False
        state["p"] = p; return True
    monkeypatch.setattr(PUB, "yt_status_full", status_full); monkeypatch.setattr(PUB, "yt_set_privacy", set_privacy)
    return calls


def _offers(ep="EP8", status="OPEN"):
    return [r for r in _decided(ep) if r["status"] == status and json.loads(r["buttons"] or "[]") == [["Approve", f"APPROVE {ep}"]]]


def _row(aid): return next(r for r in core.store().rows("Owner_Actions") if r["id"] == aid)


def test_a_never_public_take_down_offers_his_approve_and_it_puts_the_video_back(monkeypatch, setting):
    slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED"); calls = _yt(monkeypatch)
    assert CON.unpost("EP8") == SAID_OFFER
    assert calls == ["read", "set"], calls                                   # YouTube's word is read BEFORE the take-down
    rows = _offers(); assert len(rows) == 1, _decided("EP8")
    row = rows[0]
    assert row["text"] == OFFER and row["dedupe_key"].startswith("decided|EP8|down") and row["episode_id"] == "EP8" and row["tier"] == "week"
    assert not row["default_action"] and row["expires_at"] and NT.group("decided_post") == "decided" and NT.klass("decided_post") != NT.HOLD
    assert row["id"] not in [r["id"] for r in NT.needs()], "his own decision is never under Needs you"
    assert _epi("EP8")["status"] == "HELD_BY_OWNER" and sched == []
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == f"approved: EP8 publishes at {slot}" and _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)], (out, sched)
    assert _row(row["id"])["status"] == "ANSWERED"


def test_unanswered_the_offer_closes_after_seven_days_and_publishes_nothing(monkeypatch, setting):
    _slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    NT.expire_defaults(now=_later(24 * 8))
    assert _row(row["id"])["status"] == "EXPIRED" and _epi("EP8")["status"] == "HELD_BY_OWNER" and sched == []


def test_no_offer_after_a_public_video_an_unknown_read_back_or_a_record_not_scheduled(monkeypatch, setting):
    _ep8(monkeypatch, setting, status="SCHEDULED"); calls = _yt(monkeypatch, before="public")
    assert CON.unpost("EP8") == SAID_TODAY and not _offers() and calls == ["read", "set"]
    for i, read in enumerate((lambda vid: (_ for _ in ()).throw(RuntimeError("YouTube does not answer")), lambda vid: {})):      # a raise, an empty answer
        ep = f"EPR{i}"; _ep8(monkeypatch, setting, ep=ep, status="SCHEDULED"); _yt(monkeypatch, read=read)
        assert CON.unpost(ep) == f"Title {ep} is private again. Nothing was deleted. To publish it later: YouTube Studio, Visibility, Public." and not _offers(ep)
        assert _epi(ep)["status"] == "HELD_BY_OWNER"
    _ep8(monkeypatch, setting, ep="EPL", status="LIVE"); _yt(monkeypatch)          # private on YouTube, but our record says it went out
    assert "To publish it later" in CON.unpost("EPL") and not _offers("EPL")


def test_a_take_down_youtube_refused_offers_nothing(monkeypatch, setting):
    _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch, refuse=True)
    assert "could NOT be made private" in CON.unpost("EP8") and not _offers() and _epi("EP8")["status"] == "SCHEDULED"


def test_a_second_take_down_after_his_approve_gets_its_own_row(monkeypatch, setting):
    _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); first = _offers()[0]
    assert NT.answer(first["id"], "APPROVE EP8").startswith("approved") and _epi("EP8")["status"] == "SCHEDULED"
    assert CON.unpost("EP8") == SAID_OFFER
    again = _offers(); assert len(again) == 1 and again[0]["id"] != first["id"] and _row(first["id"])["status"] == "ANSWERED", _decided("EP8")


def test_an_approve_that_does_not_put_it_back_says_so_and_the_row_stays_open(monkeypatch, setting):
    _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: (_ for _ in ()).throw(RuntimeError("reschedule failed 403")))
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == "Title EP8 could NOT be put back on the schedule: RuntimeError: reschedule failed 403. Set it in YouTube Studio.", out
    assert _row(row["id"])["status"] == "OPEN" and _epi("EP8")["status"] == "HELD_BY_OWNER"
    monkeypatch.setattr(CON, "approve", lambda ep: "no free slot found")
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == "Title EP8 could NOT be put back on the schedule: no free slot found. Set it in YouTube Studio." and _row(row["id"])["status"] == "OPEN"


@pytest.mark.parametrize("case", ["taken", "past"])
def test_his_approve_takes_the_next_free_slot_when_its_own_is_taken_or_past(case, monkeypatch, setting):
    """RUL-U1g 1 (b): the offer's "otherwise at the next free slot" - its own slot held by another SCHEDULED row, or less than 30 minutes ahead (the
    clock at the slot minus 29 minutes: `_ep8` writes the slot to the minute, so 28 to 29 minutes ahead)."""
    slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED", hours=(26.0 if case == "taken" else 29 / 60)); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    assert "at its own time if that is still 30 minutes or more ahead and free, otherwise at the next free slot" in row["text"], row["text"]      # RUL-U1i 1 (b): the words and the act in one test
    if case == "taken": core.store().append("Episodes", [{"episode_id": "EPX", "status": "SCHEDULED", "yt_id": "ytEPX", "slot_et": slot, "title": "Title EPX"}])
    t0 = core.now_utc(); out = NT.answer(row["id"], "APPROVE EP8")
    assert out.startswith("approved: EP8 publishes at "), out
    t = out.rsplit(" ", 1)[1]
    held = {r.get("slot_et") for r in core.store().rows("Episodes") if r.get("episode_id") != "EP8" and r.get("status") in ("SCHEDULED", "LIVE1", "LIVE")}
    assert t != slot and core.parse_iso(t) >= t0 + dt.timedelta(minutes=30) and t not in held and sched == [("ytEP8", t)], (case, out, slot, held, sched)
    assert _epi("EP8")["status"] == "SCHEDULED" and _epi("EP8")["slot_et"] == t and _row(row["id"])["status"] == "ANSWERED"



def test_his_approve_keeps_its_own_slot_at_30_minutes_or_more(monkeypatch, setting):
    """RUL-U1i 1 (c): the keep side of the number the offer says - its own slot 31 to 32 minutes ahead (`_ep8` writes the slot to the minute) and
    free: his Approve puts it back at that very time."""
    slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED", hours=32 / 60); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == f"approved: EP8 publishes at {slot}" and sched == [("ytEP8", slot)], (out, slot, sched)
    assert _epi("EP8")["status"] == "SCHEDULED" and _row(row["id"])["status"] == "ANSWERED"


@pytest.mark.parametrize("ahead_s,kept", [(1800, True), (1799, False)], ids=["exactly_30_min", "one_second_less"])
def test_his_approve_keeps_its_slot_at_exactly_30_minutes_and_moves_it_a_second_less(ahead_s, kept, monkeypatch, setting):
    """RUL-U3k U1-8: the number the offer says, to the second - approve's own clock frozen `ahead_s` seconds before the whole-minute slot."""
    slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED", hours=2.0); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    monkeypatch.setattr(CON, "now_utc", lambda: core.parse_iso(slot) - dt.timedelta(seconds=ahead_s))
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out.startswith("approved: EP8 publishes at "), out
    assert (out == f"approved: EP8 publishes at {slot}") == kept and (sched == [("ytEP8", slot)]) == kept, (out, slot, sched)


@pytest.mark.parametrize("lock", ["paused", "paused_until", "upload_lock"])
def test_his_approve_under_a_channel_lock_schedules_nothing_and_stays_open(lock, monkeypatch, setting):
    """RUL-U1g 4: a lock raised in the 7 days after the take-down - his Approve sends nothing to YouTube, the video stays HELD_BY_OWNER, the row stays
    open and he reads why; the lock lifted, his second Approve puts it back at its own slot. (`_ep8` stubs the uploads open: the uploads case
    puts the real `launch.uploads_open` back, so the UPLOAD_LOCK cell decides.)"""
    real = LA.uploads_open
    slot, sched = _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    if lock == "paused": setting("PAUSED", "TRUE"); why, lift = "the pipeline is paused", ("PAUSED", "FALSE")
    elif lock == "paused_until": setting("PAUSED_UNTIL", core.iso(core.now_utc() + dt.timedelta(hours=1))); why, lift = "the pipeline is paused", ("PAUSED_UNTIL", "")
    else: monkeypatch.setattr(LA, "uploads_open", real); setting("UPLOAD_LOCK", "on"); why, lift = "uploads are not confirmed open yet", ("UPLOAD_LOCK", "off")
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == f"Title EP8 was NOT put back on the schedule: {why}. Your Approve stays open: tap it again once that is lifted.", out
    assert sched == [] and _epi("EP8")["status"] == "HELD_BY_OWNER" and _row(row["id"])["status"] == "OPEN"
    setting(*lift)
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out == f"approved: EP8 publishes at {slot}" and _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)], (out, sched)
    assert _row(row["id"])["status"] == "ANSWERED"


def test_the_silence_road_reads_the_same_two_locks(monkeypatch, setting):
    """RUL-U1g 4: `clear_to_post` asks `_channel_lock` - its two whys unchanged, in the same order: one function for both roads."""
    real = LA.uploads_open
    _ep8(monkeypatch, setting)
    assert CON.clear_to_post("EP8") == (True, "every check passed")
    setting("PAUSED", "TRUE"); assert CON.clear_to_post("EP8") == (False, "the pipeline is paused")
    setting("PAUSED", "FALSE"); setting("PAUSED_UNTIL", core.iso(core.now_utc() + dt.timedelta(hours=1))); assert CON.clear_to_post("EP8") == (False, "the pipeline is paused")
    setting("PAUSED_UNTIL", ""); monkeypatch.setattr(LA, "uploads_open", real); setting("UPLOAD_LOCK", "on")
    assert CON.clear_to_post("EP8") == (False, "uploads are not confirmed open yet")


@pytest.mark.parametrize("lock", ["paused", "paused_until", "upload_lock"])
def test_the_review_cards_approve_under_a_channel_lock_schedules_nothing_and_stays_open(lock, monkeypatch, setting):
    """RUL-U1h 2: a film AWAITING_APPROVAL with its review card, a channel lock on - his Approve on the card sends nothing to YouTube, the film keeps
    its status, the row is OPEN again with no answer and he reads which lock; the lock lifted, the SAME row tapped again schedules it. His Hold on a
    review card under the same lock holds its film (a "no" reads no lock). (`_ep8` stubs the uploads open: the uploads case puts the real
    `launch.uploads_open` back, so the UPLOAD_LOCK cell decides.)"""
    real = LA.uploads_open
    slot, _s8 = _ep8(monkeypatch, setting); slot9, sched = _ep8(monkeypatch, setting, ep="EP9", hours=50.0)      # the last stub records every yt_schedule
    CON.await_approval("EP8", "ytEP8", slot, "'Title EP8'."); CON.await_approval("EP9", "ytEP9", slot9, "'Title EP9'.")
    card = lambda ep: next(r for r in core.store().rows("Owner_Actions") if r.get("kind") == "creative_review" and r.get("episode_id") == ep)
    if lock == "paused": setting("PAUSED", "TRUE"); why, lift = "the pipeline is paused", ("PAUSED", "FALSE")
    elif lock == "paused_until": setting("PAUSED_UNTIL", "2099-01-01T00:00:00Z"); why, lift = "the pipeline is paused", ("PAUSED_UNTIL", "")
    else: monkeypatch.setattr(LA, "uploads_open", real); setting("UPLOAD_LOCK", "on"); why, lift = "uploads are not confirmed open yet", ("UPLOAD_LOCK", "off")
    row = card("EP8"); out = NT.answer(row["id"], "APPROVE EP8")
    assert out == f"Title EP8 was NOT approved: {why}. Nothing was sent to YouTube. Your Approve stays open: tap it again once that is lifted.", out
    assert sched == [] and _epi("EP8")["status"] == "AWAITING_APPROVAL", (sched, _epi("EP8"))
    assert _row(row["id"])["status"] == "OPEN" and _row(row["id"])["answer"] == "", _row(row["id"])
    NT.answer(card("EP9")["id"], "HOLDREVIEW EP9")
    assert _epi("EP9")["status"] == "HELD_BY_OWNER" and sched == [], (_epi("EP9"), sched)
    setting(*lift)
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out.startswith("approved: ") and _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)], (out, sched)


def test_a_raise_of_his_approve_after_a_take_down_is_logged(monkeypatch, setting):
    """CR-U1FIX_2 (3): `approve` raising under his Approve after a take-down is a WARN line of the log with the raise - never words alone (it may
    have reached YouTube before it raised; the words he reads then say what YouTube holds - RULINGS_U2i 7a, the test after this one)."""
    _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: (_ for _ in ()).throw(RuntimeError("reschedule failed 403")))
    said = []; monkeypatch.setattr(CON, "log", lambda msg, level="INFO", episode=None, public=None: said.append((msg, level, episode)))
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out.startswith("Title EP8 could NOT be put back on the schedule: RuntimeError: reschedule failed 403"), out
    assert ("his Approve after a take-down raised: RuntimeError: reschedule failed 403", "WARN", "EP8") in said, said


HELD_AT = "2026-12-01T15:00:00Z"
SAID_A = "Title EP8 could NOT be put back on the schedule: {why}. Set it in YouTube Studio."
SAID_B = ("Title EP8: YouTube already holds the time " + HELD_AT + " for it, but our own record was not written (RuntimeError: reschedule failed 403). "
          "Your Approve stays open: tap it again to finish it.")
SAID_C = ("Title EP8 may or may not be back on the schedule: RuntimeError: reschedule failed 403, and YouTube could not be read just now. "
          "Your Approve stays open: tap it again.")


@pytest.mark.parametrize("case", ["held", "not_held", "unreadable_raises", "unreadable_empty", "answered", "public_with_time"])
def test_his_approve_that_raises_says_what_youtube_holds(case, monkeypatch, setting):
    """RULINGS_U2i 7a: after a raise of `approve` the words are told by one read-back of what YouTube holds - B when the private video shows a time
    (never "could NOT"), A when it shows none, C when YouTube cannot be read; an `approve` that ANSWERED without "approved" sent nothing, so A
    with no read-back at all. In every case the row stays open, the video HELD_BY_OWNER, and the second tap (approve restored) closes the row."""
    _ep8(monkeypatch, setting, status="SCHEDULED"); _yt(monkeypatch)
    CON.unpost("EP8"); row = _offers()[0]
    good_schedule, good_approve, reads = PUB.yt_schedule, CON.approve, []
    def read(vid):
        reads.append(vid)
        if case == "public_with_time": return {"privacyStatus": "public", "publishAt": HELD_AT}
        if case == "held": return {"privacyStatus": "private", "publishAt": HELD_AT}
        if case == "unreadable_raises": raise RuntimeError("quota exceeded")
        return {} if case == "unreadable_empty" else {"privacyStatus": "private"}
    monkeypatch.setattr(PUB, "yt_status_full", read)
    if case == "answered": monkeypatch.setattr(CON, "approve", lambda ep: "no free slot found")
    else: monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: (_ for _ in ()).throw(RuntimeError("reschedule failed 403")))
    said = []; monkeypatch.setattr(CON, "log", lambda msg, level="INFO", episode=None, public=None: said.append((msg, level, episode)))      # the same spy as line 187
    out = NT.answer(row["id"], "APPROVE EP8")
    want = {"held": SAID_B, "not_held": SAID_A.format(why="RuntimeError: reschedule failed 403"), "unreadable_raises": SAID_C, "unreadable_empty": SAID_C,
            "answered": SAID_A.format(why="no free slot found"),
            "public_with_time": SAID_A.format(why="RuntimeError: reschedule failed 403")}[case]
    assert out == want, out
    assert ("could NOT" in out) == (case in ("not_held", "answered", "public_with_time")), out
    assert "YouTube already holds" not in out or case == "held", out
    assert reads == ([] if case == "answered" else ["ytEP8"]), reads
    assert _row(row["id"])["status"] == "OPEN" and _epi("EP8")["status"] == "HELD_BY_OWNER"
    kept = [m for m, lv, e in said if "our record still says HELD_BY_OWNER" in m and lv == "WARN" and e == "EP8"]
    assert len(kept) == (0 if case in ("not_held", "answered") else 1) and (case not in ("held", "public_with_time") or HELD_AT in kept[0]), (case, said)
    monkeypatch.setattr(PUB, "yt_schedule", good_schedule); monkeypatch.setattr(CON, "approve", good_approve)
    out = NT.answer(row["id"], "APPROVE EP8")
    assert out.startswith("approved: EP8 publishes at "), out
    assert _row(row["id"])["status"] == "ANSWERED" and _epi("EP8")["status"] == "SCHEDULED"
