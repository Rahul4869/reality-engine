"""U1 fix 235 (B-OWNER audit J19-1, HELD): AN ALARM META MARKS "failed" AFTER TAKING IT REACHES A RUN. The Worker keeps (KV, before any dispatch) and
dispatches a status-only webhook that holds "failed" (CA5-3's own words); delivered / read alone still start no run. Its node test runs here by name,
so the break run sees a break of worker.js."""
import os, re, shutil, subprocess
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_a_failed_status_of_an_alarm_reaches_a_run():
    if not shutil.which("node"): pytest.skip("node not installed")
    r = subprocess.run(["node", "--test", "--test-reporter=tap", "--test-name-pattern", "CA5-3", "mission_control/test_worker.mjs"],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    out = r.stdout + r.stderr
    assert r.returncode == 0 and re.search(r"(?m)^# pass 1$", out) and re.search(r"(?m)^# fail 0$", out), out[-800:]
