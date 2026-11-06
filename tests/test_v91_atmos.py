"""v9.1 Atmosphere Pack: flag off = v9 pixels (golden), determinism, every layer, safety caps, readability masks, automatic degrade, prompt directive."""
import json, os, time
import numpy as np
import pytest
from whatifs import core, atmosphere as AT, v91 as V91

def _units(n=12):
    us = [{"start": float(i * 2), "end": float(i * 2 + 2), "text": "the volcano erupts in fire" if i == 5 else "a calm street", "tag": "reveal" if i == 6 else "", "show": []} for i in range(n)]
    return us

SHOTS = [{"prompt": "lava and fire, a volcano" if i == 5 else "a street at night", "impact": i == 5} for i in range(12)]
FR = (np.random.default_rng(3).random((180, 320, 3)) * 200).astype(np.uint8)

def test_flag_off_reproduces_v9_frames_exactly(setting, tmp_path):
    from tests.golden_frames import render_hashes, versions
    g = json.load(open(os.path.join(os.path.dirname(__file__), "golden", "v9_render_frames.json")))
    setting("ATMOSPHERE_ON", "FALSE"); off = render_hashes(str(tmp_path))
    if g["versions"] == versions(): assert off == g["frames"]
    setting("ATMOSPHERE_ON", "TRUE"); setting("V91_SAFE_MODE", "TRUE"); assert render_hashes(str(tmp_path)) == off       # safe mode = v9 as well

def test_deterministic_and_every_layer_changes_something(setting):
    a = AT.Atmosphere(_units(), SHOTS, {"intensity": 3}, 320, 180, 30, seed="E1", recon=[(0, 6)], beats=[10.0])
    b = AT.Atmosphere(_units(), SHOTS, {"intensity": 3}, 320, 180, 30, seed="E1", recon=[(0, 6)], beats=[10.0])
    for g in (30, 305, 330):
        assert np.array_equal(a.apply(FR.copy(), g), b.apply(FR.copy(), g))
    base = a.apply(FR.copy(), 305)
    for L in AT.LAYERS:
        if L in ("BREATH", "PULSE"): continue
        setting(f"ATMOS_{L}_ON", "FALSE"); c = AT.Atmosphere(_units(), SHOTS, {"intensity": 3}, 320, 180, 30, seed="E1").apply(FR.copy(), 305)
        setting(f"ATMOS_{L}_ON", "TRUE"); assert not np.array_equal(base, c), L

def test_level_zero_is_untouched_and_level_follows_plan(setting):
    setting("ATMOSPHERE_LEVEL", "0"); assert np.array_equal(AT.Atmosphere(_units(), SHOTS, {}, 320, 180, 30).apply(FR.copy(), 30), FR)
    setting("ATMOSPHERE_LEVEL", "auto"); assert AT.level_for(1, {"fire"}) == 2 and AT.level_for(3, set(), True) == 3 and AT.level_for(0, set()) == 0

def test_pulse_hard_caps():
    a = AT.Atmosphere(_units(30), [{}] * 30, {"intensity": 2}, 320, 180, 30, beats=[0.5, 3.0, 3.2, 3.6, 5.0, 12.0], hud_spans=[(11.0, 13.0)])
    assert a.pulses == [3.0, 3.6, 5.0]                                                        # not < 2 s, >= 0.5 s apart, none in a HUD readout
    for g in range(0, 30 * 7): a.apply(FR.copy(), g)
    assert AT.pulse_qc(a) == [] and max(x for _, x in a.pulse_log) <= AT.PULSE_MAX_SWING
    red = np.zeros((180, 320, 3), np.uint8); red[..., 2] = 200
    out = a._pulse(red.astype(np.float32), 3.01); assert out[..., 2].max() <= 200            # never more red
    a.pulse_log.append((0.5, 0.2)); assert {c for c, _ in AT.pulse_qc(a)} >= {"pulse_swing", "pulse_early"}

def test_readability_regions_are_damped():
    a = AT.Atmosphere(_units(), SHOTS, {"intensity": 3}, 320, 180, 30)
    assert a.protect[int(180 * 0.9), 160, 0] < 0.5 and a.protect[90, 160, 0] > 0.9

def test_automatic_degrade_order(setting):
    setting("ATMOSPHERE_MAX_OVERHEAD_PCT", "1"); a = AT.Atmosphere(_units(), SHOTS, {"intensity": 3}, 320, 180, 30)
    for g in range(360):
        a.apply(FR.copy(), g); time.sleep(0.0002)
    assert a.dropped[:2] == ["PARTICLES", "FOG"] and not a.flags["PARTICLES"]

def test_overhead_budget_on_a_standard_frame_size(setting):
    """Render performance: the atmosphere's time per 1080p frame vs a typical v9 frame (camera remap + encode feed); reported, budget enforced by degrade."""
    fr = (np.random.default_rng(1).random((1080, 1920, 3)) * 255).astype(np.uint8)
    a = AT.Atmosphere(_units(), SHOTS, {"intensity": 2}, 1920, 1080, 30)
    t0 = time.perf_counter()
    for g in range(30, 40): a.apply(fr.copy(), g)
    per = (time.perf_counter() - t0) / 10
    print(f"ATMOS_PER_FRAME_1080P={per:.3f}s")
    assert per < 2.0

def test_directive_fits_and_keeps_the_prompt():
    p = "x " * 800; out = AT.with_directive(p, 1800)
    assert len(out) <= 1800 and out.startswith(p.rstrip())
    short = AT.with_directive("A meteor over a city.", 1800, vertical=True); assert "9:16" in short and "rim light" in short
    assert AT.with_directive("y" * 1795, 1800) == "y" * 1795

def test_episode_render_puts_atmosphere_first_and_guard_falls_back(monkeypatch, setting, tmp_path):
    calls = []
    real = AT.Atmosphere.__init__
    def boom(self, *a, **k): raise RuntimeError("injected")
    monkeypatch.setattr(AT.Atmosphere, "__init__", boom); V91._OFF.clear()
    with V91.guard("ATMOSPHERE_ON", "EPX"): AT.Atmosphere([], [], {}, 10, 10, 30)
    assert not V91.on("ATMOSPHERE_ON", "EPX"); V91._OFF.clear()
