"""Render-time comparison of one rehearsal-size episode with ATMOSPHERE_ON true vs false (usage: WI_FAKE=1 WI_SMALL=1 python tools/perf_atmosphere.py). See docs/CURRENT/SYSTEM.md."""
import datetime as dt, json, sys, tempfile, time
sys.path.insert(0, ".")
import numpy as np

def episode_minutes(flag):
    from whatifs import core, manage as MG, episode as EP
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    V.KokoroBackend = lambda blend: ToneVoice()
    core._store = core.LocalStore(tempfile.mkdtemp() + "/s.json"); core._store.ensure_tabs(); MG.setup(); core.set_setting("VOICE", "C")
    core.set_setting("ATMOSPHERE_ON", flag)
    fz = dt.datetime(2026, 11, 4, 3, 15, 7, tzinfo=dt.timezone.utc); EP.now_utc = lambda: fz
    t0 = time.time(); r = EP.produce((fz + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")); total = time.time() - t0
    e = core.store().rows("Episodes")[-1]
    return {"ok": r.get("ok"), "render_min": float(e.get("render_min") or 0), "produce_min": round(total / 60, 2), "atmos": json.loads(e.get("atmos_json") or "{}")}

if __name__ == "__main__":
    off = episode_minutes("FALSE"); on = episode_minutes("TRUE")
    from whatifs import atmosphere as AT, core
    fr = (np.random.default_rng(1).random((1080, 1920, 3)) * 255).astype(np.uint8)
    us = [{"start": float(i * 2), "end": float(i * 2 + 2), "text": "fire" if i == 2 else "street", "show": []} for i in range(10)]
    a = AT.Atmosphere(us, [{"prompt": "fire", "impact": True} if i == 2 else {"prompt": "street"} for i in range(10)], {"intensity": 2}, 1920, 1080, 30, seed="P")
    a.apply(fr.copy(), 70); t = time.perf_counter()
    for g in range(71, 91): a.apply(fr.copy(), g)
    per = (time.perf_counter() - t) / 20
    print(json.dumps({"off": off, "on": on, "render_overhead_pct": round(100 * (on["render_min"] - off["render_min"]) / max(1e-6, off["render_min"]), 1),
                      "atmos_1080p_s_per_frame": round(per, 4)}))
