"""whatifs/tableread.py v8.0 - the optional "table read": departments read and challenge each other's memos BEFORE the production bible
is written, and the Director reads the FINAL script before any shot is planned. Both happen before any image money is spent.

Honest status: this is OFF by default. All departments are the same kind of AI model, so extra rounds of discussion may add polish
rather than new ideas. Nobody has measured whether it helps this channel. TABLE_READ_MODE = alternate flips a recorded coin per
episode so that, after about 10 episodes per arm, `python -m whatifs.cli abtest` can compare real results (watch time, retention, cost).

Everything here is fail-forward: any error returns "no objections" / "no notes" and the normal pipeline carries on.
Objection and note text is creative material from unreleased episodes: it goes to the private Sheet and Drive only, never to the public Actions log."""
from __future__ import annotations
import hashlib, json, os, random, statistics
from whatifs.core import S, log, iso, scrub, safe_append, safe_rows, WORK

ROLES = ["WRITER", "AUDIENCE PSYCHOLOGIST", "DIRECTOR + DP", "EDITOR + SOUND", "PACKAGER", "REEL PRODUCER"]
MAX_PER_ROLE = 3
MAX_TOTAL = 12
MIN_PER_ARM = 5

def _on(v): return str(v).strip().lower() in ("on", "true", "yes", "1")

def active_arm(episode, mode=None):
    """('on'|'off', mode). Deterministic for an episode id, so the budget plan and the room always agree."""
    m = str(mode if mode is not None else S("TABLE_READ_MODE")).strip().lower()
    if _on(m): return "on", "on"
    if m == "alternate":
        flip = int(hashlib.md5(("tableread|" + str(episode)).encode()).hexdigest()[:8], 16) % 2
        return ("on" if flip else "off"), "alternate"
    return "off", ("off" if m in ("off", "false", "no", "0", "") else "off")

def clean_objections(raw, from_role):
    """Keep only well-formed objections addressed to another real department. Text is trimmed. Max 3 per department."""
    out = []
    items = raw.get("objections") if isinstance(raw, dict) else None
    for o in (items if isinstance(items, list) else []):
        if not isinstance(o, dict): continue
        to = str(o.get("to", "")).strip().upper()
        text = " ".join(str(o.get("objection", "")).split())[:300]
        req = " ".join(str(o.get("request", "")).split())[:300]
        if to not in ROLES or to == from_role or not text: continue
        out.append({"from": from_role, "to": to, "objection": text, "request": req})
        if len(out) >= MAX_PER_ROLE: break
    return out

def clean_notes(raw):
    notes = []
    items = raw.get("notes") if isinstance(raw, dict) else None
    for n in (items if isinstance(items, list) else []):
        if not isinstance(n, dict): continue
        text = " ".join(str(n.get("note", "")).split())[:240]
        if not text: continue
        try: beat = int(n.get("beat"))
        except Exception: beat = 0
        notes.append({"beat": beat, "note": text})
        if len(notes) >= 6: break
    return notes

def objections_round(memos, spine, episode, ask_many_fn=None):
    """Round 2. memos = {role: memo dict}. Returns a validated list of objections ([] on any failure)."""
    try:
        from whatifs import prompts as P
        from whatifs.data import CRAFT_BY_ROLE
        if ask_many_fn is None:
            from whatifs.models import ask_many as ask_many_fn
        sp = json.dumps(spine, ensure_ascii=False)[:2000]
        jobs = []
        for r in ROLES:
            mine = json.dumps(memos.get(r, {}), ensure_ascii=False)[:900]
            others = json.dumps({k: json.dumps(v, ensure_ascii=False)[:700] for k, v in memos.items() if k != r}, ensure_ascii=False)[:5000]
            jobs.append(dict(role="sonnet", system=P.fill(P.MEMO2, role=r, mine=mine, others=others, spine=sp, craft=CRAFT_BY_ROLE.get(r, "")),
                             prompt="Raise your objections now.", episode=episode, fake_key="memo2", max_tokens=900))
        results = ask_many_fn(jobs)
        out = []
        for r, res in zip(ROLES, results): out += clean_objections(res, r)
        return out[:MAX_TOTAL]
    except Exception as e:
        log(f"table read round skipped: {scrub(e)}", "WARN", episode); return []

def objections_text(objs):
    if not objs: return "none raised"
    return "\n".join(f"{o['from']} -> {o['to']}: {o['objection']} | wants: {o['request']}" for o in objs)[:4000]

def director_notes(script_text, look, episode, ask_fn=None):
    """The Director reads the final narration and returns up to 6 visual-planning notes ([] on any failure)."""
    try:
        from whatifs import prompts as P
        if ask_fn is None:
            from whatifs.models import ask as ask_fn
        raw = ask_fn("sonnet", P.fill(P.DIRECTOR_READ, look=look, script=str(script_text)[:24000]), "Read it and give your notes.",
                     episode=episode, fake_key="director_read", max_tokens=1200, temperature=0.4)
        return clean_notes(raw)
    except Exception as e:
        log(f"director script read skipped: {scrub(e)}", "WARN", episode); return []

def notes_text(notes):
    if not notes: return "none"
    return "\n".join(f"Beat {n['beat']}: {n['note']}" if n["beat"] else n["note"] for n in notes)[:2500]

def rows_for_sheet(rec):
    base = {"episode_id": rec["episode_id"], "arm": rec["arm"], "mode": rec["mode"]}
    rows = [dict(base, kind="objection", from_role=o["from"], to_role=o["to"], text=o["objection"], request=o["request"]) for o in rec.get("objections", [])]
    rows += [dict(base, kind="director_note", from_role="DIRECTOR + DP", to_role="shot list", text=n["note"], request=f"beat {n['beat']}") for n in rec.get("director_notes", [])]
    if not rows: rows = [dict(base, kind="status", from_role="", to_role="", text=rec.get("status", ""), request="")]
    return rows

def save(rec, out_dir=None):
    """Sheet tab Table_Read + table_read.json next to the episode. Never raises."""
    safe_append("Table_Read", rows_for_sheet(rec))
    try:
        out_dir = out_dir or os.path.join(WORK, rec["episode_id"]); os.makedirs(out_dir, exist_ok=True)
        p = os.path.join(out_dir, "table_read.json"); json.dump(rec, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False); return p
    except Exception as e:
        log(f"could not write table_read.json: {scrub(e)}", "WARN"); return None

def new_record(episode, arm, mode):
    return {"episode_id": episode, "created": iso(), "arm": arm, "mode": mode, "objections": [], "director_notes": [], "status": "off" if arm == "off" else "pending"}

# ---------------- comparison of the two arms ----------------
def _f(x):
    try: return float(x)
    except Exception: return None

def abtest_report(eps=None, analytics=None):
    """Compare episodes made with and without the table read. Pure function over Sheet rows; returns a dict (and a printable text)."""
    eps = safe_rows("Episodes") if eps is None else eps
    an = {a.get("episode_id"): a for a in (safe_rows("Analytics") if analytics is None else analytics)}
    groups = {"on": [], "off": []}
    for e in eps:
        try: arm = (json.loads(e.get("draw_json") or "{}").get("table_read") or {}).get("arm")
        except Exception: arm = None
        a = an.get(e.get("episode_id"))
        if arm in groups and a and _f(a.get("score")) is not None:
            groups[arm].append({"score": _f(a["score"]), "ret30": _f(a.get("ret30")), "pct": _f(a.get("avg_view_pct")), "cost": _f(e.get("cost_inr"))})
    def mean(xs):
        xs = [x for x in xs if x is not None]; return round(statistics.mean(xs), 4) if xs else None
    rep = {"n": {k: len(v) for k, v in groups.items()}, "mean_score": {k: mean([r["score"] for r in v]) for k, v in groups.items()},
           "mean_retention": {k: mean([r["ret30"] for r in v]) for k, v in groups.items()}, "mean_view_pct": {k: mean([r["pct"] for r in v]) for k, v in groups.items()},
           "mean_cost_inr": {k: mean([r["cost"] for r in v]) for k, v in groups.items()}, "p_value": None}
    if min(rep["n"].values()) < MIN_PER_ARM:
        rep["verdict"] = (f"NOT ENOUGH DATA: need at least {MIN_PER_ARM} analysed episodes per arm (about 10 is better); have on={rep['n']['on']}, off={rep['n']['off']}. "
                          "No conclusion should be drawn yet.")
    else:
        a = [r["score"] for r in groups["on"]]; b = [r["score"] for r in groups["off"]]
        obs = statistics.mean(a) - statistics.mean(b); pool = a + b; rng = random.Random(0); hits = 0; N = 5000
        for _ in range(N):
            rng.shuffle(pool); d = statistics.mean(pool[:len(a)]) - statistics.mean(pool[len(a):])
            if abs(d) >= abs(obs) - 1e-12: hits += 1
        rep["p_value"] = round(hits / N, 3); rep["difference"] = round(obs, 4)
        extra = (rep["mean_cost_inr"]["on"] or 0) - (rep["mean_cost_inr"]["off"] or 0)
        rep["verdict"] = (f"Table read minus no table read: score difference {obs:+.4f} (permutation p = {rep['p_value']}); extra cost about {extra:+.0f} INR per episode. "
                          + ("A difference this small is not distinguishable from chance with so few episodes." if rep["p_value"] >= 0.1 else "The difference is unlikely to be pure chance, but views depend on many other things (topic, title, season)."))
    lines = ["TABLE READ A/B REPORT", f"episodes analysed: on={rep['n']['on']} off={rep['n']['off']}",
             f"mean score: {rep['mean_score']}", f"mean retention: {rep['mean_retention']}", f"mean average view %: {rep['mean_view_pct']}",
             f"mean cost (INR): {rep['mean_cost_inr']}", rep["verdict"]]
    rep["text"] = "\n".join(lines); return rep

def abtest_main():
    rep = abtest_report(); print(rep["text"]); return rep

