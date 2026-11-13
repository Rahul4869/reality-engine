"""The clip market (D6): the clip models as the provider's own pages state them, the rule that picks the best-ranked model the month's plan can pay, the request built from a model's row, and clips bought and priced by the second. See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import json, math
from whatifs.core import S, log, set_setting, iso, now_utc, DEFAULTS, scrub

SCENE_S = 5                         # the seconds of one animated scene of a long video
LONGEST_S = 10                      # the longest shot ONE clip is asked to cover (the ranking tests every model at 10 seconds; a model's own limit may be lower)
OLD_CLIP_S = 5.0                    # with the clip market off: every clip is this long ...
OLD_STRETCH = 1.3                   # ... and may be played this much slower to cover its shot
SHAPES_OK = ("follows", "inferred")  # where a clip's shape comes from: the page says it follows the start picture / not stated and measured on every clip
STALE_PCT = 0.10                    # the listing's base price moved by more than this: the model's page must be read again
SHAPE_TOL = 0.12                    # how far a clip's shape (width / height) may be from its start picture's before it counts as another shape

def on(): return S("CLIP_VALUE_ON", bool)

def _rows(text):
    try: rows = json.loads(text or "[]")
    except Exception: return None
    return [r for r in rows if isinstance(r, dict) and str(r.get("id") or "").strip()] if isinstance(rows, list) else None

def table():
    """The clip models, one row each (cell CLIP_MODELS). An unreadable cell falls back to the built-in rows and says so."""
    rows = _rows(S("CLIP_MODELS"))
    if rows is None:
        log("CLIP_MODELS is not a readable table: the built-in rows are used", "WARN"); rows = _rows(DEFAULTS["CLIP_MODELS"][0]) or []
    return rows

def row(mid=None, rows=None):
    mid = str(mid or S("FAL_HERO_MODEL") or "").strip()
    return next((r for r in (table() if rows is None else rows) if r.get("id") == mid), None)

def hero():
    """The row of the hero clip model while the clip market is on; None = the older way (a flat price for a 5-second clip)."""
    r = row() if on() else None
    return r if r is not None and usd_s(r) is not None else None

def usd_s(r):
    """USD for one second of this model at the size its row buys; None when the row does not say."""
    try: return float((r.get("usd_s") or {})[str(r.get("res") if r.get("res") is not None else "-")])
    except (KeyError, TypeError, ValueError): return None

def secs(r, want):
    """The whole seconds to BUY for a shot of `want` seconds: rounded up, never under the model's shortest clip, never over its longest."""
    lo = int(r.get("min_s") or SCENE_S); hi = max(lo, int(r.get("max_s") or lo))
    return int(min(max(math.ceil(float(want) - 1e-6), lo), hi))

def usd(r, seconds): return round(usd_s(r) * secs(r, seconds), 6)

def longest(r=None):
    """The longest shot one clip covers: with the clip market on, the model's longest clip and at most LONGEST_S; else a 5-second clip played 30% slower."""
    r = hero() if r is None else r
    return float(min(LONGEST_S, int(r.get("max_s") or SCENE_S))) if r else OLD_CLIP_S * OLD_STRETCH

def buy(seconds=None):
    """(row, seconds bought, USD) for ONE hero clip that must cover `seconds` (None = a scene of a long video)."""
    r = hero(); want = SCENE_S if seconds is None else seconds
    if r: n = secs(r, want); return r, n, round(usd_s(r) * n, 6)
    return None, int(OLD_CLIP_S), S("PRICE_KLING_USD", float)

def hero_usd_s():
    """USD for one second of the hero clip model as the estimates count it."""
    r = hero()
    return usd_s(r) if r else S("PRICE_KLING_USD", float) / OLD_CLIP_S

def paid_s(per_shot, shots=1):
    """The seconds PAID for `shots` hero clips that each cover `per_shot` seconds."""
    r = hero()
    return shots * (secs(r, per_shot) if r else int(OLD_CLIP_S))

def args(r, image_url, prompt, seconds):
    """The request body of one clip, built from the model's row and nothing else: the prompt, the start picture in the field the row names, the
    seconds as the row's kind of value, the size where the model has a size field, and the row's own extra fields. Pure."""
    n = secs(r, seconds)
    body = {"prompt": prompt, str(r.get("start") or "image_url"): image_url, "duration": str(n) if str(r.get("dur") or "int") == "str" else n}
    if r.get("res_field") and r.get("res") not in (None, "", "-"): body[str(r["res_field"])] = r["res"]
    body.update(r.get("extra") or {})
    return body

# ------------------------------------------------------------------ the rule
def issues(r, dead=()):
    """Why this row cannot be the hero ([] = it can): it takes a start picture, gives an upright clip for an upright picture, has a price at the size
    it buys, is long enough for a scene, is listed and alive."""
    p = []
    if not str(r.get("start") or "").strip(): p.append("no field for a start picture")
    if str(r.get("shape") or "") not in SHAPES_OK: p.append("nothing says its clip takes the shape of the start picture")
    if usd_s(r) is None or usd_s(r) <= 0: p.append("no price at the size it would be bought in")
    if int(r.get("max_s") or 0) < SCENE_S: p.append(f"its longest clip is under {SCENE_S} seconds")
    if str(r.get("status") or "active") != "active": p.append(f"fal lists it as {r.get('status')}")
    if r.get("schema"): p.append(f"its inputs changed: {r.get('schema')}")
    if r.get("id") in set(dead): p.append("it is failing or retired")
    return p

def pick(rows, line, floor=None, dead=()):
    """THE RULE (pure). Among the rows that can be the hero and have a rank: those that cost at most `line` USD a second (what the month's plan can
    pay) - the highest rank wins; rows whose error bands overlap the best one's are tied, and among the tied the cheaper wins. A row ranked under
    `floor` (the lower end of the band of the model in use) is never picked. When nothing is under the line the plan does not fit: the cheapest
    ranked row is taken and `fits` is False - quality is kept and the month makes fewer Shorts. Returns {row, fits, why, tied, under} or None."""
    ok = [r for r in rows if not issues(r, dead) and r.get("elo") is not None and (floor is None or float(r["elo"]) >= float(floor))]
    if not ok: return None
    under = [r for r in ok if usd_s(r) <= float(line) + 1e-9]
    pool = under or [min(ok, key=lambda r: (usd_s(r), -float(r["elo"])))]
    best = max(pool, key=lambda r: float(r["elo"]))
    tied = [r for r in pool if float(r["elo"]) + float(r.get("ci") or 0) >= float(best["elo"]) - float(best.get("ci") or 0)]
    win = min(tied, key=lambda r: (usd_s(r), -float(r["elo"])))
    why = (f"{win.get('name') or win['id']}: {float(win['elo']):.0f} points on the ranking at USD {usd_s(win):g} a second"
           + (f"; tied by their error bands with {', '.join(str(t.get('name') or t['id']) for t in tied if t is not win)} and cheaper" if len(tied) > 1 else "")
           + (f"; the plan can pay up to USD {float(line):.3f} a second" if under else f"; NO ranked model costs at most USD {float(line):.3f} a second - the month's plan does not fit"))
    return {"row": win, "fits": bool(under), "why": why, "tied": [t["id"] for t in tied], "under": [u["id"] for u in under]}

def floor_of(mid, rows=None):
    """The lower end of the error band of the model in use (None when it has no rank: then every ranked model is at least as good as what is known)."""
    r = row(mid, rows)
    return None if not r or r.get("elo") is None else float(r["elo"]) - float(r.get("ci") or 0)

def choice(dead=(), rows=None):
    """The pick as of now: the table, the line of the month's plan, the Steward's record of failing models. A model that is dead sets no floor."""
    from whatifs import steward as STW, governor as G
    rows = table() if rows is None else rows; cur = str(S("FAL_HERO_MODEL") or "")
    gone = set(dead) | {r["id"] for r in rows if not STW.usable(r["id"])}
    return pick(rows, G.line_usd_s(), None if cur in gone else floor_of(cur, rows), gone)

# ------------------------------------------------------------------ the live listing: what a program CAN read
def _props(doc):
    """The input fields of a model from its OpenAPI document ({} when none is found)."""
    sch = ((doc or {}).get("components") or {}).get("schemas") or {}
    for want_input in (True, False):
        for name, s in sch.items():
            p = s.get("properties") if isinstance(s, dict) else None
            if isinstance(p, dict) and "prompt" in p and (not want_input or str(name).lower().endswith("input")): return p
    return {}

def schema_issues(r, props):
    """(problems, updates): does the model's live schema still take what its row says? A clip length the schema states wins over the row's."""
    p = []; upd = {}
    if not props: return ["no input schema on the listing"], upd
    if str(r.get("start") or "") not in props: p.append(f"no field '{r.get('start')}' for the start picture")
    d = props.get("duration") or {}
    for key, name in (("minimum", "min_s"), ("maximum", "max_s")):
        if isinstance(d.get(key), (int, float)) and int(d[key]) != int(r.get(name) or 0): upd[name] = int(d[key])
    if r.get("res_field"):
        enum = (props.get(str(r["res_field"])) or {}).get("enum")
        if str(r["res_field"]) not in props: p.append(f"no field '{r['res_field']}' for the size")
        elif enum and r.get("res") not in enum: p.append(f"size {r.get('res')} is not offered (it offers {', '.join(map(str, enum))})")
    return p, upd

def refresh(rows=None, save=True):
    """The table against fal's live listing (free; no model is called): is each model still listed and active, does its schema still take the
    start picture, the size and the clip lengths its row says, did the listing's BASE price move (then the row is marked stale: its page must be
    read again - the base price itself is never used, it is wrong for our setting), and - where the ranking's key exists - its newest rank. Returns the rows."""
    from whatifs import scout as SC
    rows = [dict(r) for r in (table() if rows is None else rows)]; before = json.dumps(rows, sort_keys=True); ids = [r["id"] for r in rows]; day = iso()[:10]
    def safe(fn, *a):
        try: return fn(*a)
        except Exception as e: log(f"clip market: {fn.__name__} not read ({scrub(e)[:100]})", "WARN"); return None
    status = safe(SC.fal_status, ids) or {}; prices = safe(SC.fal_prices, ids) or {}; ranks = safe(SC.aa_ranking) or {}
    for r in rows:
        if r["id"] in status: r["status"] = "active" if status[r["id"]] == "active" else str(status[r["id"]])
        doc = safe(SC.fal_schema, r["id"])
        if doc is not None:
            bad, upd = schema_issues(r, _props(doc)); r.update(upd)
            if bad: r["schema"] = "; ".join(bad)[:200]
            else: r.pop("schema", None)
        p = prices.get(r["id"]) or {}
        if isinstance(p.get("unit_price"), (int, float)):
            seen = float(p["unit_price"])
            if r.get("base") is None: r["base"] = seen
            elif abs(seen - float(r["base"])) > STALE_PCT * max(float(r["base"]), 1e-9) and not r.get("stale"):
                r["stale"] = f"fal's listing moved its base price from {float(r['base']):g} to {seen:g} on {day}: read {r.get('page') or 'its page'} again"
        elo = ranks.get(str(r.get("name") or "").lower())
        if isinstance(elo, (int, float)) and float(elo) != float(r.get("elo") or 0): r.update(elo=float(elo), ranked=day)
    if save and json.dumps(rows, sort_keys=True) != before: set_setting("CLIP_MODELS", json.dumps(rows))
    return rows

def review(now=None):
    """Weekly, inside the tool scout: refresh the table, tell the owner ONCE about a row whose listing price moved, and make the pick again. A pick
    other than the model in use is switched by the Model Steward (tab Model_Changes, one message with 'Discuss'). Returns what it found."""
    if not on(): return {}
    from whatifs import steward as STW
    rows = refresh(); cur = str(S("FAL_HERO_MODEL") or ""); out = {"hero": cur, "stale": [r["id"] for r in rows if r.get("stale")]}
    for r in rows:
        if not r.get("stale"): continue
        try:
            from whatifs import notify as NT
            NT.send("clip_price", f"The price list of {r.get('name') or r['id']} changed ({r['stale']}). The estimates keep the price read on {r.get('read')} "
                    "until its page is read again; nothing was switched.", [("OK", "OK")], tier="week", default="ok", expires_h=24 * 6, dedupe_key=f"clipstale|{r['id']}|{r['stale'][:60]}")
        except Exception as e: log(f"clip market: the owner was not told about a moved price ({scrub(e)[:80]})", "WARN")
    p = choice(rows=rows)
    if not p: log("clip market: no model in the table can be the hero - the model in use stays", "WARN"); return dict(out, pick=None)
    out.update(pick=p["row"]["id"], fits=p["fits"], why=p["why"])
    five = usd(p["row"], SCENE_S)
    if p["row"]["id"] != cur: STW.switch("hero", {"id": p["row"]["id"], "usd": five}, "picked by value: " + p["why"], tier="week")
    elif abs(S("PRICE_KLING_USD", float) - five) > 1e-9: set_setting("PRICE_KLING_USD", str(five))
    return out

def preflight():
    """(ok, words) before a production job: the hero model has a row, fal lists it as active and its schema still takes what the row says."""
    if not on(): return True, "the clip market is off (CLIP_VALUE_ON)"
    from whatifs import scout as SC
    mid = str(S("FAL_HERO_MODEL") or ""); r = row(mid)
    if r is None: return False, f"{mid} has no row in CLIP_MODELS: its price per second and its inputs are not known"
    try:
        st = (SC.fal_status([mid]) or {}).get(mid, "missing")
        if st != "active": return False, f"fal lists {mid} as {st}"
        bad, _upd = schema_issues(r, _props(SC.fal_schema(mid)))
        if bad: return False, f"{mid}: " + "; ".join(bad)
    except Exception as e: return False, f"fal's listing was not read ({scrub(e)[:100]})"
    return True, f"{mid} is listed, active and takes the inputs its row says"

# ------------------------------------------------------------------ a measured guard
def _size(path):
    import cv2
    if str(path).lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        im = cv2.imread(path); return (im.shape[1], im.shape[0]) if im is not None else None
    cap = cv2.VideoCapture(path); w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0); cap.release()
    return (w, h) if w and h else None

def shape_ok(clip, picture):
    """(ok, words): did the clip come back in the shape of its start picture? Measured on the two files (one page does not say where its model
    takes the shape from). A file that cannot be measured is not judged."""
    a, b = _size(clip), _size(picture)
    if not a or not b: return True, "not measured"
    ra, rb = a[0] / a[1], b[0] / b[1]
    return abs(ra - rb) <= SHAPE_TOL * rb, f"the clip is {a[0]} x {a[1]}, its start picture {b[0]} x {b[1]}"
