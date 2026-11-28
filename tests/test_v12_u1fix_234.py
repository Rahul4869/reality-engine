"""U1 J 234 (#268): THE OWNER ROAD'S COUNTS ARE THOSE OF THE TWO PLANTED TICKS. `tools/sweep.py::screens_of` counted every morning and needs row of the
Sheet, so its printed numbers hung on the clock of the run ("2 morning, 1 needs" at 14:50 India time, "2 morning, 2 needs" at 18:12, same code), and a
morning message of the RUN's own tick could stand in for a planted tick that sent nothing. It now counts by difference around its own two planted
ticks, keeps the counts for the walked id, and judges a second walk by them. RUL-U1g 3: the totals stand in ("(already walked)") only when the Sheet's own stamps,
read before the planted ticks, already name the planted day; two planted ticks that send nothing on a first walk are BAD."""
import datetime as dt
import pytest
from whatifs import core, notify as NT, digests as DG
from tools import sweep as SW
from tests.test_v12_owner import _wire, _window, _mailbox

WORDS = "the owner's road held: 2 rows, all registered; WhatsApp, by the two planted ticks: 1 morning, 1 needs; 0 alarm in the run"
NO_NEEDS = "no \"Needs you\" list went out at the planted 18:05 with a decision open"
BOTH = "no morning message went out at the planted 09:05; " + NO_NEEDS


def _run_at(monkeypatch, setting, hh, mm):
    """A run's Sheet at hh:mm India time on Wed 18 Nov 2026: a decision of the run is open and the run's own tick has run (as a run does)."""
    T = dt.datetime(2026, 11, 18, hh, mm, tzinfo=NT.IST)
    monkeypatch.setattr(core, "now_utc", lambda: T.astimezone(dt.timezone.utc))      # the clock the sweep reads to plant the next India day
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _mailbox(monkeypatch); _window(False)
    NT.send("bakeoff", "A decision of the run.", [("Pick A", "PICK A")], episode="EP234", default="A is used", expires_h=72, dedupe_key="run|EP234")
    DG.tick(now=T); DG.needs_tick(now=T)
    return bodies


def _sent(kind): return sum(1 for r in core.store().rows("WA_Outbox") if r.get("kind") == kind and r.get("wamid"))


@pytest.mark.parametrize("hh,mm", [(14, 50), (18, 20)], ids=["1450_IST", "1820_IST"])
def test_the_words_are_the_same_at_any_hour_of_the_run_and_a_second_walk_repeats_them(hh, mm, monkeypatch, setting):
    bodies = _run_at(monkeypatch, setting, hh, mm)
    run_needs = _sent("needs"); assert _sent("morning") == 1 and run_needs == (1 if hh >= 18 else 0)      # the run's own messages are there
    assert SW.screens_of(core, ["EP234"]) == (True, WORDS)
    n = len(bodies)
    assert SW.screens_of(core, ["EP234"]) == (True, WORDS) and len(bodies) == n                   # walked again: the same words, nothing sent
    SW._WALKED.clear()                                                                            # another process walks it: the totals, said so
    ok, words = SW.screens_of(core, ["EP234"])
    assert ok and words.endswith(" (already walked)") and f"{1 + 1} morning, {1 + run_needs} needs" in words and len(bodies) == n, words


def test_a_planted_evening_tick_that_sent_nothing_is_bad_though_the_run_sent_its_own_list(monkeypatch, setting):
    _run_at(monkeypatch, setting, 18, 20)
    assert _sent("needs") == 1                                                                    # the run's own evening list is in WA_Outbox
    monkeypatch.setattr(DG, "needs_tick", lambda now=None: False)                                 # the planted 18:05 sends nothing
    assert SW.screens_of(core, ["EP234"]) == (False, NO_NEEDS)
    assert SW.screens_of(core, ["EP234"]) == (False, NO_NEEDS)                                    # the second walk judges the first walk's counts


def test_a_first_walk_whose_two_planted_ticks_send_nothing_is_bad(monkeypatch, setting):
    _run_at(monkeypatch, setting, 18, 20)
    assert _sent("morning") == 1 and _sent("needs") == 1                                         # the run's own morning and evening messages are there
    monkeypatch.setattr(DG, "tick", lambda now=None: None); monkeypatch.setattr(DG, "needs_tick", lambda now=None: False)      # both planted ticks send nothing
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)                                        # walked again: still BAD (nothing kept would judge it by its difference too); the kept-zero pin is the second walk of test_planted_ticks_that_stamp_the_day_and_send_nothing_are_bad (break U1d-2a)


def test_a_later_walk_that_sends_never_turns_a_bad_first_walk_good(monkeypatch, setting):
    _run_at(monkeypatch, setting, 18, 20)
    tick, needs = DG.tick, DG.needs_tick
    monkeypatch.setattr(DG, "tick", lambda now=None: None); monkeypatch.setattr(DG, "needs_tick", lambda now=None: False)      # the first walk: both planted ticks send nothing
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)
    monkeypatch.setattr(DG, "tick", tick); monkeypatch.setattr(DG, "needs_tick", needs)                                         # the real ticks back: this walk's planted ticks send
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)                                                                      # the first walk's BAD stands
    assert _sent("morning") == 2 and _sent("needs") == 2                                                                        # not vacuous: the second walk's ticks really sent


def test_planted_ticks_that_stamp_the_day_and_send_nothing_are_bad(monkeypatch, setting):
    _run_at(monkeypatch, setting, 18, 20)
    monkeypatch.setattr(DG, "tick", lambda now=None: core.set_setting("DIGEST_DAILY_SENT", now.astimezone(NT.IST).date().isoformat()))
    monkeypatch.setattr(DG, "needs_tick", lambda now=None: core.set_setting("NEEDS_SENT", now.astimezone(NT.IST).date().isoformat()) or True)
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)                                        # a tick that stamps and sends nothing never vouches for itself
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)                                        # walked again: its own stamps never pass it "(already walked)" (CR-U1FIX_2 (2))


def test_one_stamp_of_the_planted_day_does_not_vouch_for_a_walk(monkeypatch, setting):
    """CR-U1FIX_2 (2), test gap: BOTH stamps must name the planted day before the walk. Only DIGEST_DAILY_SENT naming it, and two planted ticks
    that send nothing: a first walk judged by its difference - BAD, never the Sheet's totals "(already walked)"."""
    _run_at(monkeypatch, setting, 18, 20)
    core.set_setting("DIGEST_DAILY_SENT", "2026-11-19")                                          # the planted day (the next India day); NEEDS_SENT names the run's own day
    monkeypatch.setattr(DG, "tick", lambda now=None: None); monkeypatch.setattr(DG, "needs_tick", lambda now=None: False)
    assert SW.screens_of(core, ["EP234"]) == (False, BOTH)


def test_what_a_walk_keeps_is_kept_for_its_own_sheet_only(monkeypatch, setting, tmp_path):
    """CR-U1FIX_2 (2), test gap: the Sheet is part of what `_WALKED` keeps - the same id walked on another Sheet whose two planted ticks send
    nothing is BAD, never the first Sheet's counts."""
    _run_at(monkeypatch, setting, 18, 20)
    assert SW.screens_of(core, ["EP234"]) == (True, WORDS)
    other = core.LocalStore(str(tmp_path / "another_sheet.json")); other.ensure_tabs(); monkeypatch.setattr(core, "_store", other)
    monkeypatch.setattr(DG, "tick", lambda now=None: None); monkeypatch.setattr(DG, "needs_tick", lambda now=None: False)
    ok, words = SW.screens_of(core, ["EP234"])
    assert ok is False and BOTH in words and "(already walked)" not in words, words
