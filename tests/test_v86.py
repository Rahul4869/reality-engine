import pytest
"""v8.6 click-through + retention layer: lessons routed to the department that uses them, code-checked titles and thumbnail text, the opening pays off the
thumbnail, per-dimension strategy scores, missing analytics never invented, diagnosis, smarter packaging rescue (dip guard + judged swaps),
strategy change log with automatic rollback, brand clear of the timestamp, the B thumbnail passes the same QC."""
import os, json, datetime as dt
import numpy as np
from PIL import Image
from whatifs import core, growth as GR, room as ROOM, episode as EP, manage as MG, art as ART, qc as QC, publish as PUB, data as DATA
from whatifs.sampler import draw as DRAW

@pytest.fixture(autouse=True)
def _v931_rescue_timing(setting):
    setting("PKG_RESCUE_HOURS", "36")          # v9.3.1 moved the default to 72 h; these tests keep the v8.5 timing


def _lesson(text, tag): core.store().append("Lessons", [{"ts": core.iso(), "lesson": text, "evidence": "t", "applies_to": tag}])

# ------------------------------------------------------------------ 1. lessons reach the right department
def test_lessons_are_routed_by_department():
    _lesson("SHORTS-L", "reels"); _lesson("PACK-L", "packaging"); _lesson("TITLE-L", "title"); _lesson("GEN-L", ""); _lesson("RX-L", "reactions"); _lesson("OPEN-L", "opening")
    assert "SHORTS-L" in GR.lessons_for("reel") and "SHORTS-L" not in GR.lessons_for("showrunner") and "SHORTS-L" not in GR.lessons_for("packager")
    assert {"PACK-L", "TITLE-L"} <= set(GR.lessons_for("packager").split("\n")) and "GEN-L" in GR.lessons_for("showrunner")
    assert "RX-L" in GR.lessons_for("writer") and "OPEN-L" in GR.lessons_for("writer") and "OPEN-L" in GR.lessons_for("showrunner")
    assert GR.lessons_for("reel", rows=[]) == "none yet"

def test_per_video_shorts_lessons_no_longer_push_out_the_others():
    _lesson("KEEP-ME", "")
    for i in range(30): _lesson(f"shorts {i}", "reels")
    assert "KEEP-ME" in ROOM.context()["lessons"]

def test_reel_producer_and_writer_actually_receive_their_lessons(monkeypatch):
    _lesson("SHORTS-LESSON-X", "reels"); _lesson("OPENING-LESSON-Y", "opening")
    seen = []; real = ROOM.ask
    def spy(role, system, prompt, **kw): seen.append(system); return real(role, system, prompt, **kw)
    monkeypatch.setattr(ROOM, "ask", spy)
    ROOM.reels({"spine": {"premise": "p"}}, [{"type": "still", "prompt": "x"} for _ in range(10)], {"reel_formats": ["R3_myth"]}, "EPL")
    assert any("SHORTS-LESSON-X" in s for s in seen)
    seen.clear(); ROOM.run_room(DRAW("EPWR", "collective"), "EPWR")
    writer = [s for s in seen if "ROLE: WRITER" in s]
    assert writer and "OPENING-LESSON-Y" in writer[0] and "RETENTION RULES" in writer[0]

# ------------------------------------------------------------------ 2-3. packaging checked in code
def test_titles_are_checked_and_the_clean_one_wins():
    long = "What Would Really Happen To Every Single Person On Earth If The Moon Vanished Tonight"
    best, runner = GR.choose_titles([long, "The Moon Vanished. Here Is Day One.", "MOON GONE FOREVER NOW", "What If The Moon Vanished Tonight?"], "MOON GONE")
    assert best == "The Moon Vanished. Here Is Day One." and runner == "What If The Moon Vanished Tonight?"
    assert any("long" in i for i in GR.title_issues(long)) and any("shouting" in i for i in GR.title_issues("MOON VANISHED FOREVER tonight ok ok"))
    assert any("repeats" in i for i in GR.title_issues("The Moon Is Gone Forever Now", "MOON GONE FOREVER"))
    assert GR.choose_titles([], "") == ("", "") and GR.choose_titles(["x" * 120]) [0] != ""

def test_thumbnail_text_is_at_most_four_words_and_never_ends_on_a_small_word():
    assert GR.thumb_words("THE OCEAN IS GONE FOREVER NOW") == "THE OCEAN IS GONE"
    assert GR.thumb_words("WHERE IS THE OCEAN TODAY") == "WHERE IS THE OCEAN"
    assert GR.thumb_words("SEE THE END OF THE STORY") == "SEE THE END" and GR.thumb_words("LOOK UP") == "LOOK UP"

def test_tidy_pkg_is_idempotent_and_keeps_every_title():
    pkg = {"titles": ["A Very Long Title That Keeps Going And Going Past Sixty Chars Easily", "Every Ocean Froze At Noon. Then This.", "Ocean Froze"],
           "thumb_text": "NOBODY SURVIVES DAY THREE TODAY", "thumb_text_b": "LOOK"}
    a = EP.tidy_pkg(pkg); b = EP.tidy_pkg(a)
    assert a == b and a["titles"][0] == "Every Ocean Froze At Noon. Then This." and len(a["titles"]) == 3 and len(a["thumb_text"].split()) <= 4
    assert EP._title_b(a, a["titles"][0]) == a["titles"][1]

def test_the_opening_kling_clip_shows_the_thumbnail_scene(setting):
    units = [{"i": i, "start": i * 4.0, "text": f"line {i}"} for i in range(30)]
    shots = [{"type": "still", "prompt": "p"} for _ in range(30)]; shots[5]["type"] = "kling"; shots[20]["type"] = "kling"
    out = ROOM.promise_shot(shots, units, {"thumb_prompt": "a frozen ocean at noon"})
    assert out[5]["prompt"].startswith("first-person POV") and "a frozen ocean at noon" in out[5]["prompt"]      # v8.11: the re-aimed clip keeps the POV rules
    setting("IMMERSION_ON", "FALSE"); out = ROOM.promise_shot(shots, units, {"thumb_prompt": "a frozen ocean at noon"}); setting("IMMERSION_ON", "TRUE")
    assert out[5]["prompt"].startswith("a frozen ocean at noon") and out[5]["promise"] and out[20]["prompt"] == "p" and shots[5]["prompt"] == "p"
    shots[5]["type"] = "still"; assert ROOM.promise_shot(shots, units, {"thumb_prompt": "x"}) == shots
    setting("PROMISE_SHOT_ON", "FALSE"); shots[5]["type"] = "kling"; assert ROOM.promise_shot(shots, units, {"thumb_prompt": "x"}) == shots

def test_brand_is_clear_of_the_timestamp_corner(tmp_path):
    raw = tmp_path / "raw.jpg"; Image.new("RGB", (1920, 1080), (8, 10, 14)).save(raw)
    up, _, _ = ART.compose_thumbnail(str(raw), str(tmp_path), "")
    a = np.asarray(Image.open(up).convert("L"), np.float32); H, W = a.shape
    assert a[int(H * 0.86):, int(W * 0.75):].max() < 120, "something bright sits under YouTube's timestamp"
    assert a[: int(H * 0.08), : int(W * 0.3)].max() > 200, "the brand should be top-left"

def test_a_b_thumbnail_that_fails_the_phone_check_is_never_used(tmp_path, monkeypatch):
    monkeypatch.setattr(QC, "check_thumb", lambda p, s: (False, {"phone_contrast": 1}))
    assert EP._thumb_b({"thumb_prompt_b": "a pillow passing the Moon", "thumb_text_b": "LOOK UP"}, {}, str(tmp_path), "EPB", False) == ""

# ------------------------------------------------------------------ 4-5. scores, missing data, diagnosis
def test_each_dimension_is_scored_on_what_it_can_move():
    sc = GR.dim_scores({"views": 1000, "ctr": 0.05, "ret30": 0.7, "avg_view_pct": 40, "from_shorts": 30, "shorts_subs": 4},
                       [{"views": 1000, "from_shorts": 30, "shorts_subs": 4}] * 3)
    assert sc == {"pack": 0.5, "open": 0.7, "hold": 0.5, "reach": 0.5, "shorts": 0.5}
    assert GR.score_for("title", sc) == 0.5 and GR.score_for("hook", sc) == 0.7 and GR.score_for("reel", sc) == 0.5
    miss = GR.dim_scores({"views": 1000, "ret30": None, "avg_view_pct": 40}, [])
    assert miss["open"] is None and miss["shorts"] is None and GR.score_for("hook", miss) is None
    assert GR.composite(miss) == round(0.5, 4) and GR.composite({"pack": None, "open": None, "hold": None}) is None

def test_diagnosis_needs_history_and_names_the_weak_part():
    hist = [{"views": 1000, "ctr": 0.05, "ret30": 0.7, "avg_view_pct": 40}] * 3
    assert GR.diagnose({"views": 1000, "ret30": 0.3, "ctr": 0.05, "avg_view_pct": 40}, hist[:2])[0] == "insufficient data"
    lab, les = GR.diagnose({"views": 1000, "ret30": 0.3, "ctr": 0.05, "avg_view_pct": 40, "title": "T"}, hist)
    assert lab == "opening" and "first ~30 s" in les
    assert GR.diagnose({"views": 1000, "ret30": 0.7, "ctr": 0.02, "avg_view_pct": 40}, hist)[0] == "packaging"
    assert GR.diagnose({"views": 1000, "ret30": 0.7, "ctr": 0.05, "avg_view_pct": 20}, hist)[0] == "holding"
    assert GR.diagnose(hist[0], hist) == ("healthy", "")

def _live(eid, hours, **kw):
    slot = (core.now_utc() - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"episode_id": eid, "slot_et": slot, "status": "LIVE", "yt_id": "Y" + eid, "title": "T " + eid, "pkg_check": json.dumps({"action": "kept"})}
    row.update(kw); core.store().append("Episodes", [row])

def _strat(dim, name, n=0, ssum=0.0, status="ACTIVE"):
    core.store().append("Strategies", [{"dimension": dim, "name": name, "definition": "d", "status": status, "plays": n, "score_sum": ssum, "score_n": n}])

def _s(name): return next(r for r in core.store().rows("Strategies") if r["name"] == name)

def test_missing_analytics_are_retried_then_recorded_as_no_data_never_scored(monkeypatch):
    _strat("hook", "HK"); _live("EPM", 100, draw_json=json.dumps({"strategies": {"hook": "HK"}}))
    monkeypatch.setattr(MG, "pkg_rescue", lambda: []); monkeypatch.setattr(MG, "_evolve", lambda: None)
    monkeypatch.setattr(MG, "_analytics", lambda vid, t: {"pending": True})
    MG.learn(); assert not [a for a in core.store().rows("Analytics") if a["episode_id"] == "EPM"]
    core.store().update("Episodes", "episode_id", "EPM", {"slot_et": (core.now_utc() - dt.timedelta(days=12)).strftime("%Y-%m-%dT%H:%M:%SZ")})
    MG.learn(); a = next(a for a in core.store().rows("Analytics") if a["episode_id"] == "EPM")
    assert a["data_note"].startswith("no data") and a["score"] == "" and str(_s("HK")["plays"]) in ("0", "")

def test_strategies_are_credited_per_dimension_and_missing_parts_are_skipped(monkeypatch):
    for dm, nm in (("title", "TT"), ("hook", "HH"), ("story", "SS"), ("reel", "RR"), ("reel", "R2")): _strat(dm, nm)
    _live("EPD", 100, draw_json=json.dumps({"strategies": {"title": "TT", "hook": "HH", "story": "SS", "reel": "RR"}, "reel_formats": ["RR", "R2"]}))
    monkeypatch.setattr(MG, "pkg_rescue", lambda: []); monkeypatch.setattr(MG, "_evolve", lambda: None)
    monkeypatch.setattr(MG, "_analytics", lambda vid, t: {"views": 1000, "avg_view_pct": 40, "avg_view_sec": 200, "ret30": None, "ctr": None, "ctr_kind": "proxy",
                                                          "likes": 1, "shares": 1, "subs": 1, "from_shorts": 20, "curve": []})
    MG.learn()
    assert str(_s("HH")["plays"]) in ("0", ""), "no opening data = the hook is not credited"
    assert float(_s("SS")["score_sum"]) == 0.5 and float(_s("TT")["score_sum"]) == 0.5
    assert int(float(_s("RR")["score_n"])) == 1 and int(float(_s("R2")["score_n"])) == 1, "every reel format used is credited once with the Shorts result"
    row = next(a for a in core.store().rows("Analytics") if a["episode_id"] == "EPD")
    assert row["diagnosis"] == "insufficient data" and row["data_note"] == "ok" and row["shorts_views"] != ""

def test_analytics_never_invents_numbers(monkeypatch):
    class R:
        def __init__(self, j): self.j = j
        def json(self): return self.j
    monkeypatch.setattr(MG, "FAKE", False); monkeypatch.setattr(MG, "gheaders", lambda: {})
    monkeypatch.setattr(MG.requests, "get", lambda *a, **k: R({}))
    assert MG._analytics("VID", core.now_utc()) == {"pending": True}
    monkeypatch.setattr(MG.requests, "get", lambda *a, **k: R({"error": {"code": 403}}))
    assert MG._analytics("VID", core.now_utc()) is None
    calls = iter([R({"rows": [[500, 41.0, 230, 3, 1, 2]]}), R({"rows": []}), R({}), R({})])
    monkeypatch.setattr(MG.requests, "get", lambda *a, **k: next(calls))
    m = MG._analytics("VID", core.now_utc())
    assert m["views"] == 500 and m["ret30"] is None and m["ctr"] is None and m["ctr_kind"] == "proxy"

# ------------------------------------------------------------------ smarter rescue
def _pace_hist(paces):
    for i, p in enumerate(paces): _live(f"PH{i}", 200, pkg_check=json.dumps({"pace": p, "action": "kept"}))

def test_no_swap_during_a_channel_wide_dip(monkeypatch):
    _pace_hist([100, 100, 100, 20, 20, 20]); _live("EPDIP", 40, pkg_check="")
    monkeypatch.setattr(PUB, "yt_views", lambda vid: 40 * 20)
    called = []; monkeypatch.setattr(MG, "_swap", lambda st, e, rec: called.append(1) or "swapped title")
    done = MG.pkg_rescue()
    assert done[0][1].startswith("kept: channel-wide dip") and not called

def test_a_swap_is_judged_once_a_day_later(monkeypatch):
    at = (core.now_utc() - dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _live("EPSW", 70, pkg_check=json.dumps({"action": "swapped title", "views": 100, "pace": 2.0, "at": at}))
    monkeypatch.setattr(PUB, "yt_views", lambda vid: 100 + 30 * 5)
    assert ("EPSW", "judged: helped") in MG.pkg_rescue()
    rec = json.loads(next(e for e in core.store().rows("Episodes") if e["episode_id"] == "EPSW")["pkg_check"])
    assert rec["after"]["verdict"] == "helped" and any("runner-up package lifted" in l["lesson"] for l in core.store().rows("Lessons"))
    assert MG.pkg_rescue() == [] or all(x[0] != "EPSW" for x in MG.pkg_rescue())

def test_a_slower_pace_after_the_swap_is_unclear_not_a_failure(monkeypatch):
    at = (core.now_utc() - dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _live("EPUN", 70, pkg_check=json.dumps({"action": "swapped title", "views": 100, "pace": 5.0, "at": at}))
    monkeypatch.setattr(PUB, "yt_views", lambda vid: 130)
    assert ("EPUN", "judged: unclear") in MG.pkg_rescue()

# ------------------------------------------------------------------ 6. strategy log + rollback
def test_a_worse_replacement_is_rolled_back_once():
    _strat("hook", "OLD", 5, 2.5, "RETIRED"); _strat("hook", "NEW", 5, 1.5)
    GR.log_change("hook", "invented", "NEW", "OLD", 0.5)
    assert GR.rollbacks() == [("NEW", "OLD")]
    assert _s("OLD")["status"] == "ACTIVE" and _s("NEW")["status"] == "RETIRED"
    assert GR.rollbacks() == [] and GR.recently_restored("OLD")
    assert any(r["action"] == "rolled_back" for r in core.store().rows("Strategy_Log"))

def test_a_better_replacement_is_kept_and_an_unproven_one_waits():
    _strat("thumb", "T_OLD", 5, 2.0, "RETIRED"); _strat("thumb", "T_NEW", 5, 3.5); GR.log_change("thumb", "invented", "T_NEW", "T_OLD", 0.4)
    _strat("story", "S_OLD", 5, 2.0, "RETIRED"); _strat("story", "S_NEW", 2, 0.2); GR.log_change("story", "invented", "S_NEW", "S_OLD", 0.4)
    assert GR.rollbacks() == []
    acts = {(r["name"], r["action"]) for r in core.store().rows("Strategy_Log")}
    assert ("T_NEW", "kept") in acts and ("S_NEW", "kept") not in acts and _s("S_NEW")["status"] == "ACTIVE"

def test_evolve_logs_its_changes_and_never_retires_a_just_restored_strategy():
    for nm, ssum in (("V1", 4.0), ("V2", 4.0), ("V3", 1.0)): _strat("voice_x", nm, 5, ssum)
    MG._evolve()
    log = core.store().rows("Strategy_Log")
    assert any(r["action"] == "retired" and r["name"] == "V3" for r in log) and any(r["action"] == "invented" and r["replaces"] == "V3" for r in log)
    for nm, ssum in (("W1", 4.0), ("W2", 4.0), ("W3", 1.0)): _strat("voice_y", nm, 5, ssum)
    GR.log_change("voice_y", "rolled_back", "W9", "W3", 0.1)
    MG._evolve(); assert _s("W3")["status"] == "ACTIVE"

# ------------------------------------------------------------------ schema, settings, research rules
def test_schema_only_appends_and_every_new_setting_has_a_default():
    an = core.TABS["Analytics"]; i = an.index("from_shorts")          # v8.7 appends four more columns AFTER these (append-only schema)
    assert an[i:i + 5] == ["from_shorts", "diagnosis", "data_note", "shorts_views", "shorts_subs"] and an[-7:] == ["impressions", "wtpi", "rel30", "rel_avg", "engaged_views", "days", "first_json"]   # v11 appended engaged_views (append-only schema rule kept)
    assert core.TABS["Strategy_Log"][:3] == ["ts", "dimension", "action"]
    for k in ("TITLE_MIN_CHARS", "TITLE_MAX_CHARS", "THUMB_MAX_WORDS", "PROMISE_SHOT_ON", "DIAG_MIN_HISTORY", "ANALYTICS_GIVEUP_DAYS", "STRATEGY_EVAL_PLAYS", "PKG_DIP_GUARD_ON"):
        assert core.DEFAULTS[k][0] != "" and len(core.DEFAULTS[k][1]) > 20, k

def test_the_click_and_retention_rules_reach_the_prompts():
    assert "30-60 characters" in DATA.CRAFT["packager"] and "bottom-right" in DATA.CRAFT["packager"]
    assert DATA.CRAFT["retention"] in DATA.CRAFT["writer"] and DATA.CRAFT["retention"] in DATA.CRAFT["humanize"]
    assert DATA.CRAFT_BY_ROLE["WRITER"] == DATA.CRAFT["writer"]

def test_learn_adds_missing_tabs_by_itself(monkeypatch):
    seen = []; st = core.store(); real = st.ensure_tabs
    monkeypatch.setattr(type(st), "ensure_tabs", lambda self: seen.append(1) or real())
    monkeypatch.setattr(MG, "pkg_rescue", lambda: []); MG.learn()
    assert seen
