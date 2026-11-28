"""U1Q-256 (DEFERRED_TRIAGE 256; V4 audit F10, CLOSINGS_18 note 8): the rehearsal compared the owner's text with `text_of` itself - a text_of that
drops or garbles "It should move ..." passed it. The rehearsal now checks the told text against words typed in tools/rehearsal.py (STRATEGY_TOLD_TAIL)."""
import json


def _row(**k):
    p = {"metric": "shorts_engaged_first_days", "board": "shorts", "direction": "up", "horizon_videos": 8}
    return {"id": "D-U1Q256", "key": "SHORT_SHARE_S2", "old": "30", "new": "40", "why": "the Shorts arm held more viewers", "prediction": json.dumps(p), **k}


def test_the_rehearsal_months_decision_is_told_in_the_words_typed_in_the_rehearsal():
    from tools.rehearsal import STRATEGY_TOLD_TAIL
    from whatifs.org import strategy as STR
    assert STRATEGY_TOLD_TAIL == ". It should move the Shorts views that count: the views a Short holds in its first days up. Nothing to do - tap Undo to take it back."
    txt = STR.text_of(_row())
    assert txt.startswith("Strategy decided: ") and " (SHORT_SHARE_S2 30 -> 40). Why: the Shorts arm held more viewers" in txt, txt
    assert txt.endswith(STRATEGY_TOLD_TAIL), txt


def test_the_rehearsal_checks_the_told_text_against_its_own_typed_words_not_text_of_alone():
    src = open("tools/rehearsal.py", encoding="utf-8").read()
    assert 'act4["text"].endswith(STRATEGY_TOLD_TAIL)' in src
    assert "f\" ({dec4['key']} {dec4['old']} -> {dec4['new']}). Why: \" in act4[\"text\"]" in src
