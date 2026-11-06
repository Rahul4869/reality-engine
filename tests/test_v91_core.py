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
    from tests.golden_frames import render_hashes, versions
    setting("ATMOSPHERE_ON", "FALSE")          # the helper makes the episode's own stack decision, so the flag must be off for the v9 comparison
    g = json.load(open(os.path.join(os.path.dirname(__file__), "golden", "v9_render_frames.json")))
    now = render_hashes(str(tmp_path))
    assert len(now) == len(g["frames"])
    if g["versions"] != versions(): pytest.skip(f"golden frames were made with {g['versions']}; this machine has {versions()} (runtime equivalence test still runs)")
    assert now == g["frames"]
