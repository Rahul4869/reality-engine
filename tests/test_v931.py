"""v9.3.1 "Launch": the ₹0 upload check (L1), the lock detector + AI-label read-back (L2), the lock hold (L3), the uploads-open gates (L9),
the hero-still Short rules (L10) and the no-re-consent scopes (L11). No keys, no network."""
import pytest
from whatifs import core, launch as LA, publish as PUB, manage as MG

def _paid_rows(): return len(core.store().rows("Cost_Log"))

def test_upload_check_pass_opens_uploads_and_is_idempotent(monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda *a, **k: mails.append(a))
    LA._FAKE_RESULT[0] = "unlisted"; before = _paid_rows()
    assert LA.lock_state() == "unknown" and not LA.uploads_open()
    assert LA.upload_check() == "passed"
    assert LA.lock_state() == "off" and LA.uploads_open() and core.S("API_AUDIT_STATUS") == "approved"
    rows = [r for r in core.store().rows("Setup_Status") if "upload_check" in str(r)]
    assert rows and "passed" in str(rows[-1])
    assert "already passed" in LA.upload_check() and _paid_rows() == before and not mails

def test_upload_check_lock_holds_production_and_mails_once(monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda *a, **k: mails.append(a))
    LA._FAKE_RESULT[0] = "private"
    try:
        assert LA.upload_check() == "locked" and LA.lock_state() == "on" and not LA.uploads_open()
        LA.lock_detected("vid2", ["again"])
        assert len(mails) == 1                                                  # at most one urgent email a day
        MG._AUDIT_TEST[0] = True
        ok, why = MG.audit_gate([])
        assert not ok and "UPLOAD_LOCK" in why
    finally:
        LA._FAKE_RESULT[0] = "unlisted"; MG._AUDIT_TEST[0] = False

def test_gate_unknown_allows_one_then_waits_open_allows_all(setting):
    MG._AUDIT_TEST[0] = True
    try:
        assert MG.audit_gate([])[0] and not MG.audit_gate([{"yt_id": "x"}])[0]          # unknown: the old one-video allowance
        setting("UPLOAD_LOCK", "off")
        assert MG.audit_gate([{"yt_id": "x"}, {"yt_id": "y"}])[0]
    finally: MG._AUDIT_TEST[0] = False

def test_due_check_waits_six_hours(setting):
    assert LA.due_check()
    setting("UPLOAD_CHECK_AT", core.iso()); assert not LA.due_check()
    setting("UPLOAD_LOCK", "off"); setting("UPLOAD_CHECK_AT", ""); assert not LA.due_check()

def test_read_back_detects_lock_and_fixes_a_dropped_label(monkeypatch):
    monkeypatch.setattr(PUB, "FAKE", False); calls = {"label": 0, "lock": []}
    monkeypatch.setattr(PUB, "yt_set_label", lambda vid, on=True: calls.__setitem__("label", calls["label"] + 1) or True)
    monkeypatch.setattr(LA, "lock_detected", lambda vid, issues: calls["lock"].append(issues))
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: {"privacyStatus": "private", "containsSyntheticMedia": False})      # v10.1: only an explicit False is re-set
    found = PUB.verify_upload("v1", "public", None, True)
    assert calls["lock"] and calls["label"] == 1 and any("AI label fixed" in f for f in found)
    calls["lock"].clear()
    monkeypatch.setattr(PUB, "yt_status_full", lambda vid: {"privacyStatus": "private", "publishAt": "2026-11-14T15:00:00Z", "containsSyntheticMedia": True})
    assert PUB.verify_upload("v2", "private", "2026-11-14T15:00:00Z", True) == [] and not calls["lock"]

def test_read_back_switch_and_never_raises(monkeypatch, setting):
    monkeypatch.setattr(PUB, "FAKE", False)
    setting("UPLOAD_VERIFY_ON", "FALSE"); assert PUB.verify_upload("v", "public") == []

def test_produce_stops_before_any_spend_when_locked(setting):
    from whatifs import episode as EP
    setting("UPLOAD_LOCK", "on"); before = _paid_rows()
    r = EP.produce("2026-11-14T15:00:00Z")
    assert r.get("skipped") == "upload_lock" and _paid_rows() == before

def test_scopes_cover_future_features_without_reconsent():
    from tools import google_signin as GS
    for s in ("https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"):
        assert s in core.GOOGLE_SCOPES and s in GS.SC
    assert GS.SC_DRIVE == ["https://www.googleapis.com/auth/drive.file"]       # Drive stays on its own key (v8.9.2)

def test_hero_still_length_settings():
    assert core.DEFAULTS["HERO_STILL_MAX_SEC"][0] == "10" and core.DEFAULTS["HERO_STILL_MIN_SEC"][0] == "6"
    for k in ("UPLOAD_LOCK", "UPLOAD_VERIFY_ON", "UPLOAD_CHECK_AT", "UPLOAD_LOCK_ALERT_AT"):
        assert core.DEFAULTS[k][1].strip()

# ---------------- L4 pick fixes, L6 sheets default lock, L7 merge token, one-time flips
import datetime as dt, json
from whatifs import packaging as PK, sheets as SH

def _ep_with_variants(slot_in_h):
    st = core.store(); ep = "EP20261114"
    slot = (core.now_utc() + dt.timedelta(hours=slot_in_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    st.append("Episodes", [{"episode_id": ep, "yt_id": "vid14", "slot_et": slot, "status": "SCHEDULED"}])
    st.append("Packaging_Tests", [{"episode_id": ep, "yt_id": "vid14", "variant": k, "title": t, "thumb_text": "UP", "status": "LIVE" if k == "A" else "READY",
                                   "picked_by": "", "created": (core.now_utc() - dt.timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")}
                                  for k, t in (("A", "Your Pillow Is Rising"), ("B", "Gravity Just Quit Your Bedroom"), ("C", "Why Your Bed Floats at Noon"))])
    return ep

def test_pick_counts_until_two_hours_before_release_and_teaches_taste(monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: mails.append(subj))
    monkeypatch.setattr(PK, "_switch", lambda row: True)
    ep = _ep_with_variants(10)                                   # created 20 h ago: the old 6-hour rule would have refused this pick
    assert PK.apply_pick(f"PICK {ep} B").endswith("variant B applied")
    assert any("applied: B" in m for m in mails)
    assert "Gravity Just Quit Your Bedroom" in PK.taste_brief() and "Your Pillow Is Rising" in PK.taste_brief()

def test_pick_after_the_deadline_is_refused_with_a_reply(monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: mails.append(subj))
    ep = _ep_with_variants(1)                                    # release in 1 h: inside the 2-hour freeze
    assert "too late" in PK.apply_pick(f"PICK {ep} C") and any("too late" in m for m in mails)

def test_pick_messages_for_every_video_and_owner_respecting_flip(setting):
    assert core.DEFAULTS["THUMB_APPROVAL_FIRST_N"][0] == "9999"
    st = core.store(); st.append("Settings", [{"key": "THUMB_APPROVAL_FIRST_N", "value": "8", "note": ""}]); core._settings_cache = None
    assert MG.v931_upgrade(st) == ["THUMB_APPROVAL_FIRST_N"] and core.S("THUMB_APPROVAL_FIRST_N", int) == 9999
    setting("THUMB_APPROVAL_FIRST_N", "8"); assert MG.v931_upgrade(st) == []          # never twice

def test_unanswered_sheets_lock_by_default_and_switch_theater_on(monkeypatch):
    mails = []; monkeypatch.setattr(PUB, "email", lambda subj, *a, **k: mails.append(subj))
    st = core.store(); old = (core.now_utc() - dt.timedelta(hours=80)).strftime("%Y-%m-%dT%H:%M:%SZ"); new = core.iso()
    st.append("Character_Sheets", [{"ts": old, "character": "VALE", "expression": "neutral", "hash": "h1", "file": "drive:1", "status": "DRAFT"},
                                   {"ts": old, "character": "GRIMM", "expression": "neutral", "hash": "h2", "file": "drive:2", "status": "DRAFT"},
                                   {"ts": new, "character": "GRIMM", "expression": "smug", "hash": "h3", "file": "drive:3", "status": "DRAFT"}])
    assert SH.auto_lock() == 2
    rows = {r["hash"]: r["status"] for r in st.rows("Character_Sheets")}
    assert rows == {"h1": "LOCKED", "h2": "LOCKED", "h3": "DRAFT"} and core.S("CHARACTER_THEATER_ON", bool) and mails
    assert SH.auto_lock() == 0                                   # nothing more to lock; no second email

def test_sheets_default_lock_can_be_switched_off(setting):
    setting("SHEETS_DEFAULT_LOCK_H", "0"); assert SH.auto_lock() == 0

def test_merge_uses_the_merge_token_when_present():
    import yaml
    wf = yaml.safe_load(open(".github/workflows/merge.yml"))
    job = wf["jobs"]["merge"]
    assert job["env"]["GH_MERGE_TOKEN"] == "${{ secrets.GH_MERGE_TOKEN }}"
    assert 'export GH_TOKEN="$GH_MERGE_TOKEN"' in job["steps"][0]["run"]

def test_packager_brief_carries_owner_taste(setting):
    from whatifs import room as RM
    setting("TASTE_TITLES", json.dumps([{"chose": "Gravity Just Quit", "over": "Your Pillow Rises"}]))
    assert "Gravity Just Quit" in RM._owner_taste()
    setting("TASTE_TITLES", "not json"); assert RM._owner_taste() == ""

# ---------------- L5 rotation off (decision 5), engaged-view rescue at 72 h, native test link
def test_rotation_is_off_by_default_and_flipped_once_on_live_sheets(setting):
    assert core.DEFAULTS["PKG_ROTATE_ON"][0] == "FALSE" and core.DEFAULTS["PKG_RESCUE_HOURS"][0] == "72"
    st = core.store(); st.append("Settings", [{"key": "PKG_ROTATE_ON", "value": "TRUE", "note": ""}, {"key": "PKG_RESCUE_HOURS", "value": "48", "note": ""}])
    core._settings_cache = None
    assert MG.v931_upgrade(st) == ["PKG_ROTATE_ON"]                       # 48 is the owner's own value: untouched
    assert not core.S("PKG_ROTATE_ON", bool) and core.S("PKG_RESCUE_HOURS", int) == 48
    assert PK.rotate_tick() == 0

def test_rescue_prefers_engaged_views_and_compares_like_with_like(monkeypatch):
    calls = []
    monkeypatch.setattr(PUB, "yt_engaged_views", lambda vid, since: calls.append(vid) or 500)
    monkeypatch.setattr(PUB, "yt_views", lambda vid: 99999)
    v, src = MG._rescue_views("vidE", core.now_utc())
    assert (v, src) == (500, "engaged") and calls == ["vidE"]
    monkeypatch.setattr(PUB, "yt_engaged_views", lambda vid, since: None)
    assert MG._rescue_views("vidE", core.now_utc()) == (99999, "views")          # Analytics has nothing yet: public count
    assert MG._rescue_views("vidE", core.now_utc(), "engaged") == (None, "engaged")  # a swap measured on engaged views is never judged on public views

def test_native_test_link_makes_the_rescue_stand_aside():
    st = core.store(); st.append("Episodes", [{"episode_id": "EP20261121", "yt_id": "vidN", "slot_et": core.iso(), "status": "LIVE"}])
    assert PK.native_test("EP20261121") == "https://studio.youtube.com/video/vidN/edit"
    e = next(r for r in st.rows("Episodes") if r["episode_id"] == "EP20261121")
    assert "native test" in str(e.get("pkg_check"))
    assert PK.native_test("EP_missing") == ""
