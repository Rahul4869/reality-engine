"""The maker's line (D7): one sentence of his own, asked at a topic's Short, spoken after a lead-in as the long video's last words and kept in its description - never cut, never mended. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, re
from whatifs.core import S, log, store, iso, scrub

MAIL_MAX = 200                     # characters of a tapped answer ('LINE <ref> <words>'): a longer title may have been cut on the mail route - refused unspoken
LEAD_SHORT = "And one answer, from the person who made this video."
LEAD_LONG = "One last thing. The person who made this video was asked, {q} Here is the answer."
CONSENT = "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."
QUESTION = "would you keep this world?"
_PAR = re.compile(r"The maker's answer: \"[^\n]*\"(?=\n|$)")      # THE ONE regular expression of his paragraph (find, report)
_URL = re.compile(r"https?://|www\.", re.I)
_QUOTES = "\"'“”‘’„«»"
ASK_WHY = ("your line asks the viewer to subscribe, like, share or comment, or points to another video: the film's last words carry neither - type your "
           "answer to the question")

def on():
    """Is his line asked, taken and spoken? It lives in the verdict's row, so his verdict must be on too."""
    return S("MAKER_LINE_ON", bool) and S("OWNER_VERDICT_ON", bool)

def question():
    """The question his line answers (cell MAKER_QUESTION) - used when it ends with '?' and holds none of [ ] { } < > :, else the default."""
    q = " ".join(str(S("MAKER_QUESTION") or "").split())
    return q if q.endswith("?") and not any(c in q for c in "[]{}<>:") else QUESTION

def usable(line):
    """(ok, why) - NEVER CUT, NEVER MENDED: a line is spoken as he typed it, or not at all. Judged on the line with its spaces made one."""
    from whatifs import voice as VO, cta as CTA, formats as FMT
    t = " ".join(str(line or "").split())
    if not t: return False, "the line is empty"
    if not any(c.isalpha() for c in t): return False, "nothing in it can be spoken"
    mx = S("MAKER_LINE_MAX_WORDS", int)
    if len(t.split()) > mx: return False, f"it has {len(t.split())} words: at most {mx} are spoken, and a line is never cut"
    if any(c in t for c in "[]{}"): return False, "it holds [ ] { }: the voice would read it as a stage direction"
    if any(c in t for c in "<>"): return False, "it holds < or >: YouTube removes these signs from a description"
    if "*" in t or "`" in t or "__" in t or not (t[0].isalnum() or t[0] in _QUOTES):
        return False, "it holds signs the voice strips (* ` __, or a sign at its start): your words would be spoken otherwise than you typed them"
    if _URL.search(t): return False, "it holds a web address"
    if VO._COLON_RE.match(t) or VO._STAGE_RE.match(t): return False, "it begins like a speaker's label or a stage direction: the voice would not speak those words"
    if CTA.is_ask(t) or FMT.TEASE.search(t): return False, ASK_WHY
    return True, ""

def lead(clean):
    """THE LEAD-IN FITS THE ENDING, CHOSEN ONCE: the short one only when the format ends on a question AND the script really ends on it (the film has just
    asked); in every other case the long one carries the question."""
    from whatifs import formats as FMT
    if S("ENDINGS_ON", bool) and FMT.ending() == "question":
        try: last = str(FMT.ending_report(clean, FMT.current()).get("last") or "")
        except Exception as e: log(f"maker's line: the script's last sentence was not read ({scrub(e)[:80]}) - the long lead-in", "WARN"); last = ""
        if last.rstrip().endswith("?"): return LEAD_SHORT
    return LEAD_LONG.format(q=question())

def leads():
    """The two lead-ins as they are said today."""
    return (LEAD_SHORT, LEAD_LONG.format(q=question()))

def E(x):
    """The unit texts the voice's own parser makes of one line spoken by the guide (the film was made with that parser)."""
    from whatifs import voice as VO
    return [u.text for u in VO.parse_script("[DIRECTOR] " + str(x))]

def k(mk):
    """How many units his lead-in and his line make (the voice cuts a line into one unit a sentence); 0 without a line."""
    if not mk: return 0
    from whatifs import voice as VO
    return len(VO.parse_script("[DIRECTOR] " + mk["lead"] + "\n[DIRECTOR] " + mk["line"]))

# ------------------------------------------------------------------ asked at the Short
def _ask_text(ref, title):
    return (f"Your own last words for '{title}' (optional): add ONE sentence after LINE {ref} in this link's title, or type it in tab Owner_Verdicts, row {ref}, "
            f"column maker_line. If viewers pick this topic it becomes a long video and your sentence ends it: {question()} At most 30 words through this link "
            f"(its title is a public page, like your line will be); up to {S('MAKER_LINE_MAX_WORDS', int)} words in the tab. No line from you = none in the video.")

def ask(ref, title, key=None):
    """The SECOND message at a Short's row (one message takes one answer): the how-to first - the digest shows 160 characters of a queued message."""
    from whatifs import notify as NT
    return NT.send("maker_line", _ask_text(ref, title), [("My line", f"LINE {ref}")], episode=ref, tier="week", expires_h=S("OWNER_VERDICT_EXPIRES_H", float),
                   dedupe_key=key or f"makerline|{ref}")

def late(topic):
    """Has the long video of this topic been planned already? (a row of tab Ladder with this topic is USED - DESIGN QUESTION 14)"""
    return bool(topic) and any(str(r.get("topic") or "") == str(topic) and r.get("state") == "USED" for r in store().rows("Ladder"))

def _sha(line): return hashlib.sha1(" ".join(str(line).split()).encode("utf-8")).hexdigest()[:8]

def typed(r):
    """sync's step (4): a line he TYPED in the tab, not seen yet - its `line_seen` is written by verdicts.sync; here it is judged and he is told once."""
    from whatifs.org import verdicts as VER
    line = " ".join(str(r.get("maker_line") or "").split()); ok, why = usable(line)
    title = r.get("title") or r.get("ref")
    if not ok: VER.note(r["ref"], f"refused|{_sha(line)}", "maker_line", f"Your line for '{title}' is not used: {why}. Your words stay in tab Owner_Verdicts, row {r['ref']}; type another there.")
    elif late(r.get("topic")): VER.note(r["ref"], "late", "maker_line", f"Your line for '{title}' came after its long video was planned: it is kept, but that video carries none.")

def _answer(row, choice):
    """His tap: LINE <ref> <words>. Words replace his older ones; a tap without words asks once more; a choice longer than MAIL_MAX may have been cut on
    the mail route and is refused unspoken."""
    from whatifs.org import verdicts as VER
    p = str(choice or "").split(None, 2); ref = str((row or {}).get("episode_id") or "")
    if len(p) >= 2 and p[0].upper() == "LINE":
        if ref and p[1] != ref: return f"That link is for {ref}: nothing was changed. Type your sentence after LINE {ref}, or in tab Owner_Verdicts, row {ref}, column maker_line."
        ref = ref or p[1]
    r = VER._row(ref)
    if r is None: return f"{ref}: no row on tab Owner_Verdicts - nothing kept"
    title = r.get("title") or ref
    if len(str(choice or "")) > MAIL_MAX:
        return f"Your sentence may have been cut on the mail route: type it in tab Owner_Verdicts, row {ref}, column maker_line."
    if len(p) < 3 or p[0].upper() != "LINE" or not p[2].strip():
        if not VER.told(ref, "line2"):
            ask(ref, title, key=f"makerline|{ref}|2")                   # the same ask, once more
            return f"No words came with your tap: type your sentence after LINE {ref} on the new message, or in tab Owner_Verdicts, row {ref}, column maker_line."
        return f"Type your sentence in tab Owner_Verdicts, row {ref}, column maker_line."
    words = p[2].strip(); line = " ".join(words.split())
    store().update(VER.TAB, "ref", ref, {"maker_line": words, "line_seen": iso()})
    ok, why = usable(line)
    if not ok:
        VER.told(ref, f"refused|{_sha(line)}")
        return f"Your line for '{title}' is not used: {why}. Type another after LINE {ref}, or in tab Owner_Verdicts, row {ref}, column maker_line."
    if late(r.get("topic")):
        if not VER.told(ref, "late"): return f"Your line for '{title}' came after its long video was planned: it is kept, but that video carries none."
        return f"Kept: \"{line}\" (its long video was planned already)."
    return f"Kept: \"{line}\". If viewers pick this topic, its long video ends on your sentence."

def register():
    from whatifs import notify as NT
    NT.register("maker_line", on_answer=_answer)

# ------------------------------------------------------------------ taken once, on record; into the voice; the mark
def take(d, ep, clean):
    """TAKEN ONCE, ON RECORD: the newest line of the draw's topic, if usable - its row's `line_used` = {ep, line} (written by code, never by him).
    An override has no Short: None."""
    from whatifs import ladder as LAD
    from whatifs.org import verdicts as VER
    lr = LAD.row(str((d or {}).get("ladder") or ""))
    if not lr or str(lr.get("state") or "").startswith("OVERRIDE"): return None
    topic = str(lr.get("topic") or "")
    rows = [r for r in store().rows(VER.TAB) if topic and str(r.get("topic") or "") == topic and str(r.get("maker_line") or "").strip()]
    if not rows: return None
    r = sorted(rows, key=lambda x: str(x.get("line_seen") or ""), reverse=True)[0]
    line = " ".join(str(r["maker_line"]).split()); ok, why = usable(line)
    if not ok: log(f"maker's line of {r['ref']} not taken: {why}", "WARN", ep); return None
    store().update(VER.TAB, "ref", r["ref"], {"line_used": json.dumps({"ep": ep, "line": line}, ensure_ascii=False)})
    log(f"maker's line taken from {r['ref']}: the film ends on it", episode=ep)
    return {"line": line, "ref": str(r["ref"]), "at": iso(), "lead": lead(clean)}

def attach(clean, beats, mk):
    """INTO THE VOICE, NOT INTO THE SCRIPT: (what the voice is given, its beats) - the script, a long pause, the lead-in and his line, both spoken by the
    guide; (clean, beats) without a line."""
    if not mk: return clean, beats
    voiced = clean + "\n[pause:long]\n[DIRECTOR] " + mk["lead"] + "\n[DIRECTOR] " + mk["line"]
    return voiced, (list(beats) + [beats[-1]] * 3) if beats else beats

def mark(shots, units, mk):
    """THE PICTURE UNDER HIS WORDS IS THE FILM'S LAST PICTURE: the list padded to the script's lines (as plan_check pads it) and cut there, then one still a
    unit of his, marked `maker`, carrying the prompt of the script's last picture - it buys nothing."""
    if not mk: return shots
    n = len(units) - k(mk)
    out = ([dict(s) for s in shots] + [{"type": "still", "prompt": u["text"], "unit": i} for i, u in enumerate(units[:n])][len(shots):])[:n]
    P = next((str(s["prompt"]) for s in reversed(out) if s.get("type") in ("still", "living", "kling") and str(s.get("prompt") or "").strip()), None)
    if P is None: P = str(units[n - 1]["text"]) if n > 0 else ""
    for i in range(n, len(units)):
        out.append({"unit": i, "type": "still", "prompt": P, "hero": False, "focus": "wide", "maker": True})
    return out

def script_units(shots, units):
    """The units of the script itself: everything before the first `maker` shot (all of them when none)."""
    if not units: return units
    m = next((i for i, s in enumerate(shots or []) if (s or {}).get("maker")), len(units))
    return units[:m]

# ------------------------------------------------------------------ the description, its translations
def paragraph(line): return f"The maker's answer: \"{line}\""

def find(description):
    """His paragraph when the text holds exactly one, else ''."""
    m = _PAR.findall(str(description or ""))
    return m[0] if len(m) == 1 else ""

# ------------------------------------------------------------------ the check (makers_line)
def _ends(texts, seq):
    return any(texts[i:i + len(seq)] == seq for i in range(0, len(texts) - len(seq) + 1)) if seq else False

def _lead_ok(x):
    if x == LEAD_SHORT: return True
    head, tail = LEAD_LONG.split("{q}")
    if not (x.startswith(head) and x.endswith(tail)): return False
    q = x[len(head):len(x) - len(tail)]
    return q.endswith("?") and not any(c in q for c in "[]{}<>:")

def report(units, description, mk, used, states, ep=None):
    """(ok, why) for check makers_line - it compares TEXT (the unit texts the voice's own parser makes), never word tokens."""
    texts = [str((u or {}).get("text") or "") for u in units or []]; desc = str(description or "")
    if not mk:
        if any(_ends(texts, E(x)) for x in leads()): return False, "the film speaks a maker's lead-in and no line of his is on record"
        if "The maker's answer: \"" in desc: return False, "the description carries a maker's answer and no line of his is on record"
        return True, "he gave no line for this topic: none is spoken, none is written"
    try: u_ = json.loads(used) if isinstance(used, str) and used.strip() else (used if isinstance(used, dict) else {})
    except Exception: u_ = {}
    if not u_ or (ep and str(u_.get("ep") or "") != str(ep)) or str(u_.get("line") or "") != str(mk.get("line") or ""):
        return False, "the line in this film is not on his record"
    want = E(mk.get("lead") or "") + E(mk.get("line") or ""); last = (units or [])[-len(want):] if want else []
    if not _lead_ok(str(mk.get("lead") or "")) or len(last) != len(want) or [str(u.get("text") or "") for u in last] != want \
            or any(str(u.get("speaker") or "") != "DIRECTOR" for u in last):
        return False, "his line is on record and the film does not end on it, word for word"
    found = _PAR.findall(desc)
    if len(found) != 1 or found[0] != paragraph(mk["line"]): return False, "his line is not in the description that is sent"
    for st_ in states or []:
        i, typ, src = st_[0], st_[1], st_[2]
        if typ != "still" or src == i: return False, "his line is spoken over a picture made for it"
    return True, f"the film ends on his own line, word for word: \"{mk['line']}\"; the same line is in the description"

# ------------------------------------------------------------------ his voice: a field and a refusal (V3 speaks it)
def voice_issues():
    """[] while MAKER_VOICE is empty; else what is missing from his consent record."""
    if not str(S("MAKER_VOICE") or "").strip(): return []
    raw = str(S("MAKER_VOICE_CONSENT") or "").strip()
    try: rec = json.loads(raw) if raw else None
    except Exception: rec = None
    if not isinstance(rec, dict): return ["MAKER_VOICE is set and MAKER_VOICE_CONSENT holds no consent record"]
    p = []
    if not str(rec.get("file") or "").strip(): p.append("the consent record names no file")
    if str(rec.get("words") or "").strip() != CONSENT: p.append("the consent record's words are not the voice provider's consent sentence")
    return p
