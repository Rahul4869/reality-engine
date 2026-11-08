# Changes (newest first). Claude Code adds one dated entry per merged change: what, why, cost, how to switch it off.

## 2026-11-08 v10.1 (part 2) - Model Steward
- Picture/video models now look after themselves like the text and voice models: instant failover when fal retires or breaks a model (same call retried on the next approved model; living stills fall back to a free camera move), a weekly retirement watch with a card 14 days ahead and a switch 7 days before the date, and a weekly scout that tests newer models automatically (capped) and adopts them only when clearly better, 3 days after telling the owner. Never raises the clip price beyond 1.3x or $0.50 without the owner. Switches: MODEL_STEWARD_ON, MODEL_LADDERS, MODEL_FAILS_TO_SWITCH, MODEL_SWITCH_LEAD_DAYS, MODEL_MAX_PRICE_RATIO, MODEL_MAX_USD_CLIP, MODEL_UPGRADE_SCOUT_ON, MODEL_AUTO_UPGRADE_ON, MODEL_UPGRADE_MARGIN, MODEL_UPGRADE_NOTICE_DAYS. Cost: ₹0 weekly; an automatic test costs at most BAKEOFF_CAP_INR (about Rs 130 for 2 scenes x 2 models).

## 2026-11-08 v10.1 - verified-API fixes + growth upgrades
- Video: Kling 2.5 Turbo Pro hero clips (Kling 2.1 retired on fal; $0.35 per 5 s), each model gets its own input schema, retired ids replaced at run time. Stills sharper at the same price (1872x1056 = 2 MP). Bake-off candidates: Kling 2.6 Pro (silent), Wan 2.6 Flash, Hailuo 2.3 Fast.
- Uploads: no needless AI-label re-set when YouTube omits the field; 'made for kids' flagged at once; Meta AI disclosure on Reels and Facebook Reels.
- Growth: verdict styles rotate; near-duplicate scripts flagged; Shorts capped at 10 a week and hero-still Shorts off; Instagram 'Case Files' carousels with each long video; search-demand scores for premises; viewer 'what if' questions feed the scout; a card when the 500-subscriber tier is in reach; optional newsletter link.
- Switches: VERDICT_ROTATION_ON, SCRIPT_SIMILARITY_MAX, SHORTS_WEEKLY_CAP, HERO_STILL_SHORTS_ON, CAROUSEL_ON, CAROUSEL_PER_WEEK, WORKER_PUBLIC_URL, META_AI_LABEL_ON, DEMAND_SCORE_ON, VIEWER_QUESTIONS_ON, VIEWER_NAME_ON_SCREEN, YPP_WATCH_ON, NEWSLETTER_URL, V101_FLIPS_ON. Cost: about Rs +60/month video (Kling price) and Rs 0 for the rest.

## 2026-11-08 v10 growth (part 6) - pilot Shorts, Outlier Lab, model bake-off
- Two cheap pilot Shorts a week test upcoming premises; their engaged views raise or lower the premise's score (about Rs 1-2 each, ≤ Rs 40 a month). Switches: PILOTS_ON, PILOT_DAYS, PILOT_MONTHLY_INR.
- The Outlier Lab watches the opening of up to 3 standout videos a day and files judged technique cards (about Rs 0.5 each). Switches: OUTLIER_LAB_ON, OUTLIER_LAB_DAILY.
- One-time bake-off of video models with a choice card (≤ Rs 400; silence keeps the current model). Workflow: Model bake-off.

## 2026-11-08 v10-future - Policy Rescue, expiry reminders, weekly backups, the Advisor
- A policy change now comes with an impact note and Build-fix / Resume choices; keys and plans remind 14 and 3 days before they expire; the Sheet is backed up every Sunday (8 kept); one weekly Advisor card on money and growth; the dashboard's Health tab shows expiries and last runs. Switches: SHEET_BACKUP_ON, BACKUP_KEEP. Cost: about ₹2 only when a policy change happens.

## 2026-11-08 v10 growth (part 5) - Slop Guard, Retention Microscope, face check
- An AI-slop risk score for every video (shown on the dashboard; a card when high). Switches: SLOP_GUARD_ON, SLOP_WARN.
- Proven retention rules from this channel's own data reach the writer and the dashboard Lab (≥6 videos, ≥2,000 views, ≥5% effect; expire after 20 videos). Switches: MICRO_RULES_ON, MICRO_MIN_VIDEOS, MICRO_MIN_VIEWS, MICRO_MIN_EFFECT, MICRO_RULE_LIFE.
- Specials: a cast face that drifts in animation is replaced by the locked portrait (about ₹0.2 per check). Switch: FACE_CHECK_ON.

## 2026-11-08 v10 growth (part 4) - occasion-aware specials
- The two monthly cast specials now follow the calendar (Halloween, Christmas, New Year, Diwali, Holi, Eid, Lunar New Year, Valentine's, April Fools, Pi Day, Mother's Day, Thanksgiving and more), each with its own witty brief and a warm family subscribe ending; other months tie to the week's safe science trend; a heads-up card 3 days before each occasion special. Lunar dates refresh each December. Switches: SPECIALS_PER_MONTH, OCCASION_PRIORITY, OCCASION_DATES, SPECIALS_TOPICAL_ON. Cost: unchanged (2 specials a month).

## 2026-11-08 v10 growth (part 3) - Shorts Lab and the Character Love Engine
- Reel captions light up word by word inside the safe zone; a weekly card lists only the winning Shorts to link (plus an instant card for a breakout); never more than 14 Shorts a week. Switches: KINETIC_CAPTIONS_ON, REEL_CAPTION_MARGIN_PCT, SHORTS_LINK_MAX, SHORTS_BREAKOUT_X, SHORTS_WEEKLY_CAP.
- Specials now rotate renewable character formats (Grimm's Lab Log, Nana's Tea Rulings, Vale's Deduction, rivalry, jury votes, rationed backstories), learn which format wins, and end with format-specific in-character subscribe asks. Optional festive launch reel. Switches: SPECIALS_LORE_MIN_DAYS, CAST_INTRO_FESTIVE. Cost: none added.

## 2026-11-08 v10 growth (part 2) - special reels and the ₹5,000 cap
- The launch "cast intro" reel (run by hand once) and a witty 15-second cast special on the 2nd and 16th of each month, posted to YouTube Shorts, Instagram and Facebook with the subscribe line; ₹150 each at most from the owner's +₹300 specials earmark. The cap moves once to ₹5,000. Switches: SPECIALS_ON, SPECIALS_DAYS, SPECIAL_REEL_CAP_INR, SPECIALS_EARMARK_INR, V10_FLIPS_ON.

## 2026-11-08 v10 growth (part 1) - watch hours, affiliate block, audience prompts, emotion beats
- Titles and descriptions in 6 languages for every long video (about ₹2 a video). Switches: LOCALIZATIONS_ON, LOCALIZE_LANGS.
- Affiliate block with disclosure, off until links are added. Switches: AFFILIATE_ON, AFFILIATE_LINKS, AFFILIATE_DISCLOSURE.
- Witty in-character audience prompts (never rewards) with ask caps and spacing enforced by code; one earned emotion beat per video, logged for learning. Switches: ENGAGE_RULES_ON, ENGAGE_MAX_CTA, ENGAGE_NO_ASK_FIRST_PCT, ENGAGE_MIN_GAP_LINES, EMOTION_BEAT_ON.

## 2026-11-08 v9.4b (part 2) - WhatsApp control room
- Owner messages on WhatsApp (buttons inside 24 h, the utility template outside; the email copy always goes); button taps act like dashboard taps; status / pause / resume; a late-night chat that answers from the channel's real numbers and offers [Build it] for agreed ideas (₹250/month shared cap, then a cheap model). The dashboard page is published by the pipeline. Switches: WA_ON, CHAT_MONTHLY_CAP_INR, WA_TEMPLATE_NAME. Cost: chat within its cap; WhatsApp utility templates about ₹0.12 each.

## 2026-11-08 v9.4b (part 1) - Mission Control data feed and taps
- The pipeline writes the dashboard snapshot to Cloudflare KV after each tick (once the Cloudflare secrets exist); taps from the page come back encrypted and are handled once with an acknowledgement; Worker + page + tests live in `mission_control/`. Switch: DASH_ON. Cost: ₹0 (Cloudflare free plan).

## 2026-11-08 v9.4a (part 3) - owner messages, builds, orchestra, Visual Lab, platform watch
- One owner-message layer with no-spam tiers (now ≤2/day + quiet hours, week = digest Tue/Sat/Sun, fyi = dashboard), silence = default, one-click answers. Switches: NOTIFY_NOW_MAX_PER_DAY, QUIET_HOURS_IST, DIGEST_DAYS, DIGEST_HOUR_IST.
- Claude Code builds and repairs on the owner's Claude plan; Merge/Reject; tweaks auto-merge after 24 h green (decision 11). Switches: BUILDS_ON, AUTO_MERGE_TWEAKS_ON, REPAIR_ENGINE.
- Orchestra: concurrency queues for Sheet-heavy jobs; heavy jobs never near a release. Switch: ORCHESTRA_RELEASE_GUARD_H.
- Visual Lab: weekly zero-cost picture-upgrade ideas from retention data (owner's tap builds or switches them on). Switches: VISUAL_LAB_ON, VISUAL_LAB_MIN_VIDEOS, VISUAL_LAB_MAX_CARDS.
- Platform change-log watcher (₹0). Switch: FACTS_WATCH_ON. Credits money view (Max until 10 Dec; Gemini). Laptop change path documented.
- Cost: none added (rule-based; builds on the owner's plan).

## 2026-11-08 v9.4a (part 2) - the ₹4,700 budget, modes, earmark and protected core
- Cap ₹4,700 (one-time move of cap cells ≤ ₹4,500). Standard ≤ 8 long videos; Runway (₹2,400, Saturdays, ≤ 4) only by the owner's tap ('MODE RUNWAY' / 'MODE STANDARD' email link); Growth by itself when revenue exists. The ₹200 earmark is never production money; extras pause before production is squeezed. Switches: BUDGET_MODE, GROWTH_AUTO_ON, RUNWAY_CAP_INR, *_MAX_LONG_PER_MONTH, BUDGET_EARMARK_INR, GROWTH_ALLOWANCE_INR, V94A_FLIPS_ON.
- Cost: none added.

## 2026-11-08 v9.4a (part 1) - pre-production at half price (built on v9.3.2)
- The writers' room for the next slot runs 34-72 h early in its own hourly-checked job, every Claude call through Message Batches (50% off); production uses the result as written. Failure or lateness = production writes the episode as before. Switches: PREPROD_ON, ROOM_BATCH_ON, PREPROD_LEAD_HOURS, PREPROD_MIN_LEAD_HOURS, ROOM_BATCH_MAX_WAIT_MIN, PREPROD_JOB_MAX_HOURS.
- Cost: writing about half price (estimate; LLM_EST_INR is lowered only after 2 measured videos). The Tue 10 Nov video is already inside 72 h, so it is written the normal way.

## 2026-11-08 v9.3.2 - techniques are judged before use and fit-filtered; opening-window picture check (built on v9.3.1)
- A technique card is reasoned through (value, fit, metric, risk, how to raise its value) before filing; briefs get only cards that fit the episode's premise, at most 3, never forced. The owner's Neptune "POV plunge" card is seeded as TRIAL for plunge/descent premises. Switches: TECHNIQUE_INTAKE_ON, TECHNIQUE_MAX_PER_BRIEF.
- The picture check also covers up to 6 shots in the opening window. Switch: QC_VISION_OPENING_MAX (0 = v9.3.1).
- Cost: about ₹0.5 per video for the extra frames; about ₹2-3 per new technique card judged (rare).

## 2026-11-07 v9.3.1 "Launch" - the upload check replaces the API audit (built on v9.3)
- YouTube lifted the private lock for unverified API projects (2 Nov 2026). A ₹0 upload check (unlisted 20-s clip, read back, deleted) proves it on this project before any money is spent. Switch: none needed; `UPLOAD_LOCK` is set by the check.
- Every upload is read back: private-lock detector + AI-label read-back (a silently dropped label is set again). Switch: UPLOAD_VERIFY_ON.
- A video that never went public now also trips the lock (new spend pauses). The audit reminders run only when a lock is found.
- Hero-still Short: 6-10 s, hook as title, no "#shorts". Switches: HERO_STILL_MIN_SEC, HERO_STILL_MAX_SEC.
- Sign-in asks for youtube.readonly + yt-analytics-monetary.readonly now (no re-consent later).
- Cost: ₹0 (one test upload, 1-2 quota units per upload read-back).
- Packaging (owner decision 5): rotation off; rescue at 72 h on engaged views; picks until 2 h before release for every video, with a reply and a taste signal; optional YouTube Test & Compare link. Switches: PKG_ROTATE_ON, PKG_RESCUE_ENGAGED_ON, PICK_DEADLINE_BEFORE_SLOT_H, V931_FLIPS_ON.
- Character sheets lock by default after 72 h; the characters then appear on screen (owner decision 2). Switch: SHEETS_DEFAULT_LOCK_H (0 = never).
- One-tap merge can merge workflow changes when the GH_MERGE_TOKEN secret exists.

## 2026-11-07 v9.3 - virality + monetization pass (built on v9.2; V91_SAFE_MODE still restores v9)
- Cold open: YOU inside the scene first (second person, a physical stake), names and the courtroom after ~20 s; checked by the free retention gate; hooks gain a 'you_stakes' type. Switch: COLD_OPEN_YOU_ON.
- Micro-cuts: stills change framing every <= 3.2 s (2.6 s in the opening) from the same pictures; the cut map reports the median hold. Switch: MICRO_CUTS_ON.
- Advertiser safety: gore / injury / profanity words rejected in titles, thumbnail words, hooks, the opening and premises. Switch: AD_SAFE_ON.
- Shorts: trial Shorts open on YOUR stake and never reveal the verdict; the hero-still Short is scheduled after the long video and links it (bug fix: it went public ~30 h early). Switches: TRIAL_SHORTS_SAFE_ON, HERO_SHORT_DELAY_MIN.
- Packaging fixes: the uploaded title is shock-ranked; variant A is the live title (bug fix); rotation starts after 24 h and needs 1,500 views. Switches: TITLE_SHOCK_ON, PKG_ROTATE_START_H, PKG_ROTATE_MIN_VIEWS.
- Asks in character (jury identity). Switch: CTA_JURY_ON. Hero-still reels + Shorts ON by default (one-time migration, owner values kept). Switch: V93_FLIPS_ON.
- Cost: no new paid call; the one existing retention fix (about Rs 4-8) may run more often. Per video stays about Rs 467; 8 videos about Rs 3,736.

## 2026-11-06 v9.2 - fixes from the first real Script Preview (built on v9.1)
- Writer: no bigger retries (lower effort instead), per-role thinking caps, one effort per cached prefix, background jobs out of the preview, Setup fills the bench, cost-per-role and time-per-stage in the preview email.
- Shot plan: Kling on the stakes (never adjacent / plain), scene-aware POV anchors with variety, tiny lines -> free reaction cutaways (characters visible without sheets).
- Titles: natural English enforced; scroll-stopping shapes (bold claim + question, impossible claim, shock detail) ranked first.
- Voices: the owner's Gemini Voice Design voices (by ID or AI Studio name) with closest-prebuilt fallback; per-line loudness levelling + limiter; faster Setup (voice checks reused / parallel, samples kept).
- Switch off: the v9.2 flags in Settings (see the v9.2 report), or V91_SAFE_MODE = TRUE for v9.

## 2026-11-06 v9.2 - fixes from the first real Script Preview (built on v9.1; V91_SAFE_MODE still restores v9)
- Writer: thinking caps per role, a cut reply retried at LOWER effort (never more room), aligned effort for cached prefixes; bank / research only in background jobs; Setup fills an empty bench; cost per role + time per stage in the preview email.
- Shot plan: Kling on the stakes (never adjacent / plain), scene-aware varied POV anchors, tiny lines -> free reaction cutaways (characters visible without sheets).
- Voices: the owner's designed voices (Dr Grimm 3, Inspector Vale 1, Nana Rosa 1, The Archivist 2) by name -> ID, closest-prebuilt fallback; loudness levelling + limiter.
- Titles: natural-English rule + shock-first ranking (bold claim + question, impossible claim, shock detail). Setup: parallel voice checks, 7-day reuse, unchanged samples kept.

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
