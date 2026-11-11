"""World canon: the show's living bible as Palace items - the cast mirrored from the character bible, a case record written by code after every D4 write and accepted only when the upload is confirmed, the continuity debt the next script must pay, and the check canon_in_brief. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub
from whatifs.org import palace as PAL

CASE_TAG, CAST_TAG = "case-record", "cast"
_WEAK = {"were", "your", "would", "they", "them", "their", "there", "about", "what", "whole", "just", "like", "even", "ever"}
WINNER = {"vale": "Inspector Vale", "grimm": "Dr. Grimm", "split": "nobody outright (split)"}

def cast_ids():
    """The Palace ids of the cast canon: one item per character of the live character bible (Characters tab), mirrored by palace.sync_canon."""
    from whatifs import show as SH
    return [PAL.item_id("canon:character:" + str(c.get("id") or "").strip()) for c in SH.characters() if str(c.get("id") or "").strip()]

def case_id(ep):
    return PAL.item_id("canon:case:" + str(ep))

def ensure_cast(st=None, now=None):
    """Before a creative run: the cast canon exists (the daily mirror may not have run yet on a new Sheet). Returns True when it had to mirror."""
    st = st or store()
    try:
        have = {r["id"] for r in PAL.rows(st)}
        if all(i in have for i in cast_ids()): return False
        PAL.sync_canon(st=st, now=now); return True
    except Exception as e:
        log(f"cast canon not mirrored: {scrub(e)[:160]}", "WARN"); return False

def _stamp(t):
    return int((t or now_utc()).strftime("%Y%m%d%H%M"))

def is_case(r):
    return r.get("kind") == "world_canon" and CASE_TAG in (r.get("topic_tags") or [])

def _clip(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "-"

def facts(ep, room):
    """The case's facts, read by code from the show plan and the script (nothing invented, nothing judged)."""
    spine = (room or {}).get("spine") or {}; plan = spine.get("show_plan") if isinstance(spine.get("show_plan"), dict) else {}
    sc = (room or {}).get("script"); script = str((sc.get("script") if isinstance(sc, dict) else sc) or "")
    v = plan.get("verdict") if isinstance(plan.get("verdict"), dict) else {}
    proto = re.search(r"(?i)prototype\s+no\.?\s*(\d{1,4})", script)
    return {"episode": str(ep), "headline": _clip(spine.get("headline") or spine.get("premise"), 90), "premise": _clip(spine.get("premise"), 140),
            "charge": _clip(plan.get("charge"), 140), "winner": str(v.get("winner") or ""), "style": _clip(v.get("style"), 60), "detail": _clip(v.get("detail"), 90),
            "twist": _clip(plan.get("witness_twist"), 80), "prototype": proto.group(1) if proto else "", "stinger": _clip(plan.get("stinger"), 120)}

def summary(f, n):
    parts = [f"Case {n} ({f['episode'][2:10] if f['episode'].startswith('EP') else f['episode'][:10]}): {f['charge'] or f['premise'] or f['headline']}."]
    if f["winner"]: parts.append(f"Verdict: {WINNER.get(f['winner'], f['winner'])}" + (f" ({f['style']})" if f["style"] else "") + (f" on '{f['detail']}'." if f["detail"] else "."))
    if f["twist"]: parts.append(f"Witness twist: {f['twist']}.")
    if f["prototype"]: parts.append(f"Grimm's Prototype No. {f['prototype']} failed.")
    if f["stinger"]: parts.append(f"Promised next: '{f['stinger']}'")
    out = ""
    for p in parts:
        if len(out) + len(p) + 1 <= PAL.SUMMARY_MAX: out = (out + " " + p).strip()
    return out

def record(ep, room, session="", st=None, now=None):
    """D4's continuity takeaway after every write: the case record, PROPOSED (it becomes canon only on air). Returns its id ('' when it could not be written)."""
    st = st or store(); now = now or now_utc(); ep = str(ep or "")
    if not ep: return ""
    try:
        f = facts(ep, room); rs = PAL.rows(st)
        n = 1 + sum(1 for r in rs if is_case(r) and PAL.aired(r) and r["id"] != case_id(ep))
        words = [w for w in re.findall(r"[a-z]{4,}", (f["premise"] + " " + f["charge"]).lower()) if w not in PAL._STOP and w not in _WEAK][:6]
        item = {"key": "canon:case:" + ep, "kind": "world_canon", "title": _clip(f"Case {n}: {f['headline'] or ep}", 120).ljust(8, "."), "summary": summary(f, n).ljust(20, "."),
                "departments": ["D4", "D5", "D1"], "stages": ["ideation", "writing", "packaging", "planning"], "topic_tags": ["canon", "case", CASE_TAG, f["winner"] or "case"] + words, "priority": 2,
                "derived_from": [session] if session else [], "evidence": [{"source": f"show plan and script of {ep}" + (f" (Sessions:{session})" if session else ""),
                "date": iso(now)[:10], "type": "show record", "finding": json.dumps(f, ensure_ascii=False)[:600]}]}
        old = PAL.get(case_id(ep), st=st, rs=rs)
        if old is not None and old["status"] != "proposed": return old["id"]                # already on air: what aired is never rewritten
        return PAL.add(item, "D4", st=st, now=now)["id"]
    except Exception as e:
        log(f"case record for {ep} not written: {scrub(e)[:160]}", "WARN", ep); return ""

def on_air(ep, video_id, st=None, now=None):
    """After the upload is verified: the case record becomes canon (D9 holds the video id). Returns True when it moved."""
    st = st or store(); now = now or now_utc(); iid = case_id(ep)
    try:
        r = PAL.get(iid, st=st)
        if r is None or r["status"] != "proposed" or not video_id: return False
        it = {k: r[k] for k in ("kind", "title", "summary", "departments", "stages", "evidence", "derived_from", "priority")}
        it.update(id=iid, topic_tags=[t for t in r["topic_tags"] if not t.startswith("aired-")][:10] + [f"aired-{_stamp(now)}"],
                  evidence=r["evidence"] + [{"source": f"platform upload {video_id} of {ep}", "date": iso(now)[:10], "type": "show record"}])
        PAL.add(it, "D9", st=st, now=now)
        PAL.transition(iid, "accepted", "D9", f"on air as {video_id}: what aired is canon", st=st, now=now)
        return True
    except Exception as e:
        log(f"case record for {ep} not made canon: {scrub(e)[:160]}", "WARN", ep); return False

def newest_case(rs, at=None, now=None):
    """The newest case record that was on air before `at` and may be served."""
    now = now or now_utc(); lim = _stamp(at) if at else None
    c = [r for r in rs if is_case(r) and PAL.aired(r) and (lim is None or PAL.aired(r) <= lim) and PAL.servable(r, now)]
    return max(c, key=PAL.aired) if c else None

def required(rs, dept="D4", at=None, now=None):
    """What a D4 playbook must hold: every servable cast item addressed to the department, and the newest case that was on air at that time."""
    from whatifs.org import DEPARTMENTS
    now = now or now_utc(); by = {r["id"]: r for r in rs}; stage = DEPARTMENTS[dept][1]
    cast = [i for i in cast_ids() if i in by and PAL.servable(by[i], now) and PAL._addressed(by[i], dept, stage)]
    nc = newest_case(rs, at, now) if dept == "D4" else None
    return {"cast": cast, "case": nc["id"] if nc else ""}

GENERIC = {"case", "cases", "verdict", "witness", "twist", "grimm", "prototype", "failed", "promised", "next", "inspector", "vale", "nana", "rosa", "split",
           "nobody", "outright", "archivist", "court", "charge", "charged", "accused", "judge", "jury", "exhibit", "trial", "defendant", "record", "records"}

def topic_words(r):
    """What makes one case THIS case: its topic words (premise and charge), or for an older mirrored case the specific words of its title and summary."""
    if r is None: return set()
    tags = {t for t in (r.get("topic_tags") or []) if t not in ("canon", "case", CASE_TAG, "vale", "grimm", "split") and not str(t).startswith("aired-")}
    words = {w for w in tags if re.fullmatch(r"[a-z]{4,}", w)} or {w for w in re.findall(r"[a-z]{5,}", (r.get("title", "") + " " + r.get("summary", "")).lower())}
    return {w for w in words if w not in GENERIC and w not in PAL._STOP and w not in _WEAK}

def names_case(quote, r):
    """Does a callback line name its case? At least one of the case's own topic words (stem match: 'pillow' matches 'pillows') is in the line."""
    q = set(re.findall(r"[a-z]{4,}", str(quote or "").lower())); tw = topic_words(r)
    return bool(tw) and any(any(x.startswith(w[:6]) or w.startswith(x[:6]) for x in q) for w in tw)

def must_cite(dept, items, rs, now=None):
    """The continuity debt of this run: the newest aired case, when it is in the playbook (D4, CANON_CALLBACK_ON)."""
    if dept != "D4" or not S("CANON_CALLBACK_ON", bool): return []
    nc = newest_case(rs, None, now)
    return [nc["id"]] if nc and nc["id"] in set(items or []) else []

# ------------------------------------------------------------------ the check
def episode_issues(ep, script_text, st=None, now=None):
    """{'na', 'problems', 'stats'} for canon_in_brief: the D4 run that wrote this episode's script was given every required canon item, paid the
    continuity debt with a line found in the final script, and the episode's case record exists, derived from the D4 write run."""
    from whatifs.org import cite as CITE
    st = st or store(); now = now or now_utc(); ep = str(ep or ""); res = {"na": "", "problems": [], "stats": {}}
    runs = {(d, t): (r, how) for d, t, r, how in CITE.creative_runs(ep, st)}
    r, how = runs.get(("D4", "write"), (None, ""))
    own = CITE._latest(st.rows("Sessions"), "D4", "write", ep)
    pre = CITE.episode_issues(ep, "injected", st)
    if pre["na"]: res["na"] = pre["na"]; return res
    p = res["problems"]
    if r is None: p.append("the D4 run that wrote the script is not recorded" + (f" ({how})" if how and how != "own run" else "")); return res
    load = CITE._receipt(r, "LOAD"); act = CITE._receipt(r, "ACT"); rs = PAL.rows(st)
    if act.get("legacy_draft") and r.get("inject") != "prompt":
        res["na"] = f"owner-approved draft {act['legacy_draft']} was written before the canon reached the writers"; return res
    pb = next((x for x in st.rows("Palace_Playbooks") if x.get("playbook_id") == load.get("playbook_id")), None)
    try: given = {str(i).split("@")[0] for i in (json.loads(pb.get("item_ids") or "[]") if isinstance(pb.get("item_ids"), str) else pb.get("item_ids") or [])} if pb else set()
    except (TypeError, ValueError): given = set()
    if not pb: p.append(f"the D4 playbook {load.get('playbook_id') or '-'} is not stored: what the writer was given cannot be proven"); return res
    req = required(rs, "D4", parse_iso(r.get("started")), now)
    miss = [i for i in req["cast"] if i not in given] + ([req["case"]] if req["case"] and req["case"] not in given else [])
    if miss: p.append(f"the writer's playbook lacked {len(miss)} canon item(s) it had to hold: {', '.join(miss[:3])}")
    res["stats"] = {"cast": len(req["cast"]), "newest_case": req["case"] or "none yet", "canon_given": len([i for i in given if i in {x['id'] for x in rs if x['kind'] == 'world_canon'}])}
    if req["case"] and S("CANON_CALLBACK_ON", bool):
        q = next((c.get("where") for c in (act.get("citations") or []) if c.get("id") == req["case"]), None)
        if not q: p.append(f"the continuity debt was not paid: the newest aired case {req['case']} is not cited by the writer")
        elif not CITE.found(q, CITE.tokens(script_text)): p.append(f"the callback to {req['case']} is not in the final script (quoted: '{str(q)[:80]}')")
        elif not names_case(q, PAL.get(req["case"], st=st, rs=rs)):
            p.append(f"the line cited as the callback to {req['case']} does not name that case (it shares none of: {', '.join(sorted(topic_words(PAL.get(req['case'], st=st, rs=rs)))[:6])})")
        else: res["stats"]["callback"] = str(q)[:80]
    rec = PAL.get(case_id(ep), st=st, rs=rs)
    if rec is None: p.append(f"no case record for {ep}: D4 did not write its continuity takeaway")
    elif own is not None and own.get("id") not in rec["derived_from"]: p.append(f"the case record of {ep} is not derived from its D4 write run {own.get('id')}")
    return res
