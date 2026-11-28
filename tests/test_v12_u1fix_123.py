"""U1 J 123 (#131): THE LAB ROAD OF CHECK hook_lab ASKS FOR "applied". `hooks.verify_in_narration` sets the status "needs_human_choice" and leaves
`applied` true when the chosen line is no longer the opening; `contract.p_hook` read only `applied` and said PASS for a film that does not open on
its hook. On the plain lab road (no `second`, source not "short") the check now asks for the status "applied" too. The two Short roads are unchanged
(their own tests: tests/test_v12_opening.py, tests/test_v12_strategy.py)."""
from whatifs import hooks as HOOKS, contract as CON
from tests.test_hooks import SCRIPT, fake_ask

MOVED = "the hook lab's chosen line is not the first spoken line (a later rewrite changed it)"


def _lab():
    rec = HOOKS.build_record(SCRIPT, {}, "EP123", fake_ask()); HOOKS.decide(rec, SCRIPT)
    assert rec["applied"] is True and rec["status"] == "applied" and not rec.get("source") and not rec.get("second"), {k: rec.get(k) for k in ("applied", "status", "source")}
    return rec, next(c for c in rec["candidates"] if c["id"] == rec["chosen_id"])["line"]


def test_the_lab_road_fails_when_a_rewrite_moved_the_chosen_line():
    rec, line = _lab()
    assert HOOKS.verify_in_narration(rec, [{"text": "The coastline moves before anything else."}, {"text": line}]) is False
    assert rec["applied"] is True and rec["status"] == "needs_human_choice"      # the fact of the issue: applied stays true, the status says it moved
    assert CON.p_hook({"hook_rec": rec, "d": {}}) == (CON.FAIL, MOVED)


def test_the_lab_road_passes_with_the_line_in_place():
    rec, line = _lab()
    assert HOOKS.verify_in_narration(rec, [{"text": line}, {"text": "The water starts to change colour."}]) is True and rec["status"] == "applied"
    assert CON.p_hook({"hook_rec": rec, "d": {}}) == (CON.PASS, f"{len(rec['candidates'])} candidates, winner chosen by judge")      # today's words
