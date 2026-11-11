"""The ladder (Growth and Learning, D10): every topic starts as a Short - each Short's real numbers are written onto one record, the promote rule picks the long video's topic by code, a long video without a promoted Short is refused unless the owner's override is recorded, and a winner's follow-up Short is ordered with a clock. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, json, math, os, zipfile
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub

TAB = "Ladder"
CANDIDATE = ("POSTED", "READ")          # a Short that can still be promoted (READ = it has a reading)
TAKEN = ("PROMOTED", "USED")            # its topic has a long video, or is the next one
LAPSE_X = 2                             # a follow-up order this many times its clock old is given up (the wave has passed)
MEASURES = ("engaged", "watched", "subs_rate", "shares_rate")      # what the promote rule ranks a measured Short on
QUEUE = "Breakout_Queue"

def on():
    """Does the ladder bind long videos? Only while Shorts are made at all: with the Shorts track off no topic could ever climb."""
    return S("LADDER_ON", bool) and S("SHORTS_TRACK_ON", bool)

def _n(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

def rows():
    try: return store().rows(TAB)
    except Exception: return []

def row(i):
    return next((r for r in rows() if r.get("id") == i), None) if i else None

def _set(i, **kw): store().update(TAB, "id", i, kw)

def _note(r, add): return (str(r.get("note") or "") + ("; " if r.get("note") else "") + add)[:300]

def posted_at():
    """{Short id: when it really went public} - a Short the owner had to approve first is public later than it was made."""
    return {r.get("id"): r.get("posted") for r in rows() if r.get("posted")}

# ------------------------------------------------------------------ a Short enters, and what it was made of is kept
def keep(ep, wd, sc, pl, tl):
    """Keep what a Short was made of - every paid clip as made, every start picture, the script, the plan and the voice timeline - as ONE archive in
    Drive: the opening of the long video its topic may earn. Returns the Drive id ('' when it could not be kept: a Short is never lost for that)."""
    try:
        from whatifs import publish as PUB
        z = os.path.join(wd, f"{ep}_footage.zip"); clips = 0
        with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as f:
            for s in (pl or {}).get("shots") or []:
                if s.get("src") == "loop": continue                      # the loop shot is the first clip played backwards: nothing new to keep
                for name in (f"c{s['i']}.mp4", f"f{s['i']}.png"):
                    p = os.path.join(wd, name)
                    if os.path.exists(p): f.write(p, name); clips += name.endswith(".mp4")
            f.writestr("short.json", json.dumps({"id": ep, "script": {k: (sc or {}).get(k) for k in ("title", "promise", "beats")}, "plan": pl, "timeline": tl}, ensure_ascii=False, default=str))
        if not clips: raise RuntimeError("no clip was found to keep")
        fid, _url = PUB.drive_upload(z, f"{ep}_footage.zip")
        return str(fid)
    except Exception as e:
        log(f"the footage of Short {ep} was not kept ({scrub(e)[:120]}): its long video would have to open with new pictures", "WARN", ep); return ""

def enter(rec, topic=None, footage=""):
    """A Short that was made takes its step on the ladder (once per Short). A follow-up belongs to the topic of the Short it follows."""
    st = store(); sid = str((rec or {}).get("id") or "")
    if not sid or any(r.get("id") == sid for r in st.rows(TAB)): return False
    parent = row(str((topic or {}).get("follow_of") or "")); yt = str(rec.get("yt_id") or "")
    st.append(TAB, [{"id": sid, "topic": (parent or {}).get("topic") or sid, "premise": str(rec.get("premise") or ""), "title": str(rec.get("title") or "")[:120],
                     "format": rec.get("format", ""), "hook": rec.get("hook", ""), "yt_id": yt, "posted": (rec.get("ts") or iso()) if yt else "", "state": "POSTED" if yt else "MADE",
                     "footage": footage, "by": "D14", "note": (f"follow-up of {parent['id']}" if parent else "") + ("" if footage else ("; " if parent else "") + "footage not kept")}])
    return True

def _drop_footage(r):
    fid = str(r.get("footage") or "")
    if not fid: return
    try:
        from whatifs import publish as PUB; PUB.drive_delete(fid)
    except Exception as e: log(f"kept footage {fid} not deleted: {scrub(e)[:80]}", "WARN")

# ------------------------------------------------------------------ the reading: both clocks written onto the record
def read(now=None):
    """Write what is known about every Short that can still be promoted onto its row. No API call is made here: the SLOW clock's numbers (engaged
    views, share watched, subscribers, shares - 48 to 72 hours late) were read by the learning job (`brain.ingest_shorts`, tab Analytics) and the
    FAST clock's public views at the 24-hour and 48-hour mark by the tick's monitor (tab Monitor48). A reading counts as 'measured' only when it
    covers the Short's first LADDER_READ_DAYS processed days; a Short past LADDER_WINDOW_DAYS is passed over and its kept footage deleted.
    Returns how many rows changed."""
    from whatifs import brain as BR
    now = now or now_utc(); st = store(); n = 0
    sp = {r.get("id"): r for r in st.rows("Specials")}
    an = {r.get("yt_id"): r for r in st.rows("Analytics") if r.get("yt_id")}
    mon = {r.get("yt_id"): r for r in st.rows("Monitor48") if r.get("yt_id")}
    win = max(1, S("LADDER_WINDOW_DAYS", int))
    for r0 in st.rows(TAB):
        r = dict(r0); upd = {}
        if r.get("state") == "MADE":                                     # it waited for the owner's Approve: public once its row on tab Specials has a YouTube id
            y = str((sp.get(r["id"]) or {}).get("yt_id") or "")
            if y: upd.update(yt_id=y, posted=iso(now), state="POSTED"); r.update(upd)
        if r.get("state") in CANDIDATE:
            t = parse_iso(r.get("posted"))
            if t and (now - t).days > win:
                upd.update(state="PASSED", note=_note(r, f"left the {win}-day window without a long video")); _drop_footage(r); upd["footage"] = ""
            else:
                a = an.get(r.get("yt_id")); m = mon.get(r.get("yt_id")) or {}
                if a and a.get("days") not in (None, "") and BR.reading_complete(a):
                    upd.update(evidence="measured", days=int(_n(a.get("days"))), views=int(_n(a.get("views"))), engaged=int(_n(a.get("engaged_views"))),
                               watched=round(_n(a.get("avg_view_pct")), 1), shares=int(_n(a.get("shares"))), subs=int(_n(a.get("subs"))), first=str(a.get("first_json") or ""))
                for k in ("v24", "v48"):
                    if m.get(k) not in (None, ""): upd[k] = int(_n(m.get(k)))
                ev = upd.get("evidence") or r.get("evidence") or ""
                if not ev and upd.get("v48", r.get("v48")) not in (None, ""): ev = upd["evidence"] = "public"
                if ev or _n(r.get("multiple")) > 0: upd["state"] = "READ"
        changed = {k: v for k, v in upd.items() if str(r0.get(k, "") if r0.get(k) is not None else "") != str(v)}
        if changed: st.update(TAB, "id", r0["id"], dict(changed, read_at=iso(now))); n += 1
    return n

# ------------------------------------------------------------------ the promote rule (pure code)
def wilson(k, n, z=1.96):
    """The lower bound of the Wilson score interval for k of n (95%): a share that few viewers produced is trusted less than the same share from many."""
    k, n = max(0.0, _n(k)), _n(n)
    if n <= 0: return 0.0
    p = min(1.0, k / n)
    return max(0.0, (p + z * z / (2 * n) - z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / (1 + z * z / n))

def measures(r):
    """What the promote rule ranks one measured Short on: {engaged, watched, subs_rate, shares_rate} (higher is better for each)."""
    e = _n(r.get("engaged"))
    return {"engaged": e, "watched": _n(r.get("watched")), "subs_rate": wilson(r.get("subs"), e), "shares_rate": wilson(r.get("shares"), e)}

def _borda(group):
    """Order a group of measured Shorts by the sum of their ranks over MEASURES (1 = best; equal values share a rank); ties go to the more engaged
    views, then to the newer Short. Returns [(row, rank sum)]."""
    ms = {r["id"]: measures(r) for r in group}; total = {r["id"]: 0 for r in group}
    for k in MEASURES:
        vals = sorted({ms[i][k] for i in ms}, reverse=True)
        for i in ms: total[i] += vals.index(ms[i][k]) + 1
    def newer(r): t = parse_iso(r.get("posted")); return -(t.timestamp() if t else 0.0)
    return sorted(((r, total[r["id"]]) for r in group), key=lambda x: (x[1], -ms[x[0]["id"]]["engaged"], newer(x[0])))

def rank(cands, min_engaged=None):
    """The promote rule: (class, [(row, why)]) - the best non-empty class of evidence, best first. (1) 'winner': a Short the fast clock declared, by
    its multiple of the channel's median. (2) 'measured': the lowest sum of ranks over engaged views, share watched, subscribers per engaged view and
    shares per engaged view (the two rates by their Wilson lower bound); a Short under LADDER_MIN_ENGAGED engaged views comes after every Short above
    it and says 'thin evidence'. (3) 'public': public views at the 48-hour mark. Engaged views divided by views is never ranked on: a replay of a
    looping Short is a view and never an engaged view."""
    lo = S("LADDER_MIN_ENGAGED", int) if min_engaged is None else min_engaged
    win = sorted((r for r in cands if _n(r.get("multiple")) > 0), key=lambda r: -_n(r.get("multiple")))
    if win: return "winner", [(r, f"a winner: {_n(r.get('multiple')):.1f} times the channel's usual views at the same age") for r in win]
    meas = [r for r in cands if r.get("evidence") == "measured"]
    if meas:
        out = []
        for thin, group in ((False, [r for r in meas if _n(r.get("engaged")) >= lo]), (True, [r for r in meas if _n(r.get("engaged")) < lo])):
            for r, tot in _borda(group):
                out.append((r, f"rank sum {tot} over {len(MEASURES)} measures among {len(group)}: {int(_n(r.get('engaged')))} engaged views, {_n(r.get('watched')):.0f}% watched, "
                               f"{int(_n(r.get('subs')))} subscribers, {int(_n(r.get('shares')))} shares in {int(_n(r.get('days')))} processed days"
                               + (f"; THIN EVIDENCE (under {lo} engaged views)" if thin else "")))
        return "measured", out
    pub = sorted((r for r in cands if r.get("evidence") == "public"), key=lambda r: -_n(r.get("v48")))
    if pub: return "public", [(r, f"public views only (the true numbers are not processed yet): {int(_n(r.get('v48')))} at the 48-hour mark") for r in pub]
    return "", []

def candidates(rs=None):
    """The Shorts that can be promoted now: they have a reading, and their TOPIC has no long video and is not waiting for one."""
    rs = rows() if rs is None else rs
    used = {r.get("topic") for r in rs if r.get("state") in TAKEN}
    return [r for r in rs if r.get("state") == "READ" and r.get("topic") not in used]

def waiting(rs=None):
    """The promoted Short that waits for its long video (the oldest), or None."""
    return next((r for r in (rows() if rs is None else rs) if r.get("state") == "PROMOTED"), None)

def waiting_override(rs=None):
    return next((r for r in (rows() if rs is None else rs) if r.get("state") == "OVERRIDE"), None)

# ------------------------------------------------------------------ D10's run: promote
def _promote(now):
    read(now); rs = rows()
    have = waiting(rs)
    if have: return {"row": have, "new": False, "class": "", "pool": 0, "why": "already promoted"}
    cands = candidates(rs); klass, order = rank(cands)
    if not order: return {"row": None, "new": False, "class": "", "pool": len(cands), "why": why_not(now, rs)}
    best, why = order[0]
    _set(best["id"], state="PROMOTED", promoted_at=iso(now), score=f"{klass}: {why}"[:300], by="D10")
    log(f"ladder: Short {best['id']} ('{best.get('title')}') is promoted to the next long video - {klass}: {why}")
    return {"row": row(best["id"]), "new": True, "class": klass, "pool": len(cands), "why": why}

def m_promote(out):
    r = (out or {}).get("row") or {}
    return {"promoted": 1 if (out or {}).get("new") else 0, "pool": int((out or {}).get("pool") or 0), "engaged": int(_n(r.get("engaged"))), "watched": _n(r.get("watched"))}

def _promote_memos(out, brief):
    """emit hook: a promotion is told to the departments that will make the long video (a performance memo: the Short's real numbers)."""
    r = (out or {}).get("row")
    if not r or not (out or {}).get("new"): return []
    met = {k: r.get(k) for k in ("views", "engaged", "watched", "shares", "subs", "days", "v24", "v48", "multiple") if r.get(k) not in (None, "")} or {"class": out.get("class")}
    return [{"type": "performance_memo", "from_dept": "D10", "to_depts": ["D4", "D14", "D9"], "subject": f"Short {r['id']} is promoted: its topic gets the next long video"[:140],
             "body": {"window": "48h", "video": str(r["id"])[:60], "metrics": met, "changes": [f"promoted ({out.get('class')}): {str(out.get('why'))[:240]}", f"the topic: {str(r.get('premise'))[:240]}"]},
             "dedupe_key": f"ladder|promote|{r['id']}",
             "evidence": [{"source": f"Ladder:{r['id']}", "date": iso()[:10], "type": "own data", "finding": f"{out.get('class')}: {str(out.get('why'))[:260]}"}]}]

def promote(now=None):
    """Growth and Learning's run `promote`: read both clocks, and when no promoted Short is waiting, promote the best candidate by the rule. Returns
    the waiting row (new or not) or None. Called when a long video is about to start - never on a schedule a dropped job could miss."""
    from whatifs.org import runner as ORG
    now = now or now_utc()
    out = ORG.work("D10", "promote", "", lambda b: _promote(now), measure=m_promote, emit=_promote_memos)
    r = (out or {}).get("row")
    if r and out.get("new"):
        try:
            from whatifs import notify as NT
            NT.send("ladder", f"Next long video: \"{r.get('title') or r.get('premise')}\" - its Short did best of {out.get('pool')} ({out.get('class')}: {str(out.get('why'))[:200]}). "
                    "Nothing to do. Tap only if you want another topic.", [("Not this one", f"LADDER SKIP {r['id']}")], tier="digest", default="this topic is made",
                    expires_h=72, dedupe_key=f"ladder|promote|{r['id']}")
        except Exception as e: log(f"promotion not announced: {scrub(e)[:100]}", "WARN")
    return r

def why_not(now=None, rs=None):
    """In plain words: why no Short can be promoted right now."""
    now = now or now_utc(); rs = rows() if rs is None else rs
    shorts = [r for r in rs if r.get("state") in ("MADE",) + CANDIDATE + TAKEN + ("PASSED", "SKIPPED")]
    if not shorts: return "no Short has been made yet: every topic starts as a Short"
    fresh = [r for r in rs if r.get("state") in ("MADE", "POSTED")]
    if fresh:
        t = min((parse_iso(r.get("posted")) for r in fresh if parse_iso(r.get("posted"))), default=None)
        when = f"; the oldest went public {t:%d %b}" if t else "; none is public yet (waiting for your Approve)"
        return f"{len(fresh)} Short(s) have no numbers yet (public views come after 48 hours, the true numbers about 5 days after a Short goes public){when}"
    return "every Short with numbers already has its long video, or its topic was passed over"

# ------------------------------------------------------------------ the gate, the override, the room's pitch
def override(by, note, now=None):
    """Record an override: the next long video may be made about a topic that never started as a Short. One open override at a time."""
    now = now or now_utc(); have = waiting_override()
    if have: return have
    oid = f"OVR{now:%Y%m%d%H%M%S}"
    store().append(TAB, [{"id": oid, "topic": oid, "state": "OVERRIDE", "by": str(by)[:40], "promoted_at": iso(now), "note": str(note)[:300]}])
    log(f"ladder: override recorded by {by} ({str(note)[:120]}): the next long video does not need a promoted Short", "WARN")
    return row(oid)

def gate(now=None):
    """(ok, why, row): may a long video start? Yes when the ladder is off; when the owner locked his own topic (recorded as an override); when a
    promoted Short waits (one is promoted on the spot when a candidate exists); or when his override is on record. An override is used only when
    no Short can be promoted. Costs nothing; spends nothing."""
    now = now or now_utc()
    if not on(): return True, "the ladder is switched off (LADDER_ON / SHORTS_TRACK_ON)", None
    if str(S("OWNER_NEXT_PREMISE") or "").strip():
        o = override("owner_brief", "the owner locked his own topic for the next long video (Owner Brief)", now)
        return True, "the owner's own locked topic", o
    try: r = waiting() or promote(now)
    except Exception as e:
        log(f"ladder: the promote run failed ({scrub(e)[:160]})", "ERROR"); r = None
    if r: return True, f"the topic of Short {r['id']} ({str(r.get('score'))[:80]})", r
    o = waiting_override()
    if o: return True, f"override recorded by {o.get('by')} on {str(o.get('promoted_at'))[:10]}", o
    return False, why_not(now), None

def refuse(slot, why):
    """Tell the owner ONCE per slot that its long video waits for the ladder, with the one button that overrides."""
    from whatifs import notify as NT
    return NT.send("ladder", f"The long video for {str(slot)[:10]} is waiting: {why}. A long video is made only about a topic whose Short real viewers stayed for. "
                   "Tap 'Make it anyway' to make this one from the premise bench instead (recorded as your override).", [("Make it anyway", f"LADDER OVERRIDE {slot}")],
                   tier="now", default="the long video waits for a Short", expires_h=96, dedupe_key=f"ladder|{slot}")

def pitch():
    """The promoted Short's topic as the room's forced first pitch, or None. Nothing is marked here: the topic is used up by `use`, once the plan is saved."""
    r = waiting() if on() else None
    if not r: return None
    return {"premise": str(r.get("premise") or ""), "headline": str(r.get("title") or r.get("premise") or ""), "family": "", "ptype": "", "teased": True, "ladder": r["id"],
            "scores": {"grasp": 9, "pull": 9}, "total": 999}

def claim():
    """What a long video that is NOT about a promoted Short may name as its ground: the open override's id ('' when there is none)."""
    o = waiting_override() if on() else None
    return o["id"] if o else ""

def use(ref, episode, now=None):
    """The long video `episode` has a saved plan: its ladder row (a promoted Short or an override) is used up. Idempotent."""
    r = row(str(ref or "")); now = now or now_utc()
    if not r or not episode: return False
    if r.get("state") == "PROMOTED": _set(r["id"], state="USED", episode_id=episode, note=_note(r, f"long video {episode}")); return True
    if r.get("state") == "OVERRIDE": _set(r["id"], state="OVERRIDE_USED", episode_id=episode); return True
    return r.get("episode_id") == episode

def used_by(episode):
    """Has this long video already taken its ladder row (a retry keeps the topic its first attempt took)?"""
    return bool(episode) and any(r.get("episode_id") == episode for r in rows())

def runner_ups(n=3):
    """The other Shorts that could be promoted next, best first, as pitches: what a long video can truthfully tease as 'next'."""
    rs = rows(); w = waiting(rs); _k, order = rank(candidates(rs))
    return [{"premise": str(r.get("premise") or ""), "headline": str(r.get("title") or r.get("premise") or ""), "family": "", "ptype": "", "ladder": r["id"]}
            for r, _why in order if not w or r.get("topic") != w.get("topic")][:n]

def topic_report(d, premise, episode):
    """(ok, why) for check `topic_ladder`: is this long video about a topic that climbed the ladder - or made under a recorded override?"""
    ref = str((d or {}).get("ladder") or "")
    if not ref: return False, "this long video's topic never started as a Short and no override is recorded (the draw names no ladder row)"
    r = row(ref)
    if not r: return False, f"the draw names ladder row {ref}, which does not exist"
    if r.get("state") in ("OVERRIDE", "OVERRIDE_USED"):
        if r.get("episode_id") not in (None, "", episode): return False, f"override {ref} was already used by {r.get('episode_id')}"
        return True, f"override by {r.get('by')} on {str(r.get('promoted_at'))[:10]}: {str(r.get('note'))[:160]}"
    if r.get("state") not in TAKEN: return False, f"Short {ref} was never promoted (it is {r.get('state')})"
    if r.get("episode_id") not in (None, "", episode): return False, f"Short {ref} was promoted for {r.get('episode_id')}, not for this video"
    if " ".join(str(r.get("premise") or "").lower().split()) != " ".join(str(premise or "").lower().split()):
        return False, f"the video's premise is not the premise of its promoted Short {ref}"
    return True, f"the topic of Short {ref}, promoted on {str(r.get('promoted_at'))[:10]} ({str(r.get('score'))[:200]})"

def skip(sid, by="owner"):
    """The owner does not want this promoted topic: it is set aside and the rule promotes the next best when a long video is about to start."""
    r = row(sid)
    if not r or r.get("state") != "PROMOTED": return False
    _set(sid, state="SKIPPED", by=by, note=_note(r, f"set aside by {by}")); return True

def _answer(arow, choice):
    p = str(choice).split()
    if len(p) >= 2 and p[0].upper() == "LADDER" and p[1].upper() == "OVERRIDE":
        o = override("owner", f"his tap on the message for slot {p[2] if len(p) > 2 else '?'}")
        return f"recorded ({o['id']}): the next long video is made from the premise bench"
    if len(p) >= 3 and p[0].upper() == "LADDER" and p[1].upper() == "SKIP":
        return "set aside: the next best Short is promoted when the long video starts" if skip(p[2]) else f"{p[2]} is no longer waiting"
    return "recorded"

def register():
    from whatifs import notify as NT
    NT.register("ladder", on_answer=_answer)

# ------------------------------------------------------------------ the winner: one follow-up, ordered with a clock
def order_followup(key, yt_id, views, base, mark, now=None):
    """The fast clock found a WINNER (`breakout.monitor`): its ladder row says so, ONE follow-up Short is ordered with a clock, the departments get a
    performance memo and the owner one line he can stop with a tap. Nothing waits for his approval. Returns the order row, or None when this
    winner already has one."""
    now = now or now_utc(); st = store()
    line = S("SHORTS_WINNER_MIN_VIEWS", float) or 1.0
    mult = round(views / base, 2) if base else round(views / line, 2)
    r = row(key)
    if r and _n(r.get("multiple")) < mult:
        _set(key, multiple=mult, note=_note(r, f"winner at the {mark}-hour mark: {int(views)} views against " + (f"the usual {int(base)}" if base else f"the line of {int(line)} (no history yet)")))
    if any(q.get("video_key") == key for q in st.rows(QUEUE)): return None
    hours = max(1.0, S("FOLLOWUP_WITHIN_H", float)); due = now + dt.timedelta(hours=hours)
    st.append(QUEUE, [{"ts": iso(now), "video_key": key, "status": "ORDERED", "plan": "1 follow-up Short", "left": 1, "due": iso(due), "done": ""}])
    rel = f"{views / base:.1f} times the usual {int(base)}" if base else f"{int(views)} views (no history yet; the line is {int(line)})"
    try:
        from whatifs.org import runner as ORG, memos as MEM
        if ORG.on():
            MEM.write({"type": "performance_memo", "from_dept": "D10", "to_depts": ["D14", "D4", "D9"], "subject": f"Short {key} is a winner: a follow-up is ordered"[:140],
                       "body": {"window": "breakout", "video": str(key)[:60], "metrics": {"views": int(views), "usual": int(base or 0), "multiple": mult, "mark_h": int(mark)},
                                "changes": [f"one follow-up Short is due by {iso(due)}"]},
                       "dedupe_key": f"ladder|winner|{key}",
                       "evidence": [{"source": f"Monitor48:{yt_id}:v{int(mark)}", "date": iso(now)[:10], "type": "own data", "finding": f"{int(views)} public views at the {int(mark)}-hour mark: {rel}"}]}, now=now)
    except Exception as e: log(f"winner memo not written: {scrub(e)[:120]}", "WARN")
    try:
        from whatifs import notify as NT
        NT.send("breakout", f"A Short is taking off: {key} is at {rel} after {int(mark)} hours. ONE follow-up Short on its topic is being made within {int(hours)} hours "
                f"(paid from the breakout fund or the reserve). Nothing to do. https://youtu.be/{yt_id}", [("Stop it", f"BREAKOUT NO {key}")],
                tier="now", urgent=True, default="the follow-up is made", expires_h=hours, dedupe_key=f"breakout|{yt_id}")
    except Exception as e: log(f"winner not announced: {scrub(e)[:100]}", "WARN")
    log(f"ladder: Short {key} is a winner ({rel}); one follow-up ordered, due {iso(due)}")
    return next((q for q in st.rows(QUEUE) if q.get("video_key") == key), None)

def open_orders(rs=None):
    """Follow-up orders that are still to be made (ordered by code, or approved by the owner for a long video's breakout)."""
    rs = store().rows(QUEUE) if rs is None else rs
    closed = {q.get("video_key") for q in rs if q.get("status") in ("DONE", "DECLINED", "LAPSED")}
    return [q for q in rs if q.get("status") in ("ORDERED", "OVERDUE", "APPROVED", "FOLLOWUP 1") and q.get("video_key") not in closed]

def order_tried(key, why, now=None):
    """A try to make the follow-up did not end in a Short: the order keeps when and why (the next try waits, the overdue memo names the reason)."""
    try: store().update(QUEUE, "video_key", key, {"plan": f"1 follow-up Short; last try {iso(now or now_utc())}: {str(why)[:160]}"})
    except Exception as e: log(f"order note not written: {scrub(e)[:80]}", "WARN")

def order_done(key, short_id, now=None):
    """The follow-up Short was made: the order is closed with the Short that paid it, and its overdue memo (if one was written) with that proof."""
    st = store(); q = next((x for x in st.rows(QUEUE) if x.get("video_key") == key and x.get("status") in ("ORDERED", "OVERDUE", "APPROVED", "FOLLOWUP 1")), None)
    if not q: return False
    left = max(0, int(_n(q.get("left"), 1)) - 1)
    st.update(QUEUE, "video_key", key, {"left": left, "status": q["status"] if left > 0 else "DONE", "done": short_id})
    try:
        from whatifs.org import runner as ORG, memos as MEM
        if ORG.on():
            for m in MEM.find(type="problem_memo", from_dept="D10", error_class="followup_overdue"):
                if m["body"].get("where") == f"{QUEUE}:{key}": MEM.resolve(m["id"], "D10", "repair_verified", f"Specials:{short_id}", "the follow-up Short was made", now=now)
    except Exception as e: log(f"overdue memo not closed: {scrub(e)[:120]}", "WARN")
    return True

def watch(now=None):
    """Every tick: a follow-up order past its clock becomes a problem memo from Growth and Learning to the Shorts Studio (it climbs to the Council
    and the owner by the memo clocks and is closed by the follow-up being made); an order LAPSE_X times its clock old is given up - the memo stays
    open, so the owner hears that a winner got no follow-up. Returns the keys that went overdue or lapsed in this pass."""
    now = now or now_utc(); st = store(); out = []
    for q in st.rows(QUEUE):
        if q.get("status") not in ("ORDERED", "OVERDUE"): continue
        t0, due = parse_iso(q.get("ts")), parse_iso(q.get("due"))
        if not t0 or not due or now <= due: continue
        key = q["video_key"]; hours = (due - t0).total_seconds() / 3600
        if q["status"] == "ORDERED":
            plan = str(q.get("plan") or "")
            reason = plan.split("last try ", 1)[1][22:] if "last try " in plan else "no try was recorded (the Shorts job did not run)"
            try:
                from whatifs.org import runner as ORG, memos as MEM
                if ORG.on():
                    MEM.write({"type": "problem_memo", "from_dept": "D10", "to_depts": ["D14"], "subject": f"the follow-up of winner {key} is overdue"[:140],
                               "body": {"what_failed": f"the follow-up Short of winner {key} was not made within {hours:.0f} hours of the order: {reason}"[:400],
                                        "where": f"{QUEUE}:{key}", "attempt": 1, "error_class": "followup_overdue"},
                               "done_when": f"the follow-up Short of {key} is made, or the owner waives it", "episode_id": "", "dedupe_key": f"followup|{key}",
                               "evidence": [{"source": f"{QUEUE}:{key}", "date": iso(now)[:10], "type": "own data", "finding": f"ordered {q.get('ts')}, due {q.get('due')}, not made by {iso(now)}"}]}, now=now)
            except Exception as e: log(f"overdue memo not written: {scrub(e)[:120]}", "WARN")
            st.update(QUEUE, "video_key", key, {"status": "OVERDUE"}); out.append(key)
            log(f"ladder: the follow-up of winner {key} is overdue ({reason})", "WARN")
        elif now > t0 + LAPSE_X * (due - t0):
            st.update(QUEUE, "video_key", key, {"status": "LAPSED"}); out.append(key)
            log(f"ladder: the follow-up of winner {key} lapsed ({LAPSE_X} times its clock): it is no longer made", "WARN")
    return out
