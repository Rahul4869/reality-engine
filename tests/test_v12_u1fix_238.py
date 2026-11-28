"""U1 fix 238 (B-OWNER audit J19-4, HELD): THE RULE THAT MAKES "loses nothing" TRUE HAS A TEST THE BREAK RUN CAN SEE. CE-1b's three node tests of
mission_control/test_worker.mjs (keep before dispatch; a status-only webhook; a failed put answers 503) ran only in GitHub's Checks: a second pytest
wrapper runs them by name and pins "# pass 3" and "# fail 0" (none of the three rewrites _interop_payload.json), so a break of worker.js's `keep`
is caught by proving/breaks.py."""
import os, re, shutil, subprocess
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_workers_keep_before_dispatch_holds_its_rule():
    if not shutil.which("node"): pytest.skip("node not installed")
    r = subprocess.run(["node", "--test", "--test-reporter=tap", "--test-name-pattern", "CE-1b", "mission_control/test_worker.mjs"],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    out = r.stdout + r.stderr
    assert r.returncode == 0 and re.search(r"(?m)^# pass 3$", out) and re.search(r"(?m)^# fail 0$", out), out[-800:]
