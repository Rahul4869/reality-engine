"""whatifs/voiceq.py v9.2 (K107) - designed character voices and voice loudness.

DESIGNED VOICES: Gemini Voice Design voices are used BY ID ("voice_...") in speechConfig.voiceConfig.voice (Google's TTS + Voice design docs, Nov 2026).
The Characters tab's gvoice cell may hold that ID or the DISPLAY NAME from AI Studio (e.g. "Dr Grimm 3"); the name is resolved to its ID with the
voices list endpoint (GET v1beta/voices). A designed voice is used only when it is listed AND passed Voice_Check (synth_ok); otherwise the closest
PREBUILT voice by descriptors is used (v9.1 substitution), and only then Kokoro. Every substitution is logged.

LOUDNESS: every voiced line is levelled per character to one RMS target (VOICE_TARGET_RMS_DB, consistent between characters), then -VOICE_HEADROOM_DB
(about 3 dB) and a look-ahead peak limiter at VOICE_PEAK_DBFS (<= -1 dBFS). Deterministic, code only."""
from __future__ import annotations
import re
import numpy as np
from whatifs.core import S, log

DESIGNED = {"GRIMM": "Dr Grimm 3", "VALE": "Inspector Vale 1", "ROSA": "Nana Rosa 1", "ARCHIVIST": "The Archivist 2"}      # the owner's AI Studio names
PREBUILT_WANT = {"DIRECTOR": ("m", ["knowledgeable", "clear", "informative", "smooth", "even"]), "SKEPTIC": ("m", ["gravelly", "forward", "excitable", "lively"])}

def _norm(s): return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()

def resolve_designed(name_or_id, listing=None):
    """'voice_...' -> itself; a display name -> the id of the custom voice with that display name (case / punctuation ignored); else ''."""
    v = str(name_or_id or "").strip()
    if not v: return ""
    if v.startswith(("voice_", "voicekey_")): return v
    try:
        if listing is None:
            from whatifs.tts_gemini import list_voices
            listing = list_voices()
    except Exception as e:
        log(f"voice list unavailable ({str(e)[:120]}) - designed voice '{v}' not resolved", "WARN"); return ""
    n = _norm(v)
    for x in listing or []:
        if _norm(x.get("display_name")) == n and str(x.get("id", "")).startswith(("voice_", "voicekey_")): return x["id"]
    return ""

def usable(voice_id):
    """True when Voice_Check says this voice synthesised a test line."""
    try:
        from whatifs.core import store
        return any(r.get("voice") == voice_id and str(r.get("synth_ok", "")).strip().upper() in ("TRUE", "1", "YES", "OK") for r in store().rows("Voice_Check"))
    except Exception: return False

def voice_for(speaker, gvoice, taken, listing=None):
    """(voice, how) for a character: 'designed' | 'prebuilt' (wanted prebuilt) | 'substitute' (closest prebuilt) | ('', 'kokoro')."""
    from whatifs import v91 as V91
    vid = resolve_designed(gvoice, listing) if gvoice and not str(gvoice).strip() in V91.VOICE_TRAITS else ""
    if vid and vid not in taken and usable(vid): return vid, "designed"
    if vid or (gvoice and str(gvoice).startswith("voice_")): log(f"{speaker}: designed voice '{gvoice}' not usable (not listed or failed Voice_Check) - closest prebuilt voice instead", "WARN")
    want = str(gvoice).strip() if str(gvoice).strip() in V91.VOICE_TRAITS else ""
    if speaker in PREBUILT_WANT and speaker not in V91.WANT: V91.WANT[speaker] = PREBUILT_WANT[speaker]
    v, how = V91.resolve_voice(speaker, want, taken)
    if not v and DEFAULT_PREBUILT.get(speaker) and DEFAULT_PREBUILT[speaker] not in taken:      # never let one character push the narration to Kokoro
        log(f"{speaker}: no checked voice available - the v9 default prebuilt voice {DEFAULT_PREBUILT[speaker]} is used", "WARN")
        return DEFAULT_PREBUILT[speaker], "default"
    return v, ("prebuilt" if how == "wanted" else how)

DEFAULT_PREBUILT = {"JUDGE": "Gacrux", "WITNESS": "Enceladus"}     # Vale / Grimm keep their Cast voices when nothing better is usable

# ---------------------------------------------------------------- loudness
def db(x): return 20 * np.log10(max(1e-9, float(x)))

def stats(a):
    a = np.asarray(a, np.float32)
    if not a.size: return {"peak_db": -120.0, "rms_db": -120.0}
    return {"peak_db": round(db(np.max(np.abs(a))), 2), "rms_db": round(db(np.sqrt(np.mean(a.astype(np.float64) ** 2))), 2)}

def limiter(a, sr, ceiling_db=-1.0, look_ms=5.0, release_ms=60.0):
    """Look-ahead peak limiter: gain never lets |x| exceed the ceiling; smooth release. Deterministic."""
    a = np.asarray(a, np.float32)
    if not a.size: return a
    c = 10 ** (ceiling_db / 20); need = np.minimum(1.0, c / np.maximum(np.abs(a), 1e-9))
    la = max(1, int(sr * look_ms / 1000)); rel = np.exp(-1.0 / max(1, sr * release_ms / 1000))
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.concatenate([need, np.ones(la - 1, np.float32)]); g = sliding_window_view(pad, la).min(axis=1)      # look ahead: the lowest gain coming up
    out = np.empty_like(g); cur = 1.0
    for i in range(len(g)):
        cur = g[i] if g[i] < cur else g[i] + (cur - g[i]) * rel
        out[i] = cur
    return np.clip(a * out, -c, c).astype(np.float32)

def level(a, sr):
    """One voiced line: RMS to VOICE_TARGET_RMS_DB (gain between -24 and +12 dB), minus VOICE_HEADROOM_DB, then the limiter at VOICE_PEAK_DBFS."""
    a = np.asarray(a, np.float32)
    if not a.size or not S("VOICE_LEVEL_ON", bool): return a
    st = stats(a)
    if st["rms_db"] < -70: return a
    g = max(-24.0, min(12.0, S("VOICE_TARGET_RMS_DB", float) - st["rms_db"])) - S("VOICE_HEADROOM_DB", float)      # cut up to 24 dB, boost up to 12
    return limiter(a * (10 ** (g / 20)), sr, S("VOICE_PEAK_DBFS", float))
