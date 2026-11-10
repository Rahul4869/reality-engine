"""Memo schemas: every memo type the organisation can send - sender, audience, body, clocks, statuses and legal moves as data - with the validator that runs on every write. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, hashlib, json, re
from whatifs.core import S, iso, now_utc
from whatifs.org import DEPARTMENTS
from whatifs.org.palace import EVIDENCE as _TRUST, INJECT, _date_ok

ANY = "*"
URGENCIES = ("P0", "P1", "P2")                                   # P0 = do or die
URGENCY_FACTOR = {"P0": 0.25, "P1": 1.0, "P2": 2.0}              # how an urgency stretches or shrinks a type's two clocks
STATUSES = ("open", "acknowledged", "in_progress", "escalated", "resolved", "rejected")
TERMINAL = ("resolved", "rejected")                              # a terminal memo accepts no further change; a recurrence is a new, linked memo
LIVE = tuple(s for s in STATUSES if s not in TERMINAL)
# to-status -> (from-statuses, roles). Roles: holder = whoever must act now (the addressed department, the Council or the owner, by level);
# verifier = the sender, or the Execution Engine, where the type names it (the engine closes only with a row of its own ledger); owner; clock = the SLA watchdog.
MOVES = {
    "acknowledged": (("open", "escalated"), ("holder",)),
    "in_progress":  (("open", "acknowledged", "escalated"), ("holder",)),
    "escalated":    (LIVE, ("clock", "holder")),
    "resolved":     (LIVE, ("holder", "owner", "verifier")),
    "rejected":     (LIVE, ("holder", "owner")),
}
LADDER = ("department", "C", "owner")                            # level 0, 1, 2: who holds a memo after each escalation
SUBJECT = (8, 140); DONE_WHEN = (10, 300); CONSTRAINT = (5, 240); MAX_CONSTRAINTS = 8; BODY_MAX = 6000; REASON_MIN = 20
EVIDENCE_TYPES = tuple(_TRUST)                                    # the Palace's own evidence vocabulary: a memo's evidence can enter the Palace unchanged
RESEARCH_KINDS = ("technique", "policy", "tool", "revalidate", "owner", "problem", "audience")   # v12 B5: what a research question is about (policy / tool / revalidate are FACTS)

def _s(mn=1, mx=400): return {"type": "string", "minLength": mn, "maxLength": mx}
def _arr(items, mn=0, mx=12): return {"type": "array", "minItems": mn, "maxItems": mx, "items": items}
def _obj(required, props): return {"type": "object", "required": list(required), "properties": props, "additionalProperties": False}
_NUM = {"type": "number", "minimum": 0}
_SCORE = {"type": "number", "minimum": 0, "maximum": 10}
_DEPT = {"type": "string", "enum": sorted(DEPARTMENTS)}
EVIDENCE = _arr(_obj(("source", "date", "type"), {"source": _s(3, 200), "url": _s(0, 300), "date": _s(8, 25), "type": {"type": "string", "enum": list(EVIDENCE_TYPES)}, "finding": _s(0, 600)}))

# Every memo type as data. mode: ask = someone must do something and prove it; inform = every addressee must read it; record = stored, no clock.
# ack_h / resolve_h: the two clocks at urgency P1 (by_urgency overrides both; fixed = the urgency never changes them). done_when: the fixed end
# condition of a process memo; None = the sender must state it. resolved_by: the only kinds of proof that may close it.
TYPES = {
    "owner_memo": {
        "from": ("D0",), "to": ANY, "mode": "ask", "urgency": "P0", "ack_h": 1, "resolve_h": 24, "fixed": True, "done_when": None, "owner_visible": True,
        "resolved_by": ("ticket_executed", "owner_answer"), "reject_by": ("owner",),
        "purpose": "the owner's words VERBATIM, the interpretation and the departments it affects",
        "sla": "acknowledged within one tick (1 h allows for a late cron), resolved within 24 h or escalated",
        "body": _obj(("verbatim", "interpretation"), {"verbatim": _s(1, 4000), "interpretation": _s(10, 800), "channel": _s(0, 40), "received": _s(0, 25)}),
    },
    "research_memo": {
        "from": ("D2",), "to": ("D3",), "mode": "ask", "urgency": "P1", "ack_h": 24, "resolve_h": 48, "needs_evidence": True,
        "done_when": "the Review Board has scored it and said accept, test or reject", "resolved_by": ("assessment_memo",),
        "purpose": "a research question, what was found, the dated sources, proposed actions, expected impact, cost and the departments it targets",
        "sla": "assessed within 48 h",
        "body": _obj(("question", "findings", "confidence", "proposed_actions", "expected_impact", "target_depts"),
                     {"question": _s(10, 300), "findings": _arr(_s(10, 600), 1, 12), "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                      "proposed_actions": _arr(_s(10, 400), 1, 8), "expected_impact": _s(10, 400), "cost_inr": _NUM, "target_depts": _arr(_DEPT, 1, 15),
                      # v12 B5 (optional, written by whatifs/org/rnd.py): what kind of question, which gap started it, the evidence ceiling code computed,
                      # the pre-registered predictions (action index, metric, direction, horizon in videos) and the Palace item a re-validation is about
                      "kind": {"type": "string", "enum": list(RESEARCH_KINDS)}, "gap": _obj(("source", "ref"), {"source": _s(2, 40), "ref": _s(1, 200)}),
                      "evidence_ceiling": _SCORE, "palace_ref": _s(0, 60), "sources_dropped": {"type": "object"},
                      "predictions": _arr(_obj(("action", "metric", "direction", "horizon_videos"), {"action": {"type": "integer", "minimum": 0, "maximum": 7}, "metric": _s(2, 40),
                                                "direction": {"type": "string", "enum": ["up", "down"]}, "horizon_videos": {"type": "integer", "minimum": 1, "maximum": 8}}), 0, 8)}),
    },
    "assessment_memo": {
        "from": ("D3",), "to": ("C",), "mode": "ask", "urgency": "P1", "ack_h": 168, "resolve_h": 168,
        "done_when": "the Council has decided on it and issued tickets or said no", "resolved_by": ("decision_memo",),
        "purpose": "the blind cross-family jury's scores for one memo and its verdict",
        "sla": "taken up by the Council within 7 days",
        "body": _obj(("memo_ref", "scores", "verdict", "jury", "rationale"),
                     {"memo_ref": _s(3, 40), "verdict": {"type": "string", "enum": ["accept", "test", "reject"]}, "jury": _arr(_s(2, 60), 2, 6), "rationale": _s(20, 800),
                      "scores": _obj(("evidence", "novelty", "impact", "feasibility", "cost", "risk"), {k: _SCORE for k in ("evidence", "novelty", "impact", "feasibility", "cost", "risk")}),
                      # v12 B5 (optional, written by whatifs/org/board.py): the share of "yes" per checklist question per family, the planted canary's
                      # result, the research memo's kind and ceiling - everything code needs to RE-COMPUTE the verdict
                      "checklist": {"type": "object"}, "canary": _s(0, 120), "kind": {"type": "string", "enum": list(RESEARCH_KINDS)}, "evidence_ceiling": _SCORE,
                      "author_family": _s(0, 20), "predictions": {"type": "integer", "minimum": 0}, "cost_inr": _NUM}),
    },
    "creative_memo": {
        "from": ("D4", "D5", "D6", "D7"), "to": ("C",), "mode": "ask", "urgency": "P2", "ack_h": 84, "resolve_h": 84,
        "done_when": "the Council has decided on it and issued tickets or said no", "resolved_by": ("decision_memo", "assessment_memo"),
        "purpose": "a new idea, an experiment proposal, a joke or hook bank, a world-building proposal",
        "sla": "taken up by the Council within 7 days",
        "body": _obj(("idea", "kind", "rationale"), {"idea": _s(20, 1200), "kind": {"type": "string", "enum": ["idea", "experiment", "bank", "world_building"]},
                                                    "rationale": _s(20, 800), "expected_impact": _s(0, 400), "cost_inr": _NUM}),
    },
    "performance_memo": {
        "from": ("D10",), "to": ANY, "mode": "inform", "urgency": "P1", "ack_h": 24, "resolve_h": 24, "needs_evidence": True, "done_when": "every addressed department has loaded it",
        "resolved_by": ("read_by_all", "closed_unread"),
        "purpose": "48 h / 7 d / 28 d outcomes of a video, changes in technique evidence, breakouts",
        "sla": "sent to every department at once; each must load it within 24 h",
        "body": _obj(("window", "video", "metrics"), {"window": {"type": "string", "enum": ["48h", "7d", "28d", "breakout"]}, "video": _s(3, 60),
                                                     "metrics": {"type": "object", "minProperties": 1}, "changes": _arr(_s(5, 300), 0, 12)}),
    },
    "problem_memo": {
        "from": ANY, "to": ANY, "mode": "ask", "urgency": "P1", "ack_h": 2, "resolve_h": 24, "needs_evidence": True, "done_when": None, "recurring": True, "max_attempts": 2,
        "verifier": "sender", "resolved_by": ("repair_verified", "owner_waived", "episode_closed", "repair_memo"),
        "purpose": "what failed, where, the evidence and the attempt count",
        "sla": "at most 2 automatic repair attempts, then the Council, then the owner",
        "body": _obj(("what_failed", "where", "attempt"), {"what_failed": _s(5, 400), "where": _s(3, 200), "attempt": {"type": "integer", "minimum": 1},
                                                          "check": _s(0, 60), "stage": _s(0, 20), "error_class": _s(0, 80)}),
    },
    "repair_memo": {
        "from": ANY, "to": ("D8",), "mode": "ask", "urgency": "P1", "ack_h": 24, "resolve_h": 24, "needs_evidence": True,
        "done_when": "QA has re-run the check and it passed", "resolved_by": ("repair_verified", "repair_refused"),
        "purpose": "the fix that was applied and the proof that it passed again",
        "sla": "sent with the re-run; verified within 24 h",
        "body": _obj(("problem_ref", "fix", "proof"), {"problem_ref": _s(3, 40), "fix": _s(10, 800), "proof": _s(10, 400)}),
    },
    "decision_memo": {
        "from": ("C",), "to": ANY, "mode": "inform", "urgency": "P1", "ack_h": 24, "resolve_h": 24, "done_when": "every addressed department has loaded it",
        "resolved_by": ("read_by_all", "closed_unread"),
        "purpose": "what changes, why (the memos it cites), the lever class, the tickets and whether the owner must approve",
        "sla": "tickets are created with the decision; each department loads it within 24 h",
        "body": _obj(("decision", "why", "memos_cited", "lever_class", "tickets", "owner_approval"),
                     {"decision": _s(20, 800), "why": _s(20, 800), "memos_cited": _arr(_s(3, 40), 1, 20), "lever_class": {"type": "string", "enum": ["A", "B", "C", "D", "E", "none"]},
                      "tickets": _arr(_s(3, 40), 0, 20), "owner_approval": {"type": "boolean"}}),
    },
    "ticket": {
        "from": ("C",) + tuple(DEPARTMENTS), "to": ANY, "single": True, "mode": "ask", "urgency": "P1", "by_urgency": {"P0": (1, 6), "P1": (24, 48), "P2": (48, 168)},
        "done_when": None, "resolved_by": ("lever_verified", "rolled_back", "owner_answer"), "verifier": "engine", "await_days": 130,
        "purpose": "ONE executable change: lever, target, value or diff, acceptance test, rollback",
        "sla": "P0 6 h, P1 48 h, P2 7 days",
        "body": _obj(("lever_class", "target", "value", "acceptance_test", "rollback"),
                     {"lever_class": {"type": "string", "enum": ["A", "B", "C", "D", "E"]}, "target": _s(2, 200), "value": {}, "acceptance_test": _s(10, 400),
                      "rollback": _s(5, 400), "decision_ref": _s(0, 40)}),
    },
    "build_request": {
        "from": ("D12",), "to": ("D12",), "mode": "ask", "urgency": "P1", "ack_h": 24, "resolve_h": 72, "fixed": True, "done_when": None,
        "resolved_by": ("merged_verified", "owner_answer"), "verifier": "engine",
        "purpose": "a code change that no lever can make: the spec, the files, the tests to add and the acceptance",
        "sla": "a pull request within 72 h or escalated",
        "body": _obj(("spec", "files", "tests_to_add", "acceptance"), {"spec": _s(40, 4000), "files": _arr(_s(3, 200), 1, 30), "tests_to_add": _arr(_s(10, 400), 1, 20),
                                                                      "acceptance": _s(10, 600), "auto_merge": {"type": "boolean"}}),
    },
    "takeaway": {
        "from": ANY, "to": ("L",), "mode": "record", "urgency": "P2", "ack_h": 0, "resolve_h": 0, "done_when": "stored", "resolved_by": (),
        "purpose": "one atomic learning from one department run (kept in the Takeaways tab, proposed to the Palace when it is new)",
        "sla": "written by every department run",
        "body": _obj(("did", "next_time", "measures"), {"did": _s(20, 500), "worked": _arr(_s(5, 300), 0, 10), "failed": _arr(_s(5, 300), 0, 10), "next_time": _s(20, 400),
                                                       "measures": {"type": "object"}, "kind": {"type": "string", "enum": ["takeaway", "failure_lesson"]}}),
    },
}
ASK_TYPES = tuple(t for t, d in TYPES.items() if d["mode"] == "ask")
INFORM_TYPES = tuple(t for t, d in TYPES.items() if d["mode"] == "inform")
BOILERPLATE = re.compile(r"^\W*(?:n/?a|none|nothing|tbd|todo|ok|fine|good|same(?: as (?:before|last time|usual))?|no change|keep (?:going|it up|doing (?:it|this|that))|continue|"
                         r"do better|improve(?: quality| things)?|be better|try harder|as usual|see above)\W*$", re.I)

class MemoError(ValueError):
    """A memo or a takeaway was refused; .problems lists every reason."""
    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("; ".join(self.problems))

# ------------------------------------------------------------------ the small validator (the subset of JSON Schema the types above use)
_KIND = {"string": lambda v: isinstance(v, str), "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
         "integer": lambda v: isinstance(v, int) and not isinstance(v, bool), "boolean": lambda v: isinstance(v, bool),
         "array": lambda v: isinstance(v, list), "object": lambda v: isinstance(v, dict)}

def validate(schema, value, path="body"):
    """Problems of `value` against `schema` ([] = valid)."""
    out = []; t = schema.get("type")
    if t and not _KIND[t](value): return [f"{path} must be {t}"]
    if "enum" in schema and value not in schema["enum"]: out.append(f"{path} must be one of: {', '.join(map(str, schema['enum']))}")
    if isinstance(value, str):
        n = len(value.strip())
        if n < schema.get("minLength", 0): out.append(f"{path} is too short ({n} characters, needs {schema['minLength']})")
        if n > schema.get("maxLength", 10 ** 9): out.append(f"{path} is too long ({n} characters, limit {schema['maxLength']})")
    if _KIND["number"](value):
        if "minimum" in schema and value < schema["minimum"]: out.append(f"{path} must be at least {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]: out.append(f"{path} must be at most {schema['maximum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): out.append(f"{path} needs at least {schema['minItems']} entr{'y' if schema['minItems'] == 1 else 'ies'}")
        if len(value) > schema.get("maxItems", 10 ** 9): out.append(f"{path} has more than {schema['maxItems']} entries")
        if "items" in schema:
            for i, v in enumerate(value): out += validate(schema["items"], v, f"{path}[{i}]")
    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0): out.append(f"{path} needs at least {schema['minProperties']} field(s)")
        for k in schema.get("required", ()):
            if k not in value or value[k] in (None, ""): out.append(f"{path}.{k} is required")
        props = schema.get("properties") or {}
        for k, v in value.items():
            if k in props:
                if v not in (None, ""): out += validate(props[k], v, f"{path}.{k}")
            elif schema.get("additionalProperties") is False: out.append(f"{path}.{k} is not a field of this memo type")
    return out

def json_schema(mtype):
    """The whole memo of one type as a JSON Schema (draft 2020-12): what a caller hands to memos.write."""
    d = TYPES[mtype]
    props = {"type": {"const": mtype}, "from_dept": _DEPT, "to_depts": _arr({"type": "string", "enum": sorted(DEPARTMENTS) + ["all"]}, 1, 15),
             "subject": _s(*SUBJECT), "body": d["body"], "urgency": {"type": "string", "enum": list(URGENCIES)}, "done_when": _s(*DONE_WHEN),
             "constraints": _arr(_s(*CONSTRAINT), 0, MAX_CONSTRAINTS), "links": {"type": "object"}, "evidence": EVIDENCE, "cost_estimate": _NUM,
             "owner_visible": {"type": "boolean"}, "episode_id": _s(0, 40), "session_id": _s(0, 40), "dedupe_key": _s(0, 160)}
    req = ["type", "from_dept", "to_depts", "subject", "body"] + (["done_when"] if d["done_when"] is None else []) + (["evidence"] if d.get("needs_evidence") else [])
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": mtype, "description": d["purpose"], "type": "object", "required": req,
            "properties": props, "additionalProperties": False}

# ------------------------------------------------------------------ clocks and ids
def _sla_override():
    try:
        v = json.loads(S("ORG_SLA_HOURS") or "{}")
        return v if isinstance(v, dict) else {}
    except Exception: return {}

def hours(mtype, urgency):
    """(acknowledge hours, resolve hours) for a memo type at an urgency. Setting ORG_SLA_HOURS = {"type": [ack, resolve]} overrides the P1 clocks."""
    d = TYPES[mtype]; ov = _sla_override().get(mtype)
    if d.get("by_urgency") and not ov: return tuple(float(x) for x in d["by_urgency"][urgency])
    try: a, r = (float(ov[0]), float(ov[1])) if ov else (float(d["ack_h"]), float(d["resolve_h"]))
    except Exception: a, r = float(d["ack_h"]), float(d["resolve_h"])
    f = 1.0 if d.get("fixed") else URGENCY_FACTOR[urgency]
    return round(min(a, r) * f, 2), round(r * f, 2)

def clocks(mtype, urgency, now=None):
    now = now or now_utc(); a, r = hours(mtype, urgency)
    return iso(now + dt.timedelta(hours=a)), iso(now + dt.timedelta(hours=r))

def memo_id(mtype, from_dept, to_depts, dedupe_key):
    """The id IS the identity of the request (type, sender, audience, dedupe key): writing the same memo twice is a no-op, never a second memo."""
    raw = "|".join([mtype, from_dept, ",".join(sorted(to_depts)), str(dedupe_key)])
    return "M-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()

def body_hash(clean):
    core_ = {k: clean.get(k) for k in ("subject", "body", "done_when", "constraints", "urgency")}
    return hashlib.sha1(json.dumps(core_, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:12]

def _strings(v, skip=()):
    if isinstance(v, str): yield v
    elif isinstance(v, dict):
        for k, x in v.items():
            if k not in skip: yield from _strings(x)
    elif isinstance(v, list):
        for x in v: yield from _strings(x)

def _evidence(ev, now, p, need):
    if ev in (None, ""): ev = []
    bad = validate(EVIDENCE, ev, "evidence")
    if bad: p += bad[:4]; return []
    for e in ev:
        if not _date_ok(e.get("date"), now): p.append(f"evidence needs a real date that is not in the future (got '{e.get('date')}')")
    if need and not ev: p.append("this memo type needs evidence: at least one dated source")
    return [{k: str(e[k]).strip() for k in ("source", "url", "date", "type", "finding") if e.get(k)} for e in ev]

# ------------------------------------------------------------------ the write gate for memos
def check_memo(memo, now=None):
    """(clean memo, problems). Nothing is written to the Memos tab unless the problem list is empty."""
    p = []; m = dict(memo or {}); mtype = str(m.get("type") or "").strip()
    if mtype not in TYPES: return {}, [f"unknown memo type '{mtype}'"]
    if mtype == "takeaway": return {}, ["a takeaway is written by a department run (runner LEARN step), not as a memo"]
    d = TYPES[mtype]; extra = set(m) - set(json_schema(mtype)["properties"])
    if extra: p.append("unknown field(s): " + ", ".join(sorted(extra)))
    frm = str(m.get("from_dept") or "").strip()
    if frm not in DEPARTMENTS: p.append(f"unknown sender '{frm}'")
    elif d["from"] != ANY and frm not in d["from"]: p.append(f"a {mtype} is sent by {' / '.join(d['from'])}, not by {frm}")
    to = m.get("to_depts"); to = [to] if isinstance(to, str) else list(to or [])
    to = [str(x).strip() for x in to]
    if "all" in to: to = [x for x in DEPARTMENTS if x != frm]
    to = list(dict.fromkeys(to))
    if not to: p.append("to_depts must name at least one department")
    elif any(x not in DEPARTMENTS for x in to): p.append("to_depts names an unknown department: " + ", ".join(x for x in to if x not in DEPARTMENTS))
    elif d["to"] != ANY and any(x not in d["to"] for x in to): p.append(f"a {mtype} goes to {' / '.join(d['to'])}")
    if d.get("single") and len(to) != 1: p.append(f"a {mtype} has exactly one addressee (one executable change, one owner)")
    urg = str(m.get("urgency") or d["urgency"]).strip().upper()
    if urg not in URGENCIES: p.append(f"urgency must be one of {', '.join(URGENCIES)}")
    subject = re.sub(r"\s+", " ", str(m.get("subject") or "")).strip()
    if not SUBJECT[0] <= len(subject) <= SUBJECT[1]: p.append(f"subject must be {SUBJECT[0]}-{SUBJECT[1]} characters (has {len(subject)})")
    body = m.get("body")
    p += validate(d["body"], body if isinstance(body, dict) else {}, "body") if isinstance(body, dict) else ["body must be an object"]
    if isinstance(body, dict) and len(json.dumps(body, ensure_ascii=False, default=str)) > BODY_MAX:
        p.append(f"body is over {BODY_MAX} characters: store the long material (Drive, a Palace item) and link it")
    done = re.sub(r"\s+", " ", str(m.get("done_when") or d["done_when"] or "")).strip()
    if d["done_when"] is None and not DONE_WHEN[0] <= len(done) <= DONE_WHEN[1]:
        p.append(f"done_when is required for a {mtype}: say what proves it is finished ({DONE_WHEN[0]}-{DONE_WHEN[1]} characters)")
    cons = m.get("constraints") or []
    cons = [cons] if isinstance(cons, str) else list(cons)
    cons = [re.sub(r"\s+", " ", str(c)).strip() for c in cons]
    if len(cons) > MAX_CONSTRAINTS: p.append(f"at most {MAX_CONSTRAINTS} constraints (merge them; they are never shortened later)")
    if any(not CONSTRAINT[0] <= len(c) <= CONSTRAINT[1] for c in cons): p.append(f"every constraint must be {CONSTRAINT[0]}-{CONSTRAINT[1]} characters (a constraint is never cut, so it must fit)")
    links = m.get("links") or {}
    if not isinstance(links, dict) or len(links) > 10: p.append("links must be an object with at most 10 entries"); links = {}
    ev = _evidence(m.get("evidence"), now, p, d.get("needs_evidence"))
    try: cost = float(m.get("cost_estimate") or 0)
    except (TypeError, ValueError): cost = -1
    if cost < 0: p.append("cost_estimate must be a number of rupees, 0 or more")
    safe = [subject, done] + cons + list(_strings(body, skip=("verbatim",)))
    if any(INJECT.search(x) for x in safe): p.append("the text reads like an instruction to a model; a memo is information (quote it as evidence instead)")
    ov = m.get("owner_visible"); ov = d.get("owner_visible", d["mode"] == "ask") if ov in (None, "") else ov in (True, 1, "1", "TRUE", "True", "true")
    clean = {"type": mtype, "from_dept": frm, "to_depts": to, "urgency": urg, "subject": subject, "body": body if isinstance(body, dict) else {}, "done_when": done,
             "constraints": cons, "links": {str(k)[:40]: v for k, v in links.items()}, "evidence": ev, "cost_estimate": max(0.0, round(cost, 2)), "owner_visible": bool(ov),
             "episode_id": str(m.get("episode_id") or "")[:40], "session_id": str(m.get("session_id") or "")[:40]}
    clean["dedupe_key"] = str(m.get("dedupe_key") or "")[:160] or hashlib.sha1(json.dumps([subject, clean["body"]], sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
    clean["body_hash"] = body_hash(clean)
    return clean, p

# ------------------------------------------------------------------ the write gate for takeaways
def _words(text): return {w for w in re.findall(r"[a-z][a-z0-9_]{2,}", str(text or "").lower())}

def check_takeaway(t, now=None):
    """(clean takeaway, problems). A takeaway must be concrete (a measured value or dated evidence), grounded (its words name what was measured) and
    usable (a real instruction for next time); an empty or stock one is refused. It never carries a score of its own."""
    p = []; t = dict(t or {}); dept = str(t.get("dept") or "").strip()
    if dept not in DEPARTMENTS: p.append(f"unknown department '{dept}'")
    body = {k: t.get(k) for k in ("did", "worked", "failed", "next_time", "measures", "kind") if t.get(k) not in (None, "")}
    body.setdefault("measures", {})
    for k in ("worked", "failed"):
        if isinstance(body.get(k), str): body[k] = [body[k]]
    p += validate(TYPES["takeaway"]["body"], body, "takeaway")
    meas = body.get("measures") if isinstance(body.get("measures"), dict) else {}
    nums = {k: v for k, v in meas.items() if _KIND["number"](v)}
    ev = _evidence(t.get("evidence"), now, p, False)
    did, nxt = str(body.get("did") or ""), str(body.get("next_time") or "")
    lists = [str(x) for k in ("worked", "failed") for x in (body.get(k) or [])]
    if not nums and not any(len(str(e.get("finding") or "")) >= 10 for e in ev):
        p.append("not concrete: a takeaway needs at least one measured value, or dated evidence that says what was found")
    if BOILERPLATE.match(nxt) or len({w for w in _words(nxt)}) < 4: p.append("next_time is not an instruction anyone could follow (stock phrase or too thin)")
    if BOILERPLATE.match(did): p.append("did is a stock phrase, not what was done")
    if not lists: p.append("say at least one thing that worked or one thing that failed")
    text = " ".join([did, nxt] + lists).lower()
    if nums and not any(str(k).lower().replace("_", " ") in text.replace("_", " ") or re.search(rf"(?<![\d.]){re.escape(_num(v))}(?![\d.])", text) for k, v in nums.items()):
        p.append("not grounded: the text names none of the measured values")
    if "confidence" in t or "score" in t: p.append("a takeaway cannot score itself: trust is computed from the evidence type, outcomes are measured by D10")
    if any(INJECT.search(x) for x in [did, nxt] + lists): p.append("the text reads like an instruction to a model")
    clean = {"dept": dept, "did": re.sub(r"\s+", " ", did).strip(), "worked": [x.strip() for x in (body.get("worked") or [])], "failed": [x.strip() for x in (body.get("failed") or [])],
             "next_time": re.sub(r"\s+", " ", nxt).strip(), "measures": meas, "evidence": ev, "kind": body.get("kind") or "takeaway"}
    return clean, p

def _num(v):
    """A number the way a takeaway prints it (no trailing .0)."""
    return str(int(v)) if float(v).is_integer() else str(round(float(v), 2))
