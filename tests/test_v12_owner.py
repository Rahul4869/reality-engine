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
    # step 6: the dashboard's docket is the same list
    from whatifs import dash as DS
    assert {c["id"] for c in DS.build_snapshot()["docket"]} == {unk, hold, card}

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
OWN_IDS = ("EP209911260900", "EP209911260930", "EP209911260945", "SHSPARSE10")          # the whole productions of this file (step 10b: the sparse clock's Short): ids no other test file uses (a test proves it)

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
    (4, "costguard.py spend_monitor", "budget_pct", "Budget: 90% of this month's cap used", "row", "budget_pct|90|{month}", {}, _r4),
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
    (28, "packaging.py _pick_reply", "pick_ack", "Your pick for EPROW28: applied: B", "row", "pick_ack|EPROW28|applied: B|1", {}, _r28),
    (29, "premise.py below_bar_mail", "below_bar", "A video was made below the quality bar", "row", "below_bar|EPROW29|{india_day}", {}, _r29),
    (30, "premise.py skip_slot", "slot_skipped", "A slot was skipped", "row", "slot_skipped|EPROW30|{india_day}", {}, _r30),
    (31, "preview.py run (nothing reached the bar)", "preview_none", "Script Preview: nothing reached the bar", "row", None, {}, _r31),
    (32, "preview.py run", "script_preview", "Script Preview: ", "row", "preview|DRAFT209911270900",
     {"text": "A script preview is ready. It is in your e-mail.", "buttons": [["Approve", "APPROVE DRAFT209911270900"], ["Reject", "REJECT DRAFT209911270900"]],
      "default_action": "the draft is not used: the next slot writes its own script"}, _r32),
    (33, "preview.py decide (MODE)", "mode_ack", "Budget mode: Standard", "row", None, {}, _r33),
    (34, "sheets.py masters", "sheets_review", "New Toybox Noir character masters to approve", "row", "sheets|masters|VALE|{india_day}",
     {"buttons": [["Approve VALE", "APPROVE SHEET VALE"]], "default_action": "they lock by themselves"}, _r34),
    (35, "sheets.py run", "sheets_review", "Character sheets ready to review", "row", "sheets|expressions|{india_day}",
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
            btn = kw.get("buttons", n.args[2] if n.func.attr == "send" and len(n.args) > 2 else (n.args[5] if n.func.attr == "mail" and len(n.args) > 5 else None))
            if btn is None or (isinstance(btn, (ast.List, ast.Tuple)) and not btn.elts): continue
            if "default" not in kw or "expires_h" not in kw: bad.append(f"{rel}:{n.lineno}: {kind}")
    return bad

def test_every_card_has_a_default_and_an_expiry():
    """PART 7 (item 150: his absence never holds a post): every card he is sent says what his silence does and when - the build refuses one that
    does not (at run time `send` only gives it the fallback and names it). HOLD and the standing kinds are the only exemptions, and the hold list
    is pinned (test_the_lists_are_pinned). PLANTED: a card with buttons and no default is found; a hold and an inform are not."""
    files = list(_py_files()); assert _cards_without_a_default(files) == [], _cards_without_a_default(files)
    planted = 'NT.send("bakeoff", "Pick", [("A", "PICK A")], expires_h=48)\nNT.send("contract_hold", "Held", [("Fix", "FIX")])\nNT.send("budget_pct", "80%")\n' \
              'NT.mail("title_pick", "Pick", "<p>x</p>", buttons=[("A", "PICK A")], default="A goes out")\n' \
              'NT.mail("voice_pick", "Pick", "<p>x</p>", "essential", True, [("A", "PICK A")])\n'
    assert _cards_without_a_default([("whatifs/x.py", planted)]) == ["whatifs/x.py:1: bakeoff", "whatifs/x.py:4: title_pick", "whatifs/x.py:5: voice_pick"]

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

SENDERS = ("send_text", "send_buttons", "send_list", "send_image", "send_menu", "send_section", "send_group", "send_template", "reply_answer")

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
        if rel == "whatifs/org/desk.py":                                 # the desk's answer at a tick: ONE caller of `reply_answer`, and of no other sender
            for f in tree.body:
                if isinstance(f, ast.FunctionDef) and f.name == "_tick_two":
                    allowed = {id(n) for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "reply_answer"}
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
    # step 6: the dashboard's groups carry the same rows
    from whatifs import dash as DS
    g = DS.build_snapshot()["groups"]
    assert any("Budget: 80% of the cap" in x["text"] for x in g["money"]) and any("One region dominates" in x["text"] for x in g["research"]), g

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
    # step 6: and on the dashboard, pinned first on Home
    from whatifs import dash as DS
    al = DS.build_snapshot()["alarms"]
    assert [(a["id"], a["count"]) for a in al] == [(aid, 1)] and "made for kids" in al[0]["text"] and list(al[0]["buttons"].values()) == [f"ACT|{aid}|0"], al

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
    assert len(tried) == 3 and tried[-1].startswith("URGENT: YouTube"), tried                     # the alarm's own mail was still tried
    assert NT.mail("cost_check", "Weekly cost check", "<p>planted</p>", screens=False) is False
    setting("TWO_SCREENS_ON", "FALSE")
    with pytest.raises(RuntimeError): NT.mail("budget_pct", "Budget: 95%", "<p>planted</p>")              # the older path raises as today

# ------------------------------------------------------------------ step 5: HIS INPUT DESK (PART 5, items 149 and 138) - one store for both screens
from whatifs.org import desk as DESK
LABELS = {"kind": "preference", "restated": "r", "department": "D4", "raises_breakout": True, "why": "w", "needs_code": False, "new_arm": False}

def _desk_on(setting): setting("TWO_SCREENS_ON", "TRUE"); setting("STRATEGY_ON", "TRUE")
def _desk_rows(): return core.store().rows("Owner_Desk")

def _labels(monkeypatch, **w):
    """The weigher's reply, faked (the model LABELS; code decides): a preference for the writers' room that raises the breakout unless told otherwise."""
    calls = []; monkeypatch.setattr(DESK, "weigh", lambda text: calls.append(text) or {**LABELS, **w}); return calls

def _inbound(monkeypatch, mid, text):
    """One typed WhatsApp message through the real `handle_inbound` (the relay's encryption as tests/test_v94b.py does it)."""
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.b64encode(bytes(range(32))).decode(); monkeypatch.setenv("WA_RELAY_KEY", key); n = os.urandom(12)
    c = AESGCM(base64.b64decode(key)).encrypt(n, json.dumps({"messages": [{"id": mid, "type": "text", "text": text}]}).encode(), None)
    return WA.handle_inbound(json.dumps({"c": base64.b64encode(c).decode(), "n": base64.b64encode(n).decode()}))

def test_an_input_is_kept_word_for_word_once(monkeypatch, setting):
    """PART 5: his words from either screen are stored AT ONCE, word for word (up to 4,000 characters) with their channel, card and id; the same message
    twice is stored once, the same words from the other screen are a second input; every row gets the owner memo, as the tab's rows do today."""
    _desk_on(setting); calls = _labels(monkeypatch, kind="feedback")
    words = "  The last Short felt slow in its first two seconds;\nstart on the moving picture.  "
    n1, a1 = DESK.take(words, "whatsapp", ref="wamid.A")
    assert DESK.take(words, "whatsapp", ref="wamid.A") == (n1, "")
    n2, _a = DESK.take(words, "dashboard", ref="act-7", card="C9")
    rows = _desk_rows(); assert [r["verbatim"] for r in rows] == [words, words] and n2 == n1 + 1, rows
    assert [(r["channel"], r["ref"], r["card"]) for r in rows] == [("whatsapp", "wamid.A", ""), ("dashboard", "act-7", "C9")]
    assert all(r["verdict"] == "PARKED" and r["memo"] for r in rows) and len(calls) == 2 and a1.startswith(f"Your input {n1}: PARKED"), (rows, a1)
    DESK.take("y" * 4500, "dashboard", ref="act-8"); assert _desk_rows()[-1]["verbatim"] == "y" * 4000

def test_code_decides_the_verdict(monkeypatch, setting):
    """Item 138's three conditions are code: TAKEN needs all five labels (a preference, it raises the breakout, no code, no new arm, a department) -
    flip any one alone and it is PARKED; every other kind has its own plain answer, and a change he wants built is an `idea` row he can tap."""
    row = {"n": 7}
    assert DESK.decide(dict(LABELS), row)[0] == "TAKEN"
    for flip in ({"kind": "video_idea"}, {"raises_breakout": False}, {"needs_code": True}, {"new_arm": True}, {"department": "none"}):
        assert DESK.decide({**LABELS, **flip}, row)[0] == "PARKED", flip
    assert DESK.decide({**LABELS, "kind": "question"}, row)[0::2] == ("ANSWERED", "chat")
    assert "a topic" in DESK.decide({**LABELS, "kind": "video_idea"}, row)[1] and "Good / Not good" in DESK.decide({**LABELS, "kind": "feedback"}, row)[1]
    assert DESK.decide({**LABELS, "kind": "other", "restated": "he wants less red", "why": "a colour wish"}, row)[1] == "read as: he wants less red. a colour wish."
    _desk_on(setting); _labels(monkeypatch, kind="change_request", department="none")
    n, line = DESK.take("Add a countdown clock to every cold open of the long videos.", "dashboard", ref="act-1")
    idea = _row(_desk_rows()[-1]["action"]); assert "it needs a code change" in line and idea["kind"] == "idea", (line, idea)
    assert json.loads(idea["buttons"]) == [["Build it", "BUILD"], ["Not now", "PARK"]] and not idea["default_action"] and not idea["expires_at"]

def test_a_taken_input_is_his_word_in_the_palace(monkeypatch, setting):
    """R17 (10 c): a TAKEN input enters the Palace as HIS word - kind owner_preference, owner_input, accepted by the owner himself, his words (never the
    model's restatement) - and the answer says where and when, with a "Take it back" button."""
    from whatifs.org import palace as PAL
    _desk_on(setting); _labels(monkeypatch, restated="the model's own words"); words = "Open every Short on the moving picture, never on a title card."
    n, line = DESK.take(words, "dashboard", ref="act-1")
    it = PAL.get(PAL.item_id(f"owner_input|{n}")); r = _desk_rows()[-1]
    assert it["kind"] == "owner_preference" and it["owner_input"] and it["status"] == "accepted" and it["summary"] == words and it["departments"] == ["D4"], it
    assert words in json.dumps(PAL.body(it["id"])) and "the model's own words" not in json.dumps(PAL.body(it["id"])) + it["summary"]
    assert line.startswith(f"Your input {n}: TAKEN - kept word for word as your standing preference for Creative") and it["id"] in line, line
    assert r["verdict"] == "TAKEN" and json.loads(_row(r["action"])["buttons"]) == [["Take it back", f"DESK UNDO {n}"]]
    assert DESK.take("Make it calmer.", "dashboard", ref="act-2")[1].endswith("PARKED - too short to keep as a standing rule.")

def test_a_taken_item_is_served(monkeypatch, setting):
    """R17 (10 c): "proposed" never reaches a brief - his item is accepted, so the writers' room's playbook holds his words from the next script."""
    from whatifs.org import palace as PAL
    _desk_on(setting); _labels(monkeypatch); words = "Every long video ends on the feeling, never on a list of facts."
    n, _l = DESK.take(words, "whatsapp", ref="wamid.S")
    pb = PAL.playbook("D4", record=False); assert PAL.item_id(f"owner_input|{n}") in pb["items"] and words in pb["text"], pb["text"]

def test_a_taken_input_can_be_taken_back(monkeypatch, setting):
    """R17 (10 d), item 150's Undo: "Take it back" retires the item by the owner's own move and the desk row says so."""
    from whatifs.org import palace as PAL
    _desk_on(setting); _labels(monkeypatch); n, _l = DESK.take("Every long video ends on the feeling, never on a list of facts.", "dashboard", ref="act-3")
    aid = _desk_rows()[-1]["action"]; NT.register("desk", on_answer=DESK._do)
    assert NT.answer(aid, f"DESK UNDO {n}").startswith("taken back ")
    assert PAL.get(PAL.item_id(f"owner_input|{n}"))["status"] == "retired" and _desk_rows()[-1]["how"].startswith("taken back ")
    assert PAL.item_id(f"owner_input|{n}") not in PAL.playbook("D4", record=False)["items"]

def test_the_never_list_parks_with_its_reason(monkeypatch, setting):
    """LAUNCH_MAX C6: an input that asks for what this channel never does is PARKED with the words that hit and the risk - no call is paid for it."""
    _desk_on(setting); calls = _labels(monkeypatch)
    for i, t in enumerate(("Let's buy 5,000 views for the next Short.", "Just re-upload the best Short every week.", "Hide the AI label, it looks cheap.")):
        assert "which this channel never does" in DESK.take(t, "dashboard", ref=f"act-n{i}")[1]
    assert calls == [] and all(r["verdict"] == "PARKED" for r in _desk_rows())
    assert DESK.never("Show more of the night sky in every Short.") is None and DESK.never("Copy that channel's video") is not None

def test_an_idea_seven_days_old_is_never_parked_unanswered(monkeypatch, setting):
    """Item 149 (GAP 2): his own "Build this?" card from WhatsApp had a 7-day default of PARKED - with the switch on it has no default and no expiry: 8 days
    on `expire_defaults` leaves it OPEN and the morning group "Your inputs" lists it."""
    _desk_on(setting); _wire(monkeypatch); _labels(monkeypatch, kind="other")
    monkeypatch.setattr(WA, "chat", lambda text, deep=False: ("Good idea.", "show a countdown clock in cold opens, switch COLD_OPEN_CLOCK_ON", "tweak"))
    _inbound(monkeypatch, "wamid.I1", "add a countdown clock to cold opens")
    idea = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "idea")
    assert not idea["default_action"] and not idea["expires_at"], idea
    NT.expire_defaults(core.now_utc() + dt.timedelta(days=8)); assert _row(idea["id"])["status"] == "OPEN"
    assert idea["id"] in _ids(NT.group_rows("inputs")) and "Build this?" in WA.group_text("inputs")

def test_every_input_is_answered(monkeypatch, setting):
    """After the tick no row has an empty answer unless the call failed - and then it says so: a failed call is tried at the next two ticks, then STORED;
    above DESK_MONTHLY_CAP_INR no call is made and the answer says on which day it is read (the desk's cap case of item 146)."""
    _desk_on(setting); boom = []
    def fail(text): boom.append(text); raise RuntimeError("the model did not answer")
    monkeypatch.setattr(DESK, "weigh", fail)
    n, ack = DESK.take("More of the night sky in every Short, please.", "dashboard", ref="act-f")
    assert ack == DESK.ACK.format(n=n) and _desk_rows()[-1]["verdict"] == "" and "tried again" in _desk_rows()[-1]["how"]
    DESK.tick(); assert _desk_rows()[-1]["verdict"] == ""
    DESK.tick(); r = _desk_rows()[-1]; assert len(boom) == 3 and r["verdict"] == "STORED" and r["how"] == "it could not be read; it is kept word for word", r
    core.store().append("Owner_Input", [{"input": "Warmer colours in the Shorts, please."}]); _labels(monkeypatch); DESK.tick()
    assert all(r["verdict"] for r in _desk_rows()) and _desk_rows()[-1]["channel"] == "sheet"
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "owner", "item": "claude_board_c", "provider": "anthropic", "units": 1, "inr": 41, "role": "owner_desk"}])
    calls = _labels(monkeypatch); n, ack = DESK.take("Slower music under the hook, please.", "dashboard", ref="act-c")
    assert calls == [] and _desk_rows()[-1]["verdict"] == "" and "Rs 40" in ack and "is read on 01 " in ack, ack

def test_a_question_is_answered_once(monkeypatch, setting):
    """R17 (10 b): a question typed on WhatsApp is answered by the chat - ONE reply, no acknowledgement, no desk line - and stamped briefed, so the next
    morning does not count it again."""
    _desk_on(setting); bodies = _wire(monkeypatch); _labels(monkeypatch, kind="question", department="none", raises_breakout=False)
    monkeypatch.setattr(WA, "chat", lambda text, deep=False: ("Three Shorts went out this week.", "", "feature"))
    _inbound(monkeypatch, "wamid.Q1", "how many shorts went out this week?")
    r = _desk_rows()[-1]; texts = [b["text"]["body"] for b in bodies if b.get("type") == "text"]
    assert r["verdict"] == "ANSWERED" and r["briefed"] and texts == ["Three Shorts went out this week."], (r, texts)
    assert DESK.lines() == []

def test_talk_is_not_an_input(monkeypatch, setting):
    """R17 ADDS (D): "ok thanks" is talk - the chat answers it, nothing is stored and no strong call is paid; "more wonder please" is an input."""
    _desk_on(setting); _wire(monkeypatch); calls = _labels(monkeypatch); monkeypatch.setattr(WA, "chat", lambda text, deep=False: ("Noted.", "", "feature"))
    assert DESK.talk("Ok, thanks!") and DESK.talk("good night") and not DESK.talk("ok thanks but slower") and not DESK.talk("")
    _inbound(monkeypatch, "wamid.T1", "Ok, thanks!"); assert _desk_rows() == [] and calls == []
    _inbound(monkeypatch, "wamid.T2", "more wonder please"); assert [r["verbatim"] for r in _desk_rows()] == ["more wonder please"] and calls == ["more wonder please"]

# ------------------------------------------------------------------ step 6: both screens show the same, and he sees the learning (PART 6)
from whatifs import dash as DS

def _dash_action(monkeypatch, obj):
    """One tap of the page as the Worker forwards it (the relay's encryption, as tests/test_v94b.py does it)."""
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.b64encode(bytes(range(32))).decode(); monkeypatch.setenv("WA_RELAY_KEY", key); n = os.urandom(12)
    c = AESGCM(base64.b64decode(key)).encrypt(n, json.dumps(obj).encode(), None)
    return json.dumps({"c": base64.b64encode(c).decode(), "n": base64.b64encode(n).decode()})

def test_a_dashboard_input_reaches_his_desk_and_the_ack_never_holds_his_words(monkeypatch, setting):
    """PART 6 (item 149: "my inputs taken from either"): the page's box posts to the Worker's route api/input, which forwards the verb INPUT;
    `dash.handle_action` gives his words to `desk.take` (channel "dashboard", ref = the action's id, the card it was typed under) and the job weighs them
    at once; the Dash_Acks row holds the verb and "Saved as input N" - never his words; the same delivery twice is stored once; the snapshot shows the
    input with its verdict and its answer. With the switch off INPUT is no verb of today's dashboard."""
    _desk_on(setting); calls = _labels(monkeypatch, kind="feedback")
    words = "The thumbnails feel too dark on my phone"
    tap = _dash_action(monkeypatch, {"id": "d-1", "verb": "INPUT", "text": words, "card": "A20261120", "ts": 1, "src": "dash"})
    assert DS.handle_action(tap) and DS.handle_action(tap)                                              # the second delivery is handled once
    rows = _desk_rows()
    assert [(r["verbatim"], r["channel"], r["ref"], r["card"]) for r in rows] == [(words, "dashboard", "d-1", "A20261120")] and calls == [words], rows
    acks = core.store().rows("Dash_Acks")
    assert [(a["verb"], a["ok"], a["note"]) for a in acks] == [("INPUT", "TRUE", f"Saved as input {rows[0]['n']}")] and words not in json.dumps(acks), acks
    inp = DS.build_snapshot()["inputs"]
    assert [(x["text"], x["channel"], x["verdict"]) for x in inp] == [(words, "dashboard", "PARKED")] and inp[0]["answer"], inp
    setting("TWO_SCREENS_ON", "FALSE")
    assert DS.handle_action(_dash_action(monkeypatch, {"id": "d-2", "verb": "INPUT", "text": "x", "card": "", "ts": 2, "src": "dash"})) is False
    assert len(_desk_rows()) == 1

def test_both_screens_show_the_same_and_what_ran_by_default(monkeypatch, setting):
    """PART 6: with the switch off every new field of the snapshot exists and is empty (the older page reads them: tests/test_v94b.py 39-44); with it
    on, "Decided for you" holds the open decided rows with their Undo or "Take it down" and every row his silence decided in the last 48 hours ("ran by
    default", no button left), a desk or idea row is under his inputs and never there, the eight groups are WhatsApp's groups, and the money, the
    learning and the plan carry what lands with a later batch as a plain note."""
    setting("TWO_SCREENS_ON", "FALSE"); off = DS.build_snapshot()
    assert off["alarms"] == [] and off["inputs"] == [] and off["groups"] == {g: [] for g in NT.GROUPS}, off["groups"]
    assert off["plan"]["lines"] == [] and off["learning"]["lessons"] == [] and off["money"]["whatsapp"] == {} and off["money"]["treasury"]["note"]
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    post = NT.send("decided_post", "EP3 was approved by your silence and goes public at 20:30", [("Take it down", "UNPOST EP3")], expires_h=168)
    strat = NT.send("strategy", "Strategy moved one lever")
    idea = NT.send("idea", "Build this? a slower first second", [("Build it", "BUILD"), ("Not now", "PARK")])
    card = NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A")], default="A is used", expires_h=1)
    assert NT.expire_defaults(core.now_utc() + dt.timedelta(hours=2)) == 1 and _row(card)["status"] == "DEFAULTED"
    snap = DS.build_snapshot(); dec = {c["id"]: c for c in snap["decided"]}
    assert set(dec) == {post, strat, card}, dec
    assert dec[post]["verbs"] == {"Take it down": f"ACT|{post}|0"} and dec[card]["verbs"] == {} and dec[card]["default_label"] == "ran by default: A is used", dec
    assert [x["id"] for x in snap["groups"]["inputs"]] == [idea] and card not in {c["id"] for c in snap["docket"]}
    from whatifs import manage as MG                                                                    # the next five slots inside next_slots' 21 days (3 at one a week)
    assert snap["plan"]["slots"] and [s["at"] for s in snap["plan"]["slots"]] == [s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in MG.next_slots(5)]
    assert snap["money"]["whatsapp"]["src"] and "cap" in snap["money"]["whatsapp"]
    assert snap["learning"]["appetite"]["note"].endswith("batch V4b.") and snap["plan"]["department_line"]["note"]

def test_no_number_without_its_source(monkeypatch, setting):
    """PART 6 (P13's lesson: never a number without its source). PLANTED: a research item with views and no `src` is left out of the snapshot and an
    error is logged; the same kind of item with its source stays."""
    from whatifs import owner_view as OV
    setting("TWO_SCREENS_ON", "TRUE"); logged = []
    monkeypatch.setattr(DS, "log", lambda msg, level="INFO": logged.append((level, msg)))
    monkeypatch.setattr(OV, "hot_topics", lambda n=5: {"topics": [{"topic": "Glass that bends", "views": 120000},
                                                                  {"topic": "Rain that falls up", "views": 90000, "src": "Trend_Brief", "date": "2026-11-19"}], "outliers": []})
    snap = DS.build_snapshot(); topics = snap["learning"]["research"]["topics"]
    assert [t["topic"] for t in topics] == ["Rain that falls up"] and "Glass that bends" not in json.dumps(snap), topics
    assert any(lv == "ERROR" and "without a source" in m for lv, m in logged), logged
    assert DS.unsourced({"plan": {"x": {"inr": 5}}, "money": {"whatsapp": {"spent": 3, "src": "Cost_Log"}}}) == [{"inr": 5}]

def test_a_planted_secret_and_a_planted_script_do_not_show(monkeypatch, setting):
    """PART 6 (dash.py's own rule: no secrets, scripts or unreleased premises; the experiment found a special's script in the docket). PLANTED: a row
    holding a key and a `special_ready` row holding its script - neither string is in the snapshot; the special shows as its plain name with its button."""
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); key = "fal-PLANTED-0123456789abcdef"; monkeypatch.setenv("FAL_KEY", key)
    a = NT.send("bakeoff", f"The clip test failed with {key} in the reply", [("Pick A", "PICK A")], default="A is used", expires_h=48)
    b = NT.send("special_ready", "Script: GRIMM: the jar opens at midnight and the moon falls in", [("Approve", "APPROVE S1")],
                default="posted after 72 hours when its checks passed", expires_h=72)
    assert key in _row(a)["text"] and "GRIMM: the jar opens" in _row(b)["text"]                          # the rows hold them: the dashboard must not show them
    snap = DS.build_snapshot(); text = json.dumps(snap)
    assert key not in text and "GRIMM: the jar opens" not in text, text[:400]
    docket = {c["id"]: c for c in snap["docket"]}
    assert docket[b]["title"] == "A special is ready: the text is in WhatsApp and your e-mail." and list(docket[b]["verbs"]) == ["Approve"] and "***" in docket[a]["why"]

# ------------------------------------------------------------------ FINISHED BY FABLE: the corrections of the finishing pass (steps 0 to 3)
def test_a_paused_tick_retries_an_alarm(monkeypatch, setting):
    """R17 (5 a) with (11 d): through a pause an alarm WhatsApp did not take is pushed again at the paused tick. FOUND AT THE FINISH: `manage.tick` held
    a local import of notify as NT further down, which made NT a local name of the whole function - the paused branch's `NT.alarm_retry()` raised
    inside its own try and the retry never ran in a pause (the fault step 2b took out of `preview.decide`)."""
    from whatifs import manage as MG
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); got = iter(["", "wamid.P2"])
    monkeypatch.setattr(WA, "_post", lambda body, kind="reply", now=None: next(got) if kind == "alarm" else "wamid.other")
    aid = NT.send("policy", "Paused for 7 days (policy watch)", dedupe_key="policy|planted")
    assert not _row(aid)["delivered_at"] and _alarms_told() == []                                           # the firing's own push was not taken
    setting("PAUSED", "TRUE"); assert MG.tick() == {"action": "paused"}
    assert [(x["action_id"], x["wamid"]) for x in _alarms_told()] == [(aid, "wamid.P2")] and _row(aid)["delivered_at"]

def test_two_budget_thresholds_on_one_day_are_two_rows(monkeypatch, setting):
    """R17 (4) for row 4 of PART 2's table (step 2b's design question; R1-41 (2)): "Budget: 70%" and "Budget: 90%" crossed by two calls on ONE India
    day are two rows - the inform rule's dated key swallowed the second. The key is the threshold and the month; the rule's expiry still closes each."""
    from whatifs import costguard as CG, governor as G
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); share = [0.75]
    monkeypatch.setattr(CG, "month_spend", lambda: G.cap_inr() * share[0])
    assert CG.spend_monitor() == [70]
    share[0] = 0.95; assert CG.spend_monitor() == [90]
    rows = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "budget_pct"]; mk = core.now_utc().strftime("%Y-%m")
    assert [r["dedupe_key"] for r in rows] == [f"budget_pct|70|{mk}", f"budget_pct|90|{mk}"] and "90%" in rows[1]["text"], [(r["dedupe_key"], r["text"][:40]) for r in rows]
    assert all(r["expires_at"] and r["status"] == "OPEN" for r in rows)

def test_every_decision_has_a_plain_name():
    """PART 4 ("title the kind's plain name"; item 149: simple for a layman): every kind that can stand under "Needs you" or as an alarm has a plain
    name of its own within WhatsApp's 24 characters - never the code's word ("Floor eye", "Hd blocked", "Ypp tier"); a kind outside the table keeps
    its own word with spaces."""
    asked = [k for k, (c, _g) in NT.KINDS.items() if c in (NT.ALARM, NT.HOLD, NT.CARD)]
    assert len(asked) == 49 and set(NT.NAMES) == set(asked), sorted(set(asked) ^ set(NT.NAMES))
    for k in asked:
        n = NT.name(k); assert n == NT.NAMES[k] and 3 < len(n) <= 24 and "_" not in n and n[0].isupper(), (k, n)
    assert NT.name("floor_eye") == "Watch before it posts" and NT.name("hd_blocked") == "Video kept private" and NT.name("ypp_tier") == "Apply for monetisation"
    assert NT.name("pick_ack") == "Pick ack" and NT.name("zz_never_registered") == "Zz never registered" and len(NT.name("x" * 40)) == 24

def test_a_groups_buttons_are_whole_words(monkeypatch, setting):
    """S4 (a reply button holds 20 characters): the three buttons under a group are whole labels - "Research & observations" (23) is "Research" on a
    button, never "Research & observatio"."""
    from whatifs import charts as CH
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _window(True)
    monkeypatch.setattr(CH, "money_chart", lambda view, path=None: None); monkeypatch.setattr(CH, "numbers_chart", lambda view, path=None: None)
    titles = {}
    for g in NT.GROUPS:
        WA.send_group(g); titles[g] = [b["reply"]["title"] for b in bodies[-1]["interactive"]["action"]["buttons"]]
    whole = {t for _g, t in WA.MENU_GROUPS} | {"Menu", "Research", "Open the list", "Undo or take down"}
    assert titles["learned"][:2] == ["Menu", "Research"] and all(t in whole for ts in titles.values() for t in ts), titles

def test_with_the_switch_off_mail_is_the_call_of_today(monkeypatch, setting):
    """PART 2: TWO_SCREENS_ON FALSE = `PUB.email(subject, html, kind=level)`, word for word - the level reaches the mail, the mail's own answer comes
    back and no row is written."""
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "FALSE"); got = []
    monkeypatch.setattr(PUB, "email", lambda subj, html, kind="essential": got.append((subj, html, kind)) or "the mail's own answer")
    assert NT.mail("scheduled", "Video scheduled", "<p>x</p>", level="info", episode="EP1", dedupe_key="scheduled|EP1") == "the mail's own answer"
    assert got == [("Video scheduled", "<p>x</p>", "info")] and core.store().rows("Owner_Actions") == []

def test_a_tap_on_a_mails_button_reaches_what_its_link_reached(monkeypatch, setting):
    """PART 2: a row made from a mail carries the mail's own links as buttons (rows 27, 32, 34 and 35 of the table). His tap on one must reach the
    function the link reaches - `notify.answer` hands PICK, APPROVE DRAFT, REJECT DRAFT and APPROVE SHEET to `preview.decide`; a verb it does not
    know would be recorded and change nothing."""
    from whatifs import preview as PV
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); seen = []
    monkeypatch.setattr(PV, "decide", lambda title: seen.append(title) or "done")
    cases = (("title_pick", [("Keep A", "PICK EPT1 A"), ("Pick B", "PICK EPT1 B")], "PICK EPT1 B"),
             ("script_preview", [("Approve", "APPROVE DRAFT209911270900"), ("Reject", "REJECT DRAFT209911270900")], "REJECT DRAFT209911270900"),
             ("sheets_review", [("Approve VALE", "APPROVE SHEET VALE")], "APPROVE SHEET VALE"))
    for kind, btns, verb in cases:
        aid = NT.mail(kind, "Planted", "<p>x</p>", buttons=btns, default="planted", expires_h=24, dedupe_key=f"tap|{kind}")
        assert verb in [v for _l, v in json.loads(_row(aid)["buttons"])] and NT.answer(aid, verb) == "done" and _row(aid)["status"] == "ANSWERED", kind
    assert seen == [c[2] for c in cases], seen

def test_a_mails_row_keeps_the_address_he_must_open(monkeypatch, setting):
    """R1-52 (4), inside PART 2 (item 149: the screens are the road, the mail only the copy): a row made from a mail writes out the address of a link he
    must follow, as the memo writes one in a row ("<words>: <address>") - only https, never an address with a query or a fragment (a one-tap or signed
    link), never in a row whose button already is the road, never doubled when the link's words are the address, and the cut at 1,500 characters
    never leaves half of one. With the switch off nothing changes."""
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    a = NT.mail("topup", "Top-up reminder", "<ul><li><b>fal.ai</b>: about 3 days left. <a href='https://fal.ai/dashboard/billing'>Top up here</a>, then add the amount.</li></ul>", dedupe_key="topup|L1")
    assert "Top up here: https://fal.ai/dashboard/billing, then add the amount." in _row(a)["text"], _row(a)["text"]
    b = NT.mail("live", "We're live", "<p>Your first video is live: <a href='https://youtu.be/abc123'>https://youtu.be/abc123</a></p>", dedupe_key="live|L2")
    assert _row(b)["text"].count("https://youtu.be/abc123") == 1
    c = NT.mail("headroom", "Planted", "<p><a href='https://github.com/me/re/issues/new?title=MERGE%20%237'>Merge it</a> or <a href='http://example.com/x'>read</a> or <a href='https://example.com/p#frag'>jump</a></p>", dedupe_key="headroom|L3")
    assert "http" not in _row(c)["text"] and "Merge it or read or jump" in _row(c)["text"], _row(c)["text"]
    d = NT.mail("build_ready", "Change ready to merge: #7", "<p><a href='https://github.com/me/re/pull/7'>Review it on GitHub first</a></p>", buttons=[("Merge", "MERGE #7"), ("Reject", "REJECT #7")],
                default="it waits", expires_h=168, dedupe_key="build|L4")
    assert "https://" not in _row(d)["text"]                                                              # the buttons are the road
    long = "<p>" + "x" * 1440 + " <a href='https://studio.youtube.com/video/vidLINK0001/edit'>open in Studio</a> and more words after it</p>"
    e = NT.mail("cost_check", "Planted", long, dedupe_key="cost_check|L5")
    assert "http" not in _row(e)["text"] and _row(e)["text"].endswith("open in Studio:") and len(_row(e)["text"]) <= 1500, _row(e)["text"][-80:]
    k = NT.mail("uploads_private", "A video is stuck on Private", "<p>Episode EP1 (<a href='https://studio.youtube.com/video/vid1/edit'>open in Studio</a>) did not become public.</p>", dedupe_key="uploads_private|L6")
    assert "(open in Studio: https://studio.youtube.com/video/vid1/edit) did not become public." in _row(k)["text"]      # an alarm's row: its only button is "Seen"
    setting("TWO_SCREENS_ON", "FALSE")
    assert NT.mail("topup", "Top-up reminder", "<a href='https://fal.ai/dashboard/billing'>Top up here</a>") is True and len(core.store().rows("Owner_Actions")) == 6

def test_a_groups_line_never_holds_half_an_address(monkeypatch, setting):
    """R1-55 (CA-7b; bound (d) of R1-52 (4)): a group's line is a row cut at 300 characters - an address is whole in it or not in it; a row without an
    address is cut exactly as before, byte for byte."""
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    two = "<p>" + "a" * 200 + " <a href='https://fal.ai/dashboard/billing'>Top up here</a> and " + "b" * 4 + " <a href='https://platform.claude.com/settings/billing'>Top up here</a> then more</p>"
    NT.mail("topup", "Top-up reminder", two, dedupe_key="topup|G1"); plain = "c" * 400; NT.send("budget_pct", plain, dedupe_key="budget_pct|G2")
    lines = WA.group_text("money", cut=None).splitlines()
    top = next(l for l in lines if "Top-up reminder" in l); flat = next(l for l in lines if l.startswith("- ccc"))
    assert top.count("https://") == 1 and "https://fal.ai/dashboard/billing" in top and top.endswith("Top up here:") and len(top) <= 302, top
    assert flat == "- " + plain[:300]
    assert NT.whole("x" * 10, 4) == "xxxx" and NT.whole("go https://a.b/c now", 16) == "go https://a.b/c"
    assert NT.whole("go https://a.b/c now", 12) == "go" and NT.whole("go https://a.b/c now", 8) == "go" and NT.whole("short", 300) == "short"
    import re
    NT.send("topup", "Top-up reminder. " + "g" * 70 + " Top up here: https://fal.ai/dashboard/billing then add it.", dedupe_key="topup|G3")
    h = DG.head()                                                                     # the morning head: its top-up lines are cut at 120
    assert all(u in ("https://fal.ai/dashboard/billing", "https://platform.claude.com/settings/billing") for u in re.findall(r"https://[^\s,]+", h)), h
    bodies = _wire(monkeypatch); _window(False)
    WA.send_open("Alarm", "x" * 680 + " https://studio.youtube.com/video/vid9/edit", "OPEN|alarm|G4"); WA.send_open("Alarm", "y" * 800, "OPEN|alarm|G5")
    said = [b["template"]["components"][0]["parameters"][1]["text"] for b in bodies[-2:]]
    assert said == ["x" * 680, "y" * 700], [s[-60:] for s in said]                    # an address whole or not there; a text without one cut as before

def test_two_sheets_offers_on_one_day_are_two_cards(monkeypatch, setting):
    """R1-52 (5) (rows 34 and 35 of PART 2's table): masters and expression sheets are two offers, and `masters` makes at most `limit` portraits a call,
    so two masters offers can fall on ONE India day. With one key the later card returned the first and he never saw its buttons; the key says what
    is offered - the masters with the characters made."""
    from whatifs import sheets as SH
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    _r34(monkeypatch, setting); _r35(monkeypatch, setting)
    monkeypatch.setattr(SH, "masters_plan", lambda: [{"character": "GRIMM", "expression": "master", "prompt": "p", "hash": "hCA8g"}]); assert SH.masters()["made"] == 1
    rows = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "sheets_review"]; day = NT._india_day()
    assert [r["dedupe_key"] for r in rows] == [f"sheets|masters|VALE|{day}", f"sheets|expressions|{day}", f"sheets|masters|GRIMM|{day}"], [(r["dedupe_key"], r["buttons"]) for r in rows]
    assert [json.loads(r["buttons"]) for r in rows] == [[["Approve VALE", "APPROVE SHEET VALE"]], [["Approve SET", "APPROVE SHEET SET"]], [["Approve GRIMM", "APPROVE SHEET GRIMM"]]]

# ------------------------------------------------------------------ step 8a: NEVER HELD BY HIS ABSENCE (PART 7; R22 (2), (2 b), (2 c)) - the special is step 8b's
from whatifs import contract as CON, launch as LAU, publish as PUB8
from whatifs.org import floor as FL8

def _ep8(monkeypatch, setting, ep="EP8", hours=26.0, status="AWAITING_APPROVAL", **cols):
    """A long video waiting for his approval, its slot `hours` ahead; uploads open; every yt_schedule recorded."""
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); monkeypatch.setattr(LAU, "uploads_open", lambda: True)
    sched = []; monkeypatch.setattr(PUB8, "yt_schedule", lambda vid, at: sched.append((vid, at)) or True)
    slot = (core.now_utc() + dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:00Z")
    core.store().append("Episodes", [dict({"episode_id": ep, "status": status, "yt_id": "yt" + ep, "slot_et": slot, "title": "Title " + ep}, **cols)])
    return slot, sched

def _epi(ep): return next(e for e in core.store().rows("Episodes") if e["episode_id"] == ep)
def _kind(k, ep=None): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == k and (ep is None or r.get("episode_id") == ep)]
def _later(h): return core.now_utc() + dt.timedelta(hours=h)

def test_silence_is_asked_twelve_hours_before(monkeypatch, setting):
    """R22 (2), (2 b): his silence is taken SILENCE_LEAD_H (12) hours before the slot, never 1.5 - a tick can be 11 hours late (measured 19 Nov 2026).
    With the switch off `floor.eye_hours` keeps its literal (V1c's own test pins 20, 8.5, 1.0): the close of F1 of V1c's audit for the shipped state."""
    slot, _s = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "'Title EP8'.")
    r = _kind("creative_review")[0]; h = (core.parse_iso(r["expires_at"]) - core.parse_iso(r["created"])).total_seconds() / 3600
    assert abs(h - 14) < 0.05 and r["default_action"] == "approved by your silence" and "approved by your silence from" in r["text"] and "Take it down" in r["text"]
    assert abs(FL8.eye_hours(slot) - 14) < 0.05
    setting("SILENCE_LEAD_H", "3"); slot9, _s9 = _ep8(monkeypatch, setting, ep="EP9"); CON.await_approval("EP9", "ytEP9", slot9, "s")
    assert abs(FL8.eye_hours(slot9) - 20) < 0.05                                                     # the floor's card: its own cap (VIEW_FLOOR_EYE_WAIT_H 20)
    x = _kind("creative_review", "EP9")[0]
    assert abs((core.parse_iso(x["expires_at"]) - core.parse_iso(x["created"])).total_seconds() / 3600 - 23) < 0.05
    setting("TWO_SCREENS_ON", "FALSE"); s10 = (core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert abs(FL8.eye_hours(slot) - 20) < 0.05 and abs(FL8.eye_hours(s10) - 8.5) < 0.05             # R22 (2 b): F1's own clause - the literal stands with the switch off

def _decided(ep): return _kind("decided_post", ep)

@pytest.mark.parametrize("card", ["creative_review", "floor_eye"])
def test_a_tick_eleven_hours_late_keeps_the_slot(card, monkeypatch, setting):
    """R22 (2): the card expired and no tick came for 11 hours - the video is still SCHEDULED for its OWN slot (yt_schedule called with it), and one
    `decided_post` row says so with the Studio link and "Take it down" - for the review card and for the floor's card alike (one road, R17 (7 b))."""
    slot, sched = _ep8(monkeypatch, setting)
    if card == "creative_review": CON.await_approval("EP8", "ytEP8", slot, "s")
    else: CON.await_approval("EP8", "ytEP8", slot, "s", kind="floor_eye", default="goes public by itself", expires_h=FL8.eye_hours(slot))
    NT.expire_defaults(now=_later(14 + 11))
    assert _epi("EP8")["status"] == "SCHEDULED" and _epi("EP8")["slot_et"] == slot and sched == [("ytEP8", slot)]
    d = _decided("EP8"); assert len(d) == 1 and "approved by your silence and goes public at" in d[0]["text"] and "studio.youtube.com/video/ytEP8/edit" in d[0]["text"]
    assert json.loads(d[0]["buttons"]) == [["Take it down", "UNPOST EP8"]] and d[0]["expires_at"]

def test_a_moved_slot_is_told(monkeypatch, setting):
    """R22 (2): the first tick came 12 hours after the expiry, when its own slot had passed: SCHEDULED for the next free slot, and the row holds both slots."""
    slot, sched = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "s")
    late = _later(14 + 12); monkeypatch.setattr(CON, "now_utc", lambda: late)
    NT.expire_defaults(now=late)
    e = _epi("EP8"); assert e["status"] == "SCHEDULED" and e["slot_et"] != slot and sched == [("ytEP8", e["slot_et"])]
    t = _decided("EP8")[0]["text"]; assert "had passed" in t and CON._ist(slot) in t and CON._ist(e["slot_et"]) in t, t

def _ledger(ep, feature, status):
    core.store().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": ep, "stage": "final", "feature": feature, "status": status, "evidence": "planted", "promise": "p"}])

@pytest.mark.parametrize("case", ["ai_label", "floor_hold", "kids", "uploads_closed", "slop"])
def test_a_planted_failing_check_still_holds_after_the_expiry(case, monkeypatch, setting):
    """PART 7, A DEFAULT NEVER SKIPS A CHECK (the planted test of the brief): a failed final-gate row, an open floor hold, the made-for-kids cell, closed
    uploads, an open hold of the slop check - after the expiry the video is still AWAITING_APPROVAL, nothing was scheduled and the `silence|` row says why."""
    slot, sched = _ep8(monkeypatch, setting, kids_check=(core.iso() + " True") if case == "kids" else "")
    if case == "ai_label": _ledger("EP8", "ai_label", "FAIL")
    if case == "floor_hold": NT.send("floor_hold", "held by the floor", [("Publish anyway", "CONTRACT WAIVE EP8 viewer_floor")], episode="EP8", dedupe_key="floor|EP8|hold")
    if case == "slop": NT.send("contract_hold", "EP8 is HELD at the final check: slop_guard", [("Fix", "CONTRACT FIX EP8 final")], episode="EP8", dedupe_key="contract|EP8|final")
    if case == "uploads_closed": monkeypatch.setattr(LAU, "uploads_open", lambda: False)
    CON.await_approval("EP8", "ytEP8", slot, "s"); NT.expire_defaults(now=_later(25))
    assert _epi("EP8")["status"] == "AWAITING_APPROVAL" and sched == [] and not _decided("EP8")
    h = [r for r in _kind("contract_hold", "EP8") if r["dedupe_key"] == "silence|EP8"]
    assert len(h) == 1 and "was not approved by your silence" in h[0]["text"] and "It stays private." in h[0]["text"]
    assert [b[1] for b in json.loads(h[0]["buttons"])] == ["APPROVE EP8", "HOLDREVIEW EP8"] and not h[0]["expires_at"]

def test_a_clean_video_goes_public_on_its_slot_by_silence(monkeypatch, setting):
    """PART 7: a clean video he never answered is approved by his silence (the function his tap calls) and goes public on its own slot; a ledger with a
    PASS, a WAIVED and an older FAIL whose newest row passes is clean (the newest row a feature, as `run` judged it)."""
    slot, sched = _ep8(monkeypatch, setting)
    _ledger("EP8", "titles", "PASS"); _ledger("EP8", "aliveness", "WAIVED"); _ledger("EP8", "chapters", "FAIL"); _ledger("EP8", "chapters", "PASS")
    assert CON.clear_to_post("EP8") == (True, "every check passed")
    CON.await_approval("EP8", "ytEP8", slot, "s"); NT.expire_defaults(now=_later(15))
    assert _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)] and len(_decided("EP8")) == 1

def test_his_hold_tap_still_holds(monkeypatch, setting):
    """PART 7: his Hold before the expiry - the video stays HELD_BY_OWNER, no default runs on the answered card, the sweep never approves it."""
    slot, sched = _ep8(monkeypatch, setting)
    CON.await_approval("EP8", "ytEP8", slot, "s"); r = _kind("creative_review")[0]
    NT.answer(r["id"], "HOLDREVIEW EP8"); NT.expire_defaults(now=_later(25)); assert CON.review_sweep() == 0
    assert _epi("EP8")["status"] == "HELD_BY_OWNER" and sched == [] and not _decided("EP8")

def test_silence_tries_again_when_the_reason_is_gone(monkeypatch, setting):
    """R17 (7 a): uploads closed at the expiry and open two ticks later = scheduled at the next sweep, and the `silence|` row is closed "cleared" (one
    road); a failed ledger row = never, at any sweep."""
    slot, sched = _ep8(monkeypatch, setting); monkeypatch.setattr(LAU, "uploads_open", lambda: False)
    CON.await_approval("EP8", "ytEP8", slot, "s"); NT.expire_defaults(now=_later(15))
    assert _epi("EP8")["status"] == "AWAITING_APPROVAL" and CON.review_sweep() == 0
    monkeypatch.setattr(LAU, "uploads_open", lambda: True); assert CON.review_sweep() == 1
    assert _epi("EP8")["status"] == "SCHEDULED" and sched == [("ytEP8", slot)]
    h = [r for r in _kind("contract_hold", "EP8") if r["dedupe_key"] == "silence|EP8"][0]; assert h["status"] == "ANSWERED" and h["answer"] == "cleared"
    slot2, _s2 = _ep8(monkeypatch, setting, ep="EP9"); _ledger("EP9", "ai_label", "FAIL")
    CON.await_approval("EP9", "ytEP9", slot2, "s"); NT.expire_defaults(now=_later(15))
    for _ in range(3): CON.review_sweep()
    assert _epi("EP9")["status"] == "AWAITING_APPROVAL"

def test_the_floors_card_takes_the_same_road(monkeypatch, setting):
    """R17 (7 b): a `floor_eye` default goes through `approve_by_silence` - a film the floor could not judge also leaves a `decided_post` row with
    "Take it down"; and a held reason keeps it private (the floor's `eye_sweep` is its retry, as before)."""
    slot, sched = _ep8(monkeypatch, setting); _ledger("EP8", "ai_label", "FAIL")
    CON.await_approval("EP8", "ytEP8", slot, "s", kind="floor_eye", default="goes public by itself", expires_h=FL8.eye_hours(slot))
    NT.expire_defaults(now=_later(15)); assert _epi("EP8")["status"] == "AWAITING_APPROVAL" and FL8.eye_sweep() == 0
    core.store().update("Feature_Ledger", "episode_id", "EP8", {"status": "PASS"}); assert FL8.eye_sweep() == 1
    assert _epi("EP8")["status"] == "SCHEDULED" and [b[1] for b in json.loads(_decided("EP8")[0]["buttons"])] == ["UNPOST EP8"]

def test_undo_is_private_never_gone(monkeypatch, setting):
    """PART 7, UNDO NEVER DELETES (R17 ADDS (B)): his "Take it down" from the dashboard (verb UNPOST|<ep>) makes the video private and HELD_BY_OWNER
    through his Hold's own function; the function never deletes or uploads, and the video keeps its id. (Step 9a adds the stand-in's read-back.)"""
    import inspect
    tree = ast.parse(inspect.getsource(CON.unpost))
    assert not {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)} & {"yt_delete", "yt_upload"}
    slot, _s = _ep8(monkeypatch, setting, status="SCHEDULED"); priv = []; real = PUB8.yt_set_privacy
    monkeypatch.setattr(PUB8, "yt_set_privacy", lambda vid, p: priv.append((vid, p)) or True)
    ok, note = DS.route("UNPOST|EP8")
    assert ok and "is private again. Nothing was deleted." in note and priv == [("ytEP8", "private")]
    assert _epi("EP8")["status"] == "HELD_BY_OWNER" and _epi("EP8")["yt_id"] == "ytEP8"
    monkeypatch.setattr(PUB8, "yt_set_privacy", real)                       # step 9a (R18 (2)): the stand-in keeps the privacy now - its read-back is real
    vid = PUB8.yt_upload("x/EP10.mp4", "Title EP10", "d", [], now=core.now_utc())
    core.store().append("Episodes", [{"episode_id": "EP10", "status": "SCHEDULED", "yt_id": vid, "slot_et": slot, "title": "Title EP10"}])
    assert PUB8.yt_read(vid)["privacy"] == "public" and DS.route("UNPOST|EP10")[0]
    assert PUB8.yt_read(vid)["privacy"] == "private" and _epi("EP10")["yt_id"] == vid and _epi("EP10")["status"] == "HELD_BY_OWNER"
    setting("TWO_SCREENS_ON", "FALSE"); assert DS.route("UNPOST|EP8") == (False, "That action is not allowed.")

def _rehearse_to_line_56(monkeypatch, setting, tmp_path):
    """F-REH-2: the rehearsal's own opening (tools/rehearsal.py: setup, voices, the two opening ticks, the ladder skip) run in this test's store up to
    its line 56 (the first Premise_Bench row) - reaching it means line 55 held - with its two settings as the rehearsal runs them (the older tests
    run without both) and the digest's clock at 10:00 India time, planted as `test_a_pause_does_not_silence_him` plants it."""
    from tools import rehearsal as RH
    class Line56(Exception): pass
    real = core.LocalStore.append
    def append(self, tab, rows, *a, **k):
        if tab == "Premise_Bench" and rows and rows[0].get("bench_id") == "BREH0": raise Line56()
        return real(self, tab, rows, *a, **k)
    monkeypatch.setattr(core.LocalStore, "append", append); monkeypatch.setenv("WI_WORK", str(tmp_path / "rh"))
    setting("TWO_SCREENS_ON", "TRUE"); setting("LADDER_ON", "TRUE")
    D = dt.datetime(2026, 11, 20, 4, 30, tzinfo=dt.timezone.utc)                                         # Fri 20 Nov, 10:00 India time: the morning message is due
    monkeypatch.setattr(DG, "now_utc", lambda: D)
    return RH, Line56

def test_the_ladder_skip_lets_the_morning_message_pass(monkeypatch, setting, tmp_path):
    """F-REH-2 (R1-136; the code reader's CR-REH-3): after 09:00 IST the rehearsal's second opening tick pushes the morning message and bills it
    (item "whatsapp", episode "owner", role "morning") - the overhead of a clock push, not a video's money: the ladder skip (line 55) holds."""
    RH, Line56 = _rehearse_to_line_56(monkeypatch, setting, tmp_path)
    with pytest.raises(Line56): RH.run()
    assert [(r.get("item"), r.get("episode_id"), r.get("role")) for r in core.store().rows("Cost_Log")] == [("whatsapp", "owner", "morning")]

def test_the_ladder_skip_is_red_on_an_alarm_of_the_opening_ticks(monkeypatch, setting, tmp_path):
    """F-REH-2 (R1-136; the code reader's CR-REH-1): only the two clock pushes (role "morning" or "needs") pass the ladder skip. An alarm WhatsApp took
    in the opening ticks bills the same item and episode with role "alarm" - on a fresh install that is a false alarm to him: red at line 55."""
    RH, Line56 = _rehearse_to_line_56(monkeypatch, setting, tmp_path)
    real, told = DG.tick, []
    def tick(now=None):
        if not told: told.append(WA._bill({"type": "template"}, "alarm"))                                # the row an alarm's push writes (wa._bill: role = its kind)
        return real(now)
    monkeypatch.setattr(DG, "tick", tick)
    with pytest.raises(AssertionError) as e: RH.run()
    tb = e.value.__traceback__
    while tb.tb_next: tb = tb.tb_next
    assert told and tb.tb_frame.f_code.co_filename.endswith("rehearsal.py") and "a long video started without a promoted Short" in str(e.value) and "'alarm'" in str(e.value), str(e.value)[:600]


# ---------------- step 8b (PART 7, THE SPECIAL; R18 (7 c)): a special is posted by his silence only with its check on record
def _sp_card(monkeypatch, setting, checks):
    """A special made and waiting (tab Specials, `checks` as given) and its card, with the switch on."""
    from whatifs import specials as SP, launch as LA, publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    monkeypatch.setattr(PUB, "drive_upload", lambda path, name, public=False: ("f8b", "u8b")); monkeypatch.setattr(LA, "uploads_open", lambda: True)
    sid = "SP209911200900"
    core.store().append("Specials", [{"ts": core.iso(), "id": sid, "kind": "special", "title": "Grimm vs Monday", "status": "AWAITING_APPROVAL", "checks": checks}])
    SP.register(); SP._await_review("x.mp4", {"title": "Grimm vs Monday"}, "special", sid, [{"who": "GRIMM", "line": "Monday is on trial"}], checks=checks)
    return SP, sid, next(r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == sid)

def test_a_special_is_posted_by_silence_only_with_its_checks(monkeypatch, setting):
    from whatifs import launch as LA
    posted = []
    SP, sid, row = _sp_card(monkeypatch, setting, "pass")
    monkeypatch.setattr(SP, "approve", lambda s, replace=False: posted.append(s) or f"posted {s}")
    assert row["kind"] == "special_ready" and row["expires_at"] and "posted after 72 hours" in row["default_action"]
    assert NT.DEFAULTS["special_ready"] is SP._ready_silence
    core.store().update("Specials", "id", sid, {"checks": ""})
    assert "no check on record" in SP._ready_silence(row) and posted == []                     # planted: no check result on record - nothing is posted
    core.store().update("Specials", "id", sid, {"checks": "pass"})
    monkeypatch.setattr(LA, "uploads_open", lambda: False); assert "uploads" in SP._ready_silence(row) and posted == []
    monkeypatch.setattr(LA, "uploads_open", lambda: True); setting("PAUSED", "TRUE")
    assert "paused" in SP._ready_silence(row) and posted == []
    setting("PAUSED", "FALSE"); assert SP._ready_silence(row) == f"posted {sid}" and posted == [sid]

def test_a_special_without_a_check_waits_for_his_tap(monkeypatch, setting):
    import datetime as dt
    SP, sid, row = _sp_card(monkeypatch, setting, "")
    assert row["kind"] == "special_review" and not row["expires_at"] and "no check on record, so it waits for your tap" in row["default_action"]
    assert NT.klass("special_review") == NT.HOLD and any(r["id"] == row["id"] for r in NT.needs())
    NT.expire_defaults(now=core.now_utc() + dt.timedelta(days=30))                                # never posted by silence, never renewed
    assert next(r for r in core.store().rows("Owner_Actions") if r["id"] == row["id"])["status"] == "OPEN"
    assert not [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "special_ready"]

def test_the_turned_special_answers_his_approve(monkeypatch, setting):
    posted = []
    SP, sid, row = _sp_card(monkeypatch, setting, "pass")
    monkeypatch.setattr(SP, "approve", lambda s, replace=False: posted.append(s) or f"posted {s}")
    assert "posted" in NT.answer(row["id"], f"SPECIAL APPROVE {sid}") and posted == [sid]          # R17 (7 d): without the register line it records and does nothing

# ------------------------------------------------------------------ step 9b: THE SWEEP WALKS HIS TWO SCREENS (PART 9, R17 (11 c); the plan's 5.6) - on a planted clock
SCREENS_FAULTS = {"unknown_kind": "a message of a kind the register does not know: made_up_kind",
                  "refused": "1 WhatsApp message(s) refused outside the 24-hour window: reply",
                  "other_kind": "WhatsApp started a message of another kind: fyi",
                  "no_morning": "no morning message went out at the planted 09:05",
                  "no_needs": "no \"Needs you\" list went out at the planted 18:05 with a decision open"}

@pytest.mark.parametrize("fault", [None] + list(SCREENS_FAULTS))
def test_the_sweep_judges_his_two_screens_on_a_planted_clock(fault, monkeypatch, setting):
    """R17 (11 c), the plan's 5.6: `tools/sweep.py:screens_of` plants one open card and the clock - `digests.tick` at 09:05 and `digests.needs_tick` at
    18:05 India time of the next India day - so its counts never hang on the hour of the run. An id is BAD, each fault alone: a message of a kind the
    register does not know; a WhatsApp message refused at the wire outside the window; a WA_Outbox kind outside morning, needs, alarm, reply; no
    morning row (the morning message switched off); no "Needs you" row (its push dropped). Walked twice it sends nothing twice. The counter
    `owner_road_ok` counts a good id only; every mode of the sweep's `one()` judges it and the rehearsal asserts it last and prints its line."""
    import inspect
    from tools import sweep as SW, rehearsal as RH
    from whatifs import publish as PUB
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); monkeypatch.setattr(PUB, "email", lambda *a, **k: True); _window(False)
    if fault == "unknown_kind": NT.send("made_up_kind", "A message nobody registered.")
    if fault == "refused": WA.send_text("free text with the window closed")
    if fault == "other_kind": core.store().append("WA_Outbox", [{"ts": core.iso(), "wamid": "wamid.X9B", "action_id": "", "kind": "fyi", "status": "sent"}])
    if fault == "no_morning": setting("DIGEST_WA_ON", "FALSE")
    if fault == "no_needs":
        real = WA.push; monkeypatch.setattr(WA, "push", lambda kind, *a, **k: "" if kind == "needs" else real(kind, *a, **k))
    ok, words = SW.screens_of(core, ["EPS9B"])
    if fault:
        assert not ok and words == SCREENS_FAULTS[fault], words
        return
    assert ok and words == "the owner's road held: 1 rows, all registered; WhatsApp: 1 morning, 1 needs, 0 alarm", words
    out = core.store().rows("WA_Outbox"); card = core.store().rows("Owner_Actions")[0]
    assert sorted(r["kind"] for r in out) == ["morning", "needs"] and len(bodies) == 2 and all(b["type"] == "template" for b in bodies)      # outside the window: the one template
    assert card["kind"] == "bakeoff" and card["status"] == "OPEN" and card["episode_id"] == "EPS9B" and card["id"] in {r["id"] for r in NT.needs()}
    assert SW.screens_of(core, ["EPS9B"]) == (True, words) and len(bodies) == 2 and len(core.store().rows("Owner_Actions")) == 1      # walked twice: nothing sent twice
    s = SW.summary([{"id": "a", "outcome": "ok", "screens": words}, {"id": "b", "outcome": "odd", "screens": words}, {"id": "c", "outcome": "ok"}])
    assert s["owner_road_ok"] == 1 and s["bad_ids"] == ["b"]
    src = inspect.getsource(SW.one)
    assert src.count("ok_w, res[\"screens\"] = screens_of(core, [ep])") == 3 and src.count('if not ok_w: res["outcome"] = "odd"; res["problems"].append("his two screens: "') == 2
    assert 'if not ok_w: late.append("his two screens: "' in src                                    # the Short mode: a bad verdict makes the id bad
    r = inspect.getsource(RH.run)
    assert "okw9b, saidw9b = screens9b(core12, [epid]); assert okw9b" in r and 'print("owner road:"' in r and r.index("screens9b(core12") > r.index('print("v7.3 checks ok")')

# ------------------------------------------------------------------ step 10: R22 (12) - the two daily jobs at the first tick after their hour
def test_the_daily_jobs_run_once_at_the_first_tick_after_their_hour(monkeypatch, setting):
    """R22 (12): the key-expiry check (with the model switches whose date has come) and the occasion's heads-up run at the FIRST tick at or after 08:00
    and 09:00 UTC, once a UTC day - no longer only when a tick falls inside one half hour of the day (GitHub's own schedule left 7 to 11 hours between
    ticks). A day whose only ticks are at 03:10 and 14:40 UTC runs both once, at 14:40; a second tick that day runs neither; the next day runs them again."""
    from whatifs import manage as MG, caretaker as CT, steward as STWD, occasions as OC
    ran = []
    monkeypatch.setattr(CT, "ensure_expiry_seed", lambda *a, **k: None); monkeypatch.setattr(CT, "expiry_check", lambda *a, **k: ran.append("expiry"))
    monkeypatch.setattr(STWD, "apply_planned", lambda *a, **k: ran.append("switches")); monkeypatch.setattr(OC, "heads_up", lambda *a, **k: ran.append("heads_up"))
    def tick(h, m, day=16):
        t = dt.datetime(2026, 12, day, h, m, tzinfo=dt.timezone.utc); monkeypatch.setattr(MG, "now_utc", lambda: t); MG.tick(); return list(ran)
    assert tick(3, 10) == []
    assert tick(14, 40) == ["expiry", "switches", "heads_up"]
    assert tick(16, 20) == ["expiry", "switches", "heads_up"] and core.S("EXPIRY_CHECK_DAY") == "2026-12-16" and core.S("OCCASION_DAY") == "2026-12-16"
    assert tick(8, 5, day=17) == ["expiry", "switches", "heads_up", "expiry", "switches"]                        # 08:05: the check; the heads-up waits for 09:00
    assert tick(9, 0, day=17)[-1] == "heads_up" and len(ran) == 6

# ------------------------------------------------------------------ step 10b: R22 (6) - a sparse clock loses nothing
SPARSE_SHORT = "SHSPARSE10"          # a whole Short of this file (in OWN_IDS)

def test_the_sparse_clock_loses_nothing(monkeypatch, setting):
    """R22 (6): the REAL `manage.tick`, with every part in it, on the clock GitHub's own schedule gave (measured 19 Nov 2026: about four ticks a day) -
    three India days (Wed 16 to Fri 18 Dec 2026), ticks at 02:10, 09:40, 16:50 and 23:20 India time. Five cards so spread that one is open every
    evening, one Short that never reads HD (uploaded at 10:00 on day 1) and one reviewed video uploaded 27 hours before its slot (20:30 on day 3).
    WhatsApp starts ONE morning message (at the 09:40 tick) and ONE "Needs you" list (at the 23:20 tick, the first after 18:00) a day and nothing
    between 00:30 and 08:00; every card is DEFAULTED at the first tick after its expiry (the fifth, kept open for day 3's list, closes after the walk);
    the Short is public at the 16:50 tick (its cap); the video is SCHEDULED for its OWN slot - its silence was taken at the 09:40 tick of day 3
    (20:30 - SILENCE_LEAD_H 12 = 08:30). R24: the key-expiry check and the occasion's heads-up are no-ops here (this test counts whole lists)."""
    from whatifs import manage as MG, hdgate as HG, release as REL, shorts2 as SH, caretaker as CT, steward as STWD, occasions as OC
    UTC = dt.timezone.utc
    def ist(d, h, m): return dt.datetime(2026, 12, d, h, m, tzinfo=NT.IST).astimezone(UTC)
    clock = [ist(16, 0, 0)]                                                                                      # always UTC: core.iso never converts a zone
    for mod in (NT, DG, WA, MG, HG, CON, REL): monkeypatch.setattr(mod, "now_utc", lambda: clock[0])            # every module imports now_utc by name
    for mod, fn in ((CT, "ensure_expiry_seed"), (CT, "expiry_check"), (STWD, "apply_planned"), (OC, "heads_up")): monkeypatch.setattr(mod, fn, lambda *a, **k: None)
    setting("TWO_SCREENS_ON", "TRUE"); setting("HD_GATE_ON", "TRUE"); setting("SHORTS_REVIEW_FIRST_N", "0")
    bodies = _wire(monkeypatch); _mailbox(monkeypatch); _window(False)
    monkeypatch.setattr(LAU, "uploads_open", lambda: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    monkeypatch.setitem(PUB8.FAKE_FAULTS, "youtube", {"sd": True})                                              # nothing ever reads HD
    step, sched, real = [-1], [], PUB8.yt_schedule
    monkeypatch.setattr(PUB8, "yt_schedule", lambda vid, at: sched.append((vid, at, step[0])) or real(vid, at))
    cards = [NT.send("bakeoff", f"Decision {i}", [("Pick A", f"PICK S{i}")], default="A is used", expires_h=h, dedupe_key=f"sparse|{i}")
             for i, h in enumerate((12, 20, 29, 47.5, 72))]      # closing day 1 12:00 and 20:00, day 2 05:00 and 23:30, day 4 00:00 (India time)
    ticks = [ist(d, h, m) for d in (16, 17, 18) for h, m in ((2, 10), (9, 40), (16, 50), (23, 20))]
    out, seen, svid, vid, review, short_at_cap = [], {}, "", "", "", None
    slot = core.iso(ist(18, 20, 30))
    try:
        for k, t in enumerate(ticks):
            if k == 2:                                                                                           # 10:00 on day 1: the Short goes up, private
                clock[0] = ist(16, 10, 0)
                core.store().append("Premise_Bench", [{"bench_id": "B0", "premise": "What if the Moon left tonight?", "headline": "What if the Moon left tonight?",
                                                       "family": "", "ptype": "collective", "status": "READY", "claude_score": 9, "gemini_score": 9, "combined": 9, "added": core.iso()}])
                r = SH.run(force=True, now=clock[0], episode_id=SPARSE_SHORT); assert r["ok"], r
                svid = r["yt_id"]; assert HG.row(svid)["state"] == HG.WAITING
            if k == 7:                                                                                           # 17:30 on day 2: the reviewed video, 27 hours before its slot
                clock[0] = ist(17, 17, 30)
                vid = PUB8.yt_upload("x/EPSPARSE.mp4", "Title EPSPARSE", "D", [], publish_at=slot, now=clock[0])
                core.store().append("Episodes", [{"episode_id": "EPSPARSE", "slot_et": slot, "status": "UPLOADED", "yt_id": vid, "title": "Title EPSPARSE",
                                                  "uploaded_at": core.iso(clock[0])}])
                CON.await_approval("EPSPARSE", vid, slot, "'Title EPSPARSE'."); review = _kind("creative_review", "EPSPARSE")[0]["id"]
            clock[0] = t; step[0] = k; n0 = len(core.store().rows("WA_Outbox")); MG.tick()
            out += [(k, r["kind"]) for r in core.store().rows("WA_Outbox")[n0:]]
            for i in cards + ([review] if review else []):
                if i not in seen and _row(i)["status"] == "DEFAULTED": seen[i] = k
            if k == 2: short_at_cap = (HG.row(svid)["state"], HG.row(svid)["note"], PUB8.yt_read(svid).get("privacy"))
    finally: shutil.rmtree(os.path.join(core.WORK, SPARSE_SHORT), ignore_errors=True)                           # GitHub runs every test file in one process with one work folder
    assert out == [(1, "morning"), (3, "needs"), (5, "morning"), (7, "needs"), (9, "morning"), (11, "needs")], out      # nothing at 02:10, nothing at 16:50
    assert len(core.store().rows("WA_Outbox")) == 6 and len(bodies) == 6                                        # nothing else started a message
    assert [seen.get(i) for i in cards] == [2, 3, 5, 8, None] and _row(cards[4])["status"] == "OPEN"             # each at the first tick after its expiry
    assert short_at_cap == (HG.CAP, "public after 410 min; HD NO (the cap)", "public")                          # 10:00 -> the 16:50 tick: its cap
    assert seen.get(review) == 9 and sched[0] == (vid, slot, 9)                                                  # his silence at the 09:40 tick of day 3, on its OWN slot
    e = _epi("EPSPARSE"); assert e["status"] == "SCHEDULED" and e["slot_et"] == slot
    d = _decided("EPSPARSE"); assert len(d) == 1 and "approved by your silence and goes public at" in d[0]["text"] and "had passed" not in d[0]["text"]

# ------------------------------------------------------------------ FINISHED BY FABLE: the corrections of the finishing pass (steps 5 and 6)
def test_one_whatsapp_line_is_one_build_card(monkeypatch, setting):
    """PART 5: one input is one row. FOUND AT THE FINISH: a line the weigher reads as a change request got the desk's `idea` row AND, when the chat
    answered with a SPEC, a second `idea` row from `handle_inbound` - two cards that never expire for one line. The desk's row is the card; the chat's
    own card still comes for a line the desk made no card for."""
    _desk_on(setting); bodies = _wire(monkeypatch); _labels(monkeypatch, kind="change_request", department="none", raises_breakout=False)
    monkeypatch.setattr(WA, "chat", lambda text, deep=False: ("Good idea.", "show a countdown clock in cold opens, switch COLD_OPEN_CLOCK_ON", "tweak"))
    _inbound(monkeypatch, "wamid.B1", "add a countdown clock to cold opens")
    ideas = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "idea"]
    assert len(ideas) == 1 and ideas[0]["id"] == _desk_rows()[-1]["action"], ideas
    taps = [b for b in bodies if b.get("type") == "interactive" and b["interactive"]["type"] == "button"][-1]
    assert [x["reply"]["id"] for x in taps["interactive"]["action"]["buttons"]] == [f"ACT|{ideas[0]['id']}|0", f"ACT|{ideas[0]['id']}|1"], taps
    assert "(feature, on your Claude plan" in taps["interactive"]["body"]["text"]                          # the card's own kind, not the chat's
    _labels(monkeypatch, kind="other")
    _inbound(monkeypatch, "wamid.B2", "what about a clock in the corner of cold opens")
    assert len([r for r in core.store().rows("Owner_Actions") if r["kind"] == "idea"]) == 2                 # the chat's card, where the desk made none

def test_the_never_list_knows_a_phrase_never_a_word():
    """LAUNCH_MAX C6 through PART 5: the never list RECOGNISES what this channel never does. FOUND AT THE FINISH: three patterns caught a word alone
    ("pod", "bot") or any wish that held "delete ... video" or "copy ... video" - an ordinary wish was parked unweighed, with a reason that was untrue."""
    for wish in ("Put an escape pod in the next Short.", "The bot's voice is flat; make the robot funnier.", "Delete the long intro from every video.",
                 "Delete the video's intro, it drags.", "Copy the pacing of our best video for the next script."):
        assert DESK.never(wish) is None, (wish, DESK.never(wish))
    for ask in ("Join an engagement pod with other channels.", "Let's use view bots for the first hour.", "Buy some bots.", "Bots for views would help.",
                "Just delete all old videos.", "Delete that Short.", "Copy that channel's video", "Copy another channel's script."):
        assert DESK.never(ask) is not None, ask

def test_his_answer_holds_no_bookkeeping_and_one_full_stop(monkeypatch, setting):
    """PART 5 (item 145: his messages read as a person's). FOUND AT THE FINISH: the tick's own count of tries ("[tries 1]") reached the morning message
    and the dashboard, and four of `decide`'s answers ended with two full stops. The count stays on the tab; he reads the sentence."""
    _desk_on(setting)
    def fail(text): raise RuntimeError("the model did not answer")
    monkeypatch.setattr(DESK, "weigh", fail)
    DESK.take("More of the night sky in every Short, please.", "dashboard", ref="act-t")
    assert "[tries 1]" in _desk_rows()[-1]["how"]                                                         # the tab keeps the count: the next tick reads it
    told = DESK.lines(); page = DS.build_snapshot()["inputs"]
    assert len(told) == 1 and "[tries" not in told[0] and "is tried again at the next tick." in told[0], told
    assert page[0]["answer"].endswith("is tried again at the next tick.") and "[tries" not in page[0]["answer"], page
    _labels(monkeypatch, kind="video_idea", department="none", raises_breakout=False)
    _n, line = DESK.take("What if the Moon was a mirror?", "dashboard", ref="act-u")
    assert line.endswith("send it on WhatsApp as a brief.") and not line.endswith(".."), line
    assert all(".. " not in l and not l.endswith("..") for l in DESK.lines()), DESK.lines()

def test_the_desks_answer_never_wakes_him(monkeypatch, setting):
    """PART 5 with PART 4: the desk's answer at a tick is a REPLY inside his open window - and never in his quiet hours (the morning message carries
    it). FOUND AT THE FINISH: it went at any tick; and its sender was outside the scan's list. `reply_answer` has ONE caller, `desk._tick_two`."""
    _desk_on(setting); setting("QUIET_HOURS_IST", "00:30-08:00"); bodies = _wire(monkeypatch)
    night = dt.datetime(2026, 11, 20, 21, 10, tzinfo=dt.timezone.utc)                                     # 02:40 India time
    day = dt.datetime(2026, 11, 20, 6, 0, tzinfo=dt.timezone.utc)                                         # 11:30 India time
    _window(True, night); assert WA.reply_answer("Your input 1: PARKED - a topic.", night) == "" and bodies == []
    _window(True, day); assert WA.reply_answer("Your input 1: PARKED - a topic.", day) and bodies[-1]["type"] == "text"
    _window(False); assert WA.reply_answer("x", day) == "" and len(bodies) == 1
    assert _starts_outside_wa([("whatifs/x.py", "from whatifs import wa as WA\nWA.reply_answer('hi')\n")]) == ["whatifs/x.py:2: reply_answer"]
    assert _starts_outside_wa(list(_py_files())) == []

def test_the_workers_input_route_holds_its_rule():
    """PART 6: the Worker's rule for his typed words - signed in, 1 to 2,000 characters after trim, a card's id or none, forwarded only encrypted -
    proven by the node test of mission_control/test_worker.mjs. FOUND AT THE FINISH: only GitHub's Checks ran that file, so the break run could not
    see a break of worker.js. ONE node test by its name: another test of that file rewrites a tracked file and is not run here."""
    import re, subprocess
    if not shutil.which("node"): pytest.skip("node not installed")
    r = subprocess.run(["node", "--test", "--test-reporter=tap", "--test-name-pattern", r"input \(v12 B-OWNER\)", "mission_control/test_worker.mjs"],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    out = r.stdout + r.stderr
    assert r.returncode == 0 and re.search(r"(?m)^# pass 1$", out) and re.search(r"(?m)^# fail 0$", out), out[-800:]

def test_an_after_launch_note_says_what_it_asks_of_him(setting):
    """Item 199 (R1-55 (2)): a part that comes after the launch says on his dashboard that it needs nothing from him - where that is true; the
    treasury's note, which names his own recharge, says what holds until then."""
    setting("TWO_SCREENS_ON", "TRUE"); s = DS.build_snapshot()
    assert s["learning"]["department_line"]["note"] == "The department line comes with the first batch after the launch. It needs nothing from you."
    assert s["plan"]["department_line"]["note"] == s["learning"]["department_line"]["note"]
    assert s["learning"]["features"]["note"] == "The feature watch comes after the launch. It needs nothing from you."
    assert s["money"]["treasury"]["note"].endswith("Building it needs nothing from you; until then the top-up reminders reach you as they do today.")
    assert all("after the launch" not in n or "nothing from you" in n for n in DS.NOTES.values()), DS.NOTES

# ------------------------------------------------------------------ FINISHED BY FABLE: the corrections of the finishing pass (steps 0 to 4, PART A2 - the third finisher)
def test_a_video_held_by_the_final_qc_is_on_both_screens(monkeypatch, setting):
    """R1-89 (2) (the code reader's CR-2a-1; item 149): a video the final QC still fails is HELD with the gate's own card - Fix and Discuss, on both
    screens - and the e-mail is its copy. FOUND AT THE FINISH: the QC path sent the e-mail alone. 'Approve anyway' is not on it: the QC reads no waiver.
    RE-CUT (PART A3's CA3-1, R1-104): the hold comes first and the card has its own try - a card that raises never stops the hold."""
    from whatifs import episode as EP, manage as MG, contract as CON
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); ep = OWN_IDS[1]; real = CON.owner_card
    def card(*a, **k): real(*a, **k); raise RuntimeError("planted: the card's row was written, then its delivery raised")
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    held = {"ok": False, "problems": [{"code": "black_frames", "detail": "planted"}], "info": "planted"}
    monkeypatch.setattr(EP.QC, "full_check", lambda ctx: dict(held)); monkeypatch.setattr(EP.FIX, "auto_fix", lambda job, chk, cap, again: (chk, [], 0.0))
    monkeypatch.setattr(CON, "owner_card", card)                                                        # the card raises AFTER its row is written: the hold must stand
    try:
        r = EP.produce((core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), episode_id=ep); assert r.get("held"), r
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
    assert next(e for e in core.store().rows("Episodes") if e["episode_id"] == ep)["status"] == "HOLD_QC"           # the hold's own state never waits on the card
    cards = [r for r in NT.needs() if r["kind"] == "contract_hold" and r["episode_id"] == ep]
    assert len(cards) == 1 and cards[0]["dedupe_key"] == f"contract|{ep}|quality" and "black_frames" in cards[0]["text"], cards
    assert [v for _l, v in json.loads(cards[0]["buttons"])] == [f"CONTRACT FIX {ep} quality", f"DISCUSS contract {ep}"]
    assert "Approve anyway" not in [l for l, _v in json.loads(cards[0]["buttons"])]                       # R1-102: no waiver tap on a quality hold

def test_a_waive_typed_by_hand_on_a_quality_hold_waives_nothing(monkeypatch, setting):
    """R1-102: the final QC reads no waiver. A 'CONTRACT WAIVE' typed by hand on its card wrote one, started the paid fix run and answered
    'it continues'. It waives nothing, starts nothing, and names Fix; the card is open again."""
    from whatifs import contract as CON
    setting("TWO_SCREENS_ON", "TRUE"); started = []
    monkeypatch.setattr(CON, "_open_fix_issue", lambda ep: started.append(ep) or True)
    CON.owner_card("EPQW1", "quality", [("black_frames", "planted")], "Nothing was uploaded.")
    c = next(r for r in NT.open_rows() if r["kind"] == "contract_hold" and r["episode_id"] == "EPQW1")
    out = NT.answer(c["id"], "CONTRACT WAIVE EPQW1 black_frames")
    assert "has no waiver" in out and "Fix" in out and started == [] and "EPQW1" not in json.loads(core.S("CONTRACT_WAIVERS") or "{}"), out
    assert _row(c["id"])["status"] == "OPEN"

def test_the_scheduled_message_never_skips_the_review_gate(monkeypatch, setting):
    """R1-90 (1) (the code reader's CR-2a-2): the `scheduled` message stood before the try that holds the review gate - a raise in it (with the switch
    on it also writes a row) let a video uploaded with its slot go public without his approval. It has its own try: the gate is always asked."""
    from whatifs import episode as EP, manage as MG, contract as CON
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); ep = OWN_IDS[2]; asked = []; real = NT.mail
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    def mail(kind, *a, **k):
        if kind == "scheduled": raise RuntimeError("planted: the row's write failed")
        return real(kind, *a, **k)
    monkeypatch.setattr(NT, "mail", mail); monkeypatch.setattr(CON, "review_needed", lambda kind="long": True)
    monkeypatch.setattr(CON, "await_approval", lambda e, vid, slot, summary, **k: asked.append(e))
    try:
        r = EP.produce((core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), episode_id=ep); assert r.get("ok"), r
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
    assert asked == [ep]

def test_two_different_messages_of_one_kind_on_one_day_both_stand(monkeypatch, setting):
    """R1-99 (2) (the code reader's CR-2b-1, its rest): `mode_ack`, `pick_ack` and `repair_waiting` fell on the inform rule's dated key - a second,
    DIFFERENT message of one India day returned the first row, so after Runway his screens said 'Budget mode: Standard'. The key names the thing
    (`NT.said_key`): the same words as that thing's newest row are one row; other words are a new row, the newest. A, B, A on one day = three rows."""
    from whatifs import preview as PV, packaging as PK
    import tools.repair as RP
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    of = lambda k: sorted((r for r in core.store().rows("Owner_Actions") if r["kind"] == k), key=lambda r: r["id"])
    for m in ("MODE RUNWAY", "MODE STANDARD", "MODE RUNWAY", "MODE RUNWAY"): PV.decide(m)
    assert [r["text"].split(".")[0] for r in of("mode_ack")] == ["Budget mode: Runway", "Budget mode: Standard", "Budget mode: Runway"], [r["text"][:40] for r in of("mode_ack")]
    assert all(r["status"] == "OPEN" for r in of("mode_ack"))
    for t in ("applied: B", "applied: C", "applied: C"): PK._pick_reply("EP209911261100", t)
    assert [r["text"].split(". ")[0] for r in of("pick_ack")] == ["Your pick for EP209911261100: applied: B", "Your pick for EP209911261100: applied: C"]
    RP._tell_owner("whatifs/premise.py", "this file guards money, quality or publishing"); RP._tell_owner("whatifs/preview.py", "this file guards money, quality or publishing")
    assert ["premise.py" in of("repair_waiting")[0]["text"], "preview.py" in of("repair_waiting")[1]["text"]] == [True, True]
    setting("TWO_SCREENS_ON", "FALSE"); assert NT.said_key("mode_ack", "budget", "RUNWAY") is None

def test_two_previews_that_reach_nothing_are_two_rows(monkeypatch, setting):
    """R1-99 (2)'s search: `preview_none` fell on the dated key - his second Script Preview of a day that reached nothing kept the first run's reason
    on both screens. Each run is its own row: the key names the run's draft."""
    from whatifs import preview as PV, premise as PR, ladder as LAD
    from whatifs.org import runner as ORG
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch)
    for k in ("name", "episode"): monkeypatch.setitem(core.JOB, k, core.JOB.get(k))      # run() names the job: put it back after the test
    monkeypatch.setattr(LAD, "gate", lambda *a, **k: (True, "", None))
    for i, why in enumerate(("planted: no pitch reached the bar", "planted: every pitch scored under the bar")):
        def skip(*a, _w=why, **k): raise PR.SkipSlot(_w)
        monkeypatch.setattr(ORG, "work", skip); monkeypatch.setattr(PV, "now_utc", lambda _i=i: core.now_utc() + dt.timedelta(minutes=_i))
        assert PV.run()["ok"] is False
    rows = sorted((r for r in core.store().rows("Owner_Actions") if r["kind"] == "preview_none"), key=lambda r: r["id"])
    assert len(rows) == 2 and "every pitch scored under the bar" in rows[1]["text"] and all(r["dedupe_key"].startswith("preview_none|DRAFT") for r in rows), [(r["dedupe_key"], r["text"][:70]) for r in rows]

def test_a_second_brief_on_one_day_is_its_own_row(monkeypatch, setting):
    """B4 (ii) (the Fable consult on CA2-3; R1-104): `monthly_brief` has no guard of its own - a run by hand on the cron's day (a brief corrected after a
    fix) wrote other words that the dated key swallowed, and his screens kept the first brief. Its key names its words (`NT.said_key`): the same brief
    twice is one row; another brief is a new row, the newest."""
    from whatifs import manage as MG, models as M
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); monkeypatch.setitem(core.JOB, "name", core.JOB.get("name"))      # the brief names the job: put it back after the test
    for words in ("The month in one page: before the fix.", "The month in one page: after the fix.", "The month in one page: after the fix."):
        monkeypatch.setattr(M, "ask_batch", lambda *a, _w=words, **k: _w); MG.monthly_brief()
    rows = sorted((r for r in core.store().rows("Owner_Actions") if r["kind"] == "monthly_brief"), key=lambda r: r["id"])
    assert len(rows) == 2 and "before the fix" in rows[0]["text"] and "after the fix" in rows[-1]["text"], [r["text"][:60] for r in rows]

def test_a_scored_master_is_a_draft_he_can_lock(monkeypatch, setting):
    """R1-99 (4) (the code reader's CR-2b-3; it reaches him): a master the judge scored is 'DRAFT (identity 8/10)' - his 'Approve VALE' locked nothing,
    the default lock never ran and the dashboard never offered it. A status that begins 'DRAFT' is a draft everywhere it is read."""
    from whatifs import sheets as SH, dash as DS
    setting("SHEETS_DEFAULT_LOCK_H", "72"); st = core.store()      # the switch as conftest leaves it: the portraits cards are the dashboard's own, in both states
    old = (core.now_utc() - dt.timedelta(hours=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st.append("Character_Sheets", [{"ts": core.iso(), "character": "VALE", "expression": "master", "hash": "hA4v", "prompt": "p", "file": "drive:v", "status": "DRAFT (identity 8/10)", "approved_at": ""},
                                   {"ts": old, "character": "GRIMM", "expression": "master", "hash": "hA4g", "prompt": "p", "file": "drive:g", "status": "DRAFT (identity 7/10)", "approved_at": ""},
                                   {"ts": core.iso(), "character": "ROSA", "expression": "master", "hash": "hA4r", "prompt": "p", "file": "drive:r", "status": "DRAFT (identity 9/10)", "approved_at": ""}])
    assert {"sheets-VALE", "sheets-GRIMM", "sheets-ROSA"} <= {c["id"] for c in DS._docket()}
    assert SH.decide("APPROVE SHEET VALE") == "1 image(s) locked" and SH.auto_lock() == 1 and DS.route("LOCKSHEETS|ROSA")[0]
    assert {r["hash"]: r["status"] for r in st.rows("Character_Sheets")} == {"hA4v": "LOCKED", "hA4g": "LOCKED", "hA4r": "LOCKED"}

def test_the_masters_card_says_each_identity_score(monkeypatch, setting):
    """B3, ruled (C) by R1-104 (the Fable consult on CA2-4): silence locks a scored master (the memo's row 34), so the masters' card says each identity
    score against his approved portrait - a face that moved is seen before it locks. Nothing scored, no sentence."""
    from whatifs import sheets as SH, specials as SP
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); _sheet_stubs(monkeypatch)
    monkeypatch.setattr(SP, "_portrait", lambda *a, **k: "his-portrait.png")                           # a portrait to compare with: the judge scores
    monkeypatch.setattr(SH, "identity_score", lambda ref, new, who: {"VALE": 8.0, "GRIMM": 3.0}[who])
    monkeypatch.setattr(SH, "masters_plan", lambda: [{"character": c, "expression": "master", "prompt": "p", "hash": f"hCA35{c}"} for c in ("VALE", "GRIMM")])
    assert SH.masters()["made"] == 2
    card = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "sheets_review")
    assert "Identity against your portrait: VALE 8/10, GRIMM 3/10. A low score means the face moved - look before it locks." in card["text"], card["text"]
    monkeypatch.setattr(SP, "_portrait", lambda *a, **k: None)                                         # no portrait: no score, no sentence
    monkeypatch.setattr(SH, "masters_plan", lambda: [{"character": "ROSA", "expression": "master", "prompt": "p", "hash": "hCA35R"}])
    assert SH.masters()["made"] == 1
    rosa = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "sheets_review" and "ROSA" in r["buttons"])
    assert "Identity against" not in rosa["text"], rosa["text"]

def test_a_repair_that_waits_for_him_is_one_tap_away(monkeypatch, setting):
    """R1-99 (4) (the code reader's CR-2b-5; item 149): a repair waiting for his Merge told him to open GitHub's Pull requests tab, with no address on
    either screen. The row holds the change's own page - one tap - as CA-7 keeps a link he must open. RE-CUT (PART A3's CA3-2): a second change of the
    same file for the same reason on one day is its own row, with its own address."""
    import tools.repair as RP
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); why = "this file guards money, quality or publishing"
    rows = lambda: sorted((r for r in core.store().rows("Owner_Actions") if r["kind"] == "repair_waiting"), key=lambda r: r["id"])
    RP._tell_owner("whatifs/premise.py", why, "https://github.com/me/re/pull/7")
    assert "Open the change: https://github.com/me/re/pull/7" in rows()[0]["text"], rows()[0]["text"]
    RP._tell_owner("whatifs/preview.py", why)                                                            # no address known: today's words
    assert "Pull requests tab" in rows()[-1]["text"]
    RP._tell_owner("whatifs/premise.py", why, "https://github.com/me/re/pull/8")                        # a second change of the same file, the same day, the same reason
    assert len(rows()) == 3 and "Open the change: https://github.com/me/re/pull/8" in rows()[-1]["text"], [r["text"][-60:] for r in rows()]

def test_a_pick_on_the_dashboard_closes_its_card(monkeypatch, setting):
    """R1-99 (4) (the code reader's CR-2b-7; item 149: both screens show the same): a pick made on the dashboard's own card left the `title_pick` row
    open - WhatsApp still offered "Keep A" (a tap there switched his pick back) and at the deadline it read "ran by default: A goes out"."""
    from whatifs import packaging as PK, dash as DS
    setting("TWO_SCREENS_ON", "TRUE"); _mailbox(monkeypatch); ep = "EP209911261200"
    core.store().append("Episodes", [{"episode_id": ep, "slot_et": (core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "SCHEDULED", "notes": ""}])
    PK.record(ep, "vidPICK1", [{"key": k, "title": f"Title {k}", "thumb_text": f"Thumb {k}"} for k in "ABC"], {})
    card = next(r for r in NT.open_rows() if r["kind"] == "title_pick" and r["episode_id"] == ep)
    assert DS.route(f"PICK|{ep}|B")[0]
    assert _row(card["id"])["status"] == "ANSWERED" and _row(card["id"])["answer"] == f"PICK {ep} B" and not any(r["kind"] == "title_pick" for r in NT.needs())
