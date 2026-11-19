"""v12 DRAWN BY CODE (D6): the master's half of whole productions in the drawn arm - the audit repairs, the check drawn_shown catches a lying record (split from test_v12_drawn_film.py: one file under the minitest's 450 s, ruling 4 (E))."""
import os, shutil
from whatifs import core, scenes as SCN
from tests.test_v12_drawn_film import _setup, _ledger, _seg_i          # the same productions' clock (2031-03-08) and helpers: these two tests keep minutes 2 and 3


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


# ------------------------------------------------------------------ F-12: a scene whose later piece failed is never measured half-built
def test_a_scene_whose_second_piece_failed_is_its_still_never_measured_half_built(monkeypatch, setting):
    import whatifs.shotplan as SP
    from whatifs import episode as EP, render as RN
    slot, ep, jobs = _setup(monkeypatch, setting, minute=4); calls = {}
    real_pf = SP.pieces_for
    monkeypatch.setattr(SP, "pieces_for", lambda dur, kind, *a, **k: 2 if kind == "graphic" else real_pf(dur, kind, *a, **k))      # _render imports the name from whatifs.shotplan at its call
    real_d = RN.drawn_segment
    def spy(L, bg, path, nf, start, total):
        i = _seg_i(path)[0]; calls.setdefault(i, []).append((start, total))
        if i == min(calls) and len(calls[i]) == 2: raise RuntimeError("planted encoder fault on the second piece")
        return real_d(L, bg, path, nf, start, total)
    monkeypatch.setattr(RN, "drawn_segment", spy)
    try:
        r = EP.produce(slot); assert r["ok"], r
        job = jobs[-1]; assert calls, "this id's film drew no scene"
        i0 = min(calls); st = calls[i0]
        assert len(st) == 2 and st[0][0] == 0 and st[1][0] == int(st[0][1] * 1 / 2) and len({t for _, t in st}) == 1, calls          # its starts are [0, cut1] with one total
        assert not any(m.get("drawn") for m in job.segmeta if m["i"] == i0) and job.drawn[i0]["why"].startswith("the render failed"), (job.drawn[i0], [m for m in job.segmeta if m["i"] == i0])
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
