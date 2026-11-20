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
