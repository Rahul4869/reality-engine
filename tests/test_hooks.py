import json, os, re
import pytest
from whatifs import hooks as H

SCRIPT = ("## BEAT 1\n[calm] Right now about eight billion people are doing something ordinary.\n[tension] But at exactly noon all of them do it at once.\n"
          "[reveal] The water starts to change colour and the coastline moves.\n[tension] The strangest part is what happens to you.")
GOOD = [("Eight billion people do it at exactly noon.", "surprising_claim"), ("The water starts to change colour.", "outcome_promise"),
        ("The strangest part is what happens to you.", "curiosity_gap"), ("All of them do it at once.", "concrete_stakes"),
        ("The coastline moves at noon.", "concrete_stakes"), ("Water changes colour, then the coastline moves.", "outcome_promise"),
        ("Something ordinary happens to eight billion people.", "surprising_claim"), ("What happens to you is strangest.", "curiosity_gap"),
        ("Everyone does it at exactly noon.", "surprising_claim"), ("Then the water changes colour.", "outcome_promise")]

def fake_ask(cands=GOOD, scores=None, judge_fails=False):
    def ask(role, system, prompt, **kw):
        if role in ("sonnet", "hooks"): return {"candidates": [{"line": a, "type": b, "basis": "x"} for a, b in cands]}
        if judge_fails: raise RuntimeError("judge down")
        ids = re.findall(r'"id": "(h\d+)"', prompt)
        return {"scores": [dict({"id": i, "clarity": 9, "relevance": 9, "curiosity": 8, "promise_accuracy": 9, "unsupported_claim": False}, **((scores or {}).get(i, {}))) for i in ids]}
    return ask

@pytest.mark.parametrize("line,n", [("Eight billion people do it at noon.", 7), ("It's 3.5 million kilometres.", 4), ("Well-known fact", 3), ("", 0)])
def test_count_words(line, n): assert H.count_words(line) == n

def test_word_limit_is_strictly_fewer_than_ten():
    nine = "one two three four five six seven eight nine"; ten = nine + " ten"
    assert H.count_words(nine) == 9 and not any(i.startswith("too_long") for i in H.validate_line(nine, nine))
    assert any(i.startswith("too_long") for i in H.validate_line(ten, ten))

@pytest.mark.parametrize("line", ["Welcome to the strangest hour on Earth.", "Today we look at pillows.", "Did you know pillows float?", "Imagine eight billion pillows floating.", "Hey, pillows are floating."])
def test_greetings_and_throat_clearing_rejected(line):
    assert "greeting_or_throat_clearing" in H.validate_line(line, "pillows float eight billion")

def test_hype_phrase_flagged(): assert "hype_or_unsupported_phrase" in H.validate_line("The shocking secret of pillows", "pillows secret shocking")

def test_number_not_in_script_is_flagged_as_unsupported():
    assert "number_not_in_script" in H.validate_line("Nine billion people do it at noon.", SCRIPT)
    assert "number_not_in_script" not in H.validate_line("Eight billion people do it at noon.", SCRIPT)

def test_low_overlap_flagged(): assert "low_overlap_with_script" in H.validate_line("Dinosaurs secretly built volcanoes.", SCRIPT)

def test_ten_candidates_scored_ranked_and_best_chosen():
    rec = H.build_record(SCRIPT, {"premise": "p"}, "EPX", fake_ask())
    assert len(rec["candidates"]) == 10 and rec["scored_by"] == "judge"
    assert all(c["words"] < 10 for c in rec["candidates"])
    assert [c["total"] for c in rec["candidates"]] == sorted((c["total"] for c in rec["candidates"]), reverse=True)
    assert rec["chosen_id"] and all(k in rec["candidates"][0] for k in ("clarity", "relevance", "curiosity", "promise_accuracy"))

def test_overlong_and_greeting_lines_are_dropped_and_recorded():
    bad = [("Welcome to the strangest hour on Earth today friends", "curiosity_gap"), ("Today pillows float.", "curiosity_gap")] + GOOD
    rec = H.build_record(SCRIPT, {}, "EPX", fake_ask(bad))
    assert len(rec["candidates"]) == 10 and len(rec["rejected"]) >= 2
    assert all(c["words"] < 10 for c in rec["candidates"])

def test_unsupported_claim_from_judge_blocks_automatic_choice():
    rec = H.build_record(SCRIPT, {}, "EPX", fake_ask(scores={f"h{i}": {"unsupported_claim": True} for i in range(10)}))
    assert rec["chosen_id"] is None and rec["status"] == "pending"
    assert all("unsupported_claim_flagged" in c["issues"] for c in rec["candidates"])
    assert H.decide(rec, SCRIPT) == SCRIPT and rec["status"] == "needs_human_choice"

def test_low_promise_accuracy_not_eligible():
    rec = H.build_record(SCRIPT, {}, "EPX", fake_ask(scores={f"h{i}": {"promise_accuracy": 4} for i in range(10)}))
    assert rec["chosen_id"] is None

def test_judge_failure_uses_labelled_heuristics_and_applies_nothing():
    rec = H.build_record(SCRIPT, {}, "EPX", fake_ask(judge_fails=True))
    assert rec["scored_by"] == "heuristic" and rec["chosen_id"] is None
    assert any("heuristic" in n for n in rec["notes"])
    assert H.decide(rec, SCRIPT) == SCRIPT

def test_unscored_candidate_is_not_guessed():
    def ask(role, system, prompt, **kw):
        if role in ("sonnet", "hooks"): return {"candidates": [{"line": a, "type": b} for a, b in GOOD]}
        return {"scores": [{"id": "h0", "clarity": 9, "relevance": 9, "curiosity": 9, "promise_accuracy": 9}]}
    rec = H.build_record(SCRIPT, {}, "EPX", ask)
    others = [c for c in rec["candidates"] if c["id"] != "h0"]
    assert all("not_scored" in c["issues"] and not c["valid"] for c in others)

def test_apply_inserts_without_removing_anything():
    new, ok, _ = H.apply_to_script(SCRIPT, "Eight billion people do it at exactly noon.")
    assert ok and "[tension] Eight billion people do it at exactly noon." in new
    for line in SCRIPT.split("\n"): assert line in new
    assert new.index("## BEAT 1") < new.index("Eight billion people do it")

def test_apply_skips_when_writer_already_opens_that_way():
    s = "## BEAT 1\n[calm] Eight billion people do it at exactly noon.\n[calm] More."
    new, ok, why = H.apply_to_script(s, "Eight billion people do it at exactly noon.")
    assert not ok and new == s

def test_suggest_mode_records_but_does_not_apply(setting, tmp_path):
    setting("HOOK_APPLY_MODE", "suggest")
    new, rec = H.run_hooks(SCRIPT, {}, "EPS", str(tmp_path), fake_ask())
    assert new == SCRIPT and rec["status"] == "needs_human_choice" and rec["applied"] is False and rec["chosen_id"]

def test_auto_mode_applies_and_saves_record_with_episode(tmp_path):
    from whatifs import core
    new, rec = H.run_hooks(SCRIPT, {}, "EPA", str(tmp_path), fake_ask())
    assert rec["status"] == "applied" and new != SCRIPT
    saved = json.load(open(tmp_path / "hooks.json")); assert saved["episode_id"] == "EPA" and len(saved["candidates"]) == 10
    rows = core.store().rows("Hook_Candidates"); assert len(rows) >= 10 and sum(1 for r in rows if r["applied"] == "TRUE") == 1

def test_run_hooks_never_raises_and_leaves_script_unchanged(tmp_path):
    def boom(*a, **k): raise RuntimeError("all models failed")
    new, rec = H.run_hooks(SCRIPT, {}, "EPF", str(tmp_path), boom)
    assert new == SCRIPT and rec["status"] == "failed"

def test_switched_off(tmp_path, setting):
    setting("HOOKS_ON", "FALSE"); new, rec = H.run_hooks(SCRIPT, {}, "EPO", str(tmp_path), fake_ask()); assert new == SCRIPT and rec is None

def test_verify_in_narration_flags_changed_opening():
    rec = H.build_record(SCRIPT, {}, "EPV", fake_ask()); H.decide(rec, SCRIPT)
    assert H.verify_in_narration(rec, [{"text": rec["candidates"][0]["line"]}]) is True
    assert H.verify_in_narration(rec, [{"text": "Something else entirely."}]) is False and rec["status"] == "needs_human_choice"

