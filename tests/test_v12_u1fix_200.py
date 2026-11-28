"""U1 J 200 (#226): THE TWO OWNER MESSAGE KINDS THAT COME AND GO WITH THE WEEKDAY ARE THE CALENDAR'S, BY DESIGN. `replan` is sent by `replan.weekly` only
on a Monday and only with STRATEGY_ON FALSE; `advisor` by `caretaker.advisor`, only inside manage.learn's block opened by `in ("Sun",)`. The sweep names
them (WEEKDAY_KINDS) and its summary says which of them a run saw ("owner_weekday_kinds"); "owner_message_kinds" is unchanged."""
import ast, datetime as dt, inspect
import pytest
from whatifs import core, notify as NT, replan as RP, manage as MG
from tools import sweep as SW

MONDAY = dt.datetime(2026, 11, 16, 9, 0, tzinfo=dt.timezone.utc)
PROP = [{"why": "planted", "key": "LONG_PER_WEEK", "to": "3", "cost": 100}]


def _replan_rows(): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "replan"]


def test_every_weekday_kind_is_a_registered_kind_and_the_helper_names_them():
    assert set(SW.WEEKDAY_KINDS) == {"replan", "advisor"} and all(k in NT.KINDS for k in SW.WEEKDAY_KINDS)
    assert SW.weekday_kinds(["replan", "owner_verdict", "advisor"]) == ["advisor", "replan"] and SW.weekday_kinds([]) == []
    s = SW.summary([{"id": "a", "outcome": "ok", "owner": ["replan", "owner_verdict"]}, {"id": "b", "outcome": "ok", "owner": ["advisor"]}])
    assert s["owner_weekday_kinds"] == ["advisor", "replan"] and s["owner_message_kinds"] == {"advisor": 1, "owner_verdict": 1, "replan": 1}


@pytest.mark.parametrize("now,strategy,rows", [(MONDAY, "FALSE", 1), (MONDAY + dt.timedelta(days=1), "FALSE", 0), (MONDAY, "TRUE", 0)],
                         ids=["monday", "tuesday", "monday_strategy_on"])
def test_replan_is_sent_on_a_monday_only_and_only_with_strategy_off(now, strategy, rows, monkeypatch, setting):
    setting("REPLAN_ON", "TRUE"); setting("STRATEGY_ON", strategy); monkeypatch.setattr(RP, "proposals", lambda now=None: list(PROP))
    RP.weekly(now=now)
    assert len(_replan_rows()) == rows, _replan_rows()


def test_the_advisor_stands_inside_the_sunday_block_of_manage():
    tree = ast.parse(inspect.getsource(MG.learn))
    sunday = [n for n in ast.walk(tree) if isinstance(n, ast.If) and 'in ("Sun",)' in ast.unparse(n.test).replace("'", '"')]
    assert len(sunday) == 1, [ast.unparse(n.test) for n in sunday]
    inside = [n for n in ast.walk(sunday[0]) if isinstance(n, ast.Call) and ast.unparse(n.func) == "CTK.advisor"]
    everywhere = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "CTK.advisor"]
    assert len(inside) == 1 and len(everywhere) == 1
