import json, re
import pytest
from whatifs import tableread as TR, core, prompts as P
from whatifs.data import CRAFT_BY_ROLE, CRAFT


@pytest.fixture(autouse=True)
def _room_v1():
    """v11: the table read, department memos and the director read belong to room v1 (room v2 drops them by design); these tests pin v1."""
    from whatifs import core as _core
    _core.set_setting("ROOM_MODE", "v1"); yield

def test_default_mode_is_on_and_writer_room_clearance_is_enabled():
    assert core.DEFAULTS["TABLE_READ_MODE"][0] == "on"
    assert TR.active_arm("EP1") == ("on", "on")

@pytest.mark.parametrize("mode,arm", [("on", "on"), ("TRUE", "on"), ("off", "off"), ("", "off"), ("nonsense", "off")])
def test_modes(mode, arm): assert TR.active_arm("EP1", mode)[0] == arm

def test_alternate_is_deterministic_and_roughly_balanced():
    arms = [TR.active_arm(f"EP2026{i:05d}", "alternate")[0] for i in range(400)]
    assert arms == [TR.active_arm(f"EP2026{i:05d}", "alternate")[0] for i in range(400)]
    assert 150 < arms.count("on") < 250

def test_clean_objections_keeps_only_well_formed_ones():
    raw = {"objections": [{"to": "WRITER", "objection": "  too   early ", "request": "move it"},
                          {"to": "PACKAGER", "objection": "self", "request": ""},          # to own department
                          {"to": "NOBODY", "objection": "x", "request": ""},
                          {"to": "DIRECTOR + DP", "objection": "", "request": "y"},
                          "not a dict", {"to": "EDITOR + SOUND", "objection": "a" * 900, "request": "b" * 900},
                          {"to": "WRITER", "objection": "3", "request": ""}, {"to": "WRITER", "objection": "4", "request": ""}]}
    out = TR.clean_objections(raw, "PACKAGER")
    assert out[0] == {"from": "PACKAGER", "to": "WRITER", "objection": "too early", "request": "move it"}
    assert all(o["to"] in TR.ROLES and o["to"] != "PACKAGER" for o in out) and len(out) == 3
    assert all(len(o["objection"]) <= 300 and len(o["request"]) <= 300 for o in out)
    assert TR.clean_objections(None, "WRITER") == [] and TR.clean_objections({"objections": "str"}, "WRITER") == []

def test_clean_notes():
    n = TR.clean_notes({"notes": [{"beat": "2", "note": " hold  still "}, {"beat": "x", "note": "n"}, {"note": ""}, 5] + [{"beat": 1, "note": "z"}] * 9})
    assert n[0] == {"beat": 2, "note": "hold still"} and n[1]["beat"] == 0 and len(n) == 6

def test_objections_round_sends_one_job_a_role_with_research_free_craft_and_no_placeholders():
    seen = []
    def many(jobs):
        seen.extend(jobs); return [{"objections": [{"to": "WRITER", "objection": "o", "request": "r"}]} for _ in jobs]
    memos = {r: {"big_idea": f"idea of {r}"} for r in TR.ROLES}
    objs = TR.objections_round(memos, {"premise": "p"}, "EPT", many)
    assert len(seen) == len(TR.ROLES) == 5 and len(objs) == 4          # the WRITER may not object to itself (five roles: the reel producer left with the cut-down reels)
    for j in seen:
        assert "@@" not in j["system"] and j["fake_key"] == "memo2"
    w = next(j for j in seen if "ROLE: WRITER" in j["system"])
    assert "idea of PACKAGER" in w["system"] and "idea of WRITER" not in w["system"].split("OTHER DEPARTMENTS")[1]    # others only
    assert CRAFT_BY_ROLE["WRITER"][:40] in w["system"]

def test_round_and_notes_fail_forward():
    boom = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    assert TR.objections_round({r: {} for r in TR.ROLES}, {}, "E", boom) == []
    assert TR.director_notes("script", "look", "E", boom) == []

def test_director_notes_validated_and_prompt_has_no_placeholders():
    got = {}
    def ask(role, system, prompt, **k): got["s"] = system; return {"notes": [{"beat": 1, "note": "hold on silence"}, {"note": ""}]}
    n = TR.director_notes("## BEAT 1\n[calm] x", "cold light", "E", ask)
    assert n == [{"beat": 1, "note": "hold on silence"}] and "@@" not in got["s"] and "cold light" in got["s"]
    assert "none" == TR.notes_text([]) and "Beat 1: a" == TR.notes_text([{"beat": 1, "note": "a"}])

def test_every_department_has_craft_notes_and_none_quote_a_work():
    assert set(CRAFT_BY_ROLE) == set(TR.ROLES)
    for r, t in CRAFT_BY_ROLE.items(): assert len(t) > 80, r
    assert "never copy" in P.MEMO.lower() or "never copy a work" in P.MEMO

def _spy(monkeypatch):
    from whatifs import room, models
    seen = []
    real = models.ask
    def spy(role, system, prompt, **kw):
        seen.append((kw.get("fake_key"), system)); return real(role, system, prompt, **kw)
    monkeypatch.setattr(room, "ask", spy); monkeypatch.setattr(models, "ask", spy)
    return seen

def _run_room(episode="EPTR1"):
    from whatifs import manage as MG, room
    from whatifs.sampler import draw as DRAW
    MG.setup()
    return room.run_room(DRAW(episode, "collective"), episode)

def test_room_with_table_read_off_has_one_round_and_no_leftover_placeholders(monkeypatch, setting):
    setting("TABLE_READ_MODE", "off")      # v8.1: the shipped default is now "on", so this test states the arm it checks
    seen = _spy(monkeypatch)
    r = _run_room()
    keys = [k for k, _ in seen]
    assert "memo2" not in keys and "director_read" not in keys and r["table_read"]["arm"] == "off" and r["director_notes"] == []
    assert [s for k, s in seen if k == "bible"][0].count("none (no table read this time)") == 1
    assert all("@@" not in s for _, s in seen), [k for k, s in seen if "@@" in s]
    rows = core.store().rows("Table_Read"); assert len(rows) == 1 and rows[0]["kind"] == "status" and rows[0]["arm"] == "off"

def test_room_with_table_read_on_runs_round_two_before_the_bible_and_director_read_after_the_script(monkeypatch, setting):
    setting("TABLE_READ_MODE", "on"); seen = _spy(monkeypatch)
    r = _run_room("EPTR2")
    keys = [k for k, _ in seen]
    assert keys.index("memo2") < keys.index("bible") < keys.index("writer") < keys.index("director_read")
    assert "-> WRITER" in [s for k, s in seen if k == "bible"][0]                      # objections reached the bible
    assert r["director_notes"] and r["table_read"] == {"mode": "on", "arm": "on"}
    assert all("@@" not in s for _, s in seen)
    kinds = {x["kind"] for x in core.store().rows("Table_Read")}; assert kinds == {"objection", "director_note"}
    import os; assert os.path.exists(os.path.join(core.WORK, "EPTR2", "table_read.json"))

def test_director_notes_reach_the_shot_planning_prompt(monkeypatch, setting):
    setting("TABLE_READ_MODE", "on"); from whatifs import room as ROOM
    r = _run_room("EPTR3"); seen = _spy(monkeypatch)
    units = [{"i": i, "text": f"line {i}", "tag": "none", "start": i, "end": i + 1} for i in range(4)]
    ROOM.plan_shots(r, units, {"ptype": "collective"}, {"kling": 1, "living": 1}, "EPTR3")
    s = [s for k, s in seen if k == "director"][0]
    assert "The opening object must be shown close" in s and "@@" not in s

def test_all_other_prompts_have_no_leftover_placeholders(monkeypatch):
    from whatifs import room as ROOM
    r = _run_room("EPTR4"); seen = _spy(monkeypatch)
    units = [{"i": i, "text": f"line {i}", "tag": "none", "start": i, "end": i + 1} for i in range(4)]
    ROOM.plan_shots(r, units, {"ptype": "collective", "strategies": {"title": "N1_what_if", "thumb": "T1_object_scale"}}, {"kling": 1, "living": 1}, "EPTR4")
    d = {"strategies": {"title": "N1_what_if", "thumb": "T1_object_scale"}}
    ROOM.package(r, [("0:00", "Intro")], d, "EPTR4"); ROOM.extend(r, "## BEAT 1\n[calm] a b c", 50, "EPTR4")
    ROOM.continuity({"x": 1}, "EPTR4")
    assert len(seen) >= 4 and all("@@" not in s for _, s in seen), [k for k, s in seen if "@@" in s]
    assert any("CRAFT REMINDERS" in s and CRAFT["packager"][:30] in s for k, s in seen if k == "packager")

def test_research_reaches_every_department_memo(monkeypatch):
    seen = _spy(monkeypatch)
    _run_room("EPTR5")
    memos = [s for k, s in seen if k == "memo"]
    assert len(memos) == 5 and all("OBSERVED SIGNALS" in s or "RESEARCH NOT AVAILABLE" in s for s in memos)

def test_budget_plan_includes_table_read_cost_only_when_active(setting):
    from whatifs import episode as EP
    d = {"episode_id": "EPB", "stills": 50, "living": 8, "kling": 3}
    setting("TABLE_READ_MODE", "off"); base = EP.est_cost_inr(d); setting("TABLE_READ_MODE", "on"); on = EP.est_cost_inr(d)
    assert on - base == pytest.approx(core.S("TABLE_READ_EXTRA_INR", float))

# ---------------- A/B report ----------------
def _eps(arm_scores):
    eps, an = [], []
    for i, (arm, sc) in enumerate(arm_scores):
        eid = f"E{i}"; eps.append({"episode_id": eid, "draw_json": json.dumps({"table_read": {"arm": arm}}), "cost_inr": 200 + (20 if arm == "on" else 0)})
        an.append({"episode_id": eid, "score": sc, "ret30": 0.6, "avg_view_pct": 40})
    return eps, an

def test_abtest_refuses_to_conclude_with_too_little_data():
    rep = TR.abtest_report(*_eps([("on", .5)] * 3 + [("off", .5)] * 3))
    assert rep["verdict"].startswith("NOT ENOUGH DATA") and rep["p_value"] is None

def test_abtest_identical_groups_are_not_significant_and_separated_groups_are():
    same = TR.abtest_report(*_eps([("on", .5 + .01 * (i % 3)) for i in range(10)] + [("off", .5 + .01 * (i % 3)) for i in range(10)]))
    assert same["p_value"] >= 0.5 and "not distinguishable from chance" in same["verdict"]
    diff = TR.abtest_report(*_eps([("on", .7 + .001 * i) for i in range(10)] + [("off", .4 + .001 * i) for i in range(10)]))
    assert diff["p_value"] < 0.05 and "extra cost about +20" in diff["verdict"]

def test_abtest_ignores_episodes_without_an_arm_or_analytics():
    eps, an = _eps([("on", .5)] * 6 + [("off", .5)] * 6)
    eps.append({"episode_id": "OLD", "draw_json": "{}"}); eps.append({"episode_id": "BAD", "draw_json": "not json"})
    rep = TR.abtest_report(eps, an); assert rep["n"] == {"on": 6, "off": 6}

def test_abtest_main_prints(capsys):
    TR.abtest_main(); assert "TABLE READ A/B REPORT" in capsys.readouterr().out

