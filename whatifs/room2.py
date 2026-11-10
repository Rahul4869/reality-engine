"""v11 Stage B (K157): writers' room v2 - the parts of the room that research shows actually raise quality, nothing for show.

Research (9 Nov 2026 reports): role-play memos and debate add cost without quality; what works is (1) several genuinely DIFFERENT drafts from one strong
writer, (2) selection by a BLIND jury from a different model family (both orderings, ranking only, no authorship labels), (3) ONE revision against a
concrete checklist, (4) for jokes: many candidates per slot, ranked by STRONG judges that see EVERY candidate (cheap models never make taste calls).

In the room (room.run_room) when ROOM_MODE = v2:
- no role memos / table-read objections (the bible is still written: it is the showrunner's plan);
- write(): ROOM_V2_DRAFTS drafts by the script model, each forced to a different cold-open archetype (the brain's sampler picks the first);
  the jury (Gemini Pro + Gemini Flash + Claude Sonnet, labels A/B/C, each in two orders) ranks them; Borda count picks the winner; one checklist
  revision with the jury's weakest-point notes and the code's retention issues;
- jokes(): JOKE_SLOTS scene-ending lines; JOKE_CANDIDATES alternatives per slot (Sonnet); the ORIGINAL line is always a candidate; the strong jury
  (Gemini Pro + Claude Sonnet) ranks ALL candidates; a line is replaced only when a candidate beats the original. Labels and tags never change.
Every jury decision is logged (Jury_Log) so judges can be scored against real results later."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, store, iso, scrub, FAKE

JURY = (("jury", "Gemini Pro"), ("jury_flash", "Gemini Flash"), ("jury_claude", "Claude Sonnet"))
JOKE_JURY = (("jury", "Gemini Pro"), ("jury_claude", "Claude Sonnet"))
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

DRAFT_RUBRIC = ("Rank these narrations for an animated courtroom-comedy science show, best first. Judge ONLY what a viewer would feel: (1) would a "
                "stranger keep watching after the first 10 seconds; (2) clear stakes and a curiosity gap that pays off; (3) escalation with 'but/therefore', "
                "no 'and then'; (4) genuinely funny character moments; (5) accurate science; (6) a verdict that lands. Ignore length differences. The "
                "narrations are anonymous; never guess who wrote them.")
JOKE_RUBRIC = ("Rank these alternative lines for ONE moment of an animated courtroom-comedy science show, funniest first. A great line is surprising, "
               "clear on one listen, true to the speaking character, and lands its punch word last. Lines are anonymous.")

def _jury_ask(role, rubric, items, context, episode):
    """One judge, one order -> ranking of letters (best first)."""
    from whatifs.models import ask
    labels = LETTERS[:len(items)]
    body = "\n\n".join(f"[{l}]\n{t}" for l, t in zip(labels, items))
    sysmsg = rubric + ' Return JSON only: {"ranking": ["<letter>", ...] (every letter once, best first), "weakest_point": {"<letter>": "<one concrete fix>"}}'
    out = ask(role, sysmsg, (f"CONTEXT: {context}\n\n" if context else "") + body, episode=episode, fake_key="jury", max_tokens=1200, temperature=0.2)
    rk = [x for x in (out.get("ranking") or []) if x in labels]
    rk += [l for l in labels if l not in rk]                                   # a judge that skipped a letter ranks it last
    return rk, out.get("weakest_point") or {}

def jury(items, rubric, context, episode, stage, judges=JURY, orders=None):
    """Blind ranking by several judges, each in ORDERINGS orders (original + reversed). Borda count. Returns (winner_index, detail)."""
    n = len(items)
    if n <= 1: return 0, {"scores": [1.0] * n, "judges": []}
    orders = orders or max(1, S("JURY_ORDERINGS", int))
    score = [0.0] * n; notes = {}; rows = []; per = []
    for role, name in judges:
        for o in range(orders):
            idx = list(range(n)) if o % 2 == 0 else list(reversed(range(n)))
            try: rk, wp = _jury_ask(role, rubric, [items[i] for i in idx], context, episode)
            except Exception as e:
                log(f"jury {name} order {o} failed: {scrub(e)[:100]}", "WARN", episode); continue
            pos = {LETTERS[k]: idx[k] for k in range(n)}
            ranked = [pos[l] for l in rk]
            for place, i in enumerate(ranked): score[i] += (n - 1 - place)
            for l, fix in wp.items():
                if l in pos: notes.setdefault(pos[l], []).append(str(fix)[:200])
            per.append({"judge": name, "order": o, "ranking": ranked})
            rows.append({"ts": iso(), "episode_id": episode, "stage": stage, "judge": name, "order": o, "ranking": json.dumps(ranked), "n": n})
    try:
        if rows: store().append("Jury_Log", rows)
    except Exception: pass
    if not per: return 0, {"scores": score, "judges": [], "failed": True}
    win = max(range(n), key=lambda i: (score[i], -i))
    return win, {"scores": score, "judges": per, "notes": notes}

# ---------------------------------------------------------------- drafts -> jury -> one checklist revision
def _archetypes(n, episode):
    from whatifs import brain as BR
    names = list(BR.HOOK_ARCHETYPES)
    first = (BR.choose("hook", "long").get("level") if S("BRAIN_ON", bool) else None) or names[0]
    out = [first] + [x for x in names if x != first]
    return out[:max(1, n)]

def write(spine, wbrief, d, episode):
    """Returns (script_dict, verdict_like). The verdict carries the jury's scores so the room's logs keep working."""
    from whatifs.models import ask_many, ask
    from whatifs import brain as BR, growth as GR
    n = max(1, S("ROOM_V2_DRAFTS", int)); arch = _archetypes(n, episode)
    reqs = [dict(role="writer", system=wbrief, episode=episode, fake_key="writer", max_tokens=16000,
                 prompt=f"Write the full narration. COLD-OPEN ARCHETYPE (mandatory, it shapes the first 10 seconds): {a} - {BR.HOOK_ARCHETYPES.get(a, '')}. "
                        "Everything after the cold open follows the bible and the rules above.") for a in arch]
    drafts = ask_many(reqs)
    ok = [(a, x) for a, x in zip(arch, drafts) if isinstance(x, dict) and str(x.get("script", "")).strip()]
    if not ok: raise RuntimeError("room v2: no draft came back")
    texts = [x["script"] for _, x in ok]
    ctx = f"Premise: {spine.get('premise', '')}. Promise to the viewer: {GR.promise_text(spine.get('promise'))}"
    win, info = jury(texts, DRAFT_RUBRIC, ctx, episode, "drafts")
    chosen_arch, script = ok[win]
    d["room_v2"] = {"drafts": [a for a, _ in ok], "winner": chosen_arch, "scores": [round(s, 1) for s in info["scores"]]}
    d["hook_archetype"] = chosen_arch
    fixes = list(dict.fromkeys(info.get("notes", {}).get(win, [])))[:4]
    if S("RETENTION_GATE_ON", bool):
        fixes += GR.retention_issues(script.get("script", ""), spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops"))["issues"][:4]
    if fixes:                                                                  # ONE revision against a concrete checklist (research: one pass, specific)
        rev = ask("rewrite", wbrief, "REVISION CHECKLIST (apply every item; keep every label, tag, '## BEAT' line and fact): "
                  + " ".join(f"({k + 1}) {x}" for k, x in enumerate(fixes)) + "\nNARRATION:\n" + script.get("script", "") + "\nRewrite the full narration.",
                  episode=episode, fake_key="writer", max_tokens=16000)
        if str(rev.get("script", "")).strip(): script = rev; d["room_v2"]["revised_with"] = len(fixes)
    log(f"room v2: {len(ok)} drafts {[a for a, _ in ok]} -> jury chose '{chosen_arch}' {d['room_v2']['scores']}", episode=episode)
    verdict = {"verdict": "PASS", "scores": {"jury_borda": max(info["scores"])}, "fixes": {"checklist": fixes}, "room": "v2"}
    return script, verdict

# ---------------------------------------------------------------- the joke tournament (strong judges see EVERY candidate)
def _spoken(line):
    """(prefix, spoken text) of a script line; prefix keeps the speaker label and every bracket tag exactly."""
    m = re.match(r"^((?:\s*\[[^\]]*\]\s*)*(?:[A-Z][A-Z .'-]{1,24}:\s*)?(?:\s*\[[^\]]*\]\s*)*)(.*)$", line)
    return (m.group(1), m.group(2)) if m else ("", line)

def joke_slots(text, k):
    """Scene-ending spoken lines (the 'button' of each beat), spread over the episode, at most k."""
    lines = text.split("\n"); ends = []
    for i, l in enumerate(lines):
        if l.startswith("## BEAT") and i > 0:
            j = i - 1
            while j >= 0 and not _spoken(lines[j])[1].strip(): j -= 1
            if j >= 0 and len(_spoken(lines[j])[1].split()) >= 4: ends.append(j)
    if not ends: return []
    step = max(1, len(ends) // max(1, k))
    return ends[::step][:k]

def jokes(script, wbrief, episode):
    if not S("JOKE_TOURNAMENT_ON", bool): return script, {}
    from whatifs.models import ask
    text = script.get("script", ""); lines = text.split("\n")
    slots = joke_slots(text, S("JOKE_SLOTS", int))
    if not slots: return script, {"slots": 0}
    asks = [{"slot": str(i), "line": _spoken(lines[i])[1], "before": " ".join(_spoken(x)[1] for x in lines[max(0, i - 3):i])[-400:]} for i in slots]
    cand = ask("punchup", wbrief, f"For EACH slot write {S('JOKE_CANDIDATES', int)} alternative lines for the same speaker and moment: funnier, surprising, "
               "clear on one listen, punch word last, same facts. Return JSON only: {\"<slot>\": [\"line\", ...]}\nSLOTS: " + json.dumps(asks, ensure_ascii=False),
               episode=episode, fake_key="punchup", max_tokens=6000)
    changed = 0; detail = []
    for a in asks:
        alts = [str(x).strip() for x in (cand.get(a["slot"]) or []) if str(x).strip()][:S("JOKE_CANDIDATES", int)]
        if not alts: continue
        items = [a["line"]] + alts                                             # the original is always in the running
        win, info = jury(items, JOKE_RUBRIC, "Moment: " + a["before"], episode, "jokes", judges=JOKE_JURY, orders=1)
        if win != 0 and info["scores"][win] > info["scores"][0]:
            i = int(a["slot"]); pre, _ = _spoken(lines[i]); lines[i] = pre + items[win]; changed += 1
        detail.append({"slot": a["slot"], "won": win, "n": len(items)})
    if changed: log(f"joke tournament: {changed} of {len(asks)} lines improved", episode=episode)
    return dict(script, script="\n".join(lines)), {"slots": len(asks), "changed": changed, "detail": detail}
