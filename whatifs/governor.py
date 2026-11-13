"""The money governor: hard monthly cap with a pre-flight gate, per-episode estimates, the extras guard and the breakout fund. See docs/CURRENT/SYSTEM.md."""
import datetime as dt, re
from whatifs.core import S, store, month_spend, lifetime_spend_usd, now_utc, set_setting, log

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

def month_override_inr(mk=None):
    """v11 (owner 2026-11-09): a one-month cap set by the owner, e.g. MONTH_CAP_OVERRIDES = '2026-11=5226' (Rs 1,226 spent + Rs 4,000 approved for the
    rest of November). None when this month has no override."""
    mk = mk or now_utc().strftime("%Y-%m")
    for part in str(S("MONTH_CAP_OVERRIDES") or "").split(","):
        k, _, v = part.strip().partition("=")
        if k.strip() == mk:
            try: return float(v)
            except ValueError: return None
    return None

def breakout_fund_inr():
    """v11: last month's unspent money carried in as a BREAKOUT FUND (capped at BREAKOUT_FUND_CAP_INR), usable only by breakout follow-ups and extra long
    episodes on proven topics (kind 'breakout'); 0 when off or not set for this month (set once at the month's first tick by rollover_month())."""
    if not S("BREAKOUT_FUND_ON", bool) or str(S("BREAKOUT_FUND_MONTH") or "") != now_utc().strftime("%Y-%m"): return 0.0
    return max(0.0, S("BREAKOUT_FUND_INR", float))

BREAKOUT_EP_PREFIX = "BRK"      # follow-ups produced for a breakout use episode ids starting with this, so every one of their costs is counted here

def breakout_spend_inr():
    mk = now_utc().strftime("%Y-%m"); tot = 0.0; pre = _prefixes("BREAKOUT_ITEMS")
    for r in store().rows("Cost_Log"):
        if r.get("basis") == "summary" or not str(r.get("ts", "")).startswith(mk): continue
        key = f"{r.get('role') or ''} {r.get('item') or ''}".lower()
        if str(r.get("episode_id") or "").startswith(BREAKOUT_EP_PREFIX) or any(key.startswith(x) or f" {x}" in key for x in pre):
            try: tot += float(r.get("inr") or 0)
            except Exception: pass
    return tot

def breakout_fund_left_inr():
    return max(0.0, breakout_fund_inr() - breakout_spend_inr())

def rollover_month(now=None):
    """Once per month: record last month's cap/spend and set this month's breakout fund = min(cap, unspent). Idempotent."""
    now = now or now_utc(); mk = now.strftime("%Y-%m")
    if str(S("BREAKOUT_FUND_MONTH") or "") == mk: return None
    prev_cap, prev_spend = S("LAST_MONTH_CAP_INR", float), S("LAST_MONTH_SPEND_INR", float)
    fund = min(S("BREAKOUT_FUND_CAP_INR", float), max(0.0, prev_cap - prev_spend)) if (S("BREAKOUT_FUND_ON", bool) and prev_cap > 0) else 0.0
    set_setting("BREAKOUT_FUND_INR", f"{fund:.0f}"); set_setting("BREAKOUT_FUND_MONTH", mk)
    log(f"month {mk}: breakout fund Rs {fund:.0f} (last month cap Rs {prev_cap:.0f}, spent Rs {prev_spend:.0f})")
    return fund

def record_month_close():
    """Keeps LAST_MONTH_* current every tick (the values at month end are what rollover uses)."""
    set_setting("LAST_MONTH_CAP_INR", f"{cap_inr():.0f}"); set_setting("LAST_MONTH_SPEND_INR", f"{month_spend():.0f}")

def cap_inr():
    rec = last_month_revenue()
    base = min(S("BUDGET_CEILING_INR", float), max(S("BUDGET_FLOOR_INR", float), rec * S("REVENUE_SHARE", float)))
    ov = month_override_inr()
    if ov is not None: base = ov                                                              # v11: the owner's one-month cap
    mode = budget_mode()
    if mode == "runway": return min(base, S("RUNWAY_CAP_INR", float))
    if mode == "growth": return base + max(0.0, rec) * S("GROWTH_REVENUE_SHARE", float) + breakout_fund_inr()   # revenue funds extra on top of the cap
    return base + breakout_fund_inr()                                                         # v11: the carried-in breakout fund (breakout use only)

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
    if kind == "breakout":                                                                    # v11: breakout follow-ups first use the carried-in fund
        if est_inr <= breakout_fund_left_inr(): return True, "breakout fund"
    elif month_spend() + est_inr > S("BUDGET_GUARD_PCT", float) / 100.0 * cap_inr():          # v11: the 90% guard pauses extras (never production)
        _guard_alert()
        return False, f"paused: the month is at {100 * month_spend() / max(1.0, cap_inr()):.0f}% of the cap (guard {S('BUDGET_GUARD_PCT', float):.0f}%)"
    spent = month_spend_of(_prefixes("GROWTH_ITEMS"))
    if spent + est_inr > S("GROWTH_ALLOWANCE_INR", float): return False, f"growth allowance used (Rs {spent:.0f} of Rs {S('GROWTH_ALLOWANCE_INR', float):.0f})"
    left_slots = max(0, min(episodes_left_this_month(), max_long_videos() - long_videos_this_month()))
    need = left_slots * full_episode_inr()
    room = production_room_inr() - est_inr
    if room < need: return False, f"paused to protect production (Rs {room:.0f} left after this, Rs {need:.0f} needed for {left_slots} video(s))"
    return True, "ok"

def _guard_alert():
    """One WhatsApp/email card per month when the guard first pauses extras."""
    mk = now_utc().strftime("%Y-%m")
    if str(S("BUDGET_GUARD_ALERTED") or "") == mk: return
    try:
        from whatifs import notify as NT
        NT.send("budget_guard", f"Budget guard: Rs {month_spend():.0f} of Rs {cap_inr():.0f} spent this month. Extras (spin-offs, tool tests, Shorts above 1 a day) "
                "are paused; scheduled long episodes keep their money.", [("OK", "OK")], tier="now", default="ok", expires_h=48, dedupe_key=f"guard|{mk}")
    except Exception: pass
    set_setting("BUDGET_GUARD_ALERTED", mk)

def org_left_inr():
    """v12 B5: the organisation's own thinking money not yet spent this month - the unspent part of the monthly caps of the WIRED departments that
    think for money (R&D Rs 300 and the Review Board Rs 120 today, while research is on) - is never production money. 0 in Runway or with the
    organisation off. Without this the month's plan would count the same rupees twice."""
    if budget_mode() == "runway": return 0.0
    try:
        from whatifs.org import runner as ORG, registry as REG
        if not ORG.on(): return 0.0
        caps = REG.caps(); res = S("RESEARCH_ON", bool)
        return round(sum(max(0.0, float(caps[d]) - REG.spent(d)) for d in caps if d in REG.ENTRY and (res or d not in ("D2", "D3"))), 2)
    except Exception as e:
        log(f"organisation reserve not computed: {str(e)[:100]}", "WARN"); return 0.0

def remaining_inr(): return cap_inr() - month_spend()

def production_room_inr():
    """v8.7: what production may still spend this month. The maintenance reserve is kept INSIDE the cap (it was above it until v8.6, so a month could total
    the cap + Rs 100): production stops BUDGET_MAINT_RESERVE_INR below the cap; the last part is for maintenance jobs and an in-flight overshoot only."""
    return (remaining_inr() - max(0.0, S("BUDGET_MAINT_RESERVE_INR", float)) - earmark_left_inr() - specials_left_inr()      # v9.4a/v10: earmarks are never production money
            - breakout_fund_left_inr()                                                                                     # v11: nor is the breakout fund
            - org_left_inr())                                                                                              # v12 B5: nor the organisation's thinking caps

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

def tier_saving(tier, full=TIERS[0], living_s=None, floor_s=None):
    """Rupees a tier saves against the full tier (living stills, stills, a small share of the AI-writing cost for the shorter script). v12 V2d-b:
    with the motion ladder (`living_s` = the living seconds the full tier buys) a smaller tier keeps the FLOOR's living seconds and saves the rest -
    never more: a long video under the floor of moving pictures is not made."""
    u = S("USD_INR", float)
    from whatifs import media as MD                          # v12 V2d: a still at the price the code really pays (megapixels rounded up), as the cost lines count it
    if living_s is not None:
        from whatifs import clips as CL
        lv = 0.0 if tier[0] == full[0] else max(0.0, float(living_s) - float(floor_s or 0)) * living_usd_s()
    else: lv = (full[3] - tier[3]) * S("PRICE_LIVING_USD", float)
    return (u * ((full[2] - tier[2]) * MD.still_usd(S("STILL_W", int), S("STILL_H", int)) + lv)
            + S("LLM_EST_INR", float) * 0.15 * (full[1] - tier[1]) / max(1, full[1]))

def plan_for_episode(est_full_inr, eps_left, living_s=None, floor_s=None):
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
        cost = est_full_inr - tier_saving(t, living_s=living_s, floor_s=floor_s)
        if cost <= per and cost * margin <= rem: chosen = t; break
    if chosen is None:                                 # nothing fits the fair share: take the floor if the whole remaining month can still pay for it (the share is only a guide)
        floor_cost = est_full_inr - tier_saving(TIERS[-1], living_s=living_s, floor_s=floor_s)
        if floor_cost * margin <= rem: chosen = TIERS[-1]
        else:
            p.update(hold=True, tier="hold", living=0, stills=TIERS[-1][2], runtime_cap=TIERS[-1][1],
                     reason=f"budget hold: about Rs {rem:.0f} left this month, the cheapest complete episode needs about Rs {floor_cost * margin:.0f}")
            return p
    if living_s is not None:                           # v12 V2d-b: the living tier in SECONDS - the full tier buys what the month's money gave this video, every smaller tier the floor
        from whatifs import clips as CL
        ls = int(living_s if chosen[0] == TIERS[0][0] else min(int(living_s), int(floor_s or 0)))
        p.update(living_s=ls, living=ls // max(1, int(CL.SCENE_S)))
    p.update(tier=chosen[0], runtime_cap=max(run_min, min(chosen[1], cap_run)), stills=chosen[2], living=p["living"] if living_s is not None else min(chosen[3], S("LIVING_STILLS", int)),
             reason="full" if chosen[0] == "full" else f"budget tier '{chosen[0]}': runtime up to {chosen[1] // 60}:{chosen[1] % 60:02d}, {chosen[2]} new stills, "
                    + (f"{p.get('living_s')} living seconds (the floor)" if living_s is not None else f"{chosen[3]} living stills") + f", {requested_kling} Kling clips kept")
    return p

def _balance(provider):
    funded = S("FAL_FUNDED_USD" if provider == "fal" else "ANTHROPIC_FUNDED_USD", float)
    return funded - lifetime_spend_usd(provider)
def monthly_cap_reached(maintenance=False):
    """Stop starting new paid generations once logged/active-session costs hit the monthly cap.
    maintenance=True (trend scout / policy watch / playbook research, learning, brief) may use the BUDGET_MAINT_RESERVE_INR kept INSIDE the cap (v8.7)."""
    return (remaining_inr() if maintenance else production_room_inr()) <= 0      # v8.7: maintenance may use the reserve, never more than the cap itself

def premium_images():
    """Premium (key-art) images per long video: the thumbnail, + the B thumbnail of the packaging rescue (v12 V2c-b2b: no reel covers - a long video makes no cut-down reels)."""
    return 1 + (1 if S("PKG_RESCUE_ON", bool) else 0)

def long_kind():
    """Which long video the NEXT one is, for the estimate: 'ladder' = a promoted Short waits for it and it will open on that Short's footage (one
    scene and one start picture fewer, no hook lab); else 'long' (an override, or the ladder off: it opens on its own pictures)."""
    try:
        from whatifs import ladder as LAD, opening as OP
        return "ladder" if (LAD.on() and OP.on() and LAD.waiting() and not str(S("OWNER_NEXT_PREMISE") or "").strip()) else "long"
    except Exception: return "long"

def min_episode_cost_inr():
    """Cheapest honest cost of ONE episode with the minimum animated scenes (used before an episode row is even created). v12 V2d: the lines of
    the one cost model (costguard.lines)."""
    from whatifs import costguard as CG
    return CG.total(CG.lines(long_kind(), kling=S("KLING_MIN_CLIPS", int), stills=S("STILLS_MIN", int), living=0))

OPENING_EST_S = 12            # the seconds of its Short's footage a long video about a promoted Short is COUNTED to show before it exists (the first whole runs showed 12.9 to 16.5: counted low, so the floor is met by what is bought)

def living_usd_s():
    """USD for one second of a still brought to life (0 with the motion ladder off)."""
    from whatifs import clips as CL
    r = CL.living(); return float(CL.usd_s(r)) if r else 0.0

def moving_floor(kind=None, runtime=None):
    """THE FLOOR of one long video (v12 V2d-b), before anything is spent: of `runtime` seconds at least MOVING_SHARE_MIN_LONG percent are moving pictures
    made by a model - its Short's footage (kind 'ladder': counted at OPENING_EST_S), its animated scenes and its LIVING stills. Returns {on, floor_s,
    target_s, own_s (footage + scenes), living_s (the floor's living seconds), living_target_s, inr_s}. Every estimate of a long video counts the
    floor's living seconds (costguard.lines); it never asks the month's split, so the split can ask it."""
    import math
    from whatifs import clips as CL
    kind = kind or long_kind(); run = float(runtime or S("RUNTIME_MAX_SEC", float)); usd = living_usd_s()
    k = max(0, S("KLING_CLIPS", int) - (1 if kind == "ladder" else 0)); own = k * CL.SCENE_S + (OPENING_EST_S if kind == "ladder" else 0)
    lo = max(0.0, S("MOVING_SHARE_MIN_LONG", float)); hi = max(lo, S("MOVING_SHARE_LONG", float))
    out = {"on": usd > 0, "kind": kind, "runtime_s": run, "own_s": own, "floor_pct": lo, "target_pct": hi, "floor_s": math.ceil(lo / 100 * run), "target_s": math.ceil(hi / 100 * run)}
    if usd <= 0: return dict(out, living_s=0, living_target_s=0, inr_s=0.0)
    lf = max(0, out["floor_s"] - own)
    return dict(out, living_s=lf, living_target_s=max(lf, out["target_s"] - own), inr_s=round(usd * (S("USD_INR", float) or 99.0), 4))

def moving_plan(kind=None, runtime=None, mine=False, now=None):
    """THE MOVING SECONDS THIS LONG VIDEO GETS (v12 V2d-b): the floor, plus what the month's split leaves free (`split()["free_inr"]`: after the long
    videos still to come at their floor, the Shorts still to make and the reserve), shared by the long videos still to make, up to the target
    MOVING_SHARE_LONG. `mine` = the video being planned already has its row on tab Episodes, so the split no longer counts it among those to
    come: its own floor cost is taken from what is free first. Returns moving_floor's fields with living_s = what this video buys, bought_pct
    (the share its plan reaches) and free_inr."""
    mf = moving_floor(kind, runtime)
    if not mf["on"]: return dict(mf, bought_pct=0.0, free_inr=0.0)
    m = S("BUDGET_SAFETY_MARGIN", float); sp = split(now); n = sp["long_left"] + (1 if mine else 0)
    free = float(sp["free_inr"]) - (full_episode_inr(kind=mf["kind"]) * m if mine else 0.0)
    extra = max(0, int(free // (n * m * mf["inr_s"]))) if n > 0 else 0
    ls = min(mf["living_target_s"], mf["living_s"] + extra)
    return dict(mf, living_floor_s=mf["living_s"], living_s=ls, bought_pct=round(100.0 * (mf["own_s"] + ls) / max(1.0, mf["runtime_s"]), 1), free_inr=round(free, 0))

def palace_prompt_inr():
    """v12 B6a: the Palace playbook inside the creative model prompts (about 2,000 input tokens at the end of about 15 creative calls, outside the cached layers, plus the citations)."""
    return S("PALACE_PROMPT_EST_INR", float) if (S("ORG_PROMPT_INJECT", bool) and S("ORG_ON", bool) and S("PALACE_ON", bool)) else 0.0

def full_episode_inr(kling=None, kind=None):
    """Honest cost of one FULL-tier long video at the current settings. v12 V2d: the sum of the lines of the one cost model (costguard.lines) -
    every paid second and call; kind None = the next long video's own kind (long_kind)."""
    from whatifs import costguard as CG
    return CG.total(CG.lines(kind or long_kind(), kling=kling))

def short_inr():
    """What one Short costs as the month's plan counts it: the estimate of each Short format, weighted by the formats' shares."""
    from whatifs import costguard as CG, formats as FMT
    sh = FMT.short_shares(); tot = sum(sh.values()) or 1
    return sum(CG.total(CG.lines("short", fmt=f)) * w for f, w in sh.items()) / tot

def _org_caps_inr():
    """The monthly caps of the wired departments that think for money (their whole caps: the month's plan is made before anything is spent)."""
    if budget_mode() == "runway": return 0.0
    try:
        from whatifs.org import runner as ORG, registry as REG
        if not ORG.on(): return 0.0
        caps = REG.caps(); res = S("RESEARCH_ON", bool)
        return float(sum(float(caps[d]) for d in caps if d in REG.ENTRY and (res or d not in ("D2", "D3"))))
    except Exception: return 0.0

def month_room_inr():
    """What a whole month has for production BEFORE anything is spent: the cap less the breakout fund (it has its own use), the maintenance
    reserve, the owner's earmarks and the organisation's thinking caps."""
    run = budget_mode() == "runway"
    return (cap_inr() - breakout_fund_inr() - max(0.0, S("BUDGET_MAINT_RESERVE_INR", float)) - (0.0 if run else S("BUDGET_EARMARK_INR", float))
            - (0.0 if run or not S("SPECIALS_ON", bool) else S("SPECIALS_EARMARK_INR", float)) - _org_caps_inr())

def line_usd_s():
    """THE LINE (v12 V2d): the highest price, in USD for one second of hero clip, at which the month's whole plan still fits - the long videos
    with the safety margin, SHORTS_PER_MONTH Shorts, everything that is not a hero clip at its own price, and MONTH_RESERVE_INR kept free. The clip
    market picks the best-ranked model at or under it (whatifs/clips.py). It does not depend on the PRICE of the model in use."""
    from whatifs import costguard as CG, formats as FMT
    u = S("USD_INR", float) or 99.0; m = S("BUDGET_SAFETY_MARGIN", float); n_long = max_long_videos(); n_short = max(0, S("SHORTS_PER_MONTH", int)) if S("SHORTS_TRACK_ON", bool) else 0
    def split_of(L):                                              # v12 V2d-b: the living seconds of the floor are seconds of the same market - the line must pay them too
        hero = [l for l in L if l["key"] == "hero_clips" or (l["key"] == "living_clips" and l.get("unit") == "s")]
        return (CG.total(L) - sum(l["inr"] for l in hero)), float(sum(l["n"] for l in hero))
    lo, ls = split_of(CG.lines("long")); sh = FMT.short_shares(); tot = sum(sh.values()) or 1; so = ss = 0.0
    for f, w in sh.items():
        o, s_ = split_of(CG.lines("short", fmt=f)); so += o * w / tot; ss += s_ * w / tot
    secs = n_long * ls * m + n_short * ss
    if secs <= 0: return 0.0
    return max(0.0, (month_room_inr() - max(0.0, S("MONTH_RESERVE_INR", float)) - n_long * lo * m - n_short * so) / secs / u)

def split(now=None):
    """THE MONTH'S SPLIT as the money sees it NOW: what production may still spend, what the long videos still to come need (with the safety
    margin), the part of MONTH_RESERVE_INR that belongs to the days left, what one Short costs - and how many Shorts FIT beside the long videos:
    this month in all (`fit`) against what SHORTS_PER_MONTH asks (`plan`). `fits` False = the plan is larger than the money: the cadence makes
    `fit` Shorts, spread over the month, and the owner is told once (split_tell)."""
    import calendar
    from whatifs import shorts2 as SH
    now = now or now_utc(); days = calendar.monthrange(now.year, now.month)[1]; left_days = days - now.day + 1
    plan = max(0, S("SHORTS_PER_MONTH", int)); made = SH.made_this_month(now)
    long_left = max(0, min(episodes_left_this_month(), max_long_videos() - long_videos_this_month()))
    need_long = long_left * full_episode_inr() * S("BUDGET_SAFETY_MARGIN", float)
    reserve = max(0.0, S("MONTH_RESERVE_INR", float)) * left_days / days
    room = production_room_inr(); one = max(1.0, short_inr())
    more = max(0, int((room - need_long - reserve) // one))
    fit = made + min(max(0, plan - made), more)
    return {"room_inr": round(room, 0), "long_left": long_left, "long_inr": round(full_episode_inr(), 1), "need_long_inr": round(need_long, 0), "reserve_inr": round(reserve, 0),
            "short_inr": round(one, 1), "made": made, "plan": plan, "fit": fit, "more": more, "fits": fit >= plan, "days_left": left_days,
            "free_inr": round(room - need_long - reserve - max(0, fit - made) * one, 0)}

def split_tell(now=None):
    """Once a month, when fewer Shorts fit the money than SHORTS_PER_MONTH asks: one message with both numbers and why. True = sent now."""
    now = now or now_utc(); mk = now.strftime("%Y-%m")
    if not S("SHORTS_TRACK_ON", bool) or str(S("SPLIT_TOLD_MONTH") or "") == mk: return False
    sp = split(now)
    if sp["fits"]: return False
    set_setting("SPLIT_TOLD_MONTH", mk)
    try:
        from whatifs import notify as NT
        NT.send("split", f"This month's money pays {sp['fit']} Shorts, not the {sp['plan']} planned: a Short costs about Rs {sp['short_inr']:.0f}, the {sp['long_left']} long "
                f"video(s) still to come keep Rs {sp['need_long_inr']:.0f}, and Rs {sp['room_inr']:.0f} is left for production. The Shorts are spread over the rest of the "
                "month; no quality check was lowered. More Shorts need a cheaper clip model or a higher cap.", [("OK", "OK")], tier="week", default="ok", expires_h=24 * 6,
                dedupe_key=f"split|{mk}")
    except Exception as e: log(f"the owner was not told about the month's split: {str(e)[:100]}", "WARN")
    return True

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

def long_videos_per_week():
    """How many long-video slots a week the current mode publishes (= the number of publishing days)."""
    return max(1, len([d for d in str(publish_days() or "").split(",") if d.strip()]))

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

