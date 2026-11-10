"""v11 Stage D (K159): standalone daily Shorts. No keys, no network."""
import datetime as dt, json, subprocess
import pytest
from whatifs import core, shorts2 as SH, specials as SP, notify as NT, publish as PUB

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _bench(*premises):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "premise": p, "status": "READY", "combined": 9 - i} for i, p in enumerate(premises)])

def test_a_short_is_made_tagged_forecast_and_waits_for_review_at_first(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if the Moon left tonight?")
    r = SH.run(force=True)
    assert r["ok"] and r["kind"] == "short" and r["status"] == "AWAITING_APPROVAL" and r["file"].startswith("drive:")
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", r["path"]], capture_output=True, text=True).stdout)
    assert {"video", "audio"} <= {s["codec_type"] for s in o["streams"]} and 8 < float(o["format"]["duration"]) < 60
    st = core.store()
    f = next(x for x in st.rows("Video_Features") if x["video_key"] == r["id"])
    assert f["format"] == "short" and f["hook"] in __import__("whatifs.brain", fromlist=["x"]).HOOK_ARCHETYPES and f["topic"] == "space"
    assert any(x["video_key"] == r["id"] for x in st.rows("Forecasts"))
    assert st.rows("Specials")[-1]["file"].startswith("drive:")                     # the Drive id survives into the Sheet (approval needs it)
    assert {x["stage"] for x in st.rows("Jury_Log")} == {"short"}

def test_breakout_follow_ups_come_first_and_always_get_kling(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if gravity doubled?")
    st = core.store()
    st.append("Episodes", [{"episode_id": "E7", "premise": "What if the Sun went out?", "title": "The Sun On Trial"}])
    st.append("Breakout_Queue", [{"ts": core.iso(), "video_key": "E7", "status": "APPROVED", "left": 2}])
    seen = []
    import whatifs.media as MD
    real = MD.animate
    monkeypatch.setattr(MD, "animate", lambda *a, **k: (seen.append(k.get("hero")), real(*a, **k))[1])
    r = SH.run(force=True)
    assert r["ok"] and r["premise"] == "What if the Sun went out?" and seen[0] is True and not any(seen[1:])
    assert st.rows("Breakout_Queue")[-1]["status"] == "APPROVED" and int(float(st.rows("Breakout_Queue")[-1]["left"])) == 1 and r["id"].startswith("BRK")   # one more to go; charged to the breakout fund
    r2 = SH.run(force=True); assert r2["ok"] and r2["premise"] == "What if the Sun went out?"
    assert st.rows("Breakout_Queue")[-1]["status"] == "DONE"

def test_the_script_checks_reject_bad_shorts():
    good = json.loads(__import__("whatifs.fakes", fromlist=["x"]).fake_reply("short_script", ""))
    assert SH._valid(good) == []
    bad = dict(good, beats=good["beats"][:2], loop_line="")
    assert set(SH._valid(bad)) >= {"2 beats", "no loop line"}

def test_daily_target_and_budget_rules(monkeypatch, setting):
    setting("SHORTS_PER_DAY", "1.5")
    even = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc); odd = even + dt.timedelta(days=1)
    assert {SH.target_today(even), SH.target_today(odd)} == {1, 2}
    from whatifs import governor as G
    monkeypatch.setattr(G, "extras_allowed", lambda est, kind="extra": (False, "guard"))
    assert SH._budget_ok(30, first_today=False) == (False, "guard")                  # extra Shorts obey the guard
    assert SH._budget_ok(30, first_today=True)[0] is True                              # the first Short of a day is core

def test_specials_rows_keep_every_field_they_write():
    cols = set(core.TABS["Specials"])
    assert {"file", "premise", "id", "kind", "yt_id", "status"} <= cols

def test_shorts_wait_for_locked_masters(setting, monkeypatch):
    from whatifs.notify import IST
    import datetime as dt
    now = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc)          # 11:30 IST
    setting("SHORTS_NEED_MASTERS", "TRUE"); setting("PAUSED", "FALSE")
    monkeypatch.setattr(SH, "masters_ready", lambda: False); assert SH.due(now) is False
    monkeypatch.setattr(SH, "masters_ready", lambda: True); assert SH.due(now) is True

