"""whatifs/v91.py v9.1 - the switchboard for every v9.1 feature (K103):
- on(flag): a v9.1 feature runs only when its own flag is TRUE AND V91_SAFE_MODE is FALSE (safe mode = exactly v9, in one cell),
- guard(feature, episode): the FAIL-SAFE wrapper. An exception disables ONLY that feature for that episode (WARN in Run_Log + a line in the episode
  notes) and never blocks scheduling, rendering or upload. A disabled feature stays off for the rest of the episode (no retry loop).
- the Gemini voice substitution by descriptors (risk item of the v9 report)."""
from __future__ import annotations
import contextlib
from whatifs.core import S, log, JOB

_OFF = {}          # episode -> {feature: reason}

def safe_mode(): return S("V91_SAFE_MODE", bool)

def on(flag, episode=None):
    if safe_mode(): return False
    ep = episode or JOB.get("episode") or ""
    if flag in _OFF.get(ep, {}): return False
    return S(flag, bool)

def disabled(episode=None): return dict(_OFF.get(episode or JOB.get("episode") or "", {}))

@contextlib.contextmanager
def guard(flag, episode=None):
    """with guard("ATMOSPHERE_ON", ep): ...   - an exception switches that feature off for this episode and is swallowed."""
    ep = episode or JOB.get("episode") or ""
    try:
        yield
    except Exception as e:
        _OFF.setdefault(ep, {})[flag] = str(e)[:160]
        log(f"v9.1 feature {flag} failed and is OFF for this episode ({str(e)[:160]}) - the video continues without it", "WARN", ep or None)
        try:
            from whatifs.core import note_degraded
            note_degraded(f"{flag} off: {str(e)[:80]}")
        except Exception: pass

def call(flag, fn, *a, default=None, episode=None, **k):
    """Run fn only when the flag is on; any exception = the feature is off for the episode and `default` is returned."""
    if not on(flag, episode): return default
    out = default
    with guard(flag, episode):
        out = fn(*a, **k)
    return out

# ---------------------------------------------------------------- Gemini voice substitution (descriptors)
# Google's published one-word styles for the prebuilt voices; the gender column is our ASSUMPTION from listening notes (not published by Google).
VOICE_TRAITS = {"Zephyr": ("f", "bright"), "Puck": ("m", "upbeat"), "Charon": ("m", "informative"), "Kore": ("f", "firm"), "Fenrir": ("m", "excitable"),
                "Leda": ("f", "youthful"), "Orus": ("m", "firm"), "Aoede": ("f", "breezy"), "Callirrhoe": ("f", "easy-going"), "Autonoe": ("f", "bright"),
                "Enceladus": ("m", "breathy"), "Iapetus": ("m", "clear"), "Umbriel": ("m", "easy-going"), "Algieba": ("m", "smooth"), "Despina": ("f", "smooth"),
                "Erinome": ("f", "clear"), "Algenib": ("m", "gravelly"), "Rasalgethi": ("m", "informative"), "Laomedeia": ("f", "upbeat"), "Achernar": ("f", "soft"),
                "Alnilam": ("m", "firm"), "Schedar": ("m", "even"), "Gacrux": ("f", "mature"), "Pulcherrima": ("f", "forward"), "Achird": ("m", "friendly"),
                "Zubenelgenubi": ("m", "casual"), "Vindemiatrix": ("f", "gentle"), "Sadachbia": ("m", "lively"), "Sadaltager": ("m", "knowledgeable"), "Sulafat": ("f", "warm")}
WANT = {"JUDGE": ("f", ["mature", "warm", "gentle", "soft", "even"]), "WITNESS": ("m", ["breathy", "soft", "gravelly", "even", "smooth"])}

def available_voices():
    """Voices the key can really use: Voice_Check rows with synth_ok TRUE; empty when the check has not run (then nothing is assumed available)."""
    try:
        from whatifs.core import store
        return {r["voice"] for r in store().rows("Voice_Check") if str(r.get("synth_ok", "")).strip().upper() in ("TRUE", "1", "YES", "OK")}
    except Exception: return set()

def resolve_voice(speaker, wanted, taken, avail=None):
    """(voice, how): 'wanted' when it is available and free; else the closest available voice by gender + style order; else ('', 'kokoro')."""
    avail = available_voices() if avail is None else set(avail)
    if wanted and wanted in avail and wanted not in taken: return wanted, "wanted"
    g, styles = WANT.get(speaker, ("", []))
    best, score = "", -1
    for v in sorted(avail - set(taken)):
        tg, st = VOICE_TRAITS.get(v, ("", ""))
        s = (3 if tg == g else 0) + (len(styles) - styles.index(st) if st in styles else 0)
        if s > score: best, score = v, s
    if best and score >= 3:
        log(f"{speaker}: Gemini voice '{wanted or '-'}' not usable - substituted '{best}' ({VOICE_TRAITS.get(best, ('?', '?'))[1]}) by descriptors", "WARN")
        return best, "substitute"
    return "", "kokoro"
