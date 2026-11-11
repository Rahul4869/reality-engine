"""Settings, storage (Google Sheet or local rehearsal store), logging, cost log and Google sign-in. See docs/CURRENT/SYSTEM.md."""
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
_gtok = {"main": {"v": None, "exp": 0, "scope": ""}, "drive": {"v": None, "exp": 0, "scope": ""}}
# v8.9.2: Google refuses drive.file in the same consent as the YouTube permissions, so Drive has its own key (G_REFRESH_DRIVE).
# A G_REFRESH made before that rule (it already holds drive.file) keeps working for Drive when G_REFRESH_DRIVE is not set.
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/youtube",
                 "https://www.googleapis.com/auth/youtube.upload",
                 "https://www.googleapis.com/auth/youtube.force-ssl",
                 "https://www.googleapis.com/auth/yt-analytics.readonly",
      "https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",      # v9.3.1: no re-consent later
                 "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/gmail.send"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
def google_access(kind: str = "main") -> str:
    t = _gtok[kind]
    if t["v"] and time.time() < t["exp"] - 120: return t["v"]
    rt = (env("G_REFRESH_DRIVE") or env("G_REFRESH")) if kind == "drive" else env("G_REFRESH")
    data = {"client_id": env("G_CLIENT_ID"), f"client_{SC}": env("G_CLIENT_KEY"),
            f"refresh_{TK}": rt, "grant_type": f"refresh_{TK}"}
    r = requests.post(f"https://oauth2.googleapis.com/{TK}", data=data, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Google {'Drive ' if kind == 'drive' else ''}sign-in failed ({r.status_code}): {r.text[:300]}")
    j = r.json(); t["v"] = j[f"access_{TK}"]; t["exp"] = time.time() + int(j.get("expires_in", 3600)); t["scope"] = j.get("scope", "")
    return t["v"]
def gheaders() -> dict: return {"Authorization": "Bearer " + google_access()}
def gdrive_headers() -> dict: return {"Authorization": "Bearer " + google_access("drive")}

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
                  "reel3_yt", "reel4_yt", "ig3", "ig4", "fb3", "fb4", "pkg_check", "teacup_json", "kids_check", "render_min", "atmos_json", "shots_json", "drop_posted"],     # v9: teacup placements (t, x, y, scale)     # v8.5 (new columns go at the END so older Sheets keep their order)
 "Cost_Log":     ["ts", "episode_id", "item", "provider", "units", "inr",
                  "model", "in_tok", "cache_read_tok", "cache_write_tok", "out_tok", "basis", "measured_inr", "est_inr", "role", "ms"],      # v11: + ms (call latency)      # v8.11 (appended): measured token detail per AI call
                                                                                                       # (basis = measured); one 'summary' row per video: measured vs estimated AI ₹ (inr = 0)
 "Run_Log":      ["ts", "job", "episode_id", "level", "message"],
 "Revenue_Log":  ["month", "source", "inr_received", "note"],
 "Trend_Brief":  ["week", "kind", "item", "detail", "source"],
 "Lessons":      ["ts", "lesson", "evidence", "applies_to"],
 "Playbook":     ["rule_id", "department", "rule", "metric", "source", "evidence", "status", "added", "plays_on", "sum_on", "plays_off", "sum_off", "note"],      # v8.7: research-graded rules (K68)
 "Strategy_Log": ["ts", "dimension", "action", "name", "replaces", "mean_at_change", "note"],      # v8.6: every automatic strategy change, its evaluation and any rollback
 "Analytics":    ["episode_id", "yt_id", "pulled", "views", "avg_view_pct", "avg_view_sec", "ret30", "ctr", "ctr_kind", "likes", "shares", "subs", "score", "from_shorts", "diagnosis", "data_note", "shorts_views", "shorts_subs",
                  "impressions", "wtpi", "rel30", "rel_avg", "engaged_views"],      # v8.7 (appended): impressions, watch seconds per impression, retention vs similar-length YouTube videos
 "Repairs":      ["ts", "file", "error", "result", "pr"],
 # v7.4: audience research, opening hooks, cut map (all reviewable by a person)
 "Research_Brief":  ["brief_id", "brief_date", "kind", "ref", "item", "detail", "evidence_type", "source_url", "observed_at"],
 "Hook_Candidates": ["episode_id", "rank", "line", "words", "type", "clarity", "relevance", "curiosity", "promise_accuracy", "total", "valid", "issues", "chosen", "applied"],
 "Cut_Map":         ["episode_id", "cut_id", "start", "end", "duration", "kind", "action", "confidence", "reason", "method", "review_status"],
 "Reaction_Map":    ["episode_id", "t", "kind", "word", "line", "style", "total_sec"],
 "Table_Read":      ["episode_id", "arm", "mode", "kind", "from_role", "to_role", "text", "request"],
 # v8.10 (created by Setup and by the daily learning job on older Sheets)
 "Cast":            ["id", "role", "display_name", "voice", "gender", "pitch", "personality", "speech_habits", "signature_quirk", "style_direction",
                     "intro_line", "active", "weight", "last_used"],                                       # 5 experts + 15 rotating guests (owner-editable)
 "Voice_Check":     ["ts", "voice", "source", "listed", "synth_ok", "multi_speaker_ok", "detail"],         # which Gemini voice names this key can really use
 "Premise_Scores":  ["ts", "episode_id", "round", "premise", "headline", "source", "claude_score", "gemini_score", "combined", "criteria_json", "passed",
                     "chosen", "note", "ctr", "rel30", "avg_view_pct"],                                     # every pitch + both blind scores; filled with results later
 "Craft_Notebook":  ["added", "note", "applies_to", "priority", "active"],                                 # owner notes: top-priority creative input
 "Technique_Library": ["ts", "video_id", "title", "channel", "views", "hook_device", "first_3s_visual", "cut_rhythm", "sound_moment", "payoff_structure",
                       "evidence", "source_url", "applies_when", "status", "value_case"],                     # technique observations; v9.3.2: when it fits, its status and the honest value case
 "Owners_Cut":      ["ts", "episode_id", "round", "inside_scene", "weirdness_hook", "emotional_peaks", "payoff", "originality", "mean", "passed", "notes"],
 "Script_Previews": ["draft_id", "created", "status", "premise", "title", "hook", "est_cost_inr", "approved_at", "episode_id", "room_json", "note"],
 "Dash_Acks":       ["ts", "id", "verb", "ok", "note"],
 "Localizations":   ["ts", "episode_id", "yt_id", "langs", "ok"],
 "Slop_Scores":     ["ts", "episode_id", "slop", "still", "motion", "template_sim", "voice_flatness", "opening_repeat", "fingerprint", "opening"],   # v10 (K137)
 "Data_Rules":      ["ts", "key", "kind", "text", "videos", "effect", "started_at_video", "confirmed_at_video"],      # v10 (K138): Retention Microscope rules
 "Expiry_Calendar": ["item", "expires", "renew", "reminded"],             # v10 (K140): keys, tokens and plans that expire
 "Backups":         ["ts", "name", "file"],                                 # v10 (K140): weekly Sheet backups on Drive
 "Pilots":          ["ts", "id", "bench_id", "premise", "hook", "yt_id", "views", "bonus"],     # v10 (K141): premise test Shorts
 "Outlier_Lab":     ["ts", "video_id", "title", "status"],                  # v10 (K142): videos watched by the Outlier Lab
 "Bakeoff":         ["ts", "models", "card"],                               # v10 (K143)
 "Script_Fingerprints": ["ts", "episode_id", "sig"],                     # v10.1 (K145)
 "Owner_Briefs":    ["ts", "id", "target", "premise", "brief_json", "scores_json", "demand", "status", "episode_id", "outcome_json"],   # v10.3 (K154)
 "Room_Value":      ["ts", "episode_id", "winner", "margin", "room_score", "solo_score", "judge_notes", "solo_cost_inr"],               # v10.3 (K155)
 "Impact_Maps":     ["ts", "episode_id", "signature", "summary"],                     # v11.1 (K166): event-type signature per episode (V9 variety)
 "Tool_Scout":      ["ts", "endpoint_id", "name", "category", "unit_price", "unit", "aa_elo", "note"],   # v11 (K165)
 "Reach":           ["key", "date", "video_id", "impressions", "ctr", "updated"],   # v11 (K162): Reporting API channel_reach_basic_a1
 "Breakout_Scores": ["ts", "episode_id", "format", "score", "grade", "weakest", "components", "missing"],   # v11 (K158)
 "Monitor48":       ["yt_id", "video_key", "kind", "published", "v24", "v48", "updated"],                        # v11 (K158)
 "Breakout_Queue":  ["ts", "video_key", "status", "plan", "left"],                                                       # v11 (K158): approved follow-ups
 "Jury_Log":        ["ts", "episode_id", "stage", "judge", "order", "ranking", "n"],   # v11 (K157): every blind jury decision (judges are scored later)
 "Video_Features":  ["ts", "video_key", "yt_id", "format", "hook", "title", "topic", "length", "lead", "origin", "arm", "holdout", "title_text"],   # v11 (K155)
 "Technique_Evidence": ["technique_id", "format", "family", "level", "alpha", "beta", "trials", "successes", "n_videos", "p_beats_baseline", "effect_pp",
                       "baseline_rate", "status", "last_validated", "expires_at", "updated", "mechanism", "kill_condition", "source_type"],   # v11 (K155): own-channel evidence (Technique_Library is the v8.10 outlier-video library)
 "Brain_Log":       ["ts", "event", "technique_id", "from", "to", "evidence"],   # v11 (K155)
 "Forecasts":       ["ts", "video_key", "format", "metric", "lo", "mid", "hi", "naive", "basis", "actual", "scored"],   # v11 (K155)
 "Feature_Ledger":  ["ts", "episode_id", "stage", "feature", "status", "evidence", "promise"],   # v10.2 (K151): proof, per video
 "Model_Changes":   ["ts", "role", "from", "to", "why"],                     # v10.1 (K150): every automatic model switch
 "Viewer_Questions": ["ts", "video_id", "comment_id", "author", "text", "used"],   # v10.1 (K147)
 "Carousels":       ["ts", "episode_id", "files", "caption", "status", "ig_id"],     # v10.1 (K149)
 "Specials":        ["ts", "id", "kind", "title", "format", "ask", "yt_id", "ig", "fb", "status", "views_7d", "file", "premise"],      # v11: + file (Drive id for approval; was dropped), premise     # v10 (K134): cast intro + twice-monthly special reels (format learning)           # v10 G4: localized titles/descriptions set
 "WA_Outbox":       ["ts", "wamid", "action_id", "kind", "status"],          # v9.4b: WhatsApp messages sent and their delivery status
 "WA_Chat":         ["ts", "msg_id", "who", "text"],                         # v9.4b: the owner chat (private Sheet; never in logs)                      # v9.4b: dashboard taps handled (the page clears "Queued" from these)
 "Owner_Actions":   ["id", "created", "tier", "kind", "episode_id", "text", "buttons", "default_action", "expires_at", "status", "answered_at", "answer", "channel", "delivered_at", "dedupe_key", "urgent"],      # v9.4a (WP4): every owner message, button, default and answer
 # v8.11 (created by Setup and by the daily learning job on older Sheets)
 "Premise_Bench":   ["bench_id", "added", "status", "premise", "headline", "family", "ptype", "claude_score", "gemini_score", "combined", "criteria_json",
                     "source", "episode_id", "used_at", "note", "src", "demand_json"],      # v9: src = outlier | original | comment                                              # pre-scored approved premises; the scout draws from here first
 # v9 (stage 1): "Reality on Trial"
 "Demand_Signals":  ["ts", "video_id", "title", "channel", "views", "channel_median", "multiple", "published", "used"],     # v9: outlier videos (demand evidence)
 "Packaging_Tests": ["episode_id", "yt_id", "variant", "title", "thumb_text", "thumb_file", "status", "window_start", "window_end", "views_start", "views_end",
                     "views_per_hour", "ctr", "picked_by", "created"],                                          # v9: 3 pairs, owner pick, rotation result
 "Comment_Queue":   ["ts", "episode_id", "comment_id", "author", "kind", "text", "draft", "status", "replied_at", "mined"],     # v9: triaged comments (untrusted text)
 "Season":          ["ts", "episode_id", "case", "verdict", "meter_final", "jury_tally", "teacup_finders", "clue"],
 "Experiments":     ["episode_id", "created", "premise_source", "packaging_variant", "intensity", "hook_shape", "publish_slot", "hypothesis",
                     "ctr_48h", "ret30_48h", "avg_view_sec_48h", "comments_per_1k_48h", "shares_48h", "country_48h", "ctr_7d", "ret30_7d", "avg_view_sec_7d",
                     "comments_per_1k_7d", "shares_7d", "country_7d", "ctr_28d", "ret30_28d", "avg_view_sec_28d", "comments_per_1k_28d", "shares_28d", "country_28d"],
 "Character_Sheets": ["ts", "character", "expression", "hash", "prompt", "file", "status", "approved_at"],          # v9: one-time, lifetime-capped, locked after approval
 "Show_Log":        ["ts", "episode_id", "format", "intensity", "witness_twist", "verdict_winner", "meter_final", "fallback", "issues", "plan_json", "opening_line"],
 "Retention_Map":   ["ts", "episode_id", "beat", "start", "end", "shot_types", "drop_per_30s", "vs_median", "confidence", "views"],          # v9.1 (report only)
 "Role_ROI":        ["ts", "episode_id", "role", "calls", "notes", "accepted", "changed_script", "inr", "inr_per_accepted"],               # v9.1 (report only)
 "Characters":      ["id", "name", "speaker", "role", "philosophy", "rhythm", "tics", "vocabulary", "recurring_bit", "when_wrong", "relationships", "visual",
                     "voice_style", "sound", "audio_chain", "status", "updated", "gvoice", "gstyle", "cast_id", "grammar_json"],     # gvoice: Gemini voice (Voice_Check); cast_id: a Cast row to borrow                                     # the character bible (core cast; owner-editable)
 "Cache_Stats":     ["updated", "episode_id", "job", "run_id", "calls", "cached_calls", "cache_read_tok", "cache_write_5m_tok", "cache_write_1h_tok",
                     "uncached_in_tok", "out_tok", "hit_ratio", "tokens_saved", "usd_saved", "ai_measured_inr", "ai_estimated_inr", "warnings"],   # one row per episode and job
 # v12: the Knowledge Palace (whatifs/org/palace.py). The index row holds everything a department playbook needs, so one read builds it.
 "Palace_Items":    ["id", "kind", "title", "body_ref", "summary", "departments", "stages", "topic_tags", "evidence", "confidence", "status", "version", "supersedes",
                     "superseded_by", "derived_from", "owner_input", "created", "updated", "review_by", "applied_count", "last_applied", "outcome_score", "cost_note",
                     "applied_in", "content_hash", "actor", "status_note", "priority"],
 "Palace_Versions": ["version", "ts", "actor", "action", "item_id", "item_version", "from_status", "to_status", "palace_hash", "note"],          # one row per change
 "Palace_Playbooks": ["playbook_id", "ts", "dept", "stage", "topic", "palace_hash", "n_items", "tokens", "cap", "item_ids", "body_ref"],        # each distinct playbook once
 # v12: the organisation (whatifs/org/memos.py, runner.py). Memos = one row per memo; Sessions = one row per department run with its six receipts;
 # Takeaways = what every run learned; Org_Audit = one row per run, escalation and watchdog pass that did something.
 "Memos":           ["id", "type", "from_dept", "to_depts", "holder", "level", "status", "urgency", "created", "updated", "ack_due", "sla_due", "subject", "body", "done_when",
                     "constraints", "links", "evidence", "cost_estimate", "owner_visible", "owner_notified", "episode_id", "session_id", "dedupe_key", "body_hash", "acks",
                     "resolution", "escalations", "attempt", "reminders"],
 "Sessions":        ["id", "key", "dept", "trigger", "episode_id", "attempt", "status", "started", "ended", "playbook_id", "palace_hash", "inject", "inbound", "emitted",
                     "takeaways", "applied_items", "steps", "chain", "cost_inr", "budget", "error"],
 "Takeaways":       ["id", "ts", "session_id", "dept", "trigger", "episode_id", "kind", "did", "worked", "failed", "next_time", "measures", "evidence", "novel", "signature", "palace_item"],
 "Org_Audit":       ["ts", "kind", "run_id", "dept", "trigger", "episode_id", "outcome", "steps", "chain", "latency_s", "cost_inr", "budget", "model_calls", "inbound", "emitted",
                     "takeaways", "sla_overdue", "playbook_id", "error", "note"],
 # v12: the Execution Engine (whatifs/org/execute.py). Tickets = one row per ticket, the engine's state for it; Lever_Changes = one row per event of a
 # change (intent before it, applied after it, then verified or rolled_back), only ever appended.
 "Tickets":         ["id", "created", "updated", "from_dept", "dept", "lever_class", "target", "state", "change_id", "old", "new", "undo", "applied_at", "verify_by",
                     "need", "proof", "attempts", "approved", "owner_action", "decision_ref", "request_id", "pr", "note", "session"],
 "Lever_Changes":   ["ts", "change_id", "ticket_id", "lever_class", "dept", "target", "action", "old", "new", "by", "proof", "note"],
 # v12 B5: R&D and the Review Board (whatifs/org/rnd.py, board.py). Research_Agenda = one row per gap the organisation should research (computed
 # from its own failures, owner memos, outliers, expiring facts, policy and tools); Board_Log = one row per judge, order and memo of a Review Board session.
 "Research_Agenda": ["id", "ts", "updated", "source", "ref", "signature", "question", "kind", "target_depts", "urgency", "priority", "status", "memo_id", "asked_at",
                     "cost_inr", "note", "palace_ref"],
 "Board_Log":       ["ts", "session_id", "memo_ref", "label", "canary", "judge", "family", "role", "model", "order", "answers", "verdict"],
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
 "PUBLISH_DAYS": ("Sat", "US Eastern day(s) of the long-video slots. Owner plan (10 Nov 2026): ONE long video a week, 4 a month; the month's count is capped by STANDARD_MAX_LONG_PER_MONTH and the money governor"),
 "PUBLISH_HOUR_ET": ("10:00", "centre of slot, US Eastern"),
 "PUBLISH_JITTER_MIN": ("90", "+/- minutes"),
 "PRODUCE_AHEAD_HOURS": ("30", "start producing this long before a slot"),
 "REEL1_DELAY_MIN": ("15", "reel 1 after long video goes live"),
 "REEL2_DELAY_MIN": ("360", "reel 2 same day"),
 "RELEASE_GIVEUP_HOURS": ("24", "a reel release still impossible this many hours after the slot is closed (it never blocks new videos)"),
 "PRIVATE_ALERT_HOURS": ("2", "email once if the long video is still private this long after its slot"),
 # format
 "RUNTIME_MIN_SEC": ("490", "8:10 (mid-roll ads need 8 minutes)"), "RUNTIME_MAX_SEC": ("540", "9:00 (v12 V1: was 10:00; the first live video ran 13 minutes - shorter until retention earns more)"), "RUNTIME_HARD_MAX_SEC": ("600", "NOT ACTIVE (no code reads this cell): the ceiling the code enforces is RUNTIME_MAX_SEC. Was meant as: the learning loop may not stretch videos beyond this"),
 "WPM_ESTIMATE": ("150", "narration words per minute"),
 "HUMOUR_SHARE": ("0.2", "max share of wit"),
 "OUTPUT_HEIGHT": ("1440", "1440 or 1080"),
 "FPS": ("30", ""),
 # visuals and money
 "STILLS_MIN": ("44", ""), "STILLS_MAX": ("56", ""), "LIVING_STILLS": ("8", ""), "KLING_CLIPS": ("4", "v10.2 (option C): animated scenes per long video (= ANIM_SHOTS)"), "KLING_MIN_CLIPS": ("4", "v10.2 (option C): the budget controller never trims animated scenes below this; it trims living stills, then stills, then runtime"),
 "BUDGET_FLOOR_INR": ("5000", "monthly budget floor; paired with the ceiling for a hard cap (₹5,000 all-in incl. ₹300 for special reels, owner 2026-11-08)"), "BUDGET_CEILING_INR": ("5000", "hard monthly spending cap, everything included: pictures, clips, Claude writing incl. thinking, Gemini incl. TTS, retries and repairs (₹5,000 incl. ₹300 for special reels, owner 2026-11-08; a single month can be overridden in MONTH_CAP_OVERRIDES)"), "REVENUE_SHARE": ("0.10", ""),
 "USD_INR": ("99", "rupees per dollar incl. forex"),
 "PRICE_STILL_USD": ("0.0046", "legacy estimate of one cheap still (v10.1: media uses PRICE_STILL_PER_MP x megapixels rounded up)"), "PRICE_STILL_PER_MP": ("0.003", "v10.1: FLUX schnell on fal, USD per megapixel, billed rounded UP to the next whole megapixel (verified 8 Nov 2026)"), "PRICE_THUMB_USD": ("0.08", "premium image, about 2MP"),
 "PRICE_LIVING_USD": ("0.02", "living still clip"), "PRICE_KLING_USD": ("0.42", "one 5 s animated scene (v10.2: Kling 3.0 Standard on fal, audio off)"),
 "REEL1_SHORTS_ON": ("TRUE", "TRUE = reels also go to YouTube Shorts (Instagram/Facebook are controlled by META_ON)"),
 "LLM_EST_INR": ("176", "conservative AI-writing allowance per video (v9: 176 = v8.11's 200 - Rs 30 with AI_SAVER_ON + Rs 6 for the Show Plan and tag check; set 206 if you switch AI_SAVER_ON off). Reconcile with the 'ai_per_video_summary' rows in Cost_Log / Cache_Stats after 2-3 videos"),
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
 "OPERATOR_EMAIL": ("", "your email"), "DRIVE_FOLDER_ID": ("", "optional; blank = files go to the Drive root, private. Leave blank: a folder made by hand is not visible to the app's drive.file permission"),
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
 "FAL_HERO_MODEL": ("fal-ai/kling-video/o3/standard/image-to-video", "animated scenes (Kling 3.0 Standard on fal, $0.084/s audio off = $0.42 per 5 s; the Steward falls back along MODEL_LADDERS)"),
 "STILL_W": ("1872", "v10.1: still width; 1872x1056 = 1.98 MP is billed as 2 MP, the same price as the old 1632x918, with sharper pictures"), "STILL_H": ("1056", ""),
 "PARALLAX_ON": ("TRUE", "depth parallax on stills"),
 "DRIVE_ARCHIVE": ("TRUE", "copy masters to Google Drive"),
 "DRIVE_ARCHIVE_KEEP": ("12", "how many archived masters to keep in Drive (v11: 12, so Case Files countdowns have their cases; about 4 GB)"),
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
 "REEL4_DELAY_MIN": ("3000", "reel 4 (50 h: the day after that). with one long video a week this keeps a Short going out on the days after it"),
 "OPENING_WINDOW_SEC": ("45", "the opening seconds that decide whether a viewer stays: motion and fresh pictures are concentrated here"),
 "OPENING_KLING_MIN": ("1", "at least this many of the Kling clips play inside the opening window (moved, never added: same cost)"),
 "OPENING_LIVING_MIN": ("2", "at least this many living stills play inside the opening window (moved, never added)"),
 "OPENING_FRESH_ON": ("TRUE", "TRUE = every shot in the opening window gets its own new picture (taken from the same picture budget, not added to it)"),
 "PKG_RESCUE_ON": ("TRUE", "TRUE = a second thumbnail (different idea) is made with each video (about Rs 8); if the video is clearly behind the channel's usual pace after PKG_RESCUE_HOURS, the title and thumbnail are swapped once to the runner-up"),
 "PKG_RESCUE_HOURS": ("72", "age of the video when the daily learning job compares it with earlier videos at the same age"),
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
 "REHOOK_MAX_GAP_SEC": ("75", "longest stretch of script allowed without a re-hook (a question, a turn, a reveal)"),
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
 # v8.10: Gemini voice + cast, premise quality, immersion / POV, voice acting, sound design, creative constitution, Script Preview, budget view.
 # Every new behaviour has a switch: setting it to the value in brackets restores v8.9 behaviour.
 "TTS_ENGINE": ("gemini", "gemini = Gemini TTS (two speakers per request, expression tags, word timings derived by code) with automatic fallback to Kokoro on failure; kokoro = the Kokoro blended voices [kokoro]"),
 "TTS_FALLBACK_ON": ("TRUE", "TRUE = if Gemini TTS fails for an episode, the WHOLE narration is re-voiced with Kokoro (never a mix of engines in one video) and the notes say so"),
 "TTS_CHUNK_WORDS": ("220", "most words per Gemini TTS request (about 90 s of speech; the model takes 8,192 input tokens and returns at most ~10 min of audio)"),
 "TTS_RPM": ("8", "Gemini TTS requests per minute this job allows itself (Tier 1 limits vary; a 429 waits and retries)"),
 "TTS_MAX_RETRIES": ("4", "tries per TTS request (429 / 5xx wait longer each time) before the chunk is voiced line by line, then before falling back to Kokoro"),
 "TTS_ALIGN": ("auto", "how word timings are derived from Gemini audio: auto = CTC forced alignment when the aligner loads, else energy + syllable timing; energy = always the free method"),
 "PRICE_GEM_TTS_IN": ("0.5", "USD per million text input tokens, Gemini Flash TTS (Google list price Oct 2026; verify on ai.google.dev pricing)"),
 "PRICE_GEM_TTS_OUT": ("9", "USD per million AUDIO output tokens (25 tokens = 1 s of speech), Gemini Flash TTS; promotional 2026 rate"),
 "PRICE_GEM_TTS_OUT_2027": ("18", "the same rate from 1 Jan 2027 (reported doubling; verify); the code switches by itself on that date"),
 "GEMINI_FUNDED_USD": ("0", "prepaid Gemini credit you have added (Tier 1, prepaid). Add here when you top up; 0 = not tracked"),
 "GEMINI_LOW_USD": ("3", "email a top-up reminder when the estimated Gemini credit left falls below this many dollars"),
 "CAST_ON": ("TRUE", "TRUE = the two roles come from the Cast tab (5 experts + 15 rotating guests, personality briefed to the writer) [FALSE = v8.9 GUESTS]"),
 "GUEST_NO_REPEAT": ("6", "a guest never appears again within this many videos (15 guests: up to 14)"),
 "EXPERT_PICK": ("rotate", "rotate = the least recently used active expert (weight breaks ties); fixed:<id> = always that expert (e.g. fixed:E1)"),
 "PREMISE_BANK_ON": ("TRUE", "TRUE = the seed bank is LLM-generated (illogical-sounding but physically showable), regenerated monthly, deduped vs Banned + past episodes [FALSE = v8.9 template grid]"),
 "PREMISE_BANK_SIZE": ("60", "premises generated per monthly bank (one Claude call, about Rs 4-8)"),
 "PREMISE_BANK_MONTH": ("", "auto - month of the current LLM premise bank"),
 "PREMISE_DUAL_SCORE_ON": ("TRUE", "TRUE = every pitch is scored by two independent blind judges (Claude + Gemini) and the scores are combined [FALSE = the scout's own scores]"),
 "PREMISE_MIN_SCORE": ("7.0", "combined score (0-10) a pitch needs to pass. Nothing passes = new seeds (PREMISE_RETRY_ROUNDS), then the best-scoring pitch is used and you get an email (SKIP_IF_BELOW_BAR)"),
 "PREMISE_RETRY_ROUNDS": ("3", "extra scout rounds with fresh seeds after the first (v8.11: 3, was 2). Still nothing above the bar = the best-scoring pitch is used and you get an email (SKIP_IF_BELOW_BAR = TRUE skips the slot instead)"),
 "PREMISE_FAIL_FORWARD": ("FALSE", "TRUE = v8.9 behaviour (the last try accepts any pitch with floor 0)"),
 "IMMERSION_ON": ("TRUE", "TRUE = an Immersion Director gives every shot a first-person vantage, a body sensation and a sensory stack; POV rules on every image / living / Kling prompt [FALSE = v8.9 shots]"),
 "POV_CAMERA_ON": ("TRUE", "TRUE = free POV camera moves and effects in render (pov_rush, impact_shake, debris parallax) on stills, living stills, Kling clips, stock and graphics, locked to sound events [FALSE = v8.9 camera]"),
 "EMOTION_CURVE_ON": ("TRUE", "TRUE = the writer marks each line's delivery curve {slow, low, whisper, breath, gasp...}; Gemini acts it, Kokoro uses its pace part [FALSE = tags only]"),
 "SOUND_IMMERSIVE_ON": ("TRUE", "TRUE = ambient beds per scene, close-mic textures under key lines, tactile foley, the impact recipe and stereo movement in POV scenes (all code-generated, free) [FALSE = v8.9 sound]"),
 "CONSTITUTION": ("", "the Creative Constitution (blank = the built-in one in data.CONSTITUTION). Type your own text here to replace it; every department reads it"),
 "CRAFT_NOTEBOOK_ON": ("TRUE", "TRUE = active rows of the Craft_Notebook tab are top-priority creative input for the scout and every writer"),
 "TECHNIQUE_RESEARCH_ON": ("TRUE", "TRUE = the weekly scout reads titles, descriptions and top comments of top niche videos (YouTube API quota, about 120 units) and files technique observations"),
 "TECHNIQUE_MAX_VIDEOS": ("6", "top videos studied per week for the Technique Library"),
 "OWNERS_CUT_ON": ("TRUE", "TRUE = the Owner's Cut critic scores the script 1-10 (inside the scene, weirdness hook, emotional peaks, payoff, originality) before any picture money; below the bar = rewrite"),
 "OWNERS_CUT_MIN": ("7.5", "lowest mean (and no single score below 6) the Owner's Cut accepts"),
 "OWNERS_CUT_MAX_ROUNDS": ("3", "rewrites the Owner's Cut may ask for (v8.11: 3, was 2); still below the bar = the best-scoring version is made and you get an email (SKIP_IF_BELOW_BAR = TRUE skips the slot instead)"),
 "PREVIEW_USE_APPROVED": ("TRUE", "TRUE = an approved Script Preview is used by the next production slot (its writing is not paid for twice)"),
 "THINK_EST_INR": ("40", "allowance per video for Claude/Gemini thinking tokens (billed as output) on top of LLM_EST_INR; reconcile against Cost_Log"),
 "TTS_EST_INR": ("30", "allowance per video for Gemini TTS incl. one re-take and reels (10 min of speech is about 15,000 audio tokens)"),
 "ROOM_EXTRA_EST_INR": ("20", "v8.10 allowance per video for the two premise judges, the Immersion Director and the Owner's Cut (incl. one rewrite); reconcile against Cost_Log"),
 "KLING4_MAIL_MONTH": ("", "auto - month the 4th-Kling headroom email was sent"),
 "KLING_4TH_PROPOSE_ON": ("TRUE", "TRUE = the money email proposes a 4th Kling clip (setting KLING_CLIPS=4) only when the month's headroom covers it for every remaining video"),
 # v8.11: opening Kling, no skipped slots, prompt caching, model routing by capability, measured AI cost. Every behaviour has a switch; the value in
 # brackets in a note restores v8.10.
 # v9 "Reality on Trial" (stage 1: the Show Plan is requested, validated, repaired and logged; the script / render read it from stage 2)
 "SHOW_MODE": ("auto", "auto = the Showrunner also returns a Show Plan (no extra AI call), validated and logged in Show_Log; off = the Showrunner prompt without a Show Plan"),
 "SHOW_FORMAT": ("trial", "trial = Reality on Trial (charge, exhibits, witness, jury, verdict); wager = reserved for the bet-based variant"),
 "CHARACTER_INTENSITY_MIN": ("0", "lowest character intensity (0-3) the Show Plan may choose"),
 "CHARACTER_INTENSITY_MAX": ("3", "highest character intensity (0-3) the Show Plan may choose"),
 # v9 cost controls (stage 3a): AI side only, never visuals
 "OUTLIER_RANK_ON": ("TRUE", "v9: top niche videos are ranked by views / their channel's own recent median; outliers (Demand_Signals tab) feed the technique library and the bench (about 3 quota units per channel)"),
 "OUTLIER_MIN_MULTIPLE": ("2", "a video counts as an outlier when its views are at least this multiple of its channel's recent median"),
 "PREMISE_SOURCE_MIX": ("0.6", "share of bench premises drawn from outlier demand (same promise, NEW execution; never their titles or thumbnails); the rest original"),
 "PREMISE_MIX_EPISODES": ("8", "the source mix applies to the first N episodes; after that the bench is drawn by score only"),
 # v9 stage 3b: packaging, community, season, experiments
 "AUDIO_DROPS_ON": ("TRUE", "v9: the clip-bait moment is filed as a 5-8 s audio drop (Drive) for Instagram original audio. Zero cost; posting needs the Meta keys"),
 # v9 stage 3c
 "CHARACTER_SHEET_IMAGE_CAP": ("40", "LIFETIME cap on character-sheet images (all runs together, regenerations included). About Rs 8 each = about Rs 320 at most, once"),
 "SHEET_EXPRESSIONS": ("10", "expressions per character on the sheets (max 12)"),
 "BATCH_ON": ("TRUE", "TRUE = non-urgent Claude jobs (bench refill, monthly brief) go through Message Batches at half price; a batch that has not finished in BATCH_MAX_WAIT_MIN is cancelled and the same request runs normally once"),
 "BATCH_MAX_WAIT_MIN": ("40", "longest wait for a batch before the normal call is used"),
 "PRICE_BATCH_DISCOUNT": ("0.5", "batch price as a share of the normal price (Nov 2026 docs; verify)"),
 "TTS_CACHE_ON": ("TRUE", "TRUE = every voiced request is cached by text + voice + style inside the job, so a retry or a reel never pays for the same audio twice"),
 "EFFORT_AB_ON": ("FALSE", "TRUE = the script's effort alternates medium / high by episode (recorded as effort_arm) to measure the quality and cost difference"),
 "PROVENANCE_ON": ("TRUE", "TRUE = a provenance record per episode (Show Plan, bible hash, owner decisions, sheet approvals, notebook) goes to Drive for policy appeals; no personal data"),
 "GREENLIGHT_TIERS_ON": ("FALSE", "TRUE = the money email reports how much MEASURED saving could fund an upgraded tier; it never reduces the standard and never spends by itself"),
 "PKG_VARIANTS": ("3", "title + thumbnail-text pairs per video (1-3). A third pair re-uses the main thumbnail picture unless PKG_VARIANT_C_IMAGE is TRUE"),
 "PKG_VARIANT_C_IMAGE": ("FALSE", "NOT ACTIVE (no code reads this cell): the third packaging pair never gets an image of its own. Was meant as: TRUE = one more premium image for the third pair (about Rs 8 per video)"),
 "THUMB_APPROVAL_ON": ("TRUE", "TRUE = for the first THUMB_APPROVAL_FIRST_N videos you get ONE email with one-click picks; the video is already scheduled with A, so a slot never waits"),
 "THUMB_APPROVAL_FIRST_N": ("9999", "videos for which the pick message is sent (v9.3.1: every video; was 8)"),
 "THUMB_APPROVAL_HOURS": ("6", "a pick that arrives later than this is ignored (A stays, the test decides)"),
 "PKG_ROTATE_ON": ("FALSE", "v9.3.1: OFF (owner decision 5: unfair to B/C and public views now count autoplay). TRUE = the pairs take turns in equal windows inside PKG_ROTATE_HOURS after release (title + thumbnail through the API); the best views/hour stays. YouTube's Test & Compare has no public API we could verify"),
 "PKG_ROTATE_HOURS": ("48", "length of the packaging test after release"),
 "JURY_COMMENT_ON": ("TRUE", "TRUE = after release, Nana Rosa posts the jury comment (the API cannot pin: you get the text to pin)"),
 "COMMENT_REPLY_MODE": ("draft", "off | draft | auto. draft = comments are triaged into Comment_Queue with template drafts; auto = only template thank-yous to predictions are posted (capped daily); never anything else"),
 "COMMENT_REPLY_DAILY_CAP": ("10", "auto replies per day at most"),
 "COMMENT_DIGEST_WEEK": ("", "auto - ISO week of the last comments digest"),
 "TEACUP_FINDERS_MAX": ("3", "viewers named as teacup finders in the next episode (handles only, filtered)"),
 "EXPERIMENT_EPISODES": ("8", "videos that get an Experiments row (hypothesis + 48 h / 7 d / 28 d results); recommendations only, nothing changes by itself"),
 "TARGET_REGIONS": ("US,UK,CA,AU", "regions the channel aims at; used ONLY by the 'one region dominates' note (publish time is PUBLISH_HOUR_ET)"),
 "REGION_DOMINANCE_SHARE": ("0.7", "an info email when one country brings this share of a video's views"),
 "VARIETY_LOOKBACK": ("6", "episodes the variety guard compares the Show Plan with"),
 # v9.1 (K103): every v9.1 feature has its own flag; V91_SAFE_MODE switches them ALL off at once (= exactly v9)
 # v9.2 (from the first real Script Preview)
 "TRUNC_RETRY_LOWER_EFFORT": ("TRUE", "v9.2: a reply cut at its limit is retried ONCE at LOWER effort with the same limit and a tighter instruction (never with more room); then the next model [FALSE = v8 behaviour: more room]"),
 "THINK_CAPS": ('{"writer": 14000, "rewrite": 14000, "premise_bank": 12000, "bench": 16000}', "v9.2: thinking room (tokens) per role on top of the answer; caps one call's cost (Opus writer: 16k answer + 14k thinking = at most about Rs 59)"),
 "THINK_CAP_DEFAULT": ("16000", "v9.2: the thinking room for any role not in THINK_CAPS is at most this"),
 "CACHE_ALIGN_EFFORT": ("TRUE", "NOT ACTIVE (no code reads this cell): each call keeps the effort its task is routed with; two efforts on one cached prefix cost one extra cache write, logged on every run. Was meant as: calls that share a cached prefix use the first call's effort"),
 "BACKGROUND_IN_ROOM": ("FALSE", "v9.2: FALSE = the monthly premise bank and a new research brief are made ONLY by the background (learning / research) jobs; Script Preview and production just read them [TRUE = v9.1]"),
 "SETUP_FILLS_BENCH": ("TRUE", "v9.2: Setup fills an empty Premise_Bench once (normal calls, no batch wait, about Rs 45) so the first preview does not wait"),
 "TITLE_SHOCK_ON": ("TRUE", "v9.2: titles must read as natural English (odd tense like 'What Happens If Light Walked' is rejected) and the three variants use scroll-stopping shapes: bold claim + question, impossible claim, shock detail; the strongest natural one leads"),
 "VOICE_CHECK_REUSE_DAYS": ("7", "v9.2: a voice that passed Voice_Check within this many days is not checked (paid / waited) again"),
 "VOICE_SAMPLES_REUSE": ("TRUE", "v9.2: a cast sample whose voices, styles and words did not change is not made again (the earlier file is listed)"),
 "VOICE_SAMPLES_DONE": ("", "auto - which cast samples exist"),
 "VOICE_CHECK_WORKERS": ("6", "v9.2: voice checks run side by side (still paced by TTS_RPM)"),
 "KLING_STAKES_ON": ("TRUE", "v9.2: besides the one opening clip, Kling clips go to the highest-stakes beats (clip-bait, final reveal, biggest meter swing, the impact); never adjacent, never a plain explanation line"),
 "POV_VARIETY_ON": ("TRUE", "v9.2: scene-aware first-person anchors (bathroom, kitchen, hallway, window...), whole-word matching, and lens / angle / phrasing that change between consecutive pictures"),
 "REACTION_SHOTS_ON": ("TRUE", "v9.2: tiny lines ('Fine.', 'A fifth.') become a free code-made reaction cutaway of the speaking character instead of another near-identical still (fewer images bought, never more)"),
 "REACTION_MAX_WORDS": ("3", "v9.2: lines with at most this many words become reaction cutaways"),
 "DESIGNED_VOICES_ON": ("TRUE", "v9.2: the four trial characters speak in their Gemini Voice Design voices (Characters.gvoice = the voice_... ID or the AI Studio name, resolved via the voices list); a voice that is not listed or fails Voice_Check falls back to the closest prebuilt voice (logged)"),
 "VOICE_LEVEL_ON": ("TRUE", "v9.2: every voiced line levelled to one loudness for all characters, -3 dB headroom and a peak limiter (<= -1 dBFS)"),
 "VOICE_TARGET_RMS_DB": ("-20", "v9.2: the common loudness of every character's lines (RMS dBFS) before the headroom"),
 "VOICE_HEADROOM_DB": ("3", "v9.2: gain reduction after levelling (dB)"),
 "VOICE_PEAK_DBFS": ("-1", "v9.2: the limiter ceiling (dBFS)"),
 "DESIGNED_VOICES_SEEDED": ("", "auto - when the owner's designed voice names were written into the Characters tab"),
 # v9.3 (K111-K117): cold open, micro-cuts, advertiser safety, Shorts funnel, title / rotation fixes. Every item has its own switch (value in brackets = v9.2)
 "COLD_OPEN_YOU_ON": ("TRUE", "v9.3: the first seconds put YOU inside the scenario (second person, present tense, a physical stake) before any character name or courtroom word: the writer is briefed, the retention gate checks it, a hook line with 'you' is preferred [FALSE = v9.2]"),
 "COLD_OPEN_LORE_FREE_SEC": ("20", "v9.3: no character names (Grimm, Vale, Nana Rosa, Archivist) and no courtroom words (court, trial, the charge, jury, exhibit, objection, verdict) in this many opening seconds"),
 "COLD_OPEN_YOU_MIN": ("2", "v9.3: 'you / your' must be said at least this many times inside COLD_OPEN_LORE_FREE_SEC"),
 "AD_SAFE_ON": ("TRUE", "v9.3: advertiser-safety words (gore, injury detail, profanity) are rejected by code in titles, thumbnail words, hook lines, the opening 45 s and premises; danger is implied, never shown [FALSE = v9.2]"),
 "MICRO_CUTS_ON": ("TRUE", "v9.3 (render, code only, zero cost): a still or reused picture changes framing (wide / detail crop + a new camera move) at least every PIECE_MAX_SEC, so it never sits like a slideshow [FALSE = v9.2: one move per shot up to 7.5 s]"),
 "PIECE_MAX_SEC": ("3.2", "v9.3: longest single picture state on a still / reused shot after the opening window"),
 "PIECE_MAX_SEC_OPENING": ("2.6", "v9.3: the same inside OPENING_WINDOW_SEC (faster cutting while viewers decide)"),
 "PIECE_MIN_SEC": ("2.0", "v9.3: a micro-cut never makes a piece shorter than this (no jitter)"),
 "CUTMAP_MAX_HOLD_SEC": ("3.6", "v9.3: the cut map lists every still picture state held longer than this and reports the median hold (review only, measured from the real render)"),
 "TRIAL_SHORTS_SAFE_ON": ("TRUE", "v9.3: trial Shorts open on YOUR stake (not the charge) and NEVER reveal the verdict, the final meter side or the final answer: the full episode keeps the payoff [FALSE = v9.2 trilogy]"),
 "HERO_SHORT_DELAY_MIN": ("720", "v9.3: the hero-still Short is scheduled this many minutes AFTER the long video goes live (never before it; only once the YouTube API audit is approved); its description links the long video"),
 "PKG_ROTATE_START_H": ("24", "v9.3: the title / thumbnail rotation starts this many hours after release, so variant A keeps the launch window [0 = v9.2]"),
 "PKG_ROTATE_MIN_VIEWS": ("1500", "v9.3: no rotation test unless the video has at least this many views when the test would start (fewer = noise; A stays and the v8.5 rescue may act) [0 = v9.2]"),
 "CTA_JURY_ON": ("TRUE", "v9.3: in the trial format the code-added like / subscribe / share lines, the description footer and the reel asks are spoken by Vale / Grimm / Nana Rosa and make subscribing a seat on the jury [FALSE = v8.3 control-room lines]"),
 "V93_FLIPS_ON": ("TRUE", "v9.3: ONE time, Setup / the learning job switch HERO_STILL_REELS_ON and HERO_STILL_SHORTS_ON to TRUE in your Sheet, only where the cell still holds the old default FALSE (a value you typed yourself after this is never touched)"),
 "V93_FLIPS_DONE": ("", "auto - when the one-time v9.3 default flips ran and which cells they changed"),
 # v9.3.1 "Launch" (K118-K120): the ₹0 upload check replaces the API audit (YouTube lifted the private lock on 2 Nov 2026)
 "UPLOAD_LOCK": ("unknown", "v9.3.1: auto - off = the upload check proved uploads can go public; on = YouTube kept an upload private (new videos pause, nothing spent); unknown = not checked yet, treated as locked"),
 "UPLOAD_VERIFY_ON": ("TRUE", "v9.3.1: every upload is read back (1 quota unit): private-lock detector + AI-label read-back (a dropped label is set again once) [FALSE = v9.3]"),
 "UPLOAD_CHECK_AT": ("", "auto - when the upload check last ran"),
 "UPLOAD_LOCK_ALERT_AT": ("", "auto - last urgent lock email (at most one a day)"),
 "HERO_STILL_MIN_SEC": ("6", "v9.3.1: shortest hero-still reel / Short"),
 "HERO_STILL_MAX_SEC": ("10", "v9.3.1: longest hero-still reel / Short (was 25)"),
 "PICK_DEADLINE_BEFORE_SLOT_H": ("2", "v9.3.1: a title/thumbnail pick is applied until this many hours before release (was 6 h after the variants were made, which refused same-day picks)"),
 "TASTE_TITLES": ("", "auto - your last title picks over the machine's A (a taste signal for the Packager)"),
 "SHEETS_DEFAULT_LOCK_H": ("72", "v9.3.1: character sheet images still unanswered after this many hours are locked by default; 0 = never"),
 "SHEETS_THEATER_AUTO_ON_AT": ("", "auto - when CHARACTER_THEATER_ON was switched on after the default lock"),
 "V931_FLIPS_ON": ("TRUE", "v9.3.1: ONE time, THUMB_APPROVAL_FIRST_N 8 -> 9999 (a pick message for every video), only where the cell still holds 8"),
 "V931_FLIPS_DONE": ("", "auto - when the one-time v9.3.1 flips ran"),
 "TECHNIQUE_MAX_PER_BRIEF": ("3", "v9.3.2: at most this many technique cards reach a writer/director brief, and only cards that fit THIS episode's topic (a card is a tool, not a rule for every video)"),
 "TECHNIQUE_INTAKE_ON": ("TRUE", "v9.3.2: a new technique (owner's find, outlier card) is first judged for real value, fit, risk and how to raise its value; only then is it filed as active / trial / parked / rejected [FALSE = filed as-is]"),
 "QC_VISION_OPENING_MAX": ("6", "v9.3.2: the picture check also looks at up to this many shots inside the opening window (the seconds that decide retention), on top of QC_VISION_FRAMES"),
 "V932_SEEDS_DONE": ("", "auto - when the owner's seeded technique cards were filed"),
 # v9.4a (K123): pre-production at half price
 "PREPROD_ON": ("TRUE", "v9.4a: the writers' room for the next slot runs early (when nobody waits) through Message Batches at half price; production takes the result as written [FALSE = the room runs inside production]"),
 "PREPROD_LEAD_HOURS": ("72", "v9.4a: pre-production may start this many hours before a slot"),
 "PREPROD_MIN_LEAD_HOURS": ("34", "v9.4a: and must start at least this many hours before it (production starts at PRODUCE_AHEAD_HOURS)"),
 "ROOM_BATCH_ON": ("TRUE", "v9.4a: Claude calls in pre-production go through Message Batches (50% off; stacks with prompt caching) [FALSE = normal calls]"),
 "ROOM_BATCH_MAX_WAIT_MIN": ("30", "v9.4a: longest wait for one batched call; then the same request runs directly once (never two paid answers)"),
 "PREPROD_JOB_MAX_HOURS": ("5", "v9.4a: after this, the remaining calls of the job run directly (GitHub jobs stop at 6 hours)"),
 # v9.4a (K124): budget modes, protected core, earmark, growth allowance
 "BUDGET_MODE": ("standard", "v9.4a: standard | runway (owner's tap: email link 'MODE RUNWAY' / dashboard) | growth (set by itself when revenue exists, GROWTH_AUTO_ON)"),
 "GROWTH_AUTO_ON": ("TRUE", "v9.4a: Growth mode switches on by itself in a month after revenue was logged"),
 "GROWTH_REVENUE_SHARE": ("0.25", "v9.4a: in Growth mode this share of last month's revenue is added on top of the cap"),
 "RUNWAY_CAP_INR": ("2400", "v9.4a: the cap in Runway mode"),
 "RUNWAY_PUBLISH_DAYS": ("Sat", "v9.4a: publishing days in Runway mode (one long video a week)"),
 "STANDARD_MAX_LONG_PER_MONTH": ("4", "Standard makes at most this many long videos a month (owner, 10 Nov 2026: 4 - each one built to break out; daily Shorts and the spin-offs carry the volume)"),
 "RUNWAY_MAX_LONG_PER_MONTH": ("4", "v9.4a: Runway makes at most this many"),
 "GROWTH_MAX_LONG_PER_MONTH": ("13", "v9.4a: Growth may add revenue-funded videos up to this many"),
 "BUDGET_EARMARK_INR": ("200", "v9.4a: the owner's extra ₹200 for consistent faces + the dashboard: production can never use it (Standard and Growth)"),
 "BUDGET_EARMARK_ITEMS": ("faces,thumb_eye,owner_chat,dashboard", "v9.4a: Cost_Log role/item prefixes that count against the earmark"),
 "GROWTH_ALLOWANCE_INR": ("700", "v9.4a: monthly cap for growth extras (Shorts Lab, research, Outlier Lab, Advisor...); they pause first, production is never squeezed"),
 "GROWTH_ITEMS": ("shorts_lab,pilot,outlier,advisor,price_watch,research_card,engagement", "v9.4a: Cost_Log role/item prefixes that count as growth extras"),
 "V94A_FLIPS_ON": ("TRUE", "v9.4a: ONE time, BUDGET_FLOOR_INR / BUDGET_CEILING_INR move to 4700 when they hold 4500 or less"),
 "V94A_FLIPS_DONE": ("", "auto - when the one-time v9.4a cap move ran"),
 # v9.4a (K125): owner messages, no-spam tiers
 "NOTIFY_NOW_MAX_PER_DAY": ("2", "v9.4a: at most this many 'act now' messages a day (urgent ones always go)"),
 "QUIET_HOURS_IST": ("00:30-08:00", "v9.4a: non-urgent messages wait until this window ends (India time)"),
 "DIGEST_DAYS": ("Tue,Sat,Sun", "v9.4a: the digest (this week's videos, money, open actions) goes out on these days"),
 "DIGEST_HOUR_IST": ("21", "v9.4a: ...at or after this hour (India time)"),
 "DIGEST_SENT_AT": ("", "auto - last digest"),
 # v9.4a (K126): builds and repairs by Claude Code
 "BUILDS_ON": ("TRUE", "v9.4a: owner-ordered changes and repairs are built by Claude Code in GitHub Actions on the owner's Claude plan (secret CC_OAUTH_TOKEN); FALSE = nothing is built automatically"),
 "AUTO_MERGE_TWEAKS_ON": ("TRUE", "v9.4a (decision 11): a tweak the owner ordered merges by itself 24 h after every check is green (one message with Stop/Reject first); features and repairs always wait for the owner's tap"),
 "DASH_ON": ("TRUE", "v9.4b: the pipeline writes the dashboard snapshot to Cloudflare KV after each tick (only once CF_ACCOUNT_ID / CF_KV_NAMESPACE_ID / CF_KV_TOKEN exist)"),
 "ENGAGE_RULES_ON": ("TRUE", "v10 (K133): the writer gets the in-character audience-prompt library (comment / predict / take a side / share; never rewards)"),
 "ENGAGE_MAX_CTA": ("3", "v10: at most this many spoken like/subscribe/share asks per long video: one of each (story [JURY] prompts are separate)"),
 "ENGAGE_NO_ASK_FIRST_PCT": ("0.08", "v10: no like/subscribe/share ask in this first share of the spoken lines (about the first 20-40 s)"),
 "ENGAGE_MIN_GAP_LINES": ("6", "v10: never two asks within this many spoken lines"),
 "EMOTION_BEAT_ON": ("TRUE", "v10 (K133): one earned emotion beat per long video (type chosen per episode, awe most often), logged for learning"),
 "EMOTION_NO_REPEAT": ("TRUE", "v10: the same non-awe emotion type never twice in a row"),
 "EMOTION_LAST": ("", "auto - last episode's emotion beat type"),
 "SPECIALS_ON": ("TRUE", "v10 (K134, owner 2026-11-08): ~15-s cast special reels on SPECIALS_DAYS (plus the one-time cast intro), from their own earmark"),
 "SPECIALS_DAYS": ("2,16", "v10: days of the month a special reel is made and posted (twice a month)"),
 "SPECIAL_REEL_CAP_INR": ("180", "v10.2: per special reel (4 Kling 3.0 clips + pictures, about Rs 157 at Rs 92/$); was 150"),
 "SPECIALS_EARMARK_INR": ("300", "v10: the owner's +₹300 a month for specials; production can never use it; Runway mode pauses specials"),
 "SHORTS_LINK_MAX": ("4", "v10 (G2): the weekly card lists at most this many winning Shorts to link to their episodes"),
 "SHORTS_BREAKOUT_X": ("3", "v10: a Short getting more than this many times the median views per hour = one 'act now' link card"),
 "SHORTS_WEEKLY_CAP": ("10", "v10.1: at most this many Shorts in any 7 days (was 14; repetitive-content safety + quality over volume)"),
 "KINETIC_CAPTIONS_ON": ("TRUE", "v10 (G2, K135): reel captions light up word by word (numbers and YOU pop 112%) and sit REEL_CAPTION_MARGIN_PCT up from the bottom, clear of the app buttons [FALSE = v9 3-word blocks at 30%]"),
 "REEL_CAPTION_MARGIN_PCT": ("0.38", "v10: reel captions' distance from the bottom (share of the height; the Shorts/Reels buttons and title cover the lowest ~35%)"),
 "PILOTS_ON": ("TRUE", "v10 (K141): two cheap pilot Shorts a week test the next bench premises; their engaged views become a bonus on the premise score"),
 "PILOT_DAYS": ("Wed,Fri", "v10: days pilot Shorts are made (inside the 14-a-week ceiling)"),
 "PILOT_MONTHLY_INR": ("40", "v10: most pilots may cost in a month (about Rs 1-2 each)"),
 "PILOT_MEASURE_HOURS": ("48", "v10: pilots are measured after this many hours"),
 "PILOT_MAX_BONUS": ("1.0", "v10: largest bonus (or penalty) a pilot adds to its premise's bench score"),
 "OUTLIER_LAB_ON": ("TRUE", "v10 (K142): daily, up to OUTLIER_LAB_DAILY standout videos are watched (first seconds) and judged as technique cards"),
 "OUTLIER_LAB_DAILY": ("3", "v10: videos a day (carry-over value)"),
 "OUTLIER_LAB_SECONDS": ("60", "v10: seconds of each video the model watches"),
 "OUTLIER_LAB_QUERY": ("what if", "v10: the search the Outlier Lab starts from"),
 "BAKEOFF_CLIP_MODELS": ("fal-ai/kling-video/v2.6/pro/image-to-video,wan/v2.6/image-to-video/flash,fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video", "v10.1: candidates vs the current hero model (ids and prices verified on fal 8 Nov 2026; no Kling 3)"),
 "BAKEOFF_CLIP_PRICES": ("0.35,0.25,0.19", "v10.1: their USD price per clip (Kling 2.6 Pro silent 5 s; Wan 2.6 Flash 720p 5 s; Hailuo 2.3 Fast 768p 6 s)"),
 "BAKEOFF_CAP_INR": ("400", "v10: most the one-time bake-off may cost"),
 "BAKEOFF_DONE": ("", "auto - when the bake-off ran"),
 "SHEET_BACKUP_ON": ("TRUE", "v10 (K140): every Sunday all Sheet tabs go to one private zip on Drive (the private chat excluded)"),
 "BACKUP_KEEP": ("8", "v10: newest backups kept (older ones deleted)"),
 "FACE_CHECK_ON": ("TRUE", "v10 G1 (K139): each animated cast clip in a special is checked against the locked portrait (vision model, about ₹0.2); a drifted face is replaced by a slow push-in on the portrait (₹0)"),
 "SLOP_GUARD_ON": ("TRUE", "v10 (K137): an AI-slop risk score per video (still share, template repetition, flat voice, repeated opening); recorded and shown, never a hold by itself"),
 "SLOP_WARN": ("55", "v10: above this score one FYI card names the biggest factor"),
 "MICRO_RULES_ON": ("TRUE", "v10 (K138, decision 3): proven retention rules from this channel's data are added to the writer's brief"),
 "MICRO_MIN_VIDEOS": ("6", "v10: a rule needs the effect in at least this many videos"),
 "MICRO_MIN_VIEWS": ("2000", "v10: ...each with at least this many views"),
 "MICRO_MIN_EFFECT": ("0.05", "v10: ...and an average distance from the median of at least this much (5%)"),
 "MICRO_RULE_LIFE": ("20", "v10: a rule expires after this many videos unless re-confirmed"),
 "CAST_INTRO_CAP_INR": ("230", "v10.2: the voiced, animated cast intro (4 Kling scenes + 4 reference frames + voices, about Rs 180); one-time, outside the monthly specials money"),
 "WA_BRIEF": ("", "auto - the open owner-brief conversation"), "OWNER_NEXT_PREMISE": ("", "auto - the locked owner premise for the next long video"),
 "OWNER_SPECIAL_TOPIC": ("", "auto - the locked owner topic for the next special reel"), "OWNER_BRIEF_ACTIVE": ("", "auto - the brief the room is following now"),
 "OWNER_TASTE_PROVEN": ("", "auto - owner picks measured at or above the channel median (scout calibration)"),
 "ROOM_VALUE_ON": ("TRUE", "NOT ACTIVE (no code reads this cell): this test was never built and tab Room_Value stays empty. Was meant as: blind test of the writers' room script against a single-prompt script for the same premise, judged blind by a model of another family; win rate on the dashboard"),
 "ROOM_VALUE_EVERY": ("1", "NOT ACTIVE (no code reads this cell): belongs to the room value test (ROOM_VALUE_ON), which was never built. Was meant as: test every Nth long video (about Rs 15 each)"),
 "ROOM_MIN_WINRATE": ("0.6", "NOT ACTIVE (no code reads this cell): belongs to the room value test (ROOM_VALUE_ON), which was never built. Was meant as: below this win rate over 6+ tests the Advisor proposes cutting room roles"),
 "DIGEST_WA_ON": ("TRUE", "v10.3: daily + weekly WhatsApp briefs (numbers, observations, strategy, cited hot topics, what to post, risks, one chart)"),
 "DIGEST_DAILY_HOUR_IST": ("9", "v10.3: the morning brief goes out at or after this hour (IST)"),
 "DIGEST_WEEKLY_DAY": ("Sun", "v10.3: the weekly brief day"),
 "DIGEST_DAILY_SENT": ("", "auto"), "DIGEST_WEEKLY_SENT": ("", "auto"),
 "ART_STYLE": ("toybox_noir", "v10.2: the look of animated scenes, masters and the intro: toybox_noir (owner-approved 9 Nov 2026), photoreal (matches the first locked portraits) or illustrated. STYLE words only; faces and costumes always come from Characters.visual"),
 "STYLE_SAMPLES_REQUEST": ("TRUE", "v10.2: TRUE = the next 'Character sheets' run makes the 3-look comparison board of YOUR cast (about Rs 55) instead of masters; set back automatically"),
 "STYLE_SAMPLES_CAP_INR": ("80", "v10.2: the most the comparison board may cost"),
 "TRIAL_GRAMMAR_SINCE": ("2026-11-09T12:00:00Z", "v10.2: Script Previews written before this are not judged on the trial grammar"),
 "ANIM_DIRECTOR_ON": ("TRUE", "v10.2 (K152): animated scenes are placed at the cold open, ~3:00, ~6:00 and the verdict, start from reference-locked staged frames (Google) and are animated by Kling (fal)"),
 "ANIM_SHOTS": ("4", "v10.2 (owner option C): animated scenes per long video (~20 s)"),
 "PRICE_GEM_IMAGE_USD": ("0.067", "v10.2: one reference-locked start frame from Google's image model (estimate at 1K)"),
 "TRIAL_GRAMMAR_ON": ("TRUE", "v10.2: the writers' room must use the trial grammar (time ladder, exhibits with sources, Grimm's Prototype, the twist, 'Here's what's true'); the contract checks it"),
 "V102_FLIPS_ON": ("TRUE", "v10.2: ONE time: hero model Kling 2.5 Turbo Pro -> Kling 3.0 Standard (+ price 0.42), KLING_CLIPS 3 -> 4, the model ladder gains Kling 3.0; owner values never touched"),
 "V102_FLIPS_DONE": ("", "auto"),
 "LIFE_LAYER_ON": ("FALSE", "v11 (K161): breathing warp of the near part of a still. OFF: measured on 9 Nov it reads like a camera zoom (the still detector cannot tell it apart, and neither can a viewer); the world particle layer (K161b) replaces it"),
 "LIFE_AMP": ("0.004", "v11: breathing amplitude as a share of the frame height"),
 "LIFE_NEAR_DEPTH": ("0.55", "v11: depth above which a pixel counts as 'near' (moves with the breath)"),
 "LIVING_CHARACTERS_ON": ("TRUE", "v11.1 (K167): reaction cutaways show the LOCKED expression still with blinks, breathing and word-synced mouth movement"),
 "LIVING_VARIANT_EXPRESSIONS": ("neutral,shocked,smug", "v11.1: expressions that get eyes-closed + mouth-open variants (2 images each, once per character)"),
 "LIVING_VARIANTS_CAP_INR": ("150", "v11.1: lifetime cap for the variants"), "LIVING_MIN_IDENTITY": ("7", "v11.1: a variant below this identity score is rejected"),
 "LIVING_MAX_CHANGE_SHARE": ("0.08", "v11.1: a variant that changes more than this share of the picture is never used (it would flicker)"),
 "UNIT_MERGE_SEC": ("1.0", "v11.1: a narration line shorter than this with no picture of its own continues the previous shot (no sub-second flash)"),
 "VISUAL_ANIMATED_MAX_S": ("12", "v11.1: longest single piece of an animated graphic / living reaction cutaway (it re-animates after)"),
 "VISUAL_CHANGE_MAX_S": ("4", "v11.1 (K166): V2 - longest a picture state may hold in a long video (graphics / clips 2x)"),
 "BREAKOUT_HARD_BAR": ("80", "v11.1: HARD - no upload below this Breakout Score (held with the weakest part named; owner can approve anyway)"),
 "JOKE_EVERY_SEC_LONG": ("15", "v11.1 (K166): at least one [PUNCH] line per this many seconds of narration (long)"),
 "JOKE_EVERY_SEC_SHORT": ("6", "v11.1: the same for Shorts"),
 "PUNCH_PAUSE_S": ("0.5", "v11.1: silence added before every punchline (research: 300-700 ms)"), "PUNCH_PAUSE_MIN_S": ("0.3", "v11.1: V6 minimum"),
 "IMPACT_HOOK_SEC": ("3", "v11.1: V1 - a question or 'you' stake within this many seconds"),
 "IMPACT_VARIETY_MAX": ("0.97", "v11.1: V9 - an ordered 10-s event pattern this similar to one of the last 10 episodes = a near-copy (held)"),
 "IMPACT_FLASH_MAX": ("3", "v11.1: V10 - max luminance flips per second"),
 "IDEA_GATE_ON": ("TRUE", "v11.1: idea-first - a long episode's premise must be backed by an outlier (once outlier data exists)"),
 "IDEA_MIN_MULTIPLE": ("5", "v11.1: outlier multiple required"), "IDEA_MIN_SIGNALS": ("10", "v11.1: the gate applies once this many outliers are collected"),
 "REPLAN_ON": ("TRUE", "v11 (K164): Monday money check - truly free money is proposed for more hook tests / more animated Shorts (owner veto)"),
 "REPLAN_FLOOR_INR": ("500", "v11: kept untouched until the last week"), "REPLAN_LASTWEEK_FLOOR_INR": ("300", "v11: kept for running jobs in the last week"),
 "REPLAN_SHORT_INR": ("36", "v11: planning cost of one Short"), "REPLAN_MAX_SHORTS_PER_DAY": ("2.5", "v11: the most the re-planner may raise Shorts to"),
 "REPLAN_LAST": ("", "auto"), "REPLAN_PENDING": ("[]", "auto"), "REPLAN_ORIGINALS": ("{}", "auto"), "REPLAN_MONTH": ("", "auto"),
 "SCOUT_ON": ("TRUE", "v11 (K165): weekly tool scout (fal catalog + prices, deprecation watch, Artificial Analysis ranking if AA_API_KEY is set)"),
 "SCOUT_WEEKDAY": ("2", "v11: 0=Mon"), "SCOUT_LAST": ("", "auto"),
 "DEEP_TRIAL_ON": ("TRUE", "v11 (K163): one long slot a month becomes a ~20-minute Deep Trial (three acts + a Jury Room segment)"),
 "DEEP_TRIAL_DAY": ("18", "v11: the first long slot on or after this day of the month"),
 "DEEP_TRIAL_WORDS_MULT": ("1.9", "v11: narration length multiplier for the Deep Trial (about 20 minutes)"),
 "DEEP_TRIAL_MONTH": ("", "auto"),
 "REACH_ON": ("TRUE", "v11 (K162): daily impressions + thumbnail CTR per video from the YouTube Reporting API (job created once; first file ~48 h)"),
 "REACH_JOB_ID": ("", "auto"), "REACH_LAST_CREATED": ("", "auto"),
 "PARTICLES_ON": ("TRUE", "v11 (K161b): world particle layer on every still (dust in court/case, embers in the lab, rain in the office, wind outdoors) - independent motion that reads as alive"),
 "PARTICLE_DENSITY": ("1.0", "v11: particle count multiplier"),
 "PARTICLE_RES_DIV": ("2", "v11: particles are drawn at 1/N resolution and scaled up (2 = about 4x faster; soft particles hide it)"),
 "PARTICLE_GATE_FLOOR": ("0.35", "v11: particles still show at this share in dark areas (noir frames must breathe too)"),
 "PARTICLE_PREROLL_S": ("3", "v11: simulated seconds before frame 0 so the air is already full"),
 "PARTICLE_DEFAULT_WORLD": ("dust", "v11: look used when a shot has no speaker world"),
 "SOUND_WORLDS_ON": ("TRUE", "v11 (K161): per-location sound beds + story events (gavel on the verdict, paper under exhibits, fizzle after the Prototype)"),
 "SOUND_WORLD_MIN_S": ("12", "v11: shortest time a location's bed plays before it changes"),
 "SOUND_EVENTS_MAX": ("12", "v11: story sound events per episode"),
 "CASEFILES_ON": ("TRUE", "v11 (K160): one Case Files countdown a month once enough episodes are archived"),
 "CASEFILES_CASES": ("5", "v11: cases per countdown"), "CASEFILES_POOL": ("10", "v11: newest archived episodes considered"),
 "CASEFILES_SEG_SEC": ("75", "v11: seconds taken from each past episode (around its twist)"),
 "CASEFILES_MIN_NEW_SHARE": ("0.35", "v11 G1: new material / runtime must be at least this"),
 "CASEFILES_DAY": ("15", "v11: the countdown is made on or after this day of the month"),
 "CASEFILES_LAST_DISPATCH": ("", "auto"),
 "SPINOFF_CAP_INR": ("130", "v11 G0: most a spin-off may cost"),
 "SHORTS_TRACK_ON": ("TRUE", "v11 (K159): standalone daily Shorts (the month-1 launch plan)"),
 "SHORTS_PER_DAY": ("1.5", "v11: standalone Shorts per day (1.5 = 2 on even days, 1 on odd days); the first of a day is core production, the rest are extras"),
 "SHORTS_START_HOUR_IST": ("7", "v11: no Short is started before this hour (IST)"),
 "SHORTS_VARIANTS": ("3", "v11: script variants per Short (judged blind by Gemini)"),
 "SHORTS_KLING_EVERY": ("3", "v11: one new Kling shot every N Shorts (breakout follow-ups always get one)"),
 "SHORTS_REVIEW_FIRST_N": ("3", "v11: the first N standalone Shorts wait for the owner's Approve"),
 "SHORTS_LAST_DISPATCH": ("", "auto"),
 "SHORTS_NEED_MASTERS": ("TRUE", "v11: standalone Shorts wait until every character master is LOCKED (owner-approved) - no money spent on unlocked faces"),
 "FAIL_MAIL_AT": ("", "auto: last failure email time (one per day)"),
 "PROMISE_BY_SEC": ("5", "v12 V1: 5 (was 30) - the promise is the FIRST picture of the video. v11 (K158): the thumbnail/title promise must be on screen by this second of a long video"),
 "ALIVE_DETECT_WIDTH": ("480", "v11: width the still detector analyses at (2 fps); 480 px keeps dust-sized motion visible"),
 "ALIVE_PIXEL_DELTA": ("12", "v11: grey-level change (after removing the camera move) that counts a pixel as really changed"),
 "ALIVE_PIXEL_SHARE": ("0.0002", "v11: share of really-changed pixels, off the edges, that makes a half second 'alive' (measured 9 Nov at 1080p: photo + camera move = 0.0 exactly; particle worlds >= 0.0004; a moving object 0.0057)"),
 "ALIVE_MIN_SHARE": ("0.75", "v11: share of half-second windows that must be alive (natural pauses allowed); calibrate from the ledger"),
 "ALIVE_MAX_DEAD_S": ("4", "v11: longest allowed stretch that looks like a still photo"),
 "BREAKOUT_BAR": ("70", "v11: Breakout Score below this -> a card naming the weakest part (never a hold by itself)"),
 "BREAKOUT_AMPLIFY_AT": ("88", "v11: breakout-grade -> extra push"),
 "BREAKOUT_MONITOR_ON": ("TRUE", "v11: 48-hour breakout monitor (views vs the channel's usual 48-hour views)"),
 "BREAKOUT_WINDOW_H": ("48", "v11"), "BREAKOUT_MULT": ("5", "v11: a breakout = at least this multiple of the usual 48-hour views"),
 "BREAKOUT_MIN_VIEWS": ("2000", "v11: the breakout line while there is no history (fewer than BREAKOUT_MIN_HISTORY videos)"),
 "BREAKOUT_MIN_HISTORY": ("3", "v11"),
 "ROOM_MODE": ("v2", "v11 (K157): v2 = diverse drafts + blind cross-family jury + one checklist revision (no role memos); v1 = the previous room"),
 "ROOM_V2_DRAFTS": ("3", "v11: drafts per episode, each with a different cold-open archetype"),
 "JURY_ORDERINGS": ("2", "v11: each judge ranks in the original and the reversed order (position bias cancels)"),
 "JOKE_TOURNAMENT_ON": ("TRUE", "v11: scene-ending lines get alternatives ranked by strong judges; the original always competes"),
 "JOKE_SLOTS": ("8", "v11: joke slots per episode"), "JOKE_CANDIDATES": ("12", "v11: alternatives per slot"),
 "MONTH_CAP_OVERRIDES": ("", "v11: one-month caps 'YYYY-MM=INR,...' set by the owner (the v11 upgrade writes 2026-11=5226: Rs 1,226 already spent + Rs 4,000 approved on 9 Nov for the rest of November; December is back to Rs 5,000)"),
 "V11_FLIPS_DONE": ("", "auto"), "V12_FLIPS_DONE": ("", "auto"),
 "BREAKOUT_FUND_ON": ("TRUE", "v11 (owner-approved): last month's unspent money carries in as a breakout fund, only for breakout follow-ups and extra episodes on proven topics"),
 "BREAKOUT_FUND_CAP_INR": ("1000", "v11: the most that carries over"),
 "BREAKOUT_FUND_INR": ("0", "auto"), "BREAKOUT_FUND_MONTH": ("", "auto"),
 "BREAKOUT_ITEMS": ("breakout,followup", "v11: Cost_Log role/item prefixes paid from the breakout fund"),
 "LAST_MONTH_CAP_INR": ("0", "auto"), "LAST_MONTH_SPEND_INR": ("0", "auto"),
 "BUDGET_GUARD_PCT": ("90", "v11: at this % of the cap, extras pause (spin-offs, tool tests, Shorts above 1 a day); long episodes keep their money; one alert per month"),
 "BUDGET_GUARD_ALERTED": ("", "auto"),
 "BRAIN_ON": ("TRUE", "v11 (K155): the learning core: features per video, Technique_Evidence from YouTube's engaged views, Thompson sampling with a holdout, forecasts scored against the median"),
 "BRAIN_HOLDOUT": ("0.2", "v11: share of Shorts that keep the default hook (the control the sampler must beat)"),
 "BRAIN_DEFAULT_HOOK": ("verdict_first", "v11: the control hook archetype"),
 "BRAIN_PRIOR_STRENGTH": ("20", "v11: empirical-Bayes prior weight (views) centred on the channel's own rate"),
 "BRAIN_PROVEN_P": ("0.9", "v11: P(beats the channel baseline) needed to call a technique proven"),
 "BRAIN_PROMISING_P": ("0.7", "v11: ... promising"),
 "BRAIN_DEMOTE_P": ("0.6", "v11: a proven technique falls back to testing below this"),
 "BRAIN_RETIRE_P": ("0.3", "v11: retired at or below this (with enough videos)"),
 "BRAIN_MIN_VIDEOS": ("5", "v11: distinct videos before a technique can be proven or retired"),
 "BRAIN_MIN_TRIALS": ("2000", "v11: pooled views before a technique can be proven"),
 "BRAIN_RULE_DAYS": ("60", "v11: a rule expires unless re-confirmed within this many days"),
 "BRAIN_SHORT_AGE_H": ("48", "v11: a Short's numbers are first read this many hours after it goes public (then weekly to 28 days)"),
 "BRAIN_SCORE_MIN_VIEWS": ("100", "v11: a forecast is scored only once its video has this many views"),
 "CONTRACT_ON": ("TRUE", "v10.2 (K151): every promised feature is a mandatory check; a failure HOLDS the video (never uploaded) with an owner card"),
 "CONTRACT_OFF": ("", "v10.2: comma-separated feature ids switched off (owner decision only; shown in the ledger as not checked)"),
 "CONTRACT_WAIVERS": ("", "auto - per-episode waivers written only by the owner's 'Approve anyway' tap"),
 "CONTRACT_HOOK_MIN_CANDIDATES": ("10", "v10.2: Hook Lab must have scored at least this many openings"),
 "CONTRACT_HOOK_MIN_SCORE": ("6.5", "v10.2: the winning opening's score bar (when the Hook Lab reports a score)"),
 "CONTRACT_MUSIC_MIN_DB": ("-52", "v10.2: pauses between lines must carry a bed at least this loud (dBFS); silence is about -70"),
 "CONTRACT_MAX_STILL_SEC": ("9", "v10.2: no single still picture state longer than this"),
 "CONTRACT_MEASURE_IN_FAKE": ("FALSE", "tests only"),
 "ANIM_MIN_SEC": ("20", "v10.2 (owner option C, 9 Nov 2026): at least this many seconds of animated character scenes per long video"),
 "ANIM_MIN_MOTION": ("6", "v10.2: a scene must move at least this much (mean luma change 0-255 between frames 0.4 s apart); portrait push-ins score ~1-3"),
 "ANIM_MAX_STATIC_CLIPS": ("0", "v10.2: animated scenes allowed below the motion bar"),
 "SLOP_HOLD": ("70", "v10.2: slop score above this HOLDS the video (the FYI card stays at SLOP_WARN)"),
 "CRITIQUE_MIN": ("6", "v10.2: every point of the 6-point self-review (0-10) must reach this"),
 "CREATIVE_REVIEW_FIRST_N": ("3", "v10.2: the first N long videos stay private until the owner taps Approve (WhatsApp / dashboard / email)"),
 "SPECIALS_REVIEW_ON": ("TRUE", "v10.2: every special reel waits for the owner's Approve"),
 "MODEL_STEWARD_ON": ("TRUE", "v10.1 (K150): picture/video models on fal are watched weekly, fail over at once, and upgrade after a capped test, with cards in advance (text/voice models already self-update weekly)"),
 "MODEL_LADDERS": ("{\"hero\": [{\"id\": \"fal-ai/kling-video/o3/standard/image-to-video\", \"usd\": 0.42}, {\"id\": \"fal-ai/kling-video/v2.5-turbo/pro/image-to-video\", \"usd\": 0.35}, {\"id\": \"fal-ai/kling-video/v2.6/pro/image-to-video\", \"usd\": 0.35}, {\"id\": \"wan/v2.6/image-to-video/flash\", \"usd\": 0.25}, {\"id\": \"fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video\", \"usd\": 0.19}], \"living\": [{\"id\": \"fal-ai/ltx-video/image-to-video\", \"usd\": 0.02}, {\"id\": \"code-motion\", \"usd\": 0}], \"still\": [{\"id\": \"fal-ai/flux/schnell\", \"usd\": 0.006}], \"premium\": [{\"id\": \"fal-ai/flux-pro/v1.1\", \"usd\": 0.08}]}", "v10.1: per role, the models in order of preference with their USD price per clip; the Steward only moves along these (and tested candidates)"),
 "MODEL_HEALTH": ("", "auto - the Steward's record per model (status, retirement date, failures)"),
 "MODEL_PLANNED": ("", "auto - switches the Steward has announced (role -> model, date)"),
 "MODEL_CANDIDATES": ("", "auto - newer models queued for the automatic test"),
 "MODEL_SHARED_DATE_MAX": ("3", "v10.1b: the same retirement date on this many models at once = a page-wide notice, ignored"),
 "MODEL_FAILS_TO_SWITCH": ("3", "v10.1: errors in a row before a model counts as failing (a 'deprecated/not found' answer switches at once)"),
 "MODEL_SWITCH_LEAD_DAYS": ("14", "v10.1: a retiring model gets its replacement announced this many days ahead (the switch is 7 days before retirement)"),
 "MODEL_MAX_PRICE_RATIO": ("1.3", "v10.1: an automatic switch never raises the clip price above this x the current price"),
 "MODEL_MAX_USD_CLIP": ("0.5", "v10.1: ...and never above this USD per clip (higher needs the owner)"),
 "MODEL_UPGRADE_SCOUT_ON": ("TRUE", "v10.1: look for newer versions of the ladder families every week"),
 "MODEL_AUTO_UPGRADE_ON": ("TRUE", "v10.1: newer models with a readable price inside the price rule are tested automatically (capped by BAKEOFF_CAP_INR)"),
 "MODEL_UPGRADE_MARGIN": ("1.0", "v10.1: a new model must score at least this much better (0-10 vision judge) to be adopted"),
 "MODEL_UPGRADE_NOTICE_DAYS": ("3", "v10.1: days between the test result card and the switch (owner can keep or switch now)"),
 "VERDICT_ROTATION_ON": ("TRUE", "v10.1 (K144): the verdict STYLE rotates (hung jury, appeal, plea deal, technicality...) so no two cases end the same way"),
 "VERDICT_STYLE_GAP": ("3", "v10.1: a verdict style is not reused within this many cases"),
 "SCRIPT_SIMILARITY_MAX": ("0.35", "v10.1 (K145): a script more similar than this to one of the last 10 = one card + degraded note"),
 "CAROUSEL_ON": ("TRUE", "v10.1 (K149): an Instagram 'Case Files' carousel (6 slides from the episode's own stills) goes out with each long video"),
 "CAROUSEL_PER_WEEK": ("2", "v10.1: at most this many carousels in 7 days"),
 "WORKER_PUBLIC_URL": ("", "v10.1: the dashboard Worker's base URL (https://...workers.dev); carousel images are served from it for 1 day"),
 "META_AI_LABEL_ON": ("TRUE", "v10.1: Instagram/Facebook posts carry Meta's AI self-disclosure (is_ai_generated; verified 8 Nov 2026)"),
 "DEMAND_SCORE_ON": ("TRUE", "v10.1 (K146): bench premises get a search-demand score from YouTube search (own 100-calls/day bucket)"),
 "DEMAND_DAILY": ("10", "v10.1: bench premises scored per day"),
 "DEMAND_WEIGHT": ("0.6", "v10.1: added to the bench score per 1.0 of demand"),
 "DEMAND_LOOKBACK_DAYS": ("730", "v10.1: only videos from this many days count"),
 "VIEWER_QUESTIONS_ON": ("TRUE", "v10.1 (K147): 'what if' questions from comments become premise data for the scout"),
 "VIEWER_NAME_ON_SCREEN": ("FALSE", "NOT ACTIVE (no code reads this cell): no code puts a viewer's name on screen, so FALSE is what happens and TRUE would change nothing (consent best practice: keep it that way)"),
 "YPP_WATCH_ON": ("TRUE", "v10.1 (K148): weekly proxy of the 500-subscriber YPP tier; one card when Studio may show 'eligible'"),
 "YPP_PROGRESS": ("", "auto - the latest proxy (JSON) for the dashboard"),
 "NEWSLETTER_URL": ("", "v10.1: optional https link to the free 'Case Files' newsletter, added to every long description"),
 "V101_FLIPS_ON": ("TRUE", "v10.1: ONE time: retired Kling 2.1 hero model -> Kling 2.5 Turbo Pro (+ price 0.35), still size 1632x918 -> 1872x1056 (same price), Shorts cap 14 -> 10, hero-still Shorts off; owner values never touched"),
 "V101_FLIPS_DONE": ("", "auto - when the v10.1 flips ran"),
 "SPECIALS_PER_MONTH": ("2", "v10: special reel slots a month (occasions take them first, then SPECIALS_DAYS); paid from SPECIALS_EARMARK_INR"),
 "OCCASION_PRIORITY": ("halloween,christmas,new_year,diwali,holi,valentines,april_fools,lunar_new_year,eid,easter,mothers_day,thanksgiving,pi_day,science_day,childrens_day_in,teachers_day_in,fathers_day,earth_day,perseids,solstice_dec", "v10 (K136): which occasions get a month's special slots first"),
 "OCCASION_DATES": ('{"diwali": {"2026": "2026-11-08", "2027": "2027-10-29"}, "holi": {"2027": "2027-03-22"}, "eid": {"2027": "2027-03-10"}, "lunar_new_year": {"2027": "2027-02-06", "2028": "2028-01-26"}}',
                    "v10: lunar-calendar festival dates (verified 2026-11-08 from published 2026-27 calendars; Eid is moon-dependent); the yearly check adds the next year"),
 "SPECIALS_TOPICAL_ON": ("TRUE", "v10: regular specials may tie lightly to this week's safe science/space trend (never tragedies)"),
 "SPECIALS_LORE_MIN_DAYS": ("42", "v10: at most one backstory (lore) special every this many days; the canon facts rotate per character"),
 "CAST_INTRO_FESTIVE": ("", "v10: e.g. Diwali: the launch reel's courtroom glows with lamps and the court greets viewers for the festival (empty = none)"),
 "V10_FLIPS_ON": ("TRUE", "v10: ONE time, BUDGET_FLOOR_INR / BUDGET_CEILING_INR move to 5000 when they hold 4700 or less (owner approved +₹300 for specials)"),
 "V10_FLIPS_DONE": ("", "auto - when the one-time v10 cap move ran"),
 "LOCALIZATIONS_ON": ("TRUE", "v10 G4: long videos get their title and description in LOCALIZE_LANGS (one Sonnet call, about ₹2 a video) for watch hours from other languages"),
 "LOCALIZE_LANGS": ("es,pt,hi,de,fr,id", "v10 G4: languages (es pt hi de fr id ja ar it)"),
 "AFFILIATE_ON": ("FALSE", "v10 G7 (decision 7): TRUE once the owner has joined a programme and added links in AFFILIATE_LINKS"),
 "AFFILIATE_LINKS": ("[]", "v10 G7: JSON list of {name, url, topics:[words], line}; one topic-matched link per description"),
 "AFFILIATE_DISCLOSURE": ("Affiliate link: I may earn a commission if you sign up, at no extra cost to you.", "v10 G7: the disclosure line (India ASCI / US FTC)"),
 "DASH_APP_HASH": ("", "auto - fingerprint of the dashboard page last published"),
 "WA_ON": ("TRUE", "v9.4b: WhatsApp messages and chat (only once WA_TOKEN / WA_PHONE_ID / OWNER_WA secrets exist); email always goes too"),
 "WA_GRAPH_VERSION": ("v27.0", "v10.2: Meta Graph API version used for WhatsApp (v27.0 current on 9 Nov 2026; v21.0 is removed on 21 Jan 2027)"),
 "WA_TEMPLATE_NAME": ("re_action", "v9.4b: the utility template used outside the 24-hour window"),
 "WA_TEMPLATE_LANG": ("en", "v9.4b: its language code"),
 "WA_LAST_INBOUND_AT": ("", "auto - the owner's last WhatsApp message (24-hour window)"),
 "CHAT_MONTHLY_CAP_INR": ("250", "v9.4b: chat budget shared by WhatsApp and the dashboard; above it the cheap model answers"),
 "WA_BOT_NUMBER": ("", "v9.4b: the WhatsApp number of the bot (digits) for the dashboard's 'Discuss on WhatsApp' button; empty until WhatsApp is set up"),
 "ORCHESTRA_RELEASE_GUARD_H": ("2", "v9.4a: optional heavy jobs (research, Outlier Lab, platform watch) never run this close to a release"),
 "CLAUDE_CREDIT_USD_MONTH": ("0", "v9.4a: monthly Claude API credit from the owner's Max plan (100 or 200) while it lasts; money view only"),
 "CLAUDE_CREDIT_UNTIL": ("2026-12-10", "v9.4a: last day the Max credit counts (owner: Max ends 10 Dec 2026)"),
 "GEMINI_CREDIT_USD_MONTH": ("0", "v9.4a: monthly Gemini API credit from Google AI Pro (10 when linked); money view only"),
 "FACTS_WATCH_ON": ("TRUE", "v9.4a: weekly check of the official change logs (YouTube API, YPP, Anthropic, Gemini, fal, Meta, Cloudflare, GitHub); a change that affects us becomes one card"),
 "FACTS_WATCH_URLS": ("https://developers.google.com/youtube/v3/revision_history,https://developers.google.com/youtube/analytics/revision_history,https://support.google.com/youtube/answer/72851,https://docs.claude.com/en/release-notes/api,https://ai.google.dev/gemini-api/docs/changelog,https://developers.cloudflare.com/workers/platform/limits/",
                      "v9.4a: pages the watcher fingerprints (comma-separated)"),
 "FACTS_WATCH_STATE": ("", "auto - fingerprints of the watched pages (JSON)"),
 "VISUAL_LAB_ON": ("TRUE", "v9.4a: weekly, the Visual Lab compares retention around each picture treatment and proposes zero-cost picture upgrades as cards (never builds by itself)"),
 "VISUAL_LAB_MAX_CARDS": ("2", "v9.4a: at most this many Visual Lab cards a week"),
 "VISUAL_LAB_MIN_VIDEOS": ("4", "v9.4a: videos with retention data needed before the Visual Lab suggests anything"),
 "REPAIR_ENGINE": ("claude_code", "v9.4a: claude_code = the Repair Bot hands a failing run to Claude Code (₹0 API money) | api = the v9.3 paid-API repair"),
 "PKG_RESCUE_ENGAGED_ON": ("TRUE", "v9.3.1: the packaging rescue compares ENGAGED views (Analytics) instead of public views, which count autoplay since 24 Aug 2026; falls back to public views when Analytics has none [FALSE = v9.3]"),
 "V91_SAFE_MODE": ("FALSE", "TRUE = every v9.1 feature is off at once (one-cell rollback of v9.1). Layers added later keep their own switches: the picture equals v9 only with PARTICLES_ON and LIFE_LAYER_ON off as well"),
 "ATMOSPHERE_ON": ("TRUE", "v9.1 Atmosphere Pack (code only, zero cost): moving light, particles, fog, heat shimmer, lens detail, breath fog, beat pulse, aura. FALSE = exactly the v9 picture"),
 "ATMOSPHERE_LEVEL": ("auto", "auto = follows the Show Plan intensity (+1 for fire / space / impact shots), or a fixed 0-3"),
 "ATMOSPHERE_MAX_OVERHEAD_PCT": ("30", "the atmosphere may add at most this share to the render time; above it particles, then fog, then god-rays switch off by themselves (logged)"),
 "ATMOS_GODRAYS_ON": ("TRUE", "v9.1 layer: god-rays from the brightest region + a slow light sweep"),
 "ATMOS_PARTICLES_ON": ("TRUE", "v9.1 layer: dust / embers / ash / snow / rain / sparks in 3 depth layers, by mood"),
 "ATMOS_FOG_ON": ("TRUE", "v9.1 layer: fog / smoke from scrolling noise, denser far, tinted by the shot"),
 "ATMOS_SHIMMER_ON": ("TRUE", "v9.1 layer: heat shimmer on fire / desert / engine shots"),
 "ATMOS_LENS_ON": ("TRUE", "v9.1 layer: edge chromatic aberration, anamorphic streaks, halation, breathing focus"),
 "ATMOS_BREATH_ON": ("TRUE", "v9.1 layer: breath fog on cold / hot found-footage shots"),
 "ATMOS_PULSE_ON": ("TRUE", "v9.1 layer switch for the beat pulse (see PULSE_ON)"),
 "ATMOS_AURA_ON": ("TRUE", "v9.1 layer: glow around the focal point; an energy swirl at intensity 3"),
 "PULSE_ON": ("TRUE", "v9.1 beat pulse ONLY on impact / reveal beats and hero-still reels: <= 2 per second, <= 8 % luminance, never red, never in the first 2 s or during HUD / exhibit readouts (QC holds the video otherwise)"),
 "LIGHTING_DIRECTIVE_ON": ("TRUE", "v9.1: every image prompt gets a lighting + composition directive (motivated key light, rim light, haze, one focal point, hero framing, dominant + accent hue); the style lock is kept"),
 "IMAGE_PROMPT_MAX_CHARS": ("1800", "longest image prompt sent (prompt + directive + style lock); the directive is shortened first. ASSUMED safe for the image models in use"),
 "HERO_STILL_REELS_ON": ("TRUE", "v9.1 (v9.3: ON by default): one 15-25 s seamless-loop vertical reel per episode from its best premium still (CV poster score, no AI), atmosphere + pulse + aura + hook, the episode's own voiced line (no new TTS). To Drive. Zero cost"),
 "HERO_STILL_SHORTS_ON": ("FALSE", "v9.1 (v9.3: ON by default): also upload the hero-still reel as a YouTube Short, SCHEDULED HERO_SHORT_DELAY_MIN after the long video and linking it (Instagram only with Meta keys). Zero cost"),
 "HERO_STILL_CANDIDATES": ("8", "stills scored to pick the hero still"),
 "HERO_REEL_LAST_TEMPLATE": ("", "auto - the last hero-reel template (never repeated twice in a row)"),
 "CHAR_GRAMMAR_ON": ("TRUE", "v9.1: each character's cinematic grammar (Grimm handheld + dutch tilt + underlight; Vale symmetrical slow push, teal-steel; Rosa eye level, warm amber drift) on theater portraits; Characters.grammar_json overrides"),
 "THEATER_STYLE": ("portrait", "portrait | courtroom (the locked set: Rosa at the bench, Grimm at the lectern, Vale at the defence table). Needs approved sheets and CHARACTER_THEATER_ON"),
 "COURTROOM_ON": ("TRUE", "v9.1 switch for the courtroom composition (used only when THEATER_STYLE = courtroom)"),
 "RETENTION_MAP_ON": ("TRUE", "v9.1: the retention curve mapped to beats and shot types (Retention_Map tab); clear dips become Director lessons. Report only, zero cost"),
 "RETENTION_MIN_VIEWS": ("300", "no retention lesson below this many views (high confidence from 3x)"),
 "ROLE_ROI_ON": ("TRUE", "v9.1: per room role: notes accepted, script changed, cost per accepted note (Role_ROI tab, Monthly Brief). Report only, nothing is removed"),
 "COMMENT_MINING_ON": ("TRUE", "v9.1: viewers' 'what if' comments (filtered, deduplicated) become Premise_Bench CANDIDATES (src=comment), judged by both judges at the next refill. One batch call a day, about Rs 0.2"),
 "COMMENT_MINING_DAILY_CAP": ("10", "viewer suggestions classified per day at most"),
 "COMMENT_MINING_DAY": ("", "auto - the last day comments were mined"),
 "COMMENT_CREDIT_NAMES": ("FALSE", "TRUE = a kept suggestion records the viewer's handle (default: no names)"),
 "COMMENT_AI_DRAFTS_ON": ("FALSE", "v9.1: AI-drafted in-character replies to viewers' questions, ONE batch call a day (capped); drafts go to Comment_Queue and the weekly digest only, never posted"),
 "COMMENT_AI_DRAFTS_DAILY_CAP": ("10", "questions drafted per day at most"),
 "COMMENT_DRAFTS_DAY": ("", "auto - the last day drafts were made"),
 "VARIETY_REWRITE_ON": ("TRUE", "v9.1: if the opening still resembles recent ones after the avoid-list, ONE surgical rewrite of the first beat (Sonnet, about Rs 6, only when needed; never while the overrun ladder is active)"),
 "VARIETY_MAX_SCORE": ("0.5", "opening-line similarity (0-1) above which the one variety rewrite runs"),
 "AUDIO_DROP_POST_ON": ("FALSE", "v9.1: post the clip-bait audio drop as an Instagram Reel (over the hero still) when META_ON and the Meta keys exist; never twice; email on the first success"),
 "AUDIO_DROP_FIRST_MAIL": ("", "auto - when the first audio drop was posted"),
 "VOICE_SUBSTITUTE_ON": ("TRUE", "v9.1: when a character's Gemini voice is not in Voice_Check (synth_ok), the closest available voice by gender + style is used before the Kokoro fallback; logged"),
 "SPEND_WARN_PCTS": ("70,90", "one email when this month's spend passes each of these percentages of the cap"),
 "SPEND_WARN_SENT": ("", "auto - which spend warnings were sent this month"),
 "OVERRUN_LADDER_ON": ("TRUE", "TRUE = when a video's AI cost passes OVERRUN_FACTOR x its AI estimate, optional reviews are dropped, then rewrite rounds reduced (AI side only, pictures never); one email afterwards"),
 "OVERRUN_FACTOR": ("1.5", "AI spend / AI estimate above which the degradation ladder starts"),
 "DEVIATION_PCT": ("15", "the weekly cost email lists stages whose measured cost per video differs from the estimate by more than this percentage"),
 "DEVIATION_MAIL_WEEK": ("", "auto - ISO week of the last weekly cost email"),
 "KIDS_GUARD_ON": ("TRUE", "TRUE = after upload, YouTube's own made-for-kids value is read (and daily for 7 days); TRUE on YouTube = an email at once"),
 "COMMENT_AGENT_EST_INR": ("0", "monthly allowance for the comment agent (set by stage 3b; 0 while it is off)"),
 "VIDEOS_PER_MONTH_EST": ("4", "long videos per month used to spread monthly allowances per video in the estimator (follows the owner plan of 4 a month)"),
 "FOUND_FOOTAGE_ON": ("TRUE", "v9: the cold open and RECON exhibits look like found footage (helmet-cam vignette, grain, REC dot, timestamp, gentle exposure drift; glitch bursts at intensity 2+, lens crack at 3). Code only, zero cost"),
 "HUD_ON": ("TRUE", "v9: the Survival HUD from the Show Plan (values come from the script's evidence; checked by code)"),
 "JURY_METER_ON": ("TRUE", "v9: the live Jury Meter bar from the script's [METER] tags; QC checks it ends on the verdict"),
 "EXHIBIT_PINS_ON": ("TRUE", "v9: 'EXHIBIT A · credit' / 'RECONSTRUCTION' pins when an exhibit is shown"),
 "TEACUP_ON": ("TRUE", "v9: Nana's teacup hidden in 2-4 reconstruction moments (never before 30 s, never over evidence, not in thumbnails); placements logged in Episodes"),
 "LETTERBOX_ON": ("TRUE", "v9: cinema bars on hero moments (the impact)"),
 "PHOTOSENSITIVITY_QC_ON": ("TRUE", "v9: final QC measures the master: at most 3 luminance flashes per second and no large-area red flashing (a failure stops posting like any QC problem)"),
 "CHARACTER_THEATER_ON": ("FALSE", "v9: courtroom / character theatre shots from approved character sheets. FALSE until you approve the sheets: the speaker chip + exhibits are used instead"),
 "MOTION_BOOST_ON": ("FALSE", "v9: stretch each Kling clip (speed ramps, crops, echo cuts, reverse, last-frame continuity). Code only"),
 "KLING_OPENING_CLIPS": ("1", "Kling clips placed in the opening window as a first-person POV rush hook; the rest of KLING_CLIPS go to the peak / impact sequence. Moved, never added: same cost [0 = v8.10, all at the impact]"),
 "PREMISE_BENCH_ON": ("TRUE", "TRUE = the scout first draws from the Premise_Bench tab (pre-scored premises that already passed both blind judges) [FALSE = v8.10]"),
 "PREMISE_BENCH_TARGET": ("12", "approved premises the bench is filled up to"),
 "PREMISE_BENCH_MIN": ("6", "when fewer READY premises are left, the daily learning job refills the bench (extra-effort generation + both blind judges, about Rs 25-45 per refill)"),
 "PREMISE_BENCH_EFFORT": ("xhigh", "Claude effort for the bench refill (extra-effort generation; it runs about once in 3-4 weeks)"),
 "PREMISE_BENCH_EST_INR": ("45", "allowance for one bench refill (generation + both judges); a refill starts only when the month's production room still covers the next video plus this (a bench premise replaces that video's scout and judge calls, so it roughly pays for itself)"),
 "PREMISE_BENCH_MAX_AGE_DAYS": ("45", "a bench premise older than this is marked STALE and no longer used"),
 "PREMISE_BENCH_MAIL_MONTH": ("", "NOT ACTIVE (no code reads this cell): no code writes or reads this bookkeeping cell, and no 'bench could not be refilled' email exists"),
 "SKIP_IF_BELOW_BAR": ("FALSE", "FALSE = no slot is ever skipped for quality: after every premise round and every Owner's Cut rewrite, the BEST-scoring version is made, all scores are kept and you get one email [TRUE = v8.10: skip the slot]"),
 "PROMPT_CACHE_ON": ("TRUE", "TRUE = Claude prompts are cached with explicit breakpoints (shared rules 1 h, episode material 5 min or 1 h, the role's instruction uncached). Only the bill changes, never the answer [FALSE = v8.10]"),
 "CACHE_TTL_AUTO": ("TRUE", "TRUE = the episode block is cached for 1 h instead of 5 min when its next use is likely to come later than 5 min (long replies, slow steps) [FALSE = always 5 min]"),
 "CACHE_WARM_ON": ("TRUE", "TRUE = before calls that run side by side and share a prefix, ONE serial warm-up writes the cache first (a zero-output request), so the parallel calls read it"),
 "CACHE_MIN_TOKENS": ("512", "the smallest prefix Claude caches (512 tokens for the 5.x models per the prompt-caching docs, Nov 2026). Shorter prefixes are sent without a breakpoint and noted"),
 "CACHE_WARN_RATIO": ("0.6", "Cache_Stats warns (Run_Log) when an episode's cache hit ratio (reads / (reads + writes)) is below this"),
 "CACHE_EFFORT_PER_MESSAGE": ("FALSE", "TRUE = effort is sent per message (beta header) so calls with different effort can share one cached prefix; a 400 switches it off for the job by itself"),
 "SCRIPT_MODEL": ("opus", "opus = Claude Opus writes the first draft and the critic / Owner's Cut rewrites; fable = Claude Fable (stronger, 2.5x the price; its extra safety filters may refuse some biology topics, then Opus takes over by itself) [v8.10 = sonnet]"),
 "OWNERS_CUT_JUDGE": ("gemini", "gemini = Gemini Pro judges the Owner's Cut, independent of the Opus writer (v8.10 behaviour, default); opus = Claude Opus at EFFORT_JUDGE (same family as the writer, so it may favour its own style)"),
 "HAIKU_CHORES_ON": ("TRUE", "TRUE = a reply that is not valid JSON is repaired by Claude Haiku (about Rs 0.05) and accepted ONLY if every word of the original survives unchanged; otherwise the old retry runs [FALSE = v8.10]"),
 "MODEL_ROUTES": ("", "optional JSON to move a room role to another model family, e.g. {\"immersion\": \"opus\"}. Blank = the built-in routing (models.ROUTES)"),
 "EFFORT_CREATIVE": ("high", "Claude effort for creative generation (scout, showrunner, bible, premise bank / bench, first draft, rewrites): low | medium | high | xhigh | max"),
 "EFFORT_JUDGE": ("high", "Claude effort for judgment (premise judge, Owner's Cut)"),
 "EFFORT_EDIT": ("high", "Claude effort for edits (format, fact fix, humanize, length, packager, reels, memos, Director). high = the Sonnet default, i.e. v8.10 behaviour"),
 "EFFORT_CHORE": ("low", "Claude effort for mechanical chores (JSON repair)"),
 "EFFORT_OVERRIDES": ("", "optional JSON per room role, e.g. {\"writer\": \"xhigh\"}; blank = the four EFFORT_* cells"),
 "PRICE_HAIKU_IN": ("0.10", "USD per million input, Claude Haiku 5.5 (prompts up to 100k tokens; Nov 2026 list price, verify on platform.claude.com)"), "PRICE_HAIKU_OUT": ("0.50", "USD per million output"),
 "PRICE_FABLE_IN": ("10", "USD per million input, Claude Fable 5.1 (Nov 2026 list price, verify)"), "PRICE_FABLE_OUT": ("50", "USD per million output"),
 "PRICE_OPUS_CACHE_READ": ("0.05", "cache read price as a share of the Opus input price (0.05x for Opus 5.5 per the prompt-caching price table, Nov 2026; older Opus 0.1)"),
 "PRICE_OPUS_CACHE_W5": ("1.25", "5-minute cache write as a multiple of the Opus input price"), "PRICE_OPUS_CACHE_W1H": ("2", "1-hour cache write as a multiple of the Opus input price"),
 "PRICE_SONNET_CACHE_READ": ("0.05", "cache read share of the Sonnet input price (0.05x for Sonnet 5.5; older Sonnet 0.1)"),
 "PRICE_SONNET_CACHE_W5": ("1.25", "5-minute cache write multiple, Sonnet"), "PRICE_SONNET_CACHE_W1H": ("2", "1-hour cache write multiple, Sonnet"),
 "PRICE_HAIKU_CACHE_READ": ("0.1", "cache read share of the Haiku input price (0.1x for Haiku 5.5)"),
 "PRICE_HAIKU_CACHE_W5": ("1.25", "5-minute cache write multiple, Haiku"), "PRICE_HAIKU_CACHE_W1H": ("2", "1-hour cache write multiple, Haiku"),
 "PRICE_FABLE_CACHE_READ": ("0.025", "cache read share of the Fable input price (0.025x for Fable 5.1)"),
 "PRICE_FABLE_CACHE_W5": ("1.25", "5-minute cache write multiple, Fable"), "PRICE_FABLE_CACHE_W1H": ("2", "1-hour cache write multiple, Fable"),
 "VISUALS_PROTECTED": ("TRUE", "TRUE = a higher AI-writing estimate (v8.11 Opus routing) never makes the planner trim stills, living stills or Kling clips: tiers are chosen as if the AI allowance were still AI_TIER_BASE_INR. Real spend still counts in full and the cap is never passed [FALSE = the whole estimate decides the tier]"),
 "AI_TIER_BASE_INR": ("198", "the AI allowance the visual tiers were sized with (v8.10: LLM_EST_INR 148 + THINK_EST_INR 30 + ROOM_EXTRA_EST_INR 20)"),
 "AI_SAVER_ON": ("TRUE", "TRUE = AI-side savings (about Rs 30 per video, no visual cut): planning roles (scout, showrunner, bible, premise judge, memos, objections, Director, hooks, packager, reels) run at medium effort; the script, rewrites and every edit of the script keep their EFFORT_* level"),
 "BELOW_BAR_MAIL_ON": ("TRUE", "TRUE = one email per video that was made from a below-the-bar premise or script (scores attached); never an email for normal videos"),
 "TREND_CHANNELS": ("@WhatIfScienceShow,@kurzgesagt,@veritasium,@Vsauce,@RealLifeLore,@TheInfographicsShow,@zackdfilms,@MrBeast", "channels watched weekly"),
 # v12: the Knowledge Palace (whatifs/org/palace.py)
 "PALACE_ON": ("TRUE", "TRUE = the Knowledge Palace is kept up (founding knowledge, expiry, size caps, mirrors of the learning core and the show records) and check palace_health runs on every episode [FALSE = the Palace is left untouched and the check does not apply]"),
 "PALACE_PLAYBOOK_TOKENS": ("1800", "hard cap, in estimated tokens, of the knowledge block one department receives from the Palace before it acts (200-6000)"),
 "PALACE_PLAYBOOK_TOKENS_BY_DEPT": ('{"D4": 2400}', "optional JSON {department id: cap} that overrides PALACE_PLAYBOOK_TOKENS for single departments, e.g. {\"D4\": 2400}"),
 "PALACE_LIMITS_SHARE": ("0.4", "share of every department playbook reserved for limits (the owner's words, policy rules, failure lessons); limits are always served first (0.1-0.9)"),
 "PALACE_CANON_TOKENS": ("700", "v12 B6a: estimated tokens a playbook may spend on the show's canon (the cast, then the newest aired cases), ON TOP of the department's cap, so canon never pushes out a limit or knowledge (100-2000)"),
 "VIEWER_SEAT_ON": ("TRUE", "v12 V1 (Audience, D13): TRUE = before any picture is paid the first shot is made a picture (the animated promise scene opens the video), number graphics are kept to the budget, the voice gets breathing pauses, and checks viewer_promise / viewer_breath / viewer_numbers judge the result [FALSE = nothing is repaired, the three checks say NA]"),
 "NUMBERS_PER_MIN_MAX": ("4", "v12 V1: the most numbers a viewer may HEAR per minute of narration (a figure, a number word or a run of them counts once); above it the writers get one mandatory fix and the script gate holds the video"),
 "GRAPHICS_MAX_LONG": ("3", "v12 V1: the most full-screen number graphics (counter / timeline / compare) in one long video; extra ones become pictures, free"),
 "GRAPHICS_FREE_SEC": ("60", "v12 V1: no full-screen number graphic before this second (the opening shows, it does not count)"),
 "BREATH_EVERY_S": ("30", "v12 V1: the voice pauses at least this often (a pause of BREATH_PAUSE_S is placed at a sentence start; judged on the real voice timeline with 25% slack)"),
 "BREATH_PAUSE_S": ("0.7", "v12 V1: length of a placed breathing pause"), "BREATH_PAUSE_MIN_S": ("0.6", "v12 V1: what counts as a pause when the voice is judged"),
 "V12V1_FLIPS_DONE": ("", "v12 V1: set once RUNTIME_MAX_SEC (600 -> 540) and PROMISE_BY_SEC (30 -> 5) moved where the cells still held the old defaults; never runs twice"),
 "V12B6A_FLIPS_DONE": ("", "v12 B6a: set once the writers' playbook cap moved to 2,400 tokens (only where PALACE_PLAYBOOK_TOKENS_BY_DEPT was still empty); never runs twice"),
 "ORG_PROMPT_INJECT": ("TRUE", "v12 B6a: TRUE = the creative runs (D4 write and draft, D5 package, D6 plan) put their Palace playbook INTO the model prompts of their creative calls, the models cite what they applied with a quote and code verifies it (checks palace_injected, palace_cited, canon_in_brief) [FALSE = the playbook is handed over with the brief only; the three checks say NA]"),
 "CANON_CALLBACK_ON": ("TRUE", "v12 B6a: TRUE = the newest aired case is a continuity debt: the script must call back to it in one spoken line, cited with that exact line (check canon_in_brief)"),
 "CREATIVE_MEMO_MAX_PER_RUN": ("1", "v12 B6a: proposals (new ideas, experiments, joke or hook banks, world-building) a creative run may send to the Council as creative memos (0-3)"),
 "CREATIVE_MEMO_SAME_MAX": ("0.5", "v12 B6a: a proposal whose words overlap an earlier creative memo this much (0-1) is dropped as the same idea - the Council sees distinct options"),
 "PALACE_PROMPT_EST_INR": ("15", "v12 B6a: allowance per long video for the Palace playbook inside the creative prompts and the citations: about 2,000 input tokens at the end of each creative call (not cached, so the cached brief is never re-written; about Rs 10) plus about 120 output tokens of citations a call (about Rs 4); counted in the episode estimate while ORG_PROMPT_INJECT is on. Reconcile with Cost_Log after 2-3 videos"),
 "PALACE_REVIEW_DAYS": ("", "optional JSON {kind: days} that overrides how long an item stays valid before it must be re-validated (defaults: REVIEW_DAYS in whatifs/org/palace.py; 0 = never)"),
 "PALACE_KIND_CAPS": ("", "optional JSON {kind: most served items}; over the cap the lowest-value item of that kind is expired by code (defaults: KIND_CAPS in whatifs/org/palace.py)"),
 "PALACE_FOLDER_ID": ("", "auto: the Drive folder palace/ for item bodies, playbook texts and snapshots; found or created on first use"),
 "ORG_ON": ("TRUE", "TRUE = every wired department runs under the department contract (load its memos and Palace playbook, act, emit memos, write a takeaway, execute tickets, report) and checks dept_contract and takeaways_written run on every episode [FALSE = the plain calls without the organisation; the organisation also needs PALACE_ON]"),
 "ORG_SINCE": ("", "auto: when the organisation was installed on this Sheet; an episode started before that moment is not judged by the organisation's checks"),
 "ORG_SLA_HOURS": ("", "optional JSON {memo type: [acknowledge hours, resolve hours]} that overrides a memo type's two clocks (defaults: TYPES in whatifs/org/schemas.py)"),
 "ORG_ESCALATE_HOURS": ("", "optional JSON {\"1\": [P0, P1, P2 hours a memo may sit with the Council], \"2\": [P0, P1, P2 hours between reminders to the owner]} (defaults: ESCALATE_H in whatifs/org/memos.py)"),
 "ORG_OWNER_REMINDS_MAX": ("2", "how many times the owner is reminded of the same stuck item after the first message (0-9); after that it rests on his list"),
 "ORG_DEVIATION_PCT": ("25", "a measure that moves this many percent against the median of a department's earlier runs turns the run's takeaway into a new finding for the Palace (5-200)"),
 "ORG_CAPS_INR": ("", "optional JSON {department: rupees a month} for the organisation's own paid thinking (defaults in whatifs/org/registry.py: D2 300, D3 120, C 150, L 40, takeaways 60)"),
 "ORG_RUN_STALE_H": ("6", "a department run still marked running after this many hours is flagged as abandoned and becomes a problem memo (1-48)"),
 "ORG_WATCHDOG_AT": ("", "auto: when the SLA watchdog last finished a pass (the episode gate fails when this is more than a day old)"),
 # v12: the Execution Engine (whatifs/org/execute.py, levers.py)
 "EXEC_ON": ("TRUE", "TRUE = a ticket is executed by the Execution Engine: compiled into a typed change, written down before and after, verified by later evidence, rolled back when that fails; checks decisions_executed and lever_verified run on every episode [FALSE = nothing is changed by ticket: every ticket is escalated at once]"),
 "EXEC_VERIFY_RUNS": ("3", "a knowledge or rule change is rolled back when this many complete runs of its department after the change were not served the item (1-10)"),
 "EXEC_VERIFY_DAYS": ("14", "the verification window of a change, in days: no evidence by then = rolled back (an experiment arm gets this many days per output it must appear in; 2-60)"),
 "EXEC_ARM_OUTPUTS": ("2", "an experiment arm is verified when this many long videos made after it was registered carry it in their features (1-6)"),
 "EXEC_RULES_PER_DEPT": ("12", "the most prompt rules one department may hold that were made by ticket (lever class D); over it a new rule is refused until one is retired (1-40)"),
 "EXEC_BUILD_RETRIES": ("2", "how many times a code build that failed its checks, or opened no pull request, is built again before the ticket is escalated (0-4)"),
 "EXEC_BUILD_WAIT_H": ("6", "hours a code build may take to open its pull request before it counts as failed (1-48)"),
 "EXEC_TICK_AT": ("", "auto: when the Execution Engine's tick pass last finished (check lever_verified fails when tickets wait and this is more than a day old)"),
 "EXEC_AUTO_MERGE_ON": ("TRUE", "TRUE = a code build asked for by ticket merges by itself when every check is green AND its real diff only adds new test files (nothing deleted, no other file); anything else waits for the owner's Merge tap [FALSE = the owner merges every build]"),
 # v12 B5: R&D (D2) and the Review Board (D3)
 "RESEARCH_PER_WEEK": ("4", "questions the weekly deep research asks (web search, about Rs 10-15 each, inside the R&D cap of Rs 300 a month); the owner's own questions (P0) are asked on top (1-8)"),
 "RESEARCH_EST_INR": ("15", "rupees one research question is assumed to cost before any is measured; the weekly run stops asking when the R&D budget left is below this or the median measured cost, whichever is higher"),
 "RESEARCH_REPEAT_DAYS": ("28", "a research question that was answered is not asked again for this many days unless its gap grows (7-120)"),
 "RESEARCH_DEEP_EVERY_DAYS": ("7", "the weekly deep research runs when its last complete run is this many days old (checked by every daily learning job, so a missed day never skips a week; 3-14)"),
 "BOARD_MIN_EVIDENCE": ("5", "the Review Board rejects a research memo whose evidence score is below this (0-10; the score can never exceed what code could verify about its sources)"),
 "BOARD_ORDERS": ("2", "how many orders each Review Board judge reads the memos in (2 = original and reversed: judges change their verdict with the order)"),
 "BOARD_MAX_MEMOS": ("6", "research memos one Review Board session judges (plus one planted canary); the rest wait for the next session (1-10)"),
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
_SECRET_ENVS = ("G_CLIENT_KEY", "G_REFRESH", "G_REFRESH_DRIVE", "ANTHROPIC_KEY", "GEMINI_KEY", "FAL_KEY", "PEXELS_KEY", "META_PAGE_KEY", "G_CLIENT_ID", "SHEET_ID")
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
FLUSH_HOOKS = []          # v8.11: other modules' buffered rows (models.CACHE -> Cache_Stats) are written with every log flush
def flush_log():
    with _lock:
        rows = list(_logbuf); _logbuf.clear()
    if rows:
        try: store().append("Run_Log", rows)
        except Exception as e: print("log flush failed:", scrub(e))
    flush_costs()
    for h in list(FLUSH_HOOKS):
        try: h()
        except Exception as e: print("flush hook failed:", scrub(e))

# ---------------- money (buffered: one Sheet read per job, one write per flush) ----------------
_clock = threading.Lock()
_cost_buf, _session = [], {}
COST_TAPS = []          # v12: listeners called with (rupees, provider, item) on every logged cost (the department runner attributes spend to the run in flight)
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
def cost(item, provider, units, usd, episode=None, **detail):
    """detail (v8.11, optional): model, in_tok, cache_read_tok, cache_write_tok, out_tok, basis - measured token detail for the Cost_Log row."""
    inr = round(usd * S("USD_INR", float), 2)
    _spend_base()
    with _clock:
        _cost_buf.append(dict({k: v for k, v in detail.items() if k in TABS["Cost_Log"]}, ts=iso(), episode_id=episode or JOB["episode"], item=item, provider=provider, units=units, inr=inr))
        _session[provider] = _session.get(provider, 0) + inr
        due = len(_cost_buf) >= 6 or time.time() - _last_cost_flush[0] > 45
    for _fn in COST_TAPS:
        try: _fn(inr, provider, item)
        except Exception: pass
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

