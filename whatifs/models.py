"""Model discovery (names never typed in code), Claude and Gemini calls with prompt caching and routing, JSON repair, fallback and fake mode. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import hashlib, json, os, re, threading, time, concurrent.futures as cf
import requests
from whatifs.core import env, log, cost, S, store, iso, FAKE, status, note_degraded, JOB

ANTH = "https://api.anthropic.com/v1/"
CLAUDE_FAMILIES = ("opus", "sonnet", "haiku", "fable")
GEM = "https://generativelanguage.googleapis.com/v1beta/"
class Truncated(Exception):
    """The model stopped because it ran out of output room: the reply is cut and unusable as JSON. The caller retries ONCE with more room instead of re-asking blindly."""
def AH(): return {"x-api-key": env("ANTHROPIC_KEY"), "anthropic-version": "2023-06-01", "content-type": "application/json"}

def _vernum(s):
    return tuple(float(n) for n in re.findall(r"\d+(?:\.\d+)?", s)[:3]) or (0,)

def discover_models(write=True) -> dict:
    """Ask both providers which models exist today. Newest Opus, Sonnet, Gemini Pro and Flash are chosen.
    v7.3: runs weekly (Trend Scout) and after any 'model not found' error. A role that can't be found keeps its previous model."""
    global _models
    chosen = {}
    if FAKE:
        chosen = {"gem_image": "fake-image", "opus": "fake-opus", "sonnet": "fake-sonnet", "haiku": "fake-haiku", "fable": "fake-fable", "gem_pro": "fake-pro", "gem_flash": "fake-flash", "gem_tts": "fake-tts"}
    else:
        try:
            r = requests.get(ANTH + "models?limit=100", headers=AH(), timeout=30); r.raise_for_status()
            data = sorted(r.json().get("data", []), key=lambda m: m.get("created_at", ""), reverse=True)
            for fam in CLAUDE_FAMILIES:                              # v8.11: + haiku (mechanical chores) and fable (optional script writer)
                for m in data:
                    if fam in m["id"]: chosen[fam] = m["id"]; break
        except Exception as e: log(f"Anthropic model list failed: {e}", "WARN")
        try:
            r = requests.get(GEM + "models?pageSize=200", headers={"x-goog-api-key": env("GEMINI_KEY")}, timeout=30); r.raise_for_status()
            ms = [m["name"].split("/")[-1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
            bad = ("vision", "tts", "image", "embedding", "live", "audio", "lite", "exp", "preview", "thinking", "learnlm", "gemma")
            def pick(word):
                c = [m for m in ms if word in m and not any(b in m for b in bad)] or [m for m in ms if word in m and "lite" not in m]
                c.sort(key=_vernum, reverse=True); return c[0] if c else None
            chosen["gem_pro"] = pick("pro"); chosen["gem_flash"] = pick("flash")
            img = [m for m in ms if "image" in m and "flash" in m and "lite" not in m]                 # v10.2 (K152): reference-image start frames
            img.sort(key=_vernum, reverse=True); chosen["gem_image"] = img[0] if img else None
            from whatifs.tts_gemini import pick_tts                 # v8.10: the TTS model is discovered live like every other model (K11)
            chosen["gem_tts"] = pick_tts([m["name"].split("/")[-1] for m in r.json().get("models", [])])
        except Exception as e: log(f"Gemini model list failed: {e}", "WARN")
    if write:
        try: old = {r["role"]: r for r in store().rows("Models") if r.get("model")}
        except Exception: old = {}
        rows = [{"role": k, "provider": "anthropic" if k in CLAUDE_FAMILIES else "google", "model": v, "chosen_at": iso()} for k, v in chosen.items() if v]
        rows += [r for k, r in old.items() if not chosen.get(k)]
        if rows: store().replace("Models", rows)
        chosen = dict({k: r["model"] for k, r in old.items()}, **{k: v for k, v in chosen.items() if v})
        _models = None
    return chosen

_models = None
def _refresh_models():
    global _models
    try: _models = None; discover_models(); log("model list refreshed after a 'not found' error", "WARN")
    except Exception as e: log(f"model refresh failed: {e}", "WARN")
_rediscovered = [False]
def model(role):
    global _models
    if _models is None:
        _models = {r["role"]: r["model"] for r in store().rows("Models") if r.get("model")} or discover_models()
    if role not in _models and role in CLAUDE_FAMILIES and not _rediscovered[0]:      # v8.11: a Models tab from before Haiku / Fable were routed
        _rediscovered[0] = True
        try: _models = dict(_models, **{k: v for k, v in discover_models().items() if v})
        except Exception as e: log(f"model discovery for {role} failed: {e}", "WARN")
    return _models.get(role)

def parse_json(text):
    if isinstance(text, (dict, list)): return text
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.S).strip()
    cands = [t]
    if "{" in t: cands.append(t[t.find("{"): t.rfind("}") + 1])
    if "[" in t: cands.append(t[t.find("["): t.rfind("]") + 1])
    for c in cands:
        for x in (c, re.sub(r",\s*([}\]])", r"\1", c)):
            try: return json.loads(x)
            except Exception: pass
    raise ValueError(f"model did not return valid JSON (length {len(t)}; content not logged)")

# v8.9.3: Claude Sonnet 5.5 / Opus 5.5 (and Gemini thinking models) think before answering, and the thinking shares the output limit with the answer.
# Every caller's max_tokens is sized for the ANSWER, so this much extra room is added on top. It is only a ceiling: unused room costs nothing.
# v8.11: the room grows with the effort level (the docs: "set a large max_tokens at the higher levels").
THINK_ROOM = 16000
THINK_ROOM_BY_EFFORT = {"low": 6000, "medium": 16000, "high": 24000, "xhigh": 32000, "max": 48000}
TIGHT_NOTE = ("\n\nIMPORTANT (retry after a reply was cut off): keep your private reasoning short and write the final answer directly, in full, "
              "within the length asked. Do not draft it twice.")
_CALL = threading.local()

def task_of_call(): return getattr(_CALL, "task", "")

def last_call():
    """v12 (B5): what the most recent text call on this thread REALLY was - provider ('claude' / 'gemini'), the chain role that answered ('sonnet',
    'gem_pro', ...), the model id, the measured USD, and the citations and search results the API itself returned (never the model's own prose).
    Code that must prove who judged or where a fact came from reads this; {} before any call."""
    return dict(getattr(_CALL, "last", None) or {})

def _note_call(provider, role, mid, usd=0.0, citations=(), results=()):
    _CALL.last = {"provider": provider, "role": str(role or ""), "model": str(mid or ""), "usd": round(float(usd or 0), 6),
                  "citations": [dict(c) for c in citations], "results": [dict(r) for r in results]}

def _claude_sources(content):
    """(citations, results) from Claude content blocks: web_search_result_location citations (url, title, cited_text) and search results (url, title, page_age)."""
    cites, res = [], []
    for b in content or []:
        if not isinstance(b, dict): continue
        if b.get("type") == "web_search_tool_result" and isinstance(b.get("content"), list):
            res += [{"url": str(x.get("url") or ""), "title": str(x.get("title") or "")[:200], "page_age": str(x.get("page_age") or "")[:40]}
                    for x in b["content"] if isinstance(x, dict) and x.get("url")]
        for c in (b.get("citations") or []) if b.get("type") == "text" else []:
            if isinstance(c, dict) and c.get("url"):
                cites.append({"url": str(c["url"]), "title": str(c.get("title") or "")[:200], "cited_text": str(c.get("cited_text") or "")[:300]})
    return cites, res

def think_cap(task, eff):
    """v9.2: thinking room per role: THINK_CAPS (JSON {role: tokens}) first, else THINK_ROOM_BY_EFFORT capped by THINK_CAP_DEFAULT. Sized so one call
    can never cost more than its share of the writing allowance; a cut reply is retried at LOWER effort, never with more room."""
    try: caps = json.loads(S("THINK_CAPS") or "{}")
    except Exception: caps = {}
    if task in caps:
        try: return int(caps[task])
        except Exception: pass
    return min(THINK_ROOM_BY_EFFORT.get(eff or "medium", THINK_ROOM), S("THINK_CAP_DEFAULT", int) or 10 ** 9)
OUT_CEILING = 64000
EFFORTS = ("low", "medium", "high", "xhigh", "max")
_NO_SAMPLING = set()              # models that rejected temperature once: not sent to them again in this job (saves a refused request per call)
_NO_EFFORT = set()                # v8.11: models that rejected output_config.effort once (an older model): sent without it from then on
_NO_PREWARM = set()               # v8.11: models that rejected a zero-output warm-up: the first job of a fan-out runs serially instead
_PER_MSG_OFF = [False]            # v8.11: per-message effort (beta) rejected once in this job
_NO_CACHE = set()                 # v9: models that rejected a cache_control block once: sent uncached from then on (caching never fails a call)
EFFORT_RUN = {}                   # v9: per-episode effort override for the A/B test {episode: {task: level}}

class Declined(Exception):
    """The model declined (stop_reason 'refusal'). Asking the same model again would be paid twice for the same answer: the next model is used instead."""

# ---------------------------------------------------------------- v8.11: routing by capability (K90)
# Each writers'-room role -> (chain, effort class). Creative generation and judgment: Opus. The script itself: SCRIPT_MODEL (opus | fable).
# Edits, format, fact fixes, humanizing, length, packaging, reels: Sonnet. Mechanical chores (JSON repair only): Haiku, accepted only when the result
# is provably identical (json_same_words). Gemini keeps the independent judge, vision and search roles ("critic", "flash", "research").
ROUTES = {
    "scout": ("opus", "creative"), "showrunner": ("opus", "creative"), "bible": ("opus", "creative"), "premise_bank": ("opus", "creative"),
    "bench": ("opus", "creative"), "premise_judge": ("opus", "judge"), "owners_cut": ("opus", "judge"),
    "writer": ("script", "creative"), "rewrite": ("script", "creative"),
    "memo": ("sonnet", "edit"), "objections": ("sonnet", "edit"), "director_read": ("sonnet", "edit"), "director": ("sonnet", "edit"),
    "length": ("sonnet", "edit"), "format": ("sonnet", "edit"), "retention": ("sonnet", "edit"), "humanize": ("sonnet", "edit"),
    "factfix": ("sonnet", "edit"), "packager": ("sonnet", "edit"), "immersion": ("sonnet", "edit"),
    "hooks": ("sonnet", "edit"), "strategy": ("sonnet", "edit"), "brief": ("sonnet", "edit"), "repair": ("sonnet", "edit"),
    "json_repair": ("haiku", "chore"), "technique_intake": ("sonnet", "edit"),
    "localize": ("sonnet", "edit"), "special": ("sonnet", "edit"), "occasions_check": ("haiku", "chore"), "policy_rescue": ("sonnet", "edit"), "pilot": ("haiku", "chore"),                    # v10: special reels' concept                                                   # v10 G4: titles/descriptions in other languages
    "owner_chat": ("sonnet", "edit"), "owner_chat_deep": ("opus", "creative"), "owner_chat_cheap": ("haiku", "chore"),
    "jury": ("critic", "judge"), "jury_flash": ("flash", "judge"), "jury_claude": ("sonnet", "judge"), "punchup": ("sonnet", "edit"),      # v11 (K157) room v2      # v9.4b: WhatsApp / dashboard chat
    "rnd_research": ("sonnet", "edit"), "board_gemini": ("board_g", "judge"), "board_claude": ("board_c", "judge"),       # v12 B5: R&D research with web search; the Review Board's two families
    "short_writer": ("script", "creative"),          # v12 V2c: a Short is written (and fixed once) by the model that writes the long script
    "probe_gemini": ("flash", "judge"), "probe_claude": ("haiku", "chore"),          # v12 V1b: the promise line-up's two cheap readers (the right answer is known to code: no taste call)
}
SAVER_MEDIUM = ("scout", "showrunner", "bible", "premise_judge", "memo", "objections", "director", "director_read", "hooks", "packager", "immersion")
CHAIN_EFFORT = {"opus": "creative", "fable": "creative", "sonnet": "edit", "haiku": "chore"}

def _json_setting(key):
    try:
        v = json.loads(S(key) or "{}"); return v if isinstance(v, dict) else {}
    except Exception: return {}

def route(task):
    """task -> (chain key, effort class). Legacy chain keys ('opus', 'sonnet', 'critic', ...) pass through unchanged."""
    if task in ROUTES:
        chain, cls = ROUTES[task]
        over = str(_json_setting("MODEL_ROUTES").get(task) or "").strip().lower()
        if over in CHAINS or over == "script": chain = over
        if chain == "script": chain = "fable" if str(S("SCRIPT_MODEL") or "").strip().lower() == "fable" else "opus"
        return chain, cls
    return task, CHAIN_EFFORT.get(task, "edit")

def effort_for(task, cls):
    """The effort level a Claude call runs at: EFFORT_OVERRIDES[task] > EFFORT_<CLASS>. '' = do not send (the model's default)."""
    ab = EFFORT_RUN.get(JOB.get("episode") or "", {}).get(task)
    e = str(ab or _json_setting("EFFORT_OVERRIDES").get(task) or (S("PREMISE_BENCH_EFFORT") if task == "bench" else "")
            or ("medium" if S("AI_SAVER_ON", bool) and task in SAVER_MEDIUM else "") or S("EFFORT_" + str(cls).upper()) or "").strip().lower()
    return e if e in EFFORTS else ""

def _family(role):
    return role if role in CLAUDE_FAMILIES else "sonnet"

def prices(fam):
    """USD per million (input, output) and the cache multipliers (read, 5-min write, 1-h write) for a Claude family, all from Settings (K91)."""
    F = fam.upper()
    return {"in": S(f"PRICE_{F}_IN", float), "out": S(f"PRICE_{F}_OUT", float), "read": S(f"PRICE_{F}_CACHE_READ", float),
            "w5": S(f"PRICE_{F}_CACHE_W5", float), "w1h": S(f"PRICE_{F}_CACHE_W1H", float)}

def claude_usd(fam, u):
    """Measured cost of one Claude reply from its usage block. Cache writes are split into 5-min and 1-h parts when the API reports the split;
    otherwise the whole write is charged at the dearer 1-h rate when a 1-h breakpoint was sent (never under-counted)."""
    p = prices(fam); cc = u.get("cache_creation") or {}
    w_all = int(u.get("cache_creation_input_tokens", 0) or 0)
    w1 = int(cc.get("ephemeral_1h_input_tokens", 0) or 0); w5 = int(cc.get("ephemeral_5m_input_tokens", 0) or 0)
    if w_all and not (w1 or w5): w1, w5 = (w_all, 0) if u.get("_sent_1h") else (0, w_all)
    rd = int(u.get("cache_read_input_tokens", 0) or 0); inp = int(u.get("input_tokens", 0) or 0); out = int(u.get("output_tokens", 0) or 0)
    usd = (inp * p["in"] + w5 * p["in"] * p["w5"] + w1 * p["in"] * p["w1h"] + rd * p["in"] * p["read"] + out * p["out"]) / 1e6
    usd += (u.get("server_tool_use") or {}).get("web_search_requests", 0) * 0.01
    saved = (rd * p["in"] * (1 - p["read"]) - w5 * p["in"] * (p["w5"] - 1) - w1 * p["in"] * (p["w1h"] - 1)) / 1e6
    return usd, saved, {"in": inp, "read": rd, "w5": w5, "w1h": w1, "out": out}

# ---------------------------------------------------------------- v8.11: the cache manager (K89)
def est_tokens(text):
    return int(len(str(text or "")) / 4)

class CacheManager:
    """Builds the cached system blocks, chooses the episode TTL, warms the cache before a fan-out, records cache use per call and per episode
    (Cache_Stats), and warns when caching silently did not happen. It never changes what is asked: only where the breakpoints sit."""
    def __init__(self):
        self.lock = threading.Lock()
        self.seen = {}           # prefix hash -> {"sig": params signature, "at": start time, "ttl": ttl, "dur": seconds}
        self.effort_of = {}      # v9.2: prefix hash -> the effort the first call used
        self.stats = {}          # (episode, job) -> counters
        self.warned = set()
        self.run_id = os.environ.get("GITHUB_RUN_ID") or hashlib.md5(f"{time.time()}{os.getpid()}".encode()).hexdigest()[:10]
        self.dirty = set()

    def on(self): return S("PROMPT_CACHE_ON", bool)

    def blocks(self, system, model_id, sig, answer_room=0, fanout=False):
        """(system field for the request, info). info: breakpoints sent, ttl per layer, prefix hash, estimated prefix tokens."""
        from whatifs.prompts import Packed
        pk = Packed.of(system)
        info = {"bps": 0, "ttl": [], "hash": "", "prefix_tokens": 0, "sent_1h": False}
        if not self.on(): return str(system), info
        minimum = max(1, S("CACHE_MIN_TOKENS", int))
        glob, ep, role = pk.glob, pk.episode, pk.role
        out = []; cum = 0
        if glob:
            cum += est_tokens(glob); b = {"type": "text", "text": glob}
            if cum >= minimum: b["cache_control"] = {"type": "ephemeral", "ttl": "1h"}; info["ttl"].append("1h"); info["sent_1h"] = True
            out.append(b)
        if ep:
            cum += est_tokens(ep); b = {"type": "text", "text": ep}
            if cum >= minimum:
                ttl = self.episode_ttl(glob + ep, model_id, sig, answer_room, fanout)
                b["cache_control"] = {"type": "ephemeral", "ttl": ttl}; info["ttl"].append(ttl); info["sent_1h"] |= ttl == "1h"
            out.append(b)
        if role: out.append({"type": "text", "text": role})
        info["bps"] = sum(1 for b in out if "cache_control" in b)
        if not info["bps"]:
            if (glob or ep) and (model_id, "short") not in self.warned:
                self.warned.add((model_id, "short"))
                log(f"prompt cache: a shared prefix of about {cum} tokens is below CACHE_MIN_TOKENS ({minimum}) - sent without a breakpoint", "WARN")
            return str(system), info
        info["prefix_tokens"] = cum
        info["hash"] = hashlib.sha256((model_id + "|" + glob + "|" + ep).encode()).hexdigest()[:16]
        other = None
        with self.lock:
            prev = self.seen.get(info["hash"])
            if prev and prev["sig"] != sig and (info["hash"], "sig") not in self.warned:
                self.warned.add((info["hash"], "sig")); other = prev["sig"]
        if other is not None:      # v12 V2c-b2b2: written AFTER the lock is released - a log line can flush the log, the flush calls this object's own hook (flush -> rows), and that asks for the same lock: the job hung for ever whenever this warning was the 40th buffered line
            log(f"prompt cache: two calls share a prefix but differ in model parameters ({other} vs {sig}); the second cannot read the first's cache", "WARN")
        return out, info

    def aligned_effort(self, system, model_id, eff):
        """v9.2: the effort the first call with this cached prefix used (so a second call can read the cache instead of a 'differ in model parameters'
        miss). Remembered per prefix for the job."""
        from whatifs.prompts import Packed
        pk = Packed.of(system)
        if not (pk.glob or pk.episode): return eff
        h = hashlib.sha256((model_id + "|" + pk.glob + "|" + pk.episode).encode()).hexdigest()[:16]
        with self.lock:
            first = self.effort_of.setdefault(h, eff)
        if first != eff and (h, "align") not in self.warned:
            self.warned.add((h, "align")); log(f"prompt cache: effort aligned to '{first or 'default'}' (asked '{eff or 'default'}') so the shared prefix is read from the cache")
        return first
    def episode_ttl(self, prefix, model_id, sig, answer_room, fanout):
        """5 min by default. CACHE_TTL_AUTO: 1 h when the next use is likely to come after 5 min: a sequential call with a long reply (the lifetime counts
        from the START of the request, so a long reply eats the window), or a prefix whose earlier 5-min entry already expired before it was used again."""
        if not S("CACHE_TTL_AUTO", bool): return "5m"
        h = hashlib.sha256((model_id + "|" + prefix).encode()).hexdigest()[:16]
        prev = self.seen.get(h)
        if prev and prev.get("ttl") == "1h": return "1h"                              # keep one TTL per prefix (no second, different write)
        if prev and time.time() - prev["at"] > 270: return "1h"
        if not fanout and int(answer_room or 0) >= 8000: return "1h"
        return "5m"

    def note(self, info, sig, started, duration):
        if not info.get("hash"): return
        with self.lock:
            self.seen[info["hash"]] = {"sig": sig, "at": started, "ttl": "1h" if "1h" in info["ttl"][-1:] else "5m", "dur": duration}

    def record(self, episode, model_id, toks, usd, saved, info):
        """Per call: Run_Log line + counters for the episode's Cache_Stats row. Warns once when breakpoints were sent but nothing was cached."""
        ep = episode or JOB.get("episode") or ""
        key = (ep, JOB.get("name", "job"))
        if info.get("bps"):
            log(f"cache: {model_id} read {toks['read']} / wrote {toks['w5'] + toks['w1h']} (1h {toks['w1h']}) / uncached {toks['in']} / out {toks['out']} tokens", episode=episode,
                public=f"cache: read {toks['read']} wrote {toks['w5'] + toks['w1h']} tokens")
            if not toks["read"] and not (toks["w5"] + toks["w1h"]) and (model_id, "nocache") not in self.warned:
                self.warned.add((model_id, "nocache"))
                log(f"prompt cache: {model_id} cached nothing although {info['bps']} breakpoint(s) were sent (prefix about {info['prefix_tokens']} tokens; "
                    f"the model's minimum may be higher than CACHE_MIN_TOKENS={S('CACHE_MIN_TOKENS')}) - the call still worked, only uncached", "WARN", episode)
        with self.lock:
            st = self.stats.setdefault(key, {"calls": 0, "cached_calls": 0, "read": 0, "w5": 0, "w1h": 0, "in": 0, "out": 0, "saved": 0.0, "usd": 0.0, "warn": set()})
            st["calls"] += 1; st["cached_calls"] += 1 if info.get("bps") else 0
            for k in ("read", "w5", "w1h", "in", "out"): st[k] += toks.get(k, 0)
            st["saved"] += saved; st["usd"] += usd
            self.dirty.add(key)

    def record_other(self, episode, usd):
        """A Gemini text call: counted in the episode's measured AI spend (no prompt cache of ours involved)."""
        key = (episode or JOB.get("episode") or "", JOB.get("name", "job"))
        with self.lock:
            st = self.stats.setdefault(key, {"calls": 0, "cached_calls": 0, "read": 0, "w5": 0, "w1h": 0, "in": 0, "out": 0, "saved": 0.0, "usd": 0.0, "warn": set()})
            st["calls"] += 1; st["usd"] += usd; self.dirty.add(key)

    def rows(self):
        from whatifs.core import S as _S
        u = _S("USD_INR", float); out = []
        with self.lock: keys = list(self.dirty); self.dirty.clear()
        for key in keys:
            st = self.stats[key]; w = st["w5"] + st["w1h"]
            ratio = round(st["read"] / (st["read"] + w), 3) if st["read"] + w else ""
            if ratio != "" and ratio < S("CACHE_WARN_RATIO", float) and st["cached_calls"] >= 4 and "low" not in st["warn"]:
                st["warn"].add("low")
                log(f"prompt cache: hit ratio {ratio} for {key[0] or key[1]} is below CACHE_WARN_RATIO {S('CACHE_WARN_RATIO')} (see Cache_Stats)", "WARN", key[0] or None)
            out.append({"updated": iso(), "episode_id": key[0], "job": key[1], "run_id": self.run_id, "calls": st["calls"], "cached_calls": st["cached_calls"],
                        "cache_read_tok": st["read"], "cache_write_5m_tok": st["w5"], "cache_write_1h_tok": st["w1h"], "uncached_in_tok": st["in"], "out_tok": st["out"],
                        "hit_ratio": ratio, "tokens_saved": st["read"], "usd_saved": round(st["saved"], 4), "ai_measured_inr": round(st["usd"] * u, 2),
                        "ai_estimated_inr": round(ai_estimate_inr(), 2) if key[0] else "", "warnings": ",".join(sorted(st["warn"]))})
        return out

    def flush(self):
        """Upsert one Cache_Stats row per (episode, job, run). Never raises."""
        try:
            rows = self.rows()
            if not rows: return
            st = store()
            for r in rows:
                if not st.update_where("Cache_Stats", {"episode_id": r["episode_id"], "job": r["job"], "run_id": r["run_id"]}, r):
                    st.append("Cache_Stats", [r])
        except Exception as e:
            try: st.ensure_tabs()
            except Exception: pass
            print("cache stats flush skipped:", str(e)[:200])

def ai_estimate_inr():
    """The per-video AI-writing allowance the budget plans with (to compare with the measured spend in Cache_Stats / Cost_Log)."""
    from whatifs.core import S as _S
    tr = _S("TABLE_READ_EXTRA_INR", float) if str(_S("TABLE_READ_MODE") or "").strip().lower() in ("on", "true", "yes", "1") else 0.0
    return _S("LLM_EST_INR", float) + _S("THINK_EST_INR", float) + _S("ROOM_EXTRA_EST_INR", float) + tr

def write_ai_summary(episode):
    """v8.11 (K91): ONE Cost_Log row per finished video: measured AI-writing spend (every Claude + Gemini text call logged for it, TTS excluded) next to
    the estimate the budget plans with. inr = 0 on purpose (the spend is already in the measured rows; nothing is counted twice). Never raises."""
    from whatifs.core import flush_costs, S as _S
    try:
        flush_costs(); m = 0.0
        for r in store().rows("Cost_Log"):
            if r.get("episode_id") == episode and r.get("provider") in ("anthropic", "google") and r.get("item") != "gemini_tts" and r.get("basis") != "summary":
                try: m += float(r.get("inr") or 0)
                except Exception: pass
        est = ai_estimate_inr()
        store().append("Cost_Log", [{"ts": iso(), "episode_id": episode, "item": "ai_per_video_summary", "provider": "summary", "units": 0, "inr": 0,
                                     "basis": "summary", "measured_inr": round(m, 2), "est_inr": round(est, 2)}])
        log(f"AI writing for {episode}: measured Rs {m:.0f} vs estimated Rs {est:.0f}", episode=episode)
        return m, est
    except Exception as e:
        log(f"AI cost summary skipped: {str(e)[:160]}", "WARN", episode); return None

_CUR = threading.local()
CACHE = CacheManager()
try:
    from whatifs import core as _core
    if CACHE.flush not in _core.FLUSH_HOOKS: _core.FLUSH_HOOKS.append(CACHE.flush)
except Exception: pass

def _sig(mid, effort, search):
    return f"{mid}|effort={effort or 'default'}|search={bool(search)}|thinking=default"

def _claude_body(role, system, prompt, max_tokens, temperature, search, effort, fanout=False, prewarm=False):
    """The request body and the cache info. Thinking is never set (the 5.5 models think adaptively by default), so the thinking configuration is
    identical across every call that shares a prefix; effort is part of the signature (it is rendered into the prompt)."""
    mid = model(role)
    if not mid: raise RuntimeError(f"no {role} model")
    eff = "" if mid in _NO_EFFORT else effort
    room = min(OUT_CEILING, int(max_tokens) + think_cap(task_of_call(), eff))          # v9.2: a per-role thinking cap (Settings), never more on a retry
    sysf, info = (str(system), {"bps": 0, "ttl": [], "hash": "", "prefix_tokens": 0, "sent_1h": False}) if mid in _NO_CACHE else CACHE.blocks(system, mid, _sig(mid, eff, search), int(max_tokens), fanout)
    body = {"model": mid, "max_tokens": 0 if prewarm else room, "system": sysf, "messages": [{"role": "user", "content": prompt}]}
    if not prewarm and mid not in _NO_SAMPLING and temperature is not None: body["temperature"] = temperature
    headers = AH()
    if eff:
        if S("CACHE_EFFORT_PER_MESSAGE", bool) and not _PER_MSG_OFF[0]:
            body["messages"] = [{"role": "system", "content": [], "output_config": {"effort": eff}}] + body["messages"]
            headers = dict(headers, **{"anthropic-beta": "mid-conversation-output-config-2026-07-01"}); info["per_msg"] = True
        else: body["output_config"] = {"effort": eff}
    if search: body["tools"] = [{"type": S("ANTH_SEARCH_TOOL") or "web_search_20250305", "name": "web_search", "max_uses": 4}]
    return body, headers, info, room, mid, eff

def _post(body, headers):
    if FAKE:
        from whatifs.fakes import FAKE_ANTHROPIC
        return FAKE_ANTHROPIC.post(body, headers)
    return requests.post(ANTH + "messages", headers=headers, json=body, timeout=900)

def _strip_effort(body, headers):
    body.pop("output_config", None)
    body["messages"] = [m for m in body["messages"] if m.get("role") != "system"]
    headers.pop("anthropic-beta", None)

def _claude(role, system, prompt, max_tokens, temperature, search, episode, effort="", fanout=False, task=""):
    body, headers, info, room, mid, eff = _claude_body(role, system, prompt, max_tokens, temperature, search, effort, fanout)
    started = time.time()
    def post(): return _post(body, headers)
    _t0 = time.time()
    r = post()
    if r.status_code == 400 and info.get("per_msg") and re.search(r"output_config|beta|per-turn|Extra inputs", r.text, re.I):
        _PER_MSG_OFF[0] = True; log("per-message effort was rejected - top-level effort is used for the rest of this job", "WARN", episode)
        _strip_effort(body, headers); body["output_config"] = {"effort": eff}; info.pop("per_msg", None); r = post()
    if r.status_code == 400 and info.get("bps") and re.search(r"cache_control|ttl|cache", r.text, re.I):
        _NO_CACHE.add(mid); body["system"] = str(system); info = {"bps": 0, "ttl": [], "hash": "", "prefix_tokens": 0, "sent_1h": False}       # v9 hardening
        log(f"{mid} rejected cache_control - sent uncached for the rest of this job", "WARN", episode); r = post()
    if r.status_code == 400 and eff and re.search(r"effort|output_config", r.text, re.I):
        _NO_EFFORT.add(mid); _strip_effort(body, headers); r = post()                  # a model without effort support: its default level
    if r.status_code == 400 and "temperature" in body and re.search(r"temperature|top_p|top_k|sampling", r.text, re.I):
        _NO_SAMPLING.add(mid); body.pop("temperature"); r = post()          # Opus 5.5 / Sonnet 5.5 refuse temperature
    if r.status_code == 400 and body["max_tokens"] != max_tokens and "max_tokens" in r.text:
        body["max_tokens"] = room = int(max_tokens); r = post()            # an older model with a smaller output limit: the caller's own size
    if r.status_code == 400 and search and "tool" in r.text.lower():
        log("Claude web-search tool version rejected - answering without search (update ANTH_SEARCH_TOOL)", "WARN", episode)
        body.pop("tools", None); r = post()
    txt, content = "", []; fam = _family(role); usd_all = 0.0; blocks = []
    for hop in range(4):                                                   # a long web search can pause the turn: it is continued, at most 3 times
        if r.status_code != 200: raise RuntimeError(f"Claude {r.status_code}: {r.text[:300]}")
        j = r.json(); u = dict(j.get("usage", {}) or {}); u["_sent_1h"] = info.get("sent_1h")
        usd, saved, toks = claude_usd(fam, u); usd_all += usd; blocks += [b for b in (j.get("content") or []) if isinstance(b, dict)]   # output_tokens includes the thinking
        cost(f"claude_{role}", "anthropic", u.get("output_tokens", 0), usd, episode, role=getattr(_CUR, "task", ""),
             model=mid, in_tok=toks["in"], cache_read_tok=toks["read"], cache_write_tok=toks["w5"] + toks["w1h"], out_tok=toks["out"], basis="measured",
             ms=int((time.time() - _t0) * 1000))                                   # v11: latency (incl. any retry above) for the cost/latency log
        CACHE.record(episode, mid, toks, usd, saved, info)
        txt += "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")      # thinking blocks are skipped
        stop = j.get("stop_reason")
        if stop != "pause_turn" or hop == 3: break
        content += j.get("content", [])
        body["messages"] = [m for m in body["messages"] if m.get("role") == "system"] + [{"role": "user", "content": prompt}, {"role": "assistant", "content": content}]; r = post()
    CACHE.note(info, _sig(mid, eff, search), started, time.time() - started)
    if stop == "max_tokens": raise Truncated(f"Claude {role} reply was cut at {room} tokens")
    if stop == "refusal": raise Declined(f"Claude {role} declined this request")
    if stop in ("pause_turn", "model_context_window_exceeded"): raise RuntimeError(f"Claude {role} stopped early ({stop})")
    _note_call("claude", role, mid, usd_all, *_claude_sources(blocks))
    return txt

def prewarm(role, system, prompt, max_tokens, search, effort, episode=None):
    """ONE serial zero-output request (max_tokens 0) that writes the shared prefix before a fan-out, with the SAME model, effort, tools and
    breakpoints as the real calls, so every parallel call reads it. True = the cache was written or read. A model that rejects it -> False
    (the caller then runs the first job serially instead)."""
    if not CACHE.on() or not S("CACHE_WARM_ON", bool): return False
    try:
        body, headers, info, _, mid, eff = _claude_body(role, system, prompt, max_tokens, None, search, effort, fanout=True, prewarm=True)
    except Exception as e:
        log(f"cache warm-up skipped: {e}", "WARN", episode); return False
    if not info.get("bps") or mid in _NO_PREWARM: return False
    started = time.time()
    try:
        r = _post(body, headers)
        if r.status_code != 200:
            _NO_PREWARM.add(mid); log(f"cache warm-up refused ({r.status_code}) - the first call runs alone instead", "WARN", episode); return False
        u = dict(r.json().get("usage", {}) or {}); u["_sent_1h"] = info.get("sent_1h")
        usd, saved, toks = claude_usd(_family(role), u)
        cost(f"claude_{role}", "anthropic", 0, usd, episode, model=mid, in_tok=toks["in"], cache_read_tok=toks["read"],
             cache_write_tok=toks["w5"] + toks["w1h"], out_tok=0, basis="measured")
        CACHE.record(episode, mid, toks, usd, saved, info); CACHE.note(info, _sig(mid, eff, search), started, time.time() - started)
        return bool(toks["read"] or toks["w5"] or toks["w1h"])
    except Exception as e:
        log(f"cache warm-up failed: {e}", "WARN", episode); return False

def simulate_claude(role, system, prompt, max_tokens, search, effort, episode=None, fanout=False, prewarm=False):
    """Offline (WI_FAKE) twin of a Claude call: the SAME request body and breakpoints go to the fake cache server (fakes.FAKE_ANTHROPIC), which applies
    the documented caching rules; the usage it returns feeds Cache_Stats exactly like a real call. Nothing is billed. Never raises."""
    if not CACHE.on(): return None
    try:
        body, headers, info, _, mid, eff = _claude_body(role, system, prompt, max_tokens, None, search, effort, fanout, prewarm)
        started = time.time(); r = _post(body, headers)
        if r.status_code != 200: log(f"fake cache server refused the request: {r.text[:200]}", "WARN", episode); return r
        u = dict(r.json().get("usage", {}) or {}); u["_sent_1h"] = info.get("sent_1h")
        usd, saved, toks = claude_usd(_family(role), u)
        CACHE.record(episode, mid, toks, usd, saved, info); CACHE.note(info, _sig(mid, eff, search), started, 0.0)
        return r
    except Exception as e:
        log(f"cache simulation skipped: {e}", "WARN", episode); return None

def _gemini(role, system, prompt, max_tokens, temperature, search, want_json, images=None, episode=None, video=None):
    mid = model(role) or model("gem_flash")
    answered = role if model(role) else "gem_flash"                # v12 B5: the role that REALLY answers (a missing Pro model falls to Flash here): last_call() must never call a cheap model strong
    vparts = []
    if video:                                                      # v10 (Outlier Lab): a public YouTube URL, clipped to its first seconds (fileData + videoMetadata)
        vparts = [{"fileData": {"fileUri": video[0]}, "videoMetadata": {"startOffset": "0s", "endOffset": f"{int(video[1])}s"}}]
    body = {"systemInstruction": {"parts": [{"text": str(system)}]},
            "contents": [{"role": "user", "parts": vparts + [{"text": prompt}] + [{"inlineData": {"mimeType": m, "data": b}} for m, b in (images or [])]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": min(OUT_CEILING, int(max_tokens) + THINK_ROOM)}}      # v8.9.3: thinking shares this limit
    if search: body["tools"] = [{"google_search": {}}]
    elif want_json: body["generationConfig"]["responseMimeType"] = "application/json"
    _t0 = time.time()
    r = requests.post(GEM + f"models/{mid}:generateContent", headers={"x-goog-api-key": env("GEMINI_KEY")}, json=body, timeout=600)
    _ms = int((time.time() - _t0) * 1000)                                  # v11: latency per call, for the cost/latency log
    if r.status_code != 200: raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
    j = r.json(); c = (j.get("candidates") or [{}])[0]; usd = 0.0
    try:    # v8.1: Gemini calls were not in Cost_Log, so the "hard cap" under-counted. Logged from the usage numbers Google returns.
        u = j.get("usageMetadata") or {}; pro = "pro" in str(mid).lower()
        pin, pout = (S("PRICE_GEM_PRO_IN", float), S("PRICE_GEM_PRO_OUT", float)) if pro else (S("PRICE_GEM_FLASH_IN", float), S("PRICE_GEM_FLASH_OUT", float))
        out_tok = int(u.get("candidatesTokenCount", 0) or 0) + int(u.get("thoughtsTokenCount", 0) or 0); in_tok = int(u.get("promptTokenCount", 0) or 0)
        usd = (in_tok * pin + out_tok * pout) / 1e6
        cost("gemini_" + ("pro" if pro else "flash"), "google", out_tok, usd, episode, role=getattr(_CUR, "task", ""), model=mid, in_tok=in_tok, out_tok=out_tok, basis="measured", ms=_ms)
        CACHE.record_other(episode, usd)
    except Exception: pass
    if str(c.get("finishReason", "")).upper() == "MAX_TOKENS": raise Truncated(f"Gemini {role} reply was cut at {body['generationConfig']['maxOutputTokens']} tokens")
    chunks = [x.get("web") or {} for x in ((c.get("groundingMetadata") or {}).get("groundingChunks") or []) if isinstance(x, dict)]
    _note_call("gemini", answered, mid, usd, (), [{"url": str(w.get("uri") or ""), "title": str(w.get("title") or "")[:200], "page_age": ""} for w in chunks if w.get("uri")])
    return "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))

MAINTENANCE_JOBS = ("trends", "learn", "brief", "research", "money", "setup", "voices")     # may use the small reserve above the cap (policy guard, learning)
CHAINS = {"opus": [("c", "opus"), ("c", "sonnet"), ("g", "gem_pro"), ("g", "gem_flash")],
          "sonnet": [("c", "sonnet"), ("c", "opus"), ("g", "gem_pro"), ("g", "gem_flash")],
          "fable": [("c", "fable"), ("c", "opus"), ("c", "sonnet"), ("g", "gem_pro"), ("g", "gem_flash")],      # v8.11: a Fable refusal moves to Opus by itself
          "haiku": [("c", "haiku")],                                                                         # v8.11: chores only; no fallback (the caller has its own)
          "critic": [("g", "gem_pro"), ("g", "gem_flash"), ("c", "sonnet")],
          "flash": [("g", "gem_flash"), ("g", "gem_pro"), ("c", "sonnet")],
          "research": [("g", "gem_pro"), ("g", "gem_flash"), ("c", "sonnet")],
          "board_g": [("g", "gem_pro")], "board_c": [("c", "sonnet"), ("c", "opus")]}      # v12 B5: Review Board judges - strong models of ONE family each, never a cheap fallback

# ---------------------------------------------------------------- v8.11: Haiku JSON repair, accepted only when provably identical (K90)
def _words_of_text(t):
    t = re.sub(r"\\u[0-9a-fA-F]{4}|\\.", " ", str(t))
    return re.findall(r"[A-Za-z0-9]+", t)

def _words_of_json(x):
    out = []
    def walk(v):
        if isinstance(v, dict):
            for k, w in v.items(): out.extend(re.findall(r"[A-Za-z0-9]+", str(k))); walk(w)
        elif isinstance(v, list):
            for w in v: walk(w)
        elif isinstance(v, str): out.extend(re.findall(r"[A-Za-z0-9]+", v))
        else: out.extend(re.findall(r"[A-Za-z0-9]+", json.dumps(v)))
    walk(x); return out

def json_same_words(original, parsed):
    """True only if the repaired JSON holds exactly the original's words and numbers, in the same order (only punctuation, quotes, brackets and escapes
    may differ). This is the test that makes a Haiku repair give the SAME result as the expensive model's own answer."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(original or "").strip(), flags=re.S)
    a = t.find("{") if "{" in t else t.find("[")
    if a > 0: t = t[a:]
    z = max(t.rfind("}"), t.rfind("]"))
    if z >= 0: t = t[:z + 1]
    return bool(_words_of_text(t)) and _words_of_text(t) == _words_of_json(parsed)

REPAIR_SYSTEM = ("You repair broken JSON. Return the SAME content as valid JSON and nothing else. Never add, remove, reorder or change any word, number, key "
                 "or value; only fix punctuation, quotes, commas, brackets and escapes.")

def haiku_repair(text, episode=None):
    """The cheapest Claude model fixes JSON syntax (about Rs 0.05). None when off, unavailable, or not provably identical."""
    if not S("HAIKU_CHORES_ON", bool) or not str(text or "").strip(): return None
    from whatifs.governor import claude_allowed
    if not FAKE and not claude_allowed(): return None
    keep = dict(getattr(_CALL, "last", None) or {}); _CALL.last = {}     # v12 B5: the repair changes syntax only - last_call() keeps naming the model that ANSWERED and its sources
    try:
        if FAKE:
            from whatifs.fakes import fake_reply
            out = fake_reply("json_repair", str(text))
        else:
            out = _claude("haiku", REPAIR_SYSTEM, str(text)[:60000], min(32000, est_tokens(text) * 2 + 500), 0, False, episode, effort_for("json_repair", "chore"), task="json_repair")
        fixed = parse_json(out)
    except Exception as e:
        log(f"JSON repair by the chore model failed: {str(e)[:120]}", "WARN", episode); return None
    finally:
        if keep: keep["usd"] = round(float(keep.get("usd") or 0) + float((getattr(_CALL, "last", None) or {}).get("usd") or 0), 6)      # the repair's own cost is added
        _CALL.last = keep
    if json_same_words(text, fixed): log("reply was not valid JSON - repaired by the chore model (every word unchanged)", episode=episode); return fixed
    log("chore-model JSON repair changed the content - rejected, the normal retry runs", "WARN", episode); return None

# ---------------------------------------------------------------- the one entry point
PREPROD = {"on": False, "deadline": 0.0}   # v9.4a (WP2): set only by preprod.run() in its own job; module-level so fan-out threads see it too

def _preprod_batch(chain_key, search):
    """v9.4a (WP2): True when this call should go through Message Batches (half price) because pre-production is running and nobody is waiting."""
    if not PREPROD["on"] or search or not S("ROOM_BATCH_ON", bool): return False
    if chain_key not in CHAINS or CHAINS[chain_key][0][0] != "c": return False
    return not (PREPROD["deadline"] and time.time() > PREPROD["deadline"])      # past the job guard: the remaining calls run directly

ASK_TAPS = []          # v12: listeners at the one doorway for text calls; each fn(task, system, prompt) returns the system prompt to send (the department runner)
def _tap(task, system, prompt):
    for fn in list(ASK_TAPS):
        try: system = fn(str(task), system, prompt)
        except Exception as e: log(f"ask tap failed: {type(e).__name__}", "WARN")
    return system

REPLY_TAPS = []        # v12 B6a: listeners at the same doorway for what comes back; each fn(task, reply) returns the reply the caller gets (the runner takes its citations)
def _rtap(task, res):
    for fn in list(REPLY_TAPS):
        try: res = fn(str(task), res)
        except Exception as e: log(f"reply tap failed: {type(e).__name__}", "WARN")
    return res

def ask(role, system, prompt, want_json=True, max_tokens=6000, temperature=0.8, search=False, episode=None, fake_key=None, fanout=False, _direct=False):
    """Never blocks: walks the fallback chain. Claude roles move to Gemini when Claude credit runs out.
    v8.11: role may be a writers'-room task (ROUTES: model + effort chosen by capability) or a chain key as before; system may be a prompts.Packed."""
    task = role; chain_key, ecls = route(role); _CUR.task = str(task); _CALL.task = str(task)          # v9.1: Cost_Log 'role'; v9.2: per-role caps
    if ASK_TAPS: system = _tap(task, system, prompt)
    _CALL.last = {}
    if FAKE:
        from whatifs.fakes import fake_reply, fake_search, fake_cite
        if chain_key in CHAINS and CHAINS[chain_key][0][0] == "c": simulate_claude(CHAINS[chain_key][0][1], system, prompt, max_tokens, search, effort_for(task, ecls), episode, fanout)
        out = fake_reply(fake_key or role, prompt)
        p0, r0 = CHAINS[chain_key][0] if chain_key in CHAINS else ("c", _family(chain_key))
        _note_call("claude" if p0 == "c" else "gemini", r0, f"fake-{r0}", 0.0, *(fake_search(prompt) if search else ((), ())))
        if not want_json: return out
        try: res = parse_json(out)
        except ValueError:
            res = haiku_repair(out, episode)
            if res is None: raise
        return _rtap(task, fake_cite(res, system)) if REPLY_TAPS else res
    if not _direct and _preprod_batch(chain_key, search):                     # v9.4a (WP2): same request, half price, nobody waiting
        return ask_batch(role, system, prompt, want_json=want_json, max_tokens=max_tokens, episode=episode, fake_key=fake_key, temperature=temperature,
                         force=True, max_wait_min=S("ROOM_BATCH_MAX_WAIT_MIN", float))
    from whatifs.governor import claude_allowed, opus_allowed, monthly_cap_reached
    if monthly_cap_reached(maintenance=JOB.get("name") in MAINTENANCE_JOBS):
        raise RuntimeError("monthly budget cap reached; no new paid model calls will be started")
    chain = list(CHAINS[chain_key])
    if chain_key in ("opus", "fable") and not opus_allowed(): chain = [x for x in chain if x[1] not in ("opus", "fable")] or chain
    if not claude_allowed(): chain = [x for x in chain if x[0] == "g"] + [x for x in chain if x[0] == "c"]     # v8.1: Claude stays the LAST resort (a stale balance estimate must never leave a role with no model)
    last = None; refreshed = False; parse_fails = 0; first = chain[0] if chain else None; eff = effort_for(task, ecls)
    for prov, r in chain:
        mt = max_tokens
        for attempt in range(2):
            txt = None
            try:
                txt = (_claude(r, system, prompt, mt, temperature, search, episode, eff, fanout, task) if prov == "c"
                       else _gemini(r, str(system), prompt, mt, temperature, search, want_json, episode=episode))
                if want_json:
                    try: res = parse_json(txt)
                    except ValueError:
                        res = haiku_repair(txt, episode) if r != "haiku" else None       # v8.11: a cheap, verified syntax repair before paying for a re-ask
                        if res is None: raise
                else: res = txt
                if (prov, r) != first and chain_key in ("opus", "sonnet", "fable", "critic"): note_degraded(f"{task} answered by backup model {r}")
                return _rtap(task, res) if (REPLY_TAPS and want_json) else res
            except Declined as e:
                last = e; log(f"{task} via {r}: {e} - trying the next model", "WARN", episode); break
            except Truncated as e:
                last = e
                if not S("TRUNC_RETRY_LOWER_EFFORT", bool):             # v8.x behaviour (only when the owner switches v9.2 off)
                    log(f"{task} via {r}: {e} - retrying once with more room", "WARN", episode); mt = min(32000, int(mt * 1.7)); continue
                if attempt == 1: break                                   # v9.2: ONE retry per model, then the next model; never a bigger limit
                lower = {"max": "high", "xhigh": "high", "high": "medium", "medium": "low", "low": "low", "": "medium"}[eff if eff in EFFORTS else ""]
                log(f"{task} via {r}: {e} - retrying ONCE at lower effort ({eff or 'default'} -> {lower}) with the same limit and a tighter instruction", "WARN", episode)
                eff = lower; prompt = str(prompt) + TIGHT_NOTE; continue
            except ValueError as e:                            # not valid JSON: at most 3 such failures per call across the whole chain (each one is paid)
                last = e; parse_fails += 1; log(f"{task} via {r} failed: {e}", "WARN", episode)
                if parse_fails >= 3: raise RuntimeError(f"all models failed for {task}: {last}")
                time.sleep(3 + 5 * attempt)
            except Exception as e:
                last = e; log(f"{task} via {r} failed: {e}", "WARN", episode); time.sleep(3 + 5 * attempt)
                if not refreshed and re.search(r"\b404\b|not[_ ]found", str(e), re.I):
                    refreshed = True; _refresh_models()
    raise RuntimeError(f"all models failed for {task}: {last}")

# ---------------------------------------------------------------- v9: Message Batches for non-urgent jobs (50 % price; bounded wait, then the normal path)
def ask_batch(role, system, prompt, want_json=True, max_tokens=6000, episode=None, fake_key=None, temperature=0.8, force=False, max_wait_min=None):
    """One non-urgent Claude call through the Message Batches API when BATCH_ON (bench refill, monthly brief, strategy, research brief). The batch is
    polled for at most BATCH_MAX_WAIT_MIN minutes; on any error or timeout it is cancelled and the SAME request goes through ask() once (never two paid
    answers: a cancelled batch request that already finished is used instead). Cost is logged at PRICE_BATCH_DISCOUNT x the normal rate.
    Prompt caching inside batches is applied as usual; whether the discounts stack was not verified (see the report)."""
    chain_key, ecls = route(role)
    if ASK_TAPS: system = _tap(role, system, prompt)
    if FAKE or not (S("BATCH_ON", bool) or force) or chain_key not in CHAINS or CHAINS[chain_key][0][0] != "c":
        return ask(role, system, prompt, want_json=want_json, max_tokens=max_tokens, episode=episode, fake_key=fake_key, temperature=temperature, _direct=True)
    from whatifs.governor import claude_allowed, monthly_cap_reached, opus_allowed
    if not claude_allowed() or monthly_cap_reached(maintenance=JOB.get("name") in MAINTENANCE_JOBS) or (chain_key in ("opus", "fable") and not opus_allowed()):
        return ask(role, system, prompt, want_json=want_json, max_tokens=max_tokens, episode=episode, fake_key=fake_key, temperature=temperature, _direct=True)
    fam = CHAINS[chain_key][0][1]; bid = None
    try:
        body, headers, info, room, mid, eff = _claude_body(fam, system, prompt, max_tokens, temperature, False, effort_for(role, ecls))
        if mid in _NO_SAMPLING: body.pop("temperature", None)
        r = requests.post(ANTH + "messages/batches", headers=headers, json={"requests": [{"custom_id": "r1", "params": body}]}, timeout=60)
        if r.status_code >= 300: raise RuntimeError(f"batch create {r.status_code}: {r.text[:200]}")
        bid = r.json()["id"]; t0 = time.time()
        while time.time() - t0 < float(max_wait_min or S("BATCH_MAX_WAIT_MIN", float)) * 60:
            time.sleep(min(60, 10 + (time.time() - t0) / 10))
            st = requests.get(ANTH + f"messages/batches/{bid}", headers=headers, timeout=60).json()
            if st.get("processing_status") == "ended": break
        else:
            requests.post(ANTH + f"messages/batches/{bid}/cancel", headers=headers, timeout=60)
            time.sleep(5); st = requests.get(ANTH + f"messages/batches/{bid}", headers=headers, timeout=60).json()
            if (st.get("request_counts") or {}).get("succeeded", 0) < 1: raise TimeoutError("batch did not finish in time")
        res = requests.get(st["results_url"], headers=headers, timeout=120).text.strip().splitlines()
        item = json.loads(res[0])["result"]
        if item.get("type") != "succeeded": raise RuntimeError(f"batch result {item.get('type')}")
        j = item["message"]; u = dict(j.get("usage") or {}); u["_sent_1h"] = info.get("sent_1h")
        usd, saved, toks = claude_usd(fam, u); usd *= S("PRICE_BATCH_DISCOUNT", float)
        cost(f"claude_{fam}", "anthropic", u.get("output_tokens", 0), usd, episode, model=mid, in_tok=toks["in"], cache_read_tok=toks["read"],
             cache_write_tok=toks["w5"] + toks["w1h"], out_tok=toks["out"], basis="measured_batch")
        CACHE.record(episode, mid, toks, usd, saved, info)
        txt = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
        if j.get("stop_reason") in ("max_tokens", "refusal"): raise RuntimeError(f"batch stop {j.get('stop_reason')}")
        return (_rtap(role, parse_json(txt)) if REPLY_TAPS else parse_json(txt)) if want_json else txt
    except Exception as e:
        log(f"batch path not used for {role} ({str(e)[:140]}) - normal call instead", "WARN", episode)
        return ask(role, system, prompt, want_json=want_json, max_tokens=max_tokens, episode=episode, fake_key=fake_key, temperature=temperature, _direct=True)

def ask_vision(system, prompt, images, episode=None):
    """v8.2: independent frame check by Gemini Flash (then Pro). images = [(mime, base64 string)]. Returns parsed JSON, or None if no model could answer
    (the caller then reports 'vision check unavailable' and carries on: a missing judge never blocks and never fakes a pass)."""
    if FAKE:
        from whatifs.fakes import fake_reply
        return parse_json(fake_reply("vision", prompt))
    from whatifs.governor import monthly_cap_reached
    if monthly_cap_reached(maintenance=True): return None      # v8.3: the picture check of an episode that is already paid for may use the small reserve above the cap (about Rs 1)
    for role in ("gem_flash", "gem_pro", "gem_flash"):
        try: return parse_json(_gemini(role, system, prompt, 4000, 0.1, False, True, images=images, episode=episode))
        except Exception as e: log(f"vision check via {role} failed: {e}", "WARN", episode); time.sleep(8)
    return None

def ask_video(system, prompt, youtube_url, seconds=60, episode=None):
    """v10 (Outlier Lab): Gemini Flash watches the first `seconds` of a public YouTube video. Parsed JSON, or None (never raises)."""
    if FAKE:
        from whatifs.fakes import fake_reply
        return parse_json(fake_reply("outlier_video", prompt))
    from whatifs.governor import monthly_cap_reached
    if monthly_cap_reached(maintenance=False): return None
    try: return parse_json(_gemini("gem_flash", system, prompt, 2000, 0.2, False, True, episode=episode, video=(youtube_url, seconds)))
    except Exception as e: log(f"video look failed: {str(e)[:160]}", "WARN", episode); return None

def _shares_prefix(jobs):
    """True when 2+ jobs go to the same Claude chain with the same effort and search setting and the same cached layers (GLOBAL + EPISODE)."""
    from whatifs.prompts import Packed
    if len(jobs) < 2: return False
    keys = set()
    for j in jobs:
        ck, cls = route(j.get("role"))
        if ck not in CHAINS or CHAINS[ck][0][0] != "c": return False
        pk = Packed.of(j.get("system", ""))
        if not (pk.glob or pk.episode): return False
        keys.add((ck, effort_for(j.get("role"), cls), bool(j.get("search")), pk.glob, pk.episode))
    return len(keys) == 1

def ask_many(jobs, workers=4):
    """Independent calls side by side (each role stays its own call; nobody sees another's answer). v8.11: when they share a cached prefix, the cache
    is written ONCE first (a zero-output warm-up; if the model refuses that, the first job runs alone) so every parallel call reads it."""
    jobs = [dict(j, fanout=True) for j in jobs]
    head = []
    if CACHE.on() and _shares_prefix(jobs):
        j0 = jobs[0]; ck, cls = route(j0.get("role")); r = CHAINS[ck][0][1]
        if FAKE:
            simulate_claude(r, j0["system"], j0.get("prompt", ""), j0.get("max_tokens", 6000), j0.get("search"), effort_for(j0.get("role"), cls), j0.get("episode"), True, prewarm=True)
        else:
            from whatifs.governor import claude_allowed
            ok = claude_allowed() and prewarm(r, j0["system"], j0.get("prompt", ""), j0.get("max_tokens", 6000), j0.get("search"), effort_for(j0.get("role"), cls), j0.get("episode"))
            if not ok: head = [ask(**jobs[0])]; jobs = jobs[1:]
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return head + [f.result() for f in [ex.submit(ask, **j) for j in jobs]]

def selftest():
    m = discover_models()
    status("models_found", bool(m.get("sonnet") and m.get("gem_pro")), json.dumps(m))
    def claude_both():                         # v8.9.3: both Claude roles the pipeline uses; the answer room no longer has to hold the thinking too
        out = []
        for role in ("sonnet", "opus"):
            t = _claude(role, "Reply with the single word OK.", "OK?", 200, 0, False, "selftest")
            if not t.strip(): raise RuntimeError(f"Claude {role} ({model(role)}) answered with no text")
            out.append(f"{role} {model(role)}: {t.strip()[:20]}")
        return "; ".join(out)
    for name, fn in (("anthropic_works", claude_both),
                     ("gemini_works", lambda: _gemini("gem_flash", "Reply {\"ok\":true}", "ping", 200, 0, False, True))):
        try: t = fn(); status(name, bool(t), t[:120])
        except Exception as e: status(name, False, str(e)[:300])

