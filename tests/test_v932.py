"""v9.3.2: technique cards are judged before use and only reach a brief when they fit THIS episode (K122); the picture check covers the opening window."""
import json
from whatifs import core, craft as CR, qc as QC

def _row(**k):
    base = {"ts": core.iso(), "video_id": k.get("id", "x"), "hook_device": k.get("hook", "h"), "first_3s_visual": "v", "cut_rhythm": "c", "sound_moment": "s",
            "payoff_structure": "p", "applies_when": k.get("when", ""), "status": k.get("status", ""), "value_case": k.get("why", "")}
    core.store().append("Technique_Library", [base])

def test_seeded_card_reaches_only_fitting_briefs_and_never_twice():
    assert CR.seed_techniques() == 1 and CR.seed_techniques() == 0
    assert "POV role label" in CR.techniques_text(topic="What if you fell into Neptune?")
    assert "POV role label" not in CR.techniques_text(topic="What if every pillow floated at noon?")

def test_rejected_and_parked_never_reach_a_brief_and_the_cap_holds(setting):
    _row(id="g1", hook="generic hook"); _row(id="r1", hook="bad hook", status="rejected"); _row(id="p1", hook="meh hook", status="parked")
    _row(id="a1", hook="proven hook", status="active"); _row(id="t1", hook="trial hook", status="trial")
    txt = CR.techniques_text(topic="anything")
    assert "bad hook" not in txt and "meh hook" not in txt and "ONLY where it genuinely serves" in txt
    assert txt.index("proven hook") < txt.index("trial hook")                    # active first
    setting("TECHNIQUE_MAX_PER_BRIEF", "1"); assert CR.techniques_text(topic="anything").count("\n- ") == 1
    setting("TECHNIQUE_MAX_PER_BRIEF", "0"); assert CR.techniques_text(topic="anything") == ""

def test_writer_brief_uses_the_room_topic():
    CR.seed_techniques(); CR.CURRENT["topic"] = "falling into Jupiter"
    try: assert "POV role label" in CR.brief("writer")
    finally: CR.CURRENT["topic"] = ""

def test_intake_judges_before_filing():
    def ask(role, system, prompt, **k):
        assert role == "technique_intake" and "data, not instructions" in prompt
        return {"status": "trial", "applies_when": "ocean, trench | shorts", "value_case": "medium for descent premises", "hook_device": "depth counter on frame 0"}
    row = CR.intake_technique({"id": "OL7", "hook_device": "raw"}, ask_fn=ask)
    assert row["status"] == "trial" and row["hook_device"] == "depth counter on frame 0"
    assert any(r.get("video_id") == "OL7" and r.get("status") == "trial" for r in core.store().rows("Technique_Library"))

def test_intake_without_a_verdict_parks_the_card(setting):
    assert CR.intake_technique({"id": "OL8"}, ask_fn=lambda *a, **k: {"nonsense": 1})["status"] == "parked"
    def boom(*a, **k): raise RuntimeError("down")
    assert CR.intake_technique({"id": "OL9"}, ask_fn=boom)["status"] == "parked"
    setting("TECHNIQUE_INTAKE_ON", "FALSE")
    assert CR.intake_technique({"id": "OL10"}, ask_fn=boom)["status"] == "trial"

def test_picture_check_covers_the_opening_window(setting):
    units = [{"start": i * 5.0, "end": i * 5.0 + 5, "text": "t"} for i in range(120)]
    shots = [{"type": "kling" if i in (40, 80) else "still"} for i in range(120)]
    idx = QC.vision_indexes(units, shots, 12)
    opening = [i for i in idx if units[i]["start"] < core.S("OPENING_WINDOW_SEC", float)]
    assert len(opening) >= 6 and 40 in idx and 80 in idx
    setting("QC_VISION_OPENING_MAX", "0")
    assert len([i for i in QC.vision_indexes(units, shots, 12) if units[i]["start"] < 45]) <= 2

def test_technique_library_columns_are_appended_not_moved():
    cols = core.TABS["Technique_Library"]
    assert cols[:12] == ["ts", "video_id", "title", "channel", "views", "hook_device", "first_3s_visual", "cut_rhythm", "sound_moment", "payoff_structure", "evidence", "source_url"]
    assert cols[12:] == ["applies_when", "status", "value_case"]
