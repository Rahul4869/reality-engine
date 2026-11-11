"""Department registry: what each department is for, the code it wraps, its rhythm, levers, thinking cap, owned checks and the call sites that really run under the runner. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import ast, json, os
from whatifs.core import S, store, now_utc
from whatifs.org import DEPARTMENTS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CADENCES = ("tick", "episode", "daily", "weekly", "monthly")
INJECT_MODES = ("brief", "prompt")      # brief = the playbook is handed over with the work order; prompt = it is put into the model's system prompt and proven there
EVERYONE = ("owner_memo", "performance_memo", "problem_memo", "decision_memo", "ticket")       # memo types every department must load

# mission; wraps = the existing modules it owns (wrapped, never duplicated); cadence; levers = the Settings cells it may change (type, range, step and
# the direction that needs the owner: whatifs/org/levers.py); cap_inr = monthly cap for its own paid THINKING (None = it has no paid thinking of its own; production money stays
# with the governor); takes = memo types beyond EVERYONE; inject = how the Palace playbook reaches its work.
DEPTS = {
    "D0":  {"mission": "capture every owner input verbatim, route it, guarantee it is honoured", "cadence": "tick", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/wa.py", "whatifs/notify.py", "whatifs/dash.py", "whatifs/owner_view.py"), "levers": ("WA_ON", "DASH_ON"), "takes": ()},
    "D1":  {"mission": "goals, the monthly and weekly plan, cadence, priorities, budget allocation, urgency", "cadence": "weekly", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/replan.py", "whatifs/manage.py"), "levers": ("STANDARD_MAX_LONG_PER_MONTH", "PUBLISH_DAYS", "VIDEOS_PER_MONTH_EST"), "takes": ()},
    "D2":  {"mission": "automatic research: outliers, techniques, platform policy, tools, audience, competitors", "cadence": "daily", "cap_inr": 300, "inject": "brief",
            "wraps": ("whatifs/org/rnd.py", "whatifs/outlier_lab.py", "whatifs/demand.py", "whatifs/research.py", "whatifs/scout.py"), "levers": ("RESEARCH_ON", "IDEA_MIN_MULTIPLE", "RESEARCH_PER_WEEK"), "takes": ()},
    "D3":  {"mission": "assess every research and creative memo: evidence, novelty, impact, feasibility, cost, risk", "cadence": "weekly", "cap_inr": 120, "inject": "brief",
            "wraps": ("whatifs/org/board.py", "whatifs/room2.py"), "levers": ("BOARD_MIN_EVIDENCE",), "takes": ("research_memo",)},
    "D4":  {"mission": "premises, scripts, jokes, hooks, world-building", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/premise.py", "whatifs/room.py", "whatifs/room2.py", "whatifs/hooks.py", "whatifs/show.py", "whatifs/playbook.py"),
            "levers": ("ROOM_MODE", "ROOM_V2_DRAFTS", "REHOOK_MAX_GAP_SEC", "JOKE_EVERY_SEC_LONG", "COLD_OPEN_LORE_FREE_SEC"), "takes": ()},
    "D5":  {"mission": "titles, thumbnails, the promise, packaging tests", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/packaging.py", "whatifs/art.py"), "levers": ("PROMISE_BY_SEC",), "takes": ()},
    "D6":  {"mission": "stills, animated scenes, living characters, particles, micro-cuts, the render", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/media.py", "whatifs/anim.py", "whatifs/living.py", "whatifs/render.py", "whatifs/shotplan.py"),
            "levers": ("ANIM_SHOTS", "VISUAL_CHANGE_MAX_S", "PARTICLES_ON", "LIVING_CHARACTERS_ON", "CAMERA_MOTION"), "takes": ()},
    "D7":  {"mission": "voices, sound worlds, story events, the music bed, the pause before a punchline", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/voice.py", "whatifs/tts_gemini.py", "whatifs/sound.py"), "levers": ("SOUND_DESIGN_ON", "TTS_ENGINE"), "takes": ()},
    "D8":  {"mission": "the Feature Contract, the Impact Map, the enforcement matrix, problem memos, the repair loop", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/contract.py", "whatifs/enforce.py", "whatifs/qc.py", "whatifs/fixes.py"), "levers": ("CONTRACT_OFF", "BREAKOUT_HARD_BAR", "CRITIQUE_MIN"), "takes": ("repair_memo",)},
    "D9":  {"mission": "uploads, Shorts, Instagram and Facebook, schedules, spin-offs", "cadence": "episode", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/publish.py", "whatifs/shorts2.py", "whatifs/spinoff.py", "whatifs/deeptrial.py", "whatifs/specials.py"),
            "levers": ("SHORTS_PER_DAY", "REEL1_DELAY_MIN", "REEL2_DELAY_MIN", "NEXT_LINK_ON"), "takes": ()},
    "D10": {"mission": "analytics, technique evidence, sampling, forecasts, the 48-hour monitor, breakout follow-ups", "cadence": "daily", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/brain.py", "whatifs/breakout.py", "whatifs/growth.py", "whatifs/reach.py"), "levers": ("BRAIN_ON", "BRAIN_HOLDOUT"), "takes": ()},
    "D11": {"mission": "caps, the guard, the breakout fund, cost forecasts, spend vetoes", "cadence": "daily", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/governor.py", "whatifs/costguard.py"), "levers": ("BUDGET_GUARD_PCT", "BREAKOUT_FUND_CAP_INR", "AUTO_FIX_PAID_INR"), "takes": ()},
    "D12": {"mission": "reliability, the watchdog, model ladders, deprecations, incidents, build requests", "cadence": "tick", "cap_inr": None, "inject": "brief",
            "wraps": ("whatifs/steward.py", "whatifs/builds.py", "tools/repair.py"), "levers": ("PREFLIGHT_ON",), "takes": ("build_request",)},
    "C":   {"mission": "bring research, creative, owner, performance and problem memos together, decide, issue tickets", "cadence": "weekly", "cap_inr": 150, "inject": "brief",
            "wraps": (), "levers": ("ORG_SLA_HOURS",), "takes": ("assessment_memo", "creative_memo")},
    "L":   {"mission": "keep the Palace consolidated, free of duplicates and contradictions, versioned and bounded", "cadence": "weekly", "cap_inr": 40, "inject": "brief",
            "wraps": ("whatifs/org/palace.py",), "levers": ("PALACE_PLAYBOOK_TOKENS", "PALACE_PLAYBOOK_TOKENS_BY_DEPT", "PALACE_LIMITS_SHARE", "PALACE_REVIEW_DAYS", "PALACE_KIND_CAPS"),
            "takes": ("takeaway",)},
}
TAKEAWAY_CAP_INR = 60          # monthly cap for model-written takeaways across all departments (about Rs 0.5 each; none is written by a model yet)

# v12 B6a: the creative runs whose playbook goes INTO the model prompts (ORG_PROMPT_INJECT): trigger -> tasks that receive it (never the blind judges,
# never the mechanical passes), the key call that must carry it, the calls that may add ONE proposal for the Council, the narration calls that must
# pay the show's continuity debt (whatifs/org/canon.py). Every other run of the department stays in its base mode.
PROMPT = {
    "D4": {t: {"tasks": ("scout", "showrunner", "memo", "bible", "writer", "rewrite", "punchup"), "key": "writer", "propose": ("showrunner", "bible"),
               "must": ("writer", "rewrite")} for t in ("write", "draft")},
    "D5": {"package": {"tasks": ("packager",), "key": "packager", "propose": ("packager",), "must": ()}},
    "D6": {"plan": {"tasks": ("director",), "key": "director", "propose": ("director",), "must": ()}},
}
CREATIVE_RUNS = (("D4", "write"), ("D5", "package"), ("D6", "plan"))      # judged by palace_injected / palace_cited (D4 write = the episode's script)

# The call sites that run under the runner today: department -> ((file, trigger), ...). entry_issues() reads the files and fails when a call
# named here is missing or a call found there is not named here.
ENTRY = {
    "D4":  (("whatifs/episode.py", "write"), ("whatifs/preview.py", "draft")),      # v12 B6a: pre-production writing is a D4 run too
    "D5":  (("whatifs/episode.py", "package"),),
    "D6":  (("whatifs/episode.py", "plan"), ("whatifs/episode.py", "assets"), ("whatifs/episode.py", "render")),
    "D7":  (("whatifs/episode.py", "voice"),),
    "D8":  (("whatifs/episode.py", "script_gate"), ("whatifs/episode.py", "final_gate")),
    "D9":  (("whatifs/episode.py", "publish"),),
    "D10": (("whatifs/cli.py", "daily"),),
    "D2":  (("whatifs/cli.py", "daily"), ("whatifs/cli.py", "weekly")),             # v12 B5: the learning job runs R&D first (daily always, weekly when due)
    "D3":  (("whatifs/cli.py", "assess"),),                                          # v12 B5: then the Review Board, whenever a research memo waits
    "D12": (("whatifs/org/execute.py", "operate"),),
}
# Departments with no run of their own yet -> the build batch that wires them. A RATCHET: this list may only shrink (tests/test_v12_org.py).
PENDING = {"D0": "B9", "D1": "B9", "D11": "B9", "C": "B6", "L": "B8"}

# The runs an episode must have finished before each gate (the gate itself is the run in flight).
EPISODE_RUNS = {
    "script": (("D4", "write"), ("D7", "voice"), ("D5", "package"), ("D6", "plan")),
    "final":  (("D4", "write"), ("D7", "voice"), ("D5", "package"), ("D6", "plan"), ("D8", "script_gate"), ("D6", "assets"), ("D6", "render")),
}
GATE_RUNS = {"script": ("D8", "script_gate"), "final": ("D8", "final_gate")}

# Which department owns each contract check (a failed check becomes a problem memo to that department).
CHECK_OWNER = {
    "retention": "D4", "no_retired": "D4", "idea_evidence": "D4", "joke_density": "D4", "send_and_awe": "D4", "hook_lab": "D4", "owners_cut": "D4", "cold_open": "D4",
    "emotion_beat": "D4", "audience_asks": "D4", "verdict_style": "D4", "originality": "D4", "end_tease": "D4", "time_ladder": "D4", "exhibits": "D4",
    "grimm_prototype": "D4", "verdict_line": "D4", "research": "D2", "brain_playbook": "D10", "docs_current": "D12", "palace_health": "L",
    "designed_voices": "D7", "music_bed": "D7", "animation": "D6", "real_motion": "D6", "no_frozen_frames": "D6", "slop_guard": "D6", "impact_map": "D6",
    "visual_change": "D6", "living_characters": "D6", "aliveness": "D6", "promise_paid": "D6", "thumbnails": "D5", "titles": "D5", "chapters": "D5",
    "short_covers": "D5", "shorts": "D9", "self_review": "D8", "breakout_bar": "D1", "dept_contract": "D8", "takeaways_written": "D8",
    "decisions_executed": "C", "lever_verified": "D12", "research_cadence": "D2", "palace_injected": "D4", "palace_cited": "D4", "canon_in_brief": "D4",
}

def runnable(dept):
    """Can this department act today (does any call site run it under the runner)? The escalation ladder skips a holder that cannot."""
    return dept in ENTRY

def inject(dept, trigger=None):
    """How the playbook reaches this run: 'prompt' for a creative run named in PROMPT while ORG_PROMPT_INJECT is on, else the department's base mode."""
    if trigger is not None and trigger in PROMPT.get(dept, {}) and S("ORG_PROMPT_INJECT", bool): return "prompt"
    return DEPTS[dept]["inject"]

def prompt_spec(dept, trigger):
    """{'tasks', 'key', 'propose', 'must'} of a creative run ({} when the run has no prompt spec)."""
    return dict(PROMPT.get(dept, {}).get(trigger) or {})

def takes(dept, mtype):
    return mtype in EVERYONE or mtype in DEPTS[dept]["takes"]

def may_change(dept, key):
    """Is this Settings cell one of the department's levers?"""
    return key in DEPTS.get(dept, {}).get("levers", ())

def check_owner(fid):
    return CHECK_OWNER.get(fid, "D8")

def caps():
    """{department: monthly thinking cap in rupees}; setting ORG_CAPS_INR = {"D2": 250} overrides single departments."""
    out = {d: v["cap_inr"] for d, v in DEPTS.items() if v["cap_inr"] is not None}; out["takeaways"] = TAKEAWAY_CAP_INR
    try:
        ov = json.loads(S("ORG_CAPS_INR") or "{}")
        if isinstance(ov, dict): out.update({k: float(v) for k, v in ov.items() if k in out and float(v) >= 0})
    except Exception: pass
    return out

def spent(dept, st=None, now=None):
    """Rupees this department's own thinking runs (budget 'org') have cost this month, from Org_Audit."""
    st = st or store(); mk = (now or now_utc()).strftime("%Y-%m"); total = 0.0
    for r in st.rows("Org_Audit"):
        if r.get("dept") == dept and r.get("budget") == "org" and str(r.get("ts") or "").startswith(mk):
            try: total += float(r.get("cost_inr") or 0)
            except (TypeError, ValueError): pass
    return round(total, 2)

_CALLS: dict = {}
def _calls(rel, root=None):
    """Every `<x>.work("<dept>", "<trigger>", ...)` / `.run(...)` call written in a file, read from its syntax tree (remembered per file change)."""
    p = os.path.join(root or ROOT, *rel.split("/"))
    try: key = (p, os.path.getmtime(p))
    except OSError: return None
    if key not in _CALLS:
        with open(p, encoding="utf-8") as f: tree = ast.parse(f.read())
        found = set()
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("work", "run") and len(n.args) >= 2
                    and all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in n.args[:2]) and n.args[0].value in DEPARTMENTS):
                found.add((n.args[0].value, n.args[1].value))
        _CALLS.clear(); _CALLS[key] = found
    return _CALLS[key]

def entry_issues(root=None):
    """Is the registry honest? Every department is either wired (each named call site exists in the code) or pending - never both, never neither;
    a runner call that exists in a named file but is missing here is reported too; registry data points only at real files, cells and checks."""
    p = []
    both = set(ENTRY) & set(PENDING); none = set(DEPARTMENTS) - set(ENTRY) - set(PENDING)
    if both: p.append("wired AND pending: " + ", ".join(sorted(both)))
    if none: p.append("neither wired nor pending: " + ", ".join(sorted(none)))
    if set(DEPTS) != set(DEPARTMENTS): p.append("the registry and the department list differ")
    named = {}
    for dept, sites in ENTRY.items():
        for rel, trig in sites: named.setdefault(rel, set()).add((dept, trig))
    for rel, want in sorted(named.items()):
        have = _calls(rel, root)
        if have is None: p.append(f"{rel} does not exist"); continue
        p += [f"{rel}: no runner call for {d} '{t}' (the registry says it runs there)" for d, t in sorted(want - have)]
        p += [f"{rel}: runner call for {d} '{t}' is not in the registry" for d, t in sorted(have - want)]
    wired = {(d, t) for d, sites in ENTRY.items() for _f, t in sites}
    for gate, runs in EPISODE_RUNS.items():
        p += [f"gate '{gate}' requires {d} '{t}', which is not a wired call site" for d, t in runs if (d, t) not in wired]
    return p

def data_issues(root=None):
    """Static truth of the registry data: files exist, levers are real Settings cells, modes and cadences are known, every contract check has an owner."""
    from whatifs import core
    p = []
    for d, v in DEPTS.items():
        p += [f"{d}: wraps a file that does not exist ({w})" for w in v["wraps"] if not os.path.exists(os.path.join(root or ROOT, *w.split("/")))]
        p += [f"{d}: lever {k} is not a Settings cell" for k in v["levers"] if k not in core.DEFAULTS]
        if v["cadence"] not in CADENCES: p.append(f"{d}: unknown cadence '{v['cadence']}'")
        if v["inject"] not in INJECT_MODES: p.append(f"{d}: unknown inject mode '{v['inject']}'")
    seen = {}
    for d, v in DEPTS.items():
        for k in v["levers"]:
            if k in seen: p.append(f"lever {k} has two owners ({seen[k]} and {d})")
            seen[k] = d
    try:
        from whatifs import contract as CON
        ids = {f[0] for f in CON.FEATURES}
        p += [f"contract check '{i}' has no owning department" for i in sorted(ids - set(CHECK_OWNER))]
        p += [f"CHECK_OWNER names a check that does not exist ('{i}')" for i in sorted(set(CHECK_OWNER) - ids)]
    except Exception as e: p.append(f"the contract could not be read: {e}")
    p += [f"CHECK_OWNER sends '{i}' to an unknown department" for i, d in CHECK_OWNER.items() if d not in DEPARTMENTS]
    wired = {(d, t) for d, sites in ENTRY.items() for _f, t in sites}
    for d, by in PROMPT.items():                                     # v12 B6a: a prompt spec names a real run, and its key / proposing / debt calls are calls it injects
        for t, sp in by.items():
            if (d, t) not in wired: p.append(f"PROMPT names {d} '{t}', which is not a wired call site")
            if sp.get("key") not in sp.get("tasks", ()): p.append(f"PROMPT {d} '{t}': key call '{sp.get('key')}' does not receive the playbook")
            p += [f"PROMPT {d} '{t}': '{x}' is not one of its injected calls" for x in tuple(sp.get("propose", ())) + tuple(sp.get("must", ())) if x not in sp.get("tasks", ())]
    p += [f"CREATIVE_RUNS names {d} '{t}' without a prompt spec" for d, t in CREATIVE_RUNS if t not in PROMPT.get(d, {})]
    from whatifs.org import levers as LV
    return p + LV.issues()
