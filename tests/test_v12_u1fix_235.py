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


def test_a_kept_failed_status_of_an_alarm_is_drained_and_the_alarm_pushed_again(monkeypatch, setting):
    """U1 J 235 (RUL-U1, the leg PRE-P named as not covered): the run's side of the cure. The Worker keeps a status-only webhook as {messages: [],
    statuses: [the "failed" one]} under `inbox:wa:status:<id>`; the drain hands it to `wa.handle_inbound`, the alarm's WA_Outbox row reads "failed",
    and `notify.alarm_retry` pushes the alarm again - a status the Worker keeps and the run cannot read would be the same loss one step later."""
    from whatifs import core, dash as DS, notify as NT
    from tests.test_v12_owner import _wire, _mailbox, _window, _alarms_told
    from tests.test_v12_owner_face import _inbox
    setting("TWO_SCREENS_ON", "TRUE"); bodies = _wire(monkeypatch); _mailbox(monkeypatch); _window(False)
    a = NT.send("risk_lock", "Uploads locked: a strike was found", dedupe_key="risk|J235")
    told = [x for x in _alarms_told() if x["action_id"] == a]; assert len(told) == 1 and len(bodies) == 1, told
    wamid = told[0]["wamid"]
    kept, KV = _inbox(monkeypatch)
    kv = KV({f"inbox:wa:status:{wamid}": kept({"messages": [], "statuses": [{"id": wamid, "status": "failed", "recipient_id": "91000"}]})})
    assert DS.drain(kv) == 1 and kv.d == {}                                                         # handled once, its key deleted
    assert next(x for x in core.store().rows("WA_Outbox") if x.get("wamid") == wamid)["status"] == "failed"
    assert NT.alarm_retry() == 1 and [x["action_id"] for x in _alarms_told()] == [a, a] and len(bodies) == 2, _alarms_told()
