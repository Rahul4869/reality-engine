"""v9.2 item 2: Kling on the stakes (never adjacent, never a plain line), scene-aware POV anchors with variety, tiny lines -> reaction cutaways."""
import re
import numpy as np
import pytest
from whatifs import core, shotplan as SP, immersion as IM, v91 as V91

def _units():
    us = []
    lines = ["Picture your apartment at night.", "Light now moves at walking speed.", "Nothing stores this one.", "Fine.", "A fifth.",
             "The kettle glows in the kitchen.", "You brush your teeth at the mirror.", "Your reflection is 1.4 seconds late.", "Run backward down the hallway!",
             "The reflection un-brushes its teeth.", "Mm.", "Guilty or not?", "The window still shows yesterday.", "So light is slow, and you are fast.", "Case closed."]
    for i, t in enumerate(lines):
        us.append({"i": i, "text": t, "start": float(i * 6), "end": float(i * 6 + 5), "tag": "reveal" if i in (7, 12) else ("tension" if i == 8 else "none"),
                   "speaker": "SKEPTIC" if i in (3, 4) else ("JUDGE" if i in (10, 11) else "DIRECTOR"), "show": []})
    us[9]["show"] = ["[CLIPBAIT]", "[METER +3 VALE]"]; us[9]["end"] = 59.0; us[1]["show"] = ["[EXHIBIT A]"]; us[11]["show"] = ["[JURY]"]
    return us

def test_kling_goes_to_the_stakes_never_adjacent_never_plain(setting):
    us = _units(); shots = [{"type": "kling" if i in (2, 3, 4) else "still", "prompt": "p"} for i in range(len(us))]
    out = IM.apply(shots, us, {}, {"kling": 3}, "EPK")
    k = sorted(i for i, s in enumerate(out) if s["type"] == "kling")
    assert len(k) == 3 and 9 in k and 12 in k                                     # clip-bait + biggest meter swing, and the final reveal
    assert all(b - a > 1 for a, b in zip(k, k[1:])) and 2 not in k                # never adjacent; never the plain beat-2 line
    setting("KLING_STAKES_ON", "FALSE"); old = IM.apply(shots, us, {}, {"kling": 3}, "EPK2")
    assert sorted(i for i, s in enumerate(old) if s["type"] == "kling") != k        # the switch restores v9.1 placement

def test_stake_scores_skip_plain_explanations():
    sc = SP.stakes(_units()); assert sc[2] == 0 and sc[9] >= 5 and sc[12] >= 3

def test_scene_aware_anchors_whole_words_and_variety():
    assert SP.scene_of("bring the light around") == "" and SP.scene_of("a light wave hits") == "water"
    assert SP.scene_of("the kettle glows") == "kitchen" and SP.scene_of("brush your teeth at the mirror") == "bathroom"
    us = _units(); shots = [{"type": "still", "prompt": u["text"]} for u in us]
    SP.assign_anchors(shots, us, "EPA")
    a = [s["pov"]["anchor"] for s in shots]
    assert all(x != y for x, y in zip(a, a[1:])) and all(s["pov"]["lens"] != t["pov"]["lens"] for s, t in zip(shots, shots[1:]))
    assert "helmet" not in shots[5]["pov"]["anchor"] and shots[5]["pov"]["scene"] == "kitchen"
    out = IM.apply([{"type": "still", "prompt": u["text"]} for u in us], us, {}, {"kling": 0}, "EPA")
    v = SP.prompt_variety(out); assert v["top_anchor_share"] <= 0.35 and v["top_opening_share"] <= 0.35, v

def _approved_cast():
    """v12 V2d-b: a character is drawn or absent - a cutaway is planned only for a character with approved (LOCKED) art."""
    from whatifs import core
    core.store().append("Character_Sheets", [{"ts": "t", "character": c, "expression": "neutral", "hash": c, "prompt": "", "file": "sheet.png", "status": "LOCKED", "approved_at": "t"}
                                             for c in ("VALE", "GRIMM", "ROSA", "ARCHIVIST")])

def test_tiny_lines_become_reaction_cutaways_not_bought(setting):
    us = _units(); shots = [{"type": "still", "prompt": u["text"]} for u in us]
    out0, n0 = SP.reaction_shots([dict(s) for s in shots], us)
    assert n0 == 0 and all(s["type"] == "still" for s in out0)                    # v12 V2d-b: no approved art = no cutaway of that character: every line keeps its picture
    _approved_cast()
    out, n = SP.reaction_shots(shots, us)
    assert n == 4 and out[3]["type"] == "reaction" and out[3]["speaker"] == "SKEPTIC" and out[10]["type"] == "reaction" and out[11]["type"] == "still"   # a jury prompt stays
    assert out[9]["type"] == "still"                                               # a clip-bait line is never a cutaway

def test_the_code_that_drew_a_shape_in_place_of_a_character_is_gone():
    """v12 V2d-b (the owner, 11 Nov 2026, on the first live video: a flat black shape with two ovals and a name): nothing in the shot-plan module can
    draw a stand-in for a character any more, and the renderer has no call to one."""
    import inspect
    from whatifs import episode as EPI
    assert not hasattr(SP, "reaction_frame") and not hasattr(SP, "reaction_segment")
    src = inspect.getsource(EPI._render); assert "reaction_segment" not in src and "job.absent += 1" in src

def test_safe_mode_restores_v91_shot_plan(setting):
    setting("V91_SAFE_MODE", "TRUE")
    assert not V91.on("KLING_STAKES_ON") and not V91.on("POV_VARIETY_ON") and not V91.on("REACTION_SHOTS_ON")
