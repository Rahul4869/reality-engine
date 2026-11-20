"""Episode-id sweep: runs the whole fake pipeline once per FIXED episode id (the fake pipeline is seeded by the id) and writes one RESULT line per id; every hold, crash or warning class it shows is a fault to trace. See docs/CURRENT/SYSTEM.md."""
import argparse, datetime as dt, json, os, re, shutil, subprocess, sys, tempfile, time, traceback
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KEYS = ("SHEET_ID", "G_REFRESH", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY")
TEST_SETTINGS = {"CREATIVE_REVIEW_FIRST_N": "0", "V11_FLIPS_DONE": "test", "DEEP_TRIAL_ON": "FALSE"}      # the same three cells tests/conftest.py sets: direct scheduling, no one-time moves, no monthly Deep Trial
START = dt.datetime(2099, 1, 1, 9, 0)          # future-dated on purpose: the organisation's checks judge an episode made after ORG_SINCE
STEP = dt.timedelta(days=1, hours=7, minutes=13)      # every part of the id (month, day, hour, minute) moves from one id to the next
TIMEOUT_S = 1500

def fixed_ids(n, offset=0):
    """The same n ids on every machine and every day: EP2099MMDDHHMM."""
    return ["EP" + (START + (offset + k) * STEP).strftime("%Y%m%d%H%M") for k in range(n)]

def inside(path, root):
    try: return os.path.commonpath([os.path.abspath(path), os.path.abspath(root)]) == os.path.abspath(root)
    except ValueError: return False          # another drive

# v12 V2c: what the Shorts of the sweep are about (mode "short"): everyday things, names, numbers and expert words, so that many different Shorts meet the seat
SHORT_PREMISES = ("What if the Moon left tonight?", "What if gravity doubled for one hour?", "What if your shadow arrived one second late?", "What if the Sun went out?",
                  "What if photosynthesis stopped at noon?", "What if two million bees moved into your street?", "What if every mirror showed tomorrow?",
                  "What if you could hear electromagnetic waves?", "What if rain fell upward for an hour?", "What if your heartbeat set the speed of time?",
                  "What if the oceans turned to glass?", "What if nobody could lie on Tuesdays?", "What if the neutrino in your coffee had weight?",
                  "What if Mars swapped places with the Moon?", "What if you forgot the colour blue?", "What if sound travelled slower than you walk?",
                  "What if your house grew one room every night?", "What if 99 percent of your atoms took a day off?", "What if the wind kept every word you said?",
                  "What if you could only move when nobody watched?", "What if the thermodynamics of your kitchen ran backwards?", "What if stars were close enough to touch?",
                  "What if you woke up with a third arm?", "What if ice was warmer than fire?")

def warn_class(msg):
    """One class per kind of warning: numbers, ids and quoted detail are folded away so that 40 episodes give a short list."""
    m = re.sub(r"EP\d{6,}", "EP#", str(msg)); m = re.sub(r"'[^']{0,80}'|\"[^\"]{0,80}\"", "'..'", m); m = re.sub(r"\d+(\.\d+)?", "#", m)
    return re.sub(r"\s+", " ", m).strip()[:90]

def climb(core, ep):
    """v12 V2c-b: walk the ladder for one id - a Short about one of the sweep's premises is made a week ago and posted, and its numbers are read (the
    offline YouTube is as late as the real one), so that the long video of this id finds a Short to promote. False = the ladder is off."""
    from whatifs import shorts2 as SH, brain as BR, ladder as LAD
    if not LAD.on(): return False
    h = int(__import__("hashlib").sha1(ep.encode()).hexdigest(), 16)
    core.store().append("Premise_Bench", [{"bench_id": f"SW{i}", "premise": SHORT_PREMISES[(h + i * 5) % len(SHORT_PREMISES)], "headline": "", "family": "", "ptype": "collective",
                                           "status": "READY", "claude_score": 9.6 - i / 10, "gemini_score": 9.4 - i / 10, "combined": 9.5 - i / 10, "added": core.iso()} for i in range(3)])
    core.set_setting("SHORTS_REVIEW_FIRST_N", "0")
    r = SH.run(force=True, publish=True, now=core.now_utc() - dt.timedelta(days=7), episode_id="SH" + ep[2:])
    if not r.get("ok"): raise AssertionError("the Short of this id was not made: " + json.dumps({k: v for k, v in r.items() if k != "script"}, default=str)[:240])
    BR.ingest_shorts()
    return True

def opening_of(core, ep):
    """v12 V2c-b2b: (ok, words) - did the long video of a climbed id open on its Short's footage? Both checks must have PASSED: 'not applicable' on an
    id that climbed the ladder would mean the new path was not walked."""
    led = {r.get("feature"): r for r in core.store().rows("Feature_Ledger") if r.get("episode_id") == ep and r.get("feature") in ("opening_footage", "opening_shown")}
    bad = [f"{k} {(led.get(k) or {}).get('status') or 'missing'}: {str((led.get(k) or {}).get('evidence') or '')[:120]}" for k in ("opening_footage", "opening_shown") if (led.get(k) or {}).get("status") != "PASS"]
    return (not bad), ("; ".join(bad) if bad else str(led["opening_shown"].get("evidence"))[:110])

def release_of(core, ep, r):
    """v12 V2c-b2b: (ok, words) - the long video of this id made NO cut-down reel and its release is ONE step. The slot is moved into the past, the
    tick must name its release, the release must end at LIVE, and the next tick must name no release; no reel file, cover or plan was made, nothing
    is on the episode's reel cells, and every short video that went out is a standalone Short with a record on tab Release_Sheet."""
    from whatifs import manage as MG
    st = core.store(); out = os.path.dirname(str(r.get("master") or "")); bad = []
    junk = sorted(f for f in os.listdir(out) if re.match(r"(reel\d|cover\d|r\d_|clean\d)", f))
    if junk or "reels" in r: bad.append("cut-down files were made: " + ", ".join(junk[:4] or ["a reel on the result"]))
    try: rel = json.load(open(os.path.join(out, "release.json")))
    except (OSError, ValueError): rel = None
    if rel is None or "reels" in rel: bad.append("the release record is missing or still lists reels")
    row = next(x for x in st.rows("Episodes") if x.get("episode_id") == ep)
    try: dj = json.loads(row.get("draw_json") or "{}") if isinstance(row.get("draw_json"), str) else (row.get("draw_json") or {})
    except ValueError: dj = {}
    if "reel_style" in dj or "reel_formats" in dj or "reel" in (dj.get("strategies") or {}): bad.append("the draw still carries a reel strategy")
    st.update("Episodes", "episode_id", ep, {"slot_et": (core.now_utc() - dt.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")})
    a = MG.tick()
    if a.get("action") != "release1" or a.get("episode") != ep: bad.append(f"the tick did not name the long video's release: {json.dumps(a)[:120]}")
    else:
        MG.release(ep, "release1"); row = next(x for x in st.rows("Episodes") if x.get("episode_id") == ep)
        if row.get("status") != "LIVE": bad.append(f"the release did not end at LIVE in one step (status {row.get('status')})")
        a2 = MG.tick()
        if str(a2.get("action")).startswith("release"): bad.append(f"a second release was named: {json.dumps(a2)[:120]}")
    if any(str(row.get(k) or "").strip() for k in ("reel1_yt", "reel2_yt", "reel3_yt", "reel4_yt", "ig1", "ig2", "fb1", "fb2")): bad.append("a cut-down reel is on the episode's row")
    kinds = sorted({str(x.get("kind")) for x in st.rows("Release_Sheet")}) if "Release_Sheet" in core.TABS else []
    if [k for k in kinds if k != "short"]: bad.append(f"a short video went out that is not a standalone Short: {kinds}")
    return (not bad), ("; ".join(bad) if bad else "no cut-down made or uploaded; released in one step" + (f"; short videos out: {len({x.get('id') for x in st.rows('Release_Sheet')})} standalone Short(s)" if kinds else ""))

def money_of(core, ids):
    """v12 V2d: (ok, words) - THE SWEEP WALKS THE MONEY. For every id made in this run (a long video and the Short it climbed from; a Short and the one
    before it) the cost model's summary row must exist on tab Cost_Log and say: no picture or clip was paid that the estimate has no line for, and no
    counted line (the seconds of hero clip, the start pictures, the key art) was exceeded."""
    rows = {r.get("episode_id"): r for r in core.store().rows("Cost_Log") if r.get("item") == "cost_lines_summary"}; bad = []; said = []
    for i in ids:
        r = rows.get(i)
        if not r: bad.append(f"{i}: no estimate was set against what was paid"); continue
        try: kind, _, body = str(r.get("role") or "").partition(": "); j = json.loads(body)
        except ValueError: bad.append(f"{i}: the summary row cannot be read"); continue
        if j.get("unlisted"): bad.append(f"{i}: paid with no line in the estimate: {', '.join(j['unlisted'])}")
        if j.get("over"): bad.append(f"{i}: more paid than estimated: {'; '.join(j['over'])}")
        hero = (j.get("paid") or {}).get("hero_clip", 0); said.append(f"{i} ({kind}): {hero:g} of {(j.get('lines') or {}).get('hero_clip', 0):g} estimated seconds of hero clip, Rs {float(r.get('est_inr') or 0):.0f} estimated")
    return (not bad), ("; ".join(bad) if bad else "every paid picture and clip had its line: " + "; ".join(said))

def drawn_of(core, ep):
    """v12 DRAWN: (ok, words) - THE SWEEP WALKS THE DRAWN SCENES. A long video's two checks must BOTH have PASSED (drawn_plan on the shot list,
    drawn_shown on the render's record and the master) or BOTH say "not applicable: this video is not in the drawn arm"; a missing row, any other
    'not applicable' or a FAIL makes the id bad. Both good cases begin "the drawn arm held:"."""
    led = {}
    for r in core.store().rows("Feature_Ledger"):
        if r.get("episode_id") == ep and r.get("feature") in ("drawn_plan", "drawn_shown"): led[r["feature"]] = r
    p, s = led.get("drawn_plan") or {}, led.get("drawn_shown") or {}; na = "not applicable: this video is not in the drawn arm"
    if p.get("status") == "N/A" and s.get("status") == "N/A" and str(p.get("evidence")).startswith(na) and str(s.get("evidence")).startswith(na):
        return True, "the drawn arm held: this video is not in the drawn arm"
    if p.get("status") == "PASS" and s.get("status") == "PASS":
        return True, "the drawn arm held: " + str(s.get("evidence") or "").replace("the drawn arm held: ", "", 1)[:240] + " | plan: " + str(p.get("evidence") or "").replace("the drawn arm held: ", "", 1)[:160]
    return False, f"drawn_plan {p.get('status') or 'missing'}: {str(p.get('evidence') or '')[:140]}; drawn_shown {s.get('status') or 'missing'}: {str(s.get('evidence') or '')[:140]}"


def _drew(words): m = re.search(r"the drawn arm held: (\d+) scene\(s\) drawn", str(words or "")); return bool(m and int(m.group(1)) >= 1)


def motion_of(core, ep, shorts=()):
    """v12 V2d-b: (ok, words) - THE SWEEP WALKS THE LADDER'S RULES. The long video of this id (None = an id of Shorts only) must have PASSED the checks
    that measure its finished film - moving_share (the share that really moves; the seconds of clip it paid for found again), stock_share (real
    footage under its rules) and living_characters (drawn or absent) - and every Short named must have PASSED the gate of its finished file
    (short_moving, short_sound). 'Not applicable' or a missing row is a failure here: it would mean the new path was not walked."""
    led = {}
    for r in core.store().rows("Feature_Ledger"): led[(r.get("episode_id"), r.get("feature"))] = r
    want = ([(ep, k) for k in ("moving_share", "stock_share", "living_characters")] if ep else []) + [(s, k) for s in shorts for k in ("short_moving", "short_sound")]
    bad = [f"{i} {k} {(led.get((i, k)) or {}).get('status') or 'missing'}: {str((led.get((i, k)) or {}).get('evidence') or '')[:140]}" for i, k in want if (led.get((i, k)) or {}).get("status") != "PASS"]
    if bad: return False, "; ".join(bad)
    said = ([str(led[(ep, "moving_share")].get("evidence"))[:300], str(led[(ep, "stock_share")].get("evidence"))[:90]] if ep else []) + [f"{len(list(shorts))} Short(s): every half second of the file moves, sound from the first frame"]
    return True, "the ladder's rules held: " + " | ".join(said)

def inside_of(core, ep):
    """v12 V2b: (ok, words) - THE SWEEP WALKS THE INSIDE OF THE FORMAT. The long video of this id must have PASSED viewer_inside and format_ending - a trial
    only may say format_ending N/A 'is a trial' (v12 V1c, the audit's F3: its words then say what the trial ends on, and the line prints that clause) - and
    camera_path and camera_shown in a format whose camera travels (F1, F3) - a trial only may say N/A 'cuts between its pictures'. A missing row or any
    other 'not applicable' is a failure here: it would mean the new path was not walked."""
    from whatifs import formats as FMT, contract as CON
    st = core.store(); led = {}
    for r in st.rows("Feature_Ledger"):
        if r.get("episode_id") == ep: led[r.get("feature")] = r                      # the latest verdict per check
    row = next((r for r in st.rows("Episodes") if r.get("episode_id") == ep), None) or {}
    try: dj = json.loads(row.get("draw_json") or "{}") if isinstance(row.get("draw_json"), str) else (row.get("draw_json") or {})
    except ValueError: dj = {}
    fmt = str(dj.get("format") or ""); trial = fmt in FMT.FORMATS and bool(FMT.FORMATS[fmt]["show"])
    def status(k): return str((led.get(k) or {}).get("status") or "missing")
    def words(k): return str((led.get(k) or {}).get("evidence") or "")
    bad = [] if fmt in FMT.FORMATS else [f"the episode has no format ('{fmt}'): the inside of a format was not walked"]
    for k in ("viewer_inside", "format_ending", "camera_path", "camera_shown"):
        s = status(k)
        if s == "PASS": continue
        if trial and s == CON.NA and ((k == "format_ending" and "is a trial" in words(k)) or (k in ("camera_path", "camera_shown") and "cuts between its pictures" in words(k))): continue
        bad.append(f"{k} {s}: {words(k)[:140]}")
    if bad: return False, "; ".join(bad)
    m = re.search(r"(\d+) of (\d+) sentences \(([\d.]+)%\) inside the scene \(floor (\d+)%\)", words("viewer_inside"))
    share = f"{m.group(3)}% of {m.group(2)} sentences inside (floor {m.group(4)}%)" if m else words("viewer_inside")[:90]
    acts = "the trial cuts between its pictures" if trial else words("camera_path").split("; every picture")[0][:160]
    end = words("format_ending").rsplit("; ", 1)[-1][:120] if trial else words("format_ending").split("; no ask")[0][:120]      # v12 V1c (F3): the evidence's own last clause
    return True, f"inside the format held: {fmt}; {share}; {acts}; {end}"

def floor_of(core, ep, climbed=False):
    """v12 V1c: (ok, words) - THE SWEEP WALKS THE FLOOR, HIS LINE AND ONE STORY. The long video of this id must have PASSED viewer_floor (or say N/A with
    evidence that begins 'void by its canary'), makers_line and living_characters, and one_story on an id that climbed the ladder (N/A 'made under an
    override' otherwise). A missing row, any other 'not applicable' or a FAIL is a failure here. The words begin 'the floor judged: ' (or 'the floor was
    void by its canary: ') and carry the looks won of 4."""
    from whatifs import contract as CON
    led = {}
    for r in core.store().rows("Feature_Ledger"):
        if r.get("episode_id") == ep: led[r.get("feature")] = r                      # the latest verdict per check
    def status(k): return str((led.get(k) or {}).get("status") or "missing")
    def words(k): return str((led.get(k) or {}).get("evidence") or "")
    void = status("viewer_floor") == CON.NA and words("viewer_floor").startswith("void by its canary"); bad = []
    if status("viewer_floor") != CON.PASS and not void: bad.append(f"viewer_floor {status('viewer_floor')}: {words('viewer_floor')[:140]}")
    for k in ("makers_line", "living_characters"):
        if status(k) != CON.PASS: bad.append(f"{k} {status(k)}: {words(k)[:140]}")
    if climbed and status("one_story") != CON.PASS: bad.append(f"one_story {status('one_story')}: {words('one_story')[:140]}")
    if not climbed and not (status("one_story") == CON.NA and words("one_story").startswith("made under an override")):
        bad.append(f"one_story {status('one_story')} on an id that did not climb: {words('one_story')[:140]}")
    if bad: return False, "; ".join(bad)
    return True, (("the floor was void by its canary: " if void else "the floor judged: ") + words("viewer_floor")[:220] + " | " + words("makers_line")[:110] + " | "
                  + words("one_story")[:140])

def hd_of(core, ids):
    """v12 B-OWNER (PART 9, R24): (ok, words) - THE SWEEP WALKS THE HD GATE. Asked only of a run with the organisation on (the runs in which the sweep
    set HD_GATE_ON TRUE; the rehearsal sets it itself): every Short made in the run (`ids`) went up private and was made public by the gate - the
    `privacy` receipt of its YouTube record is KEPT with "public after ...". A Short without a record, with any other receipt (still WAITING, DRIFT,
    or a receipt the gate did not write) or no Short at all is a failure here: it would mean the new path was not walked."""
    from whatifs import release as REL
    if not ids: return False, "no Short was made in this run: the HD gate was not walked"
    bad = []; said = []
    for i in ids:
        y = next((x for x in REL.records(i) if x.get("platform") == "youtube"), None)
        if not y: bad.append(f"{i}: no YouTube record"); continue
        rc = list((y.get("receipts") or {}).get("privacy") or [])
        if len(rc) < 2 or rc[0] != REL.KEPT or not str(rc[1]).startswith("public after"):
            bad.append(f"{i}: privacy {rc[0] if rc else 'missing'}: {str(rc[1] if len(rc) > 1 else '')[:140]}"); continue
        said.append(f"{i}: {rc[1]}")
    if bad: return False, "; ".join(bad)
    return True, f"the HD gate held: {len(ids)} of {len(ids)} upload(s) went up private and public after their wait: " + "; ".join(said)

def screens_of(core, ids=()):
    """v12 B-OWNER (PART 9, R17 (11 c)): (ok, words) - THE SWEEP WALKS HIS TWO SCREENS on the id's own Sheet, after its run. THE CLOCK IS PLANTED, so the
    counts never hang on the hour of the run: one open card (a decision for the evening list), then `digests.tick` at 09:05 and `digests.needs_tick` at
    18:05 India time of the next India day. The id is BAD when an Owner_Actions kind is not in the register (`notify.KINDS`), when WA_Outbox holds a
    "refused_window" row or a kind outside morning, needs, alarm, reply, or when it holds no "morning" row or no "needs" row (5.6: a missing row is a
    failure). Walked twice (the rehearsal, then the sweep's rehearsal branch) it sends nothing twice: both clocks are stamped, the card is one row."""
    from whatifs import notify as NT, digests as DG, wa as WA
    ep = str((list(ids) or [""])[0] or "")
    NT.send("bakeoff", "A decision planted by the sweep: the evening list must carry it.", [("Pick A", "PICK A")], episode=ep or None,
            default="A is used", expires_h=72, dedupe_key=f"sweep|planted|{ep}")
    day = (core.now_utc().astimezone(NT.IST) + dt.timedelta(days=1)).date()
    DG.tick(now=dt.datetime(day.year, day.month, day.day, 9, 5, tzinfo=NT.IST))
    DG.needs_tick(now=dt.datetime(day.year, day.month, day.day, 18, 5, tzinfo=NT.IST))
    st = core.store(); rows = st.rows("Owner_Actions"); out = st.rows("WA_Outbox"); bad = []
    unknown = sorted({str(r.get("kind")) for r in rows if r.get("kind") not in NT.KINDS})
    if unknown: bad.append("a message of a kind the register does not know: " + ", ".join(unknown))
    refused = [str(r.get("kind") or "") for r in out if r.get("status") == "refused_window"]
    if refused: bad.append(f"{len(refused)} WhatsApp message(s) refused outside the 24-hour window: " + ", ".join(sorted(set(refused))))
    odd = sorted({str(r.get("kind") or "") for r in out if r.get("kind") not in WA.PUSH_KINDS + ("reply",)})
    if odd: bad.append("WhatsApp started a message of another kind: " + ", ".join(odd))
    n = {k: sum(1 for r in out if r.get("kind") == k and r.get("wamid")) for k in WA.PUSH_KINDS}
    if not n["morning"]: bad.append("no morning message went out at the planted 09:05")
    if not n["needs"]: bad.append("no \"Needs you\" list went out at the planted 18:05 with a decision open")
    if bad: return False, "; ".join(bad)
    return True, f"the owner's road held: {len(rows)} rows, all registered; WhatsApp: {n['morning']} morning, {n['needs']} needs, {n['alarm']} alarm"

# ------------------------------------------------------------------ one id (runs in its own process: module state never leaks between ids)
def drawn_moments():
    """v12 DRAWN (DQ-3 AMENDED): every id in the drawn arm, explaining moments from the first second and from 1.0 s, on the id's OWN Sheet - exactly
    the three cells tests/test_v12_drawn_film.py's _setup sets; nothing else is ever set by it (the offline film keeps none under the defaults: 0 of 80 ids)."""
    from whatifs.core import set_setting
    set_setting("DRAWN_SHARE_PCT", "100"); set_setting("GRAPHICS_FREE_SEC", "0"); set_setting("DRAWN_MIN_S", "1.0")


def one(ep, work, repo=ROOT, org=True, mode="produce", slot_h=10, drawn=False):
    os.environ.update(WI_FAKE="1", WI_SMALL="1", WI_WORK=os.path.join(work, "work"), PYTHONUTF8="1")
    for k in KEYS: os.environ.pop(k, None)
    os.makedirs(os.environ["WI_WORK"], exist_ok=True); sys.path.insert(0, repo)
    res = {"id": ep, "mode": mode, "org": bool(org), "outcome": "crash", "problems": [], "fails": [], "warn": {}, "degraded": [], "owner": [], "error": ""}
    t0 = time.time()
    try:
        from whatifs import core
        import whatifs.voice as V
        from tools.rehearsal import ToneVoice
        from whatifs import manage as MG, episode as EP
        if mode == "short":                                                         # v12 V2c: standalone Shorts - a first one, then the one under test (so the variety rules meet a history)
            from whatifs import shorts2 as SH
            core._store = core.LocalStore(os.path.join(work, "sheet.json")); core._store.ensure_tabs(); core._settings_cache = None
            for k, v in TEST_SETTINGS.items(): core.set_setting(k, v)
            if org: core.set_setting("HD_GATE_ON", "TRUE")                          # v12 B-OWNER (R22 (11)): the gate is FALSE as shipped; the sweep's runs with the organisation on walk it (R24)
            if not org: core.set_setting("ORG_ON", "FALSE")
            MG.setup()
            if not org: core.set_setting("ORG_ON", "FALSE")
            h = int(__import__("hashlib").sha1(ep.encode()).hexdigest(), 16); prem = [SHORT_PREMISES[(h + i * 7) % len(SHORT_PREMISES)] for i in range(2)]
            core.store().append("Premise_Bench", [{"bench_id": f"SW{i}", "premise": p, "status": "READY", "combined": 99 - i} for i, p in enumerate(prem)])
            # v12 V2c-b2: the Shorts of the sweep are RELEASED. The first is made while nobody has proven that uploads are open (an empty Sheet whose upload
            # check could not run): it must be MADE on its record, handed to Publishing and wait. Then the check passes, the file on this machine is gone
            # (another job, another day) and the tick's pass must send the copy kept in Drive. The Short under test goes out at the first try.
            from whatifs import release as REL, launch as LA
            core.set_setting("SHORTS_REVIEW_FIRST_N", "0"); core.set_setting("UPLOAD_CHECK_AT", core.iso())      # the check 'could not run' a moment ago: it is not tried again for 6 hours
            r0 = SH.run(force=True, publish=True, episode_id="SHW" + ep[2:]); late = []
            if r0.get("ok"):
                row0 = next((x for x in core.store().rows("Specials") if x.get("id") == r0["id"]), {}); rec0 = {x["platform"]: x for x in REL.records(r0["id"])}
                if not (row0.get("made") and not row0.get("yt_id") and (rec0.get("youtube") or {}).get("state") == REL.QUEUED and SH._made(row0) and REL.settle() == []):
                    late.append(f"a Short made while uploads were closed is not made-and-waiting (status {row0.get('status')}, record {(rec0.get('youtube') or {}).get('state')})")
                try: os.remove(str(r0.get("path")))
                except OSError: pass
                LA.upload_check(); done0 = REL.settle()
                ok0, why0 = REL.report(r0["id"]); row0 = next((x for x in core.store().rows("Specials") if x.get("id") == r0["id"]), {})
                if not (done0 == [r0["id"]] and ok0 and row0.get("yt_id") and row0.get("status") == "POSTED" and REL.settle() == []): late.append(f"the waiting Short did not go out when uploads opened: {why0[:160]}")
            approve = h % 2 == 1                                                         # every second id: the Short under test waits for the owner's Approve and goes out by his tap
            if approve: core.set_setting("SHORTS_REVIEW_FIRST_N", "99")
            r = SH.run(force=True, publish=True, episode_id=ep)
            if approve and r.get("ok"):
                from whatifs import specials as SPW
                if r.get("status") != "AWAITING_APPROVAL" or REL.records(ep) or REL.settle(): late.append(f"a Short that waits for the owner's Approve was touched by Publishing (status {r.get('status')})")
                said = SPW.approve(ep); r = dict(r, **next((x for x in core.store().rows("Specials") if x.get("id") == ep), {}))
                if not str(said).startswith("posted"): late.append(f"the approved Short did not go out: {str(said)[:120]}")
            okr, whyr = REL.report(ep) if r.get("ok") else (False, "not made")
            if r0.get("ok") and r.get("ok"):                                             # v12 V2d: THE SWEEP WALKS THE MONEY - both Shorts' estimates against what their runs paid
                ok_m, res["money"] = money_of(core, [r0["id"], ep])
                if not ok_m: late.append("the cost model: " + res["money"][:240])
                ok_x, res["motion"] = motion_of(core, None, [r0["id"], ep])          # v12 V2d-b: THE SWEEP WALKS THE LADDER'S RULES - both Shorts' finished files were measured
                if not ok_x: late.append("the ladder's rules: " + res["motion"][:240])
                if org:                                                              # v12 B-OWNER (R24): THE SWEEP WALKS THE HD GATE - only where it set HD_GATE_ON: both Shorts went up private and out through the gate
                    ok_h, res["hd"] = hd_of(core, [r0["id"], ep])
                    if not ok_h: late.append("the HD gate: " + res["hd"][:240])
            ok_w, res["screens"] = screens_of(core, [ep])                              # v12 B-OWNER: THE SWEEP WALKS HIS TWO SCREENS - the register, the window at the wire, the planted morning and evening
            if not ok_w: late.append("his two screens: " + res["screens"][:240])
            res["problems"] = [f"the first Short: {x}" for x in (r0.get("failed") or ([r0.get("why")] if not r0.get("ok") else []))] + [str(x) for x in (r.get("failed") or [])] + late + ([] if okr or not r.get("ok") else [f"release sheet: {whyr[:200]}"])
            if r0.get("ok") and r.get("ok") and os.path.exists(str(r.get("path") or "")) and okr and not late and r.get("status") == "POSTED":
                res["outcome"] = "ok"; res["short"] = f"{r0.get('format')}>{r.get('format')}"; res["release"] = ("approved:" if approve else "") + "+".join(x["state"] for x in REL.records(ep))
            elif r.get("held") or r0.get("held"): res["outcome"] = "held"
            else: res["outcome"] = "odd"; res["error"] = json.dumps({k: v for k, v in dict(r0, **r).items() if k != "script"}, default=str)[:300]
        elif mode == "rehearsal":                                                   # the path GitHub's Checks run: the full rehearsal, its one time-based id replaced by the fixed one
            from tools.rehearsal import run
            try: run(ep_id=ep); res["outcome"] = "ok"                                # v12 V2c-b: the rehearsal takes the fixed id itself (its Shorts' ids are derived from it)
            except AssertionError as e: res["outcome"] = "assert"; res["error"] = (str(e) or traceback.format_exc().strip().splitlines()[-2].strip())[:300]
            if res["outcome"] == "ok":                                              # v12 V2b: the rehearsal's long video judged by the sweep's own words too (its counter format_inside_held)
                ok_i, res["inside"] = inside_of(core, ep)
                if not ok_i: res["outcome"] = "odd"; res["problems"].append("inside the format: " + res["inside"]); res["error"] = res["inside"][:300]
            if res["outcome"] == "ok":                                              # v12 DRAWN: THE SWEEP WALKS THE DRAWN SCENES - in the arm both checks PASS, outside it both say so
                ok_d, res["drawn"] = drawn_of(core, ep)
                if not ok_d: res["outcome"] = "odd"; res["problems"].append("the drawn scenes: " + res["drawn"]); res["error"] = res["drawn"][:300]
            if res["outcome"] == "ok":                                              # v12 V1c: the rehearsal's long video (it climbed) - the floor, his line, one story
                ok_f, res["floor"] = floor_of(core, ep, climbed=True)
                if not ok_f: res["outcome"] = "odd"; res["problems"].append("the floor, his line or one story: " + res["floor"]); res["error"] = res["floor"][:300]
            if res["outcome"] == "ok":                                              # v12 V4: THE SWEEP WALKS THE CEO - a month of Strategy on the id's own Sheet
                from tools import rehearsal as REH4                               # the rehearsal walked the month itself (its words): a second walk would plant twice
                ok_s, res["strategy"] = (True, REH4.STRATEGY_SAID[-1]) if REH4.STRATEGY_SAID else strategy_of(core, ep, org)
                if not ok_s: res["outcome"] = "odd"; res["problems"].append("the CEO's month: " + res["strategy"]); res["error"] = res["strategy"][:300]
            if res["outcome"] == "ok" and org:                                      # v12 B-OWNER (R24): THE SWEEP WALKS THE HD GATE - the rehearsal's Shorts went up private and out through the gate
                ok_h, res["hd"] = hd_of(core, [x["id"] for x in core.store().rows("Ladder") if str(x.get("id", "")).startswith("SH")])
                if not ok_h: res["outcome"] = "odd"; res["problems"].append("the HD gate: " + res["hd"]); res["error"] = res["hd"][:300]
            if res["outcome"] == "ok":                                              # v12 B-OWNER: THE SWEEP WALKS HIS TWO SCREENS - judged again on the rehearsal's Sheet (nothing is sent twice)
                ok_w, res["screens"] = screens_of(core, [ep])
                if not ok_w: res["outcome"] = "odd"; res["problems"].append("his two screens: " + res["screens"]); res["error"] = res["screens"][:300]
        else:                                                                      # the recipe of the end-to-end test in tests/test_v12_org.py
            core._store = core.LocalStore(os.path.join(work, "sheet.json")); core._store.ensure_tabs(); core._settings_cache = None
            for k, v in TEST_SETTINGS.items(): core.set_setting(k, v)
            if org: core.set_setting("HD_GATE_ON", "TRUE")                          # v12 B-OWNER (R22 (11)): the gate is FALSE as shipped; the sweep's runs with the organisation on walk it (R24)
            if not org: core.set_setting("ORG_ON", "FALSE")
            V.KokoroBackend = lambda blend: ToneVoice()
            MG.setup(); core.set_setting("VOICE", "C")
            if not org: core.set_setting("ORG_ON", "FALSE")
            if drawn: drawn_moments()                                             # v12 DRAWN (DQ-3): the flag --drawn-moments - after the setup, before the long video
            slot = (core.now_utc() + dt.timedelta(hours=slot_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
            if climb(core, ep): res["ladder"] = "climbed"                          # v12 V2c-b: every topic starts as a Short - the long video of this id is about its promoted Short
            r = EP.produce(slot, episode_id=ep)
            res["problems"] = [str(p) for p in (r.get("problems") or [])]
            if r.get("ok") and r.get("episode") == ep and os.path.exists(str(r.get("master") or "")): res["outcome"] = "ok"
            elif r.get("held"): res["outcome"] = "held"
            else: res["outcome"] = "odd"; res["error"] = json.dumps(r, default=str)[:300]
            if res["outcome"] == "ok" and res.get("ladder") == "climbed":           # v12 V2c-b2b: THE SWEEP WALKS THE OPENING - a long video that climbed must open on its Short's footage
                ok_o, res["opening"] = opening_of(core, ep)
                if not ok_o: res["outcome"] = "odd"; res["problems"].append("the long video does not open on its Short's footage: " + res["opening"]); res["error"] = res["opening"][:300]
            if res["outcome"] == "ok":                                              # v12 V2c-b2b: THE SWEEP WALKS THE RELEASE - no cut-down reel, one step to LIVE, nothing short out but the Shorts
                ok_r, res["release"] = release_of(core, ep, r)
                if not ok_r: res["outcome"] = "odd"; res["problems"].append("cut-downs or the release step: " + res["release"]); res["error"] = res["release"][:300]
            if res["outcome"] == "ok":                                              # v12 V2d: THE SWEEP WALKS THE MONEY - the long video's estimate (and its Short's) against what the runs really paid
                ok_m, res["money"] = money_of(core, [ep] + (["SH" + ep[2:]] if res.get("ladder") == "climbed" else []))
                if not ok_m: res["outcome"] = "odd"; res["problems"].append("the cost model: " + res["money"]); res["error"] = res["money"][:300]
            if res["outcome"] == "ok":                                              # v12 V2d-b: THE SWEEP WALKS THE LADDER'S RULES - the finished film (and its Short's file) measured: what moves, real footage, characters
                ok_x, res["motion"] = motion_of(core, ep, ["SH" + ep[2:]] if res.get("ladder") == "climbed" else [])
                if not ok_x: res["outcome"] = "odd"; res["problems"].append("the ladder's rules: " + res["motion"]); res["error"] = res["motion"][:300]
            if res["outcome"] == "ok":                                              # v12 V2b: THE SWEEP WALKS THE INSIDE OF THE FORMAT - the voice, the ending, the camera path, judged on the script and the render's record
                ok_i, res["inside"] = inside_of(core, ep)
                if not ok_i: res["outcome"] = "odd"; res["problems"].append("inside the format: " + res["inside"]); res["error"] = res["inside"][:300]
            if res["outcome"] == "ok":                                              # v12 DRAWN: THE SWEEP WALKS THE DRAWN SCENES - in the arm both checks PASS, outside it both say so
                ok_d, res["drawn"] = drawn_of(core, ep)
                if not ok_d: res["outcome"] = "odd"; res["problems"].append("the drawn scenes: " + res["drawn"]); res["error"] = res["drawn"][:300]
            if res["outcome"] == "ok":                                              # v12 V1c: THE SWEEP WALKS THE FLOOR, HIS LINE AND ONE STORY - judged by first-time viewers, his line kept, the thumbnail the opening
                ok_f, res["floor"] = floor_of(core, ep, climbed=res.get("ladder") == "climbed")
                if not ok_f: res["outcome"] = "odd"; res["problems"].append("the floor, his line or one story: " + res["floor"]); res["error"] = res["floor"][:300]
            if res["outcome"] == "ok":                                              # v12 V4: THE SWEEP WALKS THE CEO - a month of Strategy on the id's own Sheet
                ok_s, res["strategy"] = strategy_of(core, ep, org)
                if not ok_s: res["outcome"] = "odd"; res["problems"].append("the CEO's month: " + res["strategy"]); res["error"] = res["strategy"][:300]
            if res["outcome"] == "ok" and org:                                      # v12 B-OWNER (R24): THE SWEEP WALKS THE HD GATE - the climbed Short went up private and out through the gate
                ok_h, res["hd"] = hd_of(core, ["SH" + ep[2:]] if res.get("ladder") == "climbed" else [])
                if not ok_h: res["outcome"] = "odd"; res["problems"].append("the HD gate: " + res["hd"]); res["error"] = res["hd"][:300]
            if res["outcome"] == "ok":                                              # v12 B-OWNER: THE SWEEP WALKS HIS TWO SCREENS - the register, the window at the wire, the planted morning and evening
                ok_w, res["screens"] = screens_of(core, [ep])
                if not ok_w: res["outcome"] = "odd"; res["problems"].append("his two screens: " + res["screens"]); res["error"] = res["screens"][:300]
        res.update(evidence(core, ep, org))
    except BaseException as e:                                                      # a crash is a result too: the last line of the traceback names it
        if isinstance(e, KeyboardInterrupt): raise
        res["outcome"] = "crash"; res["error"] = (type(e).__name__ + ": " + str(e))[:300]; res["where"] = " < ".join(f"{os.path.basename(f.filename)}:{f.lineno}" for f in traceback.extract_tb(e.__traceback__)[-3:])
        try:
            from whatifs import core
            res.update(evidence(core, ep, org))
        except Exception: pass
    res["sec"] = round(time.time() - t0)
    print("RESULT " + json.dumps(res, sort_keys=True, default=str), flush=True)
    return res

def evidence(core, ep, org):
    """What the store says about the episode after the run: failed checks with their evidence, warning classes, degraded steps, owner messages, organisation runs."""
    try: core.flush_log()
    except Exception: pass
    st = core.store(); out = {}
    led = [r for r in st.rows("Feature_Ledger") if r.get("episode_id") == ep]
    last = {}
    for r in led: last[(r.get("stage"), r.get("feature"))] = r                      # the latest verdict per check and stage
    out["fails"] = [[k[1], k[0], str(r.get("evidence"))[:200]] for k, r in sorted(last.items(), key=lambda x: str(x[0])) if r.get("status") == "FAIL"]
    out["checks"] = {s: sum(1 for r in last.values() if r.get("status") == s) for s in sorted({r.get("status") for r in last.values()})}
    warn = {}
    for r in st.rows("Run_Log"):
        if r.get("level") in ("WARN", "ERROR"):
            c = r.get("level") + ": " + warn_class(r.get("message")); warn[c] = warn.get(c, 0) + 1
    out["warn"] = warn
    out["degraded"] = list(getattr(core, "_degraded", []))
    out["owner"] = sorted({str(r.get("kind")) for r in st.rows("Owner_Actions")}) if "Owner_Actions" in core.TABS else []
    row = next((r for r in st.rows("Episodes") if r.get("episode_id") == ep), None); out["status"] = (row or {}).get("status", "")
    if org and "Sessions" in core.TABS:
        try:
            from whatifs.org import runner as RUN, memos as MEM
            ses = [s for s in st.rows("Sessions") if s.get("episode_id") == ep]
            out["runs"] = len(ses); out["runs_bad"] = sorted(f"{s['dept']}.{s['trigger']}:{s['status']}" for s in ses if s.get("status") != "ok" or RUN.verify(s))
            live = [m for m in MEM.rows(st) if m.get("status") not in ("resolved", "rejected")]; out["memos_live"] = len(live)
            out["memos_open"] = sorted(f"{m.get('type')}>{m.get('to_depts')}:{str(m.get('subject'))[:60]}" for m in live if m.get("type") == "problem_memo")      # a problem nobody settled is a fault class
        except Exception as e: out["org_error"] = (type(e).__name__ + ": " + str(e))[:200]
    return out

# ------------------------------------------------------------------ the sweep (parent): one child process per id, a few at a time
def child(ep, a, base):
    work = os.path.join(base, ep); shutil.rmtree(work, ignore_errors=True); os.makedirs(work, exist_ok=True)
    logp = os.path.join(a.logs, ep + ".log")
    cmd = [sys.executable, os.path.abspath(__file__), "--one", ep, "--work", work, "--repo", a.repo, "--mode", a.mode, "--slot-h", str(a.slot_h)] + (["--org", "off"] if a.org == "off" else []) + (["--drawn-moments"] if a.drawn_moments else [])
    env = dict(os.environ, WI_FAKE="1", WI_SMALL="1", PYTHONUTF8="1"); t0 = time.time()
    try:
        with open(logp, "w", encoding="utf-8", errors="replace") as lf:
            rc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=a.repo, env=env, timeout=a.timeout).returncode
        tail = open(logp, encoding="utf-8", errors="replace").read().splitlines()
        line = next((x for x in reversed(tail) if x.startswith("RESULT ")), None)
        res = json.loads(line[7:]) if line else {"id": ep, "outcome": "crash", "error": f"no RESULT line (exit {rc}): " + " | ".join(tail[-3:])[:300]}
    except subprocess.TimeoutExpired:
        res = {"id": ep, "outcome": "timeout", "error": f"no result after {a.timeout} s"}
    res.setdefault("sec", round(time.time() - t0))
    if not a.keep: shutil.rmtree(work, ignore_errors=True)                         # production refuses to start under 1 GB free disk: never leave episode folders behind
    return res

def strategy_of(core, ep, org=True):
    """v12 V4: the CEO's month on the id's own Sheet (see _strategy_of). A rehearsal pair's forced Short format belongs to its production, not to this month (V4's finish C22)."""
    saved = os.environ.pop("WI_SHORT_FORMAT", None)
    try: return _strategy_of(core, ep, org)
    finally:
        if saved is not None: os.environ["WI_SHORT_FORMAT"] = saved

def _strategy_of(core, ep, org=True):
    """v12 V4: (ok, words) - THE SWEEP WALKS THE CEO on the id's own Sheet, after its video. With the organisation OFF no ticket can exist: a round must
    write NOTHING. With it ON: (a) sixteen planted measured Ladder rows, all earlier than the id's own climbed Short (S1 and S3 four each, then S2's
    eight) -> ONE judgement, ONE decision SHORT_SHARE_S2 40 -> 20, its ticket, ONE "strategy" action; (b) the engine's pass sets the cell; (c) the Undo
    takes it back; (d) the next round, a planted day later, decides nothing on that key and opens the stand-in's trial; (e) a planted rejected video
    closes the uploads and one tap opens them; (f) the scoreboard leads both briefs and the decision's line is shown once."""
    import json as _j
    from whatifs.org import strategy as STR, execute as EX, risk as RISK, memos as MEM
    from whatifs import cli as CLI, digests as DG, notify as NT, scoreboard as SB
    st = core.store(); acts = lambda kind: [a for a in st.rows("Owner_Actions") if a.get("kind") == kind]
    if not org:
        before = (len(st.rows("Decisions")), len(acts("strategy")))
        core.set_setting("STRATEGY_ON", "TRUE"); CLI.strategy_round()
        if (len(st.rows("Decisions")), len(acts("strategy"))) != before: return False, "the organisation is off and a round of Strategy wrote a row or a message"
        return True, "the month's decision held: the organisation is off, nothing was written (0 decisions)"
    for k, v in (("STRATEGY_ON", "TRUE"), ("ARM_STAND_IN_ON", "TRUE"), ("PLAYBOOK_ON", "TRUE"), ("SHORT_FORMAT_FORCE", ""), ("SHORT_SHARE_S2", "40")): core.set_setting(k, v)
    own = next((r for r in st.rows("Ladder") if r.get("id") == "SH" + ep[2:]), None)
    t0 = core.parse_iso((own or {}).get("posted")) or core.now_utc(); base = t0 - dt.timedelta(hours=20)
    plan = [("S1", v) for v in (20, 30, 50, 80)] + [("S3", v) for v in (90, 120, 200, 400)] + [("S2", v) for v in (10, 10, 20, 20, 30, 30, 40, 300)]
    st.append("Ladder", [{"id": f"SW{ep[-8:]}{i:02d}", "format": f, "posted": core.iso(base + dt.timedelta(hours=i)), "state": "POSTED", "evidence": "measured",
                          "first": _j.dumps({"days": 3, "engaged": v})} for i, (f, v) in enumerate(plan)])
    p = []
    CLI.strategy_round()                                                                                          # (a)
    js = [r for r in st.rows("Decisions") if r.get("state") == "judged" and r.get("rule") in ("SHORT_ARMS", "ARMS")]
    ds = [r for r in st.rows("Decisions") if r.get("rule") not in ("HAND", "WATCH", "RISK") and r.get("state") not in ("judged", "hand", "watch")]
    if len(js) != 1 or len(ds) != 1 or (ds[0]["key"], ds[0]["old"], ds[0]["new"]) != ("SHORT_SHARE_S2", "40", "20"): return False, f"(a) {len(js)} judgement(s), decisions {[(d['key'], d['old'], d['new']) for d in ds]}"
    d = ds[0]; sa = acts("strategy")
    if not MEM.get(d["ticket"]) or len(sa) != 1 or not sa[0]["text"].startswith("Strategy decided:"): return False, f"(a) the ticket or the action is missing ({len(sa)} action(s))"
    EX.engine_tick()                                                                                              # (b)
    if core.S("SHORT_SHARE_S2") != "20": p.append(f"(b) after the engine's pass SHORT_SHARE_S2 reads {core.S('SHORT_SHARE_S2')}")
    said = NT.answer(sa[0]["id"], f"STRATEGY UNDO {d['id']}")                                                     # (c)
    if core.S("SHORT_SHARE_S2") != "40" or next(r for r in st.rows("Decisions") if r["id"] == d["id"])["state"] != "undone": p.append(f"(c) the Undo did not take it back ({said[:80]})")
    for k in ("THINK_BOOST_VARIANTS", "STANDARD_MAX_LONG_PER_MONTH", "SHORTS_PER_MONTH", "SHORTS_PER_WEEK"): STR.hand(k, core.S(k))      # (d) proves the trial opens when nothing else may move (P10; V4's finish C12 lets SPLIT move)
    real = STR.now_utc; STR.now_utc = lambda: real() + dt.timedelta(days=1)                                      # (d) a planted day later
    try: CLI.strategy_round()
    finally: STR.now_utc = real
    again = [r for r in st.rows("Decisions") if r.get("key") == "SHORT_SHARE_S2" and r["id"] != d["id"] and r.get("state") not in ("judged",)]
    cs = {r["kind"]: r for r in st.rows("Candidates")}
    if again: p.append("(d) the next round moved SHORT_SHARE_S2 again")
    if (cs.get("machine") or {}).get("state") != "trial" or (cs.get("hand") or {}).get("state") != "for his desk (B9)": p.append(f"(d) the candidates read {[(k, v.get('state')) for k, v in cs.items()]}")
    else:
        EX.engine_tick(); er = EX.state_of(cs["machine"]["ticket"])
        if not er or er[0] != "applied": p.append(f"(d) the trial's ticket is {er}")
    st.append("Specials", [{"id": f"SWREJ{ep[-6:]}", "kind": "short", "title": "a planted rejected Short", "yt_id": f"rej{ep[-6:]}", "made": core.iso(core.now_utc())}])
    vs = RISK._video_states; RISK._video_states = lambda ids: {i: ({"upload": "rejected", "reason": "planted by the sweep"} if i.startswith("rej") else {"upload": "processed"}) for i in ids}
    try: RISK.run()                                                                                               # (e)
    finally: RISK._video_states = vs
    lk = acts("risk_lock"); wr = [r for r in st.rows("Decisions") if r.get("rule") == "WATCH" and r.get("key") == "platform_flag"]
    if core.S("UPLOAD_LOCK") != "on" or len(lk) != 1 or len(wr) != 1: p.append(f"(e) lock {core.S('UPLOAD_LOCK')}, {len(lk)} lock action(s), {len(wr)} watch row(s)")
    elif not str(NT.answer(lk[0]["id"], f"RISK OPEN rej{ep[-6:]}")).startswith("the uploads are open") or core.S("UPLOAD_LOCK") != "off": p.append("(e) the tap did not open the uploads")
    SB.keep(); now = core.now_utc() + dt.timedelta(days=1, minutes=1)                                            # (f) on (d)'s planted day: the trial's decision is dated then
    if not st.rows("Scoreboard"): p.append("(f) no Scoreboard row")
    for kind in ("daily", "weekly"):
        parts = DG.compose(kind, now=now)[0].split("\n\n")
        if len(parts) < 2 or not parts[1].startswith("Scoreboard:"): p.append(f"(f) the {kind} brief does not lead with the scoreboard")
    if "Strategy decided:" not in DG.compose("daily", now=now)[0]: p.append("(f) the brief does not carry the decision's line")
    STR.briefed(now)
    if "Strategy decided:" in DG.compose("daily", now=now + dt.timedelta(minutes=1))[0]: p.append("(f) the decision's line is shown again after it went")
    if p: return False, "; ".join(p)
    n_dec = sum(1 for r in st.rows("Decisions") if r.get("rule") not in ("HAND", "WATCH", "RISK") and r.get("state") not in ("judged", "hand", "watch"))   # counted, never typed
    return True, (f"the month's decision held: {n_dec} decisions (SHORT_SHARE_S2 40 -> 20 decided, told, executed and undone; the trial opened); one judgement; "
                  "a rejected video closed and reopened the uploads")

def summary(results):
    by = {}
    for r in results: by[r["outcome"]] = by.get(r["outcome"], 0) + 1
    fails, warn, deg, own = {}, {}, {}, {}
    for r in results:
        for f in r.get("fails", []): fails.setdefault(f"{f[0]}@{f[1]}", []).append(r["id"])
        for p in r.get("problems", []): fails.setdefault("problem:" + str(p), []).append(r["id"])
        for c in r.get("warn", {}): warn.setdefault(c, []).append(r["id"])
        for d in r.get("degraded", []): deg.setdefault(str(d)[:90], []).append(r["id"])
        for k in r.get("owner", []): own.setdefault(k, []).append(r["id"])
        for b in r.get("runs_bad", []) + r.get("memos_open", []): fails.setdefault("org:" + b, []).append(r["id"])
    return {"n": len(results), "outcomes": by, "opened_on_footage": sum(1 for r in results if r.get("opening") and r["outcome"] == "ok"),
            "released_without_cutdowns": sum(1 for r in results if str(r.get("release") or "").startswith("no cut-down") and r["outcome"] == "ok"),
            "money_agreed": sum(1 for r in results if str(r.get("money") or "").startswith("every paid picture") and r["outcome"] == "ok"),
            "ladder_rules_held": sum(1 for r in results if str(r.get("motion") or "").startswith("the ladder's rules held") and r["outcome"] == "ok"),
            "format_inside_held": sum(1 for r in results if str(r.get("inside") or "").startswith("inside the format held") and r["outcome"] == "ok"),
            "drawn_held": sum(1 for r in results if str(r.get("drawn") or "").startswith("the drawn arm held:") and r["outcome"] == "ok"),          # v12 DRAWN: every long-video id
            "drawn_ids": sum(1 for r in results if _drew(r.get("drawn")) and r["outcome"] == "ok"),                                                  # ... and a FLOOR: ids that drew a scene
            "floor_judged": sum(1 for r in results if str(r.get("floor") or "").startswith("the floor judged") and r["outcome"] == "ok"),
            "strategy_month_held": sum(1 for r in results if str(r.get("strategy") or "").startswith("the month's decision held") and r["outcome"] == "ok"),      # v12 V4
            "hd_gated": sum(1 for r in results if str(r.get("hd") or "").startswith("the HD gate held") and r["outcome"] == "ok"),          # v12 B-OWNER: asked only of runs with the organisation on (R24)
            "owner_road_ok": sum(1 for r in results if str(r.get("screens") or "").startswith("the owner's road held") and r["outcome"] == "ok"),      # v12 B-OWNER: every id
            "bad_ids": sorted(r["id"] for r in results if r["outcome"] != "ok"), "fail_classes": {k: sorted(set(v)) for k, v in sorted(fails.items())},
            "warn_classes": {k: len(v) for k, v in sorted(warn.items())}, "degraded_classes": {k: len(v) for k, v in sorted(deg.items())}, "owner_message_kinds": {k: len(v) for k, v in sorted(own.items())}}

def main(argv=None):
    p = argparse.ArgumentParser(description="Sweep the fake pipeline over fixed episode ids.")
    p.add_argument("--n", type=int, default=40); p.add_argument("--offset", type=int, default=0); p.add_argument("--ids", default="")
    p.add_argument("--org", choices=("on", "off"), default="on"); p.add_argument("--mode", choices=("produce", "rehearsal", "short"), default="produce")
    p.add_argument("--jobs", type=int, default=3); p.add_argument("--out", default=""); p.add_argument("--work", default=""); p.add_argument("--repo", default=ROOT)
    p.add_argument("--slot-h", type=int, default=10); p.add_argument("--timeout", type=int, default=TIMEOUT_S); p.add_argument("--keep", action="store_true"); p.add_argument("--one", default="")
    p.add_argument("--drawn-moments", action="store_true", help="v12 DRAWN: every id in the drawn arm, explaining moments from the first second and from 1.0 s - the offline film keeps none under the defaults: 0 of 80 ids, DQ-3")
    a = p.parse_args(argv); a.repo = os.path.abspath(a.repo)
    if a.one: return 0 if one(a.one, os.path.abspath(a.work or tempfile.mkdtemp(prefix="sweep_")), a.repo, a.org == "on", a.mode, a.slot_h, a.drawn_moments)["outcome"] == "ok" else 1
    base = os.path.abspath(a.work or tempfile.mkdtemp(prefix="sweep_"))
    if inside(base, ROOT) or inside(base, a.repo): sys.exit("the work folder must be OUTSIDE the repo")
    out = os.path.abspath(a.out or os.path.join(base, "sweep_results.txt")); a.logs = os.path.join(base, "_logs"); os.makedirs(a.logs, exist_ok=True)
    ids = [x.strip() for x in a.ids.split(",") if x.strip()] or fixed_ids(a.n, a.offset)
    results = []
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"SWEEP mode={a.mode} org={a.org} ids={len(ids)} jobs={a.jobs} repo={a.repo} started={dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"); f.flush()
        with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
            for res in ex.map(lambda e: child(e, a, base), ids):
                results.append(res); f.write("RESULT " + json.dumps(res, sort_keys=True, default=str) + "\n"); f.flush()
        s = summary(results); f.write("SUMMARY " + json.dumps(s, sort_keys=True) + "\n")
        f.write(f"TOTAL ids {len(results)} ok {s['outcomes'].get('ok', 0)} bad {len(s['bad_ids'])}\n")
    print(f"TOTAL ids {len(results)} ok {s['outcomes'].get('ok', 0)} bad {len(s['bad_ids'])} -> {out}")
    return 0 if not s["bad_ids"] else 1

if __name__ == "__main__":
    sys.exit(main())
