"""v9.4b (WhatsApp control room, K131): the owner's WhatsApp is a second remote for the same verbs as Mission Control, plus a late-night chat.

Outbound: notify.send(tier='now') -> send_action(row): inside 24 h of the owner's last message = interactive reply buttons (free);
          outside it = the approved utility template WA_TEMPLATE_NAME ('re_action': the text + numbered options, quick replies 1/2/3 whose payloads
          are 'ACT|<id>|<n>'). Every send is logged in WA_Outbox; delivery statuses come back through the relay. The email copy always goes too
          (notify), so a WhatsApp failure never loses a message.
Inbound (relay Worker -> repository_dispatch 'wa_inbound', AES-GCM): button payloads are routed exactly like dashboard taps (dash.route);
          text = 'status' | 'pause' | 'resume' | 'think hard: ...' | anything else -> the chat brain (Sonnet; Opus for 'think hard'; Haiku after
          CHAT_MONTHLY_CAP_INR), which answers honestly and, for a concrete idea, offers [Build it] [Park] (a Claude Code build on the owner's plan).
Never prints message text (public logs, K32). The owner's number is the only accepted sender (the Worker drops everyone else)."""
from __future__ import annotations
import datetime as dt, json, os, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, set_setting, scrub, FAKE

def configured():
    return bool(S("WA_ON", bool) and env("WA_TOKEN") and env("WA_PHONE_ID") and env("OWNER_WA"))

def in_window(now=None):
    t = parse_iso(S("WA_LAST_INBOUND_AT")); now = now or now_utc()
    return bool(t and (now - t).total_seconds() < 23.5 * 3600)

def _post(body):
    """POST one message. Returns the WhatsApp message id or ''."""
    if FAKE: return "wamid.FAKE." + now_utc().strftime("%H%M%S%f")
    import requests
    url = f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_PHONE_ID')}/messages"
    r = requests.post(url, headers={"Authorization": f"Bearer {env('WA_TOKEN')}"}, json={"messaging_product": "whatsapp", "to": env("OWNER_WA"), **body}, timeout=30)
    if r.status_code >= 300: log(f"WhatsApp send failed {r.status_code}", "WARN"); return ""
    try: return r.json()["messages"][0]["id"]
    except Exception: return ""

def _plain(t): return re.sub(r"\s{4,}", "   ", re.sub(r"[\r\n\t]+", " ", re.sub(r"<[^>]+>", "", str(t or "")))).strip()

def send_text(text):
    return _post({"type": "text", "text": {"body": _plain(text)[:4000]}})

def send_buttons(text, buttons):
    """Up to 3 reply buttons [(title, id)]; titles are cut to 20 characters (WhatsApp limit)."""
    bs = [{"type": "reply", "reply": {"id": str(i)[:256], "title": str(t)[:20]}} for t, i in buttons[:3]]
    return _post({"type": "interactive", "interactive": {"type": "button", "body": {"text": _plain(text)[:1024]}, "action": {"buttons": bs}}})

MENU_ROWS = [("today", "Today", "next slot, what's being made"), ("numbers", "Numbers", "views, retention, subs + chart"),
             ("hot_topics", "Hot topics", "cited signals this week"), ("recommendations", "What to post", "next cases + Shorts ideas"),
             ("observations", "Observations", "what the engine noticed"), ("strategy", "Strategy", "the plan and why"),
             ("experiments", "Experiments", "tests running"), ("money", "Spend", "money vs cap + chart")]

def send_list(text, button, rows, header="Reality Engine"):
    """Interactive list (max 10 rows; title <= 24, description <= 72 characters). rows = [(id, title, description)]."""
    sec = [{"title": "Menu", "rows": [{"id": str(i)[:200], "title": str(t)[:24], "description": str(dd)[:72]} for i, t, dd in rows[:10]]}]
    return _post({"type": "interactive", "interactive": {"type": "list", "header": {"type": "text", "text": header[:60]}, "body": {"text": _plain(text)[:1024]},
                                                         "action": {"button": str(button)[:20], "sections": sec}}})

def send_image(path, caption=""):
    """Upload a PNG to WhatsApp's media store, then send it as an image message with a caption. Returns the message id or ''."""
    if not path or not os.path.exists(path): return ""
    if FAKE: return _post({"type": "image", "image": {"id": "FAKE_MEDIA_" + os.path.basename(path), "caption": _plain(caption)[:1000]}})
    import requests
    up = requests.post(f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_PHONE_ID')}/media", headers={"Authorization": f"Bearer {env('WA_TOKEN')}"},
                       data={"messaging_product": "whatsapp", "type": "image/png"}, files={"file": (os.path.basename(path), open(path, "rb"), "image/png")}, timeout=60)
    if up.status_code >= 300: log(f"WhatsApp image upload failed {up.status_code}", "WARN"); return ""
    return _post({"type": "image", "image": {"id": up.json().get("id"), "caption": _plain(caption)[:1000]}})

def send_menu(text="What do you want to see?"):
    return send_list(text, "Menu", [(f"MENU|{k}", t, dd) for k, t, dd in MENU_ROWS])

def send_section(name, demo=False):
    """One section: the text (with sources), a chart for Numbers/Spend, and 3 buttons to move on. Returns what was sent (for the log)."""
    from whatifs import owner_view as OV, charts as CH
    view = OV.build(demo=demo)
    txt = OV.render(name, view)
    chart = CH.numbers_chart(view) if name == "numbers" else (CH.money_chart(view) if name == "money" else None)
    if chart: send_image(chart, OV.TITLES.get(name, name) + (" (DEMO)" if demo else ""))
    nxt = {"today": "numbers", "numbers": "observations", "observations": "recommendations", "recommendations": "hot_topics", "hot_topics": "strategy",
           "strategy": "experiments", "experiments": "money", "money": "today"}.get(name, "today")
    send_buttons(txt, [("Menu", "MENU|menu"), (OV.TITLES[nxt][:20], f"MENU|{nxt}"), ("Pause" if not S("PAUSED", bool) else "Resume", "PAUSE" if not S("PAUSED", bool) else "RESUME")])
    return txt + (f"\n[chart: {os.path.basename(chart)}]" if chart else "")

def send_template(text, options, payloads):
    """The approved utility template: {{1}} = the text, {{2}} = '1) A  2) B  3) C'; quick replies 1/2/3 carry the payloads."""
    comps = [{"type": "body", "parameters": [{"type": "text", "text": _plain(text)[:900]}, {"type": "text", "text": _plain("  ".join(f"{i + 1}) {o}" for i, o in enumerate(options)))[:200] or "-"}]}]
    for i, p in enumerate(payloads[:3]):
        comps.append({"type": "button", "sub_type": "quick_reply", "index": str(i), "parameters": [{"type": "payload", "payload": str(p)[:256]}]})
    return _post({"type": "template", "template": {"name": S("WA_TEMPLATE_NAME"), "language": {"code": S("WA_TEMPLATE_LANG")}, "components": comps}})

def _outbox(wamid, aid, kind, status="sent"):
    store().append("WA_Outbox", [{"ts": iso(), "wamid": wamid, "action_id": aid or "", "kind": kind or "", "status": status}])

def send_action(row):
    """notify hook for 'now' messages. Never raises."""
    if not configured(): return ""
    try:
        btns = json.loads(row.get("buttons") or "[]")
        if row.get("kind") == "build_ready":
            m = re.search(r"#(\d+)", row.get("text", "")); n = m.group(1) if m else ""
            pairs = [("Merge", f"MERGE|{n}"), ("Reject", f"REJECT|{n}")]
        else:
            pairs = [(str(lbl), f"ACT|{row['id']}|{i}") for i, (lbl, _v) in enumerate(btns)]
        text = row.get("text", "") + (f"  (If you do nothing: {row['default_action']})" if row.get("default_action") else "")
        wamid = send_buttons(text, pairs) if (in_window() and pairs) else (send_template(text, [p[0] for p in pairs], [p[1] for p in pairs]) if pairs else send_text(text))
        if wamid: _outbox(wamid, row.get("id"), row.get("kind"))
        return wamid
    except Exception as e:
        log(f"WhatsApp message not sent ({type(e).__name__}); the email copy went", "WARN"); return ""

# ------------------------------------------------------------------ inbound
def _chat_spend():
    from whatifs.governor import month_spend_of
    return month_spend_of(["owner_chat"])

def _history(n=12):
    rows = store().rows("WA_Chat")[-n:]
    return "\n".join(f"{r.get('who')}: {str(r.get('text'))[:600]}" for r in rows)

CHAT_SYSTEM = ("You are the Reality Engine's assistant on the owner's WhatsApp. The owner is not technical and reads on a phone: plain short sentences, "
               "brutally honest, no flattery. You know the channel only from the CONTEXT JSON. Never invent numbers. You cannot change the budget cap, "
               "quality gates or secrets; say which Settings cell the owner would change instead. When the owner proposes a concrete change and agrees to it, "
               "end your reply with ONE line 'SPEC: <what to build, plain words, with the switch to turn it off>' and 'KIND: tweak' or 'KIND: feature'. "
               "Otherwise no SPEC line.")

def chat(text, deep=False):
    """One chat turn. Returns (reply_text, spec, kind)."""
    from whatifs.models import ask
    from whatifs import dash as DS
    cap = S("CHAT_MONTHLY_CAP_INR", float); spent = _chat_spend()
    role = "owner_chat_deep" if deep else ("owner_chat_cheap" if spent >= cap else "owner_chat")
    snap = DS.build_snapshot()
    ctx = {"engine": snap.get("engine"), "money": {k: snap["money"].get(k) for k in ("month_spend", "cap", "credit_cover")}, "open_items": len(snap.get("docket", [])),
           "progress": snap.get("progress", {}).get("kpis"), "learned": snap.get("learned")}
    try:                                                         # v10.3: the same sections as the dashboard (numbers, hot topics, recommendations...)
        from whatifs import owner_view as OV
        ov = OV.build(); ctx["owner_view"] = {k: ov.get(k) for k in ("today", "numbers", "hot_topics", "recommendations", "observations", "strategy", "experiments", "money")}
    except Exception: pass
    prompt = (f"CONTEXT (every number has a src; cite the src when you use a number; say 'no data yet' when a section is empty; label guesses as interpretation): "
              f"{json.dumps(ctx, ensure_ascii=False, default=str)[:12000]}\nRECENT CHAT:\n{_history()}\nOWNER: {text}")
    reply = ask(role, CHAT_SYSTEM, prompt, want_json=False, max_tokens=1200 if not deep else 3000, fake_key="owner_chat")
    reply = str(reply or "").strip()
    m = re.search(r"^SPEC:\s*(.+)$", reply, re.M); k = re.search(r"^KIND:\s*(tweak|feature)", reply, re.M | re.I)
    spec = m.group(1).strip() if m else ""; kind = (k.group(1).lower() if k else "feature")
    clean = re.sub(r"^(SPEC|KIND):.*$", "", reply, flags=re.M).strip()
    meter = f"(chat this month: Rs {_chat_spend():.0f} of Rs {cap:.0f}{'; cheap model now' if role == 'owner_chat_cheap' else ''})"
    return f"{clean}\n{meter}", spec, kind

def _idea_answer(row, choice):
    if str(choice).upper().startswith("BUILD"):
        from whatifs.builds import request_build
        spec = json.loads(row.get("buttons") or "[]")
        meta = json.loads(row.get("dedupe_key", "").split("|", 2)[2] or "{}") if row.get("dedupe_key", "").startswith("idea|") else {}
        ok = request_build(meta.get("spec") or row.get("text", ""), meta.get("kind", "feature"))
        return "build started" if ok else "build could not start"
    return "parked"

def register():
    from whatifs import notify as NT
    NT.register("idea", on_answer=_idea_answer)
    NT.register("wa_set", on_answer=lambda row, choice: __import__("whatifs.dash", fromlist=["route"]).route(choice)[1])

def _reply(text): send_text(text)

def handle_inbound(payload_json):
    """repository_dispatch 'wa_inbound' entry point. Returns the number of messages handled."""
    from whatifs import dash as DS, notify as NT
    register()
    try: msg = DS.decrypt(json.loads(payload_json) if isinstance(payload_json, str) else payload_json)
    except Exception as e: log(f"WhatsApp payload not readable ({type(e).__name__})", "WARN"); return 0
    st = store(); seen = {r.get("msg_id") for r in st.rows("WA_Chat")}; n = 0
    for s in msg.get("statuses", []) or []:
        for r in st.rows("WA_Outbox"):
            if r.get("wamid") == s.get("id"): st.update("WA_Outbox", "wamid", s["id"], {"status": str(s.get("status"))[:20]})
    for m in msg.get("messages", []) or []:
        mid = str(m.get("id") or "")
        if not mid or mid in seen: continue
        seen.add(mid); n += 1; set_setting("WA_LAST_INBOUND_AT", iso())
        payload, text = str(m.get("payload") or ""), str(m.get("text") or "").strip()
        st.append("WA_Chat", [{"ts": iso(), "msg_id": mid, "who": "owner", "text": (payload or text)[:1500]}])
        try:
            if payload.startswith("BRIEF|") or (not payload):               # v10.3 (K154): the owner-brief conversation (start, continue, lock)
                from whatifs import owner_brief as OB
                r = OB.button(payload) if payload.startswith("BRIEF|") else OB.handle(text)
                if r:
                    out, btns = r; send_buttons(out[-1020:], btns)
                    st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
            if payload.startswith("MENU|"):                              # v10.3: the menu system (list rows and buttons carry MENU|<section>)
                sec = payload.split("|", 1)[1]
                if sec == "menu": send_menu(); out = "(menu sent)"
                else: out = send_section(sec)
                st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
            if not payload and text.lower() in ("menu", "hi", "start", "options"):
                send_menu("Hi Rahul. What do you want to see?"); st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": "(menu sent)"}]); continue
            if not payload and text.lower().startswith("demo"):
                parts = text.lower().split(); sec = parts[1] if len(parts) > 1 and parts[1] in dict((k, 1) for k, _, _ in MENU_ROWS) else "numbers"
                out = send_section(sec, demo=True); st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
            if payload and re.match(r"^[A-Z]{2,12}(\|[A-Za-z0-9_.:+\-]{0,80}){0,3}$", payload):
                ok, note = DS.route(payload); out = ("Done: " if ok else "Not done: ") + str(note)
            elif m.get("type") in ("image", "video", "document"):
                out = "I can read text and links here. Screenshots and videos: send the link, or describe what you liked."
            else:
                low = text.lower()
                if low in ("status", "stats", "how are we doing"):
                    snap = DS.build_snapshot(); mo = snap["money"]; nr = (snap["engine"] or {}).get("next_release") or {}
                    out = (f"Engine {snap['engine']['status']} ({snap['engine']['mode']}). Spend Rs {mo['month_spend']} of Rs {mo['cap']}. "
                           f"Next: {nr.get('title') or '-'} at {str(nr.get('slot_iso') or '-')[:16]} UTC. Waiting for you: {len(snap['docket'])}.")
                elif low in ("pause", "resume"):
                    ok, note = DS.route(low.upper()); out = ("Done: " if ok else "Not done: ") + note
                else:
                    deep = low.startswith("think hard")
                    out, spec, kind = chat(re.sub(r"^think hard:?\s*", "", text, flags=re.I) if deep else text, deep=deep)
                    if spec:
                        aid = NT.send("idea", f"Build this? {spec}", [("Build it", "BUILD"), ("Park", "PARK")], tier="fyi", default="parked", expires_h=24 * 7,
                                      dedupe_key="idea|" + mid + "|" + json.dumps({"spec": spec, "kind": kind}))
                        send_buttons(out[-900:] + f"\n\nBuild it ({kind}, on your Claude plan, ₹0 API)?", [("Build it", f"ACT|{aid}|0"), ("Park", f"ACT|{aid}|1")])
                        st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
        except Exception as e:
            out = f"Something failed on my side ({type(e).__name__}). Nothing was changed."
        st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}])
        _reply(out)
    log(f"WhatsApp: {n} message(s) handled"); return n

def ensure_templates():
    """Create the utility template once (Meta approves it in minutes to hours). Returns True when it exists or was submitted."""
    if not (env("WA_TOKEN") and env("WA_WABA_ID")) or FAKE: return False
    import requests
    base = f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_WABA_ID')}/message_templates"
    h = {"Authorization": f"Bearer {env('WA_TOKEN')}"}
    have = requests.get(base, headers=h, params={"name": S("WA_TEMPLATE_NAME")}, timeout=30).json().get("data", [])
    if have: return True
    body = {"name": S("WA_TEMPLATE_NAME"), "language": S("WA_TEMPLATE_LANG"), "category": "UTILITY",
            "components": [{"type": "BODY", "text": "Reality Engine update: {{1}} Your options: {{2}} Tap a button to reply.", "example": {"body_text": [["Video EP12 is held after the quality check.", "1) Fix and post  2) Skip"]]}},
                           {"type": "BUTTONS", "buttons": [{"type": "QUICK_REPLY", "text": "1"}, {"type": "QUICK_REPLY", "text": "2"}, {"type": "QUICK_REPLY", "text": "3"}]}]}
    r = requests.post(base, headers=h, json=body, timeout=30)
    if r.status_code >= 300:                                     # v10.2 (#10): Meta's reason is logged (code/subcode/message; never the token)
        try: er = r.json().get("error", {}); why = f"code {er.get('code')}/{er.get('error_subcode')}: {er.get('error_user_msg') or er.get('message')}"
        except Exception: why = r.text[:200]
        log(f"WhatsApp template REJECTED ({r.status_code}): {why}", "ERROR"); return False
    log(f"WhatsApp template submitted ({r.status_code})"); return True

def ensure_subscribed():
    """v10.2 (#11): Meta only delivers inbound messages after the app is subscribed to the WhatsApp Business Account (POST subscribed_apps)."""
    if not (env("WA_TOKEN") and env("WA_WABA_ID")) or FAKE: return False
    import requests
    base = f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_WABA_ID')}/subscribed_apps"
    h = {"Authorization": f"Bearer {env('WA_TOKEN')}"}
    r = requests.post(base, headers=h, timeout=30)
    ok = r.status_code < 300 and bool((r.json() or {}).get("success", True))
    log(f"WhatsApp app subscription to the business account: {'OK' if ok else 'FAILED ' + r.text[:160]}", "INFO" if ok else "ERROR"); return ok
