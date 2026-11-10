"""Scheduler and upkeep: tick, release, packaging rescue, hold/resume, trend scout, learning loop, guardian, setup, self-test and the one-time setting moves. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os, json, random, re, datetime as dt, statistics
import requests
from zoneinfo import ZoneInfo
import hashlib
from whatifs.core import S, store, log, iso, parse_iso, now_utc, set_setting, status, flush_log, JOB, FAKE, env, DEFAULTS, TABS, month_spend, gheaders, WORK, scrub
from whatifs import prompts as P
from whatifs.models import ask, discover_models
from whatifs import publish as PUB
from whatifs import governor as G
from whatifs import growth as GR
from whatifs import playbook as PB
from whatifs.checkpoint import attempts as _attempts
from whatifs import checkpoint as _CK

ET = ZoneInfo("America/New_York")
DAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

def paused():
    if S("PAUSED", bool): return True
    pu = parse_iso(S("PAUSED_UNTIL"))
    if pu and pu > now_utc(): return True
    return False

def next_slots(n=3, after=None):
    after = after or now_utc()
    try: hh, mm = [int(x) for x in (S("PUBLISH_HOUR_ET").strip() + ":0").split(":")[:2]]   # '10:00' or '10:00:00' (Sheets time)
    except Exception: hh, mm = 10, 0
    from whatifs.governor import publish_days                       # v9.4a: Runway mode publishes on RUNWAY_PUBLISH_DAYS
    days = [DAYS[d.strip()[:3]] for d in publish_days().split(",") if d.strip()[:3] in DAYS]
    out, d0 = [], after.astimezone(ET).date()
    for k in range(0, 21):
        day = d0 + dt.timedelta(days=k)
        if day.weekday() not in days: continue
        rng = random.Random(str(day)); jit = rng.randint(-S("PUBLISH_JITTER_MIN", int), S("PUBLISH_JITTER_MIN", int))
        t = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=ET) + dt.timedelta(minutes=jit)
        t = t.replace(minute=(t.minute // 5) * 5, second=0)
        if t.astimezone(dt.timezone.utc) > after: out.append(t.astimezone(dt.timezone.utc))
        if len(out) >= n: break
    return out

def _note(e, add):
    n = str(e.get("notes") or "")
    return (n + " | " + add).strip(" |")[:400] if add not in n else n

def kill_check():
    """Owner typed KILL: the video goes private and is never released. Runs even while paused."""
    if not S("KILL_CHECK", bool): return
    st = store()
    for e in st.rows("Episodes"):
        if e.get("status") in ("SCHEDULED", "HELD", "UPLOADED") and str(e.get("kill", "")).upper().startswith("KILL") and e.get("yt_id"):
            PUB.yt_set_privacy(e["yt_id"], "private"); st.update("Episodes", "episode_id", e["episode_id"], {"status": "KILLED", "updated": iso()})
            log(f"{e['episode_id']} killed by owner before release")
        elif e.get("status") == "HOLD_QC" and str(e.get("kill", "")).upper().startswith("KILL"):      # v8.2: a held video is dropped by typing KILL (nothing was uploaded)
            st.update("Episodes", "episode_id", e["episode_id"], {"status": "KILLED", "updated": iso()}); log(f"{e['episode_id']} (held) dropped by owner")
            _CK.clear(e["episode_id"])          # v8.3: its saved pictures and clips no longer sit in Drive for ever

def hold_scheduled(reason="paused"):
    """While paused, videos already on YouTube's schedule are switched to private so they do NOT publish on their own."""
    st = store(); n = 0
    for e in st.rows("Episodes"):
        t = parse_iso(e.get("slot_et"))
        if e.get("status") == "SCHEDULED" and e.get("yt_id") and t and t > now_utc():
            if PUB.yt_set_privacy(e["yt_id"], "private"):
                st.update("Episodes", "episode_id", e["episode_id"], {"status": "HELD", "notes": _note(e, f"held: {reason}"), "updated": iso()}); n += 1
                log(f"{e['episode_id']} held ({reason}) - it will be re-scheduled when the pause ends")
    return n

def resume_held():
    """Pause is over: put held videos back on the schedule (their own slot if still ahead, else the next free slot)."""
    st = store(); eps = st.rows("Episodes")
    held = [e for e in eps if e.get("status") == "HELD" and e.get("yt_id")]
    if not held: return
    taken = {e.get("slot_et") for e in eps if e.get("status") in ("SCHEDULED", "LIVE1", "LIVE")}
    for e in sorted(held, key=lambda x: x.get("slot_et", "")):
        t = parse_iso(e.get("slot_et")); new = e.get("slot_et")
        if not t or t < now_utc() + dt.timedelta(minutes=45) or new in taken:
            new = next((s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in next_slots(12, now_utc() + dt.timedelta(minutes=45))
                        if s.strftime("%Y-%m-%dT%H:%M:%SZ") not in taken), None)
        if not new: continue
        try:
            PUB.yt_schedule(e["yt_id"], new); taken.add(new)
            st.update("Episodes", "episode_id", e["episode_id"], {"status": "SCHEDULED", "slot_et": new, "notes": _note(e, f"re-scheduled {new}"), "updated": iso()})
            log(f"{e['episode_id']} re-scheduled for {new}")
        except Exception as x: log(f"re-schedule of {e['episode_id']} failed: {x}", "WARN")

def _give_up_stuck(eps):
    """A release that keeps failing must never block new videos. After RELEASE_GIVEUP_HOURS it is closed with a note."""
    st = store(); g = dt.timedelta(hours=S("RELEASE_GIVEUP_HOURS", float))
    for e in eps:
        t = parse_iso(e.get("slot_et"))
        if not t: continue
        if e.get("status") == "SCHEDULED" and now_utc() > t + g:
            try: pub = PUB.yt_status(e["yt_id"]) == "public"
            except Exception: pub = False
            if pub:
                st.update("Episodes", "episode_id", e["episode_id"], {"status": "LIVE", "notes": _note(e, "reels skipped: release kept failing"), "updated": iso()})
                log(f"{e['episode_id']}: reels given up after {g}", "WARN")
            else:
                st.update("Episodes", "episode_id", e["episode_id"], {"status": "STUCK_PRIVATE", "notes": _note(e, "video never became public"), "updated": iso()})
                try:
                    from whatifs import launch as LA; LA.lock_detected(e["yt_id"], ["a scheduled video never became public"])      # v9.3.1 (L3): hold new spend
                except Exception as x: log(f"lock detector skipped: {scrub(x)}", "WARN")
                PUB.email("A video is stuck on Private", f"<p>Episode {e['episode_id']} (<a href='https://studio.youtube.com/video/{e['yt_id']}/edit'>open in Studio</a>) "
                          "did not become public at its slot. The lock detector has paused new videos so nothing is wasted; a separate urgent email explains the next step. "
                          "You can publish this one yourself in the YouTube Studio app (set it to Public).</p>")
            e["status"] = "closed"
        elif e.get("status") == "LIVE1" and now_utc() > t + dt.timedelta(minutes=S("REEL2_DELAY_MIN", int)) + g:
            st.update("Episodes", "episode_id", e["episode_id"], {"status": "LIVE", "notes": _note(e, "reel 2 skipped: release kept failing"), "updated": iso()})
            log(f"{e['episode_id']}: reel 2 given up", "WARN"); e["status"] = "closed"

AUDIT_WORDS = {"approved": "approved - uploads can go public",
               "sent": "SENT - waiting for Google (days to weeks). Videos stay private until it is approved. It flips to approved by itself when a video goes public",
               "not_sent": "not needed unless the upload check finds a lock (YouTube lifted the private lock on 2 Nov 2026; see Setup_Status upload_check)"}
def audit_state():
    a = str(S("API_AUDIT_STATUS")).strip().lower().replace(" ", "_")
    return a if a in AUDIT_WORDS else "not_sent"
def audit_seen_public():
    """v8.4: a video of this project has just been confirmed public, so the YouTube API audit must have passed. Records it (Settings + Setup_Status) once."""
    try:
        if audit_state() == "approved": return
        set_setting("API_AUDIT_STATUS", "approved"); status("youtube_api_audit", True, AUDIT_WORDS["approved"])
        log("YouTube API audit: a video is public, so the audit is approved")
    except Exception as x: log(f"audit status update skipped: {scrub(x)}", "WARN")
_AUDIT_TEST = [False]        # tests switch this on; in fake mode the gate is otherwise off so the offline rehearsal can make many videos
def audit_gate(eps):
    """(ok, why). Videos uploaded by a project the YouTube API audit has not approved are locked to Private for good (YouTube allows no appeal; they would have to be
    uploaded again by hand). So before approval only AUDIT_PRE_APPROVAL_EPISODES videos (default 1: the one you film for the audit form) are produced; the rest wait,
    and no money is spent on videos that could never be seen."""
    if FAKE and not _AUDIT_TEST[0]: return True, ""
    from whatifs import launch as LA                                   # v9.3.1 (L9): the upload check replaces the audit (YouTube lifted the lock on 2 Nov 2026)
    if LA.lock_state() == "on": return False, "YouTube is keeping uploads private (UPLOAD_LOCK = on); new videos wait so nothing is spent on videos nobody can see"
    if LA.uploads_open(): return True, ""
    try: lim = S("AUDIT_PRE_APPROVAL_EPISODES", int)
    except Exception: lim = 1
    n = sum(1 for e in eps if e.get("yt_id"))
    return (n < lim), f"{n} video(s) uploaded and the YouTube API audit is not approved yet (limit {lim}); new videos wait so no money is spent on videos that would stay private"
def audit_nudge(eps):
    """The audit form is the one setup step that is easy to forget and that nothing else forces. Once a video has been uploaded (so there is something to film for the form)
    and the audit is not approved, one email a week says exactly what to do. Never blocks anything."""
    st_ = audit_state()
    from whatifs import launch as LA
    if LA.lock_state() != "on": return                               # v9.3.1: the audit form is only needed if the upload check found a lock
    if st_ == "approved" or not any(e.get("yt_id") for e in eps): return
    last = parse_iso(S("AUDIT_NUDGE_AT"))
    if last and now_utc() - last < dt.timedelta(days=6): return
    if st_ == "not_sent":
        PUB.email("Reminder: send the YouTube API audit form", "<p>Your first video is uploaded but stays <b>private</b>, and new videos are paused, until Google approves this project (the YouTube API audit).</p>"
                  "<p>The form is not sent yet. Open <b>SETUP_CHECKLIST.md, Step 4b, Part B</b> (or tell your Claude setup chat: \"do Step 4b Part B\"); it takes about 20 minutes and every answer is written out. "
                  "After sending it, set <b>Settings -> API_AUDIT_STATUS = sent</b>.</p>")
    else:
        PUB.email("Waiting for the YouTube API audit", "<p>The audit form was sent. New videos are paused until Google approves it, so no money is spent on videos that would stay private.</p>"
                  "<p>When Google's approval email arrives, set <b>Settings -> API_AUDIT_STATUS = approved</b>; production restarts by itself within 30 minutes. "
                  "If three weeks pass with no reply, check the inbox and spam of the account that sent the form and answer anything Google asked.</p>")
    set_setting("AUDIT_NUDGE_AT", iso())

def recover_stuck(eps):
    """v8.3: a video that stayed private (usually the API audit was still pending) is checked again about twice a day for 30 days. If it has become public it is
    closed as LIVE so learning counts it; its reels are skipped (their moment passed)."""
    st = store()
    for e in eps:
        if e.get("status") != "STUCK_PRIVATE" or not e.get("yt_id"): continue
        t = parse_iso(e.get("slot_et")); last = parse_iso(e.get("updated"))
        if not t or now_utc() - t > dt.timedelta(days=30): continue
        if last and now_utc() - last < dt.timedelta(hours=12): continue
        try: pub = PUB.yt_status(e["yt_id"]) == "public"
        except Exception: pub = False
        st.update("Episodes", "episode_id", e["episode_id"], dict({"updated": iso()}, **({"status": "LIVE", "notes": ((e.get("notes") or "") + " became public late; reels skipped").strip()} if pub else {})))
        if pub: log(f"{e['episode_id']} is public now (it had been stuck on private)"); audit_seen_public()

def clean_dead_checkpoints(eps):
    """v8.3: the saved bundle of an episode that failed for good (its slot has passed) is deleted from Drive."""
    for e in eps:
        t = parse_iso(e.get("slot_et"))
        if e.get("status") == "FAILED" and t and now_utc() > t + dt.timedelta(hours=6) and _CK.has(e):
            _CK.clear(e["episode_id"])

def tick():
    """Every 30 min. Decides whether a release is due AND (independently) whether to produce the next episode."""
    JOB["name"] = "tick"
    kill_check()
    if paused():
        n = hold_scheduled("paused"); log(f"paused - nothing to do ({n} scheduled video(s) held)"); return {"action": "paused"}
    resume_held()
    try:                                                        # v9: packaging rotation windows (title + thumbnail through the API)
        from whatifs import packaging as PK
        PK.rotate_tick()
    except Exception as x: log(f"packaging rotation skipped: {scrub(x)}", "WARN")
    try:                                                        # v9.4a (WP4): queued owner messages, silence = default, the digest
        from whatifs import notify as NT
        NT.tick()
        try:                                                    # v11 (K159): start a standalone Short when one is due (one dispatch per 50 min at most)
            from whatifs import shorts2 as SH2
            last = parse_iso(S("SHORTS_LAST_DISPATCH"))
            if SH2.due() and (not last or (now_utc() - last).total_seconds() > 3000):
                from whatifs import builds as BLD
                if BLD.dispatch("special.yml", {"kind": "short"}): set_setting("SHORTS_LAST_DISPATCH", iso())
        except Exception as x: log(f"Shorts dispatch skipped: {scrub(x)}", "WARN")
        try:                                                    # v11 (K160): the monthly Case Files countdown (once enough episodes are archived)
            from whatifs import spinoff as SPO
            mk = now_utc().strftime("%Y-%m")
            made = any(r.get("kind") == "casefiles" and str(r.get("ts", "")).startswith(mk) for r in store().rows("Specials"))
            if (S("CASEFILES_ON", bool) and not made and now_utc().day >= S("CASEFILES_DAY", int) and len(SPO.eligible()) >= S("CASEFILES_CASES", int)
                    and str(S("CASEFILES_LAST_DISPATCH") or "")[:7] != mk):
                from whatifs import builds as BLD
                if BLD.dispatch("special.yml", {"kind": "casefiles"}): set_setting("CASEFILES_LAST_DISPATCH", iso())
        except Exception as x: log(f"Case Files dispatch skipped: {scrub(x)}", "WARN")
        try:                                                    # v11 (K158): the 48-hour breakout monitor (1 API unit per 50 videos)
            from whatifs import breakout as BRKM; BRKM.monitor()
        except Exception as x: log(f"breakout monitor skipped: {scrub(x)}", "WARN")
        try:                                                    # v11 (K164/K165): Monday money re-plan, weekly tool scout, month restore
            from whatifs import replan as RPL, scout as SCT; RPL.month_restore(); RPL.weekly(); SCT.weekly()
        except Exception as x: log(f"re-plan / tool scout skipped: {scrub(x)}", "WARN")
        try:                                                    # v11: month rollover (breakout fund) + month close records
            from whatifs import governor as GVR; GVR.rollover_month(); GVR.record_month_close()
        except Exception as x: log(f"month records skipped: {scrub(x)}", "WARN")
        try:                                                    # v10.3 (K153): the daily / weekly WhatsApp briefs with a chart
            from whatifs import digests as DGS; DGS.tick()
        except Exception as x: log(f"WhatsApp briefs skipped: {scrub(x)}", "WARN")
    except Exception as x: log(f"owner messages skipped: {scrub(x)}", "WARN")
    try:                                                        # v12: the organisation's SLA watchdog (overdue memos climb the ladder) and the check for runs that never reported
        from whatifs.org import memos as MEMO, runner as ORGR, execute as EXE
        if ORGR.on(): MEMO.watchdog(); ORGR.audit(); EXE.engine_tick()          # the Execution Engine's pass: start, verify or roll back every change made by ticket
    except Exception as x: log(f"organisation watchdog skipped: {scrub(x)}", "WARN")
    try:                                                        # v10 (K140): key/plan expiry reminders (14 and 3 days before), once a day
        from whatifs import caretaker as CT
        if now_utc().hour == 8 and now_utc().minute < 30:
            CT.ensure_expiry_seed(); CT.expiry_check()
            from whatifs import steward as STWD; STWD.apply_planned()               # v10.1 (K150): announced model switches whose date has come
    except Exception as x: log(f"expiry check skipped: {scrub(x)}", "WARN")
    try:                                                        # v10 (K136): the heads-up card 3 days before an occasion special (once)
        from whatifs import occasions as OC
        if now_utc().hour == 9 and now_utc().minute < 30: OC.heads_up()
    except Exception as x: log(f"occasion heads-up skipped: {scrub(x)}", "WARN")
    try:                                                        # v10 (G2): a Short taking off = one 'act now' link card (one batched views call)
        from whatifs import shortslab as SL
        if now_utc().minute < 30: SL.breakouts()                   # hourly is enough
    except Exception as x: log(f"breakout check skipped: {scrub(x)}", "WARN")
    try:                                                        # v10 G4: one video's localizations per tick (never near a release)
        from whatifs import hours as HR, orchestra as OR
        if OR.heavy_allowed(what="localizations"): HR.tick()
    except Exception as x: log(f"localizations skipped: {scrub(x)}", "WARN")
    try:                                                        # v9.4b: the dashboard snapshot (no-op until Cloudflare is set up)
        from whatifs import dash as DS
        DS.publish()
    except Exception as x: log(f"dashboard snapshot skipped: {scrub(x)}", "WARN")
    if not S("VOICE") and not _designed_voices_ok():           # v10.2 (#9): with the four designed voices passing Voice_Check, no narrator pick is needed
        t = parse_iso(S("VOICE_SAMPLES_AT"))
        if not t: return {"action": "waiting_for_voice_samples"}
        if now_utc() - t > dt.timedelta(hours=S("VOICE_WAIT_HOURS", float)):
            set_setting("VOICE", "A"); log("no voice picked in time - using A")
        else:
            return {"action": "waiting_for_voice_pick"}
    eps = store().rows("Episodes")
    _give_up_stuck(eps)
    try: recover_stuck(eps); clean_dead_checkpoints(eps)
    except Exception as x: log(f"housekeeping skipped: {scrub(x)}", "WARN")
    try: audit_nudge(eps)
    except Exception as x: log(f"audit reminder skipped: {scrub(x)}", "WARN")
    due = []
    for e in eps:
        if e.get("status") == "SCHEDULED":
            t = parse_iso(e.get("slot_et"))
            if t and now_utc() >= t + dt.timedelta(minutes=S("REEL1_DELAY_MIN", int)): due.append(("release1", e["episode_id"]))
        if e.get("status") == "LIVE1":
            t = parse_iso(e.get("slot_et"))
            if t and now_utc() >= t + dt.timedelta(minutes=S("REEL2_DELAY_MIN", int)): due.append(("release2", e["episode_id"]))
        for k in (2, 3):
            if extra_reel_due(e, k): due.append((f"release{k+1}", e["episode_id"]))
    prod = _produce_slot(eps)
    if due:
        a = {"action": due[0][0], "episode": due[0][1]}
        if prod and prod != "busy": a["slot"] = prod          # a release never blocks production (both jobs run)
        return a
    if prod == "busy": return {"action": "busy"}
    if prod: return {"action": "produce", "slot": prod}
    return {"action": "idle"}

def _produce_slot(eps):
    busy = [e for e in eps if e.get("status") in ("PLANNING", "VOICING", "VISUALS", "UPLOADED")]
    stale = [e for e in busy if (now_utc() - (parse_iso(e.get("updated")) or now_utc())).total_seconds() > 6 * 3600]
    for e in stale:
        if e.get("yt_id"):
            try: PUB.yt_set_privacy(e["yt_id"], "private")    # a half-finished upload must never publish on its own
            except Exception as x: log(f"could not make {e['yt_id']} private: {x}", "WARN")
        store().update("Episodes", "episode_id", e["episode_id"], {"status": "FAILED", "notes": "timed out", "updated": iso()})
    if [e for e in busy if e not in stale]: return "busy"
    held = [e for e in eps if e.get("status") == "HOLD_QC"]
    if held and len(held) < max(1, S("HOLD_BLOCK_AFTER", int)):
        log(f"{len(held)} video(s) held by final QC - the next slot still goes ahead (production stops at {S('HOLD_BLOCK_AFTER', int)} held)", "WARN")
        held = []
    if held:       # several holds in a row may mean something systemic: no new paid work until the owner clicks the fix link or types KILL. One reminder per day.
        last = parse_iso(S("HOLD_MAIL_AT"))
        if not last or now_utc() - last > dt.timedelta(days=1):
            from whatifs.episode import _fix_link
            PUB.email("Reminder: a video is waiting for your fix click", "".join(f"<p>{e['episode_id']}: <a href='{_fix_link(e['episode_id'])}'>click to fix</a> (or type KILL in its kill cell). New videos are paused until then.</p>" for e in held))
            set_setting("HOLD_MAIL_AT", iso())
        log(f"{len(held)} video(s) held by final QC - not starting a new episode", "WARN"); return None
    ok_a, why_a = audit_gate(eps)
    if not ok_a: log(f"upload gate: {why_a}", "WARN"); return None
    ok, why = G.can_start_episode()          # v8.1: the cap is checked BEFORE an episode row exists, so a full month never creates failed rows or half-paid videos
    if not ok:
        log(f"budget gate: not starting a new episode - {why}", "WARN")
        mk = now_utc().strftime("%Y-%m")
        if S("BUDGET_MAIL_MONTH") != mk:
            PUB.email("Monthly budget reached", f"<p>{why}.</p><p>Videos that are already scheduled still publish. New videos resume on the 1st of next month, "
                      "or raise BUDGET_FLOOR_INR / BUDGET_CEILING_INR in Settings if you want to spend more. Nothing else is needed.</p>")
            set_setting("BUDGET_MAIL_MONTH", mk)
        return None
    taken = {e.get("slot_et") for e in eps if e.get("status") in ("SCHEDULED", "LIVE1", "LIVE", "HELD", "HOLD_QC", "SKIPPED")}      # v8.10: a skipped slot stays skipped
    for slot in next_slots(4):
        s = slot.strftime("%Y-%m-%dT%H:%M:%SZ")
        if s in taken: continue
        hours = (slot - now_utc()).total_seconds() / 3600
        tries = sum(_attempts(e) for e in eps if e.get("slot_et") == s and e.get("status") == "FAILED")      # v8.2: a resumed attempt reuses its row, so attempts are counted, not rows
        if hours <= S("PRODUCE_AHEAD_HOURS", float) and tries < 2: return s
        if tries >= 2: continue
        break
    return None

def release(ep_id, which):
    """Reel k goes to YouTube Shorts + Instagram + Facebook once the long video is live. Posts the channel comment on the long video
    (YouTube's API cannot pin comments; pin it in Studio if you like)."""
    JOB["name"] = "release"; JOB["episode"] = ep_id
    st = store(); e = next(x for x in st.rows("Episodes") if x["episode_id"] == ep_id)
    want = {"release1": "SCHEDULED", "release2": "LIVE1"}.get(which, "LIVE")
    if e.get("status") != want: log(f"{which} skipped: status is {e.get('status')} (already done or closed)"); return
    if S("KILL_CHECK", bool) and str(e.get("kill", "")).upper().startswith("KILL"):
        PUB.yt_set_privacy(e["yt_id"], "private"); st.update("Episodes", "episode_id", ep_id, {"status": "KILLED", "updated": iso()}); log("killed by owner"); return
    k = {"release1": 0, "release2": 1, "release3": 2, "release4": 3}[which]
    if k >= 2: return _release_extra(st, e, k)
    if k == 0:
        if PUB.yt_status(e["yt_id"]) != "public":
            t = parse_iso(e.get("slot_et"))
            if t and now_utc() > t + dt.timedelta(hours=S("PRIVATE_ALERT_HOURS", float)) and "private alert sent" not in str(e.get("notes", "")):
                PUB.email("Video not public yet", f"<p>Episode {ep_id} should be public by now but YouTube still shows it as private. "
                          "For the first videos this usually means the Google Cloud project still needs the YouTube API audit (SETUP_CHECKLIST Step 4b). "
                          f"The reels wait; after {S('RELEASE_GIVEUP_HOURS')} h the release is closed so new videos are never blocked.</p>")
                st.update("Episodes", "episode_id", ep_id, {"notes": _note(e, "private alert sent")})
            log("long video not public yet - waiting", "WARN"); return
        audit_seen_public()
    rel = _fetch_release(ep_id, e.get("assets"))
    if k == 0:
        PUB.yt_comment(e["yt_id"], rel.get("pinned", ""))
        try:                                                    # v10.1 (K149): the Instagram 'Case Files' carousel goes out with the episode
            from whatifs import carousel as CAR; CAR.post(ep_id)
        except Exception as x: log(f"carousel post skipped: {scrub(x)}", "WARN")
    long_url = f"https://youtu.be/{e['yt_id']}"
    upd = {"status": "LIVE1" if k == 0 else "LIVE", "updated": iso()}
    if k < len(rel.get("reels", [])):
        sid, ig, fb = _post_reel(rel["reels"][k], rel, long_url)
        if sid: upd[f"reel{k+1}_yt"] = sid
        if ig: upd[f"ig{k+1}"] = ig
        if fb: upd[f"fb{k+1}"] = fb
    st.update("Episodes", "episode_id", ep_id, upd)
    if not S("LAUNCH_DONE", bool) and k == 0:
        PUB.email("We're live", f"<p>Your first video is live: <a href='{long_url}'>{long_url}</a></p><p>Nothing to do. The channel now runs on its own.</p>")
        set_setting("LAUNCH_DONE", "TRUE")
    flush_log()

def _post_reel(r, rel, long_url):
    """Upload one reel: YouTube Shorts (+ a comment with the full-video link) and, if META_ON, Instagram + Facebook. Returns (shorts id, ig id, fb id); failures are logged."""
    sid = ig = fb = ""; path = r["file"]
    cap = f"{cap_hashtags(r['caption'])}\n\nFull video: {long_url}"
    if S("REEL1_SHORTS_ON", bool):
        try:
            sid = PUB.yt_upload(path, (r.get("hook") or rel["title"])[:80] + " #shorts", cap + "\n#shorts", ["shorts", "what if"], ai_label=S("AI_LABEL_DEFAULT", bool), short=True)
            PUB.yt_comment(sid, f"Full video: {long_url}")
        except Exception as x: log(f"short upload failed: {x}", "WARN")
    else: log("YouTube Shorts copy switched off (REEL1_SHORTS_ON = FALSE)")
    if not PUB.meta_ready() and S("META_ON", bool): log("Instagram/Facebook not connected (no Meta key yet): this reel goes to YouTube only")
    if PUB.meta_ready():            # v10.1: only when Meta is connected. v8.9.1 (fix): Instagram and Facebook are tried separately (one failing no longer skips the other), the reel file is sent
        opened, links = [], {}        # directly, a public Drive link is made only if a platform needs it, and every link made is closed again in 'finally'
        def link(p):
            if p not in links:
                fid, url = PUB.drive_upload(p, os.path.basename(p), public=True); opened.append(fid); links[p] = url
            return links[p]
        try:
            curl = None
            if r.get("cover"):
                try: curl = link(r["cover"])
                except Exception as x: log(f"reel cover link skipped: {scrub(x)}", "WARN")
            try: ig = PUB.ig_reel(None, cap.replace(long_url, "link in bio"), curl, video_path=path, url_fn=lambda: link(path))
            except Exception as x: log(f"instagram post failed: {scrub(x)}", "WARN")
            try: fb = PUB.fb_reel(None, cap, video_path=path, url_fn=lambda: link(path))
            except Exception as x: log(f"facebook post failed: {scrub(x)}", "WARN")
        finally:
            for fid in opened:
                try: PUB.drive_private(fid)
                except Exception as x: log(f"could not make a Drive link private again: {scrub(x)}", "WARN")
    return sid, ig, fb

def extra_reel_due(e, k, now=None):
    """v8.5: reel k (2 or 3, i.e. reel 3 or 4) is due when the long video's first two reels are done (status LIVE), its delay has passed, the reel file was
    actually made (its Drive id is in assets: older episodes have none, and nothing is downloaded to find that out) and it has not been tried yet."""
    if k + 1 > max(2, min(4, S("REELS_PER_VIDEO", int))) or e.get("status") != "LIVE" or not e.get("yt_id"): return False
    if f"reel{k+1}_yt" not in e: return False
    if re.search(r"reels skipped|became public late", str(e.get("notes") or "")): return False
    if str(e.get("kill", "")).upper().startswith("KILL"): return False      # KILL typed after launch: no more Shorts for it      # the launch reels were given up: the extra ones stay quiet too         # the Sheet has no v8.5 columns yet (run Setup once): without the cell to mark, a Short could be posted twice
    if str(e.get(f"reel{k+1}_yt") or "").strip(): return False
    try: assets = e.get("assets") if isinstance(e.get("assets"), dict) else json.loads(e.get("assets") or "{}")
    except Exception: assets = {}
    if f"reel{k}.mp4" not in assets: return False
    t = parse_iso(e.get("slot_et")); now = now or now_utc()
    if not t or now < t + dt.timedelta(minutes=S(f"REEL{k+1}_DELAY_MIN", int)): return False
    if now > t + dt.timedelta(minutes=S(f"REEL{k+1}_DELAY_MIN", int)) + dt.timedelta(hours=S("RELEASE_GIVEUP_HOURS", float)): return False
    return True

def _release_extra(st, e, k):
    """v8.5: reels 3 and 4 go out on the following days (a Short on 6 of 7 days with Tue/Sat videos). One try each: the cell is marked before anything is
    posted, so a crash can never post a Short twice; the long video's status is never changed."""
    ep_id = e["episode_id"]; col = f"reel{k+1}_yt"
    if not extra_reel_due(e, k): log(f"release{k+1} skipped: not due or already tried"); return
    st.update("Episodes", "episode_id", ep_id, {col: "trying " + iso(), "updated": iso()})
    upd = {}
    try:
        rel = _fetch_release(ep_id, e.get("assets")); reels = rel.get("reels", [])
        if k >= len(reels): upd[col] = "none"; log(f"release{k+1}: this episode has no reel {k+1}")
        else:
            sid, ig, fb = _post_reel(reels[k], rel, f"https://youtu.be/{e['yt_id']}")
            upd = {col: sid or ("off" if not S("REEL1_SHORTS_ON", bool) else "failed"), f"ig{k+1}": ig, f"fb{k+1}": fb}
    except Exception as x: upd[col] = "failed"; log(f"release{k+1} failed: {scrub(x)}", "WARN")
    upd["updated"] = iso(); st.update("Episodes", "episode_id", ep_id, upd); flush_log()

def _fetch_release(ep_id, assets=None):
    d = os.path.join(WORK, ep_id); os.makedirs(d, exist_ok=True); path = os.path.join(d, "release.json")
    if not os.path.exists(path):
        ids = assets if isinstance(assets, dict) else json.loads(assets or "{}")
        for name, fid in ids.items():
            if name.startswith("_"): continue          # archive entries, not release files
            PUB.drive_download(fid, os.path.join(d, name))
    rel = json.load(open(path))
    for r in rel.get("reels", []):
        for key in ("file", "cover"):
            if r.get(key): r[key] = os.path.join(d, os.path.basename(r[key]))
    return rel

def cap_hashtags(text, n=5):
    """v8.9: Instagram enforces at most 5 hashtags per Reel (Dec 2025; extra tags can stop publishing or reach). Keep the first n, drop the rest."""
    seen = []
    def keep(m):
        seen.append(m.group(0)); return m.group(0) if len(seen) <= n else ""
    return re.sub(r"\s{2,}", " ", re.sub(r"#\w+", keep, str(text or ""))).strip()

# ---------------- v8.9: change-ready email + one-click merge (for Claude Code and the Repair Bot) ----------------
def pr_ready():
    """Runs in the Checks workflow after Plan Guard, every unit test and the rehearsal passed on a pull request. Emails the owner a review link and a
    one-click merge link (a pre-filled 'MERGE #n' issue: pressing Submit runs the Merge workflow, owner-only). Never raises."""
    JOB["name"] = "prready"
    if not S("PR_MAIL_ON", bool): log("change-ready email switched off (PR_MAIL_ON)"); return None
    from urllib.parse import quote
    repo, n, title, url = env("GH_REPO"), env("PR_NUMBER"), env("PR_TITLE")[:120], env("PR_URL")
    if not (repo and n.isdigit()): log("not a pull request run - no email"); return None
    merge = f"https://github.com/{repo}/issues/new?title={quote('MERGE #' + n)}&body={quote('Press Submit new issue. The robot merges the change only if every check is still green.')}"
    html = (f"<p><b>A code change passed every check</b> (Plan Guard, all unit tests, the full offline rehearsal):<br>#{n} {title}</p>"
            f"<p><a href='{merge}'>Merge it: click, then press the green <b>Submit new issue</b></a></p><p><a href='{url}'>Review it on GitHub first</a> "
            "(the green Merge button there works too).</p><p>After the merge the next half-hourly run uses the new pipeline by itself. To drop the change, close the pull request.</p>")
    try: PUB.email(f"Change ready to merge: #{n}", html); return merge
    except Exception as x: log(f"change-ready email failed: {scrub(x)}", "WARN"); return None

# ---------------- trend scout (weekly) ----------------
def trend_scout():
    JOB["name"] = "trends"
    api = []
    try:   # weekly model refresh (K11: model names discovered live, never typed)
        m = discover_models(); set_setting("MODELS_REFRESHED_AT", iso()); log(f"models refreshed: {m}")
    except Exception as e: log(f"weekly model refresh failed: {e}", "WARN")
    if not FAKE:
        try:
            after = (now_utc() - dt.timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
            for q in ["what if", "what would happen if", "science explained", "space facts"]:
                r = requests.get("https://www.googleapis.com/youtube/v3/search", headers=gheaders(), params={"part": "snippet", "q": q, "type": "video",
                                 "order": "viewCount", "publishedAfter": after, "maxResults": 10, "relevanceLanguage": "en", "regionCode": "US"}, timeout=30).json()
                ids = ",".join(i["id"]["videoId"] for i in r.get("items", []))
                if ids:
                    v = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=gheaders(), params={"part": "snippet,statistics,contentDetails", "id": ids}, timeout=30).json()
                    for x in v.get("items", []):
                        api.append({"title": x["snippet"]["title"], "channel": x["snippet"]["channelTitle"], "views": x["statistics"].get("viewCount"),
                                    "len": x["contentDetails"]["duration"]})
            ch = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=gheaders(), params={"part": "snippet,statistics", "chart": "mostPopular",
                              "regionCode": "US", "videoCategoryId": "28", "maxResults": 15}, timeout=30).json()
            for x in ch.get("items", []): api.append({"chart": "US science top", "title": x["snippet"]["title"], "channel": x["snippet"]["channelTitle"], "views": x["statistics"].get("viewCount")})
            api += _outliers()
        except Exception as e: log(f"youtube trend pull failed: {e}", "WARN")
        try:
            rss = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=30).text
            api.append({"google_trends_us": re.findall(r"<title>([^<]+)</title>", rss)[1:20]})
        except Exception as e: log(f"google trends failed: {e}", "WARN")
    rep = ask("research", P.fill(P.TRENDS, channels=S("TREND_CHANNELS"), api=json.dumps(api[:40])), "Research now. Return the JSON only.",
              search=True, fake_key="research", temperature=0.3)
    wk = now_utc().strftime("%G-W%V"); rows = []
    for x in rep.get("exploding", [])[:12]: rows.append({"week": wk, "kind": "exploding", "item": x.get("title", ""), "detail": json.dumps(x.get("patterns", {}))[:900], "source": x.get("channel", "")})
    for x in rep.get("rules_for_room", [])[:8]: rows.append({"week": wk, "kind": "rule", "item": x, "detail": "", "source": "trend scout"})
    for x in rep.get("rising_angles", [])[:6]: rows.append({"week": wk, "kind": "angle", "item": x, "detail": "", "source": "trend scout"})
    crit = []
    for x in rep.get("platform_changes", [])[:8]:
        rows.append({"week": wk, "kind": "platform", "item": x.get("change", ""), "detail": x.get("severity", ""), "source": x.get("source", "")})
        if x.get("severity") == "critical" and _official(x.get("source", "")) and re.search(r"\b(ai|synthetic|inauthentic|mass[- ]produced|repetitive)\b", x.get("change", "").lower()) and "monet" in x.get("change", "").lower():
            crit.append(x)
    store().append("Trend_Brief", rows)
    try:                                                       # v8.10: technique observations from top niche videos (titles, descriptions, top comments)
        from whatifs import craft as CR
        CR.research_techniques()
    except Exception as x: log(f"technique research skipped: {scrub(x)}", "WARN")
    PB.ensure_seed(); PB.research()                          # v8.7: the proactive, evidence-graded playbook research (never raises, inside the cap)
    if crit:
        seen = [x for x in S("GUARDIAN_SEEN").split("|") if x]
        def sig(x): return hashlib.md5(re.sub(r"[^a-z]", "", (x.get("change", "") + x.get("platform", "")).lower())[:160].encode()).hexdigest()[:10]
        new = [x for x in crit if sig(x) not in seen]
        if new:
            set_setting("GUARDIAN_SEEN", "|".join((seen + [sig(x) for x in new])[-40:]))
            guardian(new)
        else: log("policy items already acted on before - no new pause")
    flush_log(); return rep

def _official(src):
    """v8.3: the channel is paused only for a policy change reported by an official YouTube / Google page (a search headline alone could be planted by anyone).
    v8.7: the same strict test as the Playbook (playbook.is_official): any creator's youtube.com/watch link no longer counts as official."""
    if not S("GUARDIAN_NEEDS_OFFICIAL", bool): return True
    from whatifs.playbook import is_official
    return is_official(src)

def _outliers():
    """Latest uploads of the watched channels; flag videos with views >= 2x the channel's recent median (exploding)."""
    out, missing = [], []
    for h in [x.strip() for x in S("TREND_CHANNELS").split(",") if x.strip()][:10]:
        try:
            c = requests.get("https://www.googleapis.com/youtube/v3/channels", headers=gheaders(), params={"part": "contentDetails", "forHandle": h}, timeout=30).json()
            up = c["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            pl = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", headers=gheaders(), params={"part": "contentDetails", "playlistId": up, "maxResults": 15}, timeout=30).json()
            ids = ",".join(i["contentDetails"]["videoId"] for i in pl.get("items", []))
            v = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=gheaders(), params={"part": "snippet,statistics,contentDetails", "id": ids}, timeout=30).json().get("items", [])
            views = [int(x["statistics"].get("viewCount", 0)) for x in v]
            if not views: continue
            med = statistics.median(views) or 1
            for x in v:
                r = int(x["statistics"].get("viewCount", 0)) / med
                if r >= 2: out.append({"channel": h, "title": x["snippet"]["title"], "x_median": round(r, 1), "len": x["contentDetails"]["duration"]})
        except Exception as e: log(f"outlier scan {h} failed: {e}", "WARN"); missing.append(h)
    status("trend_channels", not missing, ("not found: " + ", ".join(missing)) if missing else "all watched channels found")
    return out

def guardian(items):
    """Option B: pause only on a serious AI-monetisation rule change; auto-resume after 7 days."""
    until = (now_utc() + dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    set_setting("PAUSED_UNTIL", until)
    held = hold_scheduled("policy watch")
    PUB.email("Paused for 7 days (policy watch)", "<p>A possible change to AI-content monetisation rules was found:</p><ul>" +
              "".join(f"<li>{i.get('change')} ({i.get('source')})</li>" for i in items) +
              f"</ul><p>{held} already-scheduled video(s) were switched to private so they do not go out. "
              f"Publishing resumes automatically on {until[:10]} and held videos are re-scheduled. To resume now, set PAUSED_UNTIL to blank in Settings.</p>")
    log(f"guardian pause until {until}", "WARN")
    try:                                                         # v10 (K140): Policy Rescue: one urgent card with the impact and the choices
        from whatifs import caretaker as CT; CT.policy_rescue(items)
    except Exception as x: log(f"policy rescue card skipped: {scrub(x)}", "WARN")

# ---------------- learning loop (daily) ----------------
def learn():
    JOB["name"] = "learn"; st = store()
    try: st.ensure_tabs()                                       # v8.6: new tabs/columns appear by themselves (no manual Setup run needed)
    except Exception as x: log(f"could not refresh Sheet tabs: {scrub(x)}", "WARN")
    _top_up(st)                                                 # v8.7: new strategies (rhythm, sound) and the playbook seed reach older Sheets by themselves
    try: v810_upgrade(st)
    except Exception as x: log(f"v8.10 top-up skipped: {scrub(x)}", "WARN")
    try: v93_upgrade(st)                                         # v9.3: one-time default flips (owner values never touched)
    except Exception as x: log(f"v9.3 default flips skipped: {scrub(x)}", "WARN")
    try: v931_upgrade(st)                                        # v9.3.1
    except Exception as x: log(f"v9.3.1 default flips skipped: {scrub(x)}", "WARN")
    try: v94a_upgrade(st)                                        # v9.4a: the ₹4,700 cap
    except Exception as x: log(f"v9.4a cap move skipped: {scrub(x)}", "WARN")
    try: v10_upgrade(st)                                         # v10: ₹5,000 (specials)
    except Exception as x: log(f"v10 cap move skipped: {scrub(x)}", "WARN")
    try: v101_upgrade(st)                                        # v10.1: verified models, still size, Shorts cap
    except Exception as x: log(f"v10.1 flips skipped: {scrub(x)}", "WARN")
    try: v102_upgrade(st)                                        # v10.2: Kling 3.0, 4 animated scenes
    except Exception as x: log(f"v10.2 flips skipped: {scrub(x)}", "WARN")
    try: v11_upgrade(st)                                         # v11: the owner's November allowance
    except Exception as x: log(f"v11 flips skipped: {scrub(x)}", "WARN")
    try: v12_upgrade(st)                                         # v12: the owner's cadence (4 long videos a month, weekly)
    except Exception as x: log(f"v12 flips skipped: {scrub(x)}", "WARN")
    try:
        from whatifs import craft as CRF; CRF.seed_techniques()       # v9.3.2: the owner's pre-judged technique cards, filed once
    except Exception as x: log(f"technique seeding skipped: {scrub(x)}", "WARN")
    try:
        from whatifs import sheets as SH; SH.auto_lock()            # v9.3.1 (L6): unanswered sheets lock by default
    except Exception as x: log(f"sheet default lock skipped: {scrub(x)}", "WARN")
    # v12 B5: the stale research brief is renewed by R&D's daily run (whatifs/org/rnd.py daily), which runs just before this job's learning part
    try:                                                        # v9: the jury outside the video (comment, tally, teacup finders, queue, Season, Experiments)
        from whatifs import community as CM
        for e9 in st.rows("Episodes"):
            t9 = parse_iso(e9.get("slot_et"))
            if not e9.get("yt_id") or not t9 or now_utc() < t9 or now_utc() - t9 > dt.timedelta(days=28): continue
            try: plan9 = json.loads(e9.get("draw_json") or "{}").get("show_plan") or {}
            except Exception: plan9 = {}
            if not plan9: continue
            CM.post_jury_comment(e9, plan9)
            tl9 = CM.process_comments(e9, plan9)
            if tl9 is not None:
                try: cups9 = json.loads(e9.get("teacup_json") or "[]")
                except Exception: cups9 = []
                fn9 = CM.teacup_finders(CM.fetch_comments(e9["yt_id"]), cups9) if cups9 else []
                st.update_where("Season", {"episode_id": e9["episode_id"]}, {"jury_tally": json.dumps(tl9), "teacup_finders": ", ".join(fn9)})
            an9 = next((a for a in st.rows("Analytics") if a.get("episode_id") == e9["episode_id"]), None)
            if an9: CM.experiment_results(e9["episode_id"], e9["yt_id"], t9, an9)
        from whatifs import insights as INS                     # v9.1: viewers' 'what if' suggestions -> bench candidates; AI drafts (flagged, capped)
        INS.mine_comments(); INS.ai_drafts()
        CM.weekly_digest()
    except Exception as x: log(f"community step skipped: {scrub(x)}", "WARN")
    try:                                                        # v9: made-for-kids re-check during a video's first 7 days
        from whatifs import costguard as CG
        for e9 in st.rows("Episodes"):
            t9 = parse_iso(e9.get("slot_et"))
            if e9.get("yt_id") and t9 and now_utc() - t9 < dt.timedelta(days=7) and " True" not in str(e9.get("kids_check")):
                k9 = CG.kids_check(e9["yt_id"], e9["episode_id"])
                if k9 is not None: st.update("Episodes", "episode_id", e9["episode_id"], {"kids_check": f"{iso()} {k9}"})
    except Exception as x: log(f"made-for-kids re-check skipped: {scrub(x)}", "WARN")
    try:                                                        # v9: the character bible reaches older Sheets by itself (idempotent)
        from whatifs import show as SHOW
        SHOW.seed_characters(st)
    except Exception as x: log(f"character bible top-up skipped: {scrub(x)}", "WARN")
    try: pkg_rescue()
    except Exception as x: log(f"packaging check skipped: {scrub(x)}", "WARN")
    try:                                                        # v10 (K141/K142): daily pilot measurements and the Outlier Lab (never near a release)
        from whatifs import brain as BRN; BRN.daily()           # v11 (K155): Shorts outcomes, both technique libraries, forecast scoring
        from whatifs import reach as RCH; RCH.daily()           # v11 (K162): impressions + CTR (Reporting API)
        from whatifs import pilots as PLT
        PLT.measure()                                          # v12 B5: the Outlier Lab and the search-demand scores run in R&D's daily run (whatifs/org/rnd.py)
    except Exception as x: log(f"pilots / Outlier Lab skipped: {scrub(x)}", "WARN")
    try:                                                        # v12: Knowledge Palace upkeep, then mirrors of the learning core (just updated above) and the show records
        from whatifs.org import palace as PAL; PAL.daily(st)
    except Exception as x: log(f"palace upkeep skipped: {scrub(x)}", "WARN")
    try:                                                        # v9.4a: weekly platform change-log watch + Visual Lab ideas (₹0), never near a release
        from whatifs import orchestra as OR, facts_watch as FW, visual_lab as VL
        if OR.heavy_allowed(what="weekly watch") and now_utc().strftime("%a") in ("Sun",):
            FW.run(); VL.register(); VL.suggest()
            from whatifs import specials as SPX; SPX.record_views()       # v10: specials' 7-day engaged views feed the format weights
            from whatifs import shortslab as SL; SL.link_pack()            # v10 (G2): the weekly winners-only link card
            from whatifs import occasions as OCC; OCC.refresh_lunar_dates()  # v10 (K136): early December, next year's festival dates
            from whatifs import microscope as MSC; MSC.learn()                # v10 (K138): data rules from retention
            from whatifs import caretaker as CTK; CTK.backup(); CTK.advisor()  # v10 (K140): weekly Sheet backup + the Advisor card
            from whatifs import viewers as VWR, ypp as YPPW; VWR.collect(); YPPW.check()   # v10.1 (K147/K148): viewer questions + the 500-tier watch
            from whatifs import steward as STWD; STWD.watch()                            # v10.1 (K150): retirements and newer models (free)
            if not paused(): STWD.test_candidates()                                      # the automatic test costs money: never while PAUSED
    except Exception as x: log(f"weekly watch skipped: {scrub(x)}", "WARN")
    eps = [e for e in st.rows("Episodes") if e.get("status") in ("LIVE1", "LIVE") and e.get("yt_id")]
    old = st.rows("Analytics"); done = {a["episode_id"] for a in old}
    hist = [a for a in old if str(a.get("data_note") or "ok") == "ok" and GR._num(a.get("views")) is not None]
    rows = []
    for e in eps:
        t = parse_iso(e.get("slot_et"))
        if not t or e["episode_id"] in done or now_utc() - t < dt.timedelta(hours=72): continue
        dd = json.loads(e.get("draw_json") or "{}") if not isinstance(e.get("draw_json"), dict) else e["draw_json"]
        dur = dd.get("duration_sec") or dd.get("runtime_sec")
        m = _analytics(e["yt_id"], t, dur) if dur else _analytics(e["yt_id"], t)
        if not m or m.get("pending"):                           # v8.6: YouTube Analytics lags; missing data is retried, never invented
            if now_utc() - t > dt.timedelta(days=S("ANALYTICS_GIVEUP_DAYS", int)):
                rows.append({"episode_id": e["episode_id"], "yt_id": e["yt_id"], "pulled": iso(), "score": "", "diagnosis": "insufficient data",
                             "data_note": f"no data after {S('ANALYTICS_GIVEUP_DAYS', int)} days"})
            continue
        try: m.update(_shorts_stats(e, t))
        except Exception as x: log(f"Shorts stats skipped for {e['episode_id']}: {scrub(x)}", "WARN")
        if m.get("ctr_kind") != "real" and GR._num(m.get("views")) is not None:
            prev = [GR._num(a.get("views")) for a in (hist + rows)[-10:] if GR._num(a.get("views")) is not None]
            base = (sorted(prev)[len(prev) // 2] if prev else 0) or max(1.0, float(m["views"]))
            m["ctr"] = round(min(0.15, 0.05 * float(m["views"]) / base), 4); m["ctr_kind"] = "proxy: 72h views vs channel median"
        if m.get("ctr_kind") == "real" and GR._num(m.get("ctr")) and GR._num(m.get("avg_view_sec")):
            m["wtpi"] = round(float(m["ctr"]) * float(m["avg_view_sec"]), 3)      # v8.7: watch seconds per impression = what YouTube's own A/B test judges by
        sc = GR.dim_scores(m, hist + rows); score = GR.composite(sc)
        diag, les = GR.diagnose(dict(m, title=e.get("title"), episode_id=e["episode_id"]), hist + rows)
        m.update({"episode_id": e["episode_id"], "yt_id": e["yt_id"], "pulled": iso(), "score": "" if score is None else score,
                  "diagnosis": diag, "data_note": m.get("data_note") or "ok"}); rows.append(m)
        d = json.loads(e.get("draw_json") or "{}")
        swapped = str(_pkg(e).get("action", "")).startswith("swapped")
        if les: st.append("Lessons", [{"ts": iso(), "lesson": les, "evidence": f"{e['episode_id']} vs channel medians", "applies_to": GR.DIAG_ROUTE[diag]}])
        dl = GR.dip_lesson(m.get("curve"), d.get("beat_map"), d.get("duration_sec") or d.get("runtime_sec"), e.get("title") or e["episode_id"])      # v8.7: WHERE viewers left
        if dl: st.append("Lessons", [{"ts": iso(), "lesson": dl, "evidence": f"{e['episode_id']} retention curve", "applies_to": "holding"}])
        try:                                                     # v9.1: the whole curve mapped to beats and shot types (report only)
            from whatifs import insights as INS
            try: sh91 = json.loads(e.get("shots_json") or "[]")
            except Exception: sh91 = []
            INS.file_retention(e["episode_id"], m.get("curve"), d.get("beat_map"), sh91, d.get("duration_sec") or d.get("runtime_sec"), m.get("views"), e.get("title") or "")
        except Exception as x: log(f"retention map skipped: {scrub(x)}", "WARN")
        try: PB.credit(d.get("playbook") or {}, sc, st)       # v8.7: trial rules are credited on their own metric (missing data is never credited)
        except Exception as x: log(f"playbook credit skipped: {scrub(x)}", "WARN")
        if m.get("from_shorts") is not None:
            st.append("Lessons", [{"ts": iso(), "lesson": f"{e['episode_id']}: {m['from_shorts']} long-video views came from Shorts, Shorts gained {m.get('shorts_subs', '?')} subscribers "
                                   f"(reel style {d.get('reel_style', 'teaser')}, formats {', '.join(d.get('reel_formats', [])) or '?'})",
                                   "evidence": "YouTube Analytics (traffic source SHORTS; per-Short subscribers)", "applies_to": "reels"}])
        _credit_strategies(st, strategy_credits(d, sc, swapped))      # v8.9.1: each (dimension, name) credited once per video, matched on BOTH columns
    if rows: st.append("Analytics", rows)
    try: _reaction_learning([r for r in rows if r.get("data_note") == "ok"])
    except Exception as x: log(f"reaction learning skipped: {scrub(x)}", "WARN")
    _evolve()
    try: PB.judge(st)
    except Exception as x: log(f"playbook judging skipped: {scrub(x)}", "WARN")
    try:                                                        # v8.10: premise scores meet real CTR / retention; the premise bank is renewed monthly
        from whatifs import premise as PR
        n = PR.attach_results()
        if n: log(f"premise scores: {n} chosen premise(s) now carry their CTR / retention")
        PR.regenerate_bank()
    except Exception as x: log(f"premise learning skipped: {scrub(x)}", "WARN")
    try:                                                        # v8.11: keep the Premise_Bench stocked (only when it is low and the month can pay for it)
        from whatifs import premise as PR
        PR.refill_bench()
    except Exception as x: log(f"premise bench refill skipped: {scrub(x)}", "WARN")
    flush_log()

def v810_upgrade(st):
    """v8.10 (setup + daily learning): seed the Cast tab once, and refresh Settings notes that still describe the old ₹3,500 cap (values are never touched)."""
    from whatifs import cast as CAST
    CAST.ensure_seed(st)
    for r in st.rows("Settings"):
        k = r.get("key")
        if k in DEFAULTS and "3,500" in str(r.get("note") or "") and str(r.get("note")) != DEFAULTS[k][1]:
            try: st.update("Settings", "key", k, {"note": DEFAULTS[k][1]})
            except Exception: pass

V93_FLIPS = (("HERO_STILL_REELS_ON", "FALSE", "TRUE"), ("HERO_STILL_SHORTS_ON", "FALSE", "TRUE"))

def v93_upgrade(st):
    """v9.3 (Setup + daily learning): ONCE, switch the listed Settings cells from their OLD default to the new one, ONLY where the cell still holds the
    old default (a value the owner set is never touched). Recorded in V93_FLIPS_DONE so it never runs twice; V93_FLIPS_ON = FALSE skips it. Returns the keys changed."""
    if not S("V93_FLIPS_ON", bool) or str(S("V93_FLIPS_DONE") or "").strip(): return []
    have = {r.get("key"): str(r.get("value", "")).strip().upper() for r in st.rows("Settings")}
    done = []
    for k, old, new in V93_FLIPS:
        if k in have and have[k] == old.upper():
            set_setting(k, new); done.append(k)
    set_setting("V93_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v9.3 default flips applied once: {', '.join(done)}")
    return done

V931_FLIPS = (("THUMB_APPROVAL_FIRST_N", "8", "9999"), ("PKG_ROTATE_ON", "TRUE", "FALSE"), ("PKG_RESCUE_HOURS", "36", "72"))      # decision 5 (2026-11-07)

def v94a_upgrade(st):
    """v9.4a (K124): ONE time, the cap cells move to the owner's ₹4,700 when they hold ₹4,500 or less (an owner value above that is never touched)."""
    if not S("V94A_FLIPS_ON", bool) or str(S("V94A_FLIPS_DONE") or "").strip(): return []
    from whatifs.governor import money_num
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    done = []
    for k in ("BUDGET_FLOOR_INR", "BUDGET_CEILING_INR"):
        if k in have and 0 < money_num(have[k]) <= 4500: set_setting(k, "4700"); done.append(k)
    set_setting("V94A_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v9.4a: budget cap moved to Rs 4,700 ({', '.join(done)})")
    return done

def v931_upgrade(st):
    """v9.3.1: same owner-respecting one-time pattern as v93_upgrade (a cell changes only while it still holds the old default)."""
    if not S("V931_FLIPS_ON", bool) or str(S("V931_FLIPS_DONE") or "").strip(): return []
    have = {r.get("key"): str(r.get("value", "")).strip().upper() for r in st.rows("Settings")}
    done = []
    for k, old, new in V931_FLIPS:
        if k in have and have[k] == old.upper(): set_setting(k, new); done.append(k)
    set_setting("V931_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v9.3.1 default flips applied once: {', '.join(done)}")
    return done

V101_FLIPS = (("FAL_HERO_MODEL", "fal-ai/kling-video/v2.1/standard/image-to-video", "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"),
              ("PRICE_KLING_USD", "0.25", "0.35"), ("STILL_W", "1632", "1872"), ("STILL_H", "918", "1056"),
              ("SHORTS_WEEKLY_CAP", "14", "10"), ("HERO_STILL_SHORTS_ON", "TRUE", "FALSE"))

def v101_upgrade(st):
    """v10.1: ONE time, cells still at the old default move to the verified 8 Nov 2026 values (owner-set values never touched)."""
    if not S("V101_FLIPS_ON", bool) or str(S("V101_FLIPS_DONE") or "").strip(): return []
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    done = []
    for k, old, new in V101_FLIPS:
        if k in have and have[k].upper() == old.upper(): set_setting(k, new); done.append(k)
    set_setting("V101_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v10.1: settings moved to verified values ({', '.join(done)})")
    return done

V11_KEEP_FLIP = ("DRIVE_ARCHIVE_KEEP", "2", "12")
V111_FLIPS = (("REHOOK_MAX_GAP_SEC", "90", "75"),)          # v11.1: research - re-hook at most every 75 s (now a hard contract check)

# Owner decision 10 Nov 2026: the launch cadence is 4 long videos a month, one a week (Shorts and spin-offs carry the volume).
V12_FLIPS = (("STANDARD_MAX_LONG_PER_MONTH", "8", "4"), ("PUBLISH_DAYS", "Tue,Sat", "Sat"), ("VIDEOS_PER_MONTH_EST", "9", "4"))

def v12_upgrade(st):
    """ONE time: cells still at the old defaults move to the owner's cadence (4 long videos a month, weekly). A value the owner typed is never touched."""
    if str(S("V12_FLIPS_DONE") or "").strip(): return []
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    done = []
    for k, old, new in V12_FLIPS:
        if have.get(k) == old: set_setting(k, new); done.append(k)
    set_setting("V12_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log("v12: launch cadence set (4 long videos a month, one a week): " + ", ".join(done))
    return done

V102_FLIPS = (("FAL_HERO_MODEL", "fal-ai/kling-video/v2.5-turbo/pro/image-to-video", "fal-ai/kling-video/o3/standard/image-to-video"),
              ("PRICE_KLING_USD", "0.35", "0.42"), ("KLING_CLIPS", "3", "4"), ("SPECIAL_REEL_CAP_INR", "150", "180"),
              ("KLING_MIN_CLIPS", "3", "4"), ("WA_GRAPH_VERSION", "v21.0", "v27.0"))

def _designed_voices_ok():
    """True when TTS is Gemini and every core character's designed voice is listed and synthesised OK in Voice_Check."""
    try:
        if str(S("TTS_ENGINE") or "").lower() != "gemini": return False
        from whatifs import show as SHOW
        chars = {r.get("id"): str(r.get("gvoice") or "").strip() for r in store().rows("Characters")}
        need = [chars.get(c["id"]) for c in SHOW.CHARACTERS if c["id"] in ("VALE", "GRIMM", "ROSA", "ARCHIVIST")]
        if not need or not all(need): return False
        vc = store().rows("Voice_Check")
        ok = {}
        for r in vc:                                             # Voice_Check: voice, source, listed, synth_ok (the latest row per voice wins)
            ok[str(r.get("voice") or "").strip()] = str(r.get("synth_ok")).upper() == "TRUE"
        return all(ok.get(v) for v in need)
    except Exception: return False

def v11_upgrade(st, now=None):
    """v11: ONE time. Writes the owner's November allowance (2026-11=5226) when the month is still November 2026 and the cell is empty."""
    if str(S("V11_FLIPS_DONE") or "").strip(): return []
    now = now or now_utc(); done = []
    if now.strftime("%Y-%m") == "2026-11" and not str(S("MONTH_CAP_OVERRIDES") or "").strip():
        set_setting("MONTH_CAP_OVERRIDES", "2026-11=5226"); done.append("MONTH_CAP_OVERRIDES")
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    k, old, new = V11_KEEP_FLIP
    if have.get(k) == old: set_setting(k, new); done.append(k)          # Case Files needs past masters (owner's Drive has room)
    for k, old, new in V111_FLIPS:
        if have.get(k) == old: set_setting(k, new); done.append(k)
    bad, good = "fal-ai/kling-video/v3/standard/image-to-video", "fal-ai/kling-video/o3/standard/image-to-video"
    if have.get("FAL_HERO_MODEL") == bad: set_setting("FAL_HERO_MODEL", good); done.append("FAL_HERO_MODEL")   # v11 fix: v10.2 named an endpoint fal does not list
    lad = have.get("MODEL_LADDERS") or ""
    if bad in lad: set_setting("MODEL_LADDERS", lad.replace(bad, good)); done.append("MODEL_LADDERS")
    set_setting("V11_FLIPS_DONE", iso(now) + " " + (",".join(done) or "none"))
    if done: log("v11: November allowance set (Rs 1,226 spent + Rs 4,000 for the rest of the month)")
    return done

def v102_upgrade(st):
    """v10.2: ONE time; cells still at the v10.1 defaults move to the option-C animation stack (owner-set values never touched)."""
    if not S("V102_FLIPS_ON", bool) or str(S("V102_FLIPS_DONE") or "").strip(): return []
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    done = []
    for k, old, new in V102_FLIPS:
        if k in have and have[k] == old: set_setting(k, new); done.append(k)
    lad = have.get("MODEL_LADDERS", "")
    if lad and "kling-video/o3/standard" not in lad:
        try:
            L = json.loads(lad); L["hero"] = [{"id": "fal-ai/kling-video/o3/standard/image-to-video", "usd": 0.42}] + [e for e in L.get("hero", []) if "v3/standard" not in e.get("id", "")]
            set_setting("MODEL_LADDERS", json.dumps(L)); done.append("MODEL_LADDERS")
        except Exception: pass
    set_setting("V102_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v10.2: animation stack settings moved ({', '.join(done)})")
    return done

def v10_upgrade(st):
    """v10 (K134): ONE time, the cap cells move to ₹5,000 (owner approved +₹300 for special reels) when they hold ₹4,700 or less."""
    if not S("V10_FLIPS_ON", bool) or str(S("V10_FLIPS_DONE") or "").strip(): return []
    from whatifs.governor import money_num
    have = {r.get("key"): str(r.get("value", "")).strip() for r in st.rows("Settings")}
    done = []
    for k in ("BUDGET_FLOOR_INR", "BUDGET_CEILING_INR"):
        if k in have and 0 < money_num(have[k]) <= 4700: set_setting(k, "5000"); done.append(k)
    set_setting("V10_FLIPS_DONE", iso() + " " + (",".join(done) or "none"))
    if done: log(f"v10: budget cap moved to Rs 5,000 ({', '.join(done)})")
    return done

def strategy_credits(d, sc, swapped=False):
    """{(dimension, name): score} for one analysed video. v8.9.1: built first and de-duplicated, so a strategy is credited at most once per video
    (a reel format listed twice, or named both in the draw and in reel_formats, used to be counted twice)."""
    out = {}
    for dim, name in (d.get("strategies") or {}).items():
        if not name or (swapped and dim in ("title", "thumb")): continue      # v8.5: the measured result belongs to the runner-up package
        v = GR.score_for(dim, sc)                                            # v8.6: each dimension is judged on the metric it can move
        if v is not None: out[(dim, name)] = v                               # missing data never counts as a play
    if sc.get("shorts") is not None:                                         # v8.6: every reel format used is credited with the Shorts result
        for name in dict.fromkeys(d.get("reel_formats") or []):
            if name: out.setdefault(("reel", name), sc["shorts"])
    return out

def _credit_strategies(st, credits):
    """Apply the credits with FRESH values (re-read once) and an update matched on dimension AND name (v8.9.1: matching on the name alone could
    update another dimension's row that shares the name)."""
    if not credits: return 0
    cur = {(r.get("dimension"), r.get("name")): r for r in st.rows("Strategies")}; n = 0
    for (dim, name), v in credits.items():
        r = cur.get((dim, name))
        if not r: continue
        st.update_where("Strategies", {"dimension": dim, "name": name}, {"plays": int(float(r.get("plays") or 0)) + 1,
                        "score_sum": round(float(r.get("score_sum") or 0) + v, 4), "score_n": int(float(r.get("score_n") or 0)) + 1}); n += 1
    return n

def _top_up(st):
    """v8.7: an older Sheet gets the strategies and playbook rules introduced by newer versions (no manual Setup run needed)."""
    try:
        from whatifs.data import strategy_rows
        have = {r["name"] for r in st.rows("Strategies")}; new = [r for r in strategy_rows() if r["name"] not in have]
        if have and new: st.append("Strategies", new); log(f"{len(new)} new strategy option(s) added to the Strategies tab")
    except Exception as x: log(f"strategy top-up skipped: {scrub(x)}", "WARN")
    PB.ensure_seed(st)

_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

def _shorts_stats(e, t):
    """v8.6: views and subscribers gained by this video's own Shorts (reel1..reel4), summed. Only real Short ids are read; nothing is invented."""
    ids = [str(e.get(f"reel{k}_yt") or "").strip() for k in range(1, 5)]
    if FAKE:
        r = random.Random(e.get("yt_id")); return {"shorts_views": r.randint(500, 20000), "shorts_subs": r.randint(0, 40)}
    ids = [i for i in ids if _YT_ID.match(i)]
    if not ids: return {}
    v = s_ = 0; got = False
    for vid in ids:
        p = {"ids": "channel==MINE", "startDate": t.strftime("%Y-%m-%d"), "endDate": now_utc().strftime("%Y-%m-%d"), "filters": f"video=={vid}", "metrics": "views,subscribersGained"}
        a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=p, timeout=30).json()
        if a.get("rows"): v += float(a["rows"][0][0]); s_ += float(a["rows"][0][1]); got = True
    return {"shorts_views": int(v), "shorts_subs": int(s_)} if got else {}

def _fetch_some(ep_id, assets, names):
    """v8.5: download only the named release files (not the reels) from the private Drive. Returns {name: local path} for those that exist."""
    d = os.path.join(WORK, ep_id); os.makedirs(d, exist_ok=True); out = {}
    try: ids = assets if isinstance(assets, dict) else json.loads(assets or "{}")
    except Exception: ids = {}
    for n in names:
        p = os.path.join(d, n)
        if not os.path.exists(p) and ids.get(n):
            try: PUB.drive_download(ids[n], p)
            except Exception as x: log(f"could not fetch {n}: {scrub(x)}", "WARN")
        if os.path.exists(p): out[n] = p
    return out

def _pkg(e):
    try: return json.loads(e.get("pkg_check") or "{}") if not isinstance(e.get("pkg_check"), dict) else e["pkg_check"]
    except Exception: return {}

def pkg_rescue(now=None):
    """v8.5 packaging rescue (daily, from the learning job). Once per video, at about PKG_RESCUE_HOURS old, its view PACE (views per hour since the slot) is compared
    with the median pace of earlier videos measured the same way. Clearly behind (below PKG_RESCUE_RATIO) = the title and thumbnail are swapped ONCE to the
    Packager's runner-up (2nd title + the B thumbnail made with the video). No history, a missing runner-up or an unreadable count = no swap, never a guess.
    Results go to the Episodes 'pkg_check' cell and, for a swap, to Lessons (private), so the Packager learns which promise failed."""
    if not S("PKG_RESCUE_ON", bool): return []
    st = store(); eps = st.rows("Episodes"); now = now or now_utc(); done = []
    if eps and "pkg_check" not in eps[0]: log("packaging rescue waits: the Sheet does not have the v8.5 columns yet (the daily learning job adds them by itself)", "WARN"); return []
    hrs = S("PKG_RESCUE_HOURS", float)
    def _src(c): return c.get("src") or "views"
    allhist = [(float(c["pace"]), _src(c)) for c in (_pkg(e) for e in eps) if c.get("pace") is not None]
    for e in eps:
        if e.get("status") not in ("LIVE1", "LIVE") or not e.get("yt_id") or str(e.get("pkg_check") or "").strip(): continue
        t = parse_iso(e.get("slot_et"))
        if not t: continue
        age = (now - t).total_seconds() / 3600
        if age < hrs: continue
        if age > hrs + 48:                                         # too old to compare fairly (e.g. published before v8.5): recorded, never swapped
            st.update("Episodes", "episode_id", e["episode_id"], {"pkg_check": {"action": "not checked: too old for a fair comparison"}}); continue
        v, src = _rescue_views(e["yt_id"], t)                       # v9.3.1 (L5): engaged views first (public views count autoplay since 2026-08-24)
        if v is None: continue                                     # try again tomorrow (still inside the window)
        hist = [p for p, s in allhist if s == src]                 # compare like with like (engaged vs engaged, public vs public)
        pace = v / max(1.0, age); rec = {"views": v, "src": src, "age_h": round(age, 1), "pace": round(pace, 3), "at": iso()}
        need = max(1, S("PKG_RESCUE_MIN_HISTORY", int))
        if len(hist) < need: rec["action"] = f"kept: only {len(hist)} earlier videos measured (needs {need})"
        else:
            med = statistics.median(hist); ratio = pace / med if med > 0 else 1.0
            rec.update(median_pace=round(med, 3), ratio=round(ratio, 2))
            recent = hist[-3:]
            if ratio >= S("PKG_RESCUE_RATIO", float): rec["action"] = "kept: on pace"
            elif S("PKG_DIP_GUARD_ON", bool) and len(recent) == 3 and all(p < S("PKG_RESCUE_RATIO", float) * med for p in recent):
                rec["action"] = "kept: channel-wide dip (the last 3 videos were all behind too), not a packaging problem"
            else: rec["action"] = _swap(st, e, rec)
        allhist.append((pace, src))
        st.update("Episodes", "episode_id", e["episode_id"], {"pkg_check": rec, "updated": iso()}); done.append((e["episode_id"], rec["action"]))
        log(f"packaging check {e['episode_id']}: {rec['action']} (pace {rec.get('ratio', '-')}x the median)", public=f"packaging check {e['episode_id']}: {rec['action'].split(':')[0]}")
    try: done += _judge_swaps(st, now)
    except Exception as x: log(f"swap evaluation skipped: {scrub(x)}", "WARN")
    return done

def _rescue_views(vid, since, want=None):
    """v9.3.1 (L5): (count, source). Engaged views from Analytics when PKG_RESCUE_ENGAGED_ON and available, else the public count.
    want = force one source (a swap is judged with the same source it was measured with)."""
    if want != "views" and S("PKG_RESCUE_ENGAGED_ON", bool):
        ev = PUB.yt_engaged_views(vid, (since or now_utc()).strftime("%Y-%m-%d"))
        if ev is not None: return ev, "engaged"
        if want == "engaged": return None, "engaged"
    return PUB.yt_views(vid), "views"

def _judge_swaps(st, now):
    """v8.6: a swap is judged once, at least a day later: views per hour SINCE the swap vs the pace before it. Views normally slow down with age, so a higher
    pace after the swap is a real sign it helped ('helped'); anything else is recorded as 'unclear' (never called a failure, because age alone lowers the pace)."""
    out = []
    for e in st.rows("Episodes"):
        rec = _pkg(e)
        if not str(rec.get("action", "")).startswith("swapped") or "after" in rec or not e.get("yt_id"): continue
        t = parse_iso(rec.get("at"))
        if not t or now - t < dt.timedelta(hours=24): continue
        v, _s = _rescue_views(e["yt_id"], parse_iso(e.get("slot_et")) or t, rec.get("src") or "views")
        if v is None: continue
        hrs = (now - t).total_seconds() / 3600; after = max(0.0, (v - float(rec.get("views") or 0)) / max(1.0, hrs))
        rec["after"] = {"views": v, "pace": round(after, 3), "hours": round(hrs, 1), "verdict": "helped" if after > float(rec.get("pace") or 0) else "unclear"}
        st.update("Episodes", "episode_id", e["episode_id"], {"pkg_check": rec, "updated": iso()}); out.append((e["episode_id"], "judged: " + rec["after"]["verdict"]))
        if rec["after"]["verdict"] == "helped":
            st.append("Lessons", [{"ts": iso(), "lesson": f"packaging: the runner-up package lifted '{e.get('title', '')}' from {rec.get('pace')} to {after:.2f} views/hour; "
                                   "the first package had undersold it", "evidence": "pkg_check before/after", "applies_to": "packaging"}])
    return out

def _swap(st, e, rec):
    got = _fetch_some(e["episode_id"], e.get("assets"), ["release.json", "thumb_b.jpg"])
    try: rel = json.load(open(got["release.json"])) if "release.json" in got else {}
    except Exception: rel = {}
    title_b = str(rel.get("title_b") or "").strip(); thumb_b = got.get("thumb_b.jpg") if rel.get("thumb_b") else None
    if not title_b and not thumb_b: return "kept: behind pace but no runner-up package was made"
    changed = []
    if title_b and PUB.yt_set_title(e["yt_id"], title_b): changed.append("title")
    if thumb_b and PUB.yt_thumbnail(e["yt_id"], thumb_b): changed.append("thumbnail")
    if not changed: return "kept: behind pace but the swap was refused by YouTube (see Run_Log)"
    old = e.get("title", "")
    upd = {"notes": _note(e, "packaging swapped to the runner-up (" + " + ".join(changed) + ")")}
    if "title" in changed: upd["title"] = title_b
    st.update("Episodes", "episode_id", e["episode_id"], upd)
    st.append("Lessons", [{"ts": iso(), "lesson": f"packaging: '{old}' ran at {rec.get('ratio')}x the usual pace at {rec['age_h']} h; swapped to "
                           + (f"'{title_b}'" if "title" in changed else "the same title") + (" + the B thumbnail" if "thumbnail" in changed else ""),
                           "evidence": f"{rec['views']} views at {rec['age_h']} h, median pace {rec.get('median_pace')}", "applies_to": "title"}])
    return "swapped " + " + ".join(changed)

def _reaction_learning(rows):
    """v8.3: for each analysed video, compare how many viewers stayed just before vs just after each reaction moment, per kind, and write it to Lessons."""
    from whatifs import reactions as RX
    st = store(); rmap = st.rows("Reaction_Map")
    for m in rows:
        curve = m.get("curve") or []
        ev = [r for r in rmap if r.get("episode_id") == m["episode_id"]]
        if not ev or len(curve) < 20: continue
        try: total = float(ev[0].get("total_sec") or 0)
        except Exception: total = 0.0
        for les in RX.reaction_lessons(curve, [{"t": float(r["t"]), "kind": r["kind"]} for r in ev], total, label=f"{m['episode_id']}: "):
            st.append("Lessons", [{"ts": iso(), "lesson": les, "evidence": f"{len(ev)} reactions", "applies_to": "reactions"}])

def _analytics(vid, t, dur=None):
    if FAKE:
        r = random.Random(vid); vv = r.randint(200, 9000)
        return {"views": vv, "engaged_views": int(vv * r.uniform(0.45, 0.8)), "avg_view_pct": r.uniform(25, 55), "avg_view_sec": r.uniform(120, 330), "ret30": r.uniform(0.5, 0.8),
                                        "ctr": 0.0, "ctr_kind": "proxy", "likes": 10, "shares": 2, "subs": 3, "from_shorts": r.randint(0, 150)}
    try:
        p = {"ids": "channel==MINE", "startDate": t.strftime("%Y-%m-%d"), "endDate": now_utc().strftime("%Y-%m-%d"), "filters": f"video=={vid}",
             "metrics": "views,averageViewPercentage,averageViewDuration,likes,shares,subscribersGained,engagedViews"}      # v11: engaged views = the 'stayed' signal
        a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=p, timeout=30).json()
        if a.get("error"): log(f"analytics error for {vid}: {str(a['error'])[:200]}", "WARN"); return None
        if not a.get("rows"): return {"pending": True}               # v8.6: no rows yet (Analytics lags); never recorded as 0 views
        row = a["rows"][0]
        rp = dict(p, metrics="audienceWatchRatio", dimensions="elapsedVideoTimeRatio")
        ret = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=rp, timeout=30).json().get("rows", [])
        cut = min(0.5, 30.0 / float(dur)) if dur and float(dur) > 60 else 0.05      # v8.7: exactly 30 s when the video's length is known (YouTube's Intro moment)
        ret30 = next((r[1] for r in ret if r[0] >= cut), None)    # v8.6: no curve = unknown (was a made-up 0.6)
        from_shorts = None
        try:                                                     # v8.5: how many long-video views arrived from our Shorts (traffic source SHORTS)
            tp = dict(p, metrics="views", dimensions="insightTrafficSourceType")
            tr = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=tp, timeout=30).json()
            if "rows" in tr: from_shorts = int(sum(float(r[1]) for r in tr["rows"] if str(r[0]).upper() == "SHORTS"))
        except Exception: pass
        ctr, kind, imp = 0.0, "proxy", None
        try:          # v8.7: impressions too, so the CTR unit can be checked (percentage vs ratio) instead of assumed
            cp = dict(p, metrics="videoThumbnailImpressions,videoThumbnailImpressionsClickRate"); cr = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=cp, timeout=30).json()
            r0 = cr["rows"][0]; imp = float(r0[0]) if len(r0) > 1 else None
            c = GR.ctr_ratio(r0[-1], imp, row[0])
            if c is not None: ctr = c; kind = "real"
        except Exception: pass
        rel30 = rel_avg = None
        try:          # v8.7: retention compared with ALL YouTube videos of similar length (0.5 = typical): a benchmark from the very first video
            rr = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=gheaders(), params=dict(p, metrics="relativeRetentionPerformance", dimensions="elapsedVideoTimeRatio"), timeout=30).json().get("rows", [])
            if rr:
                rel30 = next((float(r[1]) for r in rr if float(r[0]) >= cut), None); rel_avg = round(sum(float(r[1]) for r in rr) / len(rr), 4)
        except Exception: pass
        return {"ctr_kind": kind, "views": row[0], "avg_view_pct": row[1], "avg_view_sec": row[2], "likes": row[3], "shares": row[4], "subs": row[5],
                "engaged_views": row[6] if len(row) > 6 else None, "ret30": None if ret30 is None else float(ret30), "ctr": ctr if kind == "real" else None, "from_shorts": from_shorts,
                "impressions": imp, "rel30": rel30, "rel_avg": rel_avg,
                "curve": [(float(r[0]), float(r[1])) for r in ret if len(r) > 1]}
    except Exception as e: log(f"analytics failed for {vid}: {e}", "WARN"); return None

def _evolve():
    """Cut a clearly weak strategy (>=5 plays, mean < pool mean - 0.08) and invent a replacement (the number of active strategies never drops).
    v8.6: first judge earlier replacements (rolled back once if worse), log every change in Strategy_Log, never re-retire a strategy restored in the last 30 days."""
    try:
        for new_name, old_name in GR.rollbacks(): log(f"strategy rollback: {new_name} -> {old_name}")
    except Exception as x: log(f"strategy rollback check skipped: {scrub(x)}", "WARN")
    st = store(); rows = st.rows("Strategies")
    rules = [r["item"] for r in st.rows("Trend_Brief") if r["kind"] == "rule"][-8:]
    for dim in {r["dimension"] for r in rows}:
        act = [r for r in rows if r["dimension"] == dim and r["status"] == "ACTIVE"]
        scored = [r for r in act if float(r.get("score_n") or 0) >= 5]
        if len(scored) < 3: continue
        means = {r["name"]: float(r["score_sum"]) / float(r["score_n"]) for r in scored}
        pool = statistics.mean(means.values()); worst = min(means, key=means.get)
        if means[worst] < pool - 0.08 and not GR.recently_restored(worst):
            st.update_where("Strategies", {"dimension": dim, "name": worst}, {"status": "RETIRED"})
            best = sorted(means, key=means.get, reverse=True)[:2]
            try:
                new = ask("strategy", P.fill(P.STRATEGY_NEW, dim=dim, best=json.dumps({b: next(r["definition"] for r in act if r["name"] == b) for b in best}),
                          rules=json.dumps(rules), names=[r["name"] for r in rows if r["dimension"] == dim]), "Invent now.", fake_key="strategy")
                nm = re.sub(r"[^A-Za-z0-9_]+", "_", str(new.get("name") or "")).strip("_")[:40]
                if nm and nm in {r["name"] for r in rows}: nm = (nm[:30] + "_" + dim)[:40]      # v8.9.1: names stay unique across ALL dimensions
                if nm and new.get("definition") and nm not in {r["name"] for r in rows}:
                    new["name"] = nm
                    st.append("Strategies", [{"dimension": dim, "name": new["name"][:40], "definition": new["definition"][:400], "status": "ACTIVE",
                                              "plays": 0, "score_sum": 0, "score_n": 0, "created": iso(), "source": "learned"}])
                    st.append("Lessons", [{"ts": iso(), "lesson": f"{dim}: retired {worst}, added {new['name']}", "evidence": json.dumps(means), "applies_to": dim}])
                    GR.log_change(dim, "retired", worst, "", round(means[worst], 4), f"mean {means[worst]:.3f} < pool {pool:.3f} - 0.08")
                    GR.log_change(dim, "invented", new["name"][:40], worst, round(means[worst], 4), "judged after STRATEGY_EVAL_PLAYS plays")
                else:          # v8.9.1 (fix): an empty or clashing invention used to leave the weak strategy retired with no replacement (the pool shrank, K19)
                    st.update_where("Strategies", {"dimension": dim, "name": worst}, {"status": "ACTIVE"}); log(f"no usable new {dim} strategy - kept {worst}", "WARN")
            except Exception as e:
                st.update_where("Strategies", {"dimension": dim, "name": worst}, {"status": "ACTIVE"}); log(f"evolve failed, kept {worst}: {e}", "WARN")

# ---------------- money ----------------
def failure_watch():
    """One email if 3 episodes in a row failed (repair bot may be capped). Never more than once per 3 days."""
    eps = store().rows("Episodes")[-3:]
    if len(eps) == 3 and all(e.get("status") == "FAILED" for e in eps):
        last = parse_iso(S("FAIL_MAIL_AT")) if "FAIL_MAIL_AT" in settings_keys() else None
        if not last or now_utc() - last > dt.timedelta(days=3):
            PUB.email("Needs a look (3 failed tries)", "<p>The last 3 episode attempts failed. Reasons:</p><ul>" +
                      "".join(f"<li>{e.get('notes','')[:200]}</li>" for e in eps) +
                      "</ul><p>Paste the Run_Log tab into your Claude setup chat: it will tell you whether it is an account/key issue (fix by clicking) or a code issue (a separate Claude code chat). Publishing retries hourly.</p>")
            set_setting("FAIL_MAIL_AT", iso())

def settings_keys():
    return {r["key"] for r in store().rows("Settings")}

def money_check():
    JOB["name"] = "money"; msgs = []
    failure_watch()
    try:                                                         # v9: 70 % / 90 % spend warnings and the weekly estimate-vs-measured email
        from whatifs import costguard as CG
        CG.spend_monitor(); CG.weekly_deviation_mail()
    except Exception as x: log(f"cost monitor skipped: {scrub(x)}", "WARN")
    try:                                                         # v8.10: prepaid Gemini credit (TTS + writing + checks) and the monthly headroom view
        left = G.gemini_left_usd()
        if left is not None and left < S("GEMINI_LOW_USD", float):
            msgs.append(f"<li><b>Gemini</b>: about ${left:.2f} of prepaid credit left. <a href='https://aistudio.google.com/usage'>Top up here</a>, then add the amount to the "
                        "GEMINI_FUNDED_USD cell. If it runs out, narration falls back to the Kokoro voices and checks to Claude.</li>")
        prop = G.kling4_proposal(); mk = now_utc().strftime("%Y-%m")
        if prop and S("KLING4_MAIL_MONTH") != mk:
            h = G.headroom(); set_setting("KLING4_MAIL_MONTH", mk)
            PUB.email("Budget headroom: room for a 4th Kling clip", f"<p>Spent Rs {h['spent_inr']:.0f} of Rs {h['cap_inr']:.0f}; a full video costs about Rs {h['per_video_inr']:.0f} "
                      f"(TTS and thinking included).</p><p>{prop}</p>")
    except Exception as x: log(f"headroom / Gemini credit check skipped: {scrub(x)}", "WARN")
    if S("GREENLIGHT_TIERS_ON", bool):                           # v9: report only - measured savings vs the estimate over the last videos
        try:
            from whatifs.models import ai_estimate_inr
            sm = [r for r in store().rows("Cost_Log") if r.get("item") == "ai_per_video_summary"][-6:]
            sav = sum(max(0.0, float(r.get("est_inr") or 0) - float(r.get("measured_inr") or 0)) for r in sm)
            if sav > 0: msgs.append(f"<li><b>Greenlight</b>: the last {len(sm)} videos came in Rs {sav:.0f} under their AI estimate; that measured saving could fund an upgraded tier (nothing changes by itself).</li>")
        except Exception as x: log(f"greenlight report skipped: {scrub(x)}", "WARN")
    if S("AUTO_RELOAD_ON", bool):
        if msgs: PUB.email("Top-up reminder", "<ul>" + "".join(msgs) + "</ul>")
        return
    for prov, url, name in (("fal", "https://fal.ai/dashboard/billing", "fal.ai"), ("anthropic", "https://platform.claude.com/settings/billing", "Anthropic")):
        days = G.runway_days(prov)
        if days <= S("REFILL_WARN_DAYS", int):
            msgs.append(f"<li><b>{name}</b>: about {days:.0f} days left. <a href='{url}'>Top up here</a>, then add the amount to the {prov.upper() if prov=='fal' else 'ANTHROPIC'}_FUNDED_USD cell (or switch on auto-reload and set AUTO_RELOAD_ON to TRUE).</li>")
    if msgs: PUB.email("Top-up reminder", "<ul>" + "".join(msgs) + "</ul><p>If you do nothing: videos already scheduled still publish, but NO new video can be made once fal.ai credit or Anthropic credit runs out (pictures have no free fallback; writing falls back to Gemini).</p>")

def monthly_brief():
    JOB["name"] = "brief"; st = store()
    rev = [dict(r, month=G.month_key(r.get("month")) or r.get("month"), inr_received=G.money_num(r.get("inr_received"))) for r in st.rows("Revenue_Log")[-3:]]
    data = {"analytics": st.rows("Analytics")[-15:], "spend_month": month_spend(), "cap": G.cap_inr(), "revenue": rev,
            "lessons": st.rows("Lessons")[-10:], "trends": [r["item"] for r in st.rows("Trend_Brief")[-15:]]}
    try:                                                        # v9: the experiments and the season feed the brief (recommendations only)
        data["experiments"] = st.rows("Experiments")[-8:]; data["season"] = st.rows("Season")[-8:]
        from whatifs import insights as INS                     # v9.1: role ROI and the retention map (report only)
        data["role_roi"] = INS.roi_summary(); data["retention_map"] = [r for r in st.rows("Retention_Map") if r.get("confidence") in ("high", "medium")][-30:]
    except Exception: pass
    from whatifs.models import ask_batch
    txt = ask_batch("brief", P.fill(P.BRIEF, data=json.dumps(data, default=str)[:20000]) + ("\nEnd with ONE priority fix for next month (the single change most "
              "likely to raise click-through or retention, with the evidence), then a short list of other ideas. Recommend only: budget and visuals are never changed automatically."),
              "Write it.", want_json=False, fake_key="brief")
    PUB.email("Monthly brief", "<pre style='font-family:sans-serif;white-space:pre-wrap'>" + txt + "</pre>")

# ---------------- setup ----------------
def setup():
    JOB["name"] = "setup"; st = store()
    st.ensure_tabs()
    for tab, col in (("Revenue_Log", 0), ("Revenue_Log", 2), ("Settings", 1)):
        try: st.plain_text(tab, col)      # typed '2027-03' / '10:00' stay text, not dates
        except Exception as e: log(f"plain-text format for {tab} skipped: {scrub(e)}", "WARN")
    have = {r["key"] for r in st.rows("Settings")}
    st.append("Settings", [{"key": k, "value": v[0], "note": v[1]} for k, v in DEFAULTS.items() if k not in have])
    if env("OWNER_EMAIL") and not S("OPERATOR_EMAIL"): set_setting("OPERATOR_EMAIL", env("OWNER_EMAIL"))
    from whatifs.data import premise_rows, BANNED, strategy_rows
    if not st.rows("Premises"): st.append("Premises", premise_rows())
    if not st.rows("Banned"): st.append("Banned", [{"phrase": p, "reason": r} for p, r in BANNED])
    have_s = {r["name"] for r in st.rows("Strategies")}       # v8.2: also adds strategies introduced by newer versions (banter styles, reel formats) to an older Sheet
    new_s = [r for r in strategy_rows() if r["name"] not in have_s]
    if new_s: st.append("Strategies", new_s)
    PB.ensure_seed(st)                                         # v8.7: the research-graded playbook starts with its seed rules
    from whatifs import show as SHOW
    SHOW.seed_characters(st)                                   # v9: the character bible (idempotent)
    try:                                                       # v9.2: an empty bench is filled here once (normal calls), so the first preview does not wait
        from whatifs import premise as PR
        if S("SETUP_FILLS_BENCH", bool) and S("PREMISE_BENCH_ON", bool) and not PR.bench_rows(): PR.refill_bench(force=True)
    except Exception as x: log(f"first bench fill skipped: {scrub(x)}", "WARN")
    v810_upgrade(st)                                           # v8.10: Cast placeholders (owner overwrites), settings notes with the ₹4,000 cap
    try: v93_upgrade(st)                                       # v9.3: one-time default flips (owner values never touched)
    except Exception as x: log(f"v9.3 default flips skipped: {scrub(x)}", "WARN")
    try: v931_upgrade(st)                                      # v9.3.1
    except Exception as x: log(f"v9.3.1 default flips skipped: {scrub(x)}", "WARN")
    try: v94a_upgrade(st)                                      # v9.4a: the ₹4,700 cap
    except Exception as x: log(f"v9.4a cap move skipped: {scrub(x)}", "WARN")
    try: v10_upgrade(st)                                       # v10: ₹5,000 (specials)
    except Exception as x: log(f"v10 cap move skipped: {scrub(x)}", "WARN")
    try: v101_upgrade(st)                                      # v10.1: verified models, still size, Shorts cap
    except Exception as x: log(f"v10.1 flips skipped: {scrub(x)}", "WARN")
    try: v102_upgrade(st)                                      # v10.2: Kling 3.0, 4 animated scenes
    except Exception as x: log(f"v10.2 flips skipped: {scrub(x)}", "WARN")
    try: v11_upgrade(st)                                       # v11: the owner's November allowance
    except Exception as x: log(f"v11 flips skipped: {scrub(x)}", "WARN")
    try: v12_upgrade(st)                                         # v12: the owner's cadence (4 long videos a month, weekly)
    except Exception as x: log(f"v12 flips skipped: {scrub(x)}", "WARN")
    try:                                                         # v12: the founding knowledge is in the Palace from the first run
        from whatifs.org import palace as PAL, runner as ORGR; PAL.maintain(st); ORGR.install(st)
    except Exception as x: log(f"palace seed skipped: {scrub(x)}", "WARN")
    status("sheet_ready", True, f"{len(TABS)} tabs")
    from whatifs import launch as LA                                      # v9.3.1: the audit is only needed when the upload check found a lock
    status("youtube_api_audit", audit_state() == "approved" or LA.lock_state() != "on", AUDIT_WORDS[audit_state()] if LA.lock_state() == "on" else "not needed: YouTube lifted the private lock on 2 Nov 2026 (the upload check confirms it on this project)")      # v8.4: the audit form has its own Setup_Status row, so it cannot be forgotten
    if not FAKE:
        from whatifs.models import selftest
        selftest()
        try:
            ch = PUB.yt_channel(); status("youtube_connected", bool(ch.get("id")), ch.get("snippet", {}).get("title", ""))
            lv = ch.get("status", {}).get("longUploadsStatus", "")
            status("youtube_phone_verified", lv in ("allowed", "eligible"), lv or "unknown - verify at youtube.com/verify")
        except Exception as e: status("youtube_connected", False, str(e)[:300])
        try:
            r = requests.get("https://api.anthropic.com/v1/models", headers={"x-api-key": env("ANTHROPIC_KEY"), "anthropic-version": "2023-06-01"}, timeout=20)
            status("anthropic_key", r.status_code == 200, r.status_code)
        except Exception as e: status("anthropic_key", False, str(e))
        try:
            from whatifs.media import still
            p, u = still("a small blue marble on black velvet", "fal_test.jpg", "setup", seed="t", w=256, h=256)
            status("fal_works", os.path.exists(p), "test image made")
        except Exception as e: status("fal_works", False, str(e)[:300])
        if S("META_ON", bool): _meta_ids()
        status("pexels_key", bool(env("PEXELS_KEY")), "optional")
        if str(S("TTS_ENGINE")).strip().lower() == "gemini":   # v8.10: which cast voices this key can really use (about Rs 0.1)
            try:
                from whatifs.tts_gemini import voice_check, tts_model
                okn, tot, probs = voice_check(); status("gemini_tts_voices", okn == tot and tot > 0, f"model {tts_model()}: {okn}/{tot} cast voices work" + (f"; {'; '.join(probs[:3])}" if probs else ""))
            except Exception as e: status("gemini_tts_voices", False, str(e)[:300])
    flush_log()

def _meta_ids():
    try:
        k = env("META_PAGE_KEY"); GV = PUB.gv()
        me = requests.get(GV + "me", headers={"Authorization": "Bearer " + k}, params={"fields": "id,name,instagram_business_account"}, timeout=30).json()
        if "id" in me: set_setting("FB_PAGE_ID", me["id"])
        ig = (me.get("instagram_business_account") or {}).get("id")
        if ig: set_setting("IG_USER_ID", ig)
        status("meta_connected", bool(me.get("id") and ig), json.dumps({"page": me.get("name"), "ig": ig, "graph": PUB.graph_version()}))
        try:   # v7.3: posts from an app in Development mode are seen only by the app's own team
            app = requests.get(GV + "app", headers={"Authorization": "Bearer " + k}, timeout=30).json()
            live = requests.get(GV + str(app.get("id", "")), headers={"Authorization": "Bearer " + k}, params={"fields": "name,app_mode"}, timeout=30).json() if app.get("id") else {}
            mode = str(live.get("app_mode") or "").lower()
            if mode: status("meta_app_live", mode == "live", mode + (" - switch the app to Live (SETUP_CHECKLIST Step 8.8)" if mode != "live" else ""))
            else: status("meta_app_live", True, "informational: a Page token cannot read App Mode; check once in developers.facebook.com that the app is Published/Live")
        except Exception as e: status("meta_app_live", True, "informational: App Mode not readable with a Page token (" + str(e)[:120] + "); check the Meta dashboard once")
    except Exception as e: status("meta_connected", False, str(e)[:300])

