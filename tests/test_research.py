import json, datetime as dt
import pytest, requests
from whatifs import research as R, core

NOW = dt.datetime(2026, 10, 20, 12, 0, tzinfo=dt.timezone.utc)

def sig(i, kind, title, **metrics):
    return {"id": f"S{i}", "kind": kind, "title": title, "url": f"https://example.invalid/{i}", "observed_at": "2026-10-20T12:00:00Z", "published": "2026-10-19", "query": "q", "metrics": metrics}

SIGS = [sig(1, "qa_question", "What would happen if the Moon vanished tonight", score=50, views=9000, answers=2),
        sig(2, "google_trends", "moon festival", list_rank=3, approx_traffic="500+"),
        sig(3, "youtube_search", "What if the Moon disappeared", views=2_500_000, window_days=10),
        sig(4, "youtube_search", "What if bananas could talk", views=900)]

def test_unknown_signal_ids_are_dropped_and_strength_is_computed():
    ai = {"candidates": [{"premise": "What if the Moon vanished?", "evidence": ["S1", "S99"], "audience_need": "n", "click_emotion": "e", "channel_fit": "f"},
                         {"premise": "What if the ocean turned to glass?", "evidence": [], "audience_need": "n", "click_emotion": "e", "channel_fit": "f"}]}
    c = R.build_candidates(ai, SIGS)
    assert [x["evidence_strength"] for x in c] == ["direct", "none"]
    assert [o["id"] for o in c[0]["observed"]] == ["S1"]
    assert "No observed signal" in c[1]["note"]

def test_observed_evidence_carries_link_date_and_signal():
    o = R.build_candidates({"candidates": [{"premise": "What if the Moon vanished?", "evidence": ["S1"]}]}, SIGS)[0]["observed"][0]
    assert o["url"].startswith("https://") and o["observed_at"].startswith("2026-10-20") and "9,000 views" in o["signal"] and "score 50" in o["signal"]

def test_interpretation_is_labelled_as_ai_not_evidence():
    c = R.build_candidates({"candidates": [{"premise": "What if the Moon vanished?", "evidence": ["S1"], "audience_need": "x"}]}, SIGS)[0]
    assert "AI-generated interpretation" in c["ai_interpretation"]["label"]
    md = R.to_markdown({"brief_id": "B", "date": "2026-10-20", "created": "x", "completeness": "complete", "notes": [], "sources": [], "signals": SIGS, "candidates": [c]})
    assert "AI interpretation" in md and "Observed evidence" in md

def test_unsupported_trending_viral_high_intent_are_removed():
    ai = {"candidates": [{"premise": "What if the ocean turned to glass?", "evidence": [], "audience_need": "This is trending and viral and high intent", "click_emotion": "viral dread", "channel_fit": "high-intent topic"}]}
    c = R.build_candidates(ai, SIGS)[0]
    blob = json.dumps(c["ai_interpretation"]).lower()
    assert "trending" not in blob and "viral" not in blob and "high intent" not in blob and "high-intent" not in blob
    assert set(c["claims_removed"]) == {"trending", "viral", "high intent"} and c["supported_claims"] == []

def test_trending_allowed_only_with_a_matching_trends_or_chart_signal():
    s = [sig(1, "google_trends", "Moon landing anniversary", list_rank=1)]
    assert R.supported_claims("What if the Moon vanished?", s) == {"trending"}
    assert R.supported_claims("What if bananas talked?", s) == set()

def test_viral_needs_very_high_views_and_is_never_high_intent():
    assert R.supported_claims("What if the Moon disappeared", [SIGS[2]]) == {"viral"}
    assert R.supported_claims("What if bananas could talk", [SIGS[3]]) == set()
    assert "high intent" not in R.supported_claims("What if the Moon disappeared", SIGS)

def test_banned_and_recent_topics_are_filtered():
    ai = {"candidates": [{"premise": "What if the earth stopped spinning?", "evidence": []}, {"premise": "What if the Moon vanished tonight?", "evidence": []}]}
    assert [c["premise"] for c in R.build_candidates(ai, SIGS, banned=["earth stopped spinning"])] == ["What if the Moon vanished tonight?"]
    assert R.build_candidates(ai, SIGS, recent=["What if the Moon vanished tonight"], banned=["earth stopped spinning"]) == []

def test_at_most_five_candidates():
    ai = {"candidates": [{"premise": f"What if thing{i} became alive tomorrow?", "evidence": []} for i in range(9)]}
    assert len(R.build_candidates(ai, SIGS)) == 5

def test_titles_are_redacted_of_emails_and_handles():
    assert R._clean("mail me bob@example.com or follow @someuser now") == "mail me [email] or follow [handle] now"

def test_qa_collector_keeps_no_author_data(monkeypatch):
    item = {"title": "Why is the sky blue?", "link": "https://physics.stackexchange.com/q/1", "creation_date": 1760000000, "score": 5, "view_count": 100, "answer_count": 1,
            "owner": {"display_name": "Jane Private", "user_id": 77, "link": "https://x/u/77"}}
    class Resp:
        status_code = 200; text = ""
        def json(self): return {"items": [item]}
    monkeypatch.setattr(R, "_get", lambda *a, **k: Resp())
    sigs, st = R.collect_qa(NOW)
    assert sigs and "Jane" not in json.dumps(sigs) and "owner" not in json.dumps(sigs)

def _down(*a, **k): raise requests.ConnectionError("network down")

def test_all_sources_down_gives_none_and_invents_nothing(monkeypatch):
    monkeypatch.setattr(R, "_get", _down); monkeypatch.setattr(R, "_sleep", lambda s: None); monkeypatch.setattr(R, "FAKE", False)
    b = R.run_research(NOW, ask_fn=lambda *a, **k: (_ for _ in ()).throw(AssertionError("AI must not be called without signals")))
    assert b["completeness"] == "none" and b["signals"] == [] and b["candidates"] == []
    assert any("RESEARCH UNAVAILABLE" in n for n in b["notes"])

def test_partial_when_one_source_fails(monkeypatch):
    monkeypatch.setattr(R, "_sleep", lambda s: None); monkeypatch.setattr(R, "FAKE", False)
    monkeypatch.setitem(R.COLLECTORS, "youtube", lambda now=None: ([], {"source": "youtube", "status": "unavailable", "count": 0, "detail": "no Google sign-in configured"}))
    monkeypatch.setitem(R.COLLECTORS, "trends", lambda now=None: ([], {"source": "trends", "status": "unavailable", "count": 0, "detail": "HTTP 500"}))
    monkeypatch.setitem(R.COLLECTORS, "qa", lambda now=None: ([dict(SIGS[0])], {"source": "qa", "status": "ok", "count": 1, "detail": ""}))
    b = R.run_research(NOW, ask_fn=lambda *a, **k: {"candidates": [{"premise": "What if the Moon vanished tonight?", "evidence": ["S1"]}]})
    assert b["completeness"] == "partial" and "INCOMPLETE" in " ".join(b["notes"]) and len(b["candidates"]) == 1
    assert any("Only 1 of 5" in n for n in b["notes"])

def test_ai_failure_falls_back_to_raw_observed_questions(monkeypatch):
    monkeypatch.setattr(R, "FAKE", False); monkeypatch.setattr(R, "_sleep", lambda s: None)
    for k in ("youtube", "trends"): monkeypatch.setitem(R.COLLECTORS, k, lambda now=None, k=k: ([], {"source": k, "status": "unavailable", "count": 0, "detail": "x"}))
    monkeypatch.setitem(R.COLLECTORS, "qa", lambda now=None: ([dict(SIGS[0])], {"source": "qa", "status": "ok", "count": 1, "detail": ""}))
    b = R.run_research(NOW, ask_fn=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("models down")))
    c = b["candidates"][0]
    assert c["premise"].startswith("(raw audience question)") and "not assessed" in c["ai_interpretation"]["audience_need"]
    assert any("AI interpretation step failed" in n for n in b["notes"])

def test_http_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}
    class Resp:
        def __init__(s, code): s.status_code = code; s.text = "ok"
        def json(s): return {"ok": True}
    def fake(*a, **k):
        calls["n"] += 1; return Resp(503 if calls["n"] < 3 else 200)
    monkeypatch.setattr(R, "_get", fake); monkeypatch.setattr(R, "_sleep", lambda s: None)
    assert R._http("https://example.invalid") == {"ok": True} and calls["n"] == 3

def test_http_gives_up_with_clear_error_and_passes_timeout(monkeypatch):
    seen = {}
    def fake(url, params=None, headers=None, timeout=None): seen["t"] = timeout; raise requests.Timeout("slow")
    monkeypatch.setattr(R, "_get", fake); monkeypatch.setattr(R, "_sleep", lambda s: None)
    with pytest.raises(RuntimeError) as e: R._http("https://example.invalid")
    assert "Timeout" in str(e.value) and seen["t"] == 20.0

def test_client_error_is_not_retried(monkeypatch):
    calls = {"n": 0}
    class Resp: status_code = 403; text = ""
    def fake(*a, **k): calls["n"] += 1; return Resp()
    monkeypatch.setattr(R, "_get", fake); monkeypatch.setattr(R, "_sleep", lambda s: None)
    with pytest.raises(RuntimeError): R._http("https://example.invalid")
    assert calls["n"] == 1

def test_error_messages_never_contain_keys(monkeypatch):
    monkeypatch.setenv("GEMINI_KEY", "SUPERSECRETVALUE123456")
    monkeypatch.setattr(R, "_get", lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError("failed for SUPERSECRETVALUE123456")))
    monkeypatch.setattr(R, "_sleep", lambda s: None)
    with pytest.raises(RuntimeError) as e: R._http("https://example.invalid")
    assert "SUPERSECRETVALUE123456" not in str(e.value)

def test_brief_saved_dated_and_available_to_the_room(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "FAKE", True)
    b = R.run_research(NOW, ask_fn=lambda *a, **k: {"candidates": [{"premise": "What if the Moon vanished tonight?", "evidence": ["S1"], "audience_need": "n"}]})
    paths = R.save_brief(b, str(tmp_path))
    assert any(p.endswith("research_2026-10-20.json") for p in paths) and any(p.endswith(".md") for p in paths)
    rows = core.store().rows("Research_Brief")
    assert {r["evidence_type"] for r in rows} >= {"observed", "ai_interpretation", "system"}
    assert all(r["source_url"] for r in rows if r["kind"] == "signal") and all(r["brief_date"] == "2026-10-20" for r in rows)
    txt = R.text_for_room(R.latest_rows())
    assert "OBSERVED SIGNALS" in txt and "AI-SUGGESTED CANDIDATES" in txt and "interpretation, not evidence" in txt

def test_room_research_reuses_a_fresh_brief(monkeypatch):
    calls = {"n": 0}; orig = R.run_research
    def counting(*a, **k): calls["n"] += 1; return orig(*a, **k)
    monkeypatch.setattr(R, "run_research", counting)
    t1, id1 = R.room_research("E1"); t2, id2 = R.room_research("E2")
    assert calls["n"] == 1 and id1 == id2 and id1

def test_room_research_off_or_crashing_never_blocks(monkeypatch, setting):
    setting("RESEARCH_ON", "FALSE"); t, i = R.room_research("E"); assert "NOT AVAILABLE" in t and i == ""
    setting("RESEARCH_ON", "TRUE"); monkeypatch.setattr(R, "run_research", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    t, i = R.room_research("E"); assert "NOT AVAILABLE" in t and "Do not invent" in t

def test_old_brief_not_reused(monkeypatch):
    monkeypatch.setattr(R, "FAKE", True)
    b = R.run_research(NOW - dt.timedelta(days=30)); R.save_brief(b, None)
    assert R.latest_rows(7) == [] and R.latest_rows(None)

def test_scout_prompt_receives_research_and_rules():
    from whatifs import prompts as P
    p = P.fill(P.SCOUT, banned="b", recent="r", trends="t", seeds="s", families="f", prefer="any", research="[S1] a real signal")
    assert "[S1] a real signal" in p and "Never describe a pitch as trending" in p
    assert "RESEARCH NOT AVAILABLE" in P.fill(P.SCOUT, banned="b", recent="r", trends="t", seeds="s", families="f", prefer="any")

