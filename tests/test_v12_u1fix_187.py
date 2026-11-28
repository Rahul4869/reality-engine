"""U1 fix 187 (open issue 210): THE STORED CLIPS FOLLOW VIEW_FLOOR_WATCH_S. A stored clip (the canary's, a reference's) longer than the cell is cut to
the cell's seconds by stream copy (no encode: one encode an item) after the SHA check; one not longer is used as it is. Above the kit's own length nothing
can be added: the new film is watched for the kit's length and one floor_kit row a day says so. The kit is never filed again by code."""
import glob, json, os, subprocess
import pytest
from whatifs import core, publish as PUB, release as REL, notify as NT
from whatifs.core import S
from whatifs.org import floor as FL

DAY = "2099-03-04T10:00:00Z"                     # the floor's clock in these tests (no wall clock: a run across midnight would be two days)


@pytest.fixture
def floor187(setting, monkeypatch):
    setting("VIEW_FLOOR_ON", "TRUE")
    monkeypatch.setattr(FL, "iso", lambda t=None: DAY)
    yield setting


def _src(tmp_path, seconds, name="src.mp4"):
    """A deterministic film with sound (no randomness): ffmpeg's test pattern and a tone."""
    p = str(tmp_path / name)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=12", "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
                    "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", p], check=True, capture_output=True)
    return p


def _file_kit(tmp_path, setting, stored_s=8):
    """The canary's kit filed offline with a stored clip of `stored_s` seconds (make_kit files watch_s of the file it is given)."""
    setting("VIEW_FLOOR_WATCH_S", str(stored_s)); sha = FL.make_kit(_src(tmp_path, 10, "canary_film.mp4"))
    assert round(FL.seconds_of(os.path.join(core.WORK, "floor_kit", "canary.mp4"))) == stored_s
    return sha


def _cuts(d): return glob.glob(os.path.join(str(d), "**", "*_cut*.mp4"), recursive=True)


def test_a_stored_canary_longer_than_the_cell_is_cut_to_it_by_stream_copy_after_its_sha(floor187, monkeypatch, tmp_path):
    sha = _file_kit(tmp_path, floor187); floor187("VIEW_FLOOR_WATCH_S", "4"); monkeypatch.setattr(FL, "FAKE", False)
    enc = []; real = FL._ff
    monkeypatch.setattr(FL, "_ff", lambda a: (enc.append(a) if "libx264" in a and "-loop" not in a else None, real(a))[1])
    c, z = FL.kit(str(tmp_path / "k1"))
    assert abs(FL.seconds_of(c["clip"]) - 4) <= 0.2 and c["s"] == 4.0 and len(c["frames"]) == 4 // FL.EVERY_S, (FL.seconds_of(c["clip"]), c)
    assert c["clip"] in _cuts(tmp_path / "k1") and z["s"] == 4.0 and len(z["frames"]) == 2
    assert enc == [], enc                                                                                   # the cut is a stream copy: no new encode of the canary
    assert REL.sha(os.path.join(str(tmp_path / "k1"), "floor", "canary_src.mp4")) == sha                   # the stored file itself is untouched
    k = json.loads(S("VIEW_FLOOR_CANARY")); core.set_setting("VIEW_FLOOR_CANARY", json.dumps(dict(k, sha="0" * 64)))
    assert FL.kit(str(tmp_path / "k2")) == (None, "the canary file is not the one on record") and _cuts(tmp_path / "k2") == []      # refused BEFORE any cut


def test_a_stored_clip_not_longer_than_the_cell_is_used_as_it_is(floor187, monkeypatch, tmp_path):
    _file_kit(tmp_path, floor187); monkeypatch.setattr(FL, "FAKE", False)
    c, _z = FL.kit(str(tmp_path / "k8"))
    assert c["clip"] == os.path.join(str(tmp_path / "k8"), "floor", "canary_src.mp4") and c["s"] == 8.0 and len(c["frames"]) == 4 and _cuts(tmp_path / "k8") == []


def test_a_reference_through_fetched_is_cut_to_the_cell_likewise(floor187, tmp_path):
    floor187("VIEW_FLOOR_WATCH_S", "8"); v = FL.view(_src(tmp_path, 10, "ref_film.mp4"), str(tmp_path / "refview"), 8.0)
    rid = PUB.drive_upload(v["clip"], "ref187.mp4", public=False)[0]
    floor187("VIEW_FLOOR_WATCH_S", "4"); r = FL._fetched(rid, str(tmp_path / "ref1"))
    assert abs(FL.seconds_of(r["clip"]) - 4) <= 0.2 and r["s"] == 4.0 and len(r["frames"]) == 2 and r["clip"] in _cuts(tmp_path), r
    floor187("VIEW_FLOOR_WATCH_S", "8"); r = FL._fetched(rid, str(tmp_path / "ref2"))
    assert r["clip"] == str(tmp_path / "ref2") + "_src.mp4" and r["s"] == 8.0


def test_above_the_kit_the_new_film_is_watched_for_the_kits_length_and_he_is_told_once_a_day(floor187, monkeypatch, tmp_path):
    _file_kit(tmp_path, floor187); floor187("VIEW_FLOOR_WATCH_S", "12"); monkeypatch.setattr(FL, "FAKE", False)
    seen = []; real = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, seconds: (seen.append((os.path.basename(base), float(seconds))), real(src, base, seconds))[1])
    film = _src(tmp_path, 14, "new_film.mp4")
    FL.run(None, "EP187A", film, str(tmp_path / "a"), (), ())
    assert seen == [("new", 8.0)], seen                                                                     # both sides of the comparison are 8 s
    assert abs(FL.seconds_of(os.path.join(str(tmp_path / "a"), "floor", "new.mp4")) - 8) <= 0.2
    rows = lambda: [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"]
    assert [r["text"] for r in rows()] == ["The floor's kit holds 8 s and VIEW_FLOOR_WATCH_S is 12: the new film is watched for 8 s until the kit is filed again."], rows()
    FL.run(None, "EP187B", film, str(tmp_path / "b"), (), ())
    assert len(rows()) == 1 and seen[-1] == ("new", 8.0), rows()                                            # a second session the same day: no second row
    assert json.loads(S("VIEW_FLOOR_CANARY"))["sha"] and round(FL.seconds_of(os.path.join(core.WORK, "floor_kit", "canary.mp4"))) == 8      # the kit is not filed again by code


def test_at_or_below_the_kit_the_new_film_is_watched_for_the_cell_and_nothing_is_said(floor187, monkeypatch, tmp_path):
    _file_kit(tmp_path, floor187); monkeypatch.setattr(FL, "FAKE", False)
    seen = []; real = FL.view
    monkeypatch.setattr(FL, "view", lambda src, base, seconds: (seen.append(float(seconds)), real(src, base, seconds))[1])
    FL.run(None, "EP187C", _src(tmp_path, 14, "new_film.mp4"), str(tmp_path / "c"), (), ())
    assert seen == [8.0] and not [r for r in core.store().rows("Owner_Actions") if r.get("kind") == "floor_kit"], seen


def test_the_cells_note_says_what_happens_to_a_stored_clip():
    assert core.DEFAULTS["VIEW_FLOOR_WATCH_S"][1].endswith("A stored clip longer than this is cut to it when shown (no new encode); above the kit's own length the new "
                                                           "film is watched for the kit's length - file the kit again to watch more.")
    assert "keep the length they were filed with" not in core.DEFAULTS["VIEW_FLOOR_WATCH_S"][1] and NT.klass("floor_kit") == NT.INFORM
