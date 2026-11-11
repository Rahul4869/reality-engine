"""Audience (D13): the viewer's seat for a Short - the first frame, the hook, plain words, the shape and the loop are measured by code and repaired by code before any picture is paid. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import re
from whatifs.core import S, log
from whatifs import formats as FMT
from whatifs.org import audience as AUD, layman as LAY

CLIP_S = 5.0               # one clip of the hero model
STRETCH_MAX = 1.3          # a clip may be played up to this much slower to cover its shot (a beat of 6.5 s is ONE paid clip, not two)
LEAD_S = 0.35              # the voice job starts speaking this long after the first frame
CAPTION_MIN = 0.30         # captions sit at least this share of the height above the bottom edge (the platform's buttons and title cover the lowest part)
ANIMATED = ("kling",)      # the one shot type a Short is made of: a made picture animated by the hero model
SOURCES = ("picture", "chain", "loop")      # a clip starts on its own picture, on the last frame of the clip before, or it is the first clip returning
# What code can RECOGNISE as an ask or a greeting (a Short has neither). Ordinary sentences never match: "you would like it", "follow the light".
ASK_RX = re.compile(r"\b(subscrib\w*|follow (?:us|me|for more|the channel|this channel)|like (?:and|this video|the video|this short)|hit (?:the|that) (?:like|bell|button)\w*|"
                    r"smash\w* (?:the|that)|comment (?:below|down|your)|in the comments|link in (?:the |my |our )?(?:bio|description)|(?:the )?full (?:video|episode|trial|story)|"
                    r"on (?:our|my|this) channel|share this|turn on notifications|for part (?:two|2)|watch (?:the )?next)\b", re.I)
GREET_RX = re.compile(r"^\W*(?:hi|hey|hello|welcome|what'?s up|good (?:morning|evening))\b|\b(?:welcome (?:back )?to|in this (?:video|short)|today we|my name is)\b", re.I)

def on():
    """Is the viewer's seat for a Short switched on (SHORT_SEAT_ON, and the viewer's seat itself)? Off = nothing is repaired and its checks say NA."""
    return AUD.on() and S("SHORT_SEAT_ON", bool)

def sentences(text):
    return [s.strip() for s in LAY._SENT.split(" ".join(AUD.spoken(text).split())) if s.strip()]

def hook(sc):
    """The hook: the first spoken sentence of the Short."""
    lines = FMT.short_lines(sc); ss = sentences(lines[0]) if lines else []
    return ss[0] if ss else ""

def _wps(): return max(60.0, S("WPM_ESTIMATE", float)) / 60.0

def _hook_end(units, n_words):
    """When the hook ENDS on the real voice timeline: the end of the unit in which its last word is spoken (None when the timeline has no times)."""
    seen = 0
    try:
        for u in units or []:
            seen += len(str(u.get("text") or "").split())
            if seen >= max(1, n_words): return float(u["end"])
    except (KeyError, TypeError, ValueError, AttributeError): return None
    return None

# ------------------------------------------------------------------ the opening: the first frame and the first three seconds
def open_report(sc, units=None, plan=None):
    """{hook, hook_words, hook_end_s, problems}: the hook has at most SHORT_HOOK_WORDS_MAX words, is no greeting, and ENDS inside SHORT_HOOK_BY_S
    seconds of the real voice (`units`); the plan (when given) starts at 0.0 on an animated made picture - the promise picture - and the promise
    text is on screen inside the first second (SHORT_PROMISE_TEXT_ON)."""
    hk = hook(sc); n = len(hk.split()); mx = S("SHORT_HOOK_WORDS_MAX", int); by = S("SHORT_HOOK_BY_S", float); p = []
    end = _hook_end(units, n) if units else None
    if not hk: p.append("the Short has no first sentence")
    else:
        if n > mx: p.append(f"the hook has {n} words (limit {mx}): '{hk[:80]}'")
        if GREET_RX.search(hk): p.append(f"the Short opens with a greeting or an introduction instead of the hook: '{hk[:60]}'")
    if end is not None and end > by + 1e-6: p.append(f"the hook ends at {end:.1f} s of the voice (limit {by:g} s)")
    if plan is not None:
        shots = plan.get("shots") or []
        if not shots: p.append("there is no picture plan")
        else:
            s0 = shots[0]
            if float(s0.get("start") or 0) > 0.05: p.append(f"the first picture starts at {float(s0.get('start') or 0):.1f} s: the Short opens on nothing")
            if s0.get("type") not in ANIMATED: p.append(f"the Short opens on a {s0.get('type')}, not on the moving impossible picture")
            elif s0.get("src") != "picture": p.append("the first clip is not made from the promise picture")
        if S("SHORT_PROMISE_TEXT_ON", bool):
            pr = plan.get("promise") or {}; txt = str(pr.get("text") or "").strip(); pw = S("SHORT_PROMISE_WORDS_MAX", int)
            if not txt: p.append("no promise text for the first frame")
            elif len(txt.split()) > pw: p.append(f"the promise text has {len(txt.split())} words (limit {pw})")
            elif float(pr.get("at") or 0) > 1.0: p.append(f"the promise text appears at {float(pr.get('at') or 0):.1f} s (inside the first second)")
    return {"hook": hk, "hook_words": n, "hook_max": mx, "hook_end_s": None if end is None else round(end, 2), "hook_by_s": by, "problems": p}

# ------------------------------------------------------------------ plain: one number at most, no expert word
def plain_report(sc):
    """{numbers, hard, problems}: the numbers a viewer hears (limit SHORT_NUMBERS_MAX) and the expert words a layman would not know (limit
    SHORT_EXPERT_MAX; the layman measure). Nothing is exempt: a swiping viewer did not choose a title."""
    text = FMT.short_text(sc); n = AUD.count_numbers(text); nm = S("SHORT_NUMBERS_MAX", int); em = S("SHORT_EXPERT_MAX", int)
    hard = list(dict.fromkeys(LAY._key(w) for w, _s, _k in LAY.hard_words(text))) if LAY.on() else []
    p = []
    if n > nm: p.append(f"{n} numbers heard (limit {nm})")
    if len(hard) > em: p.append(f"{len(hard)} expert word(s) a layman would not know (limit {em}): {', '.join(hard[:6])}")
    return {"numbers": n, "numbers_max": nm, "hard": hard, "hard_max": em, "problems": p}

# ------------------------------------------------------------------ shape: the length, the hand-back, no ask, every second animated, the loop, captions
def _seconds(units=None, plan=None):
    try:
        if plan and float(plan.get("seconds") or 0) > 0: return float(plan["seconds"])
        if units: return float(units[-1]["end"])
    except (KeyError, TypeError, ValueError, IndexError): pass
    return None

def shape_report(sc, fmt, units=None, plan=None):
    """{seconds, band, words, asks, handback, problems}: the real length inside the format's band; the last line hands back to the first (a content
    word of the opening line returns in it); no ask; and - on the plan - every second is an animated clip of the hero model with no gap, no stock
    and no plate, the last shot is the first clip returning (the loop), and the captions are on, above the platform's buttons."""
    lines = FMT.short_lines(sc); lo, hi = FMT.short_len(fmt) if fmt in FMT.SHORTS else (S("SHORT_MIN_S", float), S("SHORT_MIN_S", float))
    sec = _seconds(units, plan); words = len(AUD.spoken(FMT.short_text(sc)).split()); p = []
    if sec is not None and sec < lo - 0.05: p.append(f"the Short is {sec:.0f} s long (format {fmt}: {lo:g} to {hi:g} s)")
    if sec is not None and sec > hi + 0.05: p.append(f"the Short is {sec:.0f} s long (format {fmt}: {lo:g} to {hi:g} s)")
    asks = list(dict.fromkeys(m.group(0).lower() for l in lines for m in ASK_RX.finditer(AUD.spoken(l))))
    if asks: p.append(f"an ask in a Short: {', '.join(repr(a) for a in asks[:4])}")
    back = sorted(LAY._stems(lines[0]) & LAY._stems(lines[-1])) if len(lines) >= 2 else []
    if len(lines) >= 2 and not back: p.append("the last line does not hand back to the first picture: no word of the opening line returns in it")
    if plan is not None:
        shots = plan.get("shots") or []; at = 0.0
        for s in shots:
            a, b = float(s.get("start") or 0), float(s.get("end") or 0)
            if s.get("type") == "stock": p.append(f"stock footage at {a:.0f} s: a Short is made of our own animated pictures")
            elif s.get("type") not in ANIMATED: p.append(f"a {s.get('type')} at {a:.0f} s is not animated")
            if a - at > 0.05: p.append(f"nothing is on screen from {at:.1f} to {a:.1f} s")
            if b - a > CLIP_S * STRETCH_MAX + 0.05: p.append(f"one clip is asked to cover {b - a:.1f} s (a clip is {CLIP_S:g} s and may be slowed to {CLIP_S * STRETCH_MAX:g} s)")
            at = max(at, b)
        if shots and sec is not None and at < sec - 0.05: p.append(f"the pictures end at {at:.1f} s, the Short at {sec:.1f} s")
        if not (shots and shots[-1].get("loop") and shots[-1].get("src") == "loop"): p.append("the last shot is not the first picture returning: the Short does not loop")
        cap = plan.get("captions") or {}
        if not cap.get("on"): p.append("the captions are off")
        elif float(cap.get("margin") or 0) < CAPTION_MIN - 1e-9: p.append(f"the captions sit at {float(cap.get('margin') or 0):.0%} of the height, under the platform's buttons (at least {CAPTION_MIN:.0%})")
    return {"seconds": None if sec is None else round(sec, 1), "band": (lo, hi), "words": words, "asks": asks, "handback": back, "problems": p[:8]}

# ------------------------------------------------------------------ the writers' one fix: everything a rewrite can repair, named
def script_issues(sc, fmt, last=()):
    """For the writers' ONE fix of a Short, before the voice is paid: the hook, the numbers, the expert words, the asks, the hand-back, the length by
    its word count, the format and the likeness - each as an instruction a rewrite can follow ([] = clean, or the seat is off)."""
    if not on(): return []
    out = []; o = open_report(sc); pl = plain_report(sc); sh = shape_report(sc, fmt); lo, hi = sh["band"]; wps = _wps()
    hp = list(o["problems"]); est = LEAD_S + o["hook_words"] / wps
    if o["hook"] and est > o["hook_by_s"] * 1.15: hp.append(f"the hook would take about {est:.1f} s to say (limit {o['hook_by_s']:g} s)")
    if hp: out.append("THE HOOK: " + "; ".join(hp) + f". The first sentence must have at most {o['hook_max']} words, be said inside {o['hook_by_s']:g} seconds and state the "
                      "impossible thing the first picture shows - no greeting, no introduction")
    if pl["problems"]: out.append("PLAIN WORDS: " + "; ".join(pl["problems"]) + f". Keep at most {pl['numbers_max']} number, turn any other into something a viewer can picture, and "
                                  "say what a thing DOES or looks like instead of its expert name")
    sp = list(sh["problems"]); wlo, whi = int(lo * wps * 0.8), int(hi * wps)
    if sh["words"] < wlo or sh["words"] > whi: sp.append(f"the Short has {sh['words']} words, about {sh['words'] / wps:.0f} s of speech (format {fmt}: {lo:g} to {hi:g} s, about {wlo} to {whi} words)")
    if sp: out.append("THE SHAPE: " + "; ".join(sp) + ". No ask of any kind; let a word of the first sentence return in the last line so that the Short loops; keep the length")
    return out + FMT.short_kept_issues(sc, fmt, last)

# ------------------------------------------------------------------ the plan: repaired by code before any picture is paid
def shape(plan, sc, fmt):
    """Repairs by code (D13's run, right before the short gate; no model is called and nothing is paid): a shot that is not an animated made picture
    becomes one, the first shot starts at 0.0 on the promise picture, the last shot is the first clip returning (the loop), the captions are on and
    above the platform's buttons, and the promise text is at most SHORT_PROMISE_WORDS_MAX words from the first frame (the title's first words when
    the writer gave none; no text at all when SHORT_PROMISE_TEXT_ON is off). Returns the new plan; 'seat' lists what was repaired."""
    out = dict(plan or {}); shots = [dict(s) for s in out.get("shots") or []]; out["shots"] = shots
    if not on() or not shots: return out
    fixed = []
    for s in shots:
        if s.get("type") not in ANIMATED:
            fixed.append(f"a {s.get('type')} made an animated picture"); s.update(type="kling", src="picture" if s.get("src") not in SOURCES else s["src"])
    if float(shots[0].get("start") or 0) > 0.05: fixed.append("the first picture moved to the first frame"); shots[0]["start"] = 0.0
    if shots[0].get("src") != "picture": fixed.append("the first clip made from the promise picture"); shots[0]["src"] = "picture"; shots[0].pop("loop", None)
    if len(shots) > 1 and not (shots[-1].get("loop") and shots[-1].get("src") == "loop"):
        fixed.append("the loop closed: the last shot is the first clip returning"); shots[-1].update(src="loop", loop=True)
    cap = dict(out.get("captions") or {})
    if not cap.get("on"): fixed.append("the captions switched on"); cap["on"] = True
    if float(cap.get("margin") or 0) < CAPTION_MIN: fixed.append("the captions lifted above the platform's buttons"); cap["margin"] = CAPTION_MIN
    out["captions"] = cap
    if S("SHORT_PROMISE_TEXT_ON", bool):
        pr = dict(out.get("promise") or {}); pw = max(1, S("SHORT_PROMISE_WORDS_MAX", int)); txt = " ".join(str(pr.get("text") or "").split())
        if not txt: txt = " ".join(str((sc or {}).get("title") or hook(sc)).split()[:pw]); fixed.append("the promise text taken from the title")
        if len(txt.split()) > pw: txt = " ".join(txt.split()[:pw]); fixed.append("the promise text cut to its first words")
        if float(pr.get("at") or 0) > 1.0: fixed.append("the promise text moved to the first frame")
        out["promise"] = {"text": txt.rstrip(" ,;:-"), "at": 0.0}
    else: out["promise"] = {"text": "", "at": 0.0}
    out["seat"] = fixed
    if fixed: log(f"viewer's seat (Short): {len(fixed)} repair(s) by code before any picture is paid: " + ", ".join(fixed))
    return out

def m_shape(plan):
    """Measures of D13's run for a Short (they become its takeaway)."""
    shots = (plan or {}).get("shots") or []
    return {"shots": len(shots), "repaired": len((plan or {}).get("seat") or []), "seconds": round(float((plan or {}).get("seconds") or 0), 1),
            "paid_clips": sum(1 for s in shots if s.get("src") != "loop"), "pictures": sum(1 for s in shots if s.get("src") == "picture"),
            "loop": int(bool(shots) and bool(shots[-1].get("loop")))}
