"""whatifs/fakes.py v8.9 - offline stand-ins for every model call (rehearsal mode WI_FAKE=1). Zero cost."""
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
    return json.dumps({"ok": True})

