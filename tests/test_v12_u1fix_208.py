"""U1 fix 208 (open issue 236): A DESK TICKET THE ENGINE REFUSED OR ROLLED BACK NO LONGER STAYS "ADOPTED" on tab Owner_Desk. The tick's desk step reads
the engine's word on every ADOPTED row's ticket: refused -> REFUSED, failed -> FAILED (U1b), rolled back -> ROLLED_BACK, with the engine's note, and the row is
briefed again so the next brief tells him; a verified or applied ticket stays ADOPTED."""
from whatifs import core
from whatifs.org import desk as DK, execute as EX


def _desk(n, ticket):
    core.store().append("Owner_Desk", [{"n": n, "ts": core.iso(core.now_utc()), "sha": "s" + n, "verbatim": "make 14 shorts a month", "verdict": "ADOPTED",
                                         "how": "SHORTS_PER_MONTH 12 -> 14 as a ticket now", "memo": "", "ticket": ticket, "action": "", "briefed": core.iso(core.now_utc())}])


def _row(n): return next(r for r in core.store().rows("Owner_Desk") if str(r["n"]) == n)


def test_a_refused_or_rolled_back_desk_ticket_says_so_and_is_told_again(monkeypatch):
    words = {"T-ref": ("refused", "out of range"), "T-rb": ("rolled_back", "the effect differed"), "T-fail": ("failed", "the apply raised"),
             "T-ok": ("verified", "ok"), "T-app": ("applied", "")}
    monkeypatch.setattr(EX, "state_of", lambda tid, st=None: words.get(tid))
    for n, t in (("901", "T-ref"), ("902", "T-rb"), ("903", "T-fail"), ("904", "T-ok"), ("905", "T-app"), ("906", "T-none")): _desk(n, t)
    DK._next_steps(core.store(), core.now_utc())
    assert (_row("901")["verdict"], _row("902")["verdict"], _row("903")["verdict"]) == ("REFUSED", "ROLLED_BACK", "FAILED")
    assert "out of range" in _row("901")["how"] and "the effect differed" in _row("902")["how"]
    assert _row("901")["briefed"] == "" and _row("902")["briefed"] == ""                                # the next brief carries the new answer
    assert [_row(n)["verdict"] for n in ("904", "905", "906")] == ["ADOPTED"] * 3                          # verified, applied or not yet read: unchanged
    assert _row("904")["briefed"] != ""
    DK._next_steps(core.store(), core.now_utc())
    assert _row("901")["verdict"] == "REFUSED" and _row("901")["briefed"] == ""                         # read once: a second tick changes nothing


def test_he_reads_not_done_and_undone_on_his_tab_and_in_the_next_brief_once(monkeypatch, setting):
    """U1 J 208 (RUL-U1 PART 3): the stored verdicts stay REFUSED / ROLLED_BACK; what he READS - the dashboard's list of his inputs (tab Owner_Desk)
    and the next brief - is "NOT DONE" / "UNDONE" with the engine's note, told once."""
    setting("TWO_SCREENS_ON", "TRUE")
    words = {"T-ref": ("refused", "out of range"), "T-rb": ("rolled_back", "the effect differed")}
    monkeypatch.setattr(EX, "state_of", lambda tid, st=None: words.get(tid))
    for n, t in (("911", "T-ref"), ("912", "T-rb")): _desk(n, t)
    DK._next_steps(core.store(), core.now_utc())
    assert (_row("911")["verdict"], _row("912")["verdict"]) == ("REFUSED", "ROLLED_BACK")                 # what is stored is unchanged
    from whatifs import dash as DA
    shown = {str(i["n"]): (i["verdict"], i["answer"]) for i in DA._inputs(True)}
    assert shown["911"] == ("NOT DONE", "the engine refused it: out of range.") and shown["912"] == ("UNDONE", "the engine took it back: the effect differed."), shown
    now = core.now_utc(); b = DK.lines(now)
    assert len([l for l in b if l.startswith('Your input 911 ("make 14 shorts a month"): NOT DONE - the engine refused it: out of range.')]) == 1, b
    assert len([l for l in b if l.startswith('Your input 912 ("make 14 shorts a month"): UNDONE - the engine took it back: the effect differed.')]) == 1, b
    assert not [l for l in b if "REFUSED" in l or "ROLLED_BACK" in l], b
    assert DK.briefed(now) >= 2 and not [l for l in DK.lines(now) if l.startswith(("Your input 911", "Your input 912"))]      # told once


def test_a_failed_desk_ticket_says_not_finished_never_refused(monkeypatch, setting):
    """U1b 208 (RULINGS_U1b PART 1): the engine writes "failed" when a change did not read back AND could not be undone - the setting may stand changed
    and the ticket has gone to repair. Its own stored verdict FAILED, its own words, shown "NOT FINISHED", told once; a refusal still says NOT DONE."""
    setting("TWO_SCREENS_ON", "TRUE")
    words = {"T-ref": ("refused", "out of range"), "T-fail": ("failed", "the apply raised")}
    monkeypatch.setattr(EX, "state_of", lambda tid, st=None: words.get(tid))
    for n, t in (("901", "T-ref"), ("903", "T-fail")): _desk(n, t)
    DK._next_steps(core.store(), core.now_utc())
    r = _row("903"); assert r["verdict"] == "FAILED" and r["briefed"] == "", r
    assert "could not put it back" in r["how"] and "the apply raised" in r["how"] and "refused" not in r["how"], r["how"]
    from whatifs import dash as DA
    assert {str(i["n"]): i["verdict"] for i in DA._inputs(True)}["903"] == "NOT FINISHED"
    now = core.now_utc(); b = DK.lines(now)
    l3, l1 = [l for l in b if l.startswith("Your input 903 ")], [l for l in b if l.startswith("Your input 901 ")]
    assert len(l3) == 1 and "NOT FINISHED" in l3[0] and "NOT DONE" not in l3[0], b
    assert len(l1) == 1 and "NOT DONE" in l1[0], b
    assert DK.briefed(now) >= 2 and _row("903")["briefed"] != "" and not [l for l in DK.lines(now) if l.startswith("Your input 903 ")]      # told once
