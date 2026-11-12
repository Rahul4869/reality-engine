"""v12 V2c-b2a THE PLATFORMS: the release sheet as data, pure request bodies, one master file sent natively to YouTube Shorts, Instagram Reels and
Facebook Reels under Publishing's own run, a receipt for every row read back from the platform, the pass that finishes what waits, check
release_sheet, and 'made' as a field of a Short's record. Each rule both ways. No keys, no network."""
import datetime as dt, json, os
import pytest
from whatifs import core, shorts2 as SH, ladder as LAD, release as REL, publish as PUB, notify as NT, specials as SP, launch as LA, manage as MG, contract as CON

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 12, 16, 6, 0, tzinfo=UTC)          # a Wednesday
H = dt.timedelta(hours=1)

@pytest.fixture(autouse=True)
def _no_faults():
    PUB.FAKE_FAULTS.clear(); yield; PUB.FAKE_FAULTS.clear()

def _quiet(monkeypatch):
    monkeypatch.setattr(PUB, "email", lambda *a, **k: True); monkeypatch.setattr(NT, "in_quiet_hours", lambda now=None: False)

def _bench(*premises):
    core.store().append("Premise_Bench", [{"bench_id": f"B{i}", "premise": p, "headline": p, "family": "", "ptype": "collective", "status": "READY", "claude_score": 9, "gemini_score": 9,
                                           "combined": 9 - i / 10, "added": core.iso()} for i, p in enumerate(premises)])

def _recs(sid): return {r["platform"]: r for r in REL.records(sid)}
def _row(sid): return next(r for r in core.store().rows("Specials") if r["id"] == sid)
def _led(sid): return [r for r in core.store().rows("Feature_Ledger") if r.get("episode_id") == sid and r.get("stage") == "release"]
def _runs(sid): return [(s["dept"], s["trigger"], s["status"]) for s in core.store().rows("Sessions") if s.get("episode_id") == sid]
def _sent(sid, p): return json.loads(_recs(sid)[p]["sent"])
def _rc(sid, p, row): return _recs(sid)[p]["receipts"][row]

def _short(monkeypatch, setting, sid, review="0", now=NOW, premise="What if the Moon left tonight?", closed=False):
    """One real (offline) Short with its own id. closed = nobody has proven yet that uploads are open, and the check is not due."""
    _quiet(monkeypatch); _bench(premise); setting("SHORTS_REVIEW_FIRST_N", review)
    if closed: setting("UPLOAD_CHECK_AT", core.iso())
    r = SH.run(force=True, now=now, episode_id=sid); assert r["ok"], r
    return r

def _count(monkeypatch):
    """Counts the uploads that really leave for a platform."""
    n = {"youtube": 0, "instagram": 0, "facebook": 0}
    for key, name in (("youtube", "yt_upload"), ("instagram", "ig_reel"), ("facebook", "fb_reel")):
        real = getattr(PUB, name)
        def wrap(*a, _real=real, _k=key, **k): n[_k] += 1; return _real(*a, **k)
        monkeypatch.setattr(PUB, name, wrap)
    return n

# ------------------------------------------------------------------ 1. the sheet is data, and it is honest about what the machine cannot set
def test_the_release_sheet_is_data_and_names_who_sets_each_row_and_how_it_is_proven():
    assert {r[0] for r in REL.SHEET} == set(REL.PLATFORMS) and len({(r[0], r[1]) for r in REL.SHEET}) == len(REL.SHEET)
    for plat, row, who, proof, what in REL.SHEET:
        assert who in ("code", "hand", "once", "later") and len(what) > 15, (plat, row)
        assert (proof in ("read", "sent", "file")) == (who == "code"), (plat, row)          # a row code sets says how it is proven; a row it cannot set claims no proof
    assert REL.rows_of("youtube") == ["file", "short", "title", "description", "tags", "category", "language", "kids", "ai", "privacy", "thumbnail", "playlist"]
    assert REL.rows_of("instagram") == ["file", "fit", "reel", "caption", "ai", "cover", "audio", "trial"] and REL.rows_of("facebook") == ["file", "fit", "description", "ai", "published"]
    assert REL.not_ours() == {"hand": 1, "once": 1, "later": 1} and REL.rows_of("youtube", "hand") == ["link"]      # the link from a Short to its long video is his hand's (V3)
    sent_only = {(r[0], r[1]) for r in REL.SHEET if r[3] == "sent"}
    assert {("instagram", "trial"), ("instagram", "audio")} <= sent_only                   # Instagram shows no field for either: never called "verified"

# ------------------------------------------------------------------ 2. request bodies are pure functions: a test reads every field
def test_the_youtube_body_is_built_without_a_network_call_and_the_upload_sends_exactly_it(monkeypatch, tmp_path):
    b = PUB.yt_body("A <title>  with   spaces", "Line one.\n#whatif", ["what if", "what if", "science"], ai_label=True)
    assert b == {"snippet": {"title": "A title with spaces", "description": "Line one.\n#whatif", "tags": ["what if", "science"], "categoryId": "28", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
                 "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "license": "youtube", "containsSyntheticMedia": True}}
    s = PUB.yt_body("t", "d", [], publish_at="2026-12-20T10:00:00Z", ai_label=False)["status"]
    assert s["privacyStatus"] == "private" and s["publishAt"] == "2026-12-20T10:00:00Z" and s["containsSyntheticMedia"] is False      # scheduled = private until its time
    assert PUB.yt_body("t", "d", [], privacy="unlisted")["status"]["privacyStatus"] == "unlisted" and "publishAt" not in PUB.yt_body("t", "d", [])["status"]
    p = tmp_path / "REL_body_1.mp4"; p.write_bytes(b"x")
    vid = PUB.yt_upload(str(p), "A <title>  with   spaces", "Line one.\n#whatif", ["what if", "what if", "science"], short=True)
    assert vid == "FAKE_REL_body_1.mp4" and PUB._fake_get("youtube", vid)["sent"] == b                    # offline, the stand-in platform holds the very body
    got = PUB.yt_read(vid); assert got["title"] == "A title with spaces" and got["privacy"] == "public" and got["ai"] is True and got["kids"] is False and got["processed"] is True
    assert PUB.yt_read("FAKE_never_uploaded.mp4") == {} and PUB.yt_read("") == {}

def test_the_instagram_and_facebook_parameters_are_pure_and_old_callers_send_what_they_always_sent(setting):
    assert PUB.ig_reel_params("cap") == {"media_type": "REELS", "caption": "cap", "share_to_feed": "true", "is_ai_generated": "true"}      # what ig_reel always sent
    assert PUB.ig_reel_params("cap", cover_url="https://x/c.jpg")["cover_url"] == "https://x/c.jpg"
    t = PUB.ig_reel_params("cap", "https://x/c.jpg", 1000, "Reality Engine", "SS_PERFORMANCE")
    assert json.loads(t["trial_params"]) == {"graduation_strategy": "SS_PERFORMANCE"} and "share_to_feed" not in t      # a Trial Reel is shown to non-followers only
    assert t["audio_name"] == "Reality Engine" and t["cover_url"] == "https://x/c.jpg" and "thumb_offset" not in t      # a cover image wins over a frame (Instagram's own rule)
    assert PUB.ig_reel_params("cap", None, 1000)["thumb_offset"] == "1000" and "thumb_offset" not in PUB.ig_reel_params("cap") and "audio_name" not in PUB.ig_reel_params("cap", audio_name="  ")
    assert len(PUB.ig_reel_params("x" * 5000)["caption"]) == 2100
    assert PUB.fb_reel_finish("d" * 3000, "V1") == {"is_ai_generated": "true", "upload_phase": "finish", "video_id": "V1", "video_state": "PUBLISHED", "description": "d" * 2000}
    setting("META_AI_LABEL_ON", "FALSE")
    assert "is_ai_generated" not in PUB.ig_reel_params("cap") and "is_ai_generated" not in PUB.fb_reel_finish("d", "V1") and PUB.ig_reel_params("cap", ai=True)["is_ai_generated"] == "true"
    assert PUB.ig_reel(None, "cap") == "FAKE_IG" and PUB.fb_reel(None, "d") == "FAKE_FB"                # the older callers (special reels, cut-down reels) are untouched
    assert PUB.ig_reel(None, "cap", ref="S9") == "FAKE_IG_S9" and PUB.ig_read("FAKE_IG_S9")["product"] == "REELS" and PUB.ig_read("FAKE_IG") == {}
    assert PUB.fb_reel(None, "d", ref="S9") == "FAKE_FB_S9" and PUB.fb_read("FAKE_FB_S9") == {"description": "d", "published": True}

# ------------------------------------------------------------------ 3. where a file fits (the platforms' own published limits)
def test_a_file_fits_a_platform_or_the_reason_is_named():
    ok = {"w": 1080, "h": 1920, "sec": 30.0, "fps": 30.0}
    assert all(REL.fit(p, ok, small=False) == [] for p in REL.PLATFORMS) and all(REL.fit(p, dict(ok, sec=3.0), small=False) == [] for p in REL.PLATFORMS)
    assert REL.fit("youtube", dict(ok, sec=180.0), small=False) == [] and "over the 180 s" in REL.fit("youtube", dict(ok, sec=181.0), small=False)[0]
    assert "long video" in REL.fit("youtube", dict(ok, w=1920, h=1080), small=False)[0] and REL.fit("youtube", dict(ok, w=1080, h=1080), small=False) == []      # square is a Short too
    assert REL.fit("facebook", dict(ok, sec=90.0), small=False) == [] and "3 to 90 s" in REL.fit("facebook", dict(ok, sec=90.5), small=False)[0] and REL.fit("facebook", dict(ok, sec=2.9), small=False)
    assert "under Facebook's 540 x 960" in REL.fit("facebook", dict(ok, w=539, h=958), small=False)[0] and "not upright" in REL.fit("facebook", dict(ok, w=1080, h=1080), small=False)[0]
    assert REL.fit("facebook", dict(ok, fps=23.0), small=False) and REL.fit("facebook", dict(ok, fps=24.0), small=False) == []
    assert REL.fit("instagram", dict(ok, sec=2.0), small=False) and REL.fit("instagram", dict(ok, w=1921), small=False) and REL.fit("instagram", dict(ok, fps=22.0), small=False)
    assert REL.fit("instagram", dict(ok, sec=95.0), small=False) == []                                   # 95 s goes to Instagram and YouTube - and not to Facebook
    small = {"w": 360, "h": 640, "sec": 22.0, "fps": 30.0}
    assert REL.fit("facebook", small, small=True) == [] and REL.fit("facebook", small, small=False)      # the rehearsal's third-size file meets the same limits as a full-size one
    assert REL.fit("youtube", {"w": 0, "h": 0, "sec": 0, "fps": 0}) == ["the file could not be measured"] and REL.fit("tiktok", ok)

# ------------------------------------------------------------------ 4. the words next to a Short: one text per platform, never an ask
ROW = {"id": "SHT", "kind": "short", "title": "The  Day the Moon Left", "format": "S1", "script": "The Moon just left. You felt it in your knees.\nThe sea goes quiet.\nWould you look up?"}

def test_every_platform_gets_its_own_words_built_from_the_shorts_own_record(setting):
    t = REL.texts(ROW); yt, ig, fb = t["youtube"], t["instagram"]["caption"], t["facebook"]["description"]
    assert yt["title"] == "The Day the Moon Left" and yt["description"].startswith("The Moon just left.\n") and yt["tags"] == ["whatif", "science", "what if"]
    assert ig.startswith("The Moon just left.\n") and fb.startswith("The Day the Moon Left\nThe Moon just left.")      # Instagram opens on the hook (its first line shows before 'more'); Facebook on the title
    assert len({yt["description"], ig, fb}) == 3 and all(REL.HOW in x for x in (yt["description"], ig, fb))                # three texts, each says how it was made
    assert all(REL.text_issues(p, x) == [] for p, x in (("youtube", yt["description"]), ("youtube", yt["title"]), ("instagram", ig), ("facebook", fb)))
    assert not [w for w in ("reality on trial", "subscribe", "#shorts", "link in bio", "Tuesday") if w.lower() in (yt["description"] + ig + fb + " ".join(yt["tags"])).lower()]
    setting("SHORT_HASHTAGS", "#a #b #c #d #e #f #g #a")
    t = REL.texts(ROW); assert t["youtube"]["description"].count("#") == 3 and t["instagram"]["caption"].count("#") == 5 and t["facebook"]["description"].count("#") == 3
    setting("SHORT_HASHTAGS", ""); assert "#" not in REL.texts(ROW)["instagram"]["caption"] and REL.texts(ROW)["youtube"]["tags"] == ["what if"]
    assert REL.texts(dict(ROW, script=""))["youtube"]["description"].startswith("The Day the Moon Left")       # no script on the record: the title stands in, never an empty line

def test_a_text_that_carries_an_ask_a_courtroom_word_a_link_or_too_many_hashtags_is_recognised_and_ordinary_words_are_not():
    assert "an ask" in REL.text_issues("youtube", "Subscribe for more.")[0] and "courtroom" in REL.text_issues("instagram", "Dr. Grimm objects.")[0]
    assert REL.text_issues("instagram", "Watch https://youtu.be/x") == ["a link"] and REL.text_issues("youtube", "#a #b #c #d") == ["4 hashtags (at most 3)"]
    assert REL.text_issues("instagram", "#a #b #c #d #e") == [] and REL.text_issues("instagram", "#a #b #c #d #e #f")
    for fine in ("The Moon just left. You felt it in your knees.", "Would you follow the light?", "You like the quiet. It does not like you.", "The sea keeps its own counsel."):
        assert REL.text_issues("youtube", fine) == [], fine                                               # only what code can RECOGNISE as wrong is named

# ------------------------------------------------------------------ 5. the receipts: wanted against what the platform itself answers
def test_a_receipt_says_kept_drift_or_sent_and_a_bad_text_is_drift_even_when_the_platform_kept_it():
    want = {"title": "T", "description": "Hook.\n#whatif", "tags": ["a", "B"], "category": "28", "language": "en", "kids": False, "ai": True, "privacy": "public"}
    same = {"title": "T", "description": "Hook.  \n #whatif", "tags": ["b", "A"], "category": "28", "language": "en", "audio_language": "en", "kids": False, "ai": True, "privacy": "public"}
    assert {v[0] for v in REL.compare("youtube", want, same).values()} == {REL.KEPT}                     # white space and the order of tags are not drift
    d = REL.compare("youtube", want, dict(same, title="Other", privacy="private", ai=False, kids=True, category="24", audio_language="hi", tags=["a"]))
    assert all(d[k][0] == REL.DRIFT for k in ("title", "privacy", "ai", "kids", "category", "language", "tags")) and d["description"][0] == REL.KEPT
    s = REL.compare("youtube", want, {"title": "T", "language": "en"})
    assert s["title"][0] == REL.KEPT and s["ai"][0] == REL.SENT and s["description"][0] == REL.SENT and s["tags"][0] == REL.SENT      # a field the answer does not carry is 'sent', never 'kept'
    bad = REL.compare("youtube", {"description": "Hook. Subscribe now!"}, {"description": "Hook. Subscribe now!"})
    assert bad["description"][0] == REL.DRIFT and "an ask" in bad["description"][1]
    assert REL.state_of({"a": [REL.KEPT, ""], "b": [REL.SENT, ""], "c": [REL.OFF, ""]}) == REL.DONE and REL.state_of({"a": [REL.KEPT, ""], "b": [REL.WAITING, ""]}) == REL.OPEN
    assert REL.state_of({"a": [REL.WAITING, ""], "b": [REL.DRIFT, ""]}) == REL.FLAWED and REL.state_of({"a": [REL.REFUSED, ""]}) == REL.FLAWED

# ------------------------------------------------------------------ 6. the real production: one master, three native uploads, every row read back
def test_a_short_goes_out_as_three_native_uploads_of_one_master_and_every_row_has_a_good_receipt(monkeypatch, setting):
    import whatifs.models as M, whatifs.media as MD
    n = _count(monkeypatch); paid = []
    r = _short(monkeypatch, setting, "SHREL01"); sid = r["id"]; row = _row(sid); rec = _recs(sid)
    assert n == {"youtube": 1, "instagram": 1, "facebook": 1} and r["status"] == "POSTED" and row["status"] == "POSTED"
    assert (row["yt_id"], row["ig"], row["fb"]) == ("FAKE_SHREL01.mp4", "FAKE_IG_SHREL01", "FAKE_FB_SHREL01") == tuple(rec[p]["native_id"] for p in REL.PLATFORMS)
    assert row["made"] == core.iso(NOW) and len(row["sha"]) == 64 and row["sha"] == REL.sha(r["path"]) and row["file"] == "drive:SHREL01.mp4" and row["cover"] == "drive:SHREL01_cover.jpg"
    assert all(x["state"] == REL.DONE and x["sha"] == row["sha"] and x["checked"] and int(float(x["tries"])) == 1 for x in rec.values())      # each platform got the master, byte for byte
    for p in REL.PLATFORMS:
        assert set(rec[p]["receipts"]) == set(REL.rows_of(p)) and all(v[0] in REL.GOOD for v in rec[p]["receipts"].values()), (p, rec[p]["receipts"])
    yt = _sent(sid, "youtube"); ig = _sent(sid, "instagram"); fb = _sent(sid, "facebook")
    assert yt["snippet"]["title"] == row["title"] and "#shorts" not in (yt["snippet"]["title"] + yt["snippet"]["description"]).lower() and yt["snippet"]["tags"] == ["whatif", "science", "what if"]
    assert yt["status"] == {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True, "license": "youtube", "containsSyntheticMedia": True}
    assert json.loads(ig["trial_params"]) == {"graduation_strategy": "SS_PERFORMANCE"} and ig["audio_name"] == "Reality Engine" and ig["cover_url"].endswith("cover.jpg") and ig["is_ai_generated"] == "true" and "share_to_feed" not in ig
    assert fb["video_state"] == "PUBLISHED" and fb["is_ai_generated"] == "true" and len({yt["snippet"]["description"], ig["caption"], fb["description"]}) == 3      # never one text for all three
    hook = row["script"].splitlines()[0]; assert ig["caption"].startswith(hook[:20]) and yt["snippet"]["description"].startswith(hook[:20])
    fake = PUB._fake_get("youtube", row["yt_id"]); assert fake["thumbnail"] == "cover.jpg" and fake["playlist"] and _rc(sid, "youtube", "thumbnail")[0] == REL.SENT
    assert _rc(sid, "instagram", "trial")[0] == REL.SENT and _rc(sid, "instagram", "audio")[0] == REL.SENT and "no field to read it back" in _rc(sid, "instagram", "trial")[1]
    assert _runs(sid) == [("D14", "write", "ok"), ("D7", "short_voice", "ok"), ("D13", "short_seat", "ok"), ("D8", "short_gate", "ok"), ("D14", "make", "ok"), ("D9", "short_publish", "ok"), ("D8", "release_gate", "ok")]
    led = _led(sid); assert [(x["feature"], x["status"]) for x in led] == [("release_sheet", "PASS")] and "YouTube Shorts: 10 kept, 2 sent without a read-back" in led[0]["evidence"] and "3 rows are not the machine's to set" in led[0]["evidence"]
    lr = LAD.row(sid); assert lr["state"] == "POSTED" and lr["yt_id"] == row["yt_id"] and lr["posted"] == core.iso(NOW)
    monkeypatch.setattr(M, "ask", lambda *a, **k: paid.append("text")); monkeypatch.setattr(MD, "still", lambda *a, **k: paid.append("image")); monkeypatch.setattr(MD, "animate", lambda *a, **k: paid.append("clip"))
    before = len(core.store().rows("Cost_Log")); REL.short(sid, now=NOW + H); assert REL.settle(NOW + H) == []
    assert n == {"youtube": 1, "instagram": 1, "facebook": 1} and not paid and len(core.store().rows("Cost_Log")) == before      # a second pass uploads nothing and pays nothing
    os.remove(os.path.join(PUB._fake_drive(), "SHREL01.mp4"))

def test_the_cover_is_the_shorts_own_first_picture_upright_and_a_jpeg(monkeypatch, setting):
    from PIL import Image
    r = _short(monkeypatch, setting, "SHREL02"); p = os.path.join(os.path.dirname(r["path"]), "cover.jpg")
    im = Image.open(p); assert im.format == "JPEG" and im.size == SP._vsize() and im.size[1] > im.size[0]
    assert os.path.exists(os.path.join(PUB._fake_drive(), "SHREL02_cover.jpg"))
    setting("SHORT_THUMB_ON", "FALSE"); _bench("What if rain fell upward?"); r2 = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL03"); assert r2["ok"]
    assert _rc("SHREL03", "youtube", "thumbnail")[0] == REL.OFF and _rc("SHREL03", "instagram", "cover")[0] == REL.OFF and "thumbnail" not in PUB._fake_get("youtube", r2["yt_id"])
    s = _sent("SHREL03", "instagram"); assert "cover_url" not in s and "thumb_offset" not in s and _led("SHREL03")[0]["status"] == "PASS"      # switched off is a receipt too, not a gap

# ------------------------------------------------------------------ 7. drift: repaired once by code, or it stands and the check fails
def test_a_dropped_ai_field_is_set_again_once_and_a_repair_that_does_not_hold_fails_the_check(monkeypatch, setting):
    from whatifs.org import memos as MEM
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}}
    r = _short(monkeypatch, setting, "SHREL04"); a = _rc("SHREL04", "youtube", "ai")
    assert a[0] == REL.FIXED and "set again and read back" in a[1] and _recs("SHREL04")["youtube"]["state"] == REL.DONE and _led("SHREL04")[0]["status"] == "PASS"
    assert "1 repaired" in _led("SHREL04")[0]["evidence"] and not MEM.find(type="problem_memo", stage="release")
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}, "refuse": ("label",)}; _bench("What if rain fell upward?")
    r2 = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL05"); a = _rc("SHREL05", "youtube", "ai")
    assert r2["ok"] and r2["status"] == "POSTED" and a[0] == REL.DRIFT and "the repair did not hold" in a[1] and _recs("SHREL05")["youtube"]["state"] == REL.FLAWED
    led = _led("SHREL05"); assert led[0]["status"] == "FAIL" and "YouTube Shorts: ai DRIFT" in led[0]["evidence"]
    ms = MEM.find(type="problem_memo", stage="release"); assert len(ms) == 1 and ms[0]["to_depts"] == ["D9"] and ms[0]["body"]["check"] == "release_sheet" and not ms[0]["episode_id"]
    assert not [x for x in core.store().rows("Owner_Actions") if x.get("kind") == "contract_hold"]       # the Short is public: nothing is held and the owner is not asked
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"ai": False}, "ignore": ("label",)}; _bench("What if the wind kept every word?")
    r4 = SH.run(force=True, now=NOW + 72 * H, episode_id="SHREL05B"); a = _rc("SHREL05B", "youtube", "ai")
    assert r4["ok"] and a[0] == REL.DRIFT and "did not hold" in a[1]                                    # YouTube accepted the repair and still shows no label: a repair counts only when the platform shows it
    PUB.FAKE_FAULTS.clear(); _bench("What if every mirror showed tomorrow?")
    r3 = SH.run(force=True, now=NOW + 120 * H, episode_id="SHREL06"); assert r3["ok"] and _led("SHREL06")[0]["status"] == "PASS"
    assert not MEM.find(type="problem_memo", stage="release")                                           # the next Short whose sheet passes closes Publishing's memo

def test_a_platform_that_shows_other_words_than_were_sent_is_drift(monkeypatch, setting):
    PUB.FAKE_FAULTS["instagram"] = {"drift": {"caption": "Something Instagram made of it", "ai": False}}; PUB.FAKE_FAULTS["facebook"] = {"drift": {"published": False}}
    _short(monkeypatch, setting, "SHREL07")
    assert _rc("SHREL07", "instagram", "caption")[0] == REL.DRIFT and _rc("SHREL07", "instagram", "ai") == [REL.DRIFT, "Instagram shows no AI label"]
    assert _rc("SHREL07", "facebook", "published")[0] == REL.WAITING and _recs("SHREL07")["facebook"]["state"] == REL.OPEN and not _led("SHREL07")      # one platform still waits: the gate has not judged yet
    n = _count(monkeypatch); PUB.FAKE_FAULTS.pop("facebook"); assert REL.settle(NOW + H) == ["SHREL07"]
    assert n == {"youtube": 0, "instagram": 0, "facebook": 0} and _rc("SHREL07", "facebook", "published")[0] == REL.KEPT      # the pass READ Facebook again; it posted nothing twice
    led = _led("SHREL07"); assert led[0]["status"] == "FAIL" and "Instagram Reels: caption DRIFT" in led[0]["evidence"] and "Facebook" not in led[0]["evidence"].split("|")[0]

def test_an_upload_that_comes_back_private_is_drift_and_trips_the_lock(monkeypatch, setting):
    PUB.FAKE_FAULTS["youtube"] = {"drift": {"privacy": "private"}}
    _short(monkeypatch, setting, "SHREL08")
    assert _rc("SHREL08", "youtube", "privacy")[0] == REL.DRIFT and LA.lock_state() == "on" and _led("SHREL08")[0]["status"] == "FAIL"

# ------------------------------------------------------------------ 8. the thumbnail waits for YouTube's processing, and a tick finishes it
def test_a_shorts_thumbnail_is_set_only_after_processing_and_the_tick_finishes_it(monkeypatch, setting):
    PUB.FAKE_FAULTS["youtube"] = {"processing": True}
    r = _short(monkeypatch, setting, "SHREL09"); sid = "SHREL09"
    assert r["status"] == "POSTED" and _rc(sid, "youtube", "thumbnail")[0] == REL.WAITING and _recs(sid)["youtube"]["state"] == REL.OPEN
    assert "thumbnail" not in PUB._fake_get("youtube", r["yt_id"]) and not _led(sid) and not _recs(sid)["youtube"]["checked"]      # no call was made too early, and nothing is judged yet
    assert _recs(sid)["instagram"]["state"] == REL.DONE and LAD.row(sid)["state"] == "POSTED"            # the Short is out; one row waits
    runs = len(_runs(sid)); assert REL.settle(NOW + H) == [] and len(_runs(sid)) == runs                 # YouTube still processes: the pass asks once and starts no department run
    n = _count(monkeypatch); PUB.FAKE_FAULTS.clear()
    assert REL.settle(NOW + 2 * H) == [sid] and n == {"youtube": 0, "instagram": 0, "facebook": 0}       # ... and finishes without a second upload
    assert _rc(sid, "youtube", "thumbnail") == [REL.SENT, "set after processing had succeeded"] and PUB._fake_get("youtube", r["yt_id"])["thumbnail"] == "cover.jpg"
    assert _recs(sid)["youtube"]["state"] == REL.DONE and _led(sid)[0]["status"] == "PASS" and all(x["checked"] for x in _recs(sid).values())
    assert REL.settle(NOW + 3 * H) == [] and len(_led(sid)) == 1                                         # judged once

def test_a_thumbnail_that_never_could_be_set_or_that_youtube_refuses_fails_the_check_with_the_reason(monkeypatch, setting):
    PUB.FAKE_FAULTS["youtube"] = {"processing": True}
    _short(monkeypatch, setting, "SHREL10"); assert REL.settle(NOW + 23 * H) == [] and not _led("SHREL10")
    assert REL.settle(NOW + 25 * H) == ["SHREL10"]                                                       # its time is up (RELEASE_SETTLE_H): a row that still waits is a row that was not set
    t = _rc("SHREL10", "youtube", "thumbnail"); assert t[0] == REL.REFUSED and "never set" in t[1] and _led("SHREL10")[0]["status"] == "FAIL"
    PUB.FAKE_FAULTS["youtube"] = {"refuse": ("thumbnail", "playlist")}; _bench("What if rain fell upward?")
    r = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL11"); assert r["ok"] and r["status"] == "POSTED"
    t = _rc("SHREL11", "youtube", "thumbnail"); assert t[0] == REL.REFUSED and "phone-verified" in t[1] and _rc("SHREL11", "youtube", "playlist")[0] == REL.REFUSED
    ev = _led("SHREL11")[0]; assert ev["status"] == "FAIL" and "thumbnail REFUSED" in ev["evidence"] and "playlist REFUSED" in ev["evidence"]

# ------------------------------------------------------------------ 9. made while uploads were closed: made, waiting, and sent later from the copy in Drive
def test_a_short_made_while_uploads_are_closed_is_made_waits_and_goes_out_from_drive_when_they_open(monkeypatch, setting):
    n = _count(monkeypatch)
    r = _short(monkeypatch, setting, "SHREL12", closed=True); sid = "SHREL12"; row = _row(sid)
    assert r["ok"] and row["made"] and not row["yt_id"] and row["status"].startswith("UPLOAD_WAITING") and n["youtube"] == 0 and LA.lock_state() == "unknown"
    assert SH._made(row) and not SH._unmade(row) and [h["id"] for h in SH.history()] == [sid] and not SH.cadence(NOW + 25 * H)[0]      # it was MADE: it counts, whatever its upload does
    assert {p: x["state"] for p, x in _recs(sid).items()} == {"youtube": REL.QUEUED} and LAD.row(sid)["state"] == "MADE" and not _led(sid)
    assert REL.settle(NOW + H) == [] and n["youtube"] == 0                                               # still closed: nothing leaves
    os.remove(r["path"]); assert not os.path.exists(r["path"])                                           # another job, another day: this machine no longer has the file
    assert LA.upload_check() == "passed" and REL.settle(NOW + 30 * H) == [sid]
    row = _row(sid); assert row["status"] == "POSTED" and row["yt_id"] and n == {"youtube": 1, "instagram": 1, "facebook": 1}
    assert all(x["state"] == REL.DONE and x["sha"] == row["sha"] for x in _recs(sid).values()) and _led(sid)[0]["status"] == "PASS"
    lr = LAD.row(sid); assert lr["state"] == "POSTED" and lr["posted"] == core.iso(NOW + 30 * H)         # the ladder's clock starts when viewers could see it, not when it was made
    assert REL.settle(NOW + 31 * H) == [] and n["youtube"] == 1

def test_only_the_master_is_ever_sent_a_changed_file_is_refused_before_any_platform_sees_it(monkeypatch, setting):
    n = _count(monkeypatch)
    r = _short(monkeypatch, setting, "SHREL13", closed=True); sid = "SHREL13"; os.remove(r["path"])
    with open(os.path.join(PUB._fake_drive(), "SHREL13.mp4"), "ab") as f: f.write(b"another platform's mark")      # the kept file is no longer the file that was made
    LA.upload_check(); assert REL.settle(NOW + H) == [sid]
    assert n == {"youtube": 0, "instagram": 0, "facebook": 0} and all(x["state"] == REL.FAILED and "not the master" in x["note"] for x in _recs(sid).values())
    row = _row(sid); assert row["status"].startswith("UPLOAD_FAILED") and not row["yt_id"] and SH._made(row)      # it stays MADE; it is not out
    led = _led(sid); assert led[0]["status"] == "FAIL" and "never went up" in led[0]["evidence"] and REL.settle(NOW + 2 * H) == []
    with pytest.raises(RuntimeError): REL.master(dict(row, sha=""), None)                               # a record without a hash vouches for no file

# ------------------------------------------------------------------ 10. a platform that fails: tried again, bounded, and nothing is posted twice
def test_a_platform_that_fails_is_tried_again_up_to_the_limit_and_youtube_is_never_uploaded_twice(monkeypatch, setting):
    n = _count(monkeypatch); PUB.FAKE_FAULTS["instagram"] = {"fail": True}
    r = _short(monkeypatch, setting, "SHREL14"); sid = "SHREL14"
    assert r["status"] == "POSTED" and _recs(sid)["instagram"]["state"] == REL.RETRY and _recs(sid)["youtube"]["state"] == REL.DONE and not _led(sid) and not _row(sid)["ig"]
    assert REL.settle(NOW + H) == [sid] and _recs(sid)["instagram"]["state"] == REL.RETRY and int(float(_recs(sid)["instagram"]["tries"])) == 2
    assert REL.settle(NOW + 2 * H) == [sid] and _recs(sid)["instagram"]["state"] == REL.FAILED          # RELEASE_TRIES_MAX (3): it stops trying
    assert n == {"youtube": 1, "instagram": 6, "facebook": 1}                                            # each of the three tries: with the cover image, then once on the promise frame
    led = _led(sid); assert led[0]["status"] == "FAIL" and "Instagram Reels: never went up (try 3" in led[0]["evidence"] and REL.settle(NOW + 3 * H) == [] and n["instagram"] == 6
    PUB.FAKE_FAULTS["instagram"] = {"fail": True}; _bench("What if rain fell upward?")
    r2 = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL15"); assert r2["ok"] and _recs("SHREL15")["instagram"]["state"] == REL.RETRY
    PUB.FAKE_FAULTS.clear(); assert REL.settle(NOW + 49 * H) == ["SHREL15"]                              # the platform is back before the limit
    assert _recs("SHREL15")["instagram"]["state"] == REL.DONE and _row("SHREL15")["ig"] == "FAKE_IG_SHREL15" and n == {"youtube": 2, "instagram": 9, "facebook": 2} and _led("SHREL15")[0]["status"] == "PASS"

def test_a_youtube_upload_that_fails_leaves_the_short_made_and_waiting_not_posted(monkeypatch, setting):
    PUB.FAKE_FAULTS["youtube"] = {"fail": True}
    r = _short(monkeypatch, setting, "SHREL16"); row = _row("SHREL16")
    assert r["ok"] and SH._made(row) and row["status"].startswith("UPLOAD_WAITING (try 1") and not row["yt_id"] and LAD.row("SHREL16")["state"] == "MADE"
    assert _recs("SHREL16")["youtube"]["state"] == REL.RETRY and _recs("SHREL16")["instagram"]["state"] == REL.DONE      # the other platforms have it
    PUB.FAKE_FAULTS.clear(); assert REL.settle(NOW + H) == ["SHREL16"] and _row("SHREL16")["status"] == "POSTED" and LAD.row("SHREL16")["posted"] == core.iso(NOW + H)

# ------------------------------------------------------------------ 11. the owner's Approve: the same run, the Short's own words
def test_an_approved_short_goes_out_through_publishings_run_under_its_own_words(monkeypatch, setting):
    n = _count(monkeypatch)
    r = _short(monkeypatch, setting, "SHREL17", review="3"); sid = "SHREL17"
    assert r["status"] == "AWAITING_APPROVAL" and r["file"].startswith("drive:") and SH._made(_row(sid)) and not REL.records(sid) and n["youtube"] == 0
    assert REL.settle(NOW + H) == [] and n["youtube"] == 0 and not REL.records(sid)                      # a Short that waits for his Approve is never touched by the pass
    assert any(a.get("kind") == "special_review" and f"SPECIAL APPROVE {sid}" in str(a) for a in core.store().rows("Owner_Actions"))
    assert SP.approve(sid) == f"posted {sid}" and n == {"youtube": 1, "instagram": 1, "facebook": 1}
    row = _row(sid); d = _sent(sid, "youtube")["snippet"]["description"]
    assert row["status"] == "POSTED" and not [w for w in ("subscribe", "tuesday", "reality on trial", "jury") if w in d.lower()], d      # before: the special reels' text - a courtroom, a cadence, an ask
    assert d.startswith(row["script"].splitlines()[0][:20]) and _runs(sid)[-2:] == [("D9", "short_publish", "ok"), ("D8", "release_gate", "ok")] and _led(sid)[0]["status"] == "PASS"
    assert SP.approve("SHNOPE") == "SHNOPE not found"

def test_with_the_release_sheet_switched_off_the_old_single_path_runs_and_the_check_does_not_apply(monkeypatch, setting):
    setting("RELEASE_SHEET_ON", "FALSE"); seen = []
    real = SP._publish; monkeypatch.setattr(SP, "_publish", lambda path, title, ep, desc=None: (seen.append(desc), real(path, title, ep, desc=desc))[1])
    r = _short(monkeypatch, setting, "SHREL18"); assert r["status"] == "POSTED" and SH._made(_row("SHREL18")) and not REL.records("SHREL18") and not _led("SHREL18")
    assert REL.settle(NOW + H) == [] and CON.p_release_sheet({"release": {"id": "SHREL18"}})[0] == CON.NA and LAD.row("SHREL18")["state"] == "POSTED"
    setting("SHORTS_REVIEW_FIRST_N", "9"); _bench("What if rain fell upward?"); r2 = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL19"); assert r2["status"] == "AWAITING_APPROVAL"
    assert SP.approve("SHREL19").startswith("posted") and seen[-1] and "subscribe" not in seen[-1].lower() and seen[-1].startswith(_row("SHREL19")["script"].splitlines()[0][:20])      # even the old path now posts an approved Short under its own words

def test_an_approved_short_waits_when_uploads_are_closed_and_the_real_tick_sends_it(monkeypatch, setting):
    """The hook in the tick is proven by running the real tick job, not by reading its name."""
    n = _count(monkeypatch)
    r = _short(monkeypatch, setting, "SHREL29", review="3", closed=True); sid = "SHREL29"
    said = SP.approve(sid); assert "is approved and waits" in said and n["youtube"] == 0 and _row(sid)["status"].startswith("UPLOAD_WAITING")
    assert _recs(sid)["youtube"]["state"] == REL.QUEUED                                                  # approved = handed to Publishing: on record, so no tick forgets it
    MG.tick(); assert n["youtube"] == 0 and not _row(sid)["yt_id"]                                       # uploads are still closed
    assert LA.upload_check() == "passed"; MG.tick()
    assert n == {"youtube": 1, "instagram": 1, "facebook": 1} and _row(sid)["status"] == "POSTED" and _led(sid)[0]["status"] == "PASS"
    MG.tick(); assert n["youtube"] == 1 and len(_led(sid)) == 1                                          # and the next tick finds nothing left to do

def test_a_platform_that_already_has_the_short_is_only_read_never_posted_twice(monkeypatch, setting):
    """The guard, tried with the case built to defeat it: every sender is called again with a record that already carries the platform's id."""
    r = _short(monkeypatch, setting, "SHREL30"); row = _row("SHREL30"); rec = _recs("SHREL30"); n = _count(monkeypatch)
    path, digest = REL.master(row, r["path"]); tx = REL.texts(row)
    for p in REL.PLATFORMS:
        nid, sent, got, rc = REL._SEND[p](row, path, digest, "", tx, rec[p], NOW + H)
        assert nid == rec[p]["native_id"] and got and all(v[0] in REL.GOOD for v in rc.values()), (p, rc)
    assert n == {"youtube": 0, "instagram": 0, "facebook": 0}
    for p in REL.PLATFORMS: REL._SEND[p](row, path, digest, "", tx, dict(rec[p], native_id=""), NOW + H)
    assert n == {"youtube": 1, "instagram": 1, "facebook": 1}                                            # (without an id it IS an upload: the counter can see one)

def test_a_job_cut_off_right_after_an_upload_never_uploads_the_short_a_second_time(monkeypatch, setting):
    """The id a platform returns is on record the moment it returns - before the read-back, the wait for processing and the playlist."""
    n = _count(monkeypatch); real = PUB.yt_read; calls = []
    monkeypatch.setattr(PUB, "yt_read", lambda vid: (_ for _ in ()).throw(RuntimeError("the job was cut off")) if not calls.append(1) and len(calls) == 1 else real(vid))
    r = _short(monkeypatch, setting, "SHREL31"); y = _recs("SHREL31")["youtube"]
    assert y["native_id"] == "FAKE_SHREL31.mp4" and y["state"] == REL.RETRY and y["sha"] == _row("SHREL31")["sha"] and json.loads(y["sent"])["snippet"]["title"]      # the id is there although everything after the upload was lost
    assert _row("SHREL31")["yt_id"] == y["native_id"] and r["status"] == "POSTED" and LAD.row("SHREL31")["state"] == "POSTED" and not _led("SHREL31")
    assert REL.settle(NOW + H) == ["SHREL31"] and n == {"youtube": 1, "instagram": 1, "facebook": 1}    # the next pass finishes the release; it does not post again
    assert _recs("SHREL31")["youtube"]["state"] == REL.DONE and _led("SHREL31")[0]["status"] == "PASS"

def test_a_reel_that_instagram_refuses_with_its_cover_image_goes_up_on_the_promise_frame(monkeypatch, setting):
    """Instagram must fetch a cover image from a link; when that fails on Meta's side the Reel is not lost for the sake of a cover."""
    n = _count(monkeypatch); PUB.FAKE_FAULTS["instagram"] = {"fail_cover": True}
    _short(monkeypatch, setting, "SHREL32"); s = _sent("SHREL32", "instagram"); rec = _recs("SHREL32")["instagram"]
    assert n["instagram"] == 2 and rec["state"] == REL.DONE and int(float(rec["tries"])) == 1 and rec["native_id"] == "FAKE_IG_SHREL32"      # one try: with the cover, then without
    assert "cover_url" not in s and s["thumb_offset"] == str(REL.PROMISE_FRAME_MS) and "promise frame" in _rc("SHREL32", "instagram", "cover")[1] and _led("SHREL32")[0]["status"] == "PASS"
    assert json.loads(s["trial_params"])["graduation_strategy"] == "SS_PERFORMANCE" and s["audio_name"] == "Reality Engine"      # everything else of the Reel is as it was

# ------------------------------------------------------------------ 12. a file that does not fit a platform, a platform that is not connected, the switches
def test_a_file_over_90_seconds_is_not_sent_to_facebook_and_never_cut_and_a_missing_meta_connection_is_no_fault(monkeypatch, setting):
    n = _count(monkeypatch); real = REL.probe; monkeypatch.setattr(REL, "probe", lambda p: dict(real(p), sec=95.0))
    _short(monkeypatch, setting, "SHREL20"); rec = _recs("SHREL20")
    assert rec["facebook"]["state"] == REL.SKIPPED and "3 to 90 s" in rec["facebook"]["note"] and n == {"youtube": 1, "instagram": 1, "facebook": 0} and not _row("SHREL20")["fb"]
    ev = _led("SHREL20")[0]; assert ev["status"] == "PASS" and "Facebook Reels: not sent (95 s is outside the 3 to 90 s" in ev["evidence"]
    monkeypatch.setattr(REL, "probe", real); setting("META_ON", "FALSE"); _bench("What if rain fell upward?")
    r = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL21"); rec = _recs("SHREL21")
    assert r["status"] == "POSTED" and rec["instagram"]["state"] == REL.OFF and rec["facebook"]["state"] == REL.OFF and n == {"youtube": 2, "instagram": 1, "facebook": 0}
    ev = _led("SHREL21")[0]; assert ev["status"] == "PASS" and ev["evidence"].count("not connected") == 2

def test_a_file_that_youtube_would_not_file_as_a_short_is_not_sent_and_the_check_fails(monkeypatch, setting):
    real = REL.probe; monkeypatch.setattr(REL, "probe", lambda p: dict(real(p), sec=200.0))
    r = _short(monkeypatch, setting, "SHREL22"); rec = _recs("SHREL22")
    assert rec["youtube"]["state"] == REL.SKIPPED and not _row("SHREL22")["yt_id"] and r["status"].startswith("UPLOAD_WAITING") and _led("SHREL22")[0]["status"] == "FAIL"

def test_the_trial_reel_and_the_audio_name_are_switches_with_a_receipt_either_way(monkeypatch, setting):
    setting("IG_TRIAL_REELS_ON", "FALSE"); setting("IG_AUDIO_NAME", "")
    _short(monkeypatch, setting, "SHREL23"); s = _sent("SHREL23", "instagram")
    assert "trial_params" not in s and s["share_to_feed"] == "true" and "audio_name" not in s          # a normal Reel, shown in the feed too
    assert _rc("SHREL23", "instagram", "trial")[0] == REL.OFF and _rc("SHREL23", "instagram", "audio")[0] == REL.OFF and _led("SHREL23")[0]["status"] == "PASS"

def test_when_the_cover_link_cannot_be_opened_instagram_takes_the_promise_frame(monkeypatch, setting):
    _quiet(monkeypatch); real = PUB.drive_upload
    monkeypatch.setattr(PUB, "drive_upload", lambda path, name, public=False, parent=None: (_ for _ in ()).throw(RuntimeError("no public links today")) if public else real(path, name, public, parent))
    _short(monkeypatch, setting, "SHREL24"); s = _sent("SHREL24", "instagram")
    assert "cover_url" not in s and s["thumb_offset"] == str(REL.PROMISE_FRAME_MS) and "promise frame" in _rc("SHREL24", "instagram", "cover")[1] and _led("SHREL24")[0]["status"] == "PASS"

# ------------------------------------------------------------------ 13. what counts as a MADE Short: a field, never a status text
def test_a_short_that_was_made_counts_as_made_whatever_its_status_says(setting):
    """Before, 'made' was read out of the status text - and the upload path's 'HELD (uploads not confirmed open)' once read like a refusal at the
    short gate: a Short paid in full was 'not made', the cadence started another a day later and its topic could be made again."""
    _bench("What if the Moon left tonight?", "What if rain fell upward?"); st = core.store()
    for status in ("UPLOAD_WAITING (uploads are not confirmed open)", "HELD (uploads not confirmed open)", "AWAITING_APPROVAL", "FAILED on a platform", "HELD (short_plain)", "anything at all", ""):
        r = {"status": status, "made": core.iso(NOW)}; assert SH._made(r) and not SH._held(r) and not SH._failed(r) and not SH._unmade(r), status      # the field decides
        assert SH._unmade({"status": status, "made": ""}), status                                        # no field, not made - whatever the status says
    assert SH._held({"status": "HELD (short_upload_x)", "made": ""}) and SH._failed({"status": "FAILED (x)", "made": ""}) and not SH._held({"status": "POSTED", "made": ""}) and not SH._failed({"status": "POSTED", "made": ""})
    assert SH._made({"status": "POSTED"}) and SH._made({"status": "HELD (uploads not confirmed open)"}) is False and not SH._made({"status": "FAILED (x)"})      # a Sheet without the column yet: the old, safe reading
    assert not hasattr(SH, "UPLOAD_HOLD")                                                                # the text match is gone
    st.append("Specials", [{"ts": core.iso(NOW), "id": "SHU1", "kind": "short", "format": "S1", "status": "UPLOAD_WAITING (uploads are not confirmed open)", "made": core.iso(NOW),
                            "premise": "What if the Moon left tonight?", "hook": "you_pov", "script": "A line."}])
    ok, why = SH.cadence(NOW + 25 * H); assert not ok and "48 hours apart" in why and SH.cadence(NOW + 48 * H)[0]      # it counts as made: the next comes 48 hours after it, not a day after it
    assert [h["id"] for h in SH.history()] == ["SHU1"] and SH._spent_premises() == ({"what if the moon left tonight?"}, set()) and SH.pick_topic()["premise"] == "What if rain fell upward?"

def test_a_failure_after_the_short_was_made_never_makes_a_second_row_and_the_pass_takes_it_up(monkeypatch, setting):
    n = _count(monkeypatch); real = REL.short; monkeypatch.setattr(REL, "short", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("the job was cut off")))
    r = _short(monkeypatch, setting, "SHREL25"); rows = [x for x in core.store().rows("Specials") if x["id"] == "SHREL25"]
    assert r["ok"] and len(rows) == 1 and SH._made(rows[0]) and rows[0]["status"].startswith("UPLOAD_WAITING (the hand-over failed") and LAD.row("SHREL25")["state"] == "MADE"
    assert _recs("SHREL25")["youtube"]["state"] == REL.QUEUED                                            # it was handed to Publishing BEFORE the call that died
    monkeypatch.setattr(REL, "short", real); assert REL.settle(NOW + H) == ["SHREL25"] and _row("SHREL25")["status"] == "POSTED" and n["youtube"] == 1
    monkeypatch.setattr(LAD, "enter", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("the Sheet hiccuped"))); _bench("What if rain fell upward?")
    r2 = SH.run(force=True, now=NOW + 48 * H, episode_id="SHREL26"); rows = [x for x in core.store().rows("Specials") if x["id"] == "SHREL26"]
    assert r2["ok"] and len(rows) == 1 and SH._made(rows[0]) and not rows[0]["status"].startswith("FAILED")      # a crash after 'made' is no crashed Short: one row, and it is made

def test_the_one_time_move_gives_older_shorts_the_field_and_never_runs_twice(setting):
    st = core.store(); t = core.iso(NOW)
    st.append("Specials", [{"ts": t, "id": "SHA", "kind": "short", "status": "POSTED"}, {"ts": t, "id": "SHB", "kind": "short", "status": "HELD (short_plain)"},
                           {"ts": t, "id": "SHC", "kind": "short", "status": "HELD (uploads not confirmed open)"}, {"ts": t, "id": "SHD", "kind": "short", "status": "FAILED (x)"},
                           {"ts": t, "id": "SHE", "kind": "short", "status": "AWAITING_APPROVAL"}, {"ts": t, "id": "SPX", "kind": "special", "status": "POSTED"},
                           {"ts": t, "id": "SHF", "kind": "short", "status": "POSTED", "made": "2026-12-01T00:00:00Z"}])
    setting("V12V2CB2_MOVE_DONE", ""); assert MG.v12v2cb2_upgrade(st) == ["SHA", "SHC", "SHE"]
    got = {r["id"]: r["made"] for r in st.rows("Specials")}; assert got == {"SHA": t, "SHB": "", "SHC": t, "SHD": "", "SHE": t, "SPX": "", "SHF": "2026-12-01T00:00:00Z"}
    st.append("Specials", [{"ts": t, "id": "SHG", "kind": "short", "status": "POSTED"}]); assert MG.v12v2cb2_upgrade(st) == [] and core.S("V12V2CB2_MOVE_DONE")      # never twice
    assert open(MG.__file__, encoding="utf-8").read().count("try: v12v2cb2_upgrade(st)") == 2           # both setup paths call it

# ------------------------------------------------------------------ 14. the ladder: a Short that never went public leaves with the window
def test_a_short_that_is_made_and_never_public_leaves_the_ladder_with_the_window(monkeypatch, setting):
    r = _short(monkeypatch, setting, "SHREL27", review="3"); assert LAD.row("SHREL27")["state"] == "MADE" and LAD.row("SHREL27")["footage"]
    assert LAD.read(NOW + dt.timedelta(days=30)) == 0 and LAD.row("SHREL27")["state"] == "MADE"
    assert LAD.read(NOW + dt.timedelta(days=31)) == 1; lr = LAD.row("SHREL27")
    assert lr["state"] == "PASSED" and "never public" in lr["note"] and not lr["footage"] and not os.path.exists(os.path.join(PUB._fake_drive(), "SHREL27_footage.zip"))
    assert LAD.went_public("SHREL27", "y1", NOW) is False                                                # past is past: nothing brings it back
    st = core.store(); st.append("Ladder", [{"id": "SHM", "topic": "SHM", "state": "MADE"}])
    assert LAD.went_public("SHM", "", NOW) is False and LAD.went_public("SHM", "yX", NOW) is True and LAD.row("SHM")["posted"] == core.iso(NOW) and LAD.went_public("SHM", "yY", NOW + H) is False

# ------------------------------------------------------------------ 15. the check itself, and the wiring
def test_check_release_sheet_reads_the_record_and_cannot_pass_without_one(monkeypatch, setting):
    assert CON.p_release_sheet({})[0] == CON.FAIL and "nothing reached" in CON.p_release_sheet({})[1]
    s, ev = CON.p_release_sheet({"release": {"id": "SHNONE"}}); assert s == CON.FAIL and "no release record for YouTube" in ev
    _short(monkeypatch, setting, "SHREL28"); assert CON.p_release_sheet({"release": {"id": "SHREL28"}})[0] == CON.PASS
    rec = _recs("SHREL28")["instagram"]["receipts"]; del rec["trial"]
    core.store().update_where("Release_Sheet", {"id": "SHREL28", "platform": "instagram"}, {"receipts": json.dumps(rec)})
    s, ev = CON.p_release_sheet({"release": {"id": "SHREL28"}}); assert s == CON.FAIL and "Instagram Reels: no receipt for trial" in ev      # a row without a receipt is not a row that passed
    core.store().update_where("Release_Sheet", {"id": "SHREL28", "platform": "instagram"}, {"receipts": json.dumps(dict(rec, trial=[REL.WAITING, "x"]))})
    assert CON.p_release_sheet({"release": {"id": "SHREL28"}})[0] == CON.FAIL                            # a row that still waits has not passed either
    core.store().update_where("Release_Sheet", {"id": "SHREL28", "platform": "instagram"}, {"receipts": json.dumps(dict(rec, trial=[REL.SENT, "x"])), "state": REL.OFF})
    s, ev = CON.p_release_sheet({"release": {"id": "SHREL28"}}); assert s == CON.PASS and "Instagram Reels: not connected" in ev      # 'not connected' excuses Instagram ...
    for stt in (REL.OFF, REL.QUEUED, REL.RETRY, REL.FAILED, REL.SKIPPED):
        core.store().update_where("Release_Sheet", {"id": "SHREL28", "platform": "youtube"}, {"state": stt, "native_id": ""})
        s, ev = CON.p_release_sheet({"release": {"id": "SHREL28"}}); assert s == CON.FAIL and "YouTube Shorts: never went up" in ev, stt      # ... and never YouTube: a Short that is not on YouTube is not released
    core.store().update_where("Release_Sheet", {"id": "SHREL28", "platform": "youtube"}, {"state": REL.FAILED, "native_id": "FAKE_SHREL28.mp4"})
    s, ev = CON.p_release_sheet({"release": {"id": "SHREL28"}}); assert s == CON.FAIL and "YouTube Shorts: is up, but its release could not be finished" in ev

def test_the_release_is_wired_into_the_contract_the_registry_the_levers_and_the_tick():
    from whatifs.org import registry as REG, levers as LV, rnd as RND
    import tools.repair as REP
    stage = {f[0]: f[1] for f in CON.FEATURES}; assert stage["release_sheet"] == "release" and REG.check_owner("release_sheet") == "D9"
    assert "release_sheet" not in RND.ORG_CHECKS and "release_sheet" in RND.metrics() and RND.SHOW_CHECKS == 49      # a promise about the show: researchable
    assert ("whatifs/release.py", "short_publish") in REG.ENTRY["D9"] and ("whatifs/release.py", "release_gate") in REG.ENTRY["D8"] and REG.entry_issues() == [] and REG.data_issues() == []
    assert REG.EPISODE_RUNS["release"] == (("D9", "short_publish"),) and REG.GATE_RUNS["release"] == ("D8", "release_gate") and "whatifs/release.py" in REG.DEPTS["D9"]["wraps"]
    for k in ("IG_TRIAL_REELS_ON", "SHORT_THUMB_ON"):
        assert REG.may_change("D9", k) and LV.LEVERS[k]["kind"] == "bool" and LV.LEVERS[k]["checks"] == ("release_sheet",) and not LV.LEVERS[k]["owner"]
    assert "whatifs/release.py" in REP.PROTECTED and core.TABS["Release_Sheet"][:6] == ["ts", "id", "platform", "kind", "native_id", "state"] and core.TABS["Specials"][-3:] == ["made", "sha", "cover"]
    for k in ("RELEASE_SHEET_ON", "IG_TRIAL_REELS_ON", "IG_AUDIO_NAME", "SHORT_THUMB_ON", "SHORT_THUMB_WAIT_S", "SHORT_HASHTAGS", "RELEASE_TRIES_MAX", "RELEASE_SETTLE_H"): assert k in core.DEFAULTS, k
    src = open(MG.__file__, encoding="utf-8").read(); assert "RELW.settle()" in src                     # the tick finishes what waits
    sh = open(SH.__file__, encoding="utf-8").read(); assert "SP._publish(out, sc[\"title\"], ep, desc=description(sc))" in sh and sh.count("SP._publish(") == 1      # the old path only behind the switch
    assert "REL.approved(sid)" in open(SP.__file__, encoding="utf-8").read()
