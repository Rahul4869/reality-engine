"""Cut-map tests use synthetic narration with KNOWN silences, so timestamps are checked against ground truth."""
import json, os
import numpy as np, pytest, soundfile as sf
from whatifs import cutmap as C, core

SR = 24000
def speech(sec, f=170):
    t = np.arange(int(sec * SR)) / SR
    return (0.3 * np.sin(2 * np.pi * f * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 4 * t))).astype(np.float32)
def quiet(sec): return (np.random.default_rng(1).standard_normal(int(sec * SR)) * 1e-4).astype(np.float32)

def build(parts, tmp_path):
    """parts = [("s", sec, text) | ("q", sec, reasons|None)] -> wav + word-level timeline with exact times."""
    audio, units, t, pend = [quiet(0.3)], [], 0.3, None
    for p in parts:
        if p[0] == "q": audio.append(quiet(p[1])); t += p[1]; pend = (p[1], p[2] if len(p) > 2 else None)
        else:
            sec, text = p[1], p[2]; words = text.split(); d = sec / len(words)
            units.append({"i": len(units), "text": text, "tag": "none", "start": round(t, 3), "end": round(t + sec, 3),
                          "words": [{"w": w, "s": round(t + i * d, 3), "e": round(t + (i + 1) * d, 3)} for i, w in enumerate(words)],
                          "pause_before": pend[0] if pend else 0.0, "pause_before_reasons": list(pend[1] or []) if pend else [], "pause_after": 0.0, "pause_after_reasons": []})
            audio.append(speech(sec)); t += sec; pend = None
    audio.append(quiet(0.4)); a = np.concatenate(audio)
    wav = str(tmp_path / "v.wav"); sf.write(wav, a, SR)
    return wav, {"duration": round(len(a) / SR, 3), "units": units}

L1 = "Right now eight billion people are doing something ordinary today"
L2 = "But at exactly noon all of them do it at once right here"

def run(parts, tmp_path, **kw):
    wav, tl = build(parts, tmp_path)
    return C.build_cutmap(wav, tl, None, 30, episode="EPT", **kw), tl, wav

def test_dead_air_found_with_correct_start_end_duration_inside_the_silence(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    c = [x for x in m["cuts"] if x["kind"] == "dead_air"]
    assert len(c) == 1; c = c[0]
    assert tl["units"][0]["end"] <= c["start"] < c["end"] <= tl["units"][1]["start"]
    assert c["duration"] == pytest.approx(c["end"] - c["start"], abs=1e-3)
    assert c["duration"] == pytest.approx(1.5 - 0.55, abs=0.12)
    assert c["action"] == "trim_suggested" and c["removable"] and 0 < c["confidence"] <= 0.95 and "silence" in c["reason"].lower()
    assert c["start"] * 30 == pytest.approx(round(c["start"] * 30), abs=1e-6) and c["end"] * 30 == pytest.approx(round(c["end"] * 30), abs=1e-6)

def test_gaps_at_or_below_0_8s_are_ignored(tmp_path):
    assert run([("s", 2.0, L1), ("q", 0.7), ("s", 2.0, L2)], tmp_path)[0]["cuts"] == []

def test_gap_just_over_0_8_is_reported(tmp_path):
    assert run([("s", 2.0, L1), ("q", 0.9), ("s", 2.0, L2)], tmp_path)[0]["cuts"]

def test_explicit_pause_is_preserved_not_cut(tmp_path):
    m, *_ = run([("s", 2.0, L1), ("q", 1.6, ["explicit_pause"]), ("s", 2.0, L2)], tmp_path)
    assert m["cuts"] == [] and any("explicit_pause" in p["reason"] for p in m["preserved"])

def test_dramatic_tag_and_paragraph_pauses_preserved(tmp_path):
    m, *_ = run([("s", 2.0, L1), ("q", 1.2, ["tag:reveal", "paragraph"]), ("s", 2.0, L2)], tmp_path)
    assert m["cuts"] == [] and m["preserved"]

def test_unusually_long_planned_pause_is_review_only_and_keeps_the_planned_length(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 5.0, ["explicit_pause"]), ("s", 2.0, L2)], tmp_path)
    c = m["cuts"]; assert len(c) == 1 and c[0]["kind"] == "long_pause" and c[0]["action"] == "review"
    gap = tl["units"][1]["start"] - tl["units"][0]["end"]
    assert gap - c[0]["duration"] >= 1.5

def test_breath_only_gap_is_preserved(tmp_path):
    assert run([("s", 2.0, L1), ("q", 1.0, ["breath"]), ("s", 2.0, L2)], tmp_path)[0]["cuts"] == []

def test_silence_inside_a_spoken_line_is_found_from_audio(tmp_path):
    wav, tl = build([("s", 1.5, "first half of the sentence now"), ("q", 1.4), ("s", 1.5, "second half arrives late again")], tmp_path)
    one = {"i": 0, "text": "first half of the sentence now second half arrives late again", "tag": "none", "start": tl["units"][0]["start"], "end": tl["units"][1]["end"],
           "words": tl["units"][0]["words"] + tl["units"][1]["words"], "pause_before": 0, "pause_before_reasons": [], "pause_after": 0, "pause_after_reasons": []}
    m = C.build_cutmap(wav, {"duration": tl["duration"], "units": [one]}, None, 30, episode="EPT")
    inside = [c for c in m["cuts"] if c.get("inside_line")]
    assert inside and tl["units"][0]["end"] <= inside[0]["start"] and inside[0]["end"] <= tl["units"][1]["start"]

def test_no_removable_suggestion_ever_overlaps_a_word(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2), ("q", 2.0), ("s", 1.5, L1)], tmp_path)
    spans = C._wordspans(tl)
    for c in m["cuts"]:
        if c["removable"]: assert not C.overlaps_speech(c["start"], c["end"], spans, pad=0.0)

def test_apply_to_timeline_refuses_to_clip_speech(tmp_path):
    _, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    with pytest.raises(ValueError): C.apply_to_timeline(tl, [{"cut_id": "X", "start": 1.0, "end": 2.0}])

def test_ripple_keeps_narration_and_captions_in_step(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    cuts = [c for c in m["cuts"] if c["removable"]]; removed = sum(c["duration"] for c in cuts)
    new = C.apply_to_timeline(tl, cuts)
    assert new["duration"] == pytest.approx(tl["duration"] - removed, abs=1e-3)
    u0, u1 = tl["units"]; n0, n1 = new["units"]
    assert n0["start"] == u0["start"] and n0["end"] == u0["end"]
    assert n1["start"] == pytest.approx(u1["start"] - removed, abs=1e-3)
    assert (n1["end"] - n1["start"]) == pytest.approx(u1["end"] - u1["start"], abs=1e-3)
    for ow, nw in zip(u1["words"], n1["words"]): assert nw["s"] - n1["start"] == pytest.approx(ow["s"] - u1["start"], abs=1e-3)

def test_edl_segments_cover_everything_except_the_cuts(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    keep = m["edl_if_suggested_trims_accepted"]
    assert sum(b - a for a, b in keep) + m["summary"]["suggested_trim_total_sec"] == pytest.approx(tl["duration"], abs=0.01)
    assert all(keep[i][1] <= keep[i + 1][0] for i in range(len(keep) - 1))

def test_ripple_info_reports_shift_frames_and_captions(tmp_path):
    m, *_ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    r = m["cuts"][0]["ripple"]
    assert r["shift_later_content_by_sec"] == m["cuts"][0]["duration"] and r["end_frame"] > r["start_frame"] and r["captions_after"] == len(L2.split())

def test_cut_containing_a_sound_effect_is_downgraded_to_review(tmp_path):
    wav, tl = build([("s", 2.0, L1), ("q", 1.8), ("s", 2.0, L2)], tmp_path)
    m = C.build_cutmap(wav, tl, None, 30, events=[("boom", tl["units"][1]["start"] - 0.8)], episode="EPT")
    c = m["cuts"][0]; assert c["action"] == "review" and c["confidence"] <= 0.3 and "sound effect" in c["reason"]

def test_cut_across_a_shot_boundary_is_marked(tmp_path):
    assert "crosses_shot_boundary" in run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)[0]["cuts"][0]["ripple"]

def test_length_mismatch_between_clocks_lowers_confidence_and_warns(tmp_path):
    ok, *_ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    wav, tl = build([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    bad = C.build_cutmap(wav, tl, None, 30, episode="EPT", master_duration=tl["duration"] + 3)
    assert not bad["sync_check"]["ok"] and any("differ" in x for x in bad["limitations"]) and bad["cuts"][0]["confidence"] < ok["cuts"][0]["confidence"]

def test_audio_only_is_labelled_estimate_and_never_auto(tmp_path):
    wav, _ = build([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    m = C.build_cutmap(wav, None, None, 30, episode="EPT")
    assert m["estimate"] is True and m["method"] == "audio_only" and any("ESTIMATE" in x for x in m["limitations"])
    assert m["cuts"] and all(c["action"] == "review" and c["estimate"] for c in m["cuts"])

def test_timeline_with_audio_is_not_an_estimate(tmp_path):
    assert run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)[0]["estimate"] is False

def test_stumble_limitation_is_always_disclosed(tmp_path):
    assert any("stumbles cannot be detected reliably" in x for x in run([("s", 2.0, L1)], tmp_path)[0]["limitations"])

def test_repeated_word_is_a_weak_review_only_stumble_signal(tmp_path):
    wav, tl = build([("s", 2.0, L1), ("q", 0.3), ("s", 2.0, "we we need to go to the ocean now please sir")], tmp_path)
    s = [c for c in C.build_cutmap(wav, tl, None, 30, episode="EPT")["cuts"] if c["kind"] == "possible_stumble"]
    assert s and s[0]["action"] == "review" and not s[0]["removable"] and s[0]["confidence"] <= 0.6

def test_no_word_timing_means_no_stumble_check(tmp_path):
    wav, tl = build([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    for u in tl["units"]: u["words"] = []
    m = C.build_cutmap(wav, tl, None, 30, episode="EPT")
    assert not any(c["kind"] == "possible_stumble" for c in m["cuts"]) and any("sentence timing only" in x for x in m["limitations"])

def test_slow_delivery_flagged_as_pacing_lag_review_only(tmp_path):
    parts = []
    for i in range(10): parts += [("s", 2.0, L1), ("q", 0.2)]
    parts += [("s", 9.0, L1)]
    lag = [c for c in run(parts, tmp_path)[0]["cuts"] if c["kind"] == "pacing_lag"]
    assert lag and not lag[0]["removable"] and lag[0]["action"] == "review"

def test_all_cuts_have_required_fields_and_valid_timestamps(tmp_path):
    m, tl, _ = run([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2), ("q", 5.0, ["explicit_pause"]), ("s", 2.0, L1)], tmp_path)
    assert m["cuts"]
    ids = [c["cut_id"] for c in m["cuts"]]; assert len(set(ids)) == len(ids)
    for c in m["cuts"]:
        for k in ("start", "end", "duration", "reason", "confidence", "kind", "action", "start_tc", "end_tc"): assert k in c
        assert 0 <= c["start"] < c["end"] <= tl["duration"] + 0.01 and 0 < c["confidence"] <= 1
    assert [c["start"] for c in m["cuts"]] == sorted(c["start"] for c in m["cuts"])

def test_timecode_format(): assert C.tc(65.4321) == "01:05.432"

def test_no_inputs_returns_a_map_that_explains_itself():
    m = C.build_cutmap(None, None, None, 30, episode="E"); assert m["method"] == "none" and m["cuts"] == [] and any("no cut map" in x for x in m["limitations"])

def test_missing_and_corrupt_audio_do_not_raise(tmp_path):
    bad = tmp_path / "bad.wav"; bad.write_bytes(b"not audio")
    assert C.build_cutmap(str(tmp_path / "nope.wav"), None, None, 30)["cuts"] == []
    assert any("could not be analysed" in x for x in C.build_cutmap(str(bad), None, None, 30)["limitations"])

def test_run_cutmap_never_raises_and_saves_files(tmp_path):
    wav, tl = build([("s", 2.0, L1), ("q", 1.5), ("s", 2.0, L2)], tmp_path)
    m, paths = C.run_cutmap(str(tmp_path), wav, tl, None, 30, (), "EPSAVE")
    assert m and {os.path.basename(p) for p in paths} == {"cutmap.json", "cutmap.md"}
    assert json.load(open(tmp_path / "cutmap.json"))["episode_id"] == "EPSAVE"
    md = open(tmp_path / "cutmap.md").read(); assert "REVIEW ONLY" in md and "Limitations" in md
    rows = core.store().rows("Cut_Map"); assert rows and rows[0]["review_status"] == "pending" and rows[0]["episode_id"] == "EPSAVE"
    assert C.run_cutmap(str(tmp_path), "/no/such.wav", "/no/such.json", None, 30, (), "EPX")[0] is not None

def test_run_cutmap_swallows_internal_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "build_cutmap", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert C.run_cutmap(str(tmp_path), None, None) == (None, [])

def test_switched_off(tmp_path, setting):
    setting("CUTMAP_ON", "FALSE"); assert C.run_cutmap(str(tmp_path), None, None) == (None, [])

def test_voice_timeline_marks_planned_pauses_and_cutmap_preserves_them(tmp_path):
    """Real pipeline integration: voice.py writes the planned-pause metadata the cut map relies on."""
    from tools.rehearsal import ToneVoice
    from whatifs.voice import narrate, Blend
    script = "[calm] Right now about eight billion people are doing something ordinary.\n[pause:long]\n[reveal] At exactly noon all of them do it at once.\n[calm] Then the water changes colour slowly."
    r = narrate(script, Blend("T", {"af_heart": 1.0}), str(tmp_path / "v"), seed="t", backend=ToneVoice())
    tl = json.load(open(r.timeline_path)); u = tl["units"]
    assert "explicit_pause" in u[1]["pause_before_reasons"] and u[1]["pause_before"] >= 1.6
    assert all("pause_before" in x and "pause_after_reasons" in x for x in u)
    m = C.build_cutmap(r.wav_path, tl, None, 30, episode="EPV")
    assert not any(c["action"] == "trim_suggested" and c["start"] >= u[0]["end"] and c["end"] <= u[1]["start"] for c in m["cuts"])
    assert any("explicit_pause" in p["reason"] for p in m["preserved"])



def test_reality_engine_speaker_tags_are_parsed_without_being_spoken():
    from whatifs.voice import parse_script
    units = parse_script("[DIRECTOR] [calm] The simulation begins.\n[SKEPTIC] [tension] Wait, what changed?\n[reveal] Here is the answer.")
    assert [(u.speaker, u.tag, u.text) for u in units] == [
        ("DIRECTOR", "calm", "The simulation begins."),
        ("SKEPTIC", "tension", "Wait, what changed?"),
        ("NARRATOR", "reveal", "Here is the answer."),
    ]
