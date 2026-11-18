"""Strategy (D1): the loop - a rule book as data, at most one decision a review, each a ticket told to him with an Undo. See docs/CURRENT/SYSTEM.md."""
# v12 V4: every decision a ticket the Execution Engine executes and verifies, told to the owner with an Undo link that never dies, settled against the
# gate's own arithmetic, frozen when he takes a hand. What stays his is a list (OWNER_ONLY) a test holds.
from __future__ import annotations
import calendar, datetime as dt, hashlib, json, math, os, statistics
from whatifs.core import S, log, store, iso, now_utc, parse_iso, set_setting, scrub, DEFAULTS

TAB = "Decisions"
IN_FORCE = ("decided", "applied")                         # a decision whose ticket the engine has not finished yet
TAKEN_BACK = ("rolled_back", "refused", "no_effect", "void")
DECIDED_MAX_H = 26                                        # a row "decided" this long whose ticket is not on tab Memos: its memo is sent once more, then it is void
OWNER_ONLY = ("BUDGET_CEILING_INR", "BUDGET_FLOOR_INR", "MONTH_CAP_OVERRIDES", "BUDGET_MODE", "PAUSED", "PUBLISH_DAYS",
              "CREDIT_COVER_MONTH_MAX_INR", "CLAUDE_CREDIT_USD_MONTH", "CLAUDE_CREDIT_FROM", "CLAUDE_CREDIT_UNTIL",     # item 53: the cap and deleting stay his
              "ORG_BUILDS_ON")     # RR-36: only B-ORG turns the organisation's builds on

def on():
    """Strategy is part of the CEO (STRATEGY_ON); FALSE = exactly the code V4 is built on (the Monday re-planner card, no review)."""
    return S("STRATEGY_ON", bool)

def _js(v, d):
    if isinstance(v, (dict, list)): return v
    try: x = json.loads(v) if str(v or "").strip() else d
    except (TypeError, ValueError): x = d
    return x if isinstance(x, type(d)) else d

def _rows(st=None): return (st or store()).rows(TAB)

def _save(st, row, **ch):
    row.update(ch); st.update(TAB, "id", row["id"], {k: (json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v) for k, v in ch.items()}); return row

def _cell(key): return str(S(key) if S(key) is not None else "").strip()

# ------------------------------------------------------------------ the vocabulary a prediction may name (one vocabulary for B8)
def _board(field):
    def read(now=None):
        from whatifs import scoreboard as SB
        rows = SB._rows(); return SB._num(rows[-1].get(field), float) if rows else None
    return read

def _first_days(now=None):
    """The median first-days measure of the Ladder's measured Shorts posted in the last 28 days (None without one)."""
    now = now or now_utc(); xs = [v for _a, t, v in short_items() if now - t <= dt.timedelta(days=28)]
    return float(statistics.median(xs)) if xs else None

def _hours_per_video(now=None):
    """The median `h` (ripe views x ripe seconds / 3600) of the long videos ripe in the last 56 days (None without one)."""
    now = now or now_utc(); xs = [v for _a, t, v, at in long_items() if at and now - at <= dt.timedelta(days=56)]
    return float(statistics.median(xs)) if xs else None

METRICS = {"shorts_engaged_90d": _board("shorts_90"), "long_hours_12m": _board("hours"), "shorts_engaged_first_days": _first_days,
           "long_hours_per_video_28d": _hours_per_video}
METRIC_WORDS = {"shorts_engaged_90d": "the Shorts views that count in 90 days", "long_hours_12m": "the long watch hours of 12 months",
                "shorts_engaged_first_days": "the views a Short holds in its first days", "long_hours_per_video_28d": "the watch hours a long video earns in its first 28 days"}
BOARD_WORDS = {"shorts": "the Shorts views that count", "hours": "the long watch hours", "subs": "subscribers"}

# ------------------------------------------------------------------ the rules (a rule is a row; a later batch adds a row)
def _slots_target(now):
    """RULE SLOTS (issue 2): the most long videos the calendar and the money hold - the largest n with 4 <= n <= min(8, the month's slots) whose month
    fits with the Shorts cell as it stands, else 4."""
    from whatifs import governor as G
    sh = S("SHORTS_PER_MONTH", int); top = min(8, G.slots(now)); fits = {}
    for n in range(4, top + 1): fits[n] = G.month_fit(n, sh, now=now)
    ok = [n for n, f in fits.items() if f["fits"]]; t = max(ok) if ok else 4
    why = (f"this month has {G.slots(now)} publishing days and the money holds {t} long videos beside {sh} Shorts"
           + (f" (Rs {fits[t]['free_inr']:.0f} free)" if t in fits else ""))
    return {"STANDARD_MAX_LONG_PER_MONTH": {"target": t, "why": why, "numbers": {"slots": G.slots(now), "shorts": sh, "free_inr": {str(n): f["free_inr"] for n, f in fits.items()}},
                                            "evidence": "ok", "count": ""}}

def short_items(st=None):
    """[(arm, posted, measure)]: a Ladder row with evidence "measured" whose `first` holds the engaged views of its first LADDER_READ_DAYS processed
    days - never `engaged`, the total to date that grows with every weekly reading - in publishing order."""
    out = []
    for r in (st or store()).rows("Ladder"):
        if r.get("evidence") != "measured" or not r.get("format"): continue
        f = _js(r.get("first"), {}); t = parse_iso(r.get("posted"))
        if "engaged" not in f or t is None: continue
        try: out.append((str(r["format"]), t, float(f["engaged"])))
        except (TypeError, ValueError): continue
    return sorted(out, key=lambda x: x[1])

def long_items(st=None):
    """[(arm, slot, h, ripe_at)]: a LIVE long video of the new code (its draw_json carries a format) with a RIPE reading; h = ripe_views x ripe_sec / 3600."""
    st = st or store(); an = {a.get("episode_id"): a for a in st.rows("Analytics") if a.get("ripe_at")}; out = []
    for e in st.rows("Episodes"):
        if e.get("status") != "LIVE" or e.get("episode_id") not in an: continue
        fmt = _js(e.get("draw_json"), {}).get("format"); t = parse_iso(e.get("slot_et")); a = an[e["episode_id"]]
        if not fmt or t is None: continue
        try: out.append((str(fmt), t, float(a["ripe_views"]) * float(a["ripe_sec"]) / 3600.0, parse_iso(a.get("ripe_at"))))
        except (TypeError, ValueError, KeyError): continue
    return sorted(out, key=lambda x: x[1])

def q1(xs): return statistics.quantiles(xs, n=4, method="inclusive")[0]

def _judged(rows, rule, key):
    return sorted([r for r in rows if r.get("rule") == rule and r["key"] == key and r["state"] == "judged"], key=lambda r: int(_js(r.get("numbers"), {}).get("point") or 0))

def judge_arms(rule, prefix, items, p1, p2, omin, noun, now=None, st=None):
    """JUDGEMENT POINTS (research 7): an arm X is judged ONCE at each point p - its FIRST p items (by publishing time) against every item of the OTHER
    arms published up to X's p-th. BELOW = median(X) < Q1(others). At p1: below -> half the share it held, down to a multiple of 5; at p2: below -> 0
    (never for the last arm above 0), not below -> the share it held before p1. Writes the rows (state judged); returns how many."""
    st = st or store(); now = now or now_utc(); rows = _rows(st); n = 0
    arms = sorted({a for a, *_r in items} | {k[len(prefix):] for k in DEFAULTS if k.startswith(prefix)})
    for arm in arms:
        key = prefix + arm; mine = [x for x in items if x[0] == arm]; done = {int(_js(r.get("numbers"), {}).get("point") or 0) for r in _judged(rows, rule, key)}
        for p in (p1, p2):
            if len(mine) < p or p in done: continue
            first = [x[2] for x in mine[:p]]; tp = mine[p - 1][1]; others = [x[2] for x in items if x[0] != arm and x[1] <= tp]
            if len(others) < omin: continue
            med, q = float(statistics.median(first)), float(q1(others)); below = med < q; cell = int(float(_cell(key) or 0))
            if p == p1: held = cell; target = (cell // 2) // 5 * 5 if below else cell
            else:
                held = int(_js((_judged(rows, rule, key) or [{}])[0].get("numbers"), {}).get("held") or cell)
                last = all(int(float(_cell(k) or 0)) == 0 for k in DEFAULTS if k.startswith(prefix) and k != key)
                target = (cell if last else 0) if below else held
            verdict = (f"below: the median of its first {p} {noun} ({med:g}) is under the others' first quartile ({q:g}, {len(others)} {noun})" if below
                       else f"not below: the median of its first {p} {noun} ({med:g}) against the others' first quartile ({q:g}, {len(others)} {noun})")
            if p == p2 and below and target: verdict += " - the last arm above 0 keeps its share"
            row = {"id": _did(rule, key, str(p), str(target), now), "ts": iso(now), "rule": rule, "key": key, "old": str(cell), "new": str(p), "why": verdict, "ticket": "",
                   "numbers": json.dumps({"point": p, "median": med, "q1": q, "n_others": len(others), "verdict": "below" if below else "not below", "target": target, "held": held}),
                   "effect_before": "", "effect_after": "", "prediction": "", "state": "judged", "told": "", "frozen_until": "", "observed": "", "scored": "", "briefed": ""}
            st.append(TAB, [row]); rows.append(row); n += 1
    return n

def arm_targets(rule, prefix, items, p1, omin, noun, now=None, st=None):
    """{key: target entry}: the newest judgement's target (unless the decision toward it was undone: then the cell); thin evidence -> the cell, counted."""
    rows = _rows(st); out = {}
    arms = sorted({k[len(prefix):] for k in DEFAULTS if k.startswith(prefix)})
    for arm in arms:
        key = prefix + arm; cell = _cell(key); js = _judged(rows, rule, key); mine = [x for x in items if x[0] == arm]
        if js:
            nb = _js(js[-1].get("numbers"), {}); t = str(nb.get("target"))
            undone = any(r["key"] == key and r["state"] == "undone" and r["ts"] >= js[-1]["ts"] for r in rows)
            out[key] = {"target": cell if undone else t, "why": js[-1]["why"], "numbers": nb, "evidence": "ok", "count": ""}
        else:
            others = [x for x in items if x[0] != arm]
            out[key] = {"target": cell, "why": f"{arm}: {len(mine)} of {p1} {noun} measured", "numbers": {"n": len(mine)}, "evidence": "thin",
                        "count": f"{arm} {len(mine)} of {p1} {noun}" if len(mine) < p1 or len(others) < omin else f"{arm} {len(mine)} of {p1} {noun}"}
    return out

def _short_arms_target(now):
    return arm_targets("SHORT_ARMS", "SHORT_SHARE_", short_items(), S("SHORT_ARM_MIN", int), S("SHORT_ARM_MIN", int), "Shorts", now)

def _arms_target(now):
    return arm_targets("ARMS", "FORMAT_SHARE_", long_items(), S("ARM_MIN_VIDEOS", int), S("ARM_OTHERS_MIN", int), "long videos", now)

def judge(now=None, st=None):
    """The review's judging pass (both arm rules, the risk line once a week)."""
    n = judge_arms("SHORT_ARMS", "SHORT_SHARE_", short_items(st), S("SHORT_ARM_MIN", int), S("SHORT_ARM_RETIRE", int), S("SHORT_ARM_MIN", int), "Shorts", now, st)
    n += judge_arms("ARMS", "FORMAT_SHARE_", [x[:3] for x in long_items(st)], S("ARM_MIN_VIDEOS", int), S("ARM_RETIRE_VIDEOS", int), S("ARM_OTHERS_MIN", int), "long videos", now, st)
    risk_row(now, st); return n

# ------------------------------------------------------------------ THE RISK LINE (rule SPLIT reads it)
def uploads(now=None, days=28, st=None):
    """(long, short) uploads in the last `days`: long = Episodes LIVE with a slot in the window; short = EVERY Specials row with a yt_id made in it."""
    st = st or store(); now = now or now_utc(); lo = now - dt.timedelta(days=days)
    lg = sum(1 for e in st.rows("Episodes") if e.get("status") == "LIVE" and parse_iso(e.get("slot_et")) and lo <= parse_iso(e["slot_et"]) <= now)
    sh = sum(1 for r in st.rows("Specials") if r.get("yt_id") and parse_iso(r.get("made") or r.get("ts")) and lo <= parse_iso(r.get("made") or r.get("ts")) <= now)
    return lg, sh

def risk_line(now=None, st=None):
    """("ok" | "worse" | "unknown", words): the v48 of the long videos of the last RISK_WINDOW_DAYS against the window before, beside the uploads."""
    st = st or store(); now = now or now_utc(); w = dt.timedelta(days=S("RISK_WINDOW_DAYS", int))
    pub = [(parse_iso(r.get("published")), float(r["v48"])) for r in st.rows("Monitor48") if r.get("kind") == "long" and str(r.get("v48") or "").strip() and parse_iso(r.get("published"))]
    cur = [v for t, v in pub if now - w <= t <= now]; prev = [v for t, v in pub if now - 2 * w <= t < now - w]
    n_min = S("RISK_MIN_LONG", int); u1, u2 = uploads(now, w.days, st), uploads(now - w, w.days, st)
    if len(cur) < n_min or len(prev) < n_min:
        return "unknown", f"not enough long videos yet ({len(cur)} and {len(prev)}; {n_min} are needed in each half)"
    mc, mp = statistics.median(cur), statistics.median(prev)
    words = (f"long videos at 48 hours: a median of {mc:.0f} views over {len(cur)} against {mp:.0f} over {len(prev)} in the four weeks before, "
             f"beside {u1[1]} against {u2[1]} short uploads")
    if mp < S("RISK_MIN_VIEWS", float): return "unknown", words + " (too few views to judge)"
    return ("worse" if mc < (1 - S("RISK_DROP_PCT", float) / 100.0) * mp else "ok"), words

def risk_row(now=None, st=None):
    """Read weekly and stored as a row 'judged' of rule RISK."""
    st = st or store(); now = now or now_utc()
    last = [r for r in _rows(st) if r.get("rule") == "RISK"]
    if last and now - (parse_iso(sorted(last, key=lambda r: r["ts"])[-1]["ts"]) or now) < dt.timedelta(days=7): return None
    v, words = risk_line(now, st)
    row = {"id": _did("RISK", "risk_line", v, words[:40], now), "ts": iso(now), "rule": "RISK", "key": "risk_line", "old": "", "new": v, "why": words, "ticket": "",
           "numbers": json.dumps({"verdict": v}), "effect_before": "", "effect_after": "", "prediction": "", "state": "judged", "told": "", "frozen_until": "",
           "observed": "", "scored": "", "briefed": ""}
    st.append(TAB, [row]); return row

def _split_target(now):
    """RULE SPLIT: RAISE the month by one step (to 16) while the risk line is not 'worse' AND the raised plan still pays the motion the lever asks
    (MOTION FIRST); LOWER by one step (not under 8) only after STRATEGY_WINDOW_END on two 'worse' readings 28 days apart whose windows began after the
    last SPLIT decision was applied. The week follows the month; the cell that binds moves first."""
    from whatifs import governor as G
    rows = _rows(); m, w = int(float(_cell("SHORTS_PER_MONTH") or 12)), int(float(_cell("SHORTS_PER_WEEK") or 3))
    days = calendar.monthrange(now.year, now.month)[1]; L = G.max_long_videos(); risk = sorted([r for r in rows if r.get("rule") == "RISK"], key=lambda r: r["ts"])
    tgt, why = m, f"the month stays at {m} Shorts"
    last_risk = risk[-1]["new"] if risk else "unknown"
    mf = G.moving_floor(); f2 = G.month_fit(L, m + 2, now=now); motion = f2["long_left"] * S("BUDGET_SAFETY_MARGIN", float) * mf["inr_s"] * (mf["living_target_s"] - mf["living_s"])
    if m + 2 <= 16 and last_risk != "worse" and f2["fits"] and f2["free_inr"] >= motion:
        tgt, why = m + 2, (f"the money pays {m + 2} Shorts after the long videos' moving seconds in full (Rs {f2['free_inr']:.0f} free, Rs {motion:.0f} for motion first)"
                           + ("; at four a week the Shorts come on four days running, then three quiet days" if min(4, max(2, math.ceil((m + 2) / 4))) == 4 else ""))
    elif now.strftime("%Y-%m-%d") > str(S("STRATEGY_WINDOW_END") or "") and m - 2 >= 8:
        applied = [r for r in rows if r.get("rule") == "SPLIT" and r["state"] in ("applied", "verified")]
        since = max((parse_iso(r["ts"]) for r in applied), default=None)
        worse = [r for r in risk if r["new"] == "worse" and (since is None or parse_iso(r["ts"]) - dt.timedelta(days=S("RISK_WINDOW_DAYS", int)) >= since)]
        if len(worse) >= 2 and parse_iso(worse[-1]["ts"]) - parse_iso(worse[0]["ts"]) >= dt.timedelta(days=28):
            tgt, why = m - 2, f"two 'worse' readings 28 days apart: {worse[-1]['why']}"
    wt = min(4, max(2, math.ceil(tgt / 4)))
    wait = "SHORTS_PER_WEEK" if (w * days // 7 < tgt and wt != w) else ""      # the cell that binds moves first: the month WAITS for the week (V4's finish C12)
    nums = {"risk": last_risk, "free_inr": f2["free_inr"], "motion_inr": round(motion, 0)}
    return {"SHORTS_PER_MONTH": {"target": str(tgt), "why": why, "numbers": nums, "evidence": "ok", "count": "", "wait": wait},
            "SHORTS_PER_WEEK": {"target": str(wt), "why": why, "numbers": nums, "evidence": "ok", "count": ""}}

def _credit_target(now):
    """RULE CREDIT: lane closed -> 0; open -> 4 while UNTIL is CREDIT_TAPER_DAYS or more away, else 0 (the last week walks 4, 2, 0); a step UP only when
    its cost for the rest of the month fits as extra money AND the cover already realised is at least that cost."""
    from whatifs import governor as G
    from whatifs.org import finance as FIN
    cell = int(float(_cell("THINK_BOOST_VARIANTS") or 0)); c = FIN.lane(now)
    if not c: return {"THINK_BOOST_VARIANTS": {"target": "0", "why": "the Claude credit's lane is closed", "numbers": {}, "evidence": "ok", "count": ""}}
    left_days = (dt.date.fromisoformat(c["until"]) - now.date()).days
    if left_days < S("CREDIT_TAPER_DAYS", int): return {"THINK_BOOST_VARIANTS": {"target": "0", "why": f"the credit ends in {left_days} days: the boost steps down", "numbers": {"days": left_days}, "evidence": "ok", "count": ""}}
    fit = G.month_fit(G.max_long_videos(), S("SHORTS_PER_MONTH", int), now=now); cost = fit["short_left"] * 2 * S("SHORT_VARIANT_EST_INR", float)
    up = G.month_fit(G.max_long_videos(), S("SHORTS_PER_MONTH", int), extra_inr=cost, now=now)["fits"] and FIN.cover(now) >= cost
    t = 4 if up or cell >= 4 else cell
    return {"THINK_BOOST_VARIANTS": {"target": str(t), "why": (f"the credit paid Rs {FIN.cover(now):.0f} this month; two more scripts a Short cost Rs {cost:.0f} for the rest of it" if up
                                                            else f"a step up waits: the credit has paid Rs {FIN.cover(now):.0f} of the Rs {cost:.0f} it would cost"),
                                     "numbers": {"cost_inr": cost, "cover_inr": FIN.cover(now)}, "evidence": "ok", "count": ""}}

RULES = (
    {"id": "CREDIT", "keys": ("THINK_BOOST_VARIANTS",), "target": _credit_target, "metric": "shorts_engaged_first_days", "board": "shorts", "direction": "up", "horizon": 8},
    {"id": "SHORT_ARMS", "keys": ("SHORT_SHARE_S1", "SHORT_SHARE_S2", "SHORT_SHARE_S3"), "target": _short_arms_target, "metric": "shorts_engaged_first_days", "board": "shorts", "direction": "up", "horizon": 8},
    {"id": "SLOTS", "keys": ("STANDARD_MAX_LONG_PER_MONTH",), "target": _slots_target, "metric": "long_hours_per_video_28d", "board": "hours", "direction": "up", "horizon": 4},
    {"id": "SPLIT", "keys": ("SHORTS_PER_MONTH", "SHORTS_PER_WEEK"), "target": _split_target, "metric": "shorts_engaged_90d", "board": "shorts", "direction": "up", "horizon": 12},
    {"id": "ARMS", "keys": ("FORMAT_SHARE_F1", "FORMAT_SHARE_F2", "FORMAT_SHARE_F3"), "target": _arms_target, "metric": "long_hours_per_video_28d", "board": "hours", "direction": "up", "horizon": 8},
    {"id": "TRIAL", "keys": (), "target": lambda now: {}, "metric": "shorts_engaged_first_days", "board": "shorts", "direction": "up", "horizon": 8},      # the arm book (trial_move)
)
PORTFOLIO = tuple(k for r in RULES for k in r["keys"])
WORDS = {"STANDARD_MAX_LONG_PER_MONTH": "{new} long videos a month instead of {old}", "SHORTS_PER_MONTH": "{new} Shorts a month instead of {old}",
         "SHORTS_PER_WEEK": "{new} Shorts a week instead of {old}", "THINK_BOOST_VARIANTS": "{new} more scripts for every Short instead of {old}",
         **{f"SHORT_SHARE_S{i}": "Short format S%d: %s%% of the Shorts instead of %s%%" % (i, "{new}", "{old}") for i in (1, 2, 3)},
         **{f"FORMAT_SHARE_F{i}": "format F%d: %s%% of the long videos instead of %s%%" % (i, "{new}", "{old}") for i in (1, 2, 3)}}

def rule_of(key): return next((r for r in RULES if key in r["keys"]), None)

def plain(key, old, new):
    return WORDS.get(key, "{key} from {old} to {new}").format(key=key, old=old or "empty", new=new or "empty")

def targets(now=None):
    """{key: {target, why, numbers, evidence, count, rule}} of every rule, in the rules' order. A rule that cannot be read today is left out (logged)."""
    now = now or now_utc(); out = {}
    for r in RULES:
        try:
            for k, v in (r["target"](now) or {}).items(): out[k] = dict(v, rule=r["id"])
        except Exception as e: log(f"strategy: rule {r['id']} could not be read: {scrub(e)[:140]}", "WARN")
    return out

# ------------------------------------------------------------------ what the running code will do with a value (the readers' own arithmetic)
def _vector(sh, key, value, prefix):
    sh = dict(sh); f = key[len(prefix):]
    try: v = max(0, int(float(value)))
    except (TypeError, ValueError): v = 0
    if v: sh[f] = v
    else: sh.pop(f, None)
    tot = sum(sh.values()) or 1
    return {k: int(10 * s / tot + 0.5) for k, s in sorted(sh.items())}

def effect(key, value, now=None):
    """What the running code will do with `value` in cell `key`. A cell is AT its target when effect(cell) == effect(target)."""
    from whatifs import governor as G, formats as FMT
    now = now or now_utc()
    if key == "STANDARD_MAX_LONG_PER_MONTH":
        n = int(float(value)) if G.budget_mode() == "standard" else G.max_long_videos()
        return min(n, G.long_videos_this_month(now) + G.slots(now, left=True))       # after the month's last slot nothing can change
    if key in ("SHORTS_PER_MONTH", "SHORTS_PER_WEEK"):
        partner = "SHORTS_PER_WEEK" if key == "SHORTS_PER_MONTH" else "SHORTS_PER_MONTH"; t = targets(now)
        pv = _cell(partner)
        if partner in t and str(t[partner]["target"]) != pv: pv = t[partner]["target"]      # the partner at ITS target whenever it is off it - gate, effect_after and settle alike (V4's finish C12)
        m, w = (int(float(value)), int(float(pv))) if key == "SHORTS_PER_MONTH" else (int(float(pv)), int(float(value)))
        days = calendar.monthrange(now.year, now.month)[1]; L = G.max_long_videos()
        k = max([j for j in range(0, m + 1) if G.month_fit(L, j, now=now)["fits"]] or [0])
        return min(m, w * days // 7, k)
    if key.startswith("FORMAT_SHARE_"):
        if str(S("FORMAT_FORCE") or "").strip() or os.environ.get("WI_FORMAT") or not FMT.on(): return {k[len("FORMAT_SHARE_"):]: _cell(k) for k in sorted(DEFAULTS) if k.startswith("FORMAT_SHARE_")}
        return _vector(FMT.shares(), key, value, "FORMAT_SHARE_")
    if key.startswith("SHORT_SHARE_"):
        if str(S("SHORT_FORMAT_FORCE") or "").strip() or os.environ.get("WI_SHORT_FORMAT"): return {k[len("SHORT_SHARE_"):]: _cell(k) for k in sorted(DEFAULTS) if k.startswith("SHORT_SHARE_")}
        return _vector(FMT.short_shares(), key, value, "SHORT_SHARE_")
    if key == "THINK_BOOST_VARIANTS":
        from whatifs.org import finance as FIN
        try: v = int(float(value))
        except (TypeError, ValueError): v = 0
        return S("SHORTS_VARIANTS", int) + (v if (FIN.credit(now)["open"] and G.claude_allowed()) else 0)
    return str(value).strip().upper() if str(value).strip().upper() in ("TRUE", "FALSE") else str(value).strip()

def at_target(key, target, now=None): return effect(key, _cell(key), now) == effect(key, target, now)

def _plan_need(key, value, now):
    """month_fit for the plan with `value` in `key` (only the cells that move the month's money)."""
    from whatifs import governor as G
    L, sh = G.max_long_videos(), S("SHORTS_PER_MONTH", int)
    if key == "STANDARD_MAX_LONG_PER_MONTH": L = effect(key, value, now)
    elif key in ("SHORTS_PER_MONTH", "SHORTS_PER_WEEK"): sh = effect(key, value, now)
    else: return None
    return G.month_fit(L, sh, now=now)

# ------------------------------------------------------------------ the next move and its three gates
def _frozen(rows, key, now):
    return any(r["key"] == key and parse_iso(r.get("frozen_until")) and parse_iso(r["frozen_until"]) > now for r in rows)

def _retry_wait(rows, key, now):
    lim = now - dt.timedelta(days=S("STRATEGY_RETRY_DAYS", float))
    return any(r["key"] == key and r["state"] in ("refused", "rolled_back") and (parse_iso(r.get("ts")) or now) > lim for r in rows)

def _moves_this_week(rows, now):
    t = now - dt.timedelta(days=7)
    return sum(1 for r in rows if r.get("rule") not in ("HAND", "WATCH", "UNDO") and r["state"] not in ("hand", "watch", "judged")
               and parse_iso(r.get("ts")) and parse_iso(r["ts"]) > t)

def _step(key, old, target):
    from whatifs.org import levers as LV
    sp = LV.LEVERS.get(key) or {}
    if sp.get("kind") not in ("int", "float"): return str(target)
    try: a, b = float(old), float(target)
    except (TypeError, ValueError): return str(target)
    d = max(-sp["step"], min(sp["step"], b - a)); v = a + d
    return str(int(round(v))) if sp["kind"] == "int" else f"{v:g}"

def next_move(now=None, st=None):
    """(candidate or None, refusals). The first key of PORTFOLIO that is not frozen, has no decision in force, waits no retry and is not at its target,
    moved one step toward the target - through RANGE, EFFECT and FIT. A refused candidate is kept as "not taken: ..." and the NEXT key is tried."""
    from whatifs.org import levers as LV
    now = now or now_utc(); rows = _rows(st); t = targets(now); refused = []
    if _moves_this_week(rows, now) >= S("STRATEGY_MOVES_PER_WEEK", int):
        return None, [f"not taken: {S('STRATEGY_MOVES_PER_WEEK', int)} decisions in seven days already"]
    for key in PORTFOLIO:
        if key not in t or _frozen(rows, key, now) or _retry_wait(rows, key, now): continue
        if any(r["key"] == key and r["state"] in IN_FORCE for r in rows): continue
        tg = t[key]; old = _cell(key)
        if tg.get("wait") and tg["wait"] in t and not at_target(tg["wait"], t[tg["wait"]]["target"], now): continue      # memo 3.5: the binding cell moves first
        if at_target(key, tg["target"], now): continue
        new = _step(key, old, tg["target"]); dept = LV.owner_of(key)
        why = LV.check(dept, key, new)["why"]
        if why: refused.append(f"not taken: {key} {old} -> {new}: {why}"); continue                                         # RANGE
        e0, e1 = effect(key, old, now), effect(key, new, now)
        if e0 == e1: refused.append(f"not taken: {key} {old} -> {new} changes nothing the code does ({e0})"); continue      # EFFECT
        n0, n1 = _plan_need(key, old, now), _plan_need(key, new, now)
        if n0 is not None and n1["need_inr"] > n0["need_inr"] and not n1["fits"]:                                            # FIT
            refused.append(f"not taken: {key} {old} -> {new}: the month would need Rs {n1['need_inr']:.0f} and has Rs {n1['room_inr']:.0f} for production"); continue
        r = rule_of(key)
        return {"rule": r["id"], "key": key, "old": old, "new": new, "why": tg["why"], "numbers": tg.get("numbers") or {}, "effect_before": e0, "effect_after": e1,
                "metric": r["metric"], "board": r["board"], "direction": r["direction"], "horizon": r.get("horizon", 4)}, refused
    return None, refused

def counting(now=None):
    """Every `count` of a rule whose evidence is thin (e.g. "S1 5 of 8 Shorts")."""
    return [v["count"] for v in targets(now).values() if v.get("evidence") == "thin" and v.get("count")]

# ------------------------------------------------------------------ a decision is a ticket
def _did(rule, key, old, new, now): return "DEC-" + hashlib.sha1(f"{rule}|{key}|{old}|{new}|{now.astimezone(dt.timezone.utc):%Y-%m-%d}".encode("utf-8")).hexdigest()[:10]

def _ticket(key, value, old, did, dedupe, now, words=None, urgency=None):
    from whatifs.org import levers as LV
    m = {"type": "ticket", "from_dept": "D1", "to_depts": [LV.owner_of(key)], "subject": f"Strategy: {words or plain(key, old, value)}"[:200],
         "body": {"lever_class": "B", "target": key, "value": value, "acceptance_test": ("the next review finds: " + f"{key} = {value} does what the decision said")[:400],
                  "rollback": f"{key} back to {old}", "decision_ref": did},
         "dedupe_key": dedupe, "done_when": f"the engine verified {key} = {value} or took it back"}
    if urgency: m["urgency"] = urgency
    return m

def decide(c, now=None, st=None):
    """(1) the ticket memo, (2) the row (state decided, its ticket id named before the runner writes), (3) the memo for Out.memos. No message here."""
    from whatifs.org import memos as MEM
    st = st or store(); now = now or now_utc(); did = _did(c["rule"], c["key"], c["old"], c["new"], now)
    memo = _ticket(c["key"], c["new"], c["old"], did, f"strategy|{did}", now)
    memo["body"]["acceptance_test"] = f"the next review finds: {c['key']} = {c['new']} makes the running code do {json.dumps(c['effect_after'])} (it did {json.dumps(c['effect_before'])})"[:400]
    base = METRICS[c["metric"]](now)
    row = {"id": did, "ts": iso(now), "rule": c["rule"], "key": c["key"], "old": c["old"], "new": c["new"], "why": str(c["why"])[:500], "numbers": json.dumps(c["numbers"], sort_keys=True),
           "effect_before": json.dumps(c["effect_before"]), "effect_after": json.dumps(c["effect_after"]), "ticket": MEM.id_for(memo, st, now), "state": "decided",
           "prediction": json.dumps({"metric": c["metric"], "board": c["board"], "direction": c["direction"], "horizon_videos": c["horizon"], "baseline": base, "read_on": ""}),
           "told": "", "frozen_until": "", "observed": "", "scored": "", "briefed": ""}
    st.append(TAB, [row]); return row, memo

# ------------------------------------------------------------------ telling him (level-triggered)
def text_of(r):
    p = _js(r.get("prediction"), {}); up = "up" if p.get("direction") == "up" else "down"
    return (f"Strategy decided: {plain(r['key'], r['old'], r['new'])} ({r['key']} {r['old']} -> {r['new']}). Why: {r['why']}. It should move "
            f"{BOARD_WORDS.get(p.get('board'), p.get('board'))}: {METRIC_WORDS.get(p.get('metric'), p.get('metric'))} {up}. Nothing to do - tap Undo to take it back.")

def tell(now=None, st=None):
    """Every row "decided" with an empty `told` whose ticket is on tab Memos gets its action (no expiry: the Undo link never dies). A crashed run tells
    late, never falsely. Returns how many were told."""
    from whatifs import notify as NT
    from whatifs.org import memos as MEM
    if not on(): return 0
    st = st or store(); n = 0
    for r in _rows(st):
        if r["state"] != "decided" or r.get("told") or not MEM.get(r["ticket"], st): continue
        aid = NT.send("strategy", text_of(r), [("Undo", f"STRATEGY UNDO {r['id']}")], tier="week", default="it stays", dedupe_key=f"strategy|{r['id']}")
        MEM.note_owner_told(r["ticket"], aid, st, now); _save(st, r, told=str(aid)); n += 1
    return n

def _action(r, st):
    return next((a for a in st.rows("Owner_Actions") if a.get("id") == r.get("told")), None)

def brief(now=None, st=None):
    """The part "*Decisions*" of the daily brief: (a) every row not yet briefed (a hand row is said in the weekly line), (b) the weekly line when it is
    due, (c) on a day with no row ONE line: no change and what is counted, or the first refusal. "" with STRATEGY_ON FALSE."""
    from whatifs import notify as NT
    if not on(): return ""
    st = st or store(); now = now or now_utc(); lines = []
    for r in _rows(st):
        if r.get("briefed") or r["state"] == "hand" or (parse_iso(r.get("ts")) or now) > now: continue
        if r["state"] == "watch": lines.append(f"Risk: {r['why']}")
        elif r["state"] == "judged": lines.append(f"{r['rule']} judged {r['key']} at {r['new']}: {r['why']}")
        elif r["state"] in TAKEN_BACK:
            ex = _js(r.get("numbers"), {}).get("engine_note") or r["state"].replace("_", " ")
            lines.append(f"Taken back: {plain(r['key'], r['old'], r['new'])} ({r['key']} stays {r['old']}). Why: {ex}.")
        elif r["state"] == "undone": continue
        else:
            a = _action(r, st); lnk = NT.link(f"STRATEGY UNDO {r['id']}", a["id"]) if a else ""
            lines.append(text_of(r) + (f" Undo: {lnk}" if lnk else ""))
    from whatifs.org import desk as DESK
    lines += DESK.lines(now, st)                                                       # the owner's desk: his inputs answered (3.9)
    wk = weekly(now, st)
    if wk: lines.append(wk)
    if not lines:
        today = _js(S("STRATEGY_TODAY"), {})
        if today.get("refused"): lines.append(f"Not taken today: {today['refused'][0]}.")
        else: lines.append("Strategy today: no change." + (f" Counting: {', '.join(today.get('counting') or counting(now))}." if (today.get("counting") or counting(now)) else ""))
    return "*Decisions*\n" + "\n".join(f"- {l}" for l in lines)

def _weekly_due(now):
    at = parse_iso(S("STRATEGY_WEEKLY_AT")); return at is None or now - at >= dt.timedelta(days=7)

def weekly(now=None, st=None):
    """THE WEEKLY LINE (every 7 days): the plan, the money, the mix, the risk words, the credit, what Strategy did and what is his."""
    from whatifs import governor as G, formats as FMT
    from whatifs.org import finance as FIN
    st = st or store(); now = now or now_utc()
    if not _weekly_due(now): return ""
    L, sh = effect("STANDARD_MAX_LONG_PER_MONTH", _cell("STANDARD_MAX_LONG_PER_MONTH"), now), S("SHORTS_PER_MONTH", int)
    sp = G.split(now); mf = G.month_fit(L, sh, now=now)
    money = f"it fits, Rs {mf['free_inr']:.0f} free (it buys moving seconds)" if mf["fits"] else f"the money pays {sp['fit']} Shorts, not {sh}"
    fm = " / ".join(f"{k} {v}" for k, v in sorted(FMT.shares().items())); sm = " / ".join(f"{k} {v}" for k, v in sorted(FMT.short_shares().items()))
    out = [f"Strategy, week of {now:%d %b}: the plan is {L} long videos and {sh} Shorts this month - {money}. Formats {fm}; Short formats {sm}."]
    cnt = counting(now)
    if cnt: out.append("Counting: " + ", ".join(cnt) + ".")
    rw = risk_words(now)
    if rw: out.append(rw)
    c = FIN.lane(now)
    if c: out.append(f"Claude credit: Rs {c['spent_inr']:.0f} used of Rs {c['amount_inr']:.0f}, Rs {c['left_inr']:.0f} left until {c['until']}; what is left on that day lapses.")
    out.append("Spin-offs: switched off; they come back only rebuilt.")
    cw = candidate_words(st)
    if cw: out.append(cw)
    rows = _rows(st); wk = [r for r in rows if r.get("rule") not in ("HAND", "WATCH", "RISK") and r["state"] not in ("hand", "watch", "judged") and (parse_iso(r.get("ts")) or now) > now - dt.timedelta(days=7)]
    if wk:
        v = sum(1 for r in wk if r.get("observed")); x = sum(1 for r in wk if r["state"] in TAKEN_BACK + ("undone",)); w = len(wk) - v - x
        out.append(f"{len(wk)} decision(s) this week: {v} took effect, {w} not seen yet, {x} taken back.")
    else: out.append("No change this week: every setting is at its target.")
    hand = [r for r in rows if r["state"] == "hand" and (parse_iso(r.get("ts")) or now) > now - dt.timedelta(days=7)]
    if hand: out.append("Outside Strategy: " + ", ".join(f"{r['key']} = {r['new']}" for r in hand) + f" - counted as your own values and left alone for {S('STRATEGY_UNDO_FREEZE_DAYS', int)} days.")
    return " ".join(out)

def risk_words(now=None):
    """The risk words of the weekly line: the newest risk line (3.5), then the watch book's (memo 3.6, once it exists)."""
    rs = sorted([r for r in _rows() if r.get("rule") == "RISK"], key=lambda r: r["ts"]); out = f"Risk line: {rs[-1]['why']}." if rs else ""
    from whatifs.org import risk as RISK
    w = RISK.words(now); return (out + " " + w).strip() if w else out

def briefed(now=None, st=None):
    """Stamp `briefed` on every row the brief that just WENT carried (rows not later than the brief's own `now`), and the weekly line's clock."""
    if not on(): return 0
    st = st or store(); now = now or now_utc(); n = 0
    for r in _rows(st):
        if r.get("briefed") or r["state"] == "hand" or (parse_iso(r.get("ts")) or now) > now: continue
        _save(st, r, briefed=iso(now)); n += 1
    if _weekly_due(now): set_setting("STRATEGY_WEEKLY_AT", iso(now))
    from whatifs.org import desk as DESK
    return n + DESK.briefed(now, st)

# ------------------------------------------------------------------ settling what the engine did
def _ticket_in_flight(key, st):
    from whatifs.org import memos as MEM
    return any(str((m.get("body") or {}).get("target")) == key for m in MEM.find(st, type="ticket"))

def _back(st, r, state, note, now):
    nums = dict(_js(r.get("numbers"), {}), engine_note=str(note)[:300])
    _save(st, r, state=state, numbers=nums, briefed=""); _follow(r, st, state, note)
    tries = [x for x in _rows(st) if x["key"] == r["key"] and x["state"] in ("refused", "rolled_back")]
    if state in ("refused", "rolled_back") and len(tries) >= 2:
        from whatifs.org import memos as MEM
        try:
            MEM.write({"type": "problem_memo", "from_dept": "D1", "to_depts": ["D12"], "subject": f"Strategy cannot move {r['key']}: two tries were taken back",
                       "body": {"what_failed": f"{r['key']}: {len(tries)} moves refused or rolled back by the engine ({str(note)[:200]})", "where": f"Decisions:{r['id']}", "attempt": 1,
                                "error_class": "strategy_stuck"},
                       "evidence": [{"source": f"Decisions:{r['id']}", "date": iso(now)[:10], "type": "own data"}], "dedupe_key": f"strategy_stuck|{r['key']}",
                       "done_when": f"a move of {r['key']} is verified"}, st, now)
        except Exception as e: log(f"strategy: the stuck memo was not written: {scrub(e)[:120]}", "WARN")
        _save(st, r, frozen_until=iso(now + dt.timedelta(days=S("STRATEGY_UNDO_FREEZE_DAYS", float))))

def settle(now=None, st=None):
    """Every row decided or applied takes the engine's word; an applied change whose effect differs from the decision's is taken back by a new ticket;
    a decision whose ticket never reached tab Memos is sent once more, then void; the undo stack sends its next ticket (written here: an undo is his).
    Returns the tickets for the review's Out.memos (a re-sent decision, a take-back of a change without effect)."""
    from whatifs.org import execute as EX, memos as MEM
    st = st or store(); now = now or now_utc(); out = []
    for r in _rows(st):
        if r["state"] not in IN_FORCE: continue
        es = EX.state_of(r["ticket"], st)
        if es is None:
            age = now - (parse_iso(r.get("ts")) or now)
            if r["state"] == "decided" and age > dt.timedelta(hours=DECIDED_MAX_H) and not MEM.get(r["ticket"], st):
                nums = _js(r.get("numbers"), {})
                if not nums.get("resent"):
                    out.append(_ticket(r["key"], r["new"], r["old"], r["id"], f"strategy|{r['id']}", now)); _save(st, r, numbers=dict(nums, resent=iso(now)))
                else: _back(st, r, "void", "its ticket was never written: nothing changed", now)
            continue
        state, note = es
        if state == "verified":
            _save(st, r, state="verified", numbers=dict(_js(r.get("numbers"), {}), engine_note=note[:300])); _follow(r, st, "verified")
            for m in MEM.find(st, type="problem_memo", from_dept="D1"):
                if m.get("dedupe_key") == f"strategy_stuck|{r['key']}":
                    try: MEM.resolve(m["id"], "D1", "repair_verified", f"Decisions:{r['id']}", "a move on that key was verified", st, now)
                    except Exception as e: log(f"strategy: the stuck memo was not closed: {scrub(e)[:120]}", "WARN")
        elif state in ("refused", "failed", "rolled_back"): _back(st, r, "rolled_back" if state == "rolled_back" else "refused", note, now)
        elif state == "applied":
            if r["state"] != "applied": _save(st, r, state="applied")
            if r.get("rule") != "TRIAL" and json.dumps(effect(r["key"], _cell(r["key"]), now)) != str(r.get("effect_after") or ""):      # a rulebook trial is no cell: the rulebook judges it
                _back(st, r, "no_effect", f"the running code would not do what was decided ({r['key']} = {_cell(r['key'])})", now)
                out.append(_ticket(r["key"], r["old"], r["new"], r["id"], f"strategy|noeffect|{r['id']}", now))
    for key in {r["key"] for r in _rows(st) if r["state"] == "undone"}:                          # the undo stack: one ticket at a time, newest first
        for r in sorted([x for x in _rows(st) if x["key"] == key and x["state"] == "undone"], key=lambda x: x["ts"], reverse=True):
            nums = _js(r.get("numbers"), {})
            if nums.get("undo_done"): continue
            if _cell(key) == str(r["old"]): _save(st, r, numbers=dict(nums, undo_done=iso(now))); continue
            if _ticket_in_flight(key, st): break
            m = _ticket(key, r["old"], r["new"], r["id"], f"strategy|undo|{r['id']}|{nums.get('undo_sent', 0)}", now)
            try: MEM.write(m, st, now); _save(st, r, numbers=dict(nums, undo_sent=int(nums.get("undo_sent", 0)) + 1))
            except Exception as e: log(f"strategy: an undo ticket was not written: {scrub(e)[:120]}", "WARN")
            break
    return out

def hands(now=None, st=None):
    """A portfolio cell that is neither its default, nor the `new` of the newest row in force for that key, nor the value of a hand row: his own value -
    recorded once as a row 'hand', frozen STRATEGY_UNDO_FREEZE_DAYS."""
    st = st or store(); now = now or now_utc(); rows = _rows(st); out = []
    for key in PORTFOLIO:
        v = _cell(key)
        if v == str(DEFAULTS.get(key, ("",))[0]).strip(): continue
        live = [r for r in rows if r["key"] == key and r["rule"] != "HAND" and (r["state"] in IN_FORCE + ("verified", "no_effect")
                or (r["state"] == "undone" and not _js(r.get("numbers"), {}).get("undo_done")))]            # a change of ours still on its way in or out is no hand
        nw = sorted(live, key=lambda r: r["ts"])[-1] if live else None
        if nw and (str(nw["new"]) == v or (nw["state"] == "no_effect" and str(nw["old"]) == v)): continue      # V4's finish C7: a take-back of ours is no hand
        if any(r["key"] == key and r["state"] == "hand" and str(r["new"]) == v for r in rows): continue
        out.append(hand(key, v, now, st))
    return out

def hand(key, value, now=None, st=None):
    """His own value of a portfolio key (a cell set by hand, or the dashboard's tap): one row 'hand', the key frozen for STRATEGY_UNDO_FREEZE_DAYS."""
    st = st or store(); now = now or now_utc()
    prev = [r for r in _rows(st) if r["key"] == key]; old = str(prev[-1]["new"]) if prev else str(DEFAULTS.get(key, ("",))[0])
    row = {"id": _did("HAND", key, old, value, now), "ts": iso(now), "rule": "HAND", "key": key, "old": old, "new": str(value), "why": "your own value",
           "numbers": "{}", "effect_before": "", "effect_after": "", "prediction": "", "ticket": "", "state": "hand", "told": "",
           "frozen_until": iso(now + dt.timedelta(days=S("STRATEGY_UNDO_FREEZE_DAYS", float))), "observed": "", "scored": "", "briefed": ""}
    if any(r["id"] == row["id"] for r in prev): return row
    st.append(TAB, [row]); return row

# ------------------------------------------------------------------ D1's run `review`
def _disposition(m):
    t = m.get("type")
    if t == "owner_memo": return ("deferred", "answered on the owner's desk: it closes with its answer")
    if t in ("performance_memo", "decision_memo"): return ("deferred", "read by Strategy: counted in this review's numbers")
    if t == "problem_memo": return ("deferred", f"read by Strategy: {(m.get('body') or {}).get('error_class') or 'the problem'} is repaired by its own department; counted in the week's line")
    return ("deferred", f"read by Strategy: a {t} is not Strategy's to close")

def review(brief):
    """D1's run `review` (cli.strategy_round, in the daily learning job): settle, hands, the watch book and the intake (later steps), then at most ONE
    decision; every inbound memo dispositioned. Returns an Out: the decision's ticket goes out through the runner."""
    from whatifs.org.runner import Out
    brief.take()                                                                   # the runner's contract: a department run takes its playbook (D1 decides by rule)
    st = store(); now = now_utc()
    resend = settle(now, st)
    hs = hands(now, st)
    judge(now, st); observe(now, st)
    risks, risk_memos = book(now, st)
    cands = intake(now, st)
    c, refused = next_move(now, st); memos = list(resend) + list(risk_memos); decided = 0
    if c: _row, memo = decide(c, now, st); memos.append(memo); decided = 1
    elif _moves_this_week(_rows(st), now) < S("STRATEGY_MOVES_PER_WEEK", int):
        tc = trial_move(now, st)
        if tc:
            _row, memo = decide_trial(tc, now, st)
            if memo: memos.append(memo); decided = 1
    cnt = counting(now)
    set_setting("STRATEGY_TODAY", json.dumps({"at": iso(now), "refused": refused[:3], "counting": cnt}))
    acts = {m["id"]: _disposition(m) for m in getattr(brief, "memos", None) or []}
    return Out(output={"decided": c, "refused": refused, "hands": len(hs)}, memos=memos, memo_actions=acts,
               measures={"decisions": decided, "refused": len(refused), "counting": len(cnt), "risks": risks, "candidates": len(cands), "hands": len(hs)})

def book(now=None, st=None):
    """The watch book's pass (memo 3.6): (rows written, memos for Out.memos)."""
    from whatifs.org import risk as RISK
    return RISK.run(now, st)

# ------------------------------------------------------------------ THE ARM BOOK (tab Candidates; rule TRIAL)
CAND = "Candidates"
TRIAL_ROLES = {"showrunner": "D4", "writer": "D4", "packager": "D4", "director": "D4"}         # a rulebook role names no department: the creative lead executes it

def file(c, now=None, st=None):
    """The ONE writer of tab Candidates. Refused without a dated source or without the policy read first; parked when nothing can execute it; a hand
    candidate waits for his desk. The same id twice is a no-op. Returns the row."""
    from whatifs.org import levers as LV
    st = st or store(); now = now or now_utc(); kind = str(c.get("kind") or "").strip(); title = str(c.get("title") or "").strip()[:120]
    cid = "CAN-" + hashlib.sha1(f"{kind}|{title}".encode("utf-8")).hexdigest()[:10]
    old = next((r for r in st.rows(CAND) if r.get("id") == cid), None)
    if old: return old
    src = [x for x in (c.get("sources") or []) if isinstance(x, dict) and str(x.get("url") or "").strip() and str(x.get("date") or "").strip()]
    how = c.get("how") if isinstance(c.get("how"), dict) else {}
    if kind not in ("machine", "hand", "subject", "name"): state = "refused: unknown kind"
    elif not src: state = "refused: no dated source"
    elif str(c.get("policy") or "") != "ok": state = "refused: no policy reading"
    elif kind == "hand": state = "for his desk (B9)"
    elif kind != "machine" or how.get("lever_class") not in ("B", "C") or not how.get("target"): state = "parked: nothing in the pipeline can execute it yet"
    elif how["lever_class"] == "C" and (isinstance(how.get("value"), dict) and how["value"].get("for") == "short"): state = "parked: a rulebook trial is judged on long videos only"
    elif how["lever_class"] == "C" and str(how["target"]).split(":", 1)[-1] not in TRIAL_ROLES: state = f"parked: {how['target']} is no rulebook role"
    elif how["lever_class"] == "B" and not LV.owner_of(str(how["target"])): state = f"parked: {how['target']} is not a lever"
    else: state = "filed"
    row = {"id": cid, "ts": iso(now), "kind": kind, "title": title, "how": json.dumps(how, sort_keys=True)[:2000], "sources": json.dumps(src)[:1000],
           "policy": str(c.get("policy") or ""), "filed_by": str(c.get("filed_by") or "")[:40], "state": state, "ticket": "", "note": ""}
    st.append(CAND, [row]); return row

def _filed(now=None):
    """The candidates to file today: the Observatory (V5) will call `file`; until it exists the stand-in list in fake mode when ARM_STAND_IN_ON."""
    from whatifs.core import FAKE
    if FAKE and S("ARM_STAND_IN_ON", bool):
        from whatifs import fakes as FK
        return FK.features()
    return []

def intake(now=None, st=None):
    st = st or store(); return [file(c, now, st) for c in _filed(now)]

def trial_move(now=None, st=None):
    """RULE TRIAL - ONE TRIAL AT A TIME: with no candidate in trial and none opened in the last TRIAL_GAP_DAYS, the oldest filed machine candidate."""
    st = st or store(); now = now or now_utc(); cs = st.rows(CAND)
    if any(r.get("state") == "trial" for r in cs): return None
    lim = now - dt.timedelta(days=S("TRIAL_GAP_DAYS", float))
    if any(r.get("rule") == "TRIAL" and (parse_iso(r.get("ts")) or now) > lim for r in _rows(st)): return None
    return next((r for r in sorted(cs, key=lambda r: str(r.get("ts") or "")) if r.get("state") == "filed" and r.get("kind") == "machine"), None)

def decide_trial(cand, now=None, st=None):
    """The candidate becomes a decision: class C - a ticket from D1 to D4 (the rulebook's role names no department); class B - its lever, through the
    three gates. Returns (row, memo) or (None, None) with the candidate parked or refused in words."""
    from whatifs.org import levers as LV, memos as MEM
    st = st or store(); now = now or now_utc(); how = _js(cand.get("how"), {}); metric = how.get("metric") if how.get("metric") in METRICS else "shorts_engaged_first_days"
    did = _did("TRIAL", cand["id"], "", str(how.get("target")), now)
    if how.get("lever_class") == "B":
        key, old, new = str(how["target"]), _cell(str(how["target"])), str(how.get("value"))
        why = LV.check(LV.owner_of(key), key, new)["why"]
        if not why and effect(key, old, now) == effect(key, new, now): why = f"{key} {old} -> {new} changes nothing the code does"
        n0, n1 = _plan_need(key, old, now), _plan_need(key, new, now)
        if not why and n0 is not None and n1["need_inr"] > n0["need_inr"] and not n1["fits"]: why = f"the month would need Rs {n1['need_inr']:.0f} and has Rs {n1['room_inr']:.0f}"
        if why: st.update(CAND, "id", cand["id"], {"state": f"not taken: {why}"[:200]}); return None, None
        memo = _ticket(key, new, old, did, f"strategy|{did}", now, words=f"trial of a candidate: {cand['title']}")
    else:
        key, old, new = str(how["target"]), "", str((how.get("value") or {}).get("rule") or "")[:240]
        memo = {"type": "ticket", "from_dept": "D1", "to_depts": [TRIAL_ROLES[key.split(":", 1)[1]]], "subject": f"Strategy: try a candidate in the rulebook: {cand['title']}"[:200],
                "body": {"lever_class": "C", "target": key, "value": how.get("value"), "acceptance_test": f"the rulebook trial runs on the next long videos and is judged on its own metric ({(how.get('value') or {}).get('metric')})"[:400],
                         "rollback": "retire the rule from the rulebook", "decision_ref": did},
                "dedupe_key": f"strategy|{did}", "done_when": "the engine verified the trial or retired it"}
    row = {"id": did, "ts": iso(now), "rule": "TRIAL", "key": key, "old": old, "new": new, "why": f"a candidate from the arm book: {cand['title']}", "numbers": json.dumps({"candidate": cand["id"]}),
           "effect_before": json.dumps(old), "effect_after": json.dumps(new), "ticket": MEM.id_for(memo, st, now), "state": "decided", "told": "", "frozen_until": "",
           "prediction": json.dumps({"metric": metric, "board": "shorts" if metric.startswith("shorts") else "hours", "direction": "up", "horizon_videos": 8, "baseline": METRICS[metric](now), "read_on": ""}),
           "observed": "", "scored": "", "briefed": ""}
    st.append(TAB, [row]); st.update(CAND, "id", cand["id"], {"state": "trial", "ticket": row["ticket"]}); return row, memo

def _follow(r, st, state, note=""):
    """A TRIAL row's candidate follows its ticket: dropped (refused, failed, rolled back) or running since its date (verified)."""
    if r.get("rule") != "TRIAL": return
    cid = _js(r.get("numbers"), {}).get("candidate")
    if not cid: return
    st.update(CAND, "id", cid, {"state": (f"running since {iso()[:10]}" if state == "verified" else f"dropped: {note}")[:200]})

def candidate_words(st=None):
    cs = (st or store()).rows(CAND); parked = sum(1 for r in cs if str(r.get("state") or "").startswith("parked")); desk = sum(1 for r in cs if r.get("state") == "for his desk (B9)")
    return f"{parked} candidate(s) parked, {desk} for your desk." if (parked or desk) else ""

# ------------------------------------------------------------------ what production DID (a later review fills `observed`; never the gate's arithmetic)
def observe(now=None, st=None):
    """SLOTS: the long videos with a slot in the decision's month (once that month is over); SPLIT: the Shorts made in it; a share: the formats of the next
    ten made after the decision; CREDIT: `asked` of the next Short's write run. The weekly line counts "took effect" from this column."""
    from whatifs import shorts2 as SH
    st = st or store(); now = now or now_utc(); n = 0
    eps = st.rows("Episodes"); sps = st.rows("Specials")
    for r in _rows(st):
        if r.get("observed") or r["state"] not in ("applied", "verified") or r.get("rule") in ("HAND", "RISK"): continue
        t = parse_iso(r.get("ts")) or now; mk = t.strftime("%Y-%m"); over = (now.year, now.month) != (t.year, t.month); obs = None
        if r["rule"] == "SLOTS" and over:
            obs = {"long_videos": sum(1 for e in eps if str(e.get("slot_et") or "").startswith(mk) and str(e.get("status") or "").upper() not in ("KILLED", "FAILED", "SKIPPED"))}
        elif r["rule"] == "SPLIT" and over:
            obs = {"shorts_made": SH.made_this_month(t)}
        elif r["key"].startswith("FORMAT_SHARE_"):
            after = [_js(e.get("draw_json"), {}).get("format") for e in sorted(eps, key=lambda e: str(e.get("created") or e.get("slot_et") or "")) if str(e.get("slot_et") or "") > r["ts"]]
            after = [f for f in after if f][:10]
            if len(after) == 10: obs = {f: after.count(f) for f in sorted(set(after))}
        elif r["key"].startswith("SHORT_SHARE_"):
            after = [x.get("format") for x in sorted(sps, key=lambda x: str(x.get("ts") or "")) if str(x.get("ts") or "") > r["ts"] and x.get("format")][:10]
            if len(after) == 10: obs = {f: after.count(f) for f in sorted(set(after))}
        elif r["rule"] == "CREDIT":
            ss = sorted((x for x in st.rows("Takeaways") if x.get("dept") == "D14" and x.get("trigger") == "write" and str(x.get("ts") or "") > r["ts"]
                         and "asked" in _js(x.get("measures"), {})), key=lambda x: str(x.get("ts") or ""))
            if ss: obs = {"asked": _js(ss[0].get("measures"), {}).get("asked")}                    # V4's finish C4 (P9): the write run's own measures (tab Takeaways), never the stored lines
        if obs is not None: _save(st, r, observed=obs); n += 1
    return n

# ------------------------------------------------------------------ UNDO (the whole stack)
def undo(did, now=None, st=None):
    """His tap on a decision's Undo: every later decision still in force on that key, newest first, then itself - all undone at once, frozen 28 days; the
    first ticket goes now, the rest one at a time (settle). The answer is built from what the engine returned."""
    from whatifs.org import execute as EX, memos as MEM, schemas as SC
    st = st or store(); now = now or now_utc(); rows = _rows(st); me = next((r for r in rows if r["id"] == did), None)
    if me is None: return f"no decision {did}"
    if me["state"] == "undone": return f"{did} was already taken back"
    stack = sorted([r for r in rows if r["key"] == me["key"] and r["state"] in IN_FORCE + ("verified",) and r["ts"] >= me["ts"] and r["rule"] != "HAND"], key=lambda r: r["ts"], reverse=True)
    if me not in stack: stack.append(me)
    fz = iso(now + dt.timedelta(days=S("STRATEGY_UNDO_FREEZE_DAYS", float))); answers = []
    first = stack[0]; es = EX.state_of(first["ticket"], st) if first.get("ticket") else None
    for r in stack: _save(st, r, state="undone", frozen_until=fz, briefed=r.get("briefed") or iso(now))
    try:
        if es is None or es[0] in EX.WAITING:
            t0 = MEM.get(first["ticket"], st) if first.get("ticket") else None
            if t0 is not None and t0["status"] in SC.LIVE: MEM.reject(first["ticket"], "owner", "undone by the owner from the strategy message", st, now)
            ans = "undone: it had not been changed yet"; _save(st, first, numbers=dict(_js(first.get("numbers"), {}), undo_done=iso(now)))
        elif es[0] in EX.FLYING:
            MEM.reject(first["ticket"], "owner", "undone by the owner from the strategy message", st, now); EX.reconcile(st, now)
            ans = f"undone: {first['key']} is back at {first['old']}" if _cell(first["key"]) == str(first["old"]) else f"undone: {first['key']} goes back to {first['old']} between videos"
        else:
            m = _ticket(first["key"], first["old"], first["new"], first["id"], f"strategy|undo|{first['id']}|0", now, urgency="P1")
            t = MEM.write(m, st, now); _save(st, first, numbers=dict(_js(first.get("numbers"), {}), undo_sent=1)); EX.engine_tick(st, now)
            e2 = EX.state_of(t["id"], st)
            if e2 and e2[0] in ("refused", "failed"): ans = f"the engine refused: {e2[1]}"
            elif _cell(first["key"]) == str(first["old"]): ans = f"undone: {first['key']} is back at {first['old']}"
            else: ans = f"undone: {first['key']} goes back to {first['old']} between videos"
    except Exception as e:
        log(f"strategy: undo of {did} did not finish: {scrub(e)[:160]}", "WARN"); ans = f"undone: {first['key']} goes back to {first['old']} between videos"
    answers.append(ans)
    later = [r["id"] for r in stack if r["id"] != did]
    if later: answers.append("taken back with it: " + ", ".join(later))
    return "; ".join(answers)

def _answer(row, choice):
    parts = str(choice or "").split()
    if len(parts) >= 3 and parts[0].upper() == "STRATEGY" and parts[1].upper() == "UNDO": return undo(parts[2])
    return "recorded"

def register():
    from whatifs import notify as NT
    NT.register("strategy", on_answer=_answer)

# ------------------------------------------------------------------ check strategy_live (the script gate)
def live_issues(st=None, now=None):
    """(problems, stats, na) for check strategy_live."""
    from whatifs.org import runner as ORG, memos as MEM
    if not on(): return [], {}, "Strategy is switched off (STRATEGY_ON)"
    if not ORG.on(): return [], {}, "organisation switched off"
    st = st or store(); now = now or now_utc(); since = parse_iso(S("ORG_SINCE")); lim = dt.timedelta(hours=S("STRATEGY_STALE_H", float))
    if not since or now - since < lim:
        return [], {}, f"Strategy has not reviewed yet: the organisation started {round((now - since).total_seconds() / 3600) if since else 0} h ago"
    p = []; last = max((t for t in (parse_iso(r.get("started")) for r in st.rows("Sessions") if r.get("dept") == "D1" and r.get("trigger") == "review" and r.get("status") == "ok") if t), default=None)
    if last is None or now - last > lim: p.append(f"Strategy's review is {'missing' if last is None else f'{round((now - last).total_seconds() / 3600)} h old'} (limit {S('STRATEGY_STALE_H', int)} h)")
    rows = _rows(st)
    for r in rows:
        if r["state"] == "decided" and now - (parse_iso(r.get("ts")) or now) > dt.timedelta(hours=DECIDED_MAX_H) and not MEM.get(r["ticket"], st):
            p.append(f"decision {r['id']} ({r['key']} {r['old']} -> {r['new']}) has stood {DECIDED_MAX_H}+ h with no ticket: only text")
    stats = {"h": round((now - last).total_seconds() / 3600) if last else None, "n": sum(1 for r in rows if r.get("ticket")),
             **{k: sum(1 for r in rows if r["state"] == k) for k in ("verified", "rolled_back", "undone", "void")}}
    return p, stats, ""
