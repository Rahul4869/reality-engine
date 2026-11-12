"""v12 B0b - baseline re-check. The rules this batch added, each proven both ways: no test may skip on GitHub's Checks (tests/skip_policy.py + the
workflow), a red Checks run names its cause on the public run page (tools/ci_report.py), the episode-id sweep (tools/sweep.py) is deterministic and
honest about every hold, crash and warning class. The v9 golden-frame comparison that now always runs is proven in tests/test_v91_core.py."""
import json, os
import pytest
import yaml
from tests import skip_policy as SP
from tools import ci_report as CI, sweep as SW

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _checks(): return yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "checks.yml"), encoding="utf-8"))["jobs"]["guard_and_rehearsal"]["steps"]
def _step(word): return next(s for s in _checks() if str(s.get("name", "")).startswith(word))

# ------------------------------------------------------------------ the no-skip rule
def test_a_strict_run_fails_on_one_skip_and_names_it_and_a_normal_run_only_reports():
    skips = ["tests/test_x.py::test_needs_node: node not installed"]
    ok, msg = SP.verdict(skips, env={"WI_NO_SKIPS": "1"}); assert ok is False and "NO-SKIP RULE" in msg and "test_needs_node" in msg and "node not installed" in msg
    ok, msg = SP.verdict(skips, env={}); assert ok is True and "test_needs_node" in msg and "NO-SKIP RULE" not in msg
    assert SP.verdict([], env={"WI_NO_SKIPS": "1"}) == (True, "")                      # nothing skipped: green and silent, strict or not
    assert SP.strict({"WI_NO_SKIPS": "true"}) and not SP.strict({"WI_NO_SKIPS": "0"}) and not SP.strict({"WI_NO_SKIPS": ""}) and not SP.strict({})

def test_the_test_run_itself_applies_the_rule(monkeypatch):
    import tests.conftest as C
    class Rep:
        def __init__(self, skipped, xfail=False):
            self.skipped = skipped; self.nodeid = "tests/test_y.py::test_z"; self.longrepr = ("tests/test_y.py", 3, "Skipped: some tool is missing")
            if xfail: self.wasxfail = "known"
    class Session: exitstatus = 0
    kept = list(C._SKIPPED); C._SKIPPED.clear()
    try:
        C.pytest_runtest_logreport(Rep(False)); C.pytest_runtest_logreport(Rep(True, xfail=True)); assert C._SKIPPED == []      # a pass and an expected failure are not skips
        monkeypatch.setenv("WI_NO_SKIPS", "1"); s = Session(); C._no_skip_verdict(s); assert s.exitstatus == 0                    # strict and nothing skipped: stays green
        C.pytest_runtest_logreport(Rep(True)); assert C._SKIPPED == ["tests/test_y.py::test_z: Skipped: some tool is missing"]
        s = Session(); C._no_skip_verdict(s); assert s.exitstatus == 1                                                             # strict + one skip: the run is RED
        monkeypatch.delenv("WI_NO_SKIPS"); s = Session(); C._no_skip_verdict(s); assert s.exitstatus == 0                          # the same skip on a normal machine: reported only
        monkeypatch.setenv("WI_NO_SKIPS", "1"); s = Session(); s.exitstatus = 2; C._no_skip_verdict(s); assert s.exitstatus == 2  # never hides another failure code
    finally:
        C._SKIPPED.clear(); C._SKIPPED.extend(kept)

def test_a_failed_test_leaves_the_episode_ids_that_reproduce_it():
    import tests.conftest as C
    class Rep:
        skipped = False; nodeid = "tests/test_integration.py::test_full"; longrepr = "boom"
        def __init__(self, failed, out=""): self.failed = failed; self.capstdout = out; self.capstderr = ""
    kept = list(C._FAILED_IDS); C._FAILED_IDS.clear()
    try:
        C.pytest_runtest_logreport(Rep(False, "[INFO] setup EP202611101356: contract script: 22/22 pass")); assert C._FAILED_IDS == []          # a passing test leaves nothing
        C.pytest_runtest_logreport(Rep(True, "no id here")); assert C._FAILED_IDS == []
        log = "[INFO] setup EP202611101356: draw\n[WARN] setup EP202611101356: contract final: 18/19 pass; FAILED: aliveness\n[INFO] x EP202611101401: y"
        C.pytest_runtest_logreport(Rep(True, log)); C.pytest_runtest_logreport(Rep(True, log))
        assert C._FAILED_IDS == ["tests/test_integration.py::test_full: EP202611101356, EP202611101401"]                 # once, every id it used
        red = CI.unit("FAILED tests/test_integration.py::test_full - assert 0\nEPISODE-IDS " + C._FAILED_IDS[0] + "\n1 failed, 5 passed in 9.00s\n", 1)
        assert ("error", "Unit tests", "EPISODE-IDS tests/test_integration.py::test_full: EP202611101356, EP202611101401") in red
    finally:
        C._FAILED_IDS.clear(); C._FAILED_IDS.extend(kept)

def test_githubs_checks_run_strict_and_report_and_keep_the_real_exit_code():
    unit = _step("Unit tests"); reh = _step("Free rehearsal"); rep = _step("Repeat the unit tests")
    assert str(unit["env"]["WI_NO_SKIPS"]) == "1" and str(rep["env"]["WI_NO_SKIPS"]) == "1"
    for step, kind, log in ((unit, "unit", "unit.log"), (reh, "rehearsal", "rehearsal.log")):
        run = step["run"]; lines = [l.strip() for l in run.splitlines() if l.strip()]
        assert lines[0] == "set +e" and "rc=${PIPESTATUS[0]}" in run and f'tee "$RUNNER_TEMP/{log}"' in run          # the test's own exit code is kept, not tee's
        assert f'python tools/ci_report.py {kind} "$RUNNER_TEMP/{log}" "$rc"' in run and lines[-1] == 'exit "$rc"'      # reported, then the step ends with the REAL code
    assert "python -m pytest tests -q" in unit["run"] and "python -m whatifs.cli rehearsal" in reh["run"]
    assert not any("secrets." in str(s.get("env", "")) for s in (unit, reh, rep))                                       # these steps hold no key, so an annotation cannot leak one
    pip = next(s["run"] for s in _checks() if "pip install" in str(s.get("run", "")))
    assert "python-docx" in pip and any("setup-node" in str(s.get("uses", "")) for s in _checks())                     # what the two machine-dependent tests need is installed there

# ------------------------------------------------------------------ a red run names its cause in public
UNIT_RED = """........F...s..
=================================== FAILURES ===================================
E   AssertionError: 36 of 36 frames differ from the v9 golden frames
=========================== short test summary info ============================
FAILED tests/test_v91_core.py::test_golden_frames_flag_off_equals_v9 - AssertionError: 36 of 36 frames differ
FAILED tests/test_v94a.py::test_cap - assert 5 <= 4
ERROR tests/test_x.py::test_y - RuntimeError: boom

NO-SKIP RULE: 1 test(s) skipped on a strict run (WI_NO_SKIPS=1). Install what the test needs or fix the test - never leave it skipping:
  SKIPPED tests/test_v94b.py::test_worker: node not installed
2 failed, 1101 passed, 1 skipped, 1 error in 1502.11s (0:25:02)
"""
UNIT_GREEN = "........................\n1113 passed in 1498.20s (0:24:58)\n"
REH_RED = """setup ok
[INFO] rehearsal EP202611101111: contract script: 21/21 pass
[WARN] rehearsal EP202611101111: contract final: 17/18 pass; FAILED: promise_paid
[WARN] rehearsal EP202611101111: contract final promise_paid: promise first shown at 44.7 s (limit 30 s)
produce ok {"ok": false, "held": true}
Traceback (most recent call last):
  File "tools/rehearsal.py", line 40, in run
KeyError: 'master'
"""
REH_GREEN = """setup ok
[INFO] rehearsal EP202611101112: contract script: 22/22 pass
[INFO] rehearsal EP202611101112: contract final: 19/19 pass
[INFO] rehearsal EPTABLE: contract script: 3/22 pass
REHEARSAL: GREEN
"""

def test_a_red_unit_run_names_every_failed_and_skipped_test_and_a_green_one_shows_the_totals():
    red = CI.unit(UNIT_RED, 1); msgs = [m for _, _, m in red]
    assert all(level == "error" and title == "Unit tests" for level, title, _ in red)
    assert any("test_golden_frames_flag_off_equals_v9" in m and "36 of 36 frames differ" in m for m in msgs) and any("test_cap" in m for m in msgs) and any(m.startswith("ERROR tests/test_x.py") for m in msgs)
    assert any(m.startswith("NO-SKIP RULE") for m in msgs) and any("SKIPPED tests/test_v94b.py::test_worker: node not installed" in m for m in msgs)
    assert "2 failed, 1101 passed, 1 skipped, 1 error" in msgs[-1]
    green = CI.unit(UNIT_GREEN, 0); assert green == [("notice", "Unit tests", "1113 passed in 1498.20s (0:24:58)")]
    crash = CI.unit("Fatal Python error: Segmentation fault\n", 139); assert crash[0][0] == "error" and "exit code 139" in crash[0][2] and "Segmentation fault" in crash[0][2]
    many = CI.unit("\n".join(f"FAILED tests/t.py::t{i} - x" for i in range(30)) + "\n30 failed in 3.00s\n", 1)
    assert len(many) == CI.MAX_ERRORS + 2 and "and 22 more" in many[-2][2] and len(many) <= 10                          # never more than the run page shows

def test_a_red_rehearsal_names_the_check_the_reason_and_the_episode_id_that_reproduces_it():
    red = CI.rehearsal(REH_RED, 1); msgs = [m for _, _, m in red]
    assert all(level == "error" and title == "Rehearsal" for level, title, _ in red)
    assert any("contract final promise_paid: promise first shown at 44.7 s (limit 30 s)" in m for m in msgs) and "KeyError: 'master'" in msgs
    assert "EP202611101111" in msgs[-1] and "python tools/sweep.py --mode rehearsal --ids EP202611101111" in msgs[-1]
    green = CI.rehearsal(REH_GREEN, 0)
    assert green == [("notice", "Rehearsal", "REHEARSAL: GREEN, episode id EP202611101112; contract script: 22/22 pass; contract final: 19/19 pass")]
    assert CI.rehearsal(REH_GREEN, 1)[-1][0] == "error" and CI.rehearsal(REH_GREEN.replace("REHEARSAL: GREEN", ""), 0)[-1][0] == "error"      # green needs BOTH the exit code and the final line
    assert "episode id unknown" in CI.rehearsal("Killed\n", 137)[-1][2]

def test_the_job_summary_holds_the_full_list_and_is_written_only_where_the_runner_asks(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)                                                            # on GitHub this test must not write into the real run's summary
    log = "\n".join(f"FAILED tests/t.py::t{i} - x" for i in range(30)) + "\n30 failed in 3.00s\n"
    assert CI.summary("unit", log, 1) is False                                                                         # no file named: nothing written anywhere
    p = tmp_path / "summary.md"; assert CI.summary("unit", log, 1, path=str(p)) is True and CI.summary("rehearsal", REH_GREEN, 0, path=str(p)) is True
    t = p.read_text(encoding="utf-8"); assert "### Unit tests: RED" in t and t.count("FAILED tests/t.py::t") == 30 and "### Rehearsal: GREEN" in t and "EP202611101112" in t
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "env.md")); u = tmp_path / "u.log"; u.write_text(UNIT_GREEN, encoding="utf-8")
    assert CI.main(["unit", str(u), "0"]) == 0 and "### Unit tests: GREEN" in (tmp_path / "env.md").read_text(encoding="utf-8")

def test_annotations_are_escaped_cut_and_reporting_never_changes_the_result(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    c = CI.command("error", "Unit tests: a, b", "50% done\nsecond line"); assert c == "::error title=Unit tests%3A a%2C b::50%25 done%0Asecond line"
    assert len(CI.command("notice", "t", "x" * 5000)) < 700
    p = tmp_path / "unit.log"; p.write_text(UNIT_RED, encoding="utf-8")
    assert CI.main(["unit", str(p), "1"]) == 0; out = capsys.readouterr().out.splitlines()                             # exit 0: the workflow step ends with the tests' own code
    assert out and all(l.startswith("::error title=Unit tests::") for l in out)
    assert CI.main(["rehearsal", str(tmp_path / "missing.log"), "1"]) == 0 and "::error title=Rehearsal::" in capsys.readouterr().out      # a missing log is itself reported
    assert CI.main(["unit"]) == 2 and CI.main(["other", "a", "0"]) == 2

# ------------------------------------------------------------------ the sweep
def test_sweep_ids_are_fixed_valid_future_and_all_different():
    import datetime as dt
    ids = SW.fixed_ids(40); assert ids == SW.fixed_ids(40) and len(set(ids)) == 40 and ids[0] == "EP209901010900" and ids[:10] == SW.fixed_ids(10)
    for i in ids: assert dt.datetime.strptime(i[2:], "%Y%m%d%H%M").year == 2099                                        # a real date in the future: the organisation's checks judge it
    assert len({i[-2:] for i in ids}) > 20 and len({i[8:10] for i in ids}) > 15 and SW.fixed_ids(8, 40)[0] not in ids   # minutes and hours move; an offset gives fresh ids

def test_warning_classes_fold_numbers_ids_and_quotes():
    a = SW.warn_class("EP209901010900: retention gate: 3 problem(s): 'opening' at 44.7 s"); b = SW.warn_class("EP209902020202: retention gate: 1 problem(s): 'verdict' at 9 s")
    assert a == b and "EP#" in a and "44" not in a
    assert SW.warn_class("script length 412 outside 500-900") != SW.warn_class("atmosphere over its time budget (31% > 25%)")

def test_sweep_summary_counts_every_hold_crash_and_class():
    rs = [{"id": "A", "outcome": "ok", "warn": {"WARN: x #": 2}, "owner": [], "fails": [], "problems": []},
          {"id": "B", "outcome": "held", "problems": ["contract:promise_paid"], "fails": [["promise_paid", "final", "promise first shown at 44.7 s"]], "warn": {"WARN: x #": 1}, "owner": ["hold"], "degraded": ["judge unavailable"]},
          {"id": "C", "outcome": "crash", "error": "KeyError: 'master'", "runs_bad": ["D6.render:breach"], "memos_open": ["problem_memo>['D6']:render crashed"]}]
    s = SW.summary(rs)
    assert s["n"] == 3 and s["outcomes"] == {"ok": 1, "held": 1, "crash": 1} and s["bad_ids"] == ["B", "C"]
    assert s["fail_classes"]["promise_paid@final"] == ["B"] and s["fail_classes"]["problem:contract:promise_paid"] == ["B"] and s["fail_classes"]["org:D6.render:breach"] == ["C"]
    assert s["warn_classes"] == {"WARN: x #": 2} and s["owner_message_kinds"] == {"hold": 1} and s["degraded_classes"] == {"judge unavailable": 1}
    assert SW.summary([rs[0]])["bad_ids"] == []

def test_sweep_refuses_a_work_folder_inside_the_repo_and_reports_a_dead_child(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as e: SW.main(["--n", "1", "--work", os.path.join(ROOT, "sweep_work")])
    assert "OUTSIDE the repo" in str(e.value) and not os.path.exists(os.path.join(ROOT, "sweep_work"))
    class A: logs = str(tmp_path); repo = ROOT; mode = "produce"; slot_h = 10; org = "on"; timeout = 60; keep = False
    class Done: returncode = 3
    def fake_run(cmd, stdout=None, **k): stdout.write("Traceback\nImportError: no module\n"); return Done()
    monkeypatch.setattr(SW.subprocess, "run", fake_run)
    r = SW.child("EP209901010900", A, str(tmp_path / "w")); assert r["outcome"] == "crash" and "no RESULT line (exit 3)" in r["error"] and "ImportError" in r["error"]
    assert not os.path.exists(str(tmp_path / "w" / "EP209901010900"))                                                  # the episode folder never stays behind
    def good_run(cmd, stdout=None, **k): stdout.write('noise\nRESULT {"id": "EP209901010900", "outcome": "ok", "sec": 5}\n'); return Done()
    monkeypatch.setattr(SW.subprocess, "run", good_run); assert SW.child("EP209901010900", A, str(tmp_path / "w"))["outcome"] == "ok"
    def slow_run(cmd, **k): raise SW.subprocess.TimeoutExpired(cmd, 60)
    monkeypatch.setattr(SW.subprocess, "run", slow_run); assert SW.child("EP209901010900", A, str(tmp_path / "w"))["outcome"] == "timeout"

# ------------------------------------------------------------------ the tests run the library versions production runs
# Found by the first run with public annotations: GitHub's Checks installed OpenCV without bounds and got 5.0.0, while production (requirements.txt)
# pins it below 5 - every "green on GitHub" had been measured on another major version than the one that renders the videos.
import re, glob
ONLY_IN_PRODUCTION = {"kokoro", "transformers"}          # the voice engine and its models: too heavy for a test machine, replaced by stand-ins in every test

def _pins(path=None):
    out = {}
    for l in open(path or os.path.join(ROOT, "requirements.txt"), encoding="utf-8"):
        m = re.match(r"([A-Za-z0-9_.-]+)(.*)", l.split("#")[0].strip())
        if m and m.group(2).strip(): out[m.group(1).lower()] = m.group(2).replace(" ", "")
    return out

def _v(s, n=3): return tuple((list(int(x) for x in re.findall(r"\d+", s)[:n]) + [0] * n)[:n])
def _inside(version, spec):
    ops = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, "==": lambda a, b: a == b, "<": lambda a, b: a < b, ">": lambda a, b: a > b}
    return all(ops[m.group(1)](_v(version), _v(m.group(2))) for m in (re.match(r"(>=|<=|==|<|>)(.+)", p) for p in spec.split(",")) if m)

def _pip_lines():
    for f in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        for l in open(f, encoding="utf-8").read().splitlines():
            if "pip install" in l and "-r requirements.txt" not in l: yield os.path.basename(f), l.split("#")[0]

def _unpinned(lines, pins):
    bad = []
    for f, l in lines:
        for t in l.split("pip install", 1)[1].split():
            bare = t.strip("\"'"); name = re.split(r"[<>=!~]", bare)[0].lower()
            if name in pins and bare.lower() != name + pins[name]: bad.append(f"{f}: {bare} (production pins {name}{pins[name]})")
    return bad

def test_version_bounds_compare_correctly():
    assert _inside("4.14.0.94", ">=4.9,<5") and not _inside("5.0.0", ">=4.9,<5") and not _inside("4.8.1", ">=4.9,<5")
    assert _inside("2.0.2", ">=1.26,<2.1") and not _inside("2.1.0", ">=1.26,<2.1") and _inside("0.13.1", ">=0.12,<0.14") and not _inside("0.14", ">=0.12,<0.14")

def test_every_workflow_installs_a_pinned_package_with_the_production_bounds():
    pins = _pins(); assert {"numpy", "opencv-python-headless", "pillow", "requests", "soundfile"} <= set(pins)
    lines = list(_pip_lines()); assert len(lines) >= 13 and any(f == "checks.yml" for f, _ in lines)
    assert _unpinned(lines, pins) == []
    # the other way round: the line GitHub's Checks used until this batch is caught, and so is a wrong bound
    old = [("checks.yml", '      - run: pip install -q "numpy>=1.26,<2.1" opencv-python-headless pillow soundfile requests pytest')]
    bad = _unpinned(old, pins); assert len(bad) == 4 and any("opencv-python-headless (production pins opencv-python-headless>=4.9,<5)" in b for b in bad)
    assert _unpinned([("x.yml", 'pip install -q "opencv-python-headless>=4.9,<6"')], pins) and not _unpinned([("x.yml", "pip install -q pytest pyyaml")], pins)

def test_this_machine_runs_the_library_versions_production_pins():
    import importlib.metadata as MD
    pins = _pins(); seen = {}
    for name, spec in pins.items():
        try: seen[name] = MD.version(name)
        except MD.PackageNotFoundError:
            assert name in ONLY_IN_PRODUCTION, f"{name} is pinned for production but not installed on this test machine"
            continue
        assert _inside(seen[name], spec), f"{name} {seen[name]} is outside the production pin {spec}: the tests would measure another version than the one that makes the videos"
    assert {"numpy", "opencv-python-headless"} <= set(seen)
    import cv2, numpy
    assert _inside(cv2.__version__, pins["opencv-python-headless"]) and _inside(numpy.__version__, pins["numpy"])      # what is imported, not only what is installed

# ------------------------------------------------------------------ no Settings cell that nothing reads
def test_every_settings_cell_is_read_by_code_or_marked_not_active():
    from whatifs import truth as T, core
    T.reset(); assert T.settings_issues() == []
    unread = set(T.unread_settings()); assert unread == set(T.UNREAD_SETTINGS) and len(unread) <= T.UNREAD_SETTINGS_MAX <= 8          # the list only shrinks
    assert set(T.settings_cells()) == set(core.DEFAULTS)                                                                # the source reader sees every cell of the table
    for k in unread: assert core.DEFAULTS[k][1].startswith(T.NOT_ACTIVE), k                                             # the Sheet and SYSTEM.md tell the truth meanwhile
    assert not [k for k, v in core.DEFAULTS.items() if v[1].startswith(T.NOT_ACTIVE) and k not in unread]
    for k in ("PRICE_OPUS_IN", "ATMOS_FOG_ON", "EFFORT_JUDGE", "SHORT_MAX_S_S3", "FPS", "VOICE", "ORG_ON"): assert k in core.DEFAULTS and k not in unread      # names the code BUILDS count as read
    doc = open(os.path.join(ROOT, "docs", "CURRENT", "SYSTEM.md"), encoding="utf-8").read()
    assert all(f"  - `{k}`: " in doc for k in unread) and f"{len(unread)} cells are read by NO code" in doc              # the generated doc names each one

def test_no_department_owns_a_lever_that_nothing_reads():
    from whatifs import truth as T, core
    from whatifs.org import registry as REG
    unread = set(T.unread_settings()); levers = [(d, k) for d, spec in REG.DEPTS.items() for k in spec.get("levers", ())]
    assert len(levers) > 20 and not [(d, k) for d, k in levers if k not in core.DEFAULTS or k in unread]               # the Execution Engine must never turn a dead cell

def test_no_unused_tab_and_no_uncalled_function_beyond_the_listed_ones():
    from whatifs import truth as T, core
    T.reset(); assert T.wiring_issues() == []
    tabs, funcs = T.unused(); assert set(tabs) == set(T.UNUSED_TABS) and set(funcs) == set(T.UNWIRED_FUNCTIONS)
    assert len(tabs) <= T.UNUSED_TABS_MAX <= 2 and len(funcs) <= T.UNWIRED_FUNCTIONS_MAX <= 10                          # both lists only shrink
    assert set(T.table_keys(None, "TABS")) == set(core.TABS) and all(t in core.TABS for t in T.UNUSED_TABS)            # the source reader sees every tab
    for f in T.UNWIRED_FUNCTIONS:                                                                                       # every listed function really exists where the list says
        path, name = f.split(":"); assert f"def {name}(" in open(os.path.join(ROOT, *path.split("/")), encoding="utf-8").read(), f
    doc = open(os.path.join(ROOT, "docs", "CURRENT", "SYSTEM.md"), encoding="utf-8").read()
    assert all(f"  - `{x}`: " in doc for x in list(T.UNUSED_TABS) + list(T.UNWIRED_FUNCTIONS))

def test_a_new_unused_tab_or_uncalled_function_fails_and_a_wired_one_must_leave_the_list(tmp_path, monkeypatch):
    from whatifs import truth as T
    cells = {"USED_ONE": ("1", "a note")}; tabs = {"Used_Tab": ["a"], "Ghost_Tab": ["a"]}
    code = 'def used(st, S): return st.rows("Used_Tab"), S("USED_ONE")\nX = used\ndef ghost_fn(): return 1\n'
    monkeypatch.setattr(T, "UNREAD_SETTINGS", {}); monkeypatch.setattr(T, "UNUSED_TABS", {}); monkeypatch.setattr(T, "UNWIRED_FUNCTIONS", {})
    root = _tree(tmp_path, cells, code, tabs=tabs); T.reset()
    assert T.unused(root) == (["Ghost_Tab"], ["whatifs/work.py:ghost_fn"])
    bad = T.wiring_issues(root); assert len(bad) == 2 and any(b.startswith("Ghost_Tab: this Sheet tab is used by no production code") for b in bad)
    assert any(b.startswith("whatifs/work.py:ghost_fn: this function is used by no production code") for b in bad) and len([b for b in T.issues(root) if "used by no production code" in b]) == 2
    monkeypatch.setattr(T, "UNUSED_TABS", {"Ghost_Tab": "never built"}); monkeypatch.setattr(T, "UNWIRED_FUNCTIONS", {"whatifs/work.py:ghost_fn": "never called"}); T.reset()
    assert T.wiring_issues(root) == []                                                                                  # listed with what is true: accepted
    monkeypatch.setattr(T, "UNWIRED_FUNCTIONS_MAX", 0); monkeypatch.setattr(T, "UNUSED_TABS_MAX", 0)
    assert len([b for b in T.wiring_issues(root) if "may only shrink" in b]) == 2                                       # neither list may grow
    monkeypatch.setattr(T, "UNWIRED_FUNCTIONS_MAX", 10); monkeypatch.setattr(T, "UNUSED_TABS_MAX", 2)
    root = _tree(tmp_path, cells, code + 'def later(st): return ghost_fn(), st.rows("Ghost_Tab")\nY = later\n', tabs=tabs); T.reset()
    bad = T.wiring_issues(root); assert len(bad) == 2 and all("used now or gone - delete the entry" in b for b in bad)  # wired: the entries must go
    T.reset()

def _tree(tmp_path, cells, code, extra=None, tabs=None):
    root = tmp_path / "repo"; (root / "whatifs").mkdir(parents=True, exist_ok=True)
    (root / "whatifs" / "core.py").write_text("DEFAULTS = {\n" + "".join(f' "{k}": ("{d}", "{n}"),\n' for k, (d, n) in cells.items()) + "}\n"
                                              + ("TABS = {\n" + "".join(f' "{t}": {json.dumps(c)},\n' for t, c in tabs.items()) + "}\n" if tabs else ""), encoding="utf-8")
    (root / "whatifs" / "work.py").write_text(code, encoding="utf-8")
    for rel, text in (extra or {}).items():
        p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
    return str(root)

def test_a_new_unread_cell_a_revived_cell_an_unmarked_note_and_a_grown_list_all_fail(tmp_path, monkeypatch):
    from whatifs import truth as T
    cells = {"USED_ONE": ("1", "a note"), "BUILT_A_ON": ("TRUE", "a layer switch"), "ON_DASH": ("x", "shown on the dashboard"), "GHOST_CELL": ("TRUE", "promises a behaviour; see USED_ONE")}
    code = 'def f(S, k):\n    """GHOST_CELL is only named in this docstring."""\n    # GHOST_CELL in a comment\n    return S("USED_ONE"), S(f"BUILT_{k}_ON")\n'
    root = _tree(tmp_path, cells, code, {"mission_control/worker.js": "const v = settings.ON_DASH;"})
    monkeypatch.setattr(T, "UNREAD_SETTINGS", {}); T.reset()
    assert T.unread_settings(root) == ["GHOST_CELL"]                                                                    # a docstring, a comment and another cell's note are not a read
    bad = T.settings_issues(root); assert len(bad) == 1 and "GHOST_CELL is read by no code" in bad[0] and bad[0].startswith("whatifs/core.py:5:")
    assert any("GHOST_CELL is read by no code" in b for b in T.issues(root))                                            # Plan Guard and check docs_current run this list
    monkeypatch.setattr(T, "UNREAD_SETTINGS", {"GHOST_CELL": "nothing reads it"}); T.reset()
    bad = T.settings_issues(root); assert len(bad) == 1 and "must start with 'NOT ACTIVE'" in bad[0]                    # listed, but the note still promises the behaviour
    cells["GHOST_CELL"] = ("TRUE", "NOT ACTIVE (no code reads this cell): nothing happens"); root = _tree(tmp_path, cells, code); T.reset()
    assert T.settings_issues(root) == []                                                                                # listed and honest: accepted
    monkeypatch.setattr(T, "UNREAD_SETTINGS_MAX", 0); assert any("may only shrink" in b for b in T.settings_issues(root)); monkeypatch.setattr(T, "UNREAD_SETTINGS_MAX", 8)
    root = _tree(tmp_path, cells, code + 'def g(S): return S("GHOST_CELL")\n'); T.reset()
    bad = T.settings_issues(root); assert len(bad) == 1 and "GHOST_CELL is read by code now - delete its UNREAD_SETTINGS entry" in bad[0]      # wired: the entry must go
    monkeypatch.setattr(T, "UNREAD_SETTINGS", {}); T.reset()
    bad = T.settings_issues(root); assert len(bad) == 1 and "is read by code but its note says 'NOT ACTIVE'" in bad[0]
    monkeypatch.setattr(T, "UNREAD_SETTINGS", {"LONG_GONE": "x"}); cells["GHOST_CELL"] = ("TRUE", "a real note"); root = _tree(tmp_path, cells, code + 'def g(S): return S("GHOST_CELL")\n'); T.reset()
    bad = T.settings_issues(root); assert len(bad) == 1 and "LONG_GONE, which is not a Settings cell any more" in bad[0]
    T.reset()
