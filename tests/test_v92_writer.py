"""v9.2 item 1: the writer's cost and time - per-role thinking caps, a cut reply retried ONCE at lower effort (never with more room), effort aligned
across calls that share a cached prefix, the monthly bank and the research brief kept out of Script Preview / production, Setup fills an empty bench."""
import json
import pytest
from whatifs import core, models as M, fakes as F, prompts as P, manage as MG, premise as PR, research as RS, room as ROOM

def _cut_then_ok(seen):
    def post(body, headers=None):
        seen.append(json.loads(json.dumps(body)))
        if len(seen) == 1: return F._Resp(200, {"content": [{"type": "text", "text": '{"script": "half'}], "stop_reason": "max_tokens", "usage": {"output_tokens": body["max_tokens"]}})
        return F._Resp(200, {"content": [{"type": "text", "text": '{"script": "ok"}'}], "stop_reason": "end_turn", "usage": {"output_tokens": 900}})
    return post

def test_cut_reply_retries_once_at_lower_effort_same_room(monkeypatch):
    seen = []; monkeypatch.setattr(M, "_post", _cut_then_ok(seen)); monkeypatch.setattr(M, "FAKE", False)
    monkeypatch.setattr(M, "model", lambda r: "fake-" + r)
    monkeypatch.setattr(M, "_gemini", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not fall through to Gemini")))
    from whatifs import governor as G
    monkeypatch.setattr(G, "monthly_cap_reached", lambda **k: False); monkeypatch.setattr(G, "claude_allowed", lambda: True); monkeypatch.setattr(G, "opus_allowed", lambda: True)
    out = M.ask("writer", "sys", "Write the narration.", max_tokens=16000)
    assert out == {"script": "ok"} and len(seen) == 2
    assert seen[1]["max_tokens"] <= seen[0]["max_tokens"]                                          # never more room
    assert seen[0]["output_config"]["effort"] == "high" and seen[1]["output_config"]["effort"] == "medium"
    assert "keep your private reasoning short" in json.dumps(seen[1]["messages"])

def test_writer_room_is_capped_by_role(setting):
    assert M.think_cap("writer", "high") == 14000 and M.think_cap("memo", "high") == 16000 and M.think_cap("x", "low") == 6000
    setting("THINK_CAPS", '{"writer": 8000}'); assert M.think_cap("writer", "max") == 8000

def test_effort_aligned_for_a_shared_prefix(capsys):
    pk = P.pack(P.MEMO, episode={"spine": "x " * 3000}, role="A")
    assert M.CACHE.aligned_effort(pk, "m", "high") == "high" and M.CACHE.aligned_effort(P.pack(P.MEMO, episode={"spine": "x " * 3000}, role="B"), "m", "medium") == "high"
    assert "effort aligned" in capsys.readouterr().out and M.CACHE.aligned_effort("no house", "m", "low") == "low"

def test_preview_room_never_runs_background_jobs(monkeypatch):
    MG.setup(); called = []
    monkeypatch.setattr(PR, "regenerate_bank", lambda *a, **k: called.append("bank") or 0)
    monkeypatch.setattr(RS, "run_research", lambda *a, **k: called.append("research") or {})
    txt, bid = RS.room_research("EPX", allow_run=False); assert "research" not in called
    from whatifs.sampler import draw as DRAW
    d = DRAW("EPBG", "collective"); ROOM.run_room(d, "EPBG")
    assert "bank" not in called and "research" not in called and "writer (first draft)" in d.get("stage_times", {}) and "owner's cut" in d["stage_times"]

def test_setup_fills_an_empty_bench_once(monkeypatch):
    n = []; real = PR.refill_bench
    monkeypatch.setattr(PR, "refill_bench", lambda force=False, episode=None: n.append(force) or real(force=force))
    MG.setup(); assert n == [True] and PR.bench_rows()
    MG.setup(); assert n == [True]                                                                  # not again once filled
