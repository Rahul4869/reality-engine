"""Cost controls that never touch pictures: the per-stage estimator, the spend monitor and the overrun ladder. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json
from whatifs.core import S, log, store, iso, now_utc, month_spend, set_setting, JOB

# ---------------------------------------------------------------- estimator (per video, INR)
def estimate_lines():
    """{stage: INR} for one full video. Stage names match Cost_Log item prefixes (see stage_of)."""
    from whatifs import governor as G
    u = S("USD_INR", float)
    tr = S("TABLE_READ_EXTRA_INR", float) if str(S("TABLE_READ_MODE") or "").strip().lower() in ("on", "true", "yes", "1") else 0.0
    vis = G.full_episode_inr() - G.voice_think_inr() - S("LLM_EST_INR", float) - tr - G.v91_extra_inr()      # v9.1 lines are listed on their own
    return {"visuals": round(vis, 1), "ai_writing": round(S("LLM_EST_INR", float) + tr + S("ROOM_EXTRA_EST_INR", float), 1),
            "thinking": round(S("THINK_EST_INR", float), 1), "tts": round(S("TTS_EST_INR", float), 1),
            "show_devices": 0.0, "community": round(S("COMMENT_AGENT_EST_INR", float) / max(1, S("VIDEOS_PER_MONTH_EST", int)), 1),
            **v91_lines()}

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
