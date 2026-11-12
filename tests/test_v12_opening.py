"""v12 V2c-b2b1 THE OPENING: a long video about a promoted Short opens on that Short's kept footage - the window (how an upright clip is shown in a
wide frame), the laying (pure), the marks on the shot list, the fetched archive, the cut files, the proven first line, the Animation Director's
three scenes, and both checks (before picture money and on the finished film). Each rule both ways. No keys, no network."""
import json, os, subprocess, zipfile
import pytest
from whatifs import core, opening as OPEN, ladder as LAD, publish as PUB, hooks as HOOKS, anim as ANIM, contract as CON, episode as EP, room as ROOM, render as RN, release as REL

SID = "SH209912010900"
TRACK = [{"clip": "c0.mp4", "start": 0.0, "end": 5.8, "slow": 1.16}, {"clip": "c1.mp4", "start": 5.8, "end": 11.2, "slow": 1.08}, {"clip": "c2.mp4", "start": 11.2, "end": 17.2, "slow": 1.2}]
STARTS = (0.2, 2.0, 4.5, 7.0, 12.0, 16.5, 19.0, 24.0, 31.0, 40.0)

def _man(sid=SID, w=720, h=1280):
    return {"short": sid, "footage": sid + "_footage.zip", "hook": "Your shadow just left without you.", "seconds": 17.2,
            "clips": {f"c{i}.mp4": {"sha": "x" * 8 + str(i), "w": w, "h": h, "sec": 5.0} for i in range(3)}, "track": [dict(t) for t in TRACK]}

def _units(starts=STARTS, end=48.0):
    return [{"i": i, "start": s, "end": (starts[i + 1] if i + 1 < len(starts) else end) - 0.1, "text": f"Sentence {i} of the long video.", "tag": "none"} for i, s in enumerate(starts)]

def _shots(n=len(STARTS)):
    out = [{"type": "still", "prompt": f"picture {i}", "unit": i} for i in range(n)]
    out[1].update(type="graphic", graphic={"label": "x"}); out[3].update(type="kling", promise=True); return out

def _ladder(sid=SID, footage=None, state="PROMOTED"):
    rec = {"ts": core.iso(), "id": sid, "kind": "short", "title": "T", "format": "S1", "yt_id": "yt" + sid, "status": "POSTED", "made": core.iso(), "premise": "What if your shadow left?"}
    core.store().append("Specials", [rec]); LAD.enter(rec, None, footage=sid + "_footage.zip" if footage is None else footage)
    core.store().update("Ladder", "id", sid, {"state": state, "promoted_at": core.iso()})
    return {"ladder": sid}

def _clip(path, w, h, sec=5.0, src="testsrc2"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"{src}=size={w}x{h}:rate=30", "-t", f"{sec}", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", path], check=True)
    return path

def _archive(tmp, sid=SID, w=180, h=320, names_id=None, extra=()):
    """A Short's footage archive in the offline Drive, built the way ladder.keep builds it: three upright clips that MOVE, their start pictures, short.json."""
    wd = os.path.join(str(tmp), "mk" + sid); os.makedirs(wd, exist_ok=True)
    plan = {"shots": [{"i": i, "beat": i, "type": "kling", "src": "picture", "start": t["start"], "end": t["end"], "picture": f"beat {i}"} for i, t in enumerate(TRACK)]
            + [{"i": 3, "beat": 3, "type": "kling", "src": "loop", "loop": True, "start": 17.2, "end": 21.0, "picture": "beat 0"}], "seconds": 21.0}
    meta = {"id": names_id or sid, "script": {"title": "T"}, "plan": plan, "timeline": {"units": [{"text": "[tension] Your shadow just left without you.", "start": 0.1, "end": 2.2}, {"text": "It is not coming back.", "start": 2.5, "end": 4.0}]}}
    z = os.path.join(PUB._fake_drive(), sid + "_footage.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as f:
        for i in range(3):
            f.write(_clip(os.path.join(wd, f"c{i}.mp4"), w, h, 5.0, ("testsrc2", "testsrc", "smptebars")[i]), f"c{i}.mp4"); f.writestr(f"f{i}.png", b"png")
        f.writestr("short.json", json.dumps(meta))
        for n in extra: f.writestr(n, b"not ours")
    return sid + "_footage.zip"

# ------------------------------------------------------------------ 1. the window
def test_the_window_is_as_wide_as_the_clips_sharpness_allows(setting):
    f = OPEN.fit(720, 1280, 1920, 1080)                                                            # a clip 720 wide, enlarged at most 2.0 times: a 4:3 window over three quarters of the frame
    assert (f["mode"], f["crop"], f["show"], f["enlarge"], f["ground"]) == ("auto", [720, 540], [1440, 1080], 2.0, True) and f["kept"] == round(540 / 1280, 3)
    assert OPEN.fit(1080, 1920, 1920, 1080)["show"] == [1920, 1080] and OPEN.fit(1080, 1920, 1920, 1080)["ground"] is False and OPEN.fit(1080, 1920, 1920, 1080)["enlarge"] <= 2.0      # a sharper clip fills the frame
    setting("OPENING_ENLARGE_MAX", "1.5"); assert OPEN.fit(720, 1280, 1920, 1080)["show"] == [1080, 1080] and OPEN.fit(720, 1280, 1920, 1080)["enlarge"] == 1.5      # the lever narrows it
    setting("OPENING_ENLARGE_MAX", "3"); assert OPEN.fit(720, 1280, 1920, 1080)["ground"] is False                                                   # and widens it
    setting("OPENING_ENLARGE_MAX", "2.0")
    fill, whole = OPEN.fit(720, 1280, 1920, 1080, "fill"), OPEN.fit(720, 1280, 1920, 1080, "whole")
    assert fill["show"] == [1920, 1080] and fill["ground"] is False and 2.6 < fill["enlarge"] < 2.7 and 0.31 < fill["kept"] < 0.33      # the frame filled: a third of the picture, enlarged 2.67 times
    assert whole["crop"] == [720, 1280] and whole["kept"] == 1.0 and whole["enlarge"] < 1 and whole["show"][0] in (606, 608) and whole["ground"] is True      # the whole clip: nothing lost, nothing enlarged
    setting("OPENING_FIT", "whole"); assert OPEN.fit(720, 1280, 1920, 1080)["mode"] == "whole" and OPEN.fit(720, 1280, 1920, 1080)["kept"] == 1.0   # the setting decides
    setting("OPENING_FIT", "sideways"); assert OPEN.fit(720, 1280, 1920, 1080)["mode"] == "auto"                                                   # an unknown word is the safe default
    wide = OPEN.fit(2560, 1080, 1920, 1080); assert wide["crop"] == [1920, 1080] and wide["ground"] is False and wide["enlarge"] == 1.0            # a clip wider than the frame only loses its sides

# ------------------------------------------------------------------ 2. the laying and the marks
def test_the_track_is_laid_under_the_first_sentences_and_ends_inside_the_footage(setting):
    lay = OPEN.lay(_units(), _man())
    assert sorted(lay) == [0, 1, 2, 3, 4]                                                          # sentence 5 ends at 19.0 s, after the 17.2 s of footage: the opening ends before it
    assert lay[0] == [["c0.mp4", 0.0, round(2.0 / 1.16, 3), 1.16]]                                 # the first picture starts at second 0 (not at the first word)
    assert lay[2] == [["c0.mp4", round(4.5 / 1.16, 3), 5.0, 1.16], ["c1.mp4", 0.0, round(1.2 / 1.08, 3), 1.08]]      # a sentence crosses from one clip into the next, each slowed as the Short played it
    assert lay[4][-1] == ["c2.mp4", round(0.8 / 1.2, 3), round(5.3 / 1.2, 3), 1.2] and OPEN.lay(_units(), _man()) == lay      # pure: the same answer twice
    setting("OPENING_SHORT_MAX_S", "8"); assert sorted(OPEN.lay(_units(), _man())) == [0, 1, 2]    # the ceiling binds
    setting("OPENING_SHORT_MAX_S", "40")
    assert OPEN.lay(_units(), {"none": "missing"}) == {} and OPEN.lay([], _man()) == {} and OPEN.lay(_units((0.2, 30.0)), _man()) == {}      # no footage, no sentences, a first sentence longer than the footage

def test_the_marks_carry_the_footage_and_marking_twice_changes_nothing(setting):
    u, m = _units(), _man(); s1 = OPEN.mark(_shots(), u, m)
    assert OPEN.marked(s1) == [0, 1, 2, 3, 4] and all(s1[i]["type"] == "kling" and s1[i]["short"]["id"] == SID for i in range(5)) and s1[5]["type"] == "still"
    assert s1[0]["promise"] is True and [i for i, s in enumerate(s1) if s.get("promise")] == [0] and "graphic" not in s1[1]      # the promise is the Short's first picture; a number graphic under the footage is gone
    assert OPEN.mark(s1, u, m) == s1 and json.loads(json.dumps(OPEN.mark(json.loads(json.dumps(s1)), u, m))) == json.loads(json.dumps(s1))      # idempotent, also across a saved plan
    gone = OPEN.mark(s1, u, {"none": "missing", "short": SID})
    assert not OPEN.marked(gone) and all(gone[i]["type"] == "still" and "promise" not in gone[i] for i in range(5))                      # the footage is gone: no shot keeps a mark it cannot pay for
    assert _shots()[3]["type"] == "kling" and "short" not in _shots()[0]                                                                # the input list was not changed

# ------------------------------------------------------------------ 3. check opening_footage: the shot list, before any picture is paid
def test_opening_footage_passes_only_on_this_shorts_footage_laid_as_the_rule_says(setting):
    setting("LADDER_ON", "TRUE"); d = _ladder(); u, m = _units(), _man(); good = OPEN.mark(_shots(), u, m)
    ok, why = OPEN.plan_report(d, good, u, m); assert ok is True and "14.9" not in why and "16.5 s" in why and SID in why and "5 shots from 3 of its 3 clips" in why, why
    def bad(shots=good, man=m, dd=d): return OPEN.plan_report(dd, shots, u, man)
    assert bad(man={"none": "missing", "short": SID, "why": "the footage of Short X was not kept"})[0] is False and "other pictures" in bad(man={"none": "missing", "short": SID, "why": "w"})[1]
    assert bad(man=None)[0] is False and bad(man=dict(m, short="SH1"))[0] is False                                                       # no manifest; the manifest of another Short
    assert bad(man=dict(m, footage="another.zip"))[0] is False and "not the archive" in bad(man=dict(m, footage="another.zip"))[1]       # another archive than the ladder row names
    plain = _shots(); assert bad(shots=plain)[0] is False and "opens on a still" in bad(shots=plain)[1]                                  # the video opens with its own pictures
    first = [dict(s) for s in good]; first[0].pop("short"); first[0]["type"] = "still"; assert bad(shots=first)[0] is False              # ... also when only the FIRST shot is its own
    demoted = [dict(s) for s in good]; demoted[2]["type"] = "still"; assert bad(shots=demoted)[0] is False and "planned as a still" in bad(shots=demoted)[1]
    alien = [dict(s) for s in good]; alien[1] = dict(alien[1], short=dict(alien[1]["short"], id="SH999")); assert bad(shots=alien)[0] is False and "another Short" in bad(shots=alien)[1]
    moved = [dict(s) for s in good]; moved[4] = dict(moved[4], short={"id": SID, "parts": [["c0.mp4", 0.0, 3.0, 1.0]]}); assert bad(shots=moved)[0] is False and "not laid as the rule says" in bad(shots=moved)[1]
    fewer = [dict(s) for s in good]; fewer[4].pop("short"); assert bad(shots=fewer)[0] is False                                         # a covered sentence shows another picture
    more = [dict(s) for s in good]; more[5] = dict(more[5], type="kling", short={"id": SID, "parts": [["c2.mp4", 4.0, 5.0, 1.2]]}); assert bad(shots=more)[0] is False
    long_first = _units((0.2, 30.0, 40.0, 44.0)); r = OPEN.plan_report(d, OPEN.mark(_shots(4), long_first, m), long_first, m)
    assert r[0] is False and "first sentence" in r[1], r                                                                                 # a first sentence longer than the whole footage: nothing can be laid

def test_an_override_has_no_footage_and_both_checks_say_so(setting):
    setting("LADDER_ON", "TRUE"); o = LAD.override("owner", "make it anyway"); d = {"ladder": o["id"]}
    for ok, why in (OPEN.plan_report(d, _shots(), _units(), {"none": "override"}), OPEN.shown_report(d, _shots(), _units(), {}, "no.mp4")):
        assert ok is None and o["id"] in why and "no Short and no footage" in why and "viewer_promise" in why
    assert OPEN.fetch(d, core.WORK)["none"] == "override" and OPEN.proven(OPEN.fetch(d, core.WORK)) is None
    assert CON.p_opening_footage({"d": d, "shots": _shots(), "units": _units()})[0] == CON.NA and CON.p_opening_shown({"d": d, "shots": _shots(), "units": _units()})[0] == CON.NA
    assert OPEN.plan_report({"ladder": ""}, _shots(), _units(), None)[0] is None and "topic_ladder" in OPEN.plan_report({"ladder": "SH404"}, _shots(), _units(), None)[1]      # no ladder row: topic_ladder judges that
    d2 = _ladder(); assert OPEN.source(d2)[0] == "short"
    setting("OPENING_SHORT_ON", "FALSE"); assert OPEN.source(d2)[0] == "off" and OPEN.plan_report(d2, _shots(), _units(), None)[0] is None and OPEN.fetch(d2, core.WORK)["none"] == "off"
    setting("OPENING_SHORT_ON", "TRUE"); setting("LADDER_ON", "FALSE"); assert OPEN.source(d2)[0] == "off"                               # no ladder, no Short to open on

# ------------------------------------------------------------------ 4. the archive
def test_the_footage_is_fetched_measured_and_an_archive_of_another_short_is_refused(tmp_path, monkeypatch, setting):
    setting("LADDER_ON", "TRUE"); d = _ladder(); fid = _archive(tmp_path, extra=("notes.txt", "../evil.txt", "c9.mp4.exe")); out = os.path.join(str(tmp_path), "ep"); os.makedirs(out)
    m = OPEN.fetch(d, out)
    assert m["short"] == SID and m["footage"] == fid and m["hook"] == "Your shadow just left without you." and m["seconds"] == 17.2       # the hook is the Short's first sentence as its voice spoke it (no delivery tag)
    assert sorted(m["clips"]) == ["c0.mp4", "c1.mp4", "c2.mp4"] and all(c["w"] == 180 and c["h"] == 320 and 4.9 <= c["sec"] <= 5.1 and len(c["sha"]) == 64 for c in m["clips"].values())
    assert [t["clip"] for t in m["track"]] == ["c0.mp4", "c1.mp4", "c2.mp4"] and [t["slow"] for t in m["track"]] == [1.16, 1.08, 1.2]      # slowed exactly as the Short played each clip; the loop shot is not footage
    wd = os.path.join(out, OPEN.DIR); assert sorted(os.listdir(wd)) == ["c0.mp4", "c1.mp4", "c2.mp4", "f0.png", "f1.png", "f2.png", "short.json"] and not os.path.exists(os.path.join(str(tmp_path), "evil.txt"))
    assert OPEN.proven(m) == {"line": "Your shadow just left without you.", "short": SID}
    setting("OPENING_HOOK_ON", "FALSE"); assert OPEN.proven(m) is None; setting("OPENING_HOOK_ON", "TRUE")
    calls = []; real = PUB.drive_download; monkeypatch.setattr(PUB, "drive_download", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    assert OPEN.fetch(d, out) == m and not calls                                                                                        # already here: not downloaded twice
    d2 = _ladder("SH209912020900", footage=_archive(tmp_path, "SH209912020900", names_id="SH_OTHER")); o2 = os.path.join(str(tmp_path), "ep2"); os.makedirs(o2)
    r2 = OPEN.fetch(d2, o2); assert r2["none"] == "broken" and "SH_OTHER" in r2["why"] and OPEN.proven(r2) is None                         # the archive on the row is another Short's footage
    d3 = _ladder("SH209912030900", footage=""); r3 = OPEN.fetch(d3, o2); assert r3["none"] == "missing" and "not kept" in r3["why"]       # nothing was kept when the Short was made
    d4 = _ladder("SH209912040900", footage="nowhere.zip"); r4 = OPEN.fetch(d4, os.path.join(str(tmp_path), "ep4")); assert r4["none"] == "broken" and "could not be read" in r4["why"]      # Drive has no such file: never a crash
    os.remove(os.path.join(wd, "c1.mp4")); os.remove(os.path.join(wd, "short.json")); z = zipfile.ZipFile(os.path.join(PUB._fake_drive(), fid)); keep = {n: z.read(n) for n in z.namelist() if n != "c1.mp4"}; z.close()
    with zipfile.ZipFile(os.path.join(PUB._fake_drive(), fid), "w") as f:
        for n, b in keep.items(): f.writestr(n, b)
    r5 = OPEN.fetch(d, out); assert r5["none"] == "broken" and "c1.mp4" in r5["why"]                                                    # a clip of the plan is missing from the archive

# ------------------------------------------------------------------ 5. the cut files
def _cut(tmp_path, setting, w=180, h=320, fitmode=None):
    setting("LADDER_ON", "TRUE")
    if fitmode: setting("OPENING_FIT", fitmode)
    d = _ladder(); _archive(tmp_path, w=w, h=h); out = os.path.join(str(tmp_path), "ep"); os.makedirs(out, exist_ok=True)
    m = OPEN.fetch(d, out); u = _units(); shots = OPEN.mark(_shots(), u, m)
    return d, m, u, shots, out, OPEN.cut(shots, u, out, m)

def test_every_opening_shot_gets_its_own_clip_as_long_as_its_sentence_through_the_window(tmp_path, setting):
    d, m, u, shots, out, oc = _cut(tmp_path, setting); W, H = RN.out_size(); b = OPEN.bounds(u)
    assert sorted(oc["clips"]) == sorted(oc["img"]) == [0, 1, 2, 3, 4] and oc["opening"]["short"] == SID and oc["opening"]["footage"] == m["footage"]
    for i in range(5):
        pr = REL.probe(oc["clips"][i]); assert (pr["w"], pr["h"]) == (W, H) and abs(pr["sec"] - (b[i + 1] - b[i])) <= 0.07, (i, pr)     # the frame's size, the sentence's length: the renderer plays it whole
        assert os.path.basename(oc["clips"][i]) == f"clip{i:03d}.mp4" and os.path.exists(oc["img"][i]) and oc["opening"]["units"][str(i)]["sha"] == REL.sha(oc["clips"][i])
        assert oc["opening"]["units"][str(i)]["parts"] == shots[i]["short"]["parts"]
    import numpy as np
    for i in (0, 1):                                                                                # slowed as the Short played it: the clip MOVES to its last frame (played at its own speed it would end early and freeze)
        dur = b[i + 1] - b[i]; x, y = OPEN._frame(oc["clips"][i], dur - 0.30), OPEN._frame(oc["clips"][i], dur - 0.07)
        assert float(np.abs(x.astype(int) - y.astype(int)).mean()) > 0.2, i
    f = oc["opening"]["fit"]; want = OPEN.fit(180, 320, W, H); assert f["show"] == want["show"] and f["enlarge"] == want["enlarge"] and f["ground"] is True
    import cv2
    fr = OPEN._frame(oc["clips"][0], 1.0); g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY); side = (W - f["show"][0]) // 2; assert side > 20
    sharp = lambda a: float(cv2.Laplacian(a, cv2.CV_64F).var())
    assert sharp(g[:, : side - 4]) < 0.25 * sharp(g[:, side + 4: W - side - 4])                                                          # beside the window lies the blurred copy, never a second sharp picture - and never black
    assert float(g[:, : side - 4].mean()) > 8
    assert OPEN.m_cut(oc) == {"opening_shots": 5, "opening_s": round(b[5], 1), "opening_enlarge": f["enlarge"]} and OPEN.m_cut({}) == {"opening_shots": 0, "opening_s": 0, "opening_enlarge": 0}

def test_the_whole_clip_and_the_filled_frame_are_the_two_ends_of_one_window(tmp_path, setting):
    d, m, u, shots, out, oc = _cut(tmp_path, setting, fitmode="fill"); W, H = RN.out_size()
    assert oc["opening"]["fit"]["ground"] is False and oc["opening"]["fit"]["show"] == [W, H] and REL.probe(oc["clips"][0])["w"] == W    # filled: no ground
    mid = oc["opening"]["units"]["0"]["sha"]; setting("OPENING_WINDOW_Y", "0"); top = OPEN.cut(shots, u, out, m)["opening"]["units"]["0"]["sha"]
    setting("OPENING_WINDOW_Y", "1"); low = OPEN.cut(shots, u, out, m)["opening"]["units"]["0"]["sha"]; assert len({mid, top, low}) == 3      # the window sits where OPENING_WINDOW_Y says: top, middle, bottom
    setting("OPENING_WINDOW_Y", "0.5"); setting("OPENING_FIT", "whole"); oc2 = OPEN.cut(shots, u, out, m)
    assert oc2["opening"]["fit"]["kept"] == 1.0 and oc2["opening"]["fit"]["ground"] is True and oc2["opening"]["units"]["0"]["sha"] != oc["opening"]["units"]["0"]["sha"]      # another window, another file

def test_a_restored_clip_is_kept_and_a_shot_that_cannot_be_cut_stops_before_anything_is_paid(tmp_path, monkeypatch, setting):
    import whatifs.media as MD
    d, m, u, shots, out, oc = _cut(tmp_path, setting); have = {"opening": oc["opening"]}
    runs = []; real = subprocess.run; monkeypatch.setattr(OPEN.subprocess, "run", lambda *a, **k: (runs.append(1), real(*a, **k))[1])
    again = OPEN.cut(shots, u, out, m, have); assert not runs and again["opening"]["units"] == oc["opening"]["units"]                    # a resume cuts nothing again: hash and parts are the recorded ones
    with open(oc["clips"][2], "ab") as f: f.write(b"x")
    OPEN.cut(shots, u, out, m, have); assert len(runs) == 1                                                                              # a file that changed is cut again
    other = dict(have["opening"], short="SH_OTHER"); n0 = len(runs); OPEN.cut(shots, u, out, m, {"opening": other}); assert len(runs) == n0 + 5      # the record of another Short proves nothing
    assert OPEN.cut(_shots(), u, out, m) == {}                                                                                          # no marked shot, nothing to do
    state = EP._assets_state(dict(oc, anchors=[], urls={})); assert state["opening"] == oc["opening"]                                    # the opening's record travels with the assets checkpoint ...
    with open(os.path.join(out, "assets.json"), "w") as f: json.dump(state, f)
    back = EP._load_assets(out); assert back["opening"] == oc["opening"] and sorted(back["clips"]) == [0, 1, 2, 3, 4]                     # ... and comes back with it
    paid = []; monkeypatch.setattr(MD, "still", lambda *a, **k: paid.append("still")); monkeypatch.setattr(MD, "animate", lambda *a, **k: paid.append("clip"))
    os.remove(os.path.join(out, OPEN.DIR, "c1.mp4"))
    with pytest.raises(RuntimeError, match="nothing is paid"): EP._assets(shots, u, out, "EPX", budget=20, footage=m)                    # the assets stage stops BEFORE it would buy another picture for the shot
    with pytest.raises(RuntimeError, match="nothing is paid"): EP._assets(shots, u, out, "EPX", budget=20, footage={"none": "broken"})
    named = [dict(s) for s in shots]; named[0] = dict(named[0], short={"id": SID, "parts": [["c9.mp4", 0.0, 2.0, 1.0]]})
    with pytest.raises(RuntimeError, match="nothing is paid"): EP._assets(named, u, out, "EPX", budget=20, footage=m)                   # a shot that names a clip the archive never held
    assert not paid

# ------------------------------------------------------------------ 6. check opening_shown: the finished film
def _film(out, clips, tail, grade="eq=brightness=-0.10:contrast=1.15,vignette=PI/3.5"):
    W, H = RN.out_size(); ins = []
    for c in clips: ins += ["-i", c]
    filt = "".join(f"[{k}:v]scale={W}:{H},setsar=1,fps={RN.fps()},format=yuv420p[v{k}];" for k in range(len(clips))) + "".join(f"[v{k}]" for k in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0,{grade}[o]"
    p = os.path.join(out, "master.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", filt, "-map", "[o]", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", p], check=True); return p

def test_the_finished_film_is_compared_with_the_footage_it_must_show(tmp_path, setting):
    d, m, u, shots, out, oc = _cut(tmp_path, setting); rec = oc["opening"]; own = _clip(os.path.join(str(tmp_path), "own.mp4"), *RN.out_size(), 6.0, "mandelbrot")
    clips = [oc["clips"][i] for i in range(5)]; master = _film(out, clips + [own], None)
    ok, why = OPEN.shown_report(d, shots, u, rec, master); assert ok is True and "16.5 s" in why and "5 shots" in why and "frames of the finished film compared" in why, why      # graded darker with a vignette: still recognised
    assert int(why.split(" frames")[0].split()[-1]) >= 25, why                                                                           # compared about every half second: a one-second effect cannot fall between two looks
    b = OPEN.bounds(u); o1, o2 = (_clip(os.path.join(str(tmp_path), f"own{i}.mp4"), *RN.out_size(), b[i + 1] - b[i], "mandelbrot") for i in (1, 2))      # other pictures, exactly as long as the sentences they replace
    swapped = _film(out, [clips[0], o1, o2] + clips[3:] + [own], None)
    ok2, why2 = OPEN.shown_report(d, shots, u, rec, swapped); assert ok2 is False and "does not show the footage" in why2, why2          # the film shows OTHER pictures under the second sentence
    at = float(why2.split("at ")[1].split(" s")[0]); assert b[1] <= at <= b[3], why2                                                     # ... and the check names when
    master = _film(out, clips + [own], None)
    plain = _shots(); assert OPEN.shown_report(d, plain, u, rec, master)[0] is False and "first shot" in OPEN.shown_report(d, plain, u, rec, master)[1]      # the shot list opens on its own picture
    assert OPEN.shown_report(d, shots, u, {}, master)[0] is False and OPEN.shown_report(d, shots, u, dict(rec, short="SH1"), master)[0] is False            # nothing on record; the record of another Short
    assert OPEN.shown_report(d, shots, u, rec, os.path.join(out, "none.mp4"))[0] is False
    moved = [dict(s) for s in shots]; moved[3] = dict(moved[3], short={"id": SID, "parts": [["c0.mp4", 0.0, 1.0, 1.0]]}); assert "other stretches" in OPEN.shown_report(d, moved, u, rec, master)[1]
    with open(clips[1], "ab") as f: f.write(b"x")
    ok3, why3 = OPEN.shown_report(d, shots, u, rec, master); assert ok3 is False and "opening shot 1 is not the file" in why3            # a clip that was replaced after the cut
    ctx = {"d": d, "shots": plain, "units": u, "opening": rec, "master": master, "ep": "EPW"}
    assert CON.p_opening_shown(ctx)[0] == CON.FAIL
    setting("CONTRACT_WAIVERS", json.dumps({"EPW": ["opening_footage"]})); st, ev = CON.p_opening_shown(ctx); assert st == CON.NA and "approved" in ev      # his Approve at the script gate is not asked for a second time
    assert CON.p_opening_shown(dict(ctx, shots=shots))[0] == CON.FAIL                                                                    # ... but a video that DOES carry the footage is still judged

def test_the_film_is_never_compared_where_two_clips_meet(tmp_path, setting):
    assert OPEN.spots([["c0.mp4", 0.0, 2.0, 1.0]], 2.0) == [0.2, 0.7, 1.2, 1.7] and OPEN.spots([["c0.mp4", 0.0, 0.3, 1.0]], 0.3) == [0.15]      # every half second, away from both ends; a stretch too short: its middle
    two = OPEN.spots([["c0.mp4", 4.404, 5.0, 1.042], ["c1.mp4", 0.0, 1.238, 1.094]], 1.97); cut = 0.596 * 1.042
    assert two and all(abs(x - cut) >= OPEN.EDGE_S - 0.002 for x in two) and any(x < cut for x in two) and any(x > cut for x in two), two      # both stretches are looked at, the change between them never (the shot the sweep found: id EP209901140910)
    assert OPEN.spots([["c0.mp4", 0.0, 0.2, 1.0], ["c1.mp4", 0.0, 1.0, 1.0]], 1.2) == [0.4, 0.9]                                       # a sliver of a clip is skipped, the other stretch is not
    d, m, u, shots, out, oc = _cut(tmp_path, setting); rec = oc["opening"]; own = _clip(os.path.join(str(tmp_path), "own.mp4"), *RN.out_size(), 6.0, "mandelbrot")
    late = _film(out, [oc["clips"][i] for i in range(5)] + [own], None, grade="tpad=start=1:start_mode=clone")                           # the film runs ONE FRAME behind its clips: at a change between two clips that is another picture
    ok, why = OPEN.shown_report(d, shots, u, rec, late); assert ok is True, why                                                           # a shot that crosses two clips (the third sentence) is still recognised
    b = OPEN.bounds(u); o1 = _clip(os.path.join(str(tmp_path), "own1.mp4"), *RN.out_size(), b[2] - b[1], "mandelbrot")
    swapped = _film(out, [oc["clips"][0], o1] + [oc["clips"][i] for i in range(2, 5)] + [own], None)
    assert OPEN.shown_report(d, shots, u, rec, swapped)[0] is False                                                                      # and other pictures under a whole sentence are still found

def test_alike_recognises_a_graded_picture_and_refuses_another_one(tmp_path):
    import cv2, numpy as np
    a = OPEN._frame(_clip(os.path.join(str(tmp_path), "a.mp4"), 640, 360, 1.0, "testsrc2"), 0.5); b = OPEN._frame(_clip(os.path.join(str(tmp_path), "b.mp4"), 640, 360, 1.0, "mandelbrot"), 0.5)
    dark = (a.astype(np.float32) * 0.55 + 12).clip(0, 255).astype(np.uint8); yy, xx = np.mgrid[0:360, 0:640]
    vig = (dark * (1.0 - 0.6 * (((xx - 320) / 320.0) ** 2 + ((yy - 180) / 180.0) ** 2) / 2)[..., None]).clip(0, 255).astype(np.uint8)
    assert OPEN.alike(a, a) > 0.99 and OPEN.alike(vig, a) >= 0.8 and OPEN.alike(cv2.resize(vig, (320, 180)), a) >= 0.8                   # darker, tinted, a vignette, another size: the same picture
    assert abs(OPEN.alike(b, a)) < 0.3 and OPEN.alike(b, a) < OPEN.SAME_MIN <= OPEN.alike(vig, a)                                        # another picture
    flat = np.full_like(a, 90); assert OPEN.alike(a, flat) is None and OPEN.alike(flat, a) == 0.0                                        # footage with nothing to recognise is not judged; a film that shows nothing is

# ------------------------------------------------------------------ 7. the first line
def test_the_first_line_is_the_shorts_hook_and_no_lab_is_run_for_it(tmp_path, monkeypatch, setting):
    script = "## BEAT 1\n[DIRECTOR] You wake up and the light is wrong.\n[CURIOUS] Wrong how?"; calls = []
    def ask(role, *a, **k): calls.append(role); raise AssertionError("the hook lab must not be asked")
    new, rec = HOOKS.run_hooks(script, {"premise": "p"}, "EPH", str(tmp_path), ask_fn=ask, proven={"line": "Your shadow just left without you.", "short": SID})
    assert not calls and rec["source"] == "short" and rec["short"] == SID and rec["applied"] and rec["status"] == "applied" and rec["scored_by"] == "viewers" and len(rec["candidates"]) == 1
    assert new.split("\n")[1].endswith("Your shadow just left without you.") and "You wake up and the light is wrong." in new          # inserted first; nothing of the writer's is removed
    rows = [r for r in core.store().rows("Hook_Candidates") if r.get("episode_id") == "EPH"]; assert len(rows) == 1 and rows[0]["applied"] == "TRUE" and rows[0]["type"] == "proven"
    d = {"ladder": SID}; units = [{"text": "Your shadow just left without you."}, {"text": "You wake up."}]
    assert HOOKS.verify_in_narration(rec, units) and CON.p_hook({"hook_rec": rec, "d": d})[0] == CON.PASS and SID in CON.p_hook({"hook_rec": rec, "d": d})[1]
    assert CON.p_hook({"hook_rec": rec, "d": {"ladder": "SH_OTHER"}})[0] == CON.FAIL and CON.p_hook({"hook_rec": rec, "d": {}})[0] == CON.FAIL      # the hook of another Short proves nothing for this video
    rec2 = json.loads(json.dumps(rec)); assert not HOOKS.verify_in_narration(rec2, [{"text": "A rewrite changed the opening."}]) and CON.p_hook({"hook_rec": rec2, "d": d})[0] == CON.FAIL
    same, rec3 = HOOKS.run_hooks("[DIRECTOR] Your shadow just left without you.\nNext line.", {}, "EPH3", str(tmp_path), ask_fn=ask, proven={"line": "Your shadow just left without you.", "short": SID})
    assert same.count("Your shadow just left without you.") == 1 and rec3["applied"] and rec3["status"] == "applied"                     # the writer already opened on it: it is not said twice
    from whatifs import packaging as PK
    monkeypatch.setattr(PK, "ad_risk", lambda line: ["unsafe"] if "shadow" in line else [])
    lab = []
    def ask2(role, *a, **k): lab.append(role); return {"candidates": [], "scores": []}
    _s, rec4 = HOOKS.run_hooks(script, {"premise": "p"}, "EPH4", str(tmp_path), ask_fn=ask2, proven={"line": "Your shadow just left without you.", "short": SID})
    assert lab and (rec4 or {}).get("source") != "short"                                                                                 # a line that is not ad-safe falls back to the lab
    assert HOOKS.proven_record(script, None) is None and HOOKS.proven_record(script, {"line": "", "short": SID}) is None

# ------------------------------------------------------------------ 8. the Animation Director, the plan check, the cut-downs
def test_the_director_buys_three_scenes_when_the_opening_is_footage_and_four_without(setting):
    u = _units(); marked = OPEN.mark(_shots(), u, _man()); plan = {"kling": 4, "living": 0}
    idx = ANIM.apply(marked, u, plan)
    assert len(idx) == 3 and plan["kling"] == 3 and not set(idx) & set(range(5)) and [marked[i]["anim"]["slot"] for i in idx] == [1, 2, 3]      # the three later anchors; the footage is never a slot
    assert OPEN.marked(marked) == [0, 1, 2, 3, 4] and all(marked[i]["type"] == "kling" and "anim" not in marked[i] for i in range(5)) and marked[0]["promise"] is True      # ... and never turned back into a still
    plain = _shots(); plan2 = {"kling": 4, "living": 0}; idx2 = ANIM.apply(plain, u, plan2)
    assert len(idx2) == 4 and 0 in idx2 and plan2["kling"] == 4 and [plain[i]["anim"]["slot"] for i in idx2] == [0, 1, 2, 3]            # without footage: four scenes, the first at second 0
    assert ANIM.pick_slots(_shots(), u, 4) == idx2 and ANIM.pick_slots(_shots(), u, 1, anchors=(0.29,)) == [4] and ANIM.pick_slots(_shots(), u, 1, skip={4}, anchors=(0.29,)) == [3]      # a skipped shot is never a slot: the next nearest is

def test_the_plan_check_and_the_paid_repair_leave_the_footage_alone(setting):
    u = _units(); marked = OPEN.mark(_shots(), u, _man())
    S_ = EP.plan_check({"shots": marked, "plan": {"kling": 1, "living": 0}, "vo": {"duration": 60}, "pkg": {"titles": ["T"]}}, u)
    assert OPEN.marked(S_["shots"]) == [0, 1, 2, 3, 4] and all(S_["shots"][i]["type"] == "kling" for i in range(5))                      # five animated shots against a plan of one: none is turned into a still
    extra = [dict(s) for s in marked]; extra[7]["type"] = "kling"; extra[8]["type"] = "kling"
    S2 = EP.plan_check({"shots": extra, "plan": {"kling": 1, "living": 0}, "vo": {"duration": 60}, "pkg": {"titles": ["T"]}}, u)
    assert S2["shots"][7]["type"] == "kling" and S2["shots"][8]["type"] == "still"                                                       # the plan's own count still binds the video's own scenes
    own = [i for i in EP.anchor_shots(marked, 3) if i >= 5]; assert len(own) == 3, own                                                 # five footage shots take nothing from a picture budget of three
    assert len([i for i in EP.anchor_shots(_shots(), 3) if _shots()[i]["type"] == "still"]) == 2                                       # ... while a paid scene of the video's own still does
    assert 5 in EP.anchor_shots(marked, 0)                                                  # the first still after the footage is the video's own picture even with no budget left: a still never re-uses a frame of the footage

def test_the_paid_repair_never_remakes_a_shot_of_the_footage(monkeypatch, setting):
    import whatifs.media as MD
    u = _units(); marked = OPEN.mark(_shots(), u, _man()); paid = []
    monkeypatch.setattr(MD, "still", lambda *a, **k: (paid.append("still"), ("x.jpg", ""))[1]); monkeypatch.setattr(MD, "animate", lambda *a, **k: (paid.append("clip"), "x.mp4")[1])
    files = {"img": {i: f"img{i:03d}.jpg" for i in range(6)}, "clips": {i: f"clip{i:03d}.mp4" for i in range(5)}, "anchors": list(range(6)), "missing": [], "urls": {}}
    job = EP.Job(ep="EPR", out=core.WORK, files=files, shots=marked, units=u, fps=30); job.render_all = lambda: None
    job.repair_assets({"vision_artifact", "vision_mismatch"}, [0, 1, 2], 80.0); assert not paid, paid                                 # the picture judge flagged three footage shots: none is bought again
    job.repair_assets({"vision_mismatch"}, [6], 80.0); assert paid == ["still"]                                                        # a picture of the video's own still is

def test_no_reaction_effect_is_drawn_over_the_footage(monkeypatch, setting):
    u = _units(); marked = OPEN.mark(_shots(), u, _man()); ev = [{"i": 2, "t": 4.5, "end": 6.9, "kind": "shock", "word": "WAIT", "line": "x"}, {"i": 7, "t": 24.0, "end": 30.9, "kind": "shock", "word": "NO", "line": "y"}]
    monkeypatch.setattr(EP.RX, "find_events", lambda units: [dict(e) for e in ev]); monkeypatch.setattr(EP.FE, "mode", lambda: "duo"); setting("REACTION_FX_ON", "TRUE")
    assert [e["i"] for e in EP.reaction_events(u, marked)] == [7]                                                                        # the burst and the zoom at second 4.5 would cover the Short's own picture: not drawn
    assert [e["i"] for e in EP.reaction_events(u, _shots())] == [2, 7]                                                                   # a video that opens on its own pictures keeps every reaction effect
    setting("REACTION_FX_ON", "FALSE"); assert EP.reaction_events(u, _shots()) == []

def test_a_cut_down_never_takes_a_shot_of_the_footage(setting):
    u = _units(); marked = OPEN.mark(_shots(), u, _man())
    assert ROOM.past_footage([0, 1, 2, 6], marked) == [5, 7, 8, 6]                                                                       # each footage shot is replaced by the next free shot of the video's own pictures
    assert ROOM.past_footage([6, 7, 8, 9], marked) == [6, 7, 8, 9] and ROOM.past_footage([0, 1, 2], _shots()) == [0, 1, 2]              # nothing to replace; no footage at all
    assert ROOM.past_footage([4, 5, 6, 7, 8, 9, 3], marked) == [5, 6, 7, 8, 9]                                                           # none left: the footage shot is dropped, never kept

def test_the_footage_is_not_offered_to_the_cut_down_planner(monkeypatch, setting):
    u = _units(); marked = OPEN.mark(_shots(), u, _man()); offered = []; real = ROOM.P.fill
    def fill(tpl, **kw):
        if "shots" in kw: offered.append(str(kw["shots"]))
        return real(tpl, **kw)
    monkeypatch.setattr(ROOM.P, "fill", fill); monkeypatch.setattr(ROOM, "ask", lambda *a, **k: {"reels": [{"shots": [0, 1, 2, 6], "lines": ["a line"]}]})
    good = ROOM.reels({"spine": {"premise": "p"}, "script": {"script": "s"}}, marked, {"reel_formats": ["myth"], "playbook": {}}, "EPQ")
    lines = offered[-1].split("\n"); assert [l.split(":")[0] for l in lines] == ["5", "6", "7", "8", "9"], lines                         # only the video's own pictures are on offer
    assert good and good[0]["shots"] == [5, 7, 8, 6]                                                                                    # and a planner that names a footage shot anyway gets the next free shot instead

def test_the_sweep_counts_an_opening_only_when_both_checks_passed():
    from tools import sweep as SW
    row = lambda f, s: {"ts": core.iso(), "episode_id": "EPS", "stage": "x", "feature": f, "status": s, "evidence": "the first 14.2 s are the footage"}
    core.store().append("Feature_Ledger", [row("opening_footage", "PASS"), row("opening_shown", "PASS")]); ok, words = SW.opening_of(core, "EPS"); assert ok and "14.2 s" in words
    core.store().append("Feature_Ledger", [dict(row("opening_shown", CON.NA), episode_id="EPT"), dict(row("opening_footage", "PASS"), episode_id="EPT")])
    assert SW.opening_of(core, "EPT")[0] is False and "opening_shown" in SW.opening_of(core, "EPT")[1] and SW.opening_of(core, "EPU")[0] is False      # 'not applicable' or no verdict at all: the path was not walked
    assert SW.summary([{"id": "a", "outcome": "ok", "opening": "x"}, {"id": "b", "outcome": "odd", "opening": "y"}, {"id": "c", "outcome": "ok"}])["opened_on_footage"] == 1

# ------------------------------------------------------------------ 9. wiring
def test_the_opening_is_registered_classified_and_protected():
    from whatifs.org import registry as REG, levers as LV, rnd as RND
    from tools import repair as RP
    feats = {f[0]: f[1] for f in CON.FEATURES}
    assert feats["opening_footage"] == "script" and feats["opening_shown"] == "final" and REG.CHECK_OWNER["opening_footage"] == REG.CHECK_OWNER["opening_shown"] == "D6"
    assert "whatifs/opening.py" in REG.DEPTS["D6"]["wraps"] and {"OPENING_FIT", "OPENING_ENLARGE_MAX"} <= set(REG.DEPTS["D6"]["levers"]) and "whatifs/opening.py" in RP.PROTECTED
    assert LV.LEVERS["OPENING_FIT"]["values"] == OPEN.MODES and LV.LEVERS["OPENING_ENLARGE_MAX"]["owner"] == "up" and "opening_footage" not in RND.ORG_CHECKS and "opening_shown" not in RND.ORG_CHECKS
    for k, v in (("OPENING_SHORT_ON", "TRUE"), ("OPENING_HOOK_ON", "TRUE"), ("OPENING_FIT", "auto"), ("OPENING_ENLARGE_MAX", "2.0"), ("OPENING_WINDOW_Y", "0.5"), ("OPENING_SHORT_MAX_S", "40")):
        assert core.DEFAULTS[k][0] == v, k
    from whatifs import formats as FMT
    assert all(FMT.rule(f, fmt) not in ("never", "advisory") for f in ("opening_footage", "opening_shown") for fmt in ("F1", "F2"))      # no format may switch the opening's checks off
