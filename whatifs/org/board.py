"""Review Board (D3): every research memo judged blind by strong judges of two model families on a fixed yes/no checklist, with a planted canary in every session; scores and the verdict are computed by code. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, re
from collections import defaultdict
from whatifs.core import S, log, store, iso, now_utc, scrub
from whatifs.org import memos as MEM, schemas as SC, palace as PAL

LOG = "Board_Log"
JUDGES = (("board_gemini", "gemini"), ("board_claude", "claude"))      # one strong judge per family; their chains hold no cheap model
STRONG = ("opus", "sonnet", "fable", "gem_pro")                        # the chain roles allowed to answer for the Board (02 point 3: cheap models never judge)
LETTERS = "ABCDEFGHIJK"
DIMS = ("evidence", "novelty", "impact", "feasibility", "risk")
QUESTIONS = (
    ("E1", "evidence", "Does every finding follow from the quoted text of its sources (nothing is claimed beyond what the quotes say)?"),
    ("E2", "evidence", "Is at least one source a measurement or an official platform statement (not opinion or marketing)?"),
    ("N1", "novelty", "Is the proposal different from everything listed under WHAT WE ALREADY DO?"),
    ("N2", "novelty", "Would a typical channel in this niche NOT already be doing this as standard practice?"),
    ("I1", "impact", "Would a viewer notice the change in our next video (see it, hear it or feel it)?"),
    ("I2", "impact", "Does the proposal address the GAP stated for the memo?"),
    ("I3", "impact", "Is it likely to move a breakout number (click-through, retention, shares, returning viewers)?"),
    ("F1", "feasibility", "Can it be done with the show's existing tools, models and settings (no new subscription or service)?"),
    ("F2", "feasibility", "Can it be done before our next video?"),
    ("R1", "risk", "Could it break YouTube policy (mass-produced or repetitive content, misleading titles or thumbnails, buying views, made-for-kids rules)?"),
    ("R2", "risk", "Could it contradict the show's canon or rules (the Reality on Trial courtroom, its four characters, accurate science)?"),
    ("R3", "risk", "Could it make our videos more generic, repetitive or cheap-looking (AI slop)?"))
RISK_Q = tuple(q for q, d, _ in QUESTIONS if d == "risk")
COST_REF_INR = 500.0                  # a change that costs this much a month (10% of the budget) scores 0 on cost; free = 10
ORDER = {"reject": 0, "test": 1, "accept": 2}

BOARD_SYSTEM = (
    "You are one member of the Review Board of 'Reality on Trial', a YouTube channel of stop-motion courtroom comedies about science what-ifs. You "
    "judge research memos written by the channel's research department. Judge each memo ONLY on what is written in it; be strict - some memos are weak "
    "on purpose, and a memo that sounds exciting but is not supported must get 'no'. Answer EVERY question for EVERY memo with yes or no and one short "
    "reason.\nQUESTIONS:\n" + "\n".join(f"{q}: {t}" for q, _d, t in QUESTIONS) +
    '\nReturn JSON only: {"answers": {"<memo letter>": {"E1": ["yes" or "no", "reason"], ... one entry per question}}}')

# Canaries: memos the code builds to be rejected. Each one fails the evidence questions AND trips a risk question - a judge that does not reject it
# is inflating (sources 5-6 of the B5 research), and the session is void.
CANARIES = (
    {"question": "Can we buy views so the algorithm notices our next video?", "findings": ["Buying 10,000 views before an upload guarantees the algorithm pushes the video to millions."],
     "sources": None, "actions": ["Buy 10,000 views from a view seller before every upload (predicts views up within 1 video)"],
     "impact": "guaranteed viral growth for every video", "cost": 4000},
    {"question": "Should we re-upload our best video every day?", "findings": ["Re-uploading the same video twice a day triples watch time within a week."],
     "sources": "[1] daily-upload-tricks.com | 2026-03-01 | practice | \"We posted every day for a month and enjoyed the process.\"",
     "actions": ["Re-upload the same long video with a new title every day (predicts views up within 1 video)"], "impact": "triple the watch hours at no cost", "cost": 0},
    {"question": "Can we mass-produce near-identical Shorts to grow faster?", "findings": ["Thirty near-identical Shorts a day is the fastest proven way to monetise an AI channel."],
     "sources": "[1] support.google.com | 2026-07-15 | official | \"Content that is mass-produced or repetitive is not eligible for monetization.\"",
     "actions": ["Generate thirty near-identical Shorts a day from one script (predicts subs up within 1 video)"], "impact": "guaranteed monetisation in a month", "cost": 300})

def due(st=None):
    """Is a research memo waiting for the Board (live, addressed to D3, not escalated past it)?"""
    return any(m["type"] == "research_memo" and "D3" in m["to_depts"] and m["level"] == 0 for m in MEM.find(st or store()))

# ------------------------------------------------------------------ scores and the verdict (pure functions: the check re-runs them)
def cost_score(cost_inr):
    try: c = max(0.0, float(cost_inr or 0))
    except (TypeError, ValueError): c = COST_REF_INR
    return round(10 * max(0.0, 1 - c / COST_REF_INR), 1)

def scores_from(shares, ceiling, cost_inr):
    """{question: share of yes} -> the six scores. Evidence can never exceed the ceiling code computed for the memo's sources."""
    sc = {d: round(10 * sum(shares.get(q, 0.0) for q, dd, _ in QUESTIONS if dd == d) / sum(1 for _q, dd, _ in QUESTIONS if dd == d), 1) for d in DIMS}
    sc["evidence"] = round(min(sc["evidence"], float(ceiling)), 1); sc["cost"] = cost_score(cost_inr)
    return sc

def bar(sc, kind, preds, min_ev):
    """The verdict one set of scores earns. Reject: weak evidence, real risk or no impact. Accept: only a FACT (policy, tool, re-validation) with
    strong evidence. Test: a promising idea with a pre-registered prediction. Anything else: reject."""
    from whatifs.org.rnd import FACT_KINDS
    if sc["evidence"] < min_ev or sc["risk"] >= 5 or sc["impact"] < 4: return "reject"
    if kind in FACT_KINDS and sc["evidence"] >= 7 and sc["feasibility"] >= 5 and sc["risk"] < 3: return "accept"
    if sc["impact"] >= 6 and sc["feasibility"] >= 5 and sc["novelty"] >= 5 and int(preds or 0) > 0: return "test"
    return "reject"

def verdict(families, ceiling, cost_inr, kind, preds, author, min_ev):
    """(verdict, scores). Scores = the mean of FAMILY means; the family that did not write the memo must earn at least the same verdict on its own
    answers (family veto)."""
    fams = sorted(families)
    shares = {q: sum(families[f].get(q, 0.0) for f in fams) / len(fams) for q, _d, _t in QUESTIONS}
    sc = scores_from(shares, ceiling, cost_inr); v = bar(sc, kind, preds, min_ev)
    for f in [x for x in fams if x != author] or fams:
        own = bar(scores_from(families[f], ceiling, cost_inr), kind, preds, min_ev)
        if ORDER[own] < ORDER[v]: v = own
    return v, sc

def assessment_issues(m):
    """What check research_cadence finds wrong with a stored assessment: fewer than two families, no canary, or a verdict / score that is not the
    code's own result on the stored checklist (a verdict nobody can forge or type by hand)."""
    b = m.get("body") or {}; ck = b.get("checklist") or {}; fams = ck.get("families") or {}
    if len(fams) < 2: return ["judged by fewer than two model families"]
    if not str(b.get("canary") or "").startswith("rejected by"): return ["no planted canary was rejected in its session"]
    try:
        v, sc = verdict(fams, b.get("evidence_ceiling", 0), b.get("cost_inr", 0), b.get("kind"), b.get("predictions", 0), b.get("author_family", ""), float(ck.get("min_evidence")))
    except Exception as e: return [f"its checklist cannot be re-computed ({type(e).__name__})"]
    out = []
    if v != b.get("verdict"): out.append(f"verdict '{b.get('verdict')}' is not the code's verdict '{v}' on its own checklist")
    if any(abs(float((b.get("scores") or {}).get(k, -1)) - sc[k]) > 0.05 for k in sc): out.append("scores differ from the code's scores on its own checklist")
    return out

# ------------------------------------------------------------------ the session
def _block(label, memo, known):
    b = memo["body"]; ev = memo.get("evidence") or []
    src = "\n".join(f"[{i}] {re.sub(r'^.*[(]', '', e.get('source', '')).rstrip(')') or e.get('url', '')} | {e.get('date', '')} | {e.get('type', '')} | "
                    f"\"{str(e.get('finding') or '').removeprefix('quote: ')[:280]}\"" for i, e in enumerate(ev, 1)) or "none"
    gap = b.get("gap") or {}
    return (f"=== MEMO {label} ===\nKIND: {'fact' if b.get('kind') in ('policy', 'tool', 'revalidate') else 'idea'}\nGAP: {gap.get('source', '')}: {gap.get('ref', '')}\n"
            f"QUESTION: {b.get('question', '')}\nFINDINGS:\n" + "\n".join(f"- {f}" for f in b.get("findings") or []) + f"\nSOURCES: {src if src == 'none' else chr(10) + src}\n"
            "PROPOSED ACTIONS:\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(b.get("proposed_actions") or [], 1)) +
            f"\nEXPECTED IMPACT: {b.get('expected_impact', '')}\nCOST TO DO IT: Rs {float(b.get('cost_inr') or 0):.0f} a month\nWHAT WE ALREADY DO:\n{known}\n")

def canary(seed):
    """The planted memo for one session (chosen by the session id), shaped like a research memo."""
    c = CANARIES[int(hashlib.sha1(str(seed).encode("utf-8")).hexdigest(), 16) % len(CANARIES)]
    ev = [] if not c["sources"] else [{"source": c["sources"].split(" | ")[0][4:], "date": c["sources"].split(" | ")[1], "type": c["sources"].split(" | ")[2],
                                       "finding": "quote: " + c["sources"].split("\"")[1]}]
    return {"id": "CANARY", "evidence": ev, "body": {"question": c["question"], "findings": c["findings"], "proposed_actions": c["actions"], "expected_impact": c["impact"],
                                                     "cost_inr": c["cost"], "kind": "technique", "gap": {"source": "growth", "ref": "views"}, "evidence_ceiling": 10, "predictions": [{}]}}

def _yes(v):
    if isinstance(v, (list, tuple)) and v: v = v[0]
    if isinstance(v, dict): v = v.get("a") or v.get("answer")
    if isinstance(v, bool): return v
    s = str(v or "").strip().lower(); return True if s.startswith("y") else (False if s.startswith("n") else None)

def _why(v):
    if isinstance(v, (list, tuple)) and len(v) > 1: return str(v[1])[:160]
    if isinstance(v, dict): return str(v.get("why") or v.get("reason") or "")[:160]
    return ""

def _parse(out, labels):
    """{label: ({question: True/False}, {question: reason}, missing)}. A question left unanswered counts AGAINST the memo (no on the good questions,
    yes on the risk questions)."""
    a = (out or {}).get("answers") if isinstance(out, dict) else None; a = a if isinstance(a, dict) else {}
    res = {}
    for l in labels:
        got = a.get(l) if isinstance(a.get(l), dict) else {}; ans, why, miss = {}, {}, 0
        for q, _d, _t in QUESTIONS:
            y = _yes(got.get(q))
            if y is None: miss += 1; y = q in RISK_Q
            ans[q] = y; why[q] = _why(got.get(q))
        res[l] = (ans, why, miss)
    return res

def _known(dept, cache):
    if dept not in cache:
        try: cache[dept] = PAL.playbook(dept, record=False)["text"][:900] or "nothing recorded yet"
        except Exception: cache[dept] = "nothing recorded yet"
    return cache[dept]

def _clean(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return "[removed: read like an instruction]" if PAL.INJECT.search(text) else text

def assess(brief):
    """D3 assess: one Board session over the waiting research memos (most pressing first, at most BOARD_MAX_MEMOS) plus the canary. Void when a judge
    was answered by another family or a cheap model, when fewer than two families answered, or when any family failed to reject the canary."""
    from whatifs import models as M
    from whatifs.org.runner import Out
    brief.take(); st = store(); now = now_utc(); sid = brief.session_id or "S-" + iso(now)
    waiting = [m for m in brief.memos if m["type"] == "research_memo"][:max(1, S("BOARD_MAX_MEMOS", int))]
    acts = {m["id"]: ("deferred", "read by the Review Board: it judges research memos only; anything else is for its addressed departments") for m in brief.memos}
    if not waiting: return Out(output={"judged": 0}, memo_actions=acts, measures={"memos_judged": 0, "void": 0})
    can = canary(sid); items = waiting + [can]
    pos = int(hashlib.sha1(sid.encode("utf-8")).hexdigest(), 16) % len(items); items.insert(pos, items.pop())          # the canary sits at a session-chosen place
    labels = LETTERS[:len(items)]; by = dict(zip(labels, items)); cache = {}
    blocks = {l: _block(l, m, _known((m["body"].get("target_depts") or ["D4"])[0], cache) if m is not can else "nothing recorded yet") for l, m in by.items()}
    fam_ans = defaultdict(lambda: defaultdict(list)); used, rows, notes, void = {}, [], [], ""
    orders = max(1, S("BOARD_ORDERS", int))
    for role, fam in JUDGES:
        for o in range(orders):
            seq = list(labels) if o % 2 == 0 else list(reversed(labels))
            try: out = M.ask(role, BOARD_SYSTEM, "\n".join(blocks[l] for l in seq), want_json=True, max_tokens=3500, temperature=0.2, fake_key="board")
            except Exception as e: notes.append(f"{fam} order {o}: no answer ({scrub(e)[:80]})"); continue
            call = M.last_call()
            if call.get("provider") != fam or call.get("role") not in STRONG:
                notes.append(f"{fam} order {o} was answered by {call.get('provider')}:{call.get('role')} - not counted"); continue
            used[fam] = call.get("model") or call.get("role")
            for l, (ans, why, miss) in _parse(out, labels).items():
                fam_ans[fam][l].append((ans, why))
                rows.append({"ts": iso(now), "session_id": sid, "memo_ref": by[l]["id"], "label": l, "canary": "TRUE" if by[l] is can else "", "judge": role, "family": fam,
                             "role": call.get("role"), "model": call.get("model"), "order": o, "answers": json.dumps({q: ("yes" if a else "no") for q, a in ans.items()}), "verdict": ""})
    fams = sorted(fam_ans)
    def shares(f, l): return {q: sum(1 for a, _w in fam_ans[f][l] if a[q]) / len(fam_ans[f][l]) for q, _d, _t in QUESTIONS}
    min_ev = float(S("BOARD_MIN_EVIDENCE", float))
    if len(fams) < 2: void = f"only {len(fams)} model famil{'y' if len(fams) == 1 else 'ies'} answered ({'; '.join(notes)[:200] or 'no judge answered'})"
    else:
        cl = next(l for l, m in by.items() if m is can)
        bad = [f for f in fams if bar(scores_from(shares(f, cl), 10, can["body"]["cost_inr"]), "technique", 1, min_ev) != "reject"]
        if bad: void = f"the planted canary (memo {cl}) was not rejected by {', '.join(bad)}: the jury was inflating, its verdicts are void"
    memos, verdicts = [], {}
    if not void:
        for l, m in by.items():
            if m is can: continue
            b = m["body"]; fs = {f: shares(f, l) for f in fams}; preds = len(b.get("predictions") or [])
            author = str((m.get("links") or {}).get("family") or "")
            v, sc = verdict(fs, b.get("evidence_ceiling", 0), b.get("cost_inr", 0), b.get("kind"), preds, author, min_ev); verdicts[m["id"]] = v
            weak = min((d for d in DIMS if d != "risk"), key=lambda d: sc[d])
            reasons = [_clean(w[q]) for f in fams for _a, w in fam_ans[f][l][:1] for q, dd, _t in QUESTIONS if dd == weak and w.get(q)][:2]
            rat = (f"{v.upper()} by code: evidence {sc['evidence']} (ceiling {b.get('evidence_ceiling', 0)}), novelty {sc['novelty']}, impact {sc['impact']}, "
                   f"feasibility {sc['feasibility']}, risk {sc['risk']}, cost {sc['cost']}; {preds} pre-registered prediction(s). Weakest: {weak}. Jury: " + " | ".join(reasons))[:800]
            am = {"type": "assessment_memo", "from_dept": "D3", "to_depts": ["C"], "urgency": m["urgency"], "subject": f"Assessment ({v}): {m['subject']}"[:140],
                  "body": {"memo_ref": m["id"], "scores": sc, "verdict": v, "jury": [f"{f}:{used[f]}" for f in fams], "rationale": rat if len(rat) >= 20 else rat + " (no notes)",
                           "checklist": {"families": fs, "min_evidence": min_ev, "orders": orders}, "canary": f"rejected by {', '.join(fams)} (memo {next(x for x, mm in by.items() if mm is can)})",
                           "kind": b.get("kind") or "technique", "evidence_ceiling": b.get("evidence_ceiling", 0), "author_family": author, "predictions": preds, "cost_inr": float(b.get("cost_inr") or 0)},
                  "evidence": [dict(e) for e in (m.get("evidence") or [])[:6]], "links": {"research": m["id"], "session": sid},
                  "owner_visible": False, "dedupe_key": f"assess|{m['id']}"}          # until the Council exists (B6) it waits silently at the owner's level
            _c, p = SC.check_memo(dict(am), now)
            if p:
                acts[m["id"]] = ("deferred", f"assessment refused by the memo write gate: {'; '.join(p[:1])}"[:300]); continue
            acts[m["id"]] = ("resolved", "assessment_memo", MEM.id_for(am, st, now)); memos.append(am)
    else:
        for m in waiting: acts[m["id"]] = ("deferred", f"Board session void, judged again next run: {void}"[:300])
        memos.append({"type": "problem_memo", "from_dept": "D3", "to_depts": ["D3"], "subject": "Review Board session void: no verdict could be trusted",
                      "body": {"what_failed": void[:400], "where": f"Review Board session {sid}", "attempt": 1}, "done_when": "a later Board session is valid (two families, canary rejected)",
                      "evidence": [{"source": f"Board_Log:{sid}", "date": iso(now)[:10], "type": "own data", "finding": void[:300]}], "dedupe_key": "board|void"})
    for r in rows: r["verdict"] = "void" if void else ("canary" if r["canary"] else verdicts.get(r["memo_ref"], ""))
    try:
        if rows: st.append(LOG, rows)
    except Exception as e: log(f"Board_Log not written: {scrub(e)[:120]}", "WARN")
    if not void:                                                          # a valid session repairs the Board's own void memo
        for m in brief.memos:
            if m["type"] == "problem_memo" and m["from_dept"] == "D3" and m.get("dedupe_key", "").startswith("board|void"):
                acts[m["id"]] = ("resolved", "repair_verified", sid)
    n = {k: sum(1 for v in verdicts.values() if v == k) for k in ORDER}
    return Out(output={"judged": len(verdicts), "void": void}, memos=memos, memo_actions=acts,
               measures={"memos_judged": len(verdicts), "accepted": n["accept"], "tested": n["test"], "rejected": n["reject"], "void": 1 if void else 0,
                         "families": len(fams), "judge_calls_discarded": sum(1 for x in notes if "not counted" in x)})
