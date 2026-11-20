"""The WhatsApp control room: interactive buttons inside the 24-hour window, the approved template outside it, and inbound owner messages. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, json, os, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, set_setting, scrub, FAKE, _plain      # v12 B-OWNER: _plain lives in core (one definition)

def configured():
    return bool(S("WA_ON", bool) and env("WA_TOKEN") and env("WA_PHONE_ID") and env("OWNER_WA"))

def in_window(now=None):
    t = parse_iso(S("WA_LAST_INBOUND_AT")); now = now or now_utc()
    return bool(t and (now - t).total_seconds() < 23.5 * 3600)

def _on(): return S("TWO_SCREENS_ON", bool)

def _post(body, kind="reply", now=None):
    """POST one message. Returns the WhatsApp message id or ''.
    v12 B-OWNER (switch TWO_SCREENS_ON): THE 24-HOUR WINDOW AT THE WIRE - outside the window nothing but a template is posted (Meta refuses free
    text there, error 131047, and the stand-in refuses it too): a WA_Outbox row "refused_window" is written and '' returned. A message that went is
    billed (`_bill`). `kind` is the push kind (morning, needs, alarm) or "reply"; the older senders call `_post(body)`."""
    if _on() and body.get("type") != "template" and not in_window(now):
        _outbox("", "", kind, "refused_window"); log(f"WhatsApp: a {kind} message outside the 24-hour window was not sent (only the template may go there)", "WARN"); return ""
    wamid = _wire(body)
    if wamid and _on(): _bill(body, kind)
    return wamid

def _wire(body):
    """The wire itself: one POST to Meta (the stand-in answers in fake mode). Returns the message id or ''."""
    if FAKE: return "wamid.FAKE." + now_utc().strftime("%H%M%S%f")
    import requests
    url = f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_PHONE_ID')}/messages"
    r = requests.post(url, headers={"Authorization": f"Bearer {env('WA_TOKEN')}"}, json={"messaging_product": "whatsapp", "to": env("OWNER_WA"), **body}, timeout=30)
    if r.status_code >= 300: log(f"WhatsApp send failed {r.status_code}", "WARN"); return ""
    try: return r.json()["messages"][0]["id"]
    except Exception: return ""

def _go(body, kind=None, now=None):
    """v12 B-OWNER: a push passes its kind and its clock to the wire; every other sender calls `_post(body)` as before."""
    return _post(body) if kind is None else _post(body, kind=kind, now=now)

def _bill(body, kind):
    """v12 B-OWNER (PART 8; item 151: overhead, never a video's money): every delivered message is a Cost_Log row of item "whatsapp", episode "owner"
    (off every video) - a template at PRICE_WA_UTILITY_INR, a message inside the window free while the month's service messages are under
    WA_SERVICE_FREE_PER_MONTH and at PRICE_WA_SERVICE_INR after it. Both prices are stated ceilings, not Meta's rates. Never raises."""
    try:
        from whatifs import core as C, costguard as CG
        tpl = body.get("type") == "template"
        inr = S("PRICE_WA_UTILITY_INR", float) if tpl else (0.0 if CG.owner_messages()["replies"] < S("WA_SERVICE_FREE_PER_MONTH", int) else S("PRICE_WA_SERVICE_INR", float))
        C.cost("whatsapp", "meta", 1, inr / (S("USD_INR", float) or 99.0), episode="owner", role=kind, basis="template" if tpl else "service")
        C.flush_costs()                                           # on the Sheet at once: the cap and the free tier read it
    except Exception as e: log(f"WhatsApp message not billed: {scrub(e)[:120]}", "WARN")

def over_cap():
    """v12 B-OWNER: this month's WhatsApp spend has reached WA_MONTHLY_CAP_INR - the morning message and the "Needs you" list then stop on WhatsApp
    (the dashboard and the mail carry everything). An alarm never asks this."""
    from whatifs import costguard as CG
    m = CG.owner_messages(); return m["spent"] >= m["cap"]

def send_text(text, kind=None, now=None):
    return _go({"type": "text", "text": {"body": _plain(text)[:4000]}}, kind, now)

def send_buttons(text, buttons, kind=None, now=None):
    """Up to 3 reply buttons [(title, id)]; titles are cut to 20 characters (WhatsApp limit)."""
    bs = [{"type": "reply", "reply": {"id": str(i)[:256], "title": str(t)[:20]}} for t, i in buttons[:3]]
    return _go({"type": "interactive", "interactive": {"type": "button", "body": {"text": _plain(text)[:1024]}, "action": {"buttons": bs}}}, kind, now)

MENU_ROWS = [("today", "Today", "next slot, what's being made"), ("numbers", "Numbers", "views, retention, subs + chart"),
             ("hot_topics", "Hot topics", "cited signals this week"), ("recommendations", "What to post", "next cases + Shorts ideas"),
             ("observations", "Observations", "what the engine noticed"), ("strategy", "Strategy", "the plan and why"),
             ("experiments", "Experiments", "tests running"), ("money", "Spend", "money vs cap + chart")]

def send_list(text, button, rows, header="Reality Engine", kind=None, now=None):
    """Interactive list (max 10 rows; title <= 24, description <= 72 characters). rows = [(id, title, description)]."""
    sec = [{"title": "Menu", "rows": [{"id": str(i)[:200], "title": str(t)[:24], "description": str(dd)[:72]} for i, t, dd in rows[:10]]}]
    return _go({"type": "interactive", "interactive": {"type": "list", "header": {"type": "text", "text": header[:60]}, "body": {"text": _plain(text)[:1024]},
                                                       "action": {"button": str(button)[:20], "sections": sec}}}, kind, now)

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

# ------------------------------------------------------------------ v12 B-OWNER (PART 4, item 150): WhatsApp starts THREE kinds of message only
PUSH_KINDS = ("morning", "needs", "alarm")
OPEN_LABELS = {"morning": "Morning message", "needs": "Needs you", "alarm": "ALARM"}
OPEN_BODY = "Reality Engine - {{1}}. {{2}} Tap Open to see everything and to answer."      # THE ONE TEMPLATE, as the pack's C0b submits it (WA_OPEN_TEMPLATE)
MENU_GROUPS = (("needs", "Needs you"), ("posted", "Posted and next"), ("learned", "What we learned"), ("research", "Research & observations"),
               ("plan", "Plan and changes"), ("inputs", "Your inputs"), ("money", "Money"), ("decided", "Decided for you"))      # the eight groups (notify.GROUPS)
SECTIONS = {"posted": ("today", "numbers"), "learned": ("experiments", "learned"), "research": ("hot_topics", "observations"),
            "plan": ("strategy", "recommendations"), "money": ("money",)}      # R18 (7 g): each group opens with the older sections it replaces

def _one_line(text):
    """A template's parameter holds no line break, tab or run of spaces (Meta refuses them)."""
    return re.sub(r"\s+", " ", _plain(text)).strip()

def open_template():
    """The Open template as `ensure_templates` submits it (category UTILITY; {{1}} the label, {{2}} the head; ONE quick reply "Open")."""
    return {"name": S("WA_OPEN_TEMPLATE"), "language": S("WA_TEMPLATE_LANG"), "category": "UTILITY",
            "components": [{"type": "BODY", "text": OPEN_BODY, "example": {"body_text": [["Needs you", "2 decisions wait; the first closes at 18:30 (A goes out)."]]}},
                           {"type": "BUTTONS", "buttons": [{"type": "QUICK_REPLY", "text": "Open"}]}]}

def send_open(label, line, payload, kind="reply", now=None):
    """THE ONE TEMPLATE outside the 24-hour window: {{1}} = the label, {{2}} = one line (an alarm's whole text, cut at 700 characters); the quick reply
    "Open" carries `payload` (OPEN|morning, OPEN|needs, OPEN|alarm|<id>). His tap is a message of his: it opens the window, and the list comes as a reply."""
    from whatifs import notify as NT                                     # FINISHED BY FABLE (CA-7b, R1-55): the template's line never holds half an address
    comps = [{"type": "body", "parameters": [{"type": "text", "text": _one_line(label)[:60]}, {"type": "text", "text": NT.whole(_one_line(line), 700) or "-"}]},
             {"type": "button", "sub_type": "quick_reply", "index": "0", "parameters": [{"type": "payload", "payload": str(payload)[:256]}]}]
    return _post({"type": "template", "template": {"name": S("WA_OPEN_TEMPLATE"), "language": {"code": S("WA_TEMPLATE_LANG")}, "components": comps}}, kind=kind, now=now)

def _hhmm(ts):
    t = parse_iso(ts); return t.astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%H:%M") if t else ""

def _decision(r):
    """A decision's list row: (CARD|<id>, its plain name, "<default> at HH:MM") - India time; a hold waits for his tap."""
    from whatifs import notify as NT
    d = r.get("default_action") or "it waits for your tap"; at = _hhmm(r.get("expires_at"))
    return (f"CARD|{r['id']}", NT.name(r.get("kind")), f"{d} at {at}" if at else d)

def _decisions():
    from whatifs import notify as NT
    return sorted(NT.needs(), key=lambda r: (str(r.get("expires_at") or "9999"), str(r.get("created") or "")))      # the earliest expiry first

def _menu_rows():
    from whatifs import notify as NT
    n = {g: len(NT.group_rows(g)) for g, _t in MENU_GROUPS}
    return [(f"MENU|{g}", t, (f"{n[g]} to decide" if g == "needs" else f"{n[g]} open")) for g, t in MENU_GROUPS]

def push(kind, row=None, now=None, text=""):
    """v12 B-OWNER (item 150): THE ONLY FUNCTION THAT STARTS A MESSAGE TO HIM, and only of three kinds - "morning" (one list: the head `text` and the
    eight groups), "needs" (one list: a row a decision, the earliest expiry first) and "alarm" (`row`: its text and its buttons). Inside the window
    the message itself; outside it THE ONE TEMPLATE with "Open". Everything else WhatsApp sends is a reply to a message of his. Returns the message
    id or ''. Acts when WhatsApp is set up (or in fake mode); every push that went is a WA_Outbox row of its kind and a Cost_Log row."""
    if kind not in PUSH_KINDS: raise ValueError(f"WhatsApp starts three kinds of message only, never '{kind}'")
    if not (configured() or FAKE): return ""
    now = now or now_utc()
    wamid = _push_alarm(row, now) if kind == "alarm" else _push_list(kind, now, text)
    if wamid: _outbox(wamid, (row or {}).get("id"), kind)
    return wamid

def _push_alarm(row, now):
    """The alarm (item 180): its text with its buttons, or the template with the whole text. It reads NO quiet hours, NO daily cap, NO WhatsApp
    money cap, NO lever, NO Palace item and calls no model."""
    text = str(row.get("text") or "") + (f" If you do nothing: {row['default_action']}." if row.get("default_action") else "")
    if in_window(now):
        btns = json.loads(row.get("buttons") or "[]")
        pairs = [(str(lbl), f"ACT|{row['id']}|{i}") for i, (lbl, _v) in enumerate(btns)]
        return send_buttons(text, pairs, kind="alarm", now=now) if pairs else send_text(text, kind="alarm", now=now)
    from whatifs import notify as NT                                     # FINISHED BY FABLE (CA-7b, R1-55): cut whole here, or send_open would get half an address
    return send_open(OPEN_LABELS["alarm"], NT.whole(text, 700), f"OPEN|alarm|{row['id']}", kind="alarm", now=now)

def _push_list(kind, now, text):
    """The morning message and the "Needs you" list. Over WA_MONTHLY_CAP_INR they stop on WhatsApp, and one `wa_cap` row says so."""
    from whatifs import notify as NT
    if over_cap():
        NT.send("wa_cap", f"WhatsApp reached its monthly cap of Rs {S('WA_MONTHLY_CAP_INR', float):.0f}: the {OPEN_LABELS[kind].lower()} went to the dashboard and your e-mail only.", tier="week")
        return ""
    rows = _decisions()
    if kind == "needs":
        if not rows: return ""                                   # no decision open = no message
        more = len(rows) - 10
        line = f"Needs you: {len(rows)} decision{'s' if len(rows) != 1 else ''}." + (f" And {more} more on the dashboard." if more > 0 else "")
        if in_window(now): return send_list(line, "Open", [_decision(r) for r in rows[:10]], kind="needs", now=now)
        first = rows[0] if rows else {}
        head = line + (f" The first closes at {_hhmm(first.get('expires_at'))}: {first.get('default_action')}." if first.get("expires_at") and first.get("default_action") else "")
        return send_open(OPEN_LABELS["needs"], head, "OPEN|needs", kind="needs", now=now)
    if in_window(now): return send_list(text or OPEN_LABELS["morning"], "Open", _menu_rows(), kind="morning", now=now)
    return send_open(OPEN_LABELS["morning"], text, "OPEN|morning", kind="morning", now=now)

def group_text(g, view=None, now=None, cut=1024):
    """One group as text: its title, the older sections it replaces (`owner_view.render`, R18 (7 g)), then its own rows. Cut at a line within `cut`
    characters, ending "more on the dashboard" (`cut` None = whole: the morning mail)."""
    from whatifs import notify as NT, owner_view as OV, digests as DG
    title = dict(MENU_GROUPS)[g]; parts = [f"*{title}*"]
    secs = SECTIONS.get(g, ())
    if secs:
        view = view or OV.build()
        parts += [DG.learned() if s == "learned" else OV.render(s, view) for s in secs]
    rows = NT.group_rows(g, now)
    parts.append("\n".join(f"- {NT.whole(r.get('text') or '', 300)}" + (f" ({NT.ran_label(r)})" if r.get("status") == "DEFAULTED" else "") for r in rows) if rows else "Nothing here now.")
    out = "\n\n".join(p for p in parts if p)
    if cut and len(out) > cut:
        tail = "\n... more on the dashboard"; keep = out[:cut - len(tail)]
        out = keep[:keep.rfind("\n")] + tail if "\n" in keep else keep + tail
    return out

def _group_action(g):
    """A group's own button: "needs" opens the list; "decided" opens the newest row of the group that carries a button (Undo, Take it down)."""
    from whatifs import notify as NT
    if g == "needs": return ("Open the list", "OPEN|needs")
    if g == "decided":
        r = next((x for x in NT.group_rows("decided") if x.get("status") in ("OPEN", "QUEUED") and json.loads(x.get("buttons") or "[]")), None)
        if r: return ("Undo or take down", f"CARD|{r['id']}")
    return None

def _button(title):
    """A group's title as a reply button (20 characters, S4): whole, or its first part ("Research & observations" -> "Research") - never cut mid-word."""
    return title if len(title) <= 20 else title.split(" & ")[0][:20]

def send_group(g, demo=False):
    """A reply: one group - its chart first where the older section had one (numbers before Posted, money before Money), its text, and up to three
    buttons: Menu, the next group, the group's own action."""
    from whatifs import owner_view as OV, charts as CH
    view = OV.build(demo=demo)
    chart = CH.numbers_chart(view) if g == "posted" else (CH.money_chart(view) if g == "money" else None)
    if chart: send_image(chart, dict(MENU_GROUPS)[g])
    txt = group_text(g, view)
    names = [x for x, _t in MENU_GROUPS]; nxt = names[(names.index(g) + 1) % len(names)]
    btns = [("Menu", "MENU|menu"), (_button(dict(MENU_GROUPS)[nxt]), f"MENU|{nxt}")] + ([_group_action(g)] if _group_action(g) else [])
    send_buttons(txt, btns)
    return txt + (f"\n[chart: {os.path.basename(chart)}]" if chart else "")

def send_card(aid):
    """A reply: one row - its text, what his silence does, and its buttons (more than three: a list whose rows are ACT|<id>|<i>)."""
    row = next((r for r in store().rows("Owner_Actions") if r.get("id") == aid), None)
    if not row: send_text("That message is no longer open."); return "(no such row)"
    btns = json.loads(row.get("buttons") or "[]"); at = _hhmm(row.get("expires_at"))
    text = str(row.get("text") or "") + (f"\nIf you do nothing: {row['default_action']}" + (f" (from {at})" if at else "") + "." if row.get("default_action") else "")
    pairs = [(str(lbl), f"ACT|{aid}|{i}") for i, (lbl, _v) in enumerate(btns)] if row.get("status") in ("OPEN", "QUEUED") else []
    if len(pairs) > 3: send_list(text, "Choose", [(p, lbl, "") for lbl, p in pairs])
    elif pairs: send_buttons(text, pairs)
    else: send_text(text + ("" if row.get("status") in ("OPEN", "QUEUED") else f"\n({str(row.get('status')).lower()})"))
    return text

def send_menu_groups(text="What do you want to see?"):
    """A reply: the eight groups as one list - the menu IS the eight groups (item 150)."""
    return send_list(text, "Open", _menu_rows())

def send_action(row):
    """notify hook for 'now' messages. Never raises.
    v12 B-OWNER: with TWO_SCREENS_ON only an ALARM row starts a message (`push("alarm")`); every other row waits for the two lists."""
    if _on():
        from whatifs import notify as NT
        try: return push("alarm", row) if NT.klass(row["kind"]) == NT.ALARM else ""
        except Exception as e: log(f"WhatsApp alarm not sent ({type(e).__name__})", "WARN"); return ""
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
    if _on(): return month_spend_of(["owner_chat", "owner_desk", "whatsapp"])      # v12 B-OWNER (R17 (9 b)): WhatsApp and the desk live INSIDE the chat's cap
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

def reply_answer(text, now=None):
    """v12 B-OWNER (PART 5): the desk's answer, weighed at a tick, as a REPLY while his 24-hour window is still open - never a new message (outside the
    window, and in his quiet hours, it waits for the morning message). Returns the message id or ''."""
    from whatifs import notify as NT
    if not in_window(now) or NT.in_quiet_hours(now): return ""      # FINISHED BY FABLE (CB-4): never in his quiet hours - the morning message carries the answer
    return send_text(text, kind="reply", now=now)                   # the wire's guard and the bill read the caller's clock (`_go` drops `now` when no kind is passed)

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
            if _on() and (payload.startswith("OPEN|") or payload.startswith("CARD|")):      # v12 B-OWNER: his tap on "Open", or on a row of a list
                p = payload.split("|")
                if p[0] == "CARD" or p[1:2] == ["alarm"]: out = send_card(p[-1])
                elif p[1:2] == ["needs"]:
                    rows = _decisions(); out = "(the needs list)"
                    if rows: send_list(f"Needs you: {len(rows)}.", "Open", [_decision(r) for r in rows[:10]])
                    else: send_text("Nothing needs you now."); out = "(nothing needs you)"
                else: send_menu_groups(); out = "(the eight groups)"
                st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
            if payload.startswith("MENU|"):                              # v10.3: the menu system (list rows and buttons carry MENU|<section>)
                sec = payload.split("|", 1)[1]
                if _on() and sec == "menu": send_menu_groups(); out = "(the eight groups)"       # v12 B-OWNER (R18 (7 f)): the menu IS the eight groups
                elif _on() and sec in dict(MENU_GROUPS): out = send_group(sec)
                elif sec == "menu": send_menu(); out = "(menu sent)"
                else: out = send_section(sec)
                st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": out[:1500]}]); continue
            if not payload and text.lower() in ("menu", "hi", "start", "options"):
                if _on(): send_menu_groups()
                else: send_menu("Hi Rahul. What do you want to see?")
                st.append("WA_Chat", [{"ts": iso(), "msg_id": mid + ".r", "who": "assistant", "text": "(menu sent)"}]); continue
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
                    deep = low.startswith("think hard"); line = ""
                    if _on():                                    # v12 B-OWNER (PART 5, R17 (10 a)): ONE place - a typed line that is not a fixed word is his input,
                        from whatifs.org import desk as DESK      # taken BEFORE the chat answers; a bare acknowledgement is talk (R17 ADDS (D))
                        if not DESK.talk(text): _n, line = DESK.take(text, "whatsapp", ref=mid)
                    out, spec, kind = chat(re.sub(r"^think hard:?\s*", "", text, flags=re.I) if deep else text, deep=deep)
                    if line: out = f"{out}\n\n{line}"                # the desk's verdict ends the chat's reply
                    if spec:
                        never_parked = _on(); aid = ""           # v12 B-OWNER: his idea is never parked by silence - no default, no expiry, open until he taps
                        if never_parked:                         # FINISHED BY FABLE (CB-1): ONE card a line - where the desk made its own `idea` row for this message, that row is the card
                            d = next((x for x in st.rows("Owner_Desk") if str(x.get("ref") or "") == mid), None)
                            a = next((x for x in st.rows("Owner_Actions") if x.get("id") == d.get("action")), None) if d and d.get("action") else None
                            if a and a.get("kind") == "idea" and a.get("status") in ("OPEN", "QUEUED"): aid, kind = a["id"], "feature"
                        if not aid:
                            aid = NT.send("idea", f"Build this? {spec}", [("Build it", "BUILD"), ("Park", "PARK")], tier="fyi", default=None if never_parked else "parked",
                                          expires_h=None if never_parked else 24 * 7, dedupe_key="idea|" + mid + "|" + json.dumps({"spec": spec, "kind": kind}))
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
    have = requests.get(base, headers=h, params={"name": S("WA_OPEN_TEMPLATE") if _on() else S("WA_TEMPLATE_NAME")}, timeout=30).json().get("data", [])
    if have: return True
    body = {"name": S("WA_TEMPLATE_NAME"), "language": S("WA_TEMPLATE_LANG"), "category": "UTILITY",
            "components": [{"type": "BODY", "text": "Reality Engine update: {{1}} Your options: {{2}} Tap a button to reply.", "example": {"body_text": [["Video EP12 is held after the quality check.", "1) Fix and post  2) Skip"]]}},
                           {"type": "BUTTONS", "buttons": [{"type": "QUICK_REPLY", "text": "1"}, {"type": "QUICK_REPLY", "text": "2"}, {"type": "QUICK_REPLY", "text": "3"}]}]}
    if _on(): body = open_template()                             # v12 B-OWNER (item 150): the ONE template, "Open"
    r = requests.post(base, headers=h, json=body, timeout=30)
    if r.status_code >= 300:                                     # v10.2 (#10): Meta's reason is logged (code/subcode/message; never the token)
        try: er = r.json().get("error", {}); why = f"code {er.get('code')}/{er.get('error_subcode')}: {er.get('error_user_msg') or er.get('message')}"
        except Exception: why = r.text[:200]
        log(f"WhatsApp template REJECTED ({r.status_code}): {why}", "ERROR"); return False
    log(f"WhatsApp template submitted ({r.status_code})"); return True

def template_status():
    """v12 B-OWNER (PART 8): the Open template's status at Meta (APPROVED, PENDING, REJECTED), "" when it cannot be read; the stand-in answers APPROVED."""
    if FAKE: return "APPROVED"
    if not (env("WA_TOKEN") and env("WA_WABA_ID")): return ""
    try:
        import requests
        d = requests.get(f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_WABA_ID')}/message_templates", headers={"Authorization": f"Bearer {env('WA_TOKEN')}"},
                         params={"name": S("WA_OPEN_TEMPLATE")}, timeout=30).json().get("data", [])
        return str((d[0] if d else {}).get("status") or "")
    except Exception as e: log(f"WhatsApp template status not read: {scrub(e)[:120]}", "WARN"); return ""

def ensure_subscribed():
    """v10.2 (#11): Meta only delivers inbound messages after the app is subscribed to the WhatsApp Business Account (POST subscribed_apps)."""
    if not (env("WA_TOKEN") and env("WA_WABA_ID")) or FAKE: return False
    import requests
    base = f"https://graph.facebook.com/{S('WA_GRAPH_VERSION')}/{env('WA_WABA_ID')}/subscribed_apps"
    h = {"Authorization": f"Bearer {env('WA_TOKEN')}"}
    r = requests.post(base, headers=h, timeout=30)
    ok = r.status_code < 300 and bool((r.json() or {}).get("success", True))
    log(f"WhatsApp app subscription to the business account: {'OK' if ok else 'FAILED ' + r.text[:160]}", "INFO" if ok else "ERROR"); return ok
