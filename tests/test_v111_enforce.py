"""v11.1 (K166): researched breakout rules are HARD-enforced (contract checks + automatic fixes + real timing). No keys, no network."""
import json
import pytest
from whatifs import core, enforce as EN, contract as CON, voice as VO

def _text(punch_every=3, n=24, send=True, awe=True):
    out = []
    for i in range(n):
        mk = ("[SEND] " if send and i == 4 else "") + ("[AWE] " if awe and i == 9 else "") + ("[PUNCH] " if i % punch_every == 1 else "")
        out.append(mk + f"VALE: line {i} with exactly ten words of narration here now ok")
    return "\n".join(out)

def test_joke_density_and_send_awe_are_hard_checks(setting):
    setting("WPM_ESTIMATE", "150")
    good = {"room": {"script": {"script": _text(3)}}}
    assert CON.p_joke_density(good)[0] == "PASS" and CON.p_send_awe(good)[0] == "PASS"
    few = {"room": {"script": {"script": _text(20)}}}
    assert CON.p_joke_density(few)[0] == "FAIL"
    assert CON.p_send_awe({"room": {"script": {"script": _text(3, send=False)}}})[0] == "FAIL"
    late = "\n".join(_text(3, awe=False).split("\n")[:23] + ["[AWE] VALE: the reveal arrives far too late in the episode"])
    assert CON.p_send_awe({"room": {"script": {"script": late}}})[0] == "FAIL"

def test_markers_are_never_spoken_and_punchlines_get_a_real_pause(setting):
    setting("PUNCH_PAUSE_S", "0.5")
    units = VO.parse_script("[DIRECTOR] One normal line here.\n[PUNCH] [SKEPTIC] And this is the joke.\n[SEND] [AWE] [DIRECTOR] Wow.") if hasattr(VO, "parse_script") else None
    src = open("whatifs/voice.py", encoding="utf-8").read()
    assert "PUNCH|SEND|AWE" in src and 'pending_gap += _S("PUNCH_PAUSE_S", float)' in src
    from whatifs import show as SH
    assert SH.SHOW_TAG_RE.sub("", "[PUNCH] [SEND] [AWE] hello").strip() == "hello"

def test_v6_flags_a_punchline_without_its_pause(setting):
    units = [{"start": 0, "end": 2.0, "text": "a"}, {"start": 2.05, "end": 3, "text": "b", "show": ["[PUNCH]"]}]
    for u in units: u["punch"] = any("PUNCH" in s for s in u.get("show", []))
    n, bad = EN.v6_punch_timing(units); assert n == 1 and bad
    units[1]["start"] = 2.5; assert EN.v6_punch_timing(units)[1] == []

def test_impact_check_fails_without_a_hook_and_records_the_map(setting):
    units = [{"start": 0, "end": 4, "text": "Long ago there was a field.", "speaker": "WITNESS"}, {"start": 4.6, "end": 6, "text": "It was green.", "speaker": "DIRECTOR", "show": ["[PUNCH]"]}]
    st, ev = CON.p_impact({"units": units, "shots": [], "ep": "EPI1"})
    assert st == "FAIL" and "V1" in ev
    units[0]["text"] = "What if YOU vanished?"
    units.append({"start": 25, "end": 27, "text": "Exhibit A: a map?", "speaker": "WITNESS"})        # a different episode, not a copy
    st, ev = CON.p_impact({"units": units, "shots": [], "ep": "EPI2"})
    assert st == "PASS", ev
    assert len(core.store().rows("Impact_Maps")) == 2

def test_variety_blocks_a_copy_of_a_recent_episode(setting):
    sig = [1, 2, 0, 3, 1, 1, 0, 2]
    core.store().append("Impact_Maps", [{"ts": core.iso(), "episode_id": "OLD", "signature": json.dumps(sig), "summary": "{}"}])
    assert EN.v9_variety(sig, "NEW") > 0.99

def test_brain_evidence_reaches_the_writer_and_retired_is_banned(monkeypatch, setting):
    from whatifs import brain as BR
    monkeypatch.setattr(BR, "verdicts", lambda: {"proven": [{"family": "hook", "level": "verdict_first", "format": "long", "p_beats_baseline": 0.93, "n_videos": 7}],
                                                 "promising": [], "retired": [{"family": "hook", "level": "countdown", "format": "long", "p_beats_baseline": 0.2, "n_videos": 6}]})
    b = EN.brain_block("long"); assert "PROVEN" in b and "verdict_first" in b and "RETIRED" in b and "countdown" in b
    assert CON.p_no_retired({"d": {"hook_archetype": "countdown"}})[0] == "FAIL" and CON.p_no_retired({"d": {"hook_archetype": "verdict_first"}})[0] == "PASS"
    assert CON.p_brain_playbook({"d": {"brain_block": b, "brain_block_in_brief": True}})[0] == "PASS"
    assert CON.p_brain_playbook({"d": {"brain_block": b, "brain_block_in_brief": False}})[0] == "FAIL"

def test_idea_gate_needs_outlier_evidence_once_data_exists(setting):
    st = core.store(); setting("IDEA_MIN_SIGNALS", "2")
    ctx = {"room": {"spine": {"premise": "What if the Moon left?"}}}
    assert CON.p_idea_evidence(ctx)[0] == CON.NA                                       # no outlier data yet: honest NA, not a fake pass
    st.append("Demand_Signals", [{"video_id": f"v{i}", "multiple": 6 + i} for i in range(3)])
    st.append("Premise_Bench", [{"bench_id": "B1", "premise": "What if the Moon left?", "status": "USED", "demand_json": json.dumps({"source_video_id": "v1"})}])
    assert CON.p_idea_evidence(ctx)[0] == "PASS"
    st.append("Premise_Bench", [{"bench_id": "B2", "premise": "What if socks were alive?", "status": "USED", "demand_json": "{}"}])
    assert CON.p_idea_evidence({"room": {"spine": {"premise": "What if socks were alive?"}}})[0] == "FAIL"

def test_visual_change_holds_a_still_that_sits_too_long_and_overload(setting, monkeypatch):
    import whatifs.shotplan as SPL
    units = [{"start": 0, "end": 10}, {"start": 10, "end": 14}]
    shots = [{"type": "still"}, {"type": "still"}]
    monkeypatch.setattr(SPL, "pieces_for", lambda dur, typ, opening=False, episode=None: 1)          # a renderer that would NOT micro-cut
    assert CON.p_visual_change({"units": units, "shots": shots, "ep": "E"})[0] == "FAIL"
    monkeypatch.setattr(SPL, "pieces_for", lambda dur, typ, opening=False, episode=None: max(1, int(dur // 2.5)))
    assert CON.p_visual_change({"units": units, "shots": shots, "ep": "E"})[0] == "PASS"
    monkeypatch.setattr(SPL, "pieces_for", lambda dur, typ, opening=False, episode=None: int(dur * 3))   # 3 changes per second = overload
    assert "V5" in CON.p_visual_change({"units": units, "shots": shots, "ep": "E"})[1]
    quick = [{"start": 0, "end": 0.9, "text": "Wait."}, {"start": 0.9, "end": 1.8, "text": "What?"}, {"start": 1.8, "end": 6, "text": "Go on then."}]
    monkeypatch.setattr(SPL, "pieces_for", lambda dur, typ, opening=False, episode=None: 1)
    assert "V5" not in CON.p_visual_change({"units": quick, "shots": [{"type": "still"}] * 3, "ep": "E"})[1]           # quick banter is not overload

def test_real_micro_cut_rule_meets_the_four_second_bar_even_for_long_lines():
    from whatifs.shotplan import pieces_for
    for dur in (3, 7, 13, 26, 40, 60):
        assert dur / pieces_for(dur, "still", False, "E") <= 4.0 + 1e-6, dur

def test_breakout_bar_blocks_below_80(monkeypatch, setting):
    from whatifs import breakout as BRK
    monkeypatch.setattr(BRK, "score", lambda *a, **k: {"score": 72.0, "weakest": "story"})
    st, ev = CON.p_breakout_bar({"d": {}}); assert st == "FAIL" and "weakest: story" in ev
    monkeypatch.setattr(BRK, "score", lambda *a, **k: {"score": 86.0, "weakest": "idea"})
    assert CON.p_breakout_bar({"d": {}})[0] == "PASS"

def test_every_owner_requirement_in_the_matrix_is_wired_to_a_real_check():
    """docs/CURRENT/ENFORCEMENT_MATRIX.md lists every owner requirement with the code that enforces it; this fails if any named check / function is missing."""
    import re, importlib
    rows = [l for l in open("docs/CURRENT/ENFORCEMENT_MATRIX.md", encoding="utf-8").read().splitlines() if l.startswith("| ") and "`" in l]
    ids = {f for f, *_ in CON.FEATURES}
    missing = []
    for l in rows:
        for ref in re.findall(r"`([^`]+)`", l):
            if ref.startswith("contract:"):
                if ref.split(":", 1)[1] not in ids: missing.append(ref)
            elif ref.startswith("fn:"):
                mod, fn = ref[3:].rsplit(".", 1)
                if not hasattr(importlib.import_module(mod), fn): missing.append(ref)
    assert len(rows) >= 25 and not missing, missing

def test_promise_survives_the_animation_director(setting):
    """v11.1 fix: ANIM.apply re-places the animated scenes; the opening one must still carry the thumbnail's promise (else promise_paid holds)."""
    src = open("whatifs/episode.py", encoding="utf-8").read()
    i = src.index("ANIM.apply(shots, units, plan)"); j = src.index("ROOM.promise_shot(shots, units, S_.get(\"pkg\")", i)
    assert j - i < 400
    from whatifs import room as ROOM
    setting("PROMISE_SHOT_ON", "TRUE"); setting("OPENING_WINDOW_SEC", "45")
    units = [{"start": 0, "end": 4, "text": "a"}, {"start": 4, "end": 9, "text": "b"}]
    shots = [{"type": "kling", "prompt": "x"}, {"type": "still"}]
    out = ROOM.promise_shot(shots, units, {"thumb_prompt": "a floating pillow"})
    assert out[0].get("promise") and "floating pillow" in out[0]["prompt"]

def test_sub_second_lines_without_their_own_picture_continue_the_previous_shot(setting, monkeypatch):
    import whatifs.shotplan as SPL
    monkeypatch.setattr(SPL, "pieces_for", lambda dur, typ, opening=False, episode=None: max(1, int(dur // 2.5)))
    units = [{"start": 0, "end": 3, "text": "Day 1"}, {"start": 3, "end": 3.6, "text": "2!"}, {"start": 3.6, "end": 4.2, "text": "3!"}, {"start": 4.2, "end": 4.8, "text": "4 kg"},
             {"start": 4.8, "end": 8.0, "text": "and so on"}]
    shots = [{"type": "still"}] * 5
    assert "V5" in CON.p_visual_change({"units": units, "shots": shots, "ep": "E", "merged_units": [99]})[1]      # every flash a new picture: overload
    assert CON.p_visual_change({"units": units, "shots": shots, "ep": "E", "merged_units": [1, 3]})[0] == "PASS"   # folded as the renderer does
    src = open("whatifs/episode.py", encoding="utf-8").read()
    assert "MERGED_UNITS.add(i)" in src and 'S("UNIT_MERGE_SEC", float)' in src

