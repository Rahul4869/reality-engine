"""Pilot Shorts: cheap 12-15 s Shorts that test bench premises before a long video is written. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, os
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, WORK, scrub, SMALL

def spent_this_month():
    mk = now_utc().strftime("%Y-%m"); tot = 0.0
    for r in store().rows("Cost_Log"):
        if r.get("basis") == "summary" or not str(r.get("ts", "")).startswith(mk): continue
        if str(r.get("episode_id") or "").startswith("PL") or str(r.get("role") or "") == "pilot":
            try: tot += float(r.get("inr") or 0)
            except Exception: pass
    return tot

def est_inr():
    fx = S("USD_INR", float) or 99.0
    return 3 * S("PRICE_STILL_USD", float) * fx + 1.0

def due(now=None):
    now = now or now_utc()
    days = [d.strip()[:3] for d in str(S("PILOT_DAYS") or "").split(",") if d.strip()]
    if now.strftime("%a") not in days: return False
    return not any(str(r.get("ts", "")).startswith(now.strftime("%Y-%m-%d")) for r in store().rows("Pilots"))

def _candidate():
    from whatifs.premise import bench_rows
    piloted = {r.get("bench_id") for r in store().rows("Pilots")}
    for r in bench_rows(mark_stale=False):
        if r.get("bench_id") not in piloted: return r
    return None

def run(publish=True):
    """Make (and post) one pilot Short. Returns a dict; never raises."""
    ep = f"PL{now_utc():%Y%m%d%H%M}"
    try:
        if not S("PILOTS_ON", bool): return {"ok": False, "why": "PILOTS_ON is FALSE"}
        from whatifs import shortslab as SL, governor as G
        if not SL.allowed_today(): return {"ok": False, "why": "the 14-Shorts-a-week ceiling is reached"}
        e = est_inr()
        if spent_this_month() + e > S("PILOT_MONTHLY_INR", float): return {"ok": False, "why": "this month's pilot money is used"}
        ok, why = G.extras_allowed(e, "pilot")
        if not ok: return {"ok": False, "why": why}
        b = _candidate()
        if not b: return {"ok": False, "why": "no unpiloted bench premise"}
        from whatifs.models import ask
        out = ask("pilot", "Write a 12-15 second vertical Short that tests a 'what if' premise: a hook that puts YOU in it with a number or a clock (max 9 words), "
                  "then exactly 3 short lines (max 8 words each), the last one an open question. Never the answer. JSON only: {hook, lines:[3]}",
                  json.dumps({"premise": b.get("premise"), "headline": b.get("headline")}), want_json=True, max_tokens=400, fake_key="pilot")
        hook = str((out or {}).get("hook") or b.get("headline") or b.get("premise"))[:80] if isinstance(out, dict) else str(b.get("headline"))[:80]
        lines = [str(x)[:70] for x in ((out or {}).get("lines") or [])][:3] if isinstance(out, dict) else []
        while len(lines) < 3: lines.append("Should the jury hear this case?")
        from whatifs import media as MD, specials as SP
        W, H = SP._vsize(); wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True)
        clips, cards, beats = [], [], [3.5, 3.5, 3.5, 3.5]
        for i, line in enumerate([hook] + lines[:3]):
            img = os.path.join(wd, f"p{i}.png")
            MD.still(f"{b.get('premise')}, moment {i + 1} of 4: {line}, first-person view, cinematic, vertical, no text", img, ep, seed=f"{ep}|{i}", w=576, h=1024)
            clips.append(SP._portrait_motion(img, os.path.join(wd, f"p{i}.mp4"), beats[i], W, H))
            cards.append(SP._card_png(line.upper() if i == 0 else "", line if i else "", os.path.join(wd, f"c{i}.png"), W, H))
        end = SP._card_png("Should the jury hear this case?", "Comment YES. Full trials Tue + Sat.", os.path.join(wd, "end.png"), W, H, end=True)
        snd = SP._sound(sum(beats) + 2.5, beats, os.path.join(wd, "s.wav"))
        path = SP._assemble(clips, beats, cards, end, snd, os.path.join(wd, f"{ep}.mp4"), W, H)
        yt = ""
        if publish:
            from whatifs import publish as PUB, launch as LA
            if LA.uploads_open():
                try: yt = PUB.yt_upload(path, hook[:90], f"{b.get('premise')}\nShould the jury hear this case? Comment YES.\nAI-assisted visuals; original story.", ["what if"], short=True, ai_label=True)
                except Exception as x: log(f"pilot upload failed: {scrub(x)[:120]}", "WARN", ep)
        store().append("Pilots", [{"ts": iso(), "id": ep, "bench_id": b.get("bench_id"), "premise": str(b.get("premise"))[:200], "hook": hook, "yt_id": yt, "views": "", "bonus": ""}])
        return {"ok": True, "id": ep, "path": path, "yt_id": yt, "bench_id": b.get("bench_id")}
    except Exception as x:
        log(f"pilot Short failed (nothing posted): {scrub(x)[:200]}", "WARN", ep); return {"ok": False, "why": str(x)[:200]}

def measure(now=None):
    """After PILOT_MEASURE_HOURS: engaged views -> a bonus (0..PILOT_MAX_BONUS) added to the premise's bench score. Never raises."""
    from whatifs import publish as PUB
    import statistics
    now = now or now_utc(); st = store(); done = 0
    rows = st.rows("Pilots")
    vals = [float(r["views"]) for r in rows if str(r.get("views", "")).strip() not in ("",)]
    for r in rows:
        t = parse_iso(r.get("ts"))
        if not r.get("yt_id") or str(r.get("views", "")).strip() or not t or (now - t).total_seconds() < S("PILOT_MEASURE_HOURS", float) * 3600: continue
        try:
            v = PUB.yt_engaged_views(r["yt_id"], t.strftime("%Y-%m-%d"))
            if v is None: v = PUB.yt_views(r["yt_id"])
            if v is None: continue
            med = statistics.median(vals) if len(vals) >= 3 else None
            bonus = round(min(S("PILOT_MAX_BONUS", float), max(-S("PILOT_MAX_BONUS", float), ((v / med) - 1.0) * S("PILOT_MAX_BONUS", float))) if med else 0.0, 2)
            st.update("Pilots", "id", r["id"], {"views": int(v), "bonus": bonus}); vals.append(float(v)); done += 1
            if bonus:
                for b in st.rows("Premise_Bench"):
                    if b.get("bench_id") == r.get("bench_id"):
                        try: st.update("Premise_Bench", "bench_id", b["bench_id"], {"combined": round(float(b.get("combined") or 0) + bonus, 2)})
                        except Exception: pass
        except Exception as x: log(f"pilot measure skipped: {scrub(x)[:80]}", "WARN")
    return done
