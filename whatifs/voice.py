"""Narration voice and pacing: the TTS engine with its fallback, human-style timing, markers and the master chain. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, os, re, subprocess, random
from dataclasses import dataclass
import numpy as np
try:
    from whatifs.core import S
except Exception:      # the voice lab can run without the settings store
    def S(key, cast=str): raise KeyError(key)

SR = 24000            # Kokoro native rate
OUT_SR = 48000

# ---------- pacing styles (rotated + learned later; values are starting points) ----------
STYLES = {
    #               base speed, gap multiplier, speed jitter, arc (start->end multiplier)
    "hypnotic":       dict(base=0.93, gap=1.25, jit=0.020, arc=(1.00, 1.00)),
    "urgent":         dict(base=1.05, gap=0.80, jit=0.030, arc=(1.00, 1.00)),
    "slow_burn":      dict(base=0.97, gap=1.05, jit=0.025, arc=(0.96, 1.05)),
    "brake":          dict(base=1.00, gap=0.95, jit=0.025, arc=(1.05, 0.94)),
    "conversational": dict(base=1.00, gap=1.00, jit=0.035, arc=(1.00, 1.00)),
}
TAGS = {  # speed multiplier, extra gap before (s), extra gap after (s)
    "calm":    (0.96, 0.00, 0.10),
    "tension": (1.05, 0.00, 0.00),
    "reveal":  (0.91, 0.40, 0.35),
    "aside":   (1.02, 0.20, 0.45),   # humour: land the line, then let it sit
    "callback":(0.98, 0.30, 0.60),
    # v8.2 reaction deliveries (the Curious One) and the expert's patience
    "wow":     (1.10, 0.06, 0.40),   # quick, bright, a small beat after so the effect can land
    "gasp":    (1.14, 0.00, 0.28),
    "awe":     (0.88, 0.28, 0.55),   # slow, breathy, long hold
    "laugh":   (1.06, 0.10, 0.32),
    "doubt":   (0.96, 0.12, 0.22),
    "patient": (0.93, 0.12, 0.25),   # the Director asking for patience before a payoff
    "close":   (0.92, 0.25, 0.45),   # v8.7: a quiet, intimate line (1-2 per video); the music hushes under it
    "none":    (1.00, 0.00, 0.00),
}

@dataclass
class Blend:
    name: str
    parts: dict            # {"af_heart":0.5, ...}  (v8.10: also the Kokoro FALLBACK recipe when gvoice is set)
    lang: str = "a"        # American English pronunciation
    gvoice: str = ""       # v8.10: the Gemini voice (Cast tab); empty = Kokoro only
    gstyle: str = ""       # v8.10: the cast member's style direction (Gemini turn style)
    def voiceprint(self) -> str:
        key = json.dumps({"p": dict(sorted(self.parts.items())), "l": self.lang, **({"g": self.gvoice} if self.gvoice else {})}, sort_keys=True)
        return "WI-VOICE-" + hashlib.sha256(key.encode()).hexdigest()[:10].upper()

@dataclass
class Unit:
    text: str
    tag: str = "none"
    speaker: str = "NARRATOR"
    gap_before: float = 0.0
    hesitate_after: float = 0.0     # from "..." or [beat]
    new_para: bool = False
    curve: list = None              # v8.10: delivery curve words from {braces} (slow, low, whisper...); never spoken
    events: list = None             # v8.10: vocal events from {braces} (breath, gasp, laugh...) on the FIRST piece of the line only
    show: list = None               # v9: show tags on this line ([EXHIBIT A], [METER +1 vale], [JURY], [CLIPBAIT], [/CLIPBAIT]); never spoken

# ---------- script parsing ----------
SPEAKERS = ("DIRECTOR", "SKEPTIC", "HOST_A", "HOST_B", "JUDGE", "WITNESS")      # v9: the judge and the surprise witness
# v8.3: every way a model writes a speaker name ('**Director:**', '[THE CURIOUS ONE]', 'CURIOUS ONE (laughing):', a label alone on its line) is one of the two roles
ALIASES = {"DIRECTOR": "DIRECTOR", "THE DIRECTOR": "DIRECTOR", "SIMULATION DIRECTOR": "DIRECTOR", "THE SIMULATION DIRECTOR": "DIRECTOR",
           "SKEPTIC": "SKEPTIC", "THE SKEPTIC": "SKEPTIC", "CURIOUS": "SKEPTIC", "CURIOUS ONE": "SKEPTIC", "THE CURIOUS ONE": "SKEPTIC",
           "HOST_A": "HOST_A", "HOST A": "HOST_A", "HOST_B": "HOST_B", "HOST B": "HOST_B",
           "VALE": "DIRECTOR", "INSPECTOR VALE": "DIRECTOR", "GRIMM": "SKEPTIC", "DR GRIMM": "SKEPTIC", "DR. GRIMM": "SKEPTIC", "DOCTOR GRIMM": "SKEPTIC",
           "JUDGE": "JUDGE", "NANA ROSA": "JUDGE", "NANA": "JUDGE", "ROSA": "JUDGE", "WITNESS": "WITNESS", "ARCHIVIST": "WITNESS", "THE ARCHIVIST": "WITNESS"}
_NAME_ALT = r"INSPECTOR\s+VALE|VALE|DR\.?\s+GRIMM|DOCTOR\s+GRIMM|GRIMM|NANA\s+ROSA|NANA|ROSA|JUDGE|THE\s+ARCHIVIST|ARCHIVIST|WITNESS|THE\s+SIMULATION\s+DIRECTOR|SIMULATION\s+DIRECTOR|THE\s+DIRECTOR|DIRECTOR|THE\s+SKEPTIC|SKEPTIC|THE\s+CURIOUS\s+ONE|CURIOUS\s+ONE|CURIOUS|HOST[_ ]A|HOST[_ ]B"
_BRACKET_RE = re.compile(r"^\[([^\[\]]{1,26})\]\s*")
_COLON_RE = re.compile(r"^(" + _NAME_ALT + r")\s*(?:\([^)]{0,24}\))?\s*(?::\s*|[\u2014\u2013-]\s+)", re.IGNORECASE)
_SPLIT_SPK_RE = re.compile(r"(?=\[(?:" + _NAME_ALT + r")\])", re.IGNORECASE)
_STRAY_RE = re.compile(r"\[[A-Za-z_ ]{1,26}(?::[A-Za-z_]{1,12})?\]")      # a bracket word must never be read aloud
_SHOW_RE = re.compile(r"\[\s*(?:/?CLIPBAIT|METER\s*[+-]?\d+\s+(?:GRIMM|VALE)|EXHIBIT\s+[A-H]|JURY|TEACUP|PUNCH|SEND|AWE)\s*\]", re.IGNORECASE)      # v9; v11.1: + PUNCH/SEND/AWE markers
_STAGE_RE = re.compile(r"^\(([A-Za-z ,'\u2019-]{1,32})\)\s*")                 # '(laughing) Okay that is wild.' -> a delivery hint, never spoken

def _speaker_of(name):
    return ALIASES.get(re.sub(r"\s+", " ", str(name).strip().upper()))

def _peel(line):
    """Read the leading [tokens] of a line in ANY order ([DIRECTOR] [calm] / [calm] [DIRECTOR] / **[SKEPTIC]** / 'Skeptic: ...' / '**Director:** ...' / '[CURIOUS ONE]').
    Returns (speaker or None, delivery tag, pause seconds, remaining text). Unknown leading tokens and stage directions are dropped, never spoken."""
    line = re.sub(r"\*\*|__|`+", "", line)
    line = re.sub(r"^(?:[\s*_>#]+|[-\u2022]\s+)+", "", line).strip()
    speaker, tag, pause = None, "none", 0.0
    for _ in range(6):
        m = _COLON_RE.match(line)
        if m: speaker = _speaker_of(m.group(1)) or speaker; line = line[m.end():].strip(); continue
        m = _BRACKET_RE.match(line)
        if not m: break
        name, _, arg = m.group(1).strip().partition(":"); low = name.strip().lower()
        if low == "beat": break                                     # inline micro-pause marker: handled later
        sp = _speaker_of(name)
        if sp or name.strip().upper() == "NARRATOR": speaker = sp
        elif low == "pause": pause += {"long": 1.6, "short": 0.6}.get(arg.strip().lower(), 1.0)
        elif low in TAGS and tag == "none": tag = low
        line = line[m.end():].strip()
        if sp: line = re.sub(r"^[:\u2014\u2013]\s*", "", line)         # '[THE CURIOUS ONE]: text'
    m = _STAGE_RE.match(line)
    if m:
        hint = m.group(1).lower()
        if tag == "none" and re.match(r"(laugh|chuckl|giggl|snicker)", hint): tag = "laugh"
        line = line[m.end():].strip()
    return speaker, tag, pause, line

_CURVE_RE = re.compile(r"\{([^{}]{0,80})\}")
def _curve(chunk):
    """v8.10: the writer's delivery curve in braces, e.g. '[SKEPTIC] [tension] {slow, low, whisper, breath} text'. Returns (text without braces, curve words,
    vocal events). Unknown words are dropped; braces are NEVER spoken (also when EMOTION_CURVE_ON is FALSE)."""
    from whatifs.data import CURVE_WORDS, CURVE_EVENTS
    words = [w.strip().lower() for m in _CURVE_RE.findall(chunk) for w in re.split(r"[,;/ ]+", m) if w.strip()]
    return _CURVE_RE.sub(" ", chunk), [w for w in dict.fromkeys(words) if w in CURVE_WORDS], [w for w in dict.fromkeys(words) if w in CURVE_EVENTS]

_CURVE_SPEED = {"slow": 0.94, "fast": 1.06, "whisper": 0.95, "hushed": 0.96, "breathless": 1.04}
def curve_speed(u):
    """Kokoro's share of the emotion curve: only the pace words (it cannot whisper or gasp)."""
    k = 1.0
    for w in (u.curve or []): k *= _CURVE_SPEED.get(w, 1.0)
    return k

def parse_script(script: str) -> list[Unit]:
    """Lines may start with [calm] [tension] [reveal] [aside] [callback] [pause:long] [pause:short] and, in Reality Engine mode, a speaker label
    ([DIRECTOR] or [SKEPTIC], also 'Director:' or '**Skeptic:**' or '[THE CURIOUS ONE]') in either order. A label alone on its line applies to the next line of speech.
    Inline: '...' = hesitation, [beat] = comic micro-pause. Labels are never spoken."""
    units: list[Unit] = []
    pending_gap = 0.0; para = False; prev_spk = None; carry = "none"; sticky = None; pend_show = []
    for raw in script.splitlines():
        if not raw.strip():
            para = True; continue
        for chunk in [c for c in _SPLIT_SPK_RE.split(raw) if c.strip()]:     # two speakers packed on one line become two units
            chunk, curve, events = _curve(chunk)                                # v8.10: {slow, whisper, breath} never spoken
            show = [re.sub(r"\s+", " ", m.group(0).upper()) for m in _SHOW_RE.finditer(chunk)]       # v9: show tags kept as data, never spoken
            chunk = _SHOW_RE.sub(" ", chunk)
            if show and not chunk.strip(): pend_show += show; continue
            show = pend_show + show; pend_show = []; close_later = False
            spk, tag, pause, line = _peel(chunk)
            pending_gap += pause
            if any("PUNCH" in s_ for s_ in show):                              # v11.1 (K166): pause-then-punch (300-700 ms of silence)
                from whatifs.core import S as _S; pending_gap += _S("PUNCH_PAUSE_S", float)
            if tag == "none": tag = carry                                      # '[tension] [SKEPTIC] text': the tag belongs to the text that follows
            if not line:
                carry = tag
                if spk: sticky = spk                                           # '[SKEPTIC]' alone on a line: the next line of speech is theirs
                continue
            carry = "none"
            speaker = spk or sticky or "NARRATOR"; sticky = None
            if prev_spk and speaker != prev_spk and "NARRATOR" not in (speaker, prev_spk): pending_gap += 0.10      # a small turn-taking gap between two characters
            prev_spk = speaker
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for i, s in enumerate(sentences):
                pieces = re.split(r"\s*(?:\.\.\.|\u2026|\[beat\])\s*", s)
                for j, p in enumerate(pieces):
                    p = re.sub(r"\s+", " ", _STRAY_RE.sub(" ", p)).strip()
                    if not p: continue
                    u = Unit(text=p, tag=tag, speaker=speaker, gap_before=pending_gap, new_para=para and i == 0 and j == 0,
                             curve=list(curve), events=list(events) if (i == 0 and j == 0) else [], show=list(show) if (i == 0 and j == 0) else [])
                    if "[/CLIPBAIT]" in show and (i, j) == (len(sentences) - 1, len(pieces) - 1): pass
                    elif "[/CLIPBAIT]" in show and (i == 0 and j == 0) and (len(sentences) > 1 or len(pieces) > 1):      # the closing tag belongs to the line's end
                        u.show = [x for x in show if x != "[/CLIPBAIT]"]; close_later = True
                    if j < len(pieces) - 1: u.hesitate_after = 1.0
                    units.append(u); pending_gap = 0.0; para = False
            if close_later and units: units[-1].show = (units[-1].show or []) + ["[/CLIPBAIT]"]
            close_later = False
    return units

# ---------- audio helpers ----------
def _trim(a: np.ndarray, thr_db=-45.0, keep=0.03, info=False):
    """Cut leading/trailing silence. info=True also returns the seconds removed at the start (word timings must be moved by the same amount)."""
    if a.size == 0: return (a, 0.0) if info else a
    win = int(0.01 * SR)
    env = np.sqrt(np.convolve(a.astype(np.float64)**2, np.ones(win)/win, mode="same"))
    idx = np.where(env > 10 ** (thr_db / 20))[0]
    if idx.size == 0: return (a, 0.0) if info else a
    s = max(0, idx[0] - int(keep*SR)); e = min(a.size, idx[-1] + int(keep*SR))
    return (a[s:e], s / SR) if info else a[s:e]

def _breath(rng: random.Random, db: float = -34.0) -> np.ndarray:
    """Soft synthetic inhale: band-limited noise with a rise/fall envelope, ~-40 dBFS."""
    n = int(rng.uniform(0.20, 0.34) * SR)
    nr = np.random.default_rng(rng.randrange(1 << 30))
    x = nr.standard_normal(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1/SR)
    X *= ((f > 400) & (f < 3200)) * (1 / np.maximum(f, 1) ** 0.3)
    x = np.fft.irfft(X, n)
    t = np.linspace(0, 1, n); env = np.sin(np.pi * t) ** 1.6
    x = x * env; x /= (np.sqrt(np.mean(x**2)) + 1e-9)
    return (x * 10 ** (db / 20)).astype(np.float32)

def _sil(sec: float) -> np.ndarray: return np.zeros(int(max(0, sec) * SR), dtype=np.float32)

# ---------- TTS backend ----------
class KokoroBackend:
    def __init__(self, blend: Blend):
        import torch
        from kokoro import KPipeline
        self.torch = torch
        self.pipe = KPipeline(lang_code=blend.lang)
        self.packs = {"NARRATOR": self._make_pack(blend)}
        self.pack = self.packs["NARRATOR"]
    def _make_pack(self, blend: Blend):
        total = sum(blend.parts.values()) or 1.0
        pack = None
        for name, wgt in blend.parts.items():
            loader = getattr(self.pipe, "load_single_voice", None) or self.pipe.load_voice
            v = loader(name).float()
            pack = v * (wgt / total) if pack is None else pack + v * (wgt / total)
        return pack
    def register_speaker(self, speaker: str, blend: Blend):
        self.packs[str(speaker).upper()] = self._make_pack(blend)
    def synth(self, text: str, speed: float, speaker: str = "NARRATOR"):
        audio, words, off = [], [], 0.0
        voice_pack = self.packs.get(str(speaker).upper(), self.pack)
        for r in self.pipe(text, voice=voice_pack, speed=speed):
            a = r.audio.detach().cpu().numpy() if hasattr(r.audio, "detach") else np.asarray(r.audio)
            for tk in (getattr(r, "tokens", None) or []):
                st, en = getattr(tk, "start_ts", None), getattr(tk, "end_ts", None)
                if st is not None and en is not None and tk.text.strip():
                    words.append({"w": tk.text, "s": off + float(st), "e": off + float(en)})
            audio.append(a.astype(np.float32)); off += a.size / SR
        return (np.concatenate(audio) if audio else np.zeros(0, np.float32)), words

# ---------- v8.4: natural irregularity ----------
class _Pacer:
    """Human timing is irregular but not random noise: tempo wanders slowly (neighbouring lines sound alike), pauses are heavy-tailed (mostly short, now and then a
    long think), and they follow the sense (a question earns a beat, a snappy reply comes fast, a long sentence earns a breath). Every episode also draws its own
    'personality' from wide continuous ranges instead of one of five fixed styles. Everything is seeded by the episode id, so a retry or a resume re-voices the
    SAME audio the saved shot list was timed against; unseeded randomness would break sync. Limits keep every value inside what still sounds like speech."""
    def __init__(self, rng, st):
        self.r = rng; self.st = st
        self.tempo = rng.uniform(0.975, 1.03)            # this episode's tempo habit
        self.gap_scale = rng.uniform(0.85, 1.20)         # fast talker or deliberate talker
        self.sigma = rng.uniform(0.38, 0.62)             # how uneven the pauses are
        self.pull = rng.uniform(0.80, 0.93)              # how slowly the tempo wanders
        self.amp = st["jit"] * rng.uniform(0.9, 1.6)
        self.long_rate = rng.uniform(0.02, 0.06)         # rare thinking pauses
        self.breath_bias = rng.uniform(0.7, 1.3)
        self.drift = 0.0; self.burst_left = 0; self.burst = 1.0
    def speed(self, prog, tag_mult):
        r, st = self.r, self.st
        arc = st["arc"][0] + (st["arc"][1] - st["arc"][0]) * prog
        self.drift = self.pull * self.drift + r.gauss(0, self.amp * (1 - self.pull ** 2) ** 0.5)
        if self.burst_left > 0: self.burst_left -= 1
        else:
            self.burst = 1.0
            if r.random() < 0.04: self.burst_left = r.randint(2, 4); self.burst = 1.0 + r.choice([-1, 1]) * r.uniform(0.03, 0.06)
        v = st["base"] * arc * tag_mult * self.tempo * (1 + self.drift) * self.burst * (1 + r.gauss(0, st["jit"] * 0.4))
        return min(1.15, max(0.85, v))
    def gap(self, u, prev, new_para):
        r = self.r; mean = 0.38 * self.st["gap"] * self.gap_scale
        g = mean / (2.718281828 ** (self.sigma ** 2 / 2)) * 2.718281828 ** (self.sigma * r.gauss(0, 1))      # log-normal with the SAME average as before
        pw = len(prev.text.split()) if prev else 0; nw = len(u.text.split()); pend = (prev.text.rstrip()[-1:] if prev else "")
        if pend == "?": g *= r.uniform(1.15, 1.5)
        elif pend == "!": g *= 0.85
        if pw >= 20: g *= 1.15
        elif 0 < pw <= 3: g *= 0.8
        if prev and u.speaker != prev.speaker:
            g *= r.uniform(0.25, 0.7) if nw <= 5 else 0.9          # a short reply lands fast
        if prev and pw >= 8 and r.random() < self.long_rate: g += r.uniform(0.55, 1.1)       # a thinking pause
        if new_para: g += r.uniform(0.30, 0.55)
        return min(1.8, max(0.0, g))
    def breath(self, gap, u, prev, rate):
        pw = len(prev.text.split()) if prev else 0
        p = min(0.95, rate * self.breath_bias * (0.5 + min(pw, 24) / 24))
        return gap >= 0.40 and len(u.text.split()) >= 7 and self.r.random() < p
    def hesitation(self):
        return min(0.95, max(0.25, 0.45 * 2.718281828 ** (0.3 * self.r.gauss(0, 1))))

# ---------- the narrator ----------
@dataclass
class NarrationResult:
    wav_path: str
    timeline_path: str
    duration: float
    voiceprint: str
    style: str

def narrate(script: str, blend: Blend, out_base: str, style: str = "slow_burn",
            seed: str = "lab", humanize: bool = True, breaths: bool = True,
            backend=None, speaker_blends: dict[str, Blend] | None = None, unit_hook=None) -> NarrationResult:
    rng = random.Random(hashlib.md5(f"{seed}|{style}".encode()).hexdigest())
    try:
        from whatifs.core import S
        trim, bdb, brate = S("SPEED_TRIM", float), S("BREATH_DB", float), S("BREATH_RATE", float)
    except Exception:
        trim, bdb, brate = 1.04, -34.0, 0.6
    st = dict(STYLES.get(style, STYLES["slow_burn"])); st["base"] *= trim
    speaker_blends = speaker_blends or {}; voice_fallback = []
    units = parse_script(script)
    from whatifs.org import audience as _AUD                # v12 V1 (D13): the voice breathes - a pause at a sentence start at least every BREATH_EVERY_S
    units = _AUD.breathe(units)
    if unit_hook:
        try: units = unit_hook(units) or units
        except Exception: pass                          # a helper must never stop the narration
    engine, be, engine_note = "kokoro", backend, ""
    if be is None and _gemini_wanted(blend, speaker_blends):     # v8.10: Gemini TTS; the whole narration falls back to Kokoro on failure (never a mix)
        try:
            from whatifs.tts_gemini import GeminiBackend
            spk = {k: (b.gvoice, b.gstyle) for k, b in speaker_blends.items() if b.gvoice}
            if blend.gvoice: spk.setdefault("NARRATOR", (blend.gvoice, blend.gstyle))
            g = GeminiBackend(spk, episode=seed); g.prime(_director_units(units, speaker_blends)); be, engine = g, "gemini"
        except Exception as e:
            try: from whatifs.core import log, scrub, note_degraded
            except Exception: log = scrub = note_degraded = None
            fb = True
            try: fb = S("TTS_FALLBACK_ON", bool)
            except Exception: pass
            if not fb: raise
            engine_note = f"Gemini TTS failed, whole narration re-voiced with Kokoro: {str(e)[:160]}"
            if log: log(engine_note, "WARN"); note_degraded("narration voiced by Kokoro (Gemini TTS failed)")
            be = None
    be = be or KokoroBackend(blend)
    if hasattr(be, "register_speaker"):
        for speaker, speaker_blend in speaker_blends.items():
            try:
                be.register_speaker(speaker, speaker_blend)
            except Exception as e:
                # Keep the episode renderable if an optional character voice cannot load, but say so (K-rule: no silent downgrade).
                voice_fallback.append(str(speaker).upper())
                try:
                    from whatifs.core import log, scrub
                    log(f"character voice {speaker} could not load ({scrub(e)[:120]}) - that role uses the default narrator voice", "WARN")
                except Exception: pass
    if speaker_blends and "DIRECTOR" in speaker_blends and "DIRECTOR" not in voice_fallback:
        for u in units:
            if u.speaker == "NARRATOR": u.speaker = "DIRECTOR"     # v8.3: in the two-role format an unlabelled line is the Director's: there is never a third voice
    n = max(1, len(units))
    chunks, timeline, t = [], [], 0.0
    def add(a):
        nonlocal t
        chunks.append(a); t += a.size / SR
    add(_sil(0.35))
    try: natural = humanize and str(S("PACING_MODE")).strip().lower() != "classic"
    except Exception: natural = humanize
    pacer = _Pacer(rng, st) if natural else None
    for i, u in enumerate(units):
        sm, gb, ga = TAGS.get(u.tag, TAGS["none"])
        t_gap0 = t; breath_here = False        # v7.4: remember which pauses were planned, so the cut map can tell them from dead air
        why_before = (["explicit_pause"] if u.gap_before > 0 else []) + (["paragraph"] if (u.new_para and humanize) else []) + ([f"tag:{u.tag}"] if (gb > 0 and humanize) else [])
        if humanize:
            prog = i / max(1, n - 1)
            if natural:
                speed = pacer.speed(prog, sm)
                gap = (pacer.gap(u, units[i - 1] if i else None, u.new_para) if i else 0.0) + gb + u.gap_before
                brk = pacer.breath(gap, u, units[i - 1] if i else None, brate) if i else False
            else:
                arc = st["arc"][0] + (st["arc"][1] - st["arc"][0]) * prog
                speed = st["base"] * arc * sm * (1 + rng.gauss(0, st["jit"]))
                speed = min(1.15, max(0.85, speed))
                gap = (rng.gauss(0.38, 0.07) if i else 0.0) * st["gap"]
                if u.new_para: gap += rng.uniform(0.30, 0.55)
                gap = max(0.0, gap) + gb + u.gap_before
                brk = bool(i and breaths and gap >= 0.40 and len(u.text.split()) >= 7 and rng.random() < brate)
            if i and breaths and brk and engine != "gemini":         # v8.10: Gemini breathes by itself (<breath> tags); no synthetic breath on top
                b = _breath(rng, bdb); pre = max(0.05, gap - b.size / SR - 0.08)
                add(_sil(pre)); add(b); add(_sil(0.08)); breath_here = True
            else:
                add(_sil(gap))
        else:
            speed = 1.0; add(_sil((0.25 if i else 0) + u.gap_before))
        pause_before = t - t_gap0
        if engine == "gemini":
            audio, words = be.take(i, u)
        elif hasattr(be, "register_speaker") and hasattr(be, "packs"):
            audio, words = be.synth(u.text, min(1.15, max(0.85, speed * curve_speed(u))), speaker=u.speaker)
        else:
            audio, words = be.synth(u.text, speed)
        audio, lead = _trim(audio, info=True)
        try:                                                                       # v9.2: per-line levelling + peak limiter (consistent loudness)
            from whatifs import v91 as V91
            if V91.on("VOICE_LEVEL_ON"):
                from whatifs.voiceq import level as _lvl
                audio = _lvl(audio, SR)
        except Exception as e_: log(f"voice levelling skipped: {e_}", "WARN")
        if lead: words = [{"w": x["w"], "s": max(0.0, x["s"] - lead), "e": max(0.0, x["e"] - lead)} for x in words]      # v8.3: word times follow the audio that was trimmed
        start = t; add(audio)
        entry = {"i": i, "text": u.text, "tag": u.tag, "speaker": u.speaker, "speed": round(speed, 3), "curve": (u.curve or []) + (u.events or []), "show": list(u.show or []),
                 "start": round(start, 3), "end": round(t, 3),
                 "words": [{"w": x["w"], "s": round(start + x["s"], 3), "e": round(start + x["e"], 3)} for x in words],
                 "pause_before": round(pause_before, 3), "pause_before_reasons": why_before + (["breath"] if breath_here else []),
                 "pause_after": 0.0, "pause_after_reasons": []}
        timeline.append(entry)
        if humanize:
            tail = ga + ((pacer.hesitation() if natural else rng.uniform(0.35, 0.60)) if u.hesitate_after else 0.0)
            if tail:
                add(_sil(tail)); entry["pause_after"] = round(tail, 3)
                entry["pause_after_reasons"] = ([f"tag:{u.tag}"] if ga > 0 else []) + (["hesitation"] if u.hesitate_after else [])
    add(_sil(0.6))
    raw = np.concatenate(chunks)
    raw_path = out_base + "_raw.wav"
    _write_wav(raw_path, raw, SR)
    wav_path = out_base + ".wav"
    _master(raw_path, wav_path)
    os.remove(raw_path)
    dur = _probe(wav_path)
    tl = {"voiceprint": blend.voiceprint(), "blend": blend.parts, "speaker_blends": {k: v.parts for k, v in speaker_blends.items()}, "voice_fallback": voice_fallback, "style": style,
          "humanized": humanize, "duration": dur, "units": timeline, "engine": engine, "engine_note": engine_note,
          "gemini_voices": {k: v.gvoice for k, v in speaker_blends.items() if v.gvoice} if engine == "gemini" else {},
          "align": getattr(be, "align", {}), "tts_stats": getattr(be, "stats", {})}
    tl_path = out_base + "_timeline.json"
    json.dump(tl, open(tl_path, "w"), indent=1)
    return NarrationResult(wav_path, tl_path, dur, blend.voiceprint(), style)

def _gemini_wanted(blend, speaker_blends):
    try: eng = str(S("TTS_ENGINE") or "gemini").strip().lower()
    except Exception: return False
    if eng != "gemini": return False
    roles = [b for b in (speaker_blends or {}).values()] or [blend]
    return all(b.gvoice for b in roles)

def _director_units(units, speaker_blends):
    """The Gemini request must already know that an unlabelled line is the Director's (the same rule narrate applies below)."""
    if speaker_blends and "DIRECTOR" in speaker_blends:
        for u in units:
            if u.speaker == "NARRATOR": u.speaker = "DIRECTOR"
    return units

def _write_wav(path, a, sr):
    import soundfile as sf
    sf.write(path, np.clip(a, -1, 1), sr, subtype="PCM_16")

def _master(src, dst):
    """v8.9 clarity chain (the v8.3 chain added a small echo and a low-mid boost that made the voice sound dense and 'in a room'):
    rumble cut, a gentle cut of the muddy low-mids, presence and air for intelligibility, a light de-esser, soft compression, NO echo or reverb,
    a whisper of room tone so silences are not digital, loudness to -16 LUFS. A dry, close voice is what sounds clear on earbuds."""
    af = ("highpass=f=85,equalizer=f=280:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=2.0,equalizer=f=9500:t=q:w=1.6:g=1.2,"
          "deesser=i=0.35,acompressor=threshold=-21dB:ratio=2.0:attack=12:release=180,aresample=48000")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
           "-f", "lavfi", "-i", "anoisesrc=color=pink:amplitude=0.0006:sample_rate=48000",
           "-filter_complex", f"[0:a]{af}[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,"
           "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]",
           "-map", "[o]", "-ac", "1", "-ar", str(OUT_SR), dst]
    subprocess.run(cmd, check=True)

def _probe(p) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return round(float(r.stdout.strip()), 3)

