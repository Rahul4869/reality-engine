"""v12 V4 - the CEO and the ladder: the scoreboard, finance wired, the loop of decisions, the rule book, the watch book, the arm book, one rule
for a breakout, the owner's desk. Every rule is proven both ways; the real code path is run, so an unwired call is seen."""
import json, os
import pytest
from whatifs import core, contract as CON, episode as EP
from whatifs.org import runner as RUN, layman as LAY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()

# ------------------------------------------------------------------ step 0: open issue 200 (the organisation off loses a native run's result)
TITLE = "What If Your Reflection Was One Second Late?"
GOOD = "You stop brushing your teeth. Your reflection does not. It is one second late, and it is looking straight at you."
def U(opening): return [{"start": 0.0, "end": 9.0, "text": opening}, {"start": 41.0, "end": 45.0, "text": "By noon the whole town has noticed."}]

def test_with_the_organisation_off_a_native_run_hands_back_its_output_and_a_plain_run_its_value(setting):
    setting("ORG_ON", "FALSE"); assert not RUN.on()
    assert RUN.work("D4", "write", "EP1", lambda b: RUN.Out({"a": 1})) == {"a": 1}                  # a native run: its output, not the Out object
    assert RUN.work("D4", "write", "EP1", lambda b: {"a": 2}) == {"a": 2}                           # a plain run: its value, unchanged
    r = RUN.run("D4", "write", lambda b: RUN.Out([3], memos=[{"x": 1}])); assert r.status == "off" and r.output == [3]

def test_with_the_organisation_off_the_promise_line_up_is_judged_not_lost(setting):
    setting("ORG_ON", "FALSE")
    s0 = {"pkg": {"titles": [TITLE]}, "d": {}, "room": {"script": {"script": GOOD}}}
    p = EP._probe(s0, "EP1", U(GOOD)); assert isinstance(p, dict) and p["status"] == "pass", p                # D13's probe as the plan stage runs it
    assert CON.p_viewer_probe({"probe": p})[0] == CON.PASS                                                  # judged with the organisation off - not N/A

# ------------------------------------------------------------------ step 1: the scoreboard (whatifs/scoreboard.py, tab Scoreboard)
import datetime as dt
from whatifs import scoreboard as SB, digests as DG, notify as NT, owner_view as OV, governor as G, truth as TRU

SB_NOW = dt.datetime(2026, 11, 16, 4, 0, tzinfo=dt.timezone.utc)
WORKED = ("Scoreboard: 40 of 1,000 subscribers (about 960 days at this pace) | Shorts views that count: 200,000 of 10,000,000 in 90 days - 2,222 a day,"
          " the bar needs 111,111 | long watch hours: 12.5 of 4,000 in 12 months - 0.03 a day, the bar needs 11.0. The bars rise on 01 Feb 2027: 8,000 hours"
          " or 20,000,000 Shorts views.")
def plant(*rows): core.store().append("Scoreboard", [dict({"hours": 12.5, "shorts_90": 200000, "src": "test"}, **r) for r in rows])

def test_the_scoreboard_line_is_the_partner_programs_own_numbers_word_for_word(setting):
    setting("STRATEGY_ON", "TRUE")
    assert SB.line(SB_NOW) == "Scoreboard: no reading yet (the first comes with the daily learning job)."
    plant({"date": "2026-10-19", "subs": 12}, {"date": "2026-11-16", "subs": 40})
    assert SB.sub_pace(SB._rows(), SB_NOW) == 1.0 and SB.eta(40, 1000, 1.0) == 960 and SB.eta(1000, 1000, None) == 0 and SB.eta(5, 1000, 0) is None
    assert SB.line(SB_NOW) == WORKED
    setting("SCOREBOARD_ELIGIBLE_PCT", "80"); assert "the bar needs 11.0 (counted at 80% eligible). The bars rise on 01 Feb 2027" in SB.line(SB_NOW)

@pytest.mark.parametrize("old, today, says", [
    (None, 40, "40 of 1,000 subscribers (no pace yet: 28 days of readings are needed)"),
    (12, 1000, "1000 of 1,000 subscribers (reached)"),
    (12, 13, "13 of 1,000 subscribers (more than 10 years at this pace)"),               # 987 / (1/28) = 27,636 days
    (12, 12, "12 of 1,000 subscribers (more than 10 years at this pace)"),               # no pace up: the bar is never reached at this pace
    (12, "", "Scoreboard: subscribers: no reading | Shorts views that count"),
])
def test_each_pace_is_said_as_it_is(setting, old, today, says):
    setting("STRATEGY_ON", "TRUE")
    plant(*([{"date": "2026-10-19", "subs": old}] if old is not None else []), {"date": "2026-11-16", "subs": today})
    assert says in SB.line(SB_NOW), SB.line(SB_NOW)

def test_the_bars_are_data_and_the_rise_is_said_until_it_comes(setting):
    setting("STRATEGY_ON", "TRUE"); plant({"date": "2027-02-01", "subs": 40})
    after = SB.line(dt.datetime(2027, 2, 1, 4, 0, tzinfo=dt.timezone.utc))
    assert "of 8,000 in 12 months" in after and "of 20,000,000 in 90 days" in after and "The bars rise" not in after and after.endswith("the bar needs 21.9.")
    setting("YPP_BARS", json.dumps([{"until": "", "subs": 500, "hours": 3000, "shorts": 3000000}]))
    assert "40 of 500 subscribers" in SB.line(SB_NOW) and "of 3,000 in 12 months" in SB.line(SB_NOW)

def test_one_reading_a_day_kept_by_the_daily_learning_job(setting):
    from whatifs import manage as MG
    MG.learn(); assert core.store().rows("Scoreboard") == []                                  # STRATEGY_ON FALSE: exactly the code V4 is built on
    setting("STRATEGY_ON", "TRUE"); MG.learn()
    rows = core.store().rows("Scoreboard"); assert [r["date"] for r in rows] == [core.now_utc().date().isoformat()] and rows[0]["subs"] == ""   # fake mode: no subscriber reading
    assert SB.keep() is None and len(core.store().rows("Scoreboard")) == 1                    # a second call on that date changes nothing
    assert SB.keep(core.now_utc() + dt.timedelta(days=1))["date"] == (core.now_utc() + dt.timedelta(days=1)).date().isoformat()

def test_the_scoreboard_is_the_first_thing_after_the_head_of_both_briefs(monkeypatch, setting):
    from whatifs import publish as PUB
    setting("STRATEGY_ON", "TRUE"); plant({"date": "2026-10-19", "subs": 12}, {"date": "2026-11-16", "subs": 40})
    for kind in ("daily", "weekly"):
        for demo in (False, True):
            parts = DG.compose(kind, demo=demo, now=SB_NOW)[0].split("\n\n")
            assert parts[0].startswith("*") and ("Morning brief" in parts[0] or "Weekly brief" in parts[0]) and parts[1] == WORKED, (kind, demo, parts[:2])
    mails = []; monkeypatch.setattr(PUB, "email", lambda subject, html, *a, **k: (mails.append(html), True)[1])
    assert NT.digest(now=SB_NOW, force=True) and mails[0].startswith("<p>" + WORKED + "</p><p><b>Mode:</b>")
    setting("STRATEGY_ON", "FALSE"); mails.clear()
    assert DG.compose("daily", now=SB_NOW)[0].split("\n\n")[1] != WORKED and NT.digest(now=SB_NOW, force=True) and mails[0].startswith("<p><b>Mode:</b>")

def test_the_stale_shorts_sentence_is_retired_and_the_money_shows_the_cap_in_force(monkeypatch, setting):
    monkeypatch.setattr(OV, "today", lambda: {"next_slot": {"ist": "Tue 18 Nov 18:00"}})
    assert OV.strategy()["plan"][0] == "Next slot Tue 18 Nov 18:00: a long video about the Short viewers picked (three Shorts a week, each a topic of its own)."
    assert "shorts_cut_from_it" in [r["id"] for r in TRU.hits("Next slot Tue: long video, then 2-4 Shorts cut from it over the next days.", "docs")]
    setting("BUDGET_CEILING_INR", "9000"); setting("BUDGET_FLOOR_INR", "6000")
    assert OV.money()["cap"] == int(round(G.cap_inr())) != 9000                               # the cap in force (no revenue in a fresh store), not the ceiling cell

# ------------------------------------------------------------------ step 2: finance is wired, and the money is his own (whatifs/org/finance.py, governor)
from whatifs import costguard as CG, shorts2 as SH, publish as PUB
from whatifs.org import finance as FIN, registry as REG, levers as LV, memos as MEM
from tests import paid_calls as PC

def day(d): return d.strftime("%Y-%m-%d")
def cost(ts, inr, provider="anthropic", basis="measured", ep="EPX", item="claude_writer"):
    core.store().append("Cost_Log", [{"ts": ts, "episode_id": ep, "item": item, "provider": provider, "units": 1, "inr": inr, "basis": basis, "role": "writer"}])
    FIN.forget(); core._base["v"] = None
def lane(setting, usd="200", frm="2026-12-10", until="2027-01-10"):
    setting("STRATEGY_ON", "TRUE"); setting("USD_INR", "99"); setting("CLAUDE_CREDIT_USD_MONTH", usd); setting("CLAUDE_CREDIT_FROM", frm); setting("CLAUDE_CREDIT_UNTIL", until); FIN.forget()
def cap5000(setting): setting("BUDGET_CEILING_INR", "5000"); setting("BUDGET_FLOOR_INR", "5000"); setting("BUDGET_MODE", "standard")

def test_time_can_be_planted_and_the_months_slots_are_counted(setting):
    setting("PUBLISH_DAYS", "Sat")
    nov = dt.datetime(2026, 11, 2, 12, 0, tzinfo=dt.timezone.utc)                                       # Mon 2 Nov 2026: the Saturdays are the 7th, 14th, 21st, 28th
    assert G.slots(nov) == 4 and G.slots(nov, left=True) == 4 and G.episodes_left_this_month(nov) == 4
    late = dt.datetime(2026, 11, 29, 12, 0, tzinfo=dt.timezone.utc)
    assert G.slots(late) == 4 and G.slots(late, left=True) == 0 and G.episodes_left_this_month(late) == 1      # after the month's last slot
    core.store().append("Episodes", [{"episode_id": "EPN", "slot_et": "2026-11-07T10:00:00", "status": "LIVE"}])
    assert G.long_videos_this_month(nov) == 1 and G.long_videos_this_month(dt.datetime(2026, 12, 1, 12, tzinfo=dt.timezone.utc)) == 0

def test_month_fit_is_the_splits_own_arithmetic_for_other_counts(setting):
    now = core.now_utc(); setting("MONTH_CAP_OVERRIDES", f"{now:%Y-%m}=20000"); checked = 0
    for n_short in (12, 4, 20):
        setting("SHORTS_PER_MONTH", str(n_short)); sp = G.split(now); mf = G.month_fit(G.max_long_videos(), n_short, now=now)
        if sp["fits"]:
            assert mf["free_inr"] == sp["free_inr"] and mf["fits"], (n_short, sp, mf); checked += 1
    assert checked >= 1
    big = G.month_fit(G.max_long_videos(), 12, extra_inr=10 ** 6, now=now); assert not big["fits"] and big["free_inr"] < 0

def test_the_credit_is_a_dated_relief_with_a_meter_of_our_own(setting):
    lane(setting)                                                                                       # USD 200 at Rs 99 = 19,800; usable 16,830; 10 Dec to 10 Jan
    cost("2026-12-12T10:00:00Z", 900); cost("2027-01-05T10:00:00Z", 300)
    jan = dt.datetime(2027, 1, 6, 6, 0, tzinfo=dt.timezone.utc); c = FIN.credit(jan)
    assert (c["amount_inr"], c["spent_inr"], c["left_inr"], c["covered_month"], c["open"], c["until"]) == (19800, 1200, 18600, 300, True, "2027-01-10")
    for ts, prov, basis in (("2027-01-11T00:00:00Z", "anthropic", "measured"), ("2026-12-09T23:00:00Z", "anthropic", "measured"),
                            ("2027-01-05T00:00:00Z", "google", "measured"), ("2027-01-05T00:00:00Z", "anthropic", "summary")):
        cost(ts, 500, provider=prov, basis=basis); assert FIN.credit(jan)["spent_inr"] == 1200, (ts, prov, basis)      # outside the window, another provider, a summary
    assert not FIN.credit(dt.datetime(2027, 1, 11, 6, tzinfo=dt.timezone.utc))["open"]                   # the day after UNTIL: closed
    cost("2026-12-20T10:00:00Z", 15100); cost("2027-01-06T01:00:00Z", 1700)                              # Rs 16,000 before this month, Rs 2,000 in it
    c = FIN.credit(jan); assert c["covered_month"] == 830 and c["left_inr"] == 1800 and not c["open"]    # 16,830 - 16,000; Rs 1,800 left is under the floor: closed
    setting("STRATEGY_ON", "FALSE"); assert FIN.cover(jan) == 0.0 and FIN.lane(jan) is None and FIN.boost("THINK_BOOST_VARIANTS", jan) == 0

def test_the_cap_stays_a_breaker_beyond_the_credits_monthly_most(setting):
    now = core.now_utc(); cap5000(setting); lane(setting, frm=day(now.replace(day=1)), until=day(now + dt.timedelta(days=20)))
    cost(core.iso(now), 9000)                                                                           # Rs 9,000 of Claude rows in an open window this month
    assert FIN.cover() == core.S("CREDIT_COVER_MONTH_MAX_INR", float) and G.own_spend_inr() == 9000 - FIN.cover() and G.monthly_cap_reached()

def test_closed_the_money_is_the_bases_and_open_no_word_says_more_than_his_own(monkeypatch, setting):
    now = core.now_utc(); cap5000(setting); texts = []
    monkeypatch.setattr(PUB, "email", lambda subject, html, *a, **k: (texts.append(str(subject) + " " + str(html)), True)[1])
    monkeypatch.setattr(NT, "send", lambda kind, text, *a, **k: texts.append(str(text)))
    cost(core.iso(now), 4400, provider="fal", item="image"); cost(core.iso(now), 900)                  # a month whose list spend is Rs 5,300; Rs 900 of it Claude's
    assert (G.own_spend_inr(), G.remaining_inr(), OV.money()["month_spend"], FIN.cover()) == (5300, -300, 5300, 0.0)     # closed (STRATEGY_ON FALSE): the base's figures
    lane(setting, usd="100", frm=day(now.replace(day=1)), until=day(now + dt.timedelta(days=20)))       # Rs 9,900, usable 6,930: the Rs 900 is covered
    assert FIN.cover() == 900 and G.own_spend_inr() == 4400 and G.remaining_inr() == 600 and OV.money()["month_spend"] == 4400
    ok, why = G.extras_allowed(50); assert not why.startswith("paused: the month is at")                # the 90% guard (Rs 4,500) does not fire
    CG.spend_monitor(); NT.digest(now=now, force=True)
    brief = DG.compose("weekly", now=now)[0]; texts.append(brief)
    assert "Your money this month: Rs 4400 of Rs 5000. Claude credit paid another Rs 900." in brief and "at list price" in brief
    assert any("Your money this month: Rs 4400 of Rs 5000. Claude credit paid another Rs 900." in t for t in texts if "<p>" in t)
    assert not [t for t in texts if "5300" in t or "5,300" in t], [t[:120] for t in texts if "5300" in t or "5,300" in t]

def test_the_router_knows_the_credit_and_no_top_up_mail_while_it_lasts(monkeypatch, setting):
    from whatifs import manage as MG
    now = core.now_utc(); last = (now.replace(day=1) - dt.timedelta(days=1)); mails = []
    monkeypatch.setattr(PUB, "email", lambda subject, html, *a, **k: (mails.append((str(subject), str(html))), True)[1])
    setting("ANTHROPIC_FUNDED_USD", "25"); setting("AUTO_RELOAD_ON", "FALSE")
    cost("2026-01-05T00:00:00Z", 50); cost(core.iso(last.replace(day=10)), 2920)                         # lifetime Claude spend USD 30 (funded 25), none of it this month
    lane(setting, usd="80", frm=day(last.replace(day=1)), until=day(now + dt.timedelta(days=20)))       # Rs 7,920 less the Rs 2,920 of the window: Rs 5,000 left
    assert FIN.lane()["left_inr"] == 5000 and G.claude_allowed() and G.runway_days("anthropic") == 999
    MG.money_check(); assert not [h for s, h in mails if s == "Top-up reminder" and "Anthropic" in h]
    setting("STRATEGY_ON", "FALSE"); mails.clear()                                                      # closed: as the base
    assert not G.claude_allowed() and G.runway_days("anthropic") < 999
    MG.money_check(); assert [h for s, h in mails if s == "Top-up reminder" and "Anthropic" in h]

def test_one_boost_ends_by_itself_on_the_windows_last_day(monkeypatch, setting):
    from tests.test_v12_short import _writer, MOON
    now = core.now_utc(); lane(setting, frm=day(now - dt.timedelta(days=1)), until=day(now + dt.timedelta(days=5))); setting("THINK_BOOST_VARIANTS", "2")
    asked = _writer(monkeypatch); sc = SH.write({"premise": MOON}, "S1", "you_pov", "SHT1", [])
    assert asked.count("short_script") == 3 + PC.V12V4_ADDED["text:short_writer"] and sc["_write"]["asked"] == 5 and sc["_write"]["won"] in range(5)
    L = {l["key"]: l for l in CG.lines("short", fmt="S1")}
    assert L["boost_variants"]["inr"] == 2 * core.S("SHORT_VARIANT_EST_INR", float) and L["boost_variants"]["calls"] == {"text:short_writer": 2}
    setting("CLAUDE_CREDIT_UNTIL", day(now - dt.timedelta(days=1))); FIN.forget()                      # the day after UNTIL: the cell still says 2
    asked.clear(); SH.write({"premise": MOON}, "S1", "you_pov", "SHT2", []); assert asked.count("short_script") == 3
    assert [l["key"] for l in CG.lines("short", fmt="S1")] == ["hero_clips", "pictures", "writing", "voice"]
    setting("CLAUDE_CREDIT_UNTIL", day(now + dt.timedelta(days=5))); setting("STRATEGY_ON", "FALSE")
    asked.clear(); SH.write({"premise": MOON}, "S1", "you_pov", "SHT3", []); assert asked.count("short_script") == 3

def _summary(ep, kind, d, ts):
    core.store().append("Cost_Log", [{"ts": core.iso(ts), "episode_id": ep, "item": "cost_lines_summary", "provider": "summary", "units": 0, "inr": 0, "basis": "summary",
                                      "role": (f"{kind}: " + (json.dumps(d) if isinstance(d, dict) else d))[:900]}])

def test_finance_watch_keeps_the_months_cover_and_turns_an_overrun_into_a_memo(setting):
    now = core.now_utc(); mk = now.strftime("%Y-%m"); lane(setting, frm=day(now.replace(day=1)), until=day(now + dt.timedelta(days=20)))
    clean = {"paid": {}, "lines": {}, "unlisted": [], "over": []}
    _summary("EP0", "long", clean, now - dt.timedelta(hours=5))
    _summary("EP1", "long", dict(clean, over=["hero_clip: 30 paid, 24 estimated"]), now - dt.timedelta(hours=4))
    _summary("EP3", "ladder", dict(clean, unlisted=["fal_mystery"]), now - dt.timedelta(hours=3))
    _summary("SHT1", "short", '{"paid": {"hero_cl', now - dt.timedelta(hours=2))                          # cut at 900 characters: does not parse
    cost(core.iso(now), 700)
    RUN.run("D11", "watch", FIN.watch)
    ms = {m["dedupe_key"]: m for m in MEM.find(type="problem_memo", from_dept="D11")}
    assert set(ms) == {"overrun|EP1", "overrun|EP3", "overrun|SHT1"} and all(m["to_depts"] == ["D12"] for m in ms.values())
    assert ms["overrun|EP1"]["subject"] == "A video cost more than its estimate: EP1" and ms["overrun|EP1"]["body"]["what_failed"] == "hero_clip: 30 paid, 24 estimated"
    assert ms["overrun|EP3"]["body"]["what_failed"] == "paid with no line: fal_mystery" and ms["overrun|EP3"]["body"]["error_class"] == "cost_overrun"
    assert ms["overrun|SHT1"]["body"]["what_failed"] == "the cost summary of SHT1 is cut and cannot be read" and ms["overrun|SHT1"]["body"]["where"] == "Cost_Log:SHT1"
    assert json.loads(core.S("CLAUDE_CREDIT_COVERED")) == {mk: 700} and FIN.cover() == 700
    setting("CLAUDE_CREDIT_FROM", day(now + dt.timedelta(days=1))); FIN.forget()                       # he types the next cycle's window: the old rows fall out of the sum
    assert FIN.credit()["covered_month"] == 0 and FIN.cover() == 700                                    # the month keeps what it had
    _summary("EP2", "long", clean, now + dt.timedelta(minutes=2)); RUN.run("D11", "watch", FIN.watch)
    left = {m["dedupe_key"] for m in MEM.find(type="problem_memo", from_dept="D11")}
    assert left == {"overrun|EP3", "overrun|SHT1"} and json.loads(core.S("CLAUDE_CREDIT_COVERED")) == {mk: 700}     # a later clean long video closes EP1's, not the others
    done = next(m for m in MEM.find(live=False, type="problem_memo", from_dept="D11") if m["dedupe_key"] == "overrun|EP1")
    assert done["status"] == "resolved" and done["resolution"]["kind"] == "repair_verified" and done["resolution"]["ref"] == "Cost_Log:EP2"

def test_the_ceos_round_runs_only_when_a_decision_could_become_a_ticket(monkeypatch, setting):
    from whatifs import cli as CLI
    calls = []; monkeypatch.setattr(FIN, "watch", lambda b: (calls.append(1), RUN.Out({"ok": 1}))[1])
    assert CLI.strategy_round() is False and calls == []                                                 # STRATEGY_ON FALSE (the older tests): no watch
    setting("STRATEGY_ON", "TRUE"); setting("EXEC_ON", "FALSE"); assert CLI.strategy_round() is False and calls == []
    setting("EXEC_ON", "TRUE"); setting("PAUSED", "TRUE"); assert CLI.strategy_round() is False and calls == []
    setting("PAUSED", "FALSE"); assert CLI.strategy_round() is True and calls == [1]
    setting("ORG_ON", "FALSE"); assert CLI.strategy_round() is False and calls == [1]
    assert ("whatifs/cli.py", "watch") in REG.ENTRY["D11"] and "D11" not in REG.PENDING and "whatifs/org/finance.py" in REG.DEPTS["D11"]["wraps"] and REG.entry_issues() == []
    assert "MONTH_RESERVE_INR" in REG.DEPTS["D11"]["levers"] and "THINK_BOOST_VARIANTS" in REG.DEPTS["D1"]["levers"] and LV.issues() == []
    assert 'lambda b: learn(), measure=WR.m_learn); strategy_round(); ORG.daily_check()' in open(os.path.join(ROOT, "whatifs", "cli.py"), encoding="utf-8").read()
    from tools import repair as RP; assert "whatifs/org/finance.py" in RP.PROTECTED and "whatifs/scoreboard.py" in RP.PROTECTED

# ------------------------------------------------------------------ step 3: the loop (whatifs/org/strategy.py; D1's run `review`; the rule SLOTS)
from whatifs.org import strategy as STR, execute as EX
from whatifs import notify as NTF

JAN = dt.datetime(2027, 1, 1, 12, 0, tzinfo=dt.timezone.utc)          # Fri 1 Jan 2027: five Saturdays (2, 9, 16, 23, 30)
FEB = dt.datetime(2027, 2, 1, 12, 0, tzinfo=dt.timezone.utc)          # Mon 1 Feb 2027: four Saturdays
def ceo(setting, cap="20000"):
    setting("STRATEGY_ON", "TRUE"); setting("PUBLISH_DAYS", "Sat"); setting("BUDGET_MODE", "standard")
    setting("BUDGET_CEILING_INR", cap); setting("BUDGET_FLOOR_INR", cap); setting("SHORTS_PER_MONTH", "12")
def at(monkeypatch, t): monkeypatch.setattr(STR, "now_utc", lambda: t)
def plant_target(monkeypatch, key, target, why="planted"):
    monkeypatch.setattr(STR, "targets", lambda now=None: {key: {"target": target, "why": why, "numbers": {}, "evidence": "ok", "count": "", "rule": STR.rule_of(key)["id"] if STR.rule_of(key) else "SLOTS"}})
def decisions(): return core.store().rows("Decisions")

def test_rule_slots_moves_one_step_when_the_calendar_and_the_money_hold_five(setting):
    ceo(setting)
    t = STR.targets(JAN)["STANDARD_MAX_LONG_PER_MONTH"]; assert t["target"] == 5 and t["rule"] == "SLOTS" and "5 publishing days" in t["why"]
    c, refused = STR.next_move(JAN); assert (c["key"], c["old"], c["new"], c["rule"], c["effect_before"], c["effect_after"]) == ("STANDARD_MAX_LONG_PER_MONTH", "4", "5", "SLOTS", 4, 5) and refused == []
    row, memo = STR.decide(c, JAN); assert row["state"] == "decided" and row["id"].startswith("DEC-") and len(row["id"]) == 14 and memo["from_dept"] == "D1"
    assert memo["body"]["lever_class"] == "B" and memo["body"]["target"] == "STANDARD_MAX_LONG_PER_MONTH" and memo["body"]["value"] == "5" and memo["body"]["decision_ref"] == row["id"]
    assert memo["dedupe_key"] == f"strategy|{row['id']}" and memo["subject"] == "Strategy: 5 long videos a month instead of 4" and memo["to_depts"] == ["D1"]
    assert json.loads(row["prediction"])["metric"] == "long_hours_per_video_28d" and json.loads(row["prediction"])["board"] == "hours"
    assert STR.next_move(JAN)[0] is None                                                                # one decision in force on a key: nothing more on it

def test_a_four_saturday_month_holds_five_at_its_target_and_the_three_gates_refuse_in_words(monkeypatch, setting):
    ceo(setting); setting("STANDARD_MAX_LONG_PER_MONTH", "5")
    assert STR.targets(FEB)["STANDARD_MAX_LONG_PER_MONTH"]["target"] == 4 and STR.at_target("STANDARD_MAX_LONG_PER_MONTH", 4, FEB)   # 5 does what 4 does: nothing is moved back for ever
    assert STR.next_move(FEB) == (None, [])
    setting("STANDARD_MAX_LONG_PER_MONTH", "4"); plant_target(monkeypatch, "STANDARD_MAX_LONG_PER_MONTH", 5)
    assert STR.next_move(FEB) == (None, [])                                                             # 4 is AT a target of 5 here (effect 4 both): passed without a word (D-STR9)
    setting("STANDARD_MAX_LONG_PER_MONTH", "7"); plant_target(monkeypatch, "STANDARD_MAX_LONG_PER_MONTH", 4)
    c, refused = STR.next_move(JAN); assert c is None and refused == ["not taken: STANDARD_MAX_LONG_PER_MONTH 7 -> 6 changes nothing the code does (5)"]      # EFFECT: one step inside the five slots
    setting("STANDARD_MAX_LONG_PER_MONTH", "4"); plant_target(monkeypatch, "STANDARD_MAX_LONG_PER_MONTH", 5)
    ceo(setting, cap="3000")                                                                            # JAN has five slots, but the money does not hold a fifth video
    c, refused = STR.next_move(JAN); assert c is None and refused[0].startswith("not taken: STANDARD_MAX_LONG_PER_MONTH 4 -> 5: the month would need Rs ") and " and has Rs " in refused[0]   # FIT
    plant_target(monkeypatch, "STANDARD_MAX_LONG_PER_MONTH", 3); ceo(setting)
    c, refused = STR.next_move(JAN); assert c is None and refused == ["not taken: STANDARD_MAX_LONG_PER_MONTH 4 -> 3: STANDARD_MAX_LONG_PER_MONTH 3 is outside the allowed range 4 to 8"]   # RANGE

def test_one_decision_a_review_and_three_in_seven_days(monkeypatch, setting):
    ceo(setting); keys = ("FORMAT_SHARE_F1", "FORMAT_SHARE_F2", "FORMAT_SHARE_F3", "THINK_BOOST_VARIANTS")
    monkeypatch.setattr(STR, "PORTFOLIO", keys)
    monkeypatch.setattr(STR, "targets", lambda now=None: {"FORMAT_SHARE_F1": {"target": "40", "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"},
                                                           "FORMAT_SHARE_F2": {"target": "40", "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"},
                                                           "FORMAT_SHARE_F3": {"target": "40", "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"},
                                                           "THINK_BOOST_VARIANTS": {"target": "2", "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"}})
    monkeypatch.setattr(STR, "rule_of", lambda key: {"id": "T", "metric": "shorts_engaged_90d", "board": "shorts", "direction": "up", "horizon": 4})
    monkeypatch.setattr(STR, "effect", lambda key, value, now=None: str(value))
    moved = []
    for d in range(4):
        c, _r = STR.next_move(JAN + dt.timedelta(days=d))
        if c: STR.decide(c, JAN + dt.timedelta(days=d)); moved.append(c["key"])
    assert moved == ["FORMAT_SHARE_F1", "FORMAT_SHARE_F2", "FORMAT_SHARE_F3"]                          # one a review; the fourth day: three in seven days already
    assert STR.next_move(JAN + dt.timedelta(days=3))[1] == ["not taken: 3 decisions in seven days already"]

def test_the_ticket_is_told_once_it_exists_and_the_brief_carries_the_whole_text_and_its_undo_link(monkeypatch, setting):
    from whatifs.org import memos as MEMO
    ceo(setting); at(monkeypatch, JAN); monkeypatch.setenv("GH_REPO", "owner/repo")
    c, _ = STR.next_move(JAN); row, memo = STR.decide(c, JAN)
    assert STR.tell(JAN) == 0 and not [a for a in core.store().rows("Owner_Actions") if a.get("kind") == "strategy"]     # the ticket write failed: nothing is said
    MEMO.write(memo); assert STR.tell(JAN) == 1 and STR.tell(JAN) == 0
    a = next(a for a in core.store().rows("Owner_Actions") if a.get("kind") == "strategy")
    assert a["text"] == STR.text_of(decisions()[0]) and a["text"].startswith("Strategy decided: 5 long videos a month instead of 4 (STANDARD_MAX_LONG_PER_MONTH 4 -> 5). Why: ")
    assert "Nothing to do - tap Undo to take it back." in a["text"] and json.loads(a["buttons"]) == [["Undo", f"STRATEGY UNDO {row['id']}"]] and not a["expires_at"]
    b = STR.brief(JAN + dt.timedelta(hours=20))
    assert b.startswith("*Decisions*\n- Strategy decided: 5 long videos") and "Undo: https://github.com/owner/repo/issues/new?title=" in b and "Strategy, week of" in b
    assert a["kind"] in NTF.INFORM_KINDS and not [r for r in NTF.open_rows() if r.get("kind") not in NTF.INFORM_KINDS]

def test_a_day_without_a_decision_says_no_change_or_the_first_refusal(monkeypatch, setting):
    ceo(setting); setting("STRATEGY_WEEKLY_AT", core.iso(JAN))
    assert STR.brief(JAN) == "*Decisions*\n- Strategy today: no change."
    setting("STRATEGY_TODAY", json.dumps({"refused": ["not taken: X 1 -> 2 changes nothing the code does (1)"], "counting": []}))
    assert STR.brief(JAN) == "*Decisions*\n- Not taken today: not taken: X 1 -> 2 changes nothing the code does (1)."
    setting("STRATEGY_TODAY", json.dumps({"refused": [], "counting": ["S1 5 of 8 Shorts", "S2 4 of 8"]}))
    assert STR.brief(JAN) == "*Decisions*\n- Strategy today: no change. Counting: S1 5 of 8 Shorts, S2 4 of 8."
    setting("STRATEGY_ON", "FALSE"); assert STR.brief(JAN) == ""

def test_what_was_shown_is_stamped_only_when_it_went(monkeypatch, setting):
    from whatifs import wa as WA
    ceo(setting); c, _ = STR.next_move(JAN); STR.decide(c, JAN)
    monkeypatch.setattr(DG, "FAKE", False); monkeypatch.setattr(WA, "configured", lambda: False)
    monkeypatch.setattr(PUB, "email", lambda *a, **k: False)                                            # the e-mail failed
    DG.send("daily", now=JAN + dt.timedelta(hours=20)); assert decisions()[0]["briefed"] == ""        # nothing stamped: the next brief carries it
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    DG.send("daily", now=JAN + dt.timedelta(hours=21)); assert decisions()[0]["briefed"] == core.iso(JAN + dt.timedelta(hours=21))
    assert core.S("STRATEGY_WEEKLY_AT") == core.iso(JAN + dt.timedelta(hours=21))

def test_his_hand_on_a_portfolio_cell_is_recorded_once_said_in_the_week_and_frozen(setting):
    from whatifs.org import runner as RN
    ceo(setting); setting("STANDARD_MAX_LONG_PER_MONTH", "6")                                         # set by hand in the Sheet
    RN.run("D1", "review", STR.review); RN.run("D1", "review", STR.review)                              # two reviews: ONE hand row
    h = [r for r in decisions() if r["state"] == "hand"]; assert len(h) == 1 and h[0]["key"] == "STANDARD_MAX_LONG_PER_MONTH" and h[0]["new"] == "6"
    assert core.parse_iso(h[0]["frozen_until"]) > core.now_utc() + dt.timedelta(days=27) and not [r for r in decisions() if r["state"] == "decided"]   # the key is frozen
    assert "Outside Strategy: STANDARD_MAX_LONG_PER_MONTH = 6 - counted as your own values and left alone for 28 days." in STR.weekly(core.now_utc() + dt.timedelta(hours=1))

def test_a_decision_is_a_ticket_or_the_check_fails_only_text(monkeypatch, setting):
    from whatifs.org import runner as RN, memos as MEMO
    setting("STRATEGY_ON", "TRUE"); setting("ORG_SINCE", core.iso(now() - dt.timedelta(days=3))); monkeypatch.setattr(STR, "PORTFOLIO", ("FORMAT_SHARE_F1",))
    monkeypatch.setattr(STR, "targets", lambda now=None: {"FORMAT_SHARE_F1": {"target": "40", "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"}})
    monkeypatch.setattr(STR, "rule_of", lambda key: {"id": "T", "metric": "shorts_engaged_90d", "board": "shorts", "direction": "up", "horizon": 4})
    setting("FORMAT_SHARE_F1", "60"); monkeypatch.setattr(STR, "effect", lambda key, value, now=None: str(value))   # the default (conftest's 70 would be his hand) and an effect
    RN.run("D1", "review", STR.review); r = decisions()[0]
    assert r["state"] == "decided" and MEMO.get(r["ticket"]) is not None and MEMO.get(r["ticket"])["type"] == "ticket"   # the runner wrote the decision's ticket
    assert STR.live_issues(now=core.now_utc() + dt.timedelta(hours=27))[0] == [] or all("only text" not in p for p in STR.live_issues(now=core.now_utc() + dt.timedelta(hours=27))[0])

def test_undo_before_the_change_rejects_the_ticket_and_freezes_the_key(monkeypatch, setting):
    from whatifs.org import memos as MEMO
    ceo(setting); at(monkeypatch, JAN); c, _ = STR.next_move(JAN); row, memo = STR.decide(c, JAN); MEMO.write(memo); STR.tell(JAN)
    a = next(a for a in core.store().rows("Owner_Actions") if a.get("kind") == "strategy")
    out = NTF.answer(a["id"], f"STRATEGY UNDO {row['id']}"); r = decisions()[0]
    assert out == "undone: it had not been changed yet" and r["state"] == "undone" and MEMO.get(row["ticket"])["status"] == "rejected"
    assert core.S("STANDARD_MAX_LONG_PER_MONTH") == "4" and STR.next_move(JAN + dt.timedelta(days=1))[0] is None            # the review the day after decides nothing on that key
    assert NTF.answer(a["id"], f"STRATEGY UNDO {row['id']}").endswith("already ANSWERED")

def test_undo_of_the_oldest_decision_takes_the_whole_stack_back_one_ticket_at_a_time(monkeypatch, setting):
    from whatifs.org import memos as MEMO, runner as RN
    ceo(setting); setting("FORMAT_SHARE_F1", "60"); monkeypatch.setattr(STR, "PORTFOLIO", ("FORMAT_SHARE_F1",))
    monkeypatch.setattr(STR, "rule_of", lambda key: {"id": "T", "metric": "shorts_engaged_90d", "board": "shorts", "direction": "up", "horizon": 4})
    monkeypatch.setattr(STR, "effect", lambda key, value, now=None: str(value))
    def engine(t):                                                                                      # one pass of the engine, a complete run of D1 (the lever's owner), Strategy's settle
        EX.engine_tick(now=t); RN.run("D1", "review", lambda b: (b.take(), RN.Out({"ok": 1}, measures={"engine_passes": 1}))[1]); EX.reconcile(now=core.now_utc()); STR.settle(core.now_utc())
    base = core.now_utc() - dt.timedelta(days=5); ids = []
    for d, tgt in ((0, "40"), (2, "20")):                                                               # the clock is real: a run proves a change only when it started after it
        t = base + dt.timedelta(days=d); monkeypatch.setattr(STR, "targets", lambda now=None, tgt=tgt: {"FORMAT_SHARE_F1": {"target": tgt, "why": "w", "numbers": {}, "evidence": "ok", "count": "", "rule": "T"}})
        c, _ = STR.next_move(t); row, memo = STR.decide(c, t); MEMO.write(memo); STR.tell(t); ids.append(row["id"]); engine(t)
    assert core.S("FORMAT_SHARE_F1") == "20" and [r["state"] for r in decisions()] == ["verified", "verified"]
    first = next(a for a in core.store().rows("Owner_Actions") if a.get("kind") == "strategy" and ids[0] in a["buttons"])
    out = NTF.answer(first["id"], f"STRATEGY UNDO {ids[0]}"); assert ids[1] in out and [r["state"] for r in decisions()] == ["undone", "undone"]
    for _i in range(6): engine(core.now_utc())                                                          # the engine's passes; settle sends the next undo ticket only when the first is done
    assert core.S("FORMAT_SHARE_F1") == "60"                                                            # the cell ends where he tapped

def test_strategy_live_is_na_on_an_empty_sheet_fails_when_stale_and_passes_after_a_review(monkeypatch, setting):
    from whatifs.org import runner as RN
    assert CON.p_strategy_live({})[0] == CON.NA                                                         # STRATEGY_ON FALSE
    setting("STRATEGY_ON", "TRUE"); s, ev = CON.p_strategy_live({}); assert s == CON.NA and ev.startswith("Strategy has not reviewed yet")   # nothing run before it
    setting("ORG_SINCE", core.iso(now() - dt.timedelta(hours=40))); s, ev = CON.p_strategy_live({}); assert s == CON.FAIL and "Strategy's review is missing" in ev
    RN.run("D1", "review", STR.review); s, ev = CON.p_strategy_live({}); assert s == CON.PASS and ev.startswith("Strategy reviewed 0 h ago; ")
    assert "strategy_live" in RND_ORG_CHECKS() and REG.CHECK_OWNER["strategy_live"] == "D1" and [f for f in CON.FEATURES if f[0] == "strategy_live"][0][1] == "script"
def RND_ORG_CHECKS():
    from whatifs.org import rnd as RND; return RND.ORG_CHECKS

def test_every_inbound_memo_of_a_review_is_dispositioned(setting):
    from whatifs.org import memos as MEMO, runner as RN
    setting("STRATEGY_ON", "TRUE")
    for m in ({"type": "problem_memo", "from_dept": "D12", "to_depts": ["D1"], "subject": "A stuck lever", "body": {"what_failed": "a lever did not move", "where": "Tickets:x", "attempt": 1},
               "evidence": [{"source": "Tickets:x", "date": "2026-11-16", "type": "own data"}], "dedupe_key": "p1", "done_when": "the lever moves on its next run"},):
        MEMO.write(m)
    RN.run("D1", "review", STR.review)
    s = [x for x in core.store().rows("Sessions") if x.get("dept") == "D1" and x.get("trigger") == "review"][-1]; assert s["status"] == "ok", s

def test_what_stays_his_is_a_list_no_lever_moves_without_his_tap_and_d1_is_wired():
    for k in STR.OWNER_ONLY: assert k in core.DEFAULTS and (LV.owner_of(k) == "" or LV.LEVERS[k]["owner"] == "always"), k
    assert LV.LEVERS["STANDARD_MAX_LONG_PER_MONTH"]["lo"] == 4 and LV.LEVERS["STANDARD_MAX_LONG_PER_MONTH"]["hi"] == 8 and LV.LEVERS["STANDARD_MAX_LONG_PER_MONTH"]["owner"] == ""
    assert ("whatifs/cli.py", "review") in REG.ENTRY["D1"] and REG.PENDING == {"D0": "B9", "C": "B6", "L": "B8"} and REG.DEPTS["D1"]["cadence"] == "daily"
    assert "whatifs/org/strategy.py" in REG.DEPTS["D1"]["wraps"] and REG.entry_issues() == [] and LV.issues() == [] and NTF.INFORM_KINDS == ("strategy", "desk")
    assert "def link(" in open(os.path.join(ROOT, "whatifs", "notify.py"), encoding="utf-8").read() and "def _link(" not in open(os.path.join(ROOT, "whatifs", "notify.py"), encoding="utf-8").read()
