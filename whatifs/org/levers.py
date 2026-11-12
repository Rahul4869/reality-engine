"""Lever registry: every Settings cell a department may change by ticket - type, range, largest step, the direction that needs the owner, the checks that judge it - and the scope of an automatic merge. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, re
from whatifs.core import S
from whatifs.org import DEPARTMENTS, registry as REG

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MERGE_MAX_LINES = 400                   # a bigger diff is read by the owner, whatever it touches
GATE, COST, PLAN, OWNER = "it weakens a quality gate", "it costs more money", "it changes the plan you set", "it switches off something you rely on"

def _n(kind, lo, hi, step, owner="", why="", checks=()): return {"kind": kind, "lo": lo, "hi": hi, "step": step, "owner": owner, "why": why, "checks": tuple(checks)}
def _b(owner="", why="", checks=()): return {"kind": "bool", "owner": owner, "why": why, "checks": tuple(checks)}
def _e(values, owner=(), why="", checks=()): return {"kind": "enum", "values": tuple(values), "owner": tuple(owner), "why": why, "checks": tuple(checks)}
def _j(keys, lo, hi, owner="", why="", checks=(), pair=False): return {"kind": "json", "keys": keys, "lo": lo, "hi": hi, "pair": pair, "owner": owner, "why": why, "checks": tuple(checks)}

# kind: int | float | bool | enum | days | csv | json. lo / hi = the allowed range; step = the largest move ONE ticket may make.
# owner = the direction that needs the owner's tap: "up" / "down" (numbers), "off" / "on" (switches), a tuple of values (enum), "always", "" = never;
# why = what that direction does. checks = the contract checks that judge the lever: a video made after the change must pass them or the change is
# rolled back; a lever without checks is judged by the next complete run of its department. Which department owns a lever: registry.DEPTS.
LEVERS = {
    "WA_ON": _b("always", "it is your own channel to the pipeline"), "DASH_ON": _b("always", "it is your own dashboard"),
    "STANDARD_MAX_LONG_PER_MONTH": _n("int", 1, 8, 1, "always", PLAN), "PUBLISH_DAYS": {"kind": "days", "owner": "always", "why": PLAN, "checks": ()},
    "VIDEOS_PER_MONTH_EST": _n("int", 1, 8, 1, "always", PLAN),
    "RESEARCH_ON": _b("off", OWNER, ("research",)), "IDEA_MIN_MULTIPLE": _n("float", 2, 20, 2, "down", GATE, ("idea_evidence",)),
    "RESEARCH_PER_WEEK": _n("int", 1, 8, 2, "up", COST, ("research_cadence",)), "BOARD_MIN_EVIDENCE": _n("int", 3, 9, 1, "down", GATE, ("research_cadence",)),
    "NUMBERS_PER_MIN_MAX": _n("float", 1, 8, 1, "up", GATE, ("viewer_numbers",)), "GRAPHICS_MAX_LONG": _n("int", 0, 8, 1, "up", GATE, ("viewer_numbers",)),
    "GRAPHICS_FREE_SEC": _n("int", 0, 180, 30, "down", GATE, ("viewer_numbers",)), "BREATH_EVERY_S": _n("int", 15, 60, 10, "up", GATE, ("viewer_breath",)),
    "PLAIN_HARD_PER_MIN_MAX": _n("float", 1, 5, 1, "up", GATE, ("viewer_plain",)), "PLAIN_OPENING_HARD_MAX": _n("int", 0, 3, 1, "up", GATE, ("viewer_plain",)),
    "PLAIN_HARD_PER_SENTENCE_MAX": _n("int", 1, 4, 1, "up", GATE, ("viewer_plain",)),
    "FORMAT_SHARE_F1": _n("int", 0, 100, 20), "FORMAT_SHARE_F2": _n("int", 0, 100, 20), "FORMAT_SHARE_F3": _n("int", 0, 100, 20),      # v12 V2a: Strategy moves the mix by small steps
    "SHORT_SHARE_S1": _n("int", 0, 100, 20), "SHORT_SHARE_S2": _n("int", 0, 100, 20), "SHORT_SHARE_S3": _n("int", 0, 100, 20),         # v12 V2c: the Shorts Studio moves its own mix by small steps
    "SHORT_MIN_S": _n("int", 10, 40, 5, "down", GATE, ("short_shape",)), "SHORT_MAX_S_S1": _n("int", 20, 60, 5, "up", GATE, ("short_shape",)),
    "SHORT_MAX_S_S2": _n("int", 20, 60, 5, "up", GATE, ("short_shape",)), "SHORT_MAX_S_S3": _n("int", 20, 60, 5, "up", GATE, ("short_shape",)),
    "SHORT_HOOK_WORDS_MAX": _n("int", 4, 20, 2, "up", GATE, ("short_open",)), "SHORT_HOOK_BY_S": _n("float", 1.5, 6, 1, "up", GATE, ("short_open",)),
    "SHORT_NUMBERS_MAX": _n("int", 0, 4, 1, "up", GATE, ("short_plain",)), "SHORT_EXPERT_MAX": _n("int", 0, 3, 1, "up", GATE, ("short_plain",)),
    "SHORT_PROMISE_WORDS_MAX": _n("int", 2, 10, 2, "up", GATE, ("short_open",)),
    "ROOM_MODE": _e(("v2", "v1"), ("v1",), "v1 is the older writers' room without the blind jury", ("owners_cut",)),
    "ROOM_V2_DRAFTS": _n("int", 2, 5, 1, "up", COST, ("owners_cut",)), "REHOOK_MAX_GAP_SEC": _n("int", 30, 120, 15, "up", GATE, ("retention",)),
    "JOKE_EVERY_SEC_LONG": _n("int", 8, 60, 10, "up", GATE, ("joke_density",)), "COLD_OPEN_LORE_FREE_SEC": _n("int", 10, 45, 10, "down", GATE, ("cold_open",)),
    "PROMISE_BY_SEC": _n("int", 5, 60, 10, "up", GATE, ("promise_paid", "viewer_promise")),
    "ANIM_SHOTS": _n("int", 2, 8, 1, "up", COST, ("animation", "real_motion")), "VISUAL_CHANGE_MAX_S": _n("float", 2, 8, 1, "up", GATE, ("visual_change",)),
    "PARTICLES_ON": _b("off", GATE, ("aliveness",)), "LIVING_CHARACTERS_ON": _b("off", GATE, ("living_characters",)),
    "CAMERA_MOTION": _e(("dynamic", "gentle"), (), "", ("no_frozen_frames",)),
    "SOUND_DESIGN_ON": _b("off", GATE, ("music_bed",)), "TTS_ENGINE": _e(("gemini", "kokoro"), (), "", ("designed_voices",)),
    "CONTRACT_OFF": {"kind": "csv", "owner": "always", "why": "it switches a promised check off", "checks": ()},
    "BREAKOUT_HARD_BAR": _n("int", 50, 95, 5, "down", GATE, ("breakout_bar",)), "CRITIQUE_MIN": _n("float", 4, 9, 1, "down", GATE, ("self_review",)),
    "SHORTS_PER_WEEK": _n("int", 1, 5, 1, "up", COST), "SHORTS_PER_MONTH": _n("int", 4, 20, 2, "up", COST),                       # v12 V2c-b: the cadence in weeks (the Shorts Studio)
    "SHORTS_BREAKOUT_X": _n("float", 2, 10, 1, "down", COST), "FOLLOWUP_WITHIN_H": _n("int", 24, 96, 24),                          # the double-down line and its clock
    "LADDER_WINDOW_DAYS": _n("int", 14, 60, 7, "", "", ("topic_ladder",)), "LADDER_MIN_ENGAGED": _n("int", 0, 500, 50, "", "", ("topic_ladder",)),   # v12 V2c-b: the promote rule (Growth and Learning)
    "OPENING_FIT": _e(("auto", "fill", "whole"), (), "", ("opening_shown",)), "OPENING_ENLARGE_MAX": _n("float", 1, 3, 0.5, "up", GATE, ("opening_shown",)),   # v12 V2c-b2b: the opening window (Visual Production); wider = softer
    "REEL1_DELAY_MIN": _n("int", 0, 120, 30), "REEL2_DELAY_MIN": _n("int", 60, 1440, 180), "NEXT_LINK_ON": _b(),
    "IG_TRIAL_REELS_ON": _b(checks=("release_sheet",)), "SHORT_THUMB_ON": _b(checks=("release_sheet",)),      # v12 V2c-b2: two rows of a Short's release sheet (reach trials: neither costs money nor weakens a gate)
    "BRAIN_ON": _b("off", "the channel stops learning from its own videos"), "BRAIN_HOLDOUT": _n("float", 0.05, 0.5, 0.1),
    "BUDGET_GUARD_PCT": _n("int", 50, 100, 10, "up", COST), "BREAKOUT_FUND_CAP_INR": _n("int", 0, 3000, 500, "up", COST), "AUTO_FIX_PAID_INR": _n("int", 0, 100, 20, "up", COST),
    "PREFLIGHT_ON": _b("off", "paid steps would start without the free health checks"),
    "ORG_SLA_HOURS": _j("memo", 0.25, 720, "always", "it changes how fast the organisation must act", pair=True),
    "PALACE_PLAYBOOK_TOKENS": _n("int", 200, 6000, 600, "", "", ("palace_health",)), "PALACE_PLAYBOOK_TOKENS_BY_DEPT": _j("dept", 200, 6000, checks=("palace_health",)),
    "PALACE_LIMITS_SHARE": _n("float", 0.1, 0.9, 0.2, "", "", ("palace_health",)), "PALACE_REVIEW_DAYS": _j("kind", 0, 3650, checks=("palace_health",)),
    "PALACE_KIND_CAPS": _j("kind", 1, 5000, checks=("palace_health",)),
}

def owner_of(key):
    """The department whose lever this cell is ('' = nobody's)."""
    return next((d for d, v in REG.DEPTS.items() if key in v["levers"]), "")

def _num(sp, v):
    """A number the way the cell holds it (ints without a point, floats without trailing zeros); None = not a number of this kind."""
    try: f = float(str(v).strip())
    except (TypeError, ValueError): return None
    if isinstance(v, bool) or f != f or f in (float("inf"), float("-inf")): return None
    if sp["kind"] == "int": return int(f) if f == int(f) else None
    return f

def _json_keys(sp):
    if sp["keys"] == "dept": return set(DEPARTMENTS)
    if sp["keys"] == "kind":
        from whatifs.org import palace as PAL
        return set(PAL.KINDS)
    from whatifs.org import schemas as SC
    return {t for t, d in SC.TYPES.items() if d["mode"] != "record"}

def _norm(sp, value):
    """(the value as the cell will hold it, why it is refused or '')."""
    k = sp["kind"]
    if k in ("int", "float"):
        v = _num(sp, value)
        if v is None: return "", f"needs {'a whole number' if k == 'int' else 'a number'} (got '{str(value)[:30]}')"
        if not sp["lo"] <= v <= sp["hi"]: return "", f"{v:g} is outside the allowed range {sp['lo']:g} to {sp['hi']:g}"
        return f"{v:g}", ""
    if k == "bool":
        s = str(value).strip().upper()
        if value is True or s in ("TRUE", "YES", "ON", "1"): return "TRUE", ""
        if value is False or s in ("FALSE", "NO", "OFF", "0"): return "FALSE", ""
        return "", f"needs TRUE or FALSE (got '{str(value)[:30]}')"
    if k == "enum":
        s = str(value).strip()
        return (s, "") if s in sp["values"] else ("", f"must be one of: {', '.join(sp['values'])} (got '{s[:30]}')")
    if k == "days":
        ds = [d.strip().title() for d in (value if isinstance(value, (list, tuple)) else str(value).split(",")) if str(d).strip()]
        if not ds or any(d not in DAYS for d in ds) or len(set(ds)) != len(ds): return "", f"needs weekdays out of {', '.join(DAYS)} (got '{str(value)[:40]}')"
        return ",".join(sorted(ds, key=DAYS.index)), ""
    if k == "csv":
        from whatifs import contract as CON
        ids = [x.strip() for x in (value if isinstance(value, (list, tuple)) else str(value).split(",")) if str(x).strip()]; known = {f[0] for f in CON.FEATURES}
        bad = [x for x in ids if x not in known]
        return ("", f"names a check that does not exist ({bad[0]})") if bad else (",".join(sorted(set(ids))), "")
    j = value
    if isinstance(j, str):
        try: j = json.loads(j) if j.strip() else {}
        except ValueError: return "", "is not valid JSON"
    if not isinstance(j, dict): return "", "needs a JSON object"
    keys = _json_keys(sp); out = {}
    for kk, vv in j.items():
        if kk not in keys: return "", f"names '{str(kk)[:30]}', which is not one of its keys"
        vals = vv if sp["pair"] else [vv]
        if sp["pair"] and (not isinstance(vv, (list, tuple)) or len(vv) != 2): return "", f"'{kk}' needs two numbers: [acknowledge hours, resolve hours]"
        nums = [_num({"kind": "float"}, x) for x in vals]
        if any(x is None or not sp["lo"] <= x <= sp["hi"] for x in nums): return "", f"'{kk}' is outside the allowed range {sp['lo']:g} to {sp['hi']:g}"
        if sp["pair"] and nums[0] > nums[1]: return "", f"'{kk}': the acknowledge clock cannot be longer than the resolve clock"
        out[kk] = [float(f"{x:g}") for x in nums] if sp["pair"] else (int(nums[0]) if nums[0] == int(nums[0]) else nums[0])
    return (json.dumps(out, sort_keys=True) if out else ""), ""

def same(key, a, b):
    """Do two cell values mean the same for this lever? (A Sheet may give a number or a switch back in another spelling.)"""
    sp = LEVERS.get(key) or {}; a, b = str(a if a is not None else "").strip(), str(b if b is not None else "").strip()
    if sp.get("kind") in ("int", "float"):
        x, y = _num({"kind": "float"}, a), _num({"kind": "float"}, b)
        return x is not None and y is not None and abs(x - y) < 1e-9
    if sp.get("kind") == "bool": return (a.upper() in ("TRUE", "YES", "ON", "1")) == (b.upper() in ("TRUE", "YES", "ON", "1"))
    if sp.get("kind") == "json":
        try: return json.loads(a or "{}") == json.loads(b or "{}")
        except ValueError: return a == b
    return a == b

def _owner_reason(sp, key, old, new):
    """Why the owner must approve this move ('' = the department may make it by itself)."""
    o = sp["owner"]; why = sp["why"] or "it is yours to decide"
    if not o or same(key, old, new): return ""
    if o == "always": return why
    if sp["kind"] in ("int", "float"):
        a, b = _num({"kind": "float"}, old), _num({"kind": "float"}, new)
        if a is None: return f"the cell holds '{old}', which is not a number, so the direction cannot be judged"
        return why if (o == "up" and b > a) or (o == "down" and b < a) else ""
    if sp["kind"] == "bool": return why if (o == "off" and new == "FALSE") or (o == "on" and new == "TRUE") else ""
    if sp["kind"] == "enum": return why if new in o else ""
    return why

def check(dept, key, value):
    """Judge one setting change before anything is written. Returns {'old', 'new', 'why', 'owner'}: why = the reason it is refused ('' = allowed);
    owner = why it needs the owner's tap first ('' = it does not). A cell nobody registered, a cell of another department, a cell no code reads,
    a value of the wrong type, outside the range or further than one step away are all refused - never clamped, never guessed."""
    from whatifs import core, truth as TRU
    out = {"old": "", "new": "", "why": "", "owner": ""}; key = str(key or "").strip(); sp = LEVERS.get(key)
    if sp is None or key not in core.DEFAULTS:
        out["why"] = f"{key or 'the target'} is not a registered lever: no ticket may change it (a change no lever can make is a code change: lever class E, to D12)"; return out
    if not REG.may_change(dept, key): out["why"] = f"{key} is a lever of {owner_of(key) or 'no department'}, not of {dept}"; return out
    if key in TRU.unread_settings(): out["why"] = f"{key} is a cell no code reads: turning it would change nothing"; return out
    out["old"] = old = str(core.settings().get(key, core.DEFAULTS[key][0])).strip()
    new, bad = _norm(sp, value)
    if bad: out["why"] = f"{key} {bad}"; return out
    if sp["kind"] in ("int", "float"):
        a, b = _num({"kind": "float"}, old), float(new)
        if a is not None and abs(b - a) > sp["step"] + 1e-9:
            out["why"] = f"{key}: {old} to {new} is more than one step ({sp['step']:g}); move it in steps so each one can be judged"; return out
    out["new"] = new; out["owner"] = _owner_reason(sp, key, old, new)
    return out

def issues():
    """Is the lever table honest? Every lever of the registry has a rule here and the other way round, its default is a value the rule itself
    accepts, every check it names exists, and no lever is a cell that no code reads."""
    from whatifs import core, truth as TRU
    p = []; reg = {k: d for d, v in REG.DEPTS.items() for k in v["levers"]}
    p += [f"lever {k} of {reg[k]} has no rule in levers.LEVERS (type, range, step, owner direction)" for k in sorted(set(reg) - set(LEVERS))]
    p += [f"levers.LEVERS has a rule for {k}, which is no department's lever" for k in sorted(set(LEVERS) - set(reg))]
    try:
        from whatifs import contract as CON
        ids = {f[0] for f in CON.FEATURES}
    except Exception as e: ids = None; p.append(f"the contract could not be read: {e}")
    dead = set(TRU.unread_settings())
    for k, sp in sorted(LEVERS.items()):
        if k not in core.DEFAULTS: p.append(f"lever {k} is not a Settings cell"); continue
        if k in dead: p.append(f"lever {k} is a cell no code reads")
        new, bad = _norm(sp, core.DEFAULTS[k][0])
        if bad: p.append(f"lever {k}: its own default {bad}")
        if ids is not None: p += [f"lever {k} is judged by check '{c}', which does not exist" for c in sp["checks"] if c not in ids]
        if sp["owner"] and not sp["why"]: p.append(f"lever {k} needs the owner in one direction but does not say why")
    return p

def merge_scope(files, need_tests=True):
    """(inside, reasons): may this pull request merge without the owner? Judged on the REAL diff, never on what the request or the builder said:
    only NEW test files (tests/test_*.py) and the regenerated SYSTEM.md; nothing deleted, nothing else touched, at least one new test, a bounded size."""
    why = []; added = tests = 0
    if not S("EXEC_AUTO_MERGE_ON", bool): why.append("automatic merge is switched off (EXEC_AUTO_MERGE_ON)")
    if not files: why.append("the diff could not be read")
    for f in files or []:
        name = str(f.get("filename") or ""); status = str(f.get("status") or "")
        try: add, dele = int(f.get("additions") or 0), int(f.get("deletions") or 0)
        except (TypeError, ValueError): add, dele = MERGE_MAX_LINES + 1, 1
        added += add
        if re.fullmatch(r"tests/test_\w+\.py", name):
            if status != "added" or dele: why.append(f"{name}: an existing test is changed (only new test files merge by themselves)")
            tests += len(re.findall(r"^\+\s*def test_\w+", str(f.get("patch") or ""), re.M))
        elif name == "docs/CURRENT/SYSTEM.md" and status == "modified": pass
        else: why.append(f"{name or '?'}: outside the automatic scope (new test files only)")
    if added > MERGE_MAX_LINES: why.append(f"{added} added lines (more than {MERGE_MAX_LINES}): too big to merge unread")
    if need_tests and files and not tests: why.append("the diff adds no test")
    return (not why), why
