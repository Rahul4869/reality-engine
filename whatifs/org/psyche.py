"""The psyche tags at making (v12 V4b step 7, D4): one vocabulary of drives, ONE tag call a video, the house constant never leads, the variety floor told first, repaired once, then held. See docs/CURRENT/SYSTEM.md."""
# v12 V4b step 7 (memo 3.7; item 142's before-launch part, items 185 and 188; D4): THE PSYCHE TAGS AT MAKING.
#
# One vocabulary of drives (data, DRIVES) and ONE tag call a video on route "psyche" - strong models of one family, no cheap fall-back (a label that
# can hold a video is never a cheap model's; hard rule 9): the premise, the title, the thumbnail text, the hook line and the first words of each beat get
# one drive each, and `lead` = the drive that carries the premise OTHER than the house constant (HOUSE: every video of the show is about the viewer).
# A missing or unknown value is asked ONCE more. Check psyche_tags (script stage) and short_psyche (short stage, DQ 4) hold a video whose tags are
# missing or outside the vocabulary after that retry, or whose lead is the house constant - read from the tags themselves, never from a flag.
# THE VARIETY FLOOR (step 7b; 02 item 145, his bound line: "no drive leads more than 2 of the last 5 long videos"; R15 on review 12a and 12b) binds
# EVERY long video, a free or a forced premise: told first (avoid() in the Showrunner's prompt and the writers' brief), repaired once (early(): one early
# tag of the chosen draft -> FEELING FIX on enforce.fix_all's one rewrite), then held at the script gate. A Short has no floor.
# The reading of wins and losses per drive, the weights and their flow are B8's. To serve the viewer, never to trick (C6).
# PSYCHE_TAGS_ON FALSE = no call, no line, no check: exactly the code before step 7.
from __future__ import annotations
import json, re
from whatifs.core import S, store, log

DRIVES = {
    "curiosity_gap": "a question the viewer needs answered",
    "unfinished_loop": "a story left open that the mind wants to close",
    "self_relevance": "it is about YOU: your body, your home, your day",
    "threat_survival": "danger, and what it takes to live through it",
    "awe_scale": "the vast and the impossible: a size, an age or a number far beyond the everyday",
    "surprise_humour": "the turn nobody saw coming, and the laugh it brings",
    "empathy_loss": "feeling for someone who loses something that matters",
    "justice_closure": "a wrong put right, a debt paid at last",
    "social_currency": "something worth telling a friend",
    "aspiration_power": "status and wish-fulfilment: YOU gain the power; a fantasy, never a get-rich claim",
}
HOUSE = ("self_relevance",)          # the house constant: every video is about the viewer - recorded on every tag set, never its lead
FLOOR_LAST = 4                       # the floor reads this many earlier long videos ...
FLOOR_MAX = 2                        # ... and holds a video whose lead already led this many of them (no drive leads more than 2 of the last 5)
LONG_KEYS = ("premise", "title", "thumb", "hook")
SHORT_KEYS = ("premise", "title", "hook")
EARLY_KEYS = ("premise",)
BEAT_WORDS = 40
BEAT_RX = re.compile(r"^[ \t]*##[ \t]*BEAT[ \t]*(\d+)[^\n]*$", re.M | re.I)

TAG_SYS = ("You label what a viewer FEELS first. Give each item below the ONE drive it pulls on first, from this closed list only (use the key):\n"
           + "\n".join(f"- {k}: {v}" for k, v in DRIVES.items())
           + "\nThen give `lead`: the drive that carries the PREMISE, other than self_relevance (every video of this show is about the viewer: that is the"
           " house constant, never a lead). Label honestly what is there; never what would sell. Return JSON only, with exactly the items given:"
           ' {"premise": key, "title": key, "thumb": key, "hook": key, "beats": {"<n>": key}, "lead": key}.')


def on(): return S("PSYCHE_TAGS_ON", bool)


def beats(script, words=BEAT_WORDS):
    """{n: the first `words` spoken words of '## BEAT n'} of a long script (bracket tags are not spoken)."""
    t = str(script or ""); ms = list(BEAT_RX.finditer(t)); out = {}
    for i, m in enumerate(ms):
        body = re.sub(r"\[[^\]]*\]", " ", t[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(t)])
        out[int(m.group(1))] = " ".join(body.split()[:words])
    return out


def first_line(text):
    """The hook line: the first spoken sentence of a script without its beat lines."""
    t = " ".join(re.sub(r"\[[^\]]*\]", " ", str(text or "")).split())
    m = re.match(r"(.+?[.?!])(\s|$)", t)
    return (m.group(1) if m else t)[:300]


def long_items(premise, title, thumb, hook, script):
    return {"premise": str(premise or ""), "title": str(title or ""), "thumb": str(thumb or ""), "hook": str(hook or ""), "beats": beats(script)}


def short_items(premise, title, lines):
    """A Short: the premise, the title and each beat's line; the hook is the first line."""
    L = [str(x).strip() for x in (lines or []) if str(x).strip()]
    return {"premise": str(premise or ""), "title": str(title or ""), "hook": L[0] if L else "", "beats": {i + 1: x for i, x in enumerate(L)}}


def _keys(items):
    return LONG_KEYS if "thumb" in items else SHORT_KEYS if "title" in items else EARLY_KEYS


def _bad(r, keys, want):
    """The values that are missing or outside DRIVES: the items in `keys`, `lead`, and every beat number in `want`."""
    r = r if isinstance(r, dict) else {}
    bt = r.get("beats") if isinstance(r.get("beats"), dict) else {}
    bt = {str(k): v for k, v in bt.items()}
    return [k for k in tuple(keys) + ("lead",) if r.get(k) not in DRIVES] + [f"beat {n}" for n in want if bt.get(str(n)) not in DRIVES]


def _prompt(items):
    L = [f"PREMISE: {items.get('premise')}"]
    if "title" in items: L.append(f"TITLE: {items.get('title')}")
    if "thumb" in items: L.append(f"THUMBNAIL TEXT: {items.get('thumb') or '(none)'}")
    if "hook" in items: L.append(f"HOOK LINE: {items.get('hook')}")
    bt = items.get("beats") or {}
    L += [f"BEAT {n}: {bt[n]}" for n in sorted(bt)]
    L.append("BEAT NUMBERS: " + ",".join(str(n) for n in sorted(bt)))
    return "\n".join(L)


def _ask(ep, items, again=False):
    from whatifs.models import ask
    try:
        return ask("psyche", TAG_SYS, _prompt(items) + ("\nLAST TIME SOME ITEMS HAD NO DRIVE OR ONE OUTSIDE THE LIST: give EVERY item one key of the list." if again else ""),
                   episode=ep, fake_key="psyche_tags", max_tokens=600, temperature=0.2)
    except Exception as e:                                     # the gate holds an untagged video: the failure is said, never hidden
        log(f"psyche: the tag call failed ({type(e).__name__}: {str(e)[:120]})", "WARN", ep); return {}


def tag(ep, items):
    """ONE call on route "psyche"; a missing or unknown value is asked ONCE more (never a third time). The result keeps every item's drive,
    `lead`, the beat numbers asked (`want`), "house": True (the house constant stands on every video) and what stayed bad (`unknown`)."""
    keys = _keys(items); want = sorted(int(n) for n in (items.get("beats") or {}))
    r = _ask(ep, items); bad = _bad(r, keys, want); asked = 1
    if bad:
        r = _ask(ep, items, again=True); bad = _bad(r, keys, want); asked = 2
    r = r if isinstance(r, dict) else {}
    bt = r.get("beats") if isinstance(r.get("beats"), dict) else {}
    out = {k: r.get(k) for k in keys + ("lead",)}
    out.update(beats={str(k): v for k, v in bt.items()}, want=want, house=True, unknown=bad, asked=asked)
    if bad: log(f"psyche: tags still missing or unknown after the one retry: {', '.join(bad)}", "WARN", ep)
    return out


def recent_leads(ep=None, n=FLOOR_LAST):
    """The leads of the newest `n` long videos on Video_Features (this one left out); a long video without tags is a video without a lead."""
    rows = [r for r in store().rows("Video_Features") if str(r.get("format") or "") == "long" and (not ep or r.get("video_key") != ep)][-n:]
    out = []
    for r in rows:
        try: dv = json.loads(r.get("drives") or "{}")
        except (TypeError, ValueError): dv = {}
        if isinstance(dv, dict) and dv.get("lead") in DRIVES: out.append(dv["lead"])
    return out


def avoided(ep=None):
    """The drives that led FLOOR_MAX of the last FLOOR_LAST long videos (DRIVES order): the next lead must be another."""
    if not on(): return []
    L = recent_leads(ep)
    return [k for k in DRIVES if L.count(k) >= FLOOR_MAX]


def least(ep=None):
    """The drive that led least in the last FLOOR_LAST long videos - never the house constant, never an avoided one (ties: DRIVES order)."""
    L = recent_leads(ep); av = avoided(ep)
    free = [k for k in DRIVES if k not in HOUSE and k not in av]
    return min(free, key=lambda k: (L.count(k), list(DRIVES).index(k)))


def avoid(ep=None):
    """TOLD FIRST: the line for the Showrunner's prompt and the writers' brief - for a free AND a forced premise - when a drive led 2 of the last 4."""
    av = avoided(ep)
    if not av: return ""
    return ("LEAD ON ANOTHER FEELING THAN " + " OR ".join(DRIVES[k] for k in av)
            + " THIS TIME: the premise stays word for word; what the viewer FEELS first changes.")


def early(ep, premise, script):
    """THE REPAIR BEFORE THE HOLD (R15 on review 12b; DQ 8): only when avoid() is not empty, ONE early tag call on the premise and the chosen draft's
    beats names the draft's lead; when it is an avoided drive or the house constant, the FEELING FIX line for enforce.fix_all's one rewrite.
    Returns (issues, the early lead)."""
    if not avoided(ep): return [], ""
    r = _ask(ep, {"premise": str(premise or ""), "beats": beats(script)})
    lead = str((r if isinstance(r, dict) else {}).get("lead") or "")
    if lead in DRIVES and lead not in HOUSE and lead not in avoided(ep): return [], lead
    x = DRIVES.get(lead) or "the same feeling as the last long videos"
    return [f"Lead on another feeling than {x}: open the first two beats on {DRIVES[least(ep)]}; keep the premise and every fact."], lead


def problems(dr, ep=None, long=True):
    """What check psyche_tags (long=True) / short_psyche (long=False) finds, read from the tags themselves: no tags; a tag missing or outside the
    vocabulary; the house constant as lead; and for a long video the variety floor - this lead already led FLOOR_MAX of the last FLOOR_LAST."""
    if not isinstance(dr, dict) or not dr: return ["no psyche tags were made for this video"]
    keys = LONG_KEYS if long else SHORT_KEYS
    want = dr.get("want") if isinstance(dr.get("want"), list) else []
    out = []
    bad = _bad(dr, keys, want) + ([] if want else ["beats (none asked)"])
    if bad: out.append("tags missing or outside the vocabulary after the one retry: " + ", ".join(bad))
    if dr.get("lead") in HOUSE: out.append(f"the lead is the house constant ({dr.get('lead')}): every video is about the viewer - the lead must be another drive")
    if long and dr.get("lead") in DRIVES:
        n = recent_leads(ep).count(dr["lead"])
        if n >= FLOOR_MAX: out.append(f"the variety floor: {dr['lead']} already led {n} of the last {FLOOR_LAST} long videos (no drive leads more than {FLOOR_MAX} of {FLOOR_LAST + 1})")
    return out
