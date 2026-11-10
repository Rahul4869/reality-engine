"""v8.1 hardening: tolerant speaker parser, code-checked format, label-preserving rewrites, budget gate, maintenance reserve, Gemini cost log, speaker tag."""
import os, json
import numpy as np
from whatifs import core, format_engine as FE, governor as G
from whatifs.voice import parse_script

def _legacy_budget(setting):
    setting("BUDGET_FLOOR_INR", "4000"); setting("BUDGET_CEILING_INR", "4000"); setting("BUDGET_EARMARK_INR", "0"); setting("V94A_FLIPS_ON", "FALSE"); setting("V10_FLIPS_ON", "FALSE"); setting("SPECIALS_ON", "FALSE")      # v9.4a: this test keeps the v8 budget profile (₹4,000, no earmark, no cap move)


GOOD = "\n".join(["## BEAT 1"] + [f"[{'DIRECTOR' if i % 2 == 0 else 'SKEPTIC'}] [calm] Line number {i} says something new." for i in range(10)])

# ---------------- parser ----------------
def test_label_in_either_order_and_other_styles_is_never_spoken():
    cases = ["[DIRECTOR] [calm] Rule one.", "[calm] [DIRECTOR] Rule one.", "DIRECTOR: Rule one.", "**[DIRECTOR]** Rule one.", "[Director][calm] Rule one."]
    for c in cases:
        us = parse_script(c)
        assert [(u.speaker, u.text) for u in us] == [("DIRECTOR", "Rule one.")], (c, us)

def test_delivery_tag_survives_when_it_comes_before_the_label():
    us = parse_script("[tension] [SKEPTIC] Wait. That assumes the air stays put.")
    assert [u.speaker for u in us] == ["SKEPTIC", "SKEPTIC"] and all(u.tag == "tension" for u in us)

def test_two_speakers_on_one_line_become_two_units_with_a_turn_gap():
    us = parse_script("[DIRECTOR] It starts. [SKEPTIC] Does it? [DIRECTOR] Yes.")
    assert [u.speaker for u in us] == ["DIRECTOR", "SKEPTIC", "DIRECTOR"] and us[1].gap_before > 0

def test_pause_and_text_on_one_line_keeps_the_text_and_unknown_brackets_are_not_spoken():
    us = parse_script("[DIRECTOR] [pause:long] [reveal] And then it stops.\n[DIRECTOR] [Note] hello there")
    assert us[0].text == "And then it stops." and us[0].gap_before >= 1.6 and us[1].text == "hello there"

def test_unlabelled_lines_stay_with_the_narrator():
    us = parse_script("[calm] The hook.\n[SKEPTIC] A question?")
    assert [u.speaker for u in us] == ["NARRATOR", "SKEPTIC"]

# ---------------- format engine ----------------
def test_check_script_accepts_dialogue_and_rejects_a_monologue_or_one_sided_script():
    assert FE.check_script(GOOD)["ok"]
    mono = "\n".join(["## BEAT 1"] + [f"[calm] Narration line {i}." for i in range(10)])
    assert not FE.check_script(mono)["ok"]
    one = "\n".join(["## BEAT 1"] + [f"[DIRECTOR] [calm] Line {i}." for i in range(10)])
    assert not FE.check_script(one)["ok"]

def test_labels_preserved_blocks_a_rewrite_that_drops_the_labels():
    stripped = "\n".join(l.split("] ", 1)[-1] if l.startswith("[") else l for l in GOOD.splitlines())
    assert FE.labels_preserved(GOOD, GOOD) and not FE.labels_preserved(GOOD, stripped)

def test_inject_puts_the_format_before_the_json_reply_line():
    out = FE.inject("ROLE: x.\nReturn JSON: {\"a\":1}", "writer")
    assert out.rindex("Return JSON") > out.index("DIRECTOR") and out.rstrip().endswith('{"a":1}')

def test_mode_follows_the_settings_cell_and_the_env_var_wins(monkeypatch, setting):
    monkeypatch.delenv("WHATIFS_PRESENTATION_FORMAT", raising=False)
    assert FE.mode() == "reality_engine"
    setting("PRESENTATION_FORMAT", "classic"); assert FE.mode() == "classic" and FE.check_script("[calm] a")["ok"]
    monkeypatch.setenv("WHATIFS_PRESENTATION_FORMAT", "reality_engine"); assert FE.mode() == "reality_engine"

def test_the_format_text_forbids_realistic_presenter_faces():
    assert "NEVER SHOWN AS REALISTIC FACES" in FE.instructions("writer").upper()

def test_speaker_blends_are_always_two_different_recipes(setting):
    from whatifs import episode as EP
    setting("DIRECTOR_VOICE", "C"); setting("SKEPTIC_VOICE", "C")
    sb = EP.speaker_blends(); assert sb["DIRECTOR"].parts != sb["SKEPTIC"].parts
    setting("PRESENTATION_FORMAT", "classic"); assert EP.speaker_blends() is None

# ---------------- room guards ----------------
def test_rewrite_steps_keep_the_original_when_labels_would_be_lost(monkeypatch):
    from whatifs import room
    stripped = "\n".join(l.split("] ", 1)[-1] if l.startswith("[") else l for l in GOOD.splitlines())
    monkeypatch.setattr(room, "ask", lambda *a, **k: {"script": stripped, "changes": "x"})
    out = room.humanize({"script": GOOD}, "E1"); assert out["script"] == GOOD
    assert room.extend({}, GOOD, 20, "E1") is None
    assert room._fix_length({"script": GOOD}, "brief", 5, 9, "E1")["script"] == GOOD

def test_format_pass_asks_once_and_keeps_the_fix_only_if_it_is_better(monkeypatch):
    from whatifs import room
    mono = "\n".join(["## BEAT 1"] + [f"[calm] Narration line {i} here." for i in range(10)])
    calls = []
    monkeypatch.setattr(room, "ask", lambda *a, **k: (calls.append(1) or {"script": GOOD.replace("Line number", "Narration line").replace(" says something new", " here")}))
    out = room.format_pass({"script": mono}, "brief", "E1")
    assert len(calls) == 1 and FE.check_script(out["script"])["ok"]
    monkeypatch.setattr(room, "ask", lambda *a, **k: {"script": mono})
    assert room.format_pass({"script": mono}, "brief", "E1")["script"] == mono          # no improvement -> original kept, never blocks

# ---------------- budget ----------------
def _spend(inr):
    core.cost("test_spend", "fal", 1, inr / core.S("USD_INR", float)); pass

def test_plan_holds_instead_of_overshooting_when_the_episode_does_not_fit(setting):
    _legacy_budget(setting)
    p = G.plan_for_episode(330.0, 8); assert not p["hold"] and p["kling"] >= 3
    _spend(3900)          # Rs 100 left of the 4,000 cap (v8.10: was 3,500)
    p = G.plan_for_episode(330.0, 1); assert p["hold"] and p["kling"] >= 3 and "hold" in p["reason"]

def test_a_new_episode_is_not_started_when_the_month_is_spent(setting):
    _legacy_budget(setting)
    ok, why = G.can_start_episode(); assert ok
    _spend(3800); ok, why = G.can_start_episode(); assert not ok and "Rs" in why

def test_maintenance_jobs_may_use_the_small_reserve_but_production_may_not(setting):
    _legacy_budget(setting)
    _spend(3920)          # v8.10 cap 4,000; v8.7: the reserve is INSIDE the cap: Rs 80 left, production (stops Rs 100 below the cap) is closed, maintenance is not
    assert G.monthly_cap_reached() and not G.monthly_cap_reached(maintenance=True)
    _spend(80); assert G.monthly_cap_reached(maintenance=True)       # the cap itself is never exceeded, not even by maintenance

def test_produce_slot_does_not_create_rows_or_start_when_the_budget_gate_closes(monkeypatch, setting):
    _legacy_budget(setting)
    from whatifs import manage as MG, publish as PUB
    sent = []; monkeypatch.setattr(PUB, "email", lambda *a, **k: sent.append(a[0]))
    _spend(3900); before = len(core.store().rows("Episodes"))
    assert MG._produce_slot(core.store().rows("Episodes")) is None and len(core.store().rows("Episodes")) == before
    assert MG._produce_slot(core.store().rows("Episodes")) is None and len(sent) == 1       # one email per month, not one per tick

def test_the_shipped_defaults_are_the_documented_budget_profile():
    assert core.DEFAULTS["BUDGET_FLOOR_INR"][0] == "5000" == core.DEFAULTS["BUDGET_CEILING_INR"][0] and core.S("KLING_MIN_CLIPS", int) == 4 and core.S("PUBLISH_DAYS") == "Tue,Sat"      # v8.10: the owner raised the cap to 4,000; v10.2: option C keeps 4 animated scenes

def test_gemini_calls_are_written_to_the_cost_log(monkeypatch):
    from whatifs import models
    class R:
        status_code = 200
        def json(self): return {"candidates": [{"content": {"parts": [{"text": "{}"}]}}], "usageMetadata": {"promptTokenCount": 100000, "candidatesTokenCount": 20000}}
    monkeypatch.setattr(models.requests, "post", lambda *a, **k: R())
    monkeypatch.setattr(models, "_models", {"gem_pro": "gemini-pro-test"})
    models._gemini("gem_pro", "s", "p", 100, 0.1, False, True); core.flush_costs()
    rows = [r for r in core.store().rows("Cost_Log") if r["item"] == "gemini_pro"]
    assert rows and float(rows[0]["inr"]) > 0

def test_claude_stays_in_the_fallback_chain_as_the_last_resort():
    import inspect, whatifs.models as M
    src = inspect.getsource(M.ask); assert 'x[0] == "g"] + [x for x in chain if x[0] == "c"]' in src

# ---------------- speaker tag ----------------
def test_speaker_tag_draws_only_while_a_role_speaks():
    from whatifs.overlay import SpeakerTag
    units = [{"start": 1.0, "end": 3.0, "speaker": "DIRECTOR"}, {"start": 4.0, "end": 5.0, "speaker": "NARRATOR"}]
    tag = SpeakerTag(units, 640, 360, 30)
    on = np.zeros((360, 640, 3), np.uint8); tag.apply(on, 60); assert on.any()
    off = np.zeros((360, 640, 3), np.uint8); tag.apply(off, 4.5 * 30); assert not off.any()
    assert not SpeakerTag([{"start": 0, "end": 1, "speaker": "NARRATOR"}], 640, 360, 30).active()
