"""Offline stand-ins for every model call (rehearsal mode WI_FAKE=1), including a fake prompt-cache server; zero cost. See docs/CURRENT/SYSTEM.md."""
import json, re, random
from whatifs.core import SMALL

def _lines(n):
    pool = ["[calm] Right now, about eight billion people are doing something ordinary.", "[tension] But at exactly noon, all of them do it at once.",
            "[reveal] That adds up to a number nobody has ever written down.", "[aside] And somewhere, someone still replies 'k' to a long text... [beat] classic.",
            "[tension] The first ten seconds look harmless.", "[calm] Then the water starts to change colour.", "[pause:short]",
            "[reveal] By the end of the hour, the coastline has moved.", "[tension] And the strangest part is what happens to you.", "[callback] So next time, maybe just... don't."]
    return [pool[i % len(pool)] for i in range(n)]

def _lines_inside(n):
    """v12 V2b: the same stand-in lines as a writer who obeys the voice rule says them - to 'you', now (whatifs/org/inside.py; used only while it is on)."""
    pool = ["[calm] Right now, you and about eight billion people are doing something ordinary.", "[tension] But at exactly noon, all of you do it at once.",
            "[reveal] That adds up to a number nobody has ever written down for you.", "[aside] And somewhere, you still reply 'k' to a long text... [beat] classic.",
            "[tension] The first ten seconds look harmless to you.", "[calm] Then the water in front of you starts to change colour.", "[pause:short]",
            "[reveal] By the end of the hour, the coastline you know has moved.", "[tension] And the strangest part is what happens to you.", "[callback] So you keep both feet on the floor... just in case."]
    return [pool[i % len(pool)] for i in range(n)]

def _inside_on():
    try:
        from whatifs.org import inside as _IN
        return _IN.on()
    except Exception: return False

def _ending():
    """v12 V2b: how the format in the making ends while ENDINGS_ON ('' otherwise): the stand-in writer obeys it."""
    try:
        from whatifs.core import S
        from whatifs import formats as _FMT
        return _FMT.ending() if S("ENDINGS_ON", bool) and _FMT.current() in _FMT.FORMATS else ""
    except Exception: return ""

FAKE_SOURCES = (   # v12 B5: what a fake web search "returns" (url, title, age in days, quoted text) - an official page, a paper and a practitioner page
    ("https://support.google.com/youtube/answer/1311392", "YouTube channel monetization policies - YouTube Help", 40, "Inauthentic content: content that is mass-produced or repetitive is not eligible."),
    ("https://arxiv.org/abs/2506.20803", "The Ideation-Execution Gap", 300, "LLM-generated ideas scored higher before execution and dropped significantly more after it."),
    ("https://www.creator-retention-notes.com/first-30-seconds", "What holds viewers in the first 30 seconds", 70, "Channels that re-hook every 40 seconds kept 9 points more viewers at 30 s."))

def _ago(days):
    import datetime as _dt
    return (_dt.datetime.now(_dt.timezone.utc).date() - _dt.timedelta(days=days)).isoformat()

def fake_search(prompt):
    """(citations, results) a fake web search returns: the three FAKE_SOURCES, each cited with its quoted text."""
    cites = [{"url": u, "title": t, "cited_text": q} for u, t, _d, q in FAKE_SOURCES]
    return cites, [{"url": u, "title": t, "page_age": _ago(d)} for u, t, d, _q in FAKE_SOURCES]

def _fake_research(prompt):
    """A fake research answer: three grounded sources, one PHANTOM the search never returned (code must drop it) and one undated source."""
    srcs = [{"url": u, "title": t, "date": _ago(d), "type": "official"} for u, t, d, _q in FAKE_SOURCES]
    srcs += [{"url": "https://made-up-study.invalid/views", "title": "A study nobody can find", "date": _ago(30), "type": "measured"},
             {"url": FAKE_SOURCES[2][0], "title": "same page, no date", "date": "", "type": "practice"}]
    return json.dumps({"answer": "Re-hooking more often and opening on the viewer holds attention; repetitive formats risk monetisation.",
                       "findings": [{"text": "Mass-produced or repetitive uploads are not eligible for monetisation; each video must differ in substance.", "sources": [0]},
                                    {"text": "Channels that re-hook about every 40 seconds keep more viewers at 30 seconds than channels that do not.", "sources": [2, 1]},
                                    {"text": "A secret study proves that courtroom shows triple their views overnight.", "sources": [3]}],
                       "sources": srcs, "confidence": 0.8, "expected_impact": "more viewers still watching at 30 seconds in the next long video",
                       "cost_inr": 0,
                       "proposed_actions": [{"action": "Re-hook the viewer at least every 40 seconds in the long video's script", "target_depts": ["D4"], "lever_class": "C",
                                             "metric": "retention", "direction": "up", "horizon_videos": 2},
                                            {"action": "Make every video's cold open differ in setting and stakes from the last three", "target_depts": ["D4"], "lever_class": "D",
                                             "metric": "originality", "direction": "up", "horizon_videos": 3}]})

_PB_LINE = re.compile(r"^- \[(PI-[0-9A-F]{10})\] (PROVEN|ACCEPTED|TESTING): (.*)$", re.M)

def _quote(obj):
    """The first ten words of the longest text (six words or more) in a reply: what a compliant model copies as the place it applied an item."""
    best = ""
    def walk(v):
        nonlocal best
        if isinstance(v, str):
            if len(v.split()) >= 6 and len(v) > len(best): best = v
        elif isinstance(v, dict): [walk(x) for x in v.values()]
        elif isinstance(v, list): [walk(x) for x in v]
    walk(obj)
    if not best: return ""
    if "\n" in best:                                                    # a narration: a spoken line from the middle (openings are rewritten by the hook lab)
        ls = [x for x in best.split("\n") if len(x.split()) >= 6 and not x.startswith(("## BEAT", "[pause"))]
        if ls: best = ls[len(ls) // 2]
    return " ".join(re.sub(r"\[[^\]]*\]", " ", best).split()[:10])

def fake_cite(res, system):
    """v12 B6a: a compliant offline model. When the system prompt carries the Palace citation rule, the reply cites one playbook line with a quote copied
    from itself, pays every MUST CITE continuity debt with a line in the narration, and (when asked) adds one proposal for the Council."""
    s = str(system or "")
    if not isinstance(res, dict) or "PALACE CITATIONS" not in s: return res
    out = dict(res); lines = _PB_LINE.findall(s); cites = []
    must = re.findall(r"MUST CITE \(continuity\): \[(PI-[0-9A-F]{10})\]", s)
    for iid in must:
        if not isinstance(out.get("script"), str): continue
        summ = next((t for i, _st, t in lines if i == iid), "the case before this one")
        line = "Remember the last case: " + " ".join(re.findall(r"[A-Za-z']+", summ)[2:9]) + "."
        parts = out["script"].split("\n"); k = max(1, len(parts) // 2)
        while k < len(parts) and parts[k].startswith(("## BEAT", "[pause")): k += 1
        parts.insert(k, "[DIRECTOR] [calm] " + line); out["script"] = "\n".join(parts); cites.append({"id": iid, "where": line})
    q = _quote(out)
    if q:
        free = [(i, t) for i, _st, t in lines if i not in must]
        words = set(re.findall(r"[a-z]{4,}", json.dumps(out).lower()))
        near = max(free, key=lambda x: len(set(re.findall(r"[a-z]{4,}", x[1].lower())) & words), default=None)      # the line closest to what it wrote
        for iid in dict.fromkeys([x[0] for x in free[:1]] + ([near[0]] if near and set(re.findall(r"[a-z]{4,}", near[1].lower())) & words else [])):
            cites.append({"id": iid, "where": q})
    if cites: out["applied_items"] = cites
    if "PROPOSAL (optional" in s:
        out["proposal"] = {"kind": "world_building", "idea": "Dr. Grimm keeps a jar of every failed prototype's last spark on his desk; each case, one more jar lights up.",
                           "rationale": "A visible running tally gives returning viewers a reward for watching every case and a callback that changes a little each time."}
    return out

def _fake_board(prompt):
    """A fake strong judge: every memo with dated sources gets yes on the good questions and no on the risk questions; a memo with no source fails."""
    out = {}
    for lab, block in re.findall(r"=== MEMO ([A-Z]) ===\n(.*?)(?=\n=== MEMO |\Z)", prompt, re.S):
        bad = "SOURCES: none" in block or any(w in block.lower() for w in ("guarantee", "re-upload", "near-identical", "buy 10,000"))
        out[lab] = {q: (["no", "nothing supports it"] if bad else ["yes", "the quoted sources support it"]) for q in ("E1", "E2", "N1", "N2", "I1", "I2", "I3", "F1", "F2")}
        out[lab].update({q: (["yes", "it breaks a rule"] if bad else ["no", "no rule is touched"]) for q in ("R1", "R2", "R3")})
    return json.dumps({"answers": out})

def _fake_probe(prompt):
    """v12 V1b: the offline reader of the promise line-up - it names a title only when the opening shares more words with it than with any other."""
    from whatifs.growth import _stems
    titles = dict(re.findall(r"(?m)^([A-D])\. (.+)$", prompt))
    def pick(op):
        s = _stems(op); sc = sorted(((len(_stems(t) & s), l) for l, t in titles.items()), reverse=True)
        return sc[0][1] if sc and sc[0][0] > 0 and (len(sc) < 2 or sc[0][0] > sc[1][0]) else "E"
    x = prompt.split("OPENING X:")[-1].split("OPENING Y:")[0]; y = prompt.split("OPENING Y:")[-1]
    return json.dumps({"X": pick(x), "Y": pick(y), "X_says": "Something strange is about to happen to you.", "Y_says": "Something strange is about to happen to you."})

# v12 V2c: what the offline writer of a Short can write - two scripts per Short format ({w} = one plain word of the premise). Each is written to pass the
# viewer's seat for a Short (a hook of at most 6 words, no number, no expert word, no ask, the last line picks up a word of the first).
_SHORT_FAKE = {
    "S1": [("The Second Your {W} Changed", "Your {w} changed its mind",
            [("picture", "Your {w} just changed its mind. You reach out, and it answers a moment late.", "your own hand reaching toward the {w} in your bedroom at dawn, and the {w} moving a moment after your hand"),
             ("consequence", "By breakfast nothing in the kitchen keeps time with your hands, and the cat has stopped trusting you.", "your kitchen table, a cup sliding after your fingers have already left it"),
             ("consequence", "By evening the whole street walks beside its own echo, and nobody remembers who moved first.", "your street at dusk, every neighbour followed by a faint copy of himself"),
             ("question", "So tonight, when the {w} reaches for you before you reach for it, do you take its hand?", "the {w} leaning toward your open hand in the dark bedroom")]),
           ("The Morning the {W} Let Go", "The {w} let go",
            [("picture", "Something is wrong with the {w}. It lets go of you while you are still holding on.", "your fingers closing on the {w} above your bed as it slips away from them"),
             ("consequence", "Inside a minute your cup, your keys and your own shadow drift a little out of reach.", "your hallway, keys and a cup hanging a hand's width above the shelf"),
             ("consequence", "Outside, the neighbours stand very still in their gardens, afraid that walking will make it worse.", "your front garden at noon, people frozen on their lawns"),
             ("question", "And if the {w} never holds you again, would you still step through your front door?", "your own hand on the front door, the {w} far behind you")])],
    "S2": [("Would You Keep the {W}?", "Keep it or lose it",
            [("power", "The {w} is yours now. One thought, and it does whatever you ask.", "your open palm in your living room, the {w} turning above it as you look at it"),
             ("personal", "Your mother calls, and before she speaks you already know it has changed her morning too.", "your phone lighting up on the sofa beside your hand"),
             ("turn", "Then you notice the price: every time you use it, something small you love goes quiet.", "the birdcage by your window, the bird's beak opening without a sound"),
             ("choice", "So would you keep the {w} and the silence, or give it back and hear them again?", "your two hands, the {w} in one and the silent phone in the other")]),
           ("The Day You Lost the {W}", "Would you want it back?",
            [("power", "Today you lose the {w}. It is simply gone, like a word on the tip of your tongue.", "your bathroom mirror in the morning, an empty place where the {w} used to be"),
             ("personal", "Your best friend laughs at first, then holds your arm, because she can see what it took with it.", "a hand closing around your sleeve at a bus stop"),
             ("turn", "Nobody tells you the strange part: without it you sleep deeply, and wake up lighter.", "your own feet leaving the bedroom floor a little as you get up"),
             ("choice", "So would you take the {w} back and carry its weight, or stay light and never look for it?", "your hand hovering over the {w} on the pavement")])],
    "S3": [("The Whole {W} Story in One Breath", "The whole {w} story",
            [("idea", "The {w} runs your whole day. Follow it once across your own room.", "your bedroom window at sunrise, the camera starting to move forward from the glass"),
             ("why", "It starts at your window, where the light arrives and decides what you can see.", "the same move continuing along the windowsill, light spilling over your hand"),
             ("scale", "It keeps going past your street, your city and the dark side of the planet without ever slowing down.", "the same move rising over your roof, your street, the curve of the Earth"),
             ("return", "And then it is back at your window, and the {w} never looks ordinary to you again.", "the same move coming down to the bedroom window it started from")]),
           ("One Breath: The {W}", "One breath, one {w}",
            [("idea", "You carry the {w} everywhere. Walk with it once around your kitchen.", "your kitchen table in the morning, the camera starting to move forward from your coffee cup"),
             ("why", "At the table it is the reason your coffee cools and your bread goes hard.", "the same move passing over the cup and the bread on the table"),
             ("scale", "Out of the door it is the same reason rivers bend, cities glow and the sea keeps breathing.", "the same move leaving through the kitchen door, over a river and a city at night"),
             ("return", "Back at your table, the {w} is still there, and now you can feel it working.", "the same move arriving back at the coffee cup on the table")])],
}

def _short_word(premise):
    """One plain word of the premise for the offline Short: a name inside the sentence first, else its first plain word - never a number word and never a
    word the layman test would count as expert."""
    from whatifs.org import audience as AUD, layman as LAY
    from whatifs.growth import _STOP
    toks = re.findall(r"[A-Za-z]+", str(premise or ""))
    ok = lambda w: w.lower() not in _STOP and w.lower() not in AUD._SMALL and w.lower() not in AUD._BIG and not LAY.unfamiliar(w.lower())
    names = [t for i, t in enumerate(toks) if i and t[0].isupper() and len(t) >= 3 and ok(t) and t.lower() not in ("what", "if")]
    plain = [t for t in toks if len(t) >= 4 and ok(t)]
    return (names or plain or ["world"])[0].lower()

def _fake_short(prompt):
    """The offline writer of a standalone Short: the script of the Short format named in the prompt, about the premise named in the prompt; the second
    script of a format when a Short of that format was made before (so that two Shorts in a row are not alike)."""
    m = re.search(r"SHORT FORMAT: (S\d)", str(prompt)); fmt = m.group(1) if m and m.group(1) in _SHORT_FAKE else "S1"
    pm = re.search(r"PREMISE: (.*)", str(prompt)); w = _short_word(pm.group(1) if pm else "")
    em = re.search(r"EARLIER SHORTS \(format: opener\): (.*)", str(prompt)); before = [x for x in (em.group(1).split(" | ") if em else []) if x.startswith(fmt + ":")]
    title, promise, beats = _SHORT_FAKE[fmt][len(before) % len(_SHORT_FAKE[fmt])]
    f = lambda t: t.replace("{W}", w.title()).replace("{w}", w)
    return json.dumps({"title": f(title), "promise": f(promise), "beats": [{"role": r, "line": f(l), "picture": f(pc)} for r, l, pc in beats]})

def fake_reply(key, prompt):
    r = random.Random(len(prompt))
    if key == "rnd_research": return _fake_research(prompt)
    if key == "board": return _fake_board(prompt)
    if key == "probe": return _fake_probe(prompt)
    if key == "outlier_video":
        return json.dumps({"hook_device": "a number on frame 0", "first_frame": "close-up of a hand", "cut_rhythm": "a cut every 1.5 s", "sound_moment": "a hit at 0:02",
                           "caption_style": "word-by-word", "why_it_works": "instant stakes", "how_to_adapt": "open on YOU + a number in the cold open"})
    if key == "pilot":
        return json.dumps({"hook": "Your bed is floating. 9 seconds.", "lines": ["Gravity just quit.", "You grab the lamp.", "Should the jury hear this case?"]})
    if key == "occasions_check":
        return json.dumps({"diwali": "2027-10-29", "holi": "2027-03-22", "eid": "2027-03-10", "lunar_new_year": "2027-02-06"})
    if key == "special":                                           # v10 specials
        return json.dumps({"title": "Grimm objects to Monday", "beats": [{"who": "GRIMM", "sec": 3, "motion": "he slams a calendar", "card": "OBJECTION", "line": "Monday is guilty"},
                           {"who": "VALE", "sec": 3, "motion": "he checks the evidence", "card": "OBSERVE", "line": "the record shows coffee"},
                           {"who": "ROSA", "sec": 3, "motion": "she sips tea", "card": "OVERRULED", "line": "Tea first."},
                           {"who": "SET", "sec": 3.5, "motion": "doors open", "card": "REALITY ON TRIAL", "line": "Court opens Tuesday"}]})
    if key == "localize":                                          # v10 G4
        try: d = json.loads(prompt)
        except Exception: d = {"langs": {"es": "Spanish"}, "title": "t", "description": "d"}
        return json.dumps({l: {"title": f"[{l}] {d.get('title', '')}"[:100], "description": f"[{l}] {d.get('description', '')}"[:4500]} for l in d.get("langs", {})})
    if key == "scout":
        P4 = [("What if every pillow on Earth floated up at noon?", "Every Pillow Just Left Earth"), ("What if your bones turned to glass for a day?", "Your Bones Are Glass Now"),
              ("What if trees screamed when they were hurt?", "The Forest Can Scream"), ("What if Saturn's rings hung over your backyard?", "Saturn's Rings, Overhead")]      # v8.9.1: distinct pitches, so the vetted-tease gate has real choices
        return json.dumps({"pitches": [{"premise": P4[i][0], "ptype": "collective",
            "headline": P4[i][1], "family": ["F08_rules", "F01_body", "F06_nature", "F09_space"][i], "triggers": ["self-relevance"],
            "scores": {k: 8 for k in ["grasp", "weird", "personal", "unpredictable", "fresh", "showable", "pull"]}, "unexpected_answer": "x", "why_now": "y"} for i in range(4)]})
    if key == "showrunner":
        return json.dumps({"premise": "What if every pillow on Earth floated up at noon?", "headline": "Every Pillow Just Left Earth", "family": "F08_rules", "ptype": "collective", "logline": "l", "thesis": "t",
            "unexpected_answer": "u", "emotional_arc": "a", "peak_moment": "p", "humour_plan": "h", "title_candidates": ["What If Every Pillow Floated Away?"],
            "thumb_concept": "c", "risks": "r",
            "show_plan": {"charge": "Every pillow stands accused of breaking gravity at noon.", "defendant": "floating pillows", "intensity": 2,
                          "exhibits": [{"id": "A", "kind": "RECON", "what": "a bedroom at 11:59", "objection": "Pillows do not fly, Inspector."},
                                       {"id": "B", "kind": "DATA", "what": "lift needed per kilogram", "source": "NASA Glenn Research Center", "objection": "Numbers lie."},
                                       {"id": "C", "kind": "RECON", "what": "the sky full of pillows", "objection": ""}],
                          "witness_twist": "a measurement nobody checked", "jury_prompts": [{"kind": "guilty", "text": "Guilty or not guilty? Tell Nana Rosa."},
                          {"kind": "prediction", "text": "Where do the pillows stop rising?"}, {"kind": "abc", "text": "A, B or C: which exhibit sold you?"}],
                          "meter_swings": [{"after": "A", "side": "grimm", "n": 1}, {"after": "B", "side": "vale", "n": 2}], "verdict": {"winner": "vale", "detail": "lift"},
                          "clipbait_id": "C", "hud_spec": [{"t": 40, "type": "scale", "label": "Height", "value": 10, "unit": "m"}], "teacup_scenes": ["A", "C"],
                          "stinger": "Next case: your bones turn to glass.", "demand_evidence": {}},
            "next_tease": {"premise": "What if your bones turned to glass for a day?", "headline": "Your Bones Are Glass Now", "family": "F01_body", "ptype": "body", "line": "Next time: your bones turn to glass. Who survives breakfast?"}})
    if key == "memo": return json.dumps({"big_idea": "b", "needs": "n", "risk": "r", "techniques": ["Spielberg ripple"]})
    if key == "bible":
        return json.dumps({"conflicts": [{"issue": "i", "decision": "d"}], "beats": [{"n": i, "purpose": "p", "feeling": "f", "visual_world": "v", "sound": "s", "key_line": "k"} for i in range(1, 7)],
            "look": "cinematic, deep teal shadows, single warm key light, 35mm, fine grain", "recurring_motif": "m", "cta": {"like": "Tap like if your pillow is still here.", "subscribe": "Subscribe before the next object leaves.", "share": "Send this to the friend who sleeps on three pillows."}})
    if key == "jury":                                                 # v11 (K157): a blind ranking, the reverse of the order shown (exercises position handling)
        import re as _re
        letters = sorted(set(_re.findall(r"^\[([A-Z])\]$", prompt, _re.M)))
        return json.dumps({"ranking": list(reversed(letters)) or ["A"], "weakest_point": {l: "make the stakes concrete in the first line" for l in letters[:1]}})
    if key == "casefiles":                                            # v11 (K160)
        n = len(re.findall(r'"case":', prompt)) if 're' in globals() else 5
        import re as _re
        n = len(_re.findall(r'"case":', prompt)) or 5
        return json.dumps({"theme": "Every time the court nearly broke physics", "title": "5 Times the Court Nearly Broke Physics (Ranked)",
                           "cold_open": "One of these cases got Dr. Grimm banned from the building. It is not the one you think.",
                           "bridges": [f"Case #{n - i}: and still to come, the case that made Nana Rosa put down her tea." if i < n - 1 else "Number one. The jury still argues about it."
                                       for i in range(n)],
                           "verdicts": [["Guilty, with sprinkles.", "Acquitted. Reluctantly.", "Mistrial. Grimm ate the evidence.", "Guilty of being correct.", "Case reopened."][i % 5] for i in range(n)],
                           "vote": "Which verdict was wrong? You are the jury. Vote in the pinned comment."})
    if key in ("short_script", "short_fix"): return _fake_short(prompt)          # v12 V2c: a standalone Short in its Short format (the fix returns a clean one)
    if key == "punchup":
        import re as _re
        m = _re.search(r"SLOTS: (\[.*\])\s*$", prompt, _re.S)
        slots = json.loads(m.group(1)) if m else []
        return json.dumps({s["slot"]: [f"{s['line']} - and that, your honour, is why the Moon now pays rent", f"{s['line']} Objection: gravity."] for s in slots})
    if key == "writer":
        m = re.search(r"~(\d+) words", prompt); words = int(m.group(1)) if m else 300
        n = max(10, words // 11) if not SMALL else 12
        body = []
        k = 0
        from whatifs import formats as _FMT
        f1 = not _FMT.show_allowed()          # v12 V2a: a format that is not a trial is answered like a compliant writer - without the trial's devices
        pool_ = _lines_inside(n) if _inside_on() else _lines(n)          # v12 V2b: with the voice rule on, the stand-in speaks to 'you' (off: byte for byte as before)
        for b, chunk in enumerate([pool_[i:i + 4] for i in range(0, n, 4)], 1):
            body.append(f"## BEAT {b}")
            for ln in chunk:          # v8.1: Reality Engine dialogue; three label styles are mixed on purpose to exercise the tolerant parser
                if ln.startswith("[pause"): body.append(ln); continue
                who = "DIRECTOR" if k % 2 == 0 else "SKEPTIC"; tag = ln[:ln.index("]") + 1]; rest = ln[len(tag):].strip()
                every = 1 if "MARKER FIX" in prompt else (6 if f1 else 2)                      # a marker-fix request gets a punchline on every line
                mk = ("" if f1 else "[SEND] " if k == 2 else "[AWE] " if k == 5 else "") + ("[PUNCH] " if k % every == 0 else "")   # v11.1: markers like the real writer
                body.append(mk + [f"[{who}] {tag} {rest}", f"{tag} [{who}] {rest}", f"{who}: {rest}"][k % 3]); k += 1
        if _ending() == "question": body.append("[DIRECTOR] [close] So... would you keep it?")          # v12 V2b: a writer who obeys F1's ending (DESIGN QUESTION 9)
        mt = re.search(r"Title: ([^|]+?)\s*\|", prompt)                    # v11.1: a RETENTION FIX request is answered like a compliant writer:
        L = [i for i, x in enumerate(body) if not x.startswith(("## BEAT", "[pause"))]      # v9: the trial tags (never spoken; ignored when SHOW_MODE = off)
        if len(L) >= 8 and not f1:
            h = len(L) // 2
            body[L[1]] = "[EXHIBIT A] [METER -1 grimm] " + body[L[1]]; body[L[h]] = "[JURY] [EXHIBIT B] [METER +2 vale] " + body[L[h]]
            body[L[h + 1]] = "[CLIPBAIT] " + body[L[h + 1]] + " [/CLIPBAIT]"; body[L[-3]] = "[JURY] " + body[L[-3]]; body[L[-2]] = "[JURY] [EXHIBIT C] " + body[L[-2]]
            # v10.2: the trial grammar (time ladder, sourced exhibits, Grimm's Prototype, the verdict line), as the real brief demands
            body[L[0]] += " At hour 1 the tide clock stalls."; body[L[2]] += " By day 1 the beaches are strange."; body[L[4]] += " By year 1 the reefs go quiet."
            body[L[1]] += " Exhibit A: NOAA tide records, 2023."; body[L[h]] += " Exhibit B: UK tidal survey, 2021."; body[L[-2]] += " Exhibit C: Laskar, Nature, 1993."
            body[L[3]] += " Behold, Prototype No. 41!"; body[L[-1]] += " Here's what's true: in a million years the tilt still wobbles."
        if "RETENTION FIX" in prompt:                                            # answered like a compliant writer: a <=14-word YOU line with the
            promise = (mt.group(1).strip().rstrip("?") + "?") if mt else "Something is wrong."     # promise first, and no exhibit/lore in the first 20 s
            body.insert(1, f"[{'DIRECTOR' if f1 else 'WITNESS'}] [tension] YOU wake up. Your pillow floats. {promise}")
            moved = []
            for j in range(2, min(len(body), 7)):                                # exhibits MOVE later (never deleted: the episode still needs them)
                moved += re.findall(r"\[EXHIBIT[^\]]*\]", body[j]) + re.findall(r"Exhibit [A-H][^.]*\.", body[j])
                body[j] = re.sub(r"\[EXHIBIT[^\]]*\]\s*", "", body[j]); body[j] = re.sub(r"Exhibit [A-H][^.]*\.\s*", "", body[j])
            if moved:
                k2 = next((j for j in range(max(8, len(body) // 2), len(body)) if not re.search(r"(?i)exhibit|^## BEAT|^\[pause", body[j])), len(body) - 2)
                tags_ = " ".join(m for m in moved if m.startswith("[")); text_ = " ".join(m for m in moved if not m.startswith("["))
                body[k2] = (tags_ + " " if tags_ else "") + body[k2] + (" " + text_ if text_ else "")
        return json.dumps({"title_working": "Pillows", "script": "\n".join(body), "facts": [{"claim": "c", "reasoning": "r"}]})
    if key == "critic" and "MEASURED CHECKS" in prompt:          # v10.2: the 6-point creative self-review (contract)
        return json.dumps({"hook": 8, "clarity": 8, "humour": 7, "visual_variety": 7, "audio": 8, "accuracy": 8, "notes": "Fake review: tighten the cold open; more Grimm."})
    if key == "critic":
        return json.dumps({"scores": {k: 8 for k in ["hook_strength", "curiosity_gap", "escalation", "unpredictable_answer", "science_plausible", "pacing_variety",
            "humour_cringe_free", "originality_vs_recent", "policy_safe", "title_thumb_promise_kept", "sounds_human", "psychological_pull"]}, "verdict": "PASS", "fixes": {}})
    if key == "director":
        m = re.search(r"There are (\d+) shots", prompt); n = int(m.group(1)) if m else 10
        mm = re.search(r"\n(\d+): ", prompt); off = int(mm.group(1)) if mm else 0
        types = ["still", "graphic", "stock", "still", "living", "still", "kling"]
        shots = []
        for i in range(n):
            t = types[i % len(types)]
            shots.append({"unit": off + i, "type": t, "prompt": f"A floating pillow over a city, shot {i}", "motion": "slow push in", "search": "ocean waves", "camera": ["whip_settle", "drift", "spin_wildly", "kb_roll"][i % 4],
                          "graphic": {"label": "Pillows airborne", "from": 0, "to": 8000000000, "unit": ""}})
        return json.dumps({"shots": shots})
    if key == "packager":
        return json.dumps({"titles": ["What If Every Pillow Floated Away At Once?", "8 Billion Pillows Just Left Earth"], "thumb_text": "WHERE'D IT GO?", "thumb_prompt": "giant pillow over New York at dusk",
            "thumb_text_b": "LOOK UP", "thumb_prompt_b": "a single pillow drifting past the Moon",
            "description": "What happens if every pillow on Earth floats away at once?\n\nChapters\n\n#science #whatif #space",
            "tags": ["what if", "science"], "pinned_comment": "Would you chase yours?"})
    if key == "vision":
        n = int(re.search(r"FRAMES: (\d+)", prompt).group(1)) if re.search(r"FRAMES: (\d+)", prompt) else 3
        return json.dumps({"frames": [{"i": i, "match": 9, "artifact": False, "note": ""} for i in range(n)]})
    if key == "memo2":
        return json.dumps({"objections": [{"to": "WRITER", "objection": "The cold open spends the peak image too early.", "request": "Hold the biggest image until beat 4."}]})
    if key == "director_read":
        return json.dumps({"notes": [{"beat": 1, "note": "The opening object must be shown close, in silence, before any wide shot."}]})
    if key == "research_synth":
        sigs = []
        m = re.search(r"SIGNALS \(JSON\): (\[.*\])", prompt, re.S)
        try: sigs = json.loads(m.group(1)) if m else []
        except Exception: sigs = []
        cands = [{"premise": "What if every pillow on Earth floated up at noon?", "family": "F08_rules", "audience_need": "Viewers appear to ask what physically happens when everyday objects float.",
                  "click_emotion": "Curiosity about a familiar object behaving impossibly.", "evidence": [s["id"] for s in sigs if "pillow" in s.get("title", "").lower()][:2] or [],
                  "channel_fit": "Strange-rules family; reasoned with simple physics."}]
        if sigs: cands.append({"premise": "What if you never slept again?", "family": "F01_body", "audience_need": "Suggests interest in sleep loss.", "click_emotion": "Dread.",
                               "evidence": [sigs[0]["id"]], "channel_fit": "Body family."})
        return json.dumps({"candidates": cands})
    if key == "hooks":
        L = [("Eight billion people do it at exactly noon.", "surprising_claim"), ("The water starts to change colour.", "outcome_promise"),
             ("The strangest part is what happens to you.", "curiosity_gap"), ("A number nobody has ever written down.", "curiosity_gap"),
             ("Nobody has written that number down.", "concrete_stakes"), ("All of them do it at once.", "concrete_stakes"),
             ("Something ordinary happens to eight billion people.", "surprising_claim"), ("By noon, the coastline has moved.", "concrete_stakes"),
             ("You find out what happens to you.", "outcome_promise"), ("Water changes colour, then the coastline moves.", "outcome_promise"),
             ("By the end of the hour, the coastline has moved today.", "surprising_claim"), ("Welcome to the strangest hour on Earth.", "curiosity_gap")]
        return json.dumps({"candidates": [{"line": a, "type": b, "basis": "script"} for a, b in L]})
    if key == "hook_score":
        ids = re.findall(r'"id": "(h\d+)"', prompt)
        return json.dumps({"scores": [{"id": i, "clarity": 9 - (n % 3) * 0.5, "relevance": 8.5, "curiosity": 8 - (n % 4) * 0.5, "promise_accuracy": 9, "unsupported_claim": False, "note": "fake"} for n, i in enumerate(ids)]})
    if key == "sync": return json.dumps({"ok": True, "problems": []})
    if key == "factcheck": return json.dumps({"checked": 3, "issues": [{"claim": "a number", "severity": "weak", "problem": "rounded", "correction": "about eight billion people"}]})
    if key == "humanize":
        m = re.search(r"NARRATION:\n(.*)\nReturn JSON", prompt, re.S)
        return json.dumps({"script": m.group(1) if m else "## BEAT 1\n[calm] Hello.", "changes": "rhythm"})
    if key == "retention":          # v8.7: the offline writer returns the narration unchanged (so the gate's 'no improvement = keep the draft' path runs)
        m = re.search(r"NARRATION:\n(.*)$", prompt, re.S)
        return json.dumps({"script": m.group(1) if m else "## BEAT 1\n[calm] Hello.", "changes": "none"})
    if key == "playbook":           # v8.7: one sourced official rule, one unsourced (must be refused), one that games the platform (must be refused)
        return json.dumps({"rules": [{"rule": "Show the exact object from the thumbnail on screen within the first five seconds of the video.", "department": "writer", "metric": "open",
                                      "source_url": "https://support.google.com/youtube/answer/9314415", "source_kind": "official", "evidence": "official", "why": "intro retention"},
                                     {"rule": "Titles with exactly seven words always get double the clicks on every channel.", "department": "packager", "metric": "pack", "source_url": "", "evidence": "well-replicated"},
                                     {"rule": "Ask viewers to sub4sub in the comments to grow faster this month.", "department": "writer", "metric": "hold", "source_url": "https://example.com/x", "evidence": "plausible"}]})
    if key == "research":
        return json.dumps({"exploding": [{"title": "t", "channel": "c", "why": "w", "patterns": {"title": "number", "thumb": "one object", "hook": "you", "structure": "countdown", "length": "9m", "humour": "light"}}],
            "platform_changes": [], "rising_angles": ["everyday x everyone"], "rules_for_room": ["Use a specific number in the title."]})
    if key == "strategy": return json.dumps({"name": "new_idea_" + str(r.randint(1, 999)), "definition": "A fresh structure."})
    if key == "brief": return "Monthly brief (rehearsal)."
    # ---- v8.10 stand-ins
    if key == "premise_bank":
        P8 = [("What if Saturn's rings were for sale?", "Saturn's Rings Are For Sale"), ("What if only you could hear Wi-Fi signals?", "You Can Hear Wi-Fi Now"),
              ("What if a volcano opened in your basement?", "There's A Volcano In Your Basement"), ("What if your shadow lagged one second behind you?", "Your Shadow Is One Second Late"),
              ("What if the Moon were as close as a skyscraper?", "The Moon Is Next Door"), ("What if your hair aged 50 years in one day?", "Your Hair Aged 50 Years Today"),
              ("What if every pillow on Earth floated up at noon?", "Every Pillow Just Left Earth"), ("What if rain fell upward for an hour?", "Rain Is Falling Up"),
              ("What if you could taste colours for a week?", "You Can Taste Colours Now"), ("What if your phone screen became a window to Mars?", "Your Phone Opens To Mars"),
              ("What if gravity flipped inside your bedroom only?", "Your Bedroom Lost Its Gravity")]
        return json.dumps({"premises": [{"premise": a, "headline": b, "family": "F09_space" if i % 2 else "F08_rules", "ptype": "collective", "pov_picture": "you look up"} for i, (a, b) in enumerate(P8)]})
    if key in ("premise_judge_claude", "premise_judge_gemini"):
        m = re.search(r"PITCHES: (\[.*?\])\s*\nReturn JSON", prompt, re.S)      # v8.10: the pitches travel in the user message
        try: pit = json.loads(m.group(1)) if m else []
        except Exception: pit = []
        off = 0.3 if key.endswith("gemini") else 0.0
        out = []
        for p in pit:
            weak = bool(re.search(r"scream|tears|lunch|gum|mushroom|yesterday", p.get("premise", ""), re.I))
            v = (4.5 if weak else 8.6) - off
            out.append(dict({c: v for c in ("weirdness", "counterintuitive_explainable", "showable_pov", "self_relevance", "emotional_peak", "novelty", "headline_fit")}, id=p["id"], note="fake"))
        return json.dumps({"scores": out})
    if key == "immersion":
        return json.dumps({"scenes": [{"quote": "The first ten seconds look harmless", "vantage": "eyes", "body": "a held breath", "senses": ["silence", "cold air"], "camera": "pov_rush", "sound": "riser", "impact": False},
                                      {"quote": "the coastline has moved", "vantage": "object", "body": "stomach drop", "senses": ["roar", "spray"], "camera": "impact_shake", "sound": "boom", "impact": True},
                                      {"quote": "the water starts to change colour", "vantage": "hands", "body": "cold fingers", "senses": ["drip"], "camera": "debris", "sound": "drip", "impact": False}],
                           "peak_quote": "By the end of the hour, the coastline has moved."})
    if key == "comment_classify":                 # v9.1: keep every other suggestion
        try: items = json.loads(prompt)
        except Exception: items = []
        return json.dumps({"items": [{"i": it["i"], "keep": it["i"] % 2 == 0, "premise": it["text"][:120]} for it in items]})
    if key == "comment_drafts":
        try: items = json.loads(prompt)
        except Exception: items = []
        return json.dumps({"items": [{"i": it["i"], "draft": "Good question. The evidence says: watch the next case. — Vale"} for it in items]})
    if key == "json_repair":                     # v8.11: syntax-only repair (trailing commas, missing closing brackets); words untouched
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(prompt).strip(), flags=re.S)
        t = t[t.find("{"):] if "{" in t else t
        t = re.sub(r",\s*([}\]])", r"\1", t)
        t += "]" * max(0, t.count("[") - t.count("]")) + "}" * max(0, t.count("{") - t.count("}"))
        return t
    if key == "bench":                           # v8.11: extra-effort premise generation for the Premise_Bench
        P6 = [("What if Saturn's rings were for sale on your street?", "Saturn's Rings Are For Sale"), ("What if you could hear every Wi-Fi signal?", "You Can Hear The Wi-Fi Now"),
              ("What if a volcano opened inside your city park?", "A Volcano Opened In The Park"), ("What if your shadow lagged ten seconds behind you?", "Your Shadow Is Ten Seconds Late"),
              ("What if the ocean stood still at noon?", "The Ocean Froze At Noon"), ("What if your reflection aged faster than you?", "Your Reflection Is Aging Faster"),
              ("What if lunch tasted like Tuesday?", "Lunch Tastes Like Tuesday"), ("What if your city floated a metre up?", "Your City Floats A Metre Up")]
        return json.dumps({"premises": [{"premise": a, "headline": b, "family": ["F09_space", "F08_rules", "F06_nature", "F01_body"][i % 4], "ptype": "collective",
                                         "pov_picture": "you, first person", **({"source_video_id": "fakevid0001"} if i < 2 else {})} for i, (a, b) in enumerate(P6)]})
    if key == "owners_cut":
        return json.dumps({"scores": {"inside_scene": 8, "weirdness_hook": 8, "emotional_peaks": 8, "payoff": 8, "originality": 8}, "fixes": []})
    if key == "techniques":
        return json.dumps({"observations": [{"video_id": "fakevid0001", "hook_device": "falls in first person before any word", "first_3s_visual": "clouds rushing at the lens",
                                             "cut_rhythm": "fast then one long hold", "sound_moment": "silence before the impact", "payoff_structure": "the bottom is revealed last", "evidence": "two comments mention the silence"},
                                            {"video_id": "invented999", "hook_device": "made up", "first_3s_visual": "x", "cut_rhythm": "x", "sound_moment": "x", "payoff_structure": "x", "evidence": "none"}]})
    return json.dumps({"ok": True})



# ---------------------------------------------------------------- v8.11: an offline Claude cache server (the documented rules, Nov 2026)
class _Resp:
    def __init__(self, code, data): self.status_code = code; self._d = data; self.text = json.dumps(data)
    def json(self): return self._d

class FakeAnthropic:
    """Applies the prompt-caching rules from the docs to a request body and answers with a realistic usage block:
    prefix order tools -> system -> messages; at most 4 breakpoints; a 1-h breakpoint never after a 5-min one; an empty text block cannot be cached;
    a prefix shorter than MIN tokens is silently not cached; writes only at breakpoints, reads look back for an earlier write of the same prefix;
    the lifetime counts from the START of the request; effort, tools and model are part of the cached prefix; max_tokens 0 = a warm-up (no output).
    Tokens are estimated as characters / 4. reply = the text to answer with (tests); clock = a time function (tests)."""
    MIN = 512
    def __init__(self, clock=None):
        import time as _t
        self.clock = clock or _t.time; self.entries = {}; self.calls = []; self.reply = '{"ok": true}'
    def reset(self): self.entries.clear(); self.calls.clear()
    def post(self, body, headers=None):
        import hashlib
        now = self.clock(); self.calls.append(body)
        sysf = body.get("system", ""); blocks = sysf if isinstance(sysf, list) else ([{"type": "text", "text": sysf}] if sysf else [])
        msgs = body.get("messages", [])
        bps = [b for b in blocks if b.get("cache_control")]
        for m in msgs:
            if isinstance(m.get("content"), list): bps += [b for b in m["content"] if isinstance(b, dict) and b.get("cache_control")]
        if len(bps) > 4: return _Resp(400, {"error": {"message": "A maximum of 4 blocks with cache_control may be provided"}})
        seen5 = False
        for b in bps:
            ttl = b["cache_control"].get("ttl", "5m")
            if ttl == "1h" and seen5: return _Resp(400, {"error": {"message": "a ttl='1h' cache_control block must not come after a ttl='5m' block"}})
            seen5 |= ttl == "5m"
            if not str(b.get("text", "")).strip(): return _Resp(400, {"error": {"message": "cache_control cannot be set for empty text blocks"}})
        if body.get("max_tokens") == 0 and (body.get("stream") or (body.get("thinking") or {}).get("type") == "enabled"):
            return _Resp(400, {"error": {"message": "max_tokens 0 is not allowed with stream or extended thinking"}})
        if any(m.get("role") == "system" and m.get("output_config") for m in msgs) and "mid-conversation-output-config" not in str((headers or {}).get("anthropic-beta", "")):
            return _Resp(400, {"error": {"message": "messages.0.output_config: Extra inputs are not permitted"}})
        head = json.dumps([body.get("model"), (body.get("output_config") or {}).get("effort"), body.get("tools"), body.get("thinking")], sort_keys=True)
        h = hashlib.sha256(head.encode()); pos = []; cum = 0
        for b in blocks:
            h.update(str(b.get("text", "")).encode()); cum += len(str(b.get("text", ""))) // 4
            pos.append((cum, h.copy().hexdigest(), b.get("cache_control")))
        for m in msgs:
            c = m.get("content"); txt = c if isinstance(c, str) else json.dumps(c, sort_keys=True)
            h.update(txt.encode()); cum += len(txt) // 4
        total = cum
        live = {k: v for k, v in self.entries.items() if v > now}; self.entries = live
        marks = [(t, k, cc) for t, k, cc in pos if cc]
        a = 0; hit_i = -1
        for i, (t, k, cc) in enumerate(marks):
            if k in live and t >= self.MIN: a = t; hit_i = i
        b1 = a; c = a; w1 = w5 = 0
        for i, (t, k, cc) in enumerate(marks):
            if i <= hit_i or t < self.MIN: continue
            ttl = cc.get("ttl", "5m")
            if ttl == "1h": w1 += t - max(b1, c); b1 = c = t
            else: w5 += t - c; c = t
            self.entries[k] = now + (3600 if ttl == "1h" else 300)
        for i, (t, k, cc) in enumerate(marks):                     # a read refreshes the entry's lifetime
            if i <= hit_i and k in self.entries: self.entries[k] = now + (3600 if cc.get("ttl") == "1h" else 300)
        last = max([t for t, k, cc in marks if t >= self.MIN] or [0])
        usage = {"input_tokens": max(0, total - max(last, a)), "cache_read_input_tokens": a, "cache_creation_input_tokens": w1 + w5,
                 "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1}, "output_tokens": 0 if body.get("max_tokens") == 0 else 400}
        content = [] if body.get("max_tokens") == 0 else [{"type": "text", "text": self.reply}]
        return _Resp(200, {"content": content, "stop_reason": "max_tokens" if body.get("max_tokens") == 0 else "end_turn", "usage": usage})

FAKE_ANTHROPIC = FakeAnthropic()
