"""v8.9: style lock, camera library, living-still atmosphere, clear rotating voices, next-episode tease, preventive plan check, hashtag cap,
change-ready email + one-click merge, CLAUDE.md, cost unchanged. No keys, no network."""
import os, json, math, random, glob, subprocess
import numpy as np
import pytest
from whatifs import core, render as RN, room as ROOM, episode as EP, governor as G, manage as MG, sampler as SA
from whatifs.data import GUESTS, STYLE_LOCK, THUMB_STYLE
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- K71 style lock
def test_style_lock_on_every_paid_shot_and_promise_shot():
    units = [{"i": i, "text": f"line {i}", "tag": "none", "start": i * 5.0} for i in range(8)]
    shots = ROOM.normalise_shots([{"unit": i, "type": "still", "prompt": "a city"} for i in range(8)], units, {"kling": 1, "living": 2}, "teal look")
    assert all(STYLE_LOCK in s["prompt"] for s in shots if s["type"] in ("still", "living", "kling"))
    out = ROOM.promise_shot(shots, units, {"thumb_prompt": "a giant pillow over New York " * 8})
    k = [s for s in out if s.get("promise")]
    assert not k or STYLE_LOCK in k[0]["prompt"]

def test_thumbnail_style_is_bright_not_dark():
    assert "brightly lit" in THUMB_STYLE and "deep shadows" not in THUMB_STYLE

def test_repair_stills_get_the_lock_too(monkeypatch):
    seen = {}
    from whatifs import media as M
    monkeypatch.setattr(M, "FAKE", False); monkeypatch.setattr(M, "fal_allowed", lambda: True)
    monkeypatch.setattr(M, "fal_run", lambda model, args, **k: seen.update(args) or {"images": [{"url": "u"}]})
    monkeypatch.setattr(M, "_dl", lambda u, p: None); monkeypatch.setattr(M, "cost", lambda *a, **k: 0)
    M.still("a glass bone", "/tmp/x.jpg", "EP"); assert STYLE_LOCK in seen["prompt"]
    seen.clear(); M.still("thumb art", "/tmp/y.jpg", "EP", premium=True); assert STYLE_LOCK not in seen["prompt"]

# ---------------- K72 camera library
@pytest.mark.parametrize("move", list(dict.fromkeys(RN.MOVES_HIGH + RN.MOVES_CALM)))
@pytest.mark.parametrize("energy", ["calm", "high"])
def test_every_move_keeps_the_viewport_inside_the_picture(move, energy):
    ww, wh, pad = 640, 360, 1.3; sw, sh = int(ww * pad), int(wh * pad); base = ww / (sw / pad)
    for seed in range(6):
        cam = RN.camera_path(move, 90, sw, sh, ww, wh, base, random.Random(seed), energy)
        assert len(cam) == 90
        for cx, cy, z, th, ps, fd in cam:
            for du, dv in ((-ww / 2, -wh / 2), (ww / 2, -wh / 2), (-ww / 2, wh / 2), (ww / 2, wh / 2)):
                x = cx + (du * math.cos(th) - dv * math.sin(th)) / z; y = cy + (du * math.sin(th) + dv * math.cos(th)) / z
                assert -0.5 - abs(ps) <= x <= sw + 0.5 + abs(ps) and -0.5 <= y <= sh + 0.5, (move, energy, seed)
            assert abs(th) <= math.radians(3.0)

def test_high_energy_moves_are_bigger_and_moves_never_repeat_back_to_back():
    ww, wh = 640, 360; sw, sh = int(ww * 1.3), int(wh * 1.3); base = ww / (sw / 1.3)
    span = lambda e: max(c[2] for c in RN.camera_path("push_parallax", 60, sw, sh, ww, wh, base, random.Random(1), e)) / base
    assert span("high") > span("calm")
    rng = random.Random(3); last = None
    for _ in range(200):
        m = RN.choose_move(rng, rng.choice(["high", "calm"]), last); assert m != last; last = m
    assert set(RN.MOVES_HIGH) <= set(RN.MOVES_HIGH + RN.MOVES_CALM) and "whip_settle" not in RN.MOVES_CALM

def test_parallax_segment_renders_exact_frames_dynamic_and_gentle(tmp_path, setting):
    from PIL import Image
    img = str(tmp_path / "a.jpg"); Image.fromarray((np.random.default_rng(1).random((300, 500, 3)) * 255).astype(np.uint8)).save(img)
    for mode in ("dynamic", "gentle"):
        setting("CAMERA_MOTION", mode)
        for mv in ("rack_focus", "kb_roll", "handheld"):
            out = RN.parallax_segment(img, str(tmp_path / f"{mode}{mv}.mp4"), 12, seed="s", energy="high", move=mv)
            n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
            assert int(n) == 12

def test_living_clip_push_keeps_frame_count(tmp_path):
    from whatifs import media as M
    clip = M.fake_clip(str(tmp_path / "c.mp4"), 320, 180, "x", 2)
    out = RN.clip_segment(clip, str(tmp_path / "o.mp4"), 24, push=0.07)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    assert int(n) == 24

# ---------------- K73 living stills
def test_living_motion_is_atmospheric_and_stronger_in_the_opening_kling_unchanged():
    liv = {"type": "living", "prompt": "lava river at night", "motion": "slow"}
    a, b = EP.motion_prompt(liv, "the lava moves", True), EP.motion_prompt(liv, "the lava moves", False)
    assert "embers" in a and "dramatic" in a and "dramatic" not in b
    k = {"type": "kling", "prompt": "p", "motion": "m"}; assert EP.motion_prompt(k, "x", True) == "m. p"

# ---------------- K74 voices
def test_blends_are_clear_two_voices_max_no_low_graded_voices():
    for parts in list(EP.BLENDS.values()) + [g[1] for g in GUESTS.values()]:
        assert len(parts) <= 2 and max(parts.values()) >= 0.65 and abs(sum(parts.values()) - 1) < 1e-6
        assert not set(parts) & {"am_onyx", "bm_george", "am_adam", "am_echo", "am_eric", "am_liam", "am_santa"}

def test_master_chain_has_no_echo():
    import inspect
    from whatifs import voice
    src = inspect.getsource(voice._master); assert "aecho" not in src and "deesser" in src

def test_guest_rotates_least_recently_used_and_is_stable_on_retry(setting):
    st = core.store(); picked = []
    for k in range(len(GUESTS) + 1):
        d = SA.draw(f"EPG{k}", "collective"); picked.append(d["guest"])
        assert SA.draw(f"EPG{k}", "collective")["guest"] == d["guest"]          # a retry draws the same guest
        st.append("Episodes", [{"episode_id": f"EPG{k}", "status": "LIVE", "draw_json": json.dumps(d)}])
    assert len(set(picked[:len(GUESTS)])) == len(GUESTS) and picked[-1] == picked[0]

def test_speaker_blends_use_the_guest_and_fall_back_when_rotation_is_off(setting):
    sb = EP.speaker_blends("G3"); assert sb["SKEPTIC"].parts == GUESTS["G3"][1] and sb["DIRECTOR"].parts != sb["SKEPTIC"].parts
    setting("GUEST_ROTATION_ON", "FALSE"); assert EP.speaker_blends("G3")["SKEPTIC"].parts == EP.BLENDS["C"]
    assert EP.speaker_blends("nope")["SKEPTIC"].parts == EP.BLENDS["C"]

def test_guest_brief_names_the_persona(setting):
    setting("SHOW_MODE", "off")                     # v9: the trial uses the core cast (no rotating guest); v8.9 behaviour under SHOW_MODE = off
    assert "night-shift nurse" in ROOM.guest_brief({"guest": "G1"}) and ROOM.guest_brief({"guest": "zz"}) == ""

# ---------------- K75 next-episode tease
def _ctx(): return {"banned": [], "recent": []}

def test_clean_tease_needs_another_family_and_falls_back_to_a_vetted_pitch():
    spine = {"premise": "What if pillows floated?", "family": "F08_rules", "next_tease": {"premise": "What if gravity flipped?", "family": "F08_rules", "line": "x"}}
    good = [{"premise": "What if your heart beat twice as fast?", "family": "F01_body", "headline": "Double Heartbeat"}]
    t = ROOM.clean_tease(spine, good); assert t["family"] == "F01_body" and t["line"]
    assert ROOM.clean_tease({"premise": "p", "family": "F01_body"}, []) == {}

def test_teased_pitch_is_used_once_and_cleared_when_it_breaks_a_rule(setting):
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass?", "family": "F01_body"}))
    assert ROOM.teased_pitch(_ctx(), [])["teased"]
    assert ROOM.teased_pitch({"banned": ["glass"], "recent": []}, []) is None and core.S("NEXT_PREMISE") == ""
    setting("NEXT_PREMISE", "not json"); assert ROOM.teased_pitch(_ctx(), []) is None

def test_scout_hands_the_showrunner_only_the_teased_pitch_and_consumes_it(setting, monkeypatch):
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass for a day?", "family": "F01_body", "headline": "Glass Bones"}))
    seen = []
    real = ROOM.ask
    def spy(role, system, prompt, **k):
        if k.get("fake_key") == "showrunner": seen.append(system)
        return real(role, system, prompt, **k)
    monkeypatch.setattr(ROOM, "ask", spy)
    d = SA.draw("EPT", "collective")
    sp = ROOM.scout_and_pick(d, dict(_ctx(), trends="", lessons="", defs={}), "EPT")
    assert "Glass Bones" in seen[0] and "TEASED AT THE END" in seen[0] and sp.get("next_tease")
    assert sp.get("teased_premise") == "What if your bones turned to glass for a day?" and core.S("NEXT_PREMISE")      # v8.9.1: kept until the plan is saved

def test_ensure_tease_appends_only_when_missing():
    t = {"premise": "What if your bones turned to glass?", "headline": "Glass Bones", "line": "Next time: your bones turn to glass."}
    s1 = ROOM.ensure_tease({"script": "## BEAT 1\n[DIRECTOR] Hello there."}, t, "EP")["script"]
    assert s1.rstrip().endswith("[DIRECTOR] [callback] Next time: your bones turn to glass.")
    s2 = {"script": "## BEAT 1\n[DIRECTOR] Next week your bones become glass, honestly."}
    assert ROOM.ensure_tease(s2, t, "EP") == s2

# ---------------- K76 preventive checks
def _S(shots, n=4, kl=1, lv=1, dur=60.0, titles=("A title",)):
    return {"shots": shots, "plan": {"kling": kl, "living": lv}, "vo": {"duration": dur}, "pkg": {"titles": list(titles)}, "d": {"promise": {"title": "Promise"}}, "room": {"spine": {}}}

def test_plan_check_repairs_before_money_and_never_raises_counts(setting):
    units = [{"text": f"line {i}"} for i in range(4)]
    S_ = EP.plan_check(_S([{"type": "kling", "prompt": ""}, {"type": "kling", "prompt": "b"}, {"type": "living", "prompt": "c"}], titles=()), units)
    sh = S_["shots"]; assert len(sh) == 4 and sum(s["type"] == "kling" for s in sh) == 1 and all(STYLE_LOCK in s["prompt"] for s in sh if s["type"] != "graphic")
    assert S_["pkg"]["titles"] == ["Promise"] and S_["plan_check"]["repairs"] >= 3
    with pytest.raises(RuntimeError): EP.plan_check(_S([]), units)
    with pytest.raises(RuntimeError): EP.plan_check(_S([{"type": "still", "prompt": "a"}], dur=5.0), units)

def test_reel_captions_keep_at_most_five_hashtags():
    assert MG.cap_hashtags("Go #a #b #c #d #e #f #g").count("#") == 5

# ---------------- K77 change handler
def test_pr_ready_email_has_a_one_click_merge_link(monkeypatch, setting):
    sent = []
    monkeypatch.setattr(MG.PUB, "email", lambda subj, html, **k: sent.append((subj, html)))
    for k, v in (("GH_REPO", "me/re"), ("PR_NUMBER", "12"), ("PR_TITLE", "Better hooks"), ("PR_URL", "https://github.com/me/re/pull/12")): monkeypatch.setenv(k, v)
    link = MG.pr_ready(); assert "issues/new?title=MERGE%20%2312" in link and sent and "MERGE" in sent[0][1]
    setting("PR_MAIL_ON", "FALSE"); sent.clear(); assert MG.pr_ready() is None and not sent

def test_pr_ready_never_raises_and_ignores_non_pr_runs(monkeypatch):
    monkeypatch.delenv("PR_NUMBER", raising=False); assert MG.pr_ready() is None
    monkeypatch.setenv("GH_REPO", "me/re"); monkeypatch.setenv("PR_NUMBER", "3")
    def boom(*a, **k): raise RuntimeError("gmail down")
    monkeypatch.setattr(MG.PUB, "email", boom); assert MG.pr_ready() is None

def test_merge_workflow_is_owner_only_and_merges_only_green_changes():
    import yaml
    y = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "merge.yml"))); job = y["jobs"]["merge"]
    assert "github.repository_owner" in job["if"] and "MERGE #" in job["if"]
    run = job["steps"][0]["run"]; assert run.index("gh pr checks") < run.index("gh pr merge")
    ck = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "checks.yml")))["jobs"]["guard_and_rehearsal"]["steps"][-1]
    assert "pull_request" in ck["if"] and "success()" in ck["if"] and "prready" in ck["run"]

def test_claude_md_and_deployed_kernel_exist_and_match_the_package():
    t = open(os.path.join(ROOT, "CLAUDE.md")).read()
    for must in ("4,000", "integration checklist", "plan_guard", "rehearsal", "Merge", "Premium tier", "docs/CHANGES.md"): assert must in t
    k = open(os.path.join(ROOT, "docs", "KERNEL.md")).read(); assert "K77" in k
    pk = os.path.join(os.path.dirname(ROOT), "FOR_CLAUDE", "KERNEL.md")
    if os.path.exists(pk): assert open(pk).read() == k          # in the package the two copies are identical; on GitHub only the repo copy exists

# ---------------- cost: unchanged by v8.9
def test_v89_adds_no_cost(setting):
    setting("PRICE_KLING_USD", "0.25")      # v10.1: this cost golden keeps the Kling 2.1 price; the new $0.35 is tested in test_v101
    d = SA.draw("EPC", "collective"); d.update(stills=52, living=8, kling=3)
    assert abs(EP.est_cost_inr(d) - G.voice_think_inr() - 376.45) < 1.0      # v8.10: only the TTS / thinking / new-room allowances were added
    assert d["tier"] == "public" and d["guest"] in GUESTS

# ---------------- K72 (owner request): stronger, varied moves everywhere + validated Director suggestions, no new cost
def _travel(move, energy, seed=1):
    ww, wh = 640, 360; sw, sh = int(ww * 1.3), int(wh * 1.3); base = ww / (sw / 1.3)
    cam = RN.camera_path(move, 90, sw, sh, ww, wh, base, random.Random(seed), energy)
    zs = [c[2] / base for c in cam]; xs = [c[0] for c in cam]; ys = [c[1] for c in cam]; th = [c[3] for c in cam]
    return (max(zs) - min(zs)) + (max(xs) - min(xs)) / sw + (max(ys) - min(ys)) / sh + (max(th) - min(th))

def test_every_move_actually_moves_and_high_energy_moves_more():
    for mv in RN.CAMERA_MOVES:
        calm, high = _travel(mv, "calm"), _travel(mv, "high")
        assert calm > 0.02, mv                         # no move is a near-static still
        assert high >= calm, mv                        # opening / pre-reaction shots get the strongest treatment

def test_calm_moves_are_stronger_than_the_old_gentle_push():
    ww, wh = 640, 360; sw, sh = int(ww * 1.3), int(wh * 1.3); base = ww / (sw / 1.3)
    z = [c[2] / base for c in RN.camera_path("push_parallax", 60, sw, sh, ww, wh, base, random.Random(2), "calm")]
    assert max(z) - min(z) >= 0.14                     # v8.7 gentle push travelled 0.16 at most, with no parallax roll or rack; calm is now ~0.15, high ~0.22

def test_director_suggestion_is_used_only_when_valid_allowed_and_not_a_repeat():
    rng = random.Random(5)
    assert RN.pick_move("orbit", rng, "high", None) == "orbit"
    assert RN.pick_move("whip_settle", rng, "calm", None) != "whip_settle"          # whip-and-settle only on strong shots
    assert RN.pick_move("drift", rng, "calm", "drift") != "drift"                  # never the same move twice in a row
    m = RN.pick_move("spin_wildly", rng, "calm", None); assert m in RN.MOVES_CALM     # unknown = code chooses
    assert set(RN.CAMERA_MOVES) == set(RN.MOVES_HIGH) | set(RN.MOVES_CALM)

def test_normalise_keeps_only_library_moves_on_stills():
    units = [{"i": i, "text": f"line {i}", "tag": "none", "start": i * 5.0} for i in range(4)]
    shots = [{"unit": 0, "type": "still", "prompt": "a", "camera": "Orbit"}, {"unit": 1, "type": "still", "prompt": "b", "camera": "spin_wildly"},
             {"unit": 2, "type": "graphic", "graphic": {"kind": "counter", "label": "x", "from": 0, "to": 5, "unit": ""}, "camera": "orbit"},
             {"unit": 3, "type": "still", "prompt": "d"}]
    out = ROOM.normalise_shots(shots, units, {"kling": 0, "living": 0}, "look")
    assert out[0].get("camera") == "orbit" and "camera" not in out[1] and "camera" not in out[2] and "camera" not in out[3]

def test_suggested_move_reaches_the_renderer_and_frame_count_is_exact(tmp_path, setting, monkeypatch):
    from PIL import Image
    img = str(tmp_path / "a.jpg"); Image.fromarray((np.random.default_rng(3).random((300, 500, 3)) * 255).astype(np.uint8)).save(img)
    setting("CAMERA_MOTION", "dynamic"); RN._LAST["move"] = None; seen = []
    real = RN.camera_path
    monkeypatch.setattr(RN, "camera_path", lambda move, *a, **k: (seen.append(move), real(move, *a, **k))[1])
    out = RN.parallax_segment(img, str(tmp_path / "o.mp4"), 15, seed="s", energy="high", move="whip_settle")
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    assert seen == ["whip_settle"] and int(n) == 15
    RN.parallax_segment(img, str(tmp_path / "p.mp4"), 15, seed="s", energy="high", move="whip_settle")
    assert seen[-1] != "whip_settle"                   # the same suggestion twice in a row is overruled

def test_camera_moves_add_no_cost_and_change_no_counts(setting):
    setting("PRICE_KLING_USD", "0.25")      # v10.1: this cost golden keeps the Kling 2.1 price; the new $0.35 is tested in test_v101
    d = {"episode_id": "EPX", "stills": 52, "living": 8, "kling": 3}
    assert EP.est_cost_inr(d) - G.voice_think_inr() == pytest.approx(376.45, abs=0.5)        # same as v8.7 (v8.10 allowances aside): camera motion is code on pictures already paid for
    assert core.DEFAULTS["KLING_CLIPS"][0] == "3" and core.DEFAULTS["LIVING_STILLS"][0] == "8" and core.DEFAULTS["KLING_MIN_CLIPS"][0] == "3"
