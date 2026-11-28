"""U1 fix 199 (open issue 222): ONE ORDER ABOUT THE RUNNER-UP THUMBNAIL. The packager's base prompt holds a placeholder where its two runner-up lines
stood; room.package fills it with exactly one order: 'a DIFFERENT idea' for a film that is not one story, 'ANOTHER LOOK AT THE SAME SCENE' for a
one-story film - never an order followed by 'this replaces the order above'."""
import re
import pytest
from whatifs import room as ROOM, opening as OPEN, prompts as P, story as STORY

OPN = {"short": "SH1", "picture": "a city of floating pillows over your street"}


@pytest.fixture
def story_on(setting, monkeypatch):
    setting("ONE_STORY_ON", "TRUE")
    monkeypatch.setattr(OPEN, "source", lambda d: ("short", {"id": "SH1"}) if str((d or {}).get("ladder") or "") == "SH1" else ("none", {}))
    yield setting


def _system(monkeypatch, d, opening):
    """The system text the packager is really sent (spy on room.ask)."""
    seen = []
    monkeypatch.setattr(ROOM, "ask", lambda role, system, prompt, **kw: (seen.append((role, str(system))), {"titles": ["What if pillows floated?"], "thumb_prompt": "x", "thumb_text": "UP"})[1])
    room = {"script": {"script": "## BEAT 1\n[calm] You wake up and your pillow is on the ceiling."}, "spine": {"premise": "every pillow floats", "promise": {}}}
    ROOM.package(room, [("0:00", "Intro")], dict(d, strategies={"title": "N1_what_if", "thumb": "T1_object_scale"}), "EPRU1", opening=opening)
    sys_ = [s for r, s in seen if r == "packager"]; assert len(sys_) == 1
    return sys_[0]


def _sentences_with(text, word):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n", text) if word.lower() in s.lower()]


def test_a_one_story_film_is_given_one_runner_up_order_another_look_at_the_same_scene(story_on, monkeypatch):
    assert STORY.words_for({"ladder": "SH1"}, OPN)                                        # the film IS one story
    s = _system(monkeypatch, {"ladder": "SH1"}, OPN)
    assert s.count("ANOTHER LOOK AT THE SAME SCENE") == 1 and len(_sentences_with(s, "RUNNER-UP")) == 1, _sentences_with(s, "RUNNER-UP")
    assert "DIFFERENT idea" not in s and "replaces the rule" not in s and STORY.RUNNER_UP in s
    assert not re.search(r"@@[A-Z_]+@@", s)                                               # no placeholder is left unfilled


def test_a_film_that_is_not_one_story_is_given_the_different_idea_order_word_for_word(story_on, monkeypatch):
    for d, opening in (({"ladder": "SH9"}, OPN), ({}, None)):
        assert not STORY.words_for(d, opening)
        s = _system(monkeypatch, d, opening)
        assert s.count("DIFFERENT idea") == 1 and "ANOTHER LOOK" not in s and P.RUNNER_UP in s and len(_sentences_with(s, "RUNNER-UP")) == 1
        assert not re.search(r"@@[A-Z_]+@@", s)


def test_the_base_prompt_holds_the_placeholder_and_not_the_two_lines():
    assert P.PACKAGER.count("@@RUNNER_UP@@") == 1 and "RUNNER-UP" not in P.PACKAGER and "DIFFERENT idea" not in P.PACKAGER
    assert "replaces the rule" not in STORY.BRIEF and "runner-up" not in STORY.BRIEF.lower()
    assert STORY.BRIEF.startswith("THUMBNAIL SCENE (fixed: the picture this video opens on, the one real viewers stayed for): \"{words}\". Write thumb_text for THIS scene.")
    assert "Whichever thumbnail a viewer taps, the video opens on what it showed." in STORY.BRIEF


def test_any_other_fill_of_the_packager_gets_the_plain_order_never_the_placeholder():
    """CR-U1FIX-a finding 6: room.package passes runner_up=; every other fill of PACKAGER (tests/test_v87.py fills promise= only, a buyer's prompt
    pack) gets prompts.RUNNER_UP from fill's defaults - the literal @@RUNNER_UP@@ never reaches a model."""
    s = P.fill(P.PACKAGER, promise="x")
    assert "@@RUNNER_UP@@" not in s and s.count(P.RUNNER_UP) == 1 and "ANOTHER LOOK" not in s, s[-600:]
