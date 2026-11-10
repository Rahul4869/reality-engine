"""Impressions and thumbnail click-through per video per day from the YouTube Reporting API. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import csv, io
from whatifs.core import S, log, store, iso, set_setting, FAKE, scrub, gheaders

YR = "https://youtubereporting.googleapis.com/v1"
REPORT = "channel_reach_basic_a1"

def ensure_job():
    """The job id (created once; reused from the Settings cell or found among existing jobs - a duplicate create is an error)."""
    jid = str(S("REACH_JOB_ID") or "").strip()
    if jid: return jid
    if FAKE: set_setting("REACH_JOB_ID", "fakejob"); return "fakejob"
    import requests
    h = gheaders()
    jobs = requests.get(f"{YR}/jobs", headers=h, timeout=30).json().get("jobs", [])
    jid = next((j["id"] for j in jobs if j.get("reportTypeId") == REPORT), None)
    if not jid:
        r = requests.post(f"{YR}/jobs", headers=h, json={"reportTypeId": REPORT, "name": "reality-engine-reach"}, timeout=30)
        if r.status_code >= 300: raise RuntimeError(f"reach job not created: {r.status_code} {r.text[:200]}")
        jid = r.json()["id"]; log("reach report job created (first file in about 48 hours)")
    set_setting("REACH_JOB_ID", jid)
    return jid

def _reports(jid, after):
    if FAKE:
        return [{"id": "r1", "createTime": "2026-11-11T08:00:00Z", "downloadUrl": "fake://r1"}]
    import requests
    p = {"createdAfter": after} if after else {}
    return requests.get(f"{YR}/jobs/{jid}/reports", headers=gheaders(), params=p, timeout=30).json().get("reports", [])

def _download(url):
    if FAKE:
        return "date,channel_id,video_id,video_thumbnail_impressions,video_thumbnail_impressions_ctr\n20261110,UC1,fakeA,1200,0.054\n20261110,UC1,,50,0.02\n"
    import requests
    r = requests.get(url, headers=gheaders(), timeout=120); r.raise_for_status(); return r.text

def parse(text):
    """Rows {date, video_id, impressions, ctr} from one CSV; columns by name; deleted videos (empty id) skipped; CTR as a 0-1 fraction."""
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        vid = (row.get("video_id") or "").strip()
        if not vid: continue
        try:
            imp = int(float(row.get("video_thumbnail_impressions") or 0)); ctr = float(row.get("video_thumbnail_impressions_ctr") or 0)
        except ValueError: continue
        if ctr > 1: ctr = ctr / 100.0
        d = str(row.get("date") or "")
        out.append({"date": f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 and d.isdigit() else d, "video_id": vid, "impressions": imp, "ctr": round(ctr, 5)})
    return out

def daily():
    """Create the job if needed, download every new daily file, upsert into the Reach tab. Returns the number of rows written."""
    if not S("REACH_ON", bool): return 0
    try:
        jid = ensure_job()
        st = store(); have = {(r.get("date"), r.get("video_id")): r for r in st.rows("Reach")}
        after = str(S("REACH_LAST_CREATED") or "")
        reps = sorted(_reports(jid, after), key=lambda r: r.get("createTime", ""))
        n = 0
        for rep in reps:
            for row in parse(_download(rep["downloadUrl"])):
                key = (row["date"], row["video_id"]); row["updated"] = iso(); row["key"] = f"{row['date']}|{row['video_id']}"
                if key in have: st.update("Reach", "key", row["key"], row)            # a re-delivered day overwrites
                else: st.append("Reach", [row]); have[key] = row
                n += 1
            set_setting("REACH_LAST_CREATED", rep.get("createTime", ""))
        if n: log(f"reach: {n} rows (impressions + CTR) from {len(reps)} file(s)")
        return n
    except Exception as e:
        log(f"reach report skipped: {scrub(e)[:160]}", "WARN"); return 0

def ctr(video_id, days=None):
    """Impression-weighted CTR for one video (all stored days, or the first `days` days). None when there is no data yet."""
    rows = sorted([r for r in store().rows("Reach") if r.get("video_id") == video_id], key=lambda r: r.get("date", ""))
    if days: rows = rows[:days]
    imp = sum(int(r.get("impressions") or 0) for r in rows)
    if not imp: return None
    return sum(int(r.get("impressions") or 0) * float(r.get("ctr") or 0) for r in rows) / imp
