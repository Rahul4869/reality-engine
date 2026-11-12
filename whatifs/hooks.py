"""Opening-line candidates per episode: written, validated by code, scored by an independent judge; the best one opens the video. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os, re
from whatifs.core import S, log, iso, scrub, safe_append

MAX_WORDS_EXCL = 10          # a line must have FEWER than this many words
TYPES = ("curiosity_gap", "concrete_stakes", "surprising_claim", "outcome_promise", "you_stakes")      # v9.3: you_stakes = second-person survival stakes
_YOU = re.compile(r"\b(you|your|you're|yourself)\b", re.I)
YOU_MARGIN = 1.5             # v9.3: a 'you' line that passes every check leads unless another line scores more than this much higher
WANT = 10

_TOKEN = re.compile(r"\d[\d,\.]*\d|\d|[A-Za-z]+(?:['\u2019][A-Za-z]+)?")
def tokens(line): return _TOKEN.findall(str(line or ""))
def count_words(line):
    """Conservative count: hyphenated words and slashes count as separate words ('well-known' = 2)."""
    return len(tokens(line))

# "today" is a greeting only where a PRESENTER speaks ("today we", "today I", "today's video"): "Today you lose the rain." is the impossible thing itself -
# a Short's own hook in format S2, and F1's brief ("one law of nature is different today"). v12 V2c-b2b2: any first line that began with "today" held the
# long video about such a Short at the script gate (found by a rehearsal; the Short's seat already knew: shortseat.GREET_RX).
_GREET = re.compile(r"^\W*(?:(?:hey|hi|hello|welcome|today(?:'?s (?:video|episode|case|topic|story|show)|,?\s+(?:we|i|let'?s|let us|i'?m|i'?ll|we'?re|we'?ll))|in this video|let'?s|let us|have you ever|did you know|ever wondered|"
                    r"imagine|picture this|what'?s up|good (?:morning|evening)|before we begin|quick question)\b"
                    r"|(?:so|well|okay|ok|alright|right|listen|look)\s*(?:[,.!:;\u2026]|\.\.\.|$))", re.I)
_HYPE = re.compile(r"\b(secrets?|shocking|shocked|you won'?t believe|mind[- ]?blowing|insane|jaw[- ]?dropping|nobody (knows|talks)|"
                   r"they don'?t want you|banned|exposed|the truth about|scientists (are )?(baffled|stunned)|changes everything|will blow your mind)\b", re.I)
_STOP = set("this that with from have what when they them then than were been will would could should about into your their there which while where "
            "just only even more most much very some such also over under after before every each other these those because being does doing done make made".split())
_NUMW = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,
         "fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,"hundred":100,"thousand":1000,
         "million":10**6,"billion":10**9,"trillion":10**12}

def _content(t): return [w for w in re.findall(r"[a-z]{4,}", str(t).lower()) if w not in _STOP]
def _stem(w): return w[:5]

def _numbers(text):
    """Set of numeric values mentioned as digits or number words."""
    vals = set()
    for tk in tokens(text):
        t = tk.lower().replace(",", "")
        if re.fullmatch(r"\d+(\.\d+)?", t): vals.add(float(t))
        elif t in _NUMW: vals.add(float(_NUMW[t]))
    return vals

def overlap_ratio(line, script):
    cw = _content(line)
    if not cw: return 1.0
    sw = {_stem(w) for w in _content(script)}
    return sum(1 for w in cw if _stem(w) in sw) / len(cw)

def validate_line(line, script):
    """Deterministic checks. Returns a list of issue codes (empty = passes)."""
    issues = []; n = count_words(line)
    if n == 0: return ["empty"]
    if n >= MAX_WORDS_EXCL: issues.append(f"too_long:{n}_words")
    if _GREET.search(line): issues.append("greeting_or_throat_clearing")
    if _HYPE.search(line): issues.append("hype_or_unsupported_phrase")
    try:                                                                       # v9.3: advertiser safety (AD_SAFE_ON): the first line a viewer hears
        from whatifs.packaging import ad_risk
        if ad_risk(line): issues.append("ad_unsafe_word")
    except Exception: pass
    missing = [v for v in _numbers(line) if v not in _numbers(script)]
    if missing: issues.append("number_not_in_script")
    if overlap_ratio(line, script) < 0.4: issues.append("low_overlap_with_script")
    return issues

def _clean_line(x): return re.sub(r"\s+", " ", str(x or "")).strip().strip('"\u201c\u201d')

def _script_text(script):
    """Narration only: tags and BEAT markers removed."""
    return re.sub(r"\[[^\]]+\]|^##.*$", " ", script or "", flags=re.M)

# ---------------- heuristic scores (used only when the judge is unavailable) ----------------
def heuristic_scores(line, script, premise=""):
    n = count_words(line); ov = overlap_ratio(line, script)
    clarity = 10 - max(0, n - 6) * 1.0 - (1.5 if any(len(w) > 9 for w in tokens(line)) else 0)
    rel = min(10, 10 * (0.5 * overlap_ratio(line, script) + 0.5 * overlap_ratio(line, premise or script)) + 1)
    cur = 6 + (1 if re.search(r"\byou|your\b", line, re.I) else 0) + (1 if re.search(r"\d", line) else 0) + (0.5 if line.rstrip().endswith("?") else 0)
    prom = 10 * ov if _numbers(line) <= _numbers(script) else 2
    return {"clarity": round(max(0, clarity), 1), "relevance": round(max(0, rel), 1), "curiosity": round(min(9, cur), 1), "promise_accuracy": round(prom, 1), "unsupported_claim": False}

def combine(sc):
    return round((sc["clarity"] + sc["relevance"] + sc["curiosity"] + sc["promise_accuracy"]) / 4, 2)

# ---------------- generation ----------------
def _generate(script, spine, n, avoid, ask_fn, episode):
    from whatifs import prompts as P
    av = ("Do not repeat or rephrase these rejected lines: " + json.dumps(avoid)) if avoid else ""
    out = ask_fn("hooks", P.fill(P.HOOKS, n=n, script=_script_text(script)[:24000], spine=json.dumps(spine or {}, ensure_ascii=False)[:2500], avoid=av),
                 "Write the opening lines now.", episode=episode, fake_key="hooks", temperature=0.9, max_tokens=3000)
    res = []
    for c in (out.get("candidates") if isinstance(out, dict) else None) or []:
        line = _clean_line(c.get("line"))
        if line: res.append({"line": line, "type": c.get("type") if c.get("type") in TYPES else "unclassified", "basis": str(c.get("basis", ""))[:200]})
    return res

def _judge(script, cands, ask_fn, episode):
    from whatifs import prompts as P
    payload = [{"id": c["id"], "line": c["line"]} for c in cands]
    out = ask_fn("critic", P.fill(P.HOOK_SCORE, script=_script_text(script)[:24000]),
                 "Score them now. CANDIDATES (JSON): " + json.dumps(payload, ensure_ascii=False), episode=episode, fake_key="hook_score", temperature=0.1, max_tokens=3000)
    got = {}
    for s in (out.get("scores") if isinstance(out, dict) else None) or []:
        try:
            got[str(s["id"])] = {"clarity": float(s["clarity"]), "relevance": float(s["relevance"]), "curiosity": float(s["curiosity"]),
                                 "promise_accuracy": float(s["promise_accuracy"]), "unsupported_claim": bool(s.get("unsupported_claim", False)), "note": str(s.get("note", ""))[:160]}
        except Exception: pass
    return got

def build_record(script, spine=None, episode="", ask_fn=None):
    """Generate -> validate -> score -> rank -> choose. Pure of side effects except model calls. Raises only if nothing can be generated."""
    if ask_fn is None:
        from whatifs.models import ask as ask_fn
    premise = (spine or {}).get("premise", "")
    kept, rejected, seen = [], [], set()
    def take(batch):
        for c in batch:
            key = re.sub(r"\W+", " ", c["line"].lower()).strip()
            if key in seen: continue
            seen.add(key); c["issues"] = validate_line(c["line"], _script_text(script)); c["words"] = count_words(c["line"])
            hard = [i for i in c["issues"] if i.startswith(("too_long", "empty", "greeting", "hype", "ad_unsafe"))]
            (rejected if hard else kept).append(c)
    take(_generate(script, spine, WANT, [], ask_fn, episode))
    if len(kept) < WANT:        # one refill for the shortfall
        try: take(_generate(script, spine, WANT - len(kept) + 3, [c["line"] for c in rejected], ask_fn, episode))
        except Exception as e: log(f"hook refill skipped: {scrub(e)}", "WARN", episode)
    kept = kept[:WANT]
    notes = []
    if not kept: raise RuntimeError("no valid hook candidates")
    if len(kept) < WANT: notes.append(f"Only {len(kept)} of {WANT} candidates passed the word-limit / greeting / hype checks.")
    for i, c in enumerate(kept): c["id"] = f"h{i}"
    scored_by = "judge"
    try: judged = _judge(script, kept, ask_fn, episode)
    except Exception as e:
        judged = {}; log(f"hook judge unavailable: {scrub(e)}", "WARN", episode)
    if not judged: scored_by = "heuristic"; notes.append("Independent judge unavailable: scores are heuristic and no hook is applied automatically.")
    for c in kept:
        sc = judged.get(c["id"]) or (heuristic_scores(c["line"], _script_text(script), premise) if scored_by == "heuristic" else None)
        if sc is None:                      # judge skipped this one: do not guess
            sc = dict(heuristic_scores(c["line"], _script_text(script), premise), promise_accuracy=0.0, unsupported_claim=True, note="not scored by judge"); c["issues"].append("not_scored")
        # code evidence overrides model optimism
        if "number_not_in_script" in c["issues"] or "low_overlap_with_script" in c["issues"]: sc["promise_accuracy"] = min(sc["promise_accuracy"], 3.0)
        if sc.get("unsupported_claim"): c["issues"].append("unsupported_claim_flagged")
        c.update({k: sc[k] for k in ("clarity", "relevance", "curiosity", "promise_accuracy")}); c["note"] = sc.get("note", "")
        c["total"] = combine(sc)
        c["valid"] = not c["issues"]
    kept.sort(key=lambda c: -c["total"])
    for r, c in enumerate(kept, 1): c["rank"] = r
    mix = {t: sum(1 for c in kept if c["type"] == t) for t in TYPES}
    if any(v == 0 for v in mix.values()): notes.append("Type mix is uneven: " + json.dumps(mix))
    min_score = S("HOOK_MIN_SCORE", float)
    eligible = [c for c in kept if c["valid"] and c["promise_accuracy"] >= 7 and c["total"] >= min_score] if scored_by == "judge" else []
    chosen = eligible[0] if eligible else None
    if chosen and S("COLD_OPEN_YOU_ON", bool):                                 # v9.3: YOU before lore - a passing second-person line leads when it is close in score
        you = next((c for c in eligible if _YOU.search(c["line"])), None)
        if you and you["total"] >= chosen["total"] - YOU_MARGIN: chosen = you
    if not chosen: notes.append("No candidate passed every check; a person should pick one or keep the writer's opening.")
    return {"episode_id": episode, "created": iso(), "scored_by": scored_by, "mode": S("HOOK_APPLY_MODE").lower(), "min_score": min_score,
            "candidates": kept, "rejected": rejected, "type_mix": mix, "chosen_id": chosen["id"] if chosen else None,
            "status": "pending", "applied": False, "notes": notes}

# ---------------- applying ----------------
def apply_to_script(script, line):
    """Insert the hook as the first spoken line (after '## BEAT 1' if present). Insert-only: no writer text is removed.
    Returns (new_script, applied, reason)."""
    if not script or not line: return script, False, "empty"
    lines = script.split("\n"); idx = None
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith("##"): continue
        idx = i; break
    if idx is None: return script, False, "no spoken line found"
    first = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", lines[idx].strip())
    if overlap_ratio(line, first) >= 0.8 and overlap_ratio(first, line) >= 0.8: return script, False, "writer's opening already says this"
    try:
        from whatifs import format_engine as _FE
        label = "[DIRECTOR] " if _FE.mode() != "classic" else ""      # v8.3: the hook is spoken by the Director (an unlabelled first line used to fall to a third voice)
    except Exception: label = ""
    lines.insert(idx, f"{label}[tension] {line}")
    return "\n".join(lines), True, "inserted as first line"

def decide(rec, script):
    """Fill rec['status'] and return the (possibly changed) script."""
    ch = next((c for c in rec["candidates"] if c["id"] == rec.get("chosen_id")), None)
    if not ch: rec["status"] = "needs_human_choice"; return script
    if rec["mode"] != "auto": rec["status"] = "needs_human_choice"; rec["notes"].append("HOOK_APPLY_MODE = suggest: recommended line recorded, not applied."); return script
    new, ok, why = apply_to_script(script, ch["line"])
    rec["applied"] = ok; rec["status"] = "applied" if ok else "needs_human_choice"; rec["apply_note"] = why
    if not ok: rec["notes"].append("Not applied: " + why)
    return new

def verify_in_narration(rec, units):
    """After narration: confirm the applied hook is really the first spoken unit (a later rewrite may have changed it)."""
    if not rec or not rec.get("applied") or not units: return True
    ch = next((c for c in rec["candidates"] if c["id"] == rec["chosen_id"]), None)
    norm = lambda s: re.sub(r"\W+", "", str(s).lower())
    spoken = "".join(norm(u.get("text", "")) for u in units[:3])          # a hook with two short sentences becomes two units
    want = norm(ch["line"]) if ch else ""
    ok = bool(want) and spoken.startswith(want[:30])
    if not ok:
        rec["notes"].append("After narration the first spoken line differs from the chosen hook (a rewrite changed it). Please review."); rec["status"] = "needs_human_choice"
        try:          # v8.9.1 (fix): the Hook_Candidates tab said applied=TRUE for a line that is no longer the opening; the row is corrected too
            from whatifs.core import store
            store().update_where("Hook_Candidates", {"episode_id": rec.get("episode_id", ""), "applied": "TRUE"}, {"applied": "FALSE", "issues": "replaced by a later rewrite"})
        except Exception: pass
    return ok

# ---------------- storage ----------------
def rows_for_sheet(rec):
    out = []
    for c in rec["candidates"]:
        out.append({"episode_id": rec["episode_id"], "rank": c["rank"], "line": c["line"], "words": c["words"], "type": c["type"], "clarity": c["clarity"], "relevance": c["relevance"],
                    "curiosity": c["curiosity"], "promise_accuracy": c["promise_accuracy"], "total": c["total"], "valid": "TRUE" if c["valid"] else "FALSE",
                    "issues": ",".join(c["issues"]), "chosen": "TRUE" if c["id"] == rec.get("chosen_id") else "", "applied": "TRUE" if (rec.get("applied") and c["id"] == rec.get("chosen_id")) else ""})
    for c in rec["rejected"]:
        out.append({"episode_id": rec["episode_id"], "rank": "", "line": c["line"], "words": c["words"], "type": c["type"], "clarity": "", "relevance": "", "curiosity": "", "promise_accuracy": "",
                    "total": "", "valid": "FALSE", "issues": ",".join(c["issues"]), "chosen": "", "applied": ""})
    return out

def save(rec, out_dir):
    safe_append("Hook_Candidates", rows_for_sheet(rec)); p = os.path.join(out_dir, "hooks.json")
    try: os.makedirs(out_dir, exist_ok=True); json.dump(rec, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except Exception as e: log(f"could not write hooks.json: {scrub(e)}", "WARN"); return None
    return p

def proven_record(script, proven, episode=""):
    """v12 V2c-b2b: the record of an opening line that needs no lab - the first sentence of the Short this long video is about, the line real
    viewers stayed for. No candidate is written and no judge is asked (real viewers outrank a jury); the one rule that still binds is advertiser
    safety, as for anything a viewer hears first. Returns None when there is no such line or it is not ad-safe (then the lab runs as usual)."""
    line = _clean_line((proven or {}).get("line")); sid = str((proven or {}).get("short") or "")
    if not line or not sid: return None
    try:
        from whatifs.packaging import ad_risk
        if ad_risk(line): log(f"the hook of Short {sid} is not advertiser-safe as a long video's first line: the hook lab runs instead", "WARN", episode); return None
    except Exception: pass
    c = {"id": "h0", "line": line, "type": "proven", "basis": f"the first sentence of Short {sid}", "issues": [], "words": count_words(line), "clarity": "", "relevance": "",
         "curiosity": "", "promise_accuracy": "", "total": "", "valid": True, "rank": 1, "note": "proven by the viewers of the Short"}
    return {"episode_id": episode, "created": iso(), "scored_by": "viewers", "source": "short", "short": sid, "mode": S("HOOK_APPLY_MODE").lower(), "min_score": S("HOOK_MIN_SCORE", float),
            "candidates": [c], "rejected": [], "type_mix": {}, "chosen_id": "h0", "status": "pending", "applied": False,
            "notes": [f"The opening line is the hook of Short {sid}, word for word: no hook lab was run."]}

def run_hooks(script, spine, episode, out_dir, ask_fn=None, proven=None):
    """Stage entry point for episode.py. Returns (script, record|None). NEVER raises; on any failure the script is returned unchanged.
    proven = {line, short}: the hook of the Short a long video is about (whatifs/opening.py) - used as the first line instead of the lab."""
    if not S("HOOKS_ON", bool): return script, None
    try:
        rec = proven_record(script, proven, episode) if proven else None
        if rec:
            script = decide(rec, script)
            if not rec["applied"] and rec.get("apply_note") == "writer's opening already says this":      # the writer opened on the Short's own words: that IS the proven line in place
                rec["applied"] = True; rec["status"] = "applied"
            save(rec, out_dir)
            log(f"opening line: the hook of Short {rec['short']}, proven by its viewers (status {rec['status']}; no hook lab)", episode=episode)
            return script, rec
    except Exception as e: log(f"the Short's hook could not be used ({scrub(e)[:120]}): the hook lab runs", "WARN", episode)
    try:
        rec = build_record(script, spine, episode, ask_fn)
        script = decide(rec, script); save(rec, out_dir)
        log(f"opening hooks: {len(rec['candidates'])} candidates, {len(rec['rejected'])} rejected, status {rec['status']}, scored by {rec['scored_by']}", episode=episode)
        return script, rec
    except Exception as e:
        log(f"opening hooks skipped (script unchanged): {scrub(e)}", "WARN", episode)
        rec = {"episode_id": episode, "created": iso(), "status": "failed", "applied": False, "candidates": [], "rejected": [], "notes": ["hook stage failed: " + scrub(str(e))[:160]]}
        try: os.makedirs(out_dir, exist_ok=True); json.dump(rec, open(os.path.join(out_dir, "hooks.json"), "w"), indent=1)
        except Exception: pass
        return script, rec

