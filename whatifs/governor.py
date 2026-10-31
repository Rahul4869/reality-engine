"""whatifs/governor.py v8.7 - hard monthly cap (v8.7: the maintenance reserve is INSIDE the cap; v8.5: the B thumbnail is counted) WITH a pre-flight gate. Preserve minimum Kling shots; trim living-still animation first.
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

def cap_inr():
    last = (now_utc().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    rec = 0.0
    for r in store().rows("Revenue_Log"):
        if month_key(r.get("month", "")) == last:
            rec += money_num(r.get("inr_received"))
    return min(S("BUDGET_CEILING_INR", float), max(S("BUDGET_FLOOR_INR", float), rec * S("REVENUE_SHARE", float)))

def remaining_inr(): return cap_inr() - month_spend()

def production_room_inr():
    """v8.7: what production may still spend this month. The maintenance reserve is kept INSIDE the cap (it was above it until v8.6, so a month could total
    the cap + Rs 100): production stops BUDGET_MAINT_RESERVE_INR below the cap; the last part is for maintenance jobs and an in-flight overshoot only."""
    return remaining_inr() - max(0.0, S("BUDGET_MAINT_RESERVE_INR", float))

def episodes_left_this_month():
    from zoneinfo import ZoneInfo
    days = [d.strip()[:3] for d in S("PUBLISH_DAYS").split(",")]
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
    return u * usd + S("LLM_EST_INR", float) + extra

def can_start_episode():
    """(ok, reason). False = do not start paid work for a new episode this month; already scheduled videos still publish."""
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

