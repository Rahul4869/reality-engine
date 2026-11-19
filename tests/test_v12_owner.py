"""v12 B-OWNER - the owner's two screens: one register of every message to him, one road for every mail, alarms that can never be muted, WhatsApp
that starts three kinds of message only, his input desk, both screens showing the same, never held by his absence, the money of his messages.
Every rule is proven both ways; the real code path is run, so an unwired call is seen. The HD gate has its own file (tests/test_v12_hdgate.py)."""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ step 0: open issue 246 (GitHub's Checks job neared its 120-minute limit)
def test_checks_job_has_room():
    """The Checks job runs the whole suite in ONE process and the rehearsal; its unit tests ran up to 1 h 36 min on V4 (open issue 246), so the
    job's limit is at least 240 minutes - and under 360, GitHub's own ceiling for a job. No test, strictness or step is loosened by it."""
    job = yaml.safe_load(open(os.path.join(ROOT, ".github", "workflows", "checks.yml"), encoding="utf-8"))["jobs"]["guard_and_rehearsal"]
    assert 240 <= job["timeout-minutes"] < 360, job["timeout-minutes"]
