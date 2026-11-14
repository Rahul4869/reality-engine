"""v12 V2b - inside the format: the voice speaks to YOU now (counted sentence by sentence), the camera path (one place per act, eye level, one direction
of travel, judged on the render's record), the ending that is the format's own, a name chip only for a drawn character, F3 "The walk". Every rule is
proven both ways, one fault at a time; the real voice job and whole productions are run, so an unwired call is seen."""
import json, os, re, shutil
import pytest
from whatifs import core, contract as CON, formats as FMT, voice as VO, enforce as EN, fakes as FK, episode as EP, reactions as RX
from whatifs.org import inside as IN, audience as AUD, registry as REG, levers as LV, rnd as RND

OWN_IDS = ("EP209908010900", "EP209908080900", "EP209908150900")      # the whole productions of this file: ids no other test file uses (a test proves it)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def ctx(text, fmt="F1"): return {"room": {"script": {"script": text}}, "d": {"format": fmt}}

# the passages of the design memo (3.1), line by line, and the figures measured with the repo's own sentence cut (the record carries them)
GOOD1 = ["[DIRECTOR] Your coffee lifts out of the cup.", "[DIRECTOR] You watch it hang there, a brown ball the size of a plum.", "[DIRECTOR] You poke it and it wobbles.",
         "[SKEPTIC] Okay, I am not cleaning that up.", "[DIRECTOR] You don't have to, because nothing in your kitchen falls any more.",
         "[DIRECTOR] You let go of the spoon and it stays where your hand left it.", "[DIRECTOR] You push off the counter by accident and your feet leave the floor.",
         "[DIRECTOR] The ceiling arrives slowly.", "[DIRECTOR] You put a hand up and stop yourself against the lamp.", "[SKEPTIC] So my whole flat is a fish tank now?",
         "[DIRECTOR] Your whole street is."]
GOOD2 = GOOD1 + ["[DIRECTOR] Gravity is the pull between any two things that have mass.", "[DIRECTOR] It is weak, and it never switches off.",
                 "[DIRECTOR] Today it has switched off.", "[DIRECTOR] Nobody knows for how long."]
GOOD2_5 = GOOD2 + ["[DIRECTOR] The last time anything like it was measured was never."]
BAD1 = ["Gravity is one of the four fundamental forces.", "It was described by Newton and later by Einstein.", "Every object with mass attracts every other object.",
        "The force gets weaker with distance.", "Astronauts in orbit are not weightless because gravity is absent.", "They are falling around the Earth all the time.",
        "Without gravity the atmosphere would drift into space.", "Nothing on the ground would stay there."]
GOOD_TRIAL = ["[DIRECTOR] You wake up and your pillow is on the ceiling.", "[DIRECTOR] You reach for it, and your arm keeps rising.",
              "[SKEPTIC] Preposterous! Gravity does not take mornings off.", "[JUDGE] Sit down, Doctor. The court has seen your pillow.",
              "[DIRECTOR] Exhibit A: every cup in your kitchen, floating at eye height.", "[WITNESS] The record shows it began at six this morning.",
              "[SKEPTIC] Then I shall prove it with Prototype No. 41.", "[SKEPTIC] Observe. I release the apple, and it falls like any apple.",
              "[DIRECTOR] It is not falling, Doctor. You are holding the string.", "[JUDGE] Mm. You at home, look at your own hands right now.",
              "[JUDGE] If they stay where you leave them, this case is yours.", "[DIRECTOR] By noon your street is full of people tied to lamp posts.",
              "[WITNESS] Nobody on record has ever needed a rope to stay home.", "[JUDGE] Here's what's true: you would last one day without the pull of the ground."]
def J(lines): return "\n".join(lines)
def no_foil(lines): return [l for l in lines if not l.startswith("[SKEPTIC]")]

@pytest.fixture
def inside(setting):
    setting("INSIDE_ON", "TRUE"); setting("VIEWER_SEAT_ON", "TRUE")
    yield
    FMT.use("")

# ------------------------------------------------------------------ 1. the beat of a line, and a unit that knows it
def test_a_heading_gives_its_own_number_or_counts_on_and_lines_before_any_heading_are_beat_0():
    text = "[DIRECTOR] Before.\n## BEAT 4\n[DIRECTOR] Four.\n\n## Notes for the editor\n[SKEPTIC] Still four.\n## beat\n[DIRECTOR] Five.\n## BEAT 9\n[DIRECTOR] Nine."
    clean, beats = IN.line_beats(text)
    assert clean == "[DIRECTOR] Before.\n[DIRECTOR] Four.\n\n[SKEPTIC] Still four.\n[DIRECTOR] Five.\n[DIRECTOR] Nine." and beats == [0, 4, 4, 4, 5, 9]      # the number written in it wins; '## Notes' is never spoken and is no beat
    c2, marks, b2 = EP._strip_beats(text); assert c2 == clean and b2 == beats and marks == [1, 2, 3, 4]                 # the episode's own strip gives the same clean text and the same beats
    assert IN.line_beats("## BEAT\n[DIRECTOR] One.\n## BEAT\n[DIRECTOR] Two.")[1] == [1, 2]                              # headings without a number count from 1

def test_a_unit_knows_the_beat_of_its_line_and_the_timeline_carries_it(tmp_path):
    from tools.rehearsal import ToneVoice
    text = "## BEAT 1\n[DIRECTOR] One. Still one.\n[SKEPTIC] Also one?\n## BEAT 2\n[DIRECTOR] Two [SKEPTIC] and a second speaker on the same line.\n## BEAT 3\n[DIRECTOR] Three."
    clean, beats = IN.line_beats(text)
    us = VO.parse_script(clean, line_beats=beats); assert [u.beat for u in us] == [1, 1, 1, 2, 2, 3] and not any("BEAT" in u.text for u in us)      # a heading is never spoken
    assert {u.beat for u in VO.parse_script(clean)} == {0} and {u.beat for u in VO.parse_script(clean, line_beats=[1])} == {0, 1}      # no list, or a list too short: beat 0
    r = VO.narrate(clean, VO.Blend("T", {"af_heart": 1.0}), str(tmp_path / "v"), seed="t", backend=ToneVoice(), line_beats=beats)
    tl = json.load(open(r.timeline_path)); assert [u["beat"] for u in tl["units"]] == [1, 1, 1, 2, 2, 3]

def test_the_reaction_tags_and_the_breathing_pauses_keep_the_beat(setting):
    setting("VIEWER_SEAT_ON", "TRUE")
    text = "## BEAT 2\n" + "\n".join(f"[DIRECTOR] [reveal] Line {k} brings a big number like {k}00." if k % 2 == 0 else "[SKEPTIC] Whoa, no way." for k in range(40))
    clean, beats = IN.line_beats(text); us = VO.parse_script(clean, line_beats=beats)
    assert {u.beat for u in RX.ensure_units(us)} == {2} and any(u.tag in ("wow", "gasp") for u in us)                  # tags changed in place, beats kept
    assert {u.beat for u in AUD.breathe(us)} == {2} and any(u.gap_before > 0 for u in us)                              # pauses placed in place, beats kept

# ------------------------------------------------------------------ 2. the measure: the passages of the memo and their measured figures
def test_the_six_passages_and_f3s_two_give_exactly_the_figures_of_the_record(inside):
    for name, lines, fmt, ins, n, share, run in (("GOOD-1", GOOD1, "F1", 10, 11, 90.9, 1), ("GOOD-2", GOOD2, "F1", 10, 15, 66.7, 4), ("GOOD-2 and a fifth", GOOD2_5, "F1", 10, 16, 62.5, 5),
                                                 ("BAD-1", BAD1, "F1", 0, 8, 0.0, 8), ("GOOD-TRIAL", GOOD_TRIAL, "F2", 9, 15, 60.0, 4),
                                                 ("F3 good", no_foil(GOOD1), "F3", 8, 9, 88.9, 1), ("F3 edge", no_foil(GOOD2), "F3", 8, 13, 61.5, 4)):
        r = IN.report(J(lines), fmt); assert (r["inside"], r["n"], r["share_pct"], r["run"]) == (ins, n, share, run), (name, r)
    assert IN.report(J(GOOD1), "F1")["problems"] == [] and IN.report(J(GOOD2), "F1")["problems"] == []                  # good: inside every rule; GOOD-2 at the run limit
    assert IN.report(J(GOOD_TRIAL), "F2")["problems"] == [] and IN.report(J(no_foil(GOOD2)), "F3")["problems"] == []    # the trial's good passage; the walk's edge passes by 1.5 points
    p = IN.report(J(GOOD2_5), "F1")["problems"]; assert len(p) == 1 and p[0].startswith("5 sentences in a row explain from outside (at most 4), from: 'Gravity is the pull"), p      # rule (b) and nothing else
    p = IN.report(J(BAD1), "F1")["problems"]
    assert p[0].startswith("only 0 of 8 sentences (0%) speak to the viewer") and p[1].startswith("8 sentences in a row") and p[2].startswith("beat 0 explains and never shows"), p

def test_the_offline_writers_as_they_wrote_before_this_batch_fail_their_floor(setting):
    """BAD-2 and BAD-TRIAL of the memo: the stand-in script as d8101c8 writes it (the switch off: byte for byte the older reply) is under the floor of
    F1 and of the trial (the experiment measured 33 to 35% and 26% on the whole productions, with the hook and the asks in them)."""
    for fmt, floor in (("F1", 50.0), ("F2", 40.0)):
        with FMT.using(fmt): text = json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"]
        r = IN.report(text, fmt); assert r["n"] >= 8 and r["share_pct"] < floor and r["problems"], (fmt, r)

# ------------------------------------------------------------------ 3. what counts as inside
def test_a_you_in_the_past_is_not_inside_and_a_wish_or_an_if_is():
    for s in ("You woke up on the ceiling this morning.", "You slowly opened the door to the street.", "You noticed the cup was gone.", "You walked into the kitchen again."):
        assert IN.past(s) and not IN.is_inside(s, "DIRECTOR", "F1"), s
    for s in ("If you were on the Moon, you would weigh less.", "You wish you were taller today.", "Imagine you had wings for an hour.",
              "You need a rope to stay home.", "You speed past the bus stop.", "You exceed every limit today.", "You open the door and look up."):
        assert not IN.past(s) and IN.is_inside(s, "DIRECTOR", "F1"), s
    assert not IN.is_inside("The ceiling arrives slowly.", "DIRECTOR", "F1")

def test_the_foils_I_puts_the_viewer_inside_in_F1_and_never_in_a_trial_or_from_the_guide():
    s = "Okay, I am not cleaning that up."
    assert IN.is_inside(s, "SKEPTIC", "F1") and not IN.is_inside(s, "DIRECTOR", "F1") and not IN.is_inside(s, "SKEPTIC", "F2") and not IN.is_inside(s, "SKEPTIC", "F3")

def test_a_short_sentence_is_a_reaction_and_is_not_counted_and_a_label_is_read_by_the_voices_own_parser():
    ss = IN.sentences("[DIRECTOR] Whoa. You see it now.\n**Curious One:** I am not cleaning that up.\n[THE CURIOUS ONE]\nSo my whole flat is a fish tank?")
    assert ss == [("You see it now.", "DIRECTOR", 0), ("I am not cleaning that up.", "SKEPTIC", 0), ("So my whole flat is a fish tank?", "SKEPTIC", 0)], ss

def test_seven_counted_sentences_are_not_judged_and_eight_are(inside):
    r = IN.report(J(BAD1[:7]), "F1"); assert r["n"] == 7 and r["problems"] == []
    assert IN.report(J(BAD1), "F1")["problems"]

def test_a_beat_that_explains_before_it_shows_fails_and_one_that_shows_first_passes(inside):
    first = ["## BEAT 1"] + GOOD1[:5] + ["## BEAT 2", "[DIRECTOR] Scientists call it microgravity, and it is everywhere now."] + GOOD1[5:]
    p = IN.report(J(first), "F1")["problems"]; assert p == ["beat 2 explains before it shows: 'Scientists call it microgravity, and it is everywhere'"], p
    after = ["## BEAT 1"] + GOOD1[:5] + ["## BEAT 2"] + GOOD1[5:7] + ["[DIRECTOR] Scientists call it microgravity, and it is everywhere now."] + GOOD1[7:]
    assert IN.report(J(after), "F1")["problems"] == []

# ------------------------------------------------------------------ 4. the check, the brief, the one fix
def test_check_viewer_inside_passes_holds_and_says_na(inside, setting):
    s, ev = CON.p_viewer_inside(ctx(J(GOOD1)))
    assert s == CON.PASS and ev == "10 of 11 sentences (90.9%) inside the scene (floor 50%); the longest run from outside 1 (limit 4); no act explains before it shows", ev
    s, ev = CON.p_viewer_inside(ctx(J(BAD1))); assert s == CON.FAIL and ev.startswith("only 0 of 8 sentences (0%)"), ev
    assert CON.p_viewer_inside(ctx(J(GOOD_TRIAL), "F2"))[0] == CON.PASS and CON.p_viewer_inside(ctx(J(BAD1), "F2"))[0] == CON.FAIL
    assert CON.p_viewer_inside(ctx(J(BAD1), ""))[0] == CON.NA                                                         # no format on the episode
    setting("INSIDE_MIN_PCT_F1", "95"); assert CON.p_viewer_inside(ctx(J(GOOD1)))[0] == CON.FAIL; setting("INSIDE_MIN_PCT_F1", "50")      # the floor is the format's cell
    setting("LECTURE_MAX_F1", "3"); assert CON.p_viewer_inside(ctx(J(GOOD2)))[0] == CON.FAIL; setting("LECTURE_MAX_F1", "4")             # and so is the run limit
    setting("INSIDE_ON", "FALSE"); s, ev = CON.p_viewer_inside(ctx(J(BAD1))); assert s == CON.NA and "INSIDE_ON" in ev
    setting("INSIDE_ON", "TRUE"); setting("VIEWER_SEAT_ON", "FALSE"); assert CON.p_viewer_inside(ctx(J(BAD1)))[0] == CON.NA

def test_a_format_can_never_loosen_viewer_inside_and_its_contract_row(inside):
    stage = {f[0]: f[1] for f in CON.FEATURES}; assert stage["viewer_inside"] == "script" and "viewer_inside" not in FMT.DEVICES
    for k in FMT.FORMATS: assert FMT.rule("viewer_inside", k) == "must", k
    r = CON.run("script", dict(ctx(J(BAD1)), ep="EPIN1"), "EPIN1", write=False)
    assert ("viewer_inside" in [f for f, _ in r["failed"]]) and not r["ok"]

def test_the_writer_is_told_the_floor_and_the_limit_of_the_format_in_the_making(inside, setting):
    assert IN.brief() == ""                                                                                            # no format in the making
    with FMT.using("F1"):
        b = IN.brief(); assert b.startswith("INSIDE THE SCENE (code counts it; a script under it goes back): at least 50% of your sentences") and "never more than 4 sentences in a row" in b
    with FMT.using("F2"): assert "at least 40%" in IN.brief() and "never more than 6 sentences" in IN.brief()
    from whatifs import room as ROOM
    with FMT.using("F1"): assert ROOM._inside_brief() == IN.brief()
    src = open(os.path.join(ROOT, "whatifs", "room.py"), encoding="utf-8").read(); assert '_format_block("writer"), _inside_brief()) if x))' in src      # in the writer's brief, beside the format's text
    setting("INSIDE_ON", "FALSE")
    with FMT.using("F1"): assert IN.brief() == ""

def test_the_one_fix_carries_the_voice_problem_and_nothing_when_inside(inside, monkeypatch, setting):
    asked = []
    monkeypatch.setattr("whatifs.models.ask", lambda *a, **k: asked.append(a[2]) or {"script": J(GOOD1)})
    with FMT.using("F1"):
        iss = IN.issues(J(BAD1)); assert len(iss) == 1 and iss[0].startswith("INSIDE THE SCENE: only 0 of 8 sentences") and iss[0].endswith("never more than 4 sentences in a row about anything but the viewer")
        sc, got = EN.fix_all({"script": J(BAD1)}, "brief", {}, "EPFIX1", "long")
        assert iss[0] in got and asked and "INSIDE FIX" in asked[0] and sc["script"] == J(GOOD1)
        assert IN.issues(J(GOOD1)) == []
        asked.clear(); sc, got = EN.fix_all({"script": J(BAD1)}, "brief", {}, "EPFIX1", "short"); assert not any("INSIDE THE SCENE" in x for x in got)      # a long video's rule only
    assert IN.issues(J(BAD1)) == []                                                                                  # no format in the making
    setting("INSIDE_ON", "FALSE")
    with FMT.using("F1"): assert IN.issues(J(BAD1)) == []

# ------------------------------------------------------------------ 5. the offline writers pass their own format's rule (and are untouched with the switch off)
def test_the_offline_writer_passes_the_voice_rule_of_its_format_and_is_byte_for_byte_the_older_one_with_the_switch_off(inside, setting):
    prompt = "Write the narration. ~300 words"
    for fmt, want in (("F1", 60.0), ("F2", 50.0)):
        with FMT.using(fmt): text = json.loads(FK.fake_reply("writer", prompt))["script"]
        r = IN.report(text, fmt); assert r["share_pct"] >= want and r["problems"] == [] and r["n"] >= 8, (fmt, r)
    setting("INSIDE_ON", "FALSE")
    with FMT.using("F1"): off = json.loads(FK.fake_reply("writer", prompt))["script"]
    lines = [l for l in FK._lines(12)]; assert all(l.split("]", 1)[1].strip() in off for l in lines if not l.startswith("[pause"))      # the older pool, word for word

# ------------------------------------------------------------------ 6. the picture half of SHOW: every beat opens on a picture
def test_a_graphic_or_real_footage_that_opens_a_beat_becomes_a_still_and_a_marked_shot_never_does(inside):
    units = [{"text": f"Line {i}.", "start": i * 3.0, "end": i * 3.0 + 2.5, "beat": b} for i, b in enumerate([1, 1, 2, 2, 3, 3, 4, 4])]
    shots = [{"type": t, "prompt": f"shot {i}", "graphic": {"kind": "counter"}} for i, t in enumerate(["still", "graphic", "graphic", "still", "stock", "still", "graphic", "still"])]
    shots[6]["promise"] = True
    with FMT.using("F1"): out = IN.open_acts(shots, units)
    assert [s["type"] for s in out] == ["still", "graphic", "still", "still", "still", "still", "graphic", "still"], out      # beats 2 and 3 open on a picture; a graphic inside a beat stays
    assert out[2].get("seat") == "a beat opens on a picture" and "graphic" not in out[2] and out[6]["type"] == "graphic"   # the marked shot is never touched
    with FMT.using("F1"): assert IN.open_acts(shots, [{k: v for k, v in u.items() if k != "beat"} for u in units]) == shots      # a timeline saved without beats: left alone
    assert IN.open_acts(shots, units) == shots                                                                         # no format in the making: left alone

def test_the_seat_and_the_beat_repair_turn_a_shot_into_a_still_with_one_helper(setting):
    setting("VIEWER_SEAT_ON", "TRUE"); setting("STYLE_LOCK", "LOCKSTYLE")
    out = [{"type": "graphic", "prompt": "", "graphic": {}, "search": "x"}]; AUD.make_still(out, [{"text": "Your cup floats."}], 0, "why", hero=True)
    assert out[0] == {"type": "still", "prompt": "Your cup floats. LOCKSTYLE", "hero": True, "seat": "why"}, out
    s = AUD.shape([{"type": "graphic", "prompt": "a graph"}], [{"text": "x", "start": 0}], {"thumb_prompt": "the promise"})
    assert s[0]["type"] == "still" and s[0]["prompt"] == "the promise. LOCKSTYLE" and s[0]["seat"] == "first picture"   # audience.shape does what it did

def test_produce_opens_every_beat_on_a_picture_after_the_seat_and_before_the_animation_director():
    import inspect
    src = inspect.getsource(EP.produce)
    a, b, c = src.index("AUD.shape(S_[\"shots\"]"), src.index("S_[\"shots\"] = shots = INS.open_acts(shots, units)"), src.index("ANIM.apply(shots, units, plan)")
    assert a < b < c                                                                                                   # D13's seat, then every beat on a picture, then the scenes are placed

# ------------------------------------------------------------------ 7. the wiring
def test_the_voice_rule_is_wired_owners_levers_protected_and_classified():
    assert REG.CHECK_OWNER["viewer_inside"] == "D13" and "whatifs/org/inside.py" in REG.DEPTS["D13"]["wraps"]
    from tools import repair as RP; assert "whatifs/org/inside.py" in RP.PROTECTED
    for k in ("INSIDE_MIN_PCT_F1", "INSIDE_MIN_PCT_F2", "INSIDE_MIN_PCT_F3"):
        assert REG.may_change("D13", k) and LV.LEVERS[k]["owner"] == "down" and (LV.LEVERS[k]["lo"], LV.LEVERS[k]["hi"], LV.LEVERS[k]["step"]) == (20, 80, 5) and LV.LEVERS[k]["checks"] == ("viewer_inside",), k
    for k in ("LECTURE_MAX_F1", "LECTURE_MAX_F2", "LECTURE_MAX_F3"):
        assert REG.may_change("D13", k) and LV.LEVERS[k]["owner"] == "up" and (LV.LEVERS[k]["lo"], LV.LEVERS[k]["hi"], LV.LEVERS[k]["step"]) == (2, 8, 1) and LV.LEVERS[k]["checks"] == ("viewer_inside",), k
    assert "viewer_inside" not in RND.ORG_CHECKS and "viewer_inside" in RND.metrics()                                 # a promise about the show (SHOW_CHECKS raised)
    assert [FMT.FORMATS[k]["inside"] for k in ("F1", "F2", "F3")] == ["INSIDE_MIN_PCT_F1", "INSIDE_MIN_PCT_F2", "INSIDE_MIN_PCT_F3"]
    assert (FMT.inside_min("F1"), FMT.inside_min("F2"), FMT.inside_min("F3"), FMT.lecture_max("F1"), FMT.lecture_max("F2"), FMT.lecture_max("F3")) == (50, 40, 60, 4, 6, 4)

def test_the_whole_productions_of_this_file_use_ids_no_other_test_file_uses():
    here = os.path.basename(__file__)
    for f in os.listdir(os.path.join(ROOT, "tests")):
        if f.endswith(".py") and f != here:
            t = open(os.path.join(ROOT, "tests", f), encoding="utf-8").read()
            for i in OWN_IDS: assert i not in t, (f, i)

# ------------------------------------------------------------------ 8. a whole F1 production: the beats reach the units, the voice is inside
def _start(monkeypatch, setting, fmt):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import ladder as LAD
    E2E._start(monkeypatch, setting); setting("FORMAT_FORCE", fmt); setting("INSIDE_ON", "TRUE"); setting("ENDINGS_ON", "TRUE"); LAD.override("owner", "make it anyway")

def _led(ep): return {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}

def test_a_whole_f1_production_carries_its_beats_to_the_units_and_speaks_to_you(monkeypatch, setting):
    from tests import test_v12_opening_e2e as E2E
    _start(monkeypatch, setting, "F1"); ep = OWN_IDS[0]
    r = EP.produce(E2E._slot(10), episode_id=ep); led = _led(ep)
    tl = json.load(open(os.path.join(core.WORK, ep, "voice_timeline.json")))
    assert len({u["beat"] for u in tl["units"]}) >= 2, sorted({u["beat"] for u in tl["units"]})                       # the beats reach the units (the break: they never do)
    assert led["viewer_inside"][0] == "PASS" and "inside the scene (floor 50%)" in led["viewer_inside"][1], led["viewer_inside"]
    script = json.load(open(os.path.join(core.WORK, ep, "plan.json")))["room"]["script"]["script"]                  # the ending is the format's (step 2)
    asks = [CTA.is_ask(CTA._peel(l)[3]) for l in script.split("\n") if l.strip() and not l.startswith("##")]
    assert [a for a in asks if a] == ["subscribe"], asks                                                              # one subscribe ask, nothing else
    assert led["format_ending"][0] == "PASS" and led["format_ending"][1].startswith("ends on its question: ") and "asks in this video: subscribe 1" in led["format_ending"][1], led["format_ending"]
    assert "next simulation" not in script.lower() and FMT.ending_report(script, "F1")["last"].endswith("?")          # no tease; the last line a question
    assert r.get("ok"), r
    shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)

# ------------------------------------------------------------------ 9. THE ENDING IS THE FORMAT'S (3.3): an ask only where code can recognise one
from whatifs import cta as CTA, room as ROOM, prompts as P, engage as EG, format_engine as FE, overlay as OV
NOT_ASKS = ["Nothing like this has ever happened to you.", "You have never felt anything like it.", "Would you like it to stay?", "You send it spinning across the room.",
            "You want to tell your friend, but your phone is floating too.", "You cannot share it with anyone.", "You text it to your sister.",
            "Your newspaper subscription is the last normal thing left.",
            "Follow me to the roof.", "Follow me.", "Now follow me across the road.", "The air would hit like a wall.", "Raindrops hit like stones.", "You tap like mad on the glass.",
            "You press like you mean it, and the door does not move.", "You hit that like a brick wall.", "Hit like a hammer, the wind takes the door.", "Tell your friend to run.",
            "Then tell your friend and watch him laugh.", "Send it to the moon and it comes back.", "Send it to your mother.", "Text it to your sister and it arrives yesterday.",
            "Share it with nobody.", "So share the last of the water.", "Pass it on the left, the way you always do.", "Comment is useless here.",
            "You ring the bell and nobody comes.", "Ring the bell. Nobody comes.", "You press the bell on the bus.", "Hit the bell on the counter and it floats away."]
ASKS = [("Subscribe for more.", "subscribe"), ("Please subscribe.", "subscribe"), ("Don't forget to subscribe.", "subscribe"), ("Hit the subscribe button.", "subscribe"),
        ("So tap like.", "like"), ("Hit like if you would have survived that.", "like"), ("And smash that like button.", "like"),
        ("Send this to the friend who would try it.", "share"), ("Send it to a friend who asks what if at dinner.", "share"), ("Share this video with someone who would panic.", "share"),
        ("Share it with one person.", "share"), ("Forward this to someone curious.", "share"), ("Text this to your group chat.", "share"),
        ("Tell me in the comments what you would do.", "comment"), ("Drop a comment below.", "comment"), ("Follow us for more.", "comment")]

@pytest.fixture
def endings(setting):
    setting("ENDINGS_ON", "TRUE")
    yield
    FMT.use("")

def test_thirty_story_sentences_are_never_asks_and_sixteen_asks_and_every_pool_line_are(endings):
    assert [s for s in NOT_ASKS if CTA.is_ask(s)] == [] and len(NOT_ASKS) == 30
    assert [(s, k, CTA.is_ask(s)) for s, k in ASKS if CTA.is_ask(s) != k] == [] and len(ASKS) == 16
    for pools in (CTA.POOLS, CTA.TRIAL_POOLS):
        for kind, entries in pools.items():
            for entry in entries:
                for line in entry: assert CTA.is_ask(line[2]) == kind and CTA.is_ask("  " + line[2].upper() + " ") == kind, line      # a reply line goes with its ask
    assert CTA.kind_of_text("Nothing like this has ever happened to you.") == "like"                                   # the older recogniser stays for "is one there?" only
    assert CTA.is_ask("So hit the bell.") is None                                                                       # a bell alone is never an ask

def test_strip_removes_only_the_kinds_a_format_does_not_carry_and_every_ask_in_the_tail(endings):
    body = [f"[DIRECTOR] Line {i} goes on about you and the floor." for i in range(12)]
    lines = body[:4] + ["[SKEPTIC] [aside] So tap like."] + body[4:8] + ["[SKEPTIC] [aside] Please subscribe."] + body[8:] + ["[DIRECTOR] Share it with one person."]
    text = J(lines)
    out, gone = CTA.strip(text, keep=("subscribe",)); assert gone == ["[SKEPTIC] [aside] So tap like.", "[DIRECTOR] Share it with one person."] and "Please subscribe." in out
    out, gone = CTA.strip(text, keep=("subscribe",), tail_from=9); assert "[SKEPTIC] [aside] Please subscribe." in gone                     # in the tail: any kind goes
    out, gone = CTA.strip(text, keep=()); assert len(gone) == 3 and not any(CTA.is_ask(CTA._peel(l)[3]) for l in out.split("\n"))
    assert CTA.strip(text, keep=("like", "subscribe", "share")) == (text, [])                                         # the trial keeps its three
    two = CTA._fmt(*CTA.POOLS["subscribe"][0][0]) + "\n" + CTA._fmt(*CTA.POOLS["subscribe"][0][1])
    assert len(CTA.strip(J(body[:6]) + "\n" + two + "\n" + J(body[6:]), keep=())[1]) == 2                            # a two-line ask leaves no reply to nothing

def test_the_tail_is_measured_in_words_205_words_and_1275_words(endings):
    w = lambda n: "\n".join("[DIRECTOR] " + " ".join(["word"] * 5) + "." for _ in range(n // 5))
    assert FMT.tail(w(205)) == 37                       # T = min(40 s x 150 / 60 = 100, 0.12 x 205 = 24.6): the lines that begin at or after word 180.4
    assert FMT.tail(w(1275)) == 235                     # T = min(100, 153) = 100: the lines that begin at or after word 1175 (the last 40 seconds)

def test_ensure_adds_only_the_formats_kinds_never_in_the_tail_and_the_trial_as_before(endings):
    lines = [f"[DIRECTOR] [calm] Line {i} is about you and your kitchen floor today." for i in range(20)]
    text = J(lines)
    with FMT.using("F1"):
        new, added, _ = CTA.ensure(text, "EPA", "", kinds=FMT.asks(), before=FMT.tail(text)); assert added == ["subscribe"]
        sp = [l for l in new.split("\n") if l.strip()]; k = [i for i, l in enumerate(sp) if CTA.is_ask(CTA._peel(l)[3])]
        assert len(k) == 1 and k[0] < FMT.tail(new) and FMT.ending_report(new + "\n[DIRECTOR] Would you keep it?", "F1")["problems"] == []
    assert CTA.ensure(text, "EPA", "") == CTA.ensure(text, "EPA", "", kinds=None, before=None) and sorted(CTA.ensure(text, "EPA", "")[1]) == ["like", "share", "subscribe"]
    assert CTA.ensure(text, "EPA", "", kinds=(), before=3)[1] == []                                                     # F3: none
    new, added, _ = CTA.ensure(text, "EPA", "", kinds=("subscribe",), before=12)                                         # the slot search itself stops before the tail
    sp = [l for l in new.split("\n") if l.strip()]; assert added == ["subscribe"] and [i for i, l in enumerate(sp) if CTA.is_ask(CTA._peel(l)[3])][0] == 12      # after slot 11: the slot is never at or after `before` (DESIGN QUESTION 8)
    assert CTA.ensure(text, "EPA", "", kinds=("subscribe",), before=5)[1] == []                                        # no calm slot before the tail: nothing added

def test_the_room_places_only_the_formats_asks_counts_what_it_removed_and_leaves_a_trial_as_it_was(endings, setting):
    lines = [f"[DIRECTOR] [calm] Line {i} is about you and your kitchen floor today." for i in range(20)]
    text = J(lines[:5] + ["[SKEPTIC] [aside] So tap like."] + lines[5:15] + ["[DIRECTOR] [calm] Share it with one person."] + lines[15:])
    d = {}
    with FMT.using("F1"):
        sc, added, _ = ROOM._place_asks({"script": text}, d, "EPR")
        kinds = [CTA.is_ask(CTA._peel(l)[3]) for l in sc["script"].split("\n")]; assert [k for k in kinds if k] == ["subscribe"] and added == ["subscribe"]
        assert d["asks_removed"] == {"like": 1, "share": 1} and ROOM._asks_words() == "the one subscribe ask"
    d2 = {}
    with FMT.using("F2"): assert ROOM._place_asks({"script": text}, d2, "EPR") == ({"script": CTA.ensure(text, "EPR", "")[0]}, *CTA.ensure(text, "EPR", "")[1:]) and d2 == {}

def test_what_strip_leaves_and_ensure_adds_never_fails_the_check_on_the_offline_writer_and_the_thirty_sentences(endings, setting):
    for fmt in ("F1", "F3"):
        with FMT.using(fmt):
            base = json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"]
            if fmt == "F3": base += "\n[DIRECTOR] You are home, and you see your street differently."
            for extra in [""] + NOT_ASKS + [s for s, _ in ASKS]:
                lines = base.split("\n"); lines.insert(len(lines) - 1, "[DIRECTOR] " + extra) if extra else None
                text = J(lines); text, _gone = CTA.strip(text, keep=FMT.asks(), tail_from=FMT.tail(text))
                text = CTA.ensure(text, "EPB", "", kinds=FMT.asks(), before=FMT.tail(text))[0]
                r = FMT.ending_report(text, fmt); assert r["problems"] == [], (fmt, extra, r)
                if extra in NOT_ASKS: assert extra in text, (fmt, extra)                                                # a story sentence survives

def test_the_last_line_of_each_ending(endings):
    pre = J(GOOD1)
    for end in ("Would you?", "Keep it?", "Would you stay?", "Keep it, or give it back?", 'Would you keep it?"'):
        assert FMT.ending_report(pre + "\n[DIRECTOR] " + end, "F1")["problems"] == [], end
    for end in ("Subscribe for more.", "Next simulation: What if the Moon left tonight?"):
        p = FMT.ending_report(pre + "\n[DIRECTOR] " + end, "F1")["problems"]; assert p and "an ask or a pointer to another video in the last seconds" in p[-1], (end, p)
    assert FMT.ending_report(pre + "\n[DIRECTOR] Your whole street is floating.", "F1")["problems"][0].startswith("the last line is not the question to the viewer")
    long_last = pre + "\n[DIRECTOR] You float above your bed and the whole house hums around you like a ship at sea all night long. Subscribe for more."
    assert FMT.tail(long_last) == len(GOOD1) + 1 and any("an ask or a pointer" in x for x in FMT.ending_report(long_last, "F1")["problems"])      # the last sentence alone, no tail line
    assert FMT.ending_report(pre + "\n[DIRECTOR] You're home.", "F3")["problems"] == []
    assert FMT.ending_report(pre + "\n[DIRECTOR] The street is quiet now.", "F3")["problems"][0].startswith("the last line is not the arrival")
    assert FMT.ending_report(pre + "\n[DIRECTOR] Are you home?", "F3")["problems"][0].startswith("the last line is not the arrival")
    assert FMT.ending_report(pre + "\n[DIRECTOR] Subscribe for more.", "F2")["problems"] == []                         # a trial: its own devices judge it

def test_check_format_ending_passes_holds_and_says_na(endings, setting):
    good = J(GOOD1 + ["[SKEPTIC] So would you keep it?"])
    c = {"room": {"script": {"script": good}}, "d": {"format": "F1", "asks_removed": {"like": 1, "share": 1}}}
    s, ev = CON.p_format_ending(c); assert s == CON.PASS and ev == "ends on its question: 'So would you keep it?'; no ask and no pointer in the tail; asks in this video: none; removed by code: 2", ev
    s, ev = CON.p_format_ending(ctx(J(GOOD1 + ["[DIRECTOR] Next simulation: What if the Moon left tonight?"]))); assert s == CON.FAIL and "pointer to another video" in ev, ev
    s, ev = CON.p_format_ending(ctx(good, "F2")); assert s == CON.NA and "ends on a tease" in ev
    assert CON.p_format_ending(ctx(good, ""))[0] == CON.NA
    setting("ENDINGS_ON", "FALSE"); s, ev = CON.p_format_ending(ctx(J(GOOD1))); assert s == CON.NA and "ENDINGS_ON" in ev
    setting("ENDINGS_ON", "TRUE")
    stage = {f[0]: f[1] for f in CON.FEATURES}; assert stage["format_ending"] == "script" and "format_ending" not in FMT.DEVICES
    for k in FMT.FORMATS: assert FMT.rule("format_ending", k) == "must"
    r = CON.run("script", dict(ctx(J(GOOD1 + ["[DIRECTOR] Subscribe for more."])), ep="EPEN1"), "EPEN1", write=False)
    assert "format_ending" in [f for f, _ in r["failed"]] and not r["ok"]

def test_no_tease_under_the_ladder_or_in_a_format_that_does_not_end_on_one_and_the_older_promise_is_still_honoured(endings, setting):
    setting("NEXT_TEASE_ON", "TRUE"); setting("SHORTS_TRACK_ON", "TRUE")
    spine = {"next_tease": {"line": "Next simulation: the Moon leaves.", "premise": "the Moon leaves", "headline": "The Moon leaves"}}
    with FMT.using("F2"):
        setting("LADDER_ON", "FALSE"); assert ROOM.tease_on() and ROOM.tease_brief(spine)                                # a trial without the ladder ends on its tease
        pitch = [{"premise": "The Moon leaves tonight for good", "family": "y", "headline": "The Moon leaves"}]
        assert ROOM.clean_tease({"family": "x", "premise": "Your pillow floats"}, pitch)["premise"] == "The Moon leaves tonight for good"      # without the ladder: a tease
        setting("LADDER_ON", "TRUE"); assert not ROOM.tease_on() and ROOM.tease_brief(spine) == "" and ROOM.clean_tease({"family": "x", "premise": "Your pillow floats"}, pitch) == {}
        assert ROOM.ensure_tease({"script": "[DIRECTOR] Last."}, spine["next_tease"], "EPT") == {"script": "[DIRECTOR] Last."}
        s, ev = CON.p_tease({"d": {}}); assert s == CON.NA and "under the ladder no next topic is promised" in ev
    with FMT.using("F1"):
        setting("LADDER_ON", "FALSE"); assert not ROOM.tease_on()                                                     # F1 ends on its question
        setting("ENDINGS_ON", "FALSE"); assert ROOM.tease_on()                                                        # switched off: the cell alone, as before
    setting("ENDINGS_ON", "TRUE"); setting("NEXT_PREMISE", json.dumps({"premise": "What if the Moon left?", "headline": "The Moon leaves"}))
    with FMT.using("F1"):
        t = ROOM.teased_pitch({"banned": [], "recent": []}, []); assert t and t["premise"] == "What if the Moon left?"   # what the video BEFORE promised is still honoured

def test_the_writer_gets_the_asks_of_its_format_and_a_trial_byte_for_byte(endings, setting):
    old = P.WRITER.replace("@@ASKS@@", P.ASKS_ALL); assert "AUDIENCE ASKS (like, subscribe, share): write exactly three" in old
    with FMT.using("F2"): assert P.fill(P.WRITER, asks=FMT.asks_brief()) == P.fill(old)                             # the trial: the original words byte for byte
    with FMT.using("F1"):
        f1 = P.fill(P.WRITER, asks=FMT.asks_brief()); assert FMT.ONE_ASK in f1 and "AUDIENCE ASKS" not in f1
    with FMT.using("F3"):
        f3 = P.fill(P.WRITER, asks=FMT.asks_brief()); assert FMT.NO_ASK in f3 and "AUDIENCE ASKS" not in f3
    setting("ENDINGS_ON", "FALSE")
    with FMT.using("F1"): assert P.fill(P.WRITER, asks=FMT.asks_brief()) == P.fill(old)
    assert P.fill(P.WRITER, words=10) == P.fill(old, words=10)                                                         # a caller that passes no asks gets the original
    src = open(os.path.join(ROOT, "whatifs", "room.py"), encoding="utf-8").read(); assert "budget=budget_brief(d), asks=FMT.asks_brief())" in src

def test_the_rewrite_orders_engage_and_the_format_block_say_the_formats_asks_and_a_trials_text_is_byte_for_byte(endings, setting):
    setting("ENGAGE_RULES_ON", "TRUE"); setting("EMOTION_BEAT_ON", "TRUE")
    with FMT.using("F2"):
        assert ROOM._keep_asks(P.HUMANIZE) == P.HUMANIZE and ROOM._keep_asks(P.FACTFIX) == P.FACTFIX and ROOM._asks_words() == "the three audience asks"
        trial_eg = EG.brief("EPG"); trial_fe = FE.instructions("director")
    setting("ENDINGS_ON", "FALSE")
    with FMT.using("F2"): assert EG.brief("EPG") == trial_eg and FE.instructions("director") == trial_fe              # the trial: byte for byte with the switch off
    with FMT.using("F1"): off_eg, off_fe = EG.brief("EPG"), FE.instructions("writer")
    setting("ENDINGS_ON", "TRUE")
    with FMT.using("F1"):
        assert "Keep the one subscribe ask in place" in ROOM._keep_asks(P.HUMANIZE) and "the one subscribe ask; keep" in ROOM._keep_asks(P.FACTFIX)
        eg = EG.brief("EPG"); assert "AUDIENCE PROMPTS" not in eg and "in the last third, before the ending" in eg and "verdict" not in eg
        fe = FE.instructions("writer"); assert FE.ASKS_ONE in fe and "\nShorts:" not in fe and "end as this format ends, with honest uncertainty" in fe and "Audience asks: exactly three" not in fe
        assert "AUDIENCE PROMPTS" in off_eg and "Audience asks: exactly three" in off_fe                                 # F1 with the switch off: as before
    with FMT.using("F3"):
        assert "Keep no audience ask (there is none: add none) in place" in ROOM._keep_asks(P.HUMANIZE)
        assert EG.brief("EPG") == "" and FE.ASKS_NONE in FE.instructions("critic")                                       # F3: no prompts, no emotion beat

def test_the_ask_chip_shows_only_the_formats_kinds(endings, setting):
    units = [{"text": "Nothing like this has ever happened to you.", "start": 0, "end": 2}, {"text": "So tap like.", "start": 3, "end": 4},
             {"text": "Please subscribe.", "start": 5, "end": 6}]
    with FMT.using("F1"): assert [k for _, _, k in OV.CtaChip(units, 640, 360, 25).spans] == ["subscribe"]
    with FMT.using("F2"): assert [k for _, _, k in OV.CtaChip(units, 640, 360, 25).spans] == ["like", "subscribe"]
    setting("ENDINGS_ON", "FALSE")
    with FMT.using("F1"): assert [k for _, _, k in OV.CtaChip(units, 640, 360, 25).spans] == ["like", "like", "subscribe"]      # as before: 'nothing like this' too

def test_the_one_fix_carries_the_ending_and_the_offline_f1_writer_ends_on_its_question(endings, monkeypatch, setting):
    asked = []
    monkeypatch.setattr("whatifs.models.ask", lambda *a, **k: asked.append(a[2]) or {"script": J(GOOD1 + ["[DIRECTOR] Would you keep it?"])})
    with FMT.using("F1"):
        iss = FMT.ending_issues(J(GOOD1 + ["[DIRECTOR] Subscribe for more."]))
        assert len(iss) == 1 and iss[0].startswith("THE ENDING: ") and "the question to the viewer - would you keep it?" in iss[0]
        sc, got = EN.fix_all({"script": J(GOOD1 + ["[DIRECTOR] Subscribe for more."])}, "brief", {}, "EPEF", "long"); assert iss[0] in got and "ENDING FIX" in asked[0]
        last = json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"].split("\n")[-1]; assert last == "[DIRECTOR] [close] So... would you keep it?"
        assert "END ON THE QUESTION" in FMT.block("writer")
    with FMT.using("F2"): assert FMT.ending_issues(J(GOOD1 + ["[DIRECTOR] Subscribe for more."])) == [] and "would you keep it" not in json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"]
    setting("ENDINGS_ON", "FALSE")
    with FMT.using("F1"): assert FMT.ending_issues(J(GOOD1 + ["[DIRECTOR] Subscribe for more."])) == [] and "would you keep it" not in json.loads(FK.fake_reply("writer", "Write the narration. ~300 words"))["script"]

def test_the_ending_is_wired_owner_lever_classified_and_f3_has_no_emotion_beat(endings, setting):
    assert REG.CHECK_OWNER["format_ending"] == "D4" and "format_ending" not in RND.ORG_CHECKS and "format_ending" in RND.metrics()
    lv = LV.LEVERS["ENDING_FREE_S"]; assert REG.may_change("D13", "ENDING_FREE_S") and (lv["lo"], lv["hi"], lv["step"], lv["owner"], lv["checks"]) == (20, 90, 10, "down", ("format_ending",))
    assert [FMT.ending(k) for k in ("F1", "F2", "F3")] == ["question", "tease", "arrival"] and FMT.ending("") == "tease"
    assert [FMT.asks(k) for k in ("F1", "F2", "F3")] == [("subscribe",), ("like", "subscribe", "share"), ()] and FMT.asks("") == FMT.ALL_ASKS
    setting("ENDINGS_ON", "FALSE"); assert FMT.asks("F3") == FMT.ALL_ASKS
    src = open(os.path.join(ROOT, "whatifs", "room.py"), encoding="utf-8").read()
    assert 'if S("EMOTION_BEAT_ON", bool) and not (S("ENDINGS_ON", bool) and FMT.rule("emotion_beat") == "never"):' in src and FMT.rule("emotion_beat", "F3") == "never"
