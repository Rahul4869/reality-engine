"""The scoreboard: the Partner Program's own numbers every morning, each beside the pace its bar needs. See docs/CURRENT/SYSTEM.md."""
# v12 V4 (D10): subscribers, the Shorts views that count in 90 days, the long watch hours of 12 months; one row a day in tab Scoreboard; the bars are data (YPP_BARS).
from __future__ import annotations
import json, math, datetime as dt
from whatifs.core import S, log, store, iso, now_utc, FAKE, scrub, DEFAULTS

SRC = "YouTube Analytics (ypp.progress) + YouTube Data channels.statistics"
PACE_DAYS = 28                                   # a subscriber pace needs a reading at least this many days old
TEN_YEARS = 3650

def on():
    """The scoreboard is part of the CEO (STRATEGY_ON); FALSE = exactly the code V4 is built on (no row, no line)."""
    return S("STRATEGY_ON", bool)

def _day(now): return (now or now_utc()).astimezone(dt.timezone.utc).date()

def _subs():
    """The channel's subscriber count (exact under 1,000), or None with a WARN. The signed-in channel (`mine=true`): no name or id in code."""
    if FAKE: return None
    try:
        import requests
        from whatifs import publish
        r = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "statistics", "mine": "true"}, headers=publish.gheaders(), timeout=30)
        items = (r.json() or {}).get("items") or []
        return int(items[0]["statistics"]["subscriberCount"])
    except Exception as e:
        log(f"scoreboard: the subscriber count was not read: {scrub(e)[:120]}", "WARN"); return None

def read(now=None):
    """{subs, hours, shorts_90, at}: the numbers the Partner Program counts, as YouTube's APIs give them today."""
    from whatifs import ypp
    p = ypp.progress(now)
    hours = round(p["hours"] * S("SCOREBOARD_ELIGIBLE_PCT", float) / 100, 1)
    return {"subs": _subs(), "hours": hours, "shorts_90": p["shorts_views_90d"], "at": iso()}

def keep(now=None):
    """One row for the UTC date (a second call on that date changes nothing). Called every day by the daily learning job (manage.learn)."""
    if not on(): return None
    day = _day(now).isoformat(); st = store()
    if any(str(r.get("date") or "") == day for r in st.rows("Scoreboard")): return None
    r = read(now)
    row = {"date": day, "subs": "" if r["subs"] is None else r["subs"], "hours": r["hours"], "shorts_90": r["shorts_90"], "src": SRC}
    st.append("Scoreboard", [row]); return row

def _bars():
    try: b = json.loads(S("YPP_BARS") or "[]")
    except Exception: b = []
    return [x for x in b if isinstance(x, dict)] or json.loads(DEFAULTS["YPP_BARS"][0])

def bars(now=None):
    """The bar of today: the first entry whose `until` is empty or not yet past."""
    today = _day(now).isoformat(); b = _bars()
    return next((x for x in b if not str(x.get("until") or "") or str(x["until"]) >= today), b[-1])

def _num(v, cast):
    try: return cast(v) if str(v).strip() != "" else None
    except Exception: return None

def _rows():
    return sorted((r for r in store().rows("Scoreboard") if str(r.get("date") or "")), key=lambda r: str(r["date"]))

def sub_pace(rows, now=None):
    """Subscribers a day: (today's subs - the subs of the newest row dated at least 28 days before today) / the days between; None without both."""
    today = _day(now)
    cur = next((_num(r.get("subs"), int) for r in rows if str(r.get("date")) == today.isoformat()), None)
    if cur is None: return None
    old = [r for r in rows if _num(r.get("subs"), int) is not None and str(r.get("date")) <= (today - dt.timedelta(days=PACE_DAYS)).isoformat()]
    if not old: return None
    o = old[-1]; days = (today - dt.date.fromisoformat(str(o["date"]))).days
    return (cur - _num(o["subs"], int)) / days

def eta(v, bar, pace):
    """Days to the bar at this pace: 0 when reached; None without a positive pace."""
    if v >= bar: return 0
    if pace is None or pace <= 0: return None
    return math.ceil((bar - v) / pace)

def line(now=None):
    """The first line of his brief (both briefs, a DEMO brief too): the bars in the Partner Program's own numbers and the pace each needs."""
    if not on(): return ""
    now = now or now_utc(); rows = _rows()
    if not rows: return "Scoreboard: no reading yet (the first comes with the daily learning job)."
    r = rows[-1]; bar = bars(now); b = _bars(); later = b[b.index(bar) + 1] if bar in b and b.index(bar) + 1 < len(b) else None
    subs = _num(r.get("subs"), int); hours = _num(r.get("hours"), float) or 0.0; shorts = _num(r.get("shorts_90"), int) or 0
    bar_subs, bar_s, bar_h = int(bar["subs"]), int(bar["shorts"]), int(bar["hours"])
    if subs is None: head = "subscribers: no reading"
    else:
        pace = sub_pace(rows, now); n = eta(subs, bar_subs, pace)
        if n == 0: P = "reached"
        elif pace is None: P = "no pace yet: 28 days of readings are needed"
        elif n is None or n > TEN_YEARS: P = "more than 10 years at this pace"          # a pace of 0 or less never reaches the bar (DESIGN QUESTION D-SB2 of the typing)
        else: P = f"about {n:,} days at this pace"
        head = f"{subs} of {bar_subs:,} subscribers ({P})"
    pct = S("SCOREBOARD_ELIGIBLE_PCT", float); E = "" if pct == 100 else f" (counted at {pct:g}% eligible)"
    R = ""
    if later and str(bar.get("until") or ""):
        rise = dt.date.fromisoformat(str(bar["until"])) + dt.timedelta(days=1)
        R = f" The bars rise on {rise:%d %b %Y}: {int(later['hours']):,} hours or {int(later['shorts']):,} Shorts views."
    return (f"Scoreboard: {head} | Shorts views that count: {shorts:,} of {bar_s:,} in 90 days - {shorts / 90:,.0f} a day, the bar needs {bar_s / 90:,.0f}"
            f" | long watch hours: {hours:.1f} of {bar_h:,} in 12 months - {hours / 365:.2f} a day, the bar needs {bar_h / 365:.1f}{E}.{R}")
