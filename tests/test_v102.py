"""v10.2: Feature Contract (K151) and Animation director (K152). No keys, no network."""
import json, os
import pytest
from whatifs import core, anim as AN, contract as CON, media as MD, notify as NT, publish as PUB, manage as MG, episode as EPI

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _units(n, step=15.0):
    return [{"start": i * step, "end": i * step + step - 1, "text": f"line {i}", "speaker": ("GRIMM", "VALE", "ROSA", "ARCHIVIST")[i % 4]} for i in range(n)]

def test_four_scenes_at_the_retention_cliffs_and_other_clips_demoted():
    units = _units(44); shots = [{"type": "kling" if i in (5, 6) else "still"} for i in range(44)]
    idx = AN.apply(shots, units, plan := {"kling": 4})
    assert len(idx) == 4 and plan["kling"] == 4
    starts = [units[i]["start"] for i in idx]; end = units[-1]["start"]
    assert starts[0] == 0 and abs(starts[1] - 0.29 * end) <= 15 and abs(starts[2] - 0.57 * end) <= 15 and starts[3] >= 0.85 * end
    assert sum(1 for s in shots if s["type"] == "kling") == 4 and all(shots[i].get("anim") for i in idx)
    assert all(shots[i]["type"] == "still" for i in (5, 6) if i not in idx)       # moved Kling slots never become extra paid clips

def test_worlds_follow_the_speaker_and_prompts_carry_the_style_lock():
    s = {"anim": {"world": "lab", "line": "the Moon is gone", "slot": 1}}
    assert "Dr. Grimm" in AN.frame_prompt(s["anim"]) and "puppet" in AN.frame_prompt(s["anim"]) and "green" in AN.frame_prompt(s["anim"])
    p = AN.acting_prompt(s); assert "anticipation" in p and "no lip movement" in p and "Dutch angle" in p
    assert AN.world_for({}, {"speaker": "VALE"}, 0) == "office" and AN.world_for({}, {"speaker": "NANA ROSA"}, 0) == "court"

def test_kling3_inputs():
    a = MD.video_args("fal-ai/kling-video/o3/standard/image-to-video", "u", "p", True)        # v11: the verified Standard endpoint takes image_url
    assert a["image_url"] == "u" and "start_image_url" not in a and a["generate_audio"] is False and a["duration"] == "5"
    b = MD.video_args("fal-ai/kling-video/v3/pro/image-to-video", "u", "p", True)              # Kling 3.0 Pro keeps start_image_url
    assert b["start_image_url"] == "u" and b["generate_audio"] is False

SCRIPT_OK = "\n".join(["GRIMM: At hour 1 the tide clock stalls!", "ARCHIVIST: Exhibit A: NOAA tide records, 2023.", "VALE: By day 1 the beaches change.",
                        "GRIMM: Behold, Prototype No. 41!", "ARCHIVIST: Exhibit B: UK tidal survey, 2021.", "VALE: By year 1 the reefs go quiet.",
                        "ARCHIVIST: Exhibit C: Laskar, Nature, 1993.", "ROSA: Here's what's true: in a million years the tilt still wobbles."])

def test_trial_grammar_checks_pass_and_fail():
    ok = {"room": {"script": {"script": SCRIPT_OK}}}
    for p in (CON.p_time_ladder, CON.p_exhibits, CON.p_prototype, CON.p_verdict_line): assert p(ok)[0] == "PASS", p.__name__
    bad = {"room": {"script": {"script": "GRIMM: The end is near. ARCHIVIST: Exhibit A: trust me."}}}
    for p in (CON.p_time_ladder, CON.p_exhibits, CON.p_prototype, CON.p_verdict_line): assert p(bad)[0] == "FAIL", p.__name__
    assert "TRIAL GRAMMAR" in __import__("whatifs.show", fromlist=["x"]).prompt_block()

def test_a_failed_check_holds_and_a_waiver_needs_the_owner(monkeypatch, setting):
    _quiet(monkeypatch)
    ctx = {"room": {"script": {"script": "GRIMM: hello"}}, "d": {}, "hook_rec": None}
    g = CON.run("script", ctx, "EPX")
    assert not g["ok"] and {"time_ladder", "exhibits"} <= {f for f, _ in g["failed"]}
    assert len([r for r in core.store().rows("Feature_Ledger") if r["episode_id"] == "EPX"]) == len(g["rows"])
    CON.owner_card("EPX", "script", g["failed"])
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "contract_hold")
    assert "waived" in NT.answer(row["id"], f"CONTRACT WAIVE EPX time_ladder,exhibits")
    g2 = CON.run("script", ctx, "EPX"); assert "time_ladder" not in {f for f, _ in g2["failed"]}
    assert any(r["status"] == "WAIVED" for r in g2["rows"])

def test_every_feature_has_a_probe_and_a_promise():
    assert len(CON.FEATURES) >= 25
    for fid, stage, probe, what in CON.FEATURES:
        assert stage in ("script", "final", "short", "release") and callable(probe) and len(what) > 8, fid          # v12 V2c: + the short gate of a standalone Short; V2c-b2: + its release gate

def test_review_gate_keeps_the_video_private_until_approved(monkeypatch, setting):
    _quiet(monkeypatch); setting("CREATIVE_REVIEW_FIRST_N", "3")
    import datetime as dt
    slot = (core.now_utc() + dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": "EPR", "yt_id": "vidR", "slot_et": slot, "status": "SCHEDULED"}])
    calls = []
    monkeypatch.setattr(PUB, "yt_set_privacy", lambda v, p: calls.append(("priv", v, p)) or True)
    monkeypatch.setattr(PUB, "yt_schedule", lambda v, s: calls.append(("sched", v, s)) or True)
    assert CON.review_needed("long")
    CON.await_approval("EPR", "vidR", slot, "'Title'. Self-review: hook 8.")
    assert ("priv", "vidR", "private") in calls and core.store().rows("Episodes")[-1]["status"] == "AWAITING_APPROVAL"
    assert "AWAITING_APPROVAL" in EPI._TAKEN and "HELD_BY_OWNER" in EPI._TAKEN
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "creative_review")
    assert "approved" in NT.answer(row["id"], "APPROVE EPR") and core.store().rows("Episodes")[-1]["status"] == "SCHEDULED"
    assert ("sched", "vidR", slot) in calls

def test_v102_flips_only_old_defaults(setting):
    st = core.store(); st.append("Settings", [{"key": "FAL_HERO_MODEL", "value": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video", "note": ""},
                                              {"key": "KLING_CLIPS", "value": "2", "note": ""}])
    core._settings_cache = None
    done = MG.v102_upgrade(st)
    assert "FAL_HERO_MODEL" in done and "KLING_CLIPS" not in done and MG.v102_upgrade(st) == []

def test_cast_intro_is_voiced_set_driven_and_waits_for_approval(monkeypatch):
    _quiet(monkeypatch)                                        # (SPECIALS_REVIEW_ON is TRUE by default)
    from whatifs import specials as SP
    r = SP.run("cast_intro", force=True)
    assert r["ok"] and r["status"] == "AWAITING_APPROVAL" and r["file"].startswith("drive:")
    import subprocess, json as J
    o = J.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", r["path"]], capture_output=True, text=True).stdout)
    assert {"video", "audio"} <= {s["codec_type"] for s in o["streams"]} and float(o["format"]["duration"]) > 15
    row = next(x for x in core.store().rows("Owner_Actions") if x["kind"] == "special_review")
    assert "nothing is posted yet" in row["text"] and "GRIMM:" in row["text"]
    posted = []
    monkeypatch.setattr(SP, "_publish", lambda path, title, ep: posted.append(ep) or {"status": "POSTED", "yt_id": "y1"})
    assert "posted" in NT.answer(row["id"], f"SPECIAL APPROVE {r['id']}") and posted == [r["id"]]
    assert all(b.get("world") and b.get("line") for b in SP.CAST_INTRO)

def test_no_intro_without_designed_voices(monkeypatch):
    _quiet(monkeypatch)
    from whatifs import specials as SP
    monkeypatch.setattr(SP, "FAKE", False)
    monkeypatch.setattr(SP, "_voice_line", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no designed voice for GRIMM")))
    r = SP.run("cast_intro", force=True)
    assert not r["ok"] and "voice" in r["why"]

def test_voice_gate_skipped_when_designed_voices_work(setting):
    st = core.store()
    st.append("Characters", [{"id": c, "gvoice": f"{c} 1"} for c in ("VALE", "GRIMM", "ROSA", "ARCHIVIST")])
    st.append("Voice_Check", [{"voice": f"{c} 1", "synth_ok": "TRUE"} for c in ("VALE", "GRIMM", "ROSA", "ARCHIVIST")])
    setting("TTS_ENGINE", "gemini")
    assert MG._designed_voices_ok()
    st.append("Voice_Check", [{"voice": "GRIMM 1", "synth_ok": "FALSE"}])
    assert not MG._designed_voices_ok()

def test_whatsapp_template_body_ends_with_plain_text():
    import inspect
    from whatifs import wa as WA
    src = inspect.getsource(WA.ensure_templates)
    body = src.split('"text": "')[1].split('"')[0]
    assert not body.rstrip().endswith("}}") and not body.lstrip().startswith("{{") and core.DEFAULTS["WA_GRAPH_VERSION"][0] == "v27.0"
    assert hasattr(WA, "ensure_subscribed")

def test_sheets_make_reference_masters_before_any_expression(setting):
    from whatifs import sheets as SH
    core.store().append("Character_Sheets", [{"character": c, "expression": "neutral", "hash": "n" + c, "file": "drive:x", "status": "LOCKED"} for c in ("VALE", "GRIMM", "ROSA")])
    r = SH.run(); assert r["made"] == 3
    rows = [x for x in core.store().rows("Character_Sheets") if x.get("expression") == "master"]
    assert len(rows) == 3 and all(x["status"].startswith("DRAFT") and "no letters" in x["prompt"].lower() for x in rows)
    assert SH.run()["made"] == 0                                    # idempotent, and no expression before the masters are LOCKED

INVENTED = ("goggle", "fedora", "beard", "tortoiseshell", "apron", "white hair", "lightning-bolt hair")

def test_character_look_comes_only_from_the_canon(setting):
    from whatifs import show as SHOW, sheets as SH, specials as SP
    canon = {c["id"]: c for c in SHOW.characters()}
    for who in AN.FACE_CAST:
        lock = AN.char_lock(who); c = canon[who]
        assert lock == f"{c['name']}: {c['visual']}", (who, lock)
        for feature in [x.strip() for x in c["visual"].split(",")]: assert feature in lock
    texts = [AN.frame_prompt({"world": w, "line": "x"}, a) for w in AN.WORLDS for a in ("16:9", "9:16")] + \
            [AN.acting_prompt({"anim": {"world": w, "line": "x"}}) for w in AN.WORLDS] + [p["prompt"] for p in SH.masters_plan()] + \
            [b["line"] for b in SP.CAST_INTRO] + list(AN.STYLE_LOCKS.values())
    for tx in texts:
        low = tx.lower()
        assert not [w for w in INVENTED if w in low], (w for w in INVENTED if w in low)
    for s in AN.STYLE_LOCKS.values():                                       # style words only: no costume or face words
        assert not any(k in s.lower() for k in ("coat", "glasses", "robe", "hair", "teacup", "pocket square"))
    setting("ART_STYLE", "photoreal"); assert "realism" in AN.frame_prompt({"world": "lab", "line": "x"}) and "puppet" not in AN.frame_prompt({"world": "lab", "line": "x"})

def test_owner_approved_old_drafts_are_not_judged_on_the_new_grammar(setting):
    import time as T
    old = {"room": {"script": {"script": "GRIMM: hello"}}, "d": {"from_preview": True, "preview_room_ts": T.time() - 86400 * 5}}
    setting("TRIAL_GRAMMAR_SINCE", core.iso())
    for p in (CON.p_time_ladder, CON.p_exhibits, CON.p_prototype, CON.p_verdict_line): assert p(old)[0] == "N/A", p.__name__
    new = {"room": {"script": {"script": "GRIMM: hello"}}, "d": {"from_preview": True, "preview_room_ts": T.time() + 60}}
    assert CON.p_time_ladder(new)[0] == "FAIL"

def test_director_never_exceeds_the_budget_plan():
    units = _units(44); shots = [{"type": "still"} for _ in range(44)]
    assert len(AN.apply(shots, units, {"kling": 3})) == 3 and core.DEFAULTS["KLING_MIN_CLIPS"][0] == "4"


def test_style_board_of_the_owners_cast_and_tap_to_choose(monkeypatch, tmp_path):
    _quiet(monkeypatch)
    from whatifs import sheets as SH
    from PIL import Image
    r = SH.style_samples()
    assert r["ok"] and os.path.exists(r["board"]) and Image.open(r["board"]).size == (150 + 480 * 4, 54 + 270 * 3)
    assert core.S("STYLE_SAMPLES_REQUEST").startswith("DONE")
    row = next(x for x in core.store().rows("Owner_Actions") if x["kind"] == "style_pick")
    assert "photoreal" in NT.answer(row["id"], "STYLE photoreal").lower() and core.S("ART_STYLE") == "photoreal"
    assert AN.frame_prompt({"world": "lab"}, style="illustrated") != AN.frame_prompt({"world": "lab"}, style="toybox_noir")

def test_every_still_carries_the_one_chosen_look(monkeypatch, setting):
    seen = []
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD, "fal_allowed", lambda: True)
    monkeypatch.setattr(MD, "fal_run", lambda model, args, timeout=0: seen.append(args["prompt"]) or {"images": [{"url": "u"}]})
    monkeypatch.setattr(MD, "_dl", lambda u, p: p)
    setting("ART_STYLE", "toybox_noir")
    try: MD.still("a harbour at night", "/tmp/s.jpg", "EP")
    except Exception: pass
    assert seen and AN.style_words("toybox_noir") in seen[0]
