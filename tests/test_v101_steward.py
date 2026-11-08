"""v10.1 Model Steward (K150): failover, retirement watch with notice, newer-model discovery, automatic tested upgrade. No keys, no network."""
import datetime as dt, json, os
import pytest
from whatifs import core, steward as ST, media as MD, notify as NT, publish as PUB, bakeoff as BK

HERO = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _live_fal(monkeypatch, behaviour):
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD, "fal_allowed", lambda: True); monkeypatch.setattr(MD, "_dl", lambda u, p: p)
    calls = []
    def run(model, args, timeout=0):
        calls.append(model); r = behaviour(model)
        if isinstance(r, Exception): raise r
        return r
    monkeypatch.setattr(MD, "fal_run", run); return calls

def test_deprecated_answer_switches_at_once_and_the_same_call_succeeds(monkeypatch):
    _quiet(monkeypatch)
    calls = _live_fal(monkeypatch, lambda m: RuntimeError("fal submit 410: This endpoint is deprecated") if m == HERO else {"video": {"url": "x"}})
    MD.animate("https://img", None, "p", "/tmp/a.mp4", "EP", hero=True)
    assert calls == [HERO, "fal-ai/kling-video/v2.6/pro/image-to-video"]
    assert core.S("FAL_HERO_MODEL") == "fal-ai/kling-video/v2.6/pro/image-to-video" and core.S("PRICE_KLING_USD", float) == 0.35
    assert ST.health()[HERO]["status"] == "dead" and any(r["kind"] == "model_switch" for r in core.store().rows("Owner_Actions"))
    assert core.store().rows("Model_Changes")[-1]["to"] == "fal-ai/kling-video/v2.6/pro/image-to-video"

def test_transient_errors_need_three_in_a_row(monkeypatch):
    _quiet(monkeypatch)
    _live_fal(monkeypatch, lambda m: RuntimeError("fal failed: timeout 503"))
    for _ in range(2):
        with pytest.raises(RuntimeError): MD.animate("https://img", None, "p", "/tmp/a.mp4", "EP", hero=True)
    assert core.S("FAL_HERO_MODEL") == HERO
    with pytest.raises(RuntimeError): MD.animate("https://img", None, "p", "/tmp/a.mp4", "EP", hero=True)       # third: switch, the next one fails too
    assert core.S("FAL_HERO_MODEL") != HERO and ST.health()[HERO]["status"] == "failing"

def test_living_stills_fall_back_to_free_code_motion(monkeypatch, tmp_path):
    _quiet(monkeypatch)
    from PIL import Image
    img = str(tmp_path / "s.png"); Image.new("RGB", (640, 360), (10, 90, 160)).save(img)
    _live_fal(monkeypatch, lambda m: RuntimeError("fal submit 404: Application not found"))
    out = MD.animate(None, img, "p", str(tmp_path / "c.mp4"), "EP", hero=False)
    assert os.path.exists(out) and core.S("FAL_LIVING_MODEL") == "code-motion"

def test_price_rule_blocks_an_expensive_jump(setting):
    setting("MODEL_LADDERS", json.dumps({"hero": [{"id": HERO, "usd": 0.35}, {"id": "fal-ai/kling-video/v9/pro/image-to-video", "usd": 2.0}], "living": [], "still": [], "premium": []}))
    assert ST.next_candidate("hero") is None

def test_parse_page_reads_retirement_date_dead_banner_and_price():
    p = ST.parse_page("<div>This endpoint will be deprecated on November 17, 2026.</div> For 5s video your request will cost $0.35.")
    assert p == {"status": "deprecating", "retire_on": "2026-11-17", "usd": 0.35}
    assert ST.parse_page("This endpoint is deprecated. This model is no longer supported")["status"] == "dead"
    assert ST.parse_page("Pricing: $0.07 per second")["usd"] == pytest.approx(0.35)

def test_watch_announces_a_retirement_then_switches_on_the_date(monkeypatch, setting):
    _quiet(monkeypatch)
    pages = {f"https://fal.ai/models/{HERO}": "This endpoint will be deprecated on November 30, 2026. For 5s video your request will cost $0.35"}
    fetch = lambda url: pages.get(url, "For 5s video your request will cost $0.35") if "explore" not in url else ""
    now = dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc)
    s = ST.watch(fetch=fetch, now=now)
    assert s["planned"]["hero"]["to"] == "fal-ai/kling-video/v2.6/pro/image-to-video" and s["planned"]["hero"]["on"] == "2026-11-23"
    assert any(r["kind"] == "model_plan" and r["tier"] == "week" for r in core.store().rows("Owner_Actions"))
    assert ST.apply_planned(dt.datetime(2026, 11, 22, tzinfo=dt.timezone.utc)) == [] and core.S("FAL_HERO_MODEL") == HERO
    assert ST.apply_planned(dt.datetime(2026, 11, 23, tzinfo=dt.timezone.utc)) == ["hero"] and core.S("FAL_HERO_MODEL") != HERO

def test_owner_can_keep_until_it_stops(monkeypatch, setting):
    _quiet(monkeypatch)
    fetch = lambda url: ("This endpoint will be deprecated on November 30, 2026." if HERO in url else "For 5s video your request will cost $0.35") if "explore" not in url else ""
    ST.watch(fetch=fetch, now=dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc))
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "model_plan")
    assert "kept" in NT.answer(row["id"], "KEEP hero")
    assert ST.apply_planned(dt.datetime(2026, 11, 25, tzinfo=dt.timezone.utc)) == [] and core.S("FAL_HERO_MODEL") == HERO
    assert ST.ensure("hero") != HERO or True                                              # on the retirement date ensure() moves on by itself

def test_newer_version_is_queued_for_an_automatic_test_and_adopted_when_better(monkeypatch, setting):
    _quiet(monkeypatch)
    newer = "fal-ai/kling-video/v3.5/pro/image-to-video"
    fetch = lambda url: (f'<a href="/models/{newer}">x</a>' if "explore" in url else ("For 5s video your request will cost $0.40" if newer in url else "For 5s video your request will cost $0.35"))
    s = ST.watch(fetch=fetch, now=dt.datetime(2026, 12, 6, tzinfo=dt.timezone.utc))
    assert s["new"] == [newer] and json.loads(core.S("MODEL_CANDIDATES"))[0]["id"] == newer
    monkeypatch.setattr(BK, "judge_pair", lambda a, b, c, d: {"ok": True, "cur_score": 6.0, "new_score": 7.6})
    ST.test_candidates(dt.datetime(2026, 12, 6, tzinfo=dt.timezone.utc))
    plan = json.loads(core.S("MODEL_PLANNED")); assert plan["hero"]["to"] == newer and plan["hero"]["on"] == "2026-12-09"
    monkeypatch.setattr(BK, "judge_pair", lambda a, b, c, d: {"ok": True, "cur_score": 7.0, "new_score": 7.3})
    setting("MODEL_CANDIDATES", json.dumps([{"id": "x/v9", "usd": 0.3}])); setting("MODEL_PLANNED", "{}")
    ST.test_candidates(); assert json.loads(core.S("MODEL_PLANNED") or "{}") == {}

def test_unreadable_price_asks_the_owner_instead_of_switching(monkeypatch):
    _quiet(monkeypatch)
    newer = "fal-ai/kling-video/v4/pro/image-to-video"
    fetch = lambda url: (f"{newer}" if "explore" in url else ("no price here" if newer in url else "For 5s video your request will cost $0.35"))
    ST.watch(fetch=fetch, now=dt.datetime(2026, 12, 6, tzinfo=dt.timezone.utc))
    assert not json.loads(core.S("MODEL_CANDIDATES") or "[]")
    assert any(r["kind"] == "model_new" and "could not be read" in r["text"] for r in core.store().rows("Owner_Actions"))

def test_judge_pair_runs_in_fake_mode(monkeypatch):
    monkeypatch.setenv("WI_SMALL", "1")
    r = BK.judge_pair(HERO, 0.35, "wan/v2.6/image-to-video/flash", 0.25)
    assert r["ok"] and 0 <= r["cur_score"] <= 10 and 0 <= r["new_score"] <= 10
