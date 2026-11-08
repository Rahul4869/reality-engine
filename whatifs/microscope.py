"""v10 G3 Retention Microscope (K138; decision 3 amends K106): data rules from second-by-second retention reach the writer's brief.
From Retention_Map (per beat: shot types, drop per 30 s vs the channel median, views) a shot type becomes a BOOSTER or a KILLER only when
the effect holds across >= MICRO_MIN_VIDEOS videos with >= MICRO_MIN_VIEWS views each, and its average distance from the median is larger
than MICRO_MIN_EFFECT. Rules live in Data_Rules with the number of the video they started at; a rule expires after MICRO_RULE_LIFE videos
unless it is re-confirmed. Rules never touch the budget, picture counts or quality gates; they only add one short line each to the writer
and the dashboard. Rule-based: no AI call."""
from __future__ import annotations
import statistics
from whatifs.core import S, log, store, iso

def _videos_done():
    return len([e for e in store().rows("Episodes") if e.get("yt_id")])

def learn():
    rows = store().rows("Retention_Map"); per = {}
    for r in rows:
        try: v, views = float(r.get("vs_median")), float(r.get("views") or 0)
        except (TypeError, ValueError): continue
        if views < S("MICRO_MIN_VIEWS", float): continue
        for t in [x.strip() for x in str(r.get("shot_types") or "").split(",") if x.strip()]:
            per.setdefault(t, {}).setdefault(r.get("episode_id"), []).append(v)
    st = store(); now_n = _videos_done(); made = []
    existing = {r.get("key"): r for r in st.rows("Data_Rules")}
    for t, eps in per.items():
        if len(eps) < S("MICRO_MIN_VIDEOS", int): continue
        eff = statistics.mean(statistics.mean(v) for v in eps.values())
        if abs(eff) < S("MICRO_MIN_EFFECT", float): continue
        kind = "killer" if eff > 0 else "booster"
        text = (f"Viewers leave {abs(eff) * 100:.0f}% faster than usual during {t} shots: keep them short and change the picture sooner." if kind == "killer"
                else f"Viewers stay {abs(eff) * 100:.0f}% better than usual during {t} shots: use them at the moments that usually lose people.")
        key = f"{kind}:{t}"
        if key in existing: st.update("Data_Rules", "key", key, {"text": text, "confirmed_at_video": now_n, "videos": len(eps), "effect": round(eff, 3)})
        else: st.append("Data_Rules", [{"ts": iso(), "key": key, "kind": kind, "text": text, "videos": len(eps), "effect": round(eff, 3), "started_at_video": now_n, "confirmed_at_video": now_n}])
        made.append(key)
    if made: log(f"Retention Microscope: {len(made)} data rule(s) active or re-confirmed")
    return made

def active_rules():
    now_n = _videos_done(); life = S("MICRO_RULE_LIFE", int)
    return [r for r in store().rows("Data_Rules") if now_n - int(float(r.get("confirmed_at_video") or 0)) < life]

def brief():
    if not S("MICRO_RULES_ON", bool): return ""
    rules = active_rules()
    if not rules: return ""
    return "DATA RULES (from this channel's own retention, Retention Microscope): " + " ".join(r["text"] for r in rules[:4])
