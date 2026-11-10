"""v11 Stage D (K159): standalone daily Shorts - each one a complete mini-trial built to break out (research: cold start + Breakout Protocol + Feel Layer).

Every Short:
- TOPIC: an approved breakout follow-up first (Breakout_Queue), else the best unused premise on the bench.
- HOOK ARCHETYPE: chosen by the Channel Brain (Thompson sampling; BRAIN_HOLDOUT keep the default as the control) and recorded as a feature.
- SCRIPT: 3 variants by Claude Sonnet, judged BLIND by Gemini Pro + Gemini Flash (a different family from the writer), both orders; deterministic
  checks: 60-120 words, 3-6 beats, first line <= 14 words, canon cast only, a loop line that feeds the first line.
- PICTURES/MOTION: beat 1 starts from a reference-locked staged frame (Google); one new Kling shot every SHORTS_KLING_EVERY Shorts (or for a breakout
  follow-up), everything else cheap living-still motion. Designed voices, captions, a cover as the first frame.
- REVIEW: the first SHORTS_REVIEW_FIRST_N Shorts wait for the owner's Approve; then they post directly.
- LEARNING: Video_Features + a forecast are written before posting; outcomes come back through brain.ingest_shorts().
- MONEY: the first Short of a day is core production (it may not eat the money reserved for the month's long slots); further Shorts are extras
  (growth allowance + the 90% guard). Episode ids start with 'SH' (not counted as specials)."""
from __future__ import annotations
import json, os
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, WORK, scrub

CAST = ("VALE", "GRIMM", "ROSA", "ARCHIVIST")
NAMES = {"VALE": "INSPECTOR VALE", "GRIMM": "DR. GRIMM", "ROSA": "NANA ROSA", "ARCHIVIST": "THE ARCHIVIST"}
WORLD_OF = {"VALE": "office", "GRIMM": "lab", "ROSA": "court", "ARCHIVIST": "case"}
RUBRIC = ("Rank these 30-second Short scripts for an animated courtroom-comedy science show, best first, as a viewer scrolling a feed: (1) would you "
          "stop scrolling in the first second; (2) is the stakes line about YOU; (3) a surprise or laugh every few seconds; (4) the last line flows back "
          "into the first (it loops); (5) accurate science. Scripts are anonymous.")

def _today_count(now):
    return sum(1 for r in store().rows("Specials") if r.get("kind") == "short" and parse_iso(r.get("ts")) and (now - parse_iso(r["ts"])).total_seconds() < 86400)

def target_today(now=None):
    """SHORTS_PER_DAY may be fractional: 1.5 -> 2 on even days, 1 on odd days."""
    now = now or now_utc(); x = S("SHORTS_PER_DAY", float)
    base = int(x); return base + (1 if (x - base) >= 0.5 and now.toordinal() % 2 == 0 else 0)

def masters_ready():
    """v11 audit: Shorts start from reference-locked faces, so they wait until every core character has a LOCKED master (owner-approved)."""
    from whatifs import show as SHOW
    locked = {r.get("character") for r in store().rows("Character_Sheets") if r.get("expression") == "master" and r.get("status") == "LOCKED"}
    return all(c["id"] in locked for c in SHOW.characters() if c.get("speaker") != "WITNESS")

def due(now=None):
    now = now or now_utc()
    if not S("SHORTS_TRACK_ON", bool) or S("PAUSED", bool): return False
    if S("SHORTS_NEED_MASTERS", bool) and not masters_ready(): return False
    from whatifs.notify import IST
    if now.astimezone(IST).hour < S("SHORTS_START_HOUR_IST", int): return False
    return _today_count(now) < target_today(now)

def _budget_ok(est, first_today):
    from whatifs import governor as G
    if first_today:                                                            # core: only the long slots' reserved money is protected
        left = max(0, min(G.episodes_left_this_month(), G.max_long_videos() - G.long_videos_this_month()))
        room = G.production_room_inr() - est
        return (room >= left * G.full_episode_inr(), f"Rs {room:.0f} left after this, Rs {left * G.full_episode_inr():.0f} kept for {left} long slot(s)")
    return G.extras_allowed(est, kind="short_extra")

def pick_topic():
    st = store()
    done = {r.get("video_key") for r in st.rows("Breakout_Queue") if r.get("status") in ("DONE", "DECLINED")}
    for r in st.rows("Breakout_Queue"):
        if r.get("status") in ("APPROVED", "FOLLOWUP 1") and r.get("video_key") not in done:
            src = next((e for e in st.rows("Episodes") if e.get("episode_id") == r["video_key"]), None) or \
                  next((s for s in st.rows("Specials") if s.get("id") == r["video_key"]), {})
            return {"premise": src.get("premise") or src.get("title") or r["video_key"], "origin": "breakout", "follow_of": r["video_key"]}
    used = {str(r.get("premise", "")).strip().lower() for r in st.rows("Specials") if r.get("kind") == "short"}
    from whatifs import premise as PRM                                  # READY rows only, best first (STALE / USED never come back)
    bench = [b for b in PRM.bench_rows(mark_stale=False) if b.get("premise") and b["premise"].strip().lower() not in used]
    if bench: return {"premise": bench[0]["premise"], "origin": "bench", "bench_id": bench[0].get("bench_id")}
    return None

def _valid(s):
    beats = s.get("beats") or []; words = sum(len(str(b.get("line", "")).split()) for b in beats)
    probs = []
    if not 3 <= len(beats) <= 6: probs.append(f"{len(beats)} beats")
    if not 60 <= words <= 120: probs.append(f"{words} words")
    if beats and len(str(beats[0].get("line", "")).split()) > 14: probs.append("first line too long")
    if any(str(b.get("who", "")).upper() not in CAST for b in beats): probs.append("unknown character")
    if not str(s.get("loop_line") or "").strip(): probs.append("no loop line")
    from whatifs import enforce as EN                                # v11.1 (K166): the same hard rules as long videos, at Shorts tempo
    secs = words / max(1.0, S("WPM_ESTIMATE", float)) * 60.0
    punches = sum(1 for b in beats if EN.PUNCH_RE.search(str(b.get("line", ""))))
    if punches < max(1, int(secs // S("JOKE_EVERY_SEC_SHORT", float))): probs.append(f"{punches} punchlines (need one per {S('JOKE_EVERY_SEC_SHORT', float):.0f} s)")
    if not any(EN.SEND_RE.search(str(b.get("line", ""))) for b in beats): probs.append("no [SEND] moment")
    return probs

def write(topic, arch, ep):
    from whatifs.models import ask_many
    from whatifs import brain as BR, room2 as R2
    spec = (f"Write ONE standalone 25-40 second Short for 'Reality on Trial' (cast: Inspector Vale, Dr. Grimm, Nana Rosa, the Archivist). PREMISE: {topic['premise']}. "
            f"HOOK ARCHETYPE (mandatory for the first line, under 1 second): {arch} - {BR.HOOK_ARCHETYPES.get(arch, '')}. Rules: 3-6 beats, 60-120 words in "
            "total, a different speaker each beat, no greeting, one real number with its source if you state a fact, a joke or surprise every few seconds, "
            "and a final line that grammatically flows back into the first line. Start every punchline with [PUNCH] (at least one every 6 seconds) and "
            "mark the one line a viewer would send to a friend with [SEND]; markers are never spoken. JSON only: {\"title\": \"<= 60 chars\", \"beats\": [{\"who\": \"VALE|GRIMM|ROSA|"
            "ARCHIVIST\", \"line\": \"...\", \"style\": \"delivery note\"}], \"loop_line\": \"the last words that lead back to the first line\"}")
    outs = ask_many([dict(role="punchup", system=spec, prompt=f"Variant {k + 1}: make it genuinely different from an obvious take.", episode=ep,
                          fake_key="short_script", max_tokens=1500) for k in range(max(1, S("SHORTS_VARIANTS", int)))])
    good = [o for o in outs if isinstance(o, dict) and not _valid(o)]
    if not good: raise RuntimeError("no Short script passed the checks: " + "; ".join(", ".join(_valid(o)) for o in outs if isinstance(o, dict))[:200])
    texts = ["\n".join(f"{b['who']}: {b['line']}" for b in g["beats"]) for g in good]
    win, info = R2.jury(texts, RUBRIC, f"Premise: {topic['premise']}", ep, "short", judges=(("jury", "Gemini Pro"), ("jury_flash", "Gemini Flash")))
    return good[win], info

def run(force=False, publish=True, now=None):
    """Make (and post, or send for review) one standalone Short. Returns a record."""
    from whatifs import specials as SP, anim as ANIM, media as MD, brain as BR
    import subprocess
    now = now or now_utc()
    if not force and not due(now): return {"ok": False, "skipped": "not due"}
    first = _today_count(now) == 0
    topic = pick_topic()
    if not topic: log("Shorts: no unused premise on the bench (the weekly research fills it)", "WARN"); return {"ok": False, "skipped": "no topic"}
    brk = topic.get("origin") == "breakout"
    ep = f"{'BRK' if brk else 'SH'}{now:%Y%m%d%H%M}"                # BRK ids: every cost of a follow-up is charged to the breakout fund
    n_kling = sum(1 for r in store().rows("Specials") if r.get("kind") == "short")
    use_kling = topic.get("origin") == "breakout" or (n_kling % max(1, S("SHORTS_KLING_EVERY", int)) == 0)
    fx = S("USD_INR", float) or 92.0
    est = (S("PRICE_KLING_USD", float) if use_kling else 0.0) * fx + 6 * 0.006 * fx + S("PRICE_GEM_IMAGE_USD", float) * fx + 6.0
    from whatifs import governor as G
    ok, why = G.extras_allowed(est, kind="breakout") if brk else _budget_ok(est, first)
    if not ok: log(f"Shorts: paused ({why})", "WARN"); return {"ok": False, "skipped": "budget", "why": why}
    choice = BR.choose("hook", "short") if S("BRAIN_ON", bool) else {"level": S("BRAIN_DEFAULT_HOOK"), "holdout": False}
    arch = choice["level"] or S("BRAIN_DEFAULT_HOOK")
    try:
        sc, jinfo = write(topic, arch, ep)
        W, H = SP._vsize(); wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True)
        from whatifs import show as SHOWM, enforce as EN
        beats = [{"who": str(b["who"]).upper(), "line": SHOWM.SHOW_TAG_RE.sub("", str(b["line"])).strip(), "punch": bool(EN.PUNCH_RE.search(str(b["line"]))),
                  "style": b.get("style", ""), "world": WORLD_OF.get(str(b["who"]).upper(), "case")} for b in sc["beats"]]      # markers never spoken / captioned
        voices, at = [], 0.6
        for i, b in enumerate(beats):
            vp, vs = SP._voice_line(b["who"], b["line"], b["style"], os.path.join(wd, f"v{i}.wav"), ep)
            lead = S("PUNCH_PAUSE_S", float) if b.get("punch") else 0.1            # v11.1: pause-then-punch
            b["sec"] = max(2.2, vs + 0.25 + lead); voices.append((vp, at + lead)); at += b["sec"]
        clips, cards = [], []
        for i, b in enumerate(beats):
            shot = {"anim": {"world": b["world"], "line": b["line"], "slot": i}}
            img = os.path.join(wd, f"f{i}.png")
            if i == 0: img, _how = ANIM.start_frame(shot, img, ep, wd, aspect="9:16"); first_frame = img
            else: MD.still(ANIM.frame_prompt(shot["anim"], "9:16"), img, ep, seed=f"{ep}{i}")
            clip = os.path.join(wd, f"c{i}.mp4")
            if i == 0 and use_kling: MD.animate(None, img, ANIM.acting_prompt(shot), clip, ep, hero=True)
            else: MD.animate(None, img, f"subtle living motion, {ANIM.style_words()}", clip, ep, hero=False)
            clips.append(clip); cards.append(SP._card_png(NAMES.get(b["who"], ""), b["line"], os.path.join(wd, f"k{i}.png"), W, H))
        cov = SP._cover(first_frame, sc["title"], os.path.join(wd, "cover.png"), W, H)
        covclip = os.path.join(wd, "cover.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", "0.5", "-i", cov, "-vf", f"scale={W}:{H},fps=30,format=yuv420p", "-c:v", "libx264", covclip],
                       check=True, timeout=120)
        clips.insert(0, covclip); cards.insert(0, SP._card_png("", "", os.path.join(wd, "blank.png"), W, H))
        secs = [0.5] + [b["sec"] for b in beats]
        end = SP._card_png("The full trial is on the channel", "Reality on Trial", os.path.join(wd, "end.png"), W, H, end=True)
        snd = SP._mix(SP._sound(sum(secs) + 2.5, secs, os.path.join(wd, "bed.wav")), [(p, t + 0.5) for p, t in voices], os.path.join(wd, "mix.wav"))
        out = SP._assemble(clips, secs, cards, end, snd, os.path.join(wd, f"{ep}.mp4"), W, H)
        rec = {"ts": iso(now), "id": ep, "kind": "short", "title": sc["title"], "format": arch, "ask": "", "yt_id": "", "ig": "", "fb": "", "status": "MADE",
               "views_7d": "", "file": "", "premise": topic["premise"]}
        BR.tag(ep, "short", title=sc["title"], premise=topic["premise"], hook=arch, sec=sum(secs), lead=beats[0]["who"],
               origin=topic.get("origin", "ai"), arm=choice.get("p_draws"), holdout=choice.get("holdout"))
        BR.forecast(ep, "short", hook=arch)
        reviewed = sum(1 for r in store().rows("Specials") if r.get("kind") == "short")
        if publish and reviewed < S("SHORTS_REVIEW_FIRST_N", int):
            rec.update(SP._await_review(out, {"title": sc["title"]}, "short", ep, beats))
        elif publish: rec.update(SP._publish(out, sc["title"], ep))
        store().append("Specials", [rec])
        if topic.get("origin") == "breakout":                 # 2 follow-ups per approved breakout, then the item is done
            q = next((r for r in store().rows("Breakout_Queue") if r.get("video_key") == topic["follow_of"] and r.get("status") == "APPROVED"), {})
            left = max(0, int(float(q.get("left") or 1)) - 1)
            store().update("Breakout_Queue", "video_key", topic["follow_of"], {"left": left, "status": "APPROVED" if left > 0 else "DONE"})
        log(f"Short {ep} ({arch}{', holdout' if choice.get('holdout') else ''}{', Kling' if use_kling else ''}): {sc['title']} -> {rec['status']}", episode=ep)
        return dict(rec, ok=True, path=out)
    except Exception as e:
        log(f"Short failed (nothing posted): {scrub(e)[:200]}", "WARN", ep); return {"ok": False, "why": scrub(e)[:200]}
