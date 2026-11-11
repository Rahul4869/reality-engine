"""Truth hygiene (v12 B1): ONE current truth. Current docs, CLAUDE.md, module docstrings, the build prompt and every prompt string carry no
retired concept; SYSTEM.md equals the code; docs/ARCHIVE is marked history. Every rule is proven BOTH ways (passes clean, fails when violated)."""
import os, shutil, subprocess, sys
import pytest
from whatifs import truth as TRU, contract as CON, core
from tools import gen_docs as GEN

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# One violating line and (where the rule has a truthful context) one allowed line per retired rule. A rule without a sample fails the suite.
SAMPLES = {
    "brand_what_ifs":         ("Welcome to What Ifs, the channel about physics.", None),
    "old_month_cap":          ("The monthly cap is Rs 4,700 including retries.", "November: Rs 4,000 top-up approved by the owner."),
    "kling_v3_path":          ("Hero model: fal-ai/kling-video/v3/standard/image-to-video.", None),
    "kling_25_hero":          ("The hero model is Kling 2.5 Turbo Pro.", "Kling 2.5 Turbo is a fallback rung of the model ladder."),
    "table_read_room":        ("Keep the table read and the role memos in every episode.", "The table read belongs to room v1 (optional)."),
    "life_layer_active":      ("LIFE_LAYER breathing warp keeps every still alive.", "LIFE_LAYER_ON is off (measured ineffective)."),
    "technique_library_core": ("The learning core stores its evidence in Technique_Library.", "Technique_Library is the outlier-video library."),
    "case_file_you":          ("The channel concept is CASE FILE: YOU.", "CASE FILE: YOU is parked."),
    "master_build_plans":     ("Follow MASTER_BUILD for the next stage.", None),
    "history_pointer":        ("Read docs/KERNEL.md first and obey it.", "docs/ARCHIVE/KERNEL.md is history."),
    "kernel_rule_number":     ("Models are discovered live (K11).", None),
    "old_version_tag":        ("Since v9.4a the room runs early.", None),
    "old_long_cadence":       ("Standard mode makes 8 long videos a month, twice a week.", None),
    "no_kling_statement":     ("The render is ffmpeg-only.", None),
    "daily_shorts_cadence":   ("Cadence: 1.5 standalone Shorts per day (SHORTS_PER_DAY).", "Cadence: 3 standalone Shorts a week (SHORTS_PER_WEEK); thirty near-identical Shorts a day would be spam."),
}

def _mini(tmp_path):
    """A small copy of the repo's truth surface: the real docs + CLAUDE.md + build prompt, and a tiny synthetic code tree that satisfies the baseline."""
    r = str(tmp_path / "repo")
    shutil.copytree(os.path.join(ROOT, "docs"), os.path.join(r, "docs"))
    shutil.copy(os.path.join(ROOT, "CLAUDE.md"), os.path.join(r, "CLAUDE.md"))
    os.makedirs(os.path.join(r, ".github", "workflows")); shutil.copy(os.path.join(ROOT, ".github", "workflows", "claude-build.yml"), os.path.join(r, ".github", "workflows"))
    for d in ("whatifs", "tools", "tests", "mission_control"): os.makedirs(os.path.join(r, d))
    for rel in sorted(set(TRU._PATH.findall("\n".join(open(p, encoding="utf-8").read() for p in TRU.doc_files(r))))):      # every file the docs name exists (empty stand-in)
        p = os.path.join(r, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p): open(p, "w").close()
    ok = '"""A module. See docs/CURRENT/SYSTEM.md."""\n'
    _w(r, "whatifs/prompts.py", ok + 'WRITER = "Open inside the story. It happens to YOU."\n')
    _w(r, "whatifs/manage.py", ok + 'A = "budget cap moved to Rs 4,700"\nB = "fal-ai/kling-video/v3/standard/image-to-video"\n'
                                    'C = ("SHORTS_PER_DAY", "SHORTS_KLING_EVERY", "REPLAN_MAX_SHORTS_PER_DAY")\n')      # v12 V2c-b: the one-time move names the three retired cadence cells
    return r

def _w(root, rel, text, mode="w"):
    p = os.path.join(root, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, mode, encoding="utf-8", newline="\n") as f: f.write(text)

def _issues(root):
    TRU.reset(); out = TRU.issues(root); TRU.reset(); return out

# ---------------------------------------------------------------- the repo itself is clean
def test_the_repo_has_one_current_truth():
    TRU.reset(); bad = TRU.issues(); assert bad == [], bad[:5]

def test_system_md_is_generated_from_the_code_and_matches_it():
    assert GEN.drift() == "", GEN.drift()
    t = open(GEN.OUT, encoding="utf-8").read()
    assert f"{len(CON.FEATURES)} HARD contract checks" in t and "| docs_current | script |" in t
    for k in ("BUDGET_CEILING_INR", "ROOM_MODE", "FAL_HERO_MODEL", "BREAKOUT_HARD_BAR"): assert f"| {k} | {core.DEFAULTS[k][0]} |" in t, k

def test_system_md_drift_fails_when_the_doc_is_edited_by_hand(tmp_path, monkeypatch):
    p = str(tmp_path / "SYSTEM.md"); open(p, "w", encoding="utf-8", newline="\n").write(GEN.render().replace("Rs 5,000 a month", "Rs 9,999 a month"))
    monkeypatch.setattr(GEN, "OUT", p)
    assert "differs from the code" in GEN.drift()
    os.remove(p); assert "missing" in GEN.drift()

def test_system_md_drift_fails_when_the_code_changes_without_regenerating(monkeypatch):
    """A doc cannot state a number the code does not hold: change the cap, a check or a module purpose in code and the committed doc is stale."""
    monkeypatch.setitem(core.DEFAULTS, "BUDGET_CEILING_INR", ("6000", core.DEFAULTS["BUDGET_CEILING_INR"][1]))
    assert "differs from the code" in GEN.drift()
    monkeypatch.undo(); assert GEN.drift() == ""
    monkeypatch.setattr(CON, "FEATURES", CON.FEATURES + [("new_check", "final", lambda ctx: (CON.PASS, ""), "a check nobody documented")])
    assert "differs from the code" in GEN.drift()

# ---------------------------------------------------------------- every retired rule, both ways
def test_every_retired_rule_has_a_proof_sample():
    assert {r["id"] for r in TRU.RETIRED} == set(SAMPLES), set(SAMPLES) ^ {r["id"] for r in TRU.RETIRED}
    assert all(r["truth"] and r["scopes"] for r in TRU.RETIRED)

@pytest.mark.parametrize("rid", sorted(SAMPLES))
def test_retired_rule_fires_on_the_retired_statement_and_not_on_the_true_one(rid):
    bad, good = SAMPLES[rid]
    assert rid in [r["id"] for r in TRU.hits(bad, "docs")], (rid, bad)
    if good: assert rid not in [r["id"] for r in TRU.hits(good, "docs")], (rid, good)
    assert TRU.hits("Nana Rosa's verdict opens with 'Here's what's true'. The cap is Rs 5,000 a month. Room v2 is the default.", "docs") == []

def test_mini_repo_is_clean_then_each_surface_fails_when_a_retired_term_is_inserted(tmp_path):
    r = _mini(tmp_path); assert _issues(r) == [], _issues(r)[:5]
    cases = [("docs/CURRENT/CONCEPT.md", "\nThe monthly cap is Rs 4,700.\n", "old_month_cap"),                       # a current doc
             ("docs/CURRENT/OWNER_REQUIREMENTS_LEDGER.md", "\nThe learning core table is Technique_Library.\n", "technique_library_core"),
             ("CLAUDE.md", "\nThe locked rules are in docs/KERNEL.md.\n", "history_pointer"),                       # CLAUDE.md
             (".github/workflows/claude-build.yml", "\n# Read docs/CHANGES.md and obey it\n", "history_pointer"),   # the build prompt
             ("whatifs/prompts.py", 'EXTRA = "You write for What Ifs, the science channel."\n', "brand_what_ifs"),  # a prompt template
             ("whatifs/prompts.py", 'CONCEPT = "The show is CASE FILE: YOU."\n', "case_file_you")]
    for rel, text, rid in cases:
        keep = open(os.path.join(r, *rel.split("/")), encoding="utf-8").read()
        _w(r, rel, text, "a"); bad = _issues(r)
        assert any(f"retired '{rid}'" in b and b.startswith(rel) for b in bad), (rel, rid, bad[:3])
        _w(r, rel, keep); assert _issues(r) == [], rel

def test_docstrings_keep_history_out(tmp_path):
    r = _mini(tmp_path)
    _w(r, "whatifs/extra.py", '"""whatifs/extra.py v8.3 - the old way.\nLong history lives here."""\nX = 1\n')
    assert any("whatifs/extra.py: module docstring must be ONE line" in b for b in _issues(r))
    _w(r, "whatifs/extra.py", '"""Extra helper since v9.4a. See docs/CURRENT/SYSTEM.md."""\nX = 1\n')
    assert any("retired 'old_version_tag'" in b and b.startswith("whatifs/extra.py") for b in _issues(r))
    _w(r, "whatifs/extra.py", "X = 1\n"); assert any("whatifs/extra.py: no module docstring" in b for b in _issues(r))
    _w(r, "whatifs/extra.py", '"""Extra helper. See docs/CURRENT/SYSTEM.md."""\nX = 1\n'); assert _issues(r) == []

def test_layout_archive_header_claude_md_size_and_dead_paths(tmp_path):
    r = _mini(tmp_path)
    _w(r, "docs/KERNEL.md", "# the locked rules\n"); assert any("only CURRENT and ARCHIVE may live here" in b for b in _issues(r)); os.remove(os.path.join(r, "docs", "KERNEL.md"))
    _w(r, "docs/ARCHIVE/OLD_REPORT.md", "# a report from an older build\n"); assert any("OLD_REPORT.md: archive file must start with" in b for b in _issues(r))
    _w(r, "docs/ARCHIVE/OLD_REPORT.md", TRU.ARCHIVE_HEADER + ". Superseded.\n\n# a report\n"); assert _issues(r) == []
    keep = open(os.path.join(r, "CLAUDE.md"), encoding="utf-8").read()
    _w(r, "CLAUDE.md", keep + "\n".join(f"- extra rule {i}" for i in range(TRU.CLAUDE_MD_MAX_LINES))); assert any("CLAUDE.md:" in b and "lines (max" in b for b in _issues(r))
    _w(r, "CLAUDE.md", keep + "\nSee `docs/CURRENT/NOT_THERE.md` and docs/ARCHIVE/KERNEL.md for the rules.\n"); bad = _issues(r)
    assert any("names a file that does not exist (docs/CURRENT/NOT_THERE.md)" in b for b in bad) and any("without saying it is history" in b for b in bad)
    _w(r, "CLAUDE.md", keep); os.remove(os.path.join(r, "docs", "CURRENT", "CONCEPT.md")); assert any("CONCEPT.md: required current doc is missing" in b for b in _issues(r))

def test_baseline_is_a_ratchet(tmp_path):
    """Code strings that must name an old value are counted: one more fails (new violation), one fewer fails too (prune the baseline)."""
    r = _mini(tmp_path); keep = open(os.path.join(r, "whatifs", "manage.py"), encoding="utf-8").read()
    _w(r, "whatifs/manage.py", 'C = "the cap is INR 4000"\n', "a"); assert sum("retired 'old_month_cap'" in b for b in _issues(r)) == 2
    _w(r, "whatifs/manage.py", keep.replace("Rs 4,700", "Rs 5,000")); assert any("lower the entry in truth.BASELINE" in b for b in _issues(r))
    for (rel, rid), (n, why) in TRU.BASELINE.items(): assert n > 0 and why and os.path.exists(os.path.join(ROOT, *rel.split("/")))

# ---------------------------------------------------------------- the four places it runs
def test_contract_check_docs_current_passes_clean_and_holds_on_a_retired_concept(setting, monkeypatch, tmp_path):
    assert ("docs_current", "script") in [(f, s) for f, s, *_ in CON.FEATURES]
    TRU.reset(); st, ev = CON.p_docs_current({}); assert st == CON.PASS, ev
    setting("CONSTITUTION", "Rule 1: this channel is What Ifs.\nRule 2: the monthly cap is Rs 4,700.")            # a prompt source that changes without a merge
    st, ev = CON.p_docs_current({}); assert st == CON.FAIL and "brand_what_ifs" in ev and "Settings CONSTITUTION" in ev
    res = CON.run("script", {}, "EP_TRUTH", write=False); assert "docs_current" in [f for f, _ in res["failed"]] and not res["ok"]
    setting("CONSTITUTION", ""); assert CON.p_docs_current({})[0] == CON.PASS
    r = _mini(tmp_path); _w(r, "docs/CURRENT/CONCEPT.md", "\nFollow MASTER_BUILD.\n", "a")
    monkeypatch.setattr(TRU, "ROOT", r); TRU.reset()
    st, ev = CON.p_docs_current({}); assert st == CON.FAIL and "master_build_plans" in ev
    monkeypatch.undo(); TRU.reset(); assert CON.p_docs_current({})[0] == CON.PASS

def test_plan_guard_goes_red_on_a_retired_concept(tmp_path):
    r = _mini(tmp_path)
    shutil.copy(os.path.join(ROOT, "tools", "plan_guard.py"), os.path.join(r, "tools", "plan_guard.py")); shutil.copy(os.path.join(ROOT, "whatifs", "truth.py"), os.path.join(r, "whatifs", "truth.py"))
    env = dict(os.environ, PYTHONUTF8="1")
    ok = subprocess.run([sys.executable, "tools/plan_guard.py"], cwd=r, capture_output=True, text=True, env=env); assert ok.returncode == 0, ok.stdout[-600:]
    _w(r, "docs/CURRENT/CONCEPT.md", "\nThe hero model is Kling 2.5 Turbo Pro.\n", "a")
    red = subprocess.run([sys.executable, "tools/plan_guard.py"], cwd=r, capture_output=True, text=True, env=env)
    assert red.returncode == 1 and "truth:" in red.stdout and "kling_25_hero" in red.stdout

def test_rehearsal_and_build_prompt_carry_the_check():
    assert 'r["feature"] == "docs_current"' in open(os.path.join(ROOT, "tools", "rehearsal.py"), encoding="utf-8").read()
    wf = open(os.path.join(ROOT, ".github", "workflows", "claude-build.yml"), encoding="utf-8").read()
    assert "docs/CURRENT/SYSTEM.md" in wf and "tools/gen_docs.py" in wf and "tests/test_docs_current.py" in wf

# ---------------------------------------------------------------- CLAUDE.md, concept, archive
def test_claude_md_points_only_at_current_docs():
    t = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
    for must in ("docs/CURRENT/SYSTEM.md", "docs/CURRENT/OWNER_REQUIREMENTS_LEDGER.md", "docs/CURRENT/ENFORCEMENT_MATRIX.md", "Rs 5,000", "integration checklist",
                 "plan_guard", "gen_docs", "rehearsal", "Merge", "never follow"): assert must in t, must
    assert len(t.splitlines()) <= TRU.CLAUDE_MD_MAX_LINES

def test_concept_names_exist_in_the_code():
    doc = open(os.path.join(ROOT, "docs", "CURRENT", "CONCEPT.md"), encoding="utf-8").read()
    code = "".join(open(os.path.join(ROOT, "whatifs", f), encoding="utf-8").read() for f in ("show.py", "core.py", "contract.py", "prompts.py", "anim.py"))
    for name in ("Reality on Trial", "Inspector Vale", "Grimm", "Nana Rosa", "Archivist", "Here's what's true", "toybox_noir"): assert name in doc and name in code, name
    ids = {f for f, *_ in CON.FEATURES}
    for check in ("grimm_prototype", "verdict_line", "exhibits"): assert f"`{check}`" in doc and check in ids

def test_archive_keeps_history_marked_and_complete():
    arch = os.path.join(ROOT, "docs", "ARCHIVE")
    for f in ("KERNEL.md", "CHANGES.md", "MODULE_DOCSTRINGS_v11_1.md"):
        t = open(os.path.join(arch, f), encoding="utf-8").read(); assert t.startswith(TRU.ARCHIVE_HEADER) and "Superseded by" in t.splitlines()[0], f
    assert "K77" in open(os.path.join(arch, "KERNEL.md"), encoding="utf-8").read()                               # the history itself is intact, only moved
