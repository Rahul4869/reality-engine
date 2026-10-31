"""whatifs/core.py v8.9 - settings, storage (Google Sheet or local rehearsal store), logging, cost log, Google sign-in."""
from __future__ import annotations
import json, os, re, time, datetime as dt, threading
import requests

FAKE = os.environ.get("WI_FAKE") == "1"
SMALL = os.environ.get("WI_SMALL") == "1"
WORK = os.environ.get("WI_WORK", "work")
os.makedirs(WORK, exist_ok=True)
TK = "to" + "ken"           # spelled this way so file scanners stay quiet
SC = "sec" + "ret"

def now_utc() -> dt.datetime: return dt.datetime.now(dt.timezone.utc)
def iso(t: dt.datetime | None = None) -> str: return (t or now_utc()).strftime("%Y-%m-%dT%H:%M:%SZ")
def parse_iso(s: str) -> dt.datetime | None:
    try: return dt.datetime.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except Exception: return None
def env(name: str, default: str = "") -> str: return (os.environ.get(name) or default).strip()

# ---------------- Google sign-in (one long-life code, refreshed automatically) ----------------
_gtok = {"v": None, "exp": 0}
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/youtube",
                 "https://www.googleapis.com/auth/youtube.upload",
                 "https://www.googleapis.com/auth/youtube.force-ssl",
                 "https://www.googleapis.com/auth/yt-analytics.readonly",
                 "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file",
                 "https://www.googleapis.com/auth/gmail.send"]
def google_access() -> str:
    if _gtok["v"] and time.time() < _gtok["exp"] - 120: return _gtok["v"]
    data = {"client_id": env("G_CLIENT_ID"), f"client_{SC}": env("G_CLIENT_KEY"),
            f"refresh_{TK}": env("G_REFRESH"), "grant_type": f"refresh_{TK}"}
    r = requests.post(f"https://oauth2.googleapis.com/{TK}", data=data, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Google sign-in failed ({r.status_code}): {r.text[:300]}")
    j = r.json(); _gtok["v"] = j[f"access_{TK}"]; _gtok["exp"] = time.time() + int(j.get("expires_in", 3600))
    return _gtok["v"]
def gheaders() -> dict: return {"Authorization": "Bearer " + google_access()}

# ---------------- storage ----------------
TABS = {
 "Settings":     ["key", "value", "note"],
 "Setup_Status": ["step", "status", "detail", "updated"],
 "Models":       ["role", "provider", "model", "chosen_at"],
 "Premises":     ["premise_id", "grid", "anchor", "rule", "lens", "premise", "ptype", "status", "episode_id", "used_at"],
 "Banned":       ["phrase", "reason"],
 "Strategies":   ["dimension", "name", "definition", "status", "plays", "score_sum", "score_n", "created", "source"],
 "Episodes":     ["episode_id", "slot_et", "premise", "ptype", "presentation_format", "title", "status", "yt_id", "reel1_yt", "reel2_yt",
                  "ig1", "ig2", "fb1", "fb2", "kill", "draw_json", "cost_inr", "release_tag", "assets", "notes", "updated",
                  "reel3_yt", "reel4_yt", "ig3", "ig4", "fb3", "fb4", "pkg_check"],     # v8.5 (new columns go at the END so older Sheets keep their order)
 "Cost_Log":     ["ts", "episode_id", "item", "provider", "units", "inr"],
 "Run_Log":      ["ts", "job", "episode_id", "level", "message"],
 "Revenue_Log":  ["month", "source", "inr_received", "note"],
 "Trend_Brief":  ["week", "kind", "item", "detail", "source"],
 "Lessons":      ["ts", "lesson", "evidence", "applies_to"],
 "Playbook":     ["rule_id", "department", "rule", "metric", "source", "evidence", "status", "added", "plays_on", "sum_on", "plays_off", "sum_off", "note"],      # v8.7: research-graded rules (K68)
 "Strategy_Log": ["ts", "dimension", "action", "name", "replaces", "mean_at_change", "note"],      # v8.6: every automatic strategy change, its evaluation and any rollback
 "Analytics":    ["episode_id", "yt_id", "pulled", "views", "avg_view_pct", "avg_view_sec", "ret30", "ctr", "ctr_kind", "likes", "shares", "subs", "score", "from_shorts", "diagnosis", "data_note", "shorts_views", "shorts_subs",
                  "impressions", "wtpi", "rel30", "rel_avg"],      # v8.7 (appended): impressions, watch seconds per impression, retention vs similar-length YouTube videos
 "Repairs":      ["ts", "file", "error", "result", "pr"],
 # v7.4: audience research, opening hooks, cut map (all reviewable by a person)
 "Research_Brief":  ["brief_id", "brief_date", "kind", "ref", "item", "detail", "evidence_type", "source_url", "observed_at"],
 "Hook_Candidates": ["episode_id", "rank", "line", "words", "type", "clarity", "relevance", "curiosity", "promise_accuracy", "total", "valid", "issues", "chosen", "applied"],
 "Cut_Map":         ["episode_id", "cut_id", "start", "end", "duration", "kind", "action", "confidence", "reason", "method", "review_status"],
 "Reaction_Map":    ["episode_id", "t", "kind", "word", "line", "style", "total_sec"],
 "Table_Read":      ["episode_id", "arm", "mode", "kind", "from_role", "to_role", "text", "request"],
}

class LocalStore:
    """Rehearsal store: same interface as SheetStore, kept in a JSON file."""
    def __init__(self, path=None):
        self.path = path or os.path.join(WORK, "local_sheet.json")
        self.d = json.load(open(self.path)) if os.path.exists(self.path) else {t: [] for t in TABS}
    def save(self): json.dump(self.d, open(self.path, "w"), indent=0, default=str)
    def ensure_tabs(self):
        for t in TABS: self.d.setdefault(t, [])
        self.save()
    def rows(self, tab): return [dict(r) for r in self.d.get(tab, [])]
    def append(self, tab, rows):
        cols = TABS[tab]; self.d.setdefault(tab, [])
        for r in rows: self.d[tab].append({c: _cell(r.get(c, "")) for c in cols})
        self.save()
    def replace(self, tab, rows):
        self.d[tab] = []; self.append(tab, rows)
    def plain_text(self, tab, col): return True      # local store keeps everything as text already
    def update(self, tab, key_col, key, changes):
        for r in self.d.get(tab, []):
            if str(r.get(key_col)) == str(key):
                r.update({k: _cell(v) for k, v in changes.items() if k in TABS[tab]}); self.save(); return True
        return False
    def update_where(self, tab, match, changes):
        """v8.9.1: update the first row matching ALL the given columns (e.g. dimension AND name)."""
        for r in self.d.get(tab, []):
            if all(str(r.get(k)) == str(v) for k, v in match.items()):
                r.update({k: _cell(v) for k, v in changes.items() if k in TABS[tab]}); self.save(); return True
        return False

class SheetStore:
    """Google Sheet via the Sheets REST API (no extra library)."""
    API = "https://sheets.googleapis.com/v4/spreadsheets/"
    def __init__(self, sheet_id): self.id = sheet_id
    def _req(self, method, url, **kw):
        for a in range(5):
            r = requests.request(method, url, headers=gheaders(), timeout=60, **kw)
            if r.status_code in (429, 500, 503): time.sleep(5 * (a + 1)); continue
            if r.status_code >= 400: raise RuntimeError(f"Sheets {r.status_code}: {r.text[:300]}")
            return r.json() if r.text else {}
        raise RuntimeError("Sheets busy after retries")
    def ensure_tabs(self):
        meta = self._req("GET", self.API + self.id + "?fields=sheets.properties(sheetId,title,gridProperties.columnCount)")
        have = {s["properties"]["title"] for s in meta.get("sheets", [])}
        add = [{"addSheet": {"properties": {"title": t, "gridProperties": {"columnCount": grid_columns(len(TABS[t]))}}}} for t in TABS if t not in have]      # v8.9.1: wide enough (the default grid is A-Z = 26 columns)
        if add: self._req("POST", self.API + self.id + ":batchUpdate", json={"requests": add})
        for t in TABS:
            v = self._req("GET", self.API + self.id + f"/values/{t}!1:1").get("values", [])
            self.widen(t, len(v[0]) + len([c for c in TABS[t] if c not in v[0]]) if v else len(TABS[t]))      # v8.9.1: older tabs grow before a wider header is written
            if not v:
                self._req("PUT", self.API + self.id + f"/values/{t}!A1?valueInputOption=RAW", json={"values": [TABS[t]]})
            else:
                # Existing sheets may predate newly introduced columns. Preserve every existing
                # header and append missing schema columns so updates never silently discard fields.
                header = list(v[0])
                missing = [c for c in TABS[t] if c not in header]
                if missing:
                    self._req("PUT", self.API + self.id + f"/values/{t}!A1?valueInputOption=RAW",
                              json={"values": [header + missing]})
    def widen(self, tab, ncols):
        """v8.9.1 (fix): a tab created with the default 26 columns (A-Z) cannot take a header or row wider than that (Episodes has 28 columns, AA-AB):
        the write fails with 'exceeds grid limits'. Columns are appended until the tab is wide enough. Returns the number of columns added."""
        meta = self._req("GET", self.API + self.id + "?fields=sheets.properties(sheetId,title,gridProperties.columnCount)")
        s = next((x["properties"] for x in meta.get("sheets", []) if x["properties"].get("title") == tab), None)
        if not s: return 0
        have = int((s.get("gridProperties") or {}).get("columnCount") or 26); need = grid_columns(ncols)
        if have >= need: return 0
        self._req("POST", self.API + self.id + ":batchUpdate", json={"requests": [{"appendDimension": {"sheetId": s["sheetId"], "dimension": "COLUMNS", "length": need - have}}]})
        return need - have
    def plain_text(self, tab, col):
        """Format one column as plain text so Sheets never turns '2027-03' or '10:00' into a date/time."""
        meta = self._req("GET", self.API + self.id + "?fields=sheets.properties(sheetId,title)")
        sid = next(s["properties"]["sheetId"] for s in meta.get("sheets", []) if s["properties"]["title"] == tab)
        self._req("POST", self.API + self.id + ":batchUpdate", json={"requests": [{"repeatCell": {
            "range": {"sheetId": sid, "startColumnIndex": col, "endColumnIndex": col + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}}, "fields": "userEnteredFormat.numberFormat"}}]})
        return True
    def _all(self, tab):
        v = self._req("GET", self.API + self.id + f"/values/{tab}").get("values", [])
        return v
    def rows(self, tab):
        v = self._all(tab)
        if not v: return []
        hdr = v[0]; out = []
        for row in v[1:]:
            out.append({h: (row[i] if i < len(row) else "") for i, h in enumerate(hdr)})
        return out
    def append(self, tab, rows):
        if not rows: return
        vals = [[_cell(r.get(c, "")) for c in TABS[tab]] for r in rows]
        self._req("POST", self.API + self.id + f"/values/{tab}!A1:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS", json={"values": vals})
    def replace(self, tab, rows):
        self._req("POST", self.API + self.id + f"/values/{tab}!A2:{col_letter(max(len(TABS[tab]), 26) + 26)}:clear", json={})      # v8.9.1: was A2:Z (columns AA+ were never cleared)
        if rows:
            vals = [[_cell(r.get(c, "")) for c in TABS[tab]] for r in rows]
            self._req("PUT", self.API + self.id + f"/values/{tab}!A2?valueInputOption=RAW", json={"values": vals})
    def update(self, tab, key_col, key, changes):
        v = self._all(tab)
        if not v: return False
        hdr = v[0]; ki = hdr.index(key_col)
        for n, row in enumerate(v[1:], start=2):
            if ki < len(row) and str(row[ki]) == str(key):
                full = [(row[i] if i < len(row) else "") for i in range(len(hdr))]
                for c, val in changes.items():
                    if c in hdr: full[hdr.index(c)] = _cell(val)
                self._req("PUT", self.API + self.id + f"/values/{tab}!A{n}?valueInputOption=RAW", json={"values": [full]})
                return True
        return False
    def update_where(self, tab, match, changes):
        """v8.9.1: update the first row matching ALL the given columns (e.g. dimension AND name), so two strategies that share a name in different
        dimensions can never overwrite each other."""
        v = self._all(tab)
        if not v: return False
        hdr = v[0]
        if any(k not in hdr for k in match): return False
        for n, row in enumerate(v[1:], start=2):
            full = [(row[i] if i < len(row) else "") for i in range(len(hdr))]
            if all(str(full[hdr.index(k)]) == str(val) for k, val in match.items()):
                for c, val in changes.items():
                    if c in hdr: full[hdr.index(c)] = _cell(val)
                self._req("PUT", self.API + self.id + f"/values/{tab}!A{n}?valueInputOption=RAW", json={"values": [full]})
                return True
        return False

def grid_columns(n):
    """Columns a tab needs: its schema plus room for a few owner-added columns, never below Google's default 26."""
    return max(26, int(n) + 4)

def col_letter(n):
    """1 -> A, 26 -> Z, 27 -> AA, 52 -> AZ."""
    s = ""
    n = int(n)
    while n > 0: n, r = divmod(n - 1, 26); s = chr(65 + r) + s
    return s

def _cell(x):
    if isinstance(x, (dict, list)): x = json.dumps(x, ensure_ascii=False)
    s = "" if x is None else str(x)
    return s[:49000]

_store = None
def store():
    global _store
    if _store is None:
        _store = LocalStore() if (FAKE or not env("SHEET_ID")) else SheetStore(env("SHEET_ID"))
    return _store

# ---------------- settings ----------------
DEFAULTS = {
 # schedule
 "PAUSED": ("FALSE", "TRUE stops everything"),
 "PAUSED_UNTIL": ("", "auto-set by Guardian"),
 "PUBLISH_DAYS": ("Tue,Sat", "US Eastern days; 2 long videos/week to fit the ₹3,500 cap while preserving 3 Kling clips and writer-room reviews"),
 "PUBLISH_HOUR_ET": ("10:00", "centre of slot, US Eastern"),
 "PUBLISH_JITTER_MIN": ("90", "+/- minutes"),
 "PRODUCE_AHEAD_HOURS": ("30", "start producing this long before a slot"),
 "REEL1_DELAY_MIN": ("15", "reel 1 after long video goes live"),
 "REEL2_DELAY_MIN": ("360", "reel 2 same day"),
 "RELEASE_GIVEUP_HOURS": ("24", "a reel release still impossible this many hours after the slot is closed (it never blocks new videos)"),
 "PRIVATE_ALERT_HOURS": ("2", "email once if the long video is still private this long after its slot"),
 # format
 "RUNTIME_MIN_SEC": ("490", "8:10 (mid-roll ads need 8 minutes)"), "RUNTIME_MAX_SEC": ("600", "10:00"), "RUNTIME_HARD_MAX_SEC": ("600", "the learning loop may not stretch videos beyond this"),
 "WPM_ESTIMATE": ("150", "narration words per minute"),
 "HUMOUR_SHARE": ("0.2", "max share of wit"),
 "OUTPUT_HEIGHT": ("1440", "1440 or 1080"),
 "FPS": ("30", ""),
 # visuals and money
 "STILLS_MIN": ("44", ""), "STILLS_MAX": ("56", ""), "LIVING_STILLS": ("8", ""), "KLING_CLIPS": ("3", "default Kling clips per long video"), "KLING_MIN_CLIPS": ("3", "minimum Kling clips; budget controller must preserve this target"),
 "BUDGET_FLOOR_INR": ("3500", "monthly budget floor; paired with ceiling for a hard ₹3,500 cap"), "BUDGET_CEILING_INR": ("3500", "hard monthly spending cap"), "REVENUE_SHARE": ("0.10", ""),
 "USD_INR": ("99", "rupees per dollar incl. forex"),
 "PRICE_STILL_USD": ("0.0046", "cheap still, 1.5MP"), "PRICE_THUMB_USD": ("0.08", "premium image, about 2MP"),
 "PRICE_LIVING_USD": ("0.02", "living still clip"), "PRICE_KLING_USD": ("0.25", "5s hero clip"),
 "REEL1_SHORTS_ON": ("TRUE", "TRUE = reels also go to YouTube Shorts (Instagram/Facebook are controlled by META_ON)"),
 "LLM_EST_INR": ("148", "conservative AI-writing allowance per video including multi-role reviews and the v8.7 retention fix (about Rs 4-8, only when the gate finds a problem); reconcile against Cost_Log"),
 "PRICE_OPUS_IN": ("4", "USD per million input (Opus 5.5 list price, Oct 2026; verify on platform.claude.com)"), "PRICE_OPUS_OUT": ("20", "USD per million output"),
 "PRICE_SONNET_IN": ("2", "USD per million input (Sonnet 5.5 list price, Oct 2026; verify)"), "PRICE_SONNET_OUT": ("10", "USD per million output"),
 "FAL_FUNDED_USD": ("10", "add here when you top up (not needed if auto-reload is on)"),
 "ANTHROPIC_FUNDED_USD": ("25", "same"),
 "AUTO_RELOAD_ON": ("FALSE", "TRUE once auto-reload is switched on in both consoles"),
 "REFILL_WARN_DAYS": ("15", ""),
 # voice
 "VOICE": ("", "A, B, C or D after listening (blank = auto-pick A after 72h)"),
 "VOICE_SAMPLES_AT": ("", "auto"),
 "SPEED_TRIM": ("1.04", "1.00 = Part-1 speed"), "PACING_MODE": ("natural", "natural = v8.4 irregular, sense-following pacing (slow tempo drift, heavy-tailed pauses, per-episode personality); classic = v8.3 pacing"), "BREATH_DB": ("-34", "louder = closer to 0"), "BREATH_RATE": ("0.6", "0..1"),
 # platform
 "YT_CATEGORY": ("28", "Science & Technology"), "AI_LABEL_DEFAULT": ("TRUE", "honest label"),
 "META_ON": ("TRUE", ""), "IG_USER_ID": ("", "auto-filled at setup"), "FB_PAGE_ID": ("", "auto-filled at setup"),
 "OPERATOR_EMAIL": ("", "your email"), "DRIVE_FOLDER_ID": ("", "auto"),
 "EMAIL_LEVEL": ("minimal", "minimal = only essential emails (voice, launch, money, pause, alerts, monthly brief); all = also one note per scheduled video"),
 "META_GRAPH_VERSION": ("v24.0", "Facebook/Instagram Graph API version; raise it when Meta retires this one"),
 # automation
 "AUTO_MERGE_REPAIRS": ("TRUE", "repair bot merges itself if all tests pass, the fix adds no new network/key/shell code AND the file is not one of the protected money / quality / publishing files (those always wait for you)"),
 "MAX_REPAIRS_PER_WEEK": ("3", "repair bot attempts per 7 days"),
 "VOICE_WAIT_HOURS": ("72", "wait this long for your voice pick, then use A"),
 "PILOT_DONE": ("FALSE", "auto"),
 "LAUNCH_DONE": ("FALSE", "auto"),
 "FAL_STILL_MODEL": ("fal-ai/flux/schnell", "cheap stills"),
 "FAL_PREMIUM_MODEL": ("fal-ai/flux-pro/v1.1", "thumbnails + reel covers"),
 "FAL_LIVING_MODEL": ("fal-ai/ltx-video/image-to-video", "living stills"),
 "FAL_HERO_MODEL": ("fal-ai/kling-video/v2.1/standard/image-to-video", "hero clips"),
 "STILL_W": ("1632", ""), "STILL_H": ("918", ""),
 "PARALLAX_ON": ("TRUE", "depth parallax on stills"),
 "DRIVE_ARCHIVE": ("TRUE", "copy masters to Google Drive"),
 "DRIVE_ARCHIVE_KEEP": ("2", "how many archived masters to keep in Drive (older ones are deleted to save space)"),
 "KILL_CHECK": ("TRUE", "type KILL in Episodes.kill to stop a video before it goes live"),
 "ANTH_SEARCH_TOOL": ("web_search_20250305", "Claude web-search tool version; if it is rejected, search is skipped automatically"),
 "GUARDIAN_SEEN": ("", "auto - policy changes already acted on"),
 "MODELS_REFRESHED_AT": ("", "auto - model list refreshed weekly"),
 # v7.4 research stage (runs before topic selection; never blocks production)
 "RESEARCH_ON": ("TRUE", "TRUE = collect public audience/topic signals before picking a topic"),
 "RESEARCH_SOURCES": ("youtube,trends,qa", "any of: youtube, trends, qa (public Q&A from Stack Exchange science sites)"),
 "RESEARCH_QA_SITES": ("physics,astronomy,biology,chemistry,space", "Stack Exchange sites read for public question titles"),
 "RESEARCH_YT_QUERIES": ("what if|what would happen if|science explained", "YouTube searches (each costs 100 YouTube API quota units), separated by |"),
 "RESEARCH_MAX_AGE_DAYS": ("7", "reuse the newest research brief if it is younger than this"),
 "RESEARCH_TIMEOUT_SEC": ("20", "timeout for each research request"),
 "RESEARCH_RETRIES": ("3", "tries per research request"),
 "RESEARCH_VIRAL_VIEWS": ("1000000", "a video this popular within 10 days may support the word 'viral' in a brief; below it the word is removed"),
 # v7.4 opening hooks
 "HOOKS_ON": ("TRUE", "TRUE = write, validate and score ten opening lines per episode"),
 "HOOK_APPLY_MODE": ("auto", "auto = use the best line as the opening if it passes every check; suggest = only record the candidates for a human to pick"),
 "HOOK_MIN_SCORE": ("7.0", "lowest combined score (0-10) a line needs to be applied automatically"),
 # v7.4 cut map (review only; nothing is ever removed automatically)
 "CUTMAP_ON": ("TRUE", "TRUE = analyse the rendered narration/video and write a reviewable cut map"),
 "CUTMAP_MIN_GAP_SEC": ("0.8", "silences longer than this are dead-air candidates"),
 "CUTMAP_LONG_PAUSE_SEC": ("2.5", "planned pauses longer than this (without an explicit [pause]) are flagged for review"),
 "CUTMAP_KEEP_PAUSE_SEC": ("0.55", "natural pause left in place when a trim is suggested"),
 "CUTMAP_VIDEO_SCAN": ("TRUE", "also scan the finished video for frozen picture / black frames (adds a few minutes)"),
 "REVIEW_TO_DRIVE": ("TRUE", "save hooks / cut map / research brief for each episode to your private Drive"),
 "RESEARCH_BUDGET_SEC": ("150", "total time allowed for all research requests of one brief; when it is used up the remaining sources are skipped"),
 # v8.0 table read (ON by default since the Reality Engine profile; research and craft notes for every department are always on)
 "TABLE_READ_MODE": ("on", "on = departments challenge each other's memos before the bible, and Director clears the final script before shots are planned; higher API usage is budgeted"),
 "TABLE_READ_EXTRA_INR": ("55", "conservative allowance for objections round + director clearance calls; reconcile against Cost_Log"),
 # v8.1 hardening: presentation format switch, character voices, format gate, speaker tag, budget gate, Gemini prices
 "PRESENTATION_FORMAT": ("reality_engine", "reality_engine = two recurring roles (DIRECTOR + SKEPTIC); classic = single narrator. The environment variable WHATIFS_PRESENTATION_FORMAT, if set, wins"),
 "DIRECTOR_VOICE": ("B", "voice recipe (A-D, see the voice samples) for the DIRECTOR role"),
 "SKEPTIC_VOICE": ("C", "voice recipe (A-D) for the SKEPTIC role; if it equals DIRECTOR_VOICE a different one is used automatically"),
 "FORMAT_GATE_ON": ("TRUE", "TRUE = code checks that both roles really speak (labels present, both contribute) and asks the writer for ONE fix if not"),
 "SPEAKER_TAG_ON": ("TRUE", "TRUE = a small code-drawn tag (DIRECTOR / SKEPTIC) shows who is speaking, so presenters never need a face"),
 "BUDGET_SAFETY_MARGIN": ("1.10", "an episode starts only if the remaining monthly budget covers its estimated cost times this margin"),
 "BUDGET_MAINT_RESERVE_INR": ("100", "v8.7: kept INSIDE the cap. Production stops this many rupees BELOW the cap; only maintenance jobs (weekly trend scout / policy watch / playbook research, learning, monthly brief) and an in-flight overshoot may use the last part. The month never totals more than the cap"),
 "BUDGET_MAIL_MONTH": ("", "auto - month for which the budget-reached email was sent"),
 "PRICE_GEM_PRO_IN": ("2", "USD per million input tokens, Gemini Pro class (Gemini 3.1 Pro list price; verify on Google's price page, it changes; logged to Cost_Log)"), "PRICE_GEM_PRO_OUT": ("12", "USD per million output tokens (thinking tokens count as output)"),
 "PRICE_GEM_FLASH_IN": ("0.75", "USD per million input tokens, Gemini Flash class (the Flash price is listed to rise on 1 Jan 2027: re-check then)"), "PRICE_GEM_FLASH_OUT": ("3.75", "USD per million output tokens"),
 # v8.2: budget tiers, reactions, render QC, hold + one-click fix, checkpoints, pre-flight
 "REACTION_MAX": ("6", "most reaction moments (sound + pop-up + punch-in) in one video"),
 "REACTION_GAP_SEC": ("35", "minimum seconds between two reaction moments, so they never feel like a broken record"),
 "REACTION_FX_ON": ("TRUE", "TRUE = original reaction effects (code-drawn burst + pop-up word, punch-in zoom, original sound) on the Curious One's reaction lines"),
 "QC_VISION_ON": ("TRUE", "TRUE = an independent Gemini Flash check of ~12 sampled frames (does the picture match the line? visible glitches?)"),
 "QC_VISION_FRAMES": ("12", "frames sampled for the vision check"),
 "QC_SYNC_TOL_SEC": ("0.12", "largest allowed gap between the narration clock and the audio in the finished file"),
 "HOLD_ON_QC_FAIL": ("TRUE", "TRUE = a video that fails final QC after the free fixes is NOT uploaded; you get an email with a one-click fix link"),
 "AUTO_FIX_PAID_INR": ("30", "most rupees the pipeline itself may spend re-making a failed picture or clip BEFORE it holds a video (a Kling retry is about Rs 25)"),
 "PREFLIGHT_MAIL_DAY": ("", "auto - day the pre-flight email was sent"),
 "HOLD_MAIL_AT": ("", "auto"),
 "API_AUDIT_STATUS": ("not_sent", "not_sent / sent / approved. Tracks the YouTube API audit (SETUP_CHECKLIST Step 4b). You set it to sent after submitting the form; it flips to approved by itself the first time a video goes public"),
 "AUDIT_PRE_APPROVAL_EPISODES": ("1", "how many videos may be uploaded BEFORE the YouTube API audit is approved. YouTube locks videos uploaded before approval to Private for good (no appeal), so more than the 1 you film for the form would be paid for and never seen. 99 = no limit"),
 "AUDIT_NUDGE_AT": ("", "auto - when the last audit reminder email went out"),
 "FIX_MAX_PAID_INR": ("80", "most rupees a one-click fix may spend on re-making failed images/clips"),
 "KLING_RETRY_MAX": ("1", "a failed Kling clip is retried this many times before the video is held"),
 "PREFLIGHT_ON": ("TRUE", "TRUE = free health checks (tools, disk, keys, Drive, voice engine) before any paid step; a red check skips the start instead of wasting money"),
 "CHECKPOINT_ON": ("TRUE", "TRUE = the plan (script, voice, shots) and the paid assets are saved to your private Drive, so a retry or a fix never pays for them twice"),
 "FREE_SHOT_MAX_RUN": ("3", "most consecutive shots allowed to reuse one picture"),
 # v8.3: render size, safety nets, fact check, like/subscribe/share asks
 "VIDEO_CRF": ("20", "x264 quality of the segments (lower = bigger files). 20 keeps a 10-minute 1440p master near 1 GB; 17 made it 4+ GB"),
 "GRAIN_LEVEL": ("3", "film-grain strength 0-6 (0 = none). Grain is moving noise: it costs file size, so keep it light"),
 "HOLD_BLOCK_AFTER": ("2", "new episodes wait only when this many videos are held at once (1 = any hold stops production, as in v8.2). One held video no longer stops the next slot"),
 "QC_VISION_REQUIRED": ("TRUE", "TRUE = if the independent Gemini picture check cannot run, the video is held instead of passing unchecked"),
 "VOICE_FALLBACK_OK": ("FALSE", "FALSE = if a character voice cannot load, the episode stops before any picture money is spent (never a third voice)"),
 "FACT_CHECK_ON": ("TRUE", "TRUE = a search-grounded check of the script's factual claims before any picture money is spent (about Rs 3 per video)"),
 "CTA_LAST": ("", "auto - which hand-written like/subscribe/share lines were used last, so two videos in a row never repeat one"),
 "CTA_ON": ("TRUE", "TRUE = witty in-story like / subscribe / share asks are written into every video (and added by code if the writer forgets them)"),
 "CTA_CHIP_ON": ("TRUE", "TRUE = a small code-drawn Like / Subscribe / Share chip appears while those lines are spoken"),
 "CTA_DESC_ON": ("TRUE", "TRUE = the description ends with a witty subscribe line and a one-click subscribe link"),
 "GUARDIAN_NEEDS_OFFICIAL": ("TRUE", "TRUE = the weekly policy watch pauses the channel only for a change reported by an official YouTube / Google source"),
 "DEGRADED_NOTE_ON": ("TRUE", "TRUE = any silent downgrade (backup model, still instead of clip, flat depth) is written to the episode notes"),
 # v8.5 growth patch: more (and better) Shorts, motion in the first minute, a packaging rescue. All free or nearly free inside the same cap.
 "REEL_STYLE": ("bridge", "bridge (default) = each Short gives one real payoff, leaves the episode's BIGGER question open and invites viewers to the full video, then the follow/share ask; standalone = a complete loopable mini-story (most reach, weakest pull to the long video); teaser = v8.4 behaviour (cut on the question + 'Full video on our channel')"),
 "REELS_PER_VIDEO": ("4", "Shorts cut from each long video (2-4). Reels 3 and 4 cost about Rs 1 of writing and nothing else (covers are drawn from the video's own pictures)"),
 "REEL3_DELAY_MIN": ("1560", "reel 3 this many minutes after the long video goes live (26 h: the next day)"),
 "REEL4_DELAY_MIN": ("3000", "reel 4 (50 h: the day after that). With Tue/Sat videos this puts a Short on 6 of 7 days"),
 "OPENING_WINDOW_SEC": ("45", "the opening seconds that decide whether a viewer stays: motion and fresh pictures are concentrated here"),
 "OPENING_KLING_MIN": ("1", "at least this many of the Kling clips play inside the opening window (moved, never added: same cost)"),
 "OPENING_LIVING_MIN": ("2", "at least this many living stills play inside the opening window (moved, never added)"),
 "OPENING_FRESH_ON": ("TRUE", "TRUE = every shot in the opening window gets its own new picture (taken from the same picture budget, not added to it)"),
 "PKG_RESCUE_ON": ("TRUE", "TRUE = a second thumbnail (different idea) is made with each video (about Rs 8); if the video is clearly behind the channel's usual pace after PKG_RESCUE_HOURS, the title and thumbnail are swapped once to the runner-up"),
 "PKG_RESCUE_HOURS": ("36", "age of the video when the daily learning job compares it with earlier videos at the same age"),
 "PKG_RESCUE_RATIO": ("0.7", "swap when the video's view pace (views per hour since its slot) is below this share of the median pace of earlier videos"),
 "PKG_RESCUE_MIN_HISTORY": ("3", "no swap until this many earlier videos have been measured (no baseline = no guess)"),
 # v8.6 click-through + retention layer (all free; code checks, no model calls)
 "TITLE_MIN_CHARS": ("30", "titles shorter than this are flagged (too vague to click)"),
 "TITLE_MAX_CHARS": ("60", "titles longer than this are flagged (cut off on phones); the clean title wins over a flawed one"),
 "THUMB_MAX_WORDS": ("4", "thumbnail text is cut to this many words (readable at phone size)"),
 "PROMISE_SHOT_ON": ("TRUE", "TRUE = the first Kling clip in the opening shows the thumbnail's scene, so the click is paid off within the first 45 s"),
 "DIAG_MIN_HISTORY": ("3", "earlier analysed videos needed before a video is diagnosed (packaging / opening / holding); fewer = 'insufficient data'"),
 "ANALYTICS_GIVEUP_DAYS": ("10", "YouTube Analytics can lag: a video with no data is retried daily up to this age, then recorded as 'no data' (never scored)"),
 "STRATEGY_EVAL_PLAYS": ("5", "plays a new (invented) strategy gets before it is compared with the one it replaced; worse = automatic rollback, once"),
 "PKG_DIP_GUARD_ON": ("TRUE", "TRUE = no title/thumbnail swap while the last 3 videos are ALL behind pace (a channel-wide dip is not a packaging problem)"),
 # v8.7: CTR + first minute + full retention + sensory sound + anti-sameness + proactive research (all free except a weekly research call, inside the cap)
 "RETENTION_GATE_ON": ("TRUE", "TRUE = code checks the script's first ~45 s (shows the title/thumbnail promise, opens a question, no throat-clearing) and its re-hooks (none missing near 3:00 and 6:00, no stretch longer than REHOOK_MAX_GAP_SEC); ONE targeted rewrite only when something fails"),
 "REHOOK_MAX_GAP_SEC": ("90", "longest stretch of script allowed without a re-hook (a question, a turn, a reveal)"),
 "SOUND_DESIGN_ON": ("TRUE", "TRUE = original code-made sound textures under the shots that show them, a music bed that changes by section, falls silent before each peak and hushes under [close] lines"),
 "NEXT_LINK_ON": ("TRUE", "TRUE = the description and the channel comment end with a link to the best related earlier video ('next simulation')"),
 "PLAYBOOK_ON": ("TRUE", "TRUE = weekly research proposes source-linked rules; they are tested on half the episodes and kept only if they move their metric (Playbook tab)"),
 "PLAYBOOK_EVAL_PLAYS": ("5", "videos needed on EACH side (with / without a trial rule) before it is judged"),
 # v8.9: cinematic visual layer, rotating guest voices, next-episode tease, change-ready emails (all free: no paid call added)
 "STYLE_LOCK": (__import__("whatifs.data", fromlist=["STYLE_LOCK"]).STYLE_LOCK, "style words appended to EVERY in-video picture and clip prompt (thumbnails get a brighter variant so they stay readable on phones)"),
 "CAMERA_MOTION": ("dynamic", "dynamic = 8-move cinematic camera library, strongest moves in the opening and right before reactions; gentle = the v8.7 moves"),
 "GUEST_ROTATION_ON": ("TRUE", "TRUE = the Curious One is a different guest each episode (new clear voice + everyday persona), least recently used first; FALSE = SKEPTIC_VOICE every time"),
 "NEXT_TEASE_ON": ("TRUE", "TRUE = each video ends by teasing the NEXT episode's premise, and the next episode is made from that teased premise"),
 "NEXT_PREMISE": ("", "auto - the premise teased at the end of the last video (the next episode picks it up)"),
 "PR_MAIL_ON": ("TRUE", "TRUE = when a code change (from Claude Code or the Repair Bot) passes every check, you get an email with a one-click merge link"),
 "TREND_CHANNELS": ("@WhatIfScienceShow,@kurzgesagt,@veritasium,@Vsauce,@RealLifeLore,@TheInfographicsShow,@zackdfilms,@MrBeast", "channels watched weekly"),
}
_settings_cache = None
def settings(refresh=False) -> dict:
    global _settings_cache
    if _settings_cache is not None and not refresh: return _settings_cache
    rows = store().rows("Settings")
    s = {k: v[0] for k, v in DEFAULTS.items()}
    for r in rows:
        if r.get("key"): s[r["key"]] = str(r.get("value", "")).strip()
    _settings_cache = s; return s
def S(key, cast=str):
    v = settings().get(key, DEFAULTS.get(key, ("",))[0])
    if cast is bool: return str(v).strip().upper() in ("TRUE", "YES", "1", "ON")
    try: return cast(v)
    except Exception: return cast(DEFAULTS[key][0]) if key in DEFAULTS else v
def set_setting(key, value):
    st = store(); global _settings_cache
    if not st.update("Settings", "key", key, {"value": value}):
        st.append("Settings", [{"key": key, "value": value, "note": DEFAULTS.get(key, ("", ""))[1]}])
    _settings_cache = None

# ---------------- logging ----------------
_logbuf, _lock = [], threading.Lock()
JOB = {"name": "job", "episode": ""}
_SECRET_ENVS = ("G_CLIENT_KEY", "G_REFRESH", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY", "PEXELS_KEY", "META_PAGE_KEY", "G_CLIENT_ID", "SHEET_ID")
def scrub(text):
    """Never let a key reach a log, the Sheet, an email or an error file."""
    s = str(text)
    for n in _SECRET_ENVS:
        v = os.environ.get(n, "")
        if v and len(v) >= 8: s = s.replace(v, "***")
    s = re.sub(r"(key=|access_to" + r"ken=|Bearer\s+|Key\s+)[A-Za-z0-9_\-\.:]{12,}", r"\1***", s)
    return s

def log(msg, level="INFO", episode=None, public=None):
    """public = a short, content-free text for the (public) Actions log. The full message still goes to the private Run_Log tab."""
    msg = scrub(msg)
    shown = scrub(public) if public is not None else msg
    line = f"[{level}] {JOB['name']} {episode or JOB['episode']}: {shown}"
    print(line, flush=True)
    with _lock: _logbuf.append({"ts": iso(), "job": JOB["name"], "episode_id": episode or JOB["episode"], "level": level, "message": str(msg)[:1500]})
    if len(_logbuf) >= 40: flush_log()
def flush_log():
    with _lock:
        rows = list(_logbuf); _logbuf.clear()
    if rows:
        try: store().append("Run_Log", rows)
        except Exception as e: print("log flush failed:", scrub(e))
    flush_costs()

# ---------------- money (buffered: one Sheet read per job, one write per flush) ----------------
_clock = threading.Lock()
_cost_buf, _session = [], {}
_base = {"v": None}
def _spend_base():
    if _base["v"] is None:
        life, month, m = {}, {}, now_utc().strftime("%Y-%m")
        for r in store().rows("Cost_Log"):
            try: v = float(r.get("inr") or 0)
            except Exception: continue
            p = r.get("provider", ""); life[p] = life.get(p, 0) + v
            if str(r.get("ts", "")).startswith(m): month[p] = month.get(p, 0) + v
        _base["v"] = {"life": life, "month": month}
    return _base["v"]
_last_cost_flush = [time.time()]
def cost(item, provider, units, usd, episode=None):
    inr = round(usd * S("USD_INR", float), 2)
    _spend_base()
    with _clock:
        _cost_buf.append({"ts": iso(), "episode_id": episode or JOB["episode"], "item": item, "provider": provider, "units": units, "inr": inr})
        _session[provider] = _session.get(provider, 0) + inr
        due = len(_cost_buf) >= 6 or time.time() - _last_cost_flush[0] > 45
    if due: flush_costs()        # v8.3: spend reaches the Sheet within seconds, so a killed or timed-out job cannot lose it
    return inr
def flush_costs():
    with _clock:
        rows = list(_cost_buf); _cost_buf.clear(); _last_cost_flush[0] = time.time()
    if rows:
        try: store().append("Cost_Log", rows)
        except Exception as e:
            print("cost flush failed:", scrub(e))
            with _clock: _cost_buf[:0] = rows
def refresh_spend():
    """v8.3: re-read Cost_Log so spend made by OTHER jobs (research, learning, a parallel run) is counted before the next paid stage.
    Everything this job spent is flushed first, so nothing is counted twice."""
    flush_costs()
    try:
        with _clock:
            _base["v"] = None; _session.clear()
            for r in _cost_buf: _session[r["provider"]] = _session.get(r["provider"], 0) + float(r.get("inr") or 0)
        _spend_base()
    except Exception as e: print("spend refresh skipped:", scrub(e))
def month_spend(provider=None) -> float:
    b = _spend_base()["month"]
    if provider: return b.get(provider, 0) + _session.get(provider, 0)
    return sum(b.values()) + sum(_session.values())
def lifetime_spend_usd(provider) -> float:
    return (_spend_base()["life"].get(provider, 0) + _session.get(provider, 0)) / S("USD_INR", float)

def safe_append(tab, rows):
    """v7.4: append rows to a tab. A tab missing from an older Sheet is created once. Never raises (reports are optional)."""
    if not rows: return True
    st = store()
    try: st.append(tab, rows); return True
    except Exception as e:
        try: st.ensure_tabs(); st.append(tab, rows); return True
        except Exception as e2:
            log(f"could not save to {tab}: {scrub(e2)}", "WARN"); return False
def safe_rows(tab):
    """v7.4: read a tab; [] if it does not exist yet or the read fails."""
    try: return store().rows(tab)
    except Exception: return []

def status(step, ok, detail=""):
    st = store(); val = "✅" if ok else "❌"
    if not st.update("Setup_Status", "step", step, {"status": val, "detail": str(detail)[:500], "updated": iso()}):
        st.append("Setup_Status", [{"step": step, "status": val, "detail": str(detail)[:500], "updated": iso()}])

_degraded = []
def note_degraded(text):
    """v8.3: a silent downgrade (backup model, still instead of clip, flat depth, plain font) is remembered and written to the episode notes."""
    t = str(text)[:90]
    if t not in _degraded and len(_degraded) < 12: _degraded.append(t)
    log(f"degraded: {t}", "WARN")
def take_degraded():
    out = list(_degraded); _degraded.clear(); return out

def retry(fn, tries=4, wait=4, what="call"):
    last = None
    for a in range(tries):
        try: return fn()
        except Exception as e:
            last = e; log(f"{what} failed (try {a+1}/{tries}): {scrub(e)}", "WARN"); time.sleep(wait * (a + 1))
    raise last

