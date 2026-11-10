"""v11 (K162): impressions + thumbnail CTR from the Reporting API reach report. No keys, no network."""
import pytest
from whatifs import core, reach as RCH

def test_job_once_rows_by_header_deleted_videos_skipped_and_redelivery_overwrites(setting):
    assert RCH.daily() == 1                                               # the fake file has 1 real video + 1 deleted (empty id)
    assert core.S("REACH_JOB_ID") == "fakejob" and core.S("REACH_LAST_CREATED")
    rows = core.store().rows("Reach")
    assert len(rows) == 1 and rows[0]["video_id"] == "fakeA" and rows[0]["date"] == "2026-11-10" and int(rows[0]["impressions"]) == 1200
    setting("REACH_LAST_CREATED", "")                                    # the same day delivered again (backfill) -> overwritten, not duplicated
    RCH.daily(); assert len(core.store().rows("Reach")) == 1
    assert RCH.ctr("fakeA") == pytest.approx(0.054) and RCH.ctr("nope") is None

def test_parse_reads_columns_by_name_and_normalises_percent():
    txt = "video_thumbnail_impressions_ctr,video_id,date,video_thumbnail_impressions\n5.2,vid1,20261101,100\n0.03,vid2,20261101,50\n"
    got = {r["video_id"]: r for r in RCH.parse(txt)}
    assert got["vid1"]["ctr"] == pytest.approx(0.052) and got["vid2"]["ctr"] == pytest.approx(0.03) and got["vid1"]["date"] == "2026-11-01"
