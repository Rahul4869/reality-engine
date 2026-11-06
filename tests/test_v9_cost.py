"""v9 stage 3a: cost controls (estimator, spend monitor, AI-side overrun ladder, weekly deviation), the made-for-kids guard and demand-first topics."""
import json
import pytest
from whatifs import core, costguard as CG, craft as CR, premise as PR, manage as MG, governor as G, publish as PUB, models as M

def _mails(monkeypatch):
    out = []; monkeypatch.setattr(PUB, "email", lambda subj, body, *a, **k: out.append(subj)); return out

def test_estimator_lines_add_up_and_never_include_a_cut():
    L = CG.estimate_lines()
    assert L["visuals"] > 100 and L["show_devices"] == 0 and abs(sum(L.values()) - G.full_episode_inr() - L["community"]) < 1.0

def test_spend_monitor_mails_each_threshold_once_a_month(monkeypatch):
    MG.setup(); mails = _mails(monkeypatch)
    monkeypatch.setattr(CG, "month_spend", lambda: 2900.0); assert CG.spend_monitor() == [70] and CG.spend_monitor() == []
    monkeypatch.setattr(CG, "month_spend", lambda: 3700.0); assert CG.spend_monitor() == [90] and len(mails) == 2

def test_overrun_ladder_is_ai_side_only_rises_and_mails_once(monkeypatch, setting):
    MG.setup(); mails = _mails(monkeypatch); est = M.ai_estimate_inr(); CG._LADDER.clear()
    monkeypatch.setattr(CG, "ai_measured", lambda ep: est * 1.2); assert CG.ladder_level("EPL") == 0
    monkeypatch.setattr(CG, "ai_measured", lambda ep: est * 1.6); assert CG.ladder_level("EPL") == 1
    monkeypatch.setattr(CG, "ai_measured", lambda ep: est * 2.1); assert CG.ladder_level("EPL") == 3
    monkeypatch.setattr(CG, "ai_measured", lambda ep: 0.0); assert CG.ladder_level("EPL") == 3            # never falls back within an episode
    assert CG.ladder_mail("EPL") and len(mails) == 1 and not CG.ladder_mail("EPOTHER")
    setting("OVERRUN_LADDER_ON", "FALSE"); assert CG.ladder_level("EPX") == 0

def test_ladder_limits_owners_cut_rounds_never_pictures(monkeypatch):
    seq = iter([5.0] * 9); n = []
    monkeypatch.setattr(CR, "judge", lambda *a: (lambda m: {"scores": {k: m for k in CR.OC_KEYS}, "mean": m, "passed": False, "fixes": ["x"]})(next(seq)))
    monkeypatch.setattr(CG, "ladder_level", lambda ep: 2)
    out, rec = CR.owners_cut({"premise": "p"}, {"script": "v0"}, "", {}, "EPO", lambda sc, fx: (n.append(1), {"script": "v1"})[1])
    assert len(rec["rounds"]) == 2 and len(n) == 1
    assert G.plan_for_episode(400.0, 8)["tier"] == "full"                                  # the ladder has no handle on tiers or Kling

def test_weekly_deviation_lists_only_big_gaps(monkeypatch):
    MG.setup(); mails = _mails(monkeypatch)
    core.cost("claude_opus", "anthropic", 1, 10.0, "EPD"); core.flush_costs()
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "EPD", "item": "ai_per_video_summary", "provider": "summary", "units": 0, "inr": 0, "basis": "summary"}])
    dev = dict((s, p) for s, m, e, p in CG.deviation_report())
    assert dev["ai_writing"] > 15 and CG.weekly_deviation_mail() and not CG.weekly_deviation_mail() and len(mails) == 1

def test_kids_guard_mails_only_when_youtube_says_true(monkeypatch, setting):
    mails = _mails(monkeypatch)
    assert CG.kids_check("vid1", "E") is False and not mails
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: {"madeForKids": True})
    assert CG.kids_check("vid1", "E") is True and mails and "made for kids" in mails[0]
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: (_ for _ in ()).throw(RuntimeError("403")))
    assert CG.kids_check("vid1", "E") is None
    setting("KIDS_GUARD_ON", "FALSE"); assert CG.kids_check("vid1", "E") is None

def test_outlier_ranking_files_demand_and_bench_keeps_new_execution(monkeypatch):
    MG.setup()
    vids = CR.outlier_rank([{"video_id": "a", "title": "t1", "channel": "c", "views": "1200000", "channel_id": "UCfake"},
                            {"video_id": "b", "title": "t2", "channel": "d", "views": "100000", "channel_id": "UCother"}])
    assert vids[0]["video_id"] == "a" and vids[0]["multiple"] == 4.0 and vids[1]["multiple"] == 0.25
    assert CR.file_demand(vids) == 1 and CR.file_demand(vids) == 0                          # only outliers, no duplicates
    core.store().append("Demand_Signals", [{"video_id": "fakevid0001", "title": "What If You Fell Into Jupiter?", "multiple": 8}])
    n = PR.refill_bench(force=True); rows = core.store().rows("Premise_Bench")
    assert n and {r["src"] for r in rows} <= {"outlier", "original"} and any(r["src"] == "outlier" and "fakevid0001" in r["demand_json"] for r in rows)
    assert not any("Jupiter" in r["premise"] for r in rows)

def test_source_mix_prefers_the_missing_source():
    MG.setup()
    rows = [{"src": "original", "premise": "a"}, {"src": "outlier", "premise": "b"}]
    assert PR._mix_order(rows)[0]["src"] == "outlier"                                        # 0 % outlier used so far < 60 %
    core.store().append("Premise_Bench", [{"bench_id": f"U{i}", "status": "USED", "src": "outlier"} for i in range(3)])
    assert PR._mix_order(rows)[0]["src"] == "original"
    core.store().append("Premise_Bench", [{"bench_id": f"V{i}", "status": "USED", "src": "original"} for i in range(6)])
    assert PR._mix_order(rows) == rows                                                       # after 8 episodes: score order only
