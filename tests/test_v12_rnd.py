"""v12 B5 - R&D (whatifs/org/rnd.py) and the Review Board (whatifs/org/board.py). Every rule is proven both ways: provenance by code (phantom,
dead, undated, future, the type by domain, the ceiling), the agenda from every gap source, the weekly run inside the cap with the owner's question
beyond it, the blind two-family checklist with the planted canary, the verdict table and the family veto, check research_cadence with every FAIL
condition, the money reserve, and the REAL learning job running both departments."""
import datetime as dt, json, os, sys
import pytest
from whatifs import core, contract as CON, models as M, fakes as FK, governor as G, cli
from whatifs.org import palace as P, schemas as SC, memos as MEM, registry as REG, runner as RUN, levers as LV, rnd as RND, board as BRD

H, D = dt.timedelta(hours=1), dt.timedelta(days=1)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def now(): return core.now_utc()
def st(): return core.store()
def agenda(): return {r["source"]: r for r in st().rows(RND.TAB)}
def memos(t): return [m for m in MEM.rows(st()) if m["type"] == t]
def sessions(dept, trig): return [r for r in st().rows("Sessions") if r["dept"] == dept and r["trigger"] == trig]
GOOD = [("https://support.google.com/youtube/answer/1", "YouTube Help", "2026-10-01", "Repetitive uploads are not eligible."),
        ("https://arxiv.org/abs/2601.00001", "A paper", "2026-09-01", "Re-hooks raised 30-second retention by 6 points."),
        ("https://www.some-creator-blog.com/post", "A blog", "2026-08-01", "We re-hook every 40 seconds.")]
def call(srcs=GOOD, provider="claude", role="sonnet", quotes=True):
    return {"provider": provider, "role": role, "model": f"fake-{role}", "usd": 0.0,
            "citations": [{"url": u, "title": t, "cited_text": q if quotes else ""} for u, t, _d, q in srcs] if provider == "claude" else [],
            "results": [{"url": u, "title": t, "page_age": d} for u, t, d, _q in srcs]}
def reply(srcs, findings, actions=()):
    return {"sources": srcs, "findings": findings, "confidence": 0.9, "expected_impact": "more viewers at 30 seconds in the next long video",
            "proposed_actions": list(actions) or [{"action": "Re-hook at least every 40 seconds in the script", "metric": "retention", "direction": "up", "horizon_videos": 2}]}
def src(i, **k): u, t, d, _q = GOOD[i]; return dict({"url": u, "title": t, "date": d, "type": "official"}, **k)

# ------------------------------------------------------------------ provenance
def test_a_source_the_search_never_returned_is_a_phantom_and_costs_two_points_of_ceiling():
    clean = RND.verify(reply([src(0), src(1)], [{"text": "Repetitive uploads are not eligible for money.", "sources": [0, 1]}]), call(), "policy")
    r = reply([src(0), src(1), {"url": "https://invented.example.org/x", "date": "2026-10-01"}],
              [{"text": "Repetitive uploads are not eligible for money.", "sources": [0, 1]}, {"text": "A study shows trials triple views overnight.", "sources": [2]}])
    v = RND.verify(r, call(), "policy")
    assert v["dropped"] == {"phantom": 1, "findings": 1} and len(v["findings"]) == 1 and v["ceiling"] == clean["ceiling"] - 2 and 2 not in v["sources"]

def test_dead_undated_and_future_sources_are_dropped_and_a_finding_without_a_source_goes_with_them():
    dead = ("https://gone.invalid/page", "Gone", "2026-10-01", "x")
    later = (now() + 3 * D).date().isoformat()
    r = reply([src(0), {"url": dead[0], "date": dead[2]}, src(1, date=""), src(2, date=later)],
              [{"text": "The official page says repetitive uploads are not eligible.", "sources": [0]}, {"text": "Only the dead page says this one thing.", "sources": [1]},
               {"text": "Only the undated and the future page say this.", "sources": [2, 3]}])
    c = call(GOOD[:1] + [dead] + [(GOOD[1][0], GOOD[1][1], "", "q")] + GOOD[2:])
    v = RND.verify(r, c, "technique")
    assert v["dropped"] == {"dead": 1, "undated": 1, "future": 1, "findings": 2} and [f["sources"] for f in v["findings"]] == [[0]]
    assert RND.verify(reply([src(1, date="")], [{"text": "dated by the page age of the search result", "sources": [0]}]), call(), "technique")["findings"]   # page_age dates it

def test_the_evidence_type_is_set_by_the_domain_and_a_model_can_only_lower_it():
    assert RND.source_type("https://www.some-creator-blog.com/x", "measured") == "practice" and RND.source_type("https://arxiv.org/abs/1", "official") == "measured"
    assert RND.source_type("https://support.google.com/youtube", "practice") == "official" and RND.source_type("https://blog.youtube/news", "opinion") == "opinion"
    v = RND.verify(reply([src(2, type="official")], [{"text": "A blog says re-hooks help retention.", "sources": [0]}]), call(), "technique")
    assert v["sources"][0]["type"] == "practice"

def test_the_ceiling_counts_domains_strong_sources_quotes_freshness_and_phantoms():
    assert RND.ceiling(0, True, 1, True, 0) == 0 and RND.ceiling(1, False, 0, True, 0) == 4 and RND.ceiling(2, False, 0, True, 0) == 6
    assert RND.ceiling(3, True, 1.0, True, 0) == 10 and RND.ceiling(3, True, 1.0, False, 0) == 8 and RND.ceiling(3, True, 1.0, True, 2) == 6
    assert RND.ceiling(3, True, 1.0, True, 0, domain_only=True) == 6 and RND.ceiling(1, False, 0, False, 3) == 0
    v = RND.verify(reply([src(0), src(1), src(2)], [{"text": "Three domains agree on re-hooks.", "sources": [0, 1, 2]}]), call(quotes=False), "technique")
    assert v["ceiling"] == 9 and v["quoted_share"] == 0.0

def test_gemini_grounding_is_matched_by_domain_only_and_tops_out_at_six():
    g = {"provider": "gemini", "role": "gem_pro", "model": "fake-gem_pro", "usd": 0, "citations": [],
         "results": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/abc", "title": "support.google.com", "page_age": ""},
                     {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/def", "title": "arxiv.org", "page_age": ""},
                     {"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/ghi", "title": "some-creator-blog.com", "page_age": ""}]}
    v = RND.verify(reply([src(0), src(1), src(2), {"url": "https://unrelated.org/a", "date": "2026-10-01"}], [{"text": "All three agree on this point.", "sources": [0, 1, 2, 3]}]), g, "policy")
    assert v["grounding"] == "domain" and v["dropped"] == {"phantom": 1} and v["ceiling"] == 4                     # capped at 6, then the phantom costs 2
    clean = RND.verify(reply([src(0), src(1), src(2)], [{"text": "All three agree on this point.", "sources": [0, 1, 2]}]), g, "policy"); assert clean["ceiling"] == 6

def test_liveness_on_a_real_network(monkeypatch):
    import requests
    class R:
        def __init__(self, c): self.status_code = c
        def close(self): pass
    monkeypatch.setattr(RND, "FAKE", False)
    for head, get, want in ((404, 200, False), (410, 200, False), (200, 200, True), (403, 200, True), (405, 404, False), (429, 0, True)):
        monkeypatch.setattr(requests, "head", lambda *a, **k: R(head)); monkeypatch.setattr(requests, "get", lambda *a, **k: R(get))
        assert RND.alive("https://example.org/a") is want, (head, get)
    def boom(e):
        def f(*a, **k): raise e
        return f
    monkeypatch.setattr(requests, "head", boom(requests.Timeout())); assert RND.alive("https://example.org/a") is True          # slow is not dead
    monkeypatch.setattr(requests, "head", boom(requests.ConnectionError())); assert RND.alive("https://example.org/a") is False
    assert RND.alive("https://made-up.invalid/x") is False and RND.alive("not a url") is False

def test_dates_in_the_forms_pages_and_models_write():
    T = dt.datetime(2026, 11, 11, tzinfo=dt.timezone.utc)
    assert RND.parse_date("2026-07-15", T) == dt.date(2026, 7, 15) and RND.parse_date("April 30, 2025", T) == dt.date(2025, 4, 30)
    assert RND.parse_date("15 July 2026", T) == dt.date(2026, 7, 15) and RND.parse_date("3 days ago", T) == dt.date(2026, 11, 8) and RND.parse_date("2026-07", T) == dt.date(2026, 7, 1)
    assert RND.parse_date("", T) is None and RND.parse_date("soon", T) is None and RND.parse_date("2026-13-40", T) is None

def test_predictions_need_a_known_metric_a_direction_and_a_horizon():
    texts, preds, tg = RND._actions({"proposed_actions": [
        {"action": "Re-hook at least every 40 seconds", "metric": "retention", "direction": "up", "horizon_videos": 2, "target_depts": ["D4", "XX"]},
        {"action": "Make thumbnails louder and brighter", "metric": "vibes", "direction": "up", "horizon_videos": 2},
        {"action": "Lower the music under narration", "metric": "ctr", "direction": "sideways", "horizon_videos": 2},
        {"action": "Shorter cold opens for every video", "metric": "ret30", "direction": "up", "horizon_videos": 12}, "too short"]}, set(RND.metrics()))
    assert preds == [{"action": 0, "metric": "retention", "direction": "up", "horizon_videos": 2}] and tg == ["D4"] and len(texts) == 4
    assert all("no measurable prediction" in t for t in texts[1:]) and "research_cadence" not in RND.metrics() and "ctr" in RND.metrics()

def test_a_question_whose_answer_cannot_be_proven_writes_no_memo(monkeypatch):
    row = {"id": "RA-X", "question": "Is anything true about this question at all?", "kind": "technique", "urgency": "P1", "target_depts": '["D4"]', "source": "check", "ref": "retention"}
    monkeypatch.setattr(FK, "_fake_research", lambda p: json.dumps(reply([{"url": "https://invented.org/a", "date": "2026-10-01"}], [{"text": "An invented study proves it.", "sources": [0]}])))
    res = RND.ask_one(row, "")
    assert res["memo"] is None and res["status"] == "unanswered" and '"phantom": 1' in res["note"]

def test_a_research_memo_carries_only_verified_evidence_and_passes_the_memo_gate():
    row = {"id": "RA-Y", "question": "What re-hook rhythm holds viewers in long explainers?", "kind": "technique", "urgency": "P1", "target_depts": '["D4"]', "source": "check", "ref": "retention"}
    res = RND.ask_one(row, "our playbook text"); m = res["memo"]
    urls = {u for u, *_ in FK.FAKE_SOURCES}
    assert res["status"] == "answered" and all(e["url"] in urls for e in m["evidence"]) and m["body"]["sources_dropped"]["phantom"] == 1
    assert m["body"]["confidence"] <= m["body"]["evidence_ceiling"] / 10 and m["links"]["verified"] == "rnd.verify" and m["links"]["family"] == "claude"
    assert all(e["finding"].startswith("quote: ") for e in m["evidence"]) and not SC.check_memo(dict(m))[1] and m["owner_visible"] is False
    assert [p["metric"] for p in m["body"]["predictions"]] == ["retention", "originality"]

# ------------------------------------------------------------------ the agenda
def _gaps_everywhere():
    t = core.iso()
    st().append("Feature_Ledger", [{"ts": t, "episode_id": f"EP{i}", "stage": "script", "feature": f, "status": "FAIL", "evidence": "x"}
                                   for i, f in enumerate(["retention", "retention", "dept_contract", "dept_contract", "dept_contract"])])
    st().append("Breakout_Scores", [{"ts": t, "episode_id": "EP1", "weakest": "hook"}, {"ts": t, "episode_id": "EP2", "weakest": "hook"}])
    MEM.write({"type": "owner_memo", "from_dept": "D0", "to_depts": ["D4"], "subject": "Owner: nostalgia in the cold open",
               "body": {"verbatim": "make the cold open feel nostalgic", "interpretation": "open each video on a sensory childhood memory"}, "done_when": "the next cold open carries a sensory memory"})
    pm = {"type": "problem_memo", "from_dept": "D8", "to_depts": ["D6"], "subject": "Rain scenes read as stills", "body": {"what_failed": "rain particles look frozen", "where": "render", "attempt": 1},
          "done_when": "aliveness passes on rain worlds", "evidence": [{"source": "Feature_Ledger", "date": t[:10], "type": "own data", "finding": "aliveness 0.0"}]}
    MEM.write(dict(pm, session_id="S1")); MEM.write(dict(pm, session_id="S2"))
    st().append("Outlier_Lab", [{"ts": t, "video_id": "VID1", "title": "What if the Moon fell", "status": "added"}])
    st().append("Tool_Scout", [{"ts": t, "endpoint_id": "fal-ai/new-video", "name": "New Video", "category": "image-to-video"}])
    P.ensure_seed(); tf = next(r for r in P.rows() if r["kind"] == "tool_fact" and r["status"] in P.SERVABLE)
    st().update("Palace_Items", "id", tf["id"], {"review_by": core.iso(now() + 5 * D)})
    return tf

def test_the_agenda_comes_from_every_gap_source_and_never_from_a_code_fault():
    tf = _gaps_everywhere(); g = {x["source"]: x for x in RND.gaps()}
    assert set(g) == {"check", "breakout", "owner", "problem", "outlier", "expiring", "tools", "policy"}
    assert g["check"]["ref"] == "retention" and g["check"]["target_depts"] == ["D4"] and g["check"]["priority"] == 5
    assert not [x for x in RND.gaps() if x["ref"] == "dept_contract"]                                       # a failed organisation check is a code fault, not research
    assert g["owner"]["urgency"] == "P0" and "nostalgic" in g["owner"]["question"] and g["problem"]["target_depts"] == ["D6"]
    assert g["expiring"]["palace_ref"] == tf["id"] and g["expiring"]["kind"] == "revalidate" and g["policy"]["kind"] == "policy"

def test_the_agenda_dedupes_drops_closed_gaps_and_asks_again_only_after_the_repeat_window():
    _gaps_everywhere(); a = RND.refresh(); b = RND.refresh()
    assert a["new"] == 8 and not b.get("new") and len(st().rows(RND.TAB)) == 8
    st().update(RND.TAB, "id", agenda()["tools"]["id"], {"status": "answered", "asked_at": core.iso(now() - 40 * D)})
    st().update(RND.TAB, "id", agenda()["outlier"]["id"], {"status": "answered", "asked_at": core.iso(now() - 2 * D)})
    c = RND.refresh(); assert c.get("reopened") == 1 and agenda()["tools"]["status"] == "open" and agenda()["outlier"]["status"] == "answered"
    st().d["Outlier_Lab"] = []; st().update(RND.TAB, "id", agenda()["breakout"]["id"], {"status": "open"}); st().d["Breakout_Scores"] = []; st().save()
    assert RND.refresh().get("dropped") == 1 and agenda()["breakout"]["status"] == "dropped"

def test_a_question_is_never_asked_again_while_its_last_memo_is_open():
    RND.refresh(); r = agenda()["policy"]
    m = MEM.write(dict(RND.ask_one(dict(r), "")["memo"]))
    st().update(RND.TAB, "id", r["id"], {"status": "answered", "asked_at": core.iso(now() - 40 * D), "memo_id": m["id"]})
    RND.refresh(); assert agenda()["policy"]["status"] == "answered"
    MEM.reject(m["id"], "D3", "closed for this test: the question may come back"); RND.refresh(); assert agenda()["policy"]["status"] == "open"

def test_a_question_whose_run_died_or_whose_call_failed_opens_again_the_next_day_not_in_a_month():
    RND.refresh(); r = agenda()["policy"]
    st().update(RND.TAB, "id", r["id"], {"status": "asked", "asked_at": core.iso(now() - 2 * H)}); RND.refresh(); assert agenda()["policy"]["status"] == "asked"
    st().update(RND.TAB, "id", r["id"], {"asked_at": core.iso(now() - 21 * H)}); RND.refresh()
    assert agenda()["policy"]["status"] == "open" and "did not finish" in agenda()["policy"]["note"]
    st().update(RND.TAB, "id", r["id"], {"status": "failed", "asked_at": core.iso(now() - 21 * H), "note": "no answer: all models failed"}); RND.refresh()
    assert agenda()["policy"]["status"] == "open" and "after a failed call" in agenda()["policy"]["note"]

def test_a_stored_ceiling_is_recomputed_from_the_day_the_memo_was_written():
    RND.refresh(); m = MEM.write(dict(RND.ask_one(dict(agenda()["policy"]), "")["memo"]))
    assert RND.ceiling_of(m) == m["body"]["evidence_ceiling"] == 8
    assert RND.ceiling_of(m, now() + 400 * D) == 8                                   # sources that were fresh when it was written stay fresh for the check

# ------------------------------------------------------------------ the weekly run: cap and P0
def test_the_weekly_run_asks_the_top_questions_inside_the_cap_and_the_owners_question_beyond_it(setting):
    _gaps_everywhere(); setting("RESEARCH_PER_WEEK", "1")
    st().append("Org_Audit", [{"ts": core.iso(), "kind": "run", "dept": "D2", "budget": "org", "cost_inr": 290}])
    r = RUN.run("D2", "weekly", RND.deep, budget="org", urgency="P0")
    a = agenda(); assert r.ok and a["owner"]["status"] == "answered" and [x["source"] for x in a.values() if "waits: R&D budget left Rs 10 < Rs 15" in x["note"]]
    assert [m["body"]["gap"]["source"] for m in memos("research_memo")] == ["owner"] and r.output == {"asked": 1, "memos": 1}
    st().append("Org_Audit", [{"ts": core.iso(), "kind": "run", "dept": "D2", "budget": "org", "cost_inr": 20}])
    with pytest.raises(RUN.CapReached): RUN.run("D2", "weekly", RND.deep, budget="org", urgency="P1")         # at the cap: only P0 work starts

def test_the_deep_research_is_due_by_level_not_by_calendar(setting):
    assert RND.deep_due()
    st().append("Sessions", [{"id": "S-W", "dept": "D2", "trigger": "weekly", "status": "ok", "started": core.iso(now() - 2 * D)}]); assert not RND.deep_due()
    st().update("Sessions", "id", "S-W", {"started": core.iso(now() - 7 * D)}); assert RND.deep_due()
    st().update("Sessions", "id", "S-W", {"started": core.iso(now() - D)}); _gaps_everywhere(); RND.refresh(); assert RND.p0_waiting() and RND.deep_due()
    st().d["Research_Agenda"] = []; st().update("Sessions", "id", "S-W", {"started": core.iso(now() - D), "status": "breach"}); st().save()
    assert not RND.deep_due()                                                            # a run that broke the contract is not paid for again tomorrow
    setting("RESEARCH_ON", "FALSE"); assert not RND.deep_due()
    setting("RESEARCH_ON", "TRUE"); setting("ORG_ON", "FALSE"); assert not RND.deep_due()

# ------------------------------------------------------------------ the Review Board
def _round():
    RUN.work("D2", "daily", "", RND.daily); RUN.run("D2", "weekly", RND.deep, budget="org"); return RUN.run("D3", "assess", BRD.assess, budget="org")

def test_a_board_session_judges_blind_in_two_families_and_two_orders_and_closes_each_memo_with_its_assessment():
    r = _round(); rm = memos("research_memo"); am = memos("assessment_memo")
    assert r.ok and len(rm) == 2 and len(am) == 2 and all(m["status"] == "resolved" and m["resolution"]["kind"] == "assessment_memo" for m in rm)
    assert {m["resolution"]["ref"] for m in rm} == {a["id"] for a in am} and all(a["level"] == 2 and not a["owner_notified"] for a in am)   # the Council's level, silent until B6
    log = st().rows(BRD.LOG); assert len(log) == 2 * 2 * 3 and {r_["family"] for r_ in log} == {"gemini", "claude"} and sum(1 for r_ in log if r_["canary"]) == 4
    a = {x["body"]["kind"]: x["body"] for x in am}
    assert a["policy"]["verdict"] == "accept" and a["technique"]["verdict"] == "test" and a["policy"]["jury"] == ["claude:fake-sonnet", "gemini:fake-gem_pro"]
    assert all(not BRD.assessment_issues(x) for x in am) and a["policy"]["canary"].startswith("rejected by claude, gemini")
    sent = []
    orig = M.ask
    def spy(role, system, prompt, *k, **kw):
        if role.startswith("board"): sent.append(prompt)
        return orig(role, system, prompt, *k, **kw)
    M.ask = spy
    try:
        RND.refresh(); st().update(RND.TAB, "id", agenda()["outlier"]["id"], {"status": "open"})
        RUN.run("D2", "weekly", RND.deep, budget="org"); RUN.run("D3", "assess", BRD.assess, budget="org")
    finally: M.ask = orig
    ids = [m["id"] for m in MEM.rows(st())]
    assert sent and not any(x in p for p in sent for x in ids + ["rnd_research", "rnd.verify", "fake-sonnet", "fake-gem_pro"])           # blind: no memo id, author or model
    assert not any("D2" in p.split("WHAT WE ALREADY DO")[0] for p in sent)

def test_a_judge_answered_by_another_family_or_a_cheap_model_does_not_count_and_the_session_is_void(monkeypatch):
    RUN.work("D2", "daily", "", RND.daily); RUN.run("D2", "weekly", RND.deep, budget="org")
    orig = M.ask
    def fallback(role, *a, **k):
        out = orig(role, *a, **k)
        if role == "board_gemini": M._note_call("claude", "sonnet", "fake-sonnet")              # Gemini Pro failed and the chain fell back to the other family
        return out
    monkeypatch.setattr(M, "ask", fallback)
    r = RUN.run("D3", "assess", BRD.assess, budget="org")
    assert r.ok and not memos("assessment_memo") and all(m["status"] != "resolved" for m in memos("research_memo"))
    pm = [m for m in memos("problem_memo") if m["from_dept"] == "D3"]; assert pm and "only 1 model family answered" in pm[0]["body"]["what_failed"]
    assert {x["verdict"] for x in st().rows(BRD.LOG)} == {"void"}
    def cheap(role, *a, **k):
        out = orig(role, *a, **k)
        if role == "board_gemini": M._note_call("gemini", "gem_flash", "fake-flash")
        return out
    monkeypatch.setattr(M, "ask", cheap); RUN.run("D3", "assess", BRD.assess, budget="org")
    assert not memos("assessment_memo") and [m for m in memos("problem_memo") if m["from_dept"] == "D3"][0]["attempt"] == 2
    monkeypatch.setattr(M, "ask", orig); RUN.run("D3", "assess", BRD.assess, budget="org")
    assert len(memos("assessment_memo")) == 2 and [m for m in MEM.rows(st()) if m["type"] == "problem_memo" and m["from_dept"] == "D3"][0]["status"] == "resolved"

def test_an_inflating_jury_that_does_not_reject_the_canary_voids_the_session(monkeypatch):
    RUN.work("D2", "daily", "", RND.daily); RUN.run("D2", "weekly", RND.deep, budget="org")
    def flatter(prompt):
        import re
        return json.dumps({"answers": {l: dict({q: ["yes", "great"] for q in ("E1", "E2", "N1", "N2", "I1", "I2", "I3", "F1", "F2")}, **{q: ["no", "fine"] for q in BRD.RISK_Q})
                                       for l in re.findall(r"=== MEMO ([A-Z]) ===", prompt)}})
    monkeypatch.setattr(FK, "_fake_board", flatter)
    RUN.run("D3", "assess", BRD.assess, budget="org")
    assert not memos("assessment_memo") and "the planted canary" in [m for m in memos("problem_memo") if m["from_dept"] == "D3"][0]["body"]["what_failed"]

def test_an_unanswered_question_counts_against_the_memo():
    out = BRD._parse({"answers": {"A": {"E1": ["yes", "ok"], "R1": "no"}}}, "AB")
    assert out["A"][0]["E1"] is True and out["A"][0]["E2"] is False and out["A"][0]["R1"] is False and out["A"][0]["R2"] is True and out["A"][2] == 10
    assert all(v is False for q, v in out["B"][0].items() if q not in BRD.RISK_Q) and all(out["B"][0][q] for q in BRD.RISK_Q)

def test_the_verdict_table_both_ways():
    yes = {q: 1.0 for q, _d, _t in BRD.QUESTIONS}; ok = dict(yes, **{q: 0.0 for q in BRD.RISK_Q})
    v = lambda fams, kind="technique", preds=1, ceil=10, author="claude", cost=0: BRD.verdict(fams, ceil, cost, kind, preds, author, 5)[0]
    assert v({"claude": ok, "gemini": ok}, "policy") == "accept" and v({"claude": ok, "gemini": ok}) == "test"              # an idea is never accepted, only tested
    assert v({"claude": ok, "gemini": ok}, preds=0) == "reject"                                                               # no pre-registered prediction, no test
    assert v({"claude": ok, "gemini": ok}, "policy", ceil=6) == "test" and v({"claude": ok, "gemini": ok}, ceil=4) == "reject"   # the ceiling binds the jury
    assert v({"claude": yes, "gemini": yes}) == "reject"                                                                      # all risks flagged
    weak = dict(ok, I2=0.0, I3=0.0)                                                                                          # the mean still earns "test"
    assert v({"claude": ok, "gemini": weak}) == "reject" and v({"claude": weak, "gemini": ok}) == "test"                     # the non-author family's veto
    half = dict(ok, I3=0.0); assert v({"claude": ok, "gemini": half}) == "test" and v({"claude": ok, "gemini": half}, "policy") == "accept"
    assert BRD.cost_score(0) == 10 and BRD.cost_score(250) == 5 and BRD.cost_score(900) == 0 and BRD.cost_score("x") == 0

def test_a_forged_verdict_or_score_is_caught_by_recomputing_the_checklist():
    _round(); a = next(x for x in memos("assessment_memo") if x["body"]["verdict"] == "test")
    assert not BRD.assessment_issues(a)
    assert "is not the code's verdict" in BRD.assessment_issues(dict(a, body=dict(a["body"], verdict="accept")))[0]
    assert "scores differ" in BRD.assessment_issues(dict(a, body=dict(a["body"], scores=dict(a["body"]["scores"], impact=1.0))))[-1]
    one = dict(a["body"], checklist=dict(a["body"]["checklist"], families={"claude": a["body"]["checklist"]["families"]["claude"]}))
    assert BRD.assessment_issues(dict(a, body=one)) == ["judged by fewer than two model families"]
    assert BRD.assessment_issues(dict(a, body=dict(a["body"], canary=""))) == ["no planted canary was rejected in its session"]

# ------------------------------------------------------------------ check research_cadence
def _aged(hours=72):
    core.set_setting("ORG_SINCE", core.iso(now() - hours * H))

def test_research_cadence_judges_nothing_while_off_or_young(setting):
    setting("ORG_ON", "FALSE"); assert CON.p_research_cadence({}) == (CON.NA, "organisation switched off")
    setting("ORG_ON", "TRUE"); setting("RESEARCH_ON", "FALSE"); assert CON.p_research_cadence({})[1] == "research switched off (RESEARCH_ON)"
    setting("RESEARCH_ON", "TRUE"); _round(); s, ev = CON.p_research_cadence({}); assert s == CON.NA and "research is judged from 48 h" in ev

def test_research_cadence_fails_on_every_broken_promise_and_passes_when_kept():
    _round(); _aged(); s, ev = CON.p_research_cadence({}); assert s == CON.PASS and "2 research memo(s): 2 assessed" in ev and "1 accept, 1 test" in ev
    d = sessions("D2", "daily")[0]; st().update("Sessions", "id", d["id"], {"started": core.iso(now() - 60 * H)})
    assert "R&D's daily run is 60 h old" in CON.p_research_cadence({})[1]; st().update("Sessions", "id", d["id"], {"started": core.iso()})
    _aged(24 * 10); w = sessions("D2", "weekly")[0]; st().update("Sessions", "id", w["id"], {"started": core.iso(now() - 9 * D)})
    assert "the weekly deep research is 9 days old while R&D budget is left" in CON.p_research_cadence({})[1]
    st().append("Org_Audit", [{"ts": core.iso(), "kind": "run", "dept": "D2", "budget": "org", "cost_inr": 300}]); assert CON.p_research_cadence({})[0] == CON.PASS   # capped = waits
    st().update("Sessions", "id", w["id"], {"started": core.iso()}); _aged()

def test_research_cadence_fails_on_unstamped_forged_late_or_overspent_research():
    _round(); _aged(); rm = memos("research_memo")[0]
    raw = {k: rm[k] for k in ("type", "from_dept", "to_depts", "subject", "body", "evidence")}
    MEM.write(dict(raw, subject="A research memo written around the verifier", dedupe_key="sneak"))
    assert "was not written through rnd.verify" in CON.p_research_cadence({})[1]
    sneak = next(m for m in memos("research_memo") if m["subject"].startswith("A research memo")); MEM.reject(sneak["id"], "D3", "test cleanup of the unstamped memo")
    st().update("Memos", "id", sneak["id"], {"links": dict(rm["links"]), "body": dict(sneak["body"], evidence_ceiling=10)})
    assert "claims evidence ceiling 10 but its sources support 8" in CON.p_research_cadence({})[1]
    st().update("Memos", "id", sneak["id"], {"body": dict(sneak["body"], evidence_ceiling=8)}); assert CON.p_research_cadence({})[0] == CON.PASS
    late = MEM.write(dict(raw, subject="A research memo that nobody assessed in time", dedupe_key="late", links=dict(rm["links"])))
    st().update("Memos", "id", late["id"], {"sla_due": core.iso(now() - H)})
    assert "is past its SLA and was neither assessed nor escalated" in CON.p_research_cadence({})[1]
    MEM.escalate(late["id"], "late in this test"); assert CON.p_research_cadence({})[0] == CON.PASS
    am = memos("assessment_memo")[0]; st().update("Memos", "id", am["id"], {"body": dict(am["body"], verdict="accept" if am["body"]["verdict"] != "accept" else "test")})
    assert "is not the code's verdict" in CON.p_research_cadence({})[1]; st().update("Memos", "id", am["id"], {"body": am["body"]})
    st().append("Org_Audit", [{"ts": core.iso(), "kind": "run", "dept": "D3", "budget": "org", "cost_inr": 200}])
    assert "D3 spent Rs 200 this month against a cap of Rs 120 with no owner question asked" in CON.p_research_cadence({})[1]

# ------------------------------------------------------------------ wiring, money, the model doorway
def test_the_real_learning_job_runs_rnd_and_the_board_first(monkeypatch):
    from whatifs import manage as MG
    monkeypatch.setattr(MG, "learn", lambda: None); monkeypatch.setattr(MG, "money_check", lambda: None)
    monkeypatch.setattr(sys, "argv", ["whatifs.cli", "learn"]); cli.main()
    assert [s["status"] for s in sessions("D2", "daily")] == ["ok"] and sessions("D2", "weekly") and sessions("D3", "assess") and memos("assessment_memo")
    assert sessions("D10", "daily")
    monkeypatch.setattr(cli, "research_round", lambda: None); cli.main()
    assert len(sessions("D2", "daily")) == 1 and len(sessions("D10", "daily")) == 2                       # without the call nothing researches: this test sees it

def test_the_learning_job_no_longer_runs_the_collectors_that_moved_to_rnd():
    src = open(os.path.join(ROOT, "whatifs", "manage.py"), encoding="utf-8").read()
    assert "OLB.run()" not in src and "RS.save_brief(RS.run_research())" not in src
    s2 = open(os.path.join(ROOT, "whatifs", "org", "rnd.py"), encoding="utf-8").read(); assert "OLB.run()" in s2 and "RS.save_brief(RS.run_research())" in s2

def test_d2_and_d3_are_wired_and_their_levers_are_registered():
    assert "D2" in REG.ENTRY and "D3" in REG.ENTRY and "D2" not in REG.PENDING and "D3" not in REG.PENDING and not REG.entry_issues() and not REG.data_issues()
    assert REG.may_change("D2", "RESEARCH_PER_WEEK") and REG.may_change("D3", "BOARD_MIN_EVIDENCE") and LV.owner_of("BOARD_MIN_EVIDENCE") == "D3"
    assert REG.check_owner("research_cadence") == "D2" and ("research_cadence", "script") in {(f[0], f[1]) for f in CON.FEATURES}
    up, down, fine, theirs = LV.check("D2", "RESEARCH_PER_WEEK", "6"), LV.check("D3", "BOARD_MIN_EVIDENCE", "4"), LV.check("D3", "BOARD_MIN_EVIDENCE", "6"), LV.check("D2", "BOARD_MIN_EVIDENCE", "6")
    assert not up["why"] and up["owner"] and not down["why"] and down["owner"] and not fine["why"] and not fine["owner"] and "is a lever of D3, not of D2" in theirs["why"]
    assert "further than" in LV.check("D3", "BOARD_MIN_EVIDENCE", "8")["why"] or LV.check("D3", "BOARD_MIN_EVIDENCE", "8")["why"]
    assert M.CHAINS["board_g"] == [("g", "gem_pro")] and all(p == "c" and r in BRD.STRONG for p, r in M.CHAINS["board_c"])            # no cheap model in a Board chain

def test_the_unspent_organisation_caps_are_never_production_money(setting):
    base = G.org_left_inr(); assert base == 420.0
    room = G.production_room_inr()
    st().append("Org_Audit", [{"ts": core.iso(), "kind": "run", "dept": "D2", "budget": "org", "cost_inr": 100}]); assert G.org_left_inr() == 320.0
    setting("RESEARCH_ON", "FALSE"); assert G.org_left_inr() == 0.0
    setting("RESEARCH_ON", "TRUE"); setting("ORG_ON", "FALSE"); assert G.org_left_inr() == 0.0 and G.production_room_inr() > room

def test_last_call_reads_the_citations_the_api_returned(monkeypatch):
    class R:
        status_code = 200; text = ""
        def json(self): return {"content": [{"type": "server_tool_use", "name": "web_search"},
                                            {"type": "web_search_tool_result", "content": [{"type": "web_search_result", "url": "https://a.org/x", "title": "A", "page_age": "May 1, 2026"}]},
                                            {"type": "text", "text": "{\"ok\": 1}", "citations": [{"type": "web_search_result_location", "url": "https://a.org/x", "title": "A", "cited_text": "quoted"}]}],
                                "usage": {"input_tokens": 1000, "output_tokens": 100, "server_tool_use": {"web_search_requests": 2}}, "stop_reason": "end_turn"}
    monkeypatch.setattr(M, "_post", lambda body, headers: R())
    assert M._claude("sonnet", "system", "prompt", 500, 0.2, True, None) == "{\"ok\": 1}"
    c = M.last_call(); assert c["provider"] == "claude" and c["role"] == "sonnet" and c["usd"] > 0.02
    assert c["citations"] == [{"url": "https://a.org/x", "title": "A", "cited_text": "quoted"}] and c["results"][0]["page_age"] == "May 1, 2026"
    class G_:
        status_code = 200; text = ""
        def json(self): return {"candidates": [{"content": {"parts": [{"text": "x"}]}, "groundingMetadata": {"groundingChunks": [{"web": {"uri": "https://redirect/1", "title": "a.org"}}]}}]}
    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: G_())
    M._gemini("gem_pro", "s", "p", 100, 0.2, True, False)
    assert M.last_call()["provider"] == "gemini" and M.last_call()["results"] == [{"url": "https://redirect/1", "title": "a.org", "page_age": ""}]
    M.ask("board_gemini", "s", "{}", want_json=True, fake_key="board"); assert M.last_call()["provider"] == "gemini" and M.last_call()["role"] == "gem_pro"
