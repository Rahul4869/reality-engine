"""v8.9.1: fixes for the defects confirmed in the external v8.9 review. No keys, no network (every remote call is replaced by a stub)."""
import os, re, json, subprocess, datetime as dt
import numpy as np
import pytest
from whatifs import core, media as M, episode as EP, room as ROOM, manage as MG, publish as PUB, render as RN, hooks as HOOKS, growth as GR, cta as CTA
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _jpg(path):
    from PIL import Image
    Image.fromarray((np.random.default_rng(1).random((40, 60, 3)) * 255).astype(np.uint8)).save(path); return path

# ---------------- Flaw 1: production never animates the offline test clip; restored pictures are never bought again for a URL
def test_animate_without_url_sends_the_real_picture_never_the_test_clip(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "FAKE", False); sent = {}
    monkeypatch.setattr(M, "fal_allowed", lambda: True, raising=False)
    import whatifs.governor as G; monkeypatch.setattr(G, "fal_allowed", lambda: True)
    monkeypatch.setattr(M, "fal_run", lambda model, args, timeout=0: (sent.update(args), {"video": {"url": "https://x/v.mp4"}})[1])
    monkeypatch.setattr(M, "_dl", lambda url, path: open(path, "wb").write(b"mp4"))
    monkeypatch.setattr(M, "fake_clip", lambda *a, **k: pytest.fail("the offline test clip must never be used in production"))
    img = _jpg(str(tmp_path / "img.jpg"))
    out = M.animate(None, img, "fog", str(tmp_path / "c.mp4"), "EP", hero=True)
    assert out.endswith("c.mp4") and (sent.get("image_url") or sent.get("start_image_url")).startswith("data:image/jpeg;base64,")
    with pytest.raises(RuntimeError, match="no picture to animate"):
        M.animate("", str(tmp_path / "missing.jpg"), "fog", str(tmp_path / "d.mp4"), "EP")

def test_animate_keeps_a_known_url(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "FAKE", False); sent = {}
    import whatifs.governor as G; monkeypatch.setattr(G, "fal_allowed", lambda: True)
    monkeypatch.setattr(M, "fal_run", lambda model, args, timeout=0: (sent.update(args), {"video": {"url": "https://x/v.mp4"}})[1])
    monkeypatch.setattr(M, "_dl", lambda url, path: open(path, "wb").write(b"mp4"))
    M.animate("https://fal/img.jpg", _jpg(str(tmp_path / "i.jpg")), "p", str(tmp_path / "c.mp4"), "EP")
    assert sent["image_url"] == "https://fal/img.jpg"

def test_checkpoint_keeps_picture_urls(tmp_path):
    files = {"img": {3: str(tmp_path / "img003.jpg")}, "clips": {}, "anchors": [3], "urls": {3: "https://fal/3.jpg", 4: None}}
    st = EP._assets_state(files); assert st["urls"] == {"3": "https://fal/3.jpg"}
    _jpg(files["img"][3]); json.dump(st, open(tmp_path / "assets.json", "w"))
    back = EP._load_assets(str(tmp_path)); assert back["urls"] == {3: "https://fal/3.jpg"} and 3 in back["img"]

def test_resumed_picture_without_url_is_not_bought_again(tmp_path, monkeypatch):
    units = [{"i": i, "text": f"line {i}", "tag": "none", "start": i * 5.0} for i in range(3)]
    shots = [{"type": "kling", "prompt": "a"}, {"type": "still", "prompt": "b"}, {"type": "still", "prompt": "c"}]
    have = {"img": {0: _jpg(str(tmp_path / "img000.jpg")), 1: _jpg(str(tmp_path / "img001.jpg")), 2: _jpg(str(tmp_path / "img002.jpg"))}, "clips": {}, "urls": {}}
    bought, animated = [], []
    monkeypatch.setattr(EP.M, "still", lambda *a, **k: (bought.append(a), pytest.fail("a restored picture was bought again"))[1])
    monkeypatch.setattr(EP.M, "animate", lambda url, path, *a, **k: (animated.append((url, path)), str(tmp_path / "clip000.mp4"))[1])
    files = EP._assets(shots, units, str(tmp_path), "EPR", budget=3, have=have)
    assert not bought and animated and animated[0][1].endswith("img000.jpg") and 0 in files["clips"]

# ---------------- Flaw 2: the Repair Bot no longer mistakes traceback line numbers for HTTP errors
def _classifier():
    y = open(os.path.join(ROOT, ".github", "workflows", "repair.yml")).read()
    return re.search(r'grep -qiE "([^"]+)" last_error\.txt', y).group(1).replace("\\\\", "\\")

@pytest.mark.parametrize("text,skip", [('File "whatifs/episode.py", line 500, in produce\nKeyError: \'x\'', False),
                                       ('File "whatifs/manage.py", line 429, in learn\nTypeError: bad', False),
                                       ("RuntimeError: Claude 529: overloaded", True), ("RuntimeError: Sheets 503: busy", True),
                                       ("RuntimeError: Gemini 429: quota", True), ("RuntimeError: YouTube start 403: forbidden", True),
                                       ("RuntimeError: fal submit 500: oops", True), ("RuntimeError: HTTP 502", True)])
def test_repair_classifier_reads_http_codes_only_in_context(tmp_path, text, skip):
    p = tmp_path / "last_error.txt"; p.write_text(text)
    r = subprocess.run(["grep", "-qiE", _classifier(), str(p)])
    assert (r.returncode == 0) == skip, text

# ---------------- Flaw 3 + structural note 2.1: the teased premise survives a failed attempt, expires, and must be a vetted pitch
def test_tease_is_consumed_only_after_the_plan_is_saved(setting):
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass?", "family": "F01_body"}))
    S_ = {"room": {"spine": {"teased_premise": "What if your bones turned to glass?"}}}
    assert EP.consume_tease({"room": {"spine": {}}}) is False and core.S("NEXT_PREMISE")
    setting("NEXT_PREMISE", json.dumps({"premise": "A newer promise", "family": "F02_time"}))
    assert EP.consume_tease(S_) is False and "newer" in core.S("NEXT_PREMISE")          # a newer tease is never wiped
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass?", "family": "F01_body"}))
    assert EP.consume_tease(S_) is True and core.S("NEXT_PREMISE") == ""

def test_failed_planning_keeps_the_tease_for_the_retry(setting, monkeypatch):
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass for a day?", "family": "F01_body", "headline": "Glass Bones"}))
    monkeypatch.setattr(EP, "_stage_plan", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("narration too short")))
    monkeypatch.setattr(EP.PF, "check", lambda *a, **k: (True, ""))
    with pytest.raises(RuntimeError): EP.produce("2031-01-07T15:00:00Z")
    assert "bones" in core.S("NEXT_PREMISE")

def test_stale_tease_is_dropped(setting):
    old = (core.now_utc() - dt.timedelta(days=ROOM.TEASE_MAX_AGE_DAYS + 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass?", "family": "F01_body", "set_at": old}))
    assert ROOM.teased_pitch({"banned": [], "recent": []}, []) is None and core.S("NEXT_PREMISE") == ""
    setting("NEXT_PREMISE", json.dumps({"premise": "What if your bones turned to glass?", "family": "F01_body", "set_at": core.iso()}))
    assert ROOM.teased_pitch({"banned": [], "recent": []}, [])["teased"]

def test_invented_tease_is_replaced_by_a_vetted_pitch():
    good = [{"premise": "What if your heart beat twice as fast?", "family": "F01_body", "headline": "Double Heartbeat"}]
    spine = {"premise": "What if pillows floated?", "family": "F08_rules", "next_tease": {"premise": "What if the moon was made of soup?", "family": "F09_space", "line": "x"}}
    t = ROOM.clean_tease(spine, good); assert t["premise"] == good[0]["premise"]
    spine["next_tease"] = {"premise": "What if your heart beat twice as fast?", "family": "F01_body", "line": "Your heart. Twice. Next."}
    t = ROOM.clean_tease(spine, good); assert t["line"] == "Your heart. Twice. Next."          # a vetted choice keeps the Showrunner's line

def test_scheduled_tease_records_when_it_was_set():
    src = open(os.path.join(ROOT, "whatifs", "episode.py")).read()
    assert "set_at=iso()" in src

# ---------------- Flaw 4: Sheets tabs grow past column Z
class _Fake(core.SheetStore):
    def __init__(self, cols=26):
        self.id = "X"; self.calls = []; self.cols = cols
    def _req(self, method, url, **kw):
        self.calls.append((method, url, kw.get("json")))
        if "fields=sheets.properties" in url:
            return {"sheets": [{"properties": {"title": t, "sheetId": n, "gridProperties": {"columnCount": self.cols}}} for n, t in enumerate(core.TABS)]}
        if "/values/" in url and method == "GET": return {"values": [["episode_id", "slot_et"]]}
        return {}

def test_narrow_tabs_are_widened_before_the_wide_header_is_written():
    s = _Fake(26); s.ensure_tabs()
    grow = [j for m, u, j in s.calls if j and "requests" in j and "appendDimension" in json.dumps(j)]
    assert grow and any(r["appendDimension"]["length"] >= core.grid_columns(len(core.TABS["Episodes"])) - 26 for j in grow for r in j["requests"])
    sid = list(core.TABS).index("Episodes")
    grow_ep = next(k for k, c in enumerate(s.calls) if c[2] and any(r.get("appendDimension", {}).get("sheetId") == sid for r in c[2].get("requests", [])))
    header_ep = next(k for k, c in enumerate(s.calls) if c[0] == "PUT" and "/values/Episodes!A1" in c[1])
    assert grow_ep < header_ep                         # the Episodes tab grows BEFORE its 28-column header is written
    s2 = _Fake(60); s2.ensure_tabs(); assert not [c for c in s2.calls if c[2] and "appendDimension" in json.dumps(c[2])]

def test_new_tabs_are_created_wide_and_clear_covers_every_column():
    class _New(_Fake):
        def _req(self, method, url, **kw):
            if "fields=sheets.properties" in url and not any(c[0] == "POST" for c in self.calls): self.calls.append((method, url, None)); return {"sheets": []}
            return super()._req(method, url, **kw)
    s = _New(); s.ensure_tabs()
    add = next(c[2] for c in s.calls if c[2] and "addSheet" in json.dumps(c[2]))
    widths = {r["addSheet"]["properties"]["title"]: r["addSheet"]["properties"]["gridProperties"]["columnCount"] for r in add["requests"]}
    assert widths["Episodes"] >= 28 + 4 and min(widths.values()) >= 26
    s.calls.clear(); s.replace("Episodes", [])
    rng = re.search(r"!A2:([A-Z]+):clear", s.calls[0][1]).group(1); assert len(rng) == 2          # past Z
    assert core.col_letter(28) == "AB" and core.col_letter(52) == "AZ"

# ---------------- Flaw 5: Instagram / Facebook independent, files sent directly, links always closed
def test_one_platform_failing_never_skips_the_other_and_links_are_closed(monkeypatch, tmp_path):
    f = tmp_path / "reel0.mp4"; f.write_bytes(b"x"); c = tmp_path / "cover0.jpg"; c.write_bytes(b"y")
    opened, closed, calls = [], [], []
    monkeypatch.setattr(MG.PUB, "drive_upload", lambda p, n, public=False: (opened.append(n), (n, "https://drive/" + n))[1])
    monkeypatch.setattr(MG.PUB, "drive_private", lambda fid: closed.append(fid))
    def ig(url, cap, cover=None, video_path=None, url_fn=None): calls.append("ig"); raise RuntimeError("IG container: error")
    def fb(url, cap, video_path=None, url_fn=None): calls.append(("fb", video_path)); return "FB1"
    monkeypatch.setattr(MG.PUB, "ig_reel", ig); monkeypatch.setattr(MG.PUB, "fb_reel", fb)
    sid, i, fbid = MG._post_reel({"file": str(f), "cover": str(c), "caption": "c #a", "hook": "h"}, {"title": "T"}, "https://youtu.be/x")
    assert calls[0] == "ig" and calls[1] == ("fb", str(f)) and fbid == "FB1" and i == ""
    assert sorted(opened) == sorted(closed) == ["cover0.jpg"]                    # the video itself was never made public (sent directly)

def test_links_are_closed_even_when_everything_fails(monkeypatch, tmp_path):
    f = tmp_path / "reel0.mp4"; f.write_bytes(b"x"); opened, closed = [], []
    monkeypatch.setattr(MG.PUB, "drive_upload", lambda p, n, public=False: (opened.append(n), (n, "https://drive/" + n))[1])
    monkeypatch.setattr(MG.PUB, "drive_private", lambda fid: closed.append(fid))
    def ig(url, cap, cover=None, video_path=None, url_fn=None): url_fn(); raise RuntimeError("down")
    def fb(url, cap, video_path=None, url_fn=None): url_fn(); raise RuntimeError("down")
    monkeypatch.setattr(MG.PUB, "ig_reel", ig); monkeypatch.setattr(MG.PUB, "fb_reel", fb)
    MG._post_reel({"file": str(f), "caption": "c"}, {"title": "T"}, "https://youtu.be/x")
    assert opened == ["reel0.mp4"] and closed == ["reel0.mp4"]                   # one link made on demand, shared, then closed

class _R:
    def __init__(self, j, code=200): self._j = j; self.status_code = code; self.text = json.dumps(j)
    def json(self): return self._j

def test_ig_and_fb_send_the_file_bytes_directly(monkeypatch, tmp_path):
    f = tmp_path / "r.mp4"; f.write_bytes(b"abc")
    monkeypatch.setattr(PUB, "FAKE", False); monkeypatch.setattr(PUB, "_meta_key", lambda: "K")
    core.set_setting("IG_USER_ID", "IG1"); core.set_setting("FB_PAGE_ID", "PG1"); posts = []
    def post(url, headers=None, data=None, timeout=0, **k):
        body = data.read() if hasattr(data, "read") else data; posts.append((url, dict(headers or {}), body))
        if url.endswith("IG1/media"): return _R({"id": "C1", "uri": "https://rupload.facebook.com/ig-api-upload/v24.0/C1"})
        if "rupload" in url: return _R({"success": True})
        if url.endswith("media_publish"): return _R({"id": "IGPOST"})
        if url.endswith("video_reels"): return _R({"video_id": "V1", "success": True})
        return _R({})
    monkeypatch.setattr(PUB.requests, "post", post)
    monkeypatch.setattr(PUB.requests, "get", lambda url, **k: _R({"status_code": "FINISHED", "status": {"video_status": "ready"}}))
    monkeypatch.setattr(PUB.time, "sleep", lambda s: None)
    no_link = lambda: pytest.fail("no public link should be needed")
    assert PUB.ig_reel(None, "cap", None, video_path=str(f), url_fn=no_link) == "IGPOST"
    assert PUB.fb_reel(None, "cap", video_path=str(f), url_fn=no_link) == "V1"
    ups = [p for p in posts if "rupload" in p[0]]
    assert len(ups) == 2 and all(p[2] == b"abc" and p[1]["offset"] == "0" and p[1]["file_size"] == "3" for p in ups)
    assert any(p[0].endswith("IG1/media") and p[2].get("upload_type") == "resumable" and "video_url" not in p[2] for p in posts)

def test_direct_upload_failure_falls_back_to_the_link(monkeypatch, tmp_path):
    f = tmp_path / "r.mp4"; f.write_bytes(b"abc")
    monkeypatch.setattr(PUB, "FAKE", False); monkeypatch.setattr(PUB, "_meta_key", lambda: "K"); core.set_setting("FB_PAGE_ID", "PG1"); used = []
    def post(url, headers=None, data=None, timeout=0, **k):
        if url.endswith("video_reels"): return _R({"video_id": "V1", "success": True})
        if "rupload" in url and (headers or {}).get("file_url"): used.append(headers["file_url"]); return _R({"success": True})
        if "rupload" in url: return _R({"error": "nope"}, 500)
        return _R({})
    monkeypatch.setattr(PUB.requests, "post", post)
    monkeypatch.setattr(PUB.requests, "get", lambda url, **k: _R({"status": {"video_status": "ready"}}))
    assert PUB.fb_reel(None, "cap", video_path=str(f), url_fn=lambda: "https://drive/link") == "V1" and used == ["https://drive/link"]

# ---------------- Flaw 6: the final mix is written as stereo and the big temp file is always removed
def test_write_mix_is_stereo_and_cleans_up(tmp_path, monkeypatch):
    mix = (np.random.default_rng(0).standard_normal((48000, 2)) * 0.1).astype(np.float32)
    out = RN.write_mix(mix, str(tmp_path / "m.wav"))
    ch = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=channels", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    assert ch == "2" and not os.path.exists(out + ".raw.wav")
    def boom(*a, **k): raise subprocess.CalledProcessError(1, "ffmpeg")
    monkeypatch.setattr(RN.subprocess, "run", boom)
    with pytest.raises(subprocess.CalledProcessError): RN.write_mix(mix, str(tmp_path / "n.wav"))
    assert not os.path.exists(str(tmp_path / "n.wav") + ".raw.wav")

# ---------------- Flaw 9: strategies credited once, matched on dimension AND name; a pool never shrinks
def test_credits_are_deduplicated_and_matched_on_dimension_and_name():
    st = core.store()
    st.append("Strategies", [{"dimension": "humour", "name": "dup", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0},
                             {"dimension": "reel", "name": "dup", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0},
                             {"dimension": "reel", "name": "R2", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0}])
    d = {"strategies": {"reel": "dup"}, "reel_formats": ["dup", "R2", "R2"]}
    cr = MG.strategy_credits(d, {"shorts": 0.6, "pack": None, "open": None, "hold": None, "reach": None})
    assert cr == {("reel", "dup"): 0.6, ("reel", "R2"): 0.6}
    MG._credit_strategies(st, cr)
    rows = {(r["dimension"], r["name"]): r for r in st.rows("Strategies")}
    assert rows[("reel", "dup")]["plays"] == "1" and rows[("reel", "R2")]["plays"] == "1" and rows[("humour", "dup")]["plays"] == "0"

def test_swapped_package_and_missing_data_are_not_credited():
    d = {"strategies": {"title": "N1", "thumb": "T1", "story": "S1"}}
    assert MG.strategy_credits(d, {"pack": 0.7, "hold": None, "open": None, "reach": None, "shorts": None}, swapped=True) == {}

def test_failed_invention_restores_the_weak_strategy(monkeypatch):
    st = core.store(); st.replace("Strategies", [])
    st.append("Strategies", [{"dimension": "story", "name": n, "status": "ACTIVE", "plays": 5, "score_sum": s * 5, "score_n": 5} for n, s in (("A", 0.9), ("B", 0.8), ("C", 0.2))])
    monkeypatch.setattr(MG, "ask", lambda *a, **k: {"name": "", "definition": "x"})
    MG._evolve()
    assert {r["name"]: r["status"] for r in st.rows("Strategies")}["C"] == "ACTIVE" and len(st.rows("Strategies")) == 3

def test_invented_name_clash_gets_a_unique_name(monkeypatch):
    st = core.store(); st.replace("Strategies", [])
    st.append("Strategies", [{"dimension": "story", "name": n, "status": "ACTIVE", "plays": 5, "score_sum": s * 5, "score_n": 5} for n, s in (("A", 0.9), ("B", 0.8), ("C", 0.2))]
              + [{"dimension": "humour", "name": "none", "status": "ACTIVE", "plays": 0, "score_sum": 0, "score_n": 0}])
    monkeypatch.setattr(MG, "ask", lambda *a, **k: {"name": "none", "definition": "a new story shape"})
    MG._evolve()
    names = [r["name"] for r in st.rows("Strategies")]
    assert names.count("none") == 1 and "none_story" in names

# ---------------- Flaw 10: no gendered line for the rotating guest; the hook sheet row is corrected
def test_no_gendered_line_about_the_guest():
    for kind, pool in CTA.POOLS.items():
        for item in pool:
            for spk, tag, text in item:
                assert not re.search(r"\b(he|she|his|her|him)\b", text, re.I), text

def test_hook_sheet_row_is_corrected_when_the_opening_changed():
    st = core.store()
    st.append("Hook_Candidates", [{"episode_id": "EPH", "line": "Eight billion people do it.", "chosen": "TRUE", "applied": "TRUE"}])
    rec = {"episode_id": "EPH", "applied": True, "chosen_id": "h0", "candidates": [{"id": "h0", "line": "Eight billion people do it."}], "notes": []}
    assert HOOKS.verify_in_narration(rec, [{"text": "Something else entirely."}]) is False
    row = [r for r in st.rows("Hook_Candidates") if r["episode_id"] == "EPH"][0]
    assert row["applied"] == "FALSE" and rec["status"] == "needs_human_choice"
    st.append("Hook_Candidates", [{"episode_id": "EPK", "line": "Ok line", "chosen": "TRUE", "applied": "TRUE"}])
    rec2 = dict(rec, episode_id="EPK", candidates=[{"id": "h0", "line": "Ok line"}], notes=[])
    assert HOOKS.verify_in_narration(rec2, [{"text": "Ok line"}]) is True
    assert [r for r in st.rows("Hook_Candidates") if r["episode_id"] == "EPK"][0]["applied"] == "TRUE"
