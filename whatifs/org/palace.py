"""Knowledge Palace: the one repository every department reads and writes - guarded items, life cycle, versions and bounded department playbooks. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import ast, glob, hashlib, json, math, os, re, shutil, tempfile
import datetime as dt
from whatifs import core
from whatifs import truth as TRU
from whatifs.core import S, log, store, iso, now_utc, parse_iso, scrub, set_setting, retry
from whatifs.org import DEPARTMENTS, STAGES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed")
TAB, VTAB, PTAB = "Palace_Items", "Palace_Versions", "Palace_Playbooks"

KINDS = ("takeaway", "technique", "strategy", "plan", "world_canon", "style_rule", "policy_rule", "tool_fact", "audience_insight", "failure_lesson", "owner_preference")
LIMIT_KINDS = ("policy_rule", "owner_preference", "failure_lesson")      # items that say "always / never": served first, never dropped silently
KEEP_KINDS = LIMIT_KINDS + ("world_canon",)                              # never displaced by a size cap (limits and the show's own history)
STATUSES = ("proposed", "accepted", "testing", "proven", "retired", "superseded", "expired")
SERVABLE = ("proven", "accepted", "testing")                             # the only statuses that may ever reach a prompt
ANY = "*"
ACTORS = ("owner", "council", "librarian", "clock", "build") + tuple(DEPARTMENTS)

# Who may create an item directly in a status (everything else enters as 'proposed' and waits for the Council).
START = {"proposed": ANY, "accepted": ("owner", "council", "build", "librarian"), "testing": ("council", "D10"), "proven": ("D10",)}

# The life cycle as DATA: (from, to) -> who may make the move. A pair that is not listed is illegal for everyone.
MOVES = {
    ("proposed", "accepted"): ("owner", "council"),
    ("proposed", "retired"): ("owner", "council"),
    ("proposed", "superseded"): ("owner", "council", "librarian", "build"),
    ("accepted", "testing"): ("owner", "council", "D10"),
    ("accepted", "proven"): ("D10",),
    ("accepted", "retired"): ("owner", "council", "D10"),
    ("accepted", "expired"): ("clock", "librarian"),
    ("accepted", "superseded"): ("owner", "council", "D10", "librarian", "build"),
    ("testing", "accepted"): ("council", "D10"),
    ("testing", "proven"): ("D10",),
    ("testing", "retired"): ("owner", "council", "D10"),
    ("testing", "expired"): ("clock", "librarian"),
    ("testing", "superseded"): ("owner", "council", "D10", "librarian", "build"),
    ("proven", "testing"): ("D10",),
    ("proven", "retired"): ("owner", "council", "D10"),
    ("proven", "expired"): ("clock", "librarian"),
    ("proven", "superseded"): ("owner", "council", "D10", "librarian", "build"),
    ("expired", "accepted"): ("owner", "council", "D10"),
    ("expired", "testing"): ("council", "D10"),
    ("expired", "proven"): ("D10",),
    ("expired", "retired"): ("owner", "council", "D10", "librarian"),
    ("expired", "superseded"): ("owner", "council", "D10", "librarian", "build"),
    ("retired", "proposed"): ANY,
    ("retired", "testing"): ("D10",),
}

# Trust is computed from the kind of evidence, never typed by whoever writes the item.
EVIDENCE = {"owner decision": 1.0, "own data": 0.9, "show record": 0.9, "measured": 0.8, "official": 0.8, "build record": 0.7, "practice": 0.6,
            "research digest": 0.5, "opinion": 0.3, "model": 0.2}
EVIDENCE_ALIAS = {"official guidance": "official", "measured-own": "own data", "owner": "owner decision"}

REVIEW_DAYS = {"takeaway": 180, "technique": 120, "strategy": 180, "plan": 45, "world_canon": 0, "style_rule": 180, "policy_rule": 90, "tool_fact": 60,
               "audience_insight": 120, "failure_lesson": 365, "owner_preference": 0}          # 0 = never (canon and the owner's words do not go stale by the clock)
KIND_CAPS = {"takeaway": 400, "technique": 300, "strategy": 80, "plan": 40, "world_canon": 600, "style_rule": 120, "policy_rule": 120, "tool_fact": 150,
             "audience_insight": 120, "failure_lesson": 200, "owner_preference": 150}
SUMMARY_MAX, INLINE_MAX, MIN_CAP, MAX_CAP = 400, 40000, 200, 6000
_RANK = {"testing": 0, "accepted": 1, "proven": 2}
_JSON_COLS = ("departments", "stages", "topic_tags", "evidence", "derived_from", "applied_in")
_GAMING_KINDS = ("technique", "strategy", "plan", "style_rule", "takeaway", "audience_insight", "tool_fact")
INJECT = re.compile(r"ignore (?:all |any |the )?(?:previous|prior|above) (?:instructions?|rules?|prompts?)|disregard (?:all |the )?(?:previous|prior|above|system)|"
                    r"you are now (?:a|an|the) |reveal (?:your|the) (?:system )?(?:prompt|instructions)", re.I)
HEADER = ("KNOWLEDGE PALACE - playbook for {dept} {name} (stage: {stage}).\n"
          "These lines are the organisation's own knowledge, stored as data. LIMIT lines always apply. Then prefer PROVEN over ACCEPTED over TESTING "
          "where they fit this job. Report the ids you used as applied_items.")
_STOP = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "has", "have", "not", "but", "its", "into", "than", "then", "when", "what", "every", "must", "never", "only"}

class PalaceError(ValueError):
    """A refused write or an illegal move; .problems lists every reason."""
    def __init__(self, problems):
        self.problems = [str(p) for p in problems]
        super().__init__("; ".join(self.problems))

# ------------------------------------------------------------------ small helpers
def _f(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d

def _list(v):
    if isinstance(v, (list, tuple)): return list(v)
    if isinstance(v, str) and v.strip():
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else [v]
        except Exception:
            return [x.strip() for x in v.split(",") if x.strip()]
    return []

def _json_setting(key):
    try:
        j = json.loads(S(key) or "{}")
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}

def item_id(key):
    """A stable id from a key (same key -> same id on every machine, so seeding and mirrors are idempotent)."""
    return "PI-" + hashlib.sha1(re.sub(r"\s+", " ", str(key or "")).strip().lower().encode("utf-8")).hexdigest()[:10].upper()

def est_tokens(text):
    """Deliberately high estimate (3.6 characters a token; the cost estimator elsewhere uses 4) so the playbook cap holds on a real tokenizer."""
    return int(math.ceil(len(str(text or "")) / 3.6))

def review_days(kind):
    return int(_f(_json_setting("PALACE_REVIEW_DAYS").get(kind), REVIEW_DAYS.get(kind, 120)))

def kind_caps():
    over = _json_setting("PALACE_KIND_CAPS")
    return {k: max(1, int(_f(over.get(k), v))) for k, v in KIND_CAPS.items()}

def cap_for(dept):
    """The hard cap (estimated tokens) of one department's playbook."""
    n = _f(_json_setting("PALACE_PLAYBOOK_TOKENS_BY_DEPT").get(dept), S("PALACE_PLAYBOOK_TOKENS", float))
    return int(max(MIN_CAP, min(MAX_CAP, n)))

def limits_share():
    return max(0.1, min(0.9, S("PALACE_LIMITS_SHARE", float)))

def _date_ok(d, now=None):
    d = str(d or "")
    if not re.match(r"^\d{4}(-\d{2}){0,2}$", d): return False
    today = (now or now_utc()).strftime("%Y-%m-%d")
    if d > today[:len(d)]: return False
    try:
        dt.date(int(d[:4]), int(d[5:7] or 1), int(d[8:10] or 1))
        return True
    except ValueError:
        return False

def confidence(evidence):
    """0-1, from the strongest evidence type plus a little for independent sources. Only the owner's own decision reaches 1.0."""
    ws = [EVIDENCE.get(e.get("type"), 0.0) for e in evidence or []]
    if not ws: return 0.0
    extra = 0.05 * min(2, len({str(e.get("source")).lower() for e in evidence}) - 1)
    return round(min(1.0 if max(ws) >= 1.0 else 0.95, max(ws) + extra), 2)

def text_issues(text, kind=""):
    """Why a text may not enter the Palace: it names a retired concept, reads like an instruction to a model, or proposes gaming the platform."""
    out = []
    for ln in str(text or "").splitlines():
        for scope in ("prompts", "docs"):
            for r in TRU.hits(ln, scope):
                msg = f"names a retired concept ({r['id']}): {r['truth']}"
                if msg not in out: out.append(msg)
        if INJECT.search(ln) and "reads like an instruction to a model, not knowledge" not in out: out.append("reads like an instruction to a model, not knowledge")
    if kind in _GAMING_KINDS:
        from whatifs.playbook import BAD
        if BAD.search(str(text or "")): out.append("proposes gaming the platform or breaking policy")
    return out

_DEFS: dict = {}
def _defs(path):
    """Names defined in a Python file (functions, classes, assignments, methods as Class.method), cached while the file does not change."""
    sig = (os.path.getmtime(path), os.path.getsize(path))
    if _DEFS.get(path, (None,))[0] == sig: return _DEFS[path][1]
    names = set()
    try:
        with open(path, encoding="utf-8", errors="ignore") as f: tree = ast.parse(f.read())
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): names.add(n.name)
            elif isinstance(n, ast.ClassDef):
                names.add(n.name)
                names |= {f"{n.name}.{m.name}" for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    for e in (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t]):
                        if isinstance(e, ast.Name): names.add(e.id)
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name): names.add(n.target.id)
    except (SyntaxError, OSError):
        pass
    _DEFS[path] = (sig, names)
    return names

def ref_ok(ref):
    """Does an applied_in reference name something that really exists? Forms: contract:<check>, setting:<KEY>, tab:<Tab>, truth:<rule>, a path, or path:name."""
    ref = str(ref or "").strip()
    if ref.startswith("contract:"):
        from whatifs import contract as CON
        return ref[9:] in {f[0] for f in CON.FEATURES}
    if ref.startswith("setting:"): return ref[8:] in core.DEFAULTS
    if ref.startswith("tab:"): return ref[4:] in core.TABS
    if ref.startswith("truth:"): return ref[6:] in {r["id"] for r in TRU.RETIRED}
    path, _, name = ref.partition(":")
    if not path or ".." in path: return False
    full = os.path.join(ROOT, *path.split("/"))
    if not os.path.exists(full): return False
    if not name: return True
    if path.endswith(".py"): return name in _defs(full)
    try:
        with open(full, encoding="utf-8", errors="ignore") as f: return name in f.read()
    except OSError:
        return False

def _hash(it):
    core_ = {k: it.get(k) for k in ("kind", "title", "summary", "body", "departments", "stages", "topic_tags", "applied_in", "derived_from", "owner_input", "priority")}
    core_["evidence"] = [[e.get("source"), e.get("type"), e.get("url", "")] for e in it.get("evidence") or []]
    return hashlib.sha1(json.dumps(core_, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]

# ------------------------------------------------------------------ the write gate
def check(item, now=None):
    """(clean item, problems). Nothing enters the Palace unless the problem list is empty."""
    p = []; it = dict(item or {})
    kind = str(it.get("kind") or "").strip()
    if kind not in KINDS: p.append(f"unknown kind '{kind}'")
    title = re.sub(r"\s+", " ", str(it.get("title") or "")).strip()
    if not 8 <= len(title) <= 120: p.append(f"title must be 8-120 characters (has {len(title)})")
    summary = re.sub(r"\s+", " ", str(it.get("summary") or "")).strip()
    if not 20 <= len(summary) <= SUMMARY_MAX: p.append(f"summary must be 20-{SUMMARY_MAX} characters (has {len(summary)})")
    body = str(it.get("body") or summary).strip()
    deps = [str(d).strip() for d in _list(it.get("departments"))]
    if not deps or any(d != "all" and d not in DEPARTMENTS for d in deps): p.append("departments must name known departments (or 'all')")
    stages = [str(s).strip() for s in _list(it.get("stages"))] or ["all"]
    if any(s != "all" and s not in STAGES for s in stages): p.append("stages must name known stages (or 'all')")
    tags = [t for t in (re.sub(r"[^a-z0-9_-]", "", str(t).lower())[:24] for t in _list(it.get("topic_tags"))) if t][:12]
    ev = []
    for e in _list(it.get("evidence")):
        if not isinstance(e, dict): p.append("every evidence entry must be an object with source, date and type"); continue
        typ = str(e.get("type") or "").strip().lower(); typ = EVIDENCE_ALIAS.get(typ, typ)
        src, d, url = str(e.get("source") or "").strip(), str(e.get("date") or "").strip(), str(e.get("url") or "").strip()
        if len(src) < 3: p.append("evidence needs a source")
        if typ not in EVIDENCE: p.append(f"evidence type '{typ}' is not one of: {', '.join(EVIDENCE)}")
        if not _date_ok(d, now): p.append(f"evidence needs a real date that is not in the future (got '{d}')")
        if url and not re.match(r"^https?://[^\s/]+\.[^\s/]+", url): p.append("an evidence url must be a web address")
        ev.append({"source": src[:200], "url": url[:300], "date": d, "type": typ, "finding": str(e.get("finding") or "").strip()[:600]})
    if not ev: p.append("no evidence: every item needs at least one dated source")
    owner = it.get("owner_input") in (True, 1, "1", "TRUE", "True", "true")
    if kind == "owner_preference" and not owner: p.append("an owner_preference is the owner's own words: owner_input must be true")
    if owner and not any(e["type"] == "owner decision" for e in ev): p.append("owner_input needs evidence of type 'owner decision' (his words, dated)")
    applied = [str(a).strip() for a in _list(it.get("applied_in")) if str(a).strip()]
    dead = [a for a in applied if not ref_ok(a)]
    if dead: p.append("applied_in names code that does not exist: " + ", ".join(dead[:4]))
    derived = [str(a).strip() for a in _list(it.get("derived_from")) if str(a).strip()]
    p += text_issues("\n".join([title, summary, body]), kind)
    rb = it.get("review_by")
    if rb not in (None, "", "never") and not parse_iso(rb): p.append("review_by must be an ISO time, 'never' or absent")
    prio = int(_f(it.get("priority"), 2) or 2)
    if prio not in (1, 2, 3): p.append("priority must be 1 (context), 2 (normal) or 3 (core)")
    clean = {"kind": kind, "title": title, "summary": summary, "body": body, "departments": deps, "stages": stages, "topic_tags": tags, "evidence": ev,
             "owner_input": owner, "applied_in": applied, "derived_from": derived, "cost_note": str(it.get("cost_note") or "")[:200], "priority": prio,
             "review_by": None if rb is None else ("" if rb in ("", "never") else str(rb))}
    clean["id"] = str(it.get("id") or item_id(it.get("key") or f"{kind}|{title}"))
    clean["confidence"] = confidence(ev)
    clean["content_hash"] = _hash(clean)
    return clean, p

def validate(item, now=None):
    clean, p = check(item, now)
    if p: raise PalaceError(p)
    return clean

# ------------------------------------------------------------------ bodies (Drive folder palace/; a local folder in fake mode)
def _folder():
    """The Drive folder palace/ under the engine's folder, found or created once (id kept in PALACE_FOLDER_ID). '' = fall back to the main folder."""
    fid = S("PALACE_FOLDER_ID")
    if fid or core.FAKE: return fid
    try:
        import requests
        parent = S("DRIVE_FOLDER_ID")
        q = "name = 'palace' and mimeType = 'application/vnd.google-apps.folder' and trashed = false" + (f" and '{parent}' in parents" if parent else "")
        r = requests.get("https://www.googleapis.com/drive/v3/files", headers=core.gdrive_headers(), params={"q": q, "fields": "files(id)", "pageSize": 1}, timeout=30)
        r.raise_for_status()
        found = r.json().get("files") or []
        if found: fid = found[0]["id"]
        else:
            meta = {"name": "palace", "mimeType": "application/vnd.google-apps.folder"}
            if parent: meta["parents"] = [parent]
            r = requests.post("https://www.googleapis.com/drive/v3/files", headers=core.gdrive_headers(), json=meta, timeout=30)
            r.raise_for_status(); fid = r.json()["id"]
        set_setting("PALACE_FOLDER_ID", fid)
        return fid
    except Exception as e:
        log(f"palace folder unavailable, using the main Drive folder: {scrub(e)[:120]}", "WARN")
        return ""

def _put_blob(name, text):
    """Store one JSON text; returns its reference ('drive:<id>')."""
    if core.FAKE:
        d = os.path.join(core.WORK, "_drive", "palace"); os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f: f.write(text)
        return "drive:palace/" + name
    from whatifs import publish as PUB
    tmp = tempfile.mkdtemp(prefix="palace_")
    try:
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f: f.write(text)
        fid, _url = retry(lambda: PUB.drive_upload(p, name, parent=_folder() or None), tries=3, wait=3, what="palace upload")
        return "drive:" + str(fid)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _get_blob(ref):
    ref = str(ref or "")
    if ref.startswith("inline:"): return ref[7:]
    if not ref.startswith("drive:"): raise PalaceError([f"unknown body reference '{ref[:40]}'"])
    fid = ref[6:]
    if core.FAKE:
        with open(os.path.join(core.WORK, "_drive", *fid.split("/")), encoding="utf-8") as f: return f.read()
    from whatifs import publish as PUB
    tmp = tempfile.mkdtemp(prefix="palace_")
    try:
        with open(PUB.drive_download(fid, os.path.join(tmp, "body.json")), encoding="utf-8") as f: return f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _body_of(it, version, actor, prev_ref):
    return {"id": it["id"], "version": version, "kind": it["kind"], "title": it["title"], "summary": it["summary"], "body": it["body"], "evidence": it["evidence"],
            "applied_in": it["applied_in"], "derived_from": it["derived_from"], "departments": it["departments"], "stages": it["stages"],
            "topic_tags": it["topic_tags"], "owner_input": it["owner_input"], "actor": actor, "prev_body_ref": prev_ref}

def _store_body(it, version, actor, prev_ref, inline=False):
    """Body reference for a new version. Drive first (3 tries); a Drive failure falls back to an inline body so the organisation never stops learning."""
    text = json.dumps(_body_of(it, version, actor, "" if str(prev_ref).startswith("inline:") else prev_ref), ensure_ascii=False, sort_keys=True)
    if inline: return "inline:" + text
    try:
        return _put_blob(f"{it['id']}.v{version}.json", text)
    except Exception as e:
        if len(text) > INLINE_MAX: raise
        log(f"palace body kept inline (Drive unavailable): {scrub(e)[:120]}", "WARN")
        return "inline:" + text

# ------------------------------------------------------------------ the index
def _parse(row):
    r = dict(row)
    for c in _JSON_COLS: r[c] = _list(r.get(c))
    r["confidence"] = _f(r.get("confidence")); r["version"] = int(_f(r.get("version"), 1) or 1); r["applied_count"] = int(_f(r.get("applied_count")))
    r["priority"] = min(3, max(1, int(_f(r.get("priority"), 2) or 2)))
    r["owner_input"] = str(r.get("owner_input") or "").strip().upper() in ("TRUE", "1", "YES")
    r["outcome_score"] = _f(r.get("outcome_score")) if str(r.get("outcome_score") or "").strip() else None
    for c in ("status", "kind", "id", "review_by", "superseded_by", "supersedes", "body_ref", "content_hash", "title", "summary", "updated"): r[c] = str(r.get(c) or "").strip()
    return r

def rows(st=None):
    """Every Palace item, parsed. On a Sheet that predates the Palace the tabs are created once."""
    st = st or store()
    try: raw = st.rows(TAB)
    except Exception:
        st.ensure_tabs(); raw = st.rows(TAB)
    return [_parse(r) for r in raw if str(r.get("id") or "").strip()]

def get(iid, st=None, rs=None):
    return next((r for r in (rows(st) if rs is None else rs) if r["id"] == iid), None)

def _need(iid, st=None):
    r = get(iid, st)
    if r is None: raise PalaceError([f"no such item {iid}"])
    return r

def palace_hash(rs):
    """One id for the whole state of the Palace: it changes when any item, version or status changes."""
    return hashlib.sha1("\n".join(sorted(f"{r['id']}@{r['version']}:{r['status']}" for r in rs)).encode("utf-8")).hexdigest()[:12]

def _log(events, st=None):
    """Append one Palace_Versions row per change (actor, action, id, item version, from, to, note) with a running version and the hash after the change."""
    st = st or store()
    try: last = max([int(_f(r.get("version"))) for r in st.rows(VTAB)] or [0])
    except Exception: last = 0
    h = palace_hash(rows(st)); t = iso()
    st.append(VTAB, [{"version": last + 1 + i, "ts": t, "actor": a, "action": act, "item_id": iid, "item_version": ver, "from_status": frm, "to_status": to,
                      "palace_hash": h, "note": str(note or "")[:300]} for i, (a, act, iid, ver, frm, to, note) in enumerate(events)])
    return last + len(events), h

def version(st=None):
    """{'version', 'palace_hash'} of the newest recorded change (version 0 = nothing recorded yet)."""
    st = st or store()
    try: vs = st.rows(VTAB)
    except Exception: vs = []
    if not vs: return {"version": 0, "palace_hash": palace_hash(rows(st))}
    top = max(vs, key=lambda r: int(_f(r.get("version"))))
    return {"version": int(_f(top.get("version"))), "palace_hash": str(top.get("palace_hash") or "")}

def _review_by(kind, now):
    d = review_days(kind)
    return iso(now + dt.timedelta(days=d)) if d > 0 else ""

def _row(it, actor, status, now, body_ref, ver=1, created=None, supersedes=""):
    t = iso(now)
    return {"id": it["id"], "kind": it["kind"], "title": it["title"], "body_ref": body_ref, "summary": it["summary"], "departments": it["departments"],
            "stages": it["stages"], "topic_tags": it["topic_tags"], "evidence": [{k: e[k] for k in ("source", "url", "date", "type") if e.get(k)} for e in it["evidence"]],
            "confidence": it["confidence"], "status": status, "version": ver, "supersedes": supersedes, "superseded_by": "", "derived_from": it["derived_from"],
            "owner_input": "TRUE" if it["owner_input"] else "", "created": created or t, "updated": t,
            "review_by": _review_by(it["kind"], now) if it.get("review_by") is None else it["review_by"], "applied_count": 0, "last_applied": "", "outcome_score": "",
            "cost_note": it.get("cost_note", ""), "applied_in": it["applied_in"], "content_hash": it["content_hash"], "actor": actor, "status_note": "",
            "priority": it.get("priority", 2)}

def _actor_ok(actor):
    if actor not in ACTORS: raise PalaceError([f"unknown actor '{actor}'"])

def _owner_rule(row, actor, new_is_owner=False):
    """The owner's words change only by the owner (the build session may transcribe a newer owner decision; nobody else may touch them)."""
    if not row.get("owner_input"): return
    if actor == "owner" or (actor == "build" and new_is_owner): return
    raise PalaceError([f"{row['id']} holds the owner's own words: only the owner can change it (asked by '{actor}')"])

def _write_update(old, it, actor, st, now, body_ref=None, inline=False):
    """A content change = a new version of the same item. The status is never touched here."""
    ver = old["version"] + 1
    ref = body_ref or _store_body(it, ver, actor, old.get("body_ref", ""), inline)
    new = _row(it, actor, old["status"], now, ref, ver=ver, created=old.get("created"), supersedes=old.get("supersedes", ""))
    keep = ("status", "superseded_by", "applied_count", "last_applied", "outcome_score", "status_note", "created", "id")
    changes = {k: v for k, v in new.items() if k not in keep}
    if it.get("review_by") is None: changes.pop("review_by")                     # a rewording does not reset the clock; re-validation does
    st.update(TAB, "id", old["id"], changes)
    return ver

def add_many(items, actor, status="proposed", st=None, now=None, inline=False, skip_invalid=False):
    """Add items (or new versions of items that already exist under the same id) in one batch. Returns [{'id', 'result'}] with result
    added / updated / unchanged / refused. Unless skip_invalid, one invalid item refuses the whole batch and nothing is written."""
    _actor_ok(actor); st = st or store(); now = now or now_utc()
    allowed = START.get(status)
    if allowed is None or (allowed != ANY and actor not in allowed): raise PalaceError([f"'{actor}' may not create an item as '{status}' (new knowledge enters as 'proposed')"])
    have = {r["id"]: r for r in rows(st)}; checked = []
    for i in items:                                             # pass 1: judge everything before anything is written
        c, p = check(i, now); old = have.get(c["id"])
        if not p and c["owner_input"] and actor not in ("owner", "build"): p.append(f"only the Owner Office records the owner's words (asked by '{actor}')")
        if not p and c["priority"] == 3 and actor not in ("owner", "council", "build"): p.append(f"priority 3 (core) is set by the owner, the Council or the founding seed only (asked by '{actor}')")
        if not p and old is not None and old["content_hash"] != c["content_hash"]:
            try: _owner_rule(old, actor, c["owner_input"])
            except PalaceError as e: p += e.problems
        checked.append((c, p))
    bad = [f"{c['title'][:40] or '?'}: {'; '.join(p)}" for c, p in checked if p]
    if bad and not skip_invalid: raise PalaceError(bad)
    new, events, out = [], [], []
    for c, p in checked:                                        # pass 2: write
        if p: out.append({"id": c["id"], "result": "refused", "why": "; ".join(p)}); continue
        old = have.get(c["id"])
        if old is None:
            row = _row(c, actor, status, now, c.get("body_ref") or _store_body(c, 1, actor, "", inline)); new.append(row); have[c["id"]] = _parse(row)
            events.append((actor, "add", c["id"], 1, "", status, c["title"][:120])); out.append({"id": c["id"], "result": "added"})
        elif old["content_hash"] == c["content_hash"]:
            out.append({"id": c["id"], "result": "unchanged"})
        else:
            ver = _write_update(old, c, actor, st, now, body_ref=c.get("body_ref"), inline=inline)
            events.append((actor, "update", c["id"], ver, old["status"], old["status"], c["title"][:120])); out.append({"id": c["id"], "result": "updated"})
    if new: st.append(TAB, new)
    if events: _log(events, st)
    return out

def add(item, actor, status="proposed", st=None, now=None, inline=False):
    """Add one item (see add_many). Returns the stored row with 'result'."""
    res = add_many([item], actor, status, st, now, inline)[0]
    return dict(_need(res["id"], st), result=res["result"])

# ------------------------------------------------------------------ life cycle
def _cascade(src_ids, why, st, now):
    """Provenance cascade: everything derived from a withdrawn item is sent back for re-validation by code (readers are never trusted to check where
    knowledge came from). A derived LIMIT stays served but becomes review-due; anything else is expired. Follows the chain to the end."""
    out, seen, queue = [], set(src_ids), list(src_ids); events = []
    while queue:
        src = queue.pop(0)
        for r in rows(st):
            if r["id"] in seen or src not in r["derived_from"] or r["status"] not in SERVABLE: continue
            seen.add(r["id"]); queue.append(r["id"]); note = f"its source {src} was withdrawn ({why})"[:300]
            if is_limit(r):
                st.update(TAB, "id", r["id"], {"review_by": iso(now - dt.timedelta(seconds=1)), "updated": iso(now), "status_note": note})
                events.append(("clock", "review_due", r["id"], r["version"], r["status"], r["status"], note))
            else:
                st.update(TAB, "id", r["id"], {"status": "expired", "updated": iso(now), "actor": "clock", "status_note": note})
                events.append(("clock", "expire", r["id"], r["version"], r["status"], "expired", note))
            out.append(r["id"])
    if events: _log(events, st)
    return out

def transition(iid, to, actor, note, st=None, now=None):
    """Move one item to another status. Raises PalaceError when the move is not in MOVES, the actor may not make it, the item holds the owner's
    words and the actor is not the owner, or no reason is given."""
    _actor_ok(actor); st = st or store(); now = now or now_utc(); r = _need(iid, st); frm = r["status"]
    if to == "superseded": raise PalaceError(["use supersede(): an item is superseded only by naming what replaces it"])
    allowed = MOVES.get((frm, to))
    if allowed is None: raise PalaceError([f"illegal move {frm} -> {to} for {iid}"])
    if allowed != ANY and actor not in allowed: raise PalaceError([f"'{actor}' may not move {iid} from {frm} to {to} (allowed: {', '.join(allowed)})"])
    _owner_rule(r, actor)
    if len(str(note or "").strip()) < 8: raise PalaceError([f"moving {iid} to {to} needs a reason (the evidence or the decision)"])
    ch = {"status": to, "updated": iso(now), "actor": actor, "status_note": str(note)[:300]}
    if frm == "expired" and to in SERVABLE: ch["review_by"] = _review_by(r["kind"], now)
    st.update(TAB, "id", iid, ch)
    _log([(actor, "move", iid, r["version"], frm, to, note)], st)
    if to == "retired": _cascade([iid], "retired", st, now)
    return _need(iid, st)

def supersede(old_id, new_item, actor, note="", st=None, now=None):
    """Replace an item by a new one: the new item takes over (same status when the old one was served, else accepted), the old one is kept as
    'superseded' with a pointer and can never be served again, and everything derived from the old one goes back for re-validation."""
    _actor_ok(actor); st = st or store(); now = now or now_utc(); old = _need(old_id, st)
    allowed = MOVES.get((old["status"], "superseded"))
    if allowed is None or actor not in allowed: raise PalaceError([f"'{actor}' may not supersede {old_id} (status {old['status']})"])
    c = validate(new_item, now)
    _owner_rule(old, actor, c["owner_input"])
    if c["owner_input"] and actor not in ("owner", "build"): raise PalaceError(["only the Owner Office records the owner's words"])
    if c["priority"] == 3 and actor not in ("owner", "council", "build"): raise PalaceError(["priority 3 (core) is set by the owner, the Council or the founding seed only"])
    if c["id"] == old_id: raise PalaceError(["the replacement has the same id as the item it replaces: that is an update, use add()"])
    if get(c["id"], st) is not None: raise PalaceError([f"the replacement {c['id']} already exists"])
    status = old["status"] if old["status"] in SERVABLE else "accepted"
    st.append(TAB, [_row(c, actor, status, now, _store_body(c, 1, actor, ""), supersedes=old_id)])
    st.update(TAB, "id", old_id, {"status": "superseded", "superseded_by": c["id"], "updated": iso(now), "actor": actor, "status_note": (note or f"replaced by {c['id']}")[:300]})
    _log([(actor, "add", c["id"], 1, "", status, f"supersedes {old_id}"), (actor, "supersede", old_id, old["version"], old["status"], "superseded", note or c["id"])], st)
    _cascade([old_id], f"superseded by {c['id']}", st, now)
    return _need(c["id"], st)

def is_limit(r):
    return bool(r.get("owner_input")) or r.get("kind") in LIMIT_KINDS

def overdue(r, now):
    rb = parse_iso(r.get("review_by")) if r.get("review_by") else None
    return bool(rb and rb < now)

def expire(st=None, now=None):
    """The clock: a served item past review_by is expired (out of every playbook until re-validated). A LIMIT is never dropped silently:
    it stays served, marked review-due, and is reported."""
    st = st or store(); now = now or now_utc(); out = {"expired": [], "review_due": []}; events = []
    for r in rows(st):
        if r["status"] not in SERVABLE or not overdue(r, now): continue
        if is_limit(r): out["review_due"].append(r["id"]); continue
        note = f"review_by {r['review_by']} passed without re-validation"
        st.update(TAB, "id", r["id"], {"status": "expired", "updated": iso(now), "actor": "clock", "status_note": note})
        events.append(("clock", "expire", r["id"], r["version"], r["status"], "expired", note)); out["expired"].append(r["id"])
    if events: _log(events, st)
    return out

def revalidate(iid, actor, note, st=None, now=None):
    """Confirm an item is still true: review_by moves forward; an expired item is accepted again. Owner, Council or D10 only, with a reason."""
    _actor_ok(actor); st = st or store(); now = now or now_utc(); r = _need(iid, st)
    if actor not in ("owner", "council", "D10"): raise PalaceError([f"'{actor}' may not re-validate (owner, council or D10 only)"])
    if r["status"] == "expired": return transition(iid, "accepted", actor, note, st, now)
    if r["status"] not in SERVABLE: raise PalaceError([f"{iid} is {r['status']}: it cannot be re-validated"])
    _owner_rule(r, actor)
    if len(str(note or "").strip()) < 8: raise PalaceError(["re-validation needs a reason (the evidence)"])
    st.update(TAB, "id", iid, {"review_by": _review_by(r["kind"], now), "updated": iso(now), "actor": actor, "status_note": str(note)[:300]})
    _log([(actor, "revalidate", iid, r["version"], r["status"], r["status"], note)], st)
    return _need(iid, st)

def mark_applied(ids, st=None, now=None):
    """Count a use: called when a department cites an item in applied_items. Usage is bookkeeping, not a new Palace version."""
    st = st or store(); now = now or now_utc(); have = {r["id"]: r for r in rows(st)}; n = 0
    for iid in dict.fromkeys(ids or []):
        r = have.get(iid)
        if r and r["status"] in SERVABLE:
            st.update(TAB, "id", iid, {"applied_count": r["applied_count"] + 1, "last_applied": iso(now)}); n += 1
    return n

def enforce_caps(st=None, now=None):
    """Size caps per kind, enforced by code (never by a model rewriting the Palace): over the cap, the lowest-value served item is expired -
    testing before accepted before proven, then lowest confidence, least used, oldest. Limits, owner words and canon are never displaced."""
    st = st or store(); now = now or now_utc(); caps = kind_caps(); by, out, events = {}, [], []
    for r in rows(st):
        if r["status"] in SERVABLE and not overdue(r, now): by.setdefault(r["kind"], []).append(r)
    for kind, rs in sorted(by.items()):
        over = len(rs) - caps.get(kind, 10 ** 9)
        if over <= 0 or kind in KEEP_KINDS: continue
        pool = sorted([r for r in rs if not r["owner_input"]], key=lambda r: (_RANK[r["status"]], r["confidence"], r["applied_count"], r["updated"], r["id"]))
        for r in pool[:over]:
            note = f"size cap for {kind} ({caps[kind]}): lowest-value item displaced"
            st.update(TAB, "id", r["id"], {"status": "expired", "updated": iso(now), "actor": "librarian", "status_note": note})
            events.append(("librarian", "expire", r["id"], r["version"], r["status"], "expired", note)); out.append(r["id"])
    if events: _log(events, st)
    return out

def row_issues(r):
    """Why a stored row is not fit to be served (a cheap re-check of the write gate on what is in the index now)."""
    p = []
    if r["kind"] not in KINDS: p.append(f"unknown kind '{r['kind']}'")
    if not 20 <= len(r["summary"]) <= SUMMARY_MAX: p.append("summary outside 20-400 characters")
    if not r["evidence"]: p.append("no evidence")
    if not r["departments"] or any(d != "all" and d not in DEPARTMENTS for d in r["departments"]): p.append("unknown department")
    if not r["body_ref"]: p.append("no body reference")
    dead = [a for a in r["applied_in"] if not ref_ok(a)]
    if dead: p.append("applied_in names code that does not exist: " + ", ".join(dead[:3]))
    p += text_issues(r["title"] + "\n" + r["summary"], r["kind"])
    return p

def tidy(st=None, now=None):
    """Self-repair before the health check: a served item that now names a retired concept is expired (the owner's words are reported instead, only
    he can change them); a code reference that no longer exists is dropped from a runtime item (seed items are corrected by their seed file)."""
    st = st or store(); now = now or now_utc(); out = {"expired": [], "refs_dropped": []}; events = []
    for r in rows(st):
        if r["status"] not in SERVABLE: continue
        dirty = text_issues(r["title"] + "\n" + r["summary"], r["kind"])
        if dirty and not r["owner_input"]:
            st.update(TAB, "id", r["id"], {"status": "expired", "updated": iso(now), "actor": "clock", "status_note": dirty[0][:300]})
            events.append(("clock", "expire", r["id"], r["version"], r["status"], "expired", dirty[0])); out["expired"].append(r["id"]); continue
        dead = [a for a in r["applied_in"] if not ref_ok(a)]
        if dead and not r["body_ref"].startswith("seed:"):
            st.update(TAB, "id", r["id"], {"applied_in": [a for a in r["applied_in"] if a not in dead], "updated": iso(now), "status_note": ("code reference lost: " + ", ".join(dead))[:300]})
            events.append(("clock", "ref_lost", r["id"], r["version"], r["status"], r["status"], ", ".join(dead))); out["refs_dropped"].append(r["id"])
            log(f"palace: {r['id']} lost its code reference(s) {', '.join(dead)[:160]}", "WARN")
    if events: _log(events, st)
    return out

# ------------------------------------------------------------------ playbooks (the ONE doorway from the Palace into a prompt)
def servable(r, now):
    """THE GUARD. Runs before any ranking: retired, superseded, expired or merely proposed items can never be served, whatever label they carry;
    nor can an item with a successor, an item past review_by (unless it is a limit), or an item that names a retired concept."""
    if r["status"] not in SERVABLE or r["superseded_by"]: return False
    if overdue(r, now) and not is_limit(r): return False
    return not _dirty(r)

_DIRTY: dict = {}
def _dirty(r):
    """Does the served text name a retired concept or read like an instruction? Remembered per text and per number of retired rules."""
    key = (r["title"], r["summary"], len(TRU.RETIRED))
    if key not in _DIRTY:
        if len(_DIRTY) > 5000: _DIRTY.clear()
        _DIRTY[key] = bool(text_issues(r["title"] + "\n" + r["summary"]))
    return _DIRTY[key]

def _addressed(r, dept, stage):
    if "all" not in r["departments"] and dept not in r["departments"]: return False
    return not r["stages"] or "all" in r["stages"] or stage in r["stages"]

def _terms(text):
    return {w[:7] for w in re.findall(r"[a-z][a-z0-9]{2,}", str(text or "").lower()) if w not in _STOP}

def _lane(r):
    return 0 if is_limit(r) else 3 - _RANK.get(r["status"], -1)

def _relevance(r, dept, stage, q, idf):
    """Deterministic score: addressed to this department by name, stage match, weighted keyword overlap with the topic, a tag hit, computed trust."""
    s = (2.0 if dept in r["departments"] else 0.0) + (1.0 if stage in r["stages"] else 0.0) + r["confidence"]
    if q:
        doc = _terms(r["title"] + " " + r["summary"] + " " + " ".join(r["topic_tags"]))
        s += 4.0 * sum(idf.get(t, 0.0) for t in q if t in doc) / (sum(idf.get(t, 1.0) for t in q) or 1.0)
        if q & {t[:7] for t in r["topic_tags"]}: s += 1.0
    if r["outcome_score"] is not None: s += max(-1.0, min(1.0, r["outcome_score"]))
    return round(s, 4)

def _line(r, now):
    lab = ("LIMIT" + (" (owner)" if r["owner_input"] else "") + (", review due" if overdue(r, now) else "")) if is_limit(r) else r["status"].upper()
    return f"- [{r['id']}] {lab}: {r['summary']}"

def playbook(dept, stage=None, topic="", rs=None, record=True, cap=None, now=None, st=None):
    """The bounded block of knowledge one department gets before it acts: guard -> lanes (limits, proven, accepted, testing) -> relevance ->
    greedy fill under the hard cap. Deterministic: the same Palace state gives byte-identical text, and playbook_id is the hash of that text."""
    if dept not in DEPARTMENTS: raise PalaceError([f"unknown department '{dept}'"])
    stage = stage or DEPARTMENTS[dept][1]
    if stage not in STAGES: raise PalaceError([f"unknown stage '{stage}'"])
    now = now or now_utc(); st = st or store(); rs = rows(st) if rs is None else rs
    cap = int(max(MIN_CAP, min(MAX_CAP, cap or cap_for(dept))))
    cands = [r for r in rs if servable(r, now) and _addressed(r, dept, stage)]
    q = _terms(topic); df = {}
    for r in cands:
        for t in _terms(r["title"] + " " + r["summary"] + " " + " ".join(r["topic_tags"])): df[t] = df.get(t, 0) + 1
    idf = {t: math.log(1.0 + len(cands) / n) for t, n in df.items()}
    ranked = sorted(cands, key=lambda r: r["id"])
    ranked.sort(key=lambda r: r["updated"], reverse=True)
    ranked.sort(key=lambda r: (_lane(r), -r["priority"], 0 if r["owner_input"] else 1, -_relevance(r, dept, stage, q, idf), -r["confidence"]))
    head = HEADER.format(dept=dept, name=DEPARTMENTS[dept][0], stage=stage)
    lines = {r["id"]: _line(r, now) for r in ranked}; cost = {i: est_tokens(l + "\n") for i, l in lines.items()}
    base = est_tokens(head + "\n"); used = [base]; chosen = set()
    def take(pool, budget):
        for r in pool:
            if r["id"] not in chosen and used[0] + cost[r["id"]] <= budget: chosen.add(r["id"]); used[0] += cost[r["id"]]
    lim = [r for r in ranked if _lane(r) == 0]; rest = [r for r in ranked if _lane(r) != 0]
    take(lim, min(cap, base + int(cap * limits_share()))); take(rest, cap); take(lim, cap)
    picked = [r for r in ranked if r["id"] in chosen]
    out = {"playbook_id": "", "dept": dept, "stage": stage, "topic": str(topic or "")[:120], "text": "", "items": [], "refs": [], "tokens": 0, "cap": cap,
           "palace_hash": palace_hash(rs), "considered": len(cands), "left_out": len(cands) - len(picked),
           "limits_left_out": [r["id"] for r in lim if r["id"] not in chosen]}
    if not picked: return out
    text = head + "\n" + "\n".join(lines[r["id"]] for r in picked)
    out.update(playbook_id="PL-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12].upper(), text=text, items=[r["id"] for r in picked],
               refs=[f"{r['id']}@{r['version']}" for r in picked], tokens=est_tokens(text))
    if record: _record(out, st)
    return out

def _record(pb, st):
    """Each distinct playbook is stored once (index row + the exact text), so a later check can prove what a department was given. Never raises."""
    try:
        if any(r.get("playbook_id") == pb["playbook_id"] for r in st.rows(PTAB)): return False
        try: ref = _put_blob(f"playbook_{pb['playbook_id']}.json", json.dumps({k: pb[k] for k in ("playbook_id", "dept", "stage", "topic", "text", "refs", "tokens", "cap", "palace_hash")}, ensure_ascii=False, sort_keys=True))
        except Exception as e: log(f"playbook text not stored on Drive: {scrub(e)[:120]}", "WARN"); ref = ""
        st.append(PTAB, [{"playbook_id": pb["playbook_id"], "ts": iso(), "dept": pb["dept"], "stage": pb["stage"], "topic": pb["topic"], "palace_hash": pb["palace_hash"],
                          "n_items": len(pb["items"]), "tokens": pb["tokens"], "cap": pb["cap"], "item_ids": pb["refs"], "body_ref": ref}])
        return True
    except Exception as e:
        log(f"playbook not recorded: {scrub(e)[:120]}", "WARN")
        return False

def playbook_issues(pb, rs, now):
    """The invariants every playbook must hold; any hit is a bug in the doorway, so the health check fails on it."""
    p = []; by = {r["id"]: r for r in rs}; tag = f"playbook {pb['dept']}"
    if pb["tokens"] > pb["cap"]: p.append(f"{tag}: {pb['tokens']} estimated tokens over its cap {pb['cap']}")
    if len(pb["items"]) != len(set(pb["items"])): p.append(f"{tag}: an item appears twice")
    bad = [i for i in pb["items"] if i not in by or not servable(by[i], now)]
    if bad: p.append(f"{tag}: serves an item that may not be served ({bad[0]})")
    lanes = [_lane(by[i]) for i in pb["items"] if i in by]
    if lanes != sorted(lanes): p.append(f"{tag}: limits are not first")
    return p

def body(iid, st=None):
    """The full record of one item, fetched on demand: seed items resolve from the repo, runtime items from Drive (or their inline fallback)."""
    r = _need(iid, st); ref = r["body_ref"]
    if ref.startswith("seed:"):
        it = next((x for x in seed_items()[0] if x["id"] == iid), None)
        if it is None: raise PalaceError([f"{iid} points at a seed entry that no longer exists ({ref})"])
        return _body_of(it, r["version"], "build", "")
    return json.loads(_get_blob(ref))

# ------------------------------------------------------------------ founding knowledge (whatifs/org/seed/*.json) and mirrors of existing records
_SEED: dict = {}
def seed_items():
    """(clean items, problems) from every seed file; cached while the files do not change. File = {"defaults": {...}, "items": [{"key": ...}, ...]}."""
    files = sorted(glob.glob(os.path.join(SEED_DIR, "*.json")))
    sig = tuple((f, os.path.getmtime(f), os.path.getsize(f)) for f in files)
    if _SEED.get("sig") == sig: return _SEED["items"], _SEED["bad"]
    items, bad, seen = [], [], {}
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f, encoding="utf-8") as fh: doc = json.load(fh)
        except Exception as e:
            bad.append(f"{name}: not valid JSON ({str(e)[:80]})"); continue
        defaults = (doc.get("defaults") or {}) if isinstance(doc, dict) else {}
        for n, raw in enumerate((doc.get("items") or []) if isinstance(doc, dict) else doc):
            it = dict(defaults, **raw) if isinstance(raw, dict) else {}
            key = str(it.get("key") or "").strip()
            if not key: bad.append(f"{name}[{n}]: every seed item needs a key"); continue
            clean, p = check(dict(it, key="seed:" + key))
            status = str(it.get("status") or "accepted")
            if status not in ("accepted", "proposed"): p.append("a seed item starts as accepted or proposed")
            if key in seen: p.append(f"duplicate key (also in {seen[key]})")
            seen.setdefault(key, name)
            if p: bad += [f"{name}:{key}: {x}" for x in p]; continue
            clean.update(status=status, batch=str(it.get("batch") or ""), body_ref=f"seed:{name}#{key}", seed_key=key, seed_file=name)
            items.append(clean)
    _SEED.update(sig=sig, items=items, bad=bad)
    return items, bad

def seed_issues():
    return list(seed_items()[1])

def ensure_seed(st=None, now=None):
    """Load the founding knowledge idempotently: a new seed item is added, a reworded one becomes a new version, and a status the organisation
    has changed since is never touched (a seed can not resurrect what was retired)."""
    st = st or store(); now = now or now_utc(); items, bad = seed_items(); have = {r["id"]: r for r in rows(st)}; new, events, changed = [], [], 0
    for it in items:
        old = have.get(it["id"])
        if old is None:
            new.append(_row(it, "build", it["status"], now, it["body_ref"])); events.append(("build", "seed", it["id"], 1, "", it["status"], it["seed_key"]))
        elif old["content_hash"] != it["content_hash"]:
            ver = _write_update(old, it, "build", st, now, body_ref=it["body_ref"]); changed += 1
            events.append(("build", "update", it["id"], ver, old["status"], old["status"], it["seed_key"]))
    if new: st.append(TAB, new)
    if events: _log(events, st)
    return {"added": len(new), "updated": changed, "invalid": len(bad), "seed": len(items)}

def _fit(parts, n=SUMMARY_MAX):
    out = ""
    for p in parts:
        p = re.sub(r"\s+", " ", str(p or "")).strip()
        if p and len(out) + len(p) + 1 <= n: out = (out + " " + p).strip()
    return out

def _drive_to(row, want, actor, note, st, now):
    """Move a mirror to the status its source says, directly or through 'testing' when the life cycle needs two legal steps."""
    if row["status"] == want or row["status"] == "superseded": return 0
    for path in ([want], ["testing", want]):
        cur, ok = row["status"], True
        for step in path:
            al = MOVES.get((cur, step))
            ok = ok and al is not None and (al == ANY or actor in al); cur = step
        if ok:
            for step in path: transition(row["id"], step, actor, note, st, now)
            return 1
    return 0

_FAMILY = {"hook": (["D4"], ["writing"]), "title": (["D5"], ["packaging"]), "topic": (["D4", "D1"], ["ideation", "planning"]),
           "length": (["D4", "D1"], ["writing", "planning"]), "lead": (["D4"], ["writing"]), "origin": (["D4", "D1"], ["ideation", "planning"])}

def sync_brain(st=None, now=None):
    """Mirror the learning core (Technique_Evidence) into the Palace. A proven / promising level is a technique (proven / testing); a retired level
    is an 'avoid' lesson in the limits lane. D10 is the only author and the learning core stays the authority: the mirror never expires by the clock."""
    st = st or store(); now = now or now_utc(); out = {"added": 0, "updated": 0, "moved": 0}
    try: lib = [t for t in st.rows("Technique_Evidence") if t.get("technique_id")]
    except Exception: lib = []
    if not lib: return out
    plan = []                                                   # (item, start status or None when it must not be created, wanted status)
    for t in lib:
        tid, state = str(t["technique_id"]), str(t.get("status") or "")
        fam, lvl, fmt = str(t.get("family") or ""), str(t.get("level") or ""), str(t.get("format") or "")
        deps, stages = _FAMILY.get(fam, (["D4"], ["writing"])); p = _f(t.get("p_beats_baseline"))
        ev = [{"source": f"Technique_Evidence {tid}", "date": str(t.get("updated") or iso(now))[:10], "type": "own data",
               "finding": f"P(beats baseline) {p}, {t.get('n_videos')} videos, {t.get('trials')} views, effect {t.get('effect_pp')} pp"}]
        base = {"departments": deps, "stages": stages, "topic_tags": [fam, lvl, fmt, "own-data"], "evidence": ev, "review_by": "never",
                "applied_in": ["whatifs/brain.py:update_library", "tab:Technique_Evidence"], "derived_from": [f"Technique_Evidence:{tid}"]}
        use = dict(base, key=f"te:{tid}", kind="technique", title=f"Own data: use {fam} = {lvl} ({fmt})"[:120],
                   summary=_fit([f"Own channel data: {fmt} videos with {fam} = {lvl} beat the channel baseline (P about {p:.1f}).", "How: " + str(t.get("mechanism")) + "." if t.get("mechanism") else ""]))
        avoid = dict(base, key=f"te-avoid:{tid}", kind="failure_lesson", title=f"Own data: avoid {fam} = {lvl} ({fmt})"[:120],
                     summary=f"Own channel data: {fmt} videos with {fam} = {lvl} lose to the channel baseline (P about {p:.1f}). Do not use it until new evidence re-opens it.")
        plan.append((use, {"proven": "proven", "promising": "testing"}.get(state), {"proven": "proven", "promising": "testing", "testing": "testing"}.get(state, "retired")))
        plan.append((avoid, "proven" if state == "retired" else None, "proven" if state == "retired" else "retired"))
    have = {r["id"]: r for r in rows(st)}
    for start in ("proven", "testing"):                         # create what the learning core now asserts
        batch = [it for it, s0, _w in plan if s0 == start and item_id(it["key"]) not in have]
        for res in (add_many(batch, "D10", start, st, now, inline=True, skip_invalid=True) if batch else []): out["added"] += res["result"] == "added"
    for it, _s0, want in plan:                                  # then keep every existing mirror in step with its source
        row = have.get(item_id(it["key"]))
        if row is None or row["status"] == "superseded": continue
        if want != "retired": out["updated"] += add_many([it], "D10", "testing", st, now, inline=True, skip_invalid=True)[0]["result"] == "updated"
        out["moved"] += _drive_to(row, want, "D10", f"learning core: {it['evidence'][0]['finding']}", st, now)
    return out

def sync_canon(st=None, now=None):
    """World canon from records that already exist: the character bible and every published case (charge, verdict, witness twist). The Librarian
    mirrors records; text typed by viewers never enters (handles and comments are left out)."""
    from whatifs import show as SHOW
    st = st or store(); now = now or now_utc(); items = []; today = iso(now)[:10]
    for c in SHOW.characters():
        cid, name = str(c.get("id") or "").strip(), str(c.get("name") or "").strip()
        if not cid or not name: continue
        items.append({"key": f"canon:character:{cid}", "kind": "world_canon", "title": f"Character: {name} ({c.get('role') or 'cast'})"[:120],
                      "summary": _fit([f"{name}, {c.get('role') or 'cast'}.", c.get("philosophy"), f"Speech: {c.get('rhythm')}." if c.get("rhythm") else "",
                                       f"Tics: {c.get('tics')}." if c.get("tics") else "", f"Running bit: {c.get('recurring_bit')}." if c.get("recurring_bit") else "",
                                       f"When wrong: {c.get('when_wrong')}." if c.get("when_wrong") else "", f"Relationships: {c.get('relationships')}." if c.get("relationships") else ""]),
                      "departments": ["D4", "D5", "D6", "D7"], "stages": ["ideation", "writing", "packaging", "visual", "sound"], "topic_tags": ["canon", "character", cid.lower()],
                      "evidence": [{"source": "character bible (Characters tab)", "date": today, "type": "show record"}], "applied_in": ["whatifs/show.py:characters", "tab:Characters"]})
    try:
        eps = {e.get("episode_id"): e for e in st.rows("Episodes") if e.get("yt_id") and str(e.get("status")) in ("SCHEDULED", "LIVE1", "LIVE")}
        shows = {r.get("episode_id"): r for r in st.rows("Show_Log")}; seasons = {r.get("episode_id"): r for r in st.rows("Season")}
    except Exception:
        eps, shows, seasons = {}, {}, {}
    for ep, e in eps.items():
        sh, se = shows.get(ep) or {}, seasons.get(ep) or {}
        if not (sh or se): continue
        charge = str(se.get("case") or "").strip() or str(e.get("premise") or "").strip()
        when = str(sh.get("ts") or se.get("ts") or today)[:10]
        items.append({"key": f"canon:case:{ep}", "kind": "world_canon", "title": f"Case {ep}: {str(e.get('title') or charge or 'untitled case')}"[:120],
                      "summary": _fit([f"Case {ep}.", f"Charge: {charge}." if charge else "", f"Verdict: {sh.get('verdict_winner') or se.get('verdict')} won (meter {sh.get('meter_final')})." if (sh.get("verdict_winner") or se.get("verdict")) else "",
                                       f"Witness twist: {sh.get('witness_twist')}." if sh.get("witness_twist") else "", "It happened on the show: later cases may refer to it and must not contradict it."]),
                      "departments": ["D4", "D5", "D1"], "stages": ["ideation", "writing", "packaging", "planning"], "topic_tags": ["canon", "case"],
                      "evidence": [{"source": f"Show_Log and Season records of {ep}", "date": when if _date_ok(when, now) else today, "type": "show record"}],
                      "applied_in": ["tab:Show_Log", "tab:Season"]})
    res = add_many(items, "librarian", "accepted", st, now, inline=True, skip_invalid=True) if items else []
    for r in res:
        if r["result"] == "refused": log(f"canon item refused: {r.get('why', '')[:160]}", "WARN")
    return {k: sum(1 for r in res if r["result"] == k) for k in ("added", "updated", "unchanged", "refused")}

# ------------------------------------------------------------------ upkeep, snapshot, health
def reconcile(st=None, now=None):
    """Audit trail for edits made outside this module (a hand edit of the Sheet): the state is re-hashed and the difference is recorded."""
    st = st or store(); v = version(st); h = palace_hash(rows(st))
    if v["version"] and v["palace_hash"] != h:
        _log([("clock", "external_edit", "", "", "", "", f"index changed outside the Palace code (was {v['palace_hash']})")], st); return True
    return False

def snapshot(st=None, now=None):
    """The whole index as one JSON on Drive, once per Palace state (a restore point and the Librarian's baseline)."""
    st = st or store(); v = version(st)
    try: done = any(r.get("action") == "snapshot" and r.get("palace_hash") == v["palace_hash"] for r in st.rows(VTAB))
    except Exception: done = False
    if done or not v["version"]: return ""
    ref = _put_blob(f"snapshot_{v['palace_hash']}.json", json.dumps({"palace_hash": v["palace_hash"], "version": v["version"], "ts": iso(now), "items": st.rows(TAB)}, ensure_ascii=False))
    _log([("librarian", "snapshot", "", "", "", "", ref)], st)
    return ref

def stats(rs, now=None, st=None):
    now = now or now_utc(); by_s, by_k = {}, {}
    for r in rs:
        by_s[r["status"]] = by_s.get(r["status"], 0) + 1; by_k[r["kind"]] = by_k.get(r["kind"], 0) + 1
    v = version(st)
    return {"items": len(rs), "served": sum(1 for r in rs if servable(r, now)), "owner": sum(1 for r in rs if r["owner_input"]), "by_status": by_s, "by_kind": by_k,
            "limits_due": sum(1 for r in rs if r["status"] in SERVABLE and is_limit(r) and overdue(r, now)),
            "inline_bodies": sum(1 for r in rs if r["body_ref"].startswith("inline:") and r["actor"] not in ("D10", "librarian")), "version": v["version"], "palace_hash": v["palace_hash"]}

def maintain(st=None, now=None):
    """Upkeep in a fixed order: audit trail (first, before any step here records a change of its own), founding knowledge, the clock, self-repair,
    size caps. Never raises - a step that fails is logged and named in the report, and the health check then judges what is really in the index."""
    if not S("PALACE_ON", bool): return {"status": "off"}
    st = st or store(); out = {}
    for name, fn in (("audit", reconcile), ("seed", ensure_seed), ("expire", expire), ("tidy", tidy), ("caps", enforce_caps)):
        try: out[name] = fn(st=st, now=now)
        except Exception as e:
            log(f"palace {name} failed: {scrub(e)[:160]}", "WARN"); out[name] = None
    return out

def daily(st=None, now=None):
    """The learning job's Palace step: upkeep, mirror the learning core and the show's records, snapshot a changed Palace. Never raises."""
    if not S("PALACE_ON", bool): return {"status": "off"}
    out = {"maintain": maintain(st, now)}
    for name, fn in (("brain", sync_brain), ("canon", sync_canon), ("snapshot", snapshot)):
        try: out[name] = fn(st=st, now=now)
        except Exception as e:
            log(f"palace {name} failed: {scrub(e)[:160]}", "WARN"); out[name] = None
    try:
        s = stats(rows(st), now, st)
        log(f"palace: {s['items']} items, {s['served']} served, version {s['version']}", public=f"knowledge palace: {s['items']} items, {s['served']} in use")
    except Exception: pass
    return out

def health(st=None, now=None):
    """{'ok', 'problems', 'notes', 'stats'}: is the Palace fit to feed departments? Problems hold the episode (contract check palace_health);
    notes are for the Librarian and the owner's brief."""
    st = st or store(); now = now or now_utc(); problems, notes = [], []
    try: rs = rows(st)
    except Exception as e: return {"ok": False, "problems": [f"the Palace index cannot be read: {scrub(e)[:120]}"], "notes": [], "stats": {}}
    items, bad = seed_items()
    problems += [f"seed file: {b}" for b in bad[:5]]
    have = {r["id"] for r in rs}; miss = [it["id"] for it in items if it["id"] not in have]
    if miss: problems.append(f"{len(miss)} founding item(s) missing from the index (first: {miss[0]})")
    if len(have) != len(rs): problems.append("the index holds the same item id twice")
    for r in rs:
        if r["status"] not in STATUSES: problems.append(f"{r['id']}: unknown status '{r['status']}'")
        elif r["status"] in SERVABLE: problems += [f"{r['id']}: {x}" for x in row_issues(r)[:2]]
    caps = kind_caps(); live = {}
    for r in rs:
        if r["status"] in SERVABLE and not overdue(r, now): live[r["kind"]] = live.get(r["kind"], 0) + 1
    for k, n in sorted(live.items()):
        if n > caps.get(k, 10 ** 9): (notes if k in KEEP_KINDS else problems).append(f"{n} served {k} items, cap {caps[k]}" + (" (limits and canon are consolidated by the Librarian, never dropped)" if k in KEEP_KINDS else ""))
    squeezed = []
    for dept in DEPARTMENTS:
        try:
            pb = playbook(dept, rs=rs, record=False, now=now, st=st); problems += playbook_issues(pb, rs, now)
            if pb["limits_left_out"]: squeezed.append(f"{dept} {len(pb['limits_left_out'])}")
        except Exception as e: problems.append(f"playbook {dept} could not be built: {scrub(e)[:100]}")
    if squeezed: notes.append("limits that did not fit a playbook cap (lowest priority first out; consolidate them or raise the cap): " + ", ".join(squeezed))
    s = stats(rs, now, st)
    if s["limits_due"]: notes.append(f"{s['limits_due']} limit(s) overdue for review (still served, marked review due)")
    if s["inline_bodies"]: notes.append(f"{s['inline_bodies']} item body(ies) kept inline after a Drive failure")
    return {"ok": not problems, "problems": problems, "notes": notes, "stats": s}

if __name__ == "__main__":
    import sys
    maintain(); _h = health()
    print("PALACE: " + ("GREEN" if _h["ok"] else "RED"), json.dumps(_h["stats"], sort_keys=True))
    for _p in _h["problems"]: print("  -", _p)
    for _n in _h["notes"]: print("  note:", _n)
    sys.exit(0 if _h["ok"] else 1)
