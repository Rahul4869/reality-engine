"""Test setup: offline fake mode, a throw-away work folder, a fresh local store for every test. No keys, no network."""
import os, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_TMP = tempfile.mkdtemp(prefix="wi_tests_")
os.environ["WI_FAKE"] = "1"; os.environ["WI_SMALL"] = "1"; os.environ["WI_WORK"] = os.path.join(_TMP, "work")
for k in ("SHEET_ID", "G_REFRESH", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY"): os.environ.pop(k, None)
import pytest
from whatifs import core

@pytest.fixture(autouse=True)
def fresh_store(tmp_path):
    core._store = core.LocalStore(str(tmp_path / "sheet.json")); core._store.ensure_tabs()
    core._settings_cache = None
    with core._clock: core._cost_buf.clear(); core._session.clear()      # v8.1: spend counters are module-level, so every test starts with an empty month
    core._base["v"] = None
    yield
    core._settings_cache = None

def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)

@pytest.fixture
def setting():
    def _set(key, value): core.set_setting(key, value)
    return _set

