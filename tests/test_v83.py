"""v8.3: one episode per slot, no third voice, tolerant label parser, like/subscribe/share asks, vision judge required, black-frame false positives,
render size, safe uploads, crash-safe spend, fact check, guardian, repair bot, hold rules, housekeeping."""
import os, re, json, subprocess, datetime as dt
import numpy as np
from whatifs import core, cta as CTA, qc as QC, voice as V, publish as PUB, format_engine as FE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- the voice parser: every way a model writes a speaker name
def _spk(s): return [(u.speaker, u.tag, u.text) for u in V.parse_script(s)]

def test_a_label_alone_on_its_line_applies_to_the_next_line():
    assert _spk("[DIRECTOR]\nThe ocean would boil.\n[SKEPTIC]\nWait, seriously?") == [("DIRECTOR", "none", "The ocean would boil."), ("SKEPTIC", "none", "Wait, seriously?")]

def test_markdown_and_plain_name_labels_are_never_spoken():
    out = _spk("**Director:** The ocean would boil.\n**Skeptic:** Wait what?\nDirector - Because physics.")
    assert [o[0] for o in out] == ["DIRECTOR", "SKEPTIC", "DIRECTOR"] and all("irector" not in o[2] and "keptic" not in o[2] and "*" not in o[2] for o in out)

def test_the_curious_one_in_any_spelling_is_the_skeptic_voice():
    out = _spk("[CURIOUS ONE] [wow] No way!\n[THE CURIOUS ONE]: That's insane.\nCurious One (whispering): Oh no.")
    assert [o[0] for o in out] == ["SKEPTIC"] * 3 and out[0][1] == "wow" and out[1][2] == "That's insane." and out[2][2] == "Oh no."

def test_stage_directions_are_dropped_and_a_laugh_becomes_the_laugh_tag():
    out = _spk("[SKEPTIC] (laughing) Okay that's wild.\n[SKEPTIC] (quietly) Fine.")
    assert out == [("SKEPTIC", "laugh", "Okay that's wild."), ("SKEPTIC", "none", "Fine.")]

def test_ordinary_words_that_look_like_labels_are_left_alone():
    out = _spk("Skeptic-minded people disagree. The Director's cut is long.")
    assert all(o[0] == "NARRATOR" for o in out) and "Skeptic-minded" in out[0][2]

class _Rec:
    """A voice backend that records which voice pack each unit was spoken with."""
    def __init__(self): self.packs = {"NARRATOR": 0}; self.used = []
    def register_speaker(self, spk, blend): self.packs[spk.upper()] = 1
    def synth(self, text, speed, speaker="NARRATOR"):
        self.used.append(speaker); n = int(24000 * 0.4); a = (0.1 * np.sin(np.arange(n) / 9)).astype(np.float32)
        a = np.concatenate([np.zeros(1800, np.float32), a])           # 75 ms of leading silence, like a real engine
        return a, [{"w": "x", "s": 0.075, "e": 0.3}]

def test_in_the_two_role_format_there_is_never_a_third_voice(tmp_path):
    be = _Rec(); B = V.Blend("n", {"af_heart": 1.0})
    r = V.narrate("The first line has no label.\n[SKEPTIC] A question?\n[DIRECTOR] An answer.", B, str(tmp_path / "n"), backend=be, speaker_blends={"DIRECTOR": B, "SKEPTIC": B})
    assert "NARRATOR" not in be.used and be.used[0] == "DIRECTOR"
    tl = json.load(open(r.timeline_path)); assert [u["speaker"] for u in tl["units"]] == ["DIRECTOR", "SKEPTIC", "DIRECTOR"]

def test_word_times_move_with_the_trimmed_audio(tmp_path):
    be = _Rec(); B = V.Blend("n", {"af_heart": 1.0})
    r = V.narrate("[DIRECTOR] One line.", B, str(tmp_path / "w"), backend=be, speaker_blends={"DIRECTOR": B, "SKEPTIC": B}, humanize=False)
    u = json.load(open(r.timeline_path))["units"][0]
    assert 0.0 <= u["words"][0]["s"] - u["start"] < 0.06            # the 0.075 s of silence was cut, so the word now starts ~0.03 s into the unit (v8.2: 0.075 s late)

def test_the_hook_is_inserted_as_a_director_line_in_the_two_role_format():
    from whatifs import hooks
    new, ok, _ = hooks.apply_to_script("## BEAT 1\n[DIRECTOR] [calm] A very different opening sentence here.", "Eight billion people do it at noon.")
    assert ok and "[DIRECTOR] [tension] Eight billion people do it at noon." in new

def test_reel_lines_are_labelled_so_they_use_the_two_voices():
    from whatifs.reels import _label_lines
    assert _label_lines(["[tension] Every pillow left.", "[SKEPTIC] Wait."], {"DIRECTOR": 1})[0].startswith("[DIRECTOR] ") and _label_lines(["[tension] x"], None) == ["[tension] x"]

# ---------------------------------------------------------------- like / subscribe / share
def test_every_hand_written_ask_is_recognised_as_its_own_kind_and_is_short():
    for kind, pool in CTA.POOLS.items():
        assert len(pool) >= 6
        for entry in pool:
            assert kind in {CTA.kind_of_text(t[2]) for t in entry}, (kind, entry)
            assert sum(len(t[2].split()) for t in entry) <= 34

def test_ordinary_science_sentences_are_not_mistaken_for_asks():
    for s in ("Two plates share a border.", "The water would like to escape.", "Send the signal to Mars.", "A like-minded crowd gathers."):
        assert CTA.kind_of_text(s) is None, s

def _script(n=30, with_reveals=True):
    return "\n".join(["## BEAT 1"] + [f"[{'DIRECTOR' if i % 2 == 0 else 'SKEPTIC'}] [{'reveal' if (with_reveals and i % 5 == 0) else 'calm'}] Plain sentence number {i} about the simulation." for i in range(n)])

def test_missing_asks_are_added_at_calm_moments_and_never_twice():
    s, added, code = CTA.ensure(_script(), "EPX", "")
    assert sorted(added) == ["like", "share", "subscribe"] and all(CTA.check(s).values())
    lines = [l for l in s.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if CTA.kind_of_text(re.sub(r"^(\[[^\]]+\]\s*)+", "", l)):
            assert "[reveal]" not in l and "[wow]" not in l and "[gasp]" not in l
    s2, added2, _ = CTA.ensure(s, "EPX", code); assert added2 == [] and s2 == s

def test_the_writers_own_asks_are_kept_and_only_the_missing_kind_is_added():
    base = _script().split("\n"); base.insert(12, "[SKEPTIC] [aside] Hit like if you stuck around for this, I'm flexible."); base.insert(20, "[DIRECTOR] [calm] Subscribe, so you are here for the next one.")
    s, added, _ = CTA.ensure("\n".join(base), "EPY", "")
    assert added == ["share"] and s.count("Hit like") == 1

def test_the_share_ask_sits_before_the_final_line_and_two_episodes_do_not_repeat_a_line():
    s1, _, c1 = CTA.ensure(_script(), "EP1", ""); s2, _, c2 = CTA.ensure(_script(), "EP2", c1)
    lines = [l for l in s1.split("\n") if l.strip()]; idx = [i for i, l in enumerate(lines) if CTA.kind_of_text(re.sub(r"^(\[[^\]]+\]\s*)+", "", l)) == "share"][0]
    assert len(lines) - idx <= 4
    p1 = dict((p[0], p[1:]) for p in c1.split(",")); p2 = dict((p[0], p[1:]) for p in c2.split(","))
    assert all(p1[k] != p2[k] for k in p1)

def test_a_short_or_odd_script_is_returned_unchanged():
    assert CTA.ensure("[DIRECTOR] hi", "E", "")[0] == "[DIRECTOR] hi" and CTA.ensure("", "E", "")[0] == ""

def test_cta_can_be_switched_off(setting):
    from whatifs import room as ROOM
    setting("CTA_ON", "FALSE"); assert core.S("CTA_ON", bool) is False

def test_the_chip_draws_only_while_an_ask_is_spoken_and_keeps_the_frame_size():
    from whatifs.overlay import CtaChip
    units = [{"start": 1.0, "end": 3.0, "text": "Hit like and that is one tiny shove.", "speaker": "SKEPTIC"}, {"start": 5.0, "end": 6.0, "text": "A plain sentence.", "speaker": "DIRECTOR"}]
    chip = CtaChip(units, 640, 360, 24); fr = np.full((360, 640, 3), 30, np.uint8)
    off = chip.apply(fr.copy(), int(8.0 * 24)); assert (off == fr).all()
    on = chip.apply(fr.copy(), int(2.0 * 24)); assert on.shape == fr.shape and (on != fr).any() and (on[:, :200] == fr[:, :200]).all()      # right side only; the speaker chip's side is untouched
    for text in ("Subscribe now.", "Send this to a friend."):
        c = CtaChip([{"start": 0, "end": 2, "text": text}], 640, 360, 24); assert (c.apply(fr.copy(), 24) != fr).any()

def test_the_description_ends_with_a_witty_subscribe_line_and_a_link():
    f = CTA.description_footer("EP1", "https://www.youtube.com/channel/X?sub_confirmation=1")
    assert "sub_confirmation=1" in f and "ubscribe" in f and len(f.splitlines()) == 3
    from whatifs import episode as EP
    d = EP._description("Hook line.\n\nChapters\n\n#a #b #c", [("0:00", "A"), ("1:00", "B"), ("2:00", "C")], {"spine": {"premise": "p"}}, "EP1")
    assert "0:00 A" in d and "ubscribe" in d and d.count("Chapters") == 1
    d2 = EP._description("No chapter word here", [("0:00", "A"), ("1:00", "B"), ("2:00", "C")], {}, "EP1"); assert "1:00 B" in d2

def test_each_reel_ends_with_a_follow_or_a_share_ask():
    a = CTA.reel_ask("EP1", 0); b = CTA.reel_ask("EP1", 1)
    assert "ollow" in a[2] and CTA.kind_of_text(b[2]) == "share"

# ---------------------------------------------------------------- final QC
def _dark(path, stars, secs=4):
    import cv2
    rng = np.random.default_rng(3); im = np.zeros((360, 640, 3), np.uint8)
    for _ in range(stars): im[rng.integers(0, 360), rng.integers(0, 640)] = 255
    cv2.imwrite(path + ".png", im)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", path + ".png", "-t", str(secs), "-r", "24", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", path], check=True)

def test_a_starfield_is_not_a_black_screen_but_a_black_screen_is(tmp_path):
    def black(p): return " ".join(QC._ff(["-i", p, "-vf", QC.BLACKDETECT, "-an"]).split("\n")).count("black_start")
    _dark(str(tmp_path / "stars.mp4"), 400); _dark(str(tmp_path / "void.mp4"), 0)
    assert black(str(tmp_path / "stars.mp4")) == 0 and black(str(tmp_path / "void.mp4")) >= 1

def test_an_unreachable_picture_judge_holds_the_video_instead_of_passing_it(monkeypatch, tmp_path, setting):
    from whatifs import models
    monkeypatch.setattr(models, "ask_vision", lambda *a, **k: None)
    _dark(str(tmp_path / "m.mp4"), 300)
    units = [{"i": i, "start": i * 0.5, "end": i * 0.5 + 0.4, "text": "x"} for i in range(6)]
    probs, info = QC.vision_check(str(tmp_path / "m.mp4"), units, [{"type": "still"}] * 6, "ep")
    assert [p["code"] for p in probs] == ["vision_unavailable"] and info["vision"] == "unavailable"
    setting("QC_VISION_REQUIRED", "FALSE"); assert QC.vision_check(str(tmp_path / "m.mp4"), units, [{"type": "still"}] * 6, "ep")[0] == []

# ---------------------------------------------------------------- render size
def test_the_default_encode_settings_are_light_and_the_grain_can_be_switched_off(setting):
    from whatifs import render as RN
    a = RN._enc_args(640, 360); assert a[a.index("-crf") + 1] == "20" and "noise=alls=3" in a[1]
    setting("GRAIN_LEVEL", "0"); assert "noise" not in RN._enc_args(640, 360)[1]

def test_the_audio_bed_is_not_identical_in_two_episodes(tmp_path):
    from whatifs import render as RN
    import soundfile as sf
    sf.write(str(tmp_path / "v.wav"), (np.random.default_rng(1).standard_normal(24000 * 4) * 0.05).astype(np.float32), 24000)
    a = RN.score(4, "EPA", [("boom", 1.0)], str(tmp_path / "v.wav")); b = RN.score(4, "EPB", [("boom", 1.0)], str(tmp_path / "v.wav"))
    assert a.shape == b.shape and not np.allclose(a, b)

# ---------------------------------------------------------------- uploads
def test_metadata_is_cleaned_before_it_can_cause_a_400_after_the_money_is_spent():
    t, d, tags = PUB.clean_meta("<b>What If</b>  " + "x" * 200, "Hello <script> " + "é" * 4000, ["ok tag", "bad<tag>", "OK TAG", "a" * 80, "x,y"] + [f"t{i}" for i in range(80)])
    assert "<" not in t and len(t) <= 100 and "<" not in d and len(d.encode("utf-8")) <= 4900
    assert len(tags) <= 30 and all(len(x) <= 30 and "<" not in x for x in tags) and len({x.lower() for x in tags}) == len(tags) and sum(len(x) + 3 for x in tags) <= 500

def test_a_retried_upload_resumes_the_same_session_and_never_makes_a_second_video(monkeypatch, tmp_path):
    f = tmp_path / "m.mp4"; f.write_bytes(b"x" * 2000)
    monkeypatch.setattr(core, "FAKE", False); monkeypatch.setattr(PUB, "FAKE", False); monkeypatch.setattr(PUB, "gheaders", lambda: {"Authorization": "Bearer t"})
    monkeypatch.setattr(PUB, "retry", lambda fn, tries=3, wait=1, what="": _retry2(fn))
    calls = {"post": 0, "put": 0}
    class R:
        def __init__(s, code, js=None, hdr=None): s.status_code = code; s._j = js or {}; s.headers = hdr or {}; s.text = ""
        def json(s): return s._j
    def post(url, **k): calls["post"] += 1; return R(200, hdr={"Location": "https://up/session1"})
    def put(url, headers=None, data=None, **k):
        calls["put"] += 1
        if headers.get("Content-Range", "").startswith("bytes */"): return R(200, {"id": "VID_DONE"})      # the first upload had actually completed
        if calls["put"] == 1: raise PUB.requests.ConnectionError("final answer lost")
        raise AssertionError("must not re-send data once the session reports it is complete")
    monkeypatch.setattr(PUB.requests, "post", post); monkeypatch.setattr(PUB.requests, "put", put)
    monkeypatch.setattr(PUB.time, "sleep", lambda s: None)
    vid = PUB.yt_upload(str(f), "T", "D", ["a"], publish_at="2099-01-01T00:00:00Z")
    assert vid == "VID_DONE" and calls["post"] == 1

def _retry2(fn):
    try: return fn()
    except Exception: return fn()

# ---------------------------------------------------------------- spend and the month
def test_spend_reaches_the_sheet_within_a_few_rows_and_other_jobs_spend_is_seen():
    for i in range(7): core.cost("t", "fal", 1, 0.01)
    assert len(core.store().rows("Cost_Log")) >= 6                       # flushed on the way, not only at the end of the job
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "OTHER", "item": "x", "provider": "fal", "units": 1, "inr": 500.0}])
    before = core.month_spend(); core.refresh_spend(); assert core.month_spend() >= before + 499

def test_fal_cost_is_logged_before_the_download_can_fail(monkeypatch, tmp_path):
    from whatifs import media
    monkeypatch.setattr(media, "FAKE", False); monkeypatch.setattr(media, "fal_run", lambda m, a, **k: {"images": [{"url": "http://x/y.jpg"}]})
    def boom(u, p): raise RuntimeError("download failed")
    monkeypatch.setattr(media, "_dl", boom)
    try: media.still("p", str(tmp_path / "a.jpg"), "EPC")
    except Exception: pass
    assert any(r["item"].startswith("image") for r in core.store().rows("Cost_Log")) or any(r["item"].startswith("image") for r in core._cost_buf)

def test_a_cut_reply_is_retried_once_with_more_room_instead_of_paying_the_same_again(monkeypatch):
    from whatifs import models
    monkeypatch.setattr(models, "FAKE", False); sizes = []
    def fake(role, system, prompt, mt, temp, search, ep=None):
        sizes.append(mt)
        if len(sizes) == 1: raise models.Truncated("cut")
        return '{"ok": true}'
    monkeypatch.setattr(models, "_claude", fake); monkeypatch.setattr(models, "model", lambda r: "m"); monkeypatch.setattr("whatifs.governor.monthly_cap_reached", lambda **k: False)      # v8.7 fix: ask() imports it from governor; models never had this name, so the old patch raised AttributeError
    monkeypatch.setattr(models.time, "sleep", lambda s: None)
    try: r = models.ask("sonnet", "s", "p", max_tokens=1000)
    except Exception as e: r = str(e)
    assert sizes[:2] == [1000, 1700] and r == {"ok": True}

def test_the_price_cells_match_the_published_list_prices():
    assert core.S("PRICE_SONNET_IN", float) == 2 and core.S("PRICE_SONNET_OUT", float) == 10 and core.S("PRICE_OPUS_IN", float) == 4 and core.S("PRICE_OPUS_OUT", float) == 20

def test_lean_tier_keeps_the_full_runtime():
    from whatifs import governor as G
    assert dict((t[0], t[1]) for t in G.TIERS)["lean"] == 600 and G.TIERS[-1][1] == 505

# ---------------------------------------------------------------- one episode per slot, holds, housekeeping
def test_a_slot_that_already_has_an_episode_is_not_produced_twice():
    from whatifs import episode as EP
    core.store().append("Episodes", [{"episode_id": "EPA", "slot_et": "2099-01-01T10:00:00Z", "status": "SCHEDULED"}])
    r = EP.produce("2099-01-01T10:00:00Z"); assert r["skipped"] == "slot_taken" and len(core.store().rows("Episodes")) == 1
    core.store().update("Episodes", "episode_id", "EPA", {"status": "FAILED"}); assert EP._slot_taken(core.store(), "2099-01-01T10:00:00Z") is None

def test_one_held_video_no_longer_stops_the_next_slot_but_two_do(setting, monkeypatch):
    from whatifs import manage as MG
    hold = lambda i: {"episode_id": f"EPH{i}", "slot_et": f"2099-01-0{i}T10:00:00Z", "status": "HOLD_QC"}
    soon = core.now_utc() + dt.timedelta(hours=5)
    monkeypatch.setattr(MG, "next_slots", lambda n=4: [soon]); monkeypatch.setattr(MG.G, "can_start_episode", lambda: (True, "")); monkeypatch.setattr(MG.PUB, "email", lambda *a, **k: None)
    assert core.S("HOLD_BLOCK_AFTER", int) == 2
    core.store().append("Episodes", [hold(1)])
    assert MG._produce_slot(core.store().rows("Episodes")) == soon.strftime("%Y-%m-%dT%H:%M:%SZ")      # one held video: the next slot still goes ahead
    core.store().append("Episodes", [hold(2)])
    assert MG._produce_slot(core.store().rows("Episodes")) is None                                    # two held at once: production waits for the owner
    setting("HOLD_BLOCK_AFTER", "1"); core.store().update("Episodes", "episode_id", "EPH2", {"status": "KILLED"})
    assert MG._produce_slot(core.store().rows("Episodes")) is None                                    # the old strict rule is one setting away

def test_a_stuck_private_video_that_became_public_is_closed_as_live(monkeypatch):
    from whatifs import manage as MG
    t = (core.now_utc() + dt.timedelta(hours=-30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": "EPS", "slot_et": t, "status": "STUCK_PRIVATE", "yt_id": "V1", "updated": "2000-01-01T00:00:00Z"}])
    monkeypatch.setattr(MG.PUB, "yt_status", lambda v: "public"); MG.recover_stuck(core.store().rows("Episodes"))
    assert core.store().rows("Episodes")[0]["status"] == "LIVE"

def test_a_policy_pause_needs_an_official_source():
    from whatifs import manage as MG
    assert MG._official("https://support.google.com/youtube/answer/1") and MG._official("https://blog.youtube/news") and not MG._official("https://evil-youtube.com/x") and not MG._official("")

def test_reaction_lessons_are_written_when_a_video_has_a_retention_curve():
    from whatifs import manage as MG
    core.store().append("Reaction_Map", [{"episode_id": "EPR", "t": 100.0, "kind": "wow", "word": "WOW", "line": "x", "style": "", "total_sec": 500}])
    curve = [(i / 100.0, 1.0 - i / 400.0) for i in range(100)]
    MG._reaction_learning([{"episode_id": "EPR", "curve": curve}])
    assert any(r.get("applies_to") == "reactions" for r in core.store().rows("Lessons"))

# ---------------------------------------------------------------- fact check, script format, safety rails
def test_a_claim_judged_wrong_is_fixed_once_and_two_stubborn_ones_stop_the_episode_before_any_picture_money(monkeypatch):
    from whatifs import room as ROOM
    script = {"script": "## BEAT 1\n[DIRECTOR] [calm] The sun is a planet.\n[SKEPTIC] [calm] Is it really?", "facts": []}
    seq = {"n": 0}
    def ask(role, *a, **k):
        if k.get("fake_key") == "factcheck":
            seq["n"] += 1
            return {"issues": [{"claim": "sun", "severity": "wrong", "correction": "star"}, {"claim": "x", "severity": "wrong", "correction": "y"}]}
        return {"script": "## BEAT 1\n[DIRECTOR] [calm] The sun is a star.\n[SKEPTIC] [calm] Is it really?", "changes": "fix"}
    monkeypatch.setattr(ROOM, "ask", ask)
    try: ROOM.fact_check({"premise": "p"}, script, "EPF"); raised = False
    except RuntimeError as e: raised = "premise skipped" in str(e)
    assert raised and seq["n"] == 2            # checked, fixed once, checked again: then the premise is skipped
    def ask_ok(role, *a, **k):
        if k.get("fake_key") == "factcheck": return {"issues": [{"claim": "n", "severity": "weak", "correction": "c"}]}
        raise AssertionError("no fix needed")
    monkeypatch.setattr(ROOM, "ask", ask_ok); assert ROOM.fact_check({"premise": "p"}, script, "EPF") is script

def test_an_unreachable_fact_checker_never_blocks(monkeypatch):
    from whatifs import room as ROOM
    def boom(*a, **k): raise RuntimeError("down")
    monkeypatch.setattr(ROOM, "ask", boom); s = {"script": "x"}; assert ROOM.fact_check({}, s, "E") is s

def test_the_repair_bot_never_merges_the_files_that_guard_money_quality_or_publishing():
    src = open(os.path.join(ROOT, "tools", "repair.py")).read()
    for f in ("whatifs/qc.py", "whatifs/governor.py", "whatifs/fixes.py", "whatifs/publish.py", "whatifs/episode.py", "tools/plan_guard.py"): assert f in src
    assert "not protected" in src and "flush_costs" in src and "err[-1500:]" not in src

def test_the_repair_bot_ignores_failures_that_are_not_bugs():
    import yaml
    y = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "repair.yml"))); txt = json.dumps(y)
    for w in ("monthly budget", "scout failed", "all models failed", "529", "fact check", "No space left"): assert w in txt

def test_produce_and_release_jobs_have_read_only_repository_access_and_no_repo_token():
    for n in ("pipeline", "setup", "learn", "brief", "trends", "voices"):
        t = open(os.path.join(ROOT, ".github", "workflows", n + ".yml")).read()
        assert "contents: read" in t and "contents: write" not in t and "GH_TOKEN" not in t, n

def test_dependencies_are_bounded():
    for line in open(os.path.join(ROOT, "requirements.txt")).read().split():
        assert "<" in line, line

def test_the_two_role_prompts_agree_with_each_other():
    from whatifs import prompts as P
    assert "18-34" in P.HOUSE and "13-34" not in P.HOUSE and "UNTRUSTED TEXT" in P.HOUSE
    assert "AUDIENCE ASKS" in P.WRITER and '"cta"' in P.BIBLE and "subscribe_moment" not in P.BIBLE and "within 8%" in P.HUMANIZE
    assert FE.enrich_spine({})["skeptic_role"] == "The Curious One" and "Curious One" in FE.REALITY_ENGINE

def test_old_checkpoints_of_failed_episodes_are_cleared(monkeypatch):
    from whatifs import manage as MG, checkpoint as CK2
    cleared = []; monkeypatch.setattr(CK2, "clear", lambda ep: cleared.append(ep)); monkeypatch.setattr(MG, "_CK", CK2)
    t = (core.now_utc() + dt.timedelta(hours=-30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"episode_id": "EPD", "slot_et": t, "status": "FAILED", "assets": {"_ckpt_plan.zip": "x"}}
    monkeypatch.setattr(CK2, "has", lambda r: True); MG.clean_dead_checkpoints([row]); assert cleared == ["EPD"]
