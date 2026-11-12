"""Writers' room v1 and the shared room steps: scout, showrunner, production bible, writer, critic and policy-safety gate, promise shot. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, hashlib, re, random
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

def SHOW_ON():
    from whatifs import show as SHOW
    return SHOW.on()

def _show_writer(spine):
    """v9: the trial brief for the writer (the validated Show Plan + the cast + the tag rules). '' when SHOW_MODE = off or no plan."""
    from whatifs import show as SHOW
    return SHOW.writer_brief(spine.get("show_plan")) if SHOW.on() and spine.get("show_plan") else ""

def V91_on(flag):
    from whatifs import v91 as V91
    return V91.on(flag)

def _pkg_extra():
    """v9: hook shapes + three title/thumbnail pairs for the packager ('' when SHOW_MODE = off). Packaging tests belong to every format (v12 V2a)."""
    from whatifs import show as SHOW
    if not SHOW.leads_on(): return ""
    from whatifs import packaging as PK
    recent = []
    for r in store().rows("Experiments")[-2:]: recent.append(r.get("hook_shape"))
    return (PK.hook_shape_brief(recent) + "\n" + (PK.TITLE_BRIEF if V91_on("TITLE_SHOCK_ON") else "") + "\nALSO return \"titles\": [2 more titles, each a DIFFERENT angle], \"thumb_text_b\" and \"thumb_text_c\" (1-4 words each, "
            "adding to their title, never repeating it). Captions and catchphrases: plain words that auto-translate well (no puns that only work in English).")

def _reel_extra(room):
    """v9: the Shorts trilogy + the clip-bait Short ('' when SHOW_MODE = off)."""
    from whatifs import show as SHOW
    if not SHOW.on(): return ""
    if S("TRIAL_SHORTS_SAFE_ON", bool):                          # v9.3: a cold Shorts viewer has never met the cast, and a Short must never spend the episode's payoff
        return ("SHORTS FOR THE TRIAL (a Shorts viewer has never met the cast: every reel must work without them): line 1 of EVERY reel puts YOU inside the "
                "impossible situation (second person, present tense, a stake, a clock or a number) before any character name or courtroom word. reel 1 = the "
                "cold open's stake as a cliffhanger (stop right before the answer); reel 2 = Dr. Grimm's strongest objection against Vale's best evidence, cut "
                "BEFORE anyone wins; reel 3 = the surprise witness's twist, stopped before what it proves; reel 4 = the clip-bait moment (its lines are inserted "
                "by code). NEVER reveal the verdict, who wins, the final Jury Meter side or the final answer in any reel: the full episode keeps the payoff, and "
                "each reel's end line names the open question only the full case answers. Plain words that auto-translate well.")
    return ("SHORTS FOR THE TRIAL: reel 1 = THE CHARGE as a cliffhanger (stop before the verdict); reel 2 = the VERDICT reaction (Grimm or Vale reacting); "
            "reel 3 = a character rant (Dr. Grimm's best objection, theatrical, never cruel); reel 4 = the clip-bait moment (its lines are inserted by code). "
            "Plain words that auto-translate well.")

def _format_block(role):
    """v12 V2a: the format's own text for a room role ('' for the trial, whose brief is the Show Plan's, and when no format is set)."""
    from whatifs import formats as FMT
    return FMT.block(role)

def _show_block():
    """v9: the Show Plan request inside the existing Showrunner call ('' when SHOW_MODE = off, so the prompt is exactly v8.11's)."""
    from whatifs import show as SHOW
    return SHOW.prompt_block() if SHOW.on() else ""

def scout_and_pick(draw, ctx, episode):
    """v8.10: the scout pitches; with PREMISE_DUAL_SCORE_ON two BLIND judges (Claude + Gemini) score every pitch on the owner's criteria, calibrated with the
    owner's taste examples; only pitches at or above PREMISE_MIN_SCORE go to the Showrunner. Nothing passes = fresh seeds (PREMISE_RETRY_ROUNDS).
    v8.11: (1) the PREMISE_BENCH is tried first (pre-scored premises that already passed both judges: no scout call at all);
    (2) still nothing above the bar after every round = the BEST-scoring pitch is used, all scores kept, the owner emailed once (spine['below_bar']);
    SKIP_IF_BELOW_BAR = TRUE restores the v8.10 skip (premise.SkipSlot). PREMISE_FAIL_FORWARD = TRUE restores the v8.9 floors (50 / 45 / 0)."""
    from whatifs.data import FAMILIES, TASTE_LIKED, TASTE_BORING, TASTE_NOTE
    from whatifs import premise as PR, craft as CR
    recent_fams = [json.loads(e.get("draw_json") or "{}").get("family", "") for e in store().rows("Episodes")[-6:] if e.get("draw_json")]
    fams = {k: v[0] for k, v in FAMILIES.items()}
    dual = S("PREMISE_DUAL_SCORE_ON", bool); ff = S("PREMISE_FAIL_FORWARD", bool); skip = S("SKIP_IF_BELOW_BAR", bool)
    if S("PREMISE_BANK_ON", bool) and S("BACKGROUND_IN_ROOM", bool): PR.regenerate_bank(episode=episode)      # v9.2: monthly bank = the learning job only
    rounds = 3 if ff or not dual else 1 + max(0, S("PREMISE_RETRY_ROUNDS", int)); used = []; best_seen = 0.0; pool = []
    taste = ("\nTASTE CALIBRATION (the owner's own examples): LIKED: " + json.dumps(TASTE_LIKED) + " BORING: " + json.dumps(TASTE_BORING) + " " + TASTE_NOTE +
             "\nAlso score: illogical-sounding but physically showable in FIRST PERSON with our pictures; headline 4-11 words.\n" + CR.brief("scout"))
    try:
        from whatifs import viewers as VW; taste += VW.scout_block()                     # v10.1 (K147): viewer questions as premise DATA
        from whatifs import owner_brief as OB2; taste += OB2.taste_block()                # v10.3 (K154): the owner's measured winners
    except Exception: pass
    past = [e.get("premise") or e.get("title") for e in store().rows("Episodes") if e.get("premise") or e.get("title")]

    def same(a, b): return _similar(a, [b]) or str(a).strip().lower() == str(b).strip().lower()

    def showrun(good, tz, below=None):
        """The Showrunner chooses among vetted pitches and sets the spine. None when it returns no premise."""
        tz_note = ("THE OWNER'S DECISION (discussed and locked with him): the FIRST pitch. Choose it and keep its premise." if tz and tz.get("owner") else
                   "PROVEN WITH REAL VIEWERS: the FIRST pitch is the topic of our Short that real viewers stayed for. Choose it and keep its premise word for word; "
                   "the other pitches are only candidates for the tease of the next case." if tz and tz.get("ladder") else
                   "TEASED AT THE END OF OUR LAST VIDEO (viewers were promised it): the FIRST pitch. Choose it and keep its premise unless it breaks a channel rule." if tz else "")
        spine = ask("showrunner", FE.inject(GR.insert_before_json(P.fill(P.SHOWRUNNER, pitches=_j(good[:5]), draw=_j(draw), defs=_j({k: ctx["defs"].get(v, "") for k, v in draw["strategies"].items()}),
                    trends=ctx["trends"], lessons=ctx["lessons"], research=ctx.get("research", "")[:3000]), "\n".join(x for x in (PB.text_for("showrunner", draw.get("playbook")), tz_note, CR.brief("showrunner"), _show_block(), _format_block("showrunner")) if x)), "showrunner"), "Choose and set the spine.", episode=episode, fake_key="showrunner")
        if not spine.get("premise"): return None
        if tz and tz.get("ladder"):                                 # v12 V2c-b: the promoted Short's premise is kept word for word BY CODE (check topic_ladder compares them)
            spine["premise"] = tz["premise"]; spine["ladder"] = tz["ladder"]; spine["headline"] = spine.get("headline") or tz.get("headline") or tz["premise"]
        from whatifs import show as SHOW
        spine = SHOW.apply_to_spine(spine, episode)                # v9: Show Plan validated + logged (shadow in stage 1); off = no-op
        from whatifs import formats as FMT
        if not FMT.show_allowed(): spine.pop("show_plan", None)      # v12 V2a: a format that is not a trial carries no Show Plan, whatever the model returned
        if dual and not tz and not any(same(spine["premise"], p.get("premise", "")) for p in good):
            log("the Showrunner's premise was not one of the scored pitches - the top scored pitch is used instead", "WARN", episode)
            spine["premise"] = good[0]["premise"]; spine["headline"] = good[0].get("headline", good[0]["premise"]); spine["family"] = good[0].get("family", "")
        spine.setdefault("family", good[0].get("family", "")); spine.setdefault("headline", good[0].get("headline", spine["premise"]))
        if dual:
            hit = next((p for p in good if same(spine["premise"], p.get("premise", ""))), good[0])
            spine["premise_score"] = hit.get("combined"); PR.mark_chosen(episode, hit.get("premise", ""))
            if hit.get("bench_id"):
                PR.bench_mark_used(episode, hit.get("premise", "")); spine["from_bench"] = True
                spine["premise_source"] = hit.get("src", "original")
                if hit.get("demand_evidence") and isinstance(spine.get("show_plan"), dict): spine["show_plan"]["demand_evidence"] = hit["demand_evidence"]
        if tz and not tz.get("ladder"):          # v8.9.1 (fix): NOT cleared here any more. It is consumed only once this episode's plan is safely saved (episode.consume_tease),
            spine["teased_premise"] = tz["premise"]         # so a failure while planning keeps the promise for the retry
            spine["from_tease"] = same(spine.get("premise", ""), tz["premise"])
        if below: spine["below_bar"] = below
        spine["next_tease"] = clean_tease(spine, good)
        return spine

    from whatifs import ladder as LAD                           # v12 V2c-b: every topic starts as a Short - the promoted Short's topic is THE pitch
    lad = None if str(S("OWNER_NEXT_PREMISE") or "").strip() else LAD.pitch()      # the owner's own locked topic comes first (his override is on the ladder's record)
    if lad:
        if dual: PR.score([lad], ctx["recent"] + past[-20:], episode)            # the judges' score is recorded, never a bar: real viewers chose this topic
        nxt = [p for p in LAD.runner_ups() + PR.bench_pitches(ctx["banned"], ctx["recent"], past, lambda f: _family_ok(f, recent_fams), k=3) if not same(p["premise"], lad["premise"])]
        if dual: PR.log_scores([lad], episode, "ladder", "ladder")
        spine = showrun([lad] + nxt[:4], lad)
        if not spine: raise RuntimeError("the Showrunner returned no spine for the promoted topic")
        log(f"premise taken from the ladder: the topic of Short {lad['ladder']} (promoted by its real numbers)", episode=episode); return spine
    if dual and S("PREMISE_BENCH_ON", bool):                     # v8.11: the bench first (already judged; the code rules are re-checked today)
        from whatifs import owner_brief as OB
        tz = OB.take_for_episode(episode) or teased_pitch(ctx, recent_fams)          # v10.3 (K154): the owner's locked brief comes first
        bench = PR.bench_pitches(ctx["banned"], ctx["recent"], past, lambda f: _family_ok(f, recent_fams))
        if tz:
            PR.score([tz], ctx["recent"] + past[-20:], episode)
            if tz.get("combined", 0) < S("PREMISE_MIN_SCORE", float) and not tz.get("owner"):
                log("the teased premise did not reach the quality bar - dropped (quality over the promise)", "WARN", episode); set_setting("NEXT_PREMISE", ""); tz = None
        if bench:
            good = ([tz] if tz else []) + [p for p in bench if not (tz and same(p["premise"], tz["premise"]))]
            PR.log_scores(good, episode, "bench", "bench")
            spine = showrun(good[:5], tz)
            if spine: log(f"premise taken from the Premise_Bench ({len(bench)} ready)", episode=episode); return spine
    for attempt in range(rounds):
        sd = PR.seeds(12, attempt, used) if S("PREMISE_BANK_ON", bool) else seeds(); used += sd
        pit = ask("scout", GR.insert_before_json(P.fill(P.SCOUT, banned=ctx["banned"], recent=ctx["recent"], trends=ctx["trends"], seeds=sd,
                  families=json.dumps(fams), prefer=draw["strategies"].get("family") or "any", research=ctx.get("research", "")), taste),
                  "Pitch now." + (" Completely new directions: the earlier pitches were not strong enough." if attempt else ""), episode=episode, fake_key="scout", temperature=1.0)
        good = []
        for p in pit.get("pitches", []):
            sc = p.get("scores", {}); tot = sum(float(v) for v in sc.values()) if sc else 0
            if _banned_hit(p.get("premise", ""), ctx["banned"]) or _similar(p.get("premise", ""), ctx["recent"]) or _similar(p.get("premise", ""), past): continue
            if not _family_ok(p.get("family"), recent_fams): continue
            if p.get("family") == draw["strategies"].get("family"): tot += 3
            p["total"] = tot; good.append(p)
        tz = teased_pitch(ctx, recent_fams)                       # v8.9: the last video promised this premise
        if dual:
            if tz: good = [tz] + [p for p in good if not _similar(p.get("premise", ""), [tz["premise"]])]
            PR.score(good, ctx["recent"] + past[-20:], episode)
            for p in good: p["total"] = p.get("combined", 0) * 10 + (2 if p.get("family") == draw["strategies"].get("family") else 0)
            best_seen = max([best_seen] + [p.get("combined", 0) for p in good])
            pool += [p for p in good if not p.get("teased")]
            passed = [p for p in good if p.get("combined", 0) >= S("PREMISE_MIN_SCORE", float)]
            if tz and tz not in passed:
                log("the teased premise did not reach the quality bar - dropped (quality over the promise)", "WARN", episode); set_setting("NEXT_PREMISE", ""); tz = None
            if ff and not passed and attempt == rounds - 1: passed = good          # v8.9 fail-forward, only when the owner switched it back on
            PR.log_scores(good, episode, attempt, "scout")
            good = sorted(passed, key=lambda p: -p["total"])
            if tz: good = [tz] + [p for p in good if p is not tz]
            good = good[:5]
        else:
            good.sort(key=lambda p: -p["total"])
            floor = [50, 45, 0][attempt] if ff else 45     # v8.10: the last try no longer accepts anything (floor 0) unless PREMISE_FAIL_FORWARD
            good = [p for p in good if p["total"] >= floor]
            if tz: good = [tz] + [p for p in good if not _similar(p.get("premise", ""), [tz["premise"]])]; good = good[:1] + good[1:5]
        if good:
            spine = showrun(good, tz)
            if spine: return spine
        log(f"scout attempt {attempt+1} gave no pitch above the bar", "WARN", episode)
    if dual and not ff:
        bar = S("PREMISE_MIN_SCORE", float)
        if skip or not pool:
            from whatifs.premise import SkipSlot
            raise SkipSlot(f"no premise reached the quality bar {bar} after {rounds} scout round(s) (best combined score {best_seen:.1f}); "
                           "every pitch and score is in the Premise_Scores tab")
        best = sorted(pool, key=lambda p: (-p.get("combined", 0), -p.get("total", 0)))[:3]       # v8.11: never a skipped slot - the best-scoring pitches
        spine = showrun(best, None, PR.below_bar_note("premise", best[0].get("combined", 0), bar, episode))
        if spine: return spine
    raise RuntimeError("scout failed 3 times")

def _mark(d, stage):
    """v9.2: per-stage wall time (seconds since the previous mark), reported in Script Preview and the episode notes."""
    import time as _t
    now = _t.time(); st = d.setdefault("stage_times", {}); last = d.get("_t_last") or now
    st[stage] = round(st.get(stage, 0) + now - last, 1); d["_t_last"] = now

def run_room(draw, episode):
    """The writers' room for one episode, in that episode's FORMAT (v12 V2a): picked once, kept in the draw, and the format of everything the room does."""
    from whatifs import formats as FMT
    if "format" not in draw: draw["format"] = FMT.pick(episode, draw)
    log(f"format of this episode: {draw['format'] + ' (' + FMT.name(draw['format']) + ')' if draw['format'] else 'none (made as before formats existed)'}", episode=episode)
    with FMT.using(draw["format"]): return _run_room(draw, episode)

def _run_room(draw, episode):
    import time as _t
    ctx = context(); d = draw; stg = d["strategies"]; defs = ctx["defs"]; d["_t_last"] = _t.time(); d["stage_times"] = {}
    ctx["research"], d["research_brief"] = RS.room_research(episode, allow_run=S("BACKGROUND_IN_ROOM", bool))       # v9.2: the room only READS the brief
    _mark(d, "research (read)")
    spine = FE.enrich_spine(scout_and_pick(d, ctx, episode)); _mark(d, "premise (bench / scout / judges / showrunner)")
    from whatifs import craft as _CRAFT                                         # v9.3.2: technique cards are filtered against THIS premise
    _CRAFT.CURRENT["topic"] = f"{spine.get('premise', '')} {spine.get('family', '')} {spine.get('title', '')}"
    spine["promise"] = GR.clean_promise(spine); d["promise"] = spine["promise"]       # v8.7: packaging first - the click promise is fixed BEFORE a word is written
    log(f"premise: {spine['premise']} | format: {spine.get('presentation_format', 'classic')}", episode=episode, public="premise chosen (text kept private until release)")
    roles = TR.ROLES
    v2 = str(S("ROOM_MODE") or "v1").lower() == "v2"                       # v11 (K157): no role memos / objections in v2 (research: theatre)
    if v2: roles = []
    arm, tmode = TR.active_arm(episode); d["table_read"] = {"mode": tmode, "arm": arm}      # recorded with the episode so the two arms can be compared later
    if v2: arm = "off"; d["table_read"]["arm"] = "off"; d["room_mode"] = "v2"
    tr = TR.new_record(episode, arm, tmode)
    mpack = dict(episode={"spine": _j(spine), "draw": _j(d), "trends": ctx["trends"][:2500], "research": ctx.get("research", "")[:2500]},      # v8.11: one cached
                 labels={"trends": "TREND BRIEF", "research": "AUDIENCE RESEARCH"}, extra_global=_craft_extra())                              # episode pack, role last
    memos = ask_many([dict(role="memo", system=P.pack(P.MEMO, role=r, craft=CRAFT_BY_ROLE.get(r, ""), **mpack).map_role(lambda t: FE.inject(t, "memo")),
                           prompt="Memo now.", episode=episode, fake_key="memo", max_tokens=1200) for r in roles]) if roles else []
    memo_by_role = dict(zip(roles, memos))
    objections = "none (no table read this time)"
    from whatifs import costguard as CG
    if arm == "on" and CG.ladder_level(episode) >= 1: arm = "lean"; log("table-read objections skipped (cost overrun ladder)", "WARN", episode)
    if arm == "on":                                       # v8.0 optional table read: round 2, still before any image money is spent
        tr["objections"] = TR.objections_round(memo_by_role, spine, episode)
        objections = TR.objections_text(tr["objections"])
        from whatifs import insights as INS
        INS.roi_note(episode, "objections", notes=len(tr["objections"]), accepted=len(tr["objections"]))      # v9.1 role ROI: all objections reach the bible
        log(f"table read: {len(tr['objections'])} objection(s) raised", episode=episode)
    _mark(d, "memos + table read")
    bible = ask("bible", FE.inject(GR.insert_before_json(P.fill(P.BIBLE, spine=_j(spine), memos=_j(memo_by_role, 8000), draw=_j(d), objections=objections), "\n".join(x for x in (_craft_extra(), _format_block("bible")) if x)), "bible"),
                "Write the bible.", episode=episode, fake_key="bible")
    wmin, wmax = int(d["words"] * 0.93), int(d["words"] * 1.07)
    wbrief = P.fill(P.WRITER, words=d["words"], wmin=wmin, wmax=wmax, story=stg["story"], storydef=defs.get(stg["story"], ""),
                    hook=stg["hook"], hookdef=defs.get(stg["hook"], ""), hooksec=d["hook_sec"], humour=stg["humour"], voice=stg["voice"], bible=_j(bible, 9000),
                    banter=defs.get(stg.get("banter") or "", "") or "natural", budget=budget_brief(d))
    from whatifs import enforce as EN                        # v11.1 (K166): the markers rule + the channel's own evidence, in every brief
    wbrief = GR.insert_before_json(wbrief, EN.writer_rules("long"))
    d["brain_block"] = EN.brain_block("long")
    if d["brain_block"]: wbrief = GR.insert_before_json(wbrief, d["brain_block"])
    d["brain_block_in_brief"] = bool(d["brain_block"]) and d["brain_block"] in wbrief
    if d.get("deep_trial"):                                  # v11 (K163): the monthly ~20-minute special
        from whatifs import deeptrial as DT; wbrief = GR.insert_before_json(wbrief, DT.NOTE)
    wbrief += f"\nHUMOUR SHARE: at most {int(round(S('HUMOUR_SHARE', float) * 100))}% of lines may be wit (setting HUMOUR_SHARE)."
    wbrief = FE.inject(wbrief, "writer")
    wbrief += ("\nRETENTION RULES: " + CRAFT["retention"] +                       # v8.6: the writer itself gets the retention rules and its own lessons
               "\nLESSONS FROM OUR OWN VIDEOS (opening, holding, hooks, reactions; follow them unless they contradict the bible): " + ctx["lessons_writer"])
    wbrief = GR.insert_before_json(wbrief, "\n".join(x for x in (                      # v8.7: the promise, this episode's rhythm and the research-graded rules
        "THE PROMISE (packaging first: the title and thumbnail were decided before you write; pay them off ON SCREEN and IN WORDS within the first 30 s): " + GR.promise_text(spine.get("promise")),
        GR.rhythm_brief(d.get("rhythm_plan"), defs), PB.text_for("writer", d.get("playbook")), guest_brief(d), tease_brief(spine), _writer_extra(episode),
        _show_writer(spine), _format_block("writer")) if x))
    if S("EFFORT_AB_ON", bool):                           # v9: medium vs high effort for the script, alternating by episode (the A/B machinery records the arm)
        from whatifs import models as _M
        arm = "medium" if int(hashlib.md5(episode.encode()).hexdigest(), 16) % 2 else "high"
        _M.EFFORT_RUN[episode] = {"writer": arm, "rewrite": arm}; d["effort_arm"] = arm
    wbrief = P.Packed.as_episode(wbrief)                  # v8.11: house rules cached 1 h, the whole brief cached as the episode layer; each call's task is its user message
    _mark(d, "bible")
    if v2:                                                 # v11 (K157): diverse drafts -> blind cross-family jury -> one checklist revision
        from whatifs import room2 as R2
        script, verdict_v2 = R2.write(spine, wbrief, d, episode); _mark(d, "room v2 (drafts + jury + revision)")
    else:
        script = ask("writer", wbrief, "Write the narration.", episode=episode, fake_key="writer", max_tokens=16000); _mark(d, "writer (first draft)")
    script = _fix_length(script, wbrief, wmin, wmax, episode)
    script = humanize(script, episode)
    script = format_pass(script, wbrief, episode)
    script, d["retention_check"] = retention_pass(script, wbrief, spine.get("promise"), episode)      # v8.7: opening + re-hooks checked by code, one fix at most
    verdict = critic(spine, script, ctx, episode)          # v11 fix: v2 keeps the critic - its scores carry the POLICY-SAFETY gate (checked below)
    if v2: verdict["room"] = "v2"; verdict.setdefault("scores", {}).update(verdict_v2.get("scores") or {})
    if verdict.get("verdict") != "PASS":
        log(f"critic asked for revision: {verdict.get('fixes')}", "WARN", episode, public="critic asked for a revision (details kept private)")
        rfix = GR.retention_issues(script.get("script", ""), spine.get("promise"), S("WPM_ESTIMATE", float), script.get("loops"))["issues"] if S("RETENTION_GATE_ON", bool) else []
        s_before = script.get("script", "")
        script = ask("rewrite", wbrief, "CRITIC FIXES (apply all): " + _j(verdict.get("fixes", {})) +          # v8.11: fixes travel in the user message (brief stays cached)
                     ("\nRETENTION FIXES STILL OPEN (apply them too; same call, no extra cost): " + " ".join(rfix) if rfix else "") + "\nRewrite the full narration.",
                     episode=episode, fake_key="writer", max_tokens=16000)
        from whatifs import insights as INS
        INS.roi_note(episode, "critic", notes=len(verdict.get("fixes") or {}), accepted=len(verdict.get("fixes") or {}) if INS.changed(s_before, script.get("script")) else 0,
                     changed=INS.changed(s_before, script.get("script")))
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
    _mark(d, "critic + rewrites + edits")
    if v2:                                                 # v11: the joke tournament runs BEFORE the fact check, so new lines are checked too
        from whatifs import room2 as R2
        script, d["joke_tournament"] = R2.jokes(script, wbrief, episode); _mark(d, "joke tournament")
    script = fact_check(spine, script, episode)           # v8.3: search-grounded check of the claims, before any picture money is spent
    _mark(d, "fact check")
    try:                                                   # v10 (K133): early, crowded or doubled asks out first; cta.ensure then puts any missing kind back at a calm slot
        from whatifs import engage as EG
        new_t, n_rm = EG.enforce(script.get("script", ""), episode)
        if n_rm: script = dict(script, script=new_t)
        if S("EMOTION_BEAT_ON", bool):
            d["emotion_beat"] = EG.pick_emotion(episode); set_setting("EMOTION_LAST", d["emotion_beat"])
    except Exception as e: log(f"engagement check skipped: {scrub(e)}", "WARN", episode)
    if S("CTA_ON", bool):                                 # v8.3: like / subscribe / share asks: the writer's own, or a hand-written one added at a calm moment
        new, added, code = CTA.ensure(script.get("script", ""), episode, S("CTA_LAST"))
        if added:
            script = dict(script, script=new); log(f"audience asks added by code: {', '.join(added)}", episode=episode)
        if code != S("CTA_LAST"): set_setting("CTA_LAST", code)
    script = ensure_tease(script, spine.get("next_tease"), episode); d["next_tease"] = spine.get("next_tease") or {}      # v8.9: the video ends on the next episode
    try:                                                   # v10.1 (K145): repetitive-content guard (never a hold; one card when too similar)
        from whatifs import similarity as SIM
        d["script_similarity"] = round(SIM.check(script.get("script", ""), episode)[0], 3)
    except Exception as e: log(f"similarity check skipped: {scrub(e)}", "WARN", episode)
    from whatifs import immersion as IM, craft as CR                       # v8.10: Immersion Director, then the Owner's Cut (both before any picture money)
    imap = IM.immersion_map(script.get("script", ""), spine, episode)
    def oc_rewrite(sc, fixes):
        try:
            out = ask("rewrite", wbrief, "OWNER'S CUT FIXES (the owner's own taste; apply all, keep every label, tag, '## BEAT' line, fact and the three audience asks): "
                      + " ".join(f"({k + 1}) {x}" for k, x in enumerate(fixes)) + "\nNARRATION:\n" + sc.get("script", "") + "\nRewrite the full narration.",
                      episode=episode, fake_key="writer", max_tokens=16000)
            if not out.get("script") or not FE.labels_preserved(sc.get("script", ""), out["script"]): return None
            new = _fix_length(dict(sc, script=out["script"]), wbrief, wmin, wmax, episode)
            if S("CTA_ON", bool): new = dict(new, script=CTA.ensure(new.get("script", ""), episode, S("CTA_LAST"))[0])
            return ensure_tease(new, spine.get("next_tease"), episode)
        except Exception as e:
            log(f"Owner's Cut rewrite failed: {scrub(e)[:160]}", "WARN", episode); return None
    s_oc = script.get("script", "")
    _mark(d, "immersion + director read")
    script, oc = CR.owners_cut(spine, script, wbrief, imap, episode, oc_rewrite); _mark(d, "owner's cut")
    from whatifs import insights as INS
    INS.roi_note(episode, "owners_cut", notes=sum(len(r.get("fixes") or []) for r in oc.get("rounds") or []),
                 accepted=sum(len(r.get("fixes") or []) for r in (oc.get("rounds") or [])[:-1]) if INS.changed(s_oc, script.get("script")) else 0,
                 changed=INS.changed(s_oc, script.get("script")))
    script = INS.variety_rewrite(script, wbrief, episode, ask)                                   # v9.1: ONE surgical opening rewrite when still too similar
    if oc.get("rounds") and len(oc["rounds"]) > 1 and IM.on(): imap = IM.immersion_map(script.get("script", ""), spine, episode) or imap
    if SHOW_ON():                                                                              # v9: the show tags, checked by code; ONE bounded tag fix
        from whatifs import show as SHOW
        d["show_plan"] = spine.get("show_plan") or {}
        iss = SHOW.check_tags(script.get("script", ""), d["show_plan"])
        if iss:
            fixed = ask("format", wbrief, "Fix ONLY these show-tag problems (add, move or remove the bracket tags; keep every spoken word, label and '## BEAT' line): "
                        + "; ".join(iss[:8]) + "\nNARRATION:\n" + script.get("script", "") + "\nReturn the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
            if fixed.get("script") and len(SHOW.check_tags(fixed["script"], d["show_plan"])) < len(iss): script = fixed
            iss = SHOW.check_tags(script.get("script", ""), d["show_plan"])
        d["show_tag_issues"] = iss
        if iss: note_degraded("show tags: " + "; ".join(iss[:3]))
    from whatifs import enforce as EN                        # v11.1: AFTER the last rewrite (fact check, asks, tease, Owner's Cut, variety, tags) -
    script, d["enforce_fix"] = EN.fix_all(script, wbrief, spine, episode, "long")   # ONE mandatory rewrite for every open retention + marker problem
    if d.get("enforce_fix"):                                 # a rewrite may drop the code-added lines: put the asks and the tease back (both idempotent)
        if S("CTA_ON", bool):
            new, added, _code = CTA.ensure(script.get("script", ""), episode, S("CTA_LAST"))
            if added: script = dict(script, script=new)
        script = ensure_tease(script, spine.get("next_tease"), episode)
    d["owners_cut"] = {"mean": (oc.get("rounds") or [{}])[-1].get("mean"), "rounds": len(oc.get("rounds") or [])} if oc.get("checked") else {}
    below = [x for x in (spine.get("below_bar"), oc.get("below_bar")) if x]                     # v8.11: made below the bar = noted + ONE email
    if below:
        from whatifs import premise as PR
        d["below_bar"] = below; note_degraded("made below the quality bar: " + ", ".join(f"{x['kind']} {x['best']}/{x['bar']}" for x in below))
        if oc.get("below_bar"): d["owners_cut"]["mean"] = oc["rounds"][oc.get("best_round", -1)]["mean"]
        PR.below_bar_mail(episode, below, spine.get("headline") or "")
    if arm == "on" and CG.ladder_level(episode) >= 1: arm = "lean"
    if arm == "on":                                       # the Director reads the FINAL script before shots are planned
        tr["director_notes"] = TR.director_notes(script.get("script", ""), bible.get("look", ""), episode)
        log(f"table read: Director gave {len(tr['director_notes'])} note(s)", episode=episode)
        INS.roi_note(episode, "director_read", notes=len(tr["director_notes"]), accepted=len(tr["director_notes"]))      # notes go into every shot list
    if arm == "on": tr["status"] = "done"
    TR.save(tr)
    try:                                                    # v9.1: role ROI rows; the opening line for the next variety check
        INS.roi_flush(episode)
        from whatifs import v91 as V91
        if V91.on("VARIETY_REWRITE_ON", episode):
            first = INS.variety_score(script.get("script", ""), [])[1]
            store().update_where("Show_Log", {"episode_id": episode}, {"opening_line": first[:300]})
    except Exception as e: log(f"role ROI / opening line skipped: {scrub(e)[:120]}", "WARN", episode)
    return {"spine": spine, "bible": bible, "script": script, "critic": verdict, "director_notes": tr["director_notes"], "table_read": {"arm": arm, "mode": tmode},
            "immersion": imap, "owners_cut": d.get("owners_cut", {})}

def _craft_extra():
    """v8.10: the Creative Constitution + the owner's Craft_Notebook (top priority) for memos and the bible."""
    from whatifs import craft as CR
    return "\n" + CR.brief("bible")

def _writer_extra(episode=""):
    """v8.10: constitution + notebook + technique library + immersion / voice-acting / pacing rules for the writer. v10: audience prompts + emotion beat."""
    from whatifs import craft as CR, immersion as IM
    try:
        from whatifs import engage as EG; eg = EG.brief(episode)
    except Exception: eg = ""
    try:
        from whatifs import microscope as MS; dr = MS.brief()                 # v10 (K138, decision 3): this channel's own retention rules
    except Exception: dr = ""
    return "\n".join(x for x in (CR.brief("writer"), IM.writer_rules(), eg, dr) if x)

# ---------------- v8.9: rotating guest + the next-episode tease ----------------
def guest_brief(d):
    from whatifs.data import GUESTS
    from whatifs import show as SHOW
    if SHOW.leads_on(): return ""                       # v9: the core cast replaces the rotating guest - in every format (v12 V2a)
    if d.get("cast"):                                   # v8.10: the Cast tab's characters (personality, habits, quirk) replace the v8.9 guest line
        from whatifs import cast as CAST
        b = CAST.brief(d["cast"])
        if b: return b
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
        out = ask("factfix", P.fill(P.FACTFIX, errors=errs, script=text), "Fix the errors now.", episode=episode, fake_key="humanize", max_tokens=16000)
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
        out = ask("retention", brief, "Fix ONLY these retention problems, at the places named, and change nothing else: " + " ".join(f"({k + 1}) {x}" for k, x in enumerate(chk["issues"])) +
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
        out = ask("format", brief, "Fix ONLY the speaker format of this narration. " + " ".join(chk["issues"]) + " Give each dialogue line a label [DIRECTOR] or [SKEPTIC] (label first, then the delivery tag), "
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
        out = ask("humanize", P.fill(P.HUMANIZE, script=script.get("script", ""), craft=CRAFT["humanize"]), "Edit now.", episode=episode, fake_key="humanize", max_tokens=16000)
        new = out.get("script", "")
        old_n = len(script.get("script", "").split()); new_n = len(new.split())
        if new and new.count("## BEAT") >= max(1, script.get("script", "").count("## BEAT") - 1) and abs(new_n - old_n) <= old_n * 0.12 and FE.labels_preserved(script.get("script", ""), new):
            script = dict(script, script=new)
        tells = ai_tells(script.get("script", ""))
        if len(tells) <= 2: break
        log(f"AI phrases still present {tells} - second human pass", "WARN", episode)
    return script

def extend(room, script_text, add_words, episode):
    out = ask("length", P.fill(P.HUMANIZE, script=script_text, craft=CRAFT["humanize"]),
              f"The narration is too short. Keep everything and ADD about {add_words} words: deepen the strongest beats with one more concrete consequence each, "
              "keep the same tags and '## BEAT' lines. Return the full narration.", episode=episode, fake_key="writer", max_tokens=16000)
    s = out.get("script", "")
    return s if len(s.split()) > len(script_text.split()) and FE.labels_preserved(script_text, s) else None

def _fix_length(script, brief, wmin, wmax, episode):
    n = len(re.sub(r"\[[^\]]+\]|##.*", "", script.get("script", "")).split())
    if wmin <= n <= wmax: return script
    log(f"script length {n} outside {wmin}-{wmax}, adjusting", "WARN", episode)
    adj = ask("length", brief, f"Your draft has {n} words. Rewrite it to {(wmin+wmax)//2} words, same structure:\n" + script.get("script", ""),
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
    dpack = {"look": look, "budget": budget_brief(draw),                                 # v8.11: shared by every chunk = one cached episode pack (the chunk's units stay last)
             "notes": TR.notes_text(room.get("director_notes", [])) + "\nPRODUCTION BIBLE: " + _j(room.get("bible", {}), 4500) + "\nEPISODE SPINE: " + _j(room.get("spine", {}), 1800) + extra + _immersion_notes(room)}
    for k, ch in enumerate(chunks):
        kl = plan["kling"] // n + (1 if k < plan["kling"] % n else 0); lv = plan["living"] // n + (1 if k < plan["living"] % n else 0)
        U = "\n".join(f'{u["i"]}: ({str(u.get("speaker", "N"))[:1]}/{u.get("tag", "none")}) {u["text"]}' for u in ch)
        allow = max(1, round(draw.get("stills", 40) * len(ch) / max(1, len(units))))
        pk = [i for i in peaks if ch[0]["i"] <= i <= ch[-1]["i"]]
        jobs.append(dict(role="director", system=P.pack(P.DIRECTOR, episode=dpack, labels={"notes": "DIRECTOR'S SCRIPT-READ NOTES AND PRODUCTION MATERIAL"}, nshots=len(ch), kling=kl, living=lv,
                                           ptype=draw["ptype"], units=U, allow=allow, peaks=pk or "none", sounds=_sound_cap(draw, len(ch))).map_role(lambda t: FE.inject(t, "director")),
                         prompt=f"Shot list for units {ch[0]['i']}-{ch[-1]['i']} (use these exact unit numbers).", episode=episode, fake_key="director", max_tokens=8000))
    shots = []
    for res in ask_many(jobs, workers=3): shots += res.get("shots", [])
    out = normalise_shots(shots, units, plan, look, peaks)
    from whatifs import immersion as IM
    from whatifs import v91 as V91
    if V91.on("REACTION_SHOTS_ON", episode):                             # v9.2: tiny lines -> free reaction cutaways of the speaking character
        with V91.guard("REACTION_SHOTS_ON", episode):
            from whatifs import shotplan as SP
            out, n_ = SP.reaction_shots(out, units)
            if n_: log(f"shot plan: {n_} tiny line(s) became reaction cutaways (no image bought)", episode=episode)
    return IM.apply(out, units, room.get("immersion") or {}, plan, episode)       # v8.10: POV on every shot type, Kling on the impact sequence, camera events

def _immersion_notes(room):
    from whatifs import immersion as IM, craft as CR
    if not IM.on(): return ""
    return ("\n" + IM.director_rules() + "\nIMMERSION MAP (from the Immersion Director: vantage, body, senses, camera and sound per moment): " + _j(room.get("immersion") or {}, 3500)
            + "\n" + CR.brief("director"))

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
        from whatifs.immersion import POV_MOVES
        if cam in POV_MOVES and S("IMMERSION_ON", bool) and S("POV_CAMERA_ON", bool): s["pov_fx"] = cam      # v8.10: POV effects work on EVERY shot type
        if isinstance(s.get("pov"), str) and S("IMMERSION_ON", bool): s["pov"] = {"vantage": s["pov"][:12]}
        elif not isinstance(s.get("pov"), dict): s.pop("pov", None)
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
            from whatifs import immersion as IM
            if IM.on() and "first-person POV" not in s["prompt"][:200]:     # v8.11: the re-aimed opening clip keeps the first-person rules
                s["prompt"] = IM.pov_prompt(dict(s, prompt=f"{tp}; {str(units[i]['text'])[:160]}"), units[i]["text"])
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

def _owner_taste():
    """v9.3.1 (L4): the owner's own title picks as a taste signal for the Packager. "" when none or on any error."""
    try:
        from whatifs.packaging import taste_brief
        return taste_brief()
    except Exception: return ""

def package(room, chapters, draw, episode):
    ctx = context(); stg = draw["strategies"]
    excerpt = room["script"].get("script", "")[:3500]
    pkg = ask("packager", FE.inject(GR.insert_before_json(P.fill(P.PACKAGER, title=stg["title"], titledef=ctx["defs"].get(stg["title"], ""), thumb=stg["thumb"],
               thumbdef=ctx["defs"].get(stg["thumb"], ""), spine=_j(room["spine"]), excerpt=excerpt, trends=ctx["trends"][:3000],
               lessons=ctx["lessons_packager"], chapters=_j(chapters), craft=CRAFT["packager"], promise=GR.promise_text(room["spine"].get("promise"))),
               "\n".join(x for x in (PB.text_for("packager", draw.get("playbook")), _pkg_extra(), _owner_taste()) if x)), "packager"), "Package now.", episode=episode, fake_key="packager")
    pt = str((room["spine"].get("promise") or {}).get("title") or "").strip()       # v8.7: the promise title is always a candidate (it wins only if the Packager's are flawed)
    if isinstance(pkg, dict) and pt and pt.lower() not in [str(t).lower() for t in pkg.get("titles") or []]: pkg["titles"] = list(pkg.get("titles") or []) + [pt]
    return pkg

def reel_count(): return max(2, min(4, S("REELS_PER_VIDEO", int)))
def reel_style():
    """v8.5: bridge (default) | standalone | teaser. Anything unknown is read as bridge (same rule as reels.reel_style)."""
    from whatifs.reels import reel_style as _rs
    return _rs()

def past_footage(sh, shots):
    """v12 V2c-b2b: a cut-down never takes a shot of the Short's own footage - made of those it would be the Short uploaded a second time. Each such
    shot is replaced by the next shot of the long video's OWN pictures that the cut-down does not use yet (none left = it is dropped)."""
    out = []
    for i in sh:
        if shots[i].get("short"):
            i = next((j for j in range(i + 1, len(shots)) if not shots[j].get("short") and j not in out and j not in sh), None)
        if i is not None and i not in out: out.append(i)
    return out

def reels(room, shots, draw, episode):
    ctx = context(); n = reel_count()
    S_ = "\n".join(f'{i}: {s["type"]}: {(s.get("prompt") or s.get("search") or "")[:90]}' for i, s in enumerate(shots) if not s.get("short"))      # v12 V2c-b2b: the Short's footage is not on offer
    fm = draw["reel_formats"]
    style = {"bridge": P.REEL_STYLE_BRIDGE, "standalone": P.REEL_STYLE_STANDALONE, "teaser": P.REEL_STYLE_TEASER}[reel_style()]
    r = ask("reels", FE.inject(GR.insert_before_json(P.fill(P.REEL, n=n, style=style, formats=fm, formatdefs=_j({f: ctx["defs"].get(f, "") for f in fm}), shots=S_[:12000],
            spine=_j(room["spine"]), trends=ctx["trends"][:2000], craft=CRAFT["reel"], lessons=ctx["lessons_reel"]), "\n".join(x for x in (PB.text_for("reel", draw.get("playbook")), _reel_extra(room)) if x)), "reels"), f"Make the {n} reels.", episode=episode, fake_key="reel",
            max_tokens=6000 + 1500 * (n - 2)).get("reels", [])
    good = []
    for x in r[:n]:
        sh = past_footage([int(i) for i in x.get("shots", []) if str(i).isdigit() and int(i) < len(shots)], shots)
        kl = [i for i in sh if shots[i]["type"] == "kling"]
        sh = [i for i in sh if shots[i]["type"] != "kling"] + kl[:1]
        if len(sh) >= 4 and x.get("lines"): x["shots"] = sh; good.append(x)
    from whatifs import show as SHOW
    cb = SHOW.clipbait_lines(room.get("script", {}).get("script", "")) if SHOW.on() else []
    if cb and len(good) >= 4:                                     # v9: the 4th Short IS the clip-bait moment, word for word (its shots stay the planner's)
        good[3]["lines"] = cb; good[3]["format"] = "clipbait"; good[3].setdefault("hook_text", SHOW.strip_tags(cb[0])[:60])
    return good

def continuity(pkg, episode):
    try:
        v = ask("critic", FE.inject(P.fill(P.SYNC, pkg=_j(pkg, 40000)), "continuity"), "Check now.", episode=episode, fake_key="sync", temperature=0.1)
        return v
    except Exception as e:
        log(f"continuity check skipped: {scrub(e)}", "WARN", episode); return {"ok": True, "problems": []}

