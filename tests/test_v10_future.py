"""v10-future WP13 (K140): Policy Rescue, expiry calendar, weekly backup, Advisor, dashboard health. No keys, no network."""
import datetime as dt, os, zipfile
import pytest
from whatifs import core, caretaker as CT, notify as NT, publish as PUB, manage as MG

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def test_policy_rescue_card_and_answers(monkeypatch, setting):
    _quiet(monkeypatch)
    MG.guardian([{"change": "AI narration channels lose monetisation", "source": "https://support.google.com/youtube/x"}])
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "policy")
    assert row["tier"] == "now" and row["urgent"] == "TRUE" and core.S("PAUSED_UNTIL")
    import whatifs.builds as BD; calls = []
    monkeypatch.setattr(BD, "request_build", lambda spec, kind="tweak": calls.append(kind) or True)
    assert NT.answer(row["id"], "BUILDFIX policy") == "fix build started" and calls == ["feature"]

def test_resume_from_the_policy_card(monkeypatch, setting):
    _quiet(monkeypatch); a = CT.policy_rescue([{"change": "x"}]); setting("PAUSED_UNTIL", "2099-01-01T00:00:00Z")
    assert NT.answer(a, "RESUME") == "resumed" and not core.S("PAUSED_UNTIL")

def test_expiry_reminders_14_then_3_days_once_each(monkeypatch):
    _quiet(monkeypatch); CT.ensure_expiry_seed(); CT.ensure_expiry_seed()
    assert len([r for r in core.store().rows("Expiry_Calendar") if r["item"].startswith("Claude Max")]) == 1
    assert CT.expiry_check(dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc)) == []
    assert CT.expiry_check(dt.datetime(2026, 11, 27, tzinfo=dt.timezone.utc)) == ["Claude Max plan (back to Pro):14"]
    assert CT.expiry_check(dt.datetime(2026, 11, 28, tzinfo=dt.timezone.utc)) == []
    assert CT.expiry_check(dt.datetime(2026, 12, 8, tzinfo=dt.timezone.utc)) == ["Claude Max plan (back to Pro):3"]
    urgent = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "expiry" and r["tier"] == "now"]; assert len(urgent) == 1

def test_weekly_backup_zip_excludes_the_private_chat_and_keeps_8(tmp_path, monkeypatch, setting):
    monkeypatch.setenv("WI_WORK", str(tmp_path))
    core.store().append("WA_Chat", [{"ts": "t", "msg_id": "m", "who": "owner", "text": "private"}])
    name = CT.backup(dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc))
    z = zipfile.ZipFile(os.path.join(str(tmp_path), name)); assert "Settings.csv" in z.namelist() and "WA_Chat.csv" not in z.namelist()
    assert CT.backup(dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc)) == ""                       # once a week
    for w in range(1, 10): CT.backup(dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc) + dt.timedelta(weeks=w))
    rows = core.store().rows("Backups"); assert len([r for r in rows if r["file"] != "deleted"]) == 8

def test_advisor_weekly_card_mentions_money_and_once(monkeypatch):
    _quiet(monkeypatch)
    a = CT.advisor(); assert CT.advisor() == a
    row = next(r for r in core.store().rows("Owner_Actions") if r["id"] == a); assert "spend Rs" in row["text"] and row["tier"] == "week"

def test_dashboard_health_has_expiry_and_runs():
    from whatifs import dash as DS
    CT.ensure_expiry_seed(); core.store().append("Run_Log", [{"ts": core.iso(), "job": "tick", "level": "INFO", "message": "x"}])
    h = DS.build_snapshot()["health"]; assert any(x["name"].startswith("Claude Max") for x in h["expiring"]) and any(x["workflow"] == "tick" for x in h["last_runs"])

# ---------------- pilots (K141), Outlier Lab (K142), bake-off (K143)
from whatifs import pilots as PL, outlier_lab as OL, bakeoff as BK

def _bench(n=2):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "added": core.iso(), "status": "READY", "premise": f"What if your bed floated {i}", "headline": f"Bed {i}", "combined": str(8 - i)} for i in range(n)])

def test_pilot_short_made_from_the_best_unpiloted_premise(monkeypatch):
    monkeypatch.setenv("WI_SMALL", "1"); _bench()
    r = PL.run(publish=False); assert r["ok"] and r["bench_id"] == "B0" and os.path.exists(r["path"])
    assert PL.run(publish=False)["bench_id"] == "B1" and PL.run(publish=False)["ok"] is False      # each premise piloted once

def test_pilot_money_and_switch(setting):
    _bench(); core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "PL202611010000", "item": "image", "inr": "45"}])
    assert "pilot money" in PL.run(publish=False)["why"]
    setting("PILOTS_ON", "FALSE"); assert PL.run(publish=False)["ok"] is False

def test_pilot_bonus_moves_the_bench_score(monkeypatch):
    _bench(1); old = (core.now_utc() - dt.timedelta(hours=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Pilots", [{"ts": old, "id": f"PLx{i}", "bench_id": "B0" if i == 3 else f"Z{i}", "yt_id": f"y{i}", "views": "" if i == 3 else str(100), "bonus": ""} for i in range(4)])
    monkeypatch.setattr(PUB, "yt_engaged_views", lambda vid, since: 300)
    assert PL.measure() == 1
    b = next(r for r in core.store().rows("Premise_Bench") if r["bench_id"] == "B0"); assert float(b["combined"]) == pytest.approx(9.0)

def test_outlier_lab_watches_and_files_a_judged_card(monkeypatch, setting):
    setting("ORCHESTRA_RELEASE_GUARD_H", "0")
    done = OL.run(); assert done == ["FAKEvid1"] and OL.run() == []                                  # seen once
    row = core.store().rows("Outlier_Lab")[-1]; assert row["status"] and row["status"] != "no answer"
    assert any(r.get("video_id") == "FAKEvid1" for r in core.store().rows("Technique_Library"))

def test_bakeoff_once_with_a_choice_card_and_safe_default(monkeypatch, setting):
    _quiet(monkeypatch); monkeypatch.setenv("WI_SMALL", "1")
    r = BK.run(); assert r["ok"] and r["models"] == 3 and BK.run()["ok"] is False
    row = next(x for x in core.store().rows("Owner_Actions") if x["kind"] == "bakeoff")
    assert "Keep current" in row["buttons"] and row["default_action"] == "keep the current model"
    assert NT.answer(row["id"], "BAKE 1") == "hero model set to fal-ai/kling-video/v2.6/pro/image-to-video" and core.S("PRICE_KLING_USD", float) == 0.35
    import whatifs.bakeoff as BKM
    assert "wan/v2.6/image-to-video/flash" in [m for m, _ in BKM._models()]                  # v10.1 candidates (verified 8 Nov 2026)
    setting("BAKEOFF_CAP_INR", "10"); assert "above" in BK.run(force=True)["why"]
