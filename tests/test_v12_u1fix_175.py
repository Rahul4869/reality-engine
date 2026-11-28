"""U1 fix 175 (open issue 195): NO CAST NAME REACHES AN F1 / F3 WRITER OUTSIDE THE CANON. Issue 77 closed the canon's road; the two roads left were the
house rules ('Dr. Grimm is theatrical, never cruel' in every brief) and a Palace item that names the cast (the seed fmt.case_files: 'Dr. Grimm fails in
at most 40% of the cases'). The house rules name no one; canon.cast_left_out leaves every non-canon item that holds a cast member's full name out of a
writer's playbook in a format with no cast. The trial keeps its cast sentence and its item; D9 still gets the compilation item."""
import pytest
from whatifs import core, models as M, formats as FMT, room as ROOM, prompts as P, show as SH, manage as MG
from whatifs.sampler import draw as DRAW
from whatifs.org import palace as PAL, canon as CANON, runner as RUN, wraps as WR

CASE_FILES = PAL.item_id("seed:fmt.case_files")
NO_CAST = [k for k, f in FMT.FORMATS.items() if not f["show"]]
TRIAL = [k for k, f in FMT.FORMATS.items() if f["show"]]


@pytest.fixture
def palace(setting):
    MG.setup(); setting("ORG_SINCE", "2026-01-01T00:00:00Z")
    st = core.store(); PAL.ensure_seed(st=st); CANON.ensure_cast(st)
    aired = "EP202611010900"
    CANON.record(aired, {"spine": {"premise": "What if the Moon walked out?", "show_plan": {"charge": "The Moon is charged with leaving.", "verdict": {"winner": "vale"}}},
                         "script": {"script": "x"}})
    assert CANON.on_air(aired, "vid-1")
    names = [c["name"] for c in SH.characters()]                                           # read from the bible the canon mirrors, never typed
    other = next(n for n in names if n.lower() not in PAL.get(CASE_FILES)["summary"].lower())
    planted = PAL.add({"key": "t.names.cast", "kind": "technique", "title": "A cold open that works", "summary": f"Open on the object; then let {other} react to it once, briefly.",
                       "departments": ["D4"], "stages": ["writing"], "topic_tags": ["opening"], "evidence": [{"source": "a test", "date": "2026-11-20", "type": "research digest"}]},
                      "build", status="accepted")["id"]
    return {"case": CANON.case_id(aired), "planted": planted}


def _writer_brief(monkeypatch, setting, fmt, ep):
    """The whole system text the room's writer really sends in `fmt` - after the department runner put its playbook into it."""
    seen = []
    monkeypatch.setattr(M, "ASK_TAPS", list(M.ASK_TAPS) + [lambda task, system, prompt: (seen.append(str(system)) if str(task) == "writer" else None, system)[1]])
    setting("FORMAT_FORCE", fmt); d = DRAW(ep, "collective"); d["format"] = fmt
    with FMT.using(fmt): RUN.work("D4", "write", ep, lambda b: ROOM.run_room(d, ep), measure=WR.m_room)
    assert seen, fmt
    return seen[0]


def test_the_house_rules_name_no_one_of_the_cast():
    low = P.HOUSE.lower()
    assert "no cruelty aimed at the viewer." in P.HOUSE and not [c["name"] for c in SH.characters() if c["name"].lower() in low]


def test_an_item_naming_the_cast_is_left_out_of_a_writers_playbook_outside_a_trial(palace):
    rs = PAL.rows(); cast = set(CANON.cast_ids())
    assert NO_CAST and TRIAL
    for fmt in NO_CAST:
        left = CANON.cast_left_out("D4", fmt)
        assert cast <= left and CASE_FILES in left and palace["planted"] in left and palace["case"] not in left, fmt      # the canon's case stays
        pb = PAL.playbook("D4", rs=rs, leave_out=left, record=False)
        assert CASE_FILES not in pb["items"] and palace["planted"] not in pb["items"] and palace["case"] in pb["items"], fmt
        assert CANON.cast_left_out("D9", fmt) == set() and CANON.cast_left_out("D8", fmt) == set()
    for fmt in TRIAL:
        assert CANON.cast_left_out("D4", fmt) == set() and CASE_FILES in PAL.playbook("D4", rs=rs, leave_out=CANON.cast_left_out("D4", fmt), record=False)["items"]
    assert CASE_FILES in PAL.playbook("D9", rs=rs, record=False)["items"]                  # the compilations' department still has it


def test_the_writers_whole_brief_holds_no_cast_line_outside_a_trial_and_the_trial_keeps_its_own(palace, monkeypatch, setting):
    case_line = f"[{palace['case']}]"
    for n, fmt in enumerate(NO_CAST):
        brief = _writer_brief(monkeypatch, setting, fmt, f"EP2026112009{n:02d}")
        assert "Dr. Grimm is theatrical" not in brief and "Dr. Grimm fails" not in brief and f"[{palace['planted']}]" not in brief, fmt
        assert case_line in brief, fmt                                                       # the newest aired case and its line stay
    brief = _writer_brief(monkeypatch, setting, TRIAL[0], "EP202611201000")
    assert f"[{CASE_FILES}]" in brief and "theatrical, never cruel" in brief                # the trial's writer: its cast sentence and the item
