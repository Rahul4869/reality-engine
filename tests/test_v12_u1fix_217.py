"""U1 fix 217 (open issue 248): A DIRECTOR'S TEXT IS NEVER CUT MID-WORD. media.clean_graphic bounds a timeline's time (14), its event (34), a label (48),
a unit (16) and a compare's names (22) at the last space inside the bound - one rule for the number card and for DRAWN's code scene."""
from whatifs import media as MD, drawn as DRAWN


def _words_of(cut, whole):
    """Every word of the cut text is a whole word of the original, in order, from its start."""
    return whole.split()[:len(cut.split())] == cut.split()


def test_every_bounded_text_is_cut_at_a_word_boundary():
    ev_t = "Second number twelve"; ev_x = "The whole ocean rises over the coastline tonight"; lab = "How the pillows of eight billion sleeping people float away"
    g = MD.clean_graphic({"kind": "timeline", "label": lab, "events": [{"t": ev_t, "text": ev_x}, {"t": "Second 9", "text": "Earth's roof follows"}]})
    e0 = g["events"][0]
    for cut, whole, n in ((e0["t"], ev_t, 14), (e0["text"], ev_x, 34), (g["label"], lab, 48)):
        assert len(cut) <= n and cut and _words_of(cut, whole) and cut == cut.strip(), (cut, whole)
    assert e0["t"] == "Second number" and e0["text"] == "The whole ocean rises over the" and g["label"] == "How the pillows of eight billion sleeping people"
    g = MD.clean_graphic({"kind": "compare", "label": lab, "unit": "kilometres per hour", "a": {"name": "The International Space Station", "value": 2},
                          "b": {"name": "The Concorde at full cruise", "value": 3}})
    assert g["a"]["name"] == "The International" and g["unit"] == "kilometres per" and g["b"]["name"] == "The Concorde at full"   # U1b finding 6 (b): b's cut pinned
    assert len(g["label"]) <= 48 and _words_of(g["label"], lab)


def test_a_text_inside_its_bound_or_ending_at_it_is_kept_whole():
    g = MD.clean_graphic({"kind": "timeline", "label": "x" * 48, "events": [{"t": "Second 1", "text": "abcd " * 6 + "wxyz"}, {"t": "Second 9", "text": "b"}]})
    assert g["label"] == "x" * 48 and g["events"][0]["text"] == "abcd " * 6 + "wxyz"            # 34 characters exactly: whole
    g = MD.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": "Second 1", "text": "abcd " * 6 + "wxyz more"}, {"t": "9", "text": "b"}]})
    assert g["events"][0]["text"] == "abcd " * 6 + "wxyz"                                          # the word ends AT the bound: kept, nothing more


def test_the_codes_scene_of_a_long_text_shows_whole_words():
    g = MD.clean_graphic({"kind": "timeline", "label": "The long fall of everything", "events": [{"t": "Second 1", "text": "The floor drops away beneath the whole city"},
                                                                                              {"t": "Second 9", "text": "Earth's roof follows"}]})
    sc, why = DRAWN.from_graphic(g)
    assert why == "" and sc["slots"]["rungs"][0]["text"] == "The floor drops away beneath the", why        # U1b finding 6 (a): the scene itself, asserted
    assert g["events"][0]["text"] == "The floor drops away beneath the"


def test_a_first_word_longer_than_its_bound_refuses_the_graphic_and_is_never_hard_cut():
    """RUL-U1 217 (CHANGE, one case): a FIRST word longer than its bound (no space inside it) is not cut mid-word - clean_graphic returns None for that
    graphic (its own refusal: the shot then becomes a normal still). A word of exactly the bound is kept whole."""
    w17, w25, w14 = "Incomprehensibles", "Antidisestablishmentarian", "Thermodynamics"
    assert (len(w17), len(w25), len(w14)) == (17, 25, 14)
    assert MD.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": w17, "text": "a"}, {"t": "Second 9", "text": "b"}]}) is None
    assert MD.clean_graphic({"kind": "compare", "label": "L", "a": {"name": w25, "value": 2}, "b": {"name": "B", "value": 3}}) is None
    g = MD.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": w14, "text": "a"}, {"t": "Second 9", "text": "b"}]})
    assert g and g["events"][0]["t"] == w14


def test_a_counters_label_is_bounded_at_a_word_where_the_others_are():
    """RUL-U1b finding 5: the counter road bounds a label it HAS with the same cut (48) - a counter with no "label" key gains none; a first word
    longer than the bound refuses the graphic (RUL-U1 217's rule)."""
    lab = "How the pillows of eight billion sleeping people float away"
    assert MD.clean_graphic({"kind": "counter", "label": lab, "from": 0, "to": 9})["label"] == "How the pillows of eight billion sleeping people"
    g0 = {"kind": "counter", "from": 0, "to": 9, "unit": "pillows"}
    assert MD.clean_graphic(dict(g0)) == g0                                                       # no label: the same keys it had, none gained
    assert MD.clean_graphic({"kind": "counter", "label": "x" * 49, "to": 9}) is None


def test_cut_strips_the_text_first_then_measures_it():
    """RUL-U1b finding 6 (c): `_cut` strips FIRST, then measures - a leading space never leaves "" nor cuts inside the first word; an event whose
    text is empty after the strip is dropped as one with no text (then `len(ev) >= 2` judges the timeline as before)."""
    import pytest
    for s in ("  " + "x" * 40, " Supercalifragilistic word"):
        with pytest.raises(ValueError): MD._cut(s, 14)                                            # the long-first-word rule: refused, never "" or a cut word
        assert MD.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": s, "text": "a"}, {"t": "Second 9", "text": "b"}]}) is None, s
    assert MD._cut("  Second 1 ", 14) == "Second 1"
    g = MD.clean_graphic({"kind": "timeline", "label": " L ", "events": [{"t": "1", "text": "   "}, {"t": " Second 1 ", "text": " a "}, {"t": "9", "text": "b"}]})
    assert g["label"] == "L" and g["events"] == [{"t": "Second 1", "text": "a"}, {"t": "9", "text": "b"}]
    assert MD.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": "1", "text": "  "}, {"t": "9", "text": "b"}]}) is None
