# Changes (newest first). Claude Code adds one dated entry per merged change: what, why, cost, how to switch it off.

## 2026-11-05 v9.1 - Atmosphere Pack, hero-still reels, the v9 "not built" items, risk fixes (built on v9)
- Atmosphere Pack (ATMOSPHERE_ON + one flag per layer): moving light, particles, fog, heat shimmer, lens detail, breath fog, beat PULSE (hard caps), aura. Code only, zero cost, ~0.02 s per 1080p frame; automatic degrade above ATMOSPHERE_MAX_OVERHEAD_PCT. Lighting + composition directive on image prompts (LIGHTING_DIRECTIVE_ON).
- Hero-still reels (HERO_STILL_REELS_ON, off), character grammar (CHAR_GRAMMAR_ON), courtroom theater (THEATER_STYLE), retention-to-beat map, role ROI, comment mining, AI-drafted replies (off), one variety rewrite, Instagram audio-drop posting (off).
- Risk fixes: the film grain seed was salted per process (re-renders differed) -> sha256 seed; the v8.2 retry test drew a different episode every clock minute -> frozen clock + a cross-minute regression test; Gemini voices resolved through Voice_Check with a descriptor-based substitute before Kokoro.
- V91_SAFE_MODE = TRUE switches every v9.1 feature off at once (= v9). Cost: default flags add about Rs 2 per video (comment mining + the occasional variety rewrite). Credits: hook-shape ideas from the MIT-licensed YouTube agent skill pack (v9).

## 2026-11-05 v9.1 - Atmosphere Pack, hero-still reels, the v9 "not built" items, risk fixes (built on v9; V91_SAFE_MODE = TRUE restores v9 exactly)
- Atmosphere Pack (code only, zero cost): god-rays + light sweep, 3-layer particles, fog, heat shimmer, lens detail, breath fog, beat PULSE (hard caps, QC holds), aura / energy swirl; lighting + composition directive on every image prompt. ATMOSPHERE_ON = FALSE gives the v9 pixels (golden test). Measured render overhead +5.1 % (standard episode) and +13.7 % (1080p clip) in a quiet sandbox (budget 30 %, automatic degrade).
- Hero-still reels (HERO_STILL_REELS_ON, off): best still by a CV poster score, seamless loop, pulse + aura + hook, the episode's own voiced line.
- Character grammar (on) and THEATER_STYLE = courtroom (portrait default); retention-to-beat map and role ROI (report only); comment mining into the bench (filtered, capped, batch); AI comment drafts (off; never posted); ONE variety rewrite (only when needed); Instagram audio-drop posting (off; Meta keys needed).
- Risk fixes: Gemini voice substitution by descriptors before Kokoro; the film-grain seed was salted per process (now stable); the intermittent v8.2 test is clock-independent (frozen) with a cross-episode regression test.
- Paid calls per episode with defaults: unchanged from v9 (test). Settings: see the v9.1 report flag table. Switch all off: V91_SAFE_MODE = TRUE.

## 2026-11-04 v9 - "Reality on Trial" (built on v8.11; contains everything since v8.9.3)
- Format: each episode is a trial (Show Plan from the existing Showrunner call, code-validated, Show_Log), the core cast in a Characters bible (Vale, Grimm, Nana Rosa, the Archivist), Nana Rosa and the Archivist voiced, no guest rotation. Switch off: SHOW_MODE = off (= v8.11).
- Signature devices by code (zero cost): found footage, Survival HUD, Jury Meter, exhibit pins with credits, Nana's teacup, letterbox; photosensitivity QC; show tags never spoken. Switches: FOUND_FOOTAGE_ON, HUD_ON, JURY_METER_ON, EXHIBIT_PINS_ON, TEACUP_ON, LETTERBOX_ON, PHOTOSENSITIVITY_QC_ON.
- Demand first: outlier ranking -> Demand_Signals -> the bench (60 % outlier-derived for 8 episodes, never their titles). Packaging: 3 pairs, owner pick with timeout, 48 h rotation test. Hook shapes adapted from the MIT-licensed open-source YouTube agent skill pack (ideas only; credited here).
- Community: jury comment (pin by hand), vote tally, teacup finders, Comment_Queue (draft by default), weekly digest; Season and Experiments tabs; variety guard; Shorts trilogy + clip-bait Short + audio drops; made-for-kids guard.
- Costs: AI_SAVER_ON TRUE, LLM_EST_INR 176; spend warnings at 70/90 %, AI-side overrun ladder, weekly estimate-vs-measured email, preview cost lines, Message Batches, audio cache. Pictures and clips are never trimmed for AI cost. One-time character sheets: lifetime cap 40 images (about Rs 320 at most), manual workflow.
- Per video about Rs 467 (8 videos about Rs 3,732; 9 about Rs 4,198). See the v9 report.

## 2026-11-02 v8.11 - opening Kling hook, no skipped slots, prompt caching, model routing by capability, measured AI cost
- Kling: 1 clip in the opening (first-person rush hook), the rest on the impact. Same count, same cost. Switch off: KLING_OPENING_CLIPS = 0.
- No skipped slots: Premise_Bench tab drawn first (refilled automatically below 6), up to 4 scout rounds, up to 3 Owner's Cut rewrites, then the best-scoring version + one email. Switch off: SKIP_IF_BELOW_BAR = TRUE, PREMISE_BENCH_ON = FALSE.
- Prompt caching with explicit breakpoints, warm-up before parallel calls, Cache_Stats tab. Switch off: PROMPT_CACHE_ON = FALSE.
- Routing: Opus for creative work and the script (SCRIPT_MODEL = opus | fable), Sonnet for edits, Haiku only for verified JSON repair, Gemini judges (Owner's Cut judge = Gemini by default). Effort per role in EFFORT_* cells.
- Cost: AI-writing estimate +₹62 per video (LLM_EST_INR 148 -> 200, THINK_EST_INR 30 -> 40); per video ≈ ₹490. Pictures and clips are never trimmed because of it (VISUALS_PROTECTED). AI_SAVER_ON saves about ₹30 per video. Measured vs estimated AI ₹ per video in Cost_Log ('ai_per_video_summary') and Cache_Stats. See the v8.11 change report.

## 2026-11-01 v8.10 - Gemini voice + cast, premise quality, first-person immersion, voice acting, immersive sound, creative constitution, Script Preview
- Narration: Gemini TTS with your Cast tab voices (5 experts + 15 rotating guests), Kokoro as automatic fallback. Switch off: TTS_ENGINE = kokoro, CAST_ON = FALSE.
- Premises: monthly AI premise bank, two blind judges (Claude + Gemini) calibrated with your liked/boring examples, Premise_Scores tab, no fail-forward (skip + email). Switch off: PREMISE_BANK_ON, PREMISE_DUAL_SCORE_ON = FALSE or PREMISE_FAIL_FORWARD = TRUE.
- Immersion: Immersion Director, first-person prompts on every picture type, Kling on the impact sequence, POV camera effects on every shot type locked to sound. Switch off: IMMERSION_ON / POV_CAMERA_ON = FALSE.
- Voice acting {curve} notes, film-edit pacing (EMOTION_CURVE_ON); immersive sound layers and the impact recipe (SOUND_IMMERSIVE_ON).
- Creative Constitution (CONSTITUTION), Craft_Notebook tab, Technique_Library tab, Owner's Cut gate (OWNERS_CUT_ON).
- Script Preview workflow with one-click approve / reject (PREVIEW_USE_APPROVED).
- Budget: cap ₹4,000; TTS (TTS_EST_INR 30) and thinking (THINK_EST_INR 30) in every estimate; Gemini prepaid credit reminder; 4th-Kling proposal only with headroom.
- Cost: about +₹60 per video in the estimate (TTS ≈ ₹14-27 for 10 min + reels, thinking allowance), + about ₹10-25 per video for the judges, Immersion Director and Owner's Cut, + ₹4-8 a month for the bank. See the cost table in the v8.10 change report.

## 2026-10-31 v8.9.1 - fixes from the external review
- Fixed 8 confirmed defects (test clip in production, Repair Bot filter, tease lost on failure, Sheets past column Z, Meta posting + Drive privacy, stereo mix, strategy scoring, guest pronoun / hook row). No cost change, no new setting. See REVISION_NOTES v8.9.1 and K78.

## 2026-10-31 · v8.9
- Cinematic look: one locked dark style on every in-video picture and clip (`STYLE_LOCK`), brighter variant for thumbnails. Free.
- Camera: 8-move library, strongest in the opening and before reactions, calm shots livelier too; the Director can suggest a move per still and code validates it (`CAMERA_MOTION`, gentle = old moves). Free, no count changes.
- Living stills: atmospheric motion prompts + a slow push on playback, same count. Free.
- Voices: clearer recipes, no echo in the master, a rotating guest for the Curious One (`GUEST_ROTATION_ON`). Free.
- Each video ends by teasing the next episode, which is then made from that premise (`NEXT_TEASE_ON`). Free.
- Preventive plan check before any picture money; Instagram captions capped at 5 hashtags. Free.
- Change handler: this file, `CLAUDE.md`, change-ready email + one-click Merge workflow (`PR_MAIL_ON`). Free (GitHub Actions).
