"""whatifs/packaging.py v9 (stage 3b) - three title + thumbnail pairs per video, an owner pick for the first THUMB_APPROVAL_FIRST_N videos that never
blocks a slot, rotation of the pairs in the first 48 hours with the result measured, and the hook shapes (K100).

YouTube Studio's "Test & Compare" has no public API that we could verify, so the fallback is used: the pairs are rotated through the Data API
(videos.update title + thumbnails.set) in equal windows inside the first PKG_ROTATE_HOURS, and each window's views per hour (and the impression CTR when
the Analytics API returns it) is recorded in Packaging_Tests; the best pair stays. A third pair re-uses the main thumbnail picture with its own text unless
PKG_VARIANT_C_IMAGE is TRUE (then one more premium image is bought: about Rs 8)."""
from __future__ import annotations
import json, re
from whatifs.core import S, log, store, iso, now_utc, parse_iso, env, FAKE

# Hook shapes adapted (ideas only, not installed) from the MIT-licensed open-source YouTube agent skill pack; credited in docs/CHANGES.md.
HOOK_SHAPES = {"statistic": "The Statistic (a number with its stated source)", "contrarian": "Contrarian Flip", "reveal": "The Reveal", "clock": "The Clock",
               "question": "The Question", "impossible": "The Impossible Claim", "comparison": "The Comparison", "list": "The List", "superlative": "The Superlative"}

TITLE_BRIEF = ("TITLES (v9.2): every title must STOP THE SCROLL in under a second. Use these shapes across the three titles: "
               "(1) BOLD CLAIM + QUESTION - a shocking statement, then a dare ('Your Reflection Is 1.4 Seconds Late. Is It Still You?'); "
               "(2) IMPOSSIBLE CLAIM - one flat sentence that sounds wrong ('Light Just Lost a Race to Your Cat'); "
               "(3) CONTRARIAN / SHOCK DETAIL - a concrete number or image that pierces ('In This Apartment, Your Toothbrush Arrives Before You Do'). "
               "Natural, grammatical English (no 'What Happens If Light Walked'), 5-10 words, 'you/your' where it fits, a concrete number or image, "
               "no clickbait words (shocking, insane, you won't believe). Lead with the WEIRDEST, most jarring angle you can defend: a plain promise statement "
               "('What Would Happen If...', 'Here's Why...') is the LAST resort, never the first title. Every claim must be one the video puts on trial and answers "
               "(true OR false) - never a promise the video does not keep (YouTube treats misleading titles as spam, and viewers who feel tricked leave in seconds).")

def hook_shape_brief(recent=()):
    """Text for the packager / writer: pick ONE shape, never the last two used; a statistic needs its source."""
    allowed = [k for k in HOOK_SHAPES if k not in list(recent)[-2:]]
    return ("HOOK SHAPE: open with ONE of " + "; ".join(HOOK_SHAPES[k] for k in allowed) + ". Name it in the JSON as \"hook_shape\" (" + "|".join(allowed) +
            "). A Statistic must name its source in the same line.")

def _words(t): return {w for w in re.findall(r"[a-z0-9']+", str(t or "").lower()) if len(w) > 2}

def coherent(title, thumb):
    """Pair coherence: the thumbnail words ADD to the title (at most one shared word) and are 1-4 words."""
    tw = str(thumb or "").split()
    return 1 <= len(tw) <= 4 and len(_words(title) & _words(thumb)) <= 1

def variants(pkg, spine=None):
    """Up to PKG_VARIANTS (title, thumb_text) pairs: A = the chosen package, B = its rescue title, C = the best other candidate that passes the title linter
    and the pair-coherence check. Never the source title of an outlier (demand) premise."""
    from whatifs import growth as GR
    spine = spine or {}; n = max(1, min(3, S("PKG_VARIANTS", int)))
    src = str((spine.get("show_plan") or {}).get("demand_evidence", {}).get("title") or "")
    cands = [(pkg.get("title"), pkg.get("thumb_text"))]
    cands += [(pkg.get("title_b"), pkg.get("thumb_text_b") or pkg.get("thumb_text"))]
    for t in (pkg.get("titles") or []) + (spine.get("title_candidates") or []):
        cands.append((t, pkg.get("thumb_text_c") or pkg.get("thumb_text")))
    from whatifs import v91 as V91
    if V91.on("TITLE_SHOCK_ON"):                                      # v9.2: natural English first, then the strongest scroll-stopper leads (A)
        order = {t: i for i, t in enumerate(rank_titles([c[0] for c in cands]))}
        cands = sorted(cands, key=lambda c: order.get(c[0], 99))
    out, seen = [], set()
    for t, th in cands:
        t = str(t or "").strip(); th = str(th or "").strip()
        if not t or t.lower() in seen or GR.title_issues(t, th): continue
        if V91.on("TITLE_SHOCK_ON") and natural_issues(t): continue         # v9.2: never a clunky title
        if src and len(_words(t) & _words(src)) / max(1, len(_words(t))) > 0.5: continue
        if not coherent(t, th): th = " ".join(GR.thumb_words(th or t, 3).split()[:3]) if hasattr(GR, "thumb_words") else th
        if not coherent(t, th): continue
        seen.add(t.lower()); out.append({"key": "ABC"[len(out)], "title": t, "thumb_text": th})
        if len(out) >= n: break
    return out or [{"key": "A", "title": str(pkg.get("title") or ""), "thumb_text": str(pkg.get("thumb_text") or "")}]

def approval_due():
    """True while fewer than THUMB_APPROVAL_FIRST_N videos have been scheduled."""
    eps = [e for e in store().rows("Episodes") if e.get("yt_id")]
    return len(eps) < S("THUMB_APPROVAL_FIRST_N", int)

def pick_link(ep, key):
    from urllib.parse import quote
    repo = env("GH_REPO")
    return f"https://github.com/{repo}/issues/new?title={quote(f'PICK {ep} {key}')}&body={quote('Press Submit new issue. The robot applies your pick.')}" if repo else ""

def record(ep, vid, vs, thumbs):
    """Store the variants with the episode (Packaging_Tests rows, status READY) and, while approvals are due, email the owner ONE message with one-click picks.
    The video is already uploaded with A, so nothing waits on the owner; a pick arriving after THUMB_APPROVAL_HOURS is ignored."""
    rows = [{"episode_id": ep, "yt_id": vid, "variant": v["key"], "title": v["title"], "thumb_text": v["thumb_text"], "thumb_file": thumbs.get(v["key"], ""),
             "status": "LIVE" if v["key"] == "A" else "READY", "window_start": "", "window_end": "", "views_start": "", "views_end": "", "views_per_hour": "",
             "ctr": "", "picked_by": "", "created": iso()} for v in vs]
    store().append("Packaging_Tests", rows)
    if approval_due() and len(vs) > 1 and S("THUMB_APPROVAL_ON", bool):
        from whatifs import publish as PUB
        li = "".join(f"<li><b>{v['key']}</b>: {v['title']} — thumbnail text “{v['thumb_text']}” <a href='{pick_link(ep, v['key'])}'>Pick {v['key']}</a></li>" for v in vs)
        try: PUB.email(f"Pick the title + thumbnail ({ep})", f"<p>The video is scheduled with A. Pick another within {S('THUMB_APPROVAL_HOURS')} hours and it is "
                       f"switched before release; no pick = A stays and the pairs are tested after release.</p><ul>{li}</ul>")
        except Exception as e: log(f"packaging pick email not sent: {str(e)[:120]}", "WARN", ep)
    return rows

def apply_pick(title):
    """'PICK EP<id> B' from the owner's one-click issue. Applied only inside THUMB_APPROVAL_HOURS of the variants' creation and before release."""
    from whatifs import publish as PUB
    m = re.match(r"^PICK (EP\d{6,14}) ([ABC])$", str(title or "").strip())
    if not m: raise SystemExit("usage: python -m whatifs.cli pkgpick 'PICK EP<id> B'")
    ep, key = m.groups(); st = store()
    rows = [r for r in st.rows("Packaging_Tests") if r.get("episode_id") == ep]
    row = next((r for r in rows if r.get("variant") == key), None)
    if not row: return f"no variant {key} for {ep}"
    t0 = parse_iso(row.get("created"))
    if not t0 or (now_utc() - t0).total_seconds() > S("THUMB_APPROVAL_HOURS", float) * 3600: return "too late: the top variant stays (the test will compare them)"
    _switch(row)
    for r in rows: st.update_where("Packaging_Tests", {"episode_id": ep, "variant": r["variant"]}, {"status": "LIVE" if r["variant"] == key else "READY",
                                                                                                      "picked_by": "owner" if r["variant"] == key else r.get("picked_by", "")})
    return f"{ep}: variant {key} applied"

def _switch(row):
    from whatifs import publish as PUB
    import os, tempfile
    PUB.yt_set_title(row["yt_id"], row["title"])
    tf = str(row.get("thumb_file") or "")
    if tf:
        try:
            if tf.startswith("drive:"):
                p = os.path.join(tempfile.mkdtemp(), "thumb.jpg"); PUB.drive_download(tf[6:], p); tf = p
            PUB.yt_thumbnail(row["yt_id"], tf)
        except Exception as e: log(f"thumbnail switch failed: {str(e)[:120]}", "WARN", row.get("episode_id"))

def rotate_tick():
    """Called by every tick: inside PKG_ROTATE_HOURS after release, each variant gets an equal window; views per hour (and CTR if available) per window
    are recorded; at the end the best one is put back for good. Bounded: one switch per window, at most 3 windows per video."""
    if not S("PKG_ROTATE_ON", bool): return 0
    from whatifs import publish as PUB
    st = store(); n = 0; hours = S("PKG_ROTATE_HOURS", float)
    by = {}
    for r in st.rows("Packaging_Tests"): by.setdefault(r.get("episode_id"), []).append(r)
    eps = {e["episode_id"]: e for e in st.rows("Episodes") if e.get("yt_id")}
    for ep, rows in by.items():
        e = eps.get(ep); rel = parse_iso((e or {}).get("slot_et"))
        if not e or not rel or len(rows) < 2 or any(r.get("status") == "WINNER" for r in rows) or any(r.get("picked_by") == "owner" for r in rows): continue
        age = (now_utc() - rel).total_seconds() / 3600
        if age < 0: continue
        win = hours / len(rows); k = min(len(rows) - 1, int(age // win)) if age < hours else len(rows)
        live = next((r for r in rows if r.get("status") == "LIVE"), rows[0])
        try: v_now = float(PUB.yt_views(e["yt_id"]) or 0)
        except Exception: v_now = None
        def close(r):
            t1 = parse_iso(r.get("window_start")) or rel; h = max(0.1, (now_utc() - t1).total_seconds() / 3600)
            vph = (v_now - float(r.get("views_start") or 0)) / h if v_now is not None and r.get("views_start") not in ("", None) else ""
            st.update_where("Packaging_Tests", {"episode_id": ep, "variant": r["variant"]}, {"window_end": iso(), "views_end": v_now if v_now is not None else "", "views_per_hour": vph,
                                                                                          "status": "TESTED"})
        if k >= len(rows):                                            # the test is over: the best window wins
            if live.get("status") == "LIVE": close(live)
            done = [r for r in st.rows("Packaging_Tests") if r.get("episode_id") == ep]
            best = max(done, key=lambda r: float(r.get("views_per_hour") or 0)); _switch(best)
            st.update_where("Packaging_Tests", {"episode_id": ep, "variant": best["variant"]}, {"status": "WINNER"}); n += 1
            log(f"packaging test {ep}: variant {best['variant']} wins ({best.get('views_per_hour')} views/hour)", episode=ep); continue
        want = rows[k]
        if live.get("variant") != want["variant"] or not live.get("window_start"):
            if live.get("window_start"): close(live)
            if live.get("variant") != want["variant"]: _switch(want)
            st.update_where("Packaging_Tests", {"episode_id": ep, "variant": want["variant"]}, {"status": "LIVE", "window_start": iso(), "views_start": v_now if v_now is not None else ""})
            n += 1
    return n


# ---------------------------------------------------------------- v9.2: natural English + the "stop-scrolling" score (K109)
_PAST = r"(?:walked|moved|stopped|happened|became|turned|went|froze|melted|vanished|disappeared|doubled|slowed|flipped)"
STALE = [r"^everyone is wrong about", r"\byou won'?t believe\b", r"\bshocking\b", r"\bgone wrong\b", r"\bmust see\b", r"\binsane\b"]

def natural_issues(title):
    """Odd English a viewer trips over (code only): present 'What Happens If' + past verb, 'If X Walked' after a present clause, a doubled 'what if',
    a dangling 'if' / 'about', clickbait clichés. Empty list = reads naturally."""
    t = " " + str(title or "").strip().lower() + " "; out = []
    if re.search(r"\bwhat happens if\b[^?]*\b" + _PAST + r"\b", t): out.append("tense clash: 'What Happens If ... <past verb>' (use 'What Would Happen If' or the present tense)")
    if re.search(r"\b(is|are|happens)\b[^?]*\bif\b[^?]*\b" + _PAST + r"\b", t) and "would" not in t: out.append("tense clash: a present clause with a past 'if' clause")
    if t.count("what if") > 1: out.append("'what if' twice")
    if re.search(r"\b(if|about|of|the|a|and|to)\s*[?!.]?\s*$", t): out.append("ends on a dangling word")
    for rx in STALE:
        if re.search(rx, t): out.append("cliche opener / clickbait word"); break
    return out

def shock_score(title):
    """0-10: how hard a title stops a scroll, by its SHAPE (code only): a bold claim, a question that dares the viewer, a concrete number or unit,
    'you / your', a contradiction or an impossible pairing, short and punchy. Accuracy is the writers' job (the video answers every claim)."""
    t = str(title or ""); tl = t.lower(); w = re.findall(r"[A-Za-z0-9.']+", t); sc = 0.0
    if re.search(r"\b(is|are|was|will|can|just|already|never|always|every|nobody|no one)\b", tl) and "?" not in t[:-1]: sc += 1.5      # a bold statement
    if t.rstrip().endswith("?"): sc += 1.5
    if re.search(r"\?\s*\S", t) or re.search(r"[.,:\-–—]\s+(and|but|so)?\s*\w+.*\?$", t): sc += 1.0                    # claim + question (two beats)
    if re.search(r"\d", t): sc += 1.5
    if re.search(r"\b(you|your|you're)\b", tl): sc += 1.0
    if re.search(r"\b(dead|alive|late|backward|backwards|frozen|wrong|impossible|faster than|slower than|disappear|vanish|eat|swallow|breathe|scream)\b", tl): sc += 1.5
    if re.search(r"\b(but|actually|already|still|never)\b", tl): sc += 0.5
    if 5 <= len(w) <= 10: sc += 1.0
    if re.match(r"\s*(what would happen if|what happens if|here'?s why|why does|how does|the science of)\b", tl): sc -= 1.5      # v9.2: a plain promise opener ranks last
    if natural_issues(t): sc -= 3.0
    return round(max(0.0, min(10.0, sc)), 2)

def rank_titles(titles):
    """Natural first, then the highest stop-scrolling score; ties keep the packager's order."""
    return sorted([t for t in titles if str(t or "").strip()], key=lambda t: (bool(natural_issues(t)), -shock_score(t)))
