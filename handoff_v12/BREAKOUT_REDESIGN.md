# BREAKOUT REDESIGN - Reality Engine (11 Nov 2026)
Authority: the owner's free hand, item 17 of `02_OWNER_VERBATIM.md` ("IF YOU HAVE TO REDESIGN CHANNEL, DO IT ... SO DO IT AS PER YOU NOW"), given after he
rejected the first live video (item 16). This page OVERRIDES `01` section 1 ("concept truth, do not re-open"), the order of the batches in `03` and
the department list in `01` section 2 wherever they differ. The budget is unchanged: Rs 5,000 a month for everything.
Status: DESIGN (research + designs + decisions). Nothing on this page is built yet; the batches in section 6 build it, one per owner "continue".

## 0. THE HONEST FRAME
- Nobody can make a channel a sure shot. Of 137,355 new long-video channels, 30.8% got even ONE video past 10,000 views in their first ten (R1).
  What can be built is a machine that takes more shots, learns from real viewers after every one, and stops spending on what they ignore.
- The money bar: ad revenue needs 1,000 subscribers AND (from 1 Feb 2027, for new applicants) 8,000 watch hours on LONG videos in 365 days (R5).
  Shorts hours do not count and Shorts ads pay only channels with 10 million Shorts views in 90 days (R5). 8,000 hours = 480,000 minutes: about
  140,000 views of a long video watched 3.5 minutes on average. So: LONG VIDEOS ARE THE MONEY PRODUCT; Shorts win subscribers and test ideas.
- Science and education is the right lane for money: median long-video RPM USD 10.22 against 2.43 for entertainment (R6).
- Realistic time: a year or more. The first real video from the new code is the first real evidence (the new code has only ever run in fake mode).

## 1. EVIDENCE (E = measured, O = opinion / practice / vendor; "read" = the build session read the page itself, else reported by a research run)
R1 E read. vidIQ, "First 10 Videos Study", 28 Jul 2026 (448,413 channels created Jan-Jun 2025; views at 30 days):
   https://vidiq.com/es/research/youtube-first-10-videos-study/ - median first Short 1,362 views, first long video 180. Best of the first ten
   reached 1,000+ views for 86.5% (Shorts) vs 57.8% (long) of channels and 10,000+ for 48.0% vs 30.8%. Per video 10,000+: 20.9% vs 10.0%. Shorts
   do NOT improve with practice (1,362 -> 1,344); long videos do (+51%, 180 -> 272). Observational, survivors only.
R2 E. Metricool, "YouTube Trends 2026", 29 Jul 2026 (799,718 videos, 71,177 accounts): https://metricool.com/youtube-trends/ - 2 to 4 posts a
   week give the best views per post in both formats; channels posting about 5 Shorts a month average 8,789 views per long video (5,985 overall);
   at 35+ Shorts a month the long videos fall back to the level of channels that post none. Shorts are watched about 16 seconds on average.
R3 E. AIR Media-Tech, 18,000 English channels, Mar 2025-Mar 2026 (updated 28 May 2026):
   https://air.io/en/audience-growth/do-youtube-shorts-help-your-long-form-videos-grow-data-from-18000-channels - best mix about 25-40% Shorts by
   upload count; above 55% long videos decline; education +37% subscribers with a mix; a sudden change of the mix (30+ points) performs badly.
R4 E. PPC Land, 28 Mar 2025: https://ppc.land/youtube-changes-how-shorts-views-are-counted-from-march-31/ - since 31 Mar 2025 a Short counts a
   view when it starts; "engaged views" is the old meaning and the one the Partner Program uses. Raw Shorts views overstate interest.
R5 E read. Tubefilter, 10 Aug 2026: https://www.tubefilter.com/2026/08/10/youtube-partner-program-ad-eligibility-requirements-shorts/ - from
   1 Feb 2027 new applicants need 8,000 watch hours in 365 days or 20 million Shorts views in 90 days; current partners keep their status; Shorts
   ads only for channels with 10 million Shorts views in 90 days. (The 9 Nov digest in `04` had the same fact independently.)
R6 E. AIR, 300 channels, May 2025-May 2026 (updated 1 Oct 2026): https://air.io/en/air-data-findings/youtube-monetization-statistics-2026 -
   median long-video RPM: Education and Science USD 10.22 (quartiles 2.31-19.50), Entertainment 2.43; Shorts RPM USD 0.02-1.48 per 1,000 views.
R7 E. Inauthentic content: Social Media Today, 13 Jul 2025
   (https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/): the rule targets
   "narrative stories with only superficial differences between them"; AI tools are allowed; the WHOLE channel loses monetisation. TechCrunch,
   20 Jul 2026 (https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/): template / repetitive content
   is not monetisable; AI-assisted videos with original commentary and distinct storytelling stay eligible. The Next Web, 15 Jun 2026
   (https://thenextweb.com/news/youtube-ai-slop-crackdown-faceless-creators-collateral-damage): 16 channels with about 35 million subscribers
   were terminated in Jan 2026.
R8 E. AI label: TechWyse, 2 Jun 2026 (https://www.techwyse.com/news/platform-updates/youtube-automatic-ai-labels-disclosure-may-2026): since
   27 May 2026 YouTube labels undisclosed PHOTOREALISTIC AI by itself; animated / unrealistic content needs only a note in the description.
R9 E. Pre-publish prediction is weak. SnapUGC challenge report, arXiv 2509.02969 (Sep 2025): the best systems reach a rank correlation of about
   0.44 with real engagement. "Multimodal LLMs as Synthetic Participants in Video-Based Studies", arXiv 2606.07541 (1 May 2026): limited agreement
   with 673 human ratings, scores squeezed toward the middle. arXiv 2609.25010 (3 Nov 2026): a panel of ten personas ranked headlines WORSE than
   one generic reader. arXiv 2508.02516 (4 Aug 2025): models that hear the audio predict better than models that only see frames.
R10 E. YouTube Help (2026), https://support.google.com/youtube/answer/16559650 and /answer/9314415: "The initial seconds of your content are when
   viewers decide to stay or move on"; the Intro metric is the share still watching after 30 seconds; align title and thumbnail with the content.
R11 O. TechSmith (2025, vendor study, 768 viewers, https://techsmith.com/blog/ai-voices-avatars-in-training-videos): a high-quality synthetic
   voice held viewers as well as a human one; the QUALITY of the voice mattered more than human vs synthetic.
R12 E. Voice ranking (Artificial Analysis Speech Arena, read 11 Nov 2026, https://artificialanalysis.ai/text-to-speech/leaderboard): the newest
   Gemini Flash TTS scores 1283, the 2.5 generation 1069 - a large step at the same Google price (USD 9 per million audio tokens to 31 Dec 2026,
   USD 18 after: about USD 0.03 a minute of speech). The top voices (1338) need a subscription the owner does not have.
R13 E. Video models (Artificial Analysis image-to-video board, read 11 Nov 2026, https://artificialanalysis.ai/video/leaderboard/image-to-video;
   fal model pages): the model we pay for today (Kling 3.0, 1000 points, USD 0.084-0.14 a second) is neither the best nor the cheapest. Several
   models score 1100+ at USD 0.035-0.08 a second; one at 959 costs USD 0.045 a second on fal. Availability on fal and vertical / start-image
   support were confirmed for only some of them - the tool scout must rank what is really offered (open point O2).
R14 E (ours). The first live video (item 16): 13:13, 10 views; its Short got a few hundred. Measured: 6 pauses in 13 minutes, loudness range 4.1 LU,
   peak above full scale, no captions, 7+ number cards, 20 seconds of animation, the promise never shown, one frame in four a black shape.
WHAT THE EVIDENCE DOES NOT SETTLE (so the machine must test it, section 5): no dated case study of a from-zero faceless what-if channel was found;
no controlled study of narration pace, number density or cuts per minute; retention and click-through "benchmarks" on the web conflict; whether a
Short's result predicts its long video is unproven; how YouTube's reviewers judge AI narration + AI pictures with original scripts is unproven.

## 2. WHAT FOLLOWS FROM IT
1. Our flop is the NORMAL first long video (180 views is the median). The channel is not broken; the first shot missed and nothing learned from it.
2. Only long videos earn (R5), long videos improve with practice and Shorts do not (R1): the machine must get good at LONG videos.
3. A new channel's long video gets almost no viewers at first, a Short gets 7 times more (R1): real viewers can be reached cheaply only through
   Shorts. So Shorts are our test bench - but few of them (R2: about 5 a month helps, 35+ hurts; R3) and never as the product.
4. A simulated audience cannot pick winners (R9). It can only refuse the obviously bad. Real viewers decide; code measures what can be measured.
5. Repeating one template is the one thing that kills monetisation for a whole channel (R7). A rigid trial with the same devices every episode is
   a business risk, not only a taste problem. A stylised (not photoreal) look keeps the AI label off the player (R8).
6. Better voice and three times more animation cost almost nothing extra if the tools are chosen by value (R12, R13).

## 3. DESIGNS CONSIDERED (scores 1-5: breakout odds / speed of learning / path to money / fits Rs 5,000 / policy safety)
A. Fix the weekly long show only (better voice, captions, fewer numbers): 2 / 1 / 4 / 4 / 3 = 14. Four blind bets a month.
B. Daily AI Shorts: 3 / 5 / 1 / 2 / 1 = 12. Shorts do not earn below 10 million views (R5), 35+ a month hurts (R2), highest ban risk (R7).
C. One fully animated hero film a month with the whole budget: 2 / 1 / 2 / 3 / 4 = 12. One shot a month.
D. (ORIGINAL, CHOSEN) HOOK-FIRST PRODUCTION run by a portfolio manager: the first 30-40 seconds of every long video are made first, fully
   animated, and published as a Short; real viewers judge the hook in 48-72 hours; only hooks that hold viewers get the rest of the money;
   the long video opens with the proven hook; a Strategy department moves the budget toward what works and informs the owner:
   4 / 4 / 4 / 4 / 4 = 20.
Why D: it turns 4 blind bets into 6-8 tested hooks a month for almost the same money (the Short's pictures are reused as the long video's opening),
it spends the expensive part only after real viewers said yes, and it aims at the only thing that pays (long watch hours).

## 4. THE REDESIGN
### 4.1 The product (what a viewer gets)
- Brand stays Reality Engine. The promise stays the owner's own: IT HAPPENS TO YOU - first person, inside the scene, your body. One changed law of
  nature per video, in the Science and Education lane.
- A FORMAT is data, not code. Two formats start; the data decides their share (never one template):
  F1 "The day it changed" (default, 70%): you live one day in the changed world - the impossible picture first, then consequences that escalate
     from your bathroom to your street to the planet, one beautiful or terrible last consequence, a verdict ("would you keep it?").
  F2 "The trial" (30%, an experiment arm): the Toybox Noir courtroom the owner designed on 9 Nov, with the same hook-first opening.
- Two voices at most in a video (a guide and a foil), designed, warm, with room to breathe. No black shapes ever: a character is drawn or absent.
- 8:10 to 9:00 minutes (mid-roll ads need 8). One idea. Numbers are rare. Captions always on screen.
### 4.2 The production recipe: HOOK-FIRST
1. Idea with outlier evidence -> title + thumbnail + the one-sentence promise (packaging before script, as today).
2. THE HOOK (30-40 s, vertical and horizontal cut from the same clips): second 0-3 SHOWS the promise in motion (the best animated shot of the
   whole video), then two consequences, then an open question. Fully animated.
3. Published as a Short. After 48-72 hours the brain reads: engaged views / views ("stayed"), average share viewed, shares, subscribers gained -
   against the channel's own last ten Shorts and against the Audience department's prediction.
4. PROMOTED hooks get the long video (its first 30-40 seconds ARE the hook; 30+ more animated seconds at the later peaks). A weak hook gets one
   rewrite or the idea is dropped - the saved money goes to the next idea. In the first month, with no baseline: the best 4 of 6.
5. The long video goes out 5-7 days after its Short, linked from it; one more Short is cut from its best moment.
### 4.3 The viewer's seat - NEW DEPARTMENT D13 AUDIENCE
Nobody in the organisation sat where the viewer sits. D13 does, with a veto before anything is published.
- MEASURED by code (hard): the promise is visible within 3 s (Short) / 5 s (long); captions present; the voice breathes (a pause of 0.6 s or more
  at least every 30 s, loudness range at or above a floor, true peak at or below -1 dBTP); numbers budget (spoken and on screen; no number card in
  the first 60 s, at most 3 a long video); no black-shape character; the ending is a scene; title, thumbnail and first seconds tell one story.
- JUDGED (a floor, never a forecast - R9): one generic first-time viewer per model family (no personas), hearing the sound, comparing the new video
  PAIRWISE against reference videos. Calibration in every session, like the Review Board's canary: the owner's rejected video (YouTube id
  7RPT4rCuP6k) must LOSE to every reference and the new video must BEAT it; a jury that does not see that is void.
- LABELS: the owner's own verdict on a video (one tap + one line) is the strongest label D13 has; real retention is the second. D13 writes down a
  prediction for every video and is scored against what really happened (B5's pre-registered predictions) - a D13 that cannot predict loses weight.
### 4.4 The CEO - D1 STRATEGY, built now, not in B9
"The brain must make such decisions proactively, inform me and implement" (item 17). D1 owns the PORTFOLIO as levers (through the Execution Engine):
- long videos a month (start 4, bounds 2-6); hook Shorts a month (start 6, bounds 4-8); uploads a week (2-4, R2); share of each format;
  the promotion bar; animated seconds per video; the split of the month's money.
- DECIDES ALONE, INFORMS, IMPLEMENTS (one line in the daily brief, one tap to undo): anything inside those bounds and inside Rs 5,000.
- ASKS THE OWNER FIRST (one card): the channel's name, leaving science and education, money above the cap, deleting a published video.
- RULES IT MUST FOLLOW: a format arm that is below the other arm's lower quartile after 8 long videos loses half its share, after 12 it is retired;
  a rule that does not predict (for example "a good hook Short means a good long video", after 12 pairs) is dropped; the mix changes by small
  steps (R3). A monthly strategy review may re-open anything on this page, with evidence.
### 4.5 Departments (changes only)
| Dept | Change |
|---|---|
| D13 Audience | NEW: the viewer's seat, measured viewer checks, the reference set with the canary, the owner's verdicts, predictions scored |
| D1 Strategy | Rewritten and moved forward: the portfolio, the promotion rule, decide-inform-implement, format arms, the monthly strategy review |
| D4 Writers | Writes for the ear: one idea, formats as data, a numbers budget, the hook first |
| D5 Packaging | One story across title, thumbnail and the first 3 seconds |
| D6 Visuals | Hero model by value (arena points per dollar, vertical + start image); animation where the promise is; a drawn cast or none |
| D7 Sound | Voice model by arena rank inside the owner's accounts; direction, pauses, loud / quiet contrast, peak limit; captions |
| D8 QA | The contract in three tiers (4.6); devices are no longer forced |
| D9 Publishing | The hook-first calendar, the link from a Short to its long video, the AI note in the description, variety across uploads |
| D10 Learning | Baselines per format; reads retention curves; tells D1 which hooks earned a long video; scores D13 |
| D11 Finance | The month's money as a portfolio (4.7) |
| D2 R&D | Standing questions: what broke out in our lane this week; which video and voice model gives the most for a dollar |
### 4.6 The contract in three tiers (the device diet)
- TIER 1, always hard: policy, accuracy (exhibits with real sources stay), safety, money, technical quality, the organisation's own checks.
- TIER 2, hard: the viewer's seat (4.3). This is the new gate before picture money (script) and before upload (final).
- TIER 3, advisory per format: the devices (time ladder, prototype beat, joke every N seconds, asks, tease ...). A device becomes a "must" for a
  format only when the learning core shows it helps THAT format; none is forced because a list says so. The trial format keeps its own devices.
### 4.7 Money (Rs 5,000; today's fixed parts: maintenance 100, specials 300, earmark 200, the organisation's thinking 420 now and 610 later)
- About Rs 3,790-3,980 for production. One topic = hook Short + long video sharing the same animation: about Rs 650-700 (60-70 animated seconds
  at about USD 0.04 a second is about Rs 260; stills, writing, voice as today minus the forced devices). 4 topics = about Rs 2,800.
- 2 hooks that are not promoted: about Rs 170 each. A "double down" reserve of about Rs 500 for a winner (a second long video, more Shorts).
- Voice: about Rs 30 a video even at the 2027 price. No new subscription.
### 4.8 Staying payable (R7, R8)
Every video differs in substance and in structure (formats, verdicts, openings rotate; a check compares each upload with the last ten); the
script is original writing with real sources; the look is stylised, never photoreal people; the description says how the video was made.

## 5. HYPOTHESES THE MACHINE MUST TEST (each gets a pre-registered prediction and a date)
H1 a hook Short's "stayed" and share viewed predict its long video's 30-second retention. H2 more animated seconds raise retention at the points
where they sit. H3 the numbers budget raises the share viewed. H4 two voices hold better than one. H5 F1 beats F2. H6 the D13 floor removes videos
the owner would reject (measured by his verdicts). A hypothesis that fails changes the plan; D1 reports it.

## 6. THE NEW BATCH PLAN (one batch per owner "continue"; every batch runs the full seven-step loop; standing rules 1-4 unchanged)
| Batch | What | Done when |
|---|---|---|
| V1 | THE VIEWER'S SEAT: department D13; the measured viewer checks; the judged floor with the canary; the owner's verdict as a label; length 8:10-9:00; voice model by rank | a flop-like episode is HELD in the rehearsal; each check proven both ways; D13 wired; sweep + GitHub green |
| V2 | HOOK-FIRST PRODUCTION: formats as data (F1, F2); the hook made first and reused as the opening; hero video model by value; the three-tier contract; cast drawn or absent; cost model; CONCEPT page rewritten | a fake hook Short and its long video share clips; devices no longer force a hold; costs inside the cap |
| V3 | PILOT ON REAL SERVICES: a test Sheet, private uploads, 2 hook Shorts + 1 long video, a step-by-step guide for the owner | the owner has WATCHED real output of the new code and given his verdicts; what reality broke is fixed |
| V4 | THE CEO AND THE LADDER: D1 wired (portfolio levers, promotion, decide-inform-implement, format rules, monthly review), D11's split, the calendar | a rehearsal month: hooks tested, 4 promoted, one decision taken, the owner informed, one undo |
| B6b | The Council (as planned; it now also hears D13 and D1) | as in 03 |
| B7 | The repair loop (as planned; a viewer-seat failure gets ONE automatic repair before a hold) | as in 03 |
| B8 | The learning loop (as planned; plus the hypotheses of section 5 and D13's score) | as in 03 |
| B9 | The Owner Office D0 (as planned, without D1) | as in 03 |
| B10 | Integration, full rehearsal, docs, the hand-over package | as in 03 |

## 7. WHAT ONLY THE OWNER CAN DO
1. TODAY: Settings cell PAUSED = TRUE on the live Sheet - the old code will otherwise publish the next video like the first and spend the month.
2. At V3: follow the pilot guide (about 20 minutes, step by step), then watch three videos and give each a verdict.
3. Each week after launch: 30 seconds per release - a thumbs up or down and one line. It is the machine's best teacher.

## 8. THE OWNER'S ACCOUNTS (as the files record them; live balances are only in his Sheet)
fal (prepaid; Settings cell FAL_FUNDED_USD, default 10), Anthropic API (prepaid; ANTHROPIC_FUNDED_USD, default 25), Google Gemini API (Tier 1
prepaid; text, pictures and the Gemini voices), Claude Max until 10 Dec 2026, then Pro (this build and later code changes run on it at no API
cost). No ElevenLabs or other voice subscription. Nothing in this redesign needs a new account.

## 9. OPEN POINTS
O1 The numbers in 4.3 and 4.2 (0.6 s pauses, 3 number cards, 30-40 s hooks) are starting values from the owner's verdict and practice, not from a
   controlled study: they are levers, and section 5 tests them.
O2 Which better-value video models are really on fal with vertical output and a start image must be read by the tool scout at V2 (prices seen on
   two fal pages disagreed with each other).
O3 The Partner Program bar: the 1,000-subscriber rule after 1 Feb 2027 was not restated by the source.
O4 9 batches remain; Claude Max ends 10 Dec 2026.
