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
