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
