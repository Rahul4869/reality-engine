"""The launch salvo (D1, items 122 and 140): ONE launch flagship, armed by data (cli salvo, no lever), made in F1, with its Part 2 held. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, os, re
from whatifs.core import S, set_setting, log, store, now_utc, scrub, iso

_CUR = {"role": "", "rec": {}}          # the salvo role (and its record: Part 2 reads its cliff from it) of the episode in the making in this process ('' = none), kept as formats keeps the format (one job makes one episode at a time)
UNARMED = "The launch flagship is not armed: the first long video will be an ordinary one."
STANDS_DOWN = "The month does not pay a held Part 2: the launch flagship stands down."

def on():
    """Is the launch salvo switched on (SALVO_ON)? Off = no flagship: every long video is made as before."""
    return S("SALVO_ON", bool)

def _ready():
    """Every condition of flagship_due but the money (one definition: flagship_due is this AND part2_fits)."""
    from whatifs import formats as FMT, contract as CON
    if not on() or str(S("SALVO_FLAGSHIP") or "").strip() != "ARMED": return False
    if not FMT.on(): return False
    for v in (os.environ.get("WI_FORMAT"), S("FORMAT_FORCE")):          # a value naming another format than F1 refuses; one naming no format is ignored (as pick ignores it)
        f = str(v or "").strip().upper()
        if f in FMT.FORMATS and f != "F1": return False
    if not S("HOOKS_ON", bool) or not CON.enabled("hook_lab"): return False          # 3.1b: the pair is never made where its first line is unjudged
    if not S("ENDINGS_ON", bool) or not CON.enabled("format_ending") or not CON.enabled("cliffhanger"): return False          # the pair is never made where its ending is unjudged (RULINGS_U1e 1)
    return S("TWO_SCREENS_ON", bool)          # R23 (2), R1-60: the pair is never made where its review road cannot end

def flagship_due(now=None):
    """Is the next long video planned the launch flagship? ALL OF: SALVO_ON; the cell SALVO_FLAGSHIP is "ARMED"; formats are on and neither
    FORMAT_FORCE nor WI_FORMAT names another format than F1; the hook lab judges its first line (HOOKS_ON, and "hook_lab" not in CONTRACT_OFF);
    the format's own ending and the cliff are judged (ENDINGS_ON; neither "format_ending" nor "cliffhanger" in CONTRACT_OFF); both screens are on (TWO_SCREENS_ON); the month pays its held Part 2 (part2_fits). The list is complete. Costs nothing."""
    return bool(_ready() and part2_fits(now))

def part2_fits(now=None):
    """THE MONEY (3.4): Part 2 is the month's NEXT long video made early - one of the month's long videos. When its slot (the long-video slot after
    the flagship's) falls in the next month, this month also pays one full long video with the safety margin; else the month as it stands."""
    from whatifs import governor as G
    from whatifs.manage import next_slots
    now = now or now_utc(); n_long, n_short = G.max_long_videos(), S("SHORTS_PER_MONTH", int)
    slots = next_slots(2, now); p2 = slots[1] if len(slots) > 1 else None
    if p2 is not None and (p2.year, p2.month) != (now.year, now.month):
        return bool(G.month_fit(n_long, n_short, extra_inr=G.full_episode_inr() * S("BUDGET_SAFETY_MARGIN", float), now=now)["fits"])
    return bool(G.month_fit(n_long, n_short, now=now)["fits"])

def mark(d, ep):
    """THE DRAW, BEFORE THE FORMAT: a new long video's draw gets its salvo role - {"role": "flagship"} when the flagship is due and the draw is no
    Deep Trial. Whatever its ground (a promoted Short, his own topic, the override), the first long video planned while it is due is the flagship.
    When only the money stands in the way, the video is an ordinary one and he is told ONCE a month (an inform row, kind "strategy").
    3.4 (R15 TO CORRECT 4): while Part 2 is owed (owed()), the draw gets PART 2's RECORD instead - {"role": "part2", "of", "premise", "cliff", "answer",
    "line"}, read from the flagship's draw_json (the record's only home): the cliff it answers travels in its own draw."""
    fid = owed()
    if fid:
        fs = _salvo_of(fid); seq = fs.get("sequel") if isinstance(fs.get("sequel"), dict) else {}
        d["salvo"] = {"role": "part2", "of": fid, "premise": str(seq.get("premise") or ""), "cliff": str(fs.get("cliff") or ""),
                      "answer": str(seq.get("answer") or ""), "line": str(seq.get("line") or "")}
        log(f"{ep} is Part 2 of the launch flagship {fid} (item 140): it opens on Part 1's cliff", "INFO", ep)
        return d
    if d.get("deep_trial"): return d
    if flagship_due():
        d["salvo"] = {"role": "flagship"}
        log(f"{ep} is the launch flagship (item 122): made in F1, written inside production", "INFO", ep)
    elif _ready():
        try:
            from whatifs import notify as NT
            NT.send("strategy", STANDS_DOWN, tier="week", dedupe_key=f"salvo_down|{now_utc():%Y-%m}")
        except Exception as e: log(f"the flagship's stand-down was not told: {scrub(e)[:120]}", "WARN", ep)
    return d

def unarmed_line(st=None):
    """D1's daily brief, one line: while SALVO_ON, the cell is empty and no long video made since verdicts.since() has a yt_id - UNARMED; '' otherwise."""
    from whatifs.org import verdicts as VD
    if not on() or str(S("SALVO_FLAGSHIP") or "").strip(): return ""
    since = VD.since()
    if any(e.get("yt_id") and (since is None or VD.made_at(e.get("episode_id")) >= since) for e in (st or store()).rows("Episodes")): return ""
    return UNARMED

def use(d):
    """Make the salvo role of the draw `d` the role of the episode in the making ('' = an ordinary video) and keep the draw's salvo RECORD beside it
    (a copy: while Part 2 is made its cliff is read from it - 3.4, R15 review 10); None clears both."""
    sv = (d.get("salvo") if isinstance(d, dict) else None) or {}
    sv = sv if isinstance(sv, dict) else {}
    _CUR["role"] = str(sv.get("role") or ""); _CUR["rec"] = dict(sv)

def role():
    """The salvo role of the episode in the making: "flagship", "part2" or ''."""
    return _CUR["role"]

CLIFF_NOTE = ("THE ENDING OF THIS VIDEO: stop at the turning point. The last spoken sentence is ONE question to 'you' about what happens next in THIS story, "
              "ending with a question mark, and the script does not answer it. Name no other video: no 'part 2', no 'next time', no 'to be continued', no ask.")
KEEP_RX = re.compile(r"\bwould you (keep|take|want|choose) (it|this|that)\b")          # R15 (review 10d): the format's stock question is no cliff
CLIFF_FIX = "This video ends on ONE question to 'you' about what happens next in THIS story - never 'would you keep it?' - and the script does not answer it"

P2_HEAD = "THIS IS PART 2. PART 1 ENDED ON THIS UNANSWERED LINE: '{cliff}'."
P2_WORDS = (" In the first three sentences say again at least {n} of these words of that question: {words} - while you show the answer happening to the "
            "viewer ({answer}).")
P2_TAIL = " Then raise the stakes - a bigger number or a new cost; never repeat Part 1's events. Name no other video."

def _say(n):
    return {1: "one", 2: "two", 3: "three"}.get(n, str(n))

def note():
    """THE CLIFF (3.3): the salvo's words to the writer - formats.block("writer") appends them to the format's own. CLIFF_NOTE for the launch flagship;
    PART 2's NOTE (3.4; R15 review 10 (a)) while its Part 2 is made: P2_HEAD + P2_WORDS + P2_TAIL from its record (use) - the cliff, the cliff's words
    (as many as the gate's cell CLIFF_PAID_WORDS asks, all of them when the cliff has fewer) and the answer; a record whose cliff has no words gets no
    P2_WORDS (the gate then needs none). Part 2 ends as F1 ends (the format's own ending). '' for an ordinary video."""
    if role() == "flagship": return CLIFF_NOTE
    if role() != "part2": return ""
    rec = _CUR["rec"]; words = cliff_words(rec.get("cliff"))
    mid = P2_WORDS.format(n=_say(min(S("CLIFF_PAID_WORDS", int), len(words))), words=", ".join(words), answer=str(rec.get("answer") or "")) if words else ""
    return P2_HEAD.format(cliff=str(rec.get("cliff") or "")) + mid + P2_TAIL

SEQUEL_KEYS = ("premise", "answer", "line")
SEQUEL_SYS = ("You write the sequel record of a long video that ends on ONE unanswered question to the viewer (its cliff). Reply with JSON only, these "
              "three keys: {\"premise\": \"Part 2's premise in one sentence: the SAME power, the stakes raised - a bigger number or a new cost, never a "
              "repeat\", \"answer\": \"what Part 2 shows in its first 30 seconds in reply to the cliff\", \"line\": \"one sentence, at most 25 words, that "
              "the guide would write under Part 1 once Part 2 is out: what Part 2 answers, in the guide's voice; no ask, no 'subscribe', no 'link'\"}")

def seal(d, clean, room, ep):
    """THE CLIFF AND THE SEQUEL RECORD HAVE ONE HOME (3.3; R15 review 9): episode._stage_plan calls it once the narration is FINAL (after ROOM.extend,
    before the draw is written to Episodes.draw_json - the record's only home). For the launch flagship: d["salvo"]["cliff"] = its last spoken sentence
    (formats.ending_report, F1) and ONE call (route "sequel", fake key "salvo_sequel") with its premise and its last 120 spoken words writes
    d["salvo"]["sequel"] = {premise, answer, line}. A reply not of that shape is asked twice more (three asks); then the sequel stays EMPTY and check
    cliffhanger fails OWED at the script gate (no picture is paid). A line that fails line_ok is dropped ("": no comment is ever posted; the release
    stands). Any other video: untouched."""
    sv = d.get("salvo") if isinstance(d, dict) else None
    if not isinstance(sv, dict) or sv.get("role") != "flagship": return d
    from whatifs import formats as FMT
    from whatifs.models import ask
    from whatifs.org import audience as AUD
    sv["cliff"] = FMT.ending_report(clean, "F1")["last"]
    tail = " ".join(AUD.spoken(clean).split()[-120:])
    prompt = (f"PART 1's PREMISE: {(room.get('spine') or {}).get('premise') or ''}\nPART 1's LAST 120 SPOKEN WORDS (it ends on its cliff): {tail}\n"
              f"THE CLIFF: {sv['cliff']}\nWrite the sequel record now.")
    seq = {}
    for i in range(3):
        try: rep = ask("sequel", SEQUEL_SYS, prompt, episode=ep, fake_key="salvo_sequel", max_tokens=800)
        except Exception as e: log(f"the sequel record's ask {i + 1} failed: {scrub(e)[:120]}", "WARN", ep); rep = None
        if isinstance(rep, dict) and all(isinstance(rep.get(k), str) and rep[k].strip() for k in SEQUEL_KEYS):
            seq = {k: " ".join(rep[k].split()) for k in SEQUEL_KEYS}; break
    if not seq: log(f"{ep}: the launch flagship has no sequel record after three asks - check cliffhanger fails OWED (no picture is paid)", "WARN", ep)
    elif not line_ok(seq["line"], own=ep):
        log(f"{ep}: the sequel record's line fails its guard and is dropped (no comment is posted; the release stands)", "WARN", ep); seq["line"] = ""
    sv["sequel"] = seq
    return d

def earlier_plans(own="", st=None):
    """RULINGS_U1e 2 (V4b-fresh, step 6a): THE EARLIER PLANS - the plan JSON of every Appetite_Plans row whose `state` is "frozen" (or "fired": a
    frozen row that fired), whose `role` is "flagship" and whose episode is not `own`. An "open" row never counts: a dead try never blocks."""
    import json as _j
    out = []
    for r in (st or store()).rows("Appetite_Plans"):
        if str(r.get("state") or "") not in ("frozen", "fired") or str(r.get("role") or "") != "flagship": continue
        if own and str(r.get("ep") or "") == str(own): continue
        try: p = _j.loads(r.get("plan") or "{}")
        except (TypeError, ValueError): continue
        if isinstance(p, dict): out.append(p)
    return out

def line_ok(line, st=None, own=""):
    """THE LINE'S OWN GUARD (item 145; 3.3) - by code when the sequel record is written and again before the line is posted: 6 to 25 words, no ask
    (shortseat.ASK_RX), no pointer to another video (formats.TEASE), packaging.ad_risk clean, room.ai_tells empty, and (R15, 02 item 145) no phrase of
    the tab Banned as the room reads it (room._banned_hit); and (step 6a, RULINGS_U1e 2) no likeness at or above SHORT_SIMILAR_MAX with the line of
    an earlier plan (earlier_plans; `own` = the flagship's own episode: its own frozen row never counts)."""
    from whatifs import formats as FMT, packaging as PK, room as ROOM
    from whatifs.org import shortseat as SS
    t = " ".join(str(line or "").split())
    if not 6 <= len(t.split()) <= 25: return False
    if SS.ASK_RX.search(t.lower()) or FMT.TEASE.search(t) or PK.ad_risk(t) or ROOM.ai_tells(t): return False
    if any(FMT.likeness(t, l) >= S("SHORT_SIMILAR_MAX", float) for l in (str(p.get("line") or "") for p in earlier_plans(own, st)) if l.strip()): return False
    return not ROOM._banned_hit(t, [r["phrase"] for r in (st or store()).rows("Banned") if r.get("phrase")])

PAID_FIX = ("PART 2 OPENS ON PART 1's QUESTION: in the first three sentences say again at least {n} of these words: {words}, while you show the answer "
            "happening to the viewer")

def cliff_words(cliff):
    """THE CLIFF'S WORDS (3.3): the cliff's words in spoken order whose five-letter stem is in shortseat.content_words(cliff), one word per stem
    ("What do you do when the second sun rises?" -> second, sun, rises)."""
    from whatifs.org import audience as AUD, shortseat as SS
    c = str(cliff or ""); st = SS.content_words(c); out = []
    for w in re.findall(r"[a-z]{3,}", AUD.spoken(c).lower()):
        if w[:5] in st and w[:5] not in {x[:5] for x in out}: out.append(w)
    return out

def paid_issues(text):
    """R15 (review 10 (b)) PAID IS TOLD AND REPAIRED BEFORE IT HOLDS - for the writers' ONE fix (enforce.fix_all, tag PART 2 FIX): while a Part 2 is
    made (its record kept by use), when its FIRST THREE spoken sentences hold fewer than CLIFF_PAID_WORDS (2) of the stems of Part 1's cliff (all of them when
    the cliff has fewer), ONE instruction naming the words; [] for any other video and for a Part 2 whose record holds no cliff. Three sentences are stricter
    than the gate's 30 seconds, so a script the fix passed passes the gate."""
    if role() != "part2": return []
    words = cliff_words(_CUR["rec"].get("cliff"))
    if not words: return []
    from whatifs.org import shortseat as SS
    need = min(S("CLIFF_PAID_WORDS", int), len(words))          # the gate's own cell (check cliffhanger): the fix and the gate never drift apart
    if len({w[:5] for w in words} & SS.content_words(" ".join(SS.sentences(text)[:3]))) >= need: return []
    return [PAID_FIX.format(n=_say(need), words=", ".join(words))]

COST_WORDS = ("lose", "lost", "alone", "forget", "die", "dying", "family", "friend", "love", "sanity", "aging", "lonely", "mother", "father", "child")
_YOU = re.compile(r"\byou(r|rself)?\b")
_NUM = re.compile(r"\d|\b(twice|double|half|ten|hundred|thousand|million|billion)\b")
_COST = re.compile(r"\b(" + "|".join(COST_WORDS) + r")\b")

def premise_parts(text):
    """THE PREMISE SCORE, AN INPUT ONLY (RR-8): how many of four RECOGNISED parts the lower-cased premise holds (0-4) - YOU, ONE POWER (exactly one
    'if'), ONE NUMBER, A HUMAN COST (a word of COST_WORDS)."""
    t = str(text or "").lower()
    return sum((bool(_YOU.search(t)), len(re.findall(r"\bif\b", t)) == 1, bool(_NUM.search(t)), bool(_COST.search(t))))

def by_parts(pitches, forced=None):
    """The bench's order for the launch flagship's FREE choice (room.scout_and_pick, the bench branch): the pitches whose `combined` is at or above
    PREMISE_MIN_SCORE (the bar is judged on `combined` alone) by combined + PREMISE_PARTS_WEIGHT x premise_parts, first; the rest after them as they
    came. It ranks; it never refuses. No flagship in the making, or a forced premise (`forced`: his topic, the teased pitch) - the order as it came;
    a forced premise's parts are logged for the record only."""
    if role() != "flagship": return pitches
    if forced:
        log(f"the launch flagship's premise is forced: {premise_parts(forced.get('premise'))} of the four parts (for the record only)", "INFO"); return pitches
    bar, w = S("PREMISE_MIN_SCORE", float), S("PREMISE_PARTS_WEIGHT", float)
    up = [p for p in pitches if float(p.get("combined") or 0) >= bar]
    return sorted(up, key=lambda p: -(float(p.get("combined") or 0) + w * premise_parts(p.get("premise")))) + [p for p in pitches if p not in up]

def arm():
    """python -m whatifs.cli salvo (a pack step): writes "ARMED" into SALVO_FLAGSHIP when the cell is "" or "STOOD_DOWN", "" into SALVO_PART2 and "0"
    into both tries cells (arming starts a new pair: the last pair's STOOD_DOWN never outlives it) and says what it did; refuses when the cell holds
    "ARMED" or an episode id (one flagship)."""
    cur = str(S("SALVO_FLAGSHIP") or "").strip()
    if cur not in ("", "STOOD_DOWN"):
        return f"Not armed: SALVO_FLAGSHIP already holds {cur} - there is one launch flagship. Nothing was changed."
    set_setting("SALVO_FLAGSHIP", "ARMED"); set_setting("SALVO_PART2", ""); set_setting("SALVO_FLAG_TRIES", "0"); set_setting("SALVO_P2_TRIES", "0")
    log("launch flagship armed: the first long video planned from now on is the flagship (cli salvo)", "WARN")
    return "Armed: the first long video planned from now on is the launch flagship (F1). SALVO_FLAGSHIP = ARMED, SALVO_PART2 empty, both tries cells = 0."

_P2_FROM = ("SCHEDULED", "AWAITING_APPROVAL")          # 3.4: the flagship's statuses while its Part 2 is owed (uploaded; waiting for its slot or its review)
P2_GROUND_NOTE = "item 140: Part 2 of the launch flagship, rendered and held"

def _draw_of(row):
    dj = (row or {}).get("draw_json")
    if isinstance(dj, dict): return dj
    try: v = json.loads(dj or "{}")
    except (TypeError, ValueError): return {}
    return v if isinstance(v, dict) else {}

def _salvo_of(ep, eps=None):
    """The salvo record in episode `ep`'s draw_json ({} when none): the flagship's cliff and sequel record have their ONE home there (3.3)."""
    row = next((e for e in (store().rows("Episodes") if eps is None else eps) if e.get("episode_id") == ep), None)
    sv = _draw_of(row).get("salvo")
    return sv if isinstance(sv, dict) else {}

def owed(eps=None):
    """OWED (3.4; R15 reviews 2b and 9): the launch flagship's episode id while its Part 2 is owed, else "". ALL OF: SALVO_ON; SALVO_FLAGSHIP holds an
    episode id whose row has a yt_id and a status in ("SCHEDULED", "AWAITING_APPROVAL"); that row's draw_json holds salvo.sequel.premise; and Part 2 is not
    made yet - SALVO_PART2 is "", or names a row whose status is "FAILED" (its retry: _produce_slot's own tries < 2 bounds it). `eps` = the Episodes rows
    when the caller holds them. Costs nothing."""
    if not on(): return ""
    fid = str(S("SALVO_FLAGSHIP") or "").strip()
    if not fid: return ""
    rows = store().rows("Episodes") if eps is None else eps
    by = {e.get("episode_id"): e for e in rows}
    f = by.get(fid) or {}
    if not f.get("yt_id") or f.get("status") not in _P2_FROM: return ""
    seq = _salvo_of(fid, rows).get("sequel")
    if not (isinstance(seq, dict) and str(seq.get("premise") or "").strip()): return ""
    p2 = str(S("SALVO_PART2") or "").strip()
    if p2 and (by.get(p2) or {}).get("status") != "FAILED": return ""
    return fid

def took(ep, d):
    """3.4: called where the plan is saved (episode.produce, after LAD.use): the cell of the role the draw carries holds this episode's id - SALVO_FLAGSHIP
    for the launch flagship (a second flagship is impossible), SALVO_PART2 for its Part 2 (it is then no more owed). Returns the cell written; an ordinary
    draw writes nothing ('')."""
    sv = d.get("salvo") if isinstance(d, dict) else None
    cell = {"flagship": "SALVO_FLAGSHIP", "part2": "SALVO_PART2"}.get(str(sv.get("role") or "")) if isinstance(sv, dict) else None
    if not cell or not ep: return ""
    set_setting(cell, ep); log(f"{ep}: its plan is saved - {cell} = {ep} (the launch pair)", "INFO", ep)
    return cell

def ground(now=None):
    """THE GROUND (3.4; R15 TO CORRECT 11) - PART 2 RECORDS ITS OWN GROUND AND NEVER TAKES HIS: ladder.gate(salvo=True) answers with it FIRST while Part 2
    is owed. Appends the pair's own Ladder row ONCE - {"id": "OVRP2" + the flagship's id, "topic": that id, "state": "OVERRIDE", "by": "part2",
    "promoted_at", "note": P2_GROUND_NOTE} - and returns it (a second call returns the same row). ladder.override is never called for it: it hands back an
    open override of another kind (his "Make it anyway" tap) and Part 2 would use it up. None when no Part 2 is owed."""
    from whatifs import ladder as LAD
    fid = owed()
    if not fid: return None
    rid = "OVRP2" + fid
    have = LAD.row(rid)
    if have: return have
    store().append(LAD.TAB, [{"id": rid, "topic": fid, "state": "OVERRIDE", "by": "part2", "promoted_at": iso(now or now_utc()), "note": P2_GROUND_NOTE}])
    log(f"ladder: Part 2 of the launch flagship {fid} records its own ground {rid} (his own open override, if one waits, stays open)", "INFO")
    return LAD.row(rid)

PITCH_NOTE = "THIS IS PART 2 OF OUR LAST LONG VIDEO: keep this premise word for word."

def pitch(draw):
    """THE PITCH (3.4; R15 TO CORRECT 4 and review 10a): Part 2's forced first pitch for room.scout_and_pick, from its draw's record (mark) - the
    sequel's premise (its headline the same), the family and ptype of the flagship's row, teased, and as its `ladder` the pair's own row ("OVRP2" + the
    flagship's id, salvo.ground): RULINGS_U2c 1 - that row is handed out ONLY by name, never by ladder.waiting_override or claim(). The room takes it on a
    branch of its own (PITCH_NOTE to the Showrunner; never the promoted Short's words "REAL VIEWERS"; owner_brief.take_for_episode is not called). None
    for any other draw, or a record without a premise or a flagship id."""
    sv = draw.get("salvo") if isinstance(draw, dict) else None
    if not (isinstance(sv, dict) and sv.get("role") == "part2"): return None
    prem, fid = str(sv.get("premise") or "").strip(), str(sv.get("of") or "").strip()
    if not prem or not fid: return None
    f = next((e for e in store().rows("Episodes") if e.get("episode_id") == fid), None) or {}
    fam = str(f.get("family") or (_draw_of(f).get("strategies") or {}).get("family") or "")
    return {"premise": prem, "headline": prem, "family": fam, "ptype": str(f.get("ptype") or ""), "teased": True, "ladder": "OVRP2" + fid,
            "scores": {"grasp": 9, "pull": 9}, "total": 999}


_LIVE = ("LIVE1", "LIVE")          # v12 V4b step 6a (memo 992-993): a pair video that is public


def _final_failed(ep, st):
    """The failures of the newest final-gate row of each feature of `ep` - contract.failed, the ONE expression that holds a video."""
    from whatifs import contract as CON
    newest = {}
    for r in st.rows("Feature_Ledger"):
        if r.get("episode_id") == ep and r.get("stage") == "final" and str(r.get("ts") or "") >= str((newest.get(r.get("feature")) or {}).get("ts") or ""): newest[r.get("feature")] = r
    return CON.failed(list(newest.values()))


def held(row, st=None):
    """HELD, THE FREEZE's TEST (memo 1000-1002): Part 2's row has a yt_id (nothing is uploaded before its final gate passed) and its status is
    "SCHEDULED", or "AWAITING_APPROVAL" with no failed final-gate row (contract.failed on its newest ledger rows) and no open HOLD row of it (its
    own `silence|` report aside, as contract.clear_to_post reads it); never "HELD_BY_OWNER", "HOLD_QC", "FAILED" or "KILLED". Waiting for a review
    nobody refused is not "not held"."""
    r = row or {}
    if not r.get("yt_id"): return False
    if r.get("status") == "SCHEDULED": return True
    if r.get("status") != "AWAITING_APPROVAL": return False
    from whatifs import notify as NT
    ep = r.get("episode_id"); st = st or store()
    if _final_failed(ep, st): return False
    return not any(o.get("episode_id") == ep and NT.klass(o.get("kind")) == NT.HOLD and not str(o.get("dedupe_key") or "").startswith("silence|") for o in NT.open_rows())


def pair_clear(ep, st=None):
    """ONE RULE, ONE PLACE (memo 991-994; B-OWNER: "added by V4b in its own build"): (ok, why), pure reads - ONE MORE READ inside
    contract.clear_to_post. THE FLAGSHIP (cell SALVO_FLAGSHIP) is clear when its Appetite_Plans row is frozen AND held(<the row of the plan's
    `held`>) is still true or that row is "LIVE1"/"LIVE" - read at every ask, because a frozen row is never rewritten - else "the flagship waits
    for its Part 2: <Part 2's status, or its first failed check, or 'not made yet'>"; with SALVO_PART2 "STOOD_DOWN" it is never clear. PART 2
    (cell SALVO_PART2) is clear when the flagship is "LIVE1" or "LIVE". Any other video, or SALVO_ON FALSE: clear."""
    if not on() or not ep: return True, "not a launch pair video"
    st = st or store()
    fid = str(S("SALVO_FLAGSHIP") or "").strip(); p2 = str(S("SALVO_PART2") or "").strip()
    by = {e.get("episode_id"): e for e in st.rows("Episodes")}
    if ep == fid:
        if p2 == "STOOD_DOWN": return False, "its Part 2 could not be made"
        from whatifs.org import appetite as APP
        pr = APP.plan_row(fid, st); p = APP.numbers(pr) or {}
        h = by.get(str(p.get("held") or "")) or {}
        if pr and str(pr.get("state") or "") in ("frozen", "fired") and h and (held(h, st) or h.get("status") in _LIVE): return True, "its Part 2 is held"
        r = by.get(p2) if p2 else None
        bad = _final_failed(p2, st) if r else []
        why = "not made yet" if not r else (f"its check {bad[0][0]} failed" if bad else f"its status is {r.get('status') or 'unknown'}")
        return False, f"the flagship waits for its Part 2: {why}"
    if ep == p2:
        if (by.get(fid) or {}).get("status") in _LIVE: return True, "Part 1 is public"
        return False, "Part 2 waits until Part 1 is public"
    return True, "not a launch pair video"


def keep_tap(ep):
    """HIS TAP IS KEPT (memo 1004-1006): "approved by him <iso>" on the plan row's note (outside its JSON: the seal holds). True when written."""
    from whatifs.org import appetite as APP
    st = store(); pr = APP.plan_row(ep, st)
    if not pr: log(f"{ep}: his Approve is kept but there is no plan row to carry it", "WARN", ep); return False
    note = str(pr.get("note") or "")
    st.update("Appetite_Plans", "ep", ep, {"note": (note + "\n" if note else "") + f"approved by him {iso()}"})
    return True


def hold_card(d):
    """R23 (3), R24 (memo 1003): the SCRIPT card of a pair video says its clock - (extra, default, expires_h) for a draw with d["salvo"] while
    SALVO_ON: "written again by itself" in SALVO_HOLD_H hours, and on the role's LAST try (its tries cell at SALVO_TRIES_MAX - 1) "dropped by itself";
    None for every other draw (the base's card, "stays held")."""
    sv = d.get("salvo") if on() and isinstance(d, dict) else None
    if not sv: return None
    tries = S("SALVO_P2_TRIES", int) if isinstance(sv, dict) and sv.get("role") == "part2" else S("SALVO_FLAG_TRIES", int)
    if tries >= S("SALVO_TRIES_MAX", int) - 1:
        return "No picture money was spent. If you do nothing it is dropped and the launch pair stands down.", "dropped by itself", S("SALVO_HOLD_H", float)
    return "No picture money was spent. If you do nothing it is written again by itself.", "written again by itself", S("SALVO_HOLD_H", float)


def _cell(k): return str(S(k) or "").strip()


def _private(vid):
    """(0) and the pair's end (R26, R27): ok = yt_set_privacy(vid, "private") - a raise (a time-out) is caught HERE and is ok False - then
    got = yt_read(vid); True only when ok is True AND got reads "private" (a read that failed is not a pass)."""
    from whatifs import publish as PUB
    try: ok = PUB.yt_set_privacy(vid, "private")
    except Exception as x: ok = False; log(f"{vid}: the privacy change raised ({scrub(x)[:120]})", "WARN")
    if ok is not True: return False
    try: got = PUB.yt_read(vid)
    except Exception as x: got = {}; log(f"{vid}: the read-back raised ({scrub(x)[:120]})", "WARN")
    return isinstance(got, dict) and got.get("privacy") == "private"


def _time_row(r):
    """(0)'s ONE row: YouTube kept the time of a pair video that is not ready - kind contract_hold, tier "now", key salvo_time|<ep>; the next tick tries again."""
    from whatifs import notify as NT
    ep = r.get("episode_id")
    NT.send("contract_hold", f"{r.get('title') or ep} is still on YouTube's schedule and its pair is not ready. If it is not private within the hour, "
            f"set it to Private in Studio: https://studio.youtube.com/video/{r.get('yt_id')}/edit", tier="now", episode=ep, dedupe_key=f"salvo_time|{ep}")


def _off_road(r, st, now):
    """(0) BACK ON THE ROAD's test (memo 1003; R19, R23 (1), R24's T1): a yt_id AND EITHER "FAILED" with a release_tag, OR pair_clear says no and the
    status is "HELD", or "SCHEDULED" with its public time (public_at, else slot_et) still ahead of `now`. An "UPLOADED" row is never taken here."""
    from whatifs.core import parse_iso
    s = r.get("status")
    if not r.get("yt_id") or s not in ("FAILED", "HELD", "SCHEDULED"): return False
    if s == "FAILED": return bool(r.get("release_tag"))
    if pair_clear(r.get("episode_id"), st)[0]: return False
    if s == "HELD": return True
    t = parse_iso(str(r.get("public_at") or r.get("slot_et") or ""))
    return bool(t and t > now)


def _close(st, pick, answer):
    """Closes the open Owner_Actions rows `pick(row)` chooses, with `answer`."""
    from whatifs import notify as NT
    for o in NT.open_rows():
        if pick(o): st.update("Owner_Actions", "id", o["id"], {"status": "ANSWERED", "answered_at": iso(), "answer": answer})


def _checks(r):
    """The last failed checks a dead row names (its notes, the attempts mark taken out; its status when it has none)."""
    t = re.sub(r"\s*\|?\s*attempts=\d+", "", str(r.get("notes") or "")).strip(" |")
    return (t.split(": ", 1)[1] if t.startswith("contract hold") and ": " in t else t) or str(r.get("status") or "unknown").lower()


def _dead(r, role, st, now):
    """(0b) DEAD (memo 1003): DROPPED or SKIPPED; KILLED (Part 2 with or without a yt_id; the flagship only with NO yt_id - his KILL of an uploaded
    flagship ends the pair, K1); FAILED with no yt_id and two attempts used or no checkpoint left; FAILED with a yt_id and no release_tag; HOLD_QC
    "contract hold (script)" older than SALVO_HOLD_H - first dropped by contract._drop_for_rewrite (his Rewrite tap's own act) and its open card closed
    "dropped for a rewrite by its clock". A HOLD_QC held at the FINAL gate is never dropped by code."""
    from whatifs import checkpoint as CK
    from whatifs.core import parse_iso
    s = r.get("status"); ep = r.get("episode_id")
    if s in ("DROPPED", "SKIPPED"): return True
    if s == "KILLED": return role == "part2" or not r.get("yt_id")
    if s == "FAILED":
        if r.get("yt_id"): return not r.get("release_tag")
        return CK.attempts(r) >= 2 or not CK.has(r)
    if s == "HOLD_QC" and str(r.get("notes") or "").startswith("contract hold (script)"):
        t = parse_iso(str(r.get("updated") or ""))
        if t and (now - t).total_seconds() / 3600.0 > S("SALVO_HOLD_H", float):
            from whatifs import contract as CON
            CON._drop_for_rewrite(ep); _close(st, lambda o: o.get("dedupe_key") == f"contract|{ep}|script", "dropped for a rewrite by its clock")
            return True
    return False


P2_DOWN = "Part 1 stays private: it ends on a question no video answers. Tap Approve to publish it as it is."
OVER = ("You stopped Part 1, so the launch pair is over. Its Part 2, if one was made, stays private for good: it answers a video nobody will see. "
        "The next long videos are ordinary ones. Nothing to do.")


def _p2_down(fid, first):
    """Part 2's stand-down row (R23 (3)): NOT kind "strategy" - B-OWNER's own hold row of the flagship, sent early: kind contract_hold, tier "week",
    key silence|<flagship>, Approve / Keep it private, no default, no expiry (approve_by_silence's later send finds it open: ONE row)."""
    from whatifs import notify as NT
    NT.send("contract_hold", f"{first} {P2_DOWN}", [("Approve", f"APPROVE {fid}"), ("Keep it private", f"HOLDREVIEW {fid}")], tier="week", episode=fid,
            dedupe_key=f"silence|{fid}")


def _follow(fid, p2, by, st, now):
    """(0b) THE CELL FOLLOWS ITS ROW (memo 1003; R19, R23 (3), R24): for a DEAD episode its tries cell + 1; under SALVO_TRIES_MAX the cell goes back
    ("ARMED" for the flagship, "" for Part 2), at the maximum it is "STOOD_DOWN" with ONE row (the flagship: an inform row, kind "strategy"; Part 2: the
    flagship's own silence| row). A flagship with a yt_id whose draw_json holds no salvo.sequel.premise stands down at once (Part 2 "STOOD_DOWN")."""
    from whatifs import notify as NT
    out = {}; mx = S("SALVO_TRIES_MAX", int)
    for role, cell, tc, ep in (("flagship", "SALVO_FLAGSHIP", "SALVO_FLAG_TRIES", fid), ("part2", "SALVO_PART2", "SALVO_P2_TRIES", p2)):
        r = by.get(ep) if ep else None
        if not r: continue
        why = _checks(r)
        if not _dead(r, role, st, now): continue
        n = (S("SALVO_FLAG_TRIES", int) if role == "flagship" else S("SALVO_P2_TRIES", int)) + 1; set_setting(tc, str(n))
        if n < mx:
            set_setting(cell, "ARMED" if role == "flagship" else ""); out[f"dead|{ep}"] = f"try {n} of {mx} dead: the cell goes back"; continue
        set_setting(cell, "STOOD_DOWN"); out[f"dead|{ep}"] = "stood down"
        if role == "flagship":
            NT.send("strategy", f"The launch flagship stood down: {n} scripts were held at their gate ({why}). The next long video is an ordinary one. Nothing to do.",
                    tier="week", episode=ep, dedupe_key=f"salvo_down|{ep}")
        else: _p2_down(fid, f"Part 2 could not be made in {n} tries ({why}).")
    f = by.get(fid) or {}
    if not _cell("SALVO_PART2") and _cell("SALVO_FLAGSHIP") == fid and f.get("yt_id") and f.get("status") not in ("KILLED", "DROPPED", "SKIPPED"):
        seq = _salvo_of(fid, list(by.values())).get("sequel")
        if not (isinstance(seq, dict) and str(seq.get("premise") or "").strip()):
            set_setting("SALVO_PART2", "STOOD_DOWN"); _p2_down(fid, "Part 1 has no Part 2: its sequel was never written."); out["no_premise"] = fid
    return out


def _over(fid, p2, by, st):
    """K1 (R24; R23 (3), R25, R26): HIS KILL OF AN UPLOADED FLAGSHIP ENDS THE PAIR - met FIRST, and nothing else is done for the pair. (i) A Part 2
    with a yt_id not yet "KILLED" is first taken off YouTube's clock (_private: `ok` kept, then the read-back); only then is it KILLED "ended with its
    Part 1" and its open rows closed - else nothing is written for it, (0)'s row is sent and the end stops here. (ii) SALVO_PART2 = "STOOD_DOWN" in
    every case. (iii) ONE row, ONCE EVER (no row with its key on Owner_Actions, open or closed). The flagship's cell keeps the killed id."""
    from whatifs import notify as NT
    r = by.get(p2) if p2 else None
    if r and r.get("yt_id") and r.get("status") != "KILLED":
        if not _private(r["yt_id"]): _time_row(r); return "Part 2 is still on YouTube's schedule"
        st.update("Episodes", "episode_id", p2, {"status": "KILLED", "notes": "ended with its Part 1", "updated": iso()})
        _close(st, lambda o: o.get("episode_id") == p2, "ended with its Part 1")
    if p2 != "STOOD_DOWN": set_setting("SALVO_PART2", "STOOD_DOWN")
    key = f"salvo_over|{fid}"
    if not any(o.get("dedupe_key") == key for o in st.rows("Owner_Actions")): NT.send("strategy", OVER, tier="week", episode=fid, dedupe_key=key)
    return "the pair is over"


def pair(now=None):
    """THE PAIR's STEP OF THE TICK (memo 1003-1008), called FIRST in every tick (manage.tick, before resume_held, in a `try` of its own). TYPED:
    (1) Part 2 is held and the flagship's plan is open -> the plan is frozen with `held` = Part 2's id, the cliff and the line (from the flagship's
    draw_json, their one home) and its sha; a frozen row is never rewritten. (2) A pair video "AWAITING_APPROVAL" whose plan row carries his kept
    tap and that has turned pair_clear -> contract.approve. BEFORE THEM, IN THIS ORDER: his KILL of an uploaded flagship ends the pair (_over, met
    FIRST: nothing else then); (0) BACK ON THE ROAD (_off_road -> _private -> contract.await_approval, else ONE salvo_time| row); (0b) THE CELL FOLLOWS
    ITS ROW (_follow). Returns what it did."""
    if not on(): return {}
    from whatifs import contract as CON
    from whatifs.org import appetite as APP
    now = now or now_utc()
    st = store(); by = {e.get("episode_id"): e for e in st.rows("Episodes")}
    fid = _cell("SALVO_FLAGSHIP"); p2 = _cell("SALVO_PART2"); out = {}
    if (by.get(fid) or {}).get("status") == "KILLED" and (by.get(fid) or {}).get("yt_id"): return {"over": _over(fid, p2, by, st)}
    for ep in (fid, p2):
        r = by.get(ep) if ep else None
        if r and _off_road(r, st, now):
            if _private(r["yt_id"]):
                CON.await_approval(ep, r["yt_id"], r.get("slot_et") or "", "Back on the review road: its upload did not end cleanly, or its pair is not ready.")
                out[f"road|{ep}"] = "back on the review road"
            else: _time_row(r); out[f"road|{ep}"] = "still on YouTube's schedule"
    out.update(_follow(fid, p2, {e.get("episode_id"): e for e in st.rows("Episodes")}, st, now))
    rows = st.rows("Episodes"); by = {e.get("episode_id"): e for e in rows}
    fid = _cell("SALVO_FLAGSHIP"); p2 = _cell("SALVO_PART2")
    pr = APP.plan_row(fid, st) if fid in by else None; p = APP.numbers(pr)
    if pr and p is not None and str(pr.get("state") or "") == "open" and p2 and p2 in by and held(by[p2], st):
        sv = _salvo_of(fid, rows); seq = sv.get("sequel") if isinstance(sv.get("sequel"), dict) else {}
        p.update(held=p2, cliff=str(sv.get("cliff") or ""), line=str(seq.get("line") or ""))
        j = json.dumps(p, sort_keys=True)
        st.update("Appetite_Plans", "ep", fid, {"plan": j, "sha": APP.sha(j), "state": "frozen"}); out["frozen"] = fid
        log(f"{fid}: the launch flagship's appetite plan is frozen with its Part 2 {p2}", "INFO", fid)
    for ep in (fid, p2):
        e = by.get(ep) or {}
        if ep and e.get("status") == "AWAITING_APPROVAL" and "approved by him" in str((APP.plan_row(ep, st) or {}).get("note") or "") and pair_clear(ep, st)[0]:
            out[ep] = CON.approve(ep)
    return out


def back(ep, now=None):
    """v12 V4b step 6c (memo 1076-1080): "Bring it back" - a Part 2 his Undo made private goes public again through THE ONE DOOR,
    `hdgate.go_public(vid, now, "appetite back")`, with the status it had before the Undo: "LIVE" when its release step had run (nothing is
    posted twice), else "SCHEDULED" with `slot_et` that minute; `undone_at` is cleared. Never `yt_schedule`. contract.approve sends such a row
    here too."""
    from whatifs import hdgate as HG
    from whatifs.org import appetite as APP
    st = store(); r = APP.undone(ep, st); e = next((x for x in st.rows("Episodes") if x.get("episode_id") == ep), None) or {}
    if r is None or not e.get("yt_id"): return f"{ep}: nothing to bring back"
    now = now or now_utc(); ok, note = HG.go_public(e["yt_id"], now, "appetite back")
    if not ok: return f"Part 2 could not be made public again ({note}); it stays private - tap Bring it back again."
    was = (re.findall(r"was (LIVE|SCHEDULED)", str(r.get("note") or "")) or ["SCHEDULED"])[-1]
    st.update("Episodes", "episode_id", ep, {"status": was, "updated": iso(), **({} if was == "LIVE" else {"slot_et": iso(now)})})
    st.update("Appetite_Plans", "ep", r.get("ep"), {"undone_at": "", "note": f"{r.get('note') or ''}; brought back {iso(now)}".strip("; ")})
    return f"Part 2 is public again ({note})."


# ---------------------------------------------------------------- v12 V4b step 8a (memo 3.8, B7; items 128, 114): THE DEPTH PASS
# For a launch pair video (the flagship, a Part 2) while the credit's lane is open: ONE call answers four questions FOR THIS EPISODE and writes an
# addendum of at most 180 words; k of the room's drafts carry it between the markers (k = 2 in an odd-numbered contest of card "depth", 1 in an even
# one), frozen by its SHA-256 (check depth_frozen); the blind jury picks as today and ONE row of tab Contests says whether a depth draft won. THE READER
# closes it (depth_open): after DEPTH_MIN_CONTESTS contests it stays only with DEPTH_KEEP_WINS or more wins among the newest of them - an arm exactly
# as good as plain drafts stays 35% of the time (2,320 of 6,561) and is closed 65%: eight contests cannot see a small edge; the rule errs toward closing.
DEPTH_SYS = ("You prepare the writer of ONE episode. Answer four questions FOR THIS EPISODE only: (1) the expert's move - what someone who knows this "
             "subject would do or notice that a layman would not; (2) the rawest material - the concrete numbers, objects, places and events this story "
             "can show; (3) the methods and tools a real investigator of this question would use; (4) the outside judge - who outside the story would "
             "judge the answer, and what would convince them. Then write an addendum for the writer of at most 180 words. No name of a person, channel "
             "or account. Reply with JSON only: {\"answers\": [\"...\", \"...\", \"...\", \"...\"], \"addendum\": \"...\"}")
DEPTH_OPEN, DEPTH_CLOSE = "DEPTH BRIEF >>>", "<<<"
DEPTH_WORDS = 180
DEPTH_KEEP_WINS = 5            # wins among the newest DEPTH_MIN_CONTESTS (8) that keep the pass (memo 3.8: "5 or more wins of 8")
_MARK_RX = re.compile(re.escape(DEPTH_OPEN) + r"(.*?)" + re.escape(DEPTH_CLOSE), re.S)

def depth_on(): return S("DEPTH_ON", bool)

def _sha(text): return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

def won(r):
    """A Contests row's `won`: True when the arm's candidate won the blind jury."""
    return str((r or {}).get("won") or "").strip().upper() in ("TRUE", "1", "YES")

def contests(card, st=None):
    """The rows of tab Contests for one card, oldest first (append order)."""
    return [r for r in (st or store()).rows("Contests") if str(r.get("card") or "") == card]

def contest(card, video_key, n, k, win, note="", st=None):
    """ONE row of tab Contests: `n` the candidates the blind jury ranked, `k` those of the arm, `won` TRUE when the arm's candidate won."""
    (st or store()).append("Contests", [{"ts": iso(), "card": card, "video_key": str(video_key or ""), "n": int(n), "k": int(k),
                                         "won": "TRUE" if win else "FALSE", "note": str(note or "")[:300]}])

def depth_open(now=None):
    """R15 (review 14d) THE READER closes the depth pass, never a cell written from a rule: True while DEPTH_ON, the credit's lane is open and Claude
    may be used, AND NOT (the newest DEPTH_MIN_CONTESTS rows of tab Contests with card "depth" exist and hold fewer than DEPTH_KEEP_WINS won)."""
    if not depth_on(): return False
    from whatifs.org import finance as FIN
    from whatifs import governor as G
    try:
        if not (FIN.lane(now) and G.claude_allowed()): return False
        m = S("DEPTH_MIN_CONTESTS", int); rows = contests("depth")[-m:] if m > 0 else []
        return not (m > 0 and len(rows) >= m and sum(1 for r in rows if won(r)) < DEPTH_KEEP_WINS)
    except Exception as e:
        log(f"salvo: the depth pass was not read, so it is closed: {scrub(e)[:120]}", "WARN"); return False

def depth_due(d, now=None):
    """The depth call is made only for a draw with d['salvo'] (the flagship, a Part 2) and only while depth_open."""
    sv = d.get("salvo") if isinstance(d, dict) else None
    return isinstance(sv, dict) and sv.get("role") in ("flagship", "part2") and depth_open(now)

def depth_split(d, spine, ep, reqs, now=None):
    """room2.write's draft requests, before they are sent (DQ 7): for a launch pair video ONE call (route depth) answers the four questions and its
    addendum goes, with the helper the room uses before its JSON instruction, between the markers of k of the requests; d['depth'] = {sha, k, sent,
    won}. Returns, per request, whether it carries the brief (all False: no pass - fewer than 2 drafts, not due, or a reply without its parts)."""
    plain = [False] * len(reqs)
    if len(reqs) < 2 or not depth_due(d, now): return plain
    from whatifs.models import ask
    from whatifs import growth as GR
    sp = spine if isinstance(spine, dict) else {}
    try:
        r = ask("depth", DEPTH_SYS, f"PREMISE: {sp.get('premise', '')}\nPROMISE TO THE VIEWER: {GR.promise_text(sp.get('promise'))}\n"
                f"THIS VIDEO: {d['salvo'].get('role')} of the launch pair", episode=ep, fake_key="depth", max_tokens=2000)
    except Exception as e:
        log(f"salvo: the depth call failed - the drafts go plain: {scrub(e)[:160]}", "WARN", episode=ep); return plain
    r = r if isinstance(r, dict) else {}
    ans = [str(x).strip() for x in (r.get("answers") or []) if str(x).strip()]
    add = " ".join(str(r.get("addendum") or "").split()[:DEPTH_WORDS])
    if len(ans) != 4 or not add:
        log("salvo: the depth reply lacks its four answers or its addendum - the drafts go plain", "WARN", episode=ep); return plain
    nth = len(contests("depth")) + 1; k = min(2 if nth % 2 else 1, len(reqs) - 1)
    pick = [(nth + i) % len(reqs) for i in range(k)]
    for i in pick: reqs[i]["prompt"] = GR.insert_before_json(reqs[i]["prompt"], f"{DEPTH_OPEN}\n{add}\n{DEPTH_CLOSE}")
    d["depth"] = {"sha": _sha(add), "k": k, "sent": [], "won": None, "nth": nth, "answers": ans}
    log(f"salvo: the depth pass - contest {nth}, {k} of {len(reqs)} drafts carry the brief", episode=ep)
    return [i in pick for i in range(len(reqs))]

def marked(reqs):
    """The SHA-256 of the text between the depth markers of each request in `reqs` that carries them - the call site's record for depth_frozen."""
    out = []
    for q in reqs:
        m = _MARK_RX.search(str((q or {}).get("prompt") or ""))
        if m: out.append(_sha(m.group(1).strip()))
    return out

def depth_contest(d, ep, carried, win):
    """After the blind jury: d['depth']['won'] and ONE Contests row (card depth). Nothing without a depth pass."""
    dp = d.get("depth") if isinstance(d, dict) else None
    if not isinstance(dp, dict): return
    w = bool(carried[win]) if 0 <= win < len(carried) else False
    dp["won"] = w
    contest("depth", ep, len(carried), sum(1 for c in carried if c), w, f"contest {dp.get('nth')}: the jury chose {'a depth draft' if w else 'a plain draft'}")
