"""v12 DRAWN-b, PART B (the Opus memo `DESIGN_DRAWN_B_RECORD.md` 3.1 to 3.4 with PREDESIGN_DRAWN_b's F-1 to F-3): the cast at its own shape, the
mouth on the voice, his own lock. Step B1: tests 1 to 6 and F-2's test of both moves. Step B2 (3.5 with F-10 to F-13 and C6 to C9): tests 7 to
12 and C9's. RULINGS_U1b PART 3: C11 and C12. Every rule both ways, one fault at a time."""
import inspect, os, shutil, wave
import numpy as np
from whatifs import core


def _art(path, w, h, seed=1):
    import cv2
    cv2.imwrite(str(path), (np.random.default_rng(seed).random((h, w, 3)) * 255).astype(np.uint8)); return str(path)


def _lock(char, path, mark=None):
    core.store().append("Character_Sheets", [{"ts": core.iso(), "character": char, "expression": "neutral", "hash": char + "neutral", "prompt": "",
                                              "file": path, "status": "LOCKED", "approved_at": mark if mark is not None else core.iso()}])


# ------------------------------------------------------------------ 3.1 THE ART AT ITS OWN SHAPE
def test_1_the_art_is_framed_whole_at_its_own_shape_in_both_framings():
    import cv2
    from whatifs import living as LV
    for name, (aw, ah) in {"3:4": (768, 1024), "4:3": (1024, 768), "1:1": (800, 800), "16:9": (1280, 720), "9:16": (720, 1280)}.items():
        art = (np.random.default_rng(1).random((ah, aw, 3)) * 255).astype(np.uint8)
        assert LV.shape_word(aw, ah) == name
        for W, H in ((1920, 1080), (640, 360), (1080, 1920), (360, 640)):
            fr, (x0, y0, x1, y1) = LV.frame_of(art, W, H); w, h = x1 - x0, y1 - y0
            err = abs((w / max(1, h)) / (aw / ah) - 1)
            assert fr.shape == (H, W, 3) and err <= 0.01 and 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H, (name, W, H, err, (x0, y0, x1, y1))
            assert (h == H) if W >= H else (w == W), (name, W, H, w, h)                    # the height filled (landscape) or the width (upright)
            if W < H and aw / ah >= 0.6:                                                  # upright, art at least 0.6 wide: the head inside the safe band
                t, b, l, r = LV.SHORT_SAFE
                assert x0 + 0.25 * w >= l * W and x0 + 0.75 * w <= r * W and y0 >= t * H and y0 + LV.HEAD * h <= b * H, (name, W, H)
    art = (np.random.default_rng(2).random((720, 1280, 3)) * 255).astype(np.uint8)
    for W, H in ((1920, 1080), (640, 360)):                                               # 16:9 art in a 16:9 frame: byte for byte today's resize
        assert np.array_equal(LV.frame_of(art, W, H)[0], cv2.resize(art, (W, H)))
    a34 = (np.random.default_rng(3).random((1024, 768, 3)) * 255).astype(np.uint8)       # C4: 3:4 art in the memo's own boxes - never the stretch
    for (W, H), box in (((1920, 1080), (555, 0, 1365, 1080)), ((1080, 1920), (0, 192, 1080, 1632))):
        fr, got = LV.frame_of(a34, W, H)
        assert tuple(got) == box and not np.array_equal(fr, cv2.resize(a34, (W, H))), (W, H, got)
    assert round(abs((1920 / 1080) / (a34.shape[1] / a34.shape[0]) - 1), 2) == 1.37 > 0.01   # a planted stretch of 3:4 art to 1920 x 1080: over the limit


def test_2_render_composes_the_art_at_its_own_shape_and_the_check_fails_a_crooked_one(tmp_path, monkeypatch, setting):
    from whatifs import living as LV, contract as CON
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", _art(tmp_path / "vale.png", 768, 1024))
    seen, real = [], LV.frame_of
    monkeypatch.setattr(LV, "frame_of", lambda art, W, H: seen.append((art.shape[:2], W, H)) or real(art, W, H))
    LV.USED.clear()
    for W, H in ((640, 360), (360, 640)):
        seen.clear(); r = LV.render("DIRECTOR", "Really? Prove it.", [], 0.0, str(tmp_path / f"c{W}.mp4"), 12, "EPB12", seed="s", size=(W, H))
        assert r and r["size"] == [W, H] and r["shape_err"] <= 0.01 and seen and seen[0] == ((1024, 768), W, H), (r, seen)      # its own pixels, at the frame's size
    assert [u["size"] for u in LV.USED] == [[640, 360], [360, 640]] and all(u["shape_err"] <= 0.01 for u in LV.USED), LV.USED
    react = [{"type": "reaction", "speaker": "DIRECTOR"}]
    assert CON.p_living({"shots": react, "absent": 0})[0] == CON.PASS
    LV.USED.append({"character": "VALE", "expression": "neutral", "blinks": 0, "mouth_frames": 0, "shape_err": 0.3})
    s, ev = CON.p_living({"shots": react, "absent": 0}); assert s == CON.FAIL and "out of its own shape" in ev, ev
    LV.USED.clear()
    assert LV.render("SKEPTIC", "No.", [], 0.0, str(tmp_path / "g.mp4"), 12, "EPB12") is None and LV.USED == []        # without a LOCKED row: None, nothing written
    import cv2                                                                            # C4: a stretch planted THROUGH render - its own measure sees it
    monkeypatch.setattr(LV, "frame_of", lambda art, W, H: (cv2.resize(art, (W, H)), (0, 0, W, H)))
    r = LV.render("DIRECTOR", "Really? Prove it.", [], 0.0, str(tmp_path / "bent.mp4"), 12, "EPB12", seed="s", size=(640, 360))
    assert r and round(r["shape_err"], 2) == 1.37, r                                       # 3:4 art pulled to 16:9
    s, ev = CON.p_living({"shots": react, "absent": 0}); assert s == CON.FAIL and "137% off" in ev, ev
    monkeypatch.setattr(LV, "frame_of", real); LV.USED.clear()                            # restored: the same cutaway at its own shape PASSES
    r = LV.render("DIRECTOR", "Really? Prove it.", [], 0.0, str(tmp_path / "true.mp4"), 12, "EPB12", seed="s", size=(640, 360))
    assert r and r["shape_err"] <= 0.01 and CON.p_living({"shots": react, "absent": 0})[0] == CON.PASS, r


def test_3_the_blink_and_mouth_pictures_are_asked_at_the_arts_own_shape(tmp_path, monkeypatch):
    import cv2
    from whatifs import living as LV, anim as ANIM, sheets as SH, publish as PUB
    asked = []
    monkeypatch.setattr(LV, "FAKE", False)
    monkeypatch.setattr(ANIM, "gemini_image", lambda prompt, refs, p, ep, aspect="16:9": asked.append(aspect) or cv2.imwrite(p, cv2.imread(refs[0])))
    monkeypatch.setattr(SH, "identity_score", lambda a, b, c, episode=None: 9)      # C9: the film is handed on
    monkeypatch.setattr(PUB, "drive_upload", lambda p, name, public=False: ("fid", ""))
    for (w, h), want in (((768, 1024), "3:4"), ((640, 360), "16:9")):
        shutil.rmtree(os.path.join(core.WORK, f"EPB13{w}"), ignore_errors=True)            # C11: one film asks at most two pictures - each art its own film
        asked.clear(); LV.variants(f"T{w}", "neutral", _art(tmp_path / f"a{w}.png", w, h), f"EPB13{w}")
        assert asked == [want, want], (w, h, asked)


# ------------------------------------------------------------------ 3.2 THE MOUTH ON THE VOICE
def test_4_the_mouth_opens_on_the_voice_inside_its_words(tmp_path, setting):
    from whatifs import living as LV
    sr, fps, n = 24000, 30, 30
    t = np.arange(sr) / sr; loud = ((t >= 0.2) & (t < 0.4)) | ((t >= 0.55) & (t < 0.8)); a = np.where(loud, 0.5 * np.sin(2 * np.pi * 220 * t), 0.0)
    wav = str(tmp_path / "v.wav")
    with wave.open(wav, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes((a * 32767).astype(np.int16).tobytes())
    words = [{"w": "word", "s": 0.2, "e": 0.8}]                                             # one word 0.2 to 0.8 s: bursts 0.2-0.4 and 0.55-0.8, silence 0.4-0.55
    env = LV.envelope(wav, 0.0, fps, n); assert len(env) == n
    on = LV.speaking(words, 0.0, fps, n, env=env)
    burst = {f for f in range(n) if 0.2 * fps - 1 <= f <= 0.4 * fps + 1 or 0.55 * fps - 1 <= f <= 0.8 * fps + 1}
    assert on and on <= burst and not on & {13, 14, 15} and all(6 <= f < 24 for f in on), sorted(on)      # only on burst frames, closed in the pause, never outside the word
    dip = list(env); dip[8] = 0.0; assert 8 in LV.speaking(words, 0.0, fps, n, env=dip)             # a one-frame dip inside a burst is filled
    older = {f for f in range(6, 24) if (f - 6) % 4 < 2}
    assert LV.speaking(words, 0.0, fps, n) == older                                         # no envelope: the older rule
    setting("LIVING_MOUTH_OPEN_K", "0"); assert LV.speaking(words, 0.0, fps, n, env=env) == older      # the cell 0: the older rule on the same words
    setting("LIVING_MOUTH_OPEN_K", "0.6")
    assert LV.envelope(str(tmp_path / "none.wav"), 0.0, fps, n) == [] and LV.speaking(words, 0.0, fps, n, env=[]) == older      # no file: [] and the older rule


# ------------------------------------------------------------------ 3.3 HIS OWN LOCK
def test_5_only_his_own_lock_turns_the_talking_cast_on(setting):
    from whatifs import living as LV, sheets as SH
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", "drive:test-vale", "2026-11-18T00:00:00Z (default)")
    assert not LV.has_art("DIRECTOR") and LV.expression_for("DIRECTOR") == (None, None)      # locked by default after 72 h: absent from the cutaways
    assert SH.locked_portraits() == {("VALE", "neutral"): "drive:test-vale"}                  # the theatre untouched
    setting("LIVING_HIS_LOCK_ONLY", "FALSE"); assert LV.has_art("DIRECTOR")                   # the switch off: the default lock counts
    setting("LIVING_HIS_LOCK_ONLY", "TRUE")
    for mark in ("2026-11-18T00:00:00Z (dashboard)", "2026-11-18T00:00:00Z"):                  # his "Lock these" and his APPROVE SHEET
        core.store().update_where("Character_Sheets", {"hash": "VALEneutral"}, {"approved_at": mark}); assert LV.has_art("DIRECTOR"), mark


# ------------------------------------------------------------------ 3.2 THE PIECE'S OWN CLOCK
def test_6_each_piece_of_a_long_cutaway_talks_on_its_own_seconds(tmp_path, monkeypatch, setting):
    from whatifs import episode as EP, living as LV, render as RN
    src = inspect.getsource(EP._render); assert 'float(u_.get("start", 0) or 0) + cut[k] / fps, path, nf, ep' in src and 'float(u_.get("start", 0) or 0) + cut[k] / fps, nf, path' in src and "wav=vo.wav_path" in src and "f0, vo.wav_path)" in src      # RUL-BRK-U1 (DRAWN-b-B-8) + RUL-U1n (F2): each call site's own offset, its unit start included - the render (:560) and the restyle arm (:562) - and each one's own voice file
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", _art(tmp_path / "vale.png", 640, 360))
    got, real = [], LV.speaking
    monkeypatch.setattr(LV, "speaking", lambda *a, **k: got.append(real(*a, **k)) or got[-1])
    fps, s0 = RN.fps(), 40.0                                                                 # the line starts at film second 40; this piece 12 s into it
    words = [{"w": "first", "s": s0 + 0.5, "e": s0 + 1.5}, {"w": "later", "s": s0 + 12.5, "e": s0 + 13.5}]
    r = LV.render("DIRECTOR", "Really? Prove it.", words, s0 + 12, str(tmp_path / "p.mp4"), int(2 * fps), "EPB16", seed="s")
    assert r and r["mouth_rule"] == "flap" and got and got[-1], (r, got)
    assert all(int(0.5 * fps) <= f < int(1.5 * fps) for f in got[-1]), sorted(got[-1])      # only the words of seconds 12 to 14 of the line
    wav, sr = str(tmp_path / "vo.wav"), 8000                                               # C5: the render HEARS the narration - sound only from second 12.9
    with wave.open(wav, "wb") as f:                                                        # of the line, inside the word 12.5 to 13.5
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        a = np.zeros(int((s0 + 15) * sr), dtype=np.int16); a[int((s0 + 12.9) * sr):int((s0 + 13.5) * sr)] = 12000; f.writeframes(a.tobytes())
    got.clear(); r = LV.render("DIRECTOR", "Really? Prove it.", words, s0 + 12, str(tmp_path / "w.mp4"), int(2 * fps), "EPB16", seed="s", wav=wav)
    assert r and r["mouth_rule"] == "voice" and got and got[-1], (r, got)
    assert all(int(0.9 * fps) - 1 <= f < int(1.5 * fps) for f in got[-1]), sorted(got[-1])  # the mouth opens only where the voice sounds


# ------------------------------------------------------------------ F-2: DRAWN's move undone once, never a FALSE he typed
def test_f2_drawns_off_move_is_undone_once_and_a_false_he_typed_stays(setting):
    from whatifs import manage as MG
    assert core.DEFAULTS["LIVING_CHARACTERS_ON"][0] == "TRUE" and core.DEFAULTS["LIVING_HIS_LOCK_ONLY"][0] == "TRUE"
    setting("LIVING_CHARACTERS_ON", "TRUE"); setting("V12DRAWN_FLIPS_DONE", ""); setting("V12DRAWNB_FLIPS_DONE", "")      # the written TRUE, both DONE cells empty
    assert MG.v12drawn_upgrade(core.store()) == ["LIVING_CHARACTERS_ON"] and MG.v12drawnb_upgrade(core.store()) == ["LIVING_CHARACTERS_ON"]
    assert core.S("LIVING_CHARACTERS_ON", bool) and core.S("V12DRAWN_FLIPS_DONE") and core.S("V12DRAWNB_FLIPS_DONE")       # TRUE, FALSE, TRUE
    assert MG.v12drawn_upgrade(core.store()) == [] and MG.v12drawnb_upgrade(core.store()) == []                           # both again: nothing moves
    setting("LIVING_CHARACTERS_ON", "FALSE"); MG.v12drawnb_upgrade(core.store()); assert not core.S("LIVING_CHARACTERS_ON", bool)      # his FALSE after that stays
    setting("V12DRAWN_FLIPS_DONE", "2026-11-19T00:00:00Z none"); setting("V12DRAWNB_FLIPS_DONE", "")                    # a FALSE he typed before DRAWN: its move moved nothing
    assert MG.v12drawnb_upgrade(core.store()) == [] and not core.S("LIVING_CHARACTERS_ON", bool)
    setting("LIVING_CHARACTERS_ON", "TRUE"); setting("V12DRAWN_FLIPS_DONE", ""); setting("V12DRAWNB_FLIPS_DONE", ""); MG.setup()
    assert core.S("LIVING_CHARACTERS_ON", bool) and core.S("V12DRAWN_FLIPS_DONE") and core.S("V12DRAWNB_FLIPS_DONE")       # the setup runs both, in order


# ------------------------------------------------------------------ 13. THE CORE'S PLANTED GUARD (item 146 (3))
def test_13_the_cores_planted_guard_the_cast_cells_move_no_slop_score(setting):
    from whatifs import slop as SL
    units = [{"i": i, "start": 4.0 * i, "end": 4.0 * (i + 1), "text": f"Line {i}: a lighthouse keeper counts the ships he never saw.",
              "speaker": "VALE" if i % 2 else "DIRECTOR"} for i in range(6)]
    shots = [{"type": "reaction" if i % 3 == 2 else "still", "prompt": f"a lighthouse at night, shot {i}"} for i in range(6)]     # the same offline plan, two cutaways in it
    assert core.S("LIVING_MOUTH_OPEN_K", float) == 0.6 and core.S("LIVING_HIS_LOCK_ONLY", bool) and core.S("LIVING_CHARACTERS_ON", bool)   # every DRAWN-b cell at its default
    at_default = SL.score(units, shots, "EPB13")
    setting("LIVING_MOUTH_OPEN_K", "0"); setting("LIVING_HIS_LOCK_ONLY", "FALSE")
    moved = SL.score(units, shots, "EPB13")
    assert at_default == moved, (at_default, moved)                                         # no shot type, unit or opening changes


# ------------------------------------------------------------------ 14. THE WALK - ONE WHOLE PRODUCTION (SERIAL-LONG: the coordinator's TEST row)
def test_14_the_walk_his_locked_art_talks_at_its_own_shape_and_a_default_lock_shows_nobody(tmp_path, monkeypatch, setting):
    import datetime as dt, shutil
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import manage as MG, episode as EP, living as LV
    now = dt.datetime(2031, 3, 14, 10, 0, tzinfo=dt.timezone.utc)                         # this test's own id: its film keeps a VALE cutaway (RULINGS_U3h 4's probe: 1 cutaway, mouth on the voice)
    slot, ep = (now + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "EP" + now.strftime("%Y%m%d%H%M")
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); monkeypatch.setattr(EP, "now_utc", lambda: now)
    art = _art(tmp_path / "vale.png", 768, 1024, seed=14)                                   # a LOCKED 3:4 picture for VALE

    def walk(sheet, mark):
        core._store = core.LocalStore(str(tmp_path / sheet)); core._store.ensure_tabs()        # its own Sheet each time
        MG.setup(); core.set_setting("VOICE", "C"); core.set_setting("LADDER_ON", "FALSE"); core.set_setting("FORMAT_FORCE", "F2")      # RULINGS_U3h 4: the shipped Sheet + the two cells without which no long film of the cast is made (conftest 41-42)
        setting("LIVING_CHARACTERS_ON", "TRUE"); setting("LIVING_HIS_LOCK_ONLY", "TRUE")
        _lock("VALE", art, mark); LV.USED.clear()
        try:
            r = EP.produce(slot); assert r["ok"], r
            led = {x["feature"]: (x["status"], x["evidence"]) for x in core.store().rows("Feature_Ledger") if x["feature"] == "living_characters"}
            return led["living_characters"], [dict(x) for x in LV.USED]
        finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)

    (st, ev), used = walk("sheet_his.json", None)                                           # his own lock
    assert st == "PASS", ev
    assert used, "this id's film kept no cutaway: name another id (TO VERIFY 1)"
    assert all(u["shape_err"] <= 0.01 and u["mouth_rule"] == "voice" for u in used), used
    (st, ev), used = walk("sheet_default.json", "2026-11-18T00:00:00Z (default)")          # the same id, the row locked "(default)"
    assert used == [] and st == "PASS" and ev.startswith("nobody is on screen"), (st, ev, used)


# ------------------------------------------------------------------ STEP B2 (3.5 with F-10 to F-13, C6 to C9): the restyle arm, built and off
def _open(monkeypatch, setting, share="10"):
    from whatifs import governor as G
    monkeypatch.setattr(G, "line_usd_s", lambda: 1.0); setting("RESTYLE_ON", "TRUE"); setting("RESTYLE_SHARE_PCT", share)


def _solid(path, w=640, h=360):
    import cv2
    im = np.zeros((h, w, 3), np.uint8); im[:] = (40, 110, 210); im[h // 4:h // 2, w // 3:w // 2] = (200, 60, 30); cv2.imwrite(str(path), im); return str(path)


def _piece(tmp_path, setting, ep, sec=1.5, folder="film"):
    """A code-made cutaway piece of VALE (his own lock) in its own folder: the restyle's source."""
    from whatifs import living as LV, render as RN
    setting("LIVING_CHARACTERS_ON", "TRUE")
    if not core.store().rows("Character_Sheets"): _lock("VALE", _solid(tmp_path / "vale_solid.png"))
    d = tmp_path / folder; d.mkdir(exist_ok=True); src = str(d / "cut000_0.mp4")
    assert LV.render("DIRECTOR", "Really? Prove it.", [], 0.0, src, int(sec * RN.fps()), ep, seed="s", record=False)
    return src


def test_7_the_restyle_row_and_its_four_locks(monkeypatch, setting):
    import json
    from whatifs import clips as CL, governor as G
    row = json.loads(core.DEFAULTS["RESTYLE_MODELS"][0])[0]
    assert CL.restyle_table() == [row] and row["id"] == core.DEFAULTS["FAL_RESTYLE_MODEL"][0] and CL.issues(row, role="restyle") == []
    assert any("a video-start row restyles a video" in x for x in CL.issues(row)), CL.issues(row)      # the hero and living picks never meet it
    for r in CL.table(): assert CL.issues(r, role="restyle"), r["id"]                                   # a clip row is never a restyle row
    monkeypatch.setattr(G, "line_usd_s", lambda: 1.0)
    assert CL.restyle() is None                                                                         # at the launch: his switch off, the share 0
    setting("RESTYLE_ON", "TRUE"); assert CL.restyle() is None                                          # the share 0
    setting("RESTYLE_SHARE_PCT", "10"); assert CL.restyle() == row                                      # all four locks open
    setting("RESTYLE_ON", "FALSE"); assert CL.restyle() is None; setting("RESTYLE_ON", "TRUE")         # HIS switch
    setting("FAL_RESTYLE_MODEL", ""); assert CL.restyle() is None; setting("FAL_RESTYLE_MODEL", row["id"])
    setting("RESTYLE_MODELS", json.dumps([dict(row, lic="research")])); assert CL.restyle() is None
    setting("RESTYLE_MODELS", json.dumps([dict(row, stale="the listing's base price moved")])); assert CL.restyle() is None      # F-13: a moved price closes the arm
    assert "its listed price moved: its page must be read again" in CL.issues(dict(row, stale="x"), role="restyle")
    setting("RESTYLE_MODELS", json.dumps([row])); assert CL.restyle() == row
    monkeypatch.setattr(G, "line_usd_s", lambda: 0.005)
    assert CL.restyle() is None and CL.restyle(within_line=False) == row                               # above the line; the estimate's own call ignores it
    b = CL.args(row, "data:x", "p", 5)
    assert "duration" not in b and b["video_url"] == "data:x" and b["resolution"] == "720p" and b["enhance_prompt"] is False, b
    for r in CL.table():                                                                                # today's rows: the same body as before, key for key, in order
        n = CL.secs(r, 5); old = {"prompt": "p", str(r.get("start") or "image_url"): "u", "duration": str(n) if str(r.get("dur") or "int") == "str" else n}
        if r.get("res_field") and r.get("res") not in (None, "", "-"): old[str(r["res_field"])] = r["res"]
        old.update(r.get("extra") or {})
        assert list(CL.args(r, "u", "p", 5).items()) == list(old.items()), r["id"]


def test_8_one_restyled_copy_is_bought_by_the_second_whole_or_not_at_all(tmp_path, monkeypatch, setting):
    import cv2
    from whatifs import media as MD, render as RN
    src = _piece(tmp_path, setting, "EPB18"); out = str(tmp_path / "rst.mp4"); booked = []
    monkeypatch.setattr(MD, "cost", lambda *a, **k: booked.append(a))
    try: MD.restyle(src, "p", out, "EPB18", 1.5); raise AssertionError("bought with the arm closed")
    except RuntimeError as e: assert "no restyle row" in str(e), e
    _open(monkeypatch, setting)
    assert MD.restyle(src, "p", out, "EPB18", 1.5) == out and not os.path.exists(out + ".part")
    assert booked == [("restyle_clip", "fal", 2, 0.0, "EPB18")], booked                                  # in seconds, rounded up, before the file stands

    def frames(path):
        cap = cv2.VideoCapture(path); fs = []
        while True:
            ok, fr = cap.read()
            if not ok: break
            fs.append(fr)
        cap.release(); return fs
    a, b = frames(src), frames(out)
    hue = lambda fs: float(np.mean([cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 0].mean() for f in fs]))
    assert a and len(a) == len(b) and abs(hue(a) - hue(b)) > 2.0, (len(a), len(b), hue(a), hue(b))     # the same frame count, the colour turned
    real = RN.probe_dur                                                                                     # F-10: a reply half a second short is never kept
    monkeypatch.setattr(RN, "probe_dur", lambda path: real(path) - 0.5 if str(path).endswith(".part") else real(path))
    out2 = str(tmp_path / "rst2.mp4")
    try: MD.restyle(src, "p", out2, "EPB18", 1.5); raise AssertionError("a short reply was kept")
    except RuntimeError as e: assert "another length" in str(e), e
    assert not os.path.exists(out2) and not os.path.exists(out2 + ".part")


def test_9_the_arm_in_the_render(tmp_path, monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import living as LV, render as RN, sheets as SH, media as MD, episode as EP
    src = _piece(tmp_path, setting, "EPB19")
    assert LV.restyle_arm("EPB19", 0, 0) is False                                                          # restyle() None: never in the arm
    _open(monkeypatch, setting, share="100"); assert LV.restyle_arm("EPB19", 0, 0) is True
    c = watch(monkeypatch); judged, score = [], [3]
    monkeypatch.setattr(SH, "identity_score", lambda ref, new, who, episode=None: judged.append(episode) or score[0])
    before = open(src, "rb").read()
    assert LV.restyle(src, "DIRECTOR", "EPB19", 0, 0, 1.5) is False and open(src, "rb").read() == before    # not the approved character: not played
    assert c["restyle"] == 1 and judged == ["EPB19"], (c, judged)
    score[0] = 9
    assert LV.restyle(src, "DIRECTOR", "EPB19", 0, 0, 1.5) is False and c["restyle"] == 1 and judged == ["EPB19"]   # kept, never bought again; judged ONCE (F-12)
    assert LV.restyle(src, "DIRECTOR", "EPB19", 1, 0, 1.5) is True and c["restyle"] == 2                    # another piece, the approved character: played
    setting("RESTYLE_EST_S", "3"); s2 = _piece(tmp_path, setting, "EPB19", sec=2.0, folder="cap")         # F-11: the cap is a cap
    assert LV.restyle(s2, "DIRECTOR", "EPB19", 0, 0, 2.0) is True and c["restyle"] == 3                    # 2 s bought
    assert LV.restyle(s2, "DIRECTOR", "EPB19", 1, 0, 2.0) is False and c["restyle"] == 3                   # 2 + 2 would pass 3: not bought
    assert open(os.path.join(os.path.dirname(s2), "rst_booked.txt")).read() == "2"
    setting("RESTYLE_EST_S", "20")
    s3 = _piece(tmp_path, setting, "EPB19", folder="empty"); open(os.path.join(os.path.dirname(s3), "rst_booked.txt"), "w").close()
    assert LV.restyle(s3, "DIRECTOR", "EPB19", 0, 0, 1.5) is False and c["restyle"] == 3                   # C6: an empty booked file CLOSES the cap
    s4 = _piece(tmp_path, setting, "EPB19", folder="fail"); w_ = MD.restyle

    def boom(*a, **k): raise RuntimeError("planted")
    monkeypatch.setattr(MD, "restyle", boom)
    try: LV.restyle(s4, "DIRECTOR", "EPB19", 0, 0, 1.5); raise AssertionError("a failed buy returned")
    except RuntimeError as e: assert "planted" in str(e), e
    assert open(os.path.join(os.path.dirname(s4), "rst_booked.txt")).read() == "2"                         # C7: a failed buy is booked too
    monkeypatch.setattr(MD, "restyle", w_)
    asked = []                                                                                              # THE CALL SITE (F-10): the source has nothing over it

    class Boom:
        def apply(self, fr, n): asked.append(n); raise RuntimeError("an overlay was asked")
    u_, nf = {"text": "Really? Prove it.", "words": [], "start": 0}, int(1.5 * RN.fps())
    for folder, fail in (("site", False), ("site2", True)):
        s5 = _piece(tmp_path, setting, "EPB19", folder=folder); d5 = os.path.dirname(s5); path = os.path.join(d5, "seg.mp4")
        LV.USED.clear(); assert LV.render("DIRECTOR", u_["text"], [], 0.0, path, nf, "EPB19", seed="s")   # the code-made piece in `path`
        made = open(path, "rb").read(); RN.set_overlay(Boom())
        if fail:                                                                                            # the planted render writes half a file, then raises
            def half(clip, target, n, **k): open(target, "wb").write(b"half a file"); raise RuntimeError("planted render")
            monkeypatch.setattr(RN, "clip_segment", half)
        EP._restyle_piece("EPB19", d5, 0, 0, "DIRECTOR", u_, 0.0, nf, path, None, None, 0, None)
        assert asked == [] and not os.path.exists(path + ".rst.mp4"), (folder, asked)
        if fail: assert open(path, "rb").read() == made and LV.USED[-1]["restyled"] is False                 # the code-made piece byte for byte
        else: assert open(path, "rb").read() != made and LV.USED[-1]["restyled"] is True                     # the restyled piece is played
    RN.set_overlay(None)


def test_10_the_restyle_is_a_line_of_the_estimate_only_while_it_can_fire(monkeypatch, setting):
    from whatifs import costguard as CG, governor as G, clips as CL
    base, ladder = CG.lines("long"), CG.lines("ladder")
    assert not [l for l in base + ladder if l["key"] in ("restyle", "restyle_identity")]                    # closed: today's estimate
    setting("RESTYLE_ON", "TRUE"); assert [l for l in CG.lines("long")] == base                            # the share 0: closed
    setting("RESTYLE_SHARE_PCT", "10")
    L = {l["key"]: l for l in CG.lines("long")}; r = CL.restyle(within_line=False); u = core.S("USD_INR", float)
    assert L["restyle"]["n"] == 20 and L["restyle"]["unit_inr"] == round(CL.usd_s(r) * u, 4) and L["restyle"]["item"] == "restyle_clip" and L["restyle"]["unit"] == "s", L["restyle"]
    i_ = L.get("restyle_identity"); assert i_, L.keys()                                                     # C8: the judge of each piece is a line
    assert i_["n"] == 20 and i_["unit_inr"] == 40.0 and i_["calls"] == {"vision": None} and i_["stage"] == "ai_writing" and i_["item"] is None, i_
    assert [l for l in CG.lines("long") if l["key"] not in ("restyle", "restyle_identity")] == base          # nothing else moves
    assert {"restyle", "restyle_identity"} <= {l["key"] for l in CG.lines("ladder")}
    assert float(G.line_usd_s()) >= 0                                                                       # no circle with the arm open


def test_11_preflight_says_where_the_trial_stands_never_a_block(monkeypatch, setting):
    import json
    from whatifs import clips as CL, governor as G, preflight as PF
    ok, why = CL.restyle_preflight(); assert ok and "built and off" in why, why
    setting("RESTYLE_ON", "TRUE"); setting("RESTYLE_SHARE_PCT", "10"); monkeypatch.setattr(G, "line_usd_s", lambda: 1.0)
    ok, why = CL.restyle_preflight(); assert ok and "can be bought at USD 0.01 a second (share 10%)" in why, why
    monkeypatch.setattr(G, "line_usd_s", lambda: 0.005); ok, why = CL.restyle_preflight(); assert not ok and "above the month's line" in why, why
    monkeypatch.setattr(G, "line_usd_s", lambda: 1.0); row = json.loads(core.DEFAULTS["RESTYLE_MODELS"][0])[0]
    setting("RESTYLE_MODELS", json.dumps([dict(row, stale="moved")])); ok, why = CL.restyle_preflight(); assert not ok and "its listed price moved" in why, why
    setting("RESTYLE_MODELS", json.dumps([dict(row, lic="research")])); ok, why = CL.restyle_preflight(); assert not ok and "licence" in why, why
    setting("FAL_RESTYLE_MODEL", "nobody/none"); ok, why = CL.restyle_preflight(); assert not ok and "has no row in RESTYLE_MODELS" in why, why
    src = inspect.getsource(PF.run)                                                                         # the house's source-text form (tests/test_v12_money.py 170)
    assert "CLR.restyle_preflight()" in src and 'add("restyle", rok, rwhy, critical=False)' in src and src.index('add("clip model", cok') < src.index('add("restyle", rok')


def test_12_the_paid_call_counter_sees_every_restyle_bought(tmp_path, monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import media as MD
    src = _piece(tmp_path, setting, "EPB22"); _open(monkeypatch, setting); c = watch(monkeypatch)
    MD.restyle(src, "p", str(tmp_path / "r1.mp4"), "EPB22", 1.5); MD.restyle(src, "p", str(tmp_path / "r2.mp4"), "EPB22", 1.5)
    assert c["restyle"] == 2, c


def test_c9_the_identity_judgement_is_booked_to_the_film_it_judges(tmp_path, monkeypatch, setting):
    import cv2
    from whatifs import sheets as SH, models as MO, living as LV, anim as ANIM, publish as PUB
    seen = []
    monkeypatch.setattr(MO, "ask_vision", lambda *a, **k: seen.append(a[3] if len(a) > 3 else k.get("episode")) or {"score": 8})
    a, b = _art(tmp_path / "a.png", 64, 64), _art(tmp_path / "b.png", 64, 64, seed=2)
    assert SH.identity_score(a, b, "VALE") == 8.0 and seen == ["SHEETS"], seen                              # the masters' own call: three arguments, "SHEETS"
    src = _piece(tmp_path, setting, "EPB33"); _open(monkeypatch, setting); seen.clear()
    assert LV.restyle(src, "DIRECTOR", "EPB33", 0, 0, 1.5) is True and seen == ["EPB33"], seen             # the restyle's judge is booked to its film
    monkeypatch.setattr(LV, "FAKE", False); seen.clear(); shutil.rmtree(os.path.join(core.WORK, "EPB33v"), ignore_errors=True)
    monkeypatch.setattr(ANIM, "gemini_image", lambda prompt, refs, p, ep, aspect="16:9": cv2.imwrite(p, cv2.imread(refs[0])))
    monkeypatch.setattr(PUB, "drive_upload", lambda p, name, public=False: ("fid", ""))
    LV.variants("GRIMM", "neutral", a, "EPB33v"); assert seen == ["EPB33v", "EPB33v"], seen                 # the living stills' judge too


# ------------------------------------------------------------------ RULINGS_U1b PART 3: C11 and C12
def test_c11_every_attempt_is_a_row_counted_by_the_cap_and_one_film_asks_at_most_its_tries(tmp_path, monkeypatch, setting):
    import cv2
    from whatifs import living as LV, anim as ANIM, sheets as SH, publish as PUB
    for e in ("EPC11", "EPC11n", "EPC11b", "EPC11e", "EPC11z"): shutil.rmtree(os.path.join(core.WORK, e), ignore_errors=True)
    base = _art(tmp_path / "vale.png", 768, 1024); _lock("VALE", base); setting("LIVING_CHARACTERS_ON", "TRUE")
    asked, fail = [], [False]

    def img(prompt, refs, p, ep, aspect="16:9"):
        asked.append(ep)
        if fail[0]: raise RuntimeError("planted picture call")
        cv2.imwrite(p, cv2.imread(refs[0]))
    monkeypatch.setattr(LV, "FAKE", False); monkeypatch.setattr(ANIM, "gemini_image", img)
    monkeypatch.setattr(SH, "identity_score", lambda a, b, c, episode=None: 3)
    monkeypatch.setattr(PUB, "drive_upload", lambda p, name, public=False: ("fid", ""))
    plus = lambda: [(r["status"], r["file"]) for r in core.store().rows("Character_Sheets") if "+" in str(r.get("expression", ""))]
    sheet0, used0 = LV._sheet_rows("VALE"), SH.used()
    assert LV.variants("VALE", "neutral", base, "EPC11") == (None, None) and LV.variants("VALE", "neutral", base, "EPC11") == (None, None)
    assert plus() == [("REJECTED", "")] * 2 and len(asked) == 2, (plus(), asked)                           # (1) two rows, two pictures; the second call asks none
    assert LV.variants("VALE", "shocked", base, "EPC11") == (None, None) and len(asked) == 2, asked        # (2) a third slot in the same film asks nothing
    setting("LIVING_VARIANTS_CAP_INR", "10")
    assert LV.variants("VALE", "neutral", base, "EPC11n") == (None, None) and len(asked) == 2 and LV.cap_room() == 0, asked      # (3) the fileless rows are counted
    assert LV._sheet_rows("VALE") == sheet0 and SH.used() == used0                                          # (4) a fileless row is never art, never a made image
    setting("LIVING_VARIANTS_CAP_INR", "150"); fail[0] = True
    assert LV.variants("VALE", "neutral", base, "EPC11b") == (None, None) and len(asked) == 4, asked
    assert plus() == [("REJECTED", "")] * 2 + [("TRIED", "")] * 2, plus()                                   # (5) a failed call is a row too ...
    assert LV.variants("VALE", "neutral", base, "EPC11b") == (None, None) and len(asked) == 4, asked        # ... and in the film's count, written BEFORE the call
    fail[0] = False; os.makedirs(os.path.join(core.WORK, "EPC11e"), exist_ok=True); open(os.path.join(core.WORK, "EPC11e", "variant_tries.txt"), "w").close()
    assert LV.variants("VALE", "neutral", base, "EPC11e") == (None, None) and len(asked) == 4, asked        # (6) a count that cannot be read asks nothing
    setting("PRICE_GEM_IMAGE_USD", "0"); assert LV.cap_room() == 999                                       # (7) a free picture divides nothing ...
    LV.variants("VALE", "neutral", base, "EPC11z"); LV.variants("VALE", "neutral", base, "EPC11z"); assert len(asked) == 6, asked      # ... the film's count still bounds it


def test_c12_the_variants_and_their_judge_are_lines_of_the_estimate(setting):
    from whatifs import costguard as CG
    t0 = CG.total(CG.lines("long"))
    _lock("VALE", "drive:test-vale")                                                                        # his lock in "neutral", no variant row
    L = {l["key"]: l for l in CG.lines("long")}
    v, j = L["living_variants"], L["living_identity"]
    assert v["n"] == 2 and v["inr"] == 13.27 and v["calls"] == {"image_ref": 2} and v["item"] == "image_ref" and v["stage"] == "visuals", v
    assert j["n"] == 2 and j["inr"] == 80.0 and j["calls"] == {"vision": None} and j["stage"] == "ai_writing" and j["item"] is None, j
    assert round(CG.total(CG.lines("long")) - t0, 2) == 93.27
    assert {"living_variants", "living_identity"} <= {l["key"] for l in CG.lines("ladder")}


def test_c12b_the_variant_lines_stand_only_where_a_picture_can_still_be_bought(setting):
    from whatifs import costguard as CG, living as LV
    keys = lambda: {l["key"]: l["n"] for l in CG.lines("long") if l["key"] in ("living_variants", "living_identity")}
    _lock("VALE", "drive:test-vale", "2026-11-18T00:00:00Z (default)")
    assert keys() == {} and LV.variant_room() == 0                                                          # (1) a lock by default only: no line
    core.store().update_where("Character_Sheets", {"hash": "VALEneutral"}, {"approved_at": "2026-11-18T00:00:00Z"})
    assert keys() == {"living_variants": 2, "living_identity": 2}                                           # (2) his lock, no picture: both lines, 2
    setting("LIVING_VARIANT_TRIES", "0"); assert keys() == {}; setting("LIVING_VARIANT_TRIES", "2")        # (4) a film asks none: no line
    core.store().append("Character_Sheets", [{"ts": core.iso(), "character": "GRIMM", "expression": "smug+eyes", "hash": "GRIMMsmug+eyes-tried-EPX-1", "prompt": "",
                                              "file": "", "status": "TRIED", "approved_at": ""}])
    setting("LIVING_VARIANTS_CAP_INR", "5"); assert keys() == {}; setting("LIVING_VARIANTS_CAP_INR", "150")      # (5) the cap passed (6.63 over 5): no line
    for kind in ("eyes", "mouth"):
        core.store().append("Character_Sheets", [{"ts": core.iso(), "character": "VALE", "expression": f"neutral+{kind}", "hash": f"VALEneutral+{kind}", "prompt": "",
                                                  "file": f"drive:test-{kind}", "status": "AUTO", "approved_at": ""}])
    assert keys() == {}                                                                                     # (3) both pictures made: no line


# ------------------------------------------------------------------ CR-DRAWN-b round 1, finding 2: the record says the rule the mouth really followed
def test_6b_the_record_says_flap_when_the_voice_rule_could_not_act(tmp_path, setting):
    """CR-DRAWN-b 2: `mouth_rule` is the rule `speaking` really used (one helper both read) - a cutaway past the WAV's end, or over a silent stretch,
    gets an envelope of zeros, flaps and says "flap"; a stretch with a voice says "voice"."""
    from whatifs import living as LV, render as RN
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", _art(tmp_path / "vale.png", 640, 360))
    fps, s0, sr = RN.fps(), 40.0, 8000; n = int(2 * fps)
    words = [{"w": "later", "s": s0 + 12.5, "e": s0 + 13.5}]
    def wav_(name, secs, loud):
        p = str(tmp_path / name)
        with wave.open(p, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
            a = np.zeros(int(secs * sr), dtype=np.int16)
            if loud: a[int((s0 + 12.9) * sr):int((s0 + 13.5) * sr)] = 12000
            f.writeframes(a.tobytes())
        return p
    for name, secs, loud, want in (("short.wav", 10.0, True, "flap"), ("silent.wav", s0 + 15, False, "flap"), ("voice.wav", s0 + 15, True, "voice")):
        w_ = wav_(name, secs, loud); env = LV.envelope(w_, s0 + 12, fps, n)
        assert env and len(env) == n, (name, env)                                             # an envelope of zeros is still a list: the old record said voice
        r = LV.render("DIRECTOR", "Really? Prove it.", words, s0 + 12, str(tmp_path / f"{name}.mp4"), n, "EPB16b", seed="s", wav=w_)
        assert r and r["mouth_rule"] == want and LV.USED[-1]["mouth_rule"] == want, (name, r)
        assert (LV.voice_median(words, s0 + 12, fps, n, env) > 0) == (want == "voice"), name


def test_cr2_1_a_cutaway_with_no_mouth_picture_names_no_mouth_rule(tmp_path, monkeypatch, setting):
    """CODEREVIEW_DRAWN-b_2 finding 1: with no mouth picture (`variants` gave none) the mouth never moves, so the record says "none" - never "voice" over
    a loud stretch, never "flap": the rule the mouth really followed (line 228's own condition)."""
    from whatifs import living as LV, render as RN
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", _art(tmp_path / "vale.png", 640, 360))
    fps, s0, sr = RN.fps(), 40.0, 8000; n = int(2 * fps)
    words = [{"w": "later", "s": s0 + 12.5, "e": s0 + 13.5}]
    w_ = str(tmp_path / "voice.wav")
    with wave.open(w_, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        a = np.zeros(int((s0 + 15) * sr), dtype=np.int16); a[int((s0 + 12.9) * sr):int((s0 + 13.5) * sr)] = 12000; f.writeframes(a.tobytes())
    assert LV.voice_median(words, s0 + 12, fps, n, LV.envelope(w_, s0 + 12, fps, n)) > 0                     # the voice rule COULD act on this stretch
    monkeypatch.setattr(LV, "variants", lambda *a, **k: (None, None))
    r = LV.render("DIRECTOR", "Really? Prove it.", words, s0 + 12, str(tmp_path / "nm.mp4"), n, "EPB16c", seed="s", wav=w_)
    assert r and r["mouth_frames"] == 0 and r["mouth_rule"] == "none" and LV.USED[-1]["mouth_rule"] == "none", r


def test_cr2_1b_an_over_changed_mouth_picture_names_no_mouth_rule(tmp_path, monkeypatch, setting):
    """READERS_DRAWN-b_tg 1: a mouth picture that changed the whole frame is thrown out by change_mask (LIVING_MAX_CHANGE_SHARE), so the mouth never moves
    and the record says "none" though `variants` gave a picture."""
    from whatifs import living as LV, render as RN
    setting("LIVING_CHARACTERS_ON", "TRUE"); _lock("VALE", _art(tmp_path / "vale.png", 640, 360))
    fps, s0, sr = RN.fps(), 40.0, 8000; n = int(2 * fps)
    words = [{"w": "later", "s": s0 + 12.5, "e": s0 + 13.5}]
    w_ = str(tmp_path / "voice.wav")
    with wave.open(w_, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        a = np.zeros(int((s0 + 15) * sr), dtype=np.int16); a[int((s0 + 12.9) * sr):int((s0 + 13.5) * sr)] = 12000; f.writeframes(a.tobytes())
    assert LV.voice_median(words, s0 + 12, fps, n, LV.envelope(w_, s0 + 12, fps, n)) > 0                     # the voice rule COULD act on this stretch
    import cv2
    cv2.imwrite(str(tmp_path / "allover.png"), np.random.default_rng(0).integers(0, 256, (360, 640, 3), dtype=np.uint8))      # the art's own shape, changed everywhere
    monkeypatch.setattr(LV, "variants", lambda *a, **k: (None, str(tmp_path / "allover.png")))
    r = LV.render("DIRECTOR", "Really? Prove it.", words, s0 + 12, str(tmp_path / "om.mp4"), n, "EPB16d", seed="s", wav=w_)
    assert r and r["variants"] == [False, True] and r["mouth_frames"] == 0 and r["mouth_rule"] == "none" and LV.USED[-1]["mouth_rule"] == "none", r


def test_a_bought_variant_whose_face_cannot_be_judged_is_not_filed(tmp_path, monkeypatch, setting):
    """RULINGS_U2k 1: on the paid road a blink / mouth picture whose identity score is None (no key, a refused call, no score) is never filed - a TRIED
    row (asked, not judged bad), its slot None, a WARN that says so - as `restyle` refuses one; a judged face below the bar stays REJECTED, one above is filed."""
    import cv2
    from whatifs import living as LV, anim as ANIM, sheets as SH, publish as PUB
    for e in ("EPU2k1n", "EPU2k1r", "EPU2k1f"): shutil.rmtree(os.path.join(core.WORK, e), ignore_errors=True)
    base = _art(tmp_path / "vale.png", 768, 1024); _lock("VALE", base); setting("LIVING_CHARACTERS_ON", "TRUE"); setting("LIVING_VARIANTS_CAP_INR", "1000")
    score, warns, real_log = [None], [], LV.log
    monkeypatch.setattr(LV, "FAKE", False)
    monkeypatch.setattr(ANIM, "gemini_image", lambda prompt, refs, p, ep, aspect="16:9": cv2.imwrite(p, cv2.imread(refs[0])))
    monkeypatch.setattr(SH, "identity_score", lambda a, b, c, episode=None: score[0])
    monkeypatch.setattr(PUB, "drive_upload", lambda p, name, public=False: ("fid", ""))
    monkeypatch.setattr(LV, "log", lambda m, *a, **k: (warns.append(m) if "WARN" in a else None, real_log(m, *a, **k))[1])
    plus = lambda: [(r["expression"], r["status"], r["file"]) for r in core.store().rows("Character_Sheets")
                    if str(r.get("character", "")).upper() == "VALE" and "+" in str(r.get("expression", ""))]
    assert LV.variants("VALE", "neutral", base, "EPU2k1n") == (None, None), plus()                          # a face that could not be judged fills no slot ...
    assert plus() == [("neutral+eyes", "TRIED", ""), ("neutral+mouth", "TRIED", "")], plus()                # ... its row is TRIED, with no file
    assert sum("could not be judged" in w for w in warns) == 2, warns
    score[0] = 3
    assert LV.variants("VALE", "neutral", base, "EPU2k1r") == (None, None)                                  # a judged face below the bar: REJECTED, as before
    assert plus()[2:] == [("neutral+eyes", "REJECTED", ""), ("neutral+mouth", "REJECTED", "")], plus()
    assert sum("rejected (identity 3)" in w for w in warns) == 2, warns
    score[0] = 9
    e_, m_ = LV.variants("VALE", "neutral", base, "EPU2k1f")                                                # a face judged above the bar: filed
    assert e_ and m_ and os.path.exists(e_) and os.path.exists(m_), (e_, m_)
    assert plus()[4:] == [("neutral+eyes", "AUTO", "drive:fid"), ("neutral+mouth", "AUTO", "drive:fid")], plus()
