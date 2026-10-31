"""whatifs/growth.py v8.7 - the click-through + retention layer of the learning loop. Small, free (no model calls), and read by real production code:
1. lessons_for(role)      : each department gets the lessons meant for it (the Reel Producer gets the Shorts lessons, the Packager the packaging ones...).
2. choose_titles()        : code-checked titles (30-60 characters, front-loaded, not shouting, not repeating the thumbnail words); best + runner-up.
3. thumb_words()          : thumbnail text is 1-4 words (readable at phone size).
4. dim_scores()           : every strategy dimension is scored on the metric it can actually move (titles/thumbnails on clicks, hooks on the first 30 s,
                            stories on how much is watched, Shorts on the long-video views they bring). Missing data is never invented.
5. diagnose()             : one plain label per analysed video (packaging / opening / holding / healthy / insufficient data) + a routed lesson.
6. strategy changes are logged (Strategy_Log) and a replacement that does worse than the strategy it replaced is rolled back automatically, once.
v8.7: 7. packaging-first promise (clean_promise), 8. retention gate (retention_issues: opening, re-hooks, re-engagement near 3:00 / 6:00, open loops),
9. rhythm blueprint per episode (rhythm_plan: least-recently-used cold-open device, interrupt, music arc, reaction density), 10. watch time per impression
for packaging (YouTube's own Test & Compare judges by watch time, not CTR), CTR unit self-check, retention vs similar-length YouTube videos for early
diagnosis, the steepest drop mapped to its beat (dip_lesson), and the related-video link (related_episode).
Sources for the rules (paraphrased, see REVISION_NOTES v8.6): YouTube's own creator guidance, the leaked 'How to Succeed in MrBeast Production' guide
(title + thumbnail first, the first minute decides retention, the video must deliver the thumbnail's promise), and large title-length studies (30-60 characters).
"""
from __future__ import annotations
import json, re, statistics
from whatifs.core import store, S, iso, log

# ------------------------------------------------------------------ 1. lessons go to the department that can use them
ROUTES = {
    "showrunner": ("story", "family", "topic", "hook", "general", "opening", "holding", "rhythm", "showrunner", ""),
    "packager":   ("title", "thumb", "packaging", "packager"),
    "writer":     ("hook", "voice", "humour", "banter", "story", "reactions", "opening", "holding", "rhythm", "writer"),
    "director":   ("sound", "director"),
    "reel":       ("reels", "reel"),
}

def _rows(tab):
    try: return store().rows(tab)
    except Exception as e: log(f"{tab} not readable yet ({e})", "WARN"); return []

def lessons_for(role, n=12, rows=None):
    """The n most recent lessons whose applies_to belongs to this role (blank applies_to = general). Never an empty prompt: 'none yet'."""
    tags = ROUTES.get(role, ("",))
    rows = _rows("Lessons") if rows is None else rows
    pick = [str(r.get("lesson", "")) for r in rows if str(r.get("applies_to", "") or "").strip().lower() in tags and r.get("lesson")]
    return "\n".join(pick[-n:])[:2500] or "none yet"

# ------------------------------------------------------------------ 2-3. packaging rules checked in code
_SMALL = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or", "is", "if", "what", "we", "you", "it", "this", "that", "with", "by", "be"}

def _words(t): return [w for w in re.findall(r"[A-Za-z0-9']+", str(t or "").lower())]

def title_issues(title, thumb_text=""):
    """Problems a viewer would feel on a phone. Empty list = clean."""
    t = str(title or "").strip(); out = []
    n = len(t)
    if n < S("TITLE_MIN_CHARS", int): out.append(f"short ({n} chars)")
    if n > S("TITLE_MAX_CHARS", int): out.append(f"long ({n} chars, cut off on phones)")
    caps = [w for w in re.findall(r"[A-Za-z]+", t) if len(w) > 4 and w.isupper()]
    if len(caps) > 1: out.append("shouting (more than one ALL-CAPS word)")
    tw = {w for w in _words(thumb_text) if w not in _SMALL}
    if tw and len(tw & set(_words(t))) / len(tw) >= 0.6: out.append("repeats the thumbnail words (they should complement, not copy)")
    if t.count("!") > 1 or t.count("?") > 1: out.append("too much punctuation")
    return out

def choose_titles(titles, thumb_text=""):
    """(best, runner_up). Keeps the Packager's order (it ranks best first) but moves clean titles ahead of flawed ones; never returns an empty title
    when any title exists. A title over YouTube's 100-character limit is cut at a word boundary."""
    seen, cand = set(), []
    for i, t in enumerate(titles or []):
        t = re.sub(r"\s+", " ", str(t or "")).strip().strip('"')
        if not t or t.lower() in seen: continue
        seen.add(t.lower())
        if len(t) > 100: t = t[:100].rsplit(" ", 1)[0]
        cand.append((sum(2 if x.startswith("long") else 1 for x in title_issues(t, thumb_text)), i, t))      # a title cut off on phones is the worst flaw
    if not cand: return "", ""
    cand.sort()
    best = cand[0][2]; runner = cand[1][2] if len(cand) > 1 else ""
    if cand[0][0]: log(f"packaging: every title had an issue; using the least flawed ({'; '.join(title_issues(best, thumb_text))})", "WARN")
    return best, runner

def thumb_words(text, max_words=None):
    """Thumbnail text, at most THUMB_MAX_WORDS words (phone readability). Trailing small words are dropped so the cut never ends on 'OF' or 'THE'."""
    max_words = max_words or S("THUMB_MAX_WORDS", int)
    w = str(text or "").split()
    if len(w) <= max_words: return " ".join(w)
    w = w[:max_words]
    while len(w) > 1 and w[-1].lower().strip(".,!?") in _SMALL: w.pop()
    return " ".join(w)

# ------------------------------------------------------------------ 4. per-dimension scores (0-1, about 0.5 = a typical video for this channel)
DIM_METRIC = {"title": "pack", "thumb": "pack", "hook": "open", "voice": "open", "humour": "hold", "banter": "hold", "story": "hold",
              "family": "reach", "reel": "shorts", "rhythm": "hold", "sound": "hold"}      # v8.7: pacing blueprints and sound density are judged on watch share

def _num(v):
    try: return None if v in (None, "") else float(v)
    except Exception: return None

def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None

def dim_scores(m, history):
    """m = this video's metrics; history = earlier Analytics rows. A part whose data is missing is None (that dimension is simply not credited)."""
    views = _num(m.get("views")); ctr = _num(m.get("ctr")); r30 = _num(m.get("ret30")); avp = _num(m.get("avg_view_pct")); fs = _num(m.get("from_shorts"))
    med_v = _median([_num(h.get("views")) for h in history]); med_fs = _median([_num(h.get("from_shorts")) for h in history])
    pack = min(1.0, ctr / 0.10) if ctr is not None and ctr > 0 else None                 # 10 % click-through ~ 1.0
    wt = _num(m.get("wtpi")); med_wt = _median([_num(h.get("wtpi")) for h in history])     # v8.7: watch seconds per impression (real CTR x average view duration)
    if wt is not None and wt > 0: pack = min(1.0, 0.5 * wt / med_wt) if med_wt else min(1.0, wt / 18.0)      # YouTube's Test & Compare judges by watch time, not CTR
    opn = max(0.0, min(1.0, r30)) if r30 is not None else None                         # share still watching at ~5 % of the runtime
    hold = min(1.0, avp / 80.0) if avp is not None and avp > 0 else None               # 40 % viewed ~ 0.5
    reach = min(1.0, 0.5 * views / med_v) if views is not None and med_v else (0.5 if views is not None else None)
    ss = _num(m.get("shorts_subs")); med_ss = _median([_num(h.get("shorts_subs")) for h in history])
    parts = []                                                                         # Shorts judged on what they bring the channel, not raw Short views
    if fs is not None: parts.append(min(1.0, 0.5 * fs / med_fs) if med_fs else (0.5 if fs > 0 else 0.25))
    if ss is not None: parts.append(min(1.0, 0.5 * ss / med_ss) if med_ss else (0.5 if ss > 0 else 0.25))
    shorts = sum(parts) / len(parts) if parts else None
    return {"pack": pack, "open": opn, "hold": hold, "reach": reach, "shorts": shorts}

def composite(sc):
    """The single Analytics 'score' (kept for reports and older strategies): clicks 20 %, opening 40 %, holding 40 %, renormalised over what exists."""
    w = {"pack": 0.2, "open": 0.4, "hold": 0.4}; got = {k: sc[k] for k in w if sc.get(k) is not None}
    if not got: return None
    return round(sum(w[k] * v for k, v in got.items()) / sum(w[k] for k in got), 4)

def score_for(dim, sc):
    """The number a strategy of this dimension is credited with, or None (not credited)."""
    k = DIM_METRIC.get(dim)
    return sc.get(k) if k else composite(sc)

# ------------------------------------------------------------------ 5. diagnosis
def diagnose(m, history):
    """(label, lesson or ''). Compared with this channel's own medians; needs MIN_HISTORY earlier videos, otherwise 'insufficient data'."""
    if len(history) < S("DIAG_MIN_HISTORY", int):            # v8.7: no channel baseline yet, but YouTube compares the video with all videos of similar length (0.5 = typical)
        t = str(m.get("title") or m.get("episode_id") or ""); r30, ra = _num(m.get("rel30")), _num(m.get("rel_avg"))
        if r30 is not None and r30 < 0.35: return "opening", f"opening: '{t}' held viewers in the first ~30 s worse than most YouTube videos of its length (relative {r30:.2f}, 0.5 = typical); show the promise sooner"
        if ra is not None and ra < 0.35: return "holding", f"holding: '{t}' kept viewers worse than most YouTube videos of its length (relative {ra:.2f}, 0.5 = typical); more re-hooks, shorter slow beats"
        return "insufficient data", ""
    sc = dim_scores(m, history); hs = [dim_scores(h, history) for h in history]
    med = {k: _median([h[k] for h in hs]) for k in ("pack", "open", "hold")}
    low = {k for k in ("pack", "open", "hold") if sc[k] is not None and med[k] and sc[k] < 0.8 * med[k]}
    if not any(sc[k] is not None for k in ("pack", "open", "hold")): return "insufficient data", ""
    t = str(m.get("title") or m.get("episode_id") or "")
    if "open" in low: return "opening", f"opening: '{t}' lost viewers in the first ~30 s ({sc['open']:.2f} vs usual {med['open']:.2f}); prove the title's promise sooner, no setup before the impossible image"
    if "hold" in low: return "holding", f"holding: '{t}' was watched less than usual ({sc['hold']:.2f} vs {med['hold']:.2f}); add a re-hook every 60-90 s and cut the slowest stretch"
    if "pack" in low: return "packaging", f"packaging: '{t}' got fewer clicks than usual while viewers who clicked stayed; the title/thumbnail undersold it"
    return "healthy", ""

DIAG_ROUTE = {"opening": "opening", "holding": "holding", "packaging": "packaging"}

# ------------------------------------------------------------------ 6. strategy changes: logged, evaluated, rolled back once if worse
def log_change(dim, action, name, replaces="", mean_at_change="", note=""):
    try: store().append("Strategy_Log", [{"ts": iso(), "dimension": dim, "action": action, "name": name, "replaces": replaces,
                                          "mean_at_change": mean_at_change, "note": str(note)[:300]}])
    except Exception as e: log(f"Strategy_Log not writable yet ({e}); change was: {dim} {action} {name}", "WARN")

def _mean(r):
    n = _num(r.get("score_n")) or 0
    return (_num(r.get("score_sum")) or 0) / n if n else None

def rollbacks():
    """A strategy invented to replace a retired one gets STRATEGY_EVAL_PLAYS plays. If its mean is below the retired strategy's mean at the time it was retired,
    the old one comes back (ACTIVE, its record intact) and the new one is retired. Each replacement is judged once. Returns the list of rollbacks."""
    st = store(); log_rows = _rows("Strategy_Log"); strat = {r["name"]: r for r in st.rows("Strategies")}
    judged = {r["name"] for r in log_rows if r.get("action") in ("kept", "rolled_back")}
    out = []
    for r in log_rows:
        if r.get("action") != "invented" or r["name"] in judged or r["name"] not in strat or r.get("replaces") not in strat: continue
        new = strat[r["name"]]
        if new.get("status") != "ACTIVE" or (_num(new.get("score_n")) or 0) < S("STRATEGY_EVAL_PLAYS", int): continue
        old_mean = _num(r.get("mean_at_change")); nm = _mean(new)
        if old_mean is None or nm is None: continue
        if nm < old_mean:
            st.update_where("Strategies", {"dimension": r["dimension"], "name": r["name"]}, {"status": "RETIRED"})      # v8.9.1: matched on dimension AND name
            st.update_where("Strategies", {"dimension": r["dimension"], "name": r["replaces"]}, {"status": "ACTIVE"})
            log_change(r["dimension"], "rolled_back", r["name"], r["replaces"], round(nm, 4), f"new mean {nm:.3f} < old {old_mean:.3f}: restored {r['replaces']}")
            st.append("Lessons", [{"ts": iso(), "lesson": f"{r['dimension']}: '{r['name']}' did worse than '{r['replaces']}' ({nm:.2f} vs {old_mean:.2f}); restored the old one",
                                   "evidence": "Strategy_Log", "applies_to": r["dimension"]}])
            out.append((r["name"], r["replaces"]))
        else:
            log_change(r["dimension"], "kept", r["name"], r["replaces"], round(nm, 4), f"new mean {nm:.3f} >= old {old_mean:.3f}")
    return out

def recently_restored(name, days=30):
    """A strategy brought back by a rollback is not retired again for `days` (no flip-flopping)."""
    import datetime as dt
    from whatifs.core import parse_iso, now_utc
    for r in _rows("Strategy_Log"):
        if r.get("action") == "rolled_back" and r.get("replaces") == name:
            t = parse_iso(r.get("ts"))
            if t and now_utc() - t < dt.timedelta(days=days): return True
    return False


# ------------------------------------------------------------------ 7. v8.7 packaging first: the promise the script is written to
_STOP = set("this that with from have what when they them then than were been will would could should about into your their there which while where every just "
            "like more most very much also only over even after before what".split())

def clean_promise(spine):
    """The Showrunner's click promise, code-checked: the cleanest title among the promise title, the title candidates and the headline; 1-4 thumbnail words;
    the thumbnail scene and what the first 30 s must show (falling back to the concept / peak the Showrunner already wrote). Never empty when anything exists."""
    spine = spine or {}; p = spine.get("promise") if isinstance(spine.get("promise"), dict) else {}
    tw = thumb_words(p.get("thumb_text") or "")
    titles = [x for x in [p.get("title")] + list(spine.get("title_candidates") or []) + [spine.get("headline")] if str(x or "").strip()]
    best, _ = choose_titles(titles, tw) if titles else ("", "")
    return {"title": best, "thumb_text": tw, "thumb_scene": str(p.get("thumb_scene") or spine.get("thumb_concept") or "")[:300],
            "first_30s": str(p.get("first_30s") or spine.get("peak_moment") or "")[:300]}

def promise_text(p):
    p = p or {}
    if not any(p.get(k) for k in ("title", "thumb_text", "thumb_scene", "first_30s")): return "none"
    return (f"Title: {p.get('title', '')} | Thumbnail words: {p.get('thumb_text', '')} | Thumbnail image: {p.get('thumb_scene', '')} | "
            f"The first 30 s must show and say: {p.get('first_30s', '')}")

def insert_before_json(prompt, text):
    """Extra brief text goes BEFORE the reply-format line, so 'Return JSON' stays the last thing the model reads."""
    if not text: return prompt
    i = prompt.rfind("\nReturn JSON")
    return prompt + "\n" + text if i < 0 else prompt[:i] + "\n" + text + prompt[i:]

# ------------------------------------------------------------------ 8. v8.7 retention gate (code-checked, one targeted fix at most)
OPENING_WORDS = 110          # about 45 s at 150 words a minute
REHOOK_RX = re.compile(r"\b(but|wait|hold on|here'?s (the|where|what|why)|that'?s not|it gets (worse|stranger|weirder)|which means|until|except|turns out|guess what|watch this|now watch)\b", re.I)
STRONG_RX = re.compile(r"\b(wait|hold on|here'?s (the|where|what|why)|that'?s not (all|the)|it gets (worse|stranger|weirder)|turns out|watch this|now watch|plot twist)\b", re.I)
_LEAD = re.compile(r"^\s*(?:(?:\[[^\]]{1,26}\]|\*\*|[A-Z][A-Za-z ]{2,24}:)\s*)+")

def _mmss(t): t = max(0, int(t)); return f"{t // 60}:{t % 60:02d}"
def _stems(t): return {w[:5] for w in re.findall(r"[a-z]{4,}", str(t or "").lower()) if w not in _STOP}

def script_lines(text, wpm=150.0):
    """Spoken lines with an estimated start time (words / wpm) and their delivery tags. Beat lines and labels are not spoken."""
    out, words = [], 0
    for raw in str(text or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("##"): continue
        lead = _LEAD.match(s); tags = [x.lower() for x in re.findall(r"\[([A-Za-z_]+)", lead.group(0))] if lead else []
        body = re.sub(r"\[[^\]]{1,26}\]", " ", s[lead.end():] if lead else s).strip(); n = len(body.split())
        if not n: continue
        out.append({"t": words / max(1.0, wpm) * 60.0, "text": body, "tags": tags, "words": n}); words += n
    return out, words / max(1.0, wpm) * 60.0

def retention_issues(text, promise=None, wpm=150.0, loops=None):
    """Problems a viewer would feel, with WHERE they are. {'ok', 'issues', 'max_gap', 'total'}. Free (no model call)."""
    lines, total = script_lines(text, wpm); issues = []; promise = promise or {}
    op, w = [], 0
    for l in lines:
        if w >= OPENING_WORDS: break
        op.append(l); w += l["words"]
    otext = " ".join(l["text"] for l in op)
    ps = _stems(" ".join(str(promise.get(k) or "") for k in ("title", "thumb_text", "thumb_scene")))
    if op and ps and not (ps & _stems(otext)):
        issues.append(f"opening: the first ~45 s never shows or names the promise ({promise_text(promise)[:170]}); put that image and those words in now")
    if op and "?" not in otext and not REHOOK_RX.search(otext): issues.append("opening: no open question or turn in the first ~45 s; plant the question the video answers")
    if op:
        from whatifs.hooks import _GREET
        if _GREET.match(op[0]["text"]): issues.append("opening: the first line clears its throat (a greeting, 'today', 'did you know'); start on the impossible thing")
    marks = [l["t"] for l in lines if "?" in l["text"] or REHOOK_RX.search(l["text"]) or set(l["tags"]) & {"reveal", "tension", "wow", "gasp", "awe"} or re.search(r"\d", l["text"])]
    pts = [0.0] + marks + [total]; gaps = [(b - a, a, b) for a, b in zip(pts, pts[1:])]; worst = max(gaps) if gaps else (0.0, 0.0, 0.0)
    if worst[0] > S("REHOOK_MAX_GAP_SEC", float):
        issues.append(f"holding: {worst[0]:.0f} s without a re-hook ({_mmss(worst[1])}-{_mmss(worst[2])}); add a question, a turn or a number in that stretch")
    strong = [l["t"] for l in lines if STRONG_RX.search(l["text"]) or set(l["tags"]) & {"reveal", "wow", "gasp", "awe"}]
    for target in (180, 360):
        if total > target + 30 and not any(abs(x - target) <= 45 for x in strong):
            issues.append(f"re-engagement: nothing genuinely new lands near {_mmss(target)}; put a turn that impresses (a reveal, a 'wait...') between {_mmss(target - 45)} and {_mmss(target + 45)}")
    for lp in (loops or []):
        if isinstance(lp, dict) and str(lp.get("open") or "").strip() and not str(lp.get("closed_in_beat") or "").strip():
            issues.append(f"payoff: the question '{str(lp['open'])[:80]}' is opened but never answered; answer it before the end")
    return {"ok": not issues, "issues": issues[:8], "max_gap": round(worst[0], 1), "total": round(total, 1)}

# ------------------------------------------------------------------ 9. v8.7 rhythm blueprint: no two episodes in a row with the same shape
REACTION_COUNT = {"sparse": "3-4", "medium": "4-5", "dense": "5-6"}

def rhythm_plan(name, rng, recent=()):
    """The concrete pacing plan of one episode: the blueprint (a learned strategy), and per-episode choices taken least-recently-used from the last episodes
    (ties broken by the episode's seeded coin), so the cold-open device, the pattern interrupt, the music arc and the reaction density keep moving."""
    from whatifs.data import RHYTHM_SPECS, OPENERS, INTERRUPTS
    from whatifs.sound import ARCS
    spec = RHYTHM_SPECS.get(name) or {}; recent = [r for r in recent if isinstance(r, dict)]
    def lru(pool, key):
        last = {}
        for k, p in enumerate(recent):
            if p.get(key): last[p[key]] = k
        return sorted(pool, key=lambda x: (last.get(x, -1), rng.random()))[0]
    plan = {"blueprint": name or "", "opener": lru(sorted(OPENERS), "opener"), "interrupt": lru(sorted(INTERRUPTS), "interrupt"),
            "arc": spec["arc"] if spec.get("arc") in ARCS else lru(list(ARCS), "arc"),
            "reactions": spec["reactions"] if spec.get("reactions") in REACTION_COUNT else lru(list(REACTION_COUNT), "reactions")}
    prev = recent[-1] if recent else {}
    plan["same_as_last"] = sum(1 for k in ("blueprint", "opener", "interrupt", "arc", "reactions") if prev.get(k) == plan[k])
    return plan

def rhythm_brief(plan, defs=None):
    from whatifs.data import OPENERS, INTERRUPTS
    if not plan: return ""
    defs = defs or {}
    return ("RHYTHM BLUEPRINT for THIS episode (viewers, and YouTube's rule against templated videos, both punish episodes that all feel the same; never reuse the "
            f"last episode's shape): {plan.get('blueprint')}: {defs.get(plan.get('blueprint'), '')} COLD OPEN DEVICE: {OPENERS.get(plan.get('opener'), plan.get('opener'))} "
            f"PATTERN INTERRUPT (exactly once, in the middle third): {INTERRUPTS.get(plan.get('interrupt'), plan.get('interrupt'))} "
            f"REACTIONS: {REACTION_COUNT.get(plan.get('reactions'), '4-5')} short Curious One reaction lines. MUSIC ARC: {plan.get('arc')}. "
            "Write one or two [close] lines (quiet, intimate, slower) at the most human moment; vary sentence length hard (3-word lines next to long rolling ones).")

# ------------------------------------------------------------------ 10. v8.7 measurement: CTR unit, related video, the steepest drop
def ctr_ratio(raw, impressions=None, views=None):
    """Impressions click-through as a ratio (0.05 = 5 %). The API documents a percentage; when impressions are known the unit is CHECKED: if
    impressions x value is at most ~1.5x the views, the value was already a ratio. None if unreadable."""
    v = _num(raw)
    if v is None or v < 0: return None
    if v > 0.5: return round(v / 100.0, 5)                                # v8.7 review: a click-through above 50 % is impossible, so this is a percentage
    imp, vw = _num(impressions), _num(views)
    if imp and imp > 0 and vw is not None and imp * v <= max(vw, 1.0) * 1.5: return round(v, 5)
    return round(v / 100.0, 5)

def related_episode(eps, analytics=(), family="", exclude=""):
    """The best earlier PUBLIC video to send viewers to next: same topic family first, then the best Analytics score, then the newest. Never a video that is
    not live (scheduled, held, killed or failed). None if there is none yet."""
    score = {a.get("episode_id"): (_num(a.get("score")) or 0.0) for a in analytics or []}; cands = []
    for e in eps or []:
        vid = str(e.get("yt_id") or "").strip()
        if e.get("episode_id") == exclude or e.get("status") not in ("LIVE1", "LIVE") or not vid or " " in vid: continue
        if str(e.get("kill", "")).upper().startswith("KILL"): continue
        try: fam = json.loads(e.get("draw_json") or "{}").get("family", "") if not isinstance(e.get("draw_json"), dict) else e["draw_json"].get("family", "")
        except Exception: fam = ""
        cands.append((bool(family) and fam == family, score.get(e.get("episode_id"), 0.0), str(e.get("slot_et") or ""), e))
    if not cands: return None
    cands.sort(key=lambda c: (c[0], c[1], c[2]), reverse=True); e = cands[0][3]
    return {"episode_id": e.get("episode_id"), "title": str(e.get("title") or "")[:90], "url": f"https://youtu.be/{e['yt_id']}"}

def dip_lesson(curve, beat_map, duration, title=""):
    """The steepest ~30 s drop after the intro (end screen excluded), if it is clearly worse than the video's usual drop, mapped to the beat it falls in.
    '' when there is no clear dip or the data is too thin. curve = [(elapsed ratio, audience watch ratio)]."""
    try: pts = sorted((float(a), float(b)) for a, b in curve or [])
    except Exception: return ""
    dur = _num(duration) or 0
    if len(pts) < 20 or dur < 60: return ""
    w = max(2, int(round(30.0 / dur * 100)))
    lo = 30.0 / dur
    drops = [(pts[i][1] - pts[i + w][1], i) for i in range(len(pts) - w) if pts[i][0] >= lo and pts[i + w][0] <= 0.92]
    if len(drops) < 3: return ""
    med = statistics.median(max(0.0, d) for d, _ in drops) or 1e-6; worst, i = max(drops)
    if worst < max(0.03, 1.8 * med): return ""
    a, b = pts[i][0] * dur, pts[i + w][0] * dur; beat = ""
    for st, name in sorted(((float(x[0]), str(x[1])) for x in beat_map or [] if len(x) >= 2), key=lambda z: z[0]):
        if st <= a: beat = name
    return (f"holding: '{title}' lost {worst * 100:.0f} % of viewers between {_mmss(a)} and {_mmss(b)}" + (f" (beat '{beat[:40]}')" if beat else "") +
            f", {worst / med:.1f}x its usual drop; shorten that beat or put a re-hook just before it")
