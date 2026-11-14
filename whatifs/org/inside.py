"""Inside the scene (D13): the voice is counted sentence by sentence - how much of it speaks to the viewer as something happening to him now, no lecture from outside, and every beat shows before it explains. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import re
from whatifs.core import S, log
from whatifs.org import audience as AUD

MIN_WORDS = 4                                              # a shorter sentence is a reaction and carries no viewpoint ("The ceiling arrives slowly." has four and counts)
_HEAD = re.compile(r"^\s*##\s*BEAT\b\s*(\d+)?", re.I)      # a beat heading; never spoken
YOU = re.compile(r"\b(you|your|yours|yourself|you're|you've|you'll|you'd)\b", re.I)
ME = re.compile(r"\b(i|i'm|i've|i'll|i'd|me|my|mine|myself|we|we're|we've|we'll|us|our|ours)\b", re.I)
EXPLAIN = re.compile(r"\b(because|that's why|which is why|the reason|this means|which means|in other words|is called|are called|known as|scientists|physicists|"
                     r"researchers|studies show|according to|in theory|technically|by definition)\b", re.I)
PAST = frozenset(("were", "had", "did", "went", "woke", "felt", "saw", "heard", "thought", "knew", "got", "took", "made", "came", "said", "looked", "walked", "opened",
                  "tried", "noticed", "reached", "stood", "sat", "ran", "fell", "found", "left", "turned", "watched"))
NOT_PAST = frozenset(("exceed", "proceed", "succeed", "embed", "bleed", "breed", "speed"))      # present-tense verbs that only look past ("need", "feed" have four letters)
_NOT_MEMORY = ("if", "wish", "imagine")                    # "if you were" is not a memory
_W = re.compile(r"[a-z']+")

def on():
    """Is the voice rule switched on (INSIDE_ON, with the viewer's seat)? Off = nothing is counted, told or repaired, and check viewer_inside says NA."""
    return AUD.on() and S("INSIDE_ON", bool)

# ------------------------------------------------------------------ the beat of a line, one convention for the whole batch
def line_beats(text):
    """(clean, beats): `clean` is the script without every line that starts with '##' (exactly what episode._strip_beats returns); `beats` holds, for each
    line of `clean` in order, its beat. A heading '## BEAT n' gives beat n (a real writer may skip or merge a beat), a heading without a number the beat
    before + 1; lines before any heading are beat 0."""
    lines, beats, cur = [], [], 0
    for raw in str(text or "").splitlines():
        if raw.strip().startswith("##"):
            m = _HEAD.match(raw)
            if m: cur = int(m.group(1)) if m.group(1) else cur + 1
            continue
        lines.append(raw); beats.append(cur)
    return "\n".join(lines), beats

# ------------------------------------------------------------------ the sentences, with the voice's own speaker parser
def _words(s):
    from whatifs.org import layman as LAY
    return LAY._TOK.findall(s)

def sentences(text):
    """[(sentence, speaker, beat)] of every COUNTED sentence (at least MIN_WORDS words): the units of voice.parse_script (its aliases, a label alone on its
    line, two speakers on one line - no second parser exists), each unit's spoken words cut into sentences by layman._SENT."""
    from whatifs import voice as VO
    from whatifs.org import layman as LAY
    clean, beats = line_beats(text)
    out = []
    for u in VO.parse_script(clean, line_beats=beats):
        for s in LAY._SENT.split(AUD.spoken(u.text)):
            s = s.strip()
            if len(_words(s)) >= MIN_WORDS: out.append((s, u.speaker, u.beat))
    return out

def past(sentence):
    """TRUE only for what code can RECOGNISE as a past 'you': the word 'you', at most one word ending in 'ly', then a verb of PAST or a word of five or more
    letters ending in 'ed' that is not in NOT_PAST - and not when one of the three words before 'you' is 'if', 'wish' or 'imagine'. Anything else is
    present (the rule errs toward the writer)."""
    w = _W.findall(str(sentence or "").lower())
    for i, t in enumerate(w):
        if t != "you" or any(x in _NOT_MEMORY for x in w[max(0, i - 3):i]): continue
        j = i + 1
        if j < len(w) and w[j].endswith("ly"): j += 1
        if j < len(w) and (w[j] in PAST or (len(w[j]) >= 5 and w[j].endswith("ed") and w[j] not in NOT_PAST)): return True
    return False

def is_inside(sentence, speaker, fmt):
    """Does this sentence put the viewer inside the scene? It speaks to 'you' now (YOU, not past) - or, in a format that is not a trial and has two voices,
    the foil (its second voice) says 'I' / 'we': the foil stands where the viewer stands. In a trial a character's 'I' is never the viewer's."""
    from whatifs import formats as FMT
    if YOU.search(sentence) and not past(sentence): return True
    f = FMT.FORMATS.get(str(fmt or ""))
    return bool(f and not f["show"] and len(f["voices"]) == 2 and speaker == f["voices"][1] and ME.search(sentence))

def _eight(s): return " ".join(str(s).split()[:8])

def report(text, fmt):
    """{n, inside, share_pct, min_pct, run, run_max, run_at, early, problems}: (a) the share of counted sentences inside the scene against the format's
    floor; (b) the longest run of counted sentences from outside against the format's limit; (c) in no beat does an explanation from outside come before
    the beat's first inside sentence (a beat that explains and never shows fails too). Seven or fewer counted sentences are not judged."""
    from whatifs import formats as FMT
    ss = sentences(text); n = len(ss); ins = [is_inside(s, spk, fmt) for s, spk, _b in ss]
    mn = FMT.inside_min(fmt); mx = FMT.lecture_max(fmt)
    run, best, best_at, at = 0, 0, "", ""
    for (s, _spk, _b), x in zip(ss, ins):
        if x: run = 0; continue
        if run == 0: at = s
        run += 1
        if run > best: best, best_at = run, at
    early, seen, shown = [], set(), set()
    for (s, _spk, b), x in zip(ss, ins):
        if x: shown.add(b); continue
        if b not in shown and b not in seen and EXPLAIN.search(s): seen.add(b); early.append((b, _eight(s)))
    share = round(100.0 * sum(ins) / n, 1) if n else 0.0
    p = []
    if n >= 8:
        if share < mn: p.append(f"only {sum(ins)} of {n} sentences ({share:g}%) speak to the viewer as something happening to him now (at least {mn:g}%)")
        if best > mx: p.append(f"{best} sentences in a row explain from outside (at most {mx}), from: '{_eight(best_at)}'")
        for b, words in early:
            p.append(f"beat {b} explains before it shows: '{words}'" if b in shown else f"beat {b} explains and never shows: '{words}'")
    return {"n": n, "inside": sum(ins), "share_pct": share, "min_pct": mn, "run": best, "run_max": mx, "run_at": _eight(best_at), "early": early, "problems": p}

def issues(text):
    """For the writers' ONE fix (enforce.fix_all, tag INSIDE FIX): one instruction, or [] when off, without a format or inside the rules."""
    from whatifs import formats as FMT
    k = FMT.current()
    if not on() or k not in FMT.FORMATS: return []
    r = report(text, k)
    if not r["problems"]: return []
    return ["INSIDE THE SCENE: " + "; ".join(r["problems"]) + ". Rewrite those sentences as what YOU see, feel or do, now, in the present tense ('your coffee lifts out of "
            "the cup'), keeping every fact; an explanation is said only after the viewer has seen the thing happen, in the same breath as it; never more than "
            + str(r["run_max"]) + " sentences in a row about anything but the viewer"]

def brief():
    """The writer's brief (beside the format's own text): the floor and the run limit of the format in the making; '' when off or without a format."""
    from whatifs import formats as FMT
    k = FMT.current()
    if not on() or k not in FMT.FORMATS: return ""
    return (f"INSIDE THE SCENE (code counts it; a script under it goes back): at least {FMT.inside_min(k):g}% of your sentences say what is happening to 'you' "
            f"right now, in the present tense; never more than {FMT.lecture_max(k)} sentences in a row from outside; every beat opens on what the viewer sees, "
            "and an explanation comes in the same breath as the thing it explains.")

# ------------------------------------------------------------------ the picture half of "show": every beat opens on a picture
def open_acts(shots, units):
    """Repair by code (in episode.produce right after D13's seat run, before the Animation Director): the shot of the first unit of every BEAT of the script
    (the units' own `beat`) whose type is 'graphic' or 'stock' becomes a still of its own line, exactly as audience.shape makes one (seat = 'a beat opens on
    a picture'). A marked shot (`short`, `promise`, `anim`) is never touched; a timeline without `beat` is left alone."""
    from whatifs import formats as FMT
    out = [dict(s) for s in shots or []]
    if not on() or FMT.current() not in FMT.FORMATS or not out or not units or any("beat" not in (u or {}) for u in units): return out
    seen, fixed = set(), 0
    for i, u in enumerate(units):
        b = u.get("beat")
        if b in seen: continue
        seen.add(b)
        if i >= len(out): break
        s = out[i]
        if s.get("type") in ("graphic", "stock") and not (s.get("short") or s.get("promise") or s.get("anim")):
            AUD.make_still(out, units, i, "a beat opens on a picture"); fixed += 1
    if fixed: log(f"inside the scene: {fixed} beat(s) opened on a graphic or real footage - each now opens on a picture of its own line")
    return out
