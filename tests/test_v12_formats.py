"""v12 V2a - formats as data and the three-tier contract: an episode has a FORMAT (F1 "The day it changed", F2 "The trial"); a format can make the
show's DEVICES optional or leave them out, and nothing else. Every rule is proven both ways; the real room and the real production are run."""
import datetime as dt, json, os, re
import pytest
from whatifs import core, contract as CON, models as M, formats as FMT, room as ROOM, room2 as R2
from whatifs.sampler import draw as DRAW
from whatifs.org import registry as REG, levers as LV, runner as RUN, rnd as RND

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()
def ctx(text, **k): return dict({"room": {"script": {"script": text}}}, **k)
BARE = "## BEAT 1\n[DIRECTOR] You stop brushing. Your reflection does not.\n[SKEPTIC] It is late. Why is it late?\n" * 6
COURT = BARE + "[SKEPTIC] Objection! Exhibit A proves it, Your Honour.\n[JUDGE] The court will rise.\n"

# ------------------------------------------------------------------ the table
def test_a_format_can_only_loosen_devices_never_a_core_viewer_or_organisation_check():
    ids = {f[0] for f in CON.FEATURES}
    assert set(FMT.DEVICES) <= ids and not any(d.startswith("viewer_") for d in FMT.DEVICES) and not set(FMT.DEVICES) & set(RND.ORG_CHECKS)
    for k, f in FMT.FORMATS.items():
        assert set(f["devices"]) <= set(FMT.DEVICES) and set(f["devices"].values()) <= set(FMT.RULES) and f["status"] in ("on", "later"), k
    assert FMT.FORMATS["F2"]["devices"] == {} and all(FMT.rule(d, "F2") == "must" for d in FMT.DEVICES)          # the trial keeps every device
    assert FMT.rule("joke_density", "F1") == "advisory" and FMT.rule("exhibits", "F1") == "never" and FMT.rule("joke_density", "") == "must"
    for hard in ("viewer_numbers", "viewer_plain", "originality", "research", "dept_contract", "format_kept"): assert FMT.rule(hard, "F1") == "must", hard

# ------------------------------------------------------------------ which format an episode gets
def test_the_format_of_a_new_episode(setting):
    assert FMT.pick("EPA") == "F2"                                                    # the test setup forces the trial for the older tests
    setting("FORMAT_FORCE", "")
    got = [FMT.pick(f"EP{i:04d}") for i in range(300)]; share = got.count("F1") / 300
    assert set(got) == {"F1", "F2"} and 0.6 < share < 0.8 and FMT.pick("EP0007") == got[7]          # the first episode of a Sheet is drawn by its id
    setting("FORMAT_FORCE", "f1"); assert FMT.pick("EPA") == "F1"
    setting("FORMAT_FORCE", "F3"); assert {FMT.pick(f"EP{i:04d}") for i in range(40)} == {"F3"}               # v12 V2b: F3 is a format now: it can be forced
    setting("FORMAT_FORCE", ""); assert FMT.pick("EPA", {"deep_trial": True}) == "F2"
    os.environ["WI_FORMAT"] = "F1"
    try: setting("FORMAT_FORCE", "F2"); assert FMT.pick("EPA") == "F1"                 # the env var wins (a rehearsal or a sweep of one format)
    finally: del os.environ["WI_FORMAT"]; setting("FORMAT_FORCE", "")
    setting("FORMATS_ON", "FALSE"); assert FMT.pick("EPA") == ""; setting("FORMATS_ON", "TRUE")
    setting("SHOW_MODE", "off"); assert {FMT.pick(f"EP{i:04d}") for i in range(40)} == {"F1"}; setting("SHOW_MODE", "auto")     # no trial without the show's world
    setting("FORMAT_SHARE_F1", "0"); assert {FMT.pick(f"EP{i:04d}") for i in range(40)} == {"F2"}
    setting("FORMAT_SHARE_F2", "0"); assert FMT.pick("EPA") == "F1"                    # nothing left to draw from: the default format

def test_the_shares_are_kept_over_the_last_ten_episodes_not_by_a_coin(setting):
    setting("FORMAT_FORCE", ""); st = core.store(); seq = []
    for i in range(10):
        ep = f"EPQ{i:02d}"; f = FMT.pick(ep) if i else "F1"; seq.append(f)
        st.append("Episodes", [{"episode_id": ep, "status": "PUBLISHED", "draw_json": {"format": f}, "updated": core.iso()}])
    assert seq[:6] == ["F1", "F2", "F1", "F1", "F1", "F2"] and seq.count("F1") == 7 and seq.count("F2") == 3
    assert FMT.pick("EPQ01") == "F2" and FMT.pick("EPQ02") == "F1"                     # an episode that has a format keeps it (a retry, a resume)
    st.append("Episodes", [{"episode_id": f"EPX{i}", "status": "FAILED", "draw_json": json.dumps({"format": "F1"}), "updated": core.iso()} for i in range(6)])
    assert FMT.pick("EPNEW") == FMT.pick("EPNEW2") == "F1"                             # failed episodes do not count (counted, six failed F1 would make F2 the next one)

# ------------------------------------------------------------------ the trial layer and the writers follow the format
def test_the_trial_layer_follows_the_format_and_the_context_is_always_restored():
    from whatifs import show as SHOW
    assert FMT.current() == "" and SHOW.on() and SHOW.leads_on() and FMT.block("writer") == ""
    with FMT.using("F1"):
        w = FMT.block("writer")
        assert FMT.current() == "F1" and not SHOW.on() and SHOW.leads_on() and w.startswith("FORMAT OF THIS EPISODE - F1") and "NOT a trial" in w and "TWO VOICES ONLY" in w
        assert "would you keep it" in FMT.block("bible") and "return no show_plan" in FMT.block("showrunner") and "first-person" in FMT.rubric("drafts")
        assert R2._rubric("drafts") == FMT.F1_DRAFTS and R2._rubric("jokes") == FMT.F1_JOKES
        with FMT.using("F2"): assert SHOW.on() and FMT.block("writer") == "" and R2._rubric("drafts") == R2.DRAFT_RUBRIC
        assert FMT.current() == "F1"
    assert FMT.current() == "" and R2._rubric("jokes") == R2.JOKE_RUBRIC
    FMT.use("nonsense"); assert FMT.current() == ""

def test_optional_devices_are_not_demanded_from_the_writers_and_never_forced_by_a_rewrite(monkeypatch):
    from whatifs import enforce as ENF
    assert "MANDATORY MARKERS" in ENF.writer_rules() and ENF.marker_issues(BARE)                    # no format (and the trial): as before
    seen = []; monkeypatch.setattr(M, "ask", lambda role, system, prompt, **k: seen.append(prompt) or {"script": COURT})
    with FMT.using("F1"):
        assert "optional in this format" in ENF.writer_rules() and "MANDATORY" not in ENF.writer_rules() and ENF.marker_issues(BARE) == []
        assert ENF.fix_markers({"script": BARE}, "brief", "EPT") == ({"script": BARE}, []) and seen == []
        iss = FMT.format_issues(COURT)
        assert iss and iss[0].startswith("NOT A TRIAL") and "exhibit a" in iss[0] and "your honour" in iss[0] and "JUDGE" in iss[0] and FMT.format_issues(BARE) == []
        out, issues = ENF.fix_all({"script": COURT}, "brief", {"promise": {"title": "your mirror is late"}}, "EPT")
        assert any(i.startswith("NOT A TRIAL") for i in issues) and "FORMAT FIX" in seen[0] and "MARKER FIX" not in seen[0] and len(seen) == 1
    with FMT.using("F2"): assert FMT.format_issues(COURT) == [] and ENF.marker_issues(BARE)

def test_the_real_room_writes_in_its_format_and_hands_the_briefs_to_the_showrunner_the_bible_and_the_writer(monkeypatch, setting):
    from whatifs import manage as MG
    MG.setup(); setting("FORMAT_FORCE", "F1"); seen = []
    def spy(mod):
        real = mod.ask
        def f(role, system, prompt, **kw): seen.append((role, str(system) + "\n" + str(prompt), FMT.current())); return real(role, system, prompt, **kw)
        monkeypatch.setattr(mod, "ask", f)
    spy(ROOM)
    if hasattr(R2, "ask"): spy(R2)
    d = DRAW("EPF1", "collective"); room = ROOM.run_room(d, "EPF1")
    assert d["format"] == "F1" and FMT.current() == "" and not d.get("show_plan") and not room["spine"].get("show_plan")
    assert seen and all(f == "F1" for _r, _t, f in seen)                              # every call of the room was made in the episode's format
    by = lambda role: [t for r, t, _f in seen if r == role]
    assert any("return no show_plan" in t for t in by("showrunner")) and not any("show_plan" in t and "charge" in t and "jury_prompts" in t for t in by("showrunner"))
    assert any("THE IMPOSSIBLE PICTURE" in t for t in by("bible")) and any("TWO VOICES ONLY" in t and "optional in this format" in t for _r, t, _f in seen)          # the writer's brief (it is the system text of the room's own passes)
    assert not any("REALITY ON TRIAL - write this episode as a trial" in t for _r, t, _f in seen)
    assert FMT.kept_report(room["script"]["script"], "F1")["problems"] == []
    seen.clear(); setting("FORMAT_FORCE", "F2"); d2 = DRAW("EPF2", "collective"); ROOM.run_room(d2, "EPF2")
    assert d2["format"] == "F2" and d2.get("show_plan") and any("REALITY ON TRIAL - write this episode as a trial" in t for _r, t, _f in seen)
    assert not any("FORMAT OF THIS EPISODE - F1" in t for _r, t, _f in seen)

# ------------------------------------------------------------------ the three-tier contract
def test_a_device_is_judged_by_the_episodes_format_and_nothing_else_is_loosened(monkeypatch):
    F = CON.FAIL
    monkeypatch.setattr(CON, "FEATURES", [("joke_density", "script", lambda c: (F, "2 punchlines (need 9)"), "j"), ("exhibits", "script", lambda c: (F, "no exhibits"), "e"),
                                          ("viewer_numbers", "script", lambda c: (F, "a flood"), "v"), ("originality", "script", lambda c: (F, "a near-copy"), "o")])
    run = lambda fmt: CON.run("script", {"d": {"format": fmt}}, "EPF", write=False)
    f1 = {r["feature"]: (r["status"], r["evidence"]) for r in run("F1")["rows"]}
    assert f1["joke_density"] == (CON.NA, "optional in format F1, not held: 2 punchlines (need 9)") and f1["exhibits"] == (CON.NA, "not part of format F1 (The day it changed)")
    assert [f for f, _ in run("F1")["failed"]] == ["viewer_numbers", "originality"] and not run("F1")["ok"]          # tier 1 and tier 2 hold in every format
    assert [f for f, _ in run("F2")["failed"]] == [f for f, _ in run("")["failed"]] == ["joke_density", "exhibits", "viewer_numbers", "originality"]

def test_format_kept_holds_a_script_that_sounds_like_a_trial_in_a_format_that_is_not_one():
    ok = "[DIRECTOR] You stop brushing. Your reflection does not.\n[SKEPTIC] So what is your verdict? Would you keep it? Trial and error, I suppose."
    s, ev = CON.p_format_kept(ctx(ok, d={"format": "F1"})); assert s == CON.PASS and "0 required, 5 optional, 5 not part of it" in ev          # ordinary uses of the words stay free
    s, ev = CON.p_format_kept(ctx(ok + "\n[WITNESS] Exhibit B, Your Honor. Dr. Grimm objects.", d={"format": "F1"}))
    assert s == CON.FAIL and "exhibit b" in ev and "your honor" in ev and "grimm" in ev and "WITNESS" in ev
    assert CON.p_format_kept(ctx(ok, d={}))[0] == CON.NA and CON.p_format_kept(ctx(ok, d={"format": "F2"}))[0] == CON.FAIL
    s, ev = CON.p_format_kept(ctx(COURT, d={"format": "F2", "show_plan": {"charge": "x"}})); assert s == CON.PASS and "10 required" in ev

def test_formats_are_wired_owned_and_ruled():
    stage = {f[0]: f[1] for f in CON.FEATURES}
    assert stage["format_kept"] == "script" and REG.check_owner("format_kept") == "D4" and "format_kept" not in RND.ORG_CHECKS and "format_kept" in RND.metrics()
    for k in ("FORMAT_SHARE_F1", "FORMAT_SHARE_F2", "FORMAT_SHARE_F3"): assert REG.may_change("D1", k) and LV.LEVERS[k]["hi"] == 100 and LV.LEVERS[k]["step"] == 20, k
    assert not REG.data_issues() and LV.issues() == [] and not REG.entry_issues()
    core.set_setting("FORMAT_FORCE", ""); core._settings_cache = None
    assert core.S("FORMAT_SHARE_F1", int) == 70 and core.S("FORMAT_SHARE_F2", int) == 30 and core.S("FORMAT_SHARE_F3", int) == 0 and core.S("FORMATS_ON", bool)
    assert "whatifs/formats.py" in open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read()
    src = open(os.path.join(ROOT, "whatifs", "room.py"), encoding="utf-8").read()
    assert all(f'_format_block("{r}")' in src for r in ("showrunner", "bible", "writer")) and "with FMT.using(draw[\"format\"]): return _run_room(draw, episode)" in src

# ------------------------------------------------------------------ the real production
def test_the_real_production_makes_an_episode_that_is_not_a_trial_and_holds_one_that_sounds_like_it(monkeypatch):
    from whatifs import episode as EP, manage as MG
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C"); core.set_setting("FORMAT_FORCE", "F1")
    slot = lambda h: (now() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    after = []                                                                        # the steps AFTER the writers' room: each must be made in the episode's format
    for step in ("package", "plan_shots"):
        monkeypatch.setattr(ROOM, step, (lambda real, step=step: lambda *a, **k: (after.append((step, FMT.current())), real(*a, **k))[1])(getattr(ROOM, step)))
    r = EP.produce(slot(10), episode_id="EP209901010900"); ep = r.get("episode"); assert r.get("ok") and FMT.current() == "", r
    assert {s for s, _f in after} == {"package", "plan_shots"} and {f for _s, f in after} == {"F1"}, after
    st = core.store(); led = {x["feature"]: (x["status"], x["evidence"]) for x in st.rows("Feature_Ledger") if x["episode_id"] == ep}
    assert led["format_kept"][0] == "PASS" and led["dept_contract"][0] == "PASS", led["format_kept"]
    assert led["joke_density"][0] == "N/A" and led["joke_density"][1].startswith("optional in format F1, not held:")           # a device was missing - and nothing was held
    for dev in ("time_ladder", "exhibits", "grimm_prototype", "verdict_line", "verdict_style"): assert led[dev] == ("N/A", "not part of format F1 (The day it changed)"), dev
    for hard in ("viewer_promise", "viewer_numbers", "viewer_breath", "viewer_plain", "viewer_probe", "originality", "retention"): assert led[hard][0] == "PASS", (hard, led[hard])
    row = next(e for e in st.rows("Episodes") if e["episode_id"] == ep); dj = row["draw_json"]; dj = json.loads(dj) if isinstance(dj, str) else dj
    assert dj["format"] == "F1" and not dj.get("show_plan")
    mine = lambda tab: [x for x in st.rows(tab) if x.get("episode_id") == ep]
    assert mine("Packaging_Tests") and mine("Experiments") and not mine("Season")        # what every format needs is kept (title and thumbnail tests, the experiment row); the trial's season row is not written
    monkeypatch.setattr(FMT, "_OTHER_VOICE", re.compile(r"\[(DIRECTOR)\]"))            # the writer keeps a voice the format does not have, and the one rewrite does not cure it
    r2 = EP.produce(slot(34), episode_id="EP209901020900")
    assert r2.get("held") and "contract:format_kept" in r2["problems"] and FMT.current() == "", r2      # (the offline writer repeats itself, so a second episode in one Sheet can also trip the originality check)
    assert not any(s["dept"] == "D9" and s["episode_id"] == r2["episode"] for s in st.rows("Sessions"))        # held before any picture was paid
