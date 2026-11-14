"""The three audience asks (like, subscribe, share), written as witty in-show moments and placed by rules. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import re, random, hashlib

KINDS = ("like", "subscribe", "share")

# What counts as an ask (kept strict so ordinary science sentences such as "they share a border" are never mistaken for one).
_RX = {
    "like": re.compile(r"\b(a like(?![\w-])|the like(?![\w-])|like button|thumbs?[- ]?up|hit like|tap like|smash like|like this|like it|drop a like|give it a like)\b", re.I),
    "subscribe": re.compile(r"\b(subscri\w*|hit the bell|notification bell|stay subscribed)\b", re.I),
    "share": re.compile(r"\b(share (this|it|the video)|send (this|it)\b|forward (this|it)|text (this|it)|pass (this|it) on|tell (a|one|your) friend)", re.I),
}
_REACTION_TAGS = ("wow", "gasp", "awe", "laugh", "doubt")
_CALM_TAGS = ("none", "calm", "aside", "callback", "patient")

def kind_of_text(text):
    """'like' | 'subscribe' | 'share' | None for one spoken line."""
    t = str(text or "")
    for k in ("subscribe", "share", "like"):
        if _RX[k].search(t): return k
    return None

# ------------------------------------------------------------------------------------------------------------------------------
# Hand-written pools: (speaker, delivery tag, text). One to two lines each, in the voices of the Director (calm expert) and the Curious One (honest, funny).
# ------------------------------------------------------------------------------------------------------------------------------
POOLS = {
    "like": [
        [("SKEPTIC", "aside", "Okay, tiny favor. If that last part rattled you, tap like. Nobody has to know you were scared.")],
        [("DIRECTOR", "aside", "If this simulation is earning its keep, the like button is right there. It's free. Unlike my coffee.")],
        [("SKEPTIC", "aside", "Every tap on the like button is basically a vote to keep running these. So, you know. Democracy."), ("DIRECTOR", "calm", "Please don't call it democracy.")],
        [("DIRECTOR", "calm", "Quick pause. A like tells the algorithm this was worth your time. Be honest, but be generous.")],
        [("SKEPTIC", "aside", "I did the math. Hit like and that is one tiny shove for this video. Shove away.")],
        [("SKEPTIC", "aside", "If your jaw dropped, tap like. If it didn't, tap like anyway. I'm flexible.")],
        [("SKEPTIC", "aside", "Thumbs up if you'd have survived that. Thumbs up anyway if you wouldn't.")],
        [("DIRECTOR", "aside", "Hit like if you want more simulations. Everything else is optional, including my dignity.")],
    ],
    "subscribe": [
        [("SKEPTIC", "aside", "Subscribe, and the next impossible thing lands in your feed. Don't, and I'll just wonder where you went."), ("DIRECTOR", "calm", "They will. Loudly.")],
        [("DIRECTOR", "calm", "We run a new simulation every week. Subscribe, and the bell does the remembering for you.")],
        [("SKEPTIC", "aside", "Subscribing is the only experiment here with a guaranteed result. You get more of this.")],
        [("DIRECTOR", "calm", "Think of subscribing as keeping the control room lights on. We'd like them on.")],
        [("SKEPTIC", "aside", "If you stuck around this long, you're basically crew. Subscribe and make it official."), ("DIRECTOR", "aside", "Crew gets no pay. But there are snacks. Imaginary snacks.")],
        [("SKEPTIC", "aside", "Subscribe. Future you will thank you. Past you was bored. Present you is still here, so.")],
        [("DIRECTOR", "calm", "The next simulation is already loading. Subscribe, so you're in the room when it runs.")],
        [("SKEPTIC", "aside", "Subscribe, or I keep asking. I have nothing else on. I live in a control room.")],
    ],
    "share": [
        [("DIRECTOR", "calm", "Last thing. Send this to the friend who would absolutely try it. You know exactly who.")],
        [("SKEPTIC", "aside", "Share this with whoever said that could never happen. Gently. Okay, not gently.")],
        [("DIRECTOR", "calm", "If this changed how you see an ordinary day, send it to one person. One is enough.")],
        [("SKEPTIC", "aside", "Forward this to the person who'd panic first. For science. And for me.")],
        [("DIRECTOR", "calm", "Know someone who asks 'what if' at dinner? Send this to them. Save the table.")],
        [("SKEPTIC", "aside", "Text this to your group chat and watch the arguments start. That's the real experiment.")],
        [("SKEPTIC", "aside", "Share it with one person. If it goes badly, blame the Director."), ("DIRECTOR", "aside", "I accept no responsibility.")],
        [("DIRECTOR", "calm", "A simulation only spreads if somebody passes it on. Send this to someone curious.")],
    ],
}
# Where each ask goes, as a share of the spoken lines. 'share' is placed relative to the END (before the final line) so the verdict keeps its weight.
POS = {"like": 0.40, "subscribe": 0.65}
CODE = {"like": "l", "subscribe": "s", "share": "h"}

DESC_SUB = [
    "Subscribe so the next simulation finds you before it finds the group chat.",
    "Subscribe: the control room runs every week, and we hate an empty chair.",
    "Subscribe, and future disasters arrive politely, in your feed.",
    "Subscribe. It costs nothing, and the Curious One will stop asking.",
    "Subscribe to keep the simulation running. The Director insists it is not a plea.",
    "Subscribe, if you want to know what breaks next.",
]
DESC_SHARE = [
    "Know someone who asks 'what if' at dinner? Send them this video.",
    "Send this to the friend who would try it. You know who.",
    "Share it with the person who said it could never happen.",
    "Pass it on to one curious person. One is plenty.",
]

# v9.3 (CTA_JURY_ON): the trial cast's own voices. [DIRECTOR] = Inspector Vale, [SKEPTIC] = Dr. Grimm, [JUDGE] = Nana Rosa. Subscribing = a seat on the jury
# (a recurring identity, not a favour). Same rules as POOLS: each entry is recognised as its kind, at most 34 words, no gendered words.
TRIAL_POOLS = {
    "like": [
        [("SKEPTIC", "aside", "Preposterous. And yet. If that rattled you, tap like. I will pretend I did not see it.")],
        [("JUDGE", "aside", "Mm. If you would have survived that, hit like. If you would not, hit like anyway. Sit down.")],
        [("DIRECTOR", "calm", "Observe. One tap on the like button keeps this court in session. The evidence suggests you enjoyed that.")],
        [("SKEPTIC", "aside", "Thumbs up if you are on my side. Thumbs up if you are not. I am counting either way.")],
        [("JUDGE", "calm", "The court notes your jaw dropped. A like makes it official. Mm.")],
        [("DIRECTOR", "aside", "If that changed your mind, the like button is the cheapest piece of evidence in this room.")],
    ],
    "subscribe": [
        [("JUDGE", "calm", "Subscribe, and you sit on the jury for every case. Jury duty, but with tea.")],
        [("SKEPTIC", "aside", "Subscribe, so you are seated when I win the next one. And I will win the next one."), ("DIRECTOR", "calm", "Noted. Every week, the same promise.")],
        [("DIRECTOR", "calm", "The next case is already filed. Subscribe, and your seat on the jury is saved.")],
        [("JUDGE", "aside", "Every juror who subscribes votes next time. Everyone else gets my disappointed look.")],
        [("SKEPTIC", "aside", "Subscribe. The court needs jurors who actually stay for the evidence. Rare. Precious. You.")],
        [("DIRECTOR", "calm", "Every week, a new impossible case. Subscribe, and the summons finds you first.")],
    ],
    "share": [
        [("JUDGE", "calm", "Send this to the friend who would vote guilty without reading the evidence. Mm. You know the one.")],
        [("SKEPTIC", "aside", "Share this with whoever still thinks I am wrong. Let them face the court.")],
        [("DIRECTOR", "calm", "Send this to one person who asks 'what if' at dinner. Every case deserves a witness.")],
        [("SKEPTIC", "aside", "Forward this to the person who would panic first. The jury needs drama.")],
        [("JUDGE", "aside", "Text this to your group chat. Then watch them argue. That is a trial too.")],
        [("DIRECTOR", "calm", "Share this with someone who would have guessed wrong. The record should show it.")],
    ],
}
TRIAL_DESC_SUB = [
    "Subscribe and take your seat on the jury: a new impossible case every week.",
    "Subscribe. Nana Rosa keeps a chair for every juror who stays for the evidence.",
    "Subscribe, so the next summons finds you before Dr. Grimm does.",
    "Subscribe to sit on the jury. Inspector Vale brings the evidence; you bring the verdict.",
]
TRIAL_DESC_SHARE = [
    "Send this case to the friend who would vote guilty without reading the evidence.",
    "Share it with the person who said it could never happen. Let the jury decide.",
    "Pass it on to one curious juror. One is plenty.",
]

# v12 V2b: WHAT CODE CAN RECOGNISE AS AN ASK - used by whatever DELETES a line or HOLDS a video (kind_of_text stays for "is one already there?", where a
# wrong yes costs nothing). Two cases only: (1) a line the code itself inserts (every line of POOLS / TRIAL_POOLS, a reply line as its entry's kind);
# (2) an imperative to subscribe, like, share or comment. A bell alone is never an ask (a doorbell, a bus bell). The rule errs toward the writer.
_LEAD = r"(?:^|[.!?]\s+)(?:(?:please|so|and|then|now|okay|ok),?\s+)*"
_WHO = r"(?:(?:a|the|that|your|one|some|any)\s+)?(?:friends?|person|people|someone|somebody|anyone|anybody|everyone|everybody|whoever|group chat|family)\b"
_ASK = (
    ("subscribe", re.compile("|".join((_LEAD + r"subscribe\b", r"\b(?:hit|tap|press|smash)\s+(?:the\s+|that\s+)?subscribe\b", r"\bsubscribe button\b",
                                        r"\bnotification bell\b", r"\b(?:don't forget|remember|make sure)\s+(?:you\s+)?to\s+subscribe\b")), re.I)),
    ("like", re.compile("|".join((_LEAD + r"(?:like this video|leave a like|drop a like|give (?:it|this) a like)\b", _LEAD + r"(?:hit|tap|smash)\s+like(?=\s+if\b|\s*[.!,;]|\s*$)",
                                   r"\blike button\b", r"\bthumbs?[- ]up if\b")), re.I)),
    ("share", re.compile("|".join((_LEAD + r"share (?:this|the) video\b", _LEAD + r"(?:share|send|forward|text|pass)\s+(?:this|it)(?:\s+video)?\s+(?:on\s+)?(?:to|with)\s+" + _WHO)), re.I)),
    ("comment", re.compile("|".join((r"\bin the comments?\b", _LEAD + r"(?:leave a comment|drop a comment|comment (?:down )?below)\b", _LEAD + r"follow (?:us|me) (?:on|for)\b",
                                     r"\bfollow (?:the channel|for more)\b")), re.I)),
)
def _norm(t): return " ".join(str(t or "").lower().split())
_OWN = {_norm(line[2]): kind for pools in (POOLS, TRIAL_POOLS) for kind, entries in pools.items() for entry in entries for line in entry}

def is_ask(text):
    """'like' | 'subscribe' | 'share' | 'comment' | None for one spoken line: yes only for a line the code inserts (its words equal a pool line's) or an
    imperative code recognises (_ASK)."""
    t = str(text or "")
    k = _OWN.get(_norm(t))
    if k: return k
    for kind, rx in _ASK:
        if rx.search(t): return kind
    return None

def _trial():
    """v9.3: the trial cast's lines are used when CTA_JURY_ON and the show format is on (SHOW_MODE = auto)."""
    try:
        from whatifs.core import S
        if not S("CTA_JURY_ON", bool): return False
        from whatifs import show as _SHOW
        return _SHOW.on()
    except Exception: return False

def _pools(): return TRIAL_POOLS if _trial() else POOLS

def _rng(seed): return random.Random(int(hashlib.md5(str(seed).encode()).hexdigest()[:12], 16))

def _fmt(spk, tag, text): return f"[{spk}] [{tag}] {text}"

# ------------------------------------------------------------------------------------------------------------------------------
def _spoken_index(lines):
    return [i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("##") and not l.strip().lower().startswith("[pause")]

def _peel(line):
    from whatifs.voice import _peel as p
    return p(line)

def check(script):
    """{'like': bool, 'subscribe': bool, 'share': bool} - which asks are already in the script (spoken lines only)."""
    have = {k: False for k in KINDS}
    for l in str(script or "").splitlines():
        if not l.strip() or l.strip().startswith("##"): continue
        _, _, _, text = _peel(l)
        k = kind_of_text(text)
        if k: have[k] = True
    return have

def strip(script, keep=(), tail_from=None):
    """v12 V2b: (script, removed) - every spoken line that is_ask names a kind NOT in `keep` is removed; and from spoken-line index `tail_from` on (the
    format's tail, formats.tail) every line that is_ask names ANY kind. `removed` lists the removed lines."""
    lines = str(script or "").split("\n"); drop = []
    for pos, i in enumerate(_spoken_index(lines)):
        k = is_ask(_peel(lines[i])[3])
        if k and (k not in keep or (tail_from is not None and pos >= tail_from)): drop.append(i)
    if not drop: return script, []
    gone = set(drop)
    return "\n".join(l for j, l in enumerate(lines) if j not in gone), [lines[i] for i in drop]

def _safe_slot(lines, spoken, target, before=None):
    """The spoken-line number nearest to `target` after which an ask can sit without stepping on a reaction, a reveal or a peak (v12 V2b: never at or
    after `before`)."""
    info = []
    for i in spoken:
        spk, tag, _, text = _peel(lines[i]); info.append((spk, tag))
    n = len(spoken)
    def ok(p):
        if p < 1 or p >= n - 1: return False
        if before is not None and p >= before: return False
        spk, tag = info[p]; nspk, ntag = info[p + 1]
        if tag not in _CALM_TAGS or ntag in _REACTION_TAGS or ntag in ("reveal",): return False
        if kind_of_text(_peel(lines[spoken[p]])[3]) or kind_of_text(_peel(lines[spoken[p + 1]])[3]): return False
        return True
    for d in range(0, 9):
        for p in (target - d, target + d):
            if ok(p): return p
    return max(1, min(n - 2, target))

def ensure(script, seed="", last="", kinds=None, before=None):
    """Add whatever of the three asks is missing. Returns (new_script, added_kinds, picked) where picked is a short code ('l2,s5,h1') to remember for variety.
    v12 V2b: only the missing kinds that are in `kinds` (None = all three) and never at or after the spoken line `before` (the format's tail).
    Never raises; an unparsable script is returned unchanged."""
    try:
        want = KINDS if kinds is None else tuple(k for k in KINDS if k in kinds)
        have = check(script)
        if all(have[k] for k in want): return script, [], last
        lines = str(script).split("\n"); spoken = _spoken_index(lines)
        if len(spoken) < 8: return script, [], last
        rng = _rng(f"{seed}|cta"); prev = {p[0]: p[1:] for p in str(last or "").split(",") if len(p) > 1}
        picks, plan = {}, []
        for k in want:
            if have[k]: continue
            pool = _pools()[k]; avoid = prev.get(CODE[k], "")
            choices = [i for i in range(len(pool)) if str(i) != avoid] or list(range(len(pool)))
            idx = rng.choice(choices)
            n = len(spoken); target = (n - 2) if k == "share" else int(n * POS[k])
            slot = _safe_slot(lines, spoken, target, before)
            if before is not None and slot >= before: continue          # no calm slot before the tail: nothing is added (DESIGN QUESTION 8 of V2b)
            picks[k] = idx; plan.append((slot, k, idx))
        added = []
        for p, k, idx in sorted(plan, key=lambda x: -x[0]):          # from the end, so earlier insert points stay valid
            new = [_fmt(*t) for t in _pools()[k][idx]]
            lines[spoken[p] + 1:spoken[p] + 1] = new; added.append(k)
            spoken = _spoken_index(lines)
        code = ",".join(f"{CODE[k]}{picks[k]}" for k in picks)
        keep = ",".join(f"{CODE[k]}{prev[CODE[k]]}" for k in KINDS if CODE[k] in prev and k not in picks)
        return "\n".join(lines), sorted(added), ",".join(x for x in (code, keep) if x)
    except Exception:
        return script, [], last

def description_footer(seed, link=""):
    r = _rng(f"{seed}|desc"); tr = _trial(); sub = r.choice(TRIAL_DESC_SUB if tr else DESC_SUB); sh = r.choice(TRIAL_DESC_SHARE if tr else DESC_SHARE)
    return sub + (f"\n{link}" if link else "") + "\n" + sh

