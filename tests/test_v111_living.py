"""v11.1 (K167): living characters - the approved character in every reaction cutaway, blinking, breathing and talking. No keys, no network."""
import os, subprocess, json
import numpy as np, pytest
from whatifs import core, living as LV, contract as CON

def _sheet(tmp_path, char="VALE", expr="neutral"):
    import cv2
    p = str(tmp_path / f"{char}_{expr}.png"); img = np.full((360, 640, 3), 90, np.uint8)
    cv2.circle(img, (320, 170), 90, (180, 160, 140), -1); cv2.circle(img, (290, 150), 9, (20, 20, 20), -1); cv2.circle(img, (350, 150), 9, (20, 20, 20), -1)
    cv2.imwrite(p, img)
    core.store().append("Character_Sheets", [{"ts": core.iso(), "character": char, "expression": expr, "hash": char + expr, "file": p, "status": "LOCKED"}])
    return p

def test_no_locked_sheet_means_fallback_and_honest_na(tmp_path, setting):
    assert LV.expression_for("DIRECTOR", "hi") == (None, None)
    assert LV.render("DIRECTOR", "hi", [], 0, str(tmp_path / "x.mp4"), 30, "E") is None
    assert CON.p_living({"shots": [{"type": "reaction"}]})[0] == CON.NA

def test_a_living_shot_blinks_talks_and_only_moves_eyes_and_mouth(tmp_path, setting):
    pytest.importorskip("cv2"); import cv2
    base = _sheet(tmp_path); LV.USED.clear()
    words = [{"w": "hello", "s": 0.5, "e": 1.1}, {"w": "there", "s": 1.3, "e": 1.9}]
    out = str(tmp_path / "live.mp4")
    r = LV.render("DIRECTOR", "Really? Prove it.", words, 0.0, out, 150, "EPL", seed="s1")
    assert r and r["character"] == "VALE" and r["blinks"] >= 3 and r["mouth_frames"] >= 6 and r["variants"] == [True, True]
    assert os.path.exists(out) and len(LV.USED) == 1
    ev = [x for x in core.store().rows("Character_Sheets") if x["expression"] == "neutral+eyes"][0]["file"]
    m, _ = LV.change_mask(cv2.imread(base), cv2.imread(ev)); assert 0 < m.mean() < 0.08          # only a small area changes (no flicker)
    assert CON.p_living({"shots": [{"type": "reaction"}]})[0] == "PASS"

def test_a_variant_that_changes_everything_is_never_used(tmp_path, setting):
    import cv2
    a = np.full((100, 100, 3), 50, np.uint8); b = np.full((100, 100, 3), 200, np.uint8)
    assert LV.change_mask(a, b) is None

def test_fallback_to_silhouette_fails_the_contract_once_sheets_are_locked(tmp_path, setting):
    _sheet(tmp_path); LV.USED.clear()
    st, ev = CON.p_living({"shots": [{"type": "reaction"}, {"type": "reaction"}]})
    assert st == "FAIL" and "silhouette" in ev
