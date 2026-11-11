"""Formats: the show's formats as data - which one an episode is, what it tells the writers, and which devices it requires, allows or leaves out (the three-tier contract). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, os, re
from whatifs.core import S, store

# TIER 3 of the contract: the show's DEVICES. A format says for each one "must" (hard, holds the video), "advisory" (judged and reported, never holds) or
# "never" (not part of the format, not judged). Every other check is tier 1 (policy, accuracy, safety, money, technical quality, the organisation's
# own machinery) or tier 2 (the viewer's seat) and can NEVER be loosened by a format - a test proves no such id can enter a format's table.
DEVICES = ("joke_density", "send_and_awe", "emotion_beat", "audience_asks", "end_tease", "verdict_style", "time_ladder", "exhibits", "grimm_prototype", "verdict_line")
RULES = ("must", "advisory", "never")
_TRIAL = ("verdict_style", "time_ladder", "exhibits", "grimm_prototype", "verdict_line")          # the trial's own grammar: meaningless outside a trial
FORMATS = {
    "F1": {"name": "The day it changed", "status": "on", "show": False, "voices": ("DIRECTOR", "SKEPTIC"), "share": "FORMAT_SHARE_F1",
           "devices": dict({k: "never" for k in _TRIAL}, joke_density="advisory", send_and_awe="advisory", emotion_beat="advisory", audience_asks="advisory", end_tease="advisory")},
    "F2": {"name": "The trial", "status": "on", "show": True, "voices": ("DIRECTOR", "SKEPTIC", "JUDGE", "WITNESS"), "share": "FORMAT_SHARE_F2", "devices": {}},
    "F3": {"name": "The walk", "status": "later", "show": False, "voices": ("DIRECTOR",), "share": "FORMAT_SHARE_F3", "devices": {k: "never" for k in DEVICES}},
}
F1_SHOWRUNNER = ("FORMAT OF THIS EPISODE - F1 \"THE DAY IT CHANGED\" (not a trial: no court, no charge, no exhibits, no jury, no judge; return no show_plan). Choose and "
                 "phrase the premise as ONE day in which one law of nature is different, and it happens to the VIEWER, at home first. The thumbnail scene is the "
                 "impossible picture of that morning.")
F1_BIBLE = ("FORMAT OF THIS EPISODE - F1 \"THE DAY IT CHANGED\" (not a trial). The beats, in this order, each one bigger than the one before: (1) THE IMPOSSIBLE PICTURE - "
            "what you see or feel in the first seconds, in your own home; (2) YOUR MORNING - the first consequences in your body and your rooms; (3) YOUR STREET - "
            "what it does to the people and things around you; (4) THE WORLD - the planet-size consequence, with the one real piece of science that explains it; "
            "(5) THE LAST CONSEQUENCE - one beautiful or terrible thing nobody saw coming; (6) THE QUESTION - the viewer's own verdict: would you keep it? "
            "No courtroom, no charge, no exhibits, no jury in any beat.")
F1_WRITER = ("FORMAT OF THIS EPISODE - F1 \"THE DAY IT CHANGED\". This episode is NOT a trial: no court, no charge, no judge, no jury, no witness, no exhibits, no "
             "prototype, no verdict by anyone but the viewer - never those words. ONE law of nature is different today and it happens to YOU.\n"
             "STRUCTURE: the impossible picture FIRST (your own home, the first seconds) -> your morning -> your street -> the world, with the one real piece of "
             "science that explains it -> the last consequence nobody saw coming -> the question: would you keep it? Each step is bigger than the one before "
             "('but' / 'therefore', never 'and then'). ONE idea; whatever the idea does not need is cut.\n"
             "TWO VOICES ONLY: [DIRECTOR] is the guide - calm, exact, warm, speaking to 'you' in the present tense; [SKEPTIC] is the foil - doubts, teases, asks what "
             "the viewer would ask. Neither is named in the script and nobody else speaks. If the brief gives you a cast, use only the temperaments of its two "
             "leads; if it asks for a callback to an earlier video, make it one plain line without courtroom words.\n"
             "HUMOUR: at most three dry asides; never a joke to fill a gap.")
F1_DRAFTS = ("Rank these narrations for a first-person science what-if show (\"it happens to you\"), best first. Judge ONLY what a viewer would feel: (1) would a "
             "stranger keep watching after the first 10 seconds; (2) is the viewer INSIDE the scene - his home, his body, his day; (3) clear stakes and a curiosity "
             "gap that pays off; (4) escalation with 'but/therefore', no 'and then', each step bigger than the last; (5) accurate science in everyday words; "
             "(6) an ending that lands - a last consequence and a question worth answering. Ignore length differences. The narrations are anonymous; never "
             "guess who wrote them.")
F1_JOKES = ("Rank these alternative lines for ONE moment of a first-person science what-if show, best first. A great line is surprising, clear on one listen, dry "
            "rather than loud, true to the speaking voice, and lands its last word. Lines are anonymous.")
# what must not be HEARD in a format that is not a trial (names, the court and its furniture). Ordinary uses stay free: "verdict", "trial and error".
_TRIAL_RX = re.compile(r"\b(dr\.? grimm|grimm|inspector vale|nana rosa|the archivist|exhibit [a-h]\b|your honou?r|objection[!,.]|the jury|jurors?|the court(?:room)?\b|the charge\b|"
                       r"defendant|prosecut\w*|gavel|prototype no\b)", re.I)
_OTHER_VOICE = re.compile(r"\[(JUDGE|WITNESS)\]|(?m:^\s*(?:JUDGE|WITNESS|NANA ROSA|THE ARCHIVIST)\s*:)")
_CUR = {"key": ""}          # the format of the episode being made in this process (one job makes one episode at a time)

def on():
    """Are formats switched on (FORMATS_ON)? Off = every episode is made as before formats existed: the global switches decide (today's trial)."""
    return S("FORMATS_ON", bool)

def name(key): return FORMATS[key]["name"] if key in FORMATS else ""

def use(key):
    """Make `key` the format of the episode in the making ('' = none: the global switches decide)."""
    _CUR["key"] = key if key in FORMATS else ""

def current(): return _CUR["key"]

class using:
    """with formats.using("F1"): ... - the format for the work inside, the previous one restored afterwards."""
    def __init__(self, key): self.key = key
    def __enter__(self): self.prev = current(); use(self.key); return self
    def __exit__(self, *a): use(self.prev); return False

def show_allowed():
    """May the trial layer (whatifs/show.py) run for the episode in the making? Yes when no format is set, else what its format says."""
    k = current(); return True if not k else bool(FORMATS[k]["show"])

def rule(check, fmt=None):
    """'must' | 'advisory' | 'never' for a contract check in a format (default: the format in the making). Anything that is not a DEVICE is always 'must'."""
    k = current() if fmt is None else str(fmt or "")
    if k not in FORMATS or check not in DEVICES: return "must"
    return FORMATS[k]["devices"].get(check, "must")

# ------------------------------------------------------------------ which format an episode gets
def shares():
    """{format: share} of the formats that can be picked now: switched on, share above 0, and - for a format that needs the trial layer - SHOW_MODE = auto."""
    from whatifs import show as SHOW
    out = {}
    for k, f in FORMATS.items():
        if f["status"] != "on" or (f["show"] and not SHOW.leads_on()): continue
        v = max(0, S(f["share"], int))
        if v: out[k] = v
    return out

def _of_row(r):
    dj = r.get("draw_json")
    try: dj = json.loads(dj) if isinstance(dj, str) and dj.strip() else dj
    except ValueError: dj = None
    f = dj.get("format") if isinstance(dj, dict) else None
    return f if f in FORMATS else ""

def pick(episode, draw=None, st=None):
    """The format of a new episode. '' when formats are off. A Deep Trial is a trial. FORMAT_FORCE (or the env var WI_FORMAT) wins next. An episode that already had a format keeps
    it. Otherwise the format furthest below its share among the last ten episodes (so 70 / 30 is 7 and 3 of ten, not a coin); the very first episode of
    a Sheet is drawn by its id."""
    if not on(): return ""
    if (draw or {}).get("deep_trial"): return "F2"
    force = str(os.environ.get("WI_FORMAT") or S("FORMAT_FORCE") or "").strip().upper()          # the env var wins (a rehearsal or a sweep of one format)
    if force in FORMATS and FORMATS[force]["status"] == "on": return force
    sh = shares(); total = sum(sh.values())
    if not total: return "F1"
    rows = (st or store()).rows("Episodes"); hist = []
    for r in reversed(rows):
        f = _of_row(r)
        if not f: continue
        if str(r.get("episode_id")) == str(episode): return f
        if str(r.get("status") or "").upper() != "FAILED" and len(hist) < 10: hist.append(f)
    if not hist:
        x = int(hashlib.sha1(str(episode).encode("utf-8")).hexdigest(), 16) % total; acc = 0
        for k, v in sh.items():
            acc += v
            if x < acc: return k
    n = len(hist) + 1; order = list(sh)
    return max(order, key=lambda k: (round(sh[k] / total - hist.count(k) / n, 6), -order.index(k)))

# ------------------------------------------------------------------ what a format tells the writers and the juries
def block(role):
    """The format's own text for one room role ('showrunner' | 'bible' | 'writer'); '' for the trial (whatifs/show.py speaks for it) and when no format is set."""
    return {"showrunner": F1_SHOWRUNNER, "bible": F1_BIBLE, "writer": F1_WRITER}.get(role, "") if current() == "F1" else ""

def rubric(kind):
    """What the blind jury is asked to rank by ('drafts' | 'jokes') in the format in the making; '' = the room's own rubric (the trial)."""
    return {"drafts": F1_DRAFTS, "jokes": F1_JOKES}.get(kind, "") if current() in ("F1", "F3") else ""

# ------------------------------------------------------------------ is the script what its format says?
def kept_report(text, fmt, d=None):
    """{format, trial_words, other_voices, problems}: a script of a format that is not a trial must not sound like one (no name of the court's cast, no
    courtroom furniture, only the format's own voices); a trial needs its Show Plan."""
    from whatifs.org import audience as AUD
    fmt = str(fmt or ""); p = []; words, voices = [], []
    if fmt not in FORMATS: return {"format": "", "trial_words": [], "other_voices": [], "problems": []}
    if FORMATS[fmt]["show"]:
        if not (d or {}).get("show_plan"): p.append("the trial has no Show Plan")
    else:
        words = list(dict.fromkeys(m.group(0).lower().strip("!,. ") for m in _TRIAL_RX.finditer(AUD.spoken(text))))
        voices = sorted({(m.group(1) or m.group(0)).strip(" :[]\n").upper() for m in _OTHER_VOICE.finditer(str(text or ""))})
        if words: p.append(f"courtroom words in a script that is not a trial: {', '.join(words[:6])}")
        if voices: p.append(f"a voice that is not part of this format speaks: {', '.join(voices[:4])}")
    return {"format": fmt, "trial_words": words, "other_voices": voices, "problems": p}

def format_issues(text):
    """For the writers' one mandatory fix: the format problem of the episode in the making as an instruction a rewrite can follow ([] = none)."""
    k = current()
    if k not in FORMATS or FORMATS[k]["show"]: return []
    r = kept_report(text, k)
    if not r["problems"]: return []
    return [f"NOT A TRIAL: this episode's format is \"{name(k)}\" - " + "; ".join(r["problems"]) + ". Remove every courtroom element and name; only "
            + " and ".join(f"[{v}]" for v in FORMATS[k]["voices"]) + " speak; say the same things as something that happens to the viewer"]

# ------------------------------------------------------------------ SHORT FORMATS (v12 V2c): the short video is a product of its own, and its format is data too
# beats = the roles of the script's beats, in order; ending = what the last line must be; max_s = the cell that holds its longest length;
# camera: "cut" = every beat opens on its own picture, "one_shot" = every clip starts on the last frame of the clip before (one continuous move).
SHORT_HOOKS = ("you_pov", "verdict_first", "impossible_number", "countdown")      # the learning core's hook archetypes a Short may open on (never the trial's own)
SHORTS = {
    "S1": {"name": "The second it changed", "status": "on", "share": "SHORT_SHARE_S1", "max_s": "SHORT_MAX_S_S1", "camera": "cut",
           "beats": ("picture", "consequence", "consequence", "question"), "ending": "question"},
    "S2": {"name": "What would you do?", "status": "on", "share": "SHORT_SHARE_S2", "max_s": "SHORT_MAX_S_S2", "camera": "cut",
           "beats": ("power", "personal", "turn", "choice"), "ending": "choice"},
    "S3": {"name": "The whole thing in 30 seconds", "status": "on", "share": "SHORT_SHARE_S3", "max_s": "SHORT_MAX_S_S3", "camera": "one_shot",
           "beats": ("idea", "why", "scale", "return"), "ending": "return"},
}
SHORT_VOICE = "DIRECTOR"                                   # one guide speaks to "you"; nobody is on screen
SHORT_HOUSE = ("You write ONE standalone vertical Short (YouTube Shorts, Instagram Reels) for the channel Reality Engine: one law of nature is different and it happens to "
               "the VIEWER. He is swiping a feed and does not know what comes next: the first sentence and the first picture are everything.\n"
               "RULES. ONE voice, the guide, speaking to 'you' in the present tense. The FIRST sentence is the hook: at most {hook} words, short enough to be said inside "
               "{by:g} seconds, and it says the impossible thing the first picture shows. ONE idea; at most {nums} number in the whole Short; everyday words only - no expert "
               "word a viewer who never studied science would not know. No greeting, no channel name, and never an ask (no like, follow, subscribe, comment, 'full video', "
               "'link'). The LAST line hands back to the first picture: a word of the first sentence returns in it, so that the video loops into its own beginning. "
               "A complete story in {lo:g} to {hi:g} seconds of speech (about {wlo} to {whi} words) - never a trailer and never a cut-down of a longer video.\n"
               "PICTURES. Every beat names what the viewer SEES: first person, eye level, his own hands or body where natural, one place, real light; the impossible "
               "thing is already happening in the first frame. No faces of people, no text or logo in a picture, no courtroom.")
SHORT_BRIEF = {
    "S1": ("FORMAT S1 \"THE SECOND IT CHANGED\". Four beats, in this order, each bigger than the one before: (1) picture - the impossible picture in the viewer's own "
           "room, the second the law changes; (2) consequence - what it does to him in the next minute; (3) consequence - a bigger one, outside his door; (4) question - "
           "ONE open question to the viewer that hands back to the first picture. The last line ends with a question mark."),
    "S2": ("FORMAT S2 \"WHAT WOULD YOU DO?\". Four beats, in this order: (1) power - the viewer gains or loses ONE power, shown as a picture; (2) personal - it touches "
           "someone or something he loves; (3) turn - the price nobody mentions; (4) choice - his own choice between two things, asked as a question with 'or' in it "
           "('would you ... or ...?')."),
    "S3": ("FORMAT S3 \"THE WHOLE THING IN 30 SECONDS\". ONE big idea told as ONE continuous camera move through one place, without a cut. Four beats, in this order: "
           "(1) idea - the whole idea in the hook; (2) why - the one reason it is true, as a picture; (3) scale - how big it gets; (4) return - the camera arrives back "
           "where it started and the last line says what the viewer now sees differently. No question is needed."),
}
SHORT_JSON = ("JSON only: {{\"title\": \"<= 60 characters\", \"promise\": \"the promise in at most {pw} words, shown as text on the first frame\", \"beats\": [{{\"role\": "
              "\"<the beat's name from the format>\", \"line\": \"what the guide says\", \"picture\": \"what the viewer sees\"}}]}}")
SHORT_RUBRIC = ("Rank these scripts for a vertical Short of a first-person science what-if channel, best first, as a viewer swiping a feed. Judge ONLY what a viewer would "
                "feel: (1) would you stop on the first sentence; (2) does it happen to YOU; (3) one clear idea a stranger gets on one listen; (4) does every beat give the "
                "eye something new; (5) does the last line make you want to see the first picture again; (6) is it true to the science. Scripts are anonymous; never guess "
                "who wrote them.")
_SCUR = {"key": ""}          # the Short format of the Short being made in this process
_W3 = re.compile(r"[a-z']+")

def short_use(key):
    """Make `key` the format of the Short in the making ('' = none)."""
    _SCUR["key"] = key if key in SHORTS else ""

def short_current(): return _SCUR["key"]

class short_using:
    """with formats.short_using("S1"): ... - the Short format for the work inside, the previous one restored afterwards."""
    def __init__(self, key): self.key = key
    def __enter__(self): self.prev = short_current(); short_use(self.key); return self
    def __exit__(self, *a): short_use(self.prev); return False

def short_name(key): return SHORTS[key]["name"] if key in SHORTS else ""

def short_len(key):
    """(shortest, longest) seconds a Short of this format may be (SHORT_MIN_S and the format's own cell: levers of D14)."""
    lo = S("SHORT_MIN_S", float); hi = S(SHORTS[key]["max_s"], float) if key in SHORTS else lo
    return lo, max(lo, hi)

def short_shares():
    """{format: share} of the Short formats that can be picked now (switched on, share above 0)."""
    return {k: v for k, v in ((k, max(0, S(f["share"], int))) for k, f in SHORTS.items() if f["status"] == "on") if v}

def short_pick(episode, history=()):
    """The format of a new Short. SHORT_FORMAT_FORCE (or the env var WI_SHORT_FORMAT) wins. Otherwise the format furthest below its share among the last
    ten Shorts (`history`: their formats, newest first), so 40 / 40 / 20 is 4, 4 and 2 of ten and never a coin; the first Short of a Sheet is drawn by its id."""
    force = str(os.environ.get("WI_SHORT_FORMAT") or S("SHORT_FORMAT_FORCE") or "").strip().upper()
    if force in SHORTS and SHORTS[force]["status"] == "on": return force
    sh = short_shares(); total = sum(sh.values())
    if not total: return "S1"
    hist = [h for h in history if h in SHORTS][:10]
    if not hist:
        x = int(hashlib.sha1(str(episode).encode("utf-8")).hexdigest(), 16) % total; acc = 0
        for k, v in sh.items():
            acc += v
            if x < acc: return k
    n = len(hist) + 1; order = list(sh)
    return max(order, key=lambda k: (round(sh[k] / total - hist.count(k) / n, 6), -order.index(k)))

def short_brief(key, hook="", avoid=()):
    """The writer's brief of a Short in format `key`: the house rules with the seat's numbers, the format's beats, the hook archetype the learning core
    picked, the openers of the last Shorts to stay away from, and the JSON shape."""
    from whatifs import brain as BR
    lo, hi = short_len(key); wps = max(60.0, S("WPM_ESTIMATE", float)) / 60.0
    house = SHORT_HOUSE.format(hook=S("SHORT_HOOK_WORDS_MAX", int), by=S("SHORT_HOOK_BY_S", float), nums=S("SHORT_NUMBERS_MAX", int), lo=lo, hi=hi,
                               wlo=int(lo * wps * 0.9), whi=int(hi * wps * 0.85))
    arch = f"\nHOOK ARCHETYPE (for the first sentence): {hook} - {BR.HOOK_ARCHETYPES.get(hook, '')}." if hook else ""
    away = ("\nSTAY AWAY FROM THESE OPENERS (the last Shorts began with them; begin differently and build differently): " + "; ".join(f"'{a}'" for a in avoid if a) + "."
            if [a for a in avoid if a] else "")
    return house + "\n" + SHORT_BRIEF[key] + arch + away + "\n" + SHORT_JSON.format(pw=S("SHORT_PROMISE_WORDS_MAX", int))

def short_rubric(key=None): return SHORT_RUBRIC

def short_lines(sc):
    """The spoken lines of a Short script, one per beat."""
    return [str(b.get("line") or "").strip() for b in ((sc or {}).get("beats") or []) if isinstance(b, dict)]

def short_text(sc):
    """The Short as the voice job reads it: every line the guide's."""
    return "\n".join(f"[{SHORT_VOICE}] {l}" for l in short_lines(sc) if l)

def opener(text):
    """The first three spoken words, lower case (what a swiping viewer hears before he decides)."""
    from whatifs.org import audience as AUD
    return " ".join(_W3.findall(AUD.spoken(text).lower())[:3])

def likeness(a, b):
    """0..1: the share of three-word phrases two Shorts have in common (of all the phrases either of them has)."""
    from whatifs.org import audience as AUD
    def sh(t):
        w = _W3.findall(AUD.spoken(t).lower()); return {" ".join(w[i:i + 3]) for i in range(max(0, len(w) - 2))}
    x, y = sh(a), sh(b)
    return round(len(x & y) / len(x | y), 3) if x and y else 0.0

def short_kept_report(sc, fmt, hook="", last=()):
    """{format, roles, trial_words, alike, problems}: is the Short what its format says, and is it unlike the Shorts before it? The beats are the
    format's, in order; the ending is the format's (S1 a question, S2 a choice with 'or'); it does not sound like a trial and only the guide speaks;
    it shares less than SHORT_SIMILAR_MAX of its phrases with each of the last ten Shorts and does not open with the same three words as any of
    them; and the pair format + hook is not the pair of either of the last two (`last`: rows {id, format, hook, script}, newest first)."""
    from whatifs.org import audience as AUD
    fmt = str(fmt or ""); p = []
    if fmt not in SHORTS: return {"format": "", "roles": [], "trial_words": [], "alike": [], "problems": []}
    beats = [b for b in ((sc or {}).get("beats") or []) if isinstance(b, dict)]; want = list(SHORTS[fmt]["beats"])
    roles = [str(b.get("role") or "").strip().lower() for b in beats]; text = short_text(sc); lines = short_lines(sc)
    if roles != want: p.append(f"the beats are {', '.join(roles) or 'missing'}; format {fmt} is {', '.join(want)}, in this order")
    end = (lines[-1] if lines else "").rstrip(" \"')")
    if SHORTS[fmt]["ending"] == "question" and not end.endswith("?"): p.append("the last line is not a question to the viewer")
    if SHORTS[fmt]["ending"] == "choice" and not (end.endswith("?") and re.search(r"\bor\b", end, re.I)): p.append("the last line is not the viewer's choice between two things (a question with 'or')")
    words = list(dict.fromkeys(m.group(0).lower().strip("!,. ") for m in _TRIAL_RX.finditer(AUD.spoken(text))))
    raw = "\n".join(str(b.get("line") or "") for b in beats)
    voices = sorted({m.group(1).upper() for m in re.finditer(r"\[(SKEPTIC|JUDGE|WITNESS|NARRATOR)\]", raw)} | {(m.group(1) or m.group(0)).strip(" :[]\n").upper() for m in _OTHER_VOICE.finditer(raw)})
    if words: p.append(f"courtroom words in a Short: {', '.join(words[:6])}")
    if voices: p.append(f"another voice than the guide speaks: {', '.join(voices[:4])}")
    alike = []; lim = S("SHORT_SIMILAR_MAX", float); op = opener(text); rows = [r for r in last if isinstance(r, dict)][:10]
    for r in rows:
        other = str(r.get("script") or "")
        if not other.strip(): continue
        lk = likeness(text, other)
        if lk >= lim: alike.append(str(r.get("id") or "")); p.append(f"it reads like Short {r.get('id')}: {lk:.0%} of the three-word phrases are the same (limit {lim:.0%})")
        elif op and op == opener(other): alike.append(str(r.get("id") or "")); p.append(f"it opens with the same three words as Short {r.get('id')} ('{op}')")
    if hook and (fmt, str(hook)) in [(str(r.get("format") or ""), str(r.get("hook") or "")) for r in rows[:2]]:
        p.append(f"format {fmt} with the hook '{hook}' was one of the last two Shorts: the pick must rotate")
    return {"format": fmt, "roles": roles, "trial_words": words, "alike": alike, "problems": p}

def short_kept_issues(sc, fmt, last=()):
    """For the writers' one fix: what a rewrite can repair about the format and the likeness ([] = none). The rotation of format and hook is the pick's
    duty, not the writer's, so it is never handed to him."""
    r = short_kept_report(sc, fmt, "", last)
    if not r["problems"]: return []
    return [f"NOT THE FORMAT, OR TOO MUCH LIKE AN EARLIER SHORT: this Short is format {fmt} \"{short_name(fmt)}\" - " + "; ".join(r["problems"])
            + f". Keep exactly the beats {', '.join(SHORTS[fmt]['beats'])} with that ending, one guide voice, no courtroom, and write it in other words than the earlier Shorts"]
