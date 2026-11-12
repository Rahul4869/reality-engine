"""v12 V2c-b2b1 THE OPENING, whole productions: a long video about a promoted Short opens on that Short's footage and pays less for it; a long video
under an override opens on pictures of its own; a long video whose footage is missing is held before any picture is paid and goes on only with the
owner's Approve. No keys, no network."""
import datetime as dt, json, os, shutil
import pytest
from whatifs import core, ladder as LAD, opening as OPEN, publish as PUB, notify as NT, manage as MG, episode as EP, render as RN, contract as CON
from tests.paid_calls import watch, V12V2CB2B_REMOVED

def _start(monkeypatch, setting):
    import whatifs.voice as V
    from tools.rehearsal import ToneVoice
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C"); setting("LADDER_ON", "TRUE")
    monkeypatch.setattr(EP, "_cleanup_work", lambda out: None)                                     # the working folder is read by the test

def _new_sheet(tmp_path, name):
    """Another channel Sheet inside one test (the offline writers write one script: a second video on the same Sheet is a copy by construction and is held for it)."""
    from whatifs import models as M, fakes as F, formats as FM
    core._store = core.LocalStore(str(tmp_path / name)); core._store.ensure_tabs(); core._settings_cache = None
    with core._clock: core._cost_buf.clear(); core._session.clear()
    core._base["v"] = None; M.CACHE.__init__(); F.FAKE_ANTHROPIC.reset(); M._models = None; FM.use("")
    for k, v in (("CREATIVE_REVIEW_FIRST_N", "0"), ("V11_FLIPS_DONE", "test"), ("FORMAT_FORCE", "F2"), ("DEEP_TRIAL_ON", "FALSE")): core.set_setting(k, v)
    MG.setup(); core.set_setting("VOICE", "C"); core.set_setting("LADDER_ON", "TRUE")

def _slot(h): return (core.now_utc() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")

def _ledger(ep): return {x["feature"]: (x["status"], str(x["evidence"])) for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep}

def _plan(ep):
    out = os.path.join(core.WORK, ep); S_ = json.load(open(os.path.join(out, "plan.json"), encoding="utf-8"))
    return out, S_, json.load(open(os.path.join(out, S_["vo"]["timeline"]), encoding="utf-8"))["units"]

def _render_log(monkeypatch):
    """What the renderer really did: every clip it played (file, frames) and the sound events it was given."""
    seen = {"clips": [], "events": []}; rc, rs = RN.clip_segment, RN.score
    monkeypatch.setattr(RN, "clip_segment", lambda clip_path, path, nframes, *a, **k: (seen["clips"].append((os.path.basename(clip_path), nframes)), rc(clip_path, path, nframes, *a, **k))[1])
    monkeypatch.setattr(RN, "score", lambda duration, seed, events, *a, **k: (seen["events"].append(list(events)), rs(duration, seed, events, *a, **k))[1])
    return seen

def test_a_long_video_opens_on_its_shorts_footage_and_one_under_an_override_on_its_own_pictures(monkeypatch, setting, tmp_path):
    from tools.sweep import climb
    _start(monkeypatch, setting); seen = _render_log(monkeypatch); A, B, sid = "EP209902010900", "EP209902080900", "SH209902010900"
    found = EP.RX.find_events                                                                      # a reaction moment is planted on the SECOND sentence: inside the opening (the sweep found one there on 1 id in 14)
    monkeypatch.setattr(EP.RX, "find_events", lambda units: [e for e in found(units) if e["i"] != 1] + [{"i": 1, "t": round(float(units[1]["start"]), 2), "end": round(float(units[1]["end"]), 2), "kind": "shock", "word": "WAIT", "line": str(units[1]["text"])[:80]}])
    assert climb(core, A) is True and LAD.row(sid)["footage"]
    paid = watch(monkeypatch); r = EP.produce(_slot(10), episode_id=A); a = dict(paid); assert r.get("ok"), r
    led = _ledger(A); assert not [k for k, v in led.items() if v[0] == "FAIL"], led
    assert led["opening_footage"][0] == "PASS" and sid in led["opening_footage"][1] and led["opening_shown"][0] == "PASS" and "frames of the finished film compared" in led["opening_shown"][1]
    assert led["hook_lab"][0] == "PASS" and f"the hook of Short {sid}" in led["hook_lab"][1] and led["viewer_promise"][0] == "PASS" and led["promise_paid"][0] == "PASS" and led["topic_ladder"][0] == "PASS"
    out, S_, units = _plan(A); shots = S_["shots"]; m = OPEN.marked(shots); b = OPEN.bounds(units); fps = RN.fps()
    assert m and m == list(range(len(m))) and b[m[-1] + 1] <= S_["opening"]["seconds"] + 1e-6 and S_["opening"]["short"] == sid and shots[0]["promise"] is True      # a prefix of the shot list, inside the footage
    hook = S_["opening"]["hook"]; assert hook and "".join(c for c in units[0]["text"].lower() if c.isalnum()).startswith("".join(c for c in hook.lower() if c.isalnum())[:30])      # the first spoken line IS the Short's hook
    played = dict(seen["clips"])
    for i in m:                                                                                    # every opening shot plays ONE clip, whole: its own cut of the footage, exactly as long as its sentence
        n = int(round(b[i + 1] * fps)) - int(round(b[i] * fps)); assert played.get(f"clip{i:03d}.mp4") == n and [c for c, _n in seen["clips"]].count(f"clip{i:03d}.mp4") == 1, (i, n, played.get(f"clip{i:03d}.mp4"))
    assert 1 in m and not [x for x in core.store().rows("Reaction_Map") if x.get("episode_id") == A and float(x.get("t") or 99) < b[m[-1] + 1]]      # no reaction effect inside the footage opening: the check above compared the film there and passed
    booms = [t for k, t in seen["events"][0] if k == "boom"]; assert sum(1 for t in booms if t < b[m[-1] + 1]) == 1 and len(booms) == 4      # one hit at second 0 for the opening, one for each of the three scenes
    assert not [i for rp in S_["rplans"] for i in rp.get("shots", []) if int(i) in m] and len(r["reels"]) >= 2                              # no cut-down is made of the Short's own footage
    assert (a.get("clip_kling"), a.get("image_ref"), a.get("text:hooks", 0)) == (3, 3, 0), a                                             # three paid scenes, three start frames, no hook lab
    assert sum(1 for c, _n in seen["clips"] if c not in {f"clip{i:03d}.mp4" for i in m}) >= 3                                             # the three scenes play too
    assert EP.produce(_slot(34), episode_id=B).get("skipped") == "ladder"                                                                 # one Short, one long video
    # ---- another Sheet without any Short: the owner overrides - that video has no Short and no footage
    _new_sheet(tmp_path, "sheet_b.json"); assert EP.produce(_slot(10), episode_id=B).get("skipped") == "ladder"
    o = LAD.override("owner", "make it anyway"); paid.clear(); seen["clips"].clear(); seen["events"].clear()
    r2 = EP.produce(_slot(10), episode_id=B); bcount = dict(paid); assert r2.get("ok"), r2
    led2 = _ledger(B); assert not [k for k, v in led2.items() if v[0] == "FAIL"], led2
    assert led2["opening_footage"][0] == CON.NA and o["id"] in led2["opening_footage"][1] and led2["opening_shown"][0] == CON.NA and "no Short and no footage" in led2["opening_shown"][1]
    assert led2["hook_lab"][0] == "PASS" and "candidates" in led2["hook_lab"][1] and led2["viewer_promise"][0] == "PASS"                   # the lab's best of ten lines, its own animated promise scene
    _o2, S2, _u2 = _plan(B); assert not OPEN.marked(S2["shots"]) and S2["opening"]["none"] == "override"
    assert (bcount.get("clip_kling"), bcount.get("image_ref")) == (4, 4) and bcount.get("text:hooks", 0) >= 1, bcount
    for k, v in V12V2CB2B_REMOVED.items(): assert bcount.get(k, 0) - a.get(k, 0) == v, (k, a.get(k, 0), bcount.get(k, 0))                 # the counter agrees: this is what the opening no longer pays
    assert a.get("image", 0) <= bcount.get("image", 0) and a.get("clip", 0) <= bcount.get("clip", 0)                                     # and nothing else got dearer

def test_a_long_video_whose_footage_is_gone_is_held_before_any_picture_and_goes_on_with_the_owners_approve(monkeypatch, setting):
    from tools.sweep import climb
    _start(monkeypatch, setting); ep, sid = "EP209903010900", "SH209903010900"
    assert climb(core, ep) is True
    PUB.drive_delete(LAD.row(sid)["footage"])                                                      # the archive is gone from Drive
    paid = watch(monkeypatch); r = EP.produce(_slot(10), episode_id=ep)
    assert r.get("held") and r["problems"] == ["contract:opening_footage"], r
    assert not paid.get("image") and not paid.get("clip_kling") and not paid.get("clip") and not paid.get("image_ref") and not paid.get("image_premium"), dict(paid)      # written and judged; no picture and no clip was paid
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep); assert e["status"] == "HOLD_QC" and "opening_footage" in e["notes"]
    led = _ledger(ep); assert led["opening_footage"][0] == "FAIL" and "could not be read" in led["opening_footage"][1] and "other pictures" in led["opening_footage"][1]
    card = [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "contract_hold" and x.get("episode_id") == ep]; assert card and "opening_footage" in card[-1]["text"]
    assert "waived opening_footage" in CON._answer({}, f"CONTRACT WAIVE {ep} opening_footage")       # his one tap: Approve anyway
    r2 = EP.produce(_slot(10), episode_id=ep, fix=True); assert r2.get("ok"), r2
    rows = [x for x in core.store().rows("Feature_Ledger") if x.get("episode_id") == ep]
    last = {x["feature"]: (x["status"], str(x["evidence"])) for x in rows}
    assert last["opening_footage"][0] == "WAIVED" and last["opening_shown"][0] == CON.NA and "approved" in last["opening_shown"][1]          # his Approve is not asked for a second time after the pictures are paid
    _o, S_, _u = _plan(ep); assert not OPEN.marked(S_["shots"])                                                                                 # it opens on pictures of its own: four scenes
    assert paid.get("clip_kling") == 4

def test_a_retry_on_another_machine_fetches_the_footage_again_and_does_not_pay_the_writing_twice(monkeypatch, setting):
    from tools.sweep import climb
    from whatifs import checkpoint as CK
    _start(monkeypatch, setting); ep, sid = "EP209904010900", "SH209904010900"; assert climb(core, ep) is True
    real = EP._assets; slot = _slot(10)
    def died(*a, **k): raise RuntimeError("the runner died before the pictures")
    monkeypatch.setattr(EP, "_assets", died); paid = watch(monkeypatch)
    with pytest.raises(RuntimeError): EP.produce(slot, episode_id=ep)
    e = next(x for x in core.store().rows("Episodes") if x["episode_id"] == ep); assert e["status"] == "FAILED" and CK.has(e) and paid.get("text:writer")      # the plan is saved; the writing was paid once
    shutil.rmtree(os.path.join(core.WORK, ep)); monkeypatch.setattr(EP, "_assets", real); paid.clear()      # another runner: nothing of the first job's folder is left
    fetched = []; rd = PUB.drive_download; monkeypatch.setattr(PUB, "drive_download", lambda fid, path: (fetched.append(str(fid)), rd(fid, path))[1])
    r = EP.produce(slot); assert r.get("ok") and r.get("episode") == ep, r                           # the retry resumes from the saved plan ...
    assert LAD.row(sid)["footage"] in fetched and not paid.get("text:writer") and not paid.get("text:hooks") and paid.get("clip_kling") == 3, (fetched, dict(paid))      # ... fetches the footage again, pays no writing twice and buys three scenes
    led = _ledger(ep); assert led["opening_footage"][0] == "PASS" and led["opening_shown"][0] == "PASS" and not [k for k, v in led.items() if v[0] == "FAIL"], led
