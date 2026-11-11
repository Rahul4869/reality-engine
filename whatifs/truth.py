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
    {"id": "old_long_cadence", "pattern": r"\btwice a week\b|\b2 long videos\b|\b8 (?:long )?videos (?:a|per) month", "flags": I, "unless": None, "scopes": ("docs", "prompts"),
     "truth": "the plan is 4 long videos a month, one a week (STANDARD_MAX_LONG_PER_MONTH, PUBLISH_DAYS); lines for viewers say 'every week'"},
    {"id": "no_kling_statement", "pattern": r"ffmpeg[- ]only|\bno[- ]Kling\b|without Kling", "flags": I, "unless": None, "scopes": ("docs",),
     "truth": "every long video has animated Kling scenes (ANIM_SHOTS) plus the ffmpeg/OpenCV render"},
    {"id": "daily_shorts_cadence", "pattern": r"SHORTS_PER_DAY|SHORTS_KLING_EVERY|REPLAN_MAX_SHORTS_PER_DAY|\bShorts ?(?:per|/) ?day\b|\bdaily Shorts\b|\b1\.5 (?:standalone )?Shorts\b", "flags": I, "unless": None, "scopes": ("docs", "prompts"),
     "truth": "the Shorts cadence is set in weeks: SHORTS_PER_WEEK (3) and SHORTS_PER_MONTH (12); every topic starts as a Short (whatifs/ladder.py)"},
]

# Ratchet baseline for the "prompts" scope: strings in code that MUST name an old value (a one-time setting move has to say what it replaces).
# (file, rule id) -> (allowed count, reason). More hits than allowed fail; fewer also fail (prune the entry), so the list can only shrink.
BASELINE = {
    ("whatifs/manage.py", "old_month_cap"): (1, "log line of the one-time cap move that already ran on the live Sheet"),
    ("whatifs/manage.py", "kling_v3_path"): (1, "the one-time correction names the wrong model id it replaces"),
    ("whatifs/manage.py", "daily_shorts_cadence"): (3, "the one-time move names the three retired cadence cells it marks on a live Sheet"),
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
    for d in ("whatifs", "tools"):                                   # sub-packages too (whatifs/org): an org module is a prompt source like any other
        for dp, dn, fn in os.walk(os.path.join(root, d)):
            dn[:] = sorted(x for x in dn if x != "__pycache__")
            out += [os.path.join(dp, f) for f in sorted(fn) if f.endswith(".py")]
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

# ---------------- Settings cells that no code reads (found by the baseline re-check, 10 Nov 2026)
# A cell nothing reads is a promise nothing keeps: the Sheet and SYSTEM.md say a behaviour exists and no line of code executes it. Every cell of the
# DEFAULTS table must be named by code outside that table (as a word in a string, or by a name the code builds, e.g. f"PRICE_{F}_IN").
# The cells below were unread in every version ever pushed. key -> what is TRUE today. The list can only shrink: wire the cell and delete its entry,
# or retire it. Meanwhile its note in the table must start with NOT_ACTIVE. A NEW unread cell fails Plan Guard, the tests and check docs_current.
NOT_ACTIVE = "NOT ACTIVE"
UNREAD_SETTINGS = {
    "CACHE_ALIGN_EFFORT": "each call keeps the effort its task is routed with; two efforts on one cached prefix cost one extra cache write, logged on every run",
    "ROOM_VALUE_ON": "the blind test of the writers' room against a single prompt was never built; tab Room_Value stays empty. Owner, 10 Nov 2026: build it (with the learning loop)",
    "ROOM_VALUE_EVERY": "belongs to the room value test, which was never built",
    "ROOM_MIN_WINRATE": "belongs to the room value test, which was never built",
    "RUNTIME_HARD_MAX_SEC": "the ceiling the code enforces is RUNTIME_MAX_SEC (sampler and governor)",
    "PKG_VARIANT_C_IMAGE": "the third packaging pair never gets an image of its own",
    "VIEWER_NAME_ON_SCREEN": "no code puts a viewer's name on screen, so FALSE is what happens; TRUE would change nothing",
    "PREMISE_BENCH_MAIL_MONTH": "no code writes or reads this bookkeeping cell",
}
UNREAD_SETTINGS_MAX = 8          # ratchet: lower it with every cell that is wired or retired, never raise it
_WORD = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
_WILD = "[A-Z0-9_]+"
OTHER_READERS = ("mission_control", ".github/workflows")          # the dashboard Worker and the workflows may name a cell too

def _defaults_node(tree, name="DEFAULTS"):
    for n in getattr(tree, "body", []):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets) and isinstance(n.value, ast.Dict): return n.value
    return None

def settings_cells(root=None):
    """{key: (line, default, note)} of the DEFAULTS table in whatifs/core.py, read from the source (no import: Plan Guard runs without packages)."""
    root = root or ROOT
    try: node = _defaults_node(ast.parse(_read(os.path.join(root, "whatifs", "core.py"))))
    except (OSError, SyntaxError): return {}
    out = {}
    for k, v in zip(node.keys, node.values) if node is not None else ():
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str)): continue
        try: val = ast.literal_eval(v)
        except Exception: val = ()
        val = val if isinstance(val, tuple) else ()
        out[k.value] = (k.lineno, str(val[0]) if val else "", str(val[1]) if len(val) > 1 else "")
    return out

def _template(parts):
    """A regex for a name the code builds from constant pieces and inserted values, or None when the constant pieces are not name-like or too short."""
    const = "".join(p for p in parts if p is not None)
    if None not in parts or len(const) < 5 or not re.fullmatch(r"[A-Z0-9_]+", const): return None
    return "".join(_WILD if p is None else re.escape(p) for p in parts)

def _flat_add(n):
    return _flat_add(n.left) + _flat_add(n.right) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) else [n]

def named_in_code(root=None):
    """(words, templates): every upper-case name in a string of the code (docstrings, comments and the DEFAULTS table itself do not count) and a
    regex for every name the code builds."""
    root = root or ROOT; words, templates = set(), set()
    for p in code_files(root):
        try: tree = ast.parse(_read(p))
        except SyntaxError: continue
        skip = set()
        for name in _LISTS.get(_rel(root, p), ()):
            table = _defaults_node(tree, name)
            if table is not None: skip |= {id(x) for x in ast.walk(table)}
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and _is_doc(n): skip.add(id(n.body[0].value))
        for n in ast.walk(tree):
            if id(n) in skip: continue
            if isinstance(n, ast.Constant) and isinstance(n.value, str): words.update(_WORD.findall(n.value))
            elif isinstance(n, ast.JoinedStr):
                t = _template([v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else None for v in n.values])
                if t: templates.add(t)
            elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                t = _template([x.value if isinstance(x, ast.Constant) and isinstance(x.value, str) else None for x in _flat_add(n)])
                if t: templates.add(t)
    for d in OTHER_READERS:
        for dp, _, fn in os.walk(os.path.join(root, *d.split("/"))):
            for f in sorted(fn):
                if f.endswith((".js", ".mjs", ".html", ".yml")): words.update(_WORD.findall(_read(os.path.join(dp, f))))
    return words, templates

def unread_settings(root=None):
    """Settings cells that no code names: nothing can be reading them."""
    root = root or ROOT
    if ("unread", root) not in _CACHE:
        words, templates = named_in_code(root); pats = [re.compile(t) for t in sorted(templates)]
        _CACHE[("unread", root)] = [k for k in settings_cells(root) if k not in words and not any(p.fullmatch(k) for p in pats)]
    return list(_CACHE[("unread", root)])

def settings_issues(root=None):
    """A new unread cell, a listed cell that is read again or gone, a listed cell whose note does not say NOT ACTIVE, or a list that grew."""
    root = root or ROOT; out = []
    cells = settings_cells(root)
    if not cells: return []          # a tree without a settings table (a test fixture) has nothing to check; a test proves the real table is read in full
    unread = set(unread_settings(root))
    for k in sorted(unread - set(UNREAD_SETTINGS)):
        out.append(f"whatifs/core.py:{cells[k][0]}: Settings cell {k} is read by no code - wire it, or remove it; hard enforcement or it does not exist")
    for k in sorted(UNREAD_SETTINGS):
        if k not in cells: out.append(f"whatifs/truth.py: UNREAD_SETTINGS lists {k}, which is not a Settings cell any more - delete the entry")
        elif k not in unread: out.append(f"whatifs/truth.py: Settings cell {k} is read by code now - delete its UNREAD_SETTINGS entry and the NOT ACTIVE mark in its note")
        elif not cells[k][2].startswith(NOT_ACTIVE): out.append(f"whatifs/core.py:{cells[k][0]}: the note of the unread cell {k} must start with '{NOT_ACTIVE}'")
    for k in sorted(set(cells) - unread):
        if cells[k][2].startswith(NOT_ACTIVE) and k not in UNREAD_SETTINGS: out.append(f"whatifs/core.py:{cells[k][0]}: {k} is read by code but its note says '{NOT_ACTIVE}'")
    if len(UNREAD_SETTINGS) > UNREAD_SETTINGS_MAX: out.append(f"whatifs/truth.py: UNREAD_SETTINGS grew to {len(UNREAD_SETTINGS)} (limit {UNREAD_SETTINGS_MAX}): the list may only shrink")
    return out

# ---------------- Sheet tabs nothing uses and functions nothing calls (same re-check, same rule: built but never wired = it does not exist)
# A tab no code names stays empty for ever; a function no production code names is a feature that exists only in its own definition (and perhaps in
# a test). Each entry says what is TRUE today or which batch wires it. Both lists may only shrink; a NEW unused tab or uncalled function fails
# Plan Guard, the tests and check docs_current. A function reached only by a built name (getattr with a string) belongs on the list with that reason.
UNUSED_TABS = {
    "Repairs": "no code writes or reads it: the repair robot counts its repairs from the pull requests on GitHub",
    "Room_Value": "the room value test was never built (see UNREAD_SETTINGS)",
}
UNWIRED_FUNCTIONS = {
    "whatifs/models.py:aligned_effort": "never called (see UNREAD_SETTINGS, CACHE_ALIGN_EFFORT)",
    "whatifs/show.py:bible_issues": "only tests call it: a hand edit of the Characters tab is not checked for protected names, real people or child characters",
    "whatifs/enforce.py:fix_markers": "never called",
    "whatifs/enforce.py:fix_retention": "never called: the writers' room runs its own retention fix",
    "whatifs/prompts.py:episode_pack": "never called",
    "whatifs/publish.py:meta_bio": "never called (a stub)",
    "whatifs/data.py:ptype_for": "never called",
    "whatifs/shotplan.py:prompt_variety": "a measure that only a test uses",
}
UNUSED_TABS_MAX, UNWIRED_FUNCTIONS_MAX = 2, 8          # ratchets: lower them with every entry that is wired or removed, never raise them
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_LISTS = {"whatifs/core.py": ("DEFAULTS", "TABS"), "whatifs/truth.py": ("UNREAD_SETTINGS", "UNUSED_TABS", "UNWIRED_FUNCTIONS")}      # tables that LIST names: being listed is not being used

def _production_text(root):
    """{rel: text} of everything that can USE a name: the code, the workflows, the dashboard. The listing tables are blanked out."""
    out = {}
    for p in code_files(root):
        rel = _rel(root, p); src = _read(p)
        if rel in _LISTS:
            try: tree = ast.parse(src)
            except SyntaxError: tree = None
            lines = src.split("\n")
            for n in getattr(tree, "body", []):
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in _LISTS[rel] for t in n.targets):
                    for i in range(n.lineno - 1, n.end_lineno): lines[i] = ""
            src = "\n".join(lines)
        out[rel] = src
    for d in OTHER_READERS:
        for dp, _, fn in os.walk(os.path.join(root, *d.split("/"))):
            for f in sorted(fn):
                if f.endswith((".js", ".mjs", ".html", ".yml")): out[_rel(root, os.path.join(dp, f))] = _read(os.path.join(dp, f))
    return out

def table_keys(root=None, name="TABS"):
    """The keys of a dict table in whatifs/core.py, read from the source."""
    try: node = _defaults_node(ast.parse(_read(os.path.join(root or ROOT, "whatifs", "core.py"))), name)
    except (OSError, SyntaxError): return []
    return [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)] if node is not None else []

def unused(root=None):
    """(tabs, functions): tabs of core.TABS that no code names in quotes; functions of whatifs/ whose name appears in production only where it is defined."""
    root = root or ROOT
    if ("unused", root) not in _CACHE:
        texts = _production_text(root); joined = "\n".join(texts.values()); count = {}
        for w in _IDENT.findall(joined): count[w] = count.get(w, 0) + 1
        tabs = [t for t in table_keys(root, "TABS") if ('"' + t + '"') not in joined and ("'" + t + "'") not in joined]
        defs = {}
        for rel, src in sorted(texts.items()):
            if not (rel.startswith("whatifs/") and rel.endswith(".py")): continue
            try: tree = ast.parse(src)
            except SyntaxError: continue
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("__"): defs.setdefault(n.name, []).append(rel)
        funcs = sorted(f"{rels[0]}:{name}" for name, rels in defs.items() if count.get(name, 0) <= len(rels))
        _CACHE[("unused", root)] = (tabs, funcs)
    return tuple(list(x) for x in _CACHE[("unused", root)])

def wiring_issues(root=None):
    """A new unused tab or uncalled function, a listed one that is used again or gone, or a list that grew."""
    root = root or ROOT
    if not table_keys(root, "TABS"): return []          # a test fixture without the tables
    tabs, funcs = unused(root); out = []
    for kind, found, listed, limit in (("Sheet tab", tabs, UNUSED_TABS, UNUSED_TABS_MAX), ("function", funcs, UNWIRED_FUNCTIONS, UNWIRED_FUNCTIONS_MAX)):
        name = "UNUSED_TABS" if kind == "Sheet tab" else "UNWIRED_FUNCTIONS"
        for x in sorted(set(found) - set(listed)): out.append(f"{x}: this {kind} is used by no production code - wire it or remove it; built but never wired does not exist")
        for x in sorted(set(listed) - set(found)): out.append(f"whatifs/truth.py: {name} lists {x}, which is used now or gone - delete the entry")
        if len(listed) > limit: out.append(f"whatifs/truth.py: {name} grew to {len(listed)} (limit {limit}): the list may only shrink")
    return out

def issues(root=None, runtime=False):
    """Everything that would make a new chat (or a model prompt) act on a retired concept. Empty list = one current truth."""
    root = root or ROOT
    out = [f"{f['file']}:{f['line']}: retired '{f['rule']}' ({f['text']}) -> {f['truth']}" for f in scan(root)]
    if ("layout", root) not in _CACHE: _CACHE[("layout", root)] = docstring_issues(root) + layout_issues(root) + settings_issues(root) + wiring_issues(root)
    out += _CACHE[("layout", root)]
    if runtime: out += live_prompt_issues()
    return out

if __name__ == "__main__":
    import sys
    bad = issues()
    print("TRUTH: " + ("GREEN" if not bad else "RED")); [print("  -", b) for b in bad]
    sys.exit(1 if bad else 0)
