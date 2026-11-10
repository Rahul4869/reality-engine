"""Audience and topic research before topic selection, with observed evidence kept apart from interpretation. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import datetime as dt, html, json, os, re, time
import xml.etree.ElementTree as ET
import requests
from whatifs.core import S, log, iso, now_utc, WORK, FAKE, env, scrub, safe_append, safe_rows

SCHEMA = 1
SOURCES = ("youtube", "trends", "qa")
AI_LABEL = "AI-generated interpretation - not observed evidence"
_CLAIM_RE = {"trending": re.compile(r"\btrending\b", re.I), "viral": re.compile(r"\bviral\b", re.I),
             "high intent": re.compile(r"\bhigh[- ]intent\b", re.I)}

_get = requests.get      # the single place network reads go through (tests replace it)
_sleep = time.sleep
_clock = time.monotonic
_deadline = {"t": None}  # set by collect(); when it passes, remaining requests are skipped (RESEARCH_BUDGET_SEC)

def _clean(text, n=200):
    t = html.unescape(str(text or ""))
    t = t.replace("@@", " ")                                   # template markers must never come from the internet
    t = re.sub(r"[\x00-\x1f\x7f]", " ", t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", t)      # no personal data in titles
    t = re.sub(r"(?<!\w)@\w{2,}", "[handle]", t)
    return re.sub(r"\s+", " ", t).strip()[:n]

def _words(t): return set(re.findall(r"[a-z]{4,}", str(t).lower()))
def _overlap(a, b): return bool(_words(a) & _words(b))

def _http(url, params=None, headers=None, kind="json"):
    """GET with timeout + retries. 429/5xx and network errors are retried with a short backoff; other 4xx fail at once."""
    tries = max(1, S("RESEARCH_RETRIES", int)); timeout = S("RESEARCH_TIMEOUT_SEC", float); last = None
    for a in range(tries):
        if _deadline["t"] is not None and _clock() > _deadline["t"]:
            raise RuntimeError("research time budget used up (RESEARCH_BUDGET_SEC)")
        try:
            r = _get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                last = RuntimeError(f"HTTP {r.status_code}"); _sleep(min(10, 2 * (a + 1))); continue
            if r.status_code >= 400: raise RuntimeError(f"HTTP {r.status_code}")
            return r.json() if kind == "json" else r.text
        except requests.RequestException as e:
            last = e; _sleep(min(10, 2 * (a + 1)))
    raise RuntimeError(scrub(f"{type(last).__name__}: {last}")[:200])

# ---------------- collectors: each returns (signals, status) and never raises ----------------
def _ok(name, signals, detail=""): return signals, {"source": name, "status": "ok" if signals else "empty", "count": len(signals), "detail": detail}
def _fail(name, e): return [], {"source": name, "status": "unavailable", "count": 0, "detail": scrub(str(e))[:200]}

def collect_youtube(now=None):
    """Public YouTube search + US science chart through the project's own YouTube key. Search costs 100 quota units per query."""
    name = "youtube"; now = now or now_utc(); sigs = []
    if not env("G_REFRESH"): return [], {"source": name, "status": "unavailable", "count": 0, "detail": "no Google sign-in configured"}
    try:
        from whatifs.core import gheaders
        H = gheaders()
        base = "https://www.googleapis.com/youtube/v3/"
        after = (now - dt.timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        queries = [q.strip() for q in S("RESEARCH_YT_QUERIES").split("|") if q.strip()][:4]
        for q in queries:
            r = _http(base + "search", {"part": "snippet", "q": q, "type": "video", "order": "viewCount", "publishedAfter": after,
                                        "maxResults": 8, "relevanceLanguage": "en", "regionCode": "US"}, H)
            ids = ",".join(i["id"]["videoId"] for i in r.get("items", []) if i.get("id", {}).get("videoId"))
            if not ids: continue
            v = _http(base + "videos", {"part": "snippet,statistics", "id": ids}, H)
            for x in v.get("items", []):
                sigs.append({"kind": "youtube_search", "query": q, "title": _clean(x["snippet"]["title"]), "url": "https://www.youtube.com/watch?v=" + x["id"],
                             "observed_at": iso(now), "published": x["snippet"].get("publishedAt", "")[:10],
                             "metrics": {"views": int(x.get("statistics", {}).get("viewCount", 0) or 0), "window_days": 10}})
        ch = _http(base + "videos", {"part": "snippet,statistics", "chart": "mostPopular", "regionCode": "US", "videoCategoryId": "28", "maxResults": 12}, H)
        for n, x in enumerate(ch.get("items", []), 1):
            sigs.append({"kind": "youtube_chart", "query": "US Science & Technology chart", "title": _clean(x["snippet"]["title"]),
                         "url": "https://www.youtube.com/watch?v=" + x["id"], "observed_at": iso(now), "published": x["snippet"].get("publishedAt", "")[:10],
                         "metrics": {"chart_rank": n, "views": int(x.get("statistics", {}).get("viewCount", 0) or 0)}})
        return _ok(name, sigs)
    except Exception as e:
        out, st = _fail(name, e); st["count"] = len(sigs); return sigs, (st if not sigs else dict(st, status="partial"))

def collect_trends(now=None):
    """Google Trends 'trending now' public RSS for the US. General (not science-only) and has no official API: treat as context."""
    name = "trends"; now = now or now_utc()
    try:
        xml = _http("https://trends.google.com/trending/rss", {"geo": "US"}, kind="text")
        root = ET.fromstring(xml); sigs = []
        for n, it in enumerate(root.iter("item"), 1):
            t = _clean((it.findtext("title") or ""))
            if not t: continue
            traffic = it.findtext("{https://trends.google.com/trending/rss}approx_traffic") or ""
            sigs.append({"kind": "google_trends", "query": "US trending now (all topics)", "title": t,
                         "url": "https://trends.google.com/trending?geo=US", "observed_at": iso(now), "published": (it.findtext("pubDate") or "")[:25],
                         "metrics": {"list_rank": n, "approx_traffic": _clean(traffic, 20)}})
            if n >= 20: break
        return _ok(name, sigs, "general US list, not limited to science")
    except Exception as e: return _fail(name, e)

def collect_qa(now=None):
    """Public question titles from Stack Exchange science sites (public API, no login, attribution = link). Author fields are ignored."""
    name = "qa"; now = now or now_utc(); sigs = []; errs = []
    since = int((now - dt.timedelta(days=90)).timestamp())
    for site in [s.strip() for s in S("RESEARCH_QA_SITES").split(",") if s.strip()][:6]:
        try:
            r = _http("https://api.stackexchange.com/2.3/questions", {"site": site, "order": "desc", "sort": "votes", "fromdate": since, "pagesize": 8})
            for x in r.get("items", []):
                sigs.append({"kind": "qa_question", "query": f"{site}.stackexchange.com, top-voted last 90 days", "title": _clean(x.get("title")),
                             "url": x.get("link", ""), "observed_at": iso(now),
                             "published": dt.datetime.fromtimestamp(x.get("creation_date", 0), dt.timezone.utc).strftime("%Y-%m-%d") if x.get("creation_date") else "",
                             "metrics": {"score": int(x.get("score", 0)), "views": int(x.get("view_count", 0)), "answers": int(x.get("answer_count", 0))}})
        except Exception as e: errs.append(f"{site}: {scrub(str(e))[:80]}")
    st = {"source": name, "status": "ok" if sigs and not errs else ("partial" if sigs else "unavailable"), "count": len(sigs), "detail": "; ".join(errs)[:300]}
    return sigs, st

COLLECTORS = {"youtube": collect_youtube, "trends": collect_trends, "qa": collect_qa}

def _fake_signals(name, now):
    """Rehearsal only (WI_FAKE=1): fixed, clearly fake signals. Never touches the network."""
    base = {"observed_at": iso(now), "published": now.strftime("%Y-%m-%d")}
    if name == "youtube":
        return [dict(base, kind="youtube_search", query="what if", title="What Happens If You Never Slept Again", url="https://example.invalid/yt1", metrics={"views": 120000, "window_days": 10})]
    if name == "trends":
        return [dict(base, kind="google_trends", query="US trending now (all topics)", title="pillow fight championship", url="https://example.invalid/trends", metrics={"list_rank": 1, "approx_traffic": "200+"})]
    return [dict(base, kind="qa_question", query="physics.stackexchange.com, top-voted last 90 days", title="What would happen if every pillow on Earth floated upward at once?",
                 url="https://example.invalid/qa1", metrics={"score": 40, "views": 9000, "answers": 3})]

def collect(now=None):
    """Run the enabled collectors. A failing one is recorded and skipped. Returns (signals with ids S1.., source_status list)."""
    want = [s.strip().lower() for s in S("RESEARCH_SOURCES").split(",") if s.strip()]
    sigs, stat = [], []
    _deadline["t"] = _clock() + max(1.0, S("RESEARCH_BUDGET_SEC", float))
    try: return _collect(now, want, sigs, stat)
    finally: _deadline["t"] = None

def _collect(now, want, sigs, stat):
    for name in SOURCES:
        if name not in want: stat.append({"source": name, "status": "skipped", "count": 0, "detail": "disabled in RESEARCH_SOURCES"}); continue
        try:
            if FAKE: s, st = _ok(name, _fake_signals(name, now or now_utc()), "rehearsal data")
            else: s, st = COLLECTORS[name](now)
        except Exception as e: s, st = _fail(name, e)
        sigs += s; stat.append(st)
    for i, s in enumerate(sigs, 1): s["id"] = f"S{i}"
    return sigs, stat

# ---------------- evidence rules (code decides, not the AI) ----------------
def _metric_text(s):
    m = s.get("metrics", {}); bits = []
    if "views" in m: bits.append(f"{m['views']:,} views")
    if "score" in m: bits.append(f"score {m['score']}")
    if m.get("answers") is not None and s["kind"] == "qa_question": bits.append(f"{m['answers']} answers")
    if "chart_rank" in m: bits.append(f"chart #{m['chart_rank']}")
    if "list_rank" in m: bits.append(f"trends list #{m['list_rank']}" + (f" ({m['approx_traffic']} searches)" if m.get("approx_traffic") else ""))
    return ", ".join(bits)

def supported_claims(premise, cited):
    """Which of 'trending' / 'viral' a candidate may use. 'high intent' is never supported: we have no search-volume data."""
    out = set(); thr = S("RESEARCH_VIRAL_VIEWS", float)
    for s in cited:
        direct = _overlap(premise, s.get("title", ""))
        if s["kind"] in ("google_trends", "youtube_chart") and direct: out.add("trending")
        if s["kind"] == "youtube_search" and direct and s["metrics"].get("views", 0) >= thr: out.add("viral")
    return out

def _strip_unsupported(text, allowed):
    removed = []
    for k, rx in _CLAIM_RE.items():
        if k in allowed: continue
        if rx.search(text or ""): removed.append(k); text = rx.sub("[claim removed: no supporting evidence]", text)
    return text, removed

def _banned_hit(t, banned): t = t.lower(); return any(b.lower() in t for b in banned if b)

def build_candidates(ai, sigs, banned=(), recent=(), limit=5):
    """Validate the AI's candidate list against the real signals. Unknown signal ids are dropped; unsupported claims are removed."""
    byid = {s["id"]: s for s in sigs}; out = []
    for c in (ai or {}).get("candidates", []) if isinstance(ai, dict) else []:
        prem = _clean(c.get("premise"), 200)
        if not prem or _banned_hit(prem, banned): continue
        if any(len(_words(prem) & _words(r)) / max(1, len(_words(prem) | _words(r))) > 0.5 for r in recent if r): continue
        ids = [i for i in (c.get("evidence") or []) if i in byid]; cited = [byid[i] for i in ids]
        allowed = supported_claims(prem, cited); removed = []
        interp = {}
        for k in ("audience_need", "click_emotion", "channel_fit"):
            txt, rm = _strip_unsupported(_clean(c.get(k), 400), allowed); interp[k] = txt; removed += rm
        prem2, rm = _strip_unsupported(prem, allowed); removed += rm
        direct = [s for s in cited if _overlap(prem, s["title"])]
        out.append({"premise": prem2, "family": _clean(c.get("family"), 30),
                    "evidence_strength": "direct" if direct else ("contextual" if cited else "none"),
                    "observed": [{"id": s["id"], "source": s["kind"], "title": s["title"], "url": s["url"], "observed_at": s["observed_at"],
                                  "signal": _metric_text(s), "query": s.get("query", "")} for s in cited],
                    "ai_interpretation": dict(interp, label=AI_LABEL),
                    "supported_claims": sorted(allowed), "claims_removed": sorted(set(removed)),
                    "note": "" if cited else "No observed signal backs this idea; it is an AI suggestion only."})
        if len(out) >= limit: break
    rank = {"direct": 0, "contextual": 1, "none": 2}
    out.sort(key=lambda c: rank[c["evidence_strength"]])
    for i, c in enumerate(out, 1): c["rank"] = i
    return out

def signal_only_candidates(sigs, limit=5):
    """No AI available: list the strongest real audience questions as-is. Nothing is interpreted or invented."""
    qa = sorted([s for s in sigs if s["kind"] == "qa_question"], key=lambda s: -s["metrics"].get("views", 0))[:limit]
    return [{"rank": i, "premise": "(raw audience question) " + s["title"], "family": "", "evidence_strength": "direct",
             "observed": [{"id": s["id"], "source": s["kind"], "title": s["title"], "url": s["url"], "observed_at": s["observed_at"],
                           "signal": _metric_text(s), "query": s.get("query", "")}],
             "ai_interpretation": {"audience_need": "not assessed: AI step unavailable", "click_emotion": "not assessed: AI step unavailable",
                                   "channel_fit": "not assessed: AI step unavailable", "label": AI_LABEL},
             "supported_claims": [], "claims_removed": [], "note": "AI interpretation unavailable; raw observed question only."} for i, s in enumerate(qa, 1)]

# ---------------- the brief ----------------
def run_research(now=None, ask_fn=None):
    """Collect -> (optional) AI interpretation -> validated brief dict. Never raises."""
    now = now or now_utc()
    brief = {"schema": SCHEMA, "brief_id": "RB" + now.strftime("%Y%m%d%H%M"), "date": now.strftime("%Y-%m-%d"), "created": iso(now),
             "completeness": "none", "notes": [], "sources": [], "signals": [], "candidates": [], "requested_candidates": 5}
    try:
        sigs, stat = collect(now)
        brief["sources"] = stat; brief["signals"] = sigs
        live = [s for s in stat if s["status"] in ("ok", "partial")]; enabled = [s for s in stat if s["status"] != "skipped"]
        brief["completeness"] = "none" if not sigs else ("complete" if len(live) == len(enabled) and all(s["status"] == "ok" for s in live) else "partial")
        for s in stat:
            if s["status"] in ("unavailable", "empty", "partial"): brief["notes"].append(f"Source '{s['source']}' {s['status']}: {s['detail'] or 'no detail'}")
        if not sigs:
            brief["notes"].append("RESEARCH UNAVAILABLE: no public signals could be collected. No topic candidates were produced. Topic selection continues without research.")
            return brief
        banned = [r.get("phrase", "") for r in safe_rows("Banned")]
        recent = [(e.get("title") or e.get("premise") or "") for e in safe_rows("Episodes")[-25:]]
        from whatifs.data import FAMILIES
        ai = None
        try:
            from whatifs import prompts as P
            from whatifs.models import ask
            ask_fn = ask_fn or ask
            slim = [{"id": s["id"], "kind": s["kind"], "title": s["title"], "signal": _metric_text(s), "date": s.get("published", "")} for s in sigs][:70]
            ai = ask_fn("flash", P.fill(P.RESEARCH, families=json.dumps({k: v[0] for k, v in FAMILIES.items()}), banned=banned[:60], recent=recent),
                        "Return the candidate topics now. SIGNALS (JSON): " + json.dumps(slim, ensure_ascii=False), temperature=0.4, fake_key="research_synth")
        except Exception as e:
            brief["notes"].append("AI interpretation step failed (" + scrub(str(e))[:120] + "); only raw observed questions are listed.")
        cands = build_candidates(ai, sigs, banned, recent) if ai else []
        if not cands:
            cands = signal_only_candidates(sigs)
            if ai: brief["notes"].append("The AI returned no usable candidates; raw observed questions are listed instead.")
        brief["candidates"] = cands
        if len(cands) < 5: brief["notes"].append(f"Only {len(cands)} of 5 requested candidates could be backed by the collected signals.")
        if any(c["evidence_strength"] == "none" for c in cands): brief["notes"].append("Candidates marked evidence 'none' are AI ideas with no observed signal behind them.")
        if brief["completeness"] != "complete": brief["notes"].append("Research is INCOMPLETE: treat it as partial input only.")
    except Exception as e:
        brief["notes"].append("Research stage crashed safely: " + scrub(str(e))[:160]); brief["completeness"] = "none" if not brief["signals"] else "partial"
    return brief

# ---------------- storage + rendering ----------------
def brief_rows(b):
    """One row per source / signal / candidate / note, so the dated brief is readable in the Sheet."""
    base = {"brief_id": b["brief_id"], "brief_date": b["date"]}; rows = []
    rows.append(dict(base, kind="status", ref="completeness", item=b["completeness"], detail=f"{len(b['signals'])} signals", evidence_type="system", source_url="", observed_at=b["created"]))
    for s in b["sources"]: rows.append(dict(base, kind="source", ref=s["source"], item=s["status"], detail=f"{s['count']} signals. {s['detail']}", evidence_type="system", source_url="", observed_at=b["created"]))
    for s in b["signals"]: rows.append(dict(base, kind="signal", ref=s["id"], item=s["title"], detail=f"{s['kind']} | {s.get('query','')} | {_metric_text(s)} | published {s.get('published','')}",
                                            evidence_type="observed", source_url=s["url"], observed_at=s["observed_at"]))
    for c in b["candidates"]:
        ev = "; ".join(f"{o['id']}: {o['signal']}" for o in c["observed"])
        rows.append(dict(base, kind="candidate", ref=f"C{c['rank']}", item=c["premise"],
                         detail=json.dumps({"evidence_strength": c["evidence_strength"], "signals": ev, "claims": c["supported_claims"], "removed": c["claims_removed"],
                                            "need": c["ai_interpretation"]["audience_need"], "emotion": c["ai_interpretation"]["click_emotion"], "fit": c["ai_interpretation"]["channel_fit"], "note": c["note"]}, ensure_ascii=False),
                         evidence_type="ai_interpretation", source_url=(c["observed"][0]["url"] if c["observed"] else ""), observed_at=b["created"]))
    for n in b["notes"]: rows.append(dict(base, kind="note", ref="", item=n, detail="", evidence_type="system", source_url="", observed_at=b["created"]))
    return rows

def to_markdown(b):
    L = [f"# Research brief {b['brief_id']} ({b['date']})", f"**Completeness: {b['completeness'].upper()}** - {len(b['signals'])} observed signals.", ""]
    if b["notes"]: L += ["## Notes and gaps"] + [f"- {n}" for n in b["notes"]] + [""]
    L += ["## Sources"] + [f"- {s['source']}: {s['status']} ({s['count']}) {s['detail']}" for s in b["sources"]] + [""]
    L += ["## Topic candidates", "Observed evidence is quoted from public sources. The audience need, click emotion and channel fit are AI interpretation.", ""]
    for c in b["candidates"]:
        L += [f"### {c['rank']}. {c['premise']}", f"- Evidence strength: **{c['evidence_strength']}**" + (f" - supported claims: {', '.join(c['supported_claims'])}" if c["supported_claims"] else ""),
              f"- Audience need (AI interpretation): {c['ai_interpretation']['audience_need']}",
              f"- Click emotion (AI interpretation): {c['ai_interpretation']['click_emotion']}",
              f"- Channel fit (AI interpretation): {c['ai_interpretation']['channel_fit']}"]
        if c["claims_removed"]: L.append(f"- Removed unsupported wording: {', '.join(c['claims_removed'])}")
        if c["note"]: L.append(f"- Note: {c['note']}")
        L.append("- Observed evidence:")
        L += [f"  - [{o['id']}] {o['title']} - {o['signal']} - {o['source']} - seen {o['observed_at'][:10]} - {o['url']}" for o in c["observed"]] or ["  - none"]
        L.append("")
    L += ["## All observed signals"] + [f"- [{s['id']}] ({s['kind']}) {s['title']} - {_metric_text(s)} - {s['url']} - seen {s['observed_at'][:10]}" for s in b["signals"]]
    return "\n".join(L) + "\n"

def save_brief(b, out_dir=None):
    """Sheet tab Research_Brief + dated .json/.md files in the work folder. Returns file paths. Never raises."""
    safe_append("Research_Brief", brief_rows(b)); paths = []
    try:
        out_dir = out_dir or WORK; os.makedirs(out_dir, exist_ok=True)
        for ext, txt in (("json", json.dumps(b, indent=1, ensure_ascii=False)), ("md", to_markdown(b))):
            p = os.path.join(out_dir, f"research_{b['date']}.{ext}"); open(p, "w", encoding="utf-8").write(txt); paths.append(p)
    except Exception as e: log(f"could not write research files: {scrub(e)}", "WARN")
    if paths and not FAKE and S("REVIEW_TO_DRIVE", bool):      # private copy; the Sheet tab stays the main record
        try:
            from whatifs import publish as PUB
            PUB.drive_upload(paths[-1], f"research_{b['date']}.md", public=False)
        except Exception as e: log(f"research brief Drive copy skipped: {scrub(e)}", "WARN")
    return paths

def latest_rows(max_age_days=None):
    rows = safe_rows("Research_Brief")
    if not rows: return []
    ids = sorted({r.get("brief_id", "") for r in rows if r.get("brief_id")})
    if not ids: return []
    last = ids[-1]; mine = [r for r in rows if r.get("brief_id") == last]
    if max_age_days is not None:
        d = mine[0].get("brief_date", "")
        try:
            age = (now_utc().date() - dt.datetime.strptime(d, "%Y-%m-%d").date()).days
            if age > max_age_days: return []
        except Exception: return []
    return mine

def text_for_room(rows, limit=4500):
    """Compact prompt text. Observed signals and AI interpretation stay in separate, labelled blocks."""
    if not rows: return "RESEARCH NOT AVAILABLE: no audience evidence this time. Do not invent any."
    rows = [dict(r, item=str(r.get("item", "")).replace("@@", " ")) for r in rows]
    status = next((r["item"] for r in rows if r.get("kind") == "status"), "unknown")
    head = f"Brief {rows[0].get('brief_id')} dated {rows[0].get('brief_date')}. Completeness: {status}."
    notes = [r["item"] for r in rows if r.get("kind") == "note"]
    sig = []
    for r in rows:
        if r.get("kind") != "signal": continue
        parts = str(r.get("detail", "")).split(" | ")
        sig.append(f"[{r['ref']}] {r['item']} ({parts[2] if len(parts) > 2 else ''}) {r.get('source_url', '')}")
    cand = []
    for r in rows:
        if r.get("kind") != "candidate": continue
        try: d = json.loads(r["detail"])
        except Exception: d = {}
        cand.append(f"{r['ref']}: {r['item']} | evidence: {d.get('evidence_strength')} ({d.get('signals','')}) | need: {d.get('need','')} | emotion: {d.get('emotion','')}")
    t = (head + ("\nGAPS: " + " ".join(notes) if notes else "") + "\nOBSERVED SIGNALS (facts, with sources):\n" + "\n".join(sig[:35]) +
         "\nAI-SUGGESTED CANDIDATES (interpretation, not evidence):\n" + "\n".join(cand))
    return t[:limit]

def room_research(episode=None, allow_run=True):
    """Called by the writers' room before topic selection. Returns (prompt_text, brief_id). Reuses a fresh brief, else collects a new one. Never raises."""
    if not S("RESEARCH_ON", bool): return "RESEARCH NOT AVAILABLE: switched off (RESEARCH_ON = FALSE). Do not invent any.", ""
    try:
        rows = latest_rows(S("RESEARCH_MAX_AGE_DAYS", int))
        if rows: return text_for_room(rows), rows[0].get("brief_id", "")
        if not allow_run:                                                     # v9.2: no new brief inside a preview / production; the newest one, any age
            old = latest_rows(3650)
            if old: log("research brief is older than RESEARCH_MAX_AGE_DAYS - the newest one is used; the learning job makes a new one", "WARN", episode)
            return (text_for_room(old), old[0].get("brief_id", "")) if old else ("RESEARCH NOT AVAILABLE: no brief yet (the learning job makes one). Do not invent any.", "")
        b = run_research(); save_brief(b)
        log(f"research brief {b['brief_id']}: {b['completeness']}, {len(b['signals'])} signals, {len(b['candidates'])} candidates", episode=episode)
        return text_for_room(brief_rows(b)), b["brief_id"]
    except Exception as e:
        log(f"research skipped: {scrub(e)}", "WARN", episode)
        return "RESEARCH NOT AVAILABLE: the research step failed. Do not invent any evidence.", ""

def main():
    """python -m whatifs.cli research  - run the stage on its own and print where the brief went."""
    b = run_research(); save_brief(b)
    print(f"research {b['brief_id']} completeness={b['completeness']} signals={len(b['signals'])} candidates={len(b['candidates'])}")
    for n in b["notes"]: print("NOTE:", n)
    return b

