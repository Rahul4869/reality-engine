"""v9.1 golden-frame helper: renders a fixed mini-scene (still with a camera move + the v9 show overlay + a POV effect) on fixed seeds and returns
a SHA-256 of every raw frame handed to the encoder (pre-encode pixels, so encoder builds do not matter). Captured on v9 code in
tests/golden/v9_render_frames.json together with the OpenCV / NumPy versions it was made with."""
import hashlib, json, os, subprocess
import numpy as np, cv2

class _Sink:
    def __init__(self): self.h = []; self.buf = b""
    def write(self, b): self.h.append(hashlib.sha256(b).hexdigest()[:16])
    def close(self): pass

def render_hashes(tmp):
    from whatifs import render as RN, showfx as SFX, core
    sinks = []
    class P:
        def __init__(self, cmd, stdin=None, **k): self.stdin = _Sink(); self.returncode = 0; sinks.append(self.stdin)
        def wait(self): return 0
    real = subprocess.Popen; RN.subprocess.Popen = P
    try:
        rng = np.random.default_rng(7); img = (rng.random((360, 640, 3)) * 255).astype(np.uint8)
        cv2.circle(img, (420, 160), 60, (250, 250, 250), -1); p = os.path.join(tmp, "g.png"); cv2.imwrite(p, img)
        depth = np.tile(np.linspace(0, 1, 640, dtype=np.float32), (360, 1))
        units = [{"start": float(i * 2), "end": float(i * 2 + 1.8), "text": "x", "speaker": "DIRECTOR", "show": []} for i in range(6)]
        units[1]["show"] = ["[EXHIBIT A]", "[METER +1 VALE]"]
        plan = {"exhibits": [{"id": "A", "kind": "RECON", "credit": ""}], "verdict": {"winner": "vale"}, "intensity": 2, "teacup_scenes": [], "hud_spec": []}
        ww, wh = RN.work_size()
        so = SFX.ShowOverlay(units, plan, ww, wh, RN.fps(), seed="GOLD")
        from whatifs import episode as EP, reactions as RX                                  # the SAME stack decision the episode render makes (v9.1)
        atm = EP.atmosphere_layer("GOLD", units, [{"prompt": "a street"}] * len(units), plan, RN.fps(), so)
        RN.set_overlay(RX.Stack([x for x in (atm, so) if x is not None]) if atm is not None else so); RN.set_cursor(0)
        RN._LAST["move"] = None
        RN.parallax_segment(p, os.path.join(tmp, "a.mp4"), 24, seed=11, depth=depth, move="push_in")
        RN.set_cursor(24); RN.set_overlay(RN.with_fx(_OV(), "impact_shake", 12, 5, 24) if hasattr(RN, "with_fx") else None)
        RN.parallax_segment(p, os.path.join(tmp, "b.mp4"), 12, seed=12, depth=depth, move="drift")
    finally:
        RN.subprocess.Popen = real; RN.set_overlay(None)
    return [h for s in sinks for h in s.h]

class _OV:
    def apply(self, fr, g): return fr

def versions(): return {"cv2": cv2.__version__, "numpy": np.__version__}
