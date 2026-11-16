"""v12 V1c - the floor, his verdict and the maker's line: THE FLOOR HOLDS A FILM - two whole productions (3.10).
MOVED WORD FOR WORD from tests/test_v12_floor.py by the V1c repair (red round 1, open issues 224 and 225; the dispatcher's ruling 4 (C)):
the proof's serial runner (`shim/minitest.py`) cuts a file at 900 s, and that file took 643 s alone once all its tests ran - so its four
longest whole productions run in tests/test_v12_floor_holds.py and tests/test_v12_floor_his_word.py, two each. Every test function below is
that file's text, unchanged; its helpers, fixtures and episode ids (OWN_IDS) stay in tests/test_v12_floor.py and are imported from there."""
from whatifs import contract as CON
from whatifs import core
from whatifs import episode as EP
from whatifs import models as M
from whatifs import notify as NT
from whatifs.org import floor as FL
import os
import pytest
from tests.test_v12_floor import OWN_IDS, _led, _start_e2e, media

@pytest.mark.parametrize("org", ["TRUE", "FALSE"])
def test_a_flop_like_film_is_held_by_the_floor_alone_with_its_own_card(monkeypatch, setting, org, media):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import publish as PUB
    _start_e2e(monkeypatch, setting); setting("ORG_ON", org); ep = OWN_IDS[1] if org == "TRUE" else OWN_IDS[2]
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, *a, **k: (mails.append(str(subject)), True)[1])
    real_view = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, s: FL.stand_in(os.path.join(os.path.dirname(base), "flop.mp4"), "flop") if base.endswith(os.sep + "new") else real_view(src, base, s))
    r = EP.produce(E2E._slot(10), episode_id=ep); led = _led(ep)
    assert not r.get("ok") and r.get("held") and [k for k, v in led.items() if v[0] == CON.FAIL] == ["viewer_floor"], led
    assert led["viewer_floor"][1].startswith("ranked beside the rejected video: ")
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)
    assert e["status"] == "HOLD_QC" and not e.get("yt_id")
    cards = [x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    assert [x["kind"] for x in cards] == ["floor_hold"] and f"https://drive.google.com/file/d/{ep}_view.mp4/view" in cards[0]["text"]
    assert not [m for m in mails if m.startswith("Video held")], mails                       # one hold, ONE message: no "one click to fix" mail beside the card

def test_a_film_held_by_a_measured_check_then_refused_by_the_floor_then_published_anyway(monkeypatch, setting):
    """(V1c finish, C2; 3.10) THE WHOLE ROAD of one film over three finishes: held by a measured check (no jury paid), then the fix renders a new master and
    the floor refuses it (its own card, no mail), then his "Publish anyway" - answered from the log, no second jury, WAIVED and uploaded."""
    from tests import test_v12_opening_e2e as E2E
    from whatifs import publish as PUB
    _start_e2e(monkeypatch, setting); ep = OWN_IDS[7]
    asks = []; real_watch = M.ask_watch
    monkeypatch.setattr(M, "ask_watch", lambda *a, **k: (asks.append(a[0]), real_watch(*a, **k))[1])
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, *a, **k: (mails.append(str(subject)), True)[1])
    row = lambda: next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)
    kinds = lambda: [x["kind"] for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    # FINISH 1 - a measured check holds the film: no jury is paid
    real_features = CON.FEATURES
    monkeypatch.setattr(CON, "FEATURES", [(f[0], f[1], (lambda ctx: (CON.FAIL, "planted")), *f[3:]) if f[0] == "aliveness" else f for f in real_features])
    r = EP.produce(E2E._slot(10), episode_id=ep)
    assert r.get("held") and row()["status"] == "HOLD_QC" and len(asks) == 0, r
    assert _led(ep)["viewer_floor"] == (CON.NA, "not judged: the measured checks come first, and a film they hold is not paid a jury")
    assert kinds() == ["contract_hold"] and len([m for m in mails if m.startswith("Video held")]) == 1, mails
    # FINISH 2 - the fix renders a new master; the floor refuses it: its own card, open until he answers, no mail
    monkeypatch.setattr(CON, "FEATURES", real_features)
    real_view = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, s: FL.stand_in(os.path.join(os.path.dirname(base), "flop.mp4"), "flop") if base.endswith(os.sep + "new") else real_view(src, base, s))
    n1 = len(mails)
    r2 = EP.fix_held(ep)
    assert r2.get("held") and r2["problems"] == ["contract:viewer_floor"], r2
    assert len(asks) == 4 and kinds() == ["contract_hold", "floor_hold"], (asks, kinds())
    hold = next(x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep and x["kind"] == "floor_hold")
    assert hold["status"] == "OPEN" and hold["expires_at"] == "" and not row().get("yt_id"), hold
    new = mails[n1:]; assert len(new) == 1 and "is HELD" in new[0] and not new[0].startswith("Video held"), new      # ONE new mail: the card's own (C2 (c), ruled by finisher 4)
    # FINISH 3 - his "Publish anyway": answered from the log (no second jury), WAIVED, uploaded
    assert NT.answer(hold["id"], f"CONTRACT WAIVE {ep} viewer_floor").startswith("waived viewer_floor")
    n2 = len(mails); r3 = EP.fix_held(ep)
    assert r3.get("ok") and len(asks) == 4 and _led(ep)["viewer_floor"][0] == CON.WAIVED and row().get("yt_id"), r3
    assert "floor_eye" not in kinds() and not [m for m in mails[n2:] if m.startswith("Video held") or "is HELD" in m], mails[n2:]
