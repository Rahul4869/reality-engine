"""v10.3 (K153): the OWNER VIEW - one data layer for WhatsApp, the dashboard, the digests and the chat brain, so they never disagree.

Evidence rules (pack rule, owner 9 Nov 2026):
  - every number carries `src` (the Sheet tab / API it came from) and `date`; nothing is invented; missing data says WHEN it will appear;
  - interpretations are labelled `kind: "interpretation"` and built from the observed numbers next to them;
  - demo mode (`demo=True`) returns a clearly marked DEMO data set so the owner can see finished designs before real data exists.
All sections are rule-based (Rs 0). Sections: today, numbers, hot_topics, recommendations, observations, strategy, experiments, money."""
from __future__ import annotations
import datetime as dt, json, statistics
from whatifs.core import S, store, iso, now_utc, parse_iso

DEMO_NOTE = "DEMO DATA - a preview of the design, not your channel's numbers"

def _f(v, d=None):
    try: return float(v)
    except (TypeError, ValueError): return d

def _date(v):
    t = parse_iso(v) if isinstance(v, str) else v
    return t.strftime("%d %b") if t else ""

def _rows(tab):
    try: return store().rows(tab)
    except Exception: return []

# ------------------------------------------------------------------ sections
def today(now=None):
    from whatifs import manage as MG
    now = now or now_utc()
    eps = _rows("Episodes")
    nxt = None
    try: nxt = (MG.next_slots(1, now) or [None])[0]
    except Exception: pass
    making = [e for e in eps if str(e.get("status", "")).upper() in ("PLANNING", "VOICING", "VISUALS", "UPLOADED", "SCHEDULED", "AWAITING_APPROVAL", "HOLD_QC", "HELD")]
    out = {"now": iso(now), "paused": MG.paused() if hasattr(MG, "paused") else False}
    if nxt:
        hrs = max(0.0, (nxt - now).total_seconds() / 3600)
        out["next_slot"] = {"utc": iso(nxt), "ist": (nxt + dt.timedelta(hours=5, minutes=30)).strftime("%a %d %b %H:%M IST"), "in_hours": round(hrs, 1)}
    out["in_progress"] = [{"episode": e.get("episode_id"), "title": e.get("title") or e.get("premise", "")[:60], "status": e.get("status"),
                           "slot": e.get("slot_et"), "src": "Episodes"} for e in making[-3:]]
    out["released_today"] = [{"episode": e.get("episode_id"), "title": e.get("title"), "yt": e.get("yt_id"), "src": "Episodes"}
                             for e in eps if e.get("yt_id") and _date(e.get("slot_et")) == _date(iso(now))]
    return out

def numbers(limit=8):
    """Per-video numbers from the Analytics tab (YouTube Analytics API; 48-72 h delay)."""
    rows = [r for r in _rows("Analytics") if r.get("yt_id")]
    by = {}
    for r in rows: by[r.get("yt_id")] = r                       # newest pull per video
    eps = {e.get("yt_id"): e for e in _rows("Episodes") if e.get("yt_id")}
    vids = []
    for yid, r in list(by.items())[-limit:]:
        e = eps.get(yid, {})
        vids.append({"title": (e.get("title") or r.get("episode_id") or yid)[:60], "yt_id": yid, "views": _f(r.get("views"), 0),
                     "avg_view_pct": _f(r.get("avg_view_pct")), "ret30": _f(r.get("ret30")), "ctr": _f(r.get("ctr")), "subs": _f(r.get("subs"), 0),
                     "shorts_views": _f(r.get("shorts_views"), 0), "pulled": r.get("pulled"), "src": "YouTube Analytics (Analytics tab)"})
    specials = [{"title": s.get("title"), "kind": s.get("kind"), "views_7d": _f(s.get("views_7d")), "yt_id": s.get("yt_id"), "src": "Specials"}
                for s in _rows("Specials") if s.get("yt_id")][-4:]
    pilots = [{"premise": p.get("premise", "")[:60], "views": _f(p.get("views")), "yt_id": p.get("yt_id"), "src": "Pilots"} for p in _rows("Pilots") if p.get("yt_id")][-4:]
    out = {"videos": vids, "specials": specials, "pilots": pilots}
    if not vids:
        out["empty"] = "No video numbers yet: YouTube Analytics shows a video's numbers 48-72 hours after it goes public."
    else:
        tot = sum(v["views"] for v in vids); subs = sum(v["subs"] for v in vids)
        avp = [v["avg_view_pct"] for v in vids if v["avg_view_pct"] is not None]
        out["totals"] = {"views": tot, "subs": subs, "avg_view_pct": round(statistics.mean(avp), 1) if avp else None, "src": "Analytics tab", "date": vids[-1].get("pulled")}
    return out

def hot_topics(n=5):
    """Cited signals from the weekly research (Trend_Brief: YouTube search/charts, Google Trends, Stack Exchange...) and outlier videos."""
    tb = [r for r in _rows("Trend_Brief") if r.get("item")]
    latest = max((r.get("week") for r in tb), default="")
    items = [{"topic": r.get("item")[:80], "why": str(r.get("detail") or "")[:160], "kind": r.get("kind"), "src": r.get("source") or "Trend_Brief",
              "date": latest} for r in tb if r.get("week") == latest][:n]
    outl = sorted(_rows("Demand_Signals"), key=lambda r: -(_f(r.get("multiple"), 0) or 0))[:3]
    watch = [{"title": str(r.get("title"))[:70], "url": f"https://youtu.be/{r.get('video_id')}", "multiple": _f(r.get("multiple")), "channel": r.get("channel"),
              "src": "YouTube Data API (Demand_Signals)", "date": _date(r.get("ts"))} for r in outl if r.get("video_id")]
    out = {"topics": items, "outliers": watch}
    if not items and not watch:
        out["empty"] = "No hot topics yet: the research job writes them every week (Trend_Brief), the outlier scan daily."
    return out

def recommendations(n=3):
    bench = [b for b in _rows("Premise_Bench") if str(b.get("status")) == "READY"]
    bench.sort(key=lambda b: -(_f(b.get("combined"), 0) or 0))
    nxt = []
    for b in bench[:n]:
        try: dj = json.loads(b.get("demand_json") or "{}")
        except Exception: dj = {}
        nxt.append({"premise": b.get("headline") or b.get("premise", "")[:80], "score": _f(b.get("combined")), "search_demand": dj.get("search_score"),
                    "src": "Premise_Bench (writers' + Gemini scores" + (", YouTube search demand" if "search_score" in dj else "") + ")"})
    shorts = [{"idea": f"Pilot test: {p.get('hook') or p.get('premise', '')[:60]}", "result_views": _f(p.get("views")), "src": "Pilots"} for p in _rows("Pilots")[-3:]]
    techniques = [{"technique": r.get("title")[:80], "status": r.get("status"), "src": "Outlier_Lab"} for r in _rows("Outlier_Lab")[-3:] if r.get("title")]
    out = {"next_cases": nxt, "shorts": shorts, "watch_for_craft": techniques}
    if not nxt: out["empty"] = "The idea bench is filling: the scout adds scored premises before each slot."
    return out

def observations(n=6):
    obs = []
    for r in _rows("Data_Rules")[-3:]:
        obs.append({"text": r.get("text"), "kind": "observed", "src": f"Retention Microscope ({r.get('videos')} videos)", "date": _date(r.get("ts"))})
    for r in _rows("Slop_Scores")[-2:]:
        s = _f(r.get("slop"), 0)
        if s >= S("SLOP_WARN", float): obs.append({"text": f"{r.get('episode_id')}: originality score {s:.0f}/100 is above the warning line.", "kind": "observed", "src": "Slop Guard", "date": _date(r.get("ts"))})
    for r in _rows("Model_Changes")[-2:]:
        obs.append({"text": f"Model change ({r.get('role')}): {r.get('from')} -> {r.get('to')}: {r.get('why')}", "kind": "observed", "src": "Model Steward", "date": _date(r.get("ts"))})
    nums = numbers()
    vids = nums.get("videos") or []
    if len(vids) >= 2:
        a, b = vids[-2], vids[-1]
        if a["avg_view_pct"] and b["avg_view_pct"]:
            d = b["avg_view_pct"] - a["avg_view_pct"]
            obs.append({"text": f"Average viewed {b['avg_view_pct']:.0f}% on the latest video vs {a['avg_view_pct']:.0f}% before ({d:+.0f} points).",
                        "kind": "observed", "src": "YouTube Analytics", "date": b.get("pulled")})
            if abs(d) >= 5:
                obs.append({"text": ("The newer structure is holding viewers better; keep its opening pattern." if d > 0 else
                                     "Viewers left earlier on the latest video; the next brief tightens the first 30 seconds."),
                            "kind": "interpretation", "src": "from the two numbers above", "date": b.get("pulled")})
    out = {"items": obs[-n:]}
    if not obs: out["empty"] = "Observations start after the first videos have 48-72 hours of analytics."
    return out

def strategy():
    from whatifs import governor as G
    t = today(); rec = recommendations(2); mode = "standard"
    try: mode = G.budget_mode()
    except Exception: pass
    plan = []
    if t.get("next_slot"): plan.append(f"Next slot {t['next_slot']['ist']}: long video, then 2-4 Shorts cut from it over the next days.")
    if rec.get("next_cases"): plan.append("Strongest idea on the bench: " + rec["next_cases"][0]["premise"])
    rules = _rows("Data_Rules")[-2:]
    if rules: plan.append("Briefs follow the latest data rules: " + "; ".join(str(r.get("text"))[:70] for r in rules))
    plan.append(f"Budget mode: {mode} (cap Rs {S('BUDGET_CEILING_INR')}).")
    return {"plan": plan, "why": "Built from the slot calendar, the idea bench and the data rules above (rule-based, no AI guess).", "kind": "interpretation"}

def experiments():
    xs = [{"episode": r.get("episode_id"), "hypothesis": r.get("hypothesis"), "variant": r.get("packaging_variant"), "ctr_48h": _f(r.get("ctr_48h")),
           "src": "Experiments"} for r in _rows("Experiments")[-4:]]
    return {"running": xs, **({} if xs else {"empty": "Experiments start with the first long video (title/thumbnail and opening tests)."})}

def money():
    from whatifs import governor as G
    month = now_utc().strftime("%Y-%m")
    spent = sum(_f(r.get("inr"), 0) or 0 for r in _rows("Cost_Log") if str(r.get("ts", "")).startswith(month))
    by = {}
    for r in _rows("Cost_Log"):
        if str(r.get("ts", "")).startswith(month): by[r.get("provider") or "other"] = by.get(r.get("provider") or "other", 0) + (_f(r.get("inr"), 0) or 0)
    return {"month_spend": round(spent), "cap": S("BUDGET_CEILING_INR", int), "by_provider": {k: round(v) for k, v in sorted(by.items(), key=lambda kv: -kv[1])},
            "src": "Cost_Log", "date": _date(iso())}

def build(demo=False):
    if demo: return demo_view()
    sec = {}
    for name, fn in (("today", today), ("numbers", numbers), ("hot_topics", hot_topics), ("recommendations", recommendations),
                     ("observations", observations), ("strategy", strategy), ("experiments", experiments), ("money", money)):
        try: sec[name] = fn()
        except Exception as e: sec[name] = {"empty": f"Not available right now ({type(e).__name__})."}
    sec["generated_at"] = iso(); sec["demo"] = False
    return sec

# ------------------------------------------------------------------ demo (clearly labelled)
def demo_view():
    vids = [("What if light moved at walking speed?", 4120, 46.2, 61.0, 5.8, 31), ("What if the Moon vanished tonight?", 9870, 51.4, 66.0, 7.1, 88),
            ("What if Earth stopped spinning?", 6310, 44.0, 58.0, 6.2, 47), ("What if you fell into Jupiter?", 15200, 53.9, 70.0, 8.4, 140)]
    v = [{"title": t, "views": a, "avg_view_pct": b, "ret30": c, "ctr": d, "subs": e, "yt_id": "DEMO", "pulled": "DEMO", "src": "DEMO"} for t, a, b, c, d, e in vids]
    return {"demo": True, "note": DEMO_NOTE, "generated_at": iso(),
            "today": {"next_slot": {"ist": "Sat 14 Nov 20:30 IST", "in_hours": 41.5}, "in_progress": [{"episode": "DEMO-5", "title": "What if oxygen doubled?", "status": "WRITING"}], "released_today": []},
            "numbers": {"videos": v, "totals": {"views": sum(x["views"] for x in v), "subs": sum(x["subs"] for x in v), "avg_view_pct": 48.9, "src": "DEMO"}, "specials": [], "pilots": []},
            "hot_topics": {"topics": [{"topic": "Comet sighting this week", "why": "search interest up 4x in 7 days (DEMO)", "src": "Google Trends (DEMO)", "date": "DEMO"},
                                      {"topic": "Mars at opposition (19 Feb 2027)", "why": "sky event: searches peak the week before (DEMO)", "src": "calendar (DEMO)", "date": "DEMO"},
                                      {"topic": "Could you survive on Venus?", "why": "top question this week (DEMO)", "src": "Stack Exchange (DEMO)", "date": "DEMO"}],
                           "outliers": [{"title": "What if the Sun disappeared? (12x channel median)", "url": "https://youtu.be/DEMO", "multiple": 12.0, "src": "DEMO"}]},
            "recommendations": {"next_cases": [{"premise": "What if gravity switched off for 5 seconds?", "score": 8.7, "search_demand": 0.81, "src": "DEMO"},
                                               {"premise": "What if you lived on a neutron star?", "score": 8.2, "search_demand": 0.64, "src": "DEMO"}],
                                "shorts": [{"idea": "Grimm's Lab Log: the 3-second verdict on 'Moon cheese'", "src": "DEMO"}], "watch_for_craft": []},
            "observations": {"items": [{"text": "Average viewed 53.9% on the latest video vs 44.0% before (+10 points).", "kind": "observed", "src": "DEMO", "date": "DEMO"},
                                       {"text": "The newer opening is holding viewers better; keep it.", "kind": "interpretation", "src": "from the line above", "date": "DEMO"}]},
            "strategy": {"plan": ["Next slot Sat 20:30 IST: long video + 3 Shorts.", "Strongest idea: gravity off for 5 seconds.", "Budget mode: standard (cap Rs 5000)."],
                         "why": "DEMO", "kind": "interpretation"},
            "experiments": {"running": [{"episode": "DEMO-4", "hypothesis": "A question title beats a statement title", "variant": "B", "ctr_48h": 8.4, "src": "DEMO"}]},
            "money": {"month_spend": 2140, "cap": 5000, "by_provider": {"fal": 1210, "anthropic": 690, "gemini": 240}, "src": "DEMO"}}

# ------------------------------------------------------------------ v10.3: one message per section (WhatsApp, digests); every number with its source
def _n(x, suf=""):
    if x is None: return "-"
    return (f"{x:,.0f}" if isinstance(x, (int, float)) and abs(x) >= 100 else (f"{x:.1f}" if isinstance(x, float) else str(x))) + suf

def render(name, view):
    """Short, scannable text: headline, up to 3 numbers, 1 observation, 1 recommendation, source/date. Never a made-up number."""
    s = view.get(name) or {}; demo = "[DEMO] " if view.get("demo") else ""
    if s.get("empty"): return f"{demo}*{TITLES.get(name, name)}*\n{s['empty']}"
    if name == "today":
        ns = s.get("next_slot") or {}
        lines = [f"Next slot: {ns.get('ist', '-')} (in {_n(ns.get('in_hours'))} h)"] + \
                [f"In progress: {x.get('title')} ({x.get('status')})" for x in (s.get("in_progress") or [])[:2]] + \
                [f"Released today: {x.get('title')}" for x in (s.get("released_today") or [])[:2]]
        src = "Episodes tab + slot calendar"
    elif name == "numbers":
        tt = s.get("totals") or {}; vids = s.get("videos") or []
        lines = [f"Views {_n(tt.get('views'))} | subs {_n(tt.get('subs'))} | avg viewed {_n(tt.get('avg_view_pct'), '%')}"] + \
                [f"{v['title'][:38]}: {_n(v['views'])} views, {_n(v.get('avg_view_pct'), '%')} viewed, CTR {_n(v.get('ctr'), '%')}" for v in vids[-3:]]
        src = f"{tt.get('src', 'YouTube Analytics')}, {tt.get('date') or '-'} (48-72 h delay)"
    elif name == "hot_topics":
        lines = [f"{t['topic']}: {t.get('why', '')} [{t.get('src')}]" for t in (s.get("topics") or [])[:3]] + \
                [f"Watch: {o['title']} ({_n(o.get('multiple'))}x its channel) {o.get('url')}" for o in (s.get("outliers") or [])[:2]]
        src = "weekly research (Trend_Brief) + daily outlier scan"
    elif name == "recommendations":
        lines = [f"Next case: {c['premise']} (score {_n(c.get('score'))}" + (f", search demand {c['search_demand']:.2f}" if c.get("search_demand") is not None else "") + ")"
                 for c in (s.get("next_cases") or [])[:3]] + [f"Short: {x['idea']}" for x in (s.get("shorts") or [])[:2]]
        src = "Premise_Bench (writers' + Gemini scores, YouTube search) + Pilots"
    elif name == "observations":
        lines = [("Observed: " if o.get("kind") == "observed" else "Interpretation: ") + str(o.get("text")) + f" [{o.get('src')}]" for o in (s.get("items") or [])[-4:]]
        src = "Retention Microscope, Slop Guard, Model Steward, YouTube Analytics"
    elif name == "strategy":
        lines = list(s.get("plan") or [])[:4] + [f"(Interpretation: {s.get('why')})"]
        src = "rule-based from the calendar, the bench and the data rules"
    elif name == "experiments":
        lines = [f"{x.get('episode')}: {x.get('hypothesis') or x.get('variant')} (CTR 48 h {_n(x.get('ctr_48h'), '%')})" for x in (s.get("running") or [])[-3:]]
        src = "Experiments tab"
    elif name == "money":
        lines = [f"Spent Rs {_n(s.get('month_spend'))} of Rs {_n(s.get('cap'))} this month"] + [f"{k}: Rs {_n(v)}" for k, v in list((s.get("by_provider") or {}).items())[:3]]
        src = f"Cost_Log, {s.get('date')}"
    else:
        lines, src = [json.dumps(s)[:300]], "-"
    return f"{demo}*{TITLES.get(name, name)}*\n" + "\n".join(f"- {l}" for l in lines if l) + f"\nSource: {src}"

TITLES = {"today": "Today", "numbers": "Numbers", "hot_topics": "Hot topics", "recommendations": "What to post next", "observations": "Observations",
          "strategy": "Strategy", "experiments": "Experiments", "money": "Spend"}

