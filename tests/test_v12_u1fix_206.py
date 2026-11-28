"""U1 fix 206 (open issue 234): THE BRIEF'S "no change" LINE SAYS WHEN THE REVIEW IS STALE. Strategy's word of the day (STRATEGY_TODAY, its "at") older
than STRATEGY_STALE_H hours is said to be stale, with its age - the same rule as check strategy_live; a review inside the limit keeps the old words."""
import datetime as dt, json
from whatifs import core
from whatifs.org import strategy as STR

NOW = dt.datetime(2031, 5, 6, 3, 0, tzinfo=dt.timezone.utc)


def _today(setting, hours_ago, refused=()):
    setting("STRATEGY_TODAY", json.dumps({"at": core.iso(NOW - dt.timedelta(hours=hours_ago)), "refused": list(refused), "counting": []}))


def test_a_stale_review_is_said_stale_and_a_fresh_one_is_not(setting, monkeypatch):
    setting("STRATEGY_ON", "TRUE"); setting("STRATEGY_STALE_H", "36"); setting("STRATEGY_WEEKLY_AT", core.iso(NOW))
    monkeypatch.setattr(STR, "counting", lambda now=None: [])
    _today(setting, 18); assert STR.brief(NOW) == "*Decisions*\n- Strategy today: no change."                     # the usual 18 hours: unchanged
    _today(setting, 40); b = STR.brief(NOW)
    assert "no change" in b and "stale" in b and "40 hours" in b and "STRATEGY_STALE_H" in b and "today" not in b, b
    _today(setting, 40, ["not taken: X 1 -> 2 changes nothing the code does (1)"]); b = STR.brief(NOW)
    assert "stale" in b and "40 hours" in b and "not taken: X 1 -> 2" in b and "today" not in b, b
    _today(setting, 36); assert "stale" not in STR.brief(NOW)                                                    # AT the limit: not stale (the check's ">")
