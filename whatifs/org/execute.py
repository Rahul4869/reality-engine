"""Execution Engine: turns a ticket into a typed change, writes it down before and after, verifies it with evidence another component wrote later, and rolls it back when that fails. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, hashlib, json, re
from whatifs import core
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub, set_setting
from whatifs.org import DEPARTMENTS, palace as PAL, memos as MEM, registry as REG, schemas as SC, levers as LV, runner as RUN
from whatifs.org.palace import PalaceError
from whatifs.org.schemas import MemoError

TAB, LOG, AUDIT = "Tickets", "Lever_Changes", "Org_Audit"
WAITING = ("queued", "awaiting_owner")                                   # nothing has been changed yet
FLYING = ("intent", "applied", "dispatched", "pr_open", "merged")        # a change is under way or waits for its proof
DONE = ("verified", "rolled_back", "refused", "failed")
STATES = WAITING + FLYING + DONE
CLASSES = {"A": "knowledge", "B": "setting", "C": "experiment", "D": "prompt rule", "E": "code"}
RULE_KINDS = ("style_rule", "policy_rule")                               # what lever class D may carry (the department's rulebook)
MAKING = ("PLANNING", "VOICING", "VISUALS")                              # Episodes statuses of a video that is being made right now
GRACE_H = 2.0                                                            # how late the tick pass may be before a check calls the engine dead
INTENT_MIN = 5                                                           # an apply still marked 'intent' after this many minutes was interrupted

class Refused(ValueError):
    """The ticket cannot be executed as written; the text is the reason the sender reads."""

# ------------------------------------------------------------------ small tools
def on():
    """Is the Execution Engine switched on? (It needs the organisation and the Palace.)"""
    return RUN.on() and S("EXEC_ON", bool)

def _js(v, d):
    if isinstance(v, (list, dict)): return v
    try: x = json.loads(v) if str(v or "").strip() else None
    except (TypeError, ValueError): x = None
    return d if x is None else x

def _int(key, lo, hi):
    try: return int(min(hi, max(lo, float(S(key) or 0))))
    except (TypeError, ValueError): return int(float(core.DEFAULTS[key][0]))

TABS_COLS = tuple(c for c in core.TABS[TAB] if c not in ("undo", "attempts"))

def _rows(st):
    try: raw = st.rows(TAB)
    except Exception:
        st.ensure_tabs(); raw = st.rows(TAB)
    out = []
    for r in raw:
        if not str(r.get("id") or "").strip(): continue
        r = dict(r)
        for c in TABS_COLS: r[c] = str(r.get(c) or "").strip()
        r["undo"] = _js(r.get("undo"), [])
        try: r["attempts"] = int(float(r.get("attempts") or 0))
        except (TypeError, ValueError): r["attempts"] = 0
        out.append(r)
    return out

def _get(tid, st): return next((r for r in _rows(st) if r["id"] == tid), None)

def _save(st, row, now, **ch):
    ch["updated"] = iso(now); row.update(ch)
    st.update(TAB, "id", row["id"], ch); return row

def _log(st, row, action, now, by="engine", proof="", note="", old=None, new=None):
    """One appended ledger row per event of a change. A row is never edited afterwards."""
    st.append(LOG, [{"ts": iso(now), "change_id": row["change_id"], "ticket_id": row["id"], "lever_class": row["lever_class"], "dept": row["dept"], "target": row["target"],
                     "action": action, "old": row["old"] if old is None else old, "new": row["new"] if new is None else new, "by": by, "proof": str(proof)[:500], "note": str(note)[:400]}])

def _audit(st, row, outcome, note, now):
    try: st.append(AUDIT, [{"ts": iso(now), "kind": "lever", "run_id": row["change_id"] or row["id"], "dept": row["dept"], "trigger": f"lever {row['lever_class']}", "outcome": outcome, "note": f"{row['target']}: {note}"[:400]}])
    except Exception as e: log(f"org audit row not written: {scrub(e)[:100]}", "WARN")

def _cid(tid, attempt): return "LC-" + hashlib.sha1(f"{tid}|{attempt}".encode("utf-8")).hexdigest()[:10].upper()

def _days(row):
    d = _int("EXEC_VERIFY_DAYS", 2, 60)
    return min(120, d * (_int("EXEC_ARM_OUTPUTS", 1, 6) if row["lever_class"] == "C" else 1))

def _memo_move(fn, *a, **k):
    """A memo move that must not stop the engine (the ticket may be held by the Council or the owner by now, or closed by a person)."""
    try: return fn(*a, **k)
    except MemoError as e: log(f"execution engine: memo not moved: {e}", "WARN"); return None

def _born(t0, st, sessions=None):
    """Episode ids whose FIRST department run started at or after t0 - videos made wholly after a change - oldest first. (A setting or an experiment is
    never applied inside an episode run, so a run that starts in the very second of the change started after it.)"""
    first = {}
    for s in (st.rows(RUN.STAB) if sessions is None else sessions):
        ep = str(s.get("episode_id") or ""); t = parse_iso(s.get("started"))
        if ep and t and (ep not in first or t < first[ep]): first[ep] = t
    return [ep for ep, t in sorted(first.items(), key=lambda x: x[1]) if t >= t0]

def idle(st, now):
    """Is no video being made right now? A setting or an experiment changes only between videos: never under a script that is already written."""
    lim = min(48.0, max(1.0, S("ORG_RUN_STALE_H", float) or 6.0)) * 3600
    try: eps = st.rows("Episodes")
    except Exception: return True
    for e in eps:
        t = parse_iso(e.get("updated"))
        if str(e.get("status") or "") in MAKING and t and 0 <= (now - t).total_seconds() < lim: return False
    return True

# ------------------------------------------------------------------ lever class A (knowledge) and D (prompt rule): a Palace item
def _old_item(old, st):
    """The item as it stands, in the form palace.add takes it back (so a changed text can be restored by rollback)."""
    try: body = str(PAL.body(old["id"], st).get("body") or old["summary"])
    except Exception: body = old["summary"]
    return {"id": old["id"], "kind": old["kind"], "title": old["title"], "summary": old["summary"], "body": body, "departments": old["departments"], "stages": old["stages"],
            "topic_tags": old["topic_tags"], "evidence": old["evidence"], "applied_in": old["applied_in"], "derived_from": old["derived_from"], "priority": old["priority"],
            "cost_note": old.get("cost_note", "")}

def _plan_knowledge(t, row, st, now):
    cls, dept, body = row["lever_class"], row["dept"], t["body"]
    m = re.match(r"^palace:(.+)$", str(body.get("target") or "").strip())
    if not m: raise Refused("the target of a knowledge or rule lever is 'palace:<item key or id>'")
    if t["from_dept"] != "C": raise Refused(f"knowledge is accepted by the Council (or the owner), not by {t['from_dept']}: send the Council a memo with the evidence")
    key = m.group(1).strip(); val = body.get("value") if isinstance(body.get("value"), dict) else {}
    rs = PAL.rows(st); old = PAL.get(key, rs=rs) or PAL.get(PAL.item_id(key), rs=rs); iid = old["id"] if old else PAL.item_id(key); item = None
    if val:
        refs = list(dict.fromkeys([str(x) for x in (val.get("derived_from") or [])] + [t["id"]] + ([str(body["decision_ref"])] if body.get("decision_ref") else [])))
        item = dict({k: v for k, v in val.items() if k != "key"}, id=iid, derived_from=refs); item.setdefault("departments", [dept])
        clean, p = PAL.check(item, now)
        if p: raise Refused("the Palace refuses the item: " + "; ".join(p[:3]))
    elif old is None: raise Refused(f"there is no Palace item '{key}' to accept and the ticket carries none")
    else: clean = old
    if clean["owner_input"] or clean["kind"] == "owner_preference" or (old and old["owner_input"]): raise Refused("the owner's own words enter and change only through the Owner Office, never by lever")
    if cls == "D" and clean["kind"] not in RULE_KINDS: raise Refused(f"a prompt-rule lever carries a rule ({' / '.join(RULE_KINDS)}), not a {clean['kind']}: use lever class A")
    if cls == "A" and clean["kind"] in RULE_KINDS: raise Refused(f"a {clean['kind']} is a rule: use lever class D (a department's rulebook is bounded)")
    if "all" not in clean["departments"] and dept not in clean["departments"]: raise Refused(f"the item is not addressed to {dept}: no run of {dept} could ever prove it was used")
    if cls == "D":
        cap = _int("EXEC_RULES_PER_DEPT", 1, 40); live = [r for r in _rows(st) if r["lever_class"] == "D" and r["dept"] == dept and r["state"] in ("applied", "verified") and r["id"] != row["id"]]
        if len(live) >= cap: raise Refused(f"the rulebook of {dept} is full ({cap} rules made by ticket): retire or merge one first")
    undo = []
    if old is None: undo.append({"op": "retire", "id": iid})
    else:
        if item is not None and clean["content_hash"] != old["content_hash"]: undo.append({"op": "restore", "item": _old_item(old, st)})
        if old["status"] not in PAL.SERVABLE: undo.append({"op": "retire", "id": iid})
    return {"target": f"palace:{iid}", "old": f"{old['status']} v{old['version']}" if old else "", "new": clean["content_hash"], "undo": undo, "item": item,
            "need": "cited" if REG.prompted(dept) else "served"}          # v12 B6a: a department whose creative calls carry the playbook must cite the item

def _do_knowledge(row, op, st, now):
    iid = row["target"].split(":", 1)[1]
    if op["item"] is not None: PAL.add(op["item"], "council", "accepted", st=st, now=now)
    cur = PAL.get(iid, st)
    if cur["status"] == "retired": cur = PAL.transition(iid, "proposed", "council", f"brought back by ticket {row['id']}", st=st, now=now)
    if cur["status"] not in PAL.SERVABLE: PAL.transition(iid, "accepted", "council", f"accepted by ticket {row['id']}", st=st, now=now)

def _present_knowledge(row, st, now):
    """Read-back: the item is in the Palace as written, servable, and inside the playbook its department would be given right now."""
    iid = row["target"].split(":", 1)[1]; rs = PAL.rows(st); cur = PAL.get(iid, rs=rs)
    if cur is None: return False, f"{iid} is not in the Palace"
    if cur["content_hash"] != row["new"]: return False, f"{iid} does not hold the text of the ticket"
    if cur["status"] not in PAL.SERVABLE: return False, f"{iid} is {cur['status']}"
    pb = PAL.playbook(row["dept"], rs=rs, record=False, now=now, st=st)
    if iid not in pb["items"]: return False, f"the playbook of {row['dept']} has no room for it ({pb['tokens']} of {pb['cap']} tokens used, {pb['left_out']} items left out)"
    return True, f"{iid} is {cur['status']} v{cur['version']} and inside the playbook of {row['dept']}"

def _books(st):
    """{playbook id: the 'item@version' references it served} - what every recorded playbook really contained."""
    return {str(r.get("playbook_id")): {str(x) for x in _js(r.get("item_ids"), [])} for r in st.rows(PAL.PTAB)}

def _verify_knowledge(row, st, now):
    iid = row["target"].split(":", 1)[1]; t0 = parse_iso(row["applied_at"]) or now; cur = PAL.get(iid, st)
    if cur is None or cur["status"] not in PAL.SERVABLE or cur["content_hash"] != row["new"]:
        return "gone", f"{iid} is {cur['status'] if cur else 'gone'}" + (" with another text" if cur and cur["content_hash"] != row["new"] else "") + ": it was withdrawn or replaced after the change"
    books = _books(st); n = 0; cite = row["need"] == "cited"; ref = f"{iid}@{cur['version']}"          # the version the ticket wrote, not an older text of the same item
    for s in st.rows(RUN.STAB):          # a later complete run: it began at or after the second of the change and is not the run that made the change
        if s.get("dept") != row["dept"] or s.get("status") != "ok" or s.get("id") == row["session"] or (parse_iso(s.get("started")) or t0) < t0 or RUN.verify(s): continue
        if cite and s.get("inject") != "prompt" and not _js(s.get("applied_items"), []): continue      # a run that cannot cite (no model prompt, no code citation) neither proves nor uses up the window
        served = ref in books.get(str(s.get("playbook_id")), ()); cited = iid in _js(s.get("applied_items"), [])
        if served and (cited or not cite):
            return "verified", (f"Sessions:{s['id']} ({row['dept']} {s.get('trigger')}) ran after the change with {ref} in its playbook {s.get('playbook_id')}"
                                + (" and cited it" if cited else " (handed over with the work order: this department's work puts no playbook into a model prompt yet)"))
        n += 1
    lim = _int("EXEC_VERIFY_RUNS", 1, 10)
    if n >= lim: return "rollback", f"{n} complete runs of {row['dept']} after the change and none was {'served and cited' if cite else 'served'} {ref}"
    return None

def _undo_knowledge(row, st, now):
    iid = row["target"].split(":", 1)[1]; did = []
    for u in row["undo"]:
        cur = PAL.get(iid, st)
        if cur is None: return "skipped", f"{iid} is gone"
        if u.get("op") == "restore":
            if cur["content_hash"] != row["new"]: return "skipped", f"{iid} was changed again after the ticket: left as it is"
            PAL.add(u["item"], "council", st=st, now=now); did.append("the earlier text is back")
        elif u.get("op") == "retire" and cur["status"] in PAL.SERVABLE:
            PAL.transition(iid, "retired", "council", f"rolled back: ticket {row['id']} was not verified", st=st, now=now); did.append("retired")
    return "done", f"{iid}: " + (", ".join(did) or "nothing had been changed")

# ------------------------------------------------------------------ lever class B (setting): a registered cell, between videos
def _plan_setting(t, row, st, now):
    key = str(t["body"].get("target") or "").strip(); c = LV.check(row["dept"], key, t["body"].get("value"))
    if c["why"]: raise Refused(c["why"])
    return {"target": key, "old": c["old"], "new": c["new"], "undo": [{"op": "set", "key": key, "value": c["old"]}], "owner": c["owner"],
            "need": ",".join(LV.LEVERS[key]["checks"]) or "run"}

def _cell(key): return str(core.settings(refresh=True).get(key, "")).strip()

def _do_setting(row, op, st, now): set_setting(row["target"], row["new"])

def _present_setting(row, st, now):
    cur = _cell(row["target"])
    return (True, f"{row['target']} reads {cur}") if LV.same(row["target"], cur, row["new"]) else (False, f"{row['target']} reads '{cur}', not '{row['new']}'")

def _verify_setting(row, st, now):
    key = row["target"]; t0 = parse_iso(row["applied_at"]) or now; cur = _cell(key)
    if not LV.same(key, cur, row["new"]): return "gone", f"{key} now holds '{cur}': it was changed by hand after the engine set '{row['new']}' (the owner's hand wins)"
    ses = st.rows(RUN.STAB); eps = _born(t0, st, ses); checks = LV.LEVERS[key]["checks"]
    if checks:
        led = {}
        for r in st.rows("Feature_Ledger"):
            if r.get("episode_id") in eps and r.get("feature") in checks: led.setdefault(r["episode_id"], {})[r["feature"]] = r          # the latest row of a check wins
        for ep in eps:
            got = led.get(ep, {}); bad = next((f for f in checks if got.get(f, {}).get("status") in ("FAIL", "WAIVED")), None)
            if bad: return "rollback", f"{ep}, made after the change, failed {bad}: {str(got[bad].get('evidence'))[:160]}"
            if all(got.get(f, {}).get("status") == "PASS" for f in checks): return "verified", f"{ep} was made after the change and passed {', '.join(checks)} with {key} = {cur}"
        return None
    runs = [s for s in ses if s.get("dept") == row["dept"] and s.get("id") != row["session"] and (parse_iso(s.get("started")) or t0) >= t0 and (not s.get("episode_id") or s.get("episode_id") in eps)]
    bad = next((s for s in runs if s.get("status") in ("failed", "breach")), None)
    if bad: return "rollback", f"{row['dept']} {bad.get('trigger')} ({bad['id']}) ended {bad.get('status')} after the change: {str(bad.get('error'))[:140]}"
    ok = next((s for s in runs if s.get("status") == "ok" and not RUN.verify(s)), None)
    if ok: return "verified", f"Sessions:{ok['id']} ({row['dept']} {ok.get('trigger')}) finished a complete run after the change with {key} = {cur}"
    return None

def _undo_setting(row, st, now):
    """Compare and swap: the old value comes back only if the cell still holds what the engine wrote."""
    key = row["target"]; cur = _cell(key)
    if not LV.same(key, cur, row["new"]): return "skipped", f"{key} holds '{cur}', not the engine's '{row['new']}': left as it is"
    set_setting(key, row["old"]); back = _cell(key)
    return ("done", f"{key} is back at '{row['old']}'") if LV.same(key, back, row["old"]) else ("failed", f"{key} could not be set back to '{row['old']}': it reads '{back}'")

# ------------------------------------------------------------------ lever class C (experiment): a trial in the research rulebook (coin flip per video)
def _plan_arm(t, row, st, now):
    from whatifs import playbook as PB
    m = re.match(r"^playbook:(\w+)$", str(t["body"].get("target") or "").strip())
    if not m or m.group(1) not in PB.DEPTS: raise Refused("the target of an experiment lever is 'playbook:<" + " | ".join(PB.DEPTS) + ">'")
    if not S("PLAYBOOK_ON", bool): raise Refused("the rulebook trials are switched off (PLAYBOOK_ON): an arm could never be assigned to a video")
    v = t["body"].get("value") if isinstance(t["body"].get("value"), dict) else {}; have = PB.rows()
    ok, bad = PB.vet([{"rule": v.get("rule"), "department": m.group(1), "metric": v.get("metric"), "source_url": v.get("source_url"), "evidence": v.get("evidence"), "why": v.get("why") or t["subject"]}], have, iso(now))
    if not ok: raise Refused(f"the rulebook refuses the arm: {bad[0][1] if bad else 'it is not a rule'}")
    trials = [r for r in have if r.get("status") == "trial"]
    if len(trials) >= PB.MAX_TRIALS: raise Refused(f"all {PB.MAX_TRIALS} trial slots are in use ({', '.join(str(r.get('rule_id')) for r in trials)}): an arm that cannot start cannot be verified")
    arm = dict(ok[0], status="trial", note=f"ticket {t['id']}: {ok[0].get('note', '')}"[:200])
    return {"target": f"playbook:{m.group(1)}", "old": "", "new": arm["rule_id"], "undo": [{"op": "retire_rule", "rule_id": arm["rule_id"]}], "arm": arm, "need": str(_int("EXEC_ARM_OUTPUTS", 1, 6))}

def _arm(rid):
    from whatifs import playbook as PB
    return next((r for r in PB.rows() if r.get("rule_id") == rid), None)

def _do_arm(row, op, st, now):
    from whatifs import playbook as PB
    if _arm(row["new"]) is None: st.append(PB.TAB, [op["arm"]])

def _present_arm(row, st, now):
    r = _arm(row["new"])
    return (True, f"rulebook trial {row['new']} is {r.get('status')}") if r is not None and r.get("status") in ("trial", "active", "retired") else (False, f"rulebook trial {row['new']} is not in the rulebook")

def _verify_arm(row, st, now):
    rid = row["new"]; t0 = parse_iso(row["applied_at"]) or now; r = _arm(rid)
    if r is None: return "gone", f"trial {rid} was removed from the rulebook"
    if r.get("status") in ("active", "retired"): return "verified", f"trial {rid} was judged on its data: {r.get('status')} ({str(r.get('note'))[:120]})"
    born = set(_born(t0, st)); have = []
    for f in st.rows("Video_Features"):
        arm = _js(f.get("arm"), {}); side = (arm.get("playbook") or {}).get(rid) if isinstance(arm, dict) and isinstance(arm.get("playbook"), dict) else None
        if f.get("format") == "long" and f.get("video_key") in born and side in ("on", "off"): have.append(f"{f.get('video_key')}: {side}")
    need = max(1, int(float(row["need"] or 1)))
    if len(have) >= need: return "verified", f"{len(have)} long video(s) made after the change carry arm {rid} in their features ({', '.join(have[:4])})"
    return None

def _undo_arm(row, st, now):
    from whatifs import playbook as PB
    r = _arm(row["new"])
    if r is None or r.get("status") not in ("trial", "queued"): return "skipped", f"trial {row['new']} is {r.get('status') if r else 'gone'}: left as it is"
    st.update(PB.TAB, "rule_id", row["new"], {"status": "retired", "note": f"rolled back by the Execution Engine (ticket {row['id']})"[:200]})
    return "done", f"trial {row['new']} was taken out of the rulebook"

# ------------------------------------------------------------------ lever class E (code): a build request, the build workflow, checks, merge, checks again
def _spec_text(req, t):
    b = req["body"]
    return "\n".join([f"ORGANISATION BUILD REQUEST {req['id']} (ticket {t['id']}" + (f", decision {t['body'].get('decision_ref')}" if t["body"].get("decision_ref") else "") + ")",
                      "WHAT TO BUILD:", str(b["spec"]), "FILES IT MAY TOUCH: " + ", ".join(b["files"]), "TESTS TO ADD (each must fail without the change):"]
                     + [f"- {x}" for x in b["tests_to_add"]] + ["ACCEPTANCE: " + str(b["acceptance"]),
                      "Put new tests in NEW files named tests/test_*.py. Do not edit or delete an existing test: a change that needs that is read by the owner first."])

def _plan_build(t, row, st, now):
    if row["dept"] != "D12": raise Refused("a code change is built by Operations: address a lever class E ticket to D12")
    if not S("BUILDS_ON", bool): raise Refused("builds are switched off (BUILDS_ON)")
    v = t["body"].get("value") if isinstance(t["body"].get("value"), dict) else {}
    req = {"type": "build_request", "from_dept": "D12", "to_depts": ["D12"], "subject": t["subject"], "links": {"ticket": t["id"]}, "dedupe_key": f"build|{t['id']}",
           "body": {"spec": v.get("spec"), "files": v.get("files"), "tests_to_add": v.get("tests_to_add"), "acceptance": v.get("acceptance") or t["body"].get("acceptance_test")},
           "done_when": "the pull request is merged and every check on the merge commit is green"}
    c, p = SC.check_memo(req, now)
    if p: raise Refused("not a valid build request: " + "; ".join(p[:3]))
    return {"target": str(t["body"].get("target") or "code")[:200], "old": "", "new": "", "undo": [{"op": "revert_build"}], "request": req, "need": "merge"}

def _dispatch(row, req, t, why, st, now):
    from whatifs import builds as BLD
    text = _spec_text(req, t) + (f"\n\nTHE PREVIOUS ATTEMPT FAILED: {why}" if why else "")
    if not BLD.request_build(text, "repair" if why else "feature", request=req["id"]): raise RuntimeError("the build workflow could not be started")

def _do_build(row, op, st, now):
    req = MEM.write(op["request"], st, now); row["request_id"] = req["id"]
    st.update(TAB, "id", row["id"], {"request_id": req["id"]})
    _dispatch(row, req, MEM.get(row["id"], st), "", st, now)

def _present_build(row, st, now): return bool(row["request_id"]), f"build request {row['request_id'] or '(none)'} was sent to the build workflow"

def build_opened(request, pr, branch="", st=None, now=None):
    """Called by the build workflow once the pull request of an organisation build exists. True = the engine owns this pull request from here."""
    st = st or store(); now = now or now_utc()
    row = next((r for r in _rows(st) if r["request_id"] == str(request or "").strip() and r["state"] == "dispatched"), None)
    if row is None or not on(): return False
    _save(st, row, now, state="pr_open", pr=str(pr)); _log(st, row, "pr_open", now, by="build", note=f"pull request #{pr} {branch}".strip())
    return True

def _retry_build(row, m, why, st, now):
    from whatifs import builds as BLD
    if row["attempts"] > _int("EXEC_BUILD_RETRIES", 0, 4): return "fail", f"{why}; {row['attempts']} builds were tried"
    if row["pr"]: BLD.close_pr(row["pr"])
    req = MEM.get(row["request_id"], st)
    if req is None or req["status"] in SC.TERMINAL: return "fail", f"{why}; its build request is closed"
    _dispatch(row, req, m, why, st, now)
    _save(st, row, now, state="dispatched", pr="", owner_action="", attempts=row["attempts"] + 1, applied_at=iso(now)); _log(st, row, "retry", now, note=why)
    return None

def _verify_build(row, st, now, m=None):
    from whatifs import builds as BLD
    t0 = parse_iso(row["applied_at"]) or now; wait = _int("EXEC_BUILD_WAIT_H", 1, 48) * 3600
    if row["state"] == "dispatched":
        return _retry_build(row, m, f"no pull request was opened within {wait // 3600} hours", st, now) if (now - t0).total_seconds() > wait else None
    ps = BLD.pr_state(row["pr"])
    if row["state"] == "pr_open":
        if ps.get("merged"):
            _save(st, row, now, state="merged", new=str(ps.get("merge_sha") or ps.get("head") or "")); _log(st, row, "merged", now, by="owner" if row["owner_action"] else "engine", note=f"pull request #{row['pr']}")
            BLD.dispatch("checks.yml", {}, ref="main"); return None
        if ps.get("state") == "closed": return "fail", f"pull request #{row['pr']} was closed without a merge"
        if ps.get("checks") == "red": return _retry_build(row, m, f"the checks of pull request #{row['pr']} are red", st, now)
        if ps.get("checks") != "green" or row["owner_action"]: return None
        inside, why = LV.merge_scope(BLD.pr_files(row["pr"]))
        if inside:
            ok, msg = BLD.merge_pr(row["pr"], f"organisation build inside the automatic scope (ticket {row['id']})")
            _log(st, row, "auto_merge" if ok else "merge_failed", now, note=msg)
            return None
        aid = BLD.build_ready(row["pr"], "feature", note="It needs your Merge because " + "; ".join(why[:2]) + ".")
        _save(st, row, now, owner_action=str(aid)); _log(st, row, "owner_asked", now, note="; ".join(why)[:400])
        _memo_move(MEM.note_owner_told, row["id"], aid, st, now)
        return None
    cs = BLD.commit_state(row["new"])                                       # merged: the checks on the merge commit decide
    if cs == "green": return "verified", f"pull request #{row['pr']} is merged and every check on the merge commit {row['new'][:10]} is green"
    if cs == "red": return "rollback", f"the checks on the merge commit {row['new'][:10]} of pull request #{row['pr']} are red"
    return None

def _undo_build(row, st, now):
    """Merged code cannot be taken back by the engine alone: a revert is built and the owner merges it."""
    from whatifs import builds as BLD
    if row["state"] != "merged":
        if row["pr"]: BLD.close_pr(row["pr"])
        return "done", f"pull request #{row['pr'] or '-'} was closed unmerged"
    ok = BLD.request_build(f"Revert the merge commit {row['new']} of pull request #{row['pr']} with git revert and nothing else: its checks are red on main.", "repair")
    return "failed", ("a revert was sent to the build workflow and waits for your Merge" if ok else "the revert could NOT be sent to the build workflow") + f" (pull request #{row['pr']} is still in main)"

_CLASS = {"A": (_plan_knowledge, _do_knowledge, _present_knowledge, _verify_knowledge, _undo_knowledge),
          "D": (_plan_knowledge, _do_knowledge, _present_knowledge, _verify_knowledge, _undo_knowledge),
          "B": (_plan_setting, _do_setting, _present_setting, _verify_setting, _undo_setting),
          "C": (_plan_arm, _do_arm, _present_arm, _verify_arm, _undo_arm),
          "E": (_plan_build, _do_build, _present_build, _verify_build, _undo_build)}

# ------------------------------------------------------------------ the life of a ticket inside the engine
def apply(ticket, brief=None, st=None, now=None):
    """The EXECUTE step of a department run hands every open ticket of that department to this function. A new ticket gets its row and is started;
    a ticket that is waiting for a free moment is tried again; a ticket whose change is under way belongs to the tick pass. Returns the state."""
    st = st or store(); now = now or now_utc(); row = _get(ticket["id"], st)
    if row is None:
        b = ticket["body"]
        row = {"id": ticket["id"], "created": iso(now), "updated": iso(now), "from_dept": ticket["from_dept"], "dept": (ticket["to_depts"] or [""])[0], "lever_class": str(b.get("lever_class") or ""),
               "target": str(b.get("target") or "")[:200], "state": "queued", "change_id": "", "old": "", "new": "", "undo": [], "applied_at": "", "verify_by": "", "need": "", "proof": "",
               "attempts": 0, "approved": "", "owner_action": "", "decision_ref": str(b.get("decision_ref") or ""), "request_id": "", "pr": "", "note": "",
               "session": str(getattr(brief, "session_id", "") or "")}          # the run that hands the ticket over: it began before the change and can never be its proof
        st.append(TAB, [row])
    elif row["state"] != "queued": return row["state"]
    return _start(row, ticket, st, now, episode=str(getattr(brief, "episode", "") or ""))

def _refuse(row, t, why, st, now, by=None):
    _save(st, row, now, state="refused", note=str(why)[:400]); _log(st, row, "refused", now, by=by or row["dept"], note=why); _audit(st, row, "refused", why, now)
    _memo_move(MEM.reject, row["id"], by or row["dept"], f"refused by the Execution Engine: {why}"[:300], st, now)
    return "refused"

def _wait(row, t, why, st, now):
    """Not yet: the reason is written once (not once per tick) and the ticket is marked as taken up, so only its resolve clock keeps running."""
    if row["note"] != why: _save(st, row, now, state="queued", note=why[:400]); _log(st, row, "queued", now, note=why)
    if t and t["status"] in ("open", "acknowledged") and t["level"] == 0: _memo_move(MEM.start, row["id"], row["dept"], f"with the Execution Engine: {why}"[:200], st, now)
    return "queued"

def _start(row, t, st, now, episode=""):
    cls = row["lever_class"]
    if cls not in _CLASS: return _refuse(row, t, f"unknown lever class '{cls}'", st, now)
    if row["attempts"] > _int("EXEC_BUILD_RETRIES", 0, 4): return _fail(row, t, f"an interrupted apply was tried {row['attempts']} times", st, now)
    plan, do, present, _v, undo = _CLASS[cls]
    try: op = plan(t, row, st, now)
    except (Refused, PalaceError, MemoError) as e: return _refuse(row, t, str(e), st, now)
    if op.get("owner") and not row["approved"]: return _ask_owner(row, t, op, st, now)
    if cls in ("B", "C"):
        if episode or not idle(st, now): return _wait(row, t, "a setting or an experiment changes between videos, never while one is being made", st, now)
        busy = next((r for r in _rows(st) if r["dept"] == row["dept"] and r["lever_class"] in ("B", "C") and r["state"] in ("intent", "applied") and r["id"] != row["id"]), None)
        if busy: return _wait(row, t, f"waits until change {busy['change_id']} ({busy['target']}) of {row['dept']} is verified: one unverified change per department", st, now)
    n = row["attempts"] + 1
    _save(st, row, now, state="intent", change_id=_cid(row["id"], n), target=op["target"], old=op["old"], new=op["new"], undo=op["undo"], need=op["need"], attempts=n, note="")
    _log(st, row, "intent", now, by=row["dept"], note=f"asked by {t['from_dept']}: {t['subject']}")
    try:
        do(row, op, st, now); ok, seen = present(row, st, now)
    except (Refused, PalaceError, MemoError) as e: ok, seen = False, str(e)
    except Exception as e:                                         # a store or network error in the middle: the row stays 'intent' and the tick pass settles it
        log(f"execution engine: apply of {row['id']} interrupted: {type(e).__name__}: {scrub(e)[:160]}", "WARN"); return "intent"
    if not ok:
        try: res, note = undo(row, st, now)
        except Exception as e: res, note = "failed", f"{type(e).__name__}: {scrub(e)[:160]}"
        if res == "failed": return _fail(row, t, f"the change did not read back ({seen}) and could not be undone: {note}", st, now)
        return _refuse(row, t, f"the change did not take: {seen}", st, now)
    return _applied(row, t, seen, st, now)

def _applied(row, t, seen, st, now):
    until = now + dt.timedelta(days=_days(row)); state = "dispatched" if row["lever_class"] == "E" else "applied"
    _save(st, row, now, state=state, applied_at=iso(now), verify_by=iso(until), proof="")
    _log(st, row, state, now, by=row["dept"], proof=f"read back: {seen}"); _audit(st, row, state, f"{row['old'] or '-'} -> {row['new'] or '-'}", now)
    _memo_move(MEM.await_proof, row["id"], until, row["change_id"], st, now)
    return state

def _ask_owner(row, t, op, st, now):
    """One pre-filled message: what changes, why, and why it needs him. The ticket waits; nothing is changed before his tap."""
    from whatifs import notify as NT
    p0 = t["urgency"] == "P0"
    text = f"{DEPARTMENTS[row['dept']][0]} wants to change {op['target']} from {op['old'] or 'empty'} to {op['new'] or 'empty'}. Why: {t['subject']}. It needs your OK because {op['owner']}."
    aid = NT.send("org_lever", text, [("Approve", f"APPROVE {row['id']}"), ("Reject", f"REJECT {row['id']}")], tier="now" if p0 else "week", urgent=p0,
                  default="nothing changes until you answer", dedupe_key=f"org_lever|{row['id']}")
    if row["state"] != "awaiting_owner":
        _save(st, row, now, state="awaiting_owner", owner_action=str(aid), target=op["target"], old=op["old"], new=op["new"], note=op["owner"][:400])
        _log(st, row, "owner_asked", now, by=row["dept"], note=op["owner"])
        _memo_move(MEM.start, row["id"], row["dept"], "waits for the owner's approval", st, now); _memo_move(MEM.note_owner_told, row["id"], aid, st, now)
    return "awaiting_owner"

def _on_answer(arow, choice):
    """The owner's tap on an approval message: APPROVE lets the engine make the change (at the next free moment); REJECT closes the ticket as his decision."""
    verb, _, tid = str(choice or "").strip().partition(" "); st = store(); now = now_utc(); row = _get(tid.strip(), st); m = MEM.get(tid.strip(), st)
    if row is None or m is None or row["state"] != "awaiting_owner": return "already settled"
    if verb.upper() == "REJECT":
        _save(st, row, now, state="refused", note="the owner said no"); _log(st, row, "owner_rejected", now, by="owner")
        _memo_move(MEM.reject, tid.strip(), "owner", "the owner said no on the approval message", st, now); return "rejected: nothing was changed"
    _save(st, row, now, state="queued", approved=iso(now), note="approved by the owner"); _log(st, row, "owner_approved", now, by="owner")
    out = _start(row, m, st, now)
    return {"applied": "approved and changed; it is now being verified", "queued": "approved; it changes between videos, at the next free moment"}.get(out, f"approved ({out})")

def register():
    from whatifs import notify as NT
    NT.register("org_lever", on_answer=_on_answer)

def _close(row, kind, note, st, now):
    """The ticket (and the build request of a code lever) is closed with the ledger row as its proof - the only way memos.resolve accepts."""
    _memo_move(MEM.resolve, row["id"], "engine", kind, row["change_id"], note, st, now)
    if not row["request_id"]: return
    if kind == "lever_verified": _memo_move(MEM.resolve, row["request_id"], "engine", "merged_verified", row["change_id"], note, st, now)
    else: _memo_move(MEM.reject, row["request_id"], "D12", f"the build was not verified: {note}"[:300], st, now)

def _fail(row, t, why, st, now):
    """The change could neither be verified nor cleanly undone, or a build ran out of attempts: the ticket goes up the ladder at once."""
    _save(st, row, now, state="failed", note=str(why)[:400]); _log(st, row, "failed", now, note=why); _audit(st, row, "failed", why, now)
    if row["request_id"]: _memo_move(MEM.reject, row["request_id"], "D12", f"the build failed: {why}"[:300], st, now)
    _memo_move(MEM.escalate, row["id"], f"the Execution Engine could not finish the change: {why}"[:200], "clock", st, now)
    return "failed"

def _rollback(row, t, why, st, now, gone=False):
    if gone: res, note = "skipped", "nothing to take back"
    else:
        try: res, note = _CLASS[row["lever_class"]][4](row, st, now)
        except Exception as e: res, note = "failed", f"{type(e).__name__}: {scrub(e)[:160]}"
    if res == "failed": return _fail(row, t, f"{why}; rollback failed: {note}", st, now)
    _save(st, row, now, state="rolled_back", proof=note[:500], note=str(why)[:400])
    _log(st, row, "rolled_back" if res == "done" else "rollback_skipped", now, proof=note, note=why); _audit(st, row, "rolled_back", f"{why}; {note}", now)
    _close(row, "rolled_back", f"{why}; {note}"[:300], st, now)
    return "rolled_back"

def _judge(row, t, st, now):
    verify = _CLASS[row["lever_class"]][3]
    v = verify(row, st, now, t) if row["lever_class"] == "E" else verify(row, st, now)
    late = (parse_iso(row["verify_by"]) or now) < now
    if v is None and late: v = ("fail" if row["lever_class"] == "E" else "rollback", f"no evidence within {_days(row)} days" + (": the checks on the merge commit never reported" if row["state"] == "merged" else ""))
    if v is None: return row["state"]
    kind, text = v
    if kind == "verified":
        _save(st, row, now, state="verified", proof=text[:500]); _log(st, row, "verified", now, proof=text); _audit(st, row, "verified", text, now)
        _close(row, "lever_verified", text[:300], st, now); return "verified"
    if kind == "fail":                                                 # a build that ran out of attempts or time: an unmerged pull request is closed; merged code is never reverted on a guess
        try:
            if row["state"] != "merged": _undo_build(row, st, now)
        except Exception as e: log(f"execution engine: pull request of {row['id']} not closed: {scrub(e)[:120]}", "WARN")
        return _fail(row, t, text, st, now)
    return _rollback(row, t, text, st, now, gone=(kind == "gone"))

def _recover(row, t, st, now):
    """An apply that a killed job left half done: look at what is really there. Present = carry on as applied; absent = start again."""
    if (now - (parse_iso(row["updated"]) or now)).total_seconds() < INTENT_MIN * 60: return "intent"
    try: ok, seen = _CLASS[row["lever_class"]][2](row, st, now)
    except Exception as e: ok, seen = False, f"{type(e).__name__}: {scrub(e)[:120]}"
    if ok and not (row["lever_class"] == "E"): return _applied(row, t, f"{seen} (found by the tick pass after an interrupted apply)", st, now)
    _save(st, row, now, state="queued", note="an apply was interrupted before it took effect; it starts again"); _log(st, row, "interrupted", now, note=seen)
    return _start(row, t, st, now)

def reconcile(st=None, now=None):
    """The tick pass. It reads state, not events, so a missed tick or a killed job loses nothing: every ticket the engine holds is moved as far as the
    evidence allows - a waiting one is started when its moment is free, an interrupted one is settled, an applied one is verified or rolled back,
    a build is followed to its merge - and a change whose ticket a person closed in the meantime is taken back."""
    st = st or store(); now = now or now_utc(); rep = {"open": 0, "moved": {}}
    if not on(): return rep
    rows = [r for r in _rows(st) if r["state"] not in DONE]
    if not rows: return rep
    ms = {m["id"]: m for m in MEM.rows(st)}
    for r in sorted(rows, key=lambda r: (r["created"], r["id"])):
        was = r["state"]
        try:
            m = ms.get(r["id"])
            if m is None or m["status"] in SC.TERMINAL:
                why = f"the ticket was closed by {((m or {}).get('resolution') or {}).get('by') or 'somebody'} while the engine held it" if m else "the ticket is gone"
                if was in WAITING: _save(st, r, now, state="refused", note=why); _log(st, r, "refused", now, note=why); out = "refused"
                else: out = _rollback(r, m, why, st, now)
            elif was == "queued": out = _start(r, m, st, now)
            elif was == "awaiting_owner": out = was
            elif was == "intent": out = _recover(r, m, st, now)
            else: out = _judge(r, m, st, now)
        except Exception as e:
            out = was; log(f"execution engine: ticket {r['id']} skipped this pass: {type(e).__name__}: {scrub(e)[:160]}", "WARN")
        if out != was: rep["moved"][r["id"]] = f"{was} -> {out}"
        if out not in DONE: rep["open"] += 1
    return rep

def overview(st=None):
    """Counts of the engine's tickets by state (the measures of an Operations run and the evidence line of the two checks)."""
    rows = _rows(st or store()); out = {"tickets": len(rows)}
    for s in ("verified", "rolled_back", "refused", "failed"): out[s] = sum(1 for r in rows if r["state"] == s)
    out["waiting"] = sum(1 for r in rows if r["state"] in WAITING); out["in_verification"] = sum(1 for r in rows if r["state"] in FLYING)
    return out

def tick_age_h(now=None):
    """Hours since the engine's tick pass last finished (None = it has never run on this Sheet)."""
    t = parse_iso(S("EXEC_TICK_AT"))
    return None if not t else round(((now or now_utc()) - t).total_seconds() / 3600, 2)

def engine_tick(st=None, now=None):
    """Every tick, next to the SLA watchdog. (1) The reconcile pass. (2) Every new ticket of a wired department is taken up at once - a department
    that only runs inside a video would otherwise see its ticket a week late: knowledge is applied now, a setting at the next gap between videos.
    (3) Only when Operations itself holds a new ticket, one D12 run: its EXECUTE step starts it. An idle engine costs two reads."""
    st = st or store(); now = now or now_utc()
    if not on(): return {"on": False}
    rep = reconcile(st, now); known = {r["id"] for r in _rows(st)}; own = []
    for m in MEM.rows(st):
        if m["type"] != "ticket" or m["status"] not in SC.LIVE or m["level"] != 0 or m["id"] in known or len(m["to_depts"]) != 1: continue
        if m["to_depts"][0] == "D12": own.append(m["id"]); continue
        if not REG.runnable(m["to_depts"][0]): continue
        try: rep["moved"][m["id"]] = f"new -> {apply(m, None, st, now)}"
        except Exception as e: log(f"execution engine: new ticket {m['id']} not taken up this pass: {type(e).__name__}: {scrub(e)[:160]}", "WARN")
    if own:
        RUN.work("D12", "operate", "", lambda b: overview(st), measure=dict, st=st, now=now); rep["operated"] = own
    try: set_setting("EXEC_TICK_AT", iso(now))
    except Exception as e: log(f"engine tick time not recorded: {scrub(e)[:100]}", "WARN")
    return dict(rep, on=True)

# ------------------------------------------------------------------ what the two contract checks judge
def decision_issues(st=None, now=None):
    """(problems, stats) for check decisions_executed: nothing decided may stay text. A decision that changes something has tickets; each ticket it
    names exists; a ticket is closed only with the engine's proof; a ticket past its deadline has been escalated to somebody who was told."""
    st = st or store(); now = now or now_utc(); ms = MEM.rows(st); by = {m["id"]: m for m in ms}; tk = {r["id"]: r for r in _rows(st)}; p = []
    decs = [m for m in ms if m["type"] == "decision_memo"]; tickets = [m for m in ms if m["type"] == "ticket"]; grace = dt.timedelta(hours=GRACE_H)
    for d in decs:
        ids = [str(x) for x in (d["body"].get("tickets") or [])]
        if d["body"].get("lever_class") not in (None, "", "none") and not ids and (parse_iso(d["created"]) or now) + grace < now:
            p.append(f"decision {d['id']} ('{d['subject'][:60]}') changes something (lever class {d['body'].get('lever_class')}) and has no ticket: it is text only")
        p += [f"decision {d['id']} names ticket {i}, which does not exist" for i in ids if i not in by or by[i]["type"] != "ticket"]
    for t in tickets:
        state = (tk.get(t["id"]) or {}).get("state", ""); kind = (t["resolution"] or {}).get("kind")
        if t["status"] == "resolved" and kind in ("lever_verified", "rolled_back") and state != {"lever_verified": "verified", "rolled_back": "rolled_back"}[kind]:
            p.append(f"ticket {t['id']} is closed as {kind} but the engine holds it as '{state or 'unknown'}'")
        if t["status"] in SC.LIVE and (parse_iso(t["sla_due"]) or now) + grace < now and (t["level"] < 2 or not t["owner_notified"]):
            p.append(f"ticket {t['id']} ('{t['subject'][:60]}') is past its deadline and nobody above was told (level {t['level']})")
    live = sum(1 for t in tickets if t["status"] in SC.LIVE)
    return p, {"decisions": len(decs), "tickets": len(tickets), "live": live, "with_owner": sum(1 for t in tickets if t["status"] in SC.LIVE and t["level"] >= 2)}

def lever_issues(st=None, now=None):
    """(problems, stats) for check lever_verified: every change the engine made has its ledger rows in order (intent before applied, a verdict with
    its proof after), nothing sits past its verification window, nothing failed without being taken back, and the lever table is honest."""
    st = st or store(); now = now or now_utc(); p = LV.issues()[:5]; rows = _rows(st); grace = dt.timedelta(hours=GRACE_H); acts = {}
    for r in st.rows(LOG): acts.setdefault(str(r.get("ticket_id")), []).append(r)
    waiting = [r for r in rows if r["state"] not in DONE and (parse_iso(r["created"]) or now) + dt.timedelta(hours=24) < now]; age = tick_age_h(now)
    if waiting and (age is None or age > 24):
        p.append(f"the Execution Engine's tick pass has {'never run' if age is None else f'not run for {age:.0f} h'} while {len(waiting)} ticket(s) wait: nothing is being verified or rolled back")
    for r in rows:
        a = [str(x.get("action")) for x in acts.get(r["id"], [])]; tag = f"change {r['change_id'] or r['id']} ({r['target']})"
        if r["state"] in FLYING and r["state"] != "intent" and (parse_iso(r["verify_by"]) or now) + grace < now: p.append(f"{tag} is past its verification window with no verdict (the tick pass is not doing its work)")
        if r["state"] == "intent" and (parse_iso(r["updated"]) or now) + grace < now: p.append(f"{tag}: an interrupted apply was never settled")
        if r["state"] == "failed": p.append(f"{tag} failed and was not taken back: {r['note'][:120]}")
        if r["state"] in ("applied", "verified", "rolled_back", "dispatched", "pr_open", "merged") and "intent" not in a: p.append(f"{tag} was changed without an intent row in the ledger")
        if r["state"] == "verified" and not any(x.get("action") == "verified" and len(str(x.get("proof") or "")) >= 20 for x in acts.get(r["id"], [])): p.append(f"{tag} is marked verified without a proof in the ledger")
        if r["state"] == "rolled_back" and not ({"rolled_back", "rollback_skipped"} & set(a)): p.append(f"{tag} is marked rolled back without a ledger row")
    return p, overview(st)
