"""U1 fix 203 (open issue 231): THE JOKE CHECK'S GAP FACTOR HAS ONE NAME. enforce.JOKE_GAP_FACTOR (2.2) and enforce.joke_gap_max() are read by check
joke_density, by the offline writer's _punch_to_rule and by the sweep test - a change of the factor moves all three, never only the check."""
import inspect
from whatifs import contract as CON, enforce as EN, fakes as FK
from whatifs.core import S


def _script(long_words):
    """One stretch of `long_words` words without a [PUNCH], then nine short stretches each closed by one: plenty of punchlines, one long gap."""
    lines = [" ".join(["word"] * long_words)]
    for _ in range(9): lines += [" ".join(["word"] * 10), "[PUNCH] Ha."]
    return "\n".join(["[PUNCH] Ha."] + lines + ["[PUNCH] Ha."])


def test_the_check_reads_the_named_factor(monkeypatch, setting):
    setting("JOKE_EVERY_SEC_LONG", "15"); setting("WPM_ESTIMATE", "150")
    t = _script(50)                                                            # a 20 s gap: inside 2.2 x 15, outside 1.0 x 15
    assert EN.JOKE_GAP_FACTOR == 2.2 and EN.joke_gap_max() == 2.2 * 15
    ctx = {"room": {"script": {"script": t}}}
    assert CON.p_joke_density(ctx)[0] == CON.PASS, CON.p_joke_density(ctx)
    monkeypatch.setattr(EN, "JOKE_GAP_FACTOR", 1.0)
    assert EN.joke_gap_max() == 15.0 and CON.p_joke_density(ctx)[0] == CON.FAIL, CON.p_joke_density(ctx)


def test_the_offline_writer_marks_to_the_named_factor(monkeypatch, setting):
    setting("JOKE_EVERY_SEC_LONG", "15"); setting("WPM_ESTIMATE", "150")
    monkeypatch.setattr(EN, "JOKE_GAP_FACTOR", 1.0)
    body = ["NARRATOR: The sky falls a little lower over the town tonight and nobody knows why %d." % k for k in range(30)]
    out = FK._punch_to_rule(list(body))
    from whatifs import hooks as HK
    hook = " ".join(["word"] * S("SHORT_HOOK_WORDS_MAX", int))
    gate = HK.apply_to_script("\n".join(out), hook)[0]
    assert EN.biggest_gap_lines(gate) <= 15.0, EN.biggest_gap_lines(gate)


def test_no_copy_of_the_factor_is_left_as_a_literal():
    for fn in (CON.p_joke_density, FK._punch_to_rule):
        src = inspect.getsource(fn); code = "\n".join(l.split("#")[0] for l in src.splitlines() if not l.strip().startswith(('"', "'")))
        assert "joke_gap_max()" in src and "2.2 *" not in code, fn.__name__
    import tests.test_v12_floor as TF
    src = inspect.getsource(TF.test_no_F2_rehearsal_id_comes_up_short_of_the_joke_rule_whatever_its_short)
    assert "EN.joke_gap_max()" in src and "> 2.2 *" not in src


# ------------------------------------------------------------------ U1 J 203 (RUL-U1 PART 3): the ONE mandatory repair reads the same named factor
def test_the_repair_reads_the_named_factor(monkeypatch, setting):
    setting("JOKE_EVERY_SEC_LONG", "15"); setting("WPM_ESTIMATE", "150")
    t = _script(50)                                                            # a 20 s gap: inside 2.2 x 15, outside 1.0 x 15
    joke = lambda issues: [i for i in issues if "[PUNCH]" in i]
    assert joke(EN.marker_issues(t)) == [] and joke(EN.fix_markers({"script": t}, "", "EPJG1")[1]) == []
    monkeypatch.setattr(EN, "JOKE_GAP_FACTOR", 1.0)
    assert joke(EN.marker_issues(t)) and joke(EN.fix_markers({"script": t}, "", "EPJG2")[1])


def test_the_short_rule_reads_its_own_setting_and_no_literal_is_left_in_enforce(setting):
    setting("JOKE_EVERY_SEC_SHORT", "7"); setting("JOKE_EVERY_SEC_LONG", "15")
    assert EN.joke_gap_max("short") == EN.JOKE_GAP_FACTOR * 7 and EN.joke_gap_max("long") == EN.joke_gap_max() == EN.JOKE_GAP_FACTOR * 15
    src = inspect.getsource(EN)
    code = "\n".join(l.split("#")[0] for l in src.splitlines() if not l.strip().startswith(('"', "'")))
    assert "2.2 *" not in code and code.count("joke_gap_max(fmt)") == 2
