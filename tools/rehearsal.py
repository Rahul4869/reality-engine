"""Full offline rehearsal: setup -> voices -> tick -> produce -> release -> trends -> learn -> brief with fake models, images and voice; proves every stage connects at zero cost. See docs/CURRENT/SYSTEM.md."""
import os, re, json, shutil, datetime as dt
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
        from whatifs import research as RS92                                  # v9.2: the research brief is a BACKGROUND job (learning / research workflow),
        RS92.save_brief(RS92.run_research()); print("research brief (background) ok")      # never made inside a preview or production
        voices(backend=ToneVoice()); print("voices ok")
        a = MG.tick()["action"]; assert a == "waiting_for_voice_pick", a          # v7.2: nothing is made before the voice pick
        set_setting("VOICE", "C")
        a = MG.tick()["action"]; assert a in ("idle", "produce"), a
        slot = (now_utc() + dt.timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        from whatifs.org import memos as OMEM4, execute as EXE4          # v12 B4: one decision of the organisation is carried from ticket to ledger proof inside the rehearsal
        tk4 = OMEM4.write({"type": "ticket", "from_dept": "C", "to_depts": ["D6"], "subject": "Rehearsal: serve Visual Production one new technique",
                           "body": {"lever_class": "A", "target": "palace:rehearsal-b4-knowledge-lever", "acceptance_test": "a later run of Visual Production is served the item", "rollback": "retire the item",
                                    "value": {"kind": "technique", "title": "Rehearsal item: keep the camera moving through the verdict", "departments": ["D6"], "stages": ["visual"], "topic_tags": ["camera"],
                                              "summary": "Rehearsal item of the Execution Engine: the camera keeps a slow move through the verdict line instead of a locked frame.",
                                              "evidence": [{"source": "tools/rehearsal.py", "date": now_utc().strftime("%Y-%m-%d"), "type": "build record", "finding": "written by the rehearsal to prove the engine end to end"}]}},
                           "done_when": "a later run of Visual Production was served the item"})
        OMEM4.write({"type": "decision_memo", "from_dept": "C", "to_depts": ["D6"], "subject": "Rehearsal decision: one knowledge lever for Visual Production",
                     "body": {"decision": "Serve Visual Production the rehearsal technique.", "why": "The rehearsal must prove that a decision becomes a verified change.", "memos_cited": [tk4["id"]],
                              "lever_class": "A", "tickets": [tk4["id"]], "owner_approval": False}})
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
        st = store(); e = st.rows("Episodes")[-1]
        if e["status"] == "AWAITING_APPROVAL":                 # v10.2: the first videos wait for the owner; the rehearsal plays the owner's Approve tap
            from whatifs import contract as CON
            assert any(r.get("kind") == "creative_review" for r in st.rows("Owner_Actions")), "review card missing"
            led = [r for r in st.rows("Feature_Ledger") if r.get("episode_id") == e["episode_id"]]
            assert led and not [r for r in led if r["status"] == "FAIL"], ("contract ledger", [r for r in led if r["status"] == "FAIL"])
            assert any(r["feature"] == "docs_current" and r["status"] == "PASS" for r in led), "truth hygiene check (docs_current) did not run"
            assert any(r["feature"] == "palace_health" and r["status"] == "PASS" for r in led), "Knowledge Palace check (palace_health) did not run"
            print("contract ledger:", len(led), "checks,", sum(1 for r in led if r["status"] == "PASS"), "pass; review card sent; approving as the owner")
            CON.approve(e["episode_id"]); e = st.rows("Episodes")[-1]
        assert e["status"] == "SCHEDULED", e
        from whatifs.org import palace as PAL                    # v12: the Knowledge Palace holds the founding knowledge, mirrors the show records and feeds a bounded playbook
        dly = PAL.daily(st); pal = PAL.rows(st); pb = PAL.playbook("D4", topic=e.get("premise", ""))
        assert len(pal) >= len(PAL.seed_items()[0]) > 50 and not PAL.seed_issues(), "Knowledge Palace not seeded"
        assert dly.get("canon") is not None and sum(1 for x in pal if x["kind"] == "world_canon") >= 4, ("world canon not mirrored", dly)
        assert pb["playbook_id"] and pb["tokens"] <= pb["cap"] and any(r.get("playbook_id") == pb["playbook_id"] for r in st.rows("Palace_Playbooks")), "writers' playbook out of bounds or not recorded"
        hp = PAL.health(st); assert hp["ok"], hp["problems"]
        print("knowledge palace:", len(pal), "items, version", hp["stats"]["version"], "; writers' playbook", pb["playbook_id"], pb["tokens"], "of", pb["cap"], "tokens")
        from whatifs.org import runner as ORGR, registry as OREG, memos as OMEM          # v12: the long video ran under the department contract, step by step
        from whatifs.core import S as _S12
        ep12 = e["episode_id"]; ses12 = {(s["dept"], s["trigger"]): s for s in st.rows("Sessions") if s.get("episode_id") == ep12}
        need12 = set(OREG.EPISODE_RUNS["final"]) | {("D8", "final_gate"), ("D9", "publish")}
        assert need12 <= set(ses12) and all(s["status"] == "ok" and not ORGR.verify(s) for s in ses12.values()), ("a department run is missing, broken or unproven", {k: v["status"] for k, v in ses12.items()})
        led12 = {r["feature"]: r["status"] for r in st.rows("Feature_Ledger") if r.get("episode_id") == ep12}
        assert led12.get("dept_contract") == "PASS" and led12.get("takeaways_written") == "PASS", ("the organisation's checks did not pass", led12.get("dept_contract"), led12.get("takeaways_written"))
        tk12 = [t for t in st.rows("Takeaways") if t.get("episode_id") == ep12]
        assert len(tk12) >= len(need12) and not any(ORGR._takeaway_problems(t) for t in tk12), "a department run wrote no valid takeaway"
        wd12 = OMEM.watchdog(st); oh12 = ORGR.health(st); assert oh12["ok"] and _S12("ORG_WATCHDOG_AT") and _S12("ORG_SINCE"), oh12["problems"]
        assert not [m for m in OMEM.rows(st) if m["status"] in ("open", "escalated") and m["type"] == "problem_memo" and m["episode_id"] == ep12], "a problem memo of the scheduled episode is still open"
        print("organisation:", len(ses12), "department runs,", len(tk12), "takeaways,", oh12["stats"]["live"], "live memos; watchdog checked", wd12["checked"])
        assert led12.get("decisions_executed") == "PASS" and led12.get("lever_verified") == "PASS", ("the Execution Engine's checks did not pass", led12.get("decisions_executed"), led12.get("lever_verified"))
        EXE4.engine_tick(st); row4 = next((x for x in st.rows("Tickets") if x.get("id") == tk4["id"]), {}); log4 = [x["action"] for x in st.rows("Lever_Changes") if x.get("ticket_id") == tk4["id"]]
        assert row4.get("state") == "verified" and log4 == ["intent", "applied", "verified"], ("the rehearsal's decision did not become a verified change", row4.get("state"), row4.get("note"), log4)
        assert (OMEM4.get(tk4["id"], st)["resolution"] or {}).get("kind") == "lever_verified" and not EXE4.lever_issues(st)[0] and not EXE4.decision_issues(st)[0], "the ticket was not closed on the ledger"
        print("execution engine: ticket", tk4["id"], "->", row4["state"], "|", " > ".join(log4), "|", str(row4.get("proof"))[:110])
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
        set_setting("TABLE_READ_MODE", "on"); set_setting("ROOM_MODE", "v1")      # v11: the table read belongs to room v1 (v2 drops role memos by design)
        rr = ROOM.run_room(DRAW("EPTABLE", "collective"), "EPTABLE")
        assert rr["table_read"]["arm"] == "on" and rr["director_notes"], "table read did not run"
        set_setting("ROOM_MODE", "v2")
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
        old = (now_utc() - dt.timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ")      # v9.3.1: the rescue now looks at 72-120 h; 6 days old = "too old" (fake mode has no view counts)
        st.update("Episodes", "episode_id", e["episode_id"], {"slot_et": old})
        MG.learn(); assert st.rows("Analytics"), "no analytics"; print("learn ok")
        assert re.search(r"too old|v9 rotation test", str(next(x for x in st.rows("Episodes") if x["episode_id"] == e["episode_id"])["pkg_check"])), "packaging check did not run"      # v9: the rotation test replaces the v8.5 rescue
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
        assert abs(G87.production_room_inr() - (G87.remaining_inr() - 100 - G87.earmark_left_inr() - G87.specials_left_inr())) < 1e-6, "maintenance reserve (and v9.4a/v10: the owner's earmarks) must sit inside the cap"
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
        # v8.10 checks: Gemini voice with the cast, premise scores by two judges, Owner's Cut, immersion, technique library, Script Preview round trip
        assert tl81.get("engine") == "gemini" and {"DIRECTOR", "SKEPTIC"} <= set(tl81.get("gemini_voices", {})) <= {"DIRECTOR", "SKEPTIC", "JUDGE", "WITNESS"}, "the narration did not use the Gemini cast voices"
        assert all(u["words"] for u in tl81["units"]), "a Gemini line has no word timings"
        from whatifs.voice_lab import cast_samples
        cs = cast_samples(os.path.join(work, "cast_samples")) if os.makedirs(os.path.join(work, "cast_samples"), exist_ok=True) is None else []
        assert len([x for x in cs if x[1]]) == 15 and re.match(r"(\d+)/\1 ", cs[0][2]) and int(cs[0][2].split("/")[0]) in (20, 24)      # v9.2: + the 4 trial characters, f"cast samples / voice check: {cs[:2]}"
        st810 = store(); flush_costs()
        assert len(st810.rows("Cast")) == 20 and st810.rows("Voice_Check"), "cast tab / voice check missing"
        ps = st810.rows("Premise_Scores"); assert ps and any(str(r["chosen"]) == "True" for r in ps) and all(r["claude_score"] and r["gemini_score"] for r in ps), "premise scores"
        assert st810.rows("Owners_Cut") and st810.rows("Technique_Library"), "Owner's Cut / technique library missing"
        assert any(c["item"] == "gemini_tts" for c in st810.rows("Cost_Log")), "TTS cost not logged"
        assert any(r["grid"].startswith("llm-") and r["status"] == "FRESH" for r in st810.rows("Premises")), "the LLM premise bank was not made"
        epd = json.loads([e for e in st810.rows("Episodes") if e.get("yt_id")][0]["draw_json"]); assert epd.get("cast") and epd.get("owners_cut"), "cast / Owner's Cut not recorded"
        from whatifs import preview as PV
        pv = PV.run(); assert pv["ok"]; dr = st810.rows("Script_Previews")[-1]; assert dr["status"] == "DRAFT"
        PV.decide("APPROVE " + dr["draft_id"]); assert store().rows("Script_Previews")[-1]["status"] == "APPROVED"
        print("v8.10 checks ok")
        # v8.11 checks: prompt caching recorded per episode, the opening Kling hook + the impact clips, measured-vs-estimated AI cost row,
        # the Premise_Bench refilled by the learning job and used first by the next room, below-the-bar never skips
        flush_costs(); from whatifs.core import flush_log as _fl; _fl()
        cs811 = [r for r in store().rows("Cache_Stats") if r["episode_id"] == e["episode_id"]]
        assert cs811 and float(cs811[0]["hit_ratio"] or 0) > 0 and int(cs811[0]["cache_read_tok"]) > 0, f"prompt cache not used: {cs811[:1]}"
        kl811 = [i for i, s_ in enumerate(sh87) if s_.get("type") == "kling"]
        assert len(kl811) == S("KLING_CLIPS", int) and sum(1 for i in kl811 if sh87[i].get("opening_hook")) == 1 and any(sh87[i].get("impact") for i in kl811), \
            f"Kling placement: {[(i, sh87[i].get('opening_hook'), sh87[i].get('impact')) for i in kl811]}"
        sm811 = [r for r in store().rows("Cost_Log") if r["item"] == "ai_per_video_summary" and r["episode_id"] == e["episode_id"]]
        assert sm811 and sm811[0]["inr"] == "0" and float(sm811[0]["est_inr"]) > 0, "measured-vs-estimated AI cost row missing"
        from whatifs import premise as PR811, room as ROOM811
        np811 = S("NEXT_PREMISE"); set_setting("NEXT_PREMISE", "")          # a teased premise would (rightly) win over the bench; tested without one
        if not PR811.bench_rows(): PR811.refill_bench(force=True)
        assert PR811.bench_rows(), "the Premise_Bench was not filled"
        sp811 = ROOM811.scout_and_pick({"strategies": {"family": "F09_space"}, "playbook": {}}, ROOM811.context(), "EPBENCH")
        assert sp811.get("from_bench") and any(r["status"] == "USED" for r in store().rows("Premise_Bench")), "the scout did not draw from the bench"
        set_setting("NEXT_PREMISE", np811)
        assert not S("SKIP_IF_BELOW_BAR", bool) and S("OWNERS_CUT_JUDGE") == "gemini"
        print("v8.11 checks ok")
        # v9 checks (stages 1-2): the Show Plan was logged, the character bible seeded, the trial tags reached the voiced timeline as data (never spoken),
        # the render devices ran (teacup placements logged, not before 30 s), no tag text reached the captions
        st9 = store(); assert st9.rows("Show_Log") and len(st9.rows("Characters")) == 4, "Show_Log / Characters missing"
        u9 = tl81["units"]
        assert any(u.get("show") for u in u9) and not any("[" in u.get("text", "") for u in u9), "show tags not carried as data / spoken"
        ep9 = next(x for x in st9.rows("Episodes") if x["episode_id"] == e["episode_id"]); cups9 = json.loads(ep9.get("teacup_json") or "[]")
        assert all(c["t"] >= 30 for c in cups9), f"teacup placements: {cups9}"
        srt9 = [os.path.join(dp, f) for dp, _, fs in os.walk(d74) for f in fs if f.endswith(".srt")]
        assert srt9 and not any(re.search(r"\[(METER|EXHIBIT|JURY|/?CLIPBAIT)", open(x).read()) for x in srt9), "a show tag reached the captions"
        pk9 = [r for r in st9.rows("Packaging_Tests") if r["episode_id"] == e["episode_id"]]
        assert 1 <= len(pk9) <= 3 and any(r["status"] in ("LIVE", "WINNER") for r in pk9) and st9.rows("Season") and st9.rows("Experiments"), "packaging pairs / Season / Experiments missing"
        print("v9 checks ok")
        # v9.1 checks: the Atmosphere Pack ran inside its time budget with the pulse caps intact, render minutes were logged
        ep91 = next(x for x in store().rows("Episodes") if x["episode_id"] == e["episode_id"])
        if S("ATMOSPHERE_ON", bool) and not S("V91_SAFE_MODE", bool):
            a91 = json.loads(ep91.get("atmos_json") or "{}")
            assert a91 and float(ep91.get("render_min") or 0) > 0, f"atmosphere / render minutes not logged: {ep91.get('atmos_json')}"
        print("v9.1 checks ok")
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

