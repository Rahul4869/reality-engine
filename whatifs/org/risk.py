"""The watch book (D1): a danger has an owner, a measure and an act the same day; WATCH is data. See docs/CURRENT/SYSTEM.md."""
# v12 V4 (items 52 and 65 (c)): rows {id, owner, measure, act}; `run` (called by Strategy's review) writes one `watch` row a danger and fixed point,
# acts (a lock, a message or a memo to the owner department) and clears the danger itself at the next fixed point at which it no longer fires.
from __future__ import annotations
import datetime as dt, json, statistics
from whatifs.core import S, log, store, iso, now_utc, parse_iso, set_setting, scrub, FAKE

def on(): return S("STRATEGY_ON", bool)

def _rows(st): return [r for r in st.rows("Decisions") if r.get("rule") == "WATCH"]

def _js(v, d):
    try: x = json.loads(v) if isinstance(v, str) and v.strip() else (v if v else d)
    except (TypeError, ValueError): x = d
    return x if isinstance(x, type(d)) else d

# ------------------------------------------------------------------ platform_flag (D9): what YouTube's own record says of our newest uploads
def _uploads(st, n):
    """[(yt_id, title, when)] of the newest n uploads: Episodes rows at LIVE and Specials rows with a yt_id."""
    out = [(e["yt_id"], str(e.get("title") or e.get("episode_id") or ""), str(e.get("slot_et") or "")) for e in st.rows("Episodes") if e.get("status") == "LIVE" and e.get("yt_id")]
    out += [(r["yt_id"], str(r.get("title") or r.get("id") or ""), str(r.get("made") or r.get("ts") or "")) for r in st.rows("Specials") if r.get("yt_id")]
    return sorted(out, key=lambda x: x[2])[-n:]

def _video_states(ids):
    """{id: {upload, reason, rating, blocked}} from ONE free videos.list (part status,contentDetails); None when the request fails (never a flag)."""
    if not ids: return {}
    if FAKE:
        from whatifs import fakes as FK
        return FK.video_states(ids)
    try:
        import requests
        from whatifs import publish
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "status,contentDetails", "id": ",".join(ids)}, headers=publish.gheaders(), timeout=30)
        if r.status_code >= 300: raise RuntimeError(f"HTTP {r.status_code}")
        out = {}
        for it in (r.json() or {}).get("items") or []:
            stt, cd = it.get("status") or {}, it.get("contentDetails") or {}
            out[it["id"]] = {"upload": stt.get("uploadStatus"), "reason": stt.get("rejectionReason") or stt.get("failureReason") or "",
                             "rating": (cd.get("contentRating") or {}).get("ytRating") or "", "blocked": (cd.get("regionRestriction") or {}).get("blocked") or []}
        return out
    except Exception as e:
        log(f"watch book: YouTube's record of our uploads was not read ({scrub(e)[:120]}) - no flag from a failed read", "WARN"); return None

def platform_flag(now=None, st=None):
    """REJECTED (uploadStatus rejected, with its reason), GONE (absent from an answer that holds other ids, or deleted), LIMITED (age-restricted or
    blocked somewhere). One finding a video; the fixed point is the video's id."""
    st = st or store(); ups = _uploads(st, S("RISK_UPLOADS_N", int)); states = _video_states([u[0] for u in ups])
    if states is None: return []
    out = []
    for vid, title, _w in ups:
        s = states.get(vid)
        if s is None:
            if states: out.append({"fires": True, "point": vid, "kind": "gone", "title": title, "why": f"{title} is gone from YouTube", "numbers": {"vid": vid}})
            continue
        if s.get("upload") == "rejected":
            out.append({"fires": True, "point": vid, "kind": "rejected", "title": title, "why": f"YouTube rejected {title} ({s.get('reason') or 'no reason given'})", "numbers": {"vid": vid, "reason": s.get("reason")}})
        elif s.get("upload") == "deleted":
            out.append({"fires": True, "point": vid, "kind": "gone", "title": title, "why": f"{title} is gone from YouTube", "numbers": {"vid": vid}})
        elif s.get("rating") == "ytAgeRestricted" or s.get("blocked"):
            how = "age-restricted" if s.get("rating") == "ytAgeRestricted" else f"blocked in {len(s.get('blocked'))} countries"
            out.append({"fires": True, "point": vid, "kind": "limited", "title": title, "why": f"YouTube {how} {title}. Nothing was closed", "numbers": {"vid": vid}})
    return out

def lock(vid, why, now=None, title=""):
    """Close the uploads (UPLOAD_LOCK on) and say so in its own true words, with one tap that opens them again. Never launch.lock_detected (its mail
    speaks of private uploads and an audit form, and no tap opens its lock)."""
    from whatifs import notify as NT
    set_setting("UPLOAD_LOCK", "on")
    head = (f"The uploads are closed: {title or vid} is gone from YouTube and you did not say that you deleted it." if str(why).startswith("gone")
            else f"The uploads are closed: {why}.")
    return NT.send("risk_lock", head + " Look at it in Studio first - the next violation inside 90 days is a strike. One tap opens the uploads again.",
                   [("Open the uploads", f"RISK OPEN {vid}")], tier="now", urgent=True, dedupe_key=f"risk_lock|{vid}")

def _act_platform(f, now, st):
    from whatifs import notify as NT
    if f["kind"] == "rejected": lock(f["point"], f["why"], now, f["title"])
    elif f["kind"] == "gone":
        NT.send("risk_gone", f"A video is gone from YouTube: {f['title']}. If you deleted it, tap I deleted it. If you did not, YouTube removed it: the uploads close in "
                f"{S('RISK_GONE_WAIT_H', int)} hours so that the next video cannot become a strike.",
                [("I deleted it", f"RISK MINE {f['point']}"), ("Close the uploads now", f"RISK CLOSE {f['point']}")], tier="now", urgent=True,
                default="the uploads close", expires_h=S("RISK_GONE_WAIT_H", float), dedupe_key=f"risk_gone|{f['point']}")
    return None                                                                          # LIMITED: the watch row's line is the act

# ------------------------------------------------------------------ repetition (D4), upload_mix (D9), pace_slip (D14)
def repetition(now=None, st=None):
    """The newest RISK_SIM_N scripts, each against the ten before it: the median of their highest likeness at or above RISK_SIMILAR_PCT percent of the
    originality limit - the scripts converge BEFORE one is held. Fixed point: each new fingerprint."""
    from whatifs import similarity as SIM
    st = st or store(); fp = st.rows("Script_Fingerprints"); n = S("RISK_SIM_N", int)
    if len(fp) < n + 1: return []
    def sig(r):
        try: return [int(x) for x in str(r.get("sig") or "").split(",") if x]
        except ValueError: return []
    pairs = []
    for i in range(len(fp) - n, len(fp)):
        best, who = 0.0, ""
        for o in fp[max(0, i - 10):i]:
            s = SIM.similarity(sig(fp[i]), sig(o))
            if s > best: best, who = s, o.get("episode_id")
        pairs.append((fp[i].get("episode_id"), who, round(best, 3)))
    med = statistics.median(p[2] for p in pairs); lim = S("RISK_SIMILAR_PCT", float) / 100.0 * S("SCRIPT_SIMILARITY_MAX", float)
    return [{"fires": med >= lim, "point": str(fp[-1].get("episode_id") or len(fp)), "kind": "repetition_trend",
             "why": f"the last {n} scripts are converging: a median likeness of {med:.2f} to the ten before each (the originality check holds at {S('SCRIPT_SIMILARITY_MAX', float):.2f})",
             "numbers": {"pairs": pairs, "median": med, "limit": lim}}]

def upload_mix(now=None, st=None):
    """Short uploads of 28 days above RISK_SHORTS_28D_MAX - an older door is on, or a hand raised the cadence. Fixed point: each ISO week."""
    from whatifs.org import strategy as STR
    st = st or store(); now = now or now_utc(); lo = now - dt.timedelta(days=28); _lg, sh = STR.uploads(now, 28, st)
    kinds = {}
    for r in st.rows("Specials"):
        t = parse_iso(r.get("made") or r.get("ts"))
        if r.get("yt_id") and t and lo <= t <= now: kinds[r.get("kind") or "?"] = kinds.get(r.get("kind") or "?", 0) + 1
    wk = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
    return [{"fires": sh > S("RISK_SHORTS_28D_MAX", int), "point": wk, "kind": "upload_mix",
             "why": f"{sh} short uploads in 28 days (more than {S('RISK_SHORTS_28D_MAX', int)}): " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())),
             "numbers": {"short": sh, "kinds": kinds}}]

def pace_slip(now=None, st=None):
    """The Ladder's measured Shorts in publishing order, judged ONLY when their count is a multiple of PACE_N and at least 12 (a fixed point): the
    median of the last six fell by PACE_DROP_PCT against the six before, which held at least PACE_MIN_ENGAGED."""
    from whatifs.org import strategy as STR
    xs = [v for _a, _t, v in STR.short_items(st)]; n = S("PACE_N", int)
    if len(xs) < 2 * n or len(xs) % n: return []
    a, b = statistics.median(xs[-n:]), statistics.median(xs[-2 * n:-n])
    fires = b >= S("PACE_MIN_ENGAGED", float) and a < (1 - S("PACE_DROP_PCT", float) / 100.0) * b
    return [{"fires": fires, "point": str(len(xs)), "kind": "pace_slip", "why": f"the last six Shorts held a median of {a:.0f} viewers who stayed against {b:.0f} for the six before",
             "numbers": {"last": a, "prev": b, "count": len(xs)}}]

WATCH = (
    {"id": "platform_flag", "owner": "D9", "measure": platform_flag, "memo": False},
    {"id": "repetition", "owner": "D4", "measure": repetition, "memo": True},
    {"id": "upload_mix", "owner": "D9", "measure": upload_mix, "memo": True},
    {"id": "pace_slip", "owner": "D14", "measure": pace_slip, "memo": True},
)

# ------------------------------------------------------------------ the pass
def _row(w, f, state, why, now):
    from whatifs.org import strategy as STR
    return {"id": STR._did("WATCH", w["id"], str(f["point"]), state, now), "ts": iso(now), "rule": "WATCH", "key": w["id"], "old": "", "new": str(f["point"])[:80], "why": str(why)[:500],
            "numbers": json.dumps(dict(f.get("numbers") or {}, kind=f.get("kind"), dedupe=f"{w['id']}|{f['point']}"), default=str), "effect_before": "", "effect_after": "",
            "prediction": "", "ticket": "", "state": state, "told": "", "frozen_until": "", "observed": "", "scored": "", "briefed": ""}

def run(now=None, st=None):
    """(rows written, memos for Strategy's Out.memos). A danger that fires at a fixed point with no `watch` row yet gets its row and its act; at the next
    fixed point at which it no longer fires, a `judged` row 'cleared' is written and its one live memo is closed by the watch itself."""
    from whatifs.org import memos as MEM
    if not on(): return 0, []
    st = st or store(); now = now or now_utc(); rows = _rows(st); out, n = [], 0
    for w in WATCH:
        try: found = w["measure"](now, st) or []
        except Exception as e: log(f"watch book: {w['id']} could not be read: {scrub(e)[:140]}", "WARN"); continue
        mine = [r for r in rows if r["key"] == w["id"]]; seen = {str(r.get("new")) for r in mine}
        for f in found:
            if str(f["point"])[:80] in seen: continue
            if f["fires"]:
                row = _row(w, f, "watch", f["why"], now); st.append("Decisions", [row]); rows.append(row); n += 1
                if w["id"] == "platform_flag": _act_platform(f, now, st)
                elif w["memo"]:
                    att = 1 + sum(1 for r in mine if r["state"] == "watch")
                    out.append({"type": "problem_memo", "from_dept": "D1", "to_depts": [w["owner"]], "owner_visible": False, "subject": f"Risk: {f['why']}"[:140],
                                "body": {"what_failed": f["why"][:400], "where": f"Decisions:{row['id']}", "attempt": att, "error_class": f["kind"]},
                                "evidence": [{"source": f"Decisions:{row['id']}", "date": iso(now)[:10], "type": "own data", "finding": f["why"][:600]}],
                                "dedupe_key": f"risk|{w['id']}", "done_when": f"the watch's next reading of {w['id']} no longer fires"})
            elif w["memo"]:
                live = [m for m in MEM.find(st, type="problem_memo", from_dept="D1") if m.get("dedupe_key") == f"risk|{w['id']}"]
                if not live: continue
                row = _row(w, f, "judged", f"{w['id']} cleared: {f['why']}", now); st.append("Decisions", [row]); rows.append(row); n += 1
                for m in live:
                    try: MEM.resolve(m["id"], "D1", "repair_verified", f"Decisions:{row['id']}", "the watch's next reading no longer fires", st, now)
                    except Exception as e: log(f"watch book: the memo of {w['id']} was not closed: {scrub(e)[:120]}", "WARN")
    return n, out

def words(now=None):
    """The watch book's words for Strategy's weekly line: the dangers it saw this week ('' = none)."""
    st = store(); now = now or now_utc()
    wk = [r for r in _rows(st) if r["state"] == "watch" and (parse_iso(r.get("ts")) or now) > now - dt.timedelta(days=7)]
    return ("Watch: " + "; ".join(r["why"] for r in wk[-3:]) + ".") if wk else ""

# ------------------------------------------------------------------ his taps
def _vid(choice): parts = str(choice or "").split(); return parts[2] if len(parts) >= 3 else ""

def _title(vid):
    r = next((r for r in _rows(store()) if r["key"] == "platform_flag" and str(r.get("new")) == vid and str(r.get("why")).endswith(" is gone from YouTube")), None)
    return r["why"][:-len(" is gone from YouTube")] if r else vid

def _open(row, choice):
    vid = _vid(choice); set_setting("UPLOAD_LOCK", "off"); st = store()
    for r in _rows(st):
        if r["key"] == "platform_flag" and str(r.get("new")) == vid:
            st.update("Decisions", "id", r["id"], {"numbers": json.dumps(dict(_js(r.get("numbers"), {}), opened=iso()))})
    return "the uploads are open"

def _gone(row, choice):
    vid = _vid(choice); c = str(choice or "").upper()
    if c.startswith("RISK MINE"):
        from whatifs.org import strategy as STR
        st = store(); now = now_utc()
        row = _row({"id": "platform_flag"}, {"point": vid, "kind": "his_delete", "numbers": {"vid": vid}}, "watch", "his own delete", now)
        row["id"] = STR._did("WATCH", "platform_flag", vid, "mine", now); st.append("Decisions", [row])
        return "noted: you deleted it - nothing was closed"
    if c.startswith("RISK CLOSE"): lock(vid, "gone", title=_title(vid)); return "the uploads are closed"
    return "recorded"

def _gone_default(row):
    vid = _vid(next((v for _l, v in json.loads(row.get("buttons") or "[]") if str(v).upper().startswith("RISK CLOSE")), ""))
    if vid: lock(vid, "gone", title=_title(vid))

def register():
    from whatifs import notify as NT
    NT.register("risk_lock", on_answer=_open)
    NT.register("risk_gone", on_answer=_gone, on_default=_gone_default)
