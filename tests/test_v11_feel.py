"""v11 Stage D (K161): the life layer makes stills read as alive; sound worlds follow the location; story sounds land on the right lines."""
import os, subprocess
import numpy as np
import pytest
from whatifs import core, render as RN, sound as SD, breakout as BRK

def _img(path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=960x540:duration=1", "-frames:v", "1", path], check=True, timeout=60)

def test_particle_layer_turns_a_flat_photo_with_a_camera_move_into_a_living_shot(tmp_path, setting, monkeypatch):
    """Acceptance (K161b): rendered at real 1080p, a photo with only a camera move and FLAT depth reads as a still; with the world particles
    every world reads >= 75% alive."""
    pytest.importorskip("cv2")
    monkeypatch.setattr(RN, "work_size", lambda: (1920, 1080)); monkeypatch.setattr(RN, "out_size", lambda: (1920, 1080))
    img = str(tmp_path / "s.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1920x1080:duration=1", "-frames:v", "1", img], check=True, timeout=60)
    depth = np.full((1080, 1920), 0.5, np.float32)
    setting("LIFE_LAYER_ON", "FALSE"); setting("CAMERA_MOTION", "dynamic")
    def share(on, world):
        setting("PARTICLES_ON", on); RN._LAST["move"] = None
        out = str(tmp_path / f"p_{on}_{world}.mp4")
        RN.parallax_segment(img, out, 4 * RN.fps(), seed=7, depth=depth, move="push_in", world=world)
        return BRK.aliveness(out)["alive_share"]
    assert share("FALSE", "court") <= 0.2
    got = {w: share("TRUE", w) for w in ("court", "lab", "office", "outdoor")}
    assert all(v >= 0.75 for v in got.values()), got

def test_sound_worlds_follow_the_speaker_and_hold_at_least_the_minimum(setting):
    units = [{"start": 0, "speaker": "SKEPTIC", "text": "Behold"}, {"start": 5, "speaker": "JUDGE", "text": "Order"},
             {"start": 14, "speaker": "JUDGE", "text": "Sit"}, {"start": 30, "speaker": "DIRECTOR", "text": "Rain again"}]
    amb = SD.worlds(units, 60)
    assert amb[0][0] == "crackle" and [a[0] for a in amb] == ["crackle", "hum", "rain"] and amb[1][1] >= 12

def test_story_sounds_land_on_the_right_lines_and_asmr_never_in_the_hook(setting):
    units = [{"start": 3, "text": "Exhibit A: NOAA, 2023."}, {"start": 40, "text": "Exhibit B: a ruler."},
             {"start": 60, "text": "Behold, Prototype No. 41!"}, {"start": 500, "text": "Here's what's true: the Moon stays."}]
    ev = SD.story_events(units)
    kinds = [k for k, _ in ev]
    assert ("paper", 40.0) in ev and all(t >= 30 for k, t in ev if k == "paper")      # no ASMR crinkle in the first 30 s
    assert "gavel" in kinds and "fizzle" in kinds
    for k in ("gavel", "paper", "fizzle"):
        a, b = SD.foley(k, "s1"), SD.foley(k, "s2")
        assert a.shape[1] == 2 and np.isfinite(a).all() and not np.allclose(a[: min(len(a), len(b))], b[: min(len(a), len(b))])   # fresh variant each use
    assert SD.KIND_GAIN["paper"] < 1 <= SD.KIND_GAIN["gavel"]

def test_the_detector_flags_a_flat_depth_camera_move_as_a_still(tmp_path, setting):
    pytest.importorskip("cv2")
    img = str(tmp_path / "s.png"); _img(img)
    setting("LIFE_LAYER_ON", "FALSE"); setting("PARTICLES_ON", "FALSE"); setting("CAMERA_MOTION", "dynamic"); RN._LAST["move"] = None
    out = str(tmp_path / "flat.mp4")
    RN.parallax_segment(img, out, 6 * RN.fps(), seed=7, depth=np.full((540, 960), 0.5, np.float32), move="push_in")
    assert BRK.aliveness(out)["alive_share"] <= 0.2                 # caught: this would fail the 'aliveness' contract check

