"""whatifs/publish.py v8.5 - YouTube (resumable upload, scheduled publishAt, thumbnail, captions, playlist, AI label, title swap),
Instagram Reels + Facebook Reels (Graph API), Google Drive archive, Gmail notices. All calls retried; failures never block the next episode."""
from __future__ import annotations
import os, re, json, time, base64
from email.mime.text import MIMEText            # v8.9.3: imported by name; the module-level email() function below would hide the `email` package
from email.mime.multipart import MIMEMultipart
import requests
from whatifs.core import gheaders, gdrive_headers, env, log, S, FAKE, retry, WORK

YT = "https://www.googleapis.com/youtube/v3/"
UP = "https://www.googleapis.com/upload/youtube/v3/"
def graph_version():
    v = (S("META_GRAPH_VERSION") or "v24.0").strip()
    return v if v.startswith("v") else "v" + v
def gv(): return f"https://graph.facebook.com/{graph_version()}/"

# ---------------- YouTube ----------------
def clean_meta(title, description, tags):
    """v8.3: YouTube rejects '<' and '>' and over-long fields with a 400 AFTER all the money is spent (and a retry with the same plan fails the same way). Clean them first."""
    t = re.sub(r"\s+", " ", re.sub(r"[<>]", "", str(title or ""))).strip()[:100] or "Untitled simulation"
    d = re.sub(r"[<>]", "", str(description or "")).strip()
    while len(d.encode("utf-8")) > 4900: d = d[:-50]                       # the limit is in BYTES, not characters
    out, seen, total = [], set(), 0
    for g in tags or []:
        g = re.sub(r"\s+", " ", re.sub(r'[<>",]', "", str(g))).strip()[:30]
        cost = len(g) + (2 if " " in g else 0) + 1
        if not g or g.lower() in seen or total + cost > 450 or len(out) >= 30: continue
        seen.add(g.lower()); out.append(g); total += cost
    return t, d, out

def _resume_point(loc, size):
    """Ask an open resumable-upload session how much it has. ('done', video_id) | ('at', bytes_received) | None (session unusable: start a new one)."""
    try:
        r = requests.put(loc, headers={"Authorization": gheaders()["Authorization"], "Content-Length": "0", "Content-Range": f"bytes */{size}"}, timeout=60)
    except requests.RequestException: return None
    if r.status_code in (200, 201):
        try: return ("done", r.json()["id"])
        except Exception: return None
    if r.status_code == 308:
        rng = r.headers.get("Range"); return ("at", int(rng.split("-")[1]) + 1 if rng else 0)
    return None

def yt_upload(path, title, description, tags, publish_at=None, made_for_kids=False, ai_label=True, short=False):
    if FAKE: return "FAKE_" + os.path.basename(path)
    title, description, tags = clean_meta(title, description, tags)
    body = {"snippet": {"title": title, "description": description, "tags": tags, "categoryId": S("YT_CATEGORY"),
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private" if publish_at else "public", "selfDeclaredMadeForKids": made_for_kids,
                       "embeddable": True, "license": "youtube", "containsSyntheticMedia": bool(ai_label)}}
    if publish_at: body["status"]["publishAt"] = publish_at
    session = {}                                   # v8.3: the upload session survives a retry, so a lost final answer can never create a second video
    def go():
        size = os.path.getsize(path); chunk = 64 * 1024 * 1024; sent = 0
        if session.get("loc"):
            rp = _resume_point(session["loc"], size)
            if rp and rp[0] == "done": return rp[1]
            if rp and rp[0] == "at": sent = rp[1]
            else: session.clear()
        if not session.get("loc"):
            h = gheaders(); h.update({"Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
            r = requests.post(UP + "videos?uploadType=resumable&part=snippet,status", headers=h, json=body, timeout=60)
            if r.status_code == 400 and "containsSyntheticMedia" in r.text:
                body["status"].pop("containsSyntheticMedia", None)
                r = requests.post(UP + "videos?uploadType=resumable&part=snippet,status", headers=h, json=body, timeout=60)
            if r.status_code >= 400: raise RuntimeError(f"YouTube start {r.status_code}: {r.text[:400]}")
            session["loc"] = r.headers["Location"]
        loc = session["loc"]
        with open(path, "rb") as f:
            f.seek(sent)
            while sent < size:
                data = f.read(chunk); end = sent + len(data) - 1
                for a in range(6):
                    try:
                        rr = requests.put(loc, headers={"Authorization": gheaders()["Authorization"], "Content-Length": str(len(data)),
                                                        "Content-Range": f"bytes {sent}-{end}/{size}"}, data=data, timeout=900)
                        break
                    except requests.RequestException as e:
                        log(f"upload chunk retry: {e}", "WARN"); time.sleep(10 * (a + 1))
                else: raise RuntimeError("upload chunk failed")
                if rr.status_code in (200, 201): return rr.json()["id"]
                if rr.status_code != 308: raise RuntimeError(f"YouTube chunk {rr.status_code}: {rr.text[:300]}")
                rng = rr.headers.get("Range"); sent = int(rng.split("-")[1]) + 1 if rng else 0; f.seek(sent)
        raise RuntimeError("upload ended without id")
    return retry(go, tries=3, wait=30, what="youtube upload")

def yt_thumbnail(vid, path):
    if FAKE: return True
    h = gheaders(); h["Content-Type"] = "image/jpeg"
    r = requests.post(UP + f"thumbnails/set?videoId={vid}", headers=h, data=open(path, "rb").read(), timeout=120)
    if r.status_code >= 400: log(f"thumbnail failed {r.status_code}: {r.text[:300]} (is the channel phone-verified?)", "WARN"); return False
    return True

def yt_captions(vid, srt_path):
    if FAKE: return True
    meta = {"snippet": {"videoId": vid, "language": "en", "name": "English", "isDraft": False}}
    boundary = "wi" + str(int(time.time()))
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n--{boundary}\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + open(srt_path, "rb").read() + f"\r\n--{boundary}--".encode()
    h = gheaders(); h["Content-Type"] = f"multipart/related; boundary={boundary}"
    r = requests.post(UP + "captions?uploadType=multipart&part=snippet", headers=h, data=body, timeout=120)
    if r.status_code >= 400: log(f"captions failed {r.status_code}: {r.text[:300]}", "WARN"); return False
    return True

def yt_playlist(vid, name):
    if FAKE: return True
    try:
        r = requests.get(YT + "playlists?part=snippet&mine=true&maxResults=50", headers=gheaders(), timeout=30).json()
        pl = next((p["id"] for p in r.get("items", []) if p["snippet"]["title"] == name), None)
        if not pl:
            pl = requests.post(YT + "playlists?part=snippet,status", headers=gheaders(), json={"snippet": {"title": name}, "status": {"privacyStatus": "public"}}, timeout=30).json()["id"]
        requests.post(YT + "playlistItems?part=snippet", headers=gheaders(), json={"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}, timeout=30)
        return True
    except Exception as e: log(f"playlist failed: {e}", "WARN"); return False

def yt_comment(vid, text):
    if FAKE or not text: return True
    try:
        cid = requests.get(YT + "channels?part=id&mine=true", headers=gheaders(), timeout=30).json()["items"][0]["id"]
        requests.post(YT + "commentThreads?part=snippet", headers=gheaders(), json={"snippet": {"channelId": cid, "videoId": vid,
                      "topLevelComment": {"snippet": {"textOriginal": text}}}}, timeout=30)
        return True
    except Exception as e: log(f"comment failed: {e}", "WARN"); return False

def yt_set_privacy(vid, privacy):
    if FAKE: return True
    r = requests.get(YT + f"videos?part=status&id={vid}", headers=gheaders(), timeout=30).json()
    if not r.get("items"): return False
    stt = r["items"][0]["status"]; stt["privacyStatus"] = privacy; stt.pop("publishAt", None)
    rr = requests.put(YT + "videos?part=status", headers=gheaders(), json={"id": vid, "status": stt}, timeout=30)
    if rr.status_code >= 400: log(f"privacy change failed {rr.status_code}: {rr.text[:300]}", "WARN"); return False
    return True

def yt_schedule(vid, publish_at):
    """Put a held (private) video back on the schedule at a new time."""
    if FAKE: return True
    r = requests.get(YT + f"videos?part=status&id={vid}", headers=gheaders(), timeout=30).json()
    if not r.get("items"): raise RuntimeError(f"video {vid} not found")
    stt = r["items"][0]["status"]; stt["privacyStatus"] = "private"; stt["publishAt"] = publish_at
    rr = requests.put(YT + "videos?part=status", headers=gheaders(), json={"id": vid, "status": stt}, timeout=30)
    if rr.status_code >= 400: raise RuntimeError(f"reschedule failed {rr.status_code}: {rr.text[:300]}")
    return True

def yt_status(vid):
    if FAKE: return "public"
    r = requests.get(YT + f"videos?part=status&id={vid}", headers=gheaders(), timeout=30).json()
    return (r.get("items") or [{}])[0].get("status", {}).get("privacyStatus")

def yt_views(vid):
    """v8.5: public view count of one video (1 quota unit). None if it cannot be read."""
    if FAKE: return None
    try:
        r = requests.get(YT + f"videos?part=statistics&id={vid}", headers=gheaders(), timeout=30).json()
        return int((r.get("items") or [{}])[0].get("statistics", {}).get("viewCount"))
    except Exception as e: log(f"view count failed for {vid}: {e}", "WARN"); return None

def yt_set_title(vid, title):
    """v8.5: change ONLY the title of a published video (the packaging rescue). The rest of the snippet is sent back exactly as YouTube returned it."""
    if FAKE: return True
    r = requests.get(YT + f"videos?part=snippet&id={vid}", headers=gheaders(), timeout=30).json()
    if not r.get("items"): return False
    sn = r["items"][0]["snippet"]
    t, _, _ = clean_meta(title, "", [])
    body = {"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "tags", "categoryId", "defaultLanguage", "defaultAudioLanguage") if k in sn}}
    body["snippet"]["title"] = t
    rr = requests.put(YT + "videos?part=snippet", headers=gheaders(), json=body, timeout=30)
    if rr.status_code >= 400: log(f"title change failed {rr.status_code}: {rr.text[:300]}", "WARN"); return False
    return True

def yt_channel():
    r = requests.get(YT + "channels?part=snippet,status,statistics&mine=true", headers=gheaders(), timeout=30).json()
    return (r.get("items") or [{}])[0]

# ---------------- Google Drive (public link for Meta + archive) ----------------
def _fake_drive(): d = os.path.join(WORK, "_drive"); os.makedirs(d, exist_ok=True); return d

def drive_upload(path, name, public=False):
    if FAKE:      # rehearsal: a local folder stands in for Drive, so checkpoints and fixes can be tested end to end
        import shutil; shutil.copyfile(path, os.path.join(_fake_drive(), name)); return name, "https://example.invalid/" + name
    h = gdrive_headers(); meta = {"name": name}
    if S("DRIVE_FOLDER_ID"): meta["parents"] = [S("DRIVE_FOLDER_ID")]
    mime = ("video/mp4" if path.endswith(".mp4") else "image/jpeg" if path.endswith(".jpg") else "audio/mpeg" if path.endswith(".mp3")
            else "text/plain" if path.endswith((".srt", ".md")) else "application/json")
    h.update({"Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": mime})
    r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable", headers=h, json=meta, timeout=60)
    r.raise_for_status()
    rr = requests.put(r.headers["Location"], headers={"Authorization": gdrive_headers()["Authorization"]}, data=open(path, "rb"), timeout=1800)
    rr.raise_for_status(); fid = rr.json()["id"]
    if public:
        requests.post(f"https://www.googleapis.com/drive/v3/files/{fid}/permissions", headers=gdrive_headers(), json={"role": "reader", "type": "anyone"}, timeout=30)
    return fid, f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"

def drive_download(fid, path):
    if FAKE:
        import shutil; src = os.path.join(_fake_drive(), str(fid))
        if not os.path.exists(src): raise RuntimeError("fake mode: no such drive file")
        shutil.copyfile(src, path); return path
    with requests.get(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media", headers=gdrive_headers(), stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for c in r.iter_content(1 << 20): f.write(c)
    return path

def drive_delete(fid):
    if FAKE:
        try: os.remove(os.path.join(_fake_drive(), str(fid)))
        except OSError: pass
        return
    try: requests.delete(f"https://www.googleapis.com/drive/v3/files/{fid}", headers=gdrive_headers(), timeout=30)
    except Exception: pass

def drive_private(fid):
    if FAKE: return
    try:
        p = requests.get(f"https://www.googleapis.com/drive/v3/files/{fid}/permissions", headers=gdrive_headers(), timeout=30).json()
        for x in p.get("permissions", []):
            if x.get("type") == "anyone": requests.delete(f"https://www.googleapis.com/drive/v3/files/{fid}/permissions/{x['id']}", headers=gdrive_headers(), timeout=30)
    except Exception: pass

# ---------------- Instagram + Facebook ----------------
def _meta_key(): return env("META_PAGE_KEY")
def MH(): return {"Authorization": "Bearer " + _meta_key()}
def _rupload(url, path):
    """v8.9.1: send the file's bytes straight to Meta's upload host (no public Drive link needed). True on success."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r = requests.post(url, headers={"Authorization": "OAuth " + _meta_key(), "offset": "0", "file_size": str(size)}, data=f, timeout=900)
    try: j = r.json()
    except Exception: j = {}
    if r.status_code >= 400 or j.get("success") is False: raise RuntimeError(f"Meta upload {r.status_code}: {str(j or r.text)[:200]}")
    return True

def _ig_finish(ig, cid):
    for _ in range(60):
        s = requests.get(gv() + cid, headers=MH(), params={"fields": "status_code,status"}, timeout=30).json()
        if s.get("status_code") == "FINISHED": break
        if s.get("status_code") == "ERROR": raise RuntimeError(f"IG processing: {s}")
        time.sleep(10)
    p = requests.post(gv() + f"{ig}/media_publish", headers=MH(), data={"creation_id": cid}, timeout=60).json()
    if "id" not in p: raise RuntimeError(f"IG publish: {p}")
    return p["id"]

def ig_reel(video_url, caption, cover_url=None, video_path=None, url_fn=None):
    """Instagram Reel. v8.9.1: with video_path the file is sent directly (Instagram's resumable upload), so Meta never has to fetch it from a Drive
    link (Drive can answer crawlers with an HTML page). Only if that fails is a public link used (url_fn makes it on demand; the caller makes it private)."""
    if FAKE: return "FAKE_IG"
    ig = S("IG_USER_ID")
    if not ig: raise RuntimeError("IG_USER_ID missing")
    base = {"media_type": "REELS", "caption": caption[:2100], "share_to_feed": "true"}
    if cover_url: base["cover_url"] = cover_url
    if video_path and os.path.exists(video_path):
        try:
            c = requests.post(gv() + f"{ig}/media", headers=MH(), data=dict(base, upload_type="resumable"), timeout=60).json()
            if "id" not in c: raise RuntimeError(f"IG container: {c}")
            _rupload(c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{graph_version()}/{c['id']}", video_path)
            return _ig_finish(ig, c["id"])
        except Exception as e:
            if not (video_url or url_fn): raise
            log(f"IG direct upload failed ({str(e)[:160]}) - trying the link upload", "WARN")
    video_url = video_url or (url_fn() if url_fn else None)
    if not video_url: raise RuntimeError("IG: no file and no link to upload")
    c = requests.post(gv() + f"{ig}/media", headers=MH(), data=dict(base, video_url=video_url), timeout=60).json()
    if "id" not in c: raise RuntimeError(f"IG container: {c}")
    return _ig_finish(ig, c["id"])

def fb_reel(video_url, description, video_path=None, url_fn=None):
    """Facebook Reel. v8.9.1: the file's bytes go straight to rupload.facebook.com; a public link (url_fn) is only the fallback."""
    if FAKE: return "FAKE_FB"
    page = S("FB_PAGE_ID"); k = _meta_key()
    s = requests.post(gv() + f"{page}/video_reels", headers=MH(), data={"upload_phase": "start"}, timeout=60).json()
    vid = s.get("video_id")
    if not vid: raise RuntimeError(f"FB start: {s}")
    up = s.get("upload_url") or f"https://rupload.facebook.com/video-upload/{graph_version()}/{vid}"
    done = False
    if video_path and os.path.exists(video_path):
        try: done = _rupload(up, video_path)
        except Exception as e:
            if not (video_url or url_fn): raise
            log(f"FB direct upload failed ({str(e)[:160]}) - trying the link upload", "WARN")
    if not done:
        video_url = video_url or (url_fn() if url_fn else None)
        if not video_url: raise RuntimeError("FB: no file and no link to upload")
        u = requests.post(up, headers={"Authorization": "OAuth " + k, "file_url": video_url}, timeout=300).json()
        if not u.get("success", True): raise RuntimeError(f"FB upload: {u}")
    f = requests.post(gv() + f"{page}/video_reels", data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                      "description": description[:2000]}, headers=MH(), timeout=60).json()
    if not f.get("success"): raise RuntimeError(f"FB finish: {f}")
    _fb_wait(vid)
    return vid

def _fb_wait(vid, tries=60):
    """Wait until Facebook has fetched and processed the file, so the Drive link can be made private safely."""
    for _ in range(tries):
        try:
            s = requests.get(gv() + str(vid), headers=MH(), params={"fields": "status"}, timeout=30).json()
        except Exception as e:
            log(f"FB status check failed: {e}", "WARN"); time.sleep(10); continue
        st = s.get("status") or {}
        vs = st.get("video_status"); ph = (st.get("processing_phase") or {}).get("status"); up = (st.get("uploading_phase") or {}).get("status")
        if vs in ("ready", "published") or ph == "complete": return True
        if "error" in (vs, ph, up): raise RuntimeError(f"FB processing: {s}")
        time.sleep(10)
    log("FB reel still processing after 10 min - continuing", "WARN"); return False

def meta_bio(text):
    """Bio link isn't API-editable on Instagram; we keep a pinned YouTube link in captions instead."""
    return False

# ---------------- email (Gmail API, from your own account) ----------------
def email(subject, html, kind="essential"):
    """kind='essential' always goes out; kind='info' only when EMAIL_LEVEL = all."""
    if kind == "info" and S("EMAIL_LEVEL").strip().lower() not in ("all", "full", "everything"):
        log(f"EMAIL skipped (EMAIL_LEVEL minimal): {subject}"); return False
    to = S("OPERATOR_EMAIL")
    if FAKE or not to:
        log(f"EMAIL (not sent): {subject}"); return False
    m = email_mime(to, subject, html)
    r = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers=gheaders(),
                      json={"raw": base64.urlsafe_b64encode(m.as_bytes()).decode()}, timeout=60)
    if r.status_code >= 400: log(f"email failed {r.status_code}: {r.text[:200]}", "WARN"); return False
    return True

def email_mime(to, subject, html):
    m = MIMEMultipart("alternative"); m["To"] = to; m["Subject"] = "[Reality Engine] " + subject
    m.attach(MIMEText(html, "html")); return m

