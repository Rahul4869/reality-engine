"""Audience (D13): the viewer's seat - what a first-time viewer would meet is measured by code and repaired by code before any picture is paid: the promise as the first picture, a voice that breathes, few numbers. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import re
from whatifs.core import S, log

PICTURES = ("still", "living", "kling")                    # shot types that show a made picture (a graphic is drawn numbers, stock is somebody else's footage)
SLACK = 1.25                                               # the voice is judged on the real timeline; the pauses are planned on an estimate of it
_SMALL = ("two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
          "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "dozen", "half", "twice", "double", "triple")
_BIG = ("hundred", "thousand", "million", "billion", "trillion", "percent")
_LABEL_WORDS = ("hour", "day", "week", "month", "year", "minute", "second", "phase", "step", "stage", "exhibit", "beat", "act", "part", "chapter", "case", "no",
                "number", "prototype", "level", "round", "rule", "law")   # "hour 1", "day 3", "Prototype No 41": a place in the story, not a statistic
_JOIN = ("one", "a", "point", "and", "of", "per", "cent")  # words that continue a number only next to one ("one point four", "a hundred", "two and a half")
_WORD = re.compile(r"\d[\d,]*(?:\.\d+)?%?|[A-Za-z']+")
_TAGS = re.compile(r"\[[^\]\n]{0,40}\]|\{[^}\n]{0,40}\}")
_LABEL = re.compile(r"(?m)^\s*\**[A-Z][A-Za-z .']{1,24}:\**\s*")

def on():
    """Is the viewer's seat switched on (VIEWER_SEAT_ON)? Off = nothing is repaired and its three checks say NA."""
    return S("VIEWER_SEAT_ON", bool)

# ------------------------------------------------------------------ numbers: what a viewer hears and reads
def spoken(text):
    """The words a viewer hears: headings, stage directions, delivery tags, show tags and speaker labels are never spoken."""
    lines = [l for l in str(text or "").split("\n") if not l.strip().startswith(("#", "[SFX", "[MUSIC", "("))]
    return _LABEL.sub(" ", _TAGS.sub(" ", "\n".join(lines)))

def count_numbers(text):
    """How many QUANTITIES a viewer hears. A figure in digits, a number word (two ... ninety, hundred ... trillion, percent, half, twice ...) or a run
    of them ("one point four million" = ONE number). Not counted: 'one' and 'a' alone, the year of a source (1993, 2023) and a place in the story
    ("hour 1", "day 3", "Exhibit 2", "Prototype No 41") - those orient the viewer, they are not statistics."""
    n = 0; run = False
    toks = [t.lower() for t in _WORD.findall(spoken(text))]
    def year(t): return t.isdigit() and len(t) == 4 and 1500 <= int(t) <= 2099
    for i, t in enumerate(toks):
        num = (t[0].isdigit() or t in _SMALL or t in _BIG) and not year(t)
        if num and not run and i and toks[i - 1] in _LABEL_WORDS and (t.isdigit() or t in _SMALL): num = False
        if num:
            if not run: n += 1
            run = True
        elif run and t in _JOIN and i + 1 < len(toks) and (toks[i + 1][0].isdigit() or toks[i + 1] in _SMALL or toks[i + 1] in _BIG or toks[i + 1] in _JOIN): pass
        else: run = False
    return n

def _minutes(text, units=None):
    try:
        end = max(float(u.get("end") or 0) for u in units or [])
        if end > 0: return end / 60.0
    except (TypeError, ValueError, AttributeError): pass
    return max(0.05, len(spoken(text).split()) / max(60.0, S("WPM_ESTIMATE", float)))

def _start(units, i):
    try: return float(units[i].get("start", units[i].get("t0", 0)) or 0)
    except (TypeError, ValueError, AttributeError, IndexError): return 0.0

def numbers_report(text, shots=None, units=None):
    """{numbers, per_min, max_per_min, graphics, graphics_max, first_graphic_s, free_s, problems}: the numbers a viewer hears per minute and the
    full-screen number graphics he must read (how many, and how early the first one comes)."""
    n = count_numbers(text); mins = _minutes(text, units); per = round(n / mins, 2); mx = S("NUMBERS_PER_MIN_MAX", float)
    g = [i for i, s in enumerate(shots or []) if s.get("type") == "graphic"]; gmax = S("GRAPHICS_MAX_LONG", int); free = S("GRAPHICS_FREE_SEC", float)
    first = min((_start(units or [], i) for i in g), default=None) if units else None
    p = []
    if per > mx: p.append(f"{n} numbers in {mins:.1f} min of speech = {per:.1f} a minute (limit {mx:g})")
    if shots is not None and len(g) > gmax: p.append(f"{len(g)} full-screen number graphics (limit {gmax})")
    if first is not None and first < free: p.append(f"a number graphic at {first:.0f} s (none before {free:.0f} s)")
    return {"numbers": n, "per_min": per, "max_per_min": mx, "graphics": len(g), "graphics_max": gmax, "first_graphic_s": first, "free_s": free, "problems": p}

def number_issues(text):
    """For the writers' one mandatory fix: the numbers problem as an instruction a rewrite can follow ([] = inside the budget or the seat is off)."""
    if not on(): return []
    r = numbers_report(text)
    if r["per_min"] <= r["max_per_min"]: return []
    keep = max(1, int(r["max_per_min"] * _minutes(text)))
    return [f"TOO MANY NUMBERS: a viewer hears {r['numbers']} numbers ({r['per_min']:.1f} a minute, limit {r['max_per_min']:g}). Keep the {keep} the story cannot lose, turn each "
            "into something a viewer can picture (a comparison, a size, a wait), never two numbers in one sentence, and cut the rest"]

# ------------------------------------------------------------------ the shot list: the promise is the first picture, numbers on screen are rare
def make_still(out, units, i, why, hero=False, prompt=""):
    """Shot i of the shot list `out` becomes a still of its own line (the prompt it had, else its line's words; the style lock added), carrying 'seat' = why.
    One helper for every repair by code that turns a graphic or real footage into a picture (audience.shape, inside.open_acts)."""
    lock = str(S("STYLE_LOCK") or "").strip()
    def text(i): return str((units[i] if i < len(units or []) else {}).get("text") or "")
    s = out[i]; p = (prompt or str(s.get("prompt") or "").strip() or text(i)).strip()
    if lock and lock not in p: p = p.rstrip(". ") + ". " + lock
    s.update(type="still", prompt=p, hero=bool(hero), seat=why); s.pop("graphic", None); s.pop("search", None)

def shape(shots, units, pkg=None):
    """Repairs by code before any picture is paid (D13's run, right before the Animation Director): the first shot is a made picture (so that the
    animated promise scene can open the video), no number graphic inside the first GRAPHICS_FREE_SEC seconds, at most GRAPHICS_MAX_LONG in the video.
    A graphic that goes becomes a still of its own line. No model is called; the still usually reuses an earlier picture, and where the opening or
    the repetition guard wants a fresh one it costs a still (under Rs 1; 2 in the fake episode). Returns the new shot list; each repaired shot
    carries 'seat' = why."""
    out = [dict(s) for s in shots or []]
    if not on() or not out: return out
    thumb = str((pkg or {}).get("thumb_prompt") or "").strip()
    def still(i, why, hero=False, prompt=""): make_still(out, units, i, why, hero=hero, prompt=prompt)
    if out[0].get("type") not in PICTURES: still(0, "first picture", hero=True, prompt=thumb)
    free = S("GRAPHICS_FREE_SEC", float); gmax = max(0, S("GRAPHICS_MAX_LONG", int)); kept = 0
    for i, s in enumerate(out):
        if s.get("type") != "graphic": continue
        if _start(units or [], i) < free: still(i, "number graphic too early")
        elif kept >= gmax: still(i, "number graphic over the budget")
        else: kept += 1
    fixed = [s["seat"] for s in out if s.get("seat")]
    if fixed: log(f"viewer's seat: {len(fixed)} repair(s) by code before any picture is paid: " + ", ".join(f"{fixed.count(w)} x {w}" for w in dict.fromkeys(fixed)))
    return out

def m_shape(shots):
    """Measures of D13's run (they become its takeaway)."""
    seat = [s.get("seat") for s in shots or [] if s.get("seat")]
    return {"shots": len(shots or []), "repaired": len(seat), "graphics_left": sum(1 for s in shots or [] if s.get("type") == "graphic"),
            "graphics_removed": sum(1 for w in seat if "graphic" in w), "first_is_picture": int(bool(shots) and shots[0].get("type") in PICTURES)}

# ------------------------------------------------------------------ the voice breathes
def _ends_sentence(u):
    t = str(getattr(u, "text", "") or "").rstrip(); return bool(t) and t[-1] in ".!?\"'" and not float(getattr(u, "hesitate_after", 0) or 0)

def breathe(units):
    """Voice units (before the voice is made): a pause of BREATH_PAUSE_S is placed at a sentence start whenever the voice has run about BREATH_EVERY_S
    without one - at a paragraph start when one comes in time, else at the next sentence. Pauses the writer already asked for count. Costs nothing."""
    if not on() or not units: return units
    every = max(5.0, S("BREATH_EVERY_S", float)); pause = S("BREATH_PAUSE_S", float); mn = S("BREATH_PAUSE_MIN_S", float); wpm = max(60.0, S("WPM_ESTIMATE", float))
    since = 0.0; added = 0
    for i, u in enumerate(units):
        gb = float(getattr(u, "gap_before", 0) or 0)
        if i and gb >= mn: since = 0.0
        elif i and _ends_sentence(units[i - 1]) and ((getattr(u, "new_para", False) and since >= every * 0.5) or since >= every * 0.8):
            u.gap_before = max(gb, pause); since = 0.0; added += 1
        since += len(str(u.text).split()) / wpm * 60 + 0.35
    if added: log(f"viewer's seat: {added} breathing pause(s) of {pause:g} s placed in the voice (one at least every {every:g} s)")
    return units

def breath_report(units):
    """{longest_s, pauses, limit_s, wpm, problems} from the REAL voice timeline: the longest stretch of speech without a pause of BREATH_PAUSE_MIN_S,
    and the pace. None when the timeline carries no times."""
    try: tl = [(float(u["start"]), float(u["end"]), str(u.get("text") or "")) for u in units or []]
    except (KeyError, TypeError, ValueError): return None
    if len(tl) < 2 or tl[-1][1] <= 0: return None
    mn = S("BREATH_PAUSE_MIN_S", float); lim = S("BREATH_EVERY_S", float) * SLACK
    mark = tl[0][0]; longest = 0.0; pauses = 0
    for (s0, e0, _t0), (s1, _e1, _t1) in zip(tl, tl[1:]):
        if s1 - e0 >= mn - 1e-6: longest = max(longest, e0 - mark); mark = s1; pauses += 1
    longest = max(longest, tl[-1][1] - mark)
    speech = sum(e - s for s, e, _t in tl); words = sum(len(t.split()) for _s, _e, t in tl)
    p = [f"the voice runs {longest:.0f} s without a pause of {mn:g} s (limit {lim:.0f} s)"] if longest > lim else []
    return {"longest_s": round(longest, 1), "pauses": pauses, "limit_s": round(lim, 1), "wpm": round(words / speech * 60) if speech > 0 else 0, "problems": p}
