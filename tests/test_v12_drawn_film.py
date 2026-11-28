"""v12 DRAWN BY CODE (D6): whole productions in the drawn arm - the render, its record, the finished file's audit and check drawn_shown (split from test_v12_drawn.py: ruling 4 (E), whole productions in a file of their own)."""
import datetime as dt, json, os, re, shutil
import pytest
from whatifs import core, scenes as SCN

FROZEN = dt.datetime(2031, 3, 8, 10, 0, tzinfo=dt.timezone.utc)          # this file's own episode ids (no other test file uses 2031-03-08)


def _setup(monkeypatch, setting, on=True, minute=0):
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    from whatifs import manage as MG, episode as EP
    now = FROZEN + dt.timedelta(minutes=minute)
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    monkeypatch.setattr(EP, "now_utc", lambda: now); monkeypatch.setattr(EP, "_cleanup_work", lambda out: None)      # the job's folder is read after the run
    setting("DRAWN_ON", "TRUE" if on else "FALSE"); setting("DRAWN_SHARE_PCT", "100"); setting("DRAWN_MIN_S", "1.0"); setting("GRAPHICS_FREE_SEC", "0")
    jobs = []; real = EP._render
    monkeypatch.setattr(EP, "_render", lambda job: (jobs.append(job), real(job))[1])
    return (now + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"), "EP" + now.strftime("%Y%m%d%H%M"), jobs


def _ledger(): return {x["feature"]: (x["status"], x["evidence"]) for x in core.store().rows("Feature_Ledger") if x["feature"] in ("drawn_plan", "drawn_shown")}


def _seg_i(path): m = re.search(r"seg(\d{3})_(\d+)\.mp4$", str(path)); return (int(m.group(1)), int(m.group(2))) if m else None


# ------------------------------------------------------------------ 12. one whole production in the arm; 10. the render and the record
def test_a_whole_production_in_the_arm_draws_proves_and_records(monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import episode as EP, render as RN, costguard as CG
    slot, ep, jobs = _setup(monkeypatch, setting); c = watch(monkeypatch); calls = {"drawn": [], "graphic": []}
    real_d, real_g = RN.drawn_segment, RN.graphic_segment
    def spy_d(L, bg, path, *a):
        assert RN._OVL["obj"] is None, "something was drawn over a drawn scene"; calls["drawn"].append(_seg_i(path)); return real_d(L, bg, path, *a)
    monkeypatch.setattr(RN, "drawn_segment", spy_d); monkeypatch.setattr(RN, "graphic_segment", lambda g, bg, path, n: (calls["graphic"].append(_seg_i(path)), real_g(g, bg, path, n))[1])
    real_f = RN.frame_at; ws = []
    monkeypatch.setattr(RN, "frame_at", lambda p, t, **k: (ws.append(k.get("w")), real_f(p, t, **k))[1])          # F-11: the audit's and the check's reads at the scene's own width
    try:
        r = EP.produce(slot); assert r["ok"], r
        job = jobs[-1]; drawn = [m for m in job.segmeta if m.get("drawn")]
        assert drawn, "this id's film drew no scene: name another id in the record (TO VERIFY 1)"
        lw = {int(x["L"]["W"]) for x in job.drawn.values() if isinstance(x, dict) and x.get("L")}
        assert ws and len(lw) == 1 and all(w in lw for w in ws), (ws, lw)                                       # every frame read passes w = the scene's layout width
        assert not ({m["i"] for m in drawn} & {x[0] for x in calls["graphic"] if x}), "a drawn scene's line also played the number card"
        assert c["text:scene"] == 1 and [l for l in CG.lines("long") if l["key"] == "drawn_scenes"]
        led = _ledger(); assert led["drawn_plan"][0] == "PASS" and led["drawn_shown"][0] == "PASS", led
        assert led["drawn_shown"][1].startswith("the drawn arm held:") and "scene(s) drawn" in led["drawn_shown"][1]
        arm = json.loads(next(x for x in core.store().rows("Video_Features") if x["video_key"] == ep)["arm"]); assert arm.get("drawn"), arm
        assert all(job.drawn[m["i"]]["ok"] and job.drawn[m["i"]].get("ink", 0) >= core.S("DRAWN_INK_MIN", float) for m in drawn)
        m0 = drawn[0]; before = [(m["i"], m["k"], m.get("drawn")) for m in job.segmeta]; redrawn = []
        real_p = RN.parallax_segment; monkeypatch.setattr(RN, "parallax_segment", lambda img, path, *a, **k: (redrawn.append(_seg_i(path)), real_p(img, path, *a, **k))[1])
        job.rerender_times([m0["f0"] / job.fps], only={(m0["i"], m0["k"])})          # exactly the named state is re-drawn, and is no longer drawn - at its FIRST second (F-16, D2-07: the state before lies inside the +-1 s window, so `only` keeps it out)
        assert redrawn == [(m0["i"], m0["k"])] and m0["drawn"] is False
        assert [(m["i"], m["k"], m.get("drawn")) for m in job.segmeta if (m["i"], m["k"]) != (m0["i"], m0["k"])] == [x for x in before if (x[0], x[1]) != (m0["i"], m0["k"])]
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)


def test_the_same_film_with_the_switch_off_asks_nothing_and_draws_nothing(monkeypatch, setting):
    from tests.paid_calls import watch
    from whatifs import episode as EP
    slot, ep, jobs = _setup(monkeypatch, setting, on=False); c = watch(monkeypatch)
    try:
        r = EP.produce(slot); assert r["ok"], r
        assert c["text:scene"] == 0 and not any(m.get("drawn") for m in jobs[-1].segmeta) and jobs[-1].drawn == {}
        assert _ledger() == {"drawn_plan": ("N/A", "not applicable: the drawn scenes are switched off"), "drawn_shown": ("N/A", "not applicable: the drawn scenes are switched off")}
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)


def test_a_refused_scene_is_its_moving_still_and_a_failed_render_never_the_zero_card(monkeypatch, setting):
    from whatifs import episode as EP, render as RN
    from whatifs.shotplan import pieces_for
    from whatifs import drawn as DRAWN
    slot, ep, jobs = _setup(monkeypatch, setting, minute=1); seen = []; zero = []; comp = {}
    real_proof = SCN.proof
    def proof(sc, units, i, dur, fps):
        seen.append(i); comp.setdefault(i, f"{sc['template']}{sc['variant']}")
        if len(seen) == 1: raise DRAWN.Refused("planted refusal")                                                      # T-1: the proof RAISES - the render's except gives the reason
        return real_proof(sc, units, i, dur, fps)
    monkeypatch.setattr(SCN, "proof", proof)
    def boom(*a, **k): raise RuntimeError("planted encoder fault")
    monkeypatch.setattr(RN, "drawn_segment", boom)
    real_g = RN.graphic_segment
    monkeypatch.setattr(RN, "graphic_segment", lambda g, bg, path, n: (zero.append((_seg_i(path), bool(bg), (g or {}).get("label") == "")), real_g(g, bg, path, n))[1])
    try:
        r = EP.produce(slot); assert r["ok"], r
        job = jobs[-1]; assert seen, "this id's film carries no scene"
        i0 = seen[0]; st0 = [m for m in job.segmeta if m["i"] == i0]
        assert job.drawn[i0] == {"ok": False, "why": "planted refusal"} and not any(m.get("drawn") for m in st0)
        dur0 = sum(m["nf"] for m in st0) / job.fps; assert len(st0) <= pieces_for(dur0 + 0.05, "still", False, ep) + 1         # cut as a still is
        assert not any(z[0] and z[0][0] == i0 and z[1] for z in zero)                                                         # its still, never the card, when a picture exists
        for i in seen[1:]:                                                                                                    # the render failed: its still, never the "0"
            assert job.drawn[i]["ok"] is False and job.drawn[i]["why"].startswith("the render failed") and not any(z[0] and z[0][0] == i and z[2] for z in zero)
        assert _ledger()["drawn_shown"][0] == "PASS" and "shown as its still" in _ledger()["drawn_shown"][1]
        arm = json.loads(next(x for x in core.store().rows("Video_Features") if x["video_key"] == ep)["arm"])
        assert comp[i0] not in (arm.get("drawn") or []), (comp, arm)                                                         # F-10: the learning core never counts a scene no viewer saw
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)


def test_an_error_inside_the_audit_shows_every_drawn_scene_as_its_still_and_holds_nothing(monkeypatch, setting):
    """The Fable re-audit, open issue 256 (a): an error inside the finished file's audit never holds a video for a drawn scene."""
    from whatifs import episode as EP
    slot, ep, jobs = _setup(monkeypatch, setting, minute=5); seen = []
    def boom(master, job): seen.append(sum(1 for m in job.segmeta if m.get("drawn"))); raise RuntimeError("planted")
    monkeypatch.setattr(SCN, "audit", boom)
    try:
        r = EP.produce(slot); assert r["ok"], r                                              # the production ends and is NOT held
        job = jobs[-1]; assert seen and seen[0] >= 1, "this id's film drew no scene: name another minute in the record"
        assert not any(m.get("drawn") for m in job.segmeta)                                  # every drawn state became its still
        assert any(str(x.get("why", "")).startswith("the audit could not run (RuntimeError)") for x in job.drawn.values() if isinstance(x, dict))
        led = _ledger(); assert led["drawn_shown"][0] == "PASS" and "the audit could not run" in led["drawn_shown"][1], led
    finally: shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)
