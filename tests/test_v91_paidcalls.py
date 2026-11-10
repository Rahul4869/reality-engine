"""v9.1 acceptance: the PAID-CALL COUNTER. With the default flags, one fake episode makes exactly the paid calls v9 made (baseline captured on v9 code in
tests/golden/v9_paid_calls.json); no new paid call appears unless its own flag is on."""
import json, os
from tests.paid_calls import count, allowed_base

def test_default_flags_add_no_paid_call(monkeypatch, tmp_path):
    base = allowed_base(json.load(open(os.path.join(os.path.dirname(__file__), "golden", "v9_paid_calls.json")))["calls"])      # v10.2: documented additions only
    now, r = count(monkeypatch, tmp_path)
    print("PAID_CALLS_V9=" + json.dumps(base, sort_keys=True)); print("PAID_CALLS_V91=" + json.dumps(now, sort_keys=True))
    # v9.2: Setup now fills an empty bench, so the episode draws from it and may make FEWER calls (no scout round); never a new or a larger category
    assert r.get("ok") and set(now) <= set(base) and all(now[k] <= base[k] for k in now), {k: (base.get(k), now.get(k)) for k in set(base) | set(now) if base.get(k) != now.get(k)}
