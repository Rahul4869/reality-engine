"""v12 B6a - the creative departments (D4/D5/D6): the Palace INSIDE the creative model prompts (palace_injected), citations verified by a quote code
finds (palace_cited), the show's canon written by code and made canon on air, the continuity debt paid in a line of the final script (canon_in_brief),
creative memos with the same-idea guard, pre-production drafts adopted only with proof, the canon budget, the money allowance and the one-time cap
move. Every rule is proven both ways, and the real pre-production job and the real reply path of models.ask are run."""
import datetime as dt, json
import pytest
from whatifs import core, contract as CON, models as M, fakes as FK, governor as G, costguard as CG, manage as MG, preview as PV
from whatifs.org import palace as P, memos as MEM, registry as REG, runner as RUN, wraps as WR, cite as CITE, canon as CANON

MIN = dt.timedelta(minutes=1)
def now(): return core.now_utc()
def st(): return core.store()
def EP(k=0): return "EP" + (now() + k * MIN).strftime("%Y%m%d%H%M")
def row(dept, trig, ep): return CITE._latest(st().rows("Sessions"), dept, trig, ep)
def act(r): return CITE._receipt(r, "ACT")

@pytest.fixture(autouse=True)
def _org():
    core.set_setting("ORG_SINCE", "2026-01-01T00:00:00Z")          # every episode id of these tests is born under the organisation
    yield

def room_fn(b):
    spine = M.ask("showrunner", "SHOWRUNNER RULES", "Choose the case.", fake_key="showrunner")
    bible = M.ask("bible", "BIBLE RULES", "Write the bible.", fake_key="bible")
    script = M.ask("writer", "WRITER RULES", "Write the narration.", fake_key="writer")
    return {"spine": spine, "bible": bible, "script": script}

def creative_episode(ep, d4=None, record=True):
    room = RUN.work("D4", "write", ep, d4 or room_fn, measure=WR.m_room)
    RUN.work("D5", "package", ep, lambda b: M.ask("packager", "PACKAGER RULES", "Package.", fake_key="packager"), measure=WR.m_pkg)
    RUN.work("D6", "plan", ep, lambda b: M.ask("director", "DIRECTOR RULES", "Shot list.", fake_key="director").get("shots", []), measure=WR.m_shots)
    if record: CANON.record(ep, room, RUN.last_session("D4", "write", ep))
    return room

def ctx(ep, room): return {"ep": ep, "room": room}

# ------------------------------------------------------------------ quotes
def test_a_quote_is_found_exactly_or_with_small_edits_and_never_when_short_or_absent():
    t = CITE.tokens("Nana Rosa sips her tea. Remember the last case: the pillows rose at noon and the city looked up.")
    assert CITE.found("the pillows rose at noon and the city", t)
    assert CITE.found("the pillows rose at exactly noon and the city looked", t)              # one word the final text lost: 9 of 10 in order
    assert not CITE.found("the pillows", t) and not CITE.found("the moon walked out of the courtroom forever", t)
    assert not CITE.found("city the and noon at rose pillows the", t)                          # the same words out of order are not a quote

def test_a_citation_counts_only_when_offered_and_quoted_from_the_output():
    out = {"script": "Line one here. Observe: three facts on my fingers and the third turns the case."}
    v = CITE.verify([{"id": "PI-A", "where": "three facts on my fingers and the third"}, {"id": "PI-B", "where": "a line the model never wrote anywhere"},
                     {"id": "PI-X", "where": "three facts on my fingers"}, {"id": "[PI-L]", "where": "three facts on my fingers and"}], ["PI-A", "PI-B", "PI-L"], {"PI-L"}, out)
    assert (v["verified"], v["unverified"], v["ghost"], v["limits"]) == (["PI-A"], ["PI-B"], ["PI-X"], ["PI-L"])

# ------------------------------------------------------------------ one doorway in, one doorway out
def test_the_playbook_enters_only_the_named_creative_calls_at_the_start_and_the_receipt_proves_it():
    spy = []
    def tap(task, system, prompt): spy.append((task, str(system))); return system
    M.ASK_TAPS.append(tap)
    try:
        ep = EP()
        room = RUN.work("D4", "write", ep, lambda b: dict(room_fn(b), judged=M.ask("jury", "JUDGE RULES", "[A]\n[B]", fake_key="jury"),
                                                       fixed=M.ask("humanize", "EDIT RULES", "NARRATION:\nx\nReturn JSON", fake_key="humanize")), measure=WR.m_room)
    finally: M.ASK_TAPS.remove(tap)
    by = dict(spy)
    for t, rules in (("showrunner", "SHOWRUNNER RULES"), ("bible", "BIBLE RULES"), ("writer", "WRITER RULES")):          # after the call's own rules, at the end of the system prompt
        assert by[t].startswith(rules) and "KNOWLEDGE PALACE" in by[t] and by[t].rstrip().endswith(CITE.RULE if t == "writer" else CITE.PROPOSE), t
    assert "KNOWLEDGE PALACE" not in by["jury"] and "KNOWLEDGE PALACE" not in by["humanize"]          # never the blind judges, never the mechanical passes
    assert "PROPOSAL (optional" in by["showrunner"] and "PROPOSAL (optional" not in by["writer"]
    r = row("D4", "write", ep); a = act(r)
    assert r["status"] == "ok" and r["inject"] == "prompt" and a["injected_tasks"] == ["bible", "showrunner", "writer"] and a["applied"] and a["cited"] >= 3
    assert "applied_items" not in room["script"] and "proposal" not in room["spine"]                    # the caller never sees what the reply tap took

def test_the_injected_block_never_changes_a_cached_layer_so_every_call_keeps_reading_the_same_cache():
    from whatifs import prompts as PR
    got = {}
    def tap(task, system, prompt): got[task] = system; return system
    brief = PR.Packed("HOUSE RULES\n", "THE WRITER'S BRIEF: bible, promise, rules\n", "")          # one brief shared by the writer, the rewrite and the mechanical passes
    def work(b):
        s = M.ask("writer", brief, "Write the narration.", fake_key="writer"); M.ask("rewrite", brief, "Apply the fixes.", fake_key="writer")
        M.ask("retention", brief, "NARRATION:\nx", fake_key="retention"); M.ask("format", brief, "NARRATION:\nx", fake_key="retention")
        return {"spine": {}, "bible": {}, "script": s}
    M.ASK_TAPS.append(tap)
    try: RUN.work("D4", "write", EP(), work, measure=WR.m_room)
    finally: M.ASK_TAPS.remove(tap)
    assert {(s.glob, s.episode) for s in got.values()} == {(brief.glob, brief.episode)}                 # byte-identical cached layers for all four calls
    assert "KNOWLEDGE PALACE" in got["writer"].role and "KNOWLEDGE PALACE" in got["rewrite"].role and got["retention"].role == "" and got["format"].role == ""

def test_the_reply_doorway_runs_on_the_real_model_path_too(monkeypatch):
    seen = []
    def spy(task, res): seen.append((task, dict(res))); return res
    monkeypatch.setattr(M, "FAKE", False)
    monkeypatch.setattr(M, "_claude", lambda *a, **k: '{"titles": ["x"], "applied_items": []}')
    monkeypatch.setattr(M, "_gemini", lambda *a, **k: '{"titles": ["x"], "applied_items": []}')
    import whatifs.governor as _G
    monkeypatch.setattr(_G, "monthly_cap_reached", lambda **k: False)
    M.REPLY_TAPS.append(spy)
    try: out = M.ask("packager", "SYSTEM", "Package.", episode="EPX")
    finally: M.REPLY_TAPS.remove(spy)
    assert out["titles"] == ["x"] and seen and seen[0][0] == "packager" and "applied_items" in seen[0][1]

def test_a_run_that_cites_nothing_it_wrote_fails_palace_cited_and_a_good_one_passes(monkeypatch):
    ep = EP(); room = creative_episode(ep)
    assert CON.p_palace_injected(ctx(ep, room))[0] == "PASS" and CON.p_palace_cited(ctx(ep, room))[0] == "PASS"
    real = FK.fake_cite
    def liar(res, system):
        out = real(res, system)
        if isinstance(out, dict) and out.get("titles"): out["applied_items"] = [dict(c, where="a quote this packager never wrote anywhere at all") for c in out.get("applied_items") or []]
        return out
    monkeypatch.setattr(FK, "fake_cite", liar)
    ep2 = EP(1); room2 = creative_episode(ep2)
    res = CON.p_palace_cited(ctx(ep2, room2))
    assert res[0] == "FAIL" and "D5 'package': no verified citation" in res[1]
    assert act(row("D5", "package", ep2))["unverified"] and not act(row("D5", "package", ep2))["applied"]

def test_a_ghost_id_is_recorded_never_counted(monkeypatch):
    real = FK.fake_cite
    monkeypatch.setattr(FK, "fake_cite", lambda res, system: dict(real(res, system), applied_items=[{"id": "PI-0000000000", "where": "A floating pillow over a city, shot 0"}]) if isinstance(res, dict) and res.get("shots") else real(res, system))
    ep = EP(); creative_episode(ep)
    a = act(row("D6", "plan", ep))
    assert a["ghost"] == ["PI-0000000000"] and not a["applied"] and row("D6", "plan", ep)["status"] == "ok"      # the model's word is not the department's code: recorded, not a breach
    assert CON.p_palace_cited(ctx(ep, {}))[0] == "FAIL"

def test_palace_injected_fails_when_a_creative_run_never_put_the_playbook_in_a_prompt():
    ep = EP(); creative_episode(ep)
    core.set_setting("ORG_PROMPT_INJECT", "FALSE")
    assert CON.p_palace_injected(ctx(ep, {}))[0] == CON.NA and CON.p_canon_in_brief(ctx(ep, {}))[0] == CON.NA      # switched off: says so, never a fake PASS
    ep2 = EP(1); RUN.work("D6", "plan", ep2, lambda b: M.ask("director", "D", "Shot list.", fake_key="director").get("shots", []), measure=WR.m_shots)
    core.set_setting("ORG_PROMPT_INJECT", "TRUE")
    RUN.work("D4", "write", ep2, room_fn, measure=WR.m_room)
    RUN.work("D5", "package", ep2, lambda b: M.ask("packager", "P", "Package.", fake_key="packager"), measure=WR.m_pkg)
    res = CON.p_palace_injected(ctx(ep2, {}))
    assert res[0] == "FAIL" and "D6 'plan' ran in 'brief' mode" in res[1]

def test_palace_injected_fails_when_the_key_call_did_not_carry_it():
    ep = EP()
    RUN.work("D4", "write", ep, lambda b: {"spine": {}, "bible": M.ask("bible", "B", "Write the bible.", fake_key="bible"), "script": {"script": "x"}}, measure=WR.m_room)
    RUN.work("D5", "package", ep, lambda b: M.ask("packager", "P", "Package.", fake_key="packager"), measure=WR.m_pkg)
    RUN.work("D6", "plan", ep, lambda b: M.ask("director", "D", "Shot list.", fake_key="director").get("shots", []), measure=WR.m_shots)
    res = CON.p_palace_injected(ctx(ep, {}))
    assert res[0] == "FAIL" and "did not reach its key call 'writer'" in res[1]

def test_a_creative_run_with_no_model_call_breaks_the_contract():
    ep = EP(); RUN.work("D5", "package", ep, lambda b: {"titles": ["typed by hand"]}, measure=WR.m_pkg)
    r = row("D5", "package", ep)
    assert r["status"] == "breach" and "no model call of this run carried the playbook" in r["error"]

# ------------------------------------------------------------------ the canon
def test_the_case_record_is_written_by_code_and_becomes_canon_only_on_air():
    ep = EP(); room = creative_episode(ep)
    r = P.get(CANON.case_id(ep))
    assert r["status"] == "proposed" and r["kind"] == "world_canon" and CANON.is_case(r) and not P.aired(r)
    assert "Every pillow stands accused" in r["summary"] and "Prototype No. 41" in r["summary"] and "Promised next" in r["summary"]
    assert r["derived_from"] == [row("D4", "write", ep)["id"]] and not P.servable(r, now())
    assert CANON.on_air(ep, "vid-1") and P.get(CANON.case_id(ep))["status"] == "accepted" and P.aired(P.get(CANON.case_id(ep)))
    assert not CANON.on_air(ep, "vid-1")                                                              # once
    room["spine"]["show_plan"]["charge"] = "A rewritten charge after the upload."
    assert CANON.record(ep, room) == CANON.case_id(ep) and "Every pillow stands accused" in P.get(CANON.case_id(ep))["summary"]      # what aired is never rewritten

def test_d9_may_make_only_the_on_air_move_and_only_on_a_show_record():
    a = P.add({"key": "t.idea", "kind": "technique", "title": "An idea someone proposed", "summary": "A technique that waits for the Council to decide on it.",
               "departments": ["D4"], "evidence": [{"source": "a test", "date": "2026-11-01", "type": "practice"}]}, "D4")
    with pytest.raises(P.PalaceError): P.transition(a["id"], "accepted", "D9", "the platform took the upload")
    c = P.add({"key": "t.canon", "kind": "world_canon", "title": "Canon that rests on opinion", "summary": "A claimed piece of lore with no show record behind it at all.",
               "departments": ["D4"], "evidence": [{"source": "a test", "date": "2026-11-01", "type": "opinion"}]}, "D4")
    with pytest.raises(P.PalaceError): P.transition(c["id"], "accepted", "D9", "the platform took the upload")
    with pytest.raises(P.PalaceError): P.transition(c["id"], "accepted", "D4", "the writer says so")

def test_the_next_script_pays_the_continuity_debt_and_canon_in_brief_proves_it():
    ep1 = EP(); creative_episode(ep1); CANON.on_air(ep1, "vid-1")
    spy = []
    def tap(task, system, prompt): spy.append((task, str(system))); return system
    M.ASK_TAPS.append(tap)
    try: ep2 = EP(1); room2 = creative_episode(ep2)
    finally: M.ASK_TAPS.remove(tap)
    by = dict(spy); cid = CANON.case_id(ep1)
    assert f"MUST CITE (continuity): [{cid}]" in by["writer"] and "MUST CITE" not in by["bible"]
    assert CITE._receipt(row("D4", "write", ep2), "LOAD")["must"] == [cid]
    res = CON.p_canon_in_brief(ctx(ep2, room2))
    assert res[0] == "PASS" and "callback in the script" in res[1], res
    lost = dict(room2, script={"script": "\n".join(l for l in room2["script"]["script"].split("\n") if "Remember the last case" not in l)})
    res = CON.p_canon_in_brief(ctx(ep2, lost))
    assert res[0] == "FAIL" and "is not in the final script" in res[1]                               # a later pass edited the callback away

def test_canon_in_brief_fails_without_the_case_record_and_when_the_debt_was_not_cited(monkeypatch):
    ep1 = EP(); creative_episode(ep1); CANON.on_air(ep1, "vid-1")
    ep2 = EP(1); room2 = creative_episode(ep2, record=False)
    res = CON.p_canon_in_brief(ctx(ep2, room2))
    assert res[0] == "FAIL" and "no case record" in res[1]
    real = FK.fake_cite
    monkeypatch.setattr(FK, "fake_cite", lambda res, system: real(res, system.replace("MUST CITE (continuity)", "must cite later")))
    ep3 = EP(2); room3 = creative_episode(ep3)
    res = CON.p_canon_in_brief(ctx(ep3, room3))
    assert res[0] == "FAIL" and ("continuity debt was not paid" in res[1] or "does not name that case" in res[1]), res      # an unrelated line cited as the callback is not a callback
    monkeypatch.setattr(FK, "fake_cite", lambda res, system: dict(real(res, system), applied_items=[c for c in real(res, system).get("applied_items") or [] if c["id"] != CANON.case_id(ep1)]) if isinstance(res, dict) else res)
    ep4 = EP(3); room4 = creative_episode(ep4)
    res = CON.p_canon_in_brief(ctx(ep4, room4))
    assert res[0] == "FAIL" and "continuity debt was not paid" in res[1]

def test_canon_in_brief_fails_when_the_writers_playbook_lacked_the_canon():
    ep1 = EP(); creative_episode(ep1); CANON.on_air(ep1, "vid-1")
    core.set_setting("PALACE_CANON_TOKENS", "100")                                                     # too small for the cast and the case
    ep2 = EP(1); room2 = creative_episode(ep2)
    res = CON.p_canon_in_brief(ctx(ep2, room2))
    assert res[0] == "FAIL" and "lacked" in res[1]

def test_the_canon_has_its_own_budget_and_never_pushes_a_limit_out():
    P.ensure_seed(); CANON.ensure_cast()
    ep = EP(); CANON.record(ep, {"spine": {"premise": "What if the Moon walked out?", "show_plan": {"charge": "The Moon is charged with leaving.", "verdict": {"winner": "vale"}}}, "script": {"script": "x"}})
    CANON.on_air(ep, "vid-1")
    rs = P.rows(); pb = P.playbook("D4", rs=rs, record=False)
    no_canon = P.playbook("D4", rs=[r for r in rs if r["kind"] != "world_canon"], record=False)
    assert pb["limits_left_out"] == no_canon["limits_left_out"] and pb["cap"] > no_canon["cap"] and pb["tokens"] <= pb["cap"]
    assert set(CANON.cast_ids()) <= set(pb["items"]) and CANON.case_id(ep) in pb["items"]
    lanes = [P._lane(next(r for r in rs if r["id"] == i)) for i in pb["items"]]
    assert lanes == sorted(lanes) and not P.playbook_issues(pb, rs, now())                            # limits, then canon, then knowledge

def test_the_mirror_never_overwrites_a_case_record():
    ep = EP(); CANON.record(ep, {"spine": {"premise": "What if gravity took a day off?", "show_plan": {"charge": "Gravity is charged with absence.", "stinger": "Next: the Moon."}}, "script": {"script": "Prototype No. 7"}})
    CANON.on_air(ep, "vid-1"); before = P.get(CANON.case_id(ep))
    st().append("Episodes", [{"episode_id": ep, "status": "LIVE", "yt_id": "vid-1", "premise": "other"}]); st().append("Show_Log", [{"episode_id": ep, "verdict_winner": "grimm"}])
    P.sync_canon()
    after = P.get(CANON.case_id(ep))
    assert after["version"] == before["version"] and after["summary"] == before["summary"] and P.aired(after)

# ------------------------------------------------------------------ creative memos
def test_proposals_become_distinct_creative_memos_for_the_council():
    idea = {"kind": "world_building", "idea": "Nana Rosa keeps a jar of confiscated prototypes that grows every case.", "rationale": "A visible tally rewards viewers who watch every case."}
    other = {"kind": "experiment", "idea": "Open one case in total silence for three seconds before the first line.", "rationale": "Silence before the hook may lift the first ten seconds."}
    out, s = CITE.proposals_to_memos("D4", [idea, dict(idea), {"kind": "nonsense", "idea": "x" * 30, "rationale": "y" * 30}])
    assert len(out) == 1 and s == {"proposals": 3, "kept": 1, "dropped_same": 1, "dropped_invalid": 1}
    MEM.write(dict(out[0], session_id="S-TEST"))
    out2, s2 = CITE.proposals_to_memos("D5", [dict(idea, idea=idea["idea"] + " Again."), other])
    assert [m["body"]["idea"] for m in out2] == [other["idea"]] and s2["dropped_same"] == 1
    assert CITE.proposals_to_memos("D8", [other])[0] == []                                           # only the creative departments propose
    m = MEM.rows()[0]; assert m["type"] == "creative_memo" and m["to_depts"] == ["C"] and not m["owner_visible"]

def test_a_creative_run_sends_one_proposal_and_never_takes_one_from_a_call_not_invited(monkeypatch):
    ep = EP(); creative_episode(ep)
    cm = [m for m in MEM.rows() if m["type"] == "creative_memo"]
    assert len(cm) == 1 and cm[0]["from_dept"] == "D4" and cm[0]["session_id"] == row("D4", "write", ep)["id"]
    real = FK.fake_cite
    monkeypatch.setattr(FK, "fake_cite", lambda res, system: dict(real(res, system), proposal={"kind": "idea", "idea": "The writer slips an idea in uninvited every time.", "rationale": "Only invited calls may propose to the Council."}) if isinstance(res, dict) else res)
    ep2 = EP(1); RUN.work("D4", "write", ep2, lambda b: {"spine": {}, "bible": {}, "script": M.ask("writer", "W", "Write.", fake_key="writer")}, measure=WR.m_room)
    assert len([m for m in MEM.rows() if m["type"] == "creative_memo"]) == 1

# ------------------------------------------------------------------ pre-production drafts
def test_a_draft_is_adopted_only_with_its_own_runs_proof():
    d = "DRAFT" + now().strftime("%Y%m%d%H%M")
    room = RUN.work("D4", "draft", d, room_fn, measure=WR.m_room); sid = RUN.last_session("D4", "draft", d)
    ep = EP(); RUN.work("D4", "write", ep, lambda b: room, measure=WR.m_room, adopt=sid)
    a = act(row("D4", "write", ep))
    assert row("D4", "write", ep)["status"] == "ok" and a["adopted"] == sid and a["injected"].startswith(f"adopted draft run {sid}") and a["applied"]
    assert CITE.creative_runs(ep)[0][2]["id"] == sid
    ep2 = EP(1); RUN.work("D4", "write", ep2, lambda b: room, measure=WR.m_room, adopt="S-NOSUCHRUN")
    assert row("D4", "write", ep2)["status"] == "breach" and "has no proof that the playbook reached it" in row("D4", "write", ep2)["error"]
    core.set_setting("ORG_PROMPT_INJECT", "FALSE"); d2 = d + "9"
    RUN.work("D4", "draft", d2, room_fn, measure=WR.m_room); sid2 = RUN.last_session("D4", "draft", d2); core.set_setting("ORG_PROMPT_INJECT", "TRUE")
    ep3 = EP(2); RUN.work("D4", "write", ep3, lambda b: room, measure=WR.m_room, adopt=sid2)
    assert row("D4", "write", ep3)["status"] == "breach" and "brief mode" in row("D4", "write", ep3)["error"]

def _draft_row(did, note, room):
    st().append("Script_Previews", [{"draft_id": did, "created": core.iso(), "status": "APPROVED", "room_json": PV._pack({"d": {}, "room": room}), "note": note}])

def test_an_automatic_draft_without_the_palace_is_written_again_and_the_owners_own_approval_stands():
    core.set_setting("PREPROD_ON", "TRUE"); core.set_setting("PREVIEW_USE_APPROVED", "TRUE")
    _draft_row("DRAFT1", "pre-production (auto, half-price batch); x", {"script": {"script": "old"}})
    assert PV.take_approved("EPA") is None and st().rows("Script_Previews")[0]["status"] == "SUPERSEDED"
    _draft_row("DRAFT2", "owner approved", {"script": {"script": "his"}})
    d, room = PV.take_approved("EPB")
    assert room["_legacy_draft"] == "DRAFT2" and st().rows("Script_Previews")[1]["status"] == "USED"
    ep = EP(); RUN.work("D4", "write", ep, lambda b: room, measure=WR.m_room, legacy=room["_legacy_draft"])
    r = row("D4", "write", ep); assert r["status"] == "ok" and r["inject"] == "brief" and act(r)["legacy_draft"] == "DRAFT2"
    RUN.work("D5", "package", ep, lambda b: M.ask("packager", "P", "Package.", fake_key="packager"), measure=WR.m_pkg)
    RUN.work("D6", "plan", ep, lambda b: M.ask("director", "D", "Shot list.", fake_key="director").get("shots", []), measure=WR.m_shots)
    res = CON.p_palace_injected(ctx(ep, room)); assert res[0] == "PASS" and "owner-approved draft DRAFT2" in res[1]
    assert CON.p_canon_in_brief(ctx(ep, room))[0] == CON.NA

def test_the_real_preproduction_job_writes_under_d4_and_production_can_adopt_it():
    core.set_setting("PREPROD_ON", "TRUE")
    out = PV.run(mode="preprod")
    assert out["ok"], out
    r = row("D4", "draft", out["draft"]); assert r["status"] == "ok" and r["inject"] == "prompt" and "writer" in act(r)["injected_tasks"]
    d, room = PV.take_approved(EP())
    assert room["org_session"] == r["id"]

# ------------------------------------------------------------------ money, settings, registry
def test_the_palace_in_the_prompts_is_counted_in_every_estimate():
    from whatifs import episode as EPI
    per = EPI.est_cost_inr({"stills": 52, "living": 8, "kling": 4, "episode_id": "EPC"})
    assert G.plan_for_episode(per, 4)["tier"] == "full" and 4 * per < 0.5 * core.S("BUDGET_CEILING_INR", float)      # at the owner's cadence (4 long videos a month) it never costs a picture
    on = G.voice_think_inr(); lines_on = CG.estimate_lines()["ai_writing"]
    core.set_setting("ORG_PROMPT_INJECT", "FALSE")
    assert G.palace_prompt_inr() == 0 and round(on - G.voice_think_inr(), 2) == core.S("PALACE_PROMPT_EST_INR", float) > 0
    assert round(lines_on - CG.estimate_lines()["ai_writing"], 1) == core.S("PALACE_PROMPT_EST_INR", float)

def test_the_writers_cap_moves_once_and_never_over_the_owners_value():
    core.set_setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT", "")
    assert MG.v12b6a_upgrade(st()) == ["PALACE_PLAYBOOK_TOKENS_BY_DEPT"] and json.loads(core.S("PALACE_PLAYBOOK_TOKENS_BY_DEPT")) == {"D4": 2400}
    core.set_setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT", "")
    assert MG.v12b6a_upgrade(st()) == [] and core.S("PALACE_PLAYBOOK_TOKENS_BY_DEPT") == ""                 # never twice
    core.set_setting("V12B6A_FLIPS_DONE", ""); core.set_setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT", '{"D4": 3000}')
    assert MG.v12b6a_upgrade(st()) == [] and core.S("PALACE_PLAYBOOK_TOKENS_BY_DEPT") == '{"D4": 3000}'       # the owner's value stands

def test_the_registry_refuses_a_prompt_spec_that_points_nowhere(monkeypatch):
    assert not REG.data_issues()
    bad = dict(REG.PROMPT, D5={"package": {"tasks": ("packager",), "key": "titler", "propose": ("director",), "must": ()}}, D7={"voice2": {"tasks": ("x",), "key": "x"}})
    monkeypatch.setattr(REG, "PROMPT", bad)
    p = " | ".join(REG.data_issues())
    assert "key call 'titler'" in p and "'director' is not one of its injected calls" in p and "D7 'voice2', which is not a wired call site" in p

def test_the_fake_model_only_cites_when_the_rule_is_in_its_prompt():
    res = {"titles": ["What if every pillow floated away at once tonight?"]}
    assert FK.fake_cite(dict(res), "no rule here") == res
    sysm = "KNOWLEDGE PALACE\n- [PI-0123456789] ACCEPTED: open on stakes\n" + CITE.RULE
    out = FK.fake_cite(dict(res), sysm)
    assert out["applied_items"] == [{"id": "PI-0123456789", "where": "What if every pillow floated away at once tonight?"}] and "proposal" not in out

def test_a_knowledge_lever_for_a_creative_department_is_verified_only_by_a_later_cited_use():
    from whatifs.org import execute as EXE
    director = lambda b: M.ask("director", "DIRECTOR RULES", "Shot list.", fake_key="director").get("shots", [])
    t = MEM.write({"type": "ticket", "from_dept": "C", "to_depts": ["D6"], "subject": "Serve the director one new technique",
                   "body": {"lever_class": "A", "target": "palace:t6-push", "acceptance_test": "a later shot plan cites it with a quote from its shots", "rollback": "retire the item",
                            "value": {"kind": "technique", "title": "A slow push in over the city", "departments": ["D6"], "stages": ["visual"],
                                      "summary": "Hold a slow push in on the floating object over the city, the camera drifting, instead of a locked frame.",
                                      "evidence": [{"source": "a test", "date": core.iso()[:10], "type": "build record"}]}}, "done_when": "a later shot plan cited it"})
    ep = EP(); RUN.work("D6", "plan", ep, director, measure=WR.m_shots)                                  # the run that applies the ticket can never be its proof
    assert EXE._get(t["id"], st())["need"] == "cited" and EXE._get(t["id"], st())["state"] == "applied"
    RUN.work("D6", "assets", ep, lambda b: {"img": {"a": 1}}, measure=WR.m_assets); RUN.work("D6", "render", ep, lambda b: "", measure=lambda o: {"master_made": 0, "frames": 1})
    EXE.reconcile(); assert EXE._get(t["id"], st())["state"] == "applied"                               # served to code-only runs: neither proof nor a used-up window
    RUN.work("D6", "plan", EP(1), director, measure=WR.m_shots); EXE.reconcile()
    row = EXE._get(t["id"], st()); assert row["state"] == "verified" and row["proof"].endswith("and cited it"), (row["state"], row["proof"])
    core.set_setting("ORG_PROMPT_INJECT", "FALSE"); assert not REG.prompted("D6") and REG.prompted("D6") is False

# ------------------------------------------------------------------ open issue 47 (the Script Room's similarity guard)
def test_a_script_is_never_similar_to_its_own_earlier_draft_and_a_copy_of_another_episode_still_is(monkeypatch):
    from whatifs import similarity as SIM, notify as NT
    sent = []; monkeypatch.setattr(NT, "send", lambda *a, **k: sent.append(a) or "x")
    text = " ".join(f"line {i} the pillows rose over the city at noon and nobody could explain the number {i * 7}" for i in range(40))
    assert SIM.check(text, "EP1") == (0.0, "")
    assert SIM.check(text, "EP1") == (0.0, "") and not sent                                          # scripted twice: not 'similar to itself', no owner message
    assert [r["episode_id"] for r in st().rows("Script_Fingerprints")] == ["EP1"]                     # one fingerprint per episode
    best, who = SIM.check(text, "EP2")
    assert who == "EP1" and best > core.S("SCRIPT_SIMILARITY_MAX", float) and sent and sent[0][0] == "similar_script"      # a copy of ANOTHER episode is still caught
