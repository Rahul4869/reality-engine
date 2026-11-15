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

# ================================================================== STEP 1 - THE JUDGED FLOOR (the memo's 3.1)
from whatifs.org import floor as FL
from whatifs import models as M, notify as NT, fakes as FK
OWN_IDS = ("EP209910010900", "EP209910080900", "EP209910150900", "EP209910220900")      # the whole productions of this file: ids no other test file uses (a test proves it)

@pytest.fixture
def floor_on(setting):
    setting("VIEW_FLOOR_ON", "TRUE"); yield setting

def test_the_older_tests_run_with_the_floor_off():
    from tests.conftest import OLD_VIEW
    assert OLD_VIEW["VIEW_FLOOR_ON"] == "FALSE" and core.DEFAULTS["VIEW_FLOOR_ON"][0] == "TRUE" and FL.on() is False
    assert {k: core.DEFAULTS[k][0] for k in ("VIEW_FLOOR_WATCH_S", "VIEW_FLOOR_EST_INR", "VIEW_FLOOR_CAP_PER_VIDEO_INR", "VIEW_FLOOR_MAX_PER_VIDEO", "VIEW_FLOOR_CANARY",
            "VIEW_FLOOR_EYE_WAIT_H")} == {"VIEW_FLOOR_WATCH_S": "60", "VIEW_FLOOR_EST_INR": "40", "VIEW_FLOOR_CAP_PER_VIDEO_INR": "75", "VIEW_FLOOR_MAX_PER_VIDEO": "2",
                                          "VIEW_FLOOR_CANARY": "", "VIEW_FLOOR_EYE_WAIT_H": "20"}
    assert (FL.LOOKS, FL.EVERY_S, FL.THINK, FK.WATCH_CHANGE, FK.WATCH_MARGIN) == (2, 2, 8000, 0.5, 10)

@pytest.fixture(scope="module")
def media(tmp_path_factory):
    """The stand-in for the rejected video (seed canary), its frozen twin, a flop (seed flop) and an offline film that moves (made once for the module)."""
    d = tmp_path_factory.mktemp("floor_media")
    can = FL.stand_in(str(d / "canary.mp4"), "canary"); tw = FL.twin(can, str(d / "canary_twin")); flop = FL.stand_in(str(d / "flop.mp4"), "flop")
    src = str(d / "film_src.mp4")
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=12", "-f", "lavfi", "-i", "sine=frequency=220:duration=60", "-t", "60",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", src], check=True, capture_output=True)
    film = FL.view(src, str(d / "film"), 60.0)                                              # (no Settings read here: a module fixture runs before the test's own store)
    return {"canary": can, "twin": tw, "flop": flop, "film": film, "src": src, "dir": str(d)}

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

def test_the_cost_row_of_a_look_carries_the_task_and_the_month_cap_closes_on_it(real, floor_on):
    from whatifs import governor as G
    use, views = real; use([_gem(GOOD)])
    M.ask_watch("floor_gemini", "s", "p", views, waits=(0, 0)); core.flush_costs()
    row = [r for r in core.store().rows("Cost_Log") if r.get("item") == "gemini_pro"][-1]
    assert row["role"] == "floor_gemini" and G.month_spend_of(["floor_gemini", "floor_claude"]) > 0
    core.set_setting("VIEW_FLOOR_CAP_PER_VIDEO_INR", "0")
    r = FL.plain(FL.run(None, "EPCAP", "x.mp4", "/nonexistent", (), ()))
    assert r["status"] == "void" and r["why"].startswith("the month's floor money is spent")

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

def test_the_floorkit_branch_files_the_kit_and_tells_him_once(floor_on, monkeypatch, media):
    import sys
    from whatifs import cli
    monkeypatch.setattr(sys, "argv", ["cli", "floorkit", media["canary"]["clip"], "abc123"])
    cli.main(); cli.main()
    k = json.loads(S("VIEW_FLOOR_CANARY")); assert k["yt"] == "abc123"
    n = [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"]
    assert len(n) == 1 and k["sha"][:8] in n[0]["text"] and "stop sharing" in n[0]["text"]

def test_check_viewer_floor_says_and_recomputes(floor_on, media):
    r = _session(media, "S-check")
    assert CON.p_viewer_floor({"floor": r}) == (CON.PASS, r["why"])
    bad = dict(r, status="fail", why="ranked beside the rejected video: nobody")
    assert CON.p_viewer_floor({"floor": bad}) == (CON.FAIL, "the stored verdict is not the code's verdict on its own looks")
    assert CON.p_viewer_floor({}) == (CON.NA, "not judged: the measured checks come first, and a film they hold is not paid a jury")
    assert CON.p_viewer_floor({"floor": {"status": "void", "why": "void by its canary: x"}}) == (CON.NA, "void by its canary: x")
    core.set_setting("VIEW_FLOOR_ON", "FALSE"); assert CON.p_viewer_floor({"floor": r})[1].startswith("the judged floor is switched off")

def test_with_the_organisation_off_the_result_is_the_same_dict(floor_on, media, tmp_path):
    from whatifs.org import runner as ORG
    core.set_setting("ORG_ON", "FALSE")
    x = ORG.work("D13", "floor", "EPOFF", lambda b: FL.run(b, "EPOFF", media["src"], str(tmp_path), (), ()))
    assert isinstance(x, ORG.Out) and isinstance(FL.plain(x), dict) and FL.plain(x)["status"] in ("pass", "fail", "void")

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

# ------------------------------------------------------------------ whole productions (ids no other test file uses)
def test_the_whole_productions_of_this_file_use_ids_no_other_test_file_uses():
    root = os.path.dirname(os.path.abspath(__file__)); here = os.path.basename(__file__)
    for f in os.listdir(root):
        if f.endswith(".py") and f != here:
            t = open(os.path.join(root, f), encoding="utf-8").read()
            for i in OWN_IDS: assert i not in t, (f, i)

def _start_e2e(monkeypatch, setting):
    from tests import test_v12_inside as INS_T
    INS_T._start(monkeypatch, setting, "F1"); setting("VIEW_FLOOR_ON", "TRUE")

def _led(ep): return {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep and x.get("stage") == "final"}

def test_a_whole_production_passes_the_floor_with_two_looks_of_each_judge(monkeypatch, setting):
    from tests import test_v12_opening_e2e as E2E
    from tests.paid_calls import watch
    _start_e2e(monkeypatch, setting); c = watch(monkeypatch); ep = OWN_IDS[0]
    r = EP.produce(E2E._slot(10), episode_id=ep); led = _led(ep)
    assert r.get("ok"), r
    assert led["viewer_floor"][0] == CON.PASS and led["viewer_floor"][1].startswith("two first-time viewers (gemini, claude) named this video over the rejected one in 4 of 4 looks")
    assert c["watch:floor_gemini"] == 2 and c["watch:floor_claude"] == 2
    rows = [x for x in core.store().rows("Floor_Log") if x["episode_id"] == ep]
    assert len(rows) == 4 and {x["view"] for x in rows} == {f"{ep}_view.mp4"}

@pytest.mark.parametrize("org", ["TRUE", "FALSE"])
def test_a_flop_like_film_is_held_by_the_floor_alone_with_its_own_card(monkeypatch, setting, org, media):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import publish as PUB
    _start_e2e(monkeypatch, setting); setting("ORG_ON", org); ep = OWN_IDS[1] if org == "TRUE" else OWN_IDS[2]
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, *a, **k: (mails.append(str(subject)), True)[1])
    real_view = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, s: FL.stand_in(os.path.join(os.path.dirname(base), "flop.mp4"), "flop") if base.endswith(os.sep + "new") else real_view(src, base, s))
    r = EP.produce(E2E._slot(10), episode_id=ep); led = _led(ep)
    assert not r.get("ok") and r.get("held") and [k for k, v in led.items() if v[0] == CON.FAIL] == ["viewer_floor"], led
    assert led["viewer_floor"][1].startswith("ranked beside the rejected video: ")
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)
    assert e["status"] == "HOLD_QC" and not e.get("yt_id")
    cards = [x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    assert [x["kind"] for x in cards] == ["floor_hold"] and f"https://drive.google.com/file/d/{ep}_view.mp4/view" in cards[0]["text"]
    assert not [m for m in mails if m.startswith("Video held")], mails                       # one hold, ONE message: no "one click to fix" mail beside the card

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
