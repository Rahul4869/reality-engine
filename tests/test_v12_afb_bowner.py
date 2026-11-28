"""AFB - the three OPEN findings of the B-OWNER audit (NOTES/AUDIT_B-OWNER.md, chapter 14, 26 Nov 2026), each a failing test, then the fix:
F1 his window card (`prepublic`, "Tonight HH:MM ... before it goes public") is sent only to a long video that is SCHEDULED - never to one still
awaiting his approval or one his silence was refused for; F2 at the FINAL gate the hold (HOLD_QC) is written before its card, so a `hold_sweep`
of another job's tick in the gap never closes it (CA3-1's order, items 149 and 150); F3 the pre-flight names the silent hold of TWO_SCREENS_ON
FALSE in one failed row that never blocks (item 223). No randomness. Every time an assertion reads is planted: an hour passed in, or `_clock`,
which fixes now_utc in core, notify and the modules a test calls. One test runs on the real clock: F2's whole production - `episode.produce`
reads now_utc in every module it runs through, so its slot is 10 hours after the real now (a fixed date would turn into a past slot the day the
real clock passes it), and none of its assertions reads a time."""
import datetime as dt, os, shutil
import pytest
from whatifs import core, notify as NT, publish as PUB, hdgate as HG

UTC = dt.timezone.utc
M = dt.timedelta(minutes=1)
SLOT = dt.datetime(2026, 12, 16, 14, 30, tzinfo=UTC)       # 20:00 India time, a Wednesday
AFB_ID = "EP209911271015"                                   # this file's one whole production: an id no other test file uses

@pytest.fixture(autouse=True)
def _no_faults():
    PUB.FAKE_FAULTS.clear(); yield; PUB.FAKE_FAULTS.clear()

def _t(h, m): return dt.datetime(2026, 12, 16, h, m, tzinfo=UTC)
def _rows(kind): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == kind]

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _clock(monkeypatch, *mods, t=SLOT - 30 * 60 * M):
    """Plan 12 (b): one fixed now for core (its iso()), notify (a card's id and expiry) and the modules the test calls - 30 hours before SLOT."""
    for m in (core, NT, PUB) + mods: monkeypatch.setattr(m, "now_utc", lambda: t)

def _long(ep, status):
    """A long video as the pipeline leaves it: uploaded PRIVATE with its time, its Episodes row on its slot (tests/test_v12_hdgate.py's `_long`)."""
    vid = PUB.yt_upload(f"x/{ep}.mp4", f"Title {ep}", "D", [], publish_at=core.iso(SLOT), now=SLOT - 30 * 60 * M)
    core.store().append("Episodes", [{"episode_id": ep, "slot_et": core.iso(SLOT), "status": status, "yt_id": vid, "title": f"Title {ep}",
                                      "uploaded_at": core.iso(SLOT - 30 * 60 * M)}])
    return vid

# ------------------------------------------------------------------ F1: hdgate.window - no "before it goes public" to a video that is not SCHEDULED
def test_f1_his_window_card_waits_until_the_video_is_scheduled(monkeypatch, setting):
    """F1: a long video still AWAITING_APPROVAL is ready in HD on its day: no `prepublic` card - it goes public only when he or his silence
    approves it (PART 7). The first tick after it turns SCHEDULED sends its ONE card; a later tick sends no second one (`_told`)."""
    setting("TWO_SCREENS_ON", "TRUE"); _quiet(monkeypatch)
    vid = _long("EPAF1", "AWAITING_APPROVAL")
    HG.tick(_t(2, 0)); assert not _rows("prepublic"), _rows("prepublic")                                   # 07:30 India time: ready, not approved
    HG.tick(_t(3, 5)); assert not _rows("prepublic") and not _rows("hd_late")                              # 08:35: still nothing - and no `hd_late` (it is in HD)
    core.store().update("Episodes", "episode_id", "EPAF1", {"status": "SCHEDULED"})                       # his Approve, or his silence (`clear_to_post`)
    HG.tick(_t(3, 30)); c = _rows("prepublic")
    assert len(c) == 1 and c[0]["episode_id"] == "EPAF1" and c[0]["text"].startswith("Tonight 20:00: Title EPAF1. Optional before it goes public"), c
    assert vid in c[0]["text"]
    HG.tick(_t(4, 0)); assert len(_rows("prepublic")) == 1

def test_f1_a_video_his_silence_was_refused_for_gets_no_window_card(monkeypatch, setting):
    """F1: a long video whose final check FAILED (its `silence|` card says "It stays private") is never told it goes public tonight."""
    setting("TWO_SCREENS_ON", "TRUE"); _quiet(monkeypatch)
    _long("EPAF2", "AWAITING_APPROVAL")
    core.store().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": "EPAF2", "stage": "final", "feature": "aliveness", "status": "FAIL",
                                            "evidence": "planted", "promise": "p"}])
    HG.tick(_t(2, 0)); HG.tick(_t(4, 0)); assert not _rows("prepublic"), _rows("prepublic")

# ------------------------------------------------------------------ F2: episode.py's final gate - the hold first, then its card
def test_f2_the_final_gate_writes_the_hold_before_its_card():
    """F2, the order read in the code (a short run; the whole production below proves it end to end and runs for minutes): in `_finish` the
    final gate's `_hold(...)` - HOLD_QC - comes before `CON.owner_card(ep, "final", ...)`, and the line after the card returns the hold's result."""
    import inspect
    from whatifs import episode as EP
    src = inspect.getsource(EP._finish)
    hold = src.find('_hold(st, ep, out, {"problems": [{"code": "contract:" + f, "detail": str(ev)} for f, ev in g["failed"]]}, notes, fix)')
    card = src.find('CON.owner_card(ep, "final", g["failed"], "Nothing was uploaded.")')
    assert 0 < hold < card, (hold, card)
    assert src[card:].split("\n")[1].strip() == "return held", src[card:].split("\n")[1]

def test_f2_a_tick_in_the_gap_never_closes_the_final_gates_card(monkeypatch, setting):
    """F2 (items 149, 150): a production whose final gate fails. A tick of another job runs `contract.hold_sweep` while `_hold` saves the
    re-render bundle (`checkpoint.save`). The hold is written first, so the sweep closes nothing: afterwards the episode is HOLD_QC AND its card
    `contract|<ep>|final` stands OPEN under "Needs you". Before the fix the card went first and the sweep closed it "cleared" (its video read VISUALS)."""
    from whatifs import episode as EP, manage as MG, contract as CON
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    setting("TWO_SCREENS_ON", "TRUE"); monkeypatch.setattr(PUB, "email", lambda *a, **k: True); ep = AFB_ID
    real_run, real_save, swept = CON.run, EP.CK.save, []
    def run(stage, ctx, ep_, write=True):
        r = real_run(stage, ctx, ep_, write=write)
        return dict(r, ok=False, failed=[("aliveness", "planted: the final gate fails")]) if stage == "final" and write else r
    def save(out, ep_, stage, *a, **k):
        if stage == "hold": swept.append(CON.hold_sweep())                                                  # the tick of another job, in the gap
        return real_save(out, ep_, stage, *a, **k)
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP.QC, "full_check", lambda ctx: {"ok": True, "problems": [], "info": "planted: the final QC passes"})   # the QC is not this test's subject
    monkeypatch.setattr(CON, "run", run); monkeypatch.setattr(EP.CK, "save", save)
    try:
        r = EP.produce((core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), episode_id=ep); assert r.get("held"), r
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
    assert next(e for e in core.store().rows("Episodes") if e["episode_id"] == ep)["status"] == "HOLD_QC"
    cards = [r for r in NT.needs() if r["kind"] == "contract_hold" and r["episode_id"] == ep]
    assert [c["dedupe_key"] for c in cards] == [f"contract|{ep}|final"] and "aliveness" in cards[0]["text"], (cards, swept)
    assert swept == [0], swept                                                                              # the sweep ran in the gap and closed nothing

# ------------------------------------------------------------------ F3: the pre-flight names the silent hold of TWO_SCREENS_ON FALSE
def test_f3_the_preflight_names_the_silent_hold_with_two_screens_off(setting):
    """F3 (item 223): with TWO_SCREENS_ON FALSE a review card he does not answer ends "stays private" and nothing asks his silence again - a
    checked video held only because he did not answer. The pre-flight says so in ONE failed row that never blocks; with the cell TRUE no such row."""
    from whatifs import preflight as PF
    setting("TWO_SCREENS_ON", "FALSE"); rows = [x for x in PF.run() if x[0] == "two screens"]
    assert len(rows) == 1 and rows[0][1] is False and rows[0][3] is False, rows
    assert "a video you do not answer stays private for good" in rows[0][2], rows
    assert "two screens" not in PF.check()[1]                                                               # a warning: never a reason to stop
    setting("TWO_SCREENS_ON", "TRUE"); assert not [x for x in PF.run() if x[0] == "two screens"]


def test_u1_a_two_screens_cell_that_cannot_be_read_is_named_two_screens_never_whatsapp(monkeypatch):
    """U1 (AFB finding 2): TWO_SCREENS_ON is read OUTSIDE the WhatsApp check - an error reading it is ONE "two screens" warning that never blocks,
    never a "whatsapp: <error>" row that hides which cell failed."""
    from whatifs import preflight as PF
    real = core.S
    def S(k, *a, **kw):
        if k == "TWO_SCREENS_ON": raise RuntimeError("the Settings tab is not readable")
        return real(k, *a, **kw)
    monkeypatch.setattr(core, "S", S)
    rows = PF.run(); two = [x for x in rows if x[0] == "two screens"]
    assert len(two) == 1 and two[0][1] is False and two[0][3] is False and two[0][2].startswith("TWO_SCREENS_ON is not readable"), rows
    assert not [x for x in rows if x[0] == "whatsapp"], rows                                                # no WhatsApp row on a cell no one could read
    assert "two screens" not in PF.check()[1]                                                               # a warning: never a reason to stop


# ------------------------------------------------------------------ U1d (RUL-U1d 2, AFB-1): the review card of the video his silence would hold says so
def test_u1d_the_review_card_names_the_silent_hold_with_two_screens_off(monkeypatch, setting):
    """RUL-U1d 2: with TWO_SCREENS_ON FALSE a review card he does not answer ends "stays private" and nothing asks again - the card of THAT video
    says so in one sentence after the Studio link (cut never), once a video; never when YouTube kept it on its schedule (it can go public on its
    slot), never on a card whose caller passed its own default and hours (floor_eye), never with the switch on."""
    from whatifs import contract as CON, dash as DSH
    setting("TWO_SCREENS_ON", "FALSE"); _quiet(monkeypatch); _clock(monkeypatch, CON, DSH)                 # CR-AUDITFIX 4: steps 1-4 on the planted clock too
    slot_iso, held = core.iso(SLOT), "it stays private for good"
    review = lambda ep: [r for r in core.store().rows("Owner_Actions") if r.get("dedupe_key") == f"review|{ep}"]
    vid = _long("EPAF5", "UPLOADED"); CON.await_approval("EPAF5", vid, slot_iso, "s")                    # 1. the switch off, an uploaded long video
    r = review("EPAF5"); assert len(r) == 1 and r[0]["status"] == "OPEN" and r[0]["tier"] == "now" and r[0]["default_action"] == "stays private", r
    assert held in r[0]["text"] and "TWO_SCREENS_ON" in r[0]["text"], r[0]["text"]
    assert r[0]["id"] in {c["id"] for c in DSH._docket()}                                                  # on the dashboard's docket - the screen he reads (item 149)
    CON.await_approval("EPAF5", vid, slot_iso, "s"); assert len(review("EPAF5")) == 1                      # once a video: no second card
    vid = _long("EPAF5L", "UPLOADED"); CON.await_approval("EPAF5L", vid, slot_iso, "x" * 3000)            # 2. a long self-review: cut, never the sentence
    t = review("EPAF5L")[0]["text"]; assert len(t) <= 1500 and held in t and "TWO_SCREENS_ON" in t, (len(t), t[-300:])
    kept = _long("EPAF5Y", "UPLOADED"); real = PUB.yt_set_privacy                                            # 3. YouTube kept THIS video on its schedule
    monkeypatch.setattr(PUB, "yt_set_privacy", lambda v, *a, **k: False if v == kept else real(v, *a, **k))
    CON.await_approval("EPAF5Y", kept, slot_iso, "s"); t = review("EPAF5Y")[0]["text"]
    assert "STILL ON YOUTUBE SCHEDULE" in t and held not in t, t                                             # it can go public on its slot: never "for good"
    vid = _long("EPAF5F", "UPLOADED")                                                                        # 4. the caller's own default and hours
    CON.await_approval("EPAF5F", vid, slot_iso, "s", kind="floor_eye", default="goes public by itself", expires_h=20)
    t = review("EPAF5F")[0]["text"]; assert "Watch it (private)" in t and held not in t, t
    setting("TWO_SCREENS_ON", "TRUE"); monkeypatch.setattr(CON, "now_utc", lambda: SLOT - 30 * 60 * M)    # 5. the switch on, the slot 30 hours ahead
    vid = _long("EPAF5T", "UPLOADED"); CON.await_approval("EPAF5T", vid, slot_iso, "s"); t = review("EPAF5T")[0]["text"]
    assert "approved by your silence" in t and held not in t, t


# ------------------------------------------------------------------ U1d (RUL-U1d 3, AFB-3): YouTube kept it on its schedule - the alarm, no window card
def test_u1d_a_video_youtube_kept_on_its_schedule_gets_the_alarm_and_no_window_card(monkeypatch, setting):
    """RUL-U1d 3: a video await_approval could not make private stays AWAITING_APPROVAL with ONLY its urgent `unscheduled|` alarm ("Set it to
    Private") - never a "before it goes public" card beside the alarm that asks him to stop it. Its ONE `prepublic` card comes at the first tick
    after it turns SCHEDULED (his Approve, or his silence) - F1's rule, unchanged."""
    from whatifs import contract as CON
    setting("TWO_SCREENS_ON", "TRUE"); _quiet(monkeypatch); monkeypatch.setattr(CON, "now_utc", lambda: _t(1, 0))
    vid = _long("EPAF6", "UPLOADED"); monkeypatch.setattr(PUB, "yt_set_privacy", lambda *a, **k: False)    # YouTube refuses the change to private
    CON.await_approval("EPAF6", vid, core.iso(SLOT), "s")
    assert next(e for e in core.store().rows("Episodes") if e["episode_id"] == "EPAF6")["status"] == "AWAITING_APPROVAL"
    al = [r for r in core.store().rows("Owner_Actions") if r.get("dedupe_key") == "unscheduled|EPAF6"]
    assert len(al) == 1 and al[0]["status"] == "OPEN" and "Set it to Private" in al[0]["text"], al
    HG.tick(_t(2, 0)); HG.tick(_t(4, 0)); assert not _rows("prepublic"), _rows("prepublic")              # awaiting him: the alarm alone
    core.store().update("Episodes", "episode_id", "EPAF6", {"status": "SCHEDULED"})                       # his Approve, or his silence
    HG.tick(_t(4, 30)); c = _rows("prepublic"); assert len(c) == 1 and c[0]["episode_id"] == "EPAF6", c  # the stand-in still reads it private and ready
    HG.tick(_t(5, 0)); assert len(_rows("prepublic")) == 1


# ------------------------------------------------------------------ U1f (RUL-U1f 3, AFB-1 for specials): the special's card names the silent hold
def test_u1f_the_special_card_names_the_silent_hold_with_two_screens_off(monkeypatch, setting):
    """RUL-U1f 3: with TWO_SCREENS_ON FALSE a special's `special_review` card closes "not posted" after 72 hours and nothing sends it again - the
    card says so in one sentence right after its head, BEFORE the Watch link and the script (the script's 600 characters are what a cut meets
    first), once a special; with the switch on both cards keep today's words."""
    from whatifs import specials as SP
    _clock(monkeypatch, SP); _quiet(monkeypatch)
    monkeypatch.setattr(PUB, "drive_upload", lambda path, name, public=False: ("FID" + name.split(".")[0], None))     # the upload answered offline
    sp = lambda ep: [r for r in core.store().rows("Owner_Actions") if r.get("episode_id") == ep]
    beats, held = [{"who": "GRIMM", "line": "What if the Moon stopped?"}], "it stays unposted for good"
    setting("TWO_SCREENS_ON", "FALSE")
    SP._await_review("x/SPAF1.mp4", {"title": "T"}, "special", "SPAF1", beats, checks="pass")                    # 1. the switch off
    r = sp("SPAF1"); assert len(r) == 1 and r[0]["dedupe_key"] == "special|SPAF1" and r[0]["kind"] == "special_review", r
    assert r[0]["default_action"] == "not posted" and r[0]["expires_at"], r
    t = r[0]["text"]; w = t.find("Watch: "); assert -1 < t.find(held) < w and -1 < t.find("TWO_SCREENS_ON") < w, t
    SP._await_review("x/SPAF1.mp4", {"title": "T"}, "special", "SPAF1", beats, checks="pass"); assert len(sp("SPAF1")) == 1      # once a special
    SP._await_review("x/SPAF2.mp4", {"title": "T"}, "special", "SPAF2", [{"who": "GRIMM", "line": "x" * 900}])  # 2. a script over 600 characters
    t = sp("SPAF2")[0]["text"]; assert held in t and "TWO_SCREENS_ON" in t and "Watch: https://drive.google.com" in t, t
    setting("TWO_SCREENS_ON", "TRUE")
    SP._await_review("x/SPAF3.mp4", {"title": "T"}, "special", "SPAF3", beats, checks="pass")                    # 3. the switch on, its checks passed
    r = sp("SPAF3"); assert len(r) == 1 and r[0]["kind"] == "special_ready" and "posted by your silence" in r[0]["text"] and "for good" not in r[0]["text"], r
    SP._await_review("x/SPAF4.mp4", {"title": "T"}, "special", "SPAF4", beats, checks="")                        # 4. the switch on, no check on record
    r = sp("SPAF4"); assert len(r) == 1 and r[0]["kind"] == "special_review" and "for good" not in r[0]["text"] and "TWO_SCREENS_ON" not in r[0]["text"], r
    assert r[0]["default_action"].startswith("not posted: it has no check on record"), r
