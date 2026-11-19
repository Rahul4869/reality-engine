"""The L1 renderer trial: the drawn scenes' shapes drawn by our own drawing code and by one candidate library on the same display list, judged by a rule written before any number. See docs/CURRENT/SYSTEM.md."""
import hashlib, os, statistics, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from whatifs import drawn as DRAWN

SIZES = ((1920, 1080), (640, 360))
ERR_AT = (640, 360)              # the reference (Own at EIGHT times the size) is measured here only: at 1920 x 1080 it would be a 15360 x 8640 layer
RULE = "the candidate wins only when it is available, gives the same bytes twice, err <= 0.8 x own's and ms <= 1.5 x own's; in every other case own stays"


class Skia:
    """The candidate (skia-python, BSD) behind the drawing seam: rect, line, arc, poly and result on a straight-alpha layer. Never imported by whatifs/."""
    def __init__(self, W, H):
        import skia
        self.sk, self.W, self.H = skia, int(W), int(H)
        self.surface = skia.Surface(self.W, self.H); self.canvas = self.surface.getCanvas(); self.canvas.clear(skia.ColorTRANSPARENT)

    def _paint(self, rgb, a, stroke=None):
        sk = self.sk; p = sk.Paint(AntiAlias=True, Color4f=sk.Color4f(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, float(a)))
        if stroke: p.setStyle(sk.Paint.kStroke_Style); p.setStrokeWidth(float(stroke))
        return p

    def _path(self, pts, close=False):
        path = self.sk.Path(); path.moveTo(*pts[0])
        for q in pts[1:]: path.lineTo(*q)
        if close: path.close()
        return path

    def rect(self, x0, y0, x1, y1, rgb, a=1.0, width=0.0):
        self.canvas.drawRect(self.sk.Rect.MakeLTRB(x0, y0, x1, y1), self._paint(rgb, a, width if width > 0 else None))

    def line(self, pts, rgb, a=1.0, width=1.0): self.canvas.drawPath(self._path(pts), self._paint(rgb, a, width))

    def arc(self, cx, cy, r, a0, a1, rgb, a=1.0, width=1.0):
        self.canvas.drawArc(self.sk.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), a0, a1 - a0, False, self._paint(rgb, a, width))

    def poly(self, pts, rgb, a=1.0): self.canvas.drawPath(self._path(pts, close=True), self._paint(rgb, a))

    def result(self):
        sk = self.sk; arr = self.surface.makeImageSnapshot().toarray(colorType=sk.kRGBA_8888_ColorType, alphaType=sk.kUnpremul_AlphaType).astype(np.float32)
        return arr[..., :3].copy(), arr[..., 3] / 255.0


BACKENDS = {"own": lambda W, H: DRAWN.Own(W, H), "skia": Skia}


def _layers(make, scenes, W, H):
    """Every gold scene's layer at each step's end, through one backend: (list of premultiplied frames, ms a frame)."""
    out, ms = [], []
    for sc in scenes:
        L = DRAWN.layout(DRAWN.expand(sc), W, H, 8.0, None, 5.0, 14, 2.0)
        for st in L["steps"]:
            t0 = time.perf_counter(); col, alp = DRAWN.layer(L, st["t0"] + st["on"], draw=make); ms.append(1000 * (time.perf_counter() - t0))
            out.append(np.clip(col * alp[..., None], 0, 255).astype(np.uint8))
    return out, statistics.median(ms) if ms else 0.0


def _digest(frames): h = hashlib.sha256(); [h.update(f.tobytes()) for f in frames]; return h.hexdigest()


def run(scenes=None):
    """{"rows": [{backend, available, why, ms, err, same}], "winner", "clause"} - a backend that cannot be imported or cannot draw is a RESULT
    (available False with its own words), never a skip and never a failure."""
    scenes = scenes or [v["gold"] for v in DRAWN.TEMPLATES.values()]
    ref, _ = _layers(lambda W, H: DRAWN.Own(W, H, k=8), scenes, *ERR_AT)
    rows = []
    for name, make in BACKENDS.items():
        row = {"backend": name, "available": True, "why": "", "ms": {}, "err": None, "same": False}
        try:
            for W, H in SIZES:
                fr, ms = _layers(make, scenes, W, H); row["ms"][f"{W}x{H}"] = round(ms, 2)
                if (W, H) == ERR_AT:
                    row["err"] = round(float(np.mean([np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))) for a, b in zip(fr, ref)])), 3)
                    row["same"] = _digest(fr) == _digest(_layers(make, scenes, W, H)[0])
        except Exception as e:
            row.update(available=False, why=f"{type(e).__name__}: {str(e)[:160]}")
        rows.append(row)
    w, clause = winner(rows)
    return {"rows": rows, "winner": w, "clause": clause}


def winner(rows):
    """THE RULE, written before any number existed (H34: own stays)."""
    own = next((r for r in rows if r["backend"] == "own"), None); cand = next((r for r in rows if r["backend"] != "own"), None)
    if cand is None: return "own", "no candidate"
    if not cand.get("available"): return "own", f"the candidate is not available ({cand.get('why') or 'no reason given'})"
    if not cand.get("same"): return "own", "the candidate did not give the same bytes twice"
    if own is None or own.get("err") is None or cand.get("err") is None: return "own", "no error could be measured"
    if cand["err"] > 0.8 * own["err"]: return "own", f"its error {cand['err']} is above 0.8 x own's {own['err']}"
    slow = [k for k, v in cand.get("ms", {}).items() if v > 1.5 * (own.get("ms") or {}).get(k, 0)]
    if slow: return "own", f"it is slower than 1.5 x own's at {', '.join(slow)}"
    return cand["backend"], f"available, the same bytes twice, error {cand['err']} <= 0.8 x {own['err']}, at most 1.5 x own's time"


def main():
    r = run()
    print("| backend | available | ms a frame | error (0-255) | same twice | why |"); print("|---|---|---|---|---|---|")
    for x in r["rows"]: print(f"| {x['backend']} | {x['available']} | {x['ms']} | {x['err']} | {x['same']} | {x['why']} |")
    print(f"\nRULE: {RULE}\n\nL1 TRIAL: winner {r['winner']} ({r['clause']})")


if __name__ == "__main__": main()
