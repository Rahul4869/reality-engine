"""The phone dashboard's data snapshot and its taps (never contains secrets, scripts or unreleased premises). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import base64, datetime as dt, json, re, statistics
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, set_setting, scrub, FAKE

MODE_IDS = {"lean": "runway", "runway": "runway", "standard": "standard", "growth": "growth"}
SETTINGS_MAP = {"shorts_per_week": ("SHORTS_PER_WEEK", "week"),   # v12 V2c-b: standalone Shorts a week, 1 to 5 (the owner's own tap) "localizations": ("LOCALIZATIONS_ON", "bool"), "affiliate_block": ("AFFILIATE_ON", "bool"),
                "native_test_reminder": ("NATIVE_TEST_REMINDER_ON", "bool"), "visual_lab": ("VISUAL_LAB_ON", "bool"), "facts_watch": ("FACTS_WATCH_ON", "bool")}

# ------------------------------------------------------------------ snapshot
def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

def _two():
    return S("TWO_SCREENS_ON", bool)

PRIVATE_LINE = "{name}: the text is in WhatsApp and your e-mail."      # v12 B-OWNER (PART 6): a row whose text holds a script or an unreleased premise
NOTES = {"department_line": "The department line comes with the first batch after the launch.",          # R5-5 (4): where a row's batch has not landed the section says so
         "treasury": "The savings line, the two pockets and the monthly recharge advice come with the treasury batch after the launch.",
         "features": "The feature watch comes after the launch.",
         "appetite": "The appetite readings come with batch V4b."}
SOURCE_KEYS = ("v", "value", "views", "inr", "pct")      # a number under one of these keys needs a non-empty `src` beside it (P13's lesson)

def _text(r, n=400):
    """v12 B-OWNER (PART 6): what a row of Owner_Actions shows on the dashboard - its text without tags, or, for a kind whose text holds a script or an
    unreleased premise (`notify.DASH_PRIVATE`), only the kind's plain name; its buttons still show."""
    from whatifs import notify as NT
    if r.get("kind") in NT.DASH_PRIVATE: return PRIVATE_LINE.format(name=NT.name(r.get("kind")))
    return re.sub(r"<[^>]+>", "", str(r.get("text", "")))[:n]

def _docket():
    from whatifs import packaging as PK, notify as NT
    st = store(); cards = []; two = _two()
    from whatifs.notify import INFORM_KINDS
    for r in (NT.needs(st.rows("Owner_Actions")) if two else st.rows("Owner_Actions")):      # v12 B-OWNER: with the switch on the docket IS "Needs you" (PART 1), of any tier
        if two:
            if r.get("kind") in ("title_pick", "sheets_review"): continue      # PART 2: the dashboard builds these two cards itself, from Packaging_Tests and Character_Sheets (below)
        elif r.get("status") not in ("OPEN", "QUEUED") or r.get("tier") == "fyi" or r.get("kind") in INFORM_KINDS: continue      # v12 V4: what was done for him is not waiting
        btns = json.loads(r.get("buttons") or "[]")
        kind = r.get("kind"); verbs = {}
        if kind == "build_ready":
            m = re.search(r"#(\d+)", r.get("text", "")); n = m.group(1) if m else ""
            verbs = {"Merge now": f"MERGE|{n}", "Reject": f"REJECT|{n}"}; kind = "merge"
        else:
            verbs = {str(lbl)[:24]: f"ACT|{r['id']}|{i}" for i, (lbl, _v) in enumerate(btns)}
        exp = parse_iso(r.get("expires_at")); created = parse_iso(r.get("created"))
        txt = _text(r) if two else re.sub(r"<[^>]+>", "", r.get("text", ""))[:400]
        cards.append({"id": r["id"], "kind": kind, "title": txt[:90], "why": txt[:400],
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

def _decided():
    """v12 V4: what was decided for him (kinds strategy and desk) - a list of its own ("Decided for you - tap to undo"), never in the count of open decisions."""
    from whatifs.notify import INFORM_KINDS
    if _two(): return _decided_two()
    out = []
    for r in store().rows("Owner_Actions"):
        if r.get("status") not in ("OPEN", "QUEUED") or r.get("kind") not in INFORM_KINDS: continue
        btns = json.loads(r.get("buttons") or "[]")
        out.append({"id": r["id"], "kind": "decided", "title": re.sub(r"<[^>]+>", "", r.get("text", ""))[:90], "why": re.sub(r"<[^>]+>", "", r.get("text", ""))[:400],
                    "default_label": r.get("default_action") or "It stays", "default_at": "", "window_h": 0, "verbs": {str(lbl)[:24]: f"ACT|{r['id']}|{i}" for i, (lbl, _v) in enumerate(btns)}})
    return out

def _decided_two(now=None):
    """v12 B-OWNER (PART 6, R17): "Decided for you" - the open STANDING_KINDS rows whose group is "decided" (strategy, decided_post: each with its Undo or
    "Take it down") and every row of any kind DEFAULTED in the last 48 hours ("ran by default": his silence decided it; a closed row has no button left).
    A desk or idea row is under his inputs, never here."""
    from whatifs import notify as NT
    since = ((now or now_utc()) - dt.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ"); out = []
    for r in store().rows("Owner_Actions"):
        k = r.get("kind")
        if r.get("status") in ("OPEN", "QUEUED") and k in NT.STANDING_KINDS and NT.group(k) == "decided": ran = False
        elif r.get("status") == "DEFAULTED" and str(r.get("answered_at") or "") >= since: ran = True
        else: continue
        btns = [] if ran else json.loads(r.get("buttons") or "[]"); txt = _text(r)
        out.append({"id": r["id"], "kind": "decided", "title": txt[:90], "why": txt[:400],
                    "default_label": ("ran by default: " + str(r.get("default_action") or "nothing changed")) if ran else (r.get("default_action") or "It stays"),
                    "default_at": (r.get("answered_at") or "") if ran else "", "window_h": 0,
                    "verbs": {str(lbl)[:24]: f"ACT|{r['id']}|{i}" for i, (lbl, _v) in enumerate(btns)}})
    return out

STAY_MIN = 3      # v12 V4 (P13): a median of his own needs three Shorts read
def _progress():
    rows = store().rows("Analytics")
    views = sum(_f(r.get("views")) for r in rows)
    hours = sum(_f(r.get("views")) * _f(r.get("avg_view_sec")) for r in rows) / 3600
    def avg(k, scale=1.0):
        v = [_f(r.get(k), None) for r in rows if r.get(k) not in (None, "")]
        v = [x for x in v if x is not None]
        return round(sum(v) / len(v) * scale, 2) if v else 0
    subs = sum(_f(r.get("subs")) for r in rows)
    stay = [100.0 * _f(r.get("engaged_views")) / _f(r.get("views")) for r in rows
            if str(r.get("days") or "").strip() and _f(r.get("views")) > 0 and str(r.get("engaged_views") or "").strip()]      # v12 V4 (P13): the Shorts' own readings (brain.ingest_shorts), in the order first read
    from whatifs import scoreboard as SBD
    bar = SBD.bars(); bar_src = "72851" if str(bar.get("until") or "") else "12843009"                                     # the Partner Program's bar of today (YPP_BARS) and its page
    k = {"ctr": {"v": avg("ctr"), "unit": "%", "label": "Click-through", "good": "higher is better", "trend": "flat"},
         "rel30": {"v": avg("ret30"), "unit": "", "label": "30-s hold", "good": "higher is better", "trend": "flat"},
         "apv": {"v": avg("avg_view_pct"), "unit": "%", "label": "Average % watched", "good": "higher is better", "trend": "flat"},
         "stay": ({"v": round(stay[-1]), "unit": "%", "good": f"your own median: {round(statistics.median(stay))}% over {len(stay)} Shorts"} if len(stay) >= STAY_MIN
                  else {"v": "-", "unit": "", "good": f"not enough Shorts yet ({len(stay)} of {STAY_MIN} read)"}) | {"label": "Shorts: engaged views per view (a proxy)", "trend": "flat"},
         "subs1k": {"v": round(subs / views * 1000, 2) if views else 0, "unit": "", "label": "Subs per 1,000 views", "good": "rising is the goal", "trend": "flat"},
         "hours_week": {"v": round(hours, 1), "unit": " h", "label": "Watch hours (all videos)", "good": f"the bar: {int(bar['hours']):,} h of long videos in 12 months and {int(bar['subs']):,} subscribers (YouTube Help {bar_src})", "trend": "flat"}}
    return {"subs": int(subs), "watch_hours": round(hours), "shorts_views_90d": int(sum(_f(r.get("shorts_views")) for r in rows)),
            "old_bar_deadline": "2027-01-31", "series_14d": [], "kpis": k}

def _cover():
    """v12 V4: the Claude credit lane's cover with STRATEGY_ON, the older money view without."""
    from whatifs import governor as G
    from whatifs.org import finance as FIN
    return FIN.cover() if FIN.on() else G.credit_cover_inr()

def _money():
    from whatifs import governor as G
    try: spent = G.own_spend_inr()                                                     # v12 V4: his own money (= the list-price spend with STRATEGY_ON FALSE)
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
    return {"month_spend": round(spent), "cap": round(G.cap_inr()), "credit_cover": round(_cover()),
            "lines": [{"label": k, "inr": round(v)} for k, v in sorted(lines.items(), key=lambda x: -x[1])], "revenue": rev,
            "modes": [{"id": "lean", "name": "Runway", "cost": round(S("RUNWAY_CAP_INR", float)), "text": "One long case a week (Saturdays), Shorts kept, smaller research and chat caps."},
                      {"id": "standard", "name": "Standard", "cost": round(S("BUDGET_CEILING_INR", float)), "text": "Two long cases a week (Tue + Sat), the full Shorts Lab, faces, research and chat."},
                      {"id": "growth", "name": "Growth", "cost": None, "text": "Standard plus a share of last month's revenue. Switches on by itself when revenue arrives."}]}

HEALTH_NOTE = {"ok": "",
               "none": "No run has been read yet, so there is nothing to judge. This is not a green light.",
               "failed": "The health check itself could not be read this time. This is not a green light. It is read again on the next run."}

def _health():
    """CE-2 (CR-7-2): a reading that failed is SAID, never shown as health. `read`: "ok" = the runs were read and at least one was found; "none" = read,
    none found; "failed" = an error or a timeout. `note`: the plain words the page shows. `expiry_read`: False when the renewal dates were not read."""
    from whatifs import caretaker as CT
    out = {"expiring": [], "last_runs": [], "read": "ok", "expiry_read": True}
    try:
        out["last_runs"] = list(CT.last_runs() or [])
        if not out["last_runs"]: out["read"] = "none"
    except Exception as e: out["last_runs"] = []; out["read"] = "failed"; log(f"dashboard health: the runs could not be read ({type(e).__name__})", "WARN")
    try: out["expiring"] = list(CT.expiring() or [])
    except Exception as e: out["expiry_read"] = False; log(f"dashboard health: the renewal dates could not be read ({type(e).__name__})", "WARN")
    out["note"] = HEALTH_NOTE[out["read"]]
    return out

def _lab():
    try:
        from whatifs import microscope as MS
        rules = MS.active_rules()
    except Exception: rules = []
    fmt = lambda r: {"text": str(r.get("text"))[:140], "effect": f"{float(r.get('effect') or 0) * 100:+.0f}% vs usual", "videos": int(float(r.get("videos") or 0))}
    return {"experiments": [], "boosters": [fmt(r) for r in rules if r.get("kind") == "booster"][:4], "killers": [fmt(r) for r in rules if r.get("kind") == "killer"][:4]}

# ------------------------------------------------------------------ v12 B-OWNER (PART 6): both screens show the same, and he sees the learning
# Every field below exists in both switch states (the page reads them: tests/test_v94b.py); with TWO_SCREENS_ON FALSE no row is read for them.
def _alarms(two):
    """The open rows of class ALARM, newest first (pinned first on Home): an incident with its count and the time of its newest firing."""
    from whatifs import notify as NT
    if not two: return []
    rows = [r for r in NT.open_rows() if NT.klass(r.get("kind")) == NT.ALARM]
    return [{"id": r["id"], "kind": r.get("kind"), "title": _text(r, 90), "text": _text(r), "count": int(_f(r.get("count"), 1) or 1), "last_at": r.get("last_at") or r.get("created") or "",
             "buttons": {str(lbl)[:24]: f"ACT|{r['id']}|{i}" for i, (lbl, _v) in enumerate(json.loads(r.get("buttons") or "[]"))}}
            for r in sorted(rows, key=lambda x: str(x.get("created") or ""), reverse=True)]

def _groups(two, now=None):
    """The eight groups of the morning message (`notify.GROUPS`), each its newest 20 rows by `notify.group_rows` - the rows WhatsApp's groups show."""
    from whatifs import notify as NT
    if not two: return {g: [] for g in NT.GROUPS}
    return {g: [{"id": r["id"], "kind": r.get("kind"), "text": _text(r, 300), "at": r.get("created") or ""} for r in NT.group_rows(g, now, limit=20)] for g in NT.GROUPS}

def _inputs(two):
    """His newest 20 inputs from every channel (tab Owner_Desk), each with its verdict as he reads it (`desk.SHOWN`) and its answer."""
    if not two: return []
    from whatifs.org import desk as DESK
    rows = sorted(store().rows(DESK.DESK), key=lambda r: int(_f(r.get("n"))), reverse=True)[:20]
    return [{"n": int(_f(r.get("n"))), "at": r.get("ts") or "", "text": str(r.get("verbatim") or ""), "verdict": DESK.SHOWN.get(r.get("verdict"), r.get("verdict") or ""),
             "answer": DESK._said(r) if r.get("how") else "", "channel": r.get("channel") or "sheet"} for r in rows]

def _section(fn, *a):
    """One part of the learning or the plan; a part that fails says so and never stops the snapshot."""
    try: return fn(*a)
    except Exception as e:
        log(f"dashboard: a part of the snapshot is not available ({type(e).__name__})", "WARN"); return {"empty": f"Not available right now ({type(e).__name__})."}

def _learning(two, learned):
    """What the channel learns: lessons (the snapshot's `learned`), research and observations with their source and date, experiments, and the notes of
    what lands with a later batch."""
    out = {"lessons": [], "research": {"topics": [], "outliers": [], "observations": []}, "experiments": [],
           "appetite": {"note": NOTES["appetite"]}, "features": {"note": NOTES["features"]}, "department_line": {"note": NOTES["department_line"]}}
    if not two: return out
    from whatifs import owner_view as OV
    hot = _section(OV.hot_topics); obs = _section(OV.observations); xs = _section(OV.experiments)
    out["lessons"] = list(learned)
    out["research"] = {"topics": hot.get("topics") or [], "outliers": hot.get("outliers") or [], "observations": obs.get("items") or [],
                       "empty": " ".join(x for x in (hot.get("empty"), obs.get("empty")) if x)}
    out["experiments"] = xs.get("running") or []
    return out

def _plan(two, now=None):
    """The plan: the CEO's lines of today (`strategy.brief`) and the rule-based plan (`owner_view.strategy`), the next five slots (times only: a title
    not yet released is a premise), and the department line's note."""
    out = {"lines": [], "slots": [], "department_line": {"note": NOTES["department_line"]}}
    if not two: return out
    from whatifs import owner_view as OV
    from whatifs.org import strategy as STR
    from whatifs.manage import next_slots
    brief = _section(lambda: {"lines": [x for x in str(STR.brief(now) or "").splitlines() if x.strip()]})
    rule = _section(OV.strategy)
    out["lines"] = (brief.get("lines") or []) + (rule.get("plan") or [])
    try: out["slots"] = [{"at": s.strftime("%Y-%m-%dT%H:%M:%SZ")} for s in next_slots(5)]
    except Exception as e: log(f"dashboard: the next slots are not available ({type(e).__name__})", "WARN")
    return out

def _owner_money(two):
    """The Money tab's two new lines: his WhatsApp month (`costguard.owner_messages`, PART 8) and the treasury's note."""
    out = {"whatsapp": {}, "treasury": {"note": NOTES["treasury"]}}
    if two:
        from whatifs import costguard as CG
        out["whatsapp"] = {**_section(CG.owner_messages), "src": "Cost_Log (item whatsapp)"}
    return out

def unsourced(snap):
    """NEVER A NUMBER WITHOUT ITS SOURCE (P13's lesson): every dict in `learning`, `plan`, `groups` and the new parts of `money` that carries a number
    under v, value, views, inr or pct and no non-empty `src`."""
    bad = []
    def walk(x):
        if isinstance(x, dict):
            if any(isinstance(x.get(k), (int, float)) and not isinstance(x.get(k), bool) for k in SOURCE_KEYS) and not str(x.get("src") or "").strip(): bad.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for k in ("learning", "plan", "groups"): walk(snap.get(k))
    for k in ("whatsapp", "treasury"): walk((snap.get("money") or {}).get(k))
    return bad

def _without(x, bad):
    """`x` with every dict of `bad` (by identity) taken out of the list or the dict that held it."""
    ids = {id(b) for b in bad}
    if isinstance(x, dict): return {k: _without(v, bad) for k, v in x.items() if id(v) not in ids}
    if isinstance(x, list): return [_without(v, bad) for v in x if id(v) not in ids]
    return x

def _scrubbed(x):
    """Every string of the snapshot through `core.scrub`: no key reaches the page."""
    if isinstance(x, dict): return {k: _scrubbed(v) for k, v in x.items()}
    if isinstance(x, list): return [_scrubbed(v) for v in x]
    return scrub(x) if isinstance(x, str) else x

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
    acks = [{"id": str(r.get("id") or ""), "verb": r.get("verb"), "at": r.get("ts"), "ok": str(r.get("ok")) == "TRUE", "note": str(r.get("note") or "")[:120]} for r in st.rows("Dash_Acks") if str(r.get("ts", "")) >= two]
    on = _two(); learned = (rules + lessons)[-6:]
    snap = {"generated_at": iso(),
            "engine": {"status": "paused" if paused() else "running", "mode": "lean" if mode == "runway" else mode, "owner_mode": "minimal",
                       "upload_lock": LA.lock_state() == "on",
                       "next_release": {"episode": nr.get("episode_id", ""), "title": str(nr.get("title") or "")[:90], "case_no": len([e for e in eps if e.get("yt_id")]) + 1,
                                        "slot_iso": nr.get("slot_et")} if nr else None},
            "docket": _docket(), "decided": _decided(), "progress": _progress(), "learned": learned,
            "lab": _lab(), "money": {**_money(), **_owner_money(on)},
            "health": _health(),
            "settings": {"shorts_per_week": S("SHORTS_PER_WEEK", int),
                         "localizations": bool(S("LOCALIZATIONS_ON", bool)) if "LOCALIZATIONS_ON" in __import__("whatifs.core", fromlist=["DEFAULTS"]).DEFAULTS else False,
                         "visual_lab": bool(S("VISUAL_LAB_ON", bool)), "facts_watch": bool(S("FACTS_WATCH_ON", bool))},
            "acks": acks, "whatsapp": str(S("WA_BOT_NUMBER") or ""),
            "alarms": _alarms(on), "groups": _groups(on), "inputs": _inputs(on), "learning": _learning(on, learned), "plan": _plan(on)}      # v12 B-OWNER (PART 6)
    if not on: return snap
    bad = unsourced(snap)
    if bad:                                                                                  # a number without its source never reaches the page
        log(f"dashboard: {len(bad)} number(s) without a source were left out of the snapshot", "ERROR"); snap = _without(snap, bad)
    return _scrubbed(snap)

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
    if head == "UNPOST" and len(parts) == 2 and _two():                      # v12 B-OWNER (PART 7): "Take it down" - private and his Hold, never a delete
        from whatifs import contract as CON
        return True, CON.unpost(parts[1])
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
        set_setting(key, val)
        try:                                                                                     # v12 V4: his own tap on a portfolio key is a hand: the key is frozen
            from whatifs.org import strategy as STR
            if STR.on() and key in STR.PORTFOLIO: STR.hand(key, val)
        except Exception as e: log(f"dashboard: the hand on {key} was not recorded: {scrub(e)[:120]}", "WARN")
        return True, f"{key} = {val}"
    return False, "That action is not allowed."

CARD_RX = re.compile(r"[A-Za-z0-9_.:\-]{1,64}")      # the Worker's rule for the card a word was typed under (mission_control/worker.js, api/input)

def _input(msg, aid):
    """v12 B-OWNER (PART 6): the page's box ("Type anything") and the line under a card - his words go to his desk, word for word (`desk.take`, channel
    "dashboard", ref = this action's id, the card it was typed under); the Dash_Acks row holds the verb and "Saved as input N", never his words."""
    from whatifs.org import desk as DESK
    card = str(msg.get("card") or "")
    n, _line = DESK.take(str(msg.get("text") or ""), "dashboard", ref=aid, card=card if CARD_RX.fullmatch(card) else "")
    return (True, f"Saved as input {n}") if n else (False, "nothing to save")

def handle_action(payload_json):
    """repository_dispatch 'dash_action' entry point. Never prints the verb or any text (public logs, K32)."""
    try: msg = decrypt(json.loads(payload_json) if isinstance(payload_json, str) else payload_json)
    except Exception as e: log(f"dashboard action not readable ({type(e).__name__})", "WARN"); return False
    aid, verb = str(msg.get("id") or ""), str(msg.get("verb") or "")
    if any(r.get("id") == aid for r in store().rows("Dash_Acks")): log("dashboard action already handled"); return True
    try: ok, note = _input(msg, aid) if verb == "INPUT" and _two() else route(verb)
    except Exception as e: ok, note = False, f"failed: {scrub(e)[:120]}"
    _ack(aid, verb, ok, note); log(f"dashboard action handled ({'ok' if ok else 'not done'})")
    try: publish()
    except Exception: pass
    return ok

class _CFKV:
    """CE-1b: the inbox keys of Cloudflare KV, listed, read and deleted with the token `publish` writes with (CF_KV_TOKEN)."""
    def __init__(s, acc, ns, tok): s.base, s.h = f"https://api.cloudflare.com/client/v4/accounts/{acc}/storage/kv/namespaces/{ns}", {"Authorization": f"Bearer {tok}"}
    def keys(s, prefix):
        import requests; r = requests.get(s.base + "/keys", params={"prefix": prefix, "limit": 1000}, headers=s.h, timeout=30); r.raise_for_status()
        return [k["name"] for k in r.json().get("result", [])]
    def get(s, key):
        import requests; from urllib.parse import quote; r = requests.get(s.base + "/values/" + quote(key, safe=""), headers=s.h, timeout=30); return r.text if r.status_code == 200 else None
    def delete(s, key):
        import requests; from urllib.parse import quote; requests.delete(s.base + "/values/" + quote(key, safe=""), headers=s.h, timeout=30)

def _kv():
    acc, ns, tok = env("CF_ACCOUNT_ID"), env("CF_KV_NAMESPACE_ID"), env("CF_KV_TOKEN")
    return None if (FAKE or not (acc and ns and tok)) else _CFKV(acc, ns, tok)

def _when(key, item):
    """CH-1 (FR-CE1b-1): the moment he gave a kept input, in milliseconds - a dash item's `ts` (the Worker's Date.now()), a WhatsApp message's `ts`
    (Meta's timestamp, in SECONDS); none or unreadable -> 0 (first, in KV's order)."""
    try:
        if key.startswith("inbox:wa:"): return float(((item.get("messages") or [{}])[0] or {}).get("ts") or 0) * 1000
        return float(item.get("ts") or 0)
    except (TypeError, ValueError, AttributeError): return 0.0

def drain(kv=None):
    """CE-1b (R1-144 (b)): every input and message of his the Worker kept (`inbox:<id>`) before its dispatch is handled exactly once - a WhatsApp
    message through `wa.handle_inbound` (deduped by its id), the rest through `handle_action` (an acked id is skipped) - and its key deleted. A run
    that was cancelled, replaced, failed or stalled loses nothing. Never logs a word of his. Returns the number of keys handled.
    CH-1 (FR-CE1b-1): KV lists the keys by their random names, so the kept inputs are handled OLDEST FIRST by the moment he gave them (`_when`) -
    his last word stands; one whose handling raised stops the drain, and the later ones stay for the next run, which does them in order. The run
    drains BEFORE its own payload, so KV not answering never stops it: nothing is handled from KV, everything stays, the run does its own tap."""
    kv = kv or _kv()
    if kv is None: return 0
    kept = []
    try: listed = [(key, kv.get(key)) for key in kv.keys("inbox:")]
    except Exception as e: log(f"the kept inputs were not read ({type(e).__name__}); they stay for the next run", "WARN"); return 0
    for key, val in listed:
        if val is None: continue
        try: item = decrypt(json.loads(val))                        # unreadable in this run (a wrong or missing key): the key STAYS - never deleted unhandled
        except Exception as e: log(f"a kept input was not readable ({type(e).__name__}); it stays for the next run", "WARN"); continue
        kept.append((_when(key, item), len(kept), key, val))
    n = 0
    for _t, _i, key, val in sorted(kept):
        try:
            if key.startswith("inbox:wa:"):
                from whatifs.wa import handle_inbound; handle_inbound(val)
            else: handle_action(val)
        except Exception as e: log(f"a kept input was not handled ({type(e).__name__}); it and the later ones stay for the next run", "WARN"); break
        try: kv.delete(key)
        except Exception as e: log(f"a handled input's key was not deleted ({type(e).__name__}); the next run finds it handled", "WARN")
        n += 1
    if n: log(f"dashboard inbox: {n} kept input(s) handled")
    return n
