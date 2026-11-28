"""U1 fix 206 (open issue 234): THE BRIEF'S "no change" LINE SAYS WHEN THE REVIEW IS STALE. Strategy's word of the day (STRATEGY_TODAY, its "at") older
than STRATEGY_STALE_H hours is said to be stale, with its age - the same rule as check strategy_live; a review inside the limit keeps the old words."""
import datetime as dt, json
from whatifs import core
from whatifs.org import strategy as STR

NOW = dt.datetime(2031, 5, 6, 3, 0, tzinfo=dt.timezone.utc)


def _today(setting, hours_ago, refused=()):
    setting("STRATEGY_TODAY", json.dumps({"at": core.iso(NOW - dt.timedelta(hours=hours_ago)), "refused": list(refused), "counting": []}))


def _judged(setting):
    """U1b finding 9: the conditions under which check strategy_live judges the review's age - and the channel not paused."""
    setting("STRATEGY_ON", "TRUE"); setting("STRATEGY_STALE_H", "36"); setting("STRATEGY_WEEKLY_AT", core.iso(NOW))
    setting("ORG_ON", "TRUE"); setting("PALACE_ON", "TRUE"); setting("EXEC_ON", "TRUE"); setting("ORG_SINCE", core.iso(NOW - dt.timedelta(days=30)))
    setting("PAUSED", "FALSE"); setting("PAUSED_UNTIL", "")


def test_a_stale_review_is_said_stale_and_a_fresh_one_is_not(setting, monkeypatch):
    setting("STRATEGY_ON", "TRUE"); setting("STRATEGY_STALE_H", "36"); setting("STRATEGY_WEEKLY_AT", core.iso(NOW))
    _judged(setting)                                                                                             # U1b finding 9: a review was due
    monkeypatch.setattr(STR, "counting", lambda now=None: [])
    _today(setting, 18); assert STR.brief(NOW) == "*Decisions*\n- Strategy today: no change."                     # the usual 18 hours: unchanged
    _today(setting, 40); b = STR.brief(NOW)
    assert b == "*Decisions*\n- Strategy has not reviewed for 40 hours: its last word is old - no change.", b                  # U1 J 206: his words (RUL-U1)
    _today(setting, 40, ["not taken: X 1 -> 2 changes nothing the code does (1)"]); b = STR.brief(NOW)
    assert b == "*Decisions*\n- Strategy has not reviewed for 40 hours: its last word is old - Not taken: not taken: X 1 -> 2 changes nothing the code does (1).", b
    _today(setting, 36); assert "has not reviewed" not in STR.brief(NOW)                                         # AT the limit: not old (the check's ">")
    _today(setting, 30); assert STR.brief(NOW) == "*Decisions*\n- Strategy today: no change."                     # inside the limit: the old line
    for h in (30, 36, 40, 90): _today(setting, h); assert "STRATEGY_STALE_H" not in STR.brief(NOW), h           # a cell's name is the build's word, not his


def test_the_old_word_line_only_where_a_review_was_due_and_his_pause_says_so(setting, monkeypatch):
    """U1b finding 9 (RULINGS_U1b): the old-word line is written only where check strategy_live judges the review's age (ONE gate for both); where the
    check names a reason, the brief keeps the words it had before 206; under his own pause the line says the cause is his."""
    _judged(setting); monkeypatch.setattr(STR, "counting", lambda now=None: [])
    setting("EXEC_ON", "FALSE"); _today(setting, 40); b = STR.brief(NOW)
    assert b == "*Decisions*\n- Strategy today: no change." and "has not reviewed" not in b, b                  # no review is run: no growing number
    assert STR.live_issues(now=NOW)[2] == "the Execution Engine is switched off (EXEC_ON): Strategy cannot decide, so it does not review"     # the check's words
    _today(setting, 40, ["X 1 -> 2 changes nothing the code does (1)"])
    assert STR.brief(NOW) == "*Decisions*\n- Not taken today: X 1 -> 2 changes nothing the code does (1)."
    setting("EXEC_ON", "TRUE"); setting("ORG_ON", "FALSE"); _today(setting, 40); assert "has not reviewed" not in STR.brief(NOW)      # the organisation off
    setting("ORG_ON", "TRUE"); setting("ORG_SINCE", core.iso(NOW - dt.timedelta(hours=20)))
    assert "has not reviewed for" not in STR.brief(NOW) and STR.live_issues(now=NOW)[2].startswith("Strategy has not reviewed yet")        # too young to judge
    setting("ORG_SINCE", core.iso(NOW - dt.timedelta(days=30))); setting("PAUSED", "TRUE"); b = STR.brief(NOW)
    assert b == "*Decisions*\n- Strategy does not review while the channel is paused: its last word is 40 hours old - no change.", b      # his pause, his words
    _today(setting, 30); assert STR.brief(NOW) == "*Decisions*\n- Strategy today: no change."                     # paused, inside the limit: the old line
    setting("PAUSED", "FALSE"); _today(setting, 40); assert "Strategy has not reviewed for 40 hours" in STR.brief(NOW)      # due and not paused: 206's line
