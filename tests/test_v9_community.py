"""v9 stage 3b: packaging pairs (pick, timeout, rotation), community (jury comment, tally, teacup finders, queue), Season, Experiments, variety guard."""
import json, datetime as dt
import pytest
from whatifs import core, packaging as PK, community as CM, manage as MG, publish as PUB, show as SHOW

PKG = {"title": "What If Every Pillow Floated Away?", "thumb_text": "NOON", "title_b": "The Day Every Pillow Left Planet Earth", "thumb_text_b": "GONE",
       "titles": ["Your Pillows Just Broke The Law Of Gravity", "Why Your Pillow Is Rising Toward Space"], "thumb_text_c": "UP"}

def test_three_coherent_pairs_and_never_the_source_title():
    vs = PK.variants(PKG, {})
    assert [v["key"] for v in vs] == ["A", "B", "C"] and all(PK.coherent(v["title"], v["thumb_text"]) for v in vs)
    vs2 = PK.variants(PKG, {"show_plan": {"demand_evidence": {"title": "The Day Every Pillow Left Planet Earth"}}})
    assert "The Day Every Pillow Left Planet Earth" not in [v["title"] for v in vs2]
    assert not PK.coherent("Pillows rise", "PILLOWS RISE NOW")

def test_hook_shapes_rotate_and_statistic_needs_source():
    b = PK.hook_shape_brief(["statistic", "clock"])
    assert "The Statistic" not in b and "The Clock" not in b and "Contrarian Flip" in b and "source" in b

def _ep(st, slot):
    st.append("Episodes", [{"episode_id": "EP20261101", "yt_id": "vid1", "slot_et": slot, "status": "LIVE"}])

def test_pick_inside_window_applies_and_late_pick_is_ignored(monkeypatch, setting):
    setting("TITLE_SHOCK_ON", "FALSE")          # v9.2 reorders variants by shock score (test_v92_titles_setup); keep the v9 order here
    MG.setup(); calls = []
    monkeypatch.setattr(PUB, "yt_set_title", lambda vid, t: calls.append(t)); monkeypatch.setattr(PUB, "email", lambda *a, **k: calls.append("mail"))
    PK.record("EP20261101", "vid1", PK.variants(PKG, {}), {})
    assert "mail" in calls and "applied" in PK.apply_pick("PICK EP20261101 B") and "The Day Every Pillow Left Planet Earth" in calls
    rows = {r["variant"]: r for r in core.store().rows("Packaging_Tests")}; assert rows["B"]["status"] == "LIVE" and rows["B"]["picked_by"] == "owner"
    for r in core.store().rows("Packaging_Tests"): core.store().update_where("Packaging_Tests", {"variant": r["variant"]}, {"created": "2020-01-01T00:00:00Z"})
    assert "too late" in PK.apply_pick("PICK EP20261101 C")
    with pytest.raises(SystemExit): PK.apply_pick("PICK nonsense")

def test_rotation_windows_then_a_winner_and_bounded(monkeypatch, setting):
    setting("TITLE_SHOCK_ON", "FALSE")          # v9.2 reorders variants by shock score; keep the v9 order here
    MG.setup(); st = core.store(); calls = []; views = {"n": 0}
    monkeypatch.setattr(PUB, "yt_set_title", lambda vid, t: calls.append(t)); monkeypatch.setattr(PUB, "yt_views", lambda vid: views["n"])
    monkeypatch.setattr(PUB, "email", lambda *a, **k: None)
    rel = core.now_utc() - dt.timedelta(hours=1); _ep(st, rel.strftime("%Y-%m-%dT%H:%M:%SZ"))
    PK.record("EP20261101", "vid1", PK.variants(PKG, {}), {})
    assert PK.rotate_tick() == 1 and PK.rotate_tick() == 0                               # window A opened once, no repeated switch
    st.update("Episodes", "episode_id", "EP20261101", {"slot_et": (core.now_utc() - dt.timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")}); views["n"] = 900
    assert PK.rotate_tick() == 1 and calls[-1] == PKG["title_b"]
    st.update("Episodes", "episode_id", "EP20261101", {"slot_et": (core.now_utc() - dt.timedelta(hours=60)).strftime("%Y-%m-%dT%H:%M:%SZ")}); views["n"] = 1000
    PK.rotate_tick(); assert any(r["status"] == "WINNER" for r in st.rows("Packaging_Tests"))
    n = len(calls); PK.rotate_tick(); assert len(calls) == n                              # finished: nothing more

def test_triage_tally_and_injection_is_just_data():
    cs = CM.fetch_comments("v")
    kinds = {c["id"]: CM.triage(c["text"]) for c in cs}
    assert kinds["c4"] == "spam_risk" and kinds["c5"] == "spam_risk" and kinds["c1"] == "prediction" and kinds["c3"] in ("prediction", "question")
    t = CM.tally(cs); assert t["guilty"] == 1 and t["not_guilty"] == 1 and t["B"] == 1

def test_teacup_finders_filtered_and_capped(setting):
    cs = [{"author": "Ana", "text": "teacup at 0:42!", "published": "1"}, {"author": "http://spam", "text": "teacup 0:42", "published": "2"},
          {"author": "Bo", "text": "teacup 0:58", "published": "3"}, {"author": "Cy", "text": "0:42 teacup", "published": "4"}]
    assert CM.teacup_finders(cs, [{"t": 41.0}]) == ["Ana", "Cy"]
    setting("TEACUP_FINDERS_MAX", "1"); assert CM.teacup_finders(cs, [{"t": 41.0}]) == ["Ana"]

def test_comment_queue_modes_and_daily_cap(monkeypatch, setting):
    MG.setup(); sent = []
    monkeypatch.setattr(PUB, "yt_reply", lambda cid, t: (sent.append(cid), True)[1])
    CM.process_comments({"episode_id": "E1", "yt_id": "v"}, {}); assert not sent              # draft mode posts nothing
    q = core.store().rows("Comment_Queue"); assert any(r["draft"] for r in q) and all(r["text"] == "[hidden]" for r in q if r["kind"] == "spam_risk")
    assert CM.process_comments({"episode_id": "E1", "yt_id": "v"}, {}) is not None and len(core.store().rows("Comment_Queue")) == len(q)   # no duplicates
    setting("COMMENT_REPLY_MODE", "auto"); setting("COMMENT_REPLY_DAILY_CAP", "1")
    CM.process_comments({"episode_id": "E2", "yt_id": "v2"}, {}); assert sent == []           # same comment ids already queued
    core.store().append("Comment_Queue", [])                                                  # (ids differ per video in real use)

def test_jury_comment_once_and_the_last_case_reaches_the_writer(monkeypatch):
    MG.setup(); posted = []
    monkeypatch.setattr(PUB, "yt_comment", lambda vid, t: (posted.append(t), True)[1]); monkeypatch.setattr(PUB, "email", lambda *a, **k: None)
    plan = {"jury_prompts": [{"kind": "guilty", "text": "Guilty or not?"}], "verdict": {"winner": "vale"}, "meter_swings": [], "charge": "c", "stinger": "s"}
    assert CM.post_jury_comment({"episode_id": "E1", "yt_id": "v"}, plan) and not CM.post_jury_comment({"episode_id": "E1", "yt_id": "v"}, plan) and len(posted) == 1
    CM.season_row("E1", plan); core.store().update_where("Season", {"episode_id": "E1"}, {"jury_tally": '{"guilty": 3}', "teacup_finders": "Ana"})
    assert "LAST CASE" in SHOW.last_case_text() and "Ana" in SHOW.last_case_text()

def test_experiments_hypothesis_results_and_region_note(monkeypatch, setting):
    MG.setup(); mails = []; monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: mails.append(subj))
    assert CM.experiment_row("E1", {"hook_shape": "clock"}, {"premise_source": "outlier", "show_plan": {"intensity": 2}})
    rel = core.now_utc() - dt.timedelta(days=8)
    assert CM.experiment_results("E1", "v", rel, {"views": 1000, "ctr": 0.06, "comments": 12, "countries": {"IN": 0.8, "US": 0.2}}) == "7d"
    r = core.store().rows("Experiments")[0]; assert r["ctr_7d"] == "0.06" and r["comments_per_1k_7d"] == "12.0" and mails
    assert CM.experiment_results("E1", "v", core.now_utc(), {}) is None
    setting("EXPERIMENT_EPISODES", "1"); assert not CM.experiment_row("E2", {}, {})

def test_variety_guard_flags_repeats_without_a_call():
    hist = [{"verdict_winner": "vale", "plan_json": json.dumps({"charge": "Every pillow stands accused of breaking gravity", "exhibits": [{"kind": "RECON"}] * 3})}] * 2
    plan = {"verdict": {"winner": "vale"}, "charge": "Every pillow stands accused of breaking gravity at noon", "exhibits": [{"kind": "RECON"}] * 3}
    iss = CM.variety_issues(plan, hist); assert len(iss) == 3
    assert CM.variety_issues(dict(plan, verdict={"winner": "grimm"}, charge="The ocean is charged with standing still", exhibits=[{"kind": "DATA"}]), hist) == []

def test_clipbait_lines_and_audio_drop(tmp_path):
    import subprocess
    from whatifs import showfx as SFX
    sc = "[DIRECTOR] intro\n[CLIPBAIT] [SKEPTIC] Pillows do not fly!\n[DIRECTOR] Observe. [/CLIPBAIT]\n[JUDGE] Mm."
    assert SHOW.clipbait_lines(sc) == ["[SKEPTIC] Pillows do not fly!", "[DIRECTOR] Observe."] and SHOW.clipbait_lines("none") == []
    m = str(tmp_path / "m.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=220:d=20", "-f", "lavfi", "-i", "color=c=gray:s=64x36:d=20", "-shortest", m], check=True)
    us = [{"start": 10.0, "end": 12.0, "show": ["[CLIPBAIT]"]}, {"start": 12.0, "end": 16.0, "show": ["[/CLIPBAIT]"]}]
    p = SFX.audio_drop(m, us, str(tmp_path), "EPA"); assert p and p.endswith(".m4a")
    assert SFX.audio_drop(m, [{"start": 1.0, "end": 2.0, "show": ["[CLIPBAIT]"]}, {"start": 2.0, "end": 15.0, "show": ["[/CLIPBAIT]"]}], str(tmp_path), "EPB") is None
