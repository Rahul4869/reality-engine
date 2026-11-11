"""v12 B4 - the Execution Engine (whatifs/org/levers.py, execute.py). Every rule is proven both ways: the lever table and its gate, each lever class
from apply through verification to rollback, the owner's approval, the between-videos rule, one unverified change per department, ledger proof on
the memo doorway, code builds and the automatic merge scope, and the two contract checks."""
import datetime as dt, json, os
import pytest
from whatifs import core, contract as CON, builds as BLD, playbook as PB
from whatifs.org import palace as P, schemas as SC, memos as MEM, registry as REG, runner as RUN, levers as LV, execute as EXE
from whatifs.org.schemas import MemoError

H, D = dt.timedelta(hours=1), dt.timedelta(days=1)

@pytest.fixture(autouse=True)
def _engine_alone():
    """The engine is judged on its own here: its department runs are code (no model call), so the creative departments stay in brief mode
    (v12 B6a puts their playbook into model prompts; that path and the cited verification it needs are tested in tests/test_v12_creative.py)."""
    core.set_setting("ORG_PROMPT_INJECT", "FALSE"); yield
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()
def today(): return core.iso()[:10]
def st(): return core.store()
def cell(k): return str(core.settings(refresh=True).get(k, "")).strip()
def trow(tid): return EXE._get(tid, st())
def ledger(tid=None): return [r for r in st().rows("Lever_Changes") if tid is None or r["ticket_id"] == tid]
def acts(tid): return [r["action"] for r in ledger(tid)]
def owner_msgs(kind): return [r for r in st().rows("Owner_Actions") if r["kind"] == kind]
def sessions_by_id(): return {s["id"]: s for s in st().rows("Sessions")}
def taker(out=None): return lambda b: (b.take(), {"x": 1} if out is None else out)[1]
def run(dept="D4", trigger="write", ep="EP1", at=None, act=None, **k):
    k.setdefault("measure", lambda o: {"units": 30})
    return RUN.run(dept, trigger, act or taker(), episode=ep, now=at, **k)
def ticket(to="D4", cls="B", target="JOKE_EVERY_SEC_LONG", value=10, frm="C", **k):
    m = {"type": "ticket", "from_dept": frm, "to_depts": [to], "subject": k.pop("subject", f"Change {target} for the next videos"),
         "body": {"lever_class": cls, "target": target, "value": value, "acceptance_test": "the next video passes its check with the new value", "rollback": "put the earlier value back"},
         "done_when": "the change is verified by later evidence or rolled back"}
    if k.get("ref"): m["body"]["decision_ref"] = k.pop("ref")
    m.update(k); return MEM.write(m)
def levers(): return {k: cell(k) for k in LV.LEVERS}
def squeeze(iid):
    """From now on the playbook of D6 has no room for this item (limits fill it to its smallest cap)."""
    core.set_setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT", '{"D6": 200}'); core.set_setting("PALACE_LIMITS_SHARE", "0.9")
    assert iid not in P.playbook("D6", record=False)["items"]
def check_row(ep, feature, status, evidence="measured by the gate"):
    st().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": ep, "stage": "script", "feature": feature, "status": status, "evidence": evidence}])
ITEM = {"kind": "technique", "title": "Open every animated scene on a slow push-in", "summary": "A slow push-in on the first animated scene holds the eye for the first three seconds of the video.",
        "departments": ["D6"], "stages": ["visual"], "topic_tags": ["camera"]}
def item(**k):
    it = dict(ITEM, evidence=[{"source": "Monitor48 rows of the last four videos", "date": today(), "type": "own data", "finding": "three of four videos with a push-in held 70% at 30 seconds"}]); it.update(k); return it
RULE = {"rule": "Open the cold open on a sensory memory before the case begins, then turn to the viewer.", "metric": "open", "source_url": "https://support.google.com/youtube/answer/12345"}
BUILD = {"spec": "Add a check that measures the silence before each punchline and fails the final gate when it is under the bar.", "files": ["whatifs/contract.py"],
         "tests_to_add": ["a test that fails when the pause before a punchline is missing"], "acceptance": "the new check is in the matrix and green"}
def applied_setting(value=10, dept="D4", target="JOKE_EVERY_SEC_LONG"):
    """A setting ticket that the engine has applied at T (now): returns (ticket, T)."""
    t = ticket(dept, "B", target, value); T = now(); run(dept, "write" if dept == "D4" else "plan", "EP1"); EXE.reconcile(now=T)
    assert trow(t["id"])["state"] == "applied", trow(t["id"])
    return t, T

# ------------------------------------------------------------------ the lever table
def test_tabs_settings_and_the_lever_table_are_honest(monkeypatch):
    assert core.TABS["Tickets"][0] == "id" and "state" in core.TABS["Tickets"] and core.TABS["Lever_Changes"][:3] == ["ts", "change_id", "ticket_id"]
    for k in ("EXEC_ON", "EXEC_VERIFY_RUNS", "EXEC_VERIFY_DAYS", "EXEC_ARM_OUTPUTS", "EXEC_RULES_PER_DEPT", "EXEC_BUILD_RETRIES", "EXEC_BUILD_WAIT_H", "EXEC_AUTO_MERGE_ON"): assert k in core.DEFAULTS
    reg = {k for v in REG.DEPTS.values() for k in v["levers"]}
    assert LV.issues() == [] and set(LV.LEVERS) == reg and len(reg) == 51 and REG.data_issues() == []
    assert all(LV.owner_of(k) and REG.may_change(LV.owner_of(k), k) for k in reg) and LV.owner_of("FAL_STILL_MODEL") == ""
    saved = LV.LEVERS.pop("ANIM_SHOTS"); assert any("ANIM_SHOTS of D6 has no rule" in x for x in LV.issues()) and any("ANIM_SHOTS" in x for x in REG.data_issues()); LV.LEVERS["ANIM_SHOTS"] = saved
    monkeypatch.setitem(LV.LEVERS, "FAL_STILL_MODEL", LV._b()); assert any("FAL_STILL_MODEL, which is no department's lever" in x for x in LV.issues()); monkeypatch.delitem(LV.LEVERS, "FAL_STILL_MODEL")
    monkeypatch.setitem(LV.LEVERS, "ANIM_SHOTS", LV._n("int", 6, 8, 1, "up", LV.COST, ("animation",))); assert any("ANIM_SHOTS: its own default 4 is outside" in x for x in LV.issues())
    monkeypatch.setitem(LV.LEVERS, "ANIM_SHOTS", LV._n("int", 2, 8, 1, "up", LV.COST, ("no_such_check",))); assert any("'no_such_check', which does not exist" in x for x in LV.issues())
    monkeypatch.setitem(LV.LEVERS, "ANIM_SHOTS", LV._n("int", 2, 8, 1, "up", "", ())); assert any("does not say why" in x for x in LV.issues())

@pytest.mark.parametrize("dept,key,value,why", [
    ("D4", "FAL_STILL_MODEL", "x", "is not a registered lever"), ("D4", "", 3, "is not a registered lever"), ("D4", "ANIM_SHOTS", 5, "is a lever of D6, not of D4"),
    ("D4", "JOKE_EVERY_SEC_LONG", "soon", "needs a whole number"), ("D4", "JOKE_EVERY_SEC_LONG", 12.5, "needs a whole number"), ("D4", "JOKE_EVERY_SEC_LONG", 5, "outside the allowed range 8 to 60"),
    ("D4", "JOKE_EVERY_SEC_LONG", 40, "more than one step (10)"), ("D6", "VISUAL_CHANGE_MAX_S", "nan", "needs a number"), ("D6", "PARTICLES_ON", "maybe", "needs TRUE or FALSE"),
    ("D4", "ROOM_MODE", "v3", "must be one of: v2, v1"), ("D1", "PUBLISH_DAYS", "Sat,Funday", "needs weekdays"), ("D8", "CONTRACT_OFF", "retention,nope", "names a check that does not exist (nope)"),
    ("L", "PALACE_KIND_CAPS", "{bad", "is not valid JSON"), ("L", "PALACE_KIND_CAPS", {"gossip": 5}, "is not one of its keys"), ("L", "PALACE_PLAYBOOK_TOKENS_BY_DEPT", {"D4": 9000}, "outside the allowed range 200 to 6000"),
    ("C", "ORG_SLA_HOURS", {"ticket": 5}, "needs two numbers"), ("C", "ORG_SLA_HOURS", {"ticket": [50, 5]}, "cannot be longer than the resolve clock"), ("L", "PALACE_REVIEW_DAYS", [1], "needs a JSON object")])
def test_a_setting_change_outside_the_rules_is_refused_never_clamped(dept, key, value, why):
    c = LV.check(dept, key, value); assert why in c["why"] and c["new"] == "", c

def test_inside_its_range_the_direction_decides_whether_the_owner_is_needed(monkeypatch):
    ok = lambda d, k, v: LV.check(d, k, v)
    assert ok("D4", "JOKE_EVERY_SEC_LONG", 10) == {"old": "15", "new": "10", "why": "", "owner": ""}                    # stricter: the department may
    assert ok("D4", "JOKE_EVERY_SEC_LONG", "25")["owner"] == LV.GATE and ok("D4", "JOKE_EVERY_SEC_LONG", 15)["owner"] == ""      # weaker: the owner; no move: nobody
    assert ok("D6", "ANIM_SHOTS", 5)["owner"] == LV.COST and ok("D6", "ANIM_SHOTS", 3)["owner"] == "" and ok("D8", "BREAKOUT_HARD_BAR", 75)["owner"] == LV.GATE and ok("D8", "BREAKOUT_HARD_BAR", 85)["owner"] == ""
    assert ok("D6", "PARTICLES_ON", "off")["new"] == "FALSE" and ok("D6", "PARTICLES_ON", False)["owner"] == LV.GATE and ok("D6", "PARTICLES_ON", True)["owner"] == ""
    assert ok("D4", "ROOM_MODE", "v1")["owner"] and not ok("D7", "TTS_ENGINE", "kokoro")["owner"] and ok("D1", "PUBLISH_DAYS", "sun, sat") == {"old": "Sat", "new": "Sat,Sun", "why": "", "owner": LV.PLAN}
    assert ok("D8", "CONTRACT_OFF", "retention")["owner"] == "it switches a promised check off" and ok("D8", "CONTRACT_OFF", "")["owner"] == ""
    assert ok("L", "PALACE_PLAYBOOK_TOKENS_BY_DEPT", '{"D4": 2400.0}')["new"] == '{"D4": 2400}' and ok("C", "ORG_SLA_HOURS", {"ticket": [12, 36]})["new"] == '{"ticket": [12.0, 36.0]}'
    assert ok("D9", "SHORTS_PER_DAY", 1)["new"] == "1" and ok("D6", "VISUAL_CHANGE_MAX_S", "3.50")["new"] == "3.5"
    assert LV.same("ANIM_SHOTS", "4", "4.0") and LV.same("PARTICLES_ON", "true", "TRUE") and not LV.same("ANIM_SHOTS", "4", "5") and LV.same("PALACE_KIND_CAPS", "", "{}") and LV.same("ROOM_MODE", "v2", "v2")
    core.set_setting("JOKE_EVERY_SEC_LONG", "soon"); assert "cannot be judged" in ok("D4", "JOKE_EVERY_SEC_LONG", 20)["owner"]          # a hand-typed non-number: the owner looks
    from whatifs import truth as TRU
    monkeypatch.setattr(TRU, "unread_settings", lambda root=None: ["ANIM_SHOTS"])
    assert "a cell no code reads" in ok("D6", "ANIM_SHOTS", 5)["why"] and any("ANIM_SHOTS is a cell no code reads" in x for x in LV.issues())

# ------------------------------------------------------------------ lever class B: a setting
def test_a_setting_waits_for_the_gap_between_videos_then_is_applied_verified_and_closed_with_ledger_proof():
    t = ticket(); r = run(); row = trow(t["id"])                                             # the ticket is executed inside the run of an episode
    assert next(x for x in r.receipts if x["step"] == "EXECUTE")["executed"] == [t["id"]] and row["state"] == "queued" and "between videos" in row["note"]
    assert cell("JOKE_EVERY_SEC_LONG") == "15" and acts(t["id"]) == ["queued"] and MEM.get(t["id"])["status"] == "in_progress"          # taken up: only the resolve clock runs now
    T = now(); st().append("Episodes", [{"episode_id": "EP1", "status": "VISUALS", "updated": core.iso(T)}])
    assert EXE.reconcile(now=T + H)["moved"] == {} and cell("JOKE_EVERY_SEC_LONG") == "15"          # a video is being made: nothing changes under it
    st().update("Episodes", "episode_id", "EP1", {"status": "UPLOADED"})
    assert EXE.reconcile(now=T + H)["moved"] == {t["id"]: "queued -> applied"} and cell("JOKE_EVERY_SEC_LONG") == "10"
    row = trow(t["id"]); m = MEM.get(t["id"]); lg = ledger(t["id"])
    assert row["old"] == "15" and row["new"] == "10" and row["need"] == "joke_density" and row["verify_by"] == core.iso(T + H + 14 * D) and row["undo"] == [{"op": "set", "key": "JOKE_EVERY_SEC_LONG", "value": "15"}]
    assert [x["action"] for x in lg] == ["queued", "intent", "applied"] and lg[2]["proof"] == "read back: JOKE_EVERY_SEC_LONG reads 10" and lg[1]["old"] == "15" and lg[1]["new"] == "10"
    assert m["status"] == "in_progress" and m["sla_due"] == row["verify_by"] and m["links"]["awaiting"] == row["change_id"]          # waiting for proof is not being late
    assert EXE.reconcile(now=T + 2 * H)["moved"] == {} and MEM.watchdog(now=T + 5 * D)["escalated"] == []
    run(ep="EP1", at=T + 3 * H, trigger="voice"); check_row("EP1", "joke_density", "PASS")                                     # EP1 began before the change: it proves nothing
    assert EXE.reconcile(now=T + 4 * H)["moved"] == {}
    run(ep="EP2", at=T + 5 * H); assert EXE.reconcile(now=T + 6 * H)["moved"] == {}                                             # made after the change, not judged yet
    check_row("EP2", "joke_density", "PASS", "a punchline every 9 seconds")
    assert EXE.reconcile(now=T + 7 * H)["moved"] == {t["id"]: "applied -> verified"}
    row = trow(t["id"]); m = MEM.get(t["id"])
    assert row["proof"] == "EP2 was made after the change and passed joke_density with JOKE_EVERY_SEC_LONG = 10" and acts(t["id"])[-1] == "verified"
    assert m["status"] == "resolved" and m["resolution"]["kind"] == "lever_verified" and m["resolution"]["by"] == "engine" and m["resolution"]["ref"] == row["change_id"]
    assert any(a["kind"] == "lever" and a["outcome"] == "verified" for a in st().rows("Org_Audit")) and EXE.reconcile(now=T + 8 * H) == {"open": 0, "moved": {}}

def test_a_video_made_after_the_change_that_fails_the_levers_check_rolls_the_setting_back():
    t, T = applied_setting(); run(ep="EP2", at=T + H); check_row("EP2", "retention", "FAIL"); assert EXE.reconcile(now=T + 2 * H)["moved"] == {}      # another check: not this lever's business
    check_row("EP2", "joke_density", "FAIL", "a gap of 31 seconds")
    assert EXE.reconcile(now=T + 3 * H)["moved"] == {t["id"]: "applied -> rolled_back"} and cell("JOKE_EVERY_SEC_LONG") == "15"
    row = trow(t["id"]); m = MEM.get(t["id"]); lg = ledger(t["id"])[-1]
    assert "EP2, made after the change, failed joke_density: a gap of 31 seconds" in row["note"] and lg["action"] == "rolled_back" and lg["proof"] == "JOKE_EVERY_SEC_LONG is back at '15'"
    assert m["status"] == "resolved" and m["resolution"]["kind"] == "rolled_back" and "failed joke_density" in m["resolution"]["note"]
    t2, T2 = applied_setting(12); run(ep="EP3", at=T2 + H); check_row("EP3", "joke_density", "WAIVED")          # the owner let the VIDEO through, not the setting
    assert EXE.reconcile(now=T2 + 2 * H)["moved"] == {t2["id"]: "applied -> rolled_back"} and cell("JOKE_EVERY_SEC_LONG") == "15"

def test_rollback_never_overwrites_a_value_the_owner_typed_after_the_engine():
    t, T = applied_setting(); core.set_setting("JOKE_EVERY_SEC_LONG", "12")                                    # the owner edits the Sheet by hand
    assert EXE.reconcile(now=T + H)["moved"] == {t["id"]: "applied -> rolled_back"} and cell("JOKE_EVERY_SEC_LONG") == "12"
    lg = ledger(t["id"])[-1]; assert lg["action"] == "rollback_skipped" and "now holds '12'" in lg["note"] and "the owner's hand wins" in lg["note"]
    assert MEM.get(t["id"])["resolution"]["kind"] == "rolled_back"
    t2 = ticket(value=9, subject="Tighten the punchline gap again"); run(ep="EP1"); T2 = now() + H; EXE.reconcile(now=T2); assert cell("JOKE_EVERY_SEC_LONG") == "9" and trow(t2["id"])["old"] == "12"
    run(ep="EP5", at=T2 + H); check_row("EP5", "joke_density", "FAIL"); core.set_setting("JOKE_EVERY_SEC_LONG", "14")          # he edits it while the failed video is on the table
    assert EXE._undo_setting(trow(t2["id"]), st(), T2 + 2 * H)[0] == "skipped" and cell("JOKE_EVERY_SEC_LONG") == "14"

def test_no_evidence_inside_the_window_is_a_rollback_and_a_lever_without_checks_is_judged_by_the_next_run(setting):
    t, T = applied_setting(); assert EXE.reconcile(now=T + 13 * D)["moved"] == {}
    assert EXE.reconcile(now=T + 14 * D + H)["moved"] == {t["id"]: "applied -> rolled_back"} and cell("JOKE_EVERY_SEC_LONG") == "15" and "no evidence within 14 days" in trow(t["id"])["note"]
    setting("EXEC_VERIFY_DAYS", "3"); t2 = ticket("D9", "B", "REEL1_DELAY_MIN", 30); run("D9", "publish", "EP1"); T2 = now() + H; EXE.reconcile(now=T2)
    assert trow(t2["id"])["need"] == "run" and trow(t2["id"])["verify_by"] == core.iso(T2 + 3 * D) and cell("REEL1_DELAY_MIN") == "30"
    run("D9", "publish", "EP7", at=T2 + H); assert EXE.reconcile(now=T2 + 2 * H)["moved"] == {t2["id"]: "applied -> verified"} and "finished a complete run after the change with REEL1_DELAY_MIN = 30" in trow(t2["id"])["proof"]
    t3 = ticket("D9", "B", "REEL2_DELAY_MIN", 480); T3 = T2 + 3 * H; EXE.apply(MEM.get(t3["id"]), now=T3); assert cell("REEL2_DELAY_MIN") == "480"      # no video in the making: applied at once
    def boom(b): b.take(); raise RuntimeError("upload refused")
    with pytest.raises(RuntimeError): run("D9", "publish", "EP8", at=T3 + H, act=boom)
    assert EXE.reconcile(now=T3 + 2 * H)["moved"] == {t3["id"]: "applied -> rolled_back"} and cell("REEL2_DELAY_MIN") == "360" and "ended failed after the change" in trow(t3["id"])["note"]

def test_the_direction_that_weakens_a_gate_waits_for_the_owners_tap_and_his_no_changes_nothing():
    t = ticket(value=25, subject="Allow a longer gap between punchlines"); run(); row = trow(t["id"]); msgs = owner_msgs("org_lever")
    assert row["state"] == "awaiting_owner" and cell("JOKE_EVERY_SEC_LONG") == "15" and acts(t["id"]) == ["owner_asked"] and len(msgs) == 1
    assert msgs[0]["text"] == ("Creative - Ideation & Writers' Room wants to change JOKE_EVERY_SEC_LONG from 15 to 25. Why: Allow a longer gap between punchlines. "
                               "It needs your OK because it weakens a quality gate.") and f"APPROVE {t['id']}" in msgs[0]["buttons"] and f"REJECT {t['id']}" in msgs[0]["buttons"]
    m = MEM.get(t["id"]); assert m["status"] == "in_progress" and msgs[0]["id"] in m["owner_notified"]
    run(ep="EP2"); EXE.reconcile(now=now() + 3 * D); assert trow(t["id"])["state"] == "awaiting_owner" and cell("JOKE_EVERY_SEC_LONG") == "15" and len(owner_msgs("org_lever")) == 1      # asked once
    assert EXE._on_answer({}, f"APPROVE {t['id']}") == "approved and changed; it is now being verified" and cell("JOKE_EVERY_SEC_LONG") == "25"
    assert trow(t["id"])["approved"] and acts(t["id"])[1:] == ["owner_approved", "intent", "applied"] and EXE._on_answer({}, f"APPROVE {t['id']}") == "already settled"
    t2 = ticket("D6", "B", "ANIM_SHOTS", 5, subject="One more animated scene per video"); run("D6", "plan"); assert "it costs more money" in owner_msgs("org_lever")[-1]["text"]
    assert EXE._on_answer({}, f"REJECT {t2['id']}") == "rejected: nothing was changed" and cell("ANIM_SHOTS") == "4" and trow(t2["id"])["state"] == "refused"
    m2 = MEM.get(t2["id"]); assert m2["status"] == "rejected" and m2["resolution"]["by"] == "owner" and acts(t2["id"]) == ["owner_asked", "owner_rejected"]
    t3 = ticket("D6", "B", "ANIM_SHOTS", 5, subject="An extra animated scene after all"); st().append("Episodes", [{"episode_id": "EP9", "status": "PLANNING", "updated": core.iso()}]); run("D6", "plan")
    assert EXE._on_answer({}, f"APPROVE {t3['id']}").startswith("approved; it changes between videos") and cell("ANIM_SHOTS") == "4" and trow(t3["id"])["state"] == "queued"
    st().update("Episodes", "episode_id", "EP9", {"status": "UPLOADED"}); EXE.reconcile(now=now() + H); assert cell("ANIM_SHOTS") == "5" and len(owner_msgs("org_lever")) == 3      # not asked twice

@pytest.mark.parametrize("to,target,value,why", [("D4", "FAL_STILL_MODEL", "x", "is not a registered lever"), ("D4", "ANIM_SHOTS", 5, "is a lever of D6, not of D4"),
                                                 ("D4", "JOKE_EVERY_SEC_LONG", 3, "outside the allowed range"), ("D4", "JOKE_EVERY_SEC_LONG", 45, "more than one step")])
def test_a_ticket_the_lever_table_refuses_is_rejected_with_the_reason_and_changes_nothing(to, target, value, why):
    before = levers(); t = ticket(to, "B", target, value); run(to); row = trow(t["id"]); m = MEM.get(t["id"])
    assert row["state"] == "refused" and why in row["note"] and acts(t["id"]) == ["refused"] and levers() == before
    assert m["status"] == "rejected" and "refused by the Execution Engine" in m["resolution"]["note"] and why in m["resolution"]["note"]
    assert EXE.reconcile(now=now() + D)["moved"] == {} and CON.p_lever_verified({})[0] == CON.PASS

def test_one_unverified_change_per_department_the_second_waits_its_turn():
    t1, T = applied_setting(); t2 = ticket(target="REHOOK_MAX_GAP_SEC", value=60, subject="Re-hook at least every minute"); t3 = ticket("D6", "B", "ANIM_SHOTS", 3, subject="One animated scene fewer")
    run(); run("D6", "plan"); EXE.reconcile(now=T + H)
    assert trow(t2["id"])["state"] == "queued" and f"waits until change {trow(t1['id'])['change_id']}" in trow(t2["id"])["note"] and cell("REHOOK_MAX_GAP_SEC") == "75"
    assert trow(t3["id"])["state"] == "applied" and cell("ANIM_SHOTS") == "3"                                                    # another department is free
    EXE.reconcile(now=T + 2 * H); assert acts(t2["id"]) == ["queued", "queued"]                                                   # one row per reason, not one per tick
    run(ep="EP2", at=T + 3 * H); check_row("EP2", "joke_density", "PASS"); moved = EXE.reconcile(now=T + 4 * H)["moved"]
    assert moved == {t1["id"]: "applied -> verified", t2["id"]: "queued -> applied"} and cell("REHOOK_MAX_GAP_SEC") == "60"

def test_a_ticket_a_person_closes_while_its_change_is_live_takes_the_change_back():
    t, T = applied_setting(); MEM.reject(t["id"], "owner", "dropped by the owner from the stuck-item message")
    assert EXE.reconcile(now=T + H)["moved"] == {t["id"]: "applied -> rolled_back"} and cell("JOKE_EVERY_SEC_LONG") == "15" and "closed by owner while the engine held it" in trow(t["id"])["note"]
    t2 = ticket(value=11, subject="Tighten the punchline gap a little"); run(); MEM.reject(t2["id"], "owner", "changed my mind about this change")
    assert EXE.reconcile(now=T + 2 * H)["moved"] == {t2["id"]: "queued -> refused"} and cell("JOKE_EVERY_SEC_LONG") == "15"

def test_an_interrupted_apply_is_settled_by_the_next_pass_from_what_is_really_there(monkeypatch):
    t = ticket(); run(); T = now() + H; real = core.set_setting; calls = []
    def flaky(k, v):
        if k == "JOKE_EVERY_SEC_LONG" and not calls: calls.append(1); raise RuntimeError("Sheets 503")
        return real(k, v)
    monkeypatch.setattr(EXE, "set_setting", flaky); EXE.reconcile(now=T)                                                           # the write fails in the middle
    assert trow(t["id"])["state"] == "intent" and cell("JOKE_EVERY_SEC_LONG") == "15" and acts(t["id"])[-1] == "intent"
    assert EXE.reconcile(now=T + dt.timedelta(minutes=2))["moved"] == {}                                                           # too fresh to call it interrupted
    assert EXE.reconcile(now=T + H)["moved"] == {t["id"]: "intent -> applied"} and cell("JOKE_EVERY_SEC_LONG") == "10" and acts(t["id"])[-3:] == ["interrupted", "intent", "applied"]
    t2 = ticket("D9", "B", "REEL1_DELAY_MIN", 30); EXE.apply(MEM.get(t2["id"])); core.set_setting("REEL1_DELAY_MIN", "30")
    st().update("Tickets", "id", t2["id"], {"state": "intent", "updated": core.iso(T)})                                           # killed after the write, before the ledger row
    assert EXE.reconcile(now=T + H)["moved"][t2["id"]] == "intent -> applied" and "found by the tick pass after an interrupted apply" in ledger(t2["id"])[-1]["proof"]

def test_a_rollback_that_fails_is_escalated_and_the_owner_hears_of_it(monkeypatch):
    t, T = applied_setting(); run(ep="EP2", at=T + H); check_row("EP2", "joke_density", "FAIL")
    monkeypatch.setattr(EXE, "set_setting", lambda k, v: None)                                                                     # the Sheet silently drops the write
    assert EXE.reconcile(now=T + 2 * H)["moved"] == {t["id"]: "applied -> failed"} and "rollback failed: JOKE_EVERY_SEC_LONG could not be set back to '15'" in trow(t["id"])["note"]
    m = MEM.get(t["id"]); assert m["status"] == "escalated" and m["level"] == 2 and "could not finish the change" in m["escalations"][-1]["why"]
    s, ev = CON.p_lever_verified({}); assert s == CON.FAIL and "failed and was not taken back" in ev
    MEM.watchdog(now=T + 3 * H); msg = owner_msgs("org_stuck"); assert len(msg) == 1 and "Change JOKE_EVERY_SEC_LONG for the next videos" in msg[0]["text"]          # not silent

# ------------------------------------------------------------------ lever class A (knowledge) and D (prompt rule)
def test_a_knowledge_ticket_is_accepted_served_to_the_next_run_and_only_then_verified():
    t = ticket("D6", "A", "palace:b4-push-in", item(), ref="M-DECISION0001"); T = now(); run("D6", "plan", at=T); row = trow(t["id"]); iid = P.item_id("b4-push-in")
    it = P.get(iid); assert row["state"] == "applied" and row["target"] == f"palace:{iid}" and row["need"] == "served" and it["status"] == "accepted" and it["actor"] == "council"
    assert t["id"] in it["derived_from"] and "M-DECISION0001" in it["derived_from"] and iid in P.playbook("D6", record=False)["items"]
    assert ledger(t["id"])[-1]["proof"] == f"read back: {iid} is accepted v1 and inside the playbook of D6" and row["undo"] == [{"op": "retire", "id": iid}]
    assert EXE.reconcile(now=T + H)["moved"] == {}                                                                                  # applied is not verified: no later run yet
    run("D4", "write", at=T + 2 * H); assert EXE.reconcile(now=T + 3 * H)["moved"] == {}                                            # another department's run proves nothing
    s = run("D6", "assets", at=T + 4 * H); assert EXE.reconcile(now=T + 5 * H)["moved"] == {t["id"]: "applied -> verified"}
    proof = trow(t["id"])["proof"]; assert f"Sessions:{s.session_id} (D6 assets) ran after the change with {iid}@1 in its playbook" in proof and "handed over with the work order" in proof
    assert MEM.get(t["id"])["resolution"]["kind"] == "lever_verified" and P.get(iid)["status"] == "accepted"

class Exec:
    """The run whose EXECUTE step hands the ticket to the engine (what the engine sees of it)."""
    def __init__(self, session_id="", episode="EP1"): self.session_id, self.episode = session_id, episode

def test_a_later_run_in_the_very_second_of_the_change_counts_and_the_run_that_made_the_change_never_does():
    # GitHub run 57: on a fast machine the next D6 run began in the clock second in which the ticket was applied; it was skipped and the proof named a later run
    P.ensure_seed(); t = ticket("D6", "A", "palace:b4-push-in", item()); T = now().replace(microsecond=0); iid = P.item_id("b4-push-in")
    EXE.apply(MEM.get(t["id"]), Exec("S-MAKER"), now=T); s = run("D6", "assets", at=T)                                              # the same second, after the change
    assert EXE.reconcile(now=T + H)["moved"] == {t["id"]: "applied -> verified"} and f"Sessions:{s.session_id} (D6 assets)" in trow(t["id"])["proof"]
    s0 = run("D6", "render", at=T + 2 * H); assert f"{iid}@1" in EXE._books(st())[sessions_by_id()[s0.session_id]["playbook_id"]]      # this run was served the item BEFORE the next ticket
    t2 = ticket("D6", "A", f"palace:{iid}", {}, subject="Confirm the push-in technique"); EXE.apply(MEM.get(t2["id"]), Exec(s0.session_id), now=T + 2 * H)      # applied inside that very run
    assert trow(t2["id"])["state"] == "applied" and trow(t2["id"])["session"] == s0.session_id and EXE.reconcile(now=T + 3 * H)["moved"] == {}          # it cannot be its own proof
    s1 = run("D6", "plan", ep="EP2", at=T + 4 * H); assert EXE.reconcile(now=T + 5 * H)["moved"] == {t2["id"]: "applied -> verified"} and s1.session_id in trow(t2["id"])["proof"]
    t3 = ticket("D10", "B", "BRAIN_HOLDOUT", 0.3, subject="A larger holdout for the sampler"); s2 = RUN.run("D10", "daily", taker(), measure=lambda o: {"rows": 4}, now=T + 6 * H)
    assert trow(t3["id"])["state"] == "applied" and trow(t3["id"])["session"] == s2.session_id and cell("BRAIN_HOLDOUT") == "0.3"          # a run without an episode applies its own lever at once ...
    st().update("Tickets", "id", t3["id"], {"applied_at": core.iso(T + 6 * H)}); assert EXE.reconcile(now=T + 7 * H)["moved"] == {}          # ... and is never the proof of it, even in the same second
    RUN.run("D10", "daily", taker(), measure=lambda o: {"rows": 4}, now=T + 30 * H, key="next day"); assert EXE.reconcile(now=T + 31 * H)["moved"] == {t3["id"]: "applied -> verified"}

def test_the_council_accepts_a_takeaway_a_department_proposed_and_a_changed_text_is_restored_on_rollback(setting):
    P.ensure_seed(); P.add(item(key="run|D6|plan|dev"), "D6"); iid = P.item_id("run|D6|plan|dev"); assert P.get(iid)["status"] == "proposed"
    t = ticket("D6", "A", f"palace:{iid}", {}); T = now(); run("D6", "plan", at=T); assert trow(t["id"])["state"] == "applied" and P.get(iid)["status"] == "accepted" and trow(t["id"])["old"] == "proposed v1"
    run("D6", "assets", at=T + H); assert EXE.reconcile(now=T + 2 * H)["moved"] == {t["id"]: "applied -> verified"}
    new = item(summary="A slow push-in on the first animated scene AND on the verdict holds the eye; the cut after it lands harder.")
    t2 = ticket("D6", "A", f"palace:{iid}", new, subject="Extend the push-in rule to the verdict"); run("D6", "plan", at=T + 3 * H); cur = P.get(iid)
    assert cur["version"] == 2 and "AND on the verdict" in cur["summary"] and trow(t2["id"])["undo"][0]["op"] == "restore"
    squeeze(iid)
    for i in range(3): run("D6", "assets", ep=f"EP{i + 2}", at=T + (4 + i) * H)
    assert EXE.reconcile(now=T + 8 * H)["moved"] == {t2["id"]: "applied -> rolled_back"} and "complete runs of D6 after the change and none was served" in trow(t2["id"])["note"]
    back = P.get(iid); assert back["version"] == 3 and "AND on the verdict" not in back["summary"] and back["status"] == "accepted" and "the earlier text is back" in trow(t2["id"])["proof"]

def test_knowledge_that_no_later_run_is_served_is_retired_again(setting):
    t = ticket("D6", "A", "palace:b4-push-in", item()); T = now(); run("D6", "plan", at=T); iid = P.item_id("b4-push-in"); squeeze(iid)
    run("D6", "assets", at=T + H); run("D6", "render", at=T + 2 * H); assert EXE.reconcile(now=T + 3 * H)["moved"] == {}
    run("D6", "plan", ep="EP2", at=T + 4 * H); assert EXE.reconcile(now=T + 5 * H)["moved"] == {t["id"]: "applied -> rolled_back"}
    assert P.get(iid)["status"] == "retired" and MEM.get(t["id"])["resolution"]["kind"] == "rolled_back" and ledger(t["id"])[-1]["proof"] == f"{iid}: retired"

def test_a_department_whose_playbook_goes_into_the_prompt_must_cite_the_item(monkeypatch):
    t = ticket("D6", "A", "palace:b4-push-in", item()); T = now()
    run("D6", "plan", at=T); iid = P.item_id("b4-push-in")                                  # (this file runs with ORG_PROMPT_INJECT off: the engine is judged on its own)
    monkeypatch.setattr(REG, "prompted", lambda d: True); t2 = ticket("D6", "A", "palace:b4-second", item(title="Hold the widest shot for the verdict line", summary="The widest shot of the court is saved for the verdict line so the room reads as one."), subject="Save the wide shot for the verdict")
    EXE.apply(MEM.get(t2["id"]), now=T); monkeypatch.setattr(REG, "prompted", lambda d: False)
    assert trow(t["id"])["need"] == "served" and trow(t2["id"])["need"] == "cited"; i2 = P.item_id("b4-second")
    run("D6", "assets", at=T + H); moved = EXE.reconcile(now=T + 2 * H)["moved"]; assert moved == {t["id"]: "applied -> verified"}          # served is not enough for the second
    run("D6", "render", at=T + 3 * H, act=lambda b: RUN.Out({"x": 1}, applied_items=[i for i in b.take()["items"] if i == i2]))
    assert EXE.reconcile(now=T + 4 * H)["moved"] == {t2["id"]: "applied -> verified"} and trow(t2["id"])["proof"].endswith("and cited it")

@pytest.mark.parametrize("kw,why", [
    (dict(frm="D4"), "knowledge is accepted by the Council (or the owner), not by D4"), (dict(target="b4-push-in"), "the target of a knowledge or rule lever is 'palace:<item key or id>'"),
    (dict(value={}), "there is no Palace item 'b4-push-in' to accept"), (dict(value=dict(ITEM)), "the Palace refuses the item: no evidence"),
    (dict(value=item(departments=["D4"])), "the item is not addressed to D6"), (dict(value=item(kind="style_rule")), "a style_rule is a rule: use lever class D"),
    (dict(value=item(kind="owner_preference", owner_input=True, evidence=[{"source": "the owner on WhatsApp", "date": "2026-11-10", "type": "owner decision"}])), "only through the Owner Office"),
    (dict(cls="D"), "a prompt-rule lever carries a rule (style_rule / policy_rule), not a technique")])
def test_a_knowledge_ticket_that_breaks_a_rule_is_refused_and_the_palace_is_untouched(kw, why):
    P.ensure_seed(); n = len(P.rows()); kw = dict(kw); t = ticket("D6", kw.pop("cls", "A"), kw.pop("target", "palace:b4-push-in"), kw.pop("value", item()), **kw); run("D6", "plan")
    assert trow(t["id"])["state"] == "refused" and why in trow(t["id"])["note"] and len(P.rows()) == n and MEM.get(t["id"])["status"] == "rejected"

def test_an_item_the_playbook_has_no_room_for_is_taken_back_at_once(setting):
    setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT", '{"D6": 200}'); setting("PALACE_LIMITS_SHARE", "0.9"); t = ticket("D6", "A", "palace:b4-push-in", item()); run("D6", "plan"); row = trow(t["id"])
    assert row["state"] == "refused" and "the playbook of D6 has no room for it" in row["note"] and P.get(P.item_id("b4-push-in"))["status"] == "retired" and acts(t["id"]) == ["intent", "refused"]

def test_a_prompt_rule_is_bounded_per_department_and_verified_like_knowledge(setting):
    rule = lambda n: item(kind="style_rule", title=f"Rule {n}: never hold a flat wide shot under a punchline", summary=f"Rule {n}: under a punchline the camera is close on the face that reacts, never on a flat wide shot.")
    setting("EXEC_RULES_PER_DEPT", "1"); t = ticket("D6", "D", "palace:b4-rule-1", rule(1)); T = now(); run("D6", "plan", at=T); iid = P.item_id("b4-rule-1")
    assert trow(t["id"])["state"] == "applied" and P.get(iid)["kind"] == "style_rule" and iid in P.playbook("D6", record=False)["items"]
    t2 = ticket("D6", "D", "palace:b4-rule-2", rule(2), subject="A second camera rule"); run("D6", "assets", at=T + H)
    assert trow(t2["id"])["state"] == "refused" and "the rulebook of D6 is full (1 rules made by ticket)" in trow(t2["id"])["note"] and P.get(P.item_id("b4-rule-2")) is None
    assert EXE.reconcile(now=T + 2 * H)["moved"] == {t["id"]: "applied -> verified"}

# ------------------------------------------------------------------ lever class C: an experiment arm
def test_an_experiment_arm_is_registered_between_videos_and_verified_by_the_features_of_later_videos():
    PB.ensure_seed(); t = ticket("D4", "C", "playbook:writer", dict(RULE), subject="Test a sensory-memory cold open"); T = now(); run(at=T)
    assert trow(t["id"])["state"] == "queued" and not [r for r in PB.rows() if r["status"] == "trial"]
    EXE.reconcile(now=T + H); row = trow(t["id"]); rid = row["new"]; arm = next(r for r in PB.rows() if r["rule_id"] == rid)
    assert row["state"] == "applied" and row["need"] == "2" and row["verify_by"] == core.iso(T + H + 28 * D) and arm["status"] == "trial" and arm["evidence"] == "official" and t["id"] in arm["note"]
    assert PB.for_episode("EP2") == {rid: PB.coin("EP2", rid)} and ledger(t["id"])[-1]["proof"] == f"read back: rulebook trial {rid} is trial"
    feat = lambda ep, arms, fmt="long": st().append("Video_Features", [{"ts": core.iso(), "video_key": ep, "format": fmt, "arm": json.dumps(arms)}])
    run(ep="EP2", at=T + 2 * H); feat("EP1", {"playbook": {rid: "on"}}); feat("EP2", {"playbook": {}}); feat("EP2s", {"playbook": {rid: "on"}}, "short")
    assert EXE.reconcile(now=T + 3 * H)["moved"] == {}                                                                              # EP1 is older than the arm; EP2 does not carry it
    st().update("Video_Features", "video_key", "EP2", {"arm": json.dumps({"playbook": {rid: "off"}})}); assert EXE.reconcile(now=T + 4 * H)["moved"] == {}      # one of the two outputs
    run(ep="EP3", at=T + 5 * H); feat("EP3", {"playbook": {rid: "on"}})
    assert EXE.reconcile(now=T + 6 * H)["moved"] == {t["id"]: "applied -> verified"} and "2 long video(s) made after the change carry arm" in trow(t["id"])["proof"] and "EP2: off, EP3: on" in trow(t["id"])["proof"]

def test_an_arm_no_video_carries_is_taken_out_again_and_a_judged_trial_counts_as_verified():
    PB.ensure_seed(); t = ticket("D4", "C", "playbook:writer", dict(RULE)); T = now(); EXE.apply(MEM.get(t["id"]), now=T); rid = trow(t["id"])["new"]
    assert EXE.reconcile(now=T + 28 * D + H)["moved"] == {t["id"]: "applied -> rolled_back"}
    arm = next(r for r in PB.rows() if r["rule_id"] == rid); assert arm["status"] == "retired" and "rolled back by the Execution Engine" in arm["note"] and PB.for_episode("EP9") == {}
    t2 = ticket("D4", "C", "playbook:packager", dict(RULE, rule="Put the consequence for the viewer, not the topic, in the first three words of the title.", metric="pack"), subject="Test consequence-first titles")
    EXE.apply(MEM.get(t2["id"]), now=T + 29 * D); r2 = trow(t2["id"])["new"]; st().update("Playbook", "rule_id", r2, {"status": "active", "note": "helped: +0.040 on pack (4 on / 4 off)"})
    assert EXE.reconcile(now=T + 30 * D)["moved"] == {t2["id"]: "applied -> verified"} and "was judged on its data: active" in trow(t2["id"])["proof"]

@pytest.mark.parametrize("target,value,why", [("playbook:director_of_fun", RULE, "the target of an experiment lever is 'playbook:<showrunner | writer"),
                                              ("playbook:writer", dict(RULE, source_url=""), "the rulebook refuses the arm: no source link"),
                                              ("playbook:writer", dict(RULE, rule="Buy views for the first hour so the video looks like it is taking off."), "games the platform or breaks policy"),
                                              ("playbook:writer", dict(RULE, metric="vibes"), "unknown metric")])
def test_an_arm_the_rulebook_refuses_is_refused(target, value, why):
    PB.ensure_seed(); n = len(PB.rows()); t = ticket("D4", "C", target, dict(value)); EXE.apply(MEM.get(t["id"]))
    assert trow(t["id"])["state"] == "refused" and why in trow(t["id"])["note"] and len(PB.rows()) == n

def test_no_free_trial_slot_or_trials_switched_off_means_refused(setting):
    PB.ensure_seed(); rs = PB.rows()[:3]
    for r in rs: st().update("Playbook", "rule_id", r["rule_id"], {"status": "trial"})
    t = ticket("D4", "C", "playbook:writer", dict(RULE)); EXE.apply(MEM.get(t["id"])); assert "all 3 trial slots are in use" in trow(t["id"])["note"]
    setting("PLAYBOOK_ON", "FALSE"); t2 = ticket("D4", "C", "playbook:writer", dict(RULE), subject="Second try"); EXE.apply(MEM.get(t2["id"])); assert "switched off (PLAYBOOK_ON)" in trow(t2["id"])["note"]

def test_the_long_video_records_its_arms_in_its_features():
    src = open(os.path.join(ROOT, "whatifs", "episode.py"), encoding="utf-8").read()
    assert 'arm={"playbook": d.get("playbook") or {}}' in src and src.count("BRN.tag(") == 1

# ------------------------------------------------------------------ lever class E: a code build
class Hub:
    """A stand-in for GitHub: what the engine sends (dispatches, merges, closes) and what it reads back (pull request state, diff, commit checks)."""
    def __init__(self, mp):
        self.sent, self.merged, self.closed, self.pr, self.files, self.commit = [], [], [], {}, [], "pending"
        mp.setattr(BLD, "dispatch", lambda wf, inputs, ref="main": self.sent.append((wf, dict(inputs), ref)) or True)
        mp.setattr(BLD, "pr_state", lambda n: dict({"checks": "pending", "merged": False, "head": "h1", "state": "open", "merge_sha": ""}, **self.pr.get(str(n), {})))
        mp.setattr(BLD, "pr_files", lambda n: list(self.files)); mp.setattr(BLD, "commit_state", lambda sha: self.commit)
        mp.setattr(BLD, "merge_pr", lambda n, why="": (self.merged.append(str(n)), self.pr.setdefault(str(n), {}).update(merged=True, merge_sha="abc123def4567"))[0] or (True, f"merged #{n}"))
        mp.setattr(BLD, "close_pr", lambda n: self.closed.append(str(n)) or True)
NEW_TEST = {"filename": "tests/test_pause.py", "status": "added", "additions": 30, "deletions": 0, "patch": "+import pytest\n+def test_a_missing_pause_fails():\n+    assert True\n"}

def build_ticket(mp, **k):
    hub = Hub(mp); t = ticket("D12", "E", "code:pause-check", dict(BUILD), subject="Add a sound check for the pause before a punchline", **k); T = now(); rep = EXE.engine_tick(now=T)
    return hub, t, T, rep

def test_a_code_ticket_becomes_a_build_request_and_one_operations_run_starts_the_build(monkeypatch):
    assert EXE.engine_tick() == {"open": 0, "moved": {}, "on": True} and not st().rows("Sessions") and EXE.tick_age_h() is not None          # an idle engine starts no run
    hub, t, T, rep = build_ticket(monkeypatch); row = trow(t["id"]); ses = st().rows("Sessions"); req = MEM.get(row["request_id"])
    assert rep["operated"] == [t["id"]] and len(ses) == 1 and (ses[0]["dept"], ses[0]["trigger"], ses[0]["status"]) == ("D12", "operate", "ok") and RUN.verify(ses[0]) == []
    assert row["state"] == "dispatched" and req["type"] == "build_request" and req["links"]["ticket"] == t["id"] and req["body"]["files"] == ["whatifs/contract.py"]
    wf, inputs, ref = hub.sent[0]; assert wf == "claude-build.yml" and inputs["kind"] == "feature" and inputs["request"] == req["id"] and len(hub.sent) == 1
    assert inputs["spec"].startswith(f"ORGANISATION BUILD REQUEST {req['id']} (ticket {t['id']})") and "TESTS TO ADD (each must fail without the change):\n- a test that fails when the pause" in inputs["spec"] and "Do not edit or delete an existing test" in inputs["spec"]
    assert acts(t["id"]) == ["intent", "dispatched"] and MEM.get(t["id"])["status"] == "in_progress"
    assert "operated" not in EXE.engine_tick(now=T + H) and len(st().rows("Sessions")) == 1                                                 # the engine has the ticket: no second run
    assert REG.runnable("D12") and "D12" not in REG.PENDING and MEM.get(t["id"])["level"] == 0 and REG.entry_issues() == []

def test_a_green_build_that_only_adds_tests_merges_by_itself_and_is_verified_on_the_merge_commit(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); req = trow(t["id"])["request_id"]
    assert "the Execution Engine follows it" in BLD.build_ready("41", "feature", "claude/feature-1", req) and trow(t["id"])["state"] == "pr_open" and trow(t["id"])["pr"] == "41" and not owner_msgs("build_ready")
    EXE.engine_tick(now=T + H); assert not hub.merged                                                                                      # checks still running
    hub.pr["41"] = {"checks": "green"}; hub.files = [NEW_TEST, {"filename": "docs/CURRENT/SYSTEM.md", "status": "modified", "additions": 2, "deletions": 1, "patch": ""}]
    EXE.engine_tick(now=T + 2 * H); assert hub.merged == ["41"] and not owner_msgs("build_ready") and "auto_merge" in acts(t["id"])
    EXE.engine_tick(now=T + 3 * H); assert trow(t["id"])["state"] == "merged" and trow(t["id"])["new"] == "abc123def4567" and hub.sent[-1] == ("checks.yml", {}, "main")
    EXE.engine_tick(now=T + 4 * H); assert trow(t["id"])["state"] == "merged"                                                              # the checks on main are not finished
    hub.commit = "green"; EXE.engine_tick(now=T + 5 * H); row = trow(t["id"])
    assert row["state"] == "verified" and row["proof"] == "pull request #41 is merged and every check on the merge commit abc123def4 is green"
    assert MEM.get(t["id"])["resolution"]["kind"] == "lever_verified" and MEM.get(req)["resolution"]["kind"] == "merged_verified" and MEM.get(req)["resolution"]["by"] == "engine"

def test_a_build_outside_the_scope_waits_for_the_owners_merge_and_is_asked_for_once(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); BLD.build_ready("42", "feature", "", trow(t["id"])["request_id"])
    hub.pr["42"] = {"checks": "green"}; hub.files = [NEW_TEST, {"filename": "whatifs/contract.py", "status": "modified", "additions": 12, "deletions": 0, "patch": "+x"}]
    EXE.engine_tick(now=T + H); EXE.engine_tick(now=T + 2 * H); msgs = owner_msgs("build_ready")
    assert not hub.merged and len(msgs) == 1 and "It needs your Merge because whatifs/contract.py: outside the automatic scope (new test files only)." in msgs[0]["text"] and "MERGE #42" in msgs[0]["buttons"]
    assert trow(t["id"])["owner_action"] == msgs[0]["id"] and "owner_asked" in acts(t["id"]) and msgs[0]["default_action"].startswith("waits")
    hub.pr["42"].update(merged=True, merge_sha="feed1234beef"); hub.commit = "green"; EXE.engine_tick(now=T + 3 * H); EXE.engine_tick(now=T + 4 * H)
    assert trow(t["id"])["state"] == "verified" and next(x for x in ledger(t["id"]) if x["action"] == "merged")["by"] == "owner"
    assert not BLD.build_ready("77", "tweak", "", "M-UNKNOWN00001").startswith("pull request") and len(owner_msgs("build_ready")) == 2          # not an organisation build: the owner's usual message

def test_red_checks_are_rebuilt_twice_then_the_ticket_goes_up_and_the_owner_hears(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); req = trow(t["id"])["request_id"]
    for i, pr in enumerate(("50", "51", "52")):
        BLD.build_ready(pr, "feature", "", req); hub.pr[pr] = {"checks": "red"}; EXE.engine_tick(now=T + (i + 1) * H)
        if i < 2: assert trow(t["id"])["state"] == "dispatched" and trow(t["id"])["attempts"] == i + 2 and hub.sent[-1][1]["kind"] == "repair" and f"THE PREVIOUS ATTEMPT FAILED: the checks of pull request #{pr} are red" in hub.sent[-1][1]["spec"]
    row = trow(t["id"]); assert row["state"] == "failed" and "3 builds were tried" in row["note"] and hub.closed == ["50", "51", "52"] and len([s for s in hub.sent if s[0] == "claude-build.yml"]) == 3
    assert MEM.get(t["id"])["status"] == "escalated" and MEM.get(req)["status"] == "rejected" and CON.p_lever_verified({})[0] == CON.FAIL
    MEM.watchdog(now=T + 4 * H); assert len(owner_msgs("org_stuck")) == 1

def test_a_build_that_opens_no_pull_request_or_fails_on_main_is_not_called_done(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); EXE.engine_tick(now=T + 5 * H); assert trow(t["id"])["state"] == "dispatched" and len(hub.sent) == 1
    EXE.engine_tick(now=T + 7 * H); assert trow(t["id"])["attempts"] == 2 and "no pull request was opened within 6 hours" in hub.sent[-1][1]["spec"]
    BLD.build_ready("60", "repair", "", trow(t["id"])["request_id"]); hub.pr["60"] = {"checks": "green"}; hub.files = [NEW_TEST]; EXE.engine_tick(now=T + 8 * H); EXE.engine_tick(now=T + 9 * H)
    hub.commit = "red"; EXE.engine_tick(now=T + 10 * H); row = trow(t["id"])
    assert row["state"] == "failed" and "the checks on the merge commit abc123def4 of pull request #60 are red" in row["note"] and "a revert was sent to the build workflow and waits for your Merge" in row["note"]
    assert "Revert the merge commit abc123def4567 of pull request #60" in hub.sent[-1][1]["spec"] and hub.sent[-1][1]["kind"] == "repair" and "request" not in hub.sent[-1][1] and MEM.get(t["id"])["status"] == "escalated"

def test_a_merge_whose_checks_never_report_is_escalated_and_never_reverted_on_a_guess(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); BLD.build_ready("80", "feature", "", trow(t["id"])["request_id"]); hub.pr["80"] = {"checks": "green"}; hub.files = [NEW_TEST]
    EXE.engine_tick(now=T + H); EXE.engine_tick(now=T + 2 * H); assert trow(t["id"])["state"] == "merged"; n = len(hub.sent)
    EXE.engine_tick(now=T + 15 * D); row = trow(t["id"])
    assert row["state"] == "failed" and "the checks on the merge commit never reported" in row["note"] and len(hub.sent) == n and not hub.closed and MEM.get(t["id"])["status"] == "escalated"

def test_the_tick_takes_up_a_new_ticket_of_any_wired_department_without_waiting_for_its_next_video(setting):
    P.ensure_seed(); ta = ticket("D6", "A", "palace:b4-push-in", item()); tb = ticket(); tx = ticket("D1", "B", "VIDEOS_PER_MONTH_EST", 5, subject="Plan for five videos"); T = now()
    st().append("Episodes", [{"episode_id": "EP1", "status": "PLANNING", "updated": core.iso(T)}]); rep = EXE.engine_tick(now=T)
    assert rep["moved"] == {ta["id"]: "new -> applied", tb["id"]: "new -> queued"} and "operated" not in rep and not st().rows("Sessions")          # no department run was needed
    assert P.get(P.item_id("b4-push-in"))["status"] == "accepted" and cell("JOKE_EVERY_SEC_LONG") == "15" and MEM.get(tb["id"])["status"] == "in_progress"
    assert trow(tx["id"]) is None and MEM.get(tx["id"])["level"] == 2                                                              # D1 has no wired run: its ticket is with the owner, not with the engine
    assert MEM.watchdog(now=T + 30 * H)["escalated"] == [] and acts(tb["id"]) == ["queued"]                                         # taken up in time: nothing climbs for a missed acknowledgement
    st().update("Episodes", "episode_id", "EP1", {"status": "UPLOADED"}); assert EXE.engine_tick(now=T + 31 * H)["moved"] == {tb["id"]: "queued -> applied"} and cell("JOKE_EVERY_SEC_LONG") == "10"
    setting("EXEC_ON", "FALSE"); t3 = ticket("D6", "B", "ANIM_SHOTS", 3, subject="One animated scene fewer"); assert EXE.engine_tick(now=T + 32 * H) == {"on": False} and trow(t3["id"]) is None

def test_the_tick_job_itself_runs_the_engine_pass(setting):
    from whatifs import manage as MG
    t = ticket("D6", "A", "palace:b4-push-in", item()); MG.tick()                                                                # the real tick job, nothing called by hand
    assert EXE.tick_age_h() is not None and trow(t["id"])["state"] == "applied" and P.get(P.item_id("b4-push-in"))["status"] == "accepted"
    setting("EXEC_ON", "FALSE"); setting("EXEC_TICK_AT", ""); t2 = ticket(subject="A ticket while the engine is off"); MG.tick(); assert EXE.tick_age_h() is None and trow(t2["id"]) is None

def test_a_dead_tick_pass_is_noticed_while_tickets_wait():
    t, T = applied_setting(); assert CON.p_lever_verified({})[0] == CON.PASS and EXE.tick_age_h() is None                              # a fresh ticket: the first tick is not late yet
    st().update("Tickets", "id", t["id"], {"created": core.iso(T - 30 * H)}); s, ev = CON.p_lever_verified({})
    assert s == CON.FAIL and "tick pass has never run while 1 ticket(s) wait: nothing is being verified or rolled back" in ev
    EXE.engine_tick(now=T - 26 * H); assert "tick pass has not run for 26 h while 1 ticket(s) wait" in CON.p_lever_verified({})[1]
    EXE.engine_tick(now=T); assert CON.p_lever_verified({})[0] == CON.PASS and EXE.tick_age_h(T + H) == 1.0

def test_a_pull_request_the_owner_closes_ends_the_build(monkeypatch):
    hub, t, T, _ = build_ticket(monkeypatch); BLD.build_ready("70", "feature", "", trow(t["id"])["request_id"]); hub.pr["70"] = {"checks": "green", "state": "closed"}
    EXE.engine_tick(now=T + H); assert trow(t["id"])["state"] == "failed" and "pull request #70 was closed without a merge" in trow(t["id"])["note"]

@pytest.mark.parametrize("to,value,flag,why", [("D6", BUILD, "TRUE", "a code change is built by Operations"), ("D12", dict(BUILD, spec="too short"), "TRUE", "not a valid build request: body.spec is too short"),
                                               ("D12", dict(BUILD, tests_to_add=[]), "TRUE", "body.tests_to_add"), ("D12", BUILD, "FALSE", "builds are switched off (BUILDS_ON)")])
def test_a_code_ticket_that_cannot_become_a_build_is_refused(monkeypatch, setting, to, value, flag, why):
    hub = Hub(monkeypatch); setting("BUILDS_ON", flag); t = ticket(to, "E", "code:x", dict(value)); EXE.apply(MEM.get(t["id"]))
    assert trow(t["id"])["state"] == "refused" and why in trow(t["id"])["note"] and not hub.sent and not [m for m in MEM.rows() if m["type"] == "build_request"]

@pytest.mark.parametrize("files,why", [
    ([dict(NEW_TEST, status="modified")], "an existing test is changed"), ([dict(NEW_TEST, deletions=2)], "an existing test is changed"),
    ([NEW_TEST, {"filename": "whatifs/governor.py", "status": "modified", "additions": 1, "deletions": 0}], "whatifs/governor.py: outside the automatic scope"),
    ([NEW_TEST, {"filename": ".github/workflows/checks.yml", "status": "modified", "additions": 1, "deletions": 0}], "outside the automatic scope"),
    ([NEW_TEST, {"filename": "tests/conftest.py", "status": "added", "additions": 3, "deletions": 0}], "tests/conftest.py: outside the automatic scope"),
    ([NEW_TEST, {"filename": "whatifs/org/seed/build.json", "status": "modified", "additions": 9, "deletions": 0}], "outside the automatic scope"),
    ([dict(NEW_TEST, patch="+x = 1\n")], "the diff adds no test"), ([dict(NEW_TEST, additions=900)], "too big to merge unread"), ([], "the diff could not be read"),
    ([NEW_TEST, {"filename": "docs/CURRENT/SYSTEM.md", "status": "removed", "additions": 0, "deletions": 9}], "outside the automatic scope")])
def test_the_automatic_merge_is_decided_on_the_real_diff_and_only_new_tests_pass(files, why, setting):
    assert LV.merge_scope([NEW_TEST]) == (True, []) and LV.merge_scope([NEW_TEST, {"filename": "docs/CURRENT/SYSTEM.md", "status": "modified", "additions": 4, "deletions": 4}])[0]
    ok, reasons = LV.merge_scope(files); assert not ok and any(why in r for r in reasons), reasons
    setting("EXEC_AUTO_MERGE_ON", "FALSE"); assert LV.merge_scope([NEW_TEST]) == (False, ["automatic merge is switched off (EXEC_AUTO_MERGE_ON)"])

def test_the_build_workflow_keeps_every_credential_away_from_the_step_that_reads_the_spec():
    import yaml
    wf = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "claude-build.yml"), encoding="utf-8")); job = wf["jobs"]["build"]; on = wf.get("on") or wf.get(True)
    assert on["workflow_dispatch"]["inputs"]["request"]["required"] is False and job["env"]["BUILD_REQUEST"] == "${{ inputs.request }}"
    assert not [k for k, v in job["env"].items() if "secrets." in str(v)], "a credential at job level reaches the step in which Claude Code reads the spec"
    claude = next(s for s in job["steps"] if "claude-code-action" in str(s.get("uses", ""))); last = job["steps"][-1]
    assert list(claude["env"]) == ["CC_OAUTH_TOKEN"] and not [k for k, v in claude["with"].items() if "secrets." in str(v)]          # its own model credential and nothing else
    assert {"SHEET_ID", "G_REFRESH", "GH_MERGE_TOKEN", "WA_TOKEN", "OWNER_EMAIL"} <= set(last["env"]) and 'build_ready "$PR" "$BUILD_KIND" "$BUILD_BRANCH" "$BUILD_REQUEST"' in last["run"]
    assert job["steps"].index(last) > job["steps"].index(claude)

# ------------------------------------------------------------------ the memo doorway and the runner
def test_a_ticket_closes_only_on_the_engines_ledger_and_waiting_for_proof_is_typed_and_bounded():
    t = ticket(); T = now()
    with pytest.raises(MemoError, match="ledger holds no 'verified' row"): MEM.resolve(t["id"], "engine", "lever_verified", "LC-NOPE000001")
    with pytest.raises(MemoError, match="ledger holds no 'rolled_back' row"): MEM.resolve(t["id"], "D4", "rolled_back", "LC-NOPE000001")
    with pytest.raises(MemoError, match="holds no applied change"): MEM.await_proof(t["id"], T + D, "LC-NOPE000001")
    st().append("Lever_Changes", [{"ts": core.iso(), "change_id": "LC-REAL000001", "ticket_id": t["id"], "action": "applied", "proof": "read back: the cell reads 10"},
                                  {"ts": core.iso(), "change_id": "LC-REAL000001", "ticket_id": "M-OTHERTICKET", "action": "verified", "proof": "EP2 passed the check with the value"},
                                  {"ts": core.iso(), "change_id": "LC-REAL000001", "ticket_id": t["id"], "action": "verified", "proof": ""}])
    with pytest.raises(MemoError, match="ledger holds no 'verified' row"): MEM.resolve(t["id"], "engine", "lever_verified", "LC-REAL000001")          # another ticket's row, and a row without proof
    with pytest.raises(MemoError, match="at most 130 days"): MEM.await_proof(t["id"], T + 200 * D, "LC-REAL000001")
    m = MEM.await_proof(t["id"], T + 20 * D, "LC-REAL000001"); assert m["status"] == "in_progress" and m["sla_due"] == core.iso(T + 20 * D) and m["links"]["awaiting"] == "LC-REAL000001"
    p = MEM.write({"type": "problem_memo", "from_dept": "D8", "to_depts": ["D4"], "subject": "joke density failed at the script gate", "body": {"what_failed": "a gap of 74 seconds", "where": "EP1", "attempt": 1},
                   "done_when": "the check passes for EP1", "evidence": [{"source": "Feature_Ledger row", "date": today(), "type": "own data"}]})
    with pytest.raises(MemoError, match="cannot wait for proof"): MEM.await_proof(p["id"], T + D, "LC-REAL000001")
    with pytest.raises(MemoError, match="'engine' may not move it"): MEM.resolve(p["id"], "engine", "repair_verified", "Sessions:S-1")          # the engine closes tickets and build requests, nothing else
    st().append("Lever_Changes", [{"ts": core.iso(), "change_id": "LC-REAL000001", "ticket_id": t["id"], "action": "verified", "proof": "EP2 passed joke_density with the value 10"}])
    assert MEM.resolve(t["id"], "engine", "lever_verified", "LC-REAL000001")["status"] == "resolved"
    with pytest.raises(MemoError, match="closed memo"): MEM.await_proof(t["id"], T + D, "LC-REAL000001")

def test_engine_off_changes_nothing_and_the_checks_do_not_apply(setting):
    setting("EXEC_ON", "FALSE"); t = ticket(); run()
    assert trow(t["id"]) is None and MEM.get(t["id"])["status"] == "escalated" and EXE.engine_tick() == {"on": False} and EXE.reconcile() == {"open": 0, "moved": {}} and not ledger()
    assert CON.p_decisions_executed({})[0] == CON.NA and CON.p_lever_verified({})[0] == CON.NA and not EXE.build_opened("M-X", "1")
    setting("EXEC_ON", "TRUE"); setting("ORG_ON", "FALSE"); assert not EXE.on() and CON.p_lever_verified({})[0] == CON.NA

# ------------------------------------------------------------------ the two checks
def decision(tickets, cls="B", **k):
    m = {"type": "decision_memo", "from_dept": "C", "to_depts": ["D4"], "subject": "Tighten the punchline gap for four videos",
         "body": {"decision": "Lower the gap between punchlines to ten seconds.", "why": "The assessment said test and the cost is nothing.", "memos_cited": ["M-ABC123"], "lever_class": cls,
                  "tickets": tickets, "owner_approval": False}}
    m.update(k); return MEM.write(m)

def test_decisions_executed_passes_on_real_tickets_and_fails_on_text_only_decisions():
    assert {(f[0], f[1]) for f in CON.FEATURES} >= {("decisions_executed", "script"), ("lever_verified", "script")} and REG.check_owner("decisions_executed") == "C" and REG.check_owner("lever_verified") == "D12"
    assert sum(1 for f in CON.FEATURES if f[1] == "script") == 34 and sum(1 for f in CON.FEATURES if f[1] == "final") == 19          # v12 B6a: + palace_injected, palace_cited, canon_in_brief
    s, ev = CON.p_decisions_executed({}); assert s == CON.NA and "nothing to execute" in ev and CON.p_lever_verified({})[0] == CON.PASS          # nothing decided yet: not a PASS (the lever table is still judged)
    t, T = applied_setting(); d = decision([t["id"]]); s, ev = CON.p_decisions_executed({}); assert s == CON.PASS and ev.startswith("1 decision(s), 1 ticket(s): none is text only; 1 open")
    d2 = decision([], subject="Change the camera style for the cold open"); assert CON.p_decisions_executed({})[0] == CON.PASS                # inside the two hours in which its tickets may still arrive
    st().update("Memos", "id", d2["id"], {"created": core.iso(T - 3 * H)}); s, ev = CON.p_decisions_executed({})
    assert s == CON.FAIL and f"decision {d2['id']}" in ev and "has no ticket: it is text only" in ev
    st().update("Memos", "id", d2["id"], {"body": json.dumps(dict(MEM.get(d2["id"])["body"], lever_class="none"))}); assert CON.p_decisions_executed({})[0] == CON.PASS          # a decision that changes nothing needs none
    decision(["M-GHOST0000001"], subject="A decision that names a ticket nobody wrote"); s, ev = CON.p_decisions_executed({}); assert s == CON.FAIL and "names ticket M-GHOST0000001, which does not exist" in ev

def test_decisions_executed_fails_on_a_forged_close_and_on_a_late_ticket_nobody_was_told_about():
    t, T = applied_setting(); row = trow(t["id"])
    st().append("Lever_Changes", [{"ts": core.iso(), "change_id": row["change_id"], "ticket_id": t["id"], "action": "verified", "proof": "typed by hand, not found by the engine"}])
    MEM.resolve(t["id"], "D4", "lever_verified", row["change_id"]); s, ev = CON.p_decisions_executed({})                              # the memo says verified, the engine holds 'applied'
    assert s == CON.FAIL and f"ticket {t['id']} is closed as lever_verified but the engine holds it as 'applied'" in ev
    t2 = ticket("D6", "B", "ANIM_SHOTS", 3, subject="One animated scene fewer"); st().update("Memos", "id", t2["id"], {"sla_due": core.iso(T - 5 * H)})
    s, ev = CON.p_decisions_executed({}); assert s == CON.FAIL and f"ticket {t2['id']}" in ev and "past its deadline and nobody above was told (level 0)" in ev
    MEM.watchdog(); m = MEM.get(t2["id"]); assert m["level"] == 2 and m["owner_notified"]                                             # escalated and the owner told: no longer the engine's failure
    assert f"ticket {t2['id']}" not in CON.p_decisions_executed({})[1]

def test_lever_verified_fails_on_every_broken_invariant_of_the_ledger(monkeypatch):
    t, T = applied_setting(); s, ev = CON.p_lever_verified({}); assert s == CON.PASS and "1 inside the verification window" in ev and "every change has its ledger rows" in ev
    force = lambda **ch: st().update("Tickets", "id", t["id"], ch); base = {k: trow(t["id"])[k] for k in ("state", "verify_by", "updated")}
    def broken(why, **ch):
        force(**ch); s, ev = CON.p_lever_verified({}); assert s == CON.FAIL and why in ev, ev
        force(**base); assert CON.p_lever_verified({})[0] == CON.PASS
    broken("is past its verification window with no verdict (the tick pass is not doing its work)", verify_by=core.iso(T - 3 * H))
    broken("an interrupted apply was never settled", state="intent", updated=core.iso(T - 3 * H))
    broken("is marked verified without a proof in the ledger", state="verified")
    broken("is marked rolled back without a ledger row", state="rolled_back")
    broken("failed and was not taken back", state="failed")
    rows = st().rows("Lever_Changes"); st().replace("Lever_Changes", [r for r in rows if r["action"] != "intent"])
    assert "was changed without an intent row in the ledger" in CON.p_lever_verified({})[1]; st().replace("Lever_Changes", rows)
    saved = LV.LEVERS.pop("ANIM_SHOTS"); s, ev = CON.p_lever_verified({}); LV.LEVERS["ANIM_SHOTS"] = saved; assert s == CON.FAIL and "ANIM_SHOTS of D6 has no rule" in ev

def test_the_generated_doc_and_the_matrix_describe_the_engine():
    doc = open(os.path.join(ROOT, "docs", "CURRENT", "SYSTEM.md"), encoding="utf-8").read(); mx = open(os.path.join(ROOT, "docs", "CURRENT", "ENFORCEMENT_MATRIX.md"), encoding="utf-8").read()
    assert "## 12. The Execution Engine" in doc and "| JOKE_EVERY_SEC_LONG | D4 | int | 8 to 60 | 10 | up: it weakens a quality gate | joke_density |" in doc and "operate (whatifs/org/execute.py)" in doc
    for ref in ("contract:decisions_executed", "contract:lever_verified", "fn:whatifs.org.execute.apply", "fn:whatifs.org.execute.reconcile", "fn:whatifs.org.levers.check", "fn:whatifs.org.levers.merge_scope",
                "fn:whatifs.org.memos.await_proof", "fn:whatifs.org.execute.idle"): assert ref in mx, ref

# ------------------------------------------------------------------ the real pipeline, twice: a knowledge ticket and a setting ticket from decision to proof
def test_two_real_episodes_carry_a_decision_from_ticket_to_ledger_proof(monkeypatch):
    from whatifs import episode as EP, manage as MG
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    slot = lambda h: (now() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ta = ticket("D6", "A", "palace:b4-push-in", item(), subject="Use a slow push-in on the first animated scene"); tb = ticket("D4", "B", "REHOOK_MAX_GAP_SEC", 70, subject="Re-hook a little more often")
    decision([ta["id"], tb["id"]])
    r = EP.produce(slot(10), episode_id="EP209901010900"); assert r.get("ok"), r
    led = {x["feature"]: x for x in st().rows("Feature_Ledger") if x["episode_id"] == "EP209901010900"}
    assert led["decisions_executed"]["status"] == "PASS" and led["lever_verified"]["status"] == "PASS" and "1 decision(s), 2 ticket(s)" in led["decisions_executed"]["evidence"]
    assert trow(ta["id"])["state"] == "applied" and trow(tb["id"])["state"] == "queued" and cell("REHOOK_MAX_GAP_SEC") == "75"          # knowledge at once; the setting waits for the gap
    feats = [f for f in st().rows("Video_Features") if f["video_key"] == "EP209901010900"]; assert feats and "playbook" in json.loads(feats[0]["arm"])
    EXE.engine_tick(); assert trow(ta["id"])["state"] == "verified" and "(D6 assets)" in trow(ta["id"])["proof"] and trow(tb["id"])["state"] == "applied" and cell("REHOOK_MAX_GAP_SEC") == "70"
    core.set_setting("CONTRACT_OFF", "originality")          # the fake writers' room returns the same script for every episode: only that check is taken out for the second video
    r2 = EP.produce(slot(34), episode_id="EP209901020900"); assert r2.get("ok"), r2
    EXE.engine_tick(); row = trow(tb["id"]); seen = [(x["feature"], x["status"], x["ts"]) for x in st().rows("Feature_Ledger") if x["episode_id"] == "EP209901020900" and x["feature"] == "retention"]
    assert row["state"] == "verified", (row["state"], row["applied_at"], seen, [(s["trigger"], s["started"]) for s in st().rows("Sessions") if s["episode_id"] == "EP209901020900"][:2])
    assert row["state"] == "verified" and row["proof"] == "EP209901020900 was made after the change and passed retention with REHOOK_MAX_GAP_SEC = 70", row
    assert MEM.get(tb["id"])["resolution"]["kind"] == "lever_verified" and CON.p_decisions_executed({})[0] == CON.PASS and CON.p_lever_verified({})[0] == CON.PASS
