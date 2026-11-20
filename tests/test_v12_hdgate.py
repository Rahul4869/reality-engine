"""v12 B-OWNER PART 9 - THE HD GATE (step 9a: the reading, the stand-in that merges, every direct upload private, `go_public` with its two policy reads,
the Short's door and its receipt; the long video's gate and his window are step 10). An upload that would go public at once goes up private, and code
makes it public when YouTube shows it processed and in HD, or at its cap - never past a policy read that failed, never on a read that failed. Each rule
both ways, one fault at a time. No keys, no network."""
import ast, datetime as dt, json, os
import pytest
from whatifs import core, shorts2 as SH, release as REL, publish as PUB, notify as NT, launch as LA, hdgate as HG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UTC = dt.timezone.utc
NOW = dt.datetime(2026, 12, 16, 6, 0, tzinfo=UTC)          # a Wednesday
M = dt.timedelta(minutes=1)

@pytest.fixture(autouse=True)
def _no_faults():
    PUB.FAKE_FAULTS.clear(); yield; PUB.FAKE_FAULTS.clear()

@pytest.fixture
def gate_on(setting):
    """R22 (11): HD_GATE_ON is FALSE in code (the shipped value until the pack proves the pipeline's clock); every test that walks the gate sets it TRUE."""
    setting("HD_GATE_ON", "TRUE"); yield setting

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _bench(premise):
    core.store().append("Premise_Bench", [{"bench_id": "B0", "premise": premise, "headline": premise, "family": "", "ptype": "collective", "status": "READY",
                                           "claude_score": 9, "gemini_score": 9, "combined": 9, "added": core.iso()}])

def _short(monkeypatch, setting, sid, now=NOW, premise="What if the Moon left tonight?"):
    """One real (offline) Short with its own id, released through the release sheet's door."""
    _quiet(monkeypatch); _bench(premise); setting("SHORTS_REVIEW_FIRST_N", "0")
    r = SH.run(force=True, now=now, episode_id=sid); assert r["ok"], r
    return r

def _yt(sid): return next(r for r in REL.records(sid) if r["platform"] == "youtube")
def _rc(sid): return _yt(sid)["receipts"]["privacy"]
def _led(sid): return [r for r in core.store().rows("Feature_Ledger") if r.get("episode_id") == sid and r.get("stage") == "release"]
def _sent_privacy(vid): return PUB._fake_get("youtube", vid)["sent"]["status"]["privacyStatus"]
def _fixed(vid): return PUB._fake_get("youtube", vid).get("fixed") or {}
def _shown(vid): return PUB.yt_read(vid).get("privacy")
def _blocked(): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "hd_blocked"]

# ------------------------------------------------------------------ R22 (11): off until it is armed
def test_the_gate_is_off_until_it_is_armed(setting):
    """R22 (11): the shipped value is FALSE - a missed pack line, or a buyer's first install on GitHub's schedule alone, fails to "public at its upload,
    as today", never to "every Short private for hours"; the older tests run with it off (`OLD_SCREENS`)."""
    from tests.conftest import OLD_SCREENS
    assert core.DEFAULTS["HD_GATE_ON"][0] == "FALSE" and OLD_SCREENS["HD_GATE_ON"] == "FALSE"
    setting("HD_GATE_ON", core.DEFAULTS["HD_GATE_ON"][0])
    vid = PUB.yt_upload("x/SHHD00.mp4", "T", "D", [], short=True, now=NOW)
    assert _sent_privacy(vid) == "public" and HG.row(vid) is None and _shown(vid) == "public"

# ------------------------------------------------------------------ the reading and the stand-in
def test_a_repair_survives_the_next_change():
    """R17 (2): the stand-in MERGES every change - a repaired AI label is not forgotten when the privacy or the time changes; the fake privacy call
    honours refuse and ignore as the label's does (R18 (7 d))."""
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}}
    vid = PUB.yt_upload("x/SHHD09.mp4", "T", "D", [], short=True, now=NOW)
    assert PUB.yt_read(vid)["ai"] is False and PUB.yt_set_label(vid, True) and PUB.yt_read(vid)["ai"] is True
    assert PUB.yt_set_privacy(vid, "private") and PUB.yt_read(vid)["privacy"] == "private" and PUB.yt_read(vid)["ai"] is True
    assert PUB.yt_set_privacy(vid, "public"); g = PUB.yt_read(vid); assert g["ai"] is True and g["privacy"] == "public"
    assert PUB.yt_schedule(vid, "2026-12-20T10:00:00Z"); g = PUB.yt_read(vid); assert g["ai"] is True and g["privacy"] == "private"
    PUB.FAKE_FAULTS["youtube"] = {"refuse": ("privacy",)}; assert PUB.yt_set_privacy(vid, "public") is False and PUB.yt_read(vid)["privacy"] == "private"
    PUB.FAKE_FAULTS["youtube"] = {"ignore": ("privacy",)}; assert PUB.yt_set_privacy(vid, "public") is True and PUB.yt_read(vid)["privacy"] == "private"
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}; assert PUB.yt_read(vid)["hd"] is False and PUB.yt_read(vid)["processed"] is True
    PUB.FAKE_FAULTS.clear(); assert PUB.yt_read(vid)["hd"] is True and HG.ready(PUB.yt_read(vid)) and not HG.ready({}) and not HG.ready({"processed": True, "hd": False})

# ------------------------------------------------------------------ the Short's door: private at its upload, public when ready
def test_ready_goes_public_in_the_job(monkeypatch, setting, gate_on):
    """PART 9 (a), (b): the Short goes up PRIVATE (what was really sent is on record), the gate is the door's last act, and a Short YouTube shows ready
    goes public inside its own job - the receipt "public after N min; HD yes", the record DONE, check release_sheet PASS."""
    r = _short(monkeypatch, setting, "SHHD01"); vid = r["yt_id"]
    assert _sent_privacy(vid) == "private" and json.loads(_yt("SHHD01")["sent"])["status"]["privacyStatus"] == "private"
    h = HG.row(vid)
    assert h["state"] == HG.PUBLIC and h["kind"] == "short" and h["hd"] == "yes" and h["ai"] == "TRUE" and int(float(h["cap_min"])) == 60 and h["uploaded"] == core.iso(NOW)
    assert _shown(vid) == "public" and _rc("SHHD01") == [REL.KEPT, "public after 0 min; HD yes"]
    assert _yt("SHHD01")["state"] == REL.DONE and LA.lock_state() != "on" and _led("SHHD01")[0]["status"] == "PASS"

def test_a_video_read_as_sd_stays_private_until_its_cap(monkeypatch, setting, gate_on):
    """THE PLANTED TEST OF THE BRIEF: a video YouTube never shows in HD is private at its upload, at +30 and at +59 minutes, and public at the first
    tick from +60 (HD_SHORT_CAP_MIN) - the receipt says "HD NO (the cap)"."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD02"); vid = r["yt_id"]
    assert _shown(vid) == "private" and HG.row(vid)["state"] == HG.WAITING and _rc("SHHD02") == [REL.WAITING, "private until YouTube shows it in HD: 0 min so far"]
    for mins in (30, 59):
        HG.tick(NOW + mins * M); assert _shown(vid) == "private" and HG.row(vid)["state"] == HG.WAITING, mins
    HG.tick(NOW + 60 * M); h = HG.row(vid)
    assert _shown(vid) == "public" and h["state"] == HG.CAP and h["note"] == "public after 60 min; HD NO (the cap)" and h["hd"] == "no"
    assert REL.settle(NOW + 61 * M) == ["SHHD02"] and _rc("SHHD02") == [REL.KEPT, "public after 60 min; HD NO (the cap)"]

def test_the_thumbnail_is_set_before_the_short_is_public(monkeypatch, setting, gate_on):
    """R17 (1): the gate is `_youtube`'s LAST act - the stand-in's record already holds the thumbnail and the playlist when its privacy turns public."""
    seen = []; real = PUB.yt_set_privacy
    monkeypatch.setattr(PUB, "yt_set_privacy", lambda vid, p: seen.append((p, dict(PUB._fake_get("youtube", vid)))) or real(vid, p))
    r = _short(monkeypatch, setting, "SHHD08"); vid = r["yt_id"]
    pub = [rec for p, rec in seen if p == "public"]
    assert len(pub) == 1 and pub[0].get("thumbnail") == "cover.jpg" and pub[0].get("playlist") and _shown(vid) == "public"

def test_a_waiting_short_is_open_not_flawed(monkeypatch, setting, gate_on):
    """R18 (4): while it waits, the record is OPEN (a WAITING `privacy` receipt keeps it open), the release gate has not run and `sent` says private;
    the pass of a later tick at the cap writes KEPT "HD NO (the cap)" and the record is DONE."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    _short(monkeypatch, setting, "SHHD12"); y = _yt("SHHD12")
    assert y["state"] == REL.OPEN and y["receipts"]["privacy"][0] == REL.WAITING and json.loads(y["sent"])["status"]["privacyStatus"] == "private" and not _led("SHHD12")
    assert REL.settle(NOW + 60 * M) == ["SHHD12"]; y = _yt("SHHD12")
    assert y["receipts"]["privacy"] == [REL.KEPT, "public after 60 min; HD NO (the cap)"] and y["state"] == REL.DONE and _led("SHHD12")[0]["status"] == "PASS"

def test_the_switch_never_strands_a_short(monkeypatch, setting, gate_on):
    """R18 (4 a): a video is gated by its HD_Wait row, never by what the switch says later - switched off while it waits, the Short still goes public at
    its cap, is never read as the lock, and UPLOAD_LOCK is untouched."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD13"); vid = r["yt_id"]; lock = core.S("UPLOAD_LOCK")
    setting("HD_GATE_ON", "FALSE")
    assert HG.tick(NOW + 60 * M) == [vid] and _shown(vid) == "public" and HG.row(vid)["state"] == HG.CAP
    REL.settle(NOW + 61 * M)
    assert _rc("SHHD13") == [REL.KEPT, "public after 60 min; HD NO (the cap)"] and core.S("UPLOAD_LOCK") == lock and LA.lock_state() != "on"

# ------------------------------------------------------------------ R22 (4), (5): a slow clock
def test_a_late_tick_still_finishes_a_short(monkeypatch, setting, gate_on):
    """R22 (5): no tick for seven hours, then one - the Short goes public at that tick: no lock, no block, no row to him."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD03"); vid = r["yt_id"]; assert HG.row(vid)["state"] == HG.WAITING
    assert HG.tick(NOW + 420 * M) == [vid]
    h = HG.row(vid); assert _shown(vid) == "public" and h["state"] == HG.CAP and h["note"] == "public after 420 min; HD NO (the cap)"
    assert LA.lock_state() != "on" and not _blocked()
    REL.settle(NOW + 421 * M); assert _rc("SHHD03") == [REL.KEPT, "public after 420 min; HD NO (the cap)"]

def test_one_late_empty_read_does_not_block(monkeypatch, setting, gate_on):
    """R22 (4): one tick seven hours after the upload whose read fails - the Short stays private and WAITING and nothing goes to him; the next tick
    reads HD and it goes public."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD11"); vid = r["yt_id"]; assert HG.row(vid)["state"] == HG.WAITING
    real = PUB.yt_read; monkeypatch.setattr(PUB, "yt_read", lambda v: {})
    HG.tick(NOW + 420 * M); h = HG.row(vid)
    assert h["state"] == HG.WAITING and h["note"] == "unread 1" and not _blocked() and "privacy" not in _fixed(vid)
    monkeypatch.setattr(PUB, "yt_read", real); PUB.FAKE_FAULTS.clear()
    HG.tick(NOW + 450 * M); h = HG.row(vid)
    assert h["state"] == HG.PUBLIC and h["note"] == "public after 450 min; HD yes" and _shown(vid) == "public"
    REL.settle(NOW + 451 * M); assert _rc("SHHD11") == [REL.KEPT, "public after 450 min; HD yes"]

def test_an_empty_read_makes_nothing_public(monkeypatch, setting, gate_on):
    """R18 (5) with R22 (4): a read that failed is not a pass - private, WAITING, no row to him; BLOCKED, "YouTube could not be read", only
    PRIVATE_ALERT_HOURS past the cap AND on the third empty read in a row (the job's read is the first); then ONE `hd_blocked` row. `go_public`
    itself changes nothing on an empty read."""
    monkeypatch.setattr(PUB, "yt_read", lambda vid: {})
    r = _short(monkeypatch, setting, "SHHD10"); vid = r["yt_id"]; h = HG.row(vid)
    assert h["state"] == HG.WAITING and h["note"] == "unread 1" and _rc("SHHD10")[0] == REL.WAITING and not _blocked() and "privacy" not in _fixed(vid)
    late = 60 + core.S("PRIVATE_ALERT_HOURS", float) * 60
    HG.tick(NOW + (late + 1) * M); h = HG.row(vid)
    assert h["state"] == HG.WAITING and h["note"] == "unread 2" and not _blocked()                    # past the cap and the hours: one late empty read blocks nothing
    HG.tick(NOW + (late + 30) * M); h = HG.row(vid)
    assert h["state"] == HG.BLOCKED and h["note"] == "YouTube could not be read" and len(_blocked()) == 1 and "privacy" not in _fixed(vid)
    b = _blocked()[0]; assert b["dedupe_key"] == f"hdblock|{vid}" and "stays private: YouTube could not be read. Nothing was deleted." in b["text"]
    HG.tick(NOW + (late + 60) * M); assert len(_blocked()) == 1 and HG.row(vid)["state"] == HG.BLOCKED
    assert HG.go_public(vid, NOW + (late + 61) * M, "cap") == (False, "blocked: YouTube could not be read") and "privacy" not in _fixed(vid) and HG.row(vid)["note"] == "YouTube could not be read"

# ------------------------------------------------------------------ the two policy reads at every door, the lock
def test_a_short_marked_for_kids_stays_private(monkeypatch, setting, gate_on):
    """R17 (1 b): `go_public` judges YouTube's own read first - a Short YouTube marked made for kids is BLOCKED, never public, with the kids alarm
    (key kids|<vid>) and ONE `hd_blocked` row; a block holds at every later tick, also when the flag is gone."""
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"kids": True}}
    r = _short(monkeypatch, setting, "SHHD04"); vid = r["yt_id"]; h = HG.row(vid)
    assert _shown(vid) == "private" and h["state"] == HG.BLOCKED and h["note"] == "YouTube marked it made for kids"
    assert _rc("SHHD04")[0] == REL.DRIFT and _yt("SHHD04")["receipts"]["kids"][0] == REL.DRIFT
    k = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "kids_flag"]; assert len(k) == 1 and k[0]["dedupe_key"] == f"kids|{vid}"
    assert len(_blocked()) == 1 and _blocked()[0]["dedupe_key"] == f"hdblock|{vid}"
    PUB.FAKE_FAULTS.clear(); HG.tick(NOW + 90 * M); REL.settle(NOW + 91 * M)
    assert _shown(vid) == "private" and HG.row(vid)["state"] == HG.BLOCKED and len(_blocked()) == 1

def test_a_dropped_label_is_repaired_once_or_blocked(monkeypatch, setting, gate_on):
    """R17 (1 b), R18 (5): an AI label YouTube does not keep is set again ONCE by the gate and read again; still dropped -> BLOCKED, never public, and one
    `hd_blocked` row under "Needs you". A label the repair restores lets the Short out."""
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}, "ignore": ("label",)}
    labels = []; real = PUB.yt_set_label
    monkeypatch.setattr(PUB, "yt_set_label", lambda vid, on=True: labels.append(vid) or real(vid, on))
    r = _short(monkeypatch, setting, "SHHD05"); vid = r["yt_id"]; h = HG.row(vid)
    assert _shown(vid) == "private" and h["state"] == HG.BLOCKED and h["note"] == "the AI label did not hold" and _rc("SHHD05")[0] == REL.DRIFT
    assert labels == [vid, vid]                                                                        # the door's one repair, then the gate's one: never a loop
    b = _blocked(); assert len(b) == 1 and b[0]["id"] in {x["id"] for x in NT.needs()} and "stays private: the AI label did not hold" in b[0]["text"]
    assert f"https://studio.youtube.com/video/{vid}/edit" in b[0]["text"]
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}}; _bench("What if rain fell upward?")
    r2 = SH.run(force=True, now=NOW + 48 * 60 * M, episode_id="SHHD06"); assert r2["ok"]; v2 = r2["yt_id"]
    assert HG.row(v2)["state"] == HG.PUBLIC and _shown(v2) == "public" and PUB.yt_read(v2)["ai"] is True and len(_blocked()) == 1

def test_a_private_read_back_is_the_lock(monkeypatch, setting, gate_on):
    """R18 (7 d): asked public by the gate and still read private - state LOCKED, the receipt DRIFT and `launch.lock_detected` (the detector moved
    from release.py, where private is now the expected answer, into `go_public`)."""
    PUB.FAKE_FAULTS["youtube"] = {"ignore": ("privacy",)}
    seen = []; real = LA.lock_detected
    monkeypatch.setattr(LA, "lock_detected", lambda vid, issues: seen.append(issues) or real(vid, issues))
    r = _short(monkeypatch, setting, "SHHD07"); vid = r["yt_id"]; h = HG.row(vid)
    assert h["state"] == HG.LOCKED and _shown(vid) == "private" and LA.lock_state() == "on" and _rc("SHHD07")[0] == REL.DRIFT and "the lock" in _rc("SHHD07")[1]
    assert len(seen) == 1 and "the HD gate made public" in seen[0][0]

def test_an_hd_wait_that_cannot_be_read_is_never_taken_as_ungated(monkeypatch, setting, gate_on):
    """v12 B-OWNER CG-1 (J1's FR-9a-3, R1-163 (2)(a); R18 (5): a read that failed is not a pass): while tab HD_Wait cannot be read, a gated Short that
    waits for HD is never read as the lock - UPLOAD_LOCK untouched, no DRIFT receipt for its privacy, nothing sent to YouTube for it. A later pass that
    reads the tab judges it as before."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD30"); vid = r["yt_id"]; assert HG.row(vid)["state"] == HG.WAITING and _shown(vid) == "private"
    st = core.store(); real = st.rows; down = [True]
    def rows(tab):
        if down[0] and tab == HG.TAB: raise RuntimeError("Sheets 503: planted - tab HD_Wait could not be read")
        return real(tab)
    monkeypatch.setattr(st, "rows", rows)
    REL.settle(NOW + 10 * M)
    assert LA.lock_state() != "on" and _rc("SHHD30")[0] != REL.DRIFT and _shown(vid) == "private" and "privacy" not in _fixed(vid)
    assert _rc("SHHD30")[0] == REL.WAITING and _rc("SHHD30")[1].startswith("not judged this pass") and _yt("SHHD30")["state"] == REL.OPEN      # R1-167 DQ2 (a)
    down[0] = False
    HG.tick(NOW + 60 * M); assert _shown(vid) == "public" and HG.row(vid)["state"] == HG.CAP
    REL.settle(NOW + 61 * M); assert _rc("SHHD30") == [REL.KEPT, "public after 60 min; HD NO (the cap)"] and LA.lock_state() != "on"

def test_a_missing_hd_wait_tab_is_made_once_and_a_read_that_still_fails_rises(monkeypatch):
    """v12 B-OWNER CG-1 (R1-167 DQ1 (a), CHECK A): a failed read of tab HD_Wait runs `ensure_tabs` ONCE and reads again - the house pattern of
    `org/execute.py` `_rows`: a tab an older Sheet has not got is made and reads empty (None: not gated). A read that still fails, or an `ensure_tabs` that
    fails, rises as `HG.Unread` - never None, which reads as "not gated"."""
    st = core.store(); real = st.rows; made = []
    def missing(tab):
        if tab == HG.TAB and not made: raise RuntimeError("Sheets 400: Unable to parse range: HD_Wait (planted: an older Sheet without the tab)")
        return real(tab)
    monkeypatch.setattr(st, "rows", missing); monkeypatch.setattr(st, "ensure_tabs", lambda: made.append(1))
    assert HG.row("vidCG1") is None and made == [1]
    def down(tab):
        if tab == HG.TAB: raise RuntimeError("Sheets 503: planted - tab HD_Wait could not be read")
        return real(tab)
    monkeypatch.setattr(st, "rows", down)
    with pytest.raises(HG.Unread): HG.row("vidCG1")
    assert made == [1, 1]                                                                              # once a call: no flag, no cache
    def broken():
        raise RuntimeError("Sheets 503: planted - the tabs could not be made")
    monkeypatch.setattr(st, "rows", missing); made.clear(); monkeypatch.setattr(st, "ensure_tabs", broken)
    with pytest.raises(HG.Unread): HG.row("vidCG1")

def test_a_first_release_with_hd_wait_unread_uploads_once_and_concludes_no_lock(monkeypatch, setting, gate_on):
    """v12 B-OWNER CG-1 (R1-167 DQ3 (a), the line at 269): with HD_GATE_ON TRUE and tab HD_Wait unreadable from BEFORE the Short's first release, the
    release raises nothing; the Short is uploaded ONCE (its id on record, never RETRY - a raise between the upload and its id would upload it a second
    time); `enter` writes its row all the same; no lock is concluded; its privacy is "not judged this pass"; and the record's `sent` says private - the
    same pass's switch decided the upload (publish.py 86)."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    st = core.store(); real = st.rows; down = [True]
    def rows(tab):
        if down[0] and tab == HG.TAB: raise RuntimeError("Sheets 503: planted - tab HD_Wait could not be read")
        return real(tab)
    monkeypatch.setattr(st, "rows", rows)
    r = _short(monkeypatch, setting, "SHHD31"); vid = r["yt_id"]; y = _yt("SHHD31")
    assert vid and y["native_id"] == vid and y["state"] != REL.RETRY and int(float(y["tries"] or 0)) == 1 and LA.lock_state() != "on"
    assert _rc("SHHD31")[0] == REL.WAITING and _rc("SHHD31")[1].startswith("not judged this pass") and y["state"] == REL.OPEN
    assert json.loads(y["sent"])["status"]["privacyStatus"] == "private" and _shown(vid) == "private"
    down[0] = False
    assert HG.row(vid)["state"] == HG.WAITING

def test_a_row_that_cannot_be_written_after_the_upload_never_uploads_the_short_twice(monkeypatch, setting, gate_on):
    """v12 B-OWNER CI-1 (OI-G1 of CG-1's block): the HD gate's row is written AFTER the real upload (publish.py 92, 130). An append that fails there no
    longer raises out of `yt_upload`: the new id reaches the release record (never RETRY, never a second upload), `sent` says private, no lock is
    concluded and the privacy is "not judged this pass"; the next pass writes the missing row from the record and the gate finishes it as any other."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    _quiet(monkeypatch); _bench("What if the Moon left tonight?"); setting("SHORTS_REVIEW_FIRST_N", "0")
    st = core.store(); real = st.append; down = [True]
    def append(tab, rows):
        if down[0] and tab == HG.TAB: raise RuntimeError("Sheets 503: planted - the HD gate's row could not be written")
        return real(tab, rows)
    monkeypatch.setattr(st, "append", append)
    SH.run(force=True, now=NOW, episode_id="SHHD32"); y = _yt("SHHD32"); vid = y["native_id"]
    assert vid and y["state"] != REL.RETRY and int(float(y["tries"] or 0)) == 1, y                    # the id on record: a later pass never uploads it again
    assert json.loads(y["sent"])["status"]["privacyStatus"] == "private" and _shown(vid) == "private" and HG.row(vid) is None and LA.lock_state() != "on"
    assert _rc("SHHD32")[0] == REL.WAITING and _rc("SHHD32")[1].startswith("not judged this pass") and y["state"] == REL.OPEN
    told = lambda: [r for r in core.store().rows("Owner_Actions") if r.get("dedupe_key") == f"hdrow|{vid}"]
    assert len(told()) == 1 and told()[0]["id"] in {x["id"] for x in NT.open_rows()}                  # R1-185: he is told at once - one row, however often it failed
    down[0] = False
    REL.settle(NOW + 10 * M); y = _yt("SHHD32")
    h = HG.row(vid); assert h and h["state"] == HG.WAITING and h["kind"] == "short" and h["uploaded"] == core.iso(NOW + 10 * M)      # the cap counts from the row: late, never early
    assert y["native_id"] == vid and int(float(y["tries"] or 0)) == 1 and _rc("SHHD32")[0] == REL.WAITING and "private until YouTube shows it in HD" in _rc("SHHD32")[1]
    assert LA.lock_state() != "on" and _shown(vid) == "private" and len(told()) == 1 and told()[0]["status"] == "ANSWERED"      # the row stands: his alarm is answered
    HG.tick(NOW + 70 * M); assert _shown(vid) == "public" and HG.row(vid)["state"] == HG.CAP

def test_a_row_the_gate_cannot_write_is_told_and_never_raises(monkeypatch, gate_on):
    """v12 B-OWNER CI-1 (R1-185): `enter`'s append failing twice (the second after `ensure_tabs`) raises nothing: ONE WARN line, the `hd_blocked` alarm
    keyed `hdrow|<vid>` with the Studio link, False. So `yt_upload` - the call of every gated door (release 268, specials 404, spinoff 140, pilots 67) -
    returns the new id and the door keeps it: never a second upload."""
    _quiet(monkeypatch); seen = []; monkeypatch.setattr(HG, "log", lambda msg, level="INFO", *a, **k: seen.append((level, str(msg))))
    st = core.store(); real = st.append
    def append(tab, rows):
        if tab == HG.TAB: raise RuntimeError("Sheets 503: planted - the HD gate's row could not be written")
        return real(tab, rows)
    monkeypatch.setattr(st, "append", append)
    assert HG.enter("vidCI1", "short", NOW) is False
    assert len([m for lv, m in seen if lv == "WARN" and "vidCI1" in m]) == 1, seen
    a = [r for r in core.store().rows("Owner_Actions") if r.get("dedupe_key") == "hdrow|vidCI1"]
    assert len(a) == 1 and a[0]["kind"] == "hd_blocked" and "https://studio.youtube.com/video/vidCI1/edit" in a[0]["text"], a
    vid = PUB.yt_upload("x/SHHD33.mp4", "T", "D", [], short=True, now=NOW)
    assert vid == "FAKE_SHHD33.mp4" and HG.row(vid) is None and _sent_privacy(vid) == "private"

def test_a_tick_that_cannot_read_hd_wait_says_so(monkeypatch, gate_on):
    """v12 B-OWNER CI-2 (OI-G2 of CG-1's block): a tick whose read of tab HD_Wait fails says so in ONE WARN line (it looked at no waiting Short) - never
    silence; a tick that reads the tab says nothing of it."""
    seen = []; monkeypatch.setattr(HG, "log", lambda msg, level="INFO", *a, **k: seen.append((level, str(msg))))
    st = core.store(); real = st.rows; down = [True]
    def rows(tab):
        if down[0] and tab == HG.TAB: raise RuntimeError("Sheets 503: planted - tab HD_Wait could not be read")
        return real(tab)
    monkeypatch.setattr(st, "rows", rows)
    assert HG.tick(NOW) == []
    said = [m for lv, m in seen if "HD_Wait" in m]; assert len(said) == 1 and [lv for lv, m in seen if "HD_Wait" in m] == ["WARN"], seen
    assert "could not be read" in said[0] and "Sheets 503" in said[0]
    down[0] = False; seen.clear()
    assert HG.tick(NOW) == [] and not [m for lv, m in seen if "HD_Wait" in m], seen

def _row_fails_twice(monkeypatch):
    """CI-1's three other doors (R1-185, R1-192): the HD_Wait append fails twice - the write after the upload and `enter`'s one retry after
    `ensure_tabs` - then works again. The uploads are counted where the REAL offline `publish.yt_upload` records one (`_fake_put` with the body sent)."""
    st = core.store(); real = st.append; failed, sent = [], []
    def append(tab, rows):
        if tab == HG.TAB and len(failed) < 2: failed.append(tab); raise RuntimeError("Sheets 503: planted - the HD gate's row could not be written")
        return real(tab, rows)
    monkeypatch.setattr(st, "append", append)
    put = PUB._fake_put
    def counted(platform, nid, **kw):
        if platform == "youtube" and "sent" in kw: sent.append(nid)
        return put(platform, nid, **kw)
    monkeypatch.setattr(PUB, "_fake_put", counted)
    return failed, sent

def _told(vid): return [r["kind"] for r in core.store().rows("Owner_Actions") if r.get("dedupe_key") == f"hdrow|{vid}"]

def test_a_special_whose_hd_row_cannot_be_written_keeps_its_id(monkeypatch, setting, gate_on):
    """CI-1, the door at specials.py 404 (`_publish`): the row failing after the upload raised out of `yt_upload` into 404's `except` - the special
    kept NO id ("MADE (not posted)") and the next post uploaded it again; the first copy stayed private with no row. Now the id is kept: POSTED,
    exactly one upload, private, and he is told (`hdrow|<id>`)."""
    from whatifs import specials as SP
    _quiet(monkeypatch); setting("UPLOAD_LOCK", "off"); setting("META_ON", "FALSE"); failed, sent = _row_fails_twice(monkeypatch)
    res = SP._publish("x/SPHD40.mp4", "What if the Moon left tonight?", "SPHD40")
    assert res.get("yt_id") == "FAKE_SPHD40.mp4" and res["status"] == "POSTED", f"the special lost its YouTube id: {res}"
    assert sent == ["FAKE_SPHD40.mp4"] and len(failed) == 2 and HG.row(res["yt_id"]) is None and _sent_privacy(res["yt_id"]) == "private"
    assert _told(res["yt_id"]) == ["hd_blocked"]

def test_a_pilot_whose_hd_row_cannot_be_written_records_its_id(monkeypatch, setting, gate_on):
    """CI-1, the door at pilots.py 67 (`run(publish=True)`): the raise was caught there and the Pilots row recorded yt "" - a video private for ever,
    with no row and no word, and its views never measured. Now the Pilots row keeps the id: exactly one upload, private, and he is told."""
    from whatifs import pilots as PL
    monkeypatch.setenv("WI_SMALL", "1"); _quiet(monkeypatch); setting("UPLOAD_LOCK", "off"); setting("PILOTS_ON", "TRUE")
    core.store().append("Premise_Bench", [{"bench_id": "B0", "added": core.iso(), "status": "READY", "premise": "What if your bed floated", "headline": "Bed", "combined": "8"}])
    failed, sent = _row_fails_twice(monkeypatch)
    r = PL.run(publish=True); assert r["ok"], r
    row = next(x for x in core.store().rows("Pilots") if x["id"] == r["id"])
    assert row["yt_id"] and row["yt_id"] == r["yt_id"] == f"FAKE_{r['id']}.mp4", f"the pilot's row lost its YouTube id: {row}"
    assert sent == [row["yt_id"]] and len(failed) == 2 and HG.row(row["yt_id"]) is None and _told(row["yt_id"]) == ["hd_blocked"]

def test_a_case_files_upload_whose_hd_row_cannot_be_written_returns_its_id(monkeypatch, gate_on):
    """CI-1, the door at spinoff.py 140 (`_publish_long`): the raise went up to `run`, which recorded FAILED with no id - the video private, no row,
    no word. Now the id is returned, nothing raises, exactly one upload. Only spinoff's OWN fake early return (139) is switched off: `yt_upload`
    runs its real offline path."""
    from whatifs import spinoff as SPO
    _quiet(monkeypatch); failed, sent = _row_fails_twice(monkeypatch); monkeypatch.setattr(SPO, "FAKE", False)
    got = SPO._publish_long("x/CFHD41.mp4", "Case Files", "desc", "CFHD41")
    assert got == {"status": "POSTED", "yt_id": "FAKE_CFHD41.mp4"} and sent == ["FAKE_CFHD41.mp4"] and len(failed) == 2
    assert HG.row("FAKE_CFHD41.mp4") is None and _sent_privacy("FAKE_CFHD41.mp4") == "private" and _told("FAKE_CFHD41.mp4") == ["hd_blocked"]

def test_the_upload_check_is_untouched(gate_on):
    """R17 (3 a): the upload check asks for unlisted and compares the answer with unlisted - the gate turns only a wanted privacy of public, and
    `launch.py` passes `hd_gate=False` as a second wall."""
    for kw in ({"hd_gate": False}, {}):
        vid = PUB.yt_upload(f"x/check{len(kw)}.mp4", "Reality Engine - upload check", "Automatic upload check.", ["test"], privacy="unlisted", ai_label=True,
                            verify=False, now=NOW, **kw)
        assert _sent_privacy(vid) == "unlisted" and HG.row(vid) is None
    tree = ast.parse(open(os.path.join(ROOT, "whatifs", "launch.py"), encoding="utf-8").read())
    assert [k.value.value for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "yt_upload" for k in n.keywords if k.arg == "hd_gate"] == [False]

# ------------------------------------------------------------------ one door: no upload asks for public, no code but the gate makes public
def _scan(rel, src):
    """What a file holds against the gate: a `yt_upload` that asks for privacy "public", a `yt_upload` with `hd_gate=False`, a `yt_set_privacy` to
    "public" outside `whatifs/hdgate.py`."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)): continue
        kw = {k.arg: k.value for k in n.keywords}
        if n.func.attr == "yt_upload":
            if isinstance(kw.get("privacy"), ast.Constant) and kw["privacy"].value == "public": out.append(("public upload", rel))
            if isinstance(kw.get("hd_gate"), ast.Constant) and kw["hd_gate"].value is False: out.append(("gate off", rel))
        if n.func.attr == "yt_set_privacy" and rel != "whatifs/hdgate.py":
            if any(isinstance(a, ast.Constant) and a.value == "public" for a in list(n.args[1:2]) + ([kw["privacy"]] if "privacy" in kw else [])): out.append(("made public", rel))
    return out

def test_every_public_upload_passes_the_gate():
    """PART 9: no call of `yt_upload` passes privacy="public" (the body's default IS public, so the gate takes every direct upload - `spinoff.py` lost
    its argument, R17 (3 b)); only `launch.py` passes `hd_gate=False`; outside `hdgate.py` no call of `yt_set_privacy` makes a video public (V4b's
    early release calls `hdgate.go_public`). Planted: the old line of spinoff.py and a direct privacy call are found."""
    found = []
    for base in ("whatifs", "tools"):
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for f in sorted(fs):
                if f.endswith(".py"):
                    p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT).replace("\\", "/")
                    found += _scan(rel, open(p, encoding="utf-8").read())
    assert found == [("gate off", "whatifs/launch.py")], found
    assert _scan("whatifs/spinoff.py", 'PUB.yt_upload(path, title, desc, [], publish_at=None, privacy="public", ai_label=True)') == [("public upload", "whatifs/spinoff.py")]
    assert _scan("whatifs/x.py", 'PUB.yt_set_privacy(vid, "public")') == [("made public", "whatifs/x.py")] and _scan("whatifs/hdgate.py", 'PUB.yt_set_privacy(vid, "public")') == []

# ------------------------------------------------------------------ step 9b: THE SWEEP WALKS THE GATE (R22 (11), R24; the plan's 5.6)
def test_the_sweep_judges_the_gate_on_every_short_of_a_run_with_the_organisation_on(monkeypatch, setting, gate_on):
    """R24 with the plan's 5.6: `tools/sweep.py:hd_of` - every Short of the run went up private and out through the gate (its `privacy` receipt KEPT
    "public after ..."). An id is BAD, each case alone: a Short still WAITING (YouTube has not shown it in HD), a receipt the gate did not write (an
    upload the gate never took: public at once, as `compare` reads it), a Short without a record, no Short at all. The sweep sets HD_GATE_ON TRUE only
    in its runs with the organisation on and asks `hd_of` only there (a part with --org off keeps the gate off, as shipped); the rehearsal sets it
    itself before its Shorts are made and asserts it last; the counter `hd_gated` counts a good id only."""
    import inspect
    from tools import sweep as SW, rehearsal as RH
    _short(monkeypatch, setting, "SHHD20")
    good = "the HD gate held: 1 of 1 upload(s) went up private and public after their wait: SHHD20: public after 0 min; HD yes"
    assert SW.hd_of(core, ["SHHD20"]) == (True, good)
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}; _short(monkeypatch, setting, "SHHD21", now=NOW + 48 * 60 * M, premise="What if rain fell upward?")
    assert SW.hd_of(core, ["SHHD20", "SHHD21"]) == (False, "SHHD21: privacy WAITING: private until YouTube shows it in HD: 0 min so far")
    REL._save("SHHD22", "youtube", NOW, native_id="v22", state=REL.DONE, receipts=REL.compare("youtube", {"privacy": "public"}, {"privacy": "public"}))      # planted: an upload the gate never took
    assert SW.hd_of(core, ["SHHD22"]) == (False, "SHHD22: privacy KEPT: public")
    assert SW.hd_of(core, ["SHHD99"]) == (False, "SHHD99: no YouTube record") and SW.hd_of(core, []) == (False, "no Short was made in this run: the HD gate was not walked")
    s = SW.summary([{"id": "a", "outcome": "ok", "hd": good}, {"id": "b", "outcome": "odd", "hd": good}, {"id": "c", "outcome": "ok"}]); assert s["hd_gated"] == 1
    src = inspect.getsource(SW.one); armed = [l.strip() for l in src.splitlines() if 'set_setting("HD_GATE_ON", "TRUE")' in l]
    assert len(armed) == 2 and all(l.startswith('if org: core.set_setting("HD_GATE_ON", "TRUE")') for l in armed), armed      # the Short mode and the produce mode, organisation on only
    assert src.count("hd_of(core, ") == 3 and src.count('if res["outcome"] == "ok" and org:') == 2 and "                if org:" in src and 'if not ok_h: late.append("the HD gate: "' in src
    r = inspect.getsource(RH.run)
    assert r.index('set_setting("HD_GATE_ON", "TRUE")') < r.index("rs12 = SH12.run(") and "okh9b, saidh9b = hd9b(core12, sh9b); assert okh9b" in r and 'f"; HD gate: {len(sh9b)} of {len(sh9b)} uploads"' in r

# ------------------------------------------------------------------ step 10: THE LONG VIDEO'S GATE AND HIS WINDOW (PART 9; R17 (3 c), ADDS (A); R18 (6); R22 (3))
SLOT = dt.datetime(2026, 12, 16, 14, 30, tzinfo=UTC)       # 20:00 India time, a Wednesday
SD, HD = {"processed": True, "hd": False}, {"processed": True, "hd": True}

def _t(h, m): return dt.datetime(2026, 12, 16, h, m, tzinfo=UTC)

def _long(ep, status="SCHEDULED", slot=SLOT, **kw):
    """A long video as the pipeline leaves it: uploaded PRIVATE with its time (publish_at: never gated at the upload), its Episodes row on its slot."""
    vid = PUB.yt_upload(f"x/{ep}.mp4", f"Title {ep}", "D", [], publish_at=core.iso(slot), now=slot - 30 * 60 * M)
    core.store().append("Episodes", [dict({"episode_id": ep, "slot_et": core.iso(slot), "status": status, "yt_id": vid, "title": f"Title {ep}",
                                           "uploaded_at": core.iso(slot - 30 * 60 * M)}, **kw)])
    return vid

def _ep(ep): return next(e for e in core.store().rows("Episodes") if e.get("episode_id") == ep)
def _rows(kind): return [r for r in core.store().rows("Owner_Actions") if r.get("kind") == kind]

def test_long_step_table(setting):
    """R22 (3): the memo's worked table, a row a tick - slot 14:30, never ready: THE BACKUP CLOCK'S RHYTHM (56 minutes apart), THE HALF-HOURLY RHYTHM
    (:07 and :37), and the pull when it turns ready at 14:42 with 15:15 set. Nothing before the lead; the cap (16:30) is never passed."""
    def walk(ticks, ready_at=None):
        pa, out = SLOT, []
        for t in ticks:
            act, tgt = HG.long_step(SLOT, pa, HD if ready_at and t >= ready_at else SD, t)
            out.append((t.strftime("%H:%M"), act, tgt.strftime("%H:%M") if tgt else None))
            if tgt: pa = tgt
        return out
    backup = [_t(12, 50), _t(13, 46), _t(14, 42), _t(15, 38), _t(16, 34)]
    assert walk(backup) == [("12:50", "none", None), ("13:46", "push", "15:15"), ("14:42", "push", "16:00"), ("15:38", "push", "16:30"), ("16:34", "none", None)]
    assert walk(backup, ready_at=_t(14, 42)) == [("12:50", "none", None), ("13:46", "push", "15:15"), ("14:42", "pull", "15:00"), ("15:38", "none", None), ("16:34", "none", None)]
    half = [_t(13, 7), _t(13, 37), _t(14, 7), _t(14, 37), _t(15, 7), _t(15, 37)]
    assert walk(half) == [("13:07", "none", None), ("13:37", "push", "15:00"), ("14:07", "push", "15:30"), ("14:37", "push", "16:00"), ("15:07", "push", "16:30"),
                          ("15:37", "none", None)]
    assert HG.long_step(SLOT, SLOT, SD, _t(12, 59)) == ("none", None) and HG.long_step(SLOT, None, SD, _t(13, 37)) == ("push", _t(15, 0))      # empty public_at = the slot
    assert HG.long_step(SLOT, SLOT, HD, _t(14, 0)) == ("none", None)                                               # ready on its slot: nothing moves
    tg = [HG.long_step(SLOT, SLOT, SD, _t(12, 0) + k * M)[1] for k in range(400)]
    assert max(t for t in tg if t) == SLOT + 120 * M                                                              # the cap is never passed

def test_the_guard_outlasts_the_clock(setting):
    """R22 (3): with the defaults the guard (75) is above the working clock's longest gap (56 minutes: WATCHDOG_STALE_MIN 45, the Worker's 10-minute cron,
    the start) and the lead (90) holds one tick - a walk of ticks 56 minutes apart, from every first minute of that rhythm, never finds a video YouTube
    does not show in HD public before its cap. With the guard at 45, the walk that starts at 13:35 finds it public at 14:30, the gate never acted."""
    assert float(core.DEFAULTS["HD_GUARD_MIN"][0]) > 60 and float(core.DEFAULTS["HD_LONG_LEAD_MIN"][0]) >= 60
    cap = SLOT + float(core.DEFAULTS["HD_LONG_CAP_MIN"][0]) * M
    def early(first, gap=56):
        pa, t = SLOT, first
        while t <= cap + 60 * M:
            if t >= pa: return pa if pa < cap else None          # YouTube has published it at pa: before its cap is the gate's miss
            _act, tgt = HG.long_step(SLOT, pa, SD, t)
            if tgt: pa = tgt
            t += gap * M
        return None
    assert [early(SLOT - 180 * M + k * M) for k in range(56)] == [None] * 56
    setting("HD_GUARD_MIN", "45"); assert early(_t(13, 35)) == SLOT

def test_a_held_video_is_never_made_public(monkeypatch, setting, gate_on):
    """PART 9: the gate acts only on status SCHEDULED - a held, waiting or taken-down video is never touched (no time set, still private); code never
    makes a long video public (YouTube's own schedule does); an empty read moves nothing either (R18 (5))."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    calls = []; real = PUB.yt_schedule
    monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: calls.append((vid, at)) or real(vid, at))
    held = {ep: _long(ep, st) for ep, st in (("EPL01", "HELD"), ("EPL02", "AWAITING_APPROVAL"), ("EPL03", "HELD_BY_OWNER"))}
    vid = _long("EPL06")
    assert HG.long_tick(_t(13, 46)) == ["EPL06"] and calls == [(vid, "2026-12-16T15:15:00Z")] and _ep("EPL06")["public_at"] == "2026-12-16T15:15:00Z"
    assert all(_shown(v) == "private" and not _ep(ep).get("public_at") for ep, v in held.items()) and _shown(vid) == "private"
    real_read = PUB.yt_read; monkeypatch.setattr(PUB, "yt_read", lambda v: {})
    assert HG.long_tick(_t(14, 42)) == [] and len(calls) == 1 and _ep("EPL06")["public_at"] == "2026-12-16T15:15:00Z" and not _ep("EPL06").get("hd_gate")      # not read is not "already public"
    monkeypatch.setattr(PUB, "yt_read", real_read); setting("HD_GATE_ON", "FALSE")
    assert HG.long_tick(_t(14, 42)) == [] and len(calls) == 1                                                     # switched off: the gate stops moving times

def test_a_public_video_is_never_scheduled_again(monkeypatch, setting, gate_on):
    """R17 ADDS (A): a long video YouTube shows public (his own hand in Studio, YouTube's schedule, an early release) is never given a time again -
    YouTube refuses one on a video that was ever published (S5); it gets its `hd_gate` line and is left alone."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    calls = []; monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: calls.append((vid, at)) or True)
    vid = _long("EPL07"); PUB.yt_set_privacy(vid, "public")                                                       # his hand in Studio
    assert HG.long_tick(_t(13, 46)) == [] and calls == [] and _shown(vid) == "public"
    assert _ep("EPL07")["hd_gate"] == "public 1756 min after upload; HD NO" and not _ep("EPL07").get("public_at")    # uploaded 08:30 the day before, public by 13:46
    PUB.FAKE_FAULTS.clear(); vid2 = _long("EPL08", public_at=core.iso(SLOT + 120 * M)); PUB.yt_set_privacy(vid2, "public")      # the gate had pushed it to its cap
    HG.long_tick(_t(16, 34)); assert calls == [] and _ep("EPL08")["hd_gate"] == "public 1920 min after upload; HD yes"
    core.store().update("Episodes", "episode_id", "EPL08", {"hd_gate": ""}); PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    HG.long_tick(_t(16, 34)); assert calls == [] and _ep("EPL08")["hd_gate"] == "public 1920 min after upload; HD NO (the cap)"

def test_his_window_card(monkeypatch, setting, gate_on):
    """PART 9, HIS WINDOW, R18 (6): on its day a long video that is uploaded and ready gets ONE card `prepublic` with DONE - a row of "Needs you" and of
    the list `wa.push("needs")` sends - its default and its expiry at the slot; not ready by 08:30 India time, one `hd_late` row; a late upload gets its
    card when it turns ready; a tapped card is never sent again."""
    from whatifs import wa as WA
    setting("TWO_SCREENS_ON", "TRUE"); _quiet(monkeypatch)
    vid = _long("EPL04")
    assert HG.tick(_t(2, 0)) == []; c = _rows("prepublic")                                                       # 07:30 India time - through the tick (no Short waits)
    assert len(c) == 1 and c[0]["episode_id"] == "EPL04" and json.loads(c[0]["buttons"]) == [["Done", "DONE"]] and c[0]["default_action"] == "it goes out without an end screen"
    assert c[0]["text"] == f"Tonight 20:00: Title EPL04. Optional before it goes public: the end screen, about 30 seconds in Studio: https://studio.youtube.com/video/{vid}/edit"
    assert c[0]["id"] in {r["id"] for r in NT.needs()} and c[0]["expires_at"]
    bodies = []; monkeypatch.setattr(WA, "in_window", lambda now=None: True); monkeypatch.setattr(WA, "_wire", lambda body: bodies.append(body) or "wamid.N")
    assert WA.push("needs", now=_t(12, 35)) and f"CARD|{c[0]['id']}" in json.dumps(bodies[-1])
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}; _long("EPL05")
    HG.long_tick(_t(2, 10)); assert not _rows("hd_late") and len(_rows("prepublic")) == 1                       # 07:40: not ready, not yet late
    HG.long_tick(_t(3, 5)); HG.long_tick(_t(3, 35)); late = _rows("hd_late")                                      # 08:35 and 09:05 India time
    assert len(late) == 1 and late[0]["episode_id"] == "EPL05" and "does not show it in HD yet" in late[0]["text"]
    PUB.FAKE_FAULTS.clear(); HG.long_tick(_t(10, 0)); c = _rows("prepublic")
    assert sorted(r["episode_id"] for r in c) == ["EPL04", "EPL05"]                                              # the late upload's card comes by itself
    NT.answer(c[0]["id"], "DONE"); HG.long_tick(_t(11, 0)); assert len(_rows("prepublic")) == 2

def test_the_real_tick_finishes_a_waiting_short(monkeypatch, setting, gate_on):
    """R18 (2): `hdgate.tick` is called by the REAL `manage.tick`, after `release.settle`, in a try of its own - a Short WAITING for HD is finished by
    the pipeline's own tick at its cap (until step 10 only the tests and the door's pass called it; the name scan cannot see a common name unwired)."""
    import inspect
    from whatifs import manage as MG
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    r = _short(monkeypatch, setting, "SHHD14"); vid = r["yt_id"]; assert HG.row(vid)["state"] == HG.WAITING
    monkeypatch.setattr(HG, "now_utc", lambda: NOW + 61 * M); MG.tick()
    h = HG.row(vid); assert h["state"] == HG.CAP and h["note"] == "public after 61 min; HD NO (the cap)" and _shown(vid) == "public"
    src = inspect.getsource(MG.tick); assert src.index("RELW.settle()") < src.index("HGT.tick()")

def test_a_video_rescheduled_after_a_pause_is_judged_from_its_new_slot(monkeypatch, setting, gate_on):
    """R17 (3 c): `public_at` has ONE writer, the gate - a time set elsewhere empties it. A video the gate had pushed to its cap, held by a pause and put
    back on its own slot by `manage.resume_held`, is judged from that slot, never from the time the gate set before the pause (else YouTube publishes it
    on its slot without HD while the gate believes it is two hours later). The same for `contract.approve` (his Approve tap, and his silence through
    `approve_by_silence`): the time it sets empties `public_at` (step 10b)."""
    from whatifs import manage as MG, contract as CON
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    _long("EPL09", public_at=core.iso(SLOT + 120 * M))
    assert MG.hold_scheduled("paused") == 1 and _ep("EPL09")["status"] == "HELD"
    MG.resume_held(); e = _ep("EPL09")
    assert e["status"] == "SCHEDULED" and e["slot_et"] == core.iso(SLOT) and e["public_at"] == ""
    assert HG.long_tick(_t(13, 44)) == ["EPL09"] and _ep("EPL09")["public_at"] == "2026-12-16T15:00:00Z"
    s2 = SLOT + 24 * 60 * M                                                                                       # Thursday 20:00 India time: a slot of its own (approve moves a taken one)
    _long("EPL12", status="AWAITING_APPROVAL", slot=s2, public_at=core.iso(s2 + 120 * M))                         # the gate had pushed it to its cap; then it waited for his approval
    assert CON.approve("EPL12").startswith("approved: EPL12") and _ep("EPL12")["status"] == "SCHEDULED" and _ep("EPL12")["slot_et"] == core.iso(s2)
    assert _ep("EPL12")["public_at"] == ""                                                                        # the time approve set empties the gate's
    assert "EPL12" in HG.long_tick(s2 - 46 * M) and _ep("EPL12")["public_at"] == "2026-12-17T15:00:00Z"            # judged from its slot (14:30 + 30), never from 16:30

def test_the_release_step_writes_the_gates_line_and_waits_for_its_time(monkeypatch, setting, gate_on):
    """PART 9: `manage.release` writes the long video's `hd_gate` line when it sees it public, and its private alert counts from max(slot, public_at) -
    the gate's own wait is never an alarm."""
    from whatifs import manage as MG
    _quiet(monkeypatch); monkeypatch.setattr(MG, "_fetch_release", lambda ep, assets=None: {"pinned": ""}); monkeypatch.setattr(PUB, "yt_comment", lambda *a, **k: True)
    vid = _long("EPL10"); PUB.yt_set_privacy(vid, "public"); monkeypatch.setattr(MG, "now_utc", lambda: SLOT + 20 * M)
    MG.release("EPL10"); e = _ep("EPL10")
    assert e["status"] == "LIVE" and e["hd_gate"] == "public 1800 min after upload; HD yes"
    _long("EPL11", public_at=core.iso(SLOT + 120 * M)); monkeypatch.setattr(PUB, "yt_status", lambda v: "private")
    monkeypatch.setattr(MG, "now_utc", lambda: SLOT + 180 * M); MG.release("EPL11")
    assert "private alert sent" not in str(_ep("EPL11").get("notes")) and _ep("EPL11")["status"] == "SCHEDULED"      # 2 h past its slot, under 2 h past the gate's time
    monkeypatch.setattr(MG, "now_utc", lambda: SLOT + 271 * M); MG.release("EPL11"); assert "private alert sent" in str(_ep("EPL11").get("notes"))

# ------------------------------------------------------------------ step 10b: the designer of record's answers to step 10's DESIGN QUESTIONS 2 and 3 (DESIGNER_ON_STEP10_QUESTIONS.md)
def _dicts(rel):
    return [n for n in ast.walk(ast.parse(open(os.path.join(ROOT, rel), encoding="utf-8").read())) if isinstance(n, ast.Dict)]

def _keys(n): return {k.value: v for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant)}

def test_the_upload_time_is_written_with_the_id():
    """DESIGN QUESTION 2, settled: `uploaded_at` (when the file reached YouTube) has ONE writer - `episode.py`, in the update that records `yt_id` right
    after the upload, so the two can never disagree and a resumed attempt that finds its id (it uploads nothing) never rewrites the time. No other
    line of whatifs/ or tools/ writes the key. The real path is the rehearsal's own assert (a whole production)."""
    up = [_keys(n) for n in _dicts("whatifs/episode.py") if "yt_id" in _keys(n) and isinstance(_keys(n).get("status"), ast.Constant) and _keys(n)["status"].value == "UPLOADED"]
    assert len(up) == 1 and "uploaded_at" in up[0] and ast.unparse(up[0]["uploaded_at"]) == "iso()", [sorted(map(str, k)) for k in up]
    writers = []
    for base in ("whatifs", "tools"):
        for dp, _dn, fs in os.walk(os.path.join(ROOT, base)):
            for f in sorted(fs):
                if f.endswith(".py"):
                    rel = os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, "/")
                    writers += [rel for n in _dicts(rel) if "uploaded_at" in _keys(n)]
    assert writers == ["whatifs/episode.py"], writers

def test_a_video_still_in_production_gets_nothing_from_the_gate(monkeypatch, setting, gate_on):
    """DESIGN QUESTION 3, settled: HIS WINDOW speaks of an UPLOADED video only (SCHEDULED or AWAITING_APPROVAL, with its id). A long video still in
    production at 08:30 India time on its day - no `yt_id`, its status neither - gets no `hd_late` and no `prepublic` row, YouTube is not read for it,
    and the tick raises nothing: its lateness already has its own voices (`slot_skipped`, and after three failed tries `pipeline_stop`)."""
    setting("TWO_SCREENS_ON", "TRUE"); _quiet(monkeypatch)
    core.store().append("Episodes", [{"episode_id": "EPL13", "slot_et": core.iso(SLOT), "status": "VISUALS", "title": "Title EPL13"}])
    reads = []; real = PUB.yt_read; monkeypatch.setattr(PUB, "yt_read", lambda v: reads.append(v) or real(v))
    assert HG.tick(_t(3, 35)) == [] and HG.long_tick(_t(4, 0)) == []                                             # 09:05 and 09:30 India time, its own day
    assert not _rows("hd_late") and not _rows("prepublic") and reads == []

# ------------------------------------------------------------------ FINISHED BY FABLE: the corrections of the finishing pass (step 9a) - PART C
def test_the_sheets_privacy_line_is_true_of_both_states():
    """R22 (5) with R22 (11). FOUND AT THE FINISH (the typist's design question 1): the release sheet's `privacy` line said only "private until YouTube
    shows it in HD ... then public" - untrue of the shipped state, where HD_GATE_ON is FALSE and a Short is public at its upload. The line is data
    (SYSTEM.md is generated from it): it names both states, R22 (5)'s words kept for the gate."""
    line = next(r[4] for r in REL.SHEET if r[:2] == ("youtube", "privacy"))
    assert "at once while HD_GATE_ON is off" in line, line
    assert "private until YouTube shows it in HD (at most HD_SHORT_CAP_MIN minutes and the wait for the pipeline's next tick), then public" in line, line

def test_a_blocked_video_is_refused_at_the_door(gate_on):
    """PART 9, A FAILED CHECK STILL HOLDS ("state BLOCKED, never public"). FOUND AT THE FINISH: only `tick` and `finish` passed over a BLOCKED row;
    `go_public` itself - THE ONE DOOR, which another batch may call - judged the video afresh and made it public once the flag was gone."""
    vid = PUB.yt_upload("x/SHHD29.mp4", "T", "D", [], short=True, now=NOW); assert HG.row(vid)["state"] == HG.WAITING
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"kids": True}}
    assert HG.go_public(vid, NOW + M) == (False, "blocked: YouTube marked it made for kids") and HG.row(vid)["state"] == HG.BLOCKED
    PUB.FAKE_FAULTS.clear()                                                                            # the flag is gone: the block still holds, at the door itself
    assert HG.go_public(vid, NOW + 2 * M, "cap") == (False, "blocked: YouTube marked it made for kids")
    assert _shown(vid) == "private" and HG.row(vid)["state"] == HG.BLOCKED and len(_blocked()) == 1

def test_a_job_that_polls_counts_one_empty_read(monkeypatch, gate_on):
    """R22 (4) ("blocked on three reads, never on one"). FOUND AT THE FINISH: `finish` counted an empty read at EVERY poll of the upload job's wait
    (every 15 seconds, up to HD_SHORT_WAIT_S), so a job whose reads failed for a minute stood at "unread 4" - and ONE late empty read, hours on, then
    blocked the Short for good. A pass counts one empty read, however often it polls. (Offline the job never polls: the fault lived in real mode only.)"""
    vid = PUB.yt_upload("x/SHHD21.mp4", "T", "D", [], short=True, now=NOW)
    monkeypatch.setattr(HG, "FAKE", False); monkeypatch.setattr(HG.time, "sleep", lambda s: None); reads = []
    monkeypatch.setattr(PUB, "yt_read", lambda v: reads.append(v) or {})
    assert HG.finish(vid, 45, NOW)[0] == HG.WAITING and len(reads) == 4 and HG.row(vid)["note"] == "unread 1", (len(reads), HG.row(vid)["note"])
    late = 60 + core.S("PRIVATE_ALERT_HOURS", float) * 60
    assert HG.finish(vid, 0, NOW + (late + 1) * M)[0] == HG.WAITING and HG.row(vid)["note"] == "unread 2" and not _blocked()      # one late empty read blocks nothing

def test_compare_never_judges_a_gated_shorts_privacy(monkeypatch, setting, gate_on):
    """R18 (4 b) (a missing test: the memo's break "`privacy` left in `want`" had none - the gate's receipt replaces the row afterwards). For a gated
    Short `compare` is never asked about `privacy`; the row is the gate's alone."""
    seen = []; real = REL.compare
    monkeypatch.setattr(REL, "compare", lambda p, want, got: seen.append((p, sorted(want))) or real(p, want, got))
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    _short(monkeypatch, setting, "SHHD14")
    yt = [w for p, w in seen if p == "youtube"]; assert yt and all("privacy" not in w for w in yt), yt
    assert _rc("SHHD14")[0] == REL.WAITING

def test_a_change_youtube_did_not_take_is_not_the_lock(monkeypatch, gate_on):
    """PART 9, the lock ("a read-back still private -> LOCKED" speaks of a change that was MADE and did not hold: R18 (7 d) plants it with `ignore`).
    FOUND AT THE FINISH (ruled a correction, R1-73): `go_public` did not read `yt_set_privacy`'s answer, so a change YouTube REFUSED or that FAILED - a
    used-up quota, one 5xx - made the Short final and private, set UPLOAD_LOCK, paused production and sent him the alarm, for a call that could not
    act. A refused change waits and is counted ("refused n"); a later call that is taken makes it public; only the third refusal in a row AND
    PRIVATE_ALERT_HOURS past the cap is the lock (R22 (4)'s own two numbers)."""
    seen = []; monkeypatch.setattr(LA, "lock_detected", lambda vid, issues: seen.append(issues))
    vid = PUB.yt_upload("x/SHHD22.mp4", "T", "D", [], short=True, now=NOW)
    PUB.FAKE_FAULTS["youtube"] = {"refuse": ("privacy",)}
    assert HG.go_public(vid, NOW + M) == (False, "not set") and HG.row(vid)["state"] == HG.WAITING and HG.row(vid)["note"] == "refused 1" and seen == []
    late = 60 + core.S("PRIVATE_ALERT_HOURS", float) * 60
    assert HG.tick(NOW + (late + 1) * M) == [vid] and HG.row(vid)["state"] == HG.WAITING and HG.row(vid)["note"] == "refused 2" and seen == []      # past the cap and the hours: a second refusal is not yet the lock
    PUB.FAKE_FAULTS.clear(); HG.tick(NOW + (late + 2) * M)                                             # the next call is taken: public, and nothing was concluded
    assert _shown(vid) == "public" and HG.row(vid)["state"] == HG.PUBLIC and seen == []
    v2 = PUB.yt_upload("x/SHHD23.mp4", "T", "D", [], short=True, now=NOW); PUB.FAKE_FAULTS["youtube"] = {"refuse": ("privacy",)}
    for k in (1, 2, 3): HG.tick(NOW + (late + k) * M)
    h = HG.row(v2); assert h["state"] == HG.LOCKED and "3 times in a row" in h["note"] and "the lock" in h["note"] and len(seen) == 1 and _shown(v2) == "private", h

# ------------------------------------------------------------------ FINISHED AT THE FINISH (PART D, the fifth finisher): HIS WINDOW AND THE LONG VIDEO'S RECEIPT (CD-1 TO CD-3)
def test_his_window_says_nothing_on_a_failed_read_or_to_a_public_video(monkeypatch, setting, gate_on):
    """PART 9, HIS WINDOW, with R18 (5) - FOUND AT THE FINISH (CD-1): `window` ran before the read was looked at, so an empty read (a failed call) at
    the first tick after 08:30 India time on its day sent `hd_late` - "YouTube does not show it in HD yet" - once and for good, a sentence nobody
    read off YouTube; and a video he had already made public in Studio got a card "optional before it goes public". An empty read tells him nothing
    (the next read that answers decides), and his window is the private time before a video goes public (item 156)."""
    vid = _long("EPL12"); real = PUB.yt_read
    monkeypatch.setattr(PUB, "yt_read", lambda v: {})
    HG.long_tick(_t(3, 35)); assert not _rows("hd_late") and not _rows("prepublic")                  # 09:05 India time: the read failed - nothing said
    monkeypatch.setattr(PUB, "yt_read", real); PUB.yt_set_privacy(vid, "public")                    # his own hand in Studio, before the slot
    HG.long_tick(_t(4, 0)); assert not _rows("prepublic") and not _rows("hd_late")
    _long("EPL13"); HG.long_tick(_t(4, 30)); assert [r["episode_id"] for r in _rows("prepublic")] == ["EPL13"]      # a private, ready video still gets its one card

def test_a_failed_read_writes_no_miss_on_the_receipt(monkeypatch, setting, gate_on):
    """PART 9 (the receipt; item 156 BINDS 4) with R18 (5) - FOUND AT THE FINISH (CD-2): `manage.release` writes the long video's `hd_gate` line once,
    from `long_line(e, yt_read(...) or {}, ...)`; a read that failed there was written for good as "HD NO" - a miss the monthly audit would count for a
    video nobody read. A failed read says so on the receipt."""
    from whatifs import manage as MG
    _quiet(monkeypatch); monkeypatch.setattr(MG, "_fetch_release", lambda ep, assets=None: {"pinned": ""}); monkeypatch.setattr(PUB, "yt_comment", lambda *a, **k: True)
    vid = _long("EPL14"); PUB.yt_set_privacy(vid, "public"); monkeypatch.setattr(MG, "now_utc", lambda: SLOT + 20 * M)
    monkeypatch.setattr(PUB, "yt_read", lambda v: {}); MG.release("EPL14")
    assert _ep("EPL14")["hd_gate"] == "public 1800 min after upload; HD not read (YouTube could not be read)"

def test_hd_late_promises_nothing_to_a_video_awaiting_his_approval(monkeypatch, setting, gate_on):
    """PART 9, HIS WINDOW - FOUND AT THE FINISH (CD-3): the `hd_late` row told every long video not in HD by 08:30 India time "It still goes out
    tonight" - also one still AWAITING_APPROVAL, which goes out only when he or his silence approves it (PART 7). Its words now follow the status."""
    PUB.FAKE_FAULTS["youtube"] = {"sd": True}
    _long("EPL15", "AWAITING_APPROVAL"); _long("EPL16")
    HG.long_tick(_t(3, 5)); said = {r["episode_id"]: r["text"] for r in _rows("hd_late")}                # 08:35 India time
    assert "If it is approved it goes out tonight" in said["EPL15"] and "It still goes out tonight" not in said["EPL15"]
    assert "It still goes out tonight" in said["EPL16"]

def test_his_window_runs_with_the_gate_off(monkeypatch, setting):
    """DQ-D1 (R22's ruling; CD-7): what touches a video's privacy or its time stands behind HD_GATE_ON; HIS WINDOW and the long video's `hd_gate` line
    run when HD_GATE_ON or TWO_SCREENS_ON is TRUE. The shipped state at the launch - screens TRUE, gate FALSE - gives the launch's first long videos
    their card (R17 (14 a), item 156) and moves no time; with BOTH cells FALSE (the older path) the gate reads nothing and says nothing."""
    from whatifs import manage as MG
    _quiet(monkeypatch); monkeypatch.setattr(MG, "_fetch_release", lambda ep, assets=None: {"pinned": ""}); monkeypatch.setattr(PUB, "yt_comment", lambda *a, **k: True)
    calls = []; monkeypatch.setattr(PUB, "yt_schedule", lambda vid, at: calls.append((vid, at)) or True)
    vid = _long("EPL18"); sd = _long("EPL19"); reads = []; real = PUB.yt_read
    monkeypatch.setattr(PUB, "yt_read", lambda v: reads.append(v) or dict(real(v), hd=v != sd))                    # EPL18 ready; EPL19 never in HD
    setting("HD_GATE_ON", "FALSE"); setting("TWO_SCREENS_ON", "FALSE")
    assert HG.long_tick(_t(13, 46)) == [] and reads == [] and not _rows("prepublic") and not _rows("hd_late")        # both off: the older path
    setting("TWO_SCREENS_ON", "TRUE")
    assert HG.long_tick(_t(13, 46)) == [] and calls == []                                                          # inside the lead: no push, no pull
    assert [r["episode_id"] for r in _rows("prepublic")] == ["EPL18"] and [r["episode_id"] for r in _rows("hd_late")] == ["EPL19"]
    assert "at 20:00: the wait for HD is switched off, so its time does not move" in _rows("hd_late")[0]["text"]
    assert not _ep("EPL18").get("public_at") and not _ep("EPL19").get("public_at")
    PUB.yt_set_privacy(vid, "public"); monkeypatch.setattr(MG, "now_utc", lambda: SLOT + 20 * M); MG.release("EPL18")
    assert _ep("EPL18")["hd_gate"] == "public 1800 min after upload; HD yes"
