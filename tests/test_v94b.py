"""v9.4b: Mission Control data feed and taps (K130). No keys, no network."""
import base64, datetime as dt, json, os, re
import pytest
from whatifs import core, dash as DS, notify as NT, publish as PUB, preview as PV, builds as BD

WORKER_VERB = re.compile(r"^[A-Z]{2,12}(\|[A-Za-z0-9_.:+\-]{0,80}){0,3}$")      # the Worker's rule (mission_control/worker.js)
KEY = base64.b64encode(bytes(range(32))).decode()

def _enc(obj, key=KEY):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    n = os.urandom(12); c = AESGCM(base64.b64decode(key)).encrypt(n, json.dumps(obj).encode(), None)
    return {"c": base64.b64encode(c).decode(), "n": base64.b64encode(n).decode()}

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _seed(monkeypatch):
    _quiet(monkeypatch); st = core.store()
    a = NT.send("visual_idea", "Visual idea: <b>Speed ramps</b>", [("Discuss", "DISCUSS motion_ramps"), ("Switch on", "VISUAL motion_ramps"), ("Park", "PARK")], tier="week", default="parked", expires_h=168)
    b = BD.build_ready("41", "tweak")
    slot = (core.now_utc() + dt.timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st.append("Episodes", [{"episode_id": "EP20261110", "yt_id": "v1", "slot_et": slot, "status": "SCHEDULED", "title": "Your Phone Weighs 400 Kilos"}])
    st.append("Packaging_Tests", [{"episode_id": "EP20261110", "variant": k, "title": f"Title {k}", "thumb_text": "9 SECONDS", "status": "LIVE" if k == "A" else "READY"} for k in "ABC"])
    st.append("Character_Sheets", [{"ts": core.iso(), "character": "ROSA", "expression": "warm", "hash": "h9", "file": "drive:9", "status": "DRAFT"}])
    return a, b

def test_snapshot_has_the_page_shape_and_only_worker_safe_verbs(monkeypatch):
    a, b = _seed(monkeypatch)
    s = DS.build_snapshot()
    for k in ("generated_at", "engine", "docket", "progress", "learned", "lab", "money", "health", "settings", "acks", "whatsapp"): assert k in s, k
    kinds = {c["kind"] for c in s["docket"]}; assert {"visual_idea", "merge", "pick", "sheets"} <= kinds
    for c in s["docket"]:
        for v in c["verbs"].values():
            assert WORKER_VERB.match(v.replace("{key}", "B")), v
    assert next(c for c in s["docket"] if c["kind"] == "merge")["verbs"] == {"Merge now": "MERGE|41", "Reject": "REJECT|41"}
    assert s["engine"]["next_release"]["title"].startswith("Your Phone") and s["money"]["cap"] == 5000
    assert "room_json" not in json.dumps(s) and "ANTHROPIC" not in json.dumps(s)                       # nothing private (K32)

def test_every_field_the_page_reads_exists():
    html = open("mission_control/mission_control.html", encoding="utf-8").read()
    s = DS.build_snapshot()
    for top, sub in set(re.findall(r"\bS\.([a-z_]+)(?:\.([a-z_]+))?", html)):
        assert top in s, top
        if sub and isinstance(s[top], dict) and sub not in ("find", "filter", "map", "length"): assert sub in s[top], f"S.{top}.{sub}"

def test_encrypted_tap_is_routed_once_and_acked(monkeypatch, setting):
    a, b = _seed(monkeypatch); monkeypatch.setenv("WA_RELAY_KEY", KEY)
    payload = _enc({"id": "t1", "verb": f"ACT|{a}|1", "ts": 1, "src": "dash"})
    assert DS.handle_action(json.dumps(payload)) and core.S("MOTION_BOOST_ON", bool)                  # button 1 = "Switch on"
    assert DS.handle_action(json.dumps(payload))                                                         # duplicate: handled once
    acks = core.store().rows("Dash_Acks"); assert len(acks) == 1 and acks[0]["ok"] == "TRUE"
    assert DS.build_snapshot()["acks"][0]["verb"] == f"ACT|{a}|1"
    assert not DS.handle_action(json.dumps({"c": "AAAA", "n": "AAAA"}))                                  # garbage never raises

def test_routes(monkeypatch, setting):
    a, b = _seed(monkeypatch); seen = []
    monkeypatch.setattr(PV, "decide", lambda t: seen.append(t) or "ok")
    assert DS.route("PICK|EP20261110|B") == (True, "ok") and seen[-1] == "PICK EP20261110 B"
    assert DS.route("MODE|lean")[0] and seen[-1] == "MODE RUNWAY"
    assert DS.route("MODE|growth")[0] is False
    assert DS.route("PAUSE") == (True, "paused") and core.S("PAUSED", bool); DS.route("RESUME"); assert not core.S("PAUSED", bool)
    assert DS.route("SET|visual_lab|false")[0] and not core.S("VISUAL_LAB_ON", bool)
    assert DS.route("SET|shorts_per_day|3") == (False, "that switch arrives with a later release")
    assert DS.route("SET|BUDGET_CEILING_INR|99999")[0] is False                                          # not on the allow-list
    assert DS.route("LOCKSHEETS|ROSA") == (True, "1 portrait(s) locked")
    monkeypatch.setattr(BD, "merge_pr", lambda n, why="": (True, f"merged #{n}"))
    assert DS.route("MERGE|41") == (True, "merged #41") and not any(r["kind"] == "build_ready" for r in NT.open_rows())
    calls = []; monkeypatch.setattr(BD, "request_build", lambda spec, kind="tweak": calls.append(kind) or True)
    assert DS.route(f"BUILD|{a}") == (True, "build started") and calls == ["feature"]
    assert DS.route("DROP|TABLE") == (False, "That action is not allowed.")

def test_publish_is_a_quiet_noop_until_cloudflare_exists(monkeypatch, setting):
    assert DS.publish() is False
    monkeypatch.setattr(DS, "FAKE", False)
    for k, v in (("CF_ACCOUNT_ID", "acc"), ("CF_KV_NAMESPACE_ID", "ns"), ("CF_KV_TOKEN", "tok")): monkeypatch.setenv(k, v)
    sent = []
    import requests
    class R: status_code = 200
    monkeypatch.setattr(requests, "put", lambda url, headers=None, data=None, timeout=0: sent.append((url, data)) or R())
    assert DS.publish()
    urls = [u for u, _ in sent]
    assert urls[0].endswith("/values/app_html") and urls[1].endswith("/storage/kv/namespaces/ns/values/snapshot") and "docket" in json.loads(sent[1][1])
    sent.clear(); assert DS.publish() and [u.rsplit("/", 1)[1] for u, _ in sent] == ["snapshot"]      # the page goes up only when it changed
    setting("DASH_ON", "FALSE"); assert DS.publish() is False

def test_dashboard_workflow():
    import yaml
    wf = yaml.safe_load(open(".github/workflows/dash.yml")); job = wf["jobs"]["act"]
    assert wf[True]["repository_dispatch"]["types"] == ["dash_action"] and job["concurrency"]["group"] == "owner-actions"
    assert "DASH_PAYLOAD" in job["env"] and any("cryptography" in str(s.get("run", "")) for s in job["steps"])

def test_every_dashboard_tab_renders_with_a_real_snapshot(monkeypatch, tmp_path):
    import shutil, subprocess
    if not shutil.which("node"): pytest.skip("node not installed")
    _seed(monkeypatch)
    p = tmp_path / "snap.json"; p.write_text(json.dumps(DS.build_snapshot()))
    out = subprocess.run(["node", "mission_control/render_check.mjs", "mission_control/mission_control.html", str(p)], capture_output=True, text=True, timeout=60).stdout
    assert "ALL TABS RENDERED" in out, out[-600:]

# ---------------- WhatsApp control room (K131)
from whatifs import wa as WA, models as M

def _wa_env(monkeypatch):
    for k, v in (("WA_TOKEN", "t"), ("WA_PHONE_ID", "p"), ("OWNER_WA", "919800000000"), ("WA_RELAY_KEY", KEY)): monkeypatch.setenv(k, v)
    sent = []; monkeypatch.setattr(WA, "_post", lambda body: sent.append(body) or f"wamid.{len(sent)}"); return sent

def test_outbound_uses_buttons_inside_the_window_and_the_template_outside(monkeypatch, setting):
    _quiet(monkeypatch); sent = _wa_env(monkeypatch)
    aid = NT.send("hold", "Video EP7 is held", [("Fix & post", "FIX EP7"), ("Skip", "SKIP EP7")], episode="EP7", tier="now", default="stays held", expires_h=72)
    body = sent[-1]; assert body["type"] == "template"                                       # nobody wrote in the last 24 h
    pays = [c["parameters"][0]["payload"] for c in body["template"]["components"] if c["type"] == "button"]
    assert pays == [f"ACT|{aid}|0", f"ACT|{aid}|1"] and WORKER_VERB.match(pays[0])
    setting("WA_LAST_INBOUND_AT", core.iso())
    NT.send("hold", "Video EP8 is held", [("Fix & post", "FIX EP8")], episode="EP8", tier="now", urgent=True)
    assert sent[-1]["type"] == "interactive" and sent[-1]["interactive"]["action"]["buttons"][0]["reply"]["id"].startswith("ACT|")
    assert len(core.store().rows("WA_Outbox")) == 2

def test_not_configured_means_email_only(monkeypatch):
    _quiet(monkeypatch); calls = []; monkeypatch.setattr(WA, "_post", lambda body: calls.append(body) or "x")
    NT.send("hold", "Held", episode="EP9", tier="now"); assert not calls

def test_inbound_button_status_dedupe_and_delivery(monkeypatch, setting):
    _seed(monkeypatch); sent = _wa_env(monkeypatch)
    a = next(r for r in core.store().rows("Owner_Actions") if r["kind"] == "visual_idea")["id"]
    core.store().append("WA_Outbox", [{"ts": core.iso(), "wamid": "wamid.X", "action_id": a, "kind": "visual_idea", "status": "sent"}])
    p = _enc({"messages": [{"id": "m1", "type": "interactive", "payload": f"ACT|{a}|1", "text": "Switch on"}], "statuses": [{"id": "wamid.X", "status": "delivered"}]})
    assert WA.handle_inbound(json.dumps(p)) == 1 and core.S("MOTION_BOOST_ON", bool)
    assert sent[-1]["text"]["body"].startswith("Done:") and core.store().rows("WA_Outbox")[0]["status"] == "delivered"
    assert WA.handle_inbound(json.dumps(p)) == 0                                              # same message id: handled once
    assert WA.in_window()

def test_status_and_pause_commands(monkeypatch, setting):
    _seed(monkeypatch); sent = _wa_env(monkeypatch)
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m2", "type": "text", "text": "status"}]})))
    assert "Spend Rs" in sent[-1]["text"]["body"] and "Waiting for you" in sent[-1]["text"]["body"]
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m3", "type": "text", "text": "pause"}]}))); assert core.S("PAUSED", bool)

def test_chat_offers_a_build_and_the_tap_builds_it(monkeypatch, setting):
    _quiet(monkeypatch); sent = _wa_env(monkeypatch); roles = []
    def fake_ask(role, system, prompt, **k):
        roles.append(role); return "Good idea: a visible 90-second clock.\nSPEC: show a countdown clock in survival cold opens, switch COLD_OPEN_CLOCK_ON\nKIND: tweak"
    monkeypatch.setattr(M, "ask", fake_ask)
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m4", "type": "text", "text": "add a countdown clock to cold opens"}]})))
    assert roles == ["owner_chat"] and sent[-1]["type"] == "interactive"
    btn = sent[-1]["interactive"]["action"]["buttons"][0]["reply"]["id"]; assert btn.startswith("ACT|")
    import whatifs.builds as BD; calls = []
    monkeypatch.setattr(BD, "request_build", lambda spec, kind="tweak": calls.append((kind, spec)) or True)
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m5", "type": "interactive", "payload": btn, "text": "Build it"}]})))
    assert calls == [("tweak", "show a countdown clock in survival cold opens, switch COLD_OPEN_CLOCK_ON")]
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m6", "type": "text", "text": "think hard: should we stop the courtroom?"}]})))
    assert roles[-1] == "owner_chat_deep"

def test_chat_cap_switches_to_the_cheap_model(monkeypatch, setting):
    _quiet(monkeypatch); _wa_env(monkeypatch); roles = []
    monkeypatch.setattr(M, "ask", lambda role, s, p, **k: roles.append(role) or "ok")
    core.store().append("Cost_Log", [{"ts": core.iso(), "role": "owner_chat", "item": "claude", "inr": "260", "basis": "measured"}])
    WA.handle_inbound(json.dumps(_enc({"messages": [{"id": "m7", "type": "text", "text": "hello"}]})))
    assert roles == ["owner_chat_cheap"]

def test_whatsapp_workflow():
    import yaml
    wf = yaml.safe_load(open(".github/workflows/whatsapp.yml")); job = wf["jobs"]["inbound"]
    assert wf[True]["repository_dispatch"]["types"] == ["wa_inbound"] and job["concurrency"]["group"] == "owner-actions" and "WA_PAYLOAD" in job["env"]
