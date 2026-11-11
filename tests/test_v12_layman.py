"""v12 V1b - the layman test (Audience, D13): a budget for the expert words a first-time viewer would not know, and the promise line-up (do the
first 30 seconds say what the video is about?). Every rule is proven both ways; the real production is run, so an unwired call is seen."""
import datetime as dt, json, os
import pytest
from whatifs import core, contract as CON, models as M, fakes as FK
from whatifs.growth import _stems
from whatifs.org import layman as LAY, registry as REG, levers as LV, runner as RUN, rnd as RND, memos as MEM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()
def ctx(text, **k): return dict({"room": {"script": {"script": text}}}, **k)
def hw(text, exempt=""): return [w for w, _s, _k in LAY.hard_words(text, exempt)]
JARGON = "This system works because of AI integration through motion scaling and tremor reduction."                  # the two versions the Ohio State
PLAIN = "This system works because of programming that makes the robot's movements more precise and less shaky."     # study gave its readers (2020)
CALM = "You stop brushing. Your reflection does not. It waits, then it follows you. "
EXPERT = ("photon", "entropy", "wavelength", "refraction", "isotope", "neutrino", "amplitude", "oscillation", "diffraction", "interferometer")
FLOOD = " ".join(f"The {w} changes everything here." for w in EXPERT) + " " + CALM * 4
TITLE = "What If Your Reflection Was One Second Late?"
GOOD = "You stop brushing your teeth. Your reflection does not. It is one second late, and it is looking straight at you."
VAGUE = "You wake up. Something is off. You cannot say what it is. The room looks the same as it did last night."
def U(opening): return [{"start": 0.0, "end": 9.0, "text": opening}, {"start": 41.0, "end": 45.0, "text": "By noon the whole town has noticed."}]

# ------------------------------------------------------------------ the measure
def test_expert_words_are_counted_the_way_a_layman_hears_them():
    assert hw(PLAIN) == [] and hw(JARGON) == []          # a LIMIT, stated: the study's sentence uses engineering words ("integration", "reduction") that code cannot recognise as expert
    assert hw("The photon leaves the mirror. Its wavelength stretches and the refraction bends it.") == ["photon", "wavelength", "refraction"]
    assert hw("Electromagnetism, thermodynamics and a spectrometer walk into your kitchen.") == ["electromagnetism", "thermodynamics", "spectrometer"]     # built like expert words
    assert hw("You take a photograph of the thermometer and the television with your telephone.") == []             # built like them, but everyday
    assert hw("You observe the coastline for one precious session.") == []                                           # the four ordinary words that held a test episode in the V1b sweep
    assert hw("You walk to the bathroom mirror and your reflection is impossibly, beautifully late.") == []          # everyday long words and their plain endings
    assert hw("Then Inspector Vale and Doctor Grimmsworth arrive from Massachusetts.") == []                         # names are not vocabulary
    assert hw("## BEAT 2 - THE ELECTROMAGNETISM\n[tension] DIRECTOR: You hear it.") == []                             # headings and speaker labels are never spoken
    assert hw("The entanglement is real.") == ["entanglement"] and hw("The entanglement is real.", "What If Entanglement Reached Your Kitchen?") == []   # the title's words: the viewer chose them
    assert LAY.unfamiliar("photons") and LAY.unfamiliar("Isotopes") and not LAY.unfamiliar("reflections") and not LAY.unfamiliar("unbelievable")

def test_viewer_plain_holds_a_flood_an_expert_opening_and_a_pile_in_one_sentence(setting):
    assert CON.p_viewer_plain(ctx(CALM * 20))[0] == CON.PASS and CON.p_viewer_plain(ctx(""))[0] == CON.FAIL
    s, ev = CON.p_viewer_plain(ctx(FLOOD)); assert s == CON.FAIL and "10 expert words a layman would not know" in ev and "(limit 2)" in ev and "in the first 30 s" in ev
    two = "The photon hits the isotope. " + CALM * 30
    s, ev = CON.p_viewer_plain(ctx(two)); assert s == CON.FAIL and "2 of them in the first 30 s (limit 1): photon, isotope" in ev and "expert words a layman" not in ev
    setting("PLAIN_OPENING_HARD_MAX", "2"); assert CON.p_viewer_plain(ctx(two))[0] == CON.PASS; setting("PLAIN_OPENING_HARD_MAX", "1")
    pile = CALM * 30 + "The photon and the isotope and the neutrino collide."
    s, ev = CON.p_viewer_plain(ctx(pile)); assert s == CON.FAIL and ev.startswith("3 in one sentence (limit 2)")
    setting("PLAIN_HARD_PER_SENTENCE_MAX", "3"); s, ev = CON.p_viewer_plain(ctx(pile)); assert s == CON.PASS and "3 expert word(s)" in ev and "sentences: median" in ev
    assert CON.p_viewer_plain(ctx(FLOOD, pkg={"titles": ["What If A Photon Met Entropy?"]}))[1].startswith("8 expert words")       # the title's own words are not counted
    setting("LAYMAN_ON", "FALSE"); assert CON.p_viewer_plain(ctx(FLOOD))[0] == CON.NA and LAY.plain_issues(FLOOD) == []

def test_the_writers_one_mandatory_fix_carries_the_expert_words(monkeypatch):
    from whatifs import enforce as ENF
    assert LAY.plain_issues(CALM * 20) == [] and "EXPERT WORDS" in LAY.plain_issues(FLOOD)[0] and "photon" in LAY.plain_issues(FLOOD)[0]
    seen = []
    monkeypatch.setattr(M, "ask", lambda role, system, prompt, **k: seen.append(prompt) or {"script": CALM * 20})
    out, issues = ENF.fix_all({"script": FLOOD}, "brief", {"promise": {"title": "your mirror is late"}}, "EPT")
    assert out["script"] == CALM * 20 and any("EXPERT WORDS" in i for i in issues) and "PLAIN WORDS FIX" in seen[0] and len(seen) == 1

# ------------------------------------------------------------------ the promise line-up
def test_the_line_up_hides_our_title_among_titles_of_our_kind_and_plants_a_foreign_opening():
    a = LAY.lineup("S-1", TITLE); assert a == LAY.lineup("S-1", TITLE) and a["options"][a["correct"]] == TITLE and len(a["options"]) == 4
    assert "What If Your Shadow Arrived One Second Late?" not in a["options"].values()                               # a decoy that shares our words is left out
    assert len({LAY.lineup(f"S-{i}", TITLE)["correct"] for i in range(60)}) == 4 and len({LAY.lineup(f"S-{i}", TITLE)["real_first"] for i in range(60)}) == 2
    for f in LAY.FOREIGN:
        for d in LAY.DECOYS: assert not (_stems(f) & _stems(d)), (f[:40], d)                                       # a planted opening belongs to NO title in any line-up
    assert a["foreign"] in LAY.FOREIGN and not (_stems(a["foreign"]) & _stems(TITLE))

def test_the_readers_must_pick_our_title_from_the_first_30_seconds_alone(setting):
    r = LAY.probe("S-7", TITLE, U(GOOD)); assert r["status"] == "pass" and r["picks"] == {"claude": r["correct"], "gemini": r["correct"]} and set(r["canary"].values()) == {"E"}
    assert CON.p_viewer_probe({"probe": r})[0] == CON.PASS
    late = LAY.probe("S-7", TITLE, [{"start": 0.0, "end": 9.0, "text": VAGUE}, {"start": 31.0, "end": 40.0, "text": GOOD}])     # the promise is named - after the first 30 seconds
    assert late["status"] == "fail" and "could not tell" in late["why"]
    s, ev = CON.p_viewer_probe({"probe": late}); assert s == CON.FAIL and "from the first 30 s alone" in ev
    assert LAY.probe("S-7", "", U(GOOD))["status"] == "na" and CON.p_viewer_probe({})[0] == CON.NA
    setting("LAYMAN_PROBE_ON", "FALSE"); assert LAY.probe("S-7", TITLE, U(GOOD))["status"] == "off" and CON.p_viewer_probe({"probe": late})[0] == CON.NA

def test_a_reader_that_guesses_or_comes_from_the_wrong_family_makes_the_session_void(monkeypatch):
    monkeypatch.setattr(FK, "_fake_probe", lambda prompt: json.dumps({"X": "B", "Y": "B", "X_says": "x", "Y_says": "y"}))     # a reader that always names a title
    r = LAY.probe("S-7", TITLE, U(GOOD)); assert r["status"] == "void" and "planted opening was given a title" in r["why"]
    s, ev = CON.p_viewer_probe({"probe": r}); assert s == CON.NA and "void" in ev
    monkeypatch.undo()
    monkeypatch.setattr(M, "last_call", lambda: {"provider": "gemini", "role": "gem_flash", "model": "fake-flash"})            # the second reader was answered by the first family
    r = LAY.probe("S-7", TITLE, U(GOOD)); assert r["status"] == "void" and "only 1 model family answered" in r["why"] and "not counted" in r["why"]
    monkeypatch.undo()
    monkeypatch.setattr(FK, "_fake_probe", lambda prompt: json.dumps({"X": "see above", "Y": 7}))                              # no readable letters
    assert LAY.probe("S-7", TITLE, U(GOOD))["status"] == "void"

def test_a_void_line_up_is_reported_by_the_department_and_closed_by_the_next_valid_one(monkeypatch):
    from whatifs import manage as MG
    MG.setup(); st = core.store()
    run = lambda ep: RUN.work("D13", "probe", ep, lambda b: LAY.probe_run(b, TITLE, U(GOOD), GOOD, ep))
    mine = lambda: [m for m in MEM.find(st, type="problem_memo", from_dept="D13") if str(m.get("dedupe_key") or "").startswith("probe|void")]
    real = FK._fake_probe
    monkeypatch.setattr(FK, "_fake_probe", lambda prompt: json.dumps({"X": "A", "Y": "A"}))
    r = run("EPV1"); assert r["status"] == "void" and len(mine()) == 1
    monkeypatch.setattr(FK, "_fake_probe", real)
    r2 = run("EPV2"); assert r2["status"] == "pass" and mine() == []
    ses = [s for s in st.rows("Sessions") if s["dept"] == "D13" and s["trigger"] == "probe"]
    assert len(ses) == 2 and all(s["status"] == "ok" and RUN.verify(s) == [] for s in ses)

# ------------------------------------------------------------------ wiring
def test_the_layman_test_is_wired_and_its_levers_are_ruled():
    assert ("whatifs/episode.py", "probe") in REG.ENTRY["D13"] and ("D13", "probe") in REG.EPISODE_RUNS["script"] and ("D13", "probe") in REG.EPISODE_RUNS["final"]
    assert not REG.entry_issues() and not REG.data_issues()
    mine = ("viewer_plain", "viewer_probe"); stage = {f[0]: f[1] for f in CON.FEATURES}
    assert {REG.check_owner(c) for c in mine} == {"D13"} and all(stage[c] == "script" for c in mine)
    assert not set(mine) & set(RND.ORG_CHECKS) and set(mine) <= set(RND.metrics())                       # promises about the show
    for k in ("PLAIN_HARD_PER_MIN_MAX", "PLAIN_OPENING_HARD_MAX", "PLAIN_HARD_PER_SENTENCE_MAX"):
        assert REG.may_change("D13", k) and LV.LEVERS[k]["owner"] == "up" and LV.LEVERS[k]["checks"] == ("viewer_plain",), k
    assert M.route("probe_gemini")[0] == "flash" and M.route("probe_claude")[0] == "haiku"
    assert "whatifs/org/layman.py" in open(os.path.join(ROOT, "tools", "repair.py"), encoding="utf-8").read()
    assert len(LAY.everyday()) > 1200 and not LAY.everyday() & LAY.EXPERT

# ------------------------------------------------------------------ the real production
def test_the_real_production_runs_the_layman_test_before_pictures_and_holds_what_a_layman_cannot_follow(monkeypatch):
    from whatifs import episode as EP, manage as MG
    from tools.rehearsal import ToneVoice
    import whatifs.voice as V
    monkeypatch.setattr(V, "KokoroBackend", lambda blend: ToneVoice()); MG.setup(); core.set_setting("VOICE", "C")
    slot = lambda h: (now() + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = EP.produce(slot(10), episode_id="EP209901010900"); ep = r.get("episode"); assert r.get("ok"), r
    st = core.store(); led = {x["feature"]: (x["status"], x["evidence"]) for x in st.rows("Feature_Ledger") if x["episode_id"] == ep}
    assert led["viewer_plain"][0] == "PASS" and led["viewer_probe"][0] == "PASS", {k: led[k] for k in led if k.startswith("viewer")}
    assert led["dept_contract"][0] == "PASS"
    mine = [s for s in st.rows("Sessions") if s["episode_id"] == ep and s["dept"] == "D13"]
    assert sorted(s["trigger"] for s in mine) == ["probe", "seat"] and all(s["status"] == "ok" and RUN.verify(s) == [] for s in mine)
    monkeypatch.setattr(LAY, "unfamiliar", lambda w: len(str(w)) >= 5)                 # every longer word is an expert word, and the one rewrite does not cure it
    monkeypatch.setattr(LAY, "_open_text", lambda units, text="": VAGUE)               # and the opening never says what the video is about
    r2 = EP.produce(slot(34), episode_id="EP209901020900")
    assert r2.get("held") and "contract:viewer_plain" in r2["problems"] and "contract:viewer_probe" in r2["problems"], r2
    assert not any(s["dept"] == "D9" and s["episode_id"] == r2["episode"] for s in st.rows("Sessions"))        # held before any picture was paid
