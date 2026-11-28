"""v12 F318 - a low-scored character master is remade before it can lock (triage 318, R1-104 (3)). The real `masters`, `decide` and `auto_lock`
run; only the paid or outside calls are stubbed: the picture maker, the upload, the judge, the month's money, the dispatch. No clock, no randomness."""
import hashlib, json, os
import pytest
from whatifs import core, sheets as SH

H = "hF318GRIMMmaster"
DAY_OLD = "2020-01-01T00:00:00Z"                                    # fixed times: no test reads the clock
FRESH = "2099-01-01T00:00:00Z"
STARTED = "cleared; the sheets run that remakes it has been started (lifetime cap still applies)"
NOT_STARTED = "NOT remade: the sheets run could not be started, so GRIMM's master was kept as it was (nothing cleared)."      # CR-U1FIX_2 (4): no run, nothing cleared

def _seed_portrait(status="LOCKED"):
    """His approved neutral portrait of GRIMM (a row with a file): what the floor is judged against."""
    core.store().append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "neutral", "hash": "nF318GRIMM", "prompt": "p",
                                              "file": "drive:his", "status": status, "approved_at": ""}])

def _seed_try(k, score, rnd=0):
    core.store().append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "master", "hash": f"{H}-r{rnd}-try{k}", "prompt": "P",
                                              "file": f"drive:t{k}", "status": f"REJECTED (identity {score}/10)", "approved_at": ""}])

def _stubs(mp, setting, scores, portrait="his.png", gov=(True, ""), raise_on=None):
    """Every paid call stubbed. `scores`: one entry per picture bought in this test - a number or None (both looks answer it) or a pair
    (his portrait first, the new picture first); the last entry answers any further picture. Returns the record of every call."""
    from whatifs import anim as ANIM, specials as SP, publish as PUB, governor as GOV, builds as BLD
    rec = {"pics": [], "looks": [], "asks": [], "portraits": [], "dispatch": []}
    setting("TWO_SCREENS_ON", "TRUE")
    def pic(text, refs, path, ep, aspect="16:9"):
        rec["pics"].append((text, path))
        if raise_on is not None and len(rec["pics"]) == raise_on: raise RuntimeError("planted picture failure")
    def look(a, b, who):
        rec["looks"].append((a, b))
        s = scores[min(len(rec["pics"]), len(scores)) - 1]
        if isinstance(s, tuple): return s[0] if a == portrait else s[1]
        return s
    def port(who, workdir, episode):
        rec["portraits"].append(who); return portrait
    def ask(est, kind="extra"):
        rec["asks"].append(est); return gov
    mp.setattr(ANIM, "gemini_image", pic); mp.setattr(SP, "_portrait", port); mp.setattr(SH, "identity_score", look)
    mp.setattr(PUB, "drive_upload", lambda *a, **k: ("fidF318", "https://drive.example/x")); mp.setattr(PUB, "email", lambda subj, html, kind="essential": True)
    mp.setattr(GOV, "extras_allowed", ask)
    mp.setattr(BLD, "dispatch", lambda wf, inputs, ref="main": rec["dispatch"].append((wf, inputs)) or True)
    mp.setattr(SH, "masters_plan", lambda: [{"character": "GRIMM", "expression": "master", "prompt": "P", "retry": "Q", "hash": H}])
    return rec

def _masters_rows():
    return [r for r in core.store().rows("Character_Sheets") if r.get("expression") == "master"]

def _card():
    rows = [r for r in core.store().rows("Owner_Actions") if r["kind"] == "sheets_review"]
    return rows[-1] if rows else None

def _status(h):
    return next(r["status"] for r in core.store().rows("Character_Sheets") if r["hash"] == h)

# ------------------------------------------------------------------ steps 1, 3, 4, 5: the floor, the two looks, the round
def test_a_master_under_the_floor_is_remade_and_the_first_good_one_is_the_draft(monkeypatch, setting):
    """On the default cells: a 4 is refused (a row with its file, counted), the second picture (the retry prompt) scores 8 and is his draft."""
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [4, 8]); before = SH.used()
    assert SH.masters()["made"] == 1
    assert [t for t, _ in rec["pics"]] == ["P", "Q"]
    rows = {r["hash"]: r for r in _masters_rows()}
    assert set(rows) == {f"{H}-r0-try0", H}, rows
    assert rows[f"{H}-r0-try0"]["status"] == "REJECTED (identity 4/10)" and rows[f"{H}-r0-try0"]["file"] == "drive:fidF318"
    assert rows[H]["status"] == "DRAFT (identity 8/10)" and rows[H]["prompt"] == "Q"
    assert SH.used() == before + 2                                    # both pictures count against the lifetime cap
    n = len(rec["pics"]); assert SH.masters()["made"] == 0 and len(rec["pics"]) == n      # a second run buys nothing

def test_a_score_at_the_floor_or_no_score_buys_nothing_more(monkeypatch, setting):
    """7.0 and 6.6 (said and compared as 7) stand; a judge that gives no score and a character with no portrait buy no remake."""
    for i, (sc, portrait, status) in enumerate(((7.0, "his.png", "DRAFT (identity 7/10)"), (6.6, "his.png", "DRAFT (identity 7/10)"),
                                                (None, "his.png", "DRAFT"), (3.0, None, "DRAFT"))):
        core.store().d["Character_Sheets"] = []; _seed_portrait()
        rec = _stubs(monkeypatch, setting, [sc], portrait=portrait)
        assert SH.masters()["made"] == 1, i
        assert len(rec["pics"]) == 1 and rec["asks"] == [], (i, rec)
        assert [r["status"] for r in _masters_rows()] == [status], (i, _masters_rows())

def test_the_judge_looks_both_ways_and_the_lower_answer_counts(monkeypatch, setting):
    asked = []
    def judge(answers):
        def f(a, b, who): asked.append((a, b)); return answers[(a, b)]
        return f
    monkeypatch.setattr(SH, "identity_score", judge({("his", "new"): 9.0, ("new", "his"): 5.0}))
    assert SH.master_score("his", "new", "GRIMM") == 5.0 and asked == [("his", "new"), ("new", "his")]
    monkeypatch.setattr(SH, "identity_score", judge({("his", "new"): None, ("new", "his"): 6.0})); assert SH.master_score("his", "new", "GRIMM") == 6.0
    monkeypatch.setattr(SH, "identity_score", judge({("his", "new"): 8.0, ("new", "his"): None})); assert SH.master_score("his", "new", "GRIMM") == 8.0
    monkeypatch.setattr(SH, "identity_score", judge({("his", "new"): None, ("new", "his"): None})); assert SH.master_score("his", "new", "GRIMM") is None
    _seed_portrait(); _stubs(monkeypatch, setting, [(9.0, 5.0)])           # in `masters` a picture that is 9 one way and 5 the other is refused
    SH.masters()                                                            # refused three times; the first of the equal 5s stands
    assert {r["hash"]: r["status"] for r in _masters_rows()} == {H: "DRAFT (identity 5/10)", f"{H}-r0-try1": "REJECTED (identity 5/10)", f"{H}-r0-try2": "REJECTED (identity 5/10)"}

# ------------------------------------------------------------------ steps 5, 6, 7: the last remake, the best attempt, the card
def test_after_the_last_remake_the_best_attempt_stands_and_the_card_says_so(monkeypatch, setting):
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3, 6, 5])
    assert SH.masters()["made"] == 1
    assert [t for t, _ in rec["pics"]] == ["P", "Q", "P"] and len({p for _, p in rec["pics"]}) == 3
    rows = {r["hash"]: r for r in _masters_rows()}
    assert set(rows) == {f"{H}-r0-try0", f"{H}-r0-try2", H}, rows
    assert rows[H]["status"] == "DRAFT (identity 6/10)" and rows[H]["prompt"] == "Q"
    assert rows[f"{H}-r0-try0"]["status"] == "REJECTED (identity 3/10)" and rows[f"{H}-r0-try2"]["status"] == "REJECTED (identity 5/10)"
    card = _card()
    assert ("Still under 7/10 after every allowed try: GRIMM (3 picture(s), no remake left). The best one is shown. Tap Remake to try again; "
            "left alone, they lock by themselves.") in card["text"], card["text"]
    assert json.loads(card["buttons"]) == [["Remake GRIMM", "REDO SHEET GRIMM master"], ["Approve GRIMM", "APPROVE SHEET GRIMM"]]
    assert "Identity against your portrait: GRIMM 6/10." in card["text"] and "no spare picture is left" not in card["text"]      # the default cap leaves a spare
    n = len(rec["pics"]); assert SH.masters()["made"] == 0 and len(rec["pics"]) == n
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait()
    _stubs(monkeypatch, setting, [3, 3, 3]); SH.masters()               # equals: the earliest stands
    rows = {r["hash"]: r for r in _masters_rows()}
    assert set(rows) == {f"{H}-r0-try1", f"{H}-r0-try2", H} and rows[H]["prompt"] == "P", rows

def test_a_remake_is_bought_only_from_the_lifetime_caps_spare(monkeypatch, setting):
    """Every score 3. The cap leaves no spare beyond what the plan still owes: no remake; one spare: exactly one; the cap full: no picture."""
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3])
    setting("CHARACTER_SHEET_IMAGE_CAP", str(SH.used() + SH.sheets_owed()))
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1
    assert [r["status"] for r in _masters_rows()] == ["DRAFT (identity 3/10)"]
    assert "GRIMM (1 picture(s), no spare picture inside the lifetime cap)" in _card()["text"], _card()["text"]
    assert "Tap Remake to try again (no spare picture is left: a remake takes one from the expression sheets); left alone," in _card()["text"], _card()["text"]
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, [3])
    setting("CHARACTER_SHEET_IMAGE_CAP", str(SH.used() + SH.sheets_owed() + 1))
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 2
    assert SH.used() + SH.sheets_owed() <= core.S("CHARACTER_SHEET_IMAGE_CAP", int)
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, [3])
    setting("CHARACTER_SHEET_IMAGE_CAP", str(SH.used()))
    assert SH.masters()["made"] == 0 and rec["pics"] == [] and _masters_rows() == [] and _card() is None
    assert rec["portraits"] == []                                      # the cap is asked BEFORE the portrait (it can draw a paid picture), as at S0
    core.store().d["Character_Sheets"] = []
    monkeypatch.setattr(SH, "plan", lambda characters=None: [{"character": "GRIMM", "expression": e, "prompt": e, "hash": "s" + e} for e in ("smug", "stern", "shocked")])
    core.store().append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "smug", "hash": "ssmug", "prompt": "smug", "file": "", "status": "DRAFT", "approved_at": ""},
                                             {"ts": FRESH, "character": "GRIMM", "expression": "stern", "hash": "sstern", "prompt": "stern", "file": "drive:s", "status": "DRAFT", "approved_at": ""}])
    assert SH.sheets_owed() == 3                                       # the master and two sheets: a row with no file is still owed, a made one is not

def test_a_remake_asks_the_months_money_first(monkeypatch, setting):
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3], gov=(False, "growth allowance used"))
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1
    assert rec["asks"] == [core.S("PRICE_GEM_IMAGE_USD", float) * core.S("USD_INR", float)] and abs(rec["asks"][0] - 6.633) < 1e-9
    assert "GRIMM (1 picture(s), no money room this month)" in _card()["text"], _card()["text"]
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, [3])
    SH.masters()
    assert len(rec["pics"]) == 3 and len(rec["asks"]) == 2              # asked before each remake, never for the first picture

def test_with_the_switch_off_or_no_remakes_it_is_one_picture(monkeypatch, setting):
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3]); setting("MASTER_FLOOR_ON", "FALSE")
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1 and rec["looks"] == [("his.png", rec["pics"][0][1])] and rec["asks"] == []
    assert [r["status"] for r in _masters_rows()] == ["DRAFT (identity 3/10)"]
    card = _card()
    assert "Still under" not in card["text"] and json.loads(card["buttons"]) == [["Approve GRIMM", "APPROVE SHEET GRIMM"]]
    assert SH.decide("REDO SHEET GRIMM master") == "cleared; the next sheets run remakes it (lifetime cap still applies)" and rec["dispatch"] == []
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, [3])
    setting("MASTER_FLOOR_ON", "TRUE"); setting("MASTER_REMAKES_MAX", "0")
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1 and rec["asks"] == []
    assert [r["status"] for r in _masters_rows()] == ["DRAFT (identity 3/10)"]
    assert "GRIMM (1 picture(s), no remake left)" in _card()["text"], _card()["text"]

def test_a_run_that_died_picks_up_its_round_and_pays_nothing_twice(monkeypatch, setting):
    _seed_portrait(); _seed_try(0, 3); _seed_try(1, 4); rec = _stubs(monkeypatch, setting, [5])
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1 and rec["pics"][0][1].endswith(f"{H}-2.png")
    assert {r["hash"]: r["status"] for r in _masters_rows()} == {f"{H}-r0-try0": "REJECTED (identity 3/10)", f"{H}-r0-try1": "REJECTED (identity 4/10)", H: "DRAFT (identity 5/10)"}
    core.store().d["Character_Sheets"] = []; _seed_portrait(); _seed_try(0, 3); _seed_try(1, 6); _seed_try(2, 5); rec = _stubs(monkeypatch, setting, [9])
    assert SH.masters()["made"] == 1 and rec["pics"] == [] and _status(H) == "DRAFT (identity 6/10)"
    core.store().d["Character_Sheets"] = []; _seed_portrait(); _seed_try(0, 4); rec = _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "FALSE")
    assert SH.masters()["made"] == 1 and rec["pics"] == [] and _status(H) == "DRAFT (identity 4/10)"

# ------------------------------------------------------------------ step 8: his Remake tap
def test_his_remake_tap_clears_the_live_master_and_starts_the_run(monkeypatch, setting):
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3, 3, 5])
    st = core.store()
    st.append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "master", "hash": f"{H}-redo-2026-11-01T00:00", "prompt": "old", "file": "drive:o", "status": "REDO", "approved_at": ""}])
    _seed_try(0, 3, rnd=1)
    st.append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "master", "hash": H, "prompt": "Q", "file": "drive:live", "status": "DRAFT (identity 6/10)", "approved_at": ""}])
    _seed_try(2, 5, rnd=1)
    assert SH.decide("REDO SHEET GRIMM master") == "cleared; the sheets run that remakes it has been started (lifetime cap still applies)"
    st_by_file = {r["file"]: r for r in _masters_rows()}
    assert st_by_file["drive:live"]["status"] == "REDO" and st_by_file["drive:live"]["hash"].startswith(H + "-redo-")
    assert [r["status"] for r in _masters_rows() if r["file"] != "drive:live"] == ["REDO", "REJECTED (identity 3/10)", "REJECTED (identity 5/10)"]
    assert rec["dispatch"] == [("sheets.yml", {})]
    assert SH.decide("REDO SHEET GRIMM master") == "no such image" and rec["dispatch"] == [("sheets.yml", {})]      # a second tap finds no live row
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 3                                  # a fresh round: three pictures again
    assert {f"{H}-r2-try0", f"{H}-r2-try1", H} <= {r["hash"] for r in _masters_rows()} and _status(H) == "DRAFT (identity 5/10)"      # two REDO rows = round 2
    from whatifs import builds as BLD
    monkeypatch.setattr(BLD, "dispatch", lambda *a, **k: False)      # GitHub refused: no next run comes (sheets.yml is never scheduled) - CR-U1FIX_2 (4): said so, nothing cleared
    assert SH.decide("REDO SHEET GRIMM master") == NOT_STARTED and _status(H) == "DRAFT (identity 5/10)"

# ------------------------------------------------------------------ the readers: a refused attempt is inert
def test_a_refused_attempt_is_never_locked_shown_or_used_and_is_counted(monkeypatch, setting):
    from whatifs import dash as DS
    setting("TWO_SCREENS_ON", "TRUE")
    st = core.store()
    st.append("Character_Sheets", [{"ts": DAY_OLD, "character": "GRIMM", "expression": "master", "hash": f"{H}-r0-try0", "prompt": "P", "file": "drive:t0", "status": "REJECTED (identity 3/10)", "approved_at": ""}])
    n = SH.used()
    assert SH.auto_lock() == 0 and SH.decide("APPROVE SHEET GRIMM") == "0 image(s) locked"
    DS.route("LOCKSHEETS|GRIMM")
    assert _status(f"{H}-r0-try0") == "REJECTED (identity 3/10)"
    assert SH.locked_portraits() == {} and "sheets-GRIMM" not in {c["id"] for c in DS._docket()}
    assert n == 1

def test_no_floor_against_a_portrait_he_never_locked(monkeypatch, setting):
    _seed_portrait(status="DRAFT"); rec = _stubs(monkeypatch, setting, [3])
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 1 and len(rec["looks"]) == 1 and rec["asks"] == []
    assert [r["status"] for r in _masters_rows()] == ["DRAFT (identity 3/10)"]
    assert rec["portraits"] == ["GRIMM"]
    for case in ([3, 6, 5], [3], [8]):                                 # judged runs too: the portrait is fetched once per character, never per attempt
        core.store().d["Character_Sheets"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, case); SH.masters()
        assert rec["portraits"] == ["GRIMM"], (case, rec["portraits"])

def test_a_failed_remake_keeps_the_best_so_far(monkeypatch, setting):
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3], raise_on=2)
    assert SH.masters()["made"] == 1 and len(rec["pics"]) == 2
    assert {r["hash"]: r["status"] for r in _masters_rows()} == {H: "DRAFT (identity 3/10)"}
    assert "GRIMM (1 picture(s), a remake failed)" in _card()["text"], _card()["text"]
    core.store().d["Character_Sheets"] = []; core.store().d["Owner_Actions"] = []; _seed_portrait(); rec = _stubs(monkeypatch, setting, [3], raise_on=1)
    assert SH.masters()["made"] == 0 and len(rec["pics"]) == 1 and _masters_rows() == [] and _card() is None

# ------------------------------------------------------------------ steps 2, 1, 6: the retry prompt, the cells, the old silence rule
def test_the_retry_prompt_is_the_face_from_the_reference_and_the_hash_is_unmoved():
    from whatifs import anim as ANIM
    from tests.test_v102 import INVENTED
    for p in SH.masters_plan():
        assert p["hash"] == hashlib.sha256(p["prompt"].encode()).hexdigest()[:16]
        q = p["retry"]
        assert q.startswith(p["prompt"].split("Same person as the reference image")[0])
        assert "Take the face, hair, age and costume from the reference image exactly; change only the rendering style." in q and q.endswith(ANIM.style_lock())
        assert ANIM.char_lock(p["character"]) not in q and not [w for w in INVENTED if w in q.lower()]

def test_the_floor_cells_and_their_defaults():
    assert {k: core.DEFAULTS[k][0] for k in ("MASTER_FLOOR_ON", "MASTER_MIN_IDENTITY", "MASTER_REMAKES_MAX")} == {"MASTER_FLOOR_ON": "TRUE", "MASTER_MIN_IDENTITY": "7", "MASTER_REMAKES_MAX": "2"}
    assert core.DEFAULTS["MASTER_MIN_IDENTITY"][0] == core.DEFAULTS["LIVING_MIN_IDENTITY"][0]
    mx = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "CURRENT", "ENFORCEMENT_MATRIX.md"), encoding="utf-8").read()
    assert "\n| A LOW-SCORED CHARACTER MASTER IS REMADE BEFORE IT CAN LOCK (F318; triage 318, R1-104 (3)):" in mx      # step 10: the matrix row

def test_the_best_attempt_still_locks_by_his_silence(monkeypatch, setting):
    _seed_portrait(); _seed_try(0, 3); _seed_try(1, 4); _seed_try(2, 5); _stubs(monkeypatch, setting, [9])
    SH.masters(); assert _status(H) == "DRAFT (identity 5/10)"
    core.store().update_where("Character_Sheets", {"hash": H}, {"ts": DAY_OLD})
    assert SH.auto_lock() >= 1 and _status(H) == "LOCKED"

# ------------------------------------------------------------------ step 8b: the dashboard says the same fact and its Redo is the same tap
def test_the_dashboard_says_a_low_master_and_its_redo_remakes_it(monkeypatch, setting):
    from whatifs import dash as DS, builds as BLD
    setting("TWO_SCREENS_ON", "TRUE"); sent = []
    monkeypatch.setattr(BLD, "dispatch", lambda wf, inputs, ref="main": sent.append((wf, inputs)) or True)
    why0 = "Locked portraits let this character appear on thumbnails and in scenes, always the same face."
    def only(status, expression="master"):
        core.store().d["Character_Sheets"] = []
        core.store().append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": expression, "hash": H, "prompt": "P", "file": "drive:m", "status": status, "approved_at": ""}])
    def why():
        return next(c["why"] for c in DS._docket() if c["id"] == "sheets-GRIMM")
    only("DRAFT (identity 6/10)")
    assert why() == why0 + " The judge scored this master 6/10 against your portrait, under 7/10: Redo remakes it.", why()
    for status in ("DRAFT (identity 7/10)", "DRAFT"):
        only(status); assert why() == why0, (status, why())
    only("DRAFT (identity 6/10)")
    ok, said = DS.route("REDOSHEETS|GRIMM")
    assert ok is True and "has been started" in said, said
    assert [r["status"] for r in _masters_rows()] == ["REDO"] and sent == [("sheets.yml", {})]
    pointer = (False, "Redo one expression with the email link 'REDO SHEET <NAME> <expression>' (lifetime image cap applies)")
    for status, expression, on in (("DRAFT", "smug", "TRUE"), ("LOCKED", "master", "TRUE"), ("DRAFT (identity 6/10)", "master", "FALSE")):
        only(status, expression); setting("MASTER_FLOOR_ON", on)
        before = [dict(r) for r in core.store().rows("Character_Sheets")]
        assert DS.route("REDOSHEETS|GRIMM") == pointer, (status, expression, on)
        assert [dict(r) for r in core.store().rows("Character_Sheets")] == before and sent == [("sheets.yml", {})], (status, expression, on)
    assert why() == why0                                                # the switch off: the S0 words

# ------------------------------------------------------------------ step 5 (review change 3): the paid loop ends by its own count
def test_a_round_ends_by_its_own_count_when_the_tab_does_not_show_the_new_rows(monkeypatch, setting):
    """A tab read that never shows the rows just written must not keep the paid loop going: MASTER_REMAKES_MAX + 1 pictures, never a fourth."""
    _seed_portrait(); rec = _stubs(monkeypatch, setting, [3]); monkeypatch.setattr(SH, "master_tries", lambda h, rows: [])
    SH.masters()
    assert len(rec["pics"]) == core.S("MASTER_REMAKES_MAX", int) + 1 == 3, rec["pics"]

# ------------------------------------------------------------------ code review U1FIX-b (4, 5): only the master's Remake starts the run; the dashboard reads the answer
def test_a_redo_of_an_expression_sheet_starts_the_run_as_the_masters_remake_does(monkeypatch, setting):
    """RUL-U3k U1-2: with MASTER_FLOOR_ON (the default) "REDO SHEET GRIMM smug" clears the live smug sheet and starts the sheets run, as the
    master's Remake does (sheets.yml is never scheduled)."""
    rec = _stubs(monkeypatch, setting, [9]); st = core.store(); assert core.S("MASTER_FLOOR_ON", bool) is True
    st.append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "smug", "hash": "hF318GRIMMsmug", "prompt": "S", "file": "drive:smug", "status": "DRAFT", "approved_at": ""}])
    assert SH.decide("REDO SHEET GRIMM smug") == STARTED and rec["dispatch"] == [("sheets.yml", {})]
    assert next(r for r in st.rows("Character_Sheets") if r["file"] == "drive:smug")["status"] == "REDO"
    st.append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "master", "hash": H, "prompt": "P", "file": "drive:m", "status": "DRAFT (identity 6/10)", "approved_at": ""}])
    assert SH.decide("REDO SHEET GRIMM master") == "cleared; the sheets run that remakes it has been started (lifetime cap still applies)" and rec["dispatch"] == [("sheets.yml", {})] * 2

def test_the_dashboards_redo_is_ok_only_when_a_live_master_was_cleared(monkeypatch, setting):
    """code review U1FIX-b (5): the dashboard's Redo on a DRAFT master is ok only when sheets.decide cleared a live row - its "no such image" is
    not ok (as UNPOST beside it reads its own answer)."""
    from whatifs import dash as DSH
    rec = _stubs(monkeypatch, setting, [9]); st = core.store(); real = SH.decide
    st.append("Character_Sheets", [{"ts": FRESH, "character": "GRIMM", "expression": "master", "hash": H, "prompt": "P", "file": "drive:m", "status": "DRAFT (identity 4/10)", "approved_at": ""}])
    monkeypatch.setattr(SH, "decide", lambda title: "no such image")
    assert DSH.route("REDOSHEETS|GRIMM") == (False, "no such image") and rec["dispatch"] == []
    monkeypatch.setattr(SH, "decide", real); ok, said = DSH.route("REDOSHEETS|GRIMM")
    assert ok is True and said == "cleared; the sheets run that remakes it has been started (lifetime cap still applies)" and rec["dispatch"] == [("sheets.yml", {})], said

# ------------------------------------------------------------------ RUL-U1h 1: two characters under the floor - four choices, Remake first, none dropped on WhatsApp
def test_a_masters_card_with_two_low_characters_keeps_all_four_choices_on_both_screens(monkeypatch, setting):
    """RUL-U1h 1: two characters end under the floor in one `masters` run -> the card keeps four buttons, Remake first; WhatsApp gets ONE list of the
    four (the card's `send_card` and the doorway `send_buttons` alike - never a button message cut to three); three choices are still three buttons;
    the dashboard holds a card per character with its own Lock and Redo."""
    from whatifs import wa as WA, dash as DS
    for who in ("A", "B"):                                              # his approved neutral portrait of each: the floor is judged against both
        core.store().append("Character_Sheets", [{"ts": FRESH, "character": who, "expression": "neutral", "hash": f"nF318{who}", "prompt": "p",
                                                  "file": f"drive:his{who}", "status": "LOCKED", "approved_at": ""}])
    _stubs(monkeypatch, setting, [3])                                   # every picture 3/10: both end under the floor after every allowed try
    monkeypatch.setattr(SH, "masters_plan", lambda: [{"character": c, "expression": "master", "prompt": "P", "retry": "Q", "hash": f"hF318{c}master"} for c in ("A", "B")])
    assert SH.masters()["made"] == 2
    four = [["Remake A", "REDO SHEET A master"], ["Remake B", "REDO SHEET B master"], ["Approve A", "APPROVE SHEET A"], ["Approve B", "APPROVE SHEET B"]]
    card = _card(); assert json.loads(card["buttons"]) == four, card["buttons"]
    sent = []; monkeypatch.setattr(WA, "_go", lambda body, kind=None, now=None: sent.append(body) or "wamid.F318")
    def rows(): return [(r["title"], r["id"]) for r in sent[-1]["interactive"]["action"]["sections"][0]["rows"]]
    WA.send_card(card["id"])
    assert len(sent) == 1 and sent[0]["interactive"]["type"] == "list" and rows() == [(t, f"ACT|{card['id']}|{i}") for i, (t, _v) in enumerate(four)], sent
    WA.send_buttons("Masters to approve", [tuple(p) for p in four])
    assert len(sent) == 2 and sent[1]["interactive"]["type"] == "list" and rows() == [tuple(p) for p in four], sent[1:]
    WA.send_buttons("Masters to approve", [tuple(p) for p in four[:3]])
    assert len(sent) == 3 and sent[2]["interactive"]["type"] == "button", sent[2:]
    assert [(b["reply"]["title"], b["reply"]["id"]) for b in sent[2]["interactive"]["action"]["buttons"]] == [tuple(p) for p in four[:3]], sent[2:]
    verbs = {c["id"]: c.get("verbs") for c in DS._docket()}
    for who in ("A", "B"):
        assert verbs.get(f"sheets-{who}") == {"Lock these": f"LOCKSHEETS|{who}", "Redo": f"REDOSHEETS|{who}"}, verbs

def test_the_masters_card_never_outgrows_a_whatsapp_list():
    """RUL-U1h 1c: at most two choices per character (Remake, Approve) and a WhatsApp list holds ten rows (wa.send_list `rows[:10]`): the planned cast
    must fit. The day it does not, this is red and the card needs a ruling (one card per character) - never a silent cut."""
    plan = SH.masters_plan()
    assert 2 * len(plan) <= 10, [p["character"] for p in plan]


# ------------------------------------------------------------------ CR-U1FIX_2 (4): a Remake whose run does not start clears nothing and says so
@pytest.mark.parametrize("how", ["refused", "raises"])
def test_a_remake_whose_run_does_not_start_says_so_and_clears_nothing(how, monkeypatch, setting):
    from whatifs import builds as BLD, dash as DSH
    _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    _masters((H, "drive:m", "DRAFT (identity 4/10)"))
    def no_run(*a, **k):
        if how == "raises": raise RuntimeError("planted: GitHub does not answer")
        return False
    monkeypatch.setattr(BLD, "dispatch", no_run)
    assert SH.decide("REDO SHEET GRIMM master") == NOT_STARTED
    assert [(r["hash"], r["status"]) for r in _masters_rows()] == [(H, "DRAFT (identity 4/10)")]
    assert DSH.route("REDOSHEETS|GRIMM") == (False, NOT_STARTED)
    assert [(r["hash"], r["status"]) for r in _masters_rows()] == [(H, "DRAFT (identity 4/10)")]


@pytest.mark.parametrize("how", ["refused", "raises"])
def test_an_expression_remake_whose_run_does_not_start_puts_the_locked_image_back(how, monkeypatch, setting):
    """RUL-U3k U1-2: an expression's Remake starts the run too; when it does not start, the LOCKED image is put back as it was and he is told."""
    from whatifs import builds as BLD
    _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    _masters(("oldsmug", "drive:oldsmug", "LOCKED"), who="VALE", expression="smug")
    def no_run(*a, **k):
        if how == "raises": raise RuntimeError("planted: GitHub does not answer")
        return False
    monkeypatch.setattr(BLD, "dispatch", no_run)
    assert SH.decide("REDO SHEET VALE smug") == "NOT remade: the sheets run could not be started, so VALE's smug was kept as it was (nothing cleared)."
    assert [(r["hash"], r["status"]) for r in core.store().rows("Character_Sheets") if r.get("character") == "VALE"] == [("oldsmug", "LOCKED")]
    assert SH.locked_portraits()[("VALE", "smug")] == "drive:oldsmug"

@pytest.mark.parametrize("how", ["refused", "raises"])
def test_a_locked_masters_remake_whose_run_does_not_start_puts_it_back_locked(how, monkeypatch, setting):
    """RUL-U1i 2 (c) with CR-U1FIX_2 (4): no DRAFT, his Remake of the LOCKED master, the run does not start - the master is put back LOCKED, the face the scenes use stays."""
    from whatifs import builds as BLD
    _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    _masters((H, "drive:m", "LOCKED"))
    def no_run(*a, **k):
        if how == "raises": raise RuntimeError("planted: GitHub does not answer")
        return False
    monkeypatch.setattr(BLD, "dispatch", no_run)
    assert SH.decide("REDO SHEET GRIMM master") == NOT_STARTED
    assert [(r["hash"], r["status"]) for r in _masters_rows()] == [(H, "LOCKED")]
    assert SH.locked_portraits()[("GRIMM", "master")] == "drive:m"


# ------------------------------------------------------------------ RUL-U1i 2: his Remake clears the DRAFT he was shown, never a LOCKED master beside it
def _masters(*rows, who="GRIMM", expression="master"):
    for h, f, s in rows:
        core.store().append("Character_Sheets", [{"ts": FRESH, "character": who, "expression": expression, "hash": h, "prompt": "P", "file": f, "status": s, "approved_at": ""}])

def _by_file(who="GRIMM"):
    return {r["file"]: r for r in core.store().rows("Character_Sheets") if r.get("character") == who}

@pytest.mark.parametrize("road,order", [("card", "locked_first"), ("dashboard", "locked_first"), ("card", "draft_first")])
def test_his_remake_clears_the_draft_he_was_shown_never_a_locked_master(road, order, monkeypatch, setting):
    """RUL-U1i 2 (a), (b): a LOCKED master of an older plan and the new plan's DRAFT - his Remake (the card, or the dashboard's Redo) clears the DRAFT,
    in either tab order; the LOCKED face the scenes use stays."""
    from whatifs import dash as DSH
    rec = _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    old, new = ("oldplan" if order == "locked_first" else "otherplan", "drive:old", "LOCKED"), (H, "drive:new", "DRAFT (identity 5/10)")
    _masters(*((old, new) if order == "locked_first" else (new, old)))
    said = SH.decide("REDO SHEET GRIMM master") if road == "card" else DSH.route("REDOSHEETS|GRIMM")
    assert said == (STARTED if road == "card" else (True, STARTED)), said
    rows = _by_file()
    assert rows["drive:old"]["status"] == "LOCKED" and rows["drive:old"]["hash"] == old[0], rows
    assert rows["drive:new"]["status"] == "REDO" and rows["drive:new"]["hash"].startswith(H + "-redo-"), rows
    assert SH.locked_portraits()[("GRIMM", "master")] == "drive:old" and rec["dispatch"] == [("sheets.yml", {})]

@pytest.mark.parametrize("case", ["one_locked", "two_locked"])
def test_a_redo_with_no_draft_clears_the_newest_locked_image(case, monkeypatch, setting):
    """RUL-U1i 2 (c): no DRAFT - his REDO of a LOCKED image stays (v9.3.1 L6) and clears the NEWEST LOCKED row; an older LOCKED row stays."""
    rec = _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    if case == "one_locked": _masters((H, "drive:only", "LOCKED"))
    else: _masters(("oldplan", "drive:old", "LOCKED"), (H, "drive:cur", "LOCKED"))
    assert SH.decide("REDO SHEET GRIMM master") == STARTED and rec["dispatch"] == [("sheets.yml", {})]
    rows = _by_file(); cur = "drive:only" if case == "one_locked" else "drive:cur"
    assert rows[cur]["status"] == "REDO" and rows[cur]["hash"].startswith(H + "-redo-"), rows
    if case == "two_locked": assert rows["drive:old"]["status"] == "LOCKED" and rows["drive:old"]["hash"] == "oldplan", rows

def test_the_same_rule_holds_for_an_expression_sheet(monkeypatch, setting):
    """RUL-U1i 2 (d): VALE smug, an older LOCKED row then a new DRAFT - REDO clears the DRAFT, the LOCKED row is untouched, the run is started (RUL-U3k U1-2)."""
    rec = _stubs(monkeypatch, setting, [9]); setting("MASTER_FLOOR_ON", "TRUE")
    _masters(("oldsmug", "drive:oldsmug", "LOCKED"), ("newsmug", "drive:newsmug", "DRAFT"), who="VALE", expression="smug")
    assert SH.decide("REDO SHEET VALE smug") == STARTED and rec["dispatch"] == [("sheets.yml", {})]
    rows = _by_file("VALE")
    assert rows["drive:newsmug"]["status"] == "REDO" and rows["drive:newsmug"]["hash"].startswith("newsmug-redo-"), rows
    assert rows["drive:oldsmug"]["status"] == "LOCKED" and rows["drive:oldsmug"]["hash"] == "oldsmug", rows


# ------------------------------------------------------------------ CR-U1FIX_2 (5): send_buttons says what reaches WhatsApp past ten choices
def test_send_buttons_says_what_reaches_whatsapp_past_ten_choices(monkeypatch):
    """Eleven choices reach WhatsApp as one list of the first ten (send_list keeps ten rows); the docstring says so, never that no choice is
    ever dropped."""
    from whatifs import wa as WA
    sent = []; monkeypatch.setattr(WA, "_go", lambda body, kind=None, now=None: sent.append(body) or "wamid.F318")
    said = []; monkeypatch.setattr(WA, "log", lambda m, *a, **k: said.append((m, a)))
    WA.send_buttons("Eleven", [(f"Choice {i}", f"ID{i}") for i in range(11)])
    assert [r["id"] for r in sent[0]["interactive"]["action"]["sections"][0]["rows"]] == [f"ID{i}" for i in range(10)], sent
    assert said == [("WhatsApp list cut to 10 of 11 choices: Eleven", ("WARN",))], said
    WA.send_buttons("Ten", [(f"Choice {i}", f"ID{i}") for i in range(10)]); assert len(said) == 1, said      # ten rows: nothing cut, nothing logged
    doc = " ".join(WA.send_buttons.__doc__.split())
    assert "ever dropped" not in doc and "up to ten choices all reach WhatsApp; past the tenth they are dropped there" in doc, doc
