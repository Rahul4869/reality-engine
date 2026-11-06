"""v9 stage 2: show tags through voice parsing, the two-speaker TTS limit, the trial voices, the writer brief, the render devices and the show QC."""
import json, os, subprocess
import numpy as np
import pytest
from whatifs import core, show as SHOW, showfx as SFX, voice as V, tts_gemini as T, episode as EP, cast as CAST, manage as MG, room as ROOM, fakes as F

SCRIPT = ("[DIRECTOR] [calm] Observe the scene.\n[EXHIBIT A] [DIRECTOR] The record shows lift.\n[JURY] [JUDGE] Mm. Guilty or not?\n"
          "[CLIPBAIT] [SKEPTIC] Pillows do not fly! They never did... never! [/CLIPBAIT]\n[METER +2 vale] [Inspector Vale] Noted.\nDr. Grimm: Preposterous!\n[WITNESS] Entry filed.")

def test_tags_are_data_never_spoken_and_new_labels_parse():
    us = V.parse_script(SCRIPT)
    assert [u.speaker for u in us][:3] == ["DIRECTOR", "DIRECTOR", "JUDGE"] and {"JUDGE", "WITNESS", "SKEPTIC"} <= {u.speaker for u in us}
    assert not any("[" in u.text or "METER" in u.text or "CLIPBAIT" in u.text for u in us)
    sh = [x for u in us for x in u.show]
    assert sh.count("[CLIPBAIT]") == 1 and sh.count("[/CLIPBAIT]") == 1 and "[METER +2 VALE]" in sh and "[EXHIBIT A]" in sh and "[JURY]" in sh
    close = next(u for u in us if "[/CLIPBAIT]" in u.show); assert close.text == "never!"            # the closing tag sits on the line's end

def test_a_gemini_request_never_carries_more_than_two_speakers():
    us = V.parse_script("[DIRECTOR] a.\n[SKEPTIC] b.\n[JUDGE] c.\n[DIRECTOR] d.\n[SKEPTIC] e.")
    groups = T._pairs(list(range(len(us))), us)
    assert all(len({us[i].speaker for i in g}) <= 2 for g in groups) and sorted(i for g in groups for i in g) == list(range(len(us)))

def test_trial_voices_judge_and_witness_and_safe_fallback(setting):
    MG.setup(); b = SHOW.extra_blends(set())
    assert set(b) == {"JUDGE", "WITNESS"} and b["JUDGE"].parts != b["WITNESS"].parts and b["JUDGE"].lang == "b"
    b2 = SHOW.extra_blends({"Gacrux"}); assert b2["JUDGE"].gvoice == ""                  # a lead already uses it -> Kokoro fallback, never a clash
    core.store().update("Characters", "id", "ROSA", {"gvoice": "NotARealVoice"}); assert SHOW.extra_blends(set())["JUDGE"].gvoice == ""
    setting("SHOW_MODE", "off"); bl = EP.speaker_blends() or {}; assert "JUDGE" not in bl

def test_core_cast_only_no_guest_rotation(setting):
    MG.setup(); import random
    rs = CAST.rows(); ex = [r for r in rs if r["role"] == "expert"]; gu = [r for r in rs if r["role"] == "guest"]
    if not ex or not gu: pytest.skip("cast placeholders without voices")
    picks = {json.dumps(CAST.pick(random.Random(i), [])) for i in range(6)}; assert len(picks) == 1
    assert ROOM.guest_brief({"cast": CAST.pick(random.Random(1), []), "guest": "x"}) == ""

def test_writer_gets_the_trial_brief_and_off_does_not():
    plan = SHOW.validate(json.loads(F.fake_reply("showrunner", ""))["show_plan"], {}, [])[0]
    b = ROOM._show_writer({"show_plan": plan})
    assert "REALITY ON TRIAL" in b and "[JUDGE] = Nana Rosa" in b and "[CLIPBAIT]" in b and '"exhibits"' in b
    assert not SHOW.ip_hits(b.split("SHOW PLAN")[0])

def _units():
    us = [{"start": float(i * 4), "end": float(i * 4 + 3.5), "text": "x", "speaker": "DIRECTOR", "show": []} for i in range(20)]
    us[1]["show"] = ["[EXHIBIT A]"]; us[9]["show"] = ["[JURY]", "[METER +2 VALE]"]; us[10]["show"] = ["[EXHIBIT B]", "[CLIPBAIT]"]; us[11]["show"] = ["[/CLIPBAIT]"]
    us[12]["show"] = ["[METER -1 GRIMM]", "[EXHIBIT C]"]; us[14]["show"] = ["[JURY]"]
    return us

PLAN = {"exhibits": [{"id": "A", "kind": "RECON", "credit": ""}, {"id": "B", "kind": "DATA", "credit": "NASA"}, {"id": "C", "kind": "RECON", "credit": ""}],
        "verdict": {"winner": "vale"}, "intensity": 3, "teacup_scenes": ["A", "C"], "hud_spec": [{"t": 6, "type": "scale", "label": "Height", "value": 10, "unit": "m"}]}

def test_overlay_draws_every_device_deterministically():
    us = _units(); so = SFX.ShowOverlay(us, PLAN, 320, 180, 30, seed="EPX", hero_spans=[(40, 44)], impacts=[41])
    assert so.active() and so.recon[0][0] == 0.0 and any(a <= 50 < b for a, b in so.recon) and so.meter_at(60) == 1
    assert len(so.cups) >= 2 and all(c["t"] >= 30 for c in so.cups) and all(abs(g - 41) >= 1 for g in so.glitch_at)
    fr = np.full((180, 320, 3), 120, np.uint8)
    for t in (2, 7, 37, 42, 50): out = so.apply(fr.copy(), int(t * 30)); assert out.shape == fr.shape
    a = so.apply(fr.copy(), 37 * 30); b = SFX.ShowOverlay(us, PLAN, 320, 180, 30, seed="EPX").apply(fr.copy(), 37 * 30); assert np.array_equal(a, b)
    assert so.apply(fr.copy(), 42 * 30)[:10].max() == 0                                  # letterbox on the hero moment

def test_show_qc_on_the_voiced_timeline():
    us = _units(); assert SFX.show_qc(us, PLAN, [{"t": 31}]) == []
    us[9]["show"] = ["[JURY]", "[METER -3 GRIMM]"]; codes = [c for c, _ in SFX.show_qc(us, PLAN, [{"t": 12}])]
    assert "meter_verdict" in codes and "teacup_early" in codes
    us[2]["show"] = ["[JURY]"]; assert "jury_early" in [c for c, _ in SFX.show_qc(us, PLAN)]
    us[11]["show"] = []; assert "clipbait" in [c for c, _ in SFX.show_qc(us, PLAN)]

def _video(tmp_path, frames, name):
    p = str(tmp_path / name); w = __import__("cv2").VideoWriter(p, __import__("cv2").VideoWriter_fourcc(*"mp4v"), 30, (64, 36))
    for f in frames: w.write(f)
    w.release(); return p

def test_photosensitivity_guard(tmp_path):
    calm = [np.full((36, 64, 3), 100 + (k % 30), np.uint8) for k in range(90)]
    assert SFX.photosensitivity(_video(tmp_path, calm, "calm.mp4")) == []
    strobe = [np.full((36, 64, 3), 230 if (k // 2) % 2 else 20, np.uint8) for k in range(90)]
    assert SFX.photosensitivity(_video(tmp_path, strobe, "strobe.mp4"))[0][0] == "photosensitive_flash"
    red = [np.dstack([np.zeros((36, 64), np.uint8), np.zeros((36, 64), np.uint8), np.full((36, 64), 230 if (k // 3) % 2 else 0, np.uint8)]) for k in range(90)]
    assert any(c == "red_flash" for c, _, _ in SFX.photosensitivity(_video(tmp_path, red, "red.mp4")))

def test_room_runs_the_tag_check_with_one_bounded_fix(monkeypatch):
    MG.setup(); from whatifs.sampler import draw as DRAW
    calls = []; real = ROOM.ask
    monkeypatch.setattr(ROOM, "ask", lambda role, *a, **k: (calls.append(role), real(role, *a, **k))[1])
    r = ROOM.run_room(DRAW("EPTAG", "collective"), "EPTAG")
    d = r if isinstance(r, dict) else {}
    assert calls.count("format") <= 2                                                     # at most one show-tag fix on top of the v8.10 format pass
