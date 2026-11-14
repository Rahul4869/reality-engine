"""Presentation-format controls (Settings cell PRESENTATION_FORMAT) and the code check of the script's format. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import os, re

FORMAT_ID = "reality_engine"
FORMAT_NAME = "The Impossible Incident / Reality Engine"

REALITY_ENGINE = """
PRESENTATION FORMAT — THE IMPOSSIBLE INCIDENT / REALITY ENGINE
Core promise: each episode is a cinematic simulation of one impossible hypothetical, not a generic podcast and not fake real-world news.
Recurring original roles:
- [DIRECTOR] = the simulation director, an expert explaining to someone bright and curious: calm, concrete, warm, sets the rules and summarizes evidence. Sometimes asks for patience ('hold on, watch this part') before a payoff, using the delivery tag [patient].
- [SKEPTIC] = THE CURIOUS ONE (the label stays [SKEPTIC]): young, excitable, honest. Asks the question the audience is actually thinking, doubts out loud, pushes consequences further, and reacts the way a real person would AT THAT EXACT MOMENT of the picture. Not equally curious about everything: some things bore or worry them, some blow their mind. Never synthetic enthusiasm.
These are fictional presenter roles, not real named experts. Never claim either is a real scientist or expert. The Curious One is a young adult, never a child.
Voice rule for this format: the 'one sharp, warm person talking to a friend' voice applies to EACH role separately. The Director talks like a calm expert friend; the Curious One like a bright, honest friend. The two of them are the whole show: no third voice, no announcer.
Audience asks: exactly three short, witty, in-story moments (a like, a subscribe, a share), each spoken by one of the two roles in its own voice, placed after a payoff (never at a peak or a death), never begging, never a menu.
Reaction rules:
- Delivery tags for the Curious One's reactions: [wow] [gasp] [awe] [laugh] [doubt]. 4 to 6 reaction lines per video, spaced out, never on every beat. Each reaction line is SHORT and sounds spoken: 'Whoa!', 'Wait... wait. No way.', 'Oh no.', 'Okay, that is wicked.' Spell sounds so a voice engine can say them (Whoa, Wow, Ohhh); no long stretched vowels. The pop-up word on screen is the first word of the line, so open with the reaction word.
- Put a reaction line RIGHT AFTER each peak (the Kling moments and the biggest reveal). The Director places the big shot on the line before it. At least once, the Director first asks for patience, then the payoff lands, then the Curious One reacts.
- A reaction must match what a real viewer feels at that point (awe at scale, dread at a bad turn, a laugh at a harmless absurdity). If nothing surprising happened, the Curious One stays quiet or just asks a question.
- Original reactions only: never quote a film, show, meme or real person's catchphrase.
Dialogue requirements:
- Write natural back-and-forth. Each spoken dialogue line MUST begin with [DIRECTOR] or [SKEPTIC], then an optional delivery tag such as [calm], [tension], [reveal], [aside], or [callback]. Example: [SKEPTIC] [tension] Wait. That assumes the atmosphere stays put.
- Alternate speakers when useful, not mechanically. Each character must add reasoning, a counterpoint, or a new question; no empty 'wow', repetitive agreement, or fake disagreement.
- The opening hook may be an unlabelled narrator line. No greetings or long setup.
Story engine: establish the scenario's rules; begin the simulation; show consequences in escalating stages; challenge a key assumption; reveal an unintuitive consequence; distinguish likely outcomes from speculative branches; end with a clear verdict and honest uncertainty.
Visual grammar:
- The studio/control room is a recurring home base, not the whole video. Target approximately 20–30% presenter/control-room visuals, 50–60% scenario visualizations, and the remainder maps, timelines, diagrams, evidence, transitions, and payoff shots. Treat these as planning guidance, not quotas that override the story.
- Build a distinct original visual language: restrained simulation timestamps, simple state indicators, a recurring world-map/timeline motif, consistent palette and camera language, and clean cinematic framing. No fake YouTube UI, no copied franchise look, no real logos, no cluttered HUD.
- Visualize consequences whenever the narration introduces a meaningful physical change. Use wide establishing shots, close-up evidence, scale comparisons, and cause/effect transitions. Avoid endless talking-head coverage and generic stock-like AI imagery.
- Make the scenario itself the thumbnail's main promise; recurring characters are supporting brand anchors, not the only focal point.
- A PRESENTER IS DRAWN OR ABSENT. Never ask for a picture of a presenter: no face (image models cannot keep one face identical across shots), no dark shape, no back of a head standing in for one. A character appears only as its approved character art, which the renderer itself places; every picture you plan shows the SCENARIO, from inside it. The video marks who is speaking with a code-drawn speaker tag.
Scientific integrity: establish assumptions; separate established physics from inference and speculation; do not invent measurements or citations; do not portray fictional events as real breaking news. If a conclusion depends on assumptions, say so.
Shorts: extract a self-contained mini-investigation or a surprising claim-and-verdict, not merely a random excerpt. The Short must make sense without the full episode and may then invite viewers to watch the full simulation.
""".strip()

CLASSIC = "Presentation format: classic What If narration. Preserve all existing storytelling, science, visual, packaging, and Shorts rules."

def mode() -> str:
    value = os.getenv("WHATIFS_PRESENTATION_FORMAT", "").strip()
    if not value:
        try:
            from whatifs.core import S
            value = S("PRESENTATION_FORMAT") or FORMAT_ID
        except Exception: value = FORMAT_ID
    return "classic" if value.strip().lower() in {"classic", "legacy", "off", "0", "false"} else FORMAT_ID

def inject(prompt: str, role: str = "general") -> str:
    """Put the format block BEFORE the prompt's 'Return JSON' line so the reply format stays the last thing the model reads."""
    block = instructions(role)
    i = prompt.rfind("\nReturn JSON")
    return prompt + "\n\n" + block if i < 0 else prompt[:i] + "\n\n" + block + "\n" + prompt[i:]

def _units(script):
    from whatifs.voice import parse_script
    return parse_script(re.sub(r"^##.*$", "", script or "", flags=re.M))

def label_count(script) -> int:
    return sum(1 for u in _units(script) if u.speaker in ("DIRECTOR", "SKEPTIC"))

def labels_preserved(old: str, new: str) -> bool:
    """A rewrite (humanize, length fix, extension) may not silently drop the speaker labels: at least 85 percent must survive."""
    if mode() == "classic": return True
    o = label_count(old)
    return o == 0 or label_count(new) >= 0.85 * o

def one_voice() -> bool:
    """v12 V2b: is the episode in the making a format with ONE voice (F3: the guide alone)? Only while ENDINGS_ON (3.3: every place changes only then)."""
    from whatifs.core import S
    from whatifs import formats as FMT
    k = FMT.current()
    return bool(S("ENDINGS_ON", bool) and k in FMT.FORMATS and len(FMT.FORMATS[k]["voices"]) == 1)

def check_script(script: str) -> dict:
    """Code-side check of the two-role format. ok=False means the writer must be asked once to fix it. v12 V2b: a format with one voice is never
    asked for a second role, and its 45-percent rule counts the guide's labels."""
    if mode() == "classic": return {"ok": True, "issues": [], "units": 0, "labeled": 0, "director": 0, "skeptic": 0}
    us = _units(script); n = max(1, len(us)); one = one_voice()
    d = sum(1 for u in us if u.speaker == "DIRECTOR"); k = sum(1 for u in us if u.speaker == "SKEPTIC")
    lab = d if one else d + k + sum(1 for u in us if u.speaker in ("JUDGE", "WITNESS"))       # v9: the judge and the witness are labelled lines too
    issues = []
    if lab / n < 0.45: issues.append(f"only {lab} of {len(us)} spoken lines carry a [DIRECTOR] or [SKEPTIC] label (need at least 45 percent)")
    if not one and min(d, k) < max(3, int(0.12 * (d + k))): issues.append(f"one role barely speaks (DIRECTOR {d}, SKEPTIC {k}); both must contribute reasoning")
    return {"ok": not issues, "issues": issues, "units": len(us), "labeled": lab, "director": d, "skeptic": k}

ASKS_ONE = ("Audience asks: exactly ONE short, witty, in-story moment in which the Curious One asks for a subscribe, after a payoff, never near the end; no like "
            "ask, no share ask.")
ASKS_NONE = "Audience asks: none, anywhere."
TAG_SENTENCE = " The video marks who is speaking with a code-drawn speaker tag."

def _for_format(block: str) -> str:
    """v12 V2b: the block line by line for the format in the making (only while ENDINGS_ON and an episode has a format; a trial's block byte for byte):
    the line 'Audience asks:' as the format's asks; the line 'Shorts:' left out outside a trial (a long video makes no Short of itself); the story
    engine ends as the format ends, not on a verdict; the speaker tag's sentence left out where the format's row shows no name chip (F1, F3)."""
    from whatifs.core import S
    from whatifs import formats as FMT
    k = FMT.current()
    if not S("ENDINGS_ON", bool) or k not in FMT.FORMATS: return block
    trial = FMT.FORMATS[k]["show"]; a = FMT.asks(); out = []
    from whatifs import path as PATH
    path_ = PATH.on(); grammar = False                                     # v12 V2b: in a camera-path format the two visual-grammar lines become ONE line, the path's rules
    one = len(FMT.FORMATS[k]["voices"]) == 1; reactions = False            # v12 V2b (3.3 d): a format with ONE voice is told of no second role and no reactions
    for line in block.split("\n"):
        if one:
            if line.startswith("Reaction rules:"): reactions = True; continue
            if reactions and line.startswith("- "): continue
            reactions = False
            if line.startswith(("- [SKEPTIC] =", "- Write natural back-and-forth", "- Alternate speakers")): continue
            line = line.replace("The two of them are the whole show: no third voice, no announcer.", "The guide is the whole show: no second voice, no announcer.")
        if path_ and (line.startswith("- The studio/control room is a recurring home base") or line.startswith("- Visualize consequences whenever")):
            if not grammar: out.append("- " + PATH.director_rules()); grammar = True
            continue
        if line.startswith("- A PRESENTER IS DRAWN OR ABSENT") and not FMT.chips(): line = line.replace(TAG_SENTENCE, "")
        if line.startswith("Audience asks:") and a != FMT.ALL_ASKS:
            if a == ("subscribe",): out.append(ASKS_ONE)
            elif not a: out.append(ASKS_NONE)
            else: out.append(line)
            continue
        if line.startswith("Shorts:") and not trial: continue
        if line.startswith("Story engine:") and not trial:
            line = line.replace("end with a clear verdict and honest uncertainty", "end as this format ends, with honest uncertainty")
        out.append(line)
    return "\n".join(out)

def instructions(role: str = "general") -> str:
    base = CLASSIC if mode() == "classic" else _for_format(REALITY_ENGINE)
    role_notes = {
        "showrunner": "Showrunner: include presentation_format='reality_engine', director_role, skeptic_role, scenario_rules, escalation_steps, and a payoff in the spine. Do not make the format overwhelm the premise.",
        "memo": "Department memo: keep your advice consistent with the two recurring presenter roles (Director, Skeptic) and the faceless presenter rule.",
        "bible": "Production bible: include the recurring characters' temperaments and their contrasting goals (never a description of how to PICTURE them: a character appears only as its approved art, placed by the renderer), recurring studio/control-room motif, palette, and 3–5 distinct scenario visual beats. Keep character designs original and repeatable.",
        "writer": "Writer: preserve the existing beat structure and target length. Label dialogue lines [DIRECTOR] or [SKEPTIC]. Use unlabelled text only for the opening hook or brief neutral narration. Do not add labels as spoken words. Give each beat at least one new visual event or meaningful turn; don't force both characters into every beat.",
        "director": "Director: use the studio/control room for setup, debate, and verdict; use scenario visualizations for physical consequences. Ensure shot prompts make the consequence visually legible; plan NO shot of a presenter - no face, no dark shape, no back of a head (a character is drawn from its approved art by the renderer, or is absent); and reserve the strongest motion for a genuine story peak. Do not create fake real-world news graphics.",
        "packager": "Packager: sell the impossible scenario and its consequence, not 'a podcast'. Use the recurring characters only if they strengthen the thumbnail. Titles must remain accurate to the actual scenario and uncertainty.",
        "critic": "Critic: assess whether the two roles contribute distinct reasoning, the simulation escalates visually, the premise is clear immediately, and the conclusion distinguishes fact from speculation. Penalize empty dialogue, repetitive studio coverage, and format gimmicks that delay the payoff.",
        "continuity": "Continuity check: confirm the recurring presenter roles and visual motif stay consistent, the timeline/state indicators agree with the narration, and the episode never presents the fictional scenario as actual news.",
    }
    if mode() == "classic":
        return base
    from whatifs.core import S
    from whatifs import path as PATH, formats as FMT
    if S("ENDINGS_ON", bool) and FMT.current() in FMT.FORMATS and PATH.on():        # v12 V2b: a camera-path format has no studio for setup, debate and verdict
        role_notes["director"] = role_notes["director"].replace("use the studio/control room for setup, debate, and verdict; ", "")
    if one_voice():                                                                   # v12 V2b (3.3 d): each note minus the clause that names the second role
        role_notes["memo"] = role_notes["memo"].replace("the two recurring presenter roles (Director, Skeptic) and ", "")
        role_notes["writer"] = role_notes["writer"].replace(" or [SKEPTIC]", "").replace("; don't force both characters into every beat", "")
        role_notes["critic"] = role_notes["critic"].replace("the two roles contribute distinct reasoning, ", "")
    return base + "\n\nROLE-SPECIFIC REQUIREMENTS: " + role_notes.get(role,"Keep the simulation visually legible, character-driven, original, and scientifically honest.")

def enrich_spine(spine: dict) -> dict:
    """Add safe metadata without removing or replacing fields from the existing spine."""
    out = dict(spine or {})
    out.setdefault("presentation_format", mode())
    if mode() != "classic":
        out.setdefault("format_name", FORMAT_NAME)
        out.setdefault("director_role", "The Simulation Director")
        out.setdefault("skeptic_role", "The Curious One")
        out.setdefault("scenario_rules", "State what changes, what stays constant, and the key assumptions.")
    return out
