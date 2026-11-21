"""v12 B-OWNER (PART 6, step 7): the face of Mission Control, proven in fake mode by code - F1 a phone's width, F2 both themes at 4.5:1, F3 a finger's
tap, F4 any snapshot renders, F5 six tabs with the alarm first. No layout engine runs here: "no sideways scroll" is proven as rules of the stylesheet;
the real screen is the pack's C0b (the deployed page at 375 pixels, `scrollWidth <= clientWidth` on each tab, and his one tap)."""
import json, re, shutil, subprocess
import pytest
from whatifs import core, dash as DS, notify as NT, publish as PUB, builds as BD

PAGE = "mission_control/mission_control.html"
TABS = ("home", "learning", "plan", "money", "inputs", "controls")

def _page():
    return open(PAGE, encoding="utf-8").read()

def _style(html=None):
    return re.search(r"<style>(.*?)</style>", html or _page(), re.S).group(1)

# ---------------- F1 PHONE WIDTH
def _wide(css):
    """Every `width` or `min-width` above 320 px (rem and em at 16 px) outside an `@media (min-width` block."""
    for m in list(re.finditer(r"@media\s*\(\s*min-width", css))[::-1]:
        i = css.index("{", m.end()); d = 0
        for j in range(i, len(css)):
            d += {"{": 1, "}": -1}.get(css[j], 0)
            if d == 0:
                css = css[:m.start()] + css[j + 1:]; break
    px = {"px": 1, "rem": 16, "em": 16}
    return [m.group(0) for m in re.finditer(r"(?<![\w-])(?:min-)?width\s*:\s*([\d.]+)(px|rem|em)\b", css) if float(m.group(1)) * px[m.group(2)] > 320]

def test_f1_the_page_fits_a_phone():
    html = _page(); css = _style(html)
    assert _wide(css) == [], _wide(css)
    assert re.search(r"(?<![\w-])body\s*\{[^}]*overflow-wrap:\s*anywhere", css)
    assert re.search(r"(?<![\w.#-])img\s*\{[^}]*max-width:\s*100%", css)
    svgs = re.findall(r"<svg\b[^>]*>", html)
    assert len(svgs) >= 8 and all("viewBox" in s for s in svgs), [s for s in svgs if "viewBox" not in s]
    assert _wide(css.replace(".wrap {", ".wrap { min-width: 480px;", 1)) == ["min-width: 480px"]                  # planted
    assert _wide(css + "\n@media (min-width: 700px) { .wrap { min-width: 600px; } }") == []                         # a wider screen may be wider

# ---------------- F2 BOTH THEMES
def _lum(h):
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def _ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

TEXT_ON = (("chalk", "ink"), ("chalk", "panel"), ("chalk", "panel-2"),                       # body text, cards, buttons
           ("muted", "ink"), ("muted", "panel"), ("muted", "panel-2"),                       # section notes and tabs; card notes; .kind, .tag.low, a disabled button
           ("brass", "panel"), ("brass", "brass-soft"),                                      # a goal label, an option's key; .tag.med, .kind.pick, the demo badge
           ("vale", "panel"), ("vale", "vale-soft"),                                         # a done note, "Rising."; .tag.high, .kind.merge
           ("grimm", "panel"), ("grimm", "grimm-soft"), ("grimm", "ink"),                    # a bad button, "Slipping."; .tag.neg, .kind.held; the PIN's error
           ("on-brass", "brass"), ("on-vale", "vale"), ("ink", "chalk"))                     # the primary and good buttons; the toast

def _tokens(block):
    return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", block))

def _themes(css):
    light = _tokens(re.search(r":root\s*\{(.*?)\}", css, re.S).group(1))
    media = _tokens(re.search(r':root:not\(\[data-theme="light"\]\)\s*\{(.*?)\}', css, re.S).group(1))
    dark = _tokens(re.search(r':root\[data-theme="dark"\]\s*\{(.*?)\}', css, re.S).group(1))
    return light, media, dark

def _low(t):
    return [(a, b, round(_ratio(t[a], t[b]), 2)) for a, b in TEXT_ON if _ratio(t[a], t[b]) < 4.5]

def test_f2_both_themes_read_at_four_and_a_half():
    light, media, dark = _themes(_style())
    assert media == dark                                                                 # the system's dark and the tapped dark are one theme
    for t in (light, dark):
        assert {x for p in TEXT_ON for x in p} <= set(t)
        assert _low(t) == [], _low(t)
    grey = dict(light, muted="#767C91")                                                  # planted: a muted grey at 3.9 on the card's surface
    assert 3.8 < _ratio(grey["muted"], grey["panel"]) < 4.0 and ("muted", "panel", round(_ratio(grey["muted"], grey["panel"]), 2)) in _low(grey)

# ---------------- the snapshots the page must render
def _full(monkeypatch, setting):
    """A snapshot built from real rows with the switch on: a card, an alarm, an inform row of the money group, a pick, portraits and his input."""
    setting("TWO_SCREENS_ON", "TRUE")
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)
    NT.send("visual_idea", "Visual idea: <b>Speed ramps</b>", [("Discuss", "DISCUSS motion_ramps"), ("Switch on", "VISUAL motion_ramps"), ("Park", "PARK")],
            tier="week", default="parked", expires_h=168)
    BD.build_ready("41", "tweak")
    NT.send("pipeline_stop", "Production paused: a health check failed.", dedupe_key="pipeline_stop|face")
    NT.send("budget_pct", "Budget: 40% of the cap is used.")
    st = core.store(); slot = (core.now_utc() + __import__("datetime").timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st.append("Episodes", [{"episode_id": "EP20261120F", "yt_id": "v1", "slot_et": slot, "status": "SCHEDULED", "title": "Your Phone Weighs 400 Kilos"}])
    st.append("Packaging_Tests", [{"episode_id": "EP20261120F", "variant": k, "title": f"Title {k}", "thumb_text": "9 SECONDS", "status": "LIVE" if k == "A" else "READY"} for k in "ABC"])
    st.append("Character_Sheets", [{"ts": core.iso(), "character": "ROSA", "expression": "warm", "hash": "h9", "file": "drive:9", "status": "DRAFT"}])
    from whatifs.org import desk as DESK
    DESK.take("More wonder, less lecture please, in the first minute.", "dashboard", ref="face-1")
    s = DS.build_snapshot()
    assert s["alarms"] and s["docket"] and s["inputs"] and s["groups"]["money"]       # the snapshot is really full
    return json.loads(json.dumps(s))

def _empty(x):
    """The same snapshot with every list empty."""
    if isinstance(x, dict): return {k: _empty(v) for k, v in x.items()}
    if isinstance(x, list): return []
    return x

def _render(snap, tmp_path, name):
    if not shutil.which("node"): pytest.skip("node not installed")
    p = tmp_path / f"{name}.json"; p.write_text(json.dumps(snap), encoding="utf-8")
    out = subprocess.run(["node", "mission_control/render_check.mjs", PAGE, str(p), "--dump"], capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
    lines = out.strip().splitlines()
    assert lines and lines[0] == "ALL TABS RENDERED", out[-800:]
    dumped = json.loads(lines[-1])
    assert tuple(dumped) == TABS
    return dumped

# ---------------- F3 ONE TAP, AND A FINGER CAN HIT IT
TARGETS = (".btn", "nav.tabs button", ".toggle", ".thumb", ".icon-btn", ".say button")
VERBS = ("data-verb", "data-rule", "data-chosen", "data-say", "data-input", "data-pick", "data-mode", "data-pause", "data-toggle", "data-step", "data-undo")

def _min_height(css, sel):
    m = re.search(r"(?:^|\n)\s*" + re.escape(sel) + r"\s*\{([^}]*)\}", css)
    h = re.search(r"min-height:\s*(\d+)px", m.group(1)) if m else None
    return int(h.group(1)) if h else 0

def _verb_tags(html):
    """Every element that carries a verb, as (tag, its attributes)."""
    return [(t.lower(), a) for t, a in re.findall(r"<([A-Za-z]+)\b([^>]*)>", html) if any(v + "=" in a for v in VERBS)]

def _answers_per_card(html):
    return [len(re.findall(r"\b(?:data-verb|data-chosen|data-rule)=", part.split("</article>")[0])) for part in html.split("<article")[1:]]

def test_f3_one_tap_and_a_finger_can_hit_it(monkeypatch, setting, tmp_path):
    css = _style()
    for sel in TARGETS: assert _min_height(css, sel) >= 44, sel
    snap = _full(monkeypatch, setting)
    snap["docket"].append({"id": "four", "kind": "advisor", "title": "Four answers", "why": "A card with four answers.", "default_label": "Nothing happens",
                           "default_at": "", "window_h": 0, "verbs": {f"Answer {i}": f"ACT|four|{i}" for i in range(4)}})       # planted: more than three
    dumped = _render(snap, tmp_path, "full")
    for tab, html in dumped.items():
        tags = _verb_tags(html)
        assert all(t == "button" for t, _a in tags), (tab, [x for x in tags if x[0] != "button"])
        assert all(n <= 3 for n in _answers_per_card(html)), (tab, _answers_per_card(html))
    four = dumped["home"].split('id="case-four"')[1].split("</article>")[0]
    assert four.count("<option") == 4 and four.count("data-chosen=") == 1 and "data-verb=" not in four       # four answers = one list and one Send
    assert 'data-say="' in dumped["home"] and 'data-input="1"' in dumped["inputs"]                         # the box under a card, the box of his inputs
    assert re.search(r'<button class="btn primary wide" data-input="1">', dumped["inputs"])                # the input's Send is a .btn (44 px)

# ---------------- F4 IT RENDERS WHATEVER COMES
def test_f4_it_renders_whatever_comes(monkeypatch, setting, tmp_path):
    full = _full(monkeypatch, setting)
    _render(full, tmp_path, "full")
    _render(_empty(full), tmp_path, "empty")
    bad = "A" * 300 + "<script>alert(1)</script>"
    hostile = json.loads(json.dumps(full))
    hostile["inputs"][0]["text"] = bad; hostile["alarms"][0]["text"] = bad; hostile["alarms"][0]["title"] = bad
    dumped = _render(hostile, tmp_path, "hostile")
    assert all("<script" not in html.lower() for html in dumped.values())
    assert "A" * 300 in dumped["inputs"] and "&lt;script&gt;" in dumped["home"]                                # shown, as text

# ---------------- F5 SIX TABS, THE ALARM FIRST
def test_f5_six_tabs_and_the_alarm_comes_first(monkeypatch, setting, tmp_path):
    html = _page()
    assert tuple(re.findall(r'<button role="tab" data-tab="([a-z]+)"', html)) == TABS
    assert re.search(r"grid-template-columns:\s*repeat\(6, 1fr\)", _style(html))
    assert '["home", "learning", "plan", "money", "inputs", "controls"]' in open("mission_control/render_check.mjs", encoding="utf-8").read()
    full = _full(monkeypatch, setting)
    home = _render(full, tmp_path, "alarm")["home"]
    assert home.index("data-alarm=") < home.index(">Needs you<")                                              # an open alarm is the first thing
    quiet = dict(full, alarms=[])
    home = _render(quiet, tmp_path, "quiet")["home"]
    assert re.findall(r"<h2[^>]*>([^<]*)</h2>", home)[0] == "Needs you"                                    # else "Needs you"

def test_the_owner_runs_keep_githubs_default_queue():
    """R1-144 (a): no `queue: max` (groups using it stalled 139-194 minutes); a replaced run loses nothing - the Worker kept the input (CE-1b)."""
    import yaml
    for f, job in ((".github/workflows/dash.yml", "act"), (".github/workflows/whatsapp.yml", "inbound")):
        assert "queue" not in yaml.safe_load(open(f))["jobs"][job]["concurrency"], f

def _jobs():
    import yaml
    return {n: yaml.safe_load(open(f".github/workflows/{f}.yml"))["jobs"][j] for n, f, j in (("dash", "dash", "act"), ("wa", "whatsapp", "inbound"), ("inbox", "pipeline", "owner_inbox"))
            if j in yaml.safe_load(open(f".github/workflows/{f}.yml"))["jobs"]}

def test_the_tick_drains_the_kept_inputs_in_the_owner_group():
    """CH-4 (OE2-2): a kept input whose dispatch GitHub refused waited for his NEXT dash or WhatsApp run - no bound at all. The pipeline's
    `owner_inbox` job runs after every tick, whatever the tick's result, in the owner runs' own group (never beside a dash or WhatsApp run, so an id
    is never handled twice) and does the drain only. The bound is the next tick (GitHub's measured tick gaps: 80 to 661 minutes)."""
    job = _jobs().get("inbox"); assert job, "no owner_inbox job in pipeline.yml: a kept input whose dispatch was refused waits for his next tap"
    assert job["needs"] == "tick" and job["if"] == "always()" and job["concurrency"] == {"group": "owner-actions", "cancel-in-progress": False}
    assert [s["run"] for s in job["steps"] if "whatifs.cli" in str(s.get("run", ""))] == ["python -m whatifs.cli dash_drain"]
    assert job["permissions"] == {"contents": "read", "actions": "write"} and "GH_ACTIONS_TOKEN" in job["env"] and "GH_TOKEN" not in job["env"]

def test_every_run_that_drains_can_answer_his_whatsapp_words():
    """CH-5: every run that drains also handles a kept WhatsApp message (`inbox:wa:`) - and the chat answers it with ANTHROPIC_KEY, which dash.yml
    did not pass: his question, drained by a dashboard run, was answered "Something failed on my side". Each job that drains carries every key the
    WhatsApp run and the dashboard run carry (its own payload aside; GH_TOKEN is the tick job's GH_ACTIONS_TOKEN, the same token, in pipeline.yml)."""
    jobs = _jobs(); need = (set(jobs["dash"]["env"]) | set(jobs["wa"]["env"])) - {"DASH_PAYLOAD", "WA_PAYLOAD"}
    for n, job in jobs.items():
        have = set(job["env"]) | ({"GH_TOKEN"} if "GH_ACTIONS_TOKEN" in job["env"] else set())
        assert not need - have, f"{n} drains without {sorted(need - have)}"

def test_cli_dash_drain_does_the_drain_and_nothing_else(monkeypatch, capsys):
    """CH-4: `cli dash_drain` (the owner_inbox job's one command) calls `drain()` - and nothing else: no payload of its own, no snapshot printed."""
    import sys
    from whatifs import cli
    calls = []
    monkeypatch.setattr(DS, "drain", lambda kv=None: calls.append(("drain", kv)) or 3)
    for name in ("handle_action", "build_snapshot", "publish"): monkeypatch.setattr(DS, name, lambda *a, _n=name, **k: calls.append(_n))
    monkeypatch.setattr(sys, "argv", ["whatifs.cli", "dash_drain"]); cli.main()
    assert calls == [("drain", None)] and capsys.readouterr().out.strip().splitlines()[-1] == "3"

def test_each_ack_names_its_action_id_and_an_unhandled_one_is_absent(setting):
    """CR-6-1 (CE-1): the page matched acks by VERB and every input is INPUT - the first ack confirmed every pending input. Each ack now carries the
    Worker's id: of two inputs only the handled one is in `acks`, by its id."""
    from whatifs import dash as DS
    setting("TWO_SCREENS_ON", "TRUE")
    DS._ack("WID2", "INPUT", True, "Saved as input 2")                          # WID1 was sent too; its run never ran
    acks = DS.build_snapshot()["acks"]
    assert [a.get("id") for a in acks] == ["WID2"] and acks[0]["verb"] == "INPUT", acks

def test_a_kept_input_is_handled_once_by_the_next_run_and_its_key_deleted(monkeypatch, setting):
    """CE-1b (R1-144 (b)): the Worker keeps each input in KV before its dispatch; a run that never ran loses nothing - the next run's drain handles
    every kept id once (an acked id is skipped) and deletes its key."""
    import base64, json as _j, os
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from whatifs import dash as DS
    key = os.urandom(32); monkeypatch.setenv("WA_RELAY_KEY", base64.b64encode(key).decode()); setting("TWO_SCREENS_ON", "TRUE")
    def kept(item):
        n = os.urandom(12); return _j.dumps({"n": base64.b64encode(n).decode(), "c": base64.b64encode(AESGCM(key).encrypt(n, _j.dumps(item).encode(), None)).decode()})
    class KV:
        def __init__(s, d): s.d = d
        def keys(s, p): return [k for k in s.d if k.startswith(p)]
        def get(s, k): return s.d.get(k)
        def delete(s, k): s.d.pop(k, None)
    w1 = {"id": "W1", "verb": "INPUT", "text": "more wonder please", "card": "", "src": "dash"}
    kv = KV({"inbox:W1": kept(w1), "snapshot": "{}"})
    assert DS.drain(kv) == 1 and list(kv.d) == ["snapshot"]
    kv.d["inbox:BAD"] = "not readable with this key"                                 # a value this run cannot read is NOT deleted
    assert DS.drain(kv) == 0 and "inbox:BAD" in kv.d; kv.d.pop("inbox:BAD")
    kv.d["inbox:W1"] = kept(w1)                                                      # the same id kept again (a dispatch AND a drain): handled once
    assert DS.drain(kv) == 1 and [r["id"] for r in core.store().rows("Dash_Acks")] == ["W1"] and "inbox:W1" not in kv.d

def _inbox(monkeypatch):
    """CH-1: the Worker's KV inbox in fake - `kept(item)` encrypts as worker.js `keep` does; the fake KV lists its keys in the order they were put,
    as Cloudflare lists them by NAME - and the names are random ids, so the listing order is not the order he acted in."""
    import base64, json as _j, os
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = os.urandom(32); monkeypatch.setenv("WA_RELAY_KEY", base64.b64encode(key).decode())
    def kept(item):
        n = os.urandom(12); return _j.dumps({"n": base64.b64encode(n).decode(), "c": base64.b64encode(AESGCM(key).encrypt(n, _j.dumps(item).encode(), None)).decode()})
    class KV:
        def __init__(s, d): s.d = d
        def keys(s, p): return [k for k in s.d if k.startswith(p)]
        def get(s, k): return s.d.get(k)
        def delete(s, k): s.d.pop(k, None)
    return kept, KV

def test_kept_inputs_are_handled_in_the_order_he_gave_them(monkeypatch, setting):
    """CH-1 (FR-CE1b-1): the drain handles his kept inputs oldest first by the moment he gave them - a dash item's `ts` (milliseconds), a WhatsApp
    message's `ts` (Meta's timestamp, SECONDS) - never by the order KV lists their random names; his last word stands. A kept input whose handling
    raised stops the drain: the later ones stay and the next run does them all, in order."""
    kept, KV = _inbox(monkeypatch); setting("TWO_SCREENS_ON", "TRUE")
    resume, pause = {"id": "R1", "verb": "RESUME", "ts": 1_000_000, "src": "dash"}, {"id": "P1", "verb": "PAUSE", "ts": 2_000_000, "src": "dash"}
    kv = KV({"inbox:a-pause": kept(pause), "inbox:b-resume": kept(resume)})           # listed newest first
    assert DS.drain(kv) == 2 and kv.d == {}
    assert core.S("PAUSED", bool) is True, "his later Pause was overridden by his earlier Resume: the drain walked KV's listing order"
    tap = {"id": "wamid.R2", "ts": "2500", "type": "button", "payload": "RESUME", "text": "Resume"}     # 2,500 s = 2,500,000 ms: AFTER the Pause below
    kv = KV({"inbox:wa:wamid.R2": kept({"messages": [tap], "statuses": []}), "inbox:c-pause": kept({**pause, "id": "P2", "ts": 2_400_000})})
    assert DS.drain(kv) == 2 and kv.d == {}
    assert core.S("PAUSED", bool) is False, "his WhatsApp Resume (2,500 s) came after the dash Pause (2,400,000 ms): seconds and milliseconds were compared raw"
    real, calls = DS.handle_action, []
    def once_down(val):                                                               # the Sheet fails on the first kept input of this run
        calls.append(val)
        if len(calls) == 1: raise TimeoutError("the sheet did not answer")
        return real(val)
    monkeypatch.setattr(DS, "handle_action", once_down)
    kv = KV({"inbox:d-pause": kept({**pause, "id": "P3", "ts": 4_000_000}), "inbox:e-resume": kept({**resume, "id": "R3", "ts": 3_000_000})})
    assert DS.drain(kv) == 0 and set(kv.d) == {"inbox:d-pause", "inbox:e-resume"}, "a later input was handled while an earlier one failed"
    assert DS.drain(kv) == 2 and kv.d == {} and core.S("PAUSED", bool) is True                  # the next run: Resume, then Pause - his last word
    assert [r["id"] for r in core.store().rows("Dash_Acks")] == ["R1", "P1", "P2", "R3", "P3"]                    # each id once, oldest first

def test_a_run_does_the_kept_inputs_before_its_own_payload(monkeypatch, setting, capsys, tmp_path):
    """CH-1 (FR-CE1b-1): three taps while one run works - A runs, B waits, C replaces B (GitHub keeps ONE pending run of a group). C's run must do B
    before C: with B = Resume and C = Pause the engine ends PAUSED. C's own payload is kept too, so the drain does it in its place and the payload
    call finds its ack: each id is acked once and the run prints "ok". The same for a WhatsApp run and a kept dash input it finds waiting."""
    import sys
    from whatifs import cli
    monkeypatch.chdir(tmp_path)                                                                   # R1-291 (6): the crash handler writes last_error.txt into the current folder - NEVER the repo's (test_v12_floor.py 606)
    kept, KV = _inbox(monkeypatch); setting("TWO_SCREENS_ON", "TRUE")
    b, c = {"id": "B1", "verb": "RESUME", "ts": 1_000_000, "src": "dash"}, {"id": "C1", "verb": "PAUSE", "ts": 2_000_000, "src": "dash"}
    kv = KV({"inbox:B1": kept(b), "inbox:C1": kept(c)})
    monkeypatch.setattr(DS, "_kv", lambda: kv); monkeypatch.setenv("DASH_PAYLOAD", kept(c)); monkeypatch.setattr(sys, "argv", ["whatifs.cli", "dash_action"])
    cli.main()
    assert core.S("PAUSED", bool) is True, "the run did its own Pause first and the drain then did the earlier Resume: his last word was overridden"
    assert [r["id"] for r in core.store().rows("Dash_Acks")] == ["B1", "C1"] and kv.d == {} and capsys.readouterr().out.strip().endswith("ok")
    msg = {"id": "wamid.P9", "ts": "3000", "type": "button", "payload": "PAUSE", "text": "Pause"}          # 3,000 s: after the kept Resume below
    kv.d.update({"inbox:wa:wamid.P9": kept({"messages": [msg], "statuses": []}), "inbox:B2": kept({**b, "id": "B2", "ts": 2_500_000})})
    monkeypatch.setenv("WA_PAYLOAD", kept({"messages": [msg], "statuses": []})); monkeypatch.setattr(sys, "argv", ["whatifs.cli", "wa_inbound"])
    cli.main()
    assert core.S("PAUSED", bool) is True and kv.d == {}, "the WhatsApp run did its own Pause before the kept Resume it found waiting"
    class Down(KV):                                                                   # KV does not answer: the run still does his own tap
        def keys(s, p): raise ConnectionError("cloudflare did not answer")
    down = Down({"inbox:C3": kept({**b, "id": "C3", "ts": 4_000_000})})
    monkeypatch.setattr(DS, "_kv", lambda: down); monkeypatch.setenv("DASH_PAYLOAD", kept({**b, "id": "C3", "ts": 4_000_000})); monkeypatch.setattr(sys, "argv", ["whatifs.cli", "dash_action"])
    cli.main()
    assert core.S("PAUSED", bool) is False and "C3" in [r["id"] for r in core.store().rows("Dash_Acks")] and "inbox:C3" in down.d, "a KV that did not answer stopped his own tap"

def test_the_snapshot_says_when_the_health_reading_failed(monkeypatch, setting):
    """CE-2 (CR-7-2): an error or a timeout while the runs are read is said in the snapshot (`read`, `note`) - never an empty list that looks healthy."""
    from whatifs import caretaker as CT
    one = [{"workflow": "tick", "ok": True, "at": core.iso()}]
    def boom(): raise TimeoutError("the sheet did not answer")
    monkeypatch.setattr(CT, "last_runs", lambda: list(one)); h = DS.build_snapshot()["health"]
    assert (h["read"], h["note"], h["expiry_read"], h["last_runs"]) == ("ok", "", True, one)
    monkeypatch.setattr(CT, "last_runs", lambda: []); h = DS.build_snapshot()["health"]
    assert h["read"] == "none" and "not a green light" in h["note"]
    monkeypatch.setattr(CT, "last_runs", boom); setting("TWO_SCREENS_ON", "TRUE"); h = DS.build_snapshot()["health"]      # through `_scrubbed` too
    assert h["read"] == "failed" and h["last_runs"] == [] and "could not be read" in h["note"] and "not a green light" in h["note"]
    monkeypatch.setattr(CT, "last_runs", lambda: list(one)); monkeypatch.setattr(CT, "expiring", boom); h = DS.build_snapshot()["health"]
    assert h["read"] == "ok" and h["expiry_read"] is False and h["expiring"] == []

GREEN = ("every recent run is fine", 'tag high">OK<', "Every run fine", 'class="light "')

def test_a_failed_health_read_is_never_the_green_light(monkeypatch, setting, tmp_path):
    """CE-2 (CR-7-2): Home and Controls say that the reading failed, found nothing or is old - no green light, no "OK", no "every recent run is fine";
    a run known to have failed stays red; a fresh reading with every run fine IS green (the control that shows these words can appear)."""
    import copy, datetime as _dt
    base = _full(monkeypatch, setting); base["generated_at"] = core.iso()
    run = lambda ok: {"workflow": "tick", "ok": ok, "at": core.iso()}
    def page(name, health, **over):
        s = copy.deepcopy(base); s.update(over)
        if health is None: s.pop("health", None)
        else: s["health"] = health
        d = _render(s, tmp_path, name); return d["home"], d["controls"]
    home, ctl = page("fine", {"expiring": [], "last_runs": [run(True)], "read": "ok", "note": "", "expiry_read": True})
    assert all(g in home for g in GREEN) and "Not read" not in home + ctl
    failed = {"expiring": [], "last_runs": [], "read": "failed", "note": DS.HEALTH_NOTE["failed"], "expiry_read": False}
    cases = {"failed": (failed, {}, "the reading failed"),
             "todays_shape": ({"expiring": [], "last_runs": []}, {}, "no run has been read yet"),          # what `_health` returns today when the read raises
             "no_health": (None, {}, "the reading failed"),
             "old": ({"expiring": [], "last_runs": [run(True)], "read": "ok", "note": ""},
                     {"generated_at": (core.now_utc() - _dt.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")}, "too old to call fine")}
    for name, (health, over, words) in cases.items():
        home, ctl = page(name, health, **over)
        assert not [g for g in GREEN if g in home], (name, [g for g in GREEN if g in home])
        assert words in home and 'class="light off"' in home and "Not read" in home and words in ctl, name
    assert "could not be read this time" in page("failed2", failed)[1]                                   # Controls carries the snapshot's own words
    home, ctl = page("bad", {"expiring": [], "last_runs": [run(True), run(False)], "read": "failed", "note": DS.HEALTH_NOTE["failed"]})
    assert 'class="light bad"' in home and "a run failed" in home and not [g for g in GREEN if g in home]

# ---------------- FINISHED BY FABLE: the corrections of the finishing pass (step 7 with step 6's snapshot)
def test_a_card_never_reads_nan_or_a_deadline_it_does_not_have(monkeypatch, setting, tmp_path):
    """PART 6 (Home: "the countdown and the default"; "Decided for you"). FOUND AT THE FINISH: a card without a deadline read "in NaN m", and a row
    his silence had already decided read "If you don't rule: ran by default: ... in now". A card says what is true of it."""
    import datetime as dt
    _full(monkeypatch, setting)
    hold = NT.send("api_audit", "Send the YouTube API audit form.", dedupe_key="api_audit|face2")           # a hold has no deadline
    card = NT.send("bakeoff", "Pick the clip model", [("Pick A", "PICK A")], default="A is used", expires_h=1)
    NT.expire_defaults(core.now_utc() + dt.timedelta(hours=2))                                              # this one ran by default
    post = NT.send("decided_post", "EP3 was approved by your silence and goes public at Sat 20:30.", [("Take it down", "UNPOST EP3")], expires_h=168)
    home = _render(json.loads(json.dumps(DS.build_snapshot())), tmp_path, "fuse")["home"]
    part = lambda i: home.split(f'id="case-{i}"')[1].split("</article>")[0]
    assert "NaN" not in home, [x[:200] for x in home.split("<article") if "NaN" in x]
    assert "No deadline: it waits for your tap." in part(hold) and "If you don" not in part(hold)
    assert "ran by default: A is used" in part(card) and "If you don" not in part(card)
    assert "If you don" not in part(post) and "Take it down" in part(post)
    assert "If you don" in home                                                                            # a card with a deadline keeps its countdown (`_full`'s visual idea)

def test_an_open_row_of_his_inputs_can_be_tapped(monkeypatch, setting, tmp_path):
    """PART 5 with PART 6 (item 149: every step of his reaches both screens). FOUND AT THE FINISH: a group's rows carried no buttons, so "Build it" and
    "Take it back" could be tapped on WhatsApp only. A row of a group carries its taps in the docket's own shape and the page shows them as buttons."""
    _full(monkeypatch, setting)
    idea = NT.send("idea", "Build this? a slower first second", [("Build it", "BUILD"), ("Not now", "PARK")])
    taken = NT.send("desk", "Your input 1: TAKEN - kept word for word as your standing preference.", [("Take it back", "DESK UNDO 1")], tier="week",
                    dedupe_key="desk|taken|1")      # a TAKEN input's row as desk.weigh_row sends it (desk.py:317); `_full`'s input stays unweighed (STRATEGY_ON off) - R1-209
    snap = json.loads(json.dumps(DS.build_snapshot()))
    row = next(x for x in snap["groups"]["inputs"] if x["id"] == idea)
    assert row["verbs"] == {"Build it": f"ACT|{idea}|0", "Not now": f"ACT|{idea}|1"}, row
    assert next(x for x in snap["groups"]["inputs"] if x["id"] == taken)["verbs"] == {"Take it back": f"ACT|{taken}|0"}, snap["groups"]["inputs"]
    part = _render(snap, tmp_path, "tap")["inputs"].split(f'id="case-{idea}"')[1].split("</article>")[0]
    assert part.count("<button") == 2 and f'data-verb="ACT|{idea}|0"' in part and f'data-verb="ACT|{idea}|1"' in part, part
    ok, _note = DS.route(f"ACT|{idea}|1")                                                                   # the tap is one `dash.route` already answers
    assert ok and all(x["id"] != idea for x in DS.build_snapshot()["groups"]["inputs"])

def test_an_address_in_a_row_is_one_tap_on_the_page(monkeypatch, setting, tmp_path):
    """F3 (every action one tap) with PART 7's own row ("Watch it (private): https://studio..."). FOUND AT THE FINISH: the page printed an address as
    text. A card carries the https addresses of its row as `links`; the page's own link buttons draw them, named by where they lead; nothing but
    https is ever drawn."""
    _full(monkeypatch, setting)
    post = NT.send("decided_post", "EP3 was approved by your silence and goes public at Sat 20:30. Watch it (private): https://studio.youtube.com/video/abc123/edit",
                   [("Take it down", "UNPOST EP3")], expires_h=168)
    hold = NT.send("api_audit", "Send the YouTube API audit form: https://support.google.com/youtube/contact/yt_api_form.", dedupe_key="api_audit|face")
    snap = json.loads(json.dumps(DS.build_snapshot()))
    dec = next(c for c in snap["decided"] if c["id"] == post); card = next(c for c in snap["docket"] if c["id"] == hold)
    assert dec["links"] == ["https://studio.youtube.com/video/abc123/edit"], dec
    assert card["links"] == ["https://support.google.com/youtube/contact/yt_api_form"], card                 # the sentence's full stop is not the address
    home = _render(snap, tmp_path, "links")["home"]
    assert '<a class="btn ghost" href="https://studio.youtube.com/video/abc123/edit" target="_blank" rel="noopener">Open Studio</a>' in home
    assert 'href="https://support.google.com/youtube/contact/yt_api_form" target="_blank" rel="noopener">Open the page</a>' in home
    for c in snap["decided"] + snap["docket"]: c["links"] = ["javascript:alert(1)", 'https://x.test/"onmouseover="y']       # planted: a hostile snapshot
    home = _render(snap, tmp_path, "badlinks")["home"]
    assert "javascript:" not in home and 'onmouseover="y' not in home
