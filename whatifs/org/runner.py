"""Department runner: the six-step contract of every department run - LOAD, ACT, EMIT, LEARN, EXECUTE, REPORT - each proven by a receipt the runner itself builds and chains. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, hashlib, json, re, statistics, threading, time
from whatifs import core, models as M
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub, set_setting
from whatifs.org import DEPARTMENTS, STAGES, palace as PAL, memos as MEM, registry as REG, schemas as SC, cite as CITE, canon as CANON
from whatifs.org.schemas import MemoError

STEPS = ("LOAD", "ACT", "EMIT", "LEARN", "EXECUTE", "REPORT")
STAB, TTAB, AUDIT = "Sessions", "Takeaways", "Org_Audit"
NOISY = ("seconds",)               # runner-observed measures that are never treated as a finding by themselves (timing noise)
HISTORY = 8                        # how many earlier runs of the same department step a measure is compared with
EXECUTOR = None                    # None = the Execution Engine (whatifs/org/execute.py); a callable fn(ticket, brief) replaces it

class ContractBreach(RuntimeError):
    """A step of the department contract was skipped or failed; .step names it."""
    def __init__(self, step, why):
        self.step, self.why = step, str(why); super().__init__(f"department contract broken at {step}: {why}")

class CapReached(RuntimeError):
    """The department's monthly thinking cap is used up (only P0 work continues)."""

class Out:
    """What an organisation-native ACT returns: its output plus the memos it sends, the Palace items it applied, what it did with every inbound
    memo ({memo id: ("resolved", kind, ref) | ("in_progress", note) | ("rejected", reason) | ("deferred", reason)}), and its own takeaways or measures."""
    def __init__(self, output=None, memos=(), applied_items=(), memo_actions=None, takeaways=(), measures=None):
        self.output, self.memos, self.applied_items = output, list(memos or []), [str(i) for i in (applied_items or [])]
        self.memo_actions, self.takeaways, self.measures = dict(memo_actions or {}), list(takeaways or []), dict(measures or {})

class Brief:
    """What LOAD hands to ACT: the department's playbook from the Palace and its inbound memos (most pressing first)."""
    def __init__(self, dept, trigger, episode, stage, topic, playbook, memos, session_id, context=None):
        self.dept, self.trigger, self.episode, self.stage, self.topic = dept, trigger, episode, stage, topic
        self.playbook, self.memos, self.session_id, self.context, self.taken = playbook or {}, list(memos or []), session_id, context, False
    def take(self):
        """The department takes its playbook: {'playbook_id', 'text', 'items'}. A run whose department never takes it is a broken run."""
        self.taken = True
        return {"playbook_id": self.playbook.get("playbook_id", ""), "text": self.playbook.get("text", ""), "items": list(self.playbook.get("items") or [])}

class Result:
    def __init__(self, status, output=None, session_id="", receipts=(), chain="", breaches=(), memos=(), takeaways=()):
        self.status, self.output, self.session_id, self.receipts, self.chain = status, output, session_id, list(receipts), chain
        self.breaches, self.memos, self.takeaways = list(breaches), list(memos), list(takeaways)
    @property
    def ok(self): return self.status == "ok"

def on():
    """Is the organisation switched on? (It reads the Palace, so it needs the Palace on too.)"""
    return S("ORG_ON", bool) and S("PALACE_ON", bool)

def _engine():
    """Who executes a ticket: the Execution Engine, unless it is switched off (EXEC_ON) - then a ticket is escalated at once, never left as text."""
    if EXECUTOR is not None: return EXECUTOR
    if not S("EXEC_ON", bool): return None
    from whatifs.org import execute as EXE
    return EXE.apply

# ------------------------------------------------------------------ receipts (built by the runner from what code observed, chained in order)
def _link(prev, rec):
    body = json.dumps({k: v for k, v in rec.items() if k != "chain"}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1((prev + "|" + body).encode("utf-8")).hexdigest()[:16]

class _Run:
    def __init__(self, sid, dept, mode, tasks=(), spec=None):
        self.sid, self.dept, self.mode, self.spec = sid, dept, mode, dict(spec or {})
        self.tasks = tuple(self.spec.get("tasks") or tasks or ())
        self.pb_text, self.calls, self.injected, self.cost, self.receipts, self.chain = "", set(), 0, 0.0, [], ""
        self.must, self.injected_tasks, self.cites, self.proposals = [], set(), [], []          # v12 B6a: continuity debt, where the playbook went, what came back
    def receipt(self, step, data):
        want = STEPS[len(self.receipts)] if len(self.receipts) < len(STEPS) else None
        if step != want: raise ContractBreach(step, f"out of order: the next step must be {want or 'nothing (the run is closed)'}")
        rec = dict(data, step=step); self.chain = _link(self.chain, rec); rec["chain"] = self.chain
        self.receipts.append(rec); return rec

def verify(session):
    """Problems of one stored Sessions row ([] = a complete, untampered run): six receipts, in order, each chained to the one before, the last
    link equal to the row's chain, and the facts each step must show."""
    p = []; tag = f"{session.get('dept')} {session.get('trigger')} ({session.get('id')})"
    try: steps = json.loads(session.get("steps") or "[]")
    except ValueError: return [f"{tag}: the receipts cannot be read"]
    names = [s.get("step") for s in steps if isinstance(s, dict)]
    if names != list(STEPS):
        miss = [s for s in STEPS if s not in names]
        return [f"{tag}: " + (f"step {miss[0]} is missing" if miss else "the steps are out of order")]
    prev = ""
    for s in steps:
        prev = _link(prev, s)
        if s.get("chain") != prev: return [f"{tag}: the receipt of {s['step']} does not match the chain (edited or written out of order)"]
    if str(session.get("chain") or "") != prev: p.append(f"{tag}: the run's chain does not match its receipts")
    by = {s["step"]: s for s in steps}
    if not by["LOAD"].get("playbook_id"): p.append(f"{tag}: no playbook was loaded")
    if by["ACT"].get("ok") and not by["ACT"].get("injected"): p.append(f"{tag}: no proof that the playbook reached the work")
    if not by["LEARN"].get("takeaways"): p.append(f"{tag}: no takeaway was written")
    return p

# ------------------------------------------------------------------ the two taps (model calls and money of the run in flight)
_ACTIVE: list = []
_LOCK = threading.Lock()

def _ask_tap(task, system, prompt):
    """Every text call passes here (models.ask). It counts the calls of the run in flight and, for a department in 'prompt' mode, puts the
    playbook at the end of the system prompt (the uncached role layer) - the one doorway by which Palace knowledge enters a model."""
    with _LOCK: r = _ACTIVE[-1] if _ACTIVE else None
    if r is None: return system
    r.calls.add(hash((task, len(str(prompt)), str(prompt)[:160])))
    if r.mode == "prompt" and r.pb_text and (not r.tasks or any(str(task).startswith(t) for t in r.tasks)):
        text = CITE.block(r.pb_text, task, r.spec, r.must)                 # v12 B6a: the playbook + the citation rule (+ the continuity debt, + the proposal invitation)
        if text not in str(system or ""):
            # At the END of the system prompt, in the ROLE layer (never cached, never mid-brief): the cached GLOBAL and EPISODE layers stay byte-identical,
            # so every call that shares a brief still reads the same cache. Measured in B6a: the same block inside the cached layer re-wrote the cache
            # per task and per department (hit ratio 0.75 -> 0.53, +45% AI cost on a fake episode).
            from whatifs.prompts import Packed
            pk = Packed.of(system); gap = "" if (not pk.role or pk.role.endswith("\n")) else "\n"
            system = Packed(pk.glob, pk.episode, pk.role + gap + "\n" + text + "\n")
        with _LOCK: r.injected += 1; r.injected_tasks.add(str(task))
    return system

def _reply_tap(task, res):
    """v12 B6a: every reply passes here (models.ask). For a call that carried the playbook it takes the model's `applied_items` and `proposal` out of
    the reply (the caller never sees them) and keeps them for the run, which verifies each citation against its final output."""
    with _LOCK: r = _ACTIVE[-1] if _ACTIVE else None
    if r is None or r.mode != "prompt" or not isinstance(res, dict): return res
    if r.tasks and not any(str(task).startswith(t) for t in r.tasks): return res
    c = res.pop("applied_items", None); pr = res.pop("proposal", None)
    with _LOCK:
        if isinstance(c, list): r.cites += [dict(x, task=str(task)) for x in c[:CITE.MAX_CITES] if isinstance(x, dict)]
        if isinstance(pr, dict) and any(str(task).startswith(t) for t in r.spec.get("propose", ())): r.proposals.append(pr)
    return res

def _cost_tap(inr, provider, item):
    with _LOCK:
        if _ACTIVE: _ACTIVE[-1].cost += float(inr or 0)

if _ask_tap not in M.ASK_TAPS: M.ASK_TAPS.append(_ask_tap)
if _reply_tap not in M.REPLY_TAPS: M.REPLY_TAPS.append(_reply_tap)
if _cost_tap not in core.COST_TAPS: core.COST_TAPS.append(_cost_tap)

# ------------------------------------------------------------------ takeaways built from what the run measured
def _history(st, dept, trigger, n=HISTORY):
    out = []
    for r in [x for x in st.rows(TTAB) if x.get("dept") == dept and x.get("trigger") == trigger][-n:]:
        try: m = json.loads(r.get("measures") or "{}")
        except (TypeError, ValueError): m = {}
        if isinstance(m, dict): out.append(m)
    return out

def build_takeaway(dept, trigger, episode, measures, hist, err=None, lessons=(), seconds=None, cost=None):
    """The takeaway of a wrapped department, made by code from what the run measured, compared with its own earlier runs. A deviation, a named
    lesson or a failure makes it a NEW finding ('_signatures'); otherwise it confirms the baseline. None = the department reported nothing
    about its own output, which the LEARN step refuses."""
    num = SC._num; isnum = SC._KIND["number"]
    meas = {str(k)[:40]: v for k, v in (measures or {}).items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)}
    nums = {k: float(v) for k, v in meas.items() if isnum(v)}; lessons = [(str(k)[:60], str(t)[:300]) for k, t in (lessons or [])]
    if not nums and not lessons and err is None: return None
    if seconds is not None: meas["seconds"] = round(float(seconds), 1)
    if cost: meas["cost_inr"] = round(float(cost), 2)
    pct = min(200.0, max(5.0, S("ORG_DEVIATION_PCT", float) or 25.0)); devs, steady = [], []
    for k, v in nums.items():
        prev = [float(h[k]) for h in hist if isnum(h.get(k))]
        if k in NOISY or len(prev) < 3: continue
        med = statistics.median(prev); ch = (0.0 if v == 0 else 100.0) if med == 0 else (v - med) / abs(med) * 100
        (devs if abs(ch) >= pct else steady).append((k, v, med, ch, len(prev)))
    where = f"{dept} {trigger} run" + (f" for {episode}" if episode else "")
    shown = ", ".join(f"{k} {num(v) if isnum(v) else v}" for k, v in list(meas.items())[:8])
    did = f"{where}: {shown}" if shown else f"{where}: stopped before it produced any output"
    worked = [f"{k} {num(v)} is in line with the last {n} runs (median {num(med)})" for k, v, med, ch, n in steady]
    failed = [f"{k} moved {ch:+.0f}% against the median of the last {n} runs ({num(v)} vs {num(med)})" for k, v, med, ch, n in devs] + [t for _k, t in lessons]
    if err is not None: failed.append(f"the run stopped with {type(err).__name__}: {scrub(err)[:160]}")
    if not worked and not failed:
        worked.append("baseline recorded: " + ", ".join(f"{k} {num(v)}" for k, v in list(nums.items())[:4]) + " (too few earlier runs to compare with)")
    if err is not None: nxt = f"Before the next {trigger} run, remove the cause of {type(err).__name__} in {dept}: this run did not finish its work" + (f" for {episode}." if episode else ".")
    elif lessons: nxt = f"Before the next {trigger} run, {dept} must clear: " + "; ".join(k for k, _t in lessons[:4]) + "."
    elif devs:
        k, v, med, ch, n = devs[0]; nxt = f"Find what changed in the inputs of {dept} before the next {trigger} run: {k} was {num(v)} against a median of {num(med)} ({ch:+.0f}%)."
    elif steady:
        k, v, med, ch, n = steady[0]; nxt = f"Keep the current {dept} settings for the {trigger} step: {k} {num(v)} stayed within {pct:.0f}% of its median {num(med)} over {n} runs."
    else:
        k, v = next(iter(nums.items())); nxt = f"Compare the next {trigger} run of {dept} with this baseline: {k} {num(v)}."
    sigs = ([f"fail:{type(err).__name__}"] if err is not None else []) + [k for k, _t in lessons[:3]] + [f"dev:{k}:{'up' if ch > 0 else 'down'}" for k, v, med, ch, n in devs[:2]]
    return {"did": did[:500], "worked": worked[:10], "failed": failed[:10], "next_time": nxt[:400], "measures": meas, "kind": "takeaway", "_signatures": sigs}

def _propose(st, dept, stage, trigger, episode, sid, tk, sig, now):
    """A new finding goes to the Palace as PROPOSED (never served until the Council accepts it). The id is the finding's class (department,
    step, signature), so the same class seen again updates one item instead of piling up copies."""
    word = sig.split(":")[1] if ":" in sig else sig
    line = next((f for f in tk["failed"] if word in f), (tk["failed"] or tk["worked"] or [tk["did"]])[0])
    summary = re.sub(r"\s+", " ", f"{line}. {tk['next_time']}")[:PAL.SUMMARY_MAX]
    item = {"key": f"run|{dept}|{trigger}|{sig}", "kind": "takeaway", "title": f"{dept} {trigger}: {sig}"[:120].ljust(8, "."), "summary": summary.ljust(20, "."),
            "departments": [dept], "stages": [stage], "topic_tags": [trigger, sig.split(":")[0]], "derived_from": [sid],
            "evidence": [{"source": f"department run {sid}" + (f", episode {episode}" if episode else ""), "date": iso(now)[:10], "type": "own data", "finding": line[:500]}]}
    try: return PAL.add(item, dept, st=st, now=now)["id"]
    except Exception as e:
        log(f"takeaway of {dept} {trigger} not proposed to the Palace: {scrub(e)[:160]}", "WARN", episode or None); return ""

# ------------------------------------------------------------------ the run
def _sid(dept, trigger, episode, key, attempt):
    return "S-" + hashlib.sha1(f"{dept}|{trigger}|{episode}|{key}|{attempt}".encode("utf-8")).hexdigest()[:12].upper()

def _crash_memo(dept, trigger, episode, err, sid, now):
    cls = type(err).__name__; msg = scrub(err)[:300] or cls; tail = f" for {episode}" if episode else ""
    return {"type": "problem_memo", "from_dept": dept, "to_depts": [dept], "subject": f"{dept} {trigger} stopped: {cls}"[:140],
            "body": {"what_failed": f"the {trigger} run stopped with {cls}: {msg}"[:400], "where": f"{dept} {trigger}{tail}", "attempt": 1, "error_class": cls},
            "done_when": f"a {dept} {trigger} run{tail} finishes all six steps", "links": {"trigger": trigger},
            "evidence": [{"source": f"Sessions:{sid}", "date": iso(now)[:10], "type": "own data", "finding": msg}], "dedupe_key": f"crash|{dept}|{trigger}|{episode}|{cls}"}

def _apply_action(m, action, dept, st):
    kind = str(action[0]) if action else ""
    if kind == "resolved": MEM.resolve(m["id"], dept, action[1], action[2], st=st)
    elif kind == "in_progress": MEM.start(m["id"], dept, action[1] if len(action) > 1 else "", st=st)
    elif kind == "rejected": MEM.reject(m["id"], dept, action[1] if len(action) > 1 else "", st=st)
    elif kind == "deferred":
        if len(str(action[1] if len(action) > 1 else "").strip()) < SC.REASON_MIN: raise MemoError(f"{m['id']}: deferring needs a real reason ({SC.REASON_MIN}+ characters)")
    else: raise MemoError(f"{m['id']}: unknown disposition '{kind}'")

def run(dept, trigger, act, *, episode="", topic="", stage=None, context=None, measure=None, lesson=None, emit=None, settle=None, key="", budget="production",
        urgency="P1", strict=True, st=None, now=None, adopt=None, legacy=None):
    """One department run under the contract. `act(brief)` does the work and returns its output (or an Out). Steps always run in this order and
    every one leaves a receipt: LOAD (inbound memos + the Palace playbook) -> ACT (playbook proven to have reached the work) -> EMIT (validated
    memos out, every inbound memo dispositioned, a problem memo for a failure) -> LEARN (a Session row and at least one valid takeaway) ->
    EXECUTE (the department's tickets, through the Execution Engine) -> REPORT (cost, latency, SLA state -> Org_Audit).
    LOAD is strict for everyone: it raises before any work. After ACT nothing is thrown away: the remaining steps always run and are recorded;
    then the original error of ACT is re-raised, and (strict) a broken step raises ContractBreach. With strict=False (work) a broken step is
    recorded as a BREACH that the episode gates fail on, and the output is still returned - a paid or irreversible result is never lost."""
    if dept not in DEPARTMENTS: raise ContractBreach("LOAD", f"unknown department '{dept}'")
    episode = str(episode or ""); stage = stage or DEPARTMENTS[dept][1]; key = str(key or "")
    if stage not in STAGES: raise ContractBreach("LOAD", f"unknown stage '{stage}'")
    if not on(): return Result("off", act(Brief(dept, trigger, episode, stage, topic, {}, [], "", context)))
    st = st or store(); t0 = now or now_utc(); sid = ""; R = None
    if not str(S("ORG_SINCE") or "").strip(): install(st, t0)          # the first run on a Sheet marks when the organisation started there
    # ---- 1 LOAD
    try:
        prior = [r for r in st.rows(STAB) if r.get("dept") == dept and r.get("trigger") == trigger and str(r.get("episode_id") or "") == episode and str(r.get("key") or "") == key]
        done = next((r for r in prior if key and r.get("status") == "ok"), None)
        if done: return Result("duplicate", None, session_id=done["id"])                 # the same keyed run already finished: never repeat a step
        if budget == "org" and urgency != "P0":
            cap = REG.caps().get(dept)
            if cap is not None and REG.spent(dept, st, t0) >= cap:
                _cap_message(dept, cap, t0); raise CapReached(f"{dept} has used its monthly thinking cap of Rs {cap:.0f}; P1 / P2 work waits for next month")
        mode = REG.inject(dept, trigger) if not legacy else REG.DEPTS[dept]["inject"]       # legacy = an owner-approved draft written before B6a: judged as written then
        spec = REG.prompt_spec(dept, trigger) if (mode == "prompt" and not legacy and REG.inject(dept, trigger) != REG.DEPTS[dept]["inject"]) else None     # a B6a creative run: only its named calls
        sid = _sid(dept, trigger, episode, key, len(prior) + 1); R = _Run(sid, dept, mode, REG.DEPTS[dept].get("inject_tasks", ()), spec)
        st.append(STAB, [{"id": sid, "key": key, "dept": dept, "trigger": trigger, "episode_id": episode, "attempt": len(prior) + 1, "status": "running", "started": iso(t0),
                          "budget": budget, "inject": R.mode}])
        inbox = MEM.inbox(dept, st, t0); overdue = sum(1 for m in inbox if (parse_iso(m["sla_due"]) or t0) < t0)
        for m in inbox: MEM.ack(m["id"], dept, st, t0)                                    # loaded = acknowledged (this stops the acknowledge clock only)
        tickets = [m for m in inbox if m["type"] == "ticket"]; inbound = [m for m in inbox if m["type"] != "ticket"]
        if R.mode == "prompt": CANON.ensure_cast(st, t0)                              # v12 B6a: the cast canon exists before a creative playbook is built
        rs = PAL.rows(st)
        if not rs: PAL.ensure_seed(st=st, now=t0); rs = PAL.rows(st)
        pb = PAL.playbook(dept, stage, topic, rs=rs, st=st, now=t0)
        if not pb["playbook_id"]: raise ContractBreach("LOAD", f"the Palace has no servable knowledge for {dept} at stage {stage}")
        R.pb_text = pb["text"]; brief = Brief(dept, trigger, episode, stage, topic, pb, inbound, sid, context)
        limits = {r["id"] for r in rs if r["id"] in set(pb["items"]) and PAL.is_limit(r)}
        if R.mode == "prompt": R.must = CANON.must_cite(dept, pb["items"], rs, t0)                # v12 B6a: the continuity debt of this run
        R.receipt("LOAD", dict({"playbook_id": pb["playbook_id"], "items": len(pb["items"]), "tokens": pb["tokens"], "palace_hash": pb["palace_hash"],
                                "inbound": [m["id"] for m in inbound], "tickets": [m["id"] for m in tickets], "overdue": overdue},
                               **({"must": R.must, "citable": len(pb["items"]) - len(limits)} if R.mode == "prompt" else {})))
    except CapReached: raise
    except Exception as e:
        why = e.why if isinstance(e, ContractBreach) else f"{type(e).__name__}: {scrub(e)[:200]}"
        if sid:
            try: st.update(STAB, "id", sid, {"status": "failed", "ended": iso(), "error": f"LOAD: {why}"[:300]})
            except Exception: pass
        log(f"{dept} {trigger}: LOAD failed, nothing was started: {why}", "ERROR", episode or None)
        raise ContractBreach("LOAD", why) from e
    # ---- 2 ACT
    err = None; raw = None; breaches = []; tw = time.time()
    with _LOCK: _ACTIVE.append(R)
    try: raw = act(brief)
    except Exception as e: err = e
    finally:
        with _LOCK:
            if R in _ACTIVE: _ACTIVE.remove(R)
    secs = round(time.time() - tw, 2); native = isinstance(raw, Out); out = raw if native else Out(raw); proof = ""; applied = []; vr = None; adopted = ""
    if err is None:
        if R.mode == "prompt" and adopt:                                       # v12 B6a: a pre-production draft is adopted only with its own run's proof
            src, why = _adoptable(st, dept, adopt)
            if src is None: breaches.append(("ACT", f"adopted draft {adopt} has no proof that the playbook reached it: {why}"))
            else:
                sa = CITE._receipt(src, "ACT"); adopted = str(adopt); proof = f"adopted draft run {adopt}: {sa.get('injected')}"
                R.injected_tasks |= set(sa.get("injected_tasks") or []); R.cites = [dict(c) for c in (sa.get("citations") or []) if isinstance(c, dict)]
                vr = CITE.verify(R.cites, [c.get("id") for c in R.cites], set(), out.output)        # re-verified against the text production really adopted
        elif R.mode == "prompt":
            proof = f"in {R.injected} model prompt(s)" if R.injected else ""
            if not R.injected: breaches.append(("ACT", "no playbook injection: no model call of this run carried the playbook"))
            vr = CITE.verify(R.cites, pb["items"], limits, out.output)
        else:
            proof = "handed over with the brief" if brief.taken else ""
            if not brief.taken: breaches.append(("ACT", "no playbook injection: the department never took its playbook"))
        ghost = [i for i in out.applied_items if i not in pb["items"]]
        if ghost: breaches.append(("ACT", "cites Palace item(s) that were not in its playbook: " + ", ".join(ghost[:3])))
        else:
            applied = list(dict.fromkeys(out.applied_items + (vr["verified"] if vr else [])))   # a model's citation counts only when its quote was found
            try:
                if applied and not adopted: PAL.mark_applied(applied, st=st)
            except Exception as e: log(f"applied items not counted: {scrub(e)[:120]}", "WARN", episode or None)
        if vr is not None:
            out.measures.update({"citations_verified": len(vr["verified"]), "citations_unverified": len(vr["unverified"]), "citations_ghost": len(vr["ghost"])})
    act_rec = {"ok": err is None, "seconds": secs, "cost_inr": round(R.cost, 2), "model_calls": len(R.calls), "injected": proof, "applied": applied,
               "error": type(err).__name__ if err is not None else ""}
    if legacy: act_rec["legacy_draft"] = str(legacy)
    if R.mode == "prompt":
        keep = [{"id": i, "where": (vr or {}).get("quotes", {}).get(i, "")} for i in ((vr or {}).get("verified", []) + (vr or {}).get("unverified", []))][:CITE.MAX_CITES]
        act_rec.update(injected_tasks=sorted(R.injected_tasks), cited=len(R.cites), citable=len(pb["items"]) - len(limits), unverified=(vr or {}).get("unverified", []),
                       ghost=(vr or {}).get("ghost", []), citations=keep, adopted=adopted)
    R.receipt("ACT", act_rec)
    # ---- 3 EMIT
    written, settled, handled, pstats = [], [], 0, None
    try:
        outbound = [dict(m) for m in out.memos]
        if emit is not None and err is None: outbound += [dict(m) for m in (emit(out.output, brief) or [])]
        if R.proposals and err is None:                                        # v12 B6a: ideas the creative calls proposed -> creative memos to the Council (same-idea guard)
            cm, pstats = CITE.proposals_to_memos(dept, R.proposals, st, t0); outbound += cm
        told = {}
        for m in outbound:
            m.setdefault("from_dept", dept); m.setdefault("episode_id", episode); m["session_id"] = sid; t_ = m.pop("_owner_told", None)
            if t_: told[id(m)] = t_
        bad = [f"{m.get('type')}: " + "; ".join(SC.check_memo(m, t0)[1][:2]) for m in outbound if SC.check_memo(m, t0)[1]]
        if bad: breaches.append(("EMIT", "invalid memo (none of this run's memos was sent): " + " | ".join(bad[:3]))); outbound = []
        if err is not None: outbound.append(dict(_crash_memo(dept, trigger, episode, err, sid, t0), session_id=sid, episode_id=episode))
        for m in outbound:
            w = MEM.write(m, st, t0); written.append(w["id"])
            if id(m) in told: MEM.note_owner_told(w["id"], told[id(m)], st, t0)
        if err is None:
            for mid, kind, ref in (settle(out.output, brief) or [] if settle is not None else []):
                MEM.resolve(mid, dept, kind, ref, st=st, now=t0); settled.append(mid)
            for m in MEM.find(st, type="problem_memo", from_dept=dept, episode_id=episode):          # this run finished: its own earlier crashes are repaired
                if m["body"].get("error_class") not in (None, "", "ContractBreach") and (m["links"] or {}).get("trigger") == trigger and m["id"] not in written:
                    MEM.resolve(m["id"], dept, "repair_verified", sid, "the same step finished in a later run", st, t0); settled.append(m["id"])
            if native:                                                                             # coverage: a memo that was loaded must not be ignored
                for m in inbound:
                    if m["from_dept"] == dept and m["body"].get("error_class"): continue          # the runner's own memo about this department's runs: closed by a clean run, not by the department's word
                    a = out.memo_actions.get(m["id"])
                    if not a: breaches.append(("EMIT", f"inbound memo {m['id']} ({m['type']}) was loaded and ignored")); continue
                    _apply_action(m, a, dept, st); handled += 1
    except MemoError as e: breaches.append(("EMIT", "; ".join(e.problems[:3])))
    except Exception as e: breaches.append(("EMIT", f"{type(e).__name__}: {scrub(e)[:160]}"))
    R.receipt("EMIT", dict({"written": written, "settled": settled, "handled": handled}, **({"proposals": pstats} if pstats else {})))
    # ---- 4 LEARN
    tids, novel, proposed = [], 0, []
    try:
        tks = [dict(t) for t in out.takeaways]; today = iso(t0)[:10]
        if not tks:
            meas = dict(out.measures)
            if measure is not None and err is None: meas.update(measure(out.output) or {})
            les = list(lesson(out.output) or []) if (lesson is not None and err is None) else []
            tk = build_takeaway(dept, trigger, episode, meas, _history(st, dept, trigger), err, les, secs, R.cost)
            if tk is not None:
                fnd = (tk["failed"] or tk["worked"])[0]
                tk["evidence"] = [{"source": f"Sessions:{sid}", "date": today, "type": "own data", "finding": fnd[:500]}]; tks = [tk]
        good, why = [], []
        for tk in tks:
            sigs = tk.pop("_signatures", None) or ([str(tk.pop("signature"))] if tk.get("signature") else [])
            c, p = SC.check_takeaway(dict(tk, dept=dept), t0)
            if p: why += p
            else: good.append((c, sigs))
        if not good: raise ContractBreach("LEARN", "no valid takeaway: " + ("; ".join(why[:3]) if why else "the department reported nothing about its own output"))
        rows = []
        for i, (c, sigs) in enumerate(good):
            tid = "T-" + hashlib.sha1(f"{sid}|{i}".encode("utf-8")).hexdigest()[:12].upper(); pid = ""
            for sg in sigs[:3]:
                pid = _propose(st, dept, stage, trigger, episode, sid, c, sg, t0) or pid
                if pid and pid not in proposed: proposed.append(pid)
            novel += 1 if sigs else 0
            rows.append({"id": tid, "ts": iso(t0), "session_id": sid, "dept": dept, "trigger": trigger, "episode_id": episode, "kind": c["kind"], "did": c["did"], "worked": c["worked"],
                         "failed": c["failed"], "next_time": c["next_time"], "measures": c["measures"], "evidence": c["evidence"], "novel": "TRUE" if sigs else "",
                         "signature": ",".join(sigs)[:200], "palace_item": pid}); tids.append(tid)
        st.append(TTAB, rows)
    except ContractBreach as e: breaches.append((e.step, e.why))
    except Exception as e: breaches.append(("LEARN", f"{type(e).__name__}: {scrub(e)[:160]}"))
    R.receipt("LEARN", {"takeaways": tids, "novel": novel, "palace": proposed})
    # ---- 5 EXECUTE
    executed, pushed = [], []
    try:
        ex = _engine() if tickets else None
        for t in tickets:
            if ex is None:
                MEM.escalate(t["id"], f"the Execution Engine is switched off (EXEC_ON), so lever class {t['body'].get('lever_class')} cannot be executed: a ticket is never left as text", dept, st, t0); pushed.append(t["id"])
            else:
                ex(t, brief); executed.append(t["id"])
    except Exception as e: breaches.append(("EXECUTE", f"{type(e).__name__}: {scrub(e)[:160]}"))
    R.receipt("EXECUTE", {"tickets": len(tickets), "executed": executed, "escalated": pushed})
    # ---- 6 REPORT
    status = "failed" if err is not None else ("breach" if breaches else "ok"); errtxt = (f"{type(err).__name__}: {scrub(err)[:200]}" if err is not None else "; ".join(f"{s}: {w}" for s, w in breaches))[:300]
    R.receipt("REPORT", {"status": status, "seconds": secs, "cost_inr": round(R.cost, 2), "sla_overdue": overdue, "breaches": [f"{s}: {w}"[:200] for s, w in breaches]})
    try:
        st.update(STAB, "id", sid, {"status": status, "ended": iso(), "playbook_id": pb["playbook_id"], "palace_hash": pb["palace_hash"], "inbound": [m["id"] for m in inbound],
                                    "emitted": written, "takeaways": tids, "applied_items": applied, "steps": R.receipts, "chain": R.chain, "cost_inr": round(R.cost, 2), "error": errtxt})
        st.append(AUDIT, [{"ts": iso(), "kind": "run", "run_id": sid, "dept": dept, "trigger": trigger, "episode_id": episode, "outcome": status, "steps": ",".join(STEPS), "chain": R.chain,
                           "latency_s": secs, "cost_inr": round(R.cost, 2), "budget": budget, "model_calls": len(R.calls), "inbound": len(inbound), "emitted": len(written),
                           "takeaways": len(tids), "sla_overdue": overdue, "playbook_id": pb["playbook_id"], "error": errtxt, "note": ""}])
    except Exception as e:
        breaches.append(("REPORT", f"{type(e).__name__}: {scrub(e)[:160]}")); status = "breach" if err is None else status
        log(f"{dept} {trigger}: the run could not be recorded: {scrub(e)[:160]}", "ERROR", episode or None)
    if breaches:
        log(f"{dept} {trigger} broke the department contract: " + " | ".join(f"{s}: {w}" for s, w in breaches)[:400], "ERROR", episode or None)
        try:
            # one memo per CLASS of breach (department, step, broken contract step), with no episode on it: it is a defect of the organisation's own
            # code, so an episode going live never closes it - only a later clean run of the same step does; a third recurrence escalates at once
            MEM.write({"type": "problem_memo", "from_dept": dept, "to_depts": [dept], "subject": f"{dept} {trigger} broke the department contract at {breaches[0][0]}"[:140],
                       "body": {"what_failed": "; ".join(f"{s}: {w}" for s, w in breaches)[:400], "where": f"{dept} {trigger}" + (f" for {episode}" if episode else ""), "attempt": 1,
                                "error_class": "ContractBreach"}, "done_when": f"a {dept} {trigger} run finishes all six steps with a valid receipt chain", "session_id": sid,
                       "links": {"trigger": trigger, "episode": episode}, "episode_id": "",
                       "evidence": [{"source": f"Sessions:{sid}", "date": iso(t0)[:10], "type": "own data", "finding": breaches[0][1][:300]}],
                       "dedupe_key": f"breach|{dept}|{trigger}|{breaches[0][0]}"}, st, t0)
        except Exception as e: log(f"breach memo not written: {scrub(e)[:120]}", "WARN", episode or None)
    if status == "ok":                                             # a clean run of this step closes the open breach memos of the same step
        try:
            for m in MEM.find(st, type="problem_memo", from_dept=dept, error_class="ContractBreach"):
                if (m["links"] or {}).get("trigger") == trigger: MEM.resolve(m["id"], dept, "repair_verified", sid, "the same step finished a clean run", st)
        except Exception as e: log(f"breach memo not closed: {scrub(e)[:120]}", "WARN", episode or None)
    if err is not None: raise err
    if breaches and strict: raise ContractBreach(*breaches[0])
    return Result(status, out.output, sid, R.receipts, R.chain, breaches, written, tids)

def work(dept, trigger, episode, fn, adopt=None, legacy=None, **kw):
    """Run an existing production step as a department run: the playbook is handed over with the work order, `fn(brief)` does exactly what the
    step always did, and its return value comes back unchanged. See run() for what is recorded and what the episode gates then judge.
    adopt = the Sessions id of the run that already did this work (a pre-production draft): its proof is checked and carried over."""
    def act(brief):
        brief.take()
        return fn(brief)
    return run(dept, trigger, act, episode=episode, strict=False, adopt=adopt, legacy=legacy, **kw).output

def last_session(dept, trigger, episode, st=None):
    """The id of the newest run of this department step for this episode ('' when none)."""
    r = CITE._latest((st or store()).rows(STAB), dept, trigger, str(episode or ""))
    return r.get("id", "") if r else ""

def _adoptable(st, dept, sid):
    """(row, '') when Sessions row `sid` is a complete, ok draft run of this department whose playbook reached its model calls; else (None, why)."""
    r = next((x for x in st.rows(STAB) if x.get("id") == sid), None)
    if r is None: return None, "the draft's run is not recorded"
    if r.get("dept") != dept or r.get("trigger") != "draft": return None, f"{sid} is a {r.get('dept')} '{r.get('trigger')}' run, not a {dept} draft"
    if r.get("status") != "ok": return None, f"the draft run is '{r.get('status')}'"
    if r.get("inject") != "prompt": return None, "the draft was written with the playbook handed over only (brief mode)"
    bad = verify(r)
    if bad: return None, bad[0]
    if not CITE._receipt(r, "ACT").get("injected_tasks"): return None, "no model call of the draft carried the playbook"
    return r, ""

def _cap_message(dept, cap, now):
    try:
        from whatifs import notify as NT
        NT.send("org_cap", f"{DEPARTMENTS[dept][0]} has used its thinking budget for this month (Rs {cap:.0f}). Urgent work continues; the rest waits for next month.",
                tier="week", dedupe_key=f"org_cap|{dept}|{now.strftime('%Y-%m')}")
    except Exception as e: log(f"cap message not sent: {scrub(e)[:100]}", "WARN")

# ------------------------------------------------------------------ what the episode gates judge
def born_under_org(ep):
    """Was this episode started after the organisation was installed on this Sheet? (An older, half-made episode is not judged by its checks.)"""
    since = parse_iso(S("ORG_SINCE")); m = re.match(r"^EP(\d{12})", str(ep or ""))
    if not since or not m: return True
    try: return dt.datetime.strptime(m.group(1), "%Y%m%d%H%M").replace(tzinfo=dt.timezone.utc) >= since.replace(second=0, microsecond=0)
    except ValueError: return True

def episode_issues(ep, gate, st=None, now=None):
    """{'na': why or '', 'problems': [...], 'runs': n}: before a gate, has every department this episode needs finished a complete run (six
    chained receipts, latest attempt ok) with a valid takeaway, and has no run of this episode broken the contract?"""
    st = st or store(); now = now or now_utc(); ep = str(ep or ""); out = {"na": "", "problems": [], "runs": 0}
    rows = [r for r in st.rows(STAB) if str(r.get("episode_id") or "") == ep and ep]
    if not rows: out["na"] = "no department run is recorded for this episode (checked outside the production pipeline)"; return out
    if not born_under_org(ep): out["na"] = "this episode was started before the organisation was installed"; return out
    latest = {}
    for r in rows:
        k = (r.get("dept"), r.get("trigger"))
        if k not in latest or int(float(r.get("attempt") or 0)) >= int(float(latest[k].get("attempt") or 0)): latest[k] = r
    takes = {}
    for t in st.rows(TTAB):
        if str(t.get("episode_id") or "") == ep: takes.setdefault(t.get("session_id"), []).append(t)
    p = out["problems"]; gate_run = REG.GATE_RUNS.get(gate)
    for dept, trig in REG.EPISODE_RUNS[gate]:
        r = latest.get((dept, trig))
        if r is None: p.append(f"{dept} '{trig}' never ran under the department contract for {ep}"); continue
        if r.get("status") != "ok": p.append(f"{dept} '{trig}' is {r.get('status')}: {str(r.get('error') or 'not finished')[:120]}"); continue
        bad = verify(r)
        if bad: p += bad[:1]; continue
        ok_t = [t for t in takes.get(r.get("id"), []) if not _takeaway_problems(t, now)]
        if not ok_t: p.append(f"{dept} '{trig}' ({r.get('id')}) wrote no valid takeaway")
        out["runs"] += 1
    for (dept, trig), r in sorted(latest.items()):
        if (dept, trig) != gate_run and r.get("status") == "breach" and (dept, trig) not in REG.EPISODE_RUNS[gate]:
            p.append(f"{dept} '{trig}' broke the contract: {str(r.get('error') or '')[:120]}")
    p += [f"registry: {x}" for x in REG.entry_issues()[:3]]
    age = MEM.watchdog_age_h(now)
    if age is not None and age > 24: p.append(f"the SLA watchdog has not finished a pass for {age:.0f} h (memo deadlines are not being enforced)")
    return out

def _takeaway_problems(row, now=None):
    def js(k, d):
        try: v = json.loads(row.get(k) or "null")
        except (TypeError, ValueError): v = None
        return v if v is not None else d
    return SC.check_takeaway({"dept": row.get("dept"), "did": row.get("did"), "worked": js("worked", []), "failed": js("failed", []), "next_time": row.get("next_time"),
                              "measures": js("measures", {}), "evidence": js("evidence", []), "kind": row.get("kind") or "takeaway"}, now)[1]

# ------------------------------------------------------------------ upkeep
def audit(st=None, now=None):
    """Runs that started and never reported (a killed job): flagged as abandoned and turned into a problem memo for their department."""
    st = st or store(); now = now or now_utc(); lim = min(48.0, max(1.0, S("ORG_RUN_STALE_H", float) or 6.0)); out = []
    for r in st.rows(STAB):
        t = parse_iso(r.get("started"))
        if r.get("status") != "running" or not t or (now - t).total_seconds() < lim * 3600: continue
        st.update(STAB, "id", r["id"], {"status": "abandoned", "ended": iso(now), "error": f"still running after {lim:.0f} h: the job was killed or timed out"})
        ep = str(r.get("episode_id") or ""); out.append(r["id"])
        try:
            MEM.write({"type": "problem_memo", "from_dept": r["dept"], "to_depts": [r["dept"]], "subject": f"{r['dept']} {r['trigger']} never finished its run"[:140],
                       "body": {"what_failed": f"the {r['trigger']} run started {r.get('started')} and never reported", "where": f"{r['dept']} {r['trigger']}" + (f" for {ep}" if ep else ""),
                                "attempt": 1, "error_class": "Abandoned"}, "done_when": f"a {r['dept']} {r['trigger']} run finishes all six steps", "links": {"trigger": r["trigger"]},
                       "evidence": [{"source": f"Sessions:{r['id']}", "date": iso(now)[:10], "type": "own data"}], "episode_id": ep, "session_id": r["id"],
                       "dedupe_key": f"crash|{r['dept']}|{r['trigger']}|{ep}|Abandoned"}, st, now)
        except Exception as e: log(f"abandoned run {r['id']}: problem memo not written: {scrub(e)[:120]}", "WARN")
    return out

def daily_check(st=None, now=None):
    """Once a day (learning job): is the SLA watchdog alive? If it has not finished a pass for 6 hours the owner is told once, at once."""
    now = now or now_utc(); age = MEM.watchdog_age_h(now)
    if not on() or age is None or age <= 6: return {"watchdog_age_h": age, "told": False}
    try:
        from whatifs import notify as NT
        NT.send("org_watchdog", f"The organisation's deadline watchdog has not run for {age:.0f} hours. Memo deadlines are not being enforced until the tick job works again.",
                tier="now", urgent=True, dedupe_key=f"org_watchdog|{now.strftime('%Y-%m-%d')}")
    except Exception as e: log(f"watchdog alarm not sent: {scrub(e)[:100]}", "WARN")
    return {"watchdog_age_h": age, "told": True}

def install(st=None, now=None):
    """Setup: remember when the organisation started on this Sheet (once)."""
    if not str(S("ORG_SINCE") or "").strip(): set_setting("ORG_SINCE", iso(now)); return True
    return False

def health(st=None, now=None):
    """{'ok', 'problems', 'stats'} for the organisation's own wiring: honest registry, real data, readable tabs."""
    st = st or store(); now = now or now_utc(); p = REG.entry_issues() + REG.data_issues()
    try: ms = MEM.stats(st, now); ss = st.rows(STAB)
    except Exception as e: return {"ok": False, "problems": p + [f"the organisation's tabs cannot be read: {scrub(e)[:100]}"], "stats": {}}
    stats = dict(ms, sessions=len(ss), breaches=sum(1 for r in ss if r.get("status") == "breach"), running=sum(1 for r in ss if r.get("status") == "running"),
                 wired=len(REG.ENTRY), pending=len(REG.PENDING), watchdog_age_h=MEM.watchdog_age_h(now))
    return {"ok": not p, "problems": p, "stats": stats}

if __name__ == "__main__":
    import sys
    _h = health()
    print("ORGANISATION: " + ("GREEN" if _h["ok"] else "RED"), json.dumps(_h["stats"], sort_keys=True, default=str))
    for _p in _h["problems"]: print("  -", _p)
    sys.exit(0 if _h["ok"] else 1)
