"""Sound design: code-generated textures under the shots, per-world beds, story events and a music bed that moves. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, re
import numpy as np
from whatifs.core import S

KINDS = ("drip", "crackle", "wind", "heartbeat", "hum", "fizz", "rumble", "tick", "rain", "glass")
DENSITY = {"sparse": 0.10, "textured": 0.20, "rich": 0.30}        # share of shots that may carry a texture
ARCS = ("build", "waves", "pulse", "still")
LEVEL = 0.04                                                        # texture peak before ducking (the bed peaks near 0.063)
REACT = ("wow", "gasp", "awe", "laugh", "doubt")
_KEYS = (("rain", r"\brain|storm|downpour"),
         ("drip", r"water|drip|ocean|\bsea\b|lake|river|\bwet\b|liquid|tears?\b|sweat|blood"),
         ("crackle", r"fire|burn|flame|lava|volcan|spark|electric|lightning"),
         ("wind", r"wind|\bair\b|\bsky\b|cloud|altitude|breath|lungs|everest|desert"),
         ("heartbeat", r"heart|pulse|pounding|panic|nerve"),
         ("glass", r"glass|\bice\b|frozen|crystal|diamond|mirror"),
         ("rumble", r"earthquake|quake|explo|collapse|crash|impact|mountain|tectonic|thunder"),
         ("tick", r"clock|second|minute|countdown|timer|\btick|\bhour"),
         ("fizz", r"acid|soda|fizz|bubble|chemical|dissolv"),
         ("hum", r"space|orbit|\bmoon\b|\bsun\b|\bstar|planet|black hole|magnet|machine|engine|\bgrid\b|signal"))

def _seed(x): return int(hashlib.md5(str(x).encode()).hexdigest()[:8], 16)

def guess(text):
    """The texture a line is about, from plain keywords (None = nothing obvious)."""
    t = str(text or "").lower()
    for kind, rx in _KEYS:
        if re.search(rx, t): return kind
    return None

def density_of(name):
    """'sparse' | 'textured' | 'rich' from a strategy name (learned names that contain the word work too). Unknown = textured."""
    n = str(name or "").lower()
    for k in DENSITY:
        if k in n: return k
    return "textured"

def _blocked(units, i):
    u = units[i] if i < len(units) else {}
    return u.get("speaker") == "SKEPTIC" and u.get("tag") in REACT       # the reaction effect owns that moment

def plan_sounds(shots, units, density="textured"):
    """Keep the Director's valid 'sound' choices, cap them by the episode's density, then fill up from what each line is about. Never two textured shots in a
    row and never on a Curious One reaction line. Returns a NEW list in which every shot has a 'sound' key (a kind or 'none')."""
    out = [dict(s) for s in shots]; n = len(out)
    target = max(2, int(round(DENSITY.get(density, DENSITY["textured"]) * n))) if n else 0
    chosen = []
    for i, s in enumerate(out):
        k = str(s.get("sound") or "").strip().lower(); s["sound"] = "none"
        if k in KINDS and not _blocked(units, i) and (not chosen or chosen[-1] != i - 1) and len(chosen) < target:
            s["sound"] = k; chosen.append(i)
    if len(chosen) < target:
        for i in range(n):
            if len(chosen) >= target: break
            if i in chosen or (i - 1) in chosen or (i + 1) in chosen or _blocked(units, i): continue
            k = guess((units[i] if i < len(units) else {}).get("text", "") + " " + str(out[i].get("prompt") or ""))
            if k: out[i]["sound"] = k; chosen.append(i)
    return out

def design(shots, units, total, rhythm=None, seed=""):
    """Everything the mixer needs, from the real narration clock: peaks (Kling shots and reveal lines, >= 20 s apart), hush spans ([close] lines),
    section changes, textures per shot, and the episode's music arc (from the rhythm blueprint)."""
    rhythm = rhythm or {}; total = float(total)
    pk = sorted({round(float(units[i]["start"]), 2) for i, s in enumerate(shots) if i < len(units) and (s.get("type") == "kling" or units[i].get("tag") == "reveal")})
    peaks = []
    for p in pk:
        if p >= 3.0 and (not peaks or p - peaks[-1] >= 20.0): peaks.append(p)
    hush = [(float(u["start"]), float(u.get("end", u["start"]))) for u in units if u.get("tag") == "close"][:6]
    sens = []
    for i, s in enumerate(shots):
        if i < len(units) and s.get("sound") in KINDS:
            b = float(units[i + 1]["start"]) if i + 1 < len(units) else total
            sens.append((s["sound"], float(units[i]["start"]), min(total, b)))
    rng = np.random.default_rng(_seed(f"{seed}|sections")); secs = []; t = float(rng.uniform(70, 100))
    while t < total - 30: secs.append(round(t, 1)); t += float(rng.uniform(75, 110))
    arc = rhythm.get("arc") if rhythm.get("arc") in ARCS else ARCS[_seed(seed) % len(ARCS)]
    return {"arc": arc, "peaks": peaks[:14], "hush": hush, "sections": secs, "sensory": sens}

def bed_gain(t, total, dz, seed=""):
    """Gain for the music bed at every sample time t (float array, seconds). Computed on a 50 Hz control grid, then interpolated."""
    total = max(1.0, float(total)); g_t = np.arange(0.0, total + 0.04, 0.02)
    arc = dz.get("arc", "still")
    if arc == "build": g = 0.55 + 0.45 * np.clip(g_t / total, 0, 1)
    elif arc == "waves": g = 0.75 + 0.25 * np.sin(2 * np.pi * g_t / 110.0 + (_seed(seed) % 628) / 100.0)
    elif arc == "pulse": g = 0.82 * (1 + 0.10 * np.sin(2 * np.pi * 0.9 * g_t))
    else: g = np.full_like(g_t, 0.8)
    rng = np.random.default_rng(_seed(f"{seed}|levels")); lvl = np.ones_like(g_t); prev = 1.0
    for s in dz.get("sections", []):
        new = float(rng.uniform(0.78, 1.18)); lvl = np.where(g_t >= s, np.interp(g_t, [s, s + 1.5], [prev, new]), lvl); prev = new
    g = g * lvl
    for a, b in dz.get("hush", []): g = g * np.where((g_t >= a - 0.3) & (g_t <= b + 0.3), 0.35, 1.0)
    for p in dz.get("peaks", []): g = g * np.interp(g_t, [p - 1.6, p - 1.2, p - 0.02, p + 0.25], [1.0, 0.06, 0.06, 1.0])
    return np.interp(t, g_t, g).astype(np.float32)

def _smooth(x, k):
    """Moving average in O(n) (a cumulative sum), used as a cheap low-pass filter."""
    k = max(1, int(k))
    if k <= 1 or len(x) <= k: return x.astype(np.float32)
    c = np.cumsum(np.concatenate([[0.0], x.astype(np.float64)])); y = (c[k:] - c[:-k]) / k; pad = len(x) - len(y)
    return np.concatenate([np.full(pad // 2, y[0]), y, np.full(pad - pad // 2, y[-1])]).astype(np.float32)

def texture(kind, sec, seed="", sr=48000):
    """One original texture, stereo (n, 2) float32, peak 1.0, 0.25 s fades. Close-miked feel: small sounds, wide but gentle panning."""
    m = max(2, int(sec * sr)); rng = np.random.default_rng(_seed(f"{seed}|{kind}")); t = np.arange(m, dtype=np.float32) / sr
    L = np.zeros(m, np.float32); R = np.zeros(m, np.float32)
    def put(at, s, pan):
        i0 = int(at * sr); e = min(m, i0 + len(s))
        if 0 <= i0 < m and e > i0: L[i0:e] += s[:e - i0] * (1 - pan); R[i0:e] += s[:e - i0] * pan
    if kind in ("drip", "rain"):
        rate = 1.1 if kind == "drip" else 16.0; at = float(rng.uniform(0.05, 0.4)); d = int(0.05 * sr); tt = np.arange(d) / sr
        while at < sec:
            f = float(rng.uniform(900, 1700)); s = (np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-tt * 60)) * tt) * np.exp(-tt * 70)).astype(np.float32)
            put(at, s * float(rng.uniform(0.4, 1.0)), float(rng.uniform(0.2, 0.8))); at += float(rng.exponential(1.0 / rate))
        if kind == "rain":
            nz = rng.standard_normal(m).astype(np.float32); hp = nz - _smooth(nz, 6); L += hp * 0.08; R += np.roll(hp, 397) * 0.08
    elif kind in ("crackle", "fizz"):
        rate = 22.0 if kind == "crackle" else 150.0; d = int((0.012 if kind == "crackle" else 0.004) * sr)
        for at in rng.uniform(0, sec, int(rate * sec) + 1):
            s = (rng.standard_normal(d) * np.exp(-np.arange(d) / max(1.0, d / 4))).astype(np.float32)
            put(float(at), s * float(rng.uniform(0.2, 1.0)), float(rng.uniform(0.1, 0.9)))
        if kind == "crackle":
            low = _smooth(rng.standard_normal(m).astype(np.float32), 400) * 4; L += low * 0.3; R += low * 0.3
    elif kind == "wind":
        lfo = (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t + float(rng.uniform(0, 6.28)))).astype(np.float32)
        L = _smooth(rng.standard_normal(m).astype(np.float32), 120) * 8 * lfo; R = _smooth(rng.standard_normal(m).astype(np.float32), 120) * 8 * lfo
    elif kind == "heartbeat":
        per = 60.0 / float(rng.uniform(58, 72)); at = 0.2; d = int(0.1 * sr); tt = np.arange(d) / sr
        lub = (np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 38)).astype(np.float32); dub = (np.sin(2 * np.pi * 44 * tt) * np.exp(-tt * 45)).astype(np.float32) * 0.7
        while at < sec: put(at, lub, 0.5); put(at + 0.28, dub, 0.5); at += per
    elif kind == "hum":
        f = float(rng.choice([55.0, 61.7, 65.4])); trem = (0.85 + 0.15 * np.sin(2 * np.pi * 0.3 * t)).astype(np.float32)
        L = ((0.6 * np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.003 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)) * trem).astype(np.float32)
        R = ((0.6 * np.sin(2 * np.pi * 1.002 * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3.01 * f * t)) * trem).astype(np.float32)
    elif kind == "rumble":
        low = _smooth(rng.standard_normal(m).astype(np.float32), 300) * 14 + (0.5 * np.sin(2 * np.pi * 31 * t)).astype(np.float32); L = low.copy(); R = low.copy()
    elif kind == "tick":
        d = int(0.006 * sr); tt = np.arange(d) / sr; at = 0.1; k = 0
        while at < sec:
            f = 3200 if k % 2 == 0 else 2600; put(at, (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 900)).astype(np.float32), 0.3 if k % 2 == 0 else 0.7); at += 1.0; k += 1
    elif kind == "glass":
        d = int(0.9 * sr); tt = np.arange(d) / sr; at = float(rng.uniform(0.1, 0.6))
        while at < sec:
            f = float(rng.uniform(1800, 3200))
            s = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) + 0.5 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 9) + 0.25 * np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 14)).astype(np.float32)
            put(at, s, float(rng.uniform(0.2, 0.8))); at += float(rng.exponential(1.8))
    else: return np.zeros((m, 2), np.float32)
    out = np.stack([L, R], 1); pk = float(np.abs(out).max())
    if pk > 1e-9: out /= pk
    f = min(int(0.25 * sr), m // 3)
    if f > 1: ramp = np.linspace(0, 1, f, dtype=np.float32)[:, None]; out[:f] *= ramp; out[-f:] *= ramp[::-1]
    return out.astype(np.float32)

# =====================================================================================================================================
# v8.10 immersive layers (SOUND_IMMERSIVE_ON; all code-generated = original, free, no licence risk): ambient beds per scene, close-mic textures under key
# lines, tactile ASMR-style foley at key moments, the impact recipe, a stereo Doppler pass for POV rushes. The voice always stays on top (the mixer ducks
# every layer under it) and the master is loudness-normalised as before.
# =====================================================================================================================================
AMBIENCE = ("wind", "hum", "rumble", "rain", "crackle", "drip")
FOLEY = ("creak", "fabric", "tap")
# v11 (K161) sound worlds: each location has its own bed; story events get their own sounds (research: voice changes keep pulling attention,
# repeated identical effects stop working -> every use is a fresh variant; ASMR textures only as quiet touches, never in the first 30 s)
WORLD_AMB = {"lab": "crackle", "office": "rain", "court": "hum", "case": "wind"}
SPEAKER_WORLD = {"DIRECTOR": "office", "VALE": "office", "SKEPTIC": "lab", "GRIMM": "lab", "JUDGE": "court", "ROSA": "court", "NANA": "court",
                 "WITNESS": "case", "ARCHIVIST": "case"}
KIND_GAIN = {"paper": 0.45, "gavel": 1.15, "fizzle": 0.8}
AMB_LEVEL = 0.022          # a low-level bed: felt more than heard
CLOSE_LEVEL = 0.03
FOLEY_LEVEL = 0.06

def _ambience_of(text):
    k = guess(text)
    return k if k in AMBIENCE else None

def immersive(shots, units, total, seed=""):
    """Design additions: ambience [(kind, a, b)] per scene (>= 25 s, a scene changes when what we see changes), close [(kind, a, b)] under [close] / whisper /
    hushed lines, foley [(kind, t)] at reveals and POV moments (>= 20 s apart, at most 8), impacts [t] (the impact recipe also shapes the bed)."""
    total = float(total); n = min(len(shots), len(units)); rng = np.random.default_rng(_seed(f"{seed}|amb"))
    amb, cur, start = [], None, 0.0
    for i in range(n):
        k = _ambience_of(str(units[i].get("text", "")) + " " + str(shots[i].get("prompt") or "")) or cur or AMBIENCE[int(rng.integers(0, 2))]
        t = float(units[i]["start"])
        if cur is None: cur, start = k, 0.0
        elif k != cur and t - start >= 25.0: amb.append((cur, start, t)); cur, start = k, t
    if cur: amb.append((cur, start, total))
    close = []
    for u in units:
        c = set(u.get("curve") or [])
        if u.get("tag") == "close" or c & {"whisper", "hushed"}:
            close.append(("tick" if len(close) % 2 else "drip", float(u["start"]), float(u.get("end", u["start"])) + 0.4))
    foley, last = [], -99.0
    for i in range(n):
        t = float(units[i]["start"])
        if (units[i].get("tag") == "reveal" or shots[i].get("pov") or shots[i].get("pov_fx")) and t - last >= 20.0 and len(foley) < 8:
            foley.append((FOLEY[len(foley) % len(FOLEY)], max(0.0, t - 0.15))); last = t
    impacts = [float(units[i]["start"]) for i in range(n) if shots[i].get("pov_fx") == "impact_shake"][:3]
    if S("SOUND_WORLDS_ON", bool):
        amb = worlds(units, total, seed) or amb
        foley = sorted(foley + story_events(units), key=lambda x: x[1])
    return {"ambience": amb, "close": close[:8], "foley": foley, "impacts": impacts}

def _world_of(u):
    sp = str(u.get("speaker") or "").upper()
    return next((w for k, w in SPEAKER_WORLD.items() if k in sp), None)

def worlds(units, total, seed=""):
    """v11: the bed follows WHERE we are (the speaking character's world); a world must last >= SOUND_WORLD_MIN_S before the bed changes."""
    amb, cur, start = [], None, 0.0
    for u in units:
        w = _world_of(u)
        if not w: continue
        k = WORLD_AMB[w]; t = float(u.get("start", 0) or 0)
        if cur is None: cur, start = k, 0.0
        elif k != cur and t - start >= S("SOUND_WORLD_MIN_S", float): amb.append((cur, start, t)); cur, start = k, t
    if cur: amb.append((cur, start, float(total)))
    return amb

def story_events(units):
    """v11: sounds tied to the story: a paper crinkle under each Exhibit (quiet, never in the first 30 s), the gavel on Nana's verdict line,
    a fizzle after Grimm's Prototype. Each kind at least 6 s apart, at most SOUND_EVENTS_MAX in total."""
    out, last = [], {}
    for u in units:
        t = float(u.get("start", 0) or 0); txt = str(u.get("text", ""))
        for kind, pat, dt_, first_ok in (("paper", "exhibit", 0.0, 30.0), ("gavel", "here's what's true", -0.1, 0.0), ("fizzle", "prototype", 1.2, 0.0)):
            if pat in txt.lower().replace("\u2019", "'") and t >= first_ok and t - last.get(kind, -99) >= 6.0:
                out.append((kind, max(0.0, t + dt_))); last[kind] = t
    return out[: S("SOUND_EVENTS_MAX", int)]

def impact_gain(t, impacts):
    """Bed + texture gain around each impact: 1-2 beats of near-silence before it, a deep hole after it (ringing time), a slow recovery."""
    g = np.ones_like(t, dtype=np.float32)
    for p in impacts:
        g = g * np.interp(t, [p - 1.3, p - 1.0, p - 0.02, p + 0.3, p + 4.0, p + 7.0], [1.0, 0.04, 0.04, 0.2, 0.25, 1.0]).astype(np.float32)
    return g

def foley(kind, seed="", sr=48000):
    """Tactile, close sounds (stereo, peak 1): a wooden/metal creak, a fabric brush, a fingertip tap."""
    rng = np.random.default_rng(_seed(f"{seed}|{kind}"))
    if kind == "creak":
        m = int(0.9 * sr); t = np.arange(m) / sr; f = 140 + 60 * np.sin(2 * np.pi * 0.9 * t) + rng.uniform(-10, 10)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / sr)) * 0.3 + rng.standard_normal(m) * 0.15
        x = x * (np.sin(np.pi * t / t[-1]) ** 2); x = _smooth(x.astype(np.float32), 3)
    elif kind == "fabric":
        m = int(0.6 * sr); t = np.arange(m) / sr; nz = rng.standard_normal(m).astype(np.float32)
        x = (nz - _smooth(nz, 8)) * (np.sin(np.pi * t / t[-1]) ** 1.5)
    elif kind == "gavel":                                    # v11: wood knock + low body, slight variation every use
        m = int(0.7 * sr); t = np.arange(m) / sr; f0 = float(rng.uniform(180, 230))
        x = (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 18) * 0.8 + np.sin(2 * np.pi * f0 * 3.1 * t) * np.exp(-t * 45) * 0.5
             + rng.standard_normal(m) * np.exp(-t * 160) * 0.6)
    elif kind == "paper":                                    # v11: an ASMR-light paper crinkle (several tiny bursts)
        m = int(0.8 * sr); x = np.zeros(m, np.float32)
        for _ in range(int(rng.integers(5, 9))):
            a = int(rng.uniform(0, 0.7) * sr); L = int(rng.uniform(0.01, 0.04) * sr); nz = rng.standard_normal(L).astype(np.float32)
            x[a:a + L] += (nz - _smooth(nz, 3))[: max(0, min(L, m - a))] * float(rng.uniform(0.4, 1.0))
    elif kind == "fizzle":                                   # v11: Grimm's device dying: a falling tone + crackles
        m = int(1.1 * sr); t = np.arange(m) / sr; f = 900 * np.exp(-t * 2.2) + float(rng.uniform(-40, 40))
        x = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 2.5) * 0.6 + (rng.random(m) < 0.004) * rng.standard_normal(m) * 0.9
    else:
        m = int(0.18 * sr); t = np.arange(m) / sr
        x = (np.sin(2 * np.pi * 420 * t) * np.exp(-t * 60) + rng.standard_normal(m) * np.exp(-t * 220) * 0.4)
    x = x.astype(np.float32); x /= (np.abs(x).max() + 1e-9); pan = float(rng.uniform(0.3, 0.7))
    return np.stack([x * (1 - pan) * 2, x * pan * 2], 1).astype(np.float32) / 2

def impact_layers(seed="", sr=48000, pal=1.0):
    """The impact recipe's sounds, stereo, starting AT the impact: boom + sub drop, then high ringing + a muffled heartbeat + one breath (about 4.5 s).
    The rumble + riser before it and the near-silence are made by the mixer (impact_run_up / impact_gain)."""
    rng = np.random.default_rng(_seed(f"{seed}|impact")); m = int(5.0 * sr); t = np.arange(m) / sr
    boom = np.sin(2 * np.pi * (60 * pal * np.exp(-t * 1.1) + 24) * t) * np.exp(-t * 1.3) * 0.75
    ring = np.sin(2 * np.pi * float(rng.uniform(6800, 7600)) * t) * np.exp(-((t - 0.15).clip(0)) * 0.9) * (t > 0.15) * 0.035
    hb = texture("heartbeat", 5.0, f"{seed}imp", sr)[:m, 0]; hb = _smooth(hb, 40) * 2.2 * np.interp(t, [0, 0.3, 3.5, 5.0], [0, 0.5, 0.35, 0])
    br = rng.standard_normal(m).astype(np.float32); br = (br - _smooth(br, 30)) * np.interp(t, [2.4, 2.8, 3.4, 3.6], [0, 0.10, 0.06, 0], left=0, right=0)
    L = (boom + ring + hb + br).astype(np.float32); R = (boom + ring * 0.8 + hb + np.roll(br, 120)).astype(np.float32)
    return np.stack([L, R], 1)

def impact_run_up(sec=3.0, seed="", sr=48000):
    """Rising rumble + riser for the seconds BEFORE the near-silence (stereo, ends at full level; the mixer places its end 1 s before the impact)."""
    rng = np.random.default_rng(_seed(f"{seed}|runup")); m = int(sec * sr); t = np.arange(m) / sr
    rum = _smooth(rng.standard_normal(m).astype(np.float32), 300) * 10 * (t / sec) ** 1.5
    ris = np.sin(2 * np.pi * (180 + 520 * (t / sec) ** 2) * t) * (t / sec) ** 2.5 * 0.25
    x = (rum + ris).astype(np.float32); x /= (np.abs(x).max() + 1e-9)
    return np.stack([x, x * 0.96], 1)

def doppler(sec, seed="", sr=48000):
    """A whoosh that flies PAST you: noise whose centre pitch falls as it passes, panned left -> right, loudest at the pass (stereo, peak 1)."""
    rng = np.random.default_rng(_seed(f"{seed}|dop")); m = max(int(0.4 * sr), int(sec * sr)); t = np.arange(m) / m
    nz = rng.standard_normal(m).astype(np.float32); hi = nz - _smooth(nz, 3); lo = _smooth(nz, 12)
    mixk = np.clip(t * 1.4 - 0.2, 0, 1).astype(np.float32)                    # bright on approach, darker after the pass (the pitch drop)
    x = (hi * (1 - mixk) + lo * 3 * mixk) * (np.exp(-((t - 0.6) / 0.22) ** 2)).astype(np.float32)
    pan = np.clip(t * 1.2 - 0.1, 0, 1).astype(np.float32)
    out = np.stack([x * (1 - pan), x * pan], 1); out /= (np.abs(out).max() + 1e-9)
    return out.astype(np.float32)

# ---------------------------------------------------------------- v12 V2d-b: the sound under a Short, from its first frame
SHORT_BED_LEVEL = 0.20                       # the place's own sound under a Short, before the voice ducks it
SHORT_HITS = ("thump", "tick", "knock")      # the colours a beat change may sound in: never the same twice in a row (a sound heard again and again is no longer heard)
ONSET_DB = -45.0                             # the level (dBFS, over 10 ms) from which a file counts as sounding
PHONE_HZ = 400                               # a Short is heard on a phone: its small speaker plays next to nothing under about this (measured reviews: -10 dB near 450 Hz, flat from 230-700 Hz up)
LOW_KINDS = ("rumble", "hum", "heartbeat")   # textures that live under PHONE_HZ: under a Short they get more of the place's air, or a phone would play silence

def short_bed(total, beats, text, seed, path, sr=48000):
    """THE SOUND UNDER A SHORT (v12 V2d-b; before: a drone that rose out of silence over a second and a half). The PLACE'S OWN SOUND from the first
    sample - a texture chosen from the words of the first picture (`guess`; nothing obvious = one of three, by the Short's id) at its full level,
    no fade-in; ONE soft hit on the first frame; a hit on every beat change in rotating colours; a short tail. Every Short's colours follow its id,
    so no two Shorts sound alike. Peak-normalised. Returns (path, the texture's kind)."""
    import soundfile as sf
    n = max(2, int(float(total) * sr)); rng = np.random.default_rng(_seed(f"{seed}|short")); kind = guess(text) or ("rumble", "hum", "wind")[_seed(seed) % 3]
    head = int(0.3 * sr); tex = texture(kind, float(total) + 0.6, f"{seed}|bed", sr)[head:head + n]      # cut behind the texture's own fade-in: the place sounds at once
    out = np.zeros((n, 2), np.float32); out[:len(tex)] += tex * SHORT_BED_LEVEL
    air = rng.standard_normal(n).astype(np.float32); out += ((_smooth(air, 8) - _smooth(air, 120)) * (0.16 if kind in LOW_KINDS else 0.10))[:, None]      # the air of a place: noise in the band a phone plays, never digital silence
    pal = float(rng.uniform(0.85, 1.2))
    def hit(at, colour, level):
        m = int(0.45 * sr); tt = np.arange(m) / sr
        if colour == "thump": s = np.sin(2 * np.pi * (70 * pal * np.exp(-tt * 9) + 38 * pal) * tt) * np.exp(-tt * 9)
        elif colour == "tick": s = np.sin(2 * np.pi * 1900 * pal * tt) * np.exp(-tt * 70) * 0.5 + np.sin(2 * np.pi * 240 * pal * tt) * np.exp(-tt * 22) * 0.6
        else: s = np.sin(2 * np.pi * 150 * pal * tt) * np.exp(-tt * 28) + rng.standard_normal(m) * np.exp(-tt * 120) * 0.25
        i0 = int(at * sr); e = min(n, i0 + m)
        if e > i0: out[i0:e] += (s[:e - i0] * level).astype(np.float32)[:, None]
    hit(0.0, "thump", 0.5); hit(0.0, "knock", 0.45)              # the first frame SOUNDS: a body for good speakers AND a knock a phone can play (a low thump alone is silence on a phone)
    at = 0.0; last = "thump"
    for b in list(beats or [])[:-1]:
        at += float(b); colour = [c for c in SHORT_HITS if c != last][int(rng.integers(0, len(SHORT_HITS) - 1))]; hit(at, colour, 0.4); last = colour
    ramp = max(1, int(0.004 * sr)); out[:ramp] *= np.linspace(0, 1, ramp, dtype=np.float32)[:, None]      # four milliseconds against a click, nothing more
    tail = min(n, int(0.25 * sr)); out[-tail:] *= np.linspace(1, 0.2, tail, dtype=np.float32)[:, None]
    out = out / (float(np.max(np.abs(out))) + 1e-9) * 0.89
    sf.write(path, out.astype(np.float32), sr); return path, kind

def first_second(path, sr=16000, phone=True):
    """What a finished file SOUNDS like when it starts, AS A PHONE PLAYS IT (everything under PHONE_HZ filtered away; phone=False = the whole signal):
    {onset_s (the first moment its level passes ONSET_DB; None = never inside a second and a half), db_200 (the mean level of its first fifth of a
    second, dBFS), db_1000 (of its first second), peak_db (of the whole signal)}. Measured on the file itself (ffmpeg decodes it; no model)."""
    import math, subprocess
    def read(af): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-t", "1.5", "-i", path, "-vn", "-ac", "1", "-ar", str(sr)] + af + ["-f", "s16le", "-"], capture_output=True, timeout=120).stdout, "<i2").astype(np.float64) / 32768.0
    full = read([]); raw = None
    x = read(["-af", f"highpass=f={PHONE_HZ},highpass=f={PHONE_HZ}"]) if phone else full
    def db(v): return round(20 * math.log10(max(1e-6, float(np.sqrt(np.mean(v ** 2))))), 1) if len(v) else -120.0
    if len(x) < sr // 20: return {"onset_s": None, "db_200": -120.0, "db_1000": -120.0, "peak_db": -120.0}
    hop = sr // 100; on = None
    for k in range(0, len(x) - hop, hop):
        if db(x[k:k + hop]) >= ONSET_DB: on = round(k / sr, 3); break
    return {"onset_s": on, "db_200": db(x[:sr // 5]), "db_1000": db(x[:sr]), "peak_db": round(20 * math.log10(max(1e-6, float(np.max(np.abs(full))) if len(full) else 1e-6)), 1)}
