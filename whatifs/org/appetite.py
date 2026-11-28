"""The appetite engine (B3, items 141 and 148 to 150): every hour of a long video's first 48 it is read - views, likes, comments and the authors who ask for more - one row a video and hour. See docs/CURRENT/SYSTEM.md."""
# v12 V4b step 6 (memo 3.6; items 141, 148, 149, 150). TYPED SO FAR: THE READING (memo 1014-1020) - every hour of a long video's first 48, ONE
# `publish.yt_stats` for every video due and its newest 100 comments, kept on tab Appetite, one row per (video, hour), never rewritten. STEP 6a:
# THE PLAN, BEFORE THE FINAL GATE (`plan`, check `appetite_plan`); 6b's rest: THE LINE and THE FIRE (`line`, `fires`, `fire`; hour 48 is
# breakout.monitor's). The pair: salvo.pair_clear / pair / held (6a). STEP 6c SO FAR: `act` - the acts recorded OUTSIDE the sealed JSON (cell `acts`), c and d;
# b and the retry of a pending act (section 17); a - the release of the held Part 2 - and the 48-hour lapse (section 18); e (section 19); the row to him
# (`_word`), his Undo (`undo`), Bring it back (salvo.back, contract.approve's head branch) and `register` (section 20): 6c is whole.
from __future__ import annotations
import hashlib, json, re, statistics
from whatifs.core import S, store, log, iso, now_utc, parse_iso, scrub

ASK_RE = re.compile(r"\bpart\s*(2|two|ii)\b|\bnext (part|episode)\b|\bwhat happens (next|after)\b|\bsequel\b|\bmore of this\b|\bwhen is (the next|part)\b"
                    r"|\bto be continued\b", re.I)          # recognised only: nothing here is ever posted or answered

def on(): return S("APPETITE_ON", bool)

def asking_authors(comments):
    """The number of distinct authors of comments of 4 words or more that `community.triage` does not call spam risk and that match ASK_RE."""
    from whatifs import community as COM
    out = set()
    for c in comments or []:
        t = str(c.get("text") or "")
        if len(t.split()) >= 4 and COM.triage(t) != "spam_risk" and ASK_RE.search(t): out.add(str(c.get("author") or ""))
    out.discard("")                                             # a comment with no author's name is no author
    return len(out)

def read(now=None):
    """Every long video with a plan whose public time `slot_et` is 1 to 48 whole hours ago (h = the whole hours since) and no Appetite row at (video, h):
    ONE `PUB.yt_stats` for all of them, `community.fetch_comments(vid, 100)` each, one row each. A failed read - an id the statistics did not answer, or
    comments that raised - writes no row (a reading that failed is never a zero) and the next tick reads that hour again. Returns the rows written."""
    if not on(): return []
    from whatifs import publish as PUB, community as COM
    now = now or now_utc(); st = store()
    eps = {e.get("episode_id"): e for e in st.rows("Episodes")}
    have = {(str(r.get("yt_id")), str(r.get("h"))) for r in st.rows("Appetite")}
    due, plans = {}, {}
    for p in st.rows("Appetite_Plans"):
        e = eps.get(p.get("ep")); vid = str(p.get("yt_id") or (e or {}).get("yt_id") or "")      # RUL-U1c C4: a plan row whose yt_id write failed reads the Episodes row's id (episode.py:953 writes it first)
        t = parse_iso((e or {}).get("slot_et") or "")
        if not vid or t is None: continue                       # nothing uploaded yet, or no episode row: nothing to read
        h = int((now - t).total_seconds() // 3600)
        if 1 <= h <= 48 and (vid, str(h)) not in have: due.setdefault(vid, (p.get("ep"), h)); plans.setdefault(vid, numbers(p))
    if not due: return []
    stats, rows = PUB.yt_stats(list(due)), []
    for vid, (ep, h) in due.items():
        if vid not in stats: log(f"appetite: no statistics for {vid} at hour {h} - nothing written", "WARN"); continue
        try: n = asking_authors(COM.fetch_comments(vid, 100))
        except Exception as x: log(f"appetite: the comments of {vid} were not read ({scrub(x)}) - nothing written", "WARN"); continue
        s = stats[vid]; pj = plans.get(vid); L = line(pj, ep, h, st) if pj else None          # 6b: the line on the PLAN's numbers (none without a plan's JSON)
        f = bool(L is not None and h <= 47 and fires(pj, h, s.get("views"), n, L)) and fire(ep, vid, s.get("views"), round(L, 1), h, "the appetite line")   # hour 48: breakout.monitor's
        rows.append({"ts": iso(now), "ep": ep, "yt_id": vid, "h": h, "views": s.get("views"), "likes": s.get("likes"), "comments": s.get("comments"), "askers": n,
                     "line": "" if L is None else round(L, 1), "fired": f})
    if rows: st.append("Appetite", rows)
    return rows

_KEYS = ("first_h", "mult", "min_views", "min_history", "alone_x", "ask_authors")

def sha(j): return hashlib.sha256(str(j or "").encode("utf-8")).hexdigest()

def plan_row(ep, st=None):
    """The episode's ONE Appetite_Plans row (None when it has none)."""
    return next((r for r in (st or store()).rows("Appetite_Plans") if ep and str(r.get("ep") or "") == str(ep)), None)

def plan_of(y, key="", st=None):
    """The plan row of the video `y` (its yt_id), else of the episode `key`; None when neither has one."""
    st = st or store()
    return next((r for r in st.rows("Appetite_Plans") if y and str(r.get("yt_id") or "") == str(y)), None) or plan_row(key, st)

def numbers(r):
    """The plan's JSON of a plan row - the numbers every reading uses; None when the row holds no whole plan."""
    try: p = json.loads((r or {}).get("plan") or "")
    except (TypeError, ValueError): return None
    return p if isinstance(p, dict) and all(k in p for k in _KEYS) else None

def plan(ep, d, now=None):
    """THE PLAN, BEFORE THE FINAL GATE (memo 3.6, step 6a; R15 TO CORRECT 7): ONE Appetite_Plans row for the episode, written only when it has none
    (`_finish` runs again on a one-click fix and on a resumed job; a frozen row is never rewritten), holding the numbers every reading uses - the
    PLAN's, never the cells' of the day: nobody moves the line after seeing views. An ordinary long video and a Part 2 are frozen at once (`sha` =
    SHA-256 of the JSON); a flagship's row stays "open" until salvo.pair freezes it with its Part 2, its cliff and its line. With APPETITE_ON FALSE or
    the organisation off nothing is written. `yt_id` is a column outside the JSON, filled after the upload (`uploaded`). Returns the row, or None."""
    from whatifs.org import runner as ORG
    if not on() or not ORG.on(): return None
    st = store(); old = plan_row(ep, st)
    if old: return old
    sv = (d or {}).get("salvo") if isinstance((d or {}).get("salvo"), dict) else {}
    role = str(sv.get("role") or "") if str(sv.get("role") or "") in ("flagship", "part2") else "long"
    j = json.dumps({"first_h": S("APPETITE_FIRE_FROM_H", int), "last_h": 48, "mult": S("BREAKOUT_MULT", float), "min_views": S("BREAKOUT_MIN_VIEWS", float),
                    "min_history": S("BREAKOUT_MIN_HISTORY", int), "alone_x": S("APPETITE_ALONE_X", float), "ask_authors": S("APPETITE_ASK_AUTHORS", int),
                    "acts": [], "held": "", "cliff": "", "line": ""}, sort_keys=True)
    frozen = role != "flagship"
    row = {"ts": iso(now or now_utc()), "ep": ep, "role": role, "yt_id": "", "plan": j, "sha": sha(j) if frozen else "", "state": "frozen" if frozen else "open", "note": ""}
    st.append("Appetite_Plans", [row])
    return row

def uploaded(ep, vid):
    """After the upload: the plan row's `yt_id` (outside the JSON, so the seal holds)."""
    st = store()
    if vid and plan_row(ep, st): st.update("Appetite_Plans", "ep", ep, {"yt_id": vid})

def unsealed(r):
    """'' when the plan row is whole; else why not - a frozen row with no sha, or a JSON that no longer hashes to its sha."""
    if str(r.get("state") or "") in ("frozen", "fired") and not r.get("sha"): return f"the plan of {r.get('ep')} is {r.get('state')} with no sha: it was never sealed"
    if r.get("sha") and sha(r.get("plan")) != str(r.get("sha")): return f"the frozen plan of {r.get('ep')} no longer hashes to its sha: it was changed after it was frozen"
    return ""

def line(p, ep, h, st=None):
    """THE LINE (memo 3.6; one family, V4's own): L(h) = the plan's `mult` x the median of our EARLIER long videos' Appetite views at hour h when at
    least the plan's `min_history` of them have a row at h; else `min_views` x h / 48 (no history, hour 9: 375)."""
    st = st or store(); eps = {e.get("episode_id"): e for e in st.rows("Episodes")}
    me = parse_iso((eps.get(ep) or {}).get("slot_et") or ""); planned = {r.get("ep") for r in st.rows("Appetite_Plans")}
    hist = []
    for r in st.rows("Appetite"):
        t = parse_iso((eps.get(r.get("ep")) or {}).get("slot_et") or "")
        if str(r.get("h")) == str(h) and r.get("ep") != ep and r.get("ep") in planned and t is not None and me is not None and t < me and r.get("views") not in (None, ""):
            hist.append(float(r["views"]))
    if len(hist) >= int(p["min_history"]): return float(p["mult"]) * statistics.median(hist)
    return float(p["min_views"]) * h / 48

def fires(p, h, views, askers, L):
    """THE FIRE's rule (memo 3.6): from the plan's `first_h` on, views at the line with at least `ask_authors` asking authors, or `alone_x` x the line alone."""
    if views in (None, "") or L is None: return False
    v = float(views)
    return h >= int(p["first_h"]) and ((v >= L and int(askers or 0) >= int(p["ask_authors"])) or v >= float(p["alone_x"]) * L)

def fire(key, y, v, base, h, why):
    """THE FIRE (memo 3.6): ONE a video, ever - the plan row of video `y` (else of episode `key`) gets state "fired" and a note of the hour, the views,
    the line and why; a second fire, or a video with no plan, does nothing. Hours 6 to 47 come from `read`; hour 48 from breakout.monitor's own hit
    (the 48-hour rule, V4's, unchanged). Returns True only when this call fired. Its acts: `act`, in the same call (step 6c)."""
    st = store(); r = plan_of(y, key, st)
    if not r or str(r.get("state") or "") == "fired": return False
    n = f"fired at hour {h}: {v} views, the line {base if base is not None else '-'} ({why}) {iso(now_utc())}"
    st.update("Appetite_Plans", "ep", r.get("ep"), {"state": "fired", "fired_at": iso(now_utc()), "fired_read": json.dumps({"key": key, "y": y, "views": v, "base": base, "h": h}), "note": "; ".join(x for x in (str(r.get("note") or ""), n) if x)})
    log(f"appetite: {r.get('ep')} FIRED - {n}", "INFO", r.get("ep"))
    try: act(r.get("ep"))                                              # v12 V4b step 6c (memo 3.6): THE ACTS ON A FIRE, in the SAME tick
    except Exception as x: log(f"appetite: the acts of {r.get('ep')} raised ({scrub(x)}) - the fire stands, its acts stay unrecorded", "WARN", r.get("ep"))
    return True


def acts(r):
    """The acts recorded on plan row `r` (memo 3.6, step 6c): {act: "<made | done | pending | refused | not made>: <what was read back>"} from its
    cell `acts` - OUTSIDE the sealed JSON, whose `acts` [] stays as it was hashed (section 13's choice 1). An unreadable cell refuses every act (an ERROR; RUL-U1c C1)."""
    cell = str((r or {}).get("acts") or "")
    try: a = json.loads(cell or "{}")
    except Exception: a = None
    if isinstance(a, dict): return a
    ep = (r or {}).get("ep")
    log(f"appetite: the acts cell of {ep} cannot be read ({cell[:80]!r}) - no act is made again", "ERROR", ep)      # RUL-U1c C1: never {} (every act would run again: a second public comment)
    try:
        from whatifs import notify as NT
        NT.send("appetite", f"The record of what was done for '{ep}' after Part 1 passed its appetite line could not be read, so no act is made again (no second comment, no second release). Nothing to do.",
                episode=ep, expires_h=168, dedupe_key=f"appetite|acts|{ep}")      # RUL-U1c C1: an owner row for a refused act (it never raises)
    except Exception as x: log(f"appetite: the row to him for the unreadable acts of {ep} was not sent: {str(x)[:120]}", "WARN", ep)
    return {k: "refused: the acts cell could not be read - no act is made again" for k in "abcde"}

def retry(now=None):
    """v12 V4b step 6c (memo 3.6, R23 (12)): every tick, BEFORE `hdgate.tick` (manage.tick), the acts of every FIRED plan row that are still
    "pending" (or not yet recorded) are tried again by `act`; a recorded act is never made again. Returns the episodes tried."""
    st = store(); out = []
    for r in st.rows("Appetite_Plans"):
        if str(r.get("state") or "") != "fired": continue
        a = acts(r)
        if all(k in a for k in "abcde") and not any(str(v).startswith("pending") for v in a.values()): continue
        try: act(r.get("ep"), now); out.append(r.get("ep"))
        except Exception as x: log(f"appetite: the acts of {r.get('ep')} were not tried again: {str(x)[:120]}", "WARN", r.get("ep"))
    return out


def _since(r, now=None):
    """Seconds since plan row `r` fired (its cell `fired_at`, written by `fire`; an older row: its `ts`); None when neither reads."""
    try: t = parse_iso(str(r.get("fired_at") or r.get("ts") or ""))
    except Exception: t = None
    return max(0.0, ((now or now_utc()) - t).total_seconds()) if t else None      # RUL-U1c C2: an unreadable time is never "0 seconds" (the act would never lapse)

def _act_a(r, p, eps, st, now=None):
    """ACT a (memo 3.6; R15, R18, R19 (12), R23 (12)): RELEASE THE HELD PART 2. ONE condition for both statuses: `contract.clear_to_post(<part 2>,
    scheduled=True)`; while it is false the act stays "pending" - and a row of Part 2 still WAITING on HD_Wait is blocked first (`hdgate.block`): his
    Hold between two tries is never answered by the gate making the video public. THE DOOR: `got = publish.yt_read`; an empty read stays pending (the
    cap never lets an UNREAD video in); `hdgate.ready(got)`, or HD_LONG_CAP_MIN minutes since the fire -> the row is entered AT THIS MOMENT (never
    earlier) and `hdgate.go_public(vid, now, "appetite")` - never `yt_set_privacy`. (False, "not read") stays pending; every other False is "refused:
    <note>" and nothing else is done. OK - or Part 2 already reads public (`go_public` never a second time): `publish.seen_public`; a row not yet LIVE
    gets status "SCHEDULED" and `slot_et` = this minute (its calendar slot kept in `notes`: "calendar slot <iso>"), `public_at` untouched (the gate
    is its one writer), `hd_gate` = the note when empty; its OPEN review card (`review|<id>`) is closed "released early"."""
    from whatifs import publish as PUB, contract as CON, hdgate as HG
    now = now or now_utc(); held = str(p.get("held") or ""); e2 = eps.get(held) or {}; vid = str(e2.get("yt_id") or "")
    if not held: return "not made: no held Part 2 - nothing to release"
    if not vid: return "pending: Part 2 has no yt_id"
    got = PUB.yt_read(vid) or {}
    if got.get("privacy") == "public": note = "Part 2 already read public"
    else:
        ok, why = CON.clear_to_post(held, scheduled=True); w = HG.row(vid)
        if not ok:
            if w and w.get("state") == HG.WAITING: HG.block(vid, f"its early release was stopped: {why}", got, now)
            return f"pending: {why}"
        if not got: return "pending: Part 2 was not read"
        if not HG.ready(got) and (_since(r, now) is None or _since(r, now) < S("HD_LONG_CAP_MIN", int) * 60): return "pending: YouTube has not processed Part 2 in HD yet"
        if w is None: HG.enter(vid, "long", now)
        ok, note = HG.go_public(vid, now, "appetite")
        if not ok: return "pending: Part 2 was not read at the door" if note == "not read" else f"refused: {note}"
    PUB.seen_public(vid, now)
    if str(e2.get("status") or "") != "LIVE":
        cal = str(e2.get("slot_et") or ""); notes = "; ".join(x for x in (str(e2.get("notes") or ""), f"calendar slot {cal}" if cal else "") if x)
        upd = {"status": "SCHEDULED", "slot_et": iso(now), "notes": notes, "updated": iso()}
        if not str(e2.get("hd_gate") or ""): upd["hd_gate"] = str(note)[:300]
        st.update("Episodes", "episode_id", held, upd)
    for o in st.rows("Owner_Actions"):
        if o.get("dedupe_key") == f"review|{held}" and o.get("status") in ("OPEN", "QUEUED"):
            st.update("Owner_Actions", "id", o["id"], {"status": "ANSWERED", "answered_at": iso(), "answer": "released early"})
    return f"made: Part 2 reads public - {note}"


def _act_e(r, eps, st, now=None):
    """v12 V4b step 6c (memo 3.6, act e): THE NEXT RELATED SHORT FORWARD - `ladder.order_followup(key, y, views, base, h, now, kind="long video",
    line=L)` for EVERY long video, the override's too, from the fire's own reading (cell `fired_read`, written by `fire`): hours 6 to 47 come from
    `read`, whose `base` IS the appetite line L (no usual); hour 48 from breakout.monitor, whose `base` is the usual and L = BREAKOUT_MIN_VIEWS. The
    order's own message is the turned card (item 150): "Nothing to do", with "Stop it". The order's premise: `shorts2._order_premise` (an override
    row's topic is its own id - the episode's premise is read). An order already standing for the video is read back, never made twice."""
    from whatifs import ladder as LAD
    try: f = json.loads(str(r.get("fired_read") or "") or "{}")
    except Exception: f = {}
    if not isinstance(f, dict) or f.get("views") in (None, "") or f.get("h") in (None, ""): return "not made: the fire's reading was not recorded"
    key = str(f.get("key") or r.get("ep") or ""); y = str(f.get("y") or r.get("yt_id") or ""); h = int(float(f["h"])); v = float(f["views"])
    b = None if f.get("base") in (None, "") else float(f["base"])
    base, L = (None, b) if h <= 47 else (b, S("BREAKOUT_MIN_VIEWS", float))
    q = LAD.order_followup(key, y, v, base, h, now, kind="long video", line=L)
    if q: return f"made: one follow-up Short ordered for {key}, due {q.get('due') if isinstance(q, dict) else q}"
    old = next((x for x in st.rows(LAD.QUEUE) if x.get("video_key") == key), None)
    return f"done: the follow-up order of {key} already stands ({old.get('status')})" if old else "refused: no order was written"


def _num(x):
    try: return float(x)
    except Exception: return 0.0

def _word(r, held, said, eps, st, now=None):
    """v12 V4b step 6c (memo 1068-1073): THE ROW TO HIM, ONE a fire with a held Part 2, sent when act a is made: kind "appetite" (INFORM, group
    "decided", in notify.STANDING_KINDS), ("Undo", "APPETITE UNDO <part 2 id>"), `expires_h=168`; the numbers are the fire's own (`fired_read`; the
    line as `_act_e` reads it) and the asking authors of that hour's Appetite row. A lapsed act a is said in the same row, with no Undo."""
    from whatifs import notify as NT
    try: fr = json.loads(str(r.get("fired_read") or "") or "{}")
    except Exception: fr = {}
    fr = fr if isinstance(fr, dict) else {}
    h = int(_num(fr.get("h"))); views = int(_num(fr.get("views"))); title = str((eps.get(r.get("ep")) or {}).get("title") or r.get("ep"))
    if said.startswith("lapsed"):
        return NT.send("appetite", f"'{title}' passed its appetite line at hour {h}, but Part 2 was not released early ({said.split(':', 1)[-1].strip()}). "
                       "Part 2 stays as it was. Nothing to do.", episode=held, expires_h=168, dedupe_key=f"appetite|{held}")
    L = _num(fr.get("base")) if h <= 47 else S("BREAKOUT_MIN_VIEWS", float)
    rd = next((x for x in st.rows("Appetite") if str(x.get("ep")) == str(r.get("ep")) and int(_num(x.get("h"))) == h), None)      # RUL-U1c A3: the row `read` writes (ep, h, askers)
    asked = f"{int(_num(rd.get('askers')))} viewers asked for more" if rd else "the viewers who asked for more were not read for that hour"; vid = str((eps.get(held) or {}).get("yt_id") or "")
    return NT.send("appetite", f"Part 2 is public since {iso(now or now_utc())}: '{title}' had {views} views at hour {h} (the line was {L:g}) and {asked}. "
                   f"Saturday's slot stays empty. Optional, ten seconds in Studio: pin the top comment, set the end screen to Part 2 "
                   f"https://youtu.be/{vid}. Undo makes it private again: your own hold on your own video, never the engine's.",
                   [("Undo", f"APPETITE UNDO {held}")], episode=held, expires_h=168, dedupe_key=f"appetite|{held}")

def _p2_row(ep, st):
    """The plan row his Undo of Part 2 `ep` is written on (memo 1074-1075): Part 2's own, else the fired row whose frozen plan holds it."""
    r = plan_row(ep, st)
    if r: return r
    for x in st.rows("Appetite_Plans"):
        try: j = json.loads(str(x.get("plan") or "") or "{}")
        except Exception: j = {}
        if isinstance(j, dict) and str(j.get("held") or "") == ep and str(x.get("state") or "") == "fired": return x
    return None

def undone(ep, st=None):
    """The plan row of Part 2 `ep` while his Undo stands (`undone_at` set), else None: contract.approve's head branch and salvo.back read it."""
    r = _p2_row(ep, st or store())
    return r if r and str(r.get("undone_at") or "") else None

def undo(ep, now=None):
    """v12 V4b step 6c (memo 1073-1077): HIS UNDO of an early release = B-OWNER's `contract.unpost(ep, verdict=False)` (REUSED: private, status
    HELD_BY_OWNER, no "down" verdict - "not yet" is no judgement of the film), READ BACK private, then `undone_at` and the status before it ("was
    LIVE" / "was SCHEDULED") on the plan row and ONE more "appetite" row with ("Bring it back", "APPETITE BACK <id>") and NO expiry. Never a delete,
    never `yt_schedule`."""
    from whatifs import contract as CON, publish as PUB, notify as NT
    st = store(); e = next((x for x in st.rows("Episodes") if x.get("episode_id") == ep), None) or {}; r = _p2_row(ep, st)
    if not e.get("yt_id") or r is None: return f"{ep}: no early release to undo"
    if str(r.get("undone_at") or ""): return "Part 2 is already private. It stays private until you tap Bring it back."
    was = "LIVE" if str(e.get("status") or "") == "LIVE" else "SCHEDULED"
    said = CON.unpost(ep, verdict=False)
    if (PUB.yt_read(e["yt_id"]) or {}).get("privacy") != "private": return said
    t = iso(now or now_utc()); note = "; ".join(x for x in (str(r.get("note") or ""), f"was {was}") if x)
    st.update("Appetite_Plans", "ep", r.get("ep"), {"undone_at": t, "note": note})
    text = "Part 2 is private again. It stays private until you tap Bring it back."
    NT.send("appetite", text, [("Bring it back", f"APPETITE BACK {ep}")], episode=ep, expires_h=None, dedupe_key=f"appetite|back|{ep}|{t}")
    return text

def _answer(row, choice):
    """His taps on an "appetite" row (memo 1071-1078): APPETITE UNDO <id> -> `undo`; APPETITE BACK <id> -> `salvo.back`; a Bring it back that did
    not go public opens its row again (it is the only way back)."""
    parts = str(choice).split()
    if len(parts) < 3 or parts[0].upper() != "APPETITE": return f"not an appetite answer: {choice}"
    if parts[1].upper() == "UNDO": return undo(parts[2])
    if parts[1].upper() != "BACK": return f"not an appetite answer: {choice}"
    from whatifs.org import salvo as SAL
    out = SAL.back(parts[2])
    if not out.startswith("Part 2 is public again"): store().update("Owner_Actions", "id", row["id"], {"status": "OPEN", "answered_at": "", "answer": ""})
    return out

def register():
    """Both verbs of kind "appetite" (the house pattern: contract.register); notify._ensure_handlers calls it before any answer runs."""
    from whatifs import notify as NT
    NT.register("appetite", on_answer=_answer)

def act(ep, now=None):
    """THE ACTS ON A FIRE (memo 3.6, step 6c) for the FIRED plan row of episode `ep`, each recorded in its cell `acts` with what was read back; an
    act already recorded is never made again - only a "pending" one is tried again. TYPED: c - PART 2's LINK FIRST IN THE FLAGSHIP'S DESCRIPTION
    (`PUB.yt_set_description`), only after Part 2 (the frozen plan's `held`) READS public and only when packaging.may_edit's test rule (a) passes
    for the flagship, else "not made: <why>"; d - THE PLAYLIST: nothing to send, recorded; b (section 17) - THE CHANNEL'S COMMENT on the flagship,
    the plan's `line` + Part 2's link, only after Part 2 READS public and the line passes salvo.line_ok again; `retry` tries a pending act at every
    tick; a (section 18) - THE RELEASE OF THE HELD PART 2, FIRST (`_act_a`), so b and c read it public in the same call; an act still pending
    APPETITE_PENDING_H hours after the fire is recorded "lapsed: <why>" and never tried again. e (section 19) - THE NEXT RELATED SHORT FORWARD (`_act_e`), for every long video. The row to
    him (`_word`, section 20): ONCE a fire with a held Part 2, when act a is made or lapses. Returns the acts recorded."""
    from whatifs import publish as PUB, packaging as PK
    from whatifs.org import salvo as SAL
    st = store(); r = plan_row(ep, st)
    if not r or str(r.get("state") or "") != "fired": return {}
    done = acts(r)
    try: p = json.loads(str(r.get("plan") or "") or "{}")
    except Exception: p = {}
    eps = {e.get("episode_id"): e for e in st.rows("Episodes")}
    def todo(k): return str(done.get(k) or "pending").startswith("pending")
    if todo("a"): done["a"] = _act_a(r, p if isinstance(p, dict) else {}, eps, st, now)    # a - FIRST: b and c read Part 2 public in the same call
    if todo("c"):
        held = str((p if isinstance(p, dict) else {}).get("held") or ""); e2 = eps.get(held) or {}; fl = eps.get(r.get("ep")) or {}
        fv = str(r.get("yt_id") or fl.get("yt_id") or "")
        if not held: done["c"] = "not made: no held Part 2 - nothing to link"
        elif not e2.get("yt_id") or not fv: done["c"] = "pending: " + ("Part 2 has no yt_id" if not e2.get("yt_id") else "the flagship has no yt_id")
        else:
            g2 = PUB.yt_read(e2["yt_id"]) or {}; link = f"Part 2: https://youtu.be/{e2['yt_id']}"
            ok, why = PK.may_edit(fl, now, clock=False)
            if g2.get("privacy") != "public": done["c"] = f"pending: Part 2 reads {g2.get('privacy') or 'nothing'}"
            elif not ok: done["c"] = f"not made: {why}"
            else:
                g = PUB.yt_read(fv) or {}; old = str(g.get("description") or "")
                if not g: done["c"] = "pending: the flagship was not read"
                elif old.startswith(link): done["c"] = f"made: read back '{link}' first"
                elif not PUB.yt_set_description(fv, link + "\n\n" + old): done["c"] = "refused: YouTube did not take the description"
                else:
                    back = str((PUB.yt_read(fv) or {}).get("description") or "")
                    done["c"] = f"made: read back '{link}' first" if back.startswith(link) else f"refused: the read-back does not start with '{link}'"
    if todo("b"):                                                     # b - THE CHANNEL'S OWN COMMENT on the flagship, only after Part 2 READS public
        held = str((p if isinstance(p, dict) else {}).get("held") or ""); e2 = eps.get(held) or {}; fl = eps.get(r.get("ep")) or {}
        fv = str(r.get("yt_id") or fl.get("yt_id") or ""); ln = str((p if isinstance(p, dict) else {}).get("line") or "").strip()
        if not held: done["b"] = "not made: no held Part 2 - nothing to link"
        elif not e2.get("yt_id") or not fv: done["b"] = "pending: " + ("Part 2 has no yt_id" if not e2.get("yt_id") else "the flagship has no yt_id")
        else:
            g2 = PUB.yt_read(e2["yt_id"]) or {}
            if g2.get("privacy") != "public": done["b"] = f"pending: Part 2 reads {g2.get('privacy') or 'nothing'}"
            elif not ln or not SAL.line_ok(ln, st, own=str(r.get("ep") or "")): done["b"] = "not made: the line failed its guard (salvo.line_ok) - nothing posted"
            else:
                cid = PUB.yt_comment(fv, f"{ln} https://youtu.be/{e2['yt_id']}")
                done["b"] = f"made: comment {cid} kept by YouTube" if cid else "refused: YouTube kept no comment"     # yt_comment answers what YouTube KEPT (P23)
    if todo("d"): done["d"] = "done: nothing sent - every long video is in its family's playlist since its upload (episode.py)"
    if todo("e"): done["e"] = _act_e(r, eps, st, now)             # e - THE NEXT RELATED SHORT FORWARD, for every long video (the override's too)
    lim = S("APPETITE_PENDING_H", int)
    if _since(r, now) is None or _since(r, now) >= lim * 3600:                                  # the lapse (memo 3.6, act a): ONE fire a video - a pending act is not tried for ever; RUL-U1c C2: a fire time that cannot be read lapses the pending acts (said to him), never retried for ever
        for k, v in list(done.items()):
            if str(v).startswith("pending"):
                done[k] = f"lapsed: {str(v).split(':', 1)[-1].strip()} - still pending {lim} hours after the fire"
                log(f"appetite: {r.get('ep')} act {k} LAPSED - {done[k]}", "WARN", r.get("ep"))
    held = str((p if isinstance(p, dict) else {}).get("held") or ""); said = str(done.get("a") or "")
    if held and said.startswith(("made", "lapsed")) and not str(acts(r).get("a") or "").startswith(("made", "lapsed")):      # the row to him: ONCE, when act a is made or lapses
        try: _word(r, held, said, eps, st, now)
        except Exception as x: log(f"appetite: the row to him for {held} was not sent: {str(x)[:120]}", "WARN", r.get("ep"))
    st.update("Appetite_Plans", "ep", r.get("ep"), {"acts": json.dumps(done, sort_keys=True)})
    log(f"appetite: {r.get('ep')} acts {done}", "INFO", r.get("ep"))
    return done
