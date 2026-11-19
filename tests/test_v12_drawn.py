"""v12 DRAWN BY CODE (D6): the house kit, the closed scene language, verify, the layout and its timing, the plan step and check drawn_plan - every rule both ways, one fault at a time."""
import datetime as dt, json, math, os, re
import numpy as np, cv2
import pytest
from whatifs import core, drawn as DRAWN, scenes as SCN
from whatifs.core import S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = dt.datetime(2031, 3, 7, 9, 0, tzinfo=dt.timezone.utc)          # this file's own episode ids (no other test file uses 2031-03)
OPTS = {"text_min": 5.0, "words_max": 14, "hold_max": 2.0}
G_COUNT = {"kind": "counter", "label": "Pillows airborne", "from": 0, "to": 8000000000, "unit": ""}


def _arm_on(setting): setting("DRAWN_ON", "TRUE"); setting("DRAWN_SHARE_PCT", "100")


def _units(texts, each=4.0): return [{"i": k, "text": t, "start": k * each, "end": k * each + each - 0.3, "words": [], "speaker": "GUIDE"} for k, t in enumerate(texts)]


def _gshot(g=None): return {"type": "graphic", "graphic": dict(g or G_COUNT), "prompt": "a picture"}


def _full(n, k=1):
    """A string of exactly n characters in k words (a slot at its full bound)."""
    letters = "Abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"; rem = n - (k - 1); parts = []
    for j in range(k):
        m = rem // (k - j); parts.append(letters[:m]); rem -= m
    return " ".join(parts)


# ------------------------------------------------------------------ 1. the module is closed; clean
def test_the_module_is_closed_and_clean_refuses_everything_outside_the_kit():
    src = open(os.path.join(ROOT, "whatifs", "drawn.py"), encoding="utf-8").read()
    for w in ("open(", "subprocess", "os.", "requests", "urllib", "socket", "eval(", "exec(", "__import__", "importlib", "S("): assert w not in src, w
    gold = {k: json.loads(json.dumps(v["gold"])) for k, v in DRAWN.TEMPLATES.items()}
    for k, v in DRAWN.TEMPLATES.items():
        assert {"use", "slots", "gold", "anti", "feel"} <= set(v), k
        assert DRAWN.clean(gold[k]) == (gold[k], ""), k                     # each gold scene comes back unchanged
    def bad(mut):
        sc = json.loads(json.dumps(gold["count"])); mut(sc); return DRAWN.clean(sc)
    assert bad(lambda s: s.update(colour="#ff0000")) == (None, "not in the scene language: colour")         # a colour is never a slot
    assert bad(lambda s: s["slots"].update(size=3)) == (None, "not in the scene language: size")
    assert bad(lambda s: s.update(template="spiral")) == (None, "an unknown template: spiral")
    assert bad(lambda s: s["slots"].pop("unit")) == (None, "a missing slot: unit")
    for evil in ("../etc", "http://x", "a\\b", "<script", "a..b"):
        assert bad(lambda s: s["slots"].update(label=evil)) == (None, "not in the scene language: label"), evil
    assert bad(lambda s: s["slots"].update(label="x" * 49)) == (None, "a text over its bound: label")
    assert DRAWN.clean(dict(gold["count"], slots=dict(gold["count"]["slots"], label="x" * 48)))[1] == ""
    assert bad(lambda s: s["slots"].update(to=float("inf"))) == (None, "not a number the kit can draw: to")
    assert bad(lambda s: s["slots"].update(to=2e15)) == (None, "not a number the kit can draw: to")
    assert bad(lambda s: s.update(cues=["x" * 41])) == (None, "not in the scene language: cues")
    assert bad(lambda s: s.update(cues=[""])) == (gold["count"] | {"cues": [""]}, "")
    assert bad(lambda s: s.update(cues=["a"] * 7)) == (None, "not in the scene language: cues")
    assert bad(lambda s: s.update(v=2)) == (None, "not in the scene language: v") and bad(lambda s: s.update(variant=2)) == (None, "not in the scene language: variant")
    sc = json.loads(json.dumps(gold["compare"])); sc["slots"]["b"]["value"] = sc["slots"]["a"]["value"]
    assert DRAWN.clean(sc) == (None, "a compare needs two different values above 0")
    sc = json.loads(json.dumps(gold["part"])); sc["slots"]["part"]["value"] = 120
    assert DRAWN.clean(sc) == (None, "a part must be above 0 and under its whole")


def test_the_older_tests_run_with_the_drawn_scenes_off():
    from tests.conftest import OLD_DRAWN
    assert OLD_DRAWN["DRAWN_ON"] == "FALSE" and core.DEFAULTS["DRAWN_ON"][0] == "TRUE" and SCN.on() is False


# ------------------------------------------------------------------ 3. the code's own scene of a Director graphic
def test_from_graphic_draws_the_directors_own_pairs_and_never_cuts_a_unit_or_a_name():
    tl = {"kind": "timeline", "label": "The long fall", "events": [{"t": "Second 1", "text": "The floor drops"}, {"t": "Second 9", "text": "The roof follows"}]}
    cmp_ = {"kind": "compare", "label": "How far", "unit": "km", "a": {"name": "The Moon", "value": 384000}, "b": {"name": "The Sun", "value": 150000000}}
    for g, t in ((G_COUNT, "count"), (tl, "ladder"), (cmp_, "compare")):
        sc, why = DRAWN.from_graphic(g)
        assert why == "" and sc["template"] == t and SCN.verify(sc, g, ("", "", "")) == "", (t, why)
    sc, _ = DRAWN.from_graphic(cmp_); f = {i["id"]: i for i in DRAWN.expand(sc)["items"]}
    lo, hi = 384000, 150000000; logf = (math.log10(lo) - math.log10(lo) + 0.35) / (math.log10(hi) - math.log10(lo) + 0.35)
    assert abs(f["bar_a"]["value"] - logf) < 1e-9 and f["bar_a"]["value"] > 10 * lo / hi           # a ratio above 20: the card's own log form
    assert DRAWN.from_graphic(dict(G_COUNT, label="Earth’s pull — 9.8 m/s² × 2")) == (None, "a character the kit cannot draw: ²")
    sc, why = DRAWN.from_graphic(dict(G_COUNT, label="Earth’s pull — twice")); assert why == "" and sc["slots"]["label"] == "Earth's pull - twice"
    long_ = "Pillows that leave the ground and float away into the sky tonight"            # 60+ characters: cut at the last space inside 48
    sc, _ = DRAWN.from_graphic(dict(G_COUNT, label=long_)); assert sc["slots"]["label"] == long_[:long_.rfind(" ", 0, 49)] and len(sc["slots"]["label"]) <= 48
    assert DRAWN.from_graphic(dict(cmp_, unit="kilometresss"))[0] is None                  # a unit of 12 characters (the bound is 8): refused, the card stays
    assert DRAWN.from_graphic(dict(cmp_, unit="light years")) == (None, "a text over its bound: light years")      # C4: never drawn as "light"


# ------------------------------------------------------------------ 4. verify: the script's own numbers, words, pairs and arrows
def _cmp(a, av, b, bv, label="How far away they are", unit="km"):
    return {"v": 1, "template": "compare", "variant": 0, "slots": {"label": label, "unit": unit, "a": {"name": a, "value": av}, "b": {"name": b, "value": bv}}, "cues": []}


G_LABEL = {"kind": "counter", "label": "How far away they are", "from": 0, "to": 1, "unit": ""}


def test_verify_refuses_a_number_a_word_a_pair_or_an_arrow_the_script_does_not_state():
    line = "The Moon is 384,000 km away and the Sun is 150,000,000 km away."
    assert SCN.verify(_cmp("The Moon", 384000, "The Sun", 150000000), G_LABEL, ("", line, "")) == ""
    assert SCN.verify(_cmp("The Moon", 384000, "The Sun", 151000000), G_LABEL, ("", line, "")) == "a number the voice never says: 151.0 million"
    assert SCN.verify(_cmp("The Moon", 384000, "The Sun", 151000000), G_LABEL, ("", line, "And 151,000,000 km is the far side.")) != "a number the voice never says: 151.0 million"
    assert SCN.verify(_cmp("The Comet", 384000, "The Sun", 150000000), G_LABEL, ("", line, "")) == "a word the script does not have: comet"
    assert SCN.verify(_cmp("The Moon", 150000000, "The Sun", 384000), G_LABEL, ("", line, "")).startswith("a value the script does not give to that name")      # swapped values
    c1 = "The 150,000,000 km to the Sun dwarfs the Moon at 384,000 km."                          # C1: never measured from a "the"
    assert SCN.verify(_cmp("The Moon", 150000000, "The Sun", 384000), G_LABEL, ("", c1, "")).startswith("a value the script does not give to that name")
    assert SCN.verify(_cmp("The Moon", 384000, "The Sun", 150000000), G_LABEL, ("", c1, "")) == ""
    gp = {"kind": "counter", "label": "Your share of the air", "from": 0, "to": 1, "unit": ""}; ln = "Oxygen is 21 of every 100 parts of all the air."
    part = lambda pn, pv, wn, wv: {"v": 1, "template": "part", "variant": 0, "slots": {"label": "Your share of the air", "part": {"name": pn, "value": pv}, "whole": {"name": wn, "value": wv}}, "cues": []}
    assert SCN.verify(part("Oxygen", 21, "All the air", 100), gp, ("", ln, "")) == ""
    assert SCN.verify(part("All the air", 21, "Oxygen", 100), gp, ("", ln, "")).startswith("a value the script does not give to that name")       # names swapped
    gl = {"kind": "counter", "label": "Who walks on the Moon", "from": 0, "to": 1, "unit": ""}
    two = ("In the year 1969 people walk on the Moon.", "In the year 1972 the last people leave the Moon.", "")
    lad = lambda rungs: {"v": 1, "template": "ladder", "variant": 0, "slots": {"label": "Who walks on the Moon", "rungs": rungs}, "cues": []}
    r69, r72 = {"t": "Year 1969", "text": "People walk on the Moon"}, {"t": "Year 1972", "text": "The last people leave"}
    assert SCN.verify(lad([r69, r72]), gl, two) == ""
    assert SCN.verify(lad([dict(r69, t="Year 1972"), dict(r72, t="Year 1969")]), gl, two).startswith("a value the script does not give to that name")      # times exchanged
    assert SCN.verify(lad([r72, r69]), gl, two) == "the rungs are not in the script's order"
    own = {"kind": "timeline", "label": "Who walks on the Moon", "events": [{"t": "Year 2001", "text": "Something odd"}, {"t": "Year 2002", "text": "Something odder"}]}
    assert SCN.verify(lad([{"t": "Year 2001", "text": "Something odd"}, {"t": "Year 2002", "text": "Something odder"}]), own, ("", "", "")) == ""      # the graphic's own entries
    gf = {"kind": "counter", "label": "Why the cup falls", "from": 0, "to": 1, "unit": ""}
    flow = lambda a, b: {"v": 1, "template": "flow", "variant": 0, "slots": {"label": "Why the cup falls", "links": [a, b]}, "cues": []}
    so = ("", "the table tilts, so the cup falls", "")
    assert SCN.verify(flow("The table tilts", "The cup falls"), gf, so) == ""
    assert SCN.verify(flow("The cup falls", "The table tilts"), gf, so) == "an arrow the script does not state: The cup falls -> The table tilts"      # C1: both begin with "the"
    assert SCN.verify(flow("The table tilts", "The cup falls"), gf, ("", "the cup falls because the table tilts", "")) == ""          # the BACK direction
    both = ("", "the table tilts and the cup falls", "")
    assert SCN.verify(flow("The table tilts", "The cup falls"), gf, both).startswith("an arrow the script does not state") and SCN.verify(flow("The cup falls", "The table tilts"), gf, both).startswith("an arrow")
    assert SCN.verify(flow("The table tilts", "The cup falls"), gf, ("", "the table is so heavy the cup falls and tilts", "")).startswith("an arrow")       # "so heavy" is no cause
    assert SCN.verify(flow("It is so", "The cup falls"), gf, ("", "it is so, so the cup falls", "")) == "a part the script cannot place: It is so"
    assert "the" in SCN.STOP and "moon" not in SCN.STOP


# ------------------------------------------------------------------ 5. the layout
def _one_text(text, w_cols, size="label", W=1920, H=1080, at=(0, 1)):
    return {"title": "", "items": [{"id": "x", "kind": "label", "at": list(at), "span": [w_cols, 0.8], "colour": "ink", "text": text, "size": size, "align": "l", "value": 1.0, "of": 1.0}],
            "steps": [{"show": ["x"], "how": "fade", "cue": ""}]}


def test_layout_fits_measures_and_refuses_by_reason():
    W, H = 1920, 1080; cw = W * DRAWN.SAFE / DRAWN.GRID[0]; T = "Abcdefghij Abcdefghij Abcdefghij Abcdef"
    w54, w43 = DRAWN.font(54, False).getlength(T), DRAWN.font(43, False).getlength(T)
    free = _one_text(T, ((w54 + w43) / 2) / cw)                                       # fits only below 5 % of the height
    with pytest.raises(DRAWN.Refused, match="a text does not fit"): DRAWN.layout(free, W, H, 6.0, None, **OPTS)
    L = DRAWN.layout(free, W, H, 6.0, None, **dict(OPTS, text_min=4.0)); assert 43 <= L["items"][0]["px"] < 54
    two = _one_text("Same", 4); two["items"].append(dict(two["items"][0], id="y")); two["steps"][0]["show"].append("y")
    with pytest.raises(DRAWN.Refused, match="two texts overlap"): DRAWN.layout(two, W, H, 6.0, None, **OPTS)
    with pytest.raises(DRAWN.Refused, match="outside the safe area"): DRAWN.layout(_one_text("Out", 2, at=(11, 1)), W, H, 6.0, None, **OPTS)
    many = _one_text("a b c d e f g h i j k l m n o", 12)
    with pytest.raises(DRAWN.Refused, match="too many words on screen"): DRAWN.layout(many, W, H, 6.0, None, **OPTS)
    many["items"][0]["id"] = "title"; many["steps"][0]["show"] = ["title"]; DRAWN.layout(many, W, H, 6.0, None, **OPTS)       # the title's words are not counted
    with pytest.raises(DRAWN.Refused, match="no portrait layout yet"): DRAWN.layout(_one_text("Tall", 4), 1080, 1920, 6.0, None, **OPTS)


def test_every_gold_scene_at_its_full_bound_is_laid_out_at_both_work_sizes():
    full = {"count": {"label": _full(48, 4), "from": 0, "to": 8000000000, "unit": _full(16)},
            "ladder": {"label": _full(48, 4), "rungs": [{"t": _full(14), "text": _full(34, 2)} for _ in range(3)]},
            "compare": {"label": _full(48, 4), "unit": _full(8), "a": {"name": _full(22, 2), "value": 384000}, "b": {"name": _full(22, 2), "value": 150000000}},
            "flow": {"label": _full(48, 4), "links": [_full(34, 2)] * 3},
            "part": {"label": _full(48, 4), "part": {"name": _full(22, 2), "value": 21}, "whole": {"name": _full(22, 2), "value": 100}}}
    for t, slots in full.items():
        for v in (0, 1):
            sc = dict(DRAWN.TEMPLATES[t]["gold"], slots=slots, variant=v)
            assert DRAWN.clean(sc)[1] == "", t
            for W, H in ((1920, 1080), (640, 360)):
                L = DRAWN.layout(DRAWN.expand(sc), W, H, 8.0, None, **OPTS)
                assert min(i["px"] for i in L["items"] if i.get("px")) >= 0.05 * H - 1, (t, v, W)
    big = dict(full["compare"], b={"name": _full(22, 2), "value": 1e12})      # "1000.00 billion Abcdefgh": 24 characters - over the value box: refused, never cut
    for W, H in ((1920, 1080), (640, 360)):
        with pytest.raises(DRAWN.Refused, match="a text does not fit"):
            DRAWN.layout(DRAWN.expand(dict(DRAWN.TEMPLATES["compare"]["gold"], slots=big, variant=0)), W, H, 8.0, None, **OPTS)


def test_the_word_limit_draws_a_real_three_rung_ladder_and_refuses_a_flood():
    lim = int(core.DEFAULTS["DRAWN_WORDS_MAX"][0])                                     # the cell's default, never a literal
    rungs = [{"t": "After 1 minute", "text": "Pillows drift over the town roofs"}, {"t": "After 1 hour", "text": "They pass the cruising airliners"},
             {"t": "After 1 day", "text": "The first ones reach outer space"}]        # 26 words: a Director's timeline of real length
    for W, H in ((1920, 1080), (640, 360)):
        sc = dict(DRAWN.TEMPLATES["ladder"]["gold"], slots={"label": "How high the pillows go", "rungs": rungs})
        DRAWN.layout(DRAWN.expand(sc), W, H, 9.0, None, **dict(OPTS, words_max=lim))
        four = dict(sc, slots={"label": "How high the pillows go", "rungs": rungs + [{"t": "After 1 week", "text": "They drift past the Moon itself"}]})
        with pytest.raises(DRAWN.Refused, match="too many words on screen"):
            DRAWN.layout(DRAWN.expand(four), W, H, 12.0, None, **dict(OPTS, words_max=lim))


# ------------------------------------------------------------------ 6. the timing
def _shapes(hows):
    items = [{"id": f"d{k}", "kind": "dot", "at": [k, 2], "span": [0.5, 0.5], "colour": "a", "text": "", "value": 1.0, "of": 1.0} for k in range(len(hows))]
    return {"title": "", "items": items, "steps": [{"show": [f"d{k}"], "how": h, "cue": ""} for k, h in enumerate(hows)]}


def test_the_timing_is_exact_cued_and_never_stands_still_past_the_hold():
    L = DRAWN.layout(_shapes(("fade", "grow", "pop")), 1920, 1080, 6.0, None, **OPTS)
    slot = (6.0 - 0.25 - 1.2) / 3
    assert [s["t0"] for s in L["steps"]] == [round(0.25 + k * slot, 4) for k in range(3)] and [s["on"] for s in L["steps"]] == [0.4, 0.8, 0.35]
    end = 0.25 + 2 * slot + 0.35; assert [p["t"] for p in L["pulses"]] == [round(end + 2.0, 4)] and L["pulses"][0]["peak"] == round(end + 2.25, 4)
    assert DRAWN.layout(_shapes(("fade", "grow", "pop")), 1920, 1080, 6.0, [None, 1.0, None], **OPTS)["steps"][1]["t0"] == 0.85          # a cue inside the window
    assert DRAWN.layout(_shapes(("fade", "grow", "pop")), 1920, 1080, 6.0, [None, 4.5, None], **OPTS)["steps"][1]["t0"] == round(0.25 + slot, 4)      # outside: kept
    five = {"v": 1, "template": "ladder", "variant": 0, "slots": {"label": "Five rungs", "rungs": [{"t": f"Step{k}", "text": "Up"} for k in range(5)]}, "cues": []}
    with pytest.raises(DRAWN.Refused, match="more steps than the line can show"): DRAWN.layout(DRAWN.expand(five), 1920, 1080, 2.4, None, **OPTS)
    L5 = DRAWN.layout(DRAWN.expand(five), 1920, 1080, 3.0, None, **OPTS); assert L5["steps"][-1]["t0"] + L5["steps"][-1]["on"] <= 3.0 - 0.6
    g = DRAWN.TEMPLATES
    assert [s["cue"] for s in DRAWN.expand(dict(g["ladder"]["gold"], cues=["x", "y", "z"]))["steps"]] == ["", "1 minute", "1 hour", "1 day"]
    assert [s["cue"] for s in DRAWN.expand(dict(g["compare"]["gold"], cues=["x", "y"]))["steps"]] == ["", "The Moon", "The Sun", ""]
    assert [s["cue"] for s in DRAWN.expand(dict(g["part"]["gold"], cues=["x"]))["steps"]] == ["", "All the air", "Oxygen", ""]
    assert [s["cue"] for s in DRAWN.expand(dict(g["flow"]["gold"], cues=["tilts"]))["steps"]] == ["", "tilts", "", ""]          # a short cue list is filled with ""


# ------------------------------------------------------------------ 9. the plan step
LINES = ["You wake up and the pillows are gone.", "Eight billion pillows rise over every city tonight.", "You watch them go.", "Then the sky fills up.",
         "Eight billion pillows rise again over the sea.", "You hold on.", "Eight billion pillows rise one last time.", "The end."]


def _film(graphic_at=(1, 4, 6)):
    units = _units(LINES); shots = [_gshot() if k in graphic_at else {"type": "still", "prompt": "p"} for k in range(len(units))]
    return shots, units, units[-1]["end"] + 0.3


def test_the_plan_step_outside_the_arm_changes_nothing(setting):
    setting("DRAWN_ON", "TRUE"); setting("DRAWN_SHARE_PCT", "0"); shots, units, total = _film(); d = {}
    out = SCN.place(shots, units, "EP203103070801", d, total, True)
    assert d["drawn"] == {"arm": False, "scenes": []} and not any(s.get("scene") for s in out) and out == shots
    setting("DRAWN_ON", "FALSE"); d2 = {}; assert SCN.place(shots, units, "EP203103070801", d2, total, True) is shots and "drawn" not in d2


def test_the_plan_step_in_the_arm_takes_the_writer_falls_to_the_code_and_varies(setting, monkeypatch):
    _arm_on(setting); shots, units, total = _film(); d = {}
    assert SCN.slots(shots, units, total) == [1, 4, 6] and 0 not in SCN.slots([_gshot()] + shots[1:], units, total)      # shot 0 is never an explaining moment
    out = SCN.place(shots, units, "EP203103070802", d, total, True)
    recs = d["drawn"]["scenes"]; assert [r["unit"] for r in recs] == [1, 4, 6]
    assert [r["by"] for r in recs[:2]] == ["writer", "writer"] and {recs[0]["variant"], recs[1]["variant"]} == {0, 1}
    assert recs[2] == dict(recs[2], by="", why="its composition is used twice already") and "scene" not in out[6]       # a third use keeps its card
    assert out[1]["scene"]["by"] == "writer" and out[1]["type"] == "graphic" and out[1]["graphic"] == shots[1]["graphic"]      # type and graphic NEVER change
    assert SCN.feature(d) == {"drawn": [f"count{recs[0]['variant']}", f"count{recs[1]['variant']}"]}
    foreign = {u: {"unit": u, "template": "count", "slots": {"label": "Pillows airborne", "from": 0, "to": 9000000000, "unit": ""}, "cues": []} for u in (1, 4, 6)}
    monkeypatch.setattr(SCN, "ask", lambda ep, wanted: foreign); d = {}
    SCN.place(shots, units, "EP203103070803", d, total, True)
    assert d["drawn"]["scenes"][0]["by"] == "code" and "a number the voice never says" in d["drawn"]["scenes"][0]["why"]      # a foreign number falls to the code's scene


def test_a_templates_first_use_takes_the_other_variant_than_the_last_drawn_video(setting):
    _arm_on(setting); shots, units, total = _film((1,))
    for v in (0, 1):
        core.store().append("Video_Features", [{"ts": core.iso(), "video_key": f"EPX{v}", "format": "long", "arm": json.dumps({"drawn": [f"count{v}"]})}]); d = {}
        SCN.place(shots, units, f"EP20310307081{v}", d, total, True)
        assert d["drawn"]["last"] == {"count": v} and d["drawn"]["scenes"][0]["variant"] == 1 - v


def test_a_plan_saved_before_the_step_asks_no_model_and_a_resume_asks_none(setting, monkeypatch):
    _arm_on(setting); shots, units, total = _film(); asked = []
    monkeypatch.setattr(SCN, "ask", lambda ep, wanted: asked.append(1) or {})
    d = {}; out = SCN.place(shots, units, "EP203103070804", d, total, False)
    assert d["drawn"] == {"arm": False, "why": "planned before the drawn arm", "scenes": []} and not asked and not any(s.get("scene") for s in out)
    d = {"drawn": {"arm": True, "last": {}, "scenes": [{"unit": 1, "template": "count", "variant": 1, "slots": DRAWN.from_graphic(G_COUNT)[0]["slots"], "cues": [], "by": "code", "why": ""},
                                                     {"unit": 4, "template": "flow", "variant": 0, "slots": {"label": "Pillows airborne", "links": ["Gone", "Back"]}, "cues": [], "by": "writer", "why": ""}]}}
    out = SCN.place(shots, units, "EP203103070804", d, total, True)
    assert not asked and out[1]["scene"]["template"] == "count" and out[1]["scene"]["variant"] == 1 and "scene" not in out[4]
    assert d["drawn"]["scenes"][1]["by"] == "" and d["drawn"]["scenes"][1]["why"] == "no longer fits after a resume"


def test_the_plan_step_never_stops_a_video(setting, monkeypatch):
    _arm_on(setting); shots, units, total = _film()
    def boom(*a, **k): raise RuntimeError("an odd unit")
    monkeypatch.setattr(SCN, "cue_s", boom); d = {}
    out = SCN.place(shots, units, "EP203103070805", d, total, True)                          # C9: the card stays, the video goes on
    assert not any(s.get("scene") for s in out) and {r["why"] for r in d["drawn"]["scenes"]} == {"error: RuntimeError"}
    monkeypatch.setattr(SCN, "last_used", boom); monkeypatch.undo(); d = {}
    monkeypatch.setattr(SCN, "last_used", boom); SCN.place(shots, units, "EP203103070806", d, total, True); assert d["drawn"]["last"] == {}
    for odd in (None, [], [1, "x", None]): assert SCN.m_place(odd) == {"slots": 0, "drawn_by_writer": 0, "drawn_by_code": 0, "kept_card": 0}
    assert SCN.m_place(out) == {"slots": 3, "drawn_by_writer": 0, "drawn_by_code": 0, "kept_card": 3}


def test_the_cost_model_carries_the_writers_call_only_with_the_arm(setting):
    from whatifs import costguard as CG
    _arm_on(setting); ln = [l for l in CG.lines("long") if l["key"] == "drawn_scenes"]
    assert len(ln) == 1 and ln[0]["inr"] == 38.0 and ln[0]["calls"] == {"text:scene": 1} and ln[0]["stage"] == "ai_writing"
    assert [l for l in CG.lines("ladder") if l["key"] == "drawn_scenes"]
    setting("DRAWN_SHARE_PCT", "0"); assert not [l for l in CG.lines("long") if l["key"] == "drawn_scenes"]
    setting("DRAWN_SHARE_PCT", "25"); setting("DRAWN_ON", "FALSE"); assert not [l for l in CG.lines("long") if l["key"] == "drawn_scenes"]


# ------------------------------------------------------------------ 11. check drawn_plan (the plan half)
def test_check_drawn_plan_says_na_pass_and_fails_each_lie(setting):
    from whatifs import contract as CON
    shots, units, total = _film(); ctx = lambda sh, d: {"shots": sh, "units": units, "d": d, "total": total}
    setting("DRAWN_ON", "FALSE"); assert CON.p_drawn_plan(ctx(shots, {})) == ("N/A", "not applicable: the drawn scenes are switched off")
    _arm_on(setting); assert CON.p_drawn_plan(ctx(shots, {"drawn": {"arm": False, "scenes": []}})) == ("N/A", "not applicable: this video is not in the drawn arm")
    d = {}; out = SCN.place(shots, units, "EP203103070807", d, total, True)
    st, why = CON.p_drawn_plan(ctx(out, d)); assert st == "PASS" and why.startswith("the drawn arm held: 2 of 3 explaining moments carry a scene") and "its composition is used twice already" in why
    none_ = [{"type": "still"} for _ in units]; assert CON.p_drawn_plan(ctx(none_, d)) == ("PASS", "the drawn arm held: no explaining moment in this film")
    sc = out[1]["scene"]
    def fails(sh, dd=None): return CON.p_drawn_plan(ctx(sh, d if dd is None else dd))[0] == "FAIL"
    assert fails(out, {"drawn": {"arm": False, "scenes": []}})                                             # a scene outside the arm
    setting("DRAWN_ON", "FALSE"); assert fails(out); _arm_on(setting)                                     # a scene with the switch off
    assert fails([dict(s, scene=sc) if k == 2 else s for k, s in enumerate(out)])                         # a scene on a shot that is not a moment
    assert fails([dict(s, scene=dict(sc, slots=dict(sc["slots"], label="a..b"))) if k == 1 else s for k, s in enumerate(out)])          # clean refuses it NOW
    assert fails([dict(s, scene=dict(sc, slots=dict(sc["slots"], to=7))) if k == 1 else s for k, s in enumerate(out)])                 # verify refuses it NOW
    setting("DRAWN_TEXT_MIN_PCT", "40"); assert fails(out); setting("DRAWN_TEXT_MIN_PCT", "5.0")          # the layout refuses it NOW
    assert fails([dict(s, scene=dict(out[1]["scene"])) if k == 4 else s for k, s in enumerate(out)])      # two scenes share one composition
    d2 = json.loads(json.dumps(d)); d2["drawn"]["last"] = {"count": out[1]["scene"]["variant"]}; assert fails(out, d2)      # the first use repeats the last drawn video's


# ------------------------------------------------------------------ 9. the resume through the real restore (one paid call over both runs)
def _setup(monkeypatch, setting):
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import manage as MG, episode as EP
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP, "now_utc", lambda: FROZEN)
    _arm_on(setting); setting("DRAWN_MIN_S", "1.0"); setting("GRAPHICS_FREE_SEC", "0")        # every offline film keeps a moment (the slot rule has its own tests above)
    return (FROZEN + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_a_resume_restores_the_writers_scenes_and_pays_the_call_once(monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import episode as EP, room as ROOM, checkpoint as CK
    slot = _setup(monkeypatch, setting); c = watch(monkeypatch); seen = []
    real_place = SCN.place
    def spy(*a, **k):
        out = real_place(*a, **k); seen.append([(i, s.get("scene")) for i, s in enumerate(out) if s.get("scene")]); return out
    monkeypatch.setattr(SCN, "place", spy)
    real = EP._assets; boom = {"n": 0}
    def flaky(*a, **k):
        boom["n"] += 1
        if boom["n"] == 1: raise RuntimeError("fal had a bad minute")
        return real(*a, **k)
    monkeypatch.setattr(EP, "_assets", flaky)
    with pytest.raises(RuntimeError): EP.produce(slot)
    rows = core.store().rows("Episodes"); assert rows[-1]["status"] == "FAILED" and CK.has(rows[-1])
    assert seen and seen[0], "the first run drew no scene: this id's film keeps no moment"
    core.store().append("Video_Features", [{"ts": core.iso(), "video_key": "EPLATER", "format": "long", "arm": json.dumps({"drawn": [f"{x['template']}{x['variant']}" for _, x in seen[0]]})}])      # C8
    monkeypatch.setattr(ROOM, "run_room", lambda *a, **k: (_ for _ in ()).throw(AssertionError("the AI writing was paid for again")))
    r = EP.produce(slot)
    assert r["ok"], r
    assert c["text:scene"] == 1 and len(seen) == 2 and seen[1] == seen[0]                      # one writer's call over both runs; the same scenes on the shots
    led = {x["feature"]: x for x in core.store().rows("Feature_Ledger") if x["feature"] == "drawn_plan"}
    assert led["drawn_plan"]["status"] == "PASS", led                                          # judged on what the plan saw, not on the row planted after it


def test_without_checkpoints_a_video_of_the_arm_finishes_and_pays_the_call_once(monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import episode as EP
    slot = _setup(monkeypatch, setting); monkeypatch.setattr(EP, "now_utc", lambda: FROZEN + dt.timedelta(minutes=1)); setting("CHECKPOINT_ON", "FALSE")
    slot = (FROZEN + dt.timedelta(hours=11)).strftime("%Y-%m-%dT%H:%M:%SZ"); c = watch(monkeypatch)
    r = EP.produce(slot)                                                                       # C6: no plan.json to save again - never a crash
    assert r["ok"], r
    assert c["text:scene"] == 1


# ------------------------------------------------------------------ STEP 5: the cast as a sheet, the mouth on the voice - FOUND BUILT, proved here
# (b) drawn or absent is asserted by the accepted test_v12_motion.py (lines 357-361: has_art without art, with one character's art, with the switch
# off) and the positive half of (a) by test_v9_matrix.py::test_sheets_lifetime_cap_idempotent_and_lock (line 81): no twin is typed for them.
def test_the_cast_sheet_rig_is_built_and_off_until_his_art_is_approved(setting):
    from whatifs import sheets as SH, living as LV
    setting("LIVING_CHARACTERS_ON", "TRUE")                                                    # C15 (d): no later OLD_ cell may flip it silently
    assert SH.locked_portraits() == {} and not any(LV.has_art(k) for k in LV.SPEAKER_CHAR)     # (a), (b) a fresh Sheet: no sheet, nobody drawn
    row = {"ts": core.iso(), "character": "VALE", "expression": "neutral", "file": "drive:test-vale-neutral", "status": "LOCKED"}
    core.store().append("Character_Sheets", [dict(row, status="PENDING"), dict(row, expression="smug", file="")])
    assert SH.locked_portraits() == {} and not LV.has_art("DIRECTOR")                         # another status, or no file: not approved art
    core.store().append("Character_Sheets", [row])
    assert SH.locked_portraits() == {("VALE", "neutral"): "drive:test-vale-neutral"}
    assert LV.has_art("DIRECTOR") and not any(LV.has_art(k) for k in ("SKEPTIC", "JUDGE", "WITNESS"))
    t0, fps, n = 10.0, 30, 60                                                                  # (c) the mouth on the voice: a 2-second cutaway at the film's second 10
    words = [{"w": "the", "s": t0 + 0.2, "e": t0 + 0.5}, {"w": "moon", "s": t0 + 0.9, "e": t0 + 1.3}]       # the shape the voice writes (voice.py: film seconds)
    on = LV.speaking(words, t0, fps, n)
    inside = lambda f: any(int(w["s"] * fps - t0 * fps) - 1 <= f <= int(w["e"] * fps - t0 * fps) + 1 for w in words)
    assert on and all(inside(f) for f in on)
    assert any(5 <= f <= 16 for f in on) and any(26 <= f <= 40 for f in on)                  # at least one frame in each word
    assert len(on) < n                                                                         # never "speaking" in every frame


# ------------------------------------------------------------------ STEP 2: 2. the kit's contrast
def _rel(rgb): return sum(w * float(DRAWN.lum(c)) for w, c in zip((0.2126, 0.7152, 0.0722), rgb))


def test_every_text_colour_keeps_four_and_a_half_to_one_on_the_worst_ground():
    worst = tuple(round(255 * (1 - DRAWN.SCRIM) + c * DRAWN.SCRIM) for c in DRAWN.PALETTE["panel"]); assert worst == (59, 62, 67)
    assert abs(_rel(worst) - 0.0478) < 0.0005
    got = {k: round(DRAWN.ratio(_rel(DRAWN.PALETTE[k]), _rel(worst)), 1) for k in ("ink", "a", "b", "dim")}
    assert got == {"ink": 9.7, "a": 6.9, "b": 6.5, "dim": 5.2} and min(got.values()) >= 4.5
    assert DRAWN.ratio(_rel((90, 96, 104)), _rel(worst)) < 4.5                                 # a planted grey fails
    sc = dict(DRAWN.TEMPLATES["count"]["gold"], slots=dict(DRAWN.TEMPLATES["count"]["gold"]["slots"], label="#ff0000"))
    assert DRAWN.clean(sc) == (None, "not in the scene language: label")                       # a colour cannot be written into a slot


# ------------------------------------------------------------------ 7. the proof, both kinds of pairs measured
def _L(t, v=0, dur=8.0, cues=None, W=640, H=360, slots=None):
    sc = dict(DRAWN.TEMPLATES[t]["gold"], variant=v, **({"slots": slots} if slots else {}))
    return DRAWN.layout(DRAWN.expand(sc), W, H, dur, cues, **OPTS)


def test_the_proof_passes_the_gold_scenes_and_fails_each_planted_fault(monkeypatch, capsys):
    rows = []
    for t in DRAWN.TEMPLATES:
        for v in (0, 1):
            r = DRAWN.proof(_L(t, v), 30, 2.0); rows.append(("good", t, v, r["still_s"], r["kit_pct"])); assert r["ok"], (t, v, r)
    for dur, cues in ((8.0, None), (12.0, None), (8.0, [None, 8.0 - 1.2 - 0.9 + 0.15]), (12.0, [None, 12.0 - 1.2 - 0.9 + 0.15])):      # C2: a screen of text alone pulses too
        r = DRAWN.proof(_L("count", 0, dur, cues), 30, 2.0); rows.append(("good", "count", dur, r["still_s"], r["kit_pct"])); assert r["ok"], (dur, cues, r)
    two = {"label": "How high", "rungs": [{"t": "1 minute", "text": "Over the roofs"}, {"t": "1 day", "text": "Into space"}]}
    assert DRAWN.proof(_L("ladder", 0, 8.0, slots=two), 30, 2.0)["ok"]
    L = _L("count", 0); L["pulses"] = []; r = DRAWN.proof(L, 30, 2.0); rows.append(("bad: no pulse", "count", 0, r["still_s"], r["kit_pct"]))
    assert not r["ok"] and r["why"].startswith("it stands still")
    assert DRAWN.proof(_L("count", 0), 30, 2.0, budget_s=0.0)["why"] == "over the time limit"
    assert DRAWN.proof(_L("flow", 0, W=1920, H=1080), 30, 2.0)["ok"]                         # one layout at 1920: proved at its own size (a, the moving part, at 480)
    real = DRAWN.layer
    monkeypatch.setattr(DRAWN, "layer", lambda L_, t, draw=None: (lambda c, a: (np.clip(c + np.float32([60, -120, 60]), 0, 255), a))(*real(L_, t, draw)))      # the finisher's F-1: every kit colour off the palette, its pulse tint kept
    r = DRAWN.proof(_L("count", 0), 30, 2.0); rows.append(("bad: off the palette", "count", 0, r["still_s"], r["kit_pct"]))
    assert not r["ok"] and r["why"].startswith("only")
    print("\nDRAWN PROOF PAIRS (kind, template, variant or line, still_s, kit_pct):"); [print(" ", x) for x in rows]      # the builder writes these into the record


# ------------------------------------------------------------------ 8. ink, through the real encoder, at both work sizes
def _picture(tmp_path, W, H):
    from PIL import Image
    yy, xx = np.mgrid[0:H, 0:W]; im = np.dstack([(xx * 255 // max(1, W - 1)), (yy * 255 // max(1, H - 1)), ((xx + yy) % 255)]).astype(np.uint8)
    p = str(tmp_path / f"pic{W}.png"); Image.fromarray(im).save(p); return p


def test_ink_reads_the_text_on_the_finished_file_and_its_limit_stands_only_on_measured_pairs(tmp_path, monkeypatch, capsys):
    from whatifs import render as RN
    rows = []
    for W, H in ((640, 360), (1920, 1080)):
        monkeypatch.setattr(RN, "work_size", lambda W=W, H=H: (W, H)); monkeypatch.setattr(RN, "out_size", lambda W=W, H=H: (W, H))
        pic = _picture(tmp_path, W, H); f_ = RN.fps(); n = 8
        def enc(L, name, bg=pic):
            p = str(tmp_path / f"{name}{W}.mp4"); RN.drawn_segment(L, bg, p, n, int(7.5 * f_), int(8.0 * f_)); return RN.frame_at(p, (n - 2) / f_)
        for t in DRAWN.TEMPLATES:
            L = _L(t, 0, W=W, H=H); g = enc(L, t); assert g is not None
            v = DRAWN.ink(g, L); rows.append(("good", t, W, v)); assert v >= 4.5, (t, W, v)
        L = _L("compare", 0, W=W, H=H)
        still = str(tmp_path / f"still{W}.mp4"); from PIL import Image
        bgr = cv2.cvtColor(np.asarray(Image.open(pic).convert("RGB")), cv2.COLOR_RGB2BGR); RN._pipe(still, (bgr for _ in range(n)), n, W, H)
        rows.append(("bad: the still alone", "compare", W, DRAWN.ink(RN.frame_at(still, 0.1), L)))
        Lp = json.loads(json.dumps(L))
        for it in Lp["items"]:
            if it.get("text"): it["colour"] = "panel"
        rows.append(("bad: text in the panel's colour", "compare", W, DRAWN.ink(enc(Lp, "panel"), L)))
        La = json.loads(json.dumps(L))
        for it in La["items"]:
            if it.get("text"): it["alpha"] = 0.3
        rows.append(("bad: text at 30% opacity", "compare", W, DRAWN.ink(enc(La, "faint"), L)))
    print("\nDRAWN INK PAIRS (kind, template, width, ratio to 1):"); [print(" ", x) for x in rows]          # the builder writes these into the record
    goods = [x[3] for x in rows if x[0] == "good"]
    blank = [x[3] for x in rows if x[0] in ("bad: the still alone", "bad: text in the panel's colour")]
    faint = [x[3] for x in rows if x[0] == "bad: text at 30% opacity"]
    lim = float(core.DEFAULTS["DRAWN_INK_MIN"][0])
    assert len(goods) == 10 and len(blank) == 4 and len(faint) == 2, rows
    assert min(goods) >= 4.5, ("every gold scene's text reads at least 4.5 to 1 on the finished file", rows)
    assert max(blank) <= 1.5, ("a frame that does not carry our text reads about 1 to 1", rows)
    assert max(faint) <= 2.6, ("a text at 30% opacity is faint: under 2.6 to 1 (source 6 on this test's grounds: 1.9 to 2.5)", rows)
    assert max(blank + faint) < lim < min(goods), ("the cell's own limit lies between every measured bad and every measured good", lim, rows)


# ------------------------------------------------------------------ 11. check drawn_shown (its unit half; the master's half is in test_v12_drawn_film_b.py)
def test_check_drawn_shown_says_na_pass_and_fails_each_lie(setting):
    from whatifs import contract as CON
    shots, units, total = _film(); sc = {"v": 1, "template": "count", "variant": 0, "slots": DRAWN.from_graphic(G_COUNT)[0]["slots"], "cues": [], "by": "code"}
    withsc = [dict(s, scene=sc) if k == 1 else s for k, s in enumerate(shots)]
    ctx = lambda sh, dr: {"master": None, "shots": sh, "drawn": dr}
    arm = {"plan": {"arm": True}, "proof": {}, "L": {}, "states": []}
    setting("DRAWN_ON", "FALSE"); assert CON.p_drawn_shown(ctx(shots, arm)) == ("N/A", "not applicable: the drawn scenes are switched off")
    _arm_on(setting); assert CON.p_drawn_shown(ctx(shots, dict(arm, plan={"arm": False}))) == ("N/A", "not applicable: this video is not in the drawn arm")
    assert CON.p_drawn_shown(ctx(shots, arm)) == ("PASS", "the drawn arm held: no explaining moment in this film")
    st, why = CON.p_drawn_shown(ctx(withsc, dict(arm, proof={1: {"ok": False, "why": "its text reached only 1.2 to 1 on the finished file"}})))
    assert st == "PASS" and "0 scene(s) drawn, 1 shown as its still: 1: its text reached only" in why                  # a still is never a failure
    assert CON.p_drawn_shown(ctx(withsc, arm))[0] == "FAIL"                                                            # a scene, no drawn state, no reason
    assert CON.p_drawn_shown(ctx(shots, dict(arm, states=[(4.0, 6.0, 1, 0)])))[0] == "FAIL"                           # a state recorded drawn on a shot without a scene
    assert CON.p_drawn_shown(ctx(withsc, dict(arm, states=[(4.0, 6.0, 1, 0)], L={1: None})))[0] == "FAIL"            # recorded drawn, and its master cannot be read
