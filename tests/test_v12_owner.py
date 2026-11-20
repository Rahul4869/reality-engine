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
