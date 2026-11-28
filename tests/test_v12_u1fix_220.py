"""U1 fix 220 (open issue 251): THE DRAWN FRAME REDUCES ONLY EACH ITEM'S OWN BOX. drawn.Own reduces (INTER_AREA, factor k) only the boxes its shapes
touched - each widened to multiples of k, never the two whole layers; outside them the layer keeps its cleared value. THE PICTURE MAY NOT CHANGE BY ONE
BYTE: every frame (and every float of the layer under it) equals the whole-layer reduction, kept here as this file's own reference. No clock in it."""
import numpy as np, cv2
from whatifs import drawn as DRAWN

OPTS = {"text_min": 5.0, "words_max": 14, "hold_max": 2.0}


class Whole(DRAWN.Own):
    """THE REFERENCE: the reduction before this fix - both whole layers, every frame."""
    def result(self):
        pm = cv2.resize(self.col * self.alp[..., None], (self.W, self.H), interpolation=cv2.INTER_AREA); al = cv2.resize(self.alp, (self.W, self.H), interpolation=cv2.INTER_AREA)
        return pm / np.maximum(al, 1e-6)[..., None], al


def _L(t, v, W, H):
    return DRAWN.layout(DRAWN.expand(dict(DRAWN.TEMPLATES[t]["gold"], variant=v)), W, H, 8.0, None, **OPTS)


def _times(L, every):
    """Samples of a scene: every `every` seconds, and each step's middle and end (where a shape is half drawn and where it settles)."""
    return sorted({round(x * every, 3) for x in range(int(8.0 / every) + 1)} | {round(s["t0"] + s["on"] * f, 3) for s in L["steps"] for f in (0.5, 1.0)})


def _same(monkeypatch, L, t):
    """(the new frame equals the reference's byte for byte, the layer under it equals the reference's float for float): ONE frame of each, the layer
    each frame was composed from read on its way (drawn.frame takes the module's `layer`)."""
    real = DRAWN.layer; got = []
    monkeypatch.setattr(DRAWN, "layer", lambda L_, t_, draw=None: (lambda r: (got.append(r), r)[1])(real(L_, t_, draw)))
    f1 = DRAWN.frame(L, t); f0 = DRAWN.frame(L, t, draw=Whole); monkeypatch.setattr(DRAWN, "layer", real)
    (c1, a1), (c0, a0) = got
    return f1.tobytes() == f0.tobytes(), (c1.tobytes(), a1.tobytes()) == (c0.tobytes(), a0.tobytes())


def test_every_frame_of_the_suites_scenes_is_byte_for_byte_the_whole_layer_reduction_at_the_small_size(monkeypatch):
    bad = []
    for t in DRAWN.TEMPLATES:                                                          # the number card (count), the timeline (ladder), the compare, and the rest
        for v in (0, 1):
            L = _L(t, v, 640, 360)
            for s in _times(L, 1.0):
                fr, lay = _same(monkeypatch, L, s)
                if not (fr and lay): bad.append((t, v, s, fr, lay))
    assert bad == [], bad


def test_every_frame_of_a_number_card_a_timeline_and_a_compare_is_the_same_at_1920(monkeypatch):
    bad = []
    for t in ("count", "ladder", "compare"):
        L = _L(t, 0, 1920, 1080); st = L["steps"]
        for s in sorted({round(st[1]["t0"] + st[1]["on"] / 2, 3) if len(st) > 1 else 0.3, round(st[-1]["t0"] + st[-1]["on"] / 2, 3), 7.9}):
            fr, lay = _same(monkeypatch, L, s)
            if not (fr and lay): bad.append((t, s, fr, lay))
    assert bad == [], bad


def test_a_scene_whose_shapes_cover_under_a_fifth_of_the_frame_reduces_under_a_quarter_of_the_layer():
    for t, v in (("count", 0), ("ladder", 0), ("compare", 0), ("compare", 1), ("part", 1)):
        for W, H in ((640, 360), (1920, 1080)):
            L = _L(t, v, W, H); m = np.zeros((H, W), bool)
            for it in L["items"]:
                if it["kind"] in ("label", "value"): continue                          # text is the layer's own (PIL), never the drawing seam's
                x0, y0, x1, y1 = [int(round(c)) for c in it["box"]]; m[max(0, y0):y1, max(0, x0):x1] = True
            assert m.mean() < 0.2, (t, v, W, m.mean())
            for s in (_times(L, 1.0) if W < 1000 else [L["steps"][-1]["t0"] + L["steps"][-1]["on"] / 2, 7.9]):
                made = []; DRAWN.layer(L, s, draw=lambda w, h: (made.append(DRAWN.Own(w, h)), made[-1])[1]); o = made[-1]
                assert o.reduced_px == sum((b[2] - b[0]) * (b[3] - b[1]) for b in o.boxes), (t, v, s)      # it counts exactly the widened boxes it reduced
                assert all(b[0] % o.k == 0 and b[1] % o.k == 0 and b[2] % o.k == 0 and b[3] % o.k == 0 for b in o.boxes), o.boxes
                assert not [(u, v_) for u in o.boxes for v_ in o.boxes if u != v_ and v_[0] <= u[0] and v_[1] <= u[1] and u[2] <= v_[2] and u[3] <= v_[3]], o.boxes      # a box inside another is reduced once
                assert o.reduced_px < 0.25 * (W * o.k) * (H * o.k), (t, v, W, s, o.reduced_px / ((W * o.k) * (H * o.k)))


def test_a_full_frame_shape_reduces_the_whole_layer_and_an_empty_layer_reduces_nothing():
    o = DRAWN.Own(64, 36); o.rect(0, 0, 64, 36, (240, 244, 248)); c, a = o.result(); r = Whole(64, 36); r.rect(0, 0, 64, 36, (240, 244, 248))
    assert o.reduced_px == 64 * 36 * 4 and (c.tobytes(), a.tobytes()) == tuple(x.tobytes() for x in r.result())
    e = DRAWN.Own(64, 36); c, a = e.result()
    assert e.reduced_px == 0 and not c.any() and not a.any() and (c.tobytes(), a.tobytes()) == tuple(x.tobytes() for x in Whole(64, 36).result())


def test_shapes_at_odd_places_on_a_layer_whose_width_is_no_multiple_of_sixteen_are_the_reference_float_for_float():
    """Boxes that end at odd pixels, overlap, touch the right and bottom edges, on a 1000 x 563 layer: every float of the result is the reference's."""
    def draw(o):
        o.rect(13.3, 7.6, 27.9, 40.2, (240, 244, 248), 0.8); o.rect(990.4, 500.2, 1000, 563, (255, 190, 70)); o.rect(100.5, 100.5, 900.5, 120.5, (120, 220, 255), 1.0, 3.0)
        o.line([(3.2, 550.7), (300.9, 400.1)], (240, 244, 248), 0.6, 2.5); o.arc(500.3, 281.7, 77.7, -90, 200, (255, 190, 70), 1.0, 9.4)
        o.poly([(611.1 + 30 * np.cos(q * np.pi / 16), 77.7 + 30 * np.sin(q * np.pi / 16)) for q in range(32)], (120, 220, 255), 0.7)
        return o
    o, r = draw(DRAWN.Own(1000, 563)), draw(Whole(1000, 563))
    c, a = o.result(); c0, a0 = r.result()
    assert (c.tobytes(), a.tobytes()) == (c0.tobytes(), a0.tobytes()) and 0 < o.reduced_px < 1000 * 563 * 4
