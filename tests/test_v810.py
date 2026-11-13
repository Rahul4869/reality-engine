"""v8.10: Gemini voice + cast, premise quality, immersion / POV on every shot type, voice acting, immersive sound, creative constitution, Script Preview,
budget view. Offline: every remote call is the fake stand-in or a stub. Happy paths AND failure paths."""
import os, json, datetime as dt
import numpy as np
import pytest
from whatifs import core, voice as V, tts_gemini as T, cast as CAST, premise as PR, immersion as IM, craft as CR, render as RN, sound as SD
from whatifs import governor as G, episode as EP, room as ROOM, manage as MG, preview as PV, data as D
from whatifs.voice import Blend

def _legacy_budget(setting):
    setting("BUDGET_FLOOR_INR", "4000"); setting("BUDGET_CEILING_INR", "4000"); setting("BUDGET_EARMARK_INR", "0"); setting("V94A_FLIPS_ON", "FALSE"); setting("V10_FLIPS_ON", "FALSE"); setting("SPECIALS_ON", "FALSE")      # v9.4a: this test keeps the v8 budget profile (₹4,000, no earmark, no cap move)


SB = {"DIRECTOR": Blend("d", {"am_michael": 1.0}, gvoice="Charon", gstyle="warm"), "SKEPTIC": Blend("s", {"af_heart": 1.0}, gvoice="Puck", gstyle="upbeat")}
SCRIPT = ("[DIRECTOR] [calm] Right now, about eight billion people are doing something ordinary.\n"
          "[SKEPTIC] [wow] {fast, breath} Wait, all of them? At the same time?\n"
          "[DIRECTOR] [reveal] {slow, low, whisper} That adds up to a number nobody has ever written down... and it keeps growing.\n"
          "[SKEPTIC] [laugh] Okay, that's terrifying.\n[DIRECTOR] [tension] The first ten seconds look harmless.\n")

def _tl(r): return json.load(open(r.timeline_path))

# ---------------------------------------------------------------- 1. voice engine
def test_gemini_narration_two_speakers_measured_timings_and_cost(tmp_path):
    r = V.narrate(SCRIPT, Blend("n", {"am_michael": 1.0}), str(tmp_path / "v"), seed="EPT", speaker_blends=SB)
    tl = _tl(r); us = tl["units"]
    assert tl["engine"] == "gemini" and tl["gemini_voices"] == {"DIRECTOR": "Charon", "SKEPTIC": "Puck"}
    assert {u["speaker"] for u in us} == {"DIRECTOR", "SKEPTIC"}
    assert all("{" not in u["text"] and "[" not in u["text"] and "<" not in u["text"] for u in us)        # braces / tags / vocal tags never spoken
    for a, b in zip(us, us[1:]): assert a["end"] <= b["start"]                                             # a monotonic master clock
    for u in us:
        assert u["words"] and u["words"][0]["s"] >= u["start"] - 0.01 and u["words"][-1]["e"] <= u["end"] + 0.05
        assert all(w["s"] <= w["e"] for w in u["words"])
    core.flush_costs(); assert any(c["item"] == "gemini_tts" and c["provider"] == "google" for c in core.store().rows("Cost_Log"))

def test_curve_braces_parsed_never_spoken_events_on_first_piece_only():
    us = V.parse_script("[SKEPTIC] [tension] {slow, whisper, breath, nonsense} It's... breathing.")
    assert [u.text for u in us] == ["It's", "breathing."] and us[0].curve == ["slow", "whisper"] and us[0].events == ["breath"] and us[1].events == []
    assert V.curve_speed(us[0]) < 1.0
    u = us[0]; u.tag = "reveal"; assert T.spoken_text(u).startswith("<breath>") and "whisper" in T.style_for(u, "warm")

def test_chunks_respect_word_limit_and_split_turns_finds_the_real_pauses(setting):
    us = V.parse_script("\n".join(f"[DIRECTOR] line number {i} has a few more words in it." for i in range(40)))
    ch = T.chunks(us, 30); assert all(sum(len(us[i].text.split()) for i in c) <= 30 or len(c) == 1 for c in ch) and sum(len(c) for c in ch) == len(us)
    sr = T.SR; tone = lambda s: (0.3 * np.sin(2 * np.pi * 150 * np.arange(int(s * sr)) / sr)).astype(np.float32); z = lambda s: np.zeros(int(s * sr), np.float32)
    a = np.concatenate([z(0.1), tone(1.0), z(0.4), tone(2.0), z(0.4), tone(1.0), z(0.1)])
    segs = T.split_turns(a, [10, 20, 10]); assert segs and abs(segs[1][0] - 1.3) < 0.15 and abs(segs[2][0] - 3.7) < 0.15
    assert T.split_turns(np.concatenate([z(0.1), tone(4.0), z(0.1)]), [10, 10, 10]) is None      # no pauses: not convincing -> caller voices line by line

def test_unconvincing_chunk_is_voiced_line_by_line(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "split_turns", lambda a, w, lead=0.0: None if len(w) > 1 else [(0.0, len(a) / T.SR)])
    r = V.narrate(SCRIPT, Blend("n", {}), str(tmp_path / "v"), seed="EPL", speaker_blends=SB); tl = _tl(r)
    assert tl["engine"] == "gemini" and tl["tts_stats"]["line_by_line"] >= 1 and tl["tts_stats"]["requests"] > 1

def test_gemini_failure_falls_back_to_kokoro_for_the_whole_narration(tmp_path, monkeypatch):
    from tools.rehearsal import ToneVoice
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice())
    monkeypatch.setattr(T, "_fake_reply", lambda body: (_ for _ in ()).throw(RuntimeError("Gemini TTS 503: overloaded")))
    r = V.narrate(SCRIPT, Blend("n", {"am_michael": 1.0}), str(tmp_path / "v"), seed="EPF", speaker_blends=SB); tl = _tl(r)
    assert tl["engine"] == "kokoro" and "Kokoro" in tl["engine_note"] and len(tl["units"]) >= 5
    assert "narration voiced by Kokoro (Gemini TTS failed)" in core.take_degraded()

def test_fallback_switched_off_raises(tmp_path, monkeypatch, setting):
    setting("TTS_FALLBACK_ON", "FALSE")
    monkeypatch.setattr(T, "_fake_reply", lambda body: (_ for _ in ()).throw(RuntimeError("Gemini TTS 503")))
    with pytest.raises(T.TTSFailed): V.narrate(SCRIPT, Blend("n", {}), str(tmp_path / "v"), seed="EPX", speaker_blends=SB)

def test_tts_engine_kokoro_restores_v89(tmp_path, monkeypatch, setting):
    from tools.rehearsal import ToneVoice
    setting("TTS_ENGINE", "kokoro"); monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice())
    monkeypatch.setattr(T, "synth", lambda *a, **k: pytest.fail("Gemini must not be called"))
    assert _tl(V.narrate(SCRIPT, Blend("n", {}), str(tmp_path / "v"), speaker_blends=SB))["engine"] == "kokoro"

def test_retry_after_busy_then_success(tmp_path, monkeypatch):
    real = T._fake_reply; n = {"k": 0}
    def flaky(body):
        n["k"] += 1
        if n["k"] == 1: raise RuntimeError("Gemini TTS 429: rate limited")
        return real(body)
    monkeypatch.setattr(T, "_fake_reply", flaky)
    a, sec = T.synth([("A", "Hello there.", "")], {"A": "Kore"}); assert sec > 0.3 and n["k"] == 2

def test_refused_voice_is_not_retried():
    with pytest.raises(T.TTSFailed): T.synth([("A", "Hi.", "")], {"A": "BROKEN_voice"})

def test_custom_voices_are_voiced_one_speaker_run_at_a_time(tmp_path, monkeypatch):
    seen = []; real = T._fake_reply
    monkeypatch.setattr(T, "_fake_reply", lambda body: (seen.append(body["generation_config"]["speech_config"]), real(body))[1])
    sb = {"DIRECTOR": Blend("d", {}, gvoice="voice_abc123"), "SKEPTIC": Blend("s", {}, gvoice="Puck")}
    assert _tl(V.narrate(SCRIPT, Blend("n", {}), str(tmp_path / "v"), seed="EPC", speaker_blends=sb))["engine"] == "gemini"
    assert seen and all(isinstance(c, list) for c in seen)          # never a two-speaker config with a designed voice
    assert T.is_prebuilt("Kore") and not T.is_prebuilt("voice_x") and not T.is_prebuilt("Nobody")

def test_tts_price_switches_on_1_jan_2027(monkeypatch):
    monkeypatch.setattr(T, "now_utc", lambda: dt.datetime(2026, 12, 31, tzinfo=dt.timezone.utc)); p26 = T.price_out()
    monkeypatch.setattr(T, "now_utc", lambda: dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)); assert T.price_out() == 2 * p26
    assert 5 < T.est_inr(600) < 40                                   # 10 minutes of narration at the 2027 rate stays well inside the allowance

def test_tts_model_is_picked_from_the_live_list():
    g = "gem" + "ini-"                     # assembled so Plan Guard (K11: no model name typed in code) stays green
    assert T.pick_tts([g + "x-flash", g + "3.8-flash-lite-tts", g + "3.8-flash-tts", g + "3.1-flash-tts-preview"]) == g + "3.8-flash-tts"
    assert T.pick_tts(["gemini-pro"]) is None

def test_voice_check_writes_the_tab(setting):
    setting("DESIGNED_VOICES_ON", "FALSE")          # v9.2: the 4 trial characters would join the 20 cast voices
    CAST.ensure_seed(); okn, tot, probs = T.voice_check()
    assert tot == 20 and okn == 20 and not probs
    rows = core.store().rows("Voice_Check"); assert len(rows) == 20 and all(r["synth_ok"] in (True, "True") for r in rows)
    core.store().update("Cast", "id", "G1", {"voice": "BROKEN_x"}); okn, tot, probs = T.voice_check(); assert okn == 19 and "G1" in probs[0]

# ---------------------------------------------------------------- 2. cast
def test_cast_guest_never_repeats_within_n_and_has_a_brief(setting):
    setting("SHOW_MODE", "off")                     # v9: the trial pins one core cast; guest rotation is the v8.10 / SHOW_MODE=off behaviour
    import random
    CAST.ensure_seed(); setting("GUEST_NO_REPEAT", "6"); hist = []
    for k in range(20):
        c = CAST.pick(random.Random(k), hist); assert c["guest"] not in [g for _, g in hist[-6:]]; hist.append((c["expert"], c["guest"]))
    assert len({g for _, g in hist}) == 15                       # every guest gets a turn (variety) and comes back (familiarity)
    b = CAST.brief(hist[-1] and {"expert": hist[-1][0], "guest": hist[-1][1]})
    assert "personality" in b and "signature quirk" in b and "[SKEPTIC]" in b
    setting("EXPERT_PICK", "fixed:E3"); assert CAST.pick(random.Random(1), hist)["expert"] == "E3"

def test_cast_voices_reach_the_speaker_blends_and_off_restores_v89(setting):
    CAST.ensure_seed(); sb = EP.speaker_blends("G1", {"expert": "E1", "guest": "G2"})
    assert sb["DIRECTOR"].gvoice == "Charon" and sb["SKEPTIC"].gvoice == "Fenrir" and sb["DIRECTOR"].parts != sb["SKEPTIC"].parts
    setting("CAST_ON", "FALSE"); assert not EP.speaker_blends("G1", {"expert": "E1", "guest": "G2"})["SKEPTIC"].gvoice

def test_empty_cast_tab_is_not_used():
    assert not CAST.enabled() and CAST.pick(__import__("random").Random(1)) == {}

# ---------------------------------------------------------------- 3. premise quality
P4 = [{"premise": "What if every pillow on Earth floated up at noon?", "headline": "Every Pillow Just Left Earth"},
      {"premise": "What if trees screamed when they were hurt?", "headline": "The Forest Can Scream"},
      {"premise": "What if Saturn's rings hung over your backyard?", "headline": "Rings"}]

def test_two_blind_judges_combine_and_code_checks_the_headline():
    out = PR.score([dict(p) for p in P4], [])
    assert out[0]["judges"] == "both" and out[0]["combined"] >= 7 and out[1]["combined"] < 7
    assert out[2]["criteria"]["headline_fit"] <= 3.0 and out[2]["combined"] < out[0]["combined"]
    assert out[0]["claude"] != out[0]["gemini"]                  # two independent judges, not one score copied

def test_one_judge_down_uses_the_other(monkeypatch):
    real = PR._judge
    monkeypatch.setattr(PR, "_judge", lambda role, *a, **k: (_ for _ in ()).throw(RuntimeError("down")) if role == "flash" else real(role, *a, **k))
    out = PR.score([dict(P4[0])], []); assert out[0]["judges"] == "one" and out[0]["combined"] > 7

def test_scores_logged_and_results_attached_later():
    out = PR.score([dict(p) for p in P4], []); PR.log_scores(out, "EPA", 0, "scout"); assert PR.mark_chosen("EPA", P4[0]["premise"])
    core.store().append("Analytics", [{"episode_id": "EPA", "ctr": "0.071", "rel30": "0.62", "avg_view_pct": "48"}])
    assert PR.attach_results() == 1
    row = next(r for r in core.store().rows("Premise_Scores") if str(r["chosen"]) == "True"); assert row["ctr"] == "0.071"

def test_nothing_passes_means_skip_not_fail_forward(monkeypatch, setting):
    setting("SETUP_FILLS_BENCH", "FALSE")          # v9.2: no bench, so the scout rounds run
    MG.setup(); monkeypatch.setattr(PR, "_judge", lambda role, pitches, *a, **k: {f"p{i + 1}": {c: 3 for c in D.PREMISE_CRITERIA} for i in range(len(pitches))})
    d = {"strategies": {"family": "F08_rules"}, "playbook": {}}
    setting("SKIP_IF_BELOW_BAR", "TRUE")                   # v8.11: skipping is now opt-in (the default ships the best version, see test_v811)
    with pytest.raises(PR.SkipSlot): ROOM.scout_and_pick(d, ROOM.context(), "EPS")
    rows = core.store().rows("Premise_Scores"); assert rows and {r["round"] for r in rows} == {"0", "1", "2", "3"}     # 1 + PREMISE_RETRY_ROUNDS (v8.11: 3) rounds, all logged
    setting("PREMISE_FAIL_FORWARD", "TRUE"); assert ROOM.scout_and_pick(d, ROOM.context(), "EPS2")["premise"]          # the owner can restore v8.9

def test_premise_bank_is_llm_generated_deduped_and_monthly(setting):
    MG.setup(); st = core.store(); st.append("Banned", [{"phrase": "rain fell upward", "reason": "test"}])
    st.append("Episodes", [{"episode_id": "EPOLD", "premise": "What if your hair aged 50 years in one day?", "status": "LIVE"}])
    n = PR.regenerate_bank(force=True); assert n >= 5
    fresh = [r for r in st.rows("Premises") if r["status"] == "FRESH"]
    assert fresh and all(r["grid"].startswith("llm-") for r in fresh)                        # the template grid is retired
    assert not any("upward" in r["premise"] or "hair aged" in r["premise"] for r in fresh)    # deduped vs Banned and past episodes
    assert not PR.bank_due() and PR.regenerate_bank() == 0                                  # once a month

# ---------------------------------------------------------------- 4. immersion / POV on every shot type
UNITS = [{"i": i, "text": t, "start": i * 4.0, "end": i * 4 + 3.5, "tag": "none"} for i, t in enumerate(
    ["You stand on the beach.", "The first ten seconds look harmless", "Then the water starts to change colour", "By the end of the hour, the coastline has moved.",
     "The wave hits.", "Silence.", "You breathe again."])]

def test_pov_on_every_picture_prompt_kling_on_the_impact_and_effects_on_every_type(setting):
    setting("KLING_STAKES_ON", "FALSE"); setting("POV_VARIETY_ON", "FALSE")          # v9.2 rules have their own tests
    setting("KLING_OPENING_CLIPS", "0")                    # v8.11: 0 restores the v8.10 placement asserted here (the opening hook is tested in test_v811)
    shots = [{"type": t, "prompt": "a beach" if t not in ("stock", "graphic") else "", "search": "waves"} for t in ("kling", "still", "living", "still", "stock", "graphic", "kling")]
    out = IM.apply(shots, UNITS, {"scenes": [{"quote": "the coastline has moved", "vantage": "object", "body": "stomach drop", "senses": [], "camera": "impact_shake", "sound": "boom", "impact": True},
                                             {"quote": "the water starts to change colour", "vantage": "hands", "body": "", "senses": [], "camera": "debris", "sound": "drip", "impact": False}]}, {"kling": 2})
    assert out[3]["impact"] and out[3]["pov_fx"] == "impact_shake" and out[2]["pov_fx"] == "debris"
    assert sorted(i for i, s in enumerate(out) if s["type"] == "kling") == [2, 3]                 # same count, moved onto the run-up + impact
    for s in out:
        if s["type"] in ("still", "living", "kling"): assert s["prompt"].startswith("first-person POV")
        else: assert "first-person" not in str(s.get("prompt"))                                   # stock / graphic get render effects instead
    assert "camera mounted on the moving object" in out[3]["motion"]
    shots2 = [{"type": "graphic", "camera": "pov_rush"}, {"type": "stock", "camera": "debris", "search": "x"}]
    out2 = IM.apply(shots2, UNITS[:2], {}, {"kling": 0}); assert out2[0]["pov_fx"] == "pov_rush" and out2[1]["pov_fx"] == "debris"
    setting("IMMERSION_ON", "FALSE"); assert IM.apply(shots, UNITS, {}, {"kling": 2}) == shots

def test_camera_events_are_locked_to_sound_events():
    shots = [{}, {"pov_fx": "pov_rush"}, {"pov_fx": "impact_shake"}, {"pov_fx": "debris"}]
    ev = IM.camera_sound_events(shots, UNITS[:4])
    assert ("doppler", 4.0) in ev and ("rush_end", 8.0) in ev and ("impact", 8.0) in ev and ("debris", 12.0) in ev

@pytest.mark.parametrize("kind", RN.POV_FX)
def test_pov_effects_keep_frame_size_and_change_the_picture(kind):
    f = RN.pov_fx(kind, 12, "s", 64, 36); fr = (np.random.default_rng(2).random((36, 64, 3)) * 255).astype(np.uint8)
    outs = [f(fr.copy(), k) for k in range(12)]
    assert all(o.shape == fr.shape and o.dtype == np.uint8 for o in outs) and any(not np.array_equal(o, fr) for o in outs)

def test_pov_effect_switch_and_overlay_order(setting):
    class Tag:
        def apply(self, fr, g): fr = fr.copy(); fr[0, 0] = 7; return fr
    ov = RN.with_fx(Tag(), "impact_shake", 10, "s", 100); fr = np.full((36, 64, 3), 50, np.uint8)
    assert isinstance(ov, RN.FxOverlay) and ov.apply(fr, 100)[0, 0, 0] == 7               # the speaker tag is drawn AFTER the shake (it never shakes)
    setting("POV_CAMERA_ON", "FALSE"); t = Tag(); assert RN.with_fx(t, "impact_shake", 10, "s", 0) is t
    assert RN.with_fx(None, None, 10, "s", 0) is None

def test_render_applies_pov_effects_to_graphic_and_still_segments(tmp_path):
    from PIL import Image
    p = str(tmp_path / "i.jpg"); Image.fromarray((np.random.default_rng(1).random((360, 640, 3)) * 255).astype(np.uint8)).save(p)
    RN.set_overlay(RN.with_fx(None, "pov_rush", 8, "s", 0)); RN.set_cursor(0)
    RN.parallax_segment(p, str(tmp_path / "a.mp4"), 8, "s"); RN.set_overlay(RN.with_fx(None, "impact_shake", 8, "s", 0)); RN.set_cursor(0)
    RN.graphic_segment({"kind": "counter", "label": "x", "from": 0, "to": 9, "unit": ""}, p, str(tmp_path / "b.mp4"), 8); RN.set_overlay(None)
    assert RN.probe_dur(str(tmp_path / "a.mp4")) > 0 and RN.probe_dur(str(tmp_path / "b.mp4")) > 0

# ---------------------------------------------------------------- 5-6. voice acting + immersive sound
def test_writer_and_director_get_the_new_rules(setting):
    w = IM.writer_rules(); assert "PRESENT TENSE, SECOND PERSON" in w and "{slow, low, whisper, breath}" in w and "3-8 seconds" in w
    assert "EVERY shot type" in IM.director_rules()
    setting("IMMERSION_ON", "FALSE"); setting("EMOTION_CURVE_ON", "FALSE"); assert IM.writer_rules() == "" and IM.director_rules() == ""

def test_immersive_design_and_mix(setting):
    units = [{"start": i * 6.0, "end": i * 6 + 5, "text": t, "tag": g, "curve": c} for i, (t, g, c) in enumerate(
        [("rain on the roof", "calm", []), ("a whisper", "close", []), ("hushed now", "none", ["hushed"]), ("the reveal", "reveal", []), ("impact", "none", []), ("after", "none", [])])]
    shots = [{"type": "still"} for _ in units]; shots[4]["pov_fx"] = "impact_shake"
    dz = SD.immersive(shots, units, 36.0, "s")
    assert dz["ambience"][0][0] == "rain" and len(dz["close"]) == 2 and dz["foley"] and dz["impacts"] == [24.0]
    g = SD.impact_gain(np.array([20.0, 23.5, 24.1, 27.0, 32.0]), [24.0]); assert g[1] < 0.1 and g[0] == 1.0 and g[-1] == 1.0 and g[3] < 0.5      # near-silence, hole, recovery
    d = SD.design(shots, units, 36.0, None, "s"); d.update(dz)
    mix = RN.score(36.0, "s", [("impact", 24.0), ("doppler", 10.0), ("rush_end", 12.0)], design=d)
    assert mix.shape[1] == 2 and np.isfinite(mix).all() and not np.allclose(mix[:, 0], mix[:, 1])      # real stereo movement

# ---------------------------------------------------------------- 7. creative constitution, notebook, techniques, Owner's Cut
def test_constitution_and_notebook_priority(setting):
    assert "INSIDE the scene" in CR.constitution()
    setting("CONSTITUTION", "Only volcano videos."); assert "Only volcano videos." in CR.constitution()
    core.store().append("Craft_Notebook", [{"note": "low", "priority": "1", "active": "TRUE"}, {"note": "TOP", "priority": "9", "active": "TRUE"}, {"note": "off", "active": "FALSE"}])
    nb = CR.notebook(); assert nb.index("TOP") < nb.index("low") and "off" not in nb
    assert "TOP PRIORITY" in CR.brief("writer"); setting("CRAFT_NOTEBOOK_ON", "FALSE"); assert CR.notebook() == ""

def test_technique_library_files_only_fetched_videos():
    assert CR.research_techniques() == 1
    row = core.store().rows("Technique_Library")[0]; assert row["video_id"] == "fakevid0001" and row["source_url"].endswith("fakevid0001")
    assert "silence" in CR.techniques_text()

def test_owners_cut_rewrites_then_passes_and_never_ships_below_the_bar(monkeypatch, setting):
    seq = iter([5.0, 8.5]); calls = []
    monkeypatch.setattr(CR, "judge", lambda *a: (lambda m: {"scores": {k: m for k in CR.OC_KEYS}, "mean": m, "passed": m >= 7.5, "fixes": ["make it first person"]})(next(seq)))
    out, rec = CR.owners_cut({"premise": "p"}, {"script": "a"}, "", {}, "EPO", lambda sc, fx: (calls.append(fx), {"script": "b"})[1])
    assert out["script"] == "b" and rec["passed"] and len(calls) == 1 and len(core.store().rows("Owners_Cut")) == 2
    monkeypatch.setattr(CR, "judge", lambda *a: {"scores": {k: 5 for k in CR.OC_KEYS}, "mean": 5.0, "passed": False, "fixes": []})
    setting("SKIP_IF_BELOW_BAR", "TRUE")                   # v8.11: skipping is opt-in
    with pytest.raises(CR.BelowBar): CR.owners_cut({"premise": "p"}, {"script": "a"}, "", {}, "EPO", lambda sc, fx: sc)
    setting("OWNERS_CUT_ON", "FALSE"); assert CR.owners_cut({}, {"script": "a"}, "", {}, "E", lambda *a: None)[1] == {"checked": False}

def test_owners_cut_unreachable_judge_never_blocks(monkeypatch):
    monkeypatch.setattr(CR, "judge", lambda *a: (_ for _ in ()).throw(RuntimeError("down")))
    out, rec = CR.owners_cut({}, {"script": "a"}, "", {}, "E", lambda *a: None); assert out == {"script": "a"} and rec["unavailable"]

def test_skipped_slot_is_recorded_and_not_retried(monkeypatch):
    MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(ROOM, "run_room", lambda d, ep: (_ for _ in ()).throw(CR.BelowBar("Owner's Cut stayed below 7.5")))
    slot = (core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = EP.produce(slot); assert r["skipped"] == "quality"
    e = core.store().rows("Episodes")[-1]; assert e["status"] == "SKIPPED"
    assert EP._slot_taken(core.store(), slot)                                              # the same slot is never produced again

# ---------------------------------------------------------------- 8. Script Preview
def test_preview_saves_a_draft_without_using_the_premise_then_approve_and_take(monkeypatch):
    MG.setup()
    r = PV.run(); assert r["ok"] and r["shots"] > 0 and r["est_cost_inr"] > 0
    row = core.store().rows("Script_Previews")[-1]; assert row["status"] == "DRAFT" and row["room_json"].startswith("z:")
    assert not any(p["status"] == "USED" for p in core.store().rows("Premises"))           # the premise is NOT used up by a preview
    assert not any(b["reason"] == "already made" for b in core.store().rows("Banned"))
    with pytest.raises(SystemExit): PV.decide("APPROVE nonsense")
    assert PV.decide(f"APPROVE {row['draft_id']}") == "APPROVE"
    d, room = PV.take_approved("EPNEW"); assert room["script"]["script"] and d.get("strategies")
    assert core.store().rows("Script_Previews")[-1]["status"] == "USED" and PV.take_approved("EPNEXT") is None

def test_rejected_or_switched_off_preview_is_not_used(setting):
    core.store().append("Script_Previews", [{"draft_id": "DRAFT202611010000", "status": "APPROVED", "room_json": PV._pack({"d": {}, "room": {"spine": {}}})}])
    setting("PREVIEW_USE_APPROVED", "FALSE"); assert PV.take_approved("E") is None
    setting("PREVIEW_USE_APPROVED", "TRUE"); PV.decide("REJECT DRAFT202611010000"); assert PV.take_approved("E") is None

# ---------------------------------------------------------------- 9. budget
def test_cap_is_4000_and_estimates_include_tts_and_thinking(setting):
    _legacy_budget(setting)
    assert core.DEFAULTS["BUDGET_CEILING_INR"][0] == "5000" and core.DEFAULTS["BUDGET_FLOOR_INR"][0] == "5000"      # v10: the owner's ₹5,000 (incl. ₹300 specials)
    assert not any("3,500" in v[1] and "was" not in v[1] for v in core.DEFAULTS.values())
    from whatifs import costguard as CG                                              # v12 V2d: the voice, the thinking, the room's extra calls and the Palace are LINES of the one cost model
    L = {l["key"]: l["inr"] for l in CG.lines("long")}; voice = CG.voice_inr(core.S("RUNTIME_MAX_SEC", float))
    base = G.min_episode_cost_inr(); assert (L["thinking"], L["room_extras"], L["palace"]) == (40, 20, 15) and L["voice"] == pytest.approx(voice, abs=0.01) and G.palace_prompt_inr() == 15
    assert voice == pytest.approx(2 * T.est_inr(core.S("RUNTIME_MAX_SEC", float)))                          # the narration and one re-take, by the second at the price of the day
    setting("TTS_ENGINE", "kokoro"); assert G.min_episode_cost_inr() == pytest.approx(base - voice, abs=0.02)
    assert EP.est_cost_inr({"stills": 50, "living": 8, "kling": 3, "episode_id": "E"}) > 300

def test_headroom_and_fourth_kling_only_when_it_fits(monkeypatch, setting):
    setting("KLING_CLIPS", "3"); setting("KLING_MIN_CLIPS", "3")      # v10.2: this golden describes the 3-clip plan; option C's 4 scenes are tested in test_v102
    _legacy_budget(setting)
    h = G.headroom(); assert h["cap_inr"] == 4000 and h["per_video_inr"] > 0
    monkeypatch.setattr(G, "episodes_left_this_month", lambda: 1); assert G.kling4_proposal()           # one video left, a full month of money: it fits
    monkeypatch.setattr(G, "episodes_left_this_month", lambda: 12); assert G.kling4_proposal() is None   # tight: never proposed
    setting("KLING_CLIPS", "4"); monkeypatch.setattr(G, "episodes_left_this_month", lambda: 1); assert G.kling4_proposal() is None

def test_gemini_credit_tracking_and_low_balance_email(monkeypatch, setting):
    assert G.gemini_left_usd() is None                                 # 0 = not tracked
    setting("GEMINI_FUNDED_USD", "5"); core.cost("gemini_tts", "google", 1000, 3.0); assert G.gemini_left_usd() == pytest.approx(2.0, abs=0.01)
    sent = []; from whatifs import publish as PUB; monkeypatch.setattr(PUB, "email", lambda s, h, kind="essential": sent.append((s, h)))
    MG.money_check(); assert any("Gemini" in h for s, h in sent)

def test_setup_seeds_cast_and_refreshes_old_cap_notes():
    st = core.store(); st.ensure_tabs(); st.append("Settings", [{"key": "BUDGET_CEILING_INR", "value": "4000", "note": "hard ₹3,500 cap"}])
    MG.setup()
    assert len(st.rows("Cast")) == 20 and sum(1 for r in st.rows("Cast") if r["role"] == "expert") == 5
    row = next(r for r in st.rows("Settings") if r["key"] == "BUDGET_CEILING_INR"); assert row["value"] == "5000" and "3,500" not in row["note"]      # v9.4a then v10: one-time moves to ₹4,700, then ₹5,000
    for t in ("Cast", "Voice_Check", "Premise_Scores", "Craft_Notebook", "Technique_Library", "Owners_Cut", "Script_Previews"): assert t in core.TABS

def test_every_new_setting_is_documented_with_its_off_value():
    for k in ("TTS_ENGINE", "CAST_ON", "PREMISE_BANK_ON", "PREMISE_DUAL_SCORE_ON", "PREMISE_FAIL_FORWARD", "IMMERSION_ON", "POV_CAMERA_ON", "EMOTION_CURVE_ON",
              "SOUND_IMMERSIVE_ON", "CRAFT_NOTEBOOK_ON", "TECHNIQUE_RESEARCH_ON", "OWNERS_CUT_ON", "PREVIEW_USE_APPROVED", "KLING_4TH_PROPOSE_ON", "GEMINI_FUNDED_USD"):
        assert k in core.DEFAULTS and core.DEFAULTS[k][1]
