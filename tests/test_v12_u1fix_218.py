"""U1 fix 218 (open issue 249): A REFUSED SCENE WITHOUT A PICTURE is the number card (C10), so its line is cut as a GRAPHIC is - never micro-cut as a
still, the card restarting at each piece. A whole production in the drawn arm with the pictures before the first moment removed (C10's no-picture road)."""
import os, shutil
from whatifs import core, scenes as SCN
from tests.test_v12_drawn_film import _setup, _seg_i


def test_a_refused_scene_without_a_picture_is_one_card_never_micro_cut(monkeypatch, setting):
    from whatifs import episode as EP, render as RN, drawn as DRAWN
    from whatifs.shotplan import pieces_for
    slot, ep, jobs = _setup(monkeypatch, setting, minute=2)
    setting("MICRO_CUTS_ON", "TRUE"); setting("PIECE_MAX_SEC", "1.0"); setting("PIECE_MAX_SEC_OPENING", "1.0"); setting("PIECE_MIN_SEC", "0.5")
    setting("VISUAL_ANIMATED_MAX_S", "100")                   # a card is one piece; a still of the same line would be several
    seen = []; cards = []; first = {}
    def proof(sc, units, i, dur, fps):
        seen.append(i)
        raise DRAWN.Refused("planted refusal")
    monkeypatch.setattr(SCN, "proof", proof)
    real_g = RN.graphic_segment
    monkeypatch.setattr(RN, "graphic_segment", lambda g, bg, path, n: (cards.append((_seg_i(path), bool(bg))), real_g(g, bg, path, n))[1])
    inner = EP._render
    def strip(job):                                            # no picture up to and including the first moment: its line has no picture to fall to
        i0 = next((i for i, s in enumerate(job.shots) if s.get("type") == "graphic" and s.get("scene")), None)
        if i0 is not None:
            first["i"] = i0
            for j in range(i0 + 1):
                job.files["img"].pop(j, None); job.files["img"].pop(str(j), None)
        return inner(job)
    monkeypatch.setattr(EP, "_render", strip)
    try:
        EP.produce(slot)
        job = jobs[-1]; i0 = first.get("i"); assert i0 is not None and seen and seen[0] == i0, (first, seen)
        st0 = [m for m in job.segmeta if m["i"] == i0]; dur0 = sum(m["nf"] for m in st0) / job.fps
        assert job.drawn[i0]["ok"] is False and st0
        assert pieces_for(dur0, "still", True, ep) > 1, "this id's first moment is too short to tell a still's cut from a card's"
        assert len(st0) == pieces_for(dur0 + 0.05, "graphic", True, ep) == 1, (len(st0), dur0)                  # one card, never micro-cut
        assert {c for c in cards if c[0] and c[0][0] == i0} == {((i0, 0), False)}, cards                         # one piece of card in every render, without a picture
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)


def test_the_refused_scenes_cut_names_the_picture():
    import inspect
    from whatifs import episode as EP
    src = inspect.getsource(EP._render)
    assert '_pieces_for(dur, "still" if (sc_ and not dr_["ok"] and img) else s["type"], opening_, ep)' in src
