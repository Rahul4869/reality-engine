"""The phone dashboard's data snapshot and its taps (never contains secrets, scripts or unreleased premises). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import base64, datetime as dt, json, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, set_setting, scrub, FAKE

MODE_IDS = {"lean": "runway", "runway": "runway", "standard": "standard", "growth": "growth"}
SETTINGS_MAP = {"shorts_per_week": ("SHORTS_PER_WEEK", "week"),   # v12 V2c-b: standalone Shorts a week, 1 to 5 (the owner's own tap) "localizations": ("LOCALIZATIONS_ON", "bool"), "affiliate_block": ("AFFILIATE_ON", "bool"),
                "native_test_reminder": ("NATIVE_TEST_REMINDER_ON", "bool"), "visual_lab": ("VISUAL_LAB_ON", "bool"), "facts_watch": ("FACTS_WATCH_ON", "bool")}

# ------------------------------------------------------------------ snapshot
def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

def _docket():
    from whatifs import packaging as PK
    st = store(); cards = []
    for r in st.rows("Owner_Actions"):
        if r.get("status") not in ("OPEN", "QUEUED") or r.get("tier") == "fyi": continue
        btns = json.loads(r.get("buttons") or "[]")
        kind = r.get("kind"); verbs = {}
        if kind == "build_ready":
            m = re.search(r"#(\d+)", r.get("text", "")); n = m.group(1) if m else ""
            verbs = {"Merge now": f"MERGE|{n}", "Reject": f"REJECT|{n}"}; kind = "merge"
        else:
            verbs = {str(lbl)[:24]: f"ACT|{r['id']}|{i}" for i, (lbl, _v) in enumerate(btns)}
        exp = parse_iso(r.get("expires_at")); created = parse_iso(r.get("created"))
        cards.append({"id": r["id"], "kind": kind, "title": re.sub(r"<[^>]+>", "", r.get("text", ""))[:90], "why": re.sub(r"<[^>]+>", "", r.get("text", ""))[:400],
                      "default_label": r.get("default_action") or "Nothing happens", "default_at": r.get("expires_at") or "",
                      "window_h": round((exp - created).total_seconds() / 3600) if exp and created else 0, "verbs": verbs})
    # title/thumbnail picks still open (before the 2-hour freeze)
    eps = {e.get("episode_id"): e for e in st.rows("Episodes")}
    by = {}
    for r in st.rows("Packaging_Tests"): by.setdefault(r.get("episode_id"), []).append(r)
    for ep, rows in by.items():
        if any(r.get("picked_by") == "owner" for r in rows): continue
        dl = PK.pick_deadline(ep)
        if not dl or now_utc() >= dl: continue
        e = eps.get(ep) or {}
        cards.append({"id": f"pick-{ep}", "kind": "pick", "title": "Pick the cover for " + str(e.get("title") or ep)[:60],
                      "why": "Three title and thumbnail pairs are ready. A is scheduled; your pick switches it before release.",
                      "default_label": "A goes out", "default_at": dl.strftime("%Y-%m-%dT%H:%M:%SZ"), "window_h": 34,
                      "options": [{"key": r.get("variant"), "label": str(r.get("title") or "")[:90], "detail": "", "thumb_text": str(r.get("thumb_text") or "")[:24],
                                   "hue": [20 + 60 * i, 200 + 20 * i]} for i, r in enumerate(sorted(rows, key=lambda x: x.get("variant", "")))],
                      "verbs": {"pick": f"PICK|{ep}|{{key}}"}})
    for r in st.rows("Character_Sheets"):
        if r.get("status") == "DRAFT":
            ch = r.get("character")
            if not any(c["id"] == f"sheets-{ch}" for c in cards):
                cards.append({"id": f"sheets-{ch}", "kind": "sheets", "title": f"Lock {str(ch).title()}'s portraits",
                              "why": "Locked portraits let this character appear on thumbnails and in scenes, always the same face.",
                              "default_label": "Locks by itself after 72 h", "default_at": "", "window_h": 72,
                              "verbs": {"Lock these": f"LOCKSHEETS|{ch}", "Redo": f"REDOSHEETS|{ch}"}})
    return cards

def _progress():
    rows = store().rows("Analytics")
    views = sum(_f(r.get("views")) for r in rows)
    hours = sum(_f(r.get("views")) * _f(r.get("avg_view_sec")) for r in rows) / 3600
    def avg(k, scale=1.0):
        v = [_f(r.get(k), None) for r in rows if r.get(k) not in (None, "")]
        v = [x for x in v if x is not None]
        return round(sum(v) / len(v) * scale, 2) if v else 0
    subs = sum(_f(r.get("subs")) for r in rows)
    k = {"ctr": {"v": avg("ctr"), "unit": "%", "label": "Click-through", "good": "4–8% is healthy", "trend": "flat"},
         "rel30": {"v": avg("ret30"), "unit": "", "label": "30-s hold", "good": "higher is better", "trend": "flat"},
         "apv": {"v": avg("avg_view_pct"), "unit": "%", "label": "Average % watched", "good": "35–45% is solid", "trend": "flat"},
         "stay": {"v": 0, "unit": "%", "label": "Shorts kept past the swipe", "good": "70%+ is strong", "trend": "flat"},
         "subs1k": {"v": round(subs / views * 1000, 2) if views else 0, "unit": "", "label": "Subs per 1,000 views", "good": "rising is the goal", "trend": "flat"},
         "hours_week": {"v": round(hours, 1), "unit": " h", "label": "Watch hours (all videos)", "good": "1,000 subs + 8,000 h unlocks ads (from 1 Feb 2027)", "trend": "flat"}}
    return {"subs": int(subs), "watch_hours": round(hours), "shorts_views_90d": int(sum(_f(r.get("shorts_views")) for r in rows)),
            "old_bar_deadline": "2027-01-31", "series_14d": [], "kpis": k}

def _money():
    from whatifs import governor as G
    try:
        from whatifs.costguard import month_spend
        spent = month_spend()
    except Exception: spent = 0.0
    mk = now_utc().strftime("%Y-%m"); lines = {}
    groups = [("Writers' room", ("writer", "memo", "objection", "critic", "bible", "showrunner", "scout", "punchup", "editor", "hook", "rewrite", "humanize")),
              ("Pictures", ("image", "still", "flux", "fal_img", "thumb")), ("Kling clips", ("kling", "clip", "hero")), ("Voices", ("tts", "voice")),
              ("Faces", ("faces",)), ("Shorts Lab", ("shorts_lab", "pilot")), ("Research and ideas", ("research", "outlier", "advisor", "trend")), ("Your chats", ("owner_chat",))]
    for r in store().rows("Cost_Log"):
        if r.get("basis") == "summary" or not str(r.get("ts", "")).startswith(mk): continue
        key = f"{r.get('role') or ''} {r.get('item') or ''}".lower()
        label = next((g for g, ps in groups if any(p in key for p in ps)), "Other")
        lines[label] = lines.get(label, 0.0) + _f(r.get("inr"))
    rev = {"affiliate": 0, "ads": None, "clients": 0}
    for r in store().rows("Revenue_Log"):
        if str(r.get("month", "")).startswith(mk):
            src = str(r.get("source") or "").lower(); key = "affiliate" if "affil" in src else ("ads" if "ad" in src or "youtube" in src else "clients")
            rev[key] = (rev[key] or 0) + _f(r.get("inr_received"))
    return {"month_spend": round(spent), "cap": round(G.cap_inr()), "credit_cover": round(G.credit_cover_inr()),
            "lines": [{"label": k, "inr": round(v)} for k, v in sorted(lines.items(), key=lambda x: -x[1])], "revenue": rev,
            "modes": [{"id": "lean", "name": "Runway", "cost": round(S("RUNWAY_CAP_INR", float)), "text": "One long case a week (Saturdays), Shorts kept, smaller research and chat caps."},
                      {"id": "standard", "name": "Standard", "cost": round(S("BUDGET_CEILING_INR", float)), "text": "Two long cases a week (Tue + Sat), the full Shorts Lab, faces, research and chat."},
                      {"id": "growth", "name": "Growth", "cost": None, "text": "Standard plus a share of last month's revenue. Switches on by itself when revenue arrives."}]}

def _health():
    try:
        from whatifs import caretaker as CT
        return {"expiring": CT.expiring(), "last_runs": CT.last_runs()}
    except Exception: return {"expiring": [], "last_runs": []}

def _lab():
    try:
        from whatifs import microscope as MS
        rules = MS.active_rules()
    except Exception: rules = []
    fmt = lambda r: {"text": str(r.get("text"))[:140], "effect": f"{float(r.get('effect') or 0) * 100:+.0f}% vs usual", "videos": int(float(r.get("videos") or 0))}
    return {"experiments": [], "boosters": [fmt(r) for r in rules if r.get("kind") == "booster"][:4], "killers": [fmt(r) for r in rules if r.get("kind") == "killer"][:4]}

def build_snapshot():
    from whatifs import governor as G, launch as LA
    from whatifs.manage import paused, next_slots
    st = store(); eps = st.rows("Episodes")
    nxt = sorted([e for e in eps if parse_iso(e.get("slot_et")) and parse_iso(e.get("slot_et")) > now_utc()], key=lambda e: e.get("slot_et"))
    nr = nxt[0] if nxt else None
    if not nr:
        try: s = next_slots(1)[0]; nr = {"episode_id": "", "title": "next episode (not written yet)", "slot_et": s.strftime("%Y-%m-%dT%H:%M:%SZ")}
        except Exception: nr = None
    mode = G.budget_mode()
    lessons = [{"text": str(r.get("lesson"))[:200], "confidence": "medium", "loop": "medium"} for r in st.rows("Lessons")[-5:]]
    rules = [{"text": str(r.get("rule"))[:200], "confidence": "high" if r.get("status") == "active" else "medium", "loop": "fast"} for r in st.rows("Playbook") if r.get("status") in ("active",)][-3:]
    two = (now_utc() - dt.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    acks = [{"verb": r.get("verb"), "at": r.get("ts"), "ok": str(r.get("ok")) == "TRUE", "note": str(r.get("note") or "")[:120]} for r in st.rows("Dash_Acks") if str(r.get("ts", "")) >= two]
    return {"generated_at": iso(),
            "engine": {"status": "paused" if paused() else "running", "mode": "lean" if mode == "runway" else mode, "owner_mode": "minimal",
                       "upload_lock": LA.lock_state() == "on",
                       "next_release": {"episode": nr.get("episode_id", ""), "title": str(nr.get("title") or "")[:90], "case_no": len([e for e in eps if e.get("yt_id")]) + 1,
                                        "slot_iso": nr.get("slot_et")} if nr else None},
            "docket": _docket(), "progress": _progress(), "learned": (rules + lessons)[-6:],
            "lab": _lab(), "money": _money(),
            "health": _health(),
            "settings": {"shorts_per_week": S("SHORTS_PER_WEEK", int),
                         "localizations": bool(S("LOCALIZATIONS_ON", bool)) if "LOCALIZATIONS_ON" in __import__("whatifs.core", fromlist=["DEFAULTS"]).DEFAULTS else False,
                         "visual_lab": bool(S("VISUAL_LAB_ON", bool)), "facts_watch": bool(S("FACTS_WATCH_ON", bool))},
            "acks": acks, "whatsapp": str(S("WA_BOT_NUMBER") or "")}

def publish():
    """Write the snapshot to Cloudflare KV. Quiet no-op until the dashboard is set up (no CF secrets) or DASH_ON is off."""
    if not S("DASH_ON", bool): return False
    acc, ns, tok = env("CF_ACCOUNT_ID"), env("CF_KV_NAMESPACE_ID"), env("CF_KV_TOKEN")
    if not (acc and ns and tok) or FAKE: return False
    import requests, hashlib, os
    base = f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{ns}/values/"
    page = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mission_control", "mission_control.html")
    if os.path.exists(page):                                       # the page itself (key app_html), only when it changed
        html = open(page, encoding="utf-8").read(); h = hashlib.sha256(html.encode()).hexdigest()[:16]
        if S("DASH_APP_HASH") != h:
            rp = requests.put(base + "app_html", headers={"Authorization": f"Bearer {tok}", "Content-Type": "text/html"}, data=html.encode(), timeout=30)
            if rp.status_code < 300: set_setting("DASH_APP_HASH", h)
    snap = build_snapshot()
    r = requests.put(f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{ns}/values/snapshot",
                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, data=json.dumps(snap, ensure_ascii=False).encode(), timeout=30)
    if r.status_code >= 300: log(f"dashboard snapshot not written ({r.status_code})", "WARN"); return False
    return True

# ------------------------------------------------------------------ taps
def decrypt(payload, key_b64=None):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.b64decode(key_b64 or env("WA_RELAY_KEY"))
    return json.loads(AESGCM(key).decrypt(base64.b64decode(payload["n"]), base64.b64decode(payload["c"]), None))

def _ack(aid, verb, ok, note):
    store().append("Dash_Acks", [{"ts": iso(), "id": str(aid)[:64], "verb": str(verb)[:120], "ok": "TRUE" if ok else "FALSE", "note": str(note)[:300]}])

def route(verb):
    """(ok, note) for one dashboard verb."""
    parts = str(verb).split("|"); head = parts[0]
    from whatifs import notify as NT, preview as PV, builds as BD
    BD.ensure_registered()
    if head == "PICK" and len(parts) == 3: return True, str(PV.decide(f"PICK {parts[1]} {parts[2]}"))
    if head == "MODE" and len(parts) == 2 and parts[1].lower() in MODE_IDS:
        m = MODE_IDS[parts[1].lower()]
        if m == "growth": return False, "Growth switches on by itself when revenue arrives"
        return True, str(PV.decide(f"MODE {m.upper()}"))
    if head in ("MERGE", "REJECT") and len(parts) == 2 and parts[1].isdigit():
        ok, msg = BD.merge_pr(parts[1], "dashboard tap") if head == "MERGE" else (BD.close_pr(parts[1]), f"closed #{parts[1]}")
        for r in NT.open_rows():
            if r.get("kind") == "build_ready" and f"#{parts[1]}" in r.get("text", ""):
                store().update("Owner_Actions", "id", r["id"], {"status": "ANSWERED", "answered_at": iso(), "answer": head, "channel": "dash"})
        return bool(ok), msg
    if head == "ACT" and len(parts) == 3:
        row = next((r for r in store().rows("Owner_Actions") if r.get("id") == parts[1]), None)
        if not row: return False, "that card is gone"
        btns = json.loads(row.get("buttons") or "[]")
        try: choice = btns[int(parts[2])][1]
        except (ValueError, IndexError): return False, "unknown button"
        return True, NT.answer(parts[1], choice, who="dash")
    if head in ("BUILD", "PARK") and len(parts) == 2:
        row = next((r for r in store().rows("Owner_Actions") if r.get("id") == parts[1]), None)
        if head == "PARK":
            if row: NT.answer(parts[1], "PARK", who="dash")
            return True, "parked"
        if not row: return False, "that idea is gone"
        ok = BD.request_build(re.sub(r"<[^>]+>", "", row.get("text", "")), "feature"); NT.answer(parts[1], "BUILD", who="dash")
        return ok, "build started" if ok else "build could not start"
    if head == "LINKED" and len(parts) == 2:
        for r in NT.open_rows():
            if r.get("kind") in ("linkpack", "link_pack") and r.get("episode_id") == parts[1]: NT.answer(r["id"], "LINKED", who="dash")
        return True, "marked as linked"
    if head == "LOCKSHEETS" and len(parts) == 2:
        n = 0
        for r in store().rows("Character_Sheets"):
            if r.get("character") == parts[1] and r.get("status") == "DRAFT":
                store().update_where("Character_Sheets", {"hash": r["hash"]}, {"status": "LOCKED", "approved_at": iso() + " (dashboard)"}); n += 1
        return n > 0, f"{n} portrait(s) locked"
    if head == "REDOSHEETS" and len(parts) == 2:
        return False, "Redo one expression with the email link 'REDO SHEET <NAME> <expression>' (lifetime image cap applies)"
    if head in ("PAUSE", "RESUME") and len(parts) == 1:
        set_setting("PAUSED", "TRUE" if head == "PAUSE" else "FALSE"); return True, "paused" if head == "PAUSE" else "resumed"
    if head == "SET" and len(parts) == 3 and parts[1] in SETTINGS_MAP:
        key, kind = SETTINGS_MAP[parts[1]]
        from whatifs.core import DEFAULTS
        if key not in DEFAULTS: return False, "that switch arrives with a later release"
        val = parts[2]
        if kind == "bool": val = "TRUE" if val.lower() in ("true", "1", "yes", "on") else "FALSE"
        else:
            try: val = str(max(1, min(5, int(float(val))))) if kind == "week" else str(max(0, min(4, int(float(val)))))
            except ValueError: return False, "not a number"
        set_setting(key, val); return True, f"{key} = {val}"
    return False, "That action is not allowed."

def handle_action(payload_json):
    """repository_dispatch 'dash_action' entry point. Never prints the verb or any text (public logs, K32)."""
    try: msg = decrypt(json.loads(payload_json) if isinstance(payload_json, str) else payload_json)
    except Exception as e: log(f"dashboard action not readable ({type(e).__name__})", "WARN"); return False
    aid, verb = str(msg.get("id") or ""), str(msg.get("verb") or "")
    if any(r.get("id") == aid for r in store().rows("Dash_Acks")): log("dashboard action already handled"); return True
    try: ok, note = route(verb)
    except Exception as e: ok, note = False, f"failed: {scrub(e)[:120]}"
    _ack(aid, verb, ok, note); log(f"dashboard action handled ({'ok' if ok else 'not done'})")
    try: publish()
    except Exception: pass
    return ok
