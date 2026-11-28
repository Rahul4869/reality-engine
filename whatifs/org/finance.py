"""Finance (D11): the money is his own - the Claude credit's lane and meter, one boost that ends by itself, the daily watch. See docs/CURRENT/SYSTEM.md."""
# v12 V4: the credit is a dated relief with a meter of our own (credit, cover, lane), one boost that ends by itself (boost), and D11's daily run (watch):
# the month's fit, the month's cover kept, an overrun as a memo to Operations. The cap stays a breaker: the lane covers at most CREDIT_COVER_MONTH_MAX_INR a month.
from __future__ import annotations
import json, time
import datetime as dt
from whatifs.core import S, log, store, iso, now_utc, set_setting, scrub

COVER_TTL_S = 600                     # tab Cost_Log is read at most once in this many seconds a process (forget() for tests; the family of open issue 214)
SUMMARY_ITEM = "cost_lines_summary"      # costguard.reconcile's row; models.py writes another summary row (ai_per_video_summary) that holds no cost lines (V4's repair C23)
_cache = {}

def on():
    """Finance is part of the CEO (STRATEGY_ON); FALSE = exactly the code V4 is built on (the credit a view, month_spend in every reader)."""
    return S("STRATEGY_ON", bool)

def forget(): _cache.clear()

def _cost_rows():
    t = time.time(); c = _cache.get("rows")
    if c and t - c[0] < COVER_TTL_S: return c[1]
    rows = store().rows("Cost_Log"); _cache["rows"] = (t, rows); return rows

def _f(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0

def _held():
    try: d = json.loads(S("CLAUDE_CREDIT_COVERED") or "{}")
    except (TypeError, ValueError): d = {}
    return d if isinstance(d, dict) else {}

def lines(now=None):
    """v12 V4b step 10 (memo 3.10, LINES AS DATA): the credit's lines sorted by `until`: CLAUDE_CREDIT_LINES (JSON [{usd, from, until}], his cell) or, with it
    empty, V4's three cells as ONE line. Each: {usd, from, until, amount_inr}. A line that does not parse or has no amount or date is dropped."""
    raw = str(S("CLAUDE_CREDIT_LINES") or "").strip(); rate = S("USD_INR", float) or 99.0; out = []
    try: data = json.loads(raw) if raw else [{"usd": S("CLAUDE_CREDIT_USD_MONTH", float), "from": S("CLAUDE_CREDIT_FROM"), "until": S("CLAUDE_CREDIT_UNTIL")}]
    except (TypeError, ValueError): data = []
    for d in data if isinstance(data, list) else []:
        try: usd = max(0.0, float(d.get("usd") or 0)); frm = str(d.get("from") or "").strip()[:10]; until = str(d.get("until") or "").strip()[:10]
        except (AttributeError, TypeError, ValueError): continue
        if usd > 0 and frm and until: out.append({"usd": usd, "from": frm, "until": until, "amount_inr": round(usd * rate, 2)})
    return sorted(out, key=lambda l: (l["until"], l["from"]))

def _spend(now):
    """Each meter row (provider anthropic, not a summary) is charged to the line with the OLDEST expiry that is open on the row's day (our allocation: the
    provider's page does not order two monthly lines). -> (lines, spent_inr per line, spent before this month per line)."""
    L = lines(now); first = now.strftime("%Y-%m-01"); sp = [0.0] * len(L); bf = [0.0] * len(L)
    for r in _cost_rows():
        if r.get("provider") != "anthropic" or r.get("basis") == "summary": continue
        day = str(r.get("ts") or "")[:10]
        for i, l in enumerate(L):                                                   # sorted by until: the first line open on that day is the oldest expiry
            if l["from"] <= day <= l["until"]:
                v = _f(r.get("inr")); sp[i] += v; bf[i] += v if day < first else 0.0; break
    return L, sp, bf

def _credit_of_lines(now):
    """credit()'s sums over the lines OPEN today (the shape V4's readers use): the amount, the spend charged to them, the covered part of this month; `until` = the
    nearest end among them (what lapses first). The day after every `until` nothing is open."""
    L, sp, bf = _spend(now); today = now.strftime("%Y-%m-%d"); floor = S("CREDIT_FLOOR_INR", float)
    op = [i for i, l in enumerate(L) if l["from"] <= today <= l["until"]]
    amount = sum(L[i]["amount_inr"] for i in op); spent = sum(sp[i] for i in op); before = sum(bf[i] for i in op); left = amount - spent
    usable = max(0.0, amount - floor); covered = max(0.0, min(spent, usable) - min(before, usable))
    until = min((L[i]["until"] for i in op), default=(L[-1]["until"] if L else ""))
    return {"open": bool(on() and op and left >= floor), "amount_inr": round(amount, 2), "spent_inr": round(spent, 2), "left_inr": round(left, 2),
            "covered_month": round(covered, 2), "until": until}

def line_state(now=None):
    """v12 V4b step 10 (THE CURVE, THE REPORT): per line not yet ended {usd, from, until, amount_inr, open, spent_inr, left_inr, target_inr, behind_inr, will_lapse_inr,
    state}. target = amount x elapsed / total x CREDIT_TARGET_PCT / 100; behind_inr = target - spent (negative = ahead); state "behind"/"ahead" only beyond
    CREDIT_CURVE_BAND_PCT of the amount, else "on". will_lapse = max(0, left - CREDIT_FLOOR_INR - day_est x days_left): day_est = the line's own spend / the days
    elapsed since its `from` (0 on its first day) - the meter's measured pace, never a forecast."""
    now = now or now_utc(); L, sp, _ = _spend(now); today = now.date(); floor = S("CREDIT_FLOOR_INR", float); out = []
    for l, s in zip(L, sp):
        try: d0, d1 = dt.date.fromisoformat(l["from"]), dt.date.fromisoformat(l["until"])
        except ValueError: continue
        if d1 < today: continue
        total = max(1, (d1 - d0).days); elapsed = min(total, max(0, (today - d0).days)); days_left = max(0, (d1 - today).days)
        amount = l["amount_inr"]; left = amount - s; target = amount * elapsed / total * S("CREDIT_TARGET_PCT", float) / 100.0
        day_est = s / elapsed if elapsed else 0.0; band = amount * S("CREDIT_CURVE_BAND_PCT", float) / 100.0
        out.append({**l, "open": d0 <= today <= d1, "spent_inr": round(s, 2), "left_inr": round(left, 2), "target_inr": round(target, 2), "behind_inr": round(target - s, 2),
                    "will_lapse_inr": round(max(0.0, left - floor - day_est * days_left), 2),
                    "state": "behind" if target - s > band else ("ahead" if s - target > band else "on")})
    return out

def lapse_lines(now=None):
    """v12 V4b step 10 (memo 3.10 THE REPORT): one sentence per OPEN line - what WILL lapse at the measured pace, "Claude credit <until>: Rs U used of Rs A; at this pace
    Rs L will lapse on that day."; [] while the lane is off. The weekly line (strategy.weekly), the Money tab's field (dash) and the morning message (digests.head) all read THIS."""
    return [f"Claude credit {ls['until']}: Rs {ls['spent_inr']:.0f} used of Rs {ls['amount_inr']:.0f}; at this pace Rs {ls['will_lapse_inr']:.0f} will lapse on that day."
            for ls in (line_state(now) if on() else []) if ls["open"]]

_SWEPT = set()                      # (until, job) the sweep already ran or failed in this process: a job that raised is not tried again in that line

def sweep(now=None):
    """v12 V4b step 10 (THE SWEEP): in a line's last CREDIT_SWEEP_H hours, while its left stays above CREDIT_FLOOR_INR (not with CREDIT_TRUE_ZERO_OK TRUE), RUN in
    this order (a) premise.refill_bench(force=True) and (b) preprod.run() - WITHOUT force, so it obeys the pair rule and its one waiting draft. Both on their own
    half-price roads. Returns the jobs run ('<until>:<job>'); a job that raised is logged and never tried again in that line."""
    now = now or now_utc(); ran = []
    if not on(): return ran
    zero = S("CREDIT_TRUE_ZERO_OK", bool); floor = S("CREDIT_FLOOR_INR", float)
    for ls in line_state(now):
        if not ls["open"]: continue
        end = dt.datetime.fromisoformat(ls["until"] + "T23:59:59+00:00"); hours = (end - now).total_seconds() / 3600.0
        if not 0 <= hours <= S("CREDIT_SWEEP_H", float): continue
        for job in ("refill_bench", "preprod"):
            tag = (ls["until"], job)
            if tag in _SWEPT: continue
            forget(); cur = next((x for x in line_state(now) if x["until"] == ls["until"]), ls)
            if not zero and cur["left_inr"] <= floor: break
            _SWEPT.add(tag)
            try:
                if job == "refill_bench":
                    from whatifs import premise as PRM
                    PRM.refill_bench(force=True)
                else:
                    from whatifs import preprod as PRE
                    PRE.run()
                ran.append(f"{ls['until']}:{job}")
            except Exception as e: log(f"finance: the sweep job {job} of the line ending {ls['until']} raised and is not tried again: {scrub(e)[:120]}", "WARN")
    return ran

def credit(now=None):
    """The Claude credit's meter (ours: the balance is not readable). {open, amount_inr, spent_inr, left_inr, covered_month, until}: the Claude rows
    (provider anthropic, not a summary) dated inside [CLAUDE_CREDIT_FROM, CLAUDE_CREDIT_UNTIL]; covered_month = what of them fell in this month
    and inside the usable part (the amount less CREDIT_FLOOR_INR). Open = the CEO on, an amount, both dates set, today inside, and at least the
    floor left. v12 V4b step 10: with CLAUDE_CREDIT_LINES set, the same figures are the sums over the lines open today."""
    now = now or now_utc()
    if str(S("CLAUDE_CREDIT_LINES") or "").strip(): return _credit_of_lines(now)
    amount = max(0.0, S("CLAUDE_CREDIT_USD_MONTH", float)) * (S("USD_INR", float) or 99.0)
    frm, until = str(S("CLAUDE_CREDIT_FROM") or "").strip()[:10], str(S("CLAUDE_CREDIT_UNTIL") or "").strip()[:10]
    floor = S("CREDIT_FLOOR_INR", float); today = now.strftime("%Y-%m-%d"); first = now.strftime("%Y-%m-01")
    rows = [r for r in _cost_rows() if r.get("provider") == "anthropic" and r.get("basis") != "summary" and frm <= str(r.get("ts") or "")[:10] <= until] if (amount > 0 and frm and until) else []
    spent = sum(_f(r.get("inr")) for r in rows); before = sum(_f(r.get("inr")) for r in rows if str(r.get("ts") or "")[:10] < first)
    left = amount - spent; usable = max(0.0, amount - floor)
    covered = max(0.0, min(spent, usable) - min(before, usable))
    is_open = on() and amount > 0 and bool(frm and until) and frm <= today <= until and left >= floor
    return {"open": bool(is_open), "amount_inr": round(amount, 2), "spent_inr": round(spent, 2), "left_inr": round(left, 2), "covered_month": round(covered, 2), "until": until}

def lane(now=None):
    """The credit's figures while its lane is open, else None (no Sheet read with the CEO off)."""
    if not on(): return None
    c = credit(now); return c if c["open"] else None

def cover(now=None):
    """What the Claude credit paid of THIS month's list-price spend: 0.0 with STRATEGY_ON FALSE, else the larger of the figure the month already holds
    (CLAUDE_CREDIT_COVERED: watch writes it and never lowers it) and the meter's covered_month, at most CREDIT_COVER_MONTH_MAX_INR."""
    if not on(): return 0.0
    now = now or now_utc(); held = _f(_held().get(now.strftime("%Y-%m")))
    return min(S("CREDIT_COVER_MONTH_MAX_INR", float), max(held, credit(now)["covered_month"]))

def boost(key, now=None):
    """A lever that ends by itself: the cell (THINK_BOOST_VARIANTS) while the credit's lane is open and Claude may be used, else 0 - the READER closes
    the boost on the end date even if no ticket ever does."""
    if not on(): return 0
    from whatifs import governor as G
    try: return max(0, S(key, int)) if (lane(now) and G.claude_allowed()) else 0
    except Exception as e:
        log(f"finance: the boost {key} was not read: {scrub(e)[:120]}", "WARN"); return 0

# ------------------------------------------------------------------ D11's daily run
def _summary(row):
    """(kind, {over, unlisted, ...} or None) of a Cost_Log summary row: its role is '<kind>: <JSON>' cut at 900 characters (costguard.reconcile)."""
    kind, sep, js = str(row.get("role") or "").partition(": ")
    try: d = json.loads(js) if sep else None
    except (TypeError, ValueError): d = None
    return kind.strip(), (d if isinstance(d, dict) else None)

def _overrun_memo(row, d, to):
    ep = str(row.get("episode_id") or "?")
    if d is None: what = f"the cost summary of {ep} is cut and cannot be read"
    else: what = "; ".join([str(x) for x in (d.get("over") or [])] + ([f"paid with no line: {', '.join(str(x) for x in d.get('unlisted'))}"] if d.get("unlisted") else []))
    return {"type": "problem_memo", "from_dept": "D11", "to_depts": [to], "subject": f"A video cost more than its estimate: {ep}",
            "body": {"what_failed": what[:400], "where": f"Cost_Log:{ep}", "attempt": 1, "error_class": "cost_overrun"},
            "evidence": [{"source": f"Cost_Log:{ep}", "date": str(row.get("ts") or iso())[:10], "type": "own data"}], "dedupe_key": f"overrun|{ep}",
            "done_when": "the estimate's lines carry it and the next video of that kind has a clean summary"}

def overruns(st=None, now=None):
    """Every summary row newer than FINANCE_SEEN_TS: an overrun (a non-empty `over` or `unlisted`, or a JSON that does not parse) becomes a problem memo
    from D11 to Operations (D12); a later CLEAN summary of the same kind resolves an open one (repair_verified, ref Cost_Log:<episode>).
    Returns (memos to send, how many were resolved, the newest ts read)."""
    from whatifs.org import memos as MEM, registry as REG
    st = st or store(); now = now or now_utc(); seen = str(S("FINANCE_SEEN_TS") or "")
    rows = st.rows("Cost_Log"); new = sorted((r for r in rows if r.get("basis") == "summary" and r.get("item") == SUMMARY_ITEM and str(r.get("ts") or "") > seen), key=lambda r: str(r.get("ts") or ""))
    kind_of = {}
    for r in rows:
        if r.get("basis") == "summary" and r.get("item") == SUMMARY_ITEM: kind_of[str(r.get("episode_id") or "")] = _summary(r)[0]
    to = "D12" if REG.takes("D12", "problem_memo") else "D8"
    out, resolved = [], 0
    for r in new:
        kind, d = _summary(r); ep = str(r.get("episode_id") or "")
        if d is None or d.get("over") or d.get("unlisted"):
            out.append(_overrun_memo(r, d, to)); continue
        for m in MEM.find(st, type="problem_memo", from_dept="D11"):
            k = str(m.get("dedupe_key") or "")
            if not k.startswith("overrun|") or kind_of.get(k.split("|", 1)[1]) != kind or str(m.get("created") or "") > str(r.get("ts") or ""): continue
            try: MEM.resolve(m["id"], "D11", "repair_verified", f"Cost_Log:{ep}", "a later video of the same kind has a clean cost summary", st, now); resolved += 1
            except Exception as e: log(f"finance: the overrun memo {m['id']} was not closed: {scrub(e)[:120]}", "WARN")
    return out, resolved, (str(new[-1].get("ts") or "") if new else seen)

def watch(brief):
    """D11's run `watch` (cli.strategy_round, in the daily learning job): (a) the month's fit for the plan in force as measures; (b) the month's cover
    written into CLAUDE_CREDIT_COVERED (never lowered); (c) every overrun as a memo to Operations. Every inbound memo is dispositioned."""
    from whatifs.org.runner import Out
    from whatifs import governor as G
    brief.take()                                                                   # the runner's contract: a department run takes its playbook (D11 decides by code)
    now = now_utc(); st = store(); mk = now.strftime("%Y-%m")
    fit = G.month_fit(G.max_long_videos(), S("SHORTS_PER_MONTH", int), now=now)
    c = credit(now); held = _held()
    if c["covered_month"] > _f(held.get(mk)):
        held[mk] = c["covered_month"]; set_setting("CLAUDE_CREDIT_COVERED", json.dumps(held, sort_keys=True))
    memos, resolved, seen = overruns(st, now)
    if seen: set_setting("FINANCE_SEEN_TS", seen)
    swept = sweep(now)                                                              # v12 V4b step 10: in a line's last CREDIT_SWEEP_H hours (the daily learning job: nobody waits)
    acts = {m["id"]: ("deferred", f"read by Finance: a {m.get('type') or 'memo'} is counted in the month's fit") for m in getattr(brief, "memos", None) or []}
    return Out(output={"fit": fit, "credit": c, "overruns": len(memos), "resolved": resolved, "swept": swept}, memos=memos, memo_actions=acts,
               measures={"fit_need_inr": fit["need_inr"], "fit_free_inr": fit["free_inr"], "fits": int(fit["fits"]), "credit_open": int(c["open"]),
                         "covered_month_inr": round(c["covered_month"], 0), "overrun_memos": len(memos), "overruns_resolved": resolved})
