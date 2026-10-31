"""whatifs/room.py v8.9 (rotating guest, next-episode tease, style lock; v8.7: packaging-first promise, retention gate, rhythm blueprint, sound cues, playbook rules; v8.6: routed lessons, promise shot) - the writers' room. Scout -> Showrunner -> department memos -> Production Bible -> Writer ->
Critic/Spectacle gate (Gemini, independent) -> one rewrite -> Director -> Packager -> Reel Producer -> Continuity check.
Fail-forward: 3 premise tries, then relax one step, then go. No human decision ever blocks."""
from __future__ import annotations
import json, re, random
from whatifs import prompts as P
from whatifs.models import ask, ask_many
from whatifs.core import store, log, S, scrub, set_setting, note_degraded
from whatifs.data import CRAFT, CRAFT_BY_ROLE
from whatifs import research as RS, tableread as TR, format_engine as FE, reactions as RX, cta as CTA
from whatifs.media import clean_graphic
from whatifs import growth as GR
from whatifs import playbook as PB
from whatifs import sound as SD

def _j(x, n=6000): s = json.dumps(x, ensure_ascii=False); return s[:n]

def context():
    st = store()
    banned = [r["phrase"] for r in st.rows("Banned")]
    eps = st.rows("Episodes")
    recent = [e.get("title") or e.get("premise") for e in eps[-25:]]
    tb = st.rows("Trend_Brief")[-40:]
    trends = [f'{r["kind"]}: {r["item"]} - {r["detail"]}' for r in tb]
    lrows = st.rows("Lessons")
    defs = {r["name"]: r["definition"] for r in st.rows("Strategies")}
    return {"banned": banned, "recent": recent, "trends": "\n".join(trends)[:5000] or "none yet",
            "lessons": GR.lessons_for("showrunner", 15, lrows), "lessons_packager": GR.lessons_for("packager", 12, lrows),
            "lessons_writer": GR.lessons_for("writer", 10, lrows), "lessons_reel": GR.lessons_for("reel", 10, lrows), "lessons_director": GR.lessons_for("director", 6, lrows), "defs": defs}      # v8.6: each department gets its own lessons

def _banned_hit(text, banned):
    t = text.lower(); return any(b.lower() in t for b in banned)

def _similar(a, recent):
    wa = set(re.findall(r"[a-z]{4,}", a.lower()))
    for r in recent:
        wb = set(re.findall(r"[a-z]{4,}", (r or "").lower()))
        if wa and wb and len(wa & wb) / len(wa | wb) > 0.5: return True
    return False

def seeds(k=12):
    fresh = [r for r in store().rows("Premises") if r.get("status") == "FRESH"]
    random.shuffle(fresh); return [r["premise"] for r in fresh[:k]]

def _family_ok(fam, recent_fams):
    if fam and fam in recent_fams[-3:]: return False
    if fam == "F12_everyone" and recent_fams[-5:].count("F12_everyone") >= 1: return False
    return True

def ai_tells(text):
    from whatifs.data import AI_TELLS
    t = text.lower(); return [w for w in AI_TELLS if w in t]

def scout_and_pick(draw, ctx, episode):
    from whatifs.data import FAMILIES
    recent_fams = [json.loads(e.get("draw_json") or "{}").get("family", "") for e in store().rows("Episodes")[-6:] if e.get("draw_json")]
    fams = {k: v[0] for k, v in FAMILIES.items()}
    for attempt in range(3):
        pit = ask("opus", P.fill(P.SCOUT, banned=ctx["banned"], recent=ctx["recent"], trends=ctx["trends"], seeds=seeds(),
                  families=json.dumps(fams), prefer=draw["strategies"].get("family") or "any", research=ctx.get("research", "")),
                  "Pitch now.", episode=episode, fake_key="scout", temperature=1.0)
        good = []
        for p in pit.get("pitches", []):
            sc = p.get("scores", {}); tot = sum(float(v) for v in sc.values()) if sc else 0
            if _banned_hit(p.get("premise", ""), ctx["banned"]) or _similar(p.get("premise", ""), ctx["recent"]): continue
            if not _family_ok(p.get("family"), recent_fams): continue
            if p.get("family") == draw["strategies"].get("family"): tot += 3
            p["total"] = tot; good.append(p)
        good.sort(key=lambda p: -p["total"])
        floor = [50, 45, 0][attempt]   # relax one step per try (fail-forward)
        good = [p for p in good if p["total"] >= floor]
        tz = teased_pitch(ctx, recent_fams)                       # v8.9: the last video promised this premise: it is the only pitch the Showrunner gets
        if tz: good = [tz] + [p for p in good if not _similar(p.get("premise", ""), [tz["premise"]])]; good = good[:1] + good[1:5]
        if good:
            tz_note = ("TEASED AT THE END OF OUR LAST VIDEO (viewers were promised it): the FIRST pitch. Choose it and keep its premise unless it breaks a channel rule." if tz else "")
            spine = ask("opus", FE.inject(GR.insert_before_json(P.fill(P.SHOWRUNNER, pitches=_j(good[:5]), draw=_j(draw), defs=_j({k: ctx["defs"].get(v, "") for k, v in draw["strategies"].items()}),
                        trends=ctx["trends"], lessons=ctx["lessons"], research=ctx.get("research", "")[:3000]), "\n".join(x for x in (PB.text_for("showrunner", draw.get("playbook")), tz_note) if x)), "showrunner"), "Choose and set the spine.", episode=episode, fake_key="showrunner")
            if spine.get("premise"):
                spine.setdefault("family", good[0].get("family", "")); spine.setdefault("headline", good[0].get("headline", spine["premise"]))
                if tz:          # v8.9.1 (fix): NOT cleared here any more. It is consumed only once this episode's plan is safely saved (episode.consume_tease),
                    spine["teased_premise"] = tz["premise"]         # so a failure while planning keeps the promise for the retry
                    spine["from_tease"] = _similar(spine.get("premise", ""), [tz["premise"]]) or spine.get("premise", "").strip().lower() == tz["premise"].strip().lower()
                spine["next_tease"] = clean_tease(spine, good)
                return spine
        log(f"scout attempt {attempt+1} gave no usable pitch", "WARN", episode)
    raise RuntimeError("scout failed 3 times")

def run_room(draw, episode):
    ctx = context(); d = draw; stg = d["strategies"]; defs = ctx["defs"]
    ctx["research"], d["research_brief"] = RS.room_research(episode)       # v7.4: audience research BEFORE topic selection (never blocks)
    spine = FE.enrich_spine(scout_and_pick(d, ctx, episode))
    spine["promise"] = GR.clean_promise(spine); d["promise"] = spine["promise"]       # v8.7: packaging first - the click promise is fixed BEFORE a word is written
    log(f"premise: {spine['premise']} | format: {spine.get('presentation_format', 'classic')}", episode=episode, public="premise chosen (text kept private until release)")
    roles = TR.ROLES
    arm, tmode = TR.active_arm(episode); d["table_read"] = {"mode": tmode, "arm": arm}      # recorded with the episode so the two arms can be compared later
    tr = TR.new_record(episode, arm, tmode)
    memos = ask_many([dict(role="sonnet", system=FE.inject(P.fill(P.MEMO, role=r, spine=_j(spine), draw=_j(d), trends=ctx["trends"][:2500],
                                                         research=ctx.get("research", "")[:2500], craft=CRAFT_BY_ROLE.get(r, "")), "memo"),
                           prompt="Memo now.", episode=episode, fake_key="memo", max_tokens=1200) for r in roles])
    memo_by_role = dict(zip(roles, memos))
    objections = "none (no table read this time)"
    if arm == "on":                                       # v8.0 optional table read: round 2, still before any image money is spent
        tr["objections"] = TR.objections_round(memo_by_role, spine, episode)
        objections = TR.objections_text(tr["objections"])
        log(f"table read: {len(tr['objections'])} objection(s) raised", episode=episode)
    bible = ask("opus", FE.inject(P.fill(P.BIBLE, spine=_j(spine), memos=_j(memo_by_role, 8000), draw=_j(d), objections=objections), "bible"),
                "Write the bible.", episode=episode, fake_key="bible")
    wmin, wmax = int(d["words"] * 0.93), int(d["words"] * 1.07)
    wbrief = P.fill(P.WRITER, words=d["words"], wmin=wmin, wmax=wmax, story=stg["story"], storydef=defs.get(stg["story"], ""),
                    hook=stg["hook"], hookdef=defs.get(stg["hook"], ""), hooksec=d["hook_sec"], humour=stg["humour"], voice=stg["voice"], bible=_j(bible, 9000),
                    banter=defs.get(stg.get("banter") or "", "") or "natural", budget=budget_brief(d))
    wbrief += f"\nHUMOUR SHARE: at most {int(round(S('HUMOUR_SHARE', float) * 100))}% of lines may be wit (setting HUMOUR_SHARE)."
    wbrief = FE.inject(wbrief, "writer")
    wbrief += ("\nRETENTION RULES: " + CRAFT["retention"] +                       # v8.6: the writer itself gets the retention rules and its own lessons
               "\nLESSONS FROM OUR OWN VIDEOS (opening, holding, hooks, reactions; follow them unless they contradict the bible): " + ctx["lessons_writer"])
    wbrief = GR.insert_before_json(wbrief, "\n".join(x for x in (                      # v8.7: the promise, this episode's rhythm and the research-graded rules
        "THE PROMISE (packaging first: the title and thumbnail were decided before you write; pay them off ON SCREEN and IN WORDS within the first 30 s): " + GR.promise_text(spine.get("promise")),
        GR.rhythm_brief(d.get("rhythm_plan"), defs), PB.text_for("writer", d.get("playbook")), guest_brief(d), tease_brief(spine)) if x))
    script = ask("sonnet", wbrief, "Write the narration.", episode=episode, fake_key="writer", max_tokens=16000)
    script = _fix_length(script, wbrief, wmin, wmax, episode)
    script = humanize(script, episode)
    script = format_pass(script, wbrief, episode)
    script, d["retention_check"] = retention_pass(script, wbrief, spine.get("promise"), episode)      # v8.7: opening + re-hooks checked by code, one fix at most
    verdict = critic(spine, script, ctx, episode)
    if verdict.get("verdict") != "PASS":
        log(f"critic asked for revision: {verdict.get('fixes')}", "WARN", episode, public="critic asked for a revision (details kept private)")
        rfix = GR.retention_issues(script.get("script", ""), spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops"))["issues"] if S("RETENTION_GATE_ON", bool) else []
        script = ask("sonnet", wbrief + "\nCRITIC FIXES (apply all): " + _j(verdict.get("fixes", {})) +
                     ("\nRETENTION FIXES STILL OPEN (apply them too; same call, no extra cost): " + " ".join(rfix) if rfix else ""), "Rewrite the full narration.",
                     episode=episode, fake_key="writer", max_tokens=16000)
        script = _fix_length(script, wbrief, wmin, wmax, episode)
        script = humanize(script, episode)
        script = format_pass(script, wbrief, episode)
        if S("RETENTION_GATE_ON", bool):      # the critic's rewrite is re-checked (recorded, no second paid fix)
            d["retention_check"]["after_rewrite"] = len(GR.retention_issues(script.get("script", ""), spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops"))["issues"])
        verdict = critic(spine, script, ctx, episode)
        if verdict.get("verdict") != "PASS":
            if min(verdict.get("scores", {}).get(k, 10) for k in ("policy_safe",)) < 7:
                raise RuntimeError("policy risk after rewrite - premise skipped")
            log("critic still unhappy after one rewrite - continuing (fail-forward)", "WARN", episode)
    script = fact_check(spine, script, episode)           # v8.3: search-grounded check of the claims, before any picture money is spent
    if S("CTA_ON", bool):                                 # v8.3: like / subscribe / share asks: the writer's own, or a hand-written one added at a calm moment
        new, added, code = CTA.ensure(script.get("script", ""), episode, S("CTA_LAST"))
        if added:
            script = dict(script, script=new); log(f"audience asks added by code: {', '.join(added)}", episode=episode)
        if code != S("CTA_LAST"): set_setting("CTA_LAST", code)
    script = ensure_tease(script, spine.get("next_tease"), episode); d["next_tease"] = spine.get("next_tease") or {}      # v8.9: the video ends on the next episode
    if arm == "on":                                       # the Director reads the FINAL script before shots are planned
        tr["director_notes"] = TR.director_notes(script.get("script", ""), bible.get("look", ""), episode)
        log(f"table read: Director gave {len(tr['director_notes'])} note(s)", episode=episode)
    if arm == "on": tr["status"] = "done"
    TR.save(tr)
    return {"spine": spine, "bible": bible, "script": script, "critic": verdict, "director_notes": tr["director_notes"], "table_read": {"arm": arm, "mode": tmode}}

# ---------------- v8.9: rotating guest + the next-episode tease ----------------
def guest_brief(d):
    from whatifs.data import GUESTS
    g = d.get("guest")
    if FE.mode() == "classic" or not S("GUEST_ROTATION_ON", bool) or g not in GUESTS: return ""
    return (f"TODAY'S GUEST (the Curious One this episode, still labelled [SKEPTIC]): {GUESTS[g][0]}. The Director welcomes them in ONE short line inside the first "
            "30 s (no greeting to the viewer, the show starts on the impossible thing); their everyday life shows up once as a concrete detail; same role as always "
            "(questions, doubts, honest reactions). An invented adult, never a real person, never a child.")

def tease_brief(spine):
    t = (spine or {}).get("next_tease") or {}
    if not S("NEXT_TEASE_ON", bool) or not t.get("line"): return ""
    return (f"END HOOK (the very last spoken line, after the share ask): the Director teases the NEXT simulation with this line or a sharper one that keeps its "
            f"premise: \"{t['line']}\". Make it a question or a stake the viewer wants answered. Never name a weekday or a date.")

TEASE_MAX_AGE_DAYS = 14

def teased_pitch(ctx, recent_fams):
    """The premise the previous video teased, as a pitch, if it still passes every channel rule (banned list, not too similar to recent titles, topic family
    spacing). None otherwise (then the NEXT_PREMISE cell is cleared, so a broken tease is never forced)."""
    if not S("NEXT_TEASE_ON", bool): return None
    raw = S("NEXT_PREMISE")
    if not str(raw or "").strip(): return None
    try: t = json.loads(raw)
    except Exception: t = {}
    pr = str(t.get("premise") or "").strip()
    from whatifs.core import parse_iso, now_utc
    at = parse_iso(t.get("set_at") or "")
    stale = bool(at) and (now_utc() - at).days > TEASE_MAX_AGE_DAYS            # v8.9.1: a promise nobody made for two weeks is dropped, never forced
    if stale or not pr or _banned_hit(pr, ctx["banned"]) or _similar(pr, ctx["recent"]) or not _family_ok(t.get("family"), recent_fams):
        set_setting("NEXT_PREMISE", ""); return None
    return {"premise": pr, "headline": t.get("headline") or pr, "family": t.get("family", ""), "ptype": t.get("ptype", ""), "teased": True,
            "scores": {"grasp": 9, "pull": 9}, "total": 999}

def clean_tease(spine, good):
    """The NEXT episode's premise + a spoken teaser line. The Showrunner's choice if it is a different family from this episode; otherwise the best other
    pitch of a different family. {} if there is none (then the video simply ends without a tease)."""
    if not S("NEXT_TEASE_ON", bool): return {}
    t = spine.get("next_tease") if isinstance(spine.get("next_tease"), dict) else {}
    fam = spine.get("family", "")
    ok = lambda x: str(x.get("premise") or "").strip() and x.get("family") != fam and not _similar(x.get("premise", ""), [spine.get("premise", "")])
    vetted = [p for p in good if not p.get("teased") and ok(p)]
    if ok(t) and not any(_similar(t.get("premise", ""), [p.get("premise", "")]) or str(t.get("premise", "")).strip().lower() == str(p.get("premise", "")).strip().lower() for p in vetted):
        t = {}            # v8.9.1 quality gate: the next episode must be one of today's VETTED, scored pitches (banned list, similarity, family spacing, score floor),
                          # never a premise the Showrunner invented on the spot; otherwise the best vetted pitch of another family is used
    if not ok(t):
        alt = vetted[0] if vetted else None
        if not alt: return {}
        t = {"premise": alt["premise"], "headline": alt.get("headline", alt["premise"]), "family": alt.get("family", ""), "ptype": alt.get("ptype", "")}
    line = re.sub(r"\s+", " ", str(t.get("line") or "")).strip() or f"Next simulation: {t.get('headline') or t['premise']}"
    return {"premise": str(t["premise"])[:200], "headline": str(t.get("headline") or t["premise"])[:90], "family": t.get("family", ""), "ptype": t.get("ptype", ""),
            "line": " ".join(line.split()[:24])}

def ensure_tease(script, tease, episode):
    """The tease must really be the last thing said. If the writer dropped it, code appends it as the Director's last line (free)."""
    if not tease or not tease.get("line") or not S("NEXT_TEASE_ON", bool): return script
    text = script.get("script", ""); tail = " ".join(text.strip().splitlines()[-3:]).lower()
    key = {w for w in re.findall(r"[a-z]{5,}", (tease.get("headline", "") + " " + tease.get("premise", "")).lower())}
    if key and len(key & set(re.findall(r"[a-z]{5,}", tail))) >= max(1, len(key) // 3): return script
    log("next-episode tease added by code as the last line", episode=episode)
    return dict(script, script=text.rstrip() + "\n[DIRECTOR] [callback] " + tease["line"])

def fact_check(spine, script, episode):
    """v8.3: an independent, search-grounded check of the script's factual claims (Gemini with Google Search; Claude's web search is the backup).
    'wrong' claims get ONE targeted rewrite by the human editor. If two or more stay wrong the premise is skipped BEFORE any picture money is spent;
    one leftover is noted in the episode notes. A checker that cannot be reached never blocks (the critic's science score still applies)."""
    if not S("FACT_CHECK_ON", bool): return script
    text = script.get("script", "")
    def run():
        rep = ask("research", P.fill(P.FACTCHECK, premise=spine.get("premise", ""), facts=_j(script.get("facts") or [], 3000), script=text[:24000]), "Check the facts now.",
                  search=True, episode=episode, fake_key="factcheck", temperature=0.1, max_tokens=4000)
        return [x for x in (rep.get("issues") or []) if isinstance(x, dict)] if isinstance(rep, dict) else []
    try: issues = run()
    except Exception as e:
        log(f"fact check unavailable ({scrub(e)[:120]}) - continuing without it", "WARN", episode); note_degraded("fact check was unavailable"); return script
    wrong = [x for x in issues if str(x.get("severity", "")).lower() == "wrong"]
    log(f"fact check: {len(issues)} note(s), {len(wrong)} judged wrong", episode=episode, public=f"fact check: {len(wrong)} claim(s) judged wrong (details kept private)")
    if not wrong: return script
    errs = "\n".join(f'- {str(x.get("claim", ""))[:200]} -> {str(x.get("correction", ""))[:260]}' for x in wrong[:6])
    try:
        out = ask("sonnet", P.fill(P.FACTFIX, errors=errs, script=text), "Fix the errors now.", episode=episode, fake_key="humanize", max_tokens=16000)
        new = out.get("script", "") if isinstance(out, dict) else ""
        old_n = len(re.sub(r"\[[^\]]+\]|##.*", "", text).split()); new_n = len(re.sub(r"\[[^\]]+\]|##.*", "", new).split())
        if new and new.count("## BEAT") >= max(1, text.count("## BEAT") - 1) and abs(new_n - old_n) <= old_n * 0.08 and FE.labels_preserved(text, new):
            script = dict(script, script=new); text = new
            try: issues = run()
            except Exception: issues = []
            wrong = [x for x in issues if str(x.get("severity", "")).lower() == "wrong"]
        else: log("fact fix rejected (it changed the structure) - keeping the draft", "WARN", episode)
    except Exception as e: log(f"fact fix skipped: {scrub(e)[:120]}", "WARN", episode)
    if len(wrong) >= 2: raise RuntimeError(f"fact check: {len(wrong)} claims still judged wrong after one fix - premise skipped before any picture money was spent")
    if wrong: note_degraded("1 claim could not be fully verified")
    return script

def retention_pass(script, brief, promise, episode):
    """v8.7: the first ~45 s and the re-hooks are CHECKED by code (growth.retention_issues: the promise shown and named, an open question, no throat-clearing,
    no stretch longer than REHOOK_MAX_GAP_SEC without a re-hook, a real turn near 3:00 and 6:00, every opened question answered). Problems = ONE targeted rewrite
    of only those spots (about Rs 4-8); it is kept only if the structure survives AND it has fewer problems. Never blocks: fail-forward. Returns (script, record)."""
    if not S("RETENTION_GATE_ON", bool): return script, {"checked": False}
    wpm = S("WPM_ESTIMATE", float); text = script.get("script", "")
    chk = GR.retention_issues(text, promise, wpm, script.get("loops"))
    rec = {"checked": True, "before": len(chk["issues"]), "after": len(chk["issues"]), "max_gap": chk["max_gap"], "fixed": False}
    if chk["ok"]: return script, rec
    log(f"retention gate: {len(chk['issues'])} problem(s): {' | '.join(chk['issues'])[:700]} - asking the writer for one targeted fix", "WARN", episode,
        public=f"retention gate: {len(chk['issues'])} problem(s), one targeted fix requested (details kept private)")
    try:
        out = ask("sonnet", brief, "Fix ONLY these retention problems, at the places named, and change nothing else: " + " ".join(f"({k + 1}) {x}" for k, x in enumerate(chk["issues"])) +
                  " Keep every speaker label, delivery tag, '## BEAT' line, fact, number and the three audience asks; keep the length within 5 percent. Return the full narration.\nNARRATION:\n" + text,
                  episode=episode, fake_key="retention", max_tokens=16000)
        new = out.get("script", "") if isinstance(out, dict) else ""
        old_n = len(re.sub(r"\[[^\]]+\]|##.*", "", text).split()); new_n = len(re.sub(r"\[[^\]]+\]|##.*", "", new).split())
        if new and new.count("## BEAT") >= max(1, text.count("## BEAT") - 1) and abs(new_n - old_n) <= old_n * 0.08 and FE.labels_preserved(text, new):
            chk2 = GR.retention_issues(new, promise, wpm, out.get("loops") or script.get("loops"))
            if len(chk2["issues"]) < len(chk["issues"]):
                script = dict(script, script=new); rec.update(after=len(chk2["issues"]), max_gap=chk2["max_gap"], fixed=True)
                if out.get("loops"): script["loops"] = out["loops"]
                log(f"retention gate: fix accepted ({len(chk['issues'])} -> {len(chk2['issues'])} problems)", episode=episode)
            else: log("retention fix did not reduce the problems - keeping the draft", "WARN", episode)
        else: log("retention fix rejected (it changed the structure) - keeping the draft", "WARN", episode)
    except Exception as e: log(f"retention fix skipped: {scrub(e)[:160]}", "WARN", episode)
    return script, rec

def _sound_cap(draw, n):
    """How many shots in a Director chunk may carry a sound texture (the episode's sound density)."""
    return max(1, int(round(n * SD.DENSITY[SD.density_of((draw.get("strategies") or {}).get("sound"))])))

def _director_extra(draw):
    """v8.7: the rhythm blueprint's visual side, the research-graded rules for the Director, and the Director's own lessons."""
    from whatifs.data import INTERRUPTS
    rp = draw.get("rhythm_plan") or {}
    out = (f"\nRHYTHM: pattern interrupt = {INTERRUPTS.get(rp.get('interrupt'), rp.get('interrupt') or 'none')}; music arc = {rp.get('arc', 'still')}; "
           "plan one held, near-silent shot right before each peak (the music drops out there).") if rp else ""
    pb = PB.text_for("director", draw.get("playbook"))
    les = context().get("lessons_director", "none yet")
    return out + ("\n" + pb if pb else "") + ("\nDIRECTOR LESSONS FROM OUR OWN VIDEOS: " + les if les and les != "none yet" else "")

def budget_brief(d):
    """The numbers the code chose for THIS episode, in plain words, so the writers and the Director plan inside them instead of being trimmed afterwards."""
    b = d.get("budget") or {}
    if not b: return "none"
    run = d.get("runtime_sec", 0)
    return (f"Tier '{b.get('tier', 'full')}'. Target runtime {run // 60}:{run % 60:02d} (never below 8:25, never above 10:00). New paid pictures: about {d.get('stills', 0)} stills, "
            f"{d.get('living', 0)} living stills, {d.get('kling', 0)} Kling clips (the Kling clips are the big payoffs; they are never cut). Plan the beats so the explanation runs on FREE shots "
            "(code-drawn counters, timelines, comparisons, real stock footage, reused pictures with new crops) and spend pictures on consequences and peaks. The viewer must never feel a shortage.")

def format_pass(script, brief, episode):
    """v8.1: the two-role format is CHECKED by code. If labels are missing or one role barely speaks, the writer gets ONE targeted fix request.
    The structure (beats, length) must survive it; otherwise the first draft is kept. Never blocks: fail-forward with a warning."""
    if not S("FORMAT_GATE_ON", bool): return script
    chk = FE.check_script(script.get("script", ""))
    if chk["ok"]: return script
    log(f"format check: {'; '.join(chk['issues'])} - asking the writer for one fix", "WARN", episode, public="format check asked for a fix (details kept private)")
    try:
        out = ask("sonnet", brief, "Fix ONLY the speaker format of this narration. " + " ".join(chk["issues"]) + " Give each dialogue line a label [DIRECTOR] or [SKEPTIC] (label first, then the delivery tag), "
                  "make the Curious One question assumptions and push consequences (never empty agreement), keep every beat, fact, number and '## BEAT' line, keep the length within 5 percent.\nNARRATION:\n" + script.get("script", ""),
                  episode=episode, fake_key="writer", max_tokens=16000)
        new = out.get("script", "")
        old_words = len(re.sub(r"\[[^\]]+\]|##.*", "", script.get("script", "")).split()); new_words = len(re.sub(r"\[[^\]]+\]|##.*", "", new).split())
        if new and new.count("## BEAT") >= max(1, script.get("script", "").count("## BEAT") - 1) and abs(new_words - old_words) <= old_words * 0.08 and FE.check_script(new)["labeled"] > chk["labeled"]:
            return dict(script, script=new)
    except Exception as e: log(f"format fix skipped: {scrub(e)}", "WARN", episode)
    log("format check still not satisfied - continuing (fail-forward); the narrator voice covers unlabeled lines", "WARN", episode)
    return script

def humanize(script, episode):
    """Human Editor pass, repeated once if AI tells remain. Keeps the old draft if the edit breaks structure."""
    for _ in range(2):
        out = ask("sonnet", P.fill(P.HUMANIZE, script=script.get("script", ""), craft=CRAFT["humanize"]), "Edit now.", episode=episode, fake_key="humanize", max_tokens=16000)
        new = out.get("script", "")
        old_n = len(script.get("script", "").split()); new_n = len(new.split())
        if new and new.count("## BEAT") >= max(1, script.get("script", "").count("## BEAT") - 1) and abs(new_n - old_n) <= old_n * 0.12 and FE.labels_preserved(script.get("script", ""), new):
            script = dict(script, script=new)
        tells = ai_tells(script.get("script", ""))
        if len(tells) <= 2: break
        log(f"AI phrases still present {tells} - second human pass", "WARN", episode)
    return script

def extend(room, script_text, add_words, episode):
    out = ask("sonnet", P.fill(P.HUMANIZE, script=script_text, craft=CRAFT["humanize"]),
              f"The narration is too short. Keep everything and ADD about {add_words} words: deepen the strongest beats with one more concrete consequence each, "
              "keep the same tags and '## BEAT' lines. Return the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
    s = out.get("script", "")
    return s if len(s.split()) > len(script_text.split()) and FE.labels_preserved(script_text, s) else None

def _fix_length(script, brief, wmin, wmax, episode):
    n = len(re.sub(r"\[[^\]]+\]|##.*", "", script.get("script", "")).split())
    if wmin <= n <= wmax: return script
    log(f"script length {n} outside {wmin}-{wmax}, adjusting", "WARN", episode)
    adj = ask("sonnet", brief, f"Your draft has {n} words. Rewrite it to {(wmin+wmax)//2} words, same structure:\n" + script.get("script", ""),
              episode=episode, fake_key="writer", max_tokens=16000)
    return adj if adj.get("script") and FE.labels_preserved(script.get("script", ""), adj["script"]) else script

def critic(spine, script, ctx, episode):
    v = ask("critic", FE.inject(P.fill(P.CRITIC, recent=ctx["recent"], episode=_j({"spine": spine, "script": script.get("script", "")}, 30000)), "critic"),
            "Judge now.", episode=episode, fake_key="critic", temperature=0.2)
    sc = v.get("scores", {})
    vals = [float(x) for x in sc.values()] if sc else [0]
    tells = ai_tells(script.get("script", ""))
    ok = (sum(vals) / len(vals) >= 7.0 and sc.get("policy_safe", 0) >= 8 and sc.get("humour_cringe_free", 0) >= 6 and sc.get("hook_strength", 0) >= 7
          and sc.get("sounds_human", 7) >= 7 and sc.get("psychological_pull", 7) >= 7 and sc.get("science_plausible", 8) >= 8 and len(tells) <= 2)
    if tells: v.setdefault("fixes", {})["writer"] = (v.get("fixes", {}).get("writer", "") + f" Remove AI phrases: {tells}.").strip()
    v["verdict"] = "PASS" if ok else "REVISE"    # computed here: the model's own verdict word is never trusted alone
    v["mean"] = round(sum(vals) / len(vals), 2)
    return v

def plan_shots(room, units, draw, plan, episode):
    look = room["bible"].get("look", "cinematic, deep shadows, single cold key light, fine film grain")
    size = 40; chunks = [units[i:i + size] for i in range(0, len(units), size)]; n = len(chunks); peaks = RX.peak_units(units)
    jobs = []; extra = _director_extra(draw)      # v8.7: computed once per shot list
    for k, ch in enumerate(chunks):
        kl = plan["kling"] // n + (1 if k < plan["kling"] % n else 0); lv = plan["living"] // n + (1 if k < plan["living"] % n else 0)
        U = "\n".join(f'{u["i"]}: ({str(u.get("speaker", "N"))[:1]}/{u.get("tag", "none")}) {u["text"]}' for u in ch)
        allow = max(1, round(draw.get("stills", 40) * len(ch) / max(1, len(units))))
        pk = [i for i in peaks if ch[0]["i"] <= i <= ch[-1]["i"]]
        jobs.append(dict(role="sonnet", system=FE.inject(P.fill(P.DIRECTOR, nshots=len(ch), kling=kl, living=lv, ptype=draw["ptype"], look=look, units=U, budget=budget_brief(draw), allow=allow, peaks=pk or "none",
                                           notes=(TR.notes_text(room.get("director_notes", [])) + "\nPRODUCTION BIBLE: " + _j(room.get("bible", {}), 4500) + "\nEPISODE SPINE: " + _j(room.get("spine", {}), 1800) + extra), sounds=_sound_cap(draw, len(ch))), "director"),
                         prompt=f"Shot list for units {ch[0]['i']}-{ch[-1]['i']} (use these exact unit numbers).", episode=episode, fake_key="director", max_tokens=8000))
    shots = []
    for res in ask_many(jobs, workers=3): shots += res.get("shots", [])
    return normalise_shots(shots, units, plan, look, peaks)

def normalise_shots(shots, units, plan, look, peaks=()):
    """Make the shot list safe: one shot per unit, caps enforced, peak gets kling, prompts present."""
    by = {}
    for s in shots:
        try: by.setdefault(int(s.get("unit", -1)), s)
        except Exception: pass
    out = []
    for u in units:
        s = dict(by.get(u["i"]) or {"type": "still", "prompt": u["text"]})
        s["unit"] = u["i"]; s["type"] = s.get("type") if s.get("type") in ("still", "living", "kling", "stock", "graphic") else "still"
        if s["type"] in ("still", "living", "kling") and not s.get("prompt"): s["prompt"] = u["text"]
        if s["type"] == "stock" and not s.get("search"): s["type"] = "still"; s["prompt"] = s.get("prompt") or u["text"]
        if s["type"] == "graphic":
            g = clean_graphic(s.get("graphic"))
            if g is None: s["type"] = "still"; s["prompt"] = u["text"]; s.pop("graphic", None)
            else: s["graphic"] = g
        cam = str(s.get("camera") or "").strip().lower(); s.pop("camera", None)      # v8.9: keep only a camera move from the library (a hint; render.pick_move has the last word)
        if cam and s["type"] in ("still", "living"):
            from whatifs.render import CAMERA_MOVES
            if cam in CAMERA_MOVES: s["camera"] = cam
        s["hero"] = bool(s.get("hero")); s["focus"] = s.get("focus") if s.get("focus") in ("wide", "left", "right", "center", "top", "bottom") else "wide"
        if out and s["type"] == "graphic" and out[-1]["type"] == "graphic": s["type"] = "still"; s["prompt"] = s.get("prompt") or u["text"]      # never two graphics in a row
        if s.get("prompt") and look not in s["prompt"]: s["prompt"] = s["prompt"].rstrip(". ") + ". " + look
        lock = str(S("STYLE_LOCK") or "").strip()                     # v8.9: one locked dark cinematic style on every in-video picture and clip
        if s.get("prompt") and lock and lock not in s["prompt"]: s["prompt"] = s["prompt"].rstrip(". ") + ". " + lock
        out.append(s)
    for typ, cap in (("kling", plan["kling"]), ("living", plan["living"])):
        idx = [i for i, s in enumerate(out) if s["type"] == typ]
        for i in idx[cap:]: out[i]["type"] = "still"
        need = cap - len(idx[:cap])
        if need > 0:        # the big shots go on the units right BEFORE a reaction line (the viewer sees it, then the Curious One reacts)
            pk = [i for i in peaks if i < len(out) and out[i]["type"] == "still"]
            pick = (pk if len(pk) <= need else [pk[int(k * len(pk) / need)] for k in range(need)])[:need]
            if len(pick) < need:
                rest = [i for i, s in enumerate(out) if s["type"] == "still" and i not in pick and units[i]["tag"] in ("reveal", "tension")] or \
                       [i for i, s in enumerate(out) if s["type"] == "still" and i not in pick]
                step = max(1, len(rest) // max(1, need - len(pick) + 1)); pick += rest[step - 1::step][: need - len(pick)]
            for i in pick: out[i]["type"] = typ
    return front_load(out, units, peaks)

def promise_shot(shots, units, pkg):
    """v8.6 (MrBeast-guide principle: the first minute must prove the thumbnail's promise): the first Kling clip inside the opening window is re-aimed at the
    thumbnail's scene, so the image that earned the click moves on screen within ~45 s. Same clip count, same cost. No Kling in the opening = unchanged."""
    tp = str((pkg or {}).get("thumb_prompt") or "").strip()
    if not tp or not S("PROMISE_SHOT_ON", bool): return shots
    for i in opening_units(units):
        if i < len(shots) and shots[i].get("type") == "kling":
            s = dict(shots[i]); s["prompt"] = f"{tp}; {str(s.get('prompt') or units[i]['text'])[:160]}"; s["promise"] = True; s["hero"] = True
            lock = str(S("STYLE_LOCK") or "").strip()
            if lock and lock not in s["prompt"]: s["prompt"] = s["prompt"].rstrip(". ") + ". " + lock      # v8.9: the style lock survives the re-aim
            out = list(shots); out[i] = s; return out
    return shots

def opening_units(units, win=None):
    """v8.5: indexes of the units that START inside the opening window (the seconds that decide whether a viewer stays)."""
    win = S("OPENING_WINDOW_SEC", float) if win is None else win
    if win <= 0: return []
    out = []
    for i, u in enumerate(units):
        try:
            if float(u.get("start")) < win: out.append(i)
        except Exception: pass
    return out

def front_load(out, units, peaks=()):
    """v8.5: viewers decide in the first ~45 s, and the even spread put the first Kling clip around minute 2-3. MOVE (never add) motion into the opening:
    at least OPENING_KLING_MIN Kling clips and OPENING_LIVING_MIN living stills start inside OPENING_WINDOW_SEC. Donors are the clips that are NOT on a
    peak (the shot before a reaction keeps its clip), latest first. Receivers are opening stills, reveal / tension lines first. Same counts = same cost."""
    opening = [i for i in opening_units(units) if i < len(out)]
    if not opening: return out
    pk = set(peaks or ())
    for typ, want in (("kling", S("OPENING_KLING_MIN", int)), ("living", S("OPENING_LIVING_MIN", int))):
        total = [i for i, s in enumerate(out) if s["type"] == typ]
        need = min(max(0, want), len(total)) - sum(1 for i in opening if out[i]["type"] == typ)
        if need <= 0: continue
        donors = sorted([i for i in total if i not in opening], key=lambda i: (i in pk, -i))
        takers = sorted([i for i in opening if out[i]["type"] == "still"], key=lambda i: (units[i].get("tag") not in ("reveal", "tension", "awe"), i))
        for d, r in zip(donors[:need], takers[:need]):
            out[d]["type"] = "still"; out[r]["type"] = typ
            out[r]["prompt"] = out[r].get("prompt") or units[r]["text"]
            if typ == "kling": out[r]["hero"] = True; out[r]["motion"] = out[r].get("motion") or "slow dramatic push in, the impossible thing moving"
    return out

def package(room, chapters, draw, episode):
    ctx = context(); stg = draw["strategies"]
    excerpt = room["script"].get("script", "")[:3500]
    pkg = ask("sonnet", FE.inject(GR.insert_before_json(P.fill(P.PACKAGER, title=stg["title"], titledef=ctx["defs"].get(stg["title"], ""), thumb=stg["thumb"],
               thumbdef=ctx["defs"].get(stg["thumb"], ""), spine=_j(room["spine"]), excerpt=excerpt, trends=ctx["trends"][:3000],
               lessons=ctx["lessons_packager"], chapters=_j(chapters), craft=CRAFT["packager"], promise=GR.promise_text(room["spine"].get("promise"))),
               PB.text_for("packager", draw.get("playbook"))), "packager"), "Package now.", episode=episode, fake_key="packager")
    pt = str((room["spine"].get("promise") or {}).get("title") or "").strip()       # v8.7: the promise title is always a candidate (it wins only if the Packager's are flawed)
    if isinstance(pkg, dict) and pt and pt.lower() not in [str(t).lower() for t in pkg.get("titles") or []]: pkg["titles"] = list(pkg.get("titles") or []) + [pt]
    return pkg

def reel_count(): return max(2, min(4, S("REELS_PER_VIDEO", int)))
def reel_style():
    """v8.5: bridge (default) | standalone | teaser. Anything unknown is read as bridge (same rule as reels.reel_style)."""
    from whatifs.reels import reel_style as _rs
    return _rs()

def reels(room, shots, draw, episode):
    ctx = context(); n = reel_count()
    S_ = "\n".join(f'{i}: {s["type"]}: {(s.get("prompt") or s.get("search") or "")[:90]}' for i, s in enumerate(shots))
    fm = draw["reel_formats"]
    style = {"bridge": P.REEL_STYLE_BRIDGE, "standalone": P.REEL_STYLE_STANDALONE, "teaser": P.REEL_STYLE_TEASER}[reel_style()]
    r = ask("sonnet", FE.inject(GR.insert_before_json(P.fill(P.REEL, n=n, style=style, formats=fm, formatdefs=_j({f: ctx["defs"].get(f, "") for f in fm}), shots=S_[:12000],
            spine=_j(room["spine"]), trends=ctx["trends"][:2000], craft=CRAFT["reel"], lessons=ctx["lessons_reel"]), PB.text_for("reel", draw.get("playbook"))), "reels"), f"Make the {n} reels.", episode=episode, fake_key="reel",
            max_tokens=6000 + 1500 * (n - 2)).get("reels", [])
    good = []
    for x in r[:n]:
        sh = [int(i) for i in x.get("shots", []) if str(i).isdigit() and int(i) < len(shots)]
        kl = [i for i in sh if shots[i]["type"] == "kling"]
        sh = [i for i in sh if shots[i]["type"] != "kling"] + kl[:1]
        if len(sh) >= 4 and x.get("lines"): x["shots"] = sh; good.append(x)
    return good

def continuity(pkg, episode):
    try:
        v = ask("critic", FE.inject(P.fill(P.SYNC, pkg=_j(pkg, 40000)), "continuity"), "Check now.", episode=episode, fake_key="sync", temperature=0.1)
        return v
    except Exception as e:
        log(f"continuity check skipped: {scrub(e)}", "WARN", episode); return {"ok": True, "problems": []}

