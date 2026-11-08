"""v10.1: verified-API fixes and growth upgrades (8 Nov 2026). No keys, no network."""
import datetime as dt, json, os
import pytest
from whatifs import core, media as MD, publish as PUB, notify as NT, show as SHOW, similarity as SIM, demand as DM, viewers as VW, ypp as YPPM, carousel as CAR, manage as MG

def test_video_args_follow_each_models_schema():
    a = MD.video_args("fal-ai/kling-video/v2.6/pro/image-to-video", "u", "p", True)
    assert a["start_image_url"] == "u" and a["generate_audio"] is False and "image_url" not in a
    b = MD.video_args("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", "u", "p", True); assert b["image_url"] == "u" and b["cfg_scale"] == 0.5 and b["duration"] == "5"
    c = MD.video_args("wan/v2.6/image-to-video/flash", "u", "p"); assert c["resolution"] == "720p"
    assert MD.video_args("fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video", "u", "p")["duration"] == "6"
    assert core.DEFAULTS["FAL_HERO_MODEL"][0] == "fal-ai/kling-video/v2.5-turbo/pro/image-to-video" and core.DEFAULTS["PRICE_KLING_USD"][0] == "0.35"

def test_still_price_rounds_up_megapixels_and_new_size_costs_the_same():
    assert MD.still_usd(1872, 1056) == pytest.approx(0.006) and MD.still_usd(1632, 918) == pytest.approx(0.006) and MD.still_usd(720, 1280) == pytest.approx(0.003)

def test_retired_model_is_replaced(monkeypatch, setting):
    setting("FAL_HERO_MODEL", "fal-ai/kling-video/v2.1/standard/image-to-video")
    seen = []
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD, "fal_allowed", lambda: True)
    monkeypatch.setattr(MD, "fal_run", lambda model, args, timeout=0: seen.append((model, args)) or {"video": {"url": "x"}})
    monkeypatch.setattr(MD, "_dl", lambda url, path: path)
    MD.animate("https://img", None, "p", "/tmp/x.mp4", "EP", hero=True)
    assert seen[0][0] == "fal-ai/kling-video/v2.5-turbo/pro/image-to-video" and seen[0][1]["cfg_scale"] == 0.5

def test_upload_readback_does_not_refix_an_omitted_label_but_flags_kids(monkeypatch, setting):
    monkeypatch.setattr(PUB, "FAKE", False); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False); monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    calls = []; monkeypatch.setattr(PUB, "yt_set_label", lambda vid, on=True: calls.append(vid) or True)
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: {"privacyStatus": "public", "selfDeclaredMadeForKids": False})
    assert PUB.verify_upload("v1", "public") == [] and calls == []                     # field omitted on read: trusted, no extra update
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: {"privacyStatus": "public", "containsSyntheticMedia": False, "madeForKids": True})
    f = PUB.verify_upload("v2", "public")
    assert calls == ["v2"] and any("made for kids" in x for x in f) and any(r["kind"] == "kids_flag" for r in core.store().rows("Owner_Actions"))

def test_verdict_style_rotates_and_repairs_repeats(setting):
    core.store().append("Show_Log", [{"plan_json": json.dumps({"verdict": {"style": s}})} for s in ("clear ruling", "split decision", "appeal granted on new evidence")])
    nxt = SHOW.next_style(); assert nxt not in ("clear ruling", "split decision", "appeal granted on new evidence")
    assert "VERDICT STYLE" in SHOW.prompt_block()

def test_similarity_guard_flags_a_near_copy(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    base = " ".join(f"Vale observes the falling moon number {i} and Grimm objects loudly" for i in range(40))
    assert SIM.check(base, "E1")[0] == 0.0
    s, who = SIM.check(base + " one new line at the end", "E2"); assert s > 0.5 and who == "E1"      # MinHash estimate of a near copy
    assert any(r["kind"] == "similar_script" for r in core.store().rows("Owner_Actions"))
    other = " ".join(f"Nana Rosa pours tea while the ocean drains away step {i} quietly" for i in range(40))
    assert SIM.check(other, "E3")[0] < 0.2

def test_demand_scores_once_and_lifts_the_bench(setting):
    core.store().append("Premise_Bench", [{"bench_id": "B1", "status": "READY", "headline": "What if the Moon vanished", "combined": "7", "demand_json": ""}])
    assert DM.run() == 1 and DM.run() == 0
    b = core.store().rows("Premise_Bench")[0]; dj = json.loads(b["demand_json"]); assert 0 <= dj["search_score"] <= 1 and float(b["combined"]) >= 7
    assert DM.score_views([10_000_000] * 5) == 1.0 and DM.score_views([500]) == 0.0

def test_viewer_questions_collected_once_and_given_to_the_scout_as_data():
    core.store().append("Episodes", [{"episode_id": "E1", "yt_id": "y1", "slot_et": (core.now_utc() - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")}])
    assert VW.collect() == 1 and VW.collect() == 0
    assert "VIEWER QUESTIONS" in VW.scout_block() and "Moon had rings" in VW.scout_block() and core.DEFAULTS["VIEWER_NAME_ON_SCREEN"][0] == "FALSE"

def test_ypp_card_only_when_the_proxy_passes(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    monkeypatch.setattr(YPPM, "progress", lambda now=None: {"subs": 420, "hours": 3100, "shorts_views_90d": 0, "uploads_90d": 8, "at": "t"})
    YPPM.check(); assert not any(r["kind"] == "ypp_tier" for r in core.store().rows("Owner_Actions"))
    monkeypatch.setattr(YPPM, "progress", lambda now=None: {"subs": 512, "hours": 3100, "shorts_views_90d": 0, "uploads_90d": 8, "at": "t"})
    YPPM.check(); assert len([r for r in core.store().rows("Owner_Actions") if r["kind"] == "ypp_tier"]) == 1
    assert json.loads(core.S("YPP_PROGRESS"))["subs"] == 512

def test_carousel_prepare_and_post_in_fake_mode(tmp_path, monkeypatch):
    ep = "EPC1"; d = os.path.join(core.WORK, ep, "shots"); os.makedirs(d, exist_ok=True)
    from PIL import Image
    for i in range(6): Image.new("RGB", (1872, 1056), (30 * i, 80, 120)).save(os.path.join(d, f"s{i}.png"))
    for i in range(6):
        with open(os.path.join(d, f"s{i}.png"), "ab") as f: f.write(os.urandom(30000))
    plan = {"charge": "The Moon is accused of leaving", "exhibits": [{"id": "A", "what": "Tides would stop", "objection": "Preposterous"}, {"id": "B", "what": "Nights get darker"}]}
    fids = CAR.prepare(ep, plan, "What If the Moon Left?")
    assert fids and len(fids) == 4
    from PIL import Image as I2
    im = I2.open(os.path.join(core.WORK, ep, "carousel", "slide1.jpg")); assert im.size == (1080, 1350) and im.format == "JPEG"
    assert CAR.post(ep) == "FAKE_CAROUSEL" and CAR.post(ep) is None

def test_v101_flips_move_only_old_defaults(setting):
    st = core.store(); st.append("Settings", [{"key": "FAL_HERO_MODEL", "value": "fal-ai/kling-video/v2.1/standard/image-to-video", "note": ""},
                                              {"key": "SHORTS_WEEKLY_CAP", "value": "12", "note": ""}, {"key": "STILL_W", "value": "1632", "note": ""}])
    core._settings_cache = None
    done = MG.v101_upgrade(st)
    assert "FAL_HERO_MODEL" in done and "STILL_W" in done and "SHORTS_WEEKLY_CAP" not in done and MG.v101_upgrade(st) == []
    assert core.S("SHORTS_WEEKLY_CAP", int) == 12

def test_episode_estimate_with_the_new_kling_price():
    from whatifs import governor as G
    fx = core.S("USD_INR", float)
    assert G.full_episode_inr() > 0 and core.S("PRICE_KLING_USD", float) == 0.35      # three hero clips now cost about Rs 28 more per episode than with Kling 2.1

def test_frame_rate_compared_as_numbers_not_text(monkeypatch):
    from whatifs import qc as Q
    assert Q._fps_num("30/1") == 30.0 and abs(Q._fps_num("10163200/338821") - 29.9958) < 1e-3 and Q._fps_num("bad") == 0.0
    monkeypatch.setattr(Q, "_probe_json", lambda args: {"streams": [{"nb_read_packets": "1985", "r_frame_rate": "30/1", "avg_frame_rate": "10163200/338821"}]})
    assert Q.packet_check("x.mp4", 66.176, 30) == []                                   # a 1-tick concat rounding is constant frame rate
    monkeypatch.setattr(Q, "_probe_json", lambda args: {"streams": [{"nb_read_packets": "1985", "r_frame_rate": "30/1", "avg_frame_rate": "25/1"}]})
    assert any("variable frame rate" in p["detail"] for p in Q.packet_check("x.mp4", 66.176, 30))

def test_without_a_meta_key_instagram_steps_are_skipped_quietly(monkeypatch, setting):
    monkeypatch.setattr(PUB, "FAKE", False); monkeypatch.delenv("META_PAGE_KEY", raising=False)
    setting("IG_USER_ID", ""); setting("FB_PAGE_ID", "")
    assert PUB.meta_ready() is False
    assert CAR.prepare("EPX", {}, "t") is None and CAR.post("EPX") is None
    monkeypatch.setenv("META_PAGE_KEY", "k"); setting("IG_USER_ID", "1789")
    assert PUB.meta_ready() is True

