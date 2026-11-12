"""Reality on Trial as code: the Show Plan contract with its validator, the character bible, the script-tag contract and the IP-similarity guard. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, store, iso

# ---------------------------------------------------------------- the cast (core only; cameos later). Speakers map onto the existing two-voice pipeline.
CHARACTERS = [
    {"id": "VALE", "name": "Inspector Vale", "speaker": "DIRECTOR", "role": "defence",
     "philosophy": "Evidence first; the universe is strange but never unfair.", "rhythm": "short calm sentences, then one long deductive run",
     "tics": "taps the exhibit twice before a deduction; says 'Observe.' before a reveal", "vocabulary": "observe; consider the evidence; the record shows",
     "recurring_bit": "lists three facts on his fingers, the third one turns the case", "when_wrong": "pauses, says 'Noted. The evidence wins.' and corrects himself plainly",
     "relationships": "former lab partner of Dr. Grimm; respects Nana Rosa's bluntness", "visual": "grey overcoat, silver-rimmed glasses, a worn evidence notebook",
     "voice_style": "low, warm, measured, clear consonants, never rushed", "sound": "soft paper rustle + pen click", "audio_chain": "highpass=f=70,equalizer=f=180:t=q:w=1:g=2,acompressor=threshold=-18dB:ratio=2.5"},
    {"id": "GRIMM", "name": "Dr. Grimm", "speaker": "SKEPTIC", "role": "prosecution",
     "philosophy": "Every impossible claim is guilty until proven otherwise.", "rhythm": "theatrical crescendos, sudden whispers, a sharp stop",
     "tics": "rolls the r in 'impossible'; claps once when he thinks he has won", "vocabulary": "objection; preposterous; the jury will note; ha",
     "recurring_bit": "his mask slips once an episode: a moment of real wonder he quickly hides", "when_wrong": "theatrical groan, then a grudging 'Fine. FINE. Note it.'",
     "relationships": "former lab partner of Inspector Vale; terrified of Nana Rosa", "visual": "black high-collar coat, red pocket square, sharp widow's peak",
     "voice_style": "rich, dramatic, villain-theatrical but never cruel, crisp diction", "sound": "single sharp clap + low cello sting", "audio_chain": "equalizer=f=120:t=q:w=1:g=3,aecho=0.8:0.6:20:0.12,acompressor=threshold=-16dB:ratio=3"},
    {"id": "ROSA", "name": "Nana Rosa", "speaker": "JUDGE", "role": "judge",
     "philosophy": "Talk less, prove more, and drink your tea before it gets cold.", "rhythm": "very short lines, long pauses, one dry punchline",
     "tics": "sips tea loudly before every ruling; says 'Mm.'", "vocabulary": "sit down; order; mm; the tea is getting cold",
     "recurring_bit": "deflates both lawyers with one sentence", "when_wrong": "'Then I was wrong. Pass the sugar.'",
     "relationships": "has known both since they were students; hides her teacup in the evidence", "visual": "silver hair bun, judge's robe over a cardigan, a floral teacup",
     "voice_style": "older, warm, slow, dry humour, clear", "sound": "teacup clink + gavel tap", "audio_chain": "highpass=f=90,lowpass=f=9000,acompressor=threshold=-20dB:ratio=2", "gvoice": "Gacrux"},
    {"id": "ARCHIVIST", "name": "The Archivist", "speaker": "WITNESS", "role": "surprise witness",
     "philosophy": "Everything that happened left a record.", "rhythm": "slow, whispered, archival", "tics": "reads dates aloud",
     "vocabulary": "the archive remembers; entry; filed", "recurring_bit": "appears only for the surprise witness", "when_wrong": "'The archive is corrected.'",
     "relationships": "known to all three, trusted by none", "visual": "never fully seen: a silhouette behind shelves", "voice_style": "whispered, close, calm",
     "sound": "page turn + distant reel-to-reel", "audio_chain": "highpass=f=150,lowpass=f=7000,aecho=0.7:0.5:40:0.2", "gvoice": "Enceladus"},
]
BIBLE_FIELDS = ("philosophy", "rhythm", "tics", "vocabulary", "recurring_bit", "when_wrong", "relationships", "visual", "voice_style", "sound", "audio_chain")

# Allowed ffmpeg audio filters for a character chain (deterministic, no randomness, no file access)
AUDIO_FILTERS = {"highpass", "lowpass", "equalizer", "acompressor", "aecho", "chorus", "atempo", "volume", "bass", "treble", "aphaser", "vibrato", "tremolo",
                 "deesser", "alimiter", "asetrate", "aresample"}

def audio_chain_ok(chain):
    """True when every filter is on the allow-list and every argument is a plain number / unit / keyword (no file paths, no expressions)."""
    if not str(chain or "").strip(): return False
    for part in str(chain).split(","):
        name, _, args = part.strip().partition("=")
        if name not in AUDIO_FILTERS: return False
        if args and not re.fullmatch(r"[A-Za-z0-9_.:=\-]+", args): return False
    return True

# IP-similarity / real-person guard (names and bible text). A hit = a validator issue; the plan or bible line is not used as written.
PROTECTED_NAMES = ["sherlock", "holmes", "watson", "moriarty", "poirot", "columbo", "marple", "lestrade", "joker", "batman", "darth", "vader", "gandalf",
                   "dumbledore", "snape", "voldemort", "hannibal", "lecter", "heisenberg", "walter white", "rick sanchez", "doc brown", "hermione", "yoda",
                   "spock", "the doctor", "doctor who", "dexter", "house m.d", "gregory house", "judge judy", "matlock", "perry mason", "phoenix wright",
                   "einstein", "feynman", "neil degrasse", "tyson", "bill nye", "attenborough", "sagan", "hawking", "musk", "mrbeast", "vsauce", "kurzgesagt"]

def ip_hits(text):
    t = " " + re.sub(r"[^a-z0-9. ]+", " ", str(text or "").lower()) + " "
    return sorted({n for n in PROTECTED_NAMES if re.search(r"(?<![a-z])" + re.escape(n) + r"(?![a-z])", t)})

def character_rows():
    """Rows for the Characters tab (the character bible; Setup seeds it once, the owner edits it)."""
    return [dict({k: c.get(k, "") for k in ("id", "name", "speaker", "role", "gvoice", "gstyle", "cast_id")}, **{k: c.get(k, "") for k in BIBLE_FIELDS}, status="core", updated=iso())
            for c in CHARACTERS]

def seed_designed_voices(st=None):
    """v9.2, once: the owner's Gemini Voice Design voices (AI Studio names) go into Characters.gvoice where the cell is empty or still holds the v9 default
    prebuilt voice. A voice the owner typed himself is never overwritten."""
    from whatifs.core import set_setting
    st = st or store()
    if S("DESIGNED_VOICES_SEEDED"): return 0
    from whatifs.voiceq import DESIGNED
    n = 0; old = {"ROSA": "Gacrux", "ARCHIVIST": "Enceladus", "VALE": "", "GRIMM": ""}
    for r in st.rows("Characters"):
        cid = r.get("id")
        if cid in DESIGNED and str(r.get("gvoice") or "").strip() in ("", old.get(cid, "")):
            st.update("Characters", "id", cid, {"gvoice": DESIGNED[cid]}); n += 1
    set_setting("DESIGNED_VOICES_SEEDED", iso())
    return n

def seed_characters(st=None):
    """Idempotent: adds only missing core characters. Returns the number added."""
    st = st or store()
    try: have = {r.get("id") for r in st.rows("Characters")}
    except Exception: have = set()
    rows = [r for r in character_rows() if r["id"] not in have]
    if rows: st.append("Characters", rows)
    try: seed_designed_voices(st)                                  # v9.2 (once)
    except Exception as e: log(f"designed voices not seeded: {str(e)[:120]}", "WARN")
    return len(rows)

def bible_issues(rows):
    """Code checks on the character bible: IP / real-person similarity, audio chain allow-list, no child characters."""
    out = []
    for r in rows:
        txt = " ".join(str(r.get(k, "")) for k in ("name",) + BIBLE_FIELDS if k != "audio_chain")
        for h in ip_hits(txt): out.append(f"{r.get('id')}: resembles a protected name or real person ('{h}')")
        if r.get("audio_chain") and not audio_chain_ok(r["audio_chain"]): out.append(f"{r.get('id')}: audio chain not on the allow-list")
        if re.search(r"\b(child|kid|toddler|little (boy|girl)|schoolboy|schoolgirl)\b", txt, re.I): out.append(f"{r.get('id')}: child characters are not allowed")
    return out

# ---------------------------------------------------------------- Show Plan contract
EXHIBIT_KINDS = ("REAL_AGENCY", "RECON", "DATA")
HUD_TYPES = {"survival": {"Survival odds", "Oxygen", "Body temperature", "Heart rate", "Water left", "Radiation dose"},
             "scale": {"Distance", "Height", "Speed", "Size", "Mass", "Energy", "Temperature", "Pressure", "Depth", "Population"},
             "clock": {"Time elapsed", "Time left", "Day", "Year"},
             "price": {"Price", "Cost", "Value"}}
WITNESS_TWISTS = ["a forgotten historical record", "a measurement nobody checked", "an animal that already does this", "a satellite that saw it",
                  "a lab accident that proved it", "a number that is off by a factor of a thousand", "the defendant's own fine print",
                  "a second effect everyone ignored", "an expert who changed sides", "the planet itself as witness", "a time-lapse that reverses the story",
                  "a tiny scale model that fails"]
JURY_KINDS = ("prediction", "guilty", "abc")
PLAN_KEYS = ("charge", "defendant", "intensity", "exhibits", "witness_twist", "jury_prompts", "meter_swings", "verdict", "clipbait_id", "hud_spec",
             "teacup_scenes", "stinger", "demand_evidence")
WPS = 2.5                                                    # spoken words per second (planning estimate; the timeline decides in QC)

def leads_on():
    """Is the show's world switched on at all (SHOW_MODE = auto)? The two leads keep their designed voices in every format."""
    return str(S("SHOW_MODE") or "off").strip().lower() == "auto"

def on():
    """Does the TRIAL layer run for the episode in the making? SHOW_MODE = auto, and the episode's format is a trial (or no format is set: v12 V2a)."""
    from whatifs import formats as FMT
    return leads_on() and FMT.show_allowed()

def _words(t): return len(re.findall(r"\S+", str(t or "")))

def history(n=12):
    """Recent Show_Log rows (newest last)."""
    try: return store().rows("Show_Log")[-n:]
    except Exception: return []

VERDICT_STYLES = ["clear ruling", "split decision", "hung jury: Nana orders a retrial", "appeal granted on new evidence", "plea deal: the defendant admits half",
                  "case dismissed on a technicality", "Nana recuses herself and the jury decides", "surprise witness changes the verdict"]

def recent_styles(k=3, hist=None):
    hist = hist if hist is not None else history(k)
    out = []
    for r in hist[-k:]:
        try: out.append(str((json.loads(r.get("plan_json") or "{}").get("verdict") or {}).get("style") or ""))
        except Exception: pass
    return [x for x in out if x]

def next_style(hist=None, seed=""):
    """v10.1 (K144): the verdict STYLE rotates (never one of the last VERDICT_STYLE_GAP styles), so no two cases end the same way (YouTube's
    'characters in the same situation with the same outcome' example of repetitive content)."""
    import hashlib
    used = set(recent_styles(S("VERDICT_STYLE_GAP", int), hist))
    free = [s for s in VERDICT_STYLES if s not in used] or VERDICT_STYLES
    return free[int(hashlib.md5(str(seed or len(used)).encode()).hexdigest()[:6], 16) % len(free)]

TRIAL_GRAMMAR = (
    "\nTRIAL GRAMMAR (mandatory; code checks every point and holds the episode if one is missing):"
    " (1) COLD OPEN: show the consequence first, with stakes and a withheld fact; no greeting."
    " (2) TIME LADDER: examine the case at HOUR 1, DAY 1, YEAR 1 and A MILLION YEARS, saying those words; the timescale is where Grimm is wrong."
    " (3) EXHIBITS: every scientific claim treated as true is entered by THE ARCHIVIST as 'Exhibit A', 'Exhibit B'... naming a real source and"
    " its year on the same line (e.g. 'Exhibit B: NOAA tide records, 2023'); Grimm's exaggerations are testimony and get corrected on screen."
    " (4) Around minute 3, DR. GRIMM demonstrates 'Prototype No.' plus the case number; it fails comically (smoke, sparks) but reveals one true thing."
    " (5) Around minute 6, INSPECTOR VALE finds the contradiction on his evidence board: the twist."
    " (6) Link beats with BUT or THEREFORE, never 'and then'."
    " (7) NANA ROSA opens the verdict with the exact words \"Here's what's true\"."
    " (8) STAGING: every scene says who is on screen and with which prop (lab, office, courtroom, or the case scene); no lone talking head.")

def villain_due(hist=None):
    """The villain wins about 1 in 3: True when his share of the recent verdicts is below a third (he may win, only on a real detail)."""
    hist = hist if hist is not None else history(9)
    w = [str(r.get("verdict_winner", "")) for r in hist if r.get("verdict_winner")]
    return not w or sum(1 for x in w if x == "grimm") / len(w) < 1 / 3

def recent_twists(k=5, hist=None):
    hist = hist if hist is not None else history(k)
    return [str(r.get("witness_twist", "")) for r in hist[-k:] if r.get("witness_twist")]

def recent_prompts(k=6, hist=None):
    hist = hist if hist is not None else history(k)
    out = []
    for r in hist[-k:]:
        try: out += [p.get("text", "") for p in json.loads(r.get("plan_json") or "{}").get("jury_prompts", [])]
        except Exception: pass
    return out

def prompt_block(hist=None):
    """Text added to the Showrunner brief (before 'Return JSON') when SHOW_MODE = auto. The same call returns the plan: no new AI role."""
    hist = hist if hist is not None else history()
    lo, hi = _irange()
    allowed = [t for t in WITNESS_TWISTS if t not in recent_twists(5, hist)]
    return ("SHOW FORMAT 'REALITY ON TRIAL' (" + str(S("SHOW_FORMAT") or "trial") + "): the impossible scenario is the DEFENDANT. Inspector Vale (the expert) defends it with evidence; "
            "Dr. Grimm (theatrical villain skeptic, never cruel, no gore) prosecutes; Nana Rosa judges; the viewers are the Jury. The science question is fully "
            "resolved in this video and Vale stays accurate. No child characters, no real people, no existing characters.\n"
            f"Add a key \"show_plan\" to your JSON: {{\"charge\":\"<=20 words\",\"defendant\":\"\",\"intensity\":{lo}-{hi},"
            "\"exhibits\":[{\"id\":\"A\",\"kind\":\"REAL_AGENCY|RECON|DATA\",\"what\":\"\",\"source\":\"agency or dataset (REAL_AGENCY/DATA)\",\"objection\":\"Grimm's objection, <=25 words\"}],"
            f"\"witness_twist\":\"one of {json.dumps(allowed)}\",\"jury_prompts\":[{{\"kind\":\"prediction|guilty|abc\",\"text\":\"in character, <=25 words\"}}] (3-5),"
            "\"meter_swings\":[{\"after\":\"exhibit id, witness or verdict\",\"side\":\"grimm|vale\",\"n\":1-3}],"
            "\"verdict\":{\"winner\":\"vale|grimm|split\",\"detail\":\"the exact point that decides it\"},\"clipbait_id\":\"exhibit id or witness\","
            "\"hud_spec\":[{\"t\":seconds,\"type\":\"survival|scale|clock|price\",\"label\":\"\",\"value\":number,\"unit\":\"\"}] or \"none\","
            "\"teacup_scenes\":[\"2-4 RECON exhibit ids\"],\"stinger\":\"<=25 words: the next case\",\"demand_evidence\":{}}\n"
            + ("Dr. Grimm MAY win this one, but only on a detail he is genuinely right about. " if villain_due(hist) else "Dr. Grimm should not win this one. ")
            + "The meter swings must add up to the verdict."
            + ((f" VERDICT STYLE for this case (different from recent cases; put it in verdict.style): {next_style(hist)}.") if S("VERDICT_ROTATION_ON", bool) else "")
            + (TRIAL_GRAMMAR if S("TRIAL_GRAMMAR_ON", bool) else "")
            + __import__("whatifs.owner_brief", fromlist=["x"]).brief_block())

def _irange():
    lo = max(0, min(3, S("CHARACTER_INTENSITY_MIN", int))); hi = max(lo, min(3, S("CHARACTER_INTENSITY_MAX", int)))
    return lo, hi

def meter_total(swings):
    return sum((1 if s.get("side") == "vale" else -1) * int(s.get("n", 0) or 0) for s in swings or [])

def _winner_of(total):
    return "vale" if total > 0 else "grimm" if total < 0 else "split"

def validate(plan, spine=None, hist=None):
    """(clean plan, issues). Deterministic repair; never calls a model. A plan that cannot be repaired becomes the code fallback (issues say so)."""
    issues = []; spine = spine or {}; hist = hist if hist is not None else history()
    if not isinstance(plan, dict):
        return fallback(spine, hist), ["no show_plan returned - code fallback used"]
    p = {k: plan.get(k) for k in PLAN_KEYS}
    p["defendant"] = str(p.get("defendant") or spine.get("premise") or "")[:200]
    ch = str(p.get("charge") or "").strip()
    if not ch: ch = "The defendant stands accused of being impossible: " + p["defendant"]; issues.append("charge missing - written from the premise")
    if _words(ch) > 20: ch = " ".join(ch.split()[:20]); issues.append("charge longer than 8 s - cut to 20 words")
    p["charge"] = ch
    lo, hi = _irange()
    try: it = int(float(p.get("intensity")))
    except Exception: it = lo + (hi - lo) // 2; issues.append("intensity missing - middle of the range used")
    if not lo <= it <= hi: issues.append(f"intensity {it} outside {lo}-{hi} - clamped"); it = max(lo, min(hi, it))
    p["intensity"] = it
    ex = []
    for i, e in enumerate([e for e in (p.get("exhibits") or []) if isinstance(e, dict)][:8]):
        kind = str(e.get("kind") or "").upper()
        if kind not in EXHIBIT_KINDS: issues.append(f"exhibit {i + 1}: unknown kind '{kind}' - RECON used"); kind = "RECON"
        src = str(e.get("source") or "").strip()
        if kind in ("REAL_AGENCY", "DATA") and not src: issues.append(f"exhibit {i + 1}: {kind} without a source - relabelled RECON"); kind = "RECON"
        obj = str(e.get("objection") or "").strip()
        if _words(obj) > 25: obj = " ".join(obj.split()[:25]); issues.append(f"exhibit {i + 1}: objection longer than 10 s - cut")
        ex.append({"id": chr(65 + i), "kind": kind, "what": str(e.get("what") or "")[:200], "source": src[:160], "credit": src[:160], "objection": obj})
    if not ex: ex = [{"id": "A", "kind": "RECON", "what": p["defendant"][:200], "source": "", "credit": "", "objection": ""}]; issues.append("no exhibits - one reconstruction exhibit added")
    p["exhibits"] = ex; ids = {e["id"] for e in ex}
    tw = str(p.get("witness_twist") or "")
    rec = recent_twists(5, hist)
    if tw not in WITNESS_TWISTS or tw in rec:
        new = next((t for t in WITNESS_TWISTS if t not in rec), WITNESS_TWISTS[0])
        issues.append(f"witness twist '{tw[:40]}' not on the menu or used in the last 5 episodes - '{new}' used"); tw = new
    p["witness_twist"] = tw
    jp = []; seen = {re.sub(r"\W+", " ", x.lower()).strip() for x in recent_prompts(6, hist)}
    for q in [q for q in (p.get("jury_prompts") or []) if isinstance(q, dict)]:
        k = str(q.get("kind") or "").lower(); txt = " ".join(str(q.get("text") or "").split()[:25])
        if k not in JURY_KINDS or not txt: continue
        if re.sub(r"\W+", " ", txt.lower()).strip() in seen: issues.append("a jury prompt repeats a recent one - dropped"); continue
        seen.add(re.sub(r"\W+", " ", txt.lower()).strip()); jp.append({"kind": k, "text": txt})
    for k, t in (("guilty", "Jury: guilty or not guilty? Write your verdict before Nana Rosa rules."), ("prediction", "Predict it now: what happens in the first hour?"),
                 ("abc", "A, B or C: which exhibit convinced you?")):
        if len(jp) >= 3: break
        jp.append({"kind": k, "text": t}); issues.append("fewer than 3 jury prompts - a default prompt added")
    p["jury_prompts"] = jp[:5]
    sw = []
    for s in [s for s in (p.get("meter_swings") or []) if isinstance(s, dict)]:
        side = str(s.get("side") or "").lower()
        try: n = max(1, min(3, int(float(s.get("n")))))
        except Exception: continue
        if side in ("grimm", "vale"): sw.append({"after": str(s.get("after") or "")[:20], "side": side, "n": n})
    vd = p.get("verdict") if isinstance(p.get("verdict"), dict) else {}
    win = str(vd.get("winner") or "").lower(); detail = str(vd.get("detail") or "")[:300]
    if win not in ("vale", "grimm", "split"): win = "vale"; issues.append("verdict missing - Vale")
    if win == "grimm" and not detail: win = "vale"; issues.append("Grimm may only win on a stated detail - verdict set to Vale")
    if win == "grimm" and not villain_due(hist): issues.append("Grimm already won his share recently - kept, noted")
    if _winner_of(meter_total(sw)) != win:                    # the Jury Meter decides: one closing swing makes it agree
        need = {"vale": 1, "grimm": -1, "split": 0}[win] - meter_total(sw)
        if need: sw.append({"after": "verdict", "side": "vale" if need > 0 else "grimm", "n": min(3, abs(need))})
        if _winner_of(meter_total(sw)) != win:
            sw = [s for s in sw if s["after"] != "verdict"]; win = _winner_of(meter_total(sw))
        issues.append("meter swings did not add up to the verdict - repaired")
    style = str(vd.get("style") or "")[:80]
    if S("VERDICT_ROTATION_ON", bool):
        if not style: style = next_style(hist, detail)                         # missing: filled quietly
        elif style in recent_styles(S("VERDICT_STYLE_GAP", int), hist):
            style = next_style(hist, detail); issues.append("verdict style repeated - rotated")
    p["meter_swings"] = sw; p["verdict"] = {"winner": win, "detail": detail, "style": style}
    cb = str(p.get("clipbait_id") or "")
    if cb not in ids and cb != "witness": cb = ex[0]["id"]; issues.append("clip-bait moment not an exhibit or the witness - the first exhibit used")
    p["clipbait_id"] = cb
    hud, hi_ = hud_check(p.get("hud_spec")); p["hud_spec"] = hud; issues += hi_
    recon = [e["id"] for e in ex if e["kind"] == "RECON"]
    tc = [t for t in (p.get("teacup_scenes") or []) if t in recon][:4]
    if len(tc) < 2 and len(recon) >= 2: tc = recon[:min(4, max(2, len(tc)))]; issues.append("teacup scenes set to reconstruction exhibits")
    p["teacup_scenes"] = tc
    st = str(p.get("stinger") or "")
    if _words(st) > 25: st = " ".join(st.split()[:25]); issues.append("stinger cut to 25 words")
    p["stinger"] = st or "Next case: " + str((spine.get("next_tease") or {}).get("headline") or "the archive is never empty.")
    p["demand_evidence"] = p.get("demand_evidence") if isinstance(p.get("demand_evidence"), dict) else {}
    for k in ("charge", "defendant", "stinger"):
        for h in ip_hits(p[k]): issues.append(f"{k} names a protected character or real person ('{h}')")
    return p, issues

def hud_check(spec):
    """HUD spec = list of {t, type, label, value, unit} or 'none'. Labels from the allowed set per type, numeric values, times ascending,
    clocks monotonic, survival odds 0-100 %. Bad entries are dropped with an issue (the HUD is optional; it never blocks)."""
    if spec in (None, "", "none") or spec == []: return "none", []
    if not isinstance(spec, list): return "none", ["hud_spec not a list - no HUD"]
    out, iss, last_t = [], [], -1.0
    for i, h in enumerate(spec[:24]):
        if not isinstance(h, dict): iss.append(f"hud {i + 1}: not an object - dropped"); continue
        typ = str(h.get("type") or "").lower(); lab = str(h.get("label") or "")
        try: t = float(h.get("t")); v = float(h.get("value"))
        except Exception: iss.append(f"hud {i + 1}: time or value not a number - dropped"); continue
        if typ not in HUD_TYPES or lab not in HUD_TYPES[typ]: iss.append(f"hud {i + 1}: label '{lab}' not allowed for '{typ}' - dropped"); continue
        if t < last_t: iss.append(f"hud {i + 1}: time goes backwards - dropped"); continue
        if lab == "Survival odds" and not 0 <= v <= 100: iss.append(f"hud {i + 1}: survival odds outside 0-100 - dropped"); continue
        prev = [x for x in out if x["label"] == lab]
        if typ == "clock" and prev and len(prev) >= 2 and (v - prev[-1]["value"]) * (prev[-1]["value"] - prev[-2]["value"]) < 0:
            iss.append(f"hud {i + 1}: '{lab}' is not monotonic - dropped"); continue
        out.append({"t": t, "type": typ, "label": lab, "value": v, "unit": str(h.get("unit") or "")[:12]}); last_t = t
    return (out or "none"), iss

def fallback(spine, hist=None):
    """A complete, valid plan from the spine alone (no model call). Used when the Showrunner returned none."""
    p, _ = validate({"charge": "", "exhibits": [], "verdict": {"winner": "vale", "detail": ""}, "jury_prompts": []}, spine, hist)
    p["fallback"] = True
    return p

def log_plan(episode, plan, issues):
    """One Show_Log row per plan (also the history the next validation reads). Never raises."""
    try:
        store().append("Show_Log", [{"ts": iso(), "episode_id": episode or "", "format": str(S("SHOW_FORMAT") or "trial"), "intensity": plan.get("intensity"),
                                     "witness_twist": plan.get("witness_twist", ""), "verdict_winner": (plan.get("verdict") or {}).get("winner", ""),
                                     "meter_final": meter_total(plan.get("meter_swings")), "fallback": bool(plan.get("fallback")),
                                     "issues": "; ".join(issues)[:900], "plan_json": json.dumps(plan, ensure_ascii=False)[:20000]}])
    except Exception as e:
        log(f"Show_Log not written: {str(e)[:120]}", "WARN", episode)

def apply_to_spine(spine, episode):
    """Room hook: validate + repair the plan the Showrunner returned, store it on the spine, log it. Shadow in stage 1 (nothing downstream reads it yet)."""
    if not on(): return spine
    hist = history()
    plan, iss = validate(spine.get("show_plan"), spine, hist)
    from whatifs import community as CM
    var = CM.variety_issues(plan, hist)                          # v9 variety guard: no extra call; the writer is told what to avoid (the ONE forced change)
    if var: plan["variety_notes"] = var; iss = iss + ["variety: " + v for v in var]
    spine["show_plan"] = plan
    if iss: log(f"show plan repaired by code: {len(iss)} fix(es)", "WARN", episode)
    log_plan(episode, plan, iss)
    return spine

def characters():
    """The bible rows (Characters tab; the built-in core cast if the tab is empty)."""
    try: rows = [r for r in store().rows("Characters") if r.get("id")]
    except Exception: rows = []
    return rows or character_rows()

KOKORO_FALLBACK = {"JUDGE": ({"bf_emma": 0.8, "af_sarah": 0.2}, "b"), "WITNESS": ({"bm_lewis": 0.85, "bm_george": 0.15}, "b")}

def extra_blends(taken):
    """v9: voices for the JUDGE and the WITNESS. Gemini voice from the Characters tab only when it is a confirmed prebuilt / Voice_Check voice that the two
    leads do not use (an unknown name would otherwise fail the whole narration); the Kokoro recipe is the fallback. Returns {speaker: Blend}."""
    from whatifs.voice import Blend
    from whatifs.tts_gemini import is_prebuilt
    out = {}
    for c in characters():
        sp = c.get("speaker")
        if sp not in KOKORO_FALLBACK: continue
        gv = str(c.get("gvoice") or "").strip()
        from whatifs import v91 as V91
        v_ = ""
        if V91.on("DESIGNED_VOICES_ON") and gv:                                # v9.2: designed voice by ID / AI Studio name, then the closest prebuilt
            with V91.guard("DESIGNED_VOICES_ON"):                              # fail-safe: a failure falls back to the v9.1 rule below
                from whatifs.voiceq import voice_for
                v_, how_ = voice_for(sp, gv, taken)
        if v_:
                taken = set(taken) | {v_}; parts, lang = KOKORO_FALLBACK[sp]
                out[sp] = Blend(sp.lower(), parts, lang=lang, gvoice=v_, gstyle=str(c.get("gstyle") or "")); continue
        from whatifs import v91 as V91
        if V91.on("VOICE_SUBSTITUTE_ON") and V91.available_voices():          # v9.1: Voice_Check decides; closest voice by descriptors before Kokoro
            gv0 = gv; gv = ""
            with V91.guard("VOICE_SUBSTITUTE_ON"):
                gv, how = V91.resolve_voice(sp, gv0, taken)
            if gv: taken = set(taken) | {gv}
        elif gv and (not is_prebuilt(gv) or gv in taken):
            log(f"{c.get('name')}: Gemini voice '{gv}' not confirmed or already used by a lead - Kokoro fallback voice for this character", "WARN"); gv = ""
        parts, lang = KOKORO_FALLBACK[sp]
        out[sp] = Blend(sp.lower(), parts, lang=lang, gvoice=gv, gstyle=str(c.get("gstyle") or c.get("voice_style") or ""))
    return out

COLD_OPEN_YOU = ("COLD OPEN (v9.3; the first ~20 s, about 50 spoken words, BEFORE any lore): second person, present tense - YOU are inside the impossible "
                 "situation right now. Line 1 is a physical stake with a clock, a number or a sensation (e.g. 'Your phone weighs four hundred kilos. You have nine "
                 "seconds.'), then what YOU see, hear and feel, escalating line by line. Spoken by [DIRECTOR] as the calm voice in your ear: no greeting, no name, "
                 "no 'welcome'. NO character names and NO courtroom words (court, trial, the charge, jury, exhibit, objection, verdict, defendant) before Nana Rosa "
                 "reads the charge. The cold open ends on the open question the trial will answer; the charge then frames that question as the case. Danger is "
                 "implied through stakes, sound and scale, never shown as injury or gore.\n")

def writer_brief(plan):
    """The writer's trial brief: the plan, the cast (labels, voices on the page, tics), the structure and the tag rules. Wording rules only; no new role."""
    cast = "; ".join(f"[{c.get('speaker')}] = {c.get('name')} ({c.get('role')}): {c.get('philosophy')} Rhythm: {c.get('rhythm')}. Tics: {c.get('tics')}. "
                     f"Words: {c.get('vocabulary')}. Recurring bit: {c.get('recurring_bit')}. When wrong: {c.get('when_wrong')}." for c in characters())
    return ("REALITY ON TRIAL - write this episode as a trial (the impossible scenario is the defendant). CAST: " + cast + "\n"
            + (COLD_OPEN_YOU if S("COLD_OPEN_YOU_ON", bool) else "") +
            "STRUCTURE: cold-open reconstruction (found footage, the viewer inside the scene) -> THE CHARGE (Nana Rosa reads it, <= 8 s) -> one beat per EXHIBIT "
            "in plan order, each with Dr. Grimm's objection (<= 10 s) -> the SURPRISE WITNESS ([WITNESS], the plan's twist) -> JURY prompts -> the VERDICT "
            "(Nana Rosa rules; the meter decides) -> a short stinger (the next case). The science question is fully answered; Vale stays accurate; Grimm is "
            "theatrical, never cruel, no gore; his mask slips once (a moment of real wonder). No child characters, no real people, no existing characters.\n"
            "TAGS (never spoken, put them at the START of the line they belong to): [EXHIBIT A] when an exhibit is shown; [METER +n vale] / [METER +n grimm] "
            "(n 1-3) after a point lands, adding up to the plan's verdict; [JURY] on 3-5 in-character questions to the viewers (none in the first 30 s); "
            "[CLIPBAIT] ... [/CLIPBAIT] around ONE quotable, self-contained moment of at most 8 s on the plan's clip-bait exhibit.\n"
            + last_case_text() + "SHOW PLAN (follow it): " + json.dumps(plan, ensure_ascii=False)[:5000])

def last_case_text():
    """v9: the previous case's jury tally and teacup finders for the cold open (handles were filtered by code; counts only, no comment text)."""
    try: rows = [r for r in store().rows("Season") if r.get("jury_tally")]
    except Exception: rows = []
    if not rows: return ""
    r = rows[-1]
    return (f"LAST CASE: the jury voted {r.get('jury_tally')}; verdict was {r.get('verdict')}. Nana Rosa may mention the vote in ONE line after the charge"
            + (f"; she thanks the teacup finders by handle: {r.get('teacup_finders')}" if r.get("teacup_finders") else "") + ".\n")

# ---------------------------------------------------------------- script-tag contract (validated now; consumed by voice / render / QC in stage 2)
TAG_RE = re.compile(r"\[(CLIPBAIT|/CLIPBAIT|METER [+-]?\d+ (?:grimm|vale)|EXHIBIT [A-H]|JURY)\]", re.I)
SHOW_TAG_RE = re.compile(r"\[(?:/?CLIPBAIT|METER[^\]]*|EXHIBIT[^\]]*|JURY|TEACUP|PUNCH|SEND|AWE)\]", re.I)        # v11.1: + markers

def strip_tags(text):
    """Show tags are never spoken: removed before TTS, captions and descriptions."""
    return re.sub(r"[ \t]{2,}", " ", SHOW_TAG_RE.sub("", str(text or ""))).strip()

def check_tags(script, plan):
    """Issues with the show tags in a script against its plan: exactly one CLIPBAIT segment of <= 8 s (word estimate), METER tags well-formed with
    n 1-3 and a final reading that agrees with the verdict, EXHIBIT ids from the plan, 3-5 JURY prompts and none in the first 30 s (word estimate)."""
    s = str(script or ""); iss = []
    for m in re.finditer(r"\[(METER|EXHIBIT)[^\]]*\]", s, re.I):
        if not TAG_RE.fullmatch(m.group(0)): iss.append(f"malformed tag {m.group(0)}")
    opens = [m.start() for m in re.finditer(r"\[CLIPBAIT\]", s, re.I)]; closes = [m.start() for m in re.finditer(r"\[/CLIPBAIT\]", s, re.I)]
    if len(opens) != 1 or len(closes) != 1 or closes[0] < opens[0]: iss.append(f"need exactly one [CLIPBAIT]...[/CLIPBAIT] segment (found {len(opens)} / {len(closes)})")
    elif _words(strip_tags(re.sub(r"\[[^\]]*\]", " ", s[opens[0]:closes[0]]))) > 8 * WPS: iss.append("clip-bait segment longer than 8 s")
    tot = 0
    for m in re.finditer(r"\[METER ([+-]?\d+) (grimm|vale)\]", s, re.I):
        n = int(m.group(1))
        if not 1 <= abs(n) <= 3: iss.append(f"meter step {n} outside 1-3")
        tot += abs(n) * (1 if m.group(2).lower() == "vale" else -1)
    want = (plan.get("verdict") or {}).get("winner")
    if want and _winner_of(tot) != want: iss.append(f"the meter ends on {_winner_of(tot)} but the verdict is {want}")
    ids = {e["id"] for e in plan.get("exhibits", [])}
    for m in re.finditer(r"\[EXHIBIT ([A-H])\]", s, re.I):
        if m.group(1).upper() not in ids: iss.append(f"[EXHIBIT {m.group(1)}] is not in the show plan")
    jury = [m.start() for m in re.finditer(r"\[JURY\]", s, re.I)]
    if not 3 <= len(jury) <= 5: iss.append(f"{len(jury)} jury prompts (need 3-5)")
    if jury and _words(strip_tags(re.sub(r"\[[^\]]*\]", " ", s[:jury[0]]))) < 30 * WPS: iss.append("a jury prompt comes in the first 30 s")
    return iss
