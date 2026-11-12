import pytest
"""v8.5 growth patch: motion + fresh pictures in the opening (moved, never added), the B thumbnail and the packaging rescue, Shorts -> long-video learning,
cost accounting, and nothing from v8.4 lost (Episodes column order, workflows). The reels this patch cut from every long video left in v12 V2c-b2b2
(tests/test_v12_cutdowns.py)."""
import os, json, datetime as dt
from PIL import Image
from whatifs import core, room as ROOM, episode as EP, manage as MG, governor as G, prompts as P, art as ART, publish as PUB

@pytest.fixture(autouse=True)
def _v931_rescue_timing(setting):
    setting("PKG_RESCUE_HOURS", "36")          # v9.3.1 moved the default to 72 h; these tests keep the v8.5 timing


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ opening: motion and fresh pictures are MOVED into the first seconds
def _units(n=60, step=4.0):
    return [{"i": i, "start": i * step, "text": f"line {i}", "tag": "reveal" if i % 7 == 3 else "none"} for i in range(n)]

def _late_plan_shots(units):
    shots = [{"unit": u["i"], "type": "still", "prompt": "p"} for u in units]
    for i in (30, 40, 50): shots[i]["type"] = "kling"
    for i in (20, 25, 35, 45): shots[i]["type"] = "living"
    return shots

def test_motion_is_moved_into_the_opening_without_changing_the_counts():
    units = _units(); plan = {"kling": 3, "living": 4}
    out = ROOM.normalise_shots(_late_plan_shots(units), units, plan, "look", peaks=[50])      # a peak = the shot that carries the big picture
    opening = ROOM.opening_units(units)                       # 45 s / 4 s per unit -> units 0..11
    assert opening == list(range(12))
    assert sum(s["type"] == "kling" for s in out) == 3 and sum(s["type"] == "living" for s in out) == 4      # same cost
    assert sum(out[i]["type"] == "kling" for i in opening) >= 1 and sum(out[i]["type"] == "living" for i in opening) >= 2
    assert out[50]["type"] == "kling", "the clip on a peak (the shot before a reaction) must keep its clip"
    moved = next(i for i in opening if out[i]["type"] == "kling")
    assert out[moved]["hero"] and out[moved]["motion"] and units[moved]["tag"] == "reveal", "reveal lines get the motion first"

def test_front_load_never_invents_clips_and_can_be_switched_off(setting):
    units = _units(); out = ROOM.normalise_shots(_late_plan_shots(units), units, {"kling": 0, "living": 0}, "look")
    assert not any(s["type"] in ("kling", "living") for s in out)
    setting("OPENING_WINDOW_SEC", "0")
    out = ROOM.normalise_shots(_late_plan_shots(units), units, {"kling": 3, "living": 4}, "look")
    assert [i for i, s in enumerate(out) if s["type"] == "kling"] == [30, 40, 50]

def test_already_front_loaded_plans_are_left_alone():
    units = _units(); shots = _late_plan_shots(units); shots[2]["type"] = "kling"; shots[30]["type"] = "still"
    shots[4]["type"] = shots[6]["type"] = "living"; shots[20]["type"] = shots[25]["type"] = "still"
    out = ROOM.normalise_shots(shots, units, {"kling": 3, "living": 4}, "look")
    assert [i for i, s in enumerate(out) if s["type"] == "kling"] == [2, 40, 50]

def test_every_opening_shot_gets_its_own_picture_inside_the_same_budget():
    shots = [{"type": "still"} for _ in range(60)]; shots[30]["type"] = "kling"
    a = EP.anchor_shots(shots, 20, opening=list(range(12)))
    assert set(range(12)) <= set(a) and 30 in a
    assert len(a) <= 20 + 12, "only the repetition guard may add pictures beyond the budget (as in v8.2)"
    base = EP.anchor_shots(shots, 20)
    assert not set(range(1, 12)) <= set(base), "without the opening rule the first seconds re-use pictures (the v8.4 behaviour)"

def test_opening_fresh_off_restores_the_old_allocation(setting):
    setting("OPENING_FRESH_ON", "FALSE")
    shots = [{"type": "still"} for _ in range(60)]
    assert EP.anchor_shots(shots, 20, opening=list(range(12))) == EP.anchor_shots(shots, 20)

# ------------------------------------------------------------------ Shorts: bridge (default), standalone, teaser
PLAN = {"lines": ["[DIRECTOR] [tension] Every ocean just froze.", "[SKEPTIC] [wow] The fish?", "[DIRECTOR] Fine for 3 days."],
        "end_line": "Whether anyone survives day four? That is the full simulation, on our channel.", "shots": [0, 1, 2, 3]}

# ------------------------------------------------------------------ reels 3-4: released on the next days, once
# ------------------------------------------------------------------ packaging rescue
def _live(eid, hours, pkg="", **kw):
    slot = (core.now_utc() - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"episode_id": eid, "slot_et": slot, "status": "LIVE", "yt_id": "Y" + eid, "title": "Title A " + eid, "pkg_check": pkg, "assets": json.dumps({"release.json": "r", "thumb_b.jpg": "t"})}
    row.update(kw); core.store().append("Episodes", [row])

def _hist(n, pace=100.0):
    for i in range(n): _live(f"H{i}", 200, json.dumps({"pace": pace, "action": "kept"}))

def _fakes(monkeypatch, views, tmp_path):
    calls = {"title": [], "thumb": []}
    monkeypatch.setattr(PUB, "yt_views", lambda vid: views)
    monkeypatch.setattr(PUB, "yt_set_title", lambda vid, t: calls["title"].append(t) or True)
    monkeypatch.setattr(PUB, "yt_thumbnail", lambda vid, p: calls["thumb"].append(p) or True)
    rj = tmp_path / "release.json"; json.dump({"title_b": "Title B", "thumb_b": "thumb_b.jpg"}, open(rj, "w"))
    tb = tmp_path / "thumb_b.jpg"; Image.new("RGB", (64, 36)).save(tb)
    monkeypatch.setattr(MG, "_fetch_some", lambda ep, a, names: {"release.json": str(rj), "thumb_b.jpg": str(tb)})
    return calls

def test_no_baseline_means_no_swap(monkeypatch, tmp_path):
    calls = _fakes(monkeypatch, 5, tmp_path); _hist(2); _live("EPN", 40)
    assert MG.pkg_rescue() == [("EPN", "kept: only 2 earlier videos measured (needs 3)")] and not calls["title"]

def test_a_lagging_video_is_swapped_once_to_the_runner_up(monkeypatch, tmp_path):
    calls = _fakes(monkeypatch, 40 * 20, tmp_path); _hist(3); _live("EPL", 40)       # pace 20/h vs median 100/h
    done = MG.pkg_rescue()
    assert done == [("EPL", "swapped title + thumbnail")] and calls["title"] == ["Title B"] and len(calls["thumb"]) == 1
    row = next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPL")
    assert row["title"] == "Title B" and "runner-up" in row["notes"] and json.loads(row["pkg_check"])["ratio"] == 0.2
    assert any("swapped to 'Title B'" in l["lesson"] for l in core.store().rows("Lessons"))
    assert MG.pkg_rescue() == [], "checked once only"

def test_an_on_pace_video_is_kept(monkeypatch, tmp_path):
    calls = _fakes(monkeypatch, 40 * 90, tmp_path); _hist(3); _live("EPG", 40)
    assert MG.pkg_rescue() == [("EPG", "kept: on pace")] and not calls["title"] and not calls["thumb"]

def test_rescue_waits_for_age_skips_old_videos_and_can_be_switched_off(monkeypatch, tmp_path, setting):
    _fakes(monkeypatch, 10, tmp_path); _hist(3)
    _live("EPY", 10); _live("EPOLD", 300)
    assert MG.pkg_rescue() == []
    old = next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPOLD")
    assert "too old" in old["pkg_check"]
    setting("PKG_RESCUE_ON", "FALSE"); _live("EPOFF", 40); assert MG.pkg_rescue() == []

def test_unreadable_views_try_again_tomorrow(monkeypatch, tmp_path):
    _fakes(monkeypatch, None, tmp_path); _hist(3); _live("EPU", 40)
    assert MG.pkg_rescue() == [] and not next(r for r in core.store().rows("Episodes") if r["episode_id"] == "EPU")["pkg_check"]

def test_title_b_and_thumb_b_helpers(tmp_path, setting):
    assert EP._title_b({"titles": ["A", "a ", "B"]}, "A") == "B" and EP._title_b({"titles": ["A"]}, "A") == ""
    assert EP._thumb_b({"thumb_prompt_b": ""}, {}, str(tmp_path), "EP", False) == ""
    setting("PKG_RESCUE_ON", "FALSE"); assert EP._thumb_b({"thumb_prompt_b": "x"}, {}, str(tmp_path), "EP", False) == ""

def test_packager_brief_asks_for_a_different_runner_up():
    assert "thumb_prompt_b" in P.PACKAGER and "DIFFERENT idea" in P.PACKAGER

def test_swapped_episodes_do_not_credit_the_swapped_out_title_strategy(monkeypatch):
    st = core.store()
    st.append("Strategies", [{"dimension": "title", "name": "TQ", "definition": "d", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0},
                             {"dimension": "voice", "name": "VQ", "definition": "d", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0}])
    _live("EPW", 100, json.dumps({"action": "swapped title + thumbnail"}), draw_json=json.dumps({"strategies": {"title": "TQ", "voice": "VQ"}, "reel_style": "bridge"}))
    monkeypatch.setattr(MG, "pkg_rescue", lambda: [])
    MG.learn()
    s = {r["name"]: r for r in st.rows("Strategies")}
    assert str(s["TQ"]["plays"]) in ("0", "") and str(s["VQ"]["plays"]) == "1"
    assert any("came from the Shorts feed" in l["lesson"] and "bridge reels" in l["lesson"] for l in st.rows("Lessons"))      # a video an older version made keeps the style of its reels on record

# ------------------------------------------------------------------ money and schema
def test_the_b_thumbnail_is_counted_in_every_estimate(setting):
    d = {"stills": 52, "living": 8, "kling": 3}
    on, min_on = EP.est_cost_inr(d), G.min_episode_cost_inr()
    setting("PKG_RESCUE_ON", "FALSE")
    off, min_off = EP.est_cost_inr(d), G.min_episode_cost_inr()
    one = core.S("USD_INR", float) * core.S("PRICE_THUMB_USD", float)
    assert G.premium_images() == 1 and abs((on - off) - one) < 0.01 and abs((min_on - min_off) - one) < 0.01

def test_new_columns_only_append_so_older_sheets_keep_their_order():
    old = ["episode_id", "slot_et", "premise", "ptype", "presentation_format", "title", "status", "yt_id", "reel1_yt", "reel2_yt",
           "ig1", "ig2", "fb1", "fb2", "kill", "draw_json", "cost_inr", "release_tag", "assets", "notes", "updated"]
    assert core.TABS["Episodes"][:len(old)] == old and core.TABS["Episodes"][len(old):len(old) + 7] == ["reel3_yt", "reel4_yt", "ig3", "ig4", "fb3", "fb4", "pkg_check"]      # v9 appends after these
    an = core.TABS["Analytics"]; assert an[an.index("score") + 1] == "from_shorts"      # v8.6 appends more columns after it

def test_every_new_setting_has_a_default_and_a_note():
    for k in ("OPENING_WINDOW_SEC", "OPENING_KLING_MIN", "OPENING_LIVING_MIN",
              "OPENING_FRESH_ON", "PKG_RESCUE_ON", "PKG_RESCUE_HOURS", "PKG_RESCUE_RATIO", "PKG_RESCUE_MIN_HISTORY"):
        assert core.DEFAULTS[k][0] != "" and len(core.DEFAULTS[k][1]) > 20, k
