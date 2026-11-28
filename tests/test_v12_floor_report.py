"""v12 V1c (audit F10, DESIGN_ANSWERS_J18 ANSWER 1) - THE REPORT STATE: a film the floor's unmeasured jury refuses goes to his eye with the clock, never
held - a file of its own (tests/test_v12_floor_holds.py 1-5: the proof's runner cuts a file at 900 s; this adds two whole productions)."""
from whatifs import contract as CON
from whatifs import core
from whatifs import episode as EP
from whatifs import models as M
from whatifs import notify as NT
from whatifs.org import floor as FL
import os
import pytest
from tests.test_v12_floor import OWN_IDS, _led, _start_e2e, media, floor_on
import datetime as dt
from whatifs.core import S

@pytest.mark.parametrize("review", ["0", "3"])
def test_a_film_the_unmeasured_floor_refuses_goes_to_his_eye_with_the_clock_and_is_never_held(monkeypatch, setting, media, review):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import publish as PUB
    _start_e2e(monkeypatch, setting); setting("VIEW_FLOOR_FAIL_HOLDS", "FALSE"); setting("ORG_ON", "FALSE"); setting("CREATIVE_REVIEW_FIRST_N", review)
    ep = OWN_IDS[8] if review == "0" else OWN_IDS[9]
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, *a, **k: (mails.append(str(subject)), True)[1])
    real_view = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, s: FL.stand_in(os.path.join(os.path.dirname(base), "flop.mp4"), "flop") if base.endswith(os.sep + "new") else real_view(src, base, s))
    r = EP.produce(E2E._slot(10), episode_id=ep)
    assert r.get("ok") and not r.get("held"), r                                                                    # (a)
    assert '"VIEW_FLOOR_FAIL_HOLDS": ("FALSE"' in open(core.__file__, encoding="utf-8").read()                    # (b) the default is REPORT
    led = _led(ep)
    assert led["viewer_floor"][0] == CON.NA and led["viewer_floor"][1].startswith("reported, not held: ranked beside the rejected video: "), led["viewer_floor"]
    assert not [k for k, v in led.items() if v[0] == CON.FAIL], led                                                # (c)
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)
    assert e["status"] == "AWAITING_APPROVAL" and e.get("yt_id"), e                                                # (d)
    cards = [x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    if review == "0":
        assert [x["kind"] for x in cards] == ["floor_eye"] and cards[0]["default_action"] == "goes public by itself" and cards[0]["expires_at"], cards
    else:
        assert [x["kind"] for x in cards] == ["creative_review"], cards      # DESIGN QUESTION (J18 ANSWER 1 (3)(e)): the design asks `not cards[0].get("expires_at")`; at 7f2a815 contract.await_approval gives every creative_review card an expiry (72 h "stays private" with TWO_SCREENS_ON FALSE, "approved by your silence" with it TRUE) - the clause is left out, not adapted
    t = cards[0]["text"]                                                                                           # (e) the card says why
    assert "ranked its first minute beside the video you rejected" in t and "not measured yet" in t and f"https://drive.google.com/file/d/{ep}_view.mp4/view" in t, t
    assert not [m for m in mails if m.startswith("Video held")], mails                                             # (f)
    assert FL.again([x for x in core.store().rows("Floor_Log") if x["episode_id"] == ep])["status"] == "fail"     # (g) the prediction is kept
    if review == "0":                                                                                              # (h) his silence publishes, by the eye's own road
        NT.expire_defaults(now=core.now_utc() + dt.timedelta(hours=21))
        assert next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep)["status"] == "SCHEDULED"

def test_the_pilot_measures_the_judges_on_the_kit_alone_and_arms_the_hold_only_on_a_measured_q(floor_on, monkeypatch, media, tmp_path):
    """(audit F11, DESIGN_ANSWERS_J18 ANSWER 2) floor.pilot: ten ordinary sessions on the kit alone - q on the clear pair {C, Z} arms or disarms the hold,
    the close pair {N, C} is the canary's SECOND minute (filed with the kit); one notice that ends "Nothing is needed from you."."""
    import json, sys
    from whatifs import release as REL, cli
    core.set_setting("VIEW_FLOOR_FAIL_HOLDS", "FALSE"); r = FL.pilot(str(tmp_path / "p1"))                    # PLANT 1: the stand-in kit (the cell empty, offline)
    assert r["sessions"] == 10 and r["answers"] == 40 and r["q"] == 1.0, r
    assert r["close"] == "the second minute" and r["close_pass"] == 0 and r["close_families"] == 20 and r["close_agree"] == 0, r
    assert S("VIEW_FLOOR_FAIL_HOLDS") == "TRUE" and json.loads(S("VIEW_FLOOR_PILOT"))["q"] == 1.0
    assert len([x for x in core.store().rows("Floor_Log") if x["episode_id"] == "FLOORPILOT"]) == 40
    assert FL.pilot_inr() == r["inr"]
    monkeypatch.setattr(sys, "argv", ["cli", "floorkit", media["canary"]["clip"], "", "pilot"]); cli.main()         # the branch's notice (design (4)(v))
    told = [x for x in core.store().rows("Owner_Actions") if str(x.get("text") or "").startswith("The first-time viewers were measured")]
    assert len(told) == 1 and told[0]["text"].endswith("Nothing is needed from you."), told
    core.set_setting("VIEW_FLOOR_CANARY", "")
    monkeypatch.setattr(FL, "twin", lambda v, base: v)                                                             # PLANT 2: a jury that is not watching
    r = FL.pilot(str(tmp_path / "p2"))
    assert r["q"] == 0.5 and r["trusted"] is False and S("VIEW_FLOOR_FAIL_HOLDS") == "FALSE", r
    core.set_setting("VIEW_FLOOR_WATCH_S", "25"); FL.make_kit(media["canary"]["clip"])                            # PLANT 3: the second minute is filed
    k = json.loads(S("VIEW_FLOOR_CANARY")); assert {"file2", "sha2"} <= set(k), k
    monkeypatch.setattr(FL, "FAKE", False)
    v = FL.kit2(str(tmp_path / "k")); assert REL.sha(v["clip"]) == k["sha2"] and v["s"] == 25.0, v
    core.set_setting("VIEW_FLOOR_CANARY", json.dumps(dict(k, sha2="0" * 64))); assert FL.kit2(str(tmp_path / "k0")) is None
