"""tools/rehearsal.py v8.0 - full offline run: setup -> voices -> tick -> produce -> release x2 -> trends -> learn -> brief.
Fake models, fake images, synthetic voice. Proves every stage connects. Costs nothing. Used by CI and the repair bot."""
import os, json, shutil, datetime as dt
import numpy as np
from whatifs import checkpoint as CK

class ToneVoice:
    SR = 24000
    def __init__(self): self.packs = {"NARRATOR": 150}; self.pack = 150
    def register_speaker(self, speaker, blend): self.packs[str(speaker).upper()] = {"DIRECTOR": 110, "SKEPTIC": 210}.get(str(speaker).upper(), 150)    # two different pitches stand in for two voices
    def synth(self, text, speed, speaker="NARRATOR"):
        f0 = self.packs.get(str(speaker).upper(), 150)
        n = int(max(0.4, len(text) * 0.058 / speed) * self.SR); t = np.arange(n) / self.SR
        a = (0.25 * np.sin(2 * np.pi * f0 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.3 * t))).astype(np.float32)
        a = np.concatenate([np.zeros(1800, np.float32), a, np.zeros(2400, np.float32)])
        ws = text.split(); d = (n / self.SR) / max(1, len(ws))
        return a, [{"w": x, "s": 0.075 + i * d, "e": 0.075 + (i + 1) * d} for i, x in enumerate(ws)]

from whatifs.core import S, TABS

def run():
    assert os.environ.get("WI_FAKE") == "1", "rehearsal needs WI_FAKE=1"
    work = os.environ.get("WI_WORK", "rh"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work, exist_ok=True)
    import whatifs.voice as V
    real = V.KokoroBackend
    V.KokoroBackend = lambda blend: ToneVoice()
    try:
        from whatifs.core import store, set_setting, now_utc, flush_costs, iso as iso_now
        def st_rows(t): flush_costs(); return store().rows(t)
        from whatifs import manage as MG, episode as EP
        from whatifs.voice_lab import main as voices
        MG.setup(); print("setup ok")
        voices(backend=ToneVoice()); print("voices ok")
        a = MG.tick()["action"]; assert a == "waiting_for_voice_pick", a          # v7.2: nothing is made before the voice pick
        set_setting("VOICE", "C")
        a = MG.tick()["action"]; assert a in ("idle", "produce"), a
        slot = (now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = EP.produce(slot); print("produce ok", json.dumps(r, default=str)[:400])
        assert os.path.exists(r["master"]) and len(r["reels"]) >= 1, "missing outputs"
        # v7.2 independent checks on the real rendered files
        from whatifs import qc as QC
        from whatifs.render import probe_dur
        ok, info = QC.check_video(r["master"], probe_dur(r["master"])); assert ok, info
        for rf in r["reels"]:
            ok, info = QC.check_video(rf, probe_dur(rf), vertical=True); assert ok, (rf, info)
        assert probe_dur(r["master"]) >= 20, "runtime floor not enforced"
        imgs = [c for c in st_rows("Cost_Log") if c["item"] == "image"]
        print("rehearsal images logged:", len(imgs))
        st = store(); e = st.rows("Episodes")[-1]; assert e["status"] == "SCHEDULED", e
        from whatifs.core import S as _S89; np89 = _S89("NEXT_PREMISE")      # v8.9: the scheduled video leaves its tease for the next episode (v8.9.1: only a saved plan uses it up)
        # v7.4 checks: research brief, ten opening hooks, reviewable cut map
        d74 = os.path.dirname(r["master"])
        hk = json.load(open(os.path.join(d74, "hooks.json"))); assert len(hk["candidates"]) == 10 and all(c["words"] < 10 for c in hk["candidates"]), "hook rules"
        cm = json.load(open(os.path.join(d74, "cutmap.json"))); assert cm["apply_policy"].startswith("REVIEW ONLY"), "cut map must stay review-only"
        assert st.rows("Research_Brief") and st.rows("Hook_Candidates"), "v7.4 reports missing from the store"
        print("v7.4 checks ok")
        # v8.1 checks: two recurring roles reach the timeline with their own voices, no label is ever spoken, the format is code-checked
        import glob
        from whatifs import format_engine as FE
        tl81 = json.load(open(glob.glob(os.path.join(d74, "voice*timeline*.json"))[0])); who = {u.get("speaker") for u in tl81["units"]}
        assert {"DIRECTOR", "SKEPTIC"} <= who, f"both roles must speak: {who}"
        assert not tl81.get("voice_fallback"), "a character voice fell back to the narrator"
        assert not any("[" in u["text"] or u["text"].upper().startswith(("DIRECTOR", "SKEPTIC")) for u in tl81["units"]), "a speaker label was spoken"
        assert FE.check_script(open(os.path.join(d74, "captions.srt")).read() and "\n".join(f"[{u['speaker']}] {u['text']}" for u in tl81["units"] if u["speaker"] != "NARRATOR"))["ok"]
        print("v8.1 checks ok")
        # v8.2 checks: final QC passed with its sync numbers, reactions were placed and recorded, checkpoints were removed after scheduling
        st82 = store(); ep82 = [e for e in st82.rows("Episodes") if e.get("yt_id")][0]
        assert ep82["status"] in ("SCHEDULED", "LIVE1", "LIVE") and not CK.has(ep82), ep82["status"]
        assert st82.rows("Reaction_Map"), "no reaction moment was recorded"
        from whatifs.core import flush_log; flush_log(); runlog = " ".join(str(r.get("message", "")) for r in st82.rows("Run_Log"))
        assert "QC long video: PASS" in runlog and "audio_offsets" in runlog, "final QC did not run or did not pass"
        print("v8.2 checks ok")
        # v8.3 checks: no third voice, all three audience asks spoken, the segments were cleaned up, the first line is the Director's, the fact check ran
        from whatifs import cta as CTA83
        assert "NARRATOR" not in who, f"a third voice was used: {who}"
        asks = {CTA83.kind_of_text(u["text"]) for u in tl81["units"]} - {None}
        assert asks == {"like", "subscribe", "share"}, f"audience asks missing or doubled: {asks}"
        assert tl81["units"][0]["speaker"] == "DIRECTOR", "the opening line must be the Director's"
        assert "fact check" in runlog, "the fact check did not run"
        assert not glob.glob(os.path.join(d74, "seg*_*.mp4")), "big intermediate segments were not removed"
        print("v8.3 checks ok")
        # v8.0 checks: the optional table read (off by default) - one room run with it on, using fake models
        from whatifs import room as ROOM, tableread as TR
        from whatifs.sampler import draw as DRAW
        assert TR.active_arm("ANY", "off")[0] == "off" and e.get("draw_json"), "table read must be off by default"
        set_setting("TABLE_READ_MODE", "on")
        rr = ROOM.run_room(DRAW("EPTABLE", "collective"), "EPTABLE")
        assert rr["table_read"]["arm"] == "on" and rr["director_notes"], "table read did not run"
        assert {x["kind"] for x in st.rows("Table_Read") if x["episode_id"] == "EPTABLE"} >= {"objection", "director_note"}, "Table_Read rows missing"
        set_setting("TABLE_READ_MODE", "off")
        assert "NOT ENOUGH DATA" in TR.abtest_report()["verdict"], "abtest must refuse to conclude without data"
        print("v8.0 checks ok")
        past = (now_utc() - dt.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        st.update("Episodes", "episode_id", e["episode_id"], {"slot_et": past})
        a = MG.tick(); assert a["action"] == "release1", a; MG.release(e["episode_id"], "release1")
        a = MG.tick(); assert a["action"] == "release2", a; MG.release(e["episode_id"], "release2")
        assert st.rows("Episodes")[-1]["status"] == "LIVE"
        # v8.5 checks: 4 bridge Shorts were made and passed QC, the B thumbnail and runner-up title were saved, reel 3 goes out the next day exactly once
        assert len(r["reels"]) == 4, f"expected 4 Shorts, got {len(r['reels'])}"
        rel85 = json.load(open(os.path.join(d74, "release.json")))
        assert len(rel85["reels"]) == 4 and rel85.get("title_b") and rel85.get("thumb_b") and os.path.exists(os.path.join(d74, "thumb_b.jpg")), "packaging rescue files missing"
        assert json.loads(st.rows("Episodes")[-1]["draw_json"]).get("reel_style") == "bridge"
        day2 = (now_utc() - dt.timedelta(hours=27)).strftime("%Y-%m-%dT%H:%M:%SZ")
        st.update("Episodes", "episode_id", e["episode_id"], {"slot_et": day2, "assets": {"reel2.mp4": "r2", "reel3.mp4": "r3", "release.json": "rj"}})
        a = MG.tick(); assert a["action"] == "release3", a; MG.release(e["episode_id"], "release3")
        e85 = next(x for x in st.rows("Episodes") if x["episode_id"] == e["episode_id"])
        assert e85["reel3_yt"].startswith("FAKE_") and e85["status"] == "LIVE", e85
        a = MG.tick(); assert a.get("action") != "release3", "reel 3 must never be posted twice"
        print("v8.5 checks ok")
        MG.trend_scout(); print("trends ok")
        old = (now_utc() - dt.timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        st.update("Episodes", "episode_id", e["episode_id"], {"slot_et": old})
        MG.learn(); assert st.rows("Analytics"), "no analytics"; print("learn ok")
        assert "too old" in str(next(x for x in st.rows("Episodes") if x["episode_id"] == e["episode_id"])["pkg_check"]), "packaging check did not run"
        # v8.6 checks: analytics carry a diagnosis and a data note, the published title passes the click checks, lessons are routed, the tabs exist
        from whatifs import growth as GR86
        a86 = [x for x in st.rows("Analytics") if x["episode_id"] == e["episode_id"]][-1]
        assert a86.get("diagnosis") and a86.get("data_note") == "ok", a86
        e86 = next(x for x in st.rows("Episodes") if x["episode_id"] == e["episode_id"])
        assert not [i for i in GR86.title_issues(e86["title"]) if i.startswith(("long", "short"))], e86["title"]
        assert "Strategy_Log" in TABS and isinstance(st.rows("Strategy_Log"), list)
        print("v8.6 checks ok")
        # v8.7 checks: packaging-first promise, rhythm plan, retention gate record, beat map, sound textures planned, playbook seeded + weekly research vetted,
        # the maintenance reserve is inside the cap, the related-video link never points at an unreleased video
        from whatifs import governor as G87, growth as GR87
        d87 = json.loads(next(x for x in st.rows("Episodes") if x["episode_id"] == e["episode_id"])["draw_json"])
        assert (d87.get("promise") or {}).get("title") and (d87.get("rhythm_plan") or {}).get("opener") and (d87.get("retention_check") or {}).get("checked"), "v8.7 plan fields missing"
        assert d87.get("beat_map") and d87.get("duration_sec") and d87["strategies"].get("rhythm") and d87["strategies"].get("sound"), "beat map / new strategies missing"
        sh87 = json.load(open(os.path.join(d74, "plan.json")))["shots"]
        assert sum(1 for s in sh87 if s.get("sound") not in (None, "none")) >= 2, "no sound texture was planned"
        pb87 = st.rows("Playbook")
        assert sum(1 for r in pb87 if r.get("added") == "seed") >= 7 and any(r.get("status") == "trial" for r in pb87), "playbook not seeded or research not vetted"
        assert not any("sub4sub" in r.get("rule", "") or not r.get("source", "").startswith("http") for r in pb87), "an unsourced or platform-gaming rule got in"
        assert abs(G87.production_room_inr() - (G87.remaining_inr() - 100)) < 1e-6, "maintenance reserve must sit inside the cap"
        assert GR87.related_episode([{"episode_id": "X", "status": "SCHEDULED", "yt_id": "abc"}]) is None, "a scheduled video must never be linked"
        print("v8.7 checks ok")
        # v8.9 checks: style lock on every paid shot prompt, a guest chosen, the next-episode tease set and spoken, the plan check ran
        lock89 = S("STYLE_LOCK")
        assert all(lock89 in (s_.get("prompt") or "") for s_ in sh87 if s_.get("type") in ("still", "living", "kling")), "style lock missing on a paid shot"
        assert d87.get("guest") and d87.get("tier") == "public", "guest / tier missing from the draw"
        assert (d87.get("next_tease") or {}).get("line") and np89 and json.loads(np89).get("premise") == d87["next_tease"]["premise"], "next-episode tease not set when the video was scheduled"
        assert rr["spine"].get("teased_premise") == json.loads(np89)["premise"], "the next room (EPTABLE) must be handed the teased premise"
        assert S("NEXT_PREMISE") == np89, "v8.9.1: a room alone (no saved plan) must NOT use up the teased premise"
        cams = [x.get("camera") for x in sh87 if x.get("camera")]
        from whatifs.render import CAMERA_MOVES as _CM
        assert cams and all(c in _CM for c in cams) and "spin_wildly" not in cams, "Director camera suggestions must be validated (only library moves kept)"
        print("v8.9 checks ok")
        MG.money_check(); MG.monthly_brief(); print("brief ok")
        # v7.3 checks: Revenue_Log months/amounts, pause hold + resume, KILL, stuck release never blocks, release is idempotent
        from whatifs.governor import month_key, money_num
        for raw, want in (("2027-03", "2027-03"), ("2027-03-01", "2027-03"), ("3/1/2027", "2027-03"), ("01/03/2027", "2027-03"), ("Mar 2027", "2027-03"), ("46447", "2027-03")):
            assert month_key(raw) == want, (raw, month_key(raw))
        assert money_num("₹ 1,234.50") == 1234.5 and money_num("") == 0
        def row(i): return next(x for x in st.rows("Episodes") if x["episode_id"] == i)
        fut = (now_utc() + dt.timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
        st.append("Episodes", [{"episode_id": "EPHOLD", "slot_et": fut, "status": "SCHEDULED", "yt_id": "FAKE_HOLD", "updated": iso_now()}])
        set_setting("PAUSED", "TRUE"); assert MG.tick()["action"] == "paused"
        assert row("EPHOLD")["status"] == "HELD", "pause did not hold the scheduled video"
        set_setting("PAUSED", "FALSE"); MG.tick()
        assert row("EPHOLD")["status"] == "SCHEDULED", "held video not re-scheduled"
        st.update("Episodes", "episode_id", "EPHOLD", {"kill": "KILL"}); set_setting("PAUSED", "TRUE"); MG.tick(); set_setting("PAUSED", "FALSE")
        assert row("EPHOLD")["status"] == "KILLED", "KILL ignored while paused"
        old2 = (now_utc() - dt.timedelta(hours=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        st.append("Episodes", [{"episode_id": "EPSTUCK", "slot_et": old2, "status": "LIVE1", "yt_id": "FAKE_STUCK", "updated": iso_now()}])
        a = MG.tick(); assert a.get("episode") != "EPSTUCK", a
        assert row("EPSTUCK")["status"] == "LIVE", "stuck release not closed"
        MG.release(e["episode_id"], "release1"); assert row(e["episode_id"])["status"] == "LIVE", "release1 ran twice"
        print("v7.3 checks ok")
        print("REHEARSAL: GREEN")
    finally:
        V.KokoroBackend = real

