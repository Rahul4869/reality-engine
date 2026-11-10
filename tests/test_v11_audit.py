"""v11 audit guards: things only a live run would reveal (workflow wiring), now checked on every upload."""
import glob, re
import pytest

def _wf(name): return open(f".github/workflows/{name}", encoding="utf-8").read()

def test_every_workflow_parses():
    yaml = pytest.importorskip("yaml")
    for p in glob.glob(".github/workflows/*.yml"):
        assert isinstance(yaml.safe_load(open(p, encoding="utf-8").read()), dict), p

def test_jobs_that_run_the_pipeline_can_message_the_owner_and_start_jobs():
    for p in glob.glob(".github/workflows/*.yml"):
        t = open(p, encoding="utf-8").read()
        if "GH_REPO: ${{ github.repository }}" in t:
            assert "WA_TOKEN: ${{ secrets.WA_TOKEN }}" in t and "GH_MERGE_TOKEN: ${{ secrets.GH_MERGE_TOKEN }}" in t, p

def test_tick_may_start_workflows_and_special_accepts_new_kinds():
    assert "actions: write" in _wf("pipeline.yml")
    s = _wf("special.yml"); assert re.search(r"kind:\s*\n(?:\s+\w+:.*\n)*?\s+type:\s*string", s)        # free text: short / casefiles are accepted

def test_watchdog_tick_and_concurrency_present():
    y = _wf("pipeline.yml"); assert "types: [tick]" in y and "group: tick" in y
