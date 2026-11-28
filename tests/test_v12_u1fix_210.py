"""U1 fix 210 (open issue 239), U1b 210 (RULINGS_U1b PART 1): "RESENT" MEANS WRITTEN. settle() returns a re-sent ticket and stamps nothing; the runner's
settle step (strategy.stamp_resent) stamps "resent" only when that ticket IS on tab Memos - a review whose memos were not written (a write that raised,
or every memo of the run dropped as invalid) stamps nothing, and the next review sends it again. A ticket that can never be written is void at once (the
writer's own check, before it goes out); a decision whose ticket was written once more and is then gone from tab Memos is void."""
import datetime as dt, inspect, json
import pytest
from whatifs import core
from whatifs.org import strategy as STR, runner as RN, memos as MEM


def _row(did):
    return next(r for r in core.store().rows("Decisions") if r["id"] == did)


def _plant(setting, did, **kw):
    setting("STRATEGY_ON", "TRUE"); setting("ORG_SINCE", core.iso(core.now_utc() - dt.timedelta(days=3)))
    core.store().append("Decisions", [dict({"id": did, "ts": core.iso(core.now_utc() - dt.timedelta(hours=27)), "rule": "SPLIT", "key": "SHORTS_PER_MONTH", "old": "12",
                                            "new": "14", "state": "decided", "why": "w", "numbers": "{}", "ticket": "MEMO-NEVER-WRITTEN"}, **kw)])


def test_settle_stamps_nothing_and_the_runners_step_stamps_after_the_write(setting):
    _plant(setting, "DEC-u210a")
    t = STR.settle(); assert len(t) == 1 and t[0]["body"]["decision_ref"] == "DEC-u210a"
    assert "resent" not in json.loads(_row("DEC-u210a")["numbers"])               # nothing written yet: nothing stamped
    assert len(STR.settle()) == 1 and _row("DEC-u210a")["state"] == "decided"              # not written: sent again, never void
    assert STR.stamp_resent({"resent": ["DEC-u210a"]}) == []                                # U1b 210 (a): its ticket is not on tab Memos - nothing stamped
    assert "resent" not in json.loads(_row("DEC-u210a")["numbers"])
    assert len(STR.settle()) == 1 and _row("DEC-u210a")["state"] == "decided"              # so the next settle sends it again


def test_a_review_whose_memos_were_not_written_stamps_nothing(setting, monkeypatch):
    _plant(setting, "DEC-u210b"); called = []; stamp = lambda o, *a, **k: (called.append(o), STR.stamp_resent(o, *a, **k))[1]      # RUL-LAST2-U1 (RD-U1l-TG F3): a spy on the settle step
    real_w, real_s, sent = MEM.write, STR.settle, []
    def write(m, *a, **k):
        if str(m.get("dedupe_key")) == "strategy|DEC-u210b": raise RuntimeError("planted: the re-sent ticket's write failed")
        return real_w(m, *a, **k)
    monkeypatch.setattr(MEM, "write", write); monkeypatch.setattr(STR, "settle", lambda *a, **k: (lambda t: (sent.extend(t), t)[1])(real_s(*a, **k)))
    with pytest.raises(RN.ContractBreach, match="planted: the re-sent ticket's write failed"):      # RUL-LAST-U1 (RD-U1k-SF F1): the planted write error is the run's breach, never swallowed
        RN.run("D1", "review", STR.review, settle=stamp)      # runner.py:323-327: a write that raises ends EMIT before its settle step
    assert [m["body"]["decision_ref"] for m in sent] == ["DEC-u210b"]                       # the review ran and sent it once more
    assert "resent" not in json.loads(_row("DEC-u210b")["numbers"]) and _row("DEC-u210b")["state"] == "decided" and called == [], called      # RUL-LAST2-U1 (RD-U1l-TG F3): settle never ran after the failed write


def test_the_daily_round_runs_the_review_with_the_stamp_step():
    from whatifs import cli
    assert 'ORG.run("D1", "review", STR.review, settle=STR.stamp_resent)' in inspect.getsource(cli)


def test_a_review_that_wrote_the_ticket_stamps_it(setting):
    _plant(setting, "DEC-u210c")
    RN.run("D1", "review", STR.review, settle=STR.stamp_resent)
    assert MEM.find(live=False, type="ticket", dedupe_key="strategy|DEC-u210c")                   # the runner wrote the re-sent ticket
    assert json.loads(_row("DEC-u210c")["numbers"])["resent"]                                    # and only then was it stamped


def test_a_review_whose_memos_were_dropped_as_invalid_stamps_nothing(setting):
    """U1b 210 (a) (CODEREVIEW_PRE-P_1 finding 1): the runner drops EVERY memo of a run when one is invalid and still calls its settle step - the
    re-sent ticket is not on tab Memos, so nothing is stamped and the next settle sends it again."""
    _plant(setting, "DEC-u210d"); called = []; stamp = lambda o, *a, **k: (called.append(o), STR.stamp_resent(o, *a, **k))[1]      # RUL-LAST-U1 (RD-U1k-SF F2): a spy on the settle step
    def act(brief):
        o = STR.review(brief); o.memos.append({"type": "ticket", "from_dept": "D1", "to_depts": ["D4"], "subject": "x"}); return o
    with pytest.raises(RN.ContractBreach, match="invalid memo"): RN.run("D1", "review", act, settle=stamp)      # EMIT dropped every memo, then settle ran
    assert not MEM.find(live=False, type="ticket", dedupe_key="strategy|DEC-u210d")                # nothing of that run was written
    assert called and "DEC-u210d" in called[0]["resent"] and "resent" not in json.loads(_row("DEC-u210d")["numbers"]), called      # settle ran (runner.py:327) and stamped nothing
    t = STR.settle()
    assert [m["body"]["decision_ref"] for m in t] == ["DEC-u210d"] and _row("DEC-u210d")["state"] == "decided"


def test_a_decision_written_once_more_and_gone_from_tab_memos_is_void(setting):
    """U1b 210 (c): "then void" as the words say - a row stamped "resent" (as a written re-send leaves it) whose ticket is no longer on tab Memos."""
    _plant(setting, "DEC-u210v", numbers=json.dumps({"resent": core.iso(core.now_utc() - dt.timedelta(hours=20))}))
    assert STR.settle() == [] and _row("DEC-u210v")["state"] == "void"
    assert "sent once more" in json.loads(_row("DEC-u210v")["numbers"])["engine_note"]


TRIAL_C = {"rule": "TRIAL", "key": "playbook:writer", "old": "", "new": "open on the verdict, never on the setup", "why": "a candidate from the arm book: t",
           "numbers": json.dumps({"candidate": "CAND-u210"}), "effect_before": json.dumps(""), "effect_after": json.dumps("open on the verdict, never on the setup"),
           "ticket": "MEMO-TRIAL-NEVER-WRITTEN"}                                          # the row decide_trial writes for a rulebook (class C) candidate


def test_a_ticket_that_can_never_be_written_is_void_at_once_and_costs_the_review_nothing(setting):
    """U1b 210 (b): a decided TRIAL row of class C has a key no department owns, so settle's class B re-send would be an invalid memo (to_depts [""]).
    The writer's own check (MEM.id_for) refuses it first: the row is void at once and nothing goes out; a review with a valid class B row beside it
    WRITES that row's ticket (no memo of the run is dropped)."""
    from whatifs.org import levers as LV
    assert LV.owner_of("playbook:writer") == ""                                                 # the reading the ruling rests on (levers.py 80)
    core.store().append("Candidates", [{"id": "CAND-u210", "state": "trial", "title": "t"}])
    _plant(setting, "DEC-u210t", **TRIAL_C)
    assert STR.settle() == [] and _row("DEC-u210t")["state"] == "void"
    assert "cannot be written" in json.loads(_row("DEC-u210t")["numbers"])["engine_note"]
    _plant(setting, "DEC-u210u", **TRIAL_C); _plant(setting, "DEC-u210w")
    RN.run("D1", "review", STR.review, settle=STR.stamp_resent)
    assert _row("DEC-u210u")["state"] == "void"
    assert MEM.find(live=False, type="ticket", dedupe_key="strategy|DEC-u210w")                    # the class B ticket beside it was WRITTEN
    assert json.loads(_row("DEC-u210w")["numbers"])["resent"]


def test_the_row_names_the_ticket_it_sends(setting):
    """U1b 210 (b): a row whose ticket id is not the re-sent ticket's names the one sent (as decide names its id before the runner writes)."""
    _plant(setting, "DEC-u210e")
    t = STR.settle(); assert len(t) == 1
    assert _row("DEC-u210e")["ticket"] == MEM.id_for(t[0]) != "MEMO-NEVER-WRITTEN"

def test_a_resent_id_with_no_row_is_named_in_a_warn(monkeypatch):
    seen = []; monkeypatch.setattr(STR, "log", lambda m, *a, **k: seen.append((m, a, k)))      # RUL-SWEEP-U1 (RD-U1j-SF F2): strategy.py:705 skipped an unknown id with no trace
    assert STR.stamp_resent({"resent": ["DEC-NO-SUCH"]}) == []
    assert [m for m, a, k in seen if "WARN" in (a + tuple(k.values()))] == ["strategy: decision DEC-NO-SUCH: re-sent, but no such row on tab Decisions: nothing stamped"], seen


def test_stamp_resent_goes_on_past_an_unknown_and_an_unwritten_id(setting, monkeypatch):
    """RUL-LAST-U1 (RD-U1k-TG F5): strategy.py:705 and :708-709 skip ONE id and go on - an unknown id and an id whose ticket was not written never stop
    the stamp of a later id whose ticket IS on tab Memos."""
    _plant(setting, "DEC-u210g"); _plant(setting, "DEC-u210f", ticket="MEMO-u210f")
    monkeypatch.setattr(MEM, "get", lambda tid, st=None: {"id": tid} if tid == "MEMO-u210f" else None)      # only DEC-u210f's ticket is on tab Memos
    assert STR.stamp_resent({"resent": ["DEC-NO-SUCH", "DEC-u210g", "DEC-u210f"]}) == []
    assert json.loads(_row("DEC-u210f")["numbers"])["resent"] and "resent" not in json.loads(_row("DEC-u210g")["numbers"])
