"""Keeps the channel safe and the owner informed without noise (policy rescue and related watch duties). See docs/CURRENT/SYSTEM.md."""
from __future__ import annotations
import csv, datetime as dt, io, json, os, statistics, zipfile
from whatifs.core import S, log, store, iso, now_utc, parse_iso, TABS, FAKE, scrub, set_setting

EXPIRY_SEED = [("Claude Max plan (back to Pro)", "2026-12-10", "Check the pipeline's Anthropic key still has a prepaid balance"),
               ("Google AI Pro (Jio)", "2028-03-13", "Keep the Jio plan active; renew AI Pro or remove GEMINI_CREDIT_USD_MONTH"),
               ("GitHub merge key (GH_MERGE_TOKEN)", "", "GitHub -> Settings -> Developer settings -> Fine-grained tokens -> Regenerate; paste as the secret"),
               ("Claude Code key (CC_OAUTH_TOKEN)", "", "Run 'claude setup-token' (Codespaces or laptop) and paste as the secret"),
               ("Relay key (GH_DISPATCH_TOKEN, Cloudflare)", "", "Regenerate the fine-grained token; paste into the Cloudflare Worker secret"),
               ("Meta WhatsApp token (WA_TOKEN)", "", "Business Settings -> System users -> Generate token; paste as the secret")]

# ------------------------------------------------------------------ Policy Rescue
def cadence_words():
    """The channel's real output, read from the settings (a prompt must describe the channel as it is, not as it once was)."""
    from whatifs import governor as G
    n = G.long_videos_per_week(); sh = int(S("SHORTS_PER_DAY", float) * 7 + 0.5) if S("SHORTS_TRACK_ON", bool) else 0
    return "about " + str(n) + (" long video" if n == 1 else " long videos") + " and " + str(sh) + " Shorts a week"

def policy_rescue(items):
    from whatifs import notify as NT
    note = ""
    try:
        from whatifs.models import ask
        note = str(ask("policy_rescue", "You protect a faceless, AI-assisted science YouTube channel with original scripts, recurring characters, honest AI labels and "
                       + cadence_words() + ". In 4 short plain sentences: what this platform change means for it, what to change, and whether "
                       "to stay paused. No jargon.", json.dumps(items)[:4000], want_json=False, max_tokens=500, fake_key="policy_rescue") or "").strip()[:900]
    except Exception as e: log(f"policy impact note skipped: {scrub(e)[:100]}", "WARN")
    return NT.send("policy", "Platform policy change found (publishing paused 7 days): " + "; ".join(str(i.get("change"))[:160] for i in items) + (f"<br><b>What it means:</b> {note}" if note else ""),
                   [("Discuss", "DISCUSS policy"), ("Build fix", "BUILDFIX policy"), ("Resume now", "RESUME")], tier="now", urgent=True,
                   default="stays paused until the date in Settings", expires_h=24 * 7, dedupe_key="policy|" + now_utc().strftime("%Y-%m-%d"))

def _policy_answer(row, choice):
    c = str(choice).upper()
    if c == "RESUME":
        set_setting("PAUSED_UNTIL", ""); set_setting("PAUSED", "FALSE"); return "resumed"
    if c.startswith("BUILDFIX"):
        from whatifs.builds import request_build
        return "fix build started" if request_build("POLICY FIX: " + str(row.get("text", ""))[:3000] + " Adapt the pipeline so it complies; keep every K-rule; tests.", "feature") else "build could not start"
    return "recorded"

# ------------------------------------------------------------------ Expiry calendar
def ensure_expiry_seed():
    st = store(); have = {r.get("item") for r in st.rows("Expiry_Calendar")}
    new = [{"item": n, "expires": d, "renew": r, "reminded": ""} for n, d, r in EXPIRY_SEED if n not in have]
    if new: st.append("Expiry_Calendar", new)

def expiry_check(now=None):
    """14 days before = 'week' card; 3 days before = 'now' card (urgent); each once. Returns the cards sent."""
    from whatifs import notify as NT
    now = now or now_utc(); st = store(); sent = []
    for r in st.rows("Expiry_Calendar"):
        try: d = dt.date.fromisoformat(str(r.get("expires") or ""))
        except ValueError: continue
        left = (d - now.date()).days; done = str(r.get("reminded") or "")
        for days, tier, tag in ((14, "week", "14"), (3, "now", "3")):
            if 0 <= left <= days and tag not in done.split(","):
                NT.send("expiry", f"{r['item']} expires on {d:%d %b %Y} ({left} days). How to renew: {r.get('renew', '')}", [("Done", "RENEWED")], tier=tier, urgent=tier == "now",
                        default="reminder again nearer the date" if tier == "week" else "it may stop working on that day", expires_h=72, dedupe_key=f"expiry|{r['item']}|{tag}")
                st.update("Expiry_Calendar", "item", r["item"], {"reminded": ",".join([x for x in done.split(",") if x] + [tag])}); sent.append(f"{r['item']}:{tag}")
                break
    return sent

# ------------------------------------------------------------------ Weekly backup
def backup(now=None):
    """All tabs as CSV in one zip, uploaded privately to Drive; the newest BACKUP_KEEP kept (older ones deleted). Returns the file name or ''."""
    if not S("SHEET_BACKUP_ON", bool): return ""
    now = now or now_utc(); name = f"reality_engine_backup_{now:%G-W%V}.zip"; st = store()
    if any(r.get("name") == name for r in st.rows("Backups")): return ""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for tab, cols in TABS.items():
            if tab in ("WA_Chat",): continue                        # the private chat is not copied around
            s = io.StringIO(); w = csv.DictWriter(s, fieldnames=list(cols), extrasaction="ignore"); w.writeheader()
            for r in st.rows(tab): w.writerow({k: r.get(k, "") for k in cols})
            z.writestr(f"{tab}.csv", s.getvalue())
    path = os.path.join(os.environ.get("WI_WORK", "work"), name); os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "wb").write(buf.getvalue())
    fid = "FAKE_" + name
    if not FAKE:
        from whatifs import publish as PUB
        fid, _url = PUB.drive_upload(path, name, public=False)
    st.append("Backups", [{"ts": iso(), "name": name, "file": fid}])
    rows = st.rows("Backups"); keep = S("BACKUP_KEEP", int)
    for old in rows[:-keep] if len(rows) > keep else []:
        if not FAKE and str(old.get("file", "")).strip() and not str(old.get("file")).startswith("FAKE"):
            try:
                from whatifs import publish as PUB; PUB.drive_delete(old["file"])
            except Exception as e: log(f"old backup not deleted: {scrub(e)[:80]}", "WARN")
        st.update("Backups", "name", old["name"], {"file": "deleted"})
    log(f"Sheet backup saved ({name})"); return name

# ------------------------------------------------------------------ Advisor (weekly money + growth card)
def advisor(now=None):
    from whatifs import governor as G, notify as NT
    now = now or now_utc()
    try:
        from whatifs.costguard import month_spend
        spent = month_spend()
    except Exception: spent = 0.0
    eps = [e for e in store().rows("Episodes") if str(e.get("slot_et", "")).startswith(now.strftime("%Y-%m")) and e.get("yt_id")]
    per_video = spent / len(eps) if eps else 0.0
    tips = []
    sp = [r for r in store().rows("Specials") if r.get("views_7d") not in (None, "")]
    if len(sp) >= 2:
        last2 = [float(r["views_7d"]) for r in sp[-2:]]; med = statistics.median([float(r["views_7d"]) for r in sp]) if len(sp) >= 3 else None
        if med and all(v < 0.5 * med for v in last2): tips.append("The last two specials did less than half their usual views: try a different format or occasion next.")
    sl = store().rows("Slop_Scores")[-3:]
    if sl and statistics.mean(float(r.get("slop") or 0) for r in sl) > S("SLOP_WARN", float): tips.append("The AI-slop risk stayed high for 3 videos: switch on one Visual Lab idea this week.")
    rules = 0
    try:
        from whatifs import microscope as MS; rules = len(MS.active_rules())
    except Exception: pass
    if rules: tips.append(f"{rules} retention rule(s) from your own data are guiding the writers now (see the Lab tab).")
    text = (f"This week: spend Rs {spent:.0f} of Rs {G.cap_inr():.0f} ({G.budget_mode()} mode)"
            + (f", about Rs {G.credit_cover_inr():.0f} covered by free credits" if G.credit_cover_inr() > 0 else "")
            + (f"; about Rs {per_video:.0f} per long video" if per_video else "") + ". " + " ".join(tips[:2]))
    return NT.send("advisor", text, [("Discuss", "DISCUSS advisor"), ("OK", "OK")], tier="week", default="noted", expires_h=24 * 6, dedupe_key=f"advisor|{now:%G-W%V}")

# ------------------------------------------------------------------ Health (dashboard)
def last_runs():
    out = {}
    for r in store().rows("Run_Log")[-400:]:
        j = r.get("job") or ""
        if not j: continue
        o = out.setdefault(j, {"workflow": j, "ok": True, "at": r.get("ts")})
        o["at"] = r.get("ts")
        if str(r.get("level", "")).upper() == "ERROR": o["ok"] = False
    return list(out.values())[-8:]

def expiring():
    out = []
    for r in store().rows("Expiry_Calendar"):
        if r.get("expires"): out.append({"name": r.get("item"), "date": r.get("expires")})
    return sorted(out, key=lambda x: x["date"])[:6]

def register():
    from whatifs import notify as NT
    NT.register("policy", on_answer=_policy_answer)
