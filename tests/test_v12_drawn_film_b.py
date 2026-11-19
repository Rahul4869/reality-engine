"""v12 DRAWN BY CODE (D6): the master's half of whole productions in the drawn arm - the audit repairs, the check drawn_shown catches a lying record (split from test_v12_drawn_film.py: one file under the minitest's 450 s, ruling 4 (E))."""
import os, shutil
from whatifs import core, scenes as SCN
from tests.test_v12_drawn_film import _setup, _ledger          # the same productions' clock (2031-03-08) and helpers: these two tests keep minutes 2 and 3


# ------------------------------------------------------------------ 11. the master's half: the audit repairs, the check catches a lying record
def test_the_audit_sends_an_unreadable_scene_to_its_still_before_the_gate(monkeypatch, setting):
    from whatifs import episode as EP
    slot, ep, jobs = _setup(monkeypatch, setting, minute=2); setting("DRAWN_INK_MIN", "50")             # no text can reach 50 to 1: every drawn state is sent back
    try:
        r = EP.produce(slot); assert r["ok"], r
        assert not any(m.get("drawn") for m in jobs[-1].segmeta) and _ledger()["drawn_shown"][0] == "PASS", _ledger()
        assert "on the finished file" in _ledger()["drawn_shown"][1]
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)


def test_check_drawn_shown_holds_a_film_whose_record_says_drawn_but_the_master_cannot_be_read(monkeypatch, setting):
    from whatifs import episode as EP
    slot, ep, jobs = _setup(monkeypatch, setting, minute=3); setting("DRAWN_INK_MIN", "50")
    monkeypatch.setattr(SCN, "audit", lambda master, job: [])                                            # the audit switched out of the way: the record lies
    try:
        r = EP.produce(slot)
        assert not r.get("ok") and _ledger()["drawn_shown"][0] == "FAIL", (r, _ledger())
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
