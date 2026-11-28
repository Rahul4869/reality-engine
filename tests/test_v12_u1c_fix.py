"""v12 RB-U1-c FIX (RULING_U1c) PART B: the tests of PART A's fixes A2, A3 and A4 (A1's test sits in tests/test_v12_launch.py right after the
test at line 1090, as the RR asked). Helpers come from tests/test_v12_launch.py, the way test_v12_floor_his_word.py takes its own from test_v12_floor."""
from whatifs import contract as CON
from whatifs import core
import datetime as dt
import json
import pytest
from tests.test_v12_launch import NOW_SV, _p2_sheet


def test_a_tap_with_no_plan_row_is_never_told_kept(monkeypatch, setting):
    """RUL-U1c A2: his Approve of a pair video that is not clear, with NO plan row to carry it, is answered "Not kept: ..." (never "Kept"), nothing is approved,
    and his card is open again."""
    from whatifs.org import appetite as APP
    SAL, rec = _p2_sheet(monkeypatch, setting, status="AWAITING_APPROVAL")
    setting("ORG_ON", "TRUE"); setting("PALACE_ON", "TRUE"); setting("APPETITE_ON", "TRUE")
    called = []; monkeypatch.setattr(CON, "approve", lambda ep: called.append(ep) or f"approved {ep}")
    st = core.store(); st.append("Owner_Actions", [{"id": "X9", "kind": "contract_review", "episode_id": "EPF1", "status": "ANSWERED", "answered_at": "2026-01-01T00:00:00Z", "answer": "APPROVE EPF1", "dedupe_key": "review|EPF1"}])
    assert APP.plan_row("EPF1") is None or not APP.plan_row("EPF1")
    out = CON._answer({"id": "X9", "dedupe_key": "review|EPF1"}, "APPROVE EPF1")
    assert out.startswith("Not kept: the flagship waits for its Part 2") and called == [], out
    x9 = next(r for r in st.rows("Owner_Actions") if r.get("id") == "X9"); assert (x9["status"], x9["answered_at"], x9["answer"]) == ("OPEN", "", ""), x9      # RUL-LAST-U1 (RD-U1k-TG F4): contract.py:1326 clears his answer too


def test_the_early_release_row_counts_the_askers_of_its_hour(monkeypatch, setting):
    """RUL-U1c A3: the "Part 2 is public since" row to him counts the askers of the fire's own hour from the Appetite row `read` writes (ep, h, askers); with
    no such row it says the viewers were not read for that hour - never "0 viewers"."""
    from whatifs import notify as NT
    from whatifs.org import appetite as APP
    SAL, rec = _p2_sheet(monkeypatch, setting, status="AWAITING_APPROVAL")
    st = core.store(); sent = []
    monkeypatch.setattr(NT, "send", lambda kind, text, *a, **k: sent.append(text) or "sent")
    fr = json.dumps({"key": "line", "h": 5, "views": 900, "base": 400})
    st.append("Appetite_Plans", [{"ep": "EPF1", "role": "flagship", "state": "fired", "fired_read": fr}, {"ep": "EPF2", "role": "flagship", "state": "fired", "fired_read": fr}])
    st.append("Appetite", [{"ep": "EPF1", "h": 5, "askers": 3}])
    eps = {"EPF1": {"title": "T1", "yt_id": "VIDF1"}, "EPF2": {"title": "T2", "yt_id": "VIDF2"}, "EPP2": {"yt_id": "VIDP2"}}
    APP._word(APP.plan_row("EPF1"), "EPP2", "made: Part 2 is public", eps, st, NOW_SV)
    assert len(sent) == 1 and "Part 2 is public since" in sent[0] and "and 3 viewers asked for more." in sent[0], sent
    APP._word(APP.plan_row("EPF2"), "EPP2", "made: Part 2 is public", eps, st, NOW_SV)
    assert len(sent) == 2 and "Part 2 is public since" in sent[1] and "the viewers who asked for more were not read for that hour" in sent[1] and "0 viewers" not in sent[1], sent


def test_part2_with_no_cliff_on_record_fails_paid():
    """RUL-U1c A4: a Part 2 whose draw holds no cliff of Part 1 cannot be checked against it - the check FAILs (PAID), never passes on 0 of 0 words."""
    ctx = {"d": {"salvo": {"role": "part2", "cliff": ""}}, "units": [{"text": "anything", "start": 0}]}
    assert CON.p_cliffhanger(ctx) == (CON.FAIL, "PAID: Part 1's cliff is not on record in Part 2's draw - Part 2 cannot be checked against it")


# ------------------------------------------------------------------ PART D: the TG test gaps (RUL-U1c D1-D5)
def test_the_room_hands_its_early_psyche_fix_to_the_one_rewrite(monkeypatch, setting):
    """RUL-U1c D1 (TG-2, B010): the room asks `psyche.early` once and hands its feeling fix (`ps`) AND the hooks' reserve to the ONE `enforce.fix_all`
    rewrite - the merged call may never drop V4b's early fix."""
    from whatifs import manage as MG, room as ROOM, enforce as EN, hooks as HOOKS
    from whatifs.org import psyche as PSY
    from whatifs.sampler import draw as DRAW
    seen = {}
    monkeypatch.setattr(PSY, "early", lambda episode, premise, script: (["X"], "awe_scale"))

    def fix(script, wbrief, spine, episode, fmt="long", reserve_s=0.0, ps=None):
        seen.update(ps=ps, reserve=reserve_s, spine=spine)
        return script, None
    monkeypatch.setattr(EN, "fix_all", fix)
    MG.setup(); ROOM.run_room(DRAW("EPTD1", "collective"), "EPTD1")
    sp = seen["spine"]; sl = ROOM.proven_line(sp)
    want = HOOKS.reserve_s({"line": sl, "short": sp.get("ladder")} if sl and core.S("OPENING_HOOK_ON", bool) else None)
    assert seen["ps"] == ["X"] and seen["reserve"] == want, seen


def test_the_short_estimate_carries_the_look_and_the_psyche_line_together(monkeypatch, setting):
    """RUL-U1c D2 (TG-3, B011): a Short's cost estimate holds the look line AND the psyche line in one list (the `+` of the two terms), with a drive that
    led 2 of the last 4 long videos."""
    from whatifs import costguard as CG
    from tests.test_v12_launch import _vf
    setting("VIEWER_SEAT_ON", "TRUE"); setting("LOOK_BAR_ON", "TRUE"); setting("PSYCHE_TAGS_ON", "TRUE")
    _vf("awe_scale", "curiosity_gap", "awe_scale", "threat_survival")
    assert {"look", "psyche_tags"} <= {l["key"] for l in CG.lines("short", fmt="S1")}


def _paused_pair(monkeypatch, setting, f, p2):
    """D3's launch pair: the flagship `f` LIVE nine hours, its held Part 2 `p2` private with a calendar slot; the plan frozen and FIRED (as the act-a test does)."""
    from whatifs import publish as PUB, launch as LAU
    from whatifs.org import appetite as APP
    monkeypatch.setattr(LAU, "uploads_open", lambda: True); monkeypatch.setattr(PUB, "FAKE_FAULTS", {})
    setting("ORG_ON", "TRUE"); setting("PALACE_ON", "TRUE"); setting("APPETITE_ON", "TRUE")
    st = core.store(); nine = core.iso(core.now_utc() - dt.timedelta(hours=9)); cal = "2099-01-01T10:00:00Z"
    vf = PUB.yt_upload(f"x/{f}.mp4", "Flag", "Old words", ["t"], hd_gate=False); vp = PUB.yt_upload(f"x/{p2}.mp4", "P2", "D", ["t"], publish_at=cal, hd_gate=False)
    st.append("Episodes", [{"episode_id": f, "yt_id": vf, "status": "LIVE", "slot_et": nine}, {"episode_id": p2, "yt_id": vp, "status": "AWAITING_APPROVAL", "slot_et": cal}])
    st.append("Owner_Actions", [{"id": f"OA-{p2}", "kind": "contract_review", "episode_id": p2, "status": "OPEN", "dedupe_key": f"review|{p2}"}])
    j = json.loads(APP.plan(f, {"salvo": {"role": "flagship"}})["plan"]); j["held"] = p2; j["line"] = "The ice shelf cracked open in nineteen minutes flat"
    js = json.dumps(j, sort_keys=True); st.update("Appetite_Plans", "ep", f, {"plan": js, "sha": APP.sha(js), "state": "frozen"}); APP.uploaded(f, vf)
    return APP, PUB, vf, vp


def test_act_a_stays_pending_while_the_pipeline_is_paused(monkeypatch, setting):
    """RUL-U1c D3 (TG-4, B012): with the pipeline paused (PAUSED TRUE) and uploads open, the fire's act a is "pending: the pipeline is paused" and Part 2
    stays private - `clear_to_post` reads the channel's lock before the pair."""
    setting("PAUSED", "TRUE")
    APP, PUB, vf, vp = _paused_pair(monkeypatch, setting, "EPPA1", "EPPA2")
    assert APP.fire("EPPA1", vf, 400.0, 375.0, 9, "the appetite line")
    assert APP.acts(APP.plan_row("EPPA1"))["a"] == "pending: the pipeline is paused" and PUB.yt_read(vp)["privacy"] == "private", APP.acts(APP.plan_row("EPPA1"))


def test_the_channel_lock_is_read_before_the_pair(monkeypatch, setting):
    """RUL-U1c D4 (TG-5, B012): a flagship with no Part 2 waiting for approval, the pipeline paused: `clear_to_post` answers the pause - never the pair's
    "the flagship waits for its Part 2" (the channel's lock comes first)."""
    from whatifs import launch as LAU
    from tests.test_v12_launch import _p2_sheet
    monkeypatch.setattr(LAU, "uploads_open", lambda: True)
    SAL, rec = _p2_sheet(monkeypatch, setting, status="AWAITING_APPROVAL")
    setting("PAUSED", "TRUE")
    assert CON.clear_to_post("EPF1") == (False, "the pipeline is paused")


def test_an_appetite_undo_that_youtube_refuses_writes_no_down_verdict(monkeypatch, setting):
    """RUL-U1c D5 (TG-6, B013): his APPETITE UNDO of an early release when YouTube refuses the privacy change: Part 2 stays public, he is told it could not
    be made private, and NO "down" verdict is written (the Undo is "not yet", never a judgement of the film - on the failure branch too)."""
    from whatifs import notify as NT
    monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False); monkeypatch.delitem(NT.HANDLERS, "appetite", raising=False)
    setting("TWO_SCREENS_ON", "TRUE"); setting("OWNER_VERDICT_ON", "TRUE")
    APP, PUB, vf, vp = _paused_pair(monkeypatch, setting, "EPUD1", "EPUD2")
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    assert APP.fire("EPUD1", vf, 400.0, 375.0, 9, "the appetite line") and APP.acts(APP.plan_row("EPUD1"))["a"].startswith("made: Part 2 reads public")
    w = [o for o in core.store().rows("Owner_Actions") if o.get("kind") == "appetite" and o.get("episode_id") == "EPUD2"]; assert len(w) == 1, w
    monkeypatch.setattr(PUB, "yt_set_privacy", lambda v, p: False)                         # YouTube refuses the change
    out = NT.answer(w[0]["id"], "APPETITE UNDO EPUD2")
    assert "could NOT be made private" in out and PUB.yt_read(vp)["privacy"] == "public", out
    assert [v for v in core.store().rows("Owner_Verdicts") if v.get("ref") == "EPUD2" and v.get("verdict") == "down"] == []


def test_an_unreadable_acts_cell_makes_no_act_again(monkeypatch, setting):
    """RUL-U1c E1 (C1, B005): a FIRED plan row whose `acts` cell cannot be read: the tick's `retry` makes NO act again (no second public comment - Part 2 reads
    public and the line is good, so a `{}` answer would post one), every act of the row reads "refused: the acts cell ...", and an ERROR line is logged."""
    from whatifs import notify as NT
    from whatifs.org import appetite as APP
    APP_, PUB, vf, vp = _paused_pair(monkeypatch, setting, "EPAC1", "EPAC2")
    assert PUB.yt_set_privacy(vp, "public")
    st = core.store(); posted, logs = [], []
    st.update("Appetite_Plans", "ep", "EPAC1", {"state": "fired", "fired_at": core.iso(core.now_utc() - dt.timedelta(hours=1)), "acts": "{not json"})
    monkeypatch.setattr(PUB, "yt_comment", lambda *a, **k: posted.append(a) or "C1")
    sends = []; monkeypatch.setattr(NT, "send", lambda *a, **k: sends.append((a, k)) or "sent"); monkeypatch.setattr(APP, "log", lambda msg, level="INFO", *a, **k: logs.append((level, msg)))
    APP.retry(); by_retry, logs_retry = list(sends), list(logs)      # RUL-LAST2-U1 (RD-U1l-SF F1): what the tick itself did, before the test's own acts(r) below
    r = APP.plan_row("EPAC1"); a = APP.acts(r)
    assert posted == [], posted
    assert set(a) == set("abcde") and all(str(a[k]).startswith("refused: the acts cell") for k in "abcde"), a
    assert any(lv == "ERROR" and "acts cell" in m for lv, m in logs_retry), logs_retry; assert ("appetite", "appetite|acts|EPAC1") in [(a[0] if a else k.get("kind"), k.get("dedupe_key")) for a, k in by_retry], by_retry      # RUL-LAST-U1 (RD-U1k-TG F3): the owner row (appetite.py:146-152), sent by retry() itself (RUL-LAST2-U1)


def test_an_unreadable_fire_time_lapses_the_pending_act(monkeypatch, setting):
    """RUL-U1c E2 (C2, B006): a FIRED plan row whose `fired_at` and `ts` are both empty cannot say how long ago it fired: its pending act a lapses ("lapsed: ...")
    at the next `act`, and Part 2 stays private - the HD cap is NOT passed for it."""
    from whatifs.org import appetite as APP
    APP_, PUB, vf, vp = _paused_pair(monkeypatch, setting, "EPLT1", "EPLT2")
    PUB.FAKE_FAULTS["youtube"] = {"processing": True}                                    # Part 2 is not processed in HD
    st = core.store()
    st.update("Appetite_Plans", "ep", "EPLT1", {"state": "fired", "fired_at": "", "ts": "", "acts": json.dumps({"a": "pending: Part 2 is not HD-ready yet"})})
    assert APP._since(APP.plan_row("EPLT1")) is None
    APP.act("EPLT1")
    a = APP.acts(APP.plan_row("EPLT1"))
    assert a["a"].startswith("lapsed: ") and PUB.yt_read(vp)["privacy"] == "private", a


def test_an_unreadable_file_is_never_uploaded_unguarded(monkeypatch, setting, tmp_path):
    """RUL-U1c E3 (C3, B007): with ANTI_MYTH_ON a file whose hash cannot be taken is refused ("upload refused") - nothing is sent; and a ledger row that cannot be
    written is told to him ONCE (kind "ledger_miss", dedupe_key "ledger|<id>"; RUL-U1d D)."""
    from whatifs import publish as PUB, notify as NT
    monkeypatch.setattr(PUB, "FAKE_FAULTS", {}); setting("ANTI_MYTH_ON", "TRUE")
    with pytest.raises(RuntimeError, match="upload refused"):
        PUB.yt_upload(str(tmp_path / "missing.mp4"), "T", "d", ["t"], ledger=True, hd_gate=False)
    assert core.store().rows(PUB.LEDGER) == []
    assert PUB._fake_get("youtube", "FAKE_missing.mp4") == {}                       # no put reached the stand-in
    sent = []; st = core.store(); real = st.append
    monkeypatch.setattr(NT, "send", lambda kind, text, *a, **k: sent.append((kind, k.get("dedupe_key"))) or "sent")
    monkeypatch.setattr(st, "append", lambda tab, rows, *a, **k: (_ for _ in ()).throw(RuntimeError("sheet down")) if tab == PUB.LEDGER else real(tab, rows, *a, **k))
    p = tmp_path / "EPLG1.mp4"; p.write_bytes(b"bytes of a render")
    vid = PUB.yt_upload(str(p), "T", "d", ["t"], hd_gate=False)
    assert sent == [("ledger_miss", f"ledger|{vid}")], sent


def test_a_lost_plan_yt_id_still_gets_its_appetite_reading(monkeypatch, setting):
    """RUL-U1c E4 (C4, B008): a plan row whose yt_id write failed (cell empty) is read through the Episodes row's yt_id: ONE Appetite row, at the whole hours since
    the slot."""
    from whatifs import publish as PUB
    from whatifs.org import appetite as APP
    setting("ORG_ON", "TRUE"); setting("PALACE_ON", "TRUE"); setting("APPETITE_ON", "TRUE")
    now = core.parse_iso("2099-03-01T12:30:00Z"); st = core.store()
    st.append("Episodes", [{"episode_id": "EPLY1", "yt_id": "VID1", "slot_et": "2099-03-01T07:30:00Z", "status": "LIVE"}])
    st.append("Appetite_Plans", [{"ep": "EPLY1", "role": "long", "yt_id": "", "state": "frozen"}])
    monkeypatch.setattr(PUB, "FAKE_FAULTS", {"youtube": {"comments": {"VID1": []}, "stats": {"VID1": {"views": 40, "likes": 2, "comments": 0}}}})
    APP.read(now)
    rows = [r for r in st.rows("Appetite") if r.get("ep") == "EPLY1"]
    assert len(rows) == 1 and str(rows[0]["yt_id"]) == "VID1" and str(rows[0]["h"]) == "5", rows


def test_a_failed_depth_call_is_named_not_absent(monkeypatch, setting):
    """RUL-U1c E5 (C5, B009): the depth call RAISES for a due launch pair video: the drafts go plain (all False), `d["depth"]["skipped"]` names the failure, and the
    check `depth_frozen` answers N/A with "did not run" - never a PASS of 0 drafts and never the absence of a depth pass."""
    from whatifs import models as MDL
    from whatifs.org import salvo as SAL
    from tests.test_v12_launch import _depth_room
    _depth_room(monkeypatch, setting)
    def boom(role, *a, **k):
        if role == "depth": raise RuntimeError("the depth route is down")
        return {"script": "## BEAT 1\nOne."}
    monkeypatch.setattr(MDL, "ask", boom)
    d = {"salvo": {"role": "flagship"}}; reqs = [{"prompt": f"p{i}"} for i in range(3)]
    got = SAL.depth_split(d, {"premise": "What if the sea left for a day?"}, "EPDF1", reqs)
    assert got == [False, False, False] and d["depth"]["skipped"].startswith("the depth call failed"), (got, d)
    assert [r["prompt"] for r in reqs] == ["p0", "p1", "p2"]
    st, text = CON.p_depth_frozen({"d": d})
    assert st == CON.NA and "did not run" in text, (st, text)


def test_a_depth_reply_without_its_parts_is_named_not_absent(monkeypatch, setting):
    """RUL-LAST-U1 (RD-U1k-TG F1): salvo.py:632 - the depth reply of a due launch pair video lacks its four answers: the drafts go plain,
    `d["depth"]["skipped"]` names it, and `depth_frozen` answers N/A with "did not run" - never the absence of a depth pass."""
    from whatifs import models as MDL
    from whatifs.org import salvo as SAL
    from tests.test_v12_launch import _depth_room
    _depth_room(monkeypatch, setting)
    def short(role, *a, **k):
        if role == "depth": return {"answers": ["a", "b", "c"], "addendum": "x"}
        return {"script": "## BEAT 1\nOne."}
    monkeypatch.setattr(MDL, "ask", short)
    d = {"salvo": {"role": "flagship"}}; reqs = [{"prompt": f"p{i}"} for i in range(3)]
    got = SAL.depth_split(d, {"premise": "What if the sea left for a day?"}, "EPDS1", reqs)
    assert got == [False, False, False] and d["depth"] == {"skipped": "the depth reply lacked its four answers or its addendum"}, (got, d)
    assert [r["prompt"] for r in reqs] == ["p0", "p1", "p2"]
    st, text = CON.p_depth_frozen({"d": d})
    assert st == CON.NA and "did not run" in text, (st, text)


def test_a_skipped_depth_pass_writes_no_contest(setting):
    """RUL-LAST-U1 (RD-U1k-TG F2): salvo.py:653 - a lost depth pass is no pass: depth_contest writes no depth Contests row and sets no `won`."""
    from whatifs.org import salvo as SAL
    n = len(SAL.contests("depth")); d = {"depth": {"skipped": "x"}}
    assert SAL.depth_contest(d, "EPDC1", [False, False], 0) is None and d["depth"] == {"skipped": "x"} and len(SAL.contests("depth")) == n, (d, SAL.contests("depth"))


@pytest.mark.parametrize("reply", [{"answers": ["a", "b", "c", "d"], "addendum": "  "}, {"answers": ["a", "b", "c", "d", "e"], "addendum": "x"}])
def test_a_depth_reply_with_no_addendum_or_five_answers_is_named_not_absent(monkeypatch, setting, reply):
    """RUL-LAST2-U1 (RD-U1l-TG F1): salvo.py:632 - four answers with a blank addendum, or five answers, are no depth pass: the drafts go plain and it is named."""
    from whatifs import models as MDL
    from whatifs.org import salvo as SAL
    from tests.test_v12_launch import _depth_room
    _depth_room(monkeypatch, setting)
    monkeypatch.setattr(MDL, "ask", lambda role, *a, **k: reply if role == "depth" else {"script": "## BEAT 1\nOne."})
    d = {"salvo": {"role": "flagship"}}; reqs = [{"prompt": f"p{i}"} for i in range(3)]
    assert SAL.depth_split(d, {"premise": "P"}, "EPDS2", reqs) == [False, False, False] and d["depth"] == {"skipped": "the depth reply lacked its four answers or its addendum"}, d
    assert [r["prompt"] for r in reqs] == ["p0", "p1", "p2"]


def test_an_unreadable_acts_cell_whose_owner_row_fails_still_refuses(monkeypatch, setting):
    """RUL-LAST2-U1 (RD-U1l-TG F2): appetite.py:150-152 - the owner row for an unreadable acts cell fails to send: acts() still refuses every act and
    logs a WARN that the row was not sent - it never raises into the tick's retry."""
    from whatifs import notify as NT
    from whatifs.org import appetite as APP
    logs = []; monkeypatch.setattr(APP, "log", lambda msg, level="INFO", *a, **k: logs.append((level, msg)))
    monkeypatch.setattr(NT, "send", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("planted: send failed")))
    a = APP.acts({"ep": "EPAC2", "acts": "{not json"})
    assert set(a) == set("abcde") and all(str(v).startswith("refused: the acts cell") for v in a.values()), a
    assert any(lv == "WARN" and "was not sent" in m for lv, m in logs), logs
