"""His verdict (D13): one row and one tap a release on tab Owner_Verdicts - his tap is the strongest label, the judged floor is scored against it and the videos he approved are its references. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, json, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub, set_setting

TAB = "Owner_Verdicts"
UP = ("up", "good", "yes", "y", "+")
DOWN = ("down", "bad", "no", "n", "-", "not good")
DEFERRED = "read by Audience: the verdict run scores the floor against the owner's verdict only; anything else is for its addressed departments"
EMPTY = {"asked": "", "verdict": "", "text": "", "maker_line": "", "seen": "", "via": "", "agree": "", "action_id": "", "line_seen": "", "line_used": "", "told": "[]"}

def on():
    """Is his verdict asked and kept? (FALSE = exactly as before: nothing is asked, kept or used - DESIGN QUESTION 9.)"""
    return S("OWNER_VERDICT_ON", bool)

def read(cell):
    """His verdict cell read as 'up', 'down' or '' - lower-cased and stripped it must EQUAL one of UP or DOWN (never a guess)."""
    v = str(cell or "").strip().lower()
    return "up" if v in UP else "down" if v in DOWN else ""

def made_at(episode_id):
    """When a long video was MADE: the UTC minute in the id's first twelve digits ('EP' + %Y%m%d%H%M) - never `slot_et`, which moves; an id without
    twelve digits counts as made now."""
    m = re.search(r"\d{12}", str(episode_id or ""))
    if m:
        try: return dt.datetime.strptime(m.group(0), "%Y%m%d%H%M").replace(tzinfo=dt.timezone.utc)
        except ValueError: pass
    return now_utc()

def since():
    """The day this batch reached the Sheet (OWNER_VERDICT_SINCE): nothing older is ever asked about, and the creative review counts from it."""
    return parse_iso(str(S("OWNER_VERDICT_SINCE") or "").strip())

def _js_list(v):
    try:
        x = json.loads(v) if str(v or "").strip() else []
        return x if isinstance(x, list) else []
    except Exception: return []

def _row(ref, rows=None):
    return next((r for r in (store().rows(TAB) if rows is None else rows) if str(r.get("ref")) == str(ref)), None)

# ------------------------------------------------------------------ what the floor said of a long video (computed again, through floor.again alone)
def _sessions(ep):
    """The floor sessions of one episode on tab Floor_Log, oldest first: [(session_id, rows)]."""
    from whatifs.org import floor as FL
    by, seq = {}, []
    for r in store().rows(FL.LOG):
        if str(r.get("episode_id") or "") != str(ep): continue
        s_ = str(r.get("session_id") or "")
        if s_ not in by: by[s_] = []; seq.append(s_)
        by[s_].append(r)
    return [(s_, by[s_]) for s_ in seq]

def _predict(ep):
    """The floor's prediction for a long video: the `predict` of its NEWEST session ('' for none, or a void one)."""
    from whatifs.org import floor as FL
    ss = _sessions(ep)
    return str(FL.again(ss[-1][1]).get("predict") or "") if ss else ""

def _judged(ep):
    """(status, view) of the newest session of an episode that is not void; ("", "") when none."""
    from whatifs.org import floor as FL
    for _s, rows in reversed(_sessions(ep)):
        st_ = FL.again(rows)["status"]
        if st_ != "void": return st_, str(rows[0].get("view") or "")
    return "", ""

def _pool(verdict, exclude, n):
    """His long videos with this verdict whose newest valid floor session PASSED and kept its viewing, newest verdict first: [(episode, view, title)]."""
    if not on() or n <= 0: return []
    out = []
    mine = [x for x in store().rows(TAB) if x.get("kind") == "long" and x.get("seen") and read(x.get("verdict")) == verdict and str(x.get("ref")) != str(exclude)]
    for r in sorted(mine, key=lambda x: str(x.get("seen") or ""), reverse=True):
        st_, vid = _judged(r["ref"])
        if st_ == "pass" and vid: out.append((str(r["ref"]), vid, " ".join(str(r.get("title") or "").split())[:80]))
        if len(out) >= n: break
    return out

def references(exclude):
    """HIS THUMBS-UP IS THE REFERENCE SET: [(episode, view id)] - never a film the floor refused, never the episode being judged."""
    return [(e, v) for e, v, _t in _pool("up", exclude, S("VIEW_FLOOR_REFS_MAX", int))]

def downs(exclude):
    """His thumbs-down on a film the floor PASSED (the floor's own misses) as down-canaries: [(episode, view id, title)] - behind VIEW_FLOOR_DOWNS_MAX (0)."""
    return _pool("down", exclude, S("VIEW_FLOOR_DOWNS_MAX", int))

# ------------------------------------------------------------------ the rows, the asks, the notices
def _long_row(e):
    ep = str(e.get("episode_id") or "")
    try: lad = str((json.loads(e.get("draw_json") or "{}") or {}).get("ladder") or "")
    except Exception: lad = ""
    lr = next((r for r in store().rows("Ladder") if str(r.get("id")) == lad), None) if lad else None
    topic = "" if not lr or str(lr.get("state") or "").startswith("OVERRIDE") else str(lr.get("topic") or "")      # "" under an override
    yt = str(e.get("yt_id") or "")
    return {"ref": ep, "kind": "long", "title": str(e.get("title") or ""), "url": ("https://youtu.be/" + yt) if yt else "", "topic": topic, "floor": _predict(ep)}

def _short_row(r):
    return {"ref": str(r.get("id")), "kind": "short", "title": str(r.get("title") or ""), "url": "https://youtu.be/" + str(r.get("yt_id") or ""), "topic": str(r.get("topic") or ""), "floor": ""}

def _ask(ref, kind, title, url, key=None):
    from whatifs import notify as NT
    text = (f"Your verdict on the new {'Short' if kind == 'short' else 'video'} '{title}': {url} - one tap. If you want to say why: tab Owner_Verdicts, row {ref}, "
            f"column text - your Sheet is private; the mail link's title is a public page, never type the why there.")
    return NT.send("owner_verdict", text, [("Good", f"VERDICT {ref} UP"), ("Not good", f"VERDICT {ref} DOWN")], episode=ref, tier="now",
                   expires_h=S("OWNER_VERDICT_EXPIRES_H", float), dedupe_key=key or f"verdict|{ref}")

def told(ref, key):
    """Was he told this already? Kept on the row (column `told`, written by code only): True when the key is there; else it is added and False."""
    r = _row(ref)
    if r is None: return True                                       # no row to keep it on: nothing is sent
    have = _js_list(r.get("told"))
    if key in have: return True
    store().update(TAB, "ref", ref, {"told": json.dumps(have + [key], ensure_ascii=False)})
    return False

def note(ref, key, kind, text):
    """A notice he is told ONCE: the digest (tier week), nothing to tap, it leaves the list by itself after 72 hours (DESIGN QUESTION 10)."""
    from whatifs import notify as NT
    if told(ref, key): return None
    return NT.send(kind, text, [], episode=ref, tier="week", expires_h=72, dedupe_key=f"told|{ref}|{key}")

def sync(now=None):
    """The tick's step (level-triggered; while PAUSED the tick returns before it). (1) An empty OWNER_VERDICT_SINCE is set to now and nothing else
    happens; (2) every public Short and every LIVE long video made since that day without a row gets one and ONE ask - oldest first, at most
    OWNER_VERDICT_ASK_MAX_PER_DAY a UTC day and only while two 'act now' places are left today; (3) a verdict cell he typed is read (up or down) and kept,
    anything else he is told once. Returns how many he was asked about."""
    if not on(): return 0
    from whatifs import notify as NT
    now = now or now_utc(); st = store(); t0 = since()
    if t0 is None:
        set_setting("OWNER_VERDICT_SINCE", iso(now)); log("owner verdicts: counted from today - no release older than today is ever asked about"); return 0
    rows = st.rows(TAB); have = {str(r.get("ref")) for r in rows}
    cands = []
    for r in st.rows("Ladder"):
        t = parse_iso(r.get("posted"))
        if r.get("yt_id") and t and t >= t0 and r.get("state") != "MADE" and str(r.get("id")) not in have: cands.append((t, "short", r))
    for e in st.rows("Episodes"):
        if e.get("status") == "LIVE" and e.get("yt_id") and made_at(e.get("episode_id")) >= t0 and str(e.get("episode_id")) not in have: cands.append((made_at(e.get("episode_id")), "long", e))
    day = now.strftime("%Y-%m-%d"); asked = sum(1 for r in rows if str(r.get("asked") or "")[:10] == day); n = 0
    for _t, kind, src in sorted(cands, key=lambda x: x[0]):
        if asked >= S("OWNER_VERDICT_ASK_MAX_PER_DAY", int) or NT.now_room() < 2: break
        row = dict(EMPTY, **(_short_row(src) if kind == "short" else _long_row(src)), asked=iso(now))
        st.append(TAB, [row])
        st.update(TAB, "ref", row["ref"], {"action_id": _ask(row["ref"], kind, row["title"], row["url"])})
        asked += 1; n += 1; log(f"owner verdicts: asked about the {kind} '{row['title'][:60]}' ({row['ref']})")
    for r in st.rows(TAB):                                          # (3) a verdict he typed in the Sheet
        if r.get("seen") or not str(r.get("verdict") or "").strip(): continue
        v = read(r["verdict"])
        if v:
            record(r["ref"], v, "", "sheet")
            if r.get("action_id"):
                try: NT.answer(r["action_id"], f"VERDICT {r['ref']} {v.upper()}", who="sheet")      # his Sheet answer closes the open message
                except Exception as e: log(f"owner verdicts: the message of {r['ref']} was not closed: {scrub(e)[:120]}", "WARN")
        else:
            cell = " ".join(str(r["verdict"]).split())
            note(r["ref"], f"unread|{cell}", "owner_verdict", f"I could not read your verdict '{cell}' on '{r.get('title') or r['ref']}': type up or down")
    return n

# ------------------------------------------------------------------ his verdict, kept; D13's run scores the floor against it
def score():
    """(agreed, scored) over the last VIEW_FLOOR_SCORE_N long videos whose verdict scored the floor (a non-empty `agree`)."""
    rows_ = sorted((r for r in store().rows(TAB) if r.get("kind") == "long" and str(r.get("agree") or "") in ("TRUE", "FALSE")), key=lambda r: str(r.get("seen") or ""))
    n = S("VIEW_FLOOR_SCORE_N", int); last = rows_[-n:] if n > 0 else []
    return sum(1 for r in last if r["agree"] == "TRUE"), len(last)

def m_run(res):
    res = res if isinstance(res, dict) else {}
    a, n = (list(res.get("score") or [0, 0]) + [0, 0])[:2]
    return {"agree": int(res.get("agree") == "TRUE"), "miss": int(res.get("agree") == "FALSE"), "scored": int(n or 0), "agreed": int(a or 0)}

def _memo(sub, what, done, ref, key, now):
    return {"type": "problem_memo", "from_dept": "D13", "to_depts": ["D13"], "subject": sub, "body": {"what_failed": what[:400], "where": "the judged floor", "attempt": 1},
            "done_when": done, "evidence": [{"source": f"Owner_Verdicts:{ref}", "date": iso(now)[:10], "type": "own data", "finding": what[:300]}], "dedupe_key": key}

def _run(brief, ref):
    """D13's `verdict` run (the shape of floor.run): `agree` = the floor's prediction against his verdict; a miss writes D13's `floor|miss` memo (closed by
    the next agreement), VIEW_FLOOR_MISS_MAX misses among the last VIEW_FLOOR_SCORE_N write `floor|score` (closed when its done_when holds - DESIGN
    QUESTION 12)."""
    from whatifs.org.runner import Out
    from whatifs.org import memos as MEM
    now = now_utc(); st = store(); r = _row(ref) or {}
    acts = {m["id"]: ("deferred", DEFERRED) for m in getattr(brief, "memos", None) or []}
    fl, v = str(r.get("floor") or ""), read(r.get("verdict"))
    agree = "" if not fl else ("TRUE" if fl == v else "FALSE")
    st.update(TAB, "ref", ref, {"agree": agree})
    memos = []
    def close(prefix, why):
        for m in MEM.find(st, type="problem_memo", from_dept="D13"):          # also one the watchdog already escalated (it has left D13's inbox by then)
            if not str(m.get("dedupe_key") or "").startswith(prefix): continue
            if m["id"] in acts: acts[m["id"]] = ("resolved", "repair_verified", ref)
            else: MEM.resolve(m["id"], "D13", "repair_verified", ref, why, st, now)
    try:
        if agree == "FALSE":
            what = f"the floor predicted {fl} for {ref}; the owner said {v}: \"{str(r.get('text') or '')[:200]}\""
            memos.append(_memo("The judged floor's prediction missed the owner's verdict", what, "the floor's next scored prediction agrees with the owner", ref, "floor|miss", now))
        elif agree == "TRUE": close("floor|miss", "the floor's next scored prediction agreed with the owner")
        a, n = score(); miss, N, M_ = n - a, S("VIEW_FLOOR_SCORE_N", int), S("VIEW_FLOOR_MISS_MAX", int)
        if agree and miss >= M_:
            what = f"the floor disagreed with the owner on {miss} of the last {n} videos"
            memos.append(_memo("The judged floor disagrees with the owner too often: " + what, what, f"the floor agrees with the owner on at least {N - M_ + 1} of his last {N} scored videos", ref, "floor|score", now))
        elif agree: close("floor|score", f"the floor agrees with the owner on {a} of his last {n} scored videos")
    except Exception as e: log(f"owner verdicts: the floor's score memos were not written: {scrub(e)[:120]}", "WARN", ref); a, n = score()
    res = {"ref": ref, "verdict": v, "floor": fl, "agree": agree, "score": [a, n]}
    return Out(output=res, memos=memos, memo_actions=acts, measures=m_run(res))

def record(ref, verdict, text="", via=""):
    """Keep his verdict on a release (a tap, the Sheet, his Hold, his drop): the row is made when none exists (a long video; nothing is asked); a row that
    has `seen` is never written again; `text` only when its cell is empty (what he typed is never overwritten). Then D13's run `verdict`. Returns what he
    reads back, or None when nothing was kept."""
    if not on(): return None
    verdict = read(verdict)
    if not verdict: return None
    st = store(); r = _row(ref)
    if r is None:
        e = next((x for x in st.rows("Episodes") if str(x.get("episode_id")) == str(ref)), None) or {"episode_id": ref}
        r = dict(EMPTY, **_long_row(e)); st.append(TAB, [r])
    if r.get("seen"): return None
    ch = {"seen": iso(), "via": str(via)[:20]}
    if read(r.get("verdict")) != verdict: ch["verdict"] = verdict              # his own word stays when it already says it (DESIGN QUESTION 11)
    if str(text or "").strip() and not str(r.get("text") or "").strip(): ch["text"] = str(text)[:1000]
    st.update(TAB, "ref", ref, ch)
    from whatifs.org import runner as ORG, floor as FL
    res = FL.plain(ORG.work("D13", "verdict", str(ref), lambda b: _run(b, str(ref)), measure=m_run))
    res = res if isinstance(res, dict) else {}
    r = _row(ref) or r; out = f"Kept: {verdict} on '{r.get('title') or ref}'."
    if str(r.get("text") or "").strip(): out += f" Your line: \"{str(r['text']).strip()[:200]}\"."
    if res.get("floor"): out += f" The floor had said {res['floor']}: " + ("it agrees." if res.get("agree") == "TRUE" else "it was wrong - noted.")
    a, n = score()
    return out + f" Floor so far: {a} of {n}."

def _answer(row, choice):
    """His tap on the verdict ask: VERDICT <ref> UP|DOWN. Words after UP or DOWN are NOT stored (the mail route's title is a public page). Anything else has
    spent the message: the same ask is sent ONCE more, then he is pointed to the tab."""
    ref = str(row.get("episode_id") or ""); p = str(choice).split(None, 3)
    if len(p) >= 3 and p[0].upper() == "VERDICT" and p[1] == ref and p[2].upper() in ("UP", "DOWN"):
        out = record(ref, p[2].lower(), "", "tap") or f"{ref}: your verdict is already kept"
        if len(p) > 3: out += f" Your words after {p[2].upper()} were not stored: the mail link's title is a public page - type the why in tab Owner_Verdicts, row {ref}, column text."
        return out
    if not told(ref, "ask2"):
        r = _row(ref) or {}
        store().update(TAB, "ref", ref, {"action_id": _ask(ref, r.get("kind") or "long", r.get("title") or ref, r.get("url") or "", key=f"verdict|{ref}|2")})
        return "I could not read that: tap Good or Not good on the new message"
    return f"type up or down in tab Owner_Verdicts, row {ref}"

def register():
    from whatifs import notify as NT
    NT.register("owner_verdict", on_answer=_answer)
