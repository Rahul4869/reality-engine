"""v11 Stage A: the owner's month cap, the carried-in breakout fund, the 90% guard, the watchdog clock wiring. No keys, no network."""
import datetime as dt
import pytest
from whatifs import core, governor as G, manage as MG, notify as NT, publish as PUB

def _spend(inr, role="writer", item="script", ts=None):
    core.store().append("Cost_Log", [{"ts": ts or core.iso(), "role": role, "item": item, "inr": inr, "basis": "logged", "provider": "fal"}])
    core._base["v"] = None                                     # month spend is cached per process; the real cost() path updates it as it goes

def test_owner_month_override_sets_the_cap_and_only_that_month(setting):
    base = G.cap_inr()
    mk = core.now_utc().strftime("%Y-%m")
    setting("MONTH_CAP_OVERRIDES", f"{mk}=5226,2099-01=1"); assert G.cap_inr() == pytest.approx(5226)
    setting("MONTH_CAP_OVERRIDES", "2099-01=1"); assert G.cap_inr() == pytest.approx(base)

def test_v11_upgrade_writes_november_once(setting):
    setting("V11_FLIPS_DONE", ""); setting("MONTH_CAP_OVERRIDES", "")
    nov = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)
    assert MG.v11_upgrade(core.store(), nov) == ["MONTH_CAP_OVERRIDES"] and core.S("MONTH_CAP_OVERRIDES") == "2026-11=5226"
    assert MG.v11_upgrade(core.store(), nov) == []

def test_breakout_fund_rolls_over_capped_and_is_breakout_only(setting, monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    setting("LAST_MONTH_CAP_INR", "5226"); setting("LAST_MONTH_SPEND_INR", "3800"); setting("BREAKOUT_FUND_MONTH", "")
    assert G.rollover_month() == 1000 and G.rollover_month() is None                      # capped at Rs 1,000; once per month
    room_with_fund = G.cap_inr()
    setting("BREAKOUT_FUND_ON", "FALSE"); assert G.cap_inr() == pytest.approx(room_with_fund - 1000)
    setting("BREAKOUT_FUND_ON", "TRUE")
    assert G.extras_allowed(400, kind="breakout") == (True, "breakout fund")
    p0 = G.production_room_inr(); _spend(300, role="breakout", item="followup short"); assert G.breakout_fund_left_inr() == pytest.approx(700)
    assert G.production_room_inr() == pytest.approx(p0)                                 # the fund's spend never eats production money

def test_guard_pauses_extras_at_90_percent_with_one_alert(setting, monkeypatch):
    sent = []
    monkeypatch.setattr(NT, "send", lambda *a, **k: sent.append(a[0]) or "id")
    cap = G.cap_inr(); _spend(cap * 0.9)
    ok, why = G.extras_allowed(10, kind="spinoff")
    assert not ok and "guard" in why and sent == ["budget_guard"]
    G.extras_allowed(10, kind="spinoff"); assert sent == ["budget_guard"]                 # one alert per month

def test_pipeline_accepts_the_watchdog_tick_and_queues_duplicates():
    y = open(".github/workflows/pipeline.yml", encoding="utf-8").read()
    assert "repository_dispatch:" in y and "types: [tick]" in y and "group: tick" in y
    w = open("mission_control/worker.js", encoding="utf-8").read()
    assert "async scheduled(" in w and "export async function watchdog" in w

def test_breakout_follow_up_costs_are_counted_by_episode_id(setting):
    setting("BREAKOUT_FUND_INR", "800"); setting("BREAKOUT_FUND_MONTH", core.now_utc().strftime("%Y-%m"))
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "BRK202611200101", "item": "clip_kling", "provider": "fal", "inr": 39}])
    assert G.breakout_fund_left_inr() == pytest.approx(761)


def test_no_setting_or_tab_is_defined_twice():
    """A duplicate key in a dict literal silently replaces the first one (v11 found Technique_Library defined twice). Never again."""
    import ast
    src = open("whatifs/core.py", encoding="utf-8").read(); tree = ast.parse(src)
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict) and any(isinstance(t, ast.Name) and t.id in ("TABS", "DEFAULTS") for t in node.targets):
            name = [t.id for t in node.targets if isinstance(t, ast.Name)][0]
            keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
            dup = sorted({k for k in keys if keys.count(k) > 1})
            found[name] = dup
    assert set(found) == {"TABS", "DEFAULTS"}, found
    assert found["TABS"] == [] and found["DEFAULTS"] == [], found

def test_v11_upgrade_moves_the_hero_model_to_the_verified_kling_endpoint(setting):
    bad, good = "fal-ai/kling-video/v3/standard/image-to-video", "fal-ai/kling-video/o3/standard/image-to-video"
    st = core.store(); setting("V11_FLIPS_DONE", ""); setting("FAL_HERO_MODEL", bad)
    setting("MODEL_LADDERS", '{"hero": [{"id": "%s", "usd": 0.42}]}' % bad)
    done = MG.v11_upgrade(st)
    assert "FAL_HERO_MODEL" in done and core.S("FAL_HERO_MODEL") == good and bad not in core.S("MODEL_LADDERS")
    from whatifs import media as MD
    a = MD.video_args(good, "http://x/i.png", "p", hero=True)
    assert a["image_url"] == "http://x/i.png" and a["generate_audio"] is False and "start_image_url" not in a

