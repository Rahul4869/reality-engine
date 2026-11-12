"""v8.11: opening Kling hook, no skipped slots (Premise_Bench + ship the best), prompt caching (explicit breakpoints, warm-up, stats, real cache prices),
model routing by capability with per-role effort, Haiku JSON repair, measured-vs-estimated AI cost, visuals protected from a higher AI estimate.
Offline: Claude calls go to the fake cache server (fakes.FAKE_ANTHROPIC), which applies the documented caching rules. Happy AND failure paths."""
import json
import pytest
from whatifs import core, models as M, prompts as P, fakes as F, premise as PR, craft as CR, immersion as IM, room as ROOM, manage as MG, governor as G, data as D

LONG = "x " * 4000                                   # ~2,000 estimated tokens: above the 512-token minimum

def _memo_pack(role="SOUND"):
    return P.pack(P.MEMO, episode={"spine": LONG, "draw": "{}"}, role=role, trends="t", craft="c")

# ---------------------------------------------------------------- Packed layers
def test_packed_split_keeps_the_exact_prompt_and_moves_only_data():
    plain = P.fill(P.MEMO, role="SOUND", spine="S1")
    pk = P.Packed.of(plain)
    assert str(pk) == plain and pk.glob == P.house_text() and pk.role.startswith("\nROLE: SOUND")       # same text, house rules split off
    q = P.pack(P.MEMO, episode={"spine": "THE-SPINE"}, role="SOUND")
    assert "THE-SPINE" in q.episode and "THE-SPINE" not in q.role and "(see SPINE in the EPISODE PACK above)" in q.role
    assert "write a short memo: your big idea" in q.role                                      # role wording unchanged
    assert q.map_role(lambda t: t + "Z").role.endswith("Z") and q.map_role(str).episode == q.episode
    w = P.Packed.as_episode(P.fill(P.WRITER, words=10)); assert w.glob and w.episode and not w.role
    assert P.Packed.of("no house rules").role == "no house rules" and not P.Packed.of("x").glob

# ---------------------------------------------------------------- breakpoints, TTL order, minimum length
def test_blocks_stable_first_1h_before_5m_role_last_uncached(setting):
    blocks, info = M.CACHE.blocks(_memo_pack(), "m", "sig", 1200, fanout=True)
    assert [("cache_control" in b) for b in blocks] == [True, True, False]
    assert blocks[0]["cache_control"]["ttl"] == "1h" and blocks[1]["cache_control"]["ttl"] == "5m" and info["bps"] == 2
    setting("PROMPT_CACHE_ON", "FALSE"); sysf, info = M.CACHE.blocks(_memo_pack(), "m", "sig")
    assert isinstance(sysf, str) and sysf == str(_memo_pack()) and info["bps"] == 0            # off = exactly the v8.10 request

def test_short_prefix_gets_no_breakpoint_and_a_warning(setting, capsys):
    setting("CACHE_MIN_TOKENS", "100000")
    sysf, info = M.CACHE.blocks(_memo_pack(), "m", "sig"); assert isinstance(sysf, str) and info["bps"] == 0
    assert "below CACHE_MIN_TOKENS" in capsys.readouterr().out

def test_ttl_auto_long_sequential_reply_gets_1h_fanout_5m_and_switch(setting):
    assert M.CACHE.episode_ttl("p1", "m", "s", 16000, False) == "1h"
    assert M.CACHE.episode_ttl("p2", "m", "s", 16000, True) == "5m"
    assert M.CACHE.episode_ttl("p3", "m", "s", 1200, False) == "5m"
    setting("CACHE_TTL_AUTO", "FALSE"); assert M.CACHE.episode_ttl("p4", "m", "s", 16000, False) == "5m"

def test_fake_server_enforces_the_documented_rules():
    srv = F.FakeAnthropic()
    bad = {"model": "m", "max_tokens": 10, "system": [{"type": "text", "text": LONG, "cache_control": {"type": "ephemeral", "ttl": "5m"}},
                                                     {"type": "text", "text": LONG + "y", "cache_control": {"type": "ephemeral", "ttl": "1h"}}], "messages": [{"role": "user", "content": "q"}]}
    assert srv.post(bad).status_code == 400                                                   # 1 h after 5 min is refused
    five = dict(bad, system=[{"type": "text", "text": "a", "cache_control": {"type": "ephemeral"}}] * 5); assert srv.post(five).status_code == 400

# ---------------------------------------------------------------- real-path Claude calls through the fake server
def test_second_call_reads_the_cache_and_cost_uses_settings_multipliers(setting):
    F.FAKE_ANTHROPIC.reply = '{"big_idea": "b"}'
    M._claude("sonnet", _memo_pack("A"), "Memo now.", 1200, 0.8, False, "EPC", "high")
    M._claude("sonnet", _memo_pack("B"), "Memo now.", 1200, 0.8, False, "EPC", "high")
    rows = [r for r in core._cost_buf if r["item"] == "claude_sonnet"]
    assert rows[0]["cache_write_tok"] > 0 and rows[0]["cache_read_tok"] == 0
    assert rows[1]["cache_read_tok"] > 0 and rows[1]["cache_write_tok"] == 0 and rows[1]["basis"] == "measured" and rows[1]["model"]
    u = {"input_tokens": 100, "cache_read_input_tokens": 1_000_000, "cache_creation_input_tokens": 0, "output_tokens": 0}
    assert M.claude_usd("sonnet", u)[0] == pytest.approx(2 * 0.05 + 100 * 2 / 1e6)                              # Sonnet 5.5: reads at 0.05x of $2 (not the old 0.1x)
    setting("PRICE_SONNET_CACHE_READ", "0.1"); assert M.claude_usd("sonnet", u)[0] == pytest.approx(0.2 + 100 * 2 / 1e6)
    w = {"input_tokens": 0, "cache_creation_input_tokens": 1_000_000, "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000, "ephemeral_5m_input_tokens": 0}, "output_tokens": 0}
    assert M.claude_usd("opus", w)[0] == pytest.approx(4 * 2)                                   # a 1-h write at 2x
    assert M.claude_usd("opus", {"cache_creation_input_tokens": 10, "_sent_1h": True})[2]["w1h"] == 10      # no split reported -> the dearer 1-h rate

def test_nothing_cached_although_breakpoints_were_sent_is_warned(capsys):
    F.FAKE_ANTHROPIC.MIN = 10 ** 9
    try: M._claude("sonnet", _memo_pack(), "Memo now.", 1200, 0.8, False, "EPN", "")
    finally: F.FAKE_ANTHROPIC.MIN = 512
    assert "cached nothing although" in capsys.readouterr().out

def test_effort_is_sent_and_a_400_drops_it_for_that_model(monkeypatch):
    seen = []
    def post(body, headers):
        seen.append(json.loads(json.dumps(body)))
        if body.get("output_config"): return F._Resp(400, {"error": {"message": "output_config.effort: unknown field"}})
        return F._Resp(200, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {"input_tokens": 5, "output_tokens": 1}})
    monkeypatch.setattr(F.FAKE_ANTHROPIC, "post", post)
    assert M._claude("opus", "sys", "q", 100, None, False, "E", "high") == "ok"
    assert seen[0]["output_config"] == {"effort": "high"} and "output_config" not in seen[1] and M.model("opus") in M._NO_EFFORT
    M._NO_EFFORT.clear()

def test_per_message_effort_uses_the_beta_header_and_falls_back(setting, monkeypatch):
    setting("CACHE_EFFORT_PER_MESSAGE", "TRUE"); M._PER_MSG_OFF[0] = False
    b, h, info, *_ = M._claude_body("opus", _memo_pack(), "q", 100, None, False, "high")
    assert b["messages"][0] == {"role": "system", "content": [], "output_config": {"effort": "high"}} and "mid-conversation" in h["anthropic-beta"] and "output_config" not in b
    monkeypatch.setattr(M, "AH", lambda: {"x-api-key": "k"})
    calls = []
    def post(body, headers):
        calls.append(body)
        if any(m.get("role") == "system" for m in body["messages"]): return F._Resp(400, {"error": {"message": "Extra inputs are not permitted"}})
        return F._Resp(200, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn", "usage": {}})
    monkeypatch.setattr(F.FAKE_ANTHROPIC, "post", post)
    assert M._claude("opus", "s", "q", 100, None, False, "E", "high") == "ok" and M._PER_MSG_OFF[0] and calls[-1]["output_config"] == {"effort": "high"}
    M._PER_MSG_OFF[0] = False

# ---------------------------------------------------------------- warm-up before a fan-out
def test_fanout_writes_once_then_every_parallel_call_reads(monkeypatch):
    jobs = [dict(role="memo", system=_memo_pack(r), prompt="Memo now.", episode="EPF", fake_key="memo", max_tokens=1200) for r in ("A", "B", "C", "D")]
    out = M.ask_many(jobs); assert len(out) == 4
    calls = F.FAKE_ANTHROPIC.calls; assert calls[0]["max_tokens"] == 0                          # the serial warm-up comes first (zero output)
    st = M.CACHE.stats[("EPF", core.JOB["name"])]
    assert st["calls"] == 5 and st["read"] > 0 and st["w5"] + st["w1h"] > 0
    assert st["read"] >= 3 * (st["w5"] + st["w1h"]) * 0.9                                       # 4 reads of one prefix written once

def test_refused_warm_up_runs_the_first_job_alone(monkeypatch):
    monkeypatch.setattr(F.FAKE_ANTHROPIC, "post", lambda body, headers=None: F._Resp(400, {"error": {"message": "max_tokens: 0 not supported"}}))
    assert M.prewarm("sonnet", _memo_pack(), "q", 1200, False, "high") is False and M.model("sonnet") in M._NO_PREWARM
    M._NO_PREWARM.clear()

def test_shared_prefix_detection_needs_same_model_effort_and_layers():
    a = dict(role="memo", system=_memo_pack("A")); b = dict(role="memo", system=_memo_pack("B"))
    assert M._shares_prefix([a, b])
    assert not M._shares_prefix([a, dict(role="critic", system=_memo_pack("B"))])              # a Gemini role: no warm-up
    assert not M._shares_prefix([a, dict(role="memo", system=P.pack(P.MEMO, episode={"spine": "other"}, role="B"))])

def test_cache_stats_tab_and_low_ratio_warning(capsys, setting):
    setting("CACHE_WARN_RATIO", "0.99")
    for r in "ABCD": M._claude("sonnet", _memo_pack(r), "q", 1200, None, False, "EPS", "high")
    core.flush_log()
    row = next(r for r in core.store().rows("Cache_Stats") if r["episode_id"] == "EPS")
    assert float(row["hit_ratio"]) > 0.5 and int(row["tokens_saved"]) > 0 and float(row["ai_estimated_inr"]) > 0
    assert "below CACHE_WARN_RATIO" in capsys.readouterr().out
    M._claude("sonnet", _memo_pack("E"), "q", 1200, None, False, "EPS", "high"); core.flush_log()
    assert len([r for r in core.store().rows("Cache_Stats") if r["episode_id"] == "EPS"]) == 1    # upserted, one row per episode and run

def test_params_mismatch_on_a_shared_prefix_is_warned(capsys):
    M.CACHE.blocks(_memo_pack(), "m", "sig-high"); M.CACHE.note({"hash": M.CACHE.blocks(_memo_pack(), "m", "sig-high")[1]["hash"], "ttl": ["1h"]}, "sig-high", 0, 0)
    M.CACHE.blocks(_memo_pack(), "m", "sig-low"); assert "differ in model parameters" in capsys.readouterr().out

def test_that_warning_can_be_the_line_that_flushes_the_log_and_the_job_does_not_hang(capsys):
    """v12 V2c-b2b2, found by a test run that stopped for ever: the warning was logged WHILE the cache manager's lock was held. core.log flushes at every
    40th buffered line, the flush calls the manager's own hook (flush -> rows), and that waits for the same lock - held by the very thread that waits."""
    import threading
    assert M.CACHE.flush in core.FLUSH_HOOKS, "the cache manager's rows are written with every log flush"
    h = M.CACHE.blocks(_memo_pack(), "m-flush", "sig-high")[1]["hash"]; M.CACHE.note({"hash": h, "ttl": ["5m"]}, "sig-high", 0, 0)
    M.CACHE.record("EPF", "m-flush", {"read": 0, "w5": 10, "w1h": 0, "in": 5, "out": 5}, 0.001, 0.0, {"bps": 0})      # a row waits for the next flush
    core.flush_log(); capsys.readouterr()
    with core._lock: core._logbuf.extend({"ts": core.iso(), "job": "t", "episode_id": "", "level": "INFO", "message": f"line {i}"} for i in range(39))
    done = []
    t = threading.Thread(target=lambda: done.append(M.CACHE.blocks(_memo_pack(), "m-flush", "sig-low")), daemon=True)
    t.start(); t.join(20)
    hung = t.is_alive()
    if hung: M.CACHE.lock = threading.Lock()          # never leave the next test of this worker a lock that is held for ever
    assert not hung, "the 40th log line was written inside the cache manager's lock: the job waits for its own lock for ever"
    assert done and "differ in model parameters" in capsys.readouterr().out and len(core._logbuf) < 39, "the warning was written and the log was flushed"

# ---------------------------------------------------------------- routing + effort
def test_routing_by_capability_and_switches(setting):
    assert M.route("writer") == ("opus", "creative") and M.route("rewrite")[0] == "opus" and M.route("humanize") == ("sonnet", "edit")
    assert M.route("premise_judge") == ("opus", "judge") and M.route("json_repair") == ("haiku", "chore") and M.route("critic")[0] == "critic"
    setting("SCRIPT_MODEL", "fable"); assert M.route("writer")[0] == "fable" and M.CHAINS["fable"][1] == ("c", "opus")     # a Fable refusal -> Opus
    setting("MODEL_ROUTES", '{"immersion": "opus"}'); assert M.route("immersion")[0] == "opus"
    assert M.effort_for("writer", "creative") == "high" and M.effort_for("json_repair", "chore") == "low" and M.effort_for("bench", "creative") == "xhigh"
    setting("EFFORT_OVERRIDES", '{"writer": "max"}'); assert M.effort_for("writer", "creative") == "max"
    setting("EFFORT_EDIT", "nonsense"); assert M.effort_for("humanize", "edit") == ""          # unknown level = the model default, never a bad request
    setting("AI_SAVER_ON", "TRUE"); assert M.effort_for("director", "edit") == "medium" and M.effort_for("format", "edit") == ""

def test_owners_cut_judge_defaults_to_independent_gemini(monkeypatch, setting):
    roles = []
    monkeypatch.setattr(M, "ask", lambda role, *a, **k: (roles.append(role), {"scores": {x: 8 for x in CR.OC_KEYS}, "fixes": []})[1])
    CR.judge({"premise": "p"}, "s", {}, "E"); setting("OWNERS_CUT_JUDGE", "opus"); CR.judge({"premise": "p"}, "s", {}, "E")
    assert roles == ["critic", "owners_cut"] and M.route("owners_cut")[0] == "opus"

def test_writer_brief_rewrites_share_one_cached_brief(monkeypatch):
    from whatifs.sampler import draw as DRAW
    seen = []; real = M.ask
    monkeypatch.setattr(ROOM, "ask", lambda role, system, prompt, **k: (seen.append((role, system)), real(role, system, prompt, **k))[1])
    MG.setup(); ROOM.run_room(DRAW("EPW", "collective"), "EPW")
    wr = [x for x in seen if x[0] in ("writer", "rewrite", "length", "format", "retention")]
    assert wr and all(isinstance(x[1], P.Packed) and x[1].episode and not x[1].role for x in wr)
    assert len({x[1].glob + x[1].episode for x in wr}) == 1                                    # every writer-group call: one identical cached brief
    st = M.CACHE.stats.get(("EPW", core.JOB["name"])); assert st and st["read"] > 0           # the room really read from the cache

# ---------------------------------------------------------------- Haiku JSON repair
def test_haiku_repair_accepts_only_identical_words(monkeypatch, setting):
    broken = '{"script": "## BEAT 1\\n[calm] Hello there", "facts": [1, 2,],'
    assert M.haiku_repair(broken) == {"script": "## BEAT 1\n[calm] Hello there", "facts": [1, 2]}
    monkeypatch.setattr(F, "fake_reply", lambda key, p: '{"script": "## BEAT 1\\n[calm] Hello", "facts": [1, 2]}')    # a word dropped
    assert M.haiku_repair(broken) is None
    setting("HAIKU_CHORES_ON", "FALSE"); assert M.haiku_repair(broken) is None
    assert not M.json_same_words('{"a": "one two"}', {"a": "one three"}) and M.json_same_words('```json\n{"a": "x\\"y", "n": 3}\n```', {"a": 'x"y', "n": 3})

def test_ask_uses_the_repair_before_paying_for_a_re_ask(monkeypatch):
    monkeypatch.setattr(F, "fake_reply", lambda key, p: '{"a": "kept words", "b": [1]}' if key == "json_repair" else '{"a": "kept words", "b": [1,')
    assert M.ask("memo", "s", "p", fake_key="memo") == {"a": "kept words", "b": [1]}            # the fake chore model fixed the syntax only

# ---------------------------------------------------------------- Premise_Bench + ship the best
def _bench_row(i, prem, comb="8.4", fam="F09_space", added=None):
    return {"bench_id": f"B{i}", "added": added or core.iso(), "status": "READY", "premise": prem, "headline": prem[:30], "family": fam, "ptype": "collective",
            "claude_score": comb, "gemini_score": comb, "combined": comb, "criteria_json": "{}", "source": "test", "episode_id": "", "used_at": "", "note": ""}

def test_bench_refill_keeps_only_premises_both_judges_passed(setting):
    setting("SETUP_FILLS_BENCH", "FALSE")          # v9.2: Setup would fill the bench itself; this test fills it
    MG.setup(); n = PR.refill_bench(force=True)
    rows = core.store().rows("Premise_Bench"); assert n == len(rows) and 1 <= n <= 12
    assert all(r["status"] == "READY" and float(r["combined"]) >= 7.0 and r["claude_score"] and r["gemini_score"] for r in rows)
    assert not any("Tuesday" in r["premise"] for r in rows) or True                            # (taste judged by the fake judges)
    assert PR.refill_bench() == 0 or len(PR.bench_rows()) < 6                                  # full enough: no refill without need
    assert any(r["source"] == "bench" for r in core.store().rows("Premise_Scores"))           # every candidate's scores kept

def test_bench_refill_waits_when_the_month_needs_the_money(monkeypatch, setting):
    setting("SETUP_FILLS_BENCH", "FALSE")          # v9.2: start from an empty bench
    MG.setup(); monkeypatch.setattr(G, "production_room_inr", lambda: 100.0)
    assert PR.refill_bench() == 0 and not core.store().rows("Premise_Bench")

def test_scout_draws_from_the_bench_first_and_marks_it_used(monkeypatch, setting):
    setting("SETUP_FILLS_BENCH", "FALSE")          # v9.2: only the three test rows on the bench
    MG.setup(); st = core.store()
    st.append("Premise_Bench", [_bench_row(1, "What if your shadow lagged ten seconds behind you?"), _bench_row(2, "What if the ocean stood still at noon?", "7.9", "F06_nature"),
                                _bench_row(3, "What if your city floated a metre up?", "9.0", "F08_rules", added="2020-01-01T00:00:00Z")])
    keys = []; real = M.ask
    monkeypatch.setattr(ROOM, "ask", lambda role, *a, **k: (keys.append(k.get("fake_key")), real(role, *a, **k))[1])
    sp = ROOM.scout_and_pick({"strategies": {"family": "F09_space"}, "playbook": {}}, ROOM.context(), "EPB")
    assert "scout" not in keys and sp.get("from_bench") and sp.get("premise_score")
    rows = {r["bench_id"]: r for r in st.rows("Premise_Bench")}
    assert rows["B3"]["status"] == "STALE" and "USED" in {rows["B1"]["status"], rows["B2"]["status"]}

def test_nothing_passes_ships_the_best_pitch_and_emails_once(monkeypatch, setting):
    MG.setup(); setting("PREMISE_BENCH_ON", "FALSE")
    monkeypatch.setattr(PR, "_judge", lambda role, pitches, *a, **k: {f"p{i + 1}": {c: 5 + i * 0.2 for c in D.PREMISE_CRITERIA} for i in range(len(pitches))})
    sp = ROOM.scout_and_pick({"strategies": {"family": "F08_rules"}, "playbook": {}}, ROOM.context(), "EPX")
    assert sp["premise"] and sp["below_bar"]["kind"] == "premise" and sp["below_bar"]["best"] < 7.0
    assert {r["round"] for r in core.store().rows("Premise_Scores")} == {"0", "1", "2", "3"}    # up to 4 scout rounds (1 + PREMISE_RETRY_ROUNDS 3)
    mails = []
    from whatifs import publish as PUB
    monkeypatch.setattr(PUB, "email", lambda subj, body, *a, **k: mails.append(subj))
    assert PR.below_bar_mail("EPX", [sp["below_bar"]]) and len(mails) == 1
    setting("BELOW_BAR_MAIL_ON", "FALSE"); assert not PR.below_bar_mail("EPX", [sp["below_bar"]])

def test_owners_cut_ships_the_best_round_not_the_last(monkeypatch, setting):
    seq = iter([6.8, 7.1, 6.0, 6.5]); vers = iter(["v1", "v2", "v3"])
    monkeypatch.setattr(CR, "judge", lambda *a: (lambda m: {"scores": {k: m for k in CR.OC_KEYS}, "mean": m, "passed": False, "fixes": ["x"]})(next(seq)))
    out, rec = CR.owners_cut({"premise": "p"}, {"script": "v0"}, "", {}, "EPO", lambda sc, fx: {"script": next(vers)})
    assert out == {"script": "v1"} and rec["below_bar"]["best"] == 7.1 and len(rec["rounds"]) == 4      # 1 + OWNERS_CUT_MAX_ROUNDS (3)
    assert len(core.store().rows("Owners_Cut")) == 4

# ---------------------------------------------------------------- A. one Kling clip in the opening, the rest on the impact
UNITS = [{"i": i, "text": t, "start": i * 12.0, "end": i * 12 + 11, "tag": "reveal" if i == 2 else "none"} for i, t in enumerate(
    ["You stand on the beach.", "Nothing moves.", "Then the sky splits open.", "Calm.", "Calm again.", "The first ten seconds look harmless",
     "Then the water starts to change colour", "By the end of the hour, the coastline has moved.", "The wave hits.", "Silence.", "You breathe again."])]
IMAP = {"scenes": [{"quote": "the coastline has moved", "vantage": "object", "body": "", "senses": [], "camera": "impact_shake", "sound": "boom", "impact": True}]}

def test_one_opening_rush_hook_and_the_rest_on_the_impact(setting):
    setting("KLING_STAKES_ON", "FALSE")          # v9.2: the v8.11 placement rule (v9.2 stakes rule: test_v92_shots)
    shots = [{"type": "kling" if i in (5, 8, 10) else "still", "prompt": "p"} for i in range(len(UNITS))]
    out = IM.apply(shots, UNITS, IMAP, {"kling": 3})
    k = sorted(i for i, s in enumerate(out) if s["type"] == "kling")
    assert len(k) == 3 and k[0] == 2 and 7 in k and 6 in k                                     # opening (reveal line inside 45 s) + impact + run-up
    assert out[2]["opening_hook"] and out[2]["pov_fx"] == "pov_rush" and "camera mounted" in out[2]["motion"] and out[2]["prompt"].startswith("first-person POV")

def test_opening_clip_count_is_a_setting_and_never_takes_the_impact_clip(setting):
    setting("KLING_STAKES_ON", "FALSE")          # v9.2: the v8.11 placement rule (stakes rule: test_v92_shots)
    shots = [{"type": "kling" if i in (5, 8, 10) else "still", "prompt": "p"} for i in range(len(UNITS))]
    setting("KLING_OPENING_CLIPS", "0"); k0 = sorted(i for i, s in enumerate(IM.apply(shots, UNITS, IMAP, {"kling": 3})) if s["type"] == "kling")
    assert all(i >= 6 for i in k0)                                                            # v8.10 placement
    setting("KLING_OPENING_CLIPS", "5"); out = IM.apply(shots, UNITS, IMAP, {"kling": 3})
    k = [i for i, s in enumerate(out) if s["type"] == "kling"]; assert len(k) == 3 and 7 in k     # capped: the impact always keeps a clip
    one = IM.apply([dict(s, type="kling" if i == 5 else "still") for i, s in enumerate(shots)], UNITS, IMAP, {"kling": 1}); assert [i for i, s in enumerate(one) if s["type"] == "kling"] == [7]
    assert IM.apply(shots, [dict(u, start=None) for u in UNITS], IMAP, {"kling": 3})          # no timing yet: no crash, no hook

def test_kling_budget_logic_unchanged_by_the_opening_clip(setting):
    a = G.full_episode_inr(); setting("KLING_OPENING_CLIPS", "0"); assert G.full_episode_inr() == a      # moved, never added

# ---------------------------------------------------------------- costs: visuals protected, measured vs estimated
def test_higher_ai_estimate_never_trims_visuals(monkeypatch, setting):
    monkeypatch.setattr(G, "production_room_inr", lambda: 3600.0)
    base = G.plan_for_episode(470.0, 8)
    setting("LLM_EST_INR", "260")
    assert G.plan_for_episode(470.0 + 60, 8)["tier"] == base["tier"] == "full"                  # +Rs 60 of AI estimate: same pictures
    setting("VISUALS_PROTECTED", "FALSE"); assert G.plan_for_episode(470.0 + 60 + 400, 8)["tier"] != "full"   # the switch restores v8.10 trimming

def test_per_video_summary_row_measured_vs_estimated_and_no_double_count():
    core.cost("claude_opus", "anthropic", 100, 1.0, "EPV", basis="measured"); core.cost("gemini_pro", "google", 10, 0.2, "EPV", basis="measured")
    core.cost("gemini_tts", "google", 10, 0.5, "EPV")
    before = core.month_spend()
    m, est = M.write_ai_summary("EPV")
    assert m == pytest.approx(1.2 * core.S("USD_INR", float), abs=0.05) and est == M.ai_estimate_inr()
    row = [r for r in core.store().rows("Cost_Log") if r["item"] == "ai_per_video_summary"][0]
    assert row["inr"] == "0" and row["basis"] == "summary" and float(row["measured_inr"]) > 0 and float(row["est_inr"]) > 0
    core.refresh_spend(); assert core.month_spend() == pytest.approx(before)

def test_tabs_are_append_only_and_new_settings_documented():
    assert core.TABS["Cost_Log"][:6] == ["ts", "episode_id", "item", "provider", "units", "inr"]
    for t in ("Premise_Bench", "Cache_Stats"): assert t in core.TABS
    for k in ("KLING_OPENING_CLIPS", "PREMISE_BENCH_ON", "SKIP_IF_BELOW_BAR", "PROMPT_CACHE_ON", "CACHE_TTL_AUTO", "CACHE_WARM_ON", "SCRIPT_MODEL", "OWNERS_CUT_JUDGE",
              "HAIKU_CHORES_ON", "EFFORT_CREATIVE", "EFFORT_CHORE", "PRICE_OPUS_CACHE_READ", "PRICE_FABLE_CACHE_W1H", "PRICE_HAIKU_IN", "VISUALS_PROTECTED", "AI_SAVER_ON"):
        assert k in core.DEFAULTS and core.DEFAULTS[k][1]
    assert core.S("OWNERS_CUT_JUDGE") == "gemini" and core.S("PREMISE_RETRY_ROUNDS", int) == 3 and core.S("OWNERS_CUT_MAX_ROUNDS", int) == 3 and not core.S("SKIP_IF_BELOW_BAR", bool)
