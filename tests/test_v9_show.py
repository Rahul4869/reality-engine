"""v9 stage 1: the Show Plan contract, its code validator / repairer, the character bible, the tag contract and the IP guard. Pure code + the fake Showrunner."""
import json, copy
import pytest
from whatifs import core, show as SHOW, room as ROOM, manage as MG, prompts as P, fakes as F

GOOD = json.loads(F.fake_reply("showrunner", ""))["show_plan"]

def test_a_good_plan_passes_unchanged_in_substance():
    p, iss = SHOW.validate(copy.deepcopy(GOOD), {"premise": "pillows"}, [])
    assert not iss, iss
    assert [e["id"] for e in p["exhibits"]] == ["A", "B", "C"] and p["exhibits"][1]["credit"] == "NASA Glenn Research Center"
    assert p["verdict"]["winner"] == "vale" and SHOW.meter_total(p["meter_swings"]) > 0 and p["clipbait_id"] == "C" and p["teacup_scenes"] == ["A", "C"]

def test_broken_plan_is_repaired_by_code_never_by_another_call():
    bad = {"charge": "word " * 40, "intensity": 9, "exhibits": [{"kind": "REAL_AGENCY", "what": "x"}, {"kind": "WEIRD"}],
           "witness_twist": "my uncle", "jury_prompts": [{"kind": "guilty", "text": "Guilty?"}], "meter_swings": [{"side": "grimm", "n": 2}],
           "verdict": {"winner": "vale"}, "clipbait_id": "Z", "hud_spec": [{"t": 5, "type": "survival", "label": "Survival odds", "value": 140, "unit": "%"},
           {"t": 9, "type": "scale", "label": "Vibes", "value": 1}], "teacup_scenes": ["A"]}
    p, iss = SHOW.validate(bad, {"premise": "p"}, [])
    assert len(p["charge"].split()) <= 20 and p["intensity"] == 3 and {e["kind"] for e in p["exhibits"]} == {"RECON"}
    assert p["witness_twist"] in SHOW.WITNESS_TWISTS and 3 <= len(p["jury_prompts"]) <= 5 and p["clipbait_id"] == "A" and p["hud_spec"] == "none"
    assert SHOW._winner_of(SHOW.meter_total(p["meter_swings"])) == p["verdict"]["winner"] == "vale" and len(iss) >= 6

def test_missing_plan_gets_a_complete_fallback():
    p, iss = SHOW.validate(None, {"premise": "What if pillows flew?"}, [])
    assert p["fallback"] and p["exhibits"] and len(p["jury_prompts"]) >= 3 and "fallback" in iss[0]

def test_intensity_range_is_a_setting(setting):
    setting("CHARACTER_INTENSITY_MIN", "1"); setting("CHARACTER_INTENSITY_MAX", "1")
    assert SHOW.validate(dict(GOOD, intensity=3), {}, [])[0]["intensity"] == 1 and "1-1" in SHOW.prompt_block([])

def test_witness_twist_never_repeats_within_five_episodes():
    hist = [{"witness_twist": t} for t in SHOW.WITNESS_TWISTS[:5]]
    p, iss = SHOW.validate(dict(GOOD, witness_twist=SHOW.WITNESS_TWISTS[0]), {}, hist)
    assert p["witness_twist"] not in SHOW.WITNESS_TWISTS[:5] and SHOW.WITNESS_TWISTS[0] not in SHOW.prompt_block(hist)

def test_villain_wins_about_one_in_three_and_only_on_a_detail():
    assert SHOW.villain_due([{"verdict_winner": "vale"}] * 3) and not SHOW.villain_due([{"verdict_winner": "grimm"}, {"verdict_winner": "vale"}])
    p, iss = SHOW.validate(dict(GOOD, verdict={"winner": "grimm", "detail": ""}), {}, [])
    assert p["verdict"]["winner"] == "vale" and any("detail" in i for i in iss)
    p, _ = SHOW.validate(dict(GOOD, verdict={"winner": "grimm", "detail": "the lift is wrong by 1000x"}), {}, [])
    assert p["verdict"]["winner"] == "grimm" and SHOW.meter_total(p["meter_swings"]) < 0          # the meter was made to agree

def test_jury_prompts_not_repeated_from_recent_episodes():
    hist = [{"plan_json": json.dumps({"jury_prompts": [GOOD["jury_prompts"][0]]})}]
    p, iss = SHOW.validate(copy.deepcopy(GOOD), {}, hist)
    assert GOOD["jury_prompts"][0]["text"] not in [q["text"] for q in p["jury_prompts"]] and len(p["jury_prompts"]) >= 3

def test_hud_labels_monotonic_clocks_and_bounds():
    spec = [{"t": 1, "type": "clock", "label": "Time left", "value": 60}, {"t": 2, "type": "clock", "label": "Time left", "value": 50},
            {"t": 3, "type": "clock", "label": "Time left", "value": 55}, {"t": 1.5, "type": "price", "label": "Price", "value": 1},
            {"t": 4, "type": "price", "label": "Price", "value": "abc"}]
    out, iss = SHOW.hud_check(spec)
    assert [h["value"] for h in out] == [60, 50] and len(iss) == 3
    assert SHOW.hud_check("none") == ("none", []) and SHOW.hud_check("weird")[0] == "none"

def test_ip_and_real_person_guard():
    assert SHOW.ip_hits("A Sherlock-style detective") == ["sherlock"] and SHOW.ip_hits("Einstein would say") == ["einstein"]
    assert not SHOW.ip_hits("Inspector Vale observes the evidence") and not SHOW.ip_hits("the houses of parliament")
    p, iss = SHOW.validate(dict(GOOD, charge="Moriarty stands accused"), {}, [])
    assert any("moriarty" in i for i in iss)

def test_character_bible_is_clean_seeded_once_and_chains_are_allow_listed():
    MG.setup(); n1 = len(core.store().rows("Characters")); assert n1 == 4 and SHOW.seed_characters() == 0
    assert not SHOW.bible_issues(core.store().rows("Characters"))
    assert SHOW.audio_chain_ok("highpass=f=70,acompressor=threshold=-18dB:ratio=2.5")
    assert not SHOW.audio_chain_ok("amovie=/etc/passwd") and not SHOW.audio_chain_ok("volume=$(rm)") and not SHOW.audio_chain_ok("")
    assert SHOW.bible_issues([{"id": "X", "name": "Little Tim", "philosophy": "a kid detective"}])

def test_tag_contract():
    plan = SHOW.validate(copy.deepcopy(GOOD), {}, [])[0]
    pre = "[DIRECTOR] " + "word " * 90 + "\n"
    good = (pre + "[JURY] Guilty or not? [EXHIBIT A] [METER -1 grimm] [METER +2 vale]\n[CLIPBAIT] [SKEPTIC] Pillows do not fly! [/CLIPBAIT]\n[JURY] Predict it. [JURY] A, B or C?")
    assert SHOW.check_tags(good, plan) == []
    assert any("CLIPBAIT" in i for i in SHOW.check_tags(good.replace("[/CLIPBAIT]", ""), plan))
    assert any("verdict" in i for i in SHOW.check_tags(good.replace("[METER +2 vale]", ""), plan))
    assert any("not in the show plan" in i for i in SHOW.check_tags(good + " [EXHIBIT H]", plan))
    assert any("first 30 s" in i for i in SHOW.check_tags("[JURY] x " + good, plan))
    assert SHOW.strip_tags("[EXHIBIT A] Look [METER +1 vale] here [JURY]") == "Look here"

def test_showrunner_call_carries_the_plan_and_off_is_exactly_v811(monkeypatch, setting):
    seen = []; real = ROOM.ask
    monkeypatch.setattr(ROOM, "ask", lambda role, system, prompt, **k: (seen.append((k.get("fake_key"), str(system))), real(role, system, prompt, **k))[1])
    MG.setup(); d = {"strategies": {"family": "F08_rules"}, "playbook": {}}
    sp = ROOM.scout_and_pick(d, ROOM.context(), "EPSHOW")
    sr = [s for k, s in seen if k == "showrunner"]
    assert sr and "REALITY ON TRIAL" in sr[0] and sp["show_plan"]["exhibits"] and core.store().rows("Show_Log")[-1]["episode_id"] == "EPSHOW"
    assert not [k for k, s in seen if k not in ("scout", "showrunner", "premise_judge_claude", "premise_judge_gemini", None)]   # no new AI role
    seen.clear(); setting("SHOW_MODE", "off"); n = len(core.store().rows("Show_Log"))
    sp2 = ROOM.scout_and_pick(d, ROOM.context(), "EPOFF")
    assert all("REALITY ON TRIAL" not in s for k, s in seen) and len(core.store().rows("Show_Log")) == n and "show_plan" in sp2   # fake echoes it; nothing validated or logged
