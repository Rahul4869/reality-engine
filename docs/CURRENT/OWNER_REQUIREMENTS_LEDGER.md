# OWNER REQUIREMENTS LEDGER - Reality Engine ("Reality on Trial")
Single source of truth for EVERYTHING the owner asked for, what was decided, and exactly HOW each point is applied in code.
Read this first in every build chat. Never ask the owner to repeat a point listed here. Updated 14 Nov 2026 (v12 build, batch V2b; section I carries his words of that day).
Companion files (all in docs/CURRENT): ENFORCEMENT_MATRIX.md (requirement -> code check, test-enforced), SYSTEM.md (what the code does, generated
from the code), CONCEPT.md (the show). Anything in docs/ARCHIVE is history and is never followed.

---------------------------------------------------------------------------------------------------------------------------------------
## A. HOW THE OWNER WANTS THE WORK DONE (standing rules)
1. **Hard enforcement, never "for namesake".** Every agreed requirement and every researched breakout technique must be BUILT and HARD-ENFORCED in
   code (blocks the video, or is built into production), with a test proving it. Researching or "including" it is not done. (10 Nov, emphatic)
2. **Breakout is the primary goal; money second; saving money is NOT a goal.** Savings only matter because they buy more breakout attempts. Every output
   (long video, Short, spin-off) is engineered for breakout ("do or die" urgency, pervasive, every aspect, crazy-level techniques).
3. **Do the maximum yourself.** The owner has 1-2 minutes a day, phone only. Any step needing him is pre-filled and babysat step by step.
4. **Never make him retype.** Track everything already said (this file). He hates repeating requirements.
5. **Brutally honest, sharp, witty.** Say what is not built. Never claim done before tests prove it.
6. **Build in stages; test everything for real;** report faults found and fixed; never break what works; full suite + rehearsal before packaging.
7. **Pipeline strictly structured:** timings, buffers, retries, timeouts, fallbacks; no stale references; no silly faults; nothing that makes him come
   back to repair code during setup with Sonnet.
8. **Writers' room must learn** from research / R&D / the channel's own data every time.
9. **Memo / department idea (owner suggestion):** separate sessions passing structured memos, judged objectively by another session in its role -
   adopted where research supports it (parallel drafting + blind cross-family jury), with cost/timing planned.
10. Mobile replies: answer first, short, minimal formatting.

## B. CONCEPT (decided)
- **Channel:** "Reality on Trial" (brand Reality Engine). Courtroom where a science what-if is on trial. Cast: Inspector Vale (calm noir detective),
  Dr. Grimm (theatrical mad scientist; prototypes always fail), Nana Rosa (blunt grandma judge; verdict opens "Here's what's true"), the Archivist
  (narrator / evidence keeper). Look: Toybox Noir (stop-motion puppet). Owner confirmed this as THE build on 9 Nov after exploring alternatives.
- **Explored and NOT adopted (do not re-propose unless asked):** plain what-if / "who would win"; "Science verdict" packaging tweak; "Sentenced" (real
  nature charged with crimes - "boring"); small-claims court. "CASE FILE: YOU" is parked (viewer-as-victim whodunit, nostalgia/ASMR seasoning, personified
  culprits) was liked as a premise but the owner chose to complete Reality on Trial. Its ideas (personified culprits, sensory first-person cold opens,
  nostalgia texture, rituals, ARG lore) are a possible future upgrade, not current scope.
- **Owner's taste (applies to all writing):** people must RELATE and FEEL ("it happens to YOU", first person, inside the scene, my body); the product
  is a feeling (dread, wonder, scale, awe, shock) with witty relatable humour, never a lecture; weird, mind-piercing titles; edgy, non-monotonous;
  characters to love; a return factor; never one more channel in a crowded pool; avoid AI slop and repetitive templates; appeal to non-science
  viewers too; Tier-1 audiences (US/UK/CA/AU), high RPM, sponsor-ready.
- **Inspiration noted (9 Nov):** Instagram pages Soft Respawn and Zuni HR - first-person nostalgia, "ASMR for eyes and ears". Copy grammar, never IP.

## C. MONEY (decided)
- November 2026: Rs 4,000 approved for the rest of the month on top of ~Rs 1,226 spent -> cap 2026-11 = Rs 5,226 (MONTH_CAP_OVERRIDES, written once).
- From 1 Dec 2026: Rs 5,000/month all-in. No new subscriptions. Stack: Claude API, Gemini (text/image/designed TTS), fal (the hero clip model is
  picked by value from the table `CLIP_MODELS` and bought by the second - batch V2d-a, section H; stills brought to life by a model of the same table, licensed for commercial use - batch V2d-b; FLUX stills), ffmpeg, GitHub Actions, Google Sheet + Drive,
  Cloudflare Worker, WhatsApp, Meta.
- Breakout fund: last month's unspent carries over, capped Rs 1,000, ONLY for breakout follow-ups (ids starting BRK). Owner-approved.
- 90% guard: extras pause (spin-offs, tool tests, follow-up Shorts), one alert; long-episode money is reserved first and the Shorts of the
  cadence keep theirs.
- Freed money is offered to the owner as one more Short a week (the re-planner's card, which he can veto); the change undoes at month end.
- Never cut: packaging tests, accuracy pass, the opening Kling scene, the reserve.

## D. GROWTH / YPP FACTS
- YPP until 31 Jan 2027: 1,000 subs + 4,000 long-form hours (or 10M Shorts views/90 days); from 1 Feb 2027: 8,000 hours or 20M Shorts views.
  Shorts hours do not count. Honest odds: 4,000 h by 1 Feb needs a breakout; base case 8,000 h ~months 8-12. Checkpoint 11 Jan.
- Launch cadence: 4 long videos + 12 Shorts a month (3 a week; every topic starts as a Short - owner, 11 Nov 2026, and the redesign he ordered)
  + 2 spin-offs (Case Files countdown, Deep Trial) per month; spin-offs also breakout-engineered. No other short video goes out: a long video makes no cut-down reels,
  and the pilot Shorts and the special reels are paused by default (batch V2c-b2b2).
  Confirmed by the owner on 10 Nov 2026 ("4 a month") and enforced: `STANDARD_MAX_LONG_PER_MONTH` = 4, `PUBLISH_DAYS` = Sat (one a week),
  one-time Sheet move `manage.v12_upgrade`, gate `governor.can_start_episode`; lines for viewers say "every week".
- Owner asked how watch hours work with fewer long videos: long videos + spin-offs earn hours; Shorts are discovery that funnels to long videos.

## E. RESEARCH CONCLUSIONS THAT ARE NOW RULES (and where they live)
| Research point | Rule in code |
|---|---|
| Idea-first: greenlight ideas with >=5x outlier evidence | contract `idea_evidence` (once >=10 outliers collected) |
| Packaging before script; promise contract; promise on screen early | packaging before shots (episode.py); contract `promise_paid` (<=30 s); promise re-aimed after the Animation Director |
| Hook: question / "you" stake by 3 s; hook lab | contract `impact_map` (V1), `hook_lab`, `cold_open` |
| Retention: but/therefore, re-hook <= 75 s, loops close, open on YOU, no lore in 20 s | contract `retention` (hard) + one mandatory fix (enforce.fix_all) |
| Laugh density >= 1/15 s in a long video whose format requires it; joke tournament (many candidates, strong judges see all) | contract `joke_density`; room2.jokes |
| Pause-then-punch 300-700 ms | built into voice timing ([PUNCH] marker -> 0.5 s), measured by `impact_map` (V6) |
| One send moment + one awe peak per video | contract `send_and_awe` |
| Visual change every 2-4 s (Shorts 1-2 s), no overload | built into render (shotplan.pieces_for), contract `visual_change` (V2/V5) |
| No frame reads as a still (parallax, particles) | world particle layer (render.Particles), contract `aliveness` (edge-masked detector, 1080p-calibrated) |
| Blink + breathing + mouth flaps on character shots | living.py (locked expression art + variants), contract `living_characters` |
| Sound: per-world beds, story-tied events, rotation (habituation), ASMR only as touches | sound.worlds / story_events (fresh variants), `impact_map` (V8) |
| Variety: no near-copy of recent episodes | `impact_map` (V9, ordered 10-s signature, 0.97) |
| Flash safety | `impact_map` (V10) |
| Breakout Score >= 80 before upload | contract `breakout_bar` (held, weakest part named) |
| One strong writer + diverse drafts + blind cross-family jury (no role-play memos) | room2.write (3 Opus drafts, Gemini Pro + Flash + Sonnet jury, both orders) |
| Critic keeps the policy-safety gate | room.critic after the jury (v11.1 fix) |
| Writers' room learns: proven/promising/retired techniques | enforce.brain_block in every brief; contracts `brain_playbook`, `no_retired`; brain Thompson sampling (20% holdout) |
| 48-h breakout monitor -> follow-ups | breakout.monitor -> card -> 2 BRK Shorts + sequel premise at the top of the bench |
| Reach data (impressions/CTR) | reach.py (Reporting API channel_reach_basic_a1, daily) |
| Spin-offs: Case Files >= 35% new, loops, verdict variety; Deep Trial monthly | spinoff.py gates G0-G3; deeptrial.py |
| Tool scouting (new models, prices, deprecations) | scout.py weekly (fal catalog + pricing; Artificial Analysis /api/v2/media/*/free) |
| Watchdog clock (GitHub cron can be hours late) | Cloudflare Worker scheduled() + tick concurrency group |
| Uploads private + publishAt early; privacyStatus always explicit | publish.yt_upload (already) |
| One current truth: no retired concept in current docs, CLAUDE.md, module docstrings or prompts (owner, 10 Nov) | whatifs/truth.py (registry of retired concepts + scanner); contract `docs_current`; Plan Guard; tests/test_docs_current.py; SYSTEM.md generated by tools/gen_docs.py |

## F. WHAT IS DELIBERATELY NOT BUILT (honest list)
- A bench of fully rendered backup videos (scripts are pre-produced via Script Preview; failures retry from checkpoints; held videos go to the owner).
- Render sharding across parallel runners (render fits the 6-h job with particles adding ~10 min).
- fal billing reconciliation from billing-events (costs are estimated per call and capped).
- Message-Batches pricing for the v2 writers' room (sync calls; slightly more cost, faster).
- YouTube Test & Compare / end screens / a Short's related-video link (no API exists).
- CASE FILE: YOU premise (parked, see B).

## G. OWNER ACTIONS STILL PENDING (babysit these)
1. Upload: the v12 build lands as ONE pull request (branch v12-organisation -> main) at the end of the build; merge only if Checks are green;
   Wednesday-Friday, never during a render. Until then main keeps running the live code.
2. Cloudflare: paste new worker.js, add Cron Trigger */10 * * * *; dispatch token Actions: Read. Optional AA_API_KEY secret.
3. Character sheets (style board -> masters -> approve) - required for living characters; cast intro approve; WhatsApp setup.
4. First 3 long videos + first 3 Shorts wait for the owner's Approve card.

## H. THE ORGANISATION / BRAIN (owner, 10 Nov 2026 - the defining requirement of the v12 build)
The whole project must function like an ORGANISATION: every department (ideation, planning, research/R&D, review/assessment, creative/writers' room,
packaging, visual production, sound, QA/enforcement, publishing, growth/learning, finance, operations) researches automatically, assesses research
automatically, creates, brings research + creative + owner inputs (current and previous) together in brainstorms, decides the best, writes key
takeaways from every session into one ever-growing KNOWLEDGE PALACE (world-building learnings, knowledge, strategies, plans) that every department
(even execution) reads and writes, learns BOTH WAYS from every other department, sends problem memos back for brainstorm-and-repair, and EVERYTHING
learned, brainstormed or decided is EXECUTED AT CODE-LINE LEVEL and HARD-ENFORCED - tested, rehearsed, executed, re-looped until corrected.
Urgency is do-or-die. Spec: handoff 01_MASTER_SPEC_ORGANISATION_BRAIN.md; plan: 03_BATCH_PLAN.md; progress: handoff_v12/BUILD_STATE.md.
Built so far: B1 truth hygiene (one current truth, enforced).
B2 Knowledge Palace core (`whatifs/org/palace.py`, check `palace_health`): every point of this ledger and every research finding is a Palace item with dated evidence and, where it is enforced, a pointer to the code that enforces it.
B3 memos and the department contract (`whatifs/org/schemas.py`, `memos.py`, `registry.py`, `runner.py`; checks `dept_contract`, `takeaways_written`): every step of the long video that belongs to a department, and the daily learning job, runs LOAD -> ACT -> EMIT -> LEARN -> EXECUTE -> REPORT with a proof per step; memos have deadlines that escalate to the owner; a failed check becomes a problem memo for the department that owns it.
B4 the Execution Engine (`whatifs/org/levers.py`, `execute.py`; checks `decisions_executed`, `lever_verified`): a decision becomes tickets, a ticket a typed change written to a ledger before and after, verified by later evidence or rolled back.
B5 R&D and the Review Board (`whatifs/org/rnd.py`, `board.py`; check `research_cadence`): research questions are computed from the organisation's own gaps, answered with web search whose sources code verifies, and judged blind by strong judges of two model families on a fixed checklist with a planted canary; the verdict is computed by code and goes to the Council. A production job runs an overdue research round itself (no video is held for it), and research that pays and keeps nothing reports itself.
B6a the creative departments (`whatifs/org/cite.py`, `canon.py`; checks `palace_injected`, `palace_cited`, `canon_in_brief`): "the writer room should learn from researcher and R&D every time" - the Palace playbook is inside the model prompt of every creative call (writers' room, packager, director, pre-production writing too), each model cites what it applied with a quote that code must find in the final work, the show's history (every case: verdict, twist, Grimm's prototype, the promised next case) is written by code and becomes canon on air, and every new script calls back to the last case in a line that names it (characters to love, a reason to come back); creative ideas go to the Council as distinct memos.
V1 the viewer's seat (`whatifs/org/audience.py`, department D13; checks `viewer_promise`, `viewer_breath`, `viewer_numbers`): owner, 11 Nov 2026, on the first live video - "the voice is absolutely trash and unretaining", "so many stats on screen", the opening never showed the promise, 13 minutes. Before any picture is paid the first shot is a picture carrying the animated promise (on screen within 5 seconds), the voice gets a pause at least every 30 seconds, numbers heard and number graphics have a budget, and a long video is at most 9:00.
V1b the layman test (`whatifs/org/layman.py`, department D13; checks `viewer_plain`, `viewer_probe`): owner, 11 Nov 2026 - "strict enforcement and checks for whether a layman audience also gets hooked and retained"; on the first live video: "I was myself unable to understand the topic of video". The expert words a layman would not know are counted by code (a budget per minute, in the first 30 seconds, in one sentence; the writers' one fix carries the problem), and the promise line-up asks two cheap readers of two model families to pick the video's title from the first 30 seconds alone (a planted opening must get none; the verdict is computed by code). Both hold a video before any picture is paid. Whether a layman is HOOKED only real viewers can say.
V2a formats as data and the three-tier contract (`whatifs/formats.py`; check `format_kept`): owner, 11 Nov 2026 - "IF YOU HAVE TO REDESIGN CHANNEL, DO IT", "the whole video looked a lot gimmicky", "WE AND PIPELINE BRAIN SHOULD BE SMART TO CHANGE THE TYPE OF VIDEO MAKING OR FORMATTING". Every new episode gets a format: F1 "The day it changed" (70 of 100; it happens to you, two voices, no courtroom, the show's devices optional) or F2 "The trial" (30 of 100; today's show with all its devices); the shares are settings Strategy can move. A format can make a show device optional or leave it out and can loosen nothing else. F1 has only run with the offline test writers: no real model has written it yet.
V2c-a the Short as a product (`whatifs/shorts2.py`, department D14 Shorts Studio; `whatifs/org/shortseat.py`, D13; checks `short_open`, `short_plain`, `short_shape`, `short_kept`, `short_contract`): owner, 11 Nov 2026 - "I hope the reels are also made for breakout virality purpose ... please dont make excuses for this". A standalone Short is no longer a courtroom in miniature: it has a Short format (S1 "The second it changed", S2 "What would you do?", S3 "The whole thing in 30 seconds"), one guide voice speaking to you, nobody on screen, every second an animated clip, no plate at either end and a loop closed by code. Before any picture is paid the first frame, the hook on the real voice (3 seconds), numbers, expert words, the length, asks, the plan and the likeness to the last ten Shorts are measured; code repairs the plan, the writers get one fix, then the short gate holds - a held Short is not made and the owner is not asked. Only the offline test writers have written one: no real model, no real clip. The uploads per platform are V2c-b2.
V2c-b1 the ladder (`whatifs/ladder.py`, department D10; check `topic_ladder`): owner, 11 Nov 2026 - "reels are meant for reaching YPP ... independently", "MAKE SURE THE PIPELINE BRAINS IS ALSO PROACTIVELY DESIGNED TO MAKE SUCH DESCISIONS AND INFORM ME AND IMPLEMENT". Every topic starts as a Short: 3 a week, 12 a month. A long video is made only about the topic of a Short that real numbers picked - computed by code when the long video is about to start (a declared winner, else rank sums over engaged views, share watched, subscribers and shares, else public views) - or under his override, which is one tap and stays on the record. A Short at 3 times the channel's usual views gets ONE follow-up inside 48 hours, ordered by code; he is told and can stop it; a late one becomes a memo that climbs to him. YouTube's true numbers are 48 to 72 hours late, so a topic's long video follows its Short by one to two weeks. Since V2c-b2b1 that long video also OPENS on the Short's footage (below). No real Short has been measured yet: every rule here has only met offline numbers.
V2c-b2a the platforms (`whatifs/release.py`, department D9; check `release_sheet`): owner, 11 Nov 2026 - "WE HAVE TO BE BREAKOUT AND VIRAL WORTHY IN EVERY ASPECT OF ALL OUTPUTS (INCLUDING ... YT VIDEO SETTINGS AND FEATURES TO BE ACTIVATED, INSTAGRAM AND FB ALSO SAME ...) ... ENSURING WE ARE STRICTLY ENFORCING THEM". A finished Short goes out as three native uploads of one master file - YouTube Shorts (its own thumbnail, set after YouTube has processed it; the playlist of its format), Instagram Reels (a Trial Reel, its cover, the audio named after the series, the AI label), Facebook Reels (90 seconds at most) - each under its own words, none with an ask. Every setting code can set is a row of the release sheet, sent by code and read back from the platform; a row the platform did not keep is repaired once or reported to Publishing. Two Instagram rows (Trial Reel, audio name) can only be proven as sent: Instagram shows nothing back. Four things stay with his hand (the link from a Short to its long video, phone verification, comments and remixing) and are never called done by the machine (batch V3). Whether a Short was made is a field of its record now. Nothing here has met a real platform: every answer so far came from an offline stand-in.
V2c-b2b1 the opening (`whatifs/opening.py`, department D6; checks `opening_footage`, `opening_shown`): the redesign he ordered on 11 Nov 2026 - "the long video, whose opening IS that Short's footage"; on the first live video: "I myself couldn't identify where the kling clips were", "no audience based thinking". A long video about a promoted Short opens on the pictures that Short's viewers stayed for: its clips in its order, laid by code under the first sentences (15 to 25 seconds today), and its first spoken line is the Short's own hook, word for word. The upright picture is shown through one window whose width follows the clip's real sharpness (a setting: the widest window that enlarges it at most 2 times, the frame filled, or the whole clip on a blurred copy of itself). The opening is paid once: three animated scenes are bought for the rest of the video instead of four, and no hook lab is run. A video that would open with other pictures is held before any picture is paid; the finished film is compared with the footage frame by frame. A long video made under his override has no Short: it opens as before, on its own animated promise scene. How an upright clip really looks in the wide frame can only be judged on real clips: no real clip has met this code.
V2c-b2b2 the cut-downs (`whatifs/manage.py` `release`, `whatifs/truth.py` `OLD_DOORS`; check `docs_current`): owner, 11 Nov 2026 - "I hope the reels are also made for breakout virality purpose ... dont make excuses" and the redesign he ordered: a Short is "never a trailer, never a cut-down". A long video makes no cut-down reels any more: nothing is planned, voiced, covered or uploaded for one, and its release is one step (public, the channel comment, live). The topic already has the Short real viewers chose and the long video opens on it; the pull from that Short to the long video is YouTube's related-video link, which only his hand can set (the first line of the one-minute release card, batch V3). Counted from the code, the defaults would have posted about 38 short videos a month through four uploads - 12 Shorts, 16 cut-downs, 8 to 9 pilot Shorts and 2 special reels - three of them with one text for every platform, an ask and nothing read back: now the channel posts the 12 standalone Shorts, every upright video goes through one door (`whatifs/release.py`), the pilot Shorts and the special reels are paused by default (he can switch either back on), and a new door fails the build. Not rebuilt: the four older doors are shut by a switch, not moved onto the release sheet.
V2d-a the money and the model (`whatifs/clips.py`, department D6; `whatifs/costguard.py` `lines`; `whatifs/governor.py` `split`): owner, 11 Nov 2026 - "can we also try to make fully motion animated videos and reels ... find out the best ways to enhance our visuals at the budget ... THE ABSOLUTE BEST POSSIBLE WAY"; on the first live video: "I myself couldn't identify where the kling clips were"; and always: "THE BUDGET STAYS SAME". The model that makes the moving pictures is picked by code: the best-ranked model the month's plan can pay, from a table of what the provider's own pages say (a tie by the ranking's error band goes to the cheaper; the cheapest model is never picked for being cheap). With the pages of 13 Nov 2026 that is a model ranked 6th of 35 at USD 0.02 a second, where the code paid 0.084 for a tier the ranking does not list. A clip is bought by the second at the length of its shot (a Short's clips are no longer slowed). Every estimate is one table of lines - every paid second and call - that the paid-call counter checks; it found Rs 55 a video held back for calls that never run and four paid pictures in no estimate. A Short is estimated at about Rs 100 (Rs 287 before), a long video at about Rs 380 to 400 (Rs 561 before); four long videos and twelve Shorts fit Rs 5,000 with about Rs 1,000 not planned (before: seven Shorts, none after the third week). When a plan does not fit the code says how many Shorts do and spreads them; no quality check is lowered. Nothing here has met a real clip or a real bill: the rank was measured at another picture size, and the first real clips are judged by his eye at the pilot.
V2d-b the ladder's rules (`whatifs/motion.py`, `whatifs/stock.py`, department D6; `whatifs/governor.py` `moving_plan`; `whatifs/sound.py` `short_bed`; checks `moving_share`, `stock_share`, `short_moving`, `short_sound`, `living_characters`): owner, 11 Nov 2026 - "can we also try to make fully motion animated videos and reels", on the first live video "I myself couldn't identify where the kling clips were" (20 of 793 seconds moved) and one frame in four a flat black shape with a name; "THE BUDGET STAYS SAME". A long video now has a floor: a fifth of its time is moving pictures made by a model, and what the month's money leaves free buys more, up to two fifths (at the prices of 13 Nov 2026 the money reaches about 28 to 30%; the code says the number it bought). Every moving second comes from one market of models that are licensed for commercial use - the cheap model the code paid for living stills is licensed for research only and is never bought again. Code places the moving seconds and the renderer shows a paid clip whole (before, half of a paid scene could be cut away). The finished film is measured: it is held under the floor or when it shows less than it paid for; a Short must move in every second of its file and sound from its first frame as a phone plays it (the sound it had was silent on a phone until the voice began) - a Short that fails after its clips are paid waits for his one tap. No shape is ever drawn in place of a character: a character appears as its approved art or not at all. Real footage of NASA and Pexels (his key) is a short anchor under rules by code - a tenth of a video at most, never first, never two in a row, changed, no clip whose title names a person, credited - and a Short has none. Nothing here has met a real clip: how gently a real living clip moves, and where the limits of the measure must sit, is first seen at the pilot.
V2b inside the format (`whatifs/org/inside.py`, department D13; `whatifs/path.py`, D6; `whatifs/formats.py`, `whatifs/cta.py`; checks `viewer_inside`, `camera_path`, `camera_shown`, `format_ending`): owner, 11 Nov 2026 - "explain every aspect or anything with a first person immersive experience and also very nice visual continuous camera experience in a good environment to make the audience literally feel the things", on the first live video "no audience feel or touch", a name label on a black shape, three asks and a tease at the end. The voice is counted sentence by sentence: a share of at least the format's floor speaks to "you" in the present tense (F1 50%, the trial 40%, F3 60%), never more than a few sentences in a row from outside, and no part explains before it has shown; the writers are told, their one fix carries it, the gate holds. Each act of a long video has ONE place, every picture is at the viewer's own eye level, the code-made camera travels one way inside an act and never backwards or tilted, and no still shows a picture made for another act - judged on what the render recorded, not the plan. The ending is the format's own: F1 ends on its question with one subscribe ask in the middle, F3 on its arrival with no ask; under the ladder no video teases a next topic. A name chip is shown only for a character who is drawn. A third format, F3 "The walk" (one voice, one route), joins at 20 of 100 beside F1 60 and the trial 20. The Short's spoken first line is kept on its ladder row and handed to the long video's writer; the witness and the third thumbnail template no longer ask for a shape; an F1 / F3 writer is no longer given the trial's cast. No new kind of paid call; at most one still an act more (the stills line carries it). Nothing here has met a real writer or a real picture model: what share a real script reaches and whether a picture model keeps one place is first seen at the pilot.
V1c the floor, his verdict and the maker's line (`whatifs/org/floor.py`, `whatifs/org/verdicts.py`, department D13; `whatifs/maker.py`, D7; `whatifs/story.py`, D5; checks `viewer_floor`, `makers_line`, `one_story`, and `living_characters` widened): owner, 11 Nov 2026 - he rejected the first live video ("absolutely looks like just a cheap pipeline made video"), and his items 16, 49 to 51, 70 and 73: nothing a first-time viewer would rank beside that video may go out, his own verdict is the strongest signal, "many AI channels don't get monetized ... due to mass producing content". THE JUDGED FLOOR: the first minute of every finished long video that passed every measured check is shown, blind and in both orders, to two strong first-time viewers of two model families beside the video he rejected (a file he gives once; offline a stand-in with its measured traits), its frozen copy and the videos he approved; a film they cannot tell from the rejected one is HELD with its own card; a session whose judges fail the planted ladder is void and the film goes to his eye with a clock - never passed by the judges' silence; one family watches and hears, the other sees a strip of pictures (that is all its API takes); one verdict a film (a session that could not judge is tried once more, then the film goes to his eye), inside a month cap. HIS VERDICT: every public Short and every live long video made since the day this reached his Sheet gets ONE tap (Good / Not good), asked at most one a day and never in the day's last "act now" place; his tap is kept on tab `Owner_Verdicts`, the floor is scored against it, and a video he approved becomes a reference. THE MAKER'S LINE: at each Short he is asked for one sentence of his own; the long video about that topic ends on it, word for word, after a long pause and a lead-in, over its last picture, and the description carries it - never cut, mended, an ask or a label; nothing is drawn or paid for it; his own voice only with his consent record (it may not be obtainable at all). ONE STORY: the thumbnail is the first picture of the Short the video opens on, the runner-up another look at it. NOBODY OF THE TRIAL'S CAST in F1 and F3, and their animated scenes show the viewer's own place. Item 49's answer that this batch owns: his own sentence in the film and in the description a reviewer reads, and one story across title, thumbnail and first seconds. Nothing here has met a real judge, a real channel or his phone: whether two real judges tell his rejected video from a new film, what a session costs and whether his voice can be had are first seen at the pilot.
Not built yet (V3, V4, V5, B6b-B10): THE BREAKOUT REDESIGN (owner, 11 Nov 2026: he rejected the first live video, made by the old code - "absolutely looks like just a cheap pipeline made video" - and gave a free hand: "IF YOU HAVE TO REDESIGN CHANNEL, DO IT"). Decided in `handoff_v12/BREAKOUT_REDESIGN.md`: hook-first production, a new Audience department with a veto, Strategy as the portfolio manager that decides, informs and implements, formats as data; then the Council, the repair loop, the learning loop with the Librarian, the Owner Office.

## I. THE OWNER'S WORDS OF 14 NOV 2026 (items 38 to 66 of the handoff's `02_OWNER_VERBATIM.md`, word for word there): what each means for the product and which batch executes it
NOTHING IN THIS SECTION IS BUILT UNLESS ITS LINE SAYS SO. Each line names the batch whose design must carry it and whose check must enforce it (A1: hard
enforcement or it does not exist). A designer reads the items themselves; this is the digest, never a replacement for his words.
1. **THE SCOREBOARD IS WHAT THE PARTNER PROGRAM COUNTS** (item 55: "there is something called eligible views, which is what worries me the most"; measured on
   his paused channel: about 120 views and 0 eligible watch hours on the first long video, about 200 views and 12 eligible on the Shorts). Every prediction,
   pace line and decision of the brain is stated in engaged Shorts views over 90 days, eligible watch hours over 12 months and subscribers - never in raw
   views. BUILT: the learning core reads `engagedViews` and learns on the engaged rate (`whatifs/brain.py`). TO BUILD: the scoreboard and its daily pace
   (V4), the learning loop's predictions (B8).
2. **EVERY OUTPUT ALONE** (items 42, 52, 55, 56, 59, 61: "every output in itself should be such maximum best made so that it can attain YPP monetization by
   itself only"; "100 million views type of content maximum possible in our budget"; "the best channel and pipeline in our niche"; "our efforts should be
   viewer centric"). The standard every design is reviewed against: each long video and each Short is made and judged as one that must break out by itself;
   the viewer is the measure, visuals and voice included. An aim every output is held to, never a promise. BUILT: the viewer's seat, the layman test, the
   Short as a product, the motion ladder, inside the format (V1a to V2b); the judged floor against the video he rejected and the videos he approved, and his
   own verdict (V1c - public links are not used as references: only one family can open one, and which public videos are "good" is the Observatory's to
   collect by rule). TO BUILD: the aspect map - every aspect with an owner and a check (V5).
3. **NEVER MASS-PRODUCED, NEVER THE SAME VIDEO TWICE** (item 49: "many AI channels don't get monetized or get demonetized due to mass producing content").
   BUILT: a Short is held when it shares more than `SHORT_SIMILAR_MAX` of its three-word phrases with one of the channel's last ten; the Short formats rotate
   by code; three long formats with their own structure, ending and camera; the Review Board asks of every idea whether it could break YouTube's policy on
   inauthentic content; the policy watch raises an official change to him; the volume is small (about 12 Shorts and 4 long videos a month); a long script more
   similar than `SCRIPT_SIMILARITY_MAX` to one of the last ten is HELD at the script gate by check `originality`, in every format, and the card is sent beside it
   (V1c corrected this line, which said "only one card, never a hold": the code holds); his own verdict and his maker's line - the human element: his own
   sentence in the film and in the description a reviewer reads - and one story across title, thumbnail and first seconds (V1c). NOT BUILT, said plainly:
   nothing compares the LOOK of a video with the channel's earlier ones. TO BUILD: "repetition across uploads" as a row of the aspect map (V5); one look and
   never one repeated scene (DRAWN BY CODE).
4. **THE CEO ACTS BY ITSELF, AHEAD OF TROUBLE** (items 39, 52, 65: "pro actively act on it, even if i dont have time"; "goal achievement urgency is very very
   real and do-or-die"). The brain watches on its own clock, reads the scoreboard every day against a pace to the goal, acts the same day on a slip, changes
   what it may change as a ticket that is verified and undone when worse, and tells him in one line; his silence never stops it. A monetisation-risk watch -
   the policy pages, the channel's own repetition, the warnings and strikes a platform reports - with an owner, a measure and an action each. TO BUILD: V4
   (with V5, B6b, B7, B8).
5. **WHAT THE MACHINE DECIDES AND WHAT STAYS HIS** (items 53, 60: "you can decide the channel name and leaving science ... for the cap and deleting, i'll
   inform"; "not just science"). The channel's name and its subject are the machine's to decide - by evidence, as a small arm first, rarely, as a ticket that
   can be undone, with one line to him. Money above the cap and deleting a video stay his. The show's present identity stays until real viewers' numbers
   say otherwise. TO BUILD: V4.
6. **LEARN FROM WHO GETS THERE FASTEST - WITHOUT SWAYING** (items 42, 65, 66). The Observatory studies first the channels and uploads that reached millions
   of views and the Partner Program fastest from a new start, inside the monetisation policy (a pattern that leads to demonetisation is recorded as a risk,
   never copied). A pattern enters as ONE trial at a time with a prediction, judged by our own viewers' eligible numbers: no chasing of every trend. His
   observation of the channel "ConChaser" is one case for it, not a benchmark. TO BUILD: V5.
7. **THE API CREDITS ARE A BONUS LAYER WITH AN END DATE, NEVER THE FLOOR** (items 38, 56, 57: "the channel video quality should not fall down suddenly because
   of no API credits"; "no visible drop in quality after credits expiry"). The base - every gate, every format, the cadence, the look - runs on Rs 5,000 a
   month without any credit. What credits pay for (the pipeline's own text calls: more drafts, more blind judgements, more scenes drawn by code) are levers
   with a start and an end date in the cost model that step down on record. Every gate judges a credit-paid output and an everyday one by the SAME bar: the
   end of the credits may cost volume or variety of drafts, never a weaker video on air. Credits are spent first on what lasts - winners that teach the
   Palace, the house kit, tested briefs; the month's credit is planned inside its month and what lapsed is reported. They pay for words, judgement and
   code-drawn scenes only, never for pictures, clips or voices. TO BUILD: V4 (the levers, the plan, the report), DRAWN BY CODE (the house kit), B8.
8. **RAILS ARE MEASURES, NEVER TEMPLATES** (item 57: the framework must not cost "dynamism flexibility" or breed "AI slop"). A rule RECOGNISES what is wrong
   and leaves the writing free; variety is itself checked (line 3); no rail prescribes a fixed script, scene or look. BUILT as the pattern of every measure
   since V1a (the repo's `CLAUDE.md`: never flag what a rule does not know). REVIEWED in every later design.
9. **THE BEST MODELS, JUDICIOUSLY** (items 55, 58, 62). In the pipeline every call that decides taste or quality goes to the strongest models of its family,
   discovered live, and cheap models do mechanical work only. BUILT: `models.ROUTES`, hard rule 9 of the repo's `CLAUDE.md`. TO BUILD: the brain spends
   where the evidence says eligible views move, every paid call on its line of the cost model (V4).
10. **HIS DESK IS WHATSAPP AND A DASHBOARD; A RELEASE NEVER WAITS FOR HIM** (items 50, 51). Every recurring step of his is doable from his phone. The
   one-minute release card is ONE message with four button links - each opens the exact Studio page of that video for one step only a hand can set (the
   Short-to-video link, the end screen, the pinned comment, the thumbnail test) - and a field for his maker's line. When he does not do it, the video goes
   out with every setting code CAN set, chosen from the release sheet, and the card stays open with a reminder. The machine never drives his browser.
   TO BUILD: B9 (the desk), V3 (the card); the designer reads YouTube's own pages for each of the four steps first.
11. **EVERY FILE IS WRITTEN FOR THE READER THAT ACTS ON IT** (items 63, 64: "every file and effort in every molecule should be to maximize results"). His words
   stay word for word in `02`; this ledger and the Palace's owner items are the structured digest that departments and models read; a file that serves no
   reader is archived. A standing rule for every batch's docs step and for B10's hand-over package.

**V4 BUILT - THE CEO AND THE LADDER (17 Nov 2026; built, NOT yet accepted)**. Where each of his items is executed: items 39, 52, 65 (the CEO acts
by itself, ahead of trouble) - D1's daily `strategy.review` in the learning job (`cli.strategy_round`): one move a review through RANGE, EFFECT and FIT
(`strategy.next_move`), each a ticket the Execution Engine applies and verifies (`strategy.decide`), check `strategy_live`; the watch book (`risk.WATCH`,
`risk.run`): a rejected or vanished video closes the uploads the same day (`risk.lock`) and holds production at the gate. Items 53, 60 (what stays
his) - `strategy.OWNER_ONLY` (the cap, the credit cells, PAUSED, the publishing days), one tap undoes (`strategy.undo`), a cell he sets by hand is
his for 28 days (`strategy.hands`), his own words are answered in the next brief (`desk.tick`, tabs Owner_Input and Owner_Desk). Item 55 (eligible
views) - the scoreboard first in every brief (`scoreboard.line`, `digests.compose`, `notify.digest`). Items 56, 57 (the credits are a bonus with an
end date; rails are measures) - Finance's lane and meter (`finance.lane`, `finance.cover`, `finance.boost`, `governor.own_spend_inr`: what the credit
paid is never counted as his), formats judged once at a fixed count by their median (`strategy.judge_arms`). Item 58 (the best models,
judiciously) - the boost asks the strongest writers for more Short scripts only while the credit lasts (`shorts2.write` through `finance.boost`).
Item 80 (the platforms' new features) - the arm book: a candidate needs a dated source and a policy reading, one trial at a time (`strategy.file`,
tab Candidates). A long video that takes off gets its follow-up Short with a clock (`breakout.monitor`, `ladder.order_followup`).

## J. THE OWNER'S WORDS OF 14 AND 15 NOV 2026 (items 67 to 100 of the handoff's `02_OWNER_VERBATIM.md`, word for word there): what each means for the product and which batch executes it
As section I: NOTHING HERE IS BUILT UNLESS ITS LINE SAYS SO; a designer reads the items themselves. Most of these items govern how the BUILD is run (its
sessions, tools and estimates) and nothing of the product - they are listed last, in one line, and live in the plan and in `02`.
12. **THE PIPELINE IS ALSO A PRODUCT HE SELLS** (items 70, 71: "I intent to utilize this pipeline as a saleable product also to high level faceless channels
   who can pay atleast 20k per purchase"; "make the world's best pipeline for me and to sell as well"). Nothing of it may be tied to this laptop, this
   account or this channel's name and subject; every setting a buyer must give is data with a setup that asks for it; no key, id or personal detail of his
   in the code or the docs; the hand-over package installs and runs for a buyer who is not him (an installer, a licence text, a manual, a demonstration
   run in fake mode); the by-products he names (packs of prompts and the like) are a list written from what the build really made - never a promise of
   income. SAID TO HIM PLAINLY: Rs 2 crore in one month is not something any channel pipeline can deliver. BUILT so far: V1c names nothing of his in code
   (the canary is a file he gives once, the question his line answers is a cell, every message says "the video you rejected"). TO BUILD: B10 (the package,
   the manual, the list of by-products); every batch's design answers "could a buyer who is not him run this?".
13. **THE LAUNCH WAITS FOR THE WHOLE PROJECT - AND EVERY OUTPUT AIMS AT A BREAKOUT OF ITS OWN** (item 73: "i will only launch when this whole project is
   finished perfectly with highest quality possible"; item 95 (c): "MAXIMUM BREKAOUT WITH EACH OUTPUT INDEPENDENT QUALITY"). No early launch (the order
   V1c, V4, V5, DRAWN BY CODE, B6b to B10, then V3 with his own sitting stands; nobody asks him again). Every single video and Short is made and judged
   on its own; a design that settles for "good enough for a first video" is refused at its review; nobody promises him a record breakout. BUILT: every
   measured gate of V1a to V2b and V1c's judged floor. TO BUILD: whatever the engine's own code could use to judge or make each finished file better goes
   to the designers of V4, V5 and later as dated evidence.
14. **THE PLATFORMS' NEW FEATURES - USED WHERE THE MACHINE CAN, OFFERED TO HIM WHERE HIS HAND HELPS, NEVER A HOLD** (item 80: "Please make ssure we are
   using such new features ... and also inform me if i can help use it, but not depend or held because of my non involvement"). A STANDING REQUIREMENT, in
   the words of item 80: (a) a STANDING WATCH for new platform features is part of the Observatory: on a schedule it reads the platforms' own announcement
   pages and dated practice sources for every platform the release sheet posts to, and files each new feature as ONE of three kinds with its sources and
   date - THE MACHINE CAN USE IT ALONE / IT NEEDS HIS HAND IN AN APP / NOT USEFUL OR NOT ALLOWED (the monetisation policy first); (b) the CEO decides which
   of the first kind to TRY - a small experiment arm with a prediction, applied as a ticket the engine can roll back, never adopted on a belief, never all
   at once; (c) the second kind goes to HIS DESK as an OPTIONAL task on the release card - what, why, how long, the link to the right screen - NEVER A HOLD:
   the release goes out at its time with the best automatic settings, a task he did not do is recorded "not done", never asked again for that video, and
   its effect is measured only where he did it; (d) every department that briefs a model gets the current list of adopted features from the Palace (one
   item per feature, dated; an item not confirmed again in 90 days is retired); (e) the setting "others may remix this Short" (and its like on each
   platform) is checked against the release sheet - on where the platform allows it through its program, a line of the runbook where only his hand can
   set it once. BUILT: nothing yet - V1c only FILES it (here and as the Palace's owner item `owner.platform_features`). TO BUILD: V5 (the watch), V4 (the
   intake and the CEO's trials), B9 (the optional task on his desk), B10 (the runbook line).
15. **A TOOL'S METHOD ENTERS THE PIPELINE ONLY AS ITS OWN CODE** (item 88: "see if the skills, plugins, connectors, etc i have installed can be used in
   pipeline ... but only if they're actually improving it"). Skills, plugins and connectors are tools of the building sessions; none is ever CALLED by the
   pipeline, nothing of the pipeline may need a Claude session or this laptop, and no text or code of a skill is copied in (no licence was found on the
   skills' folders). A method enters only through a batch's design - a measure with its arithmetic, its test, its cost line and a switch, and as a TRIAL
   with a prediction where it claims to lift a video. TO BUILD: V5 weighs five measures (views a day at the same age; three searches against a 90-day
   baseline; rising small channels; the share of Shorts in a niche; whether a niche is filling up) and gives the pipeline's read-only research calls a key
   and a quota of their own (a Settings cell; filled at the pilot by a runbook line); the "yt-script" hook formulas are practice sources for the hook lab,
   each a trial only through the Review Board.
16. **THE BUILD'S OWN WAY OF WORKING** (items 67 to 69, 71, 72, 74 to 79, 81 to 87, 89 to 94 and 96 to 100): the finisher and the chain of sessions, a
   wait that ends when its process ends, no idle session and no message that reads as a question to him, Fable keeping every design, review,
   finishing pass and audit, the tools installed for the sessions (rtk, the superpowers, caveman's voice, the code graph, the YouTube research skills
   and their read-only key, the skill packs and plugins) and what each may never do, the estimates computed from measured numbers only, and his usage
   that no command can reset. They govern the build, never the product: they live in `02` and the plan (`handoff_v12/OPUS_BUILD_PLAN.md`); none of
   them enters the pipeline, `proving/` or the project's `.venv`.
