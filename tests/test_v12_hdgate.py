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
    assert HG.go_public(vid, NOW + (late + 61) * M, "cap") == (False, "not read") and "privacy" not in _fixed(vid) and HG.row(vid)["note"] == "YouTube could not be read"

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
