"""U1 J 231 (#265): CC-3'S BREAK SEEN AT THE ROW. The held Short's card is sent by `shorts2` with `expires_h=None if two else 72`; at the row that None
and `notify._shape`'s rule (a HOLD carries no expiry) are the same thing, so only a spy saw CC-3 (tests/test_v12_owner.py
test_the_held_short_still_waits, unchanged). The caller's None exists for the day `_shape`'s rule changes: this test makes that day happen - `_shape`
returns the CALLER's expiry for a HOLD - and looks at the row: with the switch on it has NO expiry and is still OPEN 30 days later; with the switch off
it has one (today's card). No product line changes."""
import datetime as dt
from whatifs import core, notify as NT
from tests.test_v12_owner import _short8, _cards8, _row

GF = {"ok": False, "failed": [("short_sound", "the first sound comes at 0.4 s")]}


def _register_rule_out_of_the_way(monkeypatch):
    real = NT._shape
    def shape(kind, episode, buttons, default, expires_h, dedupe_key):
        b, d, e, k = real(kind, episode, buttons, default, expires_h, dedupe_key)
        return b, d, (expires_h if NT.klass(kind) == NT.HOLD else e), k      # a HOLD keeps whatever its caller gave
    monkeypatch.setattr(NT, "_shape", shape)


def test_the_held_shorts_own_none_keeps_its_row_open_without_the_registers_rule(monkeypatch, setting):
    SH, SP, sid, posted = _short8(monkeypatch, setting)
    _register_rule_out_of_the_way(monkeypatch)
    assert NT._shape("special_review", sid, [("Post", "x")], "d", 72, "k")[2] == 72          # the rule is out of the way: a HOLD's expiry is the caller's
    SH._file_hold({"id": sid, "file": "drive:f8c"}, GF, True)
    c = _cards8(sid); assert len(c) == 1 and c[0]["kind"] == "special_review" and NT.klass(c[0]["kind"]) == NT.HOLD, c
    assert not c[0]["expires_at"], c[0]["expires_at"]
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(days=30))
    assert _row(c[0]["id"])["status"] == "OPEN" and SP.ready_sweep() == 0 and posted == []
    SH2, _SP2, sid2, _p2 = _short8(monkeypatch, setting, on="FALSE", sid="SH209911200901")         # the switch off: today's card, with its expiry
    SH2._file_hold({"id": sid2}, GF, True)
    o = _cards8(sid2)[0]; assert o["default_action"] == "not posted" and o["expires_at"], o
