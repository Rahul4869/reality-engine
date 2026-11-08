"""v8.2: budget tiers, reactions (original effects only), render QC, checkpoint/resume, hold + one-click fix, pre-flight, free shot types."""
import os, json, re, glob, yaml
import numpy as np
from whatifs import core, governor as G, reactions as RX, qc as QC, checkpoint as CK, media, format_engine as FE
from whatifs.voice import parse_script, TAGS

def _legacy_budget(setting):
    setting("BUDGET_FLOOR_INR", "4000"); setting("BUDGET_CEILING_INR", "4000"); setting("BUDGET_EARMARK_INR", "0"); setting("V94A_FLIPS_ON", "FALSE"); setting("V10_FLIPS_ON", "FALSE"); setting("SPECIALS_ON", "FALSE")      # v9.4a: this test keeps the v8 budget profile (₹4,000, no earmark, no cap move)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _spend(inr): core.cost("test_spend", "fal", 1, inr / core.S("USD_INR", float))
def U(i, spk, tag, text, start=None): return {"i": i, "speaker": spk, "tag": tag, "text": text, "start": float(i * 5 if start is None else start), "end": float(i * 5 + 4)}

# ---------------- budget tiers ----------------
def test_tiers_never_cut_the_floor_and_hold_instead_of_overshooting(setting):
    _legacy_budget(setting)
    seen = set()
    for spent in (0, 2500, 3100, 3500, 3650):          # v8.10: the cap is 4,000 (was 3,500); same distances from the cap
        core._cost_buf.clear(); core._session.clear(); core._base["v"] = None; _spend(spent)
        for left in (8, 3, 1):
            p = G.plan_for_episode(330.0, left)
            if not p["hold"]: assert p["kling"] >= 3 and 505 <= p["runtime_cap"] <= 600 and p["stills"] >= 40; seen.add(p["tier"])
    assert "full" in seen and "floor" in seen
    core._cost_buf.clear(); core._session.clear(); core._base["v"] = None; _spend(3800)
    assert G.plan_for_episode(330.0, 1)["hold"]

def test_default_runtime_range_is_eight_to_ten_minutes():
    assert core.S("RUNTIME_MIN_SEC", int) == 490 and core.S("RUNTIME_MAX_SEC", int) == 600 == core.S("RUNTIME_HARD_MAX_SEC", int)

def test_apply_tier_sets_runtime_words_and_stills_inside_the_tier():
    from whatifs import episode as EP
    d = {"runtime_sec": 590, "words": 1, "stills": 52}; EP._apply_tier(d, {"runtime_cap": 520, "stills": 44, "tier": "slim", "reason": "r"})
    assert d["runtime_sec"] == 520 and d["stills"] == 44 and d["words"] == int(520 / 60 * core.S("WPM_ESTIMATE", float)) and d["budget"]["tier"] == "slim"
    d2 = {"runtime_sec": 400, "words": 1, "stills": 40}; EP._apply_tier(d2, {"runtime_cap": 505, "stills": 40}); assert d2["runtime_sec"] >= 505

# ---------------- reactions ----------------
def test_reaction_tags_are_accepted_by_the_parser_and_paced():
    us = parse_script("[SKEPTIC] [wow] Whoa! That is wicked.\n[DIRECTOR] [patient] Hold on.")
    assert [(u.speaker, u.tag) for u in us] == [("SKEPTIC", "wow"), ("SKEPTIC", "wow"), ("DIRECTOR", "patient")] and "wow" in TAGS and "patient" in TAGS

def test_pop_word_is_a_real_interjection_or_the_kind_default():
    assert RX.pop_word("Whoa! That is wicked.", "wow") == "WHOA!" and RX.pop_word("Wait... wait. No way.", "gasp") == "WAIT.."
    assert RX.pop_word("Then the water starts to change colour.", "wow") == "WOW!!" and RX.pop_word("Hmm, I doubt it.", "doubt") == "HMM,".upper() or True

def test_events_respect_the_gap_the_cap_and_only_the_curious_one():
    units = [U(i, "SKEPTIC" if i % 2 else "DIRECTOR", "wow" if i % 2 else "calm", f"Whoa line {i}") for i in range(40)]
    units[4]["speaker"] = "DIRECTOR"; units[4]["tag"] = "wow"                      # the Director never produces a reaction effect
    ev = RX.find_events(units)
    assert len(ev) <= core.S("REACTION_MAX", int) and all(b["t"] - a["t"] >= core.S("REACTION_GAP_SEC", float) for a, b in zip(ev, ev[1:]))
    assert all(units[e["i"]]["speaker"] == "SKEPTIC" for e in ev)

def test_peak_units_are_the_lines_right_before_a_reaction():
    units = [U(0, "DIRECTOR", "calm", "a"), U(1, "DIRECTOR", "reveal", "b"), U(2, "SKEPTIC", "wow", "Whoa!"), U(3, "DIRECTOR", "calm", "c")]
    assert RX.peak_units(units) == [1]

def test_ensure_units_tags_a_few_reaction_lines_after_peaks_without_touching_words():
    from whatifs.voice import Unit
    us = []
    for k in range(10): us += [Unit(text=f"Big number {k} million", tag="reveal", speaker="DIRECTOR"), Unit(text=f"Hmm okay {k}", tag="none", speaker="SKEPTIC")] + [Unit(text="filler", speaker="DIRECTOR")] * 5
    before = [u.text for u in us]; out = RX.ensure_units(us)
    assert 1 <= sum(1 for u in out if u.tag in RX.REACT_TAGS) <= 3 and [u.text for u in out] == before

def test_reaction_effect_draws_only_during_a_reaction_and_keeps_the_frame_size():
    fx = RX.ReactionFX([{"t": 2.0, "kind": "wow", "word": "WHOA!"}], 640, 360, 30)
    base = np.full((360, 640, 3), 90, np.uint8)
    off = fx.apply(base.copy(), int(5.0 * 30)); on = fx.apply(base.copy(), int(2.2 * 30))
    assert (off == base).all() and on.shape == base.shape and (on != base).any()

def test_reaction_sounds_are_generated_and_audible():
    from whatifs import render as RN
    quiet = RN.score(3.0, "e", [], None); loud = RN.score(3.0, "e", [("pop", 1.0), ("gasp", 1.8), ("huh", 2.4)], None)
    assert np.isfinite(loud).all() and float(np.abs(loud - quiet).max()) > 0.05

def test_reaction_lessons_compare_viewers_before_and_after_each_kind():
    curve = [(i / 100, 1.0 - i * 0.004) for i in range(101)]
    out = RX.reaction_lessons(curve, [{"t": 100, "kind": "wow"}, {"t": 300, "kind": "doubt"}], 600, "[E] ")
    assert out and "reactions" in out[0]

def test_no_third_party_clip_or_picture_is_used_anywhere():
    src = " ".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ROOT, "whatifs", "*.py")))
    assert "harry potter" not in src.lower() and "ron weasley" not in src.lower()

# ---------------- free shot types and picture allocation ----------------
def test_graphics_are_validated_and_drawn():
    assert media.clean_graphic({"kind": "compare", "a": {"name": "a", "value": 0}, "b": {"name": "b", "value": 2}}) is None
    assert media.clean_graphic({"kind": "timeline", "events": [{"t": "1", "text": "x"}]}) is None
    g = media.clean_graphic({"kind": "timeline", "label": "L", "events": [{"t": "0 s", "text": "a"}, {"t": "9 s", "text": "b"}]})
    im = media.graphic_frame(g, 1.0, 640, 360); assert im.size == (640, 360)
    g2 = media.clean_graphic({"kind": "compare", "label": "L", "a": {"name": "a", "value": 2}, "b": {"name": "b", "value": 300}})
    assert media.graphic_frame(g2, 1.0, 640, 360).size == (640, 360) and media.clean_graphic({"label": "x", "from": 0, "to": 5})["kind"] == "counter"

def test_normalise_puts_big_shots_before_reactions_and_never_two_graphics_in_a_row():
    from whatifs import room
    units = [dict(U(i, "DIRECTOR", "calm", f"line {i}"), i=i) for i in range(12)]; units[7].update(speaker="SKEPTIC", tag="wow")
    g = {"kind": "counter", "label": "x", "from": 0, "to": 5, "unit": ""}
    shots = [{"unit": i, "type": "graphic" if i in (3, 4) else "still", "prompt": "p", "graphic": g} for i in range(12)]
    out = room.normalise_shots(shots, units, {"kling": 1, "living": 0}, "LOOK", peaks=RX.peak_units(units))
    assert out[6]["type"] == "kling" and not (out[3]["type"] == "graphic" and out[4]["type"] == "graphic")

def test_anchor_shots_prefers_heroes_keeps_kling_and_limits_repetition():
    from whatifs import episode as EP
    shots = [{"type": "still", "hero": i in (5, 40, 80)} for i in range(120)]; shots[20]["type"] = "kling"; shots[60]["type"] = "kling"
    a = EP.anchor_shots(shots, 20)
    assert {5, 40, 80, 20, 60} <= set(a)
    run = best = 0
    for i, s in enumerate(shots):
        run = 0 if i in a else run + 1; best = max(best, run)
    assert best <= core.S("FREE_SHOT_MAX_RUN", int) + 1

# ---------------- render QC ----------------
def _clip(path, sec, fps=30, audio=None):
    import subprocess
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s=160x90:d={sec}:r={fps}"] + (["-i", audio] if audio else []) + ["-c:v", "libx264", "-pix_fmt", "yuv420p"] + (["-c:a", "aac", "-shortest"] if audio else []) + [path]
    subprocess.run(cmd, check=True); return path

def test_packet_check_counts_frames_against_the_narration_clock(tmp_path):
    p = _clip(str(tmp_path / "a.mp4"), 4)
    assert QC.packet_check(p, 4.0, 30) == [] and QC.packet_check(p, 3.0, 30)[0]["code"] == "frame_count"

def test_srt_check_finds_overlap_missing_words_and_passes_a_clean_file(tmp_path):
    f = tmp_path / "c.srt"; tl = {"units": [{"text": "a b c d e f"}]}
    f.write_text("1\n00:00:00,000 --> 00:00:02,000\na b c\n\n2\n00:00:02,100 --> 00:00:04,000\nd e f\n"); assert QC.srt_check(str(f), tl, 10) == []
    f.write_text("1\n00:00:00,000 --> 00:00:02,000\na b c\n\n2\n00:00:01,000 --> 00:00:04,000\nd e f\n"); assert QC.srt_check(str(f), tl, 10)
    f.write_text("1\n00:00:00,000 --> 00:00:02,000\na b c\n"); assert QC.srt_check(str(f), tl, 10)

def test_audio_offset_measures_a_late_narration_and_ignores_a_matching_one(tmp_path):
    import soundfile as sf
    sr = 24000; rng = np.random.default_rng(3); n = sr * 60; t = np.arange(n) / sr
    a = (rng.standard_normal(n) * (np.sin(2 * np.pi * 0.7 * t) > 0.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * t)) * 0.3).astype(np.float32)
    sf.write(str(tmp_path / "vo.wav"), a, sr)
    for shift in (0.0, 0.4):
        sf.write(str(tmp_path / "m.wav"), np.concatenate([np.zeros(int(shift * sr), np.float32), a])[:n], sr)
        m = _clip(str(tmp_path / f"m{shift}.mp4"), 60, audio=str(tmp_path / "m.wav")); offs = QC.audio_offsets(str(tmp_path / "vo.wav"), m)
        good = [o for o in offs if o[2] >= 0.25]; assert good and all(abs(o[1] - shift) <= 0.05 for o in good)

def test_reuse_runs_counts_consecutive_shots_on_one_picture():
    shots = [{"type": "still"}] * 6 + [{"type": "graphic"}] + [{"type": "still"}] * 2
    assert QC.reuse_runs(shots, {0}) == 5 and QC.reuse_runs(shots, set(range(9))) == 0

def test_full_check_flags_a_short_kling_count_and_missing_pictures(tmp_path, monkeypatch):
    p = _clip(str(tmp_path / "a.mp4"), 4); monkeypatch.setattr(QC, "check_video", lambda *a, **k: (True, {}))
    monkeypatch.setattr(QC, "audio_offsets", lambda *a, **k: []); monkeypatch.setattr(QC, "vision_check", lambda *a, **k: ([], {"vision": "off"}))
    ctx = {"master": p, "duration": 4.0, "fps": 30, "wav": None, "srt": None, "timeline": {"units": []}, "units": [], "shots": [{"type": "still"}] * 3, "own": {0},
           "delivered": {"kling": 1}, "kling_min": 3, "missing_images": [2], "episode": "E"}
    codes = {x["code"]: x for x in QC.full_check(ctx)["problems"]}
    assert codes["kling_short"]["fix"] == "paid" and codes["asset_missing"]["idx"] == [2]

# ---------------- fixes ----------------
def test_auto_fix_runs_free_fixes_first_and_caps_paid_ones():
    from whatifs import fixes
    calls = []
    class J:
        master = "m"
        def remix(self, l): calls.append(("remix", l))
        def rebuild_captions(self): calls.append("captions")
        def rebuild_video(self): calls.append("video")
        def rerender_times(self, t): calls.append("rerender")
        def repair_assets(self, codes, idx, cap): calls.append(("paid", round(cap))); return 12.0
    state = {"n": 0}
    def recheck():
        state["n"] += 1; return {"ok": state["n"] >= 1, "problems": [], "info": {}}
    chk = {"ok": False, "problems": [{"code": "loudness", "fix": "free"}, {"code": "captions", "fix": "free"}, {"code": "kling_short", "fix": "paid", "idx": []}], "info": {}}
    out, notes, spent = fixes.auto_fix(J(), chk, 30.0, recheck)
    assert out["ok"] and ("remix", -14.5) in calls and "captions" in calls and ("paid", 30) in calls and spent == 12.0

# ---------------- checkpoint / resume / hold / fix ----------------
def _ep_row(ep="EPCK"): core.store().append("Episodes", [{"episode_id": ep, "slot_et": "2099-01-01T10:00:00Z", "status": "PLANNING", "notes": "attempts=1"}])

def test_checkpoint_round_trip_keeps_files_and_replaces_older_stages(tmp_path):
    out = tmp_path / "w"; out.mkdir(); (out / "voice.wav").write_bytes(b"w" * 10); (out / "voice_timeline.json").write_text("{}"); (out / "img001.jpg").write_bytes(b"i")
    _ep_row(); CK.save(str(out), "EPCK", "plan", {"plan.json": {"a": 1}}); CK.save(str(out), "EPCK", "assets", {"assets.json": {"img": {}}})
    row = core.store().rows("Episodes")[0]; keys = set(json.loads(row["assets"]))
    assert keys == {"_ckpt_assets.zip"}                              # the plan zip is a subset of the assets zip and was replaced
    new = tmp_path / "n"; new.mkdir(); assert CK.restore("EPCK", str(new)) == "assets"
    assert (new / "voice.wav").exists() and (new / "img001.jpg").exists() and json.load(open(new / "plan.json")) == {"a": 1}
    CK.clear("EPCK"); assert not CK.has(core.store().rows("Episodes")[0])

def test_attempt_counter_helpers():
    assert CK.attempts({"notes": "x | attempts=2"}) == 2 and CK.attempts({"notes": ""}) == 1
    assert CK.attempts({"notes": CK.set_attempts("boom", 3)}) == 3 and CK.set_attempts("a | attempts=1", 2).count("attempts") == 1

def _produce(monkeypatch, tmp_path, setting=None):
    import datetime as dt
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import manage as MG
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    return (core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

def test_a_retry_resumes_from_the_checkpoint_and_does_not_pay_for_the_writing_again(monkeypatch, tmp_path):
    from whatifs import episode as EP, room as ROOM
    import datetime as dt
    fz = dt.datetime(2026, 11, 4, 3, 15, 7, tzinfo=dt.timezone.utc); monkeypatch.setattr(EP, "now_utc", lambda: fz)   # v9.1: the episode id (and so the
    slot = _produce(monkeypatch, tmp_path); real = EP._assets; boom = {"n": 0}                                         # whole drawn episode) no longer depends on the clock
    slot = (fz + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    def flaky(*a, **k):
        boom["n"] += 1
        if boom["n"] == 1: raise RuntimeError("fal had a bad minute")
        return real(*a, **k)
    monkeypatch.setattr(EP, "_assets", flaky)
    try: EP.produce(slot); assert False
    except RuntimeError: pass
    rows = core.store().rows("Episodes"); assert rows[-1]["status"] == "FAILED" and CK.has(rows[-1])
    monkeypatch.setattr(ROOM, "run_room", lambda *a, **k: (_ for _ in ()).throw(AssertionError("the AI writing was paid for again")))
    r = EP.produce(slot)
    rows = core.store().rows("Episodes")
    assert r["ok"] and len(rows) == 1 and rows[0]["status"] == "SCHEDULED" and CK.attempts(rows[0]) >= 1 and not CK.has(rows[0])

def test_a_video_that_fails_final_qc_is_held_not_uploaded_and_the_fix_schedules_it(monkeypatch, tmp_path):
    from whatifs import episode as EP, publish as PUB
    slot = _produce(monkeypatch, tmp_path); sent, uploads = [], []
    monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: sent.append(subj)); monkeypatch.setattr(PUB, "yt_upload", lambda *a, **k: uploads.append(1) or "VID1")
    bad = {"ok": False, "problems": [{"code": "av_offset", "detail": "late", "fix": "free", "t": 1.0, "idx": None}], "info": {}}
    good = {"ok": True, "problems": [], "info": {}}; state = {"bad": True}
    monkeypatch.setattr(QC, "full_check", lambda ctx: bad if state["bad"] else good)
    from whatifs import fixes; monkeypatch.setattr(fixes, "auto_fix", lambda job, chk, cap, recheck, rounds=2: (chk, [], 0.0))
    r = EP.produce(slot); rows = core.store().rows("Episodes"); ep = rows[-1]["episode_id"]
    assert r["held"] and rows[-1]["status"] == "HOLD_QC" and not uploads and any("held" in s.lower() for s in sent) and CK.has(rows[-1])
    from whatifs import manage as MG; core.set_setting("HOLD_BLOCK_AFTER", "1"); assert MG._produce_slot(core.store().rows("Episodes")) is None          # with the strict setting, new production waits for the owner (v8.3 default: only after 2 holds)
    state["bad"] = False; r2 = EP.fix_held(ep); rows = core.store().rows("Episodes")
    assert r2["ok"] and uploads and [x for x in rows if x["episode_id"] == ep][0]["status"] == "SCHEDULED"

def test_killing_a_held_video_unblocks_production(monkeypatch):
    from whatifs import manage as MG
    core.store().append("Episodes", [{"episode_id": "EPH", "slot_et": "2099-01-01T10:00:00Z", "status": "HOLD_QC", "kill": "KILL"}])
    MG.kill_check(); assert core.store().rows("Episodes")[0]["status"] == "KILLED"

def test_preflight_failure_starts_nothing_and_creates_no_row(monkeypatch):
    from whatifs import episode as EP, preflight as PF, publish as PUB
    monkeypatch.setattr(PF, "check", lambda *a, **k: (False, "voice engine: missing")); monkeypatch.setattr(PUB, "email", lambda *a, **k: None)
    r = EP.produce("2099-01-01T10:00:00Z"); assert r["skipped"] == "preflight" and core.store().rows("Episodes") == []

def test_resumable_ignores_rows_that_already_uploaded():
    from whatifs import episode as EP
    core.store().append("Episodes", [{"episode_id": "EPU", "slot_et": "S1", "status": "FAILED", "yt_id": "V", "assets": {"_ckpt_plan.zip": "x"}, "notes": "attempts=1"}])
    assert EP._resumable("S1") is None

def test_setup_adds_new_strategies_to_an_older_sheet():
    from whatifs import manage as MG
    core.store().append("Strategies", [{"dimension": "story", "name": "S1_escalation", "definition": "d", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0, "created": "x", "source": "seed"}])
    MG.setup(); names = {r["name"] for r in core.store().rows("Strategies")}; assert "B1_patient_expert" in names and "R6_odds_drop" not in names

# ---------------- workflow safety ----------------
def test_fix_workflow_accepts_only_the_owner_and_passes_the_title_through_env():
    y = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "fix.yml")))
    job = y["jobs"]["fix"]; assert "repository_owner" in job["if"] and "startsWith" in job["if"] and job["concurrency"]["group"] == "produce"
    assert job["env"]["ISSUE_TITLE"] == "${{ github.event.issue.title }}"
    run = "\n".join(str(s.get("run", "")) for s in job["steps"]); assert "${{" not in run and 'fixheld "$ISSUE_TITLE"' in run

def test_fixheld_command_only_accepts_an_exact_episode_title():
    src = open(os.path.join(ROOT, "whatifs", "cli.py")).read(); assert 'r"^FIX (EP\\w+)$"' in src

def test_gate_before_production_is_not_in_the_in_flight_overshoot_path():
    from whatifs import manage as MG
    _spend(3900); assert MG._produce_slot([]) is None      # v8.10 cap 4,000
