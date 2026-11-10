"""v9.1 acceptance, end to end with the fakes: (1) ALL v9.1 flags on: the episode is scheduled and no paid call appears beyond v9's, because every
v9.1 feature that runs inside an episode is code-only or reuses what was paid for; (2) EVERY v9.1 feature forced to fail inside one episode: each switches
itself off, the video is still rendered, checked and scheduled."""
import json, os
import pytest
from tests.paid_calls import count, allowed_base
from whatifs import core

ALL_ON = ["ATMOSPHERE_ON", "PULSE_ON", "LIGHTING_DIRECTIVE_ON", "HERO_STILL_REELS_ON", "CHAR_GRAMMAR_ON", "RETENTION_MAP_ON", "ROLE_ROI_ON",
          "COMMENT_MINING_ON", "COMMENT_AI_DRAFTS_ON", "VARIETY_REWRITE_ON", "AUDIO_DROP_POST_ON", "VOICE_SUBSTITUTE_ON"]

def test_all_flags_on_no_new_paid_call(monkeypatch, tmp_path):
    base = allowed_base(json.load(open(os.path.join(os.path.dirname(__file__), "golden", "v9_paid_calls.json")))["calls"])      # v10.2: documented additions only
    from whatifs import manage as MG
    real_setup = MG.setup
    def setup_all_on():
        real_setup()
        for f in ALL_ON: core.set_setting(f, "TRUE")
    monkeypatch.setattr(MG, "setup", setup_all_on)
    now, r = count(monkeypatch, tmp_path)
    print("PAID_CALLS_ALL_ON=" + json.dumps(now, sort_keys=True))
    # v9.2: Setup now fills an empty bench, so the episode draws from it and may make FEWER calls (no scout round); never a new or a larger category
    assert r.get("ok") and set(now) <= set(base) and all(now[k] <= base[k] for k in now), {k: (base.get(k), now.get(k)) for k in set(base) | set(now) if base.get(k) != now.get(k)}
    ep = core.store().rows("Episodes")[-1]
    assert ep["status"] == "SCHEDULED" and json.loads(ep.get("atmos_json") or "{}") and json.loads(ep.get("shots_json") or "[]")

def test_every_v91_feature_failing_still_schedules(monkeypatch, tmp_path):
    from whatifs import atmosphere as AT, herostill as HS, insights as INS, v91 as V91, manage as MG
    def boom(*a, **k): raise RuntimeError("injected v9.1 failure")
    monkeypatch.setattr(AT.Atmosphere, "_apply", boom)                      # fails on the first frame, inside the render
    monkeypatch.setattr(AT, "with_directive", boom)                         # every image prompt
    monkeypatch.setattr(HS, "pick_best", boom); monkeypatch.setattr(INS, "variety_score", boom); monkeypatch.setattr(INS, "roi_flush", boom)
    monkeypatch.setattr(V91, "resolve_voice", boom)
    real_setup = MG.setup
    def setup_all_on():
        real_setup()
        for f in ALL_ON: core.set_setting(f, "TRUE")
    monkeypatch.setattr(MG, "setup", setup_all_on); V91._OFF.clear()
    now, r = count(monkeypatch, tmp_path)
    ep = core.store().rows("Episodes")[-1]
    assert r.get("ok") and ep["status"] == "SCHEDULED", (r, ep.get("notes"))
    V91._OFF.clear()
