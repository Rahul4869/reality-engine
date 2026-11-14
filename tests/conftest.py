"""Test setup: offline fake mode, a throw-away work folder, a fresh local store for every test. No keys, no network."""
import os, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_TMP = tempfile.mkdtemp(prefix="wi_tests_")
os.environ["WI_FAKE"] = "1"; os.environ["WI_SMALL"] = "1"; os.environ["WI_WORK"] = os.path.join(_TMP, "work")
for k in ("SHEET_ID", "G_REFRESH", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY"): os.environ.pop(k, None)
import pytest
from whatifs import core

# v12 V2d: what the older tests were written for - the hero clip model of that time at a flat price for a 5-second clip, and a cadence the month's money does not bind
OLD_CLIPS = {"CLIP_VALUE_ON": "FALSE", "SPLIT_ON": "FALSE", "FAL_HERO_MODEL": "fal-ai/kling-video/o3/standard/image-to-video", "PRICE_KLING_USD": "0.42"}
# v12 V2d-b: ... and with living stills as they were (eight flat-priced five-second clips, a clip cut by the micro-cuts, the older sound under a Short). The motion
# ladder has its own tests (test_v12_motion), the rehearsal and the sweep run it. The money tests of V2d-a switch the clip market on and keep THIS off.
OLD_MOTION = {"MOTION_LADDER_ON": "FALSE", "FAL_LIVING_MODEL": "fal-ai/ltx-video/image-to-video", "PRICE_LIVING_USD": "0.02"}
# v12 V2b: ... and with the inside of a format as it was (no voice rule, no camera path, the asks and the tease of every format, a name chip for every voice,
# the shares 70 / 30 / 0). Each entry is added in the step of the batch that adds its cell; the batch's own tests are tests/test_v12_inside.py.
OLD_INSIDE = {"INSIDE_ON": "FALSE", "ENDINGS_ON": "FALSE", "CHIP_DRAWN_ONLY_ON": "FALSE", "CAMERA_PATH_ON": "FALSE",
              "FORMAT_SHARE_F1": "70", "FORMAT_SHARE_F2": "30", "FORMAT_SHARE_F3": "0"}

@pytest.fixture(autouse=True)
def fresh_store(tmp_path):
    core._store = core.LocalStore(str(tmp_path / "sheet.json")); core._store.ensure_tabs()
    core._settings_cache = None
    with core._clock: core._cost_buf.clear(); core._session.clear()      # v8.1: spend counters are module-level, so every test starts with an empty month
    core._last_cost_flush[0] = __import__("time").time()          # v12 V2d: ... and with a FRESH flush clock - the cost log sends its rows by itself when its last sending is over 45 s old, which emptied the buffer under a test that reads it whenever a slow test had run before in the same process
    core._base["v"] = None
    from whatifs import models as _m, fakes as _f          # v8.11: cache bookkeeping and the fake cache server start empty in every test
    _m.CACHE.__init__(); _f.FAKE_ANTHROPIC.reset(); _m._models = None
    import shutil as _sh; _sh.rmtree(os.path.join(core.WORK, "_tts_cache"), ignore_errors=True)      # v9: the audio cache never leaks between tests
    core.set_setting("CREATIVE_REVIEW_FIRST_N", "0")
    core.set_setting("V11_FLIPS_DONE", "test")
    core.set_setting("FORMAT_FORCE", "F2")                      # v12 V2a: the older tests are the trial's tests; formats are tested on their own (test_v12_formats)
    core.set_setting("LADDER_ON", "FALSE")                      # v12 V2c-b: the older tests make long videos straight from the premise bench; the ladder has its own tests (test_v12_ladder), the rehearsal and the sweep walk it
    for _k, _v in list(OLD_CLIPS.items()) + list(OLD_MOTION.items()) + list(OLD_INSIDE.items()): core.set_setting(_k, _v)      # v12 V2d: the older tests buy 5-second clips of the model they were written for; the clip market and the month's split have their own tests (test_v12_money), the rehearsal and the sweep run them
    from whatifs import formats as _fm; _fm.use("")
    core.set_setting("DEEP_TRIAL_ON", "FALSE")                  # v11: the monthly Deep Trial is tested on its own (test_v11_deeptrial)                  # v11: the November allowance flip is tested on its own (test_v11_stage_a)            # v10.2: older tests expect direct scheduling; the owner review gate is tested in test_v102 + the rehearsal
    yield
    core._settings_cache = None

_SKIPPED = []          # v12 B0b: every skipped test of the run, for the no-skip rule (tests/skip_policy.py)
_FAILED_IDS = []       # v12 B0b: the episode ids a FAILED test printed. Some tests make time-based ids and the fake pipeline is seeded by the id, so the id reproduces the failure (tools/sweep.py)
def pytest_runtest_logreport(report):
    if report.skipped and not hasattr(report, "wasxfail"):
        why = report.longrepr[2] if isinstance(report.longrepr, tuple) and len(report.longrepr) == 3 else report.longrepr
        _SKIPPED.append(f"{report.nodeid}: {why}")
    if getattr(report, "failed", False):
        import re
        ids = sorted(set(re.findall(r"EP\d{12}", str(getattr(report, "capstdout", "") or "") + str(getattr(report, "capstderr", "") or ""))))
        line = f"{report.nodeid}: {', '.join(ids[:6])}"
        if ids and line not in _FAILED_IDS: _FAILED_IDS.append(line)

def _no_skip_verdict(session):
    from tests.skip_policy import verdict
    ok, msg = verdict(_SKIPPED)
    if msg: print("\n" + msg, flush=True)
    if not ok and session.exitstatus == 0: session.exitstatus = 1          # a strict run (GitHub's Checks) is RED when any test skipped; another failure code is never replaced

def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)
    for line in _FAILED_IDS: print("\nEPISODE-IDS " + line, flush=True)          # read by tools/ci_report.py: the ids go onto the public run page
    _no_skip_verdict(session)

@pytest.fixture
def setting():
    def _set(key, value): core.set_setting(key, value)
    return _set

