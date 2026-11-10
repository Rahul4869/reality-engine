"""v12 B0b - the no-skip rule. A test that skips proves nothing, and a test that skips on EVERY machine hides a broken promise: until B0b the
v9 golden-frame comparison skipped on the laptop and on GitHub alike while the v11 particle layer had changed every frame. So GitHub's Checks run
strict (WI_NO_SKIPS=1 in .github/workflows/checks.yml): one skipped test fails the run and names the test. Other machines only report their skips."""
import os

STRICT_ENV = "WI_NO_SKIPS"

def strict(env=None):
    return str((os.environ if env is None else env).get(STRICT_ENV, "")).strip().lower() in ("1", "true", "yes")

def verdict(skipped, env=None):
    """skipped = ['test id: reason', ...] -> (ok, message). ok is False only on a strict run with at least one skip; the message always names every skip."""
    skipped = [str(s) for s in skipped]
    if not skipped: return True, ""
    names = "\n".join("  SKIPPED " + s[:300] for s in skipped)
    if strict(env):
        return False, f"NO-SKIP RULE: {len(skipped)} test(s) skipped on a strict run ({STRICT_ENV}=1). Install what the test needs or fix the test - never leave it skipping:\n{names}"
    return True, f"{len(skipped)} test(s) skipped on this machine (GitHub's Checks run with {STRICT_ENV}=1 and fail on any skip):\n{names}"
