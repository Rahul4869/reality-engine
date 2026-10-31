"""whatifs/models.py v8.3 - model discovery (never typed in), Claude + Gemini calls, JSON repair, automatic fallback, fake mode."""
from __future__ import annotations
import json, re, time, concurrent.futures as cf
import requests
from whatifs.core import env, log, cost, S, store, iso, FAKE, status, note_degraded

ANTH = "https://api.anthropic.com/v1/"
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
        chosen = {"opus": "fake-opus", "sonnet": "fake-sonnet", "gem_pro": "fake-pro", "gem_flash": "fake-flash"}
    else:
        try:
            r = requests.get(ANTH + "models?limit=100", headers=AH(), timeout=30); r.raise_for_status()
            data = sorted(r.json().get("data", []), key=lambda m: m.get("created_at", ""), reverse=True)
            for fam in ("opus", "sonnet"):
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
        except Exception as e: log(f"Gemini model list failed: {e}", "WARN")
    if write:
        try: old = {r["role"]: r for r in store().rows("Models") if r.get("model")}
        except Exception: old = {}
        rows = [{"role": k, "provider": "anthropic" if k in ("opus", "sonnet") else "google", "model": v, "chosen_at": iso()} for k, v in chosen.items() if v]
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
def model(role):
    global _models
    if _models is None:
        _models = {r["role"]: r["model"] for r in store().rows("Models") if r.get("model")} or discover_models()
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

def _claude(role, system, prompt, max_tokens, temperature, search, episode):
    mid = model(role)
    if not mid: raise RuntimeError(f"no {role} model")
    body = {"model": mid, "max_tokens": max_tokens, "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": prompt}]}
    if search: body["tools"] = [{"type": S("ANTH_SEARCH_TOOL") or "web_search_20250305", "name": "web_search", "max_uses": 4}]
    r = requests.post(ANTH + "messages", headers=AH(), json=body, timeout=900)
    if r.status_code == 400 and "temperature" in r.text:
        body.pop("temperature"); r = requests.post(ANTH + "messages", headers=AH(), json=body, timeout=900)
    if r.status_code == 400 and search and "tool" in r.text.lower():
        log("Claude web-search tool version rejected - answering without search (update ANTH_SEARCH_TOOL)", "WARN", episode)
        body.pop("tools", None); r = requests.post(ANTH + "messages", headers=AH(), json=body, timeout=900)
    if r.status_code != 200: raise RuntimeError(f"Claude {r.status_code}: {r.text[:300]}")
    j = r.json(); u = j.get("usage", {})
    pin, pout = (S("PRICE_OPUS_IN", float), S("PRICE_OPUS_OUT", float)) if role == "opus" else (S("PRICE_SONNET_IN", float), S("PRICE_SONNET_OUT", float))
    usd = (u.get("input_tokens", 0) * pin + u.get("cache_creation_input_tokens", 0) * pin * 1.25 +
           u.get("cache_read_input_tokens", 0) * pin * 0.1 + u.get("output_tokens", 0) * pout) / 1e6
    usd += (u.get("server_tool_use") or {}).get("web_search_requests", 0) * 0.01
    cost(f"claude_{role}", "anthropic", u.get("output_tokens", 0), usd, episode)
    txt = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
    if j.get("stop_reason") == "max_tokens": raise Truncated(f"Claude {role} reply was cut at {max_tokens} tokens")
    return txt

def _gemini(role, system, prompt, max_tokens, temperature, search, want_json, images=None):
    mid = model(role) or model("gem_flash")
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}] + [{"inlineData": {"mimeType": m, "data": b}} for m, b in (images or [])]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if search: body["tools"] = [{"google_search": {}}]
    elif want_json: body["generationConfig"]["responseMimeType"] = "application/json"
    r = requests.post(GEM + f"models/{mid}:generateContent", headers={"x-goog-api-key": env("GEMINI_KEY")}, json=body, timeout=600)
    if r.status_code != 200: raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
    j = r.json(); c = (j.get("candidates") or [{}])[0]
    try:    # v8.1: Gemini calls were not in Cost_Log, so the "hard cap" under-counted. Logged from the usage numbers Google returns.
        u = j.get("usageMetadata") or {}; pro = "pro" in str(mid).lower()
        pin, pout = (S("PRICE_GEM_PRO_IN", float), S("PRICE_GEM_PRO_OUT", float)) if pro else (S("PRICE_GEM_FLASH_IN", float), S("PRICE_GEM_FLASH_OUT", float))
        out_tok = int(u.get("candidatesTokenCount", 0) or 0) + int(u.get("thoughtsTokenCount", 0) or 0)
        cost("gemini_" + ("pro" if pro else "flash"), "google", out_tok, (int(u.get("promptTokenCount", 0) or 0) * pin + out_tok * pout) / 1e6)
    except Exception: pass
    if str(c.get("finishReason", "")).upper() == "MAX_TOKENS": raise Truncated(f"Gemini {role} reply was cut at {max_tokens} tokens")
    return "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))

MAINTENANCE_JOBS = ("trends", "learn", "brief", "research", "money", "setup", "voices")     # may use the small reserve above the cap (policy guard, learning)
CHAINS = {"opus": [("c", "opus"), ("c", "sonnet"), ("g", "gem_pro"), ("g", "gem_flash")],
          "sonnet": [("c", "sonnet"), ("c", "opus"), ("g", "gem_pro"), ("g", "gem_flash")],
          "critic": [("g", "gem_pro"), ("g", "gem_flash"), ("c", "sonnet")],
          "flash": [("g", "gem_flash"), ("g", "gem_pro"), ("c", "sonnet")],
          "research": [("g", "gem_pro"), ("g", "gem_flash"), ("c", "sonnet")]}

def ask(role, system, prompt, want_json=True, max_tokens=6000, temperature=0.8, search=False, episode=None, fake_key=None):
    """Never blocks: walks the fallback chain. Claude roles move to Gemini when Claude credit runs out."""
    if FAKE:
        from whatifs.fakes import fake_reply
        out = fake_reply(fake_key or role, prompt)
        return parse_json(out) if want_json else out
    from whatifs.governor import claude_allowed, opus_allowed, monthly_cap_reached
    from whatifs.core import JOB
    if monthly_cap_reached(maintenance=JOB.get("name") in MAINTENANCE_JOBS):
        raise RuntimeError("monthly budget cap reached; no new paid model calls will be started")
    chain = list(CHAINS[role])
    if role == "opus" and not opus_allowed(): chain = [x for x in chain if x[1] != "opus"]
    if not claude_allowed(): chain = [x for x in chain if x[0] == "g"] + [x for x in chain if x[0] == "c"]     # v8.1: Claude stays the LAST resort (a stale balance estimate must never leave a role with no model)
    last = None; refreshed = False; parse_fails = 0; first = chain[0] if chain else None
    for prov, r in chain:
        mt = max_tokens
        for attempt in range(2):
            try:
                txt = (_claude(r, system, prompt, mt, temperature, search, episode) if prov == "c"
                       else _gemini(r, system, prompt, mt, temperature, search, want_json))
                res = parse_json(txt) if want_json else txt
                if (prov, r) != first and role in ("opus", "sonnet", "critic"): note_degraded(f"{role} answered by backup model {r}")
                return res
            except Truncated as e:
                last = e; log(f"{role} via {r}: {e} - retrying once with more room", "WARN", episode)
                mt = min(32000, int(mt * 1.7)); continue      # a cut reply is a sizing problem, not a model problem: same model, bigger limit, no sleep
            except ValueError as e:                            # not valid JSON: at most 3 such failures per call across the whole chain (each one is paid)
                last = e; parse_fails += 1; log(f"{role} via {r} failed: {e}", "WARN", episode)
                if parse_fails >= 3: raise RuntimeError(f"all models failed for {role}: {last}")
                time.sleep(3 + 5 * attempt)
            except Exception as e:
                last = e; log(f"{role} via {r} failed: {e}", "WARN", episode); time.sleep(3 + 5 * attempt)
                if not refreshed and re.search(r"\b404\b|not[_ ]found", str(e), re.I):
                    refreshed = True; _refresh_models()
    raise RuntimeError(f"all models failed for {role}: {last}")

def ask_vision(system, prompt, images, episode=None):
    """v8.2: independent frame check by Gemini Flash (then Pro). images = [(mime, base64 string)]. Returns parsed JSON, or None if no model could answer
    (the caller then reports 'vision check unavailable' and carries on: a missing judge never blocks and never fakes a pass)."""
    if FAKE:
        from whatifs.fakes import fake_reply
        return parse_json(fake_reply("vision", prompt))
    from whatifs.governor import monthly_cap_reached
    from whatifs.core import JOB
    if monthly_cap_reached(maintenance=True): return None      # v8.3: the picture check of an episode that is already paid for may use the small reserve above the cap (about Rs 1)
    for role in ("gem_flash", "gem_pro", "gem_flash"):
        try: return parse_json(_gemini(role, system, prompt, 4000, 0.1, False, True, images=images))
        except Exception as e: log(f"vision check via {role} failed: {e}", "WARN", episode); time.sleep(8)
    return None

def ask_many(jobs, workers=4):
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return [f.result() for f in [ex.submit(ask, **j) for j in jobs]]

def selftest():
    m = discover_models()
    status("models_found", bool(m.get("sonnet") and m.get("gem_pro")), json.dumps(m))
    for name, fn in (("anthropic_works", lambda: _claude("sonnet", "Reply OK.", "OK?", 5, 0, False, "selftest")),
                     ("gemini_works", lambda: _gemini("gem_flash", "Reply {\"ok\":true}", "ping", 50, 0, False, True))):
        try: t = fn(); status(name, bool(t), t[:120])
        except Exception as e: status(name, False, str(e)[:300])

