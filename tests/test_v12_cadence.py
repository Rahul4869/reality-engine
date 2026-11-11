"""v12 B1b - the owner's cadence (10 Nov 2026: "4 a month"): 4 long videos a month, one a week. The gate stops a 5th, the live Sheet is moved once
(owner-typed values never touched), and nothing said to viewers or to a model states another cadence. Each rule is proven both ways."""
import re
import pytest
from whatifs import core, governor as G, manage as MG, cta as CTA, caretaker as CT, truth as TRU

def _episodes(n, status="LIVE"):
    mk = core.now_utc().strftime("%Y-%m")
    core.store().append("Episodes", [{"episode_id": f"EPCAD{i:02d}", "slot_et": f"{mk}-0{i + 1}T10:00", "status": status} for i in range(n)])

def test_defaults_are_four_a_month_one_a_week():
    assert core.DEFAULTS["STANDARD_MAX_LONG_PER_MONTH"][0] == "4" and core.DEFAULTS["PUBLISH_DAYS"][0] == "Sat" and core.DEFAULTS["VIDEOS_PER_MONTH_EST"][0] == "4"
    assert G.budget_mode() == "standard" and G.max_long_videos() == 4 and G.publish_days() == "Sat" and G.long_videos_per_week() == 1
    assert 1 <= G.episodes_left_this_month() <= 5                      # the money plan counts weekly slots, not eight

def test_the_gate_stops_the_fifth_long_video_and_not_the_fourth(setting):
    _episodes(3); ok, why = G.can_start_episode(); assert "at most" not in why, why          # 3 made: the count does not block the 4th
    _episodes(1); core.store().append("Episodes", [{"episode_id": "EPCAD98", "slot_et": core.now_utc().strftime("%Y-%m") + "-09T10:00", "status": "KILLED"}])
    assert G.long_videos_this_month() == 4                                                  # a killed episode is not counted
    ok, why = G.can_start_episode(); assert ok is False and "at most 4 long videos a month" in why
    setting("STANDARD_MAX_LONG_PER_MONTH", "8"); ok, why = G.can_start_episode(); assert "at most" not in why     # proves the gate reads the cell (fails the other way)

def test_one_time_sheet_move_flips_old_defaults_once(setting):
    for k, old, _ in MG.V12_FLIPS: setting(k, old)
    setting("V12_FLIPS_DONE", "")
    assert sorted(MG.v12_upgrade(core.store())) == sorted(k for k, _, _ in MG.V12_FLIPS)
    assert core.S("STANDARD_MAX_LONG_PER_MONTH") == "4" and core.S("PUBLISH_DAYS") == "Sat" and core.S("VIDEOS_PER_MONTH_EST") == "4"
    assert str(core.S("V12_FLIPS_DONE")).strip() and MG.v12_upgrade(core.store()) == []      # second run: nothing

def test_one_time_sheet_move_never_touches_an_owner_value(setting):
    setting("STANDARD_MAX_LONG_PER_MONTH", "6"); setting("PUBLISH_DAYS", "Wed,Sun"); setting("VIDEOS_PER_MONTH_EST", "7"); setting("V12_FLIPS_DONE", "")
    assert MG.v12_upgrade(core.store()) == []
    assert core.S("STANDARD_MAX_LONG_PER_MONTH") == "6" and core.S("PUBLISH_DAYS") == "Wed,Sun" and core.S("VIDEOS_PER_MONTH_EST") == "7"

def test_setup_runs_the_move():
    src = open(MG.__file__, encoding="utf-8").read(); assert src.count("try: v12_upgrade(st)") == 2      # both setup paths call it
    assert "V12_FLIPS_DONE" in core.DEFAULTS

def test_no_line_for_viewers_states_a_numeric_cadence():
    lines = [t[2] for pools in (CTA.POOLS, CTA.TRIAL_POOLS) for pool in pools.values() for entry in pool for t in entry]
    lines += list(CTA.DESC_SUB) + list(CTA.TRIAL_DESC_SUB) + list(CTA.DESC_SHARE) + list(CTA.TRIAL_DESC_SHARE)
    lines += [t[2] for asks in (CTA.REEL_ASKS, CTA.TRIAL_REEL_ASKS) for pool in asks.values() for t in pool]
    bad = [l for l in lines if re.search(r"\b(twice|thrice|\w+ times) a (week|month)\b|\bdaily\b|\bevery day\b", l, re.I)]
    assert len(lines) > 30 and not bad, bad
    assert sum("every week" in l.lower() for l in lines) >= 4                                       # true at any cadence of one a week or more

def test_the_retired_cadence_is_refused_everywhere():
    assert "old_long_cadence" in [r["id"] for r in TRU.RETIRED]
    assert [r["id"] for r in TRU.hits("Subscribe: a new impossible case twice a week.", "prompts")] == ["old_long_cadence"]
    assert [r["id"] for r in TRU.hits("Standard mode makes 8 long videos a month.", "docs")] == ["old_long_cadence"]
    assert TRU.hits("Subscribe: a new impossible case every week. At most 4 long videos a month.", "prompts") == []
    TRU.reset(); assert TRU.issues() == []

def test_the_policy_prompt_describes_the_channel_from_the_settings(setting, monkeypatch):
    assert CT.cadence_words() == "about 1 long video and 3 Shorts a week"                   # v12 V2c-b: the cadence is set in weeks
    setting("PUBLISH_DAYS", "Tue,Sat"); setting("SHORTS_PER_WEEK", "4"); assert CT.cadence_words() == "about 2 long videos and 4 Shorts a week"
    setting("SHORTS_TRACK_ON", "FALSE"); assert CT.cadence_words() == "about 2 long videos and 0 Shorts a week"
    setting("PUBLISH_DAYS", "Sat"); setting("SHORTS_TRACK_ON", "TRUE"); setting("SHORTS_PER_WEEK", "3")
    seen = {}
    import whatifs.models as M
    monkeypatch.setattr(M, "ask", lambda role, system, user, **k: seen.setdefault("system", system) and "A calm note.")
    from whatifs import notify as NT
    monkeypatch.setattr(NT, "send", lambda *a, **k: None)
    try: CT.policy_rescue([{"change": "x"}])
    except Exception: pass                                                                   # only the prompt matters here
    assert "about 1 long video and 3 Shorts a week" in seen.get("system", "") and "2 long videos" not in seen.get("system", "")
