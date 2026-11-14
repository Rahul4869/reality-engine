"""v12 V2c-b2b2 THE CUT-DOWNS: a long video makes no cut-down reels, its release is one step, an upright video reaches a platform through ONE door,
the older tracks are paused by default, a live Sheet is moved once, and the truth registry refuses the old words. Each rule both ways. No keys, no network."""
import datetime as dt, json, os, shutil
import pytest
from whatifs import core, manage as MG, publish as PUB, contract as CON, truth as TRU, governor as G, sampler as SAM, playbook as PB, pilots as PL, specials as SP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GONE_CELLS = ("REELS_PER_VIDEO", "REEL_STYLE", "REEL1_SHORTS_ON", "REEL2_DELAY_MIN", "REEL3_DELAY_MIN", "REEL4_DELAY_MIN", "KINETIC_CAPTIONS_ON", "TRIAL_SHORTS_SAFE_ON")
DOORS = ["whatifs/herostill.py:make_for_episode", "whatifs/insights.py:post_drop", "whatifs/pilots.py:run", "whatifs/specials.py:_publish"]

def _ago(**kw): return (core.now_utc() - dt.timedelta(**kw)).strftime("%Y-%m-%dT%H:%M:%SZ")

def _ep(ep="EPC1", status="SCHEDULED", slot=None, **kw):
    row = {"episode_id": ep, "slot_et": slot or _ago(minutes=40), "status": status, "yt_id": "VID_" + ep, "title": "T", "assets": "{}"}
    row.update(kw); core.store().append("Episodes", [row])
    d = os.path.join(core.WORK, ep); os.makedirs(d, exist_ok=True)
    json.dump({"title": "T", "pinned": "What would you do first?", "title_b": "B", "thumb_b": ""}, open(os.path.join(d, "release.json"), "w"))
    return row

def _row(ep="EPC1"): return next(r for r in core.store().rows("Episodes") if r["episode_id"] == ep)

def _wire(monkeypatch, status="public"):
    """The platform calls of the release step, counted."""
    seen = {"comment": [], "upload": [], "reel": [], "mail": [], "private": []}
    monkeypatch.setattr(PUB, "yt_status", lambda vid: status)
    monkeypatch.setattr(PUB, "yt_comment", lambda vid, text: seen["comment"].append((vid, text)))
    monkeypatch.setattr(PUB, "yt_upload", lambda *a, **k: seen["upload"].append(a) or "UP")
    monkeypatch.setattr(PUB, "ig_reel", lambda *a, **k: seen["reel"].append(a) or "IG")
    monkeypatch.setattr(PUB, "fb_reel", lambda *a, **k: seen["reel"].append(a) or "FB")
    monkeypatch.setattr(PUB, "yt_set_privacy", lambda vid, p: seen["private"].append((vid, p)))
    monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: seen["mail"].append(subj) or True)
    monkeypatch.setattr(MG, "_produce_slot", lambda eps: None)
    return seen

# ------------------------------------------------------------------ nothing of the cut-downs is left
def test_no_check_no_setting_no_role_and_no_module_of_the_cut_downs_is_left():
    ids = [f[0] for f in CON.FEATURES]; by = {}
    for f in CON.FEATURES: by[f[1]] = by.get(f[1], 0) + 1
    assert "shorts" not in ids and "short_covers" not in ids and by == {"script": 37, "final": 20, "short": 5, "short_file": 2, "release": 1} and len(ids) == 65, by      # v12 V2b: + viewer_inside
    assert not [k for k in GONE_CELLS if k in core.DEFAULTS], "a Settings cell of the cut-downs is back"
    assert "REEL1_DELAY_MIN" in core.DEFAULTS and "release step" in core.DEFAULTS["REEL1_DELAY_MIN"][1], "the release step keeps its delay cell, and the note says what it is now"
    from whatifs import models, prompts, room, cta, art, episode
    from whatifs.org import levers, registry
    assert "reels" not in models.ROUTES and "reels" not in models.SAVER_MEDIUM and not hasattr(prompts, "REEL") and not hasattr(prompts, "REEL_STYLE_BRIDGE")
    assert not any(hasattr(room, n) for n in ("reels", "reel_count", "reel_style", "past_footage")) and not hasattr(cta, "reel_ask") and not hasattr(art, "reel_cover")
    assert not hasattr(episode, "REELS") and not any(hasattr(MG, n) for n in ("_post_reel", "_release_extra", "extra_reel_due"))
    with pytest.raises(ImportError): __import__("whatifs.reels")
    assert "REEL2_DELAY_MIN" not in levers.LEVERS and "REEL2_DELAY_MIN" not in registry.DEPTS["D9"]["levers"] and "REEL1_DELAY_MIN" in registry.DEPTS["D9"]["levers"]
    assert "shorts" not in registry.CHECK_OWNER and "short_covers" not in registry.CHECK_OWNER
    for name in ("PACKAGER", "SHOWRUNNER"):
        assert "reel" not in getattr(prompts, name).lower(), f"the {name} prompt still asks for reel material nobody uses"

def test_the_draw_plans_no_reel_and_an_older_video_keeps_what_it_learned():
    MG.setup()
    d = SAM.draw("EPDRAW1", "collective")
    assert "reel" not in d["strategies"] and "reel_formats" not in d and {"story", "hook", "voice", "humour", "thumb", "title", "banter", "family"} <= set(d["strategies"])
    assert not [r for r in core.store().rows("Strategies") if r.get("dimension") == "reel"], "a new Sheet is seeded with no reel formats"
    sc = {"shorts": 0.7, "pack": 0.5, "open": 0.5, "hold": 0.5, "reach": 0.5}
    assert not [k for k in MG.strategy_credits(d, sc) if k[0] == "reel"], "a video without reels credits no reel format"
    old = {"strategies": {"reel": "R1_climax_why"}, "reel_formats": ["R1_climax_why", "R2_countdown"], "reel_style": "bridge"}
    assert {k for k in MG.strategy_credits(old, sc) if k[0] == "reel"} == {("reel", "R1_climax_why"), ("reel", "R2_countdown")}, "what an older video's reels earned stays on record"

def test_the_lesson_of_a_videos_shorts_traffic_says_what_is_true():
    new = MG.shorts_lesson("EPN", {"from_shorts": 41}, {"strategies": {}})
    assert new == "EPN: 41 long-video views came from the Shorts feed" and "reel" not in new
    old = MG.shorts_lesson("EPO", {"from_shorts": 9, "shorts_subs": 3}, {"reel_style": "bridge"})
    assert "9 long-video views" in old and "bridge reels" in old and "3 subscribers" in old

def test_the_rulebook_takes_no_rule_for_a_reel_department():
    cand = [{"department": "reel", "rule": "End every reel on the open question of the long video", "metric": "shorts", "source_url": "https://support.google.com/youtube/answer/1", "evidence": "official"},
            {"department": "writer", "rule": "Open the script inside the scene with a picture the viewer can stand in", "metric": "open", "source_url": "https://support.google.com/youtube/answer/2", "evidence": "official"}]
    kept, dropped = PB.vet(cand)
    assert [k["department"] for k in kept] == ["writer"] and any("unknown department" in str(x) for x in dropped), (kept, dropped)

# ------------------------------------------------------------------ the long video's release is ONE step
def test_release_is_one_step_public_then_the_comment_then_live(setting, monkeypatch):
    setting("VOICE", "A"); seen = _wire(monkeypatch); _ep()
    assert MG.tick() == {"action": "release1", "episode": "EPC1"}
    MG.release("EPC1", "release1")
    assert _row()["status"] == "LIVE" and seen["comment"] == [("VID_EPC1", "What would you do first?")], (_row()["status"], seen)
    assert seen["upload"] == [] and seen["reel"] == [], "nothing is uploaded with a long video's release"
    assert MG.tick() == {"action": "idle"}, "no second release is named"
    MG.release("EPC1", "release1")
    assert len(seen["comment"]) == 1, "a release that ran is never run twice"
    assert not any(str(_row().get(k) or "").strip() for k in ("reel1_yt", "reel2_yt", "reel3_yt", "reel4_yt", "ig1", "fb1"))

def test_the_release_waits_for_its_delay_and_nothing_follows_on_later_days(setting, monkeypatch):
    setting("VOICE", "A"); seen = _wire(monkeypatch); _ep(slot=_ago(minutes=5))
    assert MG.tick() == {"action": "idle"}, "REEL1_DELAY_MIN minutes after the slot, not before"
    setting("REEL1_DELAY_MIN", "3")
    assert MG.tick() == {"action": "release1", "episode": "EPC1"}
    MG.release("EPC1", "release1")
    for h in (7, 27, 51):                                                        # where reels 2, 3 and 4 used to be due
        core.store().update("Episodes", "episode_id", "EPC1", {"slot_et": _ago(hours=h), "assets": json.dumps({"reel2.mp4": "a", "reel3.mp4": "b"})})
        assert MG.tick() == {"action": "idle"}, h
    assert seen["upload"] == [] and seen["reel"] == []

def test_a_video_that_is_not_public_waits_and_the_owner_hears_once(setting, monkeypatch):
    setting("VOICE", "A"); seen = _wire(monkeypatch, status="private"); _ep(slot=_ago(hours=core.S("PRIVATE_ALERT_HOURS", float) + 1))
    MG.release("EPC1", "release1"); MG.release("EPC1", "release1")
    assert _row()["status"] == "SCHEDULED" and seen["comment"] == [] and seen["mail"] == ["Video not public yet"], (_row()["status"], seen)
    assert "release step waits" in open(os.path.join(ROOT, "whatifs", "manage.py"), encoding="utf-8").read()

def test_kill_before_the_release_makes_the_video_private(setting, monkeypatch):
    seen = _wire(monkeypatch); _ep(kill="KILL")
    MG.release("EPC1", "release1")
    assert _row()["status"] == "KILLED" and seen["private"] == [("VID_EPC1", "private")] and seen["comment"] == []

def test_a_row_an_older_version_left_half_released_is_closed_by_the_tick_and_nothing_is_posted(setting, monkeypatch):
    setting("VOICE", "A"); seen = _wire(monkeypatch); _ep("EPOLD", status="LIVE1", slot=_ago(hours=3))
    a = MG.tick()
    assert a == {"action": "idle"} and _row("EPOLD")["status"] == "LIVE" and "no cut-down reels" in _row("EPOLD")["notes"], (a, _row("EPOLD"))
    assert seen["upload"] == [] and seen["reel"] == [] and seen["comment"] == []

def test_the_cli_and_the_workflow_know_one_release():
    src = open(os.path.join(ROOT, "whatifs", "cli.py"), encoding="utf-8").read()
    assert 'cmd == "release1"' in src and not any(x in src for x in ("release2", "release3", "release4"))
    yml = open(os.path.join(ROOT, ".github", "workflows", "pipeline.yml"), encoding="utf-8").read()
    assert "startsWith(needs.tick.outputs.action, 'release')" in yml, "the pipeline hands the tick's release action to the release job"

def test_the_rehearsal_and_the_sweep_walk_the_rule():
    reh = open(os.path.join(ROOT, "tools", "rehearsal.py"), encoding="utf-8").read(); swp = open(os.path.join(ROOT, "tools", "sweep.py"), encoding="utf-8").read()
    assert 'print("cut-downs: none made, none uploaded' in reh and '"a cut-down reel was planned or made"' in reh and "a short video went out that is not a standalone Short" in reh
    assert "ok_r, res[\"release\"] = release_of(core, ep, r)" in swp and 'if not ok_r: res["outcome"] = "odd"' in swp, "every long-video id of the sweep is judged for cut-downs and the one-step release"
    from tools import sweep as SW
    s = SW.summary([{"id": "A", "mode": "produce", "outcome": "ok", "release": "no cut-down made or uploaded; released in one step"},
                    {"id": "B", "mode": "produce", "outcome": "odd", "release": "cut-down files were made: reel0.mp4", "problems": ["cut-downs or the release step: x"]},
                    {"id": "C", "mode": "short", "outcome": "ok", "release": "DONE+DONE+DONE"}])
    assert s["released_without_cutdowns"] == 1 and s["bad_ids"] == ["B"], s

# ------------------------------------------------------------------ ONE DOOR for every upright video
def _tree(tmp_path):
    r = str(tmp_path / "repo"); shutil.copytree(os.path.join(ROOT, "whatifs"), os.path.join(r, "whatifs"), ignore=shutil.ignore_patterns("__pycache__", "seed"))
    return r

def _doors(root):
    TRU.reset(); out = TRU.door_issues(root); TRU.reset(); return out

def _add(root, rel, text):
    with open(os.path.join(root, *rel.split("/")), "a", encoding="utf-8", newline="\n") as f: f.write(text)

def test_the_repo_has_the_four_listed_doors_and_no_other():
    TRU.reset()
    assert TRU.short_doors() == DOORS == sorted(TRU.OLD_DOORS) and TRU.door_issues() == [] and TRU.OLD_DOORS_MAX == len(TRU.OLD_DOORS) == 4
    assert all("FALSE" in what for what in TRU.OLD_DOORS.values()), "every listed door says which switch keeps it shut"
    for cell in ("PILOTS_ON", "SPECIALS_ON", "HERO_STILL_SHORTS_ON", "AUDIO_DROP_POST_ON"):
        assert core.DEFAULTS[cell][0] == "FALSE", f"{cell}: a listed door is open by default"

@pytest.mark.parametrize("call, door", [
    ("PUB.ig_reel(None, 'c', None, video_path=p)", True), ("PUB.fb_reel(None, 'c', video_path=p)", True), ("fb_reel(None, 'c')", True),
    ("PUB.yt_upload(p, 't', 'd', [], short=True, ai_label=True)", True), ("PUB.yt_upload(p, 't', 'd', [], short=is_short)", True),
    ("PUB.yt_upload(p, 't', 'd', [], publish_at=None)", False), ("PUB.yt_upload(p, 't', 'd', [], short=False)", False), ("PUB.yt_thumbnail(p, 'x')", False)])
def test_a_new_door_is_found_and_a_long_upload_is_not_one(tmp_path, call, door):
    r = _tree(tmp_path)
    assert _doors(r) == []
    _add(r, "whatifs/growth.py", f"\ndef post_teaser(p, is_short=True):\n    from whatifs import publish as PUB\n    from whatifs.publish import fb_reel\n    return {call}\n")
    got = _doors(r)
    assert (len(got) == 1 and got[0].startswith("whatifs/growth.py:post_teaser: uploads an upright video outside whatifs/release.py")) if door else got == [], got

def test_a_door_inside_a_nested_function_is_found_at_its_outer_function(tmp_path):
    r = _tree(tmp_path)
    _add(r, "whatifs/growth.py", "\ndef post_pack(paths):\n    from whatifs import publish as PUB\n    def one(p):\n        return PUB.ig_reel(None, 'c', None, video_path=p)\n    return [one(p) for p in paths]\n")
    assert [x.split(":")[1] for x in _doors(r)] == ["post_pack"]

def test_publishings_own_run_and_the_platform_calls_are_the_home_of_the_door(tmp_path):
    r = _tree(tmp_path)
    for rel in ("whatifs/release.py", "whatifs/publish.py"):
        _add(r, rel, "\ndef another_sender(p):\n    from whatifs import publish as PUB\n    return PUB.ig_reel(None, 'c', None, video_path=p)\n")
    assert _doors(r) == []

def test_the_list_of_older_doors_may_only_shrink(tmp_path, monkeypatch):
    r = _tree(tmp_path); p = os.path.join(r, "whatifs", "pilots.py"); src = open(p, encoding="utf-8").read()
    assert "PUB.yt_upload(" in src
    open(p, "w", encoding="utf-8", newline="\n").write(src.replace("PUB.yt_upload(", "PUB.yt_filed("))
    got = _doors(r)
    assert got == ["whatifs/truth.py: OLD_DOORS lists whatifs/pilots.py:run, which uploads nothing any more or is gone - delete the entry and lower OLD_DOORS_MAX"], got
    monkeypatch.setattr(TRU, "OLD_DOORS", dict(TRU.OLD_DOORS, **{"whatifs/growth.py:post_teaser": "a new one, listed instead of rebuilt"}))
    _add(r, "whatifs/growth.py", "\ndef post_teaser(p):\n    from whatifs import publish as PUB\n    return PUB.fb_reel(None, 'c', video_path=p)\n")
    open(p, "w", encoding="utf-8", newline="\n").write(src)
    assert _doors(r) == ["whatifs/truth.py: OLD_DOORS grew to 5 (limit 4): the list may only shrink"]

def test_a_new_door_fails_the_truth_registry_and_the_contract_check(tmp_path, monkeypatch, setting):
    r = _tree(tmp_path)
    _add(r, "whatifs/growth.py", "\ndef post_teaser(p):\n    from whatifs import publish as PUB\n    return PUB.yt_upload(p, 't', 'd', [], short=True)\n")
    TRU.reset(); bad = [x for x in TRU.issues(r) if "post_teaser" in x and "upright" in x]; TRU.reset()
    assert len(bad) == 1 and "release.short" in bad[0], bad
    # the contract check on the real repo: clean today, and held by ONE new door (the only fault set up)
    TRU.reset(); status, ev = CON.p_docs_current({})
    assert status == CON.PASS, ev
    monkeypatch.setattr(TRU, "short_doors", lambda root=None: DOORS + ["whatifs/growth.py:post_teaser"]); TRU.reset()
    status, ev = CON.p_docs_current({})
    TRU.reset()
    assert status == CON.FAIL and str(ev).startswith("1 retired or stale reference(s): whatifs/growth.py:post_teaser: uploads an upright video"), (status, ev)

def test_a_tree_without_the_platform_calls_is_not_judged(tmp_path):
    r = str(tmp_path / "bare"); os.makedirs(os.path.join(r, "whatifs"))
    _add(r, "whatifs/x.py", "def f(p):" + chr(10) + "    return ig_reel(p)" + chr(10)); _add(r, "whatifs/publish.py", ""); _add(r, "whatifs/release.py", "")
    assert _doors(r) == [], "an empty stand-in for the platform calls is no repository to judge"
    _add(r, "whatifs/publish.py", "def ig_reel(*a, **k):" + chr(10) + "    return 1" + chr(10))
    assert len(_doors(r)) == 5, "with the platform calls there, the new door is named and the four listed ones are missed"

# ------------------------------------------------------------------ the older tracks are paused by default
def test_pilot_shorts_and_special_reels_are_paused_by_default_and_their_money_is_production_money(setting, monkeypatch):
    MG.setup()
    calls = []
    monkeypatch.setattr(PUB, "yt_upload", lambda *a, **k: calls.append(a) or "UP")
    p = PL.run(); s = SP.run(kind="special")
    assert p == {"ok": False, "why": "PILOTS_ON is FALSE"} and s == {"ok": False, "why": "SPECIALS_ON is FALSE"} and calls == [], (p, s)
    assert G.specials_left_inr() == 0.0
    setting("SPECIALS_ON", "TRUE")
    assert G.specials_left_inr() == core.S("SPECIALS_EARMARK_INR", float) > 0, "switched back on, the special reels have their earmark again"

# ------------------------------------------------------------------ a live Sheet is moved once
def _live_sheet():
    st = core.store()
    have = {r.get("key") for r in st.rows("Settings")}
    for k in GONE_CELLS:
        if k not in have: st.append("Settings", [{"key": k, "value": "4" if k == "REELS_PER_VIDEO" else "TRUE", "note": "an older note"}])
    for k in ("PILOTS_ON", "SPECIALS_ON"):
        if k not in have: st.append("Settings", [{"key": k, "value": "TRUE", "note": "an older note"}])
    core._settings_cache = None
    return st

def _cell(k): return next(r for r in core.store().rows("Settings") if r.get("key") == k)

def test_the_one_time_move_marks_the_dead_cells_and_pauses_the_two_tracks(setting):
    st = _live_sheet(); st.update("Settings", "key", "PILOTS_ON", {"value": "TRUE"}); st.update("Settings", "key", "SPECIALS_ON", {"value": "TRUE"}); core._settings_cache = None
    done = MG.v12v2cb2b_upgrade(st); core._settings_cache = None
    assert sorted(done) == sorted(GONE_CELLS + ("PILOTS_ON", "SPECIALS_ON")), done
    assert all(_cell(k)["note"].startswith("RETIRED (v12 V2c-b2b)") for k in GONE_CELLS) and _cell("REELS_PER_VIDEO")["value"] == "4", "the value is left as he last saw it"
    for k in ("PILOTS_ON", "SPECIALS_ON"):
        assert _cell(k)["value"] == "FALSE" and _cell(k)["note"].startswith("PAUSED by the v12 V2c-b2b move (it was TRUE)") and core.S(k, bool) is False
    assert str(core.S("V12V2CB2B_MOVE_DONE")).strip()

def test_the_move_never_runs_twice_and_leaves_his_own_choice_alone(setting):
    st = _live_sheet(); st.update("Settings", "key", "PILOTS_ON", {"value": "FALSE", "note": "his own note"}); st.update("Settings", "key", "SPECIALS_ON", {"value": "TRUE"}); core._settings_cache = None
    done = MG.v12v2cb2b_upgrade(st); core._settings_cache = None
    assert "PILOTS_ON" not in done and _cell("PILOTS_ON")["note"] == "his own note" and "SPECIALS_ON" in done
    st.update("Settings", "key", "SPECIALS_ON", {"value": "TRUE"}); core._settings_cache = None      # he switches the special reels back on
    assert MG.v12v2cb2b_upgrade(st) == [] and _cell("SPECIALS_ON")["value"] == "TRUE", "the move is ONE time: his later choice stands"

def test_setup_runs_the_move():
    src = open(os.path.join(ROOT, "whatifs", "manage.py"), encoding="utf-8").read()
    assert src.count("try: v12v2cb2b_upgrade(st)") == 2, "both setup sites call the one-time move"
    _live_sheet(); core.store().update("Settings", "key", "PILOTS_ON", {"value": "TRUE"}); core._settings_cache = None
    MG.setup(); core._settings_cache = None
    assert _cell("PILOTS_ON")["value"] == "FALSE" and _cell("REEL_STYLE")["note"].startswith("RETIRED")

# ------------------------------------------------------------------ the truth registry refuses the old words
@pytest.mark.parametrize("line", ["Set REELS_PER_VIDEO to 4.", "The reel style comes from REEL_STYLE.", "Reel 3 goes out after REEL3_DELAY_MIN minutes.", "REEL1_SHORTS_ON sends reels to YouTube.",
                                  "Four bridge Shorts follow every video.", "Bridge reels pull viewers over.", "Shorts cut from each long video go out on the next days.",
                                  "Reels cut from the long video are posted to Instagram.", "The channel posts 4 Shorts per video.", "2 reels a long video go out on launch day."])
def test_the_retired_rule_names_the_old_plan(line):
    assert "cutdown_reels" in [r["id"] for r in TRU.hits(line, "docs")] and "cutdown_reels" in [r["id"] for r in TRU.hits(line, "prompts")], line

@pytest.mark.parametrize("line", ["A long video makes no cut-down reels.", "No Shorts cut from the long video go out any more.", "REELS_PER_VIDEO is retired.", "d.get('reel_style')",
                                  "REEL1_DELAY_MIN minutes after its slot the release step runs.", "Three Shorts a week, twelve a month.", "A bridge over the river.",
                                  "Instagram Reels and Facebook Reels get their own upload.", "4 Shorts a week at most."])
def test_the_retired_rule_does_not_fire_on_what_is_true(line):
    assert "cutdown_reels" not in [r["id"] for r in TRU.hits(line, "docs")], line

# ------------------------------------------------------------------ the estimate
def test_every_estimate_counts_two_premium_pictures_fewer(setting):
    setting("PKG_RESCUE_ON", "TRUE"); assert G.premium_images() == 2, "the thumbnail and its runner-up: no reel covers"
    a = G.min_episode_cost_inr()
    setting("PKG_RESCUE_ON", "FALSE"); assert G.premium_images() == 1
    assert a > G.min_episode_cost_inr(), "a premium picture is money in the estimate"

# ------------------------------------------------------------------ a whole production: nothing is paid for a cut-down, and the sweep's verdict can see one
def test_a_whole_production_pays_nothing_for_cut_downs_and_the_sweeps_verdict_recognises_one(monkeypatch, tmp_path):
    from tests.paid_calls import count, V12V2CB2C_COUNTED as WAS, V12V2CB2C_REMOVED as GONE
    from tools import sweep as SW
    now, r = count(monkeypatch, tmp_path)
    assert r.get("ok") and "reels" not in r, r
    assert now.get("text:reels", 0) == 0, "the cut-downs' planning call is paid again"
    assert now["image_premium"] == WAS["image_premium"] - GONE["image_premium"] == 2, ("premium pictures: the thumbnail and its runner-up, no reel cover", now["image_premium"])
    assert now["voice_job"] == WAS["voice_job"] - GONE["voice_job"] == 1, ("voice jobs: the narration, no reel", now["voice_job"])
    ep = r["episode"]; out = os.path.dirname(r["master"]); st = core.store(); relp = os.path.join(out, "release.json")
    ok, words = SW.release_of(core, ep, r)
    assert ok and words.startswith("no cut-down made or uploaded; released in one step") and _row(ep)["status"] == "LIVE", words
    def again(): st.update("Episodes", "episode_id", ep, {"status": "SCHEDULED"}); return SW.release_of(core, ep, r)
    assert again()[0], "the verdict is repeatable on a clean episode"
    # the verdict must RECOGNISE a cut-down - one fault at a time, each named alone
    open(os.path.join(out, "reel0.mp4"), "wb").write(b"x")
    assert again() == (False, "cut-down files were made: reel0.mp4"); os.remove(os.path.join(out, "reel0.mp4"))
    rel = json.load(open(relp)); json.dump(dict(rel, reels=[{"file": "reel0.mp4"}]), open(relp, "w"))
    assert again() == (False, "the release record is missing or still lists reels"); json.dump(rel, open(relp, "w"))
    st.update("Episodes", "episode_id", ep, {"reel1_yt": "SHORT_X"})
    assert again() == (False, "a cut-down reel is on the episode's row"); st.update("Episodes", "episode_id", ep, {"reel1_yt": ""})
    dj = json.loads(_row(ep)["draw_json"]); st.update("Episodes", "episode_id", ep, {"draw_json": json.dumps(dict(dj, reel_style="bridge"))})
    assert again() == (False, "the draw still carries a reel strategy"); st.update("Episodes", "episode_id", ep, {"draw_json": json.dumps(dj)})
    st.append("Release_Sheet", [{"ts": core.iso(), "id": "PULL1", "platform": "youtube", "kind": "pull", "native_id": "X", "state": "DONE"}])
    ok, words = again()
    assert not ok and words == "a short video went out that is not a standalone Short: ['pull']", words
