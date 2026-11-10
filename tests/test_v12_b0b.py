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

def test_annotations_are_escaped_cut_and_reporting_never_changes_the_result(tmp_path, capsys):
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
