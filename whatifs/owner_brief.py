"""v10.3 (K154) Owner Brief: the owner proposes the next video's or reel's topic on WhatsApp; the Showrunner discusses it with him until it is
excellent (premise, angle, hook and title options, must-include, avoid, honest scores, search demand from YouTube); 'lock' makes it the FORCED
premise of the next long video (or the next special reel). Outcomes are measured after 7 days and owner picks that beat the channel median become
calibration examples for the scout and the research brief (learning from human input, with evidence; never on opinion alone).
WhatsApp words: 'brief <idea>' / 'next video: <idea>' / 'next reel: <idea>' start; any text continues; 'lock' / 'cancel' / 'show brief'."""
from __future__ import annotations
import json, re, statistics
from whatifs.core import S, log, store, iso, now_utc, set_setting, scrub, FAKE

COACH = ("You are the Showrunner of 'Reality on Trial' (a courtroom science show: Inspector Vale, Dr. Grimm, Nana Rosa, the Archivist; trial grammar: "
         "cold open with stakes, time ladder, sourced exhibits, Grimm's failed Prototype, Vale's twist, 'Here's what's true'). The OWNER proposes a "
         "topic. Work WITH him to make it the strongest possible episode: be honest (say plainly if it is weak or already overdone and why), improve "
         "the premise wording, propose an angle, 3 cold-open hooks and 3 titles, list what it must include and avoid, score it 0-10 on curiosity, "
         "visual potential, science depth and fit with the show, and ask ONE question that would most improve it. Keep the owner's intent. "
         "JSON only: {\"reply\": \"<= 90 words, conversational\", \"brief\": {\"premise\": \"\", \"angle\": \"\", \"hooks\": [], \"titles\": [], "
         "\"must\": [], \"avoid\": []}, \"scores\": {\"curiosity\": 0, \"visual\": 0, \"science\": 0, \"fit\": 0}, \"question\": \"\"}")
START_RX = re.compile(r"^(brief|idea|topic|next video|next reel|reel idea|video idea)\s*[:\-]?\s*(.*)$", re.I | re.S)

def state():
    try: return json.loads(S("WA_BRIEF") or "{}")
    except Exception: return {}

def _save(s): set_setting("WA_BRIEF", json.dumps(s)[:20000])

def card(s):
    b = s.get("brief") or {}; sc = s.get("scores") or {}
    lines = [f"*Brief ({'next reel' if s.get('target') == 'reel' else 'next video'})*", f"Premise: {b.get('premise') or s.get('idea')}"]
    if b.get("angle"): lines.append(f"Angle: {b['angle']}")
    if b.get("hooks"): lines.append("Hooks: " + " | ".join(b["hooks"][:3]))
    if b.get("titles"): lines.append("Titles: " + " | ".join(b["titles"][:3]))
    if b.get("must"): lines.append("Must include: " + "; ".join(b["must"][:4]))
    if b.get("avoid"): lines.append("Avoid: " + "; ".join(b["avoid"][:3]))
    if sc: lines.append("Scores (Showrunner, 0-10): " + ", ".join(f"{k} {v}" for k, v in sc.items()))
    if s.get("demand") is not None: lines.append(f"Search demand: {s['demand']:.2f} (YouTube search, top results' views, 0-1)")
    return "\n".join(lines)

def _discuss(s, text):
    from whatifs.models import ask
    turns = "\n".join(f"{t['who']}: {t['text']}" for t in (s.get("turns") or [])[-10:])
    r = ask("owner_chat_deep", COACH, f"CURRENT BRIEF: {json.dumps(s.get('brief') or {'premise': s.get('idea')}, ensure_ascii=False)}\nCONVERSATION:\n{turns}\nOWNER: {text}",
            want_json=True, max_tokens=1500, fake_key="owner_brief")
    r = r if isinstance(r, dict) else {}
    if FAKE and not r.get("brief"):
        r = {"reply": "Strong start. I tightened the premise and gave Grimm a doomed demo.", "brief": {"premise": s.get("idea"), "angle": "the first 8 minutes nobody notices",
             "hooks": ["At 12:00 the Sun died. Nobody noticed.", "Eight minutes of borrowed light.", "Grimm has a stopwatch."], "titles": ["What If the Sun Died at Noon?"] * 1,
             "must": ["8 min 20 s light delay"], "avoid": ["panic clichés"]}, "scores": {"curiosity": 8, "visual": 8, "science": 7, "fit": 9}, "question": "Earth's view or the Moon's?"}
    if r.get("brief"): s["brief"] = {**(s.get("brief") or {}), **{k: v for k, v in r["brief"].items() if v}}
    if r.get("scores"): s["scores"] = r["scores"]
    try:
        from whatifs import demand as DM
        prem = (s.get("brief") or {}).get("premise") or s.get("idea")
        if prem and prem != s.get("demand_for"): s["demand"] = round(DM.score_views(DM._views_for(prem[:90])), 2); s["demand_for"] = prem
    except Exception: pass
    return str(r.get("reply") or "").strip() + (f"\n\nQuestion: {r['question']}" if r.get("question") else "")

def handle(text):
    """Returns (reply_text, buttons) when the message belongs to the brief flow, else None."""
    t = str(text or "").strip(); low = t.lower(); s = state()
    m = START_RX.match(t)
    if m and m.group(2).strip():
        s = {"active": True, "target": "reel" if "reel" in m.group(1).lower() else "video", "idea": m.group(2).strip()[:300], "turns": [], "started": iso()}
    elif not s.get("active"): return None
    elif low in ("cancel", "stop brief", "cancel brief"): _save({}); return "Brief cancelled. Nothing changed.", [("Menu", "MENU|menu")]
    elif low in ("show brief", "brief?", "show"): return card(s), [("Lock it", "BRIEF|lock"), ("Cancel", "BRIEF|cancel")]
    elif low in ("lock", "lock it", "go", "approved", "approve"): return lock()
    s.setdefault("turns", []).append({"who": "OWNER", "text": t[:600]})
    reply = _discuss(s, t)
    s["turns"].append({"who": "SHOWRUNNER", "text": reply[:600]}); _save(s)
    return f"{reply}\n\n{card(s)}", [("Lock it", "BRIEF|lock"), ("Show brief", "BRIEF|show"), ("Cancel", "BRIEF|cancel")]

def lock():
    s = state()
    if not s.get("active"): return "There is no open brief. Start one with: brief <your idea>", [("Menu", "MENU|menu")]
    b = s.get("brief") or {"premise": s.get("idea")}; bid = "OB" + now_utc().strftime("%Y%m%d%H%M")
    rec = {"premise": b.get("premise") or s.get("idea"), "headline": (b.get("titles") or [b.get("premise") or s.get("idea")])[0], "brief": b, "brief_id": bid, "set_at": iso()}
    set_setting("OWNER_NEXT_PREMISE" if s.get("target") != "reel" else "OWNER_SPECIAL_TOPIC", json.dumps(rec))
    store().append("Owner_Briefs", [{"ts": iso(), "id": bid, "target": s.get("target"), "premise": rec["premise"][:300], "brief_json": json.dumps(b)[:4000],
                                     "scores_json": json.dumps(s.get("scores") or {}), "demand": s.get("demand", ""), "status": "LOCKED", "episode_id": "", "outcome_json": ""}])
    _save({})
    if s.get("target") == "reel":
        return f"Locked for the next special reel: '{rec['premise']}'. It still waits for your Approve before posting.", [("Make it now", "BRIEF|reelnow"), ("Menu", "MENU|menu")]
    return (f"Locked: the next long video is '{rec['premise']}' (your brief goes to the whole writers' room). Want a Script Preview first?",
            [("Preview now", "BRIEF|preview"), ("Menu", "MENU|menu")])

def button(payload):
    act = payload.split("|", 1)[1] if "|" in payload else ""
    if act == "lock": return lock()
    if act == "cancel": _save({}); return "Brief cancelled.", [("Menu", "MENU|menu")]
    if act == "show": return card(state()), [("Lock it", "BRIEF|lock"), ("Cancel", "BRIEF|cancel")]
    if act in ("preview", "reelnow"):
        try:
            from whatifs import builds as BL
            BL.dispatch("preview.yml" if act == "preview" else "special.yml", {} if act == "preview" else {"kind": "special"})
            return ("Script Preview started: it arrives as a draft for your approval." if act == "preview" else "Making the reel now: it waits for your Approve."), [("Menu", "MENU|menu")]
        except Exception as e: return f"Could not start it ({scrub(e)[:80]}); it will be used at the next slot anyway.", [("Menu", "MENU|menu")]
    return "Unknown brief action.", [("Menu", "MENU|menu")]

# ---------------------------------------------------------------- use in production
def take_for_episode(episode):
    """The locked owner premise as a FORCED pitch for the scout (consumed once). None when there is none."""
    raw = S("OWNER_NEXT_PREMISE")
    if not str(raw or "").strip(): return None
    try: r = json.loads(raw)
    except Exception: set_setting("OWNER_NEXT_PREMISE", ""); return None
    set_setting("OWNER_NEXT_PREMISE", ""); set_setting("OWNER_BRIEF_ACTIVE", json.dumps(r.get("brief") or {})[:6000])
    try: store().update("Owner_Briefs", "id", r.get("brief_id"), {"status": "USED", "episode_id": episode})
    except Exception: pass
    log(f"owner brief {r.get('brief_id')} is this episode's premise", episode=episode)
    return {"premise": r.get("premise"), "headline": r.get("headline") or r.get("premise"), "family": "", "ptype": "", "teased": True, "owner": True,
            "scores": {"grasp": 9, "pull": 9}, "total": 999, "combined": 99}

def brief_block():
    """The locked brief for every room role (the showrunner and writers follow it)."""
    raw = S("OWNER_BRIEF_ACTIVE")
    if not str(raw or "").strip(): return ""
    return "\nOWNER BRIEF (decided with the owner; follow its angle, use one of its hooks or a better one, include its must-haves, avoid its avoids): " + str(raw)[:2500]

# ---------------------------------------------------------------- learning from it (evidence only)
def learn(now=None):
    """Weekly: owner briefs used >= 7 days ago get their outcome vs the channel median (views at the last pull). Owner picks at or above the median
    become calibration examples (OWNER_TASTE_PROVEN) for the scout and the research brief. Returns the lessons written."""
    st = store(); an = {r.get("episode_id"): r for r in st.rows("Analytics") if r.get("episode_id")}
    views = [float(r.get("views") or 0) for r in an.values() if r.get("views") not in (None, "")]
    if len(views) < 3: return []
    med = statistics.median(views); out = []
    proven = json.loads(S("OWNER_TASTE_PROVEN") or "[]")
    for b in st.rows("Owner_Briefs"):
        if b.get("status") != "USED" or b.get("outcome_json") or b.get("episode_id") not in an: continue
        a = an[b["episode_id"]]; v = float(a.get("views") or 0); ratio = v / med if med else 0
        oc = {"views": v, "channel_median": med, "ratio": round(ratio, 2), "ctr": a.get("ctr"), "avg_view_pct": a.get("avg_view_pct"), "src": "Analytics", "at": iso()}
        st.update("Owner_Briefs", "id", b["id"], {"outcome_json": json.dumps(oc), "status": "MEASURED"})
        lesson = f"Owner brief '{b.get('premise', '')[:70]}': {v:.0f} views = {ratio:.1f}x the channel median ({med:.0f})"
        if ratio >= 1.0: proven.append({"premise": b.get("premise"), "ratio": round(ratio, 2)}); lesson += " -> added to the scout's proven examples"
        out.append(lesson)
    set_setting("OWNER_TASTE_PROVEN", json.dumps(proven[-12:]))
    for l in out: log(l)
    return out

def taste_block():
    try: pr = json.loads(S("OWNER_TASTE_PROVEN") or "[]")
    except Exception: pr = []
    return ("\nOWNER'S PROVEN PICKS (measured: at or above the channel median; prefer premises with this kind of pull): " + json.dumps(pr[-8:], ensure_ascii=False)) if pr else ""
