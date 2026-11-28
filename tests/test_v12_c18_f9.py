"""Audit V4 F9 (RULINGS_U1c 5.3): the closing tests. (b) the Claude credit's cover ceiling from the cost model's OWN prices, not the NOTE's typed numbers.
(a) every card V4 sends, RUN through its own sender, with its default and its deadline read off the real call (RULINGS_U1e 3: two rules, two exemption lists)."""
import datetime as dt, inspect, json, math, os, sys
from whatifs import core
from whatifs.core import S

def _ceiling():
    """Memo 3.3's arithmetic for CREDIT_COVER_MONTH_MAX_INR: 1.5 x (long videos x (writing + hook lab + line-up) x 1.10 + Shorts x (Short writing + 4 x one
    boost script) + R&D + Review Board), up to the next Rs 100 - every price read where the cost model keeps it (number -> source in N\\TYPED_C18FIX.md)."""
    from whatifs.org import registry as REG
    L, Sh = S("STANDARD_MAX_LONG_PER_MONTH", int), S("SHORTS_PER_MONTH", int)
    hook, lineup = S("HOOK_LAB_EST_INR", float), S("PROBE_EST_INR", float)                   # 4, 0.5: costguard's long lines 'hook_lab' and 'probe'
    writing = max(0.0, S("LLM_EST_INR", float) - hook)                                         # 166: costguard's long line 'writing' (LLM_EST_INR less the hook lab)
    short_writing, boost = S("REPLAN_SHORT_INR", float), S("SHORT_VARIANT_EST_INR", float)      # 36: costguard's Short line 'writing'; 12: one more Short script
    caps = REG.caps()                                                                          # 300 R&D (D2), 120 Review Board (D3): the registry's thinking caps
    x = 1.5 * (L * (writing + hook + lineup) * 1.10 + Sh * (short_writing + 4 * boost) + caps["D2"] + caps["D3"])
    return math.ceil(round(x, 6) / 100) * 100, x

def test_the_cover_ceiling_is_recomputed_from_the_cost_models_own_prices(setting):
    """(audit V4 F9 (b)) The cell's default equals the ceiling recomputed from the cost model's reads and the two count cells; and the failing leg: one price
    cell moved, the recomputed ceiling no longer equals the default - so a price change in the cost model turns this red, which a typed number never did.
    The hook lab is not moved: it is a part of LLM_EST_INR (its note), so moving it alone leaves a long video's text cost - and the ceiling - unchanged."""
    c, x = _ceiling(); default = float(core.DEFAULTS["CREDIT_COVER_MONTH_MAX_INR"][0])
    assert round(x, 1) == 3267.3 and c == default, (x, c, default)
    for cell, moved in (("LLM_EST_INR", "270"), ("PROBE_EST_INR", "100.5"), ("REPLAN_SHORT_INR", "136"), ("SHORT_VARIANT_EST_INR", "112"),
                        ("ORG_CAPS_INR", json.dumps({"D2": 400})), ("ORG_CAPS_INR", json.dumps({"D3": 220}))):
        setting(cell, moved); assert _ceiling()[0] != default, (cell, moved, _ceiling())
        setting(cell, str(core.DEFAULTS[cell][0])); assert _ceiling()[0] == default, cell

F9_FILES = ("whatifs/org/strategy.py", "whatifs/org/risk.py", "whatifs/org/desk.py")
F9_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F9_NOW = dt.datetime(2027, 1, 1, 12, 0, tzinfo=dt.timezone.utc)                      # a fixed instant: no clock is read

def test_every_card_v4_sends_is_run_and_names_its_default_and_its_deadline_as_the_memo_keeps_them(monkeypatch, setting):
    """(audit V4 F9 (a), RULINGS_U1e 3) Every `NT.send(` of the three V4 files is RUN through its own sender - strategy.tell, risk.lock, risk._act_platform
    (rejected, gone), desk.tick, desk.weigh_row on its three roads (parked, TAKEN, idea) - with NT.send replaced by a recorder that keeps the raw arguments,
    the caller (file, function, line) and returns an id. RULE D: a default not empty after strip() - except the TAKEN desk row and the idea row (None).
    RULE E: a deadline above 0 - except the kinds the memo keeps open (None there: a deadline may not be added, CA5-8). The sites recorded = the sends in
    the files, counted the scan test's way (tests/test_v12_strategy.py, which stays beside this test unedited)."""
    from whatifs import notify as NT, governor as G
    from whatifs.org import strategy as STR, risk as RISK, desk as DESK, memos as MEM, execute as EX
    OPEN_BY_DESIGN = ("strategy", "desk", "idea", "risk_lock")
    scan = open(os.path.join(F9_ROOT, "tests", "test_v12_strategy.py"), encoding="utf-8").read()
    assert 'OPEN_BY_DESIGN = ("strategy", "desk", "idea", "risk_lock")' in scan                      # the list cannot drift from the scan test's own line
    sig, got = inspect.signature(NT.send), []
    def recorder(*a, **k):
        f = sys._getframe(1); args = sig.bind(*a, **k).arguments                                    # raw: what the sender gave, nothing filled in
        got.append({"kind": args["kind"], "default": args.get("default"), "expires_h": args.get("expires_h"), "key": str(args.get("dedupe_key") or ""),
                    "site": (os.path.relpath(f.f_code.co_filename, F9_ROOT).replace(os.sep, "/"), f.f_code.co_name, f.f_lineno)})
        return f"F9A{len(got)}"
    monkeypatch.setattr(NT, "send", recorder)
    setting("STRATEGY_ON", "TRUE"); setting("TWO_SCREENS_ON", "FALSE")                               # TRUE would take desk.tick to _tick_two, away from its own send
    # strategy.tell: one decided row with its ticket on tab Memos
    row = {"id": "F9D1", "state": STR.IN_FORCE[0], "told": "", "ticket": "F9T1"}
    monkeypatch.setattr(STR, "_rows", lambda st=None: [row]); monkeypatch.setattr(STR, "text_of", lambda r: "Strategy decided: planted.")
    monkeypatch.setattr(STR, "_save", lambda st, r, **ch: r.update(ch)); monkeypatch.setattr(MEM, "get", lambda t, st=None: {"id": t})
    monkeypatch.setattr(MEM, "note_owner_told", lambda *a, **k: None)
    assert STR.tell(F9_NOW) == 1
    # risk.lock, then risk._act_platform's two findings that send
    RISK.lock("F9V1", "planted rejection", F9_NOW, "Planted title")
    RISK._act_platform({"kind": "rejected", "point": "F9V2", "why": "planted rejection", "title": "Planted two"}, F9_NOW, None)
    RISK._act_platform({"kind": "gone", "point": "F9V3", "why": "gone", "title": "Planted three"}, F9_NOW, None)
    # the desk: its tick's parked road, then weigh_row's three roads
    LABELS = {"road taken": {"kind": "preference", "raises_breakout": True, "needs_code": False, "new_arm": False, "department": DESK.DESK_DEPTS[0]},
              "road idea": {"kind": "change_request", "needs_code": True}}
    monkeypatch.setattr(EX, "on", lambda: True); monkeypatch.setattr(DESK, "_memo", lambda *a, **k: {"id": "F9M1"})
    monkeypatch.setattr(DESK, "_close", lambda *a, **k: None); monkeypatch.setattr(DESK, "never", lambda t: None)
    monkeypatch.setattr(DESK, "recognise", lambda t: ("STANDARD_MAX_LONG_PER_MONTH", "5") if t in ("road tick", "road parked") else None)
    monkeypatch.setattr(DESK, "verdict", lambda key, value, now=None, force=False: ("PARKED", "planted: it does not fit this month", "FIT"))
    monkeypatch.setattr(DESK, "weigh", lambda t: LABELS[t]); monkeypatch.setattr(DESK, "_keep", lambda r, dept, now: ("TAKEN", "kept, planted"))
    monkeypatch.setattr(G, "month_spend_of", lambda prefixes: 0.0)
    st = core.store(); st.append("Owner_Input", [{"input": "road tick"}])
    assert [r["verdict"] for r in DESK.tick(F9_NOW)] == ["PARKED"]
    for text in ("road parked", "road taken", "road idea"):
        n = len(DESK._rows(st)) + 1
        st.append(DESK.DESK, [{"n": n, "ts": core.iso(F9_NOW), "sha": f"f9{n}", "verbatim": text, "verdict": "", "how": "", "memo": "F9M1", "ticket": "",
                               "action": "", "briefed": "", "channel": "dashboard", "card": "", "ref": f"f9|{n}"}])
        DESK.weigh_row(f"f9|{n}", F9_NOW)
    for c in got:
        standing = (c["kind"] == "desk" and c["key"].startswith("desk|taken|")) or c["kind"] == "idea"
        if standing: assert c["default"] is None, c                                                    # RULE D: the two standing rows name no default
        else: assert isinstance(c["default"], str) and c["default"].strip(), c                         # RULE D: every other card says what his silence does
        if c["kind"] in OPEN_BY_DESIGN: assert c["expires_h"] is None, c                               # RULE E: kept open by the memo, nor may a deadline be added
        else: assert isinstance(c["expires_h"], (int, float)) and not isinstance(c["expires_h"], bool) and c["expires_h"] > 0, c      # RULE E
    assert {c["kind"] for c in got} == {"desk", "idea", "risk_gone", "risk_lock", "strategy"}, got
    assert sum(c["kind"] == "desk" and c["key"].startswith("desk|taken|") for c in got) == 1 and any(c["kind"] == "idea" for c in got), got
    sends = sum(open(os.path.join(F9_ROOT, rel), encoding="utf-8").read().count("NT.send(") for rel in F9_FILES)      # the scan test's count (7 today)
    sites = {c["site"] for c in got}
    assert all(s[0] in F9_FILES for s in sites) and len(sites) == sends, (sorted(sites), sends)        # every site ran; none is excused
