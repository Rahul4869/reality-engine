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
    rec = {"picture": {}, "refs": [], "clip": {}, "url": {}, "still": {}, "seed": {}}
    def gem(prompt, refs, path, ep, aspect="16:9"):
        if gemini_fails: raise RuntimeError("the picture model is down")
        rec["picture"].setdefault(_n(os.path.basename(path)), []).append(prompt); MD.fake_image(path, 64, 36, "x"); return path
    def refs_(who, workdir, ep): rec["refs"].append(tuple(who)); return []
    def still(prompt, path, episode, seed=None, **k):
        rec["still"].setdefault(_n(os.path.basename(path)), []).append(prompt); rec["seed"].setdefault(_n(os.path.basename(path)), []).append(seed)      # (V1c finish, C5) and its seed
        MD.fake_image(path, 64, 36, "x"); return path, None
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
            mx = S("IMAGE_PROMPT_MAX_CHARS", int) - (len(lock) + 2) - (len(sw) + 2)          # audit F7: a text AT the directive's cut (room <= 40), where the guard can fail
            long_ = AN.picture_request(dict(shots[i], prompt=shots[i]["prompt"] + " " + "w" * (mx - 5 - len(text) - 1)), shots[i]["anim"]["line"])
            assert mx - 42 <= len(long_) <= mx and AN.NOBODY in AT.with_directive(long_, mx), len(long_)
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
    assert AN.clip_request({"anim": {"world": "place"}, "prompt": "your street", "motion": ""}, "x") == "your street"            # (V1c finish, C5) no motion: never ". "
    assert AN.clip_request({"anim": {"world": "place"}, "prompt": "your street", "motion": "drift."}, "x") == "drift. your street"

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
    # (V1c finish, C5) the picture model down: the fall-back still - the first purchase's TEXT on both roads of the repair, a fresh SEED at each repair
    ep_, slot = "EPV1C0BR", shots[i]["anim"]["slot"]
    rec = _record(monkeypatch, gemini_fails=True); AN.start_frame(shots[i], os.path.join(out, f"img{i:03d}.jpg"), ep_, out)
    assert rec["still"][i] == [want_pic] and rec["seed"][i] == [f"anim|{ep_}|{slot}"]                     # the first purchase
    for codes, flagged, missing in (({"kling_short"}, [], [i]), ({"vision_artifact"}, [i], [])):         # road 1, then both roads
        rec = _record(monkeypatch, gemini_fails=True)
        files = {"img": dict(pics) if missing else {**pics, i: os.path.join(out, f"img{i:03d}.jpg")}, "clips": {k: "c.mp4" for k in idx if k != i or not missing},
                 "anchors": sorted(set(pics) | {i}), "missing": missing, "urls": {}}
        job = _job(shots, units, out, files); n = job.fixn
        with FMT.using(fmt): job.repair_assets(codes, flagged, 999)
        assert set(rec["still"][i]) == {want_pic} and set(rec["seed"][i]) == {f"anim|{ep_}|{slot}|fix{n}"} != {f"anim|{ep_}|{slot}"}, rec["seed"]

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

# ================================================================== STEP 1 - THE JUDGED FLOOR (the memo's 3.1)
from whatifs.org import floor as FL
from whatifs import models as M, notify as NT, fakes as FK
OWN_IDS = ("EP209910010900", "EP209910080900", "EP209910150900", "EP209910220900",      # the whole productions of this file: ids no other test file uses (a test proves it)
           "EP209910290900", "EP209911050900",                                          # step 2: a film he gave a thumbs-up, and the film judged beside it
           "EP209911120900",                                                            # step 3: a long video about a promoted Short that ends on his line (and the same film on a Sheet without one)
           "EP209911190900",                                                            # the finish (C2): a film held by a measured check, then refused by the floor, then published anyway
           "EP209912170900", "EP209912240900",                                          # audit F10 (tests/test_v12_floor_report.py): a refused film in the report state, without and with his first-three review
           "EP209912280900",                                                            # (code review C18, 4) audit F6: a void floor under his first-three review - never the id of the void-session test
           "EP209912290900",                                                            # (code review C18, 3) tests/test_v12_floor_report.py: a refused film whose hold cell is armed between its check and its finish
           "EP209912300900",                                                            # (FIX-C18 round 3) tests/test_v12_floor_report.py: audit V1c F7 - a whole F1 production whose scenes are the viewer's own place
           "EP209912310915")                                                            # code review U1FIX-b (1): the THIRD case of tests/test_v12_floor_report.py's report state (review 3, TWO_SCREENS_ON FALSE) - one id a case

@pytest.fixture
def floor_on(setting):
    setting("VIEW_FLOOR_ON", "TRUE")
    core.set_setting("VIEW_FLOOR_FAIL_HOLDS", "TRUE")                      # audit F10: the older floor tests are the HOLD state's (the report state: tests/test_v12_floor_report.py)
    yield setting

def test_the_older_tests_run_with_the_floor_off():
    from tests.conftest import OLD_VIEW
    assert OLD_VIEW["VIEW_FLOOR_ON"] == "FALSE" and core.DEFAULTS["VIEW_FLOOR_ON"][0] == "TRUE" and FL.on() is False
    assert {k: core.DEFAULTS[k][0] for k in ("VIEW_FLOOR_WATCH_S", "VIEW_FLOOR_EST_INR", "VIEW_FLOOR_CAP_PER_VIDEO_INR", "VIEW_FLOOR_MAX_PER_VIDEO", "VIEW_FLOOR_CANARY",
            "VIEW_FLOOR_EYE_WAIT_H")} == {"VIEW_FLOOR_WATCH_S": "60", "VIEW_FLOOR_EST_INR": "40", "VIEW_FLOOR_CAP_PER_VIDEO_INR": "75", "VIEW_FLOOR_MAX_PER_VIDEO": "2",
                                          "VIEW_FLOOR_CANARY": "", "VIEW_FLOOR_EYE_WAIT_H": "20"}
    assert (FL.LOOKS, FL.EVERY_S, FL.THINK, FK.WATCH_CHANGE, FK.WATCH_MARGIN) == (2, 2, 8000, 0.5, 10)

_MEDIA = {}          # (V1c repair, open issue 224) the module's media, made ONCE A PROCESS: the proof's serial runner (`shim/minitest.py`) knows no fixture scope and no `tmp_path_factory`, so the folder is the run's own temp root (`tests/conftest.py` `_TMP`, removed at the end of a pytest session) and the files are kept here

@pytest.fixture(scope="module")
def media():
    """The stand-in for the rejected video (seed canary), its frozen twin, a flop (seed flop) and an offline film that moves (made once for the module)."""
    if _MEDIA: return _MEDIA
    import pathlib
    from tests.conftest import _TMP
    d = pathlib.Path(_TMP) / "floor_media"; d.mkdir(parents=True, exist_ok=True)
    can = FL.stand_in(str(d / "canary.mp4"), "canary"); tw = FL.twin(can, str(d / "canary_twin")); flop = FL.stand_in(str(d / "flop.mp4"), "flop")
    src = str(d / "film_src.mp4")
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=12", "-f", "lavfi", "-i", "sine=frequency=220:duration=60", "-t", "60",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", src], check=True, capture_output=True)
    film = FL.view(src, str(d / "film"), 60.0)                                              # (no Settings read here: a module fixture runs before the test's own store)
    _MEDIA.update({"canary": can, "twin": tw, "flop": flop, "film": film, "src": src, "dir": str(d)})
    return _MEDIA

def test_every_test_file_asks_only_for_what_the_proofs_serial_runner_gives():
    """(V1c repair, red round 1, open issue 224) The proof's serial suite runs every test file with a stand-in pytest (`shim/minitest.py`, outside the
    repo: law L10). It gives a test only `tmp_path`, `monkeypatch`, `capsys`, a parametrize name and the fixtures of the test files - no fixture scope,
    no `params`, no `request`, no `tmp_path_factory` - and of pytest itself only the names below. 29 tests of this file asked for more, passed under
    pytest here and on GitHub, and failed in the block before their first line: every test file is held to that list, so the next one fails HERE first."""
    import ast
    root = os.path.dirname(os.path.abspath(__file__))
    trees = {f: ast.parse(open(os.path.join(root, f), encoding="utf-8").read()) for f in sorted(os.listdir(root)) if f.endswith(".py")}
    def fixture_of(fn):
        for d in fn.decorator_list:
            t = d.func if isinstance(d, ast.Call) else d
            if isinstance(t, ast.Attribute) and t.attr == "fixture": return d
        return None
    known = {"tmp_path", "monkeypatch", "capsys"} | {n.name for t in trees.values() for n in t.body if isinstance(n, ast.FunctionDef) and fixture_of(n)}
    has = {"pytest": {"fixture", "mark", "raises", "approx", "skip", "fail", "importorskip", "MonkeyPatch"}, "capsys": {"readouterr"},
           "monkeypatch": {"setattr", "delattr", "setitem", "delitem", "setenv", "delenv", "chdir", "undo"}}
    bad = []
    for f, t in trees.items():
        for n in t.body:
            if not isinstance(n, ast.FunctionDef) or not (n.name.startswith("test_") or fixture_of(n)): continue
            given = set()
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "parametrize" and d.args:
                    a0 = d.args[0]
                    given |= {x.strip() for x in a0.value.split(",")} if isinstance(a0, ast.Constant) else {e.value for e in getattr(a0, "elts", []) if isinstance(e, ast.Constant)}
            bad += [f"{f}: {n.name} asks for `{a.arg}`" for a in n.args.args if a.arg not in known | given]
            fx = fixture_of(n)
            if isinstance(fx, ast.Call): bad += [f"{f}: fixture {n.name} sets `{k.arg}`" for k in fx.keywords if k.arg not in ("autouse", "scope")]
        for x in ast.walk(t):
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in has and x.attr not in has[x.value.id]:
                bad.append(f"{f}: {x.value.id}.{x.attr}")
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Attribute) and isinstance(x.value.value, ast.Name) and x.value.value.id == "pytest" \
                    and x.value.attr == "mark" and x.attr != "parametrize":
                bad.append(f"{f}: pytest.mark.{x.attr}")
    assert bad == [], bad

def _look(fam, order, items, answers, status="counted"):
    return {"family": fam, "order": order, "items": json.dumps(items), "answers": json.dumps(answers), "status": status, "downs": "[]"}

# the six worked cases of 3.1, by hand: items A = N, B = C, C = Z (pairs: 1 {C, Z}, 2 {N, C}); a cell = the wins of the first-named item
IT = {"A": "N", "B": "C", "C": "Z"}
def _fam(fam, c_over_z, n_over_c):
    out = []
    for o in range(2):
        a1 = "B" if o < c_over_z else "C"; a2 = "A" if o < n_over_c else "B"
        out.append(_look(fam, o, IT, {"1": [a1, "r1"], "2": [a2, "r2"]}))
    return out

@pytest.mark.parametrize("g_cz,g_nc,c_cz,c_nc,status,start", [
    (2, 2, 2, 2, "pass", "two first-time viewers (gemini, claude) named this video over the rejected one in 4 of 4 looks; the rejected video beat its frozen picture"),
    (2, 1, 2, 1, "fail", "ranked beside the rejected video: gemini named the new video in 1 of 2 looks"),
    (2, 2, 2, 0, "fail", "ranked beside the rejected video: claude named the new video in 0 of 2 looks"),
    (1, 2, 2, 2, "void", "void by its canary: gemini did not put the rejected video above its own frozen picture"),
    (2, 2, None, None, "void", "only 1 model family answered")])
def test_the_six_worked_cases_of_the_verdict(g_cz, g_nc, c_cz, c_nc, status, start):
    looks = _fam("gemini", g_cz, g_nc) + ([] if c_cz is None else _fam("claude", c_cz, c_nc))
    r = FL.verdict(looks, (), ())
    assert r["status"] == status and r["why"].startswith(start), r
    assert r["predict"] == {"pass": "up", "fail": "down", "void": ""}[status]
    if status == "pass": assert r["looks_won"] == 4

def test_a_jury_that_prefers_the_rejected_video_to_one_he_approved_is_void_whatever_it_said_of_the_film():
    it = {"A": "N", "B": "C", "C": "Z", "D": "R1"}           # pairs: 1 {C, Z}, 2 {N, C}, 3 {R1, C}, 4 {N, R1}
    def fam(f, r_over_c): return [_look(f, o, it, {"1": ["B", "x"], "2": ["A", "x"], "3": ["D" if o < r_over_c else "B", "x"], "4": ["A", "x"]}) for o in range(2)]
    r = FL.verdict(fam("gemini", 0) + fam("claude", 2), [None], ())
    assert r["status"] == "void" and r["why"] == "void by its canary: gemini preferred the rejected video to a video you approved"
    r = FL.verdict(fam("gemini", 2) + fam("claude", 2), [None], ())
    assert r["status"] == "pass" and r["why"].endswith(", and lost to 1 video(s) you approved") and r["vs_refs"] == 4 and r["predict"] == "up"

def test_a_missing_answer_counts_against_the_session_in_every_pair():
    empty = [_look(f, o, IT, {}) for f in ("gemini", "claude") for o in range(2)]
    assert FL.verdict(empty, (), ())["why"].startswith("void by its canary")                 # a judge that answers nothing is void by its canary, never valid
    junk = [_look(f, o, IT, {"1": ["Q", "x"], "2": ["A", "x"]}) for f in ("gemini", "claude") for o in range(2)]
    assert FL.verdict(junk, (), ())["status"] == "void"                                      # a letter that is not one of the pair's two is the worse item (Z)
    P = FL.pairs(1, 0); lab = {"N": "A", "C": "B", "Z": "C", "R1": "D"}
    assert FL._parse({}, P, lab) == {"1": ["C", "no answer"], "2": ["B", "no answer"], "3": ["B", "no answer"], "4": ["D", "no answer"]}

def test_a_film_cannot_void_its_own_session():
    """No ladder pair holds N: whatever the judges say of the new film, the session is valid when they kept the ladder."""
    for n_over_c in (0, 1, 2):
        r = FL.verdict(_fam("gemini", 2, n_over_c) + _fam("claude", 2, n_over_c), (), ())
        assert r["status"] in ("pass", "fail")
    assert all("N" not in p for p in FL.pairs(3, 2) if p[0] != "N")
    for k, j in ((1, 0), (2, 1), (3, 2)):                                                    # audit F8: k > 0 too - N's pairs are exactly N against C, each Ri, each Di
        assert sorted(p for p in FL.pairs(k, j) if "N" in p) == sorted([("N", "C")] + [("N", f"R{i}") for i in range(1, k + 1)] + [("N", f"D{i}") for i in range(1, j + 1)])

def test_a_pass_that_lost_to_his_approved_videos_predicts_nothing_and_is_never_void():
    """(audit F8) The new film LOSES to a reference: a pair {N, R1} can neither void nor fail a session, and a pass that lost to the references in most looks
    predicts nothing (`predict` "")."""
    it = {"A": "N", "B": "C", "C": "Z", "D": "R1"}           # pairs: 1 {C, Z}, 2 {N, C}, 3 {R1, C}, 4 {N, R1}
    def fam(f, n_over_r): return [_look(f, o, it, {"1": ["B", "x"], "2": ["A", "x"], "3": ["D", "x"], "4": ["A" if o < n_over_r else "D", "x"]}) for o in range(2)]
    for g, c, vr in ((0, 0, 0), (0, 1, 1), (1, 1, 2), (2, 2, 4)):
        r = FL.verdict(fam("gemini", g) + fam("claude", c), [None], ())
        assert r["status"] == "pass" and r["vs_refs"] == vr, r
        assert r["predict"] == ("up" if vr * 2 >= 4 else ""), r

def test_the_stand_in_its_twin_and_the_offline_judge_measured(media):
    can, tw, flop, film = media["canary"], media["twin"], media["flop"], media["film"]
    assert len(can["frames"]) == 30 and len(tw["frames"]) == 30 and len(film["frames"]) == 30
    assert abs(FK._changing(can["frames"]) - 100 * 14 / 29) < 0.05 and FK._changing(tw["frames"]) == 0.0 and abs(FK._changing(flop["frames"]) - 100 * 14 / 29) < 0.05
    assert FK._changing(film["frames"]) >= 100 * 14 / 29 + FK.WATCH_MARGIN
    assert os.path.getsize(can["clip"]) + os.path.getsize(tw["clip"]) + os.path.getsize(film["clip"]) + os.path.getsize(flop["clip"]) < 14 * 1024 * 1024      # a request's files under 14 MB (20 MB encoded)

def test_a_viewing_is_one_encode_and_its_strip_is_cut_from_its_own_clip(monkeypatch, media, tmp_path):
    seen = []; real = FL._ff
    monkeypatch.setattr(FL, "_ff", lambda args: (seen.append(list(args)), real(args))[1])
    v = FL.view(media["src"], str(tmp_path / "n"), 60)
    enc = [a for a in seen if "libx264" in a]; cut = [a for a in seen if any(str(x).startswith("fps=1/") for x in a)]
    assert len(enc) == 1 and len(cut) == 1 and cut[0][cut[0].index("-i") + 1] == v["clip"] and "-frames:v" in cut[0] and cut[0][cut[0].index("-frames:v") + 1] == "30"

def _session(media, sid, new=None, tight=None):
    return FL.session(sid, "sha", new or media["film"], media["canary"], media["twin"], [], [], "EPF1", view="v1")

def test_a_session_labels_carry_nothing_and_look_1_is_look_0_reversed(floor_on, monkeypatch, media):
    calls = []; real = M.ask_watch
    monkeypatch.setattr(M, "ask_watch", lambda role, system, prompt, views, **k: (calls.append((role, prompt, [v["label"] for v in views], [v["clip"] for v in views])), real(role, system, prompt, views, **k))[1])
    r = _session(media, "S-labels")
    assert r["status"] == "pass" and len(calls) == 4 and [c[0] for c in calls] == ["floor_gemini", "floor_gemini", "floor_claude", "floor_claude"]
    for a, b in (calls[0:2], calls[2:4]):
        assert b[2] == list(reversed(a[2])) and b[3] == list(reversed(a[3]))
        la = re.findall(r"PAIR (\d+): ([A-Z]) or ([A-Z])", a[1]); lb = re.findall(r"PAIR (\d+): ([A-Z]) or ([A-Z])", b[1])
        assert [(n, y, x) for n, x, y in la] == lb
    p = calls[0][1]
    assert not re.search(r"(?i)canary|twin|reject|new|flop|refer", p) and set(calls[0][2]) == {"A", "B", "C"}
    assert all(os.path.basename(x) in ("film.mp4", "canary.mp4", "canary_twin.mp4") for x in calls[0][3])      # file names are never sent: clips go as data
    rows = [x for x in core.store().rows("Floor_Log") if x["session_id"] == "S-labels"]
    assert len(rows) == 4 and all(x["status"] == "counted" and x["view"] == "v1" for x in rows) and FL.again(rows)["status"] == "pass"
    blind = lambda sid: sorted(["N", "C", "Z"], key=lambda k: hashlib.sha1(f"{sid}|{k}".encode()).hexdigest())      # (V1c finish, C12 - R7) the order is the session id's
    def look0(sid):
        it = json.loads(next(x for x in core.store().rows("Floor_Log") if x["session_id"] == sid and str(x["order"]) == "0")["items"]); return it
    it1 = look0("S-labels"); assert [it1[l] for l in sorted(it1)] == blind("S-labels"), it1
    _session(media, "S-labels-2"); it2 = look0("S-labels-2")
    assert blind("S-labels") != blind("S-labels-2") and it1 != it2 and [it2[l] for l in sorted(it2)] == blind("S-labels-2"), (it1, it2)

def test_a_look_by_another_provider_or_a_cheap_model_is_not_counted_and_the_later_family_is_not_asked(floor_on, monkeypatch, media):
    asked = []; real = M.ask_watch
    def watch(role, system, prompt, views, **k):
        asked.append(role); out = real(role, system, prompt, views, **k)
        if role == "floor_gemini": M._note_call("gemini", "gem_flash", "fake-flash")              # answered by a cheap model
        return out
    monkeypatch.setattr(M, "ask_watch", watch)
    r = _session(media, "S-cheap")
    assert r["status"] == "void" and r["why"] == "only 0 model families answered" and asked == ["floor_gemini"]
    assert any("not asked (the session was already void)" in n for n in r["notes"]) and r["view"] == ""
    rows = [x for x in core.store().rows("Floor_Log") if x["session_id"] == "S-cheap"]
    assert len(rows) == 1 and rows[0]["status"].startswith("not counted: answered by gemini:gem_flash") and rows[0]["view"] == ""

def test_floor_log_has_one_writer():
    hits = []
    for base in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), base)):
            for f in fn:
                if f.endswith(".py"):
                    t = open(os.path.join(dp, f), encoding="utf-8").read()
                    if re.search(r"\.(append|update|replace|update_where)\(\s*([\"']Floor_Log[\"']|(FL|FLR|FLOOR)\.LOG\b)", t): hits.append(f)
    assert hits == [], hits                                                                    # no other module writes the tab, by its name or by the floor's constant
    src = open(FL.__file__, encoding="utf-8").read(); assert src.count("store().append(LOG") == 1 and "assets" not in src

def test_every_verdict_from_stored_rows_goes_through_one_helper():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(root, base)):
            for f in fn:
                if f.endswith(".py") and f != "floor.py": assert "FLOOR.verdict(" not in open(os.path.join(dp, f), encoding="utf-8").read() and "FL.verdict(" not in open(os.path.join(dp, f), encoding="utf-8").read(), f
    src = open(FL.__file__, encoding="utf-8").read(); assert src.count(" verdict(rows") == 1           # only `again` calls it on stored rows

# ------------------------------------------------------------------ the doorway: models.ask_watch, judged by what was PAID (requests.post replaced)
class _R:
    def __init__(self, code, js=None, text=""): self.status_code, self._js, self.text = code, js or {}, text or json.dumps(js or {})
    def json(self): return self._js

def _gem(text, finish="STOP"): return _R(200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}], "usageMetadata": {"promptTokenCount": 30000, "candidatesTokenCount": 100, "thoughtsTokenCount": 3000}})
def _cla(text, stop="end_turn"): return _R(200, {"content": [{"type": "text", "text": text}], "stop_reason": stop, "usage": {"input_tokens": 17000, "output_tokens": 1500}})
GOOD = json.dumps({"pairs": {"1": ["A", "x"], "2": ["A", "y"]}})

@pytest.fixture
def real(monkeypatch, media):
    from whatifs import governor as G
    monkeypatch.setattr(M, "FAKE", False); monkeypatch.setattr(G, "monthly_cap_reached", lambda maintenance=False: False)
    monkeypatch.setattr(M, "model", lambda role: {"gem_pro": "g-pro-test", "sonnet": "c-son-test", "opus": "c-op-test", "gem_flash": "g-fl-test"}.get(role))
    sent = []
    def use(replies):
        it = iter(replies)
        def post(url, headers=None, json=None, timeout=None): sent.append((url, json)); return next(it)
        monkeypatch.setattr(M.requests, "post", post)
        return sent
    views = [{"label": "A", "clip": media["film"]["clip"], "frames": media["film"]["frames"][:2]}, {"label": "B", "clip": media["canary"]["clip"], "frames": media["canary"]["frames"][:2]}]
    return use, views

def test_the_doorway_waits_once_after_an_unpaid_failure_then_counts_the_look(real):
    use, views = real; sent = use([_R(503, text="busy"), _gem(GOOD)])
    out = M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0))
    assert out["pairs"]["1"][0] == "A" and "_tight" not in out and len(sent) == 2
    parts = sent[0][1]["contents"][0]["parts"]
    assert parts[0] == {"text": "OPENING A:"} and parts[1]["inlineData"]["mimeType"] == "video/mp4" and parts[-1]["text"] == "p"
    assert sent[0][1]["generationConfig"]["maxOutputTokens"] == 800 + 8000

def test_three_unpaid_failures_are_no_look(real):
    use, views = real; sent = use([_R(503), _R(503), _R(503)])
    with pytest.raises(RuntimeError): M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0))
    assert len(sent) == 3                                                                     # the strong Gemini role alone: no cheap model ever answers for it

def test_a_cut_look_is_asked_once_more_tighter_and_a_tight_cut_ends_the_call(real):
    use, views = real; sent = use([_gem("{", "MAX_TOKENS"), _gem(GOOD)])
    out = M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0))
    assert out["_tight"] is True and M.TIGHT_NOTE not in sent[0][1]["contents"][0]["parts"][-1]["text"] and M.TIGHT_NOTE in sent[1][1]["contents"][0]["parts"][-1]["text"]
    sent = use([_gem("{", "MAX_TOKENS"), _gem("{", "MAX_TOKENS"), _gem(GOOD)]); n0 = len(sent)
    with pytest.raises(RuntimeError): M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0))
    assert len(sent) - n0 == 2                                                                # cut twice: exactly two requests
    sent = use([_gem("{", "MAX_TOKENS"), _gem(GOOD)]); n0 = len(sent)
    with pytest.raises(RuntimeError): M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0), tight=True)
    assert len(sent) - n0 == 1 and M.TIGHT_NOTE in sent[-1][1]["contents"][0]["parts"][-1]["text"]      # tight from the first request: a cut ends the call

def test_a_declined_sonnet_look_goes_to_opus_once_and_never_back(real):
    use, views = real; sent = use([_cla("no", "refusal"), _cla(GOOD)])
    out = M.ask_watch("floor_claude", "s", "p", views, waits=(0, 0))
    assert out["pairs"]["2"][0] == "A" and [b["model"] for _u, b in sent] == ["c-son-test", "c-op-test"]
    c = sent[0][1]["messages"][-1]["content"]
    assert c[0]["text"].startswith("OPENING A (one picture every 2 seconds, sound off)") and c[1]["type"] == "image" and c[-1] == {"type": "text", "text": "p"}

def test_the_cost_row_of_a_look_carries_the_task_and_the_month_cap_closes_on_it(real, floor_on, tmp_path):
    from whatifs import governor as G
    use, views = real; use([_gem(GOOD)])
    M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0)); core.flush_costs()
    row = [r for r in core.store().rows("Cost_Log") if r.get("item") == "gemini_pro"][-1]
    assert row["role"] == "floor_gemini" and G.month_spend_of(["floor_gemini", "floor_claude"]) > 0
    core.set_setting("VIEW_FLOOR_CAP_PER_VIDEO_INR", "0")
    r = FL.plain(FL.run(None, "EPCAP", "x.mp4", "/nonexistent", (), ()))
    assert r["status"] == "void" and r["why"].startswith("the month's floor money is spent")
    spent = G.month_spend_of(["floor_gemini", "floor_claude"]); assert spent > 0                          # (V1c finish, C12 - R11) the cap closes ON the month's spend, not before it
    core.set_setting("VIEW_FLOOR_CAP_PER_VIDEO_INR", str((spent + 0.5) / G.max_long_videos()))
    r = FL.plain(FL.run(None, "EPCAP2", "x.mp4", str(tmp_path), (), ())); assert not r["why"].startswith("the month's floor money is spent"), r
    core.set_setting("VIEW_FLOOR_CAP_PER_VIDEO_INR", str(spent / G.max_long_videos()))
    r = FL.plain(FL.run(None, "EPCAP3", "x.mp4", str(tmp_path), (), ())); assert r["why"].startswith("the month's floor money is spent") and "Rs" in r["why"], r

# ------------------------------------------------------------------ the run: one verdict an episode; the kit; the check
def test_a_refusal_stands_across_renders_and_so_does_a_pass(floor_on, monkeypatch, media, tmp_path):
    asked = []; real = M.ask_watch
    monkeypatch.setattr(M, "ask_watch", lambda *a, **k: (asked.append(a[0]), real(*a, **k))[1])
    monkeypatch.setattr(FL, "view", lambda src, base, s: media["flop"])                      # the new film looks like the rejected one
    r1 = FL.plain(FL.run(None, "EPFAIL", media["src"], str(tmp_path), (), ()))
    assert r1["status"] == "fail" and len(asked) == 4 and r1["hold"]["family"] == "gemini" and r1["view"].endswith("_view.mp4")
    r2 = FL.plain(FL.run(None, "EPFAIL", media["src"], str(tmp_path), (), ()))                # the fix renders a NEW master: answered from the log
    assert r2["status"] == "fail" and len(asked) == 4 and r2["view"] == r1["view"] and r2["why"] == r1["why"]
    core.set_setting("CONTRACT_WAIVERS", json.dumps({"EPFAIL": ["viewer_floor"]}))           # his "Publish anyway": nothing is paid, the contract turns the FAIL into WAIVED
    led = CON.run("final", {"floor": FL.plain(FL.run(None, "EPFAIL", media["src"], str(tmp_path), (), ()))}, "EPFAIL", write=False)
    assert len(asked) == 4 and next(r for r in led["rows"] if r["feature"] == "viewer_floor")["status"] == CON.WAIVED
    monkeypatch.setattr(FL, "view", lambda src, base, s: media["film"])
    p1 = FL.plain(FL.run(None, "EPPASS", media["src"], str(tmp_path), (), ())); n = len(asked)
    p2 = FL.plain(FL.run(None, "EPPASS", media["src"], str(tmp_path), (), ()))                # the upload failed and the retry renders again: the pass stands
    assert p1["status"] == p2["status"] == "pass" and len(asked) == n and p2["view"] == p1["view"] != ""

def test_two_void_sessions_are_the_last(floor_on, monkeypatch, media, tmp_path):
    n = []; monkeypatch.setattr(M, "ask_watch", lambda *a, **k: (n.append(1), (_ for _ in ()).throw(RuntimeError("down")))[1])
    for _ in range(2): assert FL.plain(FL.run(None, "EPVOID", media["src"], str(tmp_path), (), ()))["status"] == "void"
    r = FL.plain(FL.run(None, "EPVOID", media["src"], str(tmp_path), (), ()))
    assert len(n) == 2 and r["status"] == "void" and r["why"].endswith("(not judged again: 2 sessions could not judge this video)")

def test_an_unreadable_log_fails_the_finish_and_never_makes_a_refused_film_void(floor_on, monkeypatch, media, tmp_path):
    st = core.store(); real = st.rows
    monkeypatch.setattr(st, "rows", lambda tab: (_ for _ in ()).throw(RuntimeError("the Sheet does not answer")) if tab == "Floor_Log" else real(tab))
    with pytest.raises(RuntimeError): FL.run(None, "EPLOG", media["src"], str(tmp_path), (), ())

def test_the_run_survives_an_ffmpeg_error_and_a_lost_upload(floor_on, monkeypatch, media, tmp_path):
    from whatifs import publish as PUB
    monkeypatch.setattr(PUB, "drive_upload", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("drive down")))
    monkeypatch.setattr(FL, "view", lambda src, base, s: media["film"])
    r = FL.plain(FL.run(None, "EPUP", media["src"], str(tmp_path), (), ()))
    assert r["status"] == "pass" and r["view"] == "" and r["view_url"] == ""                    # the session goes on; the minute could not be kept
    monkeypatch.setattr(FL, "view", lambda *a: (_ for _ in ()).throw(__import__("subprocess").CalledProcessError(1, "ffmpeg")))
    r = FL.plain(FL.run(None, "EPFF", media["src"], str(tmp_path), (), ()))
    assert r["status"] == "void" and r["why"] == "the floor could not run: CalledProcessError"

def test_a_void_session_writes_d13s_memo_and_the_next_valid_one_closes_it(floor_on, media, monkeypatch, tmp_path):
    """(V1c finish, C12 - R4) Under the organisation: a void session writes D13's own problem memo (floor|void); the next valid session closes it."""
    from whatifs.org import runner as ORG, memos as MEM
    floor_on("ORG_ON", "TRUE")
    live = lambda: [m for m in MEM.find(core.store(), type="problem_memo", from_dept="D13") if str(m.get("dedupe_key") or "") == "floor|void"]
    real_kit = FL.kit; monkeypatch.setattr(FL, "kit", lambda out: (None, "no canary kit"))
    ORG.work("D13", "floor", "EPVOID1", lambda b: FL.run(b, "EPVOID1", media["src"], str(tmp_path), (), ()), measure=FL.m_run)
    assert len(live()) == 1 and live()[0]["body"]["what_failed"] == "no canary kit", live()
    monkeypatch.setattr(FL, "kit", real_kit)
    r = FL.plain(ORG.work("D13", "floor", "EPVOID2", lambda b: FL.run(b, "EPVOID2", media["src"], str(tmp_path), (), ()), measure=FL.m_run))
    assert r["status"] == "pass" and live() == [], (r.get("status"), live())                                     # resolved, repair_verified

def test_no_kit_and_a_kit_whose_file_is_not_the_one_on_record(floor_on, monkeypatch, media, tmp_path):
    monkeypatch.setattr(FL, "FAKE", False)
    assert FL.kit(str(tmp_path)) == (None, "no canary kit")
    core.set_setting("VIEW_FLOOR_CANARY", "{not json"); assert FL.kit(str(tmp_path)) == (None, "no canary kit")
    sha = FL.make_kit(media["canary"]["clip"], yt="")                                      # filed offline: the local Drive stand-in
    k = json.loads(S("VIEW_FLOOR_CANARY")); assert k["sha"] == sha and k["file"] == "floor_canary.mp4" and set(k) == {"file", "sha", "yt", "made"}
    c, z = FL.kit(str(tmp_path / "k1"))
    from whatifs import release as REL
    assert REL.sha(c["clip"]) == sha and len(c["frames"]) == 30 and len(z["frames"]) == 30    # the stored clip IS the canary's viewing: never encoded again
    core.set_setting("VIEW_FLOOR_CANARY", json.dumps(dict(k, sha="0" * 64)))
    assert FL.kit(str(tmp_path / "k2")) == (None, "the canary file is not the one on record")
    r = FL.plain(FL.run(None, "EPKIT", media["src"], str(tmp_path), (), ()))
    assert r["status"] == "void" and r["why"] == "the canary file is not the one on record"

def test_the_kit_never_encodes_the_canary_again(floor_on, monkeypatch, media, tmp_path):
    FL.make_kit(media["canary"]["clip"]); called = []
    monkeypatch.setattr(FL, "FAKE", False); monkeypatch.setattr(FL, "view", lambda *a: called.append(a))
    c, _z = FL.kit(str(tmp_path)); assert c and called == []

def test_fetch_takes_a_drive_link_by_its_download_form_and_refuses_a_page(monkeypatch, media, tmp_path):
    got = []
    class _S:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def raise_for_status(self): pass
        def iter_content(self, n): yield self.body
    vid = open(media["canary"]["clip"], "rb").read()
    monkeypatch.setattr(FL.requests, "get", lambda url, **k: (got.append(url), _S(vid))[1])
    FL.fetch("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view?usp=sharing", str(tmp_path / "a.mp4"))
    assert got == ["https://drive.usercontent.google.com/download?id=1AbCdEfGhIjKlMnOpQrStUvWxYz012345&export=download&confirm=t"]
    monkeypatch.setattr(FL.requests, "get", lambda url, **k: _S(b"<html>sign in</html>"))
    with pytest.raises(RuntimeError) as e: FL.fetch("https://drive.google.com/open?id=1AbCdEfGhIjKlMnOpQrStUvWxYz012345", str(tmp_path / "b.mp4"))
    assert "did not give a video file" in str(e.value) and "Anyone with the link" in str(e.value) and "drive.google" not in str(e.value)
    FL.fetch(media["canary"]["clip"], str(tmp_path / "c.mp4")); assert os.path.getsize(str(tmp_path / "c.mp4")) == len(vid)
    monkeypatch.setattr(FL, "FETCH_MAX", 10)                                                      # (V1c finish, C4) the size limit is the module's own number
    class _S3(_S):
        def iter_content(self, n): yield from (b"x" * 8, b"x" * 8, b"x" * 8)
    monkeypatch.setattr(FL.requests, "get", lambda url, **k: _S3(b""))
    with pytest.raises(RuntimeError) as e: FL.fetch("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view", str(tmp_path / "d.mp4"))
    assert "larger than 2 GB" in str(e.value)

def test_fetch_names_no_address_when_the_link_is_not_https(tmp_path):
    """(V1c finish, C4) A link pasted as http:// or without its scheme is refused with words that name no address - never copied as a local path."""
    for src in ("http://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWx/view", "drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWx/view", "  "):
        with pytest.raises(RuntimeError) as e: FL.fetch(src, str(tmp_path / "x.mp4"))
        assert "1AbCdEf" not in str(e.value) and "drive.google" not in str(e.value) and "https://" in str(e.value), (src, e.value)

def test_the_floorkit_branch_files_the_kit_and_tells_him_once(floor_on, monkeypatch, media):
    import sys
    from whatifs import cli
    monkeypatch.setattr(sys, "argv", ["cli", "floorkit", media["canary"]["clip"], "abc123"])
    cli.main(); cli.main()
    k = json.loads(S("VIEW_FLOOR_CANARY")); assert k["yt"] == "abc123"
    n = [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"]
    assert len(n) == 1 and k["sha"][:8] in n[0]["text"] and "stop sharing" in n[0]["text"]

def test_the_floorkit_workflow_road_reads_the_event_file_and_logs_no_link(floor_on, monkeypatch, media, tmp_path, capsys):
    """(V1c finish, C4) The workflow's road: the link comes from the event file; a link that is not https:// fails with no address in the crash file
    (the public Actions log's last_error.txt), in no printed line and in no Run_Log row; the kit is unchanged."""
    import sys
    from whatifs import cli
    monkeypatch.chdir(tmp_path)                                                                   # the crash handler writes last_error.txt into the current folder - NEVER the repo's
    ev = tmp_path / "event.json"; ev.write_text(json.dumps({"inputs": {"link": media["film"]["clip"], "yt": ""}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(ev)); monkeypatch.setattr(sys, "argv", ["cli", "floorkit"])
    cli.main()
    k = json.loads(S("VIEW_FLOOR_CANARY")); assert k["yt"] == ""
    kits = [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"]          # audit F11 (J18 ANSWER 2): the workflow road also measures the judges - its own notice
    assert len([r for r in kits if str(r.get("text")).startswith("The first-time-viewer check has its reference")]) == 1
    assert len([r for r in kits if str(r.get("text")).startswith("The first-time viewers were measured")]) == 1 and len(kits) == 2, kits
    before = S("VIEW_FLOOR_CANARY"); capsys.readouterr()
    ev.write_text(json.dumps({"inputs": {"link": "http://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWx/view", "yt": ""}}), encoding="utf-8")
    with pytest.raises(RuntimeError): cli.main()
    printed = capsys.readouterr()
    assert "1AbCdEf" not in open(tmp_path / "last_error.txt", encoding="utf-8").read()
    assert "1AbCdEf" not in printed.out + printed.err and not [r for r in core.store().rows("Run_Log") if "1AbCdEf" in str(r.get("message"))]
    assert S("VIEW_FLOOR_CANARY") == before

def test_the_floorkit_success_road_prints_and_logs_no_link(floor_on, monkeypatch, media, tmp_path, capsys):
    """(audit F9) The SUCCESS road with his https link (the fetch stubbed with the film's bytes): the kit is made, and the link - his shared video's address -
    is in no printed line, no Run_Log row, no card and not in the kit's cell."""
    import sys
    from whatifs import cli
    monkeypatch.chdir(tmp_path)
    link = "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWx/view"; data = open(media["film"]["clip"], "rb").read()
    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def raise_for_status(self): pass
        def iter_content(self, n): yield data
    monkeypatch.setattr(FL.requests, "get", lambda url, **k: R())
    ev = tmp_path / "event.json"; ev.write_text(json.dumps({"inputs": {"link": link, "yt": ""}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(ev)); monkeypatch.setattr(sys, "argv", ["cli", "floorkit"])
    capsys.readouterr(); cli.main(); printed = capsys.readouterr()
    assert json.loads(S("VIEW_FLOOR_CANARY"))["sha"] and [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"]      # the success road ran
    for t in ("1AbCdEf", "drive.google.com/file"):
        assert t not in printed.out + printed.err and t not in str(S("VIEW_FLOOR_CANARY"))
        assert not [r for r in core.store().rows("Run_Log") if t in str(r.get("message"))] and not [r for r in core.store().rows("Owner_Actions") if t in str(r.get("text"))]

def test_check_viewer_floor_says_and_recomputes(floor_on, media):
    r = _session(media, "S-check")
    assert CON.p_viewer_floor({"floor": r}) == (CON.PASS, r["why"])
    bad = dict(r, status="fail", why="ranked beside the rejected video: nobody")
    assert CON.p_viewer_floor({"floor": bad}) == (CON.FAIL, "the stored verdict is not the code's verdict on its own looks")
    assert CON.p_viewer_floor({}) == (CON.NA, "not judged: the measured checks come first, and a film they hold is not paid a jury")
    assert CON.p_viewer_floor({"floor": {"status": "void", "why": "void by its canary: x"}}) == (CON.NA, "void by its canary: x")
    core.set_setting("VIEW_FLOOR_ON", "FALSE"); assert CON.p_viewer_floor({"floor": r})[1].startswith("the judged floor is switched off")

def test_the_check_recomputes_a_verdict_that_carries_no_looks(floor_on):
    """(V1c finish, C3) A pass or a fail with no looks is not the code's verdict: it never passes unverified; a void keeps its N/A."""
    bad = (CON.FAIL, "the stored verdict is not the code's verdict on its own looks")
    assert CON.p_viewer_floor({"floor": {"status": "pass", "why": "anything"}}) == bad and CON.p_viewer_floor({"floor": {"status": "fail", "why": "x"}}) == bad
    assert CON.p_viewer_floor({"floor": {"status": "void", "why": "no canary kit"}}) == (CON.NA, "no canary kit")

def test_with_the_organisation_off_the_result_is_the_same_dict(floor_on, media, tmp_path):
    from whatifs.org import runner as ORG
    core.set_setting("ORG_ON", "FALSE")
    x = ORG.work("D13", "floor", "EPOFF", lambda b: FL.run(b, "EPOFF", media["src"], str(tmp_path), (), ()))
    assert not isinstance(x, ORG.Out) and isinstance(x, dict) and FL.plain(x) is x and x["status"] in ("pass", "fail", "void")   # V4 step 0 (issue 200): the act's own dict

def test_the_line_the_estimate_and_the_routes(floor_on):
    from whatifs import costguard as CG
    L = {l["key"]: l for l in CG.lines("long")}; assert L["floor"]["inr"] == 40 and L["floor"]["calls"] == {"watch:floor_gemini": 2, "watch:floor_claude": 2}
    assert "floor" in {l["key"] for l in CG.lines("ladder")} and M.route("floor_gemini") == ("board_g", "judge") and M.route("floor_claude") == ("board_c", "judge")
    e1 = M.ai_estimate_inr(); core.set_setting("VIEW_FLOOR_ON", "FALSE")
    assert e1 - M.ai_estimate_inr() == 40 and "floor" not in {l["key"] for l in CG.lines("long")}
    assert FL.month_cap() == 75 * __import__("whatifs.governor", fromlist=["x"]).max_long_videos()

# ------------------------------------------------------------------ the owner: the hold card, his eye with a clock
def test_the_hold_card_stays_open_and_drop_kills_the_held_film(floor_on, monkeypatch):
    import datetime as dt
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    core.store().append("Episodes", [{"episode_id": "EPH", "status": "HOLD_QC"}])
    FL.hold_card("EPH", "The title", {"hold": {"family": "gemini", "reason": "the same grey cards"}, "view_url": FL.link("EPH_view.mp4")})
    row = next(r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_hold")
    assert row["text"].startswith("'The title' is HELD: two first-time viewers could not tell its first minute from the video you rejected - gemini: \"the same grey cards\". Watch that minute: https://drive.google.com/file/d/EPH_view.mp4/view.")
    assert row["expires_at"] == "" and [b[1] for b in json.loads(row["buttons"])] == ["CONTRACT WAIVE EPH viewer_floor", "FLOOR DROP EPH", "DISCUSS contract EPH"]
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(days=3))
    assert next(r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_hold")["status"] == "OPEN"      # three days later the card is still open
    assert NT.answer(row["id"], "FLOOR DROP EPH") == "EPH is dropped"
    assert next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPH")["kill"] == "KILL"
    FL.hold_card("EPH2", "T", {"hold": {"family": "claude", "reason": "r"}, "view_url": ""})
    assert "The minute could not be filed for you to watch." in next(r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == "EPH2")["text"]

def test_the_floors_hold_card_is_never_folded_into_an_older_card(floor_on):
    """(V1c finish, C1) A film held at the final check, fixed, then refused by the floor: the floor's card is its own message - never folded into the contract's."""
    CON.owner_card("EPFOLD", "final", [("aliveness", "planted")], "Nothing was uploaded.")
    res = {"status": "fail", "why": "ranked beside the rejected video: x", "hold": {"family": "gemini", "reason": "r"}, "view_url": ""}
    a = FL.hold_card("EPFOLD", "T", res)
    rows = [r for r in core.store().rows("Owner_Actions") if r["episode_id"] == "EPFOLD"]
    assert [r["kind"] for r in rows] == ["contract_hold", "floor_hold"] and rows[1]["id"] == a and rows[1]["status"] == "OPEN" and rows[1]["delivered_at"] \
        and rows[1]["expires_at"] == "" and rows[1]["dedupe_key"] == "floor|EPFOLD|hold"
    assert FL.hold_card("EPFOLD", "T", res) == a                                                  # a second hold of the SAME film folds into its own open card

def test_the_eye_hours_follow_the_slot(floor_on):
    import datetime as dt
    at = lambda h: (core.now_utc() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert FL.eye_hours(at(30)) == 20 and abs(FL.eye_hours(at(10)) - 8.5) < 0.05 and FL.eye_hours(at(2)) == 1.0

def test_a_film_the_floor_could_not_judge_is_approved_by_silence_after_its_hours_and_a_failed_default_is_tried_again(floor_on, monkeypatch):
    import datetime as dt
    from whatifs import publish as PUB, manage as MG
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    slot = (core.now_utc() + dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": "EPEYE", "status": "UPLOADED", "yt_id": "yt1", "slot_et": slot}])
    CON.await_approval("EPEYE", "yt1", slot, "summary", kind="floor_eye", default="goes public by itself", expires_h=FL.eye_hours(slot))
    st_ = lambda: next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPEYE")["status"]
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=19)); assert st_() == "AWAITING_APPROVAL"      # never before its hours
    calls = []; real = CON.approve
    monkeypatch.setattr(CON, "approve", lambda ep: (calls.append(ep), (_ for _ in ()).throw(RuntimeError("YouTube does not answer")) if len(calls) == 1 else real(ep))[1])
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=21))
    assert st_() == "AWAITING_APPROVAL" and any(str(m.get("dedupe_key")).startswith("floor|eye") for m in core.store().rows("Memos"))
    assert FL.eye_sweep() == 1 and st_() == "SCHEDULED" and len(calls) == 2                  # the next tick's sweep schedules it (level-triggered)
    assert not [m for m in __import__("whatifs.org.memos", fromlist=["x"]).find(core.store(), type="problem_memo", from_dept="D13") if str(m.get("dedupe_key")).startswith("floor|eye")]
    src = open(MG.__file__, encoding="utf-8").read(); i = src.index("NT.tick()")
    assert src.index("FLR.eye_sweep()") > i and src.index("FLR.eye_sweep()") < src.index("SH2.due()")      # right after NT.tick(), in a try of its own

def test_his_hold_before_the_hour_stands(floor_on, monkeypatch):
    import datetime as dt
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    slot = (core.now_utc() + dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": "EPHOLD", "status": "UPLOADED", "yt_id": "yt2", "slot_et": slot}])
    CON.await_approval("EPHOLD", "yt2", slot, "s", kind="floor_eye", default="goes public by itself", expires_h=20)
    row = next(r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == "EPHOLD")
    NT.answer(row["id"], "HOLDREVIEW EPHOLD"); NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=25)); FL.eye_sweep()
    assert next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPHOLD")["status"] == "HELD_BY_OWNER"

def test_a_film_that_left_the_review_by_another_road_is_never_approved_by_silence(floor_on, monkeypatch):
    """(V1c finish, C12 - R6) A floor_eye card still OPEN while its film left AWAITING_APPROVAL by another road: his silence approves nothing."""
    import datetime as dt
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    slot = (core.now_utc() + dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": "EPEYEX", "status": "UPLOADED", "yt_id": "yt3", "slot_et": slot}])
    CON.await_approval("EPEYEX", "yt3", slot, "summary", kind="floor_eye", default="goes public by itself", expires_h=FL.eye_hours(slot))
    assert next(r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == "EPEYEX")["status"] == "OPEN"
    core.store().update("Episodes", "episode_id", "EPEYEX", {"status": "HELD_BY_OWNER"})                    # by hand: the film left the review by another road
    calls = []; real = CON.approve; monkeypatch.setattr(CON, "approve", lambda ep: (calls.append(ep), real(ep))[1])
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=21)); FL.eye_sweep()
    assert next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPEYEX")["status"] == "HELD_BY_OWNER" and calls == [], calls

# ------------------------------------------------------------------ whole productions (ids no other test file uses)
def test_the_whole_productions_of_this_file_use_ids_no_other_test_file_uses():
    root = os.path.dirname(os.path.abspath(__file__)); here = os.path.basename(__file__)
    for f in os.listdir(root):
        if f.endswith(".py") and f != here:
            t = open(os.path.join(root, f), encoding="utf-8").read()
            for i in OWN_IDS: assert i not in t, (f, i)
    import ast, glob                                                                              # (code review C18, 4) ONE work folder a process (tests/conftest.py)
    users = {k: [] for k in range(len(OWN_IDS))}                                                  # and no cleaning (tests/test_v12_opening_e2e.py): each id is the
    def cases(fn):                                                                                # (RB-U1-a, code review U1FIX-b (1)) each parametrised CASE is a whole
        n = 1                                                                                     # production of its own: the product of the function's
        for d in fn.decorator_list:                                                               # pytest.mark.parametrize case counts
            if isinstance(d, ast.Call) and ast.unparse(d.func) == "pytest.mark.parametrize":
                assert len(d.args) >= 2 and isinstance(d.args[1], (ast.List, ast.Tuple)), (fn.name, "a parametrize whose cases this guard cannot count")
                n *= len(d.args[1].elts)
        return n
    owned = {}
    for f in sorted(glob.glob(os.path.join(root, "test_v12_floor*.py"))):                         # production of exactly ONE test function of the floor files
        for fn in ast.walk(ast.parse(open(f, encoding="utf-8").read())):
            if isinstance(fn, ast.FunctionDef) and fn.name.startswith("test_"):
                ks = {n.slice.value for n in ast.walk(fn) if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "OWN_IDS" and isinstance(n.slice, ast.Constant)}
                for k in ks:
                    users[k].append(f"{os.path.basename(f)}::{fn.name}")
                if ks: owned[f"{os.path.basename(f)}::{fn.name}"] = (len(ks), cases(fn))
    assert all(len(v) == 1 for v in users.values()), {k: v for k, v in users.items() if len(v) != 1}
    assert not {k: v for k, v in owned.items() if v[0] < v[1]}, ("a function naming OWN_IDS holds fewer distinct ids than its parametrised cases (ids, cases)", {k: v for k, v in owned.items() if v[0] < v[1]})

def _start_e2e(monkeypatch, setting):
    from tests import test_v12_inside as INS_T
    INS_T._start(monkeypatch, setting, "F1"); setting("VIEW_FLOOR_ON", "TRUE")
    core.set_setting("VIEW_FLOOR_FAIL_HOLDS", "TRUE")                      # audit F10: the older floor tests are the HOLD state's (the report state: tests/test_v12_floor_report.py)

def _led(ep): return {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep and x.get("stage") == "final"}

def test_a_whole_production_passes_the_floor_with_two_looks_of_each_judge(monkeypatch, setting):
    from tests import test_v12_opening_e2e as E2E
    from tests.paid_calls import watch, V12V1C_ADDED
    _start_e2e(monkeypatch, setting); c = watch(monkeypatch); ep = OWN_IDS[0]
    seen, run0 = [], FL.run                                       # audit F4: what the floor's own stage pays, counted on the whole production's counter
    def run_(*a, **k):
        b0 = dict(c); out = run0(*a, **k); seen.append({x: c[x] - b0.get(x, 0) for x in c if c[x] != b0.get(x, 0)}); return out
    monkeypatch.setattr(FL, "run", run_)
    r = EP.produce(E2E._slot(10), episode_id=ep); led = _led(ep)
    assert r.get("ok"), r
    assert led["viewer_floor"][0] == CON.PASS and led["viewer_floor"][1].startswith("two first-time viewers (gemini, claude) named this video over the rejected one in 4 of 4 looks")
    assert c["watch:floor_gemini"] == 2 and c["watch:floor_claude"] == 2
    assert seen == [V12V1C_ADDED], seen                                                       # audit F4: the four looks "and nothing else new" (tests/paid_calls.py, V12V1C_ADDED)
    rows = [x for x in core.store().rows("Floor_Log") if x["episode_id"] == ep]
    assert len(rows) == 4 and {x["view"] for x in rows} == {f"{ep}_view.mp4"}
    d = os.path.join(core.WORK, ep, "floor"); clips = [os.path.join(d, f) for f in ("new.mp4", "canary.mp4", "canary_twin.mp4")]      # (V1c finish, C10) the session's three clips
    assert all(os.path.exists(c) for c in clips) and sum(os.path.getsize(c) for c in clips) < 14 * 1024 ** 2, clips

def test_a_void_session_sends_the_film_to_his_eye_with_the_clock(monkeypatch, setting):
    import datetime as dt
    from tests import test_v12_opening_e2e as E2E
    _start_e2e(monkeypatch, setting); setting("ORG_ON", "FALSE"); ep = OWN_IDS[3]
    setting("VIEW_FLOOR_CANARY", json.dumps({"file": "missing.mp4", "sha": "0" * 64, "yt": "", "made": "2026-11-15"}))
    r = EP.produce(E2E._slot(30), episode_id=ep); led = _led(ep)
    assert r.get("ok") and led["viewer_floor"] == (CON.NA, "no canary kit")
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep); assert e["status"] == "AWAITING_APPROVAL"
    card = next(x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep and x.get("kind") == "floor_eye")
    assert "The first-time-viewer check could not judge this one (no canary kit)." in card["text"] and card["default_action"] == "goes public by itself"
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=21))
    assert next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)["status"] == "SCHEDULED"

def test_a_void_floor_on_one_of_his_first_videos_is_his_creative_review_not_the_eye(monkeypatch, setting):
    """(audit F6) A video under the creative review of his first videos gets the review's card, whatever the floor said: a void floor and a needed review
    together give `creative_review` and never `floor_eye` (the order of `if CON.review_needed` and the eye's `elif` in episode.py)."""
    from tests import test_v12_opening_e2e as E2E
    _start_e2e(monkeypatch, setting); setting("ORG_ON", "FALSE"); setting("CREATIVE_REVIEW_FIRST_N", "99"); ep = OWN_IDS[10]      # (code review C18, 4) an id of its own
    setting("VIEW_FLOOR_CANARY", json.dumps({"file": "missing.mp4", "sha": "0" * 64, "yt": "", "made": "2026-11-15"}))
    r = EP.produce(E2E._slot(30), episode_id=ep); led = _led(ep)
    assert r.get("ok") and led["viewer_floor"] == (CON.NA, "no canary kit")
    kinds = [x.get("kind") for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    assert "creative_review" in kinds and "floor_eye" not in kinds, kinds

# ================================================================== STEP 2. HIS VERDICT (3.2): one row a release, one tap, the label the floor is scored against
import datetime as _dt

def _ago(**k): return (core.now_utc() - _dt.timedelta(**k)).strftime("%Y-%m-%dT%H:%M:%SZ")

@pytest.fixture
def verdict_on(setting, monkeypatch):
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    setting("OWNER_VERDICT_ON", "TRUE"); setting("VIEW_FLOOR_ON", "TRUE"); yield setting

def _VER():
    from whatifs.org import verdicts as V
    return V

def _vrow(ref):
    return next((r for r in core.store().rows("Owner_Verdicts") if r.get("ref") == ref), None)

def _long(ep, status="LIVE", yt="ytL", title="The long one", draw=None):
    core.store().append("Episodes", [{"episode_id": ep, "status": status, "yt_id": yt, "title": title, "slot_et": _ago(days=400), "draw_json": json.dumps(draw or {})}])

def _short(sid, posted, state="POSTED", yt="ytS", title="The Short", topic="pillows"):
    core.store().append("Ladder", [{"id": sid, "topic": topic, "title": title, "yt_id": yt, "posted": posted, "state": state}])

def _judged(media, ep, new, sid, view=""):
    """A floor session of episode `ep` on the log (the offline judges): the film `new` against the stand-in and its twin."""
    return FL.session(sid, "sha", new, media["canary"], media["twin"], [], [], ep, view=view)

def test_the_older_tests_run_with_his_verdict_off():
    from tests.conftest import OLD_VIEW
    V = _VER()
    assert OLD_VIEW["OWNER_VERDICT_ON"] == "FALSE" and core.DEFAULTS["OWNER_VERDICT_ON"][0] == "TRUE" and V.on() is False
    assert {k: core.DEFAULTS[k][0] for k in ("OWNER_VERDICT_SINCE", "OWNER_VERDICT_ASK_MAX_PER_DAY", "OWNER_VERDICT_EXPIRES_H", "VIEW_FLOOR_REFS_MAX", "VIEW_FLOOR_DOWNS_MAX",
            "VIEW_FLOOR_SCORE_N", "VIEW_FLOOR_MISS_MAX")} == {"OWNER_VERDICT_SINCE": "", "OWNER_VERDICT_ASK_MAX_PER_DAY": "1", "OWNER_VERDICT_EXPIRES_H": "336",
                                                          "VIEW_FLOOR_REFS_MAX": "1", "VIEW_FLOOR_DOWNS_MAX": "0", "VIEW_FLOOR_SCORE_N": "5", "VIEW_FLOOR_MISS_MAX": "3"}
    assert V.UP == ("up", "good", "yes", "y", "+") and V.DOWN == ("down", "bad", "no", "n", "-", "not good") and V.TAB == "Owner_Verdicts"
    assert core.TABS["Owner_Verdicts"] == ["ref", "kind", "title", "url", "topic", "asked", "verdict", "text", "maker_line", "seen", "via", "floor", "agree", "action_id",
                                           "line_seen", "line_used", "told"]
    _long("EP209912010900"); V.sync(); V.record("EP209912010900", "down", "", "hold")      # the switch off (DESIGN QUESTION 9): nothing is asked, kept or used
    assert core.store().rows("Owner_Verdicts") == [] and not S("OWNER_VERDICT_SINCE") and V.references("x") == [] and V.downs("x") == []

def test_made_at_is_the_minute_in_the_id():
    V = _VER()
    assert V.made_at("EP209901021613") == _dt.datetime(2099, 1, 2, 16, 13, tzinfo=_dt.timezone.utc)
    assert abs((V.made_at("EPNODIGITS") - core.now_utc()).total_seconds()) < 5                 # an id without twelve digits counts as made now

def test_the_first_tick_sets_the_day_and_a_sheet_of_old_live_rows_is_never_asked_about(verdict_on):
    V = _VER()
    for k in range(5): _long(f"EP20260101{k:02d}00", title=f"old {k}")                      # the old code's videos (made on 1 Jan 2026)
    _short("SHOLD", _ago(days=30))
    V.sync(); assert str(S("OWNER_VERDICT_SINCE"))[:10] == core.now_utc().strftime("%Y-%m-%d")   # (1): the day is set and nothing else happens
    assert core.store().rows("Owner_Verdicts") == [] and not [a for a in core.store().rows("Owner_Actions") if a.get("kind") == "owner_verdict"]
    for k in range(5): core.store().update("Episodes", "episode_id", f"EP20260101{k:02d}00", {"slot_et": _ago(hours=-48)})   # audit F3: old rows RE-SLOTTED after the day
    V.sync(); assert core.store().rows("Owner_Verdicts") == []                                   # (2): nothing older than the day is ever asked about, re-slotted or not

def test_review_needed_counts_from_the_day_on_a_sheet_of_old_rows(verdict_on):
    V = _VER(); verdict_on("CREATIVE_REVIEW_FIRST_N", "3")
    for k in range(5): _long(f"EP20260101{k:02d}00", title=f"old {k}")
    for k in range(4): core.store().update("Episodes", "episode_id", f"EP20260101{k:02d}00", {"slot_et": _ago(hours=-48)})   # audit F3: FOUR old rows (N + 1) RE-SLOTTED after the day: still not counted - counted by slot_et they would end the review
    assert CON.review_needed("long") is False                                                    # the day is not set yet: as before (5 > 3)
    V.sync(); assert CON.review_needed("long") is True                                          # counted from the day: none of the old five
    _long("EP209912020900", status="SCHEDULED", yt="ytNEW"); assert CON.review_needed("long") is True      # the first video of the new code IS reviewed
    verdict_on("OWNER_VERDICT_ON", "FALSE"); assert CON.review_needed("long") is False

def test_one_ask_a_day_oldest_first_and_never_the_last_now_place(verdict_on):
    V = _VER(); verdict_on("OWNER_VERDICT_SINCE", _ago(days=3))
    _short("SHA", _ago(days=2), title="A pillow Short"); _short("SHMADE", _ago(days=1), state="MADE", title="never public")
    _long("EP209912030900", title="The long one", draw={"ladder": "SHA"})
    verdict_on("NOTIFY_NOW_MAX_PER_DAY", "9"); V.sync()                                         # the "act now" places are not the limit here: the day's ask count is
    rows = core.store().rows("Owner_Verdicts"); assert [r["ref"] for r in rows] == ["SHA"]      # the oldest first; one a day
    r = rows[0]
    assert (r["kind"], r["title"], r["url"], r["topic"], r["floor"]) == ("short", "A pillow Short", "https://youtu.be/ytS", "pillows", "") and r["asked"] and r["action_id"]
    a = next(x for x in core.store().rows("Owner_Actions") if x["id"] == r["action_id"])
    assert a["kind"] == "owner_verdict" and a["tier"] == "now" and a["episode_id"] == "SHA" and a["default_action"] == "" and a["dedupe_key"] == "verdict|SHA"
    assert json.loads(a["buttons"]) == [["Good", "VERDICT SHA UP"], ["Not good", "VERDICT SHA DOWN"]]
    assert a["text"] == ("Your verdict on the new Short 'A pillow Short': https://youtu.be/ytS - one tap. If you want to say why: tab Owner_Verdicts, row SHA, column text - "
                         "your Sheet is private; the mail link's title is a public page, never type the why there.")
    h = (core.parse_iso(a["expires_at"]) - core.parse_iso(a["created"])).total_seconds() / 3600; assert abs(h - 336) < 0.02
    V.sync(); assert len(core.store().rows("Owner_Verdicts")) == 1                                # OWNER_VERDICT_ASK_MAX_PER_DAY = 1
    verdict_on("OWNER_VERDICT_ASK_MAX_PER_DAY", "9"); verdict_on("NOTIFY_NOW_MAX_PER_DAY", "2")
    assert NT.now_room() == 1; V.sync(); assert len(core.store().rows("Owner_Verdicts")) == 1     # the day's last "act now" place is never taken by an ask
    verdict_on("NOTIFY_NOW_MAX_PER_DAY", "3"); assert NT.now_room() == 2; V.sync()
    rows = core.store().rows("Owner_Verdicts"); assert [r["ref"] for r in rows] == ["SHA", "EP209912030900"]
    assert (rows[1]["kind"], rows[1]["topic"], rows[1]["url"]) == ("long", "pillows", "https://youtu.be/ytL")
    assert "SHMADE" not in [r["ref"] for r in rows]                                              # a Short that is not public is never asked about
    _long("EP209912040900", title="The long two")                                                # (V1c finish, C15) its draw cell written as production writes it: a DICT
    core.store().update("Episodes", "episode_id", "EP209912040900", {"draw_json": {"ladder": "SHA"}})
    verdict_on("NOTIFY_NOW_MAX_PER_DAY", "4"); V.sync()
    assert _vrow("EP209912040900") and _vrow("EP209912040900")["topic"] == "pillows", _vrow("EP209912040900")

def test_an_ask_that_could_not_be_sent_leaves_no_row_and_is_sent_at_the_next_tick(verdict_on, monkeypatch):
    """(V1c finish, C14) ONE ROW A RELEASE, level-triggered: an ask whose write failed leaves no row behind, so the next sync asks again."""
    V = _VER(); verdict_on("OWNER_VERDICT_SINCE", _ago(days=3)); _short("SHRETRY", _ago(days=1))
    real_send = NT.send
    monkeypatch.setattr(NT, "send", lambda kind, *a, **k: (_ for _ in ()).throw(RuntimeError("sheet")) if kind == "owner_verdict" else real_send(kind, *a, **k))
    with pytest.raises(RuntimeError): V.sync()
    assert core.store().rows("Owner_Verdicts") == []
    monkeypatch.setattr(NT, "send", real_send)                                                       # the patch undone (the quiet hours stay off)
    V.sync(); r = _vrow("SHRETRY")
    assert r and r["action_id"] and next(x for x in core.store().rows("Owner_Actions") if x["id"] == r["action_id"])["status"] == "OPEN", r

def test_his_tap_is_the_label_and_words_after_it_are_not_stored(verdict_on):
    V = _VER(); verdict_on("OWNER_VERDICT_SINCE", _ago(days=3)); _short("SHT", _ago(days=1)); V.sync()
    aid = _vrow("SHT")["action_id"]
    out = NT.answer(aid, "VERDICT SHT UP I hated the voice in it")
    r = _vrow("SHT"); assert (V.read(r["verdict"]), r["via"], r["text"]) == ("up", "tap", "") and r["seen"]
    assert out.startswith("Kept: up on 'The Short'.") and "not stored" in out and "I hated" not in r["text"]

def test_an_unreadable_tap_asks_once_more_then_points_to_the_tab(verdict_on):
    V = _VER(); verdict_on("OWNER_VERDICT_SINCE", _ago(days=3)); verdict_on("NOTIFY_NOW_MAX_PER_DAY", "9"); _short("SHU", _ago(days=1)); V.sync()
    a1 = _vrow("SHU")["action_id"]
    assert NT.answer(a1, "VERDICT SHU MAYBE") == "I could not read that: tap Good or Not good on the new message"
    a2 = _vrow("SHU")["action_id"]; asks = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "owner_verdict" and x.get("episode_id") == "SHU"]
    assert a2 != a1 and len(asks) == 2 and asks[1]["dedupe_key"] == "verdict|SHU|2" and asks[1]["text"] == asks[0]["text"]
    assert NT.answer(a2, "hmm") == "type up or down in tab Owner_Verdicts, row SHU"
    assert len([x for x in core.store().rows("Owner_Actions") if x.get("kind") == "owner_verdict" and x.get("episode_id") == "SHU"]) == 2 and not _vrow("SHU")["seen"]

def test_a_typed_verdict_is_read_closes_its_message_and_his_words_are_never_overwritten(verdict_on):
    V = _VER(); verdict_on("OWNER_VERDICT_SINCE", _ago(days=3)); verdict_on("NOTIFY_NOW_MAX_PER_DAY", "9")
    _short("SHG", _ago(days=2)); _short("SHM", _ago(days=1), title="Meh Short"); verdict_on("OWNER_VERDICT_ASK_MAX_PER_DAY", "9"); V.sync()
    st = core.store()
    st.update("Owner_Verdicts", "ref", "SHG", {"verdict": " Good ", "text": "the hook made me stay"})
    st.update("Owner_Verdicts", "ref", "SHM", {"verdict": "meh", "text": "his own why"})
    V.sync()
    g = _vrow("SHG"); assert g["verdict"] == " Good " and g["text"] == "the hook made me stay" and g["via"] == "sheet" and g["seen"] and V.read(g["verdict"]) == "up"
    assert next(x for x in st.rows("Owner_Actions") if x["id"] == g["action_id"])["status"] == "ANSWERED"      # a Sheet answer closes its message
    V.record("SHG", "down", "another why", "tap"); assert V.read(_vrow("SHG")["verdict"]) == "up" and _vrow("SHG")["text"] == "the hook made me stay"      # a row with `seen`: nothing
    m = _vrow("SHM"); assert not m["seen"] and m["verdict"] == "meh"
    notes = [x for x in st.rows("Owner_Actions") if x.get("dedupe_key", "").startswith("told|SHM|")]
    assert len(notes) == 1 and notes[0]["text"] == "I could not read your verdict 'meh' on 'Meh Short': type up or down" and notes[0]["tier"] == "week"
    assert notes[0]["buttons"] == "[]" and notes[0]["kind"] == "owner_verdict" and json.loads(m["told"]) == ["unread|meh"]
    V.sync(); assert len([x for x in st.rows("Owner_Actions") if x.get("dedupe_key", "").startswith("told|SHM|")]) == 1      # told ONCE per value
    assert json.loads(_vrow("SHM")["told"]) == ["unread|meh"]
    V.record("SHM", "up", "a tap's words", "tap")                                                 # his later tap: the unread word is replaced (DESIGN QUESTION 11), his why never
    m = _vrow("SHM"); assert m["verdict"] == "up" and m["text"] == "his own why" and m["seen"]

def test_agree_after_a_floor_fail_and_his_drop_and_after_a_pass_and_his_hold(verdict_on, media):
    V = _VER(); from whatifs.org import memos as MEM
    core.store().append("Ladder", [{"id": "OVR1", "topic": "OVR1", "state": "OVERRIDE_USED"}])
    _long("EPAGF", status="HOLD_QC", yt="", title="Flop", draw={"ladder": "OVR1"}); _judged(media, "EPAGF", media["flop"], "S-agf")
    assert FL._answer({"episode_id": "EPAGF"}, "FLOOR DROP EPAGF") == "EPAGF is dropped"
    f = _vrow("EPAGF"); assert (f["kind"], V.read(f["verdict"]), f["via"], f["floor"], f["agree"]) == ("long", "down", "drop", "down", "TRUE")
    assert (f["topic"], f["url"], f["asked"], f["action_id"]) == ("", "", "", "")                  # under an override no topic; a row made by his verdict asks nothing
    _long("EPAGP", status="AWAITING_APPROVAL", title="Passed"); _judged(media, "EPAGP", media["film"], "S-agp", view="v")
    assert CON.hold_review("EPAGP") == "EPAGP stays private"
    p = _vrow("EPAGP"); assert (V.read(p["verdict"]), p["via"], p["floor"], p["agree"]) == ("down", "hold", "up", "FALSE")
    miss = [m for m in MEM.find(core.store(), type="problem_memo", from_dept="D13") if str(m.get("dedupe_key")).startswith("floor|miss")]
    assert len(miss) == 1 and 'the floor predicted up for EPAGP; the owner said down' in miss[0]["body"]["what_failed"]
    _long("EPAGQ", title="Good one"); _judged(media, "EPAGQ", media["film"], "S-agq", view="v2")
    out = V.record("EPAGQ", "up", "", "tap"); assert _vrow("EPAGQ")["agree"] == "TRUE" and "The floor had said up: it agrees." in out and "Floor so far: 2 of 3." in out
    assert not [m for m in MEM.find(core.store(), type="problem_memo", from_dept="D13") if str(m.get("dedupe_key")).startswith("floor|miss")]      # closed by the next TRUE

def test_the_score_and_its_memo(verdict_on, media):
    V = _VER(); from whatifs.org import memos as MEM
    def live(): return [m for m in MEM.find(core.store(), type="problem_memo", from_dept="D13") if str(m.get("dedupe_key")).startswith("floor|score")]
    for k in range(3):
        ep = f"EPSC{k}"; _long(ep, title=f"s{k}"); _judged(media, ep, media["film"], f"S-sc{k}", view="v"); V.record(ep, "down", "", "tap")
    assert V.score() == (0, 3) and len(live()) == 1 and "the floor disagreed with the owner on 3 of the last 3 videos" in live()[0]["subject"] + json.dumps(live()[0]["body"])
    assert live()[0]["done_when"] == "the floor agrees with the owner on at least 3 of his last 5 scored videos"
    for k in range(3, 5):
        ep = f"EPSC{k}"; _long(ep, title=f"s{k}"); _judged(media, ep, media["film"], f"S-sc{k}", view="v"); V.record(ep, "up", "", "tap")
    assert V.score() == (2, 5) and len(live()) == 1                                               # still 3 misses among the last 5
    ep = "EPSC5"; _long(ep, title="s5"); _judged(media, ep, media["film"], "S-sc5", view="v"); V.record(ep, "up", "", "tap")
    assert V.score() == (3, 5) and live() == []                                                   # 2 misses of 5: its done_when holds (DESIGN QUESTION 12)

def test_a_thumbs_up_is_a_reference_a_thumbs_down_and_a_refused_then_published_film_never(verdict_on, media, monkeypatch, tmp_path):
    V = _VER()
    _long("EPREF1", title="Approved one"); FL.plain(FL.run(None, "EPREF1", media["src"], str(tmp_path), (), ()))
    FL.plain(FL.run(None, "EPREF1", media["src"], str(tmp_path), (), ()))                         # held by another check, fixed: answered from the log, the first view kept
    view1 = next(r for r in core.store().rows("Floor_Log") if r["episode_id"] == "EPREF1")["view"]; assert view1
    V.record("EPREF1", "up", "", "tap")
    seen = lambda ref, m: core.store().update("Owner_Verdicts", "ref", ref, {"seen": _ago(minutes=m)})      # (V1c finish, C11) written apart: a film that must never be taken is always NEWER
    seen("EPREF1", 50)
    assert V.references("EPOTHER") == [("EPREF1", view1)] and V.references("EPREF1") == []        # never the episode being judged
    _long("EPREF2", title="Refused, published"); _judged(media, "EPREF2", media["flop"], "S-ref2", view="vr2"); V.record("EPREF2", "up", "", "tap"); seen("EPREF2", 40)
    _long("EPREF4", title="Its minute was not kept"); _judged(media, "EPREF4", media["film"], "S-ref4", view=""); V.record("EPREF4", "up", "", "tap"); seen("EPREF4", 30)
    _long("EPREF3", title="Void only")
    monkeypatch.setattr(M, "ask_watch", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))); _judged(media, "EPREF3", media["film"], "S-ref3", view="v3")
    monkeypatch.undo(); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False); V.record("EPREF3", "up", "", "tap"); seen("EPREF3", 20)
    verdict_on("VIEW_FLOOR_REFS_MAX", "3")
    assert V.references("EPOTHER") == [("EPREF1", view1)]                                          # a refused film, a film no valid session judged, a film whose minute was not kept: never
    verdict_on("VIEW_FLOOR_REFS_MAX", "0"); assert V.references("EPOTHER") == []
    _long("EPDN1", title='He said "no", twice'); _judged(media, "EPDN1", media["film"], "S-dn1", view="vd1"); V.record("EPDN1", "down", "", "tap"); seen("EPDN1", 10)
    _long("EPDN2", title="Refused and down"); _judged(media, "EPDN2", media["flop"], "S-dn2"); V.record("EPDN2", "down", "", "tap"); seen("EPDN2", 5)
    assert V.downs("EPOTHER") == []                                                                # the cell starts at 0
    verdict_on("VIEW_FLOOR_DOWNS_MAX", "2"); assert V.downs("EPOTHER") == [("EPDN1", "vd1", 'He said "no", twice')]      # the floor's own MISS, never a film it refused
    verdict_on("VIEW_FLOOR_REFS_MAX", "3"); assert ("EPDN1", "vd1") not in V.references("EPOTHER")
    verdict_on("VIEW_FLOOR_REFS_MAX", "5"); verdict_on("VIEW_FLOOR_DOWNS_MAX", "5")                 # (V1c step 7) room for every film: each pool keeps ITS verdict only
    assert V.references("EPOTHER") == [("EPREF1", view1)] and V.downs("EPOTHER") == [("EPDN1", "vd1", 'He said "no", twice')]
    verdict_on("OWNER_VERDICT_ON", "FALSE"); assert V.references("EPOTHER") == [] and V.downs("EPOTHER") == []   # the switch off: no reference, no down-canary (DESIGN QUESTION 9)

def test_the_pools_take_his_newest_verdicts_first_and_stop_at_their_cell(verdict_on, media):
    """(V1c finish, C20) Newest first, and the pool stops at its cell: with the default 1 the reference is his NEWEST approval alone."""
    V = _VER()
    for n, (ep, m) in enumerate((("EPPL1", 30), ("EPPL2", 20), ("EPPL3", 10))):
        _long(ep, title=f"T{n}"); _judged(media, ep, media["film"], f"S-pl{n}", view=f"vp{n}"); V.record(ep, "up", "", "tap")
        core.store().update("Owner_Verdicts", "ref", ep, {"seen": _ago(minutes=m)})
    verdict_on("VIEW_FLOOR_REFS_MAX", "1"); assert V.references("x") == [("EPPL3", "vp2")]                              # the cell's default: his NEWEST approval alone
    verdict_on("VIEW_FLOOR_REFS_MAX", "2"); assert V.references("x") == [("EPPL3", "vp2"), ("EPPL2", "vp1")]
    verdict_on("VIEW_FLOOR_REFS_MAX", "3"); assert V.references("EPPL3") == [("EPPL2", "vp1"), ("EPPL1", "vp0")]            # never the film being judged

def test_references_and_downs_are_empty_while_his_verdict_is_off(verdict_on, media):
    """(V1c finish, C11) A passed, kept film he thumbed up and one he thumbed down: both pools hold them while his verdict is on and nothing while it is off."""
    V = _VER()
    _long("EPSW1"); _judged(media, "EPSW1", media["film"], "S-sw1", view="vs1"); V.record("EPSW1", "up", "", "tap")
    _long("EPSW2", title="Down one"); _judged(media, "EPSW2", media["film"], "S-sw2", view="vs2"); V.record("EPSW2", "down", "", "tap")
    verdict_on("VIEW_FLOOR_DOWNS_MAX", "1")
    assert V.references("x") == [("EPSW1", "vs1")] and V.downs("x") == [("EPSW2", "vs2", "Down one")]
    verdict_on("OWNER_VERDICT_ON", "FALSE")
    assert V.references("x") == [] and V.downs("x") == []

def test_a_down_canary_fails_a_film_with_its_title_and_the_check_recomputes_it(verdict_on, media, monkeypatch):
    core.set_setting("VIEW_FLOOR_FAIL_HOLDS", "TRUE")                      # audit F10 (J18 ANSWER 1 (6)): a test that asserts a HOLD by the floor is the HOLD state's
    d = dict(media["film"], episode="EPDN", title='He said "no", twice')
    r = FL.session("S-down", "sha", media["film"], media["canary"], media["twin"], [], [d], "EPDOWN", view="vv")
    assert r["status"] == "fail" and r["why"].startswith("ranked beside a video you marked not good: ") and "'He said \"no\", twice'" in r["why"]
    rows = [x for x in core.store().rows("Floor_Log") if x["session_id"] == "S-down"]
    assert all(json.loads(x["downs"]) == ['He said "no", twice'] for x in rows) and FL.again(rows)["why"] == r["why"]
    assert CON.p_viewer_floor({"floor": r}) == (CON.FAIL, r["why"])                               # the check's own computation from the rows agrees
    t = 'He said "no", twice'                                                                       # (V1c finish, C16) the words of a fail by a down-canary alone, and its card
    assert r["why"] == "ranked beside a video you marked not good: " + "; ".join(f"{f}: '{t}'" for f in r["families"]) and r["hold"]["down"] == t, r["why"]
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False); FL.hold_card("EPDOWN", "T", r)
    card = next(x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == "EPDOWN" and x.get("kind") == "floor_hold")["text"]
    assert "ranked its first minute beside a video you marked not good, '" + t + "'" in card and "the video you rejected" not in card, card
    r0 = FL.session("S-nodown", "sha", media["film"], media["canary"], media["twin"], [], [], "EPDOWN0", view="vv")
    assert r0["status"] == "pass" and all(json.loads(x["downs"]) == [] for x in core.store().rows("Floor_Log") if x["session_id"] == "S-nodown")

def test_the_tick_asks_in_a_try_of_its_own_before_the_eye_sweep_and_the_finish_hands_the_floor_his_labels():
    from whatifs import manage as MG
    src = open(MG.__file__, encoding="utf-8").read(); i = src.index("NT.tick()")
    assert i < src.index("VERS.sync()") < src.index("FLR.eye_sweep()") < src.index("SH2.due()")
    e = open(EP.__file__, encoding="utf-8").read()
    assert "FLOOR.run(b, ep, master, out, VER.references(ep), VER.downs(ep))" in e and "master, out, (), ())" not in e
    n = open(NT.__file__, encoding="utf-8").read(); assert '("whatifs.org.verdicts", "register")' in n

def test_a_sheet_error_in_the_asks_never_stops_the_eye_sweep(verdict_on, monkeypatch):
    """(audit F5) "in a try of its own", run: `verdicts.sync` raises inside the REAL tick and `floor.eye_sweep` still runs - a film whose default failed is
    never left private for ever by an error in the asks."""
    from whatifs import manage as MG
    from whatifs.org import verdicts as VER_
    ran = []
    def boom(*a, **k): raise RuntimeError("the Sheet is down")
    monkeypatch.setattr(VER_, "sync", boom); monkeypatch.setattr(FL, "eye_sweep", lambda *a, **k: ran.append(1))
    MG.tick(); assert ran == [1]

def test_the_real_tick_sets_the_day_asks_about_a_short_and_schedules_a_film_his_silence_approved(verdict_on, monkeypatch):
    """(V1c finish, C13) The hooks run in the REAL tick job (the repo's rule for a new hook): the first tick sets the day, a later one asks about a new Short,
    and one schedules a film the floor could not judge whose eye card defaulted."""
    import datetime as dt
    from whatifs import manage as MG
    MG.tick(); assert S("OWNER_VERDICT_SINCE") and core.store().rows("Owner_Verdicts") == []                    # the real tick job, nothing called by hand
    _short("SHTICK", core.iso()); MG.tick()
    assert _vrow("SHTICK") and _vrow("SHTICK")["action_id"], _vrow("SHTICK")
    slot = (core.now_utc() + dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")                              # the eye test's own setup
    core.store().append("Episodes", [{"episode_id": "EPTICK", "status": "UPLOADED", "yt_id": "yt4", "slot_et": slot}])
    CON.await_approval("EPTICK", "yt4", slot, "summary", kind="floor_eye", default="goes public by itself", expires_h=FL.eye_hours(slot))
    card = next(r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == "EPTICK" and r.get("kind") == "floor_eye")
    core.store().update("Owner_Actions", "id", card["id"], {"status": "DEFAULTED"}); MG.tick()
    assert next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPTICK")["status"] == "SCHEDULED"

def test_owner_verdicts_is_written_by_its_own_module_alone():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); hits = []
    for base in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(root, base)):
            for f in fn:
                if f.endswith(".py") and f not in ("verdicts.py", "maker.py"):
                    t = open(os.path.join(dp, f), encoding="utf-8").read()
                    if re.search(r"\.(append|update|replace|update_where)\(\s*([\"']Owner_Verdicts[\"']|(VER|VERS|V)\.TAB\b)", t): hits.append(f)
    assert hits == [], hits
    src = open(_VER().__file__, encoding="utf-8").read(); assert "assets" not in src

# ================================================================== STEP 3. THE MAKER'S LINE (3.3): asked at the Short, never cut or mended, the film's last words
from whatifs import publish as PUB, qc as QC, sound as SD, motion as MOT_

GOOD_LINES = ("I would keep it for one day, then beg for gravity back.", "No.", "Never - my coffee is sacred.", "Judge me if you like, I'd keep it.", "My answer: never.")

@pytest.fixture
def line_on(setting, monkeypatch):
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    setting("OWNER_VERDICT_ON", "TRUE"); setting("MAKER_LINE_ON", "TRUE"); yield setting
    FMT.use("")

def _MK():
    from whatifs import maker as MK
    return MK

def _mkrow(ref, topic, line, seen):
    return dict(_VER().EMPTY, ref=ref, kind="short", title=ref, url="", topic=topic, floor="", maker_line=line, line_seen=seen)

def test_the_older_tests_run_with_his_line_off(setting, monkeypatch):
    from tests.conftest import OLD_VIEW
    MK = _MK()
    assert OLD_VIEW["MAKER_LINE_ON"] == "FALSE" and core.DEFAULTS["MAKER_LINE_ON"][0] == "TRUE" and MK.on() is False
    assert {k: core.DEFAULTS[k][0] for k in ("MAKER_LINE_MAX_WORDS", "MAKER_QUESTION", "MAKER_VOICE", "MAKER_VOICE_CONSENT")} == \
        {"MAKER_LINE_MAX_WORDS": "40", "MAKER_QUESTION": "would you keep this world?", "MAKER_VOICE": "", "MAKER_VOICE_CONSENT": ""}
    assert (MK.MAIL_MAX, MK.LEAD_SHORT, MK.LEAD_LONG) == (200, "And one answer, from the person who made this video.", "One last thing. The person who made this video was asked, {q} Here is the answer.")
    assert MK.CONSENT == "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    setting("OWNER_VERDICT_ON", "TRUE"); setting("OWNER_VERDICT_SINCE", _ago(days=3)); _short("SHOFF", _ago(days=1)); _VER().sync()
    assert [a["kind"] for a in core.store().rows("Owner_Actions") if a.get("episode_id") == "SHOFF"] == ["owner_verdict"]      # his verdict on, his line off: no second message
    core.store().update("Owner_Verdicts", "ref", "SHOFF", {"maker_line": "Subscribe for more."}); _VER().sync()
    assert _vrow("SHOFF")["line_seen"] == "" and not [a for a in core.store().rows("Owner_Actions") if a.get("kind") == "maker_line"]      # nothing of the line happens
    setting("MAKER_LINE_ON", "TRUE"); setting("OWNER_VERDICT_ON", "FALSE"); assert MK.on() is False                                        # the line lives in the verdict's row

def test_usable_passes_his_good_lines_and_refuses_what_would_be_cut_mended_or_an_ask(line_on):
    MK = _MK()
    for l in GOOD_LINES + ("Not for one hour.", "In 2026 I'd pay 3 rupees for it.", "Café owners would keep it.", "\"Never,\" I said."): assert MK.usable(l) == (True, ""), l
    for l, why in (("Judge: I'd keep it.", "speaker's label"), ("(laughing) I'd keep it.", "a sign at its start"), ("<3 it", "YouTube removes"), ("", "empty"), ("?! ...", "nothing in it can be spoken"),
                   ("Keep it [pause] forever.", "stage direction"), ("Keep it {softly}.", "stage direction"), ("I *love* it.", "signs the voice strips"), ("# Keep it.", "signs the voice strips"),
                   ("- keep it", "signs the voice strips"), ("Under__score it.", "signs the voice strips"), ("Use `code` here.", "signs the voice strips"),
                   ("See https://x.io for more.", "web address"), ("Go to www.example.com now.", "web address"),
                   ("Subscribe for more.", "subscribe, like, share or comment"), ("See you next week.", "points to another video")):
        ok, w = MK.usable(l); assert ok is False and why in w, (l, w)
    assert MK.usable("  No.\n ")[0] is True                                                                     # judged with its spaces made one
    assert MK.usable(" ".join(["word"] * 40) + ".")[0] is True
    ok, w = MK.usable(" ".join(["word"] * 41) + "."); assert ok is False and "41 words" in w and "never cut" in w
    line_on("MAKER_LINE_MAX_WORDS", "45"); assert MK.usable(" ".join(["word"] * 41) + ".")[0] is True            # the lever of D7

def test_the_question_is_data_and_the_lead_in_fits_the_ending(line_on):
    MK = _MK()
    assert MK.question() == "would you keep this world?"
    line_on("MAKER_QUESTION", "would you live there for a year?"); assert MK.question() == "would you live there for a year?"
    for bad in ("would you keep it", "note: would you keep it?", "would you [keep] it?", "would you <keep> it?"):
        line_on("MAKER_QUESTION", bad); assert MK.question() == "would you keep this world?", bad
    asked = "[DIRECTOR] You float above your bed.\n[DIRECTOR] Would you keep this world?"; told = "[DIRECTOR] You float above your bed.\n[DIRECTOR] And that is the day."
    line_on("ENDINGS_ON", "TRUE")
    with FMT.using("F1"): assert MK.lead(asked) == MK.LEAD_SHORT and MK.lead(told) == MK.LEAD_LONG.format(q=MK.question())      # the short one only after a real question
    for fmt in ("F2", "F3", ""):
        with FMT.using(fmt): assert MK.lead(asked) == MK.LEAD_LONG.format(q=MK.question()), fmt                                     # a trial, an arrival, no format: the film asked nothing
    line_on("ENDINGS_ON", "FALSE")
    with FMT.using("F1"): assert MK.lead(asked) == MK.LEAD_LONG.format(q=MK.question())
    assert MK.LEAD_LONG.format(q=MK.question()) == "One last thing. The person who made this video was asked, would you keep this world? Here is the answer."
    assert ":" not in MK.LEAD_SHORT and ":" not in MK.LEAD_LONG                                                                          # open issue 193

def test_his_line_goes_into_the_voice_after_a_long_pause_never_into_the_script(line_on):
    MK = _MK(); from whatifs import voice as VO
    clean = "[DIRECTOR] You float above your bed.\n\n[DIRECTOR] Would you keep this world?"; beats = [1, 1, 2]
    assert MK.attach(clean, beats, None) == (clean, beats) and MK.k(None) == 0
    mk = {"line": GOOD_LINES[0], "lead": MK.LEAD_LONG.format(q=MK.question()), "ref": "SH1", "at": "t"}
    voiced, vb = MK.attach(clean, beats, mk)
    assert voiced == clean + "\n[pause:long]\n[DIRECTOR] " + mk["lead"] + "\n[DIRECTOR] " + mk["line"] and vb == [1, 1, 2, 2, 2, 2] and len(voiced.splitlines()) == len(vb)
    us = VO.parse_script(voiced, line_beats=vb); base = VO.parse_script(clean, line_beats=beats)
    assert len(us) == len(base) + 4 and [u.text for u in us[-4:]] == ["One last thing.", "The person who made this video was asked, would you keep this world?", "Here is the answer.", GOOD_LINES[0]]
    assert all(u.speaker == "DIRECTOR" and u.beat == 2 for u in us[-4:]) and abs(us[-4].gap_before - 1.6) < 1e-9 and MK.k(mk) == 4      # the pause line makes no unit: 1.6 s before anybody answers
    three = dict(mk, line="No. Never. Not for one hour.", lead=MK.LEAD_SHORT); assert MK.k(three) == 4 and MK.E(three["line"]) == ["No.", "Never.", "Not for one hour."]
    assert MK.E("In 2026 I'd pay 3 rupees for it.") == ["In 2026 I'd pay 3 rupees for it."] and MK.E("Café owners would keep it.") == ["Café owners would keep it."]

def test_the_second_message_and_his_line_through_the_link(line_on):
    MK = _MK(); V = _VER(); line_on("OWNER_VERDICT_SINCE", _ago(days=3)); _short("SHL", _ago(days=1), title="Pillow Short"); V.sync()
    acts = [a for a in core.store().rows("Owner_Actions") if a.get("episode_id") == "SHL"]
    assert [a["kind"] for a in acts] == ["owner_verdict", "maker_line"]
    a = acts[1]
    assert (a["tier"], a["dedupe_key"], json.loads(a["buttons"])) == ("week", "makerline|SHL", [["My line", "LINE SHL"]])
    assert a["text"] == ("Your own last words for 'Pillow Short' (optional): add ONE sentence after LINE SHL in this link's title, or type it in tab Owner_Verdicts, row SHL, "
                         "column maker_line. If viewers pick this topic it becomes a long video and your sentence ends it: would you keep this world? At most 30 words through this link "
                         "(its title is a public page, like your line will be); up to 40 words in the tab. No line from you = none in the video.")
    h = (core.parse_iso(a["expires_at"]) - core.parse_iso(a["created"])).total_seconds() / 3600; assert abs(h - 336) < 0.02
    out = NT.answer(a["id"], "LINE SHL")                                                                 # a tap without words has spent the message: the same ask once more
    again = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "maker_line" and x.get("episode_id") == "SHL"]
    assert "No words came with your tap" in out and len(again) == 2 and again[1]["dedupe_key"] == "makerline|SHL|2" and again[1]["text"] == a["text"]
    assert NT.answer(again[1]["id"], "LINE SHL") == "Type your sentence in tab Owner_Verdicts, row SHL, column maker_line."
    assert len([x for x in core.store().rows("Owner_Actions") if x.get("kind") == "maker_line" and x.get("episode_id") == "SHL"]) == 2
    ans = lambda c: MK._answer({"episode_id": "SHL"}, c)
    assert ans("LINE SHL " + GOOD_LINES[0]) == f"Kept: \"{GOOD_LINES[0]}\". If viewers pick this topic, its long video ends on your sentence."
    r = _vrow("SHL"); assert r["maker_line"] == GOOD_LINES[0] and r["line_seen"] and r["line_used"] == ""
    ans("LINE SHL Not for one hour."); assert _vrow("SHL")["maker_line"] == "Not for one hour."                       # his newer words replace his older ones
    out = ans("LINE SHL Subscribe for more."); assert "is not used" in out and "subscribe, like, share or comment" in out
    long_ = "LINE SHL " + "and then " * 25; assert len(long_) > MK.MAIL_MAX
    assert ans(long_).startswith("Your sentence may have been cut on the mail route") and _vrow("SHL")["maker_line"] == "Subscribe for more."      # a cut line is never taken for his
    core.store().update("Ladder", "id", "SHL", {"state": "USED"})
    assert ans("LINE SHL Never - my coffee is sacred.") == "Your line for 'Pillow Short' came after its long video was planned: it is kept, but that video carries none."
    assert _vrow("SHL")["line_used"] == "" and _vrow("SHL")["maker_line"] == "Never - my coffee is sacred."
    core.store().append("Owner_Verdicts", [_mkrow("SHX", "other", "", "")])                              # (V1c finish, C8) the message's own ref decides, never the ref typed after LINE
    out = MK._answer({"episode_id": "SHL"}, "LINE SHX No.")
    assert out.startswith("That link is for SHL") and _vrow("SHX")["maker_line"] == "" and _vrow("SHL")["maker_line"] == "Never - my coffee is sacred.", out

def test_a_typed_line_is_seen_once_and_a_refused_or_late_one_is_told_once(line_on):
    V = _VER(); line_on("OWNER_VERDICT_SINCE", _ago(days=3)); line_on("OWNER_VERDICT_ASK_MAX_PER_DAY", "9"); line_on("NOTIFY_NOW_MAX_PER_DAY", "9")
    _short("SHA1", _ago(days=2), topic="moons"); _short("SHA2", _ago(days=1), topic="tides"); V.sync(); st = core.store()
    st.update("Owner_Verdicts", "ref", "SHA1", {"maker_line": "Subscribe for more."}); st.update("Owner_Verdicts", "ref", "SHA2", {"maker_line": "  No.  "}); V.sync()
    told = lambda ref: [a for a in st.rows("Owner_Actions") if a.get("episode_id") == ref and a.get("kind") == "maker_line" and str(a.get("dedupe_key")).startswith("told|")]
    assert _vrow("SHA1")["line_seen"] and _vrow("SHA2")["line_seen"] and _vrow("SHA2")["maker_line"] == "  No.  "                     # seen; his words are never rewritten
    t1 = told("SHA1"); assert len(t1) == 1 and "is not used" in t1[0]["text"] and t1[0]["tier"] == "week" and json.loads(t1[0]["buttons"]) == [] and not told("SHA2")
    st.update("Owner_Verdicts", "ref", "SHA1", {"line_seen": ""}); V.sync(); assert len(told("SHA1")) == 1                             # told once per value
    st.update("Ladder", "id", "SHA2", {"state": "USED"}); st.update("Owner_Verdicts", "ref", "SHA2", {"maker_line": "Never.", "line_seen": ""}); V.sync()
    assert len(told("SHA2")) == 1 and told("SHA2")[0]["text"] == "Your line for 'The Short' came after its long video was planned: it is kept, but that video carries none."

def test_his_line_is_taken_once_on_record_and_never_under_an_override(line_on):
    MK = _MK(); st = core.store()
    st.append("Ladder", [{"id": "SHP", "topic": "kettles", "title": "Kettle Short", "state": "PROMOTED"}, {"id": "SHF", "topic": "kettles", "title": "Follow-up", "state": "POSTED"},
                         {"id": "OVR9", "topic": "OVR9", "state": "OVERRIDE"}])
    st.append("Owner_Verdicts", [_mkrow("SHP", "kettles", "Not for one hour.", _ago(days=2)), _mkrow("SHF", "kettles", GOOD_LINES[0], _ago(days=1)),
                                 _mkrow("SHX", "other", "No.", _ago(hours=1)), _mkrow("SHO", "OVR9", "No.", _ago(hours=2))])
    clean = "[DIRECTOR] And that is the day."
    with FMT.using("F2"): mk = MK.take({"ladder": "SHP"}, "EPT1", clean)
    assert (mk["line"], mk["ref"], mk["lead"]) == (GOOD_LINES[0], "SHF", MK.LEAD_LONG.format(q=MK.question())) and mk["at"]      # the newest line of the TOPIC (a follow-up shares it)
    assert json.loads(_vrow("SHF")["line_used"]) == {"ep": "EPT1", "line": GOOD_LINES[0]} and _vrow("SHP")["line_used"] == "" and _vrow("SHX")["line_used"] == ""
    assert MK.take({"ladder": "OVR9"}, "EPT2", clean) is None and MK.take({"ladder": ""}, "EPT2", clean) is None                     # an override has no Short; no ladder row, no line
    st.update("Owner_Verdicts", "ref", "SHF", {"maker_line": "See you next week.", "line_used": ""})
    assert MK.take({"ladder": "SHP"}, "EPT3", clean) is None and _vrow("SHF")["line_used"] == "" and _vrow("SHP")["line_used"] == ""   # the newest is not usable: none, never an older one

def test_the_mark_pads_first_then_appends_one_still_a_unit_of_his(line_on):
    MK = _MK(); mk = {"line": "No. Never. Not for one hour.", "lead": MK.LEAD_SHORT, "ref": "SH", "at": "t"}
    units = _units(8) + [{"start": 40.0 + k, "end": 40.9 + k, "text": t, "speaker": "DIRECTOR"} for k, t in enumerate(MK.E(mk["lead"]) + MK.E(mk["line"]))]
    assert MK.k(mk) == 4 and len(units) == 12
    shots = [{"type": "still", "prompt": f"p{k}"} for k in range(5)] + [{"type": "living", "prompt": "the last living"}, {"type": "graphic", "graphic": {}}]      # one short of the 8 lines
    out = MK.mark(shots, units, mk)
    assert len(out) == 12 and out[7] == {"type": "still", "prompt": units[7]["text"], "unit": 7}                                      # padded as plan_check pads it, BEFORE the mark
    assert [i for i, s in enumerate(out) if s.get("maker")] == [8, 9, 10, 11]                                                         # a three-sentence line marks every one of its units
    assert all(out[i] == {"unit": i, "type": "still", "prompt": units[7]["text"], "hero": False, "focus": "wide", "maker": True} for i in range(8, 12))
    shots2 = [{"type": "still", "prompt": "the street at dusk"}, {"type": "living", "prompt": "the square"}, {"type": "stock", "prompt": "nasa"}, {"type": "graphic"},
              {"type": "reaction", "prompt": "grimm"}, {"type": "still", "prompt": ""}, {"type": "kling", "prompt": " "}, {"type": "graphic"}]
    assert MK.mark(shots2, units, mk)[8]["prompt"] == "the square"                                                                    # footage, graphics, cutaways and shots without words are passed over
    assert MK.mark(shots, units, None) is shots and MK.script_units(out, units) == units[:8] and MK.script_units(shots, units) == units
    assert len(MK.mark(shots + [{"type": "still", "prompt": "extra"}] * 9, units, mk)) == 12                                          # a list longer than the script is cut to it first

def _mshots(n_script, k, prompt="p"):
    return [{"type": "still", "prompt": f"{prompt}{i}"} for i in range(n_script)] + [{"unit": n_script + j, "type": "still", "prompt": f"{prompt}{n_script - 1}", "hero": False, "focus": "wide", "maker": True} for j in range(k)]

def test_his_lines_never_get_a_picture_of_their_own_and_plan_check_keeps_the_mark(line_on, monkeypatch, tmp_path):
    shots = _mshots(4, 6)
    assert not [i for i in EP.anchor_shots(shots, budget=40, max_run=3) if shots[i].get("maker")]                 # whatever the budget, and no "fresh picture in the middle" of his run
    S_ = {"shots": [dict(s) for s in shots], "plan": {}, "vo": {"duration": 999}, "pkg": {"titles": ["t"]}}
    out = EP.plan_check(S_, _units(10))["shots"]; assert [i for i, s in enumerate(out) if s.get("maker")] == list(range(4, 10)) and all(s["type"] == "still" for s in out)
    rec = []
    monkeypatch.setattr(EP.M, "still", lambda p, path, ep, seed=None, **k: (rec.append(p), (path, None))[1]); monkeypatch.setattr(EP.Job, "render_all", lambda self: None)
    monkeypatch.setattr(EP, "month_spend", lambda: 0.0)
    job = EP.Job(ep="EPR", out=str(tmp_path), files={"img": {i: "x.jpg" for i in range(4)}, "clips": {}, "anchors": [0, 1, 2, 3], "missing": []}, shots=shots, units=_units(10), vo=None, fps=25)
    job.repair_assets({"reuse_run"}, [], 50.0); assert rec == []                                                   # the reuse_run repair never buys a picture "accurate to" his line

def test_his_still_is_never_an_acts_first_and_an_act_without_a_picture_leaves_his_shots_unmarked(line_on):
    line_on("CAMERA_PATH_ON", "TRUE"); u12 = _units(12)
    with FMT.using("F1"):
        last = PATH.acts([{"type": "still"}] * 12, u12, 60.0)[-1]["units"]; assert len(last) >= 2
        sh = [{"type": "still", "prompt": "his", "maker": True} if k in last else {"type": "still", "prompt": f"p{k}"} for k in range(12)]
        out, _ = PATH.mark(sh, u12, 60.0, BIBLE, "EPM")
        assert all("path" not in out[i] for i in last) and all(out[i].get("path") for i in range(12) if i not in last)              # they continue what is on screen
        laid0 = PATH.lay(out); rep = PATH.plan_report(laid0, u12, 60.0, EP.anchors_for(laid0, u12, {"stills": 40}, {})); assert rep["problems"] == [], rep["problems"]      # (V1c finish, C7) and are not judged for a direction
        assert PATH.shown_report([{"type": "still", "act": None, "i": last[0], "src": 3, "move": "", "sign": 0, "t0": 50.0}], laid0)["problems"] == []
        sh3 = [dict(s) for s in sh]; sh3[last[1]] = {"type": "still", "prompt": "the act's own picture"}
        out, _ = PATH.mark(sh3, u12, 60.0, BIBLE, "EPM")
        assert out[last[1]]["path"]["first"] is True and out[last[0]]["path"]["first"] is False and out[last[0]]["path"]["act"] == out[last[1]]["path"]["act"]
        laid = PATH.lay(out)                                                                                                         # lay: NO skip - the place sentence is on his shot
        assert all(PATH.sentence(laid[i]["path"]["place"]) in laid[i]["prompt"] for i in last)
        anchors = EP.anchors_for(laid, u12, {"stills": 40}, {}); assert last[1] in anchors and last[0] not in anchors
        assert PATH.plan_report(laid, u12, 60.0, anchors)["problems"] == []                                                         # camera_path's rules hold

def test_his_line_is_never_the_slot_of_a_paid_scene(line_on):
    line_on("ANIM_SHOTS", "4"); line_on("ANIM_DIRECTOR_ON", "TRUE"); u14 = _units(14); sh = _mshots(10, 4)
    assert [i for i in AN.pick_slots([dict(s, maker=False) for s in sh], u14, 4) if i >= 10]                        # a short film: as plain stills, the 0.92 anchor falls on his line
    assert AN.pick_slots(sh, u14, 4, skip={i for i in range(10, 14)}) == AN.pick_slots(sh[:10], u14[:10], 4)       # the scenes stand where the film without his line has them (DESIGN QUESTION 21)
    idx = AN.apply(sh, u14, {"kling": 4}); assert len(idx) == 4 and not [i for i in idx if sh[i].get("maker")]
    assert all(s["type"] == "still" and "anim" not in s for s in sh[10:])
    sh2 = _mshots(2, 4); assert sorted(AN.apply(sh2, _units(6), {"kling": 4})) == [0, 1]                           # (V1c step 7) the script runs out of shots first: the later anchors stay empty, never his line
    assert all(s["type"] == "still" and "anim" not in s for s in sh2[2:])
    p2 = {"kling": 4}; AN.apply(_mshots(2, 4), _units(6), p2); assert p2["kling"] == 2                              # (V1c finish, C19) the two empty anchors are not bought
    sh4 = _mshots(3, 4); sh4[0]["short"] = {"id": "SHX", "parts": []}                                                # the road every laddered film takes: the opening is the Short's footage
    assert sorted(AN.apply(sh4, _units(7), {"kling": 4})) == [1, 2] and all(s["type"] == "still" and "anim" not in s for s in sh4[3:])

def test_no_clip_runs_into_his_line_and_none_is_bought_on_it(line_on):
    from tests.conftest import OLD_CLIPS, OLD_MOTION
    for k in list(OLD_CLIPS) + list(OLD_MOTION): line_on(k, core.DEFAULTS[k][0])
    line_on("MONTH_CAP_OVERRIDES", "")
    assert MOT_.plain({"type": "still"}) and not MOT_.plain({"type": "still", "maker": True})
    units = [{"start": 6.0 * k, "end": 6.0 * k + 5.9, "text": "x"} for k in range(6)]
    sh = [{"type": "still"}, {"type": "graphic"}, {"type": "still", "maker": True}, {"type": "still", "maker": True}, {"type": "still", "maker": True}, {"type": "still", "maker": True}]
    plan = {"living_s": 60}; out = MOT_.place(sh, units, 36.0, plan)
    assert all(out[i]["type"] == "still" and "buy" not in out[i] for i in range(2, 6)) and out[0]["type"] == "living"       # free budget, his line the farthest still: never brought to life
    sh2 = [{"type": "still"}, {"type": "still", "maker": True}, {"type": "still", "maker": True}]; u3 = units[:2] + [{"start": 7.0, "end": 12.0, "text": "x"}]
    assert MOT_.room_s(0, sh2, MOT_.lines_of(u3, 12.0), set()) < 7.0                                                         # a clip's room stops at his line

def test_no_sound_is_chosen_from_his_words(line_on):
    units = [{"start": 10.0 * k, "end": 10.0 * k + 9, "text": "you stand in your kitchen", "speaker": "DIRECTOR", "tag": "none"} for k in range(6)] + \
            [{"start": 60.0 + 10 * k, "end": 69.0 + 10 * k, "text": t, "speaker": "DIRECTOR", "tag": "none"} for k, t in enumerate(["Rain and thunder, a storm at sea.", "Behold the prototype exhibit, with fire."])]
    shots = [{"type": "still", "prompt": "a kitchen"} for _ in range(6)] + [{"type": "still", "prompt": "a kitchen", "maker": True, "sound": "rain"}] * 2
    out = SD.plan_sounds(shots, units, "rich"); assert all(out[i]["sound"] == "none" for i in (6, 7))                         # no texture from his words, not even the Director's choice
    assert [s["sound"] for s in SD.plan_sounds([dict(s, maker=False) for s in shots], units, "rich")][6:] != ["none", "none"]  # (without the mark one is chosen: the test can fail)
    line_on("SOUND_WORLDS_ON", "FALSE"); res = SD.immersive(shots, units, 80.0, seed="m")
    assert all(a[0] == res["ambience"][0][0] for a in res["ambience"])                                                       # the bed of the last scene goes on under his line
    line_on("SOUND_WORLDS_ON", "TRUE"); res = SD.immersive(shots, units, 80.0, seed="m")
    assert not [e for e in res["foley"] if e[0] in ("fizzle", "paper") and e[1] >= 59.0]                                     # no story event on "prototype" or "exhibit" in his sentence
    units2 = [dict(u, speaker="JUDGE") if 3 <= k < 6 else dict(u) for k, u in enumerate(units)]                              # (V1c finish, C6) a trial that ends on the Judge (court)
    line_on("SOUND_WORLD_MIN_S", "5"); amb = SD.immersive(shots, units2, 80.0, seed="m")["ambience"]                         # his two units are the guide's (office)
    assert amb[-1][0] == SD.WORLD_AMB["court"] and amb[-1][2] == 80.0 and not [a for a in amb if a[1] >= 59.0], amb          # the bed of the last scene goes on under his line

def test_the_picture_judge_never_rates_his_line_and_his_stills_are_no_reuse_run(line_on):
    u20 = _units(20); sh = _mshots(14, 6)
    assert max(QC.vision_indexes(u20, sh, 12)) < 14 and max(QC.vision_indexes(u20, [{"type": "still"}] * 20, 12)) >= 14
    assert QC.reuse_runs(sh, set(range(14))) == 0 and QC.reuse_runs([{"type": "still"}] * 20, set(range(14))) == 6           # k = 6: one held picture by design

def test_the_two_budgets_per_minute_are_the_scripts_own(line_on):
    line_on("VIEWER_SEAT_ON", "TRUE"); line_on("LAYMAN_ON", "TRUE")
    lines = [f"In 2026 you count {k} floating cups and 3 spoons." for k in range(12)]
    units = [{"start": 5.0 * k, "end": 5.0 * k + 4.8, "text": t, "speaker": "DIRECTOR"} for k, t in enumerate(lines)]
    his = [{"start": 62.0 + 14 * k, "end": 75.8 + 14 * k, "text": t, "speaker": "DIRECTOR"} for k, t in enumerate(["One last thing.", "The person who made this video was asked, would you keep this world?", "Here is the answer.", "Not for one hour."])]
    base = {"room": {"script": {"script": "\n".join("[DIRECTOR] " + t for t in lines)}}, "d": {}, "pkg": {}}
    shots = [{"type": "still", "prompt": "p"} for _ in range(12)]
    a = dict(base, shots=shots, units=units); b = dict(base, shots=shots + [{"type": "still", "prompt": "p", "maker": True}] * 4, units=units + his)
    for f in (CON.p_viewer_numbers, CON.p_viewer_plain): assert f(a) == f(b), f.__name__
    c = dict(base, shots=shots + [{"type": "still", "prompt": "p"}] * 4, units=units + his)                         # his seconds, unmarked, WOULD widen both budgets (the test can fail)
    assert CON.p_viewer_numbers(c) != CON.p_viewer_numbers(a) and CON.p_viewer_plain(c) != CON.p_viewer_plain(a), (CON.p_viewer_plain(c), CON.p_viewer_plain(a))

def test_his_paragraph_closes_the_description_and_is_never_translated(line_on, monkeypatch):
    MK = _MK(); from whatifs import hours as HR, models as M_
    line = "Café owners would keep it, 3 days a week."
    d = EP._description("Hook line.", [], {"spine": {"premise": "p"}}, "EPD", credits="Real footage: NASA.", maker=line)
    assert d.endswith("\n\nReal footage: NASA.\n\n" + MK.paragraph(line) + "\n\nThis video uses AI-assisted visuals and narration over an original script. Science is simplified for storytelling.")
    assert MK.find(d) == MK.paragraph(line) == "The maker's answer: \"Café owners would keep it, 3 days a week.\"" and MK.find(d + "\n\n" + MK.paragraph(line)) == ""
    no = EP._description("Hook line.", [], {"spine": {"premise": "p"}}, "EPD", credits="Real footage: NASA."); assert no == d.replace("\n\n" + MK.paragraph(line), "")      # without a line: as before
    seen = []
    def ask(task, system, prompt, **k):
        x = json.loads(prompt); seen.append(x["description"])
        return {l: {"title": "T " + l, "description": " ".join(w[::-1] for w in x["description"].split())} for l in x["langs"]}         # a free translation: every word rewritten
    monkeypatch.setattr(M_, "ask", ask)
    loc = HR.translate("Your Phone Weighs 400 Kilos", d)
    assert len(loc) == 6 and "The maker's answer" not in seen[0] and line not in seen[0]                                                  # the model never sees his line
    for l, v in loc.items(): assert v["description"].endswith("\n\n" + MK.paragraph(line)) and v["description"].count(MK.paragraph(line)) == 1, l     # byte for byte, once, in every language
    big = d.replace("Hook line.", "Hook " + "x" * 4700)
    for v in HR.translate("t", big).values(): assert v["description"].endswith("\n\n" + MK.paragraph(line)) and len(v["description"]) <= 4500     # cut before it, never into it
    seen.clear(); a = HR.translate("t", no); assert seen[0] == no[:4000] and all(v["description"] == " ".join(w[::-1] for w in no[:4000].split())[:4500] for v in a.values())    # no line: as it did

def _mk_ctx(MK, line="In 2026 I'd pay 3 rupees for it.", lead=None, ep="EPC1"):
    lead = lead or MK.LEAD_LONG.format(q=MK.question()); mk = {"line": line, "lead": lead, "ref": "SHC", "at": "t"}
    units = [{"start": float(k), "text": f"Script line {k}.", "speaker": "SKEPTIC"} for k in range(5)] + \
            [{"start": 5.0 + k, "text": t, "speaker": "DIRECTOR"} for k, t in enumerate(MK.E(lead) + MK.E(line))]
    desc = PUB.clean_meta("t", EP._description("Hook.", [], {"spine": {}}, ep, maker=line), [])[1]
    return {"ep": ep, "units": units, "description": desc, "maker": mk, "maker_used": json.dumps({"ep": ep, "line": line}), "maker_states": [(i, "still", 4) for i in range(5, len(units))]}

def test_check_makers_line_both_ways(line_on):
    MK = _MK(); ok = _mk_ctx(MK)
    assert CON.p_makers_line(ok) == (CON.PASS, "the film ends on his own line, word for word: \"In 2026 I'd pay 3 rupees for it.\"; the same line is in the description")
    assert CON.p_makers_line({k: v for k, v in ok.items() if k != "maker"}) == (CON.NA, "planned before the maker's line existed")
    line_on("MAKER_LINE_ON", "FALSE"); assert CON.p_makers_line(ok)[0] == CON.NA; line_on("MAKER_LINE_ON", "TRUE")
    bad = lambda **ch: CON.p_makers_line(dict(ok, **ch))
    rec = "the line in this film is not on his record"; word = "his line is on record and the film does not end on it, word for word"
    assert bad(maker_used="") == (CON.FAIL, rec) and bad(maker_used=json.dumps({"ep": "EPOTHER", "line": ok["maker"]["line"]})) == (CON.FAIL, rec)
    assert bad(maker_used=json.dumps({"ep": "EPC1", "line": "Another line."})) == (CON.FAIL, rec)
    u = [dict(x) for x in ok["units"]]; u[-1]["text"] = u[-1]["text"].replace("3", "4"); assert bad(units=u) == (CON.FAIL, word)                 # ONE digit changed
    acc = _mk_ctx(MK, line="Café owners would keep it."); assert CON.p_makers_line(acc)[0] == CON.PASS
    u = [dict(x) for x in acc["units"]]; u[-1]["text"] = u[-1]["text"].replace("é", "e"); assert CON.p_makers_line(dict(acc, units=u)) == (CON.FAIL, word)      # an accented letter
    u = [dict(x) for x in ok["units"]]; u[-2]["speaker"] = "SKEPTIC"; assert bad(units=u) == (CON.FAIL, word)
    assert bad(units=ok["units"] + [{"start": 99.0, "text": "Subscribe for more.", "speaker": "DIRECTOR"}]) == (CON.FAIL, word)                   # the film must END on it
    own = _mk_ctx(MK, lead="Here is a word from me."); assert CON.p_makers_line(own) == (CON.FAIL, word)                                         # a lead-in that is neither of the two
    assert CON.p_makers_line(_mk_ctx(MK, lead=MK.LEAD_LONG.format(q="would you live there?")))[0] == CON.PASS                                   # the long one with another question (DESIGN QUESTION 18)
    assert CON.p_makers_line(_mk_ctx(MK, lead=MK.LEAD_SHORT))[0] == CON.PASS
    assert bad(description=ok["description"].replace("The maker's answer", "The answer")) == (CON.FAIL, "his line is not in the description that is sent")
    assert bad(description=ok["description"] + "\n\n" + MK.paragraph(ok["maker"]["line"]))[0] == CON.FAIL                                       # exactly once
    sent = PUB.clean_meta("t", EP._description("Hook " + "x" * 5200, [], {"spine": {}}, "EPC1", maker=ok["maker"]["line"]), [])[1]
    assert bad(description=sent) == (CON.FAIL, "his line is not in the description that is sent")                                                # 5,200 bytes: cut from the end, where it sits
    pic = "his line is spoken over a picture made for it"
    assert bad(maker_states=ok["maker_states"] + [(9, "still", 9)]) == (CON.FAIL, pic) and bad(maker_states=[(6, "living", 4)]) == (CON.FAIL, pic)
    no = dict(ok, maker=None, maker_used="", maker_states=[], units=ok["units"][:5], description=PUB.clean_meta("t", EP._description("Hook.", [], {"spine": {}}, "EPC1"), [])[1])
    assert CON.p_makers_line(no) == (CON.PASS, "he gave no line for this topic: none is spoken, none is written")
    for lead in MK.leads():
        u = ok["units"][:5] + [{"start": 9.0 + k, "text": t, "speaker": "DIRECTOR"} for k, t in enumerate(MK.E(lead))]
        assert CON.p_makers_line(dict(no, units=u)) == (CON.FAIL, "the film speaks a maker's lead-in and no line of his is on record")         # a lead-in without a record
    assert CON.p_makers_line(dict(no, description=ok["description"])) == (CON.FAIL, "the description carries a maker's answer and no line of his is on record")

def test_a_voice_without_his_consent_stops_the_preflight_offline(line_on):
    import inspect
    from whatifs import preflight as PF
    MK = _MK(); assert MK.voice_issues() == [] and ("maker voice", True, "", True) in PF.run()
    line_on("MAKER_VOICE", "his-voice"); ok, why = PF.check(); assert ok is False and "MAKER_VOICE_CONSENT holds no consent record" in why       # OFFLINE: the refusal runs in fake mode
    line_on("MAKER_VOICE_CONSENT", json.dumps({"file": "", "date": "2026-11-15", "words": "I agree."}))
    assert MK.voice_issues() == ["the consent record names no file", "the consent record's words are not the voice provider's consent sentence"]
    line_on("MAKER_VOICE_CONSENT", json.dumps({"file": "consent.wav", "date": "2026-11-15", "words": MK.CONSENT})); assert MK.voice_issues() == []
    src = inspect.getsource(PF.run); assert src.index('add("maker voice", not MAKER.voice_issues(), "; ".join(MAKER.voice_issues()))') < src.index("if FAKE: return r")

def test_the_overlays_are_built_from_the_scripts_own_units(line_on):
    import inspect
    MK = _MK(); from whatifs import overlay as OV
    units = [{"start": 0.0, "end": 3.0, "text": "Order in the court.", "speaker": "DIRECTOR"}, {"start": 3.0, "end": 6.0, "text": "Fine.", "speaker": "SKEPTIC"},
             {"start": 8.0, "end": 9.0, "text": MK.LEAD_SHORT, "speaker": "DIRECTOR"}, {"start": 9.0, "end": 12.0, "text": "There is nothing like this world.", "speaker": "DIRECTOR"}]
    shots = [{"type": "still"}, {"type": "still"}, {"type": "still", "maker": True}, {"type": "still", "maker": True}]
    drawn = {"DIRECTOR", "SKEPTIC"}                                                                                   # VALE's art approved: the guide is drawn and named
    assert any(a >= 8.0 for a, _b, _s in OV.SpeakerTag(units, 640, 360, 25, drawn=drawn).spans)                       # the whole timeline would name a character over his words
    assert not any(a >= 8.0 for a, _b, _s in OV.SpeakerTag(MK.script_units(shots, units), 640, 360, 25, drawn=drawn).spans)
    assert any(a >= 8.0 for a, _b, _k in OV.CtaChip(units, 640, 360, 25).spans) and not any(a >= 8.0 for a, _b, _k in OV.CtaChip(MK.script_units(shots, units), 640, 360, 25).spans)
    src = inspect.getsource(EP._render)
    assert "SpeakerTag(MAKER.script_units(shots, units), ww, wh, fps, drawn=drawn_)" in src and "CtaChip(MAKER.script_units(shots, units), ww, wh, fps)" in src

def test_the_final_gate_reads_the_description_that_is_sent_and_a_plan_without_the_key_is_not_judged():
    import inspect
    src = inspect.getsource(EP._finish)
    assert 'cctx["description"] = PUB.clean_meta(title, desc, [])[1]' in src and 'if "maker" in S_: cctx["maker"] = mk_' in src      # yt_body sends clean_meta's text (it cuts from the END)

def test_line_used_is_written_by_take_alone_and_a_rerender_never_rewrites_what_a_state_shows():
    import inspect
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rx = re.compile(r"[\"']line_used[\"']\s*:"); hits = {}
    for base in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(root, base)):
            for f in fn:
                if f.endswith(".py") and f != "maker.py":
                    n = len(rx.findall(open(os.path.join(dp, f), encoding="utf-8").read()))
                    if n: hits[f] = n
    assert hits == {"verdicts.py": 1}, hits                                                                          # the empty cell of a new row; nobody else writes it
    assert not re.search(r"m\[\s*[\"'](i|type|src)[\"']\s*\]\s*=", inspect.getsource(EP.Job.rerender_times))

# ================================================================== STEP 4. ONE STORY (3.4): the thumbnail a viewer taps is the picture the film opens on
from whatifs import story as STORY, opening as OPEN_, room as ROOM_

W = "a city of floating pillows over your street"
OPN = {"short": "SH1", "picture": "  a city of  floating pillows\nover your street "}     # the archive's words as the Short's plan wrote them; one story speaks them with their spaces made one
D1 = {"ladder": "SH1"}

@pytest.fixture
def story_on(setting, monkeypatch):
    setting("ONE_STORY_ON", "TRUE")
    monkeypatch.setattr(OPEN_, "source", lambda d: ("short", {"id": "SH1"}) if str((d or {}).get("ladder") or "") == "SH1" else ("override", {"id": "OV1", "by": "owner"}))
    yield setting

def test_the_older_tests_run_with_one_story_off():
    from tests.conftest import OLD_VIEW
    assert OLD_VIEW["ONE_STORY_ON"] == "FALSE" and core.DEFAULTS["ONE_STORY_ON"][0] == "TRUE" and STORY.on() is False
    assert (STORY.OTHER_LOOK, STORY.B_MAX) == ("a closer look from another angle", 160)
    assert STORY.BRIEF.format(words="X") == ("THUMBNAIL SCENE (fixed: the picture this video opens on, the one real viewers stayed for): \"X\". Write thumb_text for THIS scene. "
                                            "For the runner-up write thumb_prompt_b as ANOTHER LOOK AT THE SAME SCENE - closer or wider, the same place, the same impossible thing - "
                                            "and thumb_text_b as other words for it; never another scene: whichever thumbnail a viewer taps, the video opens on what it showed."
                                            " This replaces the rule above that the runner-up is built on a DIFFERENT idea: here it is the SAME scene, seen another way.")      # (V1c finish, C9: a pin moved by design)

def test_the_manifest_carries_the_words_the_shorts_first_clip_was_drawn_from(monkeypatch, tmp_path):
    from whatifs import release as REL
    monkeypatch.setattr(REL, "probe", lambda p: {"w": 1080, "h": 1920, "sec": 3.0}); monkeypatch.setattr(REL, "sha", lambda p: "s")
    wd = _dir(tmp_path / "a")
    for i in range(3): open(os.path.join(wd, f"c{i}.mp4"), "wb").close()
    plan = {"shots": [{"i": 1, "start": 2.0, "end": 4.0, "picture": "the second picture"}, {"i": 2, "src": "loop", "start": 0.0, "end": 1.0, "picture": "the loop"},
                      {"i": 0, "start": 0.5, "end": 2.0, "picture": "  a city of  floating pillows "}]}
    man = OPEN_.manifest({"plan": plan, "timeline": {"units": [{"text": "[tension] What if?"}]}}, wd)
    assert man["picture"] == "a city of  floating pillows" and STORY.first_picture(man) == man["picture"] and man["hook"] == "What if?"     # the FIRST clip of the plan, never the loop
    plan["shots"][2]["picture"] = None; assert OPEN_.manifest({"plan": plan}, wd)["picture"] == ""
    assert STORY.first_picture(None) == "" and STORY.first_picture({"none": "override", "why": "x"}) == ""

def _pack(monkeypatch, d, opening):
    seen = []
    monkeypatch.setattr(ROOM_, "ask", lambda role, system, prompt, **kw: (seen.append(str(system) + " " + str(prompt)), {"titles": ["What if pillows floated?"], "thumb_prompt": "another scene", "thumb_text": "UP"})[1])
    room = {"script": {"script": "## BEAT 1\n[calm] You wake up and your pillow is on the ceiling."}, "spine": {"premise": "every pillow floats", "promise": {}}}
    pkg = ROOM_.package(room, [("0:00", "Intro")], dict(d, strategies={"title": "N1_what_if", "thumb": "T1_object_scale"}), "EPST1", opening=opening)
    return seen[-1], pkg

def test_the_packager_is_told_the_scene_on_a_laddered_video_and_not_under_an_override(story_on, monkeypatch):
    s, _ = _pack(monkeypatch, D1, OPN); assert STORY.BRIEF.format(words=W) in s and "This replaces the rule above" in s      # (V1c finish, C9) the opposite order of the base prompt is named
    for d, opn in (({"ladder": "OV1"}, OPN), (D1, {"short": "SH1", "picture": ""}), (D1, None)):          # an override; an archive with no picture words; no opening
        s, _ = _pack(monkeypatch, d, opn); assert "THUMBNAIL SCENE (fixed" not in s
    story_on("ONE_STORY_ON", "FALSE"); s, _ = _pack(monkeypatch, D1, OPN); assert "THUMBNAIL SCENE (fixed" not in s

def test_align_makes_both_thumbnails_the_opening_scene_by_construction(story_on):
    p = STORY.align({"thumb_prompt": "a pillow on the moon", "thumb_prompt_b": "  a pillow  seen from below ", "thumb_text": "UP", "titles": ["T"]}, D1, OPN)
    assert (p["thumb_prompt"], p["thumb_prompt_b"], p["thumb_text_b"], p["one_story"]) == (W, W + "; a pillow seen from below", "UP", {"short": "SH1", "words": W})
    assert p["titles"] == ["T"] and p["thumb_text"] == "UP"                                                  # the title and the thumbnail's words stay the packager's
    q = STORY.align({"thumb_prompt": "a pillow on the moon", "thumb_text": "UP", "thumb_text_b": "LOOK"}, D1, OPN)
    assert q["thumb_prompt_b"] == W + "; a pillow on the moon" and q["thumb_text_b"] == "LOOK"               # no runner-up written: its own scene becomes the other look
    assert STORY.align({"thumb_prompt": W}, D1, OPN)["thumb_prompt_b"] == W + "; " + STORY.OTHER_LOOK        # nothing else written
    lw = ("floating-pillows-" * 13)[:220]; r = STORY.align({"thumb_prompt": "x", "thumb_prompt_b": "y" * 300}, D1, {"picture": lw})
    assert len(lw) == 220 and r["thumb_prompt"] == lw and r["thumb_prompt_b"] == lw + "; " + "y" * 160       # the scene's words are never cut - only what follows them
    assert CON.p_one_story({"d": D1, "pkg": r, "opening": {"picture": lw}})[0] == CON.PASS
    cut = dict(r, thumb_prompt_b=r["thumb_prompt_b"][:160]); assert CON.p_one_story({"d": D1, "pkg": cut, "opening": {"picture": lw}})[0] == CON.FAIL      # cut whole, as promise_shot cuts: not the scene
    assert STORY.align({"thumb_prompt": "x", "thumb_prompt_b": lw + ", seen from far below"}, D1, {"picture": lw})["thumb_prompt_b"] == lw + "; seen from far below"      # (V1c finish, C9) a packager that repeats the scene keeps its other look
    assert STORY.align({"thumb_prompt": "x", "thumb_prompt_b": W}, D1, OPN)["thumb_prompt_b"] == W + "; " + STORY.OTHER_LOOK                                          # the scene alone: the other look is ours

def test_a_package_that_is_not_one_story_comes_back_as_it_came(story_on):
    def same(d, opn):
        pkg = {"thumb_prompt": "the packager's own scene", "thumb_prompt_b": "", "thumb_text": "UP"}; before = json.dumps(pkg, sort_keys=True)
        out = STORY.align(pkg, d, opn); return out is pkg and json.dumps(out, sort_keys=True) == before and "one_story" not in out
    assert same({"ladder": "OV1"}, OPN)                                                                     # under an override its own promise scene is drawn
    assert same(D1, {"short": "SH1", "picture": "  "}) and same(D1, {"none": "broken", "short": "SH1"}) and same(D1, None)      # a Short whose archive holds no picture words
    story_on("ONE_STORY_ON", "FALSE"); assert same(D1, OPN)                                                  # switched off

def test_check_one_story_both_ways(story_on, monkeypatch):
    from whatifs.org import registry as REG, rnd as RND
    import tools.repair as REP
    good = STORY.align({"thumb_prompt": "x", "thumb_prompt_b": "a pillow seen from below"}, D1, OPN)
    def chk(pkg=good, d=D1, opn=OPN): return CON.p_one_story({"d": d, "pkg": pkg, "opening": opn})
    assert chk() == (CON.PASS, f"the thumbnail is drawn from the first picture of Short SH1, the picture this video opens on: '{W}'")      # the archive's double space and line break are one space
    assert chk(dict(good, thumb_prompt_b=""))[0] == CON.PASS                                                 # no runner-up at all
    assert chk(dict(good, thumb_prompt="the packager's own scene")) == (CON.FAIL, "the thumbnail's scene is not the picture this video opens on")
    assert chk(dict(good, one_story={"short": "SH9", "words": W}))[0] == CON.FAIL and chk({k: v for k, v in good.items() if k != "one_story"})[0] == CON.FAIL
    assert chk(dict(good, thumb_prompt_b="a pillow on the moon")) == (CON.FAIL, "the runner-up thumbnail is not the opening's scene")
    assert chk(d={"ladder": "OV1"}) == (CON.NA, "made under an override: its own promise scene opens it (viewer_promise, promise_paid)")
    assert chk(opn={"short": "SH1", "picture": ""}) == (CON.NA, "the Short's archive holds no picture words")
    for kind in ("off", "none"):
        monkeypatch.setattr(OPEN_, "source", lambda d, k=kind: (k, None)); assert chk() == (CON.NA, OPEN_.none_words(kind))       # DESIGN QUESTION 22
    story_on("ONE_STORY_ON", "FALSE"); assert chk() == (CON.NA, "one story is switched off (ONE_STORY_ON)")
    assert {f[0]: f[1] for f in CON.FEATURES}["one_story"] == "script" and REG.check_owner("one_story") == "D5"
    assert "one_story" not in RND.ORG_CHECKS and "one_story" in RND.metrics() and "whatifs/story.py" in REP.PROTECTED

def test_the_opening_is_not_drawn_a_second_time():
    import inspect
    sp, pr = inspect.getsource(EP._stage_plan), inspect.getsource(EP.produce)
    assert sp.index("ROOM.package(room, chs, d, ep, opening=opn)") < sp.index("pkg = STORY.align(pkg, d, opn)") < sp.index("ROOM.plan_shots(room, su, d, plan, ep)")
    assert 'if not pkg.get("one_story"): shots = ROOM.promise_shot(shots, units, pkg)' in sp
    assert 'if not any(s_.get("promise") for s_ in shots) and not (S_.get("pkg") or {}).get("one_story"):' in pr

def test_the_rescue_swaps_to_a_runner_up_of_the_same_scene(story_on, monkeypatch, tmp_path):
    from tests import test_v85 as T85
    from whatifs import manage as MG, art as ART
    from PIL import Image
    pkg = STORY.align({"thumb_prompt": "a pillow on the moon", "thumb_prompt_b": "seen from far below", "thumb_text": "UP"}, D1, OPN); drawn = []      # (V1c finish, C9) another LOOK, never another scene
    def thumb(prompt, text, out_dir, ep, **kw):
        os.makedirs(out_dir, exist_ok=True); p = os.path.join(out_dir, "up.jpg"); Image.new("RGB", (64, 36)).save(p); drawn.append(prompt); return p, p, None
    monkeypatch.setattr(ART, "thumbnail", thumb); monkeypatch.setattr(QC, "check_thumb", lambda up, phone: (True, {}))
    b = EP._thumb_b(pkg, {}, _dir(tmp_path / "ep"), "EPRESC", False)
    assert b and drawn == [W + "; seen from far below"]                                                       # B is drawn from the opening's scene ...
    story_on("PKG_RESCUE_HOURS", "36")                                                                        # test_v85's timing (the shipped default is 72 h)
    calls = T85._fakes(monkeypatch, 40 * 20, tmp_path); T85._hist(3); T85._live("EPRESC", 40)
    monkeypatch.setattr(MG, "_fetch_some", lambda ep, a, names: {"release.json": str(tmp_path / "release.json"), "thumb_b.jpg": b})
    assert MG.pkg_rescue() == [("EPRESC", "swapped title + thumbnail")] and calls["thumb"] == [b]           # ... and the lagging video's swap sets exactly that picture

# ================================================================== STEP 6. THE SWEEP AND THE REHEARSAL WALK THE FLOOR, HIS LINE AND ONE STORY (3.10)
JUDGED = "two first-time viewers (gemini, claude) named this video over the rejected one in 4 of 4 looks; the rejected video beat its frozen picture"
GOOD_FLOOR = {"viewer_floor": (CON.PASS, JUDGED), "makers_line": (CON.PASS, "he gave no line for this topic: none is spoken, none is written"),
              "living_characters": (CON.PASS, "nobody is drawn without approved art"), "one_story": (CON.PASS, "the thumbnail is drawn from the first picture of Short SH1, the picture this video opens on: 'w'")}
OVERRIDE_NA = (CON.NA, "made under an override: its own promise scene opens it (viewer_promise, promise_paid)")

def _floor_case(ep, rows):
    core.store().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": ep, "stage": "final", "feature": k, "status": s, "evidence": e} for k, (s, e) in rows.items()])

def test_the_sweep_judges_the_floor_his_line_and_one_story_of_every_long_video():
    from tools import sweep as SW
    _floor_case("EPFL0", GOOD_FLOOR); ok, w = SW.floor_of(core, "EPFL0", climbed=True)
    assert ok and w.startswith("the floor judged: " + JUDGED) and "in 4 of 4 looks" in w, w                       # the looks won of 4 travel with the words
    _floor_case("EPFL1", dict(GOOD_FLOOR, viewer_floor=(CON.NA, "void by its canary: gemini did not put the rejected video above its own frozen picture")))
    ok, w = SW.floor_of(core, "EPFL1", climbed=True); assert ok and w.startswith("the floor was void by its canary: void by its canary"), w      # void: the film went to his eye
    _floor_case("EPFL2", dict(GOOD_FLOOR, one_story=OVERRIDE_NA)); assert SW.floor_of(core, "EPFL2", climbed=False)[0]                        # an override has no Short to be one story with
    bad = [("EPFB0", {"viewer_floor": (CON.FAIL, "ranked beside the rejected video: gemini named the new video in 1 of 2 looks")}, True),
           ("EPFB1", {"viewer_floor": (CON.NA, "the judged floor is switched off (VIEW_FLOOR_ON / VIEWER_SEAT_ON)")}, True),
           ("EPFB2", {"makers_line": (CON.NA, "the maker's line is switched off (MAKER_LINE_ON / OWNER_VERDICT_ON)")}, True),
           ("EPFB3", {"makers_line": (CON.FAIL, "his line is not in the description that is sent")}, True),
           ("EPFB4", {"living_characters": (CON.FAIL, "a cutaway to VALE's character in format F1, where nobody is on screen")}, True),
           ("EPFB5", {"one_story": (CON.NA, "the Short's archive holds no picture words")}, True),
           ("EPFB6", {"one_story": OVERRIDE_NA}, True),                                                          # an id that climbed must be ONE story
           ("EPFB7", {}, False)]                                                                                  # ... and one that did not, under an override
    for ep, change, climbed in bad:
        _floor_case(ep, dict(GOOD_FLOOR, **change)); ok, w = SW.floor_of(core, ep, climbed=climbed); assert not ok, (ep, w)
    _floor_case("EPFB8", {k: v for k, v in GOOD_FLOOR.items() if k != "makers_line"}); ok, w = SW.floor_of(core, "EPFB8", climbed=True)
    assert not ok and "makers_line missing" in w, w                                                                    # a missing row is a failure: the path was not walked
    _floor_case("EPFL3", dict(GOOD_FLOOR, viewer_floor=(CON.FAIL, "ranked beside the rejected video: x"))); _floor_case("EPFL3", GOOD_FLOOR)      # (V1c finish, C23)
    assert SW.floor_of(core, "EPFL3", climbed=True)[0]                                                              # the LATEST row of a check decides
    _floor_case("EPFL4", GOOD_FLOOR); _floor_case("EPFL4", {"makers_line": (CON.FAIL, "his line is not in the description that is sent")})
    ok, w = SW.floor_of(core, "EPFL4", climbed=True); assert not ok and "makers_line FAIL" in w, w
    s = SW.summary([{"id": "a", "outcome": "ok", "floor": "the floor judged: x"}, {"id": "b", "outcome": "odd", "floor": "the floor judged: x"},
                    {"id": "c", "outcome": "ok", "floor": "the floor was void by its canary: x"}, {"id": "d", "outcome": "ok"}])
    assert s["floor_judged"] == 1                                                                                      # the counter: judged AND the id good

def test_the_sweep_and_the_rehearsal_call_it_and_the_rehearsal_walks_his_verdict_his_line_and_the_flop():
    import inspect
    from tools import sweep as SW, rehearsal as RH
    swp = inspect.getsource(SW.one)
    assert swp.count('ok_f, res["floor"] = floor_of(core, ep, climbed=') == 2 and 'floor_of(core, ep, climbed=res.get("ladder") == "climbed")' in swp \
        and swp.index('ok_i, res["inside"] = inside_of(core, ep)') < swp.index('ok_f, res["floor"]')                    # the produce mode and the rehearsal mode, after inside_of
    src = inspect.getsource(RH.run)
    assert src.index('set_setting("OWNER_VERDICT_SINCE", (now_utc() - dt.timedelta(days=8))') < src.index("rs12 = SH12.run(") < src.index("VER1c.sync()") < src.index("r = EP.produce(slot, episode_id=epid)")
    assert '"I would keep it for one day, then beg for gravity back."' in src and '"Not for one hour."' in src and 'set_setting("OWNER_VERDICT_ASK_MAX_PER_DAY", "9")' in src
    assert 'f"LINE {ref1c} {line1c}"' in src and '.update("Owner_Verdicts"' not in src                               # his line through the second message's link (DESIGN QUESTION 25), never a write of the tab
    assert 'floor1c(core12, epid, climbed=True)' in src and 'FL1c.stand_in(os.path.join(work, "flop.mp4"), "flop")' in src and 'vf1c[1].startswith("ranked beside the rejected video")' in src
    assert 'vr1c[1].startswith("reported, not held: ranked beside the rejected video")' in src and src.index("vr1c = CON1c.p_viewer_floor(") < src.index('set_setting("VIEW_FLOOR_FAIL_HOLDS", "TRUE")') < src.index("vf1c = CON1c.p_viewer_floor(") < src.index('set_setting("VIEW_FLOOR_FAIL_HOLDS", "FALSE")')      # RULING_F10: both states, the default first, the cell put back
    assert 'VER1c._answer({"episode_id": epid}, f"VERDICT {epid} UP")' in src and 'VER1c.references(' in src and 'print("floor:"' in src
    assert 'FL1c.session("S-flop-" + epid, "flop", FL1c.stand_in(' in src                                                # (V1c finish, C21) the memo's own value: each rehearsal's flop walks its own blind order
    from whatifs import cta as CTA, maker as MK
    for line in ("I would keep it for one day, then beg for gravity back.", "Not for one hour."):
        assert MK.usable(line)[0] and CTA.kind_of_text(line) is None                                                    # neither is refused nor read as an ask by the older assert on the asks


# ---------------------------------------------------------------------------------------------------------------------------------------------------------
# V1c repair, red round 2 (open issue 228): the F2 rehearsal held one punchline short at the script gate (EP202611170305, the second pass on 46615df)
def _gate_narration(ep, hook, setting):
    """(V1c repair, red round 2) the narration the script gate measures in the F2 rehearsal, built by the production functions in the order room.py and
    episode.py run them after the writer's first draft: the stand-in's draft, the asks code adds (room._place_asks; CTA_LAST as room.py keeps it), the ONE
    mandatory fix (enforce.fix_all - the stand-in answers), the asks and the tease put back, the Short's hook put first (hooks.apply_to_script). Returns
    (narration, the fix's issues). Inside FMT.using("F2"), with the rehearsal's switches (_rehearsal_switches)."""
    from whatifs import enforce as EN, room as RM, hooks as HK, fakes as FK
    spine = {"promise": {"title": "What If Every Pillow Floated Away?", "thumb_text": "", "thumb_scene": "c", "first_30s": "p"}, "next_tease": {}}     # the rehearsal's (its plan.json)
    setting("CTA_LAST", "")
    s1, _, code = RM._place_asks(json.loads(FK.fake_reply("writer", "Write the narration.")), {}, ep); setting("CTA_LAST", code)
    fixed, issues = EN.fix_all(s1, "", spine, ep, "long")
    if issues:
        fixed = RM._place_asks(fixed, {}, ep)[0]
        fixed = RM.ensure_tease(fixed, spine["next_tease"], ep)
    return HK.apply_to_script(fixed.get("script", ""), hook)[0], issues

def _rehearsal_switches(monkeypatch, setting):
    from whatifs import fakes as FK
    monkeypatch.setattr(FK, "SMALL", True)                                    # the rehearsal and the sweep run small (tools/sweep.py sets WI_SMALL=1)
    for k in ("INSIDE_ON", "ENDINGS_ON", "LADDER_ON"): setting(k, core.DEFAULTS[k][0])       # the rehearsal's switches (conftest turns them off for the older tests)

def _short_hooks():
    """The first sentence of every offline Short format's first script: the line a promoted Short hands its long video (the ladder row's hook_line)."""
    from whatifs import fakes as FK
    return {s: FK._SHORT_FAKE[s][0][2][0][1].replace("{W}", "Shadow").replace("{w}", "shadow").split(". ")[0].rstrip(".") + "." for s in sorted(FK._SHORT_FAKE)}

def test_the_second_pass_red_id_passes_the_joke_check_on_the_narration_the_gate_measures(monkeypatch, setting):
    """(V1c repair, red round 2; open issue 228) EP202611170305 - the F2/S2 rehearsal the second pass on 46615df held at the script gate: the check
    joke_density, unchanged, on the narration the gate measures for that id ('6 punchlines (need 7); biggest gap 28 s' before the repair)."""
    _rehearsal_switches(monkeypatch, setting)
    with FMT.using("F2"):
        t, issues = _gate_narration("EP202611170305", _short_hooks()["S2"], setting)
        status, evidence = CON.p_joke_density({"room": {"script": {"script": t}}})
    assert issues and status == CON.PASS, (status, evidence)

def test_no_F2_rehearsal_id_comes_up_short_of_the_joke_rule_whatever_its_short(monkeypatch, setting):
    """(V1c repair, red round 2; open issue 228) THE SWEEP: 200 rehearsal ids (17 Nov 2026 from 00:00, one a minute - a rehearsal's id is the minute it
    starts) x the hook of every Short format: the narration the gate measures is never short of the joke rule by its own measures (enforce.joke_need,
    punch_lines, biggest_gap_lines, the check's 2.2 x JOKE_EVERY_SEC_LONG). Before the repair: with S2's hook 2 of 200 held (EP202611170113 and
    EP202611170305), with S1's and S3's 5 of 200 each."""
    import datetime as dt
    from whatifs import enforce as EN
    _rehearsal_switches(monkeypatch, setting)
    ids = [(dt.datetime(2026, 11, 17) + dt.timedelta(minutes=i)).strftime("EP%Y%m%d%H%M") for i in range(200)]
    held, walked = [], 0
    with FMT.using("F2"):
        for s, hook in _short_hooks().items():
            for ep in ids:
                t, issues = _gate_narration(ep, hook, setting); walked += bool(issues)
                if len(EN.punch_lines(t)) < EN.joke_need(t) or EN.biggest_gap_lines(t) > 2.2 * S("JOKE_EVERY_SEC_LONG", float): held.append((s, ep))
    assert walked == len(ids) * len(_short_hooks()), walked           # the ONE mandatory fix is walked on every id (the road on which the stand-in answers)
    assert held == [], (len(held), held[:10])
