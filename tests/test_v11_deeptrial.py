"""v11 (K163): the monthly Deep Trial. No keys, no network."""
from whatifs import core, deeptrial as DT, room as ROOM
from whatifs.sampler import draw as DRAW

def test_due_once_a_month_from_the_day(setting):
    setting("DEEP_TRIAL_ON", "TRUE"); setting("DEEP_TRIAL_DAY", "18"); setting("DEEP_TRIAL_MONTH", "")
    assert not DT.due("2026-12-12T15:00:00Z") and DT.due("2026-12-19T15:00:00Z")
    d = {"words": 1500}; assert DT.maybe(d, "EPD", "2026-12-19T15:00:00Z") and d["deep_trial"] and d["words"] == int(1500 * 1.9)
    assert not DT.due("2026-12-26T15:00:00Z") and DT.due("2027-01-20T15:00:00Z")      # once per month

def test_the_writer_brief_carries_the_three_acts_and_the_jury_room(monkeypatch, setting):
    setting("ROOM_MODE", "v2")
    import whatifs.models as M
    briefs = []; real = M.ask_many
    monkeypatch.setattr(M, "ask_many", lambda reqs, *a, **k: (briefs.extend(r["system"] for r in reqs if "COLD-OPEN ARCHETYPE" in r.get("prompt", "")), real(reqs, *a, **k))[1])
    d = DRAW("EPDT", "collective"); d["deep_trial"] = True
    ROOM.run_room(d, "EPDT")
    assert briefs and all("DEEP TRIAL" in b and "JURY ROOM" in b and b.index("DEEP TRIAL") < b.rindex("Return JSON") for b in briefs)
