"""v11 Stage B (K157): writers' room v2 - diverse drafts, blind cross-family jury, one revision, joke tournament. No keys, no network."""
import json
import pytest
from whatifs import core, room2 as R2

def test_both_orderings_cancel_a_pure_position_bias(monkeypatch):
    def biased(role, rubric, items, context, episode):          # always prefers whatever is shown first
        return [R2.LETTERS[i] for i in range(len(items))], {}
    monkeypatch.setattr(R2, "_jury_ask", biased)
    win, info = R2.jury(["a", "b", "c"], "r", "", "EPJ", "test", orders=2)
    assert len(set(info["scores"])) == 1                         # bias cancelled: a tie, not a fake winner

def test_a_real_preference_wins_whatever_the_order(monkeypatch):
    def likes_c(role, rubric, items, context, episode):
        order = sorted(range(len(items)), key=lambda i: 0 if items[i] == "c" else 1)
        return [R2.LETTERS[i] for i in order], {}
    monkeypatch.setattr(R2, "_jury_ask", likes_c)
    win, info = R2.jury(["a", "b", "c"], "r", "", "EPJ", "test")
    assert win == 2 and len(info["judges"]) == 6                 # 3 judges x 2 orders
    assert len(core.store().rows("Jury_Log")) == 6

def test_cross_family_jury_and_routes():
    from whatifs import models as M
    fams = {M.CHAINS[M.ROUTES[r][0]][0][0] for r, _ in R2.JURY}
    assert fams == {"g", "c"} and M.CHAINS[M.ROUTES["jury"][0]][0] == ("g", "gem_pro")
    assert all(M.CHAINS[M.ROUTES[r][0]][0][0] != "c" or M.CHAINS[M.ROUTES[r][0]][0][1] != "opus" for r, _ in R2.JURY)   # the writer (Opus) never judges

def test_write_makes_distinct_archetype_drafts_and_records_the_choice(setting):
    d = {}
    script, verdict = R2.write({"premise": "What if the Moon vanished?", "promise": {}}, "BRIEF", d, "EPW")
    assert len(set(d["room_v2"]["drafts"])) == len(d["room_v2"]["drafts"]) == 3 and d["hook_archetype"] in d["room_v2"]["drafts"]
    assert script.get("script") and verdict["room"] == "v2"
    assert {r["stage"] for r in core.store().rows("Jury_Log")} == {"drafts"}

def test_joke_tournament_keeps_labels_tags_and_the_original_can_win(monkeypatch, setting):
    text = "## BEAT 1\n[DIRECTOR] [tension] The Moon is gone and the tides have stopped completely.\n## BEAT 2\nSKEPTIC: [aside] I have a device that fixes this, obviously.\n## BEAT 3\nJUDGE: Order."
    calls = []
    def original_wins(items, rubric, context, episode, stage, judges=R2.JOKE_JURY, orders=None):
        calls.append(len(items)); return 0, {"scores": [5] + [1] * (len(items) - 1)}
    monkeypatch.setattr(R2, "jury", original_wins)
    out, info = R2.jokes({"script": text}, "BRIEF", "EPJK")
    assert out["script"] == text and info["changed"] == 0 and all(n >= 2 for n in calls)
    monkeypatch.setattr(R2, "jury", lambda items, *a, **k: (1, {"scores": [0, 5] + [0] * (len(items) - 2)}))
    out, info = R2.jokes({"script": text}, "BRIEF", "EPJK")
    new = out["script"].split("\n")
    assert info["changed"] >= 1 and new[1].startswith("[DIRECTOR] [tension] ") and new[3].startswith("SKEPTIC: [aside] ")
    assert new[0] == "## BEAT 1" and new[2] == "## BEAT 2"

def test_room_mode_switch_is_honoured_by_the_room():
    src = open("whatifs/room.py", encoding="utf-8").read()
    assert 'v2 = str(S("ROOM_MODE") or "v1").lower() == "v2"' in src and "R2.write(" in src and "R2.jokes(" in src
