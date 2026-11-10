"""v10 growth: G4 Hours Engine (localizations) and G7 affiliate block. No keys, no network."""
import json, os
import pytest
from whatifs import core, hours as HR, episode as EP

def test_translate_returns_every_language_with_limits():
    loc = HR.translate("Your Phone Weighs 400 Kilos", "What happens next.\\n\\nChapters\\n0:00 Start")
    assert set(loc) == {"es", "pt", "hi", "de", "fr", "id"} and all(len(v["title"]) <= 100 for v in loc.values())

def test_tick_localizes_one_video_once(setting):
    st = core.store()
    st.append("Episodes", [{"episode_id": "E1", "yt_id": "v1", "slot_et": "2026-11-10T15:00:00Z", "status": "SCHEDULED", "title": "A"},
                           {"episode_id": "E2", "yt_id": "v2", "slot_et": "2026-11-14T15:00:00Z", "status": "SCHEDULED", "title": "B"}])
    assert HR.tick() is True and [r["yt_id"] for r in st.rows("Localizations")] == ["v2"]          # newest first, one per tick
    assert HR.tick() is True and HR.tick() is None                                                 # then v1, then nothing left
    setting("LOCALIZATIONS_ON", "FALSE"); st.append("Episodes", [{"episode_id": "E3", "yt_id": "v3", "slot_et": "2026-11-17T15:00:00Z", "status": "SCHEDULED"}])
    assert HR.tick() is None

def test_bad_translation_never_breaks(monkeypatch):
    import whatifs.models as M
    monkeypatch.setattr(M, "ask", lambda *a, **k: "not json")
    assert HR.translate("t", "d") == {}

def test_affiliate_block_off_by_default_then_one_matched_link_with_disclosure(setting):
    assert HR.affiliate_block("falling into neptune") == ""
    setting("AFFILIATE_ON", "TRUE"); assert HR.affiliate_block("x") == ""                         # no links yet
    setting("AFFILIATE_LINKS", json.dumps([{"name": "Course A", "url": "https://a.example/x", "topics": ["planet", "neptune", "space"], "line": "Learn planets"},
                                           {"name": "Course B", "url": "https://b.example/y", "topics": ["body", "bones"]},
                                           {"name": "Bad", "url": "http://insecure.example"}]))
    b = HR.affiliate_block("What if you fell into Neptune, the windy planet")
    assert b.startswith("Learn planets: https://a.example/x") and core.S("AFFILIATE_DISCLOSURE") in b
    assert "insecure" not in HR.affiliate_block("anything")

def test_description_carries_the_block_only_when_on(setting):
    room = {"spine": {"premise": "What if you fell into Neptune"}}
    assert "Affiliate link" not in EP._description("Hook line.", [], room, "EP1")
    setting("AFFILIATE_ON", "TRUE"); setting("AFFILIATE_LINKS", json.dumps([{"name": "C", "url": "https://c.example", "topics": ["neptune"]}]))
    d = EP._description("Hook line.", [], room, "EP1")
    assert "https://c.example" in d and "Affiliate link" in d and d.rstrip().endswith("Science is simplified for storytelling.")

# ---------------- Engagement Engine + Emotion Beats (K133)
from whatifs import engage as EG, room as RM

def _script(lines): return "\n".join(lines)

def test_brief_has_the_library_the_rule_and_one_emotion(setting):
    b = EG.brief("EP20261114")
    assert "Never promise anything for a like" in b and "EMOTION BEAT" in b and any(e.upper() in b for e, _ in EG.EMOTIONS)
    assert "AUDIENCE PROMPTS" in RM._writer_extra("EP20261114")
    setting("ENGAGE_RULES_ON", "FALSE"); setting("EMOTION_BEAT_ON", "FALSE"); assert EG.brief("x") == ""

def test_emotion_choice_is_stable_weighted_and_never_repeats_a_non_awe_type(setting):
    picks = [EG.pick_emotion(f"EP{i}") for i in range(200)]
    assert picks.count("awe") > 60 and EG.pick_emotion("EP7") == EG.pick_emotion("EP7")
    for i in range(50):
        e = EG.pick_emotion(f"EP{i}")
        if e != "awe":
            setting("EMOTION_LAST", e); assert EG.pick_emotion(f"EP{i}") == "awe"; break

def test_enforce_removes_early_extra_and_crowded_asks_but_keeps_jury():
    body = [f"[VALE] [none] Line number {i} about the planet." for i in range(40)]
    body[1] = "[GRIMM] [none] Hit like if you think gravity is lying."              # too early
    body[12] = "[JURY] [VALE] [none] Guilty or innocent? Say it now."
    body[14] = "[NANA] [none] Subscribe, jury duty is twice a week."                # within 6 lines of the jury prompt
    body[25] = "[VALE] [none] Smash that like button for the jury."
    body[33] = "[NANA] [none] Share this with the friend who'd panic first."
    body[38] = "[GRIMM] [none] Subscribe or I win."                                   # 5 lines after the share: too close
    new, n = EG.enforce(_script(body), "EP")
    assert n == 3 and "[JURY]" in new and "Smash that like" in new and "Share this" in new
    assert "Hit like" not in new and "jury duty is twice" not in new and "Subscribe or I win" not in new
    assert EG.enforce("", "EP") == ("", 0)

# ---------------- Specials (K134): cast intro + twice-monthly special reels
from whatifs import specials as SP, governor as G, manage as MG, publish as PUB
import datetime as dt

def test_cast_intro_is_made_in_fake_mode_within_its_caps(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    r = SP.run(kind="cast_intro", force=True, publish=False)
    assert r["ok"] and os.path.exists(r["path"]) and r["kind"] == "cast_intro"
    import subprocess
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", r["path"]], capture_output=True, text=True).stdout)
    assert 17.0 <= dur <= 30.0                                                          # v10.2: cover + 4 voiced beats + 2.5 s end card
    assert core.store().rows("Specials")[-1]["title"].startswith("Meet the court")

def test_special_concept_falls_back_safely_and_respects_the_money(setting, monkeypatch):
    c = SP.concept("special"); assert 3 <= len(c["beats"]) <= 4 and all(b["who"] in ("VALE", "GRIMM", "ROSA", "SET") for b in c["beats"])
    import whatifs.models as M
    monkeypatch.setattr(M, "ask", lambda *a, **k: {"beats": [{"who": "OGGY"}]})            # a third-party character is refused -> safe fallback
    assert SP.concept("special")["title"].startswith("Meet the court")
    setting("SPECIAL_REEL_CAP_INR", "10"); ok, why = SP.allowed(4); assert not ok and "per-reel cap" in why
    setting("SPECIAL_REEL_CAP_INR", "180")                     # v10.2 default (Kling 3.0)
    core.store().append("Cost_Log", [{"ts": core.iso(), "episode_id": "SP202611020000", "item": "hero_clip", "provider": "fal", "inr": "290"}])
    ok, why = SP.allowed(4); assert not ok and "specials money" in why
    assert SP.run(kind="special", publish=False)["ok"] is False

def test_specials_days_and_off_switch(setting):
    assert SP.due(dt.datetime(2027, 7, 16, 15, 0, tzinfo=dt.timezone.utc)) and not SP.due(dt.datetime(2027, 7, 17, 15, 0, tzinfo=dt.timezone.utc))      # July: no occasion, the regular days
    setting("SPECIALS_ON", "FALSE"); assert SP.run(kind="special", publish=False)["ok"] is False

def test_cap_is_5000_with_both_earmarks_out_of_production(setting):
    assert core.DEFAULTS["BUDGET_CEILING_INR"][0] == "5000" and G.cap_inr() == 5000
    assert G.production_room_inr() == pytest.approx(5000 - core.S("BUDGET_MAINT_RESERVE_INR", float) - 200 - 300)
    st = core.store(); st.append("Settings", [{"key": "BUDGET_FLOOR_INR", "value": "4700", "note": ""}, {"key": "BUDGET_CEILING_INR", "value": "6000", "note": ""}])
    core._settings_cache = None
    assert MG.v10_upgrade(st) == ["BUDGET_FLOOR_INR"] and MG.v10_upgrade(st) == []

def test_special_workflow():
    import yaml
    wf = yaml.safe_load(open(".github/workflows/special.yml")); job = wf["jobs"]["special"]
    assert job["concurrency"]["group"] == "special" and any("--if-due" in str(s.get("run", "")) for s in job["steps"])

# ---------------- Character Love Engine (formats, canon, asks, learning)
def _special_rows(rows):
    core.store().append("Specials", rows)

def test_formats_are_weighted_learned_and_lore_is_rationed(setting):
    picks = [SP.pick_format(seed=i) for i in range(300)]
    assert set(picks) <= set(SP.FORMATS) and picks.count("lab_log") > picks.count("backstory")
    _special_rows([{"ts": core.iso(), "id": "SP1", "format": "backstory", "title": "t"}])
    assert "backstory" not in {SP.pick_format(seed=i) for i in range(200)}                       # one lore drop per 42 days
    old = (core.now_utc() - dt.timedelta(days=50)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().update("Specials", "id", "SP1", {"ts": old})
    _special_rows([{"ts": old, "id": f"SPv{i}", "format": f, "views_7d": v} for i, (f, v) in enumerate([("deduction", 9000), ("lab_log", 300), ("tea_ruling", 400), ("rivalry", 350)])])
    picks = [SP.pick_format(seed=i) for i in range(400)]
    assert picks.count("deduction") > picks.count("rivalry")                                      # the format that worked gets more turns

def test_backstory_uses_a_canon_fact_and_the_right_ask(monkeypatch):
    seen = []
    import whatifs.models as M
    monkeypatch.setattr(M, "ask", lambda role, s, p, **k: seen.append(p) or {"title": "The teacup", "beats": [{"who": w, "sec": 3, "motion": "m", "card": "C", "line": "l"} for w in ("ROSA", "VALE", "GRIMM", "SET")]})
    c = SP.concept("special", fmt="backstory")
    assert "chipped teacup" in seen[-1] and c["format"] == "backstory" and c["ask"] == SP.ASKS["nana"]
    assert SP.concept("special", fmt="lab_log")["ask"] == SP.ASKS["beaker"]

def test_festive_cast_intro(setting):
    setting("CAST_INTRO_FESTIVE", "Diwali")
    c = SP.concept("cast_intro"); assert "Happy Diwali from the court" in c["beats"][-1]["line"] and c["beats"][-1]["world"] == "case"      # v10.2: voiced, set-driven
    setting("CAST_INTRO_FESTIVE", ""); assert "reality goes on trial" in SP.concept("cast_intro")["beats"][-1]["line"]

def test_record_views_after_7_days(monkeypatch):
    old = (core.now_utc() - dt.timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _special_rows([{"ts": old, "id": "SPx", "format": "lab_log", "yt_id": "y1", "views_7d": ""}, {"ts": core.iso(), "id": "SPy", "format": "vote", "yt_id": "y2", "views_7d": ""}])
    monkeypatch.setattr(PUB, "yt_engaged_views", lambda vid, since: 1234)
    assert SP.record_views() == 1 and next(r for r in core.store().rows("Specials") if r["id"] == "SPx")["views_7d"] in (1234, "1234")

# ---------------- Shorts Lab (K135): kinetic captions, winners-only link card, breakouts, weekly cap
from whatifs import reels as RLS, shortslab as SL, notify as NT2

def test_kinetic_captions_light_one_word_at_a_time_inside_the_safe_zone(tmp_path, setting):
    tl = {"units": [{"text": "You have 90 seconds left", "start": 0.0, "end": 2.0,
                     "words": [{"w": "You", "s": 0.0, "e": 0.3}, {"w": "have", "s": 0.3, "e": 0.6}, {"w": "90", "s": 0.6, "e": 1.0}, {"w": "seconds", "s": 1.0, "e": 1.5}, {"w": "left", "s": 1.5, "e": 2.0}]}]}
    p = RLS._ass(tl, str(tmp_path / "a.ass"), "Hook", 1080, 1920); t = open(p).read()
    caps = [l for l in t.splitlines() if l.startswith("Dialogue: 0,")]
    assert len(caps) == 5 and "{\\c&H0000D7FF&\\fscx112\\fscy112}YOU{\\r}" in caps[0] and "{\\c&H0000D7FF&\\fscx112\\fscy112}90{\\r}" in caps[2]
    style = next(l for l in t.splitlines() if l.startswith("Style: Cap"))
    assert style.split(",")[-2] == str(int(1920 * 0.38))                                          # >= 36% up from the bottom
    hook = next(l for l in t.splitlines() if l.startswith("Style: Hook")); assert hook.split(",")[18] == "8"   # hook text in the top area
    setting("KINETIC_CAPTIONS_ON", "FALSE")
    t2 = open(RLS._ass(tl, str(tmp_path / "b.ass"), "Hook", 1080, 1920)).read()
    assert len([l for l in t2.splitlines() if l.startswith("Dialogue: 0,")]) == 2

def _eps_with_reels(n, hours_ago):
    t = (core.now_utc() - dt.timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    core.store().append("Episodes", [{"episode_id": f"E{i}", "slot_et": t, "status": "LIVE", "yt_id": f"L{i}", "reel1_yt": f"s{i}a", "reel2_yt": f"s{i}b"} for i in range(n)])

def test_link_pack_lists_only_winners_once_a_week(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    _eps_with_reels(3, 30)
    views = {"s0a": 50, "s0b": 900, "s1a": 60, "s1b": 70, "s2a": 2000, "s2b": 40}
    ids = SL.link_pack(views=views)
    assert ids == ["s2a", "s0b", "s1b"] and SL.link_pack(views=views) == ids                      # above the median (65), best first
    cards = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "linkpack"]; assert len(cards) == 1 and cards[0]["tier"] == "week" and "studio.youtube.com/video/s2a/edit" in cards[0]["text"]

def test_breakout_card_once_per_short(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT2, "in_quiet_hours", lambda now=None: False)
    _eps_with_reels(2, 10)
    v = {"s0a": 100, "s0b": 120, "s1a": 5000, "s1b": 110}
    assert SL.breakouts(views=v) == ["s1a"] and SL.breakouts(views=v) == ["s1a"]
    assert len([r for r in core.store().rows("Owner_Actions") if r["kind"] == "breakout"]) == 1

def test_weekly_cap_blocks_specials(setting):
    _eps_with_reels(7, 20); setting("SHORTS_WEEKLY_CAP", "14")
    assert SL.weekly_count() == 14 and not SL.allowed_today()
    r = SP.run(kind="special", publish=False); assert r["ok"] is False and "ceiling" in r["why"]

# ---------------- Occasions (K136): the calendar-aware Character Love Engine
from whatifs import occasions as OC

def test_dates_fixed_computed_and_lunar():
    d26, d27 = OC.dates_for_year(2026), OC.dates_for_year(2027)
    assert d26["halloween"] == dt.date(2026, 10, 31) and d26["thanksgiving"] == dt.date(2026, 11, 26) and d26["diwali"] == dt.date(2026, 11, 8)
    assert d27["easter"] == dt.date(2027, 3, 28) and d27["mothers_day"] == dt.date(2027, 5, 9) and d27["holi"] == dt.date(2027, 3, 22)
    assert "diwali" not in OC.dates_for_year(2029)                                          # unknown lunar years are skipped, never guessed

def test_occasions_take_the_month_slots_first():
    assert OC.plan_month(2027, 10) == [(dt.date(2027, 10, 29), "diwali"), (dt.date(2027, 10, 31), "halloween")]
    assert OC.plan_month(2026, 11) == [(dt.date(2026, 11, 8), "diwali"), (dt.date(2026, 11, 26), "thanksgiving")]
    assert OC.plan_month(2027, 7) == [(dt.date(2027, 7, 2), ""), (dt.date(2027, 7, 16), "")]   # no occasion: the regular days
    assert OC.slot_for(dt.date(2027, 10, 31)) == "halloween" and OC.slot_for(dt.date(2027, 10, 30)) is None

def test_halloween_special_uses_the_occasion_brief_and_the_family_ask(monkeypatch):
    seen = []
    import whatifs.models as M
    monkeypatch.setattr(M, "ask", lambda role, s, p, **k: seen.append(p) or {"title": "Trick or treat", "beats": [{"who": w, "sec": 3, "motion": "m", "card": "C", "line": "l"} for w in ("ROSA", "VALE", "GRIMM", "SET")]})
    c = SP.concept("special", occasion="halloween")
    assert "trick-or-treating" in seen[-1] and c["format"] == "occasion:halloween" and c["ask"] == OC.FAMILY_ASK

def test_heads_up_three_days_before_once(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    now = dt.datetime(2027, 10, 28, 9, 0, tzinfo=dt.timezone.utc)
    a = OC.heads_up(now); assert a and OC.heads_up(now) == a
    row = next(r for r in core.store().rows("Owner_Actions") if r["id"] == a); assert "Halloween" in row["text"] and row["tier"] == "week"
    assert OC.heads_up(dt.datetime(2027, 7, 10, 9, 0, tzinfo=dt.timezone.utc)) is None

def test_topical_hook_skips_tragedies():
    core.store().append("Trend_Brief", [{"week": "w", "kind": "news", "item": "Plane crash kills 40", "detail": "disaster"},
                                        {"week": "w", "kind": "news", "item": "Total lunar eclipse this Friday", "detail": "moon turns red"}])
    assert OC.topical_hook() == "Total lunar eclipse this Friday"

def test_lunar_dates_refresh_in_december_only(setting):
    setting("OCCASION_DATES", "{}")
    assert not OC.refresh_lunar_dates(dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc))
    assert OC.refresh_lunar_dates(dt.datetime(2026, 12, 3, tzinfo=dt.timezone.utc))
    assert OC.dates_for_year(2027)["diwali"] == dt.date(2027, 10, 29)

# ---------------- Slop Guard (K137), Retention Microscope (K138), face check (K139)
from whatifs import slop as SLOPM, microscope as MS, room as RM2

def _units(n, rate=2.5):
    out = []
    for i in range(n):
        out.append({"text": f"Line {i} about the sky falling on you", "start": i * 4.0, "end": i * 4.0 + 4.0, "words": [{"w": "x", "s": 0, "e": 0}] * int(rate * 4 + (i % 3))})
    return out

def test_slop_score_parts_and_card(monkeypatch, setting):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    shots = [{"type": "still"}] * 20
    r = SLOPM.record(_units(20), shots, "EPa"); assert r["still"] == 1.0 and r["still_share"] == 1.0 and r["slop"] >= 35
    r2 = SLOPM.record(_units(20), shots, "EPb"); assert r2["template_sim"] == 1.0 and r2["opening_repeat"] == 1.0 and r2["slop"] > core.S("SLOP_WARN", int)
    assert any(x["kind"] == "slop" and x["tier"] == "fyi" for x in core.store().rows("Owner_Actions"))
    mixed = [{"type": t} for t in ("kling", "living", "still", "graphic") * 5]
    assert SLOPM.score(_units(20), mixed)["still_share"] == 0.0
    setting("SLOP_GUARD_ON", "FALSE"); assert SLOPM.record(_units(5), shots, "EPc") == {}

def _retention(rows):
    core.store().append("Retention_Map", rows)

def test_microscope_needs_enough_videos_views_and_effect(setting):
    _retention([{"episode_id": f"E{i}", "shot_types": "graphic", "vs_median": "0.12", "views": "3000"} for i in range(5)])
    assert MS.learn() == []                                                              # 5 videos: not yet
    _retention([{"episode_id": "E5", "shot_types": "graphic", "vs_median": "0.10", "views": "3000"},
                {"episode_id": "E6", "shot_types": "kling", "vs_median": "-0.2", "views": "500"}])  # too few views: ignored
    assert MS.learn() == ["killer:graphic"]
    assert "faster than usual during graphic shots" in MS.brief() and "DATA RULES" in RM2._writer_extra("EPx")
    setting("MICRO_RULES_ON", "FALSE"); assert MS.brief() == ""

def test_microscope_rules_expire(setting):
    _retention([{"episode_id": f"E{i}", "shot_types": "living", "vs_median": "-0.08", "views": "5000"} for i in range(6)])
    MS.learn(); assert MS.active_rules()
    core.store().append("Episodes", [{"episode_id": f"N{i}", "yt_id": f"y{i}"} for i in range(25)])
    assert MS.active_rules() == []                                                       # 20 videos later, not re-confirmed

def test_dashboard_lab_shows_rules(setting):
    from whatifs import dash as DSH
    _retention([{"episode_id": f"E{i}", "shot_types": "living", "vs_median": "-0.08", "views": "5000"} for i in range(6)]); MS.learn()
    lab = DSH.build_snapshot()["lab"]; assert lab["boosters"] and lab["boosters"][0]["videos"] == 6

def test_face_drift_falls_back_to_the_portrait(monkeypatch, tmp_path):
    import whatifs.models as M
    monkeypatch.setattr(M, "ask_vision", lambda *a, **k: {"same_person": False})
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True)
    r = SP.run(kind="cast_intro", force=True, publish=False)
    assert r["ok"] and os.path.exists(r["path"])
    assert any(f.endswith("_portrait.mp4") for f in os.listdir(os.path.dirname(r["path"])))
