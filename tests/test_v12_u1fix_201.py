"""U1 fix 201 (open issue 229): WHAT CODE PUTS BACK AFTER THE LAST MEASURED FIX IS WORD FOR WORD WHAT THE FIX SAW. Measured on EP202611170305: 46 words
of asks measured by the fix, 60 other words put back, CTA_LAST naming asks the video did not carry, and the Short's hook placed after the fix.
(a) the same asks back (cta.ensure picks) and CTA_LAST read from the FINAL text; (b) the Short's proven line in place BEFORE the fix; (c) the fix
counts the seconds the hook lab's line will still add before the opening (hooks.reserve_s)."""
import pytest
from whatifs import core, room as ROOM, cta as CTA, hooks as HOOKS, enforce as EN, ladder as LAD, contract as CON, formats as FMT, growth as GR, manage as MG
from whatifs.sampler import draw as DRAW
from whatifs.org import audience as AUD, layman as LAY, inside as INS

SID = "SHU1J201"


def _said(text):
    """The spoken lines of a text as the voice reads them (headings and pauses are not lines)."""
    return [" ".join(CTA._peel(l)[3].split()) for l in str(text).split("\n") if l.strip() and not l.strip().startswith("##") and CTA._peel(l)[3].strip()]


def _asks(text):
    return [s for s in _said(text) if CTA.is_ask(s)]


def _room(monkeypatch, setting, line, ep):
    """The real room of a long video about a promoted Short whose spoken first line is `line`; the last fix is a stand-in for the rewrite that drops
    every ask and the first spoken line (the Short's line). Returns (room, what the fix saw, the fix's output, the reserve it was given)."""
    MG.setup(); setting("FORMAT_FORCE", "F1")
    assert LAD.enter({"id": SID, "premise": "What if your coffee floated?", "hook": "you_pov"}, hook_line=line)
    monkeypatch.setattr(LAD, "pitch", lambda: {"premise": "What if your coffee floated?", "headline": "Floating coffee", "family": "", "ptype": "", "teased": True,
                                               "ladder": SID, "scores": {"grasp": 9, "pull": 9}, "total": 999})
    seen = {}

    def fix_all(script, wbrief, spine, episode, fmt="long", reserve_s=0.0):
        text = script.get("script", ""); lines = text.split("\n")
        first = next(i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("##"))
        out = "\n".join(l for i, l in enumerate(lines) if i != first and not CTA.is_ask(CTA._peel(l)[3]))
        seen.update(text=text, out=out, reserve=reserve_s)
        return dict(script, script=out), ["MARKER FIX (stand-in)"]
    monkeypatch.setattr(EN, "fix_all", fix_all)
    room = ROOM.run_room(DRAW(ep, "collective"), ep)
    assert seen, "the room's last fix was not run"
    return room, seen


@pytest.mark.parametrize("endings", ["FALSE", "TRUE"])
def test_the_same_asks_come_back_after_the_fix_and_cta_last_names_the_final_texts(monkeypatch, setting, tmp_path, endings):
    """ENDINGS_ON TRUE: F1 carries the subscribe ask alone - the first placement's code still carries the older like / share codes; CTA_LAST must
    name only what the final text carries."""
    line = "Your coffee lifts off the table."
    assert HOOKS.stake(line)
    setting("ENDINGS_ON", endings); setting("CTA_LAST", "l1,s1,h1")
    room, seen = _room(monkeypatch, setting, line, "EP202611201101")
    final = room["script"]["script"]
    before = _asks(seen["text"])
    assert before and not _asks(seen["out"]), (before, _asks(seen["out"]))                       # the fix saw the asks; its rewrite dropped them all
    assert _asks(final) == before, (_asks(final), before)                                         # (a) word for word the lines it measured
    with FMT.using("F1"):                                                                          # the pool in use is the format's (the room made it in F1)
        codes = (core.S("CTA_LAST"), CTA.code_of(final), CTA.code_of(seen["text"]))
    assert codes[0] == codes[1] == codes[2] != "", codes
    assert _said(seen["text"])[0] == line and seen["reserve"] == 0.0                              # (b) the Short's line was in place BEFORE the fix; (c) a line with a stake leads
    out, rec = HOOKS.run_hooks(final, room["spine"], "EP202611201101", str(tmp_path), proven={"line": line, "short": SID})
    assert _said(out)[0] == line and rec["applied"] and rec["source"] == "short"
    assert set(_said(out)) <= set(_said(seen["text"])) | set(_said(seen["out"])), set(_said(out)) - set(_said(seen["text"])) - set(_said(seen["out"]))


def test_the_second_case_counts_the_lab_line_and_puts_back_the_line_the_fix_measured(monkeypatch, setting, tmp_path):
    line = "The coffee lifts off the table."
    assert not HOOKS.stake(line)
    room, seen = _room(monkeypatch, setting, line, "EP202611201102")
    lab_max = (HOOKS.MAX_WORDS_EXCL - 1) / core.S("WPM_ESTIMATE", float) * 60.0
    assert _said(seen["text"])[0] == line and seen["reserve"] == pytest.approx(lab_max) and lab_max > 0      # (b) and (c): the lab's longest line is counted
    out, rec = HOOKS.run_hooks(room["script"]["script"], room["spine"], "EP202611201102", str(tmp_path), proven={"line": line, "short": SID})
    lab = next(c["line"] for c in rec["candidates"] if c["id"] == rec["chosen_id"])
    said = _said(out)
    assert rec["applied"] and rec["second"]["line"] == line and said[1] == line and " ".join(said[0].split()) == " ".join(lab.split())
    new = set(said) - set(_said(seen["text"])) - set(_said(seen["out"]))
    assert new == {said[0]}, new                                                                  # nothing code put back that the fix did not see, but the lab's own line


def _edge_script(short_line):
    """A script at the joke rule's edge at 120 words a minute: the heading, the Short's line and 57 words (66 words, 33 s) before the first [PUNCH], then four short stretches
    each closed by one - have == need (5) and the first gap == joke_gap_max() exactly."""
    pool = ("the strangest part is what happens to you when eight billion people see the water change colour and the coastline "
            "moved by noon a number nobody has ever written down").split()
    words = lambda n: " ".join(pool[i % len(pool)] for i in range(n))                            # words the hook lab's lines can stand on (its overlap rule)
    lines = ["## BEAT 1", short_line + " " + words(57), "[PUNCH] Ha.", "[SEND] " + words(20), "[PUNCH] Ha.", "[AWE] " + words(20), "[PUNCH] Ha.",
             words(20), "[PUNCH] Ha.", words(20), "[PUNCH] Ha."]
    return "\n".join(lines)


def test_at_the_joke_rules_edge_the_fix_counts_the_lab_line_and_the_final_script_passes(monkeypatch, setting, tmp_path):
    setting("WPM_ESTIMATE", "120"); setting("JOKE_EVERY_SEC_LONG", "15")
    for mod, name, val in ((GR, "retention_issues", {"issues": []}), (AUD, "number_issues", []), (LAY, "plain_issues", []), (FMT, "format_issues", []),
                           (INS, "issues", []), (FMT, "ending_issues", [])):
        monkeypatch.setattr(mod, name, lambda *a, _v=val, **k: _v)                                # only the joke rule can ask for the fix here
    short = "The coffee lifts off the table."; proven = {"line": short, "short": "SH1"}
    text = _edge_script(short); ctx = lambda t: {"room": {"script": {"script": t}}}
    assert len(EN.punch_lines(text)) == EN.joke_need(text) == 5 and EN.biggest_gap_lines(text) == EN.joke_gap_max() and CON.p_joke_density(ctx(text))[0] == CON.PASS
    r = HOOKS.reserve_s(proven); assert r == pytest.approx(4.5)                                    # nine words at 120 a minute
    assert EN.marker_issues(text) == [] and EN.marker_issues(text, "long", r)                      # measured with the reserve, the edge is a problem
    same, issues = EN.fix_all({"script": text}, "", {}, "EPEDGE1", "long")                         # WITHOUT (c): nothing to fix ...
    assert issues == [] and same["script"] == text
    out0, rec0 = HOOKS.run_hooks(text, {}, "EPEDGE1", str(tmp_path / "a"), proven=proven)
    assert rec0["applied"] and CON.p_joke_density(ctx(out0))[0] == CON.FAIL                       # ... and the lab's line makes the viewer's script fail
    fixed, issues = EN.fix_all({"script": text}, "", {}, "EPEDGE2", "long", reserve_s=r)           # WITH (c): the one fix is asked for
    assert issues and any("[PUNCH]" in i for i in issues)
    out1, rec1 = HOOKS.run_hooks(fixed["script"], {}, "EPEDGE2", str(tmp_path / "b"), proven=proven)
    assert rec1["applied"] and CON.p_joke_density(ctx(out1))[0] == CON.PASS, CON.p_joke_density(ctx(out1))
