"""whatifs/fakes.py v8.11 (+ a fake Claude cache server that applies the documented caching rules) - offline stand-ins for every model call (rehearsal mode WI_FAKE=1). Zero cost."""
import json, re, random
from whatifs.core import SMALL

def _lines(n):
    pool = ["[calm] Right now, about eight billion people are doing something ordinary.", "[tension] But at exactly noon, all of them do it at once.",
            "[reveal] That adds up to a number nobody has ever written down.", "[aside] And somewhere, someone still replies 'k' to a long text... [beat] classic.",
            "[tension] The first ten seconds look harmless.", "[calm] Then the water starts to change colour.", "[pause:short]",
            "[reveal] By the end of the hour, the coastline has moved.", "[tension] And the strangest part is what happens to you.", "[callback] So next time, maybe just... don't."]
    return [pool[i % len(pool)] for i in range(n)]

def fake_reply(key, prompt):
    r = random.Random(len(prompt))
    if key == "scout":
        P4 = [("What if every pillow on Earth floated up at noon?", "Every Pillow Just Left Earth"), ("What if your bones turned to glass for a day?", "Your Bones Are Glass Now"),
              ("What if trees screamed when they were hurt?", "The Forest Can Scream"), ("What if Saturn's rings hung over your backyard?", "Saturn's Rings, Overhead")]      # v8.9.1: distinct pitches, so the vetted-tease gate has real choices
        return json.dumps({"pitches": [{"premise": P4[i][0], "ptype": "collective",
            "headline": P4[i][1], "family": ["F08_rules", "F01_body", "F06_nature", "F09_space"][i], "triggers": ["self-relevance"],
            "scores": {k: 8 for k in ["grasp", "weird", "personal", "unpredictable", "fresh", "showable", "pull"]}, "unexpected_answer": "x", "why_now": "y"} for i in range(4)]})
    if key == "showrunner":
        return json.dumps({"premise": "What if every pillow on Earth floated up at noon?", "headline": "Every Pillow Just Left Earth", "family": "F08_rules", "ptype": "collective", "logline": "l", "thesis": "t",
            "unexpected_answer": "u", "emotional_arc": "a", "peak_moment": "p", "humour_plan": "h", "title_candidates": ["What If Every Pillow Floated Away?"],
            "thumb_concept": "c", "reel_hooks": ["a", "b"], "risks": "r",
            "show_plan": {"charge": "Every pillow stands accused of breaking gravity at noon.", "defendant": "floating pillows", "intensity": 2,
                          "exhibits": [{"id": "A", "kind": "RECON", "what": "a bedroom at 11:59", "objection": "Pillows do not fly, Inspector."},
                                       {"id": "B", "kind": "DATA", "what": "lift needed per kilogram", "source": "NASA Glenn Research Center", "objection": "Numbers lie."},
                                       {"id": "C", "kind": "RECON", "what": "the sky full of pillows", "objection": ""}],
                          "witness_twist": "a measurement nobody checked", "jury_prompts": [{"kind": "guilty", "text": "Guilty or not guilty? Tell Nana Rosa."},
                          {"kind": "prediction", "text": "Where do the pillows stop rising?"}, {"kind": "abc", "text": "A, B or C: which exhibit sold you?"}],
                          "meter_swings": [{"after": "A", "side": "grimm", "n": 1}, {"after": "B", "side": "vale", "n": 2}], "verdict": {"winner": "vale", "detail": "lift"},
                          "clipbait_id": "C", "hud_spec": [{"t": 40, "type": "scale", "label": "Height", "value": 10, "unit": "m"}], "teacup_scenes": ["A", "C"],
                          "stinger": "Next case: your bones turn to glass.", "demand_evidence": {}},
            "next_tease": {"premise": "What if your bones turned to glass for a day?", "headline": "Your Bones Are Glass Now", "family": "F01_body", "ptype": "body", "line": "Next time: your bones turn to glass. Who survives breakfast?"}})
    if key == "memo": return json.dumps({"big_idea": "b", "needs": "n", "risk": "r", "techniques": ["Spielberg ripple"]})
    if key == "bible":
        return json.dumps({"conflicts": [{"issue": "i", "decision": "d"}], "beats": [{"n": i, "purpose": "p", "feeling": "f", "visual_world": "v", "sound": "s", "key_line": "k"} for i in range(1, 7)],
            "look": "cinematic, deep teal shadows, single warm key light, 35mm, fine grain", "recurring_motif": "m", "cta": {"like": "Tap like if your pillow is still here.", "subscribe": "Subscribe before the next object leaves.", "share": "Send this to the friend who sleeps on three pillows."}})
    if key == "writer":
        m = re.search(r"~(\d+) words", prompt); words = int(m.group(1)) if m else 300
        n = max(10, words // 11) if not SMALL else 12
        body = []
        k = 0
        for b, chunk in enumerate([_lines(n)[i:i + 4] for i in range(0, n, 4)], 1):
            body.append(f"## BEAT {b}")
            for ln in chunk:          # v8.1: Reality Engine dialogue; three label styles are mixed on purpose to exercise the tolerant parser
                if ln.startswith("[pause"): body.append(ln); continue
                who = "DIRECTOR" if k % 2 == 0 else "SKEPTIC"; tag = ln[:ln.index("]") + 1]; rest = ln[len(tag):].strip()
                body.append([f"[{who}] {tag} {rest}", f"{tag} [{who}] {rest}", f"{who}: {rest}"][k % 3]); k += 1
        L = [i for i, x in enumerate(body) if not x.startswith(("## BEAT", "[pause"))]      # v9: the trial tags (never spoken; ignored when SHOW_MODE = off)
        if len(L) >= 8:
            h = len(L) // 2
            body[L[1]] = "[EXHIBIT A] [METER -1 grimm] " + body[L[1]]; body[L[h]] = "[JURY] [EXHIBIT B] [METER +2 vale] " + body[L[h]]
            body[L[h + 1]] = "[CLIPBAIT] " + body[L[h + 1]] + " [/CLIPBAIT]"; body[L[-3]] = "[JURY] " + body[L[-3]]; body[L[-2]] = "[JURY] [EXHIBIT C] " + body[L[-2]]
        return json.dumps({"title_working": "Pillows", "script": "\n".join(body), "facts": [{"claim": "c", "reasoning": "r"}]})
    if key == "critic":
        return json.dumps({"scores": {k: 8 for k in ["hook_strength", "curiosity_gap", "escalation", "unpredictable_answer", "science_plausible", "pacing_variety",
            "humour_cringe_free", "originality_vs_recent", "policy_safe", "title_thumb_promise_kept", "sounds_human", "psychological_pull"]}, "verdict": "PASS", "fixes": {}})
    if key == "director":
        m = re.search(r"There are (\d+) shots", prompt); n = int(m.group(1)) if m else 10
        mm = re.search(r"\n(\d+): ", prompt); off = int(mm.group(1)) if mm else 0
        types = ["still", "graphic", "stock", "still", "living", "still", "kling"]
        shots = []
        for i in range(n):
            t = types[i % len(types)]
            shots.append({"unit": off + i, "type": t, "prompt": f"A floating pillow over a city, shot {i}", "motion": "slow push in", "search": "ocean waves", "camera": ["whip_settle", "drift", "spin_wildly", "kb_roll"][i % 4],
                          "graphic": {"label": "Pillows airborne", "from": 0, "to": 8000000000, "unit": ""}})
        return json.dumps({"shots": shots})
    if key == "packager":
        return json.dumps({"titles": ["What If Every Pillow Floated Away At Once?", "8 Billion Pillows Just Left Earth"], "thumb_text": "WHERE'D IT GO?", "thumb_prompt": "giant pillow over New York at dusk",
            "thumb_text_b": "LOOK UP", "thumb_prompt_b": "a single pillow drifting past the Moon",
            "reel_cover_prompts": ["pillow storm vertical", "pillow over ocean vertical"], "reel_cover_texts": ["8 BILLION PILLOWS?", "LOOK UP"],
            "description": "What happens if every pillow on Earth floats away at once?\n\nChapters\n\n#science #whatif #space",
            "tags": ["what if", "science"], "pinned_comment": "Would you chase yours?"})
    if key == "reel":
        return json.dumps({"reels": [{"format": "R1_climax_why", "hook_text": "WAIT FOR IT", "shots": [6, 0, 1, 3, 4, 5], "lines": ["[tension] Every pillow on Earth just left.", "[reveal] And that's the good news."],
            "end_line": "Full video on our channel.", "caption": "Where would yours go? #whatif #science #shorts"},
            {"format": "R3_myth", "hook_text": "YOU'RE WRONG", "shots": [2, 3, 5, 6, 0], "lines": ["[calm] Most people think nothing happens.", "[tension] They're wrong."],
            "end_line": "Full video on our channel.", "caption": "Think again. #whatif #science #shorts"},
            {"format": "R1_climax_why", "hook_text": "NO GRAVITY?", "shots": [1, 4, 0, 5, 2], "lines": ["[DIRECTOR] [tension] Every pillow on Earth weighs nothing now.", "[SKEPTIC] [wow] So where do they go?"],
            "end_line": "Where they land on day three? That is the full simulation, on our channel.", "caption": "Look up. #whatif #science #shorts"},
            {"format": "R3_myth", "hook_text": "8 BILLION", "shots": [3, 0, 6, 2, 1], "lines": ["[DIRECTOR] [calm] Eight billion pillows, one sky.", "[SKEPTIC] [laugh] That's a lot of feathers."],
            "end_line": "What the sky does next is in the full video.", "caption": "Feathers everywhere. #whatif #science #shorts"}]})
    if key == "vision":
        n = int(re.search(r"FRAMES: (\d+)", prompt).group(1)) if re.search(r"FRAMES: (\d+)", prompt) else 3
        return json.dumps({"frames": [{"i": i, "match": 9, "artifact": False, "note": ""} for i in range(n)]})
    if key == "memo2":
        return json.dumps({"objections": [{"to": "WRITER", "objection": "The cold open spends the peak image too early.", "request": "Hold the biggest image until beat 4."}]})
    if key == "director_read":
        return json.dumps({"notes": [{"beat": 1, "note": "The opening object must be shown close, in silence, before any wide shot."}]})
    if key == "research_synth":
        sigs = []
        m = re.search(r"SIGNALS \(JSON\): (\[.*\])", prompt, re.S)
        try: sigs = json.loads(m.group(1)) if m else []
        except Exception: sigs = []
        cands = [{"premise": "What if every pillow on Earth floated up at noon?", "family": "F08_rules", "audience_need": "Viewers appear to ask what physically happens when everyday objects float.",
                  "click_emotion": "Curiosity about a familiar object behaving impossibly.", "evidence": [s["id"] for s in sigs if "pillow" in s.get("title", "").lower()][:2] or [],
                  "channel_fit": "Strange-rules family; reasoned with simple physics."}]
        if sigs: cands.append({"premise": "What if you never slept again?", "family": "F01_body", "audience_need": "Suggests interest in sleep loss.", "click_emotion": "Dread.",
                               "evidence": [sigs[0]["id"]], "channel_fit": "Body family."})
        return json.dumps({"candidates": cands})
    if key == "hooks":
        L = [("Eight billion people do it at exactly noon.", "surprising_claim"), ("The water starts to change colour.", "outcome_promise"),
             ("The strangest part is what happens to you.", "curiosity_gap"), ("A number nobody has ever written down.", "curiosity_gap"),
             ("Nobody has written that number down.", "concrete_stakes"), ("All of them do it at once.", "concrete_stakes"),
             ("Something ordinary happens to eight billion people.", "surprising_claim"), ("By noon, the coastline has moved.", "concrete_stakes"),
             ("You find out what happens to you.", "outcome_promise"), ("Water changes colour, then the coastline moves.", "outcome_promise"),
             ("By the end of the hour, the coastline has moved today.", "surprising_claim"), ("Welcome to the strangest hour on Earth.", "curiosity_gap")]
        return json.dumps({"candidates": [{"line": a, "type": b, "basis": "script"} for a, b in L]})
    if key == "hook_score":
        ids = re.findall(r'"id": "(h\d+)"', prompt)
        return json.dumps({"scores": [{"id": i, "clarity": 9 - (n % 3) * 0.5, "relevance": 8.5, "curiosity": 8 - (n % 4) * 0.5, "promise_accuracy": 9, "unsupported_claim": False, "note": "fake"} for n, i in enumerate(ids)]})
    if key == "sync": return json.dumps({"ok": True, "problems": []})
    if key == "factcheck": return json.dumps({"checked": 3, "issues": [{"claim": "a number", "severity": "weak", "problem": "rounded", "correction": "about eight billion people"}]})
    if key == "humanize":
        m = re.search(r"NARRATION:\n(.*)\nReturn JSON", prompt, re.S)
        return json.dumps({"script": m.group(1) if m else "## BEAT 1\n[calm] Hello.", "changes": "rhythm"})
    if key == "retention":          # v8.7: the offline writer returns the narration unchanged (so the gate's 'no improvement = keep the draft' path runs)
        m = re.search(r"NARRATION:\n(.*)$", prompt, re.S)
        return json.dumps({"script": m.group(1) if m else "## BEAT 1\n[calm] Hello.", "changes": "none"})
    if key == "playbook":           # v8.7: one sourced official rule, one unsourced (must be refused), one that games the platform (must be refused)
        return json.dumps({"rules": [{"rule": "Show the exact object from the thumbnail on screen within the first five seconds of the video.", "department": "writer", "metric": "open",
                                      "source_url": "https://support.google.com/youtube/answer/9314415", "source_kind": "official", "evidence": "official", "why": "intro retention"},
                                     {"rule": "Titles with exactly seven words always get double the clicks on every channel.", "department": "packager", "metric": "pack", "source_url": "", "evidence": "well-replicated"},
                                     {"rule": "Ask viewers to sub4sub in the comments to grow faster this month.", "department": "writer", "metric": "hold", "source_url": "https://example.com/x", "evidence": "plausible"}]})
    if key == "research":
        return json.dumps({"exploding": [{"title": "t", "channel": "c", "why": "w", "patterns": {"title": "number", "thumb": "one object", "hook": "you", "structure": "countdown", "length": "9m", "humour": "light"}}],
            "platform_changes": [], "rising_angles": ["everyday x everyone"], "rules_for_room": ["Use a specific number in the title."]})
    if key == "strategy": return json.dumps({"name": "new_idea_" + str(r.randint(1, 999)), "definition": "A fresh structure."})
    if key == "brief": return "Monthly brief (rehearsal)."
    # ---- v8.10 stand-ins
    if key == "premise_bank":
        P8 = [("What if Saturn's rings were for sale?", "Saturn's Rings Are For Sale"), ("What if only you could hear Wi-Fi signals?", "You Can Hear Wi-Fi Now"),
              ("What if a volcano opened in your basement?", "There's A Volcano In Your Basement"), ("What if your shadow lagged one second behind you?", "Your Shadow Is One Second Late"),
              ("What if the Moon were as close as a skyscraper?", "The Moon Is Next Door"), ("What if your hair aged 50 years in one day?", "Your Hair Aged 50 Years Today"),
              ("What if every pillow on Earth floated up at noon?", "Every Pillow Just Left Earth"), ("What if rain fell upward for an hour?", "Rain Is Falling Up"),
              ("What if you could taste colours for a week?", "You Can Taste Colours Now"), ("What if your phone screen became a window to Mars?", "Your Phone Opens To Mars"),
              ("What if gravity flipped inside your bedroom only?", "Your Bedroom Lost Its Gravity")]
        return json.dumps({"premises": [{"premise": a, "headline": b, "family": "F09_space" if i % 2 else "F08_rules", "ptype": "collective", "pov_picture": "you look up"} for i, (a, b) in enumerate(P8)]})
    if key in ("premise_judge_claude", "premise_judge_gemini"):
        m = re.search(r"PITCHES: (\[.*?\])\s*\nReturn JSON", prompt, re.S)      # v8.10: the pitches travel in the user message
        try: pit = json.loads(m.group(1)) if m else []
        except Exception: pit = []
        off = 0.3 if key.endswith("gemini") else 0.0
        out = []
        for p in pit:
            weak = bool(re.search(r"scream|tears|lunch|gum|mushroom|yesterday", p.get("premise", ""), re.I))
            v = (4.5 if weak else 8.6) - off
            out.append(dict({c: v for c in ("weirdness", "counterintuitive_explainable", "showable_pov", "self_relevance", "emotional_peak", "novelty", "headline_fit")}, id=p["id"], note="fake"))
        return json.dumps({"scores": out})
    if key == "immersion":
        return json.dumps({"scenes": [{"quote": "The first ten seconds look harmless", "vantage": "eyes", "body": "a held breath", "senses": ["silence", "cold air"], "camera": "pov_rush", "sound": "riser", "impact": False},
                                      {"quote": "the coastline has moved", "vantage": "object", "body": "stomach drop", "senses": ["roar", "spray"], "camera": "impact_shake", "sound": "boom", "impact": True},
                                      {"quote": "the water starts to change colour", "vantage": "hands", "body": "cold fingers", "senses": ["drip"], "camera": "debris", "sound": "drip", "impact": False}],
                           "peak_quote": "By the end of the hour, the coastline has moved."})
    if key == "comment_classify":                 # v9.1: keep every other suggestion
        try: items = json.loads(prompt)
        except Exception: items = []
        return json.dumps({"items": [{"i": it["i"], "keep": it["i"] % 2 == 0, "premise": it["text"][:120]} for it in items]})
    if key == "comment_drafts":
        try: items = json.loads(prompt)
        except Exception: items = []
        return json.dumps({"items": [{"i": it["i"], "draft": "Good question. The evidence says: watch the next case. — Vale"} for it in items]})
    if key == "json_repair":                     # v8.11: syntax-only repair (trailing commas, missing closing brackets); words untouched
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(prompt).strip(), flags=re.S)
        t = t[t.find("{"):] if "{" in t else t
        t = re.sub(r",\s*([}\]])", r"\1", t)
        t += "]" * max(0, t.count("[") - t.count("]")) + "}" * max(0, t.count("{") - t.count("}"))
        return t
    if key == "bench":                           # v8.11: extra-effort premise generation for the Premise_Bench
        P6 = [("What if Saturn's rings were for sale on your street?", "Saturn's Rings Are For Sale"), ("What if you could hear every Wi-Fi signal?", "You Can Hear The Wi-Fi Now"),
              ("What if a volcano opened inside your city park?", "A Volcano Opened In The Park"), ("What if your shadow lagged ten seconds behind you?", "Your Shadow Is Ten Seconds Late"),
              ("What if the ocean stood still at noon?", "The Ocean Froze At Noon"), ("What if your reflection aged faster than you?", "Your Reflection Is Aging Faster"),
              ("What if lunch tasted like Tuesday?", "Lunch Tastes Like Tuesday"), ("What if your city floated a metre up?", "Your City Floats A Metre Up")]
        return json.dumps({"premises": [{"premise": a, "headline": b, "family": ["F09_space", "F08_rules", "F06_nature", "F01_body"][i % 4], "ptype": "collective",
                                         "pov_picture": "you, first person", **({"source_video_id": "fakevid0001"} if i < 2 else {})} for i, (a, b) in enumerate(P6)]})
    if key == "owners_cut":
        return json.dumps({"scores": {"inside_scene": 8, "weirdness_hook": 8, "emotional_peaks": 8, "payoff": 8, "originality": 8}, "fixes": []})
    if key == "techniques":
        return json.dumps({"observations": [{"video_id": "fakevid0001", "hook_device": "falls in first person before any word", "first_3s_visual": "clouds rushing at the lens",
                                             "cut_rhythm": "fast then one long hold", "sound_moment": "silence before the impact", "payoff_structure": "the bottom is revealed last", "evidence": "two comments mention the silence"},
                                            {"video_id": "invented999", "hook_device": "made up", "first_3s_visual": "x", "cut_rhythm": "x", "sound_moment": "x", "payoff_structure": "x", "evidence": "none"}]})
    return json.dumps({"ok": True})



# ---------------------------------------------------------------- v8.11: an offline Claude cache server (the documented rules, Nov 2026)
class _Resp:
    def __init__(self, code, data): self.status_code = code; self._d = data; self.text = json.dumps(data)
    def json(self): return self._d

class FakeAnthropic:
    """Applies the prompt-caching rules from the docs to a request body and answers with a realistic usage block:
    prefix order tools -> system -> messages; at most 4 breakpoints; a 1-h breakpoint never after a 5-min one; an empty text block cannot be cached;
    a prefix shorter than MIN tokens is silently not cached; writes only at breakpoints, reads look back for an earlier write of the same prefix;
    the lifetime counts from the START of the request; effort, tools and model are part of the cached prefix; max_tokens 0 = a warm-up (no output).
    Tokens are estimated as characters / 4. reply = the text to answer with (tests); clock = a time function (tests)."""
    MIN = 512
    def __init__(self, clock=None):
        import time as _t
        self.clock = clock or _t.time; self.entries = {}; self.calls = []; self.reply = '{"ok": true}'
    def reset(self): self.entries.clear(); self.calls.clear()
    def post(self, body, headers=None):
        import hashlib
        now = self.clock(); self.calls.append(body)
        sysf = body.get("system", ""); blocks = sysf if isinstance(sysf, list) else ([{"type": "text", "text": sysf}] if sysf else [])
        msgs = body.get("messages", [])
        bps = [b for b in blocks if b.get("cache_control")]
        for m in msgs:
            if isinstance(m.get("content"), list): bps += [b for b in m["content"] if isinstance(b, dict) and b.get("cache_control")]
        if len(bps) > 4: return _Resp(400, {"error": {"message": "A maximum of 4 blocks with cache_control may be provided"}})
        seen5 = False
        for b in bps:
            ttl = b["cache_control"].get("ttl", "5m")
            if ttl == "1h" and seen5: return _Resp(400, {"error": {"message": "a ttl='1h' cache_control block must not come after a ttl='5m' block"}})
            seen5 |= ttl == "5m"
            if not str(b.get("text", "")).strip(): return _Resp(400, {"error": {"message": "cache_control cannot be set for empty text blocks"}})
        if body.get("max_tokens") == 0 and (body.get("stream") or (body.get("thinking") or {}).get("type") == "enabled"):
            return _Resp(400, {"error": {"message": "max_tokens 0 is not allowed with stream or extended thinking"}})
        if any(m.get("role") == "system" and m.get("output_config") for m in msgs) and "mid-conversation-output-config" not in str((headers or {}).get("anthropic-beta", "")):
            return _Resp(400, {"error": {"message": "messages.0.output_config: Extra inputs are not permitted"}})
        head = json.dumps([body.get("model"), (body.get("output_config") or {}).get("effort"), body.get("tools"), body.get("thinking")], sort_keys=True)
        h = hashlib.sha256(head.encode()); pos = []; cum = 0
        for b in blocks:
            h.update(str(b.get("text", "")).encode()); cum += len(str(b.get("text", ""))) // 4
            pos.append((cum, h.copy().hexdigest(), b.get("cache_control")))
        for m in msgs:
            c = m.get("content"); txt = c if isinstance(c, str) else json.dumps(c, sort_keys=True)
            h.update(txt.encode()); cum += len(txt) // 4
        total = cum
        live = {k: v for k, v in self.entries.items() if v > now}; self.entries = live
        marks = [(t, k, cc) for t, k, cc in pos if cc]
        a = 0; hit_i = -1
        for i, (t, k, cc) in enumerate(marks):
            if k in live and t >= self.MIN: a = t; hit_i = i
        b1 = a; c = a; w1 = w5 = 0
        for i, (t, k, cc) in enumerate(marks):
            if i <= hit_i or t < self.MIN: continue
            ttl = cc.get("ttl", "5m")
            if ttl == "1h": w1 += t - max(b1, c); b1 = c = t
            else: w5 += t - c; c = t
            self.entries[k] = now + (3600 if ttl == "1h" else 300)
        for i, (t, k, cc) in enumerate(marks):                     # a read refreshes the entry's lifetime
            if i <= hit_i and k in self.entries: self.entries[k] = now + (3600 if cc.get("ttl") == "1h" else 300)
        last = max([t for t, k, cc in marks if t >= self.MIN] or [0])
        usage = {"input_tokens": max(0, total - max(last, a)), "cache_read_input_tokens": a, "cache_creation_input_tokens": w1 + w5,
                 "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1}, "output_tokens": 0 if body.get("max_tokens") == 0 else 400}
        content = [] if body.get("max_tokens") == 0 else [{"type": "text", "text": self.reply}]
        return _Resp(200, {"content": content, "stop_reason": "max_tokens" if body.get("max_tokens") == 0 else "end_turn", "usage": usage})

FAKE_ANTHROPIC = FakeAnthropic()
