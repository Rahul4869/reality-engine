"""v12 B-OWNER - the owner's two screens: one register of every message to him, one road for every mail, alarms that can never be muted, WhatsApp
that starts three kinds of message only, his input desk, both screens showing the same, never held by his absence, the money of his messages.
Every rule is proven both ways; the real code path is run, so an unwired call is seen. The HD gate has its own file (tests/test_v12_hdgate.py)."""
import ast, datetime as dt, json, os, shutil
import pytest, yaml
from whatifs import core, notify as NT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _row(aid): return next(r for r in core.store().rows("Owner_Actions") if r["id"] == aid)
def _ids(rows): return {r["id"] for r in rows}

# ------------------------------------------------------------------ step 0: open issue 246 (GitHub's Checks job neared its 120-minute limit)
def test_checks_job_has_room():
    """The Checks job runs the whole suite in ONE process and the rehearsal; its unit tests ran up to 1 h 36 min on V4 (open issue 246), so the
    job's limit is at least 240 minutes - and under 360, GitHub's own ceiling for a job. No test, strictness or step is loosened by it."""
    job = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "checks.yml"), encoding="utf-8"))["jobs"]["guard_and_rehearsal"]
    assert 240 <= job["timeout-minutes"] < 360, job["timeout-minutes"]

# ------------------------------------------------------------------ step 1: THE REGISTER (PART 1) - one table of every kind of message to him
VARIABLE_KINDS = {"whatifs/contract.py": ("creative_review", "floor_eye"), "whatifs/org/verdicts.py": ("maker_line", "owner_verdict")}      # the two calls that pass the kind as a variable
ALARMS = ("kids_flag", "policy", "risk_lock", "risk_gone", "uploads_private", "money_stop", "pipeline_stop", "org_watchdog")      # item 180: a FIXED list
HOLDS = {"contract_hold": "(a) a check of the video failed", "floor_hold": "(a) the first-time viewer floor held the film",
         "special_review": "(a) the Short's finished file failed a check; (a) a special has no check on record",
         "hd_blocked": "(a) the HD gate keeps a video private for a policy read",
         "org_lever": "(b) a lever only he may turn", "api_audit": "(b) only he can send YouTube's API audit form",
         "ypp_tier": "(b) only he can apply in Studio and accept the terms"}      # item 150: the named hold list - (a) quality or policy, (b) what only he can lawfully do

def _sends(root=ROOT):
    """Every call `NT.send(` and `NT.mail(` under whatifs/ and tools/: (file, line, its first argument)."""
    out = []
    for top in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(root, top)):
            for f in sorted(fn):
                if not f.endswith(".py"): continue
                p = os.path.join(dp, f); rel = os.path.relpath(p, root).replace(os.sep, "/")
                for n in ast.walk(ast.parse(open(p, encoding="utf-8").read())):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("send", "mail") and isinstance(n.func.value, ast.Name) \
                            and n.func.value.id == "NT" and n.args:
                        out.append((rel, n.lineno, n.args[0]))
    return out

def test_every_kind_sent_is_registered():
    """A kind that is sent and not in the register cannot be grouped, counted or kept from WhatsApp's three doors: the build fails on it."""
    sites = _sends(); assert len(sites) >= 50, len(sites)                                                       # 50 calls at d64fdcc
    bad = [f"{f}:{ln}: {a.value}" for f, ln, a in sites if isinstance(a, ast.Constant) and a.value not in NT.KINDS]
    var = sorted({f for f, _ln, a in sites if not isinstance(a, ast.Constant)})
    assert bad == [] and var == sorted(VARIABLE_KINDS), (bad, var)
    assert all(k in NT.KINDS for ks in VARIABLE_KINDS.values() for k in ks)

def test_the_lists_are_pinned():
    """The alarms and the holds are FIXED lists: a kind added to either only in the code fails here."""
    assert NT.ALARM_KINDS == ALARMS and sorted(NT.HOLD_KINDS) == sorted(HOLDS), (NT.ALARM_KINDS, NT.HOLD_KINDS)
    assert all(NT.klass(k) == NT.ALARM for k in ALARMS) and all(NT.klass(k) == NT.HOLD for k in HOLDS) and NT.klass("no_such_kind") == NT.CARD
    assert NT.INFORM_KINDS == ("strategy", "desk") and NT.STANDING_KINDS == ("strategy", "desk", "idea", "decided_post")      # R18 (3): the older literal is not grown
    assert all(c in (NT.ALARM, NT.HOLD, NT.CARD, NT.INFORM) and g in NT.GROUPS for c, g in NT.KINDS.values())

T0 = dt.datetime(2026, 11, 20, 5, 0, tzinfo=dt.timezone.utc)

def test_the_second_inform_is_not_swallowed(monkeypatch, setting):
    """R17 (4): an inform row has no button and no expiry, so its key kept it OPEN for ever and the next week's digest reached no screen."""
    setting("TWO_SCREENS_ON", "TRUE"); monkeypatch.setattr(NT, "now_utc", lambda: T0)
    a = NT.send("comments_digest", "Weekly comments digest: 12 questions")
    assert NT.send("comments_digest", "Weekly comments digest, sent twice") == a                               # twice on one India day = one row
    monkeypatch.setattr(NT, "now_utc", lambda: T0 + dt.timedelta(days=7))
    b = NT.send("comments_digest", "The next week's digest"); assert b != a                                     # another day = a row of its own
    rows = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "comments_digest"]
    assert len(rows) == 2 and all(r["status"] == "OPEN" and r["expires_at"] for r in rows) and NT.KINDS["comments_digest"] == (NT.INFORM, "research")
    assert NT.expire_defaults(T0 + dt.timedelta(hours=NT.INFORM_KEEP_H + 1)) == 1 and _row(a)["status"] == "EXPIRED" and _row(b)["status"] == "OPEN"
    assert not _row(NT.send("strategy", "Strategy moved one lever"))["expires_at"]                              # a standing kind never gets the inform rule's expiry
    setting("TWO_SCREENS_ON", "FALSE"); assert NT.send("budget_pct", "Budget: 80%") == NT.send("budget_pct", "Budget: 90%")      # the older path, word for word

def test_needs_you_is_one_list(monkeypatch, setting):
    """R17 ADDS (C): "Needs you" has ONE definition, `notify.needs` - open holds, open cards that ask, open rows of an unknown kind - and
    the digest's "Waiting for you" is that list (the morning head, the risks count and WhatsApp's list join in step 4, the docket in step 6)."""
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); box = []
    monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": box.append((subj, html)) or True)
    unk = NT.send("zz_never_registered", "A message of a kind nobody registered")                               # no button: still never silent
    hold = NT.send("contract_hold", "Video held: the final check failed", episode="EP1")
    card = NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A"), ("Pick B", "PICK B")], default="A is used", expires_h=48)
    NT.send("budget_pct", "Budget: 80% of the cap"); NT.send("strategy", "Strategy moved one lever")
    NT.send("voice_pick", "Voice samples are in your e-mail", [("Noted", "NOTED")], default="voice A is used", expires_h=72)      # a card that asks nothing
    assert _ids(NT.needs()) == {unk, hold, card}
    assert NT.digest(force=True) and len(box) == 1
    assert all(t in box[0][1] for t in ("A message of a kind nobody registered", "Video held", "Pick the clip model")), box[0][1]
    assert not any(t in box[0][1] for t in ("Budget: 80%", "Strategy moved", "Voice samples")), box[0][1]
    # step 4: the risks' count, the morning head and WhatsApp's list read the same rows
    from whatifs import wa as WA, digests as DG
    assert any(x.startswith("3 open decisions") for x in DG._risks({})), DG._risks({})
    assert any(l.startswith("Needs you: 3") for l in DG.head("daily").splitlines()), DG.head("daily")
    bodies = _wire(monkeypatch); _window(True); assert WA.push("needs")
    assert {x["id"] for x in bodies[-1]["interactive"]["action"]["sections"][0]["rows"]} == {f"CARD|{a}" for a in (unk, hold, card)}

def test_a_hold_without_a_button_can_be_closed(setting):
    """R17 ADDS (C): a hold sent without a button gets ("Done", "OK") - without it his tap could never close it and it stood under "Needs you" for ever."""
    setting("TWO_SCREENS_ON", "TRUE")
    aid = NT.send("api_audit", "Send the YouTube API audit form")
    assert json.loads(_row(aid)["buttons"]) == [["Done", "OK"]] and aid in _ids(NT.needs())
    NT.answer(aid, "OK"); assert _row(aid)["status"] == "ANSWERED" and aid not in _ids(NT.needs())
    setting("TWO_SCREENS_ON", "FALSE"); assert json.loads(_row(NT.send("api_audit", "again", episode="EP2"))["buttons"]) == []      # the older path

def test_the_tier_is_told_once(monkeypatch, setting):
    """R7's round 2 and R18 (7 e): `ypp.check` sends at every check while the numbers hold; with the Done button his tap closes the row, and the next
    check must not open a new hold - the kind `ypp_tier` stands on ANY row with its key, open or closed."""
    from whatifs import ypp as YPP
    setting("TWO_SCREENS_ON", "TRUE"); setting("YPP_WATCH_ON", "TRUE")
    monkeypatch.setattr(YPP, "progress", lambda now=None: {"subs": 620, "hours": 3100.0, "shorts_views_90d": 0, "uploads_90d": 6, "at": core.iso()})
    YPP.check(); rows = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "ypp_tier"]
    assert len(rows) == 1 and json.loads(rows[0]["buttons"]) == [["Done", "OK"]] and rows[0]["id"] in _ids(NT.needs())
    NT.answer(rows[0]["id"], "OK"); YPP.check()
    assert [r["id"] for r in core.store().rows("Owner_Actions") if r["kind"] == "ypp_tier"] == [rows[0]["id"]] and NT.needs() == []

def test_a_card_without_a_default_gets_the_fallback_and_is_named(setting):
    """PART 7, the card rule at run time: a card with buttons and no default or no expiry is never lost and never waits for ever - it is stored with
    the fallback default and 72 hours, and one `card_rule` row a kind a day names it (the build refuses such a call: the card scan of step 2b)."""
    setting("TWO_SCREENS_ON", "TRUE")
    a = NT.send("model_dead", "The clip model is gone", [("Switch", "SWITCH X"), ("Keep", "KEEP X")], episode="EP1")
    NT.send("model_dead", "Another model is gone", [("Switch", "SWITCH Y")], episode="EP2")
    left = (core.parse_iso(_row(a)["expires_at"]) - core.now_utc()).total_seconds() / 3600
    assert _row(a)["default_action"] == NT.CARD_FALLBACK and 71.9 < left <= 72.0, (_row(a)["default_action"], left)
    told = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "card_rule"]
    assert len(told) == 1 and "model_dead" in told[0]["text"], told                                             # one row a kind a day
    b = NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A")], default="A is used", expires_h=24); assert _row(b)["default_action"] == "A is used"
    setting("TWO_SCREENS_ON", "FALSE"); assert _row(NT.send("org_stuck", "A department is stuck", [("Look", "LOOK X")]))["default_action"] == ""      # the older path

# ------------------------------------------------------------------ step 2a: ONE ROAD (PART 2) - every mail to him goes through notify.mail
OWN_IDS = ("EP209911260900",)          # the whole production of this file: an id no other test file uses (a test proves it)

def test_the_whole_productions_of_this_file_use_ids_no_other_test_file_uses():
    root = os.path.dirname(os.path.abspath(__file__)); here = os.path.basename(__file__)
    for f in os.listdir(root):
        if f.endswith(".py") and f != here:
            t = open(os.path.join(root, f), encoding="utf-8").read()
            for i in OWN_IDS: assert i not in t, (f, i)

def _ago(**k): return (core.now_utc() - dt.timedelta(**k)).strftime("%Y-%m-%dT%H:%M:%SZ")

# the smallest call that reaches each mail site of the table (PUB.email is replaced by a box in the test)
def _r8(mp, setting):
    from whatifs import episode as EP; EP._preflight_mail("the image key is missing")
def _r9(mp, setting):                                                          # the site is inside _finish: one whole production reaches it
    from whatifs import episode as EP, manage as MG
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    mp.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    try:
        r = EP.produce((core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), episode_id=OWN_IDS[0]); assert r.get("ok"), r
    finally: shutil.rmtree(os.path.join(core.WORK, OWN_IDS[0]), ignore_errors=True)
def _r10(mp, setting):
    from whatifs import episode as EP
    out = os.path.join(core.WORK, "EPROW10"); os.makedirs(out, exist_ok=True)
    try: EP._hold(core.store(), "EPROW10", out, {"problems": [{"code": "aliveness", "detail": "planted"}]}, [], False)
    finally: shutil.rmtree(out, ignore_errors=True)
def _r13(mp, setting):
    from whatifs import manage as MG, launch as LA
    mp.setattr(MG.PUB, "yt_status", lambda vid: "private"); mp.setattr(LA, "lock_detected", lambda vid, issues: None)
    MG._give_up_stuck([{"episode_id": "EPROW13", "slot_et": _ago(days=10), "status": "SCHEDULED", "yt_id": "vidROW13"}])
def _r14(mp, setting):
    from whatifs import manage as MG
    setting("UPLOAD_LOCK", "on"); MG.audit_nudge([{"episode_id": "EPROW14", "yt_id": "vidROW14"}])
def _r15(mp, setting):
    from whatifs import manage as MG
    setting("UPLOAD_LOCK", "on"); setting("API_AUDIT_STATUS", "sent"); MG.audit_nudge([{"episode_id": "EPROW15", "yt_id": "vidROW15"}])
def _r16(mp, setting):
    from whatifs import manage as MG
    held = [{"episode_id": f"EPROW16{i}", "status": "HOLD_QC", "updated": core.iso()} for i in range(max(1, core.S("HOLD_BLOCK_AFTER", int)))]
    assert MG._produce_slot(held) is None
def _r17(mp, setting):
    from whatifs import manage as MG
    mp.setattr(MG.G, "can_start_episode", lambda: (False, "the month's cap is reached")); assert MG._produce_slot([]) is None
def _r18(mp, setting):
    from whatifs import manage as MG
    core.store().append("Episodes", [{"episode_id": "EPROW18", "slot_et": _ago(hours=core.S("PRIVATE_ALERT_HOURS", float) + 1), "status": "SCHEDULED", "yt_id": "vidROW18", "notes": ""}])
    mp.setattr(MG.PUB, "yt_status", lambda vid: "private"); MG.release("EPROW18")
def _r19(mp, setting):
    from whatifs import manage as MG
    core.store().append("Episodes", [{"episode_id": "EPROW19", "slot_et": _ago(hours=1), "status": "SCHEDULED", "yt_id": "vidROW19", "notes": ""}])
    mp.setattr(MG.PUB, "yt_status", lambda vid: "public"); mp.setattr(MG.PUB, "yt_comment", lambda *a, **k: None)
    mp.setattr(MG, "_fetch_release", lambda ep, assets=None: {"pinned": ""}); MG.release("EPROW19")
def _r20(mp, setting):
    from whatifs import manage as MG
    for k, v in (("GH_REPO", "me/re"), ("PR_NUMBER", "7"), ("PR_TITLE", "Better hooks"), ("PR_URL", "https://github.com/me/re/pull/7")): mp.setenv(k, v)
    assert MG.pr_ready()
def _r21(mp, setting):
    from whatifs import manage as MG, caretaker as CT
    mp.setattr(CT, "policy_rescue", lambda items: None)                      # the urgent card beside the mail is caretaker's own call, not a row of this table
    MG.guardian([{"change": "AI content is no longer monetised", "source": "https://support.google.com/youtube"}])
def _r22(mp, setting):
    from whatifs import manage as MG
    core.store().append("Episodes", [{"episode_id": f"EPROW22{i}", "status": "FAILED", "notes": "planted"} for i in range(3)]); MG.failure_watch()
def _money(mp, left=None, prop=None, days=999.0):
    from whatifs import manage as MG, costguard as CG
    mp.setattr(CG, "spend_monitor", lambda *a, **k: None); mp.setattr(CG, "weekly_deviation_mail", lambda *a, **k: None)      # costguard's own mails are rows of step 2b
    mp.setattr(MG.G, "gemini_left_usd", lambda: left); mp.setattr(MG.G, "kling4_proposal", lambda: prop); mp.setattr(MG.G, "runway_days", lambda provider: days)
    mp.setattr(MG.G, "headroom", lambda: {"spent_inr": 1200.0, "cap_inr": 5000.0, "per_video_inr": 600.0}); MG.money_check()
def _r23(mp, setting): _money(mp, prop="Room for a 4th clip: about Rs 120 a video.")
def _r24(mp, setting): setting("AUTO_RELOAD_ON", "TRUE"); _money(mp, left=0.5)
def _r25(mp, setting): _money(mp, days=3.0)
def _r26(mp, setting):
    from whatifs import manage as MG, models as M
    mp.setattr(M, "ask_batch", lambda *a, **k: "The month in one page."); MG.monthly_brief()
# step 2b: the table's other 22 rows
def _r1(mp, setting):
    from whatifs import community as CM, publish as PUB
    mp.setattr(PUB, "yt_comment", lambda vid, t: True); assert CM.post_jury_comment({"episode_id": "EPROW1", "yt_id": "vidROW1"}, {})
def _r2(mp, setting):
    from whatifs import community as CM
    core.store().append("Comment_Queue", [{"ts": core.iso(), "episode_id": "EPROW2", "comment_id": "cROW2", "author": "Ana", "kind": "question", "text": "How high would it go?",
                                           "draft": "", "status": "QUEUED", "replied_at": ""}]); assert CM.weekly_digest()
def _r3(mp, setting):
    from whatifs import community as CM, manage as MG
    MG.setup(); CM.experiment_results("EPROW3", "vidROW3", core.now_utc() - dt.timedelta(days=8), {"views": 1000, "countries": {"IN": 0.9, "US": 0.1}})
def _r4(mp, setting):
    from whatifs import costguard as CG, governor as G
    mp.setattr(CG, "month_spend", lambda: G.cap_inr() * 0.95); assert CG.spend_monitor() == [70, 90]
def _r5(mp, setting):
    from whatifs import costguard as CG
    mp.setitem(CG._LADDER, "EPROW5", 1); assert CG.ladder_mail("EPROW5")
def _r6(mp, setting):
    from whatifs import costguard as CG
    mp.setattr(CG, "deviation_report", lambda days=7: [("visuals", 300.0, 200.0, 50)]); assert CG.weekly_deviation_mail()
def _r7(mp, setting):
    from whatifs import costguard as CG, publish as PUB
    mp.setattr(PUB, "yt_status_full", lambda vid: {"madeForKids": True}); assert CG.kids_check("vidROW7", "EPROW7") is True
def _r11(mp, setting):
    import subprocess
    from whatifs import insights as IN, publish as PUB
    setting("AUDIO_DROP_POST_ON", "TRUE"); mp.setenv("META_TOKEN", "planted"); mp.setenv("IG_USER_ID", "planted")
    core.store().append("Episodes", [{"episode_id": "EPROW11", "status": "LIVE", "notes": ""}])
    mp.setattr(subprocess, "run", lambda *a, **k: None); mp.setattr(PUB, "ig_reel", lambda *a, **k: {"id": "igROW11"})
    assert IN.post_drop("EPROW11", "drop.wav", "still.png", "caption")
def _r12(mp, setting):
    from whatifs import launch as LA
    LA.lock_detected("vidROW12", ["planted: came back private"])
def _r27(mp, setting):
    from whatifs import packaging as PK
    core.store().append("Episodes", [{"episode_id": "EPROW27", "slot_et": (core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "SCHEDULED", "notes": ""}])
    vs = [{"key": k, "title": f"Title {k}", "thumb_text": f"Thumb {k}"} for k in "ABC"]; PK.record("EPROW27", "vidROW27", vs, {})
    left = (core.parse_iso(next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "title_pick")["expires_at"]) - core.now_utc()).total_seconds() / 3600
    assert 7.9 < left <= 8.0, left                                                     # it expires at the pick deadline: the slot minus PICK_DEADLINE_BEFORE_SLOT_H
def _r28(mp, setting):
    from whatifs import packaging as PK
    PK._pick_reply("EPROW28", "applied: B")
def _r29(mp, setting):
    from whatifs import premise as PR
    assert PR.below_bar_mail("EPROW29", [{"kind": "premise", "best": 6.5, "bar": 7}], "A title")
def _r30(mp, setting):
    from whatifs import premise as PR
    PR.skip_slot("planted: nothing reached the bar", episode="EPROW30", slot="2099-11-27")
def _r31(mp, setting):
    from whatifs import preview as PV, premise as PR, ladder as LAD
    from whatifs.org import runner as ORG
    def skip(*a, **k): raise PR.SkipSlot("planted: no pitch reached the bar")
    for k in ("name", "episode"): mp.setitem(core.JOB, k, core.JOB.get(k))      # run() names the job: put it back after the test
    mp.setattr(LAD, "gate", lambda *a, **k: (True, "", None)); mp.setattr(ORG, "work", skip)
    assert PV.run()["ok"] is False
def _r32(mp, setting):                                                         # the site is the end of a whole preview: the room writes in fake mode, nothing is bought
    from whatifs import preview as PV, ladder as LAD
    for k in ("name", "episode"): mp.setitem(core.JOB, k, core.JOB.get(k))
    mp.setattr(LAD, "gate", lambda *a, **k: (True, "", None)); mp.setattr(PV, "now_utc", lambda: dt.datetime(2099, 11, 27, 9, 0, tzinfo=dt.timezone.utc))
    assert PV.run()["draft"] == "DRAFT209911270900"
def _r33(mp, setting):
    from whatifs import preview as PV
    assert PV.decide("MODE STANDARD") == "standard"
def _sheet_stubs(mp):
    from whatifs import anim as ANIM, specials as SP, publish as PUB
    mp.setattr(ANIM, "gemini_image", lambda *a, **k: None); mp.setattr(SP, "_portrait", lambda *a, **k: None)
    mp.setattr(PUB, "drive_upload", lambda *a, **k: ("fidROW", "https://drive.example/x"))
def _r34(mp, setting):
    from whatifs import sheets as SH
    _sheet_stubs(mp); mp.setattr(SH, "masters_plan", lambda: [{"character": "VALE", "expression": "master", "prompt": "p", "hash": "hROW34"}])
    assert SH.masters()["made"] == 1
def _r35(mp, setting):
    from whatifs import sheets as SH, show as SHOW
    _sheet_stubs(mp); mp.setattr(SHOW, "characters", lambda: [{"id": "VALE", "name": "Vale"}])
    core.store().append("Character_Sheets", [{"ts": core.iso(), "character": "VALE", "expression": "master", "hash": "hROW35m", "prompt": "p", "file": "drive:m", "status": "LOCKED", "approved_at": core.iso()}])
    mp.setattr(SH, "plan", lambda characters=None: [{"character": "SET", "expression": "courtroom", "prompt": "p", "hash": "hROW35"}])
    assert SH.run()["made"] == 1
def _r36(mp, setting):
    from whatifs import sheets as SH
    core.store().append("Character_Sheets", [{"ts": _ago(hours=100), "character": "VALE", "expression": "smug", "hash": "hROW36", "prompt": "p", "file": "drive:s", "status": "DRAFT", "approved_at": ""}])
    assert SH.auto_lock() == 1
def _r37(mp, setting):
    from whatifs import sheets as SH
    _sheet_stubs(mp); mp.setattr(SH, "_board", lambda grid, path: path)
    assert SH.style_samples()["ok"]
def _r38(mp, setting):                                                         # the mail sits inside `if not FAKE`: FAKE replaced, narrate / ffmpeg / Drive stubbed
    import subprocess, types
    from whatifs import voice_lab as VL, publish as PUB
    d = os.path.join(core.WORK, "ROW38"); os.makedirs(d, exist_ok=True); mp.chdir(d)
    def narr(text, blend, base, **k):
        open(base + ".wav", "wb").close(); return types.SimpleNamespace(wav_path=base + ".wav", voiceprint="vp")
    mp.setattr(VL, "narrate", narr); mp.setattr(VL, "FAKE", False); mp.setattr(VL, "cast_samples", lambda out: [])
    mp.setattr(subprocess, "run", lambda *a, **k: None); mp.setattr(PUB, "drive_upload", lambda *a, **k: ("fidROW38", "https://drive.example/v"))
    assert VL.main()
def _r39(mp, setting):
    import tools.repair as RP
    RP._tell_owner("whatifs/premise.py", "this file guards money, quality or publishing")
VOICE_TEXT = "Voice samples are in your e-mail. To choose one, type A, B, C or D in the Sheet's VOICE cell."

# THE TABLE OF PART 2 (one table: step 2a types the 17 rows of manage.py and episode.py, step 2b the other 22):
# (#, place, kind, subject, "row" = one row of its kind / "copy" = no new row (the screens carry it through another row), its key, what else the row holds, the call)
ROAD = [
    (1, "community.py post_jury_comment", "pin_comment", "Pin this comment", "row", "pin|vidROW1",
     {"level": "info", "buttons": [["Done", "DONE"]], "default_action": "the comment stays unpinned"}, _r1),
    (2, "community.py weekly_digest", "comments_digest", "Weekly comments digest", "row", "comments_digest||{india_day}", {}, _r2),
    (3, "community.py experiment_results", "region", "One region dominates (IN 90%)", "row", "region|EPROW3", {"level": "info"}, _r3),
    (4, "costguard.py spend_monitor", "budget_pct", "Budget: 90% of this month's cap used", "row", None, {}, _r4),
    (5, "costguard.py ladder_mail", "cost_overrun", "Video finished with AI-side savings", "row", "overrun|EPROW5", {}, _r5),
    (6, "costguard.py weekly_deviation_mail", "cost_check", "Weekly cost check", "row", None, {}, _r6),
    (7, "costguard.py kids_check", "kids_flag", "URGENT: YouTube marked a video as made for kids", "row", "kids|vidROW7", {}, _r7),
    (8, "episode.py _preflight_mail", "pipeline_stop", "Production paused: a health check failed", "row", "pipeline_stop|preflight|{utc_day}", {}, _r8),
    (9, "episode.py _finish", "scheduled", "Video scheduled", "row", "scheduled|{ep}", {"level": "info"}, _r9),
    (10, "episode.py _hold", "contract_hold", "Video held: the final check failed", "copy", None, {}, _r10),
    (11, "insights.py post_drop", "audio_drop", "First audio drop posted on Instagram", "row", None, {}, _r11),
    (12, "launch.py lock_detected", "uploads_private", "URGENT: YouTube is keeping uploads private again", "row", "uploads_private", {}, _r12),
    (13, "manage.py _give_up_stuck", "uploads_private", "A video is stuck on Private", "row", "uploads_private", {}, _r13),
    (14, "manage.py audit_nudge", "api_audit", "Reminder: send the YouTube API audit form", "row", "api_audit", {"buttons": [["Done", "OK"]]}, _r14),
    (15, "manage.py audit_nudge", "api_audit_wait", "Waiting for the YouTube API audit", "row", None, {}, _r15),
    (16, "manage.py _produce_slot", "contract_hold", "Reminder: a video is waiting for your fix click", "copy", None, {}, _r16),
    (17, "manage.py _produce_slot", "money_stop", "Monthly budget reached", "row", "money_stop|{month}", {}, _r17),
    (18, "manage.py release", "uploads_private", "Video not public yet", "row", "uploads_private", {}, _r18),
    (19, "manage.py release", "live", "We're live", "row", None, {}, _r19),
    (20, "manage.py pr_ready", "build_ready", "Change ready to merge: #7", "row", "build|7",
     {"buttons": [["Merge", "MERGE #7"], ["Reject", "REJECT #7"]], "default_action": "it waits; it closes after 7 days"}, _r20),
    (21, "manage.py guardian", "policy", "Paused for 7 days (policy watch)", "row", "policy|{utc_day}", {}, _r21),
    (22, "manage.py failure_watch", "pipeline_stop", "Needs a look (3 failed tries)", "row", "pipeline_stop|fails", {}, _r22),
    (23, "manage.py money_check", "headroom", "Budget headroom: room for a 4th Kling clip", "row", None, {}, _r23),
    (24, "manage.py money_check (auto-reload)", "topup", "Top-up reminder", "row", "topup|{india_day}", {}, _r24),
    (25, "manage.py money_check", "topup", "Top-up reminder", "row", "topup|{india_day}", {}, _r25),
    (26, "manage.py monthly_brief", "monthly_brief", "Monthly brief", "row", None, {}, _r26),
    (27, "packaging.py record", "title_pick", "Pick the title + thumbnail (EPROW27)", "row", "title_pick|EPROW27",
     {"buttons": [["Keep A", "PICK EPROW27 A"], ["Pick B", "PICK EPROW27 B"], ["Pick C", "PICK EPROW27 C"]], "default_action": "A goes out"}, _r27),
    (28, "packaging.py _pick_reply", "pick_ack", "Your pick for EPROW28: applied: B", "row", "pick_ack|EPROW28|{india_day}", {}, _r28),
    (29, "premise.py below_bar_mail", "below_bar", "A video was made below the quality bar", "row", "below_bar|EPROW29|{india_day}", {}, _r29),
    (30, "premise.py skip_slot", "slot_skipped", "A slot was skipped", "row", "slot_skipped|EPROW30|{india_day}", {}, _r30),
    (31, "preview.py run (nothing reached the bar)", "preview_none", "Script Preview: nothing reached the bar", "row", "preview_none||{india_day}", {}, _r31),
    (32, "preview.py run", "script_preview", "Script Preview: ", "row", "preview|DRAFT209911270900",
     {"text": "A script preview is ready. It is in your e-mail.", "buttons": [["Approve", "APPROVE DRAFT209911270900"], ["Reject", "REJECT DRAFT209911270900"]],
      "default_action": "the draft is not used: the next slot writes its own script"}, _r32),
    (33, "preview.py decide (MODE)", "mode_ack", "Budget mode: Standard", "row", None, {}, _r33),
    (34, "sheets.py masters", "sheets_review", "New Toybox Noir character masters to approve", "row", "sheets|{india_day}",
     {"buttons": [["Approve VALE", "APPROVE SHEET VALE"]], "default_action": "they lock by themselves"}, _r34),
    (35, "sheets.py run", "sheets_review", "Character sheets ready to review", "row", "sheets|{india_day}",
     {"buttons": [["Approve SET", "APPROVE SHEET SET"]], "default_action": "they lock by themselves"}, _r35),
    (36, "sheets.py auto_lock", "sheets_locked", "Character sheets locked by default", "row", None, {}, _r36),
    (37, "sheets.py style_samples", "style_pick", "Pick the look of your show", "copy", None, {"others": ["style_pick"]}, _r37),      # the card two lines above it
    (38, "voice_lab.py main", "voice_pick", "Fallback narrator voice", "row", None,
     {"text": VOICE_TEXT, "buttons": [["Noted", "NOTED"]], "default_action": "voice A is used"}, _r38),
    (39, "tools/repair.py _tell_owner", "repair_waiting", "A code repair is waiting for you", "row", None, {}, _r39),
]
assert sorted(r[0] for r in ROAD) == [n for n in range(1, 40)], "PART 2's table: 39 rows (row 40, the one-time Google key, is the named exception)"

@pytest.mark.parametrize("site", ROAD, ids=[f"row{r[0]}" for r in ROAD])
def test_every_row_of_the_table(site, monkeypatch, setting):
    """PART 2, ONE ROAD (item 149: e-mail is only the copy): with the switch on, each mail site of the table, driven by the smallest call that reaches
    it, leaves ONE mail (the copy, his storage) AND one Owner_Actions row of its kind with the mail's words - or, where the table says copy, one mail
    and no new row. A site put back to PUB.email leaves no row; `screens` forced False in notify.mail leaves none either."""
    from whatifs import publish as PUB
    n, place, kind, subject, how, key, want, drive = site
    setting("TWO_SCREENS_ON", "TRUE"); box = []
    monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": box.append((str(subj), str(html), kind)) or True)
    before = _ids(core.store().rows("Owner_Actions"))
    drive(monkeypatch, setting)
    mails = [m for m in box if m[0].startswith(subject)]
    assert len(mails) == 1 and mails[0][2] == want.get("level", "essential"), (place, [m[0] for m in box])
    new = [r for r in core.store().rows("Owner_Actions") if r["id"] not in before]
    if how == "copy":                                                          # no row from the mail; only the rows the site itself makes beside it (row 37: its card)
        assert sorted(r["kind"] for r in new) == sorted(want.get("others", [])) and not any(r["text"].startswith(subject) for r in new), \
            (place, [(r["kind"], r["text"][:60]) for r in new]); return
    mine = [r for r in new if r["kind"] == kind]
    assert len(mine) == 1 and kind in NT.KINDS and mine[0]["text"].startswith(want.get("text", subject)), (place, [(r["kind"], r["text"][:60]) for r in new])
    if key:
        k = key.format(utc_day=core.now_utc().strftime("%Y-%m-%d"), month=core.now_utc().strftime("%Y-%m"), india_day=NT._india_day(), ep=OWN_IDS[0])
        assert mine[0]["dedupe_key"] == k, (place, mine[0]["dedupe_key"], k)
    for f, v in want.items():
        if f == "buttons": assert json.loads(mine[0]["buttons"]) == v, (place, mine[0]["buttons"])
        elif f not in ("level", "others"): assert mine[0][f] == v, (place, f, mine[0][f])
    if "text" in want: assert subject.strip() not in mine[0]["text"], (place, mine[0]["text"])      # rows 32, 38: the mail's words (a script, an unreleased premise) never reach a screen

# ------------------------------------------------------------------ step 2b: THE MAIL SCAN and THE CARD SCAN (the build refuses what the run time would only repair)
MAIL_FILES = ("whatifs/notify.py", "whatifs/digests.py", "whatifs/publish.py")      # the copy of the morning message and of a row, and the definition
MAIL_ALLOWED = {"tools/google_signin.py": "a one-time key: never a screen"}          # row 40 of PART 2's table, the named exception

def _py_files():
    for top in ("whatifs", "tools"):
        for dp, _dn, fn in os.walk(os.path.join(ROOT, top)):
            for f in sorted(fn):
                if f.endswith(".py"):
                    p = os.path.join(dp, f); yield os.path.relpath(p, ROOT).replace(os.sep, "/"), open(p, encoding="utf-8").read()

def _mails_outside(files):
    """Every place outside the three files and the allow-list that sends mail: a call of `.email(` / `.email_mime(`, an import of them from
    whatifs.publish, or Gmail's send address in a string."""
    bad = []
    for rel, src in files:
        if rel in MAIL_FILES or rel in MAIL_ALLOWED: continue
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("email", "email_mime"): bad.append(f"{rel}:{n.lineno}: .{n.func.attr}(")
            elif isinstance(n, ast.ImportFrom) and n.module == "whatifs.publish" and {a.name for a in n.names} & {"email", "email_mime"}: bad.append(f"{rel}:{n.lineno}: import")
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and "gmail/v1/users/me/messages/send" in n.value: bad.append(f"{rel}:{n.lineno}: Gmail")
    return bad

def test_no_mail_outside_notify():
    """PART 2 (item 149: e-mail is only the copy): outside notify, digests and publish's own definition nothing sends mail - every mail to him
    goes through `notify.mail`, so it is also a row both screens carry. PLANTED: a direct `PUB.email` in a copy of whatifs/slop.py is found."""
    files = list(_py_files()); assert len(files) > 100 and _mails_outside(files) == [], _mails_outside(files)
    slop = next(src for rel, src in files if rel == "whatifs/slop.py")
    assert _mails_outside([("whatifs/slop.py", slop + '\nPUB.email("x", "y")\n')]) == ["whatifs/slop.py:" + str(slop.count("\n") + 2) + ": .email("]
    assert _mails_outside([("tools/x.py", "from whatifs.publish import email\n")]) and _mails_outside([("tools/x.py", "U = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send'\n")])

def _cards_without_a_default(files):
    """Every `NT.send(` / `NT.mail(` of a literal kind of class CARD (not a standing kind) that passes buttons and no `default=` or no `expires_h=`."""
    bad = []
    for rel, src in files:
        for n in ast.walk(ast.parse(src)):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("send", "mail") and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "NT" and n.args and isinstance(n.args[0], ast.Constant)): continue
            kind = n.args[0].value; kw = {k.arg: k.value for k in n.keywords}
            if NT.klass(kind) != NT.CARD or kind in NT.STANDING_KINDS: continue
            btn = kw.get("buttons", n.args[2] if n.func.attr == "send" and len(n.args) > 2 else None)
            if btn is None or (isinstance(btn, (ast.List, ast.Tuple)) and not btn.elts): continue
            if "default" not in kw or "expires_h" not in kw: bad.append(f"{rel}:{n.lineno}: {kind}")
    return bad

def test_every_card_has_a_default_and_an_expiry():
    """PART 7 (item 150: his absence never holds a post): every card he is sent says what his silence does and when - the build refuses one that
    does not (at run time `send` only gives it the fallback and names it). HOLD and the standing kinds are the only exemptions, and the hold list
    is pinned (test_the_lists_are_pinned). PLANTED: a card with buttons and no default is found; a hold and an inform are not."""
    files = list(_py_files()); assert _cards_without_a_default(files) == [], _cards_without_a_default(files)
    planted = 'NT.send("bakeoff", "Pick", [("A", "PICK A")], expires_h=48)\nNT.send("contract_hold", "Held", [("Fix", "FIX")])\nNT.send("budget_pct", "80%")\n' \
              'NT.mail("title_pick", "Pick", "<p>x</p>", buttons=[("A", "PICK A")], default="A goes out")\n'
    assert _cards_without_a_default([("whatifs/x.py", planted)]) == ["whatifs/x.py:1: bakeoff", "whatifs/x.py:4: title_pick"]

# ------------------------------------------------------------------ step 4: WHATSAPP SENDS THREE KINDS OF MESSAGE (PART 4) and its money (PART 8)
from whatifs import wa as WA, digests as DG

def _wire(monkeypatch):
    """The stand-in wire, recorded: every body that reached Meta (the 24-hour guard and the bill in `wa._post` still run)."""
    bodies = []; monkeypatch.setattr(WA, "_wire", lambda body: bodies.append(body) or f"wamid.T{len(bodies)}"); return bodies

def _window(open_, now=None):
    core.set_setting("WA_LAST_INBOUND_AT", core.iso((now or core.now_utc()) - dt.timedelta(hours=1)) if open_ else "")

@pytest.mark.parametrize("open_", [False, True], ids=["window_closed", "window_open"])
def test_three_days_three_kinds(open_, monkeypatch, setting):
    """PART 4 (item 150): over three days (Saturday, the Sunday, Monday) of half-hourly ticks, with five decisions and twenty inform rows open and no
    alarm, WhatsApp starts exactly ONE morning message and ONE "Needs you" list a day - Sunday's morning message is the weekly one, never a second -
    and nothing else: outside the window every one is the template, inside it none is. With nothing open the evening list is not sent at all."""
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    start = dt.datetime(2026, 11, 20, 18, 30, tzinfo=dt.timezone.utc)                                   # Sat 21 Nov 2026, 00:00 India time
    assert DG.needs_tick(start + dt.timedelta(hours=19)) is False and not core.S("NEEDS_SENT") and bodies == []      # 19:00 India time, no decision open
    for i in range(5): NT.send("bakeoff", f"Decision {i}", [("Pick A", f"PICK A{i}")], default="A is used", expires_h=200 + i, dedupe_key=f"bake|{i}")
    for i in range(20): NT.send(("budget_pct", "region", "comments_digest", "scheduled")[i % 4], f"Inform row {i}", episode=f"EPI{i}")
    for k in range(144):
        now = start + dt.timedelta(minutes=30 * k); _window(open_, now); DG.tick(now)
    rows = core.store().rows("WA_Outbox")
    assert sorted(r["kind"] for r in rows) == ["morning"] * 3 + ["needs"] * 3, [(r["kind"], r["status"]) for r in rows]
    assert len(bodies) == 6 and all((b["type"] == "template") != open_ for b in bodies), [b["type"] for b in bodies]

def test_no_free_text_outside_the_window(monkeypatch, setting):
    """PART 4 (S2: outside the 24-hour window Meta takes only a template - error 131047). PLANTED: free text with the window closed is not posted and
    a WA_Outbox row says "refused_window" - the stand-in refuses what Meta refuses, so a rehearsal fails where the launch would."""
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _window(False)
    assert WA.send_text("x") == "" and bodies == [] and [r["status"] for r in core.store().rows("WA_Outbox")] == ["refused_window"]
    assert WA.send_open("Needs you", "1 decision.", "OPEN|needs") and bodies[0]["type"] == "template"                 # the template goes
    _window(True); assert WA.send_text("y") and bodies[-1]["type"] == "text"                                         # inside the window a reply goes
    setting("TWO_SCREENS_ON", "FALSE"); _window(False); assert WA.send_text("z") and bodies[-1]["type"] == "text"     # the older path, word for word

SENDERS = ("send_text", "send_buttons", "send_list", "send_image", "send_menu", "send_section", "send_group", "send_template")

def _starts_outside_wa(files):
    """Every place outside wa.py that starts a WhatsApp message: a call of `WA._post(`, a call of a sender (allowed only inside `digests._send_old`,
    the older brief), or an import of either from whatifs.wa."""
    bad = []
    for rel, src in files:
        if rel == "whatifs/wa.py": continue
        tree = ast.parse(src); allowed = set()
        if rel == "whatifs/digests.py":
            for f in tree.body:
                if isinstance(f, ast.FunctionDef) and f.name == "_send_old": allowed = {id(n) for n in ast.walk(f)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                if n.func.attr == "_post" and isinstance(n.func.value, ast.Name) and n.func.value.id in ("WA", "wa"): bad.append(f"{rel}:{n.lineno}: _post")
                elif n.func.attr in SENDERS and id(n) not in allowed: bad.append(f"{rel}:{n.lineno}: {n.func.attr}")
            elif isinstance(n, ast.ImportFrom) and n.module == "whatifs.wa" and {a.name for a in n.names} & set(SENDERS + ("_post",)): bad.append(f"{rel}:{n.lineno}: import")
    return bad

def test_only_wa_starts_a_message(setting):
    """PART 4 (item 150): `wa.push` is the ONLY function that starts a message to him, of three kinds only; outside wa.py nothing calls the wire or a
    sender (the older brief `digests._send_old` keeps its words with the switch off). PLANTED: a sender and a wire call outside wa.py are found."""
    files = list(_py_files()); assert _starts_outside_wa(files) == [], _starts_outside_wa(files)
    assert _starts_outside_wa([("whatifs/x.py", "from whatifs import wa as WA\nWA.send_text('hi')\n")]) == ["whatifs/x.py:2: send_text"]
    assert _starts_outside_wa([("whatifs/x.py", "WA._post({'type': 'text'})\n")]) == ["whatifs/x.py:1: _post"]
    assert WA.PUSH_KINDS == ("morning", "needs", "alarm"); setting("TWO_SCREENS_ON", "TRUE")
    with pytest.raises(ValueError): WA.push("digest")

def test_the_template_is_what_c0b_submits(monkeypatch, setting):
    """PART 4 and S3: THE ONE TEMPLATE - its fixed words, UTILITY, one quick reply "Open", a body within 1,024 characters that neither starts nor
    ends on a variable; what is sent fills exactly its two variables (one line, at most 700 characters) and the button's payload."""
    t = WA.open_template(); body = next(c for c in t["components"] if c["type"] == "BODY")["text"]
    assert body == "Reality Engine - {{1}}. {{2}} Tap Open to see everything and to answer." == WA.OPEN_BODY and t["category"] == "UTILITY"
    assert t["name"] == core.DEFAULTS["WA_OPEN_TEMPLATE"][0] == "re_open_v1" and len(body) <= 1024 and body.count("{{") == 2
    assert not body.strip().startswith("{{") and not body.strip().endswith("}}")
    assert [c["buttons"] for c in t["components"] if c["type"] == "BUTTONS"] == [[{"type": "QUICK_REPLY", "text": "Open"}]]
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _window(False)
    assert WA.send_open("ALARM", "YouTube marked a video\nas made for kids.  " + "x" * 900, "OPEN|alarm|A1", kind="alarm")
    sent = bodies[0]["template"]; p = sent["components"][0]["parameters"]
    assert sent["name"] == "re_open_v1" and p[0]["text"] == "ALARM" and "\n" not in p[1]["text"] and "  " not in p[1]["text"] and len(p[1]["text"]) <= 700
    assert sent["components"][1]["parameters"][0]["payload"] == "OPEN|alarm|A1"

def test_week_and_fyi_reach_both_screens(monkeypatch, setting):
    """PART 4 (item 149, GAP 2: "week" and "fyi" rows reached only the e-mail digest): they are in the groups of the morning message on WhatsApp - the
    morning list IS the eight groups - and in its mail, which holds all eight groups in full (the dashboard's groups join in step 6)."""
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); box = []
    monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": box.append((subj, html)) or True)
    NT.send("budget_pct", "Budget: 80% of the cap", tier="week"); NT.send("region", "One region dominates the views", tier="fyi", episode="EP7")
    assert "Budget: 80% of the cap" in WA.group_text("money") and "One region dominates" in WA.group_text("research")
    now = dt.datetime(2026, 11, 21, 4, 0, tzinfo=dt.timezone.utc); _window(True, now)
    assert DG.send("daily", now=now)["via"] == "whatsapp" and bodies[-1]["interactive"]["type"] == "list"
    assert [x["id"] for x in bodies[-1]["interactive"]["action"]["sections"][0]["rows"]] == [f"MENU|{g}" for g in NT.GROUPS]
    assert len(box) == 1 and all(t in box[0][1] for t in ("Budget: 80% of the cap", "One region dominates", "*Decided for you*")), box[0][1][:600]

FILLERS = ("let's dive in", "hope this helps", "great question", "happy to help", "feel free to", "don't hesitate", "exciting news", "as an ai",
           "i hope you", "just wanted to")      # a short list beside the long video's own `data.AI_TELLS`

def _sounds_like_a_machine(files):
    from whatifs import data as D
    bad = []
    for rel, src in files:
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                bad += [f"{rel}:{n.lineno}: {t}" for t in list(D.AI_TELLS) + list(FILLERS) if t in n.value.lower()]
    return bad

def test_his_messages_do_not_sound_like_a_machine():
    """THE SLOP LINE (item 145): his messages are short, plain and varied - every fixed sentence of notify, wa, digests and the desk is scanned against
    the long video's own list of AI phrases and a short list of fillers. PLANTED: "Let's dive in" in the morning head fails."""
    files = [(rel, src) for rel, src in _py_files() if rel in ("whatifs/notify.py", "whatifs/wa.py", "whatifs/digests.py", "whatifs/org/desk.py")]
    assert len(files) == 4 and _sounds_like_a_machine(files) == [], _sounds_like_a_machine(files)
    src = dict(files)["whatifs/digests.py"]; planted = src.replace('message, {loc:%a %d %b}"', 'message, {loc:%a %d %b}. Let\'s dive in"')
    assert planted != src and _sounds_like_a_machine([("whatifs/digests.py", planted)])

def test_the_groups_carry_the_older_sections(monkeypatch, setting):
    """R18 (7 g): nothing the older menu showed is lost - each group's text opens with the older sections it replaces (`owner_view.render`), and the
    two charts go as before: numbers before Posted, money before Money; a group without a chart sends none."""
    from whatifs import owner_view as OV, charts as CH
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _window(True)
    png = os.path.join(core.WORK, "owner_chart_t4.png"); open(png, "wb").write(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(CH, "money_chart", lambda view, path=None: png); monkeypatch.setattr(CH, "numbers_chart", lambda view, path=None: png)
    try:
        for g, sec in (("money", "money"), ("posted", "numbers")):
            n = len(bodies); WA.send_group(g); txt = bodies[-1]["interactive"]["body"]["text"]
            assert [b["type"] for b in bodies[n:]] == ["image", "interactive"], [b["type"] for b in bodies[n:]]
            assert all(l in txt for l in OV.render(sec, OV.build()).splitlines()[:2]), (g, txt[:400])
        n = len(bodies); WA.send_group("needs"); assert [b["type"] for b in bodies[n:]] == ["interactive"]
    finally: os.remove(png)

def _wa_costs(): return [r for r in core.store().rows("Cost_Log") if r.get("item") == "whatsapp"]

def test_whatsapp_is_counted_and_capped(monkeypatch, setting):
    """PART 8 (item 151): every delivered message is a Cost_Log row of its own, off every video - a template at the utility price, a reply free under
    the month's free tier and at the service price after it; at WA_MONTHLY_CAP_INR the morning message and the list stop on WhatsApp (one `wa_cap` row
    says so) and an alarm still goes."""
    from whatifs import costguard as CG
    setting("TWO_SCREENS_ON", "TRUE"); setting("PRICE_WA_UTILITY_INR", "2.5"); setting("PRICE_WA_SERVICE_INR", "0.75"); bodies = _wire(monkeypatch)
    _window(False); assert WA.push("morning", text="Morning message, Sat 21 Nov")
    _window(True); assert WA.send_text("a reply")
    setting("WA_SERVICE_FREE_PER_MONTH", "1"); assert WA.send_text("a second reply")
    got = [(r["role"], r["basis"], round(float(r["inr"]), 2), r["episode_id"]) for r in _wa_costs()]
    assert got == [("morning", "template", 2.5, "owner"), ("reply", "service", 0.0, "owner"), ("reply", "service", 0.75, "owner")], got
    m = CG.owner_messages(); assert (m["templates"], m["replies"], m["spent"], m["free_left"]) == (1, 2, 3.25, 0), m
    NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A")], default="A is used", expires_h=48)
    setting("WA_MONTHLY_CAP_INR", "3"); n = len(bodies)
    assert WA.push("morning", text="Morning message") == "" and WA.push("needs") == "" and len(bodies) == n
    assert [r["kind"] for r in core.store().rows("Owner_Actions") if r["kind"] == "wa_cap"] == ["wa_cap"]
    alarm = NT.send("kids_flag", "YouTube marked a video as made for kids", dedupe_key="kids|V1"); assert len(bodies) == n + 1      # step 3: the alarm pushes itself
    assert WA.push("alarm", _row(alarm)) and len(bodies) == n + 2                                                   # an alarm reads no cap

def test_whatsapp_is_inside_his_month(monkeypatch, setting):
    """PART 8, R17 (9 a): WhatsApp counts inside his Rs 5,000 - his own spend rises by it - and is never booked as paid by the Claude credit."""
    from whatifs import governor as G
    setting("TWO_SCREENS_ON", "TRUE"); setting("PRICE_WA_UTILITY_INR", "4.0"); _wire(monkeypatch); _window(False)
    own, cover = G.own_spend_inr(), G.credit_cover_inr()
    assert WA.push("morning", text="Morning message")
    assert round(G.own_spend_inr() - own, 2) == 4.0 and G.credit_cover_inr() == cover

def test_the_three_share_the_chat_cap(monkeypatch, setting):
    """PART 8, R17 (9 b): the chat, the desk and WhatsApp share CHAT_MONTHLY_CAP_INR (Rs 250) - at it the next chat turn is the cheap model's."""
    from whatifs import models as M
    roles = []; monkeypatch.setattr(M, "ask", lambda role, *a, **k: roles.append(role) or "ok")
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "owner", "item": i, "provider": "x", "units": 1, "inr": v, "role": i}
                                     for i, v in (("owner_chat", 100), ("owner_desk", 50), ("whatsapp", 100))])
    setting("TWO_SCREENS_ON", "FALSE"); WA.chat("how are the shorts doing?")
    setting("TWO_SCREENS_ON", "TRUE"); WA.chat("how are the shorts doing?")
    assert roles == ["owner_chat", "owner_chat_cheap"], roles

# ------------------------------------------------------------------ step 3: ALARMS CAN NEVER BE MUTED (PART 3, item 180); the paused branch (R18 (2)); R22 (9), R22 (10)
def _alarms_told(): return [r for r in core.store().rows("WA_Outbox") if r.get("kind") == "alarm" and r.get("wamid")]

def _mailbox(monkeypatch):
    from whatifs import publish as PUB
    box = []; monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": box.append(str(subj)) or True); return box

def test_an_alarm_arrives_on_both_screens_whatever_is_set(monkeypatch, setting):
    """THE PLANTED TEST OF THE BRIEF (item 180: "my AI had muted all of them at 2 a.m."): quiet hours on, the day's cap of "now" messages at 0, WhatsApp's
    money cap passed, the 24-hour window closed - a made-for-kids alarm is still pushed on WhatsApp (the one template, with a message id) and mailed
    once. (Its row in the dashboard's snapshot joins in step 6.)"""
    setting("TWO_SCREENS_ON", "TRUE"); setting("NOTIFY_NOW_MAX_PER_DAY", "0"); bodies = _wire(monkeypatch); box = _mailbox(monkeypatch); _window(False)
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: True)
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "owner", "item": "whatsapp", "provider": "meta", "units": 1, "inr": 500, "role": "morning"}])
    assert NT.in_quiet_hours() and NT.now_room() <= 0 and WA.over_cap()
    aid = NT.send("kids_flag", "YouTube marked a video as made for kids", dedupe_key="kids|V9")
    told = _alarms_told(); r = _row(aid)
    assert [(x["action_id"], x["wamid"]) for x in told] == [(aid, "wamid.T1")] and bodies[-1]["type"] == "template", told
    assert box == ["URGENT: YouTube marked a video as made for kids"], box
    assert r["tier"] == "now" and r["urgent"] == "TRUE" and int(r["count"]) == 1 and r["delivered_at"] and json.loads(r["buttons"]) == [["Seen", "SEEN"]], r

def test_a_flood_is_one_alarm(monkeypatch, setting):
    """S8 and item 180 (the alert that mattered was #4,000-something): fifty firings of one key are ONE push with a count of 50 - a repeat is counted and
    shown, never a second alarm and never dropped; another alarm in the middle of the flood is its own push."""
    setting("TWO_SCREENS_ON", "TRUE"); _wire(monkeypatch); box = _mailbox(monkeypatch); _window(True)
    first = [NT.send("uploads_private", f"A video is stuck on Private ({i})", dedupe_key="uploads_private") for i in range(25)]
    lock = NT.send("risk_lock", "Uploads locked: a strike was found", dedupe_key="risk|strike")
    first += [NT.send("uploads_private", f"A video is stuck on Private ({i})", dedupe_key="uploads_private") for i in range(25, 50)]
    assert len(set(first)) == 1 and lock != first[0] and [x["action_id"] for x in _alarms_told()] == [first[0], lock]
    r = _row(first[0]); assert int(r["count"]) == 50 and r["last_text"] == "A video is stuck on Private (49)" and r["text"] == "A video is stuck on Private (0)", r
    assert len([x for x in core.store().rows("Owner_Actions") if x["kind"] in ("uploads_private", "risk_lock")]) == 2 and len(box) == 2

def test_a_day_later_it_is_said_again(monkeypatch, setting):
    """A repeat is pushed again only ALARM_REGROUP_H (24) hours after the push he was given, the count in its first words; the next 24 hours count from
    that push."""
    T = dt.datetime(2026, 11, 20, 5, 0, tzinfo=dt.timezone.utc)                                          # Fri 20 Nov, 10:30 India time
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _mailbox(monkeypatch); _window(False)
    def at(h): monkeypatch.setattr(NT, "now_utc", lambda: T + dt.timedelta(hours=h))
    at(0); a = NT.send("money_stop", "Monthly budget reached", dedupe_key="money_stop|2026-11")
    at(1); NT.send("money_stop", "Monthly budget reached (again)", dedupe_key="money_stop|2026-11"); assert len(bodies) == 1
    at(25); assert NT.send("money_stop", "Still at the month's cap", dedupe_key="money_stop|2026-11") == a and len(bodies) == 2
    assert bodies[-1]["template"]["components"][0]["parameters"][1]["text"].startswith("x3 since Fri 10:30: Still at the month's cap"), bodies[-1]
    assert [x["action_id"] for x in _alarms_told()] == [a, a] and _row(a)["delivered_at"] == core.iso(T + dt.timedelta(hours=25))
    at(26); NT.send("money_stop", "Still at the cap", dedupe_key="money_stop|2026-11"); assert len(bodies) == 2 and int(_row(a)["count"]) == 4

EIGHT = ("TWO_SCREENS_ON", "WA_ON", "QUIET_HOURS_IST", "NOTIFY_NOW_MAX_PER_DAY", "DIGEST_DAILY_HOUR_IST", "NEEDS_HOUR_IST", "WA_MONTHLY_CAP_INR", "DASH_ON")
MUTERS = {"in_quiet_hours", "now_room", "over_cap", "ask"}

def _names(src):
    import textwrap
    t = ast.parse(textwrap.dedent(src))
    return {n.id for n in ast.walk(t) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}

def test_no_lever_reaches_the_alarm():
    """Item 180: no department, lever, learned rule, cap or model can mute an alarm - the eight cells around it are his (`strategy.OWNER_ONLY`; each is
    no lever, or a lever whose every move needs his tap: the pin's own expression, tests/test_v12_strategy.py 464), and the alarm's code - `_alarm`,
    its push, its retry and the alarm branch of `wa.push` - names no quiet hours, no daily cap, no money cap and no model (`ast`). PLANTED: a function
    that asks the quiet hours is found."""
    import inspect
    from whatifs.org import strategy as STR, levers as LV
    for k in EIGHT: assert k in STR.OWNER_ONLY and k in core.DEFAULTS and (LV.owner_of(k) == "" or LV.LEVERS[k]["owner"] == "always"), k
    for fn in (NT._alarm, NT._tell, NT.alarm_retry, WA.push, WA._push_alarm):
        assert not _names(inspect.getsource(fn)) & MUTERS, (fn.__name__, _names(inspect.getsource(fn)) & MUTERS)
    assert _names("def f(row):\n    if in_quiet_hours(): return ''\n") & MUTERS == {"in_quiet_hours"}

def test_an_alarm_whatsapp_did_not_take_is_sent_again(monkeypatch, setting):
    """R17 (5 a): a WhatsApp fault in the minute of an alarm must not leave it in a mailbox he does not read - every tick pushes again each open alarm
    WhatsApp has not taken (`notify.tick` begins with `alarm_retry`), and `delivered_at` is stamped only by the push that went."""
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); got = iter(["", "", "wamid.R3"]); kinds = []
    monkeypatch.setattr(WA, "_post", lambda body, kind="reply", now=None: kinds.append(kind) or next(got))
    aid = NT.send("pipeline_stop", "Production paused: a health check failed", dedupe_key="pipeline_stop|preflight|planted")
    assert kinds == ["alarm"] and not _row(aid)["delivered_at"] and _alarms_told() == []                     # attempt 1, at the firing: not taken
    assert NT.tick()["alarms"] == 0 and not _row(aid)["delivered_at"]                                       # attempt 2, the next tick: not taken
    assert NT.tick()["alarms"] == 1 and _row(aid)["delivered_at"]                                           # attempt 3: taken
    assert [(x["action_id"], x["wamid"]) for x in _alarms_told()] == [(aid, "wamid.R3")]
    assert NT.tick()["alarms"] == 0 and kinds == ["alarm"] * 3                                              # told: the retry never pushes it again

def test_an_alarm_through_mail_is_mailed_once(monkeypatch, setting):
    """R17 (5 c): an alarm that comes through `notify.mail` (rows 7, 8, 12, 13, 17, 18, 21 and 22 of PART 2's table) is mailed by `mail` and never a
    second time by the alarm; one sent straight through `send` is mailed by the alarm itself."""
    setting("TWO_SCREENS_ON", "TRUE"); _wire(monkeypatch); box = _mailbox(monkeypatch); _window(True)
    aid = NT.mail("money_stop", "Monthly budget reached", "<p>planted</p>", dedupe_key="money_stop|2099-01")
    assert box == ["Monthly budget reached"] and _row(aid)["kind"] == "money_stop" and [x["action_id"] for x in _alarms_told()] == [aid], box
    NT.send("kids_flag", "YouTube marked a video as made for kids", dedupe_key="kids|V2")
    assert box == ["Monthly budget reached", "URGENT: YouTube marked a video as made for kids"], box

def test_a_pause_does_not_silence_him(monkeypatch, setting):
    """R17 (11 d), typed in step 3 by R18 (2): through a seven-day policy pause he still gets the morning message, an answer to his input and the
    dashboard - the paused branch of `manage.tick` runs the desk, the briefs, the alarm retry and the snapshot before it returns. No default runs (the
    cards' defaults run at the first tick after the pause)."""
    from whatifs import manage as MG
    setting("TWO_SCREENS_ON", "TRUE"); setting("STRATEGY_ON", "TRUE"); setting("PAUSED", "TRUE"); _wire(monkeypatch); _mailbox(monkeypatch)
    D1 = dt.datetime(2026, 11, 20, 4, 0, tzinfo=dt.timezone.utc)                                         # Fri 20 Nov, 09:30 India time
    monkeypatch.setattr(NT, "now_utc", lambda: D1 - dt.timedelta(hours=2))
    card = NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A")], default="A is used", expires_h=1, dedupe_key="bake|pause")      # expired before the first tick
    core.store().append("Owner_Input", [{"input": "more wonder please"}])
    for day in (D1, D1 + dt.timedelta(days=1)):
        monkeypatch.setattr(DG, "now_utc", lambda d=day: d); monkeypatch.setattr(NT, "now_utc", lambda d=day: d); _window(False, day)
        assert MG.tick() == {"action": "paused"}
    assert [r["kind"] for r in core.store().rows("WA_Outbox")] == ["morning", "morning"], core.store().rows("WA_Outbox")
    assert [r["verbatim"] for r in core.store().rows("Owner_Desk") if r.get("verdict")] == ["more wonder please"]
    assert _row(card)["status"] == "OPEN" and not [r for r in core.store().rows("Owner_Actions") if r["status"] == "DEFAULTED"]

def test_the_policy_alarm_keeps_his_resume_tap(monkeypatch, setting):
    """R22 (9) (step 2a's design question 1): `guardian` sends caretaker's card FIRST and the mail follows as its copy - ONE incident with the card's
    three buttons, so his "Resume now" is never lost on either screen; when the card could not be sent, the mail's own row IS the alarm and still
    carries "Resume now"."""
    from whatifs import manage as MG, caretaker as CT
    setting("TWO_SCREENS_ON", "TRUE"); _wire(monkeypatch); box = _mailbox(monkeypatch); _window(False)
    items = [{"change": "AI content is no longer monetised", "source": "https://support.google.com/youtube"}]
    MG.guardian(items)
    pol = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "policy"]
    assert len(pol) == 1 and pol[0]["status"] == "OPEN" and int(pol[0]["count"]) == 1, [(r["status"], r["count"]) for r in pol]
    assert "RESUME" in [v for _l, v in json.loads(pol[0]["buttons"])] and [x["action_id"] for x in _alarms_told()] == [pol[0]["id"]]
    assert "Paused for 7 days (policy watch)" in box and core.S("PAUSED_UNTIL")                             # the e-mail goes exactly as today
    assert NT.answer(pol[0]["id"], "RESUME") == "resumed" and not core.S("PAUSED_UNTIL")
    def boom(items): raise RuntimeError("the model did not answer")
    monkeypatch.setattr(CT, "policy_rescue", boom); MG.guardian(items)
    pol = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "policy" and r["status"] == "OPEN"]
    assert len(pol) == 1 and json.loads(pol[0]["buttons"]) == [["Resume now", "RESUME"]] and pol[0]["text"].startswith("Paused for 7 days (policy watch)"), pol

def test_a_failed_copy_still_reaches_the_screens(monkeypatch, setting):
    """R22 (10) (item 149: e-mail is only the copy; step 2a's design question 2): an e-mail that RAISES (a token refresh, a post) never takes the row with
    it - the screens he reads keep the message; an alarm whose copy raised still tries its own URGENT mail and is still pushed."""
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); _wire(monkeypatch); _window(True); tried = []
    def boom(subj, html, kind="essential"): tried.append(str(subj)); raise RuntimeError("the token refresh failed")
    monkeypatch.setattr(PUB, "email", boom)
    a = NT.mail("budget_pct", "Budget: 90% of this month's cap used", "<p>planted</p>")
    assert [r["kind"] for r in core.store().rows("Owner_Actions")] == ["budget_pct"] and _row(a)["kind"] == "budget_pct"
    k = NT.mail("kids_flag", "URGENT: YouTube marked a video as made for kids", "<p>planted</p>", dedupe_key="kids|V3")
    assert _row(k)["kind"] == "kids_flag" and [x["action_id"] for x in _alarms_told()] == [k]
    assert len(tried) == 3 and tried[-1].startswith("URGENT: URGENT: YouTube"), tried                     # the alarm's own mail was still tried
    assert NT.mail("cost_check", "Weekly cost check", "<p>planted</p>", screens=False) is False
    setting("TWO_SCREENS_ON", "FALSE")
    with pytest.raises(RuntimeError): NT.mail("budget_pct", "Budget: 95%", "<p>planted</p>")              # the older path raises as today
