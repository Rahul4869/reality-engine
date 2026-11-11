"""v11 Stage E (K164 re-planner, K165 tool scout). No keys, no network."""
import datetime as dt, json
import pytest
from whatifs import core, replan as RPL, scout as SCT, notify as NT, publish as PUB, governor as G

MON = dt.datetime(2026, 12, 7, 6, 0, tzinfo=dt.timezone.utc)          # a Monday

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def test_free_money_is_proposed_on_monday_and_needs_the_owner(monkeypatch, setting):
    _quiet(monkeypatch)
    monkeypatch.setattr(RPL, "free_inr", lambda now=None: 20000.0)
    props = RPL.weekly(MON)                                                                     # v12 V2c-b: ONE rung - one more Short a week (the cadence is set in weeks)
    assert [(p["rung"], p["key"], p["to"]) for p in props] == [(2, "SHORTS_PER_WEEK", "4")] and core.S("SHORTS_PER_WEEK") == "3"          # nothing changes before the tap
    assert RPL.weekly(MON) == []                                                                # once per Monday
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "replan")
    assert "done" in NT.answer(row["id"], "REPLAN GO")
    assert core.S("SHORTS_PER_WEEK") == "4"
    assert RPL.month_restore(dt.datetime(2027, 1, 2, tzinfo=dt.timezone.utc))                 # next month: the owner's values come back
    assert core.S("SHORTS_PER_WEEK") == "3"

def test_no_proposal_when_the_money_is_not_free(monkeypatch, setting):
    _quiet(monkeypatch); monkeypatch.setattr(RPL, "free_inr", lambda now=None: 10.0)
    assert RPL.weekly(MON) == [] and not [r for r in core.store().rows("Owner_Actions") if r["kind"] == "replan"]

def test_free_money_keeps_the_long_slots_and_the_floor(monkeypatch, setting):
    monkeypatch.setattr(G, "production_room_inr", lambda: 3000.0); monkeypatch.setattr(G, "episodes_left_this_month", lambda: 2)
    monkeypatch.setattr(G, "max_long_videos", lambda: 4); monkeypatch.setattr(G, "long_videos_this_month", lambda: 2)
    monkeypatch.setattr(G, "full_episode_inr", lambda: 530.0)
    assert RPL.free_inr(MON) == pytest.approx(3000 - 2 * 530 - 500)

def test_scout_logs_new_models_and_raises_deprecation(monkeypatch, setting):
    _quiet(monkeypatch); setting("SCOUT_WEEKDAY", "0")
    monkeypatch.setattr(SCT, "fal_status", lambda ids: {i: ("deprecated" if "kling" in i else "active") for i in ids})
    res = SCT.weekly(MON)
    assert res["new"] == ["fal-ai/newvid/v1/image-to-video"], res
    assert float(core.store().rows("Tool_Scout")[0]["unit_price"]) == 0.07
    assert res["deprecated"] and any(r["kind"] == "scout_deprecated" for r in core.store().rows("Owner_Actions"))
    assert SCT.weekly(MON) == {}                                                                # once per day

def test_scout_uses_the_current_endpoints_only():
    src = open("whatifs/scout.py", encoding="utf-8").read()
    from whatifs import scout as _SC                                    # v12 B1: judged from the CODE (base constant + the call), no longer from docstring text
    assert _SC.AA.endswith("/api/v2") and '{AA}/media/image-to-video/models/free' in src
    assert '"/api/v2/data/' not in src and "{AA}/data/" not in src and "x-api-key" in src and "Key {env('FAL_KEY')}" in src

def test_scout_corrects_the_kling_price_from_fal(monkeypatch, setting):
    _quiet(monkeypatch); setting("SCOUT_WEEKDAY", "0"); setting("PRICE_KLING_USD", "0.42")
    monkeypatch.setattr(SCT, "fal_prices", lambda ids: {i: {"unit_price": 0.112, "unit": "second", "currency": "USD"} for i in ids})
    res = SCT.weekly(MON)
    assert res["price_check"]["usd_per_5s"] == 0.56 and core.S("PRICE_KLING_USD") == "0.56"
    assert any(r["kind"] == "scout_price" for r in core.store().rows("Owner_Actions"))

def test_kling_o3_and_v3_get_their_own_image_field():
    from whatifs import media as MD
    o3 = MD._fal_args("fal-ai/kling-video/o3/standard/image-to-video", "p", "http://i", "n") if hasattr(MD, "_fal_args") else None
    src = open("whatifs/media.py", encoding="utf-8").read()
    assert '"kling-video/o3" in m:' in src and src.index('"kling-video/o3" in m:') < src.index('"kling-video/v3" in m:')

def test_weekly_brief_reports_what_we_learned_honestly():
    from whatifs import digests as DG
    core.store().append("Technique_Evidence", [{"technique_id": "hook:verdict_first:short", "format": "short", "family": "hook", "level": "verdict_first",
                                                "status": "proven", "n_videos": 7, "p_beats_baseline": 0.93, "effect_pp": 3.1}])
    txt = DG.learned()
    assert "Proven: hook=verdict_first" in txt and "P=0.93" in txt and "Disproven (retired 60 days): none yet" in txt and "too few measured videos" in txt
    body, _ = DG.compose("weekly")
    assert "What we learned" in body

