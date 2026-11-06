"""v9.1 stage C: hero-still reels (best still, seamless loop, caps, flag off = nothing), character grammar, courtroom composition."""
import os, subprocess, json
import numpy as np, cv2
import pytest
from whatifs import core, herostill as HS, showfx as SFX, manage as MG, v91 as V91

def _imgs(tmp):
    flat = np.full((360, 640, 3), 90, np.uint8); flat += (np.random.default_rng(1).random((360, 640, 1)) * 12).astype(np.uint8)
    hero = np.full((360, 640, 3), 20, np.uint8); cv2.circle(hero, (330, 170), 70, (240, 240, 250), -1); cv2.circle(hero, (330, 170), 110, (90, 140, 230), 6)
    ps = []
    for n, im in (("flat", flat), ("hero", hero)):
        p = os.path.join(tmp, n + ".png"); cv2.imwrite(p, im); ps.append(p)
    return ps

def _master(tmp, d=40):
    m = os.path.join(tmp, "m.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=f=200:d={d}", "-f", "lavfi", "-i", f"color=c=gray:s=64x36:d={d}", "-shortest", m], check=True)
    return m

def test_poster_score_picks_the_focal_still(tmp_path):
    ps = _imgs(str(tmp_path)); best = HS.pick_best(ps)
    assert best[0].endswith("hero.png") and best[1] > HS.poster_score(cv2.imread(ps[0]))[0]

def test_templates_rotate_never_twice(setting):
    seen = []
    for _ in range(4):
        t = HS.next_template(); seen.append(t); setting("HERO_REEL_LAST_TEMPLATE", t)
    assert all(a != b for a, b in zip(seen, seen[1:]))

def test_build_is_a_seamless_capped_loop(tmp_path):
    ps = _imgs(str(tmp_path)); out = HS.build(ps[1], "IT GLOWS", _master(str(tmp_path)), 10.0, 14.0, str(tmp_path / "r.mp4"), seed="E", size=(180, 320))
    assert out and os.path.exists(out)
    cap = cv2.VideoCapture(out); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    assert 15 <= n / fps <= 25.5
    ok, first = cap.read(); cap.set(cv2.CAP_PROP_POS_FRAMES, n - 1); ok2, last = cap.read(); cap.release()
    assert ok and ok2 and np.abs(first.astype(int) - last.astype(int)).mean() < 12          # end frame close to the start frame (loop)
    a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name", "-of", "csv=p=0", out], capture_output=True, text=True)
    assert "aac" in a.stdout

def test_flag_off_makes_nothing_and_on_files_one(monkeypatch, setting, tmp_path):
    MG.setup(); ps = _imgs(str(tmp_path)); m = _master(str(tmp_path))
    units = [{"start": 10.0, "end": 12.0, "show": ["[CLIPBAIT]"]}, {"start": 12.0, "end": 15.0, "show": ["[/CLIPBAIT]"]}]
    assert HS.make_for_episode("EPH", str(tmp_path), ps, m, units, "HOOK") is None
    setting("HERO_STILL_REELS_ON", "TRUE"); monkeypatch.setattr(core, "SMALL", True, raising=False)
    r = HS.make_for_episode("EPH", str(tmp_path), ps, m, units, "HOOK"); assert r and os.path.exists(r)
    setting("V91_SAFE_MODE", "TRUE"); assert HS.make_for_episode("EPH2", str(tmp_path), ps, m, units, "HOOK") is None

def test_hero_reel_failure_never_blocks(monkeypatch, setting, tmp_path):
    setting("HERO_STILL_REELS_ON", "TRUE"); V91._OFF.clear()
    monkeypatch.setattr(HS, "pick_best", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected")))
    assert HS.make_for_episode("EPF", str(tmp_path), [], "", [], "") is None and not V91.on("HERO_STILL_REELS_ON", "EPF"); V91._OFF.clear()

def test_grammar_is_per_character_and_deterministic():
    im = np.zeros((90, 80, 3), np.uint8); im[20:70, 20:60] = 150
    g = HS.apply_grammar(im, "SKEPTIC", 1.0); assert np.array_equal(g, HS.apply_grammar(im, "SKEPTIC", 1.0)) and not np.array_equal(g, im)
    j = HS.apply_grammar(im, "JUDGE", 1.0); assert j[45, 40, 2] > j[45, 40, 0]                # warm amber (more red than blue)
    v = HS.apply_grammar(im, "DIRECTOR", 1.0); assert v[45, 40, 0] > v[45, 40, 2]             # teal-steel (more blue than red)

def test_courtroom_cut_puts_the_speaker_large():
    set_ = np.full((180, 320, 3), 40, np.uint8); por = {k: np.full((60, 45, 3), c, np.uint8) for k, c in (("JUDGE", 200), ("SKEPTIC", 120), ("DIRECTOR", 80))}
    a = HS.courtroom(set_, por, "SKEPTIC", 0.5); b = HS.courtroom(set_, por, "DIRECTOR", 0.5)
    assert (a != set_).any() and not np.array_equal(a, b)

def test_overlay_portrait_uses_grammar_only_when_on(setting):
    us = [{"start": 0.0, "end": 26.0, "speaker": "DIRECTOR", "show": []}, {"start": 30.0, "end": 40.0, "speaker": "SKEPTIC", "show": []}]   # after the cold open
    por = {"SKEPTIC": np.full((80, 60, 3), 160, np.uint8)}
    fr = np.full((360, 640, 3), 60, np.uint8)
    setting("CHAR_GRAMMAR_ON", "FALSE"); a = SFX.ShowOverlay(us, {}, 640, 360, 30, portraits=dict(por)).apply(fr.copy(), 35 * 30)
    setting("CHAR_GRAMMAR_ON", "TRUE"); b = SFX.ShowOverlay(us, {}, 640, 360, 30, portraits=dict(por)).apply(fr.copy(), 35 * 30)
    assert not np.array_equal(a, b)
