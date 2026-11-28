"""V4b step 8b-M1 (RULINGS_U3f 1a; MISS3 96-97): the base switch of the challenger - only while the credit lane is closed, only a cheap card, a line of the cost model."""
import pytest
from whatifs import core, models as MOD, costguard as CG, governor as G
from whatifs.org import finance as FIN

KEYS = [f"EP2099120{i}00" for i in range(10)]

def _lane(monkeypatch, open_):
    monkeypatch.setattr(FIN, "lane", lambda now=None: ({"open": True} if open_ else None)); monkeypatch.setattr(G, "claude_allowed", lambda: True)

def test_the_base_challenger_is_off_while_the_lane_is_open(monkeypatch, setting):
    """T1 (MISS3 8b-M1): the base share is read ONLY with the lane closed; with it open the lane's own share (0 here) decides, and with CHALLENGER_ON FALSE nothing is drawn."""
    setting("CHALLENGER_ON", "TRUE"); setting("CHALLENGER_BASE_HOOK", "100"); setting("CHALLENGER_SHARE_HOOK", "0")
    _lane(monkeypatch, False); assert all(MOD.challenger("hook", k) is True for k in KEYS) and MOD.challenger_role() == "challenger_base"
    _lane(monkeypatch, True); assert all(MOD.challenger("hook", k) is False for k in KEYS) and MOD.challenger_role() == "challenger"
    _lane(monkeypatch, False); setting("CHALLENGER_BASE_HOOK", "0"); assert not any(MOD.challenger("hook", k) for k in KEYS)
    setting("CHALLENGER_BASE_HOOK", "100"); setting("CHALLENGER_ON", "FALSE"); assert not any(MOD.challenger("hook", k) for k in KEYS)
    setting("CHALLENGER_ON", "TRUE"); setting("CHALLENGER_SHARE_HOOK", "100"); setting("CLAUDE_CREDIT_UNTIL", "2099-01-01")      # the lane closed: the lane's share is 0 whatever its cell says
    _lane(monkeypatch, False); assert MOD.challenger_share("hook") == 0.0
    _lane(monkeypatch, True); assert MOD.challenger_share("hook") > 0 and MOD.challenger("hook", "EP-any") in (True, False)

def test_a_long_passage_card_never_gets_a_base_challenger(monkeypatch, setting):
    """T2 (MISS3 8b-M1): a card outside BASE_CARDS ("first30": a long passage) gets no base challenger even with its own cell forced to 100."""
    monkeypatch.setitem(core.DEFAULTS, "CHALLENGER_BASE_FIRST30", ("100", "test: a long passage's base cell"))
    setting("CHALLENGER_ON", "TRUE"); _lane(monkeypatch, False)
    assert MOD.BASE_CARDS == ("hook", "title", "short") and not any(MOD.challenger("first30", k) for k in KEYS)

def test_a_base_challenger_is_a_line_of_the_cost_model(monkeypatch, setting):
    """T3 (MISS3 8b-M1): the base challenger is a line of costguard.lines only while the lane is closed and a base cell is above 0: n x CHALLENGER_BASE_EST_INR."""
    setting("CHALLENGER_ON", "TRUE"); _lane(monkeypatch, False)
    assert not [l for l in CG.lines("long") if l["key"] == "challenger_base"]
    setting("CHALLENGER_BASE_HOOK", "100"); L = [l for l in CG.lines("long") if l["key"] == "challenger_base"]
    assert len(L) == 1 and L[0]["n"] == 1.0 and L[0]["inr"] == 15.0 and L[0]["calls"] == {"text:challenger_base": 1.0}, L
    setting("CHALLENGER_BASE_TITLE", "50"); L = [l for l in CG.lines("long") if l["key"] == "challenger_base"]; assert L[0]["n"] == 1.5 and L[0]["inr"] == 22.5, L
    _lane(monkeypatch, True); assert not [l for l in CG.lines("long") if l["key"] == "challenger_base"]
