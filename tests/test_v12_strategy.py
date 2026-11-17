"""v12 V4 - the CEO and the ladder: the scoreboard, finance wired, the loop of decisions, the rule book, the watch book, the arm book, one rule
for a breakout, the owner's desk. Every rule is proven both ways; the real code path is run, so an unwired call is seen."""
import json, os
import pytest
from whatifs import core, contract as CON, episode as EP
from whatifs.org import runner as RUN, layman as LAY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()

# ------------------------------------------------------------------ step 0: open issue 200 (the organisation off loses a native run's result)
TITLE = "What If Your Reflection Was One Second Late?"
GOOD = "You stop brushing your teeth. Your reflection does not. It is one second late, and it is looking straight at you."
def U(opening): return [{"start": 0.0, "end": 9.0, "text": opening}, {"start": 41.0, "end": 45.0, "text": "By noon the whole town has noticed."}]

def test_with_the_organisation_off_a_native_run_hands_back_its_output_and_a_plain_run_its_value(setting):
    setting("ORG_ON", "FALSE"); assert not RUN.on()
    assert RUN.work("D4", "write", "EP1", lambda b: RUN.Out({"a": 1})) == {"a": 1}                  # a native run: its output, not the Out object
    assert RUN.work("D4", "write", "EP1", lambda b: {"a": 2}) == {"a": 2}                           # a plain run: its value, unchanged
    r = RUN.run("D4", "write", lambda b: RUN.Out([3], memos=[{"x": 1}])); assert r.status == "off" and r.output == [3]

def test_with_the_organisation_off_the_promise_line_up_is_judged_not_lost(setting):
    setting("ORG_ON", "FALSE")
    s0 = {"pkg": {"titles": [TITLE]}, "d": {}, "room": {"script": {"script": GOOD}}}
    p = EP._probe(s0, "EP1", U(GOOD)); assert isinstance(p, dict) and p["status"] == "pass", p                # D13's probe as the plan stage runs it
    assert CON.p_viewer_probe({"probe": p})[0] == CON.PASS                                                  # judged with the organisation off - not N/A

# ------------------------------------------------------------------ step 1: the scoreboard (whatifs/scoreboard.py, tab Scoreboard)
import datetime as dt
from whatifs import scoreboard as SB, digests as DG, notify as NT, owner_view as OV, governor as G, truth as TRU

SB_NOW = dt.datetime(2026, 11, 16, 4, 0, tzinfo=dt.timezone.utc)
WORKED = ("Scoreboard: 40 of 1,000 subscribers (about 960 days at this pace) | Shorts views that count: 200,000 of 10,000,000 in 90 days - 2,222 a day,"
          " the bar needs 111,111 | long watch hours: 12.5 of 4,000 in 12 months - 0.03 a day, the bar needs 11.0. The bars rise on 01 Feb 2027: 8,000 hours"
          " or 20,000,000 Shorts views.")
def plant(*rows): core.store().append("Scoreboard", [dict({"hours": 12.5, "shorts_90": 200000, "src": "test"}, **r) for r in rows])

def test_the_scoreboard_line_is_the_partner_programs_own_numbers_word_for_word(setting):
    setting("STRATEGY_ON", "TRUE")
    assert SB.line(SB_NOW) == "Scoreboard: no reading yet (the first comes with the daily learning job)."
    plant({"date": "2026-10-19", "subs": 12}, {"date": "2026-11-16", "subs": 40})
    assert SB.sub_pace(SB._rows(), SB_NOW) == 1.0 and SB.eta(40, 1000, 1.0) == 960 and SB.eta(1000, 1000, None) == 0 and SB.eta(5, 1000, 0) is None
    assert SB.line(SB_NOW) == WORKED
    setting("SCOREBOARD_ELIGIBLE_PCT", "80"); assert "the bar needs 11.0 (counted at 80% eligible). The bars rise on 01 Feb 2027" in SB.line(SB_NOW)

@pytest.mark.parametrize("old, today, says", [
    (None, 40, "40 of 1,000 subscribers (no pace yet: 28 days of readings are needed)"),
    (12, 1000, "1000 of 1,000 subscribers (reached)"),
    (12, 13, "13 of 1,000 subscribers (more than 10 years at this pace)"),               # 987 / (1/28) = 27,636 days
    (12, 12, "12 of 1,000 subscribers (more than 10 years at this pace)"),               # no pace up: the bar is never reached at this pace
    (12, "", "Scoreboard: subscribers: no reading | Shorts views that count"),
])
def test_each_pace_is_said_as_it_is(setting, old, today, says):
    setting("STRATEGY_ON", "TRUE")
    plant(*([{"date": "2026-10-19", "subs": old}] if old is not None else []), {"date": "2026-11-16", "subs": today})
    assert says in SB.line(SB_NOW), SB.line(SB_NOW)

def test_the_bars_are_data_and_the_rise_is_said_until_it_comes(setting):
    setting("STRATEGY_ON", "TRUE"); plant({"date": "2027-02-01", "subs": 40})
    after = SB.line(dt.datetime(2027, 2, 1, 4, 0, tzinfo=dt.timezone.utc))
    assert "of 8,000 in 12 months" in after and "of 20,000,000 in 90 days" in after and "The bars rise" not in after and after.endswith("the bar needs 21.9.")
    setting("YPP_BARS", json.dumps([{"until": "", "subs": 500, "hours": 3000, "shorts": 3000000}]))
    assert "40 of 500 subscribers" in SB.line(SB_NOW) and "of 3,000 in 12 months" in SB.line(SB_NOW)

def test_one_reading_a_day_kept_by_the_daily_learning_job(setting):
    from whatifs import manage as MG
    MG.learn(); assert core.store().rows("Scoreboard") == []                                  # STRATEGY_ON FALSE: exactly the code V4 is built on
    setting("STRATEGY_ON", "TRUE"); MG.learn()
    rows = core.store().rows("Scoreboard"); assert [r["date"] for r in rows] == [core.now_utc().date().isoformat()] and rows[0]["subs"] == ""   # fake mode: no subscriber reading
    assert SB.keep() is None and len(core.store().rows("Scoreboard")) == 1                    # a second call on that date changes nothing
    assert SB.keep(core.now_utc() + dt.timedelta(days=1))["date"] == (core.now_utc() + dt.timedelta(days=1)).date().isoformat()

def test_the_scoreboard_is_the_first_thing_after_the_head_of_both_briefs(monkeypatch, setting):
    from whatifs import publish as PUB
    setting("STRATEGY_ON", "TRUE"); plant({"date": "2026-10-19", "subs": 12}, {"date": "2026-11-16", "subs": 40})
    for kind in ("daily", "weekly"):
        for demo in (False, True):
            parts = DG.compose(kind, demo=demo, now=SB_NOW)[0].split("\n\n")
            assert parts[0].startswith("*") and ("Morning brief" in parts[0] or "Weekly brief" in parts[0]) and parts[1] == WORKED, (kind, demo, parts[:2])
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, html, *a, **k: (mails.append(html), True)[1])
    assert NT.digest(now=SB_NOW, force=True) and mails[0].startswith("<p>" + WORKED + "</p><p><b>Mode:</b>")
    setting("STRATEGY_ON", "FALSE"); mails.clear()
    assert DG.compose("daily", now=SB_NOW)[0].split("\n\n")[1] != WORKED and NT.digest(now=SB_NOW, force=True) and mails[0].startswith("<p><b>Mode:</b>")

def test_the_stale_shorts_sentence_is_retired_and_the_money_shows_the_cap_in_force(monkeypatch, setting):
    monkeypatch.setattr(OV, "today", lambda: {"next_slot": {"ist": "Tue 18 Nov 18:00"}})
    assert OV.strategy()["plan"][0] == "Next slot Tue 18 Nov 18:00: a long video about the Short viewers picked (three Shorts a week, each a topic of its own)."
    assert "shorts_cut_from_it" in [r["id"] for r in TRU.hits("Next slot Tue: long video, then 2-4 Shorts cut from it over the next days.", "docs")]
    setting("BUDGET_CEILING_INR", "9000"); setting("BUDGET_FLOOR_INR", "6000")
    assert OV.money()["cap"] == int(round(G.cap_inr())) != 9000                               # the cap in force (no revenue in a fresh store), not the ceiling cell
