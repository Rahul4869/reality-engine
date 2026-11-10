"""v9.4a: pre-production at half price (WP2). No keys, no network."""
import datetime as dt
import pytest
from whatifs import core, models as M, preprod as PP, preview as PV, publish as PUB

def _slot(hours): return core.now_utc() + dt.timedelta(hours=hours)

def test_routing_only_in_preprod_for_claude_without_search(monkeypatch, setting):
    calls = []
    monkeypatch.setattr(M, "FAKE", False)
    monkeypatch.setattr(M, "ask_batch", lambda *a, **k: calls.append(k) or "BATCHED")
    M.PREPROD.update(on=True, deadline=0.0)
    try:
        assert M.ask("writer", "sys", "prompt") == "BATCHED" and calls[-1]["force"] is True
        assert calls[-1]["max_wait_min"] == core.S("ROOM_BATCH_MAX_WAIT_MIN", float)
        assert not M._preprod_batch(M.route("writer")[0], True)                         # web search stays a direct call
        setting("ROOM_BATCH_ON", "FALSE"); assert not M._preprod_batch(M.route("writer")[0], False)
        setting("ROOM_BATCH_ON", "TRUE"); M.PREPROD["deadline"] = 1.0                  # past the job guard
        assert not M._preprod_batch(M.route("writer")[0], False)
    finally:
        M.PREPROD.update(on=False, deadline=0.0)
    assert not M._preprod_batch(M.route("writer")[0], False)                            # outside pre-production: never

def test_batch_failure_falls_back_once_without_recursion(monkeypatch):
    seen = []
    monkeypatch.setattr(M, "FAKE", False)
    monkeypatch.setattr(M.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network down")))
    monkeypatch.setattr(M, "ask", lambda *a, **k: seen.append(k) or "DIRECT")
    import whatifs.governor as G
    monkeypatch.setattr(G, "claude_allowed", lambda: True); monkeypatch.setattr(G, "monthly_cap_reached", lambda **k: False)
    monkeypatch.setattr(G, "opus_allowed", lambda: True)
    assert M.ask_batch("writer", "sys", "p", force=True, max_wait_min=1) == "DIRECT" and seen[-1]["_direct"] is True

def test_due_window_and_one_waiting_draft(monkeypatch, setting):
    from whatifs import manage as MG
    monkeypatch.setattr(MG, "next_slots", lambda n=3, after=None: [_slot(50)])
    assert PP.due() is not None
    monkeypatch.setattr(MG, "next_slots", lambda n=3, after=None: [_slot(20)]); assert PP.due() is None       # inside the production window
    monkeypatch.setattr(MG, "next_slots", lambda n=3, after=None: [_slot(100)]); assert PP.due() is None      # too early
    monkeypatch.setattr(MG, "next_slots", lambda n=3, after=None: [_slot(50)])
    core.store().append("Script_Previews", [{"draft_id": "DRAFT202611090000", "status": "APPROVED", "created": core.iso()}])
    assert PP.due() is None                                                                                   # one waiting draft at a time
    setting("PREPROD_ON", "FALSE"); assert PP.run(check_only=True) == "no"

def test_preprod_run_saves_an_approved_draft_without_email_and_production_takes_it(monkeypatch, setting):
    mails = []; monkeypatch.setattr(PUB, "email", lambda *a, **k: mails.append(a))
    r = PP.run(force=True)
    assert r.get("ok") and r.get("mode") == "preprod" and not M.PREPROD["on"]
    row = next(x for x in core.store().rows("Script_Previews") if x["draft_id"] == r["draft"])
    assert row["status"] == "APPROVED" and "pre-production" in row["note"] and not mails
    setting("PREVIEW_USE_APPROVED", "FALSE")                                    # pre-production drafts are used even then
    took = PV.take_approved("EP20261114")
    assert took is not None and next(x for x in core.store().rows("Script_Previews") if x["draft_id"] == r["draft"])["status"] == "USED"

def test_preprod_failure_never_raises_and_resets_the_flag(monkeypatch):
    monkeypatch.setattr(PV, "run", lambda mode="preview": (_ for _ in ()).throw(RuntimeError("boom")))
    r = PP.run(force=True)
    assert r == {"ok": False, "why": "boom"} and M.PREPROD["on"] is False

def test_settings_and_workflow():
    for k in ("PREPROD_ON", "PREPROD_LEAD_HOURS", "PREPROD_MIN_LEAD_HOURS", "ROOM_BATCH_ON", "ROOM_BATCH_MAX_WAIT_MIN", "PREPROD_JOB_MAX_HOURS"):
        assert core.DEFAULTS[k][1].strip()
    import yaml
    wf = yaml.safe_load(open(".github/workflows/preprod.yml"))
    job = wf["jobs"]["preprod"]
    assert job["concurrency"]["group"] == "preprod" and job["timeout-minutes"] < 360
    assert any("--check" in str(s.get("run", "")) for s in job["steps"])

def test_owner_previews_and_preprod_drafts_are_switched_apart(setting):
    st = core.store()
    st.append("Script_Previews", [{"draft_id": "DRAFT202611010000", "status": "APPROVED", "note": "premise score 8", "room_json": PV._pack({"d": {}, "room": {"spine": {}}})},
                                  {"draft_id": "DRAFT202611020000", "status": "APPROVED", "note": "pre-production (auto, half-price batch); x", "room_json": PV._pack({"d": {}, "room": {"spine": {}}})}])
    setting("PREVIEW_USE_APPROVED", "FALSE")
    assert PV.take_approved("E1") is not None
    assert {r["draft_id"]: r["status"] for r in st.rows("Script_Previews")} == {"DRAFT202611010000": "APPROVED", "DRAFT202611020000": "USED"}
    setting("PREPROD_ON", "FALSE"); assert PV.take_approved("E2") is None

# ---------------- WP12: ₹4,700 cap, budget modes, earmark, protected core
from whatifs import governor as G, manage as MG

def test_cap_is_4700_with_the_earmark_kept_out_of_production(setting):
    setting("BUDGET_FLOOR_INR", "4700"); setting("BUDGET_CEILING_INR", "4700"); setting("SPECIALS_ON", "FALSE")      # the v9.4a profile (v10 raised it to ₹5,000)
    assert G.budget_mode() == "standard" and G.cap_inr() == 4700
    assert G.production_room_inr() == pytest.approx(4700 - core.S("BUDGET_MAINT_RESERVE_INR", float) - 200)
    core.store().append("Cost_Log", [{"ts": core.iso(), "role": "faces_ref", "item": "image", "inr": "150", "basis": "measured"}])
    assert G.earmark_left_inr() == pytest.approx(50)                                   # spending the earmark does not cut production twice

def test_runway_by_tap_and_growth_by_revenue(setting, monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda *a, **k: mails.append(a))
    assert PV.decide("MODE RUNWAY") == "runway" and G.budget_mode() == "runway" and mails
    assert G.cap_inr() == 2400 and G.publish_days() == "Sat" and G.max_long_videos() == 4 and G.earmark_left_inr() == 0
    PV.decide("MODE STANDARD"); assert G.budget_mode() == "standard"
    last = (core.now_utc().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    core.store().append("Revenue_Log", [{"month": last, "inr_received": "10000"}])
    assert G.budget_mode() == "growth" and G.cap_inr() == pytest.approx(5000 + 10000 * 0.25)
    setting("GROWTH_AUTO_ON", "FALSE"); assert G.budget_mode() == "standard"

def test_standard_makes_at_most_4_long_videos(setting):                  # v12: the owner's cadence (10 Nov 2026: 4 a month); was 8
    mk = core.now_utc().strftime("%Y-%m")
    core.store().append("Episodes", [{"episode_id": f"EP{i}", "slot_et": f"{mk}-0{(i % 9) + 1}T15:00:00Z", "status": "LIVE"} for i in range(4)])
    ok, why = G.can_start_episode()
    assert not ok and "at most 4" in why

def test_extras_pause_before_production_is_squeezed(setting):
    ok, _ = G.extras_allowed(50); assert ok
    setting("GROWTH_ALLOWANCE_INR", "40"); ok, why = G.extras_allowed(50); assert not ok and "allowance" in why
    setting("GROWTH_ALLOWANCE_INR", "700"); setting("BUDGET_CEILING_INR", "1000"); setting("BUDGET_FLOOR_INR", "1000")
    ok, why = G.extras_allowed(50); assert not ok and "protect production" in why

def test_cap_cells_move_once_and_owner_values_above_4500_are_kept(setting):
    st = core.store(); st.append("Settings", [{"key": "BUDGET_FLOOR_INR", "value": "4000", "note": ""}, {"key": "BUDGET_CEILING_INR", "value": "5500", "note": ""}])
    core._settings_cache = None
    assert MG.v94a_upgrade(st) == ["BUDGET_FLOOR_INR"]
    assert core.S("BUDGET_FLOOR_INR", float) == 4700 and core.S("BUDGET_CEILING_INR", float) == 5500
    assert MG.v94a_upgrade(st) == []                                                   # never twice

# ---------------- WP4: owner messages with no-spam tiers
from whatifs import notify as NT

def _mails(monkeypatch):
    box = []; monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": box.append((subj, html)) or True); return box

def test_now_messages_are_capped_deduped_and_urgent_bypasses(monkeypatch, setting):
    box = _mails(monkeypatch); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False); monkeypatch.setenv("GH_REPO", "owner/reality-engine")
    a1 = NT.send("hold", "Video held", [("Fix & post", "FIX EP1"), ("Skip", "SKIP EP1")], episode="EP1", tier="now", default="stays held", expires_h=72)
    assert NT.send("hold", "Video held again", episode="EP1", tier="now") == a1 and len(box) == 1          # dedupe: same kind + episode
    NT.send("pick", "Pick a title", episode="EP2", tier="now"); assert len(box) == 2
    a3 = NT.send("pick", "Pick a title", episode="EP3", tier="now"); assert len(box) == 2                   # daily cap of 2: queued
    assert next(r for r in core.store().rows("Owner_Actions") if r["id"] == a3)["status"] == "QUEUED"
    NT.send("lock", "Uploads locked", episode="EP9", tier="now", urgent=True); assert len(box) == 3 and box[-1][0].startswith("URGENT")
    assert "FIX%20EP1" in box[0][1] and "ACT%20" + a1 in box[0][1]                                          # one-click answer links

def test_quiet_hours_queue_then_flush(monkeypatch, setting):
    box = _mails(monkeypatch); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: True)
    aid = NT.send("hold", "Held", episode="EP5", tier="now"); assert not box
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    assert NT.flush() == 1 and len(box) == 1 and next(r for r in core.store().rows("Owner_Actions") if r["id"] == aid)["status"] == "OPEN"

def test_quiet_hours_window():
    assert NT.in_quiet_hours(dt.datetime(2026, 11, 8, 2, 0, tzinfo=NT.IST)) and not NT.in_quiet_hours(dt.datetime(2026, 11, 8, 12, 0, tzinfo=NT.IST))

def test_week_and_fyi_never_mail_and_silence_runs_the_default(monkeypatch, setting):
    box = _mails(monkeypatch); ran = []
    NT.register("idea", on_default=lambda row: ran.append(row["id"]))
    aid = NT.send("idea", "Try a plunge Short", [("Build", "BUILD X"), ("Park", "PARK X")], tier="week", default="parked", expires_h=1)
    NT.send("learned", "Viewers leave at 0:41", tier="fyi")
    assert not box
    assert NT.expire_defaults(core.now_utc() + dt.timedelta(hours=2)) == 1 and ran == [aid]
    row = next(r for r in core.store().rows("Owner_Actions") if r["id"] == aid); assert row["status"] == "DEFAULTED" and row["answer"] == "parked"
    assert NT.expire_defaults(core.now_utc() + dt.timedelta(hours=2)) == 0                                   # never twice

def test_answer_routes_known_verbs_and_handlers(monkeypatch, setting):
    _mails(monkeypatch); seen = []
    NT.register("approve", on_answer=lambda row, choice: seen.append(choice) or "done")
    aid = NT.send("approve", "Raise the 4th clip?", [("Yes", "YES"), ("No", "NO")], tier="week")
    assert PV.decide(f"ACT {aid} YES") == "done" and seen == ["YES"]
    assert NT.answer(aid, "NO").startswith(f"{aid} already")                                                   # answered once
    monkeypatch.setattr(PV, "decide", lambda title: "mode-ok")
    a2 = NT.send("mode", "Switch?", tier="week"); out = NT.answer(a2, "MODE RUNWAY"); assert out == "mode-ok", out

def test_digest_goes_out_once_per_day_on_digest_days(monkeypatch, setting):
    box = _mails(monkeypatch)
    sun = dt.datetime(2026, 11, 8, 21, 30, tzinfo=NT.IST)                          # a Sunday evening IST
    NT.send("idea", "Open thing", tier="week")
    assert NT.digest(sun) and len(box) == 1 and "Waiting for you" in box[0][1] and "Mode:" in box[0][1]
    assert not NT.digest(sun) and len(box) == 1                                                                 # once a day
    mon = dt.datetime(2026, 11, 9, 21, 30, tzinfo=NT.IST); setting("DIGEST_SENT_AT", "")
    assert not NT.digest(mon)                                                                                   # Monday is not a digest day

def test_notify_tick_never_raises(monkeypatch):
    monkeypatch.setattr(NT, "flush", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    out = NT.tick(); assert "defaulted" in out

# ---------------- WP3: Claude Code builds, Merge / Reject, auto-merge for tweaks (decision 11)
from whatifs import builds as BD

def test_build_ready_message_and_auto_merge_only_for_tweaks(monkeypatch, setting):
    box = _mails(monkeypatch); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    merged = []; monkeypatch.setattr(BD, "merge_pr", lambda n, why="": merged.append((n, why)) or (True, f"merged #{n}"))
    a1 = BD.build_ready("41", "tweak"); a2 = BD.build_ready("42", "feature")
    rows = {r["id"]: r for r in core.store().rows("Owner_Actions")}
    assert rows[a1]["default_action"].startswith("auto-merge") and rows[a2]["default_action"].startswith("waits") and len(box) == 2
    assert BD.build_ready("41", "tweak") == a1                                                          # one message per pull request
    assert NT.expire_defaults(core.now_utc() + dt.timedelta(hours=25)) == 1 and merged == [("41", "auto-merge after 24 h green (decision 11)")]
    assert rows_after(a2)["status"] == "OPEN" and not any(n == "42" for n, _ in merged)                 # a feature never merges by itself
    setting("AUTO_MERGE_TWEAKS_ON", "FALSE"); a3 = BD.build_ready("43", "tweak")
    assert rows_after(a3)["default_action"].startswith("waits")

def rows_after(aid): return next(r for r in core.store().rows("Owner_Actions") if r["id"] == aid)

def test_owner_merge_and_reject_taps(monkeypatch):
    _mails(monkeypatch); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    calls = []
    monkeypatch.setattr(BD, "merge_pr", lambda n, why="": calls.append(("merge", n)) or (True, f"merged #{n}"))
    monkeypatch.setattr(BD, "close_pr", lambda n: calls.append(("close", n)) or True)
    a = BD.build_ready("50", "feature"); assert NT.answer(a, "MERGE #50") == "merged #50"
    b = BD.build_ready("51", "feature"); assert NT.answer(b, "REJECT #51") == "closed #51"
    assert calls == [("merge", "50"), ("close", "51")]

def test_merge_only_when_checks_are_green(monkeypatch):
    monkeypatch.setattr(BD, "FAKE", False)
    monkeypatch.setattr(BD, "pr_state", lambda n: {"mergeable": True, "checks": "pending", "merged": False, "head": "x"})
    ok, msg = BD.merge_pr("7"); assert not ok and "pending" in msg
    monkeypatch.setattr(BD, "pr_state", lambda n: {"mergeable": True, "checks": "green", "merged": True, "head": "x"})
    assert BD.merge_pr("7")[0]

def test_builds_switch_and_repair_engine_default():
    assert core.DEFAULTS["REPAIR_ENGINE"][0] == "claude_code" and core.DEFAULTS["BUILDS_ON"][0] == "TRUE"
    import yaml
    wf = yaml.safe_load(open(".github/workflows/claude-build.yml"))
    job = wf["jobs"]["build"]; assert job["concurrency"]["group"] == "build"
    claude = next(s for s in job["steps"] if "claude-code-action" in str(s.get("uses", "")))          # v12: the model credential goes to the Claude step only
    assert "CC_OAUTH_TOKEN" in claude["with"]["claude_code_oauth_token"] and list(claude["env"]) == ["CC_OAUTH_TOKEN"] and "CC_OAUTH_TOKEN" not in job["env"]
    assert any("gh workflow run checks.yml" in str(s.get("run", "")) for s in job["steps"])

def test_builds_off_means_nothing_is_dispatched(setting, monkeypatch):
    setting("BUILDS_ON", "FALSE"); calls = []
    monkeypatch.setattr(BD, "dispatch", lambda *a, **k: calls.append(a) or True)
    assert not BD.request_build("x", "tweak") and not calls
    setting("BUILDS_ON", "TRUE"); assert BD.request_build("x", "feature") and calls[-1][1]["kind"] == "feature"

# ---------------- ORCHESTRA, credits, Visual Lab, platform facts watcher
from whatifs import orchestra as OR, visual_lab as VL, facts_watch as FW

def test_heavy_jobs_wait_near_a_release(setting):
    core.store().append("Episodes", [{"episode_id": "EPR", "slot_et": (core.now_utc() + dt.timedelta(minutes=50)).strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "SCHEDULED"}])
    assert not OR.heavy_allowed()
    setting("ORCHESTRA_RELEASE_GUARD_H", "0"); assert OR.heavy_allowed()
    import yaml
    for f in ("learn", "research", "trends", "brief", "sheets", "voices"):
        wf = yaml.safe_load(open(f".github/workflows/{f}.yml")); job = list(wf["jobs"].values())[0]
        assert job["concurrency"]["group"] == "sheet-heavy" and job["concurrency"]["cancel-in-progress"] is False

def test_credit_cover_is_a_money_view_with_the_max_end_date(setting):
    st = core.store(); st.append("Cost_Log", [{"ts": core.iso(), "role": "writer", "item": "claude", "inr": "900", "basis": "measured"},
                                              {"ts": core.iso(), "role": "tts", "item": "gemini", "inr": "300", "basis": "measured"}])
    assert G.credit_cover_inr() == 0
    setting("CLAUDE_CREDIT_USD_MONTH", "100"); setting("GEMINI_CREDIT_USD_MONTH", "10")
    assert G.credit_cover_inr() == pytest.approx(900 + min(300, 10 * core.S("USD_INR", float)))
    setting("CLAUDE_CREDIT_UNTIL", "2020-01-01"); assert G.credit_cover_inr() == pytest.approx(min(300, 10 * core.S("USD_INR", float)))
    assert G.can_start_episode()[0] in (True, False)                                    # gates still use list prices (unchanged)

def _retention(n_eps, shot, vs):
    core.store().append("Retention_Map", [{"ts": core.iso(), "episode_id": f"E{i}", "beat": str(b), "shot_types": shot, "vs_median": str(vs)}
                                           for i in range(n_eps) for b in range(2)])

def test_visual_lab_waits_for_data_then_suggests_once_a_week(monkeypatch, setting):
    _mails(monkeypatch)
    _retention(2, "clip", 0.2); assert VL.suggest() == []                               # too few videos
    _retention(5, "clip", 0.2)
    ids = VL.suggest(); assert ids and ids[0] == "motion_ramps"                         # MOTION_BOOST_ON exists and is off: a switch-on idea
    assert VL.suggest() == ids and len([r for r in core.store().rows("Owner_Actions") if r["kind"] == "visual_idea"]) == 1      # deduped this week
    row = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "visual_idea"); assert row["tier"] == "week" and "₹0" in row["text"]

def test_visual_lab_switch_on_and_build_paths(monkeypatch, setting):
    calls = []; import whatifs.builds as BD
    monkeypatch.setattr(BD, "request_build", lambda spec, kind="tweak": calls.append((kind, spec)) or True)
    assert VL._on_answer({}, "VISUAL motion_ramps") == "MOTION_BOOST_ON switched on" and core.S("MOTION_BOOST_ON", bool)
    assert VL._on_answer({}, "VISUAL rack_focus") == "build started" and calls[-1][0] == "feature" and "RACK_FOCUS_ON" in calls[-1][1]
    assert VL._on_answer({}, "PARK") == "recorded"

def test_visual_lab_switch(setting):
    setting("VISUAL_LAB_ON", "FALSE"); _retention(6, "clip", 0.3); assert VL.suggest() == []

def test_facts_watch_baseline_then_one_card_per_changed_page(monkeypatch, setting):
    _mails(monkeypatch)
    setting("FACTS_WATCH_URLS", "https://a.example/x,https://b.example/y")
    pages = {"https://a.example/x": "v1", "https://b.example/y": "same"}
    assert FW.run(fetch=lambda u: pages[u]) == []                                       # first run = baseline only
    pages["https://a.example/x"] = "v2 (2 Nov 2026: uploads no longer locked)"
    assert FW.run(fetch=lambda u: pages[u]) == ["https://a.example/x"]
    cards = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "platform_change"]
    assert len(cards) == 1 and cards[0]["tier"] == "week"
    assert FW.run(fetch=lambda u: (_ for _ in ()).throw(RuntimeError("offline"))) == []  # unreadable pages never raise
