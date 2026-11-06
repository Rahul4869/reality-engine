"""v9 stage 3c + the integration audit: feature-flag matrix (all on / all off / each alone), API failure paths (400/401/403/429/5xx/timeouts)
with bounded attempts and no duplicate paid calls, the cache_control fallback, batches, character sheets (lifetime cap, idempotent, lock), the audio
cache and the Kling motion boost."""
import json, os, subprocess
import numpy as np
import pytest
from whatifs import core, show as SHOW, showfx as SFX, models as M, fakes as F, sheets as SH, manage as MG, tts_gemini as T, render as RN

FLAGS = ["FOUND_FOOTAGE_ON", "HUD_ON", "JURY_METER_ON", "EXHIBIT_PINS_ON", "TEACUP_ON", "LETTERBOX_ON", "CHARACTER_THEATER_ON", "MOTION_BOOST_ON"]
PLAN = SHOW.validate(json.loads(F.fake_reply("showrunner", ""))["show_plan"], {}, [])[0]

def _units():
    us = [{"start": float(i * 4), "end": float(i * 4 + 3.5), "text": "x", "speaker": "DIRECTOR" if i % 2 else "SKEPTIC", "show": []} for i in range(20)]
    us[1]["show"] = ["[EXHIBIT A]"]; us[9]["show"] = ["[JURY]", "[METER +2 VALE]"]; us[10]["show"] = ["[CLIPBAIT]"]; us[11]["show"] = ["[/CLIPBAIT]", "[EXHIBIT C]"]
    us[12]["show"] = ["[JURY]"]; us[14]["show"] = ["[JURY]"]
    return us

@pytest.mark.parametrize("combo", ["all_on", "all_off"] + FLAGS)
def test_flag_matrix_render_and_qc_never_crash(setting, combo):
    for f in FLAGS: setting(f, "TRUE" if combo == "all_on" else "FALSE")
    if combo in FLAGS: setting(combo, "TRUE")
    so = SFX.ShowOverlay(_units(), PLAN, 160, 90, 10, seed="EPM", hero_spans=[(40, 44)], impacts=[41], portraits={"DIRECTOR": np.full((40, 30, 3), 90, np.uint8)})
    fr = np.full((90, 160, 3), 120, np.uint8)
    for t in (1, 6, 33, 42, 47, 70): assert so.apply(fr.copy(), t * 10).shape == fr.shape
    assert SFX.show_qc(_units(), PLAN, so.cups) == []

def test_show_mode_off_restores_v811_everywhere(setting):
    setting("SHOW_MODE", "off")
    from whatifs import room as ROOM, episode as EP
    assert ROOM._show_block() == "" and ROOM._pkg_extra() == "" and ROOM._reel_extra({}) == "" and ROOM._show_writer({"show_plan": PLAN}) == ""
    assert SHOW.apply_to_spine({"premise": "p"}, "E") == {"premise": "p"} and "JUDGE" not in (EP.speaker_blends() or {})

# ---------------------------------------------------------------- failure paths: bounded, no duplicate paid calls
@pytest.mark.parametrize("code", [400, 401, 403, 429, 500, 529, "timeout"])
def test_api_failures_are_bounded_and_never_double_billed(monkeypatch, code):
    posts = []
    def post(body, headers):
        posts.append(1)
        if code == "timeout": raise TimeoutError("read timed out")
        return F._Resp(code, {"error": {"message": f"status {code}"}})
    monkeypatch.setattr(M, "FAKE", False); monkeypatch.setattr(M, "_post", post); monkeypatch.setattr(M.time, "sleep", lambda s: None)
    monkeypatch.setattr(M, "_gemini", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("gemini down")))
    for n in ("claude_allowed", "opus_allowed"): monkeypatch.setattr("whatifs.governor." + n, lambda: True)
    monkeypatch.setattr("whatifs.governor.monthly_cap_reached", lambda **k: False)
    before = len(core._cost_buf)
    with pytest.raises(RuntimeError): M.ask("humanize", "sys", "p")
    assert len(posts) <= 2 * 2 and len(core._cost_buf) == before                                  # 2 Claude models x 2 attempts at most; nothing billed

def test_cache_control_rejection_falls_back_uncached_for_the_job(monkeypatch):
    seen = []
    def post(body, headers):
        seen.append(isinstance(body["system"], list))
        if isinstance(body["system"], list): return F._Resp(400, {"error": {"message": "system.0.cache_control: ttl not supported"}})
        return F._Resp(200, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {"input_tokens": 3, "output_tokens": 1}})
    monkeypatch.setattr(F.FAKE_ANTHROPIC, "post", post)
    pk = P_ = __import__("whatifs.prompts", fromlist=["x"]).pack(__import__("whatifs.prompts", fromlist=["x"]).MEMO, episode={"spine": "x " * 4000}, role="R")
    assert M._claude("sonnet", pk, "q", 100, None, False, "E", "") == "ok" and seen == [True, False]
    assert M._claude("sonnet", pk, "q", 100, None, False, "E", "") == "ok" and seen[-1] is False and M.model("sonnet") in M._NO_CACHE
    M._NO_CACHE.clear()

def test_batch_failure_runs_the_normal_call_once(monkeypatch, setting):
    calls = []
    monkeypatch.setattr(M, "FAKE", False)
    monkeypatch.setattr(M.requests, "post", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("batch api down")))
    monkeypatch.setattr(M, "ask", lambda *a, **k: (calls.append(a[0]), {"ok": 1})[1])
    for n in ("claude_allowed",): monkeypatch.setattr("whatifs.governor." + n, lambda: True)
    monkeypatch.setattr("whatifs.governor.monthly_cap_reached", lambda **k: False)
    assert M.ask_batch("brief", "s", "p", want_json=False) == {"ok": 1} and calls == ["brief"]
    setting("BATCH_ON", "FALSE"); M.ask_batch("brief", "s", "p"); assert calls == ["brief", "brief"]

# ---------------------------------------------------------------- character sheets
def test_sheets_lifetime_cap_idempotent_and_lock(monkeypatch, setting):
    MG.setup(); setting("SHEET_EXPRESSIONS", "2"); setting("CHARACTER_SHEET_IMAGE_CAP", "4"); mails = []
    from whatifs import publish as PUB
    monkeypatch.setattr(PUB, "email", lambda *a, **k: mails.append(1))
    r1 = SH.run(); assert r1["made"] == 4 and r1["skipped_cap"] == len(SH.plan()) - 4 and SH.used() == 4
    r2 = SH.run(); assert r2["made"] == 0 and SH.used() == 4                                     # cap reached: never more, never twice
    setting("CHARACTER_SHEET_IMAGE_CAP", "40"); r3 = SH.run(); assert r3["made"] == len(SH.plan()) - 4
    assert SH.run()["made"] == 0                                                                 # idempotent by content hash
    assert "locked" in SH.decide("APPROVE SHEET VALE") and ("VALE", "neutral") in SH.locked_portraits()
    assert "remakes" in SH.decide("REDO SHEET VALE neutral")
    with pytest.raises(SystemExit): SH.decide("DELETE EVERYTHING")
    assert all("chibi" in p["prompt"] and "no child" in p["prompt"] for p in SH.plan()) and not any(p["character"] == "ARCHIVIST" for p in SH.plan())

# ---------------------------------------------------------------- audio cache + motion boost
def test_audio_cache_never_pays_twice(monkeypatch):
    n = []
    monkeypatch.setattr(T, "synth", lambda turns, voices, ep=None: (n.append(1), (np.zeros(2400, np.float32), 0.1))[1])
    be = T.GeminiBackend({"DIRECTOR": ("Charon", "")}, episode="E")
    from whatifs.voice import parse_script
    us = parse_script("[DIRECTOR] Hello there.")
    be._request([0], us); be._request([0], us); assert len(n) == 1 and be.stats["cache_hits"] == 1

def test_motion_boost_stretches_without_freezing(tmp_path, setting):
    clip = str(tmp_path / "c.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=160x90:d=1:r=10", clip], check=True)
    setting("MOTION_BOOST_ON", "TRUE"); RN.set_overlay(None)
    out = RN.clip_segment(clip, str(tmp_path / "o.mp4"), int(2.4 * RN.fps()))
    assert abs(RN.probe_dur(out) - 2.4) < 0.3
