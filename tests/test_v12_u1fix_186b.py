"""U1 J 186 on the promise re-aim (CR-U1FIX-a finding 5; typed into U1-JR-2 because whatifs/room.py is T-JR-2's file): in a camera-path format the
re-aimed opening kling clip of room.promise_shot carries the STILL's first-person rule (data.POV_STILL), never POV_KLING's "camera mounted on the
moving object" - the one camera immersion.apply gives every clip of a path film. Outside a path format the re-aimed clip keeps POV_KLING, as before."""
import pytest
from whatifs import data as DT, formats as FMT, immersion as IM, room as ROOM

U = [{"text": f"Line {i} on the street.", "start": i * 5.0, "end": i * 5.0 + 4, "tag": "none"} for i in range(6)]
THUMB = {"thumb_prompt": "a city of floating pillows over your street"}


@pytest.fixture
def camera(setting):
    for k in ("CAMERA_PATH_ON", "INSIDE_ON", "ENDINGS_ON", "IMMERSION_ON", "PROMISE_SHOT_ON"): setting(k, "TRUE")
    setting("POV_VARIETY_ON", "FALSE")
    yield
    FMT.use("")


def _reaim(fmt):
    """The opening kling clip re-aimed at the thumbnail's scene; (its prompt, the text pov_prompt reads the anchor from)."""
    shots = [{"type": "kling", "prompt": "k"}] + [{"type": "still", "prompt": "s"} for _ in range(5)]
    if fmt:
        with FMT.using(fmt): out = ROOM.promise_shot(shots, U, THUMB)
    else: out = ROOM.promise_shot(shots, U, THUMB)
    assert out[0].get("promise") and out[0]["type"] == "kling", out[0]
    return out[0]["prompt"], f"{THUMB['thumb_prompt']}; {U[0]['text']} {U[0]['text']}"


def test_a_path_formats_reaimed_opening_clip_carries_the_stills_first_person_rule(camera):
    for fmt in ("F1", "F3"):
        p, aimed = _reaim(fmt)
        assert p.startswith(DT.POV_STILL.format(anchor=IM.anchor_for(aimed))), (fmt, p)
        assert "camera mounted on the moving object" not in p and THUMB["thumb_prompt"] in p, (fmt, p)


def test_outside_a_path_format_the_reaimed_clip_keeps_the_kling_rule(camera):
    p, aimed = _reaim("")
    assert p.startswith(DT.POV_KLING.format(anchor=IM.anchor_for(aimed))), p
