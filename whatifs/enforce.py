"""Hard enforcement of the researched breakout rules: writer instruction, one automatic fix, then the Feature Contract check. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, math, re, subprocess
import numpy as np
from whatifs.core import S, log, store, iso, FAKE, scrub

PUNCH_RE = re.compile(r"\[\s*PUNCH\s*\]", re.I)
SEND_RE = re.compile(r"\[\s*SEND\s*\]", re.I)
AWE_RE = re.compile(r"\[\s*AWE\s*\]", re.I)

def writer_rules(fmt="long"):
    from whatifs import formats as FMT
    if FMT.rule("joke_density") != "must" and FMT.rule("send_and_awe") != "must":        # v12 V2a: a format whose devices are optional does not demand them
        return ("MARKERS (optional in this format; never spoken): start a line with [PUNCH] only where a real laugh line is - never add a joke to fill a "
                "gap. You may mark the one moment a viewer would send to a friend with [SEND] and the biggest reveal with [AWE].")
    sec = S("JOKE_EVERY_SEC_LONG" if fmt == "long" else "JOKE_EVERY_SEC_SHORT", float)
    return (f"MANDATORY MARKERS (code checks them; a missing one sends the script back): start every punchline line with [PUNCH] - at least one "
            f"punchline every {sec:.0f} seconds of narration, spread evenly, each one a real laugh line (surprise, the punch word last). Mark the one moment "
            "a viewer would send to a friend ('that is SO you') with [SEND], and the biggest awe/wow reveal with [AWE] (not in the last 20%). Markers are "
            "never spoken.")

# ---------------------------------------------------------------- brain -> writer (proven / promising / retired, from the channel's own data)
def brain_block(fmt="long"):
    try:
        from whatifs import brain as BR
        v = BR.verdicts()
    except Exception:
        return ""
    def fmt_rows(rows): return ", ".join(f"{r.get('family')}={r.get('level')} (P={float(r.get('p_beats_baseline') or 0):.2f}, {r.get('n_videos')} videos)"
                                          for r in rows if r.get("format") in (fmt, "both", "", None))[:600]
    pro, prom, ret = fmt_rows(v.get("proven") or []), fmt_rows(v.get("promising") or []), fmt_rows(v.get("retired") or [])
    if not (pro or prom or ret): return ""
    return ("THIS CHANNEL'S OWN EVIDENCE (learning core; follow it): " + (f"PROVEN - use: {pro}. " if pro else "") +
            (f"PROMISING - use where it fits: {prom}. " if prom else "") + (f"RETIRED - never use: {ret}." if ret else ""))

def retired_levels():
    try:
        from whatifs import brain as BR
        return {(r.get("family"), r.get("level")) for r in (BR.verdicts().get("retired") or [])}
    except Exception: return set()

# ---------------------------------------------------------------- idea evidence (idea-first: outliers >= IDEA_MIN_MULTIPLE in comparable channels)
def premise_evidence(row):
    """Best outlier multiple behind a bench premise (demand_json / src); 0 when none."""
    best = 0.0
    try:
        dj = json.loads(row.get("demand_json") or "{}")
        for k in ("multiple", "best_multiple", "outlier_multiple"):
            if k in dj: best = max(best, float(dj[k] or 0))
        for it in (dj.get("signals") or dj.get("videos") or []): best = max(best, float(it.get("multiple") or 0))
        sv = dj.get("source_video_id") or row.get("src_video_id")
        if sv:
            for r in store().rows("Demand_Signals"):
                if r.get("video_id") == sv: best = max(best, float(r.get("multiple") or 0))
    except Exception: pass
    return best

def demand_data_exists():
    return len([r for r in store().rows("Demand_Signals") if r.get("multiple")]) >= S("IDEA_MIN_SIGNALS", int)

# ---------------------------------------------------------------- script measures
def script_seconds(text):
    words = len(re.sub(r"\[[^\]]*\]", " ", text).split())
    return words / max(1.0, S("WPM_ESTIMATE", float)) * 60.0

def punch_lines(text): return [l for l in text.split("\n") if PUNCH_RE.search(l)]

def joke_need(text, fmt="long"):
    return max(1, int(math.floor(script_seconds(text) / S("JOKE_EVERY_SEC_LONG" if fmt == "long" else "JOKE_EVERY_SEC_SHORT", float))))

def biggest_gap_lines(text):
    """Largest stretch (in seconds of narration) without a [PUNCH] line."""
    wpm = max(1.0, S("WPM_ESTIMATE", float)); t = 0.0; last = 0.0; worst = 0.0
    for l in text.split("\n"):
        if PUNCH_RE.search(l): worst = max(worst, t - last); last = t
        t += len(re.sub(r"\[[^\]]*\]", " ", l).split()) / wpm * 60.0
    return max(worst, t - last)

def fix_markers(script, wbrief, episode, fmt="long"):
    """ONE targeted rewrite when punchline density or the [SEND]/[AWE] markers fall short (before the contract checks them)."""
    from whatifs import formats as FMT
    if FMT.rule("joke_density") != "must" and FMT.rule("send_and_awe") != "must": return script, []      # v12 V2a: optional devices are never forced by a rewrite
    text = script.get("script", ""); need = joke_need(text, fmt); have = len(punch_lines(text))
    miss = []
    if have < need or biggest_gap_lines(text) > 2.2 * S("JOKE_EVERY_SEC_LONG" if fmt == "long" else "JOKE_EVERY_SEC_SHORT", float):
        miss.append(f"add punchlines so there are at least {need} [PUNCH] lines, never more than {int(2 * S('JOKE_EVERY_SEC_LONG', float))} s apart "
                    f"(now {have}; biggest gap {biggest_gap_lines(text):.0f} s)")
    if not SEND_RE.search(text): miss.append("mark one [SEND] moment")
    if not AWE_RE.search(text): miss.append("mark the [AWE] reveal (not in the last 20%)")
    if not miss: return script, []
    from whatifs.models import ask
    rev = ask("rewrite", wbrief, "MARKER FIX (keep every other line, label, tag and fact exactly; only add or sharpen lines): " + "; ".join(miss) +
              "\nNARRATION:\n" + text + "\nRewrite the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
    if str(rev.get("script", "")).strip(): script = rev
    log(f"enforce: marker fix ({'; '.join(miss)[:160]})", episode=episode)
    return script, miss

# ---------------------------------------------------------------- final-stage validators (Impact Map V1/V3/V4/V6/V8/V9/V10)
def v1_hook(units):
    """A question or a 'you' stake is spoken within the first IMPACT_HOOK_SEC seconds."""
    early = " ".join(str(u.get("text", "")) for u in units if float(u.get("start", 0) or 0) <= S("IMPACT_HOOK_SEC", float))
    return bool(re.search(r"\?|\byou(r)?\b", early, re.I)), early[:120]

def v6_punch_timing(units):
    """Every punchline unit starts after a real pause (>= PUNCH_PAUSE_MIN_S) - measured on the narration timeline."""
    bad, n = [], 0
    for a, b in zip(units[:-1], units[1:]):
        if b.get("punch"):
            n += 1; gap = float(b.get("start", 0) or 0) - float(a.get("end", a.get("start", 0)) or 0)
            if gap < S("PUNCH_PAUSE_MIN_S", float) - 0.02: bad.append(round(gap, 2))
    return n, bad

def v8_sfx(design):
    """No sound-event kind repeats within 6 s; identical files never repeat (variants are generated per use)."""
    last, bad = {}, []
    for kind, t in sorted(((k, float(t)) for k, t in (design or {}).get("foley", [])), key=lambda x: x[1]):
        if kind in last and t - last[kind] < 6.0: bad.append((kind, round(t, 1)))
        last[kind] = t
    return bad

def signature(units, total):
    """Ordered event pattern at 10-second resolution: punch / question / exhibit / voice change. Fine enough that only a genuine near-copy of a
    recent episode scores above IMPACT_VARIETY_MAX (every episode shares the same rhythm rules, so a coarse histogram would flag them all)."""
    mins = max(1, int(math.ceil(total / 10.0))); v = np.zeros((mins, 4), np.float32); prev = None
    for u in units:
        m = min(mins - 1, int(float(u.get("start", 0) or 0) // 10)); txt = str(u.get("text", ""))
        if u.get("punch"): v[m, 0] += 1
        if "?" in txt: v[m, 1] += 1
        if re.search(r"exhibit", txt, re.I): v[m, 2] += 1
        if u.get("speaker") and u.get("speaker") != prev: v[m, 3] += 1
        prev = u.get("speaker")
    return v.flatten().tolist()

def v9_variety(sig, episode):
    rows = [r for r in store().rows("Impact_Maps") if r.get("episode_id") != episode][-10:]
    worst = 0.0
    for r in rows:
        try: o = np.array(json.loads(r["signature"]), np.float32)
        except Exception: continue
        a = np.array(sig, np.float32); n = min(len(a), len(o))
        if n == 0 or not a[:n].any() or not o[:n].any(): continue
        worst = max(worst, float(np.dot(a[:n], o[:n]) / (np.linalg.norm(a[:n]) * np.linalg.norm(o[:n]))))
    return worst

def v10_flash(path):
    """Max luminance flips per second (10 fps, 64 px; a flip = mean-luma jump > 20% of range, direction alternating)."""
    if FAKE or not path: return 0.0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=10,scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True, timeout=1800).stdout
    n = len(raw) // (64 * 36)
    if n < 3: return 0.0
    luma = np.frombuffer(raw[:n * 64 * 36], np.uint8).reshape(n, -1).mean(1)
    d = np.diff(luma); flips = (np.abs(d) > 51) & (np.sign(d) != np.sign(np.roll(d, 1)))
    per_s = [int(flips[i:i + 10].sum()) for i in range(0, len(flips), 10)]
    return float(max(per_s or [0]))

def record_map(episode, sig, extra):
    try: store().append("Impact_Maps", [{"ts": iso(), "episode_id": episode, "signature": json.dumps(sig), "summary": json.dumps(extra)[:4000]}])
    except Exception as e: log(f"impact map not recorded: {scrub(e)}", "WARN", episode)

def fix_retention(script, wbrief, spine, episode):
    """ONE targeted rewrite after the last rewrite when the retention rules still fail (promise in the first 45 s, open on YOU, no lore before 20 s,
    a re-hook at least every REHOOK_MAX_GAP_SEC, every opened question answered). The contract then checks (hard)."""
    from whatifs import growth as GR
    r = GR.retention_issues(script.get("script", ""), spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops"))
    if not r.get("issues"): return script, []
    from whatifs.models import ask
    rev = ask("rewrite", wbrief, "RETENTION FIX (mandatory; keep every label, tag, [PUNCH]/[SEND]/[AWE] marker and fact): " + " | ".join(r["issues"]) +
              "\nNARRATION:\n" + script.get("script", "") + "\nRewrite the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
    if str(rev.get("script", "")).strip(): script = rev
    log(f"enforce: retention fix ({len(r['issues'])} issue(s))", episode=episode)
    return script, r["issues"]

def marker_issues(text, fmt="long"):
    from whatifs import formats as FMT
    if FMT.rule("joke_density") != "must" and FMT.rule("send_and_awe") != "must": return []              # v12 V2a: optional devices are never forced by a rewrite
    need, have, gap = joke_need(text, fmt), len(punch_lines(text)), biggest_gap_lines(text)
    out = []
    if have < need or gap > 2.2 * S("JOKE_EVERY_SEC_LONG" if fmt == "long" else "JOKE_EVERY_SEC_SHORT", float):
        out.append(f"add punchlines so there are at least {need} [PUNCH] lines, never more than {int(2 * S('JOKE_EVERY_SEC_LONG', float))} s apart (now {have}; biggest gap {gap:.0f} s)")
    if not SEND_RE.search(text): out.append("mark one [SEND] moment")
    if not AWE_RE.search(text): out.append("mark the [AWE] reveal (not in the last 20%)")
    return out

def fix_all(script, wbrief, spine, episode, fmt="long"):
    """ONE mandatory rewrite carrying EVERY open retention + marker problem (two separate rewrites could undo each other). Returns (script, issues)."""
    from whatifs import growth as GR
    text = script.get("script", "")
    ret = GR.retention_issues(text, spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops")).get("issues") or []
    mk = marker_issues(text, fmt)
    from whatifs.org import audience as AUD                 # v12 V1 (D13): too many numbers is fixed by the same single rewrite
    nm = AUD.number_issues(text) if fmt == "long" else []
    from whatifs.org import layman as LAY                   # v12 V1b (D13): too many expert words is fixed by the same single rewrite
    pl = LAY.plain_issues(text, spine.get("promise")) if fmt == "long" else []
    from whatifs import formats as FMT                      # v12 V2a: a script that sounds like a trial in a format that is not one is fixed by the same single rewrite
    fo = FMT.format_issues(text) if fmt == "long" else []
    from whatifs.org import inside as INS                   # v12 V2b (D13): a voice from outside the scene is fixed by the same single rewrite
    ins = INS.issues(text) if fmt == "long" else []
    en = FMT.ending_issues(text) if fmt == "long" else []    # v12 V2b (D4): an ending that is not the format's is fixed by the same single rewrite
    issues = ret + mk + nm + pl + fo + ins + en
    if not issues: return script, []
    from whatifs.models import ask
    tags = (["RETENTION FIX"] if ret else []) + (["MARKER FIX"] if mk else []) + (["NUMBERS FIX"] if nm else []) + (["PLAIN WORDS FIX"] if pl else []) + (["FORMAT FIX"] if fo else []) + (["INSIDE FIX"] if ins else []) + (["ENDING FIX"] if en else [])
    rev = ask("rewrite", wbrief, f"MANDATORY FIX ({' + '.join(tags)}; keep every label, tag, [PUNCH]/[SEND]/[AWE] marker and fact; change only what fixes these): "
              + " | ".join(issues) + "\nNARRATION:\n" + text + "\nRewrite the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
    if str(rev.get("script", "")).strip(): script = rev
    log(f"enforce: one mandatory fix for {len(issues)} issue(s) ({', '.join(tags)})", episode=episode)
    return script, issues

