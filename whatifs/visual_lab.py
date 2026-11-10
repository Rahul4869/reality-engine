"""Visual Lab: weekly ranking of picture treatments by how viewers held during them, proposed at the same cost. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import statistics
from whatifs.core import S, log, store, now_utc

# zero-cost picture treatments (code only). flag = the Settings switch when it already exists (then "switch on" rather than "build").
CATALOG = [
    {"id": "micro_cuts", "for": ["still"], "flag": "MICRO_CUTS_ON", "name": "Micro-cuts on stills",
     "what": "a long still changes framing every 2.6-3.2 s (wide / detail crop + a new camera move) instead of one slow move"},
    {"id": "motion_ramps", "for": ["clip", "living"], "flag": "MOTION_BOOST_ON", "name": "Speed ramps on moving clips",
     "what": "Kling / living clips speed up into the key moment and ease out (code-only time remap)"},
    {"id": "jl_cuts", "for": ["still", "clip", "living"], "flag": "JL_CUTS_ON", "name": "J/L-cuts at scene changes",
     "what": "the next scene's sound starts 0.35 s before its picture (feels continuous, holds attention across cuts)"},
    {"id": "darkness_ramp", "for": ["still", "clip", "living"], "flag": "DARKNESS_RAMP_ON", "name": "Darkness rises with danger",
     "what": "the colour grade darkens beat by beat as the stakes rise (technique card TC-001)"},
    {"id": "impact_punch", "for": ["still", "graphic"], "flag": "IMPACT_PUNCH_ON", "name": "Impact punch-in on key words",
     "what": "a 2-frame 6% punch-in on the line's most important word (never a flash; photosensitivity-safe)"},
    {"id": "rack_focus", "for": ["still"], "flag": "RACK_FOCUS_ON", "name": "Rack-focus pull on stills",
     "what": "background blur pulls to the subject on the first 0.6 s of a still (depth without new images)"},
    {"id": "grain_grade", "for": ["still", "living"], "flag": "FILM_GRAIN_ON", "name": "Cinematic grain + vignette",
     "what": "light film grain and a soft vignette unify AI stills so they read less 'AI-clean'"},
    {"id": "dust_particles", "for": ["still"], "flag": "ATMOSPHERE_ON", "name": "Atmosphere particles",
     "what": "floating dust / embers / snow layers matched to the scene (Atmosphere Pack)"},
]

def _flag_on(flag):
    try: return bool(S(flag, bool))
    except Exception: return False            # an unknown flag = not built yet

def analyse():
    """{shot_type: {'n', 'mean_vs_median'}} from Retention_Map (vs_median > 0 = viewers left FASTER than usual during that kind of shot)."""
    rows = store().rows("Retention_Map"); per = {}; eps = set()
    for r in rows:
        try: v = float(r.get("vs_median"))
        except (TypeError, ValueError): continue
        eps.add(r.get("episode_id"))
        for t in [x.strip() for x in str(r.get("shot_types") or "").split(",") if x.strip()]:
            per.setdefault(t, []).append(v)
    return {t: {"n": len(v), "mean_vs_median": round(statistics.mean(v), 3)} for t, v in per.items() if v}, len(eps)

def suggest(now=None):
    """Create at most VISUAL_LAB_MAX_CARDS cards a week. Returns the list of catalog ids suggested."""
    if not S("VISUAL_LAB_ON", bool): return []
    stats, n_eps = analyse()
    if n_eps < S("VISUAL_LAB_MIN_VIDEOS", int): log(f"Visual Lab: {n_eps} video(s) with retention data, waiting for {S('VISUAL_LAB_MIN_VIDEOS', int)}"); return []
    weak = sorted([(d["mean_vs_median"], t) for t, d in stats.items() if d["n"] >= 3 and d["mean_vs_median"] > 0.02], reverse=True)
    if not weak: return []
    from whatifs import notify as NT
    out = []; wk = (now or now_utc()).strftime("%G-W%V")
    for score, shot in weak:
        for c in CATALOG:
            if shot not in c["for"] or _flag_on(c["flag"]) or c["id"] in out: continue
            built = c["flag"] in __import__("whatifs.core", fromlist=["DEFAULTS"]).DEFAULTS
            text = (f"Visual idea: <b>{c['name']}</b>. Viewers leave about {score * 100:.0f}% faster than usual during {shot} shots "
                    f"(over {stats[shot]['n']} moments in {n_eps} videos). Idea: {c['what']}. Cost: ₹0 (code only). "
                    + ("It already exists: one tap switches it on." if built else "It needs a small build (Claude Code, ₹0)."))
            NT.send("visual_idea", text, [("Discuss", f"DISCUSS {c['id']}"), ("Build it" if not built else "Switch on", f"VISUAL {c['id']}"), ("Park", "PARK")],
                    tier="week", default="parked", expires_h=24 * 7, dedupe_key=f"visual|{c['id']}|{wk}")
            out.append(c["id"]); break
        if len(out) >= S("VISUAL_LAB_MAX_CARDS", int): break
    return out

def _on_answer(row, choice):
    """[Switch on] flips an existing flag; [Build it] hands the spec to Claude Code; DISCUSS/PARK are recorded for the chat."""
    c = str(choice).strip()
    if not c.upper().startswith("VISUAL "): return "recorded"
    cid = c.split(" ", 1)[1].strip(); item = next((x for x in CATALOG if x["id"] == cid), None)
    if not item: return "unknown idea"
    from whatifs.core import DEFAULTS, set_setting
    if item["flag"] in DEFAULTS:
        set_setting(item["flag"], "TRUE"); return f"{item['flag']} switched on"
    from whatifs.builds import request_build
    ok = request_build(f"Visual Lab idea '{item['name']}': {item['what']}. Build it as a code-only render effect behind a new Settings switch {item['flag']} "
                       f"(default FALSE until the owner switches it on), photosensitivity-safe, through v91.guard, with tests and a golden-frame check.", "feature")
    return "build started" if ok else "build could not start"

def register():
    from whatifs import notify as NT
    NT.register("visual_idea", on_answer=_on_answer)
