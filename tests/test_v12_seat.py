"""v12 V1 - the viewer's seat (Audience, D13): the promise as the first picture, a voice that breathes, few numbers. Every rule is proven both ways:
it passes when kept and fails when broken; the real voice job and the real production are run, so an unwired call is seen."""
import datetime as dt, json, os
import pytest
from whatifs import core, contract as CON, models as M
from whatifs.org import audience as AUD, registry as REG, levers as LV, runner as RUN, rnd as RND

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()
def ctx(text, **k): return dict({"room": {"script": {"script": text}}}, **k)
def U(n, each=4.0, gap=0.1, text="We walk to the mirror and wait."):
    """A voice timeline of n lines, `gap` seconds apart."""
    out = []; t = 0.0
    for _ in range(n): out.append({"start": round(t, 2), "end": round(t + each, 2), "text": text}); t += each + gap
    return out
def shots(*types): return [dict({"type": t, "prompt": f"shot {i}", "unit": i}, **({"graphic": {"kind": "counter"}} if t == "graphic" else {})) for i, t in enumerate(types)]
FLOOD = " ".join(f"At {i} meters the delay is {i * 0.7:.1f} seconds." for i in range(1, 31))                 # the rejected video in one paragraph: every line a statistic
CALM = "You stop brushing. Your reflection does not. " * 30 + "It is 1 second late."
LONG = "\n\n".join(" ".join(f"Sentence number {k} of this paragraph keeps going without any stop." for k in range(8)) for _ in range(6))
THUMB = {"thumb_prompt": "a mirror that shows you one second late"}

# ------------------------------------------------------------------ few numbers
def test_numbers_are_counted_the_way_a_viewer_hears_them():
    c = AUD.count_numbers
    assert c("Light moves at 1.4 meters per second.") == 1 and c("one point four million people") == 1 and c("It is one of a kind.") == 0
    assert c("[tension] DIRECTOR: Two voices, three rooms and 8,000 pillows - 50 percent gone.") == 4 and c("two and a half hours, twice a day") == 2
    assert c("[PUNCH] {slow} No numbers here at all.") == 0 and c("A hundred years, a billion stars") == 2
    assert c("## BEAT 3\nAt hour 1 the tide stalls. Exhibit A: NOAA tide records, 2023. Behold Prototype No 41.") == 0        # a heading, a place in the story, a source's year
    assert c("By day 3, eight billion pillows float 2 meters up.") == 2

def test_viewer_numbers_fails_on_a_flood_of_numbers_and_on_number_graphics_out_of_budget(setting):
    assert CON.p_viewer_numbers(ctx(CALM))[0] == CON.PASS and CON.p_viewer_numbers(ctx(""))[0] == CON.FAIL
    s, ev = CON.p_viewer_numbers(ctx(FLOOD)); assert s == CON.FAIL and "a minute (limit 4)" in ev
    u = U(40); four = shots(*(["still"] * 20 + ["graphic"] * 4 + ["still"] * 16))
    s, ev = CON.p_viewer_numbers(ctx(CALM, shots=four, units=u)); assert s == CON.FAIL and "4 full-screen number graphics (limit 3)" in ev
    early = shots(*(["still", "graphic"] + ["still"] * 38))
    s, ev = CON.p_viewer_numbers(ctx(CALM, shots=early, units=u)); assert s == CON.FAIL and "a number graphic at 4 s (none before 60 s)" in ev
    three = shots(*(["still"] * 20 + ["graphic"] * 3 + ["still"] * 17))
    s, ev = CON.p_viewer_numbers(ctx(CALM, shots=three, units=u)); assert s == CON.PASS and "3 number graphic(s), the first at 82 s" in ev
    setting("GRAPHICS_MAX_LONG", "2"); assert CON.p_viewer_numbers(ctx(CALM, shots=three, units=u))[0] == CON.FAIL
    setting("NUMBERS_PER_MIN_MAX", "8"); setting("GRAPHICS_MAX_LONG", "3"); assert CON.p_viewer_numbers(ctx(FLOOD))[0] == CON.FAIL       # 37 a minute is over any allowed budget
    setting("VIEWER_SEAT_ON", "FALSE"); assert CON.p_viewer_numbers(ctx(FLOOD)) == (CON.NA, "the viewer's seat is switched off (VIEWER_SEAT_ON)")

def test_the_writers_one_mandatory_fix_carries_the_numbers_problem(monkeypatch, setting):
    from whatifs import enforce as ENF
    assert AUD.number_issues(CALM) == [] and "TOO MANY NUMBERS" in AUD.number_issues(FLOOD)[0]
    seen = []
    monkeypatch.setattr(M, "ask", lambda role, system, prompt, **k: seen.append(prompt) or {"script": CALM})
    out, issues = ENF.fix_all({"script": FLOOD}, "brief", {"promise": {"title": "your mirror is late"}}, "EPT")
    assert out["script"] == CALM and any("TOO MANY NUMBERS" in i for i in issues) and "NUMBERS FIX" in seen[0] and len(seen) == 1
    setting("VIEWER_SEAT_ON", "FALSE"); assert AUD.number_issues(FLOOD) == []

# ------------------------------------------------------------------ the shot list: the promise is the first picture
def test_the_shot_list_is_shaped_for_free_first_a_picture_then_few_number_graphics(setting):
    u = U(40); raw = shots(*(["graphic", "still", "graphic"] + ["still"] * 17 + ["graphic"] * 5 + ["stock"] + ["still"] * 14))
    out = AUD.shape(raw, u, THUMB)
    assert out[0]["type"] == "still" and out[0]["hero"] and THUMB["thumb_prompt"] in out[0]["prompt"] and out[0]["seat"] == "first picture"
    assert out[2]["type"] == "still" and out[2]["seat"] == "number graphic too early" and not out[2]["hero"] and "graphic" not in out[2]
    assert [s["type"] for s in out[20:25]] == ["graphic"] * 3 + ["still"] * 2 and out[24]["seat"] == "number graphic over the budget" and out[25]["type"] == "stock"
    assert raw[0]["type"] == "graphic" and AUD.shape(out, u, {}) == out                                  # the input is never changed; shaping twice changes nothing
    assert AUD.m_shape(out) == {"shots": 40, "repaired": 4, "graphics_left": 3, "graphics_removed": 3, "first_is_picture": 1}
    assert CON.p_viewer_numbers(ctx(CALM, shots=out, units=u))[0] == CON.PASS and CON.p_viewer_numbers(ctx(CALM, shots=raw, units=u))[0] == CON.FAIL
    setting("VIEWER_SEAT_ON", "FALSE"); assert AUD.shape(raw, u, {}) == raw

def test_the_promise_opens_the_video_and_the_gate_refuses_an_opening_that_does_not_show_it(setting):
    from whatifs import anim as ANIM, room as ROOM
    u = U(40); raw = shots(*(["graphic"] + ["still"] * 39))
    def placed(sh):                                                                    # what the production does next: the Animation Director, then the promise scene
        sh = [dict(s) for s in sh]; ANIM.apply(sh, u, {"kling": 4})
        return sh if any(s.get("promise") for s in sh) else ROOM.promise_shot(sh, u, THUMB)
    bad = placed(raw); s, ev = CON.p_viewer_promise({"shots": bad, "units": u, "pkg": THUMB}); assert s == CON.FAIL and "opens on a graphic" in ev
    good = placed(AUD.shape(raw, u, THUMB)); assert good[0]["type"] == "kling" and good[0].get("promise") and THUMB["thumb_prompt"] in good[0]["prompt"]
    assert CON.p_viewer_promise({"shots": good, "units": u, "pkg": THUMB}) == (CON.PASS, "the promise is on screen at 0.0 s")
    late = [dict(s) for s in good]; late[0].pop("promise"); late[3]["promise"] = True
    s, ev = CON.p_viewer_promise({"shots": late, "units": u, "pkg": THUMB}); assert s == CON.FAIL and "first shown at 12.3 s (limit 5 s)" in ev
    lost = [dict(s) for s in good]; lost[0].pop("promise")
    s, ev = CON.p_viewer_promise({"shots": lost, "units": u, "pkg": THUMB}); assert s == CON.FAIL and "none shows the thumbnail's promise" in ev
    stills = [dict(s, type="still", promise=False) for s in good]; assert CON.p_viewer_promise({"shots": stills, "units": u, "pkg": THUMB})[0] == CON.NA      # no animated scene: nothing to place
    assert CON.p_viewer_promise({})[0] == CON.NA and core.S("PROMISE_BY_SEC", int) == 5 and core.S("RUNTIME_MAX_SEC", int) == 540
    setting("VIEWER_SEAT_ON", "FALSE"); assert CON.p_viewer_promise({"shots": bad, "units": u})[0] == CON.NA

# ------------------------------------------------------------------ the voice breathes
def test_the_voice_gets_a_pause_at_a_sentence_start_and_the_writers_own_pauses_count(setting):
    from whatifs import voice as V
    assert max(u.gap_before for u in V.parse_script(LONG)) == 0
    units = AUD.breathe(V.parse_script(LONG)); idx = [i for i, u in enumerate(units) if u.gap_before >= 0.7]
    assert idx and all(units[i - 1].text.rstrip()[-1] in ".!?" for i in idx)
    est = lambda a, b: sum(len(u.text.split()) / 150 * 60 + 0.35 for u in units[a:b]); marks = [0] + idx + [len(units)]
    assert max(est(a, b) for a, b in zip(marks, marks[1:])) <= 30
    own = AUD.breathe(V.parse_script(LONG.replace("\n\n", "\n\n[pause:short] ")))
    assert [u.gap_before for u in own if u.new_para] == [0.6] * 5 and len([u for u in own if u.gap_before >= 0.7]) < len(idx)        # the writer's pauses count: fewer are added
    setting("VIEWER_SEAT_ON", "FALSE"); assert max(u.gap_before for u in AUD.breathe(V.parse_script(LONG))) == 0

def test_the_voice_is_judged_on_its_real_timeline(setting):
    tight = U(20); s, ev = CON.p_viewer_breath({"units": tight}); assert s == CON.FAIL and "the voice runs 82 s without a pause of 0.6 s (limit 38 s)" in ev
    airy = U(20)
    for k in (6, 12, 18):
        for x in airy[k:]: x["start"] = round(x["start"] + 0.7, 2); x["end"] = round(x["end"] + 0.7, 2)
    s, ev = CON.p_viewer_breath({"units": airy}); assert s == CON.PASS and "3 pauses" in ev and "105 words a minute" in ev
    assert CON.p_viewer_breath({"units": [{"text": "no times"}]})[0] == CON.NA and CON.p_viewer_breath({})[0] == CON.NA
    setting("BREATH_EVERY_S", "15"); assert CON.p_viewer_breath({"units": airy})[0] == CON.FAIL
    setting("VIEWER_SEAT_ON", "FALSE"); assert CON.p_viewer_breath({"units": tight})[0] == CON.NA

def test_the_real_voice_job_places_the_pauses_and_without_the_call_the_gate_sees_it(monkeypatch, tmp_path):
    from whatifs import voice as V
    from tools.rehearsal import ToneVoice
    one = LONG.replace("\n\n", " ")                                                   # one paragraph, no pause asked for: 3 minutes of unbroken speech
    def timeline(tag):
        r = V.narrate(one, V.Blend("T", {"af_heart": 1.0}), str(tmp_path / tag), seed="t", backend=ToneVoice())
        return json.load(open(r.timeline_path))["units"]
    s, ev = CON.p_viewer_breath({"units": timeline("a")}); assert s == CON.PASS, ev
    monkeypatch.setattr(AUD, "breathe", lambda units: units)                           # the call removed from the voice job
    s, ev = CON.p_viewer_breath({"units": timeline("b")}); assert s == CON.FAIL and "without a pause" in ev

# ------------------------------------------------------------------ wiring, levers, the one-time move
def test_the_audience_department_is_wired_and_its_levers_are_ruled():
    assert "D13" in REG.ENTRY and "D13" not in REG.PENDING and ("D13", "seat") in REG.EPISODE_RUNS["script"] and ("D13", "seat") in REG.EPISODE_RUNS["final"]
    assert not REG.entry_issues() and not REG.data_issues()
    mine = ("viewer_numbers", "viewer_breath", "viewer_promise"); stage = {f[0]: f[1] for f in CON.FEATURES}
    assert {REG.check_owner(c) for c in mine} == {"D13"} and all(stage[c] == "script" for c in mine)
    assert not set(mine) & set(RND.ORG_CHECKS) and set(mine) <= set(RND.metrics())                       # promises about the show: researchable, usable as prediction metrics
    for k in ("NUMBERS_PER_MIN_MAX", "GRAPHICS_MAX_LONG", "GRAPHICS_FREE_SEC", "BREATH_EVERY_S"): assert REG.may_change("D13", k) and k in LV.LEVERS, k
    assert LV.LEVERS["NUMBERS_PER_MIN_MAX"]["owner"] == "up" and LV.LEVERS["GRAPHICS_FREE_SEC"]["owner"] == "down" and LV.LEVERS["BREATH_EVERY_S"]["owner"] == "up"
    assert "viewer_promise" in LV.LEVERS["PROMISE_BY_SEC"]["checks"] and not REG.may_change("D13", "PROMISE_BY_SEC")
    assert "whatifs/org/audience.py" in open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read()

def test_the_two_changed_defaults_move_once_on_a_live_sheet_and_a_typed_value_is_kept(setting):
    from whatifs import manage as MG
    st = core.store(); setting("RUNTIME_MAX_SEC", "600"); setting("PROMISE_BY_SEC", "45")
    assert MG.v12v1_upgrade(st) == ["RUNTIME_MAX_SEC"] and core.S("RUNTIME_MAX_SEC", int) == 540 and core.S("PROMISE_BY_SEC", int) == 45
    setting("RUNTIME_MAX_SEC", "600"); assert MG.v12v1_upgrade(st) == [] and core.S("RUNTIME_MAX_SEC", int) == 600                # never twice

# ------------------------------------------------------------------ the real production
def test_the_real_production_runs_the_seat_before_pictures_and_holds_a_number_flood(monkeypatch):
    from whatifs import episode as EP, manage as MG
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    slot = lambda h: (now() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = EP.produce(slot(10), episode_id="EP209901010900"); ep = r.get("episode"); assert r.get("ok"), r
    st = core.store(); led = {x["feature"]: (x["status"], x["evidence"]) for x in st.rows("Feature_Ledger") if x["episode_id"] == ep}
    assert led["viewer_promise"][0] == "PASS" and led["viewer_numbers"][0] == "PASS" and led["viewer_breath"][0] == "PASS", {k: led[k] for k in led if k.startswith("viewer")}
    assert led["dept_contract"][0] == "PASS" and led["promise_paid"][0] in ("PASS", "NA")
    seat = [s for s in st.rows("Sessions") if s["episode_id"] == ep and s["dept"] == "D13"]
    assert [s["status"] for s in seat] == ["ok"] and RUN.verify(seat[0]) == [] and [t for t in st.rows("Takeaways") if t["episode_id"] == ep and t["dept"] == "D13"]
    monkeypatch.setattr(AUD, "count_numbers", lambda text: 999)                        # every line a statistic, and the one rewrite does not cure it
    r2 = EP.produce(slot(34), episode_id="EP209901020900"); assert r2.get("held") and "contract:viewer_numbers" in r2["problems"], r2
    assert not any(s["dept"] == "D9" and s["episode_id"] == r2["episode"] for s in st.rows("Sessions"))        # held before any picture was paid: nothing made, nothing uploaded
