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
                          "b": {"name": "B", "value": 3}})
    assert g["a"]["name"] == "The International" and g["unit"] == "kilometres per"
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
    assert why == "" or sc is None
    assert g["events"][0]["text"] == "The floor drops away beneath the"
