"""The HD gate (Publishing, D9): an upload that would go public at once goes up private, and code makes it public when YouTube shows it processed and in HD, or at its cap - never past a policy read that failed; a long video's public time is moved in steps while YouTube does not show it in HD, and his window is one card on its day. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, math, re, time
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, scrub

TAB = "HD_Wait"
WAITING, PUBLIC, CAP, BLOCKED, LOCKED = "WAITING", "PUBLIC", "CAP", "BLOCKED", "LOCKED"
UNREAD_MAX = 3          # R22 (4): an unread Short is blocked on its THIRD empty read in a row (and PRIVATE_ALERT_HOURS past its cap), never on one

def ready(got):
    """YouTube's own answer says the video is processed AND in HD (`publish.yt_read`: `processed`, `hd`) - the one judgment on those two fields."""
    return bool(got) and bool(got.get("processed")) and bool(got.get("hd"))

def row(vid):
    """The video's row on tab HD_Wait, or None. A video is GATED when it has one (R18 (4 a)) - never by what the switch says at a later pass."""
    if not vid: return None
    try: return next((r for r in store().rows(TAB) if r.get("vid") == vid), None)
    except Exception: return None

def enter(vid, kind, now=None, ai=True):
    """The upload went up private through the gate: its row (once a video). kind = "short" or "video"; cap_min = HD_SHORT_CAP_MIN for both (R18 (7 b));
    ai = what the upload asked for the AI label (R17 ADDS (E))."""
    if not vid or row(vid): return
    store().append(TAB, [{"vid": vid, "kind": kind, "uploaded": iso(now or now_utc()), "cap_min": S("HD_SHORT_CAP_MIN", int), "ai": "TRUE" if ai else "FALSE",
                          "state": WAITING, "public_at": "", "hd": "", "minutes": "", "note": ""}])

def _set(vid, **kw): store().update(TAB, "vid", vid, kw)

def _mins(since, now): return max(0, int((now - since).total_seconds() // 60)) if since else 0

def short_step(uploaded, got, now, cap=None):
    """Pure: ("public", m) when YouTube shows it ready; ("cap", m) when m minutes since the upload reach the cap (HD_SHORT_CAP_MIN); else ("wait", m)."""
    m = _mins(uploaded, now)
    if ready(got): return "public", m
    if m >= (S("HD_SHORT_CAP_MIN", float) if cap is None else float(cap)): return "cap", m
    return "wait", m

def _unread(vid, now):
    """R22 (4): one more empty read in a row, counted on the row's note ("unread 2"); returns the count."""
    r = row(vid)
    if not r or r.get("state") != WAITING: return 0                                # a row that no longer waits keeps its own words
    m = re.match(r"unread (\d+)$", str(r.get("note") or "")); n = (int(m.group(1)) if m else 0) + 1
    _set(vid, note=f"unread {n}"); return n

def _read_ok(vid):
    """A read that answers clears the count of empty reads."""
    r = row(vid)
    if r and str(r.get("note") or "").startswith("unread "): _set(vid, note="")

def block(vid, why, got=None, now=None):
    """A failed check still holds: state BLOCKED, never public, and HE IS TOLD once a video (R18 (5)): kind `hd_blocked`, no button (`send` gives it Done)."""
    from whatifs import notify as NT
    r = row(vid)
    if r and r.get("state") == BLOCKED: return why
    if r: _set(vid, state=BLOCKED, note=str(why)[:300])
    title = str((got or {}).get("title") or vid)
    try:
        NT.send("hd_blocked", f"{title} stays private: {why}. Nothing was deleted. Put it right in YouTube Studio and make it public there: "
                              f"https://studio.youtube.com/video/{vid}/edit", tier="now", dedupe_key=f"hdblock|{vid}")
    except Exception as e: log(f"the HD gate could not tell the owner that {vid} is blocked: {scrub(e)[:120]}", "WARN")
    log(f"HD gate: {vid} stays private - {why}", "WARN"); return why

def go_public(vid, now=None, why="public"):
    """THE ONE DOOR by which code makes a video public: YouTube's own read judged first (made for kids -> blocked with its alarm; an AI label that is
    False on a row that asked for it -> set once and read again, still False -> blocked), then the privacy set, read back and written on the video's
    HD_Wait row with the minutes and the HD state; a read-back that is not public is the lock (`launch.lock_detected`). An empty read changes nothing.
    Returns (ok, note) - (False, "blocked: <why>") when it refuses, (False, "not read") when YouTube could not be read."""
    from whatifs import publish as PUB, launch as LA, notify as NT
    now = now or now_utc(); r = row(vid)
    if r and r.get("state") in (BLOCKED, LOCKED): return False, "blocked: " + str(r.get("note") or r.get("state"))      # a failed check still holds - at THE door, whoever calls it
    got = PUB.yt_read(vid)
    if not got:                                                                     # R18 (5): a read that failed is not a pass
        _unread(vid, now); return False, "not read"
    _read_ok(vid)
    if got.get("kids") is True:                                                     # R17 (1 b): the policy reads at EVERY door
        try: NT.send("kids_flag", f"YouTube marked video {vid} as made for kids: it stays private and is not published. Check the audience setting in Studio; appeal if wrong.",
                     tier="now", urgent=True, dedupe_key=f"kids|{vid}")
        except Exception as e: log(f"the made-for-kids alarm of {vid} was not sent: {scrub(e)[:120]}", "WARN")
        return False, "blocked: " + block(vid, "YouTube marked it made for kids", got, now)
    asked = (str(r.get("ai") or "").upper() == "TRUE") if r else S("AI_LABEL_DEFAULT", bool)
    if asked and got.get("ai") is False:                                            # None = YouTube left the field out: no failure (as verify_upload reads it)
        PUB.yt_set_label(vid, True); again = PUB.yt_read(vid)
        if not again: _unread(vid, now); return False, "not read"
        if again.get("ai") is False: return False, "blocked: " + block(vid, "the AI label did not hold", got, now)
    PUB.yt_set_privacy(vid, "public"); back = PUB.yt_read(vid)
    if not back: _unread(vid, now); return False, "not read"
    up = parse_iso((r or {}).get("uploaded")); m = _mins(up, now) if up else 0; hd = bool(back.get("hd"))
    if (back.get("privacy") or "") != "public":                                     # asked public, it still reads otherwise: the lock (the detector moved here from release.py)
        note = f"made public, but YouTube still shows it {back.get('privacy') or 'unread'}: the lock"
        if r: _set(vid, state=LOCKED, minutes=m, hd="yes" if hd else "no", note=note)
        LA.lock_detected(vid, [f"a video the HD gate made public came back {back.get('privacy') or 'unread'}"])
        return False, note
    state = CAP if why == "cap" else PUBLIC
    note = f"public after {m} min; HD yes" if state == PUBLIC else f"public after {m} min; HD NO (the cap)"
    if r: _set(vid, state=state, public_at=iso(now), minutes=m, hd="yes" if hd else "no", note=note)
    if state == CAP and not hd: log(f"HD gate: {vid} went public at its cap after {m} min without HD (a miss)", "WARN")
    return True, note

def finish(vid, wait_s=0, now=None):
    """(state, minutes, note) of a gated video: a row that no longer waits is answered as it stands; else YouTube is read every `release.POLL_S` seconds
    until `short_step` says public or cap (then `go_public`) or `wait_s` is used up. An unread Short is BLOCKED, "YouTube could not be read", only
    PRIVATE_ALERT_HOURS past its cap AND on its third empty read in a row (R22 (4)). ("", 0, "") for a video the gate never took."""
    from whatifs import publish as PUB, release as REL
    now = now or now_utc(); r = row(vid)
    if not r: return "", 0, ""
    if r.get("state") != WAITING: return r.get("state"), int(float(r.get("minutes") or 0)), str(r.get("note") or "")
    up = parse_iso(r.get("uploaded")) or now; cap = float(r.get("cap_min") or S("HD_SHORT_CAP_MIN", float))
    left = 0 if FAKE else max(0.0, float(wait_s or 0)); t = now; n = None
    while True:
        got = PUB.yt_read(vid)
        if not got:
            if n is None: n = _unread(vid, t)                                       # R22 (4): ONE empty read a pass, however often the job polls
            if _mins(up, t) >= cap + S("PRIVATE_ALERT_HOURS", float) * 60 and n >= UNREAD_MAX: block(vid, "YouTube could not be read", None, t); break
        else:
            n = None; _read_ok(vid); act, _m = short_step(up, got, t, cap)
            if act in ("public", "cap"): go_public(vid, t, act); break
        if left <= 0: break
        time.sleep(REL.POLL_S); left -= REL.POLL_S; t = t + dt.timedelta(seconds=REL.POLL_S)
    r = row(vid) or {}
    if r.get("state") == WAITING: return WAITING, _mins(up, t), str(r.get("note") or "")
    return r.get("state"), int(float(r.get("minutes") or 0)), str(r.get("note") or "")

def tick(now=None):
    """Every tick: finish every WAITING row (`finish` with wait_s 0) - whatever HD_GATE_ON says now: a Short the gate took private is never left
    private because the switch was turned (R18 (4 a)); then the long video's gate and his window (`long_tick`). Returns the ids of the rows it looked at."""
    now = now or now_utc(); done = []
    try: rows = [r for r in store().rows(TAB) if r.get("state") == WAITING]
    except Exception: rows = []
    for r in rows:
        try: finish(r["vid"], 0, now); done.append(r["vid"])
        except Exception as e: log(f"HD gate: {r.get('vid')} not finished this tick: {scrub(e)[:160]}", "WARN")
    try: long_tick(now)
    except Exception as e: log(f"HD gate: the long videos were not looked at this tick: {scrub(e)[:160]}", "WARN")
    return done

# ------------------------------------------------------------------ the long video (step 10): its public time moves, it is never made public by code
LONG_STATUSES = ("SCHEDULED", "AWAITING_APPROVAL")       # a video uploaded with its time; only a SCHEDULED one's time is ever moved

def long_step(slot, public_at, got, now):
    """Pure: what the gate does to a long video's public time at this tick - ("none", None), ("push", target) or ("pull", target). `public_at` = the
    time YouTube publishes it now (empty = the slot: `public_at or slot`, R17 (3 c)). Before slot - HD_LONG_LEAD_MIN: nothing. Not ready: the target is
    at least HD_GUARD_MIN after this tick, on HD_STEP_MIN steps after the slot, never past slot + HD_LONG_CAP_MIN, and only ever later. Ready: back to
    the first step at or after the slot that is 5 minutes away, and only ever earlier. R22 (3): the guard outlasts the working clock's gap, so the next
    tick always comes before a video not in HD is public, until the cap; the lead holds one tick."""
    lead, step, guard, cap = (dt.timedelta(minutes=S(k, float)) for k in ("HD_LONG_LEAD_MIN", "HD_STEP_MIN", "HD_GUARD_MIN", "HD_LONG_CAP_MIN"))
    public_at = public_at or slot
    if now < slot - lead: return "none", None
    def on_step(t): return slot + step * math.ceil(max(0.0, (t - slot) / step))
    if not ready(got):
        target = min(on_step(now + guard), slot + cap)
        return ("push", target) if target > public_at else ("none", None)
    target = max(slot, on_step(now + dt.timedelta(minutes=5)))
    return ("pull", target) if target < public_at else ("none", None)

def _told(key):
    """Was a row with this key ever sent to him (open or closed)? His window is ONE card a video, and one late row."""
    try: return any(r.get("dedupe_key") == key for r in store().rows("Owner_Actions"))
    except Exception: return False

def long_line(e, got, now):
    """The `hd_gate` line of a long video YouTube shows public: "public N min after upload; HD yes" or "public N min after upload; HD NO (the cap)" - N
    from `uploaded_at` to the time it went public (`public_at`, empty = the slot; never later than now). Without HD before the cap: "HD NO"."""
    slot = parse_iso(e.get("slot_et")); pa = parse_iso(e.get("public_at")); up = parse_iso(e.get("uploaded_at"))
    went = min(pa or slot or now, now)
    head = f"public {_mins(up, went)} min after upload" if up else "public (its upload time is not on record)"
    if got.get("hd"): return head + "; HD yes"
    at_cap = bool(pa and slot and pa >= slot + dt.timedelta(minutes=S("HD_LONG_CAP_MIN", float)))
    return head + ("; HD NO (the cap)" if at_cap else "; HD NO")

def window(e, slot, got, now):
    """HIS WINDOW (item 156): on its day (India time) a long video that is uploaded and ready gets ONE card `prepublic` - the end screen in Studio,
    optional - with DONE (R18 (6): it stands under "Needs you" and in the 18:00 list; made before 09:00 it is in the morning list), the default "it goes
    out without an end screen", expiring at the slot. Not ready by 08:30 India time on its day: one `hd_late` row. Nothing after the slot."""
    from whatifs import notify as NT
    ep, vid = e["episode_id"], e["yt_id"]; title = e.get("title") or ep; at = slot.astimezone(NT.IST).strftime("%H:%M")
    if now >= slot or _told(f"prepublic|{ep}"): return
    if ready(got):
        NT.send("prepublic", f"Tonight {at}: {title}. Optional before it goes public: the end screen, about 30 seconds in Studio: "
                             f"https://studio.youtube.com/video/{vid}/edit", [("Done", "DONE")], episode=ep,
                default="it goes out without an end screen", expires_h=max(0.25, (slot - now).total_seconds() / 3600), dedupe_key=f"prepublic|{ep}")
    elif now.astimezone(NT.IST).time() >= dt.time(8, 30) and not _told(f"hd_late|{ep}"):
        NT.send("hd_late", f"{title}: YouTube does not show it in HD yet ({now.astimezone(NT.IST).strftime('%H:%M')} India time). It still goes out tonight; "
                           f"while it waits for HD its time moves by up to {S('HD_LONG_CAP_MIN', int)} minutes past {at}.", episode=ep, dedupe_key=f"hd_late|{ep}")

def long_tick(now=None):
    """The long video's gate and his window, at every tick, with HD_GATE_ON (switched off, the gate stops moving times and YouTube's own schedule
    publishes the video - R18 (4 a)). Only a SCHEDULED video's time is moved: a held or waiting one is never touched. YouTube is read first: a video it
    no longer shows private (his own hand in Studio, YouTube's schedule, an early release through `go_public`) gets its `hd_gate` line and is left alone
    - YouTube refuses a time on a video that was ever published (R17 ADDS (A)); an empty read moves nothing (R18 (5)). The new time is written to
    `public_at` - the gate is its one writer (R17 (3 c)). Returns the ids of the episodes whose time moved."""
    from whatifs import publish as PUB, notify as NT
    now = now or now_utc(); moved = []
    if not S("HD_GATE_ON", bool): return moved
    lead = dt.timedelta(minutes=S("HD_LONG_LEAD_MIN", float)); today = now.astimezone(NT.IST).date()
    try: eps = [e for e in store().rows("Episodes") if e.get("status") in LONG_STATUSES and e.get("yt_id") and parse_iso(e.get("slot_et"))]
    except Exception: return moved
    for e in eps:
        try:
            slot = parse_iso(e["slot_et"]); his_day = slot.astimezone(NT.IST).date() == today
            gate = e.get("status") == "SCHEDULED" and now >= slot - lead
            if not (his_day or gate): continue                                       # nothing to read yet: 1 quota unit a read
            got = PUB.yt_read(e["yt_id"])
            if his_day: window(e, slot, got, now)
            if not gate or not got: continue                                         # R18 (5): an empty read is not "already public" and moves nothing
            if (got.get("privacy") or "") != "private":                              # R17 ADDS (A): published - never scheduled again
                if not e.get("hd_gate"):
                    line = long_line(e, got, now); store().update("Episodes", "episode_id", e["episode_id"], {"hd_gate": line, "updated": iso()})
                    if not got.get("hd"): log(f"HD gate: {e['episode_id']} is public without HD (a miss): {line}", "WARN")
                continue
            act, target = long_step(slot, parse_iso(e.get("public_at")) or slot, got, now)
            if act in ("push", "pull") and PUB.yt_schedule(e["yt_id"], iso(target)):
                store().update("Episodes", "episode_id", e["episode_id"], {"public_at": iso(target), "updated": iso()}); moved.append(e["episode_id"])
                log(f"HD gate: {e['episode_id']} {'moved later' if act == 'push' else 'moved back'} to {iso(target)} ({'in HD' if ready(got) else 'not in HD yet'})")
        except Exception as x: log(f"HD gate: the long video {e.get('episode_id')} was not looked at: {scrub(x)[:160]}", "WARN")
    return moved
