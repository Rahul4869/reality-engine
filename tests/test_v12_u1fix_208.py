"""U1 fix 208 (open issue 236): A DESK TICKET THE ENGINE REFUSED OR ROLLED BACK NO LONGER STAYS "ADOPTED" on tab Owner_Desk. The tick's desk step reads
the engine's word on every ADOPTED row's ticket: refused (or failed) -> REFUSED, rolled back -> ROLLED_BACK, with the engine's note, and the row is
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
    assert (_row("901")["verdict"], _row("902")["verdict"], _row("903")["verdict"]) == ("REFUSED", "ROLLED_BACK", "REFUSED")
    assert "out of range" in _row("901")["how"] and "the effect differed" in _row("902")["how"]
    assert _row("901")["briefed"] == "" and _row("902")["briefed"] == ""                                # the next brief carries the new answer
    assert [_row(n)["verdict"] for n in ("904", "905", "906")] == ["ADOPTED"] * 3                          # verified, applied or not yet read: unchanged
    assert _row("904")["briefed"] != ""
    DK._next_steps(core.store(), core.now_utc())
    assert _row("901")["verdict"] == "REFUSED" and _row("901")["briefed"] == ""                         # read once: a second tick changes nothing
