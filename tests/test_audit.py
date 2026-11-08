"""v8.4: the YouTube API audit is tracked (Setup_Status row), reminded (weekly email once a video exists), and gated (only the film-for-the-form video before approval)."""
from whatifs import core, manage as M, publish as PUB

def _eps(n): return [{"episode_id": f"E{i}", "yt_id": f"V{i}", "status": "SCHEDULED"} for i in range(n)]

def test_default_state_is_not_sent_and_setup_writes_a_row(setting):
    assert M.audit_state() == "not_sent"
    M.setup()                                    # v9.3.1: not needed unless the upload check found a lock
    row = next(r for r in core.store().rows("Setup_Status") if r["step"] == "youtube_api_audit")
    assert row["status"] == "✅" and "not needed" in row["detail"]
    setting("UPLOAD_LOCK", "on"); M.setup()
    row = next(r for r in core.store().rows("Setup_Status") if r["step"] == "youtube_api_audit")
    assert row["status"] == "❌" and "upload check" in row["detail"]

def test_row_turns_green_when_approved(setting):
    setting("API_AUDIT_STATUS", "approved"); M.setup()
    assert next(r for r in core.store().rows("Setup_Status") if r["step"] == "youtube_api_audit")["status"] == "✅"

def test_odd_spellings_of_the_setting_are_understood(setting):
    setting("API_AUDIT_STATUS", " Sent "); assert M.audit_state() == "sent"
    setting("API_AUDIT_STATUS", "nonsense"); assert M.audit_state() == "not_sent"

def test_gate_lets_one_video_through_then_waits(setting, monkeypatch):
    monkeypatch.setattr(M, "_AUDIT_TEST", [True])
    assert M.audit_gate([])[0] and not M.audit_gate(_eps(1))[0]
    setting("AUDIT_PRE_APPROVAL_EPISODES", "99"); assert M.audit_gate(_eps(5))[0]

def test_gate_opens_when_approved_and_is_off_in_fake_mode_by_default(setting, monkeypatch):
    assert M.audit_gate(_eps(5))[0]                                        # fake mode: rehearsal may make many videos
    monkeypatch.setattr(M, "_AUDIT_TEST", [True]); assert not M.audit_gate(_eps(5))[0]
    setting("API_AUDIT_STATUS", "approved"); assert M.audit_gate(_eps(5))[0]

def test_a_public_video_proves_approval(setting):
    M.audit_seen_public()
    assert M.audit_state() == "approved" and core.S("API_AUDIT_STATUS") == "approved"

def _spy(monkeypatch):
    sent = []; monkeypatch.setattr(PUB, "email", lambda subject, html, kind="essential": sent.append(subject) or True); return sent

def test_no_reminder_before_any_video_exists_or_once_approved(setting, monkeypatch):
    sent = _spy(monkeypatch); M.audit_nudge([]); assert sent == []
    setting("API_AUDIT_STATUS", "approved"); M.audit_nudge(_eps(2)); assert sent == []

def test_reminder_once_a_week_with_text_for_each_state(setting, monkeypatch):
    setting("UPLOAD_LOCK", "on")          # v9.3.1: the audit reminders only run when the upload check found a lock
    sent = _spy(monkeypatch)
    M.audit_nudge(_eps(1)); M.audit_nudge(_eps(1))
    assert sent == ["Reminder: send the YouTube API audit form"]          # the second call, minutes later, stays silent
    setting("API_AUDIT_STATUS", "sent"); setting("AUDIT_NUDGE_AT", "2020-01-01T00:00:00Z"); M.audit_nudge(_eps(1))
    assert sent[-1] == "Waiting for the YouTube API audit"

def test_production_waits_at_the_gate_and_resumes_when_approved(setting, monkeypatch):
    monkeypatch.setattr(M, "_AUDIT_TEST", [True]); setting("PRODUCE_AHEAD_HOURS", "200")      # a slot is always inside the window, whatever day the test runs
    eps = _eps(1); assert M._produce_slot(eps) is None
    setting("API_AUDIT_STATUS", "approved"); assert M._produce_slot(eps) is not None
