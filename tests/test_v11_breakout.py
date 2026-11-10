"""v11 Stage C (K158): promise on screen early, the still detector, the Breakout Score, the 48-hour breakout monitor. No keys, no network."""
import datetime as dt, os, subprocess
import pytest
from whatifs import core, breakout as BRK, contract as CON, notify as NT, publish as PUB

def test_promise_must_be_on_screen_early(setting):
    units = [{"start": i * 6.0} for i in range(10)]
    early = [{"type": "still"}] * 2 + [{"type": "kling", "promise": True}] + [{"type": "still"}] * 7
    late = [{"type": "still"}] * 8 + [{"type": "kling", "promise": True}] + [{"type": "still"}]
    setting("PROMISE_SHOT_ON", "TRUE")
    assert CON.p_promise_paid({"shots": early, "units": units})[0] == "PASS"
    assert CON.p_promise_paid({"shots": late, "units": units})[0] == "FAIL"
    assert CON.p_promise_paid({"shots": [{"type": "kling"}] + [{"type": "still"}] * 9, "units": units, "d": {"promise": {"title": "x"}}})[0] == "FAIL"
    assert CON.p_promise_paid({"shots": [{"type": "still"}] * 10, "units": units})[0] == CON.NA          # v11 audit: no animated scene -> not held

def _make(path, local_motion):
    """6 s: a still picture with a slow zoom (the 'Ken Burns' look); optionally a small square that moves on its own (real life in the frame)."""
    over = ("[0:v][1:v]overlay=x='40+30*sin(t*3)':y=60" if local_motion else "[0:v]null")
    src = ["-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=1", "-f", "lavfi", "-i", "color=c=red:size=40x40:rate=25:duration=6"]
    flt = f"[0:v]trim=end_frame=1,loop=150:1:0,setpts=N/25/TB,zoompan=z='1+0.0015*on':d=1:s=640x360:fps=25[bg];" + \
          (f"[bg][1:v]overlay=x='60+120*sin(t*2.5)':y=150[v]" if local_motion else "[bg]null[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-filter_complex", flt, "-map", "[v]", "-t", "6", "-pix_fmt", "yuv420p", path], check=True, timeout=120)

def test_the_still_detector_tells_a_zooming_photo_from_a_living_frame(tmp_path, setting):
    pytest.importorskip("cv2")
    dead, alive = str(tmp_path / "dead.mp4"), str(tmp_path / "alive.mp4")
    _make(dead, False); _make(alive, True)
    a_dead, a_alive = BRK.aliveness(dead), BRK.aliveness(alive)
    assert a_alive["alive_share"] >= 0.6 and a_dead["alive_share"] <= 0.1, (a_dead, a_alive)
    longest = lambda a: max([b - x for x, b in a["dead_stretches"]] or [0])
    assert longest(a_dead) >= 3 and longest(a_alive) <= 1.5, (a_dead, a_alive)      # a slow turn of the moving object is a short pause, not a still

def test_breakout_score_uses_only_evidence_and_names_the_weakest_part():
    ledger = [{"feature": "thumbnails", "status": "PASS"}, {"feature": "titles", "status": "PASS"}, {"feature": "music_bed", "status": "PASS"},
              {"feature": "real_motion", "status": "FAIL"}]
    d = {"premise_score": 8, "hook_score": 9, "retention_check": {"issues": []}, "critique": {"humour": 6, "clarity": 8}, "emotion_beat": "awe"}
    r = BRK.score(d, ledger)
    assert 60 <= r["score"] <= 95 and r["weakest"] == "visual" and r["missing"] == []
    r2 = BRK.score({}, [])
    assert r2["score"] is None and set(r2["missing"]) == set(BRK.WEIGHTS)

def test_monitor_flags_a_breakout_once_and_waits_for_the_owner(monkeypatch, setting):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    now = dt.datetime(2026, 12, 3, 12, 0, tzinfo=dt.timezone.utc)
    pub = (now - dt.timedelta(hours=49)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st = core.store()
    st.append("Episodes", [{"episode_id": "E9", "yt_id": "hot", "slot_et": pub, "status": "LIVE"}])
    st.append("Monitor48", [{"yt_id": f"old{i}", "kind": "long", "v48": 100} for i in range(3)])
    monkeypatch.setattr(BRK, "_views", lambda ids: {i: 900 for i in ids})            # 9x the usual 100
    found = BRK.monitor(now)
    assert [f["yt_id"] for f in found] == ["hot"] and BRK.monitor(now) == []            # once
    row = next(r for r in st.rows("Owner_Actions") if r["kind"] == "breakout")
    assert "9.0x" in row["text"] and not st.rows("Breakout_Queue")                        # nothing happens without the tap
    assert "approved" in NT.answer(row["id"], "BREAKOUT GO E9") and st.rows("Breakout_Queue")[0]["status"] == "APPROVED"
    assert int(float(st.rows("Breakout_Queue")[0]["left"])) == 2 and any(b.get("bench_id") == "BRKE9" for b in st.rows("Premise_Bench"))

def test_contract_has_the_new_checks_and_they_never_count_llm_scores_as_holds():
    ids = [f for f, *_ in CON.FEATURES]
    assert "promise_paid" in ids and "aliveness" in ids and len(ids) == len(set(ids))
    import inspect
    assert "hold" not in inspect.getsource(BRK.score).lower()

def test_score_reads_the_real_evidence_fields():
    r = BRK.score({"owners_cut": {"mean": 8}}, [{"feature": "thumbnails", "status": "PASS"}], {"spine": {"score": 9}},
                  {"hook": 8, "clarity": 7, "humour": 9})
    assert r["components"]["idea"] == 0.9 and r["components"]["hook"] == 0.8 and r["components"]["story"] == 0.8

def test_promise_check_never_holds_for_what_could_not_be_done(setting):
    setting("PROMISE_SHOT_ON", "TRUE")
    units = [{"start": i * 6.0} for i in range(5)]
    assert CON.p_promise_paid({"shots": [{"type": "still"}] * 5, "units": units})[0] == CON.NA                     # budget-trimmed: no Kling
    assert CON.p_promise_paid({"shots": [{"type": "kling"}] + [{"type": "still"}] * 4, "units": units, "pkg": {"promise": {}}})[0] == CON.NA
    assert CON.p_promise_paid({"shots": [{"type": "kling"}] + [{"type": "still"}] * 4, "units": units,
                               "pkg": {"promise": {"thumbnail": "a giant Moon in a courtroom"}}})[0] == "FAIL"

