"""v12 V2d-b THE LADDER'S RULES: every moving second comes from one market of licensed models, the month's money becomes moving seconds with a floor, code
places them and the renderer shows a paid clip whole, the finished file is measured (a long video's moving share, a Short's every half second), a
character is drawn or absent, real footage is a short anchor with a record, and a Short sounds from its first frame. Each rule both ways. No keys, no network."""
import datetime as dt, inspect, json, os, shutil, subprocess
import numpy as np
import pytest
from whatifs import core, clips as CL, costguard as CG, governor as G, media as MD, steward as STW, scout as SC, shorts2 as SH, manage as MG, episode as EP, contract as CON
from whatifs import motion as MOT, stock as STK, sound as SD, specials as SP, living as LV, shotplan as SPL, render as RN, anim as AN, notify as NT, publish as PUB, ladder as LAD, release as REL
from whatifs import opening as OPEN, format_engine as FE, truth as TR, preflight as PF
from whatifs.org import registry as REG, levers as LEV, rnd as RND, memos as MEM
from tests.conftest import OLD_CLIPS, OLD_MOTION
from tests.paid_calls import watch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEY, H3, H3MAX, PIX, KLING = (r["id"] for r in json.loads(core.DEFAULTS["CLIP_MODELS"][0]))
OLD_LIVING = OLD_MOTION["FAL_LIVING_MODEL"]
DEC = dt.datetime(2026, 12, 1, 6, 0, tzinfo=dt.timezone.utc)
OWN_IDS = ("EP209906070900", "EP209906140900", "SH209906070900", "SH209906210900", "SH209906280900")      # the whole productions of this file: ids no other test file uses (a test proves it)

@pytest.fixture
def ladder(setting):
    """The cells as the code ships them: the clip market and the motion ladder ON (the older tests run with both off: tests/conftest.py)."""
    for k in list(OLD_CLIPS) + list(OLD_MOTION): setting(k, core.DEFAULTS[k][0])
    setting("MONTH_CAP_OVERRIDES", "")
    return setting

def _rows(**change):
    rows = [dict(r) for r in json.loads(core.DEFAULTS["CLIP_MODELS"][0])]
    for mid, upd in change.items(): next(r for r in rows if r["id"] == {"hey": HEY, "h3": H3, "max": H3MAX, "pix": PIX, "kling": KLING}[mid]).update(upd)
    return rows

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _december(monkeypatch, left=4):
    monkeypatch.setattr(G, "now_utc", lambda: DEC); monkeypatch.setattr(G, "episodes_left_this_month", lambda: left)

def _units(durs, speaker="DIRECTOR"):
    out = []; t = 0.0
    for k, d in enumerate(durs): out.append({"i": k, "start": round(t, 3), "end": round(t + d - 0.1, 3), "text": f"line {k} of the story", "tag": "none", "speaker": speaker}); t += d
    return out, round(t, 3)

def _film(path, parts, w=320, h=180, audio=None):
    """A small film from parts: ('move', seconds) = one made picture under a camera that never stops (the offline clip), ('hold', seconds) = one picture
    held. Encoded without grain; `audio` = a sound file laid under it."""
    ins = []; n = 0
    for kind, sec in parts:
        p = f"{path}.{n}.mp4"; n += 1
        if kind == "move": MD.fake_clip(p, w, h, f"{os.path.basename(path)}{n}", sec)
        else:
            img = MD.fake_image(p + ".jpg", w, h, f"{os.path.basename(path)}{n}")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-t", str(sec), "-r", "30", "-pix_fmt", "yuv420p", p], check=True)
        ins += ["-i", p]
    flt = "".join(f"[{k}:v]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + ins + (["-i", audio] if audio else []) + ["-filter_complex", flt, "-map", "[v]"] + (["-map", f"{n}:a", "-c:a", "aac", "-shortest"] if audio else []) + ["-r", "30", "-pix_fmt", "yuv420p", path]
    subprocess.run(cmd, check=True); return path

def _voice(path, start=0.35, sec=6.0, sr=48000):
    import soundfile as sf
    t = np.arange(int(sec * sr)) / sr; v = np.zeros(len(t), np.float32); a = int(start * sr)
    v[a:] = (0.3 * np.sin(2 * np.pi * 180 * t[a:]) * (np.sin(2 * np.pi * 3 * t[a:]) > 0)).astype(np.float32); sf.write(path, v, sr); return path

# ------------------------------------------------------------------ 1. ONE market: a licence, and the living tier by the same rule
def test_a_model_licensed_for_research_is_never_bought(ladder, setting, monkeypatch):
    assert all(r["lic"] == "commercial" for r in CL.table()) and CL.LICENSED == "commercial"                      # as fal's listing said on 13 Nov 2026
    r = dict(CL.row(HEY), lic="research"); assert CL.issues(r) == ["its licence is 'research', not commercial"] and CL.issues(CL.row(HEY)) == []
    bare = {k: v for k, v in CL.row(HEY).items() if k != "lic"}; assert CL.issues(bare) == ["its licence is 'not stated', not commercial"]      # a row that says nothing is not bought either
    rows = _rows(hey={"lic": "research"}); p = CL.pick(rows, 1.0); assert p["row"]["id"] == H3 and HEY not in p["tied"]      # the best-value model of the table - and never picked
    assert CL.pick(_rows(hey={"lic": "research", "usd_s": {"768p": 0.0001}, "elo": 2000}), 1.0)["row"]["id"] != HEY          # ... however cheap, however well ranked
    setting("CLIP_MODELS", json.dumps(_rows()))                                                                   # THE LICENCE IS READ LIVE with the status
    monkeypatch.setattr(SC, "fal_licence", lambda ids: {i: ("research" if i == HEY else "commercial") for i in ids})
    got = {x["id"]: x for x in CL.refresh()}; assert got[HEY]["lic"] == "research" and got[H3]["lic"] == "commercial" and CL.row(HEY)["lic"] == "research"
    assert CL.choice()["row"]["id"] != HEY and CL.hero() is not None and CL.issues(CL.row(HEY))                   # the pick moves away at once
    setting("CLIP_MODELS", json.dumps(_rows()))
    monkeypatch.setattr(SC, "fal_licence", lambda ids: (_ for _ in ()).throw(RuntimeError("down")))               # a listing that does not answer changes nothing
    assert {x["id"]: x["lic"] for x in CL.refresh()}[HEY] == "commercial"
    monkeypatch.setattr(SC, "fal_licence", lambda ids: {i: "" for i in ids}); assert {x["id"]: x["lic"] for x in CL.refresh()}[HEY] == "commercial"      # an empty word is no reading
    assert SC.fal_licence.__name__ == "<lambda>" and OLD_LIVING not in core.DEFAULTS["MODEL_LADDERS"][0] and OLD_LIVING not in core.DEFAULTS["FAL_LIVING_MODEL"][0]

def test_the_offline_listing_says_what_each_row_says_about_its_licence(ladder):
    assert SC.fal_licence([HEY, OLD_LIVING]) == {HEY: "commercial", OLD_LIVING: ""}

def test_the_living_tier_is_a_row_of_the_same_market(ladder, setting):
    assert CL.ladder() and CL.living()["id"] == HEY == core.S("FAL_LIVING_MODEL") and G.living_usd_s() == 0.02
    setting("FAL_LIVING_MODEL", OLD_LIVING); assert CL.row(OLD_LIVING) is None and CL.living()["id"] == HEY      # a model outside the table (the research-only one): the hero's row, never that model
    setting("CLIP_MODELS", json.dumps(_rows(pix={"lic": "research"}))); setting("FAL_LIVING_MODEL", PIX); assert CL.living()["id"] == HEY      # a row that cannot be bought: the same
    setting("FAL_LIVING_MODEL", H3); assert CL.living()["id"] == H3 and G.living_usd_s() == 0.06                  # a row that can be bought is taken as the cell says
    setting("MOTION_LADDER_ON", "FALSE"); assert CL.living() is None and not CL.ladder() and not MOT.on() and G.living_usd_s() == 0.0      # the ladder off: the older way
    setting("MOTION_LADDER_ON", "TRUE"); setting("CLIP_VALUE_ON", "FALSE"); assert CL.living() is None and not MOT.on()      # ... and it needs the clip market

def test_the_weekly_review_picks_the_living_model_by_the_same_rule_and_the_steward_switches(ladder, setting, monkeypatch):
    _quiet(monkeypatch); _december(monkeypatch); setting("FAL_LIVING_MODEL", PIX); setting("CLIP_MODELS", json.dumps(_rows(pix={"shape": "follows", "res": "360p"})))
    assert CL.choice(role="living")["row"]["id"] == HEY and CL.choice(role="hero")["row"]["id"] == HEY            # the same rule at the same line; a living model ranked far lower is replaced
    out = CL.review(); assert out["living"] == HEY and core.S("FAL_LIVING_MODEL") == HEY and float(core.S("PRICE_LIVING_USD")) == pytest.approx(0.10)
    ch = [r for r in core.store().rows("Model_Changes") if r.get("role") == "living"]; assert len(ch) == 1 and ch[0]["to"] == HEY and "picked by value" in ch[0]["why"]
    n = len(core.store().rows("Model_Changes")); CL.review(); assert len(core.store().rows("Model_Changes")) == n      # nothing to switch: nothing written
    setting("PRICE_LIVING_USD", "0.5"); CL.review(); assert float(core.S("PRICE_LIVING_USD")) == pytest.approx(0.10)      # the price cell follows the row
    setting("MOTION_LADDER_ON", "FALSE"); setting("FAL_LIVING_MODEL", PIX); assert "living" not in CL.review() and core.S("FAL_LIVING_MODEL") == PIX      # the ladder off: the living cell is left alone

def test_the_stewards_replacement_for_the_living_model_comes_from_the_market(ladder, setting, monkeypatch):
    _december(monkeypatch)
    nxt = STW.next_candidate("living", HEY); assert nxt and nxt["id"] in (H3, H3MAX) and nxt["id"] != OLD_LIVING      # the next pick by the rule, never an entry of the older ladder
    setting("MOTION_LADDER_ON", "FALSE"); setting("MODEL_LADDERS", json.dumps({"living": [{"id": OLD_LIVING, "usd": 0.02}, {"id": "code-motion", "usd": 0}]}))
    assert STW.next_candidate("living", HEY)["id"] == OLD_LIVING                                                  # the older way reads the older ladder

def test_a_living_clip_is_bought_by_the_second_and_logged_in_seconds(ladder, setting, tmp_path):
    img = MD.fake_image(str(tmp_path / "p.jpg"), 160, 90, 1)
    p = MD.animate(None, img, "p", str(tmp_path / "l.mp4"), "EPL1", hero=False, seconds=6.2); core.flush_costs()
    row = [r for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPL1"]; assert len(row) == 1 and (row[0]["item"], float(row[0]["units"])) == ("living_clip", 7.0)
    assert abs(STK.seconds(p) - 7) < 0.2                                                                          # offline, the clip is as long as it was bought
    MD.animate(None, img, "p", str(tmp_path / "l2.mp4"), "EPL2", hero=False); core.flush_costs()                    # no length given: one scene's worth
    assert float(next(r for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPL2")["units"]) == 5.0
    setting("MOTION_LADDER_ON", "FALSE"); p3 = MD.animate(None, img, "p", str(tmp_path / "l3.mp4"), "EPL3", hero=False, seconds=9); core.flush_costs()
    assert float(next(r for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPL3")["units"]) == 1.0 and abs(STK.seconds(p3) - 5) < 0.2      # the older way: one flat five-second clip

def test_a_real_living_request_is_its_rows_request_at_its_rows_price(ladder, setting, monkeypatch, tmp_path):
    sent = []
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD, "fal_allowed", lambda: True)
    monkeypatch.setattr(MD, "fal_run", lambda model, args, timeout=0: sent.append((model, args)) or {"video": {"url": "x"}})
    monkeypatch.setattr(MD, "_dl", lambda url, path: MD.fake_clip(path, 160, 90, "dl", 1))
    pic = MD.fake_image(str(tmp_path / "p.png"), 160, 90, 2)
    MD.animate("https://img", pic, "P", str(tmp_path / "o.mp4"), "EPL4", hero=False, seconds=7.4)
    assert sent == [(HEY, CL.args(CL.row(HEY), "https://img", "P", 7.4))] and sent[0][1]["duration"] == 8
    core.flush_costs(); row = next(r for r in core.store().rows("Cost_Log") if r["episode_id"] == "EPL4")
    assert (row["item"], float(row["units"])) == ("living_clip", 8.0) and float(row["inr"]) == pytest.approx(8 * 0.02 * core.S("USD_INR", float), abs=0.01)
    setting("FAL_LIVING_MODEL", OLD_LIVING); sent.clear()                                                         # the cell still names the research-only model (a live Sheet before its move):
    MD.animate("https://img", pic, "P", str(tmp_path / "o2.mp4"), "EPL5", hero=False, seconds=5); assert [m for m, _ in sent] == [HEY]      # the clip is bought from the hero's row - that model is never asked

def test_the_one_time_move_takes_a_live_sheet_off_the_research_only_model(ladder, setting, monkeypatch):
    _quiet(monkeypatch); _december(monkeypatch); setting("FAL_LIVING_MODEL", OLD_LIVING)
    setting("MODEL_LADDERS", json.dumps({"hero": [], "living": [{"id": OLD_LIVING, "usd": 0.02}, {"id": "code-motion", "usd": 0}]}))
    done = MG.v12v2db_upgrade(core.store()); assert sorted(done) == ["FAL_LIVING_MODEL", "MODEL_LADDERS"] and core.S("FAL_LIVING_MODEL") == HEY
    assert [e["id"] for e in STW.ladders()["living"]] == ["code-motion"] and "research only" in core.store().rows("Model_Changes")[-1]["why"]
    setting("FAL_LIVING_MODEL", OLD_LIVING); assert MG.v12v2db_upgrade(core.store()) == [] and core.S("FAL_LIVING_MODEL") == OLD_LIVING      # never twice
    setting("V12V2DB_MOVE_DONE", ""); setting("FAL_LIVING_MODEL", H3); assert MG.v12v2db_upgrade(core.store()) == [] and core.S("FAL_LIVING_MODEL") == H3      # his own choice is left alone
    assert inspect.getsource(MG).count("try: v12v2db_upgrade(st)") == 2                                           # both setup sites

def test_preflight_names_a_living_model_that_cannot_be_bought(ladder, setting):
    assert CL.preflight()[0] is True
    setting("FAL_LIVING_MODEL", OLD_LIVING); ok, words = CL.preflight(); assert ok is False and OLD_LIVING in words and "no row" in words and HEY in words
    setting("MOTION_LADDER_ON", "FALSE"); assert CL.preflight()[0] is True

# ------------------------------------------------------------------ 2. the month's money becomes moving seconds
def test_the_floor_of_a_long_video_is_seconds_every_estimate_counts(ladder, setting):
    f = G.moving_floor("ladder"); assert (f["on"], f["floor_s"], f["target_s"], f["own_s"], f["living_s"], f["living_target_s"]) == (True, 108, 216, 27, 81, 189)      # 540 s: a fifth, two fifths; 12 s of footage + 3 scenes
    g = G.moving_floor("long"); assert (g["own_s"], g["living_s"], g["living_target_s"]) == (20, 88, 196)                 # under an override: four scenes of its own, no footage
    assert G.moving_floor("ladder", 505)["living_s"] == 74 and f["inr_s"] == pytest.approx(0.02 * core.S("USD_INR", float))
    L = CG.lines("ladder"); lv = next(l for l in L if l["key"] == "living_clips"); st = next(l for l in L if l["key"] == "stills")
    assert (lv["n"], lv["unit"], lv["item"], lv["calls"]) == (81, "s", "living_clip", {"clip": 16}) and lv["inr"] == pytest.approx(81 * f["inr_s"], abs=0.01)
    assert st["n"] == G.TIERS[0][2] + 16                                                                          # every living clip has a picture of its own
    assert next(l for l in CG.lines("ladder", living_s=150) if l["key"] == "living_clips")["n"] == 150           # an episode says its own seconds
    assert G.full_episode_inr(kind="ladder") == CG.total(L) and G.min_episode_cost_inr() == CG.total(CG.lines(G.long_kind(), kling=core.S("KLING_MIN_CLIPS", int), stills=core.S("STILLS_MIN", int)))
    assert next(l for l in CG.lines(G.long_kind(), kling=4, stills=44, living=0) if l["key"] == "living_clips")["n"] == G.moving_floor()["living_s"]      # the cheapest episode still has its floor
    setting("MOVING_SHARE_MIN_LONG", "30"); assert G.moving_floor("ladder")["living_s"] == 135 and next(l for l in CG.lines("ladder") if l["key"] == "living_clips")["n"] == 135
    setting("MOVING_SHARE_LONG", "10"); assert G.moving_floor("ladder")["living_target_s"] == 135                 # a target under the floor is the floor
    setting("MOTION_LADDER_ON", "FALSE"); off = G.moving_floor("ladder"); assert off["on"] is False and off["living_s"] == 0
    old = next(l for l in CG.lines("ladder") if l["key"] == "living_clips"); assert (old["n"], old["unit"], old["calls"]) == (8, "", {"clip": 8})      # the older way: eight flat-priced clips

def test_the_line_the_model_pick_may_cost_pays_the_floor_too(ladder, setting, monkeypatch):
    _december(monkeypatch); with_floor = G.line_usd_s()
    setting("MOVING_SHARE_MIN_LONG", "5"); low = G.line_usd_s(); setting("MOVING_SHARE_MIN_LONG", "20")
    assert 0.02 < with_floor < low and CL.choice()["row"]["id"] == HEY and CL.choice()["fits"]                    # more seconds to pay = a lower line; today's pick still fits
    setting("MOVING_SHARE_MIN_LONG", "60"); p = CL.choice(); assert G.line_usd_s() < 0.02 and p["fits"] is False and "does not fit" in p["why"]      # a floor the month cannot pay is SAID, never hidden

def test_what_the_split_leaves_free_buys_more_seconds_up_to_the_target(ladder, setting, monkeypatch):
    _december(monkeypatch); sp = G.split(DEC); f = G.moving_floor("ladder"); m = core.S("BUDGET_SAFETY_MARGIN", float)
    p = G.moving_plan("ladder", now=DEC); extra = int(sp["free_inr"] // (sp["long_left"] * m * f["inr_s"]))
    assert sp["fits"] and sp["free_inr"] > 0 and extra > 0 and p["living_s"] == min(f["living_target_s"], 81 + extra) and p["living_floor_s"] == 81
    assert 81 < p["living_s"] < 189 and 20 < p["bought_pct"] < 40 and p["bought_pct"] == pytest.approx(100 * (27 + p["living_s"]) / 540, abs=0.06)      # today's price: more than the floor, less than the target
    mine = G.moving_plan("ladder", mine=True, now=DEC)                                                             # the video being planned has its row already: its own floor cost comes out of what is free
    assert mine["free_inr"] == pytest.approx(sp["free_inr"] - G.full_episode_inr(kind="ladder") * m, abs=1) and mine["living_s"] == 81
    setting("MONTH_CAP_OVERRIDES", "2026-12=9000"); rich = G.moving_plan("ladder", now=DEC); assert rich["living_s"] == 189 and rich["bought_pct"] == 40.0      # money enough: the target, never more
    setting("MONTH_CAP_OVERRIDES", "2026-12=3500"); poor = G.moving_plan("ladder", now=DEC); assert poor["living_s"] == 81 and poor["free_inr"] <= 0      # none free: the floor, never less
    setting("MONTH_CAP_OVERRIDES", ""); monkeypatch.setattr(G, "long_videos_this_month", lambda: 4)
    assert G.moving_plan("ladder", now=DEC)["living_s"] == 81                                                     # no long video left to share it: the floor
    setting("MOTION_LADDER_ON", "FALSE"); assert G.moving_plan("ladder", now=DEC)["on"] is False

def test_a_budget_tier_trims_living_seconds_to_the_floor_and_never_below(ladder, setting, monkeypatch):
    _december(monkeypatch); est = CG.total(CG.lines("ladder", living_s=150)); inr_s = G.moving_floor("ladder")["inr_s"]
    full = G.plan_for_episode(est, 4, living_s=150, floor_s=81); assert (full["tier"], full["living_s"], full["living"]) == ("full", 150, 30)
    assert G.tier_saving(G.TIERS[1], living_s=150, floor_s=81) - G.tier_saving(G.TIERS[1], living_s=81, floor_s=81) == pytest.approx(69 * inr_s, abs=0.01)
    assert G.tier_saving(G.TIERS[0], living_s=150, floor_s=81) == 0
    monkeypatch.setattr(G, "production_room_inr", lambda: est * 4 - 300)                                          # the full tier no longer fits this video's share: the next tier keeps the floor's seconds
    lean = G.plan_for_episode(est, 4, living_s=150, floor_s=81); assert lean["tier"] != "full" and lean["living_s"] == 81 and "81 living seconds (the floor)" in lean["reason"]
    monkeypatch.setattr(G, "production_room_inr", lambda: 200.0)                                                  # not even the floor tier: no video (a cheaper long video is the first video again)
    hold = G.plan_for_episode(est, 1, living_s=150, floor_s=81); assert hold["hold"] is True and hold["living"] == 0
    monkeypatch.setattr(G, "production_room_inr", lambda: 9000.0)
    old = G.plan_for_episode(400, 4); assert "living_s" not in old and old["living"] == min(G.TIERS[0][3], core.S("LIVING_STILLS", int))      # no seconds given: the older tiers

def test_living_seconds_are_a_counted_line(ladder, setting):
    def paid(ep, n): core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": ep, "item": "living_clip", "provider": "fal", "units": n, "inr": 0}])
    L = CG.lines("ladder", living_s=100); paid("EPR1", 100); assert CG.reconcile("EPR1", L, "ladder")["over"] == []
    paid("EPR2", 106); assert CG.reconcile("EPR2", L, "ladder")["over"] == ["living_clip: 106 paid, 100 estimated"]      # a second more than planned is an overrun
    setting("MOTION_LADDER_ON", "FALSE"); paid("EPR3", 12); assert CG.reconcile("EPR3", CG.lines("ladder"), "ladder")["over"] == []      # the older way: living clips are a ceiling nobody counts

# ------------------------------------------------------------------ 3. the placing and the cutting
def test_code_places_the_living_seconds_on_lines_that_can_show_a_whole_clip(ladder):
    units, total = _units([6, 3, 7.4, 2, 2, 9, 12, 5, 4, 6])
    shots = [{"type": "still", "prompt": "x"} for _ in units]; shots[0].update(type="kling", anim={"slot": 0}); shots[1]["type"] = "living"; shots[6]["type"] = "graphic"
    plan = {"living_s": 24, "living": 4}; out = MOT.place(shots, units, total, plan)
    liv = {i: s["buy"] for i, s in enumerate(out) if s["type"] == "living"}
    assert liv == {1: 5, 9: 6, 5: 8, 7: 5} and plan["living_bought_s"] == 24 and plan["living"] == 4
    # 1: the Director's own shot, on a 3-second line - kept, because the still after it carries the clip on (the model's shortest clip is 5 s)
    # 9: then the line farthest from everything that moves | 5: a 9-second line buys 8 (two picture states at most) | 7: the last 5 seconds of the budget
    assert 2 not in liv and all(shots[i]["type"] == out[i]["type"] for i in (0, 6))                             # the line a clip runs into is left alone; a scene and a graphic are never touched
    assert all("buy" not in s for s in out if s["type"] != "living") and [s["type"] for s in shots][1] == "living"      # the input is not changed

def test_placing_never_buys_a_second_no_line_can_show(ladder):
    units, total = _units([3, 2, 4, 3, 2])                                                                        # every line shorter than the model's shortest clip, each followed by a graphic or the end
    shots = [{"type": "still"}, {"type": "graphic"}, {"type": "living"}, {"type": "graphic"}, {"type": "still"}]
    plan = {"living_s": 30}; out = MOT.place(shots, units, total, plan)
    assert [s["type"] for s in out] == ["still", "graphic", "still", "graphic", "still"] and plan["living"] == 0 and plan["living_bought_s"] == 0      # the Director's living shot cannot be shown whole: a still again
    units, total = _units([3, 2, 4]); out = MOT.place([{"type": "still"}, {"type": "still"}, {"type": "still"}], units, total, {"living_s": 30})
    assert [s.get("buy") for s in out] == [5, None, None]                                                         # a short line whose clip can run on into the stills after it: one clip, and the lines it covers are left alone
    out = MOT.place([{"type": "still", "promise": True}, {"type": "still", "short": {"id": "x"}}, {"type": "still", "anim": {}}], units, total, {"living_s": 30})
    assert all(s["type"] == "still" and "buy" not in s for s in out)                                              # the promise picture, the Short's footage and a scene's slot are never brought to life
    units, total = _units([6, 6, 6]); plan = {"living_s": 11}; out = MOT.place([{"type": "still"}] * 3, units, total, plan); assert plan["living_bought_s"] == 6      # the budget binds: one clip of 6, not two
    plan = {"living": 2}; MOT.place([{"type": "still"}] * 3, units, total, plan); assert plan["living_s"] == 10 and plan["living_bought_s"] == 6      # a plan saved before the ladder says clips: five seconds each

def test_with_the_ladder_off_nothing_is_placed(ladder, setting):
    units, total = _units([6, 6]); setting("MOTION_LADDER_ON", "FALSE"); shots = [{"type": "still"}, {"type": "living"}]
    assert MOT.place(shots, units, total, {"living_s": 30}) is shots

def test_a_paid_clip_runs_on_into_the_stills_that_follow(ladder):
    S_ = [{"type": "kling"}, {"type": "still"}, {"type": "still"}, {"type": "graphic"}, {"type": "still"}]
    b = [0.0, 3.0, 7.0, 9.0, 11.0, 14.0]; merged = set(); MOT.carry(b, S_, {0: 5.0}, merged)
    assert b == [0.0, 5.0, 7.0, 9.0, 11.0, 14.0] and merged == set()                                               # a 5-second clip on a 3-second line: the next still starts two seconds later, when the clip is over
    b = [0.0, 3.0, 5.5, 9.0, 11.0, 14.0]; merged = set(); MOT.carry(b, S_, {0: 4.2}, merged)
    assert b == [0.0, 4.2, 5.5, 9.0, 11.0, 14.0] and merged == set()                                               # the clip is over 1.3 s before the next line: that still starts when the clip ends
    b = [0.0, 3.0, 3.8, 9.0, 11.0, 14.0]; merged = set(); MOT.carry(b, S_, {0: 5.0}, merged)
    assert b == [0.0, 5.0, 5.0, 9.0, 11.0, 14.0] and merged == {1}                                                 # a line the clip covers whole has no picture state of its own
    b = [0.0, 3.0, 5.5, 9.0, 11.0, 14.0]; MOT.carry(b, S_, {2: 6.0}, set()); assert b == [0.0, 3.0, 5.5, 9.0, 11.0, 14.0]      # never into a graphic: the clip is cut where its own line ends
    b = [0.0, 6.0, 9.0]; MOT.carry(b, S_[:2], {0: 5.0}, set()); assert b == [0.0, 6.0, 9.0]                       # a clip shorter than its line changes nothing
    b = [0.0, 3.0, 6.0, 9.0]; MOT.carry(b, [{"type": "kling"}, {"type": "living"}, {"type": "still"}], {0: 5.0, 1: 5.0}, set()); assert b == [0.0, 3.0, 8.0, 9.0]      # never into another clip's line; that clip runs on in its turn

def test_the_still_after_a_clip_keeps_a_second_of_its_own_or_is_covered(ladder):
    S_ = [{"type": "living"}, {"type": "still"}, {"type": "still"}]
    b = [0.0, 3.0, 5.5, 9.0]; merged = set(); MOT.carry(b, S_, {0: 5.0}, merged)
    assert b == [0.0, 5.5, 5.5, 9.0] and merged == {1}                                                            # half a second of a still is a flash: the clip covers the line, and is played that little slower
    assert MOT.NEXT_MIN_S == 1.0 and MOT.plain({"type": "still"}) and not MOT.plain({"type": "still", "promise": True}) and not MOT.plain({"type": "still", "short": {"id": "SH1"}}) and not MOT.plain({"type": "reaction"})

def test_one_rule_cuts_a_line_that_carries_a_clip(ladder):
    assert MOT.cuts(150, 5.0, 30, lambda s: 9) == [0, 150]                                                        # the clip covers the line: ONE picture state (before: the micro-cuts showed its start picture for half of it)
    assert MOT.cuts(160, 5.0, 30, lambda s: 9) == [0, 160]                                                        # a third of a second left: no flash of a still, the clip is played that little slower
    assert MOT.cuts(300, 5.0, 30, lambda s: 2) == [0, 150, 225, 300]                                              # five seconds left: the clip whole, then stills by the rule every still follows
    assert MOT.cuts(90, 5.0, 30, lambda s: 9) == [0, 90] and MOT.cuts(240, 5.0, 30, lambda s: 0) == [0, 150, 240]
    src = inspect.getsource(EP._render); assert "MOT.cuts(" in src and "MOT.carry(bounds, shots, clip_s_, MERGED_UNITS)" in src

def test_a_scene_takes_the_nearest_line_that_can_show_it_whole(ladder, setting):
    units, total = _units([4, 2, 2, 2, 6, 2, 2, 2, 2, 6])
    shots = [{"type": "still"} for _ in units]; shots[3]["type"] = "graphic"                                       # line 2 (2 s) is followed by a graphic: a scene there would lose three of its five seconds
    fit = MOT.scene_fit(shots, units, total); assert [fit(i) for i in (0, 1, 2, 4, 9)] == [True, False, False, True, True]
    free = AN.pick_slots(shots, units, 1, anchors=(0.2,)); strict = AN.pick_slots(shots, units, 1, anchors=(0.2,), fit=fit)
    assert free == [1] and strict == [0]                                                                          # the nearest line that can show the whole scene, not the nearest line
    assert AN.pick_slots(shots, units, 1, anchors=(0.0,), fit=lambda i: i == 9) == [0]                             # the scene at second 0 stays the first picture
    assert AN.pick_slots(shots, units, 1, anchors=(0.2,), fit=lambda i: False) == [1]                             # no line fits: the nearest one, as before

# ------------------------------------------------------------------ 4. the measure: what the finished film really shows
def test_the_finished_film_is_measured_where_a_clip_played(ladder, tmp_path):
    film = _film(str(tmp_path / "film.mp4"), [("move", 5), ("hold", 5), ("move", 4), ("hold", 6)])
    spans = [(0.0, 5.0, "footage"), (5.0, 10.0, "scene"), (10.0, 14.0, "living")]                                 # the second 'clip' ran out and was held: the render says a clip played, the film says nothing moves
    r = MOT.long_report(film, spans, paid_s=9.0)
    assert r["by"] == {"footage": 5.0, "living": 4.0} and r["moving_s"] == 9.0 and r["share_pct"] == 45.0 and r["duration"] == 20.0
    assert r["played_s"] == {"footage": 5.0, "living": 4.0, "scene": 5.0} and len(r["frozen"]) == 8 and {k for _, k in r["frozen"]} == {"scene"}
    assert r["seen_pct"] == pytest.approx(100 * 4.0 / 9.0, abs=0.1)                                               # of the 9 s this video paid for (a scene and a living still) 4 are seen moving; its Short's footage is not its own
    assert MOT.long_report(film, [], paid_s=None)["moving_s"] == 0 and MOT.long_report(film, [(14.0, 20.0, "living")])["moving_s"] == 0      # a held picture never counts, whatever the record says
    assert MOT.long_report(film, [(0.0, 5.0, "scene")], paid_s=5.0)["seen_pct"] == 100.0

def test_check_moving_share_holds_a_film_under_the_floor_or_one_that_shows_less_than_it_paid(ladder, setting, tmp_path):
    film = _film(str(tmp_path / "film.mp4"), [("move", 5), ("hold", 5), ("move", 4), ("hold", 6)])
    ok = {"master": film, "moving": [(0.0, 5.0, "scene"), (10.0, 14.0, "living")], "moving_paid_s": 9.0, "d": {"moving": {"bought_pct": 45.0}}}
    s, ev = CON.p_moving_share(ok); assert s == CON.PASS and "9 of 20 s move = 45%" in ev and "floor 20%" in ev and "this month's money planned 45%" in ev and "100% of the 9 s paid" in ev
    assert ok["d"]["moving_share"]["share_pct"] == 45.0                                                            # the measurement is kept with the video
    s, ev = CON.p_moving_share(dict(ok, moving=[(10.0, 14.0, "living")], moving_paid_s=4.0)); assert s == CON.PASS and "= 20%" in ev      # exactly the floor passes
    s, ev = CON.p_moving_share(dict(ok, moving=[(10.5, 14.0, "living")], moving_paid_s=3.5)); assert s == CON.FAIL and "only 17.5% of the film is moving pictures" in ev
    lost = dict(ok, moving=[(0.0, 5.0, "scene"), (5.0, 10.0, "living")], moving_paid_s=10.0)                       # a living clip that was paid and is not seen moving
    s, ev = CON.p_moving_share(lost); assert s == CON.FAIL and "only 50% are on screen and moving" in ev and "nothing changes at 5 s (living)" in ev
    setting("MOVING_SEEN_MIN_PCT", "50"); assert CON.p_moving_share(lost)[0] == CON.PASS; setting("MOVING_SEEN_MIN_PCT", "90")
    setting("MOVING_SHARE_MIN_LONG", "50"); assert CON.p_moving_share(ok)[0] == CON.FAIL; setting("MOVING_SHARE_MIN_LONG", "20")
    assert CON.p_moving_share(dict(ok, master=str(tmp_path / "gone.mp4")))[0] == CON.FAIL and CON.p_moving_share({"master": film})[0] == CON.NA      # no film = a failure; no render record = not judged here
    setting("MOVING_CHANGE_MIN", "50"); assert CON.p_moving_share(ok)[0] == CON.FAIL; setting("MOVING_CHANGE_MIN", core.DEFAULTS["MOVING_CHANGE_MIN"][0])      # the limit is the cell
    setting("MOTION_LADDER_ON", "FALSE"); s, ev = CON.p_moving_share(ok); assert s == CON.NA and "MOTION_LADDER_ON" in ev

def test_a_short_must_move_in_every_half_second_of_its_file(ladder, setting, tmp_path):
    good = _film(str(tmp_path / "good.mp4"), [("move", 6), ("move", 5)], w=360, h=640)
    r = MOT.short_report(good); assert r["cells"] in (21, 22) and r["moving"] == r["cells"] and r["share_pct"] == 100.0 and r["still"] == []
    s, ev = CON.p_short_moving({"short_file": {"path": good}}); assert s == CON.PASS and f"every one of the {r['cells']} half seconds" in ev
    bad = _film(str(tmp_path / "bad.mp4"), [("move", 6), ("hold", 2), ("move", 3)], w=360, h=640)                  # a clip that came back two seconds short and was held on its last frame
    r = MOT.short_report(bad); assert r["cells"] - r["moving"] >= 3 and all(6.0 <= t < 8.0 for t in r["still"])
    s, ev = CON.p_short_moving({"short_file": {"path": bad}}); assert s == CON.FAIL and "half seconds of the Short do not move" in ev and "nothing changes at 6" in ev
    assert CON.p_short_moving({})[0] == CON.FAIL and CON.p_short_moving({"short_file": {"path": str(tmp_path / "no.mp4")}})[0] == CON.FAIL
    setting("SHORT_CHANGE_MIN", "0"); assert CON.p_short_moving({"short_file": {"path": bad}})[0] == CON.PASS; setting("SHORT_CHANGE_MIN", core.DEFAULTS["SHORT_CHANGE_MIN"][0])      # the limit is the cell
    setting("MOTION_LADDER_ON", "FALSE"); assert CON.p_short_moving({"short_file": {"path": bad}})[0] == CON.NA

def test_the_two_limits_were_set_from_both_kinds_of_pairs(ladder, tmp_path):
    """A measure gets a limit only after pairs known to move AND pairs known to be held were measured (BUILD_STATE, V2c-b2b1's lesson)."""
    seg = RN.clip_segment(MD.fake_clip(str(tmp_path / "c.mp4"), 640, 360, "c", 2), str(tmp_path / "seg.mp4"), 6 * RN.fps())      # a 2-second clip asked to cover 6: played, then held under the renderer's grain
    fr, dur = MOT._read(seg, MOT.REGION); moving = [c for _, c in MOT._cells(fr, 0.0, 2.0, MOT.GAP_LONG)]; held = [c for _, c in MOT._cells(fr, 3.0, dur, MOT.GAP_LONG)]
    lim = core.S("MOVING_CHANGE_MIN", float); assert held and moving and max(held) < lim < min(moving), (held, moving)
    up = _film(str(tmp_path / "s.mp4"), [("move", 3), ("hold", 3)], w=360, h=640); fr, dur = MOT._read(up, MOT.BAND)
    lim = core.S("SHORT_CHANGE_MIN", float); assert max(c for _, c in MOT._cells(fr, 3.5, dur, MOT.GAP_SHORT)) < lim < min(c for _, c in MOT._cells(fr, 0.0, 2.5, MOT.GAP_SHORT))
    assert MOT._quiet([(0.0, 0), (0.5, 9), (1.0, 0), (1.5, 0), (2.0, 9)], 1) == [1.0, 1.5] and MOT.RUN == 2      # one quiet half second is no freeze; a second or more is

def test_an_offline_clip_never_stands_still(tmp_path):
    """Before this batch the offline clip swung and stood still twice in five seconds: no rule about what really moves could be tested on it."""
    c = MD.fake_clip(str(tmp_path / "c.mp4"), 640, 360, "seed", 8); fr, dur = MOT._read(c, MOT.REGION); ch = [x for _, x in MOT._cells(fr, 0.0, dur, MOT.GAP_LONG)]
    assert len(ch) == 16 and min(ch) > 1.5 * core.S("MOVING_CHANGE_MIN", float) and max(ch) < 6 * min(ch) and MD.FAKE_DRIFT_S >= 15                    # one steady speed, for longer than any clip a model sells

def test_check_visual_change_judges_the_picture_states_the_render_showed(ladder, setting):
    units, _ = _units([5, 5, 6]); shots = [{"type": "kling"}, {"type": "still"}, {"type": "still"}]
    ok = [(0.0, 5.0, "kling", True, False), (5.0, 8.0, "still", False, False), (8.0, 11.0, "still", False, False), (11.0, 13.5, "still", False, False), (13.5, 16.0, "still", False, False)]
    assert CON.p_visual_change({"units": units, "shots": shots, "states": ok})[0] == CON.PASS                      # a clip playing five seconds is ONE state and inside its limit
    s, ev = CON.p_visual_change({"units": units, "shots": shots, "states": [(0.0, 5.0, "kling", True, False), (5.0, 10.5, "still", False, False), (10.5, 16.0, "kling", False, False)]})
    assert s == CON.FAIL and "5.5 s as one picture state" in ev                                                   # a still held 5.5 s fails - also the still tail of a clip's line
    s, ev = CON.p_visual_change({"units": units, "shots": shots, "states": [(0.0, 9.0, "living", True, False), (9.0, 12.0, "still", False, False), (12.0, 16.0, "still", False, False)]})
    assert s == CON.FAIL and "a playing clip" in ev                                                               # a clip longer than two picture states may hold
    assert CON.p_visual_change({"units": units, "shots": shots, "states": [(0.0, 9.0, "kling", True, True), (9.0, 12.5, "still", False, False), (12.5, 16.0, "still", False, False)]})[0] == CON.PASS      # the Short's own footage was cut as a Short
    assert MOT.cap_s(CL.row(HEY)) == 8.0                                                                           # ... which is why a still is brought to life for eight seconds at most

def test_check_real_motion_judges_the_scenes_not_the_living_stills(ladder, setting, tmp_path):
    setting("CONTRACT_MEASURE_IN_FAKE", "TRUE")
    mv = MD.fake_clip(str(tmp_path / "m.mp4"), 320, 180, "m", 5); still = _film(str(tmp_path / "h.mp4"), [("hold", 5)])
    assert CON.p_motion({"clips": [mv, still], "scenes": [mv]}) == CON.p_motion({"clips": [mv]}) and CON.p_motion({"clips": [still], "scenes": []})[0] == CON.NA      # a held living clip beside it changes nothing
    assert CON.p_motion({"clips": [mv], "scenes": [still]})[0] == CON.FAIL and CON.p_motion({"clips": [still]})[0] == CON.FAIL      # without the list of scenes: every clip, as before

# ------------------------------------------------------------------ 5. a character is drawn or absent
def _sheets(tmp_path, chars=("VALE", "GRIMM", "ROSA", "ARCHIVIST"), real=True):
    for c in chars:
        f = str(tmp_path / f"{c}.png")
        if real: MD.fake_image(f, 320, 180, c)
        core.store().append("Character_Sheets", [{"ts": "t", "character": c, "expression": "neutral", "hash": c, "prompt": "", "file": f, "status": "LOCKED", "approved_at": "t"}])

def test_a_cutaway_of_a_character_is_planned_only_with_approved_art(ladder, setting, tmp_path):
    units = [{"i": 0, "start": 0, "end": 4, "text": "A long line about the pillows over the city tonight.", "speaker": "DIRECTOR", "tag": "none"},
             {"i": 1, "start": 4, "end": 5, "text": "Fine.", "speaker": "SKEPTIC", "tag": "none"}, {"i": 2, "start": 5, "end": 6, "text": "A fifth.", "speaker": "JUDGE", "tag": "none"}]
    mk = lambda: [{"type": "still", "prompt": u["text"]} for u in units]
    assert LV.has_art("SKEPTIC") is False and SPL.reaction_shots(mk(), units)[1] == 0                              # no approved art: nobody is shown
    _sheets(tmp_path, ("GRIMM",)); out, n = SPL.reaction_shots(mk(), units)
    assert LV.has_art("SKEPTIC") and not LV.has_art("JUDGE") and n == 1 and [s["type"] for s in out] == ["still", "reaction", "still"]      # only the character that is drawn
    setting("LIVING_CHARACTERS_ON", "FALSE"); assert LV.has_art("SKEPTIC") is False and SPL.reaction_shots(mk(), units)[1] == 0

def test_check_living_characters_passes_drawn_or_absent_and_nothing_else(ladder, setting, tmp_path):
    react = [{"type": "still"}, {"type": "reaction", "speaker": "SKEPTIC"}, {"type": "reaction", "speaker": "JUDGE"}]
    s, ev = CON.p_living({"shots": [{"type": "still"}], "absent": 0}); assert s == CON.PASS and "nobody is on screen" in ev      # absent passes, in every format
    s, ev = CON.p_living({"shots": react, "absent": 0}); assert s == CON.FAIL and "JUDGE, SKEPTIC" in ev and "without approved character art" in ev
    _sheets(tmp_path, ("GRIMM", "ROSA")); s, ev = CON.p_living({"shots": react, "absent": 0}); assert s == CON.PASS and "2 reaction cutaways, each the approved character" in ev
    s, ev = CON.p_living({"shots": react, "absent": 1}); assert s == CON.FAIL and "1 of 2 reaction cutaways could not show the approved character" in ev      # the art was gone at render time: the picture before continued
    from whatifs import formats as FMT
    assert all(FMT.rule("living_characters", f) == "must" for f in ("F1", "F2", "F3")) and "living_characters" not in FMT.DEVICES      # no format can make it optional
    setting("LIVING_CHARACTERS_ON", "FALSE"); s, ev = CON.p_living({"shots": react, "absent": 0}); assert s == CON.FAIL       # switched off, a planned cutaway has no art to show: never 'not applicable'

def test_no_prompt_asks_for_a_silhouette_and_the_rule_cannot_come_back(ladder):
    assert "silhouette" not in inspect.getsource(FE).lower()                                                      # the format engine told three roles to show presenters as silhouettes
    assert "A PRESENTER IS DRAWN OR ABSENT" in inspect.getsource(FE) and "presenter silhouettes" not in open(os.path.join(ROOT, "whatifs", "qc.py"), encoding="utf-8").read()
    rule = next(r for r in TR.RETIRED if r["id"] == "presenter_silhouette"); import re
    assert re.search(rule["pattern"], "Show the roles only as silhouettes, hands on a console.") and re.search(rule["pattern"], "the cutaway fell back to a silhouette")
    assert re.search(rule["pattern"], "NO realistic faces (silhouette, hands, back of head)") and not re.search(rule["pattern"], "Big readable silhouettes. Cinematic noir lighting.") and not re.search(rule["pattern"], "never fully seen: a silhouette behind shelves")      # the art direction and the canon keep the word

# ------------------------------------------------------------------ 6. real footage: a short anchor with a record
def test_the_stock_rules_on_the_shot_list(ladder, setting):
    units, total = _units([3, 3, 3, 6, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])                           # 60 s: a tenth = 6 s
    def run(idx):
        shots = [{"type": "still", "prompt": f"p{i}"} for i in range(len(units))]
        for i in idx: shots[i] = {"type": "stock", "search": "ocean waves", "prompt": f"p{i}"}
        return STK.shape(shots, units, total)
    out = run([0, 1, 2, 3, 4, 6, 8, 12]); kept = [i for i, s in enumerate(out) if s["type"] == "stock"]
    assert kept == [1, 4] and [out[i]["stock_s"] for i in kept] == [3.0, 3.0]
    # 0: never the first picture | 2: never two in a row | 3: a line of 6 s is no anchor | 6: a line of 1 s is a flash | 8, 12: a tenth of the film at most (the earliest stay)
    assert all(out[i]["type"] == "still" and out[i]["prompt"] == f"p{i}" and "search" not in out[i] for i in (0, 2, 3, 6, 8, 12))
    assert [i for i, s in enumerate(run([2, 4])) if s["type"] == "stock"] == [2, 4] and run([5]) != [] and run([])[0]["type"] == "still"
    setting("STOCK_SHARE_MAX_PCT", "5"); assert [i for i, s in enumerate(run([1, 4])) if s["type"] == "stock"] == [1]; setting("STOCK_SHARE_MAX_PCT", "10")
    setting("STOCK_MAX_S", "6"); assert 3 in [i for i, s in enumerate(run([3])) if s["type"] == "stock"]; setting("STOCK_MAX_S", "4")
    setting("STOCK_ON", "FALSE"); assert [s["type"] for s in run([1, 4])].count("stock") == 0                     # switched off: none stays
    shots = [{"type": "still"}, {"type": "stock", "search": "x"}]; STK.shape(shots, units[:2], 6.0); assert shots[1]["type"] == "stock"      # the input is not changed
    assert "STK.shape(shots, units, vo.duration)" in inspect.getsource(EP.produce)

def test_a_clip_whose_own_title_names_a_person_is_recognised(ladder):
    for t in ("Astronaut on a spacewalk outside the station", "a-man-walking-on-the-beach-854321", "Crew interview before launch", "people crossing a street", "Portrait of Dr. Smith", "kids playing"):
        assert STK.names_person(t), t
    for t in ("Ocean waves at sunset", "moon-surface-flyover-12", "Saturn's rings in infrared", "lava flowing into the sea", "humanity's home planet", "manhattan skyline at night", "a personal best: storm clouds"):
        assert not STK.names_person(t), t

def test_offline_a_clip_of_real_footage_comes_with_its_record(ladder, tmp_path):
    p = MD.stock("ocean waves", str(tmp_path / "s.mp4"), "EPS1"); rec = STK.record_of(p)
    assert rec["provider"] == "nasa" and rec["credit"] == "NASA" and rec["id"].startswith("offline-") and rec["people"] is False and STK.record_issues(rec) == []
    assert STK.record_of(str(tmp_path / "none.mp4")) == {} and "no source on record" in STK.record_issues({}) and "no credit on record" in STK.record_issues({"provider": "x", "id": "1"})
    assert STK.record_issues(dict(rec, title="astronaut waves")) == ["its title names a person ('astronaut waves')"] and STK.record_issues(dict(rec, people=True))

class _Resp:
    def __init__(self, j): self._j = j
    def json(self): return self._j

def _net(monkeypatch, tmp_path, nasa=(), pexels=(), key="k", secs=None):
    """The two libraries with the network replaced: what was asked, and a clip of a chosen length 'downloaded' per address."""
    asked = []
    def get(url, params=None, headers=None, timeout=0):
        asked.append((url, dict(params or {})))
        if "images-api.nasa.gov" in url: return _Resp({"collection": {"items": [{"href": f"https://n/{i}", "data": [d]} for i, d in enumerate(nasa)]}})
        if url.startswith("https://n/"): return _Resp([f"http://files/{url.rsplit('/', 1)[1]}~medium.mp4"])
        if "api.pexels.com" in url: return _Resp({"videos": list(pexels)})
        raise AssertionError(url)
    def dl(url, path):
        n = (secs or {}).get(url.rsplit("/", 1)[-1].split("~")[0], 6)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration={n}", "-b:v", "3M", "-pix_fmt", "yuv420p", path], check=True); return path
    monkeypatch.setattr(MD, "FAKE", False); monkeypatch.setattr(MD.requests, "get", get); monkeypatch.setattr(MD, "_dl", dl); monkeypatch.setattr(MD, "env", lambda k: key if k == "PEXELS_KEY" else "")
    return asked

def test_nasa_footage_is_taken_only_without_a_person_and_long_enough(ladder, monkeypatch, tmp_path):
    nasa = [{"nasa_id": "a1", "title": "Astronaut waves from the cupola", "keywords": ["ISS"]}, {"nasa_id": "b2", "title": "Earth at night", "keywords": ["crew", "Earth"]},
            {"nasa_id": "c3", "title": "Aurora over the pole", "keywords": ["aurora"], "description": "Seen from orbit."}, {"nasa_id": "d4", "title": "Storm from orbit", "keywords": [], "center": "JSC"}]
    asked = _net(monkeypatch, tmp_path, nasa=nasa, secs={"2": 2, "3": 6}); p = MD.stock("earth from orbit", str(tmp_path / "s.mp4"), "EPS2", need_s=3.5)
    rec = STK.record_of(p); assert (rec["provider"], rec["id"], rec["credit"], rec["maker"], rec["title"]) == ("nasa", "d4", "NASA", "JSC", "Storm from orbit")
    # a1: its title names a person | b2: its key words do | c3: 2 seconds, shorter than the line it must cover | d4: taken
    assert rec["page"] == "https://images.nasa.gov/details/d4" and rec["people"] is False and rec["seconds"] >= 3.5 and not any("pexels" in u for u, _ in asked)

def test_pexels_footage_is_taken_only_without_a_person_and_is_credited_to_its_maker(ladder, monkeypatch, tmp_path):
    vid = lambda i, slug, dur, who: {"id": i, "url": f"https://www.pexels.com/video/{slug}-{i}/", "duration": dur, "user": {"name": who}, "video_files": [{"width": 1920, "link": f"https://files/{i}"}, {"width": 640, "link": "https://files/small"}]}
    px = [vid(11, "a-woman-looking-at-the-sea", 12, "A"), vid(12, "ocean-waves", 2, "B"), vid(13, "ocean-waves-from-above", 9, "Cara Lens")]
    asked = _net(monkeypatch, tmp_path, pexels=px); p = MD.stock("ocean waves", str(tmp_path / "s.mp4"), "EPS3", need_s=3.0); rec = STK.record_of(p)
    assert (rec["provider"], rec["id"], rec["maker"], rec["credit"]) == ("pexels", "13", "Cara Lens", "Video by Cara Lens on Pexels") and rec["page"].endswith("ocean-waves-from-above-13/")
    q = next(pm for u, pm in asked if "pexels" in u); assert q["orientation"] == "landscape" and q["query"] == "ocean waves" and asked[0][0].startswith("https://images-api.nasa.gov")      # NASA first, then Pexels
    _net(monkeypatch, tmp_path, pexels=px[:2]); assert MD.stock("ocean waves", str(tmp_path / "t.mp4"), "EPS4", need_s=3.0) is None      # nothing fits: no clip (the line keeps a picture of our own)
    _net(monkeypatch, tmp_path, pexels=px, key=""); assert MD.stock("ocean waves", str(tmp_path / "u.mp4"), "EPS5", need_s=3.0) is None      # no key: Pexels is not asked

def test_the_credits_of_a_description_are_built_by_code(ladder):
    n = {"provider": "nasa", "id": "d4", "credit": "NASA"}; a = {"provider": "pexels", "id": "13", "maker": "Cara Lens", "credit": "Video by Cara Lens on Pexels"}; b = dict(a, id="14", maker="Bo")
    assert STK.credits([]) == "" and STK.credits([None, {}]) == ""
    assert STK.credits([n]) == "Real footage: NASA." and STK.credits([a, n, b, a]) == "Real footage: NASA; Pexels (https://www.pexels.com) - videos by Cara Lens, Bo."
    assert STK.credit_names(n) == ["NASA"] and STK.credit_names(a) == ["Pexels", "Cara Lens"]
    d = EP._description("Hook line.\n\nChapters", [("0:00", "A"), ("1:00", "B"), ("2:00", "C")], {"spine": {"premise": "p"}}, "EPD", None, credits=STK.credits([n]))
    assert "\n\nReal footage: NASA.\n\nThis video uses AI-assisted" in d and "Real footage" not in EP._description("Hook.", [], {"spine": {}}, "EPD")

def test_check_stock_share_judges_what_the_film_showed(ladder, setting):
    n = {"provider": "nasa", "id": "d4", "title": "Storm from orbit", "credit": "NASA", "people": False}; desc = "Hook.\n\nReal footage: NASA."
    ok = {"shots": [], "timeline": {"duration": 100.0}, "stock": {"spans": [(10.0, 13.0, 4), (40.0, 44.0, 9)], "records": {4: n, 9: n}, "description": desc}}
    s, ev = CON.p_stock_share(ok); assert s == CON.PASS and "2 clip(s) of real footage, 7 s = 7% of the film (limit 10%)" in ev and "credited: NASA" in ev
    def bad(**k): return CON.p_stock_share(dict(ok, stock=dict(ok["stock"], **k)))
    s, ev = bad(spans=[(10.0, 14.0, 4), (40.0, 44.0, 9), (60.0, 64.0, 12)], records={4: n, 9: n, 12: n}); assert s == CON.FAIL and "12.0% of the film (limit 10%)" in ev
    s, ev = bad(spans=[(0.0, 3.0, 0)], records={0: n}); assert s == CON.FAIL and "OPENS on real footage" in ev
    s, ev = bad(spans=[(10.0, 13.0, 4), (13.0, 16.0, 5)], records={4: n, 5: n}); assert s == CON.FAIL and "two shots of real footage in a row" in ev
    s, ev = bad(spans=[(10.0, 16.5, 4)], records={4: n}); assert s == CON.FAIL and "held longer than an anchor" in ev
    s, ev = bad(records={4: n}); assert s == CON.FAIL and "the footage of shot 9: no source on record" in ev
    s, ev = bad(records={4: n, 9: dict(n, title="Astronaut at the window")}); assert s == CON.FAIL and "its title names a person" in ev
    s, ev = bad(description="Hook."); assert s == CON.FAIL and "does not credit NASA" in ev
    px = {"provider": "pexels", "id": "13", "maker": "Cara Lens", "credit": "Video by Cara Lens on Pexels", "title": "ocean-waves"}
    s, ev = bad(records={4: n, 9: px}); assert s == CON.FAIL and "does not credit Pexels, Cara Lens" in ev
    assert bad(records={4: n, 9: px}, description=desc + " " + STK.credits([px]))[0] == CON.PASS
    assert bad(records={"4": n, "9": n})[0] == CON.PASS                                                           # a record restored from a checkpoint is keyed by a word
    s, ev = bad(spans=[], records={}); assert s == CON.PASS and ev == "no real footage in this video"             # allowed, never demanded
    assert CON.p_stock_share({"shots": []})[0] == CON.NA
    setting("STOCK_ON", "FALSE"); s, ev = CON.p_stock_share(ok); assert s == CON.FAIL and "switched off" in ev

def test_the_renderer_changes_real_footage_and_never_loops_it(ladder, tmp_path):
    src = str(tmp_path / "src.mp4"); subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=3", "-pix_fmt", "yuv420p", src], check=True)
    fps = RN.fps(); plain = RN.clip_segment(src, str(tmp_path / "plain.mp4"), 3 * fps, loop=True); st = RN.clip_segment(src, str(tmp_path / "stock.mp4"), 3 * fps, stock=True)
    import cv2
    def frame(p, t):
        cap = cv2.VideoCapture(p); cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * (cap.get(cv2.CAP_PROP_FPS) or 30))); ok, f = cap.read(); cap.release(); assert ok; return f
    a = OPEN.alike(frame(plain, 2.0), frame(src, 2.0)); b = OPEN.alike(frame(st, 2.0), frame(src, 2.0))
    assert a > 0.8 and b < a - 0.1, (a, b)                                                                        # cropped in and slowed: at the same second the film no longer shows the file's own picture
    assert RN.STOCK_CROP > 1.05 and RN.STOCK_SLOW > 1.05
    long_ = RN.clip_segment(src, str(tmp_path / "long.mp4"), 6 * fps, stock=True); fr, dur = MOT._read(long_, MOT.REGION)      # a clip that runs out is HELD, never started again
    assert max(c for _, c in MOT._cells(fr, 4.0, dur, MOT.GAP_LONG)) < core.S("MOVING_CHANGE_MIN", float) < min(c for _, c in MOT._cells(fr, 0.0, 3.0, MOT.GAP_LONG))
    src_ = inspect.getsource(EP._render); assert 'RN.clip_segment(files["clips"][i], path, nf, stock=True)' in src_

# ------------------------------------------------------------------ 7. a Short sounds from its first frame
def _mixed(tmp_path, bed, name, voice_at=0.35):
    mix = SP._mix(bed, [(_voice(str(tmp_path / f"{name}_v.wav"), voice_at), 0.0)], str(tmp_path / f"{name}_mix.wav"))
    return _film(str(tmp_path / f"{name}.mp4"), [("move", 6)], w=360, h=640, audio=mix)

def test_the_sound_under_a_short_is_its_places_own_from_the_first_sample(ladder, tmp_path):
    import soundfile as sf
    p, kind = SD.short_bed(6.0, [2, 2, 2], "rain on your window tonight", "SHA", str(tmp_path / "a.wav")); a, sr = sf.read(p)
    assert kind == "rain" and a.shape == (6 * sr, 2) and float(np.abs(a).max()) <= 0.9 and float(np.sqrt(np.mean(a[:sr // 100] ** 2))) > 0.02      # it sounds inside the first hundredth of a second
    assert SD.short_bed(6.0, [2, 2, 2], "your shadow on the wall", "SHA", str(tmp_path / "b.wav"))[1] in ("rumble", "hum", "wind")       # nothing obvious in the words: one of three, by the Short's id
    q, _ = SD.short_bed(6.0, [2, 2, 2], "rain on your window tonight", "SHB", str(tmp_path / "c.wav")); b, _ = sf.read(q)
    r, _ = SD.short_bed(6.0, [2, 2, 2], "rain on your window tonight", "SHA", str(tmp_path / "d.wav")); c, _ = sf.read(r)
    assert np.array_equal(a, c) and not np.array_equal(a, b)                                                      # one id, one sound; another Short, another colour

def test_check_short_sound_passes_the_new_bed_and_fails_the_older_drone(ladder, setting, tmp_path):
    units = [{"start": 0.35, "end": 2.0, "text": "Tonight your shadow is late.", "words": [{"w": "Tonight", "s": 0.35, "e": 0.7}]}]
    new = _mixed(tmp_path, SD.short_bed(6.0, [2, 2, 2], "rain on your window", "SHS1", str(tmp_path / "new.wav"))[0], "new")
    m = SD.first_second(new); assert m["onset_s"] is not None and m["onset_s"] <= 0.05 and m["db_200"] > -40 and m["peak_db"] < -0.1
    s, ev = CON.p_short_sound({"short_file": {"path": new, "units": units, "sound": "rain"}}); assert s == CON.PASS and "sound from 0 s" in ev and "the guide speaks from 0.35 s" in ev and "rain" in ev
    old = _mixed(tmp_path, SP._sound(6.0, [2, 2, 2], str(tmp_path / "old.wav")), "old")                            # the sound a Short had before: a low thump under a drone that rises out of silence
    o = SD.first_second(old); w = SD.first_second(old, phone=False)
    assert o["db_200"] < -50 and w["db_200"] > -40                                                                # loud on a studio speaker, silent on a phone until the voice starts
    s, ev = CON.p_short_sound({"short_file": {"path": old, "units": units}}); assert s == CON.FAIL and ("the first sound comes at" in ev or "silent" in ev)
    s, ev = CON.p_short_sound({"short_file": {"path": new, "units": [dict(units[0], start=1.6, words=[{"w": "Tonight", "s": 1.6, "e": 1.9}])]}}); assert s == CON.FAIL and "the guide's first word starts at 1.6 s" in ev
    s, ev = CON.p_short_sound({"short_file": {"path": new, "units": []}}); assert s == CON.FAIL and "no voice timeline" in ev
    silent = _film(str(tmp_path / "silent.mp4"), [("move", 3)], w=360, h=640); assert CON.p_short_sound({"short_file": {"path": silent, "units": units}})[0] == CON.FAIL
    setting("SHORT_SOUND_MIN_DB", "-10"); s, ev = CON.p_short_sound({"short_file": {"path": new, "units": units}}); assert s == CON.FAIL and "it fades in" in ev; setting("SHORT_SOUND_MIN_DB", "-40")
    assert CON.p_short_sound({})[0] == CON.FAIL
    setting("MOTION_LADDER_ON", "FALSE"); assert CON.p_short_sound({"short_file": {"path": old, "units": units}})[0] == CON.NA

def test_a_phone_plays_nothing_under_400_hz_and_the_measure_hears_like_one(ladder, tmp_path):
    import soundfile as sf
    sr = 48000; t = np.arange(2 * sr) / sr
    for hz, heard in ((80, False), (1000, True)):
        p = str(tmp_path / f"{hz}.wav"); sf.write(p, (0.5 * np.sin(2 * np.pi * hz * t) * np.minimum(1, t / 0.05)).astype(np.float32), sr)      # 50 ms in: no click at the first sample
        m = SD.first_second(p); assert (m["onset_s"] is not None) is heard and SD.first_second(p, phone=False)["onset_s"] <= 0.02, (hz, m)
    assert SD.PHONE_HZ == 400

# ------------------------------------------------------------------ 8. whole productions
def _runs(ep): return [(s["dept"], s["trigger"], s["status"]) for s in core.store().rows("Sessions") if s.get("episode_id") == ep]
def _led(ep): return {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}
def _summary(ep):
    row = next(x for x in core.store().rows("Cost_Log") if x["episode_id"] == ep and x["item"] == "cost_lines_summary"); return json.loads(str(row["role"]).partition(": ")[2]), row

def test_a_whole_long_video_moves_as_it_paid_shows_its_stock_under_the_rules_and_draws_its_cast(ladder, setting, monkeypatch, tmp_path):
    from tools.sweep import climb, motion_of, money_of
    from tests import test_v12_opening_e2e as E2E
    E2E._start(monkeypatch, setting); A, B, sid = OWN_IDS[:3]; _sheets(tmp_path)
    setting("STOCK_MIN_S", "0.5"); setting("STOCK_MAX_S", "30"); setting("STOCK_SHARE_MAX_PCT", "20")             # the offline lines are short and few: wide rules, so that real footage STAYS in this film and the path is walked
    assert climb(core, A) is True; c = watch(monkeypatch); r = EP.produce(E2E._slot(10), episode_id=A); a = dict(c); assert r.get("ok"), r
    led = _led(A); out, S_, units = E2E._plan(A); d = S_["d"]; plan = S_["plan"]; shots = json.load(open(os.path.join(out, "plan.json"), encoding="utf-8"))["shots"]
    assert led["moving_share"][0] == "PASS" and led["stock_share"][0] == "PASS" and led["living_characters"][0] == "PASS" and led["visual_change"][0] == "PASS", {k: led[k] for k in ("moving_share", "stock_share", "living_characters", "visual_change")}
    j, row = _summary(A); assert j["unlisted"] == [] and j["over"] == [] and row["role"].startswith("ladder: ")   # THE MONEY: every living second had its line and none was paid beyond the plan
    assert d["living_s"] >= G.moving_floor("ladder", d["runtime_sec"])["living_s"] and j["lines"]["living_clip"] == d["living_s"] and 0 < j["paid"]["living_clip"] <= d["living_s"]
    assert j["paid"]["hero_clip"] == 15 == j["lines"]["hero_clip"] and a["clip"] <= next(l for l in CG.lines("ladder", living_s=d["living_s"]) if l["key"] == "living_clips")["calls"]["clip"]
    ok, words = money_of(core, [A, sid]); assert ok, words
    ok, words = motion_of(core, A, [sid]); assert ok and words.startswith("the ladder's rules held: ") and "s move =" in words, words
    assert "real footage" in led["stock_share"][1] and ("credited: NASA" in led["stock_share"][1] or led["stock_share"][1] == "no real footage in this video")
    if "credited: NASA" in led["stock_share"][1]:
        e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == A); assert glob_stock(out) and "Real footage: NASA." in open_desc(A)
    assert _led(sid)["short_moving"][0] == "PASS" and _led(sid)["short_sound"][0] == "PASS" and ("D8", "short_file_gate", "ok") in _runs(sid)
    for i in OWN_IDS: shutil.rmtree(os.path.join(core.WORK, i), ignore_errors=True)                                # GitHub runs every test file in ONE process with one work folder: leave nothing behind

def glob_stock(out):
    import glob
    return [p for p in glob.glob(os.path.join(out, "clip*.mp4.json")) if STK.record_of(p[:-5]).get("credit") == "NASA"]

def open_desc(ep):
    """The description the upload was given (the offline platform keeps what it was sent)."""
    import glob
    for p in glob.glob(os.path.join(core.WORK, "_platform", "**", "*.json"), recursive=True):
        try: t = open(p, encoding="utf-8").read()
        except OSError: continue
        if "Real footage" in t: return t
    return ""

def test_a_whole_long_video_whose_cast_art_is_gone_shows_nobody_and_is_held(ladder, setting, monkeypatch, tmp_path):
    from tools.sweep import climb
    from tests import test_v12_opening_e2e as E2E
    E2E._start(monkeypatch, setting); B = OWN_IDS[1]; LAD.override("owner", "make it anyway")                      # under an override: it opens on its own pictures
    _sheets(tmp_path, real=False)                                                                                 # the art is APPROVED on the Sheet - and its files are gone when the film is rendered
    r = EP.produce(E2E._slot(10), episode_id=B); led = _led(B); out, S_, units = E2E._plan(B)
    n_react = sum(1 for s in S_["shots"] if s.get("type") == "reaction")
    if n_react:
        assert r.get("held") and led["living_characters"][0] == "FAIL" and f"of {n_react} reaction cutaways could not show the approved character" in led["living_characters"][1], (r, led["living_characters"])
        assert "contract:living_characters" in r["problems"]
    else: assert led["living_characters"] == ("PASS", "nobody is on screen: no cutaway of a character was made (a character without approved art is absent, never a shape)")
    assert led["moving_share"][0] == "PASS" and "footage" not in led["moving_share"][1] and "scene" in led["moving_share"][1]      # a video under an override: its own scenes and living stills, no footage
    shutil.rmtree(os.path.join(core.WORK, B), ignore_errors=True)

def test_a_whole_short_passes_the_gate_of_its_file_and_one_with_a_held_second_waits_for_the_owner(ladder, setting, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    q2(monkeypatch); _bench("What if the Moon left tonight?", "What if gravity doubled for one hour?", "What if the Sun went out?"); setting("SHORTS_REVIEW_FIRST_N", "0")
    good, bad, again = OWN_IDS[2:5]
    r = SH.run(force=True, publish=True, now=DEC, episode_id=good); assert r.get("ok") and r["status"] == "POSTED", r
    assert _runs(good)[:6] == [("D14", "write", "ok"), ("D7", "short_voice", "ok"), ("D13", "short_seat", "ok"), ("D8", "short_gate", "ok"), ("D14", "make", "ok"), ("D8", "short_file_gate", "ok")]
    led = _led(good); assert led["short_moving"][0] == led["short_sound"][0] == "PASS" and "sound from 0" in led["short_sound"][1], led
    real = MD.fake_clip
    monkeypatch.setattr(MD, "fake_clip", lambda path, w, h, seed, sec=5: real(path, w, h, seed, max(1, sec - 2)))      # the model returns every clip two seconds shorter than it was bought
    r2 = SH.run(force=True, publish=True, now=DEC + dt.timedelta(days=3), episode_id=bad); row = next(x for x in core.store().rows("Specials") if x["id"] == bad)
    assert r2.get("ok") and row["made"] and row["status"] == "AWAITING_APPROVAL" and not row.get("yt_id") and REL.records(bad) == [], (r2, row)      # MADE, kept - and not handed to Publishing
    led2 = _led(bad); assert led2["short_moving"][0] == "FAIL" and "do not move" in led2["short_moving"][1] and "release_sheet" not in led2
    msg = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "special_review" and bad in str(x)]; assert len(msg) == 1 and "HELD" in msg[0]["text"] and "short_moving" in msg[0]["text"]
    memo = MEM.find(type="problem_memo", stage="short_file"); assert len(memo) == 1 and memo[0]["to_depts"] == ["D6"] and memo[0]["body"]["check"] == "short_moving"
    assert LAD.row(bad) and SH._made(row) and SH.made_this_month(DEC + dt.timedelta(days=4)) == 2                 # it was paid: it counts as made, and the cadence does not pay for it again
    said = SP.approve(bad); row = next(x for x in core.store().rows("Specials") if x["id"] == bad); assert str(said).startswith("posted") and row["status"] == "POSTED" and row["yt_id"], said      # his one tap sends it out through the same door
    monkeypatch.setattr(MD, "fake_clip", real)
    r3 = SH.run(force=True, publish=False, now=DEC + dt.timedelta(days=6), episode_id=again); assert r3.get("ok") and _led(again)["short_moving"][0] == "PASS"
    assert MEM.find(type="problem_memo", stage="short_file") == []                                                # the next Short whose file passes closes the memo
    for i in OWN_IDS: shutil.rmtree(os.path.join(core.WORK, i), ignore_errors=True)

def test_a_held_short_that_is_not_published_says_so_on_its_record(ladder, setting, monkeypatch):
    gf = {"ok": False, "failed": [("short_sound", "the first sound comes at 0.4 s")]}; core.store().append("Specials", [{"ts": core.iso(), "id": "SHX1", "kind": "short", "status": "MADE", "made": core.iso()}])
    upd = SH._file_hold({"id": "SHX1"}, gf, publish=False); assert upd == {"status": "FILE_HELD (short_sound)"} and next(x for x in core.store().rows("Specials") if x["id"] == "SHX1")["status"] == "FILE_HELD (short_sound)"
    assert not [x for x in core.store().rows("Owner_Actions") if "SHX1" in str(x)]

def test_the_whole_production_ids_of_this_file_are_used_by_no_other_test_file():
    import glob
    for f in glob.glob(os.path.join(ROOT, "tests", "*.py")):
        if os.path.basename(f) == os.path.basename(__file__): continue
        src = open(f, encoding="utf-8").read(); assert not [i for i in OWN_IDS if i in src], (os.path.basename(f), OWN_IDS)

# ------------------------------------------------------------------ 9. wiring
def test_the_sweep_makes_an_id_bad_when_a_rule_was_not_walked(ladder):
    from tools import sweep as SW
    def row(ep, f, st="PASS", ev="e"): return {"ts": core.iso(), "episode_id": ep, "stage": "final", "feature": f, "status": st, "evidence": ev}
    core.store().append("Feature_Ledger", [row("EPA", "moving_share", ev="9 of 20 s move = 45%"), row("EPA", "stock_share"), row("EPA", "living_characters"), row("SHA", "short_moving"), row("SHA", "short_sound")])
    ok, words = SW.motion_of(core, "EPA", ["SHA"]); assert ok and words.startswith("the ladder's rules held: 9 of 20 s move = 45%")
    assert SW.motion_of(core, None, ["SHA"])[0] is True
    core.store().append("Feature_Ledger", [row("EPB", "moving_share", CON.NA, "switched off"), row("EPB", "stock_share"), row("EPB", "living_characters")])
    ok, words = SW.motion_of(core, "EPB", []); assert ok is False and "EPB moving_share N/A" in words            # 'not applicable' = the new path was not walked
    ok, words = SW.motion_of(core, "EPA", ["SHZ"]); assert ok is False and "SHZ short_moving missing" in words and "SHZ short_sound missing" in words
    s = SW.summary([{"id": "EPA", "outcome": "ok", "motion": "the ladder's rules held: x"}, {"id": "EPB", "outcome": "odd", "motion": "EPB moving_share N/A"}]); assert s["ladder_rules_held"] == 1
    src = inspect.getsource(SW.one); assert src.count("motion_of(core") == 2 and 'res["outcome"] = "odd"; res["problems"].append("the ladder\'s rules: "' in src

def test_the_batch_is_wired_protected_and_documented():
    prot = open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read()
    assert '"whatifs/motion.py"' in prot and '"whatifs/stock.py"' in prot and {"whatifs/motion.py", "whatifs/stock.py"} <= set(REG.DEPTS["D6"]["wraps"])
    stage = {f[0]: f[1] for f in CON.FEATURES}; assert len(stage) == len(CON.FEATURES) == 64
    assert (stage["moving_share"], stage["stock_share"], stage["short_moving"], stage["short_sound"], stage["living_characters"]) == ("final", "final", "short_file", "short_file", "final")
    assert [REG.check_owner(k) for k in ("moving_share", "stock_share", "short_moving", "short_sound")] == ["D6", "D6", "D6", "D7"]
    assert RND.SHOW_CHECKS == 53 and all(k not in RND.ORG_CHECKS and k in RND.metrics() for k in ("moving_share", "stock_share", "short_moving", "short_sound"))
    assert REG.GATE_RUNS["short_file"] == ("D8", "short_file_gate") and ("whatifs/shorts2.py", "short_file_gate") in REG.ENTRY["D8"] and REG.EPISODE_RUNS["short_file"][-1] == ("D14", "make")
    for k, dept, owner, checks in (("MOVING_SHARE_LONG", "D6", "", ("moving_share",)), ("MOVING_SHARE_MIN_LONG", "D6", "down", ("moving_share",)), ("STOCK_SHARE_MAX_PCT", "D6", "up", ("stock_share",)),
                                   ("SHORT_SOUND_BY_S", "D7", "up", ("short_sound",))):
        assert REG.may_change(dept, k) and LEV.LEVERS[k]["owner"] == owner and LEV.LEVERS[k]["checks"] == checks, k
    for k in ("MOTION_LADDER_ON", "MOVING_SHARE_LONG", "MOVING_SHARE_MIN_LONG", "MOVING_SEEN_MIN_PCT", "MOVING_CHANGE_MIN", "SHORT_CHANGE_MIN", "STOCK_ON", "STOCK_SHARE_MAX_PCT", "STOCK_MIN_S", "STOCK_MAX_S",
              "SHORT_SOUND_BY_S", "SHORT_SOUND_MIN_DB", "SHORT_VOICE_BY_S", "V12V2DB_MOVE_DONE"):
        assert k in core.DEFAULTS and core.DEFAULTS[k][1], k
    assert OLD_MOTION["MOTION_LADDER_ON"] == "FALSE" and core.DEFAULTS["MOTION_LADDER_ON"][0] == core.DEFAULTS["STOCK_ON"][0] == "TRUE" and core.DEFAULTS["FAL_LIVING_MODEL"][0] == HEY
    assert any(r["id"] == "presenter_silhouette" for r in TR.RETIRED) and not TR.issues()
    mx = open(os.path.join(ROOT, "docs", "CURRENT", "ENFORCEMENT_MATRIX.md"), encoding="utf-8").read()
    for ref in ("contract:moving_share", "contract:stock_share", "contract:short_moving", "contract:short_sound", "fn:whatifs.motion.place", "fn:whatifs.motion.carry", "fn:whatifs.motion.long_report",
                "fn:whatifs.governor.moving_plan", "fn:whatifs.clips.living", "fn:whatifs.stock.shape", "fn:whatifs.sound.short_bed", "fn:whatifs.shorts2._file_hold"): assert ref in mx, ref

def test_with_the_ladder_switched_off_a_short_sounds_and_is_gated_as_before(setting, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    q2(monkeypatch); _bench("What if the Moon left tonight?"); assert not MOT.on()                                # the older tests' cells (tests/conftest.py)
    r = SH.run(force=True, publish=False, now=DEC, episode_id="SHOFF1"); assert r.get("ok")
    assert ("D8", "short_file_gate", "ok") not in _runs("SHOFF1") and "short_moving" not in _led("SHOFF1")
    shutil.rmtree(os.path.join(core.WORK, "SHOFF1"), ignore_errors=True)
