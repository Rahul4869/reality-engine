"""v10 Slop Guard (K137; SLOP_GUARD_SPEC.md): one 0-100 'AI slop' risk score per video, from measurements we already have (₹0):
still share (time on plain stills vs living/Kling motion), template fingerprint (shot-type pattern vs the last 6 videos), voice flatness (spread
of words per second across lines) and opening repetition (vs the last 10 openings). Hard defects (garbled text, broken faces, frozen or black
picture, sync) are already HOLD problems in qc.full_check; this score never holds a video by itself. It is recorded per video (Slop_Scores),
shown on the dashboard, and a score above SLOP_WARN sends one FYI card naming the biggest factor (the Visual Lab then proposes fixes)."""
from __future__ import annotations
import re, statistics
from whatifs.core import S, log, store, iso

def _durations(units, shots):
    out = []
    for i, s in enumerate(shots):
        if i < len(units):
            d = max(0.0, float(units[i].get("end", 0)) - float(units[i].get("start", 0)))
        else: d = 0.0
        out.append((s.get("type", "still"), d))
    return out

def _shingles(seq, k=3):
    return {"".join(seq[i:i + k]) for i in range(max(0, len(seq) - k + 1))}

def score(units, shots, episode=""):
    durs = _durations(units, shots); total = sum(d for _, d in durs) or 1.0
    still = sum(d for t, d in durs if t in ("still", "stock")) / total
    motion = sum(d for t, d in durs if t in ("living", "kling")) / total
    code = {"still": "S", "stock": "S", "living": "L", "kling": "K", "graphic": "G", "reaction": "R"}
    fp = "".join(code.get(t, "S") for t, _ in durs)
    hist = store().rows("Slop_Scores")[-6:]
    sims = []
    mine = _shingles(list(fp))
    for h in hist:
        other = _shingles(list(str(h.get("fingerprint") or "")))
        if mine and other: sims.append(len(mine & other) / len(mine | other))
    template_sim = max(sims) if sims else 0.0
    rates = []
    for u in units:
        ws = u.get("words") or []; d = float(u.get("end", 0)) - float(u.get("start", 0))
        if ws and d > 1.0: rates.append(len(ws) / d)
    flat = 1.0 - min(1.0, statistics.pstdev(rates) / 0.6) if len(rates) >= 6 else 0.0
    opening = next((str(u.get("text", "")) for u in units if str(u.get("text", "")).strip()), "")
    def words(t): return {w for w in re.findall(r"[a-z']+", t.lower()) if len(w) > 3}
    ow = words(opening); osim = 0.0
    for h in store().rows("Slop_Scores")[-10:]:
        hw = words(str(h.get("opening") or ""))
        if ow and hw: osim = max(osim, len(ow & hw) / len(ow | hw))
    parts = {"still_share": round(max(0.0, still - 0.6) / 0.4, 3), "template_sim": round(template_sim, 3), "voice_flatness": round(flat, 3), "opening_repeat": round(osim, 3)}
    w = {"still_share": 0.35, "template_sim": 0.25, "voice_flatness": 0.2, "opening_repeat": 0.2}
    slop = round(100 * sum(min(1.0, parts[k]) * w[k] for k in w))
    return {"slop": slop, "still": round(still, 3), "motion": round(motion, 3), "fingerprint": fp[:300], "opening": opening[:200], **parts}

def record(units, shots, episode=""):
    """Score + store + (above SLOP_WARN) one FYI card. Never raises; returns the score dict or {}."""
    if not S("SLOP_GUARD_ON", bool): return {}
    try:
        r = score(units, shots, episode)
        store().append("Slop_Scores", [{"ts": iso(), "episode_id": episode, **{k: r[k] for k in ("slop", "still", "motion", "template_sim", "voice_flatness", "opening_repeat", "fingerprint", "opening")}}])
        if r["slop"] > S("SLOP_WARN", int):
            worst = max(("still_share", "template_sim", "voice_flatness", "opening_repeat"), key=lambda k: r[k])
            tip = {"still_share": "too much screen time on plain stills (the Visual Lab will propose motion upgrades)", "template_sim": "the shot pattern repeats recent videos (the variety guard changes the next structure)",
                   "voice_flatness": "the read is flat (more direction tags in the voice step)", "opening_repeat": "the opening line resembles recent ones"}[worst]
            from whatifs import notify as NT
            NT.send("slop", f"Slop risk {r['slop']}/100 for {episode}: {tip}.", tier="fyi", dedupe_key=f"slop|{episode}")
        return r
    except Exception as e:
        log(f"slop score skipped: {str(e)[:120]}", "WARN", episode); return {}
