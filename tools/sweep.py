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

def warn_class(msg):
    """One class per kind of warning: numbers, ids and quoted detail are folded away so that 40 episodes give a short list."""
    m = re.sub(r"EP\d{6,}", "EP#", str(msg)); m = re.sub(r"'[^']{0,80}'|\"[^\"]{0,80}\"", "'..'", m); m = re.sub(r"\d+(\.\d+)?", "#", m)
    return re.sub(r"\s+", " ", m).strip()[:90]

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
        if mode == "rehearsal":                                                     # the path GitHub's Checks run: the full rehearsal, its one time-based id replaced by the fixed one
            real = EP.produce
            EP.produce = lambda slot, episode_id=None, **k: real(slot, episode_id=episode_id or ep, **k)
            from tools.rehearsal import run
            try: run(); res["outcome"] = "ok"
            except AssertionError as e: res["outcome"] = "assert"; res["error"] = (str(e) or traceback.format_exc().strip().splitlines()[-2].strip())[:300]
            finally: EP.produce = real
        else:                                                                       # the recipe of the end-to-end test in tests/test_v12_org.py
            core._store = core.LocalStore(os.path.join(work, "sheet.json")); core._store.ensure_tabs(); core._settings_cache = None
            for k, v in TEST_SETTINGS.items(): core.set_setting(k, v)
            if not org: core.set_setting("ORG_ON", "FALSE")
            V.KokoroBackend = lambda blend: ToneVoice()
            MG.setup(); core.set_setting("VOICE", "C")
            if not org: core.set_setting("ORG_ON", "FALSE")
            slot = (core.now_utc() + dt.timedelta(hours=slot_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
            r = EP.produce(slot, episode_id=ep)
            res["problems"] = [str(p) for p in (r.get("problems") or [])]
            if r.get("ok") and r.get("episode") == ep and os.path.exists(str(r.get("master") or "")): res["outcome"] = "ok"
            elif r.get("held"): res["outcome"] = "held"
            else: res["outcome"] = "odd"; res["error"] = json.dumps(r, default=str)[:300]
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
    return {"n": len(results), "outcomes": by, "bad_ids": sorted(r["id"] for r in results if r["outcome"] != "ok"), "fail_classes": {k: sorted(set(v)) for k, v in sorted(fails.items())},
            "warn_classes": {k: len(v) for k, v in sorted(warn.items())}, "degraded_classes": {k: len(v) for k, v in sorted(deg.items())}, "owner_message_kinds": {k: len(v) for k, v in sorted(own.items())}}

def main(argv=None):
    p = argparse.ArgumentParser(description="Sweep the fake pipeline over fixed episode ids.")
    p.add_argument("--n", type=int, default=40); p.add_argument("--offset", type=int, default=0); p.add_argument("--ids", default="")
    p.add_argument("--org", choices=("on", "off"), default="on"); p.add_argument("--mode", choices=("produce", "rehearsal"), default="produce")
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
