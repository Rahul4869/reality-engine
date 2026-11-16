"""v12 V1c - the floor, his verdict and the maker's line: HIS VERDICT AND HIS LINE - two whole productions (3.10).
MOVED WORD FOR WORD from tests/test_v12_floor.py by the V1c repair (red round 1, open issues 224 and 225; the dispatcher's ruling 4 (C)):
the proof's serial runner (`shim/minitest.py`) cuts a file at 900 s, and that file took 643 s alone once all its tests ran - so its four
longest whole productions run in tests/test_v12_floor_holds.py and tests/test_v12_floor_his_word.py, two each. Every test function below is
that file's text, unchanged; its helpers, fixtures and episode ids (OWN_IDS) stay in tests/test_v12_floor.py and are imported from there."""
from whatifs import contract as CON
from whatifs import core
from whatifs import episode as EP
from whatifs import room as ROOM_
import json
import os
from tests.test_v12_floor import GOOD_LINES, OWN_IDS, _MK, _VER, _led, _mkrow, _start_e2e, _vrow

def test_a_second_long_video_after_his_thumbs_up_on_the_first_is_judged_beside_it(monkeypatch, setting):
    """3.10's second whole production: his thumbs-up on a film the floor passed makes it a reference; the next film's session holds it (R1) and passes."""
    from tests import test_v12_opening_e2e as E2E
    from tests.paid_calls import watch
    from whatifs import ladder as LAD
    V = _VER(); _start_e2e(monkeypatch, setting); setting("OWNER_VERDICT_ON", "TRUE"); ep1, ep2 = OWN_IDS[4], OWN_IDS[5]
    r = EP.produce(E2E._slot(10), episode_id=ep1); assert r.get("ok"), r
    assert _led(ep1)["viewer_floor"][0] == CON.PASS
    core.store().update("Episodes", "episode_id", ep1, {"status": "LIVE"}); V.record(ep1, "up", "", "tap")
    view1 = next(x for x in core.store().rows("Floor_Log") if x["episode_id"] == ep1)["view"]; assert V.references(ep2) == [(ep1, view1)]
    setting("SCRIPT_SIMILARITY_MAX", "1")                                     # a NAMED test setting: the offline writers' one text is 62% like itself (V2b's 6b) - check `originality` has its own tests
    LAD.override("owner", "make it anyway"); c = watch(monkeypatch)
    r = EP.produce(E2E._slot(40), episode_id=ep2); assert r.get("ok"), r
    led = _led(ep2); assert led["viewer_floor"][0] == CON.PASS and led["viewer_floor"][1].endswith(", and lost to 1 video(s) you approved"), led["viewer_floor"]
    rows = [x for x in core.store().rows("Floor_Log") if x["episode_id"] == ep2]
    assert len(rows) == 4 and all("R1" in json.loads(x["items"]).values() for x in rows) and c["watch:floor_gemini"] == 2 and c["watch:floor_claude"] == 2

def test_a_long_video_about_a_promoted_short_ends_on_his_line_and_pays_nothing_for_it(monkeypatch, setting, tmp_path):
    """3.10's first whole production, as far as steps 3 and 4 reach: his line is taken from the promoted Short's topic, the film ends on it
    word for word after the short lead-in (F1 ends on its question), the Director and the continuity judge never see it, no picture, scene or clip is bought
    for it - the same film on a Sheet without his line pays the same and has its scenes where this one has them. STEP 4 (one story, changed BY DESIGN and
    named in the record first): the thumbnail is the first picture of the Short the film opens on, the packager was told so, the opening is drawn once."""
    import shutil
    from tests import test_v12_opening_e2e as E2E
    from tests.paid_calls import watch
    from tools.sweep import climb
    from whatifs import ladder as LAD, models as M_
    from tests.conftest import OLD_CLIPS, OLD_MOTION, OLD_INSIDE, OLD_VIEW
    MK = _MK(); ep = OWN_IDS[6]; sid = "SH" + ep[2:]; line = GOOD_LINES[0]
    def go():                                                     # both Sheets under the same cells (a new Sheet starts from the shipped defaults: the test setup's cells first)
        for k, v in list(OLD_CLIPS.items()) + list(OLD_MOTION.items()) + list(OLD_INSIDE.items()) + list(OLD_VIEW.items()): setting(k, v)
        for k in list(OLD_CLIPS) + list(OLD_MOTION): setting(k, core.DEFAULTS[k][0])         # ... and the clip market and the motion ladder as shipped: no living clip may land on his line
        setting("MONTH_CAP_OVERRIDES", "")
        for k, v in (("FORMAT_FORCE", "F1"), ("INSIDE_ON", "TRUE"), ("ENDINGS_ON", "TRUE"), ("CAMERA_PATH_ON", "TRUE"), ("OWNER_VERDICT_ON", "TRUE"), ("MAKER_LINE_ON", "TRUE"),
                     ("ONE_STORY_ON", "TRUE")): setting(k, v)
        assert climb(core, ep) is True
    E2E._start(monkeypatch, setting); go()
    core.store().append("Owner_Verdicts", [_mkrow(sid, LAD.row(sid)["topic"], line, core.iso())])
    prompts = []; monkeypatch.setattr(M_, "ASK_TAPS", list(M_.ASK_TAPS) + [lambda task, system, prompt: (prompts.append((str(task), str(system) + " " + str(prompt))), system)[1]])
    gate = {}; real_run = CON.run
    monkeypatch.setattr(CON, "run", lambda stage, ctx, *a, **k: (gate.setdefault(stage, ctx), real_run(stage, ctx, *a, **k))[1])
    calls = []; real_ps = ROOM_.promise_shot                                                         # (V1c finish, C10) a spy: one story never re-aims a promise scene
    monkeypatch.setattr(ROOM_, "promise_shot", lambda *a_, **k_: (calls.append(1), real_ps(*a_, **k_))[1])
    paid = watch(monkeypatch); r = EP.produce(E2E._slot(10), episode_id=ep); a = dict(paid); assert r.get("ok"), r
    assert calls == []                                                                                                             # (V1c finish, C10) promise_shot never ran
    led = {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}
    assert not [k for k, v in led.items() if v[0] == CON.FAIL], led
    assert led["makers_line"] == (CON.PASS, f"the film ends on his own line, word for word: \"{line}\"; the same line is in the description")
    assert led["format_ending"][0] == CON.PASS and led["viewer_numbers"][0] == CON.PASS and led["camera_path"][0] == CON.PASS      # the script's checks judge the SCRIPT
    _out, S_, units = E2E._plan(ep); mk = S_["maker"]; k = MK.k(mk)
    assert (mk["line"], mk["ref"], mk["lead"]) == (line, sid, MK.LEAD_SHORT) and json.loads(_vrow(sid)["line_used"]) == {"ep": ep, "line": line}
    assert [u["text"] for u in units[-k:]] == MK.E(MK.LEAD_SHORT) + MK.E(line) and all(u["speaker"] == "DIRECTOR" for u in units[-k:])
    assert not [t for t, p in prompts if t in ("director", "critic") and (line in p or MK.LEAD_SHORT in p)]           # the Director and the continuity judge never see his words
    g = gate["script"]["shots"]; his = [i for i, s in enumerate(g) if s.get("maker")]
    assert his == list(range(len(units) - k, len(units))) and all(g[i]["type"] == "still" and not (g[i].get("anim") or g[i].get("buy") or g[i].get("promise")) for i in his)
    assert all(st_[1] == "still" and st_[2] != st_[0] for st_ in gate["final"]["maker_states"]) and gate["final"]["maker_states"]
    assert gate["final"]["maker"] == mk and json.loads(gate["final"]["maker_used"]) == {"ep": ep, "line": line} and gate["final"]["description"].count(MK.paragraph(line)) == 1      # (V1c finish, C10)
    scenes_a = [i for i, s in enumerate(g) if s.get("anim")]
    from whatifs import story as STORY                            # ---- step 4 (3.10): ONE STORY - the thumbnail is the picture this film opens on
    words = " ".join(str(S_["opening"].get("picture") or "").split()); pk = S_["pkg"]
    assert words and led["one_story"][0] == CON.PASS and led["one_story"][1].startswith(f"the thumbnail is drawn from the first picture of Short {sid}, the picture this video opens on: '"), led["one_story"]
    assert pk["thumb_prompt"] == words and pk["thumb_prompt_b"] == words + "; " + "a single pillow drifting past the Moon" and pk["one_story"] == {"short": sid, "words": words}      # (V1c finish, C9 (c)(5)) the offline packager's own B (it cannot see the system text: DESIGN QUESTION)
    assert [t for t, p in prompts if STORY.BRIEF.format(words=words) in p]                                            # the packager was told the scene
    assert not [i for i, s in enumerate(g) if not s.get("short") and (s.get("promise") or words in str(s.get("prompt") or ""))]      # drawn once: no shot outside the footage is re-aimed at it
    # ---- the same film on a Sheet without his line
    E2E._new_sheet(tmp_path, "sheet_noline.json"); shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True); go(); paid.clear(); gate.clear()
    r2 = EP.produce(E2E._slot(10), episode_id=ep); b = dict(paid); assert r2.get("ok"), r2
    led2 = {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}
    assert calls == [] and led2["makers_line"] == (CON.PASS, "he gave no line for this topic: none is spoken, none is written"), led2.get("makers_line")      # (V1c finish, C10)
    _o2, S2, units2 = E2E._plan(ep); assert S2["maker"] is None and len(units2) == len(units) - k
    assert {x: a.get(x, 0) for x in a if x.startswith(("image", "clip"))} == {x: b.get(x, 0) for x in b if x.startswith(("image", "clip"))}, (a, b)    # nothing is bought for his line
    assert scenes_a == [i for i, s in enumerate(gate["script"]["shots"]) if s.get("anim")]                           # and the scenes stand where they stand without it
