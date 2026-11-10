"""v11 Stage D (K160): the 'Case Files' countdown spin-off - a long video (watch hours) built to break out AND to stay clearly original
(research: Spin-off Breakout Protocol, 9 Nov 2026; YouTube's reused-content rule judges the WHOLE channel).

Build: CASEFILES_CASES past episodes (archived masters on Drive), ranked into a countdown (#N -> #1, by real views). From each, one 60-90 s segment
around its twist (57% of runtime, where the director placed an animated scene). NEW material written for this video: a cold open, an Archivist
bridge before every case (each with a forward reference: an open loop), a fresh Nana Rosa verdict after every case, and a closing jury vote.

Gates (every one enforced in code; a failure = not published):
- G0 cost <= SPINOFF_CAP_INR;
- G1 originality: new material / total runtime >= CASEFILES_MIN_NEW_SHARE;
- G2 narrative: a stated theme + every bridge opens a loop (a forward reference) + no bridge repeats another;
- G3 outcome variety: no two neighbouring cases share a verdict style, and Grimm-fails endings <= 40% of cases.
Policy: the description lists the source episodes, every case is a chapter, and the video says it contains new scenes."""
from __future__ import annotations
import json, os, re, subprocess
from whatifs.core import S, log, store, iso, now_utc, FAKE, WORK, scrub

def _assets(v):
    """The Episodes 'assets' cell as a dict, whether the store hands back a dict, JSON text or a Python-style dict string (audit fix)."""
    if isinstance(v, dict): return v
    s = str(v or "").strip()
    if not s: return {}
    try: return json.loads(s)
    except Exception:
        import ast
        try: r = ast.literal_eval(s); return r if isinstance(r, dict) else {}
        except Exception: return {}

def eligible(now=None):
    """Past episodes that have an archived master (Drive) and a public video, newest first."""
    out = []
    for e in store().rows("Episodes"):
        a = _assets(e.get("assets"))
        if a.get("_master.mp4") and e.get("yt_id"): out.append(dict(e, master_id=a["_master.mp4"]))
    return out[::-1]

def _views(e):
    try: return float(next((r.get("views") for r in store().rows("Analytics") if r.get("yt_id") == e.get("yt_id")), 0) or 0)
    except Exception: return 0.0

def pick_cases(n):
    eps = eligible()
    if len(eps) < n: return []
    ranked = sorted(eps[: max(n, S("CASEFILES_POOL", int))], key=_views)          # countdown order: weakest first, #1 = most watched
    return ranked[-n:]

def _gate_variety(cases):
    styles = [str(c.get("verdict_style") or c.get("verdict") or "").lower() for c in cases]
    probs = [f"cases {i} and {i + 1} share the verdict style '{styles[i]}'" for i in range(len(styles) - 1) if styles[i] and styles[i] == styles[i + 1]]
    grimm = sum(1 for c in cases if "grimm" in str(c.get("ending") or "").lower() and "fail" in str(c.get("ending") or "").lower())
    if cases and grimm / len(cases) > 0.4: probs.append(f"{grimm} of {len(cases)} cases end with Grimm's device failing (max 40%)")
    return probs

FWD = re.compile(r"(?i)\b(still to come|coming up|before #?1|wait (until|till)|later|next|but first|number one|#\s?1)\b")

def _gate_narrative(plan):
    probs = []
    if len(str(plan.get("theme", "")).split()) < 4: probs.append("no stated theme")
    br = [str(b) for b in plan.get("bridges") or []]
    if any(not FWD.search(b) for b in br[:-1]): probs.append("a bridge opens no loop (no forward reference)")
    if len(set(x.lower() for x in br)) < len(br): probs.append("two bridges are identical")
    return probs

def write(cases, ep):
    from whatifs.models import ask
    brief = [{"case": i + 1, "rank": len(cases) - i, "title": c.get("title"), "premise": c.get("premise")} for i, c in enumerate(cases)]
    return ask("punchup", "You write NEW material for a 'Case Files' countdown of an animated courtroom-comedy science show (cast: Inspector Vale, "
               "Dr. Grimm, Nana Rosa, the Archivist). One theme ties every case together. Write: a cold open (30-45 s, the most surprising moment "
               "teased without revealing #1), one Archivist bridge per case (20-40 s; every bridge except the last opens a loop toward a later case, e.g. "
               "'...and #3 is why Nana banned Grimm from the building'), a NEW 5-10 s Nana Rosa verdict per case (different style each time), and a closing "
               "jury vote. JSON only: {\"theme\": \"...\", \"title\": \"<= 70 chars\", \"cold_open\": \"...\", \"bridges\": [\"...\"], \"verdicts\": [\"...\"], "
               "\"vote\": \"...\"}", "CASES (countdown order, weakest first): " + json.dumps(brief, ensure_ascii=False), episode=ep, fake_key="casefiles", max_tokens=4000)

def _say(text, who, path, ep):
    from whatifs import specials as SP
    return SP._voice_line(who, text, "", path, ep)

def _segment(src, start, dur, out, W, H):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", src, "-t", f"{dur:.2f}", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-ar", "48000", "-ac", "2", out], check=True, timeout=900)
    return out

def _card_clip(text, sub, wav, sec, out, W, H, wd, k):
    from whatifs import specials as SP
    png = SP._card_png(text, sub, os.path.join(wd, f"card{k}.png"), W, H)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{sec:.2f}", "-i", png, "-i", wav, "-vf", "fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", out], check=True, timeout=300)
    return out

def _dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)

def run(force=False, publish=True):
    """Make one Case Files countdown. Returns a record (ok False + why when a gate stops it)."""
    from whatifs import publish as PUB, governor as G
    ep = f"CF{now_utc():%Y%m%d%H%M}"
    n = S("CASEFILES_CASES", int); cases = pick_cases(n)
    if not cases: return {"ok": False, "why": f"needs {n} archived episodes (have {len(eligible())})"}
    est = 6.0 + n * 3.0
    if est > S("SPINOFF_CAP_INR", float): return {"ok": False, "why": "G0 cost"}
    ok, why = G.extras_allowed(est, kind="spinoff")
    if not ok and not force: return {"ok": False, "why": why}
    probs = _gate_variety(cases)
    plan = write(cases, ep)
    probs += _gate_narrative(plan)
    if len(plan.get("bridges") or []) != n or len(plan.get("verdicts") or []) != n: probs.append("the writer did not give one bridge and one verdict per case")
    if probs: log(f"Case Files stopped by its gates: {'; '.join(probs)}", "WARN", ep); return {"ok": False, "why": "; ".join(probs)}
    from whatifs.specials import _vsize
    W, H = (1920, 1080) if not os.environ.get("WI_SMALL") else (640, 360)
    wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True)
    parts, new_sec, chapters, t = [], 0.0, [], 0.0
    def add(p, new):
        nonlocal new_sec, t
        d = _dur(p); parts.append(p); t += d
        if new: new_sec += d
    wav, s = _say(plan["cold_open"], "ARCHIVIST", os.path.join(wd, "cold.wav"), ep)
    add(_card_clip(plan.get("title", ""), "Case Files", wav, s + 0.4, os.path.join(wd, "p_cold.mp4"), W, H, wd, "c"), True)
    for i, c in enumerate(cases):
        chapters.append((t, f"#{n - i}: {c.get('title', '')}"))
        wav, s = _say(plan["bridges"][i], "ARCHIVIST", os.path.join(wd, f"b{i}.wav"), ep)
        add(_card_clip(f"#{n - i}", c.get("title", ""), wav, s + 0.3, os.path.join(wd, f"p_b{i}.mp4"), W, H, wd, f"b{i}"), True)
        src = os.path.join(wd, f"m{i}.mp4")
        if not os.path.exists(src): PUB.drive_download(c["master_id"], src)
        L = _dur(src); seg = min(S("CASEFILES_SEG_SEC", float), max(10.0, L * 0.3))
        add(_segment(src, max(0.0, L * 0.57 - seg / 2), seg, os.path.join(wd, f"p_s{i}.mp4"), W, H), False)
        wav, s = _say(plan["verdicts"][i], "ROSA", os.path.join(wd, f"v{i}.wav"), ep)
        add(_card_clip("NEW VERDICT", c.get("title", ""), wav, s + 0.3, os.path.join(wd, f"p_v{i}.mp4"), W, H, wd, f"v{i}"), True)
    wav, s = _say(plan["vote"], "VALE", os.path.join(wd, "vote.wav"), ep)
    add(_card_clip("YOU ARE THE JURY", "Vote in the pinned comment", wav, s + 0.6, os.path.join(wd, "p_vote.mp4"), W, H, wd, "vote"), True)
    share = new_sec / max(1.0, t)
    if share < S("CASEFILES_MIN_NEW_SHARE", float):
        log(f"Case Files stopped: only {share:.0%} new material (needs {S('CASEFILES_MIN_NEW_SHARE', float):.0%})", "WARN", ep)
        return {"ok": False, "why": f"G1 originality {share:.0%}"}
    lst = os.path.join(wd, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(wd, f"{ep}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True, timeout=1800)
    desc = (f"{plan.get('theme', '')}\n\nThis countdown contains NEW scenes, a new verdict for every case and a jury vote.\n\nChapters:\n"
            + "\n".join(f"{int(a // 60):d}:{int(a % 60):02d} {lbl}" for a, lbl in [(0, 'Cold open')] + chapters)
            + "\n\nSource episodes: " + ", ".join(f"https://youtu.be/{c['yt_id']}" for c in cases))
    rec = {"ts": iso(), "id": ep, "kind": "casefiles", "title": plan.get("title", ""), "format": "countdown", "status": "MADE", "premise": plan.get("theme", ""),
           "yt_id": "", "file": ""}
    if publish:
        try: rec.update(_publish_long(out, plan.get("title", ""), desc, ep))
        except Exception as e: rec["status"] = "FAILED"; log(f"Case Files upload failed: {scrub(e)[:160]}", "WARN", ep)
    store().append("Specials", [rec])
    log(f"Case Files {ep}: {n} cases, {share:.0%} new material, {t / 60:.1f} min -> {rec['status']}", episode=ep)
    return dict(rec, ok=True, path=out, new_share=round(share, 3), minutes=round(t / 60, 1))

def _publish_long(path, title, desc, ep):
    from whatifs import publish as PUB
    if FAKE: return {"status": "POSTED", "yt_id": "fake" + ep}
    vid = PUB.yt_upload(path, title, desc, ["Reality on Trial", "science", "what if", "countdown"], publish_at=None, privacy="public", ai_label=True)
    return {"status": "POSTED", "yt_id": vid}
