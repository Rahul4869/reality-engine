"""v9.3: cold open (YOU before lore), micro-cuts + measured holds, advertiser safety, Shorts that keep the payoff, packaging truth (uploaded title,
variant A, rotation start / view floor), in-character asks, the hero-still Short schedule, the one-time default flips. No keys, no network."""
import datetime as dt, json, re
import pytest
from whatifs import core, growth as GR, packaging as PK, hooks as H, show as SHOW, cta as CTA, shotplan as SP, cutmap as CM, manage as MG, v91 as V91
from whatifs import room as ROOM, publish as PUB

NEW = ["COLD_OPEN_YOU_ON", "COLD_OPEN_LORE_FREE_SEC", "COLD_OPEN_YOU_MIN", "AD_SAFE_ON", "MICRO_CUTS_ON", "PIECE_MAX_SEC", "PIECE_MAX_SEC_OPENING", "PIECE_MIN_SEC",
       "CUTMAP_MAX_HOLD_SEC", "TRIAL_SHORTS_SAFE_ON", "HERO_SHORT_DELAY_MIN", "PKG_ROTATE_START_H", "PKG_ROTATE_MIN_VIEWS", "CTA_JURY_ON", "V93_FLIPS_ON", "V93_FLIPS_DONE"]

def test_every_v93_setting_has_a_default_and_a_note():
    for k in NEW: assert k in core.DEFAULTS and core.DEFAULTS[k][1].strip(), k
    assert core.DEFAULTS["HERO_STILL_REELS_ON"][0] == "TRUE" and core.DEFAULTS["HERO_STILL_SHORTS_ON"][0] == "FALSE"      # v10.1: static Shorts off (repetition risk)

# ------------------------------------------------------------------ K111 cold open
FILL = "[DIRECTOR] [calm] The light settles over the quiet street and nothing moves."
def _script(first, second="[DIRECTOR] [tension] You feel the floor tilt under your feet."):
    return "\n".join(["## BEAT 1", first, second] + [FILL] * 40)

def _cold(text): return [x for x in GR.retention_issues(text, {})["issues"] if x.startswith("cold open")]

def test_cold_open_flags_lore_before_twenty_seconds_and_missing_you():
    bad = _script("[JUDGE] Order. The court will hear the charge against gravity.", "[SKEPTIC] Objection! Preposterous.")
    iss = _cold(bad)
    assert any("lore" in x for x in iss) and any("'you/your' 0" in x for x in iss)
    assert not _cold(_script("[DIRECTOR] [tension] Your phone weighs four hundred kilos. You have nine seconds."))

def test_cold_open_long_first_line_and_advertiser_words():
    iss = " ".join(_cold(_script("[DIRECTOR] You wake up and you notice that the blood in your veins is moving the wrong way around your whole body today.")))
    assert "first line has" in iss and "limited ads" in iss

def test_cold_open_switch_restores_v92(setting):
    setting("COLD_OPEN_YOU_ON", "FALSE")
    assert not _cold(_script("[JUDGE] Order. The court will hear the charge against gravity."))

def test_writer_brief_carries_the_cold_open_contract(setting):
    plan, _ = SHOW.validate({"charge": "x", "exhibits": [], "verdict": {"winner": "vale"}}, {"premise": "p"}, [])
    b = SHOW.writer_brief(plan); assert "COLD OPEN (v9.3" in b and b.index("COLD OPEN (v9.3") < b.index("STRUCTURE:")
    setting("COLD_OPEN_YOU_ON", "FALSE"); assert "COLD OPEN (v9.3" not in SHOW.writer_brief(plan)

HOOK_SCRIPT = ("## BEAT 1\n[DIRECTOR] [calm] Every pillow on Earth is rising at noon, toward your bedroom ceiling.\n"
               "[SKEPTIC] The pillow keeps rising past the ceiling light.\n[DIRECTOR] Pillows rise at noon.")
CANDS = [{"line": "Your pillow is rising toward the bedroom ceiling.", "type": "you_stakes"},
         {"line": "Every pillow on Earth is rising at noon.", "type": "surprising_claim"},
         {"line": "Pillows soaked in blood rise at noon.", "type": "concrete_stakes"}]

def _hook_ask(you_total, other_total):
    def ask(role, system, prompt, **k):
        if role == "hooks": return {"candidates": CANDS}
        got = json.loads(prompt.split("CANDIDATES (JSON): ", 1)[1])
        out = []
        for c in got:
            v = you_total if c["line"].startswith("Your") else other_total
            out.append({"id": c["id"], "clarity": v, "relevance": v, "curiosity": v, "promise_accuracy": v, "unsupported_claim": False})
        return {"scores": out}
    return ask

def test_hooks_reject_advertiser_words_and_prefer_a_close_you_line(setting):
    rec = H.build_record(HOOK_SCRIPT, {"premise": "pillows rise"}, "EPH", _hook_ask(8.0, 9.0))
    ch = next(c for c in rec["candidates"] if c["id"] == rec["chosen_id"])
    assert ch["line"].startswith("Your") and any("ad_unsafe_word" in c["issues"] for c in rec["rejected"])
    rec2 = H.build_record(HOOK_SCRIPT, {"premise": "pillows rise"}, "EPH", _hook_ask(7.2, 9.5))      # more than 1.5 points behind: the best line wins
    assert next(c for c in rec2["candidates"] if c["id"] == rec2["chosen_id"])["line"].startswith("Every")
    setting("COLD_OPEN_YOU_ON", "FALSE")
    rec3 = H.build_record(HOOK_SCRIPT, {"premise": "pillows rise"}, "EPH", _hook_ask(8.0, 9.0))
    assert next(c for c in rec3["candidates"] if c["id"] == rec3["chosen_id"])["line"].startswith("Every")
    assert "you_stakes" in H.TYPES

# ------------------------------------------------------------------ K113 advertiser safety
def test_ad_risk_catches_described_harm_but_not_stakes(setting):
    assert PK.ad_risk("Your Blood Turns to Gore") and PK.ad_risk("a bloody corpse on the stairs")
    assert not PK.ad_risk("You Have 90 Seconds to Survive the Boiling Ocean") and not PK.ad_risk("A deadly drop in pressure")
    assert any("advertiser" in x for x in GR.title_issues("The Gore In Your Kitchen Sink Right Now"))
    assert PK.shock_score("Gore In Your Kitchen Sink Right Now") < PK.shock_score("Your Kitchen Sink Is Breathing Right Now")
    setting("AD_SAFE_ON", "FALSE"); assert PK.ad_risk("gore") == []

def test_an_unsafe_premise_can_never_pass_the_bar(monkeypatch):
    from whatifs import premise as PR
    from whatifs.data import PREMISE_CRITERIA
    monkeypatch.setattr(PR, "_judge", lambda role, pitches, recent, ep, fk: {f"p{i + 1}": {c: 9 for c in PREMISE_CRITERIA} for i in range(len(pitches))})
    ps = PR.score([{"premise": "What if every corpse in the city woke up?", "headline": "The City Of Corpses Wakes"},
                   {"premise": "What if your pillow floated at noon?", "headline": "Your Pillow Just Floated Away"}], [], "EPX")
    bar = core.S("PREMISE_MIN_SCORE", float)
    assert ps[0].get("ad_risk") and ps[0]["combined"] < bar and ps[1]["combined"] >= bar and not ps[1].get("ad_risk")

# ------------------------------------------------------------------ K115 packaging truth
def test_the_uploaded_title_is_the_cleanest_then_the_strongest():
    titles = ["What Would Happen If Light Moved at Walking Speed", "Your Reflection Is 1.4 Seconds Late. Is It Still You?"]
    assert GR.choose_titles(titles)[0].startswith("Your Reflection")

def test_variant_a_is_always_the_live_title_even_when_flawed():
    pkg = {"title": "Pillows", "thumb_text": "UP", "title_b": "Your Pillow Is Rising Toward The Ceiling Now", "thumb_text_b": "NOON",
           "titles": ["Your Bed Just Lost Its Pillow To The Sky Today"], "thumb_text_c": "LOOK UP"}
    vs = PK.variants(pkg, {}); assert vs[0]["key"] == "A" and vs[0]["title"] == "Pillows" and len(vs) >= 2

PKG = {"title": "What If Every Pillow Floated Away?", "thumb_text": "NOON", "title_b": "The Day Every Pillow Left Planet Earth", "thumb_text_b": "GONE",
       "titles": ["Your Pillows Just Broke The Law Of Gravity", "Why Your Pillow Is Rising Toward Space"], "thumb_text_c": "UP"}

def _rot(st, ep, hours_ago):
    st.append("Episodes", [{"episode_id": ep, "yt_id": "v" + ep[-2:], "slot_et": (core.now_utc() - dt.timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "LIVE"}])

def _mock(monkeypatch, views, calls):
    monkeypatch.setattr(PUB, "yt_set_title", lambda vid, t: calls.append(t)); monkeypatch.setattr(PUB, "yt_views", lambda vid: views["n"])
    monkeypatch.setattr(PUB, "email", lambda *a, **k: None)

def test_rotation_keeps_the_launch_window_and_skips_noise(monkeypatch, setting):
    setting("PKG_ROTATE_ON", "TRUE")          # v9.3.1: rotation is OFF by default (decision 5); this tests the switch-on path
    setting("TITLE_SHOCK_ON", "FALSE"); st = core.store(); calls = []; views = {"n": 100}; _mock(monkeypatch, views, calls)
    _rot(st, "EP20261102", 5); PK.record("EP20261102", "v02", PK.variants(PKG, {}), {})
    assert PK.rotate_tick() == 0 and not calls                                                 # inside the 24 h launch window: A stays, nothing measured
    st.update("Episodes", "episode_id", "EP20261102", {"slot_et": (core.now_utc() - dt.timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")})
    assert PK.rotate_tick() == 0 and any(r["status"] == "NO_TEST" for r in st.rows("Packaging_Tests"))      # 100 views < 1,500: no test, decided once
    views["n"] = 99999; assert PK.rotate_tick() == 0 and not calls

def test_rotation_runs_after_the_launch_window_with_enough_views(monkeypatch, setting):
    setting("PKG_ROTATE_ON", "TRUE")          # v9.3.1: rotation is OFF by default (decision 5); this tests the switch-on path
    setting("TITLE_SHOCK_ON", "FALSE"); st = core.store(); calls = []; views = {"n": 5000}; _mock(monkeypatch, views, calls)
    _rot(st, "EP20261103", 25); PK.record("EP20261103", "v03", PK.variants(PKG, {}), {})
    assert PK.rotate_tick() == 1 and any(r.get("window_start") for r in st.rows("Packaging_Tests") if r["episode_id"] == "EP20261103")

# ------------------------------------------------------------------ K112 micro-cuts + measured holds
def test_micro_cuts_split_stills_and_keep_graphics_and_reactions(setting):
    assert SP.pieces_for(6.0, "still") == 2 and SP.pieces_for(6.0, "still", opening=True) == 3
    assert SP.pieces_for(3.3, "still") == 1 and SP.pieces_for(20.0, "still") == 7 and SP.pieces_for(40.0, "still") == 13   # v11.1: cap 8 -> 24
    assert SP.pieces_for(10.0, "graphic") == 1 and SP.pieces_for(10.0, "reaction") == 1                                      # animated: one piece...
    assert SP.pieces_for(20.0, "graphic") == 2 and SP.pieces_for(20.0, "reaction") == 2                                      # ...up to 12 s (v11.1)
    setting("MICRO_CUTS_ON", "FALSE")
    assert [SP.pieces_for(d, "still") for d in (6.0, 10.0, 20.0)] == [1, 2, 3]                  # the v9.2 rule
    setting("MICRO_CUTS_ON", "TRUE"); setting("V91_SAFE_MODE", "TRUE"); assert SP.pieces_for(6.0, "still") == 1

def test_micro_cut_failure_falls_back_to_the_v92_rule(monkeypatch):
    V91._OFF.clear()
    def boom(*a, **k): raise RuntimeError("injected")
    monkeypatch.setattr(SP, "S", boom)
    assert SP.pieces_for(10.0, "still", episode="EPM") == 2 and not V91.on("MICRO_CUTS_ON", "EPM"); V91._OFF.clear()

def test_cut_map_measures_still_holds():
    tl = {"duration": 20.0, "units": [{"start": 0.0, "end": 9.5, "text": "a b c", "words": []}, {"start": 10.0, "end": 19.5, "text": "d e f", "words": []}]}
    m = CM.build_cutmap(None, tl, None, 30, (), "EPC", holds=[(0, 3), (3, 6), (6, 12.0), (12, 14)])
    assert [c["kind"] for c in m["cuts"]].count("static_hold") == 1 and m["pacing"]["median_hold_sec"] == 3.0 and m["pacing"]["over_limit"] == 1
    assert "Pacing (v9.3)" in CM.to_markdown(m) and "pacing" not in CM.build_cutmap(None, tl, None, 30, (), "EPC")

# ------------------------------------------------------------------ K114 Shorts keep the payoff
def test_trial_shorts_never_spend_the_payoff(setting):
    t = ROOM._reel_extra({}); assert "NEVER reveal the verdict" in t and "VERDICT reaction" not in t and "YOU" in t
    setting("TRIAL_SHORTS_SAFE_ON", "FALSE"); assert "VERDICT reaction" in ROOM._reel_extra({})

def test_hero_short_is_scheduled_after_the_long_video_and_linked(monkeypatch, tmp_path, setting):
    setting("HERO_STILL_SHORTS_ON", "TRUE")                                    # v10.1 default is off; the mechanism is still tested
    from whatifs import herostill as HS
    ups = []
    monkeypatch.setattr(HS, "pick_best", lambda paths, n=None: ("still.png", 9.0, 0))
    monkeypatch.setattr(HS, "build", lambda *a, **k: str(tmp_path / "h.mp4"))
    monkeypatch.setattr(PUB, "drive_upload", lambda *a, **k: ("id", ""))
    monkeypatch.setattr(PUB, "yt_upload", lambda *a, **k: ups.append((a, k)) or "SID")
    V91._OFF.clear()
    assert HS.make_for_episode("EPH", str(tmp_path), ["s"], "m.mp4", [], "HOOK") and not ups                      # no slot: never uploaded
    args = dict(slot_iso="2026-12-01T15:00:00Z", long_id="LONG1", title="Your Pillow Is Rising")
    HS.make_for_episode("EPH", str(tmp_path), ["s"], "m.mp4", [], "HOOK", **args); assert not ups                 # audit not approved: never uploaded
    setting("API_AUDIT_STATUS", "approved"); HS.make_for_episode("EPH", str(tmp_path), ["s"], "m.mp4", [], "HOOK", **args)
    (a, k), = ups
    assert k["publish_at"] == "2026-12-02T03:00:00Z" and "youtu.be/LONG1" in a[2] and a[1] == "HOOK" and k.get("short")      # v9.3.1: hook = title
    assert "#shorts" not in (a[1] + a[2]).lower()

# ------------------------------------------------------------------ K116 asks in character
def test_trial_asks_are_recognised_short_and_in_character():
    for kind, pool in CTA.TRIAL_POOLS.items():
        assert len(pool) >= 6
        for entry in pool:
            assert kind in {CTA.kind_of_text(t[2]) for t in entry}, (kind, entry)
            assert sum(len(t[2].split()) for t in entry) <= 34
            for spk, tag, text in entry:
                assert spk in ("DIRECTOR", "SKEPTIC", "JUDGE") and not re.search(r"\b(he|she|his|her|him|control room|simulation)\b", text, re.I), text
    for k, pool in CTA.TRIAL_REEL_ASKS.items():
        for spk, tag, text in pool: assert ("ollow" in text) if k == "follow" else CTA.kind_of_text(text) == "share"

def test_ensure_uses_jury_lines_in_the_trial_and_the_old_lines_when_off(setting):
    sc = "\n".join(["## BEAT 1"] + [f"[{'DIRECTOR' if i % 2 == 0 else 'SKEPTIC'}] [calm] Plain sentence number {i} about the case." for i in range(30)])
    trial = {t[2] for p in CTA.TRIAL_POOLS.values() for e in p for t in e}
    s, added, _ = CTA.ensure(sc, "EPJ", ""); assert sorted(added) == ["like", "share", "subscribe"] and any(t in s for t in trial)
    f = CTA.description_footer("EPJ", "https://x?sub_confirmation=1"); assert any(x in f for x in CTA.TRIAL_DESC_SUB) and len(f.splitlines()) == 3
    setting("CTA_JURY_ON", "FALSE"); s2, _, _ = CTA.ensure(sc, "EPJ", ""); assert not any(t in s2 for t in trial)

# ------------------------------------------------------------------ K117 one-time default flips
def test_v93_flips_only_old_defaults_and_only_once(setting):
    st = core.store(); st.append("Settings", [{"key": "HERO_STILL_REELS_ON", "value": "FALSE", "note": ""}, {"key": "HERO_STILL_SHORTS_ON", "value": "no", "note": ""}])
    core._settings_cache = None
    assert MG.v93_upgrade(st) == ["HERO_STILL_REELS_ON"] and core.S("HERO_STILL_REELS_ON", bool) and not core.S("HERO_STILL_SHORTS_ON", bool)
    setting("HERO_STILL_REELS_ON", "FALSE"); assert MG.v93_upgrade(st) == [] and not core.S("HERO_STILL_REELS_ON", bool)      # never twice

def test_v93_flips_can_be_switched_off(setting):
    setting("V93_FLIPS_ON", "FALSE"); st = core.store(); st.append("Settings", [{"key": "HERO_STILL_REELS_ON", "value": "FALSE", "note": ""}])
    core._settings_cache = None
    assert MG.v93_upgrade(st) == [] and not core.S("HERO_STILL_REELS_ON", bool)
