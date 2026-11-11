"""Shorts Studio (D14): the standalone Short as a product of its own - a Short format as data, three scripts judged blind, every second an animated clip planned by code, the loop closed by code, and the viewer's seat for a Short before any picture is paid. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, math, os, subprocess
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, WORK, scrub
from whatifs import formats as FMT
from whatifs.org import shortseat as SEAT

VOICE_STYLE = "conversational"          # the guide's delivery in a Short (the voice job's own style table)
LOOP_MAX = 0.01                         # the most the last frame may differ from the first (in the band of the picture that never carries words) for the Short to loop without a jump
LOOP_BAND = (0.30, 0.52)                # that band, as shares of the height: under the promise text, above the captions
FPS = 30

def _rows(): return [r for r in store().rows("Specials") if r.get("kind") == "short"]

UPLOAD_HOLD = "HELD (uploads"           # how the upload path marks a Short that was MADE and waits to be posted (`specials._publish`)

def _held(r):
    """Was this Short refused by the short gate (written, voiced, judged - and NOT made)? A Short that was made and whose upload is on hold is not:
    it is recognised by the upload path's own status, never by a word that the name of a check could carry."""
    s = str(r.get("status") or ""); return s.startswith("HELD") and not s.startswith(UPLOAD_HOLD)

def _failed(r): return str(r.get("status") or "").startswith("FAILED")      # its job crashed: nothing was made

def _unmade(r): return _held(r) or _failed(r)

HELD_WAIT_H = 24                        # after a Short the short gate refused, the cadence tries again this many hours later (one paid writing a day at most)
ORDER_WAIT_H = 6                        # a follow-up order that could not be made (no money, held) is tried again this many hours later

def _followup(r): return str(r.get("id") or "").startswith("BRK")

def gap_h():
    """How far apart the Shorts of the cadence are made: 24 x floor(7 / SHORTS_PER_WEEK) hours (3 a week = 48 hours: the same three weekdays)."""
    return 24 * max(1, 7 // max(1, S("SHORTS_PER_WEEK", int)))

def cadence(now=None):
    """(due, why): is a Short of the cadence due? Fewer than SHORTS_PER_WEEK made in the last 7 days, fewer than SHORTS_PER_MONTH this calendar
    month, the last one at least gap_h() hours old - and after a Short the gate held or whose job crashed, HELD_WAIT_H hours (it was not made, so
    it does not count - but the writers were paid: at most one such try a day; follow-ups of a winner are outside the cadence)."""
    now = now or now_utc(); per_w, per_m = max(1, S("SHORTS_PER_WEEK", int)), max(1, S("SHORTS_PER_MONTH", int))
    mine = [(parse_iso(r.get("ts")), _unmade(r)) for r in _rows() if not _followup(r)]; mine = [(t, h) for t, h in mine if t]
    made = [t for t, h in mine if not h]
    week = sum(1 for t in made if 0 <= (now - t).total_seconds() < 7 * 86400); month = sum(1 for t in made if t.strftime("%Y-%m") == now.strftime("%Y-%m"))
    if week >= per_w: return False, f"{week} of {per_w} Shorts were made in the last 7 days"
    if month >= per_m: return False, f"{month} of {per_m} Shorts were made this month"
    if made and (now - max(made)).total_seconds() < gap_h() * 3600: return False, f"the last Short is {(now - max(made)).total_seconds() / 3600:.0f} hours old (they are made {gap_h()} hours apart)"
    held = [t for t, h in mine if h]
    if held and (now - max(held)).total_seconds() < HELD_WAIT_H * 3600 and (not made or max(held) > max(made)):
        return False, f"a Short was held or failed {(now - max(held)).total_seconds() / 3600:.0f} hours ago (the next try comes {HELD_WAIT_H} hours after it)"
    return True, ""

def _order_premise(q):
    st = store(); key = q.get("video_key")
    src = next((e for e in st.rows("Episodes") if e.get("episode_id") == key), None) or next((s for s in st.rows("Specials") if s.get("id") == key), {})
    return src.get("premise") or src.get("title") or key

def order_due(now=None):
    """The winner's follow-up that is due now, or None: an open order whose topic was not given up, not tried in the last ORDER_WAIT_H hours, while the
    last 7 days hold fewer than SHORTS_WEEKLY_CAP Shorts of any kind."""
    from whatifs import ladder as LAD
    now = now or now_utc(); made, dropped = _spent_premises()
    if sum(1 for r in _rows() if not _unmade(r) and parse_iso(r.get("ts")) and 0 <= (now - parse_iso(r["ts"])).total_seconds() < 7 * 86400) >= S("SHORTS_WEEKLY_CAP", int): return None
    for q in LAD.open_orders():
        plan = str(q.get("plan") or ""); tried = parse_iso(plan.split("last try ", 1)[1][:20]) if "last try " in plan else None
        if tried and (now - tried).total_seconds() < ORDER_WAIT_H * 3600: continue
        if str(_order_premise(q)).strip().lower() in dropped: continue          # held twice: the follow-up is left, nothing is paid a third time
        return q
    return None

def masters_ready():
    """Has every core character a LOCKED master (owner-approved)? Asked only when SHORTS_NEED_MASTERS is TRUE: a Short shows no character."""
    from whatifs import show as SHOW
    locked = {r.get("character") for r in store().rows("Character_Sheets") if r.get("expression") == "master" and r.get("status") == "LOCKED"}
    return all(c["id"] in locked for c in SHOW.characters() if c.get("speaker") != "WITNESS")

def due(now=None):
    now = now or now_utc()
    if not S("SHORTS_TRACK_ON", bool) or S("PAUSED", bool): return False
    if S("SHORTS_NEED_MASTERS", bool) and not masters_ready(): return False
    from whatifs.notify import IST
    if now.astimezone(IST).hour < S("SHORTS_START_HOUR_IST", int): return False
    return bool(order_due(now)) or cadence(now)[0]

def _budget_ok(est):
    """A Short of the cadence is core production (every topic starts as one): only the long slots' reserved money is protected."""
    from whatifs import governor as G
    left = max(0, min(G.episodes_left_this_month(), G.max_long_videos() - G.long_videos_this_month()))
    room = G.production_room_inr() - est
    return (room >= left * G.full_episode_inr(), f"Rs {room:.0f} left after this, Rs {left * G.full_episode_inr():.0f} kept for {left} long slot(s)")

# ------------------------------------------------------------------ what came before, and what comes next
def history(n=10):
    """The last `n` Shorts that were MADE in a Short format, newest first: [{id, format, hook, script}] - what the next Short must not be like."""
    out = []
    for r in reversed(_rows()):
        if r.get("format") not in FMT.SHORTS or _unmade(r): continue
        out.append({"id": r.get("id"), "format": r.get("format"), "hook": r.get("hook"), "script": r.get("script")})
        if len(out) >= n: break
    return out

def _spent_premises():
    """Premises that are used up as a Short: one that was made, or one the short gate held more than SHORT_HOLD_RETRIES times."""
    held = {}; made = set()
    for r in _rows():
        k = str(r.get("premise", "")).strip().lower()
        if _failed(r): continue                                              # a crash says nothing about the topic
        if _held(r): held[k] = held.get(k, 0) + 1
        else: made.add(k)
    return made, {k for k, c in held.items() if c > max(0, S("SHORT_HOLD_RETRIES", int))}

def pick_topic(order=None):
    """The topic of the next Short: the winner's follow-up when one is ordered (with what the winner said, so the writers continue it), else the
    best premise on the bench that no Short has used."""
    st = store(); made, dropped = _spent_premises()
    if order:
        key = order.get("video_key"); said = next((str(s.get("script") or "") for s in st.rows("Specials") if s.get("id") == key), "")
        return {"premise": _order_premise(order), "origin": "breakout", "follow_of": key, "said": said}
    from whatifs import premise as PRM                                  # READY rows only, best first (STALE / USED never come back)
    bench = [b for b in PRM.bench_rows(mark_stale=False) if b.get("premise") and b["premise"].strip().lower() not in (made | dropped)]
    if bench: return {"premise": bench[0]["premise"], "origin": "bench", "bench_id": bench[0].get("bench_id")}
    return None

def hook_for(fmt, hist, ep=None):
    """The hook archetype of the next Short: the learning core picks among the archetypes a Short may open on, never one that made the same pair
    (format, hook) as either of the last two Shorts - so formats and hooks rotate by code, whatever the learning core prefers. The draw is seeded
    by the Short's id (ep): one id always gives the same Short, so a fault seen once can be reproduced (the rule of the whole offline pipeline)."""
    from whatifs import brain as BR
    import hashlib
    taken = {(str(h.get("format")), str(h.get("hook"))) for h in hist[:2]}
    opts = [h for h in FMT.SHORT_HOOKS if (fmt, h) not in taken] or list(FMT.SHORT_HOOKS)
    seed = int(hashlib.sha1(str(ep).encode()).hexdigest()[:8], 16) if ep else None
    c = BR.choose("hook", "short", options=opts, seed=seed) if S("BRAIN_ON", bool) else {"level": S("BRAIN_DEFAULT_HOOK"), "holdout": False}
    if c.get("level") not in opts: c = dict(c, level=opts[0], holdout=False)          # the control hook was taken (or is the trial's own): the first free one
    return c

def _still_size():
    """A vertical 9:16 picture as large as the long side of the long video's stills (multiples of 16)."""
    h = S("STILL_W", int) // 16 * 16; return int(h * 9 / 16) // 16 * 16, h

def est_inr(fmt):
    """What one Short of this format costs, said BEFORE anything is paid: every second but the loop's is a paid clip of the hero model."""
    from whatifs import media as MD
    fx = S("USD_INR", float) or 92.0; lo, hi = FMT.short_len(fmt); sec = (lo + hi) / 2; nb = max(1, len(FMT.SHORTS[fmt]["beats"]) - 1)
    clips = nb * max(1, math.ceil(max(0.0, sec - SEAT.CLIP_S) / nb / (SEAT.CLIP_S * SEAT.STRETCH_MAX) - 1e-6))          # the last beat is the loop: the first clip again, free
    pictures = nb if FMT.SHORTS[fmt]["camera"] == "cut" else 1
    return round(clips * S("PRICE_KLING_USD", float) * fx + pictures * MD.still_usd(*_still_size()) * fx + S("REPLAN_SHORT_INR", float), 1)

# ------------------------------------------------------------------ D14 write: three scripts in the format, judged blind, one fix
def valid(sc):
    """Has the reply the SHAPE that was asked for (code needs it to measure anything)? [] = yes."""
    if not isinstance(sc, dict): return ["not an object"]
    beats = sc.get("beats"); p = []
    if not str(sc.get("title") or "").strip(): p.append("no title")
    if not isinstance(beats, list) or not 3 <= len(beats) <= 6: return p + [f"{len(beats) if isinstance(beats, list) else 0} beats"]
    for i, b in enumerate(beats):
        if not isinstance(b, dict) or len(str(b.get("line") or "").split()) < 3: p.append(f"beat {i + 1} has no spoken line")
        elif not str(b.get("picture") or "").strip(): p.append(f"beat {i + 1} names no picture")
        elif not str(b.get("role") or "").strip(): p.append(f"beat {i + 1} has no role")
    return p

def write(topic, fmt, hook, ep, hist):
    """SHORTS_VARIANTS scripts in the Short's format (one call each, nobody sees another's answer). A script the viewer's seat finds clean goes to the
    blind jury (strong judges of two model families see every candidate); the winner gets ONE fix with every measured problem named."""
    from whatifs.models import ask_many, ask
    from whatifs import room2 as R2
    before = [f"{h.get('format')}: {FMT.opener(h.get('script'))}" for h in hist if str(h.get("script") or "").strip()]
    system = FMT.short_brief(fmt, hook, [b.split(": ", 1)[1] for b in before])
    base = f"PREMISE: {topic['premise']}\nSHORT FORMAT: {fmt} \"{FMT.short_name(fmt)}\"\n" + (f"EARLIER SHORTS (format: opener): {' | '.join(before)}\n" if before else "")
    if topic.get("origin") == "breakout":                              # v12 V2c-b: the follow-up of a winner continues it - a repeat would be held by short_kept
        base += ("THIS IS THE FOLLOW-UP OF A SHORT THAT REAL VIEWERS STAYED FOR. Write the NEXT Short for those viewers: the next consequence, or the question it left open - "
                 "the same premise from a new side, never the same lines again.\n" + (f"THE WINNER SAID: {' / '.join(str(topic.get('said')).splitlines())[:600]}\n" if topic.get("said") else ""))
    n = max(1, S("SHORTS_VARIANTS", int))
    outs = ask_many([dict(role="short_writer", system=system, prompt=base + f"Variant {k + 1} of {n}: make it genuinely different from an obvious take.", episode=ep,
                          fake_key="short_script", max_tokens=1500) for k in range(n)])
    good = [o for o in outs if not valid(o)]
    if not good: raise RuntimeError("no Short script had the shape asked for: " + "; ".join(", ".join(valid(o)) for o in outs)[:200])
    clean = [g for g in good if not SEAT.script_issues(g, fmt, hist)]; pool = clean or good
    win, _info = R2.jury(["\n".join(FMT.short_lines(g)) for g in pool], FMT.short_rubric(fmt), f"Premise: {topic['premise']}", ep, "short")
    sc = dict(pool[win]); fixed = 0; left = SEAT.script_issues(sc, fmt, hist)
    if left:
        fx = ask("short_writer", system, base + "REWRITE this Short once. Keep the idea and what works; repair EXACTLY these measured problems:\n- " + "\n- ".join(left)
                 + "\nThe Short:\n" + json.dumps({k: sc.get(k) for k in ("title", "promise", "beats")}, ensure_ascii=False), episode=ep, fake_key="short_fix", max_tokens=1500)
        if not valid(fx): sc = dict(fx); fixed = 1
        left = SEAT.script_issues(sc, fmt, hist)
    sc["_write"] = {"variants": len(outs), "valid": len(good), "clean": len(clean), "fixed": fixed, "left": len(left)}
    return sc

def m_write(sc):
    w = dict((sc or {}).get("_write") or {}); hk = SEAT.hook(sc)
    return dict(w, words=len(" ".join(FMT.short_lines(sc)).split()), hook_words=len(hk.split()))

# ------------------------------------------------------------------ D7 short_voice: the long video's voice job, so the timeline is real
def voice(sc, ep, wd):
    """The guide speaks the Short through the long video's voice job: a real timeline (a unit per sentence, a time per word) and the breathing rule."""
    from whatifs import episode as EPI
    from whatifs.voice import narrate, Blend
    with FMT.using("F1"):                                                # a Short is never a trial: only the guide's voice is prepared, not the court's
        d = (EPI.speaker_blends() or {}).get(FMT.SHORT_VOICE) or EPI.blend()
    gv = getattr(d, "gvoice", "") or ("Gacrux" if FAKE else "")              # the rehearsal has no designed voices; live it must be the owner's designed voice
    if not gv and str(S("TTS_ENGINE") or "gemini").strip().lower() == "gemini": raise RuntimeError("no designed voice for the guide of a Short")
    d = Blend(d.name, d.parts, gvoice=gv, gstyle=getattr(d, "gstyle", ""))
    vo = narrate(FMT.short_text(sc), d, os.path.join(wd, "voice"), style=VOICE_STYLE, seed=f"{ep}|short", speaker_blends={FMT.SHORT_VOICE: d})
    with open(vo.timeline_path, encoding="utf-8") as f: tl = json.load(f)
    return {"wav": vo.wav_path, "timeline": tl, "seconds": float(vo.duration)}

def m_voice(v):
    tl = (v or {}).get("timeline") or {}; units = tl.get("units") or []
    words = sum(len(str(u.get("text") or "").split()) for u in units); speech = sum(float(u["end"]) - float(u["start"]) for u in units)
    return {"seconds": round(float((v or {}).get("seconds") or 0), 1), "sentences": len(units), "wpm": round(words / speech * 60) if speech > 0 else 0,
            "hook_end_s": round(float(units[0]["end"]), 2) if units else 0}

# ------------------------------------------------------------------ the plan: every second a clip, by code
def plan(sc, tl, fmt):
    """The pictures of a Short, planned by code from the script and the REAL voice timeline (no model is called): shots cover every second from 0.0;
    each is one clip of the hero model (CLIP_S seconds, played up to STRETCH_MAX slower when its shot is a little longer); the first clip of a beat
    starts on the beat's own picture (camera 'cut') or on the last frame of the clip before (inside a beat, and everywhere in a 'one_shot' format);
    the last beat - or its last seconds when it is long - is the FIRST clip played backwards, so the last frame is the first frame (the loop, free).
    No plate, no stock."""
    from whatifs.voice import parse_script
    units = tl.get("units") or []; lines = FMT.short_lines(sc); beats = [b for b in sc.get("beats") or [] if isinstance(b, dict)]
    total = round(float(tl.get("duration") or (float(units[-1]["end"]) + 0.6 if units else 0)), 2)
    starts, k = [], 0
    for i, l in enumerate(lines):                                            # where each beat begins on the real timeline (the voice job makes one unit per sentence)
        starts.append(0.0 if i == 0 else float(units[min(k, len(units) - 1)]["start"]) if units else 0.0)
        k += len(parse_script(f"[{FMT.SHORT_VOICE}] {l}"))
    cam = FMT.SHORTS[fmt]["camera"] if fmt in FMT.SHORTS else "cut"; C = SEAT.CLIP_S * SEAT.STRETCH_MAX          # the longest shot one clip can cover
    loop_at = round(min(max(starts[-1] if len(starts) > 1 else 0.0, total - C), max(0.0, total - 1.5)), 2)      # the loop shot: the last beat, or its last seconds when it is long
    bounds = starts + [total]; shots = []
    def pic(i): return str(beats[i].get("picture") or lines[i]).strip() if i < len(beats) else ""
    for bi in range(len(lines)):
        a = bounds[bi]; b = min(bounds[bi + 1], loop_at)
        if b - a < 0.05: continue
        n = max(1, math.ceil((b - a) / C - 1e-6)); step = (b - a) / n
        for j in range(n):
            src = "picture" if (not shots or (j == 0 and cam == "cut")) else "chain"
            shots.append({"i": len(shots), "beat": bi, "type": "kling", "src": src, "start": round(a + j * step, 2), "end": round(a + (j + 1) * step, 2), "picture": pic(bi)})
    if shots: shots.append({"i": len(shots), "beat": len(lines) - 1, "type": "kling", "src": "loop", "loop": True, "start": shots[-1]["end"], "end": total, "picture": pic(0)})
    return {"format": fmt, "seconds": total, "shots": shots, "captions": {"on": True, "margin": S("REEL_CAPTION_MARGIN_PCT", float)},
            "promise": {"text": " ".join(str(sc.get("promise") or "").split()), "at": 0.0}}

# ------------------------------------------------------------------ D14 make: the pictures, the clips, the loop, the captions, the sound
def _picture_prompt(text): return f"{text}. First person, eye level, vertical 9:16 frame, one place, real light. No text, no logo, no faces of people."

def _motion_prompt(text, src):
    from whatifs import anim as ANIM
    how = "The camera keeps moving forward from this exact frame, without a cut" if src == "chain" else "The impossible thing is already happening in the first frame; a slow first-person move forward"
    return f"{how}. {text}. {ANIM.AVOID}."

def _frame_at(clip, t, out):
    """The frame of a clip at second `t` (the picture the next clip starts on, so that the move continues)."""
    import cv2
    cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or FPS; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(n - 1, int(t * fps) - 1))); ok, fr = cap.read()
    if not ok: cap.set(cv2.CAP_PROP_POS_FRAMES, 0); ok, fr = cap.read()
    cap.release()
    if not ok: raise RuntimeError("the clip before has no readable frame to continue from")
    cv2.imwrite(out, fr); return out

def _slow(sec):
    """How much slower a clip is played to cover a shot of `sec` seconds (1.0 = as made)."""
    return max(1.0, float(sec) / SEAT.CLIP_S)

def _reverse(src, out, sec):
    """The first seconds of the first clip, played backwards (as many as the loop shot needs): it ENDS on the Short's first frame."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", f"{min(sec, SEAT.CLIP_S):.3f}", "-i", src, "-vf", f"fps={FPS},reverse", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out],
                   check=True, timeout=300)
    return out

def _ass(tl, path, promise, W, H, margin):
    """Captions word by word (the spoken word lights up) `margin` of the height above the bottom edge, and the promise text at the top from the first frame."""
    fs = int(H * 0.042); hs = int(H * 0.05)
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Cap,Anton,%d,&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,%d,2,2,60,60,%d,1\n"
            "Style: Hook,Anton,%d,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,%d,3,8,60,60,%d,1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n") % (W, H, fs, max(2, fs // 9), int(H * margin), hs, max(3, hs // 8), int(H * 0.12))
    def ts(t): h, m = int(t // 3600), int(t % 3600 // 60); return f"{h}:{m:02d}:{t % 60:05.2f}"
    ev = [f"Dialogue: 1,{ts(0)},{ts(2.6)},Hook,,0,0,0,,{promise.upper()}"] if promise else []
    for u in tl.get("units") or []:
        ws = u.get("words") or []
        if not ws:
            parts = str(u.get("text") or "").split(); d = (u["end"] - u["start"]) / max(1, len(parts))
            ws = [{"w": p, "s": u["start"] + i * d, "e": u["start"] + (i + 1) * d} for i, p in enumerate(parts)]
        for i in range(0, len(ws), 3):
            g = ws[i:i + 3]
            for j, cur in enumerate(g):
                end = g[j + 1]["s"] if j + 1 < len(g) else cur["e"]
                parts = [("{\\c&H0000D7FF&}" + str(x["w"]).upper() + "{\\r}") if k == j else str(x["w"]).upper() for k, x in enumerate(g)]
                ev.append(f"Dialogue: 0,{ts(cur['s'])},{ts(max(end, cur['s'] + 0.05))},Cap,,0,0,0,," + " ".join(parts))
    with open(path, "w", encoding="utf-8") as f: f.write(head + "\n".join(ev) + "\n")
    return path

def _loop_diff(path):
    """0..1: how different the last frame is from the first (0 = the same picture: the Short loops without a jump). Measured on the finished file, in
    the band of the picture that never carries words (LOOP_BAND): the promise text and the captions differ between the two frames by design."""
    import cv2, numpy as np
    cap = cv2.VideoCapture(path); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); ok0, a = cap.read(); b = None
    for back in range(1, 6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n - back)); ok1, b = cap.read()
        if ok1: break
    cap.release()
    if not ok0 or b is None: return 1.0
    a, b = (cv2.resize(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), (90, 160)).astype(np.float32)[int(160 * LOOP_BAND[0]):int(160 * LOOP_BAND[1])] for x in (a, b))
    return round(float(np.mean(np.abs(a - b))) / 255.0, 3)

def make(sc, v, pl, ep, wd):
    """The Short itself: each planned shot is one clip of the hero model, started on its own picture or on the frame the clip before ended on; the
    loop shot is the first clip played backwards (free); captions and the promise text are burned in; no plate at either end. Returns
    {path, seconds, clips, pictures, loop_diff}."""
    from whatifs import specials as SP, media as MD
    W, H = SP._vsize(); sw, sh = _still_size(); shots = pl["shots"]; clips = []; paid = pics = 0
    for s in shots:
        clip = os.path.join(wd, f"c{s['i']}.mp4"); sec = float(s["end"]) - float(s["start"])
        if s.get("src") == "loop": _reverse(clips[0], clip, sec)
        else:
            img = os.path.join(wd, f"f{s['i']}.png")
            if s.get("src") == "picture" or not clips: MD.still(_picture_prompt(s.get("picture") or ""), img, ep, seed=f"{ep}|{s['i']}", w=sw, h=sh); pics += 1
            else: _frame_at(clips[-1], min(SEAT.CLIP_S, float(shots[s["i"] - 1]["end"]) - float(shots[s["i"] - 1]["start"])), img)
            MD.animate(None, img, _motion_prompt(s.get("picture") or "", s.get("src")), clip, ep, hero=True); paid += 1
        clips.append(clip)
    tl = v["timeline"]; total = float(pl["seconds"])
    ass = _ass(tl, os.path.join(wd, "captions.ass"), str((pl.get("promise") or {}).get("text") or ""), W, H, float((pl.get("captions") or {}).get("margin") or SEAT.CAPTION_MIN))
    beat_secs = []
    for s in shots:
        if beat_secs and s["beat"] == last_beat: beat_secs[-1] += float(s["end"]) - float(s["start"])
        else: beat_secs.append(float(s["end"]) - float(s["start"]))
        last_beat = s["beat"]
    snd = SP._mix(SP._sound(total, beat_secs, os.path.join(wd, "bed.wav")), [(v["wav"], 0.0)], os.path.join(wd, "mix.wav"))
    fd = os.path.abspath("fonts") if os.path.isdir("fonts") else "/usr/share/fonts"
    if os.name == "nt": ass, fd = ("'" + p.replace("\\", "/").replace(":", "\\:") + "'" for p in (ass, fd))      # Windows dev laptops only: a drive colon breaks ffmpeg filter arguments
    inputs, filt = [], []
    for k, (s, c) in enumerate(zip(shots, clips)):
        inputs += ["-i", c]
        sec = float(s["end"]) - float(s["start"])
        filt.append(f"[{k}:v]setpts={_slow(sec):.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=6,"
                    f"trim=0:{sec:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{k}]")
    filt.append("".join(f"[v{k}]" for k in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0[body]")
    filt.append(f"[body]ass={ass}:fontsdir={fd}[vout]")
    out = os.path.join(wd, f"{ep}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-i", snd, "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", f"{len(clips)}:a", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True, timeout=900)
    return {"path": out, "seconds": round(total, 2), "clips": paid, "pictures": pics, "loop_diff": _loop_diff(out)}

def m_make(r):
    return {k: (r or {}).get(k, 0) for k in ("seconds", "clips", "pictures", "loop_diff")}

def make_lessons(r):
    """What the Shorts Studio must learn from a finished Short: a loop that did not close is reported as a failure of its own (the plan asked for it)."""
    d = float((r or {}).get("loop_diff") or 0)
    return [("loop_open", f"the last frame differs from the first by {d:.3f} (limit {LOOP_MAX}): the Short does not loop into its first picture")] if d > LOOP_MAX else []

def description(sc):
    """What stands under a Short: its title, its hook and how it was made - never an ask."""
    return f"{sc.get('title')}\n{SEAT.hook(sc)}\nOne law of nature is different today, and it happens to you. Reality Engine.\nAI-assisted pictures and voice; an original script."

# ------------------------------------------------------------------ the short gate: problems go to the department that owns the check, never to the owner
def _gate_memos(ep):
    """emit hook of the short gate: one problem memo per CLASS of failed check (no episode on it: a held Short is never made again under its id), to
    the department that owns the check. The next Short that passes the same check closes it."""
    from whatifs.org import registry as REG
    def emit(g, brief):
        return [{"type": "problem_memo", "from_dept": "D8", "to_depts": [REG.check_owner(fid)], "subject": f"{fid} held a Short at the short gate"[:140],
                 "body": {"what_failed": f"contract check {fid}: {str(ev)[:300]}", "where": f"{ep} short gate", "attempt": 1, "check": fid, "stage": "short"},
                 "done_when": f"a Short passes check {fid} at the short gate", "episode_id": "", "dedupe_key": f"gate|short|{fid}",
                 "evidence": [{"source": f"Feature_Ledger:{ep}:short:{fid}", "date": iso()[:10], "type": "own data", "finding": str(ev)[:300]}]}
                for fid, ev in ((g or {}).get("failed") or [])]
    return emit

def _gate_settle(ep):
    from whatifs.org import memos as MEM
    def settle(g, brief):
        rows = {r.get("feature"): r.get("status") for r in ((g or {}).get("rows") or [])}
        return [(m["id"], "repair_verified", f"Feature_Ledger:{ep}:short:{m['body'].get('check')}:PASS")
                for m in MEM.find(type="problem_memo", from_dept="D8", stage="short") if rows.get(m["body"].get("check")) == "PASS"]
    return settle

# ------------------------------------------------------------------ one Short, from the topic to the review or the upload
def run(force=False, publish=True, now=None, episode_id=None):
    """Make (and post, or send for review) one standalone Short. Returns a record. Order: the topic and its format -> D14 writes -> D7 voices ->
    code plans every second and D13 repairs the plan -> D8's short gate (nothing is paid for a picture before it; a held Short is NOT made and
    the owner is not asked) -> D14 makes it -> review or upload. episode_id = a fixed id (the sweep and the rehearsal); else the id is the minute."""
    from whatifs import specials as SP, brain as BR, contract as CON, governor as G, ladder as LAD
    from whatifs.org import runner as ORG, wraps as WR
    now = now or now_utc()
    if not force and not due(now): return {"ok": False, "skipped": "not due"}
    if publish:                                                                   # v12 V2c-b: the zero-cost upload check BEFORE the first paid call. Under "every topic starts as a Short" a Short is
        try:                                                                      # the first thing a new Sheet makes; before, only the long-video job ran the check, and no Short could be posted
            from whatifs import launch as LA
            if LA.due_check(): LA.upload_check()
            if LA.lock_state() == "on": log("upload lock is on: no Short is started (nothing spent)", "WARN"); return {"ok": False, "skipped": "upload_lock"}
        except Exception as e: log(f"upload check skipped: {scrub(e)[:100]}", "WARN")
    order = order_due(now)                                                        # v12 V2c-b: a winner's follow-up comes before the cadence (its clock is running)
    if not order and not force and not cadence(now)[0]: return {"ok": False, "skipped": "not due", "why": cadence(now)[1]}
    topic = pick_topic(order)
    if not topic: log("Shorts: no unused premise on the bench (the weekly research fills it)", "WARN"); return {"ok": False, "skipped": "no topic"}
    brk = topic.get("origin") == "breakout"
    ep = str(episode_id or f"{'BRK' if brk else 'SH'}{now:%Y%m%d%H%M}")                # BRK ids: every cost of a follow-up is charged to the breakout fund
    hist = history(); fmt = FMT.short_pick(ep, [h["format"] for h in hist]); choice = hook_for(fmt, hist, ep); arch = choice["level"]
    est = est_inr(fmt)
    ok, why = G.extras_allowed(est, kind="breakout") if brk else _budget_ok(est)
    if not ok:
        if brk: LAD.order_tried(topic["follow_of"], f"no money ({str(why)[:100]})", now)
        log(f"Shorts: paused ({why})", "WARN"); return {"ok": False, "skipped": "budget", "why": why}
    rec = {"ts": iso(now), "id": ep, "kind": "short", "title": "", "format": fmt, "ask": "", "yt_id": "", "ig": "", "fb": "", "status": "MADE", "views_7d": "", "file": "",
           "premise": topic["premise"], "hook": arch, "script": "", "sec": ""}
    try:
        wd = os.path.join(WORK, ep); os.makedirs(wd, exist_ok=True)
        with FMT.short_using(fmt):
            sc = ORG.work("D14", "write", ep, lambda b: write(topic, fmt, arch, ep, hist), measure=m_write, topic=fmt)
            rec.update(title=sc["title"], script="\n".join(FMT.short_lines(sc)))
            v = ORG.work("D7", "short_voice", ep, lambda b: voice(sc, ep, wd), measure=m_voice)
            pl = ORG.work("D13", "short_seat", ep, lambda b: SEAT.shape(plan(sc, v["timeline"], fmt), sc, fmt), measure=SEAT.m_shape)
            ctx = {"ep": ep, "short": {"script": sc, "format": fmt, "hook": arch, "units": v["timeline"].get("units") or [], "plan": pl, "last": hist}}
            g = ORG.work("D8", "short_gate", ep, lambda b: CON.run("short", ctx, ep), measure=WR.m_gate, lesson=WR.gate_lessons, emit=_gate_memos(ep), settle=_gate_settle(ep))
            rec["sec"] = pl.get("seconds")
            if not g["ok"]:
                failed = [f for f, _ in g["failed"]]
                store().append("Specials", [dict(rec, status=("HELD (" + ", ".join(failed) + ")")[:120])])
                log(f"Short {ep} ({fmt}) HELD at the short gate, not made, no picture paid: " + "; ".join(f"{f}: {str(e)[:90]}" for f, e in g["failed"][:4]), "WARN", ep)
                if brk: LAD.order_tried(topic["follow_of"], "held at the short gate (" + ", ".join(failed) + ")", now)
                return {"ok": False, "held": True, "id": ep, "kind": "short", "format": fmt, "failed": failed, "premise": topic["premise"]}
            made = ORG.work("D14", "make", ep, lambda b: make(sc, v, pl, ep, wd), measure=m_make, lesson=make_lessons)
        out = made["path"]
        footage = LAD.keep(ep, wd, sc, pl, v["timeline"])          # v12 V2c-b: what the Short was made of is kept - the opening of the long video its topic may earn
        BR.tag(ep, "short", title=sc["title"], premise=topic["premise"], hook=arch, sec=made["seconds"], lead=fmt, origin=topic.get("origin", "ai"),
               arm=choice.get("p_draws"), holdout=choice.get("holdout"))          # lead = the Short's FORMAT (nobody is on screen): the learning core compares S1, S2, S3
        BR.forecast(ep, "short", hook=arch)
        reviewed = sum(1 for r in _rows() if not _unmade(r))
        if publish and reviewed < S("SHORTS_REVIEW_FIRST_N", int):
            rec.update(SP._await_review(out, {"title": sc["title"]}, "short", ep, [{"who": "GUIDE", "line": l} for l in FMT.short_lines(sc)]))
        elif publish: rec.update(SP._publish(out, sc["title"], ep, desc=description(sc)))
        store().append("Specials", [rec])
        LAD.enter(rec, topic, footage)                         # v12 V2c-b: every Short is a step on the ladder - its numbers decide whether its topic gets the long video
        if brk: LAD.order_done(topic["follow_of"], ep, now)     # the order is closed with the Short that paid it (an approved long-video breakout has two)
        log(f"Short {ep} ({fmt} '{FMT.short_name(fmt)}', hook {arch}{', holdout' if choice.get('holdout') else ''}; {made['seconds']:.0f} s, {made['clips']} clips, loop {made['loop_diff']}): "
            f"{sc['title']} -> {rec['status']}", episode=ep)
        return dict(rec, ok=True, path=out)
    except Exception as e:
        if brk: LAD.order_tried(topic["follow_of"], f"the Short failed ({scrub(e)[:100]})", now)
        try: store().append("Specials", [dict(rec, status=("FAILED (" + scrub(e)[:90] + ")")[:120])])      # v12 V2c-b: a crashed Short is on record - the cadence waits a day before the next paid try
        except Exception: pass
        log(f"Short failed (nothing posted): {scrub(e)[:200]}", "WARN", ep); return {"ok": False, "why": scrub(e)[:200]}
