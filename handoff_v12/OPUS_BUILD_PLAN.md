# OPUS BUILD PLAN - how the rest of Reality Engine v12 is built, proven and repaired without leaving anything to the builder's opinion
Written on 13 Nov 2026 by the Fable session that proved batch V2d-b, at the owner's order (item 33 of `02_OWNER_VERBATIM.md`):
"make a solid detailed level end to end plan with everything ... so that i can use opus 5.5 and get the fable 5.2 extra high level results and
continuous debugging and automatic self correction repair loop ... i dont want to leave anything to chance to opus".
AUTHORITY: the owner's words (`02`) override this plan; this plan overrides, for every session of whatever model, the paragraphs of
`BUILD_STATE.md` under NEXT that say who builds and who proves ("A BATCH IS TWO FABLE SESSIONS", "WHAT A SESSION ON ANOTHER MODEL MAY DO") and
the model lines of `06`. Everything else in the handoff stands: the product, the order of the batches, the mandatory loop, the standing rules,
the proving, nothing real before V3, PAUSED as he set it.
FIRST ACT OF EVERY SESSION, before any reading: from the handoff folder run `.venv/Scripts/python.exe proving/next.py` (written below as
`python proving/next.py`). It checks the checkout and prints YOUR ROLE CARD. Then read this plan whole. Then the reading order of your role
(chapter 4). The plan is long because it replaces judgement with procedure: do not skim it, and do not improve on it mid-batch - a plan that
proves wrong is corrected in the record (chapter 15), never worked around.

## AMENDMENTS 1 AND 2 (14 Nov 2026, the owner's items 35 and 36) - READ BEFORE CHAPTER 3; WHERE A CHAPTER BELOW DISAGREES, THESE LINES WIN
Item 35: "fable does the quality work and quality control while opus build". Item 36 (he moved to the Ultra plan): "fable should also instantly
audit and correct and improve the file of the batches made by opus after a batch ends ... all the best work is done by fable high now and only
the insignificant work is done by opus". Written by the Fable session he set to Fable 5.2 himself (chapter 15: his words change the plan at any
time). They change WHO does each phase and WHO starts whom. The laws, the machinery, the proving and the order of the batches do not move.
THE CHAIN OF ONE BATCH (F = Fable 5.2 at Effort High, O = Opus 5.5; every session runs `next.py` first and reads this plan):
| # | Session | Phase | Does | Ends by |
|---|---|---|---|---|
| 1 | F DESIGNER (fresh; started by the finisher of the batch before) | DESIGN | detaches itself; the whole reading; THE AUDIT of every batch in the audit queue (chapter 14, A7); steps 1 to 3 | `--to DESIGN_REVIEW`; starts 2 (fresh, wake on) |
| 2 | F REVIEWER (fresh; did not write the memo) | DESIGN_REVIEW | 5.4 | CHANGES REQUIRED: `--to DESIGN`, ends its turn (1 is woken, changes the memo, moves the state back and messages 2). APPROVED: `--to BUILD`, DETACHES ITSELF, starts 3 (wake on), ends its turn |
| 3 | O BUILDER (fresh; the builder's whole reading) | BUILD | types the approved memo: steps 4, 5, 6a, the break list, the breaks all caught, the builder's block once; `proving/notes/<batch>_OPUS_DONE.md` | "BUILT BY OPUS - waits for the Fable finisher"; it does NOT run `built_gate.py` or `--to BUILT` |
| 4 | F FINISHER (= session 2, continued by the app when 3 ends; a fresh Fable session with the memo and the diff when 2 is over 60% of its context) | BUILD | THE FINISHING PASS (A5); then the builder's last acts 5.9 from act 1 on ITS final code commit | `--to BUILT --commit`; starts 5 (wake on) |
| 5 | O PROVER (fresh) | BUILT, PROVING | chapter 6 and 7 to the letter (or 8.1 to 8.4) | ACCEPTED or RED; it starts NOTHING; its report continues 4 |
| 6 | F FINISHER again | ACCEPTED / RED | GREEN: checks the acceptance on the record (the commit, the head line, GitHub's run, a clean tree), starts the next batch's DESIGNER. RED: it is the REPAIRER (8.7) and starts a FRESH O prover | - |
HOW A FABLE SESSION STARTS ANOTHER (chapter 9's call with these changes): a Fable session - `model` and `effort` omitted; an Opus session -
`model` "claude-opus-5-5", `effort` omitted (it gets the starter's, High), then ONCE `set_session_effort` to xhigh for it (the app may ask the
owner; refused or unanswered = it runs at High, said in the record). `wake_when_done` true. An Opus session can start no Fable session: it
never needs to - its ending continues the Fable session that started it. If the app refuses a start: the card and the one line of chapter 9.
AN OPUS SESSION HANDED A CARD THAT IS FABLE'S (phase DESIGN, DESIGN_REVIEW, RED / REPAIR; phase BUILD when `<batch>_OPUS_DONE.md` exists)
does nothing and tells the owner in one line: "<batch> waits for a Fable session: open one here (Fable 5.2, Effort High) and type: continue".
A FABLE SESSION HANDED A CARD BY THE OWNER'S "continue" is whatever the state and this table say is next (phase BUILD without the note
`<batch>_OPUS_DONE.md` and without an Opus builder at work: it starts the Opus builder and becomes the finisher).
- A1. PHASE DESIGN (loop steps 1 to 3: the whole reading, the research, the designs, the memo) IS A FABLE SESSION'S, at Effort High. It writes
  no code and stops at `next.py --to DESIGN_REVIEW`. The card of `next.py` still says "BUILDER - phase DESIGN": read it as THE DESIGNER.
  An Opus session that is handed that card does nothing and tells the owner in one line: "The design of <batch> is Fable's work: open a new
  session here with Fable 5.2 (Effort High) and type: continue".
- A2. THE DESIGN REVIEW ("gate on", items 34 and 35: no design is built before ANOTHER Fable session approved it) is started BY THE DESIGNER
  (item 36 (d): the chain no longer waits for the owner's click; his words "I open the reviews" put the click back). The flag
  `fable_design_gate` stays on: `next.py` stops every session that is not Fable at DESIGN_REVIEW.
- A3. THE FIRST BUILD IS AN OPUS SESSION'S: a FRESH session that does the builder's WHOLE reading (chapter 4) and then TYPES THE APPROVED MEMO -
  steps 4, 5 and 6a, a checkpoint commit after each, the break list written before the last test run, `breaks.py` until 0 missed and 0 void,
  Plan Guard, Truth, the Palace, the Organisation and the docs GREEN, the builder's block ONCE on its last commit (a red there is its own to
  repair at the cause: three attempts, then written down). It decides nothing the memo did not decide (A4). It ends with
  `proving/notes/<batch>_OPUS_DONE.md` - its last commit; per part of the memo: built as written / built otherwise and why / not built
  and why; every `DESIGN QUESTION`; every test changed by design; what it is unsure of - pushes, and stops.
- A4. THE MEMO LEAVES NO TASTE TO THE BUILDER. Every part of Step 3 names the module and the function, the measure with its exact
  arithmetic, the starting value of every number and where it comes from, the check, the test that fails, the deliberate break, the
  writers' fix sentence where a writer is told something, and the order of the build. A builder that meets a choice the memo did not make
  writes it into the record as `DESIGN QUESTION <n>` and takes the reading that changes LESS of what a viewer sees; a question a viewer
  or the money depends on stops the build for a Fable session (one line to the owner). It is never settled silently in code.
- A5. THE FINISHING PASS (Fable; the owner's "instantly audit and correct and improve"; in phase BUILD, BEFORE the batch is proven, so that
  every change of Fable's is inside the commit the block proves). In this order: (1) read `<batch>_OPUS_DONE.md` and the WHOLE diff from the
  base commit - code, tests, breaks, docs, the record - beside the approved memo; (2) AUDIT, part by part of the memo: does the code do
  exactly that (the function, the arithmetic, the numbers), does each test fail for the reason it names, does each break change one place
  that a test of its own catches, is any judge weakened (L7), is any sentence of the record untrue of the code; (3) write every finding
  into the record under `FINISHED BY FABLE`, numbered, BEFORE its edit; (4) CORRECT what is wrong and IMPROVE what is weak in the code and
  the tests themselves - an improvement stays INSIDE the approved memo (a truer execution of a part, a missing test, a sharper message,
  a fault of the same family found elsewhere); a new rule or a changed design is never added at the finish: it is an open issue for a
  later design; (5) close every OPEN finding of an audit (chapter 14); (6) the builder's last acts 5.9 from act 1 on the new final code
  commit - all breaks again, the builder's block again, `built_gate.py` GREEN, the record, `<batch>_BUILT.md`, `--to BUILT --commit`.
  The finisher never runs the serial suite or the sweep and never writes the word of acceptance: the Opus prover runs the scripts.
- A6. REPAIR IS FABLE'S (the finisher's session, which knows the code; chapter 8.7 unchanged otherwise). PROVING stays an Opus session's:
  it starts the block, waits, runs `verdict.py` and `judge_guard.py` and writes what they printed (chapters 6 to 8.4) - it decides nothing.
- A7. THE AUDIT AFTER ACCEPTANCE (chapter 14) no longer waits for the owner's word: the NEXT batch's Fable designer does it as its first
  act after `next.py` (it wrote none of that batch). A finding is closed in the next BUILD phase, typed by Opus from the audit's exact
  words and checked by the finisher (code is committed only in BUILD and REPAIR).
- A8. THE ALLOWANCE: every session reads `get_usage` at its start and end and writes the figures into the record; from 88% of a weekly
  line a Fable session writes "WHERE THE SESSION STANDS" and stops clean (chapter 10). Nothing is shortened to fit: it waits.

## AMENDMENT 3 (14 Nov 2026, the owner's item 38: "start all the department process so that we can finish the project now within this week ... without compromising any single bit of quality") - TWO LANES; WHERE A CHAPTER BELOW OR AMENDMENTS 1 AND 2 DISAGREE, THESE LINES WIN
Written by the Fable session that reviewed V2b's design and that he gave these words to (chapter 15). It moves WHEN the thinking of a batch is
done, never what a batch is built from or judged by. An Opus builder or prover at work when this was written changes nothing in what it does.
- LANE A, THE MACHINE (unchanged; serial; one laptop - L9): build -> finish -> prove, one batch after another in the owner's order. Nothing of it
  ever runs beside anything else.
- LANE B, THE THINKING (Fable only; AHEAD of the machine): the design of the next batches (loop steps 1 to 3) and its review are done while Lane A
  builds and proves an earlier batch, so that no batch waits for its design.
  B1. A PRE-DESIGNER is a fresh Fable session with the batch's brief (chapter 12). It does the builder's whole reading (chapter 4). It reads the
      handoff and the record from this folder and THE CODE from a plain export of the last accepted final code commit in its own scratchpad
      (`git -C reality-engine archive <sha> | tar -x -C <scratchpad>/code` - NEVER `git worktree add`: a registered copy stops a prover's
      pre-flight), and it reads the memo of every batch being built on top of that commit. It RUNS NOTHING of the pipeline - no test, rehearsal,
      sweep or break, and no python process but `next.py` once at its start (a prover's block looks for running processes). It never moves the
      state, never commits, never edits a file of the repo. It writes `PREDESIGN_<batch>.md` in the shared notes folder: steps 1 to 3 under the
      record's headings, to the standard of amendment A4 and of `reviews/V2b_design.md` (all three rounds: what a memo is attacked for), and a
      last part "TO VERIFY WHEN THE BATCH'S TURN COMES" - every sentence about code that a batch in between may change, and the experiment of
      5.1 with its exact commands (it is RUN then, not now).
  B2. A PRE-REVIEWER (another fresh Fable session) applies 5.4 and the seven attacks of V2b's review to the pre-design and writes
      `PREREVIEW_<batch>.md` beside it; the pre-designer changes its memo; three rounds at most.
  B3. WHEN THE BATCH'S TURN COMES (the batch before it carries the word of acceptance): the pre-designer's own session is continued - it has the
      reading - or, when it is gone or out of room, a fresh Fable designer with the whole reading takes the pre-design as its draft. It runs
      `next.py --to DESIGN`, does the audit of the batch before (A7), reads the WHOLE diff of every batch accepted since its export, RUNS the
      experiment, corrects the memo wherever the code moved, writes steps 1 to 3 into the record and moves the state to DESIGN_REVIEW. The
      reviewer (the pre-reviewer's session, or a fresh one) then reviews THE MEMO IN THE RECORD against the code as accepted, in
      `reviews/<batch>_design.md`. The gate of items 34 and 35 does not move: nothing is built before that file says APPROVED.
  B4. `next.py` knows Lane A only. A session started with a Lane B brief follows its brief and this amendment, NOT the card `next.py` prints -
      that card belongs to the batch on the machine: a Lane B session never acts on it, never starts a builder, a finisher or a prover.
  B5. THE BRAIN'S BATCHES ARE DESIGNED AT EXTRA HIGH (the owner's item 40, 14 Nov 2026: "assign design of self evolution and self evolving
      algorithm work to fable 5.2 extra high, i.e. the brains of the pipeline ... and then switch to high"). The brain = the batches that
      decide, watch, argue, repair and learn by themselves: V4, V5, B6b, B7, B8. Their designer (B1 and B3) and their design reviewer (B2 and
      the review in the record) are Fable 5.2 sessions at Effort EXTRA HIGH; everything after the approved design is Fable at High as
      amendments 1 and 2 have it. HOW (the app starts a session only at the starter's effort or lower, and applies a raised effort from the
      session's NEXT turn): the dispatcher starts the session with a first turn that only answers READY, calls `set_session_effort` "xhigh"
      (the app may ask the owner), then sends the real brief as a message - that turn runs at Extra high. A session already at work is
      stopped between two steps, raised, and told to go on. If the app refuses the raise: the session runs at High and its file says so.
      WIDENED THE SAME HOUR (item 41: "the design work of other best departments also ... while wisely using tokens between high and extra
      high and ensuring work completion"): the designer and the design reviewer of EVERY remaining batch run at Extra high - PACED BY THE
      ALLOWANCE, read at every start (`get_usage`, the weekly Fable line): under 60% every design and review is Extra high; from 60% only
      the brain's batches keep it and the others are designed at High; from 80% everything is at High and no NEW Lane B session is started -
      what is left belongs to Lane A's finishing passes and repairs (a batch that is built and cannot be finished stops the chain); the
      stop at 88% stands (A8). Extra high is spent ONLY on the design memo and its review: the dispatcher, the launch kit, the finishing
      pass, a repair and the audit are at High.
- THE DISPATCHER is the Fable session the owner gave his word to (item 38): the app lets a session start another only on the owner's own words
  in it. It starts every session of both lanes, keeps at most three Lane B sessions at work, and does no batch's own work once its context is
  past 60% (it starts a fresh Fable finisher or repairer). A session that is refused a start leaves the card and says so in the first line of
  its closing message; one word of the owner ("continue") in a new Fable session takes the dispatcher's place.
- WHAT DOES NOT MOVE: every law of chapter 2; fake mode only; the owner's order of the batches; one run at a time; the whole reading; the
  proving block; and a design is approved on the code it will be built on.

## 0. THE HONEST FRAME (said to the owner; every session keeps it true)
- A plan cannot turn one model into another. What it does: THE MODEL THAT BUILDS NEVER JUDGES ITS OWN WORK. A script computes every verdict; a
  separate session runs it; a red result goes back for repair by a fixed loop with a limit; the word of acceptance cannot even be committed
  without a green verdict file (a git hook). The first live video failed because nothing looked at the finished film the way a viewer does;
  v12's gates do, and this plan makes those gates the only way forward.
- What a script cannot judge is TASTE: whether a design is the best one for a breakout. Its guards are (a) the designs already decided by
  Fable sessions in `BREAKOUT_REDESIGN.md` and the briefs of chapter 12, (b) an independent design review before any code (5.4), (c) the Fable
  audit (chapter 14), (d) at the pilot, the owner's own eye and then real viewers. Say so whenever the owner asks how sure anything is.
- Nothing of v12 has ever met a real service. Every price is a page reading, every clip is an offline stand-in. Never write or say that a
  thing "works" when it has only passed fake mode: say "passes every check in fake mode; reality is met at the pilot".

## 1. WHAT IS BEING BUILT, IN ONE PAGE
- THE OWNER: not technical, 1 to 2 minutes a day on a phone, expects a layoff, Rs 5,000 a month for everything. He rejected the first live
  video (item 16: voice, clarity, number cards, black shapes, 2.5% animation, "ashamed to share"). His goal, in his words: breakout, virality,
  money - every aspect of every output "do or die". His words are in `02`; they are inputs to weigh AND orders where they are orders.
- THE PRODUCT (redesign sections 4, 10, 11): "It happens to YOU" - first person, one changed law of nature per video, science and education.
  EVERY TOPIC STARTS AS A SHORT (12 a month, 3 a week, animated in every second, three native uploads); real viewers' numbers promote the best
  four topics a month to a LONG VIDEO (8:10 to 9:00) that opens on its Short's footage. Formats are data (long F1, F2, soon F3; Shorts S1, S2,
  S3). The scoreboard is real: 1,000 subscribers and the watch hours / Shorts views of YouTube's Partner Program.
- THE MACHINE: a Python package `whatifs/` run by GitHub Actions; state in a Google Sheet (append-only tabs); an ORGANISATION of departments
  (D0 to D14, the Council, the Librarian) that read and write one Knowledge Palace, send memos with clocks, and turn every decision into an
  executed, verified change (`01`). A Feature Contract of hard checks holds any video that breaks a promise.
- WHERE THE BUILD STANDS: accepted - B0 to B6a, V1a, V1b, V2a, V2c (five batches), V2d-a. V2d-b THE LADDER'S RULES is built and RED after its
  first proving pass (one sweep id of 58; chapter 12.1). REMAINING, in the owner's order (items 29, 30): **V2d-b (repair) -> V2b -> V1c -> V4
  -> V5 -> DRAWN BY CODE -> B6b -> B7 -> B8 -> B9 -> B10 -> V3 (the pilot on real services and going live, LAST, with his own sitting).**
- THE LIVE CHANNEL runs old code and is PAUSED by his own hand since 13 Nov 2026. Never ask him about it, never touch that cell, never touch
  `main`. His rejected video stays public.

## 2. THE LAWS (each is enforced by a machine named in brackets; breaking one is never "a judgement call")
THE GIT HOOKS named below (L2, L3, L6) are written and proven, and are active only once THE OWNER has installed them with his one command
(the app refuses a session that tries to install a persistent hook - rightly; a session never works around that, and never runs
`--install` unless the app allows it without being asked twice). `next.py` says at every start whether they are installed. With or
without them the laws are the same: `next.py` guards every move of the state, and the Fable audit reads every commit against them.
L1  FAKE MODE ONLY. Every run has `WI_FAKE=1`. No real key exists on this laptop: never ask for one, create one, or read one; no real upload,
    no real spending, no call to a paid service. [the proving scripts remove every key name from the environment of what they start]
L2  THE BRANCH. All work is on `v12-organisation`. Never push to `main`, never merge, never force-push, never rebase or amend a pushed
    commit, never stash, reset or switch branches, never touch GitHub settings or secrets. [git hook `pre-push`]
L3  CODE IS COMMITTED ONLY IN THE PHASES BUILD AND REPAIR. A design, a review, a proving pass and an acceptance are text under `handoff_v12/`.
    [git hook `pre-commit` reads `handoff_v12/STATE.json`]
L4  THE VERDICT IS COMPUTED. Green means: `proving/verdict.py` printed `VERDICT GREEN`. No session, of any model, decides that a run "is
    basically green", "is red for an unrelated reason", or "would pass on a re-run". Unreadable is red. [`verdict.py`; `next.py --to ACCEPTED`]
L5  A RED RESULT IS NEVER RUN AGAIN UNTIL IT PASSES. A commit with a red verdict is dead: the block runs again only on a NEW final code
    commit, whole, from its first run. [`accept_block.py` and `verdict.py` refuse a second run on a red commit]
L6  THE WORD OF ACCEPTANCE (the word A-C-C-E-P-T-E-D in capitals as the status of a batch) is written into a commit subject or a heading
    of the record ONLY by the prover, ONLY after `next.py --to ACCEPTED` succeeded. Until then write "BUILT - not accepted", "NOT accepted",
    "RED". [git hook `commit-msg`]
L7  THE REPAIR IS AT THE CAUSE, NEVER AT THE JUDGE. To make a red result pass you may never: lower or raise a limit so that it passes, turn
    a hard check into advice or "not applicable", delete or loosen a test, an assertion or a deliberate break, add a skip, shrink the sweep or
    the block, change what a counter counts, catch and swallow the failure, or special-case the failing id. A test changed BY DESIGN is named
    in the record with its reason BEFORE it is changed. [`judge_guard.py` lists every such change and marks the unnamed ones; a weaker block is
    refused by `accept_block.py`; `CLAUDE.md` hard rule 3 of the repo]
L8  HARD ENFORCEMENT OR IT DOES NOT EXIST (the owner, items 12, 14, 15). Every rule a batch adds has code that executes it, a contract check
    or test that FAILS when it is not executed, a row in `docs/CURRENT/ENFORCEMENT_MATRIX.md`, and a deliberate break that a test catches.
    [`breaks.py`, `built_gate.py`, the repo's own meta-tests and Plan Guard]
L9  ONE RUN AFTER ANOTHER. Never two test, rehearsal, sweep or break runs side by side, by one session or by two. [`accept_block.py` and
    `next.py` look for running processes first]
L10 NOTHING OUTSIDE THE REPO IS WRITTEN INTO IT AND NO OUTPUT STAYS IN IT. Work folders and logs live in the session's scratchpad; the proving
    machinery lives in `REALITY_ENGINE_HANDOFF/proving/` (outside the repo). Never copy `proving/` or `shim/` into the repo.
L11 THE PROVING MACHINERY IS NOT YOURS TO CHANGE. `proving/*.py`, `proving/hooks/`, `proving/blocks/default.json`, a verdict file, a judges'
    report, `STATE.json` by hand: never edited, never bypassed (`--no-verify`, `core.hooksPath`, an environment variable, a copy of a script).
    A fault in the machinery is written into the record as an open issue with the exact command and output, the session stops, and the owner
    is told in one line that a Fable session must look. A builder writes only: `proving/blocks/<batch>.json`, `proving/breaks/<batch>.json`,
    `proving/notes/<batch>_*.md`. [the Fable audit recomputes every verdict from its archived logs: `verdict.py --verify`]
L12 THE OWNER'S WORDS are recorded verbatim in `02_OWNER_VERBATIM.md` under the next item number the moment he writes to a session, with
    "what it means for every later session". Answer him first, short, brutally honest, in viewer terms and cost - never in green checks.
    Never make him repeat anything; never ask what a record answers; one decision at a time, in one line, with what and why.
L13 THREE ATTEMPTS. A failing test, a tool of your own or an idea gets at most three repair attempts; then it is written into the record's
    OPEN ISSUES (symptom, what was tried, best hypothesis) and you move on or stop. A batch that is red three times stops the chain for a
    Fable session. [`next.py` counts the red rounds]
L14 INSTALL NOTHING, UPGRADE NOTHING. The tools on this laptop are listed in `BUILD_STATE.md` (HOW TO RUN). A library that `requirements.txt`
    pins is never moved without the workflows and the reference frames (standing rule 4).
L15 WRITE EVERY SCRIPT WITH THE FILE TOOL. Never paste code through a shell here-document on this laptop: the shell eats backslashes and line
    breaks (it has broken a file six times in this build, the last time while this plan's own tools were written).

## 3. THE ROLES AND THE CHAIN OF SESSIONS
Every session is ONE role for ONE batch and then stops. Model and effort: Opus 5.5 at the highest effort the app offers, for every building
and proving role. A session never widens its task, never starts on the next batch "while it is here", and never does another role's work.
| Role | Does | Never does | Ends by |
|---|---|---|---|
| BUILDER (phase DESIGN) | the whole reading (chapter 4), loop steps 1 to 3 into the record | writes code | `next.py --to DESIGN_REVIEW`, starts the reviewer |
| DESIGN REVIEWER | reads the memo as a stranger, applies 5.4, writes `reviews/<batch>_design.md` | edits the memo or any code | `--to BUILD` or `--to DESIGN` |
| BUILDER (phase BUILD) | steps 4, 5, 6a; the breaks; the builder's block; the record; the hand-over | the serial suite, the sweep, any verdict on itself | `--to BUILT --commit`, starts the prover |
| PROVER | the whole acceptance block from one script; the verdict; the judges' report; 6b and 7 of the record | changes any code or test; re-runs a red | `--to ACCEPTED` (then starts the next builder) or `--to RED` |
| REPAIRER | a failing test first, the fix at the cause, everything a builder does last | touches a judge to pass (L7) | `--to BUILT --commit <new>`, starts a FRESH prover |
| AUDITOR (Fable, opened by the owner) | recomputes verdicts, reads designs and diffs, writes findings (chapter 14) | changes code | `--audited <batch>` |
WHO STARTS WHOM (chapter 9 has the exact call): a builder starts its design reviewer and later its prover; a prover that accepted starts the
next batch's builder; a prover that found red does NOT start anything - its report wakes the builder's session, which repairs (it knows the
code); if that session is gone, the next session the owner opens is given the REPAIRER card by `next.py`. If the app refuses a start, the
session proposes it as a card and tells the owner in one line: "Tap the card, or open a new session (Opus 5.5, Extra high) in this folder and
type: continue". ONE WORD FROM HIM ALWAYS WORKS: whatever session he opens runs `next.py` and is told what it is.
THE REPAIRER IS THE BUILDER'S OWN SESSION wherever that session still exists and has room in its context (under 70% used); a fresh repairer
does the builder's whole reading first.

## 4. THE READING ORDER (binding; read each item WHOLE before any work; the owner stopped a batch for a reading cut short)
ALL ROLES, first: this plan; `CLAUDE.md` of the handoff folder; `02_OWNER_VERBATIM.md` whole (his words override everything).
BUILDER and fresh REPAIRER, then, in this order:
1. `00_START_HERE.md`, `01_MASTER_SPEC_ORGANISATION_BRAIN.md`, `03_BATCH_PLAN.md`, `06_STATE_PROTOCOL_CLAUDE_CODE.md`, `04_CURRENT_STATE_AND_RESEARCH.md`.
2. `reality-engine/handoff_v12/BREAKOUT_REDESIGN.md` whole - section 11 with every end note of 11.10 first, then sections 0 to 10.
3. `reality-engine/handoff_v12/BUILD_STATE.md`: the head line; STANDING RULES; THE OWNER'S VERDICT ON THE FIRST LIVE VIDEO; NEXT whole (the
   paragraph "Remember (every lesson paid for so far)" is the memory of twenty batches: read every clause); the record of the batch before
   yours and the newest accepted record whole (the model for your own); OPEN ISSUES whole, 1 to the last; HOW TO RUN whole; the BATCH LOG.
4. `reality-engine/CLAUDE.md` whole (the builders' rulebook: hard rules, the checklist, one recipe per subsystem) and, in `docs/CURRENT/`:
   `OWNER_REQUIREMENTS_LEDGER.md`, `CONCEPT.md`, `PLATFORM_FACTS.md` whole; `SYSTEM.md` and `ENFORCEMENT_MATRIX.md` for the parts your batch touches.
5. The brief of your batch in chapter 12 and every section, issue and file it names.
6. THE CODE YOUR BATCH TOUCHES, whole files, before the design: every module the brief names, every module that calls them (search the names),
   their tests, `tools/sweep.py`, `tools/rehearsal.py`, `tests/conftest.py`, `tests/paid_calls.py`.
NOT read whole (grep them for an exact detail only): the older records under DONE, `05_STALE_SCAN.txt`, `archive/`, the repo's `docs/ARCHIVE/`.
NEVER follow as current: `docs/KERNEL.md`, `docs/CHANGES.md`, anything under an ARCHIVE folder.
PROVER: this plan chapters 0 to 3 and 6 to 11; `02` whole; in `BUILD_STATE.md` the head line, STANDING RULES, the batch's record, the newest
accepted record (the model for 6b and 7), the batch's open issues, HOW TO RUN; the redesign's end note of the batch; `proving/notes/<batch>_BUILT.md`.
DESIGN REVIEWER: this plan chapters 0 to 3, 5.1 to 5.4 and the batch's brief; `02` whole; the redesign sections the brief names; the batch's
Steps 1 to 3 in the record; the code the memo says it will change (enough to judge whether the memo is true about it).
CONTEXT: read `get_usage` at your start. If your window is smaller than the reading, read items 1 to 5 whole and item 6 file by file as you
design; never drop an item silently - write into the record what you could not read and why. When your context passes 70% before your last
acts are done, write "WHERE THE SESSION STANDS" into the record (what is done, what is next, the exact command to resume), commit, and tell
the owner in one line that a fresh session continues; `next.py` gives it the same card.

## 5. THE BUILDER'S LOOP (the MANDATORY BATCH LOOP of `03`, made exact; a checkpoint commit and push after every step)
The record of a batch is a section of `BUILD_STATE.md`, the FIRST under `## DONE`, with the heading
`### <batch> - <NAME> (<date>) - BUILT, NOT ACCEPTED (the builder's record; the prover writes steps 6b and 7)` and the sub-headings exactly
as below (the machinery searches for them). Write the batch's START into the record first: the first check (the last batch accepted on the
record, GitHub's run of its final code commit, a clean tree), the usage figures, whether the batch is SPLIT (rule 6 of `06`: split it at its
start by dependency when it is clearly larger than one session; say so at the top of NEXT; each half is a batch of its own with the full loop).
### 5.1 `#### Step 1 RESEARCH`
At least FIVE sources that you read YOURSELF in this session (WebSearch / WebFetch), each with its address, its date, and E (measured: a
provider's or a platform's own page, a study with a sample) or O (opinion, practice, a vendor). Quote the sentence that matters. Read a
price, a limit or a licence ON THE PROVIDER'S OWN PAGE, never from a listing or a search snippet. End with "NOT FOUND, so nothing is built
on it: ...". Then "AN EXPERIMENT BEFORE THE DESIGN": run or read the accepted code to COUNT what it really does today in your batch's area
(calls, seconds, rupees, how often a path runs) - every batch so far found its design-shaping fact here, not in a web page.
### 5.2 `#### Step 2 CREATIVITY`
At least THREE designs as lines `A. `, `B. `, `C. ` ..., one marked `(ORIGINAL, CHOSEN)` or ORIGINAL, each scored 1 to 5 on: what a viewer or
the channel gains / enforceable / cost inside the cap / reliability / owner effort. One of them is always "as the redesign wrote it". Say why
the losers lose in one clause each. Build the case that DEFEATS your favourite before you choose it.
### 5.3 `#### Step 3 DESIGN MEMO`
One bullet per part: what executes it (module, function), what measures it, which check or test fails without it, its Settings switch (safe
default) and levers (which department owns each), the MONEY said before the build (per video and per month, from the code's own cost lines,
marked "not measured on a bill"), HYPOTHESES (numbered on from the redesign's), "CHANGED FROM THE REDESIGN, with reasons", "NOT IN THIS BATCH,
on purpose". Every number is a starting value and a lever unless a source says otherwise - say which.
Commit (text only), then `python proving/next.py --to DESIGN_REVIEW`.
### 5.4 THE DESIGN REVIEW (a fresh session that did not write the memo; started by the builder, chapter 9)
The reviewer answers each question in `handoff_v12/reviews/<batch>_design.md` with yes / no and one line of evidence:
 1. Does every part serve a viewer or the scoreboard in a way a layman could name? (List any part that only makes the machine bigger.)
 2. Does it honour every word of the owner that touches it? (Name the items of `02`; list any it forgets or contradicts.)
 3. Is every rule ENFORCEABLE as written - a measure code can compute, a check that can fail, a repair where code can repair?
 4. Does any rule judge TASTE by a cheap model, or let a model's opinion gate a video? (Forbidden: `01` N6.)
 5. Is each measure judged on the FINISHED FILE and on what the render recorded, never on the plan? Does a new measure have BOTH kinds of
    measured pairs (known good, known bad) before it gets a limit?
 6. Money: is every new paid second or call a LINE of `costguard.lines`, inside Rs 5,000, with the month's split still fitting?
 7. Does it reuse what earlier batches left ready (the brief's list), or does it rebuild something that exists?
 8. What does it change that an OLDER test or check pins? Is each such change named, with its reason?
 9. What is the worst video this design could still let through, and which check would hold it?
10. What can only reality answer, and is it written down for the pilot as an open issue?
First line of the file: `VERDICT: APPROVED` or `VERDICT: CHANGES REQUIRED`; then the numbered changes (each one concrete: "the memo must ...").
A reviewer that finds nothing to change says which three places it attacked hardest and what it found there. Commit, move the state, stop.
On CHANGES REQUIRED the builder's session is woken: it changes the memo (never argues in prose instead of changing), commits, asks again.
After three rounds without approval: stop, one line to the owner (a Fable session decides).
### 5.5 `#### Step 4 BUILD (what changed)` - the rules of building in this codebase
- Read `reality-engine/CLAUDE.md` again before the first edit: its checklist "A change is not done until" is binding.
- WRAP, never duplicate; a new behaviour sits behind a Settings switch with a safe default (`core.DEFAULTS`); the older tests keep running
  the old path through `tests/conftest.py` only when the batch changes that path BY DESIGN (name it in the record).
- Sheet tabs and columns are append-only; a changed default that must reach a live Sheet needs a one-time move in `whatifs/manage.py` whose
  changes are DATA (a `..._FLIPS` list).
- No model name in code; no retired concept in a current doc or prompt; a new org module goes on `tools/repair.py` PROTECTED first; every
  function is called by production code; every new contract check is classified (`rnd.ORG_CHECKS` or raise `rnd.SHOW_CHECKS`).
- WRITE A FINDING INTO THE RECORD BEFORE THE EDIT THAT FIXES IT ("CORRECTED BY THE BUILD", numbered).
- Seed every random draw by the id. A whole-production test gets ids no other test file uses and removes its work folders.
- After any change to settings, checks, tabs, workflows or a module docstring: `tools/gen_docs.py` and commit `SYSTEM.md`.
### 5.6 `#### Step 5 ENFORCE (rule -> executing code -> fails when broken)`
A table, one row per rule: `| Rule | Executed by | Fails when broken |`. Every row has a matrix row in `docs/CURRENT/ENFORCEMENT_MATRIX.md`,
a test that passes when satisfied AND one that fails when violated, and at least one deliberate break.
THE SWEEP MUST WALK THE NEW PATH: a batch that adds a rule about a finished video or Short adds a judge to `tools/sweep.py` (the pattern:
`money_of`, `motion_of`) that makes an id BAD when the rule's check did not PASS ("not applicable" or a missing row is a failure), a counter
in `summary()`, and that counter in `proving/blocks/<batch>.json`. The rehearsal gets its assert and its printed line.
### 5.7 `#### Step 6 PROVE` - `**6a - THE BUILDER'S HALF**`
- The batch's test file `tests/test_v12_<name>.py`: every rule both ways, one fault at a time, a test must fail for the reason it names; a
  guard is tested with the case built to defeat it; a rule tested only where another rule already refuses is not tested.
- The older tests your batch changes by design: read each BEFORE touching it; list them in the record with the reason. Never run a red test
  again in the hope of green: read, explain, reproduce alone, then fix.
- Plan Guard, Truth, the Palace, the Organisation (commands under HOW TO RUN), each GREEN; `tools/gen_docs.py` without drift.
- Every new whole-production test once in ONE process with every test file after it (GitHub's way; HOW TO RUN gives the command) - the
  laptop's two runners cannot see a collision of ids or folders between files; GitHub can, and it has cost a final commit before.
### 5.8 THE DELIBERATE BREAKS (machine-run)
Write `proving/breaks/<batch>.json` BEFORE the last test run, as "what would fail if this line went?": one break per row of the Step 5
table at the very least, and one per branch of every rule (the batches so far wrote 31 to 145). Each break changes ONE place of the real
code so that the code still runs. Then commit the candidate final code and run, in the background, alone:
`python proving/breaks.py <batch>` -> CAUGHT / MISSED / VOID per break.
MISSED = the rule has no assertion of its own: write the assertion (never delete the break), commit, run ALL breaks again on the new commit.
VOID = rewrite the break. Done only at: 0 missed, 0 void, on the code of the final commit. `git status` after every run.
### 5.9 THE BUILDER'S LAST ACTS, in this order (nothing is skipped; each is a command)
 1. The candidate final code commit is pushed; the tree is clean.
 2. `python proving/breaks.py <batch>` (5.8) - all caught on this commit.
 3. `proving/blocks/<batch>.json`: copy `default.json`, add your counters, pairs, watch lines; never remove one.
 4. The builder's block, detached, then one long wait (chapter 6.2 shows the form):
    `python proving/accept_block.py <batch> HEAD <scratch> --parts 12` - the parallel pre-check and every rehearsal pair on a frozen copy.
 5. Write `"expect_tests": <the pre-check's total>` into your block file.
 6. `python proving/built_gate.py <batch> <scratch>` until it prints GREEN (it names what is missing; a new commit means 2 and 4 again).
 7. The record: steps 1 to 6a complete; `**6b - THE PROVER'S HALF: NOT WRITTEN YET.**`; `#### Step 7 TAKEAWAY - THE BUILDER'S DRAFT`
    (WORKED / FAILED / NOT REACHED / FOR THE NEXT BATCH; also a Palace item `<batch>.takeaway` in the final code commit); the open
    issues (numbered on); the batch log row; the head line; NEXT rewritten for the batch after yours under the words NOT ACCEPTED YET,
    with "What <batch> leaves ready (use it, do not rebuild it)"; the redesign's end note in 11.10 ("WHAT THE BUILD CHANGED IN THIS SECTION").
 8. `proving/notes/<batch>_BUILT.md`: the commit; what was built in ten lines; the totals to expect; what the judge must look at (the
    facts a script cannot see: what a viewer gets, where the margin is thin, what the record claims); what fake mode cannot prove; pitfalls.
 9. Commit the text (subject "... BUILT, not accepted ..."), push, `python proving/next.py --to BUILT --commit <sha>`, commit `STATE.json`, push.
10. Start the PROVER (chapter 9), report "BUILT - not accepted" (chapter 10), stop.

## 6. THE PROVER'S BLOCK (exact; the prover builds nothing)
6.1 `python proving/next.py` (the pre-flight must be clean: settle every line it prints, or write what you see and stop), then
    `python proving/next.py --to PROVING`, commit `STATE.json` (text only), push. Read `get_usage`; note the figures.
6.2 ONE detached run, from the handoff folder, in the Bash tool (Git Bash), with a NEW scratch folder inside your session's scratchpad:
    `SC="<your scratchpad>/block1"; mkdir -p "$SC"; ( PYTHONUTF8=1 .venv/Scripts/python.exe proving/accept_block.py <batch> <final commit> "$SC" > "$SC/driver.log" 2>&1 & ); sleep 20; cat "$SC/out/STATUS.txt" "$SC/driver.log"`
    If it printed `STOP:` instead of a START line, do what the line says (never work around it).
6.3 ONE long wait as a BACKGROUND command of the session (you are told when it exits; about 2 h 30 min; do not poll, do not sleep in short calls):
    `PYTHONUTF8=1 .venv/Scripts/python.exe proving/wait_block.py "$SC" 240`
    While it runs you may read (the record, the code, GitHub's page) and draft 6b in your head - never start another run, never edit the repo.
6.4 When it ends: `cat "$SC/out/VERDICT.txt"` (the verdict without GitHub is PENDING at best), then, once, with GitHub:
    `PYTHONUTF8=1 .venv/Scripts/python.exe proving/verdict.py "$SC/out"` -> first line `VERDICT GREEN | RED | PENDING`.
    PENDING = GitHub's run of that commit is still going (about an hour after the push): wait for it in few calls and compute again. If the
    API does not answer, read the public Actions page of the repository in the browser pane (standing rule 1) and pass what it shows:
    `--github-manual "<run number>,<N passed>,<the rehearsal's line>"`.
6.5 `PYTHONUTF8=1 .venv/Scripts/python.exe proving/judge_guard.py <batch> <base commit from next.py> <final commit>` -> every change the
    batch made to its own judges; an UNEXPLAINED one is red (chapter 8) even under a green verdict.
6.6 WHAT ONLY A JUDGE CAN LOOK AT - write each into 6b in plain words, from the FACTS and WATCH lines of the verdict and the sweep's result
    files (`$SC/out/4_sweep_*.txt`, one RESULT line an id): what a viewer gets on the ids (the measures the batch added, their range, the
    lowest id); every WATCH line (a margin that is thin is said, with the ids); every point of the hand-over's "what the judge must look at";
    what the sweep did NOT cover; WHETHER THE RECORD SAYS ANYTHING THE CODE DOES NOT DO (read the functions the Step 5 table names and
    compare them with the sentences of Steps 3 to 5: a sentence the code does not keep is an open issue at least, red when a viewer or the
    money depends on it); GitHub's red runs of the batch's checkpoints, each read and explained.
6.7 GREEN and nothing in 6.5 / 6.6 that is red -> chapter 7. Otherwise -> chapter 8.
6.8 At the end, always: `python proving/cleanup.py "$SC"`; `python proving/next.py` must show a clean pre-flight.

## 7. WRITING THE ACCEPTANCE (the prover; text only)
1. In the record: `**6b - THE PROVER'S HALF**` (the model is V2d-a's Step 6 and V2d-b's 6b): the first check; each part with its total
   word for word; the sweep "N of N ids on the first pass" with what each part showed; GitHub's run number, "N passed", the rehearsal's
   line; 6.6 in plain words; the usage figures at your start and end beside the builder's. Complete `#### Step 7 TAKEAWAY`.
2. `python proving/next.py --to ACCEPTED` (it refuses without the green verdict and a clean judges' report).
3. Only now: the record's heading becomes `### <batch> - <NAME> (<date>) - ACCEPTED (final code commit <sha7> GREEN in GitHub Checks run
   <n>: <N> passed; sweep <k> of <k> ids)`; the head line; the batch log row ("done <date>"); NEXT loses the words NOT ACCEPTED YET; the
   redesign's status line; open issues closed or narrowed.
4. `python proving/verdict.py --promote <batch>` (the batch's block becomes the floor).
5. Commit BY NAME (`handoff_v12/BUILD_STATE.md`, `handoff_v12/STATE.json`, the redesign if changed), subject
   `v12 <batch>: <name> - ACCEPTED (final code commit <sha7> GREEN in GitHub Checks run <n>: <N> passed; sweep <k> of <k> ids)`, push.
6. `proving/notes/<batch>_ACCEPTED.md` (the state, what a viewer gets, what is not proven, what the next batch must know).
7. Start the next batch's BUILDER (chapter 9; `next.py --to DESIGN` is ITS first move, not yours), report (chapter 10), stop.

## 8. RED: THE SELF-CORRECTING LOOP
8.1 A red or strange result is never run again. FINISH THE BLOCK (it finishes by itself) so that every red of the commit is known at once.
8.2 REPRODUCE ALONE, from the frozen copy the block left (`$SC/wt`), nothing else running:
    a sweep id: `cd "$SC/wt" && PYTHONUTF8=1 WI_FAKE=1 <venv python> tools/sweep.py --one <id> --work "$SC/one_<id>" [--mode short|rehearsal] [--org off]`
    a test: `PYTHONPATH= WI_NO_SKIPS=1 <venv python> -m pytest "tests/<file>.py::<test>" -q -p no:cacheprovider` (GitHub's failure: the two
    tests in one process, in GitHub's order). Does it fail the same way? A result that does NOT reproduce is a finding too: write both runs down.
8.3 MEASURE on what the reproduction kept: for a hold by a check, the check's own measure on the kept file (`motion.long_report`,
    `motion.short_report`, `sound.first_second`, `opening.shown_report`, the row in tab `Feature_Ledger` of `<work>/sheet.json`); numbers,
    seconds, which shot - never an opinion. A scratch script that listens at the unchanged function is allowed; changing the function is not.
8.4 THE RED NOTE `proving/notes/<batch>_RED_<n>.md`: the block's table; the red result word for word; the reproducing command and its output;
    what was measured; the margin on the ids that passed; anything else the judge saw. NO GUESS AT A REPAIR. Then 6b "FIRST / SECOND PASS ON
    <sha7>: RED" in the record, the head line, NEXT, the batch log row (no word of acceptance), `python proving/next.py --to RED`, commit, push,
    `cleanup.py`, report RED, stop. Your report wakes the builder's session.
8.5 A RUN THAT STANDS STILL IS A FINDING, NOT A FLAKE (the `STALL?` line). Do not kill it blindly. Name the test: the pre-check's log, or run
    with `-v`; dump the stuck process: `.venv/Scripts/py-spy.exe dump --pid <pid>` (the pid is in the STALL line; a worker's child has its
    own pid - `tasklist`); write the stack into the red note. Stop ONLY your own run (`taskkill //F //PID <pid> //T`), never every python.exe.
    A block ended by YOUR tooling (a path, a full disk, the app) is not a verdict on the code: say exactly what happened in the record and
    start the block again with `--void-previous "<what failed, word for word>"` - only for that, never for a red test.
8.6 A STRANGE result under a green verdict (a number that jumped, a warning class that is new, a total that differs between the parallel
    and the serial run, a claim of the record the code does not keep): reproduce and measure as above. If a viewer, the money or a rule of
    the batch depends on it, it is RED by your written reasons (the note says so; move the state with the note - `next.py` asks for a red
    verdict, so run `verdict.py` first; when the computed verdict is green, write the finding as a numbered OPEN ISSUE in the record,
    say it in 6b and in your report, and let the Fable audit rule on it - you do not overrule a computed green by opinion).
8.7 THE REPAIRER (the builder's session, woken by the red report; or a fresh session with the builder's reading):
    `python proving/next.py --to REPAIR`; read every red note and the verdict; then, in this order: (1) WRITE THE FAILING TEST FIRST - a test
    in the batch's test file that fails on the red commit for the reason the note measured (for a sweep id: the smallest input that shows
    the same fault, plus the id itself as a whole-production case when it is cheap); commit it red-by-design in the record's words
    ("CORRECTED BY THE BUILD", numbered, written BEFORE the fix); (2) find the CAUSE in the code - read it, do not pattern-match the
    message; when the first explanation does not predict the measured numbers, it is wrong; (3) fix at the cause (L7 names what is not a
    fix); (4) the new test passes, the old ones pass, a deliberate break of the fix is CAUGHT; (5) look for the SAME FAULT ELSEWHERE - the
    family of a fault is searched by name before the commit; (6) the builder's last acts 5.9 from act 1, on the NEW final code commit;
    (7) `next.py --to BUILT --commit <new sha>`, start a FRESH prover, report "BUILT again - not accepted".
    Three red rounds on one batch: `next.py` stops the chain; tell the owner in one line that this batch needs a Fable session.

## 9. STARTING THE NEXT SESSION (exact)
Tool: `mcp__ccd_session__start_session` (load it with ToolSearch, alone in its message, if it is deferred). Parameters:
`initiation` "user_asked"; `context` "fresh"; `use_worktree` false (the session shares this checkout); `wake_when_done` true; `model` and
`effort` OMITTED (it inherits Opus 5.5 at your effort); `title` "<batch>: <role>" (under 60 characters); `name` e.g. "v2b-prover".
`background` (copy, fill the brackets): "Reality Engine v12: the code of the owner's automated YouTube channel, in `reality-engine/` (branch
`v12-organisation`) inside `C:\Users\rrahu\OneDrive\Desktop\REALITY_ENGINE_HANDOFF`. The rest of the build runs under
`reality-engine/handoff_v12/OPUS_BUILD_PLAN.md` (the owner's order, item 33 of `02_OWNER_VERBATIM.md`): the model that builds never judges its
own work; a script computes every verdict; fake mode only; nothing real before the pilot. Batch [X] is in phase [P] (final code commit [sha7])."
`prompt` (copy): "You are ONE role of ONE batch. First, from the handoff folder, run `.venv/Scripts/python.exe proving/next.py` and read the
ROLE CARD it prints. Then read `reality-engine/handoff_v12/OPUS_BUILD_PLAN.md` whole, then the reading order of your role (its chapter 4), then
do exactly what the plan says for your role and stop where it says stop. Never widen the task. Hard constraints (the plan's laws): fake mode
only (`WI_FAKE=1`), no real key, upload or spending; never push to `main`, merge or force-push; never change `proving/` or bypass a git hook;
a red result is never run again; code is committed only in the phases BUILD and REPAIR. Done looks like: the state moved by `proving/next.py`,
the record written, everything pushed, a clean tree, no frozen copy, no test process, the next session started (or the owner told in one
line), and a closing message that begins with '<batch> <BUILT | ACCEPTED | RED | APPROVED | CHANGES REQUIRED>' as the plan's chapter 10 says."
IF THE APP REFUSES THE START: call it again with `initiation` "own_initiative" (a card), and end your closing message with: "Tap the card
'<title>', or open a new session here (Opus 5.5, Extra high) and type: continue". Never start two sessions for one role; never start a
session for a role the state does not ask for; a session on another model is not started by you (the Fable auditor is the owner's click).

## 10. REPORTING (the first 400 characters of your closing message are relayed to the session that started you and are what the owner reads)
- Begin with `<batch> BUILT - not accepted` / `<batch> ACCEPTED` / `<batch> RED` / `<batch> design APPROVED` / `... CHANGES REQUIRED`, then:
  the commit; (prover) the serial totals, the sweep's "N of N ids", GitHub's run number; (builder) the pre-check total, the breaks "n of n".
- Then, in plain words: WHAT A VIEWER GETS that he did not get before; WHAT IT COSTS (rupees a video and a month, by the code's own lines);
  WHAT IS STILL NOT PROVEN (fake mode); anything that waits for the owner, as ONE question at most.
- Then the usage figures at your start and end, and the last line: `Next: <the next role and batch> - set Effort: Extra high`.
- Never report a green check as an achievement and never round a red result up: "55 of 58" is said as 55 of 58.
- To the owner directly: answer first; short; brutal; no tables of checks; his words go into `02` before you act on them.
USAGE: read `mcp__ccd_session_mgmt__get_usage` at your start and end and write the plan's figures (the 5-hour window, weekly all models,
the per-model weekly line that applies to you) and your own context into the record. From 88% of any weekly line or 92% of the 5-hour
window: finish the run you are in, write "WHERE THE SESSION STANDS" into the record, commit, push, tell the owner in one line, stop clean.
Never let a batch die in the middle of a fix.

## 11. THE TRAPS OF THIS CODEBASE AND THIS LAPTOP (each was paid for; the full list is NEXT's paragraph "Remember")
THE LAPTOP: Windows 11; the Bash tool is Git Bash; the venv is `REALITY_ENGINE_HANDOFF/.venv` (`.venv/Scripts/python.exe`, `pytest.exe`,
`py-spy.exe`); the handoff folder syncs to OneDrive (a frozen copy never lives in it; `.git/worktrees/<name>` can stay locked for a minute);
`core.autocrlf=false`, write LF; a script goes through the file tool, never a here-document (L15); a long run is started DETACHED and waited
for with ONE background command; a log of an OLDER run in the same folder must never be read as the new one (a new scratch folder per run);
the venv's `python.exe` is a launcher - one script shows as two processes; the laptop's UTC date is behind the owner's (IST).
THE TESTS: the suite is 78 files and about an hour serial, 35 minutes parallel; GitHub runs every file in ONE process with one work folder;
the older tests run in forced F2, ladder off, clip market off, motion ladder off (`tests/conftest.py`: `OLD_CLIPS`, `OLD_MOTION` - read it
before believing that the suite covers your path: the new paths are covered by the batch's own file, the rehearsals and the sweep);
`tests/paid_calls.py` is the paid-call baseline (a ceiling: every call you add is written there with its count and its reason);
`last_error.txt` is tracked and a red rehearsal rewrites it (`git checkout -- last_error.txt`; the hook refuses it).
THE FAKE WORLD: the fake pipeline is seeded by the episode id - one green rehearsal proves one id, the sweep proves 58; the rehearsal's id is
the minute; the offline clips are WIDE whatever their start picture and travel at one steady speed; an offline film is 75 to 105 seconds,
not nine minutes - a share measured on it says the path works, not what a real video shows; the offline writers cite and obey perfectly, a
real model will not; the offline platforms answer at once.
THE CODE: one cost model (`costguard.lines`) - a paid call without a line makes a sweep id bad; one door for every upright upload
(`release.py`); a status text is data other code reads; a mark on a shot (`short`, `promise`, `anim`, `buy`) must be skipped by EVERY later
step that touches that kind of shot - list those steps by searching the type's name before you build; never log while holding a lock a
log-flush hook takes; a rule about the picture reads `job.segmeta` (what the render showed), never the plan; a measure's limit sits outside
the encoder's noise only when a HELD picture was measured under the real render at both sizes; a second guard hides a broken first one.
THE RECORD: `BUILD_STATE.md` is the memory - a finding is written before its fix; a number is read from the run, never from memory; never
read a result AFTER writing it into a commit message; Plan Guard scans every text file (one flagged word; keep the record clear of it).

## 12. THE BATCH BRIEFS (the scope is the source it names - read the source, not only the brief; "issue n" = OPEN ISSUES of `BUILD_STATE.md`)
Every brief has: WHAT A VIEWER OR THE OWNER GETS - SCOPE (with its sources) - READY (use it, do not rebuild it: the lists under NEXT) -
CONSTRAINTS (decided; not re-opened by a builder) - THE WORST CASE THAT MUST BE HELD - ACCEPTANCE ADDITIONS (what the batch adds to the sweep,
the rehearsal and its block) - FOR THE PILOT (what only reality can answer; written as open issues). A builder may SPLIT a batch at its start
(rule 6) and must say so at the top of NEXT; it may never drop a scope line - a line it cannot build is an open issue with the reason.

### 12.1 V2d-b - THE LADDER'S RULES: THE REPAIR (state RED, red commit 60d9483, round 1)
The builder of V2d-b was a Fable session; by the owner's item 33 the repair is the first job under this plan: a FRESH REPAIRER with the
builder's whole reading (chapter 4), the record of V2d-b, `proving/notes/V2d-b_RED_1.md` and its dump, and all of `whatifs/motion.py`,
`whatifs/anim.py` (`pick_slots`, the Animation Director), `episode.py` from `_render` to the end of `_finish`, `contract.p_moving_share`,
`tools/sweep.py`, `tools/rehearsal.py`, `tests/test_v12_motion.py`.
WHAT IS RED (measured, the note has every number): one sweep id of 58, `EP209901010900`, is HELD by check `moving_share` in every part that
makes a long video: the video paid 13 clips of 5.0 s (65 s); 60.2 s are on screen; 57.5 s are counted moving = 88.5% against the limit 90.
Three scenes of 5 s are shown for 1.47, 3.47 and 4.37 s; two living clips for 4.77 and 4.8 s; 2.7 s are lost to the measure's half-second
grid. Three good ids and one rehearsal stood at 90.4 to 91%.
WHAT THE CODE SHOWS (read by this plan's author; the repairer CONFIRMS each point with a failing test BEFORE changing anything - where a
test contradicts a sentence here, the test wins and the record says so):
 (a) `anim.pick_slots(fit=)` asks whether a scene's line can show it whole BEFORE the living clips exist (the Animation Director runs
     before `motion.place`, the last step before the script gate) and falls back to the nearest line when none fits (`... or cand`).
 (b) `motion.place` starts with an EMPTY `busy` set: the stills a scene must run on into are not reserved. The Director's own living shots
     are taken first (`asked`), so one can sit directly after a scene; `motion.carry` then cannot carry the scene on (the next line carries
     a clip of its own) and the scene is cut where that clip starts.
 (c) `take()` buys b seconds for a room of b - 0.25 s, and `scene_fit` accepts `SCENE_S - 0.25`: a quarter second of such a clip is never
     shown, by construction.
 (d) `motion.long_report` counts whole half seconds from the start of EACH stretch (`_cells`): the rest of every stretch is lost.
 (e) The note of the cell `MOVING_SEEN_MIN_PCT` calls the 10 points of slack "what cuts and rounding may take": the limit was set to absorb
     (b) to (d); on one id of twenty they add up to more.
WHAT THE REPAIR MUST ACHIEVE (each is proven both ways and has a deliberate break):
 1. ON THE FILM: every paid clip of a long video - a scene and a living clip - is on screen for the length that was paid, to the frame, or
    it is not bought. The viewer's reason: the three animated scenes are the dearest seconds and the peaks of the video; a peak shown for
    a second and a half is money nobody sees. The record's sentence "a paid clip is shown whole" becomes true.
 2. THE MEASURE does not lose time to its own grid: on a film where nothing is frozen, the seconds the render recorded and the seconds
    counted as moving agree within half a second for the whole film. Both kinds of pairs are measured again (a HELD picture under grain at
    both sizes must still not count; `MOVING_CHANGE_MIN` is not touched).
 3. THE SWEEP SAYS IT: each long-video id's `motion` words carry the scene seconds on screen of the scene seconds paid; the block keeps the
    hard floor of `proving/blocks/V2d-b.json` - at least 95% of the paid seconds found on EVERY long-video id (add "expect_tests", add your
    own watch line for the scenes; remove nothing).
 4. `EP209901010900` is a named regression: its smallest reproduction as a unit test of the placing and the cutting (the dump has the
    shot list, the line lengths and what the render recorded), and the id itself good in the sweep.
 5. Open issue 179: a rehearsal whose long video is held ends with an assertion that NAMES the failed check. Open issue 176: the record's
    sentences about what the measure compares are made true or are listed under "CORRECTED BY THE BUILD". Open issues 177 and 178: decided
    in the record (built, or left open with the reason and the batch that owns them).
FORBIDDEN HERE (L7, made concrete): changing `MOVING_SEEN_MIN_PCT`, `MOVING_SHARE_MIN_LONG`, `MOVING_CHANGE_MIN` or `SHORT_CHANGE_MIN`;
computing the seen share from `played_s` or from the plan; lowering `paid_s` to what was shown; leaving the scenes out of what was paid;
"not applicable" for the check on a video that bought clips; removing or lowering the block's floor; special-casing the id.
THE REPAIR'S OWN DESIGN NOTE goes into the record before the fix (three ways scored, as in 5.2 - for example: reserve a scene's lines
before the living clips are placed; place the scenes after them; buy only what the lines can show; let a clip end the picture after it
later) with the measured effect of the chosen one on all 28 long-video ids of sweep parts A, B and C run ONE AT A TIME with `--one` during
the build (each alone; never a sweep beside anything).
BREAKS: `proving/breaks/V2d-b.json` - one break per line the repair changes and at least one per row of the record's Step 5 table (the
floor is 30; the builder's 108 breaks of 60d9483 were run by its own script and are not replaced, the table's rules are proven again).
WHAT A VIEWER GETS AFTER IT: nothing new to see - a long video no longer loses paid seconds of its peaks, and about one video in twenty is
no longer held by the machine's own arithmetic after its clips are paid. Money: nothing added.

### 12.2 V2b - INSIDE THE FORMAT
A VIEWER GETS: a voice that speaks to HIM in the present tense and shows before it explains; a camera that stays in one place per act and
moves on from where the last shot ended; an ending that belongs to the format instead of three asks and a tease; no name chip of a
character nobody sees; a third format, "The walk".
SCOPE: redesign 10.7 (first person as a MEASURED share of sentences - a lever; SHOW, THEN TELL; the camera path on the shot list: eye
level, one place per act, each shot beginning where the last ended, a jump = an act break, counted; stills continuing the same direction of
travel; F3 "THE WALK" as a format row and an experiment arm - shares F1 60, F2 20, F3 20 to start, levers of D1); NEXT's paragraph "V2b's
scope"; issues 74 (F1's own ending replaces what `CTA.ensure` and `room.ensure_tease` insert), 75 (the speaker chip of F1,
`overlay.name_of`), 69 (same-subject titles in the promise line-up), 101 (what an ending may promise under the ladder), 129 (the Short's
hook handed to the writers instead of inserted), 60 (the number exemptions once devices are optional), 77 (an F1 writer still receives
the trial's canon), 177 (two places still ask for a silhouette: decide, with the owner's item 16 in mind - he rejected faceless shapes),
124 and 125 (the thumbnail and the Short's first picture; the trial's devices over the footage opening: decide or hand to V1c).
READY: `whatifs/motion.py` (`place` decides WHICH stills move - a camera-path rule that wants a say goes through it or runs before it;
`carry` / `cuts`), `job.segmeta`, `formats.py` (a format is a row), `audience.py` and `layman.py` (the pattern of a measured viewer rule:
a pure measure, a repair by code where code can repair, the writers' ONE fix, the check), `opening.py`, `shotplan.py`.
CONSTRAINTS: every rule is a pure measure code computes on the script, the shot list or the finished file - never a model's opinion of
"immersion"; a rule must RECOGNISE what is wrong and never flag what it does not know (V1b held ordinary words; V2c-a a three-letter word);
a failure rides on the writers' ONE existing fix, then the gate holds; no new paid call without its line; F3 enters as an ARM (data), never
as a replacement; the first-person share and the act-break budget are levers with starting values, said as such (no study measures them on
YouTube: redesign 10.2, O7).
THE WORST CASE THAT MUST BE HELD: a script that lectures in the third person for a paragraph before anything is shown; a shot list that
jumps between five places in one act; an F1 video that ends on "subscribe" and a tease of a topic the ladder never promised.
ACCEPTANCE ADDITIONS: a sweep judge and counter (for example `format_inside_held`) on every long-video id; the rehearsal pairs gain F3
(`["F3","S1"]` at least) once F3 is a row; a watch line for the first-person share.
FOR THE PILOT: the first real F1 and F3 scripts read against the brief (issues 73, 77); whether the walk helps is the viewers' answer (H7).

### 12.3 V1c - THE FLOOR, HIS VERDICT AND THE MAKER'S LINE
A VIEWER GETS: no video that a first-time viewer would rank beside the rejected one; the owner's own sentence, in his words, at the end.
THE OWNER GETS: one tap and one line per release that teaches the machine more than any model.
SCOPE: redesign 4.3 (JUDGED: one generic first-time viewer per model family - no personas - hearing the sound, comparing the new video
PAIRWISE against reference videos; the canary in every session: the owner's rejected video, YouTube id 7RPT4rCuP6k, must LOSE to every
reference and the new video must BEAT it; a jury that does not see that is VOID; LABELS: his verdict is the strongest, real retention the
second; D13 writes a prediction per video and is scored); the owner's verdict tab; redesign 11.6 H-A and 11.9 "Maker's line" (his typed
sentence, spoken in his voice at the end and written into the description; NEVER invented - when he gave none there is none; check
`makers_line`: the text equals his stored line); issue 124 (one story across title, thumbnail and the first seconds).
READY: the Review Board's pattern (`board.py`: strong judges of one family per chain, yes/no answers, the verdict computed by code, a
planted canary, a void session); `layman.probe` (a canary that must fail); `audience.py`; D13's runs; the memo types.
CONSTRAINTS: the floor is a FLOOR, never a forecast (redesign R9: models rank engagement weakly) - it may refuse, it never promotes;
strong judges only, cross-family, blind, the verdict by code; the judged step is a paid call: its line in the cost model, a cap, fake
replies, a switch; no copy of another channel's video is stored or shown - references are the channel's own approved videos and, where the
research step finds it allowed and affordable, public links handed to a video-understanding model (redesign R18), decided in Step 1 with the
price read on the provider's page; the replicated voice does not exist before V3 - the maker's line is built with the designed voice path
and a field for his voice, and a preflight that refuses a voice without its consent record (11.9).
THE WORST CASE THAT MUST BE HELD: the rehearsal makes a flop-like episode (the rejected video's measured traits) and it is held; a jury
session that prefers the canary is void and holds nothing by itself.
ACCEPTANCE ADDITIONS: a sweep judge that the floor ran or was void-by-canary on every long-video id; the rehearsal's flop case.
FOR THE PILOT: his first three verdicts; whether the floor agrees with them (H6).

### 12.4 V4 - THE CEO AND THE LADDER
THE OWNER GETS: a machine that decides the month's plan by itself inside its bounds, tells him in one line, and can be undone with one tap;
the scoreboard as the first line of every brief; an answer to every input of his: adopted, tested or parked, and why.
SCOPE: redesign 4.4 (D1 Strategy wired: the portfolio as levers through the Execution Engine - long videos a month, Shorts a month, uploads
a week, format shares, the promotion bar, moving seconds, the split of the money; DECIDES ALONE inside the bounds and Rs 5,000, INFORMS,
IMPLEMENTS; ASKS FIRST for the channel's name, leaving science, money above the cap, deleting a video; the rules for format arms; a weekly
review in the first three months), 4.7 and 11.10 (D11's split; the compilation from month 2), 4.8 (the scoreboard), 4.9 (the owner's desk:
his input tab until B9's WhatsApp desk exists), 11.4 (the split between long videos and Shorts; the risk line: long-video views against
the Shorts count, weekly); issues 78, 103 (one rule for a long video's and a Short's breakout), 138 (count short uploads across kinds),
154 and 168 (the levers that wait for D1 and D11), 157 (an overrun of the estimate escalates), 90, 2, 144.
READY: the Execution Engine (`levers.py`, `execute.py`: a lever needs its registry entry AND its rule; owner approval by direction),
`governor.split` / `moving_plan` / `line_usd_s`, `shorts2.cadence`, `ladder.py` (the promote rule is code and stays code), `replan.py`,
`registry.PENDING` (D1 and D11 move to `ENTRY`), the memo system, `notify.py` (the only way to the owner).
CONSTRAINTS: D1 never ranks on a model's opinion; a decision is a ticket that the engine applies, verifies and can roll back - never a
sentence; lowering a floor needs the owner; the mix changes by small steps (R3); every decision carries a prediction on the scoreboard and
is scored later (B8 does the scoring - V4 stores it); a department run that returns `Out` says what it did with every inbound memo.
THE WORST CASE THAT MUST BE HELD: a "decision" that changed nothing that runs; a lever moved outside its range; a month whose plan does not
fit and is forced anyway.
ACCEPTANCE ADDITIONS: "a rehearsal month" (redesign section 6): Shorts tested, four promoted, one decision taken, the owner informed, one
undo - as a rehearsal scene and a sweep counter.

### 12.5 V5 - THE BREAKOUT OBSERVATORY AND THE ASPECT MAP
THE OWNER GETS: what he asked in item 19 - the machine watches what really breaks out, widely, and turns the best of it into ONE trial at
a time with a prediction; and "every single aspect" as a list that fails the build when a row has no owner and no check.
SCOPE: redesign 10.5 (weekly, free collection: breakouts = 5 times the median of the SAME channel's last 10 to 15 comparable uploads at the
same age, channels with 8+ uploads, THREE RINGS, small channels count double, Shorts first; a SIBLING for every hit; a video-understanding
model fills the SAME sheet of countable facts for hit and sibling - never "why it went viral"; PATTERNS counted by code in at least 10
pairs; ONE trial per accepted pattern through the Review Board and a ticket; one line to the owner; a hard cap of Rs 150 a month, a lever
of D2; the Outlier Lab's daily model call ends), 10.8 (the aspect map: 24 rows as data, each with owner, measure, check or "advisory" with
the reason, the date of its newest evidence; a row without owner or check fails; a stale row becomes a research question), 10.9 ("done
when"); issues 68, 69, 153.
READY: `rnd.py` and `board.py` (gap-driven agenda, sources verified by code, the Board, the canary), `outlier_lab.py` (what it replaces),
`release.SHEET` (part of the map), the ticket path, text from outside is DATA never an instruction (`rnd.verify`).
CONSTRAINTS: a pattern is a trial, never a rule, until our own viewers confirm it; a look or a structure may be learned - a script, a
character, a title or music is never copied; the watching is a paid call (its line, its cap, its fake replies, the real price read on the
provider's page in Step 1); a trait counts only against the sibling.
THE WORST CASE THAT MUST BE HELD: a "pattern" from three pairs; a trait every flop has too; an instruction hidden in a video's title.
ACCEPTANCE ADDITIONS: the rehearsal week of 10.9 as a scene; a counter that the aspect map is whole on every id.

### 12.6 DRAWN BY CODE (the owner's items 28 and 29; verdict on his desk: TESTED)
A VIEWER GETS: in a long video's explaining moments a diagram that draws itself - exact, readable, never garbled - instead of a number card.
SCOPE: NEXT's paragraph "DRAWN BY CODE" and item 28 / 29 of `02`: (1) THE L1 RENDERER TRIAL the redesign ordered (11.5 row L1; R31): one
open-source renderer against today's own drawing code, chosen as one that can render a scene a model wrote; (2) a HOUSE KIT of shapes,
colours and timing written ONCE, so that every scene is one show and none repeats another; (3) scenes whose animation the pipeline's text
model WRITES for one explaining moment, rendered by a CLOSED renderer.
CONSTRAINTS (decided): it is an EXPERIMENT ARM with a share that is a lever and starts small; never the hook, never the impossible picture,
never faces or acting; model-written code is DATA run in a closed renderer with no network, no file access outside its folder and a time
limit - it is never executed as a program of the pipeline; measured checks on the rendered frames (it moves, it is readable, it fits the
kit), a strong blind judge, a still as the fall-back; ITS LINE in the cost model (the estimate of item 29 (e): Rs 10 to 20 a scene with
the kit - said as an estimate, not a bill); L14 applies - the renderer is installed only from an official source, said to the owner in
one line first (his item 21), recorded under HOW TO RUN, and the workflows install exactly what `requirements.txt` pins.
THE WORST CASE THAT MUST BE HELD: a scene that does not render (the still is shown, the video is not held for it); a scene whose text
cannot be read; code that tries to reach outside its folder.
FOR THE PILOT: his eye on the first real scenes; the retention of those beats against the same kind of beat without one.

### 12.7 B6b - THE COUNCIL
SCOPE: `01` sections 2 (C), 4, 5, 7 (`council_held`); `03` "B6" second bullet; NEXT's notes "What B5 / the B5 recheck / B6a leave ready for
B6b" (read every line: how a verdict becomes a ticket, who judges creative memos, the playbook cap of C, the catch-up of the cadence);
redesign section 6 (the Council also hears D13 and D1); issues 6, 17, 38, 39, 50, 95.
CONSTRAINTS: diverge -> a blind cross-family jury -> converge -> a decision memo WITH tickets; an idea is at most a TEST; the Council never
edits what aired; owner cards only above thresholds; `council_held` goes into `rnd.ORG_CHECKS`; C moves from `registry.PENDING` to `ENTRY`.
THE WORST CASE THAT MUST BE HELD: a decision without an executed ticket; a jury of one family; memo text obeyed as an instruction.

### 12.8 B7 - THE REPAIR LOOP OF THE PIPELINE (D8 with every department)
THE OWNER GETS: fewer cards - a failure is repaired automatically at most twice before anybody is asked, and he is told once, by one path.
SCOPE: `01` section 5 (problem_memo, repair_memo) and 7 (`problem_loop_closed`); `03` "B7"; redesign section 6 (a viewer-seat failure gets
ONE automatic repair before a hold); issues 1, 15, 16, 31, 23 and 36, 52, 64, 70, 89, 108, 115, 127, 157, 178.
CONSTRAINTS: a repair never lowers a bar; at most 2 automatic repairs, then the Council, then the owner; a repeated failure class becomes a
failure lesson in the Palace; every paid repair has its line and its cap; one path to the owner (no doubled messages).
THE WORST CASE THAT MUST BE HELD: a loop that repairs for ever; a repair that passes by weakening the check; a missing Reel "closed" by
the next clean Short (issue 115).
ACCEPTANCE ADDITIONS: the rehearsal shows a forced failure repaired automatically and one that climbs to the owner.

### 12.9 B8 - THE LEARNING LOOP AND THE LIBRARIAN (D10 with all; L)
SCOPE: `01` sections 3.4 and 7 (`lever_verified`, `palace_health`); `03` "B8"; redesign 4.8 (every decision's prediction scored), section 5
and every later H (the hypotheses H1 to H27 get their scoring), 11.8 "THE MINDSET" and 11.9 (every department run names the scoreboard
number it worked for, or says why none - a run that names nothing is a broken run); issues 7, 22 (the writers'-room value test: the owner
said BUILD), 41, 42, 48, 61, 71, 99, 140, 6 and 95.
CONSTRAINTS: promotion and retirement of Palace items by evidence, deterministic merges (no model rewrites the Palace); a prediction is
scored against what happened, never re-explained; strong blind judges of another family for any taste test, with its cost line.
THE WORST CASE THAT MUST BE HELD: an expired item served in a playbook; a contradiction left standing; a run without its scoreboard number.

### 12.10 B9 - THE OWNER OFFICE (D0; D1 is V4's)
THE OWNER GETS: any message of his stored word for word, routed, answered with what will happen and when; a daily brief of at most 8
lines; cards only for what truly needs him.
SCOPE: `01` section 10 and 7 (`owner_memos_honoured`); `03` "B9"; redesign 4.9 (the desk's verdicts), 11.7 (the one-minute release card as
an owner task with a clock - never called done by the machine); issues 19, 34, 43, 56, 102, 135.
CONSTRAINTS: his words are never paraphrased in storage; every owner message goes through `notify.py`; nothing he must do is more than one
tap, pre-filled; the WhatsApp path is proven with stand-ins only (no key here) and listed for the pilot.

### 12.11 B10 - INTEGRATION, THE ORGANISATION'S REHEARSAL, THE DOCS, THE HAND-OVER PACKAGE
SCOPE: `01` sections 7 (the ORG REHEARSAL: the full cycle, GREEN before any package) and 12; `03` "B10"; the owner's item 30 (f): A
CLICK-BY-CLICK RUNBOOK for setup, the pilot and the launch, written so that a session at Effort Medium can carry it out, doing every step
code can do and stopping for him only where his own hand is needed (secrets, sign-ins, the Feature eligibility page, PAUSED, the one-click
Merge) - it never types a key; issues 3, 9, 13 (`registry.PENDING` ends empty), 18, 25, 26, 29, 35, 37, 40, 46, 53, 55, 92, 94 (the
bounded ffmpeg install in every workflow, with a test), 110 (untrack `last_error.txt`), 114, 117, 136, 137 and 160 (the four older doors:
rebuilt on the release sheet or deleted), 146. The pull request `v12-organisation` -> `main` is OPENED (never merged) with the cost table.
CONSTRAINTS: the three lists of `whatifs/truth.py` end as short as they can be; nothing references a retired concept; the package holds
CURRENT docs only; every "first-run verification" the open issues ask for is a line of the runbook with the tab and the cell to read.
B10 ENDS THE BUILD: the prover that accepts it does NOT start a session for V3 - `next.py` stops the chain; the owner is told (chapter 13).

## 13. V3 - THE PILOT ON REAL SERVICES AND GOING LIVE (LAST; the owner's own sitting; not started by any session of this chain)
What must exist before it: B10's runbook. What it must do, from the record (each is an open issue to read in full): the page "Feature
eligibility" FIRST (149) and the phone (112); the human kit - his voice recording with the consent sentence, five photos, three sentences,
the secrets typed by HIM (redesign 11.6); the month's money shown before anything is spent; the bake-off of the clip model BEFORE the first
Short (150, 151) and fal's own usage page after it (152); THE FIRST REAL LIVING CLIPS MEASURED BEFORE ANY GATE'S VERDICT COUNTS (165) and
his eye on a living still (173) and on real footage (166); the first real scripts read against their briefs (73, 81, 67, 87, 119); the
opening's window on real upright clips (123); the release sheet of the first three Shorts row by row (111, 120, 113); the long video's
override, said before he is surprised (97); the one-minute release card with the Short-to-video link first (135); the HELD rows of the old
code shown to him BEFORE he sets PAUSED back with his own hand (148, 139); the real cost of the text lines (156); 1 Jan 2027's prices (159).
Anything reality breaks goes back into this plan's loop as a batch of its own (state DESIGN), never patched live.

## 14. THE FABLE AUDIT (the owner's click; the build does not wait for it, the launch does)
WHY: Opus builds and Opus proves; the scripts keep both honest about what is GREEN. Whether a design is the best one and whether a test
truly tests is judgement - the better model looks at exactly that, at the lowest cost: it reads, it does not build.
HOW THE OWNER STARTS IT: a new session in this folder with Fable 5.2 selected, the word "audit". That session runs
`python proving/next.py --audit` and, for every batch in the queue: (1) `python proving/verdict.py --verify <its verdict file>` (the stored
verdict is recomputed from the archived logs; a mismatch is finding F1); (2) reads the judges' report and every change it lists; (3) reads
the design review and the design memo against the redesign and `02`; (4) reads the diff of `tests/` and of the PROTECTED files; (5) picks
ONE sweep id itself and runs it alone on a frozen copy of the final code commit; (6) writes `handoff_v12/reviews/<batch>_audit.md`: first
line `VERDICT: CLEAN` or `VERDICT: FINDINGS (n)`, then one line per finding - `OPEN F<n>: what is wrong, where, what proves it`.
WHAT A FINDING DOES: `next.py` prints every OPEN finding at the top of every role card and REFUSES `--to BUILT` while one is open. The
builder in charge closes each FIRST - a failing test, the fix at the cause, in its own batch's commits - and rewrites the line to
`CLOSED F<n>: <commit>, <how it is proven>`. A finding it believes is wrong stays OPEN and goes to the owner in one line (a Fable session
or he decides); it is never closed by argument.
WHEN: the session that reports an acceptance says in its closing message how many batches wait ("2 batches wait for a Fable audit");
before V3 the queue must be empty. If the owner wants Fable to approve every DESIGN before it is built (the build then waits for his click
at every batch), he says "gate on": the design reviewer of 5.4 is then a Fable session he opens, and an Opus session stops after
`--to DESIGN_REVIEW` with one line to him.

## 15. WHEN THE PLAN ITSELF IS WRONG
An Opus session never changes this file, `proving/`, or a law. It writes `PLAN ISSUE <n>: <what the plan says, what is true, the command
and output that show it>` into the record's OPEN ISSUES, does the SAFER of the two readings, and says it in its closing message. A Fable
session (the auditor, or one the owner opens for it) changes the plan, in a commit of its own that says what changed and why. The owner's
words change it at any time (L12).

## 16. THE MACHINERY (`REALITY_ENGINE_HANDOFF/proving/`, outside the repo) AND WHAT WAS PROVEN OF IT ON 13 NOV 2026
| File | What it is |
|---|---|
| `next.py` | the entry point of every session: pre-flight, role card, the guarded moves of `handoff_v12/STATE.json`, `--audit`, `--install` |
| `accept_block.py` | the acceptance block from ONE script on two frozen copies (`--parts 12` = the builder's block); never killed on a stall |
| `wait_block.py` | one background wait for a block |
| `verdict.py` | the verdict computed from the logs, GitHub included; `--show`, `--verify` (the auditor), `--promote` (the floor) |
| `github_run.py` | GitHub's Checks run of one commit from the public API: run number, "N passed", the rehearsal's line |
| `judge_guard.py` | what a batch changed in its own judges, and which changes its record does not name |
| `breaks.py` | the deliberate breaks, one place at a time, green first, the file put back and its hash compared |
| `built_gate.py` | may the builder say BUILT: the breaks, the builder's block, Plan Guard, the docs, the record's steps |
| `hook.py`, `hooks/` | the git hooks (`pre-commit`, `commit-msg`, `pre-push`): laws L2, L3, L6 |
| `cleanup.py` | removes the frozen copies and work folders of a scratch folder |
| `blocks/` | the acceptance block as DATA: `default.json` is the floor, `<batch>.json` the batch's own (never weaker) |
| `breaks/`, `built/`, `verdicts/`, `logs/`, `notes/` | break lists and results; gate results; verdicts and judges' reports; the archived logs of every block; hand-over and red notes |
PROVEN BOTH WAYS by the session that wrote them (the test scripts are kept for the auditor's eye in `proving/selftests/` - they ran from
that session's scratchpad against the logs now archived under `proving/logs/V2d-b_60d9483_1/`; the results are in the record of V2d-b):
`verdict.py` on the REAL logs of V2d-b's first pass (RED, for the reasons a judge wrote by hand, plus the thin margins as WATCH lines), on
a doctored copy with the one bad id made good (GREEN; PENDING without GitHub; RED when GitHub's total differs; RED for a missed break and
for breaks run on other code), and refused a second run on the red commit; `github_run.py` on a green, a red and a running run;
`judge_guard.py` on the real commits of V2d-b (8 changes, all named in its record); `breaks.py` on itself (one caught, one missed, one
void; the tree clean); `next.py`'s guards (13 cases); the hooks in a throwaway clone against a throwaway remote (13 cases: code outside
BUILD, a false word of acceptance four ways, the true one, `last_error.txt`, "text only" with code, a push to main, a force-push); the
mechanics of `accept_block.py` (bash from Python, one test file through the shim's runner, one sweep id from a frozen copy, its guards,
its dry run). NOT PROVEN: `accept_block.py` has not run a WHOLE block in this form (the same parts ran from a shell script on 13 Nov
2026, 2 h 23 min); its first whole run is the next prover's - if the script itself fails, that is chapter 8.5 (`--void-previous`), and
the record says so. `built_gate.py` has not met a real batch yet.
