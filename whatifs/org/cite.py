"""Creative citations: the rule the creative model calls receive, quote-anchored verification of every Palace item a model says it applied, creative memos with the same-idea guard, and the episode checks palace_injected / palace_cited. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, math, re
from whatifs.core import S, store, iso, now_utc
from whatifs.org import registry as REG

QUOTE_MIN, QUOTE_MAX = 4, 40          # words a citation's quote must have (shorter proves nothing, longer is a copy of the whole answer)
MATCH = 0.8                           # share of the quote's words that must appear, in order, inside a window of the output (tolerates small edits)
MAX_CITES = 20                        # citations kept per run (receipt size)
PROPOSAL_KINDS = ("idea", "experiment", "bank", "world_building")
SAME_LOOKBACK = 60                    # earlier creative memos a new proposal is compared with
RULE = ("PALACE CITATIONS (mandatory): your JSON must also contain \"applied_items\": a list of {\"id\": \"<an id from the playbook above>\", "
        "\"where\": \"<4-30 words copied EXACTLY from your own answer, where you applied it>\"} - one entry per playbook line you really applied. "
        "LIMIT lines always apply; do not list them. Code checks every quote against your final answer: list nothing you did not apply.")
MUST = "MUST CITE (continuity): [{ids}] - the show's own history. Call back to it in ONE spoken line of the narration and cite that exact line."
PROPOSE = ("PROPOSAL (optional, at most one): if this work gave you ONE new idea for the show that the Council should decide on, add \"proposal\": "
           "{\"kind\": \"idea|experiment|bank|world_building\", \"idea\": \"<20-600 characters>\", \"rationale\": \"<why it would make viewers come back>\"}.")

def prompt_on():
    """Do the creative departments put their playbook INTO the model prompts? (ORG_PROMPT_INJECT; off = they go back to brief mode, the checks say NA.)"""
    return S("ORG_PROMPT_INJECT", bool)

def block(pb_text, task, spec, must_ids=()):
    """The text one creative call receives: the playbook, the citation rule, a continuity debt for the narration tasks, an invitation to propose."""
    parts = [pb_text, RULE]
    if must_ids and any(str(task).startswith(t) for t in spec.get("must", ())): parts.append(MUST.format(ids="], [".join(must_ids)))
    if any(str(task).startswith(t) for t in spec.get("propose", ())): parts.append(PROPOSE)
    return "\n".join(p for p in parts if p)

# ------------------------------------------------------------------ quotes
def tokens(text):
    return re.findall(r"[a-z0-9]+", str(text or "").lower())

def flat(obj, _out=None):
    """Every text inside an output (dicts, lists, strings), joined: the material a quote must be found in."""
    out = [] if _out is None else _out
    if isinstance(obj, str): out.append(obj)
    elif isinstance(obj, dict): [flat(v, out) for v in obj.values()]
    elif isinstance(obj, (list, tuple)): [flat(v, out) for v in obj]
    elif obj is not None and not isinstance(obj, (int, float, bool)): out.append(str(obj))
    return out if _out is not None else "\n".join(out)

def _lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b): cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]

def found(quote, text_tokens):
    """Is this quote in the output? Exact (word for word) or MATCH of its words in order inside a window a little longer than the quote."""
    q = tokens(quote); n = len(q)
    if not (QUOTE_MIN <= n <= QUOTE_MAX) or not text_tokens: return False
    if " " + " ".join(q) + " " in " " + " ".join(text_tokens) + " ": return True
    need = math.ceil(n * MATCH - 1e-9); w = n + max(2, n // 2); starts = set(q[:n - need + 1])
    for i, t in enumerate(text_tokens):
        if t in starts and _lcs(q, text_tokens[i:i + w]) >= need: return True
    return False

def verify(cites, items, limits, output):
    """{'verified', 'unverified', 'ghost', 'limits', 'quotes'}: a citation counts only when its id was in the injected playbook and its quote is found in
    the final output. Ghosts (ids that were never offered) and unverified claims are kept for the record and never counted as applied."""
    toks = tokens(flat(output)); items = set(items); out = {"verified": [], "unverified": [], "ghost": [], "limits": [], "quotes": {}}
    for c in list(cites or [])[:MAX_CITES * 3]:
        if not isinstance(c, dict): continue
        iid = str(c.get("id") or "").strip().strip("[]"); where = str(c.get("where") or "")[:400]
        if not iid: continue
        if iid not in items: lane = "ghost"
        elif iid in limits: lane = "limits"
        elif found(where, toks): lane = "verified"
        else: lane = "unverified"
        if iid not in out[lane]: out[lane].append(iid)
        if lane == "verified" or iid not in out["quotes"]: out["quotes"][iid] = where[:200]
    out["unverified"] = [i for i in out["unverified"] if i not in out["verified"]]
    return out

# ------------------------------------------------------------------ creative memos (proposals) with the same-idea guard
def _words(text):
    return {w for w in tokens(text) if len(w) > 3}

def same(a, b):
    """Overlap of two ideas' word sets (Jaccard)."""
    A, B = _words(a), _words(b)
    return len(A & B) / len(A | B) if A and B else 0.0

def proposals_to_memos(dept, proposals, st=None, now=None):
    """([creative_memo, ...], stats): at most CREATIVE_MEMO_MAX_PER_RUN valid proposals; one that overlaps an earlier creative memo (or another of this run)
    by CREATIVE_MEMO_SAME_MAX or more is dropped - the Council must see distinct options, not copies of one idea."""
    from whatifs.org import memos as MEM, schemas as SC
    stats = {"proposals": 0, "kept": 0, "dropped_same": 0, "dropped_invalid": 0}
    if dept not in SC.TYPES["creative_memo"]["from"]: return [], stats
    st = st or store(); now = now or now_utc(); cap = max(0, int(S("CREATIVE_MEMO_MAX_PER_RUN", float) or 0)); lim = float(S("CREATIVE_MEMO_SAME_MAX", float) or 0.5)
    try: earlier = [str((m.get("body") or {}).get("idea") or "") for m in MEM.find(st, live=False, type="creative_memo")][-SAME_LOOKBACK:]
    except Exception: earlier = []
    out = []
    for p in list(proposals or [])[:8]:
        if not isinstance(p, dict): continue
        stats["proposals"] += 1
        idea, kind, why = str(p.get("idea") or "").strip(), str(p.get("kind") or "").strip(), str(p.get("rationale") or "").strip()
        memo = {"type": "creative_memo", "from_dept": dept, "to_depts": ["C"], "urgency": "P2", "subject": f"{dept} proposes: {idea}"[:140],
                "body": {"idea": idea[:1200], "kind": kind, "rationale": why[:800]}, "dedupe_key": "creative|" + hashlib.sha1(" ".join(sorted(_words(idea))).encode("utf-8")).hexdigest()[:16]}
        if str(p.get("expected_impact") or "").strip(): memo["body"]["expected_impact"] = str(p["expected_impact"])[:400]
        if kind not in PROPOSAL_KINDS or SC.check_memo(memo, now)[1]: stats["dropped_invalid"] += 1; continue
        if any(same(idea, e) >= lim for e in earlier + [m["body"]["idea"] for m in out]): stats["dropped_same"] += 1; continue
        if len(out) >= cap: continue
        out.append(memo)
    stats["kept"] = len(out)
    return out, stats

# ------------------------------------------------------------------ the episode checks
def _receipt(row, step):
    try: steps = json.loads(row.get("steps") or "[]")
    except (TypeError, ValueError): return {}
    return next((s for s in steps if isinstance(s, dict) and s.get("step") == step), {})

def _latest(rows, dept, trigger, ep):
    cand = [r for r in rows if r.get("dept") == dept and r.get("trigger") == trigger and str(r.get("episode_id") or "") == ep]
    return max(cand, key=lambda r: int(float(r.get("attempt") or 0))) if cand else None

def creative_runs(ep, st=None):
    """[(dept, trigger, the Sessions row that did the work or None, how)] for the episode's creative runs. An adopted pre-production draft is judged
    by the D4 'draft' run that wrote it (named in the adopting run's ACT receipt)."""
    st = st or store(); rows = st.rows("Sessions"); out = []
    for dept, trig in REG.CREATIVE_RUNS:
        r = _latest(rows, dept, trig, ep); how = "own run"
        if r is not None:
            src = _receipt(r, "ACT").get("adopted")
            if src:
                d = next((x for x in rows if x.get("id") == src), None); how = f"adopted draft {src}"; r = d
        out.append((dept, trig, r, how))
    return out

def episode_issues(ep, which, st=None):
    """{'na', 'problems', 'stats'} for check palace_injected (which='injected') or palace_cited (which='cited')."""
    from whatifs.org import runner as ORG
    st = st or store(); ep = str(ep or ""); res = {"na": "", "problems": [], "stats": {"runs": 0, "verified": 0, "unverified": 0, "ghost": 0}}
    if not ORG.on(): res["na"] = "organisation switched off"; return res
    if not prompt_on(): res["na"] = "ORG_PROMPT_INJECT is FALSE: the creative departments hand their playbook over with the brief only (switched off by setting)"; return res
    runs = creative_runs(ep, st)
    if not ep or all(r is None for _d, _t, r, _h in runs): res["na"] = "no creative department run is recorded for this episode (checked outside the production pipeline)"; return res
    if not ORG.born_under_org(ep): res["na"] = "this episode was started before the organisation was installed"; return res
    p = res["problems"]; s = res["stats"]; stored = {r.get("playbook_id") for r in st.rows("Palace_Playbooks")}
    for dept, trig, r, how in runs:
        tag = f"{dept} '{trig}'" + (f" ({how})" if how != "own run" else "")
        if r is None: p.append(f"{tag} never ran under the department contract" + (" (the adopted draft's run is missing)" if how != "own run" else "")); continue
        act = _receipt(r, "ACT"); load = _receipt(r, "LOAD"); key = REG.prompt_spec(dept, r.get("trigger")).get("key", "")
        if act.get("legacy_draft") and r.get("inject") != "prompt":                 # the owner approved this script before the Palace reached the writers
            s["legacy"] = f"{tag}: owner-approved draft {act['legacy_draft']} written before B6a (not judged)"; continue
        s["runs"] += 1
        if which == "injected":
            if r.get("inject") != "prompt": p.append(f"{tag} ran in '{r.get('inject') or 'brief'}' mode: its playbook never entered a model prompt"); continue
            tasks = act.get("injected_tasks") or []
            if key and not any(str(t).startswith(key) for t in tasks): p.append(f"{tag}: the playbook did not reach its key call '{key}' (it reached: {', '.join(tasks) or 'none'})"); continue
            if load.get("playbook_id") not in stored: p.append(f"{tag}: playbook {load.get('playbook_id') or '-'} is not stored, so what it was given cannot be proven")
        else:
            v, u, g = act.get("applied") or [], act.get("unverified") or [], act.get("ghost") or []
            s["verified"] += len(v); s["unverified"] += len(u); s["ghost"] += len(g)
            if int(act.get("citable") or 0) and not v:
                p.append(f"{tag}: no verified citation - {act.get('cited', 0)} cited, {len(u)} quote(s) not found in the output, {len(g)} id(s) never offered")
    return res
