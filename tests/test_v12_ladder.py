"""v12 V2c-b1 THE LADDER: the cadence in weeks, the numbers read by processed day, the promote rule, the refusal of a long video without a promoted
Short (and the owner's override on record), check topic_ladder, the winner's follow-up with its clock. Each rule both ways. No keys, no network."""
import datetime as dt, json, os, zipfile
import pytest
from whatifs import core, shorts2 as SH, ladder as LAD, brain as BR, breakout as BRK, notify as NT, publish as PUB, manage as MG, formats as FMT, contract as CON

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 12, 16, 6, 0, tzinfo=UTC)          # a Wednesday

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _on(setting): setting("LADDER_ON", "TRUE")              # tests/conftest.py switches the ladder off for the older tests

def _bench(*premises):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "premise": p, "headline": p, "family": "", "ptype": "collective", "status": "READY", "claude_score": 9, "gemini_score": 9,
                                           "combined": 9 - i / 10, "added": core.iso()} for i, p in enumerate(premises)])

def _made(now, *hours_ago, held=False, brk=False):
    core.store().append("Specials", [{"ts": core.iso(now - dt.timedelta(hours=h)), "id": f"{'BRK' if brk else 'SH'}{i}{int(h)}", "kind": "short", "format": "S1",
                                      "status": "HELD (short_plain)" if held else "POSTED", "premise": f"p{i}{h}"} for i, h in enumerate(hours_ago)])

def _short(sid, premise, age_days, now=None, eng=None, watched=70.0, subs=0, shares=0, views=None, days=5, v24=None, v48=None, follow_of=None, script="A line. Another line."):
    """A posted Short of `age_days` with its rows on Specials and the ladder, and - when it has numbers - on Analytics and Monitor48."""
    now = now or core.now_utc(); st = core.store(); ts = core.iso(now - dt.timedelta(days=age_days)); yt = "yt_" + sid
    rec = {"ts": ts, "id": sid, "kind": "short", "title": "T " + sid, "format": "S1", "yt_id": yt, "status": "POSTED", "premise": premise, "hook": "you_pov", "script": script, "sec": 22}
    st.append("Specials", [rec]); LAD.enter(rec, {"follow_of": follow_of} if follow_of else None, footage="")
    if eng is not None:
        first = {"days": 3, "views": int((views or eng * 2) * 0.8), "engaged": int(eng * 0.8), "watched": watched, "shares": shares, "subs": subs}
        st.append("Analytics", [{"episode_id": sid, "yt_id": yt, "pulled": core.iso(now), "views": views or eng * 2, "engaged_views": eng, "avg_view_pct": watched, "shares": shares, "subs": subs,
                                 "days": days, "first_json": json.dumps(first if days >= 3 else {}), "data_note": "ok (short)"}])
    if v24 is not None or v48 is not None:
        st.append("Monitor48", [{"yt_id": yt, "video_key": sid, "kind": "short", "published": ts, "v24": "" if v24 is None else v24, "v48": "" if v48 is None else v48}])
    return rec

def _row(sid): return LAD.row(sid)

# ------------------------------------------------------------------ 1. the cadence
def test_three_a_week_is_every_48_hours_and_then_the_week_is_full(setting):
    assert SH.gap_h() == 48 and SH.cadence(NOW) == (True, "")                                      # nothing made yet
    _made(NOW, 47); ok, why = SH.cadence(NOW); assert not ok and "48 hours apart" in why           # the last one is too fresh
    assert SH.cadence(NOW + dt.timedelta(hours=1)) == (True, "")                                   # 48 hours after it
    _made(NOW, 0); assert not SH.cadence(NOW + dt.timedelta(hours=47))[0] and SH.cadence(NOW + dt.timedelta(hours=48))[0]
    _made(NOW + dt.timedelta(hours=48), 0); ok, why = SH.cadence(NOW + dt.timedelta(hours=100)); assert not ok and "3 of 3" in why      # three in seven days: the week is full
    assert SH.cadence(NOW - dt.timedelta(hours=47) + dt.timedelta(days=7, minutes=1))[0]           # seven days after the first: the same weekday again
    for per, gap in ((1, 168), (2, 72), (3, 48), (4, 24), (5, 24), (7, 24)):
        setting("SHORTS_PER_WEEK", str(per)); assert SH.gap_h() == gap, per

def test_the_month_has_its_own_ceiling_and_a_follow_up_or_a_held_short_does_not_count(setting):
    setting("SHORTS_PER_MONTH", "2")
    first = dt.datetime(2026, 12, 1, 6, 0, tzinfo=UTC)
    _made(first, 0); _made(first + dt.timedelta(days=3), 0); now = first + dt.timedelta(days=9)
    ok, why = SH.cadence(now); assert not ok and "2 of 2 Shorts were made this month" in why
    assert SH.cadence(dt.datetime(2027, 1, 1, 6, 0, tzinfo=UTC))[0]                                # a new month
    setting("SHORTS_PER_MONTH", "12"); assert SH.cadence(now)[0]
    _made(now, 1, brk=True); assert SH.cadence(now)[0]                                             # a winner's follow-up is outside the cadence
    _made(now, 2, held=True); ok, why = SH.cadence(now); assert not ok and "held a Short" in why   # after a held Short: one paid writing a day at most
    assert SH.cadence(now + dt.timedelta(hours=22, minutes=1))[0]                                  # 24 hours after the held one

def test_due_follows_the_cadence_and_an_order_comes_first(monkeypatch, setting):
    assert SH.due(NOW) is True
    _made(NOW, 1); assert SH.due(NOW) is False                                                     # the cadence is not due
    _short("SHW", "What if the Moon left tonight?", 1, now=NOW); q = LAD.order_followup("SHW", "yt_SHW", 9000, 1000, 24, NOW)
    assert q["status"] == "ORDERED" and SH.order_due(NOW)["video_key"] == "SHW" and SH.due(NOW) is True      # the winner's follow-up is due at once
    setting("SHORTS_WEEKLY_CAP", "2"); assert SH.order_due(NOW) is None and SH.due(NOW) is False             # the ceiling of Shorts in any seven days holds for it too
    setting("SHORTS_WEEKLY_CAP", "10"); LAD.order_tried("SHW", "no money", NOW)
    assert SH.order_due(NOW + dt.timedelta(hours=5)) is None and SH.order_due(NOW + dt.timedelta(hours=7))["video_key"] == "SHW"      # a failed try waits before the next
    setting("SHORTS_TRACK_ON", "FALSE"); assert SH.due(NOW + dt.timedelta(hours=7)) is False

# ------------------------------------------------------------------ 2. the reading (YouTube is 48 to 72 hours late)
def test_the_numbers_are_read_by_processed_day_until_three_days_exist(setting):
    st = core.store(); t = NOW - dt.timedelta(days=4, hours=2)
    st.append("Specials", [{"id": "SH1", "yt_id": "s1", "ts": core.iso(t), "title": "x", "kind": "short", "format": "S1"}])
    assert BR._short_metrics("s1", t, t + dt.timedelta(days=2, hours=1)) is None                   # two days old: YouTube has processed nothing yet
    m = BR._short_metrics("s1", t, NOW); assert m["days"] == 2 and m["first_json"] == "{}" and not BR.reading_complete(m)      # four days old: two days processed - a fragment
    assert BR.ingest_shorts(NOW) == 1 and st.rows("Analytics")[0]["data_note"].startswith("partial: 2 processed") and BR.ingest_shorts(NOW + dt.timedelta(hours=19)) == 0
    assert BR.ingest_shorts(NOW + dt.timedelta(hours=24)) == 1                                     # a fragment is read again the next day ...
    a = st.rows("Analytics")[0]; f = json.loads(a["first_json"]); assert BR.reading_complete(a) and int(float(a["days"])) == 3 and f["days"] == 3 and 0 < f["engaged"] <= int(float(a["engaged_views"]))
    assert BR.ingest_shorts(NOW + dt.timedelta(hours=48)) == 0 and BR.ingest_shorts(NOW + dt.timedelta(days=8, hours=1)) == 1      # ... a whole reading weekly (late bloomers)
    assert BR.reading_complete({"engaged_views": 5}) and not BR.reading_complete({"days": 2})      # a row from before readings were counted by day keeps its weekly rhythm

def test_first_days_takes_the_same_stretch_of_every_short():
    days = [{"i": 0, "views": 100, "engaged": 60, "avp": 80, "shares": 2, "subs": 1}, {"i": 1, "views": 300, "engaged": 150, "avp": 60, "shares": 1, "subs": 0},
            {"i": 2, "views": 0, "engaged": 0, "avp": 0, "shares": 0, "subs": 0}, {"i": 7, "views": 9000, "engaged": 8000, "avp": 99, "shares": 50, "subs": 40}]
    f = BR.first_days(days, 3); assert f == {"days": 3, "views": 400, "engaged": 210, "watched": 65.0, "shares": 3, "subs": 1}        # the late spike of day 8 is not in it
    assert BR.first_days([], 3)["views"] == 0

def test_a_short_the_owner_approved_later_is_public_from_then_on(setting):
    st = core.store(); made = NOW - dt.timedelta(days=3)
    rec = {"ts": core.iso(made), "id": "SH1", "kind": "short", "title": "t", "format": "S1", "yt_id": "", "status": "AWAITING_APPROVAL", "premise": "p", "hook": "you_pov"}
    st.append("Specials", [rec]); LAD.enter(rec); assert _row("SH1")["state"] == "MADE" and LAD.read(NOW) == 0
    st.update("Specials", "id", "SH1", {"yt_id": "y1", "status": "POSTED"}); assert LAD.read(NOW) == 1
    r = _row("SH1"); assert r["state"] == "POSTED" and r["yt_id"] == "y1" and r["posted"] == core.iso(NOW)
    assert ("SH1", "y1", core.iso(NOW), "t", "S1") in BR._short_ids()                              # the learning core and the monitor count its age from the day it went public
    assert LAD.enter(rec) is False                                                                 # once per Short

# ------------------------------------------------------------------ 3. the ladder's record and the promote rule
def test_a_reading_counts_only_when_it_covers_three_processed_days(setting):
    _short("SHA", "pa", 6, now=NOW, eng=500, days=2); _short("SHB", "pb", 6, now=NOW, eng=40, days=3); _short("SHC", "pc", 3, now=NOW, v48=900); _short("SHD", "pd", 1, now=NOW)
    LAD.read(NOW); got = {i: (_row(i)["state"], _row(i).get("evidence") or "") for i in ("SHA", "SHB", "SHC", "SHD")}
    assert got == {"SHA": ("POSTED", ""), "SHB": ("READ", "measured"), "SHC": ("READ", "public"), "SHD": ("POSTED", "")}, got
    assert [r["id"] for r in LAD.candidates()] == ["SHB", "SHC"] and LAD.rank(LAD.candidates())[0] == "measured"          # true numbers outrank public views

def test_a_short_past_the_window_is_passed_over_and_its_footage_deleted(monkeypatch, setting):
    gone = []; monkeypatch.setattr(PUB, "drive_delete", lambda fid: gone.append(fid))
    _short("SHO", "old", 31, now=NOW, eng=900); core.store().update("Ladder", "id", "SHO", {"footage": "F1"}); _short("SHN", "new", 29, now=NOW, eng=10)
    LAD.read(NOW); assert _row("SHO")["state"] == "PASSED" and not _row("SHO")["footage"] and gone == ["F1"] and _row("SHN")["state"] == "READ"
    setting("LADDER_WINDOW_DAYS", "14"); LAD.read(NOW); assert _row("SHN")["state"] == "PASSED"

def test_wilson_trusts_a_share_from_many_viewers_more():
    assert LAD.wilson(2, 2) < LAD.wilson(100, 101) and LAD.wilson(1, 40) < LAD.wilson(30, 2000) and LAD.wilson(0, 500) == 0 and LAD.wilson(5, 0) == 0
    assert 0.94 < LAD.wilson(100, 101) < 0.99 and abs(LAD.wilson(50, 100) - 0.4038) < 0.001

def test_the_promote_rule_ranks_by_code(setting):
    def c(i, **k): return dict({"id": i, "evidence": "measured", "engaged": 0, "watched": 0, "subs": 0, "shares": 0, "days": 3, "posted": "2026-12-01T00:00:00Z"}, **k)
    a = c("A", engaged=2000, watched=80, subs=30, shares=40); b = c("B", engaged=900, watched=60, subs=3, shares=4); t = c("T", engaged=20, watched=99, subs=2, shares=2)
    klass, order = LAD.rank([b, t, a], min_engaged=30); assert klass == "measured" and [r["id"] for r, _ in order] == ["A", "B", "T"]
    assert "THIN EVIDENCE" in order[2][1] and "THIN" not in order[0][1] and "rank sum 4" in order[0][1]          # A is best on all four measures
    assert LAD.measures(t)["subs_rate"] < 0.03 < 2 / 20 and LAD.measures(t)["subs_rate"] > LAD.measures(a)["subs_rate"]      # the Wilson bound shrinks 2 of 20 (10%) to under 3% - still more than 30 of 2,000
    assert [r["id"] for r, _ in LAD.rank([b, t, a], min_engaged=0)[1]] == ["A", "B", "T"]           # so thin evidence is ALSO relative: under a tenth of the pool's best engaged views
    t2 = c("T2", engaged=250, watched=99, subs=20, shares=20); assert [r["id"] for r, _ in LAD.rank([a, t2], min_engaged=0)[1]] == ["T2", "A"]      # above it, three better measures out-vote reach
    assert [r["id"] for r, _ in LAD.rank([t], min_engaged=30)[1]] == ["T"] and "THIN" in LAD.rank([t], min_engaged=30)[1][0][1]      # alone, a thin Short is still the best there is - and says so
    w = c("W", engaged=5, multiple=3.4, evidence="public"); klass, order = LAD.rank([a, w]); assert klass == "winner" and order[0][0]["id"] == "W"      # a declared winner comes first
    p1, p2 = c("P1", evidence="public", v48=300), c("P2", evidence="public", v48=900)
    assert LAD.rank([p1, p2]) [0] == "public" and [r["id"] for r, _ in LAD.rank([p1, p2])[1]] == ["P2", "P1"] and LAD.rank([p1, b])[0] == "measured" and LAD.rank([]) == ("", [])
    x = c("X", engaged=1000, watched=70, subs=5, shares=5, views=9000); y = c("Y", engaged=1000, watched=70, subs=5, shares=5, views=1100, posted="2026-12-05T00:00:00Z")
    assert [r["id"] for r, _ in LAD.rank([x, y])[1]] == ["Y", "X"]                                   # a tie goes to the newer Short - never to engaged views divided by views

def test_promote_is_growth_and_learnings_run_and_everybody_is_told(monkeypatch, setting):
    _quiet(monkeypatch); _on(setting)
    _short("SHA", "What if the Moon left tonight?", 8, now=NOW, eng=300, watched=60, subs=1, shares=1); _short("SHB", "What if rain fell upward?", 6, now=NOW, eng=2000, watched=85, subs=20, shares=30)
    r = LAD.promote(NOW); st = core.store()
    assert r["id"] == "SHB" and _row("SHB")["state"] == "PROMOTED" and _row("SHB")["by"] == "D10" and "measured: rank sum 4" in _row("SHB")["score"] and _row("SHA")["state"] == "READ"
    ses = [s for s in st.rows("Sessions") if s.get("dept") == "D10" and s.get("trigger") == "promote"]; assert len(ses) == 1 and ses[0]["status"] == "ok"
    from whatifs.org import memos as MEM
    pm = [m for m in MEM.rows(st) if m["type"] == "performance_memo"]; assert len(pm) == 1 and pm[0]["to_depts"] == ["D4", "D14", "D9"] and pm[0]["body"]["video"] == "SHB" and int(float(pm[0]["body"]["metrics"]["engaged"])) == 2000
    told = [a for a in st.rows("Owner_Actions") if a.get("kind") == "ladder"]; assert len(told) == 1 and "Next long video" in told[0]["text"] and "LADDER SKIP SHB" in told[0]["buttons"]
    assert LAD.promote(NOW)["id"] == "SHB" and len([m for m in MEM.rows(st) if m["type"] == "performance_memo"]) == 1          # a waiting promotion is never replaced or announced twice
    assert NT.answer(told[0]["id"], "LADDER SKIP SHB").startswith("set aside") and _row("SHB")["state"] == "SKIPPED"            # the owner's one tap ...
    assert LAD.promote(NOW)["id"] == "SHA"                                                                                      # ... and the rule takes the next best

def test_a_topic_gets_one_long_video_and_a_follow_up_belongs_to_its_winners_topic(monkeypatch, setting):
    _quiet(monkeypatch); _on(setting)
    _short("SHA", "pa", 9, now=NOW, eng=500); _short("BRK1", "pa", 6, now=NOW, eng=900, follow_of="SHA"); _short("SHC", "pc", 6, now=NOW, eng=50)
    assert _row("BRK1")["topic"] == "SHA" and _row("BRK1")["note"].startswith("follow-up of SHA")
    assert LAD.promote(NOW)["id"] == "BRK1" and LAD.use("BRK1", "EP1", NOW) and _row("BRK1")["state"] == "USED"
    assert [r["id"] for r in LAD.candidates()] == ["SHC"] and LAD.promote(NOW)["id"] == "SHC"      # the winner SHA has the same topic: it is not promoted a second time
    assert LAD.use("SHC", "EP2", NOW) and LAD.promote(NOW) is None and LAD.use("SHC", "EP2", NOW) and not LAD.use("NOPE", "EP3")

# ------------------------------------------------------------------ 4. the gate, the refusal, the override
def test_the_gate_refuses_says_why_and_is_opened_only_by_a_promotion_or_an_override(monkeypatch, setting):
    _quiet(monkeypatch)
    assert LAD.gate(NOW)[0] is True and "switched off" in LAD.gate(NOW)[1]                         # conftest: the older tests run without the ladder
    _on(setting); ok, why, r = LAD.gate(NOW); assert not ok and why.startswith("no Short has been made yet") and r is None
    setting("SHORTS_TRACK_ON", "FALSE"); assert LAD.gate(NOW)[0] is True; setting("SHORTS_TRACK_ON", "TRUE")      # without Shorts nothing could ever climb: the ladder cannot bind
    _short("SHA", "pa", 1, now=NOW); ok, why, _ = LAD.gate(NOW); assert not ok and "1 Short(s) have no numbers yet" in why and "about 5 days" in why
    _short("SHB", "pb", 6, now=NOW, eng=400); ok, why, r = LAD.gate(NOW); assert ok and r["id"] == "SHB" and r["state"] == "PROMOTED" and "SHB" in why
    LAD.use("SHB", "EP1", NOW); core.store().update("Ladder", "id", "SHA", {"state": "PASSED"})
    ok, why, _ = LAD.gate(NOW); assert not ok and why.startswith("every Short with numbers already has its long video")
    aid = LAD.refuse("2026-12-19T15:00:00Z", why); assert LAD.refuse("2026-12-19T15:00:00Z", why) == aid       # ONE message per slot
    row = next(a for a in core.store().rows("Owner_Actions") if a["id"] == aid); assert "Make it anyway" in row["buttons"] and "waiting" in row["text"]
    assert NT.answer(aid, "LADDER OVERRIDE 2026-12-19T15:00:00Z").startswith("recorded (OVR")
    o = LAD.waiting_override(); ok, why, r = LAD.gate(NOW); assert ok and r["id"] == o["id"] and o["by"] == "owner" and "2026-12-19" in o["note"] and "override recorded by owner" in why
    assert LAD.override("owner", "again", NOW)["id"] == o["id"]                                    # one open override at a time
    assert LAD.claim() == o["id"] and LAD.use(o["id"], "EP2", NOW) and _row(o["id"])["state"] == "OVERRIDE_USED" and LAD.gate(NOW)[0] is False     # used up by ONE long video

def test_the_owners_own_locked_topic_is_an_override_on_record_and_a_promotion_beats_a_stale_override(monkeypatch, setting):
    _quiet(monkeypatch); _on(setting)
    setting("OWNER_NEXT_PREMISE", json.dumps({"premise": "What if my topic?", "brief_id": "OB1"}))
    ok, why, r = LAD.gate(NOW); assert ok and r["by"] == "owner_brief" and r["state"] == "OVERRIDE" and LAD.pitch() is None
    setting("OWNER_NEXT_PREMISE", ""); _short("SHB", "pb", 6, now=NOW, eng=400)
    ok, why, r = LAD.gate(NOW); assert ok and r["id"] == "SHB" and LAD.waiting_override() is not None      # a Short can be promoted: the override stays unused on the record
    p = LAD.pitch(); assert p["premise"] == "pb" and p["ladder"] == "SHB" and p["teased"] is True

def test_the_tick_names_no_slot_without_a_promoted_short_and_asks_once(monkeypatch, setting):
    _quiet(monkeypatch); _on(setting)
    from whatifs import governor as G
    monkeypatch.setattr(MG, "audit_gate", lambda eps: (True, "")); monkeypatch.setattr(G, "can_start_episode", lambda: (True, ""))
    slot = core.now_utc() + dt.timedelta(hours=10); s = slot.strftime("%Y-%m-%dT%H:%M:%SZ"); monkeypatch.setattr(MG, "next_slots", lambda n=3, after=None: [slot])
    assert MG._produce_slot([]) is None and MG._produce_slot([]) is None
    asks = [a for a in core.store().rows("Owner_Actions") if a.get("kind") == "ladder"]; assert len(asks) == 1 and s[:10] in asks[0]["text"]
    failed = [{"episode_id": "EPX", "slot_et": s, "status": "FAILED", "notes": "attempts=1"}]
    assert MG._produce_slot(failed) is None                                                        # a failed first attempt that took no topic does not pass either
    core.store().append("Ladder", [{"id": "SHZ", "topic": "SHZ", "state": "USED", "episode_id": "EPX", "premise": "p"}])
    assert MG._produce_slot(failed) == s                                                           # a retry keeps the topic its first attempt took
    NT.answer(asks[0]["id"], f"LADDER OVERRIDE {s}"); assert MG._produce_slot([]) == s
    setting("LADDER_ON", "FALSE"); assert MG._produce_slot([]) == s

# ------------------------------------------------------------------ 5. the writers' room and check topic_ladder
def test_the_room_keeps_the_promoted_premise_word_for_word_and_no_jury_can_drop_it(monkeypatch, setting):
    _quiet(monkeypatch); _on(setting)
    from whatifs import room as ROOM, premise as PR
    _bench("What if every mirror showed tomorrow?", "What if the wind kept every word you said?")
    _short("SHA", "What if your shadow arrived one second late?", 6, now=core.now_utc(), eng=400); _short("SHB", "What if rain fell upward for an hour?", 6, now=core.now_utc(), eng=90)
    assert LAD.gate()[2]["id"] == "SHA"
    real = PR.score; monkeypatch.setattr(PR, "score", lambda ps, recent, ep=None: [p.update(combined=1.0, claude=1, gemini=1) for p in ps] and ps)      # the judges hate it
    sp = ROOM.scout_and_pick({"strategies": {"family": "F09_space"}, "playbook": {}}, ROOM.context(), "EPL1")
    assert sp["premise"] == "What if your shadow arrived one second late?" and sp["ladder"] == "SHA" and "teased_premise" not in sp and not sp.get("from_bench")      # the offline Showrunner answered with another premise
    assert sp["premise_score"] == 1.0 and _row("SHA")["state"] == "PROMOTED"                        # the judges' score is on record; the topic is used up only when the plan is saved
    assert sp["next_tease"]["premise"] in ("What if rain fell upward for an hour?", "What if every mirror showed tomorrow?", "What if the wind kept every word you said?")      # the tease names what can truthfully come next
    monkeypatch.setattr(PR, "score", real); setting("OWNER_NEXT_PREMISE", json.dumps({"premise": "What if the owner chose?", "headline": "Owner", "brief_id": "OB1"}))
    sp2 = ROOM.scout_and_pick({"strategies": {"family": "F09_space"}, "playbook": {}}, ROOM.context(), "EPL2"); assert "ladder" not in sp2 and sp2.get("teased_premise") == "What if the owner chose?"

def test_topic_ladder_passes_only_on_this_videos_own_promoted_short_or_an_override(monkeypatch, setting):
    _quiet(monkeypatch)
    def ck(d, premise="pb", ep="EP1"): return CON.p_topic_ladder({"d": d, "room": {"spine": {"premise": premise}}, "ep": ep})
    assert ck({"ladder": "SHB"})[0] == CON.NA                                                      # the ladder is off (the older tests)
    _on(setting); _short("SHA", "pa", 6, now=NOW, eng=10); _short("SHB", "pb", 6, now=NOW, eng=400); LAD.promote(NOW); LAD.use("SHB", "EP1", NOW)
    st, ev = ck({"ladder": "SHB"}); assert st == CON.PASS and "SHB" in ev and "measured" in ev
    assert ck({})[0] == CON.FAIL and "never started as a Short" in ck({})[1]                       # the draw names no ladder row
    assert ck({"ladder": "SHB"}, premise="another premise")[0] == CON.FAIL and ck({"ladder": "SHB"}, premise="  PB ")[0] == CON.PASS
    assert ck({"ladder": "SHB"}, ep="EP9")[0] == CON.FAIL and "promoted for EP1" in ck({"ladder": "SHB"}, ep="EP9")[1]        # another video's Short
    assert ck({"ladder": "SHA"}, premise="pa")[0] == CON.FAIL and "never promoted" in ck({"ladder": "SHA"}, premise="pa")[1]
    assert ck({"ladder": "SHX"})[0] == CON.FAIL and "does not exist" in ck({"ladder": "SHX"})[1]
    o = LAD.override("owner", "his tap", NOW); st, ev = ck({"ladder": o["id"]}, premise="anything", ep="EP2"); assert st == CON.PASS and "override by owner" in ev and "his tap" in ev
    LAD.use(o["id"], "EP2", NOW); assert ck({"ladder": o["id"]}, ep="EP2")[0] == CON.PASS and ck({"ladder": o["id"]}, ep="EP3")[0] == CON.FAIL      # one override, one video
    assert [f for f in CON.FEATURES if f[0] == "topic_ladder"][0][1] == "script"

# ------------------------------------------------------------------ 6. the winner: one follow-up, ordered with a clock
def _monitored(monkeypatch, views):
    monkeypatch.setattr(BRK, "_views", lambda ids: {y: views.get(y, 0) for y in ids})

def test_a_short_at_three_times_the_median_of_the_same_mark_is_a_winner_once(monkeypatch, setting):
    _quiet(monkeypatch); st = core.store()
    st.append("Monitor48", [{"yt_id": f"old{i}", "video_key": f"O{i}", "kind": "short", "v24": 100 * (i + 1), "v48": 300 * (i + 1)} for i in range(3)])      # medians: 200 at 24 h, 600 at 48 h
    _short("SHH", "What if the Moon left tonight?", 0, now=NOW - dt.timedelta(hours=25)); _short("SHM", "pm", 0, now=NOW - dt.timedelta(hours=25)); _short("SHY", "py", 0, now=NOW - dt.timedelta(hours=20))
    _monitored(monkeypatch, {"yt_SHH": 600, "yt_SHM": 599, "yt_SHY": 99999})
    found = BRK.monitor(NOW); assert [(f["key"], f["mark"], f["base"]) for f in found] == [("SHH", 24, 200)]          # exactly 3 times; 2.995 times is not; under 24 hours nothing is judged
    q = st.rows("Breakout_Queue"); assert len(q) == 1 and q[0]["video_key"] == "SHH" and q[0]["status"] == "ORDERED" and int(float(q[0]["left"])) == 1 and q[0]["due"] == core.iso(NOW + dt.timedelta(hours=48))
    assert float(_row("SHH")["multiple"]) == 3.0 and "winner at the 24-hour mark" in _row("SHH")["note"]
    card = [a for a in st.rows("Owner_Actions") if a.get("kind") == "breakout"]; assert len(card) == 1 and "ONE follow-up" in card[0]["text"] and "BREAKOUT NO SHH" in card[0]["buttons"] and "Approve" not in card[0]["buttons"]
    from whatifs.org import memos as MEM
    pm = [m for m in MEM.rows(st) if m["type"] == "performance_memo"]; assert len(pm) == 1 and pm[0]["body"]["window"] == "breakout" and pm[0]["to_depts"] == ["D14", "D4", "D9"]
    _monitored(monkeypatch, {"yt_SHH": 2000, "yt_SHM": 1799, "yt_SHY": 899})                       # a day later: 48-hour marks (median 600) and SHY's 24-hour mark (median now 300)
    assert BRK.monitor(NOW) == [] and [f["key"] for f in BRK.monitor(NOW + dt.timedelta(hours=24))] == ["SHH"] and len(st.rows("Breakout_Queue")) == 1      # a winner again at the 48-hour mark - and still ONE order
    LAD.read(NOW); assert LAD.rank(LAD.candidates())[0] == "winner"                                 # and the promote rule puts it first
    assert NT.answer(card[0]["id"], "BREAKOUT NO SHH").startswith("stopped") and st.rows("Breakout_Queue")[0]["status"] == "DECLINED" and LAD.open_orders() == []

def test_without_history_the_line_decides_and_a_cut_down_reel_is_never_followed_up(monkeypatch, setting):
    _quiet(monkeypatch); st = core.store()
    assert BRK.short_winner(9999, []) == (False, None) and BRK.short_winner(10000, [50, 60]) == (True, None) and BRK.short_winner(170, [50, 60, 55]) == (True, 55) and BRK.short_winner(164, [50, 60, 55])[0] is False
    st.append("Episodes", [{"episode_id": "E1", "slot_et": core.iso(NOW - dt.timedelta(hours=30)), "reel1_yt": "reel1", "premise": "p"}])
    _short("SHN", "pn", 0, now=NOW - dt.timedelta(hours=30)); _monitored(monkeypatch, {"reel1": 500000, "yt_SHN": 10000})
    assert [f["key"] for f in BRK.monitor(NOW)] == ["SHN"] and [q["video_key"] for q in st.rows("Breakout_Queue")] == ["SHN"]      # the reel has no topic of its own on the ladder
    assert "no history yet" in _row("SHN")["note"] and float(_row("SHN")["multiple"]) == 1.0

def test_the_follow_up_is_made_first_told_what_the_winner_said_and_closes_its_order(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if gravity doubled?"); st = core.store()
    _short("SHW", "What if the Sun went out?", 1, now=NOW, script="The Sun just went out.\nYour street is black at noon.")
    LAD.order_followup("SHW", "yt_SHW", 9000, 1000, 24, NOW)
    import whatifs.models as M
    seen = []; real = M.ask_many; monkeypatch.setattr(M, "ask_many", lambda calls, **k: (seen.extend(c["prompt"] for c in calls), real(calls, **k))[1])
    r = SH.run(force=True, publish=False, now=NOW + dt.timedelta(hours=2))
    assert r["ok"] and r["id"].startswith("BRK") and r["premise"] == "What if the Sun went out?", {k: v for k, v in r.items() if k != "script"}
    assert all("THIS IS THE FOLLOW-UP OF A SHORT THAT REAL VIEWERS STAYED FOR" in p and "THE WINNER SAID: The Sun just went out. / Your street is black at noon." in p for p in seen) and seen
    q = st.rows("Breakout_Queue")[0]; assert q["status"] == "DONE" and q["done"] == r["id"] and int(float(q["left"])) == 0 and LAD.open_orders() == []
    lr = _row(r["id"]); assert lr["topic"] == "SHW" and lr["state"] == "MADE" and lr["footage"]      # the follow-up is a step of its winner's topic
    assert FMT.likeness(r["script"], "The Sun just went out.\nYour street is black at noon.") < 0.4
    r2 = SH.run(force=True, publish=False, now=NOW + dt.timedelta(hours=3)); assert r2["ok"] and r2["id"].startswith("SH") and r2["premise"] == "What if gravity doubled?"      # no order left: the cadence's own topic

def test_a_follow_up_that_cannot_be_paid_keeps_its_reason_and_waits(monkeypatch, setting):
    _quiet(monkeypatch); st = core.store(); from whatifs import governor as G
    _short("SHW", "What if the Sun went out?", 1, now=NOW); LAD.order_followup("SHW", "yt_SHW", 9000, 1000, 24, NOW)
    monkeypatch.setattr(G, "extras_allowed", lambda est, kind="extra": (False, "the breakout fund is empty"))
    r = SH.run(force=True, now=NOW + dt.timedelta(hours=1)); assert r["skipped"] == "budget" and not st.rows("Sessions")
    q = st.rows("Breakout_Queue")[0]; assert q["status"] == "ORDERED" and "no money (the breakout fund is empty)" in q["plan"] and SH.order_due(NOW + dt.timedelta(hours=2)) is None

def test_an_overdue_follow_up_becomes_a_memo_that_only_the_follow_up_closes(monkeypatch, setting):
    _quiet(monkeypatch); st = core.store(); from whatifs.org import memos as MEM
    _short("SHW", "What if the Sun went out?", 1, now=NOW); LAD.order_followup("SHW", "yt_SHW", 9000, 1000, 24, NOW); LAD.order_tried("SHW", "held at the short gate (short_kept)", NOW + dt.timedelta(hours=3))
    assert LAD.watch(NOW + dt.timedelta(hours=48)) == [] and not MEM.find(type="problem_memo")       # on the clock: nothing
    assert LAD.watch(NOW + dt.timedelta(hours=49)) == ["SHW"] and st.rows("Breakout_Queue")[0]["status"] == "OVERDUE"
    m = MEM.find(type="problem_memo", from_dept="D10"); assert len(m) == 1 and m[0]["to_depts"] == ["D14"] and m[0]["body"]["error_class"] == "followup_overdue"
    assert "within 48 hours" in m[0]["body"]["what_failed"] and "held at the short gate (short_kept)" in m[0]["body"]["what_failed"]
    assert LAD.watch(NOW + dt.timedelta(hours=60)) == [] and len(MEM.find(type="problem_memo")) == 1 and SH.order_due(NOW + dt.timedelta(hours=60))["video_key"] == "SHW"      # still to be made
    assert LAD.order_done("SHW", "BRK9", NOW + dt.timedelta(hours=61)) and st.rows("Breakout_Queue")[0]["status"] == "DONE" and not MEM.find(type="problem_memo")
    closed = [x for x in MEM.rows(st) if x["type"] == "problem_memo"][0]; assert closed["status"] == "resolved" and closed["resolution"]["kind"] == "repair_verified" and closed["resolution"]["ref"] == "Specials:BRK9"

def test_an_order_twice_its_clock_old_lapses_and_the_memo_stays_open(monkeypatch, setting):
    _quiet(monkeypatch); st = core.store(); from whatifs.org import memos as MEM
    setting("FOLLOWUP_WITHIN_H", "24"); _short("SHW", "p", 1, now=NOW); q = LAD.order_followup("SHW", "yt_SHW", 9000, 1000, 24, NOW); assert q["due"] == core.iso(NOW + dt.timedelta(hours=24))
    assert LAD.watch(NOW + dt.timedelta(hours=25)) == ["SHW"] and "no try was recorded" in MEM.find(type="problem_memo")[0]["body"]["what_failed"]
    assert LAD.watch(NOW + dt.timedelta(hours=47)) == [] and LAD.watch(NOW + dt.timedelta(hours=49)) == ["SHW"] and st.rows("Breakout_Queue")[0]["status"] == "LAPSED"
    assert LAD.open_orders() == [] and SH.order_due(NOW + dt.timedelta(hours=50)) is None and len(MEM.find(type="problem_memo")) == 1 and LAD.watch(NOW + dt.timedelta(hours=90)) == []

# ------------------------------------------------------------------ 7. the real productions
def test_a_short_that_is_made_takes_its_step_and_its_footage_is_kept(monkeypatch, setting):
    _quiet(monkeypatch); _bench("What if the Moon left tonight?"); setting("SHORTS_REVIEW_FIRST_N", "0"); setting("UPLOAD_LOCK", "off")
    r = SH.run(force=True, now=NOW); assert r["ok"] and r["status"] == "POSTED"
    lr = _row(r["id"]); assert lr["state"] == "POSTED" and lr["yt_id"] == r["yt_id"] and lr["topic"] == r["id"] and lr["premise"] == "What if the Moon left tonight?" and lr["posted"] == core.iso(NOW)
    z = os.path.join(PUB._fake_drive(), lr["footage"]); names = zipfile.ZipFile(z).namelist()
    assert "short.json" in names and "c0.mp4" in names and "f0.png" in names and not any(n.startswith("c") and n.endswith(".mp4") and int(n[1:-4]) >= len(names) for n in names)
    kept = json.loads(zipfile.ZipFile(z).read("short.json")); assert kept["id"] == r["id"] and kept["plan"]["shots"][-1]["src"] == "loop" and f"c{kept['plan']['shots'][-1]['i']}.mp4" not in names      # the loop shot is the first clip again
    core.store().append("Premise_Bench", [{"bench_id": "B9", "premise": "What if gravity doubled?", "status": "READY", "combined": 5}])
    monkeypatch.setattr(PUB, "drive_upload", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("Drive is down")))
    r2 = SH.run(force=True, now=NOW + dt.timedelta(hours=48)); l2 = _row(r2["id"])
    assert r2["ok"] and l2["state"] == "POSTED" and not l2["footage"] and "footage not kept" in l2["note"]      # a Short is never lost because its footage could not be kept
    assert LAD.keep("SHX", str(core.WORK), {}, {"shots": []}, {}) == ""

def test_no_long_video_without_a_promoted_short_then_the_ladder_is_walked_end_to_end(monkeypatch, setting):
    import whatifs.voice as V
    from tools.rehearsal import ToneVoice
    from tools.sweep import climb
    from whatifs import episode as EP
    _quiet(monkeypatch); monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C"); _on(setting)
    def slot(h): return (core.now_utc() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st = core.store(); core.flush_costs(); spent0 = len(st.rows("Cost_Log"))
    r0 = EP.produce(slot(10), episode_id="EP209901010900")
    core.flush_costs(); assert r0 == {"ok": False, "skipped": "ladder", "why": r0["why"]} and not st.rows("Episodes") and len(st.rows("Cost_Log")) == spent0, r0      # refused before the first paid call
    assert climb(core, "EP209901010900") is True and _row("SH209901010900")["state"] == "POSTED"
    r = EP.produce(slot(10), episode_id="EP209901010900"); assert r.get("ok") and r.get("episode") == "EP209901010900", r
    e = st.rows("Episodes")[-1]; lr = _row("SH209901010900"); d = json.loads(e["draw_json"]) if isinstance(e["draw_json"], str) else e["draw_json"]
    assert lr["state"] == "USED" and lr["episode_id"] == "EP209901010900" and e["premise"] == lr["premise"] and d["ladder"] == "SH209901010900"
    led = {x["feature"]: (x["status"], x["evidence"]) for x in st.rows("Feature_Ledger") if x.get("episode_id") == "EP209901010900"}
    assert led["topic_ladder"][0] == "PASS" and "SH209901010900" in led["topic_ladder"][1] and not [k for k, v in led.items() if v[0] == "FAIL"]
    r2 = EP.produce(slot(34), episode_id="EP209901020900"); assert r2.get("skipped") == "ladder" and "already has its long video" in r2["why"]      # one Short, one long video

def test_a_long_video_that_slipped_past_the_gate_is_held_at_the_script_gate_before_any_picture(monkeypatch, setting):
    import whatifs.voice as V, whatifs.media as MD
    from tools.rehearsal import ToneVoice
    from whatifs import episode as EP
    _quiet(monkeypatch); monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C"); _on(setting)
    monkeypatch.setattr(LAD, "gate", lambda now=None: (True, "a path around the gate", None))      # some other way into production
    paid = []; real = MD.animate; monkeypatch.setattr(MD, "animate", lambda *a, **k: (paid.append(1), real(*a, **k))[1])
    r = EP.produce((core.now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), episode_id="EP209901010900")
    assert r.get("held") and "contract:topic_ladder" in r["problems"] and not paid, r               # written, judged, held - no picture and no clip was paid
    e = core.store().rows("Episodes")[-1]; assert e["status"] == "HOLD_QC" and "topic_ladder" in e["notes"]

def test_one_short_id_always_draws_the_same_hook(setting):
    """A Short's hook comes from the learning core's sampler. Seeded by the Short's id it is the same on every run (a fault can be reproduced) and still varies from Short to Short."""
    got = {i: {SH.hook_for("S1", [], f"SH20261216{i:04d}")["level"] for _ in range(6)} for i in range(40)}
    assert all(len(v) == 1 for v in got.values()) and len({next(iter(v)) for v in got.values()}) >= 2, got

# ------------------------------------------------------------------ 8. wiring, levers, the one-time move
def test_the_daily_cells_are_gone_everywhere_and_the_new_levers_are_registered(setting):
    from whatifs.org import registry as REG, levers as LV
    from whatifs import truth as TRU, caretaker as CT, replan as RP, dash as DS
    for k in ("SHORTS_PER_DAY", "SHORTS_KLING_EVERY", "REPLAN_MAX_SHORTS_PER_DAY"):
        assert k not in core.DEFAULTS and k not in LV.LEVERS and LV.owner_of(k) == "", k
    assert not hasattr(SH, "target_today") and not hasattr(__import__("whatifs.shortslab", fromlist=["x"]), "breakouts")
    assert {LV.owner_of(k) for k in ("SHORTS_PER_WEEK", "SHORTS_PER_MONTH", "SHORTS_BREAKOUT_X", "FOLLOWUP_WITHIN_H")} == {"D14"} and {LV.owner_of(k) for k in ("LADDER_WINDOW_DAYS", "LADDER_MIN_ENGAGED")} == {"D10"}
    assert LV.LEVERS["SHORTS_PER_WEEK"]["owner"] == "up" and LV.LEVERS["SHORTS_BREAKOUT_X"]["owner"] == "down" and LV.LEVERS["LADDER_WINDOW_DAYS"]["checks"] == ("topic_ladder",)
    assert ("whatifs/ladder.py", "promote") in REG.ENTRY["D10"] and "whatifs/ladder.py" in REG.DEPTS["D10"]["wraps"] and REG.check_owner("topic_ladder") == "D10" and not REG.entry_issues() and not REG.data_issues()
    assert "daily_shorts_cadence" in {r["id"] for r in TRU.RETIRED} and TRU.issues() == []
    assert CT.cadence_words() == "about 1 long video and 3 Shorts a week"
    setting("SHORTS_PER_WEEK", "4"); assert CT.cadence_words().endswith("4 Shorts a week")
    assert DS.route("SET|shorts_per_week|2") == (True, "SHORTS_PER_WEEK = 2") and DS.route("SET|shorts_per_week|9") == (True, "SHORTS_PER_WEEK = 5") and DS.route("SET|shorts_per_day|2")[0] is False
    assert {"Ladder"} <= set(core.TABS) and core.TABS["Breakout_Queue"][-2:] == ["due", "done"] and core.TABS["Analytics"][-2:] == ["days", "first_json"]

def test_the_replanner_offers_one_more_short_a_week_at_its_real_price(monkeypatch, setting):
    from whatifs import replan as RP
    mid = dt.datetime(2026, 12, 7, 6, 0, tzinfo=UTC)
    assert RP.short_inr() >= min(SH.est_inr(f) for f in FMT.SHORTS) > 100                           # every second of a Short is a paid clip: not the old planning figure of Rs 36
    monkeypatch.setattr(RP, "free_inr", lambda now=None: 10 ** 6); p = RP.proposals(mid)
    assert [(x["rung"], x["key"], x["to"]) for x in p] == [(2, "SHORTS_PER_WEEK", "4")] and p[0]["cost"] == round(RP.days_left(mid) / 7.0 * RP.short_inr())
    setting("SHORTS_PER_WEEK", "4"); assert RP.proposals(mid) == []                                 # the top of the band
    setting("SHORTS_PER_WEEK", "3"); monkeypatch.setattr(RP, "free_inr", lambda now=None: 100.0); assert RP.proposals(mid) == []
    monkeypatch.setattr(RP, "free_inr", lambda now=None: 10 ** 6); assert RP.proposals(dt.datetime(2026, 12, 28, 6, 0, tzinfo=UTC)) == []      # under a week left: nothing to add

def test_a_live_sheet_is_moved_once(setting):
    st = core.store()
    st.append("Settings", [{"key": "SHORTS_PER_DAY", "value": "2", "note": "v11: standalone Shorts per day"}, {"key": "SHORTS_KLING_EVERY", "value": "3", "note": "x"}])
    setting("REPLAN_PENDING", json.dumps([{"rung": 2, "key": "SHORTS_PER_DAY", "to": "2.0"}, {"rung": 2, "key": "SHORTS_PER_WEEK", "to": "4"}])); setting("REPLAN_ORIGINALS", json.dumps({"SHORTS_KLING_EVERY": "3", "ANIM_SHOTS": "4"}))
    done = MG.v12v2cb_upgrade(st); assert done == ["SHORTS_PER_DAY", "SHORTS_KLING_EVERY", "REPLAN_PENDING", "REPLAN_ORIGINALS"], done
    rows = {r["key"]: r for r in st.rows("Settings")}
    assert rows["SHORTS_PER_DAY"]["note"].startswith("RETIRED (v12 V2c-b)") and "SHORTS_PER_WEEK" in rows["SHORTS_PER_DAY"]["note"] and rows["SHORTS_PER_DAY"]["value"] == "2"      # the value is left as he last saw it
    assert json.loads(core.S("REPLAN_PENDING")) == [{"rung": 2, "key": "SHORTS_PER_WEEK", "to": "4"}] and json.loads(core.S("REPLAN_ORIGINALS")) == {"ANIM_SHOTS": "4"}
    st.update("Settings", "key", "SHORTS_PER_DAY", {"note": "typed by hand"}); assert MG.v12v2cb_upgrade(st) == [] and core.S("V12V2CB_FLIPS_DONE")      # never twice
    assert open(MG.__file__, encoding="utf-8").read().count("try: v12v2cb_upgrade(st)") == 2      # both setup paths call it
