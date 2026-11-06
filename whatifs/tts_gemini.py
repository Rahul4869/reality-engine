"""whatifs/tts_gemini.py v8.10 - Gemini TTS narration (Settings TTS_ENGINE=gemini; kokoro = v8.9 voices).

How it works (API facts from Google's TTS guide, Oct 2026; the model NAME is discovered live, K11):
- POST v1beta/interactions, one request per CHUNK of consecutive lines (<= TTS_CHUNK_WORDS words, about 90 s): every line is its own turn with
  speech_metadata {speaker, style}. Two speakers per request work with PREBUILT voices only; a designed/replicated voice ("voice_...") is voiced one
  speaker-run at a time. The transcript is read VERBATIM, so our tags never go into the text: delivery goes into the turn's style, moments into
  inline vocal tags (<breath>, <gasp>, <laugh>, <sigh>, <short pause>...).
- Unary replies are WAV (24 kHz mono 16-bit). Gemini returns NO word timings, so this module MEASURES them:
  1) each line's start/end inside a chunk comes from the pauses actually found in the audio, matched to the expected line lengths (dynamic programming);
     if the match is not convincing the chunk is re-voiced ONE LINE PER REQUEST (then every line's duration is measured exactly);
  2) words inside a line: CTC forced alignment (wav2vec2 via transformers, free, CPU) when it loads (TTS_ALIGN=auto|ctc), else voiced-energy + syllable
     timing that snaps word edges to the line's own internal pauses (TTS_ALIGN=energy).
  The narration timeline (the master clock for every visual) is then built from these measured pieces exactly like the Kokoro path, so cuts stay
  frame-accurate; final QC still checks the audio against the clock (QC_SYNC_TOL_SEC).
- Rate limits: at most TTS_RPM requests a minute from this job; 429 / 5xx wait (Retry-After, else growing back-off) up to TTS_MAX_RETRIES.
- Cost: every request is logged in Cost_Log (item gemini_tts, provider google) from the usage Google returns, else from the audio length (25 tokens a second).
Fake mode (WI_FAKE=1): a local stand-in returns a WAV with one tone per turn and real pauses, so segmentation and alignment are exercised offline."""
from __future__ import annotations
import base64, io, json, re, time, wave, datetime as dt
import numpy as np
import requests
from whatifs.core import S, env, log, cost, FAKE, scrub, now_utc, iso, store, safe_append

SR = 24000
GEM = "https://generativelanguage.googleapis.com/v1beta/"
TOK_PER_SEC = 25.0
_last_req = [0.0]

class TTSFailed(RuntimeError):
    """Gemini TTS could not voice the narration (after retries and the line-by-line fallback)."""

# ---------------------------------------------------------------- model + price
def tts_model():
    from whatifs.models import model
    m = None
    try: m = model("gem_tts")
    except Exception: m = None
    if not m and not FAKE:
        try:
            from whatifs.models import discover_models
            m = discover_models().get("gem_tts")
        except Exception as e: log(f"TTS model discovery failed: {scrub(e)}", "WARN")
    return m or ("fake-tts" if FAKE else None)

def pick_tts(names):
    """From the live model list: the newest Flash TTS model (not Lite, not preview when a stable one exists). Used by models.discover_models."""
    from whatifs.models import _vernum
    c = [n for n in names if "tts" in n and "flash" in n and "lite" not in n]
    stable = [n for n in c if "preview" not in n] or c
    stable.sort(key=_vernum, reverse=True)
    return stable[0] if stable else None

def price_out():
    return S("PRICE_GEM_TTS_OUT_2027", float) if now_utc().date() >= dt.date(2027, 1, 1) else S("PRICE_GEM_TTS_OUT", float)

def est_inr(seconds):
    """Rupees for this many seconds of narration (audio output dominates; input text is about 2 % of it)."""
    return seconds * TOK_PER_SEC * price_out() / 1e6 * S("USD_INR", float) * 1.03

# ---------------------------------------------------------------- text preparation
def _clean(text):
    t = re.sub(r"\{[^{}]*\}", " ", str(text)); t = re.sub(r"\[[^\[\]]*\]", " ", t); t = re.sub(r"<[^<>]*>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def style_for(unit, base_style=""):
    """Turn-level style: the cast member's style direction + our delivery tag + the writer's emotion curve. Short (long style text makes voices drift)."""
    from whatifs.data import TAG_STYLE, CURVE_WORDS
    tag = getattr(unit, "tag", "none") or "none"
    parts = [TAG_STYLE.get(tag, ("", ""))[0]]
    if S("EMOTION_CURVE_ON", bool): parts += [CURVE_WORDS[w] for w in (getattr(unit, "curve", None) or []) if w in CURVE_WORDS]
    s = ", ".join(dict.fromkeys(p for p in parts if p))
    if base_style and not s: s = base_style
    elif base_style: s = f"{s} ({base_style})"
    return s[:160]

def spoken_text(unit):
    """The verbatim transcript for one line: inline vocal events first (a breath before a reveal, a gasp), then the words. Pauses are made by our pacer."""
    from whatifs.data import TAG_STYLE, CURVE_EVENTS
    ev = [TAG_STYLE.get(getattr(unit, "tag", "none") or "none", ("", ""))[1]]
    if S("EMOTION_CURVE_ON", bool): ev += [CURVE_EVENTS[w] for w in (getattr(unit, "events", None) or []) if w in CURVE_EVENTS]
    ev = [e for e in dict.fromkeys(ev) if e]
    return (" ".join(ev) + " " + _clean(unit.text)).strip()

def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w: return 1 if re.search(r"\d", word) else 0
    n = len(re.findall(r"[aeiouy]+", w)); n -= 1 if w.endswith("e") and n > 1 and not w.endswith("le") else 0
    return max(1, n)

def _weight(text):
    ws = _clean(text).split()
    return sum(max(1, syllables(w)) + (3 * len(re.findall(r"\d", w)) // 2) for w in ws) or 1

def chunks(units, max_words=None):
    """Consecutive lines grouped into requests of <= max_words words, cut preferably at a paragraph. Returns [[unit indexes]]."""
    max_words = max_words or max(40, S("TTS_CHUNK_WORDS", int))
    out, cur, n = [], [], 0
    for i, u in enumerate(units):
        w = len(_clean(u.text).split())
        if cur and (n + w > max_words or (getattr(u, "new_para", False) and n >= max_words * 0.6)):
            out.append(cur); cur, n = [], 0
        cur.append(i); n += w
    if cur: out.append(cur)
    return out

# ---------------------------------------------------------------- audio helpers
def wav_bytes_to_array(b):
    if b[:4] == b"RIFF":
        with wave.open(io.BytesIO(b), "rb") as w:
            sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth(); raw = w.readframes(w.getnframes())
        a = np.frombuffer(raw, dtype="<i2" if sw == 2 else np.uint8).astype(np.float32)
        a = a / 32768.0 if sw == 2 else (a - 128) / 128.0
        if ch > 1: a = a.reshape(-1, ch).mean(1)
    else:
        sr = SR; a = np.frombuffer(b[: len(b) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0       # headerless L16, 24 kHz mono
    if sr != SR: a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
    return a.astype(np.float32)

def array_to_wav_bytes(a, sr=SR):
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype("<i2").tobytes())
    return bio.getvalue()

def _env_db(a, hop=0.01):
    h = int(hop * SR); m = len(a) // h
    if m == 0: return np.array([-120.0])
    rms = np.sqrt((a[: m * h].reshape(m, h).astype(np.float64) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms + 1e-9)

def silences(a, min_len=0.12, hop=0.01):
    """[(start_s, end_s)] of quiet runs (relative threshold: 32 dB under the loud part, never above -40 dBFS)."""
    d = _env_db(a, hop)
    if d.size == 0: return []
    thr = min(-40.0, float(np.percentile(d, 95)) - 32.0)
    q = d < thr; out = []; s = None
    for k, v in enumerate(list(q) + [False]):
        if v and s is None: s = k
        elif not v and s is not None:
            if (k - s) * hop >= min_len: out.append((s * hop, k * hop))
            s = None
    return out

def split_turns(a, weights, lead=0.0):
    """Cut one chunk's audio into len(weights) lines at the pauses actually present. Dynamic programming over the candidate pauses: each boundary should
    sit near its expected position (from the line weights) and prefer longer pauses. Returns [(start_s, end_s)] or None if the match is not convincing."""
    n = len(weights); dur = len(a) / SR
    if n == 1: return [(0.0, dur)]
    sil = [(s, e) for s, e in silences(a) if s > 0.05 and e < dur - 0.05]
    if len(sil) < n - 1: return None
    voiced = dur - sum(e - s for s, e in silences(a)); tot = float(sum(weights))
    exp = []; acc = 0.0; gaps = (dur - voiced) / max(1, n)
    for k in range(n - 1): acc += weights[k] / tot * voiced + gaps; exp.append(acc)
    C = [((s + e) / 2, e - s) for s, e in sil]; m = len(C); INF = 1e18
    cost_ = [[INF] * m for _ in range(n - 1)]; back = [[-1] * m for _ in range(n - 1)]
    def c(k, j): return abs(C[j][0] - exp[k]) / max(0.4, dur / n) - 1.5 * min(0.6, C[j][1])
    for j in range(m): cost_[0][j] = c(0, j)
    for k in range(1, n - 1):
        best, bj = INF, -1
        for j in range(m):
            if j - 1 >= 0 and cost_[k - 1][j - 1] < best: best, bj = cost_[k - 1][j - 1], j - 1
            if bj >= 0: cost_[k][j] = best + c(k, j); back[k][j] = bj
    j = min(range(m), key=lambda x: cost_[n - 2][x])
    if cost_[n - 2][j] >= INF / 2: return None
    picks = [j]
    for k in range(n - 2, 0, -1): j = back[k][j]; picks.append(j)
    cuts = [C[x][0] for x in reversed(picks)]
    b = [0.0] + cuts + [dur]; segs = [(b[k], b[k + 1]) for k in range(n)]
    for k, (s, e) in enumerate(segs):            # plausibility: every line is long enough and roughly as long as its words say
        want = weights[k] / tot * voiced
        if e - s < 0.25 or not (0.4 <= (e - s) / max(0.2, want + gaps) <= 2.4): return None
    return segs

# ---------------------------------------------------------------- word timings
_CTC = {"m": None, "tried": False}
def _ctc_load():
    if _CTC["tried"]: return _CTC["m"]
    _CTC["tried"] = True
    try:
        import torch
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        name = "facebook/wav2vec2-base-960h"           # free English CTC acoustic model (Apache-2.0), cached by the workflows' Hugging Face cache
        _CTC["m"] = (torch, Wav2Vec2Processor.from_pretrained(name), Wav2Vec2ForCTC.from_pretrained(name).eval())
    except Exception as e:
        log(f"word aligner not available ({scrub(e)[:120]}) - energy + syllable timing is used", "WARN")
    return _CTC["m"]

def _ctc_words(a, words):
    m = _ctc_load()
    if not m or not words: return None
    torch, proc, net = m
    x = np.interp(np.arange(int(len(a) * 16000 / SR)) * SR / 16000, np.arange(len(a)), a).astype(np.float32)
    with torch.no_grad():
        lp = torch.log_softmax(net(proc(x, sampling_rate=16000, return_tensors="pt").input_values).logits[0], -1).numpy()
    vocab = proc.tokenizer.get_vocab(); blank = vocab.get("<pad>", 0); sep = vocab.get("|")
    seq, owner = [], []
    for wi, w in enumerate(words):
        for ch in re.sub(r"[^A-Z']", "", w.upper()):
            if ch in vocab: seq.append(vocab[ch]); owner.append(wi)
        if sep is not None and wi < len(words) - 1: seq.append(sep); owner.append(-1)
    T, L = lp.shape[0], len(seq)
    if L == 0 or T < L: return None
    # Viterbi over "stay or advance" (blank absorbed as stay): the classic trellis used for CTC forced alignment
    tr = np.full((T + 1, L + 1), -1e9, np.float32); tr[0, 0] = 0
    for t in range(T):
        tr[t + 1, 0] = tr[t, 0] + lp[t, blank]
        stay = tr[t, 1:] + lp[t, blank]; adv = tr[t, :-1] + lp[t, seq]
        tr[t + 1, 1:] = np.maximum(stay, adv)
    t, j, frame_of = T, L, [0] * L
    while j > 0 and t > 0:
        if tr[t - 1, j - 1] + lp[t - 1, seq[j - 1]] >= tr[t - 1, j] + lp[t - 1, blank]: frame_of[j - 1] = t - 1; j -= 1
        t -= 1
    sec = (len(a) / SR) / T; out = []
    for wi, w in enumerate(words):
        fr = [frame_of[k] for k in range(L) if owner[k] == wi]
        if not fr: return None
        out.append({"w": w, "s": round(fr[0] * sec, 3), "e": round((fr[-1] + 1) * sec, 3)})
    for k in range(len(out) - 1): out[k]["e"] = max(out[k]["e"], min(out[k + 1]["s"], out[k]["e"] + 0.25))
    return out

def energy_words(a, words):
    """Words spread over the VOICED time of the line by syllable weight; the line's own pauses (after a comma, a breath) stay between words."""
    if not words: return []
    dur = len(a) / SR; sil = [(s, e) for s, e in silences(a, 0.07) if e - s < dur]
    speech, t = [], 0.0
    for s, e in sil:
        if s > t: speech.append((t, s))
        t = max(t, e)
    if t < dur: speech.append((t, dur))
    speech = [(s, e) for s, e in speech if e - s > 0.02] or [(0.0, dur)]
    total = sum(e - s for s, e in speech)
    def real(x):                         # speech-time -> real time
        for s, e in speech:
            if x <= e - s + 1e-9: return s + x
            x -= e - s
        return speech[-1][1]
    wts = [max(1, syllables(w)) + 0.4 for w in words]; tot = sum(wts); acc = 0.0; out = []
    for w, k in zip(words, wts):
        s = real(acc / tot * total); acc += k; e = real(acc / tot * total - 1e-6)
        out.append({"w": w, "s": round(s, 3), "e": round(max(e, s + 0.04), 3)})
    return out

def word_times(a, text):
    words = _clean(text).split()
    mode = str(S("TTS_ALIGN") or "auto").strip().lower()
    if mode in ("auto", "ctc") and not FAKE:
        try:
            w = _ctc_words(a, words)
            if w: return w, "ctc"
        except Exception as e: log(f"CTC alignment failed for one line ({scrub(e)[:100]}) - energy timing", "WARN")
    return energy_words(a, words), "energy"

# ---------------------------------------------------------------- the request
def _pace():
    gap = 60.0 / max(1, S("TTS_RPM", int)); wait = _last_req[0] + gap - time.time()
    if wait > 0 and not FAKE: time.sleep(wait)
    _last_req[0] = time.time()

def _body(turns, voices):
    """turns = [(speaker, text, style)], voices = {speaker: voice}. One speaker = single-speaker config; two = multi-speaker config."""
    spk = list(dict.fromkeys(t[0] for t in turns))
    content = []
    for sp, text, style in turns:
        ann = {"type": "speech_metadata"}
        if len(spk) > 1: ann["speaker"] = sp
        if style: ann["style"] = style
        content.append({"type": "text", "text": text, "annotations": [ann]})
    sc = {"speakers": [{"speaker": s, "voice": voices[s]} for s in spk]} if len(spk) > 1 else [{"voice": voices[spk[0]]}]
    return {"model": tts_model(), "input": [{"type": "user_input", "content": content}], "response_format": {"type": "audio"},
            "generation_config": {"speech_config": sc}}

def _audio_of(j):
    """Base64 audio from an Interactions reply (steps[].content[] of type audio; the last one), or a generateContent-shaped reply."""
    data = None
    for st in j.get("steps") or []:
        for c in st.get("content") or []:
            if c.get("type") == "audio" and c.get("data"): data = c["data"]
    if not data and isinstance(j.get("output_audio"), dict): data = j["output_audio"].get("data")
    if not data:
        for c in j.get("candidates") or []:
            for p in (c.get("content") or {}).get("parts") or []:
                if (p.get("inlineData") or {}).get("data"): data = p["inlineData"]["data"]
    if not data: raise RuntimeError("Gemini TTS reply had no audio")
    return base64.b64decode(data)

def _usage_out(j):
    u = j.get("usage") or j.get("usageMetadata") or {}
    for k in ("total_output_tokens", "output_tokens", "candidatesTokenCount", "total_tokens_output"):
        if u.get(k): return int(u[k]), int(u.get("total_input_tokens") or u.get("input_tokens") or u.get("promptTokenCount") or 0)
    return None, None

def synth(turns, voices, episode=None):
    """One request -> (audio array, seconds). Retries 429/5xx with back-off. Cost logged per request."""
    body = _body(turns, voices); last = None
    for a in range(max(1, S("TTS_MAX_RETRIES", int))):
        _pace()
        try:
            if FAKE: j = _fake_reply(body)
            else:
                r = requests.post(GEM + "interactions", headers={"x-goog-api-key": env("GEMINI_KEY"), "content-type": "application/json"}, json=body, timeout=300)
                if r.status_code in (429, 500, 502, 503, 504):
                    ra = r.headers.get("Retry-After"); wait = float(ra) if ra and ra.replace(".", "", 1).isdigit() else 8 * (2 ** a)
                    last = RuntimeError(f"Gemini TTS {r.status_code}: {r.text[:200]}"); log(f"TTS busy ({r.status_code}), waiting {wait:.0f}s (try {a + 1})", "WARN", episode)
                    time.sleep(min(90, wait)); continue
                if r.status_code != 200: raise RuntimeError(f"Gemini TTS {r.status_code}: {r.text[:300]}")
                j = r.json()
            audio = wav_bytes_to_array(_audio_of(j)); sec = len(audio) / SR
            out_t, in_t = _usage_out(j)
            if out_t is None: out_t, in_t = int(sec * TOK_PER_SEC), int(sum(len(t[1]) + len(t[2]) for t in turns) / 4 + 30)
            cost("gemini_tts", "google", out_t, (out_t * price_out() + (in_t or 0) * S("PRICE_GEM_TTS_IN", float)) / 1e6, episode)
            return audio, sec
        except Exception as e:
            last = e
            if re.search(r"\b(400|401|403|404)\b", str(e)): break          # a refused voice / key / model: retrying the same request cannot help
            log(f"TTS request failed (try {a + 1}): {scrub(e)[:200]}", "WARN", episode); time.sleep(0 if FAKE else 4 * (a + 1))
    raise TTSFailed(f"Gemini TTS failed: {scrub(last)[:300]}")

def is_prebuilt(voice):
    from whatifs.data import PREBUILT_VOICES
    v = str(voice or "").strip()
    if v.startswith(("voice_", "voicekey_")): return False
    if v in PREBUILT_VOICES: return True
    for r in _voice_check_rows():
        if r.get("voice") == v: return str(r.get("source", "")).lower() == "prebuilt" or str(r.get("multi_speaker_ok")).upper() == "TRUE"
    return False

def _voice_check_rows():
    try: return store().rows("Voice_Check")
    except Exception: return []

# ---------------------------------------------------------------- the backend used by voice.narrate
class GeminiBackend:
    """narrate() calls prime(units) once (all paid requests happen here, chunk by chunk), then take(i, unit) per line."""
    engine = "gemini"
    def __init__(self, speakers, episode=None):
        """speakers = {'DIRECTOR': (voice, style_direction), 'SKEPTIC': (...), 'NARRATOR': (...)}"""
        self.spk = {k.upper(): v for k, v in speakers.items() if v and v[0]}; self.ep = episode; self.parts = {}; self.align = {}
        if not self.spk: raise TTSFailed("no Gemini voice for any speaker")
        if not tts_model(): raise TTSFailed("no Gemini TTS model found in the live model list")
        self.stats = {"requests": 0, "chunks": 0, "line_by_line": 0, "seconds": 0.0}
    def _voice(self, speaker):
        return self.spk.get(str(speaker).upper()) or self.spk.get("DIRECTOR") or next(iter(self.spk.values()))
    def _turn(self, u):
        v = self._voice(u.speaker); return (str(u.speaker).upper() if str(u.speaker).upper() in self.spk else "DIRECTOR", spoken_text(u), style_for(u, v[1]))
    def _request(self, idx, units):
        turns = [self._turn(units[i]) for i in idx]
        voices = {t[0]: self._voice(t[0])[0] for t in turns}
        key = _cache_key([self.ep] + turns, voices)                                 # v9: line-level audio cache (text + voice + style); a retry or a reel never re-buys it
        hit = _cache_get(key)
        if hit is not None: self.stats["cache_hits"] = self.stats.get("cache_hits", 0) + 1; return hit, 0.0
        self.stats["requests"] += 1
        a, sec = synth(turns, voices, self.ep)
        _cache_put(key, a); return a, sec
    def prime(self, units):
        self.units = units
        for idx in chunks(units):
            self.stats["chunks"] += 1
            spk = {str(units[i].speaker).upper() for i in idx}
            multi_ok = len(spk) < 2 or all(is_prebuilt(self._voice(s)[0]) for s in spk)
            groups = (_pairs(idx, units) if len(spk) > 2 else [idx]) if multi_ok else _runs(idx, units)   # custom voices: one request per same-speaker run;
                                                                                                       # v9: a request never carries more than TWO speakers
            for g in groups:
                audio, sec = self._request(g, units); self.stats["seconds"] += sec
                segs = split_turns(audio, [_weight(spoken_text(units[i])) + (2 if "<" in spoken_text(units[i]) else 0) for i in g])
                if segs is None:                                     # not convincing: every line on its own (durations measured exactly)
                    self.stats["line_by_line"] += 1
                    for i in g:
                        a, s2 = self._request([i], units); self.stats["seconds"] += s2; self.parts[i] = a
                    continue
                for i, (s, e) in zip(g, segs): self.parts[i] = audio[int(s * SR): int(e * SR)]
        missing = [i for i in range(len(units)) if i not in self.parts]
        if missing: raise TTSFailed(f"{len(missing)} line(s) without audio")
    def take(self, i, unit):
        a = self.parts.get(i)
        if a is None: raise TTSFailed(f"line {i} has no audio")
        w, how = word_times(a, unit.text); self.align[how] = self.align.get(how, 0) + 1
        return a.astype(np.float32), w

def _pairs(idx, units):
    """v9: consecutive lines grouped so each group has at most two different speakers (the multi-speaker request limit)."""
    out, cur = [], []
    for i in idx:
        sp = {str(units[j].speaker).upper() for j in cur} | {str(units[i].speaker).upper()}
        if cur and len(sp) > 2: out.append(cur); cur = []
        cur.append(i)
    if cur: out.append(cur)
    return out

def _cache_key(turns, voices):
    import hashlib, json as _j
    return hashlib.sha256(_j.dumps([turns, sorted(voices.items()), tts_model()], sort_keys=True, default=str).encode()).hexdigest()[:24]

def _cache_dir():
    import os
    from whatifs.core import WORK
    d = os.path.join(WORK, "_tts_cache"); os.makedirs(d, exist_ok=True); return d

def _cache_get(key):
    import os
    if not S("TTS_CACHE_ON", bool): return None
    p = os.path.join(_cache_dir(), key + ".npy")
    try: return np.load(p) if os.path.exists(p) else None
    except Exception: return None

def _cache_put(key, a):
    import os
    if not S("TTS_CACHE_ON", bool): return
    try: np.save(os.path.join(_cache_dir(), key + ".npy"), np.asarray(a, np.float32))
    except Exception as e: log(f"audio cache write skipped: {e}", "WARN")

def _runs(idx, units):
    out = []
    for i in idx:
        if out and str(units[out[-1][-1]].speaker).upper() == str(units[i].speaker).upper(): out[-1].append(i)
        else: out.append([i])
    return out

# ---------------------------------------------------------------- voice check (Setup + Voices workflow)
def list_voices():
    """[{id, display_name, type}] from GET v1beta/voices (custom + catalogue). [] if the call fails."""
    if FAKE:
        from whatifs.data import PREBUILT_VOICES
        return [{"id": v, "display_name": v, "type": "prebuilt"} for v in PREBUILT_VOICES]
    out, tok = [], ""
    for _ in range(10):
        r = requests.get(GEM + "voices", headers={"x-goog-api-key": env("GEMINI_KEY")}, params={"page_size": 1000, **({"page_token": tok} if tok else {})}, timeout=60)
        if r.status_code != 200: raise RuntimeError(f"voice list {r.status_code}: {r.text[:200]}")
        j = r.json()
        for v in j.get("voices") or []:
            out.append({"id": v.get("id") or v.get("name", "").split("/")[-1], "display_name": v.get("display_name") or v.get("displayName") or "", "type": v.get("type") or ""})
        tok = j.get("next_page_token") or j.get("nextPageToken") or ""
        if not tok: break
    return out

def voice_check(probe=True):
    """Which cast voices this key can REALLY use: listed by the API, a 1-second test line works, and (prebuilt only) a two-speaker line works.
    Results replace the Voice_Check tab. Cost: about 2 s of audio per voice (under Rs 0.1 for 20 voices). Returns (ok_count, total, problems)."""
    from whatifs import cast as CAST
    from whatifs.data import PREBUILT_VOICES
    want = [(r["id"], str(r["voice"]).strip()) for r in CAST.rows(active_only=False)]
    try: listed = list_voices(); err = ""
    except Exception as e: listed, err = [], scrub(e)[:160]
    by = {}
    for v in listed:
        for k in (v["id"], v["display_name"]): by[str(k).lower()] = v
    rows, problems, partner = [], [], next((v for _, v in want if v in PREBUILT_VOICES), "Kore")
    for cid, v in want:
        hit = by.get(v.lower()); src = (hit or {}).get("type") or ("prebuilt" if v in PREBUILT_VOICES else ("custom" if v.startswith("voice") else "unknown"))
        ok = multi = False; detail = err or ("listed" if hit else "not in this key's voice list")
        if probe:
            try: synth([("A", "Ready when you are.", "")], {"A": v}, "voicecheck"); ok = True
            except Exception as e: detail = scrub(e)[:160]
            if ok and src == "prebuilt":
                try: synth([("A", "Ready?", ""), ("B", "Ready.", "")], {"A": v, "B": partner if partner != v else "Puck"}, "voicecheck"); multi = True
                except Exception as e: detail = "single ok, two-speaker failed: " + scrub(e)[:120]
        if not ok: problems.append(f"{cid} {v}: {detail}")
        rows.append({"ts": iso(), "voice": v, "source": src, "listed": bool(hit), "synth_ok": ok, "multi_speaker_ok": multi, "detail": f"{cid}: {detail}"})
    try: store().replace("Voice_Check", rows)
    except Exception: safe_append("Voice_Check", rows)
    return sum(1 for r in rows if r["synth_ok"]), len(rows), problems

# ---------------------------------------------------------------- offline stand-in
_FAKE_PITCH = {}
def _fake_reply(body):
    sc = body["generation_config"]["speech_config"]
    vmap = {s["speaker"]: s["voice"] for s in sc["speakers"]} if isinstance(sc, dict) else {None: sc[0]["voice"]}
    if any(str(v).startswith("BROKEN") for v in vmap.values()): raise RuntimeError("Gemini TTS 400: voice not found (fake)")
    pieces = [np.zeros(int(0.12 * SR), np.float32)]
    for c in body["input"][0]["content"]:
        sp = (c.get("annotations") or [{}])[0].get("speaker"); v = vmap.get(sp, next(iter(vmap.values())))
        f0 = _FAKE_PITCH.setdefault(v, 105 + 9 * (len(_FAKE_PITCH) % 14))
        txt = _clean(c["text"]); n = int(max(0.35, len(txt) * 0.058) * SR); t = np.arange(n) / SR
        pieces.append((0.25 * np.sin(2 * np.pi * f0 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.3 * t))).astype(np.float32))
        pieces.append(np.zeros(int(0.42 * SR), np.float32))
    a = np.concatenate(pieces)
    return {"steps": [{"type": "model_output", "content": [{"type": "audio", "data": base64.b64encode(array_to_wav_bytes(a)).decode()}]}],
            "usage": {"total_output_tokens": int(len(a) / SR * TOK_PER_SEC), "total_input_tokens": 40}}
