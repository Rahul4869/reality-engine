"""v9.1 stage A: safe mode, the per-feature fail-safe guard, Gemini voice substitution by descriptors, and the v9 baselines (golden frames, paid calls)."""
import json, os, tempfile
import pytest
from whatifs import core, v91 as V91, show as SHOW, manage as MG

def test_safe_mode_switches_every_v91_flag_off(setting):
    setting("VOICE_SUBSTITUTE_ON", "TRUE"); assert V91.on("VOICE_SUBSTITUTE_ON")
    setting("V91_SAFE_MODE", "TRUE"); assert not V91.on("VOICE_SUBSTITUTE_ON")

def test_guard_disables_only_that_feature_for_that_episode(setting, capsys):
    setting("VOICE_SUBSTITUTE_ON", "TRUE"); V91._OFF.clear()
    with V91.guard("VOICE_SUBSTITUTE_ON", "EPG"): raise RuntimeError("boom")
    assert not V91.on("VOICE_SUBSTITUTE_ON", "EPG") and V91.on("VOICE_SUBSTITUTE_ON", "EPOTHER") and "OFF for this episode" in capsys.readouterr().out
    assert V91.call("VOICE_SUBSTITUTE_ON", lambda: 1 / 0, default="d", episode="EPH") == "d" and not V91.on("VOICE_SUBSTITUTE_ON", "EPH")
    V91._OFF.clear()

def test_voice_substitution_picks_closest_before_kokoro():
    av = {"Kore", "Sulafat", "Algenib", "Puck"}
    assert V91.resolve_voice("JUDGE", "Gacrux", set(), av) == ("Sulafat", "substitute")          # female + warm, before Kokoro
    assert V91.resolve_voice("JUDGE", "Sulafat", set(), av) == ("Sulafat", "wanted")
    assert V91.resolve_voice("WITNESS", "Enceladus", {"Algenib"}, av)[0] == "Puck"              # male, the gravelly one is taken by a lead
    assert V91.resolve_voice("WITNESS", "Enceladus", set(), {"Kore"}) == ("", "kokoro")          # no male voice available: Kokoro
    assert V91.resolve_voice("JUDGE", "Gacrux", set(), set()) == ("", "kokoro")

def test_extra_blends_use_voice_check(setting):
    MG.setup(); core.store().append("Voice_Check", [{"voice": v, "synth_ok": "TRUE"} for v in ("Sulafat", "Algenib", "Charon", "Kore")])
    b = SHOW.extra_blends({"Charon", "Kore"})
    assert b["JUDGE"].gvoice == "Sulafat" and b["WITNESS"].gvoice == "Algenib"
    setting("V91_SAFE_MODE", "TRUE"); b2 = SHOW.extra_blends({"Charon", "Kore"}); assert b2["JUDGE"].gvoice in ("", "Gacrux")   # exactly the v9 rule

def test_golden_frames_flag_off_equals_v9(tmp_path, setting):
    from tests.golden_frames import render_hashes, v9_baseline, same_as_v9
    setting("ATMOSPHERE_ON", "FALSE"); v9_baseline(setting)          # the helper makes the episode's own stack decision, so the flag must be off for the v9 comparison; v12 B0b: so must every later layer
    assert same_as_v9(render_hashes(str(tmp_path)))                  # v12 B0b: always compared - this skipped on every machine (see tests/golden_frames.py)

def test_the_v9_comparison_is_live_and_a_default_on_layer_fails_it(tmp_path, setting):
    """v12 B0b, the other way round: with the v11 particle layer left on (its default) the same comparison must FAIL and say why."""
    from tests.golden_frames import render_hashes, same_as_v9, golden, versions, LATER_LAYERS_OFF
    assert core.DEFAULTS["PARTICLES_ON"][0] == "TRUE" and set(LATER_LAYERS_OFF) <= set(core.DEFAULTS)
    setting("ATMOSPHERE_ON", "FALSE"); h = render_hashes(str(tmp_path))
    with pytest.raises(AssertionError) as e: same_as_v9(h)
    assert "frames differ from the v9 golden frames" in str(e.value)
    assert versions() in [golden()["versions"]] + golden()["verified"], f"add {versions()} to the verified list only after the v9 comparison passed on it"
    with pytest.raises(AssertionError): same_as_v9(golden()["frames"][:-1])          # a missing frame is a difference too
