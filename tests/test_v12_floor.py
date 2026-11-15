"""v12 V1c - the floor, his verdict and the maker's line. STEP 0b (the memo's 3.5 with 3.11's F1, the audit of V2b): nobody of the trial's cast is cut to
where a format's row says nobody is on screen, and the three animated scenes of such a film are the viewer's own place - asked from the shot's own words, in
the film's look, with nobody in the picture, on the first purchase and on both roads of the paid repair; the trial keeps its staged scenes byte for byte.
Every rule is proven both ways, one fault at a time."""
import hashlib, json, os, re
import pytest
from whatifs import core, contract as CON, formats as FMT, anim as AN, path as PATH, shotplan as SP, episode as EP, media as MD
from whatifs.core import S

TRIAL_WORDS = ("grimm", "vale", "rosa", "laboratory", "detective office", "courtroom")
BIBLE = {"beats": [{"n": 1, "visual_world": "your kitchen"}, {"n": 2, "visual_world": "your street"}, {"n": 3, "visual_world": "the town square"}]}

@pytest.fixture
def cast(setting):
    setting("CAST_BY_FORMAT_ON", "TRUE"); setting("CAMERA_PATH_ON", "TRUE")
    yield setting
    FMT.use("")

def _sheets(tmp_path, chars):
    for c in chars:
        f = str(tmp_path / f"{c}.png"); MD.fake_image(f, 320, 180, c)
        core.store().append("Character_Sheets", [{"ts": "t", "character": c, "expression": "neutral", "hash": c, "prompt": "", "file": f, "status": "LOCKED", "approved_at": "t"}])

def _units(n=12):
    return [{"i": k, "start": 5.0 * k, "end": 5.0 * k + 4.8, "text": f"Line {k}: you watch the kettle float above your counter.", "speaker": "DIRECTOR",
             "tag": "none", "beat": 1 + k // 4} for k in range(n)]

def _film(fmt, ep="EPV1C0B"):
    """The shot list of a film in format `fmt` as `produce` makes it before the gate: the marks first, the Animation Director's three scenes, the words last."""
    units = _units()
    shots = [{"type": "still", "prompt": f"your own hands near the floating kettle, look {k}", "motion": "", "pov": {"angle": "eye level"}} for k in range(len(units))]
    with FMT.using(fmt):
        shots, _ = PATH.mark(shots, units, 60.0, BIBLE, ep)
        idx = AN.apply(shots, units, {"kling": 3})
        shots = PATH.lay(shots)
    return shots, units, idx

def _dir(p): os.makedirs(str(p), exist_ok=True); return str(p)

def _n(name): return int(re.search(r"\d{3}", name).group(0))

def _record(monkeypatch, gemini_fails=False):
    """Recorders in place of every request that buys a picture or a clip (the picture model with references, the still, the clip): what each was HANDED."""
    rec = {"picture": {}, "refs": [], "clip": {}, "url": {}, "still": {}}
    def gem(prompt, refs, path, ep, aspect="16:9"):
        if gemini_fails: raise RuntimeError("the picture model is down")
        rec["picture"].setdefault(_n(os.path.basename(path)), []).append(prompt); MD.fake_image(path, 64, 36, "x"); return path
    def refs_(who, workdir, ep): rec["refs"].append(tuple(who)); return []
    def still(prompt, path, episode, seed=None, **k): rec["still"].setdefault(_n(os.path.basename(path)), []).append(prompt); MD.fake_image(path, 64, 36, "x"); return path, None
    def animate(url, img, prompt, path, episode, **k): i = _n(os.path.basename(path)); rec["clip"][i] = prompt; rec["url"][i] = url; return path
    monkeypatch.setattr(AN, "gemini_image", gem); monkeypatch.setattr(AN, "_refs", refs_); monkeypatch.setattr(MD, "still", still); monkeypatch.setattr(MD, "animate", animate)
    return rec

# ------------------------------------------------------------------ 0b-1. the row says who may be on screen (3.5)
def test_the_older_tests_run_with_the_cast_rule_off():
    from tests.conftest import OLD_VIEW
    assert OLD_VIEW["CAST_BY_FORMAT_ON"] == "FALSE" and core.DEFAULTS["CAST_BY_FORMAT_ON"][0] == "TRUE" and S("CAST_BY_FORMAT_ON", bool) is False

def test_the_row_decides_whether_the_trials_cast_is_cut_to(cast, tmp_path):
    assert (FMT.cast("F1"), FMT.cast("F2"), FMT.cast("F3"), FMT.cast("")) == (False, True, False, True)
    assert [FMT.FORMATS[k]["cast"] for k in ("F1", "F2", "F3")] == [False, True, False]
    _sheets(tmp_path, ("GRIMM", "VALE"))
    units = [{"i": 0, "start": 0, "end": 4, "text": "A long line about the pillows over the city tonight.", "speaker": "DIRECTOR", "tag": "none"},
             {"i": 1, "start": 4, "end": 5, "text": "Fine.", "speaker": "SKEPTIC", "tag": "none"}, {"i": 2, "start": 5, "end": 6, "text": "Right.", "speaker": "DIRECTOR", "tag": "none"}]
    mk = lambda: [{"type": "still", "prompt": u["text"]} for u in units]
    for fmt in ("F1", "F3"):
        with FMT.using(fmt): out, n = SP.reaction_shots(mk(), units)
        assert n == 0 and out == mk(), fmt                                                  # a short line is a picture line like any other: nobody is shown
    with FMT.using("F2"): out, n = SP.reaction_shots(mk(), units)
    assert n == 2 and [s["type"] for s in out] == ["still", "reaction", "reaction"]        # the trial cuts to its drawn cast as before
    cast("CAST_BY_FORMAT_ON", "FALSE")
    with FMT.using("F1"): out, n = SP.reaction_shots(mk(), units)
    assert n == 2                                                                           # the switch off: today's behaviour in every format

# ------------------------------------------------------------------ 0b-2. THE SCENES OF A FORMAT WHERE NOBODY IS ON SCREEN (3.11 F1)
@pytest.mark.parametrize("fmt", ["F1", "F3"])
def test_in_a_format_where_nobody_is_on_screen_the_three_scenes_are_the_viewers_own_place(cast, monkeypatch, tmp_path, fmt):
    shots, units, idx = _film(fmt); rec = _record(monkeypatch)
    assert len(idx) == 3 and all(shots[i]["anim"]["world"] == "place" and AN.place_scene(shots[i]) for i in idx)
    with FMT.using(fmt): EP._assets(shots, units, _dir(tmp_path / "a"), "EPV1C0B", budget=12)
    lock, sw = str(S("STYLE_LOCK") or "").strip(), AN.style_words()
    for i in idx:
        pic, clip = rec["picture"][i][-1], rec["clip"][i]
        assert pic == AN.picture_request(shots[i], shots[i]["anim"]["line"]) and clip == AN.clip_request(shots[i], units[i]["text"])
        assert PATH.sentence(shots[i]["path"]["place"]) in pic and "floating kettle" in pic and pic.endswith(AN.NOBODY) and pic.count(lock) == 1 and pic.count(sw) == 1
        assert clip.startswith(PATH.KLING_MOTION.strip().rstrip(".")) and "floating kettle" in clip and PATH.sentence(shots[i]["path"]["place"]) in clip
        assert not any(w in (pic + " " + clip).lower() for w in TRIAL_WORDS), (i, pic, clip)
        assert rec["url"][i] is None and shots[i]["anim"]["frame"] == "google"             # the file itself is animated; the word "google" is never an address
    assert rec["refs"] == []                                                                # no reference portrait is asked for a place scene

def test_the_trial_keeps_its_staged_scenes_byte_for_byte(cast, monkeypatch, tmp_path):
    shots, units, idx = _film("F2"); rec = _record(monkeypatch)
    assert [shots[i]["anim"]["world"] for i in idx] == ["case", "lab", "office"] and not any(AN.place_scene(shots[i]) for i in idx)
    with FMT.using("F2"): EP._assets(shots, units, _dir(tmp_path / "a"), "EPV1C0B2", budget=12)
    h = lambda xs: hashlib.sha256("\n".join(xs).encode("utf-8")).hexdigest()
    assert h([rec["picture"][i][-1] for i in idx]) == h([AN.frame_prompt(shots[i]["anim"]) for i in idx])      # what the code asked before V1c, byte for byte
    assert h([rec["clip"][i] for i in idx]) == h([AN.acting_prompt(shots[i]) for i in idx])
    assert sorted(rec["refs"]) == [(), ("GRIMM",), ("VALE",)]                               # the staged scenes ask for their character's portrait as before

def test_with_the_switch_off_every_format_is_as_before(cast, monkeypatch, tmp_path):
    cast("CAST_BY_FORMAT_ON", "FALSE")
    shots, units, idx = _film("F1"); rec = _record(monkeypatch)
    assert [shots[i]["anim"]["world"] for i in idx] == ["case", "lab", "office"] and all(PATH.SENTENCE not in shots[i]["prompt"] for i in idx)
    with FMT.using("F1"): EP._assets(shots, units, _dir(tmp_path / "a"), "EPV1C0B3", budget=12)
    assert [rec["picture"][i][-1] for i in idx] == [AN.frame_prompt(shots[i]["anim"]) for i in idx]
    assert [rec["clip"][i] for i in idx] == [AN.acting_prompt(shots[i]) for i in idx]

@pytest.mark.parametrize("style", ["toybox_noir", "illustrated"])
def test_a_place_scene_is_asked_in_the_films_look_on_both_roads_of_its_start_picture(cast, monkeypatch, tmp_path, style):
    """The review's change 1 and round 2's correction 3: the look words and the lock once each, on the picture model's road and on the fall-back's - and
    what `media.still` itself would send (its lines 108 to 113) and its directive's cut leave `NOBODY` whole."""
    from whatifs import atmosphere as AT
    cast("ART_STYLE", style)
    lock, sw = str(S("STYLE_LOCK") or "").strip(), AN.style_words()
    for fmt in ("F1", "F3"):
        shots, units, idx = _film(fmt); rec = _record(monkeypatch, gemini_fails=True)
        with FMT.using(fmt): EP._assets(shots, units, _dir(tmp_path / f"a{fmt}"), "EPV1C0B4", budget=12)
        for i in idx:
            text = AN.picture_request(shots[i], shots[i]["anim"]["line"])
            assert rec["still"][i] == [text] and shots[i]["anim"]["frame"] == "fallback-still"
            assert text.count(lock) == 1 and text.count(sw) == 1 and sw in text and lock in text
            sent = text
            if lock not in sent: sent = sent.rstrip(". ") + ". " + lock                      # media.still 109
            if sw not in sent: sent = sent.rstrip(". ") + ". " + sw                          # media.still 113
            assert sent == text and sent.count(lock) == 1 and sent.count(sw) == 1
            assert AN.NOBODY in AT.with_directive(text, S("IMAGE_PROMPT_MAX_CHARS", int) - (len(lock) + 2) - (len(sw) + 2))
    shot = dict(shots[idx[0]], prompt=shots[idx[0]]["prompt"] + ". " + lock)                  # a prompt that already holds the lock does not get it twice
    assert AN.picture_request(shot, "x").count(lock) == 1

def test_the_clip_request_of_a_place_scene_carries_the_paths_motion_once():
    m = PATH.KLING_MOTION
    base = {"type": "kling", "anim": {"slot": 1, "world": "place", "line": "x"}, "prompt": "your kitchen, the kettle floats", "motion": "slow drift"}
    assert AN.clip_request(dict(base, path={"act": 1}), "the line") == (m + "slow drift").strip().rstrip(".") + ". your kitchen, the kettle floats"
    assert AN.clip_request(dict(base, path={"act": 1}, motion=m + "slow drift"), "x").count(m.strip()) == 1                # held already: not again
    assert AN.clip_request(base, "x") == "slow drift. your kitchen, the kettle floats"                                     # no path mark: no path sentence
    assert AN.clip_request(dict(base, prompt=""), "the line itself") == "slow drift. the line itself"
    staged = {"type": "kling", "anim": {"slot": 1, "world": "lab", "line": "x"}, "prompt": "p", "motion": "m"}
    assert AN.clip_request(staged, "x") == AN.acting_prompt(staged) and AN.picture_request(staged, "x") == AN.frame_prompt(staged["anim"])

# ------------------------------------------------------------------ 0b-3. ONE RULE FOR THE FIRST PURCHASE AND THE REPAIR (3.11 F1 (d))
def _job(shots, units, out, files):
    j = EP.Job(ep="EPV1C0BR", out=out, files=files, shots=shots, units=units, vo=None, tl=None, rx=[], fps=30, srt="", overlay=None, rhythm={}, d={})
    j.render_all = lambda: None
    return j

@pytest.mark.parametrize("fmt", ["F1", "F3", "F2"])
def test_the_repair_asks_a_scene_with_the_texts_of_the_first_purchase_on_both_roads(cast, monkeypatch, tmp_path, fmt):
    shots, units, idx = _film(fmt); out = str(tmp_path / "r"); os.makedirs(out); i = idx[1]
    want_pic, want_clip = AN.picture_request(shots[i], shots[i]["anim"]["line"]), AN.clip_request(shots[i], units[i]["text"])
    pics = {k: MD.fake_image(os.path.join(out, f"img{k:03d}.jpg"), 64, 36, str(k)) for k in range(len(shots)) if k != i}
    # (1) the scene's start picture missing after the first purchase (and so its clip): road 1 makes the picture, the clip is made from it
    rec = _record(monkeypatch)
    files = {"img": dict(pics), "clips": {k: "c.mp4" for k in idx if k != i}, "anchors": sorted(set(pics) | {i}), "missing": [i], "urls": {}}
    with FMT.using(fmt): _job(shots, units, out, files).repair_assets({"kling_short"}, [], 999)
    assert rec["picture"][i] == [want_pic] and i not in rec["still"] and rec["clip"][i] == want_clip and rec["url"][i] is None
    assert shots[i]["anim"]["frame"] == "google" and files["img"][i].endswith(f"img{i:03d}.jpg")
    # (2) the scene flagged by the picture judge as an artifact, its clip there: both roads re-make the picture with the same text, the clip is re-made
    rec = _record(monkeypatch)
    files = {"img": {**pics, i: os.path.join(out, f"img{i:03d}.jpg")}, "clips": {k: "c.mp4" for k in idx}, "anchors": sorted(set(pics) | {i}), "missing": [], "urls": {}}
    with FMT.using(fmt): _job(shots, units, out, files).repair_assets({"vision_artifact"}, [i], 999)
    assert rec["picture"][i] and set(rec["picture"][i]) == {want_pic} and i not in rec["still"] and rec["clip"][i] == want_clip and rec["url"][i] is None
    assert shots[i]["anim"]["frame"] == "google"
    # a shot without `anim` keeps every one of today's expressions (a picture target re-made as a still accurate to its line)
    rec = _record(monkeypatch); j = idx[0] + 1
    files = {"img": {k: v for k, v in pics.items() if k != j}, "clips": {k: "c.mp4" for k in idx}, "anchors": sorted(set(pics)), "missing": [j], "urls": {}}
    with FMT.using(fmt): _job(shots, units, out, files).repair_assets(set(), [], 999)
    assert rec["still"][j] == [f"{shots[j].get('prompt')}. Clear, sharp, no text in the picture, accurate to this line: {units[j]['text'][:140]}"] and j not in rec["picture"]

# ------------------------------------------------------------------ 0b-4. THE PLACE SENTENCE AND THE TWO CHECKS' WORDS (3.11 F1 (e), (f); 3.5)
def test_lay_gives_a_place_scene_its_acts_place_and_rule_4_holds_one_without_it(cast):
    shots, units, idx = _film("F1"); i = idx[1]
    for k in idx: assert shots[k]["prompt"].startswith(PATH.sentence(shots[k]["path"]["place"])), k       # the words last: a place scene is a still of its act
    staged = dict(shots[i], anim={"slot": 1, "world": "lab", "line": "x"}, prompt="no place")
    prom = dict(shots[i], promise=True, prompt="the thumbnail's scene")
    assert PATH.lay([staged])[0]["prompt"] == "no place" and PATH.lay([prom])[0]["prompt"] == "the thumbnail's scene"      # a staged scene and a promise keep their exemption
    ctx_ = {"d": {"format": "F1", "stills": 99}, "units": units, "shots": shots, "plan": {}, "total": 60.0}
    assert CON.p_camera_path(ctx_)[0] == CON.PASS
    bad = [dict(x) for x in shots]; bad[i]["prompt"] = "your own hands near the floating kettle"
    s, ev = CON.p_camera_path(dict(ctx_, shots=bad)); assert s == CON.FAIL and f"shot {i} does not hold the place of act" in ev, ev
    ok_ = [dict(x) for x in shots]; ok_[i] = staged
    assert CON.p_camera_path(dict(ctx_, shots=ok_))[0] == CON.PASS                                      # a staged scene is not asked for the place sentence (a trial's world)

def _inside_line(ep, ev_camera):
    from tools import sweep as SW
    core.store().append("Episodes", [{"episode_id": ep, "draw_json": json.dumps({"format": "F1"})}])
    core.store().append("Feature_Ledger", [{"episode_id": ep, "feature": k, "status": "PASS", "evidence": e} for k, e in (
        ("viewer_inside", "9 of 10 sentences (90%) inside the scene (floor 50%)"), ("format_ending", "ends on its question: 'would you keep it?'; no ask"),
        ("camera_path", ev_camera), ("camera_shown", "x"))])
    return SW.inside_of(core, ep)

def test_camera_path_names_the_scenes_asked_in_their_acts_place_at_the_very_end(cast):
    shots, units, idx = _film("F1")
    ctx_ = {"d": {"format": "F1", "stills": 99}, "units": units, "shots": shots, "plan": {}, "total": 60.0}
    s, ev = CON.p_camera_path(ctx_)
    assert s == CON.PASS and ev.endswith("; every act opens on its own picture; 3 scene(s) asked in their act's place"), ev
    cast("CAST_BY_FORMAT_ON", "FALSE")
    shots0, units0, _ = _film("F1"); s0, ev0 = CON.p_camera_path(dict(ctx_, shots=shots0, units=units0))
    assert s0 == CON.PASS and ev0.endswith("; every act opens on its own picture")                       # no place scene: no clause
    assert _inside_line("EPV1C0BS1", ev) == _inside_line("EPV1C0BS2", ev0)                               # the sweep's line on every F1 and F3 id does not move

def test_check_living_characters_holds_the_cast_where_the_row_shows_nobody(cast, tmp_path):
    _sheets(tmp_path, ("GRIMM", "VALE"))
    f1 = {"format": "F1"}; react = [{"type": "still"}, {"type": "reaction", "speaker": "SKEPTIC"}]
    staged = [{"type": "kling", "anim": {"slot": 1, "world": "lab", "line": "x"}}]
    place = [{"type": "kling", "anim": {"slot": 1, "world": "place", "line": "x"}}, {"type": "still"}]
    assert CON.p_living({"d": f1, "shots": react, "absent": 0}) == (CON.FAIL, "a cutaway to SKEPTIC's character in format F1, where nobody is on screen")
    s, ev = CON.p_living({"d": {"format": "F3"}, "shots": [{"type": "still"}], "states": [(0.0, 2.0, "still", False, False), (2.0, 3.0, "reaction", False, False)], "absent": 0})
    assert s == CON.FAIL and ev.endswith("'s character in format F3, where nobody is on screen")         # what the render recorded is read too
    assert CON.p_living({"d": f1, "shots": staged, "absent": 0}) == (CON.FAIL, "a staged scene of the trial's cast (lab) in format F1, where nobody is on screen")
    assert CON.p_living({"d": f1, "shots": place, "absent": 0, "states": None}) == (CON.PASS,
           "nobody is on screen: no cutaway and no staged scene of a character was made (a character without approved art is absent, never a shape)")
    s, ev = CON.p_living({"d": {"format": "F2"}, "shots": react + staged, "absent": 0})
    assert s == CON.PASS and ev.startswith("1 reaction cutaways, each the approved character")              # the trial: as before
    cast("CAST_BY_FORMAT_ON", "FALSE")                                                                   # the switch off: what the check says today, word for word
    assert CON.p_living({"d": f1, "shots": place, "absent": 0}) == (CON.PASS, "nobody is on screen: no cutaway of a character was made (a character without approved art is absent, never a shape)")
    assert CON.p_living({"d": f1, "shots": react, "absent": 0})[0] == CON.PASS and CON.p_living({"d": f1, "shots": staged, "absent": 0})[0] == CON.PASS
