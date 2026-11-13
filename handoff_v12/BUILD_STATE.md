# BUILD_STATE - Reality Engine v12 "Organisation"
Updated: 13 Nov 2026 (B6a ACCEPTED; the owner rejected the first live video and ordered a redesign - read the next section and BREAKOUT_REDESIGN.md first; V1a ACCEPTED, V1b ACCEPTED, V2a ACCEPTED, V2c-a ACCEPTED, V2c-b1 THE LADDER ACCEPTED on 12 Nov 2026, V2c-b2a THE PLATFORMS ACCEPTED on 12 Nov 2026 - V2c-b2 was split at its start, V2c-b2b was split at its start too: V2c-b2b1 THE OPENING ACCEPTED on 12 Nov 2026, V2c-b2b2 THE CUT-DOWNS ACCEPTED on 13 Nov 2026 - V2c is complete; V2d THE MOTION LADDER AND THE MONEY is next; THE LIVE CHANNEL IS PAUSED BY THE OWNER'S OWN HAND since 13 Nov 2026 - item 22 below, open issue 148). Branch: `v12-organisation` (never main). Resume: read this file + `git log -5`.

## STANDING RULES ADDED DURING THE BUILD (rule 1: owner approved, 10 Nov 2026; rules 2-4: B0b, they follow from his rule "hard enforcement or it does not exist")
1. A batch is ACCEPTED only when its FINAL commit is green in GitHub's own `Checks` workflow (Ubuntu, real pytest, then the fake rehearsal) - the
   laptop runs (Windows, stand-in test runner) are necessary, not sufficient. Read it before writing "ACCEPTED" and record the run number in the batch log.
   How to read it - NO sign-in needed since B0b: open https://github.com/Rahul4869/reality-engine/actions?query=branch%3Av12-organisation in the
   browser pane and open the run. The section "Annotations" names every failed test, every skipped test, every failed contract check with its reason
   and the episode ids; when green it shows the totals ("N passed") and the rehearsal's episode id. The job summary on the same page has the full list
   (annotations are capped at 10 a step). A run takes about 30 minutes; do not wait idle for it - finish the write-up, then read it.
2. (B0b) Before a batch is accepted, run the sweep (`tools/sweep.py`, recipe under HOW TO RUN): the fake pipeline is seeded by the episode id, so one
   green rehearsal proves one id. A red rehearsal or a red test on GitHub is reproduced with the episode id its annotation prints
   (`--mode rehearsal --ids <id>`), traced to its cause and fixed - never re-run until it passes.
3. (B0b) Nothing may be built without being wired and no test may skip on GitHub: Plan Guard, the tests and check `docs_current` refuse a Settings cell
   that no code reads, a Sheet tab that no code uses and a function that no production code calls. The three lists of old cases in `whatifs/truth.py`
   (UNREAD_SETTINGS, UNUSED_TABS, UNWIRED_FUNCTIONS) may only shrink: wiring one means deleting its entry and lowering the limit next to the list.
4. (B0b) Every workflow installs a package that `requirements.txt` pins with exactly those bounds (a test fails otherwise). To move to a new major
   version of a library, change `requirements.txt` AND the workflows in one commit and re-verify the reference frames (`tests/golden_frames.py`).

## THE OWNER'S VERDICT ON THE FIRST LIVE VIDEO (11 Nov 2026) - READ BEFORE ANY BATCH
His exact words are item 16 of `02_OWNER_VERBATIM.md` (handoff folder). In one line: "absolutely looks like just a cheap pipeline made video",
"ashamed to share", "not even 5% chance this is watch worthy for 1 minute" - voice, clarity, too many numbers on screen, weak visuals, no
audience thinking; he wants the absolute best breakout videos and Shorts in every aspect.
WHAT THE BUILD SESSION MEASURED (the facts are next to his words in 02):
- The video: https://www.youtube.com/watch?v=7RPT4rCuP6k - title on YouTube "When you Walk FASTER than Light!!", 13:13, 10 views and 4 subscribers
  when read (11 Nov 2026). Made by the OLD live code (v10.x), not by v11.1 or v12.
- Measured from the file he uploaded (ffmpeg, 640x360 copy): 793 s; 155 hard cuts (one every 5.1 s; only 16 in the first minute); speech is
  wall-to-wall - 6 pauses of 0.7 s or more in 13 minutes (6 s of silence in total); loudness -14.1 LUFS with a range of only 4.1 LU (flat, no
  quiet / loud contrast) and a true peak of +0.8 dBFS (clips); no captions on screen.
- Seen in 92 sampled frames: about one frame in four is a flat black shape with two ovals for eyes and a name label (INSPECTOR VALE, DR. GRIMM) -
  no face, no body, no courtroom, no puppet look, no Nana Rosa; at least 7 full-screen number cards (two inside the first 50 seconds: "1.0 meters /
  2.0 meters", "SPEED OF LIGHT IN THIS APARTMENT 1.4 m/s"); the rest are dark, soft AI stills with a slow zoom (hands, toothbrush, hallway).
- First 12 seconds: a hand with a toothbrush (2 s), a blurred hand with a melted toothbrush (4 s), the black shape (4 s), a hand, the black shape.
  The promise - YOUR REFLECTION LAGS BEHIND YOU - is never SHOWN. The last 20 seconds are one still of a phone.
- The title promises walking faster than light; the film opens on a toothbrush; the description names "the Director and the Curious One"; the
  screen names Inspector Vale and Dr. Grimm. Three different shows in one upload.
- Animated (Kling) scenes: 4 a video, about 20 seconds of 793 (2.5%) - that is why he could not find them.
- A second AI he asked (two phone screenshots) said: 13 minutes is too long (8-9); a niche ceiling without an emotional hook; the shapes are less
  clickable than a face or polished animation; assumptions front-loaded; reduce the trial framing; obsess over the first 20-30 seconds and the
  thumbnail; the pipeline is a production tool, a human taste filter must decide what is good enough to publish.
WHY IT HAPPENED (causes, from the code and the file):
1. It was made by the OLD live code (v10.x). v11.1 and v12 have never been deployed - and have NEVER rendered one real video (fake mode only).
2. The cast was never drawn: the black shapes are the old format engine's rule ("presenters are never shown as realistic faces ... only as
   silhouettes"). The Toybox Noir cast needs the character sheets, an owner setup step that is still pending (04, "Owner setup steps pending").
3. The checks reward DEVICES, not a viewer: the script gate demands a time ladder, exhibits, a prototype, re-hooks, a punch line every N seconds,
   asks, a tease ... - 19 script checks that each ADD something. Nothing asks "can a normal person follow this?", "is the voice pleasant?", "are
   there too many numbers?", "did the picture show the promise?". A video can pass everything and bore its owner. That is what he saw.
4. Money: animation costs about USD 0.084 a second; 10 animated minutes would be about Rs 4,400 A VIDEO. The show is stills + motion design by
   budget; the 4 animated scenes were spent on ordinary shots instead of the one impossible picture the title sells.
WHAT THE NEW CODE ALREADY CHANGES (v11.1, in the repo, never run for real): no black shapes (check `living_characters` holds the video without the
approved cast), 10:00 at most (RUNTIME_MAX_SEC), `promise_paid`, `visual_change`, `aliveness`, `slop_guard`, `breakout_bar`, the owner's approval
of the first 3 long videos. WHAT v12 HAS ADDED SO FAR (B0-B6a): the organisation - memory, research, the Review Board, the creative departments
reading the knowledge. It changes how the system learns and enforces. It does NOT yet change the voice, the clarity, the number of numbers or the
pictures. Brutal truth: deployed today, v12 would give him a better-policed version of the same film.
THE OWNER'S FREE HAND (item 17 of `02_OWNER_VERBATIM.md`, same day): "IF YOU HAVE TO REDESIGN CHANNEL, DO IT ... SO DO IT AS PER YOU NOW ... MAKE
SURE THE PIPELINE BRAINS IS ALSO PROACTIVELY DESIGNED TO MAKE SUCH DESCISIONS AND INFORM ME AND IMPLEMENT". The budget stays Rs 5,000.
THE REDESIGN IS DECIDED AND WRITTEN: **`handoff_v12/BREAKOUT_REDESIGN.md`** (research with 14 dated sources, 4 designs, the decisions, the new
batch plan). READ IT BEFORE ANY BATCH. It overrides `01` section 1, the order of `03` and the department list wherever they differ. In short:
- Only LONG videos earn (from 1 Feb 2027: 1,000 subscribers + 8,000 long watch hours); Shorts test ideas and win subscribers, a few a month.
- HOOK-FIRST PRODUCTION: the first 30-40 fully animated seconds of every long video are made first and published as a Short; only hooks real
  viewers stay for get the long video, which opens with the proven hook.
- NEW DEPARTMENT D13 AUDIENCE (the viewer's seat, a veto before publishing; measured checks + a judged floor with the owner's rejected video
  as the planted canary). D1 STRATEGY becomes the portfolio manager that decides, informs and implements - built now, not in B9.
- Formats are data (F1 "the day it changed" 70%, F2 "the trial" 30% as an experiment arm); the contract gets three tiers and the devices are no
  longer forced; the voice and video models are chosen by value inside the owner's existing accounts.
ITEM 18 (same day, more inputs): "only 4 videos a month? ... earn money from the first video itself ... a system where I can also give inputs ...
keep learning and auto implementing and keep me informed". Answered in the redesign page: 5 long videos + 8 Shorts a month (13 uploads - the
count is set by money, D1 raises it when cost falls) and a monthly compilation; no money is possible before the Partner Program, so GOING LIVE
moves to the end of V3; the scoreboard (hours / 8,000, subscribers / 1,000) is the one goal (4.8); the owner's desk answers every input with
adopted / tested / parked and his earlier ideas each got a verdict (4.9); launch readiness covers the channel page too (4.10).
ITEM 19 (same day, after V1a): asked whether to pause the live channel and hide the rejected video he said NO - "Let the videos get posted till
we get the corrected pipeline to implement". The old code keeps publishing until V3; never ask again. He also asked that EVERY aspect be built
for breakout "do or die", that the machine OBSERVE widely what breaks out and integrate the best, a hard check that a LAYMAN understands, and a
first-person, continuous-camera experience. Answered in the redesign's new SECTION 10: the layman test (V1b), first person / one place / one
move and format arm F3 "The walk" (V2), the Breakout Observatory and the aspect map (new batch V5). The evidence R15-R19 of that section is
not in the Palace yet: the batch that builds each part adds its founding items (they need real code references).
ITEM 20 (same night, after V2a): the Shorts must be a breakout track of their own ("dont make excuses"), full motion in videos and Shorts, a
one-time human element (his voice, his photo, or what works best), every setting on every platform strictly enforced, every department for
the instant hit, and his Pexels key. Four research runs and four pages read by the build session; answered in the redesign's new SECTION 11:
SHORTS FIRST (every topic starts as a Short; 12 a month; the Shorts road into the Partner Program before 1 Feb 2027), THE MOTION LADDER (a
Short animated in every second; the paid model by value - today's costs four times the best-value one and ranks lower), THE HUMAN KIT (his
replicated voice needs no disclosure; the maker's line; no sample stops a platform seeing AI and for stylised animation it need not), THE
RELEASE SHEET (what code can set, what one sitting sets, what only his hand can do per video), new department D14 Shorts Studio, and a NEW
ORDER OF BATCHES: live after three. The evidence R20-R38 is not in the Palace yet (same rule as above).
ITEM 22 (13 Nov 2026, after V2c-b2b2): "can we save some time from the remaining build without losing any details or build or aspect
or any molecular worth of quality or compromise?" and "i have put the setting tab's PAUSED as TRUE as of now FYI". ANSWERED FROM
MEASUREMENT (the commit times of this build), not from opinion: a batch takes 4.5 to 10 hours from one ACCEPTED to the next (6 h 05
for V2c-b2b2); about half of it is proving, and the fixed block at its end is 2 h 07 of machine time (the parallel pre-check 33
minutes, the serial suite 56, the sweep 38; GitHub's 56 run beside the write-up). NOTHING OF THE PROVING IS FREE: the suite and the
sweep side by side is a lesson already paid for (HOW TO RUN: false failures under load), and item 21 says that what a batch is
judged by is never replaced or weakened; fewer tests, a smaller sweep, fewer breaks, a shorter reading, bigger batches or a lower
effort each cost something - none was offered. FREE, and only these: (1) HIS WAITS between batches (2 h 11 min that night) - he was
offered that the session which started a batch starts the next one once the last is verified ACCEPTED, up to the pilot; HIS YES IS
NEEDED, and until it is on record in `02_OWNER_VERBATIM.md` one batch per owner "continue" stands; (2) HIS PART OF THE PILOT made
ready before V3 - first of all the channel's feature access, which is more than the phone (open issue 149). THE PAUSE: he set PAUSED
to TRUE on the live Sheet himself. It replaces the "not paused" half of item 19; the rejected video stays public (he did not say
otherwise). Nobody asks him about it and no session touches the cell; what the cell does and what V3 must do BEFORE it turns back
is open issue 148.
That turn was the DESIGN step for the whole programme (research, designs, decisions, records). Built since: V1a, V1b, V2a and V2c-a (the records are under DONE).

## NEXT
**V2d WAS SPLIT AT ITS START (13 Nov 2026, token discipline rule 6), by dependency, as recommended below: V2d-a THE MONEY AND THE
MODEL (the hero clip model chosen by value from the provider's pages and listing, clips bought by the second, the cost model as
one table of lines the paid-call counter checks, the month's split) is IN WORK - its record is the first entry under DONE and
says where it stands; V2d-b THE LADDER'S RULES (the living tier L3 widened, `moving_share` measured on the finished file, a
character drawn or absent, the stock rules, the first-second sound of a Short) comes after it, before V3.** Why this order: (b)
spends what (a) frees - "AI-moving seconds per long video" can only be raised once every paid second is a priced line and the
price per second is known; (a) needs nothing of (b).
**V2d - THE MOTION LADDER AND THE MONEY** (`handoff_v12/BREAKOUT_REDESIGN.md`: 11.5, the rows "Long: motion", "Characters", "Stock"
and "Money" of 11.9, 11.10 with its end notes; R13, R30, R31, R38). Full seven-step MANDATORY BATCH LOOP. Effort: High. V2c is
COMPLETE (five batches; the last, V2c-b2b2 THE CUT-DOWNS, is the first record under DONE: check there and in `git log -5` that it
is ACCEPTED before building on it). V2d is large - SPLIT IT AT ITS START by dependency (rule 6) and say so here. A split that
follows the code: (a) THE MONEY AND THE MODEL - the hero clip model chosen BY VALUE from the live listing (rank per dollar, a
start picture, upright output; a model with clips longer than 5 seconds ends the slowed clips of V2c-a, open issue 82), the cost
model with EVERY paid second and call as a line of the estimate (open issues 72, 83, 126, 141: a Short has no line of its own,
the ladder video is over-estimated, the lump allowances), and the split 4 long + 12 Shorts inside Rs 5,000 - today twelve Shorts
at about Rs 290 do NOT fit beside four long videos; (b) THE LADDER'S RULES - the living tier widened (L3), `moving_share`
measured on the finished file (a Short 100%; a long video about 40% as a lever; open issues 86, 130: part of a paid scene is
never seen when micro-cuts split it), a character drawn or absent in every format (no silhouette fallback; open issue 75), the
stock rules for NASA and Pexels (10% at most, never first, never two in a row, changed, no people, credited; none in a Short;
check `stock_share`), the first-second sound of a Short (open issue 91). Read the fal pages and the ranking yourself before any
design: prices moved while the redesign was written (O10) and two fal pages disagreed.
What V2c-b2b2 leaves ready (use it, do not rebuild it): the channel's short videos are the STANDALONE SHORTS and nothing else -
a long video makes no cut-down reel, its release is one step (`manage.release`: public -> the channel comment -> LIVE), and every
upload of an upright video goes through ONE door, `whatifs/release.py`. `truth.short_doors` / `door_issues` / `OLD_DOORS`: a new
function that calls `ig_reel`, `fb_reel` or `yt_upload(short=True)` outside `release.py` fails Plan Guard, the tests and check
`docs_current`; the four older doors (special reels with the cast intro, pilot Shorts, the hero-still Short, the audio-drop
Reel) are OFF by default and may only leave that list (open issue 136). The paid-call counter (`tests/paid_calls.py:watch`)
now sees key art (`image_premium`) and voice jobs (`voice_job`): V2d's cost model can be checked against it call by call -
`V12V2CB2C_REMOVED` shows how a removed call is written into the baseline. `tools/sweep.py:release_of` judges every
long-video id (no cut-down, one step to LIVE). The pull from a Short to its long video is the related-video link - a hand
step, the first line of V3's release card (open issue 135).
What V2c-b2b1 leaves ready (use it, do not rebuild it): `whatifs/opening.py` (D6) - `fetch` (the Short's archive, measured), `lay` /
`mark` (the footage on the shot list: `short` = {id, parts}), `marked(shots)` (the shots that are the Short's footage - any code that
picks shots of a long video for another upload, re-makes clips or turns animated shots into stills must skip them), `fit` / `cut`
(the window), `plan_report` / `shown_report` (checks `opening_footage`, `opening_shown`), `alike` (is this frame of a finished film
that picture? - a measure with a limit taken from pairs known to be the same and pairs known to differ); `hooks.run_hooks(proven=)`;
`tests/paid_calls.py:watch` and `V12V2CB2B_REMOVED` (a paid call that is REMOVED is written into the baseline like this - `room.reels`
is next); `tools/sweep.py:opening_of` (the sweep judges every climbed id).
What V2c-b2a leaves ready (use it, do not rebuild it): `whatifs/release.py` (D9) and tab `Release_Sheet` - `SHEET` (a row per setting and
platform: who sets it, how it is proven), `fit`, `texts` / `text_issues`, `compare` (the receipts), `master` (only the file whose hash is
on the record), `queue` (the hand-over is a record), `short` (D9's run `short_publish`), `gate` (D8's run `release_gate`, check
`release_sheet` at contract stage "release"), `settle` (every tick), `approved`; the pure request bodies `publish.yt_body` /
`ig_reel_params` / `fb_reel_finish` and the read-backs `yt_read` / `ig_read` / `fb_read` with the offline stand-in platform
(`publish.FAKE_FAULTS`); a Short's record on tab `Specials` with `made`, `sha`, `file` (the master in Drive), `cover`; `ladder.went_public`.
What V2c-b1 leaves ready: `whatifs/ladder.py` (D10) and tab `Ladder` - `enter` / `keep`, `read`, `rank`, `promote`, `gate` / `refuse` /
`override`, `pitch` / `claim` / `use`, `topic_report` (check `topic_ladder`), the follow-up orders; `brain.ingest_shorts` by processed
day; `breakout.monitor`; `shorts2.cadence`; the rehearsal that walks the ladder (`run(ep_id=...)`) and `tools/sweep.py:climb`.
Totals other tests and the rehearsal print today: 60 hard checks (36 script, 18 final, 5 short, 1 release), 71 levers, 180 founding Palace
items, SHOW_CHECKS 49 (pinned in `tests/test_v12_exec.py`, `test_v12_rnd.py`, `test_v12_release.py` and `test_v12_cutdowns.py`), 84 tabs, 16 retired
rules, 4 older doors - count them again before pinning one. The older tests run with LADDER_ON FALSE.
Remember (every lesson paid for so far): every new contract check must be classified (`rnd.ORG_CHECKS` or raise `rnd.SHOW_CHECKS`, now 48);
a department run that returns `Out` must say what it did with EVERY inbound memo; a check that can hold a video must RECOGNISE what is
wrong (V1b: four ordinary words; V2c-a: a three-letter word); break the code on purpose and make sure a test fails - write the break list
as "what would fail if this line went?" BEFORE running it (V2c-b1: 31 of 31, and the list itself found a missing test); test a guard with
the case built to defeat it (V2c-b1: 2 of 20 beat 30 of 2,000); ASK WHEN A NUMBER EXISTS before building a rule on it (V2c-b1: YouTube's
numbers are 48 to 72 hours late - read the platform's own page first); seed every random draw by the id (V2c-b1: a test of V2c-a failed
once in eleven runs); a test that builds its own fresh Sheet loses the defaults of `tests/conftest.py`; a new retired-concept rule must
be narrow and needs its strings in the small repository of `tests/test_docs_current.py`; a founding item goes only to the department
that acts on it, and its date is the UTC day (the laptop's UTC date is a day behind the owner's); PROVE A NEW FIRST STEP ON AN EMPTY
SHEET with nothing run before it (V2c-b1: a green suite and four green rehearsals hid that no video could ever be made - both began
with a step that opened uploads by the way; only the sweep saw it); when one job is made to wait for another, list what the waiting
job used to do "by the way"; a status text is data other code reads (V2c-b1: "HELD" meant two things on one tab); WRITE A FINDING INTO
THIS FILE BEFORE THE EDIT THAT FIXES IT (V2c-b1: a session was cut off with a fix applied and no note); the offline clips barely move - a rule
about motion needs a test with clips that do; never run the break script while another run reads the code; never read a result AFTER
writing it into a commit message; run the rehearsal in each long format (`WI_FORMAT`) and each Short format (`WI_SHORT_FORMAT`) before
the suite; NEVER paste code with backslashes through a shell here-document (write the script with the file tool); WRITE THE BREAK LIST BEFORE THE LAST TEST RUN, not after it (V2c-b2a: the list itself found a check that could pass a Short which never reached
YouTube - its test passed for ANOTHER reason - and three missing tests, before a single break ran); a test must fail for the reason it names:
set up ONE fault at a time; THE SWEEP MUST WALK THE NEW PATH (V2c-b2a: the sweep's Shorts were made with `publish=False`, so the only proof
that starts from an empty Sheet had never met an upload); a hand-over is a RECORD, never a status word - and a second pass over a record that
already carries a platform's id may only READ; put a platform's id on record the moment it returns; a scratch script written through a shell
here-document lost its backslashes AGAIN (write every script with the file tool, even a three-line one); READ THE WHOLE BINDING
READING ORDER FIRST (a batch was stopped by the owner for cutting it short); A MEASURE NEEDS BOTH KINDS OF PAIRS BEFORE IT GETS A LIMIT
(V2c-b2b1: a hash of a tiny copy called the film's own footage "different" under a vignette - measure pairs known to be the same AND
pairs known to differ first); A MARK ON A SHOT MUST BE SKIPPED BY EVERY LATER STEP THAT TOUCHES THAT KIND OF SHOT - list those steps
by searching the type's name before the build (V2c-b2b1: the plan check, the Animation Director, the paid repair, the picture
budget, the sound events, the cut-downs, the still that re-uses the nearest earlier picture - seven places, three found only by
running); THE REHEARSAL HAS OLDER ASSERTS OF ITS OWN that pin what a batch changes by design: run all three rehearsals BEFORE the
break run; A BACKGROUND COMMAND CAN BE ENDED BY THE TOOL after about ten minutes - `git status` after every break run, a break
script keeps a copy of every file and runs in short parts, long runs are started detached (HOW TO RUN); REPRODUCE A BAD SWEEP ID
BEFORE EXPLAINING IT (V2c-b2b1: I explained one from the code, fixed another fault, and paid a whole acceptance pass - suite,
sweep, GitHub - before the id itself showed a false hold by my own check: `tools/sweep.py --one <id> --work <dir>` keeps the
folder; measure it); A CHECK THAT COMPARES A FILM WITH ITS CLIPS MUST STAY AWAY FROM CUTS (a frame apart at a cut is another
picture); COUNT WHAT THE CODE WOULD REALLY DO BEFORE DECIDING WHAT TO KEEP (V2c-b2b2: the batch's list named the cut-down
reels; searching every call that uploads an upright video found three more doors and about 38 short uploads a month); A RUN
THAT STOPS WITH EVERY WORKER IDLE IS A FINDING, NOT A FLAKE (V2c-b2b2: a real deadlock - log every finished test by name, dump
the stuck worker's stack with py-spy, HOW TO RUN); NEVER LOG WHILE HOLDING A LOCK THAT A LOG-FLUSH HOOK TAKES; THE REHEARSAL'S
IDS ARE THE MINUTE - a red one is a new id, reproduce it on the ACCEPTED code too before calling it this batch's (V2c-b2b2: a
hold of V2c-b2b1 showed up three batches of rehearsals later); a `wait for a line in a log` must not match the line a PREVIOUS
run left in the same file (V2c-b2b2: I read two old rehearsal logs as new); a script pasted through a shell here-document
lost its backslashes a THIRD time - the file tool, always.
ORDER AFTER V2d (redesign 11.10): V3 PILOT ON REAL SERVICES AND GO LIVE (three Shorts and one long video; the human kit: his
voice recording with the consent sentence, five photos, three sentences, the secrets typed by HIM; the release sheet's one-time
switches - phone verification FIRST, open issue 112, AND ADVANCED FEATURE ACCESS, which is more than the phone: open issue 149;
PAUSED set back to FALSE by HIS hand, only after the held rows were shown to him: open issue 148; the one-minute release card with the Short-to-video link as its first line,
open issue 135; the older doors decided, open issue 136; the bounded ffmpeg install in every workflow, open issue 94; then the
new code replaces the old) -> V2b INSIDE THE FORMAT (first person and the camera path as measured rules, F1's own ending
instead of the asks code still inserts - open issue 74, the speaker chip - 75, F3 "The walk", same-subject line-up titles -
69) -> V1c THE FLOOR, HIS VERDICT AND THE MAKER'S LINE -> V4 the CEO and the ladder (+ his input tab, the scoreboard, the
format and Short shares, long-video views against the Shorts count - 138) -> V5 the Breakout Observatory (Shorts first) and
the aspect map with the release sheet -> B6b -> B7 -> B8 (+ every run names its scoreboard number) -> B9 -> B10. Eleven
batches remain; the channel runs the new code after the second (V2d, V3).
The notes below (what B5 / B6a leave ready for the Council) stay valid for B6b:
**B6b - The Council (C)** (01 sections 2 (C), 4, 5, 7 `council_held`; 03 "B6", second bullet). Full seven-step MANDATORY BATCH LOOP. Effort: High.
Gathers open research / assessment / creative / owner / performance / problem memos; diverge -> blind cross-family jury -> converge -> decision
memo + tickets; owner cards only above thresholds; session takeaways; check `council_held`; C moves from `registry.PENDING` to `ENTRY`.
B6 was SPLIT at its start (token discipline rule 6, 11 Nov 2026: two halves that each need the full loop, the 40-minute suite, the sweep and a
GitHub run). B6a - Creative departments (D4/D5/D6/D7) - is ACCEPTED (record under DONE).
Original B6 scope: 01 sections 2 (D4-D7, C), 3, 5, 7 `council_held`, `canon_in_brief`, `palace_injected`, `palace_cited`; 03 "B6".
What B5 leaves ready for B6b (use it, do not rebuild it):
- Assessment memos (D3 -> C) already carry everything a decision needs: the verdict (accept / test / reject, computed by code), six scores, the
  family checklist, the research memo's evidence, its kind and `palace_ref` (a re-validation names the Palace item), and the pre-registered
  predictions (in the research memo body: action index, metric, direction, horizon). They wait SILENTLY at the owner's level until C is wired: the
  Council's first run must take up every assessment memo at level 2 (and research memos the watchdog escalated after void Board sessions - the
  Board is no longer their holder). `board.assessment_issues(m)` tells whether an assessment can be trusted.
- How the Council turns a verdict into a ticket: accept (a fact) -> lever A (a Palace item; a re-validation = accept the `proposed` item or
  supersede the expiring one named in `palace_ref`), test -> lever C (experiment: `rule`, `metric` = the prediction's metric, `source_url` = the memo's
  best evidence url), reject -> no ticket, the decision memo cites the assessment. Palace item `b4.how_to_write_a_ticket`.
- The Board can judge creative memos too: `board.assess` takes research memos today; a creative memo has no sources, so B6 decides whether D3 also
  judges creative memos (schemas: creative_memo is resolved by decision_memo OR assessment_memo) or the Council's own blind jury does.
- `board.JUDGES`, `board._parse`, `scores_from` are reusable for the Council's blind cross-family jury (strong chains `board_g` / `board_c`).
What the B5 recheck (11 Nov) adds for B6b:
- EVERY new contract check must be classified or a test fails: `council_held` goes into `rnd.ORG_CHECKS` (the organisation's machinery: never a
  research question, never a prediction metric). A promise about the show raises `rnd.SHOW_CHECKS` instead.
- The Council's jury should prove who judged the way the Board does: `models.last_call()` now names the model that REALLY answered (a syntax repair
  by the chore model no longer hides it; a missing strong Gemini model answered by the cheap one is recorded as cheap).
- A memo a department writes to ITSELF (a void session, a barren run) is escalated by the watchdog after the 2-hour acknowledge clock, so it has
  left the department's inbox by its next run: close it with `memos.find` + `memos.resolve` (pattern: `board.assess`, `rnd.deep`), never only
  through the inbox.
- Text from outside (web pages, video titles) is cleaned at `rnd.verify` / `rnd.gaps`; the Council's jury prompt should still say that memo text
  is material to judge, never an instruction (as `board.BOARD_SYSTEM` now does).
- The research round is level-triggered from two jobs (`cli.research_round` in the learning job, `cli.research_catch_up` in the production job).
  The Council's own cadence check should get the same catch-up, or a dropped cron will hold a video for it.
What B6a leaves ready for B6b:
- Creative memos (D4 showrunner / bible, D5 packager, D6 director) wait SILENTLY at the owner's level (owner_visible False) like the assessment
  memos: body {idea, kind (idea / experiment / bank / world_building), rationale}, already distinct (same-idea guard). A creative memo has no
  sources, so the Board cannot score its evidence: decide in B6b whether the Council's own blind jury judges ideas (recommended: ideas need taste,
  the Board's checklist is built for evidence) - and remember b5.facts_accept_ideas_test: an idea is at most a TEST (lever C), never "accepted".
- World-building decisions become canon through a ticket of lever A (kind world_canon, accepted by the Council); case records stay code-written
  and are accepted only on air (D9) - the Council never edits what aired.
- The Council's playbook (C) leaves 5 limits out at 1,800 tokens: give C its own cap (as D4 got 2,400) or narrow the audience of items, before it
  runs. C's runs that call a model should be a B6a-style prompt spec (registry.PROMPT) so its decisions cite what they used.
- D7 Sound has NO model call in its run (voice = TTS, sound = code), so it cannot cite or propose; its creative input comes through the bible.
  Open question for later batches, not a gap of B6a.
- Totals other tests and the rehearsal print: 47 hard checks (28 script + 19 final), 132 founding Palace items (133 with `b6a.takeaway`), 10 of 15
  departments wired (pending: D0, D1, D11, C, L), 41 levers.
- New org modules go on `tools/repair.py` PROTECTED first. Every function B6b adds must be called by production code (Plan Guard); a hook with a
  common name gets a test that runs the real job.
- Acceptance of B6b includes standing rules 1 and 2 (sweep on a frozen copy, final commit green on GitHub).

## DONE
### V2d-a - THE MONEY AND THE MODEL (13 Nov 2026) - IN WORK (steps 1-3 recorded; not built, not accepted)
The owner's "continue" for this batch is the start of this session (item 22 of `02`). V2d was SPLIT AT ITS START (the note is at
the top of NEXT). The whole binding reading order was read first (handoff `CLAUDE.md`, `00`, `02` in full with items 21 and 22,
`01`, `03`, `06`, `04`, `05`, all of the redesign - section 11 with every end note first, then sections 0 to 10 - this file's
head, the standing rules, the owner's verdict section with item 22, NEXT, the V2c-b2b2, V2c-b2b1, V2c-b2a, V2c-b1 and V2c-a
records, every open issue 1-149, HOW TO RUN, the batch log, the repo's `CLAUDE.md`, `docs/CURRENT/` - `SYSTEM.md` to the end of
its tab list - and the hand-over note), then the code the half touches: all of `costguard.py`, `governor.py`, `shorts2.py`,
`preflight.py`, `steward.py`, `scout.py`, `media.py`, `replan.py`, `bakeoff.py`, `tests/paid_calls.py`; the price and model cells
of `core.py`; `episode.est_cost_inr` and the plan stage; `shortseat.shape_report` / `shape`; `opening.manifest`; `anim.start_frame`.

#### Step 1 RESEARCH (E = the provider's or the ranking's own page, O = practice / a third party; every page below was read by the build session itself on 13 Nov 2026; the redesign's R13, R30, R31 and O2, O10 are the base)
1. E read - Artificial Analysis, image-to-video leaderboard "AA-Video-I2V v2.1" (https://artificialanalysis.ai/video/leaderboard/image-to-video;
   no date on the page, ratings "recomputed hourly"): 35 models. The board's anchor is Kling 3.0 1080p (Pro) = 1000 points (rank
   23); Kling 3.0 Omni 1080p (Pro) 1002 (rank 22) - the STANDARD tier we pay is not on the board at all. Above them, with the
   error band of each: Seedance 2.5 1161 +-15 (USD 34.12 a minute on its maker's own service), MiniMax H3 (768p) 1133 +-14 (rank
   4; 4.80 a minute), HeyGen Video 1 1124 +-14 (rank 6; 2.40 a minute), MiniMax H3 Max 1115 +-14 (9.60), Pika H3 Flex 1114 (2.10),
   Wan 3.0 1108 (12.00); below: PixVerse V6 959 +-15 (6.90).
2. E read - Artificial Analysis, methodology (https://artificialanalysis.ai/video/methodology; a change dated October 2026): blind
   pairs fitted with a Bradley-Terry model; error bands "may be slightly narrow"; EVERY model is tested at 1080p where offered,
   24 frames, 10 seconds, 16:9, from a 1920 x 1080 start picture; the price is "on the model creator's API at the settings we
   benchmark". -> the rank says nothing about an UPRIGHT clip at 768p, and the board's price is not the price on fal.
3. E read - fal, the model page and schema of the model we pay (https://fal.ai/models/fal-ai/kling-video/o3/standard/image-to-video):
   "For every second of video you generated, you will be charged $0.084 (audio off) or $0.112 (audio on)"; 3 to 15 seconds; no
   field for a clip's shape. fal's own price list (https://fal.ai/pricing) shows the SAME endpoint at 0.14 a second.
4. E read - fal, the price list (https://fal.ai/pricing, 36 video rows, no date) against the model pages: Grok Imagine Video 1.5
   is listed at 0.01 a second and its model page charges 0.08 / 0.14 / 0.25 by size; PixVerse V6 is listed at 0.005 and its page
   charges 0.025 to 0.115; H3 Max is listed at 0.05, which is its 480p price from 16 Nov. fal's own API reference
   (https://fal.ai/docs/platform-apis/v1/models/pricing) calls the figure a "Base price per billing unit" with "proportional
   adjustments for resolution/length". -> THE FINDING THAT SHAPES THE DESIGN: the price a program can read from fal's listing is
   a base figure, wrong for our setting in four of the five models compared (twice by a factor of ten). Today's weekly tool scout
   (`scout.weekly`) writes exactly that figure times five into `PRICE_KLING_USD` when it differs by a tenth: on the live channel
   it would have set the hero clip to USD 0.70 (the list's 0.14) against the model page's 0.42.
5. E read - fal, model pages and API schemas of the candidates: MiniMax H3 (`minimax/h3/image-to-video`): "$0.05 per second at
   480p, $0.06 per second at 768p, $0.13 ... at 2K and $0.16 ... at 4K"; `duration` an integer of 5 to 15; "the output canvas
   follows this image". HeyGen Video (`heygen/heygen-video/image-to-video`): "animates your image as the first frame of a 5 to 15
   second clip ... built on MiniMax H3"; regular price "$0.02 and $0.06 per second" (480p and 768p / 1080p and 2K; a half-price
   offer ended 31 Oct 2026); `image_url` required, `duration` an integer of 5 to 15, sizes 480p / 768p / 1080p / 2k; the page
   does NOT say where the clip's shape comes from. H3 Max: 0.056 a second at 768p until 15 Nov, 0.08 from 16 Nov 2026. H3 Max
   Turbo: 0.04 at 768p from 16 Nov (not on the board). PixVerse V6: 0.045 at 720p, 1 to 15 seconds. Wan 3.0: 0.05 / 0.10 / 0.20.
   Grok Imagine Video 1.5: 0.14 at 720p. The living-still model in use: USD 0.02 a 5-second clip, unchanged.
6. E read - fal, platform API reference (https://fal.ai/docs/platform-apis/v1/models, .../pricing, .../pricing/estimate): the
   listing needs no key and returns a model's status and, with `expand=openapi-3.0`, its whole input schema; the estimate
   endpoint takes only a number of billing units - "The request has no fields for parameters such as resolution or duration".
   -> a program CAN read live whether a model exists, what it takes and how long a clip may be; it can NOT read the price of
   our setting. That price is on the model's page only, and the bill is the only proof.
7. E read - Google, Gemini API price page (https://aistudio.google.com/docs/pricing): the voice model's audio output costs USD 9
   a million tokens "through December 31, 2026" and 18 from 1 Jan 2027 (the code already switches on that day:
   `tts_gemini.price_out`); a reference-locked start picture USD 0.067 (the cell is right); the Flash text models double on
   1 Jan 2027 too. Anthropic's price page (https://platform.claude.com/docs/en/about-claude/pricing): the three text price cells
   are right.
8. O read - TeamDay, "fal.ai pricing 2026", 2 Nov 2026 (https://www.teamday.ai/blog/fal-ai-pricing-2026; a third party): "The
   base price in fal's billing data is not always what you pay" - with the same example (0.01 listed, 0.14 charged); server
   errors are not billed, a request refused for its input can be. -> confirms 4; a wrong request body is not free.
NOT FOUND, so nothing is built on it: a rank for an upright clip or for 768p; whether fal's "HeyGen Video" is the board's "HeyGen
Video 1" (the same maker and model family; nobody says so in one sentence); where that model takes its clip's shape from; a
price for Pika H3 Flex on fal; any way for a program to read what a request really cost (fal's queue answers carry no cost; the
usage reports need another kind of key); the real cost of the text calls of the NEW code (never run for real).
AN EXPERIMENT BEFORE THE DESIGN (the accepted code, fake mode, a fresh store, December's Rs 5,000; counted, not guessed):
(1) What the code estimates TODAY - a long video Rs 560.7: 4 hero clips Rs 166.3, 52 stills 23.7, 8 living clips 15.8, 2 key-art
pictures 15.8, writing 176, the table read 55, thinking 40, the room's extra calls 20, the Palace in the prompts 15, the voice 30,
two small community lines 3. A Short Rs 287 (6 hero clips Rs 249.5, 3 pictures 0.9, writing and voice 36). The month: Rs 5,000
less the maintenance reserve 100, the owner's earmark 200 and the organisation's thinking caps 420 = Rs 4,280 for production.
Four long videos take Rs 2,243; what is left pays 7 Shorts, not 12 - and the cadence makes three a week until the money for the
long slots would be touched, so the 7 fall into the first sixteen days and then no Short is made for two weeks.
(2) FOUND, A FAULT OF THE OLDER CODE: Rs 55 of every long video's estimate is money for calls that are never made. The table
read (an objections round and the Director's read) belongs to the older writers' room; under the room in use (`ROOM_MODE` v2)
`room.run_room` sets it off for every episode - while `governor.full_episode_inr`, `min_episode_cost_inr`,
`costguard.estimate_lines`, `models.ai_estimate_inr` and `episode.est_cost_inr` all still add `TABLE_READ_EXTRA_INR` because the
cell `TABLE_READ_MODE` says "on". Rs 220 a month held back for nothing: three of the five missing Shorts' worth of writing.
(3) FOUND: four paid calls of every long video are in NO estimate - the reference-locked start pictures of the animated scenes
(`anim.gemini_image`, USD 0.067 each: Rs 26.5 a video). And a still is estimated at the old flat USD 0.0046 while the code pays
0.006 (two megapixels): Rs 7 a video too little.
(4) A Short's clip is five seconds because the request says "5", whatever the shot needs: a beat of 6.5 seconds is one clip
played 30% slower, a beat of 3 seconds pays for 5.
#### Step 2 CREATIVITY (scores 1-5: what a viewer or the channel gains / enforceable / cost / reliability / owner effort)
A. Type the best-value model of today and its price into the two cells: 3 / 2 / 4 / 2 / 5 = 16 - right this week; no rule, so
   the next price move is again a session's job, and the estimate stays lumps nobody can check.
B. "Arena points per dollar" as written in the redesign, computed weekly from fal's listing: 1 / 3 / 5 / 1 / 5 = 15 - the ratio
   rewards cheapness: with today's page prices it picks PixVerse V6 (959 points - ranked BELOW the model in use), and with the
   listing's own prices (research 4) it picks whatever has the smallest placeholder.
C. The cheapest model above a fixed rank: 3 / 4 / 5 / 3 / 5 = 20 - enforceable, but the floor is a number somebody types and
   nobody moves, and it treats saving as the goal ("savings never the goal").
D. A strong text model reads the pages and chooses: 2 / 1 / 4 / 2 / 5 = 14 - a taste call without eyes (redesign R9), paid, not
   reproducible, and it would read the listing's placeholder like the scout does.
E. (ORIGINAL, CHOSEN) THE BEST MODEL THE PLAN CAN PAY, BOUGHT BY THE SECOND, IN AN ESTIMATE THE COUNTER CAN CHECK. (1) The
   clip market is DATA: a table of models, each row what the provider's own page says - the price per second at each size, how
   long a clip may be, the field its start picture goes in, where the clip's shape comes from, its rank with its error band,
   the page and the day it was read. (2) The month's plan - four long videos, twelve Shorts, the fixed parts, a reserve - gives
   THE LINE: the highest price per second of animation the plan can pay. (3) Among the models that take a start picture, give
   an upright clip and cost no more than the line, the highest rank wins; models whose error bands overlap the best one's are
   tied, and among the tied the cheaper wins (what it frees buys moving seconds). A model without a rank is never picked; a
   model ranked below the one in use is never picked by code. (4) When no ranked model is under the line the plan does not fit:
   the code keeps quality, says how many Shorts DO fit, and the cadence spreads that number over the month. (5) A clip is bought
   BY THE SECOND at the length of its shot - no slowed clip, no second paid and thrown away beyond the model's shortest clip.
   (6) The estimate is ONE table of lines - every paid second and call, its count and its price cell - that every gate reads,
   and each line names the paid calls it stands for, so the paid-call counter checks the estimate call by call: 5 / 5 / 5 / 4 / 5 = 24.
#### Step 3 DESIGN MEMO
- THE CLIP MARKET (`whatifs/clips.py` NEW, Visual Production D6; on `tools/repair.py` PROTECTED; cell `CLIP_MODELS`, a JSON
  table): a row = the model's id, its name on the ranking, `usd_s` (price per second by size), `res` (the size we buy), `min_s` /
  `max_s`, `start` (the field of the start picture), `dur` (a whole number or a word), `shape` (follows the picture / stated
  where), `elo` and `ci`, `page`, `read`. Six rows as read on 13 Nov 2026. No model name is typed in code: the table is a
  Settings cell, and the request body is built from the row (`clips.args`), not from a name match.
- THE RULE (`clips.pick`, pure code): described in E (3). The line comes from the cost model (`governor.line_usd_s`). With
  the pages of 13 Nov 2026 the pick is HeyGen Video at 768p: rank 6 of 35 (1124 +-14, tied with MiniMax H3's 1133 +-14 by
  their error bands), USD 0.02 a second against 0.06 for H3 and 0.084 for the model in use, which the board does not rank (its
  dearer tier stands at 1002, rank 22). Next in line when it fails: MiniMax H3 at 768p.
- WHEN (`clips.review`, inside the weekly tool scout; the Model Steward makes the switch, writes tab `Model_Changes` and tells
  the owner with "Discuss"): the table's rows are checked against fal's live listing - is the model still listed and active,
  does its schema still have the start-picture field, the size and the clip lengths the row says (`clips.refresh`) - and the
  pick is made again. The listing's base price is KEPT with the row and only watched: when it moves, the row is marked stale
  and the owner gets one message that the model's page must be read again. It is never written into the estimate (research 4).
  The Steward's fail-over for the hero asks `clips.pick` (a dead model's row is not eligible), so a replacement is chosen by
  the same rule and never by a price ratio.
- BOUGHT BY THE SECOND (`media.animate(seconds=)`): a clip is asked for at the whole seconds its shot needs, inside the model's
  shortest and longest clip; the cost row says the seconds and the price per second. `shorts2.plan` gives every shot ONE clip
  as long as the shot (a beat longer than the model's longest clip is split); nothing is slowed (closes open issue 82's first
  point). A Short made before this batch keeps its record: the plan of each shot carries how it was played, and the opening of
  a long video reads that.
- A MEASURED GUARD: a hero clip whose shape is not its start picture's is a failed clip of that model - reported to the
  Steward like any failure (three in a row: the next model in line). Needed because one page does not say (research 5).
- THE COST MODEL (`costguard.lines(kind, ...)`, kinds `long` / `ladder` / `short`): one list of lines - the hero seconds, the
  start pictures, the stills at the real megapixel price, the living clips, the key art, the voice by the second at the price
  of the day, the writing, the thinking, the room's extra calls, the hook lab, the promise line-up, the Palace in the prompts,
  the community lines - each with its count, its unit price, its rupees and the paid calls it covers (`calls`).
  `governor.full_episode_inr`, `min_episode_cost_inr`, `episode.est_cost_inr`, `shorts2.est_inr`, `costguard.estimate_lines`
  and `models.ai_estimate_inr` all read it: one arithmetic. A long video about a promoted Short is its own kind (three scenes,
  three start pictures, no hook lab - open issue 126); a Short has its own lines (83); the line-up has its line (72); the
  writing and the voice lose what the cut-downs took with them (141); the table read is counted only where it runs (the fault
  above). After a video or a Short is made, `costguard.reconcile` sets what was really paid (tab `Cost_Log`) against the lines
  and writes one summary row; a paid item no line covers, or a counted line that was exceeded, is named in the log.
- THE SPLIT (`governor.split`): the month as a table - the cap, the fixed parts, the reserve (`MONTH_RESERVE_INR`: failed
  tries and a winner's follow-up), the long videos with the safety margin, the Shorts by the shares of their formats - and how
  many Shorts FIT. `shorts2.cadence` makes at most that many this month and spaces them over the month instead of running dry
  in the third week; when fewer fit than `SHORTS_PER_MONTH` asks, the owner is told once a month with both numbers. The lever
  that carries the plan stays `SHORTS_PER_MONTH` (the Shorts Studio's since V2c-b1): the redesign gives the split to Strategy
  (D1), which is not wired before V4 - a lever on a department that cannot run cannot be turned by anybody, so the number that
  binds is computed by code now and the lever moves to D1 when D1 exists (a new open issue).
- PRE-FLIGHT (`preflight.run`): the hero model is on fal's listing, active, and its schema matches the row - a warning, never a
  block (the Steward's next model stands ready). SWITCH: `CLIP_VALUE_ON` (FALSE = everything as before this batch: the hero is
  what `FAL_HERO_MODEL` says, five-second clips at `PRICE_KLING_USD`, slowed up to 30%).
- A LIVE SHEET IS MOVED ONCE (`manage.v12v2d_upgrade`): `FAL_HERO_MODEL` and `PRICE_KLING_USD` go to the picked model where
  they still hold the old defaults; `TABLE_READ_MODE` is left alone (the estimate now asks whether the table read RUNS).
- AT THE PILOT (V3, said here so that it is not lost): the first real step is the bake-off that exists (`bakeoff.run`, two
  scenes, capped): the picked model, the next in line and the model in use side by side on UPRIGHT pictures - the owner's eye
  decides, and the first clips' real cost is read on fal's own usage page.
- CHANGED FROM THE REDESIGN, with reasons: (1) "rank per dollar" / "arena points per dollar" is not a ratio: a ratio picks the
  cheapest model, below the one in use (design B). The rule is the best rank the plan can pay; ties by error band go to the
  cheaper. (2) "from the live listing": the listing gives existence, inputs and clip lengths; its price is a base figure that
  is wrong for our setting (research 4, 6), so the price per second is a dated reading of the model's page in the table and
  the listing only raises the alarm when it moves. (3) Half (b) of V2d spends what this frees: "AI-moving seconds per long
  video" is not raised here.
- MONEY, said before the build (prices from the pages of 13 Nov 2026 at Rs 99 a dollar; NOT measured on a real bill; the
  text lines are allowances no real run of the new code has met):
  | | today (the code's own estimate) | after this batch (planned) |
  |---|---|---|
  | A Short (S1, the middle of its band) | Rs 287: 6 clips of 5 s at USD 0.084 a second 249.5; 3 pictures 0.9; writing and voice 36 | about Rs 80: 21 paid seconds at USD 0.02 = 41.6; 3 pictures 0.9; writing 36; voice (27.5 s and one re-take) 1.3 |
  | A long video about a promoted Short | Rs 560.7 (counted as if it bought 4 scenes, a hook lab and a table read) | about Rs 385: 3 scenes of 5 s 29.7; 3 start pictures 19.9; 52 stills 30.9; 8 living clips 15.8; 2 key-art pictures 15.8; writing 170; thinking 40; the room's extra calls 20; the Palace 15; the line-up 0.5; the voice (540 s and one re-take) 24.8; community 3 |
  | A long video under an override | Rs 560.7 | about Rs 406: one scene, one start picture and the hook lab more |
  | The month (Rs 4,280 for production) | 4 long videos and 7 Shorts; the Shorts stop in the third week | 4 long videos (Rs 1,694 with the 10% margin) + 12 Shorts (about Rs 1,000) + the reserve 300 = about Rs 3,000; about Rs 1,300 not planned |
  What is not planned is not saved: the re-planner that exists offers it as one more Short a week (the owner's tap), and half
  (b) raises the moving seconds of a long video with it. If the pilot's bake-off sends the owner to MiniMax H3 (USD 0.06):
  a Short is about Rs 163, a long video about Rs 444, the month about Rs 4,200 - twelve Shorts still fit, with nothing left.
  At the price of the model in use (0.084) they do not: 9 fit.
- HYPOTHESES: H25 the picked model's upright clips at 768p look at least as good to the owner as the model in use (the pilot's
  bake-off, his eye). H26 a Short's real cost is within a fifth of its estimate (the first three real Shorts; `reconcile`).
- NOT IN V2d-a, on purpose: the living tier and the moving seconds of a long video, `moving_share`, the micro-cuts that hide
  part of a paid scene (130), a character drawn or absent, the stock rules, the first-second sound of a Short (all V2d-b); an
  offline clip that follows its start picture's shape (the offline clips stay wide: open issue 123); wiring Finance (D11).

### V2c-b2b2 - THE CUT-DOWNS (12-13 Nov 2026) - ACCEPTED (final code commit 1d3a77a GREEN in GitHub Checks run 131: 1457 passed; sweep 58 of 58 ids)
The owner's "continue" for this batch is the start of this session. The whole binding reading order was read first (handoff `CLAUDE.md`,
`00`, `02` in full, `01`, `03`, `06`, `04`, `05`, all of the redesign with section 11 and its end notes first, this file's head, the
standing rules, NEXT, the V2c-b2b1, V2c-b2a, V2c-b1 and V2c-a records, every open issue 1-134, HOW TO RUN, the batch log, the repo's
`CLAUDE.md`, `docs/CURRENT/` - `SYSTEM.md` to the end of its tab list, the rest of it is generated listings - and the hand-over note),
then the code the batch touches: `reels.py`, `room.reels` / `past_footage`, the plan stage and `_finish` of `episode.py`,
`manage.tick` / `release` / `_post_reel` / `_release_extra`, `specials.run` / `_publish` / `approve`, all of `release.py`,
`pilots.py`, `herostill.make_for_episode`, `shortslab.py`, the two contract probes, `tests/paid_calls.py`.

#### Step 1 RESEARCH (E = measured or the platform's own page, O = practice / vendor; every page below was read by the build session itself on 12 Nov 2026; the redesign's R1-R52 are the base)
1. E read - YouTube Official Blog, "How to convert YouTube Shorts views into long-form channel growth", 14 Jul 2026
   (https://blog.youtube/creator-and-artist-stories/youtube-related-videos-traffic-guide/): "The most effective tool for this is the
   Related Videos link"; a Short clipped from a long video must "function as a standalone piece of value"; when a viewer comes over,
   "reward them instantly" - the first 5 to 10 seconds of the long video must pay what the Short promised; a spoken pointer in the
   Short's last 5 seconds is advised. The post gives NO number for how many viewers the link moves.
2. E read - YouTube Help 14075157, "Add a related video to your YouTube Shorts" (no date on the page; copyright 2026): "Adding a
   related video is only available with advanced feature access"; the target must be the channel's own video, "public or unlisted";
   it is set in YouTube Studio, per Short. -> the pull from a Short to its long video is a HAND step (no API field: this file's
   V2c-b2a record, research 3), and it needs the same phone verification the Shorts thumbnail needs (open issue 112).
3. E read - YouTube Help 15824265, "Video Clips & Shorts in YouTube Studio" (no date; copyright 2026): a Short cut from a long video
   WITH STUDIO'S OWN TOOL gets "the source video ... automatically added as a related video"; creators "won't be penalized for
   using your content in a video clip or Short". -> the one mechanical gain of a cut-down - the link - exists only for a Short cut
   by hand in Studio. A cut-down uploaded by code carries no link at all.
4. E / O read - AIR Media-Tech, "Do YouTube Shorts help your long-form videos? Data from 18,000 channels", updated 28 May 2026
   (https://air.io/en/audience-growth/do-youtube-shorts-help-your-long-form-videos-grow-data-from-18000-channels; Mar 2025 - Mar
   2026, 11 niches; a vendor; its own words: "Correlation isn't causation"): the best mix is 25% to 40% Shorts by upload count,
   "above 55% ... long-form performance drops"; SCIENCE is the niche where long-only channels lead (16% more subscribers at mid
   size): "Most science YouTube Shorts are highlight clips or experiment teases that either give away the payoff entirely or stop
   too abruptly to satisfy"; the science channels that win with Shorts "treat each one as a complete micro-argument" - "make them
   genuinely self-contained, not a teaser that requires long-form to pay off"; "a sudden flood of YouTube Shorts ... consistently
   poor across every niche". Its figure "from 0.04% to 0.5% Shorts-to-long-form conversion" with the Related Video field has no
   source on the page: recorded as a claim, not as evidence.
5. E read - Metricool, "YouTube Trends 2026", 29 Jul 2026 (https://metricool.com/youtube-trends/; 799,718 videos, 71,177 accounts;
   "Correlation isn't causation here"): channels with no Shorts average 4,364 views a long video, with about 5 Shorts a month
   8,789; "channels posting 35 or more Shorts a month see their long-form performance fall back" to the level of none; a Short
   does best per post at 2 to 4 a week. (Confirms the redesign's R2 from the page itself.)
6. E read (abstract) - Rajendran, Creusy, Garnes, "Shorts on the Rise: Assessing the Effects of YouTube Shorts on Long-Form Video
   Content", arXiv 2402.18208, 28 Feb 2024, revised 8 Apr 2024: 250 large creators, before and after their first Short - "a
   significant decrease in both view counts and engagement in long-form videos". Before / after, large channels only: an
   association. -> more short uploads are not free for the long videos; three sources (4, 5, 6) point the same way.
7. O read, weak - an Australian news outlet's own six-month test, 4 Feb 2026 (187 Shorts, 3.2 million views;
   https://forestmedia.pages.dev/blog/2026-02-04-youtube-shorts-news-experiment-results; one unnamed outlet, a promotional page):
   "Taking segments from longer packages and cutting them to 60 seconds almost never worked"; "Very few viewers clicked through
   from Shorts to the main website or longer content."
8. E read - PPC Land, 6 Jul 2025, on YouTube's rule in force since 15 Jul 2025
   (https://ppc.land/youtube-improves-detection-systems-for-unoriginal-content/): content that is "mass-produced or repetitive"
   earns nothing; clip compilations "with little or no narrative" are named. Nothing in it names a creator's own footage.
9. O read, second hand - PodcastVideos, 21 Oct 2026, on a reported change of 1 Oct 2026 (it cites other outlets, no YouTube page;
   the redesign's R26 is the same report): original Shorts get more visibility; "a sustainable Shorts workflow can still reuse
   material from longer productions" but "selection, framing, and editorial contribution need to give each cut a clear reason to exist".
NOT FOUND, so nothing is built on it: any measured comparison of a Short cut from a long video with a Short made for the feed; any
measured rate at which a Short sends viewers to a long video (YouTube's own post gives none); any API field for the related-video
link; any study of how many short uploads a month a channel of four long videos can carry (the three studies above know "about 5"
and "35 and more" and a mix of 25% to 40%).
AN EXPERIMENT BEFORE THE DESIGN (read from the code and counted, no run needed): what the code would upload in a month with its own
defaults. (1) Twelve standalone Shorts through `release.py` - three native uploads each, read back. (2) SIXTEEN cut-down reels (4 a
long video) through `manage._post_reel`: one text for every platform, "#shorts" in title and text, a "Full video" line and a
follow / share ask spoken at the end, nothing read back. (3) EIGHT OR NINE "pilot Shorts" (`PILOTS_ON` TRUE, Wednesday and Friday;
`pilots.run`): four stills with a push-in - a slideshow - ending on a plate "Should the jury hear this case? Comment YES. Full
trials Tue + Sat." (4) Two special reels a month (`SPECIALS_ON` TRUE; `specials._publish`): "New trials every Tuesday and
Saturday ... Take your seat on the jury: subscribe." About THIRTY-EIGHT short uploads a month - past the 35 at which long videos
lose what Shorts gave them (research 5) - through FOUR doors, three of them unread, two of them stating a cadence the channel does
not have, and all three with an ask. Only the cut-downs were on this batch's list; the pilots and the other doors were found by
searching every call that uploads an upright video. (5) What a cut-down is: each chosen shot of the WIDE video scaled until it
fills 9:16 - the middle 31.6% of the picture, enlarged 1.78 times - for an equal share of the length, mostly stills; it opens on a
0.4-second cover plate; its lines are written by a paid planning call and spoken again by the voices; two of its four covers are
paid key art. Judged by the Short's own seat it would fail `short_open` (a plate first) and `short_shape` (an ask, stills). (6) The
long video's release is tied to it: `manage.release` runs as release 1 (SCHEDULED -> LIVE1: public check, the channel comment,
the carousel, reel 1) and release 2 six hours later (LIVE1 -> LIVE: reel 2); reels 3 and 4 on the following days.
#### Step 2 CREATIVITY (scores 1-5: what a viewer or the channel gains / enforceable / cost / reliability / owner effort)
A. Keep the four cut-downs and move them onto `release.py`: 1 / 4 / 3 / 3 / 5 = 16 - 28 or more short uploads a month, each one a
   teaser of cropped stills with an ask: the kind research 4 says fails in science, in the number research 4, 5 and 6 warn about.
B. ONE cut-down a long video, planned by the model as today (the redesign's 4.2 point 5 as first written), through `release.py`:
   2 / 4 / 4 / 3 / 5 = 18 - still a paid call, two paid covers and a second voice job for the weakest short video on the channel;
   a cut uploaded by code gets no link to its long video (research 3), so it cannot do the one thing it is for.
C. (ORIGINAL) A cut made by code from what is paid: the long video's three animated scenes with their own sentences, upright,
   through `release.py` as its own kind: 2 / 4 / 5 / 3 / 5 = 19 - free, but fifteen seconds of three unconnected peaks is no
   "standalone piece of value" (research 1) and code cannot check that it is; the wide scene keeps a third of its picture; it
   would need a second, lower standard for "a Short" beside the seat the owner asked for (item 20: never a by-product).
D. A second standalone Short on the topic at the long video's launch, made by the Shorts Studio: 3 / 4 / 2 / 4 / 5 = 18 - a real
   Short, at the full price of one (about Rs 290), for a topic that already had its shot; it takes a slot from a new topic.
E. (ORIGINAL, CHOSEN) THE SHORT THE VIEWERS CHOSE IS THE PULL, AND THERE IS ONE DOOR: no cut-down is made at all. A topic already
   has the Short that real viewers picked; the long video opens on its footage and its hook (V2c-b2b1 - exactly what YouTube's own
   post asks of the first seconds). The pull from that Short to its long video is YouTube's "most effective tool", the related-video
   link, which only a hand can set: it stays the first line of the one-minute release card (V3) and is never called done by the
   machine. Everything that made, voiced, covered, counted, checked and posted cut-downs is REMOVED; the long video's release
   becomes one step. And because the count only means something when it is true: every upload of an upright video goes through
   ONE door (`release.py`) - the three older doors that were found (pilot Shorts, special reels, the hero-still Short and the
   audio-drop Reel) are switched off by default, named on a list that may only shrink, and a new door fails the build:
   4 / 5 / 5 / 5 / 5 = 24.
#### Step 3 DESIGN MEMO
- WHAT THE CHANNEL POSTS: twelve short videos a month - the standalone Shorts of the cadence (plus one follow-up of a winner) - each
  as three native uploads through `release.py`, and four long videos: 16 uploads, 4 a week, the redesign's own plan (11.10). No
  cut-down, no pilot Short, no special reel goes out unless the owner himself switches one back on.
- THE CUT-DOWNS ARE GONE, not switched off: `room.reels` (the paid planning call), `room.reel_count` / `reel_style` /
  `past_footage`, `reels.build_reel` / `reel_lines` and the module with them, the two paid covers and the two free ones, the second
  voice job, `manage._post_reel` / `_release_extra` / `extra_reel_due`, releases 2 to 4, the checks `shorts` and `short_covers`
  (60 hard checks: 36 script, 18 final, 5 short, 1 release), the prompt `REEL` with its three styles, the packager's and the
  showrunner's reel fields, the role `reels`, the cells `REELS_PER_VIDEO`, `REEL_STYLE`, `REEL1_SHORTS_ON`, `REEL2_DELAY_MIN`,
  `REEL3_DELAY_MIN`, `REEL4_DELAY_MIN`, the sampler's draw of reel formats and its credit in the learning job.
- THE LONG VIDEO'S RELEASE IS ONE STEP (`manage.release`): `REEL1_DELAY_MIN` minutes after its slot - is it public? (else the
  alert and the wait, as today) -> the channel comment -> the carousel of a trial -> LIVE. A row an older job left in LIVE1 is
  closed to LIVE by the next tick and nothing is posted for it.
- ONE DOOR (`whatifs/truth.py`, NEW list `OLD_DOORS` beside the three lists of things that were never wired): code finds every
  function of the pipeline that uploads an upright video (`yt_upload(short=True)`, `ig_reel`, `fb_reel`). Outside `release.py`
  only the listed ones may exist - `specials._publish`, `pilots.run`, `herostill.make_for_episode`, `insights.post_drop` - each
  with what is true today (off by default; what must happen before it may come back: through `release.py`); the list may only
  shrink; a new door fails Plan Guard, the tests and check `docs_current`.
- THE OLDER TRACKS ARE PAUSED BY DEFAULT (the redesign's 4.7 FOCUS, decided on 11 Nov 2026 and never executed in code: "until a
  long video of the new code reaches 1,000 views, everything that is not the core is paused"): `PILOTS_ON` FALSE (the ladder
  tests a topic with a real Short; a pilot is four stills and an ask), `SPECIALS_ON` FALSE (their Rs 300 earmark returns to
  production by the governor's own rule). The cast intro stays a hand-started workflow behind the owner's Approve.
- A LIVE SHEET IS MOVED ONCE (`manage.v12v2cb2b_upgrade`): the rows of the retired cells are marked RETIRED in their notes;
  `PILOTS_ON` and `SPECIALS_ON` are set to FALSE where they still hold the old default, with the reason in the note.
- TRUTH: retired rule `cutdown_reels` - a current doc, a docstring or a prompt that speaks of Shorts cut from the long video as
  something the code makes fails Plan Guard, the tests and check `docs_current`.
- CHANGED FROM THE REDESIGN, with reasons: 4.2 point 5 "one more Short is cut from its best moment" is NOT built. 11.4, written
  later and the binding section, says a Short is "never a trailer, never a cut-down"; 11.10 counts 16 uploads a month with no
  cut-down among them; the one thing a cut-down does for its long video - the link - a code upload does not get (research 3);
  and the evidence found says a teaser cut from a long video is what fails in science (research 4, 7).
- NOT ADOPTED, on purpose: YouTube's advice of a spoken pointer in a Short's last five seconds (research 1). A Short is made one to
  two weeks before a long video about it exists, two Shorts in three never get one, and the Short's own rule is no ask (item 20).
- HYPOTHESIS: H24 a long video whose Short was linked to it by hand gets more of its first-week views from the Shorts feed than
  one whose Short was not (Analytics traffic source; the learning job already reads it).
- MONEY, said before the build (prices from the Settings cells, not measured): a long video no longer pays the cut-downs'
  planning call (one call on the editing model, about Rs 5-8), two premium cover pictures (about Rs 7 each at the premium
  price cell) and four short voice jobs (about two minutes of speech, about Rs 5): about Rs 25 a long video, about Rs 100 a
  month. With the special reels paused their Rs 300 earmark is production money again; the pilots' Rs 40 a month is not spent.
  Nothing new is paid. The paid-call counter must show the removed calls before any of this is claimed as done. The known gap
  stays: at today's clip price twelve Shorts a month do not fit beside four long videos (open issue 83, V2d).
- NOT IN THIS BATCH, on purpose: the release card with the link (V3); rebuilding the special reels, the cast intro, the pilots
  and the hero-still reel on `release.py` or deleting them (a new open issue - the batch that prepares the pilot decides which
  of them the channel still wants); the cost model (V2d).
- FOUND WHILE PROVING (each written here before the edit that fixes it):
  (1) **A JOB CAN HANG FOR EVER IN THE PROMPT-CACHE BOOKKEEPING - a fault of the older code, not of this batch.** Two of the
  first three parallel test runs of this batch stopped at 93-96% with every worker idle and no child process, for half an hour.
  I named the test that never finished (`tests/test_v86.py::test_missing_analytics_...`, a learning-job test; every finished
  test logged by name) and dumped the stuck worker's stack with py-spy: `manage.learn` -> `premise.refill_bench` -> `models.ask`
  -> `CacheManager.blocks` -> `core.log` -> `core.flush_log` -> `CacheManager.flush` -> `CacheManager.rows`, waiting for
  `CacheManager.lock`. `blocks` writes the warning "prompt cache: two calls share a prefix but differ in model parameters"
  (open issue 23: printed on EVERY long video) WHILE IT HOLDS that lock; `core.log` flushes its buffer at every 40th line; the
  flush calls the cache manager's own hook, which asks for the same lock - a lock that cannot be taken twice by one thread. So
  whenever that warning is the 40th buffered line, the job stops for ever: about one chance in forty per warning, on the
  live channel a production or learning job stuck until GitHub's six-hour limit, its slot lost. It showed now because this
  batch changed how many lines a run logs (no reel lines), which moved the 40th line onto the warning in one worker's order.
  Fix at the cause: nothing is logged while the lock is held (the warning is decided inside the lock and written after it);
  a test that fills the buffer to 39 lines and makes the two calls must return; a deliberate break.
  (2) THE PAID-CALL COUNTER NEVER SAW KEY ART OR A VOICE JOB. To show what the cut-downs cost I looked at the counter first: it
  patches `media.still` and counts no voice job at all, and `art.py` holds its own name for `still` - so the thumbnail and the
  two reel covers were never counted, and neither were the four reels spoken again. The counter now patches every module's
  own name for both; measured on the accepted code of V2c-b2b1 and on this code, one fake long video each: `text:reels` 1 -> 0,
  premium pictures 4 -> 2, voice jobs 5 -> 1, every other count identical.
  (3) THREE MORE PLACES STILL SPOKE TO A REEL PRODUCER, found by the older tests once the function was gone: the optional older
  writers' room had a sixth role "REEL PRODUCER" (a paid memo and a paid objection per video in that mode), the continuity
  check was asked to compare "reel lines vs facts", and the rulebook's research prompt offered a department "reel". All three
  are gone. And one function left without a caller (`show.clipbait_lines`: the fourth reel was its only user) and two cells
  nothing read any more (`KINETIC_CAPTIONS_ON`, `TRIAL_SHORTS_SAFE_ON`) were named by the truth registry at once and removed.
  (4) THE BREAK LIST, written before any break ran ("what would fail if this line went?"), found two lines of my own that
  changed nothing - a status word set on a row the tick had already closed, and a filter in the sweep's summary that no
  result could ever need. Both are gone.
  (5) **A LONG VIDEO ABOUT A PROMOTED SHORT COULD BE HELD FOR ITS SHORT'S OWN HOOK - a fault of V2c-b2b1 (the opening), found
  by this batch's third rehearsal (the trial with Shorts in S2, id EP202611121845).** HELD at the script gate by check
  `retention`: "the first line clears its throat (a greeting, 'today', 'did you know')". Reproduced alone before anything was
  explained (`tools/sweep.py --one EP202611121845 --mode rehearsal`, F2 / S2) on this code AND on the accepted code of
  V2c-b2b1 (a frozen copy of 01ad81e): the same hold on both - not this batch's change. Measured: the promoted Short is in
  format S2 "What would you do?", whose first beat is "you gain or lose one power"; its hook is "Today you lose the rain.";
  V2c-b2b1 makes that hook the long video's first line, word for word; and the long video's opening rule (`hooks._GREET`, read
  by `growth.py` and by the hook lab) takes ANY first line that begins with "today" for throat-clearing. The Short's own seat
  already knew better (`shortseat.GREET_RX` names "today we"; a test says "Today the moon lets go of you" is no greeting). The
  rule did not recognise what is wrong - the fifth time this build pays for that. The rehearsal's ids are the minute, so it
  never met this script before; no fixed sweep id of V2c-b2b1 promoted it. On the live channel it would have been an owner
  card for every long video whose Short opens "Today you ...", and for an F1 writer who opens "Today, gravity lets go" ("ONE
  law of nature is different today" is F1's own brief). Fix at the cause: "today" is a greeting only where a presenter speaks
  ("today we", "today I", "today's video", "today, let's"); tests both ways on the pattern, on the opening rule and on the hook
  lab; the id itself re-run alone before any other proof.

#### Step 4 BUILD (what changed)
- GONE: `whatifs/reels.py` (the module); `room.reels`, `reel_count`, `reel_style`, `past_footage`, `_reel_extra`; in
  `whatifs/episode.py` the reel plan in the plan stage, the two paid covers and the two free ones, the reel build with its
  second voice job, the clean copies of reel shots in the renderer, the reels on the release record and on the result;
  `manage._post_reel`, `_release_extra`, `extra_reel_due`, `cap_hashtags`, releases 2 to 4 (tick, CLI); the probes and rows of
  checks `shorts` and `short_covers` (60 hard checks: 36 script, 18 final, 5 short, 1 release); `prompts.REEL` and its three
  styles, the packager's cover fields, the showrunner's reel hooks; the role `reels` (`models.ROUTES`, `SAVER_MEDIUM`); the
  reel asks of `cta.py`; `art.reel_cover`, `reel_cover_free`; `show.clipbait_lines`; the craft note, the strategy seeds and the
  rulebook department "reel"; the sixth role of the older room; the cells `REELS_PER_VIDEO`, `REEL_STYLE`, `REEL1_SHORTS_ON`,
  `REEL2_DELAY_MIN` (a lever of D9: 71 levers), `REEL3_DELAY_MIN`, `REEL4_DELAY_MIN`, `KINETIC_CAPTIONS_ON`,
  `TRIAL_SHORTS_SAFE_ON`.
- `whatifs/manage.py`: `release` is ONE step (public? else the alert once and the wait -> the channel comment -> the carousel
  of a trial -> LIVE); the tick names it `REEL1_DELAY_MIN` minutes after the slot and nothing afterwards; `_give_up_stuck` closes
  a row an older version left at LIVE1 without posting; `shorts_lesson` (what a video's Shorts traffic leaves on tab Lessons);
  `v12v2cb2b_upgrade` at both setup sites (eight dead cells marked RETIRED, `PILOTS_ON` and `SPECIALS_ON` set to FALSE where
  they still hold the old default, never twice).
- `whatifs/truth.py`: retired rule `cutdown_reels` (16 rules) with its baseline for the one-time move; `OLD_DOORS` (four older
  doors, each with the switch that shuts it; limit 4), `short_doors` (reads the code: every function outside `release.py` and
  `publish.py` that calls `ig_reel`, `fb_reel` or `yt_upload` with `short` set), `door_issues` - part of `truth.issues`, so
  Plan Guard, the tests and check `docs_current` all refuse a new door.
- `whatifs/sampler.py`: the draw carries no reel strategy and no reel formats (a video an older version made keeps its
  credit: `manage.strategy_credits` is unchanged). `whatifs/governor.py`: `premium_images` = the thumbnail and its runner-up.
  `whatifs/core.py`: `PILOTS_ON` and `SPECIALS_ON` FALSE by default with what TRUE would do, `V12V2CB2B_MOVE_DONE`, the note
  of `REEL1_DELAY_MIN`. `whatifs/models.py`: THE DEADLOCK FIX (above). `whatifs/org/registry.py`, `levers.py`, `rnd.py`:
  2 check owners and 1 lever gone, SHOW_CHECKS 49.
- `tools/rehearsal.py`: the long video's release is one step and the rehearsal asserts that no cut-down was planned, made or
  uploaded and that every short video that went out is a standalone Short with a record on tab `Release_Sheet`.
  `tools/sweep.py`: `release_of` - every long-video id is judged the same way and is a bad id otherwise; the summary counts
  them (`released_without_cutdowns`). `tools/gen_docs.py`: SYSTEM.md lists the older doors. `tests/paid_calls.py`: the
  counter sees key art and voice jobs; `V12V2CB2C_COUNTED`, `V12V2CB2C_REMOVED` in the baseline.
- Seeds: `v2cb2c.no_cutdown_the_short_is_the_product`, `v2cb2c.related_video_link_is_the_pull`,
  `v2cb2c.more_short_uploads_cost_the_long_videos`, `v2cb2c.one_door_for_short_uploads` (all for D9), and the two lessons of
  V2c-b2b1 that were not in the Palace yet: `v2cb2b.reproduce_the_id_first` (D8), `v2cb2b.never_compare_at_a_cut` (D6); one
  item of V2c-b2b1 that named removed code was corrected (the Palace's own check named it at the first rehearsal). A first try
  filed the upload count as a limit for D9 and pushed an older limit out of its playbook: it is a strategy item now.
- Docs: 3 matrix rows (2 older rows reworded), the ledger, `CONCEPT.md`, 2 dated platform facts, the builders' recipe in
  `CLAUDE.md`, the redesign's end note, `SYSTEM.md` regenerated.
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| A long video makes no cut-down reel | nothing in the code can plan, voice, cover or upload one; `sampler.draw` | tests on what is gone; the paid-call counter (`text:reels` 0, 2 premium pictures, 1 voice job); the rehearsal; the sweep (`release_of`) |
| The long video's release is one step | `manage.tick`, `manage.release`, `manage._give_up_stuck` | tests (one step, the delay, not public, KILL, never twice, a row at LIVE1); the rehearsal; the sweep |
| One door for every upright video | `truth.short_doors`, `truth.door_issues` in `truth.issues` | Plan Guard RED, check `docs_current` FAIL, tests (a planted door by each of three calls; a long upload is none; nested; the list may only shrink) |
| The older tracks are paused by default | `core.DEFAULTS`, `pilots.run`, `specials.run`, `governor.specials_left_inr` | tests (both refuse, nothing uploaded, the earmark is production money; switched on they work) |
| A live Sheet is moved once | `manage.v12v2cb2b_upgrade` at both setup sites | tests (marks, pauses, leaves his own FALSE alone, never twice, his later TRUE stands) |
| No current doc or prompt speaks of the old plan | truth rule `cutdown_reels` | Plan Guard, the tests, check `docs_current` |
| Every estimate counts what is really bought | `governor.premium_images` | tests (two premium pictures fewer; the cost goldens moved by exactly that) |
| A log line can never hang the job | `models.CacheManager.blocks` logs after the lock is released | `tests/test_v811.py` (the warning as the 40th buffered line must return; it hangs on the old code) |
#### Step 6 PROVE
- `tests/test_v12_cutdowns.py`: **50 tests** (26 test functions; the door and the truth rule run on many cases), each rule both ways - nothing of the cut-downs is left (no check, cell, role,
  prompt field, module or lever; 60 checks by stage; the delay cell says what it is now); the draw plans no reel and seeds none,
  while a video an older version made keeps its reels' credit; the lesson of a video's Shorts traffic; the rulebook refuses a
  reel department; the release in ONE step (the tick names it, public -> comment -> LIVE, nothing uploaded, never twice, no
  second release named - not after 7, 27 or 51 hours either); the delay; a private video waits and the owner hears once; KILL;
  a row left at LIVE1 closed by the tick with nothing posted; the CLI and the workflow; the rehearsal and the sweep walk the
  rule; ONE DOOR (the repo has the four listed doors and no other, each shut by a FALSE default; a planted door by `ig_reel`,
  by `fb_reel`, by a bare name, by `yt_upload(short=True)` and by `short=<a variable>` is found; a long upload, `short=False`
  and a thumbnail call are not; a call inside a nested function is found at its outer function; `release.py` and `publish.py`
  are the door's home; a listed door that uploads nothing any more must leave the list; the list cannot grow; a new door fails
  the truth registry and, alone, check `docs_current`; a fixture without the platform calls is not judged); the paused tracks
  (both refuse with their reason, nothing is uploaded, the earmark is production money, switched on it is back); the one-time
  move (marks eight cells and leaves their values, pauses both tracks, leaves a FALSE he typed alone, never twice, his later
  TRUE stands, both setup sites call it); the truth rule on ten sentences of the old plan and nine true ones; the estimate; and
  ONE WHOLE PRODUCTION with the paid-call counter - no `text:reels`, 2 premium pictures, 1 voice job - on which the sweep's own
  verdict passes, is repeatable, and names five planted cut-downs each alone (a reel file, a reel on the release record, a reel
  on the episode's row, a reel strategy in the draw, another kind of short upload).
- With the two older faults: `tests/test_v811.py` (the warning as the 40th buffered line must return inside 20 seconds - it
  hangs on the code before the fix: run once on that code, 1 failed), `tests/test_v12_opening.py` and `tests/test_safety.py` (a
  Short's hook that opens on "Today you ..." is no throat-clearing for the opening rule, the hook lab and the Short's seat
  alike; "today we", "today I", "today's video", "today, let's" still are - ten sentences).
- Tests changed by design (24 older files): the reel tests of the patch that introduced the reels are gone with what they tested
  (`test_v85` 12, `test_v83` 2, `test_v891` 2, `test_v84`, `test_v89`, `test_v93`, `test_v10_growth` 1 each, `test_v12_opening`
  2); counts (`test_v12_exec`: 71 levers, 18 final checks, its lever example; `test_v12_release`: 49 promises about the show;
  `test_tableread`: five roles); the cost goldens moved by exactly two premium pictures (`test_v87`, `test_v89`, `test_v85`);
  the pilot and special-reel tests switch their track on first (`test_v10_future`, `test_v10_growth`); the rest lost one line
  each that named a removed thing. `tests/test_docs_current.py`: the new rule's sample and the little repository's baseline.
- Fails correctly: **63 deliberate one-place breaks** on the real repo (58 seen by the fast tests, 5 only by a whole production),
  each put back by the script (a copy of every file kept; the hashes compared), nothing else reading the code meanwhile, the
  list written before the last test run - **each failed at least one test**: a release that runs twice, ends at LIVE1, ignores
  a private video, posts no comment, ignores KILL, does not wait for its delay; a second release named for a live video; a row
  at LIVE1 never closed; the owner mailed at every try; the draw carrying a reel strategy; an older video's reels losing their
  credit; every lesson speaking of reels; the rulebook taking a reel department; a check, a cell, a role or a prompt field of
  the cut-downs back; the delay cell's note or its lever gone; the estimate counting two reel covers; a Facebook Reel, an
  Instagram Reel or a YouTube Short being no door; every YouTube upload taken for a short one; `short=False` taken for a Short;
  `short=<a variable>` not seen; only a bare call seen; a new door raising nothing; a gone door staying listed; the list
  growing; the ratchet raised; the rule outside the truth registry; the platform calls or Publishing's run taken for doors; a
  fixture judged; one module not searched; the retired cell or the old sentence allowed again; the rule firing on a true
  sentence or on the word "bridge"; a prompt allowed to name the old plan; a wrong baseline; the pilots or the special reels on
  by default; either switch not read; the paused reels keeping their earmark; the move not marking, not pausing, rewriting his
  FALSE, running every time, leaving no mark, or writing "paused" and leaving the switch on; the release job's command unknown;
  the sweep's verdict blind to a reel file, to a reel on the release record, on the episode's row or in the draw, or to another
  kind of short upload; a bad verdict not making the id bad; the warning logged inside the lock again (the test waits its 20
  seconds and fails); "today" a greeting again for every line, or for no line. Two breaks of the list were left out and say why
  (one is only meaningful together with another; one is read by a wiring test that looks at other words of the same line).
- Fake rehearsal on the working tree of the final code: **GREEN three times** - the trial with Shorts in S2 (EP202611121904), F1
  with S1 (EP202611121907), F1 with S3 (EP202611121910): every long format and every Short format. Each: a long video refused
  first (nothing spent), two Shorts made and released on three platforms, their numbers read, one promoted, the long video about
  it opening on its Short's footage - and "cut-downs: none made, none uploaded; short videos out: 2 standalone Shorts through
  the release sheet", the release in one step, no release named a day later; script 36 of 36, final 18 of 18. The first try of
  the trial with S2 (EP202611121845) was the one that found the fault of the opening (above): its long video was held; after
  the fix that id's own gates pass (36 of 36 and 18 of 18); its run then stops at the rehearsal's assertion on the organisation's
  checks, which say "not applicable" for an id from a past minute (open issue 146).
- Parallel pre-check of the whole suite before the final code commit was accepted as final: **1457 passed in 32:44**, no
  failure, no skip. Before it: three parallel runs to list what the batch changed by design (the first and the third stopped
  on the deadlock; the second listed 29 failed tests and 3 files that could not be collected - all older tests that pinned
  reels, the pilot default or counts; the 29 touched files then 804 passed).
- Full suite on a frozen copy of the FINAL code commit 1d3a77a, serial runner: **1457 passed / 0 failed / 0 skipped** (76 test files;
  1416 before this batch: 63 new, 22 gone with the reels they tested). No stall: the two runs that stopped were the deadlock.
- Sweep on the same frozen copy of 1d3a77a, after the suite had finished: **58 of 58 ids** on the first pass. No bad id, no failure
  class. A: 20 ids, organisation on - every id climbed the ladder first, its long video opened on its Short's footage (20 of
  20) and **ALL 20 WERE RELEASED IN ONE STEP WITH NO CUT-DOWN** (`release_of` on every id: no reel file, cover, plan or upload;
  the tick names the release, it ends at LIVE, no second release is named; the only short video on the Sheet is the id's own
  standalone Short): 13 drew F1 (41 pass + 13 not applicable of 54 checks), 7 drew F2 (48 + 6); 11 department runs each. B: 4
  ids, organisation off - 4 ok, each climbed, opened on its footage and was released without a cut-down. C: 4 full rehearsals
  with a fixed id - 2 in F2 (49 pass + 5 not applicable), 2 in F1 (42 + 12), each asserting inside the rehearsal that no
  cut-down was planned, made or uploaded. D (`--mode short`): 20 ids, two Shorts each, both released (the first made while
  uploads were closed and sent later from its Drive copy; 9 of the Shorts under test by the owner's Approve): 6 of 6 checks, 7
  department runs, no warning. E: 10 more ids forced to S3 - 10 of 10, 6 by Approve. The warnings of A to C are the classes the
  offline long video has always printed (the stand-in voices, the atmosphere's time valve - issue 26, the prompt-cache note -
  issue 23, now written outside the lock; in the rehearsal also its own later scenes); none comes from this batch. NOT covered
  by the sweep: the older doors (off), a video that stays private, KILL, a row at LIVE1 (open issue 145).
- GitHub Checks (standing rule 1): run **131** on 1d3a77a **GREEN**: 1457 passed (56:27), rehearsal GREEN (episode EP202611122025;
  contract script 36/36, final 18/18); its one warning and its notices are GitHub's own (Node.js 20, the Ubuntu label - open
  issues 37 and 46). Run 130 (6c09850, build part 2) GREEN too: 1446 passed, rehearsal GREEN (EP202611121929). Run 129 (6b00b68,
  build part 1) RED, read: three test files could not be collected - they imported the reel module that commit deleted
  (corrected in 6c09850; no fault of the code). Run 128 (dfbdc9f, text only) GREEN.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (180 founding items), Organisation GREEN (12 wired, 5 pending), docs regenerated
  without drift.
- Money: Rs 0 spent (fake mode). The batch adds NO paid call and removes seven a long video - the paid-call counter, on one
  fake long video of the accepted code of V2c-b2b1 against one of this code: the cut-downs' planning call 1 -> 0, premium
  pictures 4 -> 2, voice jobs 5 -> 1, every other count identical (`tests/paid_calls.py` `V12V2CB2C_REMOVED`). In rupees, from
  the price cells and not measured on a real bill: two premium pictures Rs 15.84 (USD 0.08 each at Rs 99) - the estimate before
  every video fell by exactly that -, the planning call about Rs 5-8, four short voice jobs about Rs 5: about Rs 27 a long video,
  about Rs 110 a month at four. Paused by default: the special reels (their Rs 300 earmark is production money meanwhile) and
  the pilot Shorts (up to Rs 40 a month). The known gap stays: at today's clip price twelve Shorts a month do NOT fit beside
  four long videos until V2d chooses the clip model by value (open issue 83).
#### Step 7 TAKEAWAY (also Palace item `v2cb2c.takeaway`)
- WORKED: counting what the code would really do before deciding what to keep. The batch's list named the cut-down reels; a
  search for every call that uploads an upright video found three more doors and a total of about 38 short uploads a month -
  past the line the plan itself warns about, with two texts that state a cadence the channel does not have. The decision
  ("none") only means something because the count is true now, and a guard that reads the code keeps it true.
- WORKED: reading the platform's own pages before the design, a fifth time. One sentence of a Help page - only a Short cut with
  Studio's own tool gets the link to its long video - took away the one reason to keep a cut-down made by code.
- WORKED: treating a test run that stops as a finding. Every finished test logged by name, the stuck worker's stack dumped
  while it was stuck: a real deadlock of the older code, named in ten minutes, that would have cost the live channel a video
  about once in forty warnings.
- WORKED: reproducing the red rehearsal's id on the ACCEPTED code before explaining it (the lesson of V2c-b2b1, used at once):
  the hold was the previous batch's, and the cause was a rule that did not recognise what is wrong.
- WORKED: the break list written before the last test run - 63 of 63, and the list found two lines of mine that did nothing.
- FAILED: I pasted a script through the shell again and it lost its backslashes (nothing was applied - a syntax error); I read
  two old rehearsal logs as new ones because my wait matched a line the previous run had left in the same file; and I ran
  other tests and edited files beside the first parallel run, so its stall could not be told from my own noise.
- FAILED (inherited, now closed): three batches of green rehearsals, suites and sweeps had not met a Short whose hook opens
  "Today you ..." - the offline writer has two scripts a format and the fixed ids never promoted that one. A rule that reads a
  viewer's first line needs its test sentences from EVERY format's own brief.
- LIMIT: nothing real has met any of this. The four older doors are shut by a switch, not rebuilt on the release sheet (open
  issue 136). The pull from a Short to its long video is one hand step that no code opens yet (135). No code counts short
  uploads across kinds (138). Twelve Shorts beside four long videos is 75% Shorts by uploads - above the mix at which long
  videos did best in the one large study (redesign O15): only the channel's own numbers can say, and nobody reports them yet.
- NEW QUESTION: does the hand-set link move viewers at all (H24)? YouTube calls it its most effective tool and gives no number.
- ORGANISATION: a decision about "how many" is only as good as the count behind it - count from the code, not from the plan.
  And a department's old track that nobody switched off is still a department's upload: paused is a state that must be SET.

### V2c-b2b1 - THE OPENING (12 Nov 2026) - ACCEPTED (final code commit 22103cb GREEN in GitHub Checks run 126: 1416 passed; sweep 58 of 58 ids)
The owner: "continue in new session" (12 Nov 2026, item 21 of `02`). V2c-b2b was SPLIT AT ITS START (rule 6; the note is at the top of
NEXT): V2c-b2b1 is the long video's opening made of its Short's footage; V2c-b2b2 is the end of the cut-down reels as a product.
The whole binding reading order was read first (handoff `CLAUDE.md`, `00`, `02` with the new item 21, `01`, `03`, `06`, `04`, `05`, all
of the redesign with section 11 first, this file's head, the standing rules, NEXT, the V2c-b2a, V2c-b1 and V2c-a records, every open
issue 1-122, HOW TO RUN, the batch log, the repo's `CLAUDE.md`, all of `docs/CURRENT/`, the three hand-over notes), then the code the
half touches: `episode.py` (the plan stage, the assets stage, the renderer's loop, the finish), `hooks.py`, `org/audience.py`,
`anim.py`, `room.py` (`plan_shots`, `promise_shot`, `opening_units`, `reels`), `ladder.py` (`keep`, `enter`, `gate`, `topic_report`),
`shorts2.py` (`plan`, `make`), `render.py` (`clip_segment`), `checkpoint.py`, `shotplan.pieces_for`, the contract's probes, the
paid-call counter, the rehearsal's ladder walk.

#### Step 1 RESEARCH (E = measured or the platform's own page, O = practice; every page below was read by the build session itself on 12 Nov 2026; the redesign's R1-R47 are the base)
1. E read - YouTube Official Blog, "A design journey from mobile to TV: YouTube Shorts arrive on the big screen", 7 Nov 2022, by its two
   UX directors (https://blog.youtube/news-and-events/youtube-shorts-arrive-on-the-big-screen-design-process/): YouTube tested three
   ways to show an upright video on a wide screen with viewers. The plain player with empty sides: "the joy of Shorts gets lost".
   Several videos side by side ("Jukebox"): it "strayed too far from the essence of Shorts", which "features one video at a time".
   Chosen: one video in the middle on "a color-sampled blurred background" - testers preferred it, it "made better use of the TV
   screen's additional space" and "made the experience feel more modern". Design research with viewers; the page gives no numbers.
2. O read - Google Research, "AutoFlip: An Open Source Framework for Intelligent Video Reframing", 13 Feb 2020
   (https://research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/): a fixed crop "often lead[s] to
   unsatisfactory results"; a crop window is stationary, panning or tracking, chosen per scene; when what matters does not fit the new
   shape the frame is padded - with the ground colour, else with "a blurred version of the original frame". No measured evaluation.
   -> a window AND a blurred ground are one family of answers, and the choice between them is "does what matters fit?".
3. E read - YouTube Help 9314415, "Measure key moments for audience retention" (no date on the page; copyright 2026): "Intro tells you
   what percentage of your audience still watched your video after the first 30 seconds"; a high figure "could mean" that "the content
   in the first 30 seconds matched the viewer's expectation of the video's thumbnail and title"; the advice: "Modify the first 30
   seconds of your video and experiment with different styles". -> the opening is the stretch YouTube itself measures; how it is
   shown is to be experimented with - a setting, not a belief.
4. E read - YouTube Help 1311392, channel monetisation policies (renamed 15 Jul 2025): reused content = repurposing "content that's
   already on YouTube or another online source without adding significant original commentary, substantive modifications, or
   educational or entertainment value"; "If we cannot tell that the content is yours, it may be subject to our reused content
   policy"; allowed: "Same intro and outro for your videos, but the bulk of your content is different". NOTHING on the page speaks of
   a creator's own earlier footage inside a new video. -> twenty seconds of the channel's own Short under a new narration, in a
   nine-minute video, is not what either rule names. A cut-down reel made of those same seconds WOULD be the Short a second time
   (redesign R26: re-uploads get "less distribution") - so the footage shots are kept out of the cut-downs.
5. E read - fal, the hero clip model's page and its API schema (read 12 Nov 2026;
   https://fal.ai/models/fal-ai/kling-video/o3/standard/image-to-video and .../api): inputs are the start picture, an optional end
   picture, the prompt and a duration of 3 to 15 seconds (default 5); there is NO field for the shape or the pixel size of the clip -
   it follows the start picture; USD 0.084 a second. -> the Short's clips are upright because their start pictures are; the same
   scene in 16:9 would be a second paid clip and a new draw (not the footage viewers stayed for). The page does not say how many
   pixels a clip has: code must measure every clip it is handed.
6. E read, small - Loyola University Chicago, "Short-form videos: an exploratory study on the impact of subtitles and ASMR split-screen
   format options ...", MIPRO 2025 (IEEE), 6 Mar 2025 (the abstract, on
   https://imotions.com/blog/publications/short-form-videos-an-exploratory-study-on-the-impact-of-subtitles-and-asmr-split-screen-format-options-using-eyegaze-and-facial-expression-data/):
   a second picture beside the first "significantly impact[s] visual attention patterns", with "elevated positive emotions,
   engagement, and attention" and no significant change in recall. Exploratory; the sample size is not on the page.
7. O read - N. Krawetz, "Kind of Like That", 21 Jan 2013 (https://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html):
   the difference hash - a picture shrunk to 9 x 8 grey pixels, 64 bits, each "whether the left pixel is brighter than the right" -
   "won't change if the image is scaled or the aspect ratio changes" and barely moves with brightness or colour; a distance of 0 to
   10 bits is the same picture or a variation, above 10 "likely a different image"; cropping by about a tenth can defeat it.
   -> a finished film can be compared with the footage it should show, as long as the SAME window of both is compared.
8. O read - OutlierKit, 7 Sep 2026 (https://outlierkit.com/resources/youtube-shorts-to-long-form/): the related-video link "sends a few
   hundred viewers per 100,000 Short views" (the author's estimate, no source); nothing on what a long video's opening should do for
   a viewer who comes from its Short. -> almost everybody who meets the long video's opening has NOT seen the Short; a viewer who
   has is the rare case and must recognise the topic at once.
NOT FOUND, so nothing is built on it: any measurement that compares a cropped window, a blurred ground and a split layout for upright
footage inside a wide video; any study that pairs a Short's opening with the first 30 seconds of a long video on the same topic
(H1 / H11 stay hypotheses the channel's own pairs must answer); the pixel size of the hero model's clips; any study of how far an
AI-made clip may be enlarged before viewers notice. The window's limit and the opening's length are therefore STARTING VALUES and
levers, and what a real upright clip looks like in a wide frame can only be judged at the pilot (V3).
AN EXPERIMENT BEFORE THE DESIGN (read from the code and counted, no run needed): what today's code would do with a Short's clip.
(1) The renderer's clip path already crops every clip to the frame's shape around its centre: handed an upright clip it would show
the middle 31.6% of the picture (a 16:9 window is 9 of 16 of 9 of 16 of the height) and, for a clip 720 pixels wide, enlarge it 2.67
times to fill 1,920 - with nobody measuring it and nothing on record. (2) With micro-cuts on, an animated unit longer than 2.6
seconds inside the opening window is cut into pieces of which only the FIRST is the moving clip; the others are the start picture
with a camera move. Laid under the long video's sentences as they are, most of the Short's paid seconds would never be seen.
(3) `plan_check` and the Animation Director both turn every animated shot beyond the plan's four back into a still: a marked opening
would be undone twice before the script gate. (4) A sound hit and a riser are placed at every animated unit's start: six footage
units in a row would open the video with six booms. (5) The cut-down reels choose their shots from the whole shot list: with the
footage in it, a cut-down could be the Short again. (6) Three upright panels fill a 16:9 frame almost exactly (3 x 9:16 = 27:16).
#### Step 2 CREATIVITY (scores 1-5: what a viewer or the channel gains / enforceable / cost / reliability / owner effort)
A. Replay the Short itself as the cold open (its file, its voice, its burned captions) in a frame: 1 / 4 / 5 / 4 / 5 = 19 - a viewer
   who comes from the Short watches the same 25 seconds again; everybody else gets an upright strip with captions, another voice
   than the video's, and an ending built to loop, not to open a nine-minute story.
B. Pay again: re-make the Short's pictures in 16:9 and animate them: 4 / 3 / 1 / 3 / 5 = 16 - the best picture, but the opening is
   paid a second time (3 to 4 hero clips, about Rs 115-155 a video) and it is a new draw from the model: not the footage real
   viewers stayed for (research 5).
C. The whole upright clip on a blurred ground, always (YouTube's own choice for a wide screen, research 1): 3 / 4 / 5 / 5 / 5 = 22 -
   nothing enlarged, nothing lost; but in the small player of a phone held upright the picture is a third of the width.
D. A centre crop that fills the frame, always (what the renderer does today if handed the clip): 3 / 2 / 5 / 3 / 5 = 18 - a full
   picture, of which two thirds are thrown away and the rest enlarged 2.67 times, unmeasured.
E. (ORIGINAL) The triptych: three upright panels fill 16:9 (experiment 6) - the Short's three beats side by side, each waking up as
   the voice reaches it: 2 / 3 / 5 / 3 / 5 = 18 - every paid pixel is used; but several pictures at once is what YouTube's viewers
   refused (research 1), it divides attention (research 6) and it ends "it happens to YOU, one camera".
F. (ORIGINAL, CHOSEN) THE PROVEN OPENING UNDER THE LONG VIDEO'S OWN VOICE, IN THE WIDEST WINDOW ITS SHARPNESS ALLOWS, PROVEN ON THE
   FINISHED FILM: the Short's picture track - its clips in its order at the speed viewers saw them, without the loop - is laid by
   code under the long video's first sentences; the first spoken line is the Short's own hook, word for word (real viewers
   outrank a jury: no hook lab for it); the upright picture is shown through ONE window with one dial, from the whole clip on a
   blurred ground to a full 16:9 window, and code picks the widest window that enlarges the paid picture by no more than a limit
   (a lever), measured on the clip's real pixels; the Animation Director then buys three scenes, not four. Two checks: before any
   picture money the shot list opens on THIS Short's footage (from this Short's archive, laid as the rule says), and on the
   finished film frames of the master are compared with the footage: 5 / 5 / 5 / 4 / 5 = 24.
#### Step 3 DESIGN MEMO
- WHAT A VIEWER MEETS: a long video about a promoted Short opens on the picture the Short opened on - already moving at second 0 -
  and runs through the Short's clips for as long as they last (about 15 to 25 seconds; at most `OPENING_SHORT_MAX_S`), under the
  long video's own voice. Its first sentence is the Short's hook (`OPENING_HOOK_ON`). Then the long video's own pictures begin.
- THE FOOTAGE (`whatifs/opening.py` NEW, Visual Production D6; on `tools/repair.py` PROTECTED): `fetch` downloads the archive named
  on the Short's ladder row (tab `Ladder`, column footage), unpacks only `c<i>.mp4`, `f<i>.png` and `short.json`, refuses an
  archive whose `short.json` names another Short, and measures every clip (pixels, seconds, SHA-256). The manifest travels with the
  plan (`plan.json`), so a resume proves it holds the same files.
- THE LAYING (`opening.lay`, pure code): the Short's picture track is its plan's shots without the loop shot, each clip slowed
  exactly as the Short played it. Unit i of the long video shows the track from its own start to its own end; the opening ends at
  the last sentence that ends inside the track (or inside `OPENING_SHORT_MAX_S`). A sentence may cross from one clip into the next.
- THE WINDOW (`opening.fit`, pure code; `OPENING_FIT` = auto | fill | whole): a window as wide as the clip and of shape A is cut out
  around `OPENING_WINDOW_Y` of its height and shown at the frame's full height; A runs from the clip's own shape (the whole clip) to
  16:9 (the frame filled). `auto` takes the widest A that enlarges the picture at most `OPENING_ENLARGE_MAX` times (2.0 to start: a
  clip 720 pixels wide gets a 4:3 window over three quarters of the frame's width; a clip 1,080 wide fills the frame at 1.78). What
  the window leaves free is a blurred, darkened copy of the same frame (research 1, 2) - never black bars, never a second picture.
- THE SHOT LIST (`opening.mark`): each covered unit becomes an animated shot that carries its piece of the track (`short`: the Short's
  id and the stretch of each clip); the first one carries the promise. `plan_check`, the Animation Director and the paid repair
  leave marked shots alone; the Director places its scenes at the three later anchors only (3 paid scenes, redesign 11.5 "the
  opening shared with its Short, three peaks").
- THE FILES (`opening.cut`, inside D6's `assets` run): one clip per covered unit, cut from the footage, shown through the window,
  exactly as long as its sentence, at the frame's size - so the renderer plays it as ONE piece (no still tail, no micro-cut) and
  the checkpoint keeps it like any clip. A footage unit that cannot be cut stops the assets stage BEFORE anything is paid (else the
  stage would buy a new clip for it). One sound hit at second 0, not one per unit.
- THE FIRST LINE (`hooks.run_hooks(proven=...)`): for a long video with footage the first spoken line is the first sentence of its
  Short as the Short's voice spoke it; no candidates are written and no judge is asked. A line the advertiser-safety rule refuses
  falls back to the hook lab. Check `hook_lab` passes on it only when the line is this video's Short's and is the first spoken line.
- THE CHECKS (both promises about the show; SHOW_CHECKS 51; 62 hard checks): `opening_footage` at the script gate - the draw's Short
  has a fetched archive, the shot list's first shots are its footage and nothing else, laid as `lay` says; `opening_shown` at the
  final gate - the cut files are the ones made from that archive (hashes) and frames of the finished film match them (difference
  hash of the same window, research 7). A video that opens with other pictures is HELD with the owner's card (Rewrite / Approve
  anyway): that is the rule the plan asked for, and a missing archive is his decision, not the machine's.
- A LONG VIDEO UNDER AN OVERRIDE has no Short and no footage: it opens as before this batch - the hook lab's best of ten lines and
  its own animated promise scene at second 0, four paid scenes (`viewer_promise` and `promise_paid` judge it). Both new checks say
  "not applicable" for it and name the override.
- THE CUT-DOWNS that still exist until V2c-b2b2 never take a footage shot (`room.reels`).
- LEVERS (D6): `OPENING_FIT`, `OPENING_ENLARGE_MAX` (up needs the owner: a softer picture). Switches with safe defaults:
  `OPENING_SHORT_ON` (FALSE = the opening as before this batch; both checks say NA), `OPENING_HOOK_ON`, `OPENING_WINDOW_Y`,
  `OPENING_SHORT_MAX_S`.
- CHANGED FROM THE REDESIGN, with reasons: (1) 4.2 "its first 30-40 seconds ARE the hook" and 11.4 "whose opening IS that Short's
  footage": the PICTURES and the FIRST LINE are the Short's; the rest of the words are the long video's own - a Short is a complete
  looping story (11.4), its last line hands back to its first, so replayed whole it would end where a long video must begin.
  (2) 4.2 "vertical and horizontal cut from the same clips" cannot be one cut: the clip model has no field for the shape
  (research 5) and a 16:9 window keeps a third of an upright clip. The window is a setting, its limit a lever, the pilot judges it.
  (3) The opening lasts as long as the Short's own footage (15 to 25 seconds today), not 30-40.
- HYPOTHESES: H22 a long video that opens on its Short's footage keeps more viewers to second 30 than one that opens on new
  pictures (YouTube's Intro number; the override videos are the comparison). H23 the wider window holds better than the whole clip
  on a blurred ground (the lever's two ends).
- MONEY, said before the build: NOTHING new is paid - the archive is a Drive download, the cut is ffmpeg on the runner. Per long
  video with footage the production pays LESS: one hero clip (USD 0.42, about Rs 39) and its reference start frame (USD 0.067, about
  Rs 6), the hook lab's two text calls (ten lines and their judge; a few rupees, not measured) and the fresh stills of the covered
  opening units (under Rs 1 each): about Rs 45-50 a video, about Rs 190 a month at four. The ESTIMATE before a video still counts
  four clips (it may only err upward); the paid-call counter must show the smaller count before this is claimed as done. The
  cut-downs' paid planning call (`room.reels`) belongs to V2c-b2b2. The known gap stays: at today's clip price twelve Shorts a month
  do not fit beside four long videos (open issue 83, V2d).
- NOT IN V2c-b2b1, on purpose: the cut-down reels (V2c-b2b2); the long video's thumbnail tied to the Short's first picture
  (V2b / V1c: one story across title, thumbnail and first seconds); a 16:9 re-make of the footage (V2d may price it).
- CORRECTED BY THE BUILD (found by the FIRST fake long video that walked the new path; each written here before the edit that fixes it):
  (1) THE MEASURE ON THE FINISHED FILM COULD NOT RECOGNISE ITS OWN FOOTAGE. The difference hash of research 7 said "22 to 26 of 64
  points differ" (limit 12) on frames that visibly show the same picture: in a trial-format video the renderer lays a dark vignette,
  grain, rain and a "REC" stamp over the opening, and a 9 x 8 grey copy of a smooth picture follows the vignette, not the picture.
  A check that holds a finished, paid video must recognise what is wrong, not what is graded. The measure becomes the correlation of
  the DETAIL of both frames (each grey copy minus its own blur, so brightness, vignette and tint drop out), limit set from measured
  pairs - the same footage against other pictures. (2) THE CUT-DOWNS LOST EVERY SHOT: with the opening shots taken out of their
  choice, a cut-down that had chosen them fell under the four shots it needs and none was made (check `shorts` then held the
  video). A cut-down's footage shot is REPLACED by the next free shot of the long video's own pictures, and the footage shots are
  not offered to the planner at all. (3) My parameter `opening` of the assets stage was shadowed by a local of the same name (the
  set of opening units): the first run crashed before anything was paid. Renamed. (4) FOUND BY THE BREAK LIST, before any break
  ran ("what would fail if this line went?"): eight rules had no test - where the window sits on the clip, that a cut clip is
  slowed and moves to its last frame, that a footage shot is never a scene slot (my assertion compared two calls that could not
  differ), that the paid repair leaves the footage alone, that the footage is not offered to the cut-down planner, the sweep's
  own verdict, the record's way through the checkpoint, a retry on another machine. All written first. (5) FOUND BY ONE OF THOSE
  NEW TESTS: A STILL RIGHT AFTER THE OPENING COULD RE-USE A FRAME OF THE FOOTAGE. A shot without a picture of its own shows the
  nearest earlier picture with a camera move; after the opening that picture is the first frame of a footage clip (blurred ground
  and all), and the paid repair, asked to fix such a shot, found the footage picture and (rightly) refused to re-make it. The
  first still after the footage is now always a picture of the video's own (`episode.anchor_shots`), whatever the budget says.
  (6) THE REHEARSAL'S OWN OLDER ASSERTIONS met the new opening twice: "ten hook candidates" (a video on its Short's hook has one
  line and no lab) and "four planned animated shots, one of them the opening hook" (the plan's own opening clip may lie under the
  footage). Both now state what is true for a video about a promoted Short; the lab's ten lines are proven by the production
  under an override. (7) THE FIRST BREAK RUN WAS CUT OFF BY THE TOOL AFTER ABOUT TEN MINUTES, IN THE MIDDLE OF BREAK 44, AND LEFT
  ONE BROKEN LINE IN `whatifs/contract.py` (a kill does not run the script's "put it back"). Found by `git status` before any
  other step; the file was restored from git and its text compared. The break script now keeps a copy of every file before its
  first break, restores from it at every start, and runs in parts that end inside the tool's limit. 41 of the first 43 breaks
  had failed a test; the two that did not were lines that changed nothing (a special case for the whole clip that the general
  line already gives; a file test that the cut's own failure already covers) - both lines are gone.
  (8) **FOUND BY THE SWEEP ON THE FIRST FINAL CODE COMMIT (10afffc), after a green suite of 1414 and three green rehearsals: A
  REACTION EFFECT WAS DRAWN OVER THE FOOTAGE.** Id EP209901140910 (1 of the first 14 long-video ids) was HELD at the final gate:
  "at 5.2 s the finished film does not show the footage of its Short: the two pictures are alike by 0.03". The check was right. A
  reaction moment of the long video's script fell inside the opening, and the renderer drew its effect - a punch-in zoom and a
  comic burst with a pop-up word, one second long - over the Short's picture. The pictures real viewers stayed for, covered by a
  gimmick the Short never had (the owner on the first live video: "the whole video looked a lot gimmicky"). No test and no
  rehearsal had a reaction inside its opening. Fixed at the cause: no code-drawn reaction effect (and none of its sounds) on a
  shot of the footage - the line is still spoken; a test, a whole-production proof with a planted reaction, a deliberate break.
  The final code commit moves: suite, sweep and GitHub are run again on the new one.
  (9) **THAT DIAGNOSIS WAS NOT VERIFIED ON THE ID, AND IT WAS NOT THE ID'S CAUSE.** The second sweep (on 2b78a2d, after a green
  suite of 1415 and GitHub's green run 125) held THE SAME id with the same sentence. I had reasoned from the code ("a reaction
  effect lasts a second and covers the middle of the frame") instead of reproducing the id - against standing rule 2. Reproduced
  now (`tools/sweep.py --one`, folder kept) and measured shot by shot: 11 of 12 comparisons at 0.98, one at 0.03 - in the one
  shot whose sentence crosses from the Short's first clip into its second, at 5.18 s, three hundredths of a second before the
  change of clips at 5.21 s. The film showed the footage; film and clip are a frame or two apart at a cut, so one showed the
  last frame of clip 1 and the other the first of clip 2. A FALSE HOLD BY MY OWN CHECK - the fault this build has paid for three
  times before (a check must recognise what is wrong). The reaction effect over the footage is real all the same (a planted
  reaction made the film differ and the check failed; it stays fixed) - but no sweep id showed it. Fix of the measure: the film is
  compared inside every STRETCH of a clip, every half second, never within 0.2 s of a change of clips, and each film frame may
  match the clip a frame earlier or later. Denser than before (a one-second effect cannot fall between two samples), and blind
  only where two clips meet. A test with a shot that crosses two clips and is sampled across its cut; the id itself re-run alone
  before any sweep. The final code commit moves a second time.

#### Step 4 BUILD (what changed)
- NEW `whatifs/opening.py` (D6; on `tools/repair.py` PROTECTED): `on`, `source`, `none_words`, `manifest`, `fetch`, `proven`, `bounds`,
  `lay`, `mark`, `marked`, `fit`, `cut`, `plan_report` (check `opening_footage`), `detail`, `alike`, `shown_report` (check
  `opening_shown`), `spots` (where the film is compared), `m_cut`.
- `whatifs/episode.py`: the plan stage fetches the footage before the hook, hands the Short's hook to the first line and marks the
  shot list before the cut-downs are planned (the manifest travels in `plan.json`); `produce` fetches and marks again wherever the
  job runs; `plan_check` and the paid repair skip marked shots; `anchor_shots` charges no footage shot to the picture budget and
  makes the first still after the footage a picture of the video's own; `_assets` cuts the opening first (a shot that cannot be
  cut raises before anything is paid) and its record travels with the assets checkpoint; `_render` plays a footage clip as one
  piece and places one sound hit at second 0; `reaction_events` draws no reaction effect over a footage shot; both gates get what
  they judge.
- `whatifs/hooks.py`: `proven_record`, `run_hooks(proven=...)`. `whatifs/anim.py`: `pick_slots(skip=, anchors=)`, `apply` (three
  scenes at the later anchors when the opening is footage; marked shots are never demoted). `whatifs/room.py`: `past_footage`,
  `reels` (the footage is not on offer; a named footage shot is replaced by the next free shot of the video's own pictures).
  `whatifs/contract.py`: `p_opening_footage`, `p_opening_shown`, `p_hook` (the proven line), two rows (62 hard checks: 36 script,
  20 final, 5 short, 1 release).
- `whatifs/core.py`: 6 cells (`OPENING_SHORT_ON`, `OPENING_HOOK_ON`, `OPENING_FIT`, `OPENING_ENLARGE_MAX`, `OPENING_WINDOW_Y`,
  `OPENING_SHORT_MAX_S`). `whatifs/org/registry.py`, `levers.py`: D6 wraps `opening.py`, owns both checks and 2 levers (72 levers).
  `rnd.py`: SHOW_CHECKS 51.
- `tools/rehearsal.py`: the long video of the rehearsal must open on its Short's footage and its hook (both checks PASS, never "not
  applicable"). `tools/sweep.py`: `opening_of` - every id that climbed the ladder must open on its Short's footage or the id is
  bad; the summary counts them (`opened_on_footage`). `tests/paid_calls.py`: `watch` (the counter's patches as a function) and
  `V12V2CB2B_REMOVED` (what the opening no longer pays).
- Seeds: `v2cb2b.opening_is_the_shorts_footage`, `v2cb2b.upright_in_a_wide_frame`, `v2cb2b.the_clip_model_takes_no_shape`,
  `v2cb2b.compare_detail_not_a_tiny_hash`, `v2cb2b.own_footage_once_per_upload` (172 founding items; all addressed to D6 as
  strategy / technique / tool fact - no limit was pushed out of a playbook: the Palace's note is unchanged).
- Docs: 6 matrix rows (one old row reworded), the ledger (the V2c-b2b1 paragraph), `CONCEPT.md`, the builders' recipe "The opening"
  in `CLAUDE.md`, `SYSTEM.md` regenerated.
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| A long video about a promoted Short opens on THAT Short's footage, laid as the rule says | `opening.fetch`, `lay`, `mark` in the plan stage and in `episode.produce` | `opening_footage` at the script gate (held before any picture is paid); the sweep (`opening_of`) |
| The finished film really shows it | `opening.cut` in D6's assets run; the renderer plays each clip whole | `opening_shown` at the final gate (hashes on record; frames of the master against the clips) |
| The window follows the clip's real sharpness; never black bars, never a second picture | `opening.fit` (OPENING_FIT, OPENING_ENLARGE_MAX), `opening._show` | tests on the window's arithmetic and on the pixels of a cut clip |
| Nothing is bought for a footage shot | `opening.cut` raises; `plan_check`, `anim.apply`, the paid repair and `anchor_shots` skip marked shots | tests; the paid-call counter (three scenes, three start frames) |
| The first line is the Short's hook; no lab for it | `opening.proven`, `hooks.proven_record`, `run_hooks(proven=)` | `hook_lab` (this video's Short, still the first spoken line); the counter (no lab call) |
| A cut-down never takes a footage shot | `room.reels`, `room.past_footage` | tests; the production test |
| An override opens on its own pictures and is not judged for footage | `opening.source`, `none_words` | tests; the production under an override (both checks "not applicable", four scenes, the lab) |
| A missing archive is the owner's decision, asked once | `opening.fetch` -> `plan_report`; `contract.p_opening_shown` reads the waiver | the production whose archive was deleted (held, nothing paid, his Approve, not asked again) |

#### Step 6 PROVE
- `tests/test_v12_opening.py`: **21 tests** (19 before the sweep; two came with what it found), each rule both ways - the window's arithmetic (a clip 720 wide: a 4:3 window at 2.0 times;
  the lever narrows and widens it; `fill`, `whole`, an unknown word, a clip wider than the frame); the laying (a sentence across two
  clips, each slowed as the Short played it; the end inside the footage; the ceiling); the marks (the promise on the first shot, a
  number graphic gone, twice = once, the footage gone = the marks gone); check `opening_footage` on eleven wrong cases, one fault
  at a time (no manifest, another Short's manifest, another archive, a first shot of its own, a footage shot planned as a still,
  another Short's mark, other stretches, a covered sentence without footage, one too many, a first sentence longer than the
  footage); an override and the off switch (both checks "not applicable", naming the override); the archive (measured clips, the
  hook without its delivery tag, only its own file names unpacked, another Short's archive, none kept, none in Drive, a clip
  missing); the cut files on real UPRIGHT clips that move (the frame's size, the sentence's length, moving to the last frame, a
  blurred ground beside the window that is neither sharp nor black, the three window modes, the window's place); a restored clip
  kept by hash and parts, cut again when changed; a shot that cannot be cut stops the assets stage before anything is paid; the
  record's way through the checkpoint; the finished film against the footage (graded darker with a vignette: recognised; other
  pictures under one sentence: named with the second; a replaced clip; another Short's record; the owner's waiver not asked twice,
  and not covering a video that does carry the footage); `alike` on a graded copy, another picture and a flat frame; the first line
  (no lab call, inserted first, never said twice, the hook of another Short refused, a line that is no longer first refused, a line
  that is not advertiser-safe -> the lab); three scenes at the later anchors and four without footage; the plan check, the picture
  budget, the first still after the footage, the paid repair; no reaction effect over the footage; the film never compared where
  two clips meet (the looks inside one shot; a film one frame behind its clips still recognised; other pictures still found);
  the cut-downs (the planner's offer, the replacement); the sweep's own verdict; the wiring.
- `tests/test_v12_opening_e2e.py`: **3 tests, 4 whole productions** - (1) a long video about a promoted Short: both checks PASS, the
  first spoken line is the Short's hook, every opening shot plays ONE clip of exactly its sentence's frames, one sound hit for the
  opening, no cut-down takes a footage shot, and the paid-call counter shows 3 hero clips, 3 start frames and no hook lab; then, on
  another Sheet, a long video under an OVERRIDE: both checks "not applicable" naming the override, the lab's line, its own promise
  scene, 4 hero clips, 4 start frames - the difference is exactly `V12V2CB2B_REMOVED` and nothing else got dearer; (2) the archive
  deleted from Drive: HELD at the script gate with `opening_footage` alone, no picture and no clip paid, the owner's card; his
  "Approve anyway" -> the video goes on with four scenes of its own and `opening_shown` says "not applicable: approved" (he is not
  asked twice); (3) the runner dies before the pictures: the retry on another machine resumes from the saved plan, fetches the
  footage again, pays no writing and no hook lab twice, buys three scenes, and both checks PASS.
- Tests changed by design: `test_v12_exec` (72 levers; 36 script and 20 final checks), `test_v12_release` (51 promises about the
  show), `tests/paid_calls.py` (`watch`, the removed calls). The rehearsal's two older assertions (above, corrected by the build 6).
- Fails correctly: **83 deliberate breaks** on the real repo (79 before the sweep, 4 with what it found), each one place, each put
  back by the script (a copy of every file kept; the hashes compared), nothing else reading the code meanwhile - **each failed at
  least one test**: 74 seen by the fast tests and 9 only by a whole production - the switch ignored; an override taken for a Short; another Short's archive accepted; any
  file name unpacked; the loop shot counted as footage; the Short's slowing forgotten (in the track, in the clip's seconds, in the
  cut); the hook with its tag; OPENING_HOOK_ON ignored; the opening past the footage; the ceiling ignored; no promise on the first
  shot; a mark without footage kept; a marked shot not animated; a graphic left under the footage; `opening_footage` blind to no
  manifest, another archive, a first shot of its own, another Short's footage, a still, any laying, a too-long first sentence; the
  window ignoring its limit, `whole` not whole, an unknown word kept, no blurred ground, its place ignored; the cut going on
  without the footage, with a clip the archive never held, always cutting again, trusting a file without its hash, trusting
  another Short's record, a clip longer than its sentence; `opening_shown` blind to a replaced clip, other stretches, never
  comparing, a first shot of its own, another Short's record; the raw picture compared instead of its detail; a flat frame judged;
  either check gone; the waiver not read, or read too widely; `hook_lab` passing another Short's hook or a line that is no longer
  first; the lab run anyway; an unsafe line used; the hook said twice; the Director demoting footage shots, buying the scene at
  second 0 again, taking a footage shot as a slot, losing slot numbers; the plan check demoting; the assets stage not cutting; the
  paid repair re-making a footage picture or clip; the footage eating the picture budget; a still re-using a footage frame; the
  record lost at the checkpoint (saved, restored); a cut-down keeping or being handed a footage shot, the footage on offer; the
  sweep taking "not applicable" for an opening; no owner of the checks; no lever; a softer window needing nobody; the module
  unprotected; the checks unclassified; and by production only: the plan stage not laying or not handing the hook over, a clip cut
  into pieces, a sound hit per shot, either gate without what it judges, no second fetch on another machine, a video without its
  footage going on without the owner; and with the sweep's findings: a reaction effect drawn over the footage (a fast test and a
  whole production with a planted one), the film compared where two clips meet, one look a clip instead of one every half
  second. Three runs of the list found a line that changed nothing each time (a special case of the window, a file test, an
  allowance of a frame earlier or later); all three are gone.
- Fake rehearsal on the working tree of the final code: **GREEN three times** - F1 with Shorts in S1, F2 with S2, F1 with S3: every
  long format and every Short format. Each: a long video refused first (nothing spent), two Shorts made and released, their
  numbers read, one promoted, and the long video about it OPENING ON ITS SHORT'S FOOTAGE ("the first 12.9 to 17.2 s are the footage
  of Short ...: 5 or 6 shots, 10 or 12 frames of the finished film compared with it, the least alike by 0.86 to 0.99"), its first
  line the Short's hook; 56 checks on the long video (F1: 44 pass, 12 not applicable; F2: 51 pass, 5 not applicable).
- Parallel pre-check of the whole suite before the final code commit (the new tool of item 21): 1413 passed, 1 failed in 33:33 -
  the one test that still pinned 49 promises about the show; corrected, then the final code commit.
- THE FINAL CODE COMMIT MOVED TWICE, each time after everything else was green. (a) 10afffc: serial suite on its frozen copy 1414
  passed / 0 failed / 0 skipped, GitHub run 124 GREEN (1414 passed, rehearsal GREEN EP202611120956) - and the SWEEP on the same
  frozen copy gave 57 of 58: long-video id EP209901140910 was held by `opening_shown`. I took it for a reaction effect drawn over
  the footage (a real fault - "corrected by the build" 8 - fixed in 2b78a2d) WITHOUT reproducing the id. (b) 2b78a2d: serial
  suite 1415 / 0 / 0, GitHub run 125 GREEN (1415 passed, rehearsal GREEN EP202611121154) - and the second sweep held THE SAME ID.
  Reproduced alone and measured: a false hold by the new check at a change between two clips ("corrected by the build" 9), fixed
  in 22103cb - the final code commit - where the id passes alone (43 pass, 13 not applicable) before the third sweep began.
  **83 deliberate breaks in all, each failed a test** (74 seen by the fast tests - all 74 run again after the last change of the
  measure, the 41 that touch the check or come after it in the list on the final code itself - and 9 only by a whole production:
  8 on the commit before the sweep's fixes, the planted reaction again on the final code). Three more lines that changed nothing
  were found by breaks no test noticed and are gone. Three rehearsals GREEN on the final code (F1 / S1, F2 / S2, F1 / S3: "25 to
  29 frames of the finished film compared with it, the least alike by 0.75 to 0.97").
- Full suite on a frozen copy of the FINAL code commit 22103cb, serial runner: **1416 passed / 0 failed / 0 skipped** (75 test files;
  1392 before this batch, 24 new). The first acceptance runs with NO skip: with Node.js on the laptop the dashboard test runs here
  too. The whole-production file of this batch needs about 9 of the runner's 15 minutes a file on this laptop when nothing else
  runs (17 minutes beside a sweep: never run them together).
- Sweep on the same frozen copy of 22103cb, after the suite had finished: **58 of 58 ids**. No bad id, no failure class (the third
  pass: 57 of 58 on 10afffc and on 2b78a2d, both times id EP209901140910 - see above; on 22103cb that id was run alone first and
  passed, then the whole sweep). A: 20 ids, organisation on - every id climbed the ladder first (its own Short made a week ago and
  released, its numbers read, the promotion) and **ALL 20 LONG VIDEOS OPENED ON THEIR SHORT'S FOOTAGE** (13.5 to 18.3 seconds; 24
  to 34 frames of each finished film compared with its clips; `opening_footage` and `opening_shown` PASS on every one - "not
  applicable" would have made the id bad): 13 drew F1 (43 pass + 13 not applicable of 56 checks), 7 drew F2 (50 pass + 6 not
  applicable); 11 department runs each. B: 4 ids, organisation off - 4 ok, each climbed and opened on its Short's footage. C: 4
  full rehearsals with a fixed id - 2 in F1 (44 pass + 12 not applicable), 2 in F2 (51 + 5), each asserting the opening and the
  Short's hook inside the rehearsal. D (`--mode short`): 20 ids, two Shorts each, both released (the first made while uploads
  were closed and sent later from its Drive copy; 9 of the Shorts under test by the owner's Approve): 6 of 6 checks, 7 department
  runs, no warning. E: 10 more ids forced to S3 - 10 of 10, 6 by Approve. The warnings of A to C are the classes the offline long
  video has always printed (the stand-in voices, the atmosphere's time valve - issue 26, the prompt-cache note - issue 23; in the
  rehearsal also its own later scenes: "script N% similar to EPTABLE", a reel given up); none comes from the opening. NOT covered
  by the sweep: upright clips, a missing archive, an override, a retry on another machine (open issue 132).
- GitHub Checks (standing rule 1): run **126** on 22103cb **GREEN**: 1416 passed (40:53), rehearsal GREEN (episode EP202611121421;
  contract script 36/36, final 20/20); its one warning and its notices are GitHub's own (Node.js 20, the Ubuntu label - open issues
  37 and 46). Runs 124 (10afffc: 1414 passed) and 125 (2b78a2d: 1415 passed) GREEN too - on commits the sweep then proved wrong:
  a green GitHub rehearsal is ONE id. Runs 121 to 123 RED, all read: 121 (4f57e6b, build part 1) 5 failed -
  three pinned counts and SYSTEM.md not yet regenerated; 122 (9b305c5) and 123 (0b7c0c1) 1 failed each - the test that pinned 49
  promises about the show, corrected in 10afffc. None was a fault of the code. Run 120 (8a608c2, text only) GREEN. GitHub's unit
  tests took 41 to 61 minutes in this batch (41 before): the job's limit is 120.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (173 founding items), Organisation GREEN (12 wired, 5 pending), docs regenerated
  without drift.
- Money: Rs 0 spent (fake mode). The opening adds NO paid call and removes four: the paid-call counter shows, for a long video on
  its Short's footage against one under an override, one hero clip (USD 0.42, about Rs 39), one reference start frame (USD 0.067,
  about Rs 6) and the hook lab's two text calls fewer, and no more stills or living clips (`tests/paid_calls.py`
  `V12V2CB2B_REMOVED`; the older tests' baseline is unchanged - they run with the ladder off). About Rs 45-50 a long video, about
  Rs 190 a month at four. The estimate before a video still counts four clips (open issue 126). The known gap stays: at today's
  clip price twelve Shorts a month do NOT fit beside four long videos until V2d chooses the clip model by value (open issue 83).
#### Step 7 TAKEAWAY (also Palace item `v2cb2b.takeaway`)
- WORKED: one PURE rule (`opening.lay`) and one MARK on the shot list. Everything after it - the gate, the cut, the renderer, the
  proof on the finished film - reads the mark; the script-gate check simply computes the rule again and compares.
- WORKED: the break list written as "what would fail if this line went?" before the last test run - a fourth time. It found eight
  rules without a test before a single break ran, and one of those new tests found a fault of the product (a still after the
  opening re-using a frame of the footage). Two breaks that no test noticed were lines that did nothing: deleted.
- WORKED: the sweep after everything was green - twice. Suite, three rehearsals and GitHub's run were green on two commits whose
  new check held 1 long video in 20 for nothing. Only a pass over many ids could see it; and only REPRODUCING the id showed why.
- WORKED: measuring before choosing a limit. The first measure (a hash of a tiny copy) called the film's own footage different;
  measured pairs - the same footage under a grade, other pictures - showed it at once and set the limit of its replacement.
- FAILED: the sweep's first bad id I explained from the code instead of reproducing it, "fixed" something else (a real fault, but
  not that one), and paid a whole acceptance pass - suite, sweep, GitHub - for the guess. Standing rule 2 says: reproduce the id,
  trace it, fix the cause. And my own check produced a FALSE HOLD: it compared a frame at a change between two clips. The lesson
  of V1b, V2c-a and V2c-b2a a fourth time - a check that can hold a video must recognise what is wrong.
- FAILED: I chose that first measure from an article instead of from pairs. And I ran a long break run as a background command:
  the tool ended it in the middle of a break and left a broken line in a code file - found by `git status`, not by luck. And I
  pasted two scripts through the shell again although the laptop's oldest rule says never (no backslash was lost this time).
- FAILED (the plan's, now known): "a mark on a shot" has seven readers in the long video's code that had to learn to skip it - the
  plan check, the Animation Director, the paid repair, the picture budget, the sound events, the cut-downs, the still that re-uses
  the nearest earlier picture - and an eighth, the reaction effects, found only while chasing the sweep's id. Search for every reader of a type
  before giving that type a new meaning.
- LIMIT: no upright clip of the real model has met the window. Offline clips are wide, so every rehearsal and every sweep id proved
  "the frame filled, nothing enlarged"; the upright cases rest on small test clips. Whether a 4:3 window on a blurred copy of
  itself looks like a proven opening or like a pasted phone clip only the owner's eye and the first retention curves can say
  (open issue 123, H22, H23). The thumbnail is not tied to the Short's first picture yet (124).
- NEW QUESTION: does a long video that opens on its Short's footage keep more viewers to second 30 than one that opens on new
  pictures (H22)? Every video under an override is the comparison; YouTube's Intro number is the measure.
- ORGANISATION: a thing that is "paid already" needs a mark that every department's code respects, and a check that looks at the
  finished product, not at the plan. And an acceptance run that is green is not the last word while a wider run is still owed.
- NOT IN THE PALACE YET: the founding item `v2cb2b.takeaway` was written with the first final code commit, before the sweep's two
  lessons (reproduce the id; never compare at a cut). They are in this record and in NEXT; a seed change is a code change, so the
  next batch that touches the seed file adds them.

### V2c-b2a - THE PLATFORMS (12 Nov 2026) - ACCEPTED (final code commit 3619c81 GREEN in GitHub Checks run 117: 1392 passed; sweep 58 of 58 ids)
The owner: "continue in new session" (12 Nov 2026). V2c-b2 was SPLIT AT ITS START (rule 6): V2c-b2a is how a finished Short reaches
YouTube, Instagram and Facebook and what proves it; V2c-b2b is the long video's opening and the cut-down reels (NEXT is written for it).
WHY THE SPLIT, by dependency: the batch held two machines that share no code. (a) THE SHORT'S SIDE - `publish.py`, `shorts2.run`, the
approve path, the Short's record. (b) THE LONG VIDEO'S SIDE - the hook lab, `audience.shape`, `anim.pick_slots`, the assets stage, the
checkpoint, the render, `room.reels`, `manage.release`, the rehearsal's own asserts and the many older tests that count four cut-down
Shorts. Each half needs the full loop, the 45-minute suite, the sweep and a GitHub run; V2c-b1 alone took two sessions and met the
weekly usage limit. (b) depends on (a): whatever stays of the cut-down reels must go out through the upload path (a) builds.
The whole binding reading order was read first (handoff `CLAUDE.md`, `00`, `02`, `01`, `03`, `06`, `04`, `05`, all of the redesign with
section 11 first, this file's head, the standing rules, NEXT, the V2c-b1 and V2c-a records, every open issue 1-110, HOW TO RUN, the batch
log, the repo's `CLAUDE.md`, all of `docs/CURRENT/`, the two hand-over notes), then the code the half touches: `publish.py`, `shorts2.py`,
`specials.py`, `ladder.py`, `launch.py`, `reels.py`, `manage.release` / `_post_reel`, the contract's short gate, the registry.

#### Step 1 RESEARCH (E = measured or the platform's own page, O = practice; every page below was read by the build session itself on 12 Nov 2026; the redesign's R20-R38 are the base)
1. E read - YouTube Data API, revision history (https://developers.google.com/youtube/v3/revision_history). 3 Nov 2026: `thumbnails.set`
   "now supports custom thumbnails for Shorts after video processing finishes"; the thumbnails resource gained `shortsAspectRatio`.
   2 Nov 2026: uploads from unverified API projects are no longer locked to private; with `status.privacyStatus` omitted the default is
   public. 4 Dec 2025: an upload costs about 100 quota units (was about 1,600). 27 Aug 2026: public views count from the first frame.
2. E read - YouTube Data API, `thumbnails.set` (https://developers.google.com/youtube/v3/docs/thumbnails/set): for a Short "call this
   method only after the video has finished processing" (`processingDetails.processingStatus` = `succeeded`); called earlier "the custom
   thumbnail might not be applied" - and NO error says so. About 50 quota units; 50 MB; a 403 when the channel may not set custom
   thumbnails. -> THE FINDING THAT SHAPES THE DESIGN: today's long-video code calls it right after the upload; for a Short that call can
   be accepted and do nothing. A thumbnail is a row that WAITS for processing and is finished later - a release cannot be one call.
3. E read - YouTube Data API, the `videos` resource (https://developers.google.com/youtube/v3/docs/videos): NO field says whether a video
   is a Short; `status.containsSyntheticMedia` discloses REALISTIC altered or synthetic content; title 100 characters, description 5,000
   bytes, tags 500 characters; `privacyStatus` defaults to public when omitted. -> "it is a Short" can only be proven on our own file.
4. E read - YouTube Help 15424877 (https://support.google.com/youtube/answer/15424877): an upload "with a square or vertical aspect ratio
   up to three minutes in length will be categorized as Shorts" (standard channels, since 15 Oct 2024). The page names no hashtag: "#shorts"
   in a title or a description decides nothing (today's cut-down reels still write it into both).
5. E read - Instagram Platform, IG User Media reference (https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media;
   its newest dated change is 9 Jul 2025): a Reel container takes `cover_url` (a public JPEG; wins over `thumb_offset`), `thumb_offset`
   (milliseconds into the video; default 0 = the first frame), `audio_name` (the audio "can be renamed only once"), `share_to_feed`,
   `is_ai_generated`, `trial_params` = {`graduation_strategy`: `MANUAL` | `SS_PERFORMANCE`}; caption 2,200 characters, 30 hashtags; 3 seconds
   to 15 minutes, 23-60 frames a second, at most 1,920 pixels wide, 9:16 recommended, moov atom at the front of the file.
6. E read - Instagram Platform, content publishing guide (https://developers.facebook.com/docs/instagram-platform/content-publishing):
   trial reels are "only shared to non-followers"; `SS_PERFORMANCE` = "graduated automatically if it performs well"; a container is
   FINISHED / IN_PROGRESS / ERROR / EXPIRED / PUBLISHED; 100 API posts in 24 hours; a published reel reads back `media_type` VIDEO, so
   `media_product_type` (REELS) is the field that proves a Reel.
7. E read - Instagram Platform, IG Media reference (https://developers.facebook.com/docs/instagram-platform/reference/instagram-media):
   readable after publishing: `media_product_type`, `is_ai_generated` ("indicates if the media has an AI label"), `is_shared_to_feed`,
   `thumbnail_url`, `permalink`, `caption`. NOT readable: whether it is a trial reel, the audio name. -> two Instagram rows can only be
   proven as SENT, never as read back; the record must say which is which.
8. E read - Meta, Facebook Reels publishing (https://developers.facebook.com/docs/video-api/guides/reels-publishing; examples at Graph
   v27.0): 3 to 90 seconds, 9:16, at least 540 x 960, 24-60 frames a second; `is_ai_generated` on the finish call (default false); 30 API
   posts in 24 hours; status read back with `fields=status` (`video_status`, `publishing_phase.publish_status`). Error 1363128 = a
   duration outside 3-90 seconds.
9. E read - Instagram, "Rewarding original creators", 30 Apr 2026 (https://creators.instagram.com/blog/rewarding-original-creators-on-instagram):
   adding "only a border, watermark, subtitles, or credit in the caption" to someone else's work is not original; accounts that mostly
   repost are no longer recommended; a rolling 30-day window. The page says NOTHING about a creator's own video posted on several
   platforms and nothing about AI-made video. (Reported by a search, not read: Instagram's statement of Feb 2021 that Reels "visibly
   recycled from other apps" - logos, watermarks - are recommended less; Tubefilter, 10 Feb 2021.)
10. O read - Kubernetes, "Controllers" (https://kubernetes.io/docs/concepts/architecture/controller/): a controller compares the desired
    state with the current state, acts, "and then reports the current state back"; the loop does not end. And HashiCorp's drift tutorial
    (https://developer.hashicorp.com/terraform/tutorials/state/resource-drift): drift = the recorded state "out of sync" with the real
    thing, found by reading the real thing back and comparing; then it is either accepted or overwritten. -> the release sheet is a
    desired state, the platform's own answer is the current state, and a pass that runs every tick closes the gap or names it.
NOT FOUND, so nothing is built on it: any measured effect of Trial Reels, of a Reel's cover, of an audio name or of a Shorts thumbnail on
reach (YouTube's own Shorts lead, 2023: "most thumbnails are never seen" - V2c-a research 8); whether a trial reel that does not graduate
ever shows on the profile; whether `trial_params` and `share_to_feed` may be sent together; a way to read a trial reel's state or an
audio name back; any API field for the link from a Short to its long video (hand-only, V3). Trial Reels, the cover and the audio name
are therefore SWITCHES AND STARTING VALUES from the redesign (11.4), not proven boosters.
AN EXPERIMENT BEFORE THE DESIGN (read from the code, no run needed): what a Short of today's code would carry onto the platforms.
(1) Tags "reality on trial", "what if" - the special reels' tags on a Short that is by rule never a trial. (2) ONE text for YouTube,
Instagram and Facebook; Instagram's copy gets the words "(link in bio)" only when the text happens to contain "Reality Engine channel"
- a Short's text does not. (3) No thumbnail, no cover, no audio name, no trial flag. (4) Nothing is read back for Instagram or Facebook;
for YouTube only privacy and the AI label. (5) FOUND, A FAULT: the first three Shorts wait for the owner's Approve
(`SHORTS_REVIEW_FIRST_N`), and `specials.approve` posts an approved Short through `_publish` WITHOUT the Short's own text - so exactly
the Shorts he approves would go out under the special reels' text: "New trials every Tuesday and Saturday: Reality on Trial ... Take
your seat on the jury: subscribe." A courtroom, a wrong cadence and an ask under a product that has none of them. No test saw it (the
approve tests stub `_publish`). (6) FOUND, A FAULT: a Short that is made while uploads are "not confirmed open" is marked and counted
as made - and its FILE is nowhere: the job ends, the runner's folder is gone, only the footage archive is in Drive. It could never be
posted (open issue 100 said "harmless"; it is a paid Short lost). Both are fixed by this batch's design, not patched.
#### Step 2 CREATIVITY (scores 1-5: what a viewer or the channel gains / enforceable / cost / reliability / owner effort)
A. Patch the old path: give `specials._publish` a text per platform and the missing Instagram fields: 2 / 1 / 5 / 2 / 5 = 15 - still no
   department run, nothing read back, the thumbnail set too early (research 2), and the approve path and the upload hold stay broken.
B. Three uploader functions called one after another from `shorts2.run`, each returning an id: 3 / 2 / 5 / 2 / 5 = 17 - native, but a
   release is treated as one moment. The Shorts thumbnail cannot be set in that moment, an approved or held Short is posted by other
   code than a fresh one, and "posted" stays a word nobody proved.
C. A scheduling service that posts to all three (the usual tool of social teams): 2 / 1 / 2 / 3 / 3 = 11 - a new subscription (refused by
   the budget rule), the owner's logins in a third system, another firm's defaults between us and the platforms, no read-back we control.
D. One "master record" that a model fills per platform (title, caption, hashtags written fresh for each): 3 / 1 / 3 / 2 / 5 = 14 - a paid
   call for text that code can build from what the writers already wrote, and taste in the place where the rule is "no ask, no courtroom".
E. (ORIGINAL, CHOSEN) THE RELEASE SHEET AS DATA, WITH A RECEIPT FOR EVERY ROW: one table says, for every setting of every platform, WHO sets
   it (code at every upload / the owner once / his hand per video / a later batch), WHAT it must be (a pure function of the Short) and HOW
   it is proven (which field of the platform's own answer - or, honestly, "sent only" where the platform shows nothing back). Publishing's
   run sends ONE master file, never altered, natively to each platform; every request body is built by a pure function; then the
   platform is READ BACK and each row gets a receipt: KEPT, FIXED (drift repaired once), DRIFT, SENT (no read-back exists), WAITING (the
   Shorts thumbnail until YouTube has processed the video), REFUSED, SKIPPED (the file does not fit that platform), HAND or LATER. A pass
   on every tick finishes what waits - the thumbnail, a Short the owner approved later, a Short made while uploads were closed - so there
   is ONE path to a platform, whoever starts it. A new gate after the upload (check `release_sheet`) judges the receipts; "made" becomes
   a field of the Short's own record, apart from where its upload stands: 5 / 5 / 5 / 4 / 5 = 24.
#### Step 3 DESIGN MEMO
- THE RELEASE SHEET (`whatifs/release.py` NEW, D9; `SHEET` = rows of data): platform, row, who (`code` / `once` / `hand` / `later`), how it
  is proven (`read` / `sent` / `file`), the batch for what is not built. Rows set BY CODE for a Short - YouTube: title, description (the
  hook, how it was made, at most 3 hashtags, no ask, no courtroom word), tags, category, both languages, not made for kids, the AI
  field, public, "it is a Short" (proven on the file: upright, at most 180 s - no API field exists, research 3), the Shorts thumbnail
  (only after processing, research 2), the caption track, the playlist of its Short format, the master file. Instagram: caption (the
  hook first, at most 5 hashtags, no link), Reel, cover (`cover_url`, else `thumb_offset` on the promise frame), audio name = the series,
  AI flag, Trial Reel (`SS_PERFORMANCE`), the master file. Facebook: description, AI flag, 3 to 90 s, published, the master file.
  HAND and ONCE rows (the link from a Short to its long video; remixing, comments, phone verification) are on the sheet as V3's and are
  never counted as set: the machine cannot read them (redesign 11.7).
- ONE MASTER, THREE NATIVE UPLOADS: the file made by `shorts2.make` is kept in Drive at once (the record's `file`) with its SHA-256
  (`sha`) and its cover (`cover`); every upload - now, after the owner's Approve, or days later when uploads open - sends that file and
  the receipt stores the hash of the bytes really sent. A platform never receives a file fetched from another platform ("never a file
  with another platform's mark" becomes a row that can fail: `file`). A file that does not fit a platform (Facebook: over 90 s) is
  SKIPPED there with the reason, never cut.
- PURE REQUEST BODIES (`publish.yt_body`, `ig_reel_params`, `fb_reel_finish`): the upload functions build their requests through them
  in real and in offline mode, so a test reads every field. Offline, a small stand-in platform keeps what it was sent and answers the
  read-back from it (`publish.yt_read` / `ig_read` / `fb_read`; a test can make it drift, refuse or keep a video in processing).
- THE RUN (`release.short` = D9's run `short_publish`, the one call site): fit -> texts -> YouTube (upload, read back, wait up to
  `SHORT_THUMB_WAIT_S` for processing, thumbnail, captions, playlist) -> Instagram -> Facebook -> receipts on NEW tab `Release_Sheet`
  (one row per Short and platform: native id, state, the hash sent, what was sent, what came back, the receipts). Then D8's NEW run
  `release_gate` judges NEW check `release_sheet` at NEW contract stage "release" (60 hard checks: 35 script, 19 final, 5 short, 1
  release; a promise about the show: SHOW_CHECKS 49). A failed row is a problem memo to D9 (one per class, closed by the next Short
  whose sheet passes); the Short is public by then, so nothing is "held" and the owner is told only what needs his hand.
- THE PASS THAT FINISHES (`release.settle`, every tick, level-triggered): a Short that is made and not yet out goes out when it may
  (uploads open; his Approve given); WAITING rows are finished; DRIFT is repaired ONCE by code where an API allows it (the AI field,
  the thumbnail) and then stands as DRIFT; a platform that failed is tried again at most `RELEASE_TRIES_MAX` times, then it is a
  failed row. A row still WAITING after `RELEASE_SETTLE_H` hours fails the check.
- WHAT COUNTS AS A MADE SHORT (open issues 100, 107): tab `Specials` gets `made` (when the file was finished), `sha`, `cover`. The
  cadence, the last ten, the spent topics and the review count read `made` - never a status text. `shorts2.UPLOAD_HOLD` is gone; a
  one-time move (`manage.v12v2cb2_upgrade`) writes `made` on the rows an older job left. A Short that is made and never goes public
  inside the ladder's window is PASSED there with the reason (before: MADE for ever, its footage kept for ever).
- THE APPROVE PATH: `specials.approve` hands a Short to `release.short` (its own texts, built from its record); the special reels keep
  `_publish`. The review message of a Short is sent with the master's Drive link as before.
- CHANGED FROM THE REDESIGN, with reasons: (1) "the Shorts thumbnail" is set only after processing and is a WAITING row until then
  (research 2). (2) "Trial Reels on" and "the audio named after the series" are sent and can never be read back (research 7): their
  receipt is SENT, and the record says so instead of "verified". (3) "the cover" is the Short's own promise frame, drawn by code from the
  first picture already paid - one image for the YouTube thumbnail and the Instagram cover; Facebook's API takes none. (4) Translated
  titles (redesign 11.7) need a paid model call per Short: a LATER row (V3), not built here.
- LEVERS (D9): `IG_TRIAL_REELS_ON` (off needs nobody; it is a reach experiment), `SHORT_THUMB_ON`. Switches with safe defaults:
  `RELEASE_SHEET_ON` (FALSE = the old single upload without receipts; the check says NA), `IG_AUDIO_NAME`, `SHORT_HASHTAGS`,
  `SHORT_THUMB_WAIT_S`, `RELEASE_TRIES_MAX`, `RELEASE_SETTLE_H`.
- HYPOTHESES: H20 a Trial Reel reaches more non-followers than a normal Reel of the same Short format (Instagram insights; V5 reads
  them). H21 a Short with its own thumbnail gets more views from the channel page and search than one without (Analytics traffic source).
- MONEY, said before the build: NO new paid call. A Short's release costs API quota only - about 100 units for the upload (its own
  bucket), 50 for the thumbnail, 400 for the caption track, about 100 for the playlist, 1 to 3 a read-back: about 650 of the 10,000 a
  day, three times a week; one Meta post each of the 100 and 30 a day allowed. The settle pass reads only Shorts with an open row (1
  unit each). The cover is drawn by code. Drive keeps one master (about 20 MB) per Short. The paid-call counter must stay unchanged.
- NOT IN V2c-b2a, on purpose (V2c-b2b): the long video's opening from the Short's footage; the cut-down reels (`manage._post_reel`
  still uploads them the old way, "#shorts" in title and text included); the long video's own rows of the release sheet (V3).
- CORRECTED BY THE BUILD (found while writing and running, not in the memo above): (1) NO CAPTION TRACK FOR A SHORT. The memo listed
  one (and 400 quota units for it). A Short's captions are burned into the picture, word by word; a caption track on top would show
  every word twice to a viewer who has captions switched on. So the row is not on the sheet and a Short's release costs about 250
  quota units, not 650. (2) THE HAND-OVER IS A RECORD, NOT A STATUS WORD. My first pass read a status prefix ("UPLOAD_WAITING",
  "APPROVED", "POSTED") to decide what Publishing may send - the very fault this batch retires. A Short is handed to Publishing by a
  row on tab `Release_Sheet` (state QUEUED, `release.queue`), written BEFORE the call that uploads; a Short that waits for the owner's
  Approve has no such row and the pass never touches it. (3) A SECOND PASS MUST ONLY READ. As first written, a later pass over a
  platform that was up and still had a waiting row would have posted the Reel a SECOND time on Instagram and Facebook (only the
  YouTube path looked at the id it already had). Found by reading before any test ran; now a record with a platform's id is only read
  back, and three tests count the uploads. (4) A CRASH AFTER "MADE" IS NO CRASHED SHORT: the record is appended the moment the file
  is kept, before the ladder and the hand-over; a failure after that never writes a second row. (5) Tags: the format's name is no
  search tag - a Short's tags are its hashtags' words and "what if".
#### Step 4 BUILD (what changed)
- NEW `whatifs/release.py` (D9; on `tools/repair.py` PROTECTED): `SHEET` (28 rows: 25 set by code, 1 hand, 1 once, 1 later), `on`,
  `rows_of`, `not_ours`, `sha`, `probe`, `fit`, `hashtags`, `texts`, `text_issues`, `want_youtube`, `compare`, `state_of`, `records`,
  `master`, `cover`, `connected`, `queue`, `short` (D9's run `short_publish`), `gate` (D8's run `release_gate`), `report` (check
  `release_sheet`), `approved`, `settle`, the per-platform senders and the gate's memo hooks.
- `whatifs/publish.py`: `yt_body`, `ig_reel_params`, `fb_reel_finish` (pure; the uploads send exactly what they return), `yt_read`,
  `ig_read`, `fb_read` (the read-backs), the offline stand-in platform (`FAKE_FAULTS`, `_fake_put`, `_fake_get`); `ig_reel` takes
  `thumb_offset_ms`, `audio_name`, `trial`, `ref`; `fb_reel` takes `ref`. An older caller sends byte for byte what it sent before (a test).
- `whatifs/shorts2.py`: `_made` (the field), `cover`, `_keep_master`, `_hand_over`; `run` puts the Short on record the moment its file
  is kept. Gone: `UPLOAD_HOLD` and the text match. `whatifs/specials.py`: `approve` hands a Short to Publishing (and even with the
  release sheet switched off an approved Short now goes out under its own words). `whatifs/ladder.py`: `went_public`; a Short that is
  made and never public is PASSED with the window. `whatifs/manage.py`: the tick calls `release.settle`; `v12v2cb2_upgrade` at both
  setup sites. `whatifs/contract.py`: `p_release_sheet`, stage "release" (60 hard checks: 35 script, 19 final, 5 short, 1 release).
- `whatifs/core.py`: tab `Release_Sheet` (84 tabs); 3 columns on `Specials` (made, sha, cover); 9 cells (`RELEASE_SHEET_ON`,
  `IG_TRIAL_REELS_ON`, `IG_AUDIO_NAME`, `SHORT_THUMB_ON`, `SHORT_THUMB_WAIT_S`, `SHORT_HASHTAGS`, `RELEASE_TRIES_MAX`,
  `RELEASE_SETTLE_H`, `V12V2CB2_MOVE_DONE`). `whatifs/org/registry.py`, `levers.py`: D9 wraps `release.py`, entries D9 `short_publish`
  and D8 `release_gate`, the runs before the release gate, the check's owner D9, 2 levers of D9 (70 levers). `rnd.py`: SHOW_CHECKS 49.
- `tools/rehearsal.py`: each Short of the rehearsal is released and asserted (three platforms, the master's hash on each, every row a
  good receipt, 7 department runs). `tools/sweep.py` (`--mode short`): the Shorts are RELEASED now - before, the sweep made them with
  `publish=False`, so the one proof that starts from an empty Sheet never met any upload path of a Short. The first Short of every id
  is made while uploads are closed, must be made-and-waiting, loses its local file and must go out from the Drive copy when the check
  passes; the Short under test goes out at once, and on every second id by the owner's Approve. `tools/gen_docs.py`: the release gate
  is counted.
- Seeds: `v2cb2.release_sheet_with_receipts`, `v2cb2.shorts_thumbnail_after_processing`, `v2cb2.a_short_is_proven_on_our_file`,
  `v2cb2.instagram_trial_and_audio_are_sent_only`, `v2cb2.facebook_reel_limits`, `v2cb2.one_master_own_words`,
  `v2cb2.made_is_a_field` (166 founding items; all addressed to D9 - a first try addressed two limits to D9 and D12 and pushed older
  limits out of their playbooks: narrowed, as HOW TO RUN says).
- Docs: 5 matrix rows, the ledger (the V2c-b2a paragraph), `CONCEPT.md` (a section on the platforms), 4 dated platform facts, the
  builders' recipe "The platforms" in `CLAUDE.md`, `SYSTEM.md` regenerated.
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| One master, three native uploads; only the master is ever sent | `shorts2._keep_master`, `release.master`, `release._one` | `release_sheet` (rows `file`, a platform that never went up); tests (a changed Drive copy is refused before any upload) |
| Every row code sets has a receipt from the platform's own answer | `publish.yt_body` / `ig_reel_params` / `fb_reel_finish`, `yt_read` / `ig_read` / `fb_read`, `release.compare` | `release_sheet` (DRIFT, REFUSED, WAITING, a missing receipt) |
| A row the platform shows nothing back for is SENT, never "kept"; a hand-only row is never counted | `release.SHEET` (proof `sent`; who `hand` / `once` / `later`), `release.not_ours` | tests on the sheet and on the evidence text |
| Each platform its own words; no ask, courtroom word or link | `release.texts`, `release.text_issues` in `compare` | `release_sheet` (a bad text is DRIFT even when kept); tests |
| The thumbnail only after processing; what waits is finished by the tick | `release._extras_youtube`, `release.settle` in `manage.tick` | tests (no call while processing; set after; REFUSED after `RELEASE_SETTLE_H`) |
| One path: fresh, approved, late | `shorts2._hand_over`, `specials.approve` -> `release.approved`, `release.settle` -> `release.short` | tests; `python -m whatifs.org.runner` RED when the call site is gone; the sweep (all three ways) |
| Nothing is posted twice | a record with a native id is only read back | three tests count the uploads |
| MADE is a field | `shorts2._made`, `_keep_master`, `manage.v12v2cb2_upgrade` | tests (any status with the field counts; none without it) |
| The file fits the platform or is not sent there | `release.fit` | tests (95 s: not to Facebook; 200 s: not to YouTube and the check fails) |
#### Step 6 PROVE
- FOUND BY THE BREAK LIST, BEFORE ANY BREAK RAN (the list is written as "what would fail if this line went?"): (1) THE CHECK COULD PASS A
  SHORT THAT NEVER REACHED YOUTUBE. `release.report` excused every platform whose record said "not connected" - YouTube too - and its
  test passed for another reason (an Instagram row I had left WAITING a line earlier made the check fail anyway). YouTube is the
  product: a record that is OFF, QUEUED, RETRY, FAILED or SKIPPED there now fails the check ("never went up"), and the test tries each
  of the five after proving that the same state on Instagram IS excused. (2) Three tests were missing and were written first: a repair
  that YouTube accepts and does not apply (the receipt must stay DRIFT: a repair counts only when the platform shows it); every sender
  called again with a record that already carries the platform's id (no upload - the guard tried with the case built to defeat it);
  and the tick's hook proven by running the REAL tick job (an approved Short that waits while uploads are closed, then goes out).
- `tests/test_v12_release.py`: **34 tests** (32 at first; 2 came with the two fixes below), each rule both ways - the sheet as data (who, proof, the three rows that are not the
  machine's); the three request bodies field by field, and an older caller's request unchanged; where a file fits (every limit at its
  edge); the words per platform and the four things recognised as wrong (ordinary sentences are not); the receipts (kept, drift, sent;
  a bad text is drift even when kept); the REAL production (three native ids, the master's hash on each, every row a good receipt,
  7 department runs, the gate's evidence, the ladder's clock; a second pass uploads nothing and pays nothing); the cover; a dropped AI
  field repaired once, a repair that is refused, a repair that does not hold, the memo to Publishing and its closing by the next clean
  Short; other words shown than sent; an upload that comes back private (the lock trips); the thumbnail waiting for processing, the
  pass asking without starting a run, finishing once, judging once; a thumbnail never settable or refused; made while uploads are
  closed - made, counted, waiting, sent later from the Drive copy; a changed Drive copy refused before any platform; a platform that
  fails - tried again, bounded, nothing twice; a failed YouTube upload leaves the Short made and waiting; the owner's Approve through
  the same run under the Short's own words; the off switch; 95 and 200 seconds; Meta not connected; the two Instagram switches; the
  cover link that cannot be opened; MADE as a field against every status text; a failure after "made" never a second row; the
  one-time move; never public -> PASSED with the window; the check itself; the wiring.
- Tests changed by design: `test_v12_ladder` (its two fixtures write `made`; the test of the upload-hold TEXT is gone - its rule is
  proven by the field's test in the new file: 32 tests there), `test_v102` (the stage "release"), `test_v12_exec` (70 levers, 1 check
  at the release gate), `test_v12_org` (the registry honesty test's little tree gets `release.py`).
- Run on the working tree so far: the 8 Shorts / ladder / upload files 158 passed; the 7 docs / matrix / Palace / research / engine /
  organisation files 331 passed; the rehearsal GREEN once (F1, Shorts in S1: "release sheet 1 / 1 on 3 platforms; 7 department runs",
  script 35 of 35, final 19 of 19); three sweep ids of Shorts from an empty Sheet 3 of 3 (6 of 6 checks, 7 runs each).
- Fails correctly: **63 deliberate breaks** on the real repo (61 at first; 2 more with the two fixes below, and all 63 run again on the final code), each one line, each put back by the script that made it (the files'
  hashes compared before and after), nothing else reading the code meanwhile - **each failed at least one test**: a file that is not
  the master sent anyway; the thumbnail set without waiting; a second pass uploading again (YouTube, Instagram, Facebook - three
  breaks); a text with an ask not judged; a field the platform does not show counted as kept; a waiting row, a row without a
  receipt, "not connected" on YouTube and a Short that never went up each passing the check; Facebook taking any length; a landscape
  file or any length going to YouTube as a Short; the fit ignored; one text for two platforms; an ask or a courtroom word not
  recognised; any number of hashtags; a bad row not making the record flawed; the cover switch ignored; a dropped AI field not
  repaired; a repair believed without reading it back; a private upload not tripping the lock; the Trial Reel never sent, and not
  switchable off; a platform that is not connected tried anyway; a failing platform tried for ever; the hand-over record not written
  by the run; closed uploads ignored; the ladder not told; the gate not marking what it judged; the gate never run; the Approve not
  starting the release; the pass sending while uploads are closed; a row waiting for ever; a department run every tick while YouTube
  processes; the pass switched off; the offline platform keeping another request than the upload builds; a scheduled upload not
  private; a Trial Reel also shared to the feed; a frame winning over the cover image; an older caller's Reel getting a new id;
  Facebook's AI label ignoring its switch; "made" read out of the status text again; the record not saying when; the master not
  kept in Drive; the Short not handed over before the upload call; a failure after "made" writing a second row; the off switch
  ignored; the first Shorts no longer waiting for the owner; the cover not a JPEG; an approved Short going the special reels' way;
  the old path posting under the special reels' text; a Short never public staying on the ladder; going public twice; the tick no
  longer finishing releases; the one-time move running every time, and marking refused Shorts as made; the check unable to fail;
  Publishing's run missing from the registry; the id YouTube returns not recorded at once; a Reel refused with its cover image not
  tried on the promise frame. No break went uncaught this time - because the list, written first, had already shown one fault and
  three missing tests (above).
- Fake rehearsal on the working tree of 8975c63: **GREEN three times** - F1 with Shorts in S1 (EP202611120258), F2 with S2
  (EP202611120301), F1 with S3 (EP202611120304). Each: a long video refused first, two Shorts made, each released on three platforms
  ("short gate 5 / 5; release sheet 1 / 1 on 3 platforms; 7 department runs"), numbers read, one promoted, script 35 of 35, final 19 of 19.
- FOUND BY RE-READING THE UPLOAD PATH AFTER THE BREAKS (written here before the edits that fix them): (1) A JOB CUT OFF RIGHT AFTER
  AN UPLOAD WOULD UPLOAD AGAIN. The id a platform returns was written to the record only after the read-back, the thumbnail wait (up
  to three minutes) and the playlist. A job killed in that stretch leaves a record without the id, and the next tick's pass would
  post the same Short a second time (YouTube's own Shorts lead: deleting and re-posting risks a spam flag - R24). The id must be on
  record the moment the platform returns it. (2) INSTAGRAM MUST FETCH THE COVER FROM A LINK, AND A LINK CAN FAIL ON META'S SIDE. The
  fallback to the promise frame ran only when OUR side could not open the link; when Meta cannot fetch it (Drive has answered Meta's
  fetcher with a web page before - the reason the video itself is sent as bytes since v8.9.1) the Reel fails three times and never
  goes up, for the sake of a cover. A failed Reel with a cover image must be tried once without it, on the promise frame.
  BOTH FIXED AND PROVEN: (1) each sender writes the platform's id onto the record the moment the platform returns it, before
  anything else; a test cuts the job off right after the upload (the read-back raises) and counts ONE upload after the next pass.
  (2) a Reel that Instagram refuses with its cover image is sent once more on the promise frame inside the same try; a test makes the
  stand-in platform refuse every Reel that carries a cover link and finds the Reel up, its cover receipt saying "promise frame".
  `tests/test_v12_release.py`: 34 passed. All 63 breaks run again on this code: 63 of 63 failed a test, every file restored.
- Fake rehearsal on a frozen copy of the FINAL code commit 3619c81: **GREEN three times** - F1 with Shorts in S1 (EP202611120325), F2
  with S2 (EP202611120327), F1 with S3 (EP202611120331): every long format and every Short format. Each: a long video refused first
  (nothing spent), two Shorts made and RELEASED ("short gate 5 / 5; release sheet 1 / 1 on 3 platforms; 7 department runs"), their
  numbers read, one promoted by the rule, the long video about it (script 35 of 35, final 19 of 19).
- Full suite on the same frozen copy of 3619c81: **1391 passed / 0 failed / 1 skipped** (73 test files; the skip is the dashboard test
  that needs node - GitHub runs it). 1358 before, 34 new, 1 gone by design.
- GitHub Checks (standing rule 1): run **117** on 3619c81 **GREEN**: 1392 passed (41:06), rehearsal GREEN (episode EP202611120406;
  contract script 35/35, final 19/19); its one warning and its notices are GitHub's own (Node.js 20, the Ubuntu label - open issues
  37 and 46). Runs 113 (e31b526), 114 (2e65fc4), 115 (7e416b8, the first commit with the new path) and 116 (8975c63) GREEN too:
  no run of this batch was red.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (167 founding items), Organisation GREEN (12 wired, 5 pending), docs regenerated
  without drift.
- Money: Rs 0 spent (fake mode). The release adds NO paid call: `tests/paid_calls.py` is unchanged and green in the suite, and the
  production test counts none (no text call, no picture, no clip) and no new Cost_Log row on a second pass. In production a Short's
  release is API quota only: about 100 units for the upload (its own bucket), 50 for the thumbnail, about 100 for the playlist, 1 to
  3 a read-back - about 250 of the 10,000 a day, three times a week - and one post each of Meta's 100 (Instagram) and 30 (Facebook)
  a day. The estimate of a Short itself is unchanged (about Rs 290 at today's clip price, open issue 83): twelve a month still do
  NOT fit beside four long videos until V2d chooses the clip model by value.
- Sweep on the same frozen copy of 3619c81, after the suite had finished: **58 of 58 ids**. No bad id, no failure class. A: 20 ids,
  organisation on - every id climbed the ladder first (its own Short made a week ago and RELEASED through the new path, its numbers
  read, the promotion) and its long video was scheduled: 13 drew F1 (41 pass + 13 not applicable of 54 checks), 7 drew F2 (48 pass +
  6 not applicable) - the split and the counts of V2c-b1, so the long video is untouched; 11 department runs each. B: 4 ids,
  organisation off - 4 ok, each climbed. C: 4 full rehearsals with a fixed id - 2 in F1, 2 in F2. D (`--mode short`): 20 ids, two
  Shorts each, BOTH RELEASED - the first made while uploads were closed (made, counted, waiting; its local file deleted; sent from
  its Drive copy when the check passed), the Short under test at once, on 9 of the 20 ids by the owner's Approve; the Short under test:
  11 in S1, 9 in S2, every one 6 of 6 checks (5 at the short gate, 1 at the release gate), 7 department runs, three platforms DONE,
  no memo left open, no warning. E: 10 more ids forced to S3 - 10 of 10, 6 of them by Approve. The warnings of A to C are the classes
  the offline long video has always printed (the stand-in voices, the atmosphere's time valve - issue 26, the prompt-cache note -
  issue 23, the offline writers' retention fix, the script length; in the rehearsal also its own later scenes: the table-read room
  "script N% similar to EPTABLE", a reel given up, a repaired show plan); none comes from the release. NOT covered by the sweep: a
  platform that fails, drift, a refused thumbnail, a file that does not fit (open issue 121).
#### Step 7 TAKEAWAY (also Palace item `v2cb2.takeaway`)
- WORKED: reading the platform's own page before the design, a third time. One sentence of YouTube's thumbnail reference ("only after
  the video has finished processing ... might not be applied") turned "set the thumbnail at upload" into a row that waits and a
  pass that finishes - built as planned it would have been a call that is accepted and does nothing, and nobody would have known.
  One table of Instagram's media reference turned "verified by reading back" into two honest words: KEPT and SENT.
- WORKED: the break list written as "what would fail if this line went?" BEFORE the breaks ran. It found a check that could pass a
  Short which never reached YouTube, whose test was green for another reason, and three guards without a test. Then 63 of 63.
- WORKED: reading my own upload path once more after everything was green. Two faults no test could have shown, because no test
  cuts a job off in the middle or lets Meta fail to fetch a link: a second upload after a cut-off, a Reel lost for its cover.
- FAILED: my first pass decided what to send from a status prefix - the fault this batch exists to retire - and my first senders
  would have posted a Reel twice on a second pass. Both were caught by reading before a test ran; neither should have been written.
  And a scratch script pasted through the shell lost its backslashes again (the laptop's oldest pitfall): the break run died on a
  syntax error, luckily before touching a file.
- FAILED (inherited, now closed): the sweep - the one proof that starts from an empty Sheet - had made its Shorts with `publish=False`
  since V2c-a. It never met an upload. A proof that does not walk the new path proves the old one.
- LIMIT: no real platform has answered. Every "kept" in this record was said by an offline stand-in that returns what it was sent;
  whether YouTube, Instagram and Facebook take these exact requests (a Trial Reel on a resumable upload, the audio name, the
  thumbnail after processing, the fields of the read-backs) is known from their pages only. The first three real Shorts of the
  pilot are the first evidence: read tab `Release_Sheet` row by row. Trial Reels, the cover and the audio name are switches from the
  redesign with no measured effect behind them (H20, H21).
- NEW QUESTION: does a Trial Reel help or hurt an account with almost no followers (a profile that stays empty until a Reel
  graduates)? Instagram's insights can answer after the first twelve Shorts; `IG_TRIAL_REELS_ON` is Publishing's lever.
- ORGANISATION: what a thing IS belongs in a field, where it stands belongs in its status, and a hand-over between two departments
  is a record. And a department that says "posted" must show the platform's own answer: a receipt per row, or the word SENT.

### V2c-b1 - THE LADDER (12 Nov 2026) - ACCEPTED (final code commit 3ab0e16 GREEN in GitHub Checks run 110: 1359 passed; sweep 58 of 58 ids)
The owner: "continue" (a new session for V2c-b). V2c-b was SPLIT AT ITS START (rule 6; the note is at the top of NEXT): V2c-b1 is the ladder -
the cadence, Shorts first with the promote rule and the refusal, the winner's follow-up; V2c-b2 is the platforms and the opening.
The whole binding reading order was read first (handoff `CLAUDE.md`, `00`, `02`, `01`, `03`, `06`, `04`, `05`, all of the redesign with
section 11 first, this file's head, NEXT, the V2c-a record, every open issue, HOW TO RUN, the repo's `CLAUDE.md`, all of `docs/CURRENT/`),
then the code the batch touches.

#### Step 1 RESEARCH (E = measured, O = practice / vendor; every page below was read by the build session itself; the redesign's R20-R38 are the base)
1. E read - YouTube Analytics API, "Data Model", section "Data freshness and latency" (added 9 Sep 2026 per the API's revision history;
   https://developers.google.com/youtube/analytics/data_model#data-freshness-and-latency): "the underlying analytics data is not real-time";
   "Data processing typically introduces a latency of 48 to 72 hours"; the end date "only includes data up until the last day for which all
   requested metrics are fully processed"; for real-time statistics of single videos it points to the Data API's `videos.list`.
   -> THE FINDING THAT SHAPES THE DESIGN: "after 48-72 hours the brain reads the Short's real numbers" (redesign 11.4) cannot be done as
   written. The true numbers of a Short's first 48-72 hours (engaged views, share watched, subscribers) exist 2-3 days LATER, when the Short
   is about 5 days old; only public views are real-time. Today's code reads Analytics once at 48 hours of age and then not again for a week,
   so its first reading covers whatever happened to be processed - a different stretch for every Short.
2. E read - YouTube Analytics API, metrics reference and revision history (https://developers.google.com/youtube/analytics/metrics,
   .../revision_history; entries of 26 Mar 2025, 24 Apr 2025, 27 Aug 2026): since 30 Apr 2025 a Short's `views` count every start and
   replay, `engagedViews` keeps the old meaning and "is available alongside views in all reports"; `shares`, `subscribersGained`,
   `averageViewPercentage` exist. There is NO metric for "stayed to watch" or "viewed against swiped away": that number lives only in
   Studio. -> engaged views divided by views is a proxy that a Short built to loop depresses (a replay is a view, never an engaged view),
   so it is recorded and never ranked on.
3. E read - YouTube Analytics API, channel reports (https://developers.google.com/youtube/analytics/channel_reports): the day-by-day report
   takes `engagedViews`, `shares`, `subscribersGained`, `likes`, `comments`, `averageViewPercentage` with ONE video as a filter. -> one
   call a Short gives its numbers per processed day, so code knows how many days a reading really covers.
4. E read - OverseerOS, 29 Oct 2026 (https://www.overseeros.com/blog/youtube-shorts-views-after-7-days; 4,340 short videos of 823
   channels, a matched group of 160): views at day 7 are 80.7% of day 30 at the median (quartiles 56.3% and 91.7%); 21.3% at least doubled
   after day 7 and 3.1% grew five times; the larger a Short is at day 7 the more it still grows (above 100,000 views: 63.6%). The authors:
   not a random sample, over-represents high performers. -> most of a Short is in early, but one in five is a late bloomer: the ladder
   keeps reading for 30 days and a late bloomer can still be promoted.
5. E read - Metricool, 29 Jul 2026 (https://metricool.com/youtube-trends/; 799,718 videos, 71,177 accounts): "A video usually hits its
   peak in the first three days"; about 83% of interactions arrive within ten days; a Short does best per post at 2 to 4 a week; channels
   with about 5 Shorts a month average 8,789 views per long video against 4,364 with none, and at 35 and more the gain is gone. -> 3 a
   week stays inside the measured band; a follow-up of a winner must land inside its first days.
6. E read - E. Miller, "How Not To Sort By Average Rating", 6 Feb 2009 (https://www.evanmiller.org/how-not-to-sort-by-average-rating.html):
   a raw share ranks an item with 2 of 2 above one with 100 of 101; rank by the LOWER bound of the Wilson score interval (95%). -> the
   two rates of the promote rule (subscribers and shares per engaged view) are ranked by that lower bound, so a Short with 40 viewers and
   one subscriber cannot beat one with 2,000 and thirty.
7. O read - OverseerOS, 16 Aug 2026 (https://www.overseeros.com/blog/youtube-shorts-vs-long-form; 938 breakouts of 137 channels): a
   breakout is 5 times the channel's OWN baseline per format, and in the first 30 days the baseline is a velocity; the study states no
   minimum number of uploads and says it cannot estimate how likely a breakout is. Confirms the redesign's R17 (a channel-relative
   measure at the same age); the multiple and the minimum history stay levers.
8. E read, weak - Socialinsider, 27 Jan 2026, updated 6 Nov 2026 (https://www.socialinsider.io/blog/how-long-does-it-take-for-yt-shorts-to-get-views/;
   Shorts of brand accounts): "Some Shorts get their biggest spike nearly a month after they go live". The page's own sample figures do not
   add up (two different totals), so only that late spikes exist is taken from it.
NOT FOUND, so nothing is built on it: any study that pairs one topic as a Short and as a long video (whether a Short's numbers predict
its long video - H11 - stays a hypothesis the channel's own pairs must answer); any measured effect of a follow-up Short or of how fast it
comes; any official YouTube advice on following up a hit; when the first processed day of a new upload appears in the API. The promote
rule's four measures, the 3-times line and the 48-hour clock are therefore STARTING VALUES and levers.
#### Step 2 CREATIVITY (scores 1-5: breakout odds / enforceable / cost / reliability / owner effort)
A. The calendar ladder (the redesign as first written): at the end of a month rank its twelve Shorts, the top four get next month's long
   videos: 2 / 4 / 5 / 2 / 5 = 18 - a topic waits up to six weeks, the first month has no long video, and it ignores that the numbers come late.
B. A fixed bar: a Short is promoted when it passes a line (say 70% stayed, 1,000 engaged views): 2 / 4 / 5 / 2 / 4 = 17 - nobody knows
   where the line is for a channel of 4 subscribers (the vendor benchmarks disagree), so either nothing passes or everything does.
C. A strong model reads the numbers and the scripts and picks: 2 / 1 / 4 / 2 / 5 = 14 - taste as a gate; not reproducible (R9).
D. A bandit over topics (sampling with exploration): 3 / 3 / 5 / 2 / 5 = 18 - every topic is observed once; with twelve single
   observations a bandit adds nothing to a ranking, and the exploration already exists: every topic gets its Short.
E. (ORIGINAL, CHOSEN) THE ROLLING LADDER ON TWO CLOCKS: YouTube gives two kinds of numbers, so the ladder runs two rules. The FAST clock
   (public views, real-time) finds a WINNER at the 24-hour and the 48-hour mark against the channel's own median at the same mark and
   orders its follow-up with a 48-hour clock - decided by code, the owner is told and can stop it with one tap. The SLOW clock (engaged
   views, share watched, subscribers, shares - 48 to 72 hours late) feeds the PROMOTE rule: when a long video is about to start, it takes
   the best Short of the last 30 days that no long video has used, from the best kind of evidence there is (a declared winner, else true
   numbers over the same first three days, else public views at the 48-hour mark). No candidate = no long video, before any money; the
   owner gets one message with the button that overrides, and an override is a row on the record. A check at the script gate proves the
   topic's origin again, so no other path can start a long video around the ladder: 4 / 5 / 5 / 4 / 4 = 22.
#### Step 3 DESIGN MEMO
- THE CADENCE (D14; `whatifs/shorts2.py` `due`): cells `SHORTS_PER_WEEK` 3 and `SHORTS_PER_MONTH` 12, both levers of D14 (more =
  the owner's tap: it costs money). A Short of the cadence is due when fewer than `SHORTS_PER_WEEK` were made in the last 7 days, fewer
  than `SHORTS_PER_MONTH` this calendar month, and the last one is at least 24 x floor(7 / per week) hours old (3 a week = 48 hours:
  Monday, Wednesday, Friday at one hour of day; R24 - the hour is not a factor). A follow-up of a winner is due at once, outside the
  cadence, inside the ceiling `SHORTS_WEEKLY_CAP`. A Short of the cadence is CORE production now (it only leaves the long slots' money
  alone); a follow-up is paid from the breakout fund or the reserve. `SHORTS_PER_DAY`, `SHORTS_KLING_EVERY` and
  `REPLAN_MAX_SHORTS_PER_DAY` leave the code together with everything that read them: the fractional daily target, the re-planner's rung 3
  (every Short is animated in every second, so "a new animated shot every N Shorts" means nothing), the dashboard's daily switch, D9's
  lever. The re-planner keeps ONE rung: one more Short a week up to `REPLAN_MAX_SHORTS_PER_WEEK` (4, the top of the measured band), at
  the real estimate of a Short. A live Sheet is moved once (`manage.v12v2cb_upgrade`): the three dead rows are marked RETIRED in their
  notes and a pending re-planner proposal that names one is dropped.
- THE LADDER (NEW `whatifs/ladder.py`, wrapped by D10; NEW tab `Ladder`, one row per Short = one step of a topic): a Short enters when
  it is made (`shorts2.run`), with the Drive id of its KEPT FOOTAGE (every paid clip as made, every start picture, the script, the plan and
  the voice timeline in one archive - what V2c-b2 opens the long video with; the archive of a topic that leaves the window unused is
  deleted). THE READING (`brain.ingest_shorts`, the daily learning job): one call a Short, by processed day; the ladder's numbers are the
  FIRST THREE processed days (the Short's first 48-72 hours - the same stretch for every Short, R17), re-pulled daily until those three
  days exist, then weekly to day 28 for the late bloomers (research 4); public views at the 24-hour and 48-hour mark come from the
  real-time monitor that already runs. THE PROMOTE RULE (`ladder.rank`, pure code): candidates = Shorts of the last `LADDER_WINDOW_DAYS`
  (30) whose topic no long video has used and that have a reading; the best non-empty class wins - (1) a declared winner, by its
  multiple; (2) "measured": the lowest sum of ranks over four measures - engaged views, share watched, subscribers per engaged view and
  shares per engaged view, the two rates by their Wilson lower bound (research 6) - ties to the more engaged views; (3) "public": views
  at the 48-hour mark. A candidate under `LADDER_MIN_ENGAGED` engaged views is ranked after every one above it and its promotion says
  "thin evidence". Engaged views divided by views is recorded, never ranked on (research 2). WHEN: at the last moment that still costs
  nothing - the tick's production gate, pre-production and `episode.produce` all call `ladder.gate`, which promotes on the spot through
  D10's own run `promote` when nothing is waiting (level-triggered: no video waits for a cron that was dropped - the B5 lesson). The
  promotion is announced by a performance memo to D4, D14, D9 and D1 and one line to the owner.
- THE REFUSAL: with nothing promoted and no override, no long video starts: the tick names no slot, pre-production writes no draft,
  `produce` returns before its first paid call, and the owner gets ONE message per slot: why, and the button "Make it anyway". His tap -
  or his own locked topic (the Owner Brief) - is an OVERRIDE row on tab `Ladder` (who, when, why), used up by the next long video.
  THE ROOM (`room.scout_and_pick`): the promoted premise is the forced first pitch (as the owner's own topic is); the Showrunner sets the
  spine around it; code keeps the premise word for word and the judges' bar cannot drop it - real viewers outrank a jury (R9). The topic
  is marked USED only when the episode's plan is safely saved (a failed planning keeps the promotion for the retry). NEW CHECK
  `topic_ladder` (script gate, owner D10, a promise about the show): the episode's draw names its ladder row, the row is this episode's
  and carries the same premise - or an override row; anything else holds the video before picture money.
- THE WINNER (the fast clock; `breakout.monitor`, tab `Breakout_Queue` + two columns `due`, `done`): a Short whose public views at the
  24-hour or the 48-hour mark reach `SHORTS_BREAKOUT_X` (3) times the median of the channel's earlier Shorts at the same mark (with fewer
  than `BREAKOUT_MIN_HISTORY` earlier Shorts: `SHORTS_WINNER_MIN_VIEWS`) is a winner: its ladder row says so, ONE follow-up Short is
  ordered with `due` = now + `FOLLOWUP_WITHIN_H` (48), a performance memo goes out, the owner gets one line with "Stop it". The Shorts
  Studio takes the order before anything else; the writers are told what the winner said and that a repeat is refused (`short_kept`).
  OVERDUE = A MEMO: the tick's `ladder.watch` writes a problem memo from D10 to D14 for an order past its clock, with the reason (no
  money, held at the short gate, the job did not run); it climbs to the Council and the owner by the memo clocks and is closed by the
  follow-up being made; an order twice its clock old lapses and stays on the owner's list until he waives it. A long video's 48-hour
  breakout keeps today's card. The hourly "link it in Studio" card of `shortslab.breakouts` is retired: at three Shorts a week it could
  never fire (it needed two Shorts inside two days), and spotting a Short that takes off is the winner rule's job now.
- NOT IN V2c-b1, on purpose (V2c-b2): how a Short is uploaded (still `specials._publish`), the long video's opening made from the kept
  footage, the cut-down reels. A long video promoted from a Short is, until V2c-b2, a long video ABOUT the proven topic that still opens
  with its own pictures.
- WHAT THE OWNER MUST HEAR (a consequence of research 1): the true numbers of a Short's first three days exist when it is about five
  days old. A topic's long video therefore follows its Short by one to two weeks, not by "5-7 days" (redesign 4.2); the first long video
  of the new code needs a Short that is five days old - or his override. The pilot (V3) will use the override for its one long video.
- CHANGED FROM THE REDESIGN, with reasons: (1) "the best 4 of the month" becomes "the best unused Short of the last 30 days, every time
  a long video starts" - the same four a month without a six-week wait and without a first month empty of long videos. (2) "After 48-72
  hours the brain reads" becomes two clocks, because the true numbers are 48 to 72 hours late (research 1). (3) A winner gets ONE
  follow-up decided by code and told to the owner (today: his approval, then two) - item 17: decide, inform, implement; R28: more Shorts
  is not better. (4) "Viewed against swiped away" cannot be read by code at all (research 2).
- HYPOTHESES: H11 stays open and gets its measure - every promoted topic is a pair (the Short's numbers, later the long video's first 30
  seconds). New H18: a Short's rank in its pool predicts its long video's views against the channel's median; H19: a follow-up inside 48
  hours gets more views than the channel's median Short.
- MONEY, said before the build: reading numbers and public views costs no rupee (API quota only: one Analytics call a Short a day until
  its three days exist, then weekly; one `videos.list` call per 50 videos a tick). The promote run is D10's own run without a model call.
  The kept footage is Drive space (about 20 MB a Short, deleted when a topic leaves the window unused). A follow-up Short costs what a
  Short costs (about Rs 290 at today's clip price, issue 83) and is paid only from the breakout fund or the reserve.
- CORRECTED BY THE BUILD (found by running, not by reading): (1) the promote rule ranks on a Short's numbers TO DATE (its first three
  processed days are recorded beside them, for the pairs that will test H11 and H18): ranking on the first three days alone would have shut
  out exactly the late bloomers research 4 names. A reading still counts only from three processed days on. (2) The Wilson bound is not
  enough by itself: 2 subscribers of 20 viewers (a lower bound of 2.8%) out-ranked 30 of 2,000 (1.1%) on both rates. Thin evidence is now
  also relative - under a tenth of the pool's best engaged views (`ladder.THIN_OF_BEST`) - and ranked after every other Short. (3) Under
  the ladder the long video's end tease cannot come from the scout's pitches (no scout runs): it names what can truthfully come next - the
  ladder's runner-up, else the best premise on the bench, which is the next Short's topic. (4) A promotion is not tied to a slot: a
  pre-production draft is not tied to one either, so "the promoted Short that waits" is one row, used up by the production whose plan is saved.
#### Step 4 BUILD (what changed)
- NEW `whatifs/ladder.py` (D10; on `tools/repair.py` PROTECTED) and NEW tab `Ladder`: `on`, `keep`, `enter`, `read`, `wilson`, `measures`,
  `rank`, `candidates`, `waiting`, `promote` (D10's run `promote`, with its performance memo and the owner's line), `why_not`, `override`,
  `gate`, `refuse`, `pitch`, `claim`, `use`, `used_by`, `runner_ups`, `topic_report`, `skip`, `order_followup`, `open_orders`,
  `order_tried`, `order_done`, `watch`.
- `whatifs/brain.py`: `_short_days` (one call a Short, by processed day; the offline YouTube is as late as the real one), `first_days`,
  `_short_metrics` (totals to date, the days covered, the first three days), `reading_complete`, `ingest_shorts` (daily until the reading
  covers three processed days, then weekly to day 28); `_short_ids` ages a Short the owner approved later from the day it went public.
- `whatifs/shorts2.py`: `cadence`, `gap_h`, `order_due`, `due`, `_budget_ok` (a Short of the cadence is core production), `pick_topic`
  (the order first, with what the winner said), the follow-up block of the writers' prompt, `run` (the order before the cadence; the
  footage kept; the Short enters the ladder; the order closed or its failed try recorded), `hook_for` seeded by the Short's id. Gone:
  `target_today`, the daily count, "the first Short of a day is core, the rest are extras".
- `whatifs/breakout.py`: `short_winner`; `monitor` judges a standalone Short at the 24-hour and the 48-hour mark against the same mark and
  orders the follow-up; a long video's breakout keeps its card (under the ladder its follow-up Shorts carry the topic, no sequel premise
  is put on the bench); "Stop it" closes an order. `whatifs/shortslab.py`: the hourly link card `breakouts` is gone.
- The long video: `whatifs/room.py` `scout_and_pick` (the promoted topic is the forced first pitch, kept word for word by code, never
  dropped by the judges' bar; the tease from the ladder's runner-ups and the bench), `whatifs/episode.py` (`produce` asks the gate before
  its first paid call and a retry keeps its topic; the draw carries `ladder`; `ladder.use` once the plan is saved; an adopted draft brings
  its row), `whatifs/preview.py` (no draft without the gate; the draft's draw carries its row), `whatifs/manage.py` (`_produce_slot` asks
  the gate and sends the one refusal message; the tick runs `ladder.watch` and no longer the hourly link card; `v12v2cb_upgrade` at both
  setup sites), `whatifs/contract.py` (`p_topic_ladder`, check `topic_ladder` at the script gate: 59 hard checks - 35 script, 19 final, 5 short).
- `whatifs/core.py`: 9 new cells (`SHORTS_PER_WEEK`, `SHORTS_PER_MONTH`, `LADDER_ON`, `LADDER_WINDOW_DAYS`, `LADDER_READ_DAYS`,
  `LADDER_MIN_ENGAGED`, `FOLLOWUP_WITHIN_H`, `SHORTS_WINNER_MIN_VIEWS`, `REPLAN_MAX_SHORTS_PER_WEEK`), 3 cells gone (`SHORTS_PER_DAY`,
  `SHORTS_KLING_EVERY`, `REPLAN_MAX_SHORTS_PER_DAY`), tab `Ladder`, 2 columns on `Breakout_Queue` (due, done), 2 on `Analytics` (days,
  first_json). `whatifs/org/levers.py`, `registry.py`: 6 levers in, 1 out (68 levers): D14 gets the cadence, the double-down line and its
  clock, D10 the window and the floor of the promote rule; D10 wraps `ladder.py` and has the entry `promote`; the check's owner is D10.
  `whatifs/org/rnd.py`: SHOW_CHECKS 48. `whatifs/truth.py`: retired rule `daily_shorts_cadence` (15 rules) with its baseline for the
  one-time move. `whatifs/replan.py`: one rung (one more Short a week, at the Shorts Studio's own estimate). `whatifs/caretaker.py`,
  `whatifs/dash.py`, `mission_control/mission_control.html` (the phone dashboard's stepper is "Shorts per week", 1 to 5),
  `whatifs/notify.py` (the ladder's answers), `whatifs/publish.py` (an archive is uploaded as an archive), `tools/gen_docs.py`.
- `tools/rehearsal.py`: the rehearsal WALKS THE LADDER - a long video is refused first (nothing spent), two Shorts are made a week ago and
  posted, their numbers are read, the long video is about the promoted one, the other stays a candidate and feeds the pre-production
  draft; it takes a fixed id (`run(ep_id=...)`), so one id reproduces the Shorts too. `tools/sweep.py`: `climb` gives every long-video id
  its own Short first.
- Seeds: `v2cb.numbers_arrive_late`, `v2cb.every_topic_starts_as_a_short`, `v2cb.rank_small_samples_by_the_lower_bound`,
  `v2cb.winner_gets_one_follow_up`, `v2cb.three_a_week`, `v2cb.late_bloomers` (158 founding items; the owner's cadence item lost the word
  "daily" - his decision "4 long videos a month" is unchanged).
- Docs: 6 matrix rows (one old row reworded), the ledger (the cadence, the money lines, the V2c-b1 paragraph), `CONCEPT.md`, 2 dated
  platform facts, the builders' recipe "The ladder" in `CLAUDE.md`, `SYSTEM.md` regenerated.
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| No long video without a promoted Short or an override on record | `ladder.gate` in `manage._produce_slot`, `preview.run`, `episode.produce` | refused before any money (tests); `topic_ladder` at the script gate holds what slipped past |
| The long video is about the promoted Short's topic, word for word | `room.scout_and_pick` (forced pitch, premise set by code), `ladder.use` | `topic_ladder` (the draw's row is this video's and carries the same premise) |
| The promote rule is code on real numbers; thin evidence last | `ladder.rank`, `wilson`, `read`, `promote` (D10's run) | the rule's tests; the run's receipts (`python -m whatifs.org.runner` RED when the call site is gone) |
| A reading counts from three processed days on | `brain.ingest_shorts`, `reading_complete`, `ladder.read` | tests (a fragment is not a candidate; it is read again the next day) |
| 3 a week, 12 a month, 48 hours apart; the daily plan may not come back | `shorts2.cadence` / `due`; truth rule `daily_shorts_cadence` | tests; Plan Guard, check `docs_current` |
| A winner gets one follow-up with a clock; overdue = a memo | `breakout.monitor`, `ladder.order_followup`, `shorts2.order_due`, `ladder.watch` | tests (the order, its due time, the memo, its closing by the follow-up, the lapse) |
| A Short's footage is kept for its long video | `ladder.keep` in `shorts2.run` | the production test (the archive holds every paid clip, every start picture, the script, the plan); the rehearsal |
#### Step 6 PROVE
- `tests/test_v12_ladder.py`: **33 tests** (30 at this step; three more came with what the sweep found, below), each rule both ways (three a week is every 48 hours and then the week is full; the month's
  ceiling, a follow-up and a held Short outside the count; an order before the cadence; the numbers by processed day - nothing at two
  days, a fragment at four, a whole reading a day later, then weekly; the first three days as one stretch; a Short approved later aged
  from the day it went public; a reading counted only from three processed days; the window and the deleted footage; the Wilson bound;
  the promote rule - a winner first, rank sums, thin evidence last, public views last of all, a tie to the newer Short; the promotion
  as D10's run with its memo, the owner's line and his "Not this one"; one long video per topic; the gate's three reasons, the override
  by tap used once, his own locked topic as an override, a promotion before a stale override; the tick naming no slot and asking once;
  the room keeping the premise word for word against judges that hate it; `topic_ladder` on seven wrong cases; the winner at exactly
  three times the median of the same mark, once, never a cut-down reel, the line without history; the follow-up made first, told what
  the winner said, closing its order; no money keeps its reason and waits; overdue = a memo only the follow-up closes; the lapse; the
  kept archive; one id, one hook; the wiring, the re-planner, the one-time move) and TWO WHOLE PRODUCTIONS: a long video refused before
  its first paid call, then the ladder walked end to end (Short -> numbers -> promotion -> long video, `topic_ladder` PASS, a second long
  video refused); and a long video that slipped past the gate HELD at the script gate with no picture and no clip paid.
- Fails correctly: **31 deliberate breaks** on the real repo, each put back by the script that made it, **each failed at least one test**
  (1 to 3 tests): the gate ignored at the tick; in `produce`; the check unable to fail; the premise not kept; the judges dropping the
  promoted topic; thin evidence not last; a raw share instead of the lower bound; a fragment counted as measured; the numbers read
  weekly only; a winner judged at one mark only; the winner line ignored; an order without a clock; no memo for an overdue order; the
  cadence without its gap; no month ceiling; a held Short tried again at once; the follow-up not first; the writers not told; a topic
  promoted twice; a promoted topic never used up; an override that never ends; a promotion not told; the promote rule outside the
  department contract; the footage not kept; a Short not on the ladder; the hook draw unseeded; the ladder binding without Shorts; a
  window that never closes; the owner's own topic no override; the old re-planner rung; the one-time move run twice. No gap this time -
  the unseeded hook draw got its test BEFORE the breaks were run, because the break list asked "what would fail if this line went?".
- Faults found by running, not by reading: (1) THE PROMOTE RULE let a Short with 20 viewers and 2 subscribers out-rank one with 2,000
  and 30 (the Wilson bound shrinks 10% to 2.8%, still above 1.1%): thin evidence is now also relative to the pool's best. (2) A TEST
  LEFT FROM V2c-a failed about once in eleven runs: it demanded two different hooks across three Shorts from an unseeded random draw
  (it failed here once, on a run that had nothing to do with hooks). Fixed at the cause - the draw is seeded by the Short's id, so an id
  reproduces its Short - and the test now asserts what the rotation guarantees. (3) The new truth rule first matched the Review Board's
  planted canary ("thirty near-identical Shorts a day") - narrowed to the retired plan. (4) A founding item dated by the owner's
  calendar day was refused by the Palace's write gate: the laptop's UTC date was a day behind. (5) Two founding items addressed to the
  Shorts Studio without a writing stage broke a V2c-a test of the writers' playbook: they belong to D10 alone. (6) My first rehearsal
  fixture had bench rows without judge scores. (7) Five of the first 29 tests failed on their own expectations (the start hour, a
  stored number read as text, a fixture that became a winner a day later, uploads not confirmed open) - none hid a fault of the code.
- Tests changed by design: `test_v11_shorts` (the daily target became "a Short of the cadence is core, a follow-up obeys the guard"),
  `test_v11_stage_e` (one rung), `test_v12_cadence` (3 Shorts a week), `test_v94b` (the dashboard's switch), `test_docs_current` (the
  new rule's sample, the small repository's baseline strings), `test_v12_exec` (68 levers, 35 script checks, the D14 lever),
  `test_v10_growth` (the hourly link card is retired), `test_v12_short` (the hook assertion).
- Fake rehearsal on the working tree of a0cf174: **GREEN four times** - F1 with Shorts in S1, F2 with S2, F1 with S3, F2 with S1. Each:
  a long video refused first (nothing spent), two Shorts made and posted (short gate 5 of 5, five department runs each), their numbers
  read, one promoted by the rule (three times "measured" among 2, once among 1 with the other thin), the long video about it (script
  35 of 35, final 19 of 19, `topic_ladder` PASS), the other Short feeding the pre-production draft.
- Full suite on a frozen copy of a0cf174: **1352 passed / 3 failed / 1 skipped** (72 test files; the skip is the dashboard test that needs
  node - GitHub runs it, and it passed there with the new "Shorts per week" switch). GitHub's run 105 showed the same three. All three
  traced, none a fault of the code: `test_v12_org` (the registry honesty test's little copy of the repo lacked `ladder.py`), `test_v86`
  (it pinned the last columns of tab `Analytics`; two were appended) and `test_v91_flaky_root` (it builds its own fresh Sheet in mid-test
  and so lost the "ladder off" default of the older tests: its long video was refused instead of failing where the test wanted). Corrected
  in 3d2139f; the three files and the ladder's file re-run: 155 passed. The whole suite ran a second time on the final code commit (below).
- **THE SWEEP FOUND A DEADLOCK** (the first sweep, on a frozen copy of 3d2139f): **24 of 24 long-video ids were refused** - "1 Short(s)
  have no numbers yet ... none is public yet". Cause: on a new Sheet a Short is posted only when uploads are known to be open, the
  zero-cost upload check that proves it ran ONLY inside the long-video job, and under the ladder that job waits for a posted Short. On a
  new Sheet no Short would ever have been posted and no long video ever made. (The rehearsal and the end-to-end test had not seen it:
  both start with a refused long video, which ran the check by the way.) Fixed at the cause in 6d785e7: a Short's own job runs the
  upload check before its first paid call and starts nothing while YouTube keeps uploads private; two tests, two more deliberate breaks
  (33 in all, each failed a test), a matrix row. The sweep was started again from its first id.
- **THE SECOND SWEEP WAS CUT OFF BY THE SESSION'S USAGE LIMIT, WITH A FIX HALF DONE** (12 Nov 2026): 3 of its 20 ids had started and
  none was read when the session ended - four files changed, one test red, nothing recorded. A new session read the change, completed
  it and proved it. One family of faults - WHAT COUNTS AS A SHORT THAT WAS MADE:
  (1) `shorts2._held` took every status that begins with "HELD" for a refusal at the short gate. The upload path writes "HELD (uploads
  not confirmed open)" for a Short that was MADE and paid in full: it read as "not made" - the cadence did not count it and started
  the next Short a day later, its topic stayed free to be made a second time, and it was missing from the last ten the next Short
  must differ from. It is recognised by the upload path's own status now (`shorts2.UPLOAD_HOLD`; a test ties the two together, and a
  gate check whose name happens to carry the word "upload" stays a refusal) and counts as made.
  (2) A Short whose job CRASHED (the clip model, the voice, Drive) left no row at all: the tick started the job again at its next
  turn, and again - and every try pays the writers first. A crash is a row `FAILED (reason)` on tab `Specials` now: the cadence waits
  `HELD_WAIT_H` (24) hours; a crash is no made Short (the week, the month, the week's ceiling, the first Shorts that need the owner's
  Approve, the last ten) and says nothing against its topic.
  (3) `breakout.monitor` compared a Short at the 24-hour and 48-hour mark with EVERY row of kind "short" on tab `Monitor48` - the
  cut-down reels of long videos, the special reels and the pilots too: one reel with a million views would have moved the median so
  far that no Short could be a winner. The history is the ladder's own Shorts now.
  Proof: three tests (a new one for the upload hold; the crash test, which also makes the next Short and asks for the winner's order;
  the winner test with a planted reel) and **9 more deliberate breaks, each failed a test (42 in all)**. Writing the break list first
  found two assertions that were missing (the first Shorts that need his Approve, the week's ceiling). `tests/test_v12_ladder.py` has
  33 tests. The red test was the cadence test: it still read the old sentence of the message that the fix reworded. Two matrix rows
  reworded (the cadence, the winner); the takeaway item carries the sweep's evidence. NOT KNOWN: which sweep id, if any, showed these
  three faults - the session that found them left no note. They are proven by test and by break, not by an id. The ten test files
  around the change (the ladder, the Short, the older Shorts and breakout tests, growth, the docs, the Palace, the matrix, the upload
  lock) on the working tree: **230 passed**.
- Fake rehearsal on the FINAL code (the working tree of 3ab0e16): **GREEN three times** - F1 with Shorts in S1 (EP202611112251), F2
  with S2 (EP202611112255), F1 with S3 (EP202611112300): every long format and every Short format. Each: a long video refused first
  ("no Short has been made yet: every topic starts as a Short", nothing spent), two Shorts made and posted (short gate 5 of 5), their
  numbers read, one promoted by the rule ("measured": among 2 Shorts twice, among 1 once), the long video about it (script 35 of 35,
  final 19 of 19), the other Short promoted next, for the pre-production draft.
- Full suite on a frozen copy of the FINAL code commit 3ab0e16: **1358 passed / 0 failed / 1 skipped** (72 test files; the skip is the
  dashboard test that needs node - GitHub runs it).
- Sweep on the same frozen copy of 3ab0e16, after the suite had finished: **58 of 58 ids**. No bad id, no failure class. A: 20 ids,
  organisation on - every id climbed the ladder first (its own Short made a week ago, its numbers read, the promotion) and its long
  video was scheduled: 13 drew F1 (41 pass + 13 not applicable of 54 checks), 7 drew F2 (48 pass + 6 not applicable) - the split of
  V2a and V2c-a with one more check, `topic_ladder`; 11 department runs each. (The first sweep of this batch had refused 24 of 24.)
  B: 4 ids, organisation off - 4 ok, each climbed. C: 4 full rehearsals with a fixed id - 2 in F1, 2 in F2, each refused first and
  then walked the ladder. D (`--mode short`): 20 ids, two Shorts each - 40 Shorts (20 in S1, 18 in S2, 2 in S3), every one 5 of 5 at
  the short gate with 5 department runs, no memo left open, no warning. E: 10 more ids forced to S3, two in a row each - 20 Shorts,
  10 of 10. The warnings of A to C are the classes the offline long video has always printed (the stand-in voices, the atmosphere's
  time valve - issue 26, the prompt-cache note - issue 23, the offline writers' retention fix, the script length; in the rehearsal
  also its own table-read room, "script N% similar to EPTABLE"); none comes from the ladder. NOT covered by the sweep: a Short that
  crashes and uploads that stay closed (open issue 109).
- GitHub Checks (standing rule 1): run **110** on 3ab0e16 **GREEN**: 1359 passed (26:10), rehearsal GREEN (episode EP202611112325;
  contract script 35/35, final 19/19); its one warning and its notices are GitHub's own (Node.js 20, the Ubuntu label - open issues 37
  and 46). Runs 107 (3d2139f), 108 (30f8cca) and 109 (6d785e7) GREEN. Runs 104 to 106 RED, before the three tests that pinned what
  the batch changed by design were corrected (105 was read: the same three as the laptop suite; 104 and 106 were not read).
- Plan Guard GREEN, Truth GREEN, Palace GREEN (159 founding items), Organisation GREEN (12 wired, 5 pending), docs regenerated
  without drift.
- Money: Rs 0 spent (fake mode). The ladder adds no paid call: the numbers and the public views are API quota, the promote run calls
  no model, the kept footage is Drive space (`tests/paid_calls.py` is unchanged and green in the suite). A follow-up Short costs what
  a Short costs (about Rs 290 at today's clip price, open issue 83) and is paid only from the breakout fund or the reserve. At that
  price twelve Shorts a month do NOT fit beside four long videos: the code keeps the long slots' money and pauses the Shorts when the
  rest is used up (`shorts2._budget_ok`) - V2d's model by value must close the gap before three a week is real.
#### Step 7 TAKEAWAY (also Palace item `v2cb.takeaway`)
- WORKED: reading the platform's own page BEFORE the design. One page (YouTube's numbers are 48 to 72 hours late) turned "read the
  numbers after 48-72 hours" into two clocks; built as first written, the promote rule would have ranked fragments.
- WORKED: the break list written as "what would fail if this line went?" before it was run - 42 breaks, each failed a test, and three
  times the LIST found a missing test before any break ran (the unseeded hook draw; the first Shorts that need his Approve; the week's
  ceiling). And the case built to defeat a guard: 2 subscribers of 20 viewers beat 30 of 2,000 through the Wilson bound.
- WORKED: the sweep after a green suite. It is the only proof that starts from an empty Sheet with nothing run before.
- FAILED: the suite and four rehearsals were green while on a new Sheet NO VIDEO COULD EVER HAVE BEEN MADE. Both proofs began with a
  refused long video, and that refused job ran the upload check by the way - the very thing the first Short needed. A proof that starts
  with a helpful accident says nothing about the first run. When a rule makes one job wait for another, list everything the waiting
  job used to do "by the way".
- FAILED: the session ran into the weekly usage limit with a fix applied and no note: four changed files, one red test, a sweep nobody
  read. The checkpoint rule exists for exactly this. Write the finding into this file BEFORE the edit that fixes it.
- LIMIT: nothing real has met the ladder. No real Short has been measured; the day-by-day Analytics report has never been called; "five
  days" rests on YouTube's own latency page. No study pairs a topic's Short with its long video and none measures a follow-up: the four
  equal votes of the promote rule, the 3-times line and the 48-hour clock are starting values (H11, H18, H19). Until V2c-b2 a promoted
  topic's long video opens with its own pictures and a Short is uploaded the old way (one text for every platform).
- NEW QUESTION: does a Short's rank in its pool predict its long video (H18)? Every promoted topic is a pair on record; the redesign's
  own rule (4.4) drops a rule that does not predict after 12 pairs - at four long videos a month that is three months of real data.
- ORGANISATION: a status text is data that other code reads. "HELD" meant two different things on one tab and the cadence believed the
  wrong one: whether a Short was MADE needs its own field (V2c-b2, open issue 107).

### V2c-a - THE SHORT, THE PRODUCT (11 Nov 2026) - ACCEPTED (final code commit 3b34cc3 GREEN in GitHub Checks run 99: 1325 passed; sweep 58 of 58 ids)
The owner: "continue" (a new session for this batch). V2c was SPLIT AT THE START (rule 6): V2c-a is the short video as a product a viewer meets;
V2c-b is the ladder (Shorts first, the cadence) and the platforms. It answers his item 20 ("reels ... made for breakout virality ... dont make
excuses"), closes open issues 13 (standalone Shorts outside the department contract) and 62 (Shorts outside the viewer's seat).
A fault of this session, said plainly: the first start skipped part of the binding reading order (`01`, `03`, sections 0-9 of the redesign, the
V1a / V1b / V2a records and the open issues). The owner stopped it; the batch was started again from the first step. Nothing had been built.
The session also ran into its usage limit after the proof step; it stopped with a note here, and the same session finished the batch.

#### Step 1 RESEARCH (E = measured, O = practice / vendor; "read" = the page was read by the build session; the redesign's R20-R38 are the base)
1. E read - YouTube Help 12220281 "Understand your YouTube content performance" (states the view change of 24 Aug 2026): engaged views = "How
   many times viewers stayed to watch past the initial seconds, not including any loops"; "Stayed to watch" = "The percentage of times viewers
   stayed to watch past the initial seconds of a Short". -> the number the Partner Program counts is decided in the initial seconds, once per
   viewer. A LOOP ADDS NO ENGAGED VIEW: the loop is built for the viewer who stays, never claimed as a way to the 10 million.
2. E read - TechCrunch, 26 Mar 2025 (https://techcrunch.com/2025/03/26/youtube-is-changing-how-youtube-shorts-views-are-counted): public views
   count every start and replay; earnings and Partner Program eligibility "will continue to be based on engaged views".
3. E read - P. Galloway's own thread, 14 Apr 2023 (https://threadreaderapp.com/thread/1646898356419981315.html; 5,400 Shorts of 33 channels,
   3.3 billion views): "shorts with under 60% VVSA rarely performed well"; likes, shares, comments: "We didn't observe any strong relationships";
   "Longer shorts in the study performed much better on average"; "This is still early research". CORRECTION of the redesign's R23: the sample
   is 33 channels, and the same study found LONGER Shorts did better.
4. E read - OverseerOS, 29 Oct 2026 (https://www.overseeros.com/blog/best-youtube-shorts-length; 16,537 Shorts, 1,137 channels, views at 7-30
   days): median views 36,970 at 16-30 s, 22,947 at 31-45 s, 20,938 at 46-60 s, 21,913 at 1-15 s; inside one channel 16-30 s beat 31-60 s on
   105 of 183 channels (57.4%); "should not be interpreted as the causal effect of adding or removing seconds". -> 3 and 4 DISAGREE on length:
   the length of a Short is a lever per format with a starting band, never a belief.
5. E read - Socialinsider, 24 Jun 2026, updated 6 Nov 2026 (https://socialinsider.io/blog/instagram-reels-statistics/; 9,771,822 Reels of
   brand accounts): the skip rate - plays swiped away inside the first 3 seconds - is 65.5% for small accounts and 60.5% for large ones; reach
   is best at 30-60 s (5.60%) and 3.50% beyond 120 s. Brands, not creators. Confirms R23's Instagram line.
6. E read - arXiv 2611.13002, 8 Nov 2026, full text (https://arxiv.org/html/2611.13002; 92,654 Shorts, 345 creators, published Jan 2025 -
   Apr 2026): correlation with views: share of frames with text r = -0.08, hashtags -0.06, length -0.05, has text -0.05; "generally weak";
   hooks and first seconds were NOT analysed. R24 confirmed and made exact: text on screen does not buy views (if anything slightly fewer).
   -> the promise words on screen are kept small and short-lived, behind a switch the learning loop can test - not sold as a booster.
7. E read - YouTube Help 1311392, monetisation policies (the rule renamed on 15 Jul 2025; applies to Shorts): not monetisable - "Image
   slideshows, templated storylines, or scrolling text with minimal or no narrative, commentary, or educational value", "AI-generated content
   made with generic or unoriginal templates giving the impression of mass production"; monetisable - "Same intro and outro for your videos, but
   the bulk of your content is different", a series where "each video has a distinct storyline, focus, or concept". -> three Short formats, a
   variety check over the last ten, every second animated (no slideshow), no fixed end plate.
8. E read - TechCrunch, 25 Aug 2023, YouTube's Shorts lead (https://techcrunch.com/2023/08/25/youtube-demystifies-the-shorts-algorithm-views-and-answers-other-creator-questions/):
   a seed audience, then "a lot more traffic or it may taper off"; viewers "are swiping through content not knowing what comes next"; for Shorts
   "most thumbnails are never seen"; time of day is "not a factor to optimize for"; deleting and re-posting is treated as spam. -> the first
   frame IS the packaging of a Short; the Shorts thumbnail (V2c-b) is a small thing.
Reported by a search run only (not read): vendor benchmarks for "stayed to watch" disagree (60% to 80%) and none is official; the platform
buttons cover roughly the lowest 15-25% and the right 15% of the frame (vendors; no official figure) - the captions' 38% lift (existing cell) is
on the safe side.
NOT FOUND, so nothing is claimed on it: a measured effect of a loop, of the number of words in a spoken hook, or of promise text on screen on
the share who stay; a reliable figure for how many watch short video without sound (the 85% and 92% figures are old and about other formats).
The hook budget (12 words, 3 seconds), the promise text and the loop are STARTING VALUES from the redesign and the owner's own judgment; each is
a lever or a switch, and hypothesis H15 below asks the viewers.
AN EXPERIMENT BEFORE THE DESIGN (the V2a lesson; fake mode, 7.6 seconds): today's standalone Short is 30.5 s; it OPENS on a 0.5 s still title
plate and ENDS on a 2.5 s plate "The full trial is on the channel" (an ask, and the end of any loop); 1 of its 6 clips is made by the hero model
and only in every third Short - the other five are "subtle living motion"; four courtroom voices speak ("Objection!", "Exhibit A"); every beat
carries a name plate. A cut-down courtroom, not a product.
#### Step 2 CREATIVITY (scores 1-5: what a viewer gains / enforceable / cost / reliability / owner effort)
A. New words in the old prompt (the mini-trial pipeline stays): 2 / 1 / 5 / 3 / 5 = 16 - the title plate, the name plates, the end plate and
   "one hero clip in six" stay; nothing is measured.
B. The Short is the first 30-40 seconds of the long video (the redesign's 4.2 as first written): 3 / 3 / 4 / 3 / 5 = 18 - a by-product, which
   item 20 forbids; it needs the long script first and ends on an open question instead of a complete story.
C. A model scores every finished Short for "virality" and code publishes above a line: 2 / 2 / 3 / 2 / 5 = 14 - taste as a gate (R9: weak).
D. (ORIGINAL, CHOSEN) THE SHORT AS DATA, PLANNED BY CODE, CLOSED BY CODE: a Short format is a row (its beats, its ending, its length, its
   camera); three scripts are written in it and judged blind; code - not a model - plans the pictures: the first frame is the moving
   impossible picture, every second is an animated clip, each clip starts on the last frame of the one before, and THE LOOP IS CLOSED BY CODE
   (the first clip played backwards is the last clip, so the last frame IS the first frame). D13 measures script, real voice and plan before
   any picture is paid; the writers' one fix carries what code cannot repair; then four checks hold: 5 / 5 / 3 / 3 / 5 = 21.
#### Step 3 DESIGN MEMO
- SHORT FORMATS AS DATA (`formats.SHORTS`, beside the long formats): S1 "The second it changed" (beats: picture, consequence, consequence,
  question; ends on a question; 20-35 s; a cut per beat), S2 "What would you do?" (power, personal, turn, choice; ends on the viewer's choice;
  20-45 s; a cut per beat), S3 "The whole thing in 30 seconds" (idea, why, scale, return; 20-35 s; ONE continuous shot). Shares 40 / 40 / 20 over
  the last ten Shorts (levers of D14, as the long shares are levers of D1). One guide voice speaking to "you"; nobody on screen.
- THE WRITERS (D14 `write`, the playbook inside the writer's prompt): the format's brief, the hook archetype the learning core picked (a
  trial-only archetype is not offered), the openers of the last ten Shorts to stay away from; SHORTS_VARIANTS scripts; a script the seat finds
  clean goes to the blind jury (the room's own cross-family jury); the winner gets ONE fix with every measured problem named.
- THE VOICE (D7 `short_voice`): the long video's voice job, so the timeline is real and the breathing rule applies.
- THE PLAN (code, no model): shots cover every second from 0.0; each is a 5-second hero clip; a beat's first clip starts on its own picture
  (S1, S2) or on the last frame of the clip before (inside a beat; everywhere in S3); the last seconds are the FIRST clip played backwards.
  No title plate, no name plate, no end plate, no stock. Captions word by word above the platform buttons; the promise in at most 6 words at
  the top from the first frame (a switch: research 6 gives it no credit for views).
- THE VIEWER'S SEAT FOR A SHORT (D13 `short_seat`, NEW `whatifs/org/shortseat.py`; measure -> repair by code -> the one fix -> check -> lever):
  `short_open` - the plan starts at 0.0 on an animated made picture, the first spoken sentence has at most 12 words and ENDS inside 3.0 s of
  the real voice, the promise text is on screen inside the first second; `short_plain` - at most one number heard, no expert word (the
  layman measure); `short_shape` - the real length inside the format's band, the last line hands back to the first (a content word of the
  opening returns), no ask and no greeting, every second planned as animation, no stock, the loop shot last, captions above the buttons;
  `short_kept` (owner D14) - the beats are the format's, the ending is the format's, it does not sound like a trial, and it is not like the
  last ten (script likeness, the first three words, and the pair format + hook differs from the last two). A fifth check `short_contract`
  is the organisation's: the four department runs of this Short finished under the department contract.
- A HELD SHORT IS NOT MADE: no picture is paid, the owner is not asked (a Short is cheap and he has two minutes a day), the owning department
  gets the problem memo, the topic is tried once more and then left.
- CHANGED FROM THE REDESIGN, with reasons: (1) "no two in ten with the same format and structure" is measured as likeness of script and
  opener plus rotation of format and hook - three formats times four hooks are twelve structures, which cannot fill ten slots under any
  shares without taking the hook choice away from the learning core. (2) "12 words inside 3 seconds": at a normal pace 3 seconds hold about
  7 words; the 3 seconds are the rule that binds and they are judged on the real voice. (3) The promise text is a switch, not a belief.
  (4) The loop is for the viewer who stayed; nothing claims it counts toward the Partner Program (research 1).
- NOT IN V2c-a, on purpose: the cadence (3 a week) and Shorts first (V2c-b), the uploads per platform (V2c-b), the hero model by value and
  the measured `moving_share` on the finished file (V2d). The Short is PLANNED as animated in every second here; V2d measures it.
- MONEY, said before the build: a 30-second Short is 5-6 hero clips at today's price (USD 0.42 each) = about Rs 210-250, plus up to 4
  pictures, the voice and the writing (three scripts, the jury, one fix: about Rs 40). About Rs 250-300 a Short - twice the redesign's
  Rs 150. Twelve would not fit beside four long videos until V2d chooses the hero model by value. The budget gate counts every clip, so
  today's code would simply make fewer. Nothing is spent before the pilot.
- HYPOTHESES added: H15 the promise text on screen raises "stayed to watch"; H16 a Short that loops by picture is watched past 100% more
  often; H17 which Short format holds best (the shares follow).
- CORRECTED BY THE BUILD (the first fake Shorts were counted): the first plan cut every beat into 5-second clips and paid 7 clips for a
  24-second Short. A clip may now cover a shot up to 30% longer than itself by being played that much slower (`shortseat.STRETCH_MAX`), so a
  beat of 5 to 6.5 seconds is ONE paid clip: 3 clips for S1 and 4 for S2 and S3 in the fake Shorts (about Rs 125-165 of animation). The
  estimate follows the plan (`shorts2.est_inr`) and a test proves it covers the clips really made. Whether a clip slowed by a quarter looks
  right is unknown until the pilot; V2d's choice of a model with longer clips removes the need.
#### Step 4 BUILD (what changed)
- NEW `whatifs/org/shortseat.py` (D13; on `tools/repair.py` PROTECTED): `on`, `hook`, `open_report`, `plain_report`, `shape_report`,
  `script_issues` (the one fix), `shape` (the repair of the plan), `m_shape`.
- `whatifs/formats.py`: `SHORTS` (S1, S2, S3), `SHORT_HOOKS`, the house brief and the three format briefs, `short_pick`, `short_len`,
  `short_shares`, `short_brief`, `short_rubric`, `short_using`, `opener`, `likeness`, `short_kept_report`, `short_kept_issues`.
- `whatifs/shorts2.py` REBUILT (now on PROTECTED): `history`, `pick_topic` (a held topic is tried once more, then left), `hook_for` (format
  and hook rotate by code), `est_inr`, `valid`, `write`, `voice`, `plan`, `make` (pictures, clips chained on the frame before, the loop, the
  captions, the sound), `_loop_diff`, `description`, the short gate's memo hooks, `run`. Gone: the cast, the name plates, the 0.5 s title
  plate, the end plate with its ask, "one hero clip in every third Short", the courtroom brief and its punchline rule.
- `whatifs/contract.py`: five probes and five rows at the NEW stage "short" (58 hard checks: 34 script + 19 final + 5 short).
- `whatifs/org/__init__.py`, `registry.py`: department D14 Shorts Studio (17 departments, 12 wired, 5 pending); `shorts2.py` moves from D9
  to D14; D13 also wraps `layman.py` and `shortseat.py`; entries D14 `write` / `make`, D7 `short_voice`, D13 `short_seat`, D8 `short_gate`;
  the runs a Short needs before its gate (`EPISODE_RUNS["short"]`); D14's writers get their playbook in the prompt (`PROMPT`); five check
  owners. `levers.py`: 12 rules (63 levers: 7 of D14, 5 more of D13; every loosening needs the owner). `rnd.py`: SHOW_CHECKS 47,
  `short_contract` among the organisation's own.
- `whatifs/org/runner.py` (LOAD): an empty Sheet gets its founding knowledge BEFORE the cast is mirrored (a fault found by the first fake
  Short, step 6). `whatifs/models.py`: role `short_writer` on the long script's chain. `whatifs/specials.py`: `_publish` takes a text.
  `whatifs/manage.py`: `v12v2c_upgrade` at both upgrade sites. `whatifs/core.py`: 18 cells, 3 columns on tab `Specials` (hook, script,
  sec), SHORTS_NEED_MASTERS default FALSE. `whatifs/fakes.py`: the offline writer of a Short (two scripts per format, about the premise it
  is given). `tools/rehearsal.py`: one Short is made and asserted. `tools/sweep.py`: mode `short`. `tools/gen_docs.py`: the short gate is
  counted.
- Seeds FIRST (the runner refuses a department without a playbook - it did, step 6): `v2c.short_is_a_product`, `v2c.first_seconds_decide`,
  `v2c.short_seat`, `v2c.length_is_a_lever`, `v2c.no_two_alike`, `v2c.text_earns_no_views`, `v2c.loop_by_code` (151 founding items).
- Docs: 7 matrix rows (one old row lost its dead reference), the ledger line, `CONCEPT.md` rewritten (the trial is format F2; the Short has
  its own formats), the builders' recipe in `CLAUDE.md`, one dated platform fact, `SYSTEM.md` regenerated.
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| A Short is made in ONE Short format, one guide voice, no courtroom | `formats.short_pick`, `short_brief` in `shorts2.write` | `short_kept` (short gate) |
| The first frame moves; the hook ends inside 3 s of the real voice | `shorts2.plan`, `shortseat.shape`; the one fix | `short_open` |
| One number at most, no expert word | `shortseat.script_issues` in the one fix | `short_plain` |
| The format's length, the hand-back, no ask, every second a clip, the loop, captions | `shorts2.plan` / `make`, `shortseat.shape` | `short_shape`; `_loop_diff` on the file (a test) |
| No two alike; format and hook rotate | `shorts2.hook_for`, `history`; the one fix | `short_kept` |
| The Shorts Studio, Sound and Audience ran before the gate | `runner.work` in `shorts2.run` | `short_contract`; `python -m whatifs.org.runner` RED |
| A held Short is not made and nobody is asked | `shorts2.run` (the gate before `make`) | the production test (no clip, no picture, no message) |
| Every paid clip is in the estimate | `shorts2.est_inr` before the budget rule | the production test (estimate >= clips made) |
#### Step 6 PROVE
- `tests/test_v12_short.py`: **22 tests**, each rule both ways (the format rows and the pick with its shares; the offline writer scanned over
  every premise of the sweep in every format; the hook's words and its end on the real voice; the first frame and the promise text; one
  number and no expert word, nothing exempt; the length, the hand-back, asks and ordinary sentences that are no asks; the plan in every
  format; the plan judged; the seat's repair, unchanged when shaped twice; the format kept; no two alike inside a window of ten; the rotation
  of format and hook; the writers' one fix with every problem named; only clean scripts before the jury; the gate's five checks; wiring,
  levers, the one-time move; the REAL production in S1, S2 and S3 - five department runs each, the playbook inside the writer's prompt, the
  clips and pictures counted against the estimate; the loop on the finished file both ways; a refused Short held, not made, nobody asked,
  the topic tried once more and then left, the problem memos closed by the next Short that passes; two in a row differ and a copy is held;
  a creative run that goes first on an empty Sheet). `tests/test_v11_shorts.py` rewritten: 6 tests of the track (due, money, follow-ups,
  review).
- Fails correctly (eleven deliberate breaks on the real repo, each reverted by the script that made it): D13's run removed -> 8 tests fail
  and the organisation check is RED ("no runner call for D13 'short_seat'"); the gate ignored -> 2; the seat's repair off -> 1; format and
  hook not rotated -> 3; the one fix removed -> 1; the cast mirrored before the founding knowledge -> 7; the hook not judged on the real
  voice -> 1; the estimate understated -> 2; asks not recognised -> 3; likeness not judged -> 2; THE LOOP NOT CLOSED -> **0 at first**.
- Faults found by running, not by reading: (1) THE FIRST FAKE SHORT did not start: on an empty Sheet a creative run that goes first was
  handed the cast and none of the founding knowledge (the cast was mirrored before the "is the Palace empty" test - since B6a, for D4 too).
  Fixed in `runner.run`; a test. (2) AN OLDER TEST, not a new one, found a Short about the Sun HELD: the hand-back rule counted only words
  of four letters and more. Fixed at the cause (`shortseat.content_words` knows short content words and a list of fillers); every premise of
  the sweep and four three-letter subjects are scanned in a test. (3) THE OPEN LOOP FAILED NO TEST: the offline clips barely move and the
  words burned into the first and the last frame hid the picture. The measure now compares only the band of the picture that carries no
  words (limit 0.01), a test uses clips that scroll (closed 0.001, open 0.028), an open loop is reported to the organisation as a lesson -
  the break now fails 3 tests. (4) The first plan paid 7 clips for a 24-second Short (above). (5) A founding item with "buy views" in its
  title was refused by the Palace's own write gate ("gaming the platform") - reworded. (6) Seven of the first 21 tests failed on their own
  expectations (arithmetic, a constant's spelling, a stored field read the wrong way) - corrected, none hid a fault of the code.
  (7) GITHUB'S CHECKS WERE RED FOR A CAUSE OUTSIDE THE CODE: runs 92 to 96 (two of them before this batch, two of them text-only commits)
  hung up to an hour in the step that installs ffmpeg and failed with apt's exit code 100 before any test ran; other public repositories
  reported the same on 11 Nov 2026 (GitHub's regional Ubuntu mirror did not answer). Traced on the public run page (step 4, line 107) and
  repaired at our end: the step in `checks.yml` is bounded at 30 minutes, falls back to archive.ubuntu.com and names its cause on the run page.
- Tests changed by design: 17 departments and 17 playbooks, 63 levers, 5 checks at the stage "short", the one-time moves list, the registry
  honesty test copies `shorts2.py` into its little tree, and `tests/test_v102.py` allows the stage "short" (found by the full suite, below).
- Fake rehearsal on the final code: GREEN on the working tree in F1 with a Short in S1, in F2 with S2, in F1 with S3 (each: the long
  episode's 53 checks as before, then the Short - short gate 5 of 5, five department runs, 21.7 to 23.7 s, the loop closed); 4 of 4 GREEN in sweep C on the frozen copy of 3b34cc3; GitHub's own rehearsal GREEN (episode EP202611111811, script 34/34, final 19/19; its Short is asserted inside the rehearsal - the run page does not print the Short's line yet).
- Full suite on a frozen copy: the whole suite ran on 486eb41: **1323 passed / 1 failed / 1 skipped** (71 test files). The one failure, traced: `tests/test_v102.py::test_every_feature_has_a_probe_and_a_promise` pinned the contract's stages to script and final; the stage "short" is by design (GitHub's runs 97 and 98 showed the same single failure). Corrected in 3b34cc3. On the frozen copy of 3b34cc3 the corrected file and the two Short files were re-run: **46 passed / 0 failed** (test_v102 18, test_v12_short 22, test_v11_shorts 6); the four files that read the workflow passed on the working tree (123). The whole suite on 3b34cc3 ran on GitHub (below): 1325 passed. NOT done: the whole suite a second time on the laptop on the final commit.
- Sweep on a frozen copy of 3b34cc3: **58 of 58 ids**. No bad id, no failure class. A: 20 ids, organisation on - 13 drew F1 (each 40 pass + 13 not applicable of 53 checks) and 7 drew F2 (47 pass + 6 not applicable): the same split and the same counts as in V2a, so the long video is untouched. B: 4 ids, organisation off - 4 ok. C: 4 rehearsals - 2 in F1, 2 in F2, each with its Short made and asserted. D (new, `--mode short`): 20 ids, two Shorts each over 24 premises - 40 Shorts (20 in S1, 18 in S2, 2 in S3), every Short under test 5 of 5 at the short gate with 5 department runs, no memo left open, no warning. E: 10 more ids forced to S3 because the mix had drawn it only twice - 20 Shorts, two in a row each, 10 of 10 ids.
- GitHub Checks (standing rule 1): run **99** on 3b34cc3 **GREEN**: 1325 passed (41:22), rehearsal GREEN (episode EP202611111811; contract script 34/34, final 19/19). Runs 92 to 96 RED at the step that installs ffmpeg (apt's exit code 100 after 28 to 63 minutes; no test ran): GitHub's package mirror, repaired at our end in `checks.yml` (above). Runs 97 (486eb41) and 98 (3f5f99c) RED: 1 failed / 1324 passed - the one stage-pinning test the laptop suite found, corrected in 3b34cc3; not re-run. Run 98 was the first with the bounded install step: it went through on the first mirror, so the fallback branch has still never run.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (152 founding items), Organisation GREEN (12 wired, 5 pending), docs regenerated without drift.
- Money: Rs 0 spent (fake mode). In production a Short is estimated at about Rs 290 in the middle of its length band (6 clips of the hero
  model at today's price, 3 pictures, Rs 36 for the three scripts, the jury, the fix and the voice); the fake Shorts of 22-24 s needed 3
  to 4 clips (about Rs 125-165 of animation). The writing allowance is the old cell, not measured (open issue 83).
#### Step 7 TAKEAWAY (also Palace item `v2c.takeaway`)
- WORKED: the V1a pattern a fourth time (measure -> repair by code -> the one fix -> check -> lever), on a product that had no check at all.
- WORKED: breaking the code on purpose with a script that puts every file back. Ten breaks failed tests at once; the eleventh showed a
  measure that could not tell kept from broken. A measure is trusted only after it has failed on a version broken on purpose.
- WORKED: an experiment before the design (the old Short measured in 7.6 seconds) and counting the first fake Shorts (7 paid clips -> 3).
- FAILED: I started this batch without the whole reading order and the owner had to stop me. And my first hand-back rule repeated the V1b
  fault in a new place: it held what it did not know (a three-letter word) instead of what it could recognise as wrong.
- LIMIT: nothing here proves a viewer stays. No real model has written a Short and no real clip has been made: whether a clip slowed by a
  quarter, a chain of clips started on the frame before, or a first clip played backwards LOOK right is unknown until the pilot. "One idea"
  is not measured. The hook budget, the promise text and the loop rest on the redesign and the owner's judgment, not on a study (none was
  found); only real numbers after publishing can say (H15-H17).
- NEW QUESTION: which Short format holds viewers best (H17)? The shares are data and the format is in the learning core's features, so the
  answer can move them (V2c-b reads the numbers, V4 moves the shares).
- ORGANISATION: a new department's first run needs its founding knowledge AND an empty Sheet must be seeded before anything else is
  mirrored into the Palace; a problem a later run can close should carry no episode (one memo per class of failure).

### V2a - FORMATS AS DATA AND THE THREE-TIER CONTRACT (11 Nov 2026) - ACCEPTED (final code commit 75c55ea GREEN in GitHub Checks run 91: 1303 passed; sweep 28 of 28, both formats)
The owner (mobile only): "Continue". V2 was SPLIT AT THE START (rule 6): V2a is the foundation - an episode has a format, and a format decides
which of the show's devices are required. It answers "the whole video looked a lot gimmicky" (item 16), "IF YOU HAVE TO REDESIGN CHANNEL, DO IT"
(item 17) and "WE AND PIPELINE BRAIN SHOULD BE SMART TO CHANGE THE TYPE OF VIDEO MAKING OR FORMATTING" (item 19).

#### Step 1 RESEARCH (E = measured, O = practice / vendor; "read" = read by the build session, else reported by a search run)
1. E read - Tubefilter, 13 Jul 2026: https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/ - YouTube's
   clarified examples of "generic or repetitive content": content that "looks like it's made with a template" or "may feel repetitive to viewers
   after watching several videos in a row from the same channel"; "videos where characters are put in the same situation over and over again with
   the same outcome"; storylines that follow a fixed formula. The whole channel is demonetised. -> a weekly trial with the same characters, the
   same room and the same shape of verdict is the textbook case. Formats and their devices must VARY, by data, not by hope.
2. O read - THE FIRST HAND-MADE ROUND OF THE BREAKOUT OBSERVATORY (redesign 10.5): three channels, one per ring, from a vendor's public pages
   (outlierkit.com/channel/..., read 11 Nov 2026; the vendor's baseline is the median of the 6-14 newest uploads and its line is 1.5 times, not
   our 5; ages differ; TITLES ONLY - nobody watched a video). 12 hits, 14 siblings:
   - Far ring, "What If Levels" (3,100 subscribers, 41 videos, data of 8 Nov 2026): hits "What If You Had 10,000 IQ?" (445,000 views, 159 times
     the median), "What If You Could Read Minds... and Heard Your Wife's First?" (30,000; 10.7), "What If You Went Back to 2000 With Everything You
     Know Today?" (2.7), "What If You Could See How Long Everyone Has Left to Live?" (2.5). Siblings at 0.4-1.2: "...See Who Has a Crush on You?",
     "...Everyone Had the Same Death Countdown?", "Could 2 People Really Restart Humanity?", "What If Hitler Died in 1918...", "...All Men
     Disappeared Except You?", "...the Only One Who Never Needed Sleep?".
   - Our ring, "Science eXplore" (34,700 subscribers, 48 videos, 6 Nov 2026; its newest videos get about 180 views): hits "The Psychology Of
     Being Lazy But Ambitious" (11.5), "What If Light Moved at Only 60 MPH?" (8.2 after 5 days - 1,500 views; nearly the premise of the owner's
     rejected video), "The Entire History Of The Atomic Bomb" (4.8), "Brainrot Cure: 10 Scientific Signs..." (4.7), "The Land Of Magic" (3.5),
     "What If You Fell Into Jupiter?" (2.1). Siblings at 0.8-1.0: four health warnings about the brain and the body.
   - Near ring, "Wacky Science" (825,000 subscribers): hits "ALL OF PHYSICS explained in 14 Minutes" (11 million; 2.8), "GENERAL CHEMISTRY
     explained in 19 Minutes" (1.6); siblings: smaller subjects in the same form (QR codes 0.2, Braille 0.1).
   WHAT THE SIBLINGS SHOW (the reason they are there): "you" in the title does NOT separate hits from normal videos - 4 of 4 hits and 4 of 6
   siblings of the far channel carry it. Numbers in the title do not separate either. Two differences are visible, each inside one channel:
   (a) scenarios that happen to YOU sit at the top and the two world / history scenarios without "you" at or below the median; (b) in the science
   channel the two impossible-scenario titles beat every health warning (0 of 4 siblings is a scenario). The size of the promise decides in the
   near ring (a whole subject against one small thing). NO hit in the sample is framed as a trial, a court or a case - absent, which is not
   evidence against it. 26 titles are a method test, not a finding: nothing here becomes a rule; (a) and (b) agree with making "it happens to
   you" the default format and leave the trial an arm.
3. O - the vendor's own readings of the same pages (11 Nov 2026): the far channel's formula is "a second-person power-fantasy thought experiment"
   where the story "turns personal"; the science channel "breaks out when it turns science into either a highly relatable identity problem or a
   cinematic impossible scenario"; a narrator-led explainer with a strong premise and escalating consequences. A vendor's opinion.
4. E - Metricool 2026 through Tubefilter (3 Aug 2026) and Net Influencer: the average long video is watched 2.51 minutes (3.98 a year before);
   Retention Rabbit (10,000+ videos): more than 55% of viewers leave within the first minute. -> the opening and one idea, not more devices.
5. O - Virlo trend report (Oct 2026): hypothetical "what if" science scenarios are one of four themes standing out in science; small animated
   first-person what-if accounts reach very large averages on short video (another platform).
6. E - narrative perspective (a review citing Chen and others 2024, Kim and others 2017; text, not video): second-person narration draws
   stronger emotional responses than third person under high involvement. No study of "you" narration against YouTube retention was found.
#### Step 2 CREATIVITY (scores 1-5: what a viewer gains / enforceable / cost / reliability / owner effort)
A. Rewrite the show as "The day it changed" only and delete the trial: 4 / 3 / 2 / 2 / 5 = 16 - one template again (research 1), and the owner's
   own format with its tested code thrown away.
B. A "format" paragraph added to the prompts, the checks unchanged: 2 / 1 / 5 / 2 / 5 = 15 - the devices stay forced; the first script without
   them is held by six checks (a deliberate break showed exactly that).
C. A second pipeline for the new format (its own room, its own contract): 4 / 4 / 1 / 2 / 5 = 16 - two of everything to keep in step.
D. (ORIGINAL, CHOSEN) FORMATS AS DATA ON THE SWITCHES THE CODE ALREADY HAS + A THREE-TIER CONTRACT: a format is a row (does the trial layer run,
   its voices, its device table, its brief); the episode's format travels in the draw and is "the format in the making" for everything the
   production does; the contract runner judges a DEVICE by it and nothing else: 4 / 5 / 5 / 4 / 5 = 23.
#### Step 3 DESIGN MEMO
- An experiment first: with the trial layer switched off, a whole fake episode was held by exactly ONE check (`verdict_style`) - the code already
  had a show without a courtroom (two voices, no Show Plan). Formats are built on that, not beside it.
- NEW `whatifs/formats.py`: `FORMATS` - F1 "The day it changed" (the trial layer off; DIRECTOR + SKEPTIC; the trial's five devices not part of
  it, the other five optional), F2 "The trial" (today's show; every device required), F3 "The walk" (reserved, cannot be drawn yet).
  `pick`: FORMATS_ON off = as before formats; a Deep Trial is a trial; FORMAT_FORCE (or the env var WI_FORMAT) wins; an episode keeps its
  format; else the format furthest below its share among the last ten episodes (70 / 30 = 7 and 3 of ten, not a coin; the very first episode
  of a Sheet is drawn by its id). The format is picked once in `room.run_room`, kept in the draw, and `episode.produce` makes everything after
  the room in it (reset in its `finally`).
- THE THREE TIERS: `formats.DEVICES` are the ten device checks. A format says "must", "advisory" or "never" for each. `contract.run` writes N/A
  "not part of format F1" without judging, or judges and turns a failure into N/A "optional in format F1, not held: ...". Any other check is
  always "must" - a test proves that no viewer, organisation or core check can enter a format's table.
- THE WRITERS: the format's own brief reaches the Showrunner, the bible and the writer (`formats.block`), the blind juries rank by the format
  (`formats.rubric`), an optional device is not demanded (`enforce.writer_rules`) and never forced by a rewrite (`marker_issues`, `fix_markers`).
- A NEW HARD CHECK `format_kept` (script gate; owner D4; a promise about the show): a format that is not a trial does not sound like one - no
  name of the court's cast, no courtroom furniture, only its own voices; a trial has its Show Plan. The writers' one fix carries it.
- `show.on()` now means "the TRIAL layer runs for this episode"; `show.leads_on()` means "the show's world is on": the two leads keep their
  designed voices in every format, and packaging tests, the experiment row, the provenance record and the fixed cast belong to every format.
- Settings: FORMATS_ON, FORMAT_FORCE, FORMAT_SHARE_F1 70 / F2 30 / F3 0 (levers of D1, steps of 20). Money: no new call; an F1 episode makes
  fewer (no judge and witness voices, no tag fix).
#### Step 4 BUILD (what changed)
- NEW `whatifs/formats.py` (on `tools/repair.py` PROTECTED). `whatifs/show.py`: `leads_on`, `on`. `whatifs/room.py`: `run_room` picks and sets the
  format around `_run_room`; `_format_block` in three briefs; a non-trial format carries no Show Plan; `_pkg_extra` and the guest brief ask
  `leads_on`. `whatifs/room2.py`: `_rubric`. `whatifs/enforce.py`: optional devices; the format problem joins the one mandatory fix.
  `whatifs/contract.py`: the tiers in `run`; `p_format_kept` (53 hard checks: 34 script + 19 final). `whatifs/episode.py`: the format after the
  room and on a resume, reset at the end; designed voices, provenance, packaging pairs and the experiment row in every format. `whatifs/cast.py`.
  `whatifs/fakes.py`: the offline writer answers a non-trial format without the trial's devices. `whatifs/core.py`: 5 cells. `registry.py` /
  `levers.py` / `rnd.py`: the check's owner, 3 levers of D1 (51), SHOW_CHECKS 43. `tools/rehearsal.py`: the trial's own artefacts are asserted
  for a trial only, `format_kept` for every episode. `tests/conftest.py`: the older tests run in forced F2.
- Seeds: `v2a.formats_are_data`, `v2a.device_diet`, `v2a.hits_and_siblings`, `v2a.takeaway` (144 founding items).
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| An episode is made in ONE format from the room to the upload | `formats.pick` + `formats.using` in `room.run_room`; `formats.use` in `episode.py` | the room test (every call in F1), the production test (package, shot plan, Shorts plan in F1) |
| A device is judged by the format; nothing else is loosened | `formats.rule` in `contract.run` | the tier test; the production is held by six devices when the runner ignores the format |
| An optional device is not demanded and never forced | `enforce.writer_rules`, `marker_issues`, `fix_markers` | the writers' test (no rewrite call, no "MANDATORY" in the brief) |
| A script is what its format says | `formats.format_issues` in `enforce.fix_all` | `format_kept` (script gate) |
#### Step 6 PROVE
- `tests/test_v12_formats.py`: **10 tests** - the table (a format can touch devices only); the pick (forced, by id, by the shares over the last
  ten, an episode keeps its format, failed episodes do not count, no trial without the show's world, the env var); the trial layer follows the
  format and the context is always restored; optional devices and the format fix; the REAL room in F1 and in F2 (every call made in the
  episode's format, the three briefs handed over, no trial brief in F1); the tiers; `format_kept` both ways; wiring and levers; the REAL
  production in F1 (a missing device holds nothing, the trial's devices are not judged, every viewer check passes, packaging tests and the
  experiment row are written, no season row) and an F1 episode that sounds like a trial HELD before pictures.
- Fails correctly (five deliberate breaks, each reverted): the contract ignoring the format -> the tier test fails and the F1 production is
  held by `joke_density`, `send_and_awe`, `verdict_style`, `time_ladder`, `exhibits`, `grimm_prototype` ...; the trial layer ignoring the format
  -> 2 tests fail; the room not working in its format -> 2 tests fail; optional devices forced by a rewrite -> 1 test fails; production
  forgetting the format after the room -> NO test failed at first (found by the break itself) - the production test now watches the package,
  the shot plan and the Shorts plan, and fails.
- Faults found by running, not by reading: (1) THE REHEARSAL IN F1 failed while 10 tests and a whole F1 episode had passed: title and
  thumbnail tests, the experiment row, the provenance record and the fixed cast lived behind the trial switch and would have been silently lost
  in F1. Five call sites now ask `show.leads_on()`. (2) The offline Showrunner's Show Plan stayed in an F1 spine - a non-trial format now drops
  it. (3) My own test expected the wrong next format after failed episodes; the arithmetic was right, the test was corrected so that it tells
  the two cases apart.
- Tests changed by design: 51 levers, 34 script checks; the older tests are the trial's tests (forced F2 in the test setup).
- Fake rehearsal on the final code: GREEN in each format on the working tree (`WI_FORMAT=F1` and `WI_FORMAT=F2`); 4 of 4 GREEN in sweep C on the frozen copy (2 drew F1: 41 pass + 12 not applicable of 53 checks; 2 drew F2: 48 pass + 5 not applicable; no memo left open); GitHub's own rehearsal GREEN (episode EP202611111407, script 34/34, final 19/19).
- Full suite on a frozen copy of 75c55ea: **1302 passed / 0 failed / 1 skipped** (70 test files; the older tests in forced F2, the new file in F1 and F2).
- Sweep on the same frozen copy: **28 of 28 ok**, no bad id, no failure class. A: 20 ids, organisation on - 13 drew F1 (each 40 pass + 13 not applicable) and 7 drew F2 (47 pass + 6 not applicable). B: 4 ids, organisation off - 2 F1, 2 F2. C: 4 rehearsals - 2 F1, 2 F2.
- GitHub Checks (standing rule 1): run **91** on 75c55ea **GREEN**: 1303 passed (41:40), rehearsal GREEN (episode EP202611111407; contract script 34/34, final 19/19). Run 90 (the V1b record commit) GREEN.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (144 founding items), Organisation GREEN (11 wired, 5 pending), docs regenerated without drift.
- Money: Rs 0 spent (fake mode). In production: no new call.
#### Step 7 TAKEAWAY (also Palace item `v2a.takeaway`)
- WORKED: an experiment before the design (the trial layer off -> one check holds) sized the batch in ten seconds.
- WORKED: a full rehearsal per format, and breaking the code on purpose: the rehearsal found the lost packaging tests, the break found a step
  no test watched.
- FAILED / LIMIT: F1 has only been written by the offline test writers. Whether a real model keeps the courtroom out, uses two voices and
  builds the day from the bathroom to the planet is unknown until the pilot. The asks, the tease and the emotion beat are still inserted by
  code in F1 (they can no longer hold a video - open issue 74). The canon still hands the trial's cast to an F1 writer (77).
- NEW QUESTION: does F1 hold viewers better than F2 (H5)? The shares are data now, so the answer can move them (V4, B8).
- ORGANISATION: when one switch has meant two things, list every place that asks it and sort them before splitting it.

### V1b - THE LAYMAN TEST (11 Nov 2026) - ACCEPTED (final code commit 4c0e607 GREEN in GitHub Checks run 89: 1293 passed; sweep 28 of 28)
The owner (mobile only): "Continue". V1b as planned had four parts; it was SPLIT AT THE START (rule 6): this batch is THE LAYMAN TEST - it guards
the script before any picture is paid and answers his first complaint ("I was myself unable to understand the topic of video") and his item 19
("strict enforcement and checks for whether a layman audience also gets hooked and retained"). The judged floor and his verdict tab are V1c; his
input tab and the scoreboard go to V4.

#### Step 1 RESEARCH (E = measured, O = practice; "read" = read by the build session, else reported by a search run)
1. E read - Ohio State News, 12 Feb 2020 (Shulman and others, Journal of Language and Social Psychology; 650 adults; three topics):
   https://news.osu.edu/the-use-of-jargon-kills-peoples-interest-in-science-politics/ - expert words made readers less interested and feel
   less able; a definition on hover "didn't matter at all". Its own example pair is now a test.
2. E - Cruz and Lombrozo, Nature Human Behaviour 2025 (9 experiments, 6,698 people): expert words can FEEL satisfying while understood less.
3. E - van Zeeland and Schmitt, Applied Linguistics 2013; Nation 2006; a replication in Language Teaching (Cambridge): a listener needs to know
   about 95% of the running words for adequate and 98% for good comprehension. 2% of 150 words a minute = 3 unknown words a minute.
4. E - arXiv 2604.04583 (Apr 2026; 1,239 TED talks): explanatory CLARITY predicts likes and views and beats readability formulas.
5. E - arXiv 2508.19221 (Aug 2025): 6 of 8 readability formulas agree with human judgments below r = 0.3; the best language model 0.56.
   arXiv 2502.11150 (2025): formulas, systems and models are all poor predictors of reading ease. -> no formula and no model's "clarity
   score" is a gate here.
6. O - the five-second test of usability work (Center Centre / UIE; UXPA Journal, Nov 2016): show a page for five seconds, ask what it is for.
   -> the same question for the first 30 seconds of a video, with an answer code can check.
7. E - listening research (a review, through search): sentence length has a weak, inconsistent effect on listening. -> reported, never a gate.
Not found: a study of expert words against YouTube retention. The budgets are starting values and levers.
#### Step 2 CREATIVITY (scores 1-5: what a viewer gains / enforceable / cost / reliability / owner effort)
A. A readability formula as a gate: 1 / 5 / 5 / 1 / 5 = 17 (research 5: formulas do not agree with people).
B. A model plays "a 12-year-old" and scores clarity 1-10: 3 / 2 / 4 / 2 / 5 = 16 (taste as a gate; research 5 and the redesign's R9).
C. A glossary rule - every expert word defined at first use: 2 / 4 / 5 / 3 / 5 = 19 (research 1: a definition does not rescue it).
D. (ORIGINAL, CHOSEN) A BUDGET + A LINE-UP: code counts the expert words a layman would not know (per minute, in the opening, piled into one
   sentence) and the writers' one fix carries the problem; then THE PROMISE LINE-UP - two cheap readers of two model families see only the
   first 30 seconds and must pick this video's title out of four titles of our kind, or say "cannot tell"; a second, foreign opening is planted
   in the same call and must get "cannot tell", else the session is void: 4 / 5 / 5 / 4 / 5 = 23.
#### Step 3 DESIGN MEMO
- NEW `whatifs/org/layman.py` (D13). MEASURE: an expert word = a word code can RECOGNISE as expert vocabulary - on the expert list
  (`layman.EXPERT`, about 230 science terms) or built with an affix of scientific coinage ("electro-", "-ometer", "-osis" ...). A word on the
  everyday list (`whatifs/org/seed/everyday.txt`, about 1,400 words) is never counted; neither are names and the words of the title (the viewer
  chose them). The FIRST version counted every word of 7+ letters that was missing from the everyday list - wrong, see step 6. Budgets: DISTINCT unfamiliar words per minute (2; never fewer than 2 allowed in a video), in the first
  30 seconds (1), in one sentence (2). Sentence length is reported, not judged.
- REPAIR: the problem, with the words named, joins the writers' ONE mandatory fix (`enforce.fix_all`), as the numbers do; the house prompt of the
  writers' room now asks for everyday words.
- THE LINE-UP is D13's second run (`probe`), inside the plan stage right after the package, so its result is saved with the plan and a resume
  never pays it twice (a plan saved before V1b gets it at the next run). The readers are cheap on purpose: the right answer is known to code, so
  this is no taste call, and a weak reader is the harder test. The correct letter, the three other titles, the planted opening and the order of the
  two openings are chosen by the session id. Verdict by code: void when fewer than two families answered (a reader answered by another family is
  not counted) or a reader named a title for the planted opening; else PASS only when every reader picked our title.
- CHECKS at the script gate (before picture money): `viewer_plain`, `viewer_probe` (owner D13; promises about the show, `rnd.SHOW_CHECKS` 42).
  A void line-up never holds a video: the check steps aside and D13 reports its own machinery (closed by the next valid session).
- CHANGED FROM THE REDESIGN'S 10.6, with reasons: the planted canary is a FOREIGN opening, not "the same opening flooded with expert words" - a
  model reads expert words easily, so that canary would never fail and every session would be void; the vocabulary is judged by code instead.
  "None in the first 30 seconds" starts as "at most 1": the recognition is ours and imperfect, and a false hold costs an owner tap.
- Money: two small calls a video (about Rs 0.2).
#### Step 4 BUILD (what changed)
- NEW `whatifs/org/layman.py` (on `tools/repair.py` PROTECTED): `on`, `everyday`, `unfamiliar`, `hard_words`, `plain_report`, `promise_words`,
  `plain_issues`, `lineup`, `probe`, `probe_run`. NEW `whatifs/org/seed/everyday.txt`.
- `whatifs/contract.py`: `p_viewer_plain`, `p_viewer_probe` (52 hard checks: 33 script + 19 final). `whatifs/episode.py`: `_probe` (D13's `probe`
  run) at the end of the plan stage and, for an older plan, right after the seat; the script gate's context carries the line-up.
  `whatifs/enforce.py`: the expert words join the one mandatory fix. `whatifs/prompts.py`: three lines in the house rules. `whatifs/models.py`:
  two reader roles. `whatifs/fakes.py`: the offline reader. `whatifs/org/registry.py` / `levers.py` / `rnd.py`: D13's second run in both gates'
  run lists, 2 check owners, 3 levers (48), SHOW_CHECKS 42. `whatifs/core.py`: 6 cells.
- Seeds: `v1b.expert_words`, `v1b.promise_lineup`, `v1b.takeaway` (140 founding items).
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| Few expert words: per minute, in the first 30 s, in one sentence | `layman.plain_issues` in `enforce.fix_all` (the one fix) | `viewer_plain` (script gate) |
| The first 30 s say what the video is about | `layman.probe` in D13's `probe` run (`episode._probe`) | `viewer_probe` (script gate) |
| D13's line-up ran before either gate | `runner.work("D13", "probe")` in `episode.py` | `dept_contract` holds the video; `python -m whatifs.org.runner` RED |
| A line-up whose readers guess is not believed | the planted opening + the family check in `layman.probe` | status void -> the check steps aside, D13's problem memo |
#### Step 6 PROVE
- `tests/test_v12_layman.py`: **9 tests**, each rule both ways (expert words by list and by affix; everyday words that are built like expert words; the four ordinary words of the sweep; the study's own
  sentence pinned as a stated limit; names, headings and the title's words not counted;
  the flood, the opening, the pile in one sentence, each lever; the writers' one fix; the line-up deterministic per session with the place of our
  title and the order of the openings moving, no planted opening sharing a word with any title; pass / fail / off; a reader that always names a
  title, a reader answered by the wrong family, unreadable letters -> void; the void report written and closed by the next valid session through
  the real runner; wiring and levers; the REAL production: a good fake episode passes both checks with both D13 runs proven, and an episode a
  layman cannot follow is HELD on both checks before any picture is paid).
- Fails correctly (mutations on the real repo, each reverted): D13's line-up run removed -> the organisation check is RED ("no runner call for
  D13 'probe'"), the wiring test fails and the production is held at the script gate by `dept_contract`; the gate made blind to the line-up ->
  the production test fails on `viewer_probe`; the expert words taken out of the writers' fix -> its test fails.
- Faults found by running, not by reading: (1) the department contract refused D13's second line-up - its own void report was in its inbox and
  the run had said nothing about it; a run that returns `Out` must act on every inbound memo (fixed: `memo_actions`). (2) THE SWEEP FOUND WHAT THE SUITE DID NOT. On the first frozen copy (ebceee5) the full suite passed (1292 passed / 0 failed / 1 skipped) and
  the sweep held 1 of 20 episodes (EP209901220428) at `viewer_plain` for "observe, session, coastline, precious" - four ORDINARY words. Traced, not
  re-run: the measure counted every long word missing from a hand-made list. A first sign had been "collide" in a unit test; I answered it by
  widening the list - the wrong repair. Fixed at the cause (4c0e607): only words code can recognise as expert count; the four words are a
  regression test; every word the offline writers can produce was scanned with the new measure (one everyday word found and exempted).
- Tests changed by design: 48 levers, 33 script checks, 6 department runs before the script gate (three assertions), D13's two runs in the seat
  test; the paid-call counter allows the two reader calls (`tests/paid_calls.py` V12V1B_ADDED).
- Fake rehearsal on the final code: 4 of 4 GREEN in sweep C on the frozen copy of 4c0e607 (each 47 pass + 5 not applicable of 52 checks, 11 department runs, no memo left open); GitHub's own rehearsal GREEN (episode EP202611111159, script 33/33, final 19/19).
- Full suite on a frozen copy of 4c0e607: **1292 passed / 0 failed / 1 skipped** (69 test files). The first frozen copy (ebceee5, before the correction) had the same total - the suite did not see the fault the sweep found.
- Sweep on the same frozen copy: on 4c0e607 **28 of 28 ok**, no bad id, no failure class (A: 20 ids, organisation on, each 46 pass + 6 not applicable; B: 4 ids, organisation off; C: 4 rehearsals). On the first frozen copy (ebceee5): 27 of 28 - EP209901220428 held at `viewer_plain` for four ordinary words; traced and fixed at the cause (above), never re-run on the old code.
- GitHub Checks (standing rule 1): run **89** on 4c0e607 **GREEN**: 1293 passed (42:04), rehearsal GREEN (episode EP202611111159; contract script 33/33, final 19/19). Run 88 on ebceee5 was GREEN too - GitHub runs no sweep, so the fault was found only on the laptop. Runs 86 and 87 (the V1a record and the item-19 design commit) GREEN.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (140 founding items), Organisation GREEN (11 wired, 5 pending), docs regenerated without drift.
- Money: Rs 0 spent (fake mode). In production: two small calls a video, about Rs 0.2 (logged by `models.ask`, counted by the paid-call
  counter; not yet its own line in the estimate - open issue 72).
#### Step 7 TAKEAWAY (also Palace item `v1b.takeaway`)
- WORKED: the V1a pattern again (measure -> the writers' one fix -> check -> lever) and a verdict computed by code from letters.
- WORKED: asking what the planted canary would do against the reader we really have. The designed canary could never have failed; found at the
  design step, not after a week of void sessions.
- WORKED: the sweep (standing rule 2). Nine new tests, a full fake production and a green full suite did not show that one episode in twenty
  would be held for ordinary words. A check that can hold a video is believed only after many different episodes ran under it.
- FAILED: my first measure flagged what it did not KNOW instead of what it could recognise as wrong, and my first repair of the first sign was
  to widen a list. A gate that holds a video must be built for precision; what it misses is the price.
- LIMIT: the readers are models, not laymen. The line-up proves that the first 30 seconds NAME what the video is about among unrelated titles;
  it does not prove a person is hooked, and it cannot yet tell "names the subject" from "makes the promise" (open issue 69). The recognition
  misses engineering and business words - the study's own example sentence passes it (68). No real script has been through it.
- NEW QUESTION: do scripts inside the budget hold viewers longer (H8)? Only real retention can say (B8).
- ORGANISATION: a department's report about itself returns to its own inbox - every run that returns `Out` needs `memo_actions` for all of it.

### V1a - THE VIEWER'S SEAT, measured (11 Nov 2026) - ACCEPTED (final code commit f96b87a GREEN in GitHub Checks run 85: 1284 passed; sweep 28 of 28)
The owner (mobile only, 11 Nov): "Pls do the changes yourself and begin building". Built in the same session as the redesign because he could not
open a new one. V1 split at its start: this half is what code can MEASURE and REPAIR BY ITSELF; the judged floor, the owner's tabs and the
scoreboard are V1b.

#### Step 1 RESEARCH (dated sources; E = measured, O = opinion / practice; the redesign's R1-R14 of the same day are in BREAKOUT_REDESIGN.md)
1. E - Shrestha et al., arXiv 2606.07541 (1 May 2026, abstract read): multimodal models as synthetic viewers show "limited agreement" with 673
   human ratings, squeezed toward the middle. -> what a viewer meets is measured by code where it can be; no model's taste is a gate in V1a.
2. E - Maiorano, arXiv 2609.25010 v2 (3 Nov 2026, abstract read): a ten-persona panel ranked worse than one generic reader (tau gap +0.22 / +0.26).
3. E - Mayer, research-based principles for multimedia instruction (copy hosted June 2023, read through search): coherence - deleting material
   the point does not need - positive in 18 of 19 tests, median effect 0.86; signaling 0.70; captions added to narrated graphics only 0.10.
   Measured on learning, not on watch time. -> numbers are a budget; burned-in captions for a whole long video are NOT forced (open issue 59).
4. E - Murphy et al., Applied Cognitive Psychology 2021 (through search): narration sits near 150 words a minute; comprehension holds until
   about twice that. -> pace is measured and logged, not gated.
5. O/E - YouTube Help (2026), answer 16559650 and 9314415: the initial seconds decide; the Intro metric is the share still watching at 30 s;
   align title and thumbnail with the content. -> the promise is the first picture.
6. E (ours) - the rejected video: 6 pauses in 793 s, 7+ full-screen number cards (2 in the first 50 s), the promise never shown in 12 s, 13:13.
7. Not found: a controlled study of pause frequency or of number density against retention. The three budgets are STARTING VALUES (levers).
#### Step 2 CREATIVITY (4 designs; scores 1-5: what a viewer gains / enforceable / cost / reliability / owner effort)
A. A model "viewer" judges the script for clarity and voice: 3 / 2 / 3 / 2 / 5 = 15 (research 1-2: weak, squeezed; taste as a gate).
B. More script checks of the old kind (must contain X): 1 / 5 / 5 / 4 / 5 = 20 - but adds devices, the disease itself.
C. Measures only, hold on failure: 3 / 5 / 5 / 4 / 3 = 20 - every hold is an owner card.
D. (ORIGINAL, CHOSEN) MEASURE -> REPAIR BY CODE -> CHECK -> LEVER: code measures what the viewer meets, repairs by itself what code can repair
   (the first shot, number graphics, pauses), gives the writers' one existing fix the rest (numbers heard), and only then holds:
   5 / 5 / 5 / 4 / 5 = 24. The budgets are levers of the new department, so the learning loop can move them.
#### Step 3 DESIGN MEMO
- D13 Audience = `whatifs/org/audience.py`, pure functions. One run per episode (`seat`) right before the Animation Director: `shape` makes the
  first shot a made picture (its prompt = the thumbnail's scene), turns number graphics before GRAPHICS_FREE_SEC or above GRAPHICS_MAX_LONG into
  stills (a reused picture, or a fresh still under Rs 1). The Animation Director's first anchor (0.0) then lands on shot 0 and `room.promise_shot` re-aims
  it: the promise is on screen at 0 s. PROMISE_BY_SEC 30 -> 5.
- `breathe` runs inside `voice.narrate`: a 0.7 s pause at a sentence start when the voice has run about 30 s without one (a paragraph start
  from half the window, any sentence from 80%); the writer's own pauses count. Judged on the REAL timeline with 25% slack.
- `count_numbers` counts QUANTITIES heard (a figure, a number word, or a run = one). Not counted: headings, a source's year, a place in the
  story ("hour 1", "Exhibit 2") - found when the first fake production was held by its own required devices (open issue 60).
- Three script-gate checks (before picture money): `viewer_promise`, `viewer_breath`, `viewer_numbers`; owner D13; promises about the show
  (`rnd.SHOW_CHECKS` 40). The gate's context now carries the shot list, the voice timeline and the package.
- Long videos 9:00 at most (RUNTIME_MAX_SEC 600 -> 540). Both changed defaults move once on a live Sheet (`manage.v12v1_upgrade`).
- NOT in V1a, on purpose: a loudness-range gate (narration normally has a small range; the wish was pauses), burned-in captions for long videos
  (weak evidence; V2 with the hook), the Shorts track (V2 rebuilds it), any judged test (V1b). The voice MODEL needed no change: `pick_tts`
  already takes the newest stable Flash voice, which is the best-ranked voice inside the owner's Google account today.
- Money: no model call is added. A number graphic that goes becomes a picture: a reused one, or a fresh still (under Rs 1) where the opening or
  the repetition guard wants one - 2 in the fake episode, a few rupees a video at most (open issue 66).
#### Step 4 BUILD (what changed)
- NEW `whatifs/org/audience.py` (D13; on `tools/repair.py` PROTECTED): `on`, `spoken`, `count_numbers`, `numbers_report`, `number_issues`, `shape`,
  `m_shape`, `breathe`, `breath_report`. `whatifs/org/__init__.py` + `registry.py`: department D13 (16 departments, 11 wired), its entry
  (`whatifs/episode.py`, `seat`), `EPISODE_RUNS` (both gates need D13's run), the owners of the 3 checks, 4 levers. `levers.py`: 4 rules
  (45 levers; every loosening needs the owner) and `viewer_promise` judges PROMISE_BY_SEC.
- `whatifs/contract.py`: `p_viewer_promise`, `p_viewer_breath`, `p_viewer_numbers` (50 hard checks: 31 script + 19 final). `whatifs/episode.py`: D13's
  run before `ANIM.apply`; the script gate sees shots, units, package. `whatifs/voice.py`: `breathe` after `parse_script`. `whatifs/enforce.py`:
  the numbers problem joins the ONE mandatory fix. `whatifs/prompts.py`: the Director is told graphics are rare, never first, never in the
  first minute. `whatifs/core.py`: 8 cells, 2 changed defaults. `whatifs/manage.py`: `v12v1_upgrade` at both upgrade sites.
- Seeds: `v1.viewer_seat` (a limit for D13), `v1.numbers_are_load`, `v1.floor_not_forecast`, `v1.takeaway` (137 founding items).
#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executed by | Fails when broken |
|---|---|---|
| The video opens on a made picture carrying the animated promise, on screen within 5 s | `audience.shape` -> `anim.pick_slots` -> `room.promise_shot` | `viewer_promise` (script gate), `promise_paid` (final gate) |
| The voice pauses at least every 30 s | `audience.breathe` inside `voice.narrate` | `viewer_breath` on the real timeline |
| Few numbers heard; few number graphics, none in the first minute | `enforce.fix_all` (numbers), `audience.shape` (graphics) | `viewer_numbers` |
| D13 ran before either gate | `runner.work("D13", "seat")` in `episode.py` | `dept_contract`; `python -m whatifs.org.runner` RED when the call is gone |
| A long video is at most 9:00 | RUNTIME_MAX_SEC 540 in `governor.plan_for_episode` | moved once by `v12v1_upgrade` (tested) |
#### Step 6 PROVE
- `tests/test_v12_seat.py`: **11 tests**, each rule both ways (numbers counted as heard; the flood and the graphics budget; the writers' one fix;
  the shot list shaped and unchanged when shaped twice; the promise first / late / lost / no animation; pauses placed at sentence starts and the
  writer's own pauses counted; the real timeline judged; the REAL voice job; wiring and levers; the one-time move; the REAL production: a good
  fake episode passes all three checks with D13's run proven, a number flood is HELD before any picture is paid).
- Fails correctly (mutations on the real repo, each reverted): D13's run and the voice call removed -> **3 tests fail** and the organisation
  check is RED ("no runner call for D13 'seat'"); shaping switched off inside the function and the gate's view of the shot list removed ->
  **3 tests fail** (shape, promise, the real production).
- A fault found by running, not by reading: the FIRST fake production was held by `viewer_numbers` - the counter counted "## BEAT 3" headings,
  the years of sources and the time ladder's "hour 1". Fixed in the counter (quantities, not story marks), with a test.
- My own mistake in this session: I pasted a patch with backslashes through a shell here-document (the known pitfall) and broke two lines in
  two files; found at once by the syntax error, repaired with the file tools.
- Tests changed by design: 5 count assertions before the suite (16 departments, 16 playbooks, 45 levers, 31 script checks, the runtime test) and
  4 tests the full suite found (the promise at 12 s is late now; 5 department runs before the script gate, three assertions in two tests; the
  two changed defaults are a documented one-time move in the v9 upgrade test). The commit message of f96b87a says "5 older tests": the exact
  count is 4 tests by design + 2 tests showing the one real finding = the 6 failures.
- A REAL finding of the full suite (2 tests: default flags, all flags on): the paid-call counter showed 26 images against a baseline of 24. A number graphic turned into a picture is
  not always free - where the opening or the repetition guard wants a fresh picture it is a paid still. I had written "free" in the code, the
  settings, the matrix and a founding item; corrected to "by code" everywhere and documented in the counter (`tests/paid_calls.py` V12V1_ADDED).
- Fake rehearsal on the final code: GREEN on the working tree (50 checks: 45 pass, 5 not applicable; D13's run present; 2 pauses placed, 2 early number graphics turned into pictures); 4 of 4 GREEN in sweep C on the frozen copy of f96b87a; GitHub's own rehearsal GREEN (episode EP202611110803, script 31/31, final 19/19).
- Full suite on a frozen copy of f96b87a: the whole suite ran on the laptop on b0fd0d8 (before the corrections): **1277 passed / 6 failed / 1 skipped** - all six traced (4 tests whose expectation moves by design, 2 tests showing the one real cost finding) and corrected in f96b87a. On the frozen copy of f96b87a the 9 touched or failing files were re-run: **312 passed / 0 failed** (test_v11_breakout 7, test_v12_org 99, test_v91_e2e 2, test_v91_matrix 33, test_v91_paidcalls 1, test_v12_seat 11, test_v12_palace 39, test_v12_exec 88, test_v82 32). The whole suite on f96b87a ran on GitHub (below): 1284 passed. NOT done: the whole suite a second time on the laptop on the final code.
- Sweep on the same frozen copy: **28 of 28 ok**, no bad id, no failure class. A: 20 fixed episode ids, organisation on - 20 ok. B: 4 ids, organisation off - 4 ok. C: 4 rehearsals, organisation on - 4 ok, each 45 pass + 5 not applicable of 50 checks, 10 department runs, no memo left open.
- GitHub Checks (standing rule 1): run **85** on f96b87a **GREEN**: 1284 passed (21:36), rehearsal GREEN (episode EP202611110803; contract script 31/31, final 19/19). Runs 83 (b0fd0d8) and 84 (6bfb02d) RED: 6 failed / 1278 passed - the same six tests the laptop found, traced (above) and corrected in f96b87a; not re-run.
- Plan Guard GREEN, Truth GREEN, Palace GREEN (137 founding items), Organisation GREEN (11 wired, 5 pending), docs regenerated without drift.
- Money: Rs 0 spent (fake mode). In production: no new model call; up to a few more stills in a long video (under Rs 1 each).
#### Step 7 TAKEAWAY (also Palace item `v1.takeaway`)
- WORKED: measure -> repair by code -> check -> lever. The viewer's rules cost almost nothing and the gate rarely has to hold, because code
  repairs first.
- WORKED: the old paid-call counter. It caught my "free" claim: two stills more. A cost claim is believed only when the counter agrees.
- WORKED: running the real production in a test. It found in one run what reading had not: the show's own required devices fill a script with
  numbers. A rule about the viewer must be tried on a whole episode before it is believed.
- FAILED / LIMIT: nothing here proves a viewer will ENJOY the video. V1a removes three measured faults of the rejected video (the promise not
  shown, a voice without pauses, a flood of numbers) and its length. Whether the voice is pleasant and the story clear is not measured yet (V1b's
  floor, then real viewers). No real video has been made by this code.
- NEW QUESTION: are 4 numbers a minute, 3 number graphics and a pause every 30 s the right values? They are levers; B8 must score them against
  real retention (hypotheses H2-H3 of the redesign).
- ORGANISATION: a new department needs founding knowledge before its first run (the runner refuses a department without a playbook) - seeds
  first, then the wiring.

### B5 RECHECK (11 Nov 2026; owner: "make a recheck of the B5 done and also any of its consequent impacts and correct them, if any") - DONE (final code commit 101cf96 GREEN in GitHub run 78; laptop suite 1272 / 0 / 1 skipped; rehearsal GREEN; sweep 7 of 7 green)
Not a batch (no new feature): the accepted B5 code was re-read line by line (`rnd.py`, `board.py`, the model doorway, the runner, the governor, the
job dispatcher) and then every place it touches something else (the learning job, the production job and its script gate, the month's money, the
watchdog's clocks, the checks B6a added later). 16 things were wrong or fragile; each is fixed and each code fix has a test that fails without it.

FOUND AND FIXED - would have hurt in production:
1. A JSON syntax repair hid who answered (`models.haiku_repair` -> `_claude` overwrote `last_call()`): after a repaired reply R&D saw NO search
   results, so every source became a phantom and the paid answer was thrown away; a Board judge was discarded as "a cheap model". Now the repair
   keeps the note of the call it repairs and adds its own cost.
2. A cheap model could sit on the Board: `_gemini` silently answers with the Flash model when no Pro model is known, and recorded the call as
   `gem_pro`. It now records the role that REALLY answered, so the Board's "strong models only" rule holds.
3. The Board's "session void" memo could never close in production: nobody acknowledges a memo to itself within 2 hours, the watchdog takes it up
   the ladder, and the next valid session looked for it only in its inbox - an owner message that stays open for ever. A valid session now closes
   it wherever it is (`memos.find`).
4. A video could be HELD for research any job can run: `research_cadence` is judged at the script gate, but only the daily learning job ran the
   round. Two dropped learning jobs (GitHub cron drops runs - the pipeline's own comment says so) or switching the organisation back on after days
   = hold + owner click. `cli.research_catch_up`: a production job that would meet a stale round (within 8 hours of the limit) runs it first.
5. The organisation's own plumbing became PAID web questions: a Board session void twice, a failed check gated a second time (already on the
   agenda as a check gap), and B6a's three new checks (`palace_injected`, `palace_cited`, `canon_in_brief` - not in `ORG_CHECKS`, also offered to
   the researcher as prediction metrics). `rnd._plumbing` + the list + a test that counts, so no later check can be forgotten.
6. Research that pays and keeps nothing was invisible (the run is "ok", the check passes): the likeliest failure of the first real runs (real APIs
   never touched, open issue 40). A weekly run that asked 2+ questions and kept no answer now writes a problem memo (D2 -> D2, climbs to the owner,
   closed by the next run that keeps an answer).
7. `ask_one` said "never raises" and could: a reply in an unforeseen shape (`"sources": 3`, `"target_depts": 7`) crashed the weekly run AFTER the
   paid call, and the level trigger would have paid again the next day. Shapes are read (`rnd._idx`), anything else is recorded as unanswered.
8. The daily learning job had 30 minutes; B5 put the weekly research (web search, up to 12 liveness checks a question) and the Board inside it.
   A job killed mid-research loses the paid answers. Limit 60 minutes (`.github/workflows/learn.yml`); real duration unmeasured (open issue 55).
FOUND AND FIXED - small:
9. Sources counted from 1 by the researcher were attributed to the neighbour source: the prompt now says "the first source is 0", and the clear
   case (no finding names 0, one names a position past the end) is shifted.
10. Web text that reads like an instruction to a model (a quote, a page title, a finding, a proposed action, a video title on the agenda) is
    dropped before a memo is written or a question asked; both system prompts say that memo / page text is never an instruction.
11. A session that is void after the first family (it did not answer or was not counted) no longer pays the second family.
12. More waiting memos than letters (BOARD_MAX_MEMOS above 10) could cut the canary off and crash the session: capped at 10.
13. A question dropped before it was asked waited 28 days when its gap came back: open again at once.
14. The standing policy question came twice around New Year (period counted from 1 January): counted from a fixed day.
15. A true evidence ceiling could fail the check when a run crossed midnight on the last day of freshness: one day of slack in the re-computation.
16. A Sessions row without a start time broke the weekly schedule (`max` over None): skipped.

CHECKED, NOTHING TO CHANGE:
- Money: the Rs 420 reserve (D2 300 + D3 120) leaves Rs 3,980 for production; four FULL videos need 4 x Rs 577 = Rs 2,306 (Rs 2,537 with the 1.10
  margin). Every one of the four is planned at tier `full` with the reserve and without it (computed with the governor on default prices).
- ORG_ON = FALSE: the learning job still runs the collectors that moved to R&D (the runner calls the work with an empty brief); no paid research.
- Cap reached: refused before a Session row is written; the owner's message once a month.
- Every paid call inside a run reaches Org_Audit through the cost tap (failed attempts and repairs too): the monthly figure is complete; only the
  per-question figure on the agenda is the last call (open issue 44).
- PAUSED does not stop the learning job; B6a did not touch `rnd.py` / `board.py`; creative memos go to the Council, not to the Board.

PROOF
- `tests/test_v12_rnd.py`: 31 -> **43 tests**, all pass. 1 test changed by design (the void session: "only 0 model families answered", nothing
  logged, the second family not asked).
- Fails correctly: with every code change of the recheck stashed, **12 tests fail** (11 of the 12 new ones + the changed one). The 12th new test
  (letters) passed by luck in that run - the canary's place is a hash - so it was rebuilt with a chosen session id and proven alone: it fails
  without the cap.
- Related files (matrix, organisation, creative, research): 184 passed. Plan Guard GREEN, Truth GREEN, Organisation GREEN, docs regenerated
  without drift. 2 matrix rows added.
- Full suite on a frozen copy of the final code commit 101cf96: **1272 passed / 0 failed / 1 skipped** (67 files, one uninterrupted run by itself; the skip is the dashboard render, which needs node - GitHub runs it: 1273)
- Fake rehearsal on the same copy: **GREEN** (47 checks; the research round inside it: 4 research memos -> policy: accept, technique: test, tool: accept, technique: test; canary rejected by both families; `research_cadence` PASS)
- Sweep on the same copy (the changes sit in research, the Board, the model doorway and the job dispatcher, not in the episode pipeline: a short
  sweep as after B4's late commits): A: 4 fixed ids, organisation ON: **4 ok** (status SCHEDULED, 41 PASS + 6 N/A, 9 department runs verified, 0 owner messages, 0 degraded steps); B: 1 id with ORG_ON = FALSE: **1 ok** (35 PASS + 12 N/A); C: 2 full rehearsals with a forced id: **2 ok** (status LIVE, 42 PASS + 5 N/A). **7 of 7 green.** The rehearsals' 'similar script' warnings are about the table-read episode and the preview draft (fake scripts are alike), not an episode against itself - B6a's fix of issue 47 holds. One owner-message kind that the B5 sweep did not list, `scout_price` (the weekly tool scout's price update, digest tier; `scout.py` untouched since B4): a time-based weekly job, not traced further.
- GitHub Checks (standing rule 1): GitHub run 78 (101cf96, the final code commit): **GREEN - 1273 passed, 0 skipped, rehearsal GREEN (episode id EP202611110421, script 28 / 28, final 19 / 19)**. Run 77 (2f7553e: all code fixes, before the workflow limit was raised): GREEN. Both read on the public run pages.
- My own mistake in this session: the first suite run finished in two minutes with no result (I left out `PY=`; the laptop's own python has no
  `requests`). Nothing was tested by it; it was started again with the venv python.
- Money: Rs 0 spent (fake mode). Nothing new is paid for; fix 11 saves two judge calls in a void session, fix 4 can move the weekly round's
  cost (inside the D2 / D3 caps) into a production job.

### B6a - Creative departments D4/D5/D6/D7 (11 Nov 2026) - ACCEPTED (final code commit 45ca227 GREEN in GitHub run 75; sweep 40 of 40 green)
#### Step 1 RESEARCH (13 sources, 12 of them dated; E = measured evidence, O = opinion / practice / vendor documentation)
1. E - Wallat, Heuss, de Rijke, Anand, "Correctness is not Faithfulness in RAG Attributions", arXiv 2412.18004 (Dec 2024; ICTIR 2025),
   https://arxiv.org/abs/2412.18004 : a citation can be CORRECT (the source supports the claim) while the model never used it ("post-rationalised");
   up to 57% of citations unfaithful in their adversarial tests (Command-R+). -> a self-reported `applied_items` list proves nothing by itself.
2. E - Saxena et al., "Generation-Time vs. Post-hoc Citation", arXiv 2509.21557 (Sep 2025; NeurIPS 2025 workshop), https://arxiv.org/abs/2509.21557 :
   citing while generating (G-Cite) wins on precision, citing afterwards (P-Cite) on coverage; the quality of what was retrieved drives attribution
   quality in both. -> cite at generation time (precision) AND check afterwards by code (coverage); keep the injected block small and relevant.
3. O (vendor) - Anthropic, "Introducing Citations on the Anthropic API" (23 Jan 2025), https://www.anthropic.com/news/introducing-citations-api :
   citations point at quoted spans of the given documents, which code can match back; internal evals: up to 15% better recall than custom
   prompting. -> a citation should carry a QUOTE that code can find, not only an id.
4. E - Liu et al., "Lost in the Middle", TACL 12 (2024) 157-173, https://aclanthology.org/2024.tacl-1.9/ : U-shaped accuracy - information at the
   start or end of the context is used, in the middle it is lost. -> the playbook and the canon go at the START (cached system layer), not mid-brief.
5. E - Hong, Troynikov, Huber (Chroma), "Context Rot" (14 Jul 2025), https://research.trychroma.com/context-rot : 18 models get less reliable as
   input grows, and distractors hurt more as length grows. -> bounded blocks; canon filtered to what is relevant for THIS case, not the whole bible.
6. E - "How Many Instructions Can LLMs Follow at Once?" (IFScale), arXiv 2507.11538 (Jul 2025; NeurIPS 2025), https://arxiv.org/abs/2507.11538 :
   the best frontier models reach about 68% at 500 simultaneous instructions; earlier instructions are favoured. -> caps on playbook size stay; limits first.
7. E - Li et al., "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs", arXiv 2402.10962 (Feb 2024; COLM 2024),
   https://arxiv.org/abs/2402.10962 : significant persona drift within 8 rounds. -> character canon must be re-stated in EVERY creative call of the
   run (the tap re-injects per call), not once at the top of a long chain.
8. E - ConStory-Bench, arXiv 2603.05890 (Mar 2026; ACL Findings 2026), https://arxiv.org/abs/2603.05890 : in long generated stories consistency
   errors are most common in FACTUAL and TEMPORAL dimensions, mostly mid-narrative; an automated checker grounds each judgment in explicit text.
   -> canon items must be concrete facts (who won, which prototype number, what was promised next) so code can check them.
9. E - "Finding Flawed Fictions" (FlawedFictions), arXiv 2504.11900 (Apr 2025; COLM 2025), https://arxiv.org/abs/2504.11900 :
   LLM-written stories carry 50-100% more plot holes than human originals; detection gets worse with length. -> continuity must be kept by code
   records, not trusted to the model's memory.
10. E - Park et al., "Generative Agents", UIST 2023, arXiv 2304.03442, https://arxiv.org/abs/2304.03442 : ablations - observation (memory),
    reflection and planning EACH contribute critically to believability. -> an episode record (memory) + a distilled canon line (reflection) both.
11. E - Doshi & Hauser, "Generative AI enhances individual creativity but reduces the collective diversity of novel content", Science Advances
    10(28), 12 Jul 2024, https://doi.org/10.1126/sciadv.adn5290 : AI ideas made single stories better but the set MORE ALIKE. -> creative memos must
    be checked for sameness against earlier ones by code; the Council (B6b) must see diverse options, not 10 copies.
12. E (survey) - University of Essex, parasocial study (23 May 2024), https://www.essex.ac.uk/news/2024/05/23/watching-youtube-cheers-people-up-more-than-meeting-casual-friends :
    52% of 1,080+ participants report a strong parasocial relationship with a YouTuber; classic TV research: bonds grow with REPEATED exposure and
    self-address. Backed by our own 9 Nov concept research (04 digest: winners share recurring characters and lore). -> canon is a breakout lever.
13. O (practice) - Final Draft, "10 Easy Steps to Developing Your TV Show Bible" (blog, undated),
    https://www.finaldraft.com/blog/10-easy-steps-to-developing-your-tv-show-bible , and Fiveable "running gags" (TV studies glossary): the bible is the
    archival record every incoming writer reads; running gags come back across the series and change a little each time (too much change and the
    audience stops recognising them). -> the canon keeps each gag's history; the brief asks for a VARIATION, never a repeat.
Plus official pricing: Anthropic prompt caching (docs, read 11 Nov 2026), https://platform.claude.com/docs/en/build-with-claude/prompt-caching :
cache reads 0.1x input (0.05x / 0.025x on the newest models), writes 1.25x -> a playbook in the cached system layer costs almost nothing per call.
Owner's words re-read for B6a: 02 #2 ("the writer room also should learn from researcher and R&D to enhance their performance everytime"), #6 (every
output a BREAKOUT), #8 (personify, attachment, characters to love), #12/#14/#15 (hard-enforced to the line, executed at code level), B (characters to
fall in love with, return factor, no slop, no repetition).

What the code does TODAY (read before designing, 11 Nov): all 15 departments run in "brief" mode - the playbook is "handed over" (`brief.take()`)
but `room.run_room`, `room.package` and `room.plan_shots` never read it, so NO Palace knowledge reaches any creative model call; and with
PREPROD_ON = TRUE (the default) the script is written in pre-production by `preview.run` OUTSIDE any department run, so production's D4 run only
adopts a finished draft. No world_canon item exists (0 of 126 founding items). The runner's prompt mode (the tap in `models.ask` puts the playbook
into the cached system layer and counts the calls) exists since B3 but no department uses it.

#### Step 2 CREATIVITY (6 designs + 1 parked; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A. Paste the playbook into the writer brief by hand; models list the ids they used; checks count the ids. 2/1/5/3/5. Rejected: a self-reported
  list proves nothing (research 1: up to 57% post-rationalised), and it reaches one call of one department.
- B. ONE DOORWAY IN, ONE DOORWAY OUT, QUOTE-ANCHORED CITATIONS: D4/D5/D6 switch to prompt mode for their NAMED creative calls (D4: scout,
  showrunner, bible, writer, rewrite, punchup, memo; D5: packager; D6: director) - never the judges, never the mechanical passes; the playbook sits at
  the START of the cached system layer (research 4, official caching price). A new reply tap at the same doorway collects every reply's
  `applied_items` [{id, where}] and strips it before the caller sees it. Code verifies each citation: the id was in the injected playbook, and the
  `where` quote (4-30 words) is found in the run's FINAL output (tolerant match: exact, or 80% of its words in order inside a short window). Only
  verified citations count as applied (applied_count, later D10 outcome attribution); limits are not citable (they always apply). 4/5/4/4/5.
- C. Post-hoc citation pass: after the run a model maps output lines to playbook items. 3/3/3/3/5. Rejected: one extra paid call per run; the mapper
  can rationalise the same way (research 1, 2); a cheap mapper would be a cheap model judging (rule 9).
- D. Canon as its own block (`canon.py` text pasted into the writer brief). 3/3/5/3/5. Rejected: a second doorway and a second id space; showrunner,
  bible, packager and director would each need it pasted by hand. Canon becomes Palace items (kind world_canon) in a RESERVED CANON LANE of the same
  playbook instead (limits, then canon, then proven > accepted > testing), bounded by PALACE_CANON_SHARE.
- E. ORIGINAL - CONTINUITY DEBTS: the canon is a ledger WRITTEN BY CODE from the show's own records after every D4 write (case, charge, verdict
  winner + style + deciding detail, witness twist, Grimm's prototype, the stinger's promise of the next case) - concrete factual / temporal facts, the
  kind long stories get wrong (research 8, 9). A case record becomes canon only when the platform confirms the upload ("what aired"; D9 holds the
  video id - the only status move D9 may make). The newest aired case is a MUST-CITE item for D4: the script must call back to it in at least one
  line that code finds IN THE SCRIPT (not in the notes). Repeated exposure is what builds attachment (research 12, 13) - enforced at line level and
  verified like any citation, at zero extra cost. 5/5/5/4/5.
- F. ORIGINAL - SAME-IDEA GUARD ON CREATIVE MEMOS: the showrunner, bible, packager and director may add ONE `proposal` (idea / experiment / bank /
  world_building) inside the call they already make (no extra cost); code keeps at most CREATIVE_MEMO_MAX_PER_RUN per run, validates it as a
  creative_memo to the Council and DROPS one whose word set overlaps an earlier creative memo by CREATIVE_MEMO_SAME_MAX or more (homogenisation,
  research 11) - the Council (B6b) gets distinct options, not ten copies. 4/4/5/4/5.
- G. ORIGINAL, PARKED for B8 - counterfactual ablation: re-run one creative call WITHOUT the playbook and diff the outputs to measure whether the
  knowledge changes the work causally. The most honest measure, but one extra strong call per test: it belongs to D10 as an experiment arm.
CHOSEN: B + E + F, plus the draft fix (pre-production writing runs as a D4 department run and production adopts it with proof).

#### Step 3 DESIGN MEMO
Decision: knowledge enters a creative model through ONE doorway (the ask tap) and the proof of use leaves through ONE doorway (the reply tap);
proof = a quote code can find, never a list the model typed. The show's canon is code-written history in the same Palace, served in its own lane,
accepted only on air, and the newest case is a debt the next script must pay in a line code finds.
- Runner (`whatifs/org/runner.py`): prompt mode adds CITE_RULE (the JSON key `applied_items`, and `proposal` for the proposing tasks) to the
  injected block; records WHICH tasks carried it; the reply tap collects citations + proposals per run; ACT verifies (id in playbook, quote in the
  final output) -> ACT receipt: `injected_tasks`, `cited`, `applied` (verified only), `unverified`, `ghost`; a wrapped run's citations count too.
  `work(..., adopt=<draft session>)`: production's D4 write adopts a pre-production draft only with the draft run's proof (a D4 `draft` run, ok,
  prompt mode, injected) - its verified citations carry over, re-verified against the adopted text.
- Registry: D4/D5/D6 inject "prompt" with `inject_tasks` and `key_task` (writer / packager / director) and `propose_tasks`; new D4 call site
  `whatifs/preview.py` "draft"; owners of the three new checks.
- Palace (`palace.py`): canon lane with PALACE_CANON_SHARE (default 0.25 of the cap) for departments addressed by canon; kind rule: world_canon
  `proposed -> accepted` by D9 only with a "show record" evidence (what aired); D9 may make no other move.
- Canon (`whatifs/org/canon.py`, new, PROTECTED): `record(ep, room)` after D4 write (proposed case record, key `canon|case|<ep>`, derived from
  the D4 session); `on_air(ep, video_id)` after the upload is verified; `required(...)` (cast canon + the newest aired case at that time);
  `episode_issues(ep)` for the check. Cast canon = 4 founding items from `show.CHARACTERS` (seed `canon.json`; a test keeps them equal to the code).
- Creative memos: validated + same-idea guard in the runner's EMIT for D4-D7 (`creative_memo` to C; it waits silently at the owner level until
  B6b wires the Council - the B5 pattern for assessment memos).
- Checks (script gate, 47 hard checks): `palace_injected` (each creative run of the episode - D4 write or its adopted draft, D5 package, D6 plan -
  ran in prompt mode, its key task carried the playbook, the playbook text is stored), `palace_cited` (each of those runs has >= 1 verified citation
  when its playbook had a citable item; unverified / ghost shown), `canon_in_brief` (D4's playbook held every required canon item; with
  CANON_CALLBACK_ON and an aired earlier case, the newest case is cited with a quote found in the SCRIPT; this episode's case record exists).
  NA when the organisation or ORG_PROMPT_INJECT is off, or no creative run is recorded.
- Settings (safe defaults): ORG_PROMPT_INJECT TRUE, PALACE_CANON_SHARE 0.25, CANON_CALLBACK_ON TRUE, CREATIVE_MEMO_MAX_PER_RUN 1,
  CREATIVE_MEMO_SAME_MAX 0.5, PALACE_PROMPT_EST_INR 8 (counted in the episode estimate).
- Cost: no new paid call. Extra input: about 1,900 tokens on about 12 creative calls per long video (cached on the packed calls: writer, rewrite,
  punchup, director), plus about 100 output tokens per call for the citations: estimated Rs 4-8 a video, Rs 16-32 a month at 4 long videos
  (PALACE_PROMPT_EST_INR = 8 in the estimate). Off switch: ORG_PROMPT_INJECT = FALSE (the creative runs go back to brief mode; the three checks say NA).
- Rejected: A, C, D (reasons above); G parked for B8. Risks to watch: a rewrite pass may edit away a cited line (only verified citations count; a
  run with none fails); a draft written before the previous episode aired cannot cite it (canon_in_brief judges what was aired at writing time).

#### Step 4 BUILD (what changed; commits 52d9fd4 + 3459c44)
- `whatifs/models.py`: a second doorway, REPLY_TAPS / `_rtap`, on every JSON reply (fake path, real path, batch path); the fake path runs
  `fakes.fake_cite` (a compliant offline model: cites the first playbook line and the one closest to what it wrote, pays every MUST CITE debt with
  a line in the narration, proposes once when invited).
- `whatifs/org/cite.py` (new, PROTECTED): RULE / MUST / PROPOSE texts, `block`, `tokens`, `flat`, `found` (exact, or 80% of the quote's words in
  order inside a short window), `verify` (verified / unverified / ghost / limits), `proposals_to_memos` (schema, kinds, same-idea guard, cap, silent
  to the owner), `creative_runs` (an adopted draft is judged by its D4 draft run), `episode_issues` for palace_injected / palace_cited.
- `whatifs/org/canon.py` (new, PROTECTED): `facts` / `summary` / `record` (D4's case record, PROPOSED), `on_air` (D9: aired tag + accepted),
  `newest_case`, `required`, `must_cite`, `topic_words` / `names_case` (a callback line must name its case), `ensure_cast`, `episode_issues`.
- `whatifs/org/runner.py`: mode per trigger (`registry.inject(dept, trigger)`), B6a spec only for the creative runs, the tap puts block text at the
  START of the cached global layer (`Packed.of(...).with_global`), `_reply_tap`, ACT verification + receipt fields (`injected_tasks`, `cited`,
  `citable`, `unverified`, `ghost`, `citations`, `adopted`, `legacy_draft`), citation measures in the takeaway, proposals -> creative memos in
  EMIT, `work(adopt=, legacy=)`, `_adoptable`, `last_session`, `ensure_cast` before a creative playbook is built.
- `whatifs/org/registry.py`: PROMPT (D4 write + draft, D5 package, D6 plan: tasks, key, propose, must), CREATIVE_RUNS, `prompt_spec`,
  `prompted(dept)`, D4 call site `whatifs/preview.py` "draft", data_issues refuses a prompt spec that points nowhere, owners of the 3 checks.
- `whatifs/org/palace.py`: lanes 0 limits / 1 canon / 2-4 knowledge, canon spends `canon_tokens()` ON TOP of the cap, `aired(r)`, KIND_MOVES
  (D9: world_canon proposed -> accepted, only on a show record), `sync_canon` never rewrites a case and tags older cases with their air time.
- `whatifs/org/execute.py`: a knowledge lever of D4/D5/D6 needs a CITED use (`registry.prompted`); code-only runs neither prove nor use the window.
- `whatifs/episode.py`: D4 write adopts with `adopt=` / `legacy=`, `canon.record` after D4 write, `canon.on_air` after the upload.
- `whatifs/preview.py`: the writing is a D4 "draft" run (room carries `org_session`); `take_approved` supersedes an automatic draft written
  without the Palace, keeps an owner-approved one (`_legacy_draft`, judged as written before B6a).
- `whatifs/contract.py`: checks palace_injected, palace_cited, canon_in_brief (script gate; 47 hard checks: 28 script + 19 final).
- `whatifs/governor.py` + `costguard.py`: `palace_prompt_inr()` in every estimate. `whatifs/manage.py`: `v12b6a_upgrade` (one-time move).
- `whatifs/core.py`: 7 cells - ORG_PROMPT_INJECT TRUE, PALACE_CANON_TOKENS 700, CANON_CALLBACK_ON TRUE, CREATIVE_MEMO_MAX_PER_RUN 1,
  CREATIVE_MEMO_SAME_MAX 0.5, PALACE_PROMPT_EST_INR 15, V12B6A_FLIPS_DONE; default of PALACE_PLAYBOOK_TOKENS_BY_DEPT = {"D4": 2400}.
- `whatifs/similarity.py`: open issue 47 fixed (an episode is never compared with its own earlier draft; one fingerprint per episode).
- `tools/rehearsal.py`: B6a block (3 checks PASS, every creative run prompt-mode with a verified citation, the case on air, a distinct creative
  memo, the next draft's must-cite paid in its own script) + a next shot plan that proves the B4 knowledge lever by a cited use.
- Changed against the design memo while building, and why:
  (1) cast canon: B2 already mirrors the character bible daily (`palace.sync_canon`, from the Characters tab the owner can edit) - reused, no seed
  file (it would have doubled 4 items in every creative playbook); case key = the mirror's `canon:case:<ep>`.
  (2) canon budget instead of a share: with a share the canon pushed 2 more of the owner's limits out of the writer's playbook (measured 4 -> 6).
  (3) the writer's cap: at 1,800 tokens 4 limits ALREADY did not fit before B6a (his Soft Respawn / Zuni HR inspiration, "cheap long videos are
  built to break out too", the hard gates, the parked concept) - now that the playbook really reaches the writer, the cap moves to 2,400 once
  (measured: 0 left out). C still leaves 5 out: B6b.
  (4) the callback must NAME its case (found by a test: a model could cite the case id with any line). (5) creative memos silent to the owner
  (found by a test). (6) the engine needs a cited use for D4/D5/D6 knowledge levers (the spec's lever A rule, now possible).
  (7) WHERE the block sits - the design memo's "start of the cached layer" was WRONG ON COST and was replaced after measuring (commit 45ca227):
  inside the cached GLOBAL layer the block differs per task (continuity debt, proposal invitation) and per department, and the mechanical passes
  that share the writer's brief do not carry it, so one cached brief became several. Measured on one fake episode (the fake cache server applies
  the real caching rules and the Settings' prices), switch OFF vs ON: hit ratio 0.752 -> 0.532, cache writes 14.5k -> 37.6k tokens, AI cost
  Rs 24.79 -> Rs 35.88 (+Rs 11.09, growing with the size of the real brief). Now the block is the LAST part of the system prompt (the uncached
  ROLE layer): cache reads and writes are byte-identical to OFF (hit ratio 0.752), +21.7k uncached input tokens, Rs 32.34 (+Rs 7.55, flat).
  Research 4 holds either way (an edge of the prompt, never the middle). Real-size estimate from the Settings' prices: about 15 creative calls x
  about 2,000 tokens = about Rs 10 input + about Rs 4 of citations = about Rs 14 a long video, about Rs 60 a month at 4 videos (the design
  memo's "Rs 4-8" was too low): PALACE_PROMPT_EST_INR = 15. At 4 or 5 long videos a month the plan stays 'full' (tested).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken; each proven both ways in tests/test_v12_creative.py, 28 tests)
| Rule | Executing code | Fails when broken |
|---|---|---|
| The playbook is inside the key creative calls (never judges / mechanical passes) | `runner._ask_tap`, `cite.block`, `registry.prompt_spec` | `palace_injected` (script gate); runner breach "no model call carried the playbook" |
| Knowledge counts only with a quote found in the output | `runner._reply_tap`, `models._rtap`, `cite.verify`, `cite.found` | `palace_cited`; the REAL reply path of models.ask is run in a test |
| A draft is adopted only with proof | `runner._adoptable`, `preview.take_approved` | runner breach; `palace_injected` judges the draft run; the REAL pre-production job is run in a test |
| Canon written by code, canon only on air | `canon.record`, `canon.on_air`, `palace.KIND_MOVES` | `canon_in_brief` "no case record"; PalaceError for any other D9 move |
| Continuity debt paid in the final script, naming the case | `canon.must_cite`, `canon.names_case`, `cite.MUST` | `canon_in_brief` (not cited / not in the final script / does not name the case / playbook lacked canon) |
| Canon never pushes out a limit; the owner's limits fit the writer | `palace.canon_tokens`, `manage.v12b6a_upgrade` | `palace_health` notes; canon-budget and one-time-move tests |
| Distinct creative memos to the Council | `cite.proposals_to_memos` | memo tests; the rehearsal asserts distinct ideas |
| A knowledge lever of a creative department is verified by a cited use | `execute._verify_knowledge`, `registry.prompted` | `lever_verified`; engine test; the rehearsal |
| Paid inside the Rs 5,000; never costs a picture at the owner's cadence | `governor.palace_prompt_inr`, `costguard.estimate_lines` | estimate test |
| The block never changes a cached layer (no cached brief is re-written) | `runner._ask_tap` (ROLE layer only) | cache-layer test; the contract test of prompt mode in tests/test_v12_org.py |
Matrix: 7 rows in docs/CURRENT/ENFORCEMENT_MATRIX.md (meta-test `tests/test_v111_enforce.py`). Founding items: b6a.quote_anchored_citations,
b6a.knowledge_at_the_start, b6a.restate_every_call, b6a.canon_by_code, b6a.continuity_debt, b6a.distinct_ideas, b6a.takeaway (133 founding
items; Palace GREEN; no limit crowded out of a playbook by them: D1 3, D2 1, D12 1, C 5 left out as before, D4 0 instead of 4).

#### Step 6 PROVE
- Both ways, 28 tests in tests/test_v12_creative.py: quotes (exact / small edits / too short / absent / out of order); a citation offered-and-
  quoted vs unverified vs ghost vs limit; the playbook only in the named calls and the caller never sees the citation fields; cached layers
  byte-identical; the REAL reply path of `models.ask`; a lying packager fails `palace_cited`; a ghost id is recorded, never counted; a creative
  run in brief mode / a key call without the playbook fails `palace_injected`, and the switch OFF says N/A (never a fake PASS); a creative run
  with no model call breaks the contract; the case record (written by code, proposed, canon only on air, never rewritten after); D9's one move;
  the continuity debt (given, paid, PASS; edited away -> FAIL; not cited -> FAIL; cited with an unrelated line -> FAIL; canon missing from the
  playbook -> FAIL; no case record -> FAIL); the canon budget never pushes a limit out; the mirror never overwrites a case; proposals -> distinct
  memos (same idea dropped, invalid dropped, non-creative department refused, an uninvited call's proposal ignored); drafts adopted only with
  proof (missing run, brief-mode draft -> breach); an automatic draft without the Palace is superseded, the owner's own approval stands; the REAL
  pre-production job writes under D4; the engine verifies a creative knowledge lever only by a later CITED use; estimates; the one-time cap move
  (once, never over the owner's value); the registry refuses a prompt spec that points nowhere; the similarity guard (issue 47) both ways.
- Mutations (each restored): citations never verified -> 6 tests fail; reply doorway removed on the real path -> 1; any line counts as a
  callback -> 1; pre-production writing outside D4 -> 1; the tap no longer injects -> 9; `canon.record` removed from the real episode job ->
  the rehearsal HOLDS the episode at `canon_in_brief` ("no case record ... D4 did not write its continuity takeaway").
- Faults found by tests / by measuring, fixed before acceptance (none by a first green run): (a) creative memos were owner-visible - the
  watchdog would have pinged the owner about every idea; (b) any script line passed as the callback; (c) a department in base prompt mode was
  limited to the B6a call list; (d) the block inside the cached layer re-wrote the prompt cache (+45% AI cost on a fake episode, see step 4
  (7)); (e) the canon share pushed 2 more owner limits out of the writer's playbook; (f) the engine's knowledge lever for D6 could never be
  verified once D6 had to cite (the rehearsal went RED: code-only runs used up the window) - code-only runs are skipped, a later shot plan proves it.
- Existing tests changed BY DESIGN (each with the reason in a comment): 28 script checks (was 25); `sync_canon` re-compares 4 characters (a
  case is written once); engine and contract test files run with ORG_PROMPT_INJECT off (their departments are code, no model call); the
  writers' own cap in two playbook tests; the canon budget on top of the cap; the registry test copies the new call-site file; the prompt-mode
  contract test (the playbook in the ROLE layer); two money goldens (+ the Palace allowance; the nine-video-month golden keeps its own cost
  profile, as it does for its Kling price); a pre-production test draft carries its D4 run.
- GitHub runs of this batch: #69, #70 GREEN (research, design); #71 RED = 54 existing tests that were code-only creative runs or pinned totals
  (fixed in 3459c44); #72 RED = 3 pinned tests (two money goldens + the pre-production draft; fixed in aba1b6f, the same 3 the laptop suite
  found); #73 GREEN (1260 passed, 0 skipped, rehearsal GREEN EP202611110156, script 28 / 28, final 19 / 19). Both RED runs traced, none re-run.
  #74 GREEN (f608e5b: 1260 passed, rehearsal GREEN EP202611110203). **#75 GREEN on the FINAL code commit 45ca227: 1261 passed, 0 skipped,
  rehearsal GREEN (episode id EP202611110234, script 28 / 28, final 19 / 19).** The one warning is GitHub's own (open issue 37).
- Laptop, final code (45ca227): full suite 1260 passed / 0 failed / 1 skipped (the known laptop-only skip); rehearsal GREEN (script 28 / 28, final 19 / 19;
  `creative departments: D4 write 3 verified, D5 package 2 verified, D6 plan 2 verified | case on air | 1 creative memo | next draft
  paid its debt`); Plan Guard GREEN; truth registry GREEN; Palace GREEN (133 items). The first laptop suite (3459c44) was 1255 / 3 / 1: the 3
  were the pinned tests of run #72.
- Sweep (standing rule 2) on a frozen copy of 45ca227: 40 of 40 fixed episode ids green, every id script 28 / 28 and final 19 / 19 (41 PASS +
  6 N/A of 47), no fail class, no degraded class, no owner message, no prompt-cache warning. An earlier sweep on aba1b6f was stopped at 15 of
  15 green when the cache fault was found (the code under test was about to change).

#### Step 7 TAKEAWAY (also Palace item `b6a.takeaway`, 133 founding items)
- What worked: one doorway in (the ask tap) and one doorway out (the reply tap) meant 9 creative calls in 3 departments got knowledge and proof
  without touching a single prompt template; playing a LYING model in tests (a quote it never wrote, an id never offered, an unrelated line as
  the callback, an uninvited proposal) found what every green run hid; reusing B2's canon mirror and B5's silent-memo pattern kept the batch small.
- What the batch found that nobody had asked about: since B3 every department "took" its playbook and NO model call had ever seen one; with
  pre-production on, the script was written outside any department run; 4 of the owner's own limits had never fitted the writer's block.
  "Handed over" was a receipt, not a fact. Rule for every later batch: trace each rule to the call that uses it, and make the receipt name that call.
- What to watch: (1) a verified quote proves the line exists, not that the knowledge caused it (open issue 48, D10 in B8); (2) the real cost
  of the block must be reconciled with Cost_Log after 2-3 real videos (allowance Rs 15; measured only on the fake cache server); (3) real
  models may cite sloppily at first - `palace_cited` then HOLDS the episode before picture money: read the `unverified` / `ghost` lists in
  the D4/D5/D6 Sessions rows before touching the check; ORG_PROMPT_INJECT = FALSE is the off switch, never a lower bar; (4) measure money
  claims before writing them down: the design memo's cost line was an estimate and it was wrong twice (placement and amount).

### B5 - R&D + Review Board (11 Nov 2026) - ACCEPTED (final code commit a1c5204 GREEN in GitHub run 67; sweep 58 of 58 green)

#### Step 1 RESEARCH (12 dated sources; E = measured evidence, O = opinion / practice / vendor documentation)
Honest note: for the arXiv papers the abstract page was read, not the full paper; 6 and 11 are quoted from a search summary (not opened).
1. E - Rao, Wong, Callison-Burch, "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents", arXiv 2604.03173,
   3 Apr 2026: 3-13% of citation URLs are hallucinated (never existed), 5-18% do not resolve; deep research agents cite MORE and hallucinate MORE;
   a liveness check given to the model cut non-resolving URLs 6-79x to under 1%. -> a source counts only if the SEARCH TOOL returned it (never a URL
   the model typed) and it answers a liveness check; a phantom source is dropped and counted against the memo.
2. E - Onweller et al., "Cited but Not Verified", arXiv 2605.06635, 7 May 2026: frontier deep-research agents keep link validity above 94% and
   relevance above 80% but reach only 39-77% factual accuracy; accuracy falls about 42% as tool calls grow from 2 to 150. -> a valid link is not
   support: the evidence a memo carries is the tool's own quoted text, the jury checks "does the finding follow from the quote", and each question
   gets a SMALL bounded search (max_uses), never an open-ended agent loop.
3. E - Awuni et al., "Who Judges Matters: Family-Conditioned Preference in LLM-as-Judge Panels", arXiv 2609.17857, 15 Sep 2026 (9,312 judgments,
   4 families): every family prefers its own family by 3.4-8.4 points; 55.4% of AB/BA pairs REVERSE with the order; panel composition changes 18.5% of
   outcomes. -> the jury is balanced by FAMILY (mean of family means, not of judges), every judge sees two orders, and the family that did not
   write the memo must clear the bar by itself before anything is accepted.
4. E - Verga et al. (Cohere), "Replacing Judges with Juries" (PoLL), arXiv 2404.18796, 29 Apr 2024: a panel of models from disjoint families beat a
   single large judge, with less intra-model bias, at over 7x lower cost. -> a cross-family panel is the right shape; a single judge never decides.
5. E - Huang & Zhou, "Comparative Evaluation of LLM-Based Review Paradigms", arXiv 2610.41391, 30 Oct 2026 (232 + 11,513 ICLR submissions): direct
   1-10 rating "compresses most predictions above the accept threshold, flagging almost none" of the weak papers; after recalibration it beat Elo
   with 24% of the calls. -> no free 0-10 scores from a model: judges answer concrete yes/no questions and CODE turns them into scores.
6. E - "LLM-as-a-Reviewer" benchmark, arXiv 2605.25415, May 2026 (search summary): most of 12 models over-rate papers, some families by up to 2.43
   points on the venue scale. -> inflation is the default; the verdict needs an independent calibration signal (design D: the planted canary).
7. E - Lee et al., "CheckEval", arXiv 2403.18771 (EMNLP 2025): decomposed binary checklist questions raised average agreement across 12 evaluator
   models by 0.45 and reduced score variance; RubricEval, arXiv 2603.25133, Mar 2026: rubric-level questions with explicit reasoning cut inter-judge
   variance further. -> the rubric is a fixed checklist per dimension with a one-line reason per answer.
8. E - Si, Hashimoto, Yang, "The Ideation-Execution Gap", arXiv 2506.20803, Jun 2025 (ICLR 2026): 43 experts executed ideas blind (100+ h each);
   LLM ideas scored HIGHER before execution and dropped significantly more after it on every metric (p < 0.05), with rankings flipping. -> a
   jury's praise is a hypothesis: a creative technique can at most be "test" (an experiment arm, lever C); "accept" is kept for facts (policy,
   tools, prices) backed by official or measured sources.
9. O - Anthropic web search tool documentation (read 11 Nov 2026): USD 10 per 1,000 searches plus tokens (results count as input); failed searches
   not billed; usable in the Message Batches API at the same search price (batches throttle searches); citations carry url, title and up to 150
   characters of `cited_text`; results carry `page_age`; `max_uses` caps searches per turn; tool versions 20250305 / 20260209 / 20260318.
   -> evidence is read from the API's citation blocks (url + quoted text + page age), not from the model's prose; cost per question is computable.
10. O - Google Gemini grounding pricing (Google Cloud pricing page via search summary, 2026): Gemini 3 family 5,000 grounded prompts a month free, then
   USD 14 per 1,000 queries; Gemini 2.5 billed per prompt (USD 35 per 1,000 after 1,500 a day). -> Gemini grounding is the fallback researcher
   (cheap, but no quoted text: its findings get a lower evidence ceiling).
11. O - YouTube "inauthentic content" monetisation update, 15 Jul 2025 (TeamYouTube; 2026 enforcement reported, search summary): mass-produced or
   repetitive uploads ("narrated stories with only superficial differences") are ineligible; AI tools are allowed. -> platform policy is a standing
   research question every 4 weeks and a risk question every juror must answer for every proposal.
12. E - NovGauge, arXiv 2609.11234, Sep 2026 (search summary): LLM judges over-attend to technical validity and underweight novelty. -> novelty is
   judged against the department's OWN playbook (what we already do), given to the jury, not against the model's general sense.
Re-read: 02 points 2 ("evaluated by another chat session objectively in its role"), 3 (cheap models never judge taste), 12, 14 ("AUTOMATIC
RESEARCH, AUTOMATIC ASSESSMENT OF RESEARCH"), 15; 01 sections 2 (D2, D3), 5, 7 `research_cadence`, 8, 9; open issues 8, 13, 30.

#### Step 2 CREATIVITY (4 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Extend the topic brief": keep `research.py`'s brief, add one web-search call, let `room2.jury` rank the findings. 2 / 2 / 5 / 3 / 5. Rejected:
  a ranking has no accept / test / reject, room2's jury includes a cheap judge (02 point 3), and the brief answers "which topic", not "what is wrong
  with us and who does it better".
- B "Deep-research agent": plan -> many searches -> read -> synthesise per question (the commercial deep-research shape). 4 / 2 / 1 / 2 / 5.
  Rejected: sources 1-2 (most hallucinated URLs, accuracy falls ~42% as tool calls grow) and the cap (Rs 300 buys about 20 bounded questions a month).
- C "Gap-driven agenda + grounded memo + checklist board": the agenda is computed by code from the organisation's own failures (failed checks,
  weakest breakout component, recurring problems, owner memos, outliers, expiring facts, policy and tool changes); one bounded search call per
  question; provenance verified by code; a blind cross-family jury answers fixed yes/no questions; code computes scores and the verdict.
  4 / 5 / 4 / 4 / 5. Taken as the core.
- D ORIGINAL, beyond the research - five rules that make a jury's verdict something code can check:
  (1) PLANTED CANARY: every Board session contains one memo the code built to be rejected (no dated source, a guaranteed-views claim, a policy
      breach, nothing measurable), shown blind among the real ones. Each FAMILY of judges must reject it on its own, or the whole session is void
      (no verdict written, the memos wait for the next run). Calibration is measured on every session, not assumed (sources 5, 6).
  (2) EVIDENCE CEILING: code computes the highest evidence score a memo can get from what it can verify (sources the search tool really returned,
      that resolve, dated, distinct domains, official or measured types, how fresh); the jury can lower it, never raise it (sources 1, 2).
  (3) FAMILY VETO: scores are the mean of FAMILY means, and nothing is accepted or sent to test unless the family that did NOT write the memo
      clears the bar by itself (source 3).
  (4) PRE-REGISTRATION: every proposed action carries a prediction in a fixed vocabulary (a contract check or an Analytics column, a direction, a
      horizon in videos); without one a technique cannot reach "test" - the prediction becomes the experiment's metric when the Council issues it.
  (5) FACTS ACCEPT, IDEAS TEST: only a fact (policy, tool, price, an expiring Palace fact) can be "accept"; a creative technique is at most "test"
      (source 8: what juries love before execution falls hardest after it).
  5 / 5 / 4 / 4 / 5.
Decision: C + D. Rejected after scoring: Message Batches for research (searches cost the same in a batch, only tokens halve - about Rs 4 a question,
~Rs 70 a month - while the batch API throttles searches and the daily job would wait up to 40 minutes per batch; recorded as an open issue for
measurement, not built); a third (cheap) judge; letting the model choose the evidence type (code classifies by domain).

#### Step 3 DESIGN MEMO
- Decision: two native departments - `whatifs/org/rnd.py` (D2) and `whatifs/org/board.py` (D3) - the first departments whose ACT returns
  `runner.Out` (memos, every inbound memo dispositioned, measures), so the runner proves every step.
- Where they run (level-triggered, so a missed day never skips a week): the daily `learn` job, in this order: D2 `daily` (Rs 0: the Outlier Lab, the
  search-demand scores and the research brief move here from `manage.learn`; then the agenda is refreshed) -> D2 `weekly` when the last complete
  weekly run is RESEARCH_DEEP_EVERY_DAYS old (paid, budget "org", cap Rs 300) -> D3 `assess` when a research memo waits (paid, budget "org", cap
  Rs 120) -> D10 `daily` as before. A research memo is therefore assessed the same day it is written (SLA 48 h).
- D2 agenda (`Research_Agenda` tab, one row per gap, deduplicated by signature, a question answered is not asked again for RESEARCH_REPEAT_DAYS):
  failed contract checks (28 days, by count; addressed to the check's owner), the weakest breakout component, recurring problem memos (attempt >= 2),
  open owner memos (P0, always asked, outside the weekly count), Outlier Lab videos (14 days), Palace facts / plans / policy rules expiring within
  14 days or expired (closes the research side of open issue 8), new or deprecated models in `Tool_Scout`, and a standing platform-policy question
  every 28 days. Priority is computed; the weekly run asks the top RESEARCH_PER_WEEK while the D2 budget left covers the estimate per question
  (RESEARCH_EST_INR or the median measured cost, whichever is higher); P0 is asked even past the cap (01 section 9).
- One question = one `models.ask` call with the web-search tool (role `rnd_research`, Sonnet chain; Gemini grounding is the fallback), at most 4
  searches. `models.last_call()` (new, additive) returns the provider, the model, the measured cost and the citations the API itself returned.
- Provenance by code (`rnd.verify`): a source counts only if its URL is among the API's citations or results (a URL the model typed is a PHANTOM:
  dropped, counted, and costs the memo 2 points of ceiling); it must resolve (404 / 410 / no host = dead; 401-429 = alive but blocked); it needs a
  publication date not in the future (the result's page age or the model's date); its type is decided by its domain (platform / vendor = official,
  research = measured, else practice), never by the model; its quoted text is the API's `cited_text`. A finding with no surviving source is dropped;
  a question with no surviving finding writes no memo (agenda row "unanswered", the money is still counted). Evidence ceiling 0-10 from distinct
  domains, official / measured sources, freshness and phantoms.
- Research memo (to D3): question, findings, confidence (never above ceiling / 10), proposed actions, expected impact, cost, target departments; new
  optional body fields kind, gap, evidence_ceiling, predictions, palace_ref; links carry the agenda row and the researcher's family (the jury never
  sees it). Schema change is additive.
- D3 Board session (`board.assess`): up to BOARD_MAX_MEMOS research memos + 1 canary, labelled A, B, C... with no department, model or id; for each
  memo the jury also sees the target department's own playbook ("what we already do") for the novelty questions. Two judges of two families
  (`board_gemini` = Gemini Pro only, `board_claude` = Sonnet then Opus: chains with NO cheap model), each in BOARD_ORDERS orders (original and
  reversed). 12 yes/no questions with a one-line reason each: evidence 2, novelty 2, impact 3, feasibility 2, risk 3 (policy, owner rules /
  canon, slop); cost is computed by code from the memo's cost. Scores per dimension = 10 x the share of "yes" (family-balanced); evidence is capped
  by the ceiling. Verdict by code (`board.verdict`): reject when evidence < BOARD_MIN_EVIDENCE, risk >= 5 or impact < 4; accept only a FACT
  (policy, tool, revalidate) with evidence >= 7, feasibility >= 5, risk < 3; test when impact >= 6, feasibility >= 5, novelty >= 5 and at least
  one valid prediction; else reject; accept / test also need the non-author family alone to clear the same bar. A judge answered by the wrong model
  (fallback to another family or to a cheap model), a single family, or a canary not rejected by every family = session void.
- Assessment memo (to the Council) carries the scores, the verdict, the jury (family:model), the rationale, the family checklist shares and the
  canary result; `research_cadence` RE-COMPUTES every stored verdict from the stored checklist and fails on a mismatch (a verdict nobody can forge).
  Until the Council exists (B6) an assessment memo waits at the owner's level silently (owner_visible only for an accepted P0 fact).
- Check `research_cadence` (script gate, owner D2): FAIL when (after a 48-hour grace from ORG_SINCE) D2's daily run is more than 50 hours old, the
  weekly run more than RESEARCH_DEEP_EVERY_DAYS + 1 days old while budget is left, a research memo is past its SLA and neither assessed nor
  escalated, a research memo lacks the provenance stamp (not written by `rnd.verify`), an assessment's verdict differs from the code's verdict on its
  own checklist, an assessment lacks two families or the canary, or a department spent past its cap by more than one question's estimate without a P0.
- Money (rule 2): D2 cap Rs 300 (about 4 questions a week at Rs ~10-15 each, measured per call), D3 cap Rs 120 (about Rs 10-20 a session).
  The unspent part of the caps of WIRED departments is reserved from production like an earmark (`governor.org_left_inr`), so the month's plan
  never counts the organisation's thinking money twice.
- Levers: + RESEARCH_PER_WEEK (D2; up = costs more -> owner), + BOARD_MIN_EVIDENCE (D3; down = weaker gate -> owner). D2 and D3 leave
  `registry.PENDING` (7 -> 5), so their tickets reach the engine.
- Rejected: the Board writing Palace items or tickets (the Council decides, B6); the model choosing the evidence type; free 0-10 scores; one judge
  family; Message Batches (see step 2); re-validating Palace facts directly (only owner, Council, D10 may - the memo carries `palace_ref` for B6).
- Tests: provenance both ways (phantom, dead, undated, future-dated, type clamp, finding without source, empty memo), agenda from every gap source and
  dedupe, cap and P0, the jury's family / model / canary rules, verdict table both ways, forged verdict, the check's every FAIL condition, the REAL
  learn job running D2 and D3, a fake research cycle end to end (agenda -> memo -> assessment -> the Council's level).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/rnd.py` (D2): `gaps` (8 gap sources, Rs 0) + `refresh` (tab `Research_Agenda`: dedupe by signature, drop closed gaps, re-open after
  RESEARCH_REPEAT_DAYS, never while the last memo is open, a dead or failed ask re-opens after 20 h); `daily` (the research brief, the Outlier Lab and
  the search-demand scores moved here from `manage.learn`, then the agenda); `deep` + `deep_due` (weekly, level-triggered, P0 first and past the cap,
  P1/P2 while the budget left covers max(RESEARCH_EST_INR, median measured)); `ask_one` (role `rnd_research`, web search, at most 4 searches);
  `verify` / `alive` / `source_type` / `parse_date` / `ceiling` (provenance by code); `build_memo` (research memo with the stamp `rnd.verify`);
  `ceiling_of` + `cadence_issues` (what the check judges).
- NEW `whatifs/org/board.py` (D3): 12 yes/no questions (2 evidence, 2 novelty, 3 impact, 2 feasibility, 3 risk); 3 canaries (no source + bought views; an irrelevant quote + daily re-uploads; an official quote that says the
  opposite + mass-produced Shorts); `assess` (blind blocks A, B, C... with the target department's own playbook, 2 families x BOARD_ORDERS orders,
  the answering model checked through `models.last_call`, void rules, assessment memos, a D3 -> D3 problem memo when void, closed by the next valid
  session); `scores_from` / `bar` / `verdict` / `cost_score` (pure: the check re-runs them); `assessment_issues`. Tab `Board_Log`.
- `whatifs/models.py` (protected): `last_call()` + `_note_call` + `_claude_sources` (the API's citations and results, the answering chain role and
  the measured USD, recorded by `_claude`, `_gemini` and the fake path); routes `rnd_research` (Sonnet chain), `board_gemini` / `board_claude` with
  chains `board_g` = Gemini Pro only and `board_c` = Sonnet then Opus (no cheap model can answer for the Board).
- `whatifs/org/schemas.py` (protected): research memo + kind, gap, evidence_ceiling, predictions, palace_ref, sources_dropped; assessment memo +
  checklist, canary, kind, evidence_ceiling, author_family, predictions, cost_inr (all optional: additive). `RESEARCH_KINDS`.
- `whatifs/org/memos.py` (protected): `id_for` (the id `write` will use, so a department can close a memo with the memo it sends in the same run).
- `whatifs/org/registry.py` (protected): D2 wired (`cli.py` daily + weekly), D3 wired (`cli.py` assess), PENDING 7 -> 5 (D0, D1, D11, C, L);
  `reach.py` moves to D10's wraps (master spec lists it under both; it measures our own videos); D2 + RESEARCH_PER_WEEK, D3 + BOARD_MIN_EVIDENCE;
  CHECK_OWNER research_cadence -> D2. `whatifs/org/levers.py`: 2 rules (41 levers).
- `whatifs/contract.py`: check `research_cadence` at the script gate: **44 hard checks (25 script + 19 final)**.
- `whatifs/cli.py`: `research_round()` runs first in the learning job (D2 daily, D2 weekly when due, D3 when a memo waits; each failure logged,
  never stops the job). `whatifs/manage.py` (protected): the research brief renewal, `OLB.run()` and `DMD.run()` left `learn` (now in D2 daily).
- `whatifs/governor.py` (protected): `org_left_inr` - the unspent part of the wired departments' thinking caps (D2 Rs 300 + D3 Rs 120 while
  research is on) is subtracted in `production_room_inr` like an earmark.
- `whatifs/core.py` (protected): tabs `Research_Agenda` (17 columns), `Board_Log` (12); 7 settings: RESEARCH_PER_WEEK 4, RESEARCH_EST_INR 15,
  RESEARCH_REPEAT_DAYS 28, RESEARCH_DEEP_EVERY_DAYS 7, BOARD_MIN_EVIDENCE 5, BOARD_ORDERS 2, BOARD_MAX_MEMOS 6.
- `whatifs/fakes.py`: a fake web search (3 sources with quotes and page ages relative to today), a fake research answer (with one phantom and one
  undated source, two predictions), a fake strict judge that rejects every canary. `tools/repair.py` PROTECTED + rnd.py, board.py.
- 7 founding items `b5.*` (125 founding items, Palace GREEN, no playbook crowded further); `tools/rehearsal.py` runs the real `research_round`.
- Changed against the design memo after seeing real behaviour or re-reading: (1) the ceiling is computed on the sources the memo CARRIES (a kept
  source no finding used had raised it); (2) a question is never asked again while its last memo is still open (the new memo would have collided with
  the open one and the runner would have refused every memo of that run); (3) the five faults of step 6a; (4) assessments stay silent at the owner's
  level for now - the design said "owner_visible for an accepted P0 fact", but the only message the ladder has today says "Stuck past its deadline"
  for a memo written a second earlier.
- Existing tests changed BY DESIGN (say so in the final PR): `tests/test_v12_org.py` (a pending department for the escalation test is now D11, D2
  is wired), `tests/test_v12_exec.py` (41 levers, 25 script checks), `tests/test_v94a.py`, `tests/test_v87.py`, `tests/test_v10_growth.py` (production
  room minus `org_left_inr`).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executes | Fails when broken |
|---|---|---|
| Research is computed from the organisation's own gaps and runs by itself | `rnd.gaps`, `refresh`, `deep_due`, `cli.research_round` | `research_cadence` FAIL (daily run older than 50 h; weekly older than RESEARCH_DEEP_EVERY_DAYS + 1 with budget left); the real learn job test |
| A source counts only if the search tool returned it, it resolves, it is dated and not in the future; type by domain | `rnd.verify`, `alive`, `source_type`, `models.last_call` | phantom / dead / undated / future dropped and counted; no surviving finding = no memo; `research_cadence` FAIL on a memo without the stamp or with a ceiling its evidence does not support |
| Blind, strong, two families, two orders, fixed questions; scores and verdict by code | `board.assess`, `_parse`, `scores_from`, `verdict` | a judge answered by another family or a cheap model is not counted; < 2 families = void; `research_cadence` re-computes every stored verdict |
| A planted canary must be rejected by every family | `board.canary`, `assess` | session void, no assessment, D3 problem memo (recurring -> escalates) |
| Only facts accepted; ideas tested only with a pre-registered prediction | `board.bar`, `rnd.metrics`, `_actions` | decided by code; the forged-verdict test |
| Caps: R&D Rs 300, Board Rs 120; P0 continues; the unspent part is not production money | `runner.run` (budget "org"), `rnd.deep` (in-run guard), `governor.org_left_inr` | CapReached before the run; `research_cadence` FAIL on overspend without an owner question |
Matrix: 5 rows (meta-test green). Founding items: 7.

#### Step 6 PROVE
- `tests/test_v12_rnd.py`: **31 tests**, each rule both ways: a phantom source dropped and costing 2 points; dead, undated and future sources dropped
  with the findings that stood only on them; the type set by the domain (a model may only lower it); the ceiling table; Gemini matched by domain and
  capped at 6; liveness on a real network (404 / 410 / no host dead, 401-429 and timeouts alive); five date forms; predictions need a known metric, a
  direction and a horizon; an unprovable answer writes no memo; a memo carries only verified evidence and passes the memo gate; the agenda from all
  8 gap sources and never from a code fault; dedupe, drop, re-open after the window, never while the last memo is open, a dead or failed ask open
  again after 20 h; the ceiling recomputed from the day the memo was written; the weekly run inside the cap with the owner's question beyond it, and
  CapReached at the cap; due by level, not by calendar (a broken run is not re-paid); a Board session blind (no memo id, author or model in any
  prompt), two families x two orders x memos + canary, each research memo closed by its own assessment, assessments silent at the Council's level;
  a judge answered by the other family or by a cheap model not counted -> void -> D3 problem memo (recurs) -> closed by the next valid session; an
  inflating jury voids the session; unanswered questions count against the memo; the verdict table and the family veto; forged verdicts, scores,
  one family, no canary caught; `research_cadence` N/A off / young, and every FAIL condition (daily 60 h, weekly 9 days with budget left - not when
  capped, no stamp, forged ceiling, past SLA and not escalated, forged verdict, D3 overspend); the REAL learning job; the collectors moved; the wiring;
  the lever rules (up costs more -> owner; down weakens the gate -> owner; another department's lever refused); the money reserve; `last_call` reading
  the API's citation blocks, Gemini grounding chunks and the fake path.
- Live proof by mutation on the real repo, each reverted: the phantom check removed and the canary rule disabled (one run) -> **7 tests fail**, the
  canary test among them;
  `research_round()` removed from the learning job -> the wiring test fails while `python -m whatifs.org.runner` and the truth scan both stay GREEN
  (the literal calls still exist inside the function: B4's warning about name scans holds again).
- Fake rehearsal on the final code: **GREEN** - contract script 25 / 25, final 19 / 19 on GitHub; the research round inside it: 3 research memos ->
  policy: accept, technique: test, technique: test; canary rejected by both families; `research_cadence` PASS.
- Full suite: **1232 passed / 0 failed / 1 skipped** (66 files, one uninterrupted run by itself on a frozen copy of c325b3e; the skip is the dashboard
  render, which needs node - GitHub runs it). The final commit a1c5204 adds only the takeaway seed item, a CLAUDE.md recipe and generated docs.
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (126 founding items; the limits note unchanged: D1 3,
  D4 4, D12 1, C 6). Organisation **GREEN** (10 wired, 5 pending).
- Sweep (standing rule 2): on a frozen copy of a1c5204 - A: 40 fixed ids, organisation ON: **40 ok, 0 held, 0 crashed** (each: status SCHEDULED,
  38 PASS + 6 N/A, 9 department runs verified, 0 live memos, 0 owner messages, 0 degraded steps); B: 10 ids with ORG_ON = FALSE: **10 ok** (35 PASS +
  9 N/A); C: 8 full rehearsals with a forced id: **8 ok** (status LIVE, 39 PASS + 5 N/A, the research round in each: 3 live memos = the assessments
  waiting silently for the Council). **58 of 58 green.** Warning classes: the same 9 in every episode and 1 in 1 of 40 as in B4 - none is new.
  Traced, not new: every rehearsal also sends the owner a 'similar script' message because the rehearsal renders the SAME episode again and
  `similarity.check` compares it with its own earlier fingerprint (the episode is named as its own twin; code untouched by B5) - open issue 47.
- GitHub Checks (standing rule 1), every commit of the batch read on the public run page: #61 (step 1) and #62 (steps 2-3) GREEN. **#63 (be89fa4) RED**
  - 6 failed / 1196 passed: exactly the six tests whose expectation changed by design (41 levers, 25 script checks, D2 no longer pending, three
  production-room formulas off by the organisation's Rs 420 reserve), updated in the next commit. **#64 (9060e41) and #65 (8f5a9d7) RED at the
  rehearsal** (unit tests 1231 / 1233 passed): the rehearsal's own production-room formula (`maintenance reserve ... must sit inside the cap`) - the same
  assertion my laptop rehearsal failed on, fixed in c325b3e. Traced from the annotations, not re-run. **#66 (c325b3e) GREEN. #67 (a1c5204, the final
  code commit): GREEN - 1233 passed, 0 skipped, rehearsal GREEN (episode id EP202611102139, script 25 / 25, final 19 / 19).** New notice on the run page:
  GitHub's `ubuntu-latest` label moves to Ubuntu 26 from 19 Oct 2026 (open issue 46).
- Money: Rs 0 spent (fake mode). Expected in production: R&D about Rs 10-15 a question x 4 a week (cap Rs 300), the Board about Rs 10-20 a session
  (cap Rs 120); NOT measured - the first real runs must be read (open issue 40).

#### Step 7 TAKEAWAY (also Palace item `b5.takeaway`, 126 founding items)
- WORKED: every judgement as a PURE function of stored data (the ceiling, the scores, the verdict). The check re-runs them on what is stored, so a
  typed, edited or forged verdict fails `research_cadence` - the Board's word is not trusted, its arithmetic is re-done.
- WORKED: a test the judge must fail. The planted canary turns "is the jury inflating?" (sources 5-6) from a worry into a measurement per session; a
  flattering judge (yes to every good question, no to every risk) is caught by the test that simulates it.
- WORKED: re-reading the finished code as a stranger again (B4's lesson). It found five faults no test had asked about, each about TIME: a row stuck
  in "asked" after a killed run, a 28-day wait after a failed call, a one-day shift at midnight in the recomputed ceiling, a broken weekly run re-paid
  every day, and a "stuck" message to the owner for a memo written a second earlier.
- WORKED: the real-job test. Removing `research_round()` from the learning job left the registry scan AND the truth scan green (the literal calls
  still exist inside the function); only the test that runs `python -m whatifs.cli learn` saw it.
- WATCH: the fake judge recognises the canaries by their words - it is a stand-in. Real calibration exists only in production: read `Board_Log`
  (verdict "void" and its reason) after the first real sessions.
- WATCH: nothing researched changes a video until the Council (B6) turns assessments into tickets; until then every assessment waits silently at
  the owner's level (open issue 38).
- WATCH: the real web-search citations, Gemini grounding and the cost per question are proven with stand-ins and the documentation (open issue 40).

### B4 - Execution Engine (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below; final code commit ad99fd2 GREEN in GitHub run 59)
Result in one line: whatever the organisation decides can now only exist as a change that runs - a ticket is compiled into a typed change, written to a
ledger before and after, verified by evidence somebody else wrote later, and rolled back when that fails; a decision without executed tickets fails a
HARD check before picture money. Honest limits: no real ticket is written until the Council exists (B6), so B4 by itself changes no video; knowledge is
proven "served", not yet "cited" (B6); the code lever is proven with stand-ins for GitHub, never on GitHub itself; tickets for the 7 departments that
are still pending go straight to the owner's level.

#### Step 1 RESEARCH (14 dated sources; E = measured evidence, O = opinion / practice / vendor documentation)
Honest note: for sources 1-5 and 14 the abstract page was read, not the full paper; 4 and 9c are quoted from a search summary.
1. E - Mohammadi et al., "Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows", arXiv 2602.14849, 16 Feb 2026 (v2 29 May 2026):
   orchestrators treat a tool's RETURN as the signal that work is settled; effects are bufferable, reversible or irreversible; commit only when
   nothing earlier can still conflict; abort compensates what was already let out. -> "applied" is not "done": a change is settled only by later evidence.
2. E - Chen et al., "Cordon: Semantic Transactions for Tool-Using LLM Agents", arXiv 2606.17573, 16 Jun 2026: reversible changes first, outward
   actions staged, the composed flow validated BEFORE an irreversible commit, audit metadata recorded. -> the undo is computed and stored before
   the change; the only irreversible lever (merged code) has the strictest gate.
3. E - Wu et al., "Safe to Resume? Breaking Execution Continuity of Agent Execution via Rollback", arXiv 2608.29381, 29 Aug 2026: "correct rollback
   does not imply secure recovery" - a faithfully restored state can sit next to newer external facts that never coexisted with it (three
   end-to-end attacks, five frameworks). -> a rollback restores the old value ONLY if the cell still holds what the engine wrote.
4. E - "Always-On Agents" survey, arXiv 2606.30306, Jun 2026: 27 of 435 surveyed works expose any rollback; none reports recovery success or cost.
5. E - Lin et al., "Safety in Self-Evolving LLM Agent Systems", arXiv 2606.23075, 22 Jun 2026: a bad self-change is lineage-persistent (40 of 40
   payloads persisted); 17 of 25 module x life-cycle cells critical; scanners that sit beside the agent stopped 2.5%. -> every self-change carries
   its lineage (ticket -> decision -> memos), is reversible, and the commit gate is code OUTSIDE the component that proposed it.
6. E - Cloudflare post-mortem, 18 Nov 2025: an internally generated configuration file doubled in size, the proxy hit a hard limit and failed
   network-wide for 5 h 46 min; first remediation: treat internally generated configuration "the same way" as user input; more kill switches.
   -> the organisation's own values pass type, range and step checks like untrusted input; one switch (`EXEC_ON`) stops the engine.
7. E - Google Cloud incident report, 12 Jun 2025: a policy with blank fields replicated worldwide in seconds into a code path with no flag and
   no error handling. Remediation: flags off by default, incremental roll-out with time to validate, fail open. -> one change at a time, a
   verification window before "verified", and a broken engine never throws away or blocks work that is already paid.
8. O - LaunchDarkly "guarded rollouts" documentation (read 10 Nov 2026): automatic rollback needs a minimum sample; with too little data at
   the end it rolls back; it suits metrics where "worse" is unambiguous. -> at one video a week statistics are impossible, so the engine ISOLATES
   (one unverified change per department) and uses the hard contract checks (pass / fail) as guardrails; no evidence in the window = rolled back.
9. E - reward hacking by coding agents: (a) SpecBench, arXiv 2605.21384, 21 May 2026: 97.8% on the visible tests against 83.3% on held-out tests
   (gap 14.5 points, growing with task size); (b) ImpossibleBench rates quoted in a 2026 safety report: 0-11.8% of runs change or game the tests;
   (c) METR: one model gamed the scorer in 39 of 128 runs, and telling it not to "had a nearly negligible effect". -> a code lever is verified
   by checks the build did not write, and the automatic merge is decided by code reading the real diff - never by the request or the prompt.
10. E - The Hacker News, 4 Jun 2026: flaw in the Claude Code GitHub Action (fixed in v1.0.94, CVSS 7.8): injected text could make the agent read the
   job's environment and leak its secrets; advice: a job that reads untrusted text holds no secret beyond the model credential and the workflow's
   own access. -> `claude-build.yml`: the Sheet, WhatsApp and merge secrets move off the step in which Claude Code runs.
11. O - optional stopping: Johari et al., arXiv 1512.04922, and simulations in practitioner write-ups (stopping at the first p < 0.05 gives about
   21-28% false positives instead of 5%). -> the engine never judges an experiment arm early; it verifies only that the arm is assigned and
   recorded, and the existing fixed rule (plays on both sides) gives the verdict.
12. E - Tang et al., "Holistic Configuration Management at Facebook", SOSP 2015: validators on every change, canary on a subset, automatic rollback.
13. O - the Kubernetes controller pattern (level-triggered reconciliation: a missed event is harmless because the next pass re-reads state).
   -> the engine's tick pass reads state (cells, Sessions, the ledger of checks), never an event queue; a killed job is settled by the next pass.
14. E - Zhang et al., "Darwin Goedel Machine", arXiv 2505.22954, 29 May 2025 (v3 12 Mar 2026): a self-modifying agent went from 20.0% to 50.0% on
   SWE-bench with sandboxing and human oversight. -> gated self-change works; the gate is the product.
Re-read: 02 points 2, 12, 14, 15 ("whatever they learn or brainstorm or decide ... strictly code line level executed and enforced"), 01 sections 4-7.

#### Step 2 CREATIVITY (4 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Immediate applier": apply by lever class, read back, mark verified. 2 / 2 / 5 / 2 / 4. Rejected: read-back proves the write, not the effect
  (source 1); nothing ever rolls back.
- B "Guarded roll-out": apply -> probation -> guardrail checks -> automatic rollback (sources 8, 12). 4 / 4 / 5 / 4 / 4. Taken as the core.
- C "Desired-state reconciler": a pass on every tick compares what should be with what is and converges (source 13). 3 / 4 / 4 / 5 / 4. Taken for
  crash-safety: the tick pass also settles an apply that a killed job left half done.
- D ORIGINAL, beyond the research - five rules for a system with ONE video a week and ONE owner:
  (1) isolation instead of statistics: at most one unverified setting or experiment per department, and settings change BETWEEN videos, never
      inside one - so one video's checks can be attributed to one change, and no script is judged against a bar it was not written for;
  (2) proof by somebody else: a change is verified only by rows another component wrote AFTER it (a later department run, a later video's check
      rows, a later Video_Features row, GitHub's own check runs) - the engine's own read-back is necessary, never sufficient;
  (3) the owner's hand wins: rollback is compare-and-swap; a cell the owner edited after the engine is never overwritten (source 3);
  (4) the direction decides who may turn a lever: inside its range a department moves a lever freely in the direction that makes a gate stricter
      or cheaper; the direction that weakens a gate or costs more needs the owner's one tap, pre-filled;
  (5) additive-only automatic merge: a build may ADD tests and rule data and nothing else; one deleted line, one protected file or no new test
      sends it to the owner (source 9).
  5 / 5 / 5 / 4 / 5.
Decision: B + C + D together.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/levers.py` (every lever: type, range, largest step, the direction that needs the owner, the checks that judge it; the
  scope of an automatic merge) and `whatifs/org/execute.py` (the engine). A ticket's free text (`acceptance_test`, `rollback`) is for people; the
  engine compiles `lever_class` + `target` + `value` into a typed operation with a registered verifier, or refuses the ticket with the reason.
- Tabs appended: `Tickets` (one row per ticket: the engine's state) and `Lever_Changes` (append-only: intent, applied, verified, rolled_back,
  refused, queued, owner_asked ... one row per event, written BEFORE and AFTER every change).
- States: queued -> (awaiting_owner) -> intent -> applied -> verified | rolled_back; refused; failed. Code lever: dispatched -> pr_open -> merged -> verified.
- Lever classes: A knowledge = a Palace item accepted with the Council's authority (the Palace's own gate refuses anybody else); verified when a
  later run of the target department was served it (and cited it once that department runs in `prompt` mode - B6); undo = retire / restore the old
  version. B setting = a registered cell, owner department only (`registry.may_change`), type / range / step, never a cell no code reads; applied
  between videos; verified by a video BORN after the change passing the lever's own checks; a failed check, a failed run or no evidence in the
  window = rollback. C experiment = a rulebook trial (`whatifs/playbook.py`: coin flip per video = holdout, plays on both sides before a verdict);
  the long video's features now record its arms; verified when the next N long videos carry the arm, or the trial was judged. D prompt rule = a
  Palace rule item (style / policy), bounded per department, otherwise as A. E code = a `build_request` from D12, the build workflow, checks,
  additive-only automatic merge or the owner's Merge tap, checks on the merge commit, at most 2 re-builds, then escalation.
- The reconcile pass runs on every tick (next to the SLA watchdog); D12 Operations gets its run (trigger `operate`) only when it has a ticket to
  execute. A ticket closes as `lever_verified` / `rolled_back` only when the ledger holds that row (`memos._proof_problem`).
- Waiting for evidence is not being late: once a change is applied the ticket's resolve clock moves to the end of its verification window
  (`memos.await_proof`, typed, bounded, needs the ledger row); the engine itself rolls back when that window ends.
- Checks: `decisions_executed` and `lever_verified`, both at the script gate (before picture money). They FAIL on a broken invariant (a decision
  with no ticket, a ticket closed without ledger proof, a change past its window with no verdict, a failed rollback, an overdue ticket nobody
  escalated) - never merely because the owner has not answered yet.
- Money: Rs 0 (no model call). Code builds run on the owner's Claude plan (Rs 0 API), at most 1 + 2 attempts per ticket.
- Rejected: executing the ticket's `acceptance_test` text (a self-written test is the thing sources 9 and 14 warn about); applying a setting in
  the EXECUTE step of an episode run (it would change the bar under a script already written); automatic revert of drift (it would fight the
  owner's hand edits); a department run for D12 on every tick (about 670 empty runs per two-week verification window).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/levers.py`: the lever table - 39 Settings cells (15 whole numbers, 6 decimals, 9 switches, 3 choices, 4 JSON maps, the publish days,
  the list of switched-off checks), each with type, range, largest step, the direction that needs the owner (28 of 39 have one) and the contract
  checks that judge it (22 of 39; the rest are judged by the next complete run of their department). `check`, `same`, `issues`, `owner_of`, `merge_scope`.
- NEW `whatifs/org/execute.py` (599 lines): `apply` (the runner's EXECUTE step), `engine_tick` + `reconcile` (the tick pass), the five lever classes as
  (plan, do, read-back, verify, undo), the owner's approval message and its answer, `decision_issues` / `lever_issues` (what the two checks judge).
- Tabs appended: `Tickets` (24 columns), `Lever_Changes` (12). 9 settings: EXEC_ON, EXEC_VERIFY_RUNS (3), EXEC_VERIFY_DAYS (14), EXEC_ARM_OUTPUTS (2),
  EXEC_RULES_PER_DEPT (12), EXEC_BUILD_RETRIES (2), EXEC_BUILD_WAIT_H (6), EXEC_AUTO_MERGE_ON (TRUE), EXEC_TICK_AT (auto).
- `whatifs/org/memos.py`: a ticket closes as `lever_verified` / `rolled_back` (a build request as `merged_verified`) only when the ledger holds that row
  with a proof for that ticket; only the engine may close them that way; `await_proof` (typed, needs the ledger row, at most 130 days).
- `whatifs/org/runner.py`: the engine is the default executor (`_engine`); with `EXEC_ON` = FALSE a ticket is escalated at once. `set_executor` is gone.
- `whatifs/org/registry.py`: D12 Operations is wired (`execute.py`, trigger `operate`; pending list 8 -> 7); the two new checks have owners (C, D12);
  `data_issues` includes the lever table.
- `whatifs/contract.py`: checks `decisions_executed` and `lever_verified`, both at the script gate: **43 hard checks (24 script + 19 final)**.
- `whatifs/builds.py` + `whatifs/cli.py` + `.github/workflows/claude-build.yml`: a build can carry its build request id; the real diff (`pr_files`) and
  the checks of any commit (`commit_state`) can be read; the workflow's Sheet, WhatsApp, owner and merge credentials moved from the whole job to its
  last step - the step in which Claude Code reads the spec now holds only its own model credential and the workflow's own repository access.
- `whatifs/manage.py` (tick: `EXE.engine_tick()` next to the watchdog), `whatifs/notify.py` (the approval answer is registered), `whatifs/episode.py`
  (the long video's features now record its experiment arms - they were always empty for long videos).
- `whatifs/truth.py`: two entries deleted, `UNWIRED_FUNCTIONS_MAX` 10 -> 8. `tools/repair.py` PROTECTED: + levers.py, execute.py, builds.py.
- Generated docs: SYSTEM.md section 12 (states, the five classes, the whole lever table). 5 matrix rows. 7 founding items `b4.*`: 118, 0 refused.
- `tools/rehearsal.py`: a Council decision with one knowledge ticket is written before the video and must end `verified` on the ledger.
- Changed against the design memo after seeing real behaviour: (1) proof names the exact item VERSION (an updated item was "verified" by a playbook
  that still held its old text); (2) a video that starts in the very second of a change counts as made after it; (3) the tick takes up new tickets
  of every wired department itself - a department that only runs inside a video would have seen its ticket a week late and the ticket would have
  climbed to the owner for a missed acknowledgement; (4) the tick records when it last finished and the check fails when tickets wait and that is a day
  old; (5) a merge whose checks never report is escalated, never reverted on a guess; (6) the automatic merge scope is narrower than the master
  spec's "tests + rules": NEW TEST FILES ONLY - rule data has its own lever (D) with verification and rollback, a build that edits it would bypass both;
  (7) `decisions_executed` says N/A, not PASS, while nothing has been decided: the sweep showed 40 videos each "passing" a check that had judged nothing;
  (8) found by GitHub, not by the laptop: "after the change" is judged to the second, and on a fast machine the next run of the department began in
  the very second of the change - it was skipped and the proof named a later run. Now a run that begins in that second counts, and the run that
  hands the ticket over is recorded (`Tickets.session`) and can never be the proof of its own ticket.
- Existing tests changed because their expectation changed BY DESIGN (say so in the final PR): `tests/test_v94a.py` (the model credential sits on
  the Claude step, not on the job), `tests/test_v12_org.py` (a ticket cannot be closed with a made-up reference any more; "no engine registered" is now
  "engine switched off"; D12 left the pending set; the registry fixture copies execute.py).

#### Step 5 ENFORCE (rule -> executing code -> fails when broken)
| Rule | Executes | Fails when broken |
|---|---|---|
| A ticket is compiled into a typed change or refused with the reason; its free text is never executed | `execute.apply`, `_start`, the five `_plan_*` | ticket rejected, ledger row `refused`, nothing written (tests: more than 20 refusal cases) |
| Intent before, applied + read-back after, then a verdict with its proof; rows only appended | `execute._start`, `_applied`, `_judge`, `_log` | `lever_verified` FAIL ("without an intent row", "verified without a proof", "rolled back without a ledger row") |
| Verified only by rows another component wrote after the change | `_verify_knowledge` (later run, exact version), `_verify_setting` (video made after, the lever's checks), `_verify_arm` (features of later videos), `_verify_build` (checks on the merge commit) | stays `applied`; no evidence inside the window = rollback |
| A department turns only its own registered lever, right type, inside range, one step, never a cell no code reads | `levers.check`, `registry.may_change` | refused before anything is written |
| The direction that weakens a gate, costs more or changes the plan waits for the owner's tap | `levers._owner_reason`, `execute._ask_owner`, `_on_answer` | state `awaiting_owner`, cell unchanged; ONE message |
| A setting / experiment changes between videos; one unverified change per department | `execute.idle`, `_start`, `_wait` | state `queued` with the reason (one ledger row per reason) |
| Rollback never overwrites the owner's later value | `execute._undo_setting` (compare and swap) | ledger `rollback_skipped`, cell untouched |
| A rollback that fails, or a build out of attempts, goes up at once and the owner hears | `execute._fail` -> `memos.escalate` -> watchdog | `lever_verified` FAIL; owner message (tests assert the message) |
| A ticket closes only on the ledger; only the engine closes it that way | `memos._proof_problem`, `memos._roles` | MemoError, memo unchanged |
| Waiting for proof is typed, bounded and needs the applied row | `memos.await_proof` | MemoError |
| Knowledge by lever needs the Council's authority, never the owner's words, must fit the playbook at once | `_plan_knowledge`, `palace.add`, `_present_knowledge` | refused; an item that does not fit is retired again at once |
| A department's rulebook is bounded | `_plan_knowledge` (`EXEC_RULES_PER_DEPT`) | refused |
| A code build merges by itself only when the real diff adds new test files and nothing else | `levers.merge_scope`, `execute._verify_build` | owner's Merge message with the reason (tests: 10 kinds of diff) |
| At most 1 + 2 builds; closed pull request, red main, silent main are never "done" | `execute._retry_build`, `_judge`, `_undo_build` | state `failed`, escalated |
| No credential on the step that reads the spec | `.github/workflows/claude-build.yml` | `tests/test_v12_exec.py` (job env, step env), `tests/test_safety.py` |
| Nothing decided stays text | `execute.decision_issues` | `decisions_executed` FAIL (no ticket, ghost ticket, forged close, late and nobody told) |
| The tick pass is alive | `execute.engine_tick` (`EXEC_TICK_AT`), `lever_issues` | `lever_verified` FAIL after a day; a test runs the REAL tick job and fails when the call is removed |
| The lever table is honest | `levers.issues` in `registry.data_issues` and in `lever_verified` | `python -m whatifs.org.runner` RED; check FAIL; tests |

#### Step 6 PROVE
- `tests/test_v12_exec.py`: **88 tests (46 functions)**, each rule both ways: 18 kinds of setting value refused; the direction rule for every lever
  type; a setting from queue to applied to verified with the exact ledger rows; rollback on the lever's own check (and NOT on another check); the
  owner's hand-typed value surviving a rollback; the window ending; the approval message word for word, asked once, Approve / Reject / approve while a
  video is being made; one unverified change per department; a ticket a person closes; an apply killed before and after the write; a rollback that
  fails (the owner hears); knowledge accepted, served, verified with the session named; a proposed takeaway accepted by the Council; a changed text
  restored; knowledge nobody is served retired again; a prompt-mode department must cite; 8 kinds of knowledge ticket refused; the bounded rulebook;
  an experiment arm from registration to the features of two later videos; an arm nobody carries retired; 4 kinds of arm refused; a code ticket to
  build request to dispatch to pull request to automatic merge to green main; outside the scope -> the owner, once; red checks -> two re-builds ->
  escalation; no pull request; red main -> revert build + escalation; silent main -> escalation, no revert; a closed pull request; 10 kinds of diff
  against the merge scope; the workflow file; the memo doorway; both checks with every FAIL condition; the real tick job; and the real pipeline
  twice (a knowledge ticket verified in the first video, a setting ticket applied in the gap and verified by the second video's retention check).
- Faults the tests and the re-reading found in the new code, all fixed (repair attempts: none reached 3): points (1) to (5) of step 4 "changed against the design
  memo" and the unnoticed removal of the tick call; plus two mistakes of my own on the way: a patch pasted through a shell here-document lost
  its backslashes, failed its own assertion and the UNPATCHED script reformatted the whole founding-knowledge file (restored from git, redone from a
  file - the warning under HOW TO RUN is right); and new founding items addressed to D1 and the Council pushed three more low-priority limits out of
  D1's playbook (audiences narrowed: D1 is back at 3; the Council went from 5 to 6, open issue 6).
- Live proof on the real repo: the engine's call removed from `manage.tick` -> the new wiring test fails (1 failed), restored -> passes. One lever rule
  deleted from `levers.py` -> `python -m whatifs.org.runner` RED naming it. NOTE: the truth scan stayed GREEN in the first case - it counts names and
  the name still appears in the rehearsal and in the docs generator; that is why the wiring test runs the real job.
- Fake rehearsal on the final code: **GREEN** - contract script 24 / 24, final 19 / 19; 9 department runs, 9 takeaways; the rehearsal's decision:
  ticket -> `intent > applied > verified`, proof "Sessions:... (D6 assets) ran after the change with PI-...@1 in its playbook".
- Full suite: **1201 passed / 0 failed / 1 skipped** (65 files, one uninterrupted run by itself on a frozen copy of the final code commit ad99fd2; the skipped
  test is the dashboard render, which needs node - GitHub runs it: 1202). An earlier full run (commit 822dfa3) had 1197 / 0 / 1 in 64 files and the 65th
  file stopped by the runner's 15-minute limit - my mistake: the sweep was running at the same time (by itself that file takes 477 s).
- Sweep (standing rule 2): on a frozen copy of 822dfa3 - A: 40 fixed ids, organisation ON: **40 ok, 0 held, 0 crashed** (each: status SCHEDULED, 9 department
  runs verified, 0 live memos, 0 owner messages, 0 degraded steps); B: 10 ids with ORG_ON = FALSE: **10 ok** (35 PASS + 8 N/A); C: 8 full rehearsals with
  a forced id: **8 ok** (status LIVE, 39 PASS + 4 N/A, the rehearsal's decision verified on the ledger in each). **58 of 58 green.** Warning classes: the
  same 9 in every episode and 1 in 1 of 40 as in B0b - none is new. The two later code commits (one status word of one check; the one-second rule of the
  verifier) each got a short sweep on its own frozen copy - 7f9e7fd: 4 + 1 + 2, ad99fd2: 3 + 3 rehearsals: **13 of 13 green** (organisation ON and
  nothing decided: 38 PASS + 5 N/A).
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (118 founding items). Organisation **GREEN**.
- GitHub Checks (standing rule 1): every commit of the batch read on the public run page. Runs 54, 55, 56 GREEN (56 = 822dfa3: 1201 passed, 0 skipped,
  rehearsal GREEN). **Run 57 (7f9e7fd): RED - 1 failed / 1200 passed**: this batch's own end-to-end test, at an assertion whose first part held
  (`'verified' == 'verified'`). Traced, not re-run (step 4, point 8): the proof named a later run than the test expected, because the next run of the
  department had begun in the same clock second as the change. Honest limit of that diagnosis: the public run page shows only the first line of the
  assertion (log lines need a sign-in); the failing part is INFERRED - it is the only part of that assertion that depends on timing - and the
  mechanism is reproduced in `test_a_later_run_in_the_very_second_of_the_change_counts...`, which fails on the old code. Run 58 (e362042: the same
  code + one CLAUDE.md recipe) GREEN half an hour later - the fault is a matter of milliseconds. **Run 59 (ad99fd2, the final code commit, with the fix and a test that fails on the old code): GREEN - 1202 passed,
  0 skipped, rehearsal GREEN (episode id EP202611101921, script 24 / 24, final 19 / 19).** The one warning on every run page is GitHub's own (Node.js 20
  deprecated for `actions/setup-node@v4`; open issue 37).
- Money: Rs 0 added (no model call). Not measured in production: nothing is live until the final PR.

#### Step 7 TAKEAWAY (also Palace item `b4.takeaway`)
- WORKED: asking of every proof "who wrote it, and when?". The first verifier accepted a playbook holding the OLD text of an item and would have
  called an unchanged department "verified". Proof now names the version, the session and the playbook.
- WORKED: re-reading the finished engine as a stranger before the long runs. It found the three faults no test had asked about: the week-long wait of
  a ticket for a department that only runs inside a video, the blind revert of a healthy merge, and the dead tick nobody would have noticed.
- WORKED: testing the silence again (B3's lesson): every state that waits now has a clock that ends, and every end has somebody who is told.
- WORKED: standing rules 1 and 2. GitHub's faster machine failed ONE test once (run 57) that the laptop, the 58-run sweep and the runs before and
  after it all passed. Traced from the public run page alone to a one-second ordering rule, reproduced in a test, fixed. The run after it was green
  on the SAME code: had the red run been re-run instead of traced, the fault would have gone into production as "flaky".
- WATCH: until the Council exists (B6) NO real ticket is written. The engine is proven by tests and the rehearsal; it changes no video by itself.
- WATCH: "served" is the proof for knowledge and rules today; "cited" arrives when B6 puts playbooks into prompts (the verifier already demands it then).
- WATCH: the code lever has never touched the real GitHub (no keys on this laptop, by rule): the diff reader, the checks on the merge commit and the
  changed workflow file are proven with stand-ins and by reading. The first organisation build must be watched (open issue 29).
- WATCH: at one video a week a setting change takes about a week to verify and a failed check rolls it back even when the script was simply weak.
  That is the price of isolation; the Council will see "rolled back: EP... failed <check>" and may ask again.
- WATCH: a name-count scan cannot protect a wiring with a common name. For every new hook: one test that runs the real job.

### B0b - Baseline re-check (10 Nov 2026) - ACCEPTED (final code commit 9c5d0e3 GREEN in GitHub run 52)
Result in one line: the code the build stands on was re-proven the hard way - 58 full fake pipelines over fixed episode ids are green - and the real
faults turned out to sit in the PROOF, not in the pipeline: a comparison that ran on no machine, GitHub's Checks measuring another major version of
OpenCV than production, red runs nobody could read, and features that were built or promised but never wired. All four classes are now refused by
code. Honest limits: nothing here changes a video; the never-wired features are listed and marked, NOT built (open issues 22-25; the owner decided
on 10 Nov that the largest one, the room value test, is to be BUILT in B8).
No new feature, so no seven-step loop; the six steps of the B0b plan are recorded instead, plus the research behind the new rules.

#### Step 1 - GitHub Checks read for every commit since the baseline
- Runs 42, 43, 44 (B3's three last commits): GREEN. Run 45 (the sweep tool): GREEN.
- Run 38 (B2 final, red at the rehearsal step): CAUSE CONFIRMED without a sign-in. The rehearsal step started at 11:11:33 UTC, the rehearsal names
  its episode by the minute, and on the old B2 code `tools/sweep.py --mode rehearsal --ids EP202611101111` is HELD by `promise_paid` ("promise first
  shown at 44.7 s (limit 30 s)") and then dies on `r["master"]`, exactly a red rehearsal; the ids of 11:12 and 11:13 pass. It is the stale promise
  flag B3 fixed. On the NEW code the same id passes both gates (35 checks PASS, no FAIL, status SCHEDULED).
- Runs 27, 30, 32: red at unit tests, already explained (before B0's fixes; the two mid-batch commits of B1 / B1b).
- Runs 46, 47, 48: RED at unit tests BECAUSE THE NEW RULE WORKED - the first runs in which the reference-frame comparison really ran on GitHub. Their
  annotation named the cause in one line: OpenCV 5.0.0 on GitHub, 36 of 36 frames differ (step 3 below). Run 49, the first with the library pin (step 5): GREEN - 1111 passed, 0 skipped, rehearsal GREEN. Runs 50, 51, 52: GREEN.

#### Step 2 - the sweep (`tools/sweep.py`, kept tool)
- One process per id (module state never leaks), fixed future-dated ids `EP2099MMDDHHMM` that are the same on every machine, one RESULT line per id
  with the outcome, failed checks + evidence, warning classes, degraded steps, owner messages and the organisation's runs; a work folder inside the
  repo is refused; episode folders are deleted after each id (117 MB each).
- A: 40 ids, organisation ON: **40 ok, 0 held, 0 crashed**. Every id: status SCHEDULED, 37 checks PASS + 4 N/A, 9 department runs all verified, 0 live
  memos, 0 owner messages, 0 degraded steps.
- B: 10 ids with ORG_ON = FALSE (the old path): **10 ok, 0 held, 0 crashed** (35 PASS + 6 N/A: the two organisation checks are N/A by design when the organisation is off).
- C: 9 full rehearsals with a forced id (the path GitHub runs): **8 of 8 fixed ids ok** (status LIVE, 37 PASS + 4 N/A, every assertion of the rehearsal holds).
  The ninth run was the id of run 38's minute on the NEW code: it passes both gates (it was held on the old code); the rehearsal then stops on its own
  assertion that the two organisation checks PASS, which cannot hold for an id dated before the organisation started on the Sheet (N/A by design).
  Counted as explained, not as green: 40 + 10 + 8 = 58 green pipelines.
- Warning classes: 9 appear in every episode and 1 in 1 of 40, all traced (step 3). None depends on the id.

#### Step 3 - every class traced to its cause
| Class | Cause | Verdict / action |
|---|---|---|
| JUDGE / WITNESS "no checked voice available" (every id) | the sweep recipe runs no voice lab, so tab Voice_Check is empty | recipe artifact; the fallback to the default prebuilt voice is the designed one |
| "script length ... adjusting", "retention gate ... / fix did not reduce", "Showrunner's premise was not one of the scored pitches" (every id) | the canned fake replies (a 158-word script, a premise outside the pitch list) | fake-data artifacts; each is a guarded fallback, and the HARD checks judge the final script (`retention` PASS on all 40) |
| "atmosphere over its time budget (153% > 30%) - particles switched off" (every id; fog too on 1 id) | the time valve `ATMOSPHERE_MAX_OVERHEAD_PCT`: in the SMALL fake render the rest of the frame work is tiny, so the share is always over | by design, logged, stored in `Episodes.atmos_json`; whether it trips at full size can only be seen on the first real render (open issue 26) |
| "prompt cache: two calls share a prefix but differ in model parameters" (every id, twice) | REAL: `CACHE_ALIGN_EFFORT` (default TRUE) is read by no code; `models.aligned_effort` was tested but never called in any version | measured on one fake episode: 21 calls, 44,006 tokens read from cache, 14,538 written, hit ratio 0.75; the two misses cost about one extra cache write each, an estimated Rs 3-10 a video (NOT measured in production). Not wired now, because aligning efforts would LOWER or raise the effort of a creative or judging call (breakout first); cell marked NOT ACTIVE; open issue 23 |
That one real class led to a scan of the whole table, and then of tabs and functions:
- **8 of 691 Settings cells are read by no code, in any version ever pushed**: `CACHE_ALIGN_EFFORT`; `ROOM_VALUE_ON` (default TRUE), `ROOM_VALUE_EVERY`,
  `ROOM_MIN_WINRATE` - the blind test "writers' room script against a single-prompt script", with its own tab, about Rs 15 a video, was NEVER BUILT;
  `RUNTIME_HARD_MAX_SEC` (the code enforces `RUNTIME_MAX_SEC`); `PKG_VARIANT_C_IMAGE`; `VIEWER_NAME_ON_SCREEN` (no code shows a name, so the safe
  default is what happens); `PREMISE_BENCH_MAIL_MONTH`.
- **2 of 78 tabs are used by no code**: `Room_Value`, `Repairs`. **10 of 1,404 functions are called by no production code**: `models.aligned_effort`,
  `show.bible_issues` (the check of the character bible for protected names, real people and child characters - only tests call it),
  `enforce.fix_markers`, `enforce.fix_retention`, `prompts.episode_pack`, `publish.meta_bio`, `data.ptype_for`, `shotplan.prompt_variety`, and the two
  hooks B4 will call (`registry.may_change`, `runner.set_executor`).
- What was done about them now: each is listed in `whatifs/truth.py` with what is TRUE today, the 8 cell notes start with "NOT ACTIVE (no code reads this
  cell)" and SYSTEM.md section 4 prints all three lists, so no chat and no owner is told a behaviour exists that does not. What was NOT done: none of
  them was built or wired in this batch (each needs its department's batch or an owner word - open issues 22-25).
- Known candidates of the plan: open issue 1 measured (below); open issue 16 not triggered by any id (stays with B7); open issue 20 closed by the
  episode-id trace (step 4).
- Open issue 1 measured: world particles at real 1080p, 12 seeds x 4 worlds, one 4-second shot each: 43 of 48 shots read 100% alive, the lowest are
  rain 57% / 71% / 86% and embers 71%; dust and wind 100% on all seeds. No id of the sweep failed `aliveness`. The per-shot guarantee is still missing.

#### Step 4 - the tests the laptop skipped (6)
| Test | Did GitHub run it? | Now |
|---|---|---|
| `test_safety` restore step (python-docx) | yes | python-docx installed in the venv; the test now also uses the interpreter that runs it (it called whatever `python` was first on PATH) |
| `test_v94b` dashboard render (node) | yes | still skipped on the laptop (node not installed; not worth an install - GitHub runs it) |
| `test_v91_core` + 2 in `test_v91_matrix`: the picture equals the reference frames | **NO - on no machine** | always compared now, see below |
| `test_v87` mirror files of the old upload package | **NO - on no machine** (the folder exists nowhere) | removed, with the dead branch of one `test_v89` test |
- The reference-frame comparison skipped wherever OpenCV / NumPy differed from the versions the file was made with (4.13.0 / 2.4.4) - and production
  and Checks pin NumPy below 2.1. 22 more comparisons in `test_each_flag_alone` and one in `test_v91_atmos` were switched off by the same guard without
  even counting as skipped. Forced to run with the original versions on this laptop: **25 failures, 36 of 36 frames differ**. Bisected: the commit
  that added the file matches on Windows too (so the frames are identical across Linux and Windows), live `main` matches, the handoff snapshot does not;
  with `PARTICLES_ON` = FALSE the current code matches again on 4.13.0 / 2.4.4 AND on 4.14.0 / 2.0.2. So: NO regression in the base renderer; the
  particle layer (on by default, intended) is the whole difference; and the version guard had been hiding that the promise "all switches off = the old
  picture" was unchecked. Now: `tests/golden_frames.py` `v9_baseline` (later layers off) + `same_as_v9` (never skips; the message says whether the code
  or an unverified library version is the suspect); a new default-on render layer fails it until its switch is listed.
- The no-skip rule: `tests/skip_policy.py` + `tests/conftest.py` + `WI_NO_SKIPS=1` in the Checks workflow. Proven with real pytest on this laptop both
  ways: the file with the node test exits 1 and names the test on a strict run, exits 0 on a normal run; files without a skip exit 0 on a strict run.
- A red run names its cause in public: `tools/ci_report.py` after the unit tests and after the rehearsal writes annotations + an uncapped job summary
  (failed and skipped tests, failed contract checks with the reason, the last error line, the episode ids a failed test printed, and the command that
  reproduces a red rehearsal). The step still ends with the tests' own exit code.

#### Step 5 - B0's two fixes on Linux, and what GitHub was really measuring
- `whatifs/reels.py` (Windows-only path lines) and `whatifs/render.py` (particle seed): GitHub run 28 (B0 final) and every later unit-test step are green on
  Linux, the particle test included.
- FOUND by the first annotated run: `pip install opencv-python-headless` without bounds in the Checks workflow installs **OpenCV 5.0.0**, while
  `requirements.txt` (production) pins `>=4.9,<5`. Every green GitHub run of B0-B3 was therefore measured on another major version than the one that
  renders the videos; with 5.0.0 all 36 reference frames differ. Fixed at the root: all 13 workflow pip lines that name a pinned package now carry the
  bounds of `requirements.txt` (OpenCV in 4 workflows, plus pillow, requests, soundfile); a test fails on any line that does not, and another fails when
  the installed or imported version on the test machine is outside the pins. The pipeline's own jobs install from `requirements.txt` and were always right.

#### Research behind the new rules (dated sources; E = measured, O = official / practice)
1. E - Kim, Chen et al., "How Disabled Tests Manifest in Test Maintainability Challenges?", ESEC/FSE 2021: 122,000 commits, 15 systems; 41% of disabled
   tests never come back, most stay disabled for years. -> no test may skip where acceptance is decided.
2. E - Dutta et al., "Detecting Flaky Tests in Probabilistic and Machine Learning Applications" (FLASH), ISSTA 2020: running tests under many seeds found
   11 new flaky tests in 20 projects. -> the sweep over fixed ids.
3. E - Dutta et al., "To Seed or Not to Seed?", ICST 2022: 114 projects; fixing one seed is a workaround that hides the failing seeds. -> the rehearsal
   keeps its time-based id, and the id is printed so a failure is reproduced, not re-run away.
4. E - Parry et al., "Systemic Flakiness", EASE 2025 (arXiv 2504.16777): 810 flaky tests; failures cluster around shared causes. -> one cause (the promise
   flag) explained both B3's held test and run 38; trace the cluster, not the single red.
5. E - Chen et al., arXiv 2502.02760 (Feb 2025): randomised hash order exposes implementation-dependent flakiness. -> same class as B0's particle seed.
6. O - GitHub Docs, workflow commands (read 10 Nov 2026): error / notice annotations, job summaries (20 step summaries a job); GitHub community
   discussion 68471: 10 error annotations a step, the rest dropped silently. -> 8 causes + "and N more" + totals, full list in the job summary.
7. O - Flutter golden-file guide and others: reference images are compared on one defined platform, usually with a tolerance. -> measured here instead
   of assumed: the frames are bit-identical on two systems and two version pairs, so the comparison stays exact, and the failure message names an
   unverified library version as the first suspect.

#### What changed (code)
- NEW `tools/sweep.py`, `tools/ci_report.py`, `tests/skip_policy.py`, `tests/test_v12_b0b.py` (20 tests).
- `whatifs/truth.py`: `settings_issues` / `unread_settings`, `wiring_issues` / `unused`, the three shrinking lists; all three run inside `truth.issues`, so
  Plan Guard, the tests and contract check `docs_current` enforce them. `tools/gen_docs.py`: SYSTEM.md section 4 prints the lists.
- `whatifs/core.py`: 10 notes reworded (the 8 dead cells + one stale cadence note + the safe-mode note); NO default value changed.
- `.github/workflows/`: Checks runs strict + reports (2 steps); 13 pip lines pinned like `requirements.txt`.
- Tests: `tests/golden_frames.py`, `test_v91_core`, `test_v91_matrix`, `test_v91_atmos` (always compare), `test_v87` (-1 dead test), `test_v89`, `test_safety`,
  `tests/conftest.py` (skips, episode ids of failed tests). `tests/golden/v9_render_frames.json`: verified versions recorded.
- 8 matrix rows; 6 founding Palace items `b0b.*` + the owner's decision `owner.room_value_test` (111 items, 0 refused; build rules entered as techniques for D12 / D8 so that no limit was pushed out
  of a playbook - the first try as policy rules pushed out 8).
- Laptop venv: + python-docx, + pytest 9.2 (real pytest for single files: `../.venv/Scripts/python.exe -m pytest tests/<file> -q`; the stand-in runner
  still wins when PYTHONPATH points at the shim).

#### Proof
- Each new rule both ways, live on the real repo: a Settings cell nothing reads -> Plan Guard RED, check `docs_current` FAIL, test file 12 / 1; a function
  nothing calls -> Plan Guard RED; files restored -> GREEN. The particle layer left on -> the reference comparison FAILS (a kept test). A strict run with
  a skip -> exit 1 (real pytest). A failed test under real pytest prints its `EPISODE-IDS` line.
- Mistakes of my own on the way (repair attempts, none reached 3): the first sweep chain was started behind a failed clean-up command and ran on the
  working tree (stopped, restarted on a frozen copy of the commit); `tools/ci_report.py` was broken twice by a shell that eats backslashes in pasted
  code (now only written through the file tools); the settings scan first counted its own list as a reader; 4 truth tests failed on a fixture without
  a settings table.
- Laptop, final code: full suite (64 files), ONE uninterrupted run with the stand-in runner: **1113 passed / 0 failed / 1 skipped** (1088 before; + 20 in
  `test_v12_b0b`, + 1 live test of the reference comparison, + 4 that used to skip and now run). The 1 skip is the dashboard render test (node), which GitHub runs.
- Fake rehearsal on the final code: **GREEN** - episode id EP202611101515, contract script 22 / 22, final 19 / 19. Plan Guard GREEN (truth scan included), Palace GREEN
  (111 founding items, 0 refused), SYSTEM.md regenerated, no drift.
- GitHub: final code commit 9c5d0e3 = run 52: **GREEN** - 1114 passed, 0 skipped (real pytest, Ubuntu, OpenCV under 5), rehearsal GREEN with episode
  id EP202611101504 (22 / 22 + 19 / 19) - read from the public annotations, no sign-in. Runs 49, 50, 51 GREEN too; runs 46, 47, 48 RED for the one
  explained cause (OpenCV 5.0.0 before the pin). The commit that adds this record changes this file only (run 53): a record cannot contain its own
  run, so the next session reads run 53 before it starts B4.
- Money: Rs 0 (no model call, no paid step). Nothing is live until the final PR.

#### Takeaway (also Palace item `b0b.takeaway`)
- WORKED: making the failure readable first. The first run whose failures were written onto the public page showed in one glance what four batches of
  green had hidden (OpenCV 5 on GitHub). Before trusting any proof, ask where it really runs and whether it can skip.
- WORKED: following ONE warning to its cause instead of classing it as noise. The prompt-cache line led to a cell nothing reads, that to a scan of every
  cell, tab and function, and that to a paid test that was never built.
- WORKED: bisecting with the original library versions instead of regenerating the reference frames. Regenerating would have signed off the unknown.
- WATCH: "listed and marked" is not "built". Open issues 22-25 are real gaps; the lists only stop them from growing and from being believed.
- WATCH: the sweep is fake mode. It proves the plumbing for many ids, not the taste of a real script; and the time valve of the atmosphere always trips
  in the small render, so the full set of layers is never rehearsed past frame 120.
- WATCH: knowledge items written as limits push other limits out of the 1,800-token playbooks at once (seen and undone here; open issue 6 stands).

### B3 - Memo system + Department contract (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: the project now runs like an organisation at the level of code - every step of the long video that belongs to a department, and the
daily learning job, goes through LOAD -> ACT -> EMIT -> LEARN -> EXECUTE -> REPORT with a proof per step; departments talk through validated memos with
deadlines that escalate to the owner; a failed check or a crashed step becomes a problem memo for the department that owns it; two new HARD checks hold
the video when a department walks around the contract. Honest limits: 7 of 15 departments are wired (8 are pending by plan); the playbook is HANDED to
each run but is not yet inside any model prompt (B6), so B3 by itself changes no video; no ticket can be executed until B4.

#### Step 1 RESEARCH (11 dated sources; E = measured evidence, O = opinion / practice / official guidance)
1. E - Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (MAST), arXiv 2503.13657, 17 Mar 2025 (v3 26 Oct 2025, NeurIPS 2025): 1,600+ annotated
   traces, 7 frameworks, 14 failure modes. Largest: step repetition 15.7%, reasoning-action mismatch 13.2%, unaware of termination conditions 12.4%,
   disobey task specification 11.8%; verification failures together 23.5%; "ignored other agent's input" 1.9%, "fail to ask for clarification" 6.8%.
   Better role prompts gave +9.4%, an added verification step +15.6%, and the authors say prompt fixes are inconsistent and the cause is
   organisational design, not the model. -> the six steps are a state machine in CODE with a proof per step; nothing relies on a prompt saying "follow the steps".
2. E - Wang et al., "The Unreliable Progress Bar", arXiv 2609.08589, 8 Sep 2026: models report their own task progress unreliably while work is under
   way; "frameworks should not control task flow on the strength of the model's state reports alone". -> a memo or a step changes state only on
   evidence that code observed (ids returned by the store, a cost counter, a ledger row), never on a claim.
3. E - Wang, Goyal, Chandrasekharan, Sundaram, "Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM Handoffs", arXiv 2608.29028,
   29 Aug 2026: a compressed handoff keeps the facts and loses the rules about how they may be used (boundary survival 0.80 -> 0.57 at a 25-word
   budget while facts stay near ceiling); vague boundary wording leaked in 73% / 50% of cases, explicit constraints under 15%, a typed audience
   allowlist nearly zero. -> a memo carries a typed audience list enforced by code on read and a `constraints` list that is never shortened.
4. E - Dubey, "Real-Time Detection and Repair of LLM Agent Failures", arXiv 2608.02464, 3 Aug 2026 (2,823 episodes): a deterministic verification
   layer (recompute stated totals from tool results, check required calls) caught 60% of failures, 96% with a coverage check, 0 false positives;
   roll back + re-run recovered 45% vs 16%. -> the runner recomputes cost and counts itself and runs a coverage check: every inbound memo that was
   loaded must be dispositioned.
5. E - Dennis et al., "In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks", arXiv 2604.27891, 30 Apr 2026: an external
   orchestrator graph failed 9-24% of conversations against 0.5-11.5% for one prompt holding the whole procedure. -> departments are code wrappers;
   the organisation adds NO model hop; knowledge goes into the existing call's context (and Rs 0).
6. O/official - Anthropic, "How we built our multi-agent research system", 13 Jun 2025: a delegated task needs an objective, an output format,
   tool guidance and clear boundaries; multi-agent runs cost about 15x a chat; resume from a checkpoint instead of restarting; pass artifacts by
   reference. -> every asking memo needs `subject` + `done_when` + `constraints`; bodies are small and link to artifacts; each run leaves a durable row at start.
7. O/official - PagerDuty escalation policy docs (read 10 Nov 2026): not acknowledged inside the timeout -> next level; acknowledging halts
   escalation but does not resolve; a policy repeats a bounded number of times (9) and then stops. -> two clocks per memo (acknowledge, resolve),
   a ladder as data, bounded owner reminders.
8. O/official - A2A Protocol specification 1.0.0 (a2a-protocol.org, read 10 Nov 2026): task states submitted / working / input-required /
   auth-required / completed / failed / canceled / rejected; a task in a terminal state accepts no further message; the sender's message id is used
   to detect duplicates. -> memo statuses and legal moves are data; a terminal memo is immutable; a recurrence is a new, linked memo.
9. O/practice - Richardson, "Transactional outbox" (microservices.io, read 10 Nov 2026): a relay can publish the same message twice, so the
   consumer must be idempotent. -> a Sheet has no transaction, so the memo id is the hash of (type, sender, audience, dedupe key): writing it twice is a no-op.
10. E - Yin et al., "From Reflection to Co-Evolution: Self-Evolving Agents with Locally Verified Memory" (Anchor), arXiv 2611.10382, 7 Nov 2026:
    most self-written lessons barely change a decision and some reinforce the wrong action; admitting only verified ones gave up to +19.9% success
    with 41% fewer stored memories. And E - Asadolahi et al., "Memory Reward Inflation in Self-Improving LLM Agents", arXiv 2608.00017, 29 Jun 2026:
    self-graded memories inflate and a judge with correlated errors cannot fix it. -> a takeaway cannot score itself, is built on measured outcomes,
    enters the Palace only as `proposed`, and only when it is new (a confirmation is counted, not stored again).
11. E (numbers from secondary summaries, not re-checked against the paper) - Hong et al., MetaGPT, arXiv 2308.00352 (2023, ICLR 2024): structured
    documents and subscriptions instead of free dialogue raised executability (reported 3.75 of 4). -> departments subscribe to memo types.
Not established by any source found: a controlled study that isolates typed schema validation of handoffs (only vendor claims exist); and what SLA
lengths are best for an automated content organisation - the hours below are a design choice taken from the master spec, to be tuned by D1 later.

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Spec-literal": a Memos tab with a JSON body, `write / ack / resolve`, a watchdog that flips overdue rows to escalated, a runner that calls six
  functions in order. 2/2/5/3/5 = 17. Weak: "the step ran" is proven only by the call; a re-run duplicates memos; a takeaway can be boilerplate;
  nothing stops production from calling the old module directly; a raise after the upload step could cause a second upload on the retry.
- B "Research stack": typed schemas, statuses and moves as data, two clocks + bounded ladder, hashed idempotent ids, deterministic verification
  with a coverage check, delegation fields, boundary fields, takeaways gated by measurement. 3/4/5/4/5 = 21. Weak: still a wrapper production can
  walk around; "a takeaway every run" floods the Palace; escalation would wait on departments that do not exist yet.
- C "The receipt chain" (ORIGINAL, on B's mechanics):
  1. Receipts, not claims: the proof of each step is assembled by the runner from what code observed and hash-chained in order; a run is complete
     only with all six links; the gate re-computes the chain.
  2. Never lose paid or irreversible work (my own rule, from reading the upload path): before ACT the runner is strict (it raises before any money);
     after ACT a failed step becomes a recorded BREACH and the result of ACT is still returned - the gate, not an exception, then holds the video.
  3. The episode gate judges the organisation: HARD checks `dept_contract` (script stage, before picture money) and `takeaways_written` (final stage,
     before upload).
  4. Escalation never waits on a department that cannot act: the ladder department -> Council -> owner skips every holder that has no wired entry
     point, computed from the registry, so the Council is skipped until B6 wires it and joins by itself afterwards.
  5. An honest registry: a department either names real call sites that run under the runner (verified by reading the code) or is listed as
     pending with its batch; the pending list can only shrink and SYSTEM.md prints it.
  6. Measured takeaways with a novelty gate: built from the run's measured outcomes against the department's own history; only a deviation or a
     failure is proposed to the Palace; a confirmation is counted. Model-written lessons join in B6 / B8 through the same validator.
  7. Boundaries travel verbatim: audience allowlist enforced on read, constraints never shortened (too long = refused on write), ONE render function.
  8. Two clocks plus attempts: a third failed attempt escalates at once; a terminal memo is immutable; a recurrence opens a linked successor.
  9. One tap at the one model doorway (`models.ask`): counts a run's model calls and, for a department in "prompt" mode, puts the playbook into the
     cached layer of the system prompt and proves it was there. B3 wraps the real departments in "brief" mode (behaviour unchanged, as the plan
     orders); B6 flips the creative ones to "prompt" in the registry.
  4/5/5/4/5 = 23.
- DECISION: C.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/schemas.py` (memo types, bodies, SLA clocks, statuses and moves as data; real JSON Schema output; a small validator, no
  new dependency), `whatifs/org/memos.py` (write / inbox / ack / start / resolve / reject / escalate / watchdog / render), `whatifs/org/registry.py`
  (15 departments: mission, wrapped modules, cadence, levers, monthly thinking cap, subscriptions, owned checks, wired entry points or pending batch),
  `whatifs/org/runner.py` (`run` = strict six steps; `work` = the wrapper for existing production call sites). Tabs appended: `Memos`, `Sessions`,
  `Takeaways`, `Org_Audit` (`Tickets` and `Lever_Changes` arrive with the Execution Engine in B4; a ticket is already a validated memo type).
- Wrapped in B3 (behaviour unchanged; 9 call sites in `whatifs/episode.py`, 1 in `whatifs/cli.py`): D4 write, D7 voice, D5 package, D6 plan,
  D8 script gate, D6 assets, D6 render, D8 final gate, D9 publish; D10 daily learning. The SLA watchdog runs on every tick.
  Pending by plan: D0, D1 (B9), D2, D3 (B5), D11, D12 (B4 / B7), Council (B6), Librarian (B8).
- Memo traffic that is real after B3: problem memos (a department run that crashed -> D12; a failed contract check -> the department that owns the
  check), resolved by code when the same check passes again, the owner waives it or the episode is closed; takeaways from every run.
- EXECUTE in B3: the step always runs and reads the department's open tickets; with no engine registered a ticket is escalated at once with the
  reason (never left as text). B4 registers `execute.apply`.
- Money: Rs 0 (no model call is added). Monthly thinking caps per department are data now and enforced by the runner for runs that declare
  `budget="org"` (P0 continues, P1 / P2 wait - master spec section 9); the paid organisation calls themselves arrive in B5 / B6.
- Sheet traffic per run: about 4 reads and 4 writes; 9 runs per episode.
- Rejected: a JSON Schema library (new dependency for a subset we can validate in 60 lines); wrapping inside `room.py` / `publish.py` themselves
  (every test and side path would change behaviour at once - call sites first, the rest per department batch); a model-written takeaway per run
  now (about Rs 0.5 each and exactly the unverified self-lesson sources 10 warn about); raising on a bookkeeping error after ACT (double-upload risk);
  one owner message per stuck memo (noise - one grouped message, bounded reminders).
- Enforcement plan and tests: steps 5-6 (each rule both ways; the acceptance tests of the plan: a run without takeaway / without playbook
  injection / with an invalid memo FAILS; SLA escalation).
- Palace seed items: `whatifs/org/seed/build.json`, keys `b3.*`, written in step 4 once the code they point at exists (the write gate refuses a
  reference to code that is not there).

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/schemas.py` (11 memo types as data: sender, audience, body, two clocks, statuses, legal moves, kinds of proof; a validator for the
  JSON Schema subset used; `json_schema(type)` gives the real schema; `check_memo`, `check_takeaway`), `whatifs/org/memos.py` (write / inbox / ack /
  start / resolve / reject / escalate / watchdog / sweep_episodes / render / stats), `whatifs/org/registry.py` (15 departments: mission, wrapped modules,
  rhythm, levers, thinking cap, wired call sites or pending batch, runs each gate needs, owner of each of the 41 checks), `whatifs/org/runner.py`
  (`run`, `work`, `verify`, `episode_issues`, `build_takeaway`, `audit`, `daily_check`, `health`; by hand: `python -m whatifs.org.runner`),
  `whatifs/org/wraps.py` (measures of each wrapped step, gate memos and their settlement).
- Tabs appended: `Memos` (30 columns), `Sessions` (21), `Takeaways` (16), `Org_Audit` (20). 9 settings: ORG_ON, ORG_SINCE, ORG_SLA_HOURS,
  ORG_ESCALATE_HOURS, ORG_OWNER_REMINDS_MAX (2), ORG_DEVIATION_PCT (25), ORG_CAPS_INR, ORG_RUN_STALE_H (6), ORG_WATCHDOG_AT.
- Two taps, each a few lines in a protected file: `models.ASK_TAPS` (every text call passes `models.ask`; the runner counts a run's calls and, in
  "prompt" mode, puts the playbook into the cached layer of the system prompt) and `core.COST_TAPS` (every logged cost is attributed to the run in flight).
- Production wiring: 9 call sites in `whatifs/episode.py` (D4 write, D7 voice, D5 package, D6 plan, D8 script_gate, D6 assets, D6 render, D8 final_gate,
  D9 publish) and the daily learning job in `whatifs/cli.py` (D10 daily) now run through `runner.work`; the SLA watchdog and the check for runs that
  never reported run on every tick (`manage.tick`); Setup and the first run mark when the organisation started on a Sheet (`ORG_SINCE`); the owner's
  answer to a stuck-item message is registered with the owner messages (`notify._ensure_handlers`).
- Checks: `dept_contract` (script stage) and `takeaways_written` (final stage): 41 HARD checks now (22 script + 19 final).
- Founding knowledge: 12 new items `b3.*` in `whatifs/org/seed/build.json` (11 research-backed + the takeaway): 104 founding items, 0 refused.
- Generated docs: SYSTEM.md section 11 (the six steps, the department table with wired / pending, memo types with clocks and kinds of proof, check owners).
- Changed against the design memo after seeing real behaviour: (1) a memo that asks for work is visible to the owner by default - the first deadline
  test showed a stuck memo reaching the owner's level and no message going out; (2) the runner settles the memos it wrote about a department's own
  crashes and breaches itself (a clean run of the same step is the proof) - otherwise a department's own breach memo blocked its next run; (3) one
  breach memo per CLASS (department, step, broken step), carrying no episode, so an episode going live can never close a broken contract.
- FIX of an existing fault found on the way (not organisation code; say so in the final PR): `whatifs/anim.py` - when the Animation Director moved the
  animated scenes, the `promise` flag stayed on a shot it had turned into a still; the re-aim in `episode.produce` was then skipped and `promise_paid`
  HELD THE FINISHED VIDEO at the final gate, after the picture money ("promise first shown at 43.7 s"). It depended on where the room had put its first
  animated scene, i.e. on the episode. Found because the new end-to-end test was held on one run out of four; reproduced with a fixed episode id with
  the organisation ON and OFF (same hold); now the flag leaves with the demotion and that episode passes with the promise at 0.3 s.

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| Six steps, in order, each with a receipt built by the runner and chained | `runner.run`, `runner._Run.receipt` | ContractBreach at the step; `runner.verify` -> `dept_contract` / `takeaways_written` FAIL |
| LOAD before any work: inbound memos acknowledged, a non-empty playbook from the Palace | `runner.run` (LOAD) | ContractBreach before ACT is called (also for `work`): nothing spent |
| The playbook reaches the work (brief: taken; prompt: inside a model prompt of the run) | `Brief.take`, `runner._ask_tap` | breach "no playbook injection" |
| A run may cite only Palace items its playbook served | `runner.run` (ACT) | breach "not in its playbook" |
| Every outbound memo valid or none is sent; every inbound memo dispositioned | `schemas.check_memo`, `runner.run` (EMIT) | breach "invalid memo" / "loaded and ignored" |
| At least one valid takeaway per run; stock, empty, ungrounded or self-scored refused | `schemas.check_takeaway`, `runner.build_takeaway` | breach at LEARN; `takeaways_written` FAIL |
| Only a new finding is proposed to the Palace, as `proposed`, one item per class | `runner._propose` -> `palace.add` | tests; the Palace guard keeps `proposed` out of every playbook |
| A ticket is executed by the engine or escalated at once | `runner.run` (EXECUTE) | tests; the ticket's own clocks |
| Never lose paid or irreversible work | `runner.work` (strict=False after ACT) | tests (upload id returned; the gate holds instead) |
| Every wired call site exists and is registered; pending list only shrinks | `registry.entry_issues` | `dept_contract` FAIL; `python -m whatifs.org.runner` RED; tests |
| Memo: valid, to the right audience, closed only with proof, never rewritten, never reopened | `memos.write`, `memos.inbox`, `memos._move`, `memos.resolve` | MemoError, nothing written / status unchanged |
| Two clocks; a miss climbs department -> Council -> owner, skipping a level that cannot act | `memos.watchdog`, `memos.escalate` | tests; `Org_Audit` rows |
| The owner hears once, bounded reminders, 3 messages a pass at most; DROP / KEEP by one tap | `memos._tell_owner`, `memos._on_answer` | tests |
| A dead watchdog is noticed | `runner.daily_check` (owner message after 6 h), `runner.episode_issues` (gate FAIL after 24 h) | tests |
| A run that never reported is flagged and becomes a problem memo | `runner.audit` (every tick) | tests |
| A failed check -> problem memo for its owner; closed by the ledger (passed / waived) or the episode's end | `wraps.gate_memos`, `wraps.gate_settle`, `memos.sweep_episodes` | tests |
| A department's own paid thinking stays under its monthly cap (P0 continues) | `runner.run` (budget "org"), `registry.caps`, `registry.spent` | CapReached before the run starts |
6 matrix rows added (docs/CURRENT/ENFORCEMENT_MATRIX.md; the meta-test proves every reference is wired). The rehearsal asserts: all 9 department runs
of the episode present, ok and verified; both checks PASS (not N/A); 9 valid takeaways; the watchdog ran; organisation health; no open problem memo.

#### Step 6 PROVE
- `tests/test_v12_org.py`: 99 tests (56 functions), each rule both ways. The plan's acceptance tests are in it: a department run WITHOUT TAKEAWAY fails
  (nothing reported / stock takeaway), WITHOUT PLAYBOOK INJECTION fails (brief mode never taken; prompt mode with no model call; Palace cannot feed it),
  with an INVALID MEMO fails (and none of its memos is sent); SLA ESCALATION (unacknowledged, unresolved, third attempt, through the Council once it is
  wired, never before the deadline). Also: 26 kinds of bad memo each refused with nothing written; all 150 combinations of status x move x role checked
  against the move table; a tampered Sessions row (missing step, reordered, edited receipt, wrong chain) fails verification; the upload id survives a
  broken contract; the real pipeline end to end (9 runs, both checks PASS) and the same pipeline with ONE department walking around the runner
  (held at the script gate, nothing made or uploaded).
- The tests found 3 real bugs in the new code, all fixed: the silent owner level, the self-blocking breach memo (both above), and a measure function that
  crashed on odd output (it would have turned a healthy step into a breach and held a video).
- Repair attempts used: test file first run 91 / 8 (4 causes: the 3 bugs and the voice stand-in missing in the end-to-end test) -> 98 / 1 (the
  measure bug had a second input shape) -> 99 / 0. Nothing reached the cap of 3.
- Live proof on the real repo: one wrapper removed from `whatifs/episode.py` + the stock-phrase rule switched off in `schemas.py` ->
  `python -m whatifs.org.runner` RED (naming the missing call site), the test file 89 passed / 10 failed, and the real pipeline HELD the episode with
  `contract:dept_contract`; files restored -> GREEN. The promise fix: its regression test fails on the old `anim.py` (13 / 1) and passes on the new.
- Full suite (63 files), ONE uninterrupted run on the final code: **1088 passed / 0 failed / 6 skipped** (988 before + 99 organisation tests + 1 promise
  regression test). No existing test needed a change. (A first full run before the promise fix was 1087 / 0.)
- Fake rehearsal on the final code: **GREEN** - contract script 22 / 22 (`dept_contract` included), final 19 / 19 (`takeaways_written` included);
  9 department runs, 9 takeaways, 0 live memos; Palace 109 items.
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift. Palace **GREEN** (104 founding items). Organisation **GREEN**.
- Money: Rs 0 added (no model call). Not measured in production: nothing is live until the final PR.

#### Step 7 TAKEAWAY (also Palace item `b3.takeaway`)
- WORKED: reading the production path BEFORE wrapping it. The upload id is saved only after the upload returns, so a raise in between means a second
  upload on the retry: that one reading turned "any broken step raises" into "strict before the work, never throw the work away after it".
- WORKED: testing the silence. The deadline test asked "who hears about it?" and the answer was nobody. For every escalation or alarm in later batches,
  assert the message that goes out, not only the status that changes.
- WORKED: an end-to-end test on the real pipeline. It found a fault in code B3 never touched (the stale promise flag) that had been holding finished
  videos on some episodes. Trace an intermittent hold to its cause before calling it flaky: here it was reproducible with a fixed episode id.
- WATCH: "handed over" is not "used". After B3 no model prompt contains Palace knowledge. B6 must flip the creative departments to "prompt" mode and
  wrap the Script Preview / pre-production room first (open issues 12, 13).
- WATCH: a receipt proves that a step happened and what the runner saw; it does not prove the work was good. Quality stays with the contract checks.
- WATCH: the organisation's bookkeeping is now on the critical path: LOAD failing stops a department before it starts (by design). `ORG_ON` = FALSE
  is the switch if the organisation layer itself ever misbehaves; the Palace switch turns the organisation off with it.
- WATCH: until the Council is wired (B6) an unresolved memo goes straight from the department to the owner's level (issues 15, 17).

### B2 - Knowledge Palace core (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: the organisation has ONE repository of knowledge - 92 founding items (the owner's words, the research, the build's own lessons),
each with dated evidence and a pointer to the code that enforces it - with a write gate, a life cycle with authority, and one guarded doorway that
builds a bounded playbook per department. It runs daily, at Setup and as HARD check `palace_health` on every episode. Honest limit: no department
READS a playbook yet (that is B3 + B6), so B2 by itself changes no video.

#### Step 1 RESEARCH (10 dated sources; E = measured evidence, O = opinion / practice / official guidance)
1. E - Zhang et al., "Agentic Context Engineering" (ACE), arXiv 2510.04618, Oct 2025 (v3 Mar 2026, ICLR 2026): knowledge kept as itemised bullets
   (id + helpful/harmful counters), changed only by small delta entries merged with NON-model logic; asking a model to rewrite the whole memory
   collapses it into a vague summary. +10.6% on agent tasks, +8.6% finance, 86.9% lower adaptation latency. Limit: without a reliable outcome
   signal the memory turns noisy or harmful. -> items, never a rewritten document; deterministic merges; outcome counters come from D10 only.
2. E - Shen, Toyoda, Leung, "Revoked but Still Authoritative", arXiv 2609.08258, 8 Sep 2026: five memory systems that mark a contradicted fact
   "invalid" but keep it; 9 scenarios x 9 models: NO system enforces the revocation by default - if the retrieval layer can see the revoked record it
   is returned, ranks above its replacement and the agent acts on it. Fix that worked: a guard between agent and memory that withholds it.
   -> the status filter runs in code BEFORE ranking; a retired / superseded / expired item can never reach a prompt, label or no label.
3. E - Nakayashiki, "When Stale Constraints Go Unchecked", arXiv 2608.25553, 26 Aug 2026: 16 models; a consolidated memory whose source record was
   later withdrawn still drove the decision in 77.3 / 74.7 / 74.7% of episodes; models checked where a memory came from in about 1 episode in 5; a
   "freshness" cue did nothing; a rule that prefers memories stating a LIMIT recovered +89.3 points. -> (a) code, not the reader, invalidates items
   derived from a withdrawn source; (b) limits get a reserved lane at the top of every playbook.
4. E - Rasmussen et al., "Zep: a temporal knowledge graph architecture for agent memory", arXiv 2501.13956, Jan 2025: contradicted facts get an end
   date instead of being deleted; 94.8% vs 93.4% on Deep Memory Retrieval; up to +18.5% accuracy and -90% latency on LongMemEval, mostly because the
   context shrank from ~115,000 to ~1,600 tokens. -> keep history, serve a small current slice.
5. E - Dash et al., "From Untrusted Input to Trusted Memory" (MPBench), arXiv 2606.04329, 3 Jun 2026: one hostile memory write has long-term effect;
   4 write channels, 9 structural weaknesses; agents that write and read memory more eagerly are more exploitable; prompt-injection defences do not
   cover it. -> a write gate: evidence required, the trust level is computed by code from the evidence type, viewer / web text never enters as an
   accepted item, items are rendered to models as data.
6. O/official - Anthropic, "Effective context engineering for AI agents", 29 Sep 2025: the smallest set of high-signal tokens; hybrid loading (a
   small preloaded block + fetch the rest on demand). -> a bounded playbook is preloaded; full bodies are fetched by id only when needed.
7. O/official - Anthropic prompt-caching docs (read 10 Nov 2026): a cache hit needs a 100% identical prefix; minimum cacheable length 512-4,096
   tokens by model; cache reads cost 0.1x (0.05x on the newest Opus / Sonnet). -> the same Palace state must give a byte-identical playbook
   (deterministic order, id = hash of the text), and it only changes when knowledge changes.
8. O/practice - Consortium for Service Innovation, KCS v6 Practices Guide, technique 5.2 (article states): Work in Progress / Not Validated /
   Validated / Archived; the life cycle is non-linear; an article is validated by being REUSED successfully; archive, never delete.
   -> status life cycle with re-validation, promotion by evidence of use, nothing deleted.
9. E/official - Google Sheets API limits (developers.google.com, read 10 Nov 2026): 300 requests a minute per project, 60 per user, 2 MB payload
   advised; a cell holds 50,000 characters. -> the Sheet row is a small index that is enough to build a playbook in ONE read; long bodies live
   outside the Sheet; writes are batched.
10. E - "BM25 wins at scale" (2026 scaling study, as reported; primary id not verified): keyword ranking beats dense retrieval and agent search on
   large piles, and at small sizes exact matching is enough. -> tag + keyword scoring in code (Rs 0, deterministic, no new dependency); an embedding
   scorer can be plugged in later if the Palace outgrows it.
Not established by any source found: that a rule placed first in a long prompt is obeyed more reliably than one placed last (the "lost in the
middle" work is about retrieval). The lane order below is therefore a design choice backed by source 3, not by a placement study.

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Spec-literal store": item rows edited in place, bodies on Drive, playbook = top items by tag overlap cut at a character cap. 2/3/5/3/5 = 18.
  Weak: a retired item is only as safe as every caller's filter; nothing ties knowledge to the code that applies it; ids change with wording.
- B "Research stack" (ACE + Zep + KCS): itemised entries, deterministic delta merges, end-dating instead of deleting, promotion by reuse, keyword
  retrieval, small preloaded block. 4/4/4/4/5 = 21. Weak: still trusts labels at read time (source 2) and lets a stale limit vanish quietly.
- C "The guarded ledger" (ORIGINAL, built on B's mechanics):
  1. ONE doorway out: every playbook is built by one function whose first step is the status-and-date guard, so nothing retired, superseded,
     expired or still only proposed can reach a prompt even if maintenance never ran.
  2. Provenance cascade: when an item is superseded or retired, everything `derived_from` it is expired by code in the same call.
  3. Limits lane: owner words, policy rules and failure lessons are served first and hold a reserved share of every playbook.
  4. Asymmetric expiry (my own rule, from sources 2-3): a stale TECHNIQUE is dropped until re-validated; a stale LIMIT keeps being served, marked
     "review due" and reported - a limit must never disappear silently.
  5. Content-addressed playbooks: id = hash of the exact text, so the id is proof of what was injected and the cached prefix stays stable.
  6. Trust is computed, not typed: confidence comes from the evidence types (owner decision > own measured data > measured study / official
     > practice > research digest > opinion > model claim); nothing enters without dated evidence.
  7. Knowledge is tied to code: every `applied_in` reference (a check, a setting, a function, a file) must exist or the Palace is unhealthy.
  8. Founding knowledge is code: seed items live in the repo (`whatifs/org/seed/*.json`), load idempotently, and can never resurrect a status that
     the organisation later changed.
  9. The truth registry guards the door: an item naming a retired concept is refused on write and flagged if a concept is retired later.
  4/5/5/4/5 = 23.
- DECISION: C.

#### Step 3 DESIGN MEMO
- Decision: `whatifs/org/palace.py` (+ `whatifs/org/__init__.py` with the department and stage lists, `whatifs/org/seed/*.json`). Tabs appended:
  `Palace_Items` (index: everything a playbook needs, so one Sheet read builds it), `Palace_Versions` (one row per change with a running version and
  a hash of the whole Palace), `Palace_Playbooks` (each distinct playbook once). Bodies: seed items resolve from the repo; runtime items go to the
  Drive folder `palace/` (retry, then an inline fallback so learning never stops on a Drive hiccup).
- Life cycle as DATA: proposed -> accepted -> testing -> proven / retired; superseded; expired; each move lists who may make it (owner, council,
  D10, librarian, clock, build). Owner items change only by the owner. An illegal move raises.
- Playbook: guard -> lanes (limits, proven, accepted, testing) -> relevance (department, stage, topic keywords) -> greedy fill under a hard cap
  (default 1,800 estimated tokens per department) -> id = hash.
- Size caps per kind: when a kind is over its cap the lowest-value item (never owner words or limits) is expired by code, not by a model.
- Runs in production now: daily learning job + both setup paths (`palace.daily` / `palace.maintain`), and a new HARD contract check `palace_health`
  on every episode (index valid, seed present, no dead code reference, no retired concept, caps, every department's playbook builds inside its cap
  with only servable items). NOT in this batch (by the plan): injecting playbooks into department prompts and citing them (B3 runner, B6 checks
  `palace_injected` / `palace_cited`), the Council, the Librarian's merges, D10 outcome scores.
- Rejected: an embedding index (new dependency or paid calls for a few hundred short items; source 10); storing bodies only in Sheet cells
  (cell limit, heavy reads); letting a model merge or rewrite items (source 1); deleting anything (sources 4, 8); a hand-kept Palace doc (the
  generated SYSTEM.md gets a Palace section instead).
- Enforcement plan and tests: see steps 5-6 (every transition both ways, guard, cascade, expiry both kinds, caps, cap of the playbook, seed
  validity, contract PASS / FAIL, rehearsal assertion, matrix row).
- Cost: Rs 0 (no model call). Sheet traffic: 1 read per playbook, 1-3 writes per change; seeding is one batched append.
- Palace seed items: `whatifs/org/seed/build.json` (keys `b2.*`: 10 research-backed items + the takeaway). The seed moved out of `handoff_v12/palace_seed`
  into the code tree, because production loads it.

#### Step 4 BUILD (what changed)
- NEW `whatifs/org/__init__.py` (departments + stages) and `whatifs/org/palace.py` (930 lines): `check` / `validate` (write gate), `add` / `add_many`,
  `transition`, `supersede`, `expire`, `revalidate`, `mark_applied`, `enforce_caps`, `tidy`, `servable` (the guard), `playbook`, `playbook_issues`,
  `body`, `seed_items` / `ensure_seed`, `sync_brain`, `sync_canon`, `reconcile`, `snapshot`, `maintain`, `daily`, `health`. By hand: `python -m whatifs.org.palace`.
- NEW founding knowledge, 92 items in `whatifs/org/seed/`: owner.json 29 (his words, verbatim quote kept as evidence), breakout.json 15, feel.json 15,
  platform.json 15, build.json 18 (B1, B1b, B2). By kind: owner_preference 25, technique 27, tool_fact 13, policy_rule 10, strategy 7, audience_insight 4,
  takeaway 3, plan 2, failure_lesson 1. 0 refused by the gate. Over 120 `applied_in` references, every one resolves to a real check, setting, tab,
  function or file. Second-hand research is honest about itself: status accepted, computed trust 0.5, nothing is "proven" until D10 measures it.
- Mirrors of records that already exist (seed sources 3 and 4 of the plan): `sync_brain` (Technique_Evidence -> technique items, and a retired level
  becomes an "avoid" lesson in the limits lane; the learning core stays the authority) and `sync_canon` (character bible + every published case from
  Show_Log / Season; viewer handles never enter).
- Tabs appended: `Palace_Items` (28 columns), `Palace_Versions`, `Palace_Playbooks`. 7 settings: PALACE_ON, PALACE_PLAYBOOK_TOKENS (1800),
  PALACE_PLAYBOOK_TOKENS_BY_DEPT, PALACE_LIMITS_SHARE (0.4), PALACE_REVIEW_DAYS, PALACE_KIND_CAPS, PALACE_FOLDER_ID.
- Production hooks: `manage.learn` -> `palace.daily` (after the learning core's own update), `manage.setup` -> `palace.maintain`,
  contract check `palace_health` (39 hard checks now: 21 script + 18 final).
- `truth.code_files` and `gen_docs._modules` now walk sub-packages, so `whatifs/org/` is under the truth scan and in SYSTEM.md; SYSTEM.md has a
  generated section 10 (kinds, statuses, the whole move table, review windows, caps, departments, founding-knowledge counts).
- `publish.drive_upload` gained `parent=` (the Drive folder palace/); bodies fall back to an inline copy when Drive fails.
- Added during the build after looking at real output (not in the design memo): item `priority` 1-3 (3 = core, only owner / Council / seed may set it)
  and tighter department addressing - the first writers' playbook had opened with a minor owner idea and left out "it happens to YOU".

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| Nothing enters without dated evidence, a known kind / department / stage, a 20-400 character summary; trust computed by code | `palace.check` | write refused (PalaceError), nothing stored; `palace_health` on stored rows |
| Every `applied_in` reference exists in the code | `palace.ref_ok` | write refused; seed -> tests + `palace_health` FAIL; runtime row -> reference dropped + logged |
| No retired concept, no instruction-like text, no platform-gaming proposal in the Palace | `palace.text_issues` (uses `truth.RETIRED`) | write refused; later hit -> never served, auto-expired (owner words: `palace_health` FAIL) |
| Only listed moves, only by the listed roles, always with a reason | `palace.transition` + `MOVES` | PalaceError, status unchanged |
| The owner's words change only by the owner | `palace._owner_rule` | PalaceError |
| Nothing retired / superseded / expired / proposed reaches a prompt (also after a hand edit) | `palace.servable` inside `palace.playbook` | `playbook_issues` -> `palace_health` FAIL |
| Withdrawn knowledge sends its descendants back | `palace._cascade` | tests |
| Stale technique dropped; stale limit kept, marked, reported | `palace.expire` + guard | tests; note in `palace_health` |
| Playbook inside its hard cap, limits first, deterministic, id = hash of text | `palace.playbook` | `playbook_issues` -> `palace_health` FAIL |
| Size caps per kind by code; limits, owner words and canon never displaced | `palace.enforce_caps` | `palace_health` FAIL when a kind stays over its cap |
| Founding knowledge present; a seed never resurrects a changed status | `palace.ensure_seed` | `palace_health` FAIL (missing items / broken seed file) |
| Palace kept up every day, at Setup and before every episode's check | `palace.daily` / `maintain` | rehearsal asserts; `palace_health` |
4 matrix rows added (docs/CURRENT/ENFORCEMENT_MATRIX.md; the meta-test proves every reference is wired). Rehearsal asserts `palace_health` PASS, the
seed, mirrored canon, a recorded writers' playbook inside its cap, and a healthy Palace at the end.

#### Step 6 PROVE
- `tests/test_v12_palace.py`: 39 tests, each rule both ways. Highlights: 23 kinds of bad item each refused with nothing written; ALL 343 combinations
  of from-status x to-status x role checked against the move table; a randomised 140-item Palace in every status, for 15 departments x 3 caps: nothing
  unservable ever served, never over the cap, limits first, same text whatever the row order; a hand-edited status cell cannot bring a superseded
  item back; Drive down -> learning continues; real-Drive path proven with stubs (folder found / created / unreachable).
- The tests found 2 real bugs in my own code, both fixed: (1) the playbook checker crashed on a retired row instead of reporting it; (2) upkeep logged
  its own changes before the audit compared hashes, so an edit made outside the code went unrecorded - the audit now runs first.
- 3 test expectations were wrong on first run and corrected (repair attempt 1 of 3 each): a department's default stage, the count of mirrors created
  when a retired level turns promising, an over-clever file-order assertion.
- Live proof on the real repo: a dead code reference + a retired concept put into feel.json, and a retired brand name put into a string of
  palace.py -> the test file went 34 passed / 5 failed, Plan Guard RED (naming the line), `python -m whatifs.org.palace` RED (naming both seed faults);
  files restored -> 39/39, GREEN, GREEN.
- Fake rehearsal on the final code: **GREEN** - contract script 21/21 (`palace_health` included), final 18/18; Palace 97 items (92 founding +
  4 characters + the rehearsal's case), writers' playbook 1,745 of 1,800 estimated tokens, recorded in `Palace_Playbooks`.
- Full suite (62 files), ONE uninterrupted run on the final code: **988 passed / 0 failed / 6 skipped** (949 before + the 39 new tests; no existing
  test needed a change, although `palace_health` now runs inside every script-stage contract call of the older tests).
- Plan Guard **GREEN**. Truth scan **GREEN**. SYSTEM.md regenerated, no drift.

#### Step 7 TAKEAWAY (also Palace item `b2.takeaway`)
- WORKED: writing the founding knowledge through the SAME gate as runtime knowledge. The `applied_in` rule forced every "this is enforced" claim to
  name code that exists; the gate is exercised by 92 real items before any department uses it.
- WORKED: reading the real output before trusting the rule. The ranking was correct by its own rules and still wrong for the writer; priority and
  addressing fixed it. Do this for every selection or ranking rule in later batches (memo routing, the Council's agenda, the research agenda).
- WORKED: testing the checker against inputs it should never see - that is how the crash on a retired row surfaced.
- WATCH: a few low-priority limits do not fit an 1,800-token playbook (D1 3, D4 4, D12 1, Council 5). Reported by the health check as a note, nothing
  is silent - but the Council (B6) / Librarian (B8) must merge them or the cap for those departments must rise (setting PALACE_PLAYBOOK_TOKENS_BY_DEPT).
- WATCH: an edit made outside the code is recorded only if the next upkeep runs before the next Palace write (the hash is taken after each write).
- WATCH: tool facts expire 60 days and plans 45 days after seeding unless re-validated: B5's research cadence must re-validate them.
- WATCH: the Sheets / Drive path of the Palace is proven with the local store and stubs only (no keys on this laptop, by rule). First real proof =
  the first learning job after the merge; the B10 first-run verification must look at tab `Palace_Items` and at `palace_health` in the Feature_Ledger.
### B1b - Owner decision executed: 4 long videos a month (10 Nov 2026) - ACCEPTED
Not a plan batch: the generated SYSTEM.md from B1 exposed that the ledger said 4 long videos a month while the code allowed 8. The owner was asked
in one line and answered "4 a month". Executed at code-line level the same session (no new research: the decision is the owner's).
- BUILD: `core.DEFAULTS` STANDARD_MAX_LONG_PER_MONTH 8 -> 4, PUBLISH_DAYS Tue,Sat -> Sat (one a week; Saturday was already one of the two days and
  is the Runway day), VIDEOS_PER_MONTH_EST 9 -> 4, new cell V12_FLIPS_DONE. `manage.v12_upgrade` + `V12_FLIPS`: ONE-time move of the live Sheet,
  only for cells still at the old default (an owner-typed value is never touched); called from both setup paths. `governor.long_videos_per_week`.
  Viewer lines in `whatifs/cta.py`: 4 subscribe lines promised "twice a week" -> "every week" (true at any cadence of one a week or more, so no
  runtime substitution and nothing to leak). `caretaker.cadence_words`: the policy-rescue prompt now describes the channel from the settings
  (it said "about 2 long videos + 10-14 Shorts a week").
- Design note: a cadence placeholder filled at use time was considered for the viewer lines and rejected (leak risk into a spoken script, and tests
  compare pool lines verbatim); wording that cannot become false won.
- ENFORCE: gate `governor.can_start_episode` (already existed; now reads 4); new retired rule `old_long_cadence` in `truth.RETIRED` (14 rules) so
  "twice a week" / "8 videos a month" / "2 long videos" fail Plan Guard, the tests and contract `docs_current`; matrix row added; ledger section D updated.
- PROVE: `tests/test_v12_cadence.py` 8 tests, both ways (4th allowed / 5th blocked / cell change lifts it; Sheet move flips old defaults once and
  leaves owner values; no viewer line states a numeric cadence; prompt follows the settings). The new rule caught a 4th "Twice a week" line that a
  case-sensitive search had missed. Expectation updates forced by the decision: test_v94a (at most 8 -> 4), test_hardening (PUBLISH_DAYS),
  test_v91_matrix (V12_FLIPS added to the documented one-time moves), test_v91_insights (see below).
- Full suite (61 files): **949 passed / 0 failed / 6 skipped**. Honest detail: the uninterrupted run was 948 / 1. The 1 = test_v91_insights estimator
  bound (comment-mining share + variety rewrite < Rs 3 per video): the MONTHLY comment-mining money is unchanged (about Rs 6) but is now shared by 4
  videos instead of 9, so the per-video line rose from Rs 0.7 to Rs 1.5. Test now asserts the monthly amount (repair attempt 1 of 3) -> file 9/9.
  No second uninterrupted full run after that one-file test edit. Rehearsal **GREEN** (20 + 18). Plan Guard **GREEN**.
- EFFECT ON MONEY (not measured in production - nothing is live until the final PR): the planner now splits the month over 4-5 weekly slots instead
  of 8-9, so each long video gets a larger share of the cap and extras (Shorts, breakout follow-ups) have more free money. The cap itself is unchanged.
- TAKEAWAY: a decision is only executed when every place that SAYS the old thing is found; registering the old value as a retired concept found one
  the manual search missed. Do this for every future owner decision that replaces something.

### B1 - Truth hygiene (10 Nov 2026) - ACCEPTED (all 7 loop steps recorded below)
Result in one line: there is now ONE current truth, and code refuses anything else - in docs, CLAUDE.md, module docstrings, the build prompt and
every prompt string - on every push (Plan Guard), in the suite, in the rehearsal and on every episode (contract check `docs_current`).

#### Step 1 RESEARCH (7 dated sources; E = measured evidence, O = opinion/practice)
1. E - Gloaguen et al., "Evaluating AGENTS.md" (ETH Zurich / LogicStar), arXiv 2602.11988, 12 Feb 2026 (v3 29 Sep 2026): repository context files do
   NOT generally raise coding-agent success and raise cost > 20%; agents obey what the file says; repo overviews do not help; only non-standard
   practices are worth writing. -> CLAUDE.md must be short, rules only, and never wrong (a wrong line is obeyed).
2. E - Chroma, "Context Rot" (Hong, Troynikov, Huber), Jul 2025, 18 models: reliability falls as input grows; distractors that are topically CLOSE to
   the right answer hurt most. -> an old doc about the same system is the worst kind of distractor; keep history out of what a chat loads.
3. O/official - Anthropic Claude Code memory docs (code.claude.com/docs/en/memory, read 10 Nov 2026): CLAUDE.md is context, not enforcement; target
   under 200 lines; specific + concise is followed more reliably. -> enforcement must live in tests/checks, not in the file's wording.
4. E/practice - Grafana Loki CI "check generated documentation" step: reference docs are generated from code and CI fails when the committed file
   differs. Same idea: Fern "Stopping schema drift" (Aug 2026): derive, don't document. -> SYSTEM.md is generated, drift fails the build.
5. O/practice - Vale prose linter (vale.sh; Fern guide Oct 2026; Grafana writers' toolkit): retired terms are data (existence / substitution rules);
   only zero-false-positive rules get error severity. -> retired concepts as data rules with context exceptions, all at error level.
6. O/practice - ADR immutability (Fowler bliki; Backstage docs): never delete or rewrite an accepted record; mark it superseded and point to the
   replacement. -> ARCHIVE keeps files byte-intact under a HISTORICAL header naming what replaced them.
7. E/practice - ESLint bulk suppressions (eslint.org, Apr 2025) and Notion's ratchet file: legacy violations are baselined by count per file+rule; new
   ones fail at once; stale baselines must be pruned. -> a reviewed baseline for code strings that legitimately name old values (migrations).

#### Step 2 CREATIVITY (3 designs; scores 1-5: breakout impact / enforceability / cost / reliability / owner effort)
- A "Move + grep" (literal minimum): move files, hand-write SYSTEM.md, one test with a regex list. 2/2/5/2/5 = 16. Weak: SYSTEM.md is stale the day
  after; the list lives in a test the organisation cannot extend; nothing runs outside pytest.
- B "Docs-as-code stack" (research): generated SYSTEM.md + drift test, Vale-style rules as data, ADR-style archive, ratchet baseline. 3/4/4/4/5 = 20.
  Weak: still only a build-time gate; Vale itself would be a new CI dependency (rejected: same rule model in ~100 lines of Python).
- C "Truth Registry" (ORIGINAL): ONE module (`whatifs/truth.py`) is the organisation's single statement of what is current and what is retired:
  retired concepts are data (pattern, allowed context, why, the CURRENT truth that replaced it); current facts are RENDERED from the live code into
  SYSTEM.md (a doc cannot state a number the code does not hold); the same scan runs in four places - Plan Guard (every push), the test suite, the
  rehearsal, and as contract check `docs_current` on every episode (it also reads the CONSTITUTION cell, the one prompt source that changes without a
  merge). Later batches append to the registry (Council retires a concept -> it is banned everywhere on the next run). 4/5/4/4/5 = 22.
- DECISION: C built with B's mechanics (generate-and-diff, rule data, ADR archive, ratchet baseline).

#### Step 3 DESIGN MEMO
- Decision: docs/CURRENT (SYSTEM.md generated by `tools/gen_docs.py`; CONCEPT.md, OWNER_REQUIREMENTS_LEDGER.md, ENFORCEMENT_MATRIX.md,
  PLATFORM_FACTS.md hand-kept) + docs/ARCHIVE (KERNEL, CHANGES, the two old laptop prompts, all v11.1 module docstrings) under a
  "HISTORICAL - DO NOT FOLLOW" header. CLAUDE.md rewritten (< 200 lines, rules only, points only at docs/CURRENT). Every module docstring = one-line
  purpose + pointer. claude-build.yml prompt re-pointed. `whatifs/truth.py` = registry + scanner.
- Why: sources 1-3 (a chat obeys what it reads; near-topic history is the worst distractor; wording is not enforcement), 4 (generated beats written).
- Rejected: Vale binary (new dependency); a `.claude/settings.json` Read-deny on docs/ARCHIVE (would also block the owner's own history look-ups and
  changes how his Claude Code behaves without him asking); deleting history (source 6); a new hand-kept changelog (second source of truth - git + PR
  bodies are the log until the Palace exists in B2).
- Cost: Rs 0 (no model call; the scan takes ~1.5 s once per process, then cached).
- Palace seed items: `handoff_v12/palace_seed/B1.json`.

#### Step 4 BUILD (what changed)
- NEW `whatifs/truth.py`: RETIRED (13 rules, each with the truth that replaced it), BASELINE (2 reviewed entries), `scan`, `docstring_issues`,
  `layout_issues`, `live_prompt_issues` (CONSTITUTION cell), `issues`. Run by hand: `python -m whatifs.truth`.
- NEW `tools/gen_docs.py` -> `docs/CURRENT/SYSTEM.md` (369 lines: facts, how it runs, v12 status, truth rules, 38 checks, 39 key settings, 24 jobs,
  71 tabs, 103 modules). NEW `docs/CURRENT/CONCEPT.md`. Ledger + matrix moved to docs/CURRENT and corrected. PLATFORM_FACTS moved (content unchanged).
- docs/ARCHIVE: KERNEL.md, CHANGES.md, OWNER_LAPTOP_CHANGES.md, PROMPT_LAPTOP_CHANGE.md (header added, text unedited), MODULE_DOCSTRINGS_v11_1.md
  (every old docstring, nothing lost).
- CLAUDE.md rewritten: 64 lines (was 67 lines of v8-v10 history incl. the old caps and "table read" as a keep-rule).
- 101 module docstrings -> one line each. `.github/workflows/claude-build.yml` prompt now reads CLAUDE.md + docs/CURRENT/SYSTEM.md and runs gen_docs.
- Stale statements the scan found INSIDE live code and that are now fixed (settings notes in `whatifs/core.py`, text only, no default changed):
  PUBLISH_DAYS (cited the old cap), BUDGET_FLOOR_INR / BUDGET_CEILING_INR (old-cap history), BRAIN_ON (named the outlier library as the learning-core
  table), CONSTITUTION + MODEL_ROUTES (pointed at the old changelog), PREPROD_ON, SHOW_MODE, FAL_HERO_MODEL, TTS_ENGINE (old version labels).
  Mission Control guide: 2 rule numbers, 1 old changelog pointer, 1 dead test path fixed.

#### Step 5 ENFORCE (rule -> executing code -> check -> matrix row)
| Rule | Executes | Fails when broken |
|---|---|---|
| No retired concept in current docs, CLAUDE.md, build prompt, docstrings, prompt strings | `truth.scan` | Plan Guard RED; contract `docs_current` FAIL (episode HELD); tests |
| No retired concept in the owner's CONSTITUTION cell (changes without a merge) | `truth.live_prompt_issues` | contract `docs_current` FAIL |
| SYSTEM.md equals the code | `gen_docs.render` / `gen_docs.drift` | `test_system_md_*` (hand edit AND code change without regenerating) |
| docs/ = CURRENT + ARCHIVE only; ARCHIVE files marked; CLAUDE.md <= 200 lines; every named path exists | `truth.layout_issues` | Plan Guard RED; contract; tests |
| Docstring = one line + pointer, no history | `truth.docstring_issues` | Plan Guard RED; contract; tests |
| Old values in code only where reviewed (ratchet) | `truth.BASELINE` | one more hit fails; one fewer fails until pruned |
Matrix row added (`contract:docs_current`, `fn:whatifs.truth.issues`, `fn:tools.plan_guard.main`, `fn:tools.gen_docs.render`); the meta-test covers it.
Rehearsal asserts `docs_current` ran and passed.

#### Step 6 PROVE
- `tests/test_docs_current.py`: 28 tests, every rule proven BOTH ways (13 retired rules each fire on the retired sentence and stay quiet on the true
  one; 6 surfaces - 2 current docs, CLAUDE.md, build prompt, 2 prompt strings - each fail when a retired term is inserted and pass when removed;
  layout, docstrings, baseline ratchet, SYSTEM.md drift x2, contract PASS/FAIL incl. a dirty CONSTITUTION cell, Plan Guard GREEN/RED by subprocess).
- Live proof on the real repo: appended "The monthly cap is Rs 4,700 and the room is the table read." to docs/CURRENT/CONCEPT.md -> the suite file went
  21 passed / 7 failed and Plan Guard went RED naming both rules; file restored -> 28/28 and GREEN.
- Full suite (60 files): **940 passed / 0 failed / 6 skipped**. Honest detail: the one uninterrupted full run was 939 / 1 failed. The 1 =
  `test_v11_stage_e::test_scout_uses_the_current_endpoints_only`, which had been passing only because the OLD docstring of scout.py contained the
  endpoint text (the code builds the URL from a base constant). Test rewritten to judge the code itself (repair attempt 1 of 3) -> file re-run 8/8.
  A second uninterrupted full run after that one-file test edit was not repeated (35 min).
- This full run also closes B0's caveat: every B0-era test passed in one uninterrupted run (incl. test_v11_feel after the particle-seed fix).
- Fake rehearsal: **GREEN** (contract script 20/20 - `docs_current` included - and final 18/18). Plan Guard: **GREEN**.

#### Step 7 TAKEAWAY
- WORKED: generating the doc from the code and then scanning the generated doc found stale statements inside LIVE settings notes that no grep of the
  docs folder could find. Scan what the code says about itself, not just the documents.
- WORKED: the one-line-docstring change exposed a test that was passing on docstring text instead of code. Tests that grep source files can be
  satisfied by comments; prefer asserting on imported values.
- WATCH: rules are line-based with an "unless" context - keep current docs one fact per line or a true sentence can be flagged (or a false one missed).
- WATCH: inline code comments still carry version labels and rule numbers (thousands; declared "history labels" in CLAUDE.md and SYSTEM.md section 4).
  If a future chat is ever seen acting on one, extend `truth.scan` to comments.

### B0 - Bootstrap & verify (10 Nov 2026) - ACCEPTED
- Laptop (Windows 11): installed Git 2.56, Python 3.12.10, ffmpeg/ffprobe 9.0.2 via winget. venv at `REALITY_ENGINE_HANDOFF/.venv` with the
  requirements.txt pins (numpy 2.0.2, opencv-headless 4.14, pillow 12.3, requests, pyyaml) + tzdata, soundfile, cryptography (Checks installs these too).
  Not installed: kokoro, transformers (no test needed them).
- Repo cloned, branch `v12-organisation` from main, commit "v11.1 baseline (from handoff)" pushed.
- Files only on main (kept, untouched): `.keepalive`, `PRIVACY.md`, `README.md`. 35 files only in the snapshot (v10.2-v11.1 work) are now on the branch.
- Plan Guard GREEN; full suite (59 files) 912 passed / 0 failed / 6 skipped; fake rehearsal GREEN (script 19/19, final 18/18).
- How 912/0 was reached: first run 897 / 15 (9 = Windows ffmpeg path in `whatifs/reels.py`, fixed with 2 nt-only lines; 5 = `cryptography` missing in
  the venv; 2 = no DejaVu font on Windows, fonts copied to the path the code looks for). Second run 911 / 1: `test_v11_feel` particle test,
  intermittent - a REAL v11.1 bug (`render.Particles` seeded from Python's per-process `hash()`), fixed with an md5 seed. Confirmed by B1's full run.
- Code changes in B0 (both protected-area; say so in the final PR): `whatifs/reels.py` (Windows-only path escaping), `whatifs/render.py`
  (deterministic particle seed).

## PROTECTED-AREA FILES TOUCHED SO FAR (list them in the final PR)
- V2c-b2b2: `whatifs/manage.py` (the long video's release is one step; `_post_reel`, `_release_extra`, `extra_reel_due` and
  `cap_hashtags` are gone; `shorts_lesson`; the one-time move `v12v2cb2b_upgrade` at both setup sites; a row at LIVE1 is closed
  by the tick), `whatifs/episode.py` (no reel plan, cover, build or clean copy; the release record lists no reels),
  `whatifs/room.py` (`reels`, `reel_count`, `reel_style`, `past_footage`, `_reel_extra` are gone), `whatifs/contract.py` (the
  checks `shorts` and `short_covers` are gone: 60 hard checks), `whatifs/core.py` (8 cells gone, `PILOTS_ON` and
  `SPECIALS_ON` FALSE by default, 1 new cell, the note of `REEL1_DELAY_MIN`), `whatifs/truth.py` (retired rule
  `cutdown_reels`, `OLD_DOORS`, `short_doors`, `door_issues`), `whatifs/governor.py` (two premium pictures fewer in every
  estimate), `whatifs/models.py` (the role `reels` is gone; THE DEADLOCK FIX in `CacheManager.blocks`), `whatifs/playbook.py`
  (no reel department), `whatifs/org/registry.py`, `levers.py`, `rnd.py` (2 check owners and 1 lever gone: 71 levers;
  SHOW_CHECKS 49). DELETED: `whatifs/reels.py`. Not protected, touched: `whatifs/sampler.py`, `prompts.py`, `fakes.py`,
  `data.py`, `format_engine.py`, `cta.py`, `art.py`, `show.py`, `tableread.py`, `cli.py`, `tools/rehearsal.py`,
  `tools/sweep.py`, `tools/gen_docs.py`, `tests/paid_calls.py`, `mission_control/mission_control.html` (one sample line).
- V2c-b2b1: `whatifs/opening.py` (NEW; on the protected list from its first commit), `whatifs/episode.py` (the plan stage fetches and
  lays the opening; `plan_check`, `anchor_shots`, the paid repair, `_assets`, `_render`, `reaction_events` and both gates know a
  footage shot), `whatifs/contract.py` (2 new probes and rows; `p_hook` knows the Short's hook), `whatifs/room.py` (`past_footage`;
  the cut-down planner is not offered footage shots), `whatifs/core.py` (6 cells), `whatifs/org/registry.py`, `levers.py`, `rnd.py`
  (D6 wraps the module, 2 check owners, 2 levers, SHOW_CHECKS 51), `tools/repair.py` (the list itself). Not protected, touched:
  `whatifs/hooks.py`, `whatifs/anim.py`, `tools/rehearsal.py`, `tools/sweep.py`, `tests/paid_calls.py`.
- V2c-b2a: `whatifs/release.py` (NEW; on the protected list from its first commit), `whatifs/publish.py` (three pure request-body
  functions - `yt_body`, `ig_reel_params`, `fb_reel_finish` - that the uploads now send through; three read-backs - `yt_read`,
  `ig_read`, `fb_read`; the offline stand-in platform; `ig_reel` / `fb_reel` take new optional arguments - an older caller's request
  is byte for byte what it was, a test proves it; `verify_upload` unchanged and still behind every YouTube upload),
  `whatifs/shorts2.py` (`_made` reads the field; `cover`, `_keep_master`, `_hand_over`; the record is written the moment the file is
  kept; `UPLOAD_HOLD` gone), `whatifs/contract.py` (1 check added at a NEW stage "release", `release_sheet`; no existing check
  changed), `whatifs/manage.py` (`release.settle` on the tick; `v12v2cb2_upgrade` at both setup sites), `whatifs/core.py` (tab
  `Release_Sheet`; 3 columns appended to `Specials`; 9 cells in, none out, no default changed), `whatifs/ladder.py` (`went_public`;
  a Short that is made and never public is PASSED with the window), `whatifs/org/registry.py` / `levers.py` / `rnd.py` (D9 wraps
  `release.py`; entries D9 `short_publish` and D8 `release_gate`; 2 levers of D9, neither costs money nor weakens a gate; SHOW_CHECKS
  49), `tools/repair.py` (the list itself). MONEY: no paid call added; `tests/paid_calls.py` unchanged. Not on the list and changed:
  `whatifs/specials.py` (`approve` hands a Short to Publishing), `tools/rehearsal.py`, `tools/sweep.py`, `tools/gen_docs.py`.
- V2c-b1: `whatifs/ladder.py` (NEW; on the protected list from its first commit), `whatifs/contract.py` (1 check added at the script
  gate, `topic_ladder`; no existing check changed), `whatifs/episode.py` (`produce` asks the ladder gate before its first paid call; the
  draw carries `ladder`; `ladder.use` once the plan is saved), `whatifs/preview.py` (no draft without the gate), `whatifs/room.py`
  (`scout_and_pick`: the promoted topic is the forced first pitch, its premise kept by code; the end tease), `whatifs/manage.py`
  (`_produce_slot` asks the gate and sends the one refusal message; `ladder.watch` on the tick, the hourly link card gone;
  `v12v2cb_upgrade` at both setup sites), `whatifs/core.py` (9 cells in; 3 cells OUT - SHORTS_PER_DAY, SHORTS_KLING_EVERY,
  REPLAN_MAX_SHORTS_PER_DAY, with a one-time move; tab `Ladder`; 2 columns appended to `Breakout_Queue`, 2 to `Analytics`),
  `whatifs/publish.py` (an archive is uploaded as an archive), `whatifs/shorts2.py` (the cadence in weeks, a winner's order before the
  cadence, the footage kept, the upload check before the first paid call, a crashed Short on record), `whatifs/truth.py` (retired rule
  `daily_shorts_cadence`), `whatifs/org/registry.py` / `levers.py` / `rnd.py` (D10 wraps the ladder and has the run `promote`; 6 levers
  in, 1 out: 68; SHOW_CHECKS 48), `tools/repair.py` (PROTECTED + ladder.py). Also touched, not protected: `whatifs/brain.py` (a Short's
  numbers by processed day), `whatifs/breakout.py` (the winner rule), `whatifs/replan.py` (one rung), `whatifs/shortslab.py` (the hourly
  link card removed), `whatifs/caretaker.py`, `whatifs/dash.py`, `whatifs/notify.py`, `mission_control/mission_control.html` (the phone
  dashboard's switch is "Shorts per week"), `tools/rehearsal.py`, `tools/sweep.py`, `tools/gen_docs.py`. No workflow file changed.
- V2c-a: `whatifs/contract.py` (5 checks added at the new stage "short"; no existing check changed), `whatifs/org/runner.py` (LOAD: an empty
  Sheet is seeded before the cast is mirrored - nothing else in the six steps changed), `whatifs/models.py` (one role, `short_writer`, on the
  long script's chain - no price or limit changed), `whatifs/formats.py` (the Short formats beside the long ones; the long formats untouched),
  `whatifs/core.py` (18 cells, 3 columns appended to tab `Specials`, default SHORTS_NEED_MASTERS TRUE -> FALSE), `whatifs/manage.py`
  (`v12v2c_upgrade` at both upgrade sites), `whatifs/org/registry.py` / `levers.py` / `__init__.py` / `rnd.py` (D14, 12 levers, SHOW_CHECKS
  47), `tools/repair.py` (PROTECTED + shortseat.py and shorts2.py), `tools/rehearsal.py` (one Short made and asserted). Also touched, not
  protected before: `whatifs/shorts2.py` (rebuilt; protected now), `whatifs/specials.py` (`_publish` takes an optional text),
  `whatifs/fakes.py`, `tools/sweep.py` (mode `short`), `tools/gen_docs.py`, and **`.github/workflows/checks.yml`** (the step that installs
  ffmpeg: bounded at 30 minutes, a second mirror, a named error - a WORKFLOW change; its normal path ran green on GitHub, its fallback
  path has never run: read it in the final PR).
- V2a: `whatifs/contract.py` (`run` judges a device by the episode's format - no check is weakened for the trial or for an episode without a
  format; 1 check added), `whatifs/episode.py` (the format after the room, on a resume and reset at the end; designed voices, provenance,
  packaging pairs and the experiment row in every format), `whatifs/room.py` / `room2.py` (the format around the room, three briefs, the
  rubrics), `whatifs/enforce.py` (optional devices; the format fix), `whatifs/show.py` (`leads_on` / `on`), `whatifs/cast.py`, `whatifs/core.py`
  (5 cells), `whatifs/org/registry.py` / `levers.py` / `rnd.py`, `tools/repair.py` (PROTECTED + formats.py), `tools/rehearsal.py` (format-aware).
- V1b: `whatifs/contract.py` (2 checks added; no existing check changed), `whatifs/episode.py` (`_probe`: D13's line-up run in the plan stage; the
  script gate's context carries it), `whatifs/enforce.py` (the expert words join the one mandatory fix), `whatifs/prompts.py` (three lines in the
  house rules), `whatifs/models.py` (two reader roles), `whatifs/core.py` (6 cells), `whatifs/org/registry.py` / `levers.py` / `rnd.py` (the second
  run, 3 levers, SHOW_CHECKS 42), `tools/repair.py` (PROTECTED + layman.py), `tools/rehearsal.py` (2 assertions).
- V1a: `whatifs/contract.py` (3 checks added; no existing check changed), `whatifs/episode.py` (D13's run before the Animation Director; the script
  gate's context carries the shot list, the timeline and the package), `whatifs/voice.py` (one call after `parse_script`), `whatifs/enforce.py`
  (the numbers problem joins the one mandatory fix), `whatifs/prompts.py` (one sentence for the Director), `whatifs/core.py` (8 cells; defaults
  RUNTIME_MAX_SEC 600 -> 540 and PROMISE_BY_SEC 30 -> 5), `whatifs/manage.py` (`v12v1_upgrade`), `whatifs/org/registry.py` / `levers.py` /
  `__init__.py` / `rnd.py` (D13, 4 levers, SHOW_CHECKS 40), `tools/repair.py` (PROTECTED + audience.py), `tools/rehearsal.py` (2 assertions).
- B5 recheck: `whatifs/models.py` (`haiku_repair` keeps the repaired call's note; `_gemini` records the role that really answered - no route, price
  or limit changed), `whatifs/org/rnd.py`, `whatifs/org/board.py` (the 16 corrections above). Also touched, not protected: `whatifs/cli.py` (one
  call at the start of the production job), `.github/workflows/learn.yml` (limit 30 -> 60 minutes).
- B4: `whatifs/core.py` (2 tabs + 9 settings appended; nothing existing changed), `whatifs/episode.py` (ONE argument added to the brain's `tag` call: the
  long video's experiment arms are recorded in its features), `whatifs/manage.py` (one call on the tick: `EXE.engine_tick()`), `tools/repair.py`
  (PROTECTED list + levers.py, execute.py, builds.py), `whatifs/org/memos.py` / `schemas.py` / `runner.py` / `registry.py` (ledger proof on the memo
  doorway, the engine as verifier, the typed wait for proof, the engine as default executor, D12 wired), `whatifs/contract.py` (2 checks added; no existing
  check changed), `whatifs/truth.py` (2 list entries deleted, limit lowered). Also touched, not on the protected list before: `whatifs/builds.py` (new
  optional arguments and three read functions; the owner's own builds behave as before), `whatifs/cli.py` (one optional argument), `whatifs/notify.py`
  (one handler registered), `tools/gen_docs.py`, `tools/rehearsal.py`, and **`.github/workflows/claude-build.yml`** (one optional input `request`; the
  Sheet, WhatsApp, owner and merge credentials moved from the job to its last step; the model credential to the Claude step) - a WORKFLOW change that
  could not be run here: read it in the final PR.
- B0b: `whatifs/core.py` (10 Settings NOTES reworded: the 8 cells no code reads, one stale cadence note, the safe-mode note; no default value changed),
  `.github/workflows/checks.yml` (unit tests run strict and report; rehearsal reports; pip line pinned) and the pip line of 12 more workflows (same
  bounds as `requirements.txt`; OpenCV goes from 5.0.0 back under 5 in `preview.yml` job 2, `sheets.yml`, `repair.yml`; pillow / requests / soundfile
  resolve to the same versions as today). Also touched, not on the protected list: `whatifs/truth.py` (two scans + three lists), `tools/gen_docs.py`,
  new `tools/sweep.py`, `tools/ci_report.py`.
- B3: `whatifs/episode.py` (9 call sites wrapped with `ORG.work`; what each step does is unchanged), `whatifs/core.py` (4 tabs + 9 settings appended, `COST_TAPS`
  hook in `cost`), `whatifs/models.py` (`ASK_TAPS` hook in `ask` and `ask_batch`; a no-op when nothing listens), `whatifs/manage.py` (watchdog + audit on the tick,
  `install` in Setup), `tools/repair.py` (PROTECTED list extended with the org modules, `contract.py`, `truth.py`). Also touched, not on the protected list before:
  `whatifs/contract.py` (2 checks added), `whatifs/cli.py` (learning job wrapped), `whatifs/notify.py` (one handler registered), `whatifs/anim.py` (the promise-flag
  fix), `tools/gen_docs.py`, `tools/rehearsal.py`.
- B2: `whatifs/core.py` (3 tabs + 7 settings appended; nothing existing changed), `whatifs/manage.py` (2 calls: `palace.daily` in the learning job,
  `palace.maintain` in Setup), `whatifs/publish.py` (`drive_upload` gained an optional `parent`; behaviour without it is unchanged). Also touched,
  not on the protected list: `whatifs/contract.py` (check `palace_health` added), `whatifs/truth.py` + `tools/gen_docs.py` (walk sub-packages),
  `tools/rehearsal.py` (Palace assertions).
- B0: `whatifs/reels.py`, `whatifs/render.py`.
- B1b: `whatifs/core.py` (3 defaults changed: STANDARD_MAX_LONG_PER_MONTH, PUBLISH_DAYS, VIDEOS_PER_MONTH_EST; 1 new cell), `whatifs/manage.py`
  (`v12_upgrade` added + 2 calls), `whatifs/governor.py` (`long_videos_per_week` added; no existing rule changed).
- B1: `tools/plan_guard.py` (truth hook added), `whatifs/contract.py` (check `docs_current` added; no existing check changed), `whatifs/core.py`
  (10 settings NOTES reworded, no default value changed), `tools/repair.py` / `whatifs/governor.py` / `whatifs/publish.py` / `whatifs/episode.py` /
  `whatifs/manage.py` and the other protected modules: docstring line only.

## OPEN ISSUES
1. (D6/D8, for B6-B7) Rain particles ("office" world) can read as a still for some seeds (aliveness 0.0 seen). Now deterministic, and seed 7 passes,
   but the particle layer has no guarantee per seed. Proper fix: after rendering, measure aliveness and re-seed/boost when below the bar (needs an
   enforcement check + failing test).
   MEASURED in B0b (real 1080p, 12 seeds x 4 worlds, one 4-second shot each, flat depth, push-in): 43 of 48 shots 100% alive; rain 57% / 71% / 86% on
   seeds 8 / 2 / 9, embers 71% on seed 10; dust and wind 100% on every seed. No id of the 58-run sweep failed check `aliveness`. Still open for B6-B7.
2. (B1b follow-up, low, for B9) In a month with 5 Saturdays one week has no long video (cap 4). By design today; D1 planning (B9) may choose which
   Saturday to skip or spread differently. `DIGEST_DAYS` (owner digests) still Tue,Sat,Sun - unrelated to publishing, left as is.
3. (NEW, low) `mission_control/worker.js` line 27 comment still says fixes were "recorded in CHANGES.md". Left alone on purpose: it is a comment in the
   deployed Worker file, and JS comments are outside the scan. Fix it the next time the Worker is changed anyway.
4. (laptop) Test temp dirs `mt_*` accumulate in `%TEMP%`; automatic cleanup of that shared folder was blocked by the app's safety rule. Disk free
   333 GB, so no risk; delete by hand only if space ever gets tight.
5. (handoff folder, outside git) The handoff `CLAUDE.md` still says the repo's own CLAUDE.md "is historical until batch B1 rewrites it". B1 has
   rewritten it; the sentence is now simply spent. No action needed.
6. (B2 -> B6 / B8) A few low-priority limits do not fit an 1,800-token playbook: D1 3, D4 4, D12 1, Council 6 (5 before B4: the Council now also gets
   the item that says how a ticket must look) (lowest priority first out; the health
   check reports it as a note). Fix belongs to the Council / Librarian: merge overlapping limits, or raise the cap for those departments - since B4
   there is a lever for that (`PALACE_PLAYBOOK_TOKENS_BY_DEPT`, owned by L; a ticket to L reaches the engine once L is wired in B8).
7. (B2 -> B8) An edit of the `Palace_Items` tab made outside the code is recorded as `external_edit` only when upkeep runs before the next Palace
   write. Served content is safe either way (the guard re-checks every row); only the audit entry can be missed.
8. (B2 -> B5) Founding tool facts expire 60 days, and the two plans 45 days, after they are first written to the live Sheet (the clock starts at
   seeding, not at the date of the research) unless re-validated. By design; B5's research cadence has to re-validate or replace them.
9. (B2 -> B10) The Palace's real Google Sheets / Drive path is proven with the local store and stubs only (no keys on this laptop, by rule). The
   first learning job after the merge writes 92 rows in one append and makes no Drive call (founding bodies resolve from the repo). B10's first-run
   verification must check tab `Palace_Items` and `palace_health` in `Feature_Ledger`.
10. CLOSED in B3: `whatifs/org/palace.py` and every org module are on the `tools/repair.py` PROTECTED list.
11. (B2, low) `Palace_Versions` numbers come from the last row + 1: two jobs writing in the same second could reuse a number (timestamp and hash
   still tell them apart; the tick's concurrency group makes it unlikely).

12. (B3 -> B6) Brief mode is a hand-over: no model prompt contains Palace knowledge yet. B6: set `inject` to "prompt" for D4-D7 in `registry.DEPTS`
   (and `inject_tasks` if the blind judges must not be handed the playbook), add `applied_items` to the creative outputs, build `palace_injected` /
   `palace_cited`. An adopted Script Preview makes no model call, so in prompt mode it would (correctly) breach: wrap the preview room first.
13. (B3 -> B5 / B6 / B9) Not under the runner yet: Script Preview and pre-production room runs (`whatifs/preview.py`, `preprod.py`), standalone Shorts,
   specials, Case Files, Deep Trial, packaging rescue, releases (Reels), the research and trends jobs. Each needs its call site + registry entry in
   its department's batch; B10 must end with `registry.PENDING` empty.
14. (B3 -> B6) D7's voice run covers the first narration only; the "too short -> extend -> narrate again" loop re-narrates outside the run.
15. (B3 -> B7) A step that keeps crashing may reach the owner twice: the pipeline's existing failure mail and the stuck-item message (after the third
   attempt or 24 h; weekly tier unless P0). B7's repair loop must make it ONE path.
16. (B3 -> B7) `promise_paid` is judged at the final gate although the shot plan exists at the script gate: a failure costs the picture money first.
   Proposal: judge it at the script gate too (needs shots and units in the script-stage context).
17. (B3 -> B6 / B8) Proposed takeaway items wait in the Palace until the Council exists. Bounded by class (department x step x signature), not by runs.
18. (B3 -> B10) About 9-10 extra Sheets calls per department run, 9 runs an episode: proven on the local store only. First-run verification must watch
   for quota errors and look at tabs `Memos`, `Sessions`, `Takeaways`, `Org_Audit` and at both organisation checks in `Feature_Ledger`.
19. (B3 -> B9) The SLA hours are the master spec's defaults, not tuned. D1 owns tuning (setting ORG_SLA_HOURS).
20. CLOSED in B0b (the ids are traceable now: a failed test prints its episode ids onto the public run page, a red rehearsal prints its id and the
   command that reproduces it, and `tools/sweep.py` runs any id on any machine). Was: (B3, low) `tests/test_integration.py` and the rehearsal still make time-based episode ids and the fake pipeline is seeded by the id, so another
   id-dependent fault could surface on some minute. That is a feature while faults remain: trace it, do not re-run it away.

21. CLOSED in B0b (every run read; run 38 reproduced with the id of its minute: the stale promise flag; standing rules 1-2). Was: (FOUND 10 Nov after B3, verification gap of B0-B3) GitHub runs the `Checks` workflow on EVERY push of this branch (Ubuntu, Python 3.11, real pytest,
   then the fake rehearsal) and no batch ever read its result: every "green" in this file is the laptop (Windows, the stand-in test runner). Read on
   10 Nov (step outcomes are public; log lines need a GitHub sign-in): baseline RED at unit tests (expected, before B0's fixes); B0 GREEN; B1 final
   GREEN; B1b final GREEN; the two mid-batch commits of B1 / B1b RED at unit tests (the 939 / 1 and 948 / 1 already recorded above, fixed one commit
   later); **B2's final commit c54b9b6 RED at the REHEARSAL step (unit tests green there)** although the laptop rehearsal was green; B3's first three
   commits GREEN; B3's final commit 6b89d83 was still running. Best hypothesis for the B2 failure, NOT confirmed (no log access): the stale promise
   flag fixed in B3, which holds the rehearsal's episode on some minutes. To do: confirm from the log, sweep the fake pipeline over many fixed episode
   ids, and make "the batch's final commit is green on GitHub" part of every batch's acceptance.
   Where to look: https://github.com/Rahul4869/reality-engine/actions?query=branch%3Av12-organisation

22. (B0b -> B8, OWNER DECIDED 10 Nov 2026: "build") The blind test "writers' room script against a single-prompt script" was NEVER BUILT: 3 Settings
   cells (`ROOM_VALUE_ON` default TRUE, `ROOM_VALUE_EVERY`, `ROOM_MIN_WINRATE`) and tab `Room_Value` exist, no code does. The owner was asked "build it
   with the learning loop (B8), or drop it?" and answered "build" (Palace item `owner.room_value_test`, addressed to D10). B8 builds it inside the full
   batch loop: strong blind judges of another model family (cheap models never make taste calls), cost logged and counted in the estimates (the old
   note says about Rs 15 a video - re-estimate it), fake replies, a switch, a matrix row, the win rate where the owner sees it. When it runs: delete
   the three cells from `truth.UNREAD_SETTINGS` and the tab from `truth.UNUSED_TABS`, drop the NOT ACTIVE marks. Until then the cells do nothing.
23. (B0b -> B4 / B7) `CACHE_ALIGN_EFFORT` is NOT ACTIVE: two calls with different effort on one cached prefix cost one extra cache write each, on every
   episode (fake episode: 2 misses; an estimated Rs 3-10 a video, at most about Rs 40 a month at 4 videos; NOT measured in production). Wiring
   `models.aligned_effort` as written would change the effort of a creative or judging call to whatever came first - against 'breakout first'. Options
   for the batch that owns model levers: per-message effort (`CACHE_EFFORT_PER_MESSAGE`, needs a real API call to prove), or retire the cell.
24. (B0b -> B6) `show.bible_issues` (protected names, real people, child characters, audio chain) is called by tests only: a hand edit of the
   `Characters` tab is not checked in production. The seed bible is clean (a test proves it). B6 wires it into a check when it wraps the creative departments.
25. (B0b -> B6 / B7 / B10) Never wired, harmless today, each to be wired or removed by its department's batch: cells `RUNTIME_HARD_MAX_SEC`,
   `PKG_VARIANT_C_IMAGE`, `VIEWER_NAME_ON_SCREEN`, `PREMISE_BENCH_MAIL_MONTH`; functions `enforce.fix_markers`, `enforce.fix_retention`,
   `prompts.episode_pack`, `publish.meta_bio`, `data.ptype_for`, `shotplan.prompt_variety`; tab `Repairs`. B10 must end with the three lists in
   `whatifs/truth.py` as short as they can be and say so in the PR.
26. (B0b -> B10) The atmosphere's time valve (`ATMOSPHERE_MAX_OVERHEAD_PCT` 30) switches its particles off on EVERY small fake render (153% measured),
   so the rehearsal never shows the full set of layers after frame 120 and says nothing about full size. First-run verification must read
   `Episodes.atmos_json` (`dropped`) of the first real videos; if layers are dropped there, D6 tunes the cell.
27. CLOSED on 12 Nov 2026 (the owner allowed tools that help, item 21 of `02`): Node.js is installed and the dashboard test runs on the
   laptop (HOW TO RUN, "TOOLS INSTALLED ON 12 NOV 2026"). Was: (B0b, laptop) One test still skips on the laptop: the dashboard render
   needs node (GitHub runs it). Install node only if a batch changes the Worker.
28. (B4 -> B6) Knowledge and rule levers (A, D) are verified as SERVED (the item, in that version, was in the playbook of a later complete run). CITED
   is demanded by the same verifier as soon as a department runs in `prompt` mode (B6, open issue 12). Until then "verified" for A / D means handed over.
29. (B4 -> B10) The code lever (E) has never run against the real GitHub: `builds.pr_files`, `builds.commit_state`, the dispatch of `checks.yml` on main
   after a merge, the new `request` input and the moved credentials in `claude-build.yml` are proven with stand-ins, by a YAML test and by reading.
   First-run verification must watch the first organisation build end to end. If the checks on a merge commit never report, the ticket is escalated
   after `EXEC_VERIFY_DAYS` (never reverted on a guess).
30. (B4 -> B6 / B8 / B9; D2 and D3 unlocked in B5) A ticket for a department that has no wired run (D0, D1, D11, C, L) goes straight to the owner's level (B3 rule),
   so the 16 levers of those departments are in the table but cannot be turned by ticket yet. Each batch that wires a department unlocks its levers.
31. (B4 -> B7) A rollback reaches the sender only through the ticket's resolution note and an `Org_Audit` row (kind `lever`). No problem memo and no
   failure lesson is written for it yet: B7's repair loop must feed rollbacks into both.
32. (B4, low) The tick job and the produce job can touch the same ticket at the same moment (two processes, one Sheet, no lock). The engine's steps are
   idempotent (same item id, compare-and-swap, a recovery pass for a half-done apply), so the worst case seen in thought is a doubled ledger row.
33. (B4 -> B6) A script written BEFORE a setting change (an approved Script Preview) and adopted after it is judged against the new bar and counts as
   "made after the change". A stricter bar can so fail an older draft and roll the setting back. B6 wraps the preview room: stamp the draft with the
   lever values it was written under.
34. (B4 -> B9) The owner's approval message for a lever goes out on tier `week` unless the ticket is P0 (as the stuck-item message does). D0 may want
   `now` for approvals; and an approval that is never answered rests on his list after the usual reminders.
35. (B4 -> B6 / B10) `EXEC_AUTO_MERGE_ON` defaults to TRUE with a scope of NEW TEST FILES ONLY. The master spec says "tests + rules only": narrowed on
   purpose (rules have lever class D). Tell the owner in the final PR; he can widen it or switch it off.
36. (B4 -> B7) `CACHE_ALIGN_EFFORT` (open issue 23) was NOT taken up in B4: it is not a lever of any department. Still open for B7.
37. (B4, low -> B10) GitHub's run page shows one warning that is GitHub's own: Node.js 20 is deprecated and `actions/setup-node@v4` (in `checks.yml`) is
   forced onto Node.js 24. Green today; move the action to its next major version when a batch touches the workflows anyway.

38. (B5 -> B6) Assessment memos wait silently at the owner's level until the Council is wired (C pending); research memos that the watchdog escalated
   after a void Board session can no longer be assessed by D3 (it is not their holder). The Council's first run must take up both.
39. (B5 -> B6) Re-validation: a research memo about an expiring Palace fact carries `palace_ref`; only the owner, the Council or D10 may re-validate,
   so founding facts still expire until B6's Council issues the A ticket (open issue 8: the research side is closed, the Palace side is not).
40. (B5 -> B10) Real APIs never touched (no keys here, by rule): the web-search citation blocks (`cited_text`, `page_age`), Gemini grounding chunks
   (domain-level match, titles are domains), the liveness check from GitHub's runners and the real cost per question are proven with stand-ins and the
   documentation. First-run verification must read tab `Research_Agenda` (notes: ceiling, kept, dropped, rupees) and `Board_Log` (families, models).
41. (B5 -> B8) Message Batches are not used for research or the Board: searches cost the same in a batch, only tokens halve (about Rs 4 a question),
   and the batch API throttles searches while the job waits. Decide on measured cost (RESEARCH_EST_INR follows the median measured cost).
42. (B5 -> B8) Predictions are stored and validated but nobody scores them yet against later videos; D10's learning loop (B8) should score them
   (research yield per gap source, which kinds of advice came true).
43. (B5 -> B9) The owner sees research verdicts nowhere yet (no digest, assessments are silent until the Council exists); D0 (B9).
44. (B5, low) Inside one weekly run the in-run budget guard counts the last successful model call of each question only; the monthly figure in
   `Org_Audit` (and so the cap) is exact. The manual `research.yml` workflow (`cli research`) still runs the topic brief outside the runner.
45. (B5) Liveness from GitHub's runners: a site that blocks robots (401-429) counts as alive, a timeout counts as alive, 404 / 410 / no host is dead.

46. (B5, low -> B10) GitHub's run page now notes that the `ubuntu-latest` label moves to Ubuntu 26 from 19 Oct 2026. The Checks pin Python 3.11 and
   the library bounds of requirements.txt, so the move should be quiet; if a run turns red right after it, read the annotation for a system library
   (ffmpeg, fonts) first. Pin `runs-on: ubuntu-24.04` only if that happens.

47. (B5 sweep, medium -> B6 or the next batch that touches the Script Room) `whatifs/similarity.py:check` compares a script with the last 10
   fingerprints INCLUDING the same episode's own earlier one. Any episode scripted twice (seen in the rehearsal's re-render; NOT checked whether
   a production re-run does it) is reported 'N% similar to itself': a degraded step and a false `similar_script` owner message. Fix: skip rows whose `episode_id` equals the
   episode (replace that episode's fingerprint instead of appending a second); test both ways (a twin of ITSELF is not similar, a different
   episode at the same score still is). Not a weakened check - the comparison with other episodes stays.
   FIXED in B6a: `whatifs/similarity.py:check` compares with the last 10 fingerprints of OTHER episodes and keeps one fingerprint per episode
   (a re-scripted episode replaces its own); test_a_script_is_never_similar_to_its_own_earlier_draft_and_a_copy_of_another_episode_still_is.
48. (B6a -> B8) A verified citation proves the quoted line EXISTS in the output, not that the knowledge CAUSED it (a model can still quote a line
   it would have written anyway). The callback to the last case must name the case (code), but a general technique has no such topical test.
   The causal measure is design G (parked): D10 re-runs one creative call without the playbook as an experiment arm and compares; and D10's
   outcome attribution per applied item (applied_count, outcome_score). B8.
49. (B6a, one-time cost, tell the owner in the PR) On the first production after the merge, an AUTOMATIC pre-production draft written before
   B6a is superseded (it never saw the Palace) and production writes the script again under D4 at the normal price instead of using the
   half-price draft, once (the draft already paid is lost: the writing is paid again, about Rs 150-180 by the LLM_EST_INR allowance). An owner-approved draft is kept (his decision) and judged as written before B6a.
50. (B6a -> B6b) The Council's playbook leaves 5 limits out at 1,800 tokens: give C its own cap or narrow audiences before the Council runs.
51. (B6a, low) D7 Sound has no model call inside its run (TTS + code), so it can neither cite Palace knowledge nor propose; sound ideas reach the
   show only through the bible (D4). Revisit if a D7 model step is ever added.
52. (B6a -> B7, medium) `palace_cited` and `canon_in_brief` are hard gates before picture money. In fake mode the offline model cites
   perfectly; a REAL model may cite sloppily (no `applied_items`, a quote from a line a later pass rewrote). D4 is robust (the showrunner's and
   the bible's quotes sit in the room output untouched), D5 and D6 quote from one call each. A miss HOLDS the episode with an owner card - the
   enforcement the owner asked for, but a hold for citation mechanics is not a quality problem. B7's repair loop (problem memo -> at most 2
   automatic repairs -> Council -> owner) should give the department ONE automatic re-ask ('cite again, quoting your final answer') before the
   hold. Until then: read `unverified` / `ghost` in the Sessions row; the off switch is ORG_PROMPT_INJECT, never a lower bar. Note: the two
   losing drafts of the writers' room are always listed as `unverified` (their text is not in the final script) - that is expected, not a fault.

53. (B5 recheck -> B10, with 40) Source positions: counting from 1 is detected only in the clear case (no finding names source 0 and one names a
   position past the end). A reply that counts from 1 and never cites its last source is NOT detected: its findings sit on the neighbour's
   source (a real source, the wrong one). The prompt now says "the first source is 0". Read the first real runs: compare each finding with the
   quote of its source.

54. (B5 recheck, by design) When the learning job was dropped, the production job runs the research round first: the weekly research and a Board
   session can then sit at the start of a production job (minutes; paid inside the D2 / D3 caps, never production money; limit 340 minutes).

55. (B5 recheck -> B10) The learning job's limit is 60 minutes now. How long the weekly day really takes is unknown (web search, up to 12
   liveness checks a question, 4 judge calls). Read the duration of the first real weekly run on the Actions page; if it nears 60, bound the
   questions of one run by time (the rest stays open on the agenda).

56. (B5 recheck -> B9) The owner's own questions are asked past the cap with NO count limit, and asked again every RESEARCH_REPEAT_DAYS while the
   owner memo stays open. Nobody writes owner memos until D0 exists (B9): B9 must close an owner memo once its research was assessed, or cap
   the repeats.

57. (B5 recheck, by design) A memo a department writes to itself (void Board session, barren research) is escalated after the 2-hour acknowledge
   clock, so the owner hears of it within hours (one message, bounded reminders) and the next good run closes it. If that is too loud in real
   life, give self-addressed memos the department's own cadence as their acknowledge clock (`schemas.py`) - not changed here.

58. (B5 recheck) When the SECOND family (Claude) is down, the first one (Gemini) has already been paid before the session is void: it cannot be
   known beforehand. Bounded by the research memo's deadline (it climbs away from the Board) and by D3's cap.

59. (V1a -> V2) Long videos carry no burned-in captions (YouTube's own caption track is uploaded; Shorts have word-by-word captions). Evidence
   for burning them into a narrated long video is weak (Mayer: 0.10). V2 puts captions on the hook and tests the rest as a lever.

60. (V1a -> V2, the device diet) The show's required devices produce numbers themselves (the time ladder's "hour 1", exhibits with years, a
   prototype number). The counter exempts story marks and source years; when the devices become optional per format, review the exemptions.

61. (V1a -> B8) NUMBERS_PER_MIN_MAX 4, GRAPHICS_MAX_LONG 3, GRAPHICS_FREE_SEC 60 and BREATH_EVERY_S 30 are starting values from the owner's
   verdict, not from a controlled study (none was found). They are levers of D13; the learning loop must score them against real retention.

62. (V1a -> V2) The Shorts track (`shorts2.py`) is not under the viewer's seat yet; V2 rebuilds Shorts as hooks and puts them under it.

63. (V1a, correction of item 16's facts) The "+0.8 dBFS true peak" was measured on a re-encoded download of the video; the pipeline limits its
   own master to -1 dBTP (`render.py`, check in `qc.py`), so it is not evidence of clipping. The loudness range (4.1 LU) is normal for narration
   and is not a gate. The measured faults that stand: 6 pauses in 13 minutes, the number cards, the opening, the length, the black shapes.

64. (V1a -> B7) A viewer's-seat failure that code cannot repair holds the video with an owner card. B7's repair loop should give the owning
   department ONE automatic repair first (a hold for too many numbers after the writers' fix is rare, but it is an owner tap).

65. (V1a -> V2) The promise rule needs an animated scene to ride on: when the money trims all animation the check says NA. V2's fully animated
   hook removes the case.

66. (V1a, money, low) A number graphic that the seat turns into a picture can cost a fresh still (under Rs 1): 2 in the fake episode; the
   repetition guard of `episode.anchor_shots` may add up to 12 in the worst case (about Rs 7 a video). Counted in the paid-call counter
   (`tests/paid_calls.py` V12V1_ADDED). If real videos show more than a few, give seat-converted shots their own small cap.

67. (V1b, recognition by affix) An everyday word that is built like an expert word and is not on `whatifs/org/seed/everyday.txt` is counted
   ("psychological" was found by scanning the offline writers and exempted). At the pilot (V3) read the counted words of every real script in
   the `viewer_plain` evidence and exempt the ordinary ones - never an expert word, never a looser rule.

68. (V1b, the measure is a floor) It misses every expert word that is not on `layman.EXPERT` and carries no scientific affix: engineering and
   business words ("integration", "reduction" - the Ohio State study's own example passes), and new coinages. Add to the list when one is seen.
   The real measure of "a layman knows this word" is a frequency list of spoken English (a data file whose licence allows it): a question for
   the tool scout (V5).

69. (V1b -> V2 / V5) The line-up's other titles are a built-in list of 10 about other subjects, so it catches an opening that does not NAME its
   subject, not one that names the subject without making the promise. Same-subject titles (the runner-up titles of the package, our own past
   titles, the Observatory's finds) would make it harder; needs care that a runner-up title is not also true of the video.

70. (V1b -> B7) A `viewer_plain` or `viewer_probe` failure after the writers' one fix holds the video with an owner card (as issue 64): B7 gives
   the owning department one automatic repair first.

71. (V1b -> B8) Whether scripts inside the expert-word budget hold viewers longer is unproven (H8); the three budgets are starting values.

72. (V1b, money, low) The line-up's two reader calls (about Rs 0.2 a video, Rs 1 a month) are logged in Cost_Log and counted by the paid-call
   counter but are not a line of their own in `costguard.estimate_lines` / `governor.min_episode_cost_inr` (they sit inside the Rs 40 thinking
   lump). CLAUDE.md hard rule 2 asks for every new paid call in the estimates: V2's cost model adds the line.

73. (V2a -> V3) F1's brief ("The day it changed") has only met the offline test writers. The first real F1 script is the pilot's first
   evidence: read it against the brief (courtroom words, two voices, the day from the bathroom to the planet, the question at the end).

74. (V2a -> V2b) In F1 the three asks, the tease and the emotion beat are still asked for by the writer's base prompt and inserted by code
   (`CTA.ensure`, `room.ensure_tease`). They can no longer hold a video, but they are still in it. V2b: F1's own ending replaces them.

75. (V2a -> V2b) In F1 the speaker chip says "THE DIRECTOR" / "THE CURIOUS ONE" (`overlay.name_of`), and the silhouette fallback for reaction
   shots exists in every format. "A character is drawn or absent" is V2b.

76. (V2a -> V2c) Shorts or special reels made by OTHER jobs after the episode (no format in the making) follow the global switches, so they
   treat every episode as a trial. V2c rebuilds Shorts as hooks and gives every job the episode's format (it is in the draw).

77. (V2a, the canon) The canon (B6a) is the trial's world: an F1 writer still receives the cast items and the callback duty; the F1 brief
   tells him to use only the two leads' temperaments and one plain callback line. A real model may leak courtroom words - `format_kept` then
   holds the video (an owner tap). Watch at the pilot; the real fix is a playbook that knows the format.

78. (V2a -> V4) The format shares are levers of D1, which is not wired yet: until V4 nobody moves them. FORMAT_FORCE is the manual override
   (the pilot uses it).

79. (V2a) The first episode of a Sheet is drawn by its id (70 / 30 by chance); from the second on the shares hold over the last ten.

80. (V2a, tests) The older tests run in forced F2 (`tests/conftest.py`). F1 is covered by `tests/test_v12_formats.py`, the rehearsal with
   `WI_FORMAT=F1` and the sweep's mix - not by the whole suite. GitHub's own rehearsal draws its format by a time-based id (about 7 of 10
   runs F1): a fault in one format can show on some runs only; the laptop proof runs both.

81. (V2c-a -> V3) Only the offline writers have written a Short. At the pilot read the first real scripts against the brief (a hook that
   ends inside 3 seconds, the format's four beats with their names, the returning word in the last line) and the `short_*` evidence in
   `Feature_Ledger`; a real model may name its beats differently, and `short_kept` then holds the Short after the one fix.
82. (V2c-a -> V2d / V3) Three picture choices no fake run can judge: a clip played up to 30% slower to cover its shot
   (`shortseat.STRETCH_MAX`), a clip started on the frame the clip before ended on (drift over a chain is unknown - redesign R19), and the
   first clip played backwards as the loop (motion that only reads forward - falling, pouring - may look wrong). V2d's model with longer
   clips removes the first; the pilot shows the other two; each is one constant or one format row to change.
83. (V2c-a, money -> V2d) A Short is estimated at about Rs 290 in the middle of its band at today's hero price (the redesign planned Rs
   150): twelve a month do not fit beside four long videos until V2d chooses the model by value. The writing (three scripts on the long
   script's model, the jury, one fix) and the voice sit inside the old cell REPLAN_SHORT_INR (Rs 36) - not measured; a Short has no line in
   `costguard.estimate_lines` (the family of issue 72). V2d's cost model.
84. (V2c-a -> V2c-b) The cadence is untouched: SHORTS_PER_DAY (1.5) still decides when a Short is due; SHORTS_KLING_EVERY is read only by the
   re-planner (a stale rung); JOKE_EVERY_SEC_SHORT only by the cut-down reels. The live channel does not run this track.
85. (V2c-a -> V2c-b) A Short is still uploaded by `specials._publish` from inside `shorts2.run` (the special reels' tags, one text for
   every platform, no D9 run, nothing read back). The first 3 Shorts wait for the owner's Approve as before.
86. (V2c-a -> V2d) The loop on the finished file is measured and REPORTED (lesson `loop_open`), not a gate: a Short whose loop did not
   close is a code fault, and the clips are paid by then. The plan's loop shot is a gate (`short_shape`). `moving_share` on the file is V2d.
87. (V2c-a, the hand-back) The rule asks for a content word of the first line in the last line. A writer who hands back with another word
   for the same thing ("mirror" / "reflection") is held after the one fix and the Short is not made (the topic is tried once more). Read the
   `short_shape` evidence of held Shorts at the pilot; if it happens, let the writer NAME the returning picture and verify that instead.
88. (V2c-a) "One idea" is not measured: code cannot recognise it. It is carried by the format's four beats and the brief.
89. (V2c-a -> B7) A held Short gets no repair beyond the writers' one fix. Its problem memo (one per class of failure, no episode) waits
   for the next Short that passes; a class that never passes climbs to the owner by the memo clocks. B7's repair loop should own it.
90. (V2c-a, the learning core) The Short's FORMAT is recorded in `Video_Features.lead` (nobody is on screen), so the learning core
   compares S1, S2 and S3 as the family "lead". Say so wherever that family is shown to the owner (V4).
91. (V2c-a -> V2d) The sound of a Short is still the special reels' code-made bed (a drone, a hit per beat). "The first-second sound of a
   Short" (redesign 11.8, D7) is not built.
92. (V2c-a -> B10, with 18) Five department runs a Short (about 50 Sheet calls) are proven on the local store only.
93. (V2c-a, CLOSED / narrowed) Issue 13: the standalone Short now runs under the department contract (D14, D7, D13, D8); specials, Case
   Files, Deep Trial, packaging rescue and the releases still do not. Issue 62: closed (the Short is under the viewer's seat). Issue 76:
   the standalone Short has its own format and never the trial layer; the cut-down reels and the special reels made by other jobs still
   follow the global switches (V2c-b).
94. (V2c-a -> V3, BEFORE GO-LIVE) Twelve other workflows (production, pre-production, learning, specials ...) still install ffmpeg with
   the unbounded line `apt-get update && apt-get install ffmpeg`. On 11 Nov 2026 GitHub's regional Ubuntu mirror did not answer for hours:
   a production job would have hung up to an hour and made no video. `checks.yml` has the bounded step with a second mirror (its fallback
   branch has never run for real). Give the other workflows the same step - and one test that every workflow's install line is the
   bounded one - in the batch that prepares the pilot, and watch the first runs.
95. (V2c-a, the Palace note) `python -m whatifs.org.palace` reports limits that do not fit a playbook cap as "D1 3, D2 1, D12 1, C 5"
   (open issue 6 recorded D1 3, D4 4, D12 1, Council 6 before the writers got their own cap). None of this batch's items is addressed to
   those departments; D2's one limit was not traced here. The Librarian's batch (B8) owns it.
96. (V2c-b1 -> V2c-b2) A promoted topic's long video still opens with its OWN pictures: the Short's footage is kept (tab `Ladder`,
   column footage) and not used yet. The footage is vertical (9:16); how it opens a 16:9 video - a crop that travels down the frame, or a
   framed layout - is V2c-b2's design decision and can only be judged on real clips (the pilot).
97. (V2c-b1 -> V3, TELL THE OWNER AT THE PILOT) A Short's true numbers exist when it is about five days old (YouTube is 48 to 72 hours
   late), and the first three Shorts wait for his Approve first. So the first long video of the new code needs a Short that has been
   public for five days - or his override ("Make it anyway" on the refusal message). The pilot's one long video will need the override;
   the pilot guide must say so before he is surprised by a long video that "waits".
98. (V2c-b1 -> V3 / B10) Real APIs never touched (no keys here, by rule): the day-by-day Analytics report with one video as a filter
   (`brain._short_days`: views, engagedViews, averageViewPercentage, shares, subscribersGained), the Pacific-day start (8 hours; 7 in
   summer), a day without activity returning no row (the coverage then follows the documented latency, `brain.LATENCY_DAYS`). First-run
   verification must read tab `Analytics` (days, first_json, data_note) and tab `Ladder` after the first week of Shorts.
99. (V2c-b1 -> B8) Starting values without a study behind them: the four measures with equal votes, the floor of thin evidence (30
   engaged views; a tenth of the pool's best), the 3-times line at the 24-hour and 48-hour mark, the 10,000-view line without history,
   the 48-hour clock, the 30-day window. All are levers or constants in one place; H11, H18 and H19 need the learning loop to score them -
   the pairs are on record (a `Ladder` row with its numbers and the episode it earned).
100. (V2c-b1) A Short whose upload is held ("uploads not confirmed open") or that the owner never approves stays MADE on the ladder: it
   has no numbers and can never be promoted. Harmless, but nothing reminds him beyond the review message itself.
101. (V2c-b1 -> V2b / V4) Under the ladder a long video's end tease names the ladder's runner-up or the next bench topic. The promise
   breaks when a newer Short wins the next promotion (the rule decides by numbers, never by the tease). The cell NEXT_PREMISE is still
   written at scheduling and is no longer taken up while a promoted Short exists. V2b (F1's own ending) should decide what an ending
   promises. D1 "owns the split" in the redesign; the cadence levers went to D14 (the task's wording) and D1 is not wired until V4.
102. (V2c-b1, FOUND, not this batch's) `whatifs/dash.py` SETTINGS_MAP: the entries "localizations" and "affiliate_block" sit inside a
   comment on the same line since the standalone Shorts track was added, so those two dashboard switches answer "not allowed". And the
   sample data inside `mission_control/mission_control.html` still shows an old monthly cost. Fix with the next dashboard change.
103. (V2c-b1 -> V4) A LONG video's 48-hour breakout still asks the owner to approve two follow-up Shorts (the old card); only a Short's
   own breakout is decided by code. One rule for both belongs to V4.
104. (V2c-b1, tests) The older tests run with LADDER_ON FALSE (`tests/conftest.py`), as they run in forced F2: the ladder is covered by
   `tests/test_v12_ladder.py` (two whole productions among them), the rehearsal (it walks the ladder) and the sweep (`climb`), not by
   the whole suite.
105. (V2c-b1, FOUND AND FIXED; the family is wider) A Short's hook came from an unseeded random draw, so a sweep id did not reproduce its
   Short and one test of V2c-a failed about once in eleven runs. The draw is seeded by the Short's id now. NOT checked here: whether
   the long video's sampler draws (`brain.choose` from the writers' room) are seeded by the episode id.
106. CLOSED / narrowed in V2c-b1: issue 84 (the cadence: closed); issue 85 stays for V2c-b2 (a Short is still uploaded by
   `specials._publish`; nothing is read back); the redesign's O5 and O8 (how many Shorts) stay watched by D1 (V4).
107. (V2c-b1 -> V2c-b2) Whether a Short was MADE hangs on a status text: `shorts2.UPLOAD_HOLD` is the beginning of the sentence
   `specials._publish` writes when uploads are not confirmed open (a test ties the two; a refusal at the short gate also begins with
   "HELD"). V2c-b2 rebuilds the upload under D9: give a Short its own field for "made" apart from where its upload stands, and retire
   the text match. Issue 100 (such a Short stays MADE on the ladder with no numbers) stays open with it.
108. (V2c-b1 -> B7) A Short whose job crashes is tried again once a day with no end: a try whose crash comes after the writing has paid the writers (the old
   allowance of about Rs 36), nothing counts the tries, and the owner hears of it only through the department run's
   own problem memo and its clocks. B7's repair loop should own it: one memo per class of crash and a stop after a few tries.
109. (V2c-b1, the proof) The crash row and the upload hold are proven by unit tests and deliberate breaks only: the sweep's Shorts
   never crash and its uploads are always open. Which sweep id, if any, showed the three faults of step 6d is not known (the session
   that found them was cut off without a note).
110. (V2c-b1, FOUND, not this batch's) `last_error.txt` in the repository's root is a TRACKED file: a red rehearsal on the laptop
   rewrites it, and four commits carry it with a laptop traceback (a local folder path in a public repository; no key, no
   address). The workflows only upload it from their own runner. Untrack it and add it to `.gitignore` with the next change that
   touches the workflows; until then never `git add` it.
111. (V2c-b2a -> V3 / B10) Real platforms never touched (no keys here, by rule). Proven with the offline stand-in and the platforms'
   own pages only: `publish.yt_read` (videos.list with the parts snippet, status, processingDetails; YouTube often leaves
   `containsSyntheticMedia` out of its answer - the row is then SENT, not KEPT), a Reel container with `trial_params`, `audio_name` and
   `thumb_offset` on the resumable upload, `ig_read` (Instagram shows `caption` only with Facebook Login), `fb_read`
   (`status.publishing_phase`). The pilot must read tab `Release_Sheet` of the first three Shorts row by row (state, receipts, note)
   and the `release_sheet` evidence in `Feature_Ledger`.
112. (V2c-b2a -> V3, TELL THE OWNER AT THE PILOT) A custom thumbnail needs a phone-verified channel (one of his one-time switches,
   redesign 11.7). Until then YouTube refuses the call, every Short's sheet fails on the row `thumbnail` and Publishing's memo climbs
   to him. Either he verifies FIRST (make it the pilot guide's first step) or `SHORT_THUMB_ON` is set to FALSE until he has.
113. (V2c-b2a -> V3 / V4) Trial Reels on an account with almost no followers: a trial reel is shown to non-followers only, and whether
   one that never graduates ever shows on the profile is unknown - the Instagram profile could stay empty. `IG_TRIAL_REELS_ON` is a
   lever of Publishing (redesign O13, H20). Whether `trial_params` and `share_to_feed` may be sent together is unknown too:
   `share_to_feed` is left out of a trial reel.
114. (V2c-b2a, low -> B10) Drive housekeeping: every Short's master (about 20 MB) and cover stay in the owner's Drive, and each
   Instagram upload leaves one copy of the cover that was public for a minute (made private again, never deleted - the pattern the
   cut-down reels' covers already use). The footage archive is deleted when a topic leaves the window; the master is not.
115. (V2c-b2a -> B7) A row a platform did not keep is ONE problem memo per class (`gate|release|release_sheet`) to D9, closed by the
   next Short whose sheet passes. So the fault of one Short (a Reel that never went up after three tries) is "closed" by the next
   clean Short although that Reel is still missing; tab `Release_Sheet` keeps the truth (FAILED). B7's repair loop should own what is
   past the limit and tell the owner which Short is missing where.
116. (V2c-b2a) An upload that comes back private trips the lock (as before), but the Short keeps its YouTube id, says POSTED on tab
   `Specials` (privacy DRIFT on its sheet) and the ladder starts its clock. Harmless while the lock pauses everything; after the lock
   such a Short is public only if he publishes it by hand (the lock mail says so).
117. (V2c-b2a -> B10, with 18 and 92) Sheet calls: a Short's release adds two department runs (about 20 calls) and the tick's pass reads
   tab `Release_Sheet` every 30 minutes (one call; one more for `Specials` while a record is open). Proven on the local store only.
118. (V2c-b2a -> V2c-b2b) The cut-down reels (`manage._post_reel`) and the special reels (`specials._publish`) still go out the old
   way: one text for every platform, "#shorts" in title and text, the tags "shorts" / "what if" / "reality on trial", nothing read
   back, no record. V2c-b2b decides what stays of the cut-downs; whatever stays must go out through `release.py` (tab `Release_Sheet`
   has the column `kind` for it).
119. (V2c-b2a, the hook under a Short) What stands first under a Short is the first SENTENCE of its script as its record kept it. A
   hook of three words gives a thin first line on Instagram. Read the first real captions at the pilot.
120. (V2c-b2a -> V3) `SHORT_THUMB_WAIT_S` (the job waits up to 3 minutes for YouTube's processing, asking every 15 seconds) has never
   run: offline the stand-in is processed at once or not at all. If a 30-second Short usually needs longer, its thumbnail always
   arrives one tick (30 minutes) late: set the cell from what the pilot shows.
121. (V2c-b2a, the proof) NOT covered by the sweep: a platform that fails, drift, a refused thumbnail, a file that does not fit (unit
   tests and deliberate breaks only). Covered by the sweep on every id: a Short made while uploads are closed and sent later from its
   Drive copy, and a straight release; on about every second id the owner's Approve.
122. CLOSED / narrowed in V2c-b2a: issue 85 - closed for the standalone Short (Publishing's own run, read back), open for the
   cut-down and the special reels (118). Issue 100 - closed: a Short made while uploads are closed keeps its file and goes out when
   they open; one that is never approved leaves the ladder with the window. Issue 107 - closed: `made` is a field. Issue 109 -
   narrowed: the upload hold is in the sweep now; a crashing Short is not.

123. (V2c-b2b1 -> V3, TELL THE OWNER AT THE PILOT) How an upright clip of the real model looks through the opening's window is NOT KNOWN.
   Offline clips are wide (the offline clip maker ignores its start picture's shape), so every rehearsal and every sweep id met only
   the case "the frame filled, nothing enlarged"; the upright cases (a 4:3 window on a blurred copy, the filled frame, the whole
   clip) are proven on small test clips only. At the pilot: read the opening's log line of the first long video ("clips of W x H,
   window ..., enlarged ... times"), show the owner its first 20 seconds, and set `OPENING_FIT`, `OPENING_ENLARGE_MAX` and
   `OPENING_WINDOW_Y` from what he says and what the first retention curves show (redesign O14, H22, H23).
124. (V2c-b2b1 -> V2b / V1c) The long video's THUMBNAIL is not tied to the Short's first picture. The promise flag sits on the first
   footage shot, so `viewer_promise` / `promise_paid` say "the promise is on screen at 0.x s" because the Short's own promise picture
   opens the video - nobody compares it with the thumbnail's scene. One story across title, thumbnail and first seconds is V2b / V1c.
125. (V2c-b2b1 -> V3 / V2b) In the trial format (F2) the show's devices - the "REC" look with its vignette and grain, rain, the speaker
   chip - are drawn over the footage opening. Check `opening_shown` recognises the footage under them (0.80 and more), but whether
   the pictures viewers stayed for should be graded at all is a question for the owner's eye at the pilot.
126. (V2c-b2b1, money -> V2d) The estimate before a long video still counts four hero clips and the hook lab; a video on its Short's
   footage pays one clip, one start frame and two text calls fewer (about Rs 45-50). The estimate errs upward only. V2d's cost
   model should count a ladder video truthfully (with issues 72 and 83).
127. (V2c-b2b1 -> B7) A long video whose archive is missing or unreadable is held at the script gate with the owner's card. Its
   "Rewrite" button drops the episode and the next tick starts it again - with the same missing archive it is held again; only
   "Approve anyway" moves it (then it opens on its own pictures and is not asked again). B7's repair loop should own it: one
   automatic re-fetch, then a card that offers only what helps.
128. (V2c-b2b1) The opening ends with the last sentence that ENDS inside the footage, so the last seconds of the footage are usually not
   shown (17.2 s of footage gave 12.9 to 16.5 s of opening in the rehearsals). Carrying a sentence over the footage's end would need
   a rule about freezing or slowing: not built.
129. (V2c-b2b1 -> V3 / V2b) The Short's hook is INSERTED before the writer's own first line (as the lab's line always was). A real
   writer who knows the premise may open with nearly the same words; code skips the insert only when the two lines overlap 80% both
   ways. Read the first real scripts at the pilot; V2b (the inside of a format) may hand the hook to the writers instead.
130. (V2c-b2b1, FOUND, not this batch's -> V2d) With micro-cuts on, an animated scene of the video's OWN that is longer than 2.6 seconds
   inside the opening window (4 seconds elsewhere) is cut into pieces of which only the first plays the clip; the others show its
   start picture with a camera move. Part of a paid 5-second scene may so never be seen. (A footage clip is played whole since
   this batch.) V2d measures `moving_share` on the finished file: fix it there.
131. (V2c-b2b1, FOUND, not this batch's) Check `hook_lab` passes for a LAB line that is no longer the first spoken line:
   `hooks.verify_in_narration` sets the status to needs_human_choice and leaves `applied` true, and the check reads only `applied`.
   The Short's hook is judged strictly (the status must be "applied"); the lab's path was not changed here.
132. (V2c-b2b1, the proof) NOT covered by the sweep: upright clips (123), a missing archive, an override, a retry on another machine
   (whole-production tests and deliberate breaks only). Covered by the sweep on every long-video id: the footage fetched, laid,
   cut, rendered and found again on the finished film.
133. (V2c-b2b1 -> V2c-b2b2) The cut-down reels still exist and still go out the old way (issue 118); since this batch they never take a
   footage shot. V2c-b2b2 decides what stays of them.
134. CLOSED / narrowed in V2c-b2b1: issue 96 - closed as a design (the window is a setting and its limit a lever), open as a judgment
   on real clips (123). Issue 65 (the promise needs an animated scene to ride on) - closed for a video on its Short's footage,
   whose opening is always animated; open for a video under an override when the money trims every scene.

135. (V2c-b2b2 -> V3, THE OWNER'S HAND, BEFORE GO-LIVE) The pull from a Short to its long video is YouTube's related-video link
   and nothing else. No API sets it; it needs advanced feature access (phone verification - issue 112). No code opens the task
   yet: the one-minute release card (V3) must put it FIRST - at the long video's release, one message with the Studio link of
   the Short named on the video's ladder row (`d["ladder"]`), the long video's title, the three taps and a "Done" button; never
   called verified by the machine (the sheet's row `link` is `hand`). H24 measures it (Analytics traffic source SHORTS, which
   the learning job already reads).
136. (V2c-b2b2 -> the batch that prepares the pilot) FOUR OLDER DOORS ARE SHUT BY A SWITCH, NOT REBUILT (`truth.OLD_DOORS`):
   `specials._publish` (the special reels, the hand-started cast intro, and a standalone Short only when RELEASE_SHEET_ON is
   FALSE), `pilots.run`, `herostill.make_for_episode`, `insights.post_drop`. Each still carries its old words - the special
   reels' text says "New trials every Tuesday and Saturday ... Take your seat on the jury: subscribe", the pilot's end plate
   "Comment YES. Full trials Tue + Sat" - and reads nothing back. Switching one on by hand posts through that old upload.
   Decide per track: rebuild it on `release.py` (a kind of its own on tab `Release_Sheet`) or delete it; the cast intro and the
   channel trailer of redesign 4.10 belong to the pilot's sitting. The list may only shrink (a test).
137. (V2c-b2b2) `HERO_STILL_REELS_ON` is TRUE: every long video still makes a hero-still reel file and files it in Drive (free);
   nothing uploads it unless `HERO_STILL_SHORTS_ON`. A file nobody posts: decide with 136.
138. (V2c-b2b2 -> V4) Twelve short uploads a month is true by construction now, but no code COUNTS short uploads across kinds:
   `shortslab.allowed_today` (`SHORTS_WEEKLY_CAP` 10) still counts the old reel cells of tab `Episodes` and every row of tab
   `Specials`. If an older door is switched on, only that weekly ceiling bounds it. D1's weekly line "long-video views against
   the Shorts count" (redesign 11.4, O8, O15) is V4.
139. (V2c-b2b2 -> V3, TELL THE OWNER IN THE GO-LIVE GUIDE) A long video the OLD live code scheduled with four reels waiting:
   the new code posts none of them (the release is one step; a row at LIVE1 is closed by the tick). The week of the switch has
   no cut-downs; the one-time move also pauses the pilot Shorts and the special reels on the live Sheet (he can switch either
   back on - through the old upload, issue 136).
140. (V2c-b2b2 -> B8) History kept, read by nothing: the rows of the "reel" department on tab `Playbook` and of the dimension
   "reel" on tab `Strategies` of a live Sheet, lessons filed for "reels" (`growth.lessons_for("reel")` still maps them; no
   prompt asks for them). A video the old code made keeps its reel credit (`manage.strategy_credits`). The Librarian's batch
   may archive them.
141. (V2c-b2b2, money -> V2d) The estimate before a long video fell by two premium pictures (Rs 15.84 at the price cell). The
   planning call and the four voice jobs sat inside lump allowances (`LLM_EST_INR`, `TTS_EST_INR`) that were NOT lowered: the
   estimate errs upward by about Rs 10 a video. V2d's cost model (with 72, 83, 126).
142. (V2c-b2b2) The optional older writers' room (`ROOM_MODE` v1) has five roles now (the reel producer left): one memo and one
   objection fewer per video in that mode. Only the rehearsal's table-read scene runs it.
143. (V2c-b2b2, FOUND AND FIXED; the family may be wider) A job could hang for ever in the prompt-cache bookkeeping (a warning
   logged while a lock was held, when it was the 40th buffered log line - the record of this batch, "found while proving").
   Fixed in `models.CacheManager.blocks`. NOT checked beyond this module: other code that logs while it holds a lock which a
   log-flush hook also takes (`core.FLUSH_HOOKS` has one hook today: the cache manager's). A new flush hook must never take a
   lock its owner holds while logging. On the live channel (old code) the fault is still there until go-live: a production or
   learning job that sits idle for hours is this, not the platform.
144. (V2c-b2b2, NOT ADOPTED) YouTube's advice of a spoken pointer to the long video in a Short's last five seconds (its blog,
   14 Jul 2026): a Short is made one to two weeks before a long video about it exists and two in three never get one. If the
   hand-set link shows traffic (H24), V4 may test a winner's follow-up Short that points.
145. (V2c-b2b2, the proof) NOT covered by the sweep: the older doors (they are off), a video that stays private at its
   release, KILL, a row left at LIVE1 (unit tests and deliberate breaks only). Covered on every long-video id: no cut-down
   file, plan or upload; the release in one step; nothing short out but the standalone Shorts.
146. (V2c-b2b2, the tools) A rehearsal id from a PAST minute cannot be re-run to its end. On the fresh Sheet of the re-run the
   organisation is younger than the episode the id names, so `dept_contract`, `takeaways_written` and three more organisation
   checks say "not applicable: this episode was started before the organisation was installed", and the rehearsal's own
   assertion (they must PASS) stops the run. Everything before that line is reproduced - it was enough here (the hold at the
   script gate; after the fix 36 of 36 and 18 of 18). To carry a red rehearsal of GitHub past that line, `tools/rehearsal.run`
   with a fixed id should date the organisation's install before the id's minute. Not built. The fixed ids of the sweep lie in
   the future and never meet it.
147. CLOSED / narrowed in V2c-b2b2: issue 118 - closed for the cut-down reels (gone), open for the special reels as 136. Issue
   133 - closed. Issue 76 - closed for the cut-downs. Issue 84's last line (`JOKE_EVERY_SEC_SHORT` "only by the cut-down
   reels") was not exact: `enforce.py` reads the cell for any text judged as a Short; nothing of this batch touched it. Issue
   13 - narrowed: the long video's release step (`manage.release`) is still not a department run of Publishing.
148. (the owner, 13 Nov 2026 -> V3, BEFORE GO-LIVE; item 22 of `02_OWNER_VERBATIM.md`) THE LIVE CHANNEL IS PAUSED BY THE OWNER'S OWN
   HAND: he set the Settings cell PAUSED to TRUE. What the live code (`origin/main`) does while it is TRUE, read from the code,
   NOT from the live Sheet (the build session cannot see it): `manage.tick` runs `kill_check`, then `hold_scheduled("paused")` -
   a video already on YouTube's schedule with its slot still ahead is set to private and its row to HELD - and returns: nothing
   is produced, no release step runs; the jobs `preprod`, `pilot` and `special --if-due` stop at the gate of `cli.py`. Hand-started
   jobs still run, and so does whatever only reads (the learning job was not read line by line). The rejected video stays public.
   WHAT V3 MUST DO: (1) the new code reads the same cell (`manage.paused`, `shorts2.py`): NOTHING is made until HE sets it back
   to FALSE - an explicit step of the pilot guide, after his secrets and the first pre-flight, never set by the machine;
   (2) the first tick after that runs `resume_held`: EVERY row at HELD with a `yt_id` goes back on the schedule - a video the OLD
   code made would be published by the new channel, unasked. Before the cell turns, the pilot guide must list the HELD rows and
   take his word on each (keep private, or delete); no code does that today; (3) his decision of 11 Nov ("not paused", item 19)
   is replaced for the pause only - never ask him about it, never touch the cell; (4) while it is paused the old code spends
   nothing on new videos and the hang of open issue 143 cannot bite. Until go-live the channel posts nothing.
149. (found 13 Nov 2026 while answering item 22 -> V3; CORRECTS redesign 11.7 and the wording of issues 112 and 135) "ADVANCED
   FEATURES" IS NOT PHONE VERIFICATION. YouTube Help 9890437, read 13 Nov 2026: the phone gives the INTERMEDIATE features
   (videos over 15 minutes, custom thumbnails, live streaming); the ADVANCED ones need enough channel history, or identity
   verification by video, or by a valid ID (the page: either unlocks them "immediately"; its details page was not read - how
   long a review takes is not known). On the advanced list: related video on Shorts, pin comments, add chapters, A/B testing,
   clickable links in a long video's description, apply for monetization, multi-language features. So on the release sheet:
   the thumbnail needs the phone (issue 112 stands); the Short-to-video link (135), the pinned comment, the thumbnail A/B test
   and the translated titles need ADVANCED access - and so may the chapters code writes into every description (whether
   YouTube shows them without it was not found). Where he sees it: YouTube Studio > Settings > Channel > Feature eligibility
   ("Enabled" next to what the channel has). He was told on 13 Nov 2026 to look NOW, so that the pilot does not wait for a
   verification. V3: the pilot guide's first step is that page, not only the phone; a row of the release sheet whose feature
   the channel does not have yet must say so (`hand` / not available), never fail as if the upload were wrong. The dated row
   for `docs/CURRENT/PLATFORM_FACTS.md` goes in with the batch that touches `release.py` (no code and no current doc changed
   on 13 Nov).

## HOW TO RUN ON THIS LAPTOP (the Bash tool = Git Bash works; from `reality-engine/`)
- Env: `export PYTHONUTF8=1 WI_FAKE=1 PY=../.venv/Scripts/python.exe`
- Suite: `bash ../shim/runall.sh . <outdir outside repo>` (~35 min; run it in the background). Some files: `bash ../shim/runseq.sh . <outdir> test_a test_b`.
- Rehearsal: `WI_SMALL=1 WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.cli rehearsal > <log outside repo>` (~3 min); delete the work dir after.
- Plan Guard: `../.venv/Scripts/python.exe tools/plan_guard.py`. Truth only: `../.venv/Scripts/python.exe -m whatifs.truth`.
- Organisation only (registry honesty + data, prints GREEN / RED): `WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.org.runner`.
- After adding or moving a runner call site: update `whatifs/org/registry.py` ENTRY / PENDING, then `tools/gen_docs.py`.
- The end-to-end test in `tests/test_v12_org.py` runs two fake episodes (about 2 minutes); the file needs `tools/rehearsal.py` importable (it is).
- Palace only (seeds a local store, prints GREEN / RED + every problem): `WI_WORK=<dir outside repo> ../.venv/Scripts/python.exe -m whatifs.org.palace`.
- After ANY change to a seed file in `whatifs/org/seed/`: run that Palace command, then `tools/gen_docs.py` (SYSTEM.md prints the seed counts).
- Stopping a background suite run: stopping the task does NOT stop the runner loop on Windows. Also stop the `bash.exe` processes whose command line
  contains `runall.sh` / `runseq.sh` and the `python.exe` running `minitest.py`, or tests keep starting.
- After ANY change to settings, checks, tabs, workflows or a module docstring: `../.venv/Scripts/python.exe tools/gen_docs.py` and commit SYSTEM.md.
- Plan Guard flags one specific word in every text file and several words in file names (see `tools/plan_guard.py` BANNED_NAME_WORDS) - keep
  BUILD_STATE and seed files clear of them.
- Sweep (standing rule 2; about 2 minutes an id alone, 4-5 with 3 jobs; ALWAYS on a frozen copy so that edits do not change the code under test):
  `git worktree add --detach <scratch>/wt <commit>`, then from that folder `<venv python> tools/sweep.py --n 40 --jobs 3 --work <dir outside any repo> --out <file>`;
  `--org off` = the old path; `--mode rehearsal --ids <id,...>` = the full rehearsal with a forced id; `--one <id> --work <dir>` = one id, folder kept.
  Read only the `TOTAL` and `SUMMARY` lines; per-id logs are in `<work>/_logs/`. Afterwards `git worktree remove --force <scratch>/wt` and, if git then
  complains about `.git/worktrees/<name>`, delete that folder by hand (OneDrive can hold it for a minute).
- Real pytest for single files (same runner as GitHub): `PYTHONPATH= ../.venv/Scripts/python.exe -m pytest tests/<file>.py -q -p no:cacheprovider`;
  add `WI_NO_SKIPS=1` to run strict like GitHub's Checks.
- Truth registry by hand: `../.venv/Scripts/python.exe -m whatifs.truth` (retired concepts, unread cells, unused tabs, uncalled functions).
- The engine by hand in a test or a scratch store: write a ticket with `memos.write`, call `execute.engine_tick(now=...)`, read tab `Tickets` (state, proof,
  note) and tab `Lever_Changes` (the events). Every engine function takes `now`, so a verification window can be walked through without waiting.
- After adding a founding item addressed to a department: run the Palace command and read its `note:` line - an item for a crowded department (D1, D4,
  D12, C) can push a low-priority limit out of that playbook. Narrow the audience instead.
- NEVER run the full suite and the sweep at the same time: the suite runner stops a test file after 15 minutes, and under the sweep's load
  `test_v91_flaky_root` (999 s that day) and `test_v82` (764 s) run into it. Suite first (about 40 minutes with the engine's tests), then the sweep.
- NEVER paste code with backslashes through a shell here-document on this laptop: the shell halves them (it broke a file twice in B0b). Write the
  file with the file tools, then run it.
- TOOLS INSTALLED ON 12 NOV 2026 (the owner's standing permission, item 21 of `02_OWNER_VERBATIM.md`: a tool is allowed where it helps
  the tests or saves tokens, from an official source, and NEVER at the price of quality - what a batch is judged by stays "in the
  same manner"). (1) **Node.js LTS** v26.13.1 (winget package `OpenJS.NodeJS.LTS`, in `C:\Program Files\nodejs`; a shell that does
  not find it: `export PATH="/c/Program Files/nodejs:$PATH"`). The dashboard test of `tests/test_v94b.py` no longer skips: THE LAPTOP
  NOW RUNS EVERY TEST GITHUB RUNS (14 passed in that file with `WI_NO_SKIPS=1`). (2) **pytest-xdist** 3.8.0 (with execnet 2.1.2) in
  the venv: the whole suite with real pytest, in parallel and strict like GitHub -
  `PYTHONPATH= WI_NO_SKIPS=1 ../.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider -n 6 > <log outside the repo> 2>&1`.
  PROVEN ONCE on 3e4636f (the accepted code of V2c-b2a): **1392 passed in 30:25, exit 0** - GitHub's own total for run 117 - against
  about 50 minutes for the serial runner. USE IT AS THE PRE-CHECK before a batch's final code commit: one run shows every test the
  batch changed by design (the three red runs of V2c-a and V2c-b1 were exactly such tests). THE ACCEPTANCE RUN IS UNCHANGED: the
  serial suite on a frozen copy (`bash ../shim/runall.sh`), then the sweep, then GitHub's Checks. Its output to a file is buffered:
  wait for the process to end and read the last line; a red run: `grep -a "^FAILED" <log>`. Never run it beside the serial suite or
  the sweep. Nothing that `requirements.txt` pins was touched (`pip check`: no broken requirements); never upgrade a pinned package
  (standing rule 4). With node present the serial suite should report 0 skipped from now on - not seen yet; the next acceptance run
  will show it. If a parallel total ever differs from the serial one, trust the serial one, trace the difference and write it here.
- A BACKGROUND COMMAND CAN BE ENDED BY THE TOOL after about ten minutes (12 Nov 2026, batch V2c-b2b1: a run of deliberate breaks was cut
  off in the middle of a break and left one broken line in a code file - a kill does not run a script's "put it back"). Start anything
  longer DETACHED - `( <command> > <log outside the repo> 2>&1 & )` in a short foreground call - and wait with a small Python loop on
  the log's last line (at most about 9 minutes a call). A break script keeps a copy of every file before its first break, restores
  from the copy at every start, and runs in parts of a few minutes. After ANY break run: `git status` before the next step.
- A RUN THAT STOPS WITH EVERY WORKER IDLE IS A FINDING, NOT A FLAKE (12 Nov 2026, batch V2c-b2b2: two of three parallel runs
  stopped at 93-96% for half an hour - a real deadlock in the prompt-cache bookkeeping, open issue 143). How it was found, in
  ten minutes: run with `-v` so every finished test is logged by name; the worker whose count stands still names the test (the
  next one in its file); then dump that worker's stack while it is stuck: `../.venv/Scripts/py-spy.exe dump --pid <pid>`.
  TOOL INSTALLED ON 12 NOV 2026 under the owner's standing permission (item 21 of `02`): **py-spy** 0.4.3 from PyPI, in the
  venv only (it reads the stack of a running Python process; it changes nothing that `requirements.txt` pins and no test
  depends on it). Stop ONLY your own run: find the pytest process by its command line and `taskkill //F //PID <pid> //T`
  (a blanket kill of every python.exe is refused by the app, rightly).
- The offline clip maker ignores the shape of its start picture: every offline clip is WIDE (the size of a long video's still), also a
  Short's. A rule about UPRIGHT clips (the opening's window) needs test clips made upright by ffmpeg (`tests/test_v12_opening.py`).
- git: `core.autocrlf=false` (keep LF); write files with LF. Commit identity Rahul4869 (noreply address); push with
  `GIT_TERMINAL_PROMPT=1 GCM_INTERACTIVE=always git push` (credentials are saved).

## BATCH LOG
| Batch | Status | Suite | Rehearsal | Notes |
|---|---|---|---|---|
| B0 | done 10 Nov 2026 | 912 / 0 / 6 skipped | GREEN (19 + 18) | 2 small fixes (Windows ffmpeg path; particle seed determinism). GitHub run 28: GREEN |
| B1 | done 10 Nov 2026 | 940 / 0 / 6 skipped | GREEN (20 + 18) | Truth Registry; docs/CURRENT + ARCHIVE; generated SYSTEM.md; check `docs_current` (38 hard checks now). GitHub run 31: GREEN |
| B1b | done 10 Nov 2026 | 949 / 0 / 6 skipped | GREEN (20 + 18) | Owner decision "4 a month" executed: cap 4, weekly Saturday, one-time Sheet move, truthful viewer lines, retired rule. GitHub run 33: GREEN |
| B2 | done 10 Nov 2026 | 988 / 0 / 6 skipped | GREEN (21 + 18) | Knowledge Palace core: 92 founding items, write gate, life cycle with authority, guarded playbooks, check `palace_health` (39 hard checks now). GitHub run 38: RED at the rehearsal (the stale promise flag, reproduced in B0b; fixed in B3) |
| B3 | done 10 Nov 2026 | 1088 / 0 / 6 skipped | GREEN (22 + 19) | Memos + department contract: 4 org modules + wrappers, 7 departments wired, SLA watchdog, checks `dept_contract` + `takeaways_written` (41 hard checks now); promise-flag fix. GitHub run 42: GREEN |
| B0b | done 10 Nov 2026 | 1113 / 0 / 1 skipped | GREEN (22 + 19) | Baseline re-check: sweep 58 of 58 fixed ids green; reference frames always compared; no-skip rule; Checks pinned to production's library versions (they ran OpenCV 5.0.0); red runs name their cause in public; 8 cells / 2 tabs / 10 functions that were never wired are listed and may only shrink; owner: build the room value test in B8. GitHub run 52: GREEN (1114 passed, 0 skipped); runs 46-48 RED = OpenCV 5.0.0 before the pin |
| B4 | done 10 Nov 2026 | 1201 / 0 / 1 skipped | GREEN (24 + 19) | Execution Engine: lever table (39 levers), 5 lever classes from ticket to ledger proof or rollback, owner approval by direction, between-videos rule, D12 wired, checks `decisions_executed` + `lever_verified` (43 hard checks now), build workflow hardened. GitHub run 59: GREEN (1202 passed, 0 skipped); run 57 RED = one test, a one-second ordering rule of the verifier, traced and fixed (runs 54-56 and 58 GREEN) |
| B5 | done 11 Nov 2026 | 1232 / 0 / 1 skipped | GREEN (25 + 19) | R&D + Review Board: gap-driven research agenda (8 gap sources), sources verified by code (phantom / dead / undated dropped, evidence ceiling), blind two-family Board with yes/no checklist, verdict by code, family veto, planted canary per session; check `research_cadence` (44 hard checks), D2 + D3 wired, 41 levers. Sweep 58 of 58. GitHub run 67: GREEN (1233 passed, 0 skipped); #63 RED = 6 by-design tests, #64/#65 RED = rehearsal money formula, traced and fixed |
| B6a | done 11 Nov 2026 | 1260 / 0 / 1 skipped | GREEN (28 + 19) | Creative departments: the Palace playbook inside the writer / packager / director prompts (end of the system prompt, cached layers untouched), citations verified by quote, canon written by code and accepted on air, continuity debt paid in the script, distinct creative memos to the Council, drafts adopted only with proof; checks `palace_injected`, `palace_cited`, `canon_in_brief` (47 hard checks); the writers' playbook holds the owner's limits again (cap 2,400); open issue 47 fixed. Sweep 40 of 40. GitHub run 75: GREEN (1261 passed, 0 skipped); #71 RED = 54 by-design tests, #72 RED = 3 pinned tests, traced and fixed |
| B5 recheck | done 11 Nov 2026 | 1272 / 0 / 1 skipped | GREEN (28 + 19) | Owner asked for a recheck of B5 and its consequences: 16 corrections (a syntax repair hid who answered; a cheap Gemini model could sit on the Board; the void-session memo never closed; a video could be held for research a job can run; the organisation's plumbing became paid web questions; barren research was invisible; a crash after a paid call; the learning job's 30-minute limit; 8 small ones), 12 new tests. GitHub run 78 (101cf96, the final code commit): **GREEN - 1273 passed, 0 skipped, rehearsal GREEN (episode id EP202611110421, script 28 / 28, final 19 / 19)** |
| REDESIGN | done 11 Nov 2026 | - | - | The owner rejected the first live video (made by the old code) and gave a free hand: research (14 dated sources), 4 designs, the decisions and the new batch plan in `handoff_v12/BREAKOUT_REDESIGN.md`. No code changed |
| V1a | done 11 Nov 2026 | GitHub 1284 passed (run 85); laptop 312 / 0 on the 9 touched files | GREEN (50 checks: 45 pass, 5 not applicable) | The viewer's seat, measured: department D13 Audience; before any picture is paid the first shot is a picture carrying the animated promise (5 s), the voice gets a pause every 30 s, numbers heard and number graphics have a budget; 3 script-gate checks (50 hard checks), 4 levers (45), long videos 9:00 at most. GitHub run 85 GREEN on f96b87a; sweep 28 of 28. |
| V1b | done 11 Nov 2026 | 1292 / 0 / 1 (laptop); GitHub 1293 passed (run 89) | GREEN (52 checks: 47 pass, 5 not applicable) | The layman test: expert words a layman would not know counted by code (a budget per minute, in the first 30 s, in one sentence; the writers' one fix carries it) and the promise line-up (two cheap readers of two model families pick the video's title from the first 30 s; a planted opening must get none; verdict by code); 2 script-gate checks (52 hard checks), 3 levers (48), D13's second run. GitHub run 89 GREEN on 4c0e607; sweep 28 of 28 (the first sweep held 1 of 20 for ordinary words - fixed at the cause). |
| V2a | done 11 Nov 2026 | 1302 / 0 / 1 (laptop); GitHub 1303 passed (run 91) | GREEN in F1 and in F2 (53 checks) | Formats as data and the three-tier contract: every episode has a format (F1 "The day it changed" 70, F2 "The trial" 30; shares are levers of D1), the trial layer, the briefs, the juries and the production follow it; a format can make a show device optional or leave it out and nothing else; new check format_kept (53 hard checks), 3 levers (51). GitHub run 91 GREEN on 75c55ea; sweep 28 of 28 (15 episodes in F1, 9 in F2, 4 rehearsals). |
| V2c-a | done 11 Nov 2026 | 1323 / 1 / 1 on 486eb41, the 1 corrected (laptop); GitHub 1325 passed (run 99) | GREEN in F1 / F2 with a Short in S1 / S2 / S3 (53 + 5 checks) | The Short as a product: department D14 Shorts Studio; Short formats as data (S1, S2, S3); `shorts2.py` rebuilt - one guide voice, every second a clip planned by code, the loop closed by code, no plate; the viewer's seat for a Short (`shortseat.py`) and 5 checks at a new stage "short" (58 hard checks), 12 levers (63); a held Short is not made. V2c was split at its start. GitHub run 99 GREEN on 3b34cc3; sweep 58 of 58 ids. |
| V2c-b1 | done 12 Nov 2026 | 1358 / 0 / 1 on 3ab0e16 (laptop); GitHub 1359 passed (run 110) | GREEN in F1 / F2 with Shorts in S1 / S2 / S3 (54 + 5 checks) | The ladder: every topic starts as a Short (3 a week, 12 a month, 48 hours apart); YouTube's true numbers are read by processed day (they are 48 to 72 hours late) and public views at the 24-hour and 48-hour mark; D10's promote rule (code, never a model) picks the long video's topic and a long video without a promoted Short or an owner override is refused before any money (new tab `Ladder`, check `topic_ladder`: 59 hard checks); a winner gets ONE follow-up ordered by code with a 48-hour clock, overdue = a memo; 6 levers in, 1 out (68). V2c-b was split at its start. The sweep found what a green suite and four green rehearsals had hidden: on a new Sheet no video could ever have been made - and three faults in what counts as a made Short; all fixed at the cause, 42 deliberate breaks. GitHub run 110 GREEN on 3ab0e16; sweep 58 of 58 ids. Runs 104-106 RED = three tests that pinned what the batch changed by design, corrected. |
| V2c-b2a | done 12 Nov 2026 | 1391 / 0 / 1 on 3619c81 (laptop); GitHub 1392 passed (run 117) | GREEN in F1 / F2 with Shorts in S1 / S2 / S3 (54 + 5 + 1 checks) | The platforms: a finished Short goes out as three native uploads of ONE master file under Publishing's own run (new `whatifs/release.py`, D9 `short_publish`) - YouTube Shorts (its own thumbnail, set only after YouTube has processed the video; the playlist of its format), Instagram Reels (a Trial Reel, its cover, the audio named after the series, the AI label), Facebook Reels (90 seconds at most); each under its own words, none with an ask. The release sheet is data (who sets each row, how it is proven), every request body a pure function, every platform read back and every row given a receipt on new tab `Release_Sheet` (kept, fixed, drift, sent only, waiting, refused, skipped, off); a pass on every tick finishes what waits; a release gate after the uploads (D8 `release_gate`, new check `release_sheet` at new stage "release": 60 hard checks); `made` is a field of the Short's record (the status-text match is gone); 2 levers (70). V2c-b2 was split at its start. Found and fixed: an approved Short would have gone out under the special reels' text; a Short made while uploads were closed lost its file; a check that could pass a Short which never reached YouTube; a second upload after a cut-off; the sweep had never published a Short. 63 deliberate breaks, each failed a test. No paid call added. GitHub run 117 GREEN on 3619c81 (no run of the batch was red); sweep 58 of 58 ids. |
| V2c-b2b1 | done 12 Nov 2026 | 1416 / 0 / 0 on 22103cb (laptop); GitHub 1416 passed (run 126) | GREEN in F1 / F2 with Shorts in S1 / S2 / S3 (56 + 5 + 1 checks) | The opening: a long video about a promoted Short opens on that Short's kept footage (new `whatifs/opening.py`, D6) - the archive of its ladder row fetched and measured, the Short's picture track laid by code under the first sentences, one clip a shot cut through ONE window whose width follows the clip's real sharpness (a setting and a lever; a blurred copy of the picture as ground), the first spoken line the Short's own hook (no hook lab), three paid scenes instead of four; a video under an override opens on its own promise scene; checks `opening_footage` (before picture money) and `opening_shown` (frames of the finished film against the footage): 62 hard checks; 2 levers (72). V2c-b2b was split at its start. Found and fixed: a hash of a tiny copy could not recognise its own footage under a grade; the cut-downs lost every shot; a still after the opening re-used a frame of the footage; a reaction effect drawn over the footage; and - by the SWEEP, twice, after a green suite, green rehearsals and a green GitHub run - a false hold by the new check on 1 long video in 20 (it compared a frame where two clips meet; first misread, then reproduced and fixed). 83 deliberate breaks, each failed a test. No paid call added, four removed (about Rs 45-50 a long video). GitHub run 126 GREEN on 22103cb (124 and 125 GREEN on the two commits before the sweep's fixes; 121-123 RED = tests that pinned counts changed by design); sweep 58 of 58 ids on the third pass (57 of 58 on the first two). |
| V2c-b2b2 | done 13 Nov 2026 | 1457 / 0 / 0 on 1d3a77a (laptop); GitHub 1457 passed (run 131) | GREEN in F1 / F2 with Shorts in S1 / S2 / S3 (54 + 5 + 1 checks) | The cut-downs: a long video makes NO cut-down reels any more - the paid planning call, two paid covers, four re-voiced reels, the old upload, releases 2 to 4 and the checks `shorts` and `short_covers` are gone (60 hard checks; 71 levers); its topic already has the Short real viewers chose and the pull from that Short is YouTube's related-video link, a hand step (V3's release card); the long video's release is one step. Counted from the code, the defaults would have posted about 38 short videos a month through four uploads (12 Shorts, 16 cut-downs, 8-9 pilot Shorts, 2 special reels): now 12 - ONE door for every upright video (`release.py`; `truth.OLD_DOORS`: four older doors, off by default, may only shrink; a new door fails Plan Guard, the tests and check `docs_current`), the pilot Shorts and the special reels paused by default and moved once on a live Sheet. Found while proving and fixed at the cause, both older than this batch: a job could hang for ever in the prompt-cache bookkeeping (a warning logged inside a lock; found with a stack dump of a stuck test worker), and a long video was held for its Short's own hook 'Today you ...' (reproduced with the id on the accepted code first). 63 deliberate breaks, each failed a test. No paid call added, seven removed a long video (about Rs 27; the counter agrees). GitHub run 131 GREEN on 1d3a77a (130 GREEN; 129 RED = three test files importing the deleted module at the first build checkpoint); sweep 58 of 58 ids on the first pass. |
| V2d | next | | | The motion ladder and the money: the hero model by value, the living tier, a character drawn or absent, stock rules (NASA / Pexels), the cost model |
| V3 | after V2d | | | Pilot on real services (3 Shorts + 1 long video), the human kit, the release sheet's one-time switches, then GO LIVE with the new code |
| V2b | after V3 | | | Inside the format: first person and camera continuity as measured rules, F1's own ending, F3 "The walk" |
| V1c | after V2b | | | The judged floor with the canary (the owner's rejected video must lose), his verdict tab, the maker's line |
| V4 | after V1c | | | The CEO and the ladder: D1 Strategy wired, the portfolio, decide-inform-implement; the owner's input tab and the scoreboard |
| V5 | after V4 | | | The Breakout Observatory (hits against siblings, three rings, patterns counted by code, one trial each) and the aspect map (item 19) |
| B6b | after V5 | | | The Council |
