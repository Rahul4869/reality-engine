"""v10.3 (K153, Phase 2): owner view, WhatsApp menu + sections + charts, daily/weekly briefs, data-aware chat. No keys, no network."""
import datetime as dt, json, os
import pytest
from whatifs import core, owner_view as OV, charts as CH, wa as WA, digests as DG, notify as NT, publish as PUB

def _capture(monkeypatch):
    sent = []
    monkeypatch.setattr(WA, "_post", lambda body: sent.append(body) or "wamid.T")
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    return sent

def test_every_section_renders_with_a_source_and_empty_states_say_when():
    v = OV.build()
    for name in OV.TITLES:
        txt = OV.render(name, v)
        assert txt.startswith("*") and ("Source:" in txt or "yet" in txt or "start" in txt or "filling" in txt), (name, txt)
    assert "48-72 hours" in OV.render("numbers", v)                            # no data yet: says when it appears

def test_demo_view_is_labelled_everywhere():
    v = OV.build(demo=True)
    assert v["demo"] and all(OV.render(n, v).startswith("[DEMO]") for n in OV.TITLES)
    p = CH.numbers_chart(v, "/tmp/wi_demo_chart.png")
    from PIL import Image
    assert p and Image.open(p).size == (1080, 1080)

def test_no_data_no_chart():
    assert CH.numbers_chart(OV.build()) is None and CH.bars([], [], "x", "y", "/tmp/x.png") is None

def test_menu_is_a_list_of_sections(monkeypatch):
    sent = _capture(monkeypatch)
    WA.send_menu()
    b = sent[-1]; rows = b["interactive"]["action"]["sections"][0]["rows"]
    assert b["interactive"]["type"] == "list" and len(rows) <= 10 and all(len(r["title"]) <= 24 and r["id"].startswith("MENU|") for r in rows)
    assert {r["id"].split("|")[1] for r in rows} == set(OV.TITLES)

def test_inbound_menu_and_sections_with_chart_and_buttons(monkeypatch):
    sent = _capture(monkeypatch)
    from whatifs import dash as DS
    msgs = [{"id": "m1", "type": "text", "text": "menu"}, {"id": "m2", "type": "interactive", "payload": "MENU|numbers"}, {"id": "m3", "type": "text", "text": "demo numbers"}]
    monkeypatch.setattr(DS, "decrypt", lambda p: {"messages": msgs})
    assert WA.handle_inbound("{}") == 3
    kinds = [s.get("type") for s in sent]
    assert kinds.count("interactive") >= 3 and "image" in kinds                      # menu list, section buttons x2, the demo chart image
    texts = [s["interactive"]["body"]["text"] for s in sent if s.get("type") == "interactive" and s["interactive"]["type"] == "button"]
    assert any("Numbers" in t and "Source:" not in t or "48-72" in t for t in texts) and any(t.startswith("[DEMO]") for t in texts)

def test_daily_brief_parts_and_dedupe(monkeypatch, setting):
    sent = _capture(monkeypatch)
    txt, chart = DG.compose("daily", demo=True)
    for part in ("Morning brief", "Numbers", "Observations", "Strategy", "Hot topics", "What to post next", "Risks"): assert part in txt, part
    assert chart and txt.startswith("*[DEMO]")
    now = dt.datetime(2026, 11, 10, 4, 0, tzinfo=dt.timezone.utc)                   # 09:30 IST
    assert DG.due("daily", now) and DG.send("daily", now=now)["via"] in ("whatsapp", "template")
    assert not DG.due("daily", now) and DG.due("daily", now + dt.timedelta(days=1))
    assert not DG.due("daily", dt.datetime(2026, 11, 11, 1, 0, tzinfo=dt.timezone.utc))          # 06:30 IST: too early

def test_outside_the_window_the_brief_uses_the_template_with_menu_buttons(monkeypatch, setting):
    sent = _capture(monkeypatch)
    monkeypatch.setattr(DG, "FAKE", False); monkeypatch.setattr(WA, "configured", lambda: True); monkeypatch.setattr(WA, "in_window", lambda now=None: False)
    r = DG.send("weekly", now=dt.datetime(2026, 11, 15, 4, 0, tzinfo=dt.timezone.utc))
    tpl = [s for s in sent if s.get("type") == "template"]
    assert r["via"] == "template" and tpl and any(p["parameters"][0].get("payload") == "MENU|menu" for p in tpl[-1]["template"]["components"] if p["type"] == "button")

def test_chat_brain_gets_the_owner_view(monkeypatch):
    seen = {}
    import whatifs.models as M
    def fake_ask(role, system, prompt, **k): seen["p"] = prompt; return "Post the Jupiter case next. Source: Premise_Bench."
    monkeypatch.setattr(M, "ask", fake_ask)
    out, spec, kind = WA.chat("what should I post today?")
    assert "owner_view" in seen["p"] and "recommendations" in seen["p"] and "cite the src" in seen["p"]
