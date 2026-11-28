"""U1 fix 186 (open issue 209): ONE CAMERA IN A CAMERA-PATH REQUEST. In a format whose camera is a path, a shot of type "kling" gets the STILL's
first-person rule in its prompt (data.POV_STILL: "the camera IS the viewer's eyes"), never POV_KLING's "camera mounted on the moving object"; its
motion keeps the path's sentence (path.KLING_MOTION). Outside a camera-path format nothing changes."""
import pytest
from whatifs import data as DT, formats as FMT, immersion as IM, path as PATH

U = [{"text": f"Line {i} on the street.", "start": i * 5.0, "end": i * 5.0 + 4, "tag": "reveal" if i == 2 else "none"} for i in range(6)]


@pytest.fixture
def camera(setting):
    for k in ("CAMERA_PATH_ON", "INSIDE_ON", "ENDINGS_ON", "IMMERSION_ON"): setting(k, "TRUE")
    setting("POV_VARIETY_ON", "FALSE")
    yield
    FMT.use("")


def _plan():
    return [{"type": "kling", "prompt": "k"}, {"type": "living", "prompt": "l"}] + [{"type": "still", "prompt": "s"} for _ in range(4)]


def _apply(fmt, shots=None):
    shots = shots if shots is not None else _plan()
    with FMT.using(fmt): return shots, IM.apply([dict(s) for s in shots], U, {}, {"kling": 1}, "EP186")


def _rule(rule, before, i):
    """The rule as the data module says it, formatted with the anchor pov_prompt reads for this shot."""
    return rule.format(anchor=IM.anchor_for(str(before[i].get("prompt") or "") + " " + U[i]["text"]))


def test_a_kling_shot_of_a_path_format_carries_the_stills_first_person_rule_and_the_paths_motion(camera):
    for fmt in ("F1", "F3"):
        before, out = _apply(fmt); ks = [i for i, s in enumerate(out) if s["type"] == "kling"]
        assert ks, (fmt, out)
        for i in ks:
            p = out[i]["prompt"]
            assert p.startswith(_rule(DT.POV_STILL, before, i)), (fmt, p)
            assert "camera mounted on the moving object" not in p, (fmt, p)
            assert out[i]["motion"].startswith(PATH.KLING_MOTION), (fmt, out[i]["motion"])
        for i, s in enumerate(out):
            if s["type"] == "still": assert s["prompt"].startswith(_rule(DT.POV_STILL, before, i)), (fmt, s["prompt"])      # a still: as today


def test_applied_twice_the_path_formats_kling_prompt_and_motion_are_the_same(camera):
    _, once = _apply("F1"); _, twice = _apply("F1", once)
    for a, b in zip(once, twice):
        if a["type"] == "kling": assert (a["prompt"], a["motion"]) == (b["prompt"], b["motion"]), (a, b)
    assert sum(1 for s in twice if s["type"] == "kling") == 1


def test_outside_a_camera_path_format_the_kling_shot_keeps_the_mounted_camera(camera):
    before, out = _apply("F2"); ks = [i for i, s in enumerate(out) if s["type"] == "kling"]
    assert ks
    for i in ks:
        assert out[i]["prompt"].startswith(_rule(DT.POV_KLING, before, i)), out[i]["prompt"]
        assert "the camera IS the viewer's eyes" not in out[i]["prompt"] and out[i]["motion"].startswith("first-person camera mounted on the moving object"), out[i]


def test_pov_prompt_picks_its_rule_by_the_type_the_caller_gives():
    a = IM.pov_prompt({"type": "kling", "prompt": "a car on the road"}, "the road", "still")
    assert a == IM.pov_prompt({"type": "still", "prompt": "a car on the road"}, "the road")
    assert IM.pov_prompt({"type": "kling", "prompt": "a car on the road"}, "the road").startswith(DT.POV_KLING.format(anchor=IM.anchor_for("a car on the road the road")))
    assert IM.pov_prompt({"type": "kling", "prompt": a}, "", "still") == a                                           # idempotent
