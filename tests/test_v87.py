"""v8.7: packaging-first promise, retention gate, rhythm blueprint (anti-sameness), sensory sound, related-video link, research-graded playbook with trials,
watch-time-per-impression packaging score, CTR unit check, relative retention, dip finder, and the maintenance reserve INSIDE the cap. No keys, no network."""
import json, os, datetime as dt, random
import numpy as np
import pytest
from whatifs import core, growth as GR, governor as G, playbook as PB, sound as SD, render as RN, room as ROOM, manage as MG, episode as EP, prompts as P
from whatifs.sampler import draw as DRAW

def _legacy_budget(setting):
    setting("BUDGET_FLOOR_INR", "4000"); setting("BUDGET_CEILING_INR", "4000"); setting("BUDGET_EARMARK_INR", "0"); setting("V94A_FLIPS_ON", "FALSE"); setting("V10_FLIPS_ON", "FALSE"); setting("SPECIALS_ON", "FALSE")      # v9.4a: this test keeps the v8 budget profile (₹4,000, no earmark, no cap move)


def _spend(inr): core.cost("test_spend", "fal", 1, inr / core.S("USD_INR", float))

# ------------------------------------------------------------------ money: the month never totals more than the cap
def test_reserve_is_inside_the_cap(setting):
    _legacy_budget(setting)
    assert abs(G.production_room_inr() - (G.remaining_inr() - 100 - G.org_left_inr())) < 1e-6          # v12 B5: the organisation's thinking caps are reserved too
    _spend(3905); assert G.monthly_cap_reached()      # v8.10 cap 4,000 and not G.monthly_cap_reached(maintenance=True)
    ok, why = G.can_start_episode(); assert not ok and "maintenance" in why
    _spend(95); assert G.monthly_cap_reached(maintenance=True)

def test_a_full_nine_video_month_fits_under_the_production_line(setting):
    setting("KLING_CLIPS", "3"); setting("KLING_MIN_CLIPS", "3")      # v10.2: this golden describes the 3-clip plan; option C's 4 scenes are tested in test_v102
    setting("PRICE_KLING_USD", "0.25")      # v10.1: this cost golden keeps the Kling 2.1 price; the new $0.35 is tested in test_v101
    d = {"stills": 52, "living": 8, "kling": 3, "episode_id": "EPC"}
    per = EP.est_cost_inr(d)
    pal = G.palace_prompt_inr(); assert pal == 10                                  # v12 B6a: the Palace in the creative prompts is in every estimate
    assert 455 + pal < per < 475 + pal and core.S("LLM_EST_INR", float) == 176      # v9: AI_SAVER_ON by default (v8.11: 200; Opus script, thinking 40)
    assert 8 * per <= core.S("BUDGET_CEILING_INR", float)                 # v8.11: 8 videos fit the cap on padded estimates; 9 do not (see the v8.11 report:
    plan = G.plan_for_episode(per, 9)                                      # AI-side savings, never visual cuts) - and the planner keeps every picture and clip
    assert plan["tier"] == "full" and plan["kling"] == 3
    assert G.min_episode_cost_inr() * core.S("BUDGET_SAFETY_MARGIN", float) < 530 + pal * core.S("BUDGET_SAFETY_MARGIN", float)      # v8.11: + the higher AI allowance

def test_plan_for_episode_uses_the_production_room(setting):
    _legacy_budget(setting)
    _spend(3550)            # v8.10 cap 4,000: Rs 350 production room: the full tier no longer fits with the 1.10 margin, a cheaper tier or a hold, never an overspend
    p = G.plan_for_episode(348.0 + 62, 1)             # v8.11: a realistic estimate (AI allowance +62; the visuals protection subtracts exactly that again)
    assert p["hold"] or p["tier"] in ("lean", "slim", "floor")

# ------------------------------------------------------------------ CTR unit, watch time per impression, relative retention, dips
def test_ctr_unit_is_checked_not_assumed():
    assert GR.ctr_ratio(5.0, 10000, 600) == 0.05          # a percentage (10000 x 5 would be far more clicks than views)
    assert GR.ctr_ratio(0.05, 10000, 600) == 0.05         # already a ratio (500 clicks <= 600 views)
    assert GR.ctr_ratio(4.2) == 0.042                     # no impressions: the documented percentage
    assert GR.ctr_ratio(None) is None and GR.ctr_ratio(-1) is None and GR.ctr_ratio("x") is None

def test_packaging_is_scored_on_watch_time_per_impression():
    assert GR.dim_scores({"wtpi": 9.0}, [])["pack"] == pytest.approx(0.5)
    hist = [{"wtpi": 18.0}, {"wtpi": 18.0}]
    assert GR.dim_scores({"wtpi": 9.0}, hist)["pack"] == pytest.approx(0.25)
    assert GR.dim_scores({"ctr": 0.05}, [])["pack"] == pytest.approx(0.5)      # v8.6 behaviour when only CTR exists
    assert GR.score_for("rhythm", {"hold": 0.4}) == 0.4 and GR.score_for("sound", {"hold": 0.3}) == 0.3

def test_early_diagnosis_uses_retention_vs_similar_length_videos():
    lab, les = GR.diagnose({"rel30": 0.2, "title": "T"}, []); assert lab == "opening" and "0.20" in les
    lab, les = GR.diagnose({"rel30": 0.6, "rel_avg": 0.25, "title": "T"}, []); assert lab == "holding"
    assert GR.diagnose({"rel30": 0.6, "rel_avg": 0.6}, [])[0] == "insufficient data"
    assert GR.diagnose({}, [])[0] == "insufficient data"

def _curve(drop_at=0.40, drop=0.10):
    pts = []
    for i in range(101):
        r = i / 100; y = 1.0 - 0.002 * i
        if r > drop_at: y -= min(drop, drop * (r - drop_at) / 0.05)
        pts.append((r, y))
    return pts

def test_dip_finder_maps_the_steepest_drop_to_its_beat():
    les = GR.dip_lesson(_curve(), [[0, "Intro"], [200, "The flood"], [300, "Aftermath"]], 600, "Ocean Gone")
    assert les.startswith("holding:") and "The flood" in les and "4:00" in les
    assert GR.dip_lesson(_curve(drop=0.0), [[0, "Intro"]], 600) == ""
    assert GR.dip_lesson([], [], 600) == "" and GR.dip_lesson(_curve(), [], 30) == ""

def test_analytics_reads_impressions_and_relative_retention(monkeypatch):
    class R:
        def __init__(self, j): self.j = j
        def json(self): return self.j
    calls = iter([R({"rows": [[500, 41.0, 230, 3, 1, 2]]}), R({"rows": [[0.0, 1.0], [0.05, 0.7], [0.1, 0.6]]}), R({}),
                  R({"rows": [[10000, 5.0]]}), R({"rows": [[0.0, 0.5], [0.05, 0.62], [0.5, 0.4]]})])
    monkeypatch.setattr(MG, "FAKE", False); monkeypatch.setattr(MG, "gheaders", lambda: {})
    monkeypatch.setattr(MG.requests, "get", lambda *a, **k: next(calls))
    m = MG._analytics("VID", core.now_utc(), 600)
    assert m["ctr_kind"] == "real" and m["ctr"] == 0.05 and m["impressions"] == 10000 and m["ret30"] == 0.7
    assert m["rel30"] == 0.62 and m["rel_avg"] == pytest.approx(0.5067, abs=1e-3)

def test_learn_records_wtpi_dip_lesson_and_credits_playbook_trials(monkeypatch):
    st = core.store(); rid = "PBTEST1"
    st.append("Playbook", [{"rule_id": rid, "department": "writer", "rule": "a trial rule for the test", "metric": "hold", "source": "https://support.google.com/youtube",
                            "evidence": "official", "status": "trial", "added": "t", "plays_on": 0, "sum_on": 0, "plays_off": 0, "sum_off": 0}])
    slot = (core.now_utc() - dt.timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st.append("Episodes", [{"episode_id": "EPL", "slot_et": slot, "status": "LIVE", "yt_id": "VIDL", "title": "Ocean Gone",
                            "draw_json": {"strategies": {}, "playbook": {rid: "on"}, "beat_map": [[0, "Intro"], [200, "The flood"]], "duration_sec": 600}}])
    monkeypatch.setattr(MG, "_analytics", lambda vid, t, dur=None: {"views": 900, "avg_view_pct": 40.0, "avg_view_sec": 200.0, "ret30": 0.6, "ctr": 0.05, "ctr_kind": "real",
                                                                    "likes": 1, "shares": 1, "subs": 1, "from_shorts": None, "curve": _curve()})
    monkeypatch.setattr(MG, "_shorts_stats", lambda e, t: {}); monkeypatch.setattr(MG, "pkg_rescue", lambda now=None: [])
    MG.learn()
    a = [r for r in st.rows("Analytics") if r["episode_id"] == "EPL"][-1]; assert float(a["wtpi"]) == 10.0
    assert any("lost" in l["lesson"] and "The flood" in l["lesson"] for l in st.rows("Lessons"))
    pb = next(r for r in st.rows("Playbook") if r["rule_id"] == rid); assert int(pb["plays_on"]) == 1 and float(pb["sum_on"]) == pytest.approx(0.5)

def test_missing_metrics_never_credit_a_trial():
    st = core.store(); st.append("Playbook", [{"rule_id": "PBM", "department": "writer", "rule": "r", "metric": "open", "source": "https://x.y", "status": "trial", "plays_on": 0, "sum_on": 0}])
    assert PB.credit({"PBM": "on"}, {"open": None, "hold": 0.4}) == 0

# ------------------------------------------------------------------ packaging first
def test_clean_promise_prefers_a_clean_title_and_short_thumb_text():
    p = GR.clean_promise({"promise": {"title": "THIS IS A VERY LOUD TITLE THAT IS WAY TOO LONG FOR ANY PHONE SCREEN", "thumb_text": "don't sneeze ever again please"},
                          "title_candidates": ["Your Bones Are Glass Now. Don't Breathe."], "thumb_concept": "glass skeleton", "peak_moment": "the first crack"})
    assert p["title"] == "Your Bones Are Glass Now. Don't Breathe." and len(p["thumb_text"].split()) <= 4
    assert p["thumb_scene"] == "glass skeleton" and p["first_30s"] == "the first crack"
    assert GR.promise_text({}) == "none" and "Thumbnail image" in GR.promise_text(p)

def test_insert_before_json_keeps_the_reply_format_last():
    out = GR.insert_before_json("ROLE\nReturn JSON: {}", "EXTRA")
    assert out.index("EXTRA") < out.index("Return JSON") and GR.insert_before_json("x", "") == "x"
    assert "@@PROMISE@@" not in P.fill(P.PACKAGER, promise="PROMISE-X") and "PROMISE-X" in P.fill(P.PACKAGER, promise="PROMISE-X")
    assert "at most 4 shots" in P.fill(P.DIRECTOR, sounds=4) and '"promise"' in P.SHOWRUNNER

def test_writer_brief_carries_the_promise_the_rhythm_and_the_playbook(monkeypatch, setting):
    setting("ROOM_MODE", "v1")                                 # v1 path (single writer call); the v2 path is checked below
    PB.ensure_seed(); seen = {}
    real = ROOM.ask
    def spy(role, system, prompt, *a, **k):
        seen.setdefault(prompt, system); return real(role, system, prompt, *a, **k)
    monkeypatch.setattr(ROOM, "ask", spy)
    d = DRAW("EPW", "collective"); r = ROOM.run_room(d, "EPW")
    w = seen["Write the narration."]
    assert "THE PROMISE" in w and "RHYTHM BLUEPRINT" in w and "PLAYBOOK" in w and w.index("THE PROMISE") < w.rindex("Return JSON")
    assert r["spine"]["promise"]["title"] and d["retention_check"]["checked"] and d["promise"] == r["spine"]["promise"]


def test_room_v2_drafts_carry_the_same_brief_and_the_critic_still_gates(monkeypatch, setting):
    """v11: every v2 draft gets the full writer brief (promise, rhythm, playbook); the critic (policy-safety scores) still runs after the jury."""
    setting("ROOM_MODE", "v2"); PB.ensure_seed()
    import whatifs.models as M
    briefs, critics = [], []
    real_many = M.ask_many
    monkeypatch.setattr(M, "ask_many", lambda reqs, *a, **k: (briefs.extend(r["system"] for r in reqs if "COLD-OPEN ARCHETYPE" in r.get("prompt", "")), real_many(reqs, *a, **k))[1])
    real_critic = ROOM.critic
    monkeypatch.setattr(ROOM, "critic", lambda *a, **k: (critics.append(1), real_critic(*a, **k))[1])
    d = DRAW("EPW2", "collective"); ROOM.run_room(d, "EPW2")
    assert len(briefs) == core.S("ROOM_V2_DRAFTS", int) and all("THE PROMISE" in w and "RHYTHM BLUEPRINT" in w and "PLAYBOOK" in w for w in briefs)
    assert critics, "the critic (policy-safety gate) must still run in room v2"

# ------------------------------------------------------------------ retention gate
FILL = "[DIRECTOR] [calm] The light settles over the quiet street and nothing moves."
def _script(n=150, gap=(), strong=(45, 90), first="[DIRECTOR] [calm] Every pillow on Earth floats up at noon?"):
    out = ["## BEAT 1", first]
    for i in range(1, n):
        if i in strong: out.append("[SKEPTIC] [reveal] Wait, it gets worse from here on out.")
        elif i % 8 == 0 and not (gap and gap[0] <= i <= gap[1]): out.append("[SKEPTIC] So where does all of it go now?")
        else: out.append(FILL)
    return "\n".join(out)

def test_retention_issues_find_the_problems_and_where_they_are(setting):
    setting("COLD_OPEN_YOU_ON", "FALSE")          # v9.3 cold-open checks are tested in test_v93 (this fixture has no 'you' in its opening)
    pr = {"title": "Every Pillow Just Left Earth", "thumb_text": "LOOK UP", "thumb_scene": "pillows over a city"}
    assert GR.retention_issues(_script(), pr)["ok"]
    r = GR.retention_issues(_script(gap=(30, 70)), pr); assert not r["ok"] and r["max_gap"] > 90 and any(x.startswith("holding") for x in r["issues"])
    r = GR.retention_issues(_script(first="[DIRECTOR] Welcome back, today we talk about clouds."), pr)
    assert any("never shows or names the promise" in x for x in r["issues"]) and any("clears its throat" in x for x in r["issues"])
    r = GR.retention_issues(_script(strong=()), pr); assert sum("re-engagement" in x for x in r["issues"]) == 2
    r = GR.retention_issues(_script(), pr, loops=[{"open": "where do they land", "closed_in_beat": ""}]); assert any(x.startswith("payoff") for x in r["issues"])

def test_retention_pass_spends_nothing_when_the_script_is_fine(monkeypatch, setting):
    setting("COLD_OPEN_YOU_ON", "FALSE")          # v9.3: see test_v93 for the cold-open checks
    monkeypatch.setattr(ROOM, "ask", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no call expected")))
    pr = {"title": "Every Pillow Just Left Earth"}
    s, rec = ROOM.retention_pass({"script": _script()}, "brief\nReturn JSON", pr, "EPR")
    assert rec["checked"] and rec["before"] == 0 and not rec["fixed"]

def test_retention_pass_one_fix_accepted_only_if_better(monkeypatch):
    pr = {"title": "Every Pillow Just Left Earth"}; bad = _script(gap=(30, 70)); good = _script()
    calls = []
    monkeypatch.setattr(ROOM, "ask", lambda *a, **k: calls.append(1) or {"script": good})
    s, rec = ROOM.retention_pass({"script": bad}, "brief", pr, "EPR")
    assert rec["fixed"] and rec["after"] < rec["before"] and s["script"] == good and len(calls) == 1
    stripped = "\n".join(l.replace("[DIRECTOR] ", "").replace("[SKEPTIC] ", "") for l in good.splitlines())       # labels dropped = structure broken
    monkeypatch.setattr(ROOM, "ask", lambda *a, **k: {"script": stripped})
    s, rec = ROOM.retention_pass({"script": bad}, "brief", pr, "EPR"); assert not rec["fixed"] and s["script"] == bad
    monkeypatch.setattr(ROOM, "ask", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("API 529 overloaded")))
    s, rec = ROOM.retention_pass({"script": bad}, "brief", pr, "EPR"); assert not rec["fixed"] and s["script"] == bad      # an API error never blocks

def test_retention_gate_can_be_switched_off(setting):
    setting("RETENTION_GATE_ON", "FALSE")
    s, rec = ROOM.retention_pass({"script": "x"}, "b", {}, "E"); assert rec == {"checked": False}

# ------------------------------------------------------------------ rhythm blueprint: no two episodes in a row with the same shape
def test_rhythm_plan_rotates_least_recently_used():
    plans = []
    for k in range(8):
        p = GR.rhythm_plan("RB2_double_peak", random.Random(k), plans)
        if plans: assert p["opener"] != plans[-1]["opener"] and p["interrupt"] != plans[-1]["interrupt"]
        plans.append(p)
    assert len({p["opener"] for p in plans[:6]}) == 6
    assert GR.rhythm_plan("RB1_slow_fuse", random.Random(1), []) == GR.rhythm_plan("RB1_slow_fuse", random.Random(1), [])
    assert GR.rhythm_plan("RB3_pressure_cooker", random.Random(2), [])["arc"] == "pulse"
    assert "COLD OPEN DEVICE" in GR.rhythm_brief(plans[0]) and GR.rhythm_brief({}) == ""

def test_draw_has_rhythm_sound_and_playbook_even_on_an_old_sheet():
    d = DRAW("EPD1", "body")
    assert d["strategies"]["rhythm"] and d["strategies"]["sound"] and d["rhythm_plan"]["opener"] and isinstance(d["playbook"], dict)
    assert 3 <= d["hook_sec"] <= 8 and DRAW("EPD1", "body") == d
    st = core.store(); st.append("Episodes", [{"episode_id": "EPD1", "draw_json": d}])
    assert DRAW("EPD2", "body")["rhythm_plan"]["opener"] != d["rhythm_plan"]["opener"]

def test_learning_job_tops_up_new_strategies_on_an_older_sheet():
    st = core.store(); st.append("Strategies", [{"dimension": "story", "name": "S1_escalation", "status": "ACTIVE"}])
    MG._top_up(st); names = {r["name"] for r in st.rows("Strategies")}
    assert {"RB1_slow_fuse", "SD_textured"} <= names and len(st.rows("Playbook")) >= 7

# ------------------------------------------------------------------ sensory sound
def _units(n=12):
    out = []
    for i in range(n):
        txt = ["The ocean water rises fast.", "A heart starts pounding.", "Nothing much.", "The fire spreads."][i % 4]
        out.append({"i": i, "text": txt, "start": i * 5.0, "end": i * 5.0 + 4.5, "speaker": "SKEPTIC" if i == 3 else "DIRECTOR", "tag": "wow" if i == 3 else ("close" if i == 6 else "none")})
    return out

def test_plan_sounds_caps_spacing_and_reactions():
    u = _units(20); shots = [{"type": "still", "sound": "laser"} for _ in u]; shots[0]["sound"] = "drip"; shots[1]["sound"] = "wind"
    out = SD.plan_sounds(shots, u, "textured"); used = [i for i, s in enumerate(out) if s["sound"] != "none"]
    assert out[0]["sound"] == "drip" and out[1]["sound"] == "none" and "laser" not in {s["sound"] for s in out}
    assert len(used) <= 4 and all(b - a > 1 for a, b in zip(used, used[1:])) and 3 not in used
    assert SD.density_of("SD_rich") == "rich" and SD.density_of("new_learned") == "textured" and SD.guess("a glass of ice") == "glass"

def test_design_peaks_hush_and_textures():
    u = _units(12); shots = [{"type": "kling" if i in (2, 4, 9) else "still", "sound": "heartbeat" if i == 1 else "none"} for i in range(12)]
    dz = SD.design(shots, u, 60.0, {"arc": "waves"}, seed="E")
    assert dz["peaks"] == [10.0, 45.0] and dz["hush"] == [(30.0, 34.5)] and dz["sensory"] == [("heartbeat", 5.0, 10.0)] and dz["arc"] == "waves"

def test_the_bed_drops_before_a_peak_and_old_mixes_are_unchanged():
    a = RN.score(20.0, "EPS", [], None); b = RN.score(20.0, "EPS", [], None, design=None); assert np.array_equal(a, b)
    dz = {"arc": "still", "peaks": [12.0], "hush": [], "sections": [], "sensory": [("drip", 2.0, 6.0)]}
    c = RN.score(20.0, "EPS", [], None, design=dz); assert c.shape == a.shape and np.isfinite(c).all()
    rms = lambda x, s, e: float(np.sqrt(np.mean(x[int(s * 48000):int(e * 48000)] ** 2)))
    assert rms(c, 11.0, 11.9) < 0.25 * rms(a, 11.0, 11.9)
    assert np.array_equal(c, RN.score(20.0, "EPS", [], None, design=dz))          # retries re-mix identical audio

@pytest.mark.parametrize("kind", SD.KINDS)
def test_every_texture_is_finite_and_normalised(kind):
    x = SD.texture(kind, 2.0, "s", 48000); assert x.shape == (96000, 2) and np.isfinite(x).all() and np.abs(x).max() <= 1.0001

def test_close_tag_is_a_delivery_never_spoken():
    from whatifs.voice import parse_script
    u = parse_script("[DIRECTOR] [close] It is quiet now.\n[close] [SKEPTIC] Too quiet.")
    assert [(x.speaker, x.tag) for x in u] == [("DIRECTOR", "close"), ("SKEPTIC", "close")] and all("close" not in x.text.lower() for x in u)

# ------------------------------------------------------------------ come back for more: the related-video link
def test_related_episode_links_only_live_videos_same_family_first():
    eps = [{"episode_id": "A", "status": "LIVE", "yt_id": "aaa", "title": "A", "draw_json": json.dumps({"family": "F01_body"}), "slot_et": "1"},
           {"episode_id": "B", "status": "LIVE", "yt_id": "bbb", "title": "B", "draw_json": json.dumps({"family": "F09_space"}), "slot_et": "2"},
           {"episode_id": "C", "status": "SCHEDULED", "yt_id": "ccc", "draw_json": json.dumps({"family": "F01_body"})},
           {"episode_id": "D", "status": "LIVE", "yt_id": "ddd", "kill": "KILL", "draw_json": json.dumps({"family": "F01_body"})}]
    an = [{"episode_id": "B", "score": 0.9}, {"episode_id": "A", "score": 0.2}]
    assert GR.related_episode(eps, an, "F01_body", "NEW")["url"] == "https://youtu.be/aaa"
    assert GR.related_episode(eps, an, "F05_tech", "NEW")["episode_id"] == "B"
    assert GR.related_episode(eps, an, "F01_body", "A")["episode_id"] == "B" and GR.related_episode([], [], "x") is None

def test_description_puts_the_next_link_after_the_hook_paragraph(setting):
    setting("CTA_DESC_ON", "FALSE")
    out = EP._description("Hook line.\n\nSummary.\n\nChapters", [("0:00", "Intro")], {"spine": {}}, "EP", {"title": "Glass Bones", "url": "https://youtu.be/xyz"})
    assert out.startswith("Hook line.\n\nWatch next: Glass Bones https://youtu.be/xyz\n\nSummary.")
    assert "Watch next" not in EP._description("Hook.", [], {"spine": {}}, "EP")

# ------------------------------------------------------------------ the research-graded playbook
def test_vet_refuses_unsourced_gaming_duplicate_and_sets_evidence_by_code():
    have = [{"rule": "Show the promise on screen within the first thirty seconds of every video."}]
    cands = [{"rule": "Use a bright single-subject thumbnail that is readable on a phone at small size.", "department": "packager", "metric": "pack", "source_url": "https://support.google.com/youtube/answer/12340300", "evidence": "plausible"},
             {"rule": "Put one strong reveal in the middle third so viewers have a reason to keep watching.", "department": "writer", "metric": "hold", "source_url": "https://someblog.example/post", "evidence": "well-replicated"},
             {"rule": "Titles with exactly seven words always double the clicks.", "department": "packager", "metric": "pack", "source_url": ""},
             {"rule": "Ask viewers to sub4sub so the channel grows faster this month.", "department": "writer", "metric": "hold", "source_url": "https://x.example/a"},
             {"rule": "Show the promise on screen within the first thirty seconds of the video.", "department": "writer", "metric": "open", "source_url": "https://support.google.com/youtube"},
             {"rule": "A rule for a department that does not exist in this channel.", "department": "marketing", "metric": "pack", "source_url": "https://x.example/b"}]
    ok, bad = PB.vet(cands, have)
    assert [r["evidence"] for r in ok] == ["official", "plausible"] and all(r["status"] == "queued" for r in ok)
    assert sorted(w for _, w in bad) == sorted(["no source link", "games the platform or breaks policy", "repeats an existing rule", "unknown department"])
    many = [dict(cands[0], rule=f"Rule number {k} about thumbnails that is long enough to pass the length check.") for k in range(6)]
    ok, bad = PB.vet(many, []); assert len(ok) <= PB.MAX_NEW

def test_trial_coins_are_recorded_and_text_follows_them(setting):
    st = core.store(); st.append("Playbook", [
        {"rule_id": "PA", "department": "writer", "rule": "active rule", "evidence": "official", "status": "active"},
        {"rule_id": "PT", "department": "writer", "rule": "trial rule", "evidence": "plausible", "status": "trial"},
        {"rule_id": "PR", "department": "writer", "rule": "retired rule", "evidence": "plausible", "status": "retired"}])
    flags = PB.for_episode("EP1"); assert set(flags) == {"PT"} and flags == PB.for_episode("EP1")
    ons = sum(PB.coin(f"EP{k}", "PT") == "on" for k in range(200)); assert 70 < ons < 130
    assert "active rule" in PB.text_for("writer", {"PT": "off"}) and "trial rule" not in PB.text_for("writer", {"PT": "off"})
    assert "trial rule" in PB.text_for("writer", {"PT": "on"}) and "retired rule" not in PB.text_for("writer", {"PT": "on"})
    setting("PLAYBOOK_ON", "FALSE"); assert PB.text_for("writer", {"PT": "on"}) == "" and PB.for_episode("EP1") == {}

def _trial(rid, on, off, ev="plausible", n=5):
    return {"rule_id": rid, "department": "writer", "rule": f"rule {rid}", "metric": "hold", "evidence": ev, "status": "trial",
            "plays_on": n, "sum_on": round(on * n, 4), "plays_off": n, "sum_off": round(off * n, 4)}

def test_judge_promotes_retires_waits_and_fills_free_slots():
    st = core.store()
    st.append("Playbook", [_trial("UP", 0.55, 0.45), _trial("DOWN", 0.40, 0.50), _trial("FLAT", 0.50, 0.50), _trial("OFF15", 0.5, 0.5, "official", 15),
                           {"rule_id": "Q1", "department": "writer", "rule": "queued one", "metric": "hold", "status": "queued"}])
    ch = {rid: new for rid, new, _ in PB.judge()}
    assert ch["UP"] == "active" and ch["DOWN"] == "retired" and "FLAT" not in ch and ch["OFF15"] == "active" and ch["Q1"] == "trial"
    assert any(r["action"] in ("kept", "rolled_back") for r in st.rows("Strategy_Log"))

def test_research_failure_never_raises_and_trend_scout_completes():
    def boom(*a, **k): raise RuntimeError("search quota exhausted")
    assert PB.research(ask_fn=boom)["status"] == "failed"
    MG.trend_scout()        # fake mode: the weekly job still finishes, the vetted rule is queued, the bad ones refused
    rs = core.store().rows("Playbook"); assert any(r.get("evidence") == "official" and r.get("added") != "seed" for r in rs)
    assert not any("sub4sub" in r.get("rule", "") for r in rs)

# v12 B0b: the test of the mirror files of the old upload package was removed. It looked for a documents folder NEXT TO the repo that exists neither on
# GitHub nor in the v12 layout, so it skipped on every machine and proved nothing; that package and its kernel document are history (docs/ARCHIVE).


# ---------------- v8.7 review fixes (found while verifying the build) ----------------
def test_official_label_needs_a_youtube_published_page_not_any_youtube_link():
    from whatifs import playbook as PB
    assert PB.is_official("https://support.google.com/youtube/answer/9314415")
    assert PB.is_official("https://blog.youtube/news-and-events/x") and PB.is_official("https://developers.google.com/youtube/analytics/metrics")
    assert PB.is_official("https://www.youtube.com/@CreatorInsider/videos") and PB.is_official("https://youtube-creators.googleblog.com/2020/x")
    assert not PB.is_official("https://www.youtube.com/watch?v=abc123")          # anyone's video
    assert not PB.is_official("https://www.youtube.com/@creatorinsiderfan/videos")  # look-alike handle
    assert not PB.is_official("https://support.google.com/mail/answer/1") and not PB.is_official("https://evil-youtube.com/x") and not PB.is_official("")
    assert PB.evidence_label("https://www.youtube.com/watch?v=abc123", "official") == "plausible"

def test_policy_pause_uses_the_strict_official_test(setting):
    from whatifs import manage as MG
    setting("GUARDIAN_NEEDS_OFFICIAL", "TRUE")
    assert MG._official("https://support.google.com/youtube/answer/1") and not MG._official("https://www.youtube.com/watch?v=planted1234")

def test_ctr_above_half_is_always_read_as_a_percentage():
    from whatifs import growth as GR
    assert GR.ctr_ratio(4.2) == pytest.approx(0.042) and GR.ctr_ratio(0.9, impressions=10, views=100) == pytest.approx(0.009)
    assert GR.ctr_ratio(0.05, impressions=1000, views=60) == pytest.approx(0.05) and GR.ctr_ratio(5.0, impressions=1000, views=60) == pytest.approx(0.05)
    assert GR.ctr_ratio(None) is None and GR.ctr_ratio(-1) is None


def test_rehearsal_voice_samples_never_overwrite_the_repo_folder(tmp_path, monkeypatch):
    import whatifs.voice_lab as VL
    calls = []
    def fake_narrate(script, blend, out_base, **kw):
        calls.append(out_base); raise RuntimeError("stop after the path is chosen")
    monkeypatch.setattr(VL, "narrate", fake_narrate)
    with pytest.raises(RuntimeError): VL.main(backend=object())
    assert calls and calls[0].startswith(os.path.join(core.WORK, "voice_samples")) and not calls[0].startswith("voice_samples")

def test_critic_rewrite_carries_the_open_retention_problems(monkeypatch, setting):
    """v8.7 review fix: the critic's full rewrite used to start from the brief again and could undo the retention fix; the problems still open now ride in the
    same rewrite call (no extra cost). With the gate off nothing is added."""
    for gate in ("TRUE", "FALSE"):
        setting("RETENTION_GATE_ON", gate); seen = []
        real_ask = ROOM.ask
        def spy(role, system, prompt, **kw):
            if kw.get("fake_key") == "writer" and "CRITIC FIXES" in prompt: seen.append(prompt)      # v8.11: the fixes ride in the user message (the brief stays cached)
            return real_ask(role, system, prompt, **kw)
        monkeypatch.setattr(ROOM, "ask", spy)
        monkeypatch.setattr(ROOM, "critic", lambda spine, script, ctx, ep: {"verdict": "REVISE", "fixes": {"writer": "sharper"}, "scores": {"policy_safe": 9}, "mean": 6.0})
        monkeypatch.setattr(GR, "retention_issues", lambda *a, **k: {"ok": False, "issues": ["holding: 120 s without a re-hook (2:00-4:00)"], "max_gap": 120.0, "total": 500.0})
        d = DRAW("EPCRIT" + gate, "collective"); d["budget"] = {"tier": "full"}
        ROOM.run_room(d, "EPCRIT" + gate)
        assert seen, "the critic rewrite did not run"
        assert ("RETENTION FIXES STILL OPEN" in seen[0] and "2:00-4:00" in seen[0]) == (gate == "TRUE")
        monkeypatch.undo()
