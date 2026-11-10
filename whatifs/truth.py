"""Truth Registry: the single statement of what is current and what is retired, and the scanner that enforces it in docs, docstrings and prompts. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import ast, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT_DIR, ARCHIVE_DIR = "docs/CURRENT", "docs/ARCHIVE"
ARCHIVE_HEADER = "> HISTORICAL - DO NOT FOLLOW"
POINTER = "docs/CURRENT/SYSTEM.md"
REQUIRED_DOCS = ("SYSTEM.md", "CONCEPT.md", "OWNER_REQUIREMENTS_LEDGER.md", "ENFORCEMENT_MATRIX.md")
CLAUDE_MD_MAX_LINES = 200          # Anthropic's own target for a CLAUDE.md file; a longer file is followed less reliably
I = re.I

# Every retired concept is DATA. A line that matches `pattern` is a violation unless it also matches `unless` (the context in which naming the old
# thing is true, e.g. "off", "not adopted"). `scopes`: "docs" = current docs, CLAUDE.md, build prompts and module docstrings; "prompts" = every
# string the code can send to a model or write to the Sheet. `truth` is what replaced it (shown in the failure, so the fix is never a guess).
# Later batches append here (a concept the Council retires is banned everywhere on the next run). Never delete a rule: retired stays retired.
RETIRED = [
    {"id": "brand_what_ifs", "pattern": r"\bWhat[ -]Ifs\b|\bWhatIfs\b", "flags": 0, "unless": None, "scopes": ("docs", "prompts"),
     "truth": "the brand is Reality Engine and the show is Reality on Trial"},
    {"id": "old_month_cap", "pattern": r"(?:₹|\bRs\.?|\bINR)\s?4,?[07]00\b", "flags": 0, "unless": r"top-up|approved|rest of (the month|November)", "scopes": ("docs", "prompts"),
     "truth": "the cap is Rs 5,000 a month all-in (November 2026 only: Rs 5,226)"},
    {"id": "kling_v3_path", "pattern": r"kling-video/v3/standard", "flags": I, "unless": None, "scopes": ("docs", "prompts"),
     "truth": "the hero clip model id is fal-ai/kling-video/o3/standard/image-to-video (Kling 3.0 Standard)"},
    {"id": "kling_25_hero", "pattern": r"Kling 2\.5 Turbo|kling-video/v2\.5-turbo", "flags": I, "unless": r"ladder|fallback|candidate|bake-?off", "scopes": ("docs",),
     "truth": "the hero clip model is Kling 3.0 Standard; older Kling models exist only as fallback rungs of MODEL_LADDERS"},
    {"id": "table_read_room", "pattern": r"\btable[- ]read|\brole(?:[- ]play)?[- ]memos?\b", "flags": I, "unless": r"\bv1\b|optional|off by default|\bno role|does not use", "scopes": ("docs",),
     "truth": "the writers' room is v2 (diverse drafts + blind cross-family jury + one checklist revision); the table read belongs to the optional room v1"},
    {"id": "life_layer_active", "pattern": r"LIFE_LAYER", "flags": 0, "unless": r"\boff\b|FALSE|ineffective|replaced", "scopes": ("docs",),
     "truth": "the breathing warp is OFF (measured ineffective); the world particle layer replaced it"},
    {"id": "technique_library_core", "pattern": r"Technique_Library", "flags": 0, "unless": r"outlier", "scopes": ("docs",),
     "truth": "Technique_Library is the outlier-video library; the learning core uses Technique_Evidence"},
    {"id": "case_file_you", "pattern": r"CASE FILE:? YOU", "flags": I, "unless": r"parked|not adopted|not current|R&D proposal", "scopes": ("docs", "prompts"),
     "truth": "the concept is Reality on Trial; CASE FILE: YOU is parked and may return only as an R&D proposal that wins in the Council"},
    {"id": "master_build_plans", "pattern": r"MASTER_BUILD|\bv9_2\b", "flags": 0, "unless": None, "scopes": ("docs", "prompts"),
     "truth": "the plan is the v12 Organisation build (handoff_v12/BUILD_STATE.md)"},
    {"id": "history_pointer", "pattern": r"KERNEL\.md|CHANGES\.md|DECISIONS\.md|PROMPT_LAPTOP_CHANGE|OWNER_LAPTOP_CHANGES", "flags": 0, "unless": r"ARCHIVE|HISTORICAL|history", "scopes": ("docs", "prompts"),
     "truth": "the only docs to follow are in docs/CURRENT (start at docs/CURRENT/SYSTEM.md)"},
    {"id": "kernel_rule_number", "pattern": r"\bK\d{1,3}[a-z]?\b", "flags": 0, "unless": None, "scopes": ("docs",),
     "truth": "the numbered kernel rules are history; current rules are the checks listed in docs/CURRENT/ENFORCEMENT_MATRIX.md"},
    {"id": "old_version_tag", "pattern": r"\bv(?:7|8|9|10)(?:\.\d+)*[a-z]?\b", "flags": 0, "unless": None, "scopes": ("docs",),
     "truth": "current docs describe what the code does now, without the history of versions 7 to 10"},
    {"id": "no_kling_statement", "pattern": r"ffmpeg[- ]only|\bno[- ]Kling\b|without Kling", "flags": I, "unless": None, "scopes": ("docs",),
     "truth": "every long video has animated Kling scenes (ANIM_SHOTS) plus the ffmpeg/OpenCV render"},
]

# Ratchet baseline for the "prompts" scope: strings in code that MUST name an old value (a one-time setting move has to say what it replaces).
# (file, rule id) -> (allowed count, reason). More hits than allowed fail; fewer also fail (prune the entry), so the list can only shrink.
BASELINE = {
    ("whatifs/manage.py", "old_month_cap"): (1, "log line of the one-time cap move that already ran on the live Sheet"),
    ("whatifs/manage.py", "kling_v3_path"): (1, "the one-time correction names the wrong model id it replaces"),
}

_CACHE: dict = {}

def reset():
    _CACHE.clear()

def _read(path):
    with open(path, encoding="utf-8", errors="ignore") as f: return f.read()

def _rel(root, p):
    return os.path.relpath(p, root).replace(os.sep, "/")

def doc_files(root=None):
    """The files a build or setup chat is told to follow: docs/CURRENT, CLAUDE.md, README.md, the Mission Control guide and the build-workflow prompt."""
    root = root or ROOT; out = []
    for dp, _, fn in os.walk(os.path.join(root, *CURRENT_DIR.split("/"))):
        out += [os.path.join(dp, f) for f in sorted(fn) if f.endswith(".md")]
    for rel in ("CLAUDE.md", "README.md", ".github/workflows/claude-build.yml"):
        p = os.path.join(root, *rel.split("/"))
        if os.path.exists(p): out.append(p)
    mc = os.path.join(root, "mission_control")
    if os.path.isdir(mc): out += [os.path.join(mc, f) for f in sorted(os.listdir(mc)) if f.endswith(".md")]
    return out

def code_files(root=None):
    root = root or ROOT; out = []
    for d in ("whatifs", "tools"):
        dd = os.path.join(root, d)
        if os.path.isdir(dd): out += [os.path.join(dd, f) for f in sorted(os.listdir(dd)) if f.endswith(".py")]
    return out

def _is_doc(node):
    b = getattr(node, "body", None)
    return bool(b) and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str)

def _code_texts(root):
    """Per code file: (rel, module docstring or None, [(line number, text) for every string constant that is not a docstring])."""
    out = []
    for p in code_files(root):
        rel = _rel(root, p); src = _read(p)
        if not src.strip(): continue
        try: tree = ast.parse(src)
        except SyntaxError: out.append((rel, None, [])); continue
        skip = set()
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and _is_doc(n): skip.add(id(n.body[0].value))
        mod_doc = tree.body[0].value.value if _is_doc(tree) else None
        strings = [(n.lineno, n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip and len(n.value) > 3]
        out.append((rel, mod_doc, strings))
    return out

def hits(line, scope):
    """The retired rules a single line breaks in a scope."""
    out = []
    for r in RETIRED:
        if scope not in r["scopes"] or not re.search(r["pattern"], line, r["flags"]): continue
        if r["unless"] and re.search(r["unless"], line, I): continue
        out.append(r)
    return out

def _scan_text(rel, text, scope, first_line=1):
    return [{"file": rel, "line": first_line + i, "rule": r["id"], "truth": r["truth"], "text": ln.strip()[:120]}
            for i, ln in enumerate(str(text).splitlines()) for r in hits(ln, scope)]

def scan(root=None):
    """Every retired concept found in the current docs, module docstrings and code strings (after the reviewed baseline). Cached per root."""
    root = root or ROOT
    if ("scan", root) in _CACHE: return _CACHE[("scan", root)]
    found = []
    for p in doc_files(root): found += _scan_text(_rel(root, p), _read(p), "docs")
    code = []
    for rel, mod_doc, strings in _code_texts(root):
        if mod_doc: found += _scan_text(rel, mod_doc, "docs")
        if rel == "whatifs/truth.py": continue                     # the registry has to name what it retires
        for ln, s in strings: code += _scan_text(rel, s, "prompts", ln)
    counts = {}
    for f in code: counts[(f["file"], f["rule"])] = counts.get((f["file"], f["rule"]), 0) + 1
    for key, (allowed, _why) in BASELINE.items():
        n = counts.get(key, 0)
        if n < allowed: found.append({"file": key[0], "line": 0, "rule": key[1], "truth": f"baseline allows {allowed} but only {n} found: lower the entry in truth.BASELINE", "text": "stale baseline"})
    found += [f for f in code if counts[(f["file"], f["rule"])] > BASELINE.get((f["file"], f["rule"]), (0, ""))[0]]
    _CACHE[("scan", root)] = found
    return found

def docstring_issues(root=None):
    """Every code module carries exactly one line: its purpose + the pointer to the current system doc. History never lives in a docstring."""
    root = root or ROOT; out = []
    for rel, mod_doc, _ in _code_texts(root):
        if mod_doc is None: out.append(f"{rel}: no module docstring (one line: purpose + 'See {POINTER}.')")
        elif len(mod_doc.strip().splitlines()) != 1 or POINTER not in mod_doc: out.append(f"{rel}: module docstring must be ONE line ending with 'See {POINTER}.'")
    return out

_PATH = re.compile(r"(?<![\w/.-])(?:docs|tools|whatifs|tests|handoff_v12|mission_control|\.github)/[\w./-]*\.(?:md|py|yml|js|mjs|html)\b")

def layout_issues(root=None):
    """docs/ = CURRENT + ARCHIVE only; ARCHIVE files are marked; CLAUDE.md is short and points only at CURRENT; every path a current doc names exists."""
    root = root or ROOT; out = []; docs = os.path.join(root, "docs")
    extra = sorted(set(os.listdir(docs)) - {"CURRENT", "ARCHIVE"}) if os.path.isdir(docs) else ["(docs folder missing)"]
    if extra: out.append(f"docs/: only CURRENT and ARCHIVE may live here, found {', '.join(extra)}")
    for f in REQUIRED_DOCS:
        if not os.path.exists(os.path.join(root, *CURRENT_DIR.split("/"), f)): out.append(f"{CURRENT_DIR}/{f}: required current doc is missing")
    arch = os.path.join(root, *ARCHIVE_DIR.split("/"))
    for dp, _, fn in os.walk(arch) if os.path.isdir(arch) else []:
        for f in sorted(fn):
            if not _read(os.path.join(dp, f)).lstrip("﻿").startswith(ARCHIVE_HEADER): out.append(f"{_rel(root, os.path.join(dp, f))}: archive file must start with '{ARCHIVE_HEADER}'")
    cm = os.path.join(root, "CLAUDE.md")
    if not os.path.exists(cm): out.append("CLAUDE.md: missing")
    else:
        t = _read(cm)
        if len(t.splitlines()) > CLAUDE_MD_MAX_LINES: out.append(f"CLAUDE.md: {len(t.splitlines())} lines (max {CLAUDE_MD_MAX_LINES}; move detail into {CURRENT_DIR})")
        if CURRENT_DIR + "/" not in t: out.append(f"CLAUDE.md: must point at {CURRENT_DIR}/")
    for p in doc_files(root):
        rel = _rel(root, p)
        if not rel.endswith(".md"): continue
        for i, ln in enumerate(_read(p).splitlines(), 1):
            if ARCHIVE_DIR in ln and not re.search(r"histor|never follow|do not follow", ln, I): out.append(f"{rel}:{i}: names {ARCHIVE_DIR} without saying it is history")
            for m in _PATH.findall(ln):
                if not os.path.exists(os.path.join(root, *m.split("/"))): out.append(f"{rel}:{i}: names a file that does not exist ({m})")
    return out

def live_prompt_issues():
    """Prompt sources that change WITHOUT a merge: the owner's CONSTITUTION cell is read by every department, so it is scanned on every episode."""
    try:
        from .core import S
        return [f"Settings CONSTITUTION:{f['line']}: retired '{f['rule']}' -> {f['truth']}" for f in _scan_text("Settings CONSTITUTION", S("CONSTITUTION") or "", "prompts")]
    except Exception:
        return []

def issues(root=None, runtime=False):
    """Everything that would make a new chat (or a model prompt) act on a retired concept. Empty list = one current truth."""
    root = root or ROOT
    out = [f"{f['file']}:{f['line']}: retired '{f['rule']}' ({f['text']}) -> {f['truth']}" for f in scan(root)]
    if ("layout", root) not in _CACHE: _CACHE[("layout", root)] = docstring_issues(root) + layout_issues(root)
    out += _CACHE[("layout", root)]
    if runtime: out += live_prompt_issues()
    return out

if __name__ == "__main__":
    import sys
    bad = issues()
    print("TRUTH: " + ("GREEN" if not bad else "RED")); [print("  -", b) for b in bad]
    sys.exit(1 if bad else 0)
