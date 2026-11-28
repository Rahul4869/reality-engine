"""v12 DRAWN-b - the look bar (D13, whatifs/org/look.py): one strong judge answers fixed yes/no questions about the art direction of a finished film's twelve
pictures, blind, beside the owner's reference sheets, the film's own flattened twin and the rejected video's pictures; code computes the verdict. Step L1a:
the pictures, the twin, the kit, the verdict, a session, D13's run with its log rules, the check at the gate of a Short's file (`contract:short_look`, its
verdict computed again) and one whole Short looked at with the bar on. Step L1b: the kit filed by `python -m whatifs.cli look_kit`, its pre-flight row. Step L2: the free re-grade of a Short below the bar, its hold, a later pass under its logged fix, never more than LOOK_HOLDS_MAX_RUN held in a row. Every rule is proven both ways, one fault at a time."""
import datetime as dt, json, os, shutil, subprocess
import numpy as np
import pytest
from PIL import Image
from whatifs import core, models as M, fakes as FK, publish as PUB, release as REL, contract as CON
from whatifs.org import look as LOOK
from tests.conftest import OLD_CLIPS, OLD_MOTION

COLOURS = [(200, 40, 40), (40, 200, 40), (40, 40, 200), (220, 200, 30), (200, 30, 200), (30, 200, 200),
           (240, 140, 20), (120, 40, 220), (20, 120, 60), (110, 200, 90), (150, 90, 40), (60, 60, 160)]

@pytest.fixture
def bar(setting):
    setting("LOOK_BAR_ON", "TRUE"); setting("VIEWER_SEAT_ON", "TRUE"); setting("LOOK_REFS", ""); setting("VIEW_FLOOR_CANARY", ""); setting("LOOK_BAR_PCT", "70")
    FK.LOOK_FAULTS["mode"] = ""
    yield setting
    FK.LOOK_FAULTS["mode"] = ""

def _ff(args): subprocess.run(["ffmpeg", "-y", "-v", "error"] + args, check=True, capture_output=True, timeout=120)

def _card_film(d):
    """24 seconds: twelve two-second colour cards, each with a black half-second at both of its edges (so the middle of a stretch shows its card), and a
    white bar at the card's own place (a lit, varied film)."""
    os.makedirs(d, exist_ok=True); n = 0
    for k, c in enumerate(COLOURS):
        for slot in range(4):
            im = Image.new("RGB", (640, 360), (0, 0, 0) if slot in (0, 3) else c)
            if slot in (1, 2): im.paste((255, 255, 255), (30 + 45 * k, 40, 70 + 45 * k, 320))
            im.save(os.path.join(d, f"card{n:03d}.png")); n += 1
    out = os.path.join(d, "cards.mp4")
    _ff(["-framerate", "2", "-i", os.path.join(d, "card%03d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "10", out])
    return out

def _held_film(d):
    """24 seconds of ONE picture held (the planted flat film of the brief)."""
    os.makedirs(d, exist_ok=True); p = os.path.join(d, "held.png"); im = Image.new("RGB", (640, 360), (90, 110, 150)); im.paste((230, 230, 230), (200, 100, 440, 260)); im.save(p)
    out = os.path.join(d, "held.mp4"); _ff(["-loop", "1", "-i", p, "-t", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "10", out]); return out

_FILMS = {}          # (RULINGS_U3ag C1; the floor's `_MEDIA` form) the two films, made ONCE A PROCESS: the proof's serial runner (`shim/minitest.py`) knows no fixture scope and no `tmp_path_factory`, so the folder is the run's own temp root (`tests/conftest.py` `_TMP`)

@pytest.fixture(scope="module")
def films():
    if _FILMS: return _FILMS
    from tests.conftest import _TMP
    d = os.path.join(_TMP, "lookfilms"); os.makedirs(d, exist_ok=True)
    _FILMS.update({"cards": _card_film(os.path.join(d, "c")), "held": _held_film(os.path.join(d, "h"))})
    return _FILMS

def _asked(monkeypatch):
    calls = []; real = M.ask_watch
    def ask(role, system, prompt, views, **k):
        calls.append({"role": role, "prompt": prompt, "views": views, "caption": k.get("caption")}); return real(role, system, prompt, views, **k)
    monkeypatch.setattr(M, "ask_watch", ask); return calls

def _grey(p): return np.asarray(Image.open(p).convert("L"), np.float32)

def _contrast(p): a = _grey(p); return float(np.percentile(a, 95) - np.percentile(a, 5))

# ------------------------------------------------------------------ 1, 2: the pictures and the flattened twin
def test_1_pictures_sit_in_the_middle_of_twelve_equal_stretches(films, tmp_path):
    pics = LOOK.pictures(films["cards"], str(tmp_path / "p"))
    assert len(pics) == 12
    for k, p in enumerate(pics):
        im = Image.open(p); assert max(im.size) == LOOK.CELL, im.size
        a = np.asarray(im.convert("RGB"), np.float32).reshape(-1, 3); a = a[a.sum(axis=1) < 700]      # the card's colour, without its white bar
        near = min(range(12), key=lambda j: float(np.abs(a.mean(axis=0) - np.array(COLOURS[j], np.float32)).sum()))
        assert near == k and float(a.mean()) > 30, (k, near, a.mean(axis=0))                         # picture k shows card k (never its black edge)
    bad = tmp_path / "x.mp4"; bad.write_bytes(b"not a film")
    assert LOOK.pictures(str(bad), str(tmp_path / "q")) == []

def test_2_the_flattened_twin_is_one_grey_picture_at_a_third_of_its_contrast(tmp_path):
    pics = LOOK.stand_ref(str(tmp_path / "r"), "twin test")
    tw = LOOK.flat(pics, str(tmp_path / "t"))
    assert len(tw) == 12 and len({open(p, "rb").read() for p in tw}) == 1
    a = np.asarray(Image.open(tw[0]).convert("RGB"), np.int16); assert int(np.abs(a[..., 0] - a[..., 1]).max()) <= 3 and int(np.abs(a[..., 1] - a[..., 2]).max()) <= 3
    assert _contrast(tw[0]) <= 0.4 * _contrast(pics[0]), (_contrast(tw[0]), _contrast(pics[0]))

# ------------------------------------------------------------------ 3: the verdict, computed by code from planted rows
ALL = LOOK.ASKED["short"]

def _row(n_yes, z=(), c=None, refs=(LOOK.ASKED["canary"], LOOK.ASKED["canary"]), bar=70, status="counted", drop=(), kind="short"):
    letters = iter(LOOK.LETTERS); items, asked, answers, names = {}, {}, {}, {}
    def put(kd, keys, yes):
        L = next(letters); items[L] = kd; asked[kd] = list(keys)
        answers[L] = {k: ("yes" if k in yes else "no") for k in ALL if not (kd == "N" and k in drop)}           # every film is answered all eight questions
    put("N", LOOK.ASKED[kind], n_yes); put("Z", LOOK.ASKED["twin"], z)
    if c is not None: put("C", LOOK.ASKED["canary"], c)
    for i, ry in enumerate(refs, 1): put(f"R{i}", LOOK.ASKED["canary"], ry); names[f"R{i}"] = f"sheet {i}"
    return {"status": status, "items": json.dumps(items), "asked": json.dumps(asked), "names": json.dumps(names), "answers": json.dumps(answers), "bar": bar}

def test_3_the_verdict_of_planted_rows_both_ways(bar):
    six, five = ALL[:6], ALL[:5]
    r = LOOK.verdict(_row(six, c=())); assert r["status"] == "pass" and "6 of 8" in r["why"] and r["refs"] == 2 and r["canary"] == [0, 5], r            # (a)
    r = LOOK.verdict(_row(five)); assert r["status"] == "fail" and r["missed"] == ["depth", "system", "caption"], r                                     # (b)
    assert "weak on depth and energy, one design for all lettering, captions" in r["why"] and "(70% needed)" in r["why"]
    r = LOOK.verdict(_row(six, z=("frame", "light", "colour"))); assert r["status"] == "void" and "flattened picture" in r["why"], r                    # (c)
    r = LOOK.verdict(_row(six, c=LOOK.ASKED["canary"])); assert r["status"] == "pass" and r["canary"] == [5, 5], r                                     # (d) R16: C voids nothing
    r = LOOK.verdict(_row(six, refs=(LOOK.ASKED["canary"], ("frame", "light", "colour")))); assert r["status"] == "void" and "(sheet 2)" in r["why"], r  # (e)
    r = LOOK.verdict(_row(five, drop=("caption",))); assert r["status"] == "void" and "did not answer every question" in r["why"], r                   # (f) never fail
    r = LOOK.verdict(_row(six, refs=())); assert r["status"] == "void" and r["why"] == "no reference sheet stood beside the film", r                     # (g)
    st = "not counted: answered by gemini:gem_pro"
    r = LOOK.verdict(_row(six, status=st)); assert r["status"] == "void" and r["why"] == st, r                                                         # (h)
    assert LOOK.verdict(_row(ALL[:5], kind="long"))["status"] == "pass" and LOOK.verdict(_row(ALL[:4], kind="long"))["status"] == "fail"               # (i) 5 / 4 of 7
    assert LOOK.verdict(_row(ALL[:4], bar=50))["status"] == "pass" and LOOK.verdict(_row(ALL[:3], bar=50))["status"] == "fail"                         # ON the bar: 400 = 400
    bar("LOOK_BAR_PCT", "90")
    r = LOOK.verdict(_row(six, bar=70)); assert r["status"] == "pass", r                                                                              # (j) the row's bar
    r = LOOK.verdict(_row(six, z=("same", "system", "caption", "alive", "depth"))); assert r["status"] == "pass", r                                     # (k) twin on its three
    assert LOOK.again([])["status"] == "void" and LOOK.again([_row(five), _row(six)])["status"] == "pass"

# ------------------------------------------------------------------ 4, 5: a session, offline
def test_4_a_session_is_blind_counted_only_from_a_strong_claude_and_stores_every_field(bar, monkeypatch, tmp_path):
    calls = _asked(monkeypatch); out = str(tmp_path)
    pics = LOOK.stand_ref(str(tmp_path / "film"), "a varied film"); refs, why = LOOK.kit(out); canary = LOOK.stand_bad(str(tmp_path / "bad"))
    assert why == "" and len(refs) == 2
    r1 = LOOK.session("S-look-1", "sha1", pics, "short", refs, canary, "EPLOOK4")
    assert r1["status"] == "pass" and r1["why"].startswith("8 of 8"), r1
    rows = [x for x in core.store().rows(LOOK.LOG) if x["episode_id"] == "EPLOOK4"]
    assert len(rows) == 1 and set(rows[0]) >= set(core.TABS[LOOK.LOG]) and all(str(rows[0][k]) != "" for k in core.TABS[LOOK.LOG] if k not in ("fix", "view"))
    assert json.loads(rows[0]["asked"])["Z"] == ["frame", "light", "colour"] and json.loads(rows[0]["asked"])["N"] == list(ALL) and str(rows[0]["bar"]) == "70"
    p = calls[0]["prompt"]
    assert calls[0]["role"] == "look_claude" and all(f"\n- {k}: " in p for k in ALL) and len(calls[0]["views"]) == 5
    assert calls[0]["caption"] == "FILM {label} (twelve pictures spread evenly over its length):"
    import re
    assert not re.search(r"(?i)twin|canary|reject|reference|flat|stand", p + json.dumps([v["label"] for v in calls[0]["views"]]))
    LOOK.session("S-look-2", "sha1", pics, "short", refs, canary, "EPLOOK4b")
    r2 = [x for x in core.store().rows(LOOK.LOG) if x["episode_id"] == "EPLOOK4b"][0]
    assert json.loads(r2["items"]) != json.loads(rows[0]["items"])                                            # the letters are drawn from the session id
    for who in ({"provider": "gemini", "role": "opus"}, {"provider": "claude", "role": "haiku"}):
        monkeypatch.setattr(M, "last_call", lambda who=who: dict(who, model="m"))
        r = LOOK.session("S-look-3", "sha1", pics, "short", refs, canary, "EPLOOK4c")
        assert r["status"] == "void" and r["why"] == f"not counted: answered by {who['provider']}:{who['role']}", r

def test_5_the_planted_flat_film_fails_at_its_first_session(bar, films, monkeypatch, tmp_path):
    calls = _asked(monkeypatch)
    r = LOOK.plain(LOOK.run(None, "EPLOOK5", films["held"], str(tmp_path), "short"))
    assert r["status"] == "fail" and r["yes"] == 0 and r["asked"] == 8 and len(calls) == 1, r

# ------------------------------------------------------------------ 6, 7, 8: the judge's faults and D13's run
def test_6_a_judge_that_fails_its_canaries_makes_the_session_void_and_reports_it_once(bar, films, tmp_path):
    for mode, words in (("lenient", "flattened picture"), ("harsh", "failed a reference you chose (stand-in"), ("mute", "did not answer every question")):
        FK.LOOK_FAULTS["mode"] = mode
        o = LOOK.run(None, f"EPLOOK6{mode}", films["cards"], str(tmp_path / mode), "short"); r = LOOK.plain(o)
        assert r["status"] == "void" and words in r["why"], (mode, r)
        assert CON._look({"look": r}) == (CON.NA, r["why"][:380]), (mode, CON._look({"look": r}))          # the check says N/A: a void session holds nothing
        assert [m["dedupe_key"] for m in o.memos] == ["look|void"] and o.memos[0]["to_depts"] == ["D13"], (mode, o.memos)

def test_7_the_log_rules_of_run(bar, films, monkeypatch, tmp_path):
    calls = _asked(monkeypatch); out = str(tmp_path)
    def go(ep, film, fixed=""): return LOOK.plain(LOOK.run(None, ep, films[film], out, "short", fixed))
    assert go("EPL7P", "cards")["status"] == "pass" and len(calls) == 1
    assert go("EPL7P", "cards")["status"] == "pass" and go("EPL7P", "cards", "grade")["status"] == "pass" and len(calls) == 1           # a pass is never asked again
    r = go("EPL7F", "held"); assert r["status"] == "fail" and r["fix"] == "" and len(calls) == 2
    assert go("EPL7F", "held")["status"] == "fail" and len(calls) == 2                                                                 # returned until a fix is given
    r = go("EPL7F", "held", "grade"); assert r["status"] == "fail" and r["fix"] == "grade" and len(calls) == 3                          # ONE new session...
    assert go("EPL7F", "held", "grade")["fix"] == "grade" and go("EPL7F", "held")["status"] == "fail" and len(calls) == 3                # ...whose result is final
    n = len(calls)                                                                                                                       # R16: the three-session walk
    assert go("EPL7W", "held")["status"] == "fail"
    FK.LOOK_FAULTS["mode"] = "mute"; assert go("EPL7W", "held", "grade")["status"] == "void"; FK.LOOK_FAULTS["mode"] = ""
    assert go("EPL7W", "held")["status"] == "fail" and len(calls) == n + 2                                                               # no fix given: the fail stands
    assert go("EPL7W", "held", "grade")["status"] == "fail" and len(calls) == n + 3                                                      # a later pass: ONE more
    for fx in ("", "grade", "grade", ""): go("EPL7W", "held", fx)
    assert len(calls) == n + 3
    FK.LOOK_FAULTS["mode"] = "mute"; n = len(calls)
    assert go("EPL7V", "cards")["status"] == "void" and go("EPL7V", "cards")["status"] == "void" and len(calls) == n + 2
    r = go("EPL7V", "cards"); assert r["status"] == "void" and r["why"].endswith("(not judged again)") and len(calls) == n + 2         # two voids are the last
    FK.LOOK_FAULTS["mode"] = ""; bar("LOOK_CAP_PER_FILM_INR", "0"); n = len(calls)
    r = go("EPL7C", "cards"); assert r["status"] == "void" and r["why"].startswith("the month's look money is spent (Rs") and len(calls) == n

def test_8_a_film_made_to_the_bar_passes_at_its_first_session_and_nothing_is_made_again(bar, films, monkeypatch, tmp_path):
    calls = _asked(monkeypatch)
    o = LOOK.run(None, "EPLOOK8", films["cards"], str(tmp_path), "short"); r = LOOK.plain(o)
    assert r["status"] == "pass" and r["yes"] == 8 and r["fix"] == "" and len(calls) == 1 and o.memos == [], r
    assert LOOK.m_run(r) == {"look_pass": 1, "look_fail": 0, "look_void": 0, "look_yes": 8, "look_asked": 8}

# ------------------------------------------------------------------ 9: the kit - its reading half (step L1a), its filing and the pre-flight row (step L1b)
def _sheet(tmp_path, name):
    pics = LOOK.stand_ref(str(tmp_path / f"{name}_c"), name); im = Image.new("RGB", (4 * 320, 3 * 180))
    for i, p in enumerate(pics): im.paste(Image.open(p), ((i % 4) * 320, (i // 4) * 180))
    f = str(tmp_path / f"{name}.jpg"); im.save(f, "JPEG", quality=92); return f

def test_9_the_kit_keeps_only_the_files_that_were_filed_and_real_mode_without_it_is_void(bar, monkeypatch, tmp_path):
    good, other = _sheet(tmp_path, "good"), _sheet(tmp_path, "other")
    gid = PUB.drive_upload(good, "look_ref_good.jpg", public=False)[0]; oid = PUB.drive_upload(other, "look_ref_other.jpg", public=False)[0]
    bar("LOOK_REFS", json.dumps([{"name": "good", "file": gid, "sha": REL.sha(good), "keys": ["frame", "light", "glitter"], "grid": [4, 3], "made": "d"},
                                 {"name": "changed", "file": oid, "sha": REL.sha(good), "keys": ["frame"], "grid": [4, 3], "made": "d"}]))
    refs, why = LOOK.kit(str(tmp_path / "k"))
    assert why == "" and [r["name"] for r in refs] == ["good"] and refs[0]["keys"] == ["frame", "light"] and len(refs[0]["pics"]) == 12
    assert max(Image.open(refs[0]["pics"][0]).size) == LOOK.CELL
    bar("LOOK_REFS", ""); monkeypatch.setattr(LOOK, "FAKE", False)
    asked = []; monkeypatch.setattr(M, "ask_watch", lambda *a, **k: asked.append(a) or {})
    r = LOOK.plain(LOOK.run(None, "EPLOOK9", str(tmp_path / "none.mp4"), str(tmp_path / "k2"), "short"))
    assert r["status"] == "void" and r["why"] == "no look kit" and asked == [], r

def test_9_the_kit_is_filed_hashed_from_the_command_and_the_pre_flight_says_when_there_is_none(bar, monkeypatch, tmp_path, capsys):
    import sys
    from whatifs import cli, preflight as PF
    big = str(tmp_path / "big.png"); Image.new("RGB", (2560, 1920), (120, 60, 30)).save(big); good = _sheet(tmp_path, "good")
    monkeypatch.setattr(sys, "argv", ["cli", "look_kit", f"{big}|mahadev|frame,light,glitter", f"{good}|skit|light, caption"]); cli.main()
    printed = capsys.readouterr().out; cell = json.loads(core.S("LOOK_REFS"))
    assert [e["name"] for e in cell] == ["mahadev", "skit"] and [e["keys"] for e in cell] == [["frame", "light", "glitter"], ["light", "caption"]], cell
    assert all(e["grid"] == [4, 3] and e["made"] and e["file"] in printed and e["sha"] in printed for e in cell), (cell, printed)
    assert "http" not in printed and "drive.google" not in printed                                  # names, ids and hashes - never a link
    for i, e in enumerate(cell):                                                                    # the filed file IS the hashed one: a JPEG, at most 1280 on its long side
        p = PUB.drive_download(e["file"], str(tmp_path / f"back{i}.jpg")); im = Image.open(p)
        assert REL.sha(p) == e["sha"] and im.format == "JPEG" and max(im.size) <= 1280, (e, im.format, im.size)
    assert Image.open(str(tmp_path / "back0.jpg")).size == (1280, 960)
    refs, why = LOOK.kit(str(tmp_path / "k")); assert why == "" and [r["name"] for r in refs] == ["mahadev", "skit"] and refs[0]["keys"] == ["frame", "light"]
    assert not [r for r in core.store().rows("Owner_Actions") if "look" in str(r.get("kind"))]       # filing the kit sends him nothing
    monkeypatch.setattr(LOOK, "FAKE", False)
    def row(): return next(x for x in PF.run(need_voice=False) if x[0] == "look kit")
    r = row(); assert r[1] is True and r[2] == "2 reference sheet(s) filed" and r[3] is False, r
    bar("LOOK_REFS", ""); r = row(); assert r[1] is False and "no look kit" in r[2] and "void on every real film" in r[2] and r[3] is False, r

# ------------------------------------------------------------------ 13, 14: the check at the gate of a Short's file (`contract:short_look`)
def _ladder(bar):
    for k in list(OLD_CLIPS) + list(OLD_MOTION): bar(k, core.DEFAULTS[k][0])          # the clip market and the motion ladder as shipped: the gate of a Short's file runs

def test_13_a_void_session_or_a_first_fail_holds_nothing_and_the_cell_switches_the_bar_off(bar, films, tmp_path):
    _ladder(bar); ctx = {"short_file": {"path": films["cards"], "units": [], "sound": None}}
    def check(r): st, ev = CON.p_short_look(dict(ctx, look=r)); return st, ev, CON.failed([{"feature": "short_look", "status": st, "evidence": ev}])
    FK.LOOK_FAULTS["mode"] = "mute"
    r = LOOK.plain(LOOK.run(None, "EPLOOK13V", films["cards"], str(tmp_path / "v"), "short"))
    assert r["status"] == "void" and check(r) == (CON.NA, r["why"][:380], []), (r, check(r))                 # ONE void session: N/A, the Short is handed over
    LOOK.run(None, "EPLOOK13V", films["cards"], str(tmp_path / "v"), "short"); r = LOOK.plain(LOOK.run(None, "EPLOOK13V", films["cards"], str(tmp_path / "v"), "short"))
    assert r["why"].endswith("(not judged again)") and check(r) == (CON.NA, r["why"][:380], []), (r, check(r))  # the run's own words after its last void: still N/A
    FK.LOOK_FAULTS["mode"] = ""
    r = LOOK.plain(LOOK.run(None, "EPLOOK13F", films["held"], str(tmp_path / "f"), "short"))
    assert r["status"] == "fail" and r["fix"] == "" and check(r) == (CON.NA, "below the bar once: no free fix has run, so nothing is held", []), (r, check(r))
    bar("LOOK_BAR_ON", "FALSE"); n = len(core.store().rows(LOOK.LOG))
    r = LOOK.plain(LOOK.run(None, "EPLOOK13O", films["cards"], str(tmp_path / "o"), "short"))
    assert r["status"] == "off" and len(core.store().rows(LOOK.LOG)) == n, r                                  # the cell FALSE: no session, no row ...
    assert check(r)[:2] == (CON.NA, "the look bar is switched off (LOOK_BAR_ON / VIEWER_SEAT_ON)")             # ... and N/A

def test_14_the_gate_computes_the_verdict_again_from_the_stored_answers(bar, films, tmp_path):
    _ladder(bar); ctx = {"short_file": {"path": films["cards"], "units": [], "sound": None}}
    r = LOOK.plain(LOOK.run(None, "EPLOOK14", films["cards"], str(tmp_path), "short"))
    assert r["status"] == "pass" and CON.p_short_look(dict(ctx, look=r)) == (CON.PASS, r["why"][:380]), r
    bad = (CON.FAIL, "the stored verdict is not the code's verdict on its own answers")
    assert CON.p_short_look(dict(ctx, look=dict(r, row=dict(r["row"], status="not counted: answered by gemini:fast")))) == bad          # the row's status edited
    ans = {L: {k: "no" for k in a} for L, a in json.loads(r["row"]["answers"]).items()}
    assert CON.p_short_look(dict(ctx, look=dict(r, row=dict(r["row"], answers=json.dumps(ans))))) == bad                                # its answers edited
    assert CON.p_short_look(dict(ctx, look=dict(r, status="fail"))) == bad                                                              # the stored status edited
    assert CON.p_short_look(dict(ctx, short_file={}, look=r))[0] == CON.FAIL                                                            # no finished file: the file's own rule

# ------------------------------------------------------------------ 19: one whole Short with the bar on (the long video's half comes with step L3)
DEC = dt.datetime(2026, 12, 1, 6, 0, tzinfo=dt.timezone.utc)
SHORT_ID = "SH209912190900"          # this file's own id (no other test file uses it)

def test_19_a_whole_short_is_looked_at_once_with_the_bar_on_and_its_money_is_its_line(bar, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    from tests.test_v12_money import _covered, _summary
    from tests.paid_calls import watch
    from whatifs import shorts2 as SH, costguard as CG
    _ladder(bar); bar("MONTH_CAP_OVERRIDES", ""); bar("SHORTS_REVIEW_FIRST_N", "0"); bar("SHORT_FORMAT_FORCE", "S1")
    q2(monkeypatch); _bench("What if the Moon left tonight?", "What if gravity doubled for one hour?", "What if the Sun went out?")
    c = watch(monkeypatch)
    try:
        r = SH.run(force=True, publish=False, now=DEC, episode_id=SHORT_ID); assert r.get("ok"), r
        rows = [x for x in core.store().rows(LOOK.LOG) if x.get("episode_id") == SHORT_ID]
        led = {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == SHORT_ID}
        assert len(rows) == 1 and rows[0]["kind"] == "short" and LOOK.again(rows)["status"] == "pass", rows                   # ONE session, the fake judge passes it
        assert led["short_look"] == (CON.PASS, LOOK.again(rows)["why"][:380]), led.get("short_look")
        assert c["watch:look_claude"] == 1 and _covered({k: n for k, n in c.items() if k.startswith("watch:")}, CG.lines("short", fmt="S1")) == [], dict(c)
        assert [l["calls"] for l in CG.lines("short", fmt="S1") if l["key"] == "look"] == [{"watch:look_claude": 2}]                         # the cost row of the look: its line
        j, _row_ = _summary(SHORT_ID); assert j["unlisted"] == [] and j["over"] == [], j                                                    # costguard.reconcile clean
    finally:
        shutil.rmtree(os.path.join(core.WORK, SHORT_ID), ignore_errors=True)

def test_22_the_sweep_judges_the_look_of_each_id_on_its_short_and_counts_it(bar):
    """L1c (R16 (a)): `look_of` on planted ledgers - the Short's newest `short_look` PASS -> ok, the words begin "the look bar judged: "; N/A "void by
    its canary: ..." -> ok; N/A "not judged", a first fail ("below the bar once"), the bar switched off, a missing row, a FAIL -> BAD; an id with no
    Short is asked nothing; `summary()` counts `look_judged` (judged AND the id good); the three branches of `one` and the rehearsal call it (the form
    of tests/test_v12_drawn.py's judge of the drawn arm)."""
    import inspect
    from tools import sweep as SW, rehearsal as RH
    def judge(sh, *rows):
        core.store().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": sh, "feature": "short_look", "status": st, "evidence": ev} for st, ev in rows])
        return SW.look_of(core, "EP" + sh[2:], short=sh)
    ok, w = judge("SHLK221", (CON.PASS, "the look bar held: 8 of 8 yes (bar 70%)")); assert ok and w.startswith("the look bar judged: SHLK221: ") and "8 of 8" in w, w
    ok, w = judge("SHLK222", (CON.NA, "void by its canary: the judge passed the film's own flattened picture"))
    assert ok and w == "the look bar was void by its canary: SHLK222: the judge passed the film's own flattened picture", w
    for sh, row in (("SHLK223", (CON.NA, "not judged")), ("SHLK224", (CON.NA, "below the bar once: no free fix has run, so nothing is held")),
                    ("SHLK225", (CON.NA, "the look bar is switched off (LOOK_BAR_ON / VIEWER_SEAT_ON)")),
                    ("SHLK226", (CON.FAIL, "the stored verdict is not the code's verdict on its own answers"))):
        ok, w = judge(sh, row); assert not ok and w.startswith(f"short_look {row[0]} on {sh}: "), (sh, w)
    ok, w = judge("SHLK227"); assert not ok and w.startswith("short_look missing on SHLK227"), w                                   # a missing row
    ok, w = judge("SHLK228", (CON.PASS, "the look bar held: 8 of 8"), (CON.FAIL, "y")); assert not ok and "FAIL" in w, w           # the newest verdict
    ok, w = SW.look_of(core, "EPLK229", short=None); assert ok and not w.startswith("the look bar judged"), w                     # no Short: nothing asked, not counted
    s = SW.summary([{"id": "a", "outcome": "ok", "look": "the look bar judged: x"}, {"id": "b", "outcome": "odd", "look": "the look bar judged: x"},
                    {"id": "c", "outcome": "ok", "look": "the look bar was void by its canary: x"}, {"id": "d", "outcome": "ok", "look": "the look bar asked nothing of d"},
                    {"id": "e", "outcome": "ok"}])
    assert s["look_judged"] == 1 and s["bad_ids"] == ["b"], s
    src = inspect.getsource(SW.one)
    assert src.count('ok_l, res["look"] = look_of(core, ep, short=') == 3 and 'look_of(core, ep, short=ep)' in src and 'look_of(core, ep, short="SH" + ep[2:], long=True)' in src \
        and 'look_of(core, ep, short="SH" + ep[2:] if res.get("ladder") == "climbed" else None, long=True)' in src and 'if not ok_l: late.append("the look bar: "' in src
    assert src.count('if not ok_l: res["outcome"] = "odd"; res["problems"].append("the look bar: "') == 2                           # the rehearsal mode and the produce mode
    r = inspect.getsource(RH.run)
    assert 'look12(core12, epid, short=s + epid[2:]) for s in ("SH", "SHB")' in r and 'all(x.startswith("the look bar judged: ") for x in saidl12)' in r \
        and r.index('print("inside the format:", said12[:420])') < r.index('print("look:"')


# ------------------------------------------------------------------ L2: a Short's free fix, its hold, a later pass under its logged fix, the run of holds
def _judge(monkeypatch, films, *seq):
    """The judge stubbed by session, in turn: "fail" shows it the planted flat film's pictures, "void" mutes it, "pass" shows the Short's own pictures."""
    seq = list(seq); real = LOOK.pictures; said = []
    def pictures(master, d):
        s = seq.pop(0) if seq else "pass"; said.append(s); FK.LOOK_FAULTS["mode"] = "mute" if s == "void" else ""
        return real(films["held"] if s == "fail" else master, d)
    monkeypatch.setattr(LOOK, "pictures", pictures); return said

def _regrades(monkeypatch, c=None, broken=False):
    """`shorts2.regrade` counted: each entry True when nothing was bought during it (`paid_calls.watch`); `broken` makes it raise."""
    from whatifs import shorts2 as SH
    done = []; real = SH.regrade
    def regrade(made, shots):
        if broken: raise RuntimeError("planted: the re-grade broke")
        before = dict(c or {}); out = real(made, shots); done.append(dict(c or {}) == before); return out
    monkeypatch.setattr(SH, "regrade", regrade); return done

def _setup(bar, monkeypatch):
    from tests.test_v12_short import _quiet as q2, _bench
    _ladder(bar); bar("MONTH_CAP_OVERRIDES", ""); bar("SHORTS_REVIEW_FIRST_N", "0"); bar("SHORT_FORMAT_FORCE", "S1")
    q2(monkeypatch); _bench("What if the Moon left tonight?", "What if gravity doubled for one hour?", "What if the Sun went out?")

def _whole(ep, k=0, publish=False):
    from whatifs import shorts2 as SH
    r = SH.run(force=True, publish=publish, now=DEC + dt.timedelta(days=k), episode_id=ep)
    rows = [x for x in core.store().rows(LOOK.LOG) if x.get("episode_id") == ep]
    led = {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}
    return r, rows, led, next((x for x in SH._rows() if x.get("id") == ep), {})

def _gone(*eps):
    for ep in eps: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)

# ------------------------------------------------------------------ L3, HALF A (episode.py, render.py): 15, 16, 21, 25, 26 - the long video's look, its free fix, its hold
def _render_levers(monkeypatch, tmp_path, fix, plan):
    """ONE `_render` of two 10 s still lines (line 0 inside the opening window, line 1 outside it) with `job.look_fix` planted: the plan the Atmosphere pack
    is handed, the particle density of the render and each piece's (seed, energy) - no pixel is drawn (`parallax_segment` is recorded, `concat` stops it)."""
    import cv2
    from whatifs import episode as EP, render as RN
    class Stop(Exception): pass
    seen = {"plan": None, "pieces": []}
    monkeypatch.setattr(EP, "atmosphere_layer", lambda ep, units, shots, plan_, fps, so=None: seen.__setitem__("plan", dict(plan_)))
    monkeypatch.setattr(RN, "parallax_segment", lambda img, path, nf, **k: (seen["pieces"].append((str(k.get("seed")), k.get("energy"))), seen.__setitem__("dens", RN._FIX["density"])))
    monkeypatch.setattr(RN, "concat", lambda segs, path: (_ for _ in ()).throw(Stop()))
    units = [{"i": i, "start": 10.0 * i, "end": 10.0 * (i + 1), "text": f"Line {i} in your kitchen.", "beat": 1, "speaker": "DIRECTOR", "tag": "none"} for i in range(2)]
    files = {"img": {}, "clips": {}}
    for i in range(2):
        files["img"][i] = str(tmp_path / f"lv{i}.png"); cv2.imwrite(files["img"][i], np.full((360, 640, 3), 90 + 60 * i, np.uint8))
    job = EP.Job(files=files, shots=[{"type": "still", "prompt": f"p{i}"} for i in range(2)], units=units, vo=type("V", (), {"duration": 20.0})(), out=str(tmp_path),
                 ep="EPL15", rx=[], d={"show_plan": dict(plan)}, fps=RN.fps())
    job.look_fix = set(fix)
    with pytest.raises(Stop): EP._render(job)
    seen["after"] = RN._FIX["density"]                                 # RULINGS_U2c 3: "dens" is the density INSIDE the render, "after" once it raised
    return seen

def _line(seen, i): return [e for s_, e in seen["pieces"] if s_.startswith(f"EPL15{i}")]

def _long(monkeypatch, setting, floor=False):
    """A whole offline long production with the look bar on (the start of tests/test_v12_floor.py; its judged floor only when asked)."""
    from tests import test_v12_floor as FLT
    FLT._start_e2e(monkeypatch, setting)
    if not floor: setting("VIEW_FLOOR_ON", "FALSE")
    setting("LOOK_BAR_ON", "TRUE"); setting("VIEWER_SEAT_ON", "TRUE")
    return FLT

def _renders(monkeypatch, c=None):
    """`episode.Job.render_all` counted: each entry (the levers of that render, what was paid during it on the `paid_calls.watch` counter `c`)."""
    from whatifs import episode as EP
    seen = []; real = EP.Job.render_all; c = c if c is not None else {}
    def render_all(self):
        b0 = dict(c); out = real(self)
        seen.append((set(getattr(self, "look_fix", None) or ()), {k: c[k] - b0.get(k, 0) for k in c if c[k] != b0.get(k, 0)})); return out
    monkeypatch.setattr(EP.Job, "render_all", render_all); return seen

def _produce(ep, k=10):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import episode as EP
    r = EP.produce(E2E._slot(k), episode_id=ep)
    rows = [x for x in core.store().rows(LOOK.LOG) if x.get("episode_id") == ep]
    led = {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep and x.get("stage") == "final"}
    return r, rows, led

def test_15_the_long_fixs_three_levers_each_alone_and_a_lever_that_cannot_act_is_no_fix(bar, monkeypatch, tmp_path):
    from whatifs import episode as EP, render as RN
    monkeypatch.setitem(RN._FIX, "density", 1.0)                                         # restored after the test: one render's fix never reaches another test
    bar("OPENING_WINDOW_SEC", "5"); bar("ATMOSPHERE_ON", "TRUE"); bar("ATMOSPHERE_LEVEL", "auto"); bar("PARTICLES_ON", "TRUE")
    src0 = np.full((360, 640, 3), 120, np.uint8)
    def lay_(): return [len(L["x"]) for L in RN.Particles("court", src0, "s", 640, 360, 10, 30).layers]      # built as living.py builds it
    lay0 = lay_()                                                                                         # before any long render
    assert EP._look_lever_acts("light", "EPL15") is True and EP._look_lever_acts("particles", "EPL15") is True and EP._look_lever_acts("framing", "EPL15") is True
    bar("ATMOSPHERE_LEVEL", "2"); assert EP._look_lever_acts("light", "EPL15") is False                                  # a fixed level wins in atmosphere.level_for
    bar("ATMOSPHERE_LEVEL", "auto"); bar("ATMOSPHERE_ON", "FALSE"); assert EP._look_lever_acts("light", "EPL15") is False
    bar("PARTICLES_ON", "FALSE"); assert EP._look_lever_acts("particles", "EPL15") is False and EP._look_lever_acts("grade", "EPL15") is False
    base = _render_levers(monkeypatch, tmp_path, set(), {"intensity": 2})                                                 # look_fix empty: all four as today
    assert base["plan"] == {"intensity": 2} and base["dens"] == 1.0 and _line(base, 1) and _line(base, 1)[0] == "calm", base
    lit = _render_levers(monkeypatch, tmp_path, {"light"}, {"intensity": 2}); assert lit["plan"] == {"intensity": 3} and lit["dens"] == 1.0, lit
    assert _render_levers(monkeypatch, tmp_path, {"light"}, {"intensity": 3})["plan"] == {"intensity": 3}                  # never above 3
    pt = _render_levers(monkeypatch, tmp_path, {"particles"}, {"intensity": 2}); assert pt["dens"] == 1.5 and pt["plan"] == {"intensity": 2}, pt
    assert pt["after"] == 1.0 and base["after"] == 1.0 and lay_() == lay0, (pt["after"], lay0)            # RULINGS_U2c 3: gone when _render raised after its set_fix; a later film is as made
    fr = _render_levers(monkeypatch, tmp_path, {"framing"}, {"intensity": 2})
    assert len(_line(fr, 1)) == len(_line(fr, 0)) and _line(fr, 1)[0] == "high" and fr["plan"] == {"intensity": 2} and fr["dens"] == 1.0, fr["pieces"]
    src = np.full((360, 640, 3), 120, np.uint8)
    def n_(): return sum(len(L["x"]) for L in RN.Particles("court", src, "s", 640, 360, 10, 30).layers)
    RN.set_fix(1.0); n1 = n_(); RN.set_fix(1.5); n15 = n_(); k_ = len(RN.Particles("court", src, "s", 640, 360, 10, 30).layers); RN.set_fix(1.0)
    assert n15 > n1 and abs(n15 - 1.5 * n1) <= k_, (n1, n15)                                                                # 1.5 times the density, each layer rounded
    # RULINGS_U2c 3: the free fix lives for ONE render of its own film, and for every render of it (_render and Job.rerender_times are fixed's)
    def sets(): RN.set_fix(1.5); return "made"
    assert RN.fixed(sets)() == "made" and RN._FIX["density"] == 1.0                                       # gone when the render returns, too
    assert EP._render.__code__ is RN.fixed(sets).__code__ and EP.Job.rerender_times.__code__ is RN.fixed(sets).__code__
    assert EP._render.__wrapped__.__name__ == "_render" and EP.Job.rerender_times.__wrapped__.__name__ == "rerender_times"
    import cv2
    png = str(tmp_path / "rr.png"); cv2.imwrite(png, src0); inside = []
    monkeypatch.setattr(RN, "parallax_segment", lambda img, path, nf, **k: inside.append(RN._FIX["density"]))
    monkeypatch.setattr(RN, "concat", lambda segs, path: path); monkeypatch.setattr(RN, "mux", lambda v, a, path: path)
    for fix_, want in (({"particles"}, 1.5), (set(), 1.0)):                                               # a re-drawn segment: its film's own density, whatever was left before
        job = EP.Job(files={"img": {0: png}, "clips": {}}, shots=[{"type": "still", "prompt": "p0"}], units=[], vo=type("V", (), {"duration": 2.0})(), out=str(tmp_path),
                     ep="EPL15", rx=[], d={"show_plan": {}}, fps=RN.fps())
        job.look_fix = set(fix_); job.overlay = None; job.fixn = 0
        job.segmeta = [{"i": 0, "k": 0, "f0": 0, "nf": 10, "path": str(tmp_path / "rr0.mp4"), "img": png}]
        RN.set_fix(1.0 if fix_ else 1.5); job.rerender_times([0.1])
        assert inside[-1] == want and RN._FIX["density"] == 1.0, (fix_, inside, RN._FIX)

def test_15_a_film_whose_only_missed_point_cannot_act_gets_no_second_render_and_its_second_look_says_none(bar, films, monkeypatch, setting):
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]
    setting("ATMOSPHERE_ON", "TRUE"); setting("ATMOSPHERE_LEVEL", "2")                        # a fixed level: "light" cannot act
    monkeypatch.setattr(LOOK, "fix_of", lambda res: ["light"], raising=False)                 # its only missed point asks for light (look.fix_of itself is half B's)
    said = _judge(monkeypatch, films, "fail", "fail"); ren = _renders(monkeypatch)
    try:
        r, rows, led = _produce(ep)
        assert said == ["fail", "fail"] and len(ren) == 1, (said, ren)                        # NO second render
        assert [LOOK.again([x])["status"] for x in rows] == ["fail", "fail"] and [x["fix"] for x in rows] == ["", "none"], rows
    finally: _gone(ep)

def test_16_a_long_video_below_the_bar_is_rendered_again_once_under_its_levers_and_every_final_check_judges_the_second_master(bar, films, monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import episode as EP, publish as PUB2, release as REL2
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]; c = watch(monkeypatch)
    setting("ATMOSPHERE_ON", "TRUE"); setting("ATMOSPHERE_LEVEL", "auto"); setting("PARTICLES_ON", "TRUE")
    said = _judge(monkeypatch, films, "fail", "pass"); ren = _renders(monkeypatch, c); up = []; real = PUB2.yt_upload
    monkeypatch.setattr(PUB2, "yt_upload", lambda master, *a, **k: (up.append(REL2.sha(master)), real(master, *a, **k))[1])
    try:
        r, rows, led = _produce(ep)
        want = {x for x in LOOK.fix_of(LOOK.again(rows[:1])) if x != "grade" and EP._look_lever_acts(x, ep)}
        assert said == ["fail", "pass"] and want and [f for f, _d in ren] == [set(), want], (said, ren, want)    # twice, the second time under the levers its missed points ask for
        assert ren[1][1] == {}, ren[1][1]                                                                       # nothing was bought again
        assert [LOOK.again([x])["status"] for x in rows] == ["fail", "pass"] and set(rows[1]["fix"].split(",")) == want, rows
        assert led["look_bar"][0] == CON.PASS and r.get("ok"), (led.get("look_bar"), r)
        assert rows[1]["sha"] != rows[0]["sha"] and up == [rows[1]["sha"]], (rows, up)                         # every check after the look read the second master: it is the film uploaded
    finally: _gone(ep)

def test_21_the_cores_planted_guards_the_bar_moves_no_slop_score_and_no_reference_reaches_a_film(bar):
    import inspect, re
    from whatifs import slop as SL, render as RN, shorts2 as SH2, episode as EP, media as MD, anim as AN
    units = [{"i": i, "start": 4.0 * i, "end": 4.0 * (i + 1), "text": f"Line {i}: a kettle boils at a lower heat on a mountain.", "speaker": "DIRECTOR"} for i in range(6)]
    shots = [{"type": "still", "prompt": f"a kitchen on a mountain, shot {i}"} for i in range(6)]
    bar("LOOK_BAR_ON", "TRUE"); on_ = SL.score(units, shots, "EPL21"); bar("LOOK_BAR_ON", "FALSE"); off_ = SL.score(units, shots, "EPL21")
    assert on_ == off_, (on_, off_)
    for mod in (RN, SH2, EP, MD, AN):                                                                           # a source scan: a reference never reaches a film
        src = inspect.getsource(mod)
        assert "LOOK_REFS" not in src and not re.search(r"\b(?:LOOK|look|LK)\.(?:kit|cells)\(", src), mod.__name__

def test_21_a_film_held_by_the_look_bar_was_not_uploaded(bar, films, monkeypatch, setting):
    from whatifs import publish as PUB2
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[2]; up = []; real = PUB2.yt_upload
    monkeypatch.setattr(PUB2, "yt_upload", lambda master, *a, **k: (up.append(master), real(master, *a, **k))[1])
    said = _judge(monkeypatch, films, "fail", "fail")
    try:
        r, rows, led = _produce(ep, 30)
        e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)
        assert said == ["fail", "fail"] and led["look_bar"][0] == CON.FAIL and up == [] and not e.get("yt_id"), (said, led.get("look_bar"), up, e.get("status"))
    finally: _gone(ep)

def test_25_a_later_pass_renders_once_under_the_logged_fix_and_asks_no_session(bar, films, monkeypatch, setting, tmp_path):
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]
    setting("ATMOSPHERE_ON", "TRUE"); setting("ATMOSPHERE_LEVEL", "auto")
    assert LOOK.plain(LOOK.run(None, ep, films["held"], str(tmp_path / ep), "long"))["status"] == "fail"                 # the log: fail, then pass after "light"
    assert LOOK.plain(LOOK.run(None, ep, films["cards"], str(tmp_path / ep), "long", "light"))["status"] == "pass"
    assert LOOK.logged_fix(ep) == ["light"]
    calls = _asked(monkeypatch); ren = _renders(monkeypatch)
    try:
        r, rows, led = _produce(ep)
        looked = [x for x in calls if x["role"] == LOOK.ROLE]
        assert [f for f, _d in ren] == [{"light"}] and looked == [] and len(rows) == 2, (ren, len(looked), rows)   # rendered ONCE, under its logged fix; no session
        assert led["look_bar"][0] == CON.PASS, led.get("look_bar")
    finally: _gone(ep)

def test_26_a_long_video_below_the_bar_twice_pays_no_floor_jury_and_its_card_is_look_hold(bar, films, monkeypatch, setting):
    from tests.paid_calls import watch
    FLT = _long(monkeypatch, setting, floor=True); ep = FLT.OWN_IDS[2]; c = watch(monkeypatch)
    said = _judge(monkeypatch, films, "fail", "fail")
    try:
        r, rows, led = _produce(ep, 30)
        assert said == ["fail", "fail"] and not {k: v for k, v in c.items() if k.startswith("watch:floor_") and v}, (said, dict(c))
        assert [f for f, (s_, _e) in led.items() if s_ == CON.FAIL] == ["look_bar"], led
        kinds = [x.get("kind") for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
        card = next(x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep and x.get("kind") == "look_hold")
        assert "contract_hold" not in kinds and card["default_action"] == "stays held", (kinds, card)
    finally: _gone(ep)

def test_10_the_house_grade_stands_under_the_captions_and_one_source_grades_the_long_video(setting, monkeypatch):
    import inspect
    from whatifs import shorts2 as SH, render as RN, specials as SP
    seen = []; shots = [{"i": 0, "start": 0.0, "end": 2.0}, {"i": 1, "start": 2.0, "end": 3.5}]
    monkeypatch.setattr(SH.subprocess, "run", lambda args, **k: seen.append(args[args.index("-filter_complex") + 1]))
    for g in ("", RN.GRADE): SH._assemble(shots, ["a.mp4", "b.mp4"], "m.wav", "c.ass", "F", "o.mp4", 3.5, grade=g)
    W, H = SP._vsize()
    today = ";".join([f"[{k}:v]setpts={SH.slow_of(s):.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={SH.FPS},tpad=stop_mode=clone:stop_duration=6,"
                      f"trim=0:{float(s['end']) - float(s['start']):.3f},setpts=PTS-STARTPTS,format=yuv420p[v{k}]" for k, s in enumerate(shots)]
                     + ["[v0][v1]concat=n=2:v=1:a=0[body]", "[body]ass=c.ass:fontsdir=F[vout]"])          # today's `make`, built by hand
    assert seen[0] == today, seen[0]                                                                         # no grade: the filter of today, byte for byte
    assert seen[1] == today.replace("[body]ass=", f"[body]{RN.GRADE},ass="), seen[1]                          # the grade UNDER the captions, never over them
    assert 'grade=RN.GRADE if S("SHORT_GRADE_ON", bool) else ""' in inspect.getsource(SH.make)
    setting("GRAIN_LEVEL", "3")
    assert RN._enc_args(640, 360)[1] == "scale=640:360:flags=lanczos,eq=contrast=1.06:saturation=1.08:gamma=0.98,vignette=PI/5,noise=alls=3:allf=t,format=yuv420p"   # no pixel of a long video moves

def test_11_a_short_below_the_bar_is_re_graded_once_for_free_and_looked_at_again(bar, films, monkeypatch):
    from tests.paid_calls import watch
    ep = "SH209912190910"; _setup(bar, monkeypatch); c = watch(monkeypatch)
    said = _judge(monkeypatch, films, "fail", "pass"); free = _regrades(monkeypatch, c)
    try:
        r, rows, led, rec = _whole(ep)
        assert said == ["fail", "pass"] and free == [True], (said, free)                                      # ONE re-grade, nothing bought by it, looked at again
        assert [LOOK.again([x])["status"] for x in rows] == ["fail", "pass"] and [x["fix"] for x in rows] == ["", "grade"], rows
        assert led["short_look"] == (CON.PASS, LOOK.again(rows[-1:])["why"][:380]), led.get("short_look")
        assert r.get("ok") and not str(rec.get("status")).startswith("FILE_HELD"), (r, rec.get("status"))     # handed over
        assert all(led[f][0] == CON.PASS for f in ["short_moving", "short_sound"] + [f for f in led if "loop" in f]), led   # the re-graded file moves, sounds, loops
    finally: _gone(ep)

def test_12_still_below_after_its_free_fix_the_short_is_kept_and_held_and_with_the_arm_on_it_is_not_re_graded(bar, films, monkeypatch):
    eps = ("SH209912190911", "SH209912190912"); _setup(bar, monkeypatch)
    _judge(monkeypatch, films, "fail", "fail", "fail", "fail"); free = _regrades(monkeypatch)
    try:
        r, rows, led, rec = _whole(eps[0], publish=True)
        assert rec.get("status") == "AWAITING_APPROVAL" and [x["fix"] for x in rows] == ["", "grade"] and free == [True], (rec.get("status"), rows, free)      # held: its card waits for his tap
        assert led["short_look"][0] == CON.FAIL and led["short_look"][1].endswith(" - after its free fix"), led["short_look"]
        cards = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "special_review" and x.get("episode_id") == eps[0]]
        assert len(cards) == 1 and "below your look bar" in str(cards[0].get("text")), cards                   # ONE card, the check's own words
        assert "after its free fix" in str(cards[0].get("text")), cards[0].get("text")                      # RULINGS_U2c 2 (b): the card says what was tried
        bar("SHORT_GRADE_ON", "TRUE")                                                                          # the arm: `make` graded it already
        from whatifs import shorts2 as SH2
        held = []; real_hold = SH2._file_hold                                                                   # RULINGS_U2c 2 (b): the gate's own words, kept for the card
        monkeypatch.setattr(SH2, "_file_hold", lambda rec_, gf, publish: held.append(gf) or real_hold(rec_, gf, publish))
        r, rows, led, rec = _whole(eps[1], k=1)
        assert free == [True] and [x["fix"] for x in rows] == ["", "none"], (free, rows)                       # `regrade` NOT called
        assert led["short_look"][0] == CON.FAIL and led["short_look"][1].endswith(" - a second look agreed; no free fix exists for these points"), led["short_look"]
        assert rec.get("status") == "FILE_HELD (short_look)", rec.get("status")
        real_hold({"id": eps[1]}, held[0], True)                                                              # the same words on his card (memo 815: "and the card carries them")
        cards = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "special_review" and x.get("episode_id") == eps[1]]
        assert len(held) == 1 and len(cards) == 1 and NONE_FORM.lstrip(" -") in str(cards[0].get("text")), (held, cards)
    finally: _gone(*eps)

def test_13_l2_fail_then_void_and_a_broken_re_grade_hold_nothing(bar, films, monkeypatch, tmp_path):
    _ladder(bar); ctx = {"short_file": {"path": films["cards"], "units": [], "sound": None}}
    def check(r): st, ev = CON.p_short_look(dict(ctx, look=r)); return st, ev, CON.failed([{"feature": "short_look", "status": st, "evidence": ev}])
    assert LOOK.plain(LOOK.run(None, "EPLOOK13FV", films["held"], str(tmp_path), "short"))["status"] == "fail"
    FK.LOOK_FAULTS["mode"] = "mute"; r = LOOK.plain(LOOK.run(None, "EPLOOK13FV", films["held"], str(tmp_path), "short", "grade")); FK.LOOK_FAULTS["mode"] = ""
    assert r["status"] == "void" and check(r) == (CON.NA, r["why"][:380], []), (r, check(r))                 # fail then void: N/A, handed over
    ep = "SH209912190913"; _setup(bar, monkeypatch); said = _judge(monkeypatch, films, "fail"); _regrades(monkeypatch, broken=True)
    try:
        r, rows, led, rec = _whole(ep)
        assert said == ["fail"] and [x["fix"] for x in rows] == [""], (said, rows)                             # the fix broke: no second session
        assert led["short_look"] == (CON.NA, "below the bar once: no free fix has run, so nothing is held") and not str(rec.get("status")).startswith("FILE_HELD"), (led.get("short_look"), rec.get("status"))
    finally: _gone(ep)

def test_23_a_later_pass_makes_the_short_again_under_its_logged_fix_before_the_look(bar, films, monkeypatch, tmp_path):
    eps = ("SH209912190914", "SH209912190915"); _setup(bar, monkeypatch)
    for ep in eps:                                                                                             # the log of each: fail, then pass after the fix "grade"
        assert LOOK.plain(LOOK.run(None, ep, films["held"], str(tmp_path / ep), "short"))["status"] == "fail"
        assert LOOK.plain(LOOK.run(None, ep, films["cards"], str(tmp_path / ep), "short", "grade"))["status"] == "pass"
    assert LOOK.logged_fix(eps[0]) == ["grade"] and LOOK.logged_fix("SH209912190999") == []
    calls = _asked(monkeypatch); free = _regrades(monkeypatch)
    try:
        r, rows, led, rec = _whole(eps[0])
        looked = [x for x in calls if x["role"] == LOOK.ROLE]
        assert free == [True] and looked == [] and len(rows) == 2 and led["short_look"][0] == CON.PASS, (free, len(looked), rows, led.get("short_look"))   # re-graded ONCE, no session
        _regrades(monkeypatch, broken=True)
        r, rows, led, rec = _whole(eps[1], k=1)
        looked = [x for x in calls if x["role"] == LOOK.ROLE]
        assert looked == [] and len(rows) == 2 and led["short_look"] == (CON.NA, "not judged"), (len(looked), rows, led.get("short_look"))       # no look ...
        assert not str(rec.get("status")).startswith("FILE_HELD"), rec.get("status")                          # ... and not held
    finally: _gone(*eps)

def test_24_never_more_than_two_films_of_a_kind_are_held_for_their_look_in_a_row(bar, films, tmp_path):
    _ladder(bar); ctx = {"short_file": {"path": films["cards"], "units": [], "sound": None}}
    def check(r): st, ev = CON.p_short_look(dict(ctx, look=r)); return st, ev, CON.failed([{"feature": "short_look", "status": st, "evidence": ev}])
    def twice(ep, kind="short"):
        LOOK.run(None, ep, films["held"], str(tmp_path / ep), kind); o = LOOK.run(None, ep, films["held"], str(tmp_path / ep), kind, "grade"); return o, LOOK.plain(o)
    for ep in ("EPL24L1", "EPL24L2"): assert twice(ep, "long")[1]["fix"] == "grade"
    assert not LOOK.held_run("short", "SHL24A")                                                                # two held LONG videos do not spare a Short
    for ep in ("SHL24A", "SHL24B"):
        o, r = twice(ep); assert check(r)[0] == CON.FAIL and check(r)[2] and [m["dedupe_key"] for m in o.memos] == ["look|below|short"], (ep, check(r), o.memos)
    assert LOOK.held_run("short", "SHL24C") and not LOOK.held_run("short", "SHL24A")                          # the film itself is never counted
    o, r = twice("SHL24C")
    assert check(r) == (CON.NA, f"the look bar held 2 films in a row: reported, not held - {r['why']}"[:380], []), check(r)      # reported, handed over
    assert [m["dedupe_key"] for m in o.memos] == ["look|below|short", "look|run|short"] and o.memos[1]["to_depts"] == ["D13"], o.memos
    sent = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "look_run"]
    assert len(sent) == 1 and sent[0].get("episode_id") == "SHL24C", sent                                     # ONE message to him
    bar("LOOK_HOLDS_MAX_RUN", "0"); assert not LOOK.held_run("short", "SHL24D") and check(r)[0] == CON.FAIL, check(r)   # 0 = no bound: never spared
    bar("LOOK_HOLDS_MAX_RUN", "2")
    assert LOOK.plain(LOOK.run(None, "SHL24P", films["cards"], str(tmp_path / "p"), "short"))["status"] == "pass"
    assert not LOOK.held_run("short", "SHL24D")                                                                # a pass between them ...
    o, r = twice("SHL24D"); assert check(r)[0] == CON.FAIL and check(r)[2], check(r)                          # ... and the third is HELD


# ------------------------------------------------------------------ v12 DRAWN-b L3, half B (T-DRAWNb-8b): the long video's card, its void, the sweep
def test_17_a_long_video_still_below_is_held_by_its_own_card_and_his_taps_work(monkeypatch):
    """L3 (R16 (e), (f)): `look.hold_card` sends kind `look_hold` (a HOLD), default "stays held", the three buttons; the card's two second forms, each
    on its own planted result; the kind's handler is the floor's (`_ensure_handlers` loads it): "Drop it" kills the film, "Publish anyway" is the
    contract's waive. (The `_finish` half - a whole long video held by this card - is NEEDS L3a: see TYPED_DRAWN-b-L3b.md.)"""
    from whatifs import notify as NT
    from whatifs.org import floor as FL
    sent = []; monkeypatch.setattr(NT, "send", lambda kind, text, options, **k: sent.append((kind, text, options, k)) or "id")
    ep = "EPLOOK17A"; why = "below your look bar: 3 of 7 look points (70% needed)"
    LOOK.hold_card(ep, "The Moon left", {"status": "fail", "why": why, "fix": "light", "view": "VIEW17"})
    LOOK.hold_card(ep, "The Moon left", {"status": "fail", "why": why, "fix": "none", "view": ""})
    assert [s[0] for s in sent] == ["look_hold", "look_hold"] and NT.klass("look_hold") == NT.HOLD and "look_hold" in NT.HOLD_KINDS
    assert sent[0][1] == ("'The Moon left' is HELD for its look. Beside the videos you chose as your bar, a blind judge found it " + why + ". It was re-rendered "
                          "once for free and looked at again. See its pictures: https://drive.google.com/file/d/VIEW17/view. This judge is a proxy until your own "
                          "verdicts have calibrated it: publish it anyway, or drop it."), sent[0][1]
    assert "A second look agreed; no free fix exists for these points." in sent[1][1] and "re-rendered" not in sent[1][1], sent[1][1]
    for _kind, _text, options, k in sent:
        assert options == [("Publish anyway", f"CONTRACT WAIVE {ep} look_bar"), ("Drop it", f"FLOOR DROP {ep}"), ("Discuss", f"DISCUSS contract {ep}")], options
        assert k == {"tier": "now", "urgent": True, "episode": ep, "default": "stays held", "dedupe_key": f"look|{ep}|hold"}, k
    NT.HANDLERS.pop("look_hold", None); NT._ensure_handlers(); assert NT.HANDLERS.get("look_hold") is FL._answer, NT.HANDLERS.get("look_hold")
    core.store().append("Episodes", [{"episode_id": ep, "status": "FILE_HELD"}])
    FL._answer({"episode_id": ep}, f"FLOOR DROP {ep}")
    assert next(r for r in core.store().rows("Episodes") if r.get("episode_id") == ep).get("kill") == "KILL"                       # "Drop it" kills it
    got = []; monkeypatch.setattr(CON, "_answer", lambda row, choice: got.append(choice) or "waived")
    FL._answer({"episode_id": ep}, f"CONTRACT WAIVE {ep} look_bar"); assert got == [f"CONTRACT WAIVE {ep} look_bar"], got           # "Publish anyway": the contract's waive

def test_18_a_void_look_of_a_long_video_holds_nothing_and_the_check_is_wired(bar):
    """L3: VOID -> NOT HELD - `look_bar` on a void session is N/A with the session's own words and fails nothing (the film goes on to the floor and the
    gate as today); never judged -> N/A "not judged"; the check stands in `FEATURES` right after `viewer_floor` (stage "final"), D13 owns it, its two
    call sites are named in the registry. (The `_finish` half is NEEDS L3a: see TYPED_DRAWN-b-L3b.md.)"""
    from whatifs.org import registry as RG
    void = {"status": "void", "why": "the judge could not be calibrated on this film"}
    st, ev = CON.p_look_bar({"look": void}); assert (st, ev) == (CON.NA, void["why"]) and CON.failed([{"feature": "look_bar", "status": st, "evidence": ev}]) == []
    assert CON.p_look_bar({}) == (CON.NA, "not judged")
    names = [f[0] for f in CON.FEATURES]; f = {x[0]: x for x in CON.FEATURES}
    assert f["look_bar"][1:3] == ("final", CON.p_look_bar) and names.index("look_bar") == names.index("viewer_floor") + 1
    assert RG.CHECK_OWNER["look_bar"] == "D13" and ("whatifs/episode.py", "look") in RG.ENTRY["D13"] and ("whatifs/episode.py", "look_fix") in RG.ENTRY["D6"]

def test_22_l3_the_sweep_also_asks_look_bar_of_every_long_video_and_the_rehearsal_asserts_it(bar):
    """L3 (R16 (a), (b)): `look_of(..., long=True)` asks `look_bar` of the id's own long video - PASS ok and counted, a missing row and any other N/A
    BAD; with its Short asked too, the Short's FAIL still makes the id bad and a void long video beside a judged Short is ok; the rehearsal and produce
    branches of `one` pass `long=True`, the rehearsal asserts the long video's PASS after its "look:" line."""
    import inspect
    from tools import sweep as SW, rehearsal as RH
    def put(ep, feat, *rows): core.store().append("Feature_Ledger", [{"ts": core.iso(), "episode_id": ep, "feature": feat, "status": st, "evidence": ev} for st, ev in rows])
    put("EPLK3A", "look_bar", (CON.PASS, "5 of 7 look points")); ok, w = SW.look_of(core, "EPLK3A", long=True)
    assert ok and w == "the look bar judged: EPLK3A: 5 of 7 look points", w
    ok, w = SW.look_of(core, "EPLK3B", long=True); assert not ok and w.startswith("look_bar missing on EPLK3B"), w                  # a missing row: always BAD
    put("EPLK3C", "look_bar", (CON.NA, "below the bar once: no free fix has run, so nothing is held"))
    ok, w = SW.look_of(core, "EPLK3C", long=True); assert not ok and w.startswith(f"look_bar {CON.NA} on EPLK3C: "), w
    put("EPLK3D", "look_bar", (CON.PASS, "6 of 7")); put("SHLK3D", "short_look", (CON.FAIL, "x"))
    ok, w = SW.look_of(core, "EPLK3D", short="SHLK3D", long=True); assert not ok and w.startswith(f"short_look {CON.FAIL} on SHLK3D: "), w
    put("EPLK3E", "look_bar", (CON.NA, "void by its canary: the judge passed the twin")); put("SHLK3E", "short_look", (CON.PASS, "8 of 8"))
    ok, w = SW.look_of(core, "EPLK3E", short="SHLK3E", long=True)
    assert ok and w == "the look bar judged: SHLK3E: 8 of 8 | void by its canary: EPLK3E: the judge passed the twin", w
    assert SW.summary([{"id": "p", "outcome": "ok", "look": SW.look_of(core, "EPLK3A", long=True)[1]}])["look_judged"] == 1
    src = inspect.getsource(SW.one)
    assert src.count('look_of(core, ep, short="SH" + ep[2:], long=True)') == 1 and src.count('if res.get("ladder") == "climbed" else None, long=True)') == 1 \
        and src.count("long=True") == 2 and 'look_of(core, ep, short=ep)' in src
    r = inspect.getsource(RH.run)
    assert 'look12(core12, epid, long=True)' in r and 'saidb12.startswith("the look bar judged: ")' in r and r.index('print("look:"') < r.index('print("look (long):"')

# ------------------------------------------------------------------ L3 merge (T-DRAWNb-9): test 18's _finish half and test 19's long half (17's _finish half is test 26)
def test_18_a_void_look_of_a_long_video_holds_nothing_and_the_film_goes_on_to_the_floor_and_the_gate(bar, films, monkeypatch, setting):
    from tests.paid_calls import watch
    FLT = _long(monkeypatch, setting, floor=True); ep = FLT.OWN_IDS[0]; c = watch(monkeypatch)
    said = _judge(monkeypatch, films, "void"); ren = _renders(monkeypatch)
    try:
        r, rows, led = _produce(ep)
        assert said == ["void"] and len(ren) == 1, (said, ren)                                                  # one session, no free fix for a void
        assert led["look_bar"][0] == CON.NA, led.get("look_bar")                                                # void -> N/A, never a FAIL
        assert led["viewer_floor"][0] == CON.PASS and c["watch:floor_gemini"] == 2 and c["watch:floor_claude"] == 2, (led.get("viewer_floor"), dict(c))   # on to the floor as today
        kinds = [x.get("kind") for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
        assert "look_hold" not in kinds and r.get("ok"), (kinds, r)                                             # and through the gate: nothing held by the look
    finally: _gone(ep)

def test_19_a_whole_long_video_is_looked_at_once_with_the_bar_on_and_its_money_is_its_line(bar, monkeypatch, setting):
    from tests.test_v12_money import _covered, _summary
    from tests.paid_calls import watch
    from whatifs import costguard as CG
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[3]; c = watch(monkeypatch)
    try:
        r, rows, led = _produce(ep); assert r.get("ok"), r
        assert len(rows) == 1 and rows[0]["kind"] == "long" and LOOK.again(rows)["status"] == "pass", rows                   # ONE session, the fake judge passes it
        assert led["look_bar"] == (CON.PASS, LOOK.again(rows)["why"][:380]), led.get("look_bar")
        L = CG.lines("long")
        assert c["watch:look_claude"] == 1 and _covered({k: n for k, n in c.items() if k.startswith("watch:")}, L) == [], dict(c)
        assert [l["calls"] for l in L if l["key"] == "look"] == [{"watch:look_claude": 2}]                                   # the cost row of the look: its line
        j, _row_ = _summary(ep); assert j["unlisted"] == [] and j["over"] == [], j                                          # costguard.reconcile clean
    finally: _gone(ep)

# ------------------------------------------------------------------ RULINGS_U2c 2: the Short's hold card carries the END of a check's words
NONE_FORM = " - a second look agreed; no free fix exists for these points"

def test_the_hold_card_keeps_the_end_of_a_checks_words(monkeypatch):
    from whatifs import shorts2 as SH2, notify as NT
    x = "".join(chr(97 + i % 26) for i in range(150)); assert SH2._ev(x) == x                                       # whole when it fits
    y = "".join(chr(65 + i % 26) for i in range(380)); e = SH2._ev(y)
    assert len(e) <= 150 and e.startswith(y[:60]) and " ... " in e and e.endswith(y[-60:]), e                      # its start and its END
    sent = []; monkeypatch.setattr(NT, "send", lambda kind, text, *a, **k: sent.append((kind, text)))
    gf = {"ok": False, "failed": [("short_moving", "m" * 200), ("short_sound", "s" * 200), ("short_look", "w" * 300 + NONE_FORM)]}
    SH2._file_hold({"id": "SHX9", "file": "drive:f9"}, gf, True)                                                    # three checks with their names: 493 characters
    assert [k for k, _ in sent] == ["special_review"] and NONE_FORM.lstrip(" -") in sent[0][1], sent                # ONE card; short_look is the LAST, its end kept

def test_the_look_bar_keeps_its_form_whole_when_the_why_is_long(monkeypatch):
    w = "below your look bar: " + "q" * 379                                                                         # a why of 400 characters
    monkeypatch.setattr(LOOK, "on", lambda: True); monkeypatch.setattr(LOOK, "held_run", lambda kind, ep: False)
    monkeypatch.setattr(LOOK, "again", lambda rows: {"status": "fail", "why": w})
    for fx, form in (("grade", " - after its free fix"), ("none", NONE_FORM)):
        st, ev = CON._look({"look": {"status": "fail", "why": w, "fix": fx, "row": {"kind": "short", "episode_id": "SHX8"}}})
        assert st == CON.FAIL and len(ev) <= 380 and ev.endswith(form) and ev.startswith("below your look bar: "), (fx, st, len(ev), ev[-80:])   # the form is never cut; why gives way

# ------------------------------------------------------------------ 20: one accent (step L4, memo 3.4; miss 279's house kit)
def test_20_the_shorts_accent_is_the_kits_its_cover_is_drawn_in_it_and_the_source_holds_no_other(monkeypatch, tmp_path):
    import inspect
    from PIL import ImageFont
    from whatifs import shorts2 as SH, drawn as DRAWN, specials as SP, media as MD
    monkeypatch.setattr(MD, "font", lambda size, bold=True: ImageFont.load_default(size=size))         # a face at the cover's own size: the repo carries no font file
    r_, g_, b_ = DRAWN.PALETTE["b"]
    assert SH._accent() == ((r_, g_, b_), "&H00%02X%02X%02X" % (b_, g_, r_)), SH._accent()          # the kit's amber; the ASS colour in its BGR order
    src = inspect.getsource(SH)
    assert "D7FF" not in src and "(255, 214, 0)" not in src                                           # no second accent typed anywhere in the Short's code
    fr = str(tmp_path / "f0.png"); Image.new("RGB", (540, 960), (40, 40, 40)).save(fr)
    out = SH.cover(fr, "What if the Moon left tonight?", str(tmp_path / "cover.jpg"))
    im = Image.open(out); a = np.asarray(im.convert("RGB"), np.int32).reshape(-1, 3)
    def near(c): return int(np.sum(np.max(np.abs(a - np.asarray(c, np.int32)), axis=1) <= 20))
    assert im.size == tuple(SP._vsize()) and near(DRAWN.PALETTE["b"]) > 200 and near((255, 214, 0)) == 0, (im.size, near(DRAWN.PALETTE["b"]), near((255, 214, 0)))

def test_20_the_captions_of_a_made_short_light_the_spoken_word_and_the_promise_in_the_kits_accent(bar, monkeypatch):
    from whatifs import shorts2 as SH, drawn as DRAWN
    ep = "SH209912190920"; _setup(bar, monkeypatch)
    real = SH._ass; made = []
    monkeypatch.setattr(SH, "_ass", lambda *a, **k: made.append(real(*a, **k)) or made[-1])          # the path `make` wrote its captions to
    r_, g_, b_ = DRAWN.PALETTE["b"]; acc = "&H00%02X%02X%02X" % (b_, g_, r_)
    try:
        r, rows, led, rec = _whole(ep)
        assert r.get("ok") and len(made) == 1, (r, made)
        with open(made[0], encoding="utf-8") as f: cap = f.read()
        st = {x.split(",")[0]: x.split(",") for x in cap.splitlines() if x.startswith("Style: ")}
        assert st["Style: Cap"][4] == acc and st["Style: Hook"][3] == acc, st                         # the lit word's colour and the promise text's
        lit = [x for x in cap.splitlines() if x.startswith("Dialogue: 0,")]
        assert lit and all(("{\\c" + acc + "&}") in x for x in lit), lit[:3]                         # every caption line lights its spoken word in the accent
        assert "D7FF" not in cap, cap[:400]
    finally: _gone(ep)


# ------------------------------------------------------------------ CR-DRAWN-b round 1: findings 1 (c), 3 to 7 (each rule both ways)
def test_15c_a_restyled_cutaway_keeps_its_films_density_and_no_density_outlives_a_render(bar, monkeypatch, tmp_path):
    """CR-DRAWN-b 1: `fixed` wraps `_render` (and `rerender_times`), never `_restyle_piece` - a restyle in the middle of a fixed render keeps the film's
    density; what the render set is gone once it ended, so a later film is drawn as made."""
    from whatifs import episode as EP, render as RN
    monkeypatch.setitem(RN._FIX, "density", 1.0)
    src0 = np.full((360, 640, 3), 120, np.uint8)
    def lay_(): return [len(L["x"]) for L in RN.Particles("court", src0, "s", 640, 360, 10, 30).layers]
    lay0 = lay_()
    RN.set_fix(1.5)
    EP._restyle_piece("EPL15C", str(tmp_path), 0, 0, "DIRECTOR", {"text": "Really? Prove it."}, 0.0, 10, str(tmp_path / "p.mp4"), None, None, 0, None)
    assert RN._FIX["density"] == 1.5, RN._FIX                                   # the restyle arm resets nothing in the middle of a fixed render
    assert not hasattr(EP._restyle_piece, "__wrapped__") and EP._render.__wrapped__.__name__ == "_render"
    pt = _render_levers(monkeypatch, tmp_path, {"particles"}, {"intensity": 2})
    assert pt["dens"] == 1.5 and pt["after"] == 1.0 and lay_() == lay0, (pt["dens"], pt["after"], lay0)


def test_cr3_a_void_long_look_keeps_no_private_sheet_whatever_its_road(bar, films, monkeypatch, tmp_path):
    """CR-DRAWN-b 3: the long video's private sheet is deleted on EVERY void - a session that returns void, and one that raises after the upload; a valid
    session keeps it."""
    up, gone = [], []; real = PUB.drive_upload
    def upload(p, name, **k): r = real(p, name, **k); up.append(r[0]); return r
    monkeypatch.setattr(PUB, "drive_upload", upload); monkeypatch.setattr(PUB, "drive_delete", lambda fid: gone.append(fid))
    r = LOOK.plain(LOOK.run(None, "EPLCR3P", films["cards"], str(tmp_path / "p"), "long"))
    assert r["status"] == "pass" and len(up) == 1 and gone == [], (r, up, gone)
    FK.LOOK_FAULTS["mode"] = "mute"
    r = LOOK.plain(LOOK.run(None, "EPLCR3V", films["cards"], str(tmp_path / "v"), "long"))
    FK.LOOK_FAULTS["mode"] = ""
    assert r["status"] == "void" and len(up) == 2 and gone == [up[1]], (r, up, gone)
    def boom(*a, **k): raise RuntimeError("the log could not be written")
    monkeypatch.setattr(LOOK, "session", boom)
    r = LOOK.plain(LOOK.run(None, "EPLCR3R", films["cards"], str(tmp_path / "r"), "long"))
    assert r["status"] == "void" and r["why"] == "the look bar could not run: RuntimeError" and len(up) == 3 and gone == [up[1], up[2]], (r, up, gone)


def test_cr3b_a_failed_delete_of_a_void_sessions_sheet_is_a_warn_never_a_change_of_result(bar, films, monkeypatch, tmp_path):
    """CODEREVIEW_DRAWN-b_2 finding 3: the void session's private sheet cannot be deleted (a Drive error) -> `LOOK.run` does not raise, the result is
    still the session's own void (not "the look bar could not run"), and a WARN says the sheet "was not deleted"."""
    warns, log_ = [], LOOK.log
    def gone(fid): raise RuntimeError("planted: Drive refused the delete")
    monkeypatch.setattr(PUB, "drive_delete", gone)
    monkeypatch.setattr(LOOK, "log", lambda m, *a, **k: (warns.append(m) if "WARN" in a else None, log_(m, *a, **k))[1])
    FK.LOOK_FAULTS["mode"] = "mute"
    try: r = LOOK.plain(LOOK.run(None, "EPLCR3D", films["cards"], str(tmp_path / "d"), "long"))
    finally: FK.LOOK_FAULTS["mode"] = ""
    assert r["status"] == "void" and not r["why"].startswith("the look bar could not run"), r
    assert any("was not deleted" in w for w in warns), warns


def test_cr4_a_kit_longer_than_the_letters_is_cut_to_what_a_session_can_name(bar, films, tmp_path):
    """CR-DRAWN-b 4: N, Z and C take three of the eight letters - LOOK_REFS_MAX 6 with six filed sheets gives a counted session beside five of them."""
    specs = []
    for n in range(6):
        f = _sheet(tmp_path, f"s{n}")
        specs.append({"name": f"s{n}", "file": PUB.drive_upload(f, f"look_ref_s{n}.jpg", public=False)[0], "sha": REL.sha(f), "keys": ["frame", "light"], "grid": [4, 3], "made": "d"})
    bar("LOOK_REFS", json.dumps(specs)); bar("LOOK_REFS_MAX", "6")
    refs, why = LOOK.kit(str(tmp_path / "k")); assert why == "" and [x["name"] for x in refs] == ["s0", "s1", "s2", "s3", "s4"], (why, refs)
    r = LOOK.plain(LOOK.run(None, "EPLCR4", films["cards"], str(tmp_path / "o"), "short"))
    assert r["status"] == "pass" and r["refs"] == 5, r


def test_cr5_the_free_fixs_levers_are_the_memos_table(bar):
    """CR-DRAWN-b 5: `fix_of` against the L3 table written out (DESIGN_DRAWN-b 3.3's RUBRIC) - each point alone, the whole miss, the points with no lever."""
    one = {"frame": ["framing"], "light": ["light"], "colour": ["grade"], "alive": ["particles"], "depth": ["framing"], "same": [], "system": [], "caption": []}
    assert {k: LOOK.fix_of({"missed": [k]}) for k in one} == one
    assert LOOK.fix_of({"missed": list(one)}) == ["framing", "grade", "light", "particles"]
    assert LOOK.fix_of({"missed": ["same", "system", "caption"]}) == [] and LOOK.fix_of({}) == [] and LOOK.fix_of(None) == []


def test_cr6_the_months_look_money_closes_on_look_claudes_own_rows(bar, films, tmp_path):
    """CR-DRAWN-b 6: the cap above 0 - look_claude's own rows at the month's cap close it; just below it, or the same rupees on another role, do not."""
    from whatifs import governor as G
    bar("LOOK_CAP_PER_FILM_INR", "100"); bar("SHORTS_PER_MONTH", "3"); cap = 100.0 * (G.max_long_videos() + 3)
    def plant(role, inr): core.store().append("Cost_Log", [{"ts": core.iso(), "role": role, "item": "planted", "inr": inr, "basis": "actual"}])
    def spent(): core.flush_costs(); return G.month_spend_of(["look_claude"])
    def go(ep): return LOOK.plain(LOOK.run(None, ep, films["cards"], str(tmp_path / ep), "short"))
    assert cap > 0 and LOOK.month_cap() == cap
    plant("floor_claude", cap); r = go("EPLCR6A"); assert r["status"] == "pass", r                    # another role's rupees are not the look's
    plant("look_claude", cap - spent() - 1); r = go("EPLCR6B"); assert r["status"] == "pass", r       # Rs 1 below the cap: it runs
    plant("look_claude", cap - spent() + 0.25); r = go("EPLCR6C")
    assert r["status"] == "void" and r["why"] == f"the month's look money is spent (Rs {cap:.0f} of Rs {cap:.0f})", (r, cap)


def test_cr7_a_valid_session_closes_the_void_report_and_only_a_pass_of_its_kind_ends_a_run_of_holds(bar, films, tmp_path):
    """CR-DRAWN-b 7: an open "look|void" memo is closed repair_verified by the next valid session (a fail too); "look|run|<kind>" only by a pass of
    that kind - a fail, or a pass of the other kind, leaves it open."""
    from whatifs.org import memos as MEM
    def go(ep, film, kind="short"): return LOOK.plain(LOOK.run(None, ep, films[film], str(tmp_path / ep), kind))
    FK.LOOK_FAULTS["mode"] = "mute"; o = LOOK.run(None, "EPLCR7V", films["cards"], str(tmp_path / "v"), "short"); FK.LOOK_FAULTS["mode"] = ""
    v = MEM.write(o.memos[0])
    run_ = MEM.write(dict(o.memos[0], subject="The look bar held films in a row: this one is reported, not held", dedupe_key="look|run|short"))
    assert MEM.get(v["id"])["status"] == "open" and MEM.get(run_["id"])["status"] == "open"
    assert go("EPLCR7F", "held")["status"] == "fail"
    c = MEM.get(v["id"]); assert c["status"] == "resolved" and c["resolution"]["kind"] == "repair_verified" and c["resolution"]["ref"].startswith("L-"), c
    assert MEM.get(run_["id"])["status"] == "open", MEM.get(run_["id"])                                 # a fail never ends a run of holds
    assert go("EPLCR7L", "cards", "long")["status"] == "pass" and MEM.get(run_["id"])["status"] == "open"  # nor a pass of the other kind
    assert go("EPLCR7P", "cards")["status"] == "pass"
    c = MEM.get(run_["id"]); assert c["status"] == "resolved" and c["resolution"]["kind"] == "repair_verified", c


def test_a_lost_second_look_after_its_free_fix_says_the_fix_ran_and_keeps_its_levers(bar, films, monkeypatch, setting):
    """RULINGS_U2k 3 (b) (CODEREVIEW_DRAWN-b_1 finding 8): the free fix was rendered (the published master IS the fixed film) and the second look
    raised -> the levers stay the fix's, the look's result is void with true words, `_look` holds nothing (N/A) and never says "no free fix has run".
    Leg (a) (the fix render raising) is RULINGS_U3d 8: the test below."""
    from whatifs import episode as EP
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]
    setting("ATMOSPHERE_ON", "TRUE"); setting("ATMOSPHERE_LEVEL", "auto"); setting("PARTICLES_ON", "TRUE")
    said = _judge(monkeypatch, films, "fail"); ren = _renders(monkeypatch); jobs, looks = [], []; ra_, run_ = EP.Job.render_all, LOOK.run
    monkeypatch.setattr(EP.Job, "render_all", lambda self: (jobs.append(self), ra_(self))[1])
    def run(*a, **k):
        looks.append(k.get("fixed"))
        if len(looks) == 2: raise RuntimeError("planted: the second look broke")
        return run_(*a, **k)
    monkeypatch.setattr(LOOK, "run", run)
    try:
        r, rows, led = _produce(ep)
        want = {x for x in LOOK.fix_of(LOOK.again(rows[:1])) if x != "grade" and EP._look_lever_acts(x, ep)}
        assert said == ["fail"] and "particles" in want and [f for f, _d in ren] == [set(), want], (said, ren, want)    # the fix WAS rendered, under its levers
        assert len(looks) == 2 and looks[0] is None and set(looks[1].split(",")) == want, looks                      # the second look was asked and broke
        assert len(rows) == 1 and LOOK.again(rows)["status"] == "fail", rows                                            # one session: the first look's fail
        assert jobs and jobs[-1].look_fix == want, (jobs[-1].look_fix if jobs else None, want)                          # the levers stay: true of the master
        st_, ev_ = led["look_bar"]
        assert st_ == CON.NA and "was rendered and is the film" in ev_ and "no free fix has run" not in ev_, led["look_bar"]
        assert r.get("ok"), r                                                                                           # nothing is held
    finally: _gone(ep)


def test_a_failed_fix_render_makes_the_first_film_again_under_its_levers(bar, films, monkeypatch, setting):
    """RULINGS_U3d 8 (RULINGS_U2k 3 (a)): the free fix's render raises -> the levers go back and the FIRST film is made again by the same call (local
    ffmpeg, no paid call), so the film published is the one its record names; the look's result stays the first fail and `_look` says "no free fix has
    run" - true. A later `rerender_times` (the drawn audit), if one runs, re-draws under the first film's levers (set_fix 1.0)."""
    from whatifs import episode as EP
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]
    setting("ATMOSPHERE_ON", "TRUE"); setting("ATMOSPHERE_LEVEL", "auto"); setting("PARTICLES_ON", "TRUE")
    said = _judge(monkeypatch, films, "fail"); jobs, ren, rt, warns = [], [], [], []; ra_, rt_, log_ = EP.Job.render_all, EP.Job.rerender_times, EP.log
    def render_all(self):
        jobs.append(self); ren.append(set(getattr(self, "look_fix", None) or ()))
        if len(ren) == 2: raise RuntimeError("planted: the fix render broke")
        return ra_(self)
    monkeypatch.setattr(EP.Job, "render_all", render_all)
    monkeypatch.setattr(EP.Job, "rerender_times", lambda self, *a, **k: (rt.append(set(getattr(self, "look_fix", None) or ())), rt_(self, *a, **k))[1])
    monkeypatch.setattr(EP, "log", lambda m, *a, **k: (warns.append(m) if "WARN" in a else None, log_(m, *a, **k))[1])
    try:
        r, rows, led = _produce(ep)
        want = {x for x in LOOK.fix_of(LOOK.again(rows[:1])) if x != "grade" and EP._look_lever_acts(x, ep)}
        assert said == ["fail"] and "particles" in want and ren == [set(), want, set()], (said, ren, want, rt)        # the first film made again, under its own levers
        assert jobs[-1].look_fix == set() and all(f == set() for f in rt), (jobs[-1].look_fix, rt)                    # the levers went back
        assert any("the first film is rendered again under its own levers" in w for w in warns), warns
        assert any(w.startswith(f"the first film of {ep} was rendered again under its own levers") for w in warns), warns
        assert len(rows) == 1 and LOOK.again(rows)["status"] == "fail", rows                                            # one session: the first look's fail
        st_, ev_ = led["look_bar"]
        assert st_ == CON.NA and "below the bar once: no free fix has run, so nothing is held" in ev_, led["look_bar"]
        assert r.get("ok"), r                                                                                           # the film published
    finally: _gone(ep)


def test_a_lost_second_look_with_no_lever_that_can_act_says_no_fix_ran_and_renders_once(bar, films, monkeypatch, setting):
    """CODEREVIEW_DRAWN-b_2 finding 2 (the `made_` False road, no lever): the first look fails, no lever of its misses can act on this film (fx_ empty:
    the "none" confirmation) and the second look raises -> one render, the look's result the first fail, `_look` N/A "no free fix has run" and never
    "was rendered", the WARN "the film stays as rendered" (nothing was re-rendered)."""
    from whatifs import episode as EP
    FLT = _long(monkeypatch, setting); ep = FLT.OWN_IDS[1]
    said = _judge(monkeypatch, films, "fail"); ren = _renders(monkeypatch); looks, warns = [], []; run_, log_ = LOOK.run, EP.log
    monkeypatch.setattr(EP, "_look_lever_acts", lambda x, ep_: False)                                                   # no lever can act on this film
    def run(*a, **k):
        looks.append(k.get("fixed"))
        if len(looks) == 2: raise RuntimeError("planted: the second look broke")
        return run_(*a, **k)
    monkeypatch.setattr(LOOK, "run", run)
    monkeypatch.setattr(EP, "log", lambda m, *a, **k: (warns.append(m) if "WARN" in a else None, log_(m, *a, **k))[1])
    try:
        r, rows, led = _produce(ep)
        assert said == ["fail"] and [f for f, _d in ren] == [set()] and looks == [None, "none"], (said, ren, looks)   # one render; the confirmation asked and broke
        assert len(rows) == 1 and LOOK.again(rows)["status"] == "fail", rows
        st_, ev_ = led["look_bar"]
        assert st_ == CON.NA and "below the bar once: no free fix has run, so nothing is held" in ev_ and "was rendered" not in ev_, led["look_bar"]
        assert not any("was rendered again under its own levers" in w for w in warns), warns
        assert any("the film stays as rendered" in w for w in warns) and not any("rendered again" in w or "fixed film stands" in w for w in warns), warns
        assert r.get("ok"), r
    finally: _gone(ep)
