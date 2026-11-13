"""Real footage (Visual Production, D6): free NASA and Pexels footage as a short 'reality anchor' of a long video - placed by code under its rules, kept with a record of where it came from, changed by the renderer and credited in the description. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, re, subprocess
from whatifs.core import S, log

# What code can RECOGNISE as a person in a clip's own title (neither library has a field for it: Pexels' search takes no such filter, NASA's answer has none).
# A clip whose title, key words or page address carries one of these words is not taken. A person nobody named is not recognised: see the record's `people`.
PEOPLE_RX = re.compile(r"\b(man|men|woman|women|person|persons|people|human|humans|boy|boys|girl|girls|child|children|kid|kids|baby|babies|face|faces|portrait|portraits|selfie|"
                       r"crowd|crowds|couple|family|families|worker|workers|model|models|student|students|doctor|nurse|astronaut|astronauts|cosmonaut|cosmonauts|crew|crews|"
                       r"crewmember|crewmembers|spacewalker|scientist|scientists|engineer|engineers|technician|technicians|pilot|pilots|interview|interviews|speech|"
                       r"president|senator|administrator|director|commander|mr|mrs|ms|dr)\b", re.I)
MERGE_S = 1.0          # a line of real footage may run this much longer than STOCK_MAX_S on the film (a sub-second line after it has no picture of its own)

def on(): return S("STOCK_ON", bool)

def names_person(text):
    """Does a clip's own title, key words or page address NAME a person (the only way code can recognise one)?"""
    return bool(PEOPLE_RX.search(re.sub(r"[-_/+.]+", " ", str(text or ""))))

# ------------------------------------------------------------------ the plan: where real footage may stand (pure, before any money)
def shape(shots, units, total):
    """THE STOCK RULES ON THE SHOT LIST (pure; nothing is paid or fetched): a shot of real footage stays only where it is a 'reality anchor' - never the
    first picture, never right after another one, on a line of STOCK_MIN_S to STOCK_MAX_S seconds, and all of them together at most STOCK_SHARE_MAX_PCT
    of the runtime (the earliest stay). Every other one becomes a picture of our own (its prompt, or the line itself). With STOCK_ON off none stays.
    A shot that stays carries `stock_s`, the seconds of its line."""
    from whatifs import motion as MOT
    out = [dict(s) for s in shots]; n = min(len(out), len(units or []))
    idx = [i for i in range(n) if out[i].get("type") == "stock"]
    if not idx: return out
    sp = MOT.lines_of(units, total); lo, hi = S("STOCK_MIN_S", float), S("STOCK_MAX_S", float); room = S("STOCK_SHARE_MAX_PCT", float) / 100.0 * float(total); used = 0.0; why = {}
    def back(i, reason):
        out[i]["type"] = "still"; out[i]["prompt"] = out[i].get("prompt") or str(units[i].get("text") or ""); out[i].pop("search", None); out[i].pop("stock_s", None)
        why[reason] = why.get(reason, 0) + 1
    for i in idx:
        d = sp[i][1] - sp[i][0]
        if not on(): back(i, "real footage is switched off")
        elif i == 0 or sp[i][0] <= 1e-6: back(i, "never the first picture")
        elif out[i - 1].get("type") == "stock": back(i, "never two in a row")
        elif d < lo - 1e-6 or d > hi + 1e-6: back(i, f"only on a line of {lo:g} to {hi:g} seconds")
        elif used + d > room + 1e-6: back(i, f"{S('STOCK_SHARE_MAX_PCT', float):g}% of the film at most")
        else: used += d; out[i]["stock_s"] = round(d, 2)
    if why: log("stock rules: " + "; ".join(f"{c} shot(s) of real footage became pictures of our own ({r})" for r, c in sorted(why.items())) + f"; {sum(1 for s in out[:n] if s.get('type') == 'stock')} stay for {used:.1f} s")
    return out

# ------------------------------------------------------------------ the record: where a clip came from
def seconds(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip() or 0)
    except Exception: return 0.0

def write_record(path, rec):
    """The record of one clip of real footage, kept beside its file: {provider, id, title, page, maker, credit, people}."""
    with open(str(path) + ".json", "w", encoding="utf-8") as f: json.dump(rec, f, ensure_ascii=False)
    return rec

def record_of(path):
    try:
        with open(str(path) + ".json", encoding="utf-8") as f: r = json.load(f)
        return r if isinstance(r, dict) else {}
    except (OSError, ValueError): return {}

def record_issues(rec):
    """Why a record cannot stand ([] = it can): it names where the clip came from and how it is credited, and its title names no person."""
    r = rec if isinstance(rec, dict) else {}; p = []
    if not str(r.get("provider") or "").strip() or not str(r.get("id") or "").strip(): p.append("no source on record")
    if not str(r.get("credit") or "").strip(): p.append("no credit on record")
    if r.get("people") or names_person(f"{r.get('title') or ''} {r.get('page') or ''}"): p.append(f"its title names a person ('{str(r.get('title') or r.get('page') or '')[:50]}')")
    return p

def credits(records):
    """The credit lines of a description, built by code from the records of the footage the film really shows ('' = it shows none). NASA asks to be
    acknowledged as the source; Pexels' API asks for a prominent link and, where possible, the maker's name."""
    recs = [r for r in records or [] if isinstance(r, dict) and r.get("credit")]
    if not recs: return ""
    out = []
    if any(r.get("provider") == "nasa" for r in recs): out.append("NASA")
    makers = list(dict.fromkeys(str(r.get("maker") or "").strip() for r in recs if r.get("provider") == "pexels" and str(r.get("maker") or "").strip()))
    if any(r.get("provider") == "pexels" for r in recs): out.append("Pexels (https://www.pexels.com)" + (" - videos by " + ", ".join(makers[:6]) if makers else ""))
    other = list(dict.fromkeys(str(r["credit"]) for r in recs if r.get("provider") not in ("nasa", "pexels")))
    return "Real footage: " + "; ".join(out + other) + "."

def credit_names(rec):
    """What the description must carry for this record."""
    p = str((rec or {}).get("provider") or "")
    return ["NASA"] if p == "nasa" else (["Pexels"] + ([str(rec["maker"]).strip()] if str(rec.get("maker") or "").strip() else [])) if p == "pexels" else [str((rec or {}).get("credit") or "")]

# ------------------------------------------------------------------ the finished film: what the render really showed
def report(shots, spans, records, description, duration):
    """THE STOCK RULES ON THE FINISHED FILM. `spans` = [(start, end, shot)] - the stretches in which the renderer played real footage, as it recorded
    them. Returns {n, seconds, share_pct, limit_pct, problems}: at most STOCK_SHARE_MAX_PCT of the runtime; never the first picture; never two in a
    row; no stretch longer than STOCK_MAX_S (+ MERGE_S); every clip has a record that names its source and its credit and no person; every credit
    stands in the description."""
    spans = sorted(spans or []); total = sum(float(b) - float(a) for a, b, _ in spans); lim = S("STOCK_SHARE_MAX_PCT", float); hi = S("STOCK_MAX_S", float); p = []
    share = 100.0 * total / max(0.1, float(duration or 0))
    if not on() and spans: p.append(f"real footage is switched off (STOCK_ON) and the film shows {len(spans)} clip(s) of it")
    if share > lim + 1e-6: p.append(f"{total:.1f} s of real footage = {share:.1f}% of the film (limit {lim:g}%)")
    if spans and float(spans[0][0]) <= 0.05: p.append("the film OPENS on real footage (never the first picture)")
    idx = [int(i) for _a, _b, i in spans]
    if any(j - i == 1 for i, j in zip(idx, idx[1:])): p.append("two shots of real footage in a row")
    long_ = [f"{float(b) - float(a):.1f} s at {float(a):.0f} s" for a, b, _ in spans if float(b) - float(a) > hi + MERGE_S + 1e-6]
    if long_: p.append(f"real footage held longer than an anchor ({hi:g} s): " + ", ".join(long_[:3]))
    desc = str(description or "").lower()
    for _a, _b, i in spans:
        rec = (records or {}).get(i) or (records or {}).get(str(i)) or {}
        bad = record_issues(rec)
        if bad: p.append(f"the footage of shot {i}: " + "; ".join(bad)); continue
        miss = [c for c in credit_names(rec) if c and c.lower() not in desc]
        if miss: p.append(f"the description does not credit {', '.join(miss)} (shot {i})")
    return {"n": len(spans), "seconds": round(total, 1), "share_pct": round(share, 1), "limit_pct": lim, "problems": list(dict.fromkeys(p))[:6],
            "credits": sorted({c for _a, _b, i in spans for c in credit_names((records or {}).get(i) or (records or {}).get(str(i)) or {}) if c})}
