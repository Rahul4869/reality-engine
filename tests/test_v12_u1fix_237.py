"""U1 fix 237 (B-OWNER audit J19-3, HELD): ONE KEPT INPUT WHOSE HANDLING RAISES AT EVERY RUN NO LONGER BLOCKS EVERY LATER ONE FOR GOOD. The drain counts
the tries of a kept key (cell DASH_DRAIN_TRIES); a failure stops the drain twice (his order stands), at the third the drain passes it - it stays KEPT
in KV, never deleted unhandled - handles the later ones, and ONE pipeline_stop alarm names its key (never a word of his)."""
import json
from whatifs import core, dash as DS
from tests.test_v12_owner_face import _inbox


def _alarms(): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "pipeline_stop"]


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
