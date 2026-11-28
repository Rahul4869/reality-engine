"""U1 fix 210 (open issue 239): "resent" IS STAMPED ONLY AFTER THE RUNNER WROTE THE RE-SENT TICKET. settle() returns the ticket and stamps nothing; the
runner's settle step (strategy.stamp_resent, called only after the run's memos were written) stamps it. A review whose memos were never written leaves the
row unstamped, so the next review sends it again - never void for a ticket that was not sent once more."""
import datetime as dt, inspect, json
from whatifs import core
from whatifs.org import strategy as STR, runner as RN, memos as MEM


def _row(did):
    return next(r for r in core.store().rows("Decisions") if r["id"] == did)


def _plant(setting, did):
    setting("STRATEGY_ON", "TRUE"); setting("ORG_SINCE", core.iso(core.now_utc() - dt.timedelta(days=3)))
    core.store().append("Decisions", [{"id": did, "ts": core.iso(core.now_utc() - dt.timedelta(hours=27)), "rule": "SPLIT", "key": "SHORTS_PER_MONTH", "old": "12",
                                       "new": "14", "state": "decided", "why": "w", "numbers": "{}", "ticket": "MEMO-NEVER-WRITTEN"}])


def test_settle_stamps_nothing_and_the_runners_step_stamps_after_the_write(setting):
    _plant(setting, "DEC-u210a")
    t = STR.settle(); assert len(t) == 1 and t[0]["body"]["decision_ref"] == "DEC-u210a"
    assert "resent" not in json.loads(_row("DEC-u210a")["numbers"] or "{}")               # nothing written yet: nothing stamped
    assert len(STR.settle()) == 1 and _row("DEC-u210a")["state"] == "decided"              # not written: sent again, never void
    assert STR.stamp_resent({"resent": ["DEC-u210a"]}) == []
    assert json.loads(_row("DEC-u210a")["numbers"])["resent"]
    assert STR.settle() == [] and _row("DEC-u210a")["state"] == "void"                     # stamped and still no ticket: then void


def test_a_review_whose_memos_were_not_written_stamps_nothing(setting, monkeypatch):
    _plant(setting, "DEC-u210b")
    real_w, real_s, sent = MEM.write, STR.settle, []
    def write(m, *a, **k):
        if str(m.get("dedupe_key")) == "strategy|DEC-u210b": raise RuntimeError("planted: the re-sent ticket's write failed")
        return real_w(m, *a, **k)
    monkeypatch.setattr(MEM, "write", write); monkeypatch.setattr(STR, "settle", lambda *a, **k: (lambda t: (sent.extend(t), t)[1])(real_s(*a, **k)))
    try: RN.run("D1", "review", STR.review, settle=STR.stamp_resent)
    except Exception as e: print("RAISED", type(e).__name__, str(e)[:300])
    assert [m["body"]["decision_ref"] for m in sent] == ["DEC-u210b"]                       # the review ran and sent it once more
    assert "resent" not in json.loads(_row("DEC-u210b")["numbers"] or "{}") and _row("DEC-u210b")["state"] == "decided"


def test_the_daily_round_runs_the_review_with_the_stamp_step():
    from whatifs import cli
    assert 'ORG.run("D1", "review", STR.review, settle=STR.stamp_resent)' in inspect.getsource(cli)


def test_a_review_that_wrote_the_ticket_stamps_it(setting):
    _plant(setting, "DEC-u210c")
    RN.run("D1", "review", STR.review, settle=STR.stamp_resent)
    assert MEM.find(live=False, type="ticket", dedupe_key="strategy|DEC-u210c")                   # the runner wrote the re-sent ticket
    assert json.loads(_row("DEC-u210c")["numbers"])["resent"]                                    # and only then was it stamped
