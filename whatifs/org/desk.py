"""The owner's desk: what he types in tab Owner_Input is kept word for word, judged by code and answered in the next brief. See docs/CURRENT/SYSTEM.md."""
# v12 V4 (redesign 4.9, until B9; D0 wraps it and stays pending): the tick stores his input on tab Owner_Desk, files an owner memo (D0 -> D1) and closes it at once
# with the verdict BY CODE - ADOPTED only where code can recognise the whole input as a request (three patterns), PARKED otherwise.
from __future__ import annotations
import hashlib, json, re
from whatifs.core import S, log, store, iso, now_utc, scrub

IN, DESK = "Owner_Input", "Owner_Desk"
HEAD = r"^\s*(?:please\s+)?(?:(?:make|do|post|set|give me|i want|we want|go to)\s+)?"
TAIL = r"\s*[.!]?\s*$"
PATTERNS = ((re.compile(HEAD + r"(\d{1,2})\s+shorts?\s+(?:a|per|every)\s+month" + TAIL), "SHORTS_PER_MONTH"),
            (re.compile(HEAD + r"(\d)\s+shorts?\s+(?:a|per|every)\s+week" + TAIL), "SHORTS_PER_WEEK"),
            (re.compile(HEAD + r"(\d)\s+(?:long\s+)?videos?\s+(?:a|per|every)\s+month" + TAIL), "STANDARD_MAX_LONG_PER_MONTH"))
FIRST = " Ideas go in the tab Owner_Input; your verdict on a video goes in Owner_Verdicts."

def on(): return S("STRATEGY_ON", bool)

def recognise(text):
    """(key, value) when the WHOLE input is one of the three requests (a question, a refusal or a remark is weighed, never executed: item 18), else None."""
    t = str(text or "").strip().lower()
    for rx, key in PATTERNS:
        m = rx.search(t)                                                         # HEAD's ^ and TAIL's $ hold the WHOLE input
        if m: return key, int(m.group(1))
    return None

def _sha(text): return hashlib.sha1(str(text).encode("utf-8")).hexdigest()

def _rows(st=None): return (st or store()).rows(DESK)

def verdict(key, value, now=None, force=False):
    """('ADOPTED', how, step value) or ('PARKED', why, None) through RANGE, EFFECT and FIT (his own word overrides FIT only - never RANGE or EFFECT)."""
    from whatifs.org import levers as LV, strategy as STR
    sp = LV.LEVERS.get(key) or {}; old = STR._cell(key)
    if not sp.get("lo", 0) <= value <= sp.get("hi", 10 ** 6):
        return "PARKED", f"{key} = {value} is outside what Strategy may set ({sp.get('lo')} to {sp.get('hi')}); a value inside that range would be adopted", None
    new = STR._step(key, old, value)
    e0, e1 = STR.effect(key, old, now), STR.effect(key, new, now)
    if e0 == e1: return "PARKED", f"{key} {old} -> {new} changes nothing the code does this month ({e0}); it would when the calendar or the money changes", None
    n0, n1 = STR._plan_need(key, old, now), STR._plan_need(key, new, now)
    if not force and n0 is not None and n1["need_inr"] > n0["need_inr"] and not n1["fits"]:
        return "PARKED", f"the month would need Rs {n1['need_inr']:.0f} and has Rs {n1['room_inr']:.0f} for production; a higher cap or a cheaper clip model would change it - or tap Do it anyway", "FIT"
    rest = "" if str(new) == str(value) else f"; the rest after it is verified ({key} {new} -> {value})"
    return "ADOPTED", f"{key} {old} -> {new} as a ticket now{rest}", new

def _ticket(n, key, new, old, now, dedupe):
    from whatifs.org import memos as MEM, strategy as STR
    m = STR._ticket(key, new, old, f"DESK-{n}", dedupe, now, words=f"the owner's input {n}: {key} {old} -> {new}")
    return MEM.write(m, now=now)

def _memo(n, text, interp, now, link=""):
    from whatifs.org import memos as MEM
    m = {"type": "owner_memo", "from_dept": "D0", "to_depts": ["D1"], "subject": f"Owner input {n} (tab Owner_Input)",
         "body": {"verbatim": str(text)[:4000], "interpretation": interp[:800], "channel": "Owner_Input", "received": iso(now)},
         "dedupe_key": f"desk|memo|{n}" + (f"|{link}" if link else ""), "done_when": "the desk's verdict is written on tab Owner_Desk and reaches him in the next brief"}
    if link: m["links"] = {"first": link}
    return MEM.write(m, now=now)

def _close(mid, n, now):
    from whatifs.org import memos as MEM
    MEM.resolve(mid, "D1", "desk_answered", f"Owner_Desk:{n}", "answered on the owner's desk", now=now)

def tick(now=None):
    """Every new input (its sha1 not on Owner_Desk) is stored, filed and answered in the same tick. Returns the rows written."""
    from whatifs.org import execute as EX
    if not on(): return []
    st = store(); now = now or now_utc(); seen = {r.get("sha") for r in _rows(st)}; out = []
    for r in st.rows(IN):
        text = str(r.get("input") or "")
        if not text.strip() or _sha(text) in seen: continue
        n = len(_rows(st)) + 1; seen.add(_sha(text)); rec = recognise(text)
        row = {"n": n, "ts": iso(now), "sha": _sha(text), "verbatim": text[:4000], "verdict": "", "how": "", "memo": "", "ticket": "", "action": "", "briefed": ""}
        if not EX.on():
            row.update(verdict="STORED", how="stored word for word; the organisation is switched off, so nothing was filed"); st.append(DESK, [row]); out.append(row); continue
        interp = ((f"recognised as: {rec[0]} = {rec[1]}" if rec else "not a request code can recognise")
                  + (" (the input is longer than 4,000 characters: the tab Owner_Input holds all of it)" if len(text) > 4000 else ""))
        try: m = _memo(n, text, interp, now)
        except Exception as e:
            row.update(verdict="STORED", how=f"Your input {n} is stored on the tab; it could not be filed ({scrub(e)[:200]})"); st.append(DESK, [row]); out.append(row); continue
        row["memo"] = m["id"]
        if rec:
            v, how, new = verdict(rec[0], rec[1], now)
            if v == "ADOPTED":
                from whatifs.org import strategy as STR
                try: t = _ticket(n, rec[0], new, STR._cell(rec[0]), now, f"desk|{n}"); row["ticket"] = t["id"]
                except Exception as e: v, how = "PARKED", f"the ticket could not be written ({scrub(e)[:160]})"
            row.update(verdict=v, how=how)
            if v == "PARKED" and new == "FIT":
                from whatifs import notify as NT
                row["action"] = NT.send("desk", f"Your input {n}: {how}.", [("Do it anyway", f"DESK DO {n}")], tier="week", default="it stays parked", dedupe_key=f"desk|{n}")
        else:
            row.update(verdict="PARKED", how=f"stored word for word as input {n}; no rule of Strategy can act on it; the Council reads it when it exists (B6b)")
        st.append(DESK, [row]); out.append(row)
        try: _close(m["id"], n, now)
        except Exception as e: log(f"desk: the owner memo of input {n} was not closed: {scrub(e)[:160]}", "WARN")
    _next_steps(st, now)
    return out

def _next_steps(st, now):
    """An ADOPTED request further than one step: the next step once the last ticket is verified."""
    from whatifs.org import memos as MEM, strategy as STR
    for r in _rows(st):
        if r.get("verdict") != "ADOPTED" or not r.get("ticket"): continue
        rec = recognise(r.get("verbatim")); t = MEM.get(r["ticket"], st)
        if not rec or t is None or t["status"] != "resolved" or (t.get("resolution") or {}).get("kind") != "lever_verified": continue
        key, value = rec; cur = STR._cell(key)
        if str(cur) == str(value): continue
        new = STR._step(key, cur, value)
        try: nt = _ticket(r["n"], key, new, cur, now, f"desk|{r['n']}|{new}"); st.update(DESK, "n", r["n"], {"ticket": nt["id"]})
        except Exception as e: log(f"desk: the next step of input {r['n']} was not written: {scrub(e)[:120]}", "WARN")

def lines(now=None, st=None):
    """The brief's answers: every desk row not yet briefed. The first answer ever ends with where ideas and verdicts go."""
    from whatifs import notify as NT
    st = st or store(); now = now or now_utc(); rows = _rows(st); first = not any(r.get("briefed") for r in rows); out = []
    for r in rows:
        if r.get("briefed") or str(r.get("ts") or "") > iso(now): continue
        txt = str(r.get("verbatim") or "").replace("\n", " ")
        line = f"Your input {r['n']} (\"{txt[:80]}\"): {r.get('verdict')} - {r.get('how')}."
        a = next((x for x in st.rows("Owner_Actions") if x.get("id") == r.get("action")), None) if r.get("action") else None
        if a: line += " Do it anyway: " + NT.link(f"DESK DO {r['n']}", a["id"])
        out.append(line)
    if out and first: out[-1] += FIRST
    return out

def briefed(now=None, st=None):
    st = st or store(); now = now or now_utc(); n = 0
    for r in _rows(st):
        if r.get("briefed") or str(r.get("ts") or "") > iso(now): continue
        st.update(DESK, "n", r["n"], {"briefed": iso(now)}); n += 1
    return n

def _do(row, choice):
    """'Do it anyway': his own word overrides FIT (the cadence's split still never spends what the month does not have) - never RANGE or EFFECT."""
    parts = str(choice or "").split(); n = parts[2] if len(parts) >= 3 else ""
    st = store(); now = now_utc(); r = next((x for x in _rows(st) if str(x.get("n")) == n), None)
    if r is None: return f"no input {n}"
    rec = recognise(r.get("verbatim"))
    if not rec: return "nothing to do: that input is not a request code can act on"
    v, how, new = verdict(rec[0], rec[1], now, force=True)
    if v != "ADOPTED": return f"not done: {how}"
    from whatifs.org import strategy as STR
    t = _ticket(n, rec[0], new, STR._cell(rec[0]), now, f"desk|{n}|anyway")
    m = _memo(n, r.get("verbatim"), f"recognised as: {rec[0]} = {rec[1]} - his own word overrides the money's fit (Do it anyway)", now, link=r.get("memo") or "")
    try: _close(m["id"], n, now)
    except Exception as e: log(f"desk: the second owner memo of input {n} was not closed: {scrub(e)[:120]}", "WARN")
    st.update(DESK, "n", r["n"], {"verdict": "ADOPTED", "how": f"{how} (your own word overrode the money's fit)", "ticket": t["id"]})
    return f"done: {how}"

def register():
    from whatifs import notify as NT
    NT.register("desk", on_answer=_do)
