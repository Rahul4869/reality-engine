"""U1 fix 177 (b) (open issue 197): THE HEAD OF CRAFT IS TOLD THE TRUTH. A technique is taken in for the whole channel: the intake prompt says the
channel makes its films in more than one format - one a courtroom trial with a cast and a verdict, the others with neither - and names no cast member.
Points 1-6 and the JSON it asks for are unchanged."""
from whatifs import craft as CR, show as SH

JSON_BEFORE = (' {"applies_when": "comma keywords from topics | formats", "status": "active|trial|parked|rejected", "value_case": "<= 60 words, honest", "hook_device": "",\n'
               '"first_3s_visual": "", "cut_rhythm": "", "sound_moment": "", "payoff_structure": ""}')


def test_the_intake_prompt_says_there_is_more_than_one_format_and_names_no_cast_member():
    p = CR.INTAKE_PROMPT
    assert p.startswith('You are the head of craft for Reality Engine, a faceless first-person science "what if" channel. It makes its films in more than one format:')
    assert "one of them\nis a courtroom trial with a recurring cast and a verdict, the others have no cast and no verdict." in p
    names = [c["name"] for c in SH.characters()]                                          # read from the bible the canon mirrors, never typed
    assert len(names) >= 3 and not [n for n in names if n.lower() in p.lower()], names


def test_the_six_points_and_the_json_are_unchanged():
    p = CR.INTAKE_PROMPT
    assert p.split("Return JSON:", 1)[1] == JSON_BEFORE
    assert all(f"\n{i}. " in p for i in range(1, 7)) and "Do NOT take it at face value. Reason it through:\n1. mechanism:" in p
