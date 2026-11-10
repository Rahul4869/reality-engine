"""v11 Stage D (K160): the Case Files countdown - real assembly from archived masters, every gate enforced. No keys, no network."""
import json, os, subprocess
import pytest
from whatifs import core, spinoff as SPO, publish as PUB, manage as MG

def _masters(tmp, n):
    st = core.store(); ids = []
    for i in range(n):
        p = str(tmp / f"master{i}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration=40", "-f", "lavfi", "-i", "sine=frequency=440:duration=40",
                        "-shortest", "-pix_fmt", "yuv420p", "-c:a", "aac", p], check=True, timeout=120)
        st.append("Episodes", [{"episode_id": f"E{i}", "yt_id": f"y{i}", "title": f"Case {i}", "premise": f"What if {i}?", "assets": json.dumps({"_master.mp4": f"drv{i}"}),
                                "verdict_style": ["guilty", "acquitted", "mistrial", "guilty", "appeal"][i % 5]}])
        st.append("Analytics", [{"yt_id": f"y{i}", "views": 100 * (i + 1), "engaged_views": 50}])
        ids.append(p)
    return ids

def test_a_countdown_is_built_with_new_material_and_chapters(monkeypatch, tmp_path, setting):
    paths = _masters(tmp_path, 5)
    monkeypatch.setattr(PUB, "drive_download", lambda fid, dst: __import__("shutil").copy(paths[int(fid[3:])], dst) or dst)
    setting("CASEFILES_SEG_SEC", "12")
    r = SPO.run(force=True)
    assert r["ok"] and r["new_share"] >= 0.35 and r["status"] == "POSTED", r
    assert os.path.exists(r["path"]) and r["minutes"] > 0.5
    assert core.store().rows("Specials")[-1]["kind"] == "casefiles"

def test_gates_stop_repetition_and_loop_less_bridges():
    cases = [{"verdict_style": "guilty"}, {"verdict_style": "guilty"}, {"ending": "Grimm's device fails"}]
    assert any("share the verdict style" for p in SPO._gate_variety(cases) for _ in [0]) and SPO._gate_variety(cases)
    assert SPO._gate_variety([{"ending": "grimm fails"}, {"ending": "grimm fails"}, {"ending": "win"}])        # 67% Grimm fails > 40%
    assert "a bridge opens no loop (no forward reference)" in SPO._gate_narrative({"theme": "a long enough theme here", "bridges": ["Case one.", "Last."]})
    assert SPO._gate_narrative({"theme": "every time physics broke", "bridges": ["and still to come, the big one", "Number one."]}) == []

def test_not_enough_archived_episodes_is_said_plainly():
    r = SPO.run(force=True)
    assert not r["ok"] and "archived episodes" in r["why"]

def test_archive_keeps_enough_masters_for_a_countdown(setting):
    assert int(core.DEFAULTS["DRIVE_ARCHIVE_KEEP"][0]) >= int(core.DEFAULTS["CASEFILES_CASES"][0]) * 2
    st = core.store(); st.append("Settings", [{"key": "DRIVE_ARCHIVE_KEEP", "value": "2", "note": ""}]); core._settings_cache = None
    setting("V11_FLIPS_DONE", "")
    assert "DRIVE_ARCHIVE_KEEP" in MG.v11_upgrade(st)

def test_archive_cell_is_read_in_every_form():
    assert SPO._assets({"_master.mp4": "a"}) == {"_master.mp4": "a"} and SPO._assets('{"_master.mp4": "b"}')["_master.mp4"] == "b"
    assert SPO._assets("{'_master.mp4': 'c'}")["_master.mp4"] == "c" and SPO._assets("") == {} and SPO._assets("garbage") == {}

