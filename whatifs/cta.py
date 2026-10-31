"""whatifs/cta.py v8.3 - the three audience asks (LIKE, SUBSCRIBE, SHARE), written as witty moments of the show itself.

Why: v8.2 had only one optional subscribe line and nothing for like or share. A viewer asks themselves "did I enjoy this?" at the moments right after a payoff,
and "who would love this?" at the end. So the asks are placed there, spoken by the two recurring roles in their own voices, and kept short.

How it works (three layers, so an ask is never missing and never ugly):
  1. The Showrunner's bible invents three premise-specific lines (the writer prompt places them: like ~40%, subscribe ~65%, share in the last 40 s).
  2. check()/ensure() verify by code that all three asks exist in the final script. A missing one is inserted from the hand-written pools below, at a calm
     moment (never right before or after a reaction, a reveal or a peak), rotating so two videos in a row never use the same line.
  3. Extras: a small code-drawn chip while the line is spoken (overlay.CtaChip), a witty description footer with a one-click subscribe link, and a follow / share ask
     at the end of each reel.
Nothing here calls an AI model or costs money. Everything is original text.
"""
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
        [("DIRECTOR", "calm", "We run a new simulation twice a week. Subscribe, and the bell does the remembering for you.")],
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
    "Subscribe: the control room runs twice a week, and we hate an empty chair.",
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
REEL_ASKS = {
    "follow": [("SKEPTIC", "aside", "Follow, so the simulation keeps running."), ("SKEPTIC", "aside", "Follow for the next impossible day."), ("DIRECTOR", "calm", "Follow, and see what breaks next.")],
    "share": [("SKEPTIC", "aside", "Send this to the friend who'd panic first."), ("DIRECTOR", "calm", "Share this with someone curious."), ("SKEPTIC", "aside", "Share it. Blame the Director.")],
}

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

def _safe_slot(lines, spoken, target):
    """The spoken-line number nearest to `target` after which an ask can sit without stepping on a reaction, a reveal or a peak."""
    info = []
    for i in spoken:
        spk, tag, _, text = _peel(lines[i]); info.append((spk, tag))
    n = len(spoken)
    def ok(p):
        if p < 1 or p >= n - 1: return False
        spk, tag = info[p]; nspk, ntag = info[p + 1]
        if tag not in _CALM_TAGS or ntag in _REACTION_TAGS or ntag in ("reveal",): return False
        if kind_of_text(_peel(lines[spoken[p]])[3]) or kind_of_text(_peel(lines[spoken[p + 1]])[3]): return False
        return True
    for d in range(0, 9):
        for p in (target - d, target + d):
            if ok(p): return p
    return max(1, min(n - 2, target))

def ensure(script, seed="", last=""):
    """Add whatever of the three asks is missing. Returns (new_script, added_kinds, picked) where picked is a short code ('l2,s5,h1') to remember for variety.
    Never raises; an unparsable script is returned unchanged."""
    try:
        have = check(script)
        if all(have.values()): return script, [], last
        lines = str(script).split("\n"); spoken = _spoken_index(lines)
        if len(spoken) < 8: return script, [], last
        rng = _rng(f"{seed}|cta"); prev = {p[0]: p[1:] for p in str(last or "").split(",") if len(p) > 1}
        picks, plan = {}, []
        for k in KINDS:
            if have[k]: continue
            pool = POOLS[k]; avoid = prev.get(CODE[k], "")
            choices = [i for i in range(len(pool)) if str(i) != avoid] or list(range(len(pool)))
            idx = rng.choice(choices); picks[k] = idx
            n = len(spoken); target = (n - 2) if k == "share" else int(n * POS[k])
            plan.append((_safe_slot(lines, spoken, target), k, idx))
        added = []
        for p, k, idx in sorted(plan, key=lambda x: -x[0]):          # from the end, so earlier insert points stay valid
            new = [_fmt(*t) for t in POOLS[k][idx]]
            lines[spoken[p] + 1:spoken[p] + 1] = new; added.append(k)
            spoken = _spoken_index(lines)
        code = ",".join(f"{CODE[k]}{picks[k]}" for k in picks)
        keep = ",".join(f"{CODE[k]}{prev[CODE[k]]}" for k in KINDS if CODE[k] in prev and k not in picks)
        return "\n".join(lines), sorted(added), ",".join(x for x in (code, keep) if x)
    except Exception:
        return script, [], last

def description_footer(seed, link=""):
    r = _rng(f"{seed}|desc"); sub = r.choice(DESC_SUB); sh = r.choice(DESC_SHARE)
    return sub + (f"\n{link}" if link else "") + "\n" + sh

def reel_ask(seed, k):
    """(speaker, tag, text) spoken at the very end of reel k: reel 1 asks to follow, reel 2 asks to share."""
    pool = REEL_ASKS["follow" if k % 2 == 0 else "share"]
    return _rng(f"{seed}|reel{k}").choice(pool)
