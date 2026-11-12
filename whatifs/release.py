"""The release sheet (Publishing, D9): every setting of every platform as data - who sets it, what it must be, how it is proven - one master file sent natively to YouTube Shorts, Instagram Reels and Facebook Reels, and a receipt for every row read back from the platform. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, os, re, time
from whatifs.core import S, log, store, iso, now_utc, parse_iso, FAKE, WORK, SMALL, scrub

TAB = "Release_Sheet"
PLATFORMS = ("youtube", "instagram", "facebook")
NAMES = {"youtube": "YouTube Shorts", "instagram": "Instagram Reels", "facebook": "Facebook Reels"}
# A receipt: what happened to ONE row of the sheet on ONE platform.
KEPT, FIXED, SENT, SKIPPED, OFF = "KEPT", "FIXED", "SENT", "SKIPPED", "OFF"      # the platform shows the value / it drifted and code repaired it / sent, and the platform shows nothing back / not applicable / switched off
WAITING = "WAITING"                                                                # it cannot be set yet (a Short's thumbnail before YouTube has processed the video)
DRIFT, REFUSED = "DRIFT", "REFUSED"                                                # the platform shows another value / the platform refused the call
GOOD, BAD = (KEPT, FIXED, SENT, SKIPPED, OFF), (DRIFT, REFUSED)
# A platform's record (tab Release_Sheet, column state):
QUEUED = "QUEUED"                                                                  # handed to Publishing, nothing sent yet (uploads are not open, or the job died before the upload)
OPEN, RETRY = "OPEN", "RETRY"                                                      # up, a row still waits / the upload failed and is tried again
DONE, FLAWED, FAILED = "DONE", "FLAWED", "FAILED"                                  # every row good / up, a row is bad / never went up
FINAL = (DONE, FLAWED, FAILED, SKIPPED, OFF)
YT_SHORT_MAX_S = 180                    # YouTube files an upright or square upload of at most three minutes as a Short (Help 15424877; no API field says so)
PROMISE_FRAME_MS = 1000                 # the frame Instagram takes as the cover when no cover image could be handed over: the promise picture with its words
POLL_S = 15                             # how often the upload job asks YouTube whether processing has finished

# THE SHEET. who: 'code' = set by code at every upload and judged by check release_sheet; 'hand' = only the owner's hand in the platform's own app can
# set it, per video; 'once' = a channel switch he sets once; 'later' = a batch that is not built yet. proof: 'read' = a field of the platform's own
# answer; 'sent' = the platform accepted the call and shows nothing back; 'file' = proven on our own file before it is sent.
SHEET = (
    ("youtube", "file", "code", "file", "the master file, byte for byte - never a file fetched back from another platform"),
    ("youtube", "short", "code", "file", "upright and at most 180 seconds, so YouTube files it as a Short"),
    ("youtube", "title", "code", "read", "the Short's own title"),
    ("youtube", "description", "code", "read", "the hook, how it was made, at most 3 hashtags; no ask, no courtroom word, no link"),
    ("youtube", "tags", "code", "read", "the topic's own tags (never the trial's)"),
    ("youtube", "category", "code", "read", "Science and Technology (YT_CATEGORY)"),
    ("youtube", "language", "code", "read", "English, title and audio"),
    ("youtube", "kids", "code", "read", "not made for kids"),
    ("youtube", "ai", "code", "read", "the altered-content field, true to what the video is (AI_LABEL_DEFAULT)"),
    ("youtube", "privacy", "code", "read", "public at once, set by us and never left to YouTube's default"),
    ("youtube", "thumbnail", "code", "sent", "the Short's own cover, set only after YouTube has processed the video (SHORT_THUMB_ON)"),
    ("youtube", "playlist", "code", "sent", "the playlist of its Short format"),
    ("youtube", "link", "hand", "", "the link from the Short to its long video (YouTube Studio; the one-minute release card, batch V3)"),
    ("youtube", "switches", "once", "", "phone verification (custom thumbnails need it), comments on, remixing on (the pilot sitting, batch V3)"),
    ("youtube", "translations", "later", "", "translated title and description (a paid call per Short; batch V3)"),
    ("instagram", "file", "code", "file", "the master file, byte for byte"),
    ("instagram", "fit", "code", "file", "3 seconds to 15 minutes, 23 to 60 frames a second, at most 1,920 pixels wide"),
    ("instagram", "reel", "code", "read", "a Reel (media_product_type REELS)"),
    ("instagram", "caption", "code", "read", "the hook first, at most 5 hashtags; no ask, no courtroom word, no link"),
    ("instagram", "ai", "code", "read", "Meta's AI label (META_AI_LABEL_ON)"),
    ("instagram", "cover", "code", "read", "the Short's own cover, else its promise frame (SHORT_THUMB_ON)"),
    ("instagram", "audio", "code", "sent", "the audio named after the series (IG_AUDIO_NAME)"),
    ("instagram", "trial", "code", "sent", "a Trial Reel: non-followers first, shared with everybody when it performs (IG_TRIAL_REELS_ON)"),
    ("facebook", "file", "code", "file", "the master file, byte for byte"),
    ("facebook", "fit", "code", "file", "3 to 90 seconds, upright, at least 540 x 960, 24 to 60 frames a second"),
    ("facebook", "description", "code", "read", "the title, the hook, at most 3 hashtags; no ask, no courtroom word, no link"),
    ("facebook", "ai", "code", "sent", "Meta's AI label (META_AI_LABEL_ON)"),
    ("facebook", "published", "code", "read", "published, not a draft"),
)

def on(): return S("RELEASE_SHEET_ON", bool)

def rows_of(platform, who="code"): return [r[1] for r in SHEET if r[0] == platform and r[2] == who]

def not_ours():
    """The rows the machine cannot set: {'hand': n, 'once': n, 'later': n} - never counted as set, by anybody."""
    out = {}
    for r in SHEET:
        if r[2] != "code": out[r[2]] = out.get(r[2], 0) + 1
    return out

# ------------------------------------------------------------------ the file: its hash, its shape, where it fits
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def probe(path):
    """{w, h, sec, fps} of a video file, measured on the file itself."""
    import cv2
    cap = cv2.VideoCapture(path); fps = float(cap.get(cv2.CAP_PROP_FPS) or 0); n = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0); cap.release()
    return {"w": w, "h": h, "sec": round(n / fps, 2) if fps > 0 else 0.0, "fps": round(fps, 2)}

def fit(platform, p, small=None):
    """Why this file can NOT go to `platform` as a short video ([] = it fits). Pure: the platforms' own published limits (YouTube Help 15424877;
    Instagram's media reference; Facebook's Reels publishing guide - 12 Nov 2026). small = the rehearsal's third-size render (its pixels count three
    times, so the offline pipeline meets the same limits as a full-size file)."""
    k = 3 if (SMALL if small is None else small) else 1
    w, h, sec, fps = int(p.get("w") or 0) * k, int(p.get("h") or 0) * k, float(p.get("sec") or 0), float(p.get("fps") or 0)
    if w <= 0 or h <= 0 or sec <= 0: return ["the file could not be measured"]
    out = []
    if platform == "youtube":
        if h < w: out.append(f"{w} x {h} is wider than it is tall: YouTube would file it as a long video, not a Short")
        if sec > YT_SHORT_MAX_S: out.append(f"{sec:.0f} s is over the {YT_SHORT_MAX_S} s of a Short")
    elif platform == "instagram":
        if not 3 <= sec <= 900: out.append(f"{sec:.0f} s is outside Instagram's 3 s to 15 min")
        if not 23 <= fps <= 60: out.append(f"{fps:g} frames a second is outside Instagram's 23 to 60")
        if w > 1920: out.append(f"{w} pixels wide is over Instagram's 1,920")
    elif platform == "facebook":
        if not 3 <= sec <= 90: out.append(f"{sec:.0f} s is outside the 3 to 90 s of a Facebook Reel")
        if h <= w: out.append(f"{w} x {h} is not upright")
        if w < 540 or h < 960: out.append(f"{w} x {h} is under Facebook's 540 x 960")
        if not 24 <= fps <= 60: out.append(f"{fps:g} frames a second is outside Facebook's 24 to 60")
    else: out.append(f"unknown platform '{platform}'")
    return out

# ------------------------------------------------------------------ the words next to a Short, per platform (code, from its own record)
HOW = "Made with AI tools from an original script: the pictures, the motion and the voice."
PROMISE = "One law of nature is different today, and it happens to you."
LIMITS = {"youtube": 3, "instagram": 5, "facebook": 3}          # hashtags a platform's text may carry

def hashtags(n):
    seen = []
    for t in re.findall(r"#\w+", str(S("SHORT_HASHTAGS") or "")):
        if t.lower() not in [x.lower() for x in seen]: seen.append(t)
    return seen[:max(0, n)]

def _hook(row):
    """The first spoken sentence of the Short (what its record kept of the script)."""
    from whatifs.org import shortseat as SEAT
    first = next((l.strip() for l in str(row.get("script") or "").splitlines() if l.strip()), "")
    s = SEAT.sentences(first)
    return (s[0] if s else first).strip()

def texts(row):
    """What stands next to a Short on each platform, built by code from the Short's own record (title, script) - never one text for all three:
    {'youtube': {title, description, tags}, 'instagram': {caption}, 'facebook': {description}}. YouTube: the title is the title, the description
    opens on the hook. Instagram: the caption opens on the hook (its first line is what shows before 'more'); no link (a caption cannot carry one).
    Facebook: title, then hook. No ask anywhere: a Short asks for nothing."""
    title = " ".join(str(row.get("title") or "").split()); hook = _hook(row) or title
    def tags(p): return " ".join(hashtags(LIMITS[p]))
    return {"youtube": {"title": title[:100], "description": "\n".join(x for x in (hook, "", PROMISE, HOW, tags("youtube")) if x is not None).strip(),
                        "tags": list(dict.fromkeys([t.lstrip("#") for t in hashtags(8)] + ["what if"]))},
            "instagram": {"caption": "\n".join(x for x in (hook, "", title, HOW, tags("instagram")) if x is not None).strip()},
            "facebook": {"description": "\n".join(x for x in (title, hook, HOW, tags("facebook")) if x is not None).strip()}}

def text_issues(platform, text):
    """What is recognisably wrong with a text next to a Short ([] = nothing): an ask (the Short's own rule), a courtroom word (a Short is never a
    trial), a link, more hashtags than the platform's row allows. Only what code can RECOGNISE is named."""
    from whatifs import formats as FMT
    from whatifs.org import shortseat as SEAT
    t = str(text or ""); out = []
    m = SEAT.ASK_RX.search(t)
    if m: out.append(f"an ask ('{m.group(0)}')")
    c = FMT._TRIAL_RX.search(t)
    if c: out.append(f"a courtroom word ('{c.group(0).strip()}')")
    if re.search(r"https?://|\bwww\.", t, re.I): out.append("a link")
    n = len(re.findall(r"#\w+", t))
    if n > LIMITS.get(platform, 3): out.append(f"{n} hashtags (at most {LIMITS.get(platform, 3)})")
    return out

def _same(a, b): return " ".join(str(a or "").split()) == " ".join(str(b or "").split())

# ------------------------------------------------------------------ the receipts (pure): what was wanted against what the platform answered
def want_youtube(tx):
    from whatifs import publish as PUB
    b = PUB.yt_body(tx["youtube"]["title"], tx["youtube"]["description"], tx["youtube"]["tags"], ai_label=S("AI_LABEL_DEFAULT", bool))
    sn, stt = b["snippet"], b["status"]
    return b, {"title": sn["title"], "description": sn["description"], "tags": sn["tags"], "category": sn["categoryId"], "language": sn["defaultLanguage"],
               "kids": False, "ai": stt["containsSyntheticMedia"], "privacy": stt["privacyStatus"]}

def compare(platform, want, got):
    """Receipts for the rows a platform's own answer can prove: {row: [state, detail]}. KEPT = the platform shows what was wanted; DRIFT = it shows
    something else; SENT = the platform's answer does not carry the field at all (it was sent; nothing more can be said). A text that carries what a
    Short must never carry (an ask, a courtroom word, a link, too many hashtags) is DRIFT even when the platform kept it word for word."""
    out = {}
    for row, w in want.items():
        g = got.get(row)
        if row in ("title", "description", "caption"):
            bad = text_issues(platform, w)
            if bad: out[row] = [DRIFT, "the text carries " + ", ".join(bad)]
            elif g is None: out[row] = [SENT, "the platform's answer does not show the text"]
            else: out[row] = [KEPT, f"{len(str(g))} characters, as sent"] if _same(g, w) else [DRIFT, f"the platform shows '{str(g)[:60]}', sent '{str(w)[:60]}'"]
        elif row == "tags":
            a, b = sorted(str(x).lower() for x in (g or [])), sorted(str(x).lower() for x in w)
            out[row] = [KEPT, ", ".join(w)] if a == b else ([SENT, "the platform's answer does not show the tags"] if g is None else [DRIFT, f"the platform shows {a}, sent {b}"])
        elif row == "language":
            ok = got.get("language") == w and got.get("audio_language") in (w, None)
            out[row] = [KEPT, str(w)] if ok else [DRIFT, f"title language {got.get('language')}, audio language {got.get('audio_language')}, sent {w}"]
        elif g is None: out[row] = [SENT, "the platform's answer does not show this field"]
        else: out[row] = [KEPT, str(g)] if g == w else [DRIFT, f"the platform shows {g}, wanted {w}"]
    return out

def state_of(receipts):
    """The state of one platform's record from its receipts: FLAWED when a row is bad, OPEN while one waits, else DONE."""
    v = [r[0] for r in (receipts or {}).values()]
    return FLAWED if any(x in BAD for x in v) else OPEN if WAITING in v else DONE

# ------------------------------------------------------------------ the record (tab Release_Sheet: one row per Short and platform)
def _js(v, d):
    try: return json.loads(v) if isinstance(v, str) and v.strip() else (v if isinstance(v, (dict, list)) else d)
    except ValueError: return d

def records(sid=None):
    try: rs = store().rows(TAB)
    except Exception: return []
    out = []
    for r in rs:
        if sid is not None and r.get("id") != sid: continue
        r = dict(r); r["receipts"] = _js(r.get("receipts"), {}); out.append(r)
    return out

def _save(sid, platform, now, **kw):
    st = store(); kw = {k: (json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else v) for k, v in kw.items()}
    if not st.update_where(TAB, {"id": sid, "platform": platform}, kw):
        st.append(TAB, [dict({"ts": iso(now), "id": sid, "platform": platform, "kind": "short", "native_id": "", "state": "", "sha": "", "sent": "{}", "got": "{}",
                              "receipts": "{}", "tries": 0, "checked": "", "note": ""}, **kw)])

def _short_row(sid):
    return next((r for r in store().rows("Specials") if r.get("id") == sid and r.get("kind") == "short"), None)

def _fetch(ref, path):
    """A kept file (the master, the cover) from the owner's Drive back onto this machine."""
    from whatifs import publish as PUB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path): PUB.drive_download(str(ref).replace("drive:", ""), path)
    return path

def master(row, path=None):
    """The Short's master file on this machine - the file `shorts2.make` wrote, or the copy kept in Drive - and ONLY that file: its SHA-256 must be
    the one on the Short's record. Anything else is refused before a platform sees it."""
    sid = row["id"]; p = path if (path and os.path.exists(path)) else _fetch(row.get("file") or "", os.path.join(WORK, sid, f"{sid}.mp4"))
    have, want = sha(p), str(row.get("sha") or "")
    if not want or have != want: raise RuntimeError(f"the file at hand is not the master of {sid} (its hash is {have[:12]}, the record says {want[:12] or 'nothing'})")
    return p, have

def cover(row, path=None):
    """The Short's cover on this machine, or '' (switched off, or none was kept: the platforms then pick a frame)."""
    if not S("SHORT_THUMB_ON", bool): return ""
    if path and os.path.exists(path): return path
    if not str(row.get("cover") or "").strip(): return ""
    try: return _fetch(row["cover"], os.path.join(WORK, row["id"], "cover.jpg"))
    except Exception as e: log(f"the cover of {row['id']} could not be fetched ({scrub(e)[:80]})", "WARN", row["id"]); return ""

# ------------------------------------------------------------------ one platform at a time
def _extras_youtube(vid, rc, row, cov, got, first, now):
    """The rows of YouTube that are calls of their own: the AI field repaired once, the thumbnail (only after processing), the playlist."""
    from whatifs import publish as PUB, formats as FMT
    if rc.get("ai", [""])[0] == DRIFT and got.get("ai") is False:                # YouTube dropped the label: set it again, once, and read it back
        fixed = PUB.yt_set_label(vid, True) and PUB.yt_read(vid).get("ai") is True
        rc["ai"] = [FIXED, "YouTube had dropped the AI field; set again and read back"] if fixed else [DRIFT, "YouTube shows no AI field and the repair did not hold"]
    if rc.get("thumbnail", [""])[0] not in (SENT, OFF, REFUSED):
        if not cov: rc["thumbnail"] = [OFF, "no cover (SHORT_THUMB_ON is FALSE, or none was kept): YouTube picks a frame"]
        else:
            left = 0 if FAKE else max(0.0, S("SHORT_THUMB_WAIT_S", float)) if first else 0
            while not got.get("processed") and left > 0:
                time.sleep(POLL_S); left -= POLL_S; got = PUB.yt_read(vid) or got
            if got.get("processed"):
                rc["thumbnail"] = [SENT, "set after processing had succeeded"] if PUB.yt_thumbnail(vid, cov) else [REFUSED, "YouTube refused the thumbnail (custom thumbnails need a phone-verified channel)"]
            else:
                t0 = parse_iso(row.get("made")); late = t0 and (now - t0).total_seconds() > S("RELEASE_SETTLE_H", float) * 3600 and not first
                rc["thumbnail"] = ([REFUSED, f"YouTube had not finished processing after {S('RELEASE_SETTLE_H')} hours: the thumbnail was never set"] if late
                                   else [WAITING, "YouTube is still processing the video: a thumbnail set now might be accepted and never shown"])
    if rc.get("playlist", [""])[0] != SENT:
        name = FMT.short_name(str(row.get("format") or "")) or "Shorts"
        rc["playlist"] = [SENT, f"'{name}'"] if PUB.yt_playlist(vid, name) else [REFUSED, f"the Short could not be added to the playlist '{name}'"]
    return rc

def _youtube(row, path, digest, cov, tx, rec, now):
    from whatifs import publish as PUB
    body, want = want_youtube(tx); vid = str((rec or {}).get("native_id") or ""); first = not vid
    if first:
        vid = PUB.yt_upload(path, tx["youtube"]["title"], tx["youtube"]["description"], tx["youtube"]["tags"], short=True, ai_label=S("AI_LABEL_DEFAULT", bool))
        _save(row["id"], "youtube", now, native_id=vid, state=OPEN, sha=digest, sent=body)      # on record AT ONCE: a job cut off after this line must never upload the Short a second time
    got = PUB.yt_read(vid); rc = dict((rec or {}).get("receipts") or {})
    rc.update(compare("youtube", want, got) if got else {k: [SENT, "the upload could not be read back"] for k in want})
    if got.get("privacy") == "private":                                             # asked public, came back private: the lock - the detector alerts and production pauses
        from whatifs import launch as LA; LA.lock_detected(vid, ["a Short came back private (asked public)"])
    rc["file"] = [KEPT, f"sha256 {digest[:12]}: the master"]; rc["short"] = [KEPT, "upright, at most 180 s"]
    rc = _extras_youtube(vid, rc, row, cov, got, first, now)
    return vid, body, got, rc

def _linker(opened):
    """Public Drive links, made only when a platform asks for one and closed again by the caller."""
    from whatifs import publish as PUB
    links = {}
    def link(p):
        if p not in links:
            fid, url = PUB.drive_upload(p, os.path.basename(p), public=True); opened.append(fid); links[p] = url
        return links[p]
    return link

def _instagram(row, path, digest, cov, tx, rec, now):
    from whatifs import publish as PUB
    opened = []; link = _linker(opened); cap = tx["instagram"]["caption"]; curl = None
    trial = "SS_PERFORMANCE" if S("IG_TRIAL_REELS_ON", bool) else ""; audio = str(S("IG_AUDIO_NAME") or "").strip()
    mid = str((rec or {}).get("native_id") or "")
    if mid: sent = _js((rec or {}).get("sent"), {}); curl = sent.get("cover_url")      # it is up already: a later pass only reads it back, it never posts a second Reel
    else:
        try:
            if cov:
                try: curl = link(cov)
                except Exception as e: log(f"the cover link could not be opened ({scrub(e)[:80]}): Instagram takes the promise frame", "WARN", row["id"])
            off = None if curl or not S("SHORT_THUMB_ON", bool) else PROMISE_FRAME_MS
            try: mid = PUB.ig_reel(None, cap, curl, video_path=path, url_fn=lambda: link(path), thumb_offset_ms=off, audio_name=audio, trial=trial, ref=row["id"])
            except Exception as e:
                if not curl: raise
                # Instagram must FETCH a cover image from a link, and a link can fail on Meta's side: the Reel is never lost for its cover - once more, on the promise frame
                log(f"Instagram refused the Reel with its cover image ({scrub(e)[:100]}): once more with the promise frame as the cover", "WARN", row["id"])
                curl = None; off = PROMISE_FRAME_MS
                mid = PUB.ig_reel(None, cap, None, video_path=path, url_fn=lambda: link(path), thumb_offset_ms=off, audio_name=audio, trial=trial, ref=row["id"])
            sent = PUB.ig_reel_params(cap, curl, off, audio, trial)
            _save(row["id"], "instagram", now, native_id=mid, state=OPEN, sha=digest, sent=sent)      # on record at once (see the YouTube sender)
        finally:
            for fid in opened:
                try: PUB.drive_private(fid)
                except Exception: pass
    got = PUB.ig_read(mid)
    want = {"reel": "REELS", "caption": cap, "ai": bool(S("META_AI_LABEL_ON", bool))}
    rc = compare("instagram", {"caption": cap}, got) if got else {"caption": [SENT, "the Reel could not be read back"]}
    rc["reel"] = [KEPT, "REELS"] if got.get("product") == want["reel"] else ([SENT, "the Reel could not be read back"] if not got else [DRIFT, f"Instagram shows {got.get('product')}, not a Reel"])
    rc["ai"] = ([OFF, "META_AI_LABEL_ON is FALSE"] if not want["ai"] else [SENT, "the Reel could not be read back"] if not got or got.get("ai") is None
                else [KEPT, "the AI label is on"] if got.get("ai") else [DRIFT, "Instagram shows no AI label"])
    rc["cover"] = ([OFF, "SHORT_THUMB_ON is FALSE: Instagram picks a frame"] if not S("SHORT_THUMB_ON", bool) else [SENT, "the Reel could not be read back"] if not got
                   else [KEPT, "the Short's own cover" if curl else "its promise frame (no cover image could be handed over)"] if got.get("cover") else [DRIFT, "Instagram shows no cover"])
    rc["audio"] = [SENT, f"'{audio}' (Instagram shows no field to read it back)"] if "audio_name" in sent else [OFF, "IG_AUDIO_NAME is blank"]
    rc["trial"] = [SENT, "Trial Reel, graduated by performance (Instagram shows no field to read it back)"] if "trial_params" in sent else [OFF, "IG_TRIAL_REELS_ON is FALSE: a normal Reel"]
    rc["file"] = [KEPT, f"sha256 {digest[:12]}: the master"]; rc["fit"] = [KEPT, "inside Instagram's limits"]
    return mid, sent, got, rc

def _facebook(row, path, digest, cov, tx, rec, now):
    from whatifs import publish as PUB
    opened = []; link = _linker(opened); desc = tx["facebook"]["description"]; fid = str((rec or {}).get("native_id") or "")
    if not fid:                                                                     # (it is up already: a later pass only reads it back)
        try:
            fid = PUB.fb_reel(None, desc, video_path=path, url_fn=lambda: link(path), ref=row["id"])
            _save(row["id"], "facebook", now, native_id=fid, state=OPEN, sha=digest)                # on record at once (see the YouTube sender)
        finally:
            for x in opened:
                try: PUB.drive_private(x)
                except Exception: pass
    sent = PUB.fb_reel_finish(desc, fid); got = PUB.fb_read(fid)
    rc = compare("facebook", {"description": desc}, got) if got else {"description": [SENT, "the Reel could not be read back"]}
    rc["published"] = [SENT, "the Reel could not be read back"] if not got else [KEPT, "published"] if got.get("published") else [WAITING, "Facebook has not published it yet"]
    rc["ai"] = [SENT, "sent (Facebook shows no field to read it back)"] if "is_ai_generated" in sent else [OFF, "META_AI_LABEL_ON is FALSE"]
    rc["file"] = [KEPT, f"sha256 {digest[:12]}: the master"]; rc["fit"] = [KEPT, "3 to 90 s, upright"]
    return fid, sent, got, rc

_SEND = {"youtube": _youtube, "instagram": _instagram, "facebook": _facebook}

def connected(platform):
    """'' when the platform can be posted to, else why not (Instagram and Facebook are optional: Meta not connected is no fault)."""
    from whatifs import publish as PUB
    if platform == "youtube": return ""
    if not PUB.meta_ready(): return "Instagram and Facebook are not connected (META_ON, the Meta key)"
    if not FAKE and not str(S("IG_USER_ID" if platform == "instagram" else "FB_PAGE_ID") or "").strip(): return f"no {NAMES[platform].split()[0]} account is connected"
    return ""

def _one(platform, row, path, digest, cov, pr, tx, rec, now):
    """Send (or finish) ONE platform's release of a Short and write its record. Never raises: a failure is a record."""
    sid = row["id"]; tries = int(float((rec or {}).get("tries") or 0))
    try:
        why = connected(platform)
        if why and not (rec or {}).get("native_id"): _save(sid, platform, now, state=OFF, note=why); return OFF
        bad = fit(platform, pr)
        if bad and not (rec or {}).get("native_id"):                                 # the file does not fit this platform: it is not sent there, and never cut to fit
            _save(sid, platform, now, state=SKIPPED, note="; ".join(bad)[:300], receipts={"fit" if platform != "youtube" else "short": [SKIPPED, "; ".join(bad)[:200]]}); return SKIPPED
        nid, sent, got, rc = _SEND[platform](row, path, digest, cov, tx, rec, now)
        stt = state_of(rc)
        _save(sid, platform, now, native_id=nid, state=stt, sha=digest, sent=sent, got=got, receipts=rc, tries=tries + (0 if (rec or {}).get("native_id") else 1),
              note="; ".join(f"{k}: {v[1]}" for k, v in rc.items() if v[0] in BAD + (WAITING,))[:300])
        return stt
    except Exception as e:
        tries += 1; stt = FAILED if tries >= max(1, S("RELEASE_TRIES_MAX", int)) else RETRY
        _save(sid, platform, now, state=stt, tries=tries, note=f"try {tries}: {scrub(e)[:200]}")
        log(f"release of {sid} to {NAMES[platform]} failed (try {tries}): {scrub(e)[:160]}", "WARN", sid); return stt

# ------------------------------------------------------------------ D9's run: one Short, three native uploads, a receipt for every row
def _release(sid, path, cov, now):
    from whatifs import launch as LA, ladder as LAD
    st = store(); row = _short_row(sid)
    if not row: raise RuntimeError(f"{sid} is not a standalone Short on record")
    if not str(row.get("made") or "").strip(): raise RuntimeError(f"{sid} was never made: there is nothing to release")
    queue(sid, now)
    if not LA.uploads_open():
        st.update("Specials", "id", sid, {"status": "UPLOAD_WAITING (uploads are not confirmed open)"})
        return {"id": sid, "waiting": "uploads are not confirmed open", "states": {}}
    have = {r["platform"]: r for r in records(sid)}; states = {}
    try: path, digest = master(row, path)
    except Exception as e:                                                          # no master, or not THE master: nothing is sent anywhere, and it is on record
        for p in PLATFORMS:
            if not (have.get(p) or {}).get("native_id"): _save(sid, p, now, state=FAILED, note=f"no master to send: {scrub(e)[:200]}")
        st.update("Specials", "id", sid, {"status": "UPLOAD_FAILED (the master file could not be used)"})
        log(f"release of {sid} refused: {scrub(e)[:200]}", "ERROR", sid)
        return {"id": sid, "states": {p: FAILED for p in PLATFORMS}, "yt_id": str(row.get("yt_id") or ""), "receipts": {}}
    cov = cover(row, cov); pr = probe(path); tx = texts(row)
    for p in PLATFORMS:
        rec = have.get(p)
        states[p] = rec["state"] if rec and rec.get("state") in FINAL else _one(p, row, path, digest, cov, pr, tx, rec, now)
    recs = {r["platform"]: r for r in records(sid)}; yt = str((recs.get("youtube") or {}).get("native_id") or "")
    was = str(row.get("yt_id") or "")
    st.update("Specials", "id", sid, {"yt_id": yt, "ig": str((recs.get("instagram") or {}).get("native_id") or ""), "fb": str((recs.get("facebook") or {}).get("native_id") or ""),
                                      "status": "POSTED" if yt else f"UPLOAD_WAITING ({str((recs.get('youtube') or {}).get('note') or 'YouTube')[:80]})"})
    if yt and not was: LAD.went_public(sid, yt, now)                                # the ladder's clock starts when the Short really went public
    return {"id": sid, "states": states, "yt_id": yt, "receipts": {p: (recs.get(p) or {}).get("receipts") or {} for p in PLATFORMS}}

def queue(sid, now=None):
    """Hand a Short to Publishing: from now on the pass of every tick will see it through, whatever happens to this job. The hand-over is a RECORD
    (a row on tab Release_Sheet), never a word in a status text. Once per Short."""
    if not any(r.get("platform") == "youtube" for r in records(sid)): _save(sid, "youtube", now or now_utc(), state=QUEUED, note="handed to Publishing")

def m_release(out):
    """D9 short_publish: how many platforms have the Short and what the receipts say."""
    out = out if isinstance(out, dict) else {}; rc = [v[0] for p in (out.get("receipts") or {}).values() for v in p.values()]
    return {"platforms": sum(1 for s in (out.get("states") or {}).values() if s in (DONE, FLAWED, OPEN)), "rows_good": sum(1 for x in rc if x in GOOD),
            "rows_bad": sum(1 for x in rc if x in BAD), "rows_waiting": sum(1 for x in rc if x == WAITING)}

def release_lessons(out):
    """What Publishing must learn from a release: every row a platform did not keep, by platform and row."""
    return [(f"release:{p}:{k}", f"{NAMES[p]}, row '{k}': {v[1]}"[:240]) for p, rs in ((out or {}).get("receipts") or {}).items() for k, v in rs.items() if v[0] in BAD]

def _gate_emit(sid):
    def emit(g, brief):
        return [{"type": "problem_memo", "from_dept": "D8", "to_depts": ["D9"], "subject": f"{fid}: a Short's release sheet has a row the platform did not keep"[:140],
                 "body": {"what_failed": f"contract check {fid}: {str(ev)[:300]}", "where": f"{sid} release gate", "attempt": 1, "check": fid, "stage": "release"},
                 "done_when": f"a Short passes check {fid} at the release gate", "episode_id": "", "dedupe_key": f"gate|release|{fid}",
                 "evidence": [{"source": f"Feature_Ledger:{sid}:release:{fid}", "date": iso()[:10], "type": "own data", "finding": str(ev)[:300]}]}
                for fid, ev in ((g or {}).get("failed") or [])]
    return emit

def _gate_settle(sid):
    from whatifs.org import memos as MEM
    def settle_(g, brief):
        rows = {r.get("feature"): r.get("status") for r in ((g or {}).get("rows") or [])}
        return [(m["id"], "repair_verified", f"Feature_Ledger:{sid}:release:{m['body'].get('check')}:PASS")
                for m in MEM.find(type="problem_memo", from_dept="D8", stage="release") if rows.get(m["body"].get("check")) == "PASS"]
    return settle_

def gate(sid, now=None):
    """D8's run `release_gate`: check release_sheet judges the receipts of a Short whose every platform is final. Once per Short. The Short is public
    by then, so nothing is held and the owner is not asked: a row the platform did not keep is a problem memo to Publishing."""
    from whatifs import contract as CON
    from whatifs.org import runner as ORG, wraps as WR
    now = now or now_utc()
    g = ORG.work("D8", "release_gate", sid, lambda b: CON.run("release", {"ep": sid, "release": {"id": sid}}, sid), measure=WR.m_gate, lesson=WR.gate_lessons,
                 emit=_gate_emit(sid), settle=_gate_settle(sid))
    for r in records(sid): store().update_where(TAB, {"id": sid, "platform": r["platform"]}, {"checked": iso(now)})
    return g

def short(sid, path=None, cover_path=None, now=None):
    """Release ONE standalone Short: Publishing's run `short_publish`. The same call sends a fresh Short, a Short the owner has just approved and a
    Short that waited for uploads to open - and finishes what a platform made wait. When every platform is final, the release gate judges the sheet."""
    from whatifs.org import runner as ORG
    now = now or now_utc()
    out = ORG.work("D9", "short_publish", sid, lambda b: _release(sid, path, cover_path, now), measure=m_release, lesson=release_lessons)
    recs = records(sid)
    if recs and all(r.get("state") in FINAL for r in recs) and not all(str(r.get("checked") or "").strip() for r in recs): gate(sid, now)
    return out

def report(sid, now=None):
    """(ok, why) for check `release_sheet`: every row of the sheet that code sets was KEPT by the platform (or repaired once, or sent where the
    platform shows nothing back, or is switched off / not applicable) - on YouTube always, on Instagram and Facebook when they are connected."""
    recs = {r["platform"]: r for r in records(sid)}
    if "youtube" not in recs: return False, f"{sid} has no release record for YouTube"
    bad, parts = [], []
    for p in PLATFORMS:
        r = recs.get(p)
        if not r: bad.append(f"{NAMES[p]}: no record"); continue
        stt = r.get("state"); rc = r.get("receipts") or {}
        if stt == OFF and p != "youtube": parts.append(f"{NAMES[p]}: not connected"); continue          # Instagram and Facebook are optional; YouTube is the product
        if stt == SKIPPED and p != "youtube": parts.append(f"{NAMES[p]}: not sent ({str(r.get('note'))[:80]})"); continue
        if stt in (FAILED, RETRY, SKIPPED, OFF, QUEUED):
            bad.append(f"{NAMES[p]}: " + ("is up, but its release could not be finished" if r.get("native_id") else "never went up") + f" ({str(r.get('note'))[:100]})"); continue
        miss = [k for k in rows_of(p) if k not in rc]
        wrong = [f"{k} {v[0]} ({v[1][:70]})" for k, v in rc.items() if v[0] in BAD + (WAITING,)]
        if miss: bad.append(f"{NAMES[p]}: no receipt for " + ", ".join(miss))
        if wrong: bad.append(f"{NAMES[p]}: " + "; ".join(wrong))
        n = lambda *s: sum(1 for v in rc.values() if v[0] in s)
        parts.append(f"{NAMES[p]}: {n(KEPT)} kept" + (f", {n(FIXED)} repaired" if n(FIXED) else "") + f", {n(SENT)} sent without a read-back" + (f", {n(OFF, SKIPPED)} off" if n(OFF, SKIPPED) else ""))
    if bad: return False, " | ".join(bad)
    no = not_ours()
    return True, "; ".join(parts) + f"; {sum(no.values())} rows are not the machine's to set ({', '.join(f'{v} {k}' for k, v in sorted(no.items()))})"

# ------------------------------------------------------------------ the pass that finishes (every tick)
def approved(sid):
    """The owner approved a Short: it goes out through the same run as every other Short (its own words, its master, its cover)."""
    row = _short_row(sid)
    if not row: return f"{sid} not found"
    store().update("Specials", "id", sid, {"status": "APPROVED"})
    out = short(sid) or {}
    return f"posted {sid}" if out.get("yt_id") else f"{sid} is approved and waits: {out.get('waiting') or 'the upload did not go through yet'}"

def settle(now=None):
    """Every tick: finish what waits. A Short that was HANDED TO PUBLISHING (it has a record - a Short that still waits for the owner's Approve has
    none) and is not out yet goes out as soon as uploads are open; a platform that failed is tried again; a row that waited for YouTube's
    processing is finished - only when YouTube says it is ready, or its time is up. Level-triggered: it reads state, so a dropped tick loses
    nothing. Returns the ids it worked on."""
    if not on(): return []
    from whatifs import launch as LA, publish as PUB
    now = now or now_utc(); done = []; by = {}
    for r in records(): by.setdefault(r.get("id"), {})[r.get("platform")] = r
    if not by: return []
    try: made = {r["id"]: r for r in store().rows("Specials") if r.get("kind") == "short" and str(r.get("made") or "").strip()}
    except Exception: return []
    for sid, recs in by.items():
        row = made.get(sid)
        if not row or all(str(r.get("checked") or "").strip() for r in recs.values()): continue      # judged: finished
        t0 = parse_iso(row.get("made"))
        if not t0 or (now - t0).days > max(1, S("LADDER_WINDOW_DAYS", int)): continue      # past the ladder's window nothing is sent any more
        try:
            if any(r.get("state") in (QUEUED, RETRY) for r in recs.values()):
                if LA.uploads_open(): short(sid, now=now); done.append(sid)
            elif any(r.get("state") == OPEN for r in recs.values()):
                y = recs.get("youtube") or {}; late = (now - t0).total_seconds() > S("RELEASE_SETTLE_H", float) * 3600
                waits_yt = (y.get("receipts") or {}).get("thumbnail", [""])[0] == WAITING
                if late or not waits_yt or PUB.yt_read(y.get("native_id")).get("processed"): short(sid, now=now); done.append(sid)
            elif all(r.get("state") in FINAL for r in recs.values()): gate(sid, now); done.append(sid)
        except Exception as e: log(f"release settle of {sid} failed: {scrub(e)[:160]}", "WARN", sid)
    return done
