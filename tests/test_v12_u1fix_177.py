"""v12 J 177 (a), as N/RULINGS_U1c.md section 1 rules it again: check camera_shown (`path.shown_report`) judges a state with an act when it was DRAWN
AS A STILL - type "still", or type "living" / "kling" whose record carries the key "clip" and it is false (its clip failed, a later piece k > 0, or
a repair re-drew it). A living / kling record without the key, a clip that played, and every graphic, reaction or stock state are never judged:
the type decides, nothing else. The render's record (`ctx['path_states']`, episode.py) carries the key."""
import os, shutil
from whatifs import core, contract as CON, path as PATH, episode as EP, qc as QCM

OWN_IDS = ("EP209806170900",)      # the whole production of this file: an id no other test file uses

ACT2 = -1                          # act 2's sign, as its shots' marks give it
SHOTS = [{"type": "still", "path": {"act": 1, "sign": 1}}, {"type": "still", "path": {"act": 2, "sign": ACT2}}, {"type": "still", "path": {"act": 2, "sign": ACT2}}]

def _st(**kw):
    s = {"t0": 21.0, "t1": 23.0, "i": 2, "type": "kling", "act": 2, "src": 1, "move": "drift", "sign": ACT2, "fallback": False, "clip": False}
    s.update(kw); return s

def _rep(*states): return PATH.shown_report(list(states), SHOTS)

def test_i_a_kling_state_drawn_as_a_still_with_a_move_off_the_path_is_one_problem_naming_its_time():
    r = _rep(_st(move="pull"))
    assert r["states"] == 1 and len(r["problems"]) == 1 and "at 21.0 s" in r["problems"][0] and "'pull'" in r["problems"][0], r

def test_ii_a_kling_state_drawn_as_a_still_against_its_acts_direction_is_a_problem():
    r = _rep(_st(sign=-ACT2))
    assert r["states"] == 1 and r["problems"] == ["at 21.0 s the camera travelled against act 2's direction"], r

def test_iii_a_living_state_drawn_as_a_still_in_its_acts_direction_is_counted_and_passes():
    r = _rep(_st(type="living"))
    assert r["states"] == 1 and r["acts"] == 1 and r["moves"] == {"drift": 1} and r["problems"] == [], r

def test_iv_a_clip_that_played_is_not_judged():
    r = _rep(_st(clip=True, move="", sign=0))
    assert r["states"] == 0 and r["problems"] == [], r

def test_v_a_living_or_kling_record_without_the_key_clip_is_not_judged():
    for t in ("kling", "living"):
        s = _st(type=t, move="pull", sign=0); del s["clip"]
        r = _rep(s); assert r["states"] == 0 and r["problems"] == [], (t, r)

def test_vi_a_graphic_card_recorded_with_no_move_is_not_judged():
    r = _rep(_st(type="graphic", move="", sign=0))
    assert r["states"] == 0 and r["problems"] == [], r

def test_vii_a_cutaway_recorded_as_the_render_records_it_is_not_judged():
    r = _rep(_st(type="reaction", move="", sign=0, fallback=False))                      # the cutaway's record, as tests/test_v12_inside.py pins it
    assert r["states"] == 0 and r["problems"] == [], r

def test_viii_a_re_drawn_graphic_card_is_not_judged_the_type_decides():
    r = _rep(_st(type="graphic", move="drift", sign=ACT2))
    assert r["states"] == 0, r
    for t in ("stock", "reaction", "graphic", "anything"):                                # never judged, on any record
        r = _rep(_st(type=t, move="pull", sign=-ACT2, src=0)); assert r["states"] == 0 and r["problems"] == [], (t, r)

def test_a_still_is_judged_as_before_with_or_without_the_key_clip():
    for s in (_st(type="still", move=""), _st(type="still", move="", clip=True)):
        r = _rep(s); assert r["states"] == 1 and len(r["problems"]) == 1 and "was not recorded: ''" in r["problems"][0], (s, r)
    s = _st(type="still", move=""); del s["clip"]; assert _rep(s)["states"] == 1

def test_a_film_of_cards_cutaways_and_a_re_drawn_clip_state_passes():
    r = _rep(_st(type="living"), _st(type="graphic", move="", sign=0, t0=24.0), _st(type="reaction", move="", sign=0, t0=26.0),
             _st(type="kling", clip=True, move="", sign=0, t0=28.0), _st(type="graphic", t0=30.0))
    assert r["states"] == 1 and r["problems"] == [], r

def test_a_whole_f1_production_records_a_re_drawn_clip_state_and_camera_shown_judges_it(monkeypatch, setting):
    """The render's record: a whole F1 production (the camera-path arm). One still shot of an act is recorded AS THE RENDER RECORDS A PLAYED CLIP
    (type living; piece 0 clip True, move '', sign 0; a later piece drawn as a still) - a named tool of this test, the fake film buys no clip - and the
    final check is made to find a black stretch on it ONCE, so the quality control's fix path (fixes.auto_fix -> rerender_times) re-draws it. Its
    `path_states` record then has `clip` False, shown_report counts it, and the whole film - its graphic cards and cutaways inside acts with it - passes."""
    from tests import test_v12_opening_e2e as E2E
    from whatifs import ladder as LAD
    E2E._start(monkeypatch, setting); setting("FORMAT_FORCE", "F1"); setting("INSIDE_ON", "TRUE"); setting("ENDINGS_ON", "TRUE"); setting("CAMERA_PATH_ON", "TRUE")
    LAD.override("owner", "make it anyway"); ep = OWN_IDS[0]
    target = {}; planted = []; real_render = EP._render; real_full = QCM.full_check; real_scan = QCM.scan_times
    def render(job, *a, **k):
        out = real_render(job, *a, **k)
        if not target:
            by = {}
            for m in job.segmeta: by.setdefault(m["i"], []).append(m)
            i = next((i for i in sorted(by) if i > 0 and all(m.get("act") is not None and m.get("type") == "still" and not m.get("fallback") and m.get("img") for m in by[i])), None)
            if i is not None:
                for m in by[i]:
                    m["type"] = "living"
                    if m["k"] == 0: m.update(clip=True, move="", sign=0)                  # as the render records a clip's state (piece 0); a later piece was drawn as a still
                m0 = min(by[i], key=lambda m: m["k"]); target.update(i=i, t=m0["f0"] / job.fps + 0.1)
        return out
    def full(c):
        r = real_full(c)
        if target and not planted:
            planted.append("black"); return dict(r, ok=False, problems=list(r.get("problems") or []) + [{"code": "black", "detail": "planted", "fix": "", "t": target["t"], "idx": None}])
        return r
    def scan(path):
        if planted == ["black"]: planted.append("scan"); return {"black": [target["t"]], "frozen": []}
        return real_scan(path)
    monkeypatch.setattr(EP, "_render", render); monkeypatch.setattr(QCM, "full_check", full); monkeypatch.setattr(QCM, "scan_times", scan)
    real_mark = PATH.mark                                                                 # RULINGS_U3u (2): the fake F1 film has no card or cutaway inside an act - one marked still of an act (never its first) becomes the code-made reaction cutaway before the render draws it, as tests/test_v12_inside.py 1195 does
    def mark(shots_, *a, **k):
        out_, plan_ = real_mark(shots_, *a, **k)
        j = next((j for j, s in enumerate(out_) if j > 0 and (s.get("path") or {}).get("act") is not None and not s["path"].get("first") and s.get("type") == "still"), None)
        if j is not None: out_[j] = dict(out_[j], type="reaction", speaker="SKEPTIC")
        return out_, plan_
    monkeypatch.setattr(PATH, "mark", mark)
    gate = {}; real_run = CON.run
    monkeypatch.setattr(CON, "run", lambda stage, c, *a, **k: (gate.__setitem__(stage, c), real_run(stage, c, *a, **k))[1])
    EP.produce(E2E._slot(10), episode_id=ep)
    assert target and planted == ["black", "scan"], (target, planted)                    # the fix path ran on the planted clip state
    ps = gate["final"]["path_states"]; shots = gate["final"]["shots"]; i = target["i"]
    rec = [s for s in ps if s["i"] == i]
    assert rec and all(s["type"] == "living" and s["clip"] is False and not s["fallback"] and s["move"] in PATH.MOVES and s["sign"] == shots[i]["path"]["sign"]
                       for s in rec), rec                                                 # the record: drawn as a still, in its act's direction
    assert PATH.shown_report(rec, shots)["states"] == len(rec)                           # ... and camera_shown judges it
    assert any(s["type"] in ("graphic", "reaction") and s["act"] is not None and s["clip"] is False for s in ps), ps      # cards / cutaways inside acts are in this film
    whole = PATH.shown_report(ps, shots); assert whole["problems"] == [], whole
    assert CON.p_camera_shown(gate["final"])[0] == CON.PASS, CON.p_camera_shown(gate["final"])
    shutil.rmtree(os.path.join(core.WORK, ep), ignore_errors=True)



def test_camera_shown_never_judges_a_card_or_a_cutaway_whose_record_says_clip_false():
    """J 177 (a), RULINGS_U3za: the TYPE decides (path.shown_report). The render writes "clip" on EVERY state (episode.py path_states), so a graphic
    card and a reaction cutaway inside an act are recorded with clip False, move '' and sign 0 (episode.py: mv_ is '' for a graphic, a cutaway).
    Judged as stills they would fail a good film; they are never judged - only the still beside them is."""
    shots = [{"type": "still", "path": {"act": "A", "place": "p", "sign": 1, "first": True}},
             {"type": "graphic", "path": {"act": "A", "place": "p", "sign": 1, "first": False}},
             {"type": "reaction", "path": {"act": "A", "place": "p", "sign": 1, "first": False}}]
    rec = [{"t0": 0.0, "t1": 2.0, "i": 0, "type": "still", "act": "A", "src": 0, "move": PATH.MOVES[0], "sign": 1, "fallback": False, "clip": False},
           {"t0": 2.0, "t1": 4.0, "i": 1, "type": "graphic", "act": "A", "src": 0, "move": "", "sign": 0, "fallback": False, "clip": False},
           {"t0": 4.0, "t1": 6.0, "i": 2, "type": "reaction", "act": "A", "src": 0, "move": "", "sign": 0, "fallback": False, "clip": False}]
    r = PATH.shown_report(rec, shots)
    assert r["states"] == 1 and r["problems"] == [], r
