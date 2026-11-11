"""v12 V2c-a - the Short as a product (Shorts Studio, D14) and the viewer's seat for a Short (Audience, D13): Short formats as data, a hook judged on
the real voice, plain words, the shape, the loop closed by code, no two alike. Every rule is proven both ways: it passes when kept and fails when
broken; the real writers' call, the real voice job and the real production are run, so an unwired call is seen."""
import datetime as dt, json, os, subprocess
import pytest
from whatifs import core, contract as CON, formats as FMT, shorts2 as SH, fakes as FK, notify as NT, publish as PUB, media as MD
from whatifs.org import shortseat as SEAT, registry as REG, levers as LV, rnd as RND, runner as RUN, memos as MEM, cite as CITE
from tools import sweep as SW

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc)
MOON = "What if the Moon left tonight?"

def good(fmt="S1", premise=MOON, before=""):
    """The offline writer's own Short in a format (the second script of the format when `before` names an earlier Short of it)."""
    return json.loads(FK.fake_reply("short_script", f"PREMISE: {premise}\nSHORT FORMAT: {fmt}\n" + (f"EARLIER SHORTS (format: opener): {before}\n" if before else "")))

def tl(sc, pace=0.30, lead=0.35, gap=0.25):
    """A voice timeline the way the voice job makes it: one unit per sentence, `pace` seconds a word."""
    from whatifs.voice import parse_script
    units = []; t = lead
    for line in FMT.short_lines(sc):
        for u in parse_script(f"[DIRECTOR] {line}"):
            n = len(u.text.split()); units.append({"text": u.text, "start": round(t, 2), "end": round(t + n * pace, 2), "speaker": "DIRECTOR"}); t += n * pace + gap
    return {"units": units, "duration": round(t - gap + 0.6, 2)}

def gate(sc, fmt="S1", hook="you_pov", last=(), **over):
    t = tl(sc); pl = SEAT.shape(SH.plan(sc, t, fmt), sc, fmt)
    return {"ep": "SHT1", "short": dict({"script": sc, "format": fmt, "hook": hook, "units": t["units"], "plan": pl, "last": list(last)}, **over)}

def led(ctx):
    return {r["feature"]: (r["status"], r["evidence"]) for r in CON.run("short", ctx, ctx["ep"], write=False)["rows"]}

def with_line(sc, i, line):
    out = json.loads(json.dumps(sc)); out["beats"][i]["line"] = line; return out

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _bench(*premises):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "premise": p, "status": "READY", "combined": 9 - i} for i, p in enumerate(premises)])

def _writer(monkeypatch, first=None, fix=None):
    """Replace what the offline writer answers (first = every variant, fix = the one fix); returns the list of keys asked."""
    asked = []; real = FK.fake_reply
    def fr(key, prompt):
        asked.append(key)
        if key == "short_script" and first is not None: return json.dumps(first(prompt) if callable(first) else first)
        if key == "short_fix" and fix is not None: return json.dumps(fix(prompt) if callable(fix) else fix)
        return real(key, prompt)
    monkeypatch.setattr(FK, "fake_reply", fr); return asked

# ------------------------------------------------------------------ Short formats are data
def test_short_formats_are_rows_of_data_and_the_pick_keeps_the_shares(setting, monkeypatch):
    ids = {f[0] for f in CON.FEATURES}
    assert set(FMT.SHORTS) == {"S1", "S2", "S3"} and all(len(f["beats"]) == 4 and f["camera"] in ("cut", "one_shot") for f in FMT.SHORTS.values())
    assert not any(set(f) & ids for f in FMT.SHORTS.values()) and not any("devices" in f for f in FMT.SHORTS.values())     # a Short format can loosen no check
    assert "object_on_trial" not in FMT.SHORT_HOOKS and set(FMT.SHORT_HOOKS) <= set(__import__("whatifs.brain", fromlist=["x"]).HOOK_ARCHETYPES)
    assert FMT.short_shares() == {"S1": 40, "S2": 40, "S3": 20} and FMT.short_len("S1") == (20.0, 35.0) and FMT.short_len("S2") == (20.0, 45.0) and FMT.short_len("S3") == (20.0, 35.0)
    assert FMT.short_pick("SH1") == FMT.short_pick("SH1") and {FMT.short_pick(f"SH{i}") for i in range(40)} == {"S1", "S2", "S3"}        # the first Short of a Sheet: by its id
    hist = []
    for i in range(10): hist.insert(0, FMT.short_pick(f"SH{i}", hist))                 # newest first, as shorts2.history gives it
    assert (hist.count("S1"), hist.count("S2"), hist.count("S3")) == (4, 4, 2)          # 40 / 40 / 20 is 4, 4 and 2 of ten, not a coin
    setting("SHORT_SHARE_S3", "0"); assert "S3" not in {FMT.short_pick(f"SH{i}", ["S1", "S2"] * 5) for i in range(20)}; setting("SHORT_SHARE_S3", "20")
    setting("SHORT_FORMAT_FORCE", "S3"); assert FMT.short_pick("SH1", ["S3"] * 9) == "S3"
    monkeypatch.setenv("WI_SHORT_FORMAT", "S2"); assert FMT.short_pick("SH1") == "S2"; monkeypatch.delenv("WI_SHORT_FORMAT"); setting("SHORT_FORMAT_FORCE", "")
    b = FMT.short_brief("S2", "you_pov", ["your moon just", "the gravity is"])
    assert "at most 12 words" in b and "inside 3 seconds" in b and "WHAT WOULD YOU DO?" in b and "you_pov" in b and "'your moon just'" in b and "never an ask" in b
    setting("SHORT_HOOK_WORDS_MAX", "8"); assert "at most 8 words" in FMT.short_brief("S1")                # the brief carries the seat's own numbers
    with FMT.short_using("S3"):
        assert FMT.short_current() == "S3"
    assert FMT.short_current() == ""

def test_the_offline_writer_passes_its_own_seat_in_every_format():
    for fmt in FMT.SHORTS:
        for before in ("", f"{fmt}: something else here"):
            for prem in SW.SHORT_PREMISES + (MOON, "What if two million bees moved in?", "What if the sea froze?", "What if the sky fell?", "What if ice was hot?"):      # every premise the sweep uses, and short words
                sc = good(fmt, prem, before)
                assert SH.valid(sc) == [] and SEAT.script_issues(sc, fmt) == [], (fmt, before, prem, SEAT.script_issues(sc, fmt))
    assert FK._short_word("What if photosynthesis stopped at noon?") == "stopped" and FK._short_word("What if two million bees moved in?") == "bees"      # never an expert word, never a number word
    assert good("S1")["beats"][0]["line"] != good("S1", before="S1: your moon just")["beats"][0]["line"]                # a second Short of a format is another script

# ------------------------------------------------------------------ short_open: the first frame and the first three seconds
def test_the_hook_is_short_and_ends_inside_three_seconds_of_the_real_voice(setting):
    sc = good(); t = tl(sc); pl = SEAT.shape(SH.plan(sc, t, "S1"), sc, "S1")
    r = SEAT.open_report(sc, t["units"], pl); assert r["problems"] == [] and r["hook"] == "Your moon just changed its mind." and r["hook_words"] == 6 and r["hook_end_s"] <= 3.0
    long_ = with_line(sc, 0, "Your moon just changed its mind about staying anywhere near you or your little house tonight. You reach out.")
    assert any("the hook has 16 words (limit 12)" in p for p in SEAT.open_report(long_)["problems"])
    slow = tl(sc, pace=0.55); r = SEAT.open_report(sc, slow["units"], pl); assert any("the hook ends at 3.6 s of the voice (limit 3 s)" in p for p in r["problems"])
    setting("SHORT_HOOK_BY_S", "4"); assert SEAT.open_report(sc, slow["units"], pl)["problems"] == []; setting("SHORT_HOOK_BY_S", "3")
    setting("SHORT_HOOK_WORDS_MAX", "5"); assert any("limit 5" in p for p in SEAT.open_report(sc)["problems"]); setting("SHORT_HOOK_WORDS_MAX", "12")
    for hello in ("Hey guys, welcome back. Your moon is gone.", "In this video the moon leaves. You reach out.", "Welcome to Reality Engine. Your moon left."):
        assert any("greeting" in p for p in SEAT.open_report(with_line(sc, 0, hello))["problems"]), hello
    assert SEAT.open_report(with_line(sc, 0, "Today the moon lets go of you. You reach out."))["problems"] == []          # an ordinary opening is no greeting

def test_the_first_frame_is_the_moving_promise_picture_and_the_promise_is_readable(setting):
    sc = good(); t = tl(sc); pl = SEAT.shape(SH.plan(sc, t, "S1"), sc, "S1")
    def P(**ch): out = json.loads(json.dumps(pl)); out["shots"][0].update(ch.pop("shot0", {})); out.update(ch); return SEAT.open_report(sc, t["units"], out)["problems"]
    assert P() == []
    assert any("opens on nothing" in p for p in P(shot0={"start": 0.5})) and any("opens on a plate" in p for p in P(shot0={"type": "plate"}))
    assert any("not made from the promise picture" in p for p in P(shot0={"src": "chain"})) and any("no picture plan" in p for p in P(shots=[]))
    assert any("no promise text" in p for p in P(promise={"text": "", "at": 0})) and any("has 8 words (limit 6)" in p for p in P(promise={"text": "one two three four five six seven eight", "at": 0}))
    assert any("appears at 1.5 s" in p for p in P(promise={"text": "The moon let go", "at": 1.5}))
    setting("SHORT_PROMISE_TEXT_ON", "FALSE"); assert P(promise={"text": "", "at": 0}) == []          # switched off: no text is asked for

# ------------------------------------------------------------------ short_plain: one number at most, no expert word
def test_a_short_has_one_number_at_most_and_no_expert_word(setting):
    sc = good(); assert SEAT.plain_report(sc)["problems"] == [] and SEAT.plain_report(sc)["numbers"] == 0
    one = with_line(sc, 1, "By breakfast three cups have slid off the table, and the cat has stopped trusting you."); assert SEAT.plain_report(one)["problems"] == []
    two = with_line(one, 2, "By evening two million people walk beside their own echo, and nobody remembers who moved first.")
    assert SEAT.plain_report(two)["numbers"] == 2 and any("2 numbers heard (limit 1)" in p for p in SEAT.plain_report(two)["problems"])
    setting("SHORT_NUMBERS_MAX", "2"); assert SEAT.plain_report(two)["problems"] == []; setting("SHORT_NUMBERS_MAX", "1")
    hard = with_line(sc, 1, "By breakfast the photon flux in your kitchen has changed, and the cat has stopped trusting you.")
    r = SEAT.plain_report(hard); assert r["hard"] and any("expert word(s) a layman would not know (limit 0)" in p for p in r["problems"])
    setting("SHORT_EXPERT_MAX", "2"); assert SEAT.plain_report(hard)["problems"] == []; setting("SHORT_EXPERT_MAX", "0")
    plain = with_line(sc, 1, "By breakfast you observe the coastline in one precious session, and the cat has stopped trusting you.")      # the four ordinary words of the V1b sweep
    assert SEAT.plain_report(plain)["hard"] == []
    titled = dict(with_line(sc, 1, "By breakfast the photon in your kitchen is late too."), title="The Photon That Was Late")
    assert "photon" in SEAT.plain_report(titled)["hard"]                                    # a swiping viewer chose no title: nothing is exempt
    setting("LAYMAN_ON", "FALSE"); assert SEAT.plain_report(hard)["hard"] == []             # the layman measure switched off: expert words are not judged

# ------------------------------------------------------------------ short_shape: length, hand-back, no ask, every second animated, the loop, captions
def test_the_shape_of_a_short_length_hand_back_and_no_ask(setting):
    sc = good(); t = tl(sc); assert SEAT.shape_report(sc, "S1", t["units"])["problems"] == []
    fast = SEAT.shape_report(sc, "S1", tl(sc, pace=0.15)["units"]); slow = SEAT.shape_report(sc, "S1", tl(sc, pace=0.6)["units"])
    assert fast["seconds"] < 20 and any("s long (format S1: 20 to 35 s)" in p for p in fast["problems"])
    assert slow["seconds"] > 35 and any("s long (format S1: 20 to 35 s)" in p for p in slow["problems"])
    assert SEAT.shape_report(sc, "S2", tl(sc, pace=0.52)["units"])["problems"] == []                                    # 39 s is inside S2's band, not inside S1's
    setting("SHORT_MAX_S_S1", "45"); assert SEAT.shape_report(sc, "S1", tl(sc, pace=0.52)["units"])["problems"] == []; setting("SHORT_MAX_S_S1", "35")
    for short in ("sun", "sky", "sea", "ice"):                                                                        # a three-letter word is a picture too (a Short about the Sun was held at first)
        s3 = with_line(with_line(sc, 0, f"The {short} is yours now. One thought, and it obeys."), 3, f"So would you keep the {short}, or let go?")
        assert SEAT.shape_report(s3, "S1", t["units"])["handback"] == [short], short
    filler = with_line(with_line(sc, 0, "You are not the one who did it. It was all for her."), 3, "So who was it for, and why not you?")
    assert any("does not hand back" in p for p in SEAT.shape_report(filler, "S1", t["units"])["problems"])               # fillers alone hand nothing back
    lost = with_line(sc, 3, "So tonight, do you close the window or leave it open?")
    assert any("does not hand back to the first picture" in p for p in SEAT.shape_report(lost, "S1", t["units"])["problems"]) and SEAT.shape_report(sc, "S1", t["units"])["handback"]
    for ask in ("Subscribe for more.", "Follow us for part two.", "Like and share this.", "Comment below what you would do.", "The full video is on our channel.", "Link in bio."):
        assert any("an ask in a Short" in p for p in SEAT.shape_report(with_line(sc, 2, "By evening the street is quiet. " + ask), "S1", t["units"])["problems"]), ask
    for fine in ("You would like it here.", "You follow the light across the full moon.", "Nobody will comment on it.", "You share the room with it."):
        assert not any("an ask" in p for p in SEAT.shape_report(with_line(sc, 2, "By evening the street is quiet. " + fine), "S1", t["units"])["problems"]), fine

def test_the_plan_is_an_animated_clip_in_every_second_and_ends_on_the_first_clip():
    for fmt in FMT.SHORTS:
        sc = good(fmt); t = tl(sc); pl = SH.plan(sc, t, fmt); shots = pl["shots"]
        assert shots[0]["start"] == 0.0 and shots[0]["src"] == "picture" and shots[-1]["end"] == pl["seconds"] == t["duration"]
        assert all(abs(a["end"] - b["start"]) < 0.011 for a, b in zip(shots, shots[1:])) and all(s["type"] == "kling" for s in shots)
        assert all(0.5 < s["end"] - s["start"] <= SEAT.CLIP_S * SEAT.STRETCH_MAX + 0.01 for s in shots)
        assert shots[-1]["src"] == "loop" and shots[-1]["loop"] and shots[-1]["picture"] == shots[0]["picture"] and [s["src"] for s in shots].count("loop") == 1
        firsts = [s for i, s in enumerate(shots[:-1]) if i == 0 or s["beat"] != shots[i - 1]["beat"]]
        if FMT.SHORTS[fmt]["camera"] == "cut": assert all(s["src"] == "picture" for s in firsts) and len(firsts) == 3          # every beat opens on its own picture
        else: assert [s["src"] for s in shots[:-1]] == ["picture"] + ["chain"] * (len(shots) - 2)                               # one continuous shot
        assert SEAT.shape_report(sc, fmt, t["units"], SEAT.shape(pl, sc, fmt))["problems"] == []
    long_ = tl(good("S2"), pace=0.64); pl = SH.plan(good("S2"), long_, "S2")                                                     # a 44 s Short: longer beats need a second clip
    assert 40 < pl["seconds"] <= 45 and sum(1 for s in pl["shots"] if s["src"] == "chain") >= 3 and all(s["end"] - s["start"] <= 6.51 for s in pl["shots"])

def test_the_plan_is_judged_every_second_animated_no_stock_the_loop_captions():
    sc = good(); t = tl(sc); pl = SEAT.shape(SH.plan(sc, t, "S1"), sc, "S1")
    def P(f):
        out = json.loads(json.dumps(pl)); f(out); return SEAT.shape_report(sc, "S1", t["units"], out)["problems"]
    assert P(lambda o: None) == []
    assert any("stock footage at" in p for p in P(lambda o: o["shots"][1].update(type="stock")))
    assert any("a still at" in p and "is not animated" in p for p in P(lambda o: o["shots"][1].update(type="still")))
    assert any("nothing is on screen from" in p for p in P(lambda o: o["shots"][1].update(start=o["shots"][1]["start"] + 1.0)))
    assert any("one clip is asked to cover" in p for p in P(lambda o: (o["shots"][0].update(end=o["shots"][1]["end"]), o["shots"].pop(1))))
    assert any("the pictures end at" in p for p in P(lambda o: o["shots"][-1].update(end=o["shots"][-1]["end"] - 2.0)))
    assert any("does not loop" in p for p in P(lambda o: o["shots"][-1].update(loop=False))) and any("does not loop" in p for p in P(lambda o: o["shots"][-1].update(src="picture")))
    assert any("the captions are off" in p for p in P(lambda o: o["captions"].update(on=False)))
    assert any("under the platform's buttons" in p for p in P(lambda o: o["captions"].update(margin=0.1)))

def test_the_seat_repairs_the_plan_by_code_before_any_picture_is_paid(setting):
    sc = dict(good(), promise="one two three four five six seven eight nine"); t = tl(sc); raw = SH.plan(sc, t, "S1")
    bad = json.loads(json.dumps(raw)); bad["shots"][0].update(type="plate", start=0.5, src="chain"); bad["shots"][2]["type"] = "stock"
    bad["shots"][-1].update(src="picture", loop=False); bad["captions"] = {"on": False, "margin": 0.05}; bad["promise"]["at"] = 2.0
    assert len(SEAT.open_report(sc, t["units"], bad)["problems"]) >= 3 and len(SEAT.shape_report(sc, "S1", t["units"], bad)["problems"]) >= 3
    fixed = SEAT.shape(bad, sc, "S1")
    assert SEAT.open_report(sc, t["units"], fixed)["problems"] == [] and SEAT.shape_report(sc, "S1", t["units"], fixed)["problems"] == []
    assert len(fixed["seat"]) >= 7 and fixed["promise"] == {"text": "one two three four five six", "at": 0.0} and fixed["captions"] == {"on": True, "margin": SEAT.CAPTION_MIN}
    assert bad["shots"][0]["type"] == "plate"                                                           # the plan handed in is not changed
    again = SEAT.shape(fixed, sc, "S1"); assert again["seat"] == [] and again["shots"] == fixed["shots"]         # shaped twice: nothing more to repair
    assert SEAT.shape(SH.plan(dict(sc, promise=""), t, "S1"), dict(sc, promise=""), "S1")["promise"]["text"] == "The Second Your Moon Changed"      # none given: the title's first words
    m = SEAT.m_shape(fixed); assert m["loop"] == 1 and m["repaired"] >= 7 and m["paid_clips"] == m["shots"] - 1 and m["pictures"] >= 1
    setting("SHORT_PROMISE_TEXT_ON", "FALSE"); assert SEAT.shape(raw, sc, "S1")["promise"]["text"] == ""; setting("SHORT_PROMISE_TEXT_ON", "TRUE")
    setting("SHORT_SEAT_ON", "FALSE"); off = SEAT.shape(bad, sc, "S1"); assert off["shots"][0]["type"] == "plate" and "seat" not in off and SEAT.script_issues(sc, "S1") == []

# ------------------------------------------------------------------ short_kept: the format, and no two alike
def test_a_short_is_what_its_format_says():
    sc = good("S1"); assert FMT.short_kept_report(sc, "S1")["problems"] == []
    swapped = json.loads(json.dumps(sc)); swapped["beats"][1]["role"] = "question"; swapped["beats"][3]["role"] = "consequence"
    assert any("format S1 is picture, consequence, consequence, question" in p for p in FMT.short_kept_report(swapped, "S1")["problems"])
    assert any("the last line is not a question" in p for p in FMT.short_kept_report(with_line(sc, 3, "So tonight the moon reaches for you first."), "S1")["problems"])
    s2 = good("S2"); assert FMT.short_kept_report(s2, "S2")["problems"] == []
    assert any("choice between two things" in p for p in FMT.short_kept_report(with_line(s2, 3, "So would you keep the moon and the silence?"), "S2")["problems"])
    s3 = good("S3"); assert FMT.short_kept_report(s3, "S3")["problems"] == [] and not s3["beats"][3]["line"].endswith("?")          # S3 needs no question
    assert any("the beats are" in p for p in FMT.short_kept_report(s3, "S1")["problems"])                                          # the wrong format's beats
    trial = with_line(sc, 1, "Objection! Exhibit A shows the kitchen has stopped trusting you, says Dr. Grimm.")
    r = FMT.short_kept_report(trial, "S1"); assert {"objection", "exhibit a", "dr. grimm"} <= set(r["trial_words"]) and any("courtroom words in a Short" in p for p in r["problems"])
    assert any("another voice than the guide speaks: SKEPTIC" in p for p in FMT.short_kept_report(with_line(sc, 1, "[SKEPTIC] By breakfast nothing keeps time with you."), "S1")["problems"])
    assert FMT.short_kept_report(with_line(sc, 1, "By breakfast the verdict of trial and error is in: nothing keeps time."), "S1")["problems"] == []      # ordinary uses stay free

def test_no_two_shorts_in_ten_are_alike(setting):
    sc = good("S1"); mine = "\n".join(FMT.short_lines(sc)); other = "\n".join(FMT.short_lines(good("S1", before="S1: x")))
    assert FMT.likeness(mine, mine) == 1.0 and FMT.likeness(mine, other) < 0.1 and FMT.opener(mine) == "your moon just"
    twin = "\n".join(FMT.short_lines(good("S1", "What if gravity doubled?")))                               # the same script with another noun: a template
    assert FMT.likeness(mine, twin) >= 0.4
    last = lambda script, fmt="S2", hook="countdown", i="SH9": [{"id": i, "format": fmt, "hook": hook, "script": script}]
    assert FMT.short_kept_report(sc, "S1", "you_pov", last(other))["problems"] == []
    r = FMT.short_kept_report(sc, "S1", "you_pov", last(twin)); assert r["alike"] == ["SH9"] and any("it reads like Short SH9" in p for p in r["problems"])
    assert any("opens with the same three words as Short SH9 ('your moon just')" in p for p in FMT.short_kept_report(sc, "S1", "you_pov", last("Your moon just left. Nothing else is the same here at all."))["problems"])
    setting("SHORT_SIMILAR_MAX", "0.95"); assert FMT.short_kept_report(sc, "S1", "you_pov", last(twin))["problems"] == []; setting("SHORT_SIMILAR_MAX", "0.4")
    ten = [{"id": f"SH{i}", "format": "S3", "hook": "countdown", "script": other} for i in range(10)]
    assert FMT.short_kept_report(sc, "S1", "you_pov", ten + last(twin))["problems"] == []                   # the twin is the ELEVENTH back: outside the window of ten
    assert FMT.short_kept_report(sc, "S1", "you_pov", ten[:9] + last(twin))["problems"]                     # the tenth back: inside it
    two = [{"id": "SH8", "format": "S2", "hook": "countdown", "script": ""}, {"id": "SH7", "format": "S1", "hook": "you_pov", "script": ""}, {"id": "SH6", "format": "S1", "hook": "verdict_first", "script": ""}]
    assert any("was one of the last two Shorts: the pick must rotate" in p for p in FMT.short_kept_report(sc, "S1", "you_pov", two)["problems"])
    assert FMT.short_kept_report(sc, "S1", "verdict_first", two)["problems"] == []                           # the third back may return
    assert FMT.short_kept_issues(sc, "S1", two) == [] and FMT.short_kept_issues(sc, "S1", last(twin))        # the rotation is the pick's duty, never the writer's

def test_the_pick_rotates_format_and_hook_by_code(setting):
    hist = [{"id": "SH8", "format": "S1", "hook": "you_pov", "script": ""}, {"id": "SH7", "format": "S1", "hook": "verdict_first", "script": ""}]
    for on in ("TRUE", "FALSE"):
        setting("BRAIN_ON", on)
        for _ in range(12):
            c = SH.hook_for("S1", hist); assert c["level"] in ("impossible_number", "countdown"), c
            assert SH.hook_for("S2", hist)["level"] in FMT.SHORT_HOOKS
    setting("BRAIN_DEFAULT_HOOK", "object_on_trial"); setting("BRAIN_ON", "FALSE"); assert SH.hook_for("S1", [])["level"] == FMT.SHORT_HOOKS[0]      # the trial's own hook is never a Short's

# ------------------------------------------------------------------ D14 write: variants, the seat before the jury, ONE fix
def test_the_writers_get_one_fix_with_every_measured_problem_named(monkeypatch):
    flawed = with_line(with_line(good(), 0, "Your moon just changed its mind about staying anywhere near you or your little house tonight. You reach out."),
                       3, "So now, do you close the window? Subscribe for more.")
    asked = _writer(monkeypatch, first=flawed)
    prompts = []; real = FK.fake_reply
    monkeypatch.setattr(FK, "fake_reply", lambda key, prompt, _r=real: (prompts.append(prompt) if key == "short_fix" else None, _r(key, prompt))[1])
    sc = SH.write({"premise": MOON}, "S1", "you_pov", "SHT1", [])
    assert asked.count("short_script") == 3 and asked.count("short_fix") == 1 and sc["_write"] == {"variants": 3, "valid": 3, "clean": 0, "fixed": 1, "left": 0}
    assert SEAT.script_issues(sc, "S1") == [] and "THE HOOK: the hook has 16 words" in prompts[0] and "an ask in a Short: 'subscribe'" in prompts[0] and "does not hand back" in prompts[0]
    assert SH.m_write(sc)["fixed"] == 1 and SH.m_write(sc)["hook_words"] == 6

def test_a_clean_script_needs_no_fix_and_only_clean_scripts_reach_the_jury(monkeypatch):
    asked = _writer(monkeypatch); sc = SH.write({"premise": MOON}, "S1", "you_pov", "SHT1", [])
    assert asked.count("short_fix") == 0 and sc["_write"]["clean"] == 3 and sc["_write"]["fixed"] == 0
    clean = good(); flawed = with_line(clean, 2, "By evening the street is quiet. Subscribe for more.")
    def first(prompt): return clean if "Variant 2 of 3" in prompt else flawed
    asked = _writer(monkeypatch, first=first); sc = SH.write({"premise": MOON}, "S1", "you_pov", "SHT2", [])
    assert sc["_write"]["clean"] == 1 and sc["_write"]["fixed"] == 0 and "Subscribe" not in json.dumps(sc) and asked.count("short_fix") == 0
    _writer(monkeypatch, first={"title": "x", "beats": [{"line": "one"}]})
    with pytest.raises(RuntimeError, match="no Short script had the shape asked for"): SH.write({"premise": MOON}, "S1", "you_pov", "SHT3", [])

# ------------------------------------------------------------------ the short gate
def test_the_short_gate_judges_five_checks_before_any_picture(setting):
    stage = {f[0]: f[1] for f in CON.FEATURES}; mine = ("short_open", "short_plain", "short_shape", "short_kept", "short_contract")
    assert [k for k, v in stage.items() if v == "short"] == list(mine) and all(FMT.rule(c, "F1") == "must" and FMT.rule(c, "") == "must" for c in mine)
    g = led(gate(good())); assert [g[c][0] for c in mine] == ["PASS"] * 4 + [CON.NA], g                    # no department run in this unit test: the organisation's check steps aside
    assert "ends at" in g["short_open"][1] and "0 number(s) heard" in g["short_plain"][1] and "the last is the first clip returning" in g["short_shape"][1] and "format S1" in g["short_kept"][1]
    bad = with_line(with_line(good(), 1, "By breakfast two cups and three plates slide a quark away. Subscribe for more."), 3, "So tonight, do you sleep?")
    g = led(gate(bad)); assert g["short_plain"][0] == "FAIL" and g["short_shape"][0] == "FAIL" and g["short_open"][0] == "PASS" and g["short_kept"][0] == "PASS"
    g = led(gate(good(), fmt="S2")); assert g["short_kept"][0] == "FAIL" and "the beats are" in g["short_kept"][1]
    g = led(gate(good(), units=tl(good(), pace=0.55)["units"])); assert g["short_open"][0] == "FAIL" and "the hook ends at 3.6 s of the voice" in g["short_open"][1]      # judged on the REAL voice
    g = led(gate(good(), units=[])); assert [g[c][0] for c in mine[:4]] == ["FAIL"] * 4 and "without its real voice timeline" in g["short_open"][1]
    g = led({"ep": "SHT1"}); assert g["short_open"] == ("FAIL", "no Short script reached the short gate")
    setting("SHORT_SEAT_ON", "FALSE"); g = led(gate(bad)); assert [g[c][0] for c in mine[:4]] == [CON.NA] * 4; setting("SHORT_SEAT_ON", "TRUE")
    setting("CONTRACT_OFF", "short_plain"); assert "short_plain" not in led(gate(bad))

# ------------------------------------------------------------------ wiring, levers, the one-time move
def test_the_shorts_studio_is_wired_and_its_levers_are_ruled(setting):
    assert REG.DEPTS["D14"]["wraps"] == ("whatifs/shorts2.py",) and "whatifs/shorts2.py" not in REG.DEPTS["D9"]["wraps"] and "whatifs/org/shortseat.py" in REG.DEPTS["D13"]["wraps"]
    assert "D14" in REG.ENTRY and "D14" not in REG.PENDING and REG.EPISODE_RUNS["short"] == (("D14", "write"), ("D7", "short_voice"), ("D13", "short_seat")) and REG.GATE_RUNS["short"] == ("D8", "short_gate")
    assert not REG.entry_issues() and not REG.data_issues() and REG.inject("D14", "write") == "prompt" and REG.inject("D14", "make") == "brief"
    assert [REG.check_owner(c) for c in ("short_open", "short_plain", "short_shape", "short_kept", "short_contract")] == ["D13", "D13", "D13", "D14", "D8"]
    assert "short_contract" in RND.ORG_CHECKS and {"short_open", "short_plain", "short_shape", "short_kept"} <= set(RND.metrics()) and "short_contract" not in RND.metrics()
    for k in ("SHORT_SHARE_S1", "SHORT_SHARE_S2", "SHORT_SHARE_S3", "SHORT_MIN_S", "SHORT_MAX_S_S1", "SHORT_MAX_S_S2", "SHORT_MAX_S_S3"): assert REG.may_change("D14", k) and k in LV.LEVERS, k
    for k in ("SHORT_HOOK_WORDS_MAX", "SHORT_HOOK_BY_S", "SHORT_NUMBERS_MAX", "SHORT_EXPERT_MAX", "SHORT_PROMISE_WORDS_MAX"): assert REG.may_change("D13", k) and LV.LEVERS[k]["owner"] == "up", k
    assert LV.LEVERS["SHORT_MIN_S"]["owner"] == "down" and LV.LEVERS["SHORT_MAX_S_S2"]["checks"] == ("short_shape",) and LV.LEVERS["SHORT_HOOK_BY_S"]["checks"] == ("short_open",)
    rep = open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read(); assert "whatifs/org/shortseat.py" in rep and "whatifs/shorts2.py" in rep
    from whatifs import models as M
    assert M.route("short_writer") == M.route("writer")                                    # the Short is written by the model that writes the long script

def test_shorts_no_longer_wait_for_the_character_masters_moved_once(setting, monkeypatch):
    from whatifs import manage as MG
    now = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc); setting("PAUSED", "FALSE")
    monkeypatch.setattr(SH, "masters_ready", lambda: False); assert core.S("SHORTS_NEED_MASTERS", bool) is False and SH.due(now) is True       # a Short shows no character
    setting("SHORTS_NEED_MASTERS", "TRUE"); assert SH.due(now) is False                                                                         # the owner can still ask for the wait
    assert MG.v12v2c_upgrade(core.store()) == ["SHORTS_NEED_MASTERS"] and core.S("SHORTS_NEED_MASTERS", bool) is False and core.S("V12V2C_FLIPS_DONE")
    setting("SHORTS_NEED_MASTERS", "TRUE"); assert MG.v12v2c_upgrade(core.store()) == [] and core.S("SHORTS_NEED_MASTERS", bool) is True       # never twice: a value typed later stays

# ------------------------------------------------------------------ the REAL production
def _made(r):
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", r["path"]], capture_output=True, text=True).stdout)
    return {s["codec_type"] for s in o["streams"]}, float(o["format"]["duration"])

def test_the_real_production_makes_a_short_in_every_format(monkeypatch, setting):
    _quiet(monkeypatch); _bench(MOON, "What if gravity doubled for one hour?", "What if your shadow arrived one second late?")
    st = core.store(); calls = {"hero": 0, "other": 0, "still": 0}
    ra, rs = MD.animate, MD.still
    monkeypatch.setattr(MD, "animate", lambda *a, **k: (calls.__setitem__("hero" if k.get("hero") else "other", calls["hero" if k.get("hero") else "other"] + 1), ra(*a, **k))[1])
    monkeypatch.setattr(MD, "still", lambda *a, **k: (calls.__setitem__("still", calls["still"] + 1), rs(*a, **k))[1])
    sent = []; rsend = NT.send
    monkeypatch.setattr(NT, "send", lambda kind, *a, **k: (sent.append(kind), rsend(kind, *a, **k))[1])
    for i, fmt in enumerate(("S1", "S2", "S3")):
        setting("SHORT_FORMAT_FORCE", fmt); before = dict(calls)
        r = SH.run(force=True, now=T0 + dt.timedelta(minutes=i)); print(r.get("id"), r.get("why"))
        assert r["ok"] and r["kind"] == "short" and r["format"] == fmt and r["status"] == "AWAITING_APPROVAL" and r["file"].startswith("drive:"), r
        kinds, dur = _made(r); lo, hi = FMT.short_len(fmt)
        assert kinds >= {"video", "audio"} and lo <= dur <= hi and abs(dur - float(r["sec"])) < 0.2
        led_ = {x["feature"]: x for x in st.rows("Feature_Ledger") if x["episode_id"] == r["id"]}
        assert {k: v["status"] for k, v in led_.items()} == {c: "PASS" for c in ("short_open", "short_plain", "short_shape", "short_kept", "short_contract")}, led_
        assert all(v["stage"] == "short" for v in led_.values()) and "3 department run(s) complete" in led_["short_contract"]["evidence"]
        ses = [(s["dept"], s["trigger"], s["status"]) for s in st.rows("Sessions") if s["episode_id"] == r["id"]]
        assert ses == [("D14", "write", "ok"), ("D7", "short_voice", "ok"), ("D13", "short_seat", "ok"), ("D8", "short_gate", "ok"), ("D14", "make", "ok")], ses
        w = next(s for s in st.rows("Sessions") if s["episode_id"] == r["id"] and s["trigger"] == "write")
        act = CITE._receipt(w, "ACT"); load = CITE._receipt(w, "LOAD")
        assert w["inject"] == "prompt" and "short_writer" in act["injected_tasks"] and load["items"] >= 5          # the Shorts Studio's knowledge was inside the writer's prompt
        row = next(x for x in st.rows("Specials") if x["id"] == r["id"])
        assert row["format"] == fmt and row["hook"] in FMT.SHORT_HOOKS and len(row["script"].split()) > 40 and float(row["sec"]) == float(r["sec"])
        f = next(x for x in st.rows("Video_Features") if x["video_key"] == r["id"]); assert f["format"] == "short" and f["lead"] == fmt and f["hook"] == row["hook"]
        mk = next(json.loads(t["measures"]) for t in st.rows("Takeaways") if t["episode_id"] == r["id"] and t["trigger"] == "make")
        paid = calls["hero"] - before["hero"]
        assert paid == mk["clips"] >= 2 and calls["other"] == 0 and calls["still"] - before["still"] == mk["pictures"] == (3 if FMT.SHORTS[fmt]["camera"] == "cut" else 1)
        assert SH.est_inr(fmt) >= paid * core.S("PRICE_KLING_USD", float) * core.S("USD_INR", float)          # the estimate said before anything was paid covers the clips really made
        assert mk["loop_diff"] <= SH.LOOP_MAX and SH._loop_diff(r["path"]) == mk["loop_diff"]                   # the last frame is the first frame again
    assert {x["stage"] for x in st.rows("Jury_Log")} == {"short"} and len({(x["format"], x["hook"]) for x in st.rows("Specials")}) == 3      # what the rotation guarantees: no pair of format and hook twice (the hook alone may repeat across formats - v12 V2c-b: the draw is seeded by the Short's id, so this no longer depends on chance)
    assert not [m for m in MEM.find(type="problem_memo")] and sent.count("special_review") == 3 and "contract_hold" not in sent
    assert [(x["format"], x["status"]) for x in st.rows("Specials")] == [("S1", "AWAITING_APPROVAL"), ("S2", "AWAITING_APPROVAL"), ("S3", "AWAITING_APPROVAL")]

def test_the_loop_is_closed_on_the_finished_file_and_an_open_loop_is_seen(monkeypatch, tmp_path):
    """The offline clips barely move, so they cannot tell a closed loop from an open one (a deliberate break showed it): here every clip scrolls."""
    import shutil
    n = [0]
    def moving(image_url, image_path, prompt, path, episode, hero=False, **k):
        n[0] += 1
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=360x640:rate=30:duration=5", "-vf", f"hue=h={47 * n[0]},scroll=vertical=0.004",
                        "-pix_fmt", "yuv420p", path], check=True)
        return path
    monkeypatch.setattr(MD, "animate", moving); out = {}; rev = []; real = SH._reverse
    for fmt in ("S1", "S3"):
        sc = good(fmt)
        for name, fn in (("closed", lambda src, o, sec: (rev.append((os.path.basename(src), round(sec, 2))), real(src, o, sec))[1]), ("open", lambda src, o, sec: shutil.copy(src, o))):
            wd = str(tmp_path / (fmt + name)); os.makedirs(wd); monkeypatch.setattr(SH, "_reverse", fn)
            v = SH.voice(sc, "SHL1", wd); pl = SEAT.shape(SH.plan(sc, v["timeline"], fmt), sc, fmt); m = SH.make(sc, v, pl, "SHL1", wd)
            out[(fmt, name)] = m; assert m["clips"] == len(pl["shots"]) - 1                                   # the loop shot is no paid clip
            if name == "closed": assert rev[-1] == ("c0.mp4", round(pl["shots"][-1]["end"] - pl["shots"][-1]["start"], 2))          # it IS the first clip, played backwards
    for fmt in ("S1", "S3"):
        assert out[(fmt, "closed")]["loop_diff"] <= SH.LOOP_MAX < out[(fmt, "open")]["loop_diff"], {k: v["loop_diff"] for k, v in out.items()}
        assert SH.make_lessons(out[(fmt, "closed")]) == [] and SH.make_lessons(out[(fmt, "open")])[0][0] == "loop_open"          # an open loop is reported to the organisation

def test_a_short_the_seat_refuses_is_held_not_made_and_the_owner_is_not_asked(monkeypatch, setting):
    _quiet(monkeypatch); _bench(MOON, "What if gravity doubled for one hour?"); st = core.store(); setting("SHORT_FORMAT_FORCE", "S1")
    flawed = with_line(with_line(good(), 1, "By breakfast two cups and three plates have slid off the table. Subscribe for more."), 3, "So tonight, do you sleep?")
    _writer(monkeypatch, first=flawed, fix=flawed)                                             # the writers' one fix does not repair it
    paid = []; monkeypatch.setattr(MD, "animate", lambda *a, **k: paid.append("clip")); monkeypatch.setattr(MD, "still", lambda *a, **k: paid.append("still"))
    sent = []; rsend = NT.send; monkeypatch.setattr(NT, "send", lambda kind, *a, **k: (sent.append(kind), rsend(kind, *a, **k))[1])
    r = SH.run(force=True, now=T0)
    assert r["ok"] is False and r["held"] and set(r["failed"]) == {"short_plain", "short_shape"} and r["premise"] == MOON and paid == [] and sent == []
    row = st.rows("Specials")[-1]; assert row["status"] == "HELD (short_plain, short_shape)" and row["format"] == "S1" and row["yt_id"] == ""
    ses = [(s["dept"], s["trigger"], s["status"]) for s in st.rows("Sessions")]
    assert ses == [("D14", "write", "ok"), ("D7", "short_voice", "ok"), ("D13", "short_seat", "ok"), ("D8", "short_gate", "ok")]          # D14 never made it
    memos = MEM.find(type="problem_memo", from_dept="D8"); assert sorted(m["body"]["check"] for m in memos) == ["short_plain", "short_shape"]
    assert all(m["to_depts"] == ["D13"] and m["episode_id"] == "" and m["status"] not in ("resolved", "rejected") for m in memos)
    assert SH.history() == [] and not st.rows("Video_Features")                                # a held Short is no part of what was made
    r2 = SH.run(force=True, now=T0 + dt.timedelta(minutes=1)); assert r2["held"] and r2["premise"] == MOON           # the topic is tried once more ...
    assert SH.pick_topic()["premise"] == "What if gravity doubled for one hour?"                                      # ... and then left (SHORT_HOLD_RETRIES 1)
    assert len(MEM.find(type="problem_memo", from_dept="D8")) == 2                                                    # one memo per class of failure, not per Short
    monkeypatch.undo(); _quiet(monkeypatch); setting("SHORT_FORMAT_FORCE", "S1")
    r3 = SH.run(force=True, now=T0 + dt.timedelta(minutes=2)); assert r3["ok"] and r3["premise"] == "What if gravity doubled for one hour?", r3
    assert all(m["status"] == "resolved" for m in MEM.find(type="problem_memo", from_dept="D8"))                     # the next Short that passes closes them
    assert sum(1 for x in st.rows("Specials") if x["status"].startswith("HELD")) == 2 and len(SH.history()) == 1

def test_two_shorts_in_a_row_differ_and_a_copy_is_held(monkeypatch, setting):
    _quiet(monkeypatch); _bench(MOON, "What if gravity doubled for one hour?", "What if your shadow arrived one second late?"); st = core.store(); setting("SHORT_FORMAT_FORCE", "S1")
    a = SH.run(force=True, now=T0); b = SH.run(force=True, now=T0 + dt.timedelta(minutes=1)); assert a["ok"] and b["ok"], (a, b)
    rows = st.rows("Specials"); assert rows[0]["hook"] != rows[1]["hook"] and FMT.likeness(rows[0]["script"], rows[1]["script"]) < 0.1 and FMT.opener(rows[0]["script"]) != FMT.opener(rows[1]["script"])
    copy = good("S1", "What if your shadow arrived one second late?")                           # the first Short's script with another noun
    _writer(monkeypatch, first=copy, fix=copy)
    c = SH.run(force=True, now=T0 + dt.timedelta(minutes=2)); assert c["held"] and c["failed"] == ["short_kept"], c
    assert "it reads like Short " + a["id"] in next(x["evidence"] for x in st.rows("Feature_Ledger") if x["episode_id"] == c["id"] and x["feature"] == "short_kept")
    assert MEM.find(type="problem_memo", from_dept="D8")[0]["to_depts"] == ["D14"]

def test_a_creative_run_that_goes_first_on_an_empty_sheet_gets_the_founding_knowledge(monkeypatch):
    from whatifs.org import palace as P
    _quiet(monkeypatch); _bench(MOON); st = core.store(); assert P.rows(st) == []
    r = SH.run(force=True, publish=False, now=T0); assert r["ok"], r
    w = next(s for s in st.rows("Sessions") if s["trigger"] == "write"); load = CITE._receipt(w, "LOAD")
    mine = {x["id"] for x in P.rows(st) if "D14" in x["departments"]}
    assert load["items"] >= 5 and len(mine) >= 5 and mine <= set(P.playbook("D14", "writing", record=False)["items"])          # not the cast alone
