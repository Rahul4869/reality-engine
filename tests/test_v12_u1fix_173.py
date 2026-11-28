"""U1 fix 173 (open issue 193): AUDIENCE.SPOKEN FOLLOWS THE VOICE. The words every measure reads (numbers, expert words, sentences, pauses, the tail's
words, the scenes' word alignment) are the words the voice says: a line's label is read by voice._peel (only the known names are labels), never by a
second rule of its own - 'Next simulation: What if the Moon left tonight?' is spoken whole, so it is measured whole."""
import json
from whatifs import voice as VO, formats as FMT, fakes as FK
from whatifs.org import audience as AUD


def _words(text):
    return str(text).split()


def test_a_line_that_starts_with_an_unknown_word_and_a_colon_is_measured_whole():
    got = AUD.spoken("Next simulation: What if the Moon left tonight?")
    assert "Next simulation" in got and len(_words(got)) == 8, got


def test_every_name_the_voice_knows_is_a_label_in_every_form_it_is_written():
    names = list(VO.SPEAKERS) + list(VO.ALIASES)          # read from the voice, never typed here
    assert len(names) >= 20
    for name in names:
        for line in (f"{name}: Hello there.", f"**{name.title()}:** Hello there.", f"[{name}] [calm] Hello there."):
            assert _words(AUD.spoken(line)) == ["Hello", "there."], (line, AUD.spoken(line))


def test_every_line_of_the_offline_writer_is_measured_as_the_voice_says_it():
    seen = 0
    for fmt in FMT.FORMATS:
        with FMT.using(fmt): text = json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"]
        for line in text.split("\n"):
            if line.strip().startswith(("#", "[SFX", "[MUSIC", "(")): continue          # the filter that stays: headings and directions are never spoken
            said = AUD._TAGS.sub(" ", VO._peel(line)[3])
            assert _words(AUD.spoken(line)) == _words(said), (fmt, line); seen += 1
    assert seen >= 3 * len(FMT.FORMATS)
