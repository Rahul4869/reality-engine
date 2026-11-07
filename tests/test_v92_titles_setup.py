"""v9.2 items 4-5: natural-English titles ranked by a scroll-stopping score; Setup speed (voice checks reused / side by side, unchanged samples kept)."""
import pytest
from whatifs import core, packaging as PK, growth as GR, manage as MG, tts_gemini as T, cast as CAST

BAD = "Everyone Is Wrong About What Happens If Light Walked"

def test_the_preview_title_is_rejected_as_clunky():
    assert PK.natural_issues(BAD) and GR.title_issues(BAD)
    assert not PK.natural_issues("What Would Happen If Light Walked Through Your Home?")
    assert PK.natural_issues("What Happens If The Moon Melted") and PK.natural_issues("Your Mirror Is Lying To You About")

def test_shock_shapes_beat_plain_promises():
    bold = "Your Reflection Is 1.4 Seconds Late. Is It Still You?"
    impossible = "Light Just Lost a Race to Your Cat"
    plain = "What Would Happen If Light Moved at Walking Speed"
    assert PK.shock_score(bold) > PK.shock_score(plain) and PK.shock_score(impossible) > PK.shock_score(plain)
    assert PK.rank_titles([plain, BAD, bold])[0] == bold and PK.rank_titles([BAD, plain])[-1] == BAD

def test_variants_lead_with_the_strongest_natural_title():
    pkg = {"title": "What Would Happen If Light Moved at Walking Speed", "thumb_text": "TOO SLOW", "title_b": BAD, "thumb_text_b": "WAIT",
           "titles": ["Your Reflection Is 1.4 Seconds Late. Is It Still You?", "Light Just Lost a Race to Your Cat Today"], "thumb_text_c": "TICK TOCK"}
    vs = PK.variants(pkg, {})
    assert vs[0]["title"].startswith("Your Reflection") and BAD not in [v["title"] for v in vs]
    assert "STOP THE SCROLL" in PK.TITLE_BRIEF and "never a promise the video does not keep" in PK.TITLE_BRIEF

def test_title_rule_switch(setting):
    setting("TITLE_SHOCK_ON", "FALSE"); assert not GR.title_issues(BAD)                      # v9.1 linter only

def test_voice_check_reuses_recent_passes_and_runs_side_by_side(monkeypatch):
    MG.setup(); CAST.ensure_seed(); calls = []
    real = T.synth
    monkeypatch.setattr(T, "synth", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    ok1, tot1, _ = T.voice_check(); first = len(calls)
    ok2, tot2, _ = T.voice_check(); assert len(calls) == first and ok2 == ok1 and tot2 == tot1          # nothing re-checked within 7 days
    assert first > 0 and any("reused check" in r["detail"] for r in core.store().rows("Voice_Check"))
