"""U1 fix 237 (B-OWNER audit J19-3, HELD): ONE KEPT INPUT WHOSE HANDLING RAISES AT EVERY RUN NO LONGER BLOCKS EVERY LATER ONE FOR GOOD. The drain counts
the tries of a kept key (cell DASH_DRAIN_TRIES); a failure stops the drain twice (his order stands), at the third the drain passes it - it stays KEPT
in KV, never deleted unhandled - handles the later ones, and ONE alarm names its key (never a word of his). U1 J 237 (RUL-U1): the
alarm tells him the one thing he can do - send it again in other words - and keeps the key and the error's name for whoever repairs it.
RUL-U1b (CODEREVIEW_PRE-P_1 findings 2-4): the one alarm is OWED until it is sent (the count reaches DRAIN_TRIES only on a sent alarm); once told,
the stored count stops there and the cell is not written again; the cell is read into numbers once, so a hand-edited cell never stops the drain;
the alarm is its own kind `input_unread` ("A message was not read"), never "Production stopped"."""
import json
import pytest
from whatifs import core, dash as DS, notify as NT
from tests.test_v12_owner_face import _inbox


def _alarms(): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "input_unread"]


def _a_bad_key(monkeypatch, setting):
    """The planted inbox: X1 raises at every run, Y1 (a PAUSE) is the later one; returns the KV stand-in."""
    kept, KV = _inbox(monkeypatch); setting("TWO_SCREENS_ON", "TRUE")
    bad = {"id": "X1", "verb": "INPUT", "text": "my secret words", "ts": 1_000_000, "src": "dash"}
    later = {"id": "Y1", "verb": "PAUSE", "ts": 2_000_000, "src": "dash"}
    kv = KV({"inbox:x-bad": kept(bad), "inbox:y-later": kept(later)})
    real = DS.handle_action
    def raises_on_x1(val):
        if "X1" in json.dumps(DS.decrypt(json.loads(val))): raise ValueError("planted: always raises")
        return real(val)
    monkeypatch.setattr(DS, "handle_action", raises_on_x1)
    return kv


def _cell(): return json.loads(core.S("DASH_DRAIN_TRIES") or "{}")


def test_the_one_alarm_is_owed_until_it_is_sent(monkeypatch, setting):
    """U1b finding 2: the sending of the alarm fails at the third run -> no row, the later key handled, the count stays below DRAIN_TRIES; the
    fourth run sends it; never a second row after."""
    kv = _a_bad_key(monkeypatch, setting); real_send, down = NT.send, [False]
    def send(kind, *a, **k):
        if down[0] and kind == "input_unread": raise TimeoutError("planted: the sending failed")
        return real_send(kind, *a, **k)
    monkeypatch.setattr(NT, "send", send)
    assert DS.drain(kv) == 0 and DS.drain(kv) == 0 and _alarms() == []
    down[0] = True
    assert DS.drain(kv) == 1 and set(kv.d) == {"inbox:x-bad"} and _alarms() == []                  # run 3: passed, the later one handled, the alarm NOT sent
    assert _cell() == {"inbox:x-bad": DS.DRAIN_TRIES - 1}, _cell()                                   # owed: the count stays below DRAIN_TRIES
    down[0] = False
    assert DS.drain(kv) == 0 and len(_alarms()) == 1 and _cell() == {"inbox:x-bad": DS.DRAIN_TRIES}      # run 4: the owed alarm is sent, once
    assert DS.drain(kv) == 0 and DS.drain(kv) == 0 and len(_alarms()) == 1 and set(kv.d) == {"inbox:x-bad"}      # runs 5, 6: still one row, still kept


def test_once_told_the_cell_is_not_written_again(monkeypatch, setting):
    """U1b finding 3 (i): after the alarm the stored count never passes DRAIN_TRIES - two more drains with the key still kept leave the cell's text
    unchanged and call set_setting 0 times (one Sheet write at every tick for 30 days was waste)."""
    kv = _a_bad_key(monkeypatch, setting)
    for _ in range(3): DS.drain(kv)
    assert len(_alarms()) == 1; text, writes = core.S("DASH_DRAIN_TRIES"), []
    real_set = DS.set_setting
    monkeypatch.setattr(DS, "set_setting", lambda *a, **k: (writes.append(a), real_set(*a, **k))[1])
    assert DS.drain(kv) == 0 and DS.drain(kv) == 0 and set(kv.d) == {"inbox:x-bad"}
    assert core.S("DASH_DRAIN_TRIES") == text and writes == [] and len(_alarms()) == 1, (text, core.S("DASH_DRAIN_TRIES"), writes)


@pytest.mark.parametrize("hand", ["x", 9], ids=["not_a_number", "past_the_cap"])
def test_a_hand_edited_cell_never_stops_the_drain(monkeypatch, setting, hand):
    """U1b finding 3 (ii): the cell is read into numbers once, where it is loaded - a value that is not a whole number from 1 to DRAIN_TRIES counts
    as 0. The drain returns a number, raises nothing, and treats the key as at its first try (his order stands: the later one waits)."""
    kv = _a_bad_key(monkeypatch, setting); setting("DASH_DRAIN_TRIES", json.dumps({"inbox:x-bad": hand}))
    n = DS.drain(kv)
    assert n == 0 and set(kv.d) == {"inbox:x-bad", "inbox:y-later"} and _cell() == {"inbox:x-bad": 1} and _alarms() == [], (n, _cell())


def test_a_key_that_always_raises_is_passed_at_the_third_try_and_named_once(monkeypatch, setting):
    kept, KV = _inbox(monkeypatch); setting("TWO_SCREENS_ON", "TRUE")
    bad = {"id": "X1", "verb": "INPUT", "text": "my secret words", "ts": 1_000_000, "src": "dash"}
    later = {"id": "Y1", "verb": "PAUSE", "ts": 2_000_000, "src": "dash"}
    kv = KV({"inbox:x-bad": kept(bad), "inbox:y-later": kept(later)})
    real = DS.handle_action
    def raises_on_x1(val):
        if "X1" in json.dumps(DS.decrypt(json.loads(val))): raise ValueError("planted: always raises")
        return real(val)
    monkeypatch.setattr(DS, "handle_action", raises_on_x1)
    assert DS.drain(kv) == 0 and set(kv.d) == {"inbox:x-bad", "inbox:y-later"}                  # try 1: his order stands, the later one waits
    assert DS.drain(kv) == 0 and set(kv.d) == {"inbox:x-bad", "inbox:y-later"}                  # try 2
    assert _alarms() == []
    assert DS.drain(kv) == 1 and set(kv.d) == {"inbox:x-bad"}                                   # try 3: passed (kept), the later one handled
    assert core.S("PAUSED", bool) is True
    a = _alarms(); assert len(a) == 1 and "inbox:x-bad" in a[0]["text"] and "my secret words" not in a[0]["text"], a
    assert a[0]["text"] == ("One message you sent could not be read by the pipeline three runs in a row. It is kept, not lost, and your later messages are "
                            "handled. If it mattered today, send it again in other words. (inbox:x-bad, ValueError)"), a[0]["text"]      # U1 J 237: the one thing he can do
    assert a[0]["kind"] == "input_unread" and a[0]["dedupe_key"] == "input_unread|inbox:x-bad", (a[0]["kind"], a[0]["dedupe_key"])      # U1b finding 4: its own kind
    assert NT.NAMES[a[0]["kind"]] == "A message was not read" and NT.klass(a[0]["kind"]) == NT.ALARM and NT.name(a[0]["kind"]) != "Production stopped"
    assert not [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "pipeline_stop"]                                   # never "Production stopped"
    assert DS.drain(kv) == 0 and set(kv.d) == {"inbox:x-bad"} and len(_alarms()) == 1              # a fourth run: still kept, never a second alarm


def test_a_key_that_heals_clears_its_count(monkeypatch, setting):
    kept, KV = _inbox(monkeypatch); setting("TWO_SCREENS_ON", "TRUE")
    p = {"id": "P7", "verb": "PAUSE", "ts": 1_000_000, "src": "dash"}
    kv = KV({"inbox:p7": kept(p)}); real, calls = DS.handle_action, []
    def once_down(val):
        calls.append(1)
        if len(calls) <= 2: raise TimeoutError("the sheet did not answer")
        return real(val)
    monkeypatch.setattr(DS, "handle_action", once_down)
    assert DS.drain(kv) == 0 and DS.drain(kv) == 0 and DS.drain(kv) == 1 and kv.d == {}             # healed at the third run: handled, not passed
    assert _alarms() == [] and "inbox:p7" not in (core.S("DASH_DRAIN_TRIES") or "")
