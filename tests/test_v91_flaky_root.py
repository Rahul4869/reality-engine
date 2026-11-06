"""v9.1 risk item: root cause of the intermittent v8.2 checkpoint-resume failure.
Root cause: episode ids have minute resolution ("EP" + YYYYmmddHHMM) and every test shares one WORK folder (and the fake Drive folder). When an earlier
test produced an episode in the SAME clock minute, its leftover output folder / fake-Drive checkpoint carried the same id into the next test. This test
forces that collision deterministically (a frozen clock) instead of waiting for it to happen by chance."""
import datetime as dt
import pytest
from whatifs import core, checkpoint as CK

FROZEN = dt.datetime(2026, 11, 5, 9, 30, 7, tzinfo=dt.timezone.utc)
# Minutes whose drawn episodes differ most (6 vs 10 beats, shortest vs longest runtime): the retry must schedule the video for every one of them.
MINUTES = [15, 23]

def _setup(monkeypatch):
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import manage as MG, episode as EP
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP, "now_utc", lambda: FROZEN)
    return (FROZEN + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

def test_same_minute_leftovers_never_leak_into_a_new_episode(monkeypatch, tmp_path):
    from whatifs import episode as EP, room as ROOM
    slot = _setup(monkeypatch)
    assert EP.produce(slot)["ok"]                                         # an earlier episode in THIS minute, then a fresh Sheet (as in the next test)
    core._store = core.LocalStore(str(tmp_path / "sheet2.json")); core._store.ensure_tabs(); _setup(monkeypatch)
    real = EP._assets; boom = {"n": 0}
    def flaky(*a, **k):
        boom["n"] += 1
        if boom["n"] == 1: raise RuntimeError("fal had a bad minute")
        return real(*a, **k)
    monkeypatch.setattr(EP, "_assets", flaky)
    with pytest.raises(RuntimeError): EP.produce(slot)
    rows = core.store().rows("Episodes"); assert rows[-1]["status"] == "FAILED" and CK.has(rows[-1])
    monkeypatch.setattr(ROOM, "run_room", lambda *a, **k: (_ for _ in ()).throw(AssertionError("the AI writing was paid for again")))
    r = EP.produce(slot); rows = core.store().rows("Episodes")
    assert r["ok"] and len(rows) == 1 and rows[0]["status"] == "SCHEDULED" and not CK.has(rows[0])

@pytest.mark.parametrize("minute", MINUTES)
def test_retry_schedules_for_differently_drawn_episodes(monkeypatch, tmp_path, minute):
    from whatifs import episode as EP, room as ROOM
    import whatifs.voice as V
    from tools.rehearsal import ToneVoice
    from whatifs import manage as MG
    fz = dt.datetime(2026, 11, 4, 3, minute, 7, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C"); monkeypatch.setattr(EP, "now_utc", lambda: fz)
    slot = (fz + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"); real = EP._assets; boom = {"n": 0}
    def flaky(*a, **k):
        boom["n"] += 1
        if boom["n"] == 1: raise RuntimeError("fal had a bad minute")
        return real(*a, **k)
    monkeypatch.setattr(EP, "_assets", flaky)
    with pytest.raises(RuntimeError): EP.produce(slot)
    monkeypatch.setattr(ROOM, "run_room", lambda *a, **k: (_ for _ in ()).throw(AssertionError("paid twice")))
    r = EP.produce(slot); rows = core.store().rows("Episodes")
    assert r["ok"] and rows[0]["status"] == "SCHEDULED", (r, rows[0].get("notes"))
