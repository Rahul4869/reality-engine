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

# ------------------------------------------------------------------ one id (runs in its own process: module state never leaks between ids)
def one(ep, work, repo=ROOT, org=True, mode="produce", slot_h=10):
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
            res["problems"] = [f"the first Short: {x}" for x in (r0.get("failed") or ([r0.get("why")] if not r0.get("ok") else []))] + [str(x) for x in (r.get("failed") or [])] + late + ([] if okr or not r.get("ok") else [f"release sheet: {whyr[:200]}"])
            if r0.get("ok") and r.get("ok") and os.path.exists(str(r.get("path") or "")) and okr and not late and r.get("status") == "POSTED":
                res["outcome"] = "ok"; res["short"] = f"{r0.get('format')}>{r.get('format')}"; res["release"] = ("approved:" if approve else "") + "+".join(x["state"] for x in REL.records(ep))
            elif r.get("held") or r0.get("held"): res["outcome"] = "held"
            else: res["outcome"] = "odd"; res["error"] = json.dumps({k: v for k, v in dict(r0, **r).items() if k != "script"}, default=str)[:300]
        elif mode == "rehearsal":                                                   # the path GitHub's Checks run: the full rehearsal, its one time-based id replaced by the fixed one
            from tools.rehearsal import run
            try: run(ep_id=ep); res["outcome"] = "ok"                                # v12 V2c-b: the rehearsal takes the fixed id itself (its Shorts' ids are derived from it)
            except AssertionError as e: res["outcome"] = "assert"; res["error"] = (str(e) or traceback.format_exc().strip().splitlines()[-2].strip())[:300]
        else:                                                                       # the recipe of the end-to-end test in tests/test_v12_org.py
            core._store = core.LocalStore(os.path.join(work, "sheet.json")); core._store.ensure_tabs(); core._settings_cache = None
            for k, v in TEST_SETTINGS.items(): core.set_setting(k, v)
            if not org: core.set_setting("ORG_ON", "FALSE")
            V.KokoroBackend = lambda blend: ToneVoice()
            MG.setup(); core.set_setting("VOICE", "C")
            if not org: core.set_setting("ORG_ON", "FALSE")
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
    cmd = [sys.executable, os.path.abspath(__file__), "--one", ep, "--work", work, "--repo", a.repo, "--mode", a.mode, "--slot-h", str(a.slot_h)] + (["--org", "off"] if a.org == "off" else [])
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
            "released_without_cutdowns": sum(1 for r in results if str(r.get("release") or "").startswith("no cut-down") and r["outcome"] == "ok"), "bad_ids": sorted(r["id"] for r in results if r["outcome"] != "ok"), "fail_classes": {k: sorted(set(v)) for k, v in sorted(fails.items())},
            "warn_classes": {k: len(v) for k, v in sorted(warn.items())}, "degraded_classes": {k: len(v) for k, v in sorted(deg.items())}, "owner_message_kinds": {k: len(v) for k, v in sorted(own.items())}}

def main(argv=None):
    p = argparse.ArgumentParser(description="Sweep the fake pipeline over fixed episode ids.")
    p.add_argument("--n", type=int, default=40); p.add_argument("--offset", type=int, default=0); p.add_argument("--ids", default="")
    p.add_argument("--org", choices=("on", "off"), default="on"); p.add_argument("--mode", choices=("produce", "rehearsal", "short"), default="produce")
    p.add_argument("--jobs", type=int, default=3); p.add_argument("--out", default=""); p.add_argument("--work", default=""); p.add_argument("--repo", default=ROOT)
    p.add_argument("--slot-h", type=int, default=10); p.add_argument("--timeout", type=int, default=TIMEOUT_S); p.add_argument("--keep", action="store_true"); p.add_argument("--one", default="")
    a = p.parse_args(argv); a.repo = os.path.abspath(a.repo)
    if a.one: return 0 if one(a.one, os.path.abspath(a.work or tempfile.mkdtemp(prefix="sweep_")), a.repo, a.org == "on", a.mode, a.slot_h)["outcome"] == "ok" else 1
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
