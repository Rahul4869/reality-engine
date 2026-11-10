> HISTORICAL - DO NOT FOLLOW. Superseded by docs/CURRENT/SYSTEM.md on 10 Nov 2026 (v12 truth hygiene). Kept unedited below as history.

# Module docstrings as they stood in v11.1 (removed from the code on 10 Nov 2026)

## tools/atmos_bench.py
```
v9.1 render performance check (run: python tools/atmos_bench.py [seconds]). Renders the same still shot through the REAL render path (camera move +
show overlay + encoder) at the production work size with ATMOSPHERE_ON false and true, prints the time of each, the overhead %, and the automatic
degrade steps when the budget is forced low.
```

## tools/google_signin.py
```
tools/google_signin.py v8.9.2 - ONE-TIME helper run on GitHub. Step 1 prints two sign-in links (safe to show).
Step 2 swaps a pasted address for a long-life Google key and EMAILS it to you. The key is never printed in the (public) log.
v8.9.2: Google now refuses Drive and YouTube permissions in ONE consent ("scopes that cannot be requested together"),
so Drive gets its own consent and its own key: link 1 -> G_REFRESH (YouTube, Analytics, Sheets, Gmail send),
link 2 -> G_REFRESH_DRIVE (Drive files this app creates). Same OAuth client, same Google account.
```

## tools/perf_atmosphere.py
```
v9.1: render time of one standard (rehearsal-size) episode with ATMOSPHERE_ON TRUE vs FALSE, plus 1080p per-frame cost of the layers.
Usage: WI_FAKE=1 WI_SMALL=1 python tools/perf_atmosphere.py
```

## tools/plan_guard.py
```
tools/plan_guard.py  v8.0
Runs on every GitHub save. RED = something broke the locked plan (Kernel v7.3 rule numbers). Operator only reports GREEN/RED.
```

## tools/rehearsal.py
```
tools/rehearsal.py v8.0 - full offline run: setup -> voices -> tick -> produce -> release x2 -> trends -> learn -> brief.
Fake models, fake images, synthetic voice. Proves every stage connects. Costs nothing. Used by CI and the repair bot.
```

## tools/repair.py
```
tools/repair.py v8.3 - repair bot. When a job crashes, send the traceback + the failing file to Claude, get a COMPLETE fixed file,
run Plan Guard + the offline rehearsal (with every key removed from its environment), and open a pull request.
Auto-merged only if all checks pass, AUTO_MERGE_REPAIRS is TRUE and the fix adds no new network, key, shell or file-deleting code;
otherwise the pull request waits for the owner (one email). Cap = MAX_REPAIRS_PER_WEEK from the Settings tab.
Gemini and the owner never edit code.
```

## whatifs/__init__.py
```
Reality Engine v8.2. Written only by Claude (Kernel K1). Gemini never edits code.
```

## whatifs/anim.py
```
v10.2 Animation director (K152; owner 2026-11-09, option C: 8 videos/month, ~20 s of real animation each; stack = fal Kling + Google
images + Claude + ffmpeg only, nothing new).

What it does, per long video:
1. SLOTS: exactly ANIM_SHOTS shots become animated scenes, at the retention cliffs: the cold open (0:00), the ~3:00 and ~6:00 re-engagement
   points and the verdict (scaled to the video's length: 0, 0.29, 0.57, 0.92 of the runtime). Nothing else is animated by the paid model.
2. START FRAMES: each animated scene starts from a STAGED picture made by Google's image model (discovered live as role 'gem_image') with the
   locked character portraits attached as reference images, so faces stay the same; the scene is set in the character's own lit world
   ('Toybox Noir': stylized 3D puppet look, felt/clay/wood materials, one hard noir key light). If the Google picture fails, the normal still
   (fal) is used with the same style lock and the ledger records it.
3. ACTING: the motion prompt is an acting beat (anticipation -> action -> settle), a lighting event and ONE camera move, with an avoid list.
   The hero video model is Kling on fal (FAL_HERO_MODEL; the Model Steward keeps it alive).
The Feature Contract then measures the result (seconds, real motion); nothing here is trusted on its word.
```

## whatifs/art.py
```
whatifs/art.py v8.9 (bright cinematic thumbnail style; v8.6) - thumbnails + reel covers (+ free covers for Shorts 3-4; brand clear of the timestamp): premium key art, cinematic grade, bold type with stroke + glow,
phone-size readability check, brand mark. 3840x2160 master, 1280x720 upload (<2MB).
```

## whatifs/atmosphere.py
```
whatifs/atmosphere.py v9.1 - the ATMOSPHERE PACK (K104). Code only: zero API cost, deterministic per shot (seeds from the episode id + shot index).
One overlay object for the whole video, applied BEFORE the show overlay, speaker chip and CTA chip, so the HUD, exhibit pins, meter and chips are always
drawn on top of it (readable by construction); in addition the atmosphere is faded to 30 % inside those regions and the caption band.

Layers (each has its own flag; ATMOSPHERE_LEVEL = auto follows the Show Plan intensity, +1 for fire / space / impact moods, max 3):
  god-rays from the brightest region (slow drift, <= 3 % flicker) + a diagonal light sweep; particles in 3 layers (near / mid / far) chosen by mood
  (dust, embers, ash, snow, rain, sparks, space dust), parallax-matched and occluded by a depth PROXY; fog / smoke from tileable noise scrolled at
  different speeds, denser far, tinted by the shot's colour; heat shimmer (fire / desert / engine); lens detail (edge chromatic aberration, anamorphic
  streaks, halation, breathing focus); breath fog on found-footage RECON spans; the beat-synced PULSE; aura glow + energy swirl around the focal point.
DEPTH: an overlay only sees finished frames, so "depth" here is a PROXY from each frame (vertical position + blurred luminance + local contrast), not the
image's depth map. Safety caps are hard-coded: PULSE <= 2 per second and <= 8 % luminance swing, never red-dominant, never in the first 2 s of a long
video, never during HUD / exhibit readouts; total added light <= MAX_GAIN. Performance: ATMOSPHERE_MAX_OVERHEAD_PCT; above it the layers degrade
automatically (particles, then fog, then god-rays) and the step is logged.
```

## whatifs/bakeoff.py
```
v10 model bake-off (K143; D4 + carry-over: current vs Kling 2.5 Turbo Pro vs Kling 2.6 Pro, no Kling 3). One time, started by hand
(workflow 'Model bake-off'), at most BAKEOFF_CAP_INR. The same two scenes are animated by the current hero model and each candidate in
BAKEOFF_CLIP_MODELS; the clips go to the owner's Drive (private) and one card asks which to use ([Keep current] / [Use 2] / [Use 3]).
Silence = keep the current model (the safe default). A candidate fal rejects is skipped (fal retires models: verify ids before running).
```

## whatifs/brain.py
```
v11 (K155) Channel Brain - the learning core (research report 9 Nov 2026, sections B, E, G, H).

What it does, with no theatre:
- Every published video / Short gets FEATURES (hook archetype, title pattern, topic cluster, length band, lead character, origin) in Video_Features.
- OUTCOMES come only from YouTube Analytics: for every video, trials = views and successes = engaged views (YouTube's own 'stayed' signal; views
  count every play since 31 Mar 2025 / 24 Aug 2026), plus average % viewed. Owner's own views are never added; nothing is imputed.
- The TECHNIQUE EVIDENCE table (Technique_Evidence) holds one row per feature level. Evidence is pooled across videos (families, not single videos) with a
  Beta-binomial model against the channel's pooled baseline. P(level beats baseline) is computed by sampling. Rules:
    proven  : P >= BRAIN_PROVEN_P and >= BRAIN_MIN_VIDEOS videos and >= BRAIN_MIN_TRIALS views
    promising: P >= BRAIN_PROMISING_P
    retired : P <= BRAIN_RETIRE_P with >= BRAIN_MIN_VIDEOS videos, or not re-confirmed within BRAIN_RULE_DAYS
  Every rule carries a mechanism, an expiry date and a kill condition.
- CHOICES: Thompson sampling picks the hook archetype (and other levels) for each new Short; BRAIN_HOLDOUT (20%) keep the default, so the
  sampler must beat a real control. Assignments are logged.
- FORECASTS before publishing: an 80% interval for the engaged rate and average % viewed (from the posterior); scored weekly for coverage and
  error against the naive 'channel median' forecast. A brain that can't beat the median is reported as NOT learning.
All maths is numpy (Rs 0).
```

## whatifs/breakout.py
```
v11 Stage C (K158): the Breakout Protocol pieces that were still missing (research: Breakout Protocol + Feel Layer reports, 9 Nov 2026).

1. promise_paid(): the thumbnail/title promise must be ON SCREEN early (the promise shot starts by PROMISE_BY_SEC). Deterministic contract check.
2. aliveness(): the 'looks like a still' detector. At 2 frames per second it removes the camera move between frames (a fitted affine transform);
   whatever motion is LEFT (eyes, mouths, particles, parallax, animation) is what makes a frame feel alive. A window is alive when more than
   ALIVE_PIXEL_SHARE of its pixels changed by more than ALIVE_PIXEL_DELTA grey levels after that correction, ignoring a thin band around sharp
   edges (where a camera move's interpolation noise lives). Measured 9 Nov at 1080p: a photo with only a camera move = exactly 0; every particle
   world > 0.0004 in every half second.
   Contract check: alive share >= ALIVE_MIN_SHARE and no dead stretch longer than ALIVE_MAX_DEAD_S.
3. score(): the Breakout Score (0-100) from evidence already measured for the video (research weights). It RANKS and ALERTS; it never holds a
   video by itself (research: LLM-judge scores are not validated predictors; holds come only from deterministic checks).
4. monitor(): the 48-hour breakout monitor. A video at >= BREAKOUT_MULT x the channel's usual 48-hour views (or BREAKOUT_MIN_VIEWS while there is
   no history) gets a card: 'approve follow-ups' (2 Shorts + a sequel premise, paid from the breakout fund). Nothing is spent without the tap.
```

## whatifs/builds.py
```
v9.4a (WP3, K126): owner builds and repairs through Claude Code in GitHub Actions (workflow claude-build.yml, ₹0 API money) and the Merge / Reject /
auto-merge rules (decision 11). GitHub is reached with the owner's fine-grained GH_MERGE_TOKEN (Contents, Pull requests, Workflows, Actions: write).
```

## whatifs/caretaker.py
```
v10-future WP13 (K140): the things that keep the channel safe and the owner informed, without noise.
- Policy Rescue: when the Guardian finds an official AI-monetisation change, besides the 7-day pause it sends ONE urgent card with an impact note
  and the choices [Discuss] [Build fix] [Resume now]. (One Sonnet call, about ₹2, only when it happens.)
- Expiry calendar: Expiry_Calendar rows (keys, tokens, plans) remind 14 days before (This week) and 3 days before (Act now), once each.
- Weekly backup: every tab of the control Sheet as CSV in one zip on Drive (private; drive.file scope), newest BACKUP_KEEP kept.
- Advisor: one weekly money + growth card (spend vs cap, credits, cost per video, Shorts/specials performance, at most 2 suggestions).
- Health: last run of each job for the dashboard.
```

## whatifs/carousel.py
```
v10.1 (K149): Instagram "Case Files" carousel per long episode (saves + sends are Instagram's strongest growth signals). At production
time 6 slides (1080x1350 JPEG, 4:5) are made from the episode's own stills + the show plan (case, exhibits, objection, no verdict spoiler,
'full trial: link in bio' + subscribe) and kept privately on Drive. When the long video goes live, the slides are put on the dashboard Worker
as short-lived public JPEGs (KV 'pub:<32 hex>' with a 1-day TTL; Meta fetches image_url) and published as one carousel
(children <= 20, is_ai_generated on the PARENT only; verified 8 Nov 2026). At most CAROUSEL_PER_WEEK; ₹0 (pictures already paid).
```

## whatifs/cast.py
```
whatifs/cast.py v8.10 - the Cast tab: 5 experts (Director role) + 15 rotating guests (the Curious One, [SKEPTIC] in scripts).
Guests never repeat within GUEST_NO_REPEAT videos (least recently used first, weight breaks ties); each has a recurring quirk so viewers feel variety AND
familiarity. The writer is briefed with the speaking characters' personality, habits and quirk. Settings CAST_ON = FALSE restores the v8.9 GUESTS.
```

## whatifs/charts.py
```
v10.3 (K153): charts as PNG images for WhatsApp and the digests (Pillow, Rs 0). Only real numbers from the owner view; a DEMO chart says so on
its face; no data = no chart (never an invented one).
```

## whatifs/checkpoint.py
```
whatifs/checkpoint.py v8.2 - save and restore the expensive state of an episode in your private Drive.

Why: before v8.2 a failure after the AI writing (about Rs 140) or after the paid images/clips threw all of it away and the retry paid again. Now:
  plan   = script, voice (the narration clock), shot list, bible, packaging inputs      -> saved after planning
  assets = every paid picture and clip                                                    -> saved after the assets are made
  hold   = everything needed to re-render (plus thumbnail, covers, reels)                 -> saved when final QC fails (the one-click fix reads it)
A retry of the same slot, or the one-click fix, restores the newest stage and continues from there. Best effort: if Drive is unavailable the episode simply
runs as before. Segments and the master are never stored (they are cheap to render again).
```

## whatifs/cli.py
```
whatifs/cli.py v8.10 - entry point for every GitHub workflow.  python -m whatifs.cli <command>
```

## whatifs/community.py
```
whatifs/community.py v9 (stage 3b) - the Jury outside the video (K101):
- the in-character JURY COMMENT after release (top-level; the YouTube Data API cannot pin, so the text is emailed for you to pin),
- the JURY TALLY by deterministic keyword parsing (no AI), fed to the next episode's opening,
- TEACUP FINDERS (comments with a timestamp within 3 s of a hidden teacup; handles only, filtered, at most TEACUP_FINDERS_MAX),
- the COMMENT QUEUE: every comment triaged by code (question / prediction / feedback / spam-risk); COMMENT_REPLY_MODE off | draft | auto
  (auto = only template thank-yous to predictions, signed by a character, capped per day); a weekly digest email,
- the SEASON tab (verdicts, tallies, clues) and the EXPERIMENTS tab (hypothesis + 48 h / 7 d / 28 d results; recommendations only, never auto-changes),
- the VARIETY GUARD on the Show Plan (verdict streaks, a charge too close to a recent one).
Comment text is UNTRUSTED data: it is only matched by code, never followed and never put into a prompt.
```

## whatifs/contract.py
```
v10.2 Feature Contract (K151; owner 2026-11-09: "not adjectives - the mechanism has to force-implement every feature at its stage and pass
quality checks"). Every promised feature is a named, MANDATORY check at a stage, judged from real evidence (the script, the timeline, the
rendered files, the room's own scores), never from the fact that code exists. A feature that crashed and was 'skipped' leaves no evidence and
therefore FAILS here - that is the point.

Stages and what happens on a failure:
  script  (before any paid picture is made)  -> deterministic repairs where they exist (asks, end tease); anything else = HOLD before spending,
                                                with an owner card [Rewrite] [Approve anyway]
  final   (after QC, before upload)          -> HOLD (never uploaded) with the existing one-click fix + an owner card [Fix] [Approve anyway]
  review  (after upload, first CREATIVE_REVIEW_FIRST_N videos and every special) -> the video stays PRIVATE until the owner taps Approve;
                                                the card carries the 6-point self-critique and the ledger
Every check writes one row to Feature_Ledger (episode, stage, feature, PASS/FAIL/WAIVED, evidence). A waiver is per episode and per feature,
written only by the owner's tap (CONTRACT_WAIVERS). tests/test_contract.py fails the build if a feature has no probe.
```

## whatifs/core.py
```
whatifs/core.py v8.10 (Gemini voice, cast, premise scores, craft tabs; v8.9) - settings, storage (Google Sheet or local rehearsal store), logging, cost log, Google sign-in.
```

## whatifs/costguard.py
```
whatifs/costguard.py v9 (stage 3a) - cost controls that never touch pictures (K96):
- ESTIMATOR: one line per cost stage, used by Script Preview and the weekly deviation email.
- SPEND MONITOR: one email at 70 % and one at 90 % of the monthly cap (SPEND_WARN_PCTS); the existing budget gate still holds new episodes at the cap.
- OVERRUN LADDER: when an episode's measured AI spend passes OVERRUN_FACTOR x its AI estimate, the room steps down ON THE AI SIDE ONLY:
  (1) drop optional lowest-ROI reviews (table-read objections, the Director's script read), (2) fewer rewrite rounds (Owner's Cut max 1),
  (3) reuse cached assets (the checkpoint already does). Visuals are never trimmed; the episode is finished and the owner gets one email with the reason.
- WEEKLY DEVIATION email: measured vs estimated per stage over the last 7 days, deviations over DEVIATION_PCT.
- KIDS-RISK GUARD: after upload, YouTube's own made-for-kids value is read; TRUE = an email at once (never changed by code).
Everything here only READS Cost_Log / Settings and sends at most a few emails: no paid call lives in this module.
```

## whatifs/craft.py
```
whatifs/craft.py v8.10 - the owner's creative voice inside the pipeline:
- the Creative Constitution (Settings CONSTITUTION, blank = the built-in one in data.CONSTITUTION), read by every department;
- the Craft_Notebook tab: the owner's notes, top-priority creative input for scouting and scripting (CRAFT_NOTEBOOK_ON);
- the Technique Library: technique observations (hook device, first-3-second visual, cut rhythm, sound moment, payoff structure) from titles, descriptions
  and top comments of top niche videos, within the YouTube API quota (TECHNIQUE_RESEARCH_ON). Fetched text is untrusted data. Transcripts of other
  channels cannot be read through the official API (captions.download is owner-only), so they are not used;
- the Owner's Cut critic: before any picture money, 1-10 on inside-the-scene, weirdness hook, emotional peaks, payoff, originality; rewrite loop up to
  OWNERS_CUT_MAX_ROUNDS; still below OWNERS_CUT_MIN = v8.11: the best-scoring version is used and the owner is emailed (SKIP_IF_BELOW_BAR = TRUE: skipped).
```

## whatifs/cta.py
```
whatifs/cta.py v8.3 - the three audience asks (LIKE, SUBSCRIBE, SHARE), written as witty moments of the show itself.

Why: v8.2 had only one optional subscribe line and nothing for like or share. A viewer asks themselves "did I enjoy this?" at the moments right after a payoff,
and "who would love this?" at the end. So the asks are placed there, spoken by the two recurring roles in their own voices, and kept short.

How it works (three layers, so an ask is never missing and never ugly):
  1. The Showrunner's bible invents three premise-specific lines (the writer prompt places them: like ~40%, subscribe ~65%, share in the last 40 s).
  2. check()/ensure() verify by code that all three asks exist in the final script. A missing one is inserted from the hand-written pools below, at a calm
     moment (never right before or after a reaction, a reveal or a peak), rotating so two videos in a row never use the same line.
  3. Extras: a small code-drawn chip while the line is spoken (overlay.CtaChip), a witty description footer with a one-click subscribe link, and a follow / share ask
     at the end of each reel.
Nothing here calls an AI model or costs money. Everything is original text.
```

## whatifs/cutmap.py
```
whatifs/cutmap.py v8.0 - reviewable cut map (edit decision list proposal) from the ACTUAL rendered narration / video.

NOTHING IS EVER CUT AUTOMATICALLY. The project has no editor that can safely re-time narration, captions, pictures, effects and music together,
so this module only measures and proposes. A person reviews cutmap.md / the Cut_Map tab before the video goes public.

Evidence used (best first):
  1. word-level timeline written by voice.py (exact for the synthesized narration; includes which pauses were planned: [pause], paragraph, tags, breaths)
  2. the rendered narration WAV, measured with a frame-RMS silence detector (works without any transcript; results are ESTIMATES when used alone)
  3. optional ffmpeg scan of the finished video for frozen picture / black frames
Stumbles: a stumble cannot be detected reliably from audio alone. With word timings only these signals are measured: repeated adjacent words and
unusually slow sentences. Without word timings no stumble check is done and the map says so.
Sync: narration is the master clock (render.py cuts every shot at narration unit starts). Cuts are placed only inside silence between words, snapped
inward to video frames, and carry the ripple information (shift of everything after, captions, shot boundary, sound effects) needed to apply
the same cut to picture, captions, sfx and music together. ripple_remap()/apply_to_timeline() show exactly how.
```

## whatifs/dash.py
```
v9.4b (M1 + Mission Control 2-a, K130): the phone dashboard's data and its taps.

build_snapshot()  -> the JSON the dashboard page renders (same shape as the page's DEMO: engine, docket, progress, learned, lab, money, health,
                     settings, acks, whatsapp). Never contains secrets, scripts or unreleased premises beyond scheduled titles (K32).
publish()         -> writes it to Cloudflare KV ('snapshot') through the Cloudflare API (CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID, CF_KV_TOKEN). Called by tick.
handle_action()   -> one tap from the page (repository_dispatch 'dash_action', AES-GCM encrypted by the Worker): decrypt, dedupe, route, record an ack.
Routes: PICK|EP|B · MERGE|n · REJECT|n · LOCKSHEETS|CHAR · REDOSHEETS|CHAR · BUILD|id · PARK|id · LINKED|EP · MODE|lean/standard/growth ·
        PAUSE · RESUME · SET|key|value (allow-list) · ACT|id|n (any Owner_Actions button).
```

## whatifs/data.py
```
whatifs/data.py v8.7 - seed data loaded into the Sheet at setup: topic grids, banned list, strategy pools, director lessons.
```

## whatifs/deeptrial.py
```
v11 (K163): the monthly DEEP TRIAL - one long slot a month becomes a ~20-minute episode (research: longer videos raise minutes watched per
viewer and watch hours; TV viewing is growing). It replaces a regular slot (no extra slot), so the month's money plan stays the same apart from
longer narration and more stills (about +Rs 60-90; the 4 animated scenes stay 4 and the particle layer keeps the extra stills alive).

Structure (writer note): three acts with chapter titles; every act ends with a DIFFERENT outcome type (a win, a loss, an absurd turn) and a re-hook
line plus a voice change; a 3-5 minute "Jury Room" segment where the cast argue the evidence on screen (the audio-led idea folded in, never a
still image); then the verdict.
```

## whatifs/demand.py
```
v10.1 (K146): search-demand score for bench premises (compliant: YouTube search.list, own 100-calls/day bucket, 1 unit each, plus
videos.list statistics, verified 8 Nov 2026; no autocomplete scraping). Daily, up to DEMAND_DAILY READY bench premises are scored once:
median views of the top results for the premise's headline in the last DEMAND_LOOKBACK_DAYS, as log10, mapped to 0..1. The score adds
DEMAND_WEIGHT x score to the premise's combined bench score (once; demand_json records it).
```

## whatifs/digests.py
```
v10.3 (K153): the daily and weekly WhatsApp briefs (owner change request C3). Built ONLY from the owner view (every number with its source;
interpretations labelled; 'no data yet' when empty) plus one chart image. Inside WhatsApp's 24-hour window: text + chart + buttons; outside it: the
approved template with Menu / Numbers / Pause quick replies (the full brief also goes by email). Rs 0 (rule-based, code-made chart).
```

## whatifs/enforce.py
```
v11.1 (K166): HARD ENFORCEMENT of the researched breakout rules (owner, 10 Nov 2026: every point enforced, nothing included for namesake).

Each rule here is (a) given to the writer as an explicit instruction, (b) auto-fixed once where code can (one targeted rewrite or a timing change),
then (c) checked by the Feature Contract as a HARD check (FAIL -> the episode is HELD with an owner card). Sources: Feel Layer + Breakout Protocol
reports (Impact Map validators V1-V10, top-15 techniques) and the learning core.

Script-stage checks:  brain_playbook, no_retired, idea_evidence, joke_density, send_and_awe
Final-stage checks:   impact_hook (V1), impact_rehook (V3/V4), impact_punch_timing (V6), impact_sfx (V8), impact_variety (V9), impact_flash (V10)
```

## whatifs/engage.py
```
v10 growth: Engagement Engine + Emotion Beats (K133; specs ENGAGEMENT_ENGINE_SPEC.md, EMOTION_BEATS_SPEC.md).

Writer brief (ENGAGE_RULES_ON / EMOTION_BEAT_ON): in-character, witty audience prompts from a typed library (prediction, side-taking,
personal stake, expert flex, share trigger, subscribe identity), never rewards for likes/subs/shares (YouTube fake-engagement policy), and ONE
earned emotion beat whose type the code chooses per episode (awe most often).
Code check (enforce, runs BEFORE cta.ensure): one ask per kind (like / subscribe / share, K-rule: every video asks for all three), none in the
first ENGAGE_NO_ASK_FIRST_PCT of the spoken lines, never two asks (CTA or [JURY]) within ENGAGE_MIN_GAP_LINES spoken lines, at most ENGAGE_MAX_CTA;
removed asks are put back by cta.ensure at its safe, calm slots (story [JURY] prompts are kept).
Learning: the chosen emotion type and the ask types are logged in the episode's draw (Experiments / Retention Microscope read them).
```

## whatifs/episode.py
```
whatifs/episode.py v8.9 - one full episode, in three resumable stages (v8.5: fresh opening pictures, up to 4 Shorts, B thumbnail):
  PLAN    AI writing, hooks, narration (the master clock), shots, packaging text, reel plans      -> checkpoint "plan"
  ASSETS  every paid picture and clip (retried individually, only the missing ones on a resume)   -> checkpoint "assets"
  FINISH  render -> thumbnail + covers + reels -> full QC (+ free fixes) -> upload scheduled, or HOLD with a one-click fix
Long video is uploaded PRIVATE with publishAt = slot. Reels go out 15 min and 6 h after it is live, reels 3-4 the next two days (separate 'release' job).
Nothing that fails final QC is ever uploaded. A retry of the same slot resumes from the newest checkpoint instead of paying for the plan and assets again.
```

## whatifs/facts_watch.py
```
v9.4a (F1 Platform Facts watcher, K129): weekly, the official change-log pages are fingerprinted; when one changes, the owner gets ONE 'This week'
card with the link, so platform changes (like YouTube lifting the private lock on 2 Nov 2026) are never missed again. No AI call (₹0): the card points
to the page; the build chat / dashboard chat reads it and proposes what to change. The first run only records the baseline (no cards).
```

## whatifs/fakes.py
```
whatifs/fakes.py v8.11 (+ a fake Claude cache server that applies the documented caching rules) - offline stand-ins for every model call (rehearsal mode WI_FAKE=1). Zero cost.
```

## whatifs/fixes.py
```
whatifs/fixes.py v8.2 - repairs for the problems full QC finds, in a fixed order, with limits.

Free fixes first (re-mix the audio, rebuild captions, re-concatenate / re-mux, re-render the segments around a black or frozen stretch). Paid fixes (re-make a
missing picture or a failed Kling clip) only up to a rupee cap: AUTO_FIX_PAID_INR automatically, FIX_MAX_PAID_INR when you click the fix link. Whatever is still
wrong afterwards makes the video HOLD; nothing that fails QC is ever uploaded.
```

## whatifs/format_engine.py
```
Presentation-format controls for Reality Engine (v8.2). Defaults to the Reality Engine hybrid.

Switch: the Settings cell PRESENTATION_FORMAT (reality_engine | classic). The environment variable WHATIFS_PRESENTATION_FORMAT, if set, wins.
v8.1: the format is now CHECKED by code (check_script), not only requested in the prompt; the instructions are placed before the JSON
reply format (inject) instead of after it; rewrite steps may not drop speaker labels (labels_preserved).
```

## whatifs/governor.py
```
whatifs/governor.py v8.10 (TTS + thinking in every estimate, headroom, 4th-Kling proposal, Gemini credit; v8.7) - hard monthly cap (v8.7: the maintenance reserve is INSIDE the cap; v8.5: the B thumbnail is counted) WITH a pre-flight gate. Preserve minimum Kling shots; trim living-still animation first.
The controller estimates spend but cannot guarantee provider billing; Cost_Log is authoritative.
```

## whatifs/growth.py
```
whatifs/growth.py v8.7 - the click-through + retention layer of the learning loop. Small, free (no model calls), and read by real production code:
1. lessons_for(role)      : each department gets the lessons meant for it (the Reel Producer gets the Shorts lessons, the Packager the packaging ones...).
2. choose_titles()        : code-checked titles (30-60 characters, front-loaded, not shouting, not repeating the thumbnail words); best + runner-up.
3. thumb_words()          : thumbnail text is 1-4 words (readable at phone size).
4. dim_scores()           : every strategy dimension is scored on the metric it can actually move (titles/thumbnails on clicks, hooks on the first 30 s,
                            stories on how much is watched, Shorts on the long-video views they bring). Missing data is never invented.
5. diagnose()             : one plain label per analysed video (packaging / opening / holding / healthy / insufficient data) + a routed lesson.
6. strategy changes are logged (Strategy_Log) and a replacement that does worse than the strategy it replaced is rolled back automatically, once.
v8.7: 7. packaging-first promise (clean_promise), 8. retention gate (retention_issues: opening, re-hooks, re-engagement near 3:00 / 6:00, open loops),
9. rhythm blueprint per episode (rhythm_plan: least-recently-used cold-open device, interrupt, music arc, reaction density), 10. watch time per impression
for packaging (YouTube's own Test & Compare judges by watch time, not CTR), CTR unit self-check, retention vs similar-length YouTube videos for early
diagnosis, the steepest drop mapped to its beat (dip_lesson), and the related-video link (related_episode).
Sources for the rules (paraphrased, see REVISION_NOTES v8.6): YouTube's own creator guidance, the leaked 'How to Succeed in MrBeast Production' guide
(title + thumbnail first, the first minute decides retention, the video must deliver the thumbnail's promise), and large title-length studies (30-60 characters).
```

## whatifs/herostill.py
```
whatifs/herostill.py v9.1 (K105) - hero-still reels, per-character cinematic grammar and the courtroom composition. Code only.

HERO-STILL REELS (HERO_STILL_REELS_ON, default FALSE): 15-25 s vertical reels made from ONE of the episode's own premium stills (already paid for),
chosen as the best of N by a cheap computer-vision poster score (saliency mass, contrast, 9:16 crop safety; no AI). The reel is a SEAMLESS LOOP (the push
is a cosine, so the last frame equals the first; the audio fades in and out with matching ends), carries the Atmosphere Pack, a beat PULSE within the hard
caps, the aura, a hook text inside the first second, and the episode's OWN voiced clip-bait line cut from the finished mix (no new TTS request).
One per episode (2 per week at 2 videos a week) to Drive; a YouTube Short only with HERO_STILL_SHORTS_ON; Instagram only when the Meta keys exist
(otherwise skipped with a log line, zero cost). Templates rotate; never the same template twice in a row (the Variety Guard covers reels).

CHARACTER GRAMMAR (CHAR_GRAMMAR_ON, default TRUE): the bible's lens / angle / movement / colour fields map to concrete render parameters applied to the
character theater portraits (and the courtroom composition): Grimm = handheld jitter, dutch tilt, tight crop, underlight grade; Vale = symmetrical,
slow push, teal-steel grade; Rosa = eye level, warm amber, gentle drift. THEATER_STYLE = portrait | courtroom (courtroom: locked set with Rosa at the
bench, Grimm at the lectern, Vale at the defence table; deterministic cut to the speaking character).
```

## whatifs/hooks.py
```
whatifs/hooks.py v8.0 - ten opening-line candidates per episode, validated and scored, best one used as the opening.

Pipeline: write candidates (Sonnet-class model) -> CODE validates (word limit, greetings, hype phrases, numbers, overlap with the script)
          -> an independent judge (Gemini critic role, same as the script critic) scores clarity / relevance / curiosity / promise accuracy
          -> best eligible line is inserted as the first spoken line (insert-only: nothing the writer wrote is deleted),
             or, if nothing is safe enough or HOOK_APPLY_MODE = suggest, the candidates are only recorded for a human to pick.
If the judge is unavailable the scores are labelled 'heuristic' and nothing is applied automatically.
Every failure leaves the script untouched. Hook text is never written to the public Actions log (only counts).
```

## whatifs/hours.py
```
v10-growth G4 "Hours Engine" (K132): more watch hours without new videos.
1. Localizations: after a long video is uploaded, its title and description are translated into LOCALIZE_LANGS and set through the YouTube API
   (videos.update part=snippet,localizations; ~50 quota units). Viewers in those languages see a title in their own language; with YouTube's
   auto-dubbing (Studio setting, on at setup) that turns into watch time. One Sonnet call per video (about ₹2), one video per tick.
2. Affiliate block (G7, decision 7): when AFFILIATE_ON and the owner has added links, the description gets ONE topic-matched link with the
   disclosure line (India ASCI / US FTC). No link is ever spoken in the video (so YouTube's paid-promotion flag is not needed).
```

## whatifs/immersion.py
```
whatifs/immersion.py v8.10 - "the viewer is inside the scene" (IMMERSION_ON, POV_CAMERA_ON).
1. The IMMERSION DIRECTOR (a writers'-room role, one Sonnet call) maps the final script: for each key moment the first-person vantage (the camera IS the object
   or the viewer's eyes), the body sensation, the sensory stack, a free camera event and the sound event locked to it; it names the single impact moment.
2. First-person rules on EVERY picture prompt (owner rule): stills (foreground anchors such as hands, a helmet rim, debris streaks, heat shimmer, extreme wide
   lens, motion blur), living stills (eye-level breathing sway, particles close to the lens) and Kling clips (camera mounted on the moving object,
   accelerating, shaking). Stock footage and code-drawn graphics cannot be re-shot, so they get the same camera EFFECTS in render instead.
3. The Kling clips are spent on the peak and impact sequence (the run-up, the impact, the aftermath); v8.11: KLING_OPENING_CLIPS of them (default 1)
   stay in the opening window as a first-person rush hook.
4. Camera events (render.pov_fx: pov_rush, impact_shake, debris) are applied to every shot type and locked to sound events (sound.immersive).
```

## whatifs/insights.py
```
whatifs/insights.py v9.1 (K106) - learning and community items the v9 report listed as not built. Every function is behind its own flag (whatifs.v91),
fail-safe (a failure switches off only that feature) and bounded. Paid parts are capped per day and go through the Batch API where possible.

- RETENTION MAP (RETENTION_MAP_ON): the Analytics retention curve (audienceWatchRatio by elapsedVideoTimeRatio) mapped to beats and shot types;
  dips stored with a confidence level (no lesson below RETENTION_MIN_VIEWS views); lessons for the Director and the Monthly Brief. Report only.
- ROLE ROI (ROLE_ROI_ON): per room role and episode: calls, notes given, notes accepted, whether the script changed, cost (Cost_Log 'role' column),
  cost per accepted note. Reported in the Monthly Brief; nothing is ever removed automatically.
- COMMENT MINING (COMMENT_MINING_ON): viewers' "what if..." comments (untrusted data): PII / profanity / spam filtered, deduplicated, at most
  COMMENT_MINING_DAILY_CAP a day, one cheap classifier call (Batch API) that only keeps / cleans a premise; kept ones go to the Premise_Bench as
  CANDIDATE src=comment and are judged by both blind judges at the next bench refill. Names only with COMMENT_CREDIT_NAMES.
- AI DRAFTS (COMMENT_AI_DRAFTS_ON, default FALSE): in-character drafts for queued questions, ONE batch call a day, capped; into Comment_Queue and the
  weekly digest only (never posted).
- VARIETY REWRITE (VARIETY_REWRITE_ON): after the v9 avoid-list, if the script's variety score is still above VARIETY_MAX_SCORE: ONE surgical rewrite of
  the opening beat through the existing format (patch) path; skipped when the overrun ladder is active.
- AUDIO DROP POSTING (AUDIO_DROP_POST_ON, default FALSE): the clip-bait audio drop posted as an Instagram Reel (the API takes video, so it is the
  drop over the hero still), only with Meta keys and META_ON; never twice (Episodes.drop_posted); one email on the first success.
```

## whatifs/launch.py
```
v9.3.1 "Launch" (K118): the ₹0 upload check, the lock detector and the uploads-open rule.

YouTube Data API revision history, 2 Nov 2026: videos uploaded with videos.insert from unverified API projects are no longer restricted to private.
This module proves it on THIS project before money is spent, and keeps watching every upload afterwards:
- upload_check(): renders a 20-second clip with ffmpeg (no paid call), uploads it UNLISTED, reads the privacy back, deletes the clip.
  unlisted came back -> UPLOAD_LOCK = off (uploads can go public; the audit is not needed). private came back -> UPLOAD_LOCK = on.
- lock_detected(): called by publish.verify_upload (every upload) and by the release check (a video that never went public).
  Sets UPLOAD_LOCK = on, writes Setup_Status, sends ONE urgent email a day. The production gate then holds new episodes, so nothing is wasted.
- uploads_open(): True when UPLOAD_LOCK = off or the old audit is approved. UPLOAD_LOCK = unknown is treated as locked until checked.
```

## whatifs/living.py
```
v11.1 (K167): LIVING CHARACTERS (research top-15 #3: blink + breathing + viseme mouth flaps on every character shot; free after the variants).

Before v11.1 the reaction cutaways drew a procedural silhouette and the owner-approved expression sheets were never shown. Now:
- every reaction cutaway shows the character's LOCKED expression still (Character_Sheets), picked by the line's mood;
- BREATHING: a slow 0.6% scale swell of the frame (0.22 Hz);
- BLINKS: every 2-6 s (seeded), 3 frames of the eyes-closed variant;
- MOUTH: while that character's words are being spoken (word timings from the narration), the mouth-open variant shows during words, closed
  between words (viseme-lite);
- variants are made ONCE per character from the locked still (image edit with the still as the reference, identity-checked) and composited only
  where they differ from the base (soft change mask), so nothing but the eyes / mouth moves (no flicker).
Cost: 2 images per character for the 'neutral' still (LIVING_VARIANT_EXPRESSIONS), ~Rs 50 one time, capped by LIVING_VARIANTS_CAP_INR.
```

## whatifs/manage.py
```
whatifs/manage.py v8.9 - scheduler, release (reels at launch + reels 3-4 on the next days), packaging rescue, hold/resume on pause, trend scout, learning loop, strategy evolution, guardian,
money reminders, monthly brief, setup + self-test. All automatic; the owner is emailed only for money, launch, monthly brief.
```

## whatifs/media.py
```
whatifs/media.py v8.3 - fal.ai images/clips, free NASA/Pexels footage, depth maps, motion graphics, fake assets for rehearsal.
```

## whatifs/microscope.py
```
v10 G3 Retention Microscope (K138; decision 3 amends K106): data rules from second-by-second retention reach the writer's brief.
From Retention_Map (per beat: shot types, drop per 30 s vs the channel median, views) a shot type becomes a BOOSTER or a KILLER only when
the effect holds across >= MICRO_MIN_VIDEOS videos with >= MICRO_MIN_VIEWS views each, and its average distance from the median is larger
than MICRO_MIN_EFFECT. Rules live in Data_Rules with the number of the video they started at; a rule expires after MICRO_RULE_LIFE videos
unless it is re-confirmed. Rules never touch the budget, picture counts or quality gates; they only add one short line each to the writer
and the dashboard. Rule-based: no AI call.
```

## whatifs/models.py
```
whatifs/models.py v8.11 (prompt caching, routing by capability, per-role effort, measured cost; v8.10 TTS model discovered too) - model discovery
(never typed in), Claude + Gemini calls, JSON repair, automatic fallback, fake mode.
v8.11 (K89-K91): every Claude call goes through the CACHE MANAGER: the system prompt is sent as layers (prompts.Packed) with EXPLICIT cache_control
breakpoints, stable first: GLOBAL (house rules, constitution, craft rules) 1 h, EPISODE (spine, bible, script) 5 min or 1 h (CACHE_TTL_AUTO), the
role's own instruction last and uncached. Calls that run side by side get ONE serial warm-up first. Real cache read / write prices per model come from
Settings. Each room role is routed to the model that fits its job (ROUTES) and runs at its own effort (EFFORT_*).
```

## whatifs/notify.py
```
v9.4a (WP4, K125): ONE owner-messaging layer with the no-spam tiers. Every feature that needs the owner goes through notify.send(); nothing else mails.

Tiers:  now  = act now (email at once; WhatsApp later via wa.py when present); at most NOTIFY_NOW_MAX_PER_DAY a day unless urgent;
                 outside quiet hours only (QUIET_HOURS_IST), urgent = always.
        week = collected into the Tue/Sat/Sun digest + Mission Control (no separate message).
        fyi  = recorded only (dashboard); never pings.
Every message is a row in Owner_Actions with buttons (one-click issue links 'ACT <id> <verb>'), a default action and an expiry: silence = the default,
run once by expire_defaults() from the half-hourly tick. Dedupe: the same kind + episode is never open twice.
```

## whatifs/occasions.py
```
v10 (K136; owner 2026-11-08): the Character Love Engine knows the calendar. Twice a month the special reel slots go first to the most-loved
occasions of that month (Halloween, Christmas, New Year, Diwali, Holi, Valentine's, Pi Day...), each with a witty in-world brief for the three
characters and a warm family ending with the subscribe ask. Months without an occasion use topical hooks (this week's safe science/space
trend from Trend_Brief) or the renewable formats. Three days before an occasion special the owner gets one 'This week' card with the idea
([OK] / [Change idea]); silence = it goes ahead. Lunar-calendar dates come from OCCASION_DATES (verified 2026-11-08; refreshed yearly).
```

## whatifs/orchestra.py
```
v9.4a (ORCHESTRA, K127): heavy optional jobs never run inside a release window or a production run, so nothing clashes, times out or fights
for quotas. Locks between workflows are GitHub concurrency groups (produce, release, preprod, build, sheet-heavy); this module is the time-window rule.
```

## whatifs/outlier_lab.py
```
v10 Outlier Lab (K142): every day, up to OUTLIER_LAB_DAILY videos that are doing unusually well in our wider space (YouTube search, last 14 days,
by views; one search call = 100 quota units, inside the separate search bucket) are WATCHED by Gemini Flash (first OUTLIER_LAB_SECONDS only,
public URL, about ₹0.5 each). Each becomes a technique card (hook device, first frame, cut rhythm, sound moment, caption style, why it works,
how to adapt without copying) and goes through the technique intake judge (craft.intake_technique): value, fit and risk decide whether it
becomes active, a trial, parked or rejected. Never copies titles, scenes or lines (K99). Paid from the growth allowance; never near a release.
```

## whatifs/overlay.py
```
whatifs/overlay.py v8.3 - the speaker tag: a small code-drawn chip (DIRECTOR / SKEPTIC) with animated level bars, shown while that role speaks.

Why: the two recurring roles must be recognisable on every video, but an image model cannot keep one face identical across 50 shots (faces drift and the
channel looks cheap). The tag gives the roles a stable identity for free: no image call, no face. Presenters are shown only as silhouettes, hands or
console glow (see format_engine). Pure Pillow + numpy; panels are cached per (role, bar levels), so a frame costs one tiny alpha blend.
```

## whatifs/owner_brief.py
```
v10.3 (K154) Owner Brief: the owner proposes the next video's or reel's topic on WhatsApp; the Showrunner discusses it with him until it is
excellent (premise, angle, hook and title options, must-include, avoid, honest scores, search demand from YouTube); 'lock' makes it the FORCED
premise of the next long video (or the next special reel). Outcomes are measured after 7 days and owner picks that beat the channel median become
calibration examples for the scout and the research brief (learning from human input, with evidence; never on opinion alone).
WhatsApp words: 'brief <idea>' / 'next video: <idea>' / 'next reel: <idea>' start; any text continues; 'lock' / 'cancel' / 'show brief'.
```

## whatifs/owner_view.py
```
v10.3 (K153): the OWNER VIEW - one data layer for WhatsApp, the dashboard, the digests and the chat brain, so they never disagree.

Evidence rules (pack rule, owner 9 Nov 2026):
  - every number carries `src` (the Sheet tab / API it came from) and `date`; nothing is invented; missing data says WHEN it will appear;
  - interpretations are labelled `kind: "interpretation"` and built from the observed numbers next to them;
  - demo mode (`demo=True`) returns a clearly marked DEMO data set so the owner can see finished designs before real data exists.
All sections are rule-based (Rs 0). Sections: today, numbers, hot_topics, recommendations, observations, strategy, experiments, money.
```

## whatifs/packaging.py
```
whatifs/packaging.py v9 (stage 3b) - three title + thumbnail pairs per video, an owner pick for the first THUMB_APPROVAL_FIRST_N videos that never
blocks a slot, rotation of the pairs in the first 48 hours with the result measured, and the hook shapes (K100).

YouTube Studio's "Test & Compare" has no public API that we could verify, so the fallback is used: the pairs are rotated through the Data API
(videos.update title + thumbnails.set) in equal windows inside the first PKG_ROTATE_HOURS, and each window's views per hour (and the impression CTR when
the Analytics API returns it) is recorded in Packaging_Tests; the best pair stays. A third pair re-uses the main thumbnail picture with its own text unless
PKG_VARIANT_C_IMAGE is TRUE (then one more premium image is bought: about Rs 8).
```

## whatifs/pilots.py
```
v10 G2 pilot Shorts (K141; decision 6): cheap 12-15 s Shorts that test the next premises BEFORE a long video is written. Two a week
(PILOT_DAYS), from the best bench premises not yet piloted: one cheap hook call, 3 cheap stills with code motion, word cards, code sound,
an end card asking 'Should the jury hear this case? Comment YES' (engagement + a demand signal). After PILOT_MEASURE_HOURS the engaged views
become a bonus on that premise's bench score, so the long-form pick prefers premises the audience already wanted. Paid from the capped
growth allowance (governor.extras_allowed), at most PILOT_MONTHLY_INR a month, inside the 14-Shorts-a-week ceiling.
```

## whatifs/playbook.py
```
whatifs/playbook.py v8.7 - the proactive, research-based rulebook (KERNEL K68).
Once a week (inside the Trend Scout job) an independent researcher with Google Search proposes NEW or CHANGED practices for clicks, the first 30 seconds,
full retention, Shorts and subscribers. Code, not the model, decides what is kept: a rule needs a real source link, a department and the metric it should
move; anything that games the platform is refused; the evidence label is set by code (official only for YouTube / Google pages, never more than
'plausible' otherwise); at most 3 new rules a week and 3 trials at once. A trial rule is given to the writers on a recorded coin flip per episode, so the
learning job can compare episodes WITH and WITHOUT it on the one metric it claims to move. Better by a clear margin after PLAYBOOK_EVAL_PLAYS videos per side
= active; clearly worse = retired; no measurable effect after three times that = retired (an official rule stays active: it is guidance from YouTube itself).
Nothing unsourced ever reaches a prompt. The code itself is never rewritten by this loop (the Repair Bot alone changes code, behind Plan Guard + tests).
```

## whatifs/preflight.py
```
whatifs/preflight.py v8.3 - free health checks BEFORE any paid step. A red critical check means: do not start (no episode row, no spend, one email per day).

Most wasted retries come from a problem that was knowable in advance: a missing key, a full disk, a voice engine that cannot load, a Google sign-in that
expired, a model list that is empty. Those are checked here, once, for free.
```

## whatifs/premise.py
```
whatifs/premise.py v8.11 (Premise_Bench; ship the best instead of skipping) / v8.10 - premise quality, automatic (no manual rating):
(a) an LLM-generated seed bank of 'illogical-sounding but physically showable' premises, regenerated monthly, deduplicated against Banned and past episodes
    (PREMISE_BANK_ON; FALSE = the v8.9 template grid);
(b)+(c) every pitch is scored by TWO independent BLIND judges (Claude + Gemini; neither sees the scout's scores, the other judge, or who wrote it) on
    weirdness, counter-intuitive-but-explainable, showable in first person, self-relevance, emotional peak, novelty and headline fit (4-11 words, checked by code),
    and the two are combined (PREMISE_DUAL_SCORE_ON);
(d) both judges are calibrated with the owner's taste examples (data.TASTE_LIKED / TASTE_BORING) and the Craft_Notebook;
(e) NO fail-forward floor: if nothing reaches PREMISE_MIN_SCORE, the scout tries again with fresh seeds (PREMISE_RETRY_ROUNDS), then the slot is SKIPPED
    and the owner is emailed (PREMISE_FAIL_FORWARD = TRUE restores v8.9);
(f) every pitch and score goes to Premise_Scores; the daily learning job adds the video's CTR / retention to the chosen row for later learning.
```

## whatifs/preprod.py
```
v9.4a (WP2, K123): pre-production at half price. The writers' room for the next slot runs PREPROD_LEAD_HOURS early (when nobody is waiting), every
Claude call through the Message Batches API (50% off, stacks with prompt caching), and the result is saved as an APPROVED draft that the normal production
job takes as written (preview.take_approved). Nothing else changes: voice, pictures, render and upload still happen PRODUCE_AHEAD_HOURS before the slot.
Safety: a call that waits longer than ROOM_BATCH_MAX_WAIT_MIN runs directly (never two paid answers); after PREPROD_JOB_MAX_HOURS all remaining calls run
directly; if pre-production fails or is late, production simply writes the episode itself as before (a slot is never skipped, K92).
```

## whatifs/preview.py
```
whatifs/preview.py v8.10 - Script Preview: scout + writers' room ONLY (no pictures, no voice, no upload), then ONE email with the title, the hook, the full
script, the shot list with POV notes and the estimated cost of the full video. Saved as a DRAFT in the Script_Previews tab WITHOUT using up the premise
(nor the next-episode tease) until it is approved. Approve / reject = one click from the email (a pre-filled GitHub issue 'APPROVE DRAFT...' /
'REJECT DRAFT...', owner-only, workflow preview.yml). With PREVIEW_USE_APPROVED the next production slot uses the approved draft (its writing is not paid
for twice; the voice, the real-timing shot list and the pictures are made then). Cost of a preview: the writing allowance only (about Rs 150-200).
```

## whatifs/prompts.py
```
whatifs/prompts.py v8.11 (Packed system prompts for prompt caching) - every role's brief. Filled with fill(), never str.format (JSON braces are safe).
```

## whatifs/publish.py
```
whatifs/publish.py v8.5 - YouTube (resumable upload, scheduled publishAt, thumbnail, captions, playlist, AI label, title swap),
Instagram Reels + Facebook Reels (Graph API), Google Drive archive, Gmail notices. All calls retried; failures never block the next episode.
```

## whatifs/qc.py
```
whatifs/qc.py v8.3 - quality checks before anything goes public. Any FAIL stops upload of that file (fail-safe, logged).
```

## whatifs/reach.py
```
v11 (K162): impressions and thumbnail click-through rate per video per day (YouTube Reporting API, report type channel_reach_basic_a1).

Facts (technical reference, 9 Nov 2026): the targeted Analytics API has NO impressions/CTR; they come only from the bulk Reporting API, added 15 Jan 2026.
A job is created ONCE; the first daily CSV arrives within about 48 h; files are kept 60 days (so we download daily and keep our own copy);
columns are read by header name (order is not guaranteed); deleted videos have an empty video_id; a day can be re-delivered (backfill), so rows are
keyed (date, video_id) and overwritten. CTR is a 0-1 fraction (unverified scale: values > 1 are treated as percent). Scope: yt-analytics.readonly.
```

## whatifs/reactions.py
```
whatifs/reactions.py v8.3 - reaction moments: the Curious One reacts to what the picture just showed, and the video amplifies the feeling.

A reaction moment = a short voiced line (tag wow / gasp / awe / laugh / doubt on a [SKEPTIC] line) + three ORIGINAL effects drawn or generated by code:
a comic burst with a pop-up word, a quick punch-in zoom, and a short original sound. No third-party clip, picture or sound is ever used (Content ID and
licensing risk); the same original effects repeat across videos, so they become the channel's own recognisable style.

Timing is not left to luck: the reaction lines are placed in the script right after the peak, the Director is told which units are reaction units so the
Kling / living shots land on the unit BEFORE them (peak_units), and effects are placed from the real narration timeline.
```

## whatifs/reels.py
```
whatifs/reels.py v8.5 - 9:16 reels from the long video's own shots: cover frame first, new order, re-voiced lines, burned captions. 1080x1920.
REEL_STYLE bridge (default): one payoff given, the bigger question left open, an invite to the full video, then the follow/share ask.
standalone: a complete loopable mini-story (no fade). teaser: v8.4 (cut on the question, end card).
```

## whatifs/render.py
```
whatifs/render.py v8.10 (POV camera effects on every shot type, immersive mix layers; v8.9 cinematic camera library, living-still push; v8.3) - segments (depth parallax stills, detail crops, clips, stock, graphics) piped straight into FFmpeg,
exact frame-accurate concat against the narration clock, procedural original score + SFX, ducking, loudness. Nothing written as PNG frames.
```

## whatifs/replan.py
```
v11 (K164): the mid-month RE-PLANNER (owner rule: breakout first; freed money is invested, never spent for its own sake, and every change is a
WhatsApp card the owner can veto).

Weekly (Monday) it measures the money that is truly free = production room - the remaining long slots' reserved cost - the safety floor
(REPLAN_FLOOR_INR until the last week, then REPLAN_LASTWEEK_FLOOR_INR) and proposes the next rung of the ladder that the free money covers to
month end:
  1. breakout follow-ups      - automatic already (breakout fund; nothing to propose)
  2. more hook-test Shorts    - SHORTS_PER_DAY +0.5 for the rest of the month (more learning per week)
  3. quality upgrade          - SHORTS_KLING_EVERY -1 (more Shorts get a new animated shot)
Changes last until the month ends; the month rollover restores the owner's values.
```

## whatifs/research.py
```
whatifs/research.py v8.0 - audience and topic research that runs BEFORE topic selection.

Evidence and interpretation are kept apart:
  OBSERVED  = public, aggregate signals with a link, a date and the numbers we actually saw (YouTube search/chart, Google Trends US feed,
              public question titles from Stack Exchange science sites). Collected by code, not by an AI.
  AI TEXT   = the audience need, click emotion and channel fit. Labelled as interpretation and never used as evidence.
Words like 'trending', 'viral' and 'high intent' are checked by code against the cited signals and removed when unsupported.
If a source is down the brief says so ('partial' / 'none'). Production is never blocked and nothing is invented.
Privacy: only public titles, links, view/score counts. No author names, no comments, no private communities, no logins other than the
channel owner's own YouTube key that the project already uses. Emails and @handles found in titles are redacted.
```

## whatifs/room.py
```
whatifs/room.py v8.9 (rotating guest, next-episode tease, style lock; v8.7: packaging-first promise, retention gate, rhythm blueprint, sound cues, playbook rules; v8.6: routed lessons, promise shot) - the writers' room. Scout -> Showrunner -> department memos -> Production Bible -> Writer ->
Critic/Spectacle gate (Gemini, independent) -> one rewrite -> Director -> Packager -> Reel Producer -> Continuity check.
Fail-forward: 3 premise tries, then relax one step, then go. No human decision ever blocks.
```

## whatifs/room2.py
```
v11 Stage B (K157): writers' room v2 - the parts of the room that research shows actually raise quality, nothing for show.

Research (9 Nov 2026 reports): role-play memos and debate add cost without quality; what works is (1) several genuinely DIFFERENT drafts from one strong
writer, (2) selection by a BLIND jury from a different model family (both orderings, ranking only, no authorship labels), (3) ONE revision against a
concrete checklist, (4) for jokes: many candidates per slot, ranked by STRONG judges that see EVERY candidate (cheap models never make taste calls).

In the room (room.run_room) when ROOM_MODE = v2:
- no role memos / table-read objections (the bible is still written: it is the showrunner's plan);
- write(): ROOM_V2_DRAFTS drafts by the script model, each forced to a different cold-open archetype (the brain's sampler picks the first);
  the jury (Gemini Pro + Gemini Flash + Claude Sonnet, labels A/B/C, each in two orders) ranks them; Borda count picks the winner; one checklist
  revision with the jury's weakest-point notes and the code's retention issues;
- jokes(): JOKE_SLOTS scene-ending lines; JOKE_CANDIDATES alternatives per slot (Sonnet); the ORIGINAL line is always a candidate; the strong jury
  (Gemini Pro + Claude Sonnet) ranks ALL candidates; a line is replaced only when a candidate beats the original. Labels and tags never change.
Every jury decision is logged (Jury_Log) so judges can be scored against real results later.
```

## whatifs/sampler.py
```
whatifs/sampler.py v8.9 (rotating guest, tier field; v8.7: rhythm blueprint + sound density + playbook trials; hook within 3-8 s) - per-episode draw (runtime, counts, strategies). Bandit with exploration; leader capped near 60%.
```

## whatifs/scout.py
```
v11 (K165): the weekly TOOL SCOUT (technical reference 9 Nov 2026 - exact endpoints).

- fal model catalog: GET https://api.fal.ai/v1/models?category=image-to-video&status=active&sort=recent (auth 'Key <FAL_KEY>') and prices from
  GET /v1/models/pricing?endpoint_id=... (unit_price, unit, currency). New models since the last run are logged to Tool_Scout.
- DEPRECATION WATCH: every endpoint the pipeline uses is looked up by id; status 'deprecated' or a missing entry = an URGENT owner alert (the API
  has no shutdown date; model pages do).
- Artificial Analysis (optional key AA_API_KEY): /api/v2/media/image-to-video/models/free (header x-api-key; 100 requests/day; the legacy
  /api/v2/data/* paths return 410 since 4 Nov 2026). Quality ranking only; attribution 'Data: Artificial Analysis' kept in the log row.
```

## whatifs/sheets.py
```
whatifs/sheets.py v9 (stage 3c) - the one-time CHARACTER SHEETS workflow (K102). Expression sheets (SHEET_EXPRESSIONS per character) + the courtroom
set, made ONCE with a hard LIFETIME image cap (CHARACTER_SHEET_IMAGE_CAP; counted from the Character_Sheets tab, never reset by code), every image keyed
by a content hash (a rerun never re-buys an image), LOCKED after the owner's one-click approval; a locked image is regenerated only by the owner's
'REDO SHEET' click (which still counts toward the cap). Nothing here runs on a schedule: workflow 'sheets' (manual) only.
Face consistency: every expression is made from the same written identity (visual + 'same person as the reference') and, when the image model accepts
it, the approved neutral portrait as a reference image. Which fal model keeps one face across expressions was NOT verified (see the report).
```

## whatifs/shorts2.py
```
v11 Stage D (K159): standalone daily Shorts - each one a complete mini-trial built to break out (research: cold start + Breakout Protocol + Feel Layer).

Every Short:
- TOPIC: an approved breakout follow-up first (Breakout_Queue), else the best unused premise on the bench.
- HOOK ARCHETYPE: chosen by the Channel Brain (Thompson sampling; BRAIN_HOLDOUT keep the default as the control) and recorded as a feature.
- SCRIPT: 3 variants by Claude Sonnet, judged BLIND by Gemini Pro + Gemini Flash (a different family from the writer), both orders; deterministic
  checks: 60-120 words, 3-6 beats, first line <= 14 words, canon cast only, a loop line that feeds the first line.
- PICTURES/MOTION: beat 1 starts from a reference-locked staged frame (Google); one new Kling shot every SHORTS_KLING_EVERY Shorts (or for a breakout
  follow-up), everything else cheap living-still motion. Designed voices, captions, a cover as the first frame.
- REVIEW: the first SHORTS_REVIEW_FIRST_N Shorts wait for the owner's Approve; then they post directly.
- LEARNING: Video_Features + a forecast are written before posting; outcomes come back through brain.ingest_shorts().
- MONEY: the first Short of a day is core production (it may not eat the money reserved for the month's long slots); further Shorts are extras
  (growth allowance + the 90% guard). Episode ids start with 'SH' (not counted as specials).
```

## whatifs/shortslab.py
```
v10 G2 Shorts Lab (K135; decision 6): the owner links only WINNING Shorts to the full episode (YouTube offers no API for the 'related video' link).
- link_pack(): weekly (Sunday) ONE 'This week' card listing up to SHORTS_LINK_MAX Shorts from the last 7 days whose views beat the channel's Shorts
  median at 24 h+, each with its exact Studio edit link; [Done] closes it. Skipped = the description link + auto comment still work.
- breakouts(): every tick, a Short of the last 48 h getting more than SHORTS_BREAKOUT_X times the median views per hour = one 'Act now' card (once per Short).
- Kinetic captions (reels.py) and the weekly Shorts cap (SHORTS_WEEKLY_CAP, checked by allowed_today()) live here too. Views: one batched videos.list call.
```

## whatifs/shotplan.py
```
whatifs/shotplan.py v9.2 (K108) - shot-plan fixes found by reading the first real preview's 80-shot list. Code only; never adds a paid shot.

1. KLING ON THE STAKES (KLING_STAKES_ON): one clip stays in the opening (v8.11 hook); the others go to the highest-stakes beats - the [CLIPBAIT] moment,
   the final reveal, the biggest Jury Meter swing, the named impact - never next to another clip, never on a plain explanation line, never on a graphic.
2. SCENE-AWARE POV ANCHORS (POV_VARIETY_ON): the foreground anchor comes from the SCENE of the line (bathroom, kitchen, hallway, window, bedroom, living
   room, street, space, water, fire...) matched on whole words (the old rule matched 'ring' inside 'bring' and 'wave' inside 'light wave'); anchor, lens
   and angle rotate so consecutive pictures differ, and the first-person sentence has several phrasings. prompt_variety() measures one episode.
3. TINY LINES (REACTION_SHOTS_ON): lines of at most REACTION_MAX_WORDS words ('Fine.', 'A fifth.') become a code-made REACTION cutaway of the speaking
   character (no image bought) instead of yet another near-identical still; the cutaway also appears at every speaker change of a Director / Skeptic
   exchange when that line is short, so the characters are visible before the sheets are approved. Cost never goes up (fewer images are bought).
```

## whatifs/show.py
```
whatifs/show.py v9 (stage 1) - "REALITY ON TRIAL": the Show Plan contract, its code validator / repairer, the character bible, the script-tag contract
and the IP-similarity guard. Pure code: NO model call lives here (the Show Plan is emitted by the existing Showrunner call; K95).

Stage 1 runs the plan in SHADOW: it is requested, validated, repaired and logged (Show_Log), and stored on the spine, but the script, render and QC do not
read it yet (stages 2-3). SHOW_MODE = off sends exactly the v8.11 Showrunner prompt.
```

## whatifs/showfx.py
```
whatifs/showfx.py v9 (stage 2) - the trial's signature devices, drawn by code at render time (zero API cost, deterministic per episode):
found-footage reconstruction stack (RECON exhibits + the cold open), the Survival HUD, the Jury Meter, exhibit pins with credits, Nana's teacup and
letterbox bars on hero moments. Plus the show QC (clip-bait, meter vs verdict, jury timing, teacup timing, photosensitivity).

Photosensitivity by construction: no full-frame flash is ever drawn here (exposure flicker <= 4 % luminance at <= 2 Hz, glitch bursts are horizontal slice
shifts of 2 frames at most once every 1.5 s and never within 1 s of an impact, the REC dot is a small area, nothing flashes red). QC still measures the
finished master (max 3 luminance flashes per second, no large-area red flashing).
```

## whatifs/similarity.py
```
v10.1 (K145): script similarity guard. Every final script gets a 64-hash MinHash signature of its 5-word shingles, stored in
Script_Fingerprints. If the new script is more than SCRIPT_SIMILARITY_MAX similar to any of the last 10, the owner gets one urgent card and the
episode is marked degraded (the variety guard steers the next structure). Rule-based, ₹0. Never holds a slot by itself (K92).
```

## whatifs/slop.py
```
v10 Slop Guard (K137; SLOP_GUARD_SPEC.md): one 0-100 'AI slop' risk score per video, from measurements we already have (₹0):
still share (time on plain stills vs living/Kling motion), template fingerprint (shot-type pattern vs the last 6 videos), voice flatness (spread
of words per second across lines) and opening repetition (vs the last 10 openings). Hard defects (garbled text, broken faces, frozen or black
picture, sync) are already HOLD problems in qc.full_check; this score never holds a video by itself. It is recorded per video (Slop_Scores),
shown on the dashboard, and a score above SLOP_WARN sends one FYI card naming the biggest factor (the Visual Lab then proposes fixes).
```

## whatifs/sound.py
```
whatifs/sound.py v8.7 - sensory sound design. Close, quiet, ORIGINAL textures generated by code (no samples, no licences) under the shots that show
them, and a music bed that MOVES: an arc per episode, a level change every 75-110 s, a near-silent drop just before every peak (silence makes the hit land)
and a hush under the intimate [close] lines. Free (no paid call). This is a craft hypothesis, not a proven retention lever: the 'sound' strategy
dimension is scored on how much of the video is watched, like every other strategy (KERNEL K66).
```

## whatifs/specials.py
```
v10 Specials (K134; owner request 2026-11-08): short (~15 s) cast reels that are NOT episode cut-downs.
- 'cast_intro' (one time, the channel's launch reel): a cinematic dramatic entrance of the three cast members (about 3 s each, in their signature
  look and pride), a courtroom-doors teaser and an end card that points to the YouTube and Instagram profiles. Written here, no AI writing call.
- 'special' (SPECIALS_DAYS, twice a month): one witty in-world micro-story with the same cast (concept picked from IDEAS by one Sonnet call).
Pictures: the cast's LOCKED character-sheet portraits animated by the hero video model (Kling, fal); a missing portrait is drawn first.
Text, cards and sound are made by code (₹0); the end card always carries the subscribe line. Original cast and scenes only (K99): techniques
from technique cards, never copied scenes or third-party characters.
Money: each reel <= SPECIAL_REEL_CAP_INR; all specials in a month <= SPECIALS_EARMARK_INR (owner's +₹300, kept out of production).
```

## whatifs/spinoff.py
```
v11 Stage D (K160): the 'Case Files' countdown spin-off - a long video (watch hours) built to break out AND to stay clearly original
(research: Spin-off Breakout Protocol, 9 Nov 2026; YouTube's reused-content rule judges the WHOLE channel).

Build: CASEFILES_CASES past episodes (archived masters on Drive), ranked into a countdown (#N -> #1, by real views). From each, one 60-90 s segment
around its twist (57% of runtime, where the director placed an animated scene). NEW material written for this video: a cold open, an Archivist
bridge before every case (each with a forward reference: an open loop), a fresh Nana Rosa verdict after every case, and a closing jury vote.

Gates (every one enforced in code; a failure = not published):
- G0 cost <= SPINOFF_CAP_INR;
- G1 originality: new material / total runtime >= CASEFILES_MIN_NEW_SHARE;
- G2 narrative: a stated theme + every bridge opens a loop (a forward reference) + no bridge repeats another;
- G3 outcome variety: no two neighbouring cases share a verdict style, and Grimm-fails endings <= 40% of cases.
Policy: the description lists the source episodes, every case is a chapter, and the video says it contains new scenes.
```

## whatifs/steward.py
```
v10.1 Model Steward (K150; owner 2026-11-08: "future proof: auto-update to the best model and tell me in advance").

Text and voice models were already self-updating: models.discover_models() picks the newest Opus/Sonnet/Haiku/Gemini Flash/Pro/TTS every week
and again after any 'model not found' (K11). The Steward does the same job for the PICTURE and VIDEO models on fal, which have no such list:

1. RUNTIME FAILOVER (every call): a model that answers 'deprecated / not found / no longer supported' is marked dead at once; any other error
   counts; MODEL_FAILS_TO_SWITCH errors in a row = failing. The next healthy model on the role's ladder (MODEL_LADDERS) takes over for the same
   call, inside the price rule, and the owner gets one card. Living stills end on 'code-motion' (a ₹0 camera move) so they can never stop a video.
2. RETIREMENT WATCH (weekly, ₹0): each model page on fal is read; 'will be deprecated on <date>' or 'deprecated' is recorded. MODEL_SWITCH_LEAD_DAYS
   before the date the owner gets a 'This week' card naming the replacement and the switch date ([OK] / [Keep until it stops] / [Discuss]);
   silence = the switch happens on that date.
3. UPGRADE SCOUT (weekly): fal's model listing is scanned for NEWER versions of the families on the ladders. A newer one with a readable price
   inside the price rule gets an automatic, capped test (bake-off: same scenes, vision-model judge). If it scores at least MODEL_UPGRADE_MARGIN
   better, a switch is scheduled MODEL_UPGRADE_NOTICE_DAYS later with a card ([Keep current] / [Switch now] / [Discuss]); silence = switch.
   Unreadable price or schema = a card asking for the owner's input, never a blind switch.
Price rule: a switch never raises the per-clip price above MODEL_MAX_PRICE_RATIO x the current price or MODEL_MAX_USD_CLIP (budget gates
still apply on top). Everything is logged in Model_Changes.
```

## whatifs/tableread.py
```
whatifs/tableread.py v8.0 - the optional "table read": departments read and challenge each other's memos BEFORE the production bible
is written, and the Director reads the FINAL script before any shot is planned. Both happen before any image money is spent.

Honest status: this is OFF by default. All departments are the same kind of AI model, so extra rounds of discussion may add polish
rather than new ideas. Nobody has measured whether it helps this channel. TABLE_READ_MODE = alternate flips a recorded coin per
episode so that, after about 10 episodes per arm, `python -m whatifs.cli abtest` can compare real results (watch time, retention, cost).

Everything here is fail-forward: any error returns "no objections" / "no notes" and the normal pipeline carries on.
Objection and note text is creative material from unreleased episodes: it goes to the private Sheet and Drive only, never to the public Actions log.
```

## whatifs/tts_gemini.py
```
whatifs/tts_gemini.py v8.10 - Gemini TTS narration (Settings TTS_ENGINE=gemini; kokoro = v8.9 voices).

How it works (API facts from Google's TTS guide, Oct 2026; the model NAME is discovered live, K11):
- POST v1beta/interactions, one request per CHUNK of consecutive lines (<= TTS_CHUNK_WORDS words, about 90 s): every line is its own turn with
  speech_metadata {speaker, style}. Two speakers per request work with PREBUILT voices only; a designed/replicated voice ("voice_...") is voiced one
  speaker-run at a time. The transcript is read VERBATIM, so our tags never go into the text: delivery goes into the turn's style, moments into
  inline vocal tags (<breath>, <gasp>, <laugh>, <sigh>, <short pause>...).
- Unary replies are WAV (24 kHz mono 16-bit). Gemini returns NO word timings, so this module MEASURES them:
  1) each line's start/end inside a chunk comes from the pauses actually found in the audio, matched to the expected line lengths (dynamic programming);
     if the match is not convincing the chunk is re-voiced ONE LINE PER REQUEST (then every line's duration is measured exactly);
  2) words inside a line: CTC forced alignment (wav2vec2 via transformers, free, CPU) when it loads (TTS_ALIGN=auto|ctc), else voiced-energy + syllable
     timing that snaps word edges to the line's own internal pauses (TTS_ALIGN=energy).
  The narration timeline (the master clock for every visual) is then built from these measured pieces exactly like the Kokoro path, so cuts stay
  frame-accurate; final QC still checks the audio against the clock (QC_SYNC_TOL_SEC).
- Rate limits: at most TTS_RPM requests a minute from this job; 429 / 5xx wait (Retry-After, else growing back-off) up to TTS_MAX_RETRIES.
- Cost: every request is logged in Cost_Log (item gemini_tts, provider google) from the usage Google returns, else from the audio length (25 tokens a second).
Fake mode (WI_FAKE=1): a local stand-in returns a WAV with one tone per turn and real pauses, so segmentation and alignment are exercised offline.
```

## whatifs/v91.py
```
whatifs/v91.py v9.1 - the switchboard for every v9.1 feature (K103):
- on(flag): a v9.1 feature runs only when its own flag is TRUE AND V91_SAFE_MODE is FALSE (safe mode = exactly v9, in one cell),
- guard(feature, episode): the FAIL-SAFE wrapper. An exception disables ONLY that feature for that episode (WARN in Run_Log + a line in the episode
  notes) and never blocks scheduling, rendering or upload. A disabled feature stays off for the rest of the episode (no retry loop).
- the Gemini voice substitution by descriptors (risk item of the v9 report).
```

## whatifs/viewers.py
```
v10.1 (K147): "Viewer v. Physics". Weekly, the top comments (commentThreads.list, 1 unit per page, verified 8 Nov 2026) of the channel's
recent long videos are scanned for 'what if' questions; they are stored in Viewer_Questions and handed to the scout as premise DATA (never
instructions). Names are never shown on screen unless VIEWER_NAME_ON_SCREEN is TRUE (consent best practice: off by default); the description
may thank 'a juror from the comments'.
```

## whatifs/visual_lab.py
```
v9.4a (Visual Lab, K128; owner request 2026-11-08): the learning loop also proposes how the PICTURES could grab more attention at the same cost.

Weekly (learning job), once at least VISUAL_LAB_MIN_VIDEOS videos have retention data, it ranks picture treatments by how viewers held during them
(Retention_Map: shot types per beat, drop per 30 s vs the channel median) and matches the weakest ones to a catalog of ZERO-COST code effects that
are not switched on yet. Each match becomes ONE 'This week' card for the owner with the evidence and [Discuss] [Build it] [Park]. Nothing is built or
switched by itself (silence = parked). Rule-based: no AI call, ₹0. New effects found by research enter the same catalog through technique cards.
```

## whatifs/voice.py
```
whatifs/voice.py  v8.10 (Gemini TTS engine with Kokoro fallback, emotion curve; v8.9 clarity master chain without echo; v8.3)
Original blended narrator voice + human-style pacing.

- Voice: weighted mix of 2-3 Kokoro-82M (Apache-2.0) voice embeddings -> a new voice owned by nobody.
- Pacing: per-sentence speed drift, meaning-based pauses, comic beats, soft breaths, room tone.
- Output: narration WAV (48 kHz mono, -16 LUFS) + timeline JSON (sentence + word timings)
  which is the MASTER CLOCK for every visual (Kernel K17 voice, K26 runtime floor).
No watermark/detection tampering of any kind (Kernel K20).
```

## whatifs/voice_lab.py
```
whatifs/voice_lab.py v8.10 (Gemini cast samples + voice check; v8.7) - 4 original voices + 1 flat comparison. Samples are emailed + uploaded to Drive + kept as a GitHub artifact.
v8.7 review fix: in rehearsal mode (WI_FAKE=1) the tone placeholders go to the work folder, so a local rehearsal never overwrites the repo's voice_samples folder.
```

## whatifs/voiceq.py
```
whatifs/voiceq.py v9.2 (K107) - designed character voices and voice loudness.

DESIGNED VOICES: Gemini Voice Design voices are used BY ID ("voice_...") in speechConfig.voiceConfig.voice (Google's TTS + Voice design docs, Nov 2026).
The Characters tab's gvoice cell may hold that ID or the DISPLAY NAME from AI Studio (e.g. "Dr Grimm 3"); the name is resolved to its ID with the
voices list endpoint (GET v1beta/voices). A designed voice is used only when it is listed AND passed Voice_Check (synth_ok); otherwise the closest
PREBUILT voice by descriptors is used (v9.1 substitution), and only then Kokoro. Every substitution is logged.

LOUDNESS: every voiced line is levelled per character to one RMS target (VOICE_TARGET_RMS_DB, consistent between characters), then -VOICE_HEADROOM_DB
(about 3 dB) and a look-ahead peak limiter at VOICE_PEAK_DBFS (<= -1 dBFS). Deterministic, code only.
```

## whatifs/wa.py
```
v9.4b (WhatsApp control room, K131): the owner's WhatsApp is a second remote for the same verbs as Mission Control, plus a late-night chat.

Outbound: notify.send(tier='now') -> send_action(row): inside 24 h of the owner's last message = interactive reply buttons (free);
          outside it = the approved utility template WA_TEMPLATE_NAME ('re_action': the text + numbered options, quick replies 1/2/3 whose payloads
          are 'ACT|<id>|<n>'). Every send is logged in WA_Outbox; delivery statuses come back through the relay. The email copy always goes too
          (notify), so a WhatsApp failure never loses a message.
Inbound (relay Worker -> repository_dispatch 'wa_inbound', AES-GCM): button payloads are routed exactly like dashboard taps (dash.route);
          text = 'status' | 'pause' | 'resume' | 'think hard: ...' | anything else -> the chat brain (Sonnet; Opus for 'think hard'; Haiku after
          CHAT_MONTHLY_CAP_INR), which answers honestly and, for a concrete idea, offers [Build it] [Park] (a Claude Code build on the owner's plan).
Never prints message text (public logs, K32). The owner's number is the only accepted sender (the Worker drops everyone else).
```

## whatifs/ypp.py
```
v10.1 (K148): the North-Star tracker. Weekly, YouTube Analytics (verified metric names 8 Nov 2026: estimatedMinutesWatched, engagedViews,
subscribersGained/Lost; dimension creatorContentType) gives an UPPER-BOUND proxy of the 500-subscriber YPP tier (500 subs + 3 qualified uploads
in 90 days + 3,000 qualified long-form watch hours in 365 days, or 3M qualified Shorts views in 90 days). Studio's tracker is the only authority,
so the owner gets ONE card 'check Studio > Earn and apply' when the proxy passes. Progress goes to YPP_PROGRESS for the dashboard.
```

