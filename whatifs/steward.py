"""v10.1 Model Steward (K150; owner 2026-11-08: "future proof: auto-update to the best model and tell me in advance").

Text and voice models were already self-updating: models.discover_models() picks the newest Opus/Sonnet/Haiku/Gemini Flash/Pro/TTS every week
and again after any 'model not found' (K11). The Steward does the same job for the PICTURE and VIDEO models on fal, which have no such list:

1. RUNTIME FAILOVER (every call): a model that answers 'deprecated / not found / no longer supported' is marked dead at once; any other error
   counts; MODEL_FAILS_TO_SWITCH errors in a row = failing. The next healthy model on the role's ladder (MODEL_LADDERS) takes over for the same
   call, inside the price rule, and the owner gets one card. Living stills end on 'code-motion' (a ₹0 camera move) so they can never stop a video.
2. RETIREMENT WATCH (weekly, ₹0): each model page on fal is read; 'will be deprecated on <date>' or 'deprecated' is recorded. MODEL_SWITCH_LEAD_DAYS
   before the date the owner gets a 'This week' card naming the replacement and the switch date ([OK] / [Keep until it stops] / [Discuss]);
   silence = the switch happens on that date.
3. UPGRADE SCOUT (weekly): fal's model listing is scanned for NEWER versions of the families on the ladders. A newer one with a readable price
   inside the price rule gets an automatic, capped test (bake-off: same scenes, vision-model judge). If it scores at least MODEL_UPGRADE_MARGIN
   better, a switch is scheduled MODEL_UPGRADE_NOTICE_DAYS later with a card ([Keep current] / [Switch now] / [Discuss]); silence = switch.
   Unreadable price or schema = a card asking for the owner's input, never a blind switch.
Price rule: a switch never raises the per-clip price above MODEL_MAX_PRICE_RATIO x the current price or MODEL_MAX_USD_CLIP (budget gates
still apply on top). Everything is logged in Model_Changes."""
from __future__ import annotations
import datetime as dt, json, re
from whatifs.core import S, log, store, iso, now_utc, set_setting, DEFAULTS, FAKE, scrub

ROLE_SETTINGS = {"hero": ("FAL_HERO_MODEL", "PRICE_KLING_USD"), "living": ("FAL_LIVING_MODEL", "PRICE_LIVING_USD"),
                 "still": ("FAL_STILL_MODEL", None), "premium": ("FAL_PREMIUM_MODEL", "PRICE_THUMB_USD")}
DEAD_SIGNS = ("deprecat", "no longer supported", "not found", "does not exist", "application not found", "unknown endpoint", " 404", " 410", "retired")
CODE_MOTION = "code-motion"
FAMILY_RX = [r"fal-ai/kling-video/v(\d+(?:\.\d+)?)(?:-turbo)?/(?:pro|standard)/image-to-video", r"wan/v(\d+(?:\.\d+)?)/image-to-video(?:/flash)?",
             r"fal-ai/minimax/hailuo-(\d+(?:\.\d+)?)(?:-fast)?/(?:standard|pro)/image-to-video"]

def ladders():
    try: return json.loads(S("MODEL_LADDERS") or "{}")
    except Exception: return json.loads(DEFAULTS["MODEL_LADDERS"][0])

def health():
    try: return json.loads(S("MODEL_HEALTH") or "{}")
    except Exception: return {}

def _save(h): set_setting("MODEL_HEALTH", json.dumps(h)[:45000])

def _log(role, frm, to, why):
    store().append("Model_Changes", [{"ts": iso(), "role": role, "from": frm, "to": to, "why": str(why)[:300]}])

def usable(mid, today=None):
    if mid == CODE_MOTION: return True
    h = health().get(mid) or {}
    if h.get("status") in ("dead", "failing"): return False
    r = h.get("retire_on")
    return not (r and (today or now_utc().date()).isoformat() >= r)

def price_of(role, mid):
    for e in ladders().get(role, []):
        if e.get("id") == mid: return float(e.get("usd") or 0)
    return None

def current(role):
    key, _ = ROLE_SETTINGS[role]
    return S(key)

def _price_ok(role, frm, cand_usd):
    cur = price_of(role, frm)
    if cur is None:
        _, pk = ROLE_SETTINGS[role]; cur = S(pk, float) if pk else 0.0
    cap = S("MODEL_MAX_USD_CLIP", float)
    return cand_usd <= cap and (cur <= 0 or cand_usd <= cur * S("MODEL_MAX_PRICE_RATIO", float) or cand_usd <= cur)

def next_candidate(role, after=None):
    """The best usable ladder entry other than `after` that passes the price rule (ladder order = preference)."""
    frm = after or current(role)
    for e in ladders().get(role, []):
        mid = e.get("id")
        if mid == frm or not usable(mid): continue
        if mid == CODE_MOTION or _price_ok(role, frm, float(e.get("usd") or 0)): return e
    return None

def switch(role, to_entry, why, tier="now"):
    key, pk = ROLE_SETTINGS[role]; frm = S(key)
    if not to_entry or to_entry.get("id") == frm: return frm
    set_setting(key, to_entry["id"])
    if pk and to_entry.get("usd") is not None: set_setting(pk, str(to_entry["usd"]))
    _log(role, frm, to_entry["id"], why); log(f"model steward: {role} {frm} -> {to_entry['id']} ({why})", "WARN")
    try:
        from whatifs import notify as NT
        NT.send("model_switch", f"The {role} picture/video model was switched from {frm} to {to_entry['id']} ({why}). Price per clip: ${to_entry.get('usd', '?')}. "
                "Quality checks and the budget cap still apply. Reply Discuss if you want a different choice.", [("OK", "OK"), ("Discuss", f"DISCUSS model {role}")],
                tier=tier, default="the new model stays", expires_h=72, dedupe_key=f"switch|{role}|{to_entry['id']}")
    except Exception: pass
    return to_entry["id"]

def ensure(role, mid=None):
    """The model to use now for this role: the current one, or the next healthy one if the current is dead/retired (switching it)."""
    mid = mid or current(role)
    if usable(mid): return mid
    nxt = next_candidate(role, mid)
    if nxt: return switch(role, nxt, f"{mid} is retired or failing")
    return mid                                                     # nothing better: keep trying (the error path reports it)

def report_success(mid):
    h = health(); e = h.get(mid)
    if e and e.get("fails"): e["fails"] = 0; _save(h)

def report_failure(role, mid, err):
    """Returns the replacement model id (already switched) or None."""
    text = " " + str(err).lower(); h = health(); e = h.setdefault(mid, {})
    if any(s in text for s in DEAD_SIGNS): e.update(status="dead", note=str(err)[:160], checked=iso())
    else:
        e["fails"] = int(e.get("fails") or 0) + 1
        if e["fails"] >= S("MODEL_FAILS_TO_SWITCH", int): e.update(status="failing", note=str(err)[:160], checked=iso())
    _save(h)
    if e.get("status") in ("dead", "failing"):
        nxt = next_candidate(role, mid)
        if nxt: return switch(role, nxt, f"{mid}: {str(err)[:100]}")
        try:
            from whatifs import notify as NT
            NT.send("model_dead", f"The {role} model {mid} stopped working and no approved replacement fits the price rule. Videos continue with what still works; please choose a model (Discuss).",
                    [("Discuss", f"DISCUSS model {role}")], tier="now", urgent=True, dedupe_key=f"dead|{mid}")
        except Exception: pass
    return None

# ------------------------------------------------------------------ weekly watch
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}

def parse_page(text):
    """{'status': 'dead'|'deprecating'|'ok', 'retire_on': 'YYYY-MM-DD'|None, 'usd': float|None} from a fal model page's text."""
    t = re.sub(r"\s+", " ", str(text or "")).lower(); out = {"status": "ok", "retire_on": None, "usd": None}
    m = re.search(r"will be deprecated on (\w+) (\d{1,2}),? (\d{4})", t)
    if m and m.group(1) in MONTHS:
        out.update(status="deprecating", retire_on=dt.date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2))).isoformat())
    elif "this endpoint is deprecated" in t or "no longer supported" in t: out["status"] = "dead"
    p = re.search(r"for 5s video your request will cost \$(\d+(?:\.\d+)?)", t) or re.search(r"\$(\d+(?:\.\d+)?)\s*(?:/|per)\s*(?:video )?second", t)
    if p:
        v = float(p.group(1)); out["usd"] = round(v if "5s video" in p.group(0) else v * 5, 4)
    return out

def _fetch(url):
    import requests
    r = requests.get(url, timeout=25, headers={"User-Agent": "RealityEngine-model-steward/1.0"}); r.raise_for_status()
    return re.sub(r"(?s)<[^>]+>", " ", r.text)

def watch(fetch=None, now=None):
    """Weekly: retirement dates of every ladder/current model, planned switches with notice, and newer-version discovery. Returns a summary."""
    if not S("MODEL_STEWARD_ON", bool) or (FAKE and fetch is None): return {}
    fetch = fetch or _fetch; now = now or now_utc(); h = health(); planned = {}; found = []
    ids = {e.get("id") for es in ladders().values() for e in es} | {current(r) for r in ROLE_SETTINGS}
    for mid in sorted(i for i in ids if i and i != CODE_MOTION):
        try: info = parse_page(fetch(f"https://fal.ai/models/{mid}"))
        except Exception as e: log(f"steward: {mid} page not read ({str(e)[:80]})", "WARN"); continue
        e = h.setdefault(mid, {}); e.update({k: v for k, v in info.items() if k in ("status", "retire_on") and v}); e["checked"] = iso()
        if info.get("usd"): e["usd_seen"] = info["usd"]
    _save(h)
    from whatifs import notify as NT
    for role in ROLE_SETTINGS:
        mid = current(role); e = h.get(mid) or {}
        r = e.get("retire_on")
        if e.get("status") == "dead" or (r and (dt.date.fromisoformat(r) - now.date()).days <= S("MODEL_SWITCH_LEAD_DAYS", int)):
            nxt = next_candidate(role, mid)
            if not nxt: continue
            on = now.date() if e.get("status") == "dead" or not r else max(now.date(), dt.date.fromisoformat(r) - dt.timedelta(days=7))
            planned[role] = {"to": nxt["id"], "usd": nxt.get("usd"), "on": on.isoformat(), "why": f"{mid} retires {r or 'now'}"}
            NT.send("model_plan", f"{mid} ({role}) will be retired on fal {('on ' + r) if r else 'now'}. Plan: switch to {nxt['id']} (${nxt.get('usd')}/clip) on {on.isoformat()}.",
                    [("OK", "OK"), ("Keep until it stops", f"KEEP {role}"), ("Discuss", f"DISCUSS model {role}")], tier="week",
                    default=f"switch on {on.isoformat()}", expires_h=24 * 6, dedupe_key=f"plan|{role}|{nxt['id']}")
    if planned:
        cur = json.loads(S("MODEL_PLANNED") or "{}"); cur.update(planned); set_setting("MODEL_PLANNED", json.dumps(cur))
    if S("MODEL_UPGRADE_SCOUT_ON", bool):
        try: found = discover(fetch)
        except Exception as e: log(f"steward discovery skipped: {str(e)[:100]}", "WARN")
    return {"checked": len(ids), "planned": planned, "new": found}

def _ver(s):
    try: return tuple(int(x) for x in str(s).split("."))
    except ValueError: return (0,)

def discover(fetch):
    """Newer versions of the ladder families on fal's listing -> automatic capped test (or a card when the price/schema is unknown)."""
    page = fetch("https://fal.ai/explore/image-to-video-apis")
    known = {e.get("id") for es in ladders().values() for e in es}
    best = {}
    for rx in FAMILY_RX:
        cur_vers = [_ver(m.group(1)) for m in (re.search(rx, k) for k in known) if m]
        if not cur_vers: continue
        top = max(cur_vers)
        for m in re.finditer(rx, page):
            mid, v = m.group(0), _ver(m.group(1))
            if mid not in known and v > top: best[mid] = v
    out = []
    from whatifs import notify as NT
    for mid in sorted(best):
        try: info = parse_page(fetch(f"https://fal.ai/models/{mid}"))
        except Exception: info = {"usd": None, "status": "ok"}
        if info.get("status") != "ok": continue
        cur = price_of("hero", current("hero")) or S("PRICE_KLING_USD", float)
        if info.get("usd") and _price_ok("hero", current("hero"), info["usd"]) and S("MODEL_AUTO_UPGRADE_ON", bool):
            cand = json.loads(S("MODEL_CANDIDATES") or "[]")
            if not any(c.get("id") == mid for c in cand): cand.append({"id": mid, "usd": info["usd"], "found": iso()})
            set_setting("MODEL_CANDIDATES", json.dumps(cand[-6:]))
            NT.send("model_new", f"A newer video model appeared: {mid} (${info['usd']}/5 s clip vs ${cur} now). It will be tested automatically (capped) and only adopted if it looks clearly better.",
                    [("OK", "OK"), ("Skip it", f"SKIPMODEL {mid}")], tier="week", default="tested automatically", expires_h=24 * 6, dedupe_key=f"new|{mid}")
        else:
            NT.send("model_new", f"A newer video model appeared: {mid}, but its price or inputs could not be read safely. Want it tested? (Discuss)",
                    [("Discuss", f"DISCUSS model {mid}")], tier="week", default="ignored for now", expires_h=24 * 6, dedupe_key=f"new|{mid}")
        out.append(mid)
    return out

def apply_planned(now=None):
    """Daily: planned switches whose date has come (unless the owner said KEEP)."""
    now = now or now_utc()
    try: plan = json.loads(S("MODEL_PLANNED") or "{}")
    except Exception: plan = {}
    done = []
    for role, p in list(plan.items()):
        if p.get("keep"): continue
        if p.get("on") and now.date().isoformat() >= p["on"]:
            switch(role, {"id": p["to"], "usd": p.get("usd")}, p.get("why", "planned"), tier="week"); done.append(role); plan.pop(role)
    set_setting("MODEL_PLANNED", json.dumps(plan)); return done

def _answer(row, choice):
    c = str(choice).upper()
    if c.startswith("KEEP "):
        role = choice.split()[1].lower(); plan = json.loads(S("MODEL_PLANNED") or "{}")
        if role in plan: plan[role]["keep"] = True; set_setting("MODEL_PLANNED", json.dumps(plan))
        return f"kept the current {role} model until it stops (then the ladder takes over)"
    if c.startswith("SKIPMODEL "):
        mid = choice.split()[1]; cand = [x for x in json.loads(S("MODEL_CANDIDATES") or "[]") if x.get("id") != mid]
        set_setting("MODEL_CANDIDATES", json.dumps(cand)); return f"{mid} will not be tested"
    if c.startswith("SWITCHNOW "):
        role = choice.split()[1].lower(); plan = json.loads(S("MODEL_PLANNED") or "{}")
        if role in plan: p = plan.pop(role); set_setting("MODEL_PLANNED", json.dumps(plan)); switch(role, {"id": p["to"], "usd": p.get("usd")}, "owner: switch now"); return "switched"
    return "recorded"

def register():
    from whatifs import notify as NT
    for k in ("model_plan", "model_new", "model_switch", "model_upgrade"): NT.register(k, on_answer=_answer)

def test_candidates(now=None):
    """Weekly: run the capped automatic bake-off for queued candidates; schedule a switch when one is clearly better."""
    if not S("MODEL_AUTO_UPGRADE_ON", bool): return None
    cand = json.loads(S("MODEL_CANDIDATES") or "[]")
    if not cand: return None
    c = cand[0]
    from whatifs import bakeoff as BK
    res = BK.judge_pair(current("hero"), price_of("hero", current("hero")) or S("PRICE_KLING_USD", float), c["id"], c["usd"])
    set_setting("MODEL_CANDIDATES", json.dumps(cand[1:]))
    if not res or not res.get("ok"): return res
    if res["new_score"] - res["cur_score"] >= S("MODEL_UPGRADE_MARGIN", float):
        on = ((now or now_utc()).date() + dt.timedelta(days=S("MODEL_UPGRADE_NOTICE_DAYS", int))).isoformat()
        plan = json.loads(S("MODEL_PLANNED") or "{}"); plan["hero"] = {"to": c["id"], "usd": c["usd"], "on": on, "why": f"tested better ({res['new_score']:.1f} vs {res['cur_score']:.1f})"}
        set_setting("MODEL_PLANNED", json.dumps(plan))
        from whatifs import notify as NT
        NT.send("model_upgrade", f"Test result: {c['id']} scored {res['new_score']:.1f}/10 vs {res['cur_score']:.1f} for the current model, at ${c['usd']}/clip. Switching on {on}.",
                [("Keep current", "KEEP hero"), ("Switch now", "SWITCHNOW hero"), ("Discuss", "DISCUSS model hero")], tier="week", default=f"switch on {on}", expires_h=24 * 4, dedupe_key=f"upg|{c['id']}")
    return res
