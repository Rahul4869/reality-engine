"""Cost controls that never touch pictures: the per-stage estimator, the spend monitor and the overrun ladder. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json
from whatifs.core import S, log, store, iso, now_utc, month_spend, set_setting, JOB

# ---------------------------------------------------------------- the cost model: ONE table of lines (v12 V2d)
TEXT = ("text:", "vision", "batch")          # what the writing lines stand for in the paid-call counter: every text call, vision check and batch submission

def _line(key, what, n, unit_inr, stage, unit="", item=None, calls=None):
    return {"key": key, "what": what, "n": n, "unit": unit, "unit_inr": round(float(unit_inr), 4), "inr": round(float(n) * float(unit_inr), 2), "stage": stage,
            "item": item, "calls": dict(calls or {})}

def total(L): return round(sum(l["inr"] for l in L), 2)

def table_read_runs(arm_on=None):
    """Does the table read (the objections round and the Director's read) really RUN? Only in the older writers' room: under ROOM_MODE v2 the room
    switches it off for every episode, so its allowance is money for calls that are never made."""
    if str(S("ROOM_MODE") or "v1").strip().lower() == "v2": return False
    return str(S("TABLE_READ_MODE") or "").strip().lower() in ("on", "true", "yes", "1") if arm_on is None else bool(arm_on)

def voice_inr(seconds):
    """The voice of `seconds` of narration at the price of the day, the re-takes of TTS_RETAKES included (0 when the engine is not the paid one)."""
    if str(S("TTS_ENGINE") or "").strip().lower() != "gemini": return 0.0
    from whatifs import tts_gemini as T
    return T.est_inr(float(seconds)) * (1 + max(0, S("TTS_RETAKES", int)))

def short_shots(fmt):
    """(paid hero clips, seconds each clip covers, pictures, seconds of the Short) for a Short of this format BEFORE it is written: the middle of the
    format's band; a beat longer than one clip can cover is split. With clips bought by the second EVERY beat is counted as paid: the loop (the
    first clip again, free) is no longer than that first clip, so part of the last beat is usually a paid clip too - the estimate may only err
    upward (the first whole Shorts showed it: a plan bought 23 seconds where 'the last beat is free' had said 21)."""
    import math
    from whatifs import formats as FMT, clips as CL
    lo, hi = FMT.short_len(fmt); sec = (lo + hi) / 2; beats = max(2, len(FMT.SHORTS[fmt]["beats"])); cut = FMT.SHORTS[fmt]["camera"] == "cut"
    if CL.hero(): per = sec / beats; nb = beats
    else: nb = beats - 1; per = max(0.0, sec - CL.OLD_CLIP_S) / nb      # the older way: 5-second clips, the loop is one of them and the last beat is free
    each = max(1, math.ceil(per / CL.longest() - 1e-6))
    return nb * each, per / each, (nb if cut else 1), sec

def lines(kind="long", kling=None, stills=None, living=None, table_read=None, fmt=None, shots=None, seconds=None, living_s=None):
    """THE estimate: every paid second and call of one video as a line - {key, what, n, unit, unit_inr, inr, stage, item, calls}. `n` times the price
    cell is the line; `item` is the Cost_Log item that pays it (reconcile); `calls` is what the paid-call counter must see for it. Kinds: 'long' (a
    long video that opens on its own pictures: an override, or the ladder off), 'ladder' (a long video about a promoted Short: its opening is that
    Short's footage, already paid - one scene and one start picture fewer, no hook lab), 'short' (fmt = its Short format; shots = its real plan once
    it exists; seconds = its real length). Every gate reads this one table (governor, episode, shorts2)."""
    from whatifs import governor as G, clips as CL, media as MD
    u = S("USD_INR", float); hero_inr = CL.hero_usd_s() * u
    if kind == "short":
        from whatifs import shorts2 as SH
        if shots is not None:
            paid = [s for s in shots if s.get("src") != "loop"]; n_clips = len(paid); pics = sum(1 for s in paid if s.get("src") == "picture") or (1 if paid else 0)
            hero_s = sum(int(s.get("buy") or CL.buy(float(s["end"]) - float(s["start"]))[1]) for s in paid)
            sec = float(seconds or (shots[-1]["end"] if shots else 0))
        else:
            n_clips, per, pics, sec = short_shots(fmt); hero_s = CL.paid_s(per, n_clips)
        n_var = max(1, S("SHORTS_VARIANTS", int))
        return [_line("hero_clips", "every second of the Short but the loop's: clips of the hero model", hero_s, hero_inr, "visuals", "s", "hero_clip", {"clip_kling": n_clips}),
                _line("pictures", "the start picture of each beat", pics, MD.still_usd(*SH._still_size()) * u, "visuals", "", "image", {"image": pics}),
                _line("writing", f"{n_var} scripts, the blind jury, one fix", 1, S("REPLAN_SHORT_INR", float), "ai_writing", "", None, {"text:short_writer": n_var + 1}),
                _line("voice", "the guide's voice, by the second", 1, voice_inr(sec), "tts", "", "gemini_tts", {"voice_job": 1})]
    ladder = kind == "ladder"; full = G.TIERS[0]
    k = S("KLING_CLIPS", int) if kling is None else int(kling)
    if ladder: k = max(0, k - 1)                                          # the scene at second 0 is the Short's footage: paid when the Short was made
    st_n = full[2] if stills is None else int(stills); lv = min(full[3], S("LIVING_STILLS", int)) if living is None else int(living)
    lr = CL.living()                                                    # v12 V2d-b: with the motion ladder a still is brought to life BY THE SECOND from a row of the clip market:
    if lr is not None:                                                  # `living_s` = the seconds this video buys (None = the floor every long video is counted with); each clip has its own picture
        ls = int(G.moving_floor(kind)["living_s"] if living_s is None else living_s); lc = ls // max(1, int(lr.get("min_s") or CL.SCENE_S)); st_n += lc
        live = _line("living_clips", "stills brought to life: seconds of a clip model of the market", ls, CL.usd_s(lr) * u, "visuals", "s", "living_clip", {"clip": lc})
    else: live = _line("living_clips", "living stills", lv, S("PRICE_LIVING_USD", float) * u, "visuals", "", "living_clip", {"clip": lv})
    if S("CAMERA_PATH_ON", bool):                                       # v12 V2b: one picture an act beyond the budget (an act's first picture is a guarantee), at most the allowance + 1
        from whatifs import path as PATH
        st_n += PATH.allowance(S("RUNTIME_MAX_SEC", float)) + 1
    L = [_line("hero_clips", "animated scenes of the hero model", CL.paid_s(CL.SCENE_S, k), hero_inr, "visuals", "s", "hero_clip", {"clip_kling": k}),
         _line("start_frames", "the reference-locked start picture of each animated scene", k, S("PRICE_GEM_IMAGE_USD", float) * u, "visuals", "", "image_ref", {"image_ref": k}),
         _line("stills", "pictures", st_n, MD.still_usd(S("STILL_W", int), S("STILL_H", int)) * u, "visuals", "", "image", {"image": st_n}),
         live,
         _line("key_art", "the thumbnail and its runner-up", G.premium_images(), S("PRICE_THUMB_USD", float) * u, "visuals", "", "image_premium", {"image_premium": G.premium_images()}),
         _line("voice", "the narration, by the second", 1, voice_inr(S("RUNTIME_MAX_SEC", float)), "tts", "", "gemini_tts", {"voice_job": 1}),
         _line("writing", "the writers' room, the juries and every edit of the script", 1, max(0.0, S("LLM_EST_INR", float) - S("HOOK_LAB_EST_INR", float)), "ai_writing", "", None, {t: None for t in TEXT}),
         _line("thinking", "thinking tokens of the text models", 1, S("THINK_EST_INR", float), "thinking"),
         _line("room_extras", "the premise judges, the Immersion Director, the Owner's Cut", 1, S("ROOM_EXTRA_EST_INR", float), "ai_writing")]
    if not ladder: L.append(_line("hook_lab", "the hook lab: ten opening lines and their judge", 1, S("HOOK_LAB_EST_INR", float), "ai_writing", "", None, {"text:hooks": 1}))
    if table_read_runs(table_read): L.append(_line("table_read", "the older room's objections round and the Director's read", 1, S("TABLE_READ_EXTRA_INR", float), "ai_writing"))
    if G.palace_prompt_inr(): L.append(_line("palace", "the Palace playbook inside the creative prompts", 1, G.palace_prompt_inr(), "ai_writing"))
    if S("LAYMAN_PROBE_ON", bool): L.append(_line("probe", "the promise line-up: two cheap readers", 1, S("PROBE_EST_INR", float), "ai_writing", "", None, {"text:probe_gemini": 1, "text:probe_claude": 1}))
    return L + [_line(k_, "a small community line", 1, v, k_) for k_, v in v91_lines().items() if v]

def estimate_lines():
    """{stage: INR} for one full long video (the weekly deviation report and the Script Preview read it). Stage names match Cost_Log item prefixes
    (see stage_of); the sums come from the one table of lines."""
    L = lines("long"); by = {}
    for l in L: by[l["stage"]] = by.get(l["stage"], 0.0) + l["inr"]
    return {"visuals": round(by.get("visuals", 0.0), 1), "ai_writing": round(by.get("ai_writing", 0.0), 1), "thinking": round(by.get("thinking", 0.0), 1),
            "tts": round(by.get("tts", 0.0), 1), "show_devices": 0.0, "community": round(S("COMMENT_AGENT_EST_INR", float) / max(1, S("VIDEOS_PER_MONTH_EST", int)), 1),
            **{k: round(by.get(k, 0.0), 1) for k in v91_lines()}}

COUNTED = ("hero_clip", "image_ref", "image_premium")          # lines whose count is exact: more paid than estimated is an overrun (stills and living clips are ceilings)

def reconcile(episode, L, kind=""):
    """After a video or a Short is made: what was really paid for pictures and clips (tab Cost_Log, by item: seconds of hero clip, start pictures,
    stills, living clips, key art) against the lines of its estimate. Writes ONE summary row (inr 0: the spend is in the measured rows) and returns
    {paid, lines, unlisted, over}: `unlisted` = a paid item no line covers; `over` = a counted line that was exceeded. Never raises."""
    try:
        from whatifs.core import flush_costs
        flush_costs(); paid = {}
        for r in store().rows("Cost_Log"):
            if r.get("episode_id") != episode or stage_of(r.get("item"), r.get("provider")) != "visuals": continue      # pictures and clips only (a summary row is no paid item: its stage is 'other')
            try: paid[r["item"]] = paid.get(r["item"], 0.0) + float(r.get("units") or 0)
            except (TypeError, ValueError): pass
        want = {}
        for l in L:
            if l.get("item") and l["stage"] == "visuals": want[l["item"]] = want.get(l["item"], 0.0) + float(l["n"])
        unlisted = sorted(i for i in paid if i not in want and paid[i] > 0)
        from whatifs import clips as _CL
        counted = COUNTED + (("living_clip",) if _CL.living() is not None else ())          # v12 V2d-b: living seconds are a budget - more paid than planned is an overrun
        over = sorted(f"{i}: {paid[i]:g} paid, {want[i]:g} estimated" for i in paid if i in want and i in counted and paid[i] > want[i] + 1e-6)
        out = {"paid": paid, "lines": want, "unlisted": unlisted, "over": over, "est_inr": total(L)}
        store().append("Cost_Log", [{"ts": iso(), "episode_id": episode, "item": "cost_lines_summary", "provider": "summary", "units": 0, "inr": 0, "basis": "summary",
                                     "est_inr": out["est_inr"], "role": (f"{kind}: " + json.dumps({"paid": paid, "lines": want, "unlisted": unlisted, "over": over}, sort_keys=True))[:900]}])
        if unlisted or over:
            log(f"cost lines of {episode}: " + "; ".join(([f"paid with no line in the estimate: {', '.join(unlisted)}"] if unlisted else []) + over), "WARN", episode)
        return out
    except Exception as e:
        log(f"cost lines not reconciled: {str(e)[:160]}", "WARN", episode); return None

def v91_lines():
    """v9.1 estimator lines per video (INR). Atmosphere, retention map, role ROI, grammar and hero-still reels are code-only (0). The small paid ones
    use their caps: comment mining one batch call a day (~Rs 0.2), AI drafts one batch call a day when on, the variety rewrite about Rs 6 when it fires
    (assumed in 1 of 4 episodes)."""
    from whatifs import v91 as V91
    vpm = max(1, S("VIDEOS_PER_MONTH_EST", int))
    return {"atmosphere": 0.0, "hero_reels": 0.0, "retention_map": 0.0, "role_roi": 0.0,
            "comment_mining": round(0.2 * 30 / vpm, 1) if V91.on("COMMENT_MINING_ON") else 0.0,
            "comment_ai_drafts": round(0.5 * 30 / vpm, 1) if V91.on("COMMENT_AI_DRAFTS_ON") else 0.0,
            "variety_rewrite": round(6.0 * 0.25, 1) if V91.on("VARIETY_REWRITE_ON") else 0.0}

def stage_of(item, provider=""):
    i = str(item or "")
    if i.startswith(("claude_", "gemini_pro", "gemini_flash")): return "ai_writing"
    if i == "gemini_tts": return "tts"
    if i.startswith(("comment_", "community")): return "community"
    if i.startswith(("kling", "fal", "image", "still", "living", "premium", "thumb")) or provider == "fal": return "visuals"
    return "other"

# ---------------------------------------------------------------- spend monitor
def spend_monitor():
    """One email per threshold per month. Returns the thresholds mailed now."""
    from whatifs import governor as G, publish as PUB
    cap = G.cap_inr(); spent = month_spend(); mk = now_utc().strftime("%Y-%m"); sent = str(S("SPEND_WARN_SENT") or "")
    out = []
    for p in sorted(int(x) for x in str(S("SPEND_WARN_PCTS") or "70,90").split(",") if x.strip().isdigit()):
        tag = f"{mk}:{p}"
        if cap > 0 and spent >= cap * p / 100 and tag not in sent:
            out.append(p); sent = (sent + "," + tag).strip(",")
    if out:
        set_setting("SPEND_WARN_SENT", ",".join(sent.split(",")[-12:]))
        try:
            PUB.email(f"Budget: {max(out)}% of this month's cap used",
                      f"<p>Spent about Rs {spent:.0f} of Rs {cap:.0f} this month. New videos still start only while the month can pay for a complete one "
                      "(pictures and clips are never cut to make room). Measured vs estimated AI cost per video: the 'ai_per_video_summary' rows in Cost_Log.</p>")
        except Exception as e: log(f"spend warning not sent: {str(e)[:120]}", "WARN")
    return out

# ---------------------------------------------------------------- overrun ladder (AI side only)
def ai_measured(episode):
    from whatifs.core import flush_costs
    try: flush_costs()
    except Exception: pass
    m = 0.0
    for r in store().rows("Cost_Log"):
        if r.get("episode_id") == episode and stage_of(r.get("item"), r.get("provider")) == "ai_writing":
            try: m += float(r.get("inr") or 0)
            except Exception: pass
    return m

_LADDER = {}
def ladder_level(episode):
    """0 = normal; 1 = drop optional reviews; 2 = also fewer rewrite rounds; 3 = also reuse cached assets only. Never touches visuals.
    The level only rises within an episode (a later cheaper step never re-enables a dropped review)."""
    if not episode or not S("OVERRUN_LADDER_ON", bool): return 0
    from whatifs.models import ai_estimate_inr
    est = max(1.0, ai_estimate_inr()); m = ai_measured(episode); f = S("OVERRUN_FACTOR", float)
    lvl = 0 if m <= est * f else 1 if m <= est * (f + 0.25) else 2 if m <= est * (f + 0.5) else 3
    prev = _LADDER.get(episode, 0); lvl = max(prev, lvl)
    if lvl > prev:
        _LADDER[episode] = lvl
        log(f"AI spend Rs {m:.0f} is above {f}x the AI estimate Rs {est:.0f} - degradation ladder step {lvl} (AI side only; pictures untouched)", "WARN", episode)
    return lvl

def ladder_mail(episode):
    """After the episode: one email when the ladder was used."""
    lvl = _LADDER.get(episode, 0)
    if not lvl: return False
    from whatifs import publish as PUB
    steps = ["optional reviews (table-read objections, the Director's script read) were dropped", "Owner's Cut rewrites were limited to 1",
             "only cached / already-made assets were reused"][:lvl]
    try:
        PUB.email("Video finished with AI-side savings (cost overrun)", f"<p>Episode {episode}: the AI writing cost ran above {S('OVERRUN_FACTOR')}x its estimate, so: "
                  + "; ".join(steps) + ". Pictures, living stills and Kling clips were NOT reduced. Details: Cost_Log and Cache_Stats.</p>")
        return True
    except Exception as e:
        log(f"overrun email not sent: {str(e)[:120]}", "WARN", episode); return False

# ---------------------------------------------------------------- weekly deviation report
def deviation_report(days=7):
    """[(stage, measured per video, estimated per video, pct)] for stages off by more than DEVIATION_PCT, over videos with a summary row in the window."""
    import datetime as dt
    from whatifs.core import parse_iso
    rows = store().rows("Cost_Log"); since = now_utc() - dt.timedelta(days=days)
    eps = {r["episode_id"] for r in rows if r.get("item") == "ai_per_video_summary" and (parse_iso(str(r.get("ts"))) or since) >= since}
    if not eps: return []
    per = {}
    for r in rows:
        if r.get("episode_id") in eps and r.get("basis") != "summary":
            try: per[stage_of(r.get("item"), r.get("provider"))] = per.get(stage_of(r.get("item"), r.get("provider")), 0.0) + float(r.get("inr") or 0)
            except Exception: pass
    est = estimate_lines(); out = []
    for st_, e in est.items():
        if e <= 0: continue
        m = per.get(st_, 0.0) / len(eps); pct = (m - e) / e * 100
        if abs(pct) > S("DEVIATION_PCT", float): out.append((st_, round(m, 1), e, round(pct)))
    return out

def weekly_deviation_mail():
    wk = now_utc().strftime("%G-W%V")
    if S("DEVIATION_MAIL_WEEK") == wk: return False
    dev = deviation_report(); set_setting("DEVIATION_MAIL_WEEK", wk)
    if not dev: return False
    from whatifs import publish as PUB
    li = "".join(f"<li>{s}: measured Rs {m} per video vs estimated Rs {e} ({p:+d}%)</li>" for s, m, e, p in dev)
    PUB.email("Weekly cost check: estimate vs measured", f"<ul>{li}</ul><p>Estimates are planning numbers in Settings; nothing was changed automatically.</p>")
    return True

def preview_cost_flags(draft_id):
    """Script Preview: the writing this preview really cost vs its estimate (flag above +10 %), plus the full projected line list."""
    from whatifs.models import ai_estimate_inr
    m = ai_measured(draft_id); e = ai_estimate_inr()
    return {"lines": estimate_lines(), "ai_measured": round(m, 1), "ai_estimate": round(e, 1), "flag": m > e * 1.10}

# ---------------------------------------------------------------- kids-risk guard
def kids_check(vid, episode=None):
    """YouTube's computed made-for-kids value for an uploaded video (status.madeForKids; selfDeclaredMadeForKids is what we sent). TRUE = email at once.
    Returns True / False / None (unknown). Never changes the setting on YouTube."""
    if not S("KIDS_GUARD_ON", bool) or not vid: return None
    try:
        from whatifs import publish as PUB
        st_ = PUB.yt_status_full(vid) or {}
    except Exception as e:
        log(f"made-for-kids check unavailable: {str(e)[:120]}", "WARN", episode); return None
    mfk = st_.get("madeForKids")
    if mfk is True:
        try:
            PUB.email("URGENT: YouTube marked a video as made for kids",
                      f"<p>Video {vid} ({episode or ''}) is now 'made for kids' on YouTube (comments, notifications and personalised ads are off). "
                      "We uploaded it as NOT made for kids. Check it in YouTube Studio; if you disagree, change the audience setting there.</p>")
        except Exception as e: log(f"kids alert not sent: {str(e)[:120]}", "WARN", episode)
    return mfk
