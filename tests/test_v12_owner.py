"""v12 B-OWNER - the owner's two screens: one register of every message to him, one road for every mail, alarms that can never be muted, WhatsApp
that starts three kinds of message only, his input desk, both screens showing the same, never held by his absence, the money of his messages.
Every rule is proven both ways; the real code path is run, so an unwired call is seen. The HD gate has its own file (tests/test_v12_hdgate.py)."""
import ast, datetime as dt, json, os
import yaml
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
