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

T0 = dt.datetime(2031, 3, 15, 12, 0, tzinfo=dt.timezone.utc)                         # plan 12 (b): the pilots' money tests run on a fixed day, never the wall clock

def _fixed_day(monkeypatch, t=T0):
    from whatifs import governor as G
    for mod in (core, FL, G): monkeypatch.setattr(mod, "now_utc", lambda: t)        # core.iso reads core.now_utc; floor and governor hold names of their own
    return t

def _cost(inr):                                                                       # one pilot session's rupees on the Cost_Log
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "FLOORPILOT", "item": "floor_gemini", "provider": "gemini", "units": "1", "inr": str(inr), "basis": "measured"}])

@pytest.mark.parametrize("review,screens", [("0", "FALSE"), ("3", "TRUE"), ("3", "FALSE")])      # U1 (F10): the review's default under BOTH TWO_SCREENS_ON values
def test_a_film_the_unmeasured_floor_refuses_goes_to_his_eye_with_the_clock_and_is_never_held(monkeypatch, setting, media, review, screens):
    from tests import test_v12_opening_e2e as E2E
    from whatifs import publish as PUB
    _start_e2e(monkeypatch, setting); setting("VIEW_FLOOR_FAIL_HOLDS", "FALSE"); setting("ORG_ON", "FALSE"); setting("CREATIVE_REVIEW_FIRST_N", review); setting("TWO_SCREENS_ON", screens)
    ep = {("0", "FALSE"): OWN_IDS[8], ("3", "TRUE"): OWN_IDS[9], ("3", "FALSE"): OWN_IDS[13]}[(review, screens)]      # code review U1FIX-b (1): each case its own whole production (one work folder a process, no cleaning)
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
        assert [x["kind"] for x in cards] == {"TRUE": ["title_pick", "scheduled", "creative_review"], "FALSE": ["creative_review"]}[screens], cards      # RULING_F10: his first three have the review's own clock (item 223); BEHAVIOUR 6 is void | RULINGS_U3u (1): with TWO_SCREENS_ON TRUE every mail is also a row of its kind (notify.mail, item 149) - the title pick (packaging.record) and the 'scheduled' notice come before the review card
        cards = [x for x in cards if x["kind"] == "creative_review"]      # RULINGS_U3u (1): the review's own card - the clock (next line) and (e) read it
        assert cards[0]["expires_at"] and cards[0]["default_action"] == {"TRUE": "approved by your silence", "FALSE": "stays private"}[screens], cards      # U1 (F10): each wording as written (item 223)
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

def test_a_refused_film_whose_hold_cell_is_armed_after_its_check_still_reaches_his_eye(monkeypatch, setting, media):
    """(code review C18, 3) The check reads VIEW_FLOOR_FAIL_HOLDS once; the workflow 'Floor kit' has its own concurrency group, so its pilot may write the cell
    TRUE beside a production, between the check and the finish. The check REPORTED the refusal (N/A), so the finish decides on the floor's status and never
    reads the cell again: the film reaches his eye with the clock, one floor_eye card - never scheduled public unseen."""
    from tests import test_v12_opening_e2e as E2E
    _start_e2e(monkeypatch, setting); setting("VIEW_FLOOR_FAIL_HOLDS", "FALSE"); setting("ORG_ON", "FALSE"); setting("CREATIVE_REVIEW_FIRST_N", "0")
    ep = OWN_IDS[11]
    real_view = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, s: FL.stand_in(os.path.join(os.path.dirname(base), "flop.mp4"), "flop") if base.endswith(os.sep + "new") else real_view(src, base, s))
    real_run = CON.run
    def run(stage, ctx, ep_, *a, **k):                                                                            # the pilot arms the hold right after the check
        r = real_run(stage, ctx, ep_, *a, **k)
        if stage == "final" and k.get("write", True) and (ctx.get("floor") or {}).get("status") == "fail": core.set_setting("VIEW_FLOOR_FAIL_HOLDS", "TRUE")
        return r
    monkeypatch.setattr(CON, "run", run)
    r = EP.produce(E2E._slot(10), episode_id=ep)
    assert r.get("ok") and not r.get("held") and S("VIEW_FLOOR_FAIL_HOLDS") == "TRUE", r
    assert _led(ep)["viewer_floor"][0] == CON.NA
    cards = [x for x in core.store().rows("Owner_Actions") if x.get("episode_id") == ep]
    assert [x["kind"] for x in cards] == ["floor_eye"] and cards[0]["default_action"] == "goes public by itself" and cards[0]["expires_at"], cards
    assert "ranked its first minute beside the video you rejected" in cards[0]["text"] and "not measured yet" in cards[0]["text"], cards[0]["text"]

def test_the_pilots_notice_says_what_the_hold_cell_holds_after_it_and_a_pilot_that_measured_nothing_says_nothing_changes(floor_on, monkeypatch, tmp_path):
    """(code review C18, 2) The workflow run with no link (the kit already filed) and a pilot that could not measure (this month's allowance already spent: no session ran): the notice
    never opens "were measured", says nothing changes, and its second sentence is read from the hold cell AFTER the pilot - armed, held for his tap; not armed,
    his silence publishes."""
    import json, sys
    from whatifs import cli
    monkeypatch.chdir(tmp_path)
    ev = tmp_path / "event.json"; ev.write_text(json.dumps({"inputs": {"link": "", "yt": ""}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(ev)); monkeypatch.setattr(sys, "argv", ["cli", "floorkit"])
    _fixed_day(monkeypatch); core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "120"); core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 120, "month": "2031-03"}))
    def told(): return [x["text"] for x in core.store().rows("Owner_Actions") if x.get("kind") == "floor_kit"]
    for cell in ("TRUE", "FALSE"):
        core.set_setting("VIEW_FLOOR_FAIL_HOLDS", cell); n = len(told()); cli.main(); new = told()[n:]
        p = json.loads(S("VIEW_FLOOR_PILOT")); assert p["sessions"] == 0 and p["measured"] is False and S("VIEW_FLOOR_FAIL_HOLDS") == cell, p
        assert len(new) == 1 and new[0].startswith("The first-time viewers could not be measured") and "Nothing changes." in new[0], new
        assert new[0].endswith("Nothing is needed from you.") and not [t for t in told() if "frozen picture in" in t and t in new], new
        assert new[0].endswith("This month's pilots have cost Rs 120 of Rs 120. Nothing is needed from you."), new           # code review C18 (8), RULINGS_U1c 4.3: the rupees
        if cell == "TRUE": assert "held for your tap" in new[0] and "published after your silence" not in new[0], new
        else: assert "published after your silence" in new[0] and "held for your tap" not in new[0], new
    core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "450"); n = len(told()); cli.main(); new = told()[n:]      # the measured wording: Rs 330 left, ten sessions of Rs 0 offline
    assert len(new) == 1 and new[0].startswith("The first-time viewers were measured"), new
    assert new[0].endswith("This month's pilots have cost Rs 120 of Rs 450. Nothing is needed from you."), new

def test_the_pilots_rupees_come_off_the_floors_month_count_in_their_own_month_only_and_its_cap_stops_it(floor_on, monkeypatch, tmp_path):
    """(code review C18, 7) The pilot's money with rupees (offline every session is Rs 0, so `pilot_inr() == r["inr"]` was 0 == 0): (a) what is left of the month's
    cap (RULINGS_U1c 4.1) under one session's cost stops the pilot after ONE session, and the cell adds this month's earlier pilot money to its own; (b) floor.run's month count takes the pilot's rupees
    off in the pilot's own month only - "the month's floor money is spent" exactly when the spend less the pilot's reaches the cap."""
    import json
    cost = _cost; _fixed_day(monkeypatch)                                                    # plan 12 (b): a fixed day, never the wall clock
    month, last = "2031-03", "2031-02"
    core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 200, "month": month})); core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "230")      # RULINGS_U1c 4.1: Rs 30 left of the month's one allowance
    real = FL.session; monkeypatch.setattr(FL, "session", lambda *a, **k: (cost(50), real(*a, **k))[1])        # each session: Rs 50 on the Cost_Log
    r = FL.pilot(str(tmp_path / "p"))
    assert r["sessions"] == 1 and r["inr"] == 50.0 and r["measured"] is False, r                                  # (a) stopped by its own cap
    assert json.loads(S("VIEW_FLOOR_PILOT"))["inr"] == 250.0 and FL.pilot_inr() == 250.0
    monkeypatch.setattr(FL, "kit", lambda out: (None, "no kit (stubbed: the money is decided before the kit)"))
    cap = FL.month_cap(); assert cap > 0; cost(cap + 50)                                                         # the month's floor spend: cap + 100
    def why(pilot):
        core.set_setting("VIEW_FLOOR_PILOT", json.dumps(pilot)); return FL.plain(FL.run(None, "EPFLOORMONEY", "", str(tmp_path / "r")))["why"]
    spent = lambda x: f"the month's floor money is spent (Rs {x:.0f} of Rs {cap:.0f})"
    assert why({"inr": 101, "month": month}).startswith("no kit (stubbed")                                       # (b) cap - 1 after the pilot's own rupees
    assert why({"inr": 100, "month": month}) == spent(cap)                                                        # the cap reached exactly
    assert why({"inr": 200, "month": last}) == spent(cap + 100) and FL.pilot_inr() == 0.0                         # last month's pilot takes nothing off
    assert why({}) == spent(cap + 100)                                                                            # never measured: nothing off

def test_a_new_kit_disarms_the_hold_until_a_pilot_measures_it(floor_on, media):
    """(code review C18, 12) The hold is armed for the kit a pilot measured: a NEW kit filed with no pilot after it (the local road `cli floorkit <file>`, or a
    workflow pilot that raised after the kit was filed) puts the cell back to REPORT - the jury is not measured on it."""
    assert FL.fail_holds() is True                                                                                # armed, as a trusted pilot leaves it
    FL.make_kit(media["canary"]["clip"])
    assert FL.fail_holds() is False and S("VIEW_FLOOR_FAIL_HOLDS") == "FALSE"

def test_every_command_a_sheet_note_names_is_a_command_of_the_cli():
    """(code review C18, 10) A note of the Sheet that says "the command <name>" names a real branch of cli.main (VIEW_FLOOR_PILOT named 'floorpilot')."""
    import inspect, re
    from whatifs import cli
    cmds = set(re.findall(r'cmd == "(\w+)"', inspect.getsource(cli.main)))
    named = [(k, n) for k, v in core.DEFAULTS.items() for n in re.findall(r"\bthe command (\w+)", str(v[1] if isinstance(v, tuple) and len(v) > 1 else ""))]
    assert named and not [x for x in named if x[1] not in cmds], named
    note = core.DEFAULTS["VIEW_FLOOR_PILOT_CAP_INR"][1]; assert "how many sessions it ran" not in note, note      # the notice counts answers, never sessions

def test_the_report_line_is_decided_on_the_result_alone(floor_on):
    """(code review C18, 3) The unit leg: a refusal's report line reads neither the hold cell nor the switch again - the cell armed after the check, or the floor
    switched off after it, the film the check reported still gets its line; a result that is no refusal gets none."""
    res = {"status": "fail", "hold": {"family": "gemini", "reason": "the frozen picture"}, "view_url": "https://drive.google.com/file/d/X/view"}
    assert FL.fail_holds() is True and FL.report_line(res).startswith("Two first-time viewers ranked its first minute beside the video you rejected - gemini:"), FL.report_line(res)
    core.set_setting("VIEW_FLOOR_ON", "FALSE"); assert "not measured yet" in FL.report_line(res)
    assert [FL.report_line(dict(res, status=s)) for s in ("pass", "void", "off")] == ["", "", ""] and FL.report_line(None) == ""

def test_a_refusal_he_waived_gets_no_report_line(floor_on):
    """(RUL-U1p) His "Publish anyway" decided the refusal: the finish marks the result waived, and a waived refusal is never reported to his eye again."""
    res = {"status": "fail", "hold": {"family": "gemini", "reason": "the frozen picture"}, "view_url": "https://drive.google.com/file/d/X/view"}
    assert FL.report_line(res) and FL.report_line(dict(res, waived=True)) == "" and FL.report_line(dict(res, waived=False)), FL.report_line(dict(res, waived=True))

def test_the_pilots_cap_is_one_allowance_for_the_month(floor_on, monkeypatch, tmp_path):
    """(code review C18, 8; RULINGS_U1c 4.1) VIEW_FLOOR_PILOT_CAP_INR is ONE allowance a calendar month: a pilot stops at what this month's earlier pilots left
    of it; a second pilot with nothing left runs no session and changes nothing; a new month starts the allowance again. A fixed day (plan 12 (b))."""
    import json
    _fixed_day(monkeypatch)
    core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 200, "month": "2031-03"})); core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "230")
    real = FL.session; monkeypatch.setattr(FL, "session", lambda *a, **k: (_cost(50), real(*a, **k))[1])        # each session: Rs 50 on the Cost_Log
    r = FL.pilot(str(tmp_path / "p1"))
    assert r["sessions"] == 1 and r["inr"] == 50.0 and json.loads(S("VIEW_FLOOR_PILOT"))["inr"] == 250.0, r       # Rs 30 left: one session of Rs 50, then stop
    r = FL.pilot(str(tmp_path / "p2")); p = json.loads(S("VIEW_FLOOR_PILOT"))                                     # the same month again: nothing left
    assert r["sessions"] == 0 and r["measured"] is False and p["inr"] == 250.0 and p["month"] == "2031-03" and S("VIEW_FLOOR_FAIL_HOLDS") == "TRUE", (r, p)
    core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 200, "month": "2031-02"}))                            # last month's pilots: a new allowance
    r = FL.pilot(str(tmp_path / "p3")); p = json.loads(S("VIEW_FLOOR_PILOT"))
    assert r["sessions"] == 5 and r["inr"] == 250.0 and p["inr"] == 250.0 and p["month"] == "2031-03", (r, p)

def test_what_is_left_for_an_owed_pilot_is_not_productions_money(floor_on, monkeypatch):
    """(code review C18, 8; RULINGS_U1c 4.2) While a kit is on file (VIEW_FLOOR_CANARY) and VIEW_FLOOR_PILOT holds no measurement, what is left of the month's
    pilot allowance is held back from production's money (governor.production_room_inr, which month_fit reads); a measured pilot, no kit or the floor off hold
    nothing. A fixed day (plan 12 (b))."""
    import json
    from whatifs import governor as G
    _fixed_day(monkeypatch); kit = json.dumps({"file": "floor_canary.mp4", "sha": "0" * 64, "yt": "", "made": "2031-03-01"})
    core.set_setting("VIEW_FLOOR_CANARY", kit); core.set_setting("VIEW_FLOOR_PILOT", ""); assert FL.on() is True
    core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "0"); room0 = G.production_room_inr(); assert FL.pilot_left_inr() == 0.0
    core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "450")
    assert FL.pilot_left_inr() == 450.0 and round(room0 - G.production_room_inr(), 2) == 450.0, (room0, G.production_room_inr())
    core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 200, "month": "2031-03", "measured": False})); assert FL.pilot_left_inr() == 250.0
    assert round(room0 - G.production_room_inr(), 2) == 250.0
    core.set_setting("VIEW_FLOOR_PILOT", json.dumps({"inr": 200, "month": "2031-03", "measured": True})); assert FL.pilot_left_inr() == 0.0
    core.set_setting("VIEW_FLOOR_PILOT", ""); core.set_setting("VIEW_FLOOR_CANARY", ""); assert FL.pilot_left_inr() == 0.0          # no kit on file: no pilot is owed
    core.set_setting("VIEW_FLOOR_CANARY", kit); core.set_setting("VIEW_FLOOR_ON", "FALSE"); assert FL.pilot_left_inr() == 0.0    # the floor off
    core.set_setting("VIEW_FLOOR_ON", "TRUE"); core.set_setting("VIEW_FLOOR_PILOT_CAP_INR", "300")      # code review U1FIX-b (9): a fault FAILS CLOSED
    def fault(*a, **k): raise RuntimeError("planted: the pilot's cell cannot be read")
    monkeypatch.setattr(FL, "pilot_inr", fault)
    assert FL.pilot_left_inr() == 300.0 and round(room0 - G.production_room_inr(), 2) == 300.0, (room0, G.production_room_inr())      # the WHOLE allowance held
    monkeypatch.setattr(FL, "S", fault)                                                                    # no cell readable at all: the code's own allowance
    assert FL.pilot_left_inr() == float(core.DEFAULTS["VIEW_FLOOR_PILOT_CAP_INR"][0]) == 450.0

def test_a_whole_production_asks_every_place_scenes_start_picture_with_nobody_in_the_films_look(monkeypatch, setting):
    """Audit V1c F7 (RULINGS_U1c 5.2; FIX-C18 round 3): ONE whole offline production in F1 - its row puts nobody on screen (formats.py: "cast": False), so
    with CAST_BY_FORMAT_ON anim.apply writes the world "place" - with a recorder around atmosphere.with_directive that calls through. The picture model is
    down for a place scene's start picture (as the unit test's gemini_fails), so each is asked on the fall-back's road, media.still, whose directive is the
    cut that can lose NOBODY (Google's road sends picture_request untouched). (i) the plan holds a place scene; (ii) for EVERY one, the text its start
    picture was really asked with was recorded, and what with_directive returned for it holds NOBODY, the lock once and the look words once (the unit test
    tests/test_v12_floor.py::test_a_place_scene_is_asked_in_the_films_look_on_both_roads_of_its_start_picture, on the production's own texts);
    (iii) as many recorded texts as place scenes in the plan."""
    import re, threading
    from tests import test_v12_opening_e2e as E2E
    from whatifs import anim as AN, atmosphere as AT
    _start_e2e(monkeypatch, setting); setting("CAST_BY_FORMAT_ON", "TRUE"); ep = OWN_IDS[12]
    plans, asked, sent, here = [], {}, {}, threading.local()                  # the pictures are bought in threads: a start picture's text is tied to its shot per thread
    real_apply, real_sf, real_gem, real_wd = AN.apply, AN.start_frame, AN.gemini_image, AT.with_directive
    def apply_(shots, *a, **k):
        out = real_apply(shots, *a, **k); plans.append([i for i, s in enumerate(shots) if AN.place_scene(s)]); return out
    def start_frame(shot, path, *a, **k):
        i = int(re.search(r"img(\d{3})", os.path.basename(path)).group(1)); here.i = i if AN.place_scene(shot) else None
        if here.i is not None: asked.setdefault(i, []).append(AN.picture_request(shot, str((shot.get("anim") or {}).get("line") or ""), k.get("aspect", a[2] if len(a) > 2 else "16:9")))
        try: return real_sf(shot, path, *a, **k)
        finally: here.i = None
    def gem(prompt, *a, **k):
        if AN.NOBODY in str(prompt): raise RuntimeError("the picture model is down")
        return real_gem(prompt, *a, **k)
    def with_directive(prompt, *a, **k):
        out = real_wd(prompt, *a, **k)
        if getattr(here, "i", None) is not None: sent.setdefault(here.i, []).append((prompt, out))
        return out
    monkeypatch.setattr(AN, "apply", apply_); monkeypatch.setattr(AN, "start_frame", start_frame); monkeypatch.setattr(AN, "gemini_image", gem)
    monkeypatch.setattr(AT, "with_directive", with_directive)
    r = EP.produce(E2E._slot(10), episode_id=ep)
    lock, sw = str(S("STYLE_LOCK") or "").strip(), AN.style_words(); place = plans[-1] if plans else []
    assert lock and sw and place, (lock, sw, plans, r)                                                                           # (i)
    for i in place:                                                                                                              # (ii)
        assert len(sent.get(i, [])) == 1 and sent[i][0][0] == asked[i][-1] and sent[i][0][0].endswith(AN.NOBODY), (i, sent.get(i), asked.get(i))
        out = sent[i][0][1]
        assert AN.NOBODY in out and out.count(lock) == 1 and out.count(sw) == 1, (i, out)
    assert sum(len(v) for v in sent.values()) == len(place) and sorted(sent) == sorted(place), (sorted(sent), place)               # (iii)
