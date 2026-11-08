"""whatifs/governor.py v8.10 (TTS + thinking in every estimate, headroom, 4th-Kling proposal, Gemini credit; v8.7) - hard monthly cap (v8.7: the maintenance reserve is INSIDE the cap; v8.5: the B thumbnail is counted) WITH a pre-flight gate. Preserve minimum Kling shots; trim living-still animation first.
The controller estimates spend but cannot guarantee provider billing; Cost_Log is authoritative."""
import datetime as dt, re
from whatifs.core import S, store, month_spend, lifetime_spend_usd, now_utc

def month_key(s):
    """'2027-03', '2027-03-01', '01/03/2027', '3/1/2027', 'Mar 2027' or a Sheets date number -> '2027-03'. Unknown -> ''."""
    s = str(s or "").strip()
    if not s: return ""
    m = re.match(r"^(\d{4})[-/.](\d{1,2})", s)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a == 1 and b != 1: mon = b          # 01/03/2027 = day first (a typed month becomes the 1st)
        elif b == 1 and a != 1: mon = a        # 3/1/2027 = month first
        elif a > 12: mon = b
        elif b > 12: mon = a
        else: mon = b
        return f"{y:04d}-{mon:02d}" if 1 <= mon <= 12 else ""
    if re.match(r"^\d{5}(\.\d+)?$", s):     # Sheets serial date
        d = dt.date(1899, 12, 30) + dt.timedelta(days=int(float(s))); return d.strftime("%Y-%m")
    for f in ("%b %Y", "%B %Y", "%b-%Y", "%B-%Y", "%b %y", "%B %y", "%b-%y"):
        try: return dt.datetime.strptime(s, f).strftime("%Y-%m")
        except Exception: pass
    return ""

def money_num(s):
    """'1,234.50', '₹ 1,234', 'INR 900' -> float. Unknown -> 0."""
    t = re.sub(r"[^\d.\-]", "", str(s or ""))
    try: return float(t) if t not in ("", ".", "-") else 0.0
    except Exception: return 0.0

def last_month_revenue():
    last = (now_utc().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    rec = 0.0
    for r in store().rows("Revenue_Log"):
        if month_key(r.get("month", "")) == last:
            rec += money_num(r.get("inr_received"))
    return rec

def budget_mode():
    """v9.4a (K124): 'runway' only when the owner chose it (one tap); 'growth' by itself when last month had revenue (GROWTH_AUTO_ON); else 'standard'."""
    m = str(S("BUDGET_MODE") or "standard").strip().lower()
    if m == "runway": return "runway"
    if m == "growth" or (S("GROWTH_AUTO_ON", bool) and last_month_revenue() > 0): return "growth"
    return "standard"

def cap_inr():
    rec = last_month_revenue()
    base = min(S("BUDGET_CEILING_INR", float), max(S("BUDGET_FLOOR_INR", float), rec * S("REVENUE_SHARE", float)))
    mode = budget_mode()
    if mode == "runway": return min(base, S("RUNWAY_CAP_INR", float))
    if mode == "growth": return base + max(0.0, rec) * S("GROWTH_REVENUE_SHARE", float)          # revenue funds extra on top of the cap
    return base

def month_spend_of(prefixes):
    """v9.4a: this month's spend on Cost_Log rows whose role or item starts with one of the prefixes (earmarked lines, growth extras)."""
    mk = now_utc().strftime("%Y-%m"); tot = 0.0
    for r in store().rows("Cost_Log"):
        if r.get("basis") == "summary" or not str(r.get("ts", "")).startswith(mk): continue
        key = f"{r.get('role') or ''} {r.get('item') or ''}".lower()
        if any(key.startswith(p) or f" {p}" in key for p in prefixes):
            try: tot += float(r.get("inr") or 0)
            except Exception: pass
    return tot

def _prefixes(key): return [x.strip().lower() for x in str(S(key) or "").split(",") if x.strip()]

def earmark_left_inr():
    """v9.4a: the owner's earmarked money (faces + dashboard) not yet spent this month; production can never use it (Standard and Growth)."""
    if budget_mode() == "runway": return 0.0
    return max(0.0, S("BUDGET_EARMARK_INR", float) - month_spend_of(_prefixes("BUDGET_EARMARK_ITEMS")))

def specials_left_inr():
    """v10 (K134): the owner's +₹300 for the twice-monthly special reels, kept out of production (0 in Runway or when specials are off)."""
    if budget_mode() == "runway" or not S("SPECIALS_ON", bool): return 0.0
    from whatifs.specials import spent_this_month
    return max(0.0, S("SPECIALS_EARMARK_INR", float) - spent_this_month())

def max_long_videos():
    return {"runway": S("RUNWAY_MAX_LONG_PER_MONTH", int), "growth": S("GROWTH_MAX_LONG_PER_MONTH", int)}.get(budget_mode(), S("STANDARD_MAX_LONG_PER_MONTH", int))

def long_videos_this_month():
    mk = now_utc().strftime("%Y-%m")
    return sum(1 for e in store().rows("Episodes") if str(e.get("slot_et", "")).startswith(mk) and str(e.get("status", "")).upper() not in ("KILLED", "FAILED", "SKIPPED"))

def credit_cover_inr():
    """v9.4a: this month's spend covered by provider credits (money view only; budget gates still count list prices, the safe side).
    Claude credit counts only until CLAUDE_CREDIT_UNTIL (Max ends 10 Dec 2026); Gemini credit while GEMINI_CREDIT_USD_MONTH > 0."""
    fx = S("USD_INR", float) or 99.0; out = 0.0; today = now_utc().strftime("%Y-%m-%d")
    def spent(prefixes):
        return month_spend_of(prefixes)
    until = str(S("CLAUDE_CREDIT_UNTIL") or "")
    if S("CLAUDE_CREDIT_USD_MONTH", float) > 0 and (not until or today <= until):
        out += min(spent(["writer", "memo", "objection", "critic", "bible", "showrunner", "scout", "owner_chat", "hook", "punchup", "editor", "claude"]),
                   S("CLAUDE_CREDIT_USD_MONTH", float) * fx)
    if S("GEMINI_CREDIT_USD_MONTH", float) > 0:
        out += min(spent(["gemini", "tts", "voice", "judge", "fact", "vision", "thumb_eye", "faces"]), S("GEMINI_CREDIT_USD_MONTH", float) * fx)
    return out

def extras_allowed(est_inr, kind="extra"):
    """v9.4a (K124, protected core): (ok, reason) for any growth extra (Shorts Lab, research, chat...). Allowed only while (a) the month's extras stay inside
    GROWTH_ALLOWANCE_INR and (b) after this spend the remaining slots' production still fits. Extras pause first; production is never squeezed."""
    spent = month_spend_of(_prefixes("GROWTH_ITEMS"))
    if spent + est_inr > S("GROWTH_ALLOWANCE_INR", float): return False, f"growth allowance used (Rs {spent:.0f} of Rs {S('GROWTH_ALLOWANCE_INR', float):.0f})"
    left_slots = max(0, min(episodes_left_this_month(), max_long_videos() - long_videos_this_month()))
    need = left_slots * full_episode_inr()
    room = production_room_inr() - est_inr
    if room < need: return False, f"paused to protect production (Rs {room:.0f} left after this, Rs {need:.0f} needed for {left_slots} video(s))"
    return True, "ok"

def remaining_inr(): return cap_inr() - month_spend()

def production_room_inr():
    """v8.7: what production may still spend this month. The maintenance reserve is kept INSIDE the cap (it was above it until v8.6, so a month could total
    the cap + Rs 100): production stops BUDGET_MAINT_RESERVE_INR below the cap; the last part is for maintenance jobs and an in-flight overshoot only."""
    return remaining_inr() - max(0.0, S("BUDGET_MAINT_RESERVE_INR", float)) - earmark_left_inr() - specials_left_inr()      # v9.4a/v10: earmarks are never production money

def episodes_left_this_month():
    from zoneinfo import ZoneInfo
    days = [d.strip()[:3] for d in publish_days().split(",")]
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = now_utc().astimezone(ZoneInfo("America/New_York")).date(); n = 0; d = today
    while d.month == today.month:
        if names[d.weekday()] in days: n += 1
        d += dt.timedelta(days=1)
    return max(1, n)

# v8.2 budget tiers. Code sets the numbers; Claude and Gemini are briefed with them and write/plan inside them. The floor is never cut:
# 8:25 minimum (the 8:10 mid-roll line plus margin), 3 Kling clips, both roles, captions, full QC. Order of trimming: living stills, stills, runtime.
TIERS = (("full", 600, 52, 8), ("lean", 600, 48, 4), ("slim", 570, 44, 0), ("floor", 505, 40, 0))     # name, runtime cap (s), new stills, living stills

def tier_saving(tier, full=TIERS[0]):
    """Rupees a tier saves against the full tier (living stills, stills, a small share of the AI-writing cost for the shorter script)."""
    u = S("USD_INR", float)
    return (u * ((full[2] - tier[2]) * S("PRICE_STILL_USD", float) + (full[3] - tier[3]) * S("PRICE_LIVING_USD", float))
            + S("LLM_EST_INR", float) * 0.15 * (full[1] - tier[1]) / max(1, full[1]))

def plan_for_episode(est_full_inr, eps_left):
    """Pick the budget tier for ONE episode (see TIERS) and keep the configured minimum Kling clips in every tier.

    Returns tier, runtime_cap (seconds), stills, living, kling, hold, reason. The cap is a planning guard, not a provider-side spending lock;
    the estimate includes the AI-writing and table-read allowances but real usage can differ (see Cost_Log). Nothing below the floor tier is ever
    produced: if even the floor does not fit the rest of the month, hold=True and the caller must not start any paid work.
    """
    if S("VISUALS_PROTECTED", bool):     # v8.11: a higher AI estimate never trims pictures or clips (real spend in `rem` still counts in full)
        est_full_inr -= max(0.0, S("LLM_EST_INR", float) + S("THINK_EST_INR", float) + S("ROOM_EXTRA_EST_INR", float) - S("AI_TIER_BASE_INR", float))
    rem = production_room_inr()          # v8.7: inside the cap, minus the maintenance reserve
    per = rem / max(1, eps_left)
    minimum_kling = max(0, S("KLING_MIN_CLIPS", int))
    requested_kling = max(minimum_kling, S("KLING_CLIPS", int))
    margin = S("BUDGET_SAFETY_MARGIN", float)
    cap_run = min(S("RUNTIME_MAX_SEC", int), TIERS[0][1]); run_min = max(S("RUNTIME_MIN_SEC", int) + 15, TIERS[-1][1])
    p = {"kling": requested_kling, "opus": True, "hold": False, "tier": "full", "reason": "full"}
    chosen = None
    for t in TIERS:                                    # richest tier that fits this video's fair share of the month
        cost = est_full_inr - tier_saving(t)
        if cost <= per and cost * margin <= rem: chosen = t; break
    if chosen is None:                                 # nothing fits the fair share: take the floor if the whole remaining month can still pay for it (the share is only a guide)
        floor_cost = est_full_inr - tier_saving(TIERS[-1])
        if floor_cost * margin <= rem: chosen = TIERS[-1]
        else:
            p.update(hold=True, tier="hold", living=0, stills=TIERS[-1][2], runtime_cap=TIERS[-1][1],
                     reason=f"budget hold: about Rs {rem:.0f} left this month, the cheapest complete episode needs about Rs {floor_cost * margin:.0f}")
            return p
    p.update(tier=chosen[0], runtime_cap=max(run_min, min(chosen[1], cap_run)), stills=chosen[2], living=min(chosen[3], S("LIVING_STILLS", int)),
             reason="full" if chosen[0] == "full" else f"budget tier '{chosen[0]}': runtime up to {chosen[1] // 60}:{chosen[1] % 60:02d}, {chosen[2]} new stills, {chosen[3]} living stills, {requested_kling} Kling clips kept")
    return p

def _balance(provider):
    funded = S("FAL_FUNDED_USD" if provider == "fal" else "ANTHROPIC_FUNDED_USD", float)
    return funded - lifetime_spend_usd(provider)
def monthly_cap_reached(maintenance=False):
    """Stop starting new paid generations once logged/active-session costs hit the monthly cap.
    maintenance=True (trend scout / policy watch / playbook research, learning, brief) may use the BUDGET_MAINT_RESERVE_INR kept INSIDE the cap (v8.7)."""
    return (remaining_inr() if maintenance else production_room_inr()) <= 0      # v8.7: maintenance may use the reserve, never more than the cap itself

def premium_images():
    """Premium (key-art) images per long video: the thumbnail + 2 reel covers, + the B thumbnail of the packaging rescue (v8.5). Reels 3-4 use free covers."""
    return 3 + (1 if S("PKG_RESCUE_ON", bool) else 0)

def min_episode_cost_inr():
    """Cheapest honest cost of ONE episode with the minimum Kling clips (used before an episode row is even created)."""
    u = S("USD_INR", float)
    usd = S("KLING_MIN_CLIPS", int) * S("PRICE_KLING_USD", float) + premium_images() * S("PRICE_THUMB_USD", float) + S("STILLS_MIN", int) * S("PRICE_STILL_USD", float)
    extra = S("TABLE_READ_EXTRA_INR", float) if S("TABLE_READ_MODE").strip().lower() in ("on", "true", "yes", "1") else 0.0
    return u * usd + S("LLM_EST_INR", float) + extra + voice_think_inr() + v91_extra_inr()

def v91_extra_inr():
    """v9.1: the small paid v9.1 lines per video (comment mining, AI drafts, the variety rewrite; their flags decide) so the budget sees them. 0 in safe mode."""
    try:
        from whatifs import costguard as CG
        return float(sum(CG.v91_lines().values()))
    except Exception: return 0.0

def voice_think_inr():
    """v8.10: the allowances the v8.9 estimate did not have: Gemini TTS (when it is the engine), model thinking tokens (billed as output) and the new
    room calls (two premise judges, Immersion Director, Owner's Cut)."""
    tts = S("TTS_EST_INR", float) if str(S("TTS_ENGINE") or "").strip().lower() == "gemini" else 0.0
    return tts + S("THINK_EST_INR", float) + S("ROOM_EXTRA_EST_INR", float)

def full_episode_inr(kling=None):
    """Honest cost of one FULL-tier episode at the current settings (pictures, clips, premium art, writing, table read, TTS, thinking)."""
    u = S("USD_INR", float); k = S("KLING_CLIPS", int) if kling is None else kling; full = TIERS[0]
    usd = k * S("PRICE_KLING_USD", float) + premium_images() * S("PRICE_THUMB_USD", float) + full[2] * S("PRICE_STILL_USD", float) + min(full[3], S("LIVING_STILLS", int)) * S("PRICE_LIVING_USD", float)
    extra = S("TABLE_READ_EXTRA_INR", float) if S("TABLE_READ_MODE").strip().lower() in ("on", "true", "yes", "1") else 0.0
    return u * usd + S("LLM_EST_INR", float) + extra + voice_think_inr() + v91_extra_inr()

def headroom():
    """v8.10: what is left this month after every remaining video is made at the full tier (+ the safety margin). Positive = room for more."""
    left = episodes_left_this_month(); need = full_episode_inr() * S("BUDGET_SAFETY_MARGIN", float) * left
    room = production_room_inr()
    return {"room_inr": round(room, 0), "videos_left": left, "need_inr": round(need, 0), "headroom_inr": round(room - need, 0),
            "per_video_inr": round(full_episode_inr(), 0), "cap_inr": round(cap_inr(), 0), "spent_inr": round(month_spend(), 0)}

def kling4_proposal():
    """A 4th Kling clip is proposed ONLY when the headroom pays for it in every remaining video (with the safety margin). None otherwise."""
    if not S("KLING_4TH_PROPOSE_ON", bool) or S("KLING_CLIPS", int) >= 4: return None
    h = headroom(); extra = S("PRICE_KLING_USD", float) * S("USD_INR", float) * S("BUDGET_SAFETY_MARGIN", float) * h["videos_left"]
    if h["headroom_inr"] < extra: return None
    return (f"Headroom this month: about Rs {h['headroom_inr']:.0f} after the {h['videos_left']} remaining video(s) at full quality. A 4th Kling clip in each "
            f"costs about Rs {extra:.0f} in total, so it fits: set KLING_CLIPS to 4 in Settings to use it (set it back to 3 any time).")

def gemini_left_usd():
    """Estimated prepaid Gemini credit left (GEMINI_FUNDED_USD minus everything logged for provider google, TTS included). None = not tracked."""
    f = S("GEMINI_FUNDED_USD", float)
    return None if f <= 0 else f - lifetime_spend_usd("google")

def publish_days():
    """v9.4a: the publishing days of the current mode (Runway: RUNWAY_PUBLISH_DAYS)."""
    return S("RUNWAY_PUBLISH_DAYS") if budget_mode() == "runway" else S("PUBLISH_DAYS")

def can_start_episode():
    """(ok, reason). False = do not start paid work for a new episode this month; already scheduled videos still publish."""
    if long_videos_this_month() >= max_long_videos():
        return False, f"{budget_mode()} mode makes at most {max_long_videos()} long videos a month (this month's are done)"
    need = min_episode_cost_inr() * S("BUDGET_SAFETY_MARGIN", float); rem = production_room_inr()
    return rem >= need, f"Rs {rem:.0f} left for production this month (Rs {S('BUDGET_MAINT_RESERVE_INR', float):.0f} of the cap is kept for maintenance), a minimum episode needs about Rs {need:.0f}"

def fal_allowed():
    # Do not start new image/video jobs once the monthly budget is exhausted.
    return not monthly_cap_reached() and (S("AUTO_RELOAD_ON", bool) or _balance("fal") > 0.4)

def claude_allowed():
    # When the cap is reached, model routing should prefer non-Claude fallback providers.
    return not monthly_cap_reached() and (S("AUTO_RELOAD_ON", bool) or _balance("anthropic") > 0.4)

def opus_allowed(): return claude_allowed() and production_room_inr() > 150

def runway_days(provider):
    usd = lifetime_spend_usd(provider)
    rows = [r for r in store().rows("Cost_Log") if r.get("provider") == provider]
    if not rows: return 999
    first = min(str(r["ts"]) for r in rows)
    try: days = max(1.0, (now_utc() - dt.datetime.strptime(first, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)).days or 1)
    except Exception: days = 30
    per_day = usd / days
    return 999 if per_day <= 0 else _balance(provider) / per_day

