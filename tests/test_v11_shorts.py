"""The standalone Shorts track: when one is due, the money rules, the breakout follow-ups, the review of the first ones. No keys, no network.
(What a Short IS - its format, the viewer's seat, the short gate - is tested in tests/test_v12_short.py.)"""
import datetime as dt, json, subprocess
import pytest
from whatifs import core, shorts2 as SH, specials as SP, notify as NT, publish as PUB, formats as FMT

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _bench(*premises):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "premise": p, "status": "READY", "combined": 9 - i} for i, p in enumerate(premises)])

def test_a_short_is_made_tagged_forecast_and_waits_for_review_at_first(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if the Moon left tonight?")
    r = SH.run(force=True)
    assert r["ok"] and r["kind"] == "short" and r["status"] == "AWAITING_APPROVAL" and r["file"].startswith("drive:")
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", r["path"]], capture_output=True, text=True).stdout)
    assert {"video", "audio"} <= {s["codec_type"] for s in o["streams"]} and 20 <= float(o["format"]["duration"]) <= 45
    st = core.store()
    f = next(x for x in st.rows("Video_Features") if x["video_key"] == r["id"])
    assert f["format"] == "short" and f["hook"] in FMT.SHORT_HOOKS and f["topic"] == "space" and f["lead"] in FMT.SHORTS          # lead = the Short's format: nobody is on screen
    assert any(x["video_key"] == r["id"] for x in st.rows("Forecasts"))
    assert st.rows("Specials")[-1]["file"].startswith("drive:")                     # the Drive id survives into the Sheet (approval needs it)
    assert {x["stage"] for x in st.rows("Jury_Log")} == {"short"}

def test_breakout_follow_ups_come_first_are_charged_to_the_fund_and_differ(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if gravity doubled?")
    st = core.store()
    st.append("Episodes", [{"episode_id": "E7", "premise": "What if the Sun went out?", "title": "The Sun On Trial"}])
    st.append("Breakout_Queue", [{"ts": core.iso(), "video_key": "E7", "status": "APPROVED", "left": 2}])
    seen = []
    import whatifs.media as MD
    real = MD.animate
    monkeypatch.setattr(MD, "animate", lambda *a, **k: (seen.append(k.get("hero")), real(*a, **k))[1])
    now = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc)
    r = SH.run(force=True, now=now)
    assert r["ok"] and r["premise"] == "What if the Sun went out?" and seen and all(seen)          # every clip of a Short is made by the hero model
    assert st.rows("Breakout_Queue")[-1]["status"] == "APPROVED" and int(float(st.rows("Breakout_Queue")[-1]["left"])) == 1 and r["id"].startswith("BRK")   # one more to go; charged to the breakout fund
    r2 = SH.run(force=True, now=now + dt.timedelta(minutes=1)); assert r2["ok"] and r2["premise"] == "What if the Sun went out?", r2
    assert st.rows("Breakout_Queue")[-1]["status"] == "DONE"
    a, b = st.rows("Specials")[-2:]; assert (a["format"], a["hook"]) != (b["format"], b["hook"]) and FMT.likeness(a["script"], b["script"]) < 0.4      # two follow-ups on one topic are two different Shorts

def test_daily_target_and_budget_rules(monkeypatch, setting):
    setting("SHORTS_PER_DAY", "1.5")
    even = dt.datetime(2026, 12, 2, 6, 0, tzinfo=dt.timezone.utc); odd = even + dt.timedelta(days=1)
    assert {SH.target_today(even), SH.target_today(odd)} == {1, 2}
    from whatifs import governor as G
    monkeypatch.setattr(G, "extras_allowed", lambda est, kind="extra": (False, "guard"))
    assert SH._budget_ok(30, first_today=False) == (False, "guard")                  # extra Shorts obey the guard
    assert SH._budget_ok(30, first_today=True)[0] is True                              # the first Short of a day is core

def test_the_estimate_counts_every_paid_clip_and_a_refusal_makes_nothing(monkeypatch, setting):
    fx = core.S("USD_INR", float); clip = core.S("PRICE_KLING_USD", float) * fx
    for fmt in FMT.SHORTS: assert SH.est_inr(fmt) >= 3 * clip + core.S("REPLAN_SHORT_INR", float), fmt          # at least three hero clips, the writing and the voice
    assert SH.est_inr("S2") >= SH.est_inr("S1")                                        # the longer band never costs less
    _quiet(monkeypatch); _bench("What if the Moon left tonight?")
    monkeypatch.setattr(SH, "_budget_ok", lambda est, first: (False, f"no room for Rs {est:.0f}"))
    r = SH.run(force=True); assert r == {"ok": False, "skipped": "budget", "why": r["why"]} and "no room for Rs" in r["why"]
    assert not core.store().rows("Specials") and not core.store().rows("Sessions")          # nothing was written, voiced or paid

def test_specials_rows_keep_every_field_they_write():
    cols = set(core.TABS["Specials"])
    assert {"file", "premise", "id", "kind", "yt_id", "status", "format", "hook", "script", "sec"} <= cols

def test_a_held_short_does_not_count_as_one_of_the_first_reviewed(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if the Moon left tonight?"); setting("SHORTS_REVIEW_FIRST_N", "1")
    core.store().append("Specials", [{"ts": core.iso(), "id": "SH0", "kind": "short", "format": "S1", "status": "HELD (short_plain)", "premise": "x"}])
    r = SH.run(force=True); assert r["ok"] and r["status"] == "AWAITING_APPROVAL"       # the first Short that was really made still waits for the owner
