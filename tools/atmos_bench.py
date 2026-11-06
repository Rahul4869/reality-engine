"""v9.1 render performance check (run: python tools/atmos_bench.py [seconds]). Renders the same still shot through the REAL render path (camera move +
show overlay + encoder) at the production work size with ATMOSPHERE_ON false and true, prints the time of each, the overhead %, and the automatic
degrade steps when the budget is forced low."""
import os, sys, time, tempfile, json
import numpy as np, cv2
os.environ.setdefault("WI_FAKE", "1")
from whatifs import core, render as RN, atmosphere as AT, showfx as SFX

def run(sec, atmos, budget=None):
    core._store = core.LocalStore(tempfile.mkdtemp() + "/s.json"); core._store.ensure_tabs()
    if budget is not None: core.set_setting("ATMOSPHERE_MAX_OVERHEAD_PCT", str(budget))
    ww, wh = RN.work_size(); fps = RN.fps(); n = int(sec * fps); tmp = tempfile.mkdtemp()
    rng = np.random.default_rng(5); img = (rng.random((wh * 13 // 10, ww * 13 // 10, 3)) * 255).astype(np.uint8)
    cv2.circle(img, (img.shape[1] // 2, img.shape[0] // 3), img.shape[0] // 8, (250, 250, 250), -1); p = os.path.join(tmp, "s.png"); cv2.imwrite(p, img)
    units = [{"start": float(i * 4), "end": float(i * 4 + 4), "text": "fire and lava" if i % 3 == 0 else "a street", "show": [], "speaker": "DIRECTOR"} for i in range(int(sec / 4) + 2)]
    shots = [{"prompt": u["text"], "impact": i == 1} for i, u in enumerate(units)]
    plan = {"intensity": 2, "exhibits": [], "verdict": {"winner": "vale"}, "hud_spec": []}
    parts = [SFX.ShowOverlay(units, plan, ww, wh, fps, seed="B")]
    atm = None
    if atmos:
        atm = AT.Atmosphere(units, shots, plan, ww, wh, fps, seed="B", beats=[4.0, 9.0]); parts.insert(0, atm)
    from whatifs import reactions as RX
    RN.set_overlay(RX.Stack(parts)); RN.set_cursor(0); RN._LAST["move"] = None
    t = time.time(); RN.parallax_segment(p, os.path.join(tmp, "o.mp4"), n, seed=3, move="push_in"); el = time.time() - t
    RN.set_overlay(None)
    return el, atm

if __name__ == "__main__":
    sec = float(sys.argv[1]) if len(sys.argv) > 1 else 10
    off, _ = run(sec, False); on, atm = run(sec, True)
    print(json.dumps({"work_size": RN.work_size(), "seconds_of_video": sec, "render_s_atmos_off": round(off, 2), "render_s_atmos_on": round(on, 2),
                      "overhead_pct": round((on - off) / off * 100, 1), "budget_pct": core.S("ATMOSPHERE_MAX_OVERHEAD_PCT"), "dropped": atm.dropped}))
    _, atm2 = run(min(sec, 8), True, budget=1)
    print(json.dumps({"forced_budget_pct": 1, "degrade_steps": atm2.dropped}))
